import json, glob, statistics
from collections import defaultdict

files = glob.glob('chunking/enriched_chunks/operational/*.json')

by_src = defaultdict(list)

for f in files:
    try:
        with open(f, 'r', encoding='utf-8') as fh:
            data = json.load(fh)
        content = data.get('chunk_content', '')
        src = data.get('source_file', 'UNKNOWN')
        cat = data.get('category', '')
        dtype = data.get('document_type', '')
        by_src[(src, cat, dtype)].append(len(content))
    except:
        pass

print(f'Vsego operational fajlov: {len(by_src)}')
print()

sorted_src = sorted(by_src.items(), key=lambda x: sum(x[1]), reverse=True)

for (src, cat, dtype), sizes in sorted_src:
    total = sum(sizes)
    avg = statistics.mean(sizes)
    med = statistics.median(sizes)
    mn = min(sizes)
    mx = max(sizes)
    n = len(sizes)
    print('Fail: {}'.format(src))
    print('  Kategorija: {}  |  Tip: {}'.format(cat or '-', dtype or '-'))
    print('  Chankov: {:3d} | mediana: {:5.0f} | srednee: {:5.0f} | min: {:5.0f} | max: {:5.0f} | vsego simvolov: {:>8d}'.format(n, med, avg, mn, mx, total))
    print()
