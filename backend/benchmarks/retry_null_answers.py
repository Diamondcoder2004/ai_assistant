#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для повторного запуска бенчмарка только для вопросов с null/пустыми ответами.
Читает results.csv из указанной директории, находит строки без ответов,
перезапускает бенчмарк для них и обновляет CSV.
"""

import asyncio
import json
import time
import os
import csv
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import jwt
import requests
import pandas as pd
from tqdm import tqdm

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)

sys.path.insert(0, str(Path(__file__).parent.parent))
from llm_judge import LLMJudge

# ================= НАСТРОЙКИ =================
API_BASE_URL = "http://localhost:8880"
JWT_SECRET = "gZPocVPGMFSqFDBQVkHaVlSGa0c5sqtX8KYtxkcF"
USER_ID = "a1527bad-f668-45b6-8aca-82bcafa00cd9"
USER_EMAIL = "sabitovalmaz965@gmail.ru"

ENABLE_JUDGE = True
JUDGE_MAX_RETRIES = 3
JUDGE_RETRY_DELAY = 5

DEFAULT_PARALLEL_REQUESTS = 4
DEFAULT_BATCH_SIZE = 10

ALL_COLUMNS = [
    "index", "question", "expected", "answer", "time_total_sec", "num_hits", "sources",
    "judge_relevance", "judge_completeness", "judge_helpfulness",
    "judge_clarity", "judge_hallucination_risk",
    "judge_context_recall", "judge_faithfulness", "judge_currency", "judge_binary_correctness",
    "judge_overall_score", "judge_justification"
]

judge = None


def generate_jwt() -> str:
    payload = {
        "iss": "supabase",
        "sub": USER_ID,
        "role": "authenticated",
        "email": USER_EMAIL,
        "iat": int(time.time()),
        "exp": int(time.time()) + 86400,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def normalize_text(text: str) -> str:
    if not text:
        return text
    text = str(text)
    text = text.replace('\u00A0', ' ').replace('\u200B', '').replace('\u202F', ' ')
    return ' '.join(text.split())


def is_null_answer(answer) -> bool:
    """Проверяет, является ли ответ null/пустым/ошибочным"""
    if answer is None:
        return True
    s = str(answer).strip()
    if s == '' or s.lower() == 'nan' or s.lower() == 'null':
        return True
    return False


def fetch_api_sync(query: str, token: str) -> Tuple[str, List[Dict], float]:
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    start = time.perf_counter()
    try:
        resp = requests.post(f"{API_BASE_URL}/query", json={
            "query": query,
            "k": 5,
            "max_tokens": 500
        }, headers=headers, timeout=120)
        end = time.perf_counter()

        if resp.status_code == 200:
            data = resp.json()
            answer = data.get("answer", "")
            sources = data.get("sources", [])

            if isinstance(sources, str):
                try:
                    sources = json.loads(sources)
                except:
                    sources = []

            return answer, sources, end - start
        else:
            return f"HTTP_ERROR_{resp.status_code}: {resp.text[:100]}", [], end - start
    except Exception as e:
        return f"ERROR: {e}", [], time.perf_counter() - start


async def judge_response(question: str, expected: str, actual: str, sources: List[Dict]) -> Optional[Dict[str, Any]]:
    if not judge:
        return None

    for attempt in range(JUDGE_MAX_RETRIES):
        try:
            evaluation = await asyncio.to_thread(judge.evaluate,
                                                 question=question,
                                                 answer=actual,
                                                 expected=expected,
                                                 sources=sources)
            return evaluation
        except Exception as e:
            print(f"ATTEMPT {attempt + 1}/{JUDGE_MAX_RETRIES} for judge failed: {e}")
            if attempt < JUDGE_MAX_RETRIES - 1:
                delay = JUDGE_RETRY_DELAY * (2 ** attempt)
                await asyncio.sleep(delay)
            else:
                return None
    return None


async def process_row(row: Dict[str, Any], semaphore: asyncio.Semaphore) -> Dict[str, Any]:
    async with semaphore:
        question = str(row.get("question", "")).strip()
        expected = str(row.get("expected", "")).strip()
        idx = row.get("index", "?")

        token = generate_jwt()

        try:
            answer, sources, time_total = await asyncio.to_thread(fetch_api_sync, question, token)

            # Повторная попытка при сетевой ошибке
            if "ERROR" in answer and "401" not in answer:
                print(f"  RETRY for question {idx}...")
                await asyncio.sleep(2)
                answer, sources, time_total = await asyncio.to_thread(fetch_api_sync, question, token)

            is_bn = (answer.startswith("БН") or
                     answer.startswith("Ничего не найдено") or
                     "HTTP_ERROR" in answer or "ERROR" in answer)

            result = dict(row)  # копируем оригинальную строку
            result["answer"] = normalize_text(answer)
            result["time_total_sec"] = round(time_total, 3)
            result["num_hits"] = len(sources)
            result["sources"] = json.dumps(sources, ensure_ascii=False)

            # LLM Judge оценка
            if ENABLE_JUDGE and answer and not is_bn:
                judge_result = await judge_response(question, expected, answer, sources)
                if judge_result:
                    result["judge_relevance"] = judge_result.relevance
                    result["judge_completeness"] = judge_result.completeness
                    result["judge_helpfulness"] = judge_result.helpfulness
                    result["judge_clarity"] = judge_result.clarity
                    result["judge_hallucination_risk"] = judge_result.hallucination_risk
                    result["judge_context_recall"] = judge_result.context_recall
                    result["judge_faithfulness"] = judge_result.faithfulness
                    result["judge_currency"] = judge_result.currency
                    result["judge_binary_correctness"] = judge_result.binary_correctness
                    result["judge_overall_score"] = judge_result.overall_score
                    result["judge_justification"] = normalize_text(judge_result.reasoning)

            print(f"  ✅ [{idx}] Done. Answer: {str(answer)[:60]}...")
            return result

        except Exception as e:
            print(f"\nERROR processing question {idx}: {e}")
            result = dict(row)
            result["answer"] = f"ERROR: {e}"
            result["time_total_sec"] = 0.0
            result["num_hits"] = 0
            return result


async def main():
    global judge

    import argparse
    parser = argparse.ArgumentParser(description="Retry null answers in benchmark results")
    parser.add_argument("--results", "-r", required=True, help="Путь к results.csv")
    parser.add_argument("--parallel", "-p", type=int, default=DEFAULT_PARALLEL_REQUESTS,
                        help="Количество параллельных запросов")
    parser.add_argument("--batch-size", "-b", type=int, default=DEFAULT_BATCH_SIZE)
    args = parser.parse_args()

    results_path = Path(args.results)
    if not results_path.exists():
        print(f"ERROR: File {results_path} not found")
        return

    print("=" * 60)
    print("RETRY NULL ANSWERS BENCHMARK")
    print("=" * 60)

    # Читаем CSV
    df = pd.read_csv(results_path, encoding='utf-8-sig')
    print(f"📄 Загружено {len(df)} строк из {results_path}")

    # Находим строки с null/пустыми ответами
    null_mask = df['answer'].apply(is_null_answer)
    null_df = df[null_mask].copy()
    print(f"🔍 Найдено {len(null_df)} строк с пустыми/null ответами")

    if len(null_df) == 0:
        print("✅ Нет строк для повторной обработки!")
        return

    # Список строк для повторной обработки
    null_rows = null_df.to_dict(orient='records')

    print(f"\nИндексы вопросов без ответа: {[r['index'] for r in null_rows[:20]]}{'...' if len(null_rows) > 20 else ''}")

    if ENABLE_JUDGE:
        print("\nJudge INITIALIZING...")
        judge = LLMJudge()
        print("Judge READY")

    semaphore = asyncio.Semaphore(args.parallel)

    print(f"\n🚀 Запуск повторных запросов к {API_BASE_URL}...")
    print(f"   Параллелизм: {args.parallel}, батч: {args.batch_size}")

    updated_rows = []
    for i in range(0, len(null_rows), args.batch_size):
        batch = null_rows[i:i + args.batch_size]
        tasks = [asyncio.create_task(process_row(row, semaphore)) for row in batch]
        batch_results = await asyncio.gather(*tasks)
        updated_rows.extend(batch_results)
        print(f"📦 Батч {i+1}-{i+len(batch)} обработан")

    # Обновляем DataFrame: заменяем строки с null ответами
    print(f"\n💾 Обновление результатов...")
    updated_dict = {int(r['index']): r for r in updated_rows}

    for i, row in df.iterrows():
        idx = int(row['index']) if not pd.isna(row['index']) else -1
        if idx in updated_dict:
            for col in ALL_COLUMNS:
                if col in updated_dict[idx]:
                    df.at[i, col] = updated_dict[idx][col]

    # Сохраняем обновленный CSV (перезаписываем оригинал)
    df.to_csv(results_path, index=False, encoding='utf-8-sig')
    print(f"✅ Обновлено {len(updated_rows)} строк. Файл сохранён: {results_path}")

    # Краткая статистика
    still_null = df['answer'].apply(is_null_answer).sum()
    print(f"\n📊 Итог:")
    print(f"  Всего строк: {len(df)}")
    print(f"  Успешно обработано: {len(updated_rows)}")
    print(f"  Ещё без ответа: {still_null}")

    if 'judge_overall_score' in df.columns:
        valid_scores = pd.to_numeric(df['judge_overall_score'], errors='coerce').dropna()
        if len(valid_scores) > 0:
            print(f"  Средний Judge Overall Score: {valid_scores.mean():.2f}")

    print("\n" + "=" * 60)
    print("RETRY COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
