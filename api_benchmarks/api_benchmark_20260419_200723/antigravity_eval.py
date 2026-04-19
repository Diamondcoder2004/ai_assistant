#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Antigravity самостоятельная оценка ответов бенчмарка.
Оценивает каждый ответ по 5-балльной шкале, сравнивая с ожидаемым ответом.
"""
import pandas as pd
import requests
import json
import os
import time
import concurrent.futures
from dotenv import load_dotenv

# Подгружаем .env из корня проекта
load_dotenv(dotenv_path=r"d:\ai_assistant\.env")

API_URL = os.getenv("ROUTERAI_BASE_URL", "https://routerai.ru/api/v1") + "/chat/completions"
API_KEY = os.getenv("ROUTERAI_API_KEY")
MODEL = "qwen/qwen3-next-80b-a3b-instruct"  # inception/mercury-2 использует только reasoning tokens, content=None

benchmark_dir = r"d:\ai_assistant\api_benchmarks\api_benchmark_20260419_200723"
input_csv = os.path.join(benchmark_dir, "results.csv")
output_csv = os.path.join(benchmark_dir, "antigravity_eval_results.csv")

print(f"API URL: {API_URL}")
print(f"MODEL: {MODEL}")
print(f"API_KEY: {'SET' if API_KEY else 'NOT SET'}")

PROMPT_TEMPLATE = """Ты независимый эксперт-оценщик качества ответов RAG-системы.
Твоя задача — строго и честно оценить, насколько хорош фактический ответ системы по сравнению с ожидаемым.

Вопрос пользователя: {question}

Ожидаемый правильный ответ: {expected}

Фактический ответ системы: {answer}

Оцени качество ответа по 5-балльной шкале:
- 1: Ответ полностью неверный / нет нужной информации / галлюцинации
- 2: Ответ частично верный, но с серьёзными ошибками или пропусками
- 3: Ответ в целом верный, но неполный или расплывчатый
- 4: Ответ хороший, точный, с незначительными недостатками
- 5: Ответ отличный, полный, точный, соответствует ожидаемому

Верни ТОЛЬКО одну цифру: 1, 2, 3, 4 или 5. Ничего больше."""


def evaluate_row(row_data, max_retries=3, delay=2):
    index, question, expected, answer = row_data
    prompt = PROMPT_TEMPLATE.format(
        question=str(question)[:1500],
        expected=str(expected)[:1500],
        answer=str(answer)[:2000]
    )
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.0,
        "max_tokens": 20
    }

    for attempt in range(max_retries):
        try:
            resp = requests.post(API_URL, headers=headers, json=payload, timeout=30)
            resp.raise_for_status()
            data = resp.json()

            choices = data.get('choices')
            if not choices:
                raise ValueError(f"No choices in response: {data}")

            message = choices[0].get('message')
            if not message:
                raise ValueError(f"No message in choice: {choices[0]}")

            content = message.get('content')
            if not content:
                raise ValueError(f"No content in message: {message}")

            # Извлекаем первую цифру из ответа
            digits = ''.join(filter(str.isdigit, content.strip()))
            if not digits:
                raise ValueError(f"No digits found in: {content!r}")

            score = float(digits[0])
            if score < 1 or score > 5:
                score = max(1.0, min(5.0, score))

            return index, score

        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(delay * (attempt + 1))
            else:
                print(f"[FAIL] Row {index}: {e}")
                return index, None


def main():
    print("Читаем CSV...")
    df = pd.read_csv(input_csv, encoding='utf-8')
    total = len(df)
    print(f"Всего строк: {total}. Начинаем параллельную оценку (10 воркеров)...")

    rows = [
        (row['index'], row['question'], row['expected'], row['answer'])
        for _, row in df.iterrows()
    ]

    eval_dict = {}
    completed = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_idx = {executor.submit(evaluate_row, r): r[0] for r in rows}
        for future in concurrent.futures.as_completed(future_to_idx):
            result = future.result()
            if result:
                idx, score = result
                eval_dict[idx] = score
            completed += 1
            if completed % 25 == 0:
                done_count = sum(1 for v in eval_dict.values() if v is not None)
                print(f"  Завершено: {completed}/{total} | Успешно оценено: {done_count}")

    df['antigravity_score'] = df['index'].map(eval_dict)

    df_out = df[['index', 'question', 'expected', 'answer',
                 'judge_overall_score', 'antigravity_score']]
    df_out.to_csv(output_csv, index=False, encoding='utf-8-sig')

    valid = df_out['antigravity_score'].dropna()
    failed = df_out['antigravity_score'].isna().sum()

    print(f"\n=== РЕЗУЛЬТАТЫ ===")
    print(f"Успешно оценено: {len(valid)}/{total}")
    print(f"Ошибок (None): {failed}")
    print(f"Antigravity средний балл: {valid.mean():.3f} / 5.0")
    print(f"Judge средний балл:       {df_out['judge_overall_score'].mean():.3f} / 5.0")
    print(f"Файл сохранён: {output_csv}")


if __name__ == "__main__":
    main()
