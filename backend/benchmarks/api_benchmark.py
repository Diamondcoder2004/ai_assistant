#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Бенчмарк для тестирования API системы через LLM-as-a-Judge.
Читает вопросы из директории с тестовыми файлами (JSON/CSV),
отправляет запросы к API и оценивает качество ответов с помощью LLM Judge.
"""

import asyncio
import json
import time
import os
import csv
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import jwt
import requests

import pandas as pd
from tqdm import tqdm

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from llm_judge import LLMJudge

# ================= НАСТРОЙКИ =================
API_BASE_URL = "http://localhost:8880"
JWT_SECRET = "gZPocVPGMFSqFDBQVkHaVlSGa0c5sqtX8KYtxkcF"
USER_ID = "a1527bad-f668-45b6-8aca-82bcafa00cd9"
USER_EMAIL = "sabitovalmaz965@gmail.ru"

TEST_FILES_DIR = Path("../tests") # Директория с тестовыми файлами
DEFAULT_TEST_FILE = Path(__file__).parent.parent.parent / "new_data" / "benchmark_dataset.csv"

ENABLE_JUDGE = True
JUDGE_MAX_RETRIES = 3
JUDGE_RETRY_DELAY = 5

DEFAULT_PARALLEL_REQUESTS = 2
DEFAULT_BATCH_SIZE = 10

BENCHMARK_ROOT = Path("api_benchmarks")

judge = None

def generate_jwt() -> str:
    payload = {
        "iss": "supabase",
        "sub": USER_ID,
        "role": "authenticated",
        "email": USER_EMAIL,
        "iat": int(time.time()),
        "exp": int(time.time()) + 86400, # 24 часа
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def normalize_text(text: str) -> str:
    if not text:
        return text
    text = str(text)
    text = text.replace('\u00A0', ' ').replace('\u200B', '').replace('\u202F', ' ')
    return ' '.join(text.split())

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
            print(f"⚠️ Попытка {attempt + 1}/{JUDGE_MAX_RETRIES} для судьи не удалась: {e}")
            if attempt < JUDGE_MAX_RETRIES - 1:
                delay = JUDGE_RETRY_DELAY * (2 ** attempt)
                await asyncio.sleep(delay)
            else:
                return None
    return None

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

async def process_question(row: Dict[str, Any], idx: int, semaphore: asyncio.Semaphore) -> Dict[str, Any]:
    async with semaphore:
        question = row.get("question") or row.get("Вопрос", "")
        expected = row.get("expected_answer") or row.get("Ответ", "")
        
        # Генерируем свежий токен для каждого запроса
        token = generate_jwt()
        
        try:
            answer, sources, time_total = await asyncio.to_thread(fetch_api_sync, question, token)
            
            # Повторная попытка при сетевой ошибке (не 401)
            if "ERROR" in answer and "401" not in answer:
                print(f"⚠️ Повторная попытка для вопроса {idx}...")
                await asyncio.sleep(2)
                answer, sources, time_total = await asyncio.to_thread(fetch_api_sync, question, token)

            is_bn = (answer.startswith("БН") or
                     answer.startswith("Ничего не найдено") or
                     "HTTP_ERROR" in answer or "ERROR" in answer)
            result = {
                "index": idx,
                "question": question,
                "expected": expected,
                "answer": normalize_text(answer),
                "time_total_sec": round(time_total, 3),
                "num_hits": len(sources),
                "sources": json.dumps(sources, ensure_ascii=False)
            }
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
            return result
        except Exception as e:
            print(f"\n❌ Ошибка при обработке вопроса {idx}: {e}")
            return {
                "index": idx,
                "question": question,
                "expected": expected,
                "answer": f"ERROR: {e}",
                "time_total_sec": 0.0,
                "num_hits": 0,
            }

async def main():
    global judge

    import argparse
    parser = argparse.ArgumentParser(description="API Benchmark с LLM Judge")
    parser.add_argument("--file", "-f", default=str(DEFAULT_TEST_FILE), help="Путь к тестовому файлу (JSON или CSV)")
    parser.add_argument("--limit", "-l", type=int, default=None, help="Ограничить количество вопросов")
    parser.add_argument("--batch-size", "-b", type=int, default=DEFAULT_BATCH_SIZE, help="Размер батча для параллельной обработки")
    parser.add_argument("--parallel", "-p", type=int, default=DEFAULT_PARALLEL_REQUESTS, help="Количество параллельных запросов")
    args = parser.parse_args()

    print("=" * 60)
    print("📊 ЗАПУСК БЕНЧМАРКА ЧЕРЕЗ API С LLM JUDGE")
    print("=" * 60)

    test_file = Path(args.file)
    if not test_file.exists():
        print(f"❌ Файл {test_file} не найден")
        return

    # Поддержка CSV и JSON
    if test_file.suffix.lower() == '.csv':
        df = pd.read_csv(test_file, encoding='utf-8')
        questions = df.to_dict(orient='records')
    elif test_file.suffix.lower() == '.json':
        with open(test_file, 'r', encoding='utf-8') as f:
            questions = json.load(f)
    else:
        print("❌ Формат файла не поддерживается. Нужен .csv или .json")
        return

    if args.limit:
        questions = questions[:args.limit]

    print(f"✅ Загружено {len(questions)} вопросов из {test_file}")

    BENCHMARK_ROOT.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = BENCHMARK_ROOT / f"api_benchmark_{timestamp}"
    output_dir.mkdir(exist_ok=True)

    print(f"📁 Результаты будут сохранены в: {output_dir}")

    if ENABLE_JUDGE:
        print(f"🤖 Инициализация LLM Judge...")
        judge = LLMJudge()
        print("✅ LLM Judge готов")

    token = generate_jwt()
    print("🔑 JWT токен сгенерирован")

    all_columns = [
        "index", "question", "expected", "answer", "time_total_sec", "num_hits", "sources",
        "judge_relevance", "judge_completeness", "judge_helpfulness",
        "judge_clarity", "judge_hallucination_risk", 
        "judge_context_recall", "judge_faithfulness", "judge_currency", "judge_binary_correctness",
        "judge_overall_score", "judge_justification"
    ]

    results_csv_path = output_dir / "results.csv"
    with open(results_csv_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=all_columns, extrasaction='ignore')
        writer.writeheader()

    semaphore = asyncio.Semaphore(args.parallel)

    print(f"\n🚀 Запуск обращений к {API_BASE_URL} с батчем {args.batch_size} и параллелизмом {args.parallel}...")

    results = []
    for i in range(0, len(questions), args.batch_size):
        batch = questions[i:i + args.batch_size]
        tasks = [asyncio.create_task(process_question(q, i + j + 1, semaphore)) for j, q in enumerate(batch)]

        batch_results = await asyncio.gather(*tasks)
        results.extend(batch_results)

        with open(results_csv_path, 'a', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=all_columns, extrasaction='ignore')
            for res in batch_results:
                writer.writerow(res)

        print(f"✅ Обработан батч {i+1}-{i+len(batch)}")

    print(f"\n✅ Результаты сохранены в {results_csv_path}")

    # Статистика
    print("\n" + "=" * 60)
    print("📈 ПРЕДВАРИТЕЛЬНЫЕ МЕТРИКИ")
    print("=" * 60)

    result_df = pd.DataFrame(results)

    print(f"\n⏱️ ВРЕМЯ:")
    print(f"  Среднее время ответа API: {result_df['time_total_sec'].mean():.2f} сек")

    if ENABLE_JUDGE:
        print("\n🤖 ОЦЕНКИ LLM-СУДЬИ (1-5, чем выше, тем лучше)")
        judge_cols = [col for col in result_df.columns if col.startswith("judge_") and col != "judge_justification"]
        if judge_cols:
            for col in judge_cols:
                if col in result_df.columns:
                    mean_score = result_df[col].mean()
                    print(f"  {col.replace('judge_', '').capitalize()}: {mean_score:.2f}")

    errors_count = result_df['answer'].apply(lambda x: str(x).startswith("ERROR") or str(x).startswith("HTTP")).sum()
    if errors_count > 0:
        print(f"\n❌ ОШИБОК API: {errors_count}")

    print("\n" + "=" * 60)
    print("✅ БЕНЧМАРК ЗАВЕРШЁН")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
