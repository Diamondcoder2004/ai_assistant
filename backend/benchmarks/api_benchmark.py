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
from pathlib import Path

# Принудительная установка UTF-8 для вывода в консоль Windows
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

TEST_FILES_DIR = Path("../tests") # Директория с тестовыми файлами
DEFAULT_TEST_FILE = Path(__file__).parent.parent.parent / "new_data" / "benchmark_dataset.csv"

ENABLE_JUDGE = True
JUDGE_MAX_RETRIES = 3
JUDGE_RETRY_DELAY = 5

DEFAULT_PARALLEL_REQUESTS = 4
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
            print(f"ATTEMPT {attempt + 1}/{JUDGE_MAX_RETRIES} for judge failed: {e}")
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
            "max_tokens": 2000
        }, headers=headers, timeout=180)
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

        answer = ""
        sources = []
        time_total = 0.0
        attempt = 0
        MAX_ERROR_RETRIES = 5   # Лимит для HTTP ошибок (rate limit и т.п.)
        MAX_EMPTY_RETRIES = 4   # Лимит для пустых ответов (бэкенд завис)

        # Retry:
        # - Пустой ответ → максимум MAX_EMPTY_RETRIES раз, потом пишем пустым
        # - HTTP/ERROR → максимум MAX_ERROR_RETRIES раз, потом пишем как есть
        while True:
            attempt += 1
            token = generate_jwt()
            try:
                answer, sources, time_total = await asyncio.to_thread(fetch_api_sync, question, token)
            except Exception as e:
                answer = f"ERROR: {e}"
                sources = []
                time_total = 0.0

            is_empty = not str(answer).strip()
            is_http_error = "HTTP_ERROR" in str(answer) or (str(answer).startswith("ERROR") and not is_empty)

            if not is_empty and not is_http_error:
                # Нормальный ответ
                break

            if is_empty and attempt >= MAX_EMPTY_RETRIES:
                print(f"  [Q{idx}] Giving up after {attempt} attempts (empty response), writing empty")
                break

            if is_http_error and attempt >= MAX_ERROR_RETRIES:
                print(f"  [Q{idx}] Giving up after {attempt} attempts: {str(answer)[:80]}")
                break

            delay = min(5 * (2 ** min(attempt - 1, 4)), 30)  # backoff: 5,10,20,30,30...
            print(f"  [Q{idx}] Attempt {attempt} failed ({str(answer)[:60]}), retry in {delay}s...")
            await asyncio.sleep(delay)

        is_bn = (answer.startswith("БН") or answer.startswith("Ничего не найдено"))
        is_failed = "HTTP_ERROR" in str(answer) or (str(answer).startswith("ERROR"))

        result = {
            "index": idx,
            "question": question,
            "expected": expected,
            "answer": normalize_text(answer),
            "time_total_sec": round(time_total, 3),
            "num_hits": len(sources),
            "sources": json.dumps(sources, ensure_ascii=False)
        }

        # LLM Judge оценка — retry до победного, но не более 10 попыток
        if ENABLE_JUDGE and answer and not is_bn and not is_failed:
            judge_result = None
            judge_attempt = 0
            while judge_result is None and judge_attempt < 10:
                judge_attempt += 1
                try:
                    judge_result = await asyncio.to_thread(
                        judge.evaluate,
                        question=question,
                        answer=answer,
                        expected=expected,
                        sources=sources
                    )
                except Exception as e:
                    delay = min(5 * (2 ** min(judge_attempt - 1, 5)), 60)
                    print(f"  [Q{idx}] Judge attempt {judge_attempt} failed: {e}, retry in {delay}s...")
                    await asyncio.sleep(delay)

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


async def main():
    global judge

    import argparse
    parser = argparse.ArgumentParser(description="API Benchmark с LLM Judge")
    parser.add_argument("--file", "-f", default=str(DEFAULT_TEST_FILE), help="Путь к тестовому файлу (JSON или CSV)")
    parser.add_argument("--limit", "-l", type=int, default=None, help="Ограничить количество вопросов")
    parser.add_argument("--batch-size", "-b", type=int, default=DEFAULT_BATCH_SIZE, help="Размер батча для параллельной обработки")
    parser.add_argument("--parallel", "-p", type=int, default=DEFAULT_PARALLEL_REQUESTS, help="Количество параллельных запросов")
    parser.add_argument("--cache", "-c", default=None, help="Путь к CSV с уже готовыми ответами (кэш).")
    parser.add_argument("--resume-dir", "-r", default=None, help="Продолжить бенчмарк в существующей папке: дописывает новые ответы в её results.csv, пропуская уже отвеченные вопросы.")
    args = parser.parse_args()

    print("=" * 60)
    print("STARTING API BENCHMARK WITH LLM JUDGE")
    print("=" * 60)

    test_file = Path(args.file)
    if not test_file.exists():
        print(f"ERROR: File {test_file} not found")
        return

    # Поддержка CSV и JSON
    if test_file.suffix.lower() == '.csv':
        df = pd.read_csv(test_file, encoding='utf-8')
        questions = df.to_dict(orient='records')
    elif test_file.suffix.lower() == '.json':
        with open(test_file, 'r', encoding='utf-8') as f:
            questions = json.load(f)
    else:
        print("ERROR: File format not supported. Use .csv or .json")
        return

    if args.limit:
        questions = questions[:args.limit]

    print(f"SUCCESS: Loaded {len(questions)} questions from {test_file}")

    # ===== ОПРЕДЕЛЯЕМ ПАПКУ ВЫВОДА =====
    BENCHMARK_ROOT.mkdir(exist_ok=True)
    if args.resume_dir:
        output_dir = Path(args.resume_dir)
        if not output_dir.exists():
            print(f"ERROR: --resume-dir папка не найдена: {output_dir}")
            return
        # Автоматически используем results.csv из этой папки как кэш
        auto_cache = output_dir / "results.csv"
        if auto_cache.exists() and not args.cache:
            args.cache = str(auto_cache)
        print(f"♻️  Режим продолжения: {output_dir}")
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = BENCHMARK_ROOT / f"api_benchmark_{timestamp}"
        output_dir.mkdir(exist_ok=True)

    print(f"📁 Результаты будут сохранены в: {output_dir}")

    # ===== КЭШИРУЕМ СТАРЫЕ РЕЗУЛЬТАТЫ =====
    cache: dict = {}  # question_text -> row dict
    if args.cache:
        cache_path = Path(args.cache)
        if cache_path.exists():
            try:
                cache_df = pd.read_csv(cache_path, encoding='utf-8-sig')
                for _, row in cache_df.iterrows():
                    q = str(row.get('question', '')).strip()
                    a = str(row.get('answer', '')).strip()
                    # Считаем ответ валидным если он непустой и не ERROR/HTTP_ERROR
                    if q and a and a != 'nan' and not a.startswith('ERROR') and not a.startswith('HTTP_ERROR'):
                        cache[q] = row.to_dict()
                print(f"✅ Кэш загружен: {len(cache)} готовых ответов из {cache_path.name}")
            except Exception as e:
                print(f"⚠️  Не удалось загрузить кэш: {e}")
        else:
            print(f"⚠️  Файл кэша не найден: {cache_path}")

    if ENABLE_JUDGE:
        print("Judge INITIALIZING...")
        judge = LLMJudge()
        print("Judge READY")

    token = generate_jwt()
    print("JWT token generated")

    all_columns = [
        "index", "question", "expected", "answer", "time_total_sec", "num_hits", "sources",
        "judge_relevance", "judge_completeness", "judge_helpfulness",
        "judge_clarity", "judge_hallucination_risk", 
        "judge_context_recall", "judge_faithfulness", "judge_currency", "judge_binary_correctness",
        "judge_overall_score", "judge_justification"
    ]

    results_csv_path = output_dir / "results.csv"

    # ===== ОПРЕДЕЛЯЕМ ЧТО УЖЕ ЗАПИСАНО В ФАЙЛ НА ДИСКЕ =====
    already_written: set = set()  # вопросы которые уже физически в файле
    if results_csv_path.exists() and args.resume_dir:
        try:
            existing_df = pd.read_csv(results_csv_path, encoding='utf-8-sig')
            for _, row in existing_df.iterrows():
                q = str(row.get('question', '')).strip()
                if q:
                    already_written.add(q)
            print(f"📋 В файле уже записано: {len(already_written)} строк")
        except Exception as e:
            print(f"⚠️  Не удалось прочитать существующий results.csv: {e}")

    # Создаём файл только если он не существует (не перезаписываем!)
    if not results_csv_path.exists():
        with open(results_csv_path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=all_columns, extrasaction='ignore')
            writer.writeheader()

    semaphore = asyncio.Semaphore(args.parallel)

    print(f"\n🚀 Запуск обращений к {API_BASE_URL} с батчем {args.batch_size} и параллелизмом {args.parallel}...")

    results = []
    cached_count = 0
    new_count = 0
    skipped_count = 0

    for i in range(0, len(questions), args.batch_size):
        batch = questions[i:i + args.batch_size]
        batch_results = []
        tasks_map = []  # (j, q) для вопросов без кэша

        for j, q in enumerate(batch):
            q_text = str(q.get('question') or q.get('Вопрос', '')).strip()
            if q_text in already_written:
                # Уже физически записано в файл — пропускаем
                skipped_count += 1
                batch_results.append(('skip', j, None))
            elif q_text in cache:
                # Есть в кэше но не записано — запишем
                cached_row = cache[q_text]
                result = {col: cached_row.get(col, '') for col in all_columns}
                result['index'] = i + j + 1
                batch_results.append(('cached', j, result))
                cached_count += 1
            else:
                tasks_map.append((j, q))
                new_count += 1

        # Обрабатываем только новые вопросы
        if tasks_map:
            tasks = [asyncio.create_task(process_question(q, i + j + 1, semaphore)) for j, q in tasks_map]
            new_results = await asyncio.gather(*tasks)
            for (j, _), res in zip(tasks_map, new_results):
                batch_results.append(('new', j, res))

        # Сортируем по оригинальному индексу в батче
        batch_results.sort(key=lambda x: x[1])
        ordered_results = [r for _, _, r in batch_results if r is not None]  # пропускаем skip
        results.extend(ordered_results)

        # Дозаписываем только не-skip строки
        rows_to_write = [r for t, _, r in batch_results if t != 'skip']
        if rows_to_write:
            with open(results_csv_path, 'a', encoding='utf-8-sig', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=all_columns, extrasaction='ignore')
                for res in rows_to_write:
                    writer.writerow(res)

        cached_in_batch = sum(1 for t, _, _ in batch_results if t == 'cached')
        new_in_batch = sum(1 for t, _, _ in batch_results if t == 'new')
        skip_in_batch = sum(1 for t, _, _ in batch_results if t == 'skip')
        if cached_in_batch + new_in_batch > 0 or skip_in_batch == 0:
            print(f"Batch {i+1}-{i+len(batch)} processed (кэш: {cached_in_batch}, новых: {new_in_batch}, пропущено: {skip_in_batch})")

    print(f"\n📊 Итого: {cached_count} из кэша, {new_count} новых запросов к API, {skipped_count} пропущено (уже в файле)")

    print(f"\nResults saved to {results_csv_path}")

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
        print(f"\nAPI ERRORS: {errors_count}")

    print("\n" + "=" * 60)
    print("BENCHMARK COMPLETED")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
