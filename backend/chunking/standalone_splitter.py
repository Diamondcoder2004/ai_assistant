#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Standalone Markdown splitter - replaces Mardown_splitter.py dependency on langchain.
Splits .md files by headers, handles oversized chunks, merges small ones.
"""

import os
import re

INPUT_DIR = "../../new_data/source"
OUTPUT_DIR = "chunks_universal"
MIN_CHUNK_SIZE = 1000
MAX_CHUNK_SIZE = 20000
SEPARATOR = "\n\n---CHUNK---\n\n"


def split_into_sections(text: str):
    """Split markdown text by headers (h1-h5). Returns list of (header_level, header_text, content)."""
    pattern = r'^(#{1,5})\s+(.+)$'
    lines = text.split('\n')
    sections = []
    current_header = None
    current_level = 0
    current_content = []

    for line in lines:
        match = re.match(pattern, line.strip())
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


def recursive_split_text(text: str, max_size: int):
    """Split text when it exceeds max_size, preferring paragraph boundaries."""
    if len(text) <= max_size:
        return [text]

    # Try splitting on double newlines (paragraphs)
    paragraphs = re.split(r'\n\n+', text)
    result = []
    current = ""

    for para in paragraphs:
        if not para.strip():
            continue
        if not current:
            current = para
        elif len(current) + len(para) + 2 <= max_size:
            current += "\n\n" + para
        else:
            result.append(current)
            current = para

    if current:
        if len(current) < MIN_CHUNK_SIZE and result:
            result[-1] += "\n\n" + current
        else:
            result.append(current)

    return result if result else [text]


def process_file(input_path: str, output_path: str):
    with open(input_path, 'r', encoding='utf-8') as f:
        text = f.read()

    sections = split_into_sections(text)

    # If we have sections, use them; otherwise treat whole text as one section
    if sections:
        chunks = []
        for level, header, body in sections:
            chunk = body
            if header:
                chunk = header + "\n" + body
            if len(chunk) > MAX_CHUNK_SIZE:
                sub_chunks = recursive_split_text(chunk, MAX_CHUNK_SIZE)
                chunks.extend(sub_chunks)
            else:
                chunks.append(chunk)
    else:
        chunks = recursive_split_text(text, MAX_CHUNK_SIZE)

    # Merge small chunks
    merged = []
    buffer = ""
    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue
        if not buffer:
            buffer = chunk
        elif len(buffer) < MIN_CHUNK_SIZE or len(buffer) + len(chunk) + 2 <= MAX_CHUNK_SIZE:
            buffer += "\n\n" + chunk
        else:
            merged.append(buffer)
            buffer = chunk

    if buffer:
        if len(buffer) < MIN_CHUNK_SIZE and merged:
            merged[-1] += "\n\n" + buffer
        else:
            merged.append(buffer)

    if not merged and text.strip():
        merged = [text.strip()]

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(SEPARATOR.join(merged))

    sizes = [len(c) for c in merged]
    print(f"  {os.path.basename(input_path)}: {len(merged)} chunks [{min(sizes)}-{max(sizes)} chars]")


def main():
    input_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), INPUT_DIR))
    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), OUTPUT_DIR))

    print(f"Input:  {input_dir}")
    print(f"Output: {output_dir}")
    print(f"Min chunk: {MIN_CHUNK_SIZE}, Max chunk: {MAX_CHUNK_SIZE}")
    print()

    total_files = 0
    total_chunks = 0

    for root, _, files in os.walk(input_dir):
        for file in sorted(files):
            if not file.endswith('.md'):
                continue

            input_path = os.path.join(root, file)
            rel_path = os.path.relpath(input_path, input_dir)
            output_path = os.path.join(output_dir, rel_path)

            process_file(input_path, output_path)
            total_files += 1

            with open(output_path, 'r', encoding='utf-8') as f:
                content = f.read()
                cnt = content.count(SEPARATOR) + 1 if content.strip() else 0
                total_chunks += cnt

    print(f"\n{'='*50}")
    print(f"Files: {total_files}")
    print(f"Total chunks: {total_chunks}")
    print(f"{'='*50}")


if __name__ == '__main__':
    main()
