# Wiki Router Rework — Implementation Plan

**Goal:** Replace Supabase-dependent WikiRouter with a JSON-based agentic knowledge layer that loads from `index.json`, does fast keyword candidate search, and calls `inception/mercury-2` for LLM routing decisions.

**Architecture:** Two-stage pipeline: (1) `build_index.py` aggregates enriched chunks into per-document entries in `index.json`; (2) at runtime, `WikiSearchTool` loads the index into memory, `WikiRouterAgent` uses keyword search + LLM to produce `WikiRoutingResult` for downstream agents (QueryGenerator, SearchAgent, ResponseAgent).

**Design:** [thoughts/shared/designs/2026-05-05-wiki-router-rework-design.md](../designs/2026-05-05-wiki-router-rework-design.md)

---

## Dependency Graph

```
Batch 1 (parallel): 1.1, 1.2, 1.3 [foundation — no deps]
Batch 2 (parallel): 2.1, 2.2, 2.3 [core — depends on batch 1]
Batch 3 (parallel): 3.1, 3.2, 3.3 [integration — depends on batch 2]
Batch 4 (sequential): 4.1 [cleanup — depends on batch 3]
```

---

## Batch 1: Foundation (parallel — 3 implementers)

All tasks in this batch have NO dependencies and run simultaneously.

### Task 1.1: Wiki Data Models (`backend/wiki/models.py`)

**File:** `backend/wiki/models.py`
**Test:** `backend/tests/test_wiki_models.py`
**Depends:** none

Design requires `WikiDocument` and `WikiRoutingResult` dataclasses. I'm putting them in a dedicated `models.py` instead of inside `wiki_router.py` to keep concerns separated and allow `search_tool.py` to import `WikiDocument` without circular dependencies.

```python
# backend/tests/test_wiki_models.py
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
```

```python
# backend/wiki/models.py
"""
Wiki data models — WikiDocument and WikiRoutingResult.

These are the core data structures for the JSON-based wiki knowledge layer.
WikiDocument represents a per-document entry in the index.
WikiRoutingResult is the output of WikiRouterAgent, consumed by downstream agents.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class WikiDocument:
    """
    A single document entry in the wiki index.

    Aggregated from enriched_chunks per source_file.
    Contains metadata, business rules, and search-relevant fields.
    """

    id: str
    title: str
    category: str  # ЛК / ДУ / ТПП
    source_origin: str  # normative / operational
    source_file: str
    summary: str
    key_terms: List[str] = field(default_factory=list)
    chunk_count: int = 0
    url: str = ""
    business_rules: List[str] = field(default_factory=list)
    client_types: List[str] = field(default_factory=list)
    power_ranges: List[str] = field(default_factory=list)
    related_files: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, object]:
        """Serialize to dict for JSON storage."""
        return {
            "id": self.id,
            "title": self.title,
            "category": self.category,
            "source_origin": self.source_origin,
            "source_file": self.source_file,
            "summary": self.summary,
            "key_terms": self.key_terms,
            "chunk_count": self.chunk_count,
            "url": self.url,
            "business_rules": self.business_rules,
            "client_types": self.client_types,
            "power_ranges": self.power_ranges,
            "related_files": self.related_files,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "WikiDocument":
        """Deserialize from dict (e.g., loaded from JSON)."""
        return cls(
            id=data["id"],
            title=data["title"],
            category=data["category"],
            source_origin=data["source_origin"],
            source_file=data["source_file"],
            summary=data["summary"],
            key_terms=data.get("key_terms", []),
            chunk_count=data.get("chunk_count", 0),
            url=data.get("url", ""),
            business_rules=data.get("business_rules", []),
            client_types=data.get("client_types", []),
            power_ranges=data.get("power_ranges", []),
            related_files=data.get("related_files", []),
        )

    def searchable_text(self) -> str:
        """
        Produce a single lowercase string for keyword matching.

        Concatenates title, summary, key_terms, business_rules, and category
        into one searchable blob. Used by WikiSearchTool for fast candidate scoring.
        """
        parts = [
            self.title,
            self.summary,
            " ".join(self.key_terms),
            " ".join(self.business_rules),
            self.category,
        ]
        return " ".join(parts).lower()


@dataclass
class WikiRoutingResult:
    """
    Result of WikiRouterAgent routing.

    Passed to QueryGenerator (key_terms, wiki_context),
    SearchAgent (document_filters, search_hints),
    and ResponseAgent (wiki_context, business_rules).
    """

    concepts: List[WikiDocument]  # Selected relevant documents
    wiki_context: str  # Formatted context string for agents
    search_hints: List[str]  # Hints for SearchAgent
    combined_keywords: List[str]  # Keywords for QueryGenerator
    document_filters: Dict[str, List[str]]  # Qdrant filters
    matched_categories: List[str]  # Matched categories (ЛК/ДУ/ТПП)
    confidence: float  # Routing confidence (0-1)
```

**Verify:** `cd backend && python -m pytest tests/test_wiki_models.py -v`
**Commit:** `feat(wiki): add WikiDocument and WikiRoutingResult data models`

---

### Task 1.2: Config Update (`backend/config.py`)

**File:** `backend/config.py`
**Test:** `backend/tests/test_wiki_config.py`
**Depends:** none

Design requires removing Supabase wiki vars and adding `WIKI_INDEX_PATH`. I'm also removing `WIKI_TABLE_NAME` and `WIKI_TOP_K_CONCEPTS` since they're Supabase-specific. The `ENABLE_WIKI_ROUTER` flag stays but defaults to `true` now (the new system works without Supabase).

```python
# backend/tests/test_wiki_config.py
"""Tests for wiki-related config values."""
import pytest
from pathlib import Path
import config


class TestWikiConfig:
    """Tests for wiki configuration."""

    def test_wiki_index_path_default(self):
        """WIKI_INDEX_PATH has a sensible default."""
        # Default should point to wiki/data/index.json relative to backend dir
        expected = config.BASE_DIR / "wiki" / "data" / "index.json"
        assert config.WIKI_INDEX_PATH == expected

    def test_wiki_index_path_is_path(self):
        """WIKI_INDEX_PATH is a Path object."""
        assert isinstance(config.WIKI_INDEX_PATH, Path)

    def test_enable_wiki_router_default(self):
        """ENABLE_WIKI_ROUTER defaults to true."""
        # The new system works without Supabase, so default is True
        assert isinstance(config.ENABLE_WIKI_ROUTER, bool)

    def test_wiki_router_model_default(self):
        """WIKI_ROUTER_MODEL defaults to inception/mercury-2."""
        assert config.WIKI_ROUTER_MODEL == "inception/mercury-2"

    def test_wiki_top_k_default(self):
        """WIKI_TOP_K defaults to 3."""
        assert config.WIKI_TOP_K == 3

    def test_wiki_search_top_k_default(self):
        """WIKI_SEARCH_TOP_K defaults to 5 (candidates before LLM refinement)."""
        assert config.WIKI_SEARCH_TOP_K == 5

    def test_no_supabase_wiki_vars(self):
        """Supabase wiki vars (WIKI_TABLE_NAME) should not exist in config."""
        assert not hasattr(config, "WIKI_TABLE_NAME")
```

```python
# Changes to backend/config.py — replace the LLM WIKI section

# OLD (lines 84-89):
# ENABLE_WIKI_ROUTER = os.getenv("ENABLE_WIKI_ROUTER", "false").lower() == "true"
# WIKI_TABLE_NAME = os.getenv("WIKI_TABLE_NAME", "wiki_concepts")
# WIKI_TOP_K_CONCEPTS = int(os.getenv("WIKI_TOP_K_CONCEPTS", "3"))

# NEW:
# =============================================================================
# WIKI ROUTER (JSON-based Agentic Knowledge Layer)
# =============================================================================

ENABLE_WIKI_ROUTER = os.getenv("ENABLE_WIKI_ROUTER", "true").lower() == "true"
WIKI_INDEX_PATH = Path(os.getenv("WIKI_INDEX_PATH", str(BASE_DIR / "wiki" / "data" / "index.json")))
WIKI_ROUTER_MODEL = os.getenv("WIKI_ROUTER_MODEL", "inception/mercury-2")
WIKI_TOP_K = int(os.getenv("WIKI_TOP_K", "3"))  # LLM-selected documents
WIKI_SEARCH_TOP_K = int(os.getenv("WIKI_SEARCH_TOP_K", "5"))  # Keyword candidates before LLM
```

**Verify:** `cd backend && python -m pytest tests/test_wiki_config.py -v`
**Commit:** `feat(config): replace Supabase wiki vars with JSON-based config`

---

### Task 1.3: Build Index Script (`backend/wiki/build_index.py`)

**File:** `backend/wiki/build_index.py`
**Test:** `backend/tests/test_build_index.py`
**Depends:** 1.1 (imports WikiDocument)

This is the one-time script that reads enriched chunks and produces `index.json`. It groups chunks by `source_file`, aggregates metadata, and writes the index.

```python
# backend/tests/test_build_index.py
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
```

```python
# backend/wiki/build_index.py
"""
Wiki Index Builder — one-time script to build index.json from enriched chunks.

Reads enriched_chunks/{normative,operational}/*.json, groups by source_file,
aggregates metadata (keywords, summaries, entities), and produces index.json
for WikiSearchTool to load at runtime.

Usage:
    python -m wiki.build_index
    # or:
    python backend/wiki/build_index.py
"""

import json
import logging
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional

from wiki.models import WikiDocument

logger = logging.getLogger(__name__)

# Default paths relative to backend/
DEFAULT_CHUNKS_DIR = Path(__file__).parent.parent / "chunking" / "enriched_chunks"
DEFAULT_URL_MAPPING_PATH = Path(__file__).parent / "data" / "url_mapping.json"
DEFAULT_OUTPUT_PATH = Path(__file__).parent / "data" / "index.json"

INDEX_VERSION = "1.0"


class WikiIndexBuilder:
    """
    Builds wiki index from enriched chunks.

    Groups chunks by source_file, aggregates metadata,
    and produces a JSON index for runtime use.
    """

    def __init__(
        self,
        chunks_dir: Path = DEFAULT_CHUNKS_DIR,
        url_mapping_path: Optional[Path] = DEFAULT_URL_MAPPING_PATH,
        output_path: Path = DEFAULT_OUTPUT_PATH,
    ):
        self.chunks_dir = chunks_dir
        self.url_mapping_path = url_mapping_path
        self.output_path = output_path
        self._url_mapping: Dict[str, str] = {}
        self._load_url_mapping()

    def _load_url_mapping(self):
        """Load URL mapping from JSON file (optional)."""
        if self.url_mapping_path and self.url_mapping_path.exists():
            try:
                with open(self.url_mapping_path, "r", encoding="utf-8") as f:
                    self._url_mapping = json.load(f)
                logger.info(f"Loaded URL mapping: {len(self._url_mapping)} entries")
            except (json.JSONDecodeError, OSError) as e:
                logger.warning(f"Failed to load URL mapping: {e}")
                self._url_mapping = {}

    def _load_and_group_chunks(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Load all enriched chunk JSON files and group by source_file.

        Returns:
            {source_file: [chunk_dict, ...]}
        """
        groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

        for origin in ["normative", "operational"]:
            origin_dir = self.chunks_dir / origin
            if not origin_dir.exists():
                logger.warning(f"Chunks directory not found: {origin_dir}")
                continue

            for json_file in origin_dir.glob("*.json"):
                try:
                    with open(json_file, "r", encoding="utf-8") as f:
                        chunk = json.load(f)
                    source_file = chunk.get("source_file", json_file.name)
                    groups[source_file].append(chunk)
                except (json.JSONDecodeError, KeyError) as e:
                    logger.warning(f"Failed to read {json_file}: {e}")

        logger.info(f"Loaded {sum(len(v) for v in groups.values())} chunks "
                     f"from {len(groups)} source files")
        return dict(groups)

    def _generate_id(self, source_file: str) -> str:
        """
        Generate a machine-friendly ID from source_file.

        Converts filename to a slug: lowercase, hyphens, no extension.
        """
        # Remove extension
        name = Path(source_file).stem
        # Transliterate common Cyrillic patterns isn't needed —
        # we use the original name slugified
        # Replace spaces and special chars with hyphens
        slug = re.sub(r'[^\w\s-]', '', name.lower())
        slug = re.sub(r'[\s_]+', '-', slug)
        slug = slug.strip('-')
        return slug if slug else f"doc-{hash(source_file) % 10000}"

    def _aggregate_document(
        self, source_file: str, chunks: List[Dict[str, Any]]
    ) -> WikiDocument:
        """
        Aggregate multiple chunks of a single source file into one WikiDocument.

        Merges keywords, entities, hypothetical questions, and summaries.
        """
        # Take category and source_origin from first chunk (should be consistent)
        first = chunks[0]
        category = first.get("category", "ТПП")
        source_origin = first.get("source_origin", "operational")

        # Aggregate keywords (deduplicated)
        all_keywords = []
        seen_keywords = set()
        for chunk in chunks:
            for kw in chunk.get("keywords", []):
                kw_lower = kw.lower()
                if kw_lower not in seen_keywords:
                    seen_keywords.add(kw_lower)
                    all_keywords.append(kw)

        # Aggregate entities (deduplicated)
        all_entities = []
        seen_entities = set()
        for chunk in chunks:
            for ent in chunk.get("entities", []):
                if ent not in seen_entities:
                    seen_entities.add(ent)
                    all_entities.append(ent)

        # Combine summaries (take first summary + first hypothetical questions)
        summaries = []
        for chunk in chunks:
            s = chunk.get("chunk_summary", "").strip()
            if s:
                summaries.append(s)
        combined_summary = summaries[0] if summaries else f"Документ: {source_file}"
        # If multiple summaries, combine top 2
        if len(summaries) > 1:
            combined_summary = f"{summaries[0]} {summaries[1]}"

        # Title from breadcrumbs or source_file
        breadcrumbs = chunks[0].get("breadcrumbs", "")
        if breadcrumbs:
            # Take the last segment of breadcrumbs as title
            title = breadcrumbs.split(" > ")[-1] if " > " in breadcrumbs else breadcrumbs
        else:
            title = Path(source_file).stem

        # URL from mapping
        url = self._url_mapping.get(source_file, "")

        # Extract business rules from hypothetical questions (heuristic)
        # We don't have explicit business_rules in chunks, so we use
        # hypothetical_questions as a proxy for search terms
        # business_rules will be populated by the LLM in a future enhancement
        # For now, we leave it empty — the LLM router will extract rules at query time

        # Determine client_types and power_ranges from keywords/entities
        client_types = []
        power_ranges = []
        all_text = " ".join(all_keywords + all_entities).lower()
        if "фл" in all_text or "физическ" in all_text:
            client_types.append("ФЛ")
        if "ип" in all_text or "индивидуальн" in all_text:
            client_types.append("ИП")
        if "юл" in all_text or "юридическ" in all_text:
            client_types.append("ЮЛ")
        if "15 кв" in all_text or "до 15" in all_text or "<15kw" in all_text:
            power_ranges.append("<15kW")
        if "150 кв" in all_text or "15-150" in all_text:
            power_ranges.append("15-150kW")
        if "670 кв" in all_text or "150-670" in all_text:
            power_ranges.append("150-670kW")
        if "свыше 670" in all_text or ">670kw" in all_text:
            power_ranges.append(">670kW")
        if not client_types:
            client_types = ["any"]
        if not power_ranges:
            power_ranges = ["any"]

        return WikiDocument(
            id=self._generate_id(source_file),
            title=title,
            category=category,
            source_origin=source_origin,
            source_file=source_file,
            url=url,
            summary=combined_summary,
            business_rules=[],  # Populated by LLM at query time
            client_types=client_types,
            power_ranges=power_ranges,
            key_terms=all_keywords[:15],  # Cap at 15 terms
            related_files=[],  # Could be populated from chunk metadata
            chunk_count=len(chunks),
        )

    def build(self) -> Dict[str, Any]:
        """
        Build the complete wiki index from enriched chunks.

        Returns:
            Dict with 'version', 'generated_at', and 'documents' keys.
        """
        groups = self._load_and_group_chunks()

        documents = []
        for source_file, chunks in groups.items():
            doc = self._aggregate_document(source_file, chunks)
            documents.append(doc.to_dict())

        # Sort by category then title for deterministic output
        documents.sort(key=lambda d: (d["category"], d["title"]))

        index = {
            "version": INDEX_VERSION,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "documents": documents,
        }

        logger.info(f"Built index with {len(documents)} documents")
        return index

    def save(self, index: Dict[str, Any], output_path: Optional[Path] = None):
        """Save index to JSON file."""
        path = output_path or self.output_path
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(index, f, ensure_ascii=False, indent=2)

        logger.info(f"Index saved to {path} ({len(index['documents'])} documents)")


# CLI entry point
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    )

    print("=== Wiki Index Builder ===")
    print(f"Chunks dir: {DEFAULT_CHUNKS_DIR}")
    print(f"Output: {DEFAULT_OUTPUT_PATH}")

    builder = WikiIndexBuilder()
    index = builder.build()
    builder.save(index)

    print(f"\nDone! {len(index['documents'])} documents indexed.")
    print(f"Output: {DEFAULT_OUTPUT_PATH}")
```

**Verify:** `cd backend && python -m pytest tests/test_build_index.py -v`
**Commit:** `feat(wiki): add build_index.py for JSON index generation`

---

## Batch 2: Core Modules (parallel — 3 implementers)

All tasks in this batch depend on Batch 1 completing.

### Task 2.1: Wiki Search Tool (`backend/wiki/search_tool.py`)

**File:** `backend/wiki/search_tool.py`
**Test:** `backend/tests/test_wiki_search_tool.py`
**Depends:** 1.1 (imports WikiDocument)

Design specifies keyword intersection scoring against `title`, `summary`, `key_terms`, `business_rules`. I'm implementing this as a pure in-memory search with no LLM calls — fast (microseconds).

```python
# backend/tests/test_wiki_search_tool.py
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
        # Should find tp-do-15kvt as top result
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
        # More specific match should score higher
        if len(results) >= 2:
            # tp-do-15kvt has "до 15 кВт" in title + "кВт" in business_rules
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
```

```python
# backend/wiki/search_tool.py
"""
WikiSearchTool — fast keyword search over the wiki index.

Loads index.json into memory at init and provides keyword intersection
scoring for candidate selection. No LLM calls — microseconds per query.
"""

import json
import logging
import re
from pathlib import Path
from typing import List, Optional

from wiki.models import WikiDocument

logger = logging.getLogger(__name__)


class WikiSearchTool:
    """
    In-memory keyword search over wiki document index.

    Uses keyword intersection scoring: query words matched against
    title, summary, key_terms, business_rules, and category.
    """

    def __init__(self, index_path: Optional[Path] = None):
        """
        Initialize and load the index.

        Args:
            index_path: Path to index.json. If None, uses config default.
                        If file doesn't exist, logs warning and starts empty.
        """
        if index_path is None:
            import config
            index_path = config.WIKI_INDEX_PATH

        self.index_path = Path(index_path)
        self.documents: List[WikiDocument] = []
        self._load_index()

    def _load_index(self):
        """Load index.json into memory."""
        if not self.index_path.exists():
            logger.warning(
                f"Wiki index not found at {self.index_path}. "
                f"Wiki routing will return empty results. "
                f"Run 'python -m wiki.build_index' to generate the index."
            )
            return

        try:
            with open(self.index_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.documents = [
                WikiDocument.from_dict(doc_data)
                for doc_data in data.get("documents", [])
            ]
            logger.info(f"Loaded {len(self.documents)} wiki documents from {self.index_path}")

        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.error(f"Failed to load wiki index: {e}")
            self.documents = []

    def _tokenize(self, text: str) -> set:
        """
        Tokenize text into lowercase word set for matching.

        Splits on whitespace and punctuation, removes short tokens (< 2 chars).
        """
        # Split on non-word chars, keep Cyrillic and Latin
        words = re.findall(r'[a-zA-Zа-яА-ЯёЁ0-9]+', text.lower())
        return {w for w in words if len(w) >= 2}

    def search(
        self,
        query: str,
        top_k: int = 5,
        category: Optional[str] = None,
    ) -> List[WikiDocument]:
        """
        Search wiki documents by keyword intersection scoring.

        Args:
            query: User query text
            top_k: Maximum number of results
            category: Optional category filter (ЛК/ДУ/ТПП)

        Returns:
            List of WikiDocument sorted by relevance (descending)
        """
        if not query or not self.documents:
            return []

        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []

        scored = []
        for doc in self.documents:
            # Apply category filter
            if category and doc.category != category:
                continue

            # Build searchable text and tokenize
            doc_tokens = self._tokenize(doc.searchable_text())

            # Score = number of matching tokens / total query tokens
            # This gives higher scores to documents matching more query terms
            matches = query_tokens & doc_tokens
            if not matches:
                continue

            # Weighted scoring:
            # - Title matches are worth 3x
            # - Key terms matches are worth 2x
            # - Other matches are worth 1x
            title_tokens = self._tokenize(doc.title)
            key_terms_tokens = self._tokenize(" ".join(doc.key_terms))

            score = 0.0
            for token in matches:
                if token in title_tokens:
                    score += 3.0
                elif token in key_terms_tokens:
                    score += 2.0
                else:
                    score += 1.0

            # Normalize by query length to favor documents matching more terms
            score /= len(query_tokens)

            scored.append((score, doc))

        # Sort by score descending
        scored.sort(key=lambda x: x[0], reverse=True)

        return [doc for _, doc in scored[:top_k]]

    def get_document_by_id(self, doc_id: str) -> Optional[WikiDocument]:
        """
        Retrieve a document by its ID.

        Args:
            doc_id: Document ID to look up

        Returns:
            WikiDocument if found, None otherwise
        """
        for doc in self.documents:
            if doc.id == doc_id:
                return doc
        return None

    def get_all_documents(self) -> List[WikiDocument]:
        """Return all loaded documents."""
        return self.documents

    def count(self) -> int:
        """Return number of loaded documents."""
        return len(self.documents)
```

**Verify:** `cd backend && python -m pytest tests/test_wiki_search_tool.py -v`
**Commit:** `feat(wiki): add WikiSearchTool with keyword intersection scoring`

---

### Task 2.2: Wiki Router Agent (`backend/wiki/wiki_router.py` — rewrite)

**File:** `backend/wiki/wiki_router.py`
**Test:** `backend/tests/test_wiki_router.py`
**Depends:** 1.1 (imports WikiDocument, WikiRoutingResult), 2.1 (uses WikiSearchTool)

This is the core rewrite. The new WikiRouterAgent replaces the Supabase-dependent WikiRouter with a JSON-based agent that uses WikiSearchTool for candidate selection and `inception/mercury-2` for LLM routing decisions.

```python
# backend/tests/test_wiki_router.py
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
        agent = WikiRouterAgent(index_path=sample_index_file)
        assert agent.search_tool is not None
        assert len(agent.search_tool.documents) == 2

    def test_route_returns_routing_result(self, sample_index_file):
        """route() returns WikiRoutingResult."""
        agent = WikiRouterAgent(index_path=sample_index_file)
        # Mock LLM to return valid JSON
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
        agent = WikiRouterAgent(index_path=sample_index_file)
        result = agent.route("")
        assert result.confidence == 0.0
        assert result.concepts == []

    def test_route_no_candidates(self, sample_index_file):
        """Query with no keyword matches returns empty result."""
        agent = WikiRouterAgent(index_path=sample_index_file)
        result = agent.route("квантовая физика термоядерный синтез")
        # No candidates → empty result (no LLM call)
        assert result.confidence == 0.0

    def test_route_llm_failure_fallback(self, sample_index_file):
        """LLM failure falls back to keyword-search candidates."""
        agent = WikiRouterAgent(index_path=sample_index_file)

        # Mock LLM to raise exception
        with patch.object(agent.client.chat.completions, 'create', side_effect=Exception("LLM error")):
            result = agent.route("заявка на подключение")

        # Should fall back to keyword results
        assert isinstance(result, WikiRoutingResult)
        # Confidence should be lower (fallback)
        assert result.confidence < 0.5

    def test_route_llm_invalid_json_retry(self, sample_index_file):
        """Invalid JSON from LLM triggers retry, then fallback."""
        agent = WikiRouterAgent(index_path=sample_index_file)

        # First call returns invalid JSON, second call also fails
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "not valid json {{{"

        with patch.object(agent.client.chat.completions, 'create', return_value=mock_response):
            result = agent.route("подключение к электросетям")

        # Should fall back after retries
        assert isinstance(result, WikiRoutingResult)

    def test_route_with_fallback(self, sample_index_file):
        """route_with_fallback works even when route returns empty."""
        agent = WikiRouterAgent(index_path=sample_index_file)

        # Mock route to return empty result
        empty_result = WikiRoutingResult(
            concepts=[], wiki_context="", search_hints=[],
            combined_keywords=[], document_filters={},
            matched_categories=[], confidence=0.0,
        )
        with patch.object(agent, 'route', return_value=empty_result):
            result = agent.route_with_fallback("как подать заявку")

        # Fallback should still return something (even if empty from route)
        assert isinstance(result, WikiRoutingResult)

    def test_format_candidates_for_llm(self, sample_index_file):
        """_format_candidates produces valid LLM prompt text."""
        agent = WikiRouterAgent(index_path=sample_index_file)
        doc = agent.search_tool.documents[0]
        formatted = agent._format_candidates([doc])
        assert doc.title in formatted
        assert doc.category in formatted
        assert "заявка" in formatted

    def test_missing_index_graceful(self, tmp_path):
        """Missing index file results in graceful empty results."""
        missing_path = tmp_path / "nonexistent.json"
        agent = WikiRouterAgent(index_path=missing_path)
        result = agent.route("как подать заявку")
        assert result.confidence == 0.0
        assert result.concepts == []
```

```python
# backend/wiki/wiki_router.py
"""
WikiRouterAgent — JSON-based agentic knowledge router.

Replaces the Supabase-dependent WikiRouter with a two-stage pipeline:
1. WikiSearchTool: fast keyword candidate search (microseconds)
2. LLM (inception/mercury-2): relevance scoring + context extraction

Produces WikiRoutingResult for downstream agents:
- QueryGenerator: key_terms, wiki_context
- SearchAgent: document_filters, search_hints
- ResponseAgent: wiki_context, business_rules
"""

import json
import logging
from typing import List, Optional

from langfuse.openai import OpenAI

import config
from wiki.models import WikiDocument, WikiRoutingResult
from wiki.search_tool import WikiSearchTool

logger = logging.getLogger(__name__)

# LLM prompt for wiki routing
WIKI_ROUTING_PROMPT = """Ты — эксперт-маршрутизатор базы знаний Башкирэнерго.

Запрос клиента: "{user_query}"

Кандидаты из базы знаний:
{formatted_candidates}

Задача:
1. Выбери 1-3 наиболее релевантных документа из кандидатов
2. Извлеки бизнес-правила, применимые к запросу
3. Определи фильтры: category, client_type, power_range
4. Собери key_terms для поисковых запросов

Верни JSON:
{{
  "selected_docs": ["doc_id_1", "doc_id_2"],
  "business_rules": ["Правило 1", "Правило 2"],
  "filters": {{
    "client_type": ["ФЛ"],
    "power_range": ["<15kW"],
    "category": ["ТПП"]
  }},
  "key_terms": ["термин1", "термин2"],
  "confidence": 0.85
}}

Если ни один документ не релевантен запросу, верни:
{{
  "selected_docs": [],
  "business_rules": [],
  "filters": {{}},
  "key_terms": [],
  "confidence": 0.0
}}"""


class WikiRouterAgent:
    """
    Agentic wiki router using keyword search + LLM refinement.

    Pipeline:
    1. WikiSearchTool.search() → candidate documents (top 5)
    2. If no candidates → return empty result
    3. Format candidates + user query into LLM prompt
    4. Call inception/mercury-2 with JSON output format
    5. Parse response into WikiRoutingResult
    """

    def __init__(
        self,
        index_path: Optional[str] = None,
        model: Optional[str] = None,
    ):
        """
        Initialize WikiRouterAgent.

        Args:
            index_path: Path to index.json. If None, uses config default.
            model: LLM model name. If None, uses config default.
        """
        self.model = model or getattr(config, "WIKI_ROUTER_MODEL", "inception/mercury-2")
        self.search_tool = WikiSearchTool(
            index_path=Path(index_path) if index_path else None
        )
        self.client = OpenAI(
            api_key=config.ROUTERAI_API_KEY,
            base_url=config.ROUTERAI_BASE_URL,
        )
        self._top_k_candidates = getattr(config, "WIKI_SEARCH_TOP_K", 5)
        self._top_k_selected = getattr(config, "WIKI_TOP_K", 3)
        logger.info(
            f"WikiRouterAgent initialized: model={self.model}, "
            f"documents={self.search_tool.count()}"
        )

    def route(self, user_query: str, top_k: int = 3) -> WikiRoutingResult:
        """
        Route a user query through the wiki knowledge layer.

        Args:
            user_query: User's question
            top_k: Max number of documents to select

        Returns:
            WikiRoutingResult with concepts, context, and filters
        """
        if not user_query or not user_query.strip():
            return WikiRoutingResult(
                concepts=[], wiki_context="", search_hints=[],
                combined_keywords=[], document_filters={},
                matched_categories=[], confidence=0.0,
            )

        # Stage 1: Keyword candidate search
        candidates = self.search_tool.search(
            user_query, top_k=self._top_k_candidates
        )

        if not candidates:
            logger.info("WikiRouter: no keyword candidates found")
            return WikiRoutingResult(
                concepts=[], wiki_context="", search_hints=[],
                combined_keywords=[], document_filters={},
                matched_categories=[], confidence=0.0,
            )

        logger.info(f"WikiRouter: {len(candidates)} keyword candidates")

        # Stage 2: LLM refinement
        try:
            result = self._llm_route(user_query, candidates, top_k)
            return result
        except Exception as e:
            logger.warning(f"WikiRouter: LLM routing failed — {e}")
            # Fallback: return keyword candidates without LLM refinement
            return self._fallback_result(candidates)

    def route_with_fallback(self, user_query: str) -> WikiRoutingResult:
        """
        Route with fallback strategy.

        If route returns empty and the index is small,
        return all documents as context.
        """
        result = self.route(user_query, top_k=3)

        if not result.concepts and self.search_tool.count() <= 15:
            # Fallback: return all documents for small indexes
            all_docs = self.search_tool.get_all_documents()
            logger.info(
                f"WikiRouter: fallback — returning all {len(all_docs)} documents"
            )
            return self._build_result_from_docs(all_docs, confidence=0.3)

        return result

    def _llm_route(
        self,
        user_query: str,
        candidates: List[WikiDocument],
        top_k: int,
    ) -> WikiRoutingResult:
        """
        Call LLM to select relevant documents and extract context.

        Args:
            user_query: User's question
            candidates: Keyword-search candidates
            top_k: Max documents to select

        Returns:
            WikiRoutingResult with LLM-selected documents
        """
        formatted = self._format_candidates(candidates)
        prompt = WIKI_ROUTING_PROMPT.format(
            user_query=user_query,
            formatted_candidates=formatted,
        )

        max_retries = 2
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "Ты эксперт-маршрутизатор. Отвечай ТОЛЬКО в формате JSON.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.15,
                    max_tokens=1000,
                    response_format={"type": "json_object"},
                )

                result_text = response.choices[0].message.content
                parsed = json.loads(result_text)
                return self._parse_llm_response(parsed, candidates, top_k)

            except json.JSONDecodeError as e:
                logger.warning(
                    f"WikiRouter: JSON parse error (attempt {attempt + 1}): {e}"
                )
                if attempt < max_retries - 1:
                    continue

            except Exception as e:
                logger.warning(f"WikiRouter: LLM error (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    continue

        # All retries failed — fallback
        logger.warning("WikiRouter: all LLM retries failed, using fallback")
        return self._fallback_result(candidates)

    def _format_candidates(self, candidates: List[WikiDocument]) -> str:
        """Format candidate documents for the LLM prompt."""
        parts = []
        for i, doc in enumerate(candidates, 1):
            parts.append(f"[{i}] ID: {doc.id}")
            parts.append(f"    Название: {doc.title}")
            parts.append(f"    Категория: {doc.category}")
            parts.append(f"    Описание: {doc.summary}")
            if doc.business_rules:
                parts.append(f"    Правила: {'; '.join(doc.business_rules)}")
            if doc.key_terms:
                parts.append(f"    Ключевые слова: {', '.join(doc.key_terms[:10])}")
            if doc.client_types and doc.client_types != ["any"]:
                parts.append(f"    Типы клиентов: {', '.join(doc.client_types)}")
            if doc.power_ranges and doc.power_ranges != ["any"]:
                parts.append(f"    Мощность: {', '.join(doc.power_ranges)}")
            parts.append("")
        return "\n".join(parts)

    def _parse_llm_response(
        self,
        parsed: dict,
        candidates: List[WikiDocument],
        top_k: int,
    ) -> WikiRoutingResult:
        """Parse LLM JSON response into WikiRoutingResult."""
        selected_ids = parsed.get("selected_docs", [])
        business_rules = parsed.get("business_rules", [])
        filters = parsed.get("filters", {})
        key_terms = parsed.get("key_terms", [])
        confidence = min(max(parsed.get("confidence", 0.5), 0.0), 1.0)

        # Map selected IDs to WikiDocument objects
        id_to_doc = {doc.id: doc for doc in candidates}
        selected_docs = []
        for doc_id in selected_ids[:top_k]:
            if doc_id in id_to_doc:
                selected_docs.append(id_to_doc[doc_id])

        # If no docs selected by LLM, return empty
        if not selected_docs:
            return WikiRoutingResult(
                concepts=[], wiki_context="", search_hints=[],
                combined_keywords=[], document_filters={},
                matched_categories=[], confidence=0.0,
            )

        return self._build_result_from_docs(
            selected_docs,
            business_rules=business_rules,
            extra_key_terms=key_terms,
            extra_filters=filters,
            confidence=confidence,
        )

    def _build_result_from_docs(
        self,
        docs: List[WikiDocument],
        business_rules: Optional[List[str]] = None,
        extra_key_terms: Optional[List[str]] = None,
        extra_filters: Optional[dict] = None,
        confidence: float = 0.5,
    ) -> WikiRoutingResult:
        """Build WikiRoutingResult from a list of WikiDocument."""
        # Wiki context
        context_parts = ["=== КОНТЕКСТ ИЗ WIKI (База знаний Башкирэнерго) ==="]
        for i, doc in enumerate(docs, 1):
            context_parts.append(f"\n--- Документ {i}: {doc.title} ---")
            context_parts.append(f"Категория: {doc.category}")
            context_parts.append(f"Описание: {doc.summary}")
            if doc.business_rules:
                context_parts.append("Ключевые правила:")
                for rule in doc.business_rules:
                    context_parts.append(f"  - {rule}")
            if doc.key_terms:
                context_parts.append(f"Ключевые слова: {', '.join(doc.key_terms)}")
        context_parts.append("\n=== КОНЕЦ КОНТЕКСТА WIKI ===")

        wiki_context = "\n".join(context_parts)

        # Search hints
        search_hints = []
        for doc in docs:
            search_hints.append(f"искать: {doc.title}")
            if doc.key_terms:
                search_hints.append(f"термины: {', '.join(doc.key_terms[:5])}")
        search_hints = list(dict.fromkeys(search_hints))  # deduplicate preserving order

        # Combined keywords
        combined_keywords = []
        seen = set()
        for doc in docs:
            for kw in doc.key_terms:
                if kw.lower() not in seen:
                    seen.add(kw.lower())
                    combined_keywords.append(kw)
        if extra_key_terms:
            for kw in extra_key_terms:
                if kw.lower() not in seen:
                    seen.add(kw.lower())
                    combined_keywords.append(kw)

        # Document filters
        client_types = set()
        power_ranges = set()
        categories = set()
        for doc in docs:
            for ct in doc.client_types:
                client_types.add(ct)
            for pr in doc.power_ranges:
                power_ranges.add(pr)
            categories.add(doc.category)

        # Merge LLM-provided filters
        if extra_filters:
            for ct in extra_filters.get("client_type", []):
                client_types.add(ct)
            for pr in extra_filters.get("power_range", []):
                power_ranges.add(pr)
            for cat in extra_filters.get("category", []):
                categories.add(cat)

        # Remove "any" if there are specific values
        if len(client_types) > 1 and "any" in client_types:
            client_types.discard("any")
        if len(power_ranges) > 1 and "any" in power_ranges:
            power_ranges.discard("any")

        document_filters = {
            "client_type": list(client_types),
            "power_range": list(power_ranges),
            "category": list(categories),
        }

        # Business rules (from LLM or from docs)
        all_rules = list(business_rules or [])
        for doc in docs:
            all_rules.extend(doc.business_rules)
        all_rules = list(dict.fromkeys(all_rules))  # deduplicate

        # Add business rules to wiki context if not already there
        if all_rules and "Ключевые правила:" not in wiki_context:
            rules_section = "\nБизнес-правила:\n" + "\n".join(f"  - {r}" for r in all_rules)
            wiki_context = wiki_context.replace(
                "=== КОНЕЦ КОНТЕКСТА WIKI ===",
                f"{rules_section}\n=== КОНЕЦ КОНТЕКСТА WIKI ==="
            )

        matched_categories = list(categories)

        return WikiRoutingResult(
            concepts=docs,
            wiki_context=wiki_context,
            search_hints=search_hints,
            combined_keywords=combined_keywords,
            document_filters=document_filters,
            matched_categories=matched_categories,
            confidence=confidence,
        )

    def _fallback_result(self, candidates: List[WikiDocument]) -> WikiRoutingResult:
        """Build fallback result from keyword candidates without LLM."""
        return self._build_result_from_docs(
            candidates[:3],  # Take top 3 keyword matches
            confidence=0.3,  # Lower confidence for fallback
        )

    def count_concepts(self) -> int:
        """Number of documents in the wiki index."""
        return self.search_tool.count()
```

**Verify:** `cd backend && python -m pytest tests/test_wiki_router.py -v`
**Commit:** `feat(wiki): rewrite WikiRouterAgent with JSON-based LLM routing`

---

### Task 2.3: Wiki Package Init (`backend/wiki/__init__.py` — update)

**File:** `backend/wiki/__init__.py`
**Test:** none (package init, tested via other tests)
**Depends:** 1.1, 2.1, 2.2 (imports all new modules)

```python
# backend/wiki/__init__.py
"""
Wiki Package — JSON-based Agentic Knowledge Layer for RAG pipeline.

Components:
- models: WikiDocument and WikiRoutingResult dataclasses
- search_tool: WikiSearchTool for fast keyword candidate search
- wiki_router: WikiRouterAgent for LLM-based routing decisions
- build_index: WikiIndexBuilder for generating index.json from enriched chunks

Legacy components (removed):
- wiki_store: Supabase-based storage (removed — no longer needed)
- wiki_extractor: LLM-powered extraction (removed — replaced by build_index)
"""

from wiki.models import WikiDocument, WikiRoutingResult
from wiki.search_tool import WikiSearchTool
from wiki.wiki_router import WikiRouterAgent

__all__ = ["WikiDocument", "WikiRoutingResult", "WikiSearchTool", "WikiRouterAgent"]
```

**Verify:** `cd backend && python -c "from wiki import WikiDocument, WikiRoutingResult, WikiSearchTool, WikiRouterAgent; print('OK')"`
**Commit:** `refactor(wiki): update __init__.py for new module structure`

---

## Batch 3: Integration (parallel — 3 implementers)

All tasks in this batch depend on Batch 2 completing.

### Task 3.1: Update `backend/main.py` — Integrate New WikiRouterAgent

**File:** `backend/main.py`
**Test:** `backend/tests/test_main_wiki_integration.py`
**Depends:** 2.2 (imports WikiRouterAgent)

The main change is replacing `from wiki.wiki_router import WikiRouter` with `from wiki.wiki_router import WikiRouterAgent` and updating the `AgenticRAG.__init__` and `query()` method. The `route_with_fallback` method name stays the same.

```python
# backend/tests/test_main_wiki_integration.py
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
        # Fields used by main.py
        assert hasattr(result, "wiki_context")
        assert hasattr(result, "document_filters")
        assert hasattr(result, "concepts")
        assert hasattr(result, "matched_categories")

    def test_agentic_rag_initializes_wiki_router(self):
        """AgenticRAG initializes WikiRouterAgent when ENABLE_WIKI_ROUTER is True."""
        with patch.dict("os.environ", {"ENABLE_WIKI_ROUTER": "true"}):
            import config
            # Force re-read of config
            config.ENABLE_WIKI_ROUTER = True

            with patch("wiki.wiki_router.WikiSearchTool") as mock_search:
                mock_search.return_value.documents = []
                mock_search.return_value.count.return_value = 0
                from main import AgenticRAG
                rag = AgenticRAG()
                assert hasattr(rag, "wiki_router")
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

        # Verify the result has the expected fields
        assert mock_result.wiki_context == "Test wiki context"
        assert "ТПП" in mock_result.document_filters["category"]
```

Changes to `backend/main.py` — replace lines 15-16 and 48:

```python
# OLD (line 15):
# from wiki.wiki_router import WikiRouter

# NEW (line 15):
from wiki.wiki_router import WikiRouterAgent

# OLD (line 48):
# self.wiki_router = WikiRouter()

# NEW (line 48):
self.wiki_router = WikiRouterAgent()

# The rest of main.py stays the same because:
# - WikiRouterAgent has the same route_with_fallback() method
# - WikiRoutingResult has the same fields (wiki_context, document_filters, concepts, matched_categories)
# - The interface is compatible
```

**Verify:** `cd backend && python -m pytest tests/test_main_wiki_integration.py -v`
**Commit:** `feat(main): integrate WikiRouterAgent replacing WikiRouter`

---

### Task 3.2: Update `backend/config.py` — Remove Supabase Wiki Vars

**File:** `backend/config.py`
**Test:** `backend/tests/test_wiki_config.py` (already written in Task 1.2)
**Depends:** 1.2 (config changes)

This task applies the config changes from Task 1.2. The test was already written there. Here we just make the actual edit to `config.py`.

Replace lines 84-89 in `backend/config.py`:

```python
# OLD (lines 84-89):
# =============================================================================
# LLM WIKI (Karpathy-style Knowledge Graph)
# =============================================================================

ENABLE_WIKI_ROUTER = os.getenv("ENABLE_WIKI_ROUTER", "false").lower() == "true"
WIKI_TABLE_NAME = os.getenv("WIKI_TABLE_NAME", "wiki_concepts")
WIKI_TOP_K_CONCEPTS = int(os.getenv("WIKI_TOP_K_CONCEPTS", "3"))

# NEW:
# =============================================================================
# WIKI ROUTER (JSON-based Agentic Knowledge Layer)
# =============================================================================

ENABLE_WIKI_ROUTER = os.getenv("ENABLE_WIKI_ROUTER", "true").lower() == "true"
WIKI_INDEX_PATH = Path(os.getenv("WIKI_INDEX_PATH", str(BASE_DIR / "wiki" / "data" / "index.json")))
WIKI_ROUTER_MODEL = os.getenv("WIKI_ROUTER_MODEL", "inception/mercury-2")
WIKI_TOP_K = int(os.getenv("WIKI_TOP_K", "3"))
WIKI_SEARCH_TOP_K = int(os.getenv("WIKI_SEARCH_TOP_K", "5"))
```

**Verify:** `cd backend && python -m pytest tests/test_wiki_config.py -v`
**Commit:** `refactor(config): replace Supabase wiki vars with JSON-based config`

---

### Task 3.3: Generate Initial `index.json` Data File

**File:** `backend/wiki/data/index.json`
**Test:** none (generated artifact, validated by build_index tests)
**Depends:** 1.3 (build_index.py must exist)

This task runs the build script to generate the initial `index.json` from existing enriched chunks.

```bash
# Run from backend directory:
cd backend && python -m wiki.build_index
```

After running, verify the output:
```bash
# Check that index.json was created and has documents:
python -c "import json; data = json.load(open('wiki/data/index.json', encoding='utf-8')); print(f'Documents: {len(data[\"documents\"])}')"
```

Also create a URL mapping file for source files that have known URLs:

```python
# backend/wiki/data/url_mapping.json
# This file maps source_file names to their URLs on bashkirenergo.ru
# The build_index.py script reads this to populate the url field.
{
    "gid-po-tp.md": "https://www.bashkirenergo.ru/consumers/gid-po-tekhnologicheskomu-prisoedineniyu/",
    "tp-do-15kvt.md": "https://www.bashkirenergo.ru/consumers/gid-po-tekhnologicheskomu-prisoedineniyu/15kvt/",
    "1-shag-podacha-zayavki.md": "https://www.bashkirenergo.ru/consumers/gid-po-tekhnologicheskomu-prisoedineniyu/1-shag/",
    "2-shag-vypolnenie-rabot.md": "https://www.bashkirenergo.ru/consumers/gid-po-tekhnologicheskomu-prisoedineniyu/2-shag/",
    "3-shag-poluchenie-aktov.md": "https://www.bashkirenergo.ru/consumers/gid-po-tekhnologicheskomu-prisoedineniyu/3-shag/",
    "faq-kt-tpp-2026.md": "https://www.bashkirenergo.ru/consumers/gid-po-tekhnologicheskomu-prisoedineniyu/questions/"
}
```

**Verify:** `cd backend && python -m wiki.build_index && python -c "import json; d=json.load(open('wiki/data/index.json',encoding='utf-8')); print(f'{len(d[\"documents\"])} docs')"`
**Commit:** `feat(wiki): generate initial index.json from enriched chunks`

---

## Batch 4: Cleanup (sequential — 1 implementer)

### Task 4.1: Remove Legacy Wiki Files and Update Imports

**Files to delete:**
- `backend/wiki/wiki_store.py` — Supabase-dependent, no longer needed
- `backend/wiki/wiki_extractor.py` — LLM extraction replaced by build_index.py

**Files to update:**
- `backend/wiki/__init__.py` — already updated in Task 2.3
- `backend/main.py` — already updated in Task 3.1

**Test:** `backend/tests/test_wiki_cleanup.py`
**Depends:** 3.1, 3.2, 3.3 (all integration complete)

```python
# backend/tests/test_wiki_cleanup.py
"""Tests that legacy wiki modules are removed and new modules work."""
import pytest
import importlib


class TestWikiCleanup:
    """Verify legacy modules are gone and new modules work."""

    def test_wiki_store_removed(self):
        """wiki_store module should not be importable."""
        with pytest.raises(ImportError):
            importlib.import_module("wiki.wiki_store")

    def test_wiki_extractor_removed(self):
        """wiki_extractor module should not be importable."""
        with pytest.raises(ImportError):
            importlib.import_module("wiki.wiki_extractor")

    def test_wiki_models_importable(self):
        """wiki.models should be importable."""
        from wiki.models import WikiDocument, WikiRoutingResult
        assert WikiDocument is not None
        assert WikiRoutingResult is not None

    def test_wiki_search_tool_importable(self):
        """wiki.search_tool should be importable."""
        from wiki.search_tool import WikiSearchTool
        assert WikiSearchTool is not None

    def test_wiki_router_agent_importable(self):
        """wiki.wiki_router should import WikiRouterAgent."""
        from wiki.wiki_router import WikiRouterAgent
        assert WikiRouterAgent is not None

    def test_wiki_build_index_importable(self):
        """wiki.build_index should be importable."""
        from wiki.build_index import WikiIndexBuilder
        assert WikiIndexBuilder is not None

    def test_no_supabase_imports_in_wiki(self):
        """No wiki module should import from supabase."""
        import wiki.models
        import wiki.search_tool
        import wiki.wiki_router
        import wiki.build_index

        for module in [wiki.models, wiki.search_tool, wiki.wiki_router, wiki.build_index]:
            source = inspect.getsource(module)
            assert "from supabase" not in source
            assert "import supabase" not in source
```

After deleting the legacy files, verify the entire wiki package works:

```bash
cd backend && python -m pytest tests/test_wiki_models.py tests/test_wiki_config.py tests/test_wiki_search_tool.py tests/test_wiki_router.py tests/test_wiki_cleanup.py -v
```

**Verify:** `cd backend && python -m pytest tests/test_wiki_*.py -v`
**Commit:** `chore(wiki): remove legacy Supabase-dependent wiki_store and wiki_extractor`

---

## Summary

| Batch | Task | File | Action | Depends |
|-------|------|------|--------|---------|
| 1 | 1.1 | `backend/wiki/models.py` | CREATE | none |
| 1 | 1.2 | `backend/config.py` | MODIFY | none |
| 1 | 1.3 | `backend/wiki/build_index.py` | CREATE | 1.1 |
| 2 | 2.1 | `backend/wiki/search_tool.py` | CREATE | 1.1 |
| 2 | 2.2 | `backend/wiki/wiki_router.py` | REWRITE | 1.1, 2.1 |
| 2 | 2.3 | `backend/wiki/__init__.py` | REWRITE | 1.1, 2.1, 2.2 |
| 3 | 3.1 | `backend/main.py` | MODIFY | 2.2 |
| 3 | 3.2 | `backend/config.py` | MODIFY (apply 1.2) | 1.2 |
| 3 | 3.3 | `backend/wiki/data/index.json` | GENERATE | 1.3 |
| 4 | 4.1 | `backend/wiki/wiki_store.py`, `backend/wiki/wiki_extractor.py` | DELETE | 3.1, 3.2, 3.3 |

**Total: 10 micro-tasks across 4 batches**

### Key Design Decisions

1. **WikiDocument in separate `models.py`** — avoids circular imports between `search_tool.py` and `wiki_router.py`
2. **`ENABLE_WIKI_ROUTER` defaults to `true`** — the new system works without Supabase, so it should be on by default
3. **`WIKI_ROUTER_MODEL` defaults to `inception/mercury-2`** — per design spec, fast LLM for routing
4. **Keyword search scoring uses weighted tokens** — title matches 3x, key_terms 2x, other 1x
5. **LLM routing uses `response_format={"type":"json_object"}`** — forces JSON output from mercury-2
6. **Fallback on LLM failure** — returns keyword candidates with lower confidence (0.3)
7. **`business_rules` field starts empty in index.json** — the LLM router extracts rules at query time from document summaries and key_terms
8. **`url_mapping.json` is optional** — build_index.py works without it, URLs default to empty string
9. **`route_with_fallback` method preserved** — same interface as old WikiRouter, minimal changes to main.py