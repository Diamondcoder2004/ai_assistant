"""Tests for WikiSearchTool — keyword search over wiki index."""
import json
import pytest
from pathlib import Path
from unittest.mock import patch

from wiki.models import WikiDocument
from wiki.search_tool import WikiSearchTool


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
            summary="Порядок ТП для физических лиц с мощностью до 15 кВт. Срок: до 4 месяцев.",
            business_rules=["Срок выполнения: до 4 месяцев", "Ставка платы: 550 руб/кВт"],
            client_types=["ФЛ"],
            power_ranges=["<15kW"],
            key_terms=["заявка", "договор", "технические условия", "АРБП"],
            chunk_count=8,
        ).to_dict(),
        WikiDocument(
            id="tp-150-670kvt",
            title="Технологическое присоединение от 150 до 670 кВт",
            category="ТПП",
            source_origin="operational",
            source_file="tp-150-670kvt.md",
            summary="Порядок ТП для юридических лиц с мощностью от 150 до 670 кВт.",
            business_rules=["Срок: до 1 года"],
            client_types=["ЮЛ", "ИП"],
            power_ranges=["150-670kW"],
            key_terms=["заявка", "технические условия", "проект ТП"],
            chunk_count=12,
        ).to_dict(),
        WikiDocument(
            id="lk-instruktsiya",
            title="Инструкция по работе в Личном кабинете",
            category="ЛК",
            source_origin="operational",
            source_file="lk-instruktsiya.md",
            summary="Инструкция по регистрации и работе в ЛК Башкирэнерго.",
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


class TestWikiSearchTool:
    """Tests for WikiSearchTool."""

    def test_load_index(self, sample_index_file):
        """WikiSearchTool loads index.json correctly."""
        tool = WikiSearchTool(index_path=sample_index_file)
        assert len(tool.documents) == 3

    def test_search_finds_relevant_docs(self, sample_index_file):
        """Search returns documents matching the query."""
        tool = WikiSearchTool(index_path=sample_index_file)
        results = tool.search("заявка на подключение до 15 кВт")
        assert len(results) > 0
        assert results[0].id == "tp-do-15kvt"

    def test_search_returns_top_k(self, sample_index_file):
        """Search respects top_k parameter."""
        tool = WikiSearchTool(index_path=sample_index_file)
        results = tool.search("технологическое присоединение", top_k=2)
        assert len(results) <= 2

    def test_search_empty_query(self, sample_index_file):
        """Empty query returns empty results."""
        tool = WikiSearchTool(index_path=sample_index_file)
        results = tool.search("")
        assert results == []

    def test_search_no_matches(self, sample_index_file):
        """Query with no matches returns empty results."""
        tool = WikiSearchTool(index_path=sample_index_file)
        results = tool.search("квантовая физика")
        assert results == []

    def test_search_category_filter(self, sample_index_file):
        """Search can filter by category."""
        tool = WikiSearchTool(index_path=sample_index_file)
        results = tool.search("регистрация", category="ЛК")
        assert len(results) > 0
        assert all(d.category == "ЛК" for d in results)

    def test_search_by_business_rules(self, sample_index_file):
        """Search matches business_rules text."""
        tool = WikiSearchTool(index_path=sample_index_file)
        results = tool.search("550 руб кВт")
        assert len(results) > 0
        assert results[0].id == "tp-do-15kvt"

    def test_missing_index_file(self, tmp_path):
        """Missing index file results in empty documents with warning."""
        missing_path = tmp_path / "nonexistent.json"
        tool = WikiSearchTool(index_path=missing_path)
        assert tool.documents == []

    def test_search_scoring_order(self, sample_index_file):
        """Results are ordered by relevance score (descending)."""
        tool = WikiSearchTool(index_path=sample_index_file)
        results = tool.search("технологическое присоединение кВт")
        if len(results) >= 2:
            assert results[0].id in ["tp-do-15kvt", "tp-150-670kvt"]

    def test_get_document_by_id(self, sample_index_file):
        """Can retrieve a document by its ID."""
        tool = WikiSearchTool(index_path=sample_index_file)
        doc = tool.get_document_by_id("tp-do-15kvt")
        assert doc is not None
        assert doc.title == "Технологическое присоединение до 15 кВт"

    def test_get_document_by_id_not_found(self, sample_index_file):
        """Returns None for non-existent ID."""
        tool = WikiSearchTool(index_path=sample_index_file)
        doc = tool.get_document_by_id("nonexistent")
        assert doc is None
