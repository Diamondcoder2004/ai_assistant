import json, os
from pathlib import Path
from collections import defaultdict

base = Path('chunking/enriched_chunks')
all_chunks = []

for cat in ['normative', 'operational']:
    for f in (base / cat).glob('*.json'):
        with open(f, 'r', encoding='utf-8') as fh:
            ch = json.load(fh)
        all_chunks.append(ch)

norm_count = sum(1 for c in all_chunks if c.get('source_origin') == 'normative')
oper_count = sum(1 for c in all_chunks if c.get('source_origin') == 'operational')

print(f'Total chunks: {len(all_chunks)}')
print(f'Normative: {norm_count}')
print(f'Operational: {oper_count}')
print()

# What source_files are there?
src_files = defaultdict(lambda: {'count': 0, 'total_chars': 0, 'sizes': []})
for c in all_chunks:
    sf = c.get('source_file', 'unknown')
    cc = len(c.get('chunk_content', c.get('content', '')))
    src_files[sf]['count'] += 1
    src_files[sf]['total_chars'] += cc
    src_files[sf]['sizes'].append(cc)

print(f'Unique source files: {len(src_files)}')
print()

# Stats
sizes = [len(c.get('chunk_content', c.get('content', ''))) for c in all_chunks]
sorted_sizes = sorted(sizes)
n = len(sorted_sizes)

print('=== CHUNK SIZE STATISTICS ===')
print(f'  Min:    {sorted_sizes[0]:,} chars')
print(f'  Max:    {sorted_sizes[-1]:,} chars')
print(f'  Median: {sorted_sizes[n//2]:,} chars')
print(f'  Mean:   {sum(sizes)//n:,} chars')
print(f'  P25:    {sorted_sizes[n//4]:,} chars')
print(f'  P75:    {sorted_sizes[3*n//4]:,} chars')
print(f'  P90:    {sorted_sizes[9*n//10]:,} chars')
print(f'  P95:    {sorted_sizes[95*n//100]:,} chars')
print()

# Top 10 largest chunks
print('=== TOP 10 LARGEST CHUNKS ===')
ranked = sorted(all_chunks, key=lambda c: len(c.get('chunk_content', c.get('content', ''))), reverse=True)
for i, c in enumerate(ranked[:10], 1):
    sz = len(c.get('chunk_content', c.get('content', '')))
    sf = c.get('source_file', '?')[:50]
    cid = c.get('chunk_id', '?')
    cat = c.get('category', '?')
    print(f'{i:>2}. [{sz:>6,} chars] {sf} | id={cid} | cat={cat}')
print()

# Per-file stats
print('=== PER-FILE STATS ===')
for sf in sorted(src_files.keys()):
    d = src_files[sf]
    s = d['sizes']
    avg = sum(s) // len(s) if s else 0
    print(f'  {sf:<50} chunks={d["count"]:>3}  total={d["total_chars"]:>7}  avg={avg:>5}  min={min(s):>5}  max={max(s):>5}')
