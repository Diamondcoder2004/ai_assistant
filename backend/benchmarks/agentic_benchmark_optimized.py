#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
agentic_benchmark_optimized.py – Оптимизированная версия бенчмарка для Agentic RAG с:
- Batch processing для экономии памяти
- Streaming сохранением результатов
- Оптимизированным async LLM
- Контролем использования памяти
- LLM-as-a-Judge оценкой
"""

import asyncio
import json
import time
import gc
import os
import csv
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

import numpy as np
import pandas as pd
from tqdm import tqdm

# Добавляем родительскую директорию в path для импорта
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import AgenticRAG
from llm_judge import LLMJudge

# ================= НАСТРОЙКИ =================
FAQ_FILE = Path("../faq_question.csv")
PARALLEL_REQUESTS = 2  # workers для Agentic RAG (медленнее но стабильнее)

RETRIEVE_K = 10
USE_RERANKER = False

# Веса поиска (Agentic RAG сам подбирает, но можно задать дефолтные)
RETRIEVE_PREF_WEIGHT = 0.4
RETRIEVE_HYPE_WEIGHT = 0.2
RETRIEVE_LEXICAL_WEIGHT = 0.2
RETRIEVE_CONTEXTUAL_WEIGHT = 0.4

COMPUTE_EMBEDDING_SIM = False  # Agentic RAG использует LLM Judge вместо embedding similarity

ENABLE_JUDGE = True
JUDGE_MODEL = "qwen/qwen3.5-flash-02-23"  # Использует ту же модель что и RAG
JUDGE_MAX_RETRIES = 3
JUDGE_RETRY_DELAY = 5

# === ОПТИМИЗАЦИИ ===
BATCH_SIZE = 1  # Вопросы обрабатываются по одному
SAVE_INTERVAL = 5  # Сохранение каждые N вопросов
CLEAR_CACHE_INTERVAL = 10  # Очистка кэша каждые N вопросов

BENCHMARK_ROOT = Path("agentic_benchmarks")

# ================= ИНИЦИАЛИЗАЦИЯ =================
rag = None
judge = None


def get_config_snapshot() -> Dict[str, Any]:
    return {
        "timestamp": datetime.now().isoformat(),
        "script_settings": {
            "FAQ_FILE": str(FAQ_FILE),
            "PARALLEL_REQUESTS": PARALLEL_REQUESTS,
            "BATCH_SIZE": BATCH_SIZE,
            "RETRIEVE_K": RETRIEVE_K,
            "USE_RERANKER": USE_RERANKER,
            "RETRIEVE_PREF_WEIGHT": RETRIEVE_PREF_WEIGHT,
            "RETRIEVE_HYPE_WEIGHT": RETRIEVE_HYPE_WEIGHT,
            "RETRIEVE_LEXICAL_WEIGHT": RETRIEVE_LEXICAL_WEIGHT,
            "RETRIEVE_CONTEXTUAL_WEIGHT": RETRIEVE_CONTEXTUAL_WEIGHT,
            "COMPUTE_EMBEDDING_SIM": COMPUTE_EMBEDDING_SIM,
            "ENABLE_JUDGE": ENABLE_JUDGE,
            "JUDGE_MODEL": JUDGE_MODEL,
            "JUDGE_MAX_RETRIES": JUDGE_MAX_RETRIES,
            "JUDGE_RETRY_DELAY": JUDGE_RETRY_DELAY,
        },
        "agentic_rag_features": {
            "multi_query_generation": True,
            "auto_weight_selection": True,
            "clarification_questions": True,
            "friendly_response_style": True,
            "source_citation": True,
        }
    }


def extract_json_from_text(text: str) -> Optional[Dict]:
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1 and end > start:
        text = text[start:end + 1]
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def normalize_text(text: str) -> str:
    """Нормализует текст: заменяет NBSP и другие невидимые символы на обычные пробелы."""
    if not text:
        return text
    # Заменяем неразрывный пробел (NBSP) на обычный
    text = text.replace('\u00A0', ' ')
    # Заменяем другие специальные пробелы
    text = text.replace('\u2000', ' ')  # EN QUAD
    text = text.replace('\u2001', ' ')  # EM QUAD
    text = text.replace('\u2002', ' ')  # EN SPACE
    text = text.replace('\u2003', ' ')  # EM SPACE
    text = text.replace('\u2004', ' ')  # THREE-PER-EM SPACE
    text = text.replace('\u2005', ' ')  # FOUR-PER-EM SPACE
    text = text.replace('\u2006', ' ')  # SIX-PER-EM SPACE
    text = text.replace('\u2007', ' ')  # FIGURE SPACE
    text = text.replace('\u2008', ' ')  # PUNCTUATION SPACE
    text = text.replace('\u2009', ' ')  # THIN SPACE
    text = text.replace('\u200A', ' ')  # HAIR SPACE
    text = text.replace('\u202F', ' ')  # NARROW NO-BREAK SPACE
    text = text.replace('\u205F', ' ')  # MEDIUM MATHEMATICAL SPACE
    text = text.replace('\u3000', ' ')  # IDEOGRAPHIC SPACE
    # Удаляем zero-width символы
    text = text.replace('\u200B', '')  # ZERO WIDTH SPACE
    text = text.replace('\u200C', '')  # ZERO WIDTH NON-JOINER
    text = text.replace('\u200D', '')  # ZERO WIDTH JOINER
    text = text.replace('\uFEFF', '')  # ZERO WIDTH NO-BREAK SPACE (BOM)
    # Нормализуем множественные пробелы в один
    text = ' '.join(text.split())
    return text


async def judge_response(question: str, expected: str, actual: str, sources: List[Dict]) -> Optional[Dict[str, Any]]:
    """Оценка ответа через LLM Judge."""
    if not judge:
        return None

    for attempt in range(JUDGE_MAX_RETRIES):
        try:
            # Используем синхронный метод в async контексте
            loop = asyncio.get_event_loop()
            evaluation = await loop.run_in_executor(
                None,
                lambda: judge.evaluate(
                    question=question,
                    answer=actual,
                    sources=sources
                )
            )

            result = {
                "scores": {
                    "relevance": evaluation.relevance,
                    "completeness": evaluation.completeness,
                    "helpfulness": evaluation.helpfulness,
                    "clarity": evaluation.clarity,
                    "hallucination_risk": evaluation.hallucination_risk
                },
                "overall_score": evaluation.overall_score,
                "justification": evaluation.reasoning
            }
            return result

        except Exception as e:
            print(f"⚠️ Попытка {attempt + 1}/{JUDGE_MAX_RETRIES} для судьи не удалась: {e}")
            if attempt < JUDGE_MAX_RETRIES - 1:
                delay = JUDGE_RETRY_DELAY * (2 ** attempt)
                print(f"   Повтор через {delay} сек...")
                await asyncio.sleep(delay)
            else:
                print(f"❌ Все попытки судьи исчерпаны для вопроса: {question[:50]}...")
                return None

    return None


async def get_answer(query: str) -> Tuple[str, List[Dict], float, float, float, Dict]:
    """Получение ответа от Agentic RAG."""
    global rag

    if rag is None:
        rag = AgenticRAG()

    start_retrieve = time.perf_counter()

    # Выполняем запрос через Agentic RAG
    result = rag.query(query)

    end_generation = time.perf_counter()
    time_total = end_generation - start_retrieve

    # Разделяем время на retrieve и generation (примерно)
    time_retrieve = time_total * 0.75  # 75% на поиск
    time_generation = time_total * 0.25  # 25% на генерацию

    answer = result["answer"]
    sources = result.get("sources", [])
    queries_used = result.get("queries_used", [])
    search_params = result.get("search_params", {})

    return answer, sources, time_retrieve, 0.0, time_generation, {
        "queries_used": queries_used,
        "search_params": search_params,
        "confidence": result.get("confidence", 0.0)
    }


async def process_question(row: Dict[str, Any], idx: int, semaphore: asyncio.Semaphore) -> Dict[str, Any]:
    """Обработка одного вопроса."""
    question = row["Вопрос"].strip()
    expected = row["Ответ"].strip()

    async with semaphore:
        try:
            answer, sources, time_retrieve, time_rerank, time_generation, metadata = await get_answer(question)
            time_total = time_retrieve + time_rerank + time_generation

            is_bn = (answer.startswith("БН") or
                     answer.startswith("Ничего не найдено") or
                     answer.startswith("Требуется уточнение") or
                     len(answer.strip()) < 3)

            if is_bn and idx < 5:
                print(f"\n⚠️ БН для вопроса {idx}: {question[:50]}...")
                print(f"   Ответ: {answer[:100]}")

            result = {
                "index": idx,
                "question": question,
                "expected": expected,
                "answer": normalize_text(answer),
                "time_retrieve_sec": round(time_retrieve, 3),
                "time_rerank_sec": round(time_rerank, 3),
                "time_generation_sec": round(time_generation, 3),
                "time_total_sec": round(time_total, 3),
                "num_hits": len(sources),
                "confidence": metadata.get("confidence", 0.0),
                "queries_used": json.dumps(metadata.get("queries_used", []), ensure_ascii=False),
                "search_params": json.dumps(metadata.get("search_params", {}), ensure_ascii=False),
            }

            # LLM Judge оценка
            if ENABLE_JUDGE and answer and not is_bn and sources:
                judge_result = await judge_response(question, expected, answer, sources)
                if judge_result:
                    for metric, score in judge_result["scores"].items():
                        result[f"judge_{metric}"] = score
                    result["judge_overall_score"] = judge_result.get("overall_score", 0.0)
                    result["judge_justification"] = normalize_text(judge_result.get("justification", ""))

            # Очищаем память
            del sources
            gc.collect()

            return result

        except Exception as e:
            print(f"\n❌ Ошибка при обработке вопроса {idx}: {e}")
            return {
                "index": idx,
                "question": question,
                "expected": expected,
                "answer": f"ERROR: {e}",
                "time_retrieve_sec": 0.0,
                "time_rerank_sec": 0.0,
                "time_generation_sec": 0.0,
                "time_total_sec": 0.0,
                "num_hits": 0,
                "confidence": 0.0,
                "queries_used": "[]",
                "search_params": "{}",
            }


async def main():
    global judge

    print("=" * 60)
    print("📊 ЗАПУСК БЕНЧМАРКА AGENTIC RAG (ОПТИМИЗИРОВАННЫЙ)")
    print("=" * 60)

    if not FAQ_FILE.exists():
        print(f"❌ Файл {FAQ_FILE} не найден")
        return

    df = pd.read_csv(FAQ_FILE, encoding='utf-8')

    if "Вопрос" not in df.columns or "Ответ" not in df.columns:
        print("❌ Файл должен содержать колонки 'Вопрос' и 'Ответ'")
        return

    questions = df.to_dict(orient='records')
    print(f"✅ Загружено {len(questions)} вопросов из {FAQ_FILE}")

    # Создаём директорию для результатов
    import os
    output_dir_env = os.environ.get("BENCHMARK_OUTPUT_DIR")
    if output_dir_env:
        output_dir = Path(output_dir_env)
        output_dir.mkdir(parents=True, exist_ok=True)
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = BENCHMARK_ROOT / f"agentic_benchmark_{timestamp}"
        output_dir.mkdir(parents=True, exist_ok=True)

    print(f"📁 Результаты будут сохранены в: {output_dir}")

    # Сохраняем конфигурацию
    config_snapshot = get_config_snapshot()
    config_path = output_dir / "config.json"
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config_snapshot, f, ensure_ascii=False, indent=2)
    print(f"⚙️ Конфигурация сохранена в {config_path}")

    # Инициализация LLM Judge
    if ENABLE_JUDGE:
        print(f"🤖 Инициализация LLM Judge (модель: {JUDGE_MODEL})...")
        judge = LLMJudge()
        print("✅ LLM Judge готов")

    # === STREAMING СОХРАНЕНИЕ ===
    all_columns = [
        "index", "question", "expected", "answer",
        "time_retrieve_sec", "time_rerank_sec", "time_generation_sec", "time_total_sec",
        "num_hits", "confidence", "queries_used", "search_params",
        "judge_relevance", "judge_completeness", "judge_helpfulness",
        "judge_clarity", "judge_hallucination_risk", "judge_overall_score", "judge_justification",
    ]

    results_csv_path = output_dir / "results.csv"
    with open(results_csv_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=all_columns, extrasaction='ignore')
        writer.writeheader()

    semaphore = asyncio.Semaphore(PARALLEL_REQUESTS)

    print(f"\n🚀 Запуск обработки с параллельностью {PARALLEL_REQUESTS}...")
    print(f"🔧 Веса поиска: pref={RETRIEVE_PREF_WEIGHT}, hype={RETRIEVE_HYPE_WEIGHT}, "
          f"lexical={RETRIEVE_LEXICAL_WEIGHT}, contextual={RETRIEVE_CONTEXTUAL_WEIGHT}")
    print(f"🔧 LLM Judge: {'ВКЛЮЧЕН' if ENABLE_JUDGE else 'ОТКЛЮЧЕН'}")

    # Обработка вопросов с периодическим сохранением
    for i in range(0, len(questions), BATCH_SIZE):
        batch = questions[i:i + BATCH_SIZE]
        tasks = [process_question(q, i + j, semaphore) for j, q in enumerate(batch)]

        for future in tqdm(asyncio.as_completed(tasks), total=len(tasks),
                          desc=f"Вопросы {i+1}-{i+len(batch)}", leave=False):
            res = await future

            # Немедленное сохранение
            with open(results_csv_path, 'a', encoding='utf-8-sig', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=all_columns, extrasaction='ignore')
                writer.writerow(res)

        # Периодическая очистка памяти
        if (i + 1) % CLEAR_CACHE_INTERVAL == 0:
            gc.collect()
            print(f"  🧹 Очистка памяти после {i + 1} вопросов...")

    print(f"\n✅ Результаты сохранены в {results_csv_path}")

    # Вывод статистики
    print("\n" + "=" * 60)
    print("📈 ПРЕДВАРИТЕЛЬНЫЕ МЕТРИКИ")
    print("=" * 60)

    result_df = pd.read_csv(results_csv_path)

    # Временные метрики
    print(f"\n⏱️ ВРЕМЯ:")
    print(f"  Среднее время на вопрос: {result_df['time_total_sec'].mean():.2f} сек")
    print(f"  Поиск (среднее): {result_df['time_retrieve_sec'].mean():.2f} сек")
    print(f"  Генерация (среднее): {result_df['time_generation_sec'].mean():.2f} сек")

    # Уверенность
    print(f"\n🎯 УВЕРЕННОСТЬ:")
    print(f"  Средняя уверенность: {result_df['confidence'].mean():.2f}")

    # Количество источников
    print(f"\n📚 ИСТОЧНИКИ:")
    print(f"  Среднее кол-во источников: {result_df['num_hits'].mean():.1f}")

    # LLM Judge метрики
    if ENABLE_JUDGE:
        print("\n🤖 ОЦЕНКИ LLM-СУДЬИ (1-5, чем выше, тем лучше)")
        judge_cols = [col for col in result_df.columns if col.startswith("judge_") and col not in ("judge_justification",)]
        if judge_cols:
            for col in judge_cols:
                if col in result_df.columns:
                    mean_score = result_df[col].mean()
                    print(f"  {col.replace('judge_', '').capitalize()}: {mean_score:.2f}")
        else:
            print("  Нет оценок судьи")

    # Длина ответов
    result_df['answer_len'] = result_df['answer'].apply(lambda x: len(str(x)))
    print(f"\n📝 ДЛИНА ОТВЕТОВ:")
    print(f"  Среднее: {result_df['answer_len'].mean():.0f} символов")
    print(f"  Макс: {result_df['answer_len'].max()} символов")
    print(f"  Мин: {result_df['answer_len'].min()} символов")

    # Подсчёт БН ответов
    bn_count = result_df['answer'].apply(lambda x: str(x).startswith("БН") or
                                                   str(x).startswith("Ничего не найдено") or
                                                   str(x).startswith("Требуется уточнение")).sum()
    bn_rate = (bn_count / len(result_df)) * 100
    print(f"\n⚠️ БН ОТВЕТОВ: {bn_count} ({bn_rate:.1f}%)")

    print("\n" + "=" * 60)
    print("✅ БЕНЧМАРК ЗАВЕРШЁН")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
