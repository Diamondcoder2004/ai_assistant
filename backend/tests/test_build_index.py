"""Tests for build_index.py — wiki index builder."""
import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch

from wiki.build_index import WikiIndexBuilder


@pytest.fixture
def sample_chunks_dir(tmp_path):
    """Create a temporary directory with sample enriched chunks."""
    operational = tmp_path / "operational"
    operational.mkdir()
    normative = tmp_path / "normative"
    normative.mkdir()

    # Operational chunk 1
    (operational / "gid-po-tp_abc123_p1.json").write_text(
        json.dumps({
            "chunk_id": "abc123_p1",
            "source_file": "gid-po-tp.md",
            "chunk_content": "Гид по технологическому присоединению",
            "breadcrumbs": "Гид по ТП > Главная",
            "chunk_summary": "Обзор этапов ТП",
            "hypothetical_questions": ["Какие этапы ТП?"],
            "keywords": ["технологическое присоединение", "этапы"],
            "entities": ["Башкирэнерго"],
            "category": "ТПП",
            "source_origin": "operational",
            "document_source": "html_page",
        }, ensure_ascii=False),
        encoding="utf-8",
    )

    # Operational chunk 2 (same source_file)
    (operational / "gid-po-tp_abc123_p2.json").write_text(
        json.dumps({
            "chunk_id": "abc123_p2",
            "source_file": "gid-po-tp.md",
            "chunk_content": "Подача заявки на ТП",
            "breadcrumbs": "Гид по ТП > Шаг 1",
            "chunk_summary": "Порядок подачи заявки",
            "hypothetical_questions": ["Как подать заявку?"],
            "keywords": ["заявка", "подключение"],
            "entities": ["Башкирэнерго"],
            "category": "ТПП",
            "source_origin": "operational",
            "document_source": "html_page",
        }, ensure_ascii=False),
        encoding="utf-8",
    )

    # Normative chunk
    (normative / "fz-35_def456_p1.json").write_text(
        json.dumps({
            "chunk_id": "def456_p1",
            "source_file": "1. ФЗ 35 (28.04.2025).md",
            "chunk_content": "ФЗ об электроэнергетике",
            "breadcrumbs": "ФЗ 35 > Общие положения",
            "chunk_summary": "Общие положения закона об электроэнергетике",
            "hypothetical_questions": ["Что регулирует ФЗ 35?"],
            "keywords": ["электроэнергетика", "закон", "ФЗ 35"],
            "entities": ["ФЗ №35-ФЗ"],
            "category": "ТПП",
            "source_origin": "normative",
            "document_source": "pdf",
        }, ensure_ascii=False),
        encoding="utf-8",
    )

    return tmp_path


@pytest.fixture
def sample_url_mapping(tmp_path):
    """Create a minimal URL mapping file."""
    mapping_file = tmp_path / "url_mapping.json"
    mapping_file.write_text(
        json.dumps({
            "gid-po-tp.md": "https://www.bashkirenergo.ru/consumers/gid-po-tekhnologicheskomu-prisoedineniyu/",
        }, ensure_ascii=False),
        encoding="utf-8",
    )
    return mapping_file


class TestWikiIndexBuilder:
    """Tests for WikiIndexBuilder."""

    def test_load_chunks_groups_by_source(self, sample_chunks_dir):
        """Chunks are grouped by source_file."""
        builder = WikiIndexBuilder(chunks_dir=sample_chunks_dir)
        groups = builder._load_and_group_chunks()
        # Two source files: gid-po-tp.md and 1. ФЗ 35 (28.04.2025).md
        assert len(groups) == 2
        # gid-po-tp.md has 2 chunks
        assert any("gid-po-tp" in k for k in groups)
        gid_key = [k for k in groups if "gid-po-tp" in k][0]
        assert len(groups[gid_key]) == 2

    def test_build_creates_documents(self, sample_chunks_dir, sample_url_mapping):
        """build() produces WikiDocument entries."""
        builder = WikiIndexBuilder(
            chunks_dir=sample_chunks_dir,
            url_mapping_path=sample_url_mapping,
        )
        index = builder.build()
        assert "version" in index
        assert "documents" in index
        assert len(index["documents"]) == 2

    def test_build_document_has_required_fields(self, sample_chunks_dir, sample_url_mapping):
        """Each document in the index has all required fields."""
        builder = WikiIndexBuilder(
            chunks_dir=sample_chunks_dir,
            url_mapping_path=sample_url_mapping,
        )
        index = builder.build()
        for doc in index["documents"]:
            assert "id" in doc
            assert "title" in doc
            assert "category" in doc
            assert "source_origin" in doc
            assert "source_file" in doc
            assert "summary" in doc
            assert "key_terms" in doc
            assert "chunk_count" in doc

    def test_build_aggregates_keywords(self, sample_chunks_dir, sample_url_mapping):
        """Keywords from multiple chunks are deduplicated and aggregated."""
        builder = WikiIndexBuilder(
            chunks_dir=sample_chunks_dir,
            url_mapping_path=sample_url_mapping,
        )
        index = builder.build()
        gid_doc = [d for d in index["documents"] if "gid-po-tp" in d["source_file"]][0]
        # Should contain keywords from both chunks
        assert "технологическое присоединение" in gid_doc["key_terms"]
        assert "заявка" in gid_doc["key_terms"]

    def test_build_counts_chunks(self, sample_chunks_dir, sample_url_mapping):
        """chunk_count reflects the number of chunks per document."""
        builder = WikiIndexBuilder(
            chunks_dir=sample_chunks_dir,
            url_mapping_path=sample_url_mapping,
        )
        index = builder.build()
        gid_doc = [d for d in index["documents"] if "gid-po-tp" in d["source_file"]][0]
        assert gid_doc["chunk_count"] == 2

    def test_save_and_load_index(self, sample_chunks_dir, sample_url_mapping, tmp_path):
        """Index can be saved to JSON and loaded back."""
        builder = WikiIndexBuilder(
            chunks_dir=sample_chunks_dir,
            url_mapping_path=sample_url_mapping,
        )
        index = builder.build()
        output_path = tmp_path / "index.json"
        builder.save(index, output_path)

        # Load and verify
        with open(output_path, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        assert loaded["version"] == index["version"]
        assert len(loaded["documents"]) == len(index["documents"])

    def test_empty_chunks_dir(self, tmp_path, sample_url_mapping):
        """Empty chunks directory produces empty documents list."""
        empty_dir = tmp_path / "empty_chunks"
        empty_dir.mkdir()
        (empty_dir / "normative").mkdir()
        (empty_dir / "operational").mkdir()

        builder = WikiIndexBuilder(
            chunks_dir=empty_dir,
            url_mapping_path=sample_url_mapping,
        )
        index = builder.build()
        assert index["documents"] == []

    def test_url_mapping_applied(self, sample_chunks_dir, sample_url_mapping):
        """URL mapping is applied to documents."""
        builder = WikiIndexBuilder(
            chunks_dir=sample_chunks_dir,
            url_mapping_path=sample_url_mapping,
        )
        index = builder.build()
        gid_doc = [d for d in index["documents"] if "gid-po-tp" in d["source_file"]][0]
        assert gid_doc["url"] == "https://www.bashkirenergo.ru/consumers/gid-po-tekhnologicheskomu-prisoedineniyu/"
