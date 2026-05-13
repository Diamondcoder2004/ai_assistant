"""
Integration test for dual collection search.
Verifies that config → search_tool → search_agent → prompts
all work together correctly.
"""
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from qdrant_client.http import models

import config
from tools.search_tool import SearchTool, SearchRequest, SearchResult, build_qdrant_filter
from agents.search_agent import SearchAgent
from prompts.system_prompt import get_system_prompt
from prompts.query_generation import get_query_generation_prompt


class TestConfigIntegration:
    """Verify config has dual collection variables."""

    def test_normative_collection_name(self):
        assert hasattr(config, 'NORMATIVE_COLLECTION_NAME')
        assert config.NORMATIVE_COLLECTION_NAME == "normative_documents"

    def test_operational_collection_name(self):
        assert hasattr(config, 'OPERATIONAL_COLLECTION_NAME')
        assert config.OPERATIONAL_COLLECTION_NAME == "operational_content"

    def test_chunks_dir(self):
        assert hasattr(config, 'CHUNKS_DIR')

    def test_collection_name_deprecated(self):
        assert hasattr(config, 'COLLECTION_NAME')
        assert config.COLLECTION_NAME == config.NORMATIVE_COLLECTION_NAME


class TestFilterPipeline:
    """Verify document_filters flow from Wiki Router to Qdrant Filter."""

    def test_full_filter_pipeline(self):
        """Wiki Router filters → build_qdrant_filter → Qdrant Filter."""
        # Simulate Wiki Router output
        document_filters = {
            "category": ["ТПП"],
            "client_type": ["ФЛ"],
            "power_range": ["<15kW"],
        }
        
        qf = build_qdrant_filter(document_filters)
        
        assert qf is not None
        assert len(qf.must) == 3
        
        # Verify each condition
        keys = [c.key for c in qf.must]
        assert "category" in keys
        assert "client_type" in keys
        assert "power_range" in keys

    def test_filter_with_any_values(self):
        """client_type and power_range always include 'any'."""
        document_filters = {
            "client_type": ["ФЛ"],
            "power_range": ["<15kW"],
        }
        
        qf = build_qdrant_filter(document_filters)
        
        for condition in qf.must:
            if condition.key == "client_type":
                assert "any" in condition.match.any
            if condition.key == "power_range":
                assert "any" in condition.match.any


class TestSearchResultCollectionField:
    """Verify SearchResult has collection_name field."""

    def test_search_result_with_collection(self):
        result = SearchResult(
            id="test-1",
            content="Test content about ТПП",
            summary="Test summary",
            category="ТПП",
            filename="test_file",
            breadcrumbs="Раздел 1 > Статья 2",
            score_hybrid=0.85,
            score_semantic=0.75,
            score_lexical=0.65,
            metadata={"document_type": "regulation"},
            collection_name="normative_documents",
        )
        assert result.collection_name == "normative_documents"

    def test_search_result_operational(self):
        result = SearchResult(
            id="test-2",
            content="FAQ content",
            summary="FAQ summary",
            category="ТПП",
            filename="faq",
            breadcrumbs="FAQ",
            score_hybrid=0.80,
            score_semantic=0.70,
            score_lexical=0.60,
            metadata={"document_type": "faq"},
            collection_name="operational_content",
        )
        assert result.collection_name == "operational_content"


class TestPromptsIntegration:
    """Verify prompts mention both collections."""

    def test_system_prompt_has_collections(self):
        prompt = get_system_prompt()
        assert "normative_documents" in prompt
        assert "operational_content" in prompt

    def test_query_generation_has_collection_hints(self):
        prompt = get_query_generation_prompt(
            user_query="Сколько стоит подключение?",
        )
        assert "prefer_collection" in prompt


class TestSearchToolCollections:
    """Verify SearchTool knows about both collections."""

    @patch('tools.search_tool.get_routerai_embedder')
    @patch('tools.search_tool.QdrantClient')
    def test_search_tool_has_two_collections(self, mock_qdrant, mock_embedder):
        tool = SearchTool()
        assert len(tool.collections) == 2
        assert config.NORMATIVE_COLLECTION_NAME in tool.collections
        assert config.OPERATIONAL_COLLECTION_NAME in tool.collections
