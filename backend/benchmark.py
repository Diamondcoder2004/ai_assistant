"""
Benchmark для оценки качества Agentic RAG с загрузкой из CSV и LLM-as-a-Judge.
"""
import logging
import json
import os
import sys
import time
import csv
import shutil
import uuid
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
from dataclasses import dataclass, asdict

import pandas as pd
from tqdm import tqdm

import config
from main import AgenticRAG
from llm_judge import LLMJudge, LLMEvaluation
from utils.langfuse_tracer import observe_rag, get_langfuse_client

logging.basicConfig(
    level=logging.INFO,
    format=config.LOG_FORMAT,
    datefmt=config.LOG_DATE_FORMAT,
    handlers=[
        logging.FileHandler(config.LOGS_DIR / f"benchmark_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log", encoding="utf-8"),
        logging.StreamHandler(stream=open(os.devnull, 'w'))
    ]
)

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkSample:
    """Пример для бенчмарка."""
    id: int
    question: str
    expected_answer: str
    source_file: str = ""


@dataclass
class BenchmarkResult:
    """Результат бенчмарка."""
    sample_id: int
    question: str
    expected_answer: str
    source_file: str
    generated_answer: str
    queries_used: List[str]
    search_params: Dict[str, Any]
    sources: List[Dict[str, Any]]
    confidence: float
    retrieval_time: float
    generation_time: float
    total_time: float
    # LLM Judge оценки
    relevance_score: float = 0.0
    completeness_score: float = 0.0
    helpfulness_score: float = 0.0
    clarity_score: float = 0.0
    hallucination_risk: float = 0.0
    context_recall: float = 0.0
    faithfulness: float = 0.0
    currency: float = 0.0
    binary_correctness: int = 0
    overall_score: float = 0.0
    judge_reasoning: str = ""
    # Per-component scores (усреднённые по cited/использованным источникам)
    cited_pref: float = 0.0
    cited_hype: float = 0.0
    cited_bm25: float = 0.0
    cited_contextual: float = 0.0
    cited_count: int = 0


class AgenticRAGBenchmark:
    """Бенчмарк для оценки качества Agentic RAG."""

    CRITERIA = [
        "relevance", "completeness", "helpfulness", "clarity",
        "hallucination_risk", "context_recall", "faithfulness",
        "currency", "binary_correctness", "overall_score"
    ]

    def __init__(
        self,
        samples: List[BenchmarkSample],
        use_llm_judge: bool = True,
        skip_query_generator: bool = False,
    ):
        self.samples = samples
        self.rag = AgenticRAG()
        self.llm_judge = LLMJudge() if use_llm_judge else None
        self.use_llm_judge = use_llm_judge
        self.skip_query_generator = skip_query_generator
        self.results: List[BenchmarkResult] = []
        self.benchmark_run_id = uuid.uuid4().hex[:12]  # группы трасс в Langfuse
        self.langfuse_client = get_langfuse_client()   # None если Langfuse выключен
        logger.info(
            f"Benchmark: {len(samples)} примеров, "
            f"Judge={'ВКЛ' if use_llm_judge else 'ВЫКЛ'}, "
            f"Langfuse={'ВКЛ' if self.langfuse_client else 'ВЫКЛ'}"
        )

    @observe_rag(name="Benchmark.run")
    def run(self, output_dir: str = "api_benchmarks") -> pd.DataFrame:
        """Запуск бенчмарка — root trace в Langfuse."""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        logger.info(
            f"Benchmark run {self.benchmark_run_id}: {len(self.samples)} samples, "
            f"judge_model={config.JUDGE_LLM_MODEL}"
        )

        for sample in tqdm(self.samples, desc="Benchmark"):
            result = self._evaluate_sample(sample)
            self.results.append(result)

        # Сохранение результатов
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_df = self._to_dataframe()

        # CSV для совместимости с Excel (BOM + utf-8-sig)
        csv_path = output_path / f"benchmark_{timestamp}.csv"
        results_df.to_csv(csv_path, index=False, encoding="utf-8-sig")
        logger.info(f"CSV сохранён: {csv_path}")

        # Детальный JSON со всеми полями
        json_path = output_path / f"benchmark_{timestamp}.json"
        detailed = []
        for r in self.results:
            d = asdict(r)
            d["sources"] = r.sources  # сохраняем полные источники
            detailed.append(d)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(detailed, f, ensure_ascii=False, indent=2)

        # Статистика
        stats = self._calculate_stats()
        stats_path = output_path / f"stats_{timestamp}.json"
        with open(stats_path, "w", encoding="utf-8") as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)

        # Симлинк на latest
        latest_csv = output_path / "latest_results.csv"
        latest_stats = output_path / "latest_stats.json"
        try:
            if latest_csv.exists() or latest_csv.is_symlink():
                latest_csv.unlink()
            if latest_stats.exists() or latest_stats.is_symlink():
                latest_stats.unlink()
        except Exception:
            pass
        # Copy instead of symlink for Windows
        shutil.copy(csv_path, latest_csv)
        shutil.copy(stats_path, latest_stats)

        logger.info(f"Результаты сохранены в {output_path}")
        self._print_summary(stats)

        return results_df

    @observe_rag(name="Benchmark.evaluate")
    def _evaluate_sample(self, sample: BenchmarkSample) -> BenchmarkResult:
        """Оценка одного примера — дочерний span, RAG pipeline внутри как внуки."""
        start_time = time.time()

        self.rag.set_category("не известна")
        self.rag.reset_history()

        # Полный запрос через AgenticRAG.query() — включает Search + Response
        retrieval_start = time.time()
        try:
            response = self.rag.query(
                sample.question,
                auto_retry=True,
                skip_query_generator=self.skip_query_generator,
            )
        except Exception as e:
            logger.error(f"Ошибка запроса [{sample.id}]: {e}")
            return BenchmarkResult(
                sample_id=sample.id,
                question=sample.question,
                expected_answer=sample.expected_answer,
                source_file=sample.source_file,
                generated_answer=f"ERROR: {e}",
                queries_used=[],
                search_params={},
                sources=[],
                confidence=0.0,
                retrieval_time=0.0,
                generation_time=0.0,
                total_time=time.time() - start_time
            )
        total_time = time.time() - start_time

        # Приблизительно разделяем время
        retrieval_time = total_time * 0.6
        generation_time = total_time * 0.4

        answer = response.get("answer", "")
        sources = response.get("sources", [])
        queries = response.get("queries_used", [])
        search_params = response.get("search_params", {})
        confidence = response.get("confidence", 0.0)

        # Per-component scores: среднее только по cited/использованным источникам
        if sources:
            n = len(sources)
            cited_pref = sum(s.get("pref_score", 0.0) for s in sources) / n
            cited_hype = sum(s.get("hype_score", 0.0) for s in sources) / n
            cited_bm25 = sum(s.get("bm25_score", 0.0) for s in sources) / n
            cited_contextual = sum(s.get("contextual_score", 0.0) for s in sources) / n
            cited_count = n
        else:
            cited_pref = cited_hype = cited_bm25 = cited_contextual = 0.0
            cited_count = 0

        # LLM Judge
        llm_eval = None
        if self.use_llm_judge and self.llm_judge and answer and "ERROR:" not in answer:
            logger.info(f"  [Judge] Оценка #{sample.id}...")
            llm_eval = self.llm_judge.evaluate(
                question=sample.question,
                answer=answer,
                expected=sample.expected_answer,
                sources=sources
            )

        # Запись скоринга в Langfuse (трейс-уровень, уже внутри evaluate span)
        if self.langfuse_client and llm_eval:
            self._record_judge_scores(
                llm_eval, sample, answer, num_sources=len(sources),
                num_queries=len(queries), confidence=confidence
            )

        return BenchmarkResult(
            sample_id=sample.id,
            question=sample.question,
            expected_answer=sample.expected_answer,
            source_file=sample.source_file,
            generated_answer=answer,
            queries_used=queries,
            search_params=search_params,
            sources=sources,
            confidence=confidence,
            retrieval_time=retrieval_time,
            generation_time=generation_time,
            total_time=total_time,
            relevance_score=llm_eval.relevance if llm_eval else 0.0,
            completeness_score=llm_eval.completeness if llm_eval else 0.0,
            helpfulness_score=llm_eval.helpfulness if llm_eval else 0.0,
            clarity_score=llm_eval.clarity if llm_eval else 0.0,
            hallucination_risk=llm_eval.hallucination_risk if llm_eval else 0.0,
            context_recall=llm_eval.context_recall if llm_eval else 0.0,
            faithfulness=llm_eval.faithfulness if llm_eval else 0.0,
            currency=llm_eval.currency if llm_eval else 0.0,
            binary_correctness=llm_eval.binary_correctness if llm_eval else 0,
            overall_score=llm_eval.overall_score if llm_eval else 0.0,
            judge_reasoning=llm_eval.reasoning if llm_eval else "",
            cited_pref=round(cited_pref, 3),
            cited_hype=round(cited_hype, 3),
            cited_bm25=round(cited_bm25, 3),
            cited_contextual=round(cited_contextual, 3),
            cited_count=cited_count,
        )

    def _record_judge_scores(self, llm_eval, sample, answer, *,
                               num_sources=0, num_queries=0, confidence=0.0):
        """Запись всех скорингов LLM Judge в Langfuse — для текущего evaluate span."""
        client = self.langfuse_client
        if not client or not llm_eval:
            return

        try:
            # 9 критериев + overall
            score_defs = [
                ("judge_relevance",           llm_eval.relevance,           "NUMERIC"),
                ("judge_completeness",        llm_eval.completeness,        "NUMERIC"),
                ("judge_helpfulness",         llm_eval.helpfulness,         "NUMERIC"),
                ("judge_clarity",             llm_eval.clarity,             "NUMERIC"),
                ("judge_hallucination_risk",  llm_eval.hallucination_risk,  "NUMERIC"),
                ("judge_context_recall",      llm_eval.context_recall,      "NUMERIC"),
                ("judge_faithfulness",        llm_eval.faithfulness,        "NUMERIC"),
                ("judge_currency",            llm_eval.currency,            "NUMERIC"),
                ("judge_binary_correctness",  llm_eval.binary_correctness,  "NUMERIC"),
                ("judge_overall_score",       llm_eval.overall_score,       "NUMERIC"),
            ]

            for name, value, dtype in score_defs:
                client.score_current_span(
                    name=name,
                    value=float(value),
                    data_type=dtype,
                    comment=f"Q#{sample.id}: {sample.question[:120]}..."
                )

            # Метаданные спана
            client.update_current_span(metadata={
                "benchmark_run_id": self.benchmark_run_id,
                "sample_id": sample.id,
                "source_file": sample.source_file,
                "expected_answer": sample.expected_answer[:500],
                "num_sources": num_sources,
                "num_queries": num_queries,
                "confidence": round(confidence, 3),
                "answer_length": len(answer),
                "judge_model": config.JUDGE_LLM_MODEL,
            })

            logger.debug(f"Langfuse scoring OK for #{sample.id}")

        except Exception as e:
            logger.warning(f"Langfuse score failed for #{sample.id}: {e}")

    def _to_dataframe(self) -> pd.DataFrame:
        """DataFrame с плоскими полями."""
        rows = []
        for r in self.results:
            row = {
                "id": r.sample_id,
                "question": r.question,
                "expected": r.expected_answer,
                "source_file": r.source_file,
                "answer": r.generated_answer[:3000],
                "time_total_sec": round(r.total_time, 3),
                "num_hits": len(r.sources),
                "queries": " | ".join(r.queries_used),
                "sources_json": json.dumps(r.sources, ensure_ascii=False),
                "confidence": round(r.confidence, 3),
                "cited_pref": round(r.cited_pref, 3),
                "cited_hype": round(r.cited_hype, 3),
                "cited_bm25": round(r.cited_bm25, 3),
                "cited_contextual": round(r.cited_contextual, 3),
                "cited_count": r.cited_count,
            }
            if self.use_llm_judge:
                row.update({
                    "judge_relevance": r.relevance_score,
                    "judge_completeness": r.completeness_score,
                    "judge_helpfulness": r.helpfulness_score,
                    "judge_clarity": r.clarity_score,
                    "judge_hallucination_risk": r.hallucination_risk,
                    "judge_context_recall": r.context_recall,
                    "judge_faithfulness": r.faithfulness,
                    "judge_currency": r.currency,
                    "judge_binary_correctness": r.binary_correctness,
                    "judge_overall_score": round(r.overall_score, 2),
                    "judge_reasoning": r.judge_reasoning[:500],
                })
            rows.append(row)
        return pd.DataFrame(rows)

    def _calculate_stats(self) -> Dict[str, Any]:
        """Сводная статистика."""
        if not self.results:
            return {}

        n = len(self.results)
        valid = [r for r in self.results if "ERROR:" not in r.generated_answer and r.generated_answer != "Требуется уточнение"]
        errors = n - len(valid)

        stats = {
            "timestamp": datetime.now().isoformat(),
            "total_samples": n,
            "valid_samples": len(valid),
            "errors": errors,
            "avg_total_time_sec": round(sum(r.total_time for r in valid) / max(len(valid), 1), 2),
            "avg_retrieval_time_sec": round(sum(r.retrieval_time for r in valid) / max(len(valid), 1), 2),
            "avg_generation_time_sec": round(sum(r.generation_time for r in valid) / max(len(valid), 1), 2),
            "avg_confidence": round(sum(r.confidence for r in valid) / max(len(valid), 1), 3),
            "avg_queries": round(sum(len(r.queries_used) for r in valid) / max(len(valid), 1), 1),
            "avg_sources": round(sum(len(r.sources) for r in valid) / max(len(valid), 1), 1),
        }

        if self.use_llm_judge:
            judged = [r for r in valid if r.overall_score > 0]
            if judged:
                jn = len(judged)
                stats.update({
                    "judge_evaluated": jn,
                    "judge_avg_relevance": round(sum(r.relevance_score for r in judged) / jn, 2),
                    "judge_avg_completeness": round(sum(r.completeness_score for r in judged) / jn, 2),
                    "judge_avg_helpfulness": round(sum(r.helpfulness_score for r in judged) / jn, 2),
                    "judge_avg_clarity": round(sum(r.clarity_score for r in judged) / jn, 2),
                    "judge_avg_hallucination_risk": round(sum(r.hallucination_risk for r in judged) / jn, 2),
                    "judge_avg_context_recall": round(sum(r.context_recall for r in judged) / jn, 2),
                    "judge_avg_faithfulness": round(sum(r.faithfulness for r in judged) / jn, 2),
                    "judge_avg_currency": round(sum(r.currency for r in judged) / jn, 2),
                    "judge_avg_binary_correctness": round(sum(r.binary_correctness for r in judged) / jn, 2),
                    "judge_avg_overall": round(sum(r.overall_score for r in judged) / jn, 2),
                    "judge_binary_rate": f"{round(sum(r.binary_correctness for r in judged) / jn * 100, 1)}%",
                })

        return stats

    def _print_summary(self, stats: Dict[str, Any]):
        """Вывод сводки в консоль (без emoji для Windows-совместимости)."""
        print("\n" + "=" * 60)
        print("BENCHMARK RESULTS")
        print("=" * 60)
        print(f"Samples:          {stats.get('total_samples', 0)}")
        print(f"Successful:       {stats.get('valid_samples', 0)}")
        print(f"Errors:           {stats.get('errors', 0)}")
        print(f"Avg total time:   {stats.get('avg_total_time_sec', 0)}s")
        print(f"  Retriever:      {stats.get('avg_retrieval_time_sec', 0)}s")
        print(f"  Generation:     {stats.get('avg_generation_time_sec', 0)}s")
        print(f"Avg queries:      {stats.get('avg_queries', 0)}")
        print(f"Avg sources:      {stats.get('avg_sources', 0)}")

        if stats.get("judge_evaluated"):
            print("\n-- LLM JUDGE --")
            print(f"  Evaluated:     {stats.get('judge_evaluated', 0)}")
            print(f"  Relevance:     {stats.get('judge_avg_relevance', 0)} / 5")
            print(f"  Completeness:  {stats.get('judge_avg_completeness', 0)} / 5")
            print(f"  Helpfulness:   {stats.get('judge_avg_helpfulness', 0)} / 5")
            print(f"  Clarity:       {stats.get('judge_avg_clarity', 0)} / 5")
            print(f"  Hallucination: {stats.get('judge_avg_hallucination_risk', 0)} / 5")
            print(f"  ContextRecall: {stats.get('judge_avg_context_recall', 0)} / 5")
            print(f"  Faithfulness:  {stats.get('judge_avg_faithfulness', 0)} / 5")
            print(f"  Currency:      {stats.get('judge_avg_currency', 0)} / 5")
            print(f"  Binary OK:     {stats.get('judge_binary_rate', 'N/A')}")
            print(f"  Overall:       {stats.get('judge_avg_overall', 0)} / 5")
        print("=" * 60)


def load_benchmark_csv(filepath: str, limit: int = 0) -> List[BenchmarkSample]:
    """Загрузка примеров из CSV с колонками: question, expected_answer, source_file."""
    samples = []
    filepath = Path(filepath)

    with open(filepath, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            question = row.get("question", "").strip()
            expected = row.get("expected_answer", "").strip()
            source_file = row.get("source_file", "").strip()

            if not question:
                continue

            samples.append(BenchmarkSample(
                id=i + 1,
                question=question,
                expected_answer=expected,
                source_file=source_file
            ))

            if limit > 0 and len(samples) >= limit:
                break

    logger.info(f"Загружено {len(samples)} примеров из {filepath}")
    return samples


def main():
    """Точка входа."""
    import argparse

    parser = argparse.ArgumentParser(description="Benchmark Agentic RAG с LLM Judge")
    parser.add_argument("--csv", default="new_data/benchmark_dataset.csv",
                        help="CSV с примерами (question, expected_answer, source_file)")
    parser.add_argument("--output", "-o", default="api_benchmarks",
                        help="Директория для результатов")
    parser.add_argument("--limit", type=int, default=0,
                        help="Ограничить количество примеров (0 = все)")
    parser.add_argument("--no-judge", action="store_true",
                        help="Без LLM Judge")

    parser.add_argument("--no-query-gen", action="store_true",
                        help="Отключить QueryGenerator (по умолчанию включён)")
    parser.add_argument("--no-safety", action="store_true",
                        help="Отключить safety-фичи (relevance filter, adaptive BM25, regulatory boost, source quality)")

    args = parser.parse_args()

    # Apply --no-safety: disable all Phase 2/3 features to replicate April baseline
    if args.no_safety:
        import tools.relevance_filter as rf
        rf.MIN_OVERLAP = 0
        config.ADAPTIVE_BM25_BOOST = False
        config.REGULATORY_QUERY_BOOST = False
        config.SOURCE_QUALITY_THRESHOLD = 0.0
        logger.info("--no-safety: relevance filter, adaptive BM25, regulatory boost, source quality DISABLED")

    csv_path = Path(args.csv)
    if not csv_path.exists():
        # Ищем относительно backend/
        csv_path = Path("..") / args.csv
    if not csv_path.exists():
        print(f"[ERROR] CSV не найден: {args.csv}")
        return

    samples = load_benchmark_csv(str(csv_path), limit=args.limit)
    if not samples:
        print("[ERROR] Нет примеров для бенчмарка")
        return

    use_judge = not args.no_judge
    benchmark = AgenticRAGBenchmark(
        samples,
        use_llm_judge=use_judge,
        skip_query_generator=args.no_query_gen,
    )
    benchmark.run(output_dir=args.output)


if __name__ == "__main__":
    main()
