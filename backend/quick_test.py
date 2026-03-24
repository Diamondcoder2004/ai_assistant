"""
Быстрый тест Agentic RAG на выбранных вопросах из benchmark_results.csv
"""
import pandas as pd
import json
import time
from pathlib import Path
from datetime import datetime

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import AgenticRAG

# Загрузка данных
QUESTIONS_FILE = "d:/PythonProjects/bashkir_rag/benchmarks/benchmark_results.csv"
OUTPUT_DIR = "quick_test_results"

# Загружаем вопросы
df = pd.read_csv(QUESTIONS_FILE)
print(f"Загружено {len(df)} вопросов")

# Берём первые 5 вопросов для быстрого теста
test_questions = df.head(5)

# Инициализация RAG
rag = AgenticRAG()

# Создание директории для результатов
Path(OUTPUT_DIR).mkdir(exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

results = []

print(f"\n🚀 Запуск теста на {len(test_questions)} вопросах...\n")

for idx, row in test_questions.iterrows():
    question = row['question']
    expected = row.get('expected', '')
    
    print(f"\n{'='*70}")
    print(f"Вопрос #{idx}: {question[:100]}...")
    print(f"{'='*70}")
    
    start_time = time.time()
    
    # Выполнение запроса
    result = rag.query(question)
    
    total_time = time.time() - start_time
    
    print(f"\n⏱️ Время: {total_time:.2f} сек")
    print(f"\n📝 Ответ ({len(result['answer'])} символов):")
    print(result['answer'][:500] + "..." if len(result['answer']) > 500 else result['answer'])
    
    print(f"\n🔍 Поисковые запросы: {result['queries_used']}")
    print(f"📚 Источников: {len(result['sources'])}")
    print(f"🎯 Уверенность: {result['confidence']:.2f}")
    
    results.append({
        'index': idx,
        'question': question,
        'expected': expected,
        'generated_answer': result['answer'],
        'queries_used': json.dumps(result['queries_used'], ensure_ascii=False),
        'sources_count': len(result['sources']),
        'confidence': result['confidence'],
        'time_sec': total_time
    })

# Сохранение результатов
output_file = Path(OUTPUT_DIR) / f"quick_test_{timestamp}.csv"
results_df = pd.DataFrame(results)
results_df.to_csv(output_file, index=False, encoding='utf-8-sig')

print(f"\n{'='*70}")
print(f"✅ Тест завершён!")
print(f"📁 Результаты сохранены в {output_file}")
print(f"{'='*70}")
