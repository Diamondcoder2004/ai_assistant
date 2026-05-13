"""
Search Agent — агент поиска с Tool Calling
"""
import logging
import uuid
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
from math import ceil
from typing import List, Optional, Dict, Any, Tuple

import config
from qdrant_client.http import models
from tools.search_tool import SearchTool, SearchRequest, SearchResult, build_qdrant_filter
from tools.relevance_filter import (
    filter_by_overlap,
    is_regulatory_query,
    compute_source_quality,
)
from agents.query_generator import QueryGeneratorAgent, QueryGenerationResult
from utils.timing import timing, timing_context
from utils.agent_logger import log_agent_response
from utils.langfuse_tracer import observe_rag

logger = logging.getLogger(__name__)


class SearchAgent:
    """
    Агент поиска с использованием Tool Calling.
    
    Использует LLM для:
    - Принятия решения о поиске
    - Выбора стратегии поиска (конкатенация или раздельно)
    - Подбора параметров поиска (веса, k)
    - Анализа результатов и принятия решения о дополнительном поиске
    """
    
    def __init__(self):
        self.search_tool = SearchTool()
        self.query_generator = QueryGeneratorAgent()
        logger.info("SearchAgent инициализирован")
    
    @timing("SearchAgent.search")
    @observe_rag(name="SearchAgent.search")
    def search(
        self,
        user_query: str,
        history: str = "",
        category: str = "не известна",
        auto_retry: bool = True,
        max_retries: int = 2,
        user_hints: Optional[Dict[str, Any]] = None,
        query_id: Optional[str] = None,
        session_id: Optional[str] = None,
        session_logger: Optional[Any] = None,
        document_filters: Optional[Dict[str, List[str]]] = None,
        skip_query_generator: bool = False,
    ) -> Dict[str, Any]:
        """
        Поиск с использованием агента.

        Args:
            user_query: Вопрос пользователя
            history: История диалога
            category: Категория клиента
            auto_retry: Автоматическая повторная попытка при плохих результатах
            max_retries: Максимальное количество повторных попыток
            user_hints: Рекомендации от пользователя (k, weights, и т.д.)
            query_id: Уникальный ID запроса (для логирования)
            session_id: ID сессии (для логирования)
            skip_query_generator: Пропустить QueryGenerator, искать по сырому запросу

        Returns:
            Словарь с результатами:
            - clarification_needed: bool
            - clarification_questions: List[str]
            - results: List[SearchResult]
            - queries_used: List[str]
            - search_params: Dict
            - confidence: float
        """
        _query_id = query_id or str(uuid.uuid4())
        _session_id = session_id or "unknown"
        _start_time = time.time()
        
        logger.info(f"SearchAgent: поиск для '{user_query[:50]}...'")
        if user_hints:
            logger.info(f"Рекомендации от пользователя: {user_hints}")

        # 1. Генерация поисковых запросов (либо QueryGenerator LLM, либо сырой запрос)
        if skip_query_generator:
            logger.info(f"SearchAgent: QueryGenerator пропущен — поиск по сырому запросу")
            queries = [user_query]
            gen_search_params = {"strategy": "concat", "k": 10}
            gen_confidence = 0.8
            gen_clarification_needed = False
            gen_clarification_questions = []
            gen_reasoning = ""
            if session_logger:
                session_logger.add_step("QueryGenerator", "skipped", {"reason": "skip_query_generator"}, {}, 0)
        else:
            if session_logger:
                with session_logger.step(
                    "QueryGenerator",
                    "generate",
                    {
                        "query": user_query,
                        "history_length": len(history),
                        "category": category,
                        "user_hints": user_hints or {}
                    }
                ) as query_step:
                    gen_result = self.query_generator.generate(
                        user_query=user_query,
                        history=history,
                        category=category,
                        user_hints=user_hints,
                        query_id=_query_id,
                        session_id=_session_id
                    )
                    
                    query_step.set_output({
                        "queries": [q["text"] for q in gen_result.queries],
                        "search_params": gen_result.search_params,
                        "clarification_needed": gen_result.clarification_needed,
                        "clarification_questions": gen_result.clarification_questions,
                        "confidence": gen_result.confidence
                    })
            else:
                gen_result = self.query_generator.generate(
                    user_query=user_query,
                    history=history,
                    category=category,
                    user_hints=user_hints,
                    query_id=_query_id,
                    session_id=_session_id
                )
            # Extract results from generator
            queries = self.query_generator.get_queries_text(gen_result)
            gen_search_params = gen_result.search_params
            gen_confidence = gen_result.confidence
            gen_clarification_needed = gen_result.clarification_needed
            gen_clarification_questions = gen_result.clarification_questions
            gen_reasoning = gen_result.reasoning

        # 2. Проверка необходимости уточнения (только если QueryGenerator работал)
        if gen_clarification_needed:
            logger.info("Требуется уточнение")
            result = {
                "clarification_needed": True,
                "clarification_questions": gen_clarification_questions,
                "results": [],
                "queries_used": [],
                "search_params": gen_search_params,
                "confidence": gen_confidence,
                "reasoning": gen_reasoning
            }
            # Логирование результата
            log_agent_response(
                query_id=_query_id,
                session_id=_session_id,
                user_query=user_query,
                response_data={
                    "answer": "",
                    "sources": [],
                    "queries_used": [],
                    "search_params": gen_search_params,
                    "confidence": gen_confidence,
                    "reasoning": gen_reasoning,
                    "clarification_needed": True,
                    "clarification_questions": gen_clarification_questions
                },
                timing_info={"total_time": time.time() - _start_time}
            )
            return result

        # Build Qdrant filter from document_filters
        qf_filter = build_qdrant_filter(document_filters)
        if qf_filter:
            logger.info(f"Qdrant filter applied: {document_filters}")

        # 2.5 Category-aware blended search (if QueryGenerator detected ЛК or ДУ)
        if not skip_query_generator:
            detected_category = gen_result.detected_category
        else:
            detected_category = "\u043d\u0435 \u0438\u0437\u0432\u0435\u0441\u0442\u043d\u0430"

        use_blended = (
            config.CATEGORY_FILTER_ENABLED
            and detected_category in ("\u041b\u041a", "\u0414\u0423")
            and gen_confidence >= 0.6
            and not gen_clarification_needed
        )

        # 3. Выполнение поиска
        strategy = gen_search_params.get("strategy", "concat")
        k_per_query = gen_search_params.get("k", 10)
        if user_hints and user_hints.get("k"):
            k_per_query = user_hints.get("k")

        if use_blended:
            logger.info(
                f"Category-aware search: detected={detected_category}, "
                f"confidence={gen_confidence:.2f}, k={k_per_query}"
            )

        logger.info(f"Поиск по запросам: {queries}, стратегия: {strategy}")

        if use_blended:
            # Category-aware blended search (parallel filtered + unfiltered)
            results = self._blended_search(
                queries=queries,
                k=k_per_query,
                category=detected_category,
                qf_filter=qf_filter,
            )
        else:
            # Existing single search (no category filter)
            with timing_context("SearchAgent.tool_search"):
                results = self.search_tool.search_multi(
                    queries=queries,
                    qf_filter=qf_filter,
                    k=k_per_query * len(queries) if strategy == "separate" else k_per_query,
                )

        # 3.5 Post-retrieval relevance filter: drop chunks with zero token overlap
        before_filter = len(results)
        results = filter_by_overlap(results, user_query)
        if len(results) < before_filter:
            logger.info(
                f"Relevance filter: {len(results)}/{before_filter} chunks kept"
            )

        # 3.6 Regulatory query boost: if query sounds legal/regulatory,
        # boost normative_documents results to overcome FAQ ranking bias
        if config.REGULATORY_QUERY_BOOST and is_regulatory_query(user_query):
            boost_factor = config.REGULATORY_QUERY_BOOST_FACTOR
            boosted = 0
            for r in results:
                if r.collection_name == config.NORMATIVE_COLLECTION_NAME:
                    r.score_hybrid = round(r.score_hybrid * boost_factor, 4)
                    boosted += 1
            if boosted > 0:
                # Re-sort by boosted score
                results.sort(key=lambda r: r.score_hybrid, reverse=True)
                logger.info(
                    f"Regulatory boost: {boosted} normative chunks boosted "
                    f"(x{boost_factor}), re-sorted"
                )

        # 3.7 Source quality scoring: compute quality metrics for the
        # surviving chunks (used by ResponseAgent to decide low-confidence)
        source_quality = compute_source_quality(results, user_query)
        if source_quality["is_low_quality"]:
            logger.warning(
                f"Low source quality: score={source_quality['score']}, "
                f"overlap={source_quality['avg_overlap']}, "
                f"kept={source_quality['survived_count']}"
            )

        # 4. Оценка качества результатов
        confidence = gen_confidence
        if len(results) < 3:
            logger.warning(f"Мало результатов: {len(results)}")
            confidence *= 0.7

        # 5. Автоматическая повторная попытка если нужно
        if auto_retry and len(results) < 3 and max_retries > 0:
            logger.info(f"Попытка {max_retries}: повторный поиск с другими параметрами")
            retry_result = self._retry_search(
                user_query=user_query,
                original_queries=queries,
                max_retries=max_retries - 1,
                document_filters=document_filters,
            )
            if len(retry_result["results"]) > len(results):
                results = retry_result["results"]
                queries = retry_result["queries_used"]

        logger.info(f"Поиск завершён: найдено {len(results)} результатов")

        result = {
            "clarification_needed": False,
            "clarification_questions": [],
            "results": results,
            "queries_used": queries,
            "search_params": gen_search_params,
            "confidence": confidence,
            "reasoning": gen_reasoning,
            "source_quality": source_quality,  # P3.2: quality metrics for ResponseAgent
        }
        
        # Логирование результата поиска
        log_agent_response(
            query_id=_query_id,
            session_id=_session_id,
            user_query=user_query,
            response_data={
                "answer": "",
                "sources": [
                    {
                        "id": r.id,
                        "filename": r.filename,
                        "breadcrumbs": r.breadcrumbs,
                        "score_hybrid": r.score_hybrid,
                        "score_semantic": r.score_semantic,
                        "score_lexical": r.score_lexical,
                        "collection_name": r.collection_name,
                        # Per-component scores from metadata (for retrieval quality diagnosis)
                        "pref_score": r.metadata.get("pref_score", 0.0),
                        "hype_score": r.metadata.get("hype_score", 0.0),
                        "contextual_score": r.metadata.get("contextual_score", 0.0),
                        "bm25_score": r.metadata.get("bm25_score", 0.0),
                    }
                    for r in results[:10]
                ],
                "queries_used": queries,
                "search_params": gen_search_params,
                "confidence": confidence,
                "reasoning": gen_reasoning
            },
            timing_info={"total_time": time.time() - _start_time}
        )
        
        return result



    @observe_rag(name="SearchAgent._retry_search")
    def _retry_search(
        self,
        user_query: str,
        original_queries: List[str],
        max_retries: int = 1,
        document_filters: Optional[Dict[str, List[str]]] = None,
    ) -> Dict[str, Any]:
        """Повторный поиск с изменёнными параметрами."""
        # Попытка с увеличенным k и изменёнными весами
        retry_params = {
            "k": 15,
            "pref_weight": 0.25,
            "hype_weight": 0.25,
            "lexical_weight": 0.25,
            "contextual_weight": 0.25,
            "strategy": "separate"
        }
        
        qf_filter = build_qdrant_filter(document_filters)
        results = self.search_tool.search_multi(
            queries=original_queries,
            qf_filter=qf_filter,
            k=10,
        )
        
        return {
            "results": results,
            "queries_used": original_queries,
            "search_params": retry_params
        }

    def _blended_search(
        self,
        queries: List[str],
        k: int,
        category: str,
        qf_filter: Optional[models.Filter] = None,
        weights: Optional[Dict[str, float]] = None,
    ) -> List[SearchResult]:
        """
        Two-phase blended search with filtered and unfiltered results.

        30% top-k comes from category-filtered search (ЛК or ДУ),
        70% from unfiltered search. Graceful degradation:
        if filtered is empty - fall back to unfiltered.
        """
        blend_ratio = config.CATEGORY_FILTER_BLEND_RATIO
        filtered_k = max(1, ceil(k * blend_ratio))
        unfiltered_k = k

        # Category filter via existing build_qdrant_filter
        category_filter = build_qdrant_filter({"category": [category]})

        logger.info(
            f"Blended search: category={category}, "
            f"filtered_k={filtered_k}, unfiltered_k={unfiltered_k}, "
            f"total_k={k}, blend_ratio={blend_ratio}"
        )

        # Parallel searches
        with ThreadPoolExecutor(max_workers=2) as executor:
            f_future = executor.submit(
                self.search_tool.search_multi,
                queries=queries,
                qf_filter=category_filter,
                k=filtered_k,
                weights=weights,
            )
            u_future = executor.submit(
                self.search_tool.search_multi,
                queries=queries,
                qf_filter=qf_filter,
                k=unfiltered_k,
                weights=weights,
            )
            try:
                filtered_results = f_future.result()
            except Exception as e:
                logger.warning(f"Filtered search failed: {e}. Falling back to unfiltered only.")
                filtered_results = []

            try:
                unfiltered_results = u_future.result()
            except Exception as e:
                logger.warning(f"Unfiltered search failed: {e}. Falling back to filtered only.")
                unfiltered_results = []

        logger.info(
            f"Blended search results: {len(filtered_results)} filtered, "
            f"{len(unfiltered_results)} unfiltered"
        )

        return blend_results(
            filtered=filtered_results,
            unfiltered=unfiltered_results,
            total_k=k,
        )

    def format_results(self, results: List[SearchResult], top_k: int = 5) -> str:
        """
        Форматирование результатов для передачи в LLM.
        
        Args:
            results: Список результатов поиска
            top_k: Количество лучших результатов
        
        Returns:
            Форматированный текст
        """
        if not results:
            return "Результаты поиска: ничего не найдено."
        
        formatted = []
        for i, result in enumerate(results[:top_k], 1):
            text = (
                f"[Источник {i}]\n"
                f"Документ: {result.filename}\n"
                f"Раздел: {result.breadcrumbs}\n"
                f"Категория: {result.category}\n"
                f"Текст: {result.content[:500]}...\n"
                f"Релевантность: {result.score_hybrid:.3f}\n"
            )
            formatted.append(text)
        
        return "\n---\n".join(formatted)


# =============================================================================
# Category-aware blended search
# =============================================================================


def blend_results(
    filtered: List[SearchResult],
    unfiltered: List[SearchResult],
    total_k: int,
) -> List[SearchResult]:
    """
    Blend filtered and unfiltered search results.

    - All filtered results go into the final list (they are prioritized).
    - unfiltered fill remaining slots up to total_k, skipping duplicates by .id.
    - Final sort by score_hybrid (descending).
    - If filtered is empty - uses only unfiltered (graceful degradation).
    """
    blended = list(filtered)
    seen_ids = {r.id for r in blended}

    for r in unfiltered:
        if len(blended) >= total_k:
            break
        if r.id not in seen_ids:
            blended.append(r)
            seen_ids.add(r.id)

    blended.sort(key=lambda r: r.score_hybrid, reverse=True)
    return blended[:total_k]
