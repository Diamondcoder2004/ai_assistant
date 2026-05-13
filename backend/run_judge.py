"""Run LLM Judge on existing benchmark CSV."""
import pandas as pd
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from llm_judge import LLMJudge

csv_in = r'D:\ai_assistant\backend\api_benchmarks\no_query_gen_full\benchmark_20260508_032927.csv'
csv_out = csv_in.replace('.csv', '_judged.csv')
stats_out = csv_in.replace('.csv', '_judge_stats.json')

df = pd.read_csv(csv_in, encoding='utf-8-sig')
judge = LLMJudge()
n = len(df)

results = {k: [] for k in [
    'judge_relevance', 'judge_completeness', 'judge_helpfulness',
    'judge_clarity', 'judge_hallucination_risk', 'judge_context_recall',
    'judge_faithfulness', 'judge_currency', 'judge_binary_correctness',
    'judge_overall_score', 'judge_reasoning'
]}

for i, row in df.iterrows():
    q = str(row['question'])[:80]
    try:
        sources_raw = row['sources_json']
        if isinstance(sources_raw, str):
            sources = json.loads(sources_raw)
        elif pd.isna(sources_raw) or sources_raw is None:
            sources = []
        else:
            sources = sources_raw
    except (json.JSONDecodeError, TypeError):
        sources = []

    expected = str(row['expected']) if not pd.isna(row['expected']) else ''

    t0 = time.time()
    success = False
    for attempt in range(3):
        try:
            ev = judge.evaluate(
                str(row['question']),
                str(row['answer']),
                expected,
                sources
            )
            results['judge_relevance'].append(ev.relevance)
            results['judge_completeness'].append(ev.completeness)
            results['judge_helpfulness'].append(ev.helpfulness)
            results['judge_clarity'].append(ev.clarity)
            results['judge_hallucination_risk'].append(ev.hallucination_risk)
            results['judge_context_recall'].append(ev.context_recall)
            results['judge_faithfulness'].append(ev.faithfulness)
            results['judge_currency'].append(ev.currency)
            results['judge_binary_correctness'].append(ev.binary_correctness)
            results['judge_overall_score'].append(ev.overall_score)
            results['judge_reasoning'].append(ev.reasoning[:200])
            print(f'[{i+1}/{n}] bin={ev.binary_correctness} overall={ev.overall_score:.1f} ({time.time()-t0:.1f}s) {q}')
            success = True
            break
        except Exception as e:
            if attempt == 2:
                print(f'[{i+1}/{n}] FAILED after 3 attempts: {e}')
                for k in results:
                    results[k].append(None)
            else:
                time.sleep(2)

# Append results to CSV
for col_name, values in results.items():
    df[col_name] = values

df.to_csv(csv_out, index=False, encoding='utf-8-sig')

# Compute stats
numeric_cols = [c for c in results if c != 'judge_reasoning' and c != 'judge_binary_correctness']
stats = {}
for c in numeric_cols:
    vals = [v for v in results[c] if v is not None]
    if vals:
        stats[c] = {'mean': sum(vals) / len(vals), 'count': len(vals)}

bin_vals = [v for v in results['judge_binary_correctness'] if v is not None]
stats['binary_correctness_pct'] = sum(bin_vals) / len(bin_vals) * 100 if bin_vals else 0
stats['total_judged'] = len([v for v in results['judge_overall_score'] if v is not None])

with open(stats_out, 'w', encoding='utf-8') as f:
    json.dump(stats, f, ensure_ascii=False, indent=2)

print(f'\n=== DONE: {stats["total_judged"]}/{n} judged ===')
print(f'Binary correctness: {stats["binary_correctness_pct"]:.1f}%')
for c in numeric_cols:
    if c in stats:
        print(f'{c}: {stats[c]["mean"]:.2f}')
