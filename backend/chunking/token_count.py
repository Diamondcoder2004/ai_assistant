#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import tiktoken
from collections import defaultdict

# ================= НАСТРОЙКИ =================

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR = os.path.join(SCRIPT_DIR, "..", "deepseek_groups")   # папка с исходными .md файлами

# Выбор кодировки (модели):
# - "cl100k_base" – для gpt-4, gpt-3.5-turbo
# - "p50k_base"   – для gpt-3 (davinci)
# - "r50k_base"   – для gpt-2, gpt-3 (ada, babbage, curie)
ENCODING_NAME = "cl100k_base"

# ==============================================

def count_tokens_in_file(filepath: str, encoding) -> int:
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()
    return len(encoding.encode(text))

def main():
    encoding = tiktoken.get_encoding(ENCODING_NAME)
    print(f"🔄 Подсчёт токенов (кодировка: {ENCODING_NAME})")
    print(f"📂 Входная папка: {INPUT_DIR}\n")

    if not os.path.isdir(INPUT_DIR):
        print(f"❌ Папка {INPUT_DIR} не найдена!")
        sys.exit(1)

    files_data = []
    total_tokens = 0

    for root, dirs, files in os.walk(INPUT_DIR):
        for file in files:
            if file.endswith(".md"):
                filepath = os.path.join(root, file)
                tokens = count_tokens_in_file(filepath, encoding)
                total_tokens += tokens
                files_data.append((file, tokens))

    # сортировка по убыванию токенов
    files_data.sort(key=lambda x: x[1], reverse=True)

    # вывод статистики по каждому файлу
    for filename, token_count in files_data:
        print(f"📄 {filename:<40} {token_count:>8} токенов")

    # общая статистика
    print("\n" + "=" * 60)
    print(f"📊 ВСЕГО ФАЙЛОВ: {len(files_data)}")
    print(f"🔢 СУММАРНО ТОКЕНОВ: {total_tokens}")
    if files_data:
        avg_tokens = total_tokens // len(files_data)
        print(f"📏 СРЕДНЕЕ: {avg_tokens} токенов на файл")
        print(f"📈 МАКСИМУМ: {files_data[0][1]} токенов ({files_data[0][0]})")
        print(f"📉 МИНИМУМ: {files_data[-1][1]} токенов ({files_data[-1][0]})")
    print("=" * 60)

if __name__ == "__main__":
    main()