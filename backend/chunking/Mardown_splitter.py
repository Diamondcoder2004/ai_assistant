#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
from typing import List, Tuple
from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)

# ================= НАСТРОЙКИ =================

INPUT_DIR = "../deepseek_groups"          # папка с исходными .md файлами
OUTPUT_DIR = "chunks_universal"         # папка для результатов
MIN_CHUNK_SIZE = 1000                    # минимальный размер чанка (символов)
MAX_CHUNK_SIZE = 20_000                    # максимальный размер чанка
SEPARATOR = "\n\n---CHUNK---\n\n"        # разделитель между чанками в выходном файле

# Заголовки для первичного разбиения (любые уровни)
HEADERS_TO_SPLIT_ON = [
    ("#", "h1"),
    ("##", "h2"),
    ("###", "h3"),
    ("####", "h4"),
    ("#####", "h5"),
]

# ================= ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =================

def merge_small_chunks(chunks: List[str], min_size: int, max_size: int) -> List[str]:
    """
    Объединяет мелкие чанки с соседними, не превышая max_size.
    """
    if len(chunks) <= 1:
        return chunks

    result = []
    buffer = ""

    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue

        if not buffer:
            buffer = chunk
            continue

        # Пробуем объединить
        combined = buffer + "\n\n" + chunk
        if len(buffer) < min_size or len(combined) <= max_size:
            buffer = combined
        else:
            result.append(buffer)
            buffer = chunk

    if buffer:
        if len(buffer) < min_size and result:
            result[-1] += "\n\n" + buffer
        else:
            result.append(buffer)

    return result


def split_by_headers(text: str) -> List[str]:
    """
    Пытается разбить текст по заголовкам Markdown.
    Если заголовков нет или разбиение не удалось – возвращает пустой список.
    """
    splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=HEADERS_TO_SPLIT_ON,
        strip_headers=False,
        return_each_line=False,
    )
    try:
        docs = splitter.split_text(text)
        chunks = [doc.page_content for doc in docs if doc.page_content.strip()]
        return chunks if len(chunks) > 1 else []  # считаем, что один чанк – это плохое разбиение
    except Exception:
        return []


def recursive_split(text: str, max_size: int) -> List[str]:
    """
    Универсальный рекурсивный сплиттер с уважением к таблицам и абзацам.
    """
    # Разделители в порядке приоритета: пустая строка (абзац), перевод строки,
    # конец строки таблицы (|\n), точка с пробелом, пробел.
    separators = [
        "\n\n",
        "\n",
        r"\n\|",          # конец строки таблицы (не разрывает строки таблицы)
        ". ",
        " ",
    ]
    splitter = RecursiveCharacterTextSplitter(
        separators=separators,
        chunk_size=max_size,
        chunk_overlap=0,
        length_function=len,
        keep_separator=True,
    )
    return splitter.split_text(text)


def smart_chunking(text: str) -> List[str]:
    """
    Основная функция:
    1. Пытается разбить по заголовкам.
    2. Если получилось много чанков – обрабатывает слишком большие из них.
    3. Если заголовков нет или разбиение дало один чанк – использует рекурсивный сплиттер.
    4. Объединяет мелкие чанки.
    """
    # Шаг 1: пробуем разбить по заголовкам
    header_chunks = split_by_headers(text)

    if header_chunks:
        # Есть структура – обрабатываем каждый крупный чанк отдельно
        final_chunks = []
        for chunk in header_chunks:
            if len(chunk) > MAX_CHUNK_SIZE:
                # разбиваем крупный чанк рекурсивно
                final_chunks.extend(recursive_split(chunk, MAX_CHUNK_SIZE))
            else:
                final_chunks.append(chunk)
    else:
        # Нет структуры – сразу рекурсивное разбиение
        final_chunks = recursive_split(text, MAX_CHUNK_SIZE)

    # Шаг 2: объединяем слишком мелкие чанки
    final_chunks = merge_small_chunks(final_chunks, MIN_CHUNK_SIZE, MAX_CHUNK_SIZE)

    # Шаг 3: если после всех операций не осталось чанков, но текст не пуст – отдаём его целиком
    if not final_chunks and text.strip():
        final_chunks = [text.strip()]

    return final_chunks


def process_file(input_path: str, output_path: str):
    with open(input_path, "r", encoding="utf-8") as f:
        text = f.read()

    chunks = smart_chunking(text)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(SEPARATOR.join(chunks))

    sizes = [len(c) for c in chunks]
    print(f"✅ {os.path.basename(input_path)}")
    print(f"   📦 Чанков: {len(chunks)}")
    if sizes:
        print(f"   📏 Мин: {min(sizes)} | Макс: {max(sizes)} | Средний: {sum(sizes)//len(sizes)}")
    else:
        print("   ⚠️  Пустой результат")


def process_directory(input_dir: str, output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    total_chunks = 0
    files_count = 0

    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.endswith(".md"):
                input_path = os.path.join(root, file)
                rel_path = os.path.relpath(input_path, input_dir)
                output_path = os.path.join(output_dir, rel_path)
                process_file(input_path, output_path)

                # подсчёт чанков в выходном файле
                with open(output_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    cnt = content.count(SEPARATOR) + 1 if content.strip() else 0
                    total_chunks += cnt
                    files_count += 1

    print("\n" + "=" * 50)
    print(f"📁 Файлов обработано: {files_count}")
    print(f"📦 Всего чанков: {total_chunks}")
    print(f"📂 Выходная директория: {output_dir}")
    print("=" * 50)


if __name__ == "__main__":
    print("🔄 Универсальный сплиттер Markdown (адаптивный)")
    print(f"📐 MIN: {MIN_CHUNK_SIZE}, MAX: {MAX_CHUNK_SIZE}")
    print()
    process_directory(INPUT_DIR, OUTPUT_DIR)