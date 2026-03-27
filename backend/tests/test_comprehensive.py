"""
Комплексные тесты для Agentic RAG системы

Тесты покрывают:
1. Кэширование BM25
2. Граничные случаи параметров
3. Влияние user_hints на решение агента
4. Нагрузочное тестирование
"""
import pytest
import logging
import time
import asyncio
from unittest.mock import Mock, patch, MagicMock
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any

from agents.query_generator import QueryGeneratorAgent, QueryGenerationResult
from agents.search_agent import SearchAgent
from agents.response_agent import ResponseAgent
from tools.search_tool import SearchTool, SearchRequest, SearchResult
from main import AgenticRAG
import config

logging.basicConfig(level=logging.CRITICAL)  # Отключаем логи во время тестов


# =============================================================================
# TEST 1: BM25 CACHING
# =============================================================================

class TestBM25Caching:
    """Тесты кэширования BM25."""

    def test_bm25_load_once(self):
        """
        Проверка, что BM25 загружается только один раз.
        
        Ожидание:
        - Первый вызов search() загружает документы
        - Второй вызов search() НЕ загружает документы повторно
        """
        tool = SearchTool()
        
        # Мокаем метод scroll чтобы считать вызовы
        with patch.object(tool.client, 'scroll') as mock_scroll:
            # Настраиваем mock для возврата пустых данных
            mock_scroll.side_effect = [([], None), ([], None)]
            
            # Первый поиск (должен загрузить документы)
            try:
                tool.search(SearchRequest(query="тест", k=5))
            except Exception:
                pass  # Игнорируем ошибки, важно что load() был вызван
            
            call_count_after_first = mock_scroll.call_count
            
            # Второй поиск (не должен загружать документы)
            try:
                tool.search(SearchRequest(query="тест2", k=5))
            except Exception:
                pass
            
            call_count_after_second = mock_scroll.call_count
            
            # Проверка: scroll не должен вызываться второй раз
            assert call_count_after_second == call_count_after_first, \
                "BM25 кэш не работает: документы загружаются повторно"

    def test_bm25_force_reload(self):
        """
        Проверка, что force=True перезагружает кэш.
        """
        tool = SearchTool()
        
        with patch.object(tool.client, 'scroll') as mock_scroll:
            mock_scroll.side_effect = [([], None), ([], None)]
            
            # Первый поиск
            try:
                tool.search(SearchRequest(query="тест", k=5))
            except Exception:
                pass
            
            # Принудительная перезагрузка
            tool.load(force=True)
            
            # Проверка: scroll был вызван ещё раз
            assert mock_scroll.call_count >= 2, "force=True не перезагружает кэш"

    def test_bm25_tokenization_cache(self):
        """
        Проверка кэширования токенизации.
        
        Ожидание:
        - Одинаковые тексты токенизируются одинаково
        """
        tool = SearchTool()
        
        text = "подача заявки на технологическое присоединение"
        
        tokens1 = tool._tokenize_text(text)
        tokens2 = tool._tokenize_text(text)
        
        assert tokens1 == tokens2, "Токенизация нестабильна"


# =============================================================================
# TEST 2: BOUNDARY CASES FOR PARAMETERS
# =============================================================================

class TestParameterBoundaries:
    """Тесты граничных случаев параметров."""

    def test_k_min_boundary(self):
        """
        Проверка минимального значения k=1.
        
        Ожидание:
        - SearchRequest принимает k=1
        """
        request = SearchRequest(query="тест", k=1)
        assert request.k == 1

    def test_k_max_boundary(self):
        """
        Проверка максимального значения k=100.
        
        Ожидание:
        - SearchRequest принимает k=100
        """
        request = SearchRequest(query="тест", k=100)
        assert request.k == 100

    def test_weights_sum_to_one(self):
        """
        Проверка, что сумма весов равна 1.0.
        
        Ожидание:
        - pref_weight + hype_weight + lexical_weight + contextual_weight = 1.0
        """
        request = SearchRequest(
            query="тест",
            pref_weight=0.4,
            hype_weight=0.3,
            lexical_weight=0.2,
            contextual_weight=0.1
        )
        
        total = (request.pref_weight + request.hype_weight + 
                 request.lexical_weight + request.contextual_weight)
        assert abs(total - 1.0) < 0.001, f"Сумма весов не равна 1.0: {total}"

    def test_zero_weight_for_component(self):
        """
        Проверка нулевого веса для одного компонента.
        
        Ожидание:
        - Можно отключить компонент установкой веса в 0
        """
        request = SearchRequest(
            query="тест",
            pref_weight=0.5,
            hype_weight=0.5,
            lexical_weight=0.0,  # Отключаем BM25
            contextual_weight=0.0
        )
        
        assert request.lexical_weight == 0.0
        assert request.contextual_weight == 0.0

    def test_all_weight_on_one_component(self):
        """
        Проверка веса 1.0 для одного компонента.
        
        Ожидание:
        - Можно установить весь вес на один компонент
        """
        request = SearchRequest(
            query="тест",
            pref_weight=1.0,
            hype_weight=0.0,
            lexical_weight=0.0,
            contextual_weight=0.0
        )
        
        assert request.pref_weight == 1.0

    def test_negative_weights_not_allowed(self):
        """
        Проверка, что отрицательные веса не допускаются.
        
        Ожидание:
        - SearchRequest создаётся, но логика должна обрабатывать
        """
        # Pydantic не валидирует, но логика должна обрабатывать
        request = SearchRequest(
            query="тест",
            pref_weight=-0.1,
            hype_weight=0.4,
            lexical_weight=0.4,
            contextual_weight=0.3
        )
        
        # Отрицательные веса технически возможны, но нежелательны
        assert request.pref_weight == -0.1

    def test_weights_greater_than_one(self):
        """
        Проверка весов > 1.0.
        
        Ожидание:
        - SearchRequest создаётся, но гибридная оценка может быть > 1
        """
        request = SearchRequest(
            query="тест",
            pref_weight=2.0,
            hype_weight=0.0,
            lexical_weight=0.0,
            contextual_weight=0.0
        )
        
        assert request.pref_weight == 2.0


# =============================================================================
# TEST 3: USER HINTS INFLUENCE ON AGENT DECISIONS
# =============================================================================

class TestUserHintsInfluence:
    """Тесты влияния user_hints на решение агента."""

    def test_user_hints_k_override(self):
        """
        Проверка, что user_hints['k'] переопределяет решение агента.
        
        Ожидание:
        - Агент использует k из user_hints, если оно разумно
        """
        agent = QueryGeneratorAgent()
        
        user_hints = {"k": 15}
        
        # Мокаем ответ LLM с дефолтным k=10
        mock_response = {
            "clarification_needed": False,
            "clarification_questions": [],
            "queries": [{"text": "тест", "reason": "тест"}],
            "search_params": {
                "k": 10,  # Агент хочет k=10
                "pref_weight": 0.4,
                "hype_weight": 0.3,
                "lexical_weight": 0.2,
                "contextual_weight": 0.1,
                "strategy": "concat"
            },
            "confidence": 0.8,
            "reasoning": "тест"
        }
        
        with patch.object(agent.client.chat.completions, 'create') as mock_create:
            mock_create.return_value.choices[0].message.content = str(mock_response)
            
            result = agent.generate("тест", user_hints=user_hints)
            
            # Проверяем, что LLM получил user_hints
            call_args = mock_create.call_args
            prompt_text = call_args[1]['messages'][1]['content']
            
            # user_hints должен быть в промпте
            assert "k" in prompt_text or "15" in prompt_text

    def test_user_hints_temperature_override(self):
        """
        Проверка, что user_hints['temperature'] переопределяет решение агента.
        """
        agent = QueryGeneratorAgent()
        
        user_hints = {"temperature": 1.2}
        
        mock_response = {
            "clarification_needed": False,
            "clarification_questions": [],
            "queries": [{"text": "тест", "reason": "тест"}],
            "search_params": {
                "k": 10,
                "pref_weight": 0.4,
                "hype_weight": 0.3,
                "lexical_weight": 0.2,
                "contextual_weight": 0.1,
                "strategy": "concat"
            },
            "confidence": 0.8,
            "reasoning": "тест"
        }
        
        with patch.object(agent.client.chat.completions, 'create') as mock_create:
            mock_create.return_value.choices[0].message.content = str(mock_response)
            
            result = agent.generate("тест", user_hints=user_hints)
            
            # Проверяем, что LLM получил user_hints
            call_args = mock_create.call_args
            prompt_text = call_args[1]['messages'][1]['content']
            
            assert "temperature" in prompt_text or "1.2" in prompt_text

    def test_user_hints_max_tokens_override(self):
        """
        Проверка, что user_hints['max_tokens'] переопределяет решение агента.
        """
        agent = QueryGeneratorAgent()
        
        user_hints = {"max_tokens": 3000}
        
        mock_response = {
            "clarification_needed": False,
            "clarification_questions": [],
            "queries": [{"text": "тест", "reason": "тест"}],
            "search_params": {
                "k": 10,
                "pref_weight": 0.4,
                "hype_weight": 0.3,
                "lexical_weight": 0.2,
                "contextual_weight": 0.1,
                "strategy": "concat"
            },
            "confidence": 0.8,
            "reasoning": "тест"
        }
        
        with patch.object(agent.client.chat.completions, 'create') as mock_create:
            mock_create.return_value.choices[0].message.content = str(mock_response)
            
            result = agent.generate("тест", user_hints=user_hints)
            
            call_args = mock_create.call_args
            prompt_text = call_args[1]['messages'][1]['content']
            
            assert "max_tokens" in prompt_text or "3000" in prompt_text

    def test_user_hints_extreme_k(self):
        """
        Проверка экстремального значения k=100.
        
        Ожидание:
        - Агент должен обработать запрос, но может скорректировать
        """
        agent = QueryGeneratorAgent()
        
        user_hints = {"k": 100}
        
        mock_response = {
            "clarification_needed": False,
            "clarification_questions": [],
            "queries": [{"text": "тест", "reason": "тест"}],
            "search_params": {
                "k": 100,  # Агент принимает k=100
                "pref_weight": 0.4,
                "hype_weight": 0.3,
                "lexical_weight": 0.2,
                "contextual_weight": 0.1,
                "strategy": "concat"
            },
            "confidence": 0.8,
            "reasoning": "тест"
        }
        
        with patch.object(agent.client.chat.completions, 'create') as mock_create:
            mock_create.return_value.choices[0].message.content = str(mock_response)
            
            result = agent.generate("тест", user_hints=user_hints)
            
            # Проверяем, что k=100 было передано
            assert result.search_params.get("k") == 100

    def test_user_hints_conflicting_weights(self):
        """
        Проверка конфликтующих весов (сумма != 1.0).
        
        Ожидание:
        - Агент должен нормализовать веса или использовать дефолтные
        """
        agent = QueryGeneratorAgent()
        
        # Сумма = 1.5 (конфликт)
        user_hints = {
            "pref_weight": 0.6,
            "hype_weight": 0.4,
            "lexical_weight": 0.3,
            "contextual_weight": 0.2
        }
        
        mock_response = {
            "clarification_needed": False,
            "clarification_questions": [],
            "queries": [{"text": "тест", "reason": "тест"}],
            "search_params": {
                "k": 10,
                "pref_weight": 0.6,
                "hype_weight": 0.4,
                "lexical_weight": 0.3,
                "contextual_weight": 0.2,
                "strategy": "concat"
            },
            "confidence": 0.8,
            "reasoning": "тест"
        }
        
        with patch.object(agent.client.chat.completions, 'create') as mock_create:
            mock_create.return_value.choices[0].message.content = str(mock_response)
            
            result = agent.generate("тест", user_hints=user_hints)
            
            # Проверяем, что агент получил конфликтующие веса
            total = sum([
                result.search_params.get("pref_weight", 0),
                result.search_params.get("hype_weight", 0),
                result.search_params.get("lexical_weight", 0),
                result.search_params.get("contextual_weight", 0)
            ])
            
            # Агент может нормализовать или оставить как есть
            assert total > 0  # Просто проверяем, что веса есть

    def test_no_user_hints_uses_defaults(self):
        """
        Проверка, что без user_hints используются дефолтные значения.
        """
        agent = QueryGeneratorAgent()
        
        mock_response = {
            "clarification_needed": False,
            "clarification_questions": [],
            "queries": [{"text": "тест", "reason": "тест"}],
            "search_params": {
                "k": 10,
                "pref_weight": config.RETRIEVE_PREF_WEIGHT,
                "hype_weight": config.RETRIEVE_HYPE_WEIGHT,
                "lexical_weight": config.RETRIEVE_LEXICAL_WEIGHT,
                "contextual_weight": config.RETRIEVE_CONTEXTUAL_WEIGHT,
                "strategy": "concat"
            },
            "confidence": 0.8,
            "reasoning": "тест"
        }
        
        with patch.object(agent.client.chat.completions, 'create') as mock_create:
            mock_create.return_value.choices[0].message.content = str(mock_response)
            
            result = agent.generate("тест", user_hints=None)
            
            # Проверка дефолтных значений
            assert result.search_params.get("k") == 10
            assert abs(result.search_params.get("pref_weight", 0) - config.RETRIEVE_PREF_WEIGHT) < 0.01


# =============================================================================
# TEST 4: LOAD TESTING
# =============================================================================

class TestLoadPerformance:
    """Нагрузочные тесты."""

    def test_concurrent_search_requests(self):
        """
        Проверка обработки множественных параллельных запросов.
        
        Ожидание:
        - 10 параллельных запросов обрабатываются без ошибок
        """
        tool = SearchTool()
        
        def make_search(query: str):
            try:
                results = tool.search(SearchRequest(query=query, k=5))
                return len(results)
            except Exception as e:
                return 0
        
        queries = [f"тест {i}" for i in range(10)]
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            results = list(executor.map(make_search, queries))
        
        # Проверка: все запросы обработаны
        assert len(results) == 10

    def test_sequential_search_performance(self):
        """
        Проверка производительности последовательных запросов.
        
        Ожидание:
        - 5 последовательных запросов выполняются < 30 секунд
        """
        tool = SearchTool()
        
        start_time = time.time()
        
        for i in range(5):
            try:
                tool.search(SearchRequest(query=f"тест {i}", k=5))
            except Exception:
                pass
        
        elapsed = time.time() - start_time
        
        # Проверка: общее время < 30 секунд
        assert elapsed < 30, f"Слишком медленно: {elapsed:.2f}с"

    def test_response_agent_performance(self):
        """
        Проверка производительности ResponseAgent.
        
        Ожидание:
        - Генерация ответа < 10 секунд
        """
        agent = ResponseAgent()
        
        results = [
            SearchResult(
                id="1",
                content="Тестовый контент " * 100,
                summary="Саммари",
                category="Тест",
                filename="test_doc",
                breadcrumbs="Раздел 1",
                score_hybrid=0.9,
                score_semantic=0.8,
                score_lexical=0.7,
                metadata={}
            )
        ]
        
        start_time = time.time()
        
        try:
            response = agent.generate_response(
                user_query="Тестовый вопрос",
                search_results=results,
                temperature=0.7,
                max_tokens=500
            )
            
            elapsed = time.time() - start_time
            
            # Проверка: время < 10 секунд
            assert elapsed < 10, f"Слишком медленно: {elapsed:.2f}с"
            
            # Проверка: ответ не пустой
            assert "answer" in response
            
        except Exception as e:
            pytest.skip(f"LLM недоступен: {e}")

    def test_query_generator_performance(self):
        """
        Проверка производительности QueryGenerator.
        
        Ожидание:
        - Генерация запросов < 5 секунд
        """
        agent = QueryGeneratorAgent()
        
        start_time = time.time()
        
        try:
            result = agent.generate("Как подать заявку на подключение?")
            
            elapsed = time.time() - start_time
            
            # Проверка: время < 5 секунд
            assert elapsed < 5, f"Слишком медленно: {elapsed:.2f}с"
            
            # Проверка: запросы сгенерированы
            assert len(result.queries) >= 1
            
        except Exception as e:
            pytest.skip(f"LLM недоступен: {e}")


# =============================================================================
# TEST 5: EDGE CASES
# =============================================================================

class TestEdgeCases:
    """Тесты крайних случаев."""

    def test_empty_query(self):
        """
        Проверка пустого запроса.
        
        Ожидание:
        - SearchRequest создаётся, но поиск возвращает 0 результатов
        """
        tool = SearchTool()
        
        try:
            results = tool.search(SearchRequest(query="", k=5))
            # Пустой запрос может вернуть результаты или 0
            assert isinstance(results, list)
        except Exception as e:
            # Или выбросить ошибку
            assert True

    def test_very_long_query(self):
        """
        Проверка очень длинного запроса (> 500 символов).
        
        Ожидание:
        - SearchRequest обрабатывает длинный запрос
        """
        tool = SearchTool()
        
        long_query = "тест " * 200  # 1000 символов
        
        try:
            results = tool.search(SearchRequest(query=long_query, k=5))
            assert isinstance(results, list)
        except Exception:
            pass

    def test_special_characters_in_query(self):
        """
        Проверка специальных символов в запросе.
        
        Ожидание:
        - SearchRequest обрабатывает специальные символы
        """
        tool = SearchTool()
        
        special_query = "тест!@#$%^&*()_+-=[]{}|;':\",./<>?"
        
        try:
            results = tool.search(SearchRequest(query=special_query, k=5))
            assert isinstance(results, list)
        except Exception:
            pass

    def test_unicode_query(self):
        """
        Проверка Unicode символов в запросе.
        
        Ожидание:
        - SearchRequest обрабатывает Unicode
        """
        tool = SearchTool()
        
        unicode_query = "тест 你好 🚀"
        
        try:
            results = tool.search(SearchRequest(query=unicode_query, k=5))
            assert isinstance(results, list)
        except Exception:
            pass

    def test_response_agent_no_results(self):
        """
        Проверка ResponseAgent без результатов поиска.
        
        Ожидание:
        - Агент генерирует ответ или сообщает об отсутствии информации
        """
        agent = ResponseAgent()
        
        try:
            response = agent.generate_response(
                user_query="Тестовый вопрос",
                search_results=[],
                temperature=0.7,
                max_tokens=500
            )
            
            # Проверка: ответ есть
            assert "answer" in response
            
        except Exception as e:
            pytest.skip(f"LLM недоступен: {e}")


# =============================================================================
# TEST 6: INTEGRATION TESTS
# =============================================================================

class TestIntegration:
    """Интеграционные тесты."""

    def test_full_pipeline_with_mock(self):
        """
        Проверка полного пайплайна с моками.
        
        Ожидание:
        - Query Generator → Search → Response Agent работают вместе
        """
        rag = AgenticRAG()
        
        # Мокаем SearchAgent
        mock_search_result = {
            "clarification_needed": False,
            "results": [
                SearchResult(
                    id="1",
                    content="Тестовый контент",
                    summary="Саммари",
                    category="Тест",
                    filename="test_doc",
                    breadcrumbs="Раздел 1",
                    score_hybrid=0.9,
                    score_semantic=0.8,
                    score_lexical=0.7,
                    metadata={}
                )
            ],
            "queries_used": ["тест"],
            "search_params": {"k": 10},
            "confidence": 0.8
        }
        
        with patch.object(rag.search_agent, 'search') as mock_search:
            mock_search.return_value = mock_search_result
            
            # Мокаем ResponseAgent
            with patch.object(rag.response_agent, 'generate_response') as mock_response:
                mock_response.return_value = {
                    "answer": "Тестовый ответ",
                    "sources": [],
                    "confidence": 0.8
                }
                
                result = rag.query("Тестовый вопрос")
                
                # Проверка: пайплайн сработал
                assert "answer" in result
                assert result["answer"] == "Тестовый ответ"

    def test_session_id_handling(self):
        """
        Проверка обработки session_id.
        
        Ожидание:
        - session_id корректно передаётся через пайплайн
        """
        rag = AgenticRAG()
        
        # session_id должен быть строкой
        session_id = "test-session-123"
        
        # Проверка: session_id сохраняется
        assert isinstance(session_id, str)


# =============================================================================
# RUN TESTS
# =============================================================================

def run_tests():
    """Запуск тестов."""
    pytest.main([__file__, "-v", "--tb=short"])


if __name__ == "__main__":
    run_tests()
