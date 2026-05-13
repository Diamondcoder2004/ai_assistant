"""Tests for dual collection search tool."""
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from qdrant_client.http import models

from tools.search_tool import (
    SearchTool,
    SearchRequest,
    SearchResult,
    build_qdrant_filter,
)


class TestBuildQdrantFilter:
    """Tests for Qdrant filter builder."""

    def test_none_filters_returns_none(self):
        assert build_qdrant_filter(None) is None

    def test_empty_filters_returns_none(self):
        assert build_qdrant_filter({}) is None

    def test_category_filter(self):
        f = build_qdrant_filter({"category": ["ТПП"]})
        assert f is not None
        assert len(f.must) == 1
        assert f.must[0].key == "category"
        assert f.must[0].match.any == ["ТПП"]

    def test_client_type_adds_any(self):
        f = build_qdrant_filter({"client_type": ["ФЛ"]})
        assert f is not None
        assert len(f.must) == 1
        assert f.must[0].key == "client_type"
        assert "ФЛ" in f.must[0].match.any
        assert "any" in f.must[0].match.any

    def test_power_range_adds_any(self):
        f = build_qdrant_filter({"power_range": ["<15kW"]})
        assert f is not None
        assert f.must[0].key == "power_range"
        assert "<15kW" in f.must[0].match.any
        assert "any" in f.must[0].match.any

    def test_combined_filters(self):
        f = build_qdrant_filter({
            "category": ["ТПП"],
            "client_type": ["ФЛ"],
            "power_range": ["<15kW"],
        })
        assert f is not None
        assert len(f.must) == 3

    def test_client_type_already_has_any(self):
        f = build_qdrant_filter({"client_type": ["ФЛ", "any"]})
        assert f is not None
        # Should not duplicate "any"
        assert f.must[0].match.any.count("any") == 1

    def test_document_type_filter(self):
        f = build_qdrant_filter({"document_type": ["regulation"]})
        assert f is not None
        assert f.must[0].key == "document_type"
        assert f.must[0].match.any == ["regulation"]


class TestSearchResultCollectionName:
    """Tests for SearchResult with collection_name."""

    def test_search_result_has_collection_name(self):
        result = SearchResult(
            id="test-id",
            content="test content",
            summary="test summary",
            category="ТПП",
            filename="test_file",
            breadcrumbs="Раздел 1",
            score_hybrid=0.9,
            score_semantic=0.8,
            score_lexical=0.7,
            metadata={},
            collection_name="normative_documents",
        )
        assert result.collection_name == "normative_documents"

    def test_search_result_default_collection_name(self):
        result = SearchResult(
            id="test-id",
            content="test",
            summary="",
            category="",
            filename="",
            breadcrumbs="",
            score_hybrid=0.0,
            score_semantic=0.0,
            score_lexical=0.0,
            metadata={},
        )
        assert result.collection_name == ""


class TestSearchToolInit:
    """Tests for SearchTool initialization."""

    @patch('tools.search_tool.get_routerai_embedder')
    @patch('tools.search_tool.QdrantClient')
    def test_collections_initialized(self, mock_qdrant, mock_embedder):
        import config
        tool = SearchTool()
        assert config.NORMATIVE_COLLECTION_NAME in tool.collections
        assert config.OPERATIONAL_COLLECTION_NAME in tool.collections
        assert len(tool.collections) == 2
