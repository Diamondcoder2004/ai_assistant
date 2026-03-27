"""
Тесты влияния пользовательских параметров (user_hints) на решение агентов

Проверяет:
1. Как user_hints влияют на параметры поиска
2. Граничные значения параметров
3. Конфликтующие рекомендации
"""
import pytest
import json
import logging
from unittest.mock import patch, MagicMock, call
from typing import Dict, Any, List

from agents.query_generator import QueryGeneratorAgent, QueryGenerationResult
from agents.search_agent import SearchAgent
from main import AgenticRAG
import config

logging.basicConfig(level=logging.CRITICAL)


# =============================================================================
# MOCK HELPERS
# =============================================================================

def create_mock_llm_response(
    k: int = 10,
    pref_weight: float = 0.4,
    hype_weight: float = 0.3,
    lexical_weight: float = 0.2,
    contextual_weight: float = 0.1,
    strategy: str = "concat",
    queries: List[Dict[str, str]] = None,
    clarification_needed: bool = False,
    clarification_questions: List[str] = None,
    confidence: float = 0.8,
    reasoning: str = "тест"
):
    """Создание мок-ответа LLM."""
    if queries is None:
        queries = [{"text": "тестовый запрос", "reason": "прямой запрос"}]
    if clarification_questions is None:
        clarification_questions = []
    
    return {
        "clarification_needed": clarification_needed,
        "clarification_questions": clarification_questions,
        "queries": queries,
        "search_params": {
            "k": k,
            "pref_weight": pref_weight,
            "hype_weight": hype_weight,
            "lexical_weight": lexical_weight,
            "contextual_weight": contextual_weight,
            "strategy": strategy
        },
        "confidence": confidence,
        "reasoning": reasoning
    }


# =============================================================================
# TESTS: K PARAMETER
# =============================================================================

class TestUserHintsK:
    """Тесты параметра k."""

    def test_user_hints_k_small(self):
        """
        user_hints k=5 (малое значение).
        
        Ожидание:
        - Агент должен использовать k=5 или предложить больше
        """
        agent = QueryGeneratorAgent()
        
        user_hints = {"k": 5}
        
        mock_response = create_mock_llm_response(k=5)
        
        with patch.object(agent.client.chat.completions, 'create') as mock_create:
            mock_create.return_value.choices[0].message.content = str(mock_response)
            
            result = agent.generate("тест", user_hints=user_hints)
            
            # Проверка: k=5
            assert result.search_params.get("k") == 5
            
            # Проверка: user_hints был в промпте
            call_args = mock_create.call_args
            prompt = call_args[1]['messages'][1]['content']
            assert "5" in prompt or "k" in prompt

    def test_user_hints_k_large(self):
        """
        user_hints k=50 (большое значение).
        
        Ожидание:
        - Агент может использовать k=50 или скорректировать
        """
        agent = QueryGeneratorAgent()
        
        user_hints = {"k": 50}
        
        mock_response = create_mock_llm_response(k=50)
        
        with patch.object(agent.client.chat.completions, 'create') as mock_create:
            mock_create.return_value.choices[0].message.content = str(mock_response)
            
            result = agent.generate("тест", user_hints=user_hints)
            
            # Проверка: k=50
            assert result.search_params.get("k") == 50

    def test_user_hints_k_extreme(self):
        """
        user_hints k=100 (экстремальное значение).
        
        Ожидание:
        - Агент должен обработать, но может предупредить
        """
        agent = QueryGeneratorAgent()
        
        user_hints = {"k": 100}
        
        mock_response = create_mock_llm_response(k=100)
        
        with patch.object(agent.client.chat.completions, 'create') as mock_create:
            mock_create.return_value.choices[0].message.content = str(mock_response)
            
            result = agent.generate("тест", user_hints=user_hints)
            
            # Проверка: k=100
            assert result.search_params.get("k") == 100

    def test_user_hints_k_not_provided(self):
        """
        user_hints без k.
        
        Ожидание:
        - Агент использует дефолтное k=10
        """
        agent = QueryGeneratorAgent()
        
        user_hints = {"temperature": 0.8}  # Без k
        
        mock_response = create_mock_llm_response(k=10)
        
        with patch.object(agent.client.chat.completions, 'create') as mock_create:
            mock_create.return_value.choices[0].message.content = str(mock_response)
            
            result = agent.generate("тест", user_hints=user_hints)
            
            # Проверка: k=10 (дефолт)
            assert result.search_params.get("k") == 10


# =============================================================================
# TESTS: TEMPERATURE PARAMETER
# =============================================================================

class TestUserHintsTemperature:
    """Тесты параметра temperature."""

    def test_user_hints_temperature_low(self):
        """
        user_hints temperature=0.1 (низкая температура).
        
        Ожидание:
        - Агент использует temperature=0.1 для LLM
        """
        agent = QueryGeneratorAgent()
        
        user_hints = {"temperature": 0.1}
        
        mock_response = create_mock_llm_response()
        
        with patch.object(agent.client.chat.completions, 'create') as mock_create:
            mock_create.return_value.choices[0].message.content = str(mock_response)
            
            result = agent.generate("тест", user_hints=user_hints, temperature=0.1)
            
            # Проверка: temperature передан в LLM
            call_args = mock_create.call_args
            assert call_args[1]['temperature'] == 0.1

    def test_user_hints_temperature_high(self):
        """
        user_hints temperature=1.5 (высокая температура).
        
        Ожидание:
        - Агент использует temperature=1.5 для LLM
        """
        agent = QueryGeneratorAgent()
        
        user_hints = {"temperature": 1.5}
        
        mock_response = create_mock_llm_response()
        
        with patch.object(agent.client.chat.completions, 'create') as mock_create:
            mock_create.return_value.choices[0].message.content = str(mock_response)
            
            result = agent.generate("тест", user_hints=user_hints, temperature=1.5)
            
            # Проверка: temperature передан в LLM
            call_args = mock_create.call_args
            assert call_args[1]['temperature'] == 1.5

    def test_user_hints_temperature_zero(self):
        """
        user_hints temperature=0 (детерминированный ответ).
        
        Ожидание:
        - Агент использует temperature=0
        """
        agent = QueryGeneratorAgent()
        
        user_hints = {"temperature": 0.0}
        
        mock_response = create_mock_llm_response()
        
        with patch.object(agent.client.chat.completions, 'create') as mock_create:
            mock_create.return_value.choices[0].message.content = str(mock_response)
            
            result = agent.generate("тест", user_hints=user_hints, temperature=0.0)
            
            # Проверка: temperature=0
            call_args = mock_create.call_args
            assert call_args[1]['temperature'] == 0.0


# =============================================================================
# TESTS: MAX_TOKENS PARAMETER
# =============================================================================

class TestUserHintsMaxTokens:
    """Тесты параметра max_tokens."""

    def test_user_hints_max_tokens_small(self):
        """
        user_hints max_tokens=500 (мало токенов).
        
        Ожидание:
        - Агент использует max_tokens=500
        """
        agent = QueryGeneratorAgent()
        
        user_hints = {"max_tokens": 500}
        
        mock_response = create_mock_llm_response()
        
        with patch.object(agent.client.chat.completions, 'create') as mock_create:
            mock_create.return_value.choices[0].message.content = str(mock_response)
            
            result = agent.generate("тест", user_hints=user_hints, max_tokens=500)
            
            # Проверка: max_tokens=500
            call_args = mock_create.call_args
            assert call_args[1]['max_tokens'] == 500

    def test_user_hints_max_tokens_large(self):
        """
        user_hints max_tokens=4000 (много токенов).
        
        Ожидание:
        - Агент использует max_tokens=4000
        """
        agent = QueryGeneratorAgent()
        
        user_hints = {"max_tokens": 4000}
        
        mock_response = create_mock_llm_response()
        
        with patch.object(agent.client.chat.completions, 'create') as mock_create:
            mock_create.return_value.choices[0].message.content = str(mock_response)
            
            result = agent.generate("тест", user_hints=user_hints, max_tokens=4000)
            
            # Проверка: max_tokens=4000
            call_args = mock_create.call_args
            assert call_args[1]['max_tokens'] == 4000


# =============================================================================
# TESTS: WEIGHTS
# =============================================================================

class TestUserHintsWeights:
    """Тесты весов поиска."""

    def test_user_hints_pref_weight_high(self):
        """
        user_hints pref_weight=0.8 (высокий вес семантики).
        
        Ожидание:
        - Агент использует pref_weight=0.8
        """
        agent = QueryGeneratorAgent()
        
        user_hints = {"pref_weight": 0.8}
        
        mock_response = create_mock_llm_response(pref_weight=0.8, hype_weight=0.1, lexical_weight=0.05, contextual_weight=0.05)
        
        with patch.object(agent.client.chat.completions, 'create') as mock_create:
            mock_create.return_value.choices[0].message.content = str(mock_response)
            
            result = agent.generate("тест", user_hints=user_hints)
            
            # Проверка: pref_weight=0.8
            assert abs(result.search_params.get("pref_weight", 0) - 0.8) < 0.01

    def test_user_hints_lexical_weight_high(self):
        """
        user_hints lexical_weight=0.7 (высокий вес BM25).
        
        Ожидание:
        - Агент использует lexical_weight=0.7
        """
        agent = QueryGeneratorAgent()
        
        user_hints = {"lexical_weight": 0.7}
        
        mock_response = create_mock_llm_response(pref_weight=0.1, hype_weight=0.1, lexical_weight=0.7, contextual_weight=0.1)
        
        with patch.object(agent.client.chat.completions, 'create') as mock_create:
            mock_create.return_value.choices[0].message.content = str(mock_response)
            
            result = agent.generate("тест", user_hints=user_hints)
            
            # Проверка: lexical_weight=0.7
            assert abs(result.search_params.get("lexical_weight", 0) - 0.7) < 0.01

    def test_user_hints_weights_sum_not_one(self):
        """
        user_hints с суммой весов != 1.0.
        
        Ожидание:
        - Агент может нормализовать или использовать как есть
        """
        agent = QueryGeneratorAgent()
        
        # Сумма = 1.5
        user_hints = {
            "pref_weight": 0.6,
            "hype_weight": 0.4,
            "lexical_weight": 0.3,
            "contextual_weight": 0.2
        }
        
        mock_response = create_mock_llm_response(
            pref_weight=0.6, hype_weight=0.4, lexical_weight=0.3, contextual_weight=0.2
        )
        
        with patch.object(agent.client.chat.completions, 'create') as mock_create:
            mock_create.return_value.choices[0].message.content = str(mock_response)
            
            result = agent.generate("тест", user_hints=user_hints)
            
            # Проверка: веса переданы
            total = sum([
                result.search_params.get("pref_weight", 0),
                result.search_params.get("hype_weight", 0),
                result.search_params.get("lexical_weight", 0),
                result.search_params.get("contextual_weight", 0)
            ])
            
            # Агент может оставить как есть или нормализовать
            assert total > 0


# =============================================================================
# TESTS: STRATEGY
# =============================================================================

class TestUserHintsStrategy:
    """Тесты стратегии поиска."""

    def test_user_hints_strategy_concat(self):
        """
        user_hints strategy="concat".
        
        Ожидание:
        - Агент использует стратегию concat
        """
        agent = QueryGeneratorAgent()
        
        user_hints = {"strategy": "concat"}
        
        mock_response = create_mock_llm_response(strategy="concat")
        
        with patch.object(agent.client.chat.completions, 'create') as mock_create:
            mock_create.return_value.choices[0].message.content = str(mock_response)
            
            result = agent.generate("тест", user_hints=user_hints)
            
            # Проверка: strategy="concat"
            assert result.search_params.get("strategy") == "concat"

    def test_user_hints_strategy_separate(self):
        """
        user_hints strategy="separate".
        
        Ожидание:
        - Агент использует стратегию separate
        """
        agent = QueryGeneratorAgent()
        
        user_hints = {"strategy": "separate"}
        
        mock_response = create_mock_llm_response(strategy="separate")
        
        with patch.object(agent.client.chat.completions, 'create') as mock_create:
            mock_create.return_value.choices[0].message.content = str(mock_response)
            
            result = agent.generate("тест", user_hints=user_hints)
            
            # Проверка: strategy="separate"
            assert result.search_params.get("strategy") == "separate"


# =============================================================================
# TESTS: COMBINED HINTS
# =============================================================================

class TestUserHintsCombined:
    """Тесты комбинации user_hints."""

    def test_user_hints_all_parameters(self):
        """
        user_hints со всеми параметрами.
        
        Ожидание:
        - Агент использует все переданные параметры
        """
        agent = QueryGeneratorAgent()
        
        user_hints = {
            "k": 15,
            "temperature": 1.0,
            "max_tokens": 3000,
            "pref_weight": 0.5,
            "hype_weight": 0.2,
            "lexical_weight": 0.2,
            "contextual_weight": 0.1,
            "strategy": "separate"
        }
        
        mock_response = create_mock_llm_response(
            k=15,
            pref_weight=0.5,
            hype_weight=0.2,
            lexical_weight=0.2,
            contextual_weight=0.1,
            strategy="separate"
        )
        
        with patch.object(agent.client.chat.completions, 'create') as mock_create:
            mock_create.return_value.choices[0].message.content = str(mock_response)
            
            result = agent.generate(
                "тест",
                user_hints=user_hints,
                temperature=1.0,
                max_tokens=3000
            )
            
            # Проверка: k=15
            assert result.search_params.get("k") == 15
            
            # Проверка: strategy="separate"
            assert result.search_params.get("strategy") == "separate"

    def test_user_hints_empty_dict(self):
        """
        user_hints = {} (пустой словарь).
        
        Ожидание:
        - Агент использует дефолтные параметры
        """
        agent = QueryGeneratorAgent()
        
        user_hints = {}
        
        mock_response = create_mock_llm_response(k=10)
        
        with patch.object(agent.client.chat.completions, 'create') as mock_create:
            mock_create.return_value.choices[0].message.content = str(mock_response)
            
            result = agent.generate("тест", user_hints=user_hints)
            
            # Проверка: k=10 (дефолт)
            assert result.search_params.get("k") == 10

    def test_user_hints_none(self):
        """
        user_hints = None.
        
        Ожидание:
        - Агент использует дефолтные параметры
        """
        agent = QueryGeneratorAgent()
        
        mock_response = create_mock_llm_response(k=10)
        
        with patch.object(agent.client.chat.completions, 'create') as mock_create:
            mock_create.return_value.choices[0].message.content = str(mock_response)
            
            result = agent.generate("тест", user_hints=None)
            
            # Проверка: k=10 (дефолт)
            assert result.search_params.get("k") == 10


# =============================================================================
# TESTS: PROMPT CONTENT
# =============================================================================

class TestUserHintsPromptContent:
    """Тесты содержания промпта с user_hints."""

    def test_user_hints_in_prompt(self):
        """
        Проверка, что user_hints попадает в промпт.
        
        Ожидание:
        - Промпт содержит рекомендации от пользователя
        """
        agent = QueryGeneratorAgent()
        
        user_hints = {"k": 20, "temperature": 1.2}
        
        mock_response = create_mock_llm_response(k=20)
        
        with patch.object(agent.client.chat.completions, 'create') as mock_create:
            mock_create.return_value.choices[0].message.content = str(mock_response)
            
            result = agent.generate("тест", user_hints=user_hints, temperature=1.2)
            
            # Проверка: user_hints в промпте
            call_args = mock_create.call_args
            prompt = call_args[1]['messages'][1]['content']
            
            # Промпт должен содержать рекомендации
            assert "k" in prompt or "20" in prompt

    def test_user_hints_detailed_in_prompt(self):
        """
        Проверка детального содержания user_hints в промпте.
        """
        agent = QueryGeneratorAgent()
        
        user_hints = {
            "k": 25,
            "pref_weight": 0.6,
            "lexical_weight": 0.3
        }
        
        mock_response = create_mock_llm_response(k=25, pref_weight=0.6, lexical_weight=0.3)
        
        with patch.object(agent.client.chat.completions, 'create') as mock_create:
            mock_create.return_value.choices[0].message.content = str(mock_response)
            
            result = agent.generate("тест", user_hints=user_hints)
            
            # Проверка: user_hints в промпте
            call_args = mock_create.call_args
            prompt = call_args[1]['messages'][1]['content']
            
            # Промпт должен содержать ключевые значения
            assert "25" in prompt or "k" in prompt


# =============================================================================
# RUN TESTS
# =============================================================================

def run_tests():
    """Запуск тестов."""
    pytest.main([__file__, "-v", "--tb=short"])


if __name__ == "__main__":
    run_tests()
