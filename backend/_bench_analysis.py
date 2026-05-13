import csv, json
from collections import defaultdict

results = []
with open('api_benchmarks/benchmark_20260513_075934.csv', 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        results.append(row)

print('Vsego zapisej:', len(results))
print()

# Binary correctness distribution
correct = sum(1 for r in results if r.get('judge_binary_correctness', '') == '1')
incorrect = sum(1 for r in results if r.get('judge_binary_correctness', '') == '0')
not_judged = sum(1 for r in results if r.get('judge_binary_correctness', '') not in ('0', '1'))
print('Binary correctness:')
print('  correct:    {} ({:.1f}%)'.format(correct, correct/len(results)*100))
print('  incorrect:  {} ({:.1f}%)'.format(incorrect, incorrect/len(results)*100))
print('  not judged: {}'.format(not_judged))
print()

# Sources count analysis
src_counts = [int(r.get('num_hits', 0)) for r in results]
from collections import Counter
cnt = Counter(src_counts)
print('Istochnikov po zaprosam:')
for n in sorted(cnt.keys()):
    corr = sum(1 for r in results if int(r.get('num_hits', 0)) == n and r.get('judge_binary_correctness', '') == '1')
    total = cnt[n]
    rate = corr/total*100 if total > 0 else 0
    print('  {} istochnikov: {:3d} zaprosov ({:.0f}%), iz nih correct: {:3d} ({:.1f}%)'.format(n, total, total/len(results)*100, corr, rate))
print()

# Source file analysis - what KB doc produced the answer
print('=== Istochniki, iz kotoryh bralis otvety ===')
src_counter = defaultdict(int)
for r in results:
    src_json = r.get('sources_json', '[]')
    try:
        srcs = json.loads(src_json)
        for s in srcs:
            fname = s.get('source_file', 'unknown')
            src_counter[fname] += 1
    except:
        pass

sorted_src = sorted(src_counter.items(), key=lambda x: x[1], reverse=True)
for src, count in sorted_src[:30]:
    print('  {:4d} | {}'.format(count, src[:60]))
