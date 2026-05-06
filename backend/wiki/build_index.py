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
