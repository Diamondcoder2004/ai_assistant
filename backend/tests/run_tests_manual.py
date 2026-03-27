"""
Тестовый скрипт для проверки функциональности без pytest

Запуск: python run_tests_manual.py
"""
import sys
import time
import logging
from unittest.mock import patch, MagicMock

# Добавляем backend в path
sys.path.insert(0, r'd:\ai_assistant\backend')

from agents.query_generator import QueryGeneratorAgent, QueryGenerationResult
from agents.search_agent import SearchAgent
from agents.response_agent import ResponseAgent
from tools.search_tool import SearchTool, SearchRequest, SearchResult

logging.basicConfig(level=logging.CRITICAL)


class TestRunner:
    """Простой тестовый раннер."""
    
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
    
    def run_test(self, name, test_func):
        """Запуск одного теста."""
        print(f"  Running: {name}...", end=" ")
        try:
            test_func()
            print("✓ PASSED")
            self.passed += 1
        except AssertionError as e:
            print(f"✗ FAILED: {e}")
            self.failed += 1
            self.errors.append((name, str(e)))
        except Exception as e:
            print(f"✗ ERROR: {e}")
            self.failed += 1
            self.errors.append((name, f"{type(e).__name__}: {e}"))
    
    def summary(self):
        """Вывод итогов."""
        print(f"\n{'='*60}")
        print(f"TOTAL: {self.passed + self.failed} tests")
        print(f"PASSED: {self.passed}")
        print(f"FAILED: {self.failed}")
        
        if self.errors:
            print(f"\nErrors:")
            for name, error in self.errors:
                print(f"  - {name}: {error}")
        
        return self.failed == 0


# =============================================================================
# TESTS: BM25 CACHING
# =============================================================================

def test_bm25_load_once():
    """Проверка, что BM25 загружается только один раз."""
    tool = SearchTool()
    
    with patch.object(tool.client, 'scroll') as mock_scroll:
        mock_scroll.side_effect = [([], None), ([], None)]
        
        try:
            tool.search(SearchRequest(query="тест", k=5))
        except Exception:
            pass
        
        call_count_after_first = mock_scroll.call_count
        
        try:
            tool.search(SearchRequest(query="тест2", k=5))
        except Exception:
            pass
        
        call_count_after_second = mock_scroll.call_count
        
        assert call_count_after_second == call_count_after_first, \
            "BM25 кэш не работает"

def test_bm25_force_reload():
    """Проверка, что force=True перезагружает кэш."""
    tool = SearchTool()
    
    with patch.object(tool.client, 'scroll') as mock_scroll:
        mock_scroll.side_effect = [([], None), ([], None)]
        
        try:
            tool.search(SearchRequest(query="тест", k=5))
        except Exception:
            pass
        
        tool.load(force=True)
        
        assert mock_scroll.call_count >= 2, "force=True не перезагружает кэш"


# =============================================================================
# TESTS: PARAMETER BOUNDARIES
# =============================================================================

def test_k_min_boundary():
    """Проверка минимального k=1."""
    request = SearchRequest(query="тест", k=1)
    assert request.k == 1

def test_k_max_boundary():
    """Проверка максимального k=100."""
    request = SearchRequest(query="тест", k=100)
    assert request.k == 100

def test_weights_sum_to_one():
    """Проверка суммы весов = 1.0."""
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

def test_zero_weight():
    """Проверка нулевого веса."""
    request = SearchRequest(
        query="тест",
        pref_weight=0.5,
        hype_weight=0.5,
        lexical_weight=0.0,
        contextual_weight=0.0
    )
    
    assert request.lexical_weight == 0.0
    assert request.contextual_weight == 0.0

def test_all_weight_on_one():
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
# TESTS: USER HINTS
# =============================================================================

def test_user_hints_k_in_prompt():
    """Проверка, что user_hints['k'] попадает в промпт."""
    agent = QueryGeneratorAgent()
    
    user_hints = {"k": 15}
    
    mock_response_data = {
        "clarification_needed": False,
        "clarification_questions": [],
        "queries": [{"text": "тест", "reason": "тест"}],
        "search_params": {"k": 15},
        "confidence": 0.8,
        "reasoning": "тест"
    }
    
    with patch.object(agent.client.chat.completions, 'create') as mock_create:
        mock_create.return_value.choices[0].message.content = str(mock_response_data)
        
        result = agent.generate("тест", user_hints=user_hints)
        
        call_args = mock_create.call_args
        prompt = call_args[1]['messages'][1]['content']
        
        assert "k" in prompt.lower() or "15" in prompt, "user_hints не в промпте"

def test_user_hints_temperature_to_llm():
    """Проверка, что temperature передаётся в LLM."""
    agent = QueryGeneratorAgent()
    
    mock_response_data = {
        "clarification_needed": False,
        "clarification_questions": [],
        "queries": [{"text": "тест", "reason": "тест"}],
        "search_params": {"k": 10},
        "confidence": 0.8,
        "reasoning": "тест"
    }
    
    with patch.object(agent.client.chat.completions, 'create') as mock_create:
        mock_create.return_value.choices[0].message.content = str(mock_response_data)
        
        result = agent.generate("тест", temperature=1.2)
        
        call_args = mock_create.call_args
        assert call_args[1]['temperature'] == 1.2, "temperature не передан"

def test_user_hints_max_tokens_in_prompt():
    """Проверка, что max_tokens попадает в промпт через user_hints."""
    agent = QueryGeneratorAgent()
    
    user_hints = {"max_tokens": 3000}
    
    mock_response_data = {
        "clarification_needed": False,
        "clarification_questions": [],
        "queries": [{"text": "тест", "reason": "тест"}],
        "search_params": {"k": 10, "max_tokens": 3000},
        "confidence": 0.8,
        "reasoning": "тест"
    }
    
    with patch.object(agent.client.chat.completions, 'create') as mock_create:
        mock_create.return_value.choices[0].message.content = str(mock_response_data)
        
        result = agent.generate("тест", user_hints=user_hints)
        
        call_args = mock_create.call_args
        prompt = call_args[1]['messages'][1]['content']
        
        # Проверяем, что max_tokens был в промпте
        assert "max_tokens" in prompt.lower() or "3000" in prompt, "max_tokens не в промпте"

def test_no_user_hints_defaults():
    """Проверка дефолтных значений без user_hints."""
    agent = QueryGeneratorAgent()
    
    mock_response_data = {
        "clarification_needed": False,
        "clarification_questions": [],
        "queries": [{"text": "тест", "reason": "тест"}],
        "search_params": {"k": 10},
        "confidence": 0.8,
        "reasoning": "тест"
    }
    
    with patch.object(agent.client.chat.completions, 'create') as mock_create:
        mock_create.return_value.choices[0].message.content = str(mock_response_data)
        
        result = agent.generate("тест", user_hints=None)
        
        assert result.search_params.get("k") == 10, "k не равно дефолту"


# =============================================================================
# TESTS: UTILITY
# =============================================================================

def test_tokenize_text():
    """Тест токенизации."""
    tool = SearchTool()
    
    text = "подача заявки на подключение"
    tokens = tool._tokenize_text(text)
    
    assert isinstance(tokens, list)
    assert len(tokens) > 0

def test_format_context():
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

def test_format_results():
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
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("="*60)
    print("MANUAL TEST RUNNER")
    print("="*60)
    
    runner = TestRunner()
    
    print("\n--- BM25 Caching ---")
    runner.run_test("test_bm25_load_once", test_bm25_load_once)
    runner.run_test("test_bm25_force_reload", test_bm25_force_reload)
    
    print("\n--- Parameter Boundaries ---")
    runner.run_test("test_k_min_boundary", test_k_min_boundary)
    runner.run_test("test_k_max_boundary", test_k_max_boundary)
    runner.run_test("test_weights_sum_to_one", test_weights_sum_to_one)
    runner.run_test("test_zero_weight", test_zero_weight)
    runner.run_test("test_all_weight_on_one", test_all_weight_on_one)
    
    print("\n--- User Hints ---")
    runner.run_test("test_user_hints_k_in_prompt", test_user_hints_k_in_prompt)
    runner.run_test("test_user_hints_temperature_to_llm", test_user_hints_temperature_to_llm)
    runner.run_test("test_user_hints_max_tokens_in_prompt", test_user_hints_max_tokens_in_prompt)
    runner.run_test("test_no_user_hints_defaults", test_no_user_hints_defaults)
    
    print("\n--- Utility Functions ---")
    runner.run_test("test_tokenize_text", test_tokenize_text)
    runner.run_test("test_format_context", test_format_context)
    runner.run_test("test_format_results", test_format_results)
    
    # Итоги
    success = runner.summary()
    
    sys.exit(0 if success else 1)
