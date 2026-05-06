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
