import os
import json
import re

RAW_DIR = "raw_responses"
OUT_FILE = "recovered_chunks.json"


def fix_json(text: str):
    # фикс сломанных escape
    return re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', text)


def load_multiple_json(text):
    decoder = json.JSONDecoder()
    pos = 0
    results = []

    while pos < len(text):

        while pos < len(text) and text[pos].isspace():
            pos += 1

        if pos >= len(text):
            break

        try:
            obj, index = decoder.raw_decode(text, pos)
            results.append(obj)
            pos = index
        except json.JSONDecodeError:
            pos += 1

    return results


all_chunks = []

files = os.listdir(RAW_DIR)

for file in files:

    path = os.path.join(RAW_DIR, file)

    print("Processing:", file)

    with open(path, encoding="utf-8") as f:
        text = f.read()

    text = fix_json(text)

    json_blocks = load_multiple_json(text)

    if not json_blocks:
        print("NO JSON:", file)
        continue

    for obj in json_blocks:

        if isinstance(obj, list):
            all_chunks.extend(obj)

        elif isinstance(obj, dict):
            all_chunks.append(obj)

print("Total chunks recovered:", len(all_chunks))


with open(OUT_FILE, "w", encoding="utf-8") as f:
    json.dump(all_chunks, f, ensure_ascii=False, indent=2)

print("Saved to", OUT_FILE)
