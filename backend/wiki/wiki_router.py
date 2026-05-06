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
from pathlib import Path
from typing import List, Optional

from langfuse.openai import OpenAI

import config
from wiki.models import WikiDocument, WikiRoutingResult
from wiki.search_tool import WikiSearchTool

logger = logging.getLogger(__name__)

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

        try:
            result = self._llm_route(user_query, candidates, top_k)
            return result
        except Exception as e:
            logger.warning(f"WikiRouter: LLM routing failed — {e}")
            return self._fallback_result(candidates)

    def route_with_fallback(self, user_query: str) -> WikiRoutingResult:
        """
        Route with fallback strategy.

        If route returns empty and the index is small,
        return all documents as context.
        """
        result = self.route(user_query, top_k=3)

        if not result.concepts and self.search_tool.count() <= 15:
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

        id_to_doc = {doc.id: doc for doc in candidates}
        selected_docs = []
        for doc_id in selected_ids[:top_k]:
            if doc_id in id_to_doc:
                selected_docs.append(id_to_doc[doc_id])

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

        search_hints = []
        for doc in docs:
            search_hints.append(f"искать: {doc.title}")
            if doc.key_terms:
                search_hints.append(f"термины: {', '.join(doc.key_terms[:5])}")
        search_hints = list(dict.fromkeys(search_hints))

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

        client_types = set()
        power_ranges = set()
        categories = set()
        for doc in docs:
            for ct in doc.client_types:
                client_types.add(ct)
            for pr in doc.power_ranges:
                power_ranges.add(pr)
            categories.add(doc.category)

        if extra_filters:
            for ct in extra_filters.get("client_type", []):
                client_types.add(ct)
            for pr in extra_filters.get("power_range", []):
                power_ranges.add(pr)
            for cat in extra_filters.get("category", []):
                categories.add(cat)

        if len(client_types) > 1 and "any" in client_types:
            client_types.discard("any")
        if len(power_ranges) > 1 and "any" in power_ranges:
            power_ranges.discard("any")

        document_filters = {
            "client_type": list(client_types),
            "power_range": list(power_ranges),
            "category": list(categories),
        }

        all_rules = list(business_rules or [])
        for doc in docs:
            all_rules.extend(doc.business_rules)
        all_rules = list(dict.fromkeys(all_rules))

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
            candidates[:3],
            confidence=0.3,
        )

    def count_concepts(self) -> int:
        """Number of documents in the wiki index."""
        return self.search_tool.count()
