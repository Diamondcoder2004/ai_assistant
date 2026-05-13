import pandas as pd

df = pd.read_csv(
    r'D:\ai_assistant\backend\api_benchmarks\no_query_gen_full\benchmark_20260508_032927_judged.csv',
    encoding='utf-8-sig'
)
col = 'judge_binary_correctness'
print(f'Total rows: {len(df)}')
print(f'Column {col} value counts:')
print(df[col].value_counts().sort_index())
print(f'')
print(f'Mean (all): {df[col].mean():.3f}')
valid = df[df[col] >= 0]
print(f'Excluding -1: {len(valid)} valid, mean={valid[col].mean():.3f}')
print(f'bin=1: {(df[col]==1).sum()} ({(df[col]==1).sum()/len(df)*100:.1f}%)')
print(f'bin=0: {(df[col]==0).sum()} ({(df[col]==0).sum()/len(df)*100:.1f}%)')
print(f'bin=-1: {(df[col]==-1).sum()} ({(df[col]==-1).sum()/len(df)*100:.1f}%)')
print(f'')
print(f'Overall score mean: {df["judge_overall_score"].mean():.2f}')
print(f'Completeness mean: {df["judge_completeness"].mean():.2f}')
print(f'Context recall mean: {df["judge_context_recall"].mean():.2f}')
