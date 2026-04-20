#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse
import pandas as pd
from pathlib import Path
ФФ
def main():
    parser = argparse.ArgumentParser(description="Анализ результатов бенчмарка")
    parser.add_argument("--results", required=True, help="Путь к директории с results.csv")
    args = parser.parse_args()

    results_dir = Path(args.results)
    csv_path = results_dir / "results.csv"

    if not csv_path.exists():
        print(f"❌ Файл {csv_path} не найден")
        return

    df = pd.read_csv(csv_path)

    print('=' * 60)
    print('📊 АНАЛИЗ РЕЗУЛЬТАТОВ БЕНЧМАРКА')
    print('=' * 60)

    print(f'\n📈 ОБЩАЯ СТАТИСТИКА:')
    print(f'  Всего вопросов: {len(df)}')

    print(f'\n⏱️ ВРЕМЕННЫЕ МЕТРИКИ:')
    print(f'  Среднее время: {df["time_total_sec"].mean():.2f} сек')
    print(f'  Медиана: {df["time_total_sec"].median():.2f} сек')
    print(f'  Мин/Макс: {df["time_total_sec"].min():.2f} / {df["time_total_sec"].max():.2f} сек')

    if "retrieval_time" in df.columns:
        print(f'  Поиск: {df["retrieval_time"].mean():.2f} сек')
    if "generation_time" in df.columns:
        print(f'  Генерация: {df["generation_time"].mean():.2f} сек')

    print(f'\n🎯 УВЕРЕННОСТЬ:')
    if "confidence" in df.columns:
        print(f'  Средняя: {df["confidence"].mean():.3f}')
    else:
        print('  Данные не найдены (столбец confidence отсутствует)')

    print(f'\n📚 ИСТОЧНИКИ:')
    print(f'  Среднее кол-во: {df["num_hits"].mean():.1f}')

    print(f'\n🤖 ОЦЕНКИ LLM-СУДЬИ (1-5):')
    for col in ['judge_relevance', 'judge_completeness', 'judge_helpfulness', 'judge_clarity', 'judge_hallucination_risk', 'judge_overall_score']:
        if col in df.columns:
            print(f'  {col.replace("judge_", "").capitalize()}: {df[col].mean():.2f}')

    print(f'\n📝 ДЛИНА ОТВЕТОВ:')
    df['answer_len'] = df['answer'].str.len()  # Исправлено для избежания NaN
    print(f'  Среднее: {df["answer_len"].mean():.0f} символов')

    # Проверка на NBSP
    nbsp_count = df['answer'].apply(lambda x: '\u00A0' in str(x)).sum()
    print(f'\n🔍 ОТВЕТОВ С NBSP: {nbsp_count} ({nbsp_count/len(df)*100:.1f}%)')

if __name__ == "__main__":
    main()
