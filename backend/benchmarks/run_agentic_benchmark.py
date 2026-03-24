"""
Benchmark Agentic RAG на реальных данных из FAQ
"""
import logging
import json
import time
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
from dataclasses import dataclass, asdict
from tqdm import tqdm

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

import config
from main import AgenticRAG
from llm_judge import LLMJudge

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format=config.LOG_FORMAT,
    datefmt=config.LOG_DATE_FORMAT,
    handlers=[
        logging.FileHandler(
            config.LOGS_DIR / f"agentic_benchmark_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


@dataclass
class AgenticBenchmarkResult:
    """Результат бенчмарка Agentic RAG."""
    index: int
    question: str
    expected_answer: str
    generated_answer: str
    queries_used: List[str]
    search_params: Dict[str, Any]
    sources: List[Dict[str, Any]]
    confidence: float
    retrieval_time: float
    generation_time: float
    llm_judge_time: float
    total_time: float
    # LLM Judge оценки
    relevance_score: float = 0.0
    completeness_score: float = 0.0
    helpfulness_score: float = 0.0
    clarity_score: float = 0.0
    hallucination_risk: float = 0.0
    llm_overall_score: float = 0.0
    llm_reasoning: str = ""


class AgenticBenchmark:
    """Бенчмарк Agentic RAG на реальных данных."""
    
    def __init__(self, questions_file: str, use_llm_judge: bool = True):
        self.questions_file = questions_file
        self.use_llm_judge = use_llm_judge
        self.rag = AgenticRAG()
        self.llm_judge = LLMJudge() if use_llm_judge else None
        self.results: List[AgenticBenchmarkResult] = []
        
        logger.info(f"Загрузка вопросов из {questions_file}")
        self.df = pd.read_csv(questions_file)
        logger.info(f"Загружено {len(self.df)} вопросов")
        
        if use_llm_judge:
            logger.info("LLM Judge: ВКЛЮЧЕН")
        else:
            logger.info("LLM Judge: ОТКЛЮЧЕН")
    
    def run(self, output_dir: str = "agentic_results", limit: int = None) -> pd.DataFrame:
        """
        Запуск бенчмарка.
        
        Args:
            output_dir: Директория для результатов
            limit: Ограничить количество вопросов (для теста)
        """
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        df = self.df if limit is None else self.df.head(limit)
        
        logger.info(f"Запуск бенчмарка на {len(df)} вопросах...")
        
        for idx, row in tqdm(df.iterrows(), total=len(df), desc="Agentic Benchmark"):
            result = self._evaluate_question(idx, row)
            self.results.append(result)
        
        # Сохранение результатов
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_df = self._to_dataframe()
        results_df.to_csv(output_path / f"results_{timestamp}.csv", index=False, encoding='utf-8-sig')
        
        # Статистика
        stats = self._calculate_stats()
        with open(output_path / f"stats_{timestamp}.json", "w", encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        
        # Сравнение с оригиналом
        if 'bleu' in self.df.columns:
            comparison = self._compare_with_original()
            with open(output_path / f"comparison_{timestamp}.json", "w", encoding='utf-8') as f:
                json.dump(comparison, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Результаты сохранены в {output_path}")
        self._print_summary(stats)
        
        return results_df
    
    def _evaluate_question(self, idx: int, row: pd.Series) -> AgenticBenchmarkResult:
        """Оценка одного вопроса."""
        start_time = time.time()
        
        question = row['question']
        expected = row.get('expected', '')
        
        # Определение категории из вопроса (можно улучшить)
        category = self._detect_category(question)
        self.rag.set_category(category)
        
        # Выполнение запроса
        retrieval_start = time.time()
        search_result = self.rag.search_agent.search(
            user_query=question,
            history="",
            category=category
        )
        retrieval_time = time.time() - retrieval_start
        
        # Проверка необходимости уточнения
        if search_result["clarification_needed"]:
            return AgenticBenchmarkResult(
                index=idx,
                question=question,
                expected_answer=expected,
                generated_answer="Требуется уточнение",
                queries_used=[],
                search_params={},
                sources=[],
                confidence=0.0,
                retrieval_time=retrieval_time,
                generation_time=0.0,
                llm_judge_time=0.0,
                total_time=time.time() - start_time
            )
        
        # Генерация ответа
        generation_start = time.time()
        response_result = self.rag.response_agent.generate_response(
            user_query=question,
            search_results=search_result["results"],
            history=""
        )
        generation_time = time.time() - generation_start
        
        # LLM Judge оценка
        llm_judge_time = 0.0
        llm_eval = None
        
        if self.use_llm_judge and self.llm_judge:
            logger.info(f"  [{idx}] LLM Judge оценивает ответ...")
            llm_judge_start = time.time()
            
            llm_eval = self.llm_judge.evaluate(
                question=question,
                answer=response_result["answer"],
                sources=response_result["sources"]
            )
            
            llm_judge_time = time.time() - llm_judge_start
            logger.info(f"  [{idx}] LLM Judge: Overall={llm_eval.overall_score:.2f}")
        
        total_time = time.time() - start_time
        
        return AgenticBenchmarkResult(
            index=idx,
            question=question,
            expected_answer=expected,
            generated_answer=response_result["answer"],
            queries_used=search_result["queries_used"],
            search_params=search_result.get("search_params", {}),
            sources=response_result["sources"],
            confidence=response_result["confidence"],
            retrieval_time=retrieval_time,
            generation_time=generation_time,
            llm_judge_time=llm_judge_time,
            total_time=total_time,
            # LLM оценки
            relevance_score=llm_eval.relevance if llm_eval else 0.0,
            completeness_score=llm_eval.completeness if llm_eval else 0.0,
            helpfulness_score=llm_eval.helpfulness if llm_eval else 0.0,
            clarity_score=llm_eval.clarity if llm_eval else 0.0,
            hallucination_risk=llm_eval.hallucination_risk if llm_eval else 0.0,
            llm_overall_score=llm_eval.overall_score if llm_eval else 0.0,
            llm_reasoning=llm_eval.reasoning if llm_eval else ""
        )
    
    def _detect_category(self, question: str) -> str:
        """Определение категории клиента из вопроса."""
        question_lower = question.lower()
        
        if any(word in question_lower for word in ['физическое лицо', 'квартира', 'дом', 'участок', 'дача', 'СНТ']):
            return "физическое лицо"
        elif any(word in question_lower for word in ['юридическое лицо', 'организация', 'предприятие', 'ИП', 'бизнес']):
            return "юридическое лицо"
        else:
            return "не известна"
    
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
        llm_judge_time = sum(r.llm_judge_time for r in self.results)
        
        stats = {
            "total_samples": len(self.results),
            "total_time_sec": total_time,
            "avg_time_sec": total_time / len(self.results),
            "avg_retrieval_time_sec": retrieval_time / len(self.results),
            "avg_generation_time_sec": generation_time / len(self.results),
            "avg_llm_judge_time_sec": llm_judge_time / len(self.results) if self.use_llm_judge else 0,
            "avg_confidence": sum(r.confidence for r in self.results) / len(self.results),
            "clarification_count": sum(1 for r in self.results if r.generated_answer == "Требуется уточнение"),
            "avg_queries_per_request": sum(len(r.queries_used) for r in self.results) / len(self.results),
            "avg_sources_per_request": sum(len(r.sources) for r in self.results) / len(self.results),
        }
        
        # LLM метрики
        if self.use_llm_judge:
            llm_results = [r for r in self.results if r.relevance_score > 0]
            if llm_results:
                stats.update({
                    "llm_judge_enabled": True,
                    "llm_evaluated_count": len(llm_results),
                    "avg_relevance_score": sum(r.relevance_score for r in llm_results) / len(llm_results),
                    "avg_completeness_score": sum(r.completeness_score for r in llm_results) / len(llm_results),
                    "avg_helpfulness_score": sum(r.helpfulness_score for r in llm_results) / len(llm_results),
                    "avg_clarity_score": sum(r.clarity_score for r in llm_results) / len(llm_results),
                    "avg_hallucination_risk": sum(r.hallucination_risk for r in llm_results) / len(llm_results),
                    "avg_llm_overall_score": sum(r.llm_overall_score for r in llm_results) / len(llm_results),
                })
        
        return stats
    
    def _compare_with_original(self) -> Dict[str, Any]:
        """Сравнение с оригинальным benchmark."""
        comparison = {
            "questions_analyzed": len(self.results),
            "agentic_better": 0,
            "original_better": 0,
            "similar": 0,
            "details": []
        }
        
        for r in self.results:
            orig_row = self.df[self.df['index'] == r.index]
            if orig_row.empty:
                continue
            
            orig_emb_sim = orig_row['emb_sim'].values[0] if 'emb_sim' in orig_row.columns else 0
            agentic_score = r.llm_overall_score / 5.0  # Нормализация к 0-1
            
            diff = agentic_score - orig_emb_sim
            
            detail = {
                "index": int(r.index),
                "question": r.question[:100],
                "original_emb_sim": float(orig_emb_sim),
                "agentic_llm_score": float(agentic_score),
                "difference": float(diff),
                "winner": "agentic" if diff > 0.1 else "original" if diff < -0.1 else "similar"
            }
            comparison["details"].append(detail)
            
            if diff > 0.1:
                comparison["agentic_better"] += 1
            elif diff < -0.1:
                comparison["original_better"] += 1
            else:
                comparison["similar"] += 1
        
        return comparison
    
    def _print_summary(self, stats: Dict[str, Any]):
        """Вывод сводки."""
        print("\n" + "=" * 70)
        print("📊 СВОДКА БЕНЧМАРКА AGENTIC RAG")
        print("=" * 70)
        
        print(f"Всего вопросов: {stats.get('total_samples', 0)}")
        print(f"Общее время: {stats.get('total_time_sec', 0):.2f} сек")
        print(f"Среднее время на вопрос: {stats.get('avg_time_sec', 0):.2f} сек")
        print(f"  - Поиск: {stats.get('avg_retrieval_time_sec', 0):.2f} сек")
        print(f"  - Генерация: {stats.get('avg_generation_time_sec', 0):.2f} сек")
        if self.use_llm_judge:
            print(f"  - LLM Judge: {stats.get('avg_llm_judge_time_sec', 0):.2f} сек")
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
            print(f"  💡 Helpfulness (полезность): {stats.get('avg_helpfulness_score', 0):.2f} / 5")
            print(f"  ✨ Clarity (ясность): {stats.get('avg_clarity_score', 0):.2f} / 5")
            print(f"  ⚠️ Hallucination Risk (1=высокий, 5=низкий): {stats.get('avg_hallucination_risk', 0):.2f} / 5")
            print(f"  🎯 Общая оценка LLM: {stats.get('avg_llm_overall_score', 0):.2f} / 5")
        
        print("=" * 70)


def main():
    """Точка входа."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Agentic RAG Benchmark на реальных данных")
    parser.add_argument("--input", "-i", default="d:/PythonProjects/bashkir_rag/benchmarks/benchmark_results.csv",
                       help="Файл с вопросами (CSV)")
    parser.add_argument("--output", "-o", default="agentic_results", help="Директория для результатов")
    parser.add_argument("--limit", "-l", type=int, default=None, help="Ограничить количество вопросов")
    parser.add_argument("--no-llm-judge", action="store_true", help="Отключить LLM Judge")
    
    args = parser.parse_args()
    
    benchmark = AgenticBenchmark(args.input, use_llm_judge=not args.no_llm_judge)
    benchmark.run(output_dir=args.output, limit=args.limit)


if __name__ == "__main__":
    main()
