"""
Search Agent — агент поиска с Tool Calling
"""
import logging
import uuid
import time
from typing import List, Optional, Dict, Any

import config
from tools.search_tool import SearchTool, SearchRequest, SearchResult
from agents.query_generator import QueryGeneratorAgent, QueryGenerationResult
from utils.timing import timing, timing_context
from utils.agent_logger import log_agent_response

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
        session_logger: Optional[Any] = None
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

        # 1. Генерация поисковых запросов с учётом рекомендаций
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

        # 2. Проверка необходимости уточнения
        if self.query_generator.needs_clarification(gen_result):
            logger.info("Требуется уточнение")
            result = {
                "clarification_needed": True,
                "clarification_questions": gen_result.clarification_questions,
                "results": [],
                "queries_used": [],
                "search_params": gen_result.search_params,
                "confidence": gen_result.confidence,
                "reasoning": gen_result.reasoning
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
                    "search_params": gen_result.search_params,
                    "confidence": gen_result.confidence,
                    "reasoning": gen_result.reasoning,
                    "clarification_needed": True,
                    "clarification_questions": gen_result.clarification_questions
                },
                timing_info={"total_time": time.time() - _start_time}
            )
            return result

        # 3. Выполнение поиска
        queries = self.query_generator.get_queries_text(gen_result)
        strategy = gen_result.search_params.get("strategy", "concat")
        k_per_query = gen_result.search_params.get("k", 10)

        logger.info(f"Поиск по запросам: {queries}, стратегия: {strategy}")

        with timing_context("SearchAgent.tool_search"):
            results = self.search_tool.search_multiple(
                queries=queries,
                k_per_query=k_per_query // len(queries) if strategy == "separate" else k_per_query,
                strategy=strategy
            )

        # 4. Оценка качества результатов
        confidence = gen_result.confidence
        if len(results) < 3:
            logger.warning(f"Мало результатов: {len(results)}")
            confidence *= 0.7

        # 5. Автоматическая повторная попытка если нужно
        if auto_retry and len(results) < 3 and max_retries > 0:
            logger.info(f"Попытка {max_retries}: повторный поиск с другими параметрами")
            retry_result = self._retry_search(
                user_query=user_query,
                original_queries=queries,
                max_retries=max_retries - 1
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
            "search_params": gen_result.search_params,
            "confidence": confidence,
            "reasoning": gen_result.reasoning
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
                    }
                    for r in results[:10]
                ],
                "queries_used": queries,
                "search_params": gen_result.search_params,
                "confidence": confidence,
                "reasoning": gen_result.reasoning
            },
            timing_info={"total_time": time.time() - _start_time}
        )

        return result

    def _retry_search(
        self,
        user_query: str,
        original_queries: List[str],
        max_retries: int
    ) -> Dict[str, Any]:
        """Повторный поиск с изменёнными параметрами."""
        # Попытка с увеличенным k и изменёнными весами
        retry_params = {
            "k": 15,
            "pref_weight": 0.3,
            "hype_weight": 0.3,
            "lexical_weight": 0.3,
            "contextual_weight": 0.1,
            "strategy": "separate"
        }
        
        request = SearchRequest(
            query=" ".join(original_queries),
            k=retry_params["k"],
            pref_weight=retry_params["pref_weight"],
            hype_weight=retry_params["hype_weight"],
            lexical_weight=retry_params["lexical_weight"],
            contextual_weight=retry_params["contextual_weight"]
        )
        
        results = self.search_tool.search(request)
        
        return {
            "results": results,
            "queries_used": original_queries,
            "search_params": retry_params
        }
    
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
