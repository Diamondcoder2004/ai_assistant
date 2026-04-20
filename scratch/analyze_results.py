import pandas as pd
import os
import glob
from pathlib import Path

def analyze(results_path, dataset_path):
    print(f"Analyzing {results_path}...")
    
    # Load data
    results_df = pd.read_csv(results_path)
    dataset_df = pd.read_csv(dataset_path)
    
    # Map categories (source_file)
    results_df['source_file'] = dataset_df['source_file'].iloc[:len(results_df)].values
    
    # Define categories based on filename content
    def get_category(filename):
        if not isinstance(filename, str): return 'Прочее'
        if 'Личный кабинет' in filename: return 'Личный кабинет'
        if '861' in filename: return 'ПП 861 (Законодательство)'
        if 'Паспорт услуги' in filename or 'Паспорт' in filename: return 'Паспорта услуг'
        if 'Памятка' in filename: return 'Памятки'
        if 'Часто задаваемые вопросы' in filename: return 'FAQ'
        return 'Прочее'
        
    results_df['category'] = results_df['source_file'].apply(get_category)
    
    # Overall metrics
    total_q = len(results_df)
    system_errors = results_df['answer'].str.startswith("Произошла ошибка").sum()
    avg_overall = results_df['judge_overall_score'].mean()
    binary_acc = (results_df['judge_binary_correctness'] == 1).sum() / total_q
    avg_time = results_df['time_total_sec'].mean()
    
    print(f"Total Questions: {total_q}")
    print(f"System Errors: {system_errors}")
    print(f"Avg Overall Score: {avg_overall:.2f}")
    print(f"Binary Accuracy: {binary_acc:.2%}")
    print(f"Avg Time: {avg_time:.2f}s")
    
    # Per-category metrics
    cat_metrics = results_df.groupby('category').agg({
        'question': 'count',
        'judge_overall_score': 'mean',
        'judge_binary_correctness': lambda x: (x == 1).mean(),
        'time_total_sec': 'mean'
    }).rename(columns={
        'question': 'count',
        'judge_overall_score': 'avg_score',
        'judge_binary_correctness': 'accuracy',
        'time_total_sec': 'avg_time'
    })
    
    print("\nCategory Metrics:")
    print(cat_metrics)
    
    # Error Analysis
    # Low scores (< 3.0) excluding system errors
    mask_low = (results_df['judge_overall_score'] < 3.0) & (~results_df['answer'].str.startswith("Произошла ошибка"))
    low_score_samples = results_df[mask_low]
    
    # Hallucinations
    hallucinations = results_df[results_df['judge_hallucination_risk'] < 3.0]
    
    # Faithfulness
    unfaithful = results_df[results_df['judge_faithfulness'] < 3.0]
    
    # Context issues
    missing_context = results_df[results_df['judge_context_recall'] < 3.0]
    
    return {
        'overall': {
            'total': total_q,
            'errors': system_errors,
            'avg_score': avg_overall,
            'accuracy': binary_acc,
            'avg_time': avg_time
        },
        'categories': cat_metrics.to_dict(orient='index'),
        'low_scores': low_score_samples[['question', 'expected', 'answer', 'judge_overall_score', 'judge_justification']].head(10).to_dict(orient='records'),
        'hallucinations': hallucinations[['question', 'answer', 'judge_justification']].head(5).to_dict(orient='records'),
        'missing_context': missing_context[['question', 'expected', 'judge_justification']].head(5).to_dict(orient='records')
    }

if __name__ == "__main__":
    # Find latest benchmark folder
    bench_dirs = glob.glob('api_benchmarks/api_benchmark_*')
    if not bench_dirs:
        print("No benchmarks found")
    else:
        latest_dir = max(bench_dirs, key=os.path.getmtime)
        results_csv = os.path.join(latest_dir, 'results.csv')
        dataset_csv = 'new_data/benchmark_dataset.csv'
        
        if os.path.exists(results_csv):
            res = analyze(results_csv, dataset_csv)
            # You could save this to a json or just print
        else:
            print(f"Results not found in {latest_dir}")
