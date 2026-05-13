"""
enrich_benchmark_components.py — дообогащение старого benchmark CSV per-component scores.

Для каждого вопроса из CSV:
1. Эмбедит запрос и ищет в Qdrant через SearchTool.search_multi()
2. Матчит найденные чанки с источниками из sources_json по chunk_id
3. Извлекает pref_score, hype_score, contextual_score, bm25_score из свежих результатов
4. Усредняет по всем матчнувшимся источникам
5. Сохраняет новый CSV с колонками cited_pref, cited_hype, cited_bm25, cited_contextual, cited_count

Запуск:
    cd backend
    python enrich_benchmark_components.py ../api_benchmarks/benchmark_20260513_001947.csv

Зависимости: pandas, tqdm (уже есть в requirements.txt)
"""

import json
import logging
import sys
from pathlib import Path

import pandas as pd
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).parent))
import config
from tools.search_tool import SearchTool


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("enrich")


def enrich_csv(input_csv: str, output_csv: str | None = None) -> None:
    """Читает CSV, дообогащает per-component scores, сохраняет новый CSV."""
    if output_csv is None:
        src = Path(input_csv)
        output_csv = str(src.parent / f"{src.stem}_enriched{src.suffix}")

    logger.info(f"Читаем CSV: {input_csv}")
    df = pd.read_csv(input_csv, encoding="utf-8-sig")
    logger.info(f"Загружено строк: {len(df)}")
    logger.info(f"Колонки: {list(df.columns)}")

    if "sources_json" not in df.columns:
        logger.error("Нет колонки sources_json — нечего обогащать.")
        sys.exit(1)

    # Инициализируем SearchTool
    logger.info("Инициализируем SearchTool (загрузка BM25, инициализация эмбеддера)...")
    tool = SearchTool()
    tool.load()
    logger.info("SearchTool готов.")

    # Новые колонки
    cited_pref = []
    cited_hype = []
    cited_bm25 = []
    cited_contextual = []
    cited_count = []

    for idx, row in tqdm(df.iterrows(), total=len(df), desc="Обогащение"):
        question = str(row.get("question", "")).strip()
        sources_raw = row.get("sources_json", "[]")

        if not question or not sources_raw or sources_raw == "[]":
            cited_pref.append(0.0)
            cited_hype.append(0.0)
            cited_bm25.append(0.0)
            cited_contextual.append(0.0)
            cited_count.append(0)
            continue

        # Парсим старые источники
        try:
            old_sources = json.loads(sources_raw)
        except (json.JSONDecodeError, TypeError):
            old_sources = []

        if not old_sources:
            cited_pref.append(0.0)
            cited_hype.append(0.0)
            cited_bm25.append(0.0)
            cited_contextual.append(0.0)
            cited_count.append(0)
            continue

        # Извлекаем parent prefix из старых источников.
        # chunk_id = "{md5}_p{N}" — матчим по MD5-префиксу, т.к. Qdrant мог
        # перезалиться с новыми _p{N} индексами, но MD5 от содержания тот же.
        old_prefixes = set()
        for s in old_sources:
            cid = str(s.get("chunk_id", "") or s.get("id", ""))
            if "_p" in cid:
                prefix = cid.split("_p")[0]
                if prefix:
                    old_prefixes.add(prefix)

        if not old_prefixes:
            cited_pref.append(0.0)
            cited_hype.append(0.0)
            cited_bm25.append(0.0)
            cited_contextual.append(0.0)
            cited_count.append(0)
            continue

        # Ищем в Qdrant
        try:
            results = tool.search_multi(queries=[question], k=20)
        except Exception as e:
            logger.warning(f"Ошибка поиска для строки {idx}: {e}")
            cited_pref.append(0.0)
            cited_hype.append(0.0)
            cited_bm25.append(0.0)
            cited_contextual.append(0.0)
            cited_count.append(0)
            continue

        if not results:
            cited_pref.append(0.0)
            cited_hype.append(0.0)
            cited_bm25.append(0.0)
            cited_contextual.append(0.0)
            cited_count.append(0)
            continue

        # Матчим по parent prefix chunk_id
        matched_scores = []
        for r in results:
            r_cid = str(r.metadata.get("chunk_id", "") or r.id)
            r_prefix = r_cid.split("_p")[0] if "_p" in r_cid else r_cid
            if r_prefix in old_prefixes:
                matched_scores.append({
                    "pref": r.metadata.get("pref_score", 0.0),
                    "hype": r.metadata.get("hype_score", 0.0),
                    "contextual": r.metadata.get("contextual_score", 0.0),
                    "bm25": r.metadata.get("bm25_score", 0.0),
                })

        if matched_scores:
            n = len(matched_scores)
            avg_pref = sum(m["pref"] for m in matched_scores) / n
            avg_hype = sum(m["hype"] for m in matched_scores) / n
            avg_bm25 = sum(m["bm25"] for m in matched_scores) / n
            avg_contextual = sum(m["contextual"] for m in matched_scores) / n
            cited_pref.append(round(avg_pref, 3))
            cited_hype.append(round(avg_hype, 3))
            cited_bm25.append(round(avg_bm25, 3))
            cited_contextual.append(round(avg_contextual, 3))
            cited_count.append(n)
        else:
            cited_pref.append(0.0)
            cited_hype.append(0.0)
            cited_bm25.append(0.0)
            cited_contextual.append(0.0)
            cited_count.append(0)

    df["cited_pref"] = cited_pref
    df["cited_hype"] = cited_hype
    df["cited_bm25"] = cited_bm25
    df["cited_contextual"] = cited_contextual
    df["cited_count"] = cited_count

    logger.info(f"\nСтатистика совпадений:")
    logger.info(f"  Среднее cited_count: {sum(cited_count) / max(len(cited_count), 1):.1f}")
    logger.info(f"  Макс cited_count: {max(cited_count)}")
    logger.info(f"  Строк с нулевым совпадением: {sum(1 for c in cited_count if c == 0)} / {len(cited_count)}")

    df.to_csv(output_csv, index=False, encoding="utf-8-sig")
    logger.info(f"\nСохранено: {output_csv}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python enrich_benchmark_components.py <benchmark.csv>")
        print("  На выходе: <benchmark>_enriched.csv")
        sys.exit(1)

    enrich_csv(sys.argv[1])
