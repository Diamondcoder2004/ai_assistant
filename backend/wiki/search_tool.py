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
            if category and doc.category != category:
                continue

            doc_tokens = self._tokenize(doc.searchable_text())
            matches = query_tokens & doc_tokens
            if not matches:
                continue

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

            score /= len(query_tokens)
            scored.append((score, doc))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [doc for _, doc in scored[:top_k]]

    def get_document_by_id(self, doc_id: str) -> Optional[WikiDocument]:
        """Retrieve a document by its ID."""
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
