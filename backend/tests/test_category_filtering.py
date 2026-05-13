"""Tests for category-aware partial filtering in SearchAgent."""
import pytest
from unittest.mock import MagicMock, patch
from dataclasses import dataclass
from typing import List, Dict, Any

from agents.search_agent import SearchAgent, blend_results
from tools.search_tool import SearchResult


# =============================================================================
# blend_results() unit tests
# =============================================================================

@pytest.fixture
def make_result():
    """Factory for SearchResult test doubles."""
    def _make(
        id: str,
        score_hybrid: float,
        category: str = "\u0422\u041f\u041f",
    ) -> SearchResult:
        return SearchResult(
            id=id,
            content="test content",
            summary="test summary",
            category=category,
            filename="test_file",
            breadcrumbs="test",
            score_hybrid=score_hybrid,
            score_semantic=score_hybrid * 0.8,
            score_lexical=score_hybrid * 0.6,
            metadata={},
            collection_name="normative_documents",
        )
    return _make


class TestBlendResults:
    """Tests for the standalone blend_results() function."""

    def test_basic_blend(self, make_result):
        """Filtered results come first, unfiltered fill remaining slots."""
        filtered = [
            make_result("A", 0.9),
            make_result("B", 0.8),
        ]
        unfiltered = [
            make_result("C", 0.85),
            make_result("D", 0.7),
        ]
        blended = blend_results(filtered, unfiltered, total_k=3)
        assert len(blended) == 3
        ids = [r.id for r in blended]
        assert ids[0] == "A"  # highest score
        assert ids[1] in ("B", "C")

    def test_dedup_by_id(self, make_result):
        """Duplicate chunk_ids are skipped (filtered takes priority)."""
        filtered = [
            make_result("A", 0.9),
            make_result("B", 0.8),
        ]
        unfiltered = [
            make_result("B", 0.8),  # duplicate of B
            make_result("C", 0.7),
        ]
        blended = blend_results(filtered, unfiltered, total_k=3)
        assert len(blended) == 3
        assert {r.id for r in blended} == {"A", "B", "C"}

    def test_sorted_by_hybrid_score(self, make_result):
        """Results are sorted by score_hybrid descending."""
        filtered = [
            make_result("B", 0.8),
        ]
        unfiltered = [
            make_result("A", 0.9),
            make_result("C", 0.7),
        ]
        blended = blend_results(filtered, unfiltered, total_k=3)
        assert [r.id for r in blended] == ["A", "B", "C"]

    def test_empty_filtered_graceful(self, make_result):
        """Empty filtered list falls back to unfiltered."""
        blended = blend_results(
            filtered=[],
            unfiltered=[make_result("A", 0.9), make_result("B", 0.8)],
            total_k=3,
        )
        assert len(blended) == 2
        assert [r.id for r in blended] == ["A", "B"]

    def test_empty_unfiltered_graceful(self, make_result):
        """Empty unfiltered list still returns filtered."""
        blended = blend_results(
            filtered=[make_result("A", 0.9)],
            unfiltered=[],
            total_k=3,
        )
        assert len(blended) == 1
        assert blended[0].id == "A"

    def test_limit_total_k(self, make_result):
        """Results are limited to total_k."""
        filtered = [make_result("A", 0.9), make_result("B", 0.8)]
        unfiltered = [make_result("C", 0.7), make_result("D", 0.6)]
        blended = blend_results(filtered, unfiltered, total_k=2)
        assert len(blended) == 2


# =============================================================================
# QueryGenerationResult category tests
# =============================================================================

class TestQueryGeneratorCategory:
    """Tests for detected_category in QueryGenerationResult."""

    def test_from_dict_parses_detected_category(self):
        """detected_category is parsed from LLM JSON dict."""
        from agents.query_generator import QueryGenerationResult
        data = {
            "clarification_needed": False,
            "clarification_questions": [],
            "queries": [{"text": "test", "reason": "test"}],
            "search_params": {},
            "confidence": 0.9,
            "reasoning": "test",
            "detected_category": "\u041b\u041a",
        }
        result = QueryGenerationResult.from_dict(data)
        assert result.detected_category == "\u041b\u041a"

    def test_from_dict_default_unknown(self):
        """Missing detected_category defaults to 'не известна'."""
        from agents.query_generator import QueryGenerationResult
        data = {
            "clarification_needed": False,
            "clarification_questions": [],
            "queries": [{"text": "test", "reason": "test"}],
            "search_params": {},
            "confidence": 0.5,
            "reasoning": "test",
        }
        result = QueryGenerationResult.from_dict(data)
        assert result.detected_category == "не известна"

    def test_default_result_has_unknown(self):
        """_default_result() sets detected_category = 'не известна'."""
        from agents.query_generator import QueryGeneratorAgent
        agent = QueryGeneratorAgent()
        result = agent._default_result("тестовый запрос")
        assert result.detected_category == "не известна"

    def test_dataclass_default_field(self):
        """Default value of detected_category is 'не известна'."""
        from agents.query_generator import QueryGenerationResult
        result = QueryGenerationResult(
            clarification_needed=False,
            clarification_questions=[],
            queries=[],
            search_params={},
            confidence=0.5,
            reasoning="",
        )
        assert result.detected_category == "не известна"


# =============================================================================
# Prompt content tests
# =============================================================================

class TestQueryGenerationPromptCategory:
    """Tests for category detection in prompts."""

    def test_prompt_contains_category_section(self):
        """Prompt has 'Детекция категории вопроса' section."""
        from prompts.query_generation import QUERY_GENERATION_PROMPT
        assert "Детекция категории" in QUERY_GENERATION_PROMPT

    def test_prompt_contains_category_lk(self):
        """Prompt mentions ЛК category criteria."""
        from prompts.query_generation import QUERY_GENERATION_PROMPT
        assert "ЛК" in QUERY_GENERATION_PROMPT

    def test_prompt_contains_category_du(self):
        """Prompt mentions ДУ category criteria."""
        from prompts.query_generation import QUERY_GENERATION_PROMPT
        assert "ДУ" in QUERY_GENERATION_PROMPT

    def test_prompt_contains_category_tpp(self):
        """Prompt mentions ТПП category criteria."""
        from prompts.query_generation import QUERY_GENERATION_PROMPT
        assert "ТПП" in QUERY_GENERATION_PROMPT

    def test_prompt_contains_detected_category_field(self):
        """Prompt includes detected_category in JSON format example."""
        from prompts.query_generation import QUERY_GENERATION_PROMPT
        assert "detected_category" in QUERY_GENERATION_PROMPT

    def test_get_prompt_still_works(self):
        """get_query_generation_prompt still returns valid prompt."""
        from prompts.query_generation import get_query_generation_prompt
        prompt = get_query_generation_prompt(
            user_query="тест",
            history="",
            category="ТПП",
        )
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "Детекция категории" in prompt


# =============================================================================
# SearchAgent integration tests (mocked sub-components)
# =============================================================================

class TestSearchAgentCategory:
    """Tests for category-aware blended search in SearchAgent."""

    @patch('agents.search_agent.config')
    @patch('agents.search_agent.SearchTool')
    @patch('agents.search_agent.QueryGeneratorAgent')
    def test_blended_search_for_lk(
        self, mock_qg_class, mock_st_class, mock_config
    ):
        """Detected ЛК triggers blended search (not single search)."""
        mock_config.CATEGORY_FILTER_ENABLED = True
        mock_config.CATEGORY_FILTER_BLEND_RATIO = 0.3
        mock_config.REGULATORY_QUERY_BOOST = False
        mock_config.SOURCE_QUALITY_THRESHOLD = 0.25

        mock_qg = MagicMock()
        mock_qg_class.return_value = mock_qg
        mock_qg.generate.return_value = MagicMock(
            clarification_needed=False,
            clarification_questions=[],
            queries=[MagicMock(text="тестовый запрос")],
            search_params={"k": 10, "strategy": "concat"},
            confidence=0.85,
            reasoning="test",
            detected_category="ЛК",
        )
        mock_qg.get_queries_text.return_value = ["тестовый запрос"]
        mock_qg.needs_clarification.return_value = False

        mock_st = MagicMock()
        mock_st_class.return_value = mock_st
        mock_st.search_multi.return_value = [
            SearchResult(
                id="1", content="ЛК content", summary="s",
                category="ЛК", filename="f", breadcrumbs="b",
                score_hybrid=0.9, score_semantic=0.8, score_lexical=0.7,
                metadata={}, collection_name="operational_content",
            )
        ]

        agent = SearchAgent()
        result = agent.search(
            user_query="как войти в личный кабинет?",
        )

        assert mock_st.search_multi.call_count >= 2
        assert len(result["results"]) >= 1
        assert result["clarification_needed"] is False

    @patch('agents.search_agent.config')
    @patch('agents.search_agent.SearchTool')
    @patch('agents.search_agent.QueryGeneratorAgent')
    def test_no_filter_for_tpp(
        self, mock_qg_class, mock_st_class, mock_config
    ):
        """detected_category='ТПП' should NOT trigger blended search."""
        mock_config.CATEGORY_FILTER_ENABLED = True
        mock_config.CATEGORY_FILTER_BLEND_RATIO = 0.3
        mock_config.REGULATORY_QUERY_BOOST = False
        mock_config.SOURCE_QUALITY_THRESHOLD = 0.25

        mock_qg = MagicMock()
        mock_qg_class.return_value = mock_qg
        mock_qg.generate.return_value = MagicMock(
            clarification_needed=False,
            clarification_questions=[],
            queries=[MagicMock(text="тестовый запрос")],
            search_params={"k": 10, "strategy": "concat"},
            confidence=0.9,
            reasoning="test",
            detected_category="ТПП",
        )
        mock_qg.get_queries_text.return_value = ["тестовый запрос"]
        mock_qg.needs_clarification.return_value = False

        mock_st = MagicMock()
        mock_st_class.return_value = mock_st
        mock_st.search_multi.return_value = [
            SearchResult(
                id="1", content="ТПП content", summary="s",
                category="ТПП", filename="f", breadcrumbs="b",
                score_hybrid=0.9, score_semantic=0.8, score_lexical=0.7,
                metadata={}, collection_name="normative_documents",
            )
        ]

        agent = SearchAgent()
        result = agent.search(user_query="сроки технологического присоединения?")

        assert mock_st.search_multi.call_count >= 1

    @patch('agents.search_agent.config')
    @patch('agents.search_agent.SearchTool')
    @patch('agents.search_agent.QueryGeneratorAgent')
    def test_low_confidence_skips_filter(
        self, mock_qg_class, mock_st_class, mock_config
    ):
        """confidence < 0.6 should NOT trigger blended search even for ЛК."""
        mock_config.CATEGORY_FILTER_ENABLED = True
        mock_config.CATEGORY_FILTER_BLEND_RATIO = 0.3
        mock_config.REGULATORY_QUERY_BOOST = False
        mock_config.SOURCE_QUALITY_THRESHOLD = 0.25

        mock_qg = MagicMock()
        mock_qg_class.return_value = mock_qg
        mock_qg.generate.return_value = MagicMock(
            clarification_needed=False,
            clarification_questions=[],
            queries=[MagicMock(text="тестовый запрос")],
            search_params={"k": 10, "strategy": "concat"},
            confidence=0.45,
            reasoning="low confidence",
            detected_category="ЛК",
        )
        mock_qg.get_queries_text.return_value = ["тестовый запрос"]
        mock_qg.needs_clarification.return_value = False

        mock_st = MagicMock()
        mock_st_class.return_value = mock_st
        mock_st.search_multi.return_value = []

        agent = SearchAgent()
        result = agent.search(user_query="какой-то вопрос")

        assert mock_st.search_multi.call_count >= 1

    @patch('agents.search_agent.config')
    @patch('agents.search_agent.SearchTool')
    @patch('agents.search_agent.QueryGeneratorAgent')
    def test_skip_unknown_category(
        self, mock_qg_class, mock_st_class, mock_config
    ):
        """detected_category='не известна' -> single search, no blend."""
        mock_config.CATEGORY_FILTER_ENABLED = True
        mock_config.CATEGORY_FILTER_BLEND_RATIO = 0.3
        mock_config.REGULATORY_QUERY_BOOST = False
        mock_config.SOURCE_QUALITY_THRESHOLD = 0.25

        mock_qg = MagicMock()
        mock_qg_class.return_value = mock_qg
        mock_qg.generate.return_value = MagicMock(
            clarification_needed=False,
            clarification_questions=[],
            queries=[MagicMock(text="тестовый запрос")],
            search_params={"k": 10, "strategy": "concat"},
            confidence=0.7,
            reasoning="test",
            detected_category="не известна",
        )
        mock_qg.get_queries_text.return_value = ["тестовый запрос"]
        mock_qg.needs_clarification.return_value = False

        mock_st = MagicMock()
        mock_st_class.return_value = mock_st
        mock_st.search_multi.return_value = []

        agent = SearchAgent()
        result = agent.search(user_query="вопрос без категории")
        assert mock_st.search_multi.call_count >= 1

    @patch('agents.search_agent.config')
    @patch('agents.search_agent.SearchTool')
    @patch('agents.search_agent.QueryGeneratorAgent')
    def test_skip_query_generator_no_blend(
        self, mock_qg_class, mock_st_class, mock_config
    ):
        """skip_query_generator=True -> single search, no blend."""
        mock_config.CATEGORY_FILTER_ENABLED = True
        mock_config.CATEGORY_FILTER_BLEND_RATIO = 0.3
        mock_config.REGULATORY_QUERY_BOOST = False
        mock_config.SOURCE_QUALITY_THRESHOLD = 0.25

        mock_st = MagicMock()
        mock_st_class.return_value = mock_st
        mock_st.search_multi.return_value = []

        agent = SearchAgent()
        result = agent.search(
            user_query="простой запрос",
            skip_query_generator=True,
        )
        assert mock_st.search_multi.call_count >= 1
