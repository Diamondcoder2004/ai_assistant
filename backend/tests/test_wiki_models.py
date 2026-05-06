"""Tests for wiki data models."""
import pytest
from wiki.models import WikiDocument, WikiRoutingResult


class TestWikiDocument:
    """Tests for WikiDocument dataclass."""

    def test_create_wiki_document_minimal(self):
        """Create WikiDocument with only required fields."""
        doc = WikiDocument(
            id="tp-do-15kvt",
            title="Технологическое присоединение до 15 кВт",
            category="ТПП",
            source_origin="operational",
            source_file="tp-do-15kvt.md",
            summary="Порядок ТП для физических лиц с мощностью до 15 кВт",
            key_terms=["заявка", "договор", "технические условия"],
            chunk_count=8,
        )
        assert doc.id == "tp-do-15kvt"
        assert doc.category == "ТПП"
        assert doc.business_rules == []
        assert doc.client_types == []
        assert doc.power_ranges == []
        assert doc.url == ""
        assert doc.related_files == []

    def test_create_wiki_document_full(self):
        """Create WikiDocument with all fields."""
        doc = WikiDocument(
            id="tp-do-15kvt",
            title="Технологическое присоединение до 15 кВт",
            category="ТПП",
            source_origin="operational",
            source_file="tp-do-15kvt.md",
            url="https://www.bashkirenergo.ru/consumers/gid-po-tekhnologicheskomu-prisoedineniyu/15kvt/",
            summary="Порядок ТП для физических лиц с мощностью до 15 кВт",
            business_rules=["Срок выполнения: до 4 месяцев", "Ставка платы: 550 руб/кВт"],
            client_types=["ФЛ"],
            power_ranges=["<15kW"],
            key_terms=["заявка", "договор", "технические условия", "АРБП"],
            related_files=["1-shag-podacha-zayavki.md", "passport-tp-do-15kvt.md"],
            chunk_count=8,
        )
        assert doc.business_rules == ["Срок выполнения: до 4 месяцев", "Ставка платы: 550 руб/кВт"]
        assert doc.client_types == ["ФЛ"]
        assert doc.power_ranges == ["<15kW"]

    def test_wiki_document_to_dict(self):
        """WikiDocument serializes to dict correctly."""
        doc = WikiDocument(
            id="test-id",
            title="Test Title",
            category="ЛК",
            source_origin="operational",
            source_file="test.md",
            summary="Test summary",
            key_terms=["term1"],
            chunk_count=3,
        )
        d = doc.to_dict()
        assert d["id"] == "test-id"
        assert d["category"] == "ЛК"
        assert d["business_rules"] == []
        assert d["client_types"] == []

    def test_wiki_document_from_dict(self):
        """WikiDocument deserializes from dict correctly."""
        data = {
            "id": "test-id",
            "title": "Test Title",
            "category": "ДУ",
            "source_origin": "normative",
            "source_file": "test.md",
            "url": "https://example.com",
            "summary": "Test summary",
            "business_rules": ["Rule 1"],
            "client_types": ["ЮЛ"],
            "power_ranges": ["15-150kW"],
            "key_terms": ["term1", "term2"],
            "related_files": ["other.md"],
            "chunk_count": 5,
        }
        doc = WikiDocument.from_dict(data)
        assert doc.id == "test-id"
        assert doc.business_rules == ["Rule 1"]
        assert doc.url == "https://example.com"

    def test_wiki_document_from_dict_missing_optional(self):
        """WikiDocument deserializes with missing optional fields using defaults."""
        data = {
            "id": "minimal",
            "title": "Minimal",
            "category": "ТПП",
            "source_origin": "operational",
            "source_file": "min.md",
            "summary": "Min summary",
            "key_terms": [],
            "chunk_count": 1,
        }
        doc = WikiDocument.from_dict(data)
        assert doc.url == ""
        assert doc.business_rules == []
        assert doc.client_types == []
        assert doc.power_ranges == []
        assert doc.related_files == []

    def test_wiki_document_searchable_text(self):
        """WikiDocument produces searchable text for keyword matching."""
        doc = WikiDocument(
            id="tp-do-15kvt",
            title="Технологическое присоединение до 15 кВт",
            category="ТПП",
            source_origin="operational",
            source_file="tp-do-15kvt.md",
            summary="Порядок ТП для физических лиц",
            business_rules=["Срок: 4 месяца"],
            key_terms=["заявка", "договор"],
            chunk_count=5,
        )
        text = doc.searchable_text()
        assert "технологическое присоединение" in text
        assert "заявка" in text
        assert "договор" in text
        assert "порядок тп" in text
        assert "срок" in text


class TestWikiRoutingResult:
    """Tests for WikiRoutingResult dataclass."""

    def test_empty_routing_result(self):
        """Create empty WikiRoutingResult."""
        result = WikiRoutingResult(
            concepts=[],
            wiki_context="",
            search_hints=[],
            combined_keywords=[],
            document_filters={},
            matched_categories=[],
            confidence=0.0,
        )
        assert result.concepts == []
        assert result.wiki_context == ""
        assert result.confidence == 0.0

    def test_routing_result_with_data(self):
        """Create WikiRoutingResult with populated fields."""
        doc = WikiDocument(
            id="tp-do-15kvt",
            title="ТП до 15 кВт",
            category="ТПП",
            source_origin="operational",
            source_file="tp-do-15kvt.md",
            summary="Порядок ТП для ФЛ",
            key_terms=["заявка"],
            chunk_count=5,
        )
        result = WikiRoutingResult(
            concepts=[doc],
            wiki_context="Контекст Wiki",
            search_hints=["искать: заявка на ТП"],
            combined_keywords=["заявка", "ТП"],
            document_filters={"client_type": ["ФЛ"], "power_range": ["<15kW"], "category": ["ТПП"]},
            matched_categories=["ТПП"],
            confidence=0.9,
        )
        assert len(result.concepts) == 1
        assert result.confidence == 0.9
        assert "ФЛ" in result.document_filters["client_type"]
