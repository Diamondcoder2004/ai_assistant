import csv, json

with open('../api_benchmarks/benchmark_20260510_202137.csv', 'r', encoding='utf-8-sig') as f:
    rows = list(csv.DictReader(f))

scored = [(i, r) for i, r in enumerate(rows) if r.get('judge_overall_score') and r['judge_overall_score'].strip()]
scored.sort(key=lambda x: float(x[1]['judge_overall_score']))

print(f'Total questions: {len(rows)}, scored: {len(scored)}')
print()
print('=== 20 WORST QUESTIONS ===')
for rank, (idx, r) in enumerate(scored[:20], 1):
    q = r['question'][:80]
    exp = r['expected'][:60]
    src = r['source_file'][:50]
    print(f'{rank}. [id={r["id"]}] Score={r["judge_overall_score"]} | Q: {q}')
    print(f'   Expected: {exp}')
    print(f'   Source: {src}')
    print()

worst = [{'idx': r['id'], 'question': r['question'], 'expected': r['expected'], 'source_file': r['source_file']} for _, r in scored[:20]]
with open('worst_20.json', 'w', encoding='utf-8') as f:
    json.dump(worst, f, ensure_ascii=False, indent=2)
print('Saved to worst_20.json')
