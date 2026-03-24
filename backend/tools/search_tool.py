"""
Search Tool — инструмент поиска в базе знаний
"""
import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from pathlib import Path

from qdrant_client import QdrantClient
import numpy as np
import pymorphy3

import config
from utils.router_embedding import get_routerai_embedder

logger = logging.getLogger(__name__)

# Синглтон для MorphAnalyzer (избегаем повторной инициализации)
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
    pref_weight: float = 0.4
    hype_weight: float = 0.3
    lexical_weight: float = 0.2
    contextual_weight: float = 0.1


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


class SearchTool:
    """
    Инструмент поиска в базе знаний с гибридным поиском.
    
    Поддерживает 4 компонента:
    - pref: семантический вектор (summary + content)
    - hype: семантический вектор (hypothetical questions)
    - lexical: BM25 (токенизированный текст)
    - contextual: семантический вектор (соседние чанки)
    """
    
    def __init__(self):
        self.client = QdrantClient(host=config.QDRANT_HOST, port=config.QDRANT_PORT)
        self.embedder = get_routerai_embedder()
        self.bm25 = None
        self.documents = []
        self.point_ids = []
        self.payloads = {}
        self._loaded = False
        
    def load(self, force: bool = False):
        """Загрузка документов для BM25."""
        if self._loaded and not force:
            return
        
        logger.info("Загрузка документов для поиска...")
        scroll_result = self.client.scroll(
            collection_name=config.COLLECTION_NAME,
            with_payload=True,
            with_vectors=False,
            limit=10000
        )
        
        self.documents = []
        self.point_ids = []
        self.payloads = {}
        
        points, next_page = scroll_result
        while points:
            for point in points:
                payload = point.payload
                content = payload.get("content", "") or payload.get("text", "")
                self.documents.append(self._tokenize_text(content))
                self.point_ids.append(point.id)
                self.payloads[point.id] = payload
            
            if next_page is None:
                break
            scroll_result = self.client.scroll(
                collection_name=config.COLLECTION_NAME,
                with_payload=True,
                with_vectors=False,
                offset=next_page.offset,
                limit=10000
            )
            points, next_page = scroll_result
        
        # BM25 будет загружен при первом запросе
        self._loaded = True
        logger.info(f"Загружено {len(self.documents)} документов")
    
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
        """Получение BM25 оценок."""
        from rank_bm25 import BM25Plus

        query_tokens = self._tokenize_text(query)
        bm25 = BM25Plus(self.documents)
        scores = bm25.get_scores(query_tokens)

        # Нормализация через tanh с меньшим делителем (строже)
        # Делитель 15 вместо 5 даёт более широкий диапазон оценок
        normalized = {}
        for idx, score in enumerate(scores):
            point_id = self.point_ids[idx]
            normalized[point_id] = float(np.tanh(score / 15.0))

        return normalized
    
    def search(self, request: SearchRequest) -> List[SearchResult]:
        """
        Гибридный поиск.
        
        Args:
            request: Запрос на поиск
        
        Returns:
            Список результатов поиска
        """
        self.load()
        
        logger.info(f"Поиск: '{request.query[:50]}...' k={request.k}")
        
        # 1. Векторный поиск
        query_vector = self.embedder.embed_query(request.query)
        
        # Поиск по pref
        pref_hits = self.client.query_points(
            collection_name=config.COLLECTION_NAME,
            query=query_vector,
            using="pref",
            limit=request.k * 3,
            with_payload=True,
            with_vectors=False,
        ).points
        
        # Поиск по hype
        hype_hits = self.client.query_points(
            collection_name=config.COLLECTION_NAME,
            query=query_vector,
            using="hype",
            limit=request.k * 3,
            with_payload=True,
            with_vectors=False,
        ).points
        
        # Поиск по contextual
        contextual_hits = self.client.query_points(
            collection_name=config.COLLECTION_NAME,
            query=query_vector,
            using="contextual",
            limit=request.k * 3,
            with_payload=True,
            with_vectors=False,
        ).points
        
        # 2. BM25 поиск
        bm25_scores = self._get_bm25_scores(request.query)
        
        # 3. Сбор всех результатов
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
        
        # 4. Гибридная оценка
        all_ids = set(pref_scores.keys()) | set(hype_scores.keys()) | \
                  set(contextual_scores.keys()) | set(bm25_scores.keys())

        # Min-max scaling для BM25 перед softmax
        bm25_values = list(bm25_scores.values()) if bm25_scores else [0]
        bm25_min = min(bm25_values)
        bm25_max = max(bm25_values)
        bm25_range = bm25_max - bm25_min if bm25_max > bm25_min else 1.0

        # Softmax с temperature=2 для BM25
        temperature = 2.0
        bm25_scaled = {}
        exp_scores = {}
        for pid in all_ids:
            raw_score = bm25_scores.get(pid, 0.0)
            # Min-max scaling [0, 1]
            normalized = (raw_score - bm25_min) / bm25_range
            # Применяем temperature и экспоненту для softmax
            exp_scores[pid] = np.exp(normalized / temperature)

        # Softmax нормализация
        exp_sum = sum(exp_scores.values()) if exp_scores else 1.0
        for pid in all_ids:
            bm25_scaled[pid] = exp_scores[pid] / exp_sum if exp_sum > 0 else 0.0

        combined_scores = {}
        for pid in all_ids:
            s_pref = pref_scores.get(pid, 0.0)
            s_hype = hype_scores.get(pid, 0.0)
            s_contextual = contextual_scores.get(pid, 0.0)
            s_bm25 = bm25_scaled.get(pid, 0.0)

            combined_scores[pid] = (
                request.pref_weight * s_pref +
                request.hype_weight * s_hype +
                request.contextual_weight * s_contextual +
                request.lexical_weight * s_bm25
            )
        
        # 5. Сортировка и выбор топ-k
        sorted_results = sorted(
            combined_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:request.k]
        
        # 6. Формирование результатов
        results = []
        for pid, hybrid_score in sorted_results:
            if pid not in all_payloads:
                continue
            
            payload = all_payloads[pid]
            source = payload.get("source_file", "Неизвестно")
            
            result = SearchResult(
                id=pid,
                content=payload.get("content", "") or payload.get("text", ""),
                summary=payload.get("summary", ""),
                category=payload.get("category", ""),
                filename=Path(source).stem,
                breadcrumbs=payload.get("breadcrumbs", ""),
                score_hybrid=hybrid_score,
                # Взвешенное среднее для семантической оценки (pref > hype > contextual)
                score_semantic=(0.5 * pref_scores.get(pid, 0.0) +
                               0.35 * hype_scores.get(pid, 0.0) +
                               0.15 * contextual_scores.get(pid, 0.0)),
                # Нормализованный BM25 (после min-max scaling)
                score_lexical=(bm25_scores.get(pid, 0.0) - bm25_min) / bm25_range if bm25_range > 0 else 0.0,
                metadata={
                    "chunk_id": payload.get("chunk_id"),
                    "pref_score": pref_scores.get(pid, 0.0),
                    "hype_score": hype_scores.get(pid, 0.0),
                    "contextual_score": contextual_scores.get(pid, 0.0),
                    "bm25_score": bm25_scores.get(pid, 0.0),
                    "bm25_scaled": bm25_scaled.get(pid, 0.0),
                }
            )
            results.append(result)
        
        logger.info(f"Найдено {len(results)} результатов")
        return results
    
    def search_multiple(self, queries: List[str], 
                       k_per_query: int = 5,
                       strategy: str = "concat") -> List[SearchResult]:
        """
        Поиск по нескольким запросам.
        
        Args:
            queries: Список запросов
            k_per_query: Количество результатов на запрос
            strategy: "concat" или "separate"
        
        Returns:
            Список результатов
        """
        if strategy == "concat":
            # Конкатенация запросов
            combined_query = " ".join(queries)
            request = SearchRequest(query=combined_query, k=k_per_query * len(queries))
            return self.search(request)
        else:
            # Раздельный поиск
            all_results = []
            seen_ids = set()
            
            for query in queries:
                request = SearchRequest(query=query, k=k_per_query)
                results = self.search(request)
                
                for result in results:
                    if result.id not in seen_ids:
                        seen_ids.add(result.id)
                        all_results.append(result)
            
            # Сортировка по hybrid score
            all_results.sort(key=lambda x: x.score_hybrid, reverse=True)
            return all_results[:k_per_query * len(queries)]
