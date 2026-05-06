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
