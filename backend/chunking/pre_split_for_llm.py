#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Предварительная разбивка больших .md файлов для LLM-обогащения.
Файлы >100k токенов делятся на части по заголовкам/абзацам.
Файлы ≤100k токенов копируются as-is.

Входные папки:
  - new_data/source/markdown_data/    (бывшие PDF)
  - new_data/source/operational/html_pages/  (бывшие HTML)

Выходные папки:
  - new_data/source/markdown_data_split/
  - new_data/source/html_pages_split/
"""

import os
import re
import sys
import shutil
from pathlib import Path
from typing import List, Tuple

import tiktoken

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# ================= НАСТРОЙКИ =================

SCRIPT_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
BASE_DIR = SCRIPT_DIR / ".." / ".." / "new_data" / "source"

INPUT_DIRS = [
    (BASE_DIR / "markdown_data", BASE_DIR / "markdown_data_split"),
    (BASE_DIR / "operational" / "html_pages", BASE_DIR / "html_pages_split"),
]

MAX_TOKENS = 50_000
ENCODING_NAME = "cl100k_base"

# Заголовки Markdown для разбиения
HEADER_PATTERN = re.compile(r'^(#{1,5})\s+(.+)$')

# Изображения Markdown: ![alt](url)
IMAGE_PATTERN = re.compile(r'!\[.*?\]\(.*?\)')


# ================= ФУНКЦИИ =================

def count_tokens(text: str, encoding) -> int:
    """Подсчёт токенов в тексте."""
    return len(encoding.encode(text))


def strip_images(text: str) -> str:
    """
    Удаляет markdown-изображения вида ![alt](url), но сохраняет обычные ссылки [text](url).
    Также убирает пустые строки, которые остались после удаления.
    """
    text = IMAGE_PATTERN.sub('', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text


def split_into_sections(text: str) -> List[Tuple[int, str, str]]:
    """Разбивает Markdown по заголовкам. Возвращает [(level, header_line, body)]."""
    lines = text.split('\n')
    sections = []
    current_header = None
    current_level = 0
    current_content = []

    for line in lines:
        match = HEADER_PATTERN.match(line.strip())
        if match:
            if current_content:
                body = '\n'.join(current_content).strip()
                if body:
                    sections.append((current_level, current_header, body))
            current_level = len(match.group(1))
            current_header = line.strip()
            current_content = []
        else:
            current_content.append(line)

    if current_content:
        body = '\n'.join(current_content).strip()
        if body:
            sections.append((current_level, current_header, body))

    return sections


def split_by_paragraphs(text: str, max_tokens: int, encoding) -> List[str]:
    """Разбивает текст по абзацам, собирая куски ≤ max_tokens."""
    paragraphs = re.split(r'\n\n+', text)
    parts = []
    current = ""

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        candidate = (current + "\n\n" + para).strip() if current else para
        if count_tokens(candidate, encoding) <= max_tokens:
            current = candidate
        else:
            if current:
                parts.append(current)
            # Если один абзац сам по себе > max_tokens, кладём как есть
            current = para

    if current:
        parts.append(current)

    return parts if parts else [text]


def group_sections_into_parts(
    sections: List[Tuple[int, str, str]],
    max_tokens: int,
    encoding
) -> List[str]:
    """Группирует секции (header+body) в части ≤ max_tokens."""
    parts = []
    current_chunks = []
    current_tokens = 0

    for level, header, body in sections:
        section_text = f"{header}\n{body}" if header else body
        section_tokens = count_tokens(section_text, encoding)

        # Если одна секция сама > max_tokens, разбиваем её по абзацам
        if section_tokens > max_tokens:
            # Сначала сохраняем накопленное
            if current_chunks:
                parts.append("\n\n".join(current_chunks))
                current_chunks = []
                current_tokens = 0

            sub_parts = split_by_paragraphs(section_text, max_tokens, encoding)
            parts.extend(sub_parts)
            continue

        # Проверяем: влезет ли в текущую часть
        if current_tokens + section_tokens > max_tokens and current_chunks:
            parts.append("\n\n".join(current_chunks))
            current_chunks = []
            current_tokens = 0

        current_chunks.append(section_text)
        current_tokens += section_tokens

    if current_chunks:
        parts.append("\n\n".join(current_chunks))

    return parts


def process_file(
    input_path: Path,
    output_dir: Path,
    max_tokens: int,
    encoding
) -> Tuple[int, int]:
    """
    Обрабатывает один файл.
    Возвращает (token_count, num_parts).
    """
    with open(input_path, "r", encoding="utf-8") as f:
        text = f.read()

    tokens = count_tokens(text, encoding)
    basename = input_path.stem
    ext = input_path.suffix

    if tokens <= max_tokens:
        # Копируем as-is, но чистим изображения
        cleaned = strip_images(text)
        dest = output_dir / input_path.name
        with open(dest, "w", encoding="utf-8") as f:
            f.write(cleaned)
        return tokens, 1

    # Разбиваем
    sections = split_into_sections(text)

    if len(sections) > 1:
        parts = group_sections_into_parts(sections, max_tokens, encoding)
    else:
        parts = split_by_paragraphs(text, max_tokens, encoding)

    for i, part in enumerate(parts, start=1):
        part_name = f"{basename}_part{i}{ext}"
        dest = output_dir / part_name
        cleaned_part = strip_images(part)
        with open(dest, "w", encoding="utf-8") as f:
            f.write(cleaned_part)

    return tokens, len(parts)


def main():
    encoding = tiktoken.get_encoding(ENCODING_NAME)
    print(f"🔄 Pre-split для LLM (лимит: {MAX_TOKENS:,} токенов)")
    print(f"📐 Кодировка: {ENCODING_NAME}\n")

    total_files = 0
    total_split = 0
    total_parts = 0

    for input_dir, output_dir in INPUT_DIRS:
        input_dir = input_dir.resolve()
        output_dir = output_dir.resolve()

        if not input_dir.exists():
            print(f"⚠️  Папка {input_dir} не найдена, пропускаем")
            continue

        output_dir.mkdir(parents=True, exist_ok=True)

        md_files = sorted(input_dir.glob("*.md"))
        if not md_files:
            print(f"⚠️  В {input_dir} нет .md файлов")
            continue

        print(f"📂 {input_dir.name} → {output_dir.name}")
        print(f"   Файлов: {len(md_files)}\n")

        for fp in md_files:
            tokens, num_parts = process_file(fp, output_dir, MAX_TOKENS, encoding)
            total_files += 1
            total_parts += num_parts

            if num_parts > 1:
                total_split += 1
                print(f"   ✂️  {fp.name}: {tokens:,} токенов → {num_parts} частей")
            else:
                print(f"   ✅ {fp.name}: {tokens:,} токенов (не разделён)")

        print()

    print("=" * 60)
    print(f"📊 Всего файлов: {total_files}")
    print(f"✂️  Разделено: {total_split}")
    print(f"📦 Итого частей: {total_parts}")
    print("=" * 60)


if __name__ == "__main__":
    main()
