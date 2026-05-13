import pandas as pd
df = pd.read_csv('D:/ai_assistant/backend/api_benchmarks/benchmark_20260513_075934_enriched.csv', encoding='utf-8-sig')
print('binary_correctness value counts:')
print(df['judge_binary_correctness'].value_counts().sort_index())
print()
print('other targets value counts:')
print('relevance:', df['judge_relevance'].value_counts().sort_index().to_dict())
print('context_recall:', df['judge_context_recall'].value_counts().sort_index().to_dict())
print('overall_score:', df['judge_overall_score'].value_counts().sort_index().to_dict())
