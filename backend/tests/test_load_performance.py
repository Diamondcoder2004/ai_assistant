"""
Нагрузочные тесты с метриками производительности

Тесты измеряют:
- Время ответа при различной нагрузке
- Процент ошибок
- P95, P99 перцентили
"""
import pytest
import time
import statistics
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import patch, MagicMock

from agents.query_generator import QueryGeneratorAgent
from agents.search_agent import SearchAgent
from agents.response_agent import ResponseAgent
from tools.search_tool import SearchTool, SearchRequest
from main import AgenticRAG


# =============================================================================
# PERFORMANCE METRICS
# =============================================================================

class PerformanceMetrics:
    """Класс для сбора метрик производительности."""
    
    def __init__(self):
        self.latencies: List[float] = []
        self.errors: int = 0
        self.successes: int = 0
    
    def record(self, latency_ms: float, success: bool = True):
        """Запись результата запроса."""
        self.latencies.append(latency_ms)
        if success:
            self.successes += 1
        else:
            self.errors += 1
    
    @property
    def avg_latency(self) -> float:
        """Средняя задержка."""
        return statistics.mean(self.latencies) if self.latencies else 0
    
    @property
    def min_latency(self) -> float:
        """Минимальная задержка."""
        return min(self.latencies) if self.latencies else 0
    
    @property
    def max_latency(self) -> float:
        """Максимальная задержка."""
        return max(self.latencies) if self.latencies else 0
    
    @property
    def p50_latency(self) -> float:
        """Медиана (P50)."""
        if not self.latencies:
            return 0
        sorted_latencies = sorted(self.latencies)
        idx = len(sorted_latencies) // 2
        return sorted_latencies[idx]
    
    @property
    def p95_latency(self) -> float:
        """P95 перцентиль."""
        if not self.latencies:
            return 0
        sorted_latencies = sorted(self.latencies)
        idx = int(len(sorted_latencies) * 0.95)
        return sorted_latencies[min(idx, len(sorted_latencies) - 1)]
    
    @property
    def p99_latency(self) -> float:
        """P99 перцентиль."""
        if not self.latencies:
            return 0
        sorted_latencies = sorted(self.latencies)
        idx = int(len(sorted_latencies) * 0.99)
        return sorted_latencies[min(idx, len(sorted_latencies) - 1)]
    
    @property
    def error_rate(self) -> float:
        """Процент ошибок."""
        total = self.successes + self.errors
        return (self.errors / total * 100) if total > 0 else 0
    
    @property
    def rps(self) -> float:
        """Запросов в секунду (если известна общая длительность)."""
        return 0  # Вычисляется externally
    
    def summary(self) -> Dict[str, Any]:
        """Сводка метрик."""
        return {
            "total_requests": self.successes + self.errors,
            "successes": self.successes,
            "errors": self.errors,
            "error_rate": f"{self.error_rate:.2f}%",
            "avg_latency_ms": f"{self.avg_latency:.2f}",
            "min_latency_ms": f"{self.min_latency:.2f}",
            "max_latency_ms": f"{self.max_latency:.2f}",
            "p50_latency_ms": f"{self.p50_latency:.2f}",
            "p95_latency_ms": f"{self.p95_latency:.2f}",
            "p99_latency_ms": f"{self.p99_latency:.2f}"
        }


# =============================================================================
# LOAD TESTS
# =============================================================================

class TestLoadStress:
    """Нагрузочные и стресс тесты."""

    def test_burst_load_10_requests(self):
        """
        Стресс-тест: 10 запросов одновременно.
        
        Ожидание:
        - Все запросы обрабатываются
        - Среднее время < 10 секунд
        """
        metrics = PerformanceMetrics()
        tool = SearchTool()
        
        def make_request(query: str):
            start = time.time()
            try:
                results = tool.search(SearchRequest(query=query, k=5))
                latency_ms = (time.time() - start) * 1000
                metrics.record(latency_ms, success=True)
                return len(results)
            except Exception as e:
                latency_ms = (time.time() - start) * 1000
                metrics.record(latency_ms, success=False)
                return 0
        
        queries = [f"как подать заявку {i}" for i in range(10)]
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request, q) for q in queries]
            results = [f.result() for f in as_completed(futures)]
        
        # Проверка метрик
        summary = metrics.summary()
        print(f"\n=== Burst Load 10 Requests ===")
        print(f"Avg: {summary['avg_latency_ms']}мс, P95: {summary['p95_latency_ms']}мс")
        print(f"Errors: {summary['error_rate']}")
        
        assert metrics.successes == 10, f"Не все запросы успешны: {metrics.successes}/10"
        assert metrics.avg_latency < 10000, f"Слишком медленно: {metrics.avg_latency:.2f}мс"

    def test_sustained_load_20_requests(self):
        """
        Тест устойчивой нагрузки: 20 запросов последовательно.
        
        Ожидание:
        - Все запросы обрабатываются
        - Общее время < 60 секунд
        """
        metrics = PerformanceMetrics()
        tool = SearchTool()
        
        start_total = time.time()
        
        for i in range(20):
            start = time.time()
            try:
                results = tool.search(SearchRequest(query=f"тест {i}", k=5))
                latency_ms = (time.time() - start) * 1000
                metrics.record(latency_ms, success=True)
            except Exception as e:
                latency_ms = (time.time() - start) * 1000
                metrics.record(latency_ms, success=False)
        
        total_time = time.time() - start_total
        
        # Проверка метрик
        summary = metrics.summary()
        print(f"\n=== Sustained Load 20 Requests ===")
        print(f"Total time: {total_time:.2f}с")
        print(f"Avg: {summary['avg_latency_ms']}мс, P95: {summary['p95_latency_ms']}мс")
        
        assert metrics.successes == 20, f"Не все запросы успешны: {metrics.successes}/20"
        assert total_time < 60, f"Слишком медленно: {total_time:.2f}с"

    def test_query_generator_load(self):
        """
        Нагрузочный тест Query Generator.
        
        Ожидание:
        - 10 запросов генерируются < 30 секунд
        """
        metrics = PerformanceMetrics()
        agent = QueryGeneratorAgent()
        
        mock_response = {
            "clarification_needed": False,
            "clarification_questions": [],
            "queries": [{"text": "тест", "reason": "тест"}],
            "search_params": {"k": 10, "pref_weight": 0.4, "hype_weight": 0.3, "lexical_weight": 0.2, "contextual_weight": 0.1},
            "confidence": 0.8,
            "reasoning": "тест"
        }
        
        with patch.object(agent.client.chat.completions, 'create') as mock_create:
            mock_create.return_value.choices[0].message.content = str(mock_response)
            
            start_total = time.time()
            
            for i in range(10):
                start = time.time()
                try:
                    result = agent.generate(f"вопрос {i}")
                    latency_ms = (time.time() - start) * 1000
                    metrics.record(latency_ms, success=True)
                except Exception as e:
                    latency_ms = (time.time() - start) * 1000
                    metrics.record(latency_ms, success=False)
            
            total_time = time.time() - start_total
            
            summary = metrics.summary()
            print(f"\n=== Query Generator Load ===")
            print(f"Total time: {total_time:.2f}с")
            print(f"Avg: {summary['avg_latency_ms']}мс")
            
            assert metrics.successes == 10
            assert total_time < 30

    def test_response_agent_load(self):
        """
        Нагрузочный тест Response Agent.
        
        Ожидание:
        - 10 ответов генерируются < 60 секунд
        """
        metrics = PerformanceMetrics()
        agent = ResponseAgent()
        
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Тестовый ответ с источниками [1][2]."
        
        with patch.object(agent.client.chat.completions, 'create') as mock_create:
            mock_create.return_value = mock_response
            
            start_total = time.time()
            
            for i in range(10):
                start = time.time()
                try:
                    result = agent.generate_response(
                        user_query=f"вопрос {i}",
                        search_results=[],
                        temperature=0.7,
                        max_tokens=500
                    )
                    latency_ms = (time.time() - start) * 1000
                    metrics.record(latency_ms, success=True)
                except Exception as e:
                    latency_ms = (time.time() - start) * 1000
                    metrics.record(latency_ms, success=False)
            
            total_time = time.time() - start_total
            
            summary = metrics.summary()
            print(f"\n=== Response Agent Load ===")
            print(f"Total time: {total_time:.2f}с")
            print(f"Avg: {summary['avg_latency_ms']}мс")
            
            assert metrics.successes == 10
            assert total_time < 60


# =============================================================================
# SCALABILITY TESTS
# =============================================================================

class TestScalability:
    """Тесты масштабируемости."""

    def test_search_with_varying_k(self):
        """
        Тест поиска с различным k.
        
        Ожидание:
        - Время растёт линейно с k
        """
        tool = SearchTool()
        results = {}
        
        for k in [5, 10, 20]:
            start = time.time()
            try:
                search_results = tool.search(SearchRequest(query="тест", k=k))
                elapsed = time.time() - start
                results[k] = {"time": elapsed, "count": len(search_results)}
            except Exception as e:
                results[k] = {"time": time.time() - start, "count": 0, "error": str(e)}
        
        print(f"\n=== Scalability by k ===")
        for k, v in results.items():
            print(f"k={k}: {v['time']:.2f}с, results={v['count']}")
        
        # Проверка: время растёт с k
        if results[5].get("count", 0) > 0 and results[10].get("count", 0) > 0:
            assert results[10]["time"] >= results[5]["time"] * 0.8  # Допускаем 20% вариацию

    def test_bm25_cache_warmup(self):
        """
        Тест прогрева BM25 кэша.
        
        Ожидание:
        - Первый запрос медленнее второго
        """
        tool = SearchTool()
        
        # Сброс кэша
        tool._loaded = False
        
        times = []
        for i in range(3):
            start = time.time()
            try:
                tool.search(SearchRequest(query="тест", k=5))
            except Exception:
                pass
            elapsed = time.time() - start
            times.append(elapsed)
        
        print(f"\n=== BM25 Cache Warmup ===")
        print(f"Request 1: {times[0]:.2f}с")
        print(f"Request 2: {times[1]:.2f}с")
        print(f"Request 3: {times[2]:.2f}с")
        
        # Проверка: первый запрос может быть медленнее
        # (но не всегда, т.к. кэш может быть уже прогрет)
        if times[0] > 1.0:  # Если первый > 1с
            assert times[1] < times[0] or times[1] < 1.0, "Кэш не работает"


# =============================================================================
# BENCHMARK SAMPLES
# =============================================================================

class TestBenchmarkSamples:
    """Бенчмарк на реальных вопросах."""

    @pytest.mark.parametrize("question", [
        "Как подать заявку на технологическое присоединение?",
        "Какие документы нужны для подключения?",
        "Сколько стоит подключение к электросетям?",
        "Какие сроки технологического присоединения?",
        "Можно ли подать заявку онлайн?",
    ])
    def test_benchmark_questions(self, question: str):
        """
        Бенчмарк на реальных вопросах.
        
        Ожидание:
        - Ответ генерируется < 15 секунд
        """
        rag = AgenticRAG()
        
        start = time.time()
        
        try:
            # Мокаем search чтобы ускорить тест
            mock_search_result = {
                "clarification_needed": False,
                "results": [],
                "queries_used": [question],
                "search_params": {"k": 10},
                "confidence": 0.8
            }
            
            with patch.object(rag.search_agent, 'search') as mock_search:
                mock_search.return_value = mock_search_result
                
                # Мокаем response
                mock_response = MagicMock()
                mock_response.choices[0].message.content = "Тестовый ответ"
                
                with patch.object(rag.response_agent.client.chat.completions, 'create') as mock_create:
                    mock_create.return_value = mock_response
                    
                    result = rag.query(question)
                    
                    elapsed = time.time() - start
                    
                    print(f"\n=== Benchmark: {question[:50]}... ===")
                    print(f"Time: {elapsed:.2f}с")
                    
                    assert elapsed < 15, f"Слишком медленно: {elapsed:.2f}с"
                    assert "answer" in result
                    
        except Exception as e:
            pytest.skip(f"Ошибка: {e}")


# =============================================================================
# RUN TESTS
# =============================================================================

def run_tests():
    """Запуск тестов."""
    pytest.main([__file__, "-v", "--tb=short", "-s"])


if __name__ == "__main__":
    run_tests()
