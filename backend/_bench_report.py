# -*- coding: utf-8 -*-
import csv, json, statistics
from collections import defaultdict, Counter

results = []
with open('api_benchmarks/benchmark_20260513_075934.csv', 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        results.append(row)

N = len(results)
judged = [r for r in results if r.get('judge_binary_correctness') in ('0','1')]
NJ = len(judged)

out = []
def p(s=''):
    out.append(s)

p('========== БЕНЧМАРК v6 — СТАТИСТИКА ==========')
p('Дата: 2026-05-13 07:59')
p('Файл: api_benchmarks/benchmark_20260513_075934.csv')
p('')
p(f'Всего запросов: {N}')
p(f'Оценено Judge: {NJ}')
p('')

# 1. Binary correctness
correct = sum(1 for r in judged if r['judge_binary_correctness'] == '1')
incorrect = NJ - correct
p('1. Бинарная корректность (judge)')
p(f'  Правильно:  {correct} ({correct/NJ*100:.1f}%)')
p(f'  Неправильно: {incorrect} ({incorrect/NJ*100:.1f}%)')
p('')

# 2. Judge scores distribution
p('2. Средние оценки Judge (по 286 оценённым)')
metrics = [
    ('relevance', 'Релевантность', 5),
    ('completeness', 'Полнота', 5),
    ('helpfulness', 'Полезность', 5),
    ('clarity', 'Ясность', 5),
    ('hallucination_risk', 'Безопасность (5=нет галлюцинаций)', 5),
    ('context_recall', 'Контекст (5=полное извлечение)', 5),
    ('faithfulness', 'Фактологичность', 5),
    ('currency', 'Актуальность', 5),
    ('overall_score', 'Общая оценка', 5),
]
for key, label, scale in metrics:
    vals = [float(r.get('judge_' + key, 0)) for r in judged if r.get('judge_' + key, '')]
    if vals:
        avg = statistics.mean(vals)
        med = statistics.median(vals)
        p(f'  {label}: среднее={avg:.2f} медиана={med:.2f} из {scale}')
p('')

# 3. Correct vs incorrect comparison
p('3. Сравнение правильных vs неправильных ответов')
correct_r = [r for r in judged if r['judge_binary_correctness'] == '1']
incorrect_r = [r for r in judged if r['judge_binary_correctness'] == '0']
for key, label in [('num_hits', 'Источников'), ('judge_relevance', 'Релевантность'), 
                    ('judge_completeness', 'Полнота'), ('judge_context_recall', 'Контекст'),
                    ('judge_faithfulness', 'Фактологичность'), ('confidence', 'Уверенность')]:
    c_vals = [float(r.get(key, 0)) for r in correct_r if r.get(key, '')]
    i_vals = [float(r.get(key, 0)) for r in incorrect_r if r.get(key, '')]
    if c_vals and i_vals:
        p(f'  {label}: correct={statistics.mean(c_vals):.2f} | incorrect={statistics.mean(i_vals):.2f}')
p('')

# 4. Sources distribution
p('4. Распределение по количеству источников')
src_cnt = Counter(int(r.get('num_hits', 0)) for r in results)
for n in sorted(src_cnt.keys()):
    cr = sum(1 for r in results if int(r.get('num_hits', 0)) == n and r.get('judge_binary_correctness') == '1')
    tot = src_cnt[n]
    p(f'  {n} ист.: {tot:3d} запросов ({tot/N*100:.0f}%) | корректных: {cr:3d} ({cr/tot*100:.1f}%)')
p('')

# 5. Source files usage
p('5. Топ-20 source_file из sources_json')
src_counter = Counter()
for r in results:
    s = r.get('sources_json', '[]')
    try:
        srcs = json.loads(s)
        for src in srcs:
            fn = src.get('filename', 'unknown')
            src_counter[fn] += 1
    except:
        pass
for fn, cnt in src_counter.most_common(20):
    p(f'  {cnt:4d} | {fn}')
p('')

# 6. By category from sources_json
p('6. Распределение по категориям (из sources_json)')
cat_counter = Counter()
for r in results:
    s = r.get('sources_json', '[]')
    try:
        srcs = json.loads(s)
        for src in srcs:
            cat = src.get('category', 'unknown')
            cat_counter[cat] += 1
    except:
        pass
for cat, cnt in cat_counter.most_common():
    p(f'  {cnt:4d} | {cat}')
p('')

# 7. Confidence distribution
p('7. Распределение confidence')
conf_cnt = Counter()
for r in results:
    c = float(r.get('confidence', 0))
    bucket = int(c * 10) / 10
    conf_cnt[bucket] += 1
for bucket in sorted(conf_cnt.keys()):
    cr = sum(1 for r in results if abs(float(r.get('confidence', 0)) - bucket) < 0.05 and r.get('judge_binary_correctness') == '1')
    tot = conf_cnt[bucket]
    p(f'  {bucket:.1f}: {tot:3d} запросов ({tot/N*100:.0f}%) | correct: {cr:3d} ({cr/tot*100:.1f}%)')
p('')

# 8. Questions by complexity (answer length)
p('8. Длина ответов')
ans_lens = [len(r.get('answer', '')) for r in results]
p(f'  мин: {min(ans_lens)} симв.')
p(f'  макс: {max(ans_lens)} симв.')
p(f'  медиана: {statistics.median(ans_lens):.0f} симв.')
p(f'  среднее: {statistics.mean(ans_lens):.0f} симв.')
p('')

# 9. Time distribution
p('9. Время выполнения')
times = [float(r.get('time_total_sec', 0)) for r in results]
p(f'  мин: {min(times):.1f} сек')
p(f'  макс: {max(times):.1f} сек')
p(f'  медиана: {statistics.median(times):.1f} сек')
p(f'  среднее: {statistics.mean(times):.1f} сек')
p('')

# 10. Distribution of expected answers from benchmark CSV
p('10. Source_file из benchmark_dataset.csv')
bench_src = Counter(r.get('source_file', '') for r in results)
desc_src = bench_src.most_common(20)
for src, cnt in desc_src:
    cr = sum(1 for r in results if r.get('source_file', '') == src and r.get('judge_binary_correctness') == '1')
    tot = cnt
    p(f'  {cnt:4d} | correct: {cr:3d} ({cr/tot*100:.1f}%) | {src}')

# Write to file
output = '\n'.join(out)
with open('api_benchmarks/benchmark_report_20260513.txt', 'w', encoding='utf-8') as f:
    f.write(output)
print('Saved to api_benchmarks/benchmark_report_20260513.txt')
print(output[:2000])
