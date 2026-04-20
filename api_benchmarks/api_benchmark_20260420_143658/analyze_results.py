import pandas as pd
import os

csv_path = r'd:\ai_assistant\api_benchmarks\api_benchmark_20260420_143658\results.csv'
df = pd.read_csv(csv_path)

print(f"Total rows: {len(df)}")
errors = df[df['answer'].str.startswith('ERROR', na=False)]
print(f"Total errors: {len(errors)}")

if len(errors) > 0:
    print("\nFirst 10 error messages:")
    print(errors['answer'].head(10).tolist())

# Also check average scores where binary_correctness is 0
print("\nMetrics summary (excluding errors):")
success_df = df[~df['answer'].str.startswith('ERROR', na=False)]
metrics = [
    "judge_relevance", "judge_completeness", "judge_helpfulness",
    "judge_clarity", "judge_hallucination_risk", 
    "judge_context_recall", "judge_faithfulness", "judge_currency", "judge_binary_correctness"
]
print(success_df[metrics].mean())
