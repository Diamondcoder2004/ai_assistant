"""
Скрипт для быстрой оценки выбранных ответов Agentic RAG через LLM Judge
"""
import pandas as pd
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from llm_judge import LLMJudge

def evaluate_selected_answers(results_file: str, output_file: str = None):
    """Оценка выбранных ответов через LLM Judge."""
    
    df = pd.read_csv(results_file)
    judge = LLMJudge()
    
    if output_file is None:
        output_file = Path(results_file).stem + "_with_llm_judge.csv"
    
    evaluations = []
    
    print(f"Оценка ответов из {results_file}")
    print(f"Всего ответов: {len(df)}")
    print("=" * 70)
    
    for idx, row in df.iterrows():
        print(f"\n[{idx + 1}/{len(df)}] Вопрос: {row['question'][:80]}...")
        
        # Источники могут быть в разных полях
        sources_data = row.get('sources', '[]')
        if sources_data == '[]' or pd.isna(sources_data):
            sources = []
        else:
            try:
                sources = json.loads(sources_data)
            except:
                sources = []
        
        evaluation = judge.evaluate(
            question=row['question'],
            answer=row['generated_answer'],
            sources=sources
        )
        
        evaluations.append({
            'index': idx,
            'relevance': evaluation.relevance,
            'completeness': evaluation.completeness,
            'helpfulness': evaluation.helpfulness,
            'clarity': evaluation.clarity,
            'hallucination_risk': evaluation.hallucination_risk,
            'overall_score': evaluation.overall_score,
            'reasoning': evaluation.reasoning
        })
        
        print(f"  🎯 Overall: {evaluation.overall_score:.2f}/5")
        print(f"  📌 Relevance: {evaluation.relevance}/5")
        print(f"  📋 Completeness: {evaluation.completeness}/5")
        print(f"  💡 Reasoning: {evaluation.reasoning[:100]}...")
    
    # Добавление оценок в DataFrame
    eval_df = pd.DataFrame(evaluations)
    result_df = pd.concat([df.reset_index(drop=True), eval_df.set_index('index')], axis=1)
    result_df.to_csv(output_file, index=False, encoding='utf-8-sig')
    
    # Статистика
    stats = {
        'total_evaluated': len(evaluations),
        'avg_relevance': sum(e['relevance'] for e in evaluations) / len(evaluations),
        'avg_completeness': sum(e['completeness'] for e in evaluations) / len(evaluations),
        'avg_helpfulness': sum(e['helpfulness'] for e in evaluations) / len(evaluations),
        'avg_clarity': sum(e['clarity'] for e in evaluations) / len(evaluations),
        'avg_hallucination_risk': sum(e['hallucination_risk'] for e in evaluations) / len(evaluations),
        'avg_overall_score': sum(e['overall_score'] for e in evaluations) / len(evaluations),
        'evaluations': evaluations
    }
    
    stats_file = Path(output_file).stem + "_stats.json"
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    
    print("\n" + "=" * 70)
    print("📊 ИТОГОВАЯ СТАТИСТИКА:")
    print(f"  Оценено ответов: {stats['total_evaluated']}")
    print(f"  📌 Relevance: {stats['avg_relevance']:.2f}/5")
    print(f"  📋 Completeness: {stats['avg_completeness']:.2f}/5")
    print(f"  💡 Helpfulness: {stats['avg_helpfulness']:.2f}/5")
    print(f"  ✨ Clarity: {stats['avg_clarity']:.2f}/5")
    print(f"  ⚠️ Hallucination Risk: {stats['avg_hallucination_risk']:.2f}/5")
    print(f"  🎯 Overall Score: {stats['avg_overall_score']:.2f}/5")
    print("=" * 70)
    print(f"\nРезультаты сохранены в {output_file}")
    print(f"Статистика сохранена в {stats_file}")
    
    return result_df, stats


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="LLM Judge для оценки ответов Agentic RAG")
    parser.add_argument("--input", "-i", required=True, help="Файл с результатами (CSV)")
    parser.add_argument("--output", "-o", help="Файл для результатов (CSV)")
    parser.add_argument("--limit", "-l", type=int, help="Ограничить количество ответов")
    
    args = parser.parse_args()
    
    # Загрузка и оценка
    df = pd.read_csv(args.input)
    if args.limit:
        df = df.head(args.limit)
        df.to_csv("selected_results.csv", index=False, encoding='utf-8-sig')
        args.input = "selected_results.csv"
    
    evaluate_selected_answers(args.input, args.output)
