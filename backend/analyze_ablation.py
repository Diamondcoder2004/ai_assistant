import pandas as pd
import sys
sys.stdout.reconfigure(encoding='utf-8')

t1 = pd.read_csv('api_benchmarks/ablation_baseline/latest_results.csv', encoding='utf-8-sig')
t3 = pd.read_csv('api_benchmarks/ablation_no_query_gen/latest_results.csv', encoding='utf-8-sig')

# Side-by-side comparison
print("=== SIDE-BY-SIDE: All 10 questions ===")
print()

for i, (_, row_t1) in enumerate(t1.iterrows()):
    q = row_t1['question']
    row_t3 = t3[t3['question'] == q]
    if len(row_t3) == 0:
        continue
    row_t3 = row_t3.iloc[0]
    
    t1_ok = row_t1['judge_binary_correctness']
    t3_ok = row_t3['judge_binary_correctness']
    t1_comp = row_t1['judge_completeness']
    t3_comp = row_t3['judge_completeness']
    t1_ctx = row_t1['judge_context_recall']
    t3_ctx = row_t3['judge_context_recall']
    t1_q = row_t1['queries']
    t3_q = row_t3['queries']
    
    winner = 'T3' if t3_ok > t1_ok else ('T1' if t1_ok > t3_ok else '=')
    if t3_ok == t1_ok and t3_comp > t1_comp:
        winner = 'T3*'  # T3 better even if binary same
    
    print(f"Q{i+1}: {q[:80]}...")
    print(f"  T1 (QueryGen): binary={t1_ok}, comp={t1_comp}, ctx={t1_ctx}")
    print(f"  T3 (raw):      binary={t3_ok}, comp={t3_comp}, ctx={t3_ctx}")
    print(f"  T1 queries: {t1_q[:100]}...")
    print(f"  Winner: {winner}")
    print()
