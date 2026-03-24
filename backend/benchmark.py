"""
Benchmark для оценки качества Agentic RAG
"""
import logging
import json
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
from dataclasses import dataclass, asdict

import pandas as pd
from tqdm import tqdm

import config
from main import AgenticRAG
from llm_judge import LLMJudge, LLMEvaluation

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format=config.LOG_FORMAT,
    datefmt=config.LOG_DATE_FORMAT,
    handlers=[
        logging.FileHandler(config.LOGS_DIR / f"benchmark_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkSample:
    """Пример для бенчмарка."""
    id: int
    question: str
    expected_answer: str  # эталонный ответ
    expected_sources: List[str]  # ожидаемые документы
    category: str = "не известна"


@dataclass
class BenchmarkResult:
    """Результат бенчмарка."""
    sample_id: int
    question: str
    generated_answer: str
    queries_used: List[str]
    search_params: Dict[str, Any]
    sources: List[Dict[str, Any]]
    confidence: float
    retrieval_time: float
    generation_time: float
    total_time: float
    # Метрики (заполняются отдельно)
    relevance_score: float = 0.0
    completeness_score: float = 0.0
    hallucination_risk: float = 0.0
    source_accuracy: float = 0.0


class AgenticRAGBenchmark:
    """
    Бенчмарк для оценки качества Agentic RAG.

    Метрики:
    - Relevance (релевантность ответа)
    - Completeness (полнота ответа)
    - Helpfulness (полезность)
    - Clarity (ясность)
    - Hallucination Risk (риск галлюцинаций)
    - Source Accuracy (точность источников)
    - Время выполнения
    """

    def __init__(self, samples: List[BenchmarkSample], use_llm_judge: bool = True):
        self.samples = samples
        self.rag = AgenticRAG()
        self.llm_judge = LLMJudge() if use_llm_judge else None
        self.use_llm_judge = use_llm_judge
        self.results: List[BenchmarkResult] = []
        logger.info(f"Benchmark инициализирован: {len(samples)} примеров")
        if use_llm_judge:
            logger.info("LLM Judge: ВКЛЮЧЕН")
        else:
            logger.info("LLM Judge: ОТКЛЮЧЕН")
    
    def run(self, output_dir: str = "results") -> pd.DataFrame:
        """
        Запуск бенчмарка.
        
        Args:
            output_dir: Директория для сохранения результатов
        
        Returns:
            DataFrame с результатами
        """
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        logger.info(f"Запуск бенчмарка на {len(self.samples)} примерах...")
        
        for sample in tqdm(self.samples, desc="Benchmark"):
            result = self._evaluate_sample(sample)
            self.results.append(result)
        
        # Сохранение результатов
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_df = self._to_dataframe()
        results_df.to_csv(output_path / f"results_{timestamp}.csv", index=False)
        
        # Статистика
        stats = self._calculate_stats()
        with open(output_path / f"stats_{timestamp}.json", "w", encoding="utf-8") as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Результаты сохранены в {output_path}")
        self._print_summary(stats)
        
        return results_df
    
    def _evaluate_sample(self, sample: BenchmarkSample) -> BenchmarkResult:
        """Оценка одного примера."""
        start_time = time.time()

        # Установка категории
        self.rag.set_category(sample.category)

        # Выполнение запроса
        retrieval_start = time.time()
        search_result = self.rag.search_agent.search(
            user_query=sample.question,
            history="",
            category=sample.category
        )
        retrieval_time = time.time() - retrieval_start

        # Проверка необходимости уточнения
        if search_result["clarification_needed"]:
            return BenchmarkResult(
                sample_id=sample.id,
                question=sample.question,
                generated_answer="Требуется уточнение",
                queries_used=[],
                search_params=search_result.get("search_params", {}),
                sources=[],
                confidence=0.0,
                retrieval_time=retrieval_time,
                generation_time=0.0,
                total_time=time.time() - start_time
            )

        # Генерация ответа
        generation_start = time.time()
        response_result = self.rag.response_agent.generate_response(
            user_query=sample.question,
            search_results=search_result["results"],
            history=""
        )
        generation_time = time.time() - generation_start

        total_time = time.time() - start_time

        # LLM Judge оценка
        llm_eval = None
        if self.use_llm_judge and self.llm_judge:
            logger.info("  [LLM Judge] Оценивает ответ...")
            llm_eval = self.llm_judge.evaluate(
                question=sample.question,
                answer=response_result["answer"],
                sources=response_result["sources"]
            )

        # Формирование результата
        return BenchmarkResult(
            sample_id=sample.id,
            question=sample.question,
            generated_answer=response_result["answer"],
            queries_used=search_result["queries_used"],
            search_params=search_result.get("search_params", {}),
            sources=response_result["sources"],
            confidence=response_result["confidence"],
            retrieval_time=retrieval_time,
            generation_time=generation_time,
            total_time=total_time,
            # LLM оценки
            relevance_score=llm_eval.relevance if llm_eval else 0.0,
            completeness_score=llm_eval.completeness if llm_eval else 0.0,
            hallucination_risk=llm_eval.hallucination_risk if llm_eval else 0.0
        )
    
    def _to_dataframe(self) -> pd.DataFrame:
        """Преобразование результатов в DataFrame."""
        data = []
        for r in self.results:
            data.append(asdict(r))
        return pd.DataFrame(data)
    
    def _calculate_stats(self) -> Dict[str, Any]:
        """Расчёт статистики."""
        if not self.results:
            return {}

        total_time = sum(r.total_time for r in self.results)
        retrieval_time = sum(r.retrieval_time for r in self.results)
        generation_time = sum(r.generation_time for r in self.results)

        # LLM Judge метрики (только для оценённых результатов)
        llm_results = [r for r in self.results if r.relevance_score > 0]
        
        stats = {
            "total_samples": len(self.results),
            "total_time_sec": total_time,
            "avg_time_sec": total_time / len(self.results),
            "avg_retrieval_time_sec": retrieval_time / len(self.results),
            "avg_generation_time_sec": generation_time / len(self.results),
            "avg_confidence": sum(r.confidence for r in self.results) / len(self.results),
            "clarification_count": sum(1 for r in self.results if r.generated_answer == "Требуется уточнение"),
            "avg_queries_per_request": sum(len(r.queries_used) for r in self.results) / len(self.results),
            "avg_sources_per_request": sum(len(r.sources) for r in self.results) / len(self.results),
        }
        
        # Добавляем LLM метрики если есть оценки
        if llm_results:
            stats.update({
                "llm_judge_enabled": self.use_llm_judge,
                "llm_evaluated_count": len(llm_results),
                "avg_relevance_score": sum(r.relevance_score for r in llm_results) / len(llm_results),
                "avg_completeness_score": sum(r.completeness_score for r in llm_results) / len(llm_results),
                "avg_hallucination_risk": sum(r.hallucination_risk for r in llm_results) / len(llm_results),
                "avg_llm_overall_score": (
                    sum(r.relevance_score + r.completeness_score + r.hallucination_risk 
                        for r in llm_results) / (3 * len(llm_results))
                )
            })
        
        return stats

    def _print_summary(self, stats: Dict[str, Any]):
        """Вывод сводки."""
        print("\n" + "=" * 60)
        print("📊 СВОДКА БЕНЧМАРКА")
        print("=" * 60)

        print(f"Всего примеров: {stats.get('total_samples', 0)}")
        print(f"Общее время: {stats.get('total_time_sec', 0):.2f} сек")
        print(f"Среднее время на запрос: {stats.get('avg_time_sec', 0):.2f} сек")
        print(f"  - Поиск: {stats.get('avg_retrieval_time_sec', 0):.2f} сек")
        print(f"  - Генерация: {stats.get('avg_generation_time_sec', 0):.2f} сек")
        print(f"Средняя уверенность: {stats.get('avg_confidence', 0):.2f}")
        print(f"Запросов на уточнение: {stats.get('clarification_count', 0)}")
        print(f"Среднее кол-во поисковых запросов: {stats.get('avg_queries_per_request', 0):.1f}")
        print(f"Среднее кол-во источников: {stats.get('avg_sources_per_request', 0):.1f}")
        
        # LLM Judge метрики
        if stats.get("llm_judge_enabled"):
            print("\n🤖 LLM JUDGE ОЦЕНКИ:")
            print(f"  Оценено ответов: {stats.get('llm_evaluated_count', 0)}")
            print(f"  📌 Relevance (релевантность): {stats.get('avg_relevance_score', 0):.2f} / 5")
            print(f"  📋 Completeness (полнота): {stats.get('avg_completeness_score', 0):.2f} / 5")
            print(f"  ⚠️ Hallucination Risk (1=высокий, 5=низкий): {stats.get('avg_hallucination_risk', 0):.2f} / 5")
            print(f"  🎯 Общая оценка LLM: {stats.get('avg_llm_overall_score', 0):.2f} / 5")

        print("=" * 60)


def load_benchmark_samples(filepath: str) -> List[BenchmarkSample]:
    """
    Загрузка примеров для бенчмарка из JSON.
    
    Формат файла:
    [
      {
        "id": 1,
        "question": "Как подать заявку на подключение?",
        "expected_answer": "...",
        "expected_sources": ["документ1", "документ2"],
        "category": "физическое лицо"
      }
    ]
    """
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    samples = []
    for item in data:
        samples.append(BenchmarkSample(
            id=item["id"],
            question=item["question"],
            expected_answer=item.get("expected_answer", ""),
            expected_sources=item.get("expected_sources", []),
            category=item.get("category", "не известна")
        ))
    
    return samples


def create_default_samples() -> List[BenchmarkSample]:
    """Создание дефолтных примеров для тестирования."""
    return [
        BenchmarkSample(
            id=1,
            question="Как подать заявку на технологическое присоединение?",
            expected_answer="Для подачи заявки на технологическое присоединение необходимо...",
            expected_sources=["Постановление 861", "Правила технологического присоединения"],
            category="физическое лицо"
        ),
        BenchmarkSample(
            id=2,
            question="Какие документы нужны для подключения участка?",
            expected_answer="Для подключения земельного участка требуются следующие документы...",
            expected_sources=["Перечень документов", "Требования к заявителям"],
            category="физическое лицо"
        ),
        BenchmarkSample(
            id=3,
            question="Сколько стоит подключение к электросетям?",
            expected_answer="Стоимость подключения зависит от категории заявителя...",
            expected_sources=["Тарифы на подключение", "Постановление о ставках"],
            category="юридическое лицо"
        ),
        BenchmarkSample(
            id=4,
            question="Как изменить категорию потребителя?",
            expected_answer="Для изменения категории потребителя необходимо...",
            expected_sources=["Порядок изменения категории", "Требования к документам"],
            category="юридическое лицо"
        ),
        BenchmarkSample(
            id=5,
            question="Что делать если отключили свет?",
            expected_answer="При отключении электроэнергии необходимо...",
            expected_sources=["Правила предоставления услуг", "Аварийная служба"],
            category="физическое лицо"
        ),
    ]


def main():
    """Точка входа для бенчмарка."""
    import argparse

    parser = argparse.ArgumentParser(description="Benchmark для Agentic RAG")
    parser.add_argument("--samples", "-s", help="Файл с примерами (JSON)")
    parser.add_argument("--output", "-o", default="results", help="Директория для результатов")
    parser.add_argument("--use-default", action="store_true", help="Использовать дефолтные примеры")
    parser.add_argument("--no-llm-judge", action="store_true", help="Отключить LLM Judge оценку")
    parser.add_argument("--llm-judge-only", action="store_true", help="Только LLM Judge (без пересоздания ответов)")

    args = parser.parse_args()

    # Загрузка примеров
    if args.samples:
        samples = load_benchmark_samples(args.samples)
    elif args.use_default:
        samples = create_default_samples()
    else:
        print("❌ Укажите --samples или --use-default")
        return

    # Запуск бенчмарка
    use_llm_judge = not args.no_llm_judge
    benchmark = AgenticRAGBenchmark(samples, use_llm_judge=use_llm_judge)
    benchmark.run(output_dir=args.output)


if __name__ == "__main__":
    main()
