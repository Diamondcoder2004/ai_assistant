import csv

with open('../api_benchmarks/benchmark_20260513_001947.csv', 'r', encoding='utf-8-sig') as f:
    v3 = list(csv.DictReader(f))

with open('../api_benchmarks/benchmark_20260510_202137.csv', 'r', encoding='utf-8-sig') as f:
    v2_all = list(csv.DictReader(f))

v2_lookup = {r['id']: r for r in v2_all}

print('=== v3 enriched chunks vs v2 baseline on 20 WORST questions ===')
print()

improved = []
regressed = []
for r in v3:
    qid = r['id']
    old = v2_lookup.get(qid, {})
    old_s = float(old.get('judge_overall_score', -10)) if old.get('judge_overall_score','').strip() else -10
    new_s = float(r.get('judge_overall_score', -10))
    delta = new_s - old_s
    if delta > 0.5:
        improved.append((delta, r['question'][:60]))
    elif delta < -0.5:
        regressed.append((delta, r['question'][:60]))

print(f'Total: {len(v3)} questions')
print(f'Improved (delta > +0.5): {len(improved)}')
for d, q in sorted(improved, reverse=True):
    print(f'  +{d:.1f}  {q}')
print()
print(f'Regressed (delta < -0.5): {len(regressed)}')
for d, q in sorted(regressed):
    print(f'  {d:.1f}  {q}')
print()

# Questions where LLM says info not in sources
print('=== "No info in sources" cases ===')
for r in v3:
    ans = r.get('answer','')
    for phrase in ['не указан', 'нет информац', 'отсутствует', 'не содержит']:
        if phrase in ans[:100].lower():
            print(f'  Q{r["id"]}: {r["question"][:70]}')
            break

print()
print('=== Summary ===')
# Calculate averages
v3_scores = [float(r.get('judge_overall_score', 0)) for r in v3 if r.get('judge_overall_score','').strip()]
v3_bin = [int(r.get('judge_binary_correctness', 0)) for r in v3 if r.get('judge_binary_correctness','').strip()]
print(f'v3: overall={sum(v3_scores)/len(v3_scores):.2f}, binary={sum(v3_bin)}/{len(v3_bin)}={100*sum(v3_bin)/len(v3_bin):.1f}%')
