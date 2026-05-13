"""Compare old vs new enriched chunks statistics. Output to file."""
import json, os, sys
from pathlib import Path
from statistics import mean, median, stdev

old_root = Path('old_data/chunks_enriched_fixed_old_data')
new_root = Path('backend/chunking/enriched_chunks')

OUTPUT = Path('chunk_comparison_report.txt')

def analyze_chunks(root):
    results = {
        'files': 0, 'categories': {}, 'total_content_chars': 0, 
        'content_lengths': [], 'total_json_chars': 0,
        'has_summary': 0, 'has_questions': 0, 'has_keywords': 0, 'has_entities': 0,
        'question_counts': [], 'keyword_counts': [], 'entity_counts': [],
        'summary_lengths': [],
    }
    
    for cat in sorted(os.listdir(root)):
        cat_path = root / cat
        if cat_path.is_dir():
            results['categories'][cat] = 0
            for f in sorted(os.listdir(cat_path)):
                fp = cat_path / f
                if fp.suffix == '.json':
                    with open(fp, 'r', encoding='utf-8') as fh:
                        raw = fh.read()
                        data = json.loads(raw)
                    results['total_json_chars'] += len(raw)
                    
                    content = data.get('chunk_content', '')
                    clen = len(content)
                    results['files'] += 1
                    results['categories'][cat] += 1
                    results['total_content_chars'] += clen
                    results['content_lengths'].append(clen)
                    
                    summary = data.get('chunk_summary', '')
                    questions = data.get('hypothetical_questions', [])
                    keywords = data.get('keywords', [])
                    entities = data.get('entities', [])
                    
                    if summary:
                        results['has_summary'] += 1
                        results['summary_lengths'].append(len(summary))
                    if questions: 
                        results['has_questions'] += 1
                    if keywords: 
                        results['has_keywords'] += 1
                    if entities: 
                        results['has_entities'] += 1
                    results['question_counts'].append(len(questions) if isinstance(questions, list) else 0)
                    results['keyword_counts'].append(len(keywords) if isinstance(keywords, list) else 0)
                    results['entity_counts'].append(len(entities) if isinstance(entities, list) else 0)
    return results

old = analyze_chunks(old_root)
new = analyze_chunks(new_root)

lines = []
def w(s=''):
    lines.append(s)

w('=' * 100)
w('CHUNK COMPARISON REPORT')
w('OLD: old_data/chunks_enriched_fixed_old_data (April baseline, 39.5% binary)')
w('NEW: backend/chunking/enriched_chunks (current, 21.4% binary)')
w('=' * 100)

w()
w('=== BASIC COUNTS ===')
w(f'  Total JSON files:          OLD={old["files"]:>6}    NEW={new["files"]:>6}')
w(f'  Total JSON size (MB):      OLD={old["total_json_chars"]/1e6:>6.2f}    NEW={new["total_json_chars"]/1e6:>6.2f}')
w(f'  Total content chars:       OLD={old["total_content_chars"]:>10,}  NEW={new["total_content_chars"]:>10,}')

o_len = old['content_lengths']
n_len = new['content_lengths']

w()
w('=== CHUNK CONTENT SIZE (chars) ===')
w(f'  Min:                       OLD={min(o_len):>8,}    NEW={min(n_len):>8,}')
w(f'  Max:                       OLD={max(o_len):>8,}    NEW={max(n_len):>8,}')
w(f'  Mean:                      OLD={int(mean(o_len)):>8,}    NEW={int(mean(n_len)):>8,}')
w(f'  Median:                    OLD={int(median(o_len)):>8,}    NEW={int(median(n_len)):>8,}')
w(f'  StdDev:                    OLD={int(stdev(o_len)):>8,}    NEW={int(stdev(n_len)):>8,}')

ocpf = old["total_content_chars"] // old["files"] if old["files"] else 0
ncpf = new["total_content_chars"] // new["files"] if new["files"] else 0
w(f'  Content chars per file:    OLD={ocpf:>8,}    NEW={ncpf:>8,}')

w()
w('=== SIZE PERCENTILES ===')
for pct in [10, 25, 50, 75, 90, 95, 99]:
    o_sorted = sorted(o_len)
    n_sorted = sorted(n_len)
    o_idx = min(int(len(o_sorted) * pct / 100), len(o_sorted)-1)
    n_idx = min(int(len(n_sorted) * pct / 100), len(n_sorted)-1)
    w(f'  P{pct:>2}:                     OLD={o_sorted[o_idx]:>8,}    NEW={n_sorted[n_idx]:>8,}')

w()
w('=== METADATA COMPLETENESS ===')
for label, o_cnt, n_cnt, total_o, total_n in [
    ('With summary', old['has_summary'], new['has_summary'], old['files'], new['files']),
    ('With hypoth. questions', old['has_questions'], new['has_questions'], old['files'], new['files']),
    ('With keywords', old['has_keywords'], new['has_keywords'], old['files'], new['files']),
    ('With entities', old['has_entities'], new['has_entities'], old['files'], new['files']),
]:
    o_pct = o_cnt/total_o*100 if total_o else 0
    n_pct = n_cnt/total_n*100 if total_n else 0
    w(f'  {label:<25} OLD={o_cnt:>5}/{total_o} ({o_pct:5.1f}%)    NEW={n_cnt:>5}/{total_n} ({n_pct:5.1f}%)')

w()
w('=== METADATA PER CHUNK (avg) ===')
o_qmean = mean(old['question_counts']) if old['question_counts'] else 0
n_qmean = mean(new['question_counts']) if new['question_counts'] else 0
o_kmean = mean(old['keyword_counts']) if old['keyword_counts'] else 0
n_kmean = mean(new['keyword_counts']) if new['keyword_counts'] else 0
o_emean = mean(old['entity_counts']) if old['entity_counts'] else 0
n_emean = mean(new['entity_counts']) if new['entity_counts'] else 0
o_smean = int(mean(old['summary_lengths'])) if old['summary_lengths'] else 0
n_smean = int(mean(new['summary_lengths'])) if new['summary_lengths'] else 0

w(f'  Questions per chunk:       OLD={o_qmean:>8.1f}    NEW={n_qmean:>8.1f}')
w(f'  Keywords per chunk:        OLD={o_kmean:>8.1f}    NEW={n_kmean:>8.1f}')
w(f'  Entities per chunk:        OLD={o_emean:>8.1f}    NEW={n_emean:>8.1f}')
w(f'  Summary length (chars):    OLD={o_smean:>8,}    NEW={n_smean:>8,}')

w()
w('=== CATEGORY DISTRIBUTION ===')
all_cats = sorted(set(list(old['categories'].keys()) + list(new['categories'].keys())))
for cat in all_cats:
    o_cnt = old['categories'].get(cat, 0)
    n_cnt = new['categories'].get(cat, 0)
    w(f'  {cat:<25}    OLD={o_cnt:>5}    NEW={n_cnt:>5}')

w()
w('=== KEY RATIOS ===')
w(f'  Files ratio (new/old):      {new["files"]/old["files"]:.2f}')
w(f'  Content ratio (new/old):    {new["total_content_chars"]/old["total_content_chars"]:.2f}')
w(f'  Avg chunk size ratio:       {ncpf/ocpf:.2f}x' if ocpf else '  N/A')

w()
w('=== CATEGORY MAPPING (old -> new) ===')
w('  OLD: legal        -> NEW: normative  (laws, regulations)')
w('  OLD: informational -> NEW: operational')
w('  OLD: instructions  -> NEW: operational')
w('  OLD: passports    -> NEW: operational')

# Summary quality samples
old_summaries = []
new_summaries = []
for cat_dir in ['legal', 'informational', 'instructions', 'passports']:
    cat_path = old_root / cat_dir
    if cat_path.exists():
        for f in sorted(os.listdir(cat_path))[:5]:
            fp = cat_path / f
            if fp.suffix == '.json':
                with open(fp, 'r', encoding='utf-8') as fh:
                    data = json.load(fh)
                    s = data.get('chunk_summary', '')
                    qs = data.get('hypothetical_questions', [])
                    ks = data.get('keywords', [])
                    if s:
                        old_summaries.append((s, qs, ks, fp.name))
for cat_dir in ['normative', 'operational']:
    cat_path = new_root / cat_dir
    if cat_path.exists():
        for f in sorted(os.listdir(cat_path))[:10]:
            fp = cat_path / f
            if fp.suffix == '.json':
                with open(fp, 'r', encoding='utf-8') as fh:
                    data = json.load(fh)
                    s = data.get('chunk_summary', '')
                    qs = data.get('hypothetical_questions', [])
                    ks = data.get('keywords', [])
                    if s:
                        new_summaries.append((s, qs, ks, fp.name))

w()
w('=== SUMMARY QUALITY (samples) ===')
w('OLD summaries:')
for s, qs, ks, fname in old_summaries[:3]:
    w(f'  [{len(s)} chars] [{fname}]')
    w(f'    Summary: {s[:200]}')
    if qs:
        w(f'    Questions ({len(qs)}): {qs[:3]}')
    if ks:
        w(f'    Keywords ({len(ks)}): {ks[:5]}')
    w()

w('NEW summaries:')
for s, qs, ks, fname in new_summaries[:3]:
    w(f'  [{len(s)} chars] [{fname}]')
    w(f'    Summary: {s[:200]}')
    if qs:
        w(f'    Questions ({len(qs)}): {qs[:3]}')
    if ks:
        w(f'    Keywords ({len(ks)}): {ks[:5]}')
    w()

# Content sample comparison
w()
w('=== CONTENT SAMPLE (first 300 chars) ===')
# Old - legal
for cat_dir in ['legal']:
    cat_path = old_root / cat_dir
    if cat_path.exists():
        for f in sorted(os.listdir(cat_path))[:2]:
            fp = cat_path / f
            with open(fp, 'r', encoding='utf-8') as fh:
                data = json.load(fh)
            content = data.get('chunk_content', '')
            w(f'  OLD {fp.name} ({len(content)} chars):')
            w(f'    {content[:300]}')
            w()

# New - normative
for cat_dir in ['normative']:
    cat_path = new_root / cat_dir
    if cat_path.exists():
        for f in sorted(os.listdir(cat_path))[:2]:
            fp = cat_path / f
            with open(fp, 'r', encoding='utf-8') as fh:
                data = json.load(fh)
            content = data.get('chunk_content', '')
            w(f'  NEW {fp.name} ({len(content)} chars):')
            w(f'    {content[:300]}')
            w()

result = '\n'.join(lines)
with open(OUTPUT, 'w', encoding='utf-8') as f:
    f.write(result)
print(f'Report written to {OUTPUT}')
print(f'({len(result)} chars, {len(lines)} lines)')
print()
print(result)
