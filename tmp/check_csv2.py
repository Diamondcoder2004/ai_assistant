import pandas as pd

files = [
    'D:/ai_assistant/api_benchmarks/benchmark_20260510_202137.csv',
    'D:/ai_assistant/api_benchmarks/benchmark_20260510_202137_enriched.csv',
    'D:/ai_assistant/api_benchmarks/benchmark_20260513_001947.csv',
    'D:/ai_assistant/api_benchmarks/latest_results.csv',
]
for f in files:
    df = pd.read_csv(f, encoding='utf-8-sig', low_memory=False)
    cols_with_cited = [c for c in df.columns if 'cited' in c.lower()]
    print(f'{f.split("/")[-1]}: {len(df)} rows, cited_cols={cols_with_cited[:4]}')
    if cols_with_cited:
        print(f'  cited_count mean={df["cited_count"].mean():.2f}')
