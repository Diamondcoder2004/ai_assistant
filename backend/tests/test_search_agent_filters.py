"""Tests for search agent filter integration."""
import pytest
from unittest.mock import MagicMock, patch
from qdrant_client.http import models

from agents.search_agent import SearchAgent
from tools.search_tool import SearchResult, build_qdrant_filter


class TestSearchAgentFilters:
    """Tests for document_filters integration in SearchAgent."""

    def test_build_filter_from_document_filters(self):
        """document_filters dict converts to Qdrant Filter."""
        doc_filters = {
            "category": ["ТПП"],
            "client_type": ["ФЛ"],
            "power_range": ["<15kW"],
        }
        qf = build_qdrant_filter(doc_filters)
        assert qf is not None
        assert len(qf.must) == 3

    def test_empty_document_filters_gives_none(self):
        """Empty document_filters gives None filter."""
        qf = build_qdrant_filter({})
        assert qf is None

    def test_none_document_filters_gives_none(self):
        """None document_filters gives None filter."""
        qf = build_qdrant_filter(None)
        assert qf is None

    @patch('agents.search_agent.SearchTool')
    @patch('agents.search_agent.QueryGeneratorAgent')
    def test_search_passes_filter_to_search_multi(self, mock_qg_class, mock_st_class):
        """Search agent passes qf_filter to search_multi."""
        # Setup mocks
        mock_qg = MagicMock()
        mock_qg_class.return_value = mock_qg
        mock_qg.generate.return_value = MagicMock(
            clarification_needed=False,
            clarification_questions=[],
            queries=[MagicMock(text="тестовый запрос")],
            search_params={"k": 10, "strategy": "concat"},
            confidence=0.9,
            reasoning="test",
        )
        mock_qg.get_queries_text.return_value = ["тестовый запрос"]
        mock_qg.needs_clarification.return_value = False

        mock_st = MagicMock()
        mock_st_class.return_value = mock_st
        mock_st.search_multi.return_value = [
            SearchResult(
                id="1", content="test", summary="s", category="ТПП",
                filename="f", breadcrumbs="b", score_hybrid=0.9,
                score_semantic=0.8, score_lexical=0.7,
                metadata={}, collection_name="normative_documents",
            )
        ]

        agent = SearchAgent()
        result = agent.search(
            user_query="Сколько стоит подключение?",
            document_filters={"category": ["ТПП"], "client_type": ["ФЛ"]},
        )

        # Verify search_multi was called with qf_filter
        call_args = mock_st.search_multi.call_args
        assert call_args is not None
        qf_filter = call_args.kwargs.get('qf_filter') or call_args[1].get('qf_filter')
        assert qf_filter is not None
        assert len(qf_filter.must) >= 1
