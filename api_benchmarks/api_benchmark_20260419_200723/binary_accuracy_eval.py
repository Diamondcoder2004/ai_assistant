#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Бинарная оценка точности: 1 если ответ семантически содержит правильный ответ, иначе 0.
Считает итоговый % точности системы.
"""
import pandas as pd
import requests
import os
import concurrent.futures
import time
from dotenv import load_dotenv

load_dotenv(dotenv_path=r"d:\ai_assistant\.env")

API_URL = os.getenv("ROUTERAI_BASE_URL", "https://routerai.ru/api/v1") + "/chat/completions"
API_KEY = os.getenv("ROUTERAI_API_KEY")
MODEL = "qwen/qwen3-next-80b-a3b-instruct"

benchmark_dir = r"d:\ai_assistant\api_benchmarks\api_benchmark_20260419_200723"
input_csv = os.path.join(benchmark_dir, "results.csv")
output_csv = os.path.join(benchmark_dir, "binary_accuracy_results.csv")

PROMPT = """Ты эксперт по оценке качества ответов. Твоя задача — определить, содержит ли ОТВЕТ СИСТЕМЫ правильную информацию из ОЖИДАЕМОГО ОТВЕТА, с учётом семантики.

Правила оценки:
- Оцени 1 (правильно), если ответ системы по смыслу содержит ключевую информацию из ожидаемого ответа, даже если:
  * Ответ более длинный или подробный
  * Слова сформулированы по-другому (синонимы)
  * Есть небольшие несущественные дополнения
  * Числа или сроки указаны в другом формате (например, "один рабочий день" = "1 рабочий день")
- Оцени 0 (неправильно), если:
  * Ответ системы содержит неверную информацию
  * Ключевой факт из ожидаемого ответа отсутствует
  * Ответ уклончивый / предлагает обратиться за ответом, хотя правильный ответ известен

Вопрос: {question}

Ожидаемый правильный ответ: {expected}

Ответ системы: {answer}

Верни ТОЛЬКО одну цифру: 1 (правильно) или 0 (неправильно). Никаких пояснений."""


def evaluate_row(row_data, max_retries=3, delay=2):
    index, question, expected, answer = row_data
    prompt = PROMPT.format(
        question=str(question)[:1000],
        expected=str(expected)[:1000],
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
        "max_tokens": 5
    }

    for attempt in range(max_retries):
        try:
            resp = requests.post(API_URL, headers=headers, json=payload, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            content = data['choices'][0]['message'].get('content')
            if not content:
                raise ValueError("content is None")
            digits = ''.join(filter(lambda c: c in '01', content.strip()))
            if not digits:
                raise ValueError(f"No 0/1 found in: {content!r}")
            return index, int(digits[0])
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(delay * (attempt + 1))
            else:
                print(f"[FAIL] Row {index}: {e}")
                return index, None


def main():
    print("Reading CSV...")
    df = pd.read_csv(input_csv, encoding='utf-8')
    total = len(df)
    print(f"Total rows: {total}. Running binary semantic accuracy evaluation (model: {MODEL})...")

    rows = [
        (row['index'], row['question'], row['expected'], row['answer'])
        for _, row in df.iterrows()
    ]

    eval_dict = {}
    completed = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(evaluate_row, r): r[0] for r in rows}
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result:
                idx, score = result
                eval_dict[idx] = score
            completed += 1
            if completed % 25 == 0:
                correct = sum(1 for v in eval_dict.values() if v == 1)
                total_done = len(eval_dict)
                pct = (correct / total_done * 100) if total_done else 0
                print(f"  Done: {completed}/{total} | Current accuracy: {pct:.1f}%")

    df['correct'] = df['index'].map(eval_dict)

    df_out = df[['index', 'question', 'expected', 'answer', 'judge_overall_score', 'correct']].copy()
    df_out.to_csv(output_csv, index=False, encoding='utf-8-sig')

    valid = df_out[df_out['correct'].notna()]
    failed = df_out['correct'].isna().sum()
    correct_count = (valid['correct'] == 1).sum()
    wrong_count = (valid['correct'] == 0).sum()
    accuracy = correct_count / len(valid) * 100

    print(f"\n{'='*50}")
    print(f"BINARY ACCURACY RESULTS")
    print(f"{'='*50}")
    print(f"Total questions:   {total}")
    print(f"Evaluated:         {len(valid)}")
    print(f"Failed (errors):   {failed}")
    print(f"Correct (1):       {correct_count}  ({correct_count/len(valid)*100:.1f}%)")
    print(f"Wrong   (0):       {wrong_count}  ({wrong_count/len(valid)*100:.1f}%)")
    print(f"ACCURACY:          {accuracy:.2f}%")
    print(f"Judge avg score:   {df_out['judge_overall_score'].mean():.3f}")
    print(f"{'='*50}")
    print(f"Saved to: {output_csv}")


if __name__ == "__main__":
    main()
