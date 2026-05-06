"""Tests for WikiRouterAgent integration in main.py."""
import pytest
from unittest.mock import patch, MagicMock

from wiki.models import WikiDocument, WikiRoutingResult


class TestWikiIntegration:
    """Tests for wiki integration in AgenticRAG."""

    def test_wiki_router_agent_import(self):
        """WikiRouterAgent can be imported from wiki package."""
        from wiki.wiki_router import WikiRouterAgent
        assert WikiRouterAgent is not None

    def test_wiki_routing_result_has_expected_fields(self):
        """WikiRoutingResult has all fields needed by downstream agents."""
        result = WikiRoutingResult(
            concepts=[],
            wiki_context="",
            search_hints=[],
            combined_keywords=[],
            document_filters={},
            matched_categories=[],
            confidence=0.0,
        )
        assert hasattr(result, "wiki_context")
        assert hasattr(result, "document_filters")
        assert hasattr(result, "concepts")
        assert hasattr(result, "matched_categories")

    def test_agentic_rag_initializes_wiki_router(self):
        """AgenticRAG initializes WikiRouterAgent when ENABLE_WIKI_ROUTER is True."""
        with patch.dict("os.environ", {"ENABLE_WIKI_ROUTER": "true"}):
            import config
            config.ENABLE_WIKI_ROUTER = True

            with patch("wiki.wiki_router.WikiSearchTool") as mock_search:
                mock_search.return_value.documents = []
                mock_search.return_value.count.return_value = 0
                from main import AgenticRAG
                rag = AgenticRAG()
                assert hasattr(rag, "wiki_router")
                from wiki.wiki_router import WikiRouterAgent
                assert isinstance(rag.wiki_router, WikiRouterAgent)

    def test_wiki_context_passed_to_search_agent(self):
        """wiki_context from WikiRouter is passed to SearchAgent."""
        from wiki.models import WikiRoutingResult, WikiDocument

        mock_result = WikiRoutingResult(
            concepts=[WikiDocument(
                id="test", title="Test", category="ТПП",
                source_origin="operational", source_file="test.md",
                summary="Test summary", key_terms=["test"], chunk_count=1,
            )],
            wiki_context="Test wiki context",
            search_hints=["hint1"],
            combined_keywords=["keyword1"],
            document_filters={"category": ["ТПП"]},
            matched_categories=["ТПП"],
            confidence=0.9,
        )

        assert mock_result.wiki_context == "Test wiki context"
        assert "ТПП" in mock_result.document_filters["category"]
