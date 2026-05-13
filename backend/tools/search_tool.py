"""
Search Tool — инструмент поиска в базе знаний (две коллекции).
"""
import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

from qdrant_client import QdrantClient
from qdrant_client.http import models
import numpy as np
import pymorphy3

import config
from utils.router_embedding import get_routerai_embedder

logger = logging.getLogger(__name__)

_morph_analyzer = None


def get_morph_analyzer():
    """Получение экземпляра MorphAnalyzer (синглтон)."""
    global _morph_analyzer
    if _morph_analyzer is None:
        logger.info("Инициализация MorphAnalyzer...")
        _morph_analyzer = pymorphy3.MorphAnalyzer()
    return _morph_analyzer


@dataclass
class SearchRequest:
    """Запрос на поиск."""
    query: str
    k: int = 10
    pref_weight: float = 0.25
    hype_weight: float = 0.25
    lexical_weight: float = 0.25
    contextual_weight: float = 0.25


@dataclass
class SearchResult:
    """Результат поиска."""
    id: str
    content: str
    summary: str
    category: str
    filename: str
    breadcrumbs: str
    score_hybrid: float
    score_semantic: float
    score_lexical: float
    metadata: Dict[str, Any]
    collection_name: str = ""  # NEW: which collection this result came from


def build_qdrant_filter(
    document_filters: Optional[Dict[str, List[str]]] = None
) -> Optional[models.Filter]:
    """
    Convert Wiki Router document_filters dict to Qdrant Filter.
    
    Args:
        document_filters: {"client_type": ["ФЛ"], "power_range": ["<15kW"], "category": ["ТПП"]}
    
    Returns:
        Qdrant Filter object or None
    """
    if not document_filters:
        return None
    
    conditions = []
    
    if "category" in document_filters and document_filters["category"]:
        categories = list(document_filters["category"])
        # Нормативные документы (ФЗ, ПП) имеют category="Общая" и нужны при любом запросе.
        # Добавляем "Общая" чтобы они не выпадали из выборки при фильтрации по ТПП/ЛК/ДУ.
        if "Общая" not in categories:
            categories.append("Общая")
        conditions.append(models.FieldCondition(
            key="category",
            match=models.MatchAny(any=categories)
        ))
    
    if "client_type" in document_filters and document_filters["client_type"]:
        # Add "any" to avoid excluding general documents
        types = list(document_filters["client_type"])
        if "any" not in types:
            types.append("any")
        conditions.append(models.FieldCondition(
            key="client_type",
            match=models.MatchAny(any=types)
        ))
    
    if "power_range" in document_filters and document_filters["power_range"]:
        ranges = list(document_filters["power_range"])
        if "any" not in ranges:
            ranges.append("any")
        conditions.append(models.FieldCondition(
            key="power_range",
            match=models.MatchAny(any=ranges)
        ))
    
    if "document_type" in document_filters and document_filters["document_type"]:
        conditions.append(models.FieldCondition(
            key="document_type",
            match=models.MatchAny(any=document_filters["document_type"])
        ))
    
    return models.Filter(must=conditions) if conditions else None


class SearchTool:
    """
    Инструмент поиска в базе знаний с гибридным поиском по двум коллекциям.
    
    Поддерживает 4 компонента:
    - pref: семантический вектор (summary + content)
    - hype: семантический вектор (hypothetical questions)
    - lexical: BM25 (токенизированный текст)
    - contextual: семантический вектор (соседние чанки)
    """
    
    def __init__(self):
        self.client = QdrantClient(
            host=config.QDRANT_HOST,
            port=config.QDRANT_PORT,
            timeout=30,
            check_compatibility=False,
        )
        self.collections = [
            config.NORMATIVE_COLLECTION_NAME,
            config.OPERATIONAL_COLLECTION_NAME,
        ]
        self.embedder = get_routerai_embedder()
        self.bm25 = None
        self.documents = []
        self.point_ids = []
        self.payloads = {}
        self._loaded = False
        
    def load(self, force: bool = False):
        """Загрузка документов для BM25 из ОБЕИХ коллекций."""
        if self._loaded and not force:
            return

        logger.info("Загрузка документов для поиска из двух коллекций...")
        self.documents = []
        self.point_ids = []
        self.payloads = {}

        for coll_name in self.collections:
            try:
                scroll_result = self.client.scroll(
                    collection_name=coll_name,
                    with_payload=True,
                    with_vectors=False,
                    limit=10000
                )
                
                points, next_page = scroll_result
                while True:
                    for point in points:
                        payload = point.payload
                        content = payload.get("content", "") or payload.get("chunk_content", "")
                        
                        # For FAQ add summary and questions for better BM25
                        full_text = content
                        if payload.get("category") == "faqs" or payload.get("document_type") == "faq":
                            summary = payload.get("summary", "") or payload.get("chunk_summary", "")
                            questions_str = payload.get("questions", "")
                            full_text = f"{content} {summary} {questions_str}"
                        
                        self.documents.append(self._tokenize_text(full_text))
                        self.point_ids.append(point.id)
                        self.payloads[point.id] = payload

                    if next_page is None:
                        break
                    scroll_result = self.client.scroll(
                        collection_name=coll_name,
                        with_payload=True,
                        with_vectors=False,
                        offset=next_page.offset,
                        limit=10000
                    )
                    points, next_page = scroll_result
                
                logger.info(f"Загружено из '{coll_name}': {len(self.documents)} документов")
            except Exception as e:
                logger.warning(f"⚠️ Ошибка загрузки из '{coll_name}': {e}. Продолжаем...")

        self._loaded = True
        logger.info(f"Всего загружено {len(self.documents)} документов из обеих коллекций")
    
    def _tokenize_text(self, text: str) -> list:
        """Токенизация текста с лемматизацией."""
        import re
        try:
            morph = get_morph_analyzer()
            words = re.findall(r'\w+', text.lower())
            return [morph.parse(word)[0].normal_form for word in words]
        except ImportError:
            return re.findall(r'\w+', text.lower())
    
    def _get_bm25_scores(self, query: str) -> Dict[str, float]:
        """Получение BM25 оценок (единое пространство для обеих коллекций)."""
        from rank_bm25 import BM25Plus

        query_tokens = self._tokenize_text(query)
        
        if not query_tokens:
            return {pid: 0.0 for pid in self.point_ids}
        
        bm25 = BM25Plus(self.documents)
        scores = bm25.get_scores(query_tokens)

        max_score = max(scores) if len(scores) > 0 else 1.0
        
        if max_score <= 0:
            return {pid: 0.0 for pid in self.point_ids}
        
        normalized = {}
        for idx, score in enumerate(scores):
            point_id = self.point_ids[idx]
            normalized_score = max(0.0, float(score / max_score))
            normalized[point_id] = normalized_score if max_score > 0 else 0.0

        return normalized
    
    def search(
        self,
        request: SearchRequest,
        collection_name: Optional[str] = None,
        qf_filter: Optional[models.Filter] = None,
    ) -> List[SearchResult]:
        """
        Гибридный поиск в одной коллекции с опциональным Qdrant-фильтром.
        
        Args:
            request: Запрос на поиск
            collection_name: Имя коллекции (default: normative_documents)
            qf_filter: Qdrant Filter для префильтрации
        
        Returns:
            Список результатов поиска
        """
        self.load()
        
        coll = collection_name or config.NORMATIVE_COLLECTION_NAME
        
        logger.info(f"Поиск в '{coll}': '{request.query[:50]}...' k={request.k}")
        
        query_vector = self.embedder.embed_query(request.query)
        
        # Search by pref vector
        pref_hits = self.client.query_points(
            collection_name=coll,
            query=query_vector,
            using="pref",
            limit=request.k * 3,
            with_payload=True,
            with_vectors=False,
            query_filter=qf_filter,
        ).points
        
        # Search by hype vector
        hype_hits = self.client.query_points(
            collection_name=coll,
            query=query_vector,
            using="hype",
            limit=request.k * 3,
            with_payload=True,
            with_vectors=False,
            query_filter=qf_filter,
        ).points
        
        # Search by contextual vector
        contextual_hits = self.client.query_points(
            collection_name=coll,
            query=query_vector,
            using="contextual",
            limit=request.k * 3,
            with_payload=True,
            with_vectors=False,
            query_filter=qf_filter,
        ).points
        
        # BM25 scores
        bm25_scores = self._get_bm25_scores(request.query)
        
        # Combine results
        all_payloads = {}
        pref_scores = {}
        hype_scores = {}
        contextual_scores = {}
        
        for hit in pref_hits:
            pref_scores[hit.id] = hit.score
            all_payloads[hit.id] = hit.payload
        for hit in hype_hits:
            hype_scores[hit.id] = hit.score
            all_payloads[hit.id] = hit.payload
        for hit in contextual_hits:
            contextual_scores[hit.id] = hit.score
            all_payloads[hit.id] = hit.payload
        
        all_ids = set(pref_scores.keys()) | set(hype_scores.keys()) | \
                  set(contextual_scores.keys()) | set(bm25_scores.keys())

        combined_scores = {}
        for pid in all_ids:
            s_pref = pref_scores.get(pid, 0.0)
            s_hype = hype_scores.get(pid, 0.0)
            s_contextual = contextual_scores.get(pid, 0.0)
            s_bm25 = bm25_scores.get(pid, 0.0)
            combined_scores[pid] = (
                request.pref_weight * s_pref +
                request.hype_weight * s_hype +
                request.contextual_weight * s_contextual +
                request.lexical_weight * s_bm25
            )

        # Adaptive BM25 boost: when semantic (pref) scores are weak,
        # shift weight from hype to lexical for better precision.
        p_weight, h_weight, l_weight, c_weight = (
            request.pref_weight, request.hype_weight,
            request.lexical_weight, request.contextual_weight,
        )
        if config.ADAPTIVE_BM25_BOOST and pref_scores:
            max_pref = max(pref_scores.values())
            if max_pref < config.ADAPTIVE_BM25_THRESHOLD:
                logger.info(
                    f"Adaptive BM25: max pref_score={max_pref:.3f} < "
                    f"threshold={config.ADAPTIVE_BM25_THRESHOLD}, "
                    f"boosting lexical weight {l_weight}->{l_weight + 0.2}"
                )
                # Shift 0.2 weight from hype to lexical
                h_weight = max(h_weight - 0.2, 0.0)
                l_weight = min(l_weight + 0.2, 0.6)
                # Recompute with adjusted weights
                combined_scores = {}
                for pid in all_ids:
                    combined_scores[pid] = (
                        p_weight * pref_scores.get(pid, 0.0) +
                        h_weight * hype_scores.get(pid, 0.0) +
                        c_weight * contextual_scores.get(pid, 0.0) +
                        l_weight * bm25_scores.get(pid, 0.0)
                    )
        
        sorted_results = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)[:request.k]
        
        results = []
        for pid, hybrid_score in sorted_results:
            if pid not in all_payloads:
                continue
            payload = all_payloads[pid]
            source = payload.get("source_file", "Неизвестно")
            
            result = SearchResult(
                id=pid,
                content=payload.get("content", "") or payload.get("chunk_content", ""),
                summary=payload.get("summary", "") or payload.get("chunk_summary", ""),
                category=payload.get("category", ""),
                filename=Path(source).stem,
                breadcrumbs=payload.get("breadcrumbs", ""),
                score_hybrid=hybrid_score,
                score_semantic=(0.5 * pref_scores.get(pid, 0.0) +
                               0.35 * hype_scores.get(pid, 0.0) +
                               0.15 * contextual_scores.get(pid, 0.0)),
                score_lexical=bm25_scores.get(pid, 0.0),
                metadata={
                    "chunk_id": payload.get("chunk_id"),
                    "pref_score": pref_scores.get(pid, 0.0),
                    "hype_score": hype_scores.get(pid, 0.0),
                    "contextual_score": contextual_scores.get(pid, 0.0),
                    "bm25_score": bm25_scores.get(pid, 0.0),
                    "document_type": payload.get("document_type", ""),
                    "client_type": payload.get("client_type", ""),
                    "power_range": payload.get("power_range", ""),
                },
                collection_name=payload.get("collection_name", coll),
            )
            results.append(result)
        
        logger.info(f"Найдено {len(results)} результатов в '{coll}'")
        return results
    
    def search_multi(
        self,
        queries: List[str],
        qf_filter: Optional[models.Filter] = None,
        k: int = 10,
        weights: Optional[Dict[str, float]] = None,
    ) -> List[SearchResult]:
        """
        Параллельный поиск по ОБЕИМ коллекциям с мержем результатов.
        
        Args:
            queries: Список поисковых запросов
            qf_filter: Qdrant Filter для префильтрации
            k: Количество результатов (top-k)
            weights: Веса поиска (default from config)
        
        Returns:
            Отсортированный список результатов из обеих коллекций
        """
        self.load()
        
        if weights is None:
            weights = {
                "pref": config.RETRIEVE_PREF_WEIGHT,
                "hype": config.RETRIEVE_HYPE_WEIGHT,
                "lexical": config.RETRIEVE_LEXICAL_WEIGHT,
                "contextual": config.RETRIEVE_CONTEXTUAL_WEIGHT,
            }
        
        request = SearchRequest(
            query=" ".join(queries),  # Combined query for BM25
            k=k,
            pref_weight=weights.get("pref", 0.25),
            hype_weight=weights.get("hype", 0.25),
            lexical_weight=weights.get("lexical", 0.25),
            contextual_weight=weights.get("contextual", 0.25),
        )
        
        # Parallel search across both collections
        all_results = []
        
        def search_collection(coll_name: str) -> List[SearchResult]:
            try:
                return self.search(request, collection_name=coll_name, qf_filter=qf_filter)
            except Exception as e:
                logger.warning(f"⚠️ Ошибка поиска в '{coll_name}': {e}. Продолжаем...")
                return []
        
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = {
                executor.submit(search_collection, coll): coll
                for coll in self.collections
            }
            for future in as_completed(futures):
                coll_name = futures[future]
                try:
                    results = future.result()
                    all_results.extend(results)
                    logger.info(f"[OK] '{coll_name}': {len(results)} результатов")
                except Exception as e:
                    logger.warning(f"⚠️ Ошибка в '{coll_name}': {e}")
        
        # Sort by hybrid score and take top-k
        all_results.sort(key=lambda r: r.score_hybrid, reverse=True)
        return all_results[:k]
    
    def search_multiple(self, queries: List[str], 
                       k_per_query: int = 5,
                       strategy: str = "concat") -> List[SearchResult]:
        """
        Поиск по нескольким запросам (legacy, без фильтров).
        Делегирует к search_multi для совместимости.
        """
        return self.search_multi(queries=queries, k=k_per_query * len(queries))
