#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pandas as pd

df = pd.read_csv(r'd:\PythonProjects\agentic_rag\benchmarks\agentic_benchmarks\agentic_benchmark_20260323_111101\results.csv')

print('=' * 60)
print('📊 АНАЛИЗ РЕЗУЛЬТАТОВ БЕНЧМАРКА')
print('=' * 60)

print(f'\n📈 ОБЩАЯ СТАТИСТИКА:')
print(f'  Всего вопросов: {len(df)}')

print(f'\n⏱️ ВРЕМЕННЫЕ МЕТРИКИ:')
print(f'  Среднее время: {df["time_total_sec"].mean():.2f} сек')
print(f'  Медиана: {df["time_total_sec"].median():.2f} сек')
print(f'  Мин/Макс: {df["time_total_sec"].min():.2f} / {df["time_total_sec"].max():.2f} сек')
print(f'  Поиск: {df["time_retrieve_sec"].mean():.2f} сек')
print(f'  Генерация: {df["time_generation_sec"].mean():.2f} сек')

print(f'\n🎯 УВЕРЕННОСТЬ:')
print(f'  Средняя: {df["confidence"].mean():.3f}')

print(f'\n📚 ИСТОЧНИКИ:')
print(f'  Среднее кол-во: {df["num_hits"].mean():.1f}')

print(f'\n🤖 ОЦЕНКИ LLM-СУДЬИ (1-5):')
for col in ['judge_relevance', 'judge_completeness', 'judge_helpfulness', 'judge_clarity', 'judge_hallucination_risk', 'judge_overall_score']:
    print(f'  {col.replace("judge_", "").capitalize()}: {df[col].mean():.2f}')

print(f'\n📝 ДЛИНА ОТВЕТОВ:')
df['answer_len'] = df['answer'].apply(len)
print(f'  Среднее: {df["answer_len"].mean():.0f} символов')

# Проверка на NBSP
nbsp_count = df['answer'].apply(lambda x: '\u00A0' in str(x)).sum()
print(f'\n🔍 ОТВЕТОВ С NBSP: {nbsp_count} ({nbsp_count/len(df)*100:.1f}%)')
