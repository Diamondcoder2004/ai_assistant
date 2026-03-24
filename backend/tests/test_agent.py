"""
Тесты для Agentic RAG
"""
import pytest
import logging
from unittest.mock import Mock, patch

from agents.query_generator import QueryGeneratorAgent, QueryGenerationResult
from agents.search_agent import SearchAgent
from agents.response_agent import ResponseAgent
from tools.search_tool import SearchTool, SearchRequest, SearchResult
from main import AgenticRAG

logging.basicConfig(level=logging.CRITICAL)  # Отключаем логи во время тестов


class TestQueryGeneratorAgent:
    """Тесты для QueryGeneratorAgent."""
    
    def test_init(self):
        """Тест инициализации."""
        agent = QueryGeneratorAgent()
        assert agent.client is not None
        assert agent.model is not None
    
    def test_generate_single_query(self):
        """Тест генерации одиночного запроса."""
        agent = QueryGeneratorAgent()
        
        # Мокаем ответ LLM
        mock_response = {
            "clarification_needed": False,
            "clarification_questions": [],
            "queries": [
                {"text": "как подать заявку на подключение", "reason": "прямой запрос"}
            ],
            "search_params": {
                "k": 10,
                "pref_weight": 0.5,
                "hype_weight": 0.2,
                "lexical_weight": 0.2,
                "contextual_weight": 0.1,
                "strategy": "concat"
            },
            "confidence": 0.9,
            "reasoning": "Тестовый запрос"
        }
        
        with patch.object(agent.client.chat.completions, 'create') as mock_create:
            mock_create.return_value.choices[0].message.content = str(mock_response)
            
            result = agent.generate("Как подать заявку?")
            
            assert isinstance(result, QueryGenerationResult)
            assert not result.clarification_needed
            assert len(result.queries) >= 1
    
    def test_needs_clarification(self):
        """Тест проверки необходимости уточнения."""
        agent = QueryGeneratorAgent()
        
        result_with_clarification = QueryGenerationResult(
            clarification_needed=True,
            clarification_questions=["Вопрос 1?", "Вопрос 2?"],
            queries=[],
            search_params={},
            confidence=0.3,
            reasoning="Требуется уточнение"
        )
        
        result_without_clarification = QueryGenerationResult(
            clarification_needed=False,
            clarification_questions=[],
            queries=[{"text": "запрос", "reason": "тест"}],
            search_params={},
            confidence=0.8,
            reasoning="Всё понятно"
        )
        
        assert agent.needs_clarification(result_with_clarification)
        assert not agent.needs_clarification(result_without_clarification)
    
    def test_get_queries_text(self):
        """Тест получения текстов запросов."""
        agent = QueryGeneratorAgent()
        
        result = QueryGenerationResult(
            clarification_needed=False,
            clarification_questions=[],
            queries=[
                {"text": "запрос 1", "reason": "причина 1"},
                {"text": "запрос 2", "reason": "причина 2"}
            ],
            search_params={},
            confidence=0.8,
            reasoning="тест"
        )
        
        queries = agent.get_queries_text(result)
        assert queries == ["запрос 1", "запрос 2"]


class TestSearchTool:
    """Тесты для SearchTool."""
    
    def test_init(self):
        """Тест инициализации."""
        tool = SearchTool()
        assert tool.client is not None
        assert tool.embedder is not None
    
    def test_tokenize_text(self):
        """Тест токенизации."""
        tool = SearchTool()
        
        tokens = tool._tokenize_text("подача заявки на подключение")
        assert isinstance(tokens, list)
        assert len(tokens) > 0
    
    def test_search_request(self):
        """Тест создания SearchRequest."""
        request = SearchRequest(
            query="тестовый запрос",
            k=5,
            pref_weight=0.4,
            hype_weight=0.3,
            lexical_weight=0.2,
            contextual_weight=0.1
        )
        
        assert request.query == "тестовый запрос"
        assert request.k == 5
        assert abs(request.pref_weight + request.hype_weight + 
                   request.lexical_weight + request.contextual_weight - 1.0) < 0.01


class TestSearchAgent:
    """Тесты для SearchAgent."""
    
    def test_init(self):
        """Тест инициализации."""
        agent = SearchAgent()
        assert agent.search_tool is not None
        assert agent.query_generator is not None
    
    def test_format_results(self):
        """Тест форматирования результатов."""
        agent = SearchAgent()
        
        results = [
            SearchResult(
                id="1",
                content="Тестовый контент",
                summary="Тестовое саммари",
                category="Тест",
                filename="test_doc",
                breadcrumbs="Раздел 1",
                score_hybrid=0.9,
                score_semantic=0.8,
                score_lexical=0.7,
                metadata={}
            )
        ]
        
        formatted = agent.format_results(results, top_k=1)
        assert "Тестовый контент" in formatted
        assert "test_doc" in formatted


class TestResponseAgent:
    """Тесты для ResponseAgent."""
    
    def test_init(self):
        """Тест инициализации."""
        agent = ResponseAgent()
        assert agent.client is not None
        assert agent.model is not None
    
    def test_format_context(self):
        """Тест форматирования контекста."""
        agent = ResponseAgent()
        
        results = [
            SearchResult(
                id="1",
                content="Контент 1",
                summary="Саммари 1",
                category="Категория 1",
                filename="doc1",
                breadcrumbs="Раздел 1",
                score_hybrid=0.9,
                score_semantic=0.8,
                score_lexical=0.7,
                metadata={}
            )
        ]
        
        context = agent._format_context(results)
        assert "doc1" in context
        assert "Контент 1" in context
    
    def test_generate_clarification_response(self):
        """Тест генерации уточняющего ответа."""
        agent = ResponseAgent()
        
        response = agent.generate_clarification_response(
            user_query="Сколько стоит?",
            clarification_questions=[
                "Вас интересует стоимость подключения?",
                "Вы физическое или юридическое лицо?"
            ]
        )
        
        assert "Сколько стоит" in response
        assert "Вас интересует стоимость подключения?" in response


class TestAgenticRAG:
    """Тесты для основной системы AgenticRAG."""
    
    def test_init(self):
        """Тест инициализации."""
        rag = AgenticRAG()
        assert rag.search_agent is not None
        assert rag.response_agent is not None
        assert rag.history == ""
        assert rag.category == "не известна"
    
    def test_set_category(self):
        """Тест установки категории."""
        rag = AgenticRAG()
        rag.set_category("юридическое лицо")
        assert rag.category == "юридическое лицо"
    
    def test_reset_history(self):
        """Тест сброса истории."""
        rag = AgenticRAG()
        rag.history = "Вопрос 1\nОтвет 1\n"
        rag.reset_history()
        assert rag.history == ""
    
    def test_get_system_prompt(self):
        """Тест получения системного промпта."""
        rag = AgenticRAG()
        prompt = rag.get_system_prompt()
        assert "Башкирэнерго" in prompt
        assert "поиск" in prompt.lower()


def run_tests():
    """Запуск тестов."""
    pytest.main([__file__, "-v"])


if __name__ == "__main__":
    run_tests()
