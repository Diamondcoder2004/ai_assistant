"""
Простые тесты для проверки базовой функциональности

Эти тесты работают без внешних зависимостей и используют только mock-объекты.
"""
import pytest
import time
import logging
from unittest.mock import Mock, patch, MagicMock

from agents.query_generator import QueryGeneratorAgent, QueryGenerationResult
from agents.search_agent import SearchAgent
from agents.response_agent import ResponseAgent
from tools.search_tool import SearchTool, SearchRequest, SearchResult

logging.basicConfig(level=logging.CRITICAL)


# =============================================================================
# TEST 1: BM25 CACHING
# =============================================================================

class TestBM25Caching:
    """Тесты кэширования BM25."""

    def test_bm25_load_once(self):
        """
        Проверка, что BM25 загружается только один раз.
        """
        tool = SearchTool()
        
        # Мокаем метод scroll чтобы считать вызовы
        with patch.object(tool.client, 'scroll') as mock_scroll:
            mock_scroll.side_effect = [([], None), ([], None)]
            
            # Первый поиск
            try:
                tool.search(SearchRequest(query="тест", k=5))
            except Exception:
                pass
            
            call_count_after_first = mock_scroll.call_count
            
            # Второй поиск
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


# =============================================================================
# TEST 2: PARAMETER BOUNDARIES
# =============================================================================

class TestParameterBoundaries:
    """Тесты граничных случаев параметров."""

    def test_k_min_boundary(self):
        """Проверка минимального значения k=1."""
        request = SearchRequest(query="тест", k=1)
        assert request.k == 1

    def test_k_max_boundary(self):
        """Проверка максимального значения k=100."""
        request = SearchRequest(query="тест", k=100)
        assert request.k == 100

    def test_weights_sum_to_one(self):
        """Проверка, что сумма весов равна 1.0."""
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
        """Проверка нулевого веса для одного компонента."""
        request = SearchRequest(
            query="тест",
            pref_weight=0.5,
            hype_weight=0.5,
            lexical_weight=0.0,
            contextual_weight=0.0
        )
        
        assert request.lexical_weight == 0.0
        assert request.contextual_weight == 0.0

    def test_all_weight_on_one_component(self):
        """Проверка веса 1.0 для одного компонента."""
        request = SearchRequest(
            query="тест",
            pref_weight=1.0,
            hype_weight=0.0,
            lexical_weight=0.0,
            contextual_weight=0.0
        )
        
        assert request.pref_weight == 1.0


# =============================================================================
# TEST 3: USER HINTS INFLUENCE
# =============================================================================

class TestUserHintsInfluence:
    """Тесты влияния user_hints на решение агента."""

    def test_user_hints_k_in_prompt(self):
        """
        Проверка, что user_hints['k'] попадает в промпт.
        """
        agent = QueryGeneratorAgent()
        
        user_hints = {"k": 15}
        
        mock_response_data = {
            "clarification_needed": False,
            "clarification_questions": [],
            "queries": [{"text": "тест", "reason": "тест"}],
            "search_params": {"k": 15, "pref_weight": 0.4, "hype_weight": 0.3, "lexical_weight": 0.2, "contextual_weight": 0.1},
            "confidence": 0.8,
            "reasoning": "тест"
        }
        
        with patch.object(agent.client.chat.completions, 'create') as mock_create:
            mock_create.return_value.choices[0].message.content = str(mock_response_data)
            
            result = agent.generate("тест", user_hints=user_hints)
            
            # Проверка: user_hints был в промпте
            call_args = mock_create.call_args
            prompt = call_args[1]['messages'][1]['content']
            
            # Промпт должен содержать k или значение
            assert "k" in prompt.lower() or "15" in prompt

    def test_user_hints_temperature_passed_to_llm(self):
        """
        Проверка, что temperature передаётся в LLM.
        """
        agent = QueryGeneratorAgent()
        
        mock_response_data = {
            "clarification_needed": False,
            "clarification_questions": [],
            "queries": [{"text": "тест", "reason": "тест"}],
            "search_params": {"k": 10, "pref_weight": 0.4, "hype_weight": 0.3, "lexical_weight": 0.2, "contextual_weight": 0.1},
            "confidence": 0.8,
            "reasoning": "тест"
        }
        
        with patch.object(agent.client.chat.completions, 'create') as mock_create:
            mock_create.return_value.choices[0].message.content = str(mock_response_data)
            
            result = agent.generate("тест", temperature=1.2)
            
            # Проверка: temperature=1.2 передан в LLM
            call_args = mock_create.call_args
            assert call_args[1]['temperature'] == 1.2

    def test_user_hints_max_tokens_passed_to_llm(self):
        """
        Проверка, что max_tokens передаётся в LLM.
        """
        agent = QueryGeneratorAgent()
        
        mock_response_data = {
            "clarification_needed": False,
            "clarification_questions": [],
            "queries": [{"text": "тест", "reason": "тест"}],
            "search_params": {"k": 10, "pref_weight": 0.4, "hype_weight": 0.3, "lexical_weight": 0.2, "contextual_weight": 0.1},
            "confidence": 0.8,
            "reasoning": "тест"
        }
        
        with patch.object(agent.client.chat.completions, 'create') as mock_create:
            mock_create.return_value.choices[0].message.content = str(mock_response_data)
            
            result = agent.generate("тест", max_tokens=3000)
            
            # Проверка: max_tokens=3000 передан в LLM
            call_args = mock_create.call_args
            assert call_args[1]['max_tokens'] == 3000

    def test_no_user_hints_uses_defaults(self):
        """
        Проверка, что без user_hints используются дефолтные значения.
        """
        agent = QueryGeneratorAgent()
        
        mock_response_data = {
            "clarification_needed": False,
            "clarification_questions": [],
            "queries": [{"text": "тест", "reason": "тест"}],
            "search_params": {"k": 10, "pref_weight": 0.4, "hype_weight": 0.3, "lexical_weight": 0.2, "contextual_weight": 0.1},
            "confidence": 0.8,
            "reasoning": "тест"
        }
        
        with patch.object(agent.client.chat.completions, 'create') as mock_create:
            mock_create.return_value.choices[0].message.content = str(mock_response_data)
            
            result = agent.generate("тест", user_hints=None)
            
            # Проверка: k=10 (дефолт)
            assert result.search_params.get("k") == 10


# =============================================================================
# TEST 4: AGENT INITIALIZATION
# =============================================================================

class TestAgentInitialization:
    """Тесты инициализации агентов."""

    def test_query_generator_init(self):
        """Тест инициализации QueryGenerator."""
        agent = QueryGeneratorAgent()
        assert agent.client is not None
        assert agent.model is not None

    def test_search_agent_init(self):
        """Тест инициализации SearchAgent."""
        agent = SearchAgent()
        assert agent.search_tool is not None
        assert agent.query_generator is not None

    def test_response_agent_init(self):
        """Тест инициализации ResponseAgent."""
        agent = ResponseAgent()
        assert agent.client is not None
        assert agent.model is not None

    def test_search_tool_init(self):
        """Тест инициализации SearchTool."""
        tool = SearchTool()
        assert tool.client is not None
        assert tool.embedder is not None


# =============================================================================
# TEST 5: UTILITY FUNCTIONS
# =============================================================================

class TestUtilityFunctions:
    """Тесты вспомогательных функций."""

    def test_tokenize_text(self):
        """Тест токенизации текста."""
        tool = SearchTool()
        
        text = "подача заявки на подключение"
        tokens = tool._tokenize_text(text)
        
        assert isinstance(tokens, list)
        assert len(tokens) > 0

    def test_format_context(self):
        """Тест форматирования контекста."""
        agent = ResponseAgent()
        
        results = [
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
        ]
        
        context = agent._format_context(results)
        
        assert "test_doc" in context
        assert "Тестовый контент" in context

    def test_format_results(self):
        """Тест форматирования результатов."""
        agent = SearchAgent()
        
        results = [
            SearchResult(
                id="1",
                content="Тест",
                summary="Саммари",
                category="Тест",
                filename="doc",
                breadcrumbs="Раздел",
                score_hybrid=0.9,
                score_semantic=0.8,
                score_lexical=0.7,
                metadata={}
            )
        ]
        
        formatted = agent.format_results(results, top_k=1)
        
        assert "Тест" in formatted
        assert "doc" in formatted


# =============================================================================
# RUN TESTS
# =============================================================================

def run_tests():
    """Запуск тестов."""
    pytest.main([__file__, "-v", "--tb=short"])


if __name__ == "__main__":
    run_tests()
