"""Tests for WikiRouterAgent — JSON-based agentic knowledge router."""
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from wiki.models import WikiDocument, WikiRoutingResult
from wiki.search_tool import WikiSearchTool
from wiki.wiki_router import WikiRouterAgent


@pytest.fixture
def sample_index_file(tmp_path):
    """Create a sample index.json for testing."""
    docs = [
        WikiDocument(
            id="tp-do-15kvt",
            title="Технологическое присоединение до 15 кВт",
            category="ТПП",
            source_origin="operational",
            source_file="tp-do-15kvt.md",
            summary="Порядок ТП для физических лиц с мощностью до 15 кВт",
            business_rules=["Срок выполнения: до 4 месяцев", "Ставка платы: 550 руб/кВт"],
            client_types=["ФЛ"],
            power_ranges=["<15kW"],
            key_terms=["заявка", "договор", "технические условия", "АРБП"],
            chunk_count=8,
        ).to_dict(),
        WikiDocument(
            id="lk-instruktsiya",
            title="Инструкция по работе в Личном кабинете",
            category="ЛК",
            source_origin="operational",
            source_file="lk-instruktsiya.md",
            summary="Инструкция по регистрации и работе в ЛК",
            key_terms=["личный кабинет", "регистрация", "авторизация"],
            chunk_count=5,
        ).to_dict(),
    ]

    index_data = {
        "version": "1.0",
        "generated_at": "2026-05-05T12:00:00Z",
        "documents": docs,
    }

    index_file = tmp_path / "index.json"
    with open(index_file, "w", encoding="utf-8") as f:
        json.dump(index_data, f, ensure_ascii=False)

    return index_file


class TestWikiRouterAgent:
    """Tests for WikiRouterAgent."""

    def test_init_loads_search_tool(self, sample_index_file):
        """WikiRouterAgent initializes with WikiSearchTool."""
        agent = WikiRouterAgent(index_path=str(sample_index_file))
        assert agent.search_tool is not None
        assert len(agent.search_tool.documents) == 2

    def test_route_returns_routing_result(self, sample_index_file):
        """route() returns WikiRoutingResult."""
        agent = WikiRouterAgent(index_path=str(sample_index_file))
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "selected_docs": ["tp-do-15kvt"],
            "business_rules": ["Срок выполнения: до 4 месяцев"],
            "filters": {"client_type": ["ФЛ"], "power_range": ["<15kW"], "category": ["ТПП"]},
            "key_terms": ["заявка", "ТП", "15 кВт"],
            "confidence": 0.9,
        })

        with patch.object(agent.client.chat.completions, 'create', return_value=mock_response):
            result = agent.route("как подать заявку на подключение 15 кВт")

        assert isinstance(result, WikiRoutingResult)
        assert result.confidence > 0

    def test_route_empty_query(self, sample_index_file):
        """Empty query returns empty result with confidence 0."""
        agent = WikiRouterAgent(index_path=str(sample_index_file))
        result = agent.route("")
        assert result.confidence == 0.0
        assert result.concepts == []

    def test_route_no_candidates(self, sample_index_file):
        """Query with no keyword matches returns empty result."""
        agent = WikiRouterAgent(index_path=str(sample_index_file))
        result = agent.route("квантовая физика термоядерный синтез")
        assert result.confidence == 0.0

    def test_route_llm_failure_fallback(self, sample_index_file):
        """LLM failure falls back to keyword-search candidates."""
        agent = WikiRouterAgent(index_path=str(sample_index_file))

        with patch.object(agent.client.chat.completions, 'create', side_effect=Exception("LLM error")):
            result = agent.route("заявка на подключение")

        assert isinstance(result, WikiRoutingResult)
        assert result.confidence < 0.5

    def test_route_llm_invalid_json_retry(self, sample_index_file):
        """Invalid JSON from LLM triggers retry, then fallback."""
        agent = WikiRouterAgent(index_path=str(sample_index_file))

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "not valid json {{{"

        with patch.object(agent.client.chat.completions, 'create', return_value=mock_response):
            result = agent.route("подключение к электросетям")

        assert isinstance(result, WikiRoutingResult)

    def test_route_with_fallback(self, sample_index_file):
        """route_with_fallback works even when route returns empty."""
        agent = WikiRouterAgent(index_path=str(sample_index_file))

        empty_result = WikiRoutingResult(
            concepts=[], wiki_context="", search_hints=[],
            combined_keywords=[], document_filters={},
            matched_categories=[], confidence=0.0,
        )
        with patch.object(agent, 'route', return_value=empty_result):
            result = agent.route_with_fallback("как подать заявку")

        assert isinstance(result, WikiRoutingResult)

    def test_format_candidates_for_llm(self, sample_index_file):
        """_format_candidates produces valid LLM prompt text."""
        agent = WikiRouterAgent(index_path=str(sample_index_file))
        doc = agent.search_tool.documents[0]
        formatted = agent._format_candidates([doc])
        assert doc.title in formatted
        assert doc.category in formatted
        assert "заявка" in formatted

    def test_missing_index_graceful(self, tmp_path):
        """Missing index file results in graceful empty results."""
        missing_path = tmp_path / "nonexistent.json"
        agent = WikiRouterAgent(index_path=str(missing_path))
        result = agent.route("как подать заявку")
        assert result.confidence == 0.0
        assert result.concepts == []
