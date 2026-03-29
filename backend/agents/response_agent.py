"""
Response Agent — агент формирования ответов
"""
import logging
import json
from typing import List, Optional, Dict, Any

from openai import OpenAI
import config
from prompts.system_prompt import get_system_prompt
from tools.search_tool import SearchResult
from agents.search_agent import SearchAgent
from utils.timing import timing, timing_context
from utils.agent_logger import log_agent_response

logger = logging.getLogger(__name__)


class ResponseAgent:
    """
    Агент для формирования ответов на основе результатов поиска.
    
    Использует LLM для:
    - Генерации ответа на основе найденной информации
    - Цитирования источников
    - Поддержки контекста диалога
    - Дружелюбного стиля общения
    """
    
    def __init__(self):
        self.client = OpenAI(
            api_key=config.ROUTERAI_API_KEY,
            base_url=config.ROUTERAI_BASE_URL
        )
        self.model = config.DEFAULT_LLM_MODEL
        logger.info(f"ResponseAgent инициализирован: {self.model}")
    
    @timing("ResponseAgent.generate_response")
    def generate_response(
        self,
        user_query: str,
        search_results: List[SearchResult],
        history: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2000,
        query_id: Optional[str] = None,
        session_id: Optional[str] = None,
        session_logger: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Генерация ответа.

        Args:
            user_query: Вопрос пользователя
            search_results: Результаты поиска
            history: История диалога
            temperature: Температура генерации
            max_tokens: Максимум токенов
            query_id: Уникальный ID запроса (для логирования)
            session_id: ID сессии (для логирования)

        Returns:
            Словарь с ответом:
            - answer: текст ответа
            - sources: список источников
            - confidence: уверенность
        """
        import uuid
        import time
        
        _query_id = query_id or str(uuid.uuid4())
        _session_id = session_id or "unknown"
        _start_time = time.time()
        
        # Формирование контекста из результатов поиска
        with timing_context("ResponseAgent.format_context"):
            context = self._format_context(search_results)

        # Формирование истории диалога
        history_context = self._format_history(history)

        # Системный промпт
        system_prompt = get_system_prompt()

        # Пользовательский промпт
        with timing_context("ResponseAgent.create_prompt"):
            user_prompt = self._create_user_prompt(
                user_query=user_query,
                context=context,
                history=history_context
            )

        logger.info(f"Генерация ответа для '{user_query[:50]}...'")

        try:
            with timing_context("ResponseAgent.llm_completion"):
                # Retry-логика для обработки 502 ошибок провайдера
                max_retries = 3
                base_delay = 2  # секунды
                
                for attempt in range(max_retries):
                    try:
                        response = self.client.chat.completions.create(
                            model=self.model,
                            messages=[
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": user_prompt}
                            ],
                            temperature=temperature,
                            max_tokens=max_tokens
                        )
                        
                        # Логирование полного ответа от провайдера
                        logger.info(f"LLM raw response: id={getattr(response, 'id', 'N/A')}, "
                                   f"choices={getattr(response, 'choices', None)}, "
                                   f"model={getattr(response, 'model', 'N/A')}")
                        
                        # Проверка на валидность ответа
                        if not response.choices:
                            # Проверяем, есть ли ошибка от провайдера
                            error_info = getattr(response, 'error', {})
                            if error_info:
                                logger.warning(f"Attempt {attempt + 1}/{max_retries}: Provider error - {error_info}")
                                
                                # Если это 502/503 ошибка и это не последняя попытка — retry
                                if attempt < max_retries - 1:
                                    delay = base_delay * (2 ** attempt)  # Экспоненциальная задержка
                                    logger.info(f"Retrying in {delay}s... (attempt {attempt + 2}/{max_retries})")
                                    time.sleep(delay)
                                    continue
                            
                            # Логируем всю структуру ответа для отладки
                            try:
                                response_dict = {
                                    "id": getattr(response, "id", None),
                                    "choices": getattr(response, "choices", None),
                                    "created": getattr(response, "created", None),
                                    "model": getattr(response, "model", None),
                                    "system_fingerprint": getattr(response, "system_fingerprint", None),
                                    "object": getattr(response, "object", None),
                                    "usage": {
                                        "prompt_tokens": getattr(getattr(response, "usage", None), "prompt_tokens", None),
                                        "completion_tokens": getattr(getattr(response, "usage", None), "completion_tokens", None),
                                        "total_tokens": getattr(getattr(response, "usage", None), "total_tokens", None),
                                    } if getattr(response, "usage", None) else None,
                                    "error": error_info
                                }
                                logger.error(f"LLM empty choices structure: {json.dumps(response_dict, indent=2, default=str)}")
                            except Exception as e:
                                logger.error(f"Failed to serialize response: {e}")
                            
                            raise ValueError(f"LLM returned empty choices: {response}")
                        
                        # Успешный ответ — выходим из цикла retry
                        break
                        
                    except Exception as e:
                        # Если это последняя попытка — пробрасываем ошибку дальше
                        if attempt == max_retries - 1:
                            raise
                        
                        # Логирование ошибки и retry
                        logger.warning(f"Attempt {attempt + 1}/{max_retries} failed: {e}")
                        delay = base_delay * (2 ** attempt)
                        logger.info(f"Retrying in {delay}s... (attempt {attempt + 2}/{max_retries})")
                        time.sleep(delay)

            answer = response.choices[0].message.content
            
            # Логирование частичного ответа (первые 200 символов)
            logger.info(f"LLM answer preview: {answer[:200]}...")

            # Извлечение источников с перемаппингом индексов
            with timing_context("ResponseAgent.extract_sources"):
                sources, updated_answer = self._extract_sources(search_results, answer)

            logger.info(f"Ответ сгенерирован: {len(updated_answer)} символов, источников: {len(sources)}")

            response_data = {
                "answer": updated_answer,
                "sources": sources,
                "confidence": 0.8 if search_results else 0.3,
                "context_used": context
            }
            
            # Логирование в session_logger если есть
            if session_logger:
                session_logger.set_final_answer(updated_answer, len(sources))

            # Логирование ответа
            timing_info = {"total_time": time.time() - _start_time}
            log_agent_response(
                query_id=_query_id,
                session_id=_session_id,
                user_query=user_query,
                response_data=response_data,
                timing_info=timing_info
            )

            return response_data

        except Exception as e:
            logger.error(f"Ошибка генерации ответа: {e}")
            return {
                "answer": "Произошла ошибка при генерации ответа. Пожалуйста, попробуйте ещё раз.",
                "sources": [],
                "confidence": 0.0,
                "context_used": ""
            }
    
    def _format_context(self, results: List[SearchResult]) -> str:
        """Форматирование контекста из результатов поиска."""
        if not results:
            return "Контекст: информация не найдена."

        parts = []
        for i, result in enumerate(results[:10], 1):
            part = (
                f"[src_{i}]\n"
                f"Файл: {result.filename}\n"
                f"Раздел: {result.breadcrumbs}\n"
                f"Категория: {result.category if result.category else 'не указана'}\n"
                f"Текст:\n{result.content}\n"
            )
            parts.append(part)

        return "\n---\n".join(parts)
    
    def _format_history(self, history: str) -> str:
        """Форматирование истории диалога."""
        if not history:
            return "История диалога: это первый вопрос."
        return f"История диалога:\n{history}"
    
    def _create_user_prompt(
        self,
        user_query: str,
        context: str,
        history: str
    ) -> str:
        """Создание пользовательского промпта."""
        return f"""
{history}

{context}

---
Вопрос пользователя: {user_query}

Используя приведённую выше информацию из базы знаний, дай точный и развёрнутый ответ на вопрос.

ВАЖНО: При ссылке на источник используй ТОЛЬКО цифру в квадратных скобках:
- ✅ ПРАВИЛЬНО: [1], [2], [3], [1][3]
- ❌ НЕПРАВИЛЬНО: "источник 1", "источник [1]", "[src_1]"

Пример: "согласно документу [1] и инструкции [2][3]..."

Если информации недостаточно, честно скажи об этом.
"""
    
    def _extract_sources(self, results: List[SearchResult], answer_text: str = "") -> tuple[List[Dict[str, Any]], str]:
        """
        Извлечение информации об источниках.

        Возвращает только те источники, на которые модель ссылается в ответе.
        Источники сортируются по количеству цитирований и важности.

        Args:
            results: Результаты поиска
            answer_text: Текст ответа (для подсчёта упоминаний)

        Returns:
            Кортеж (список источников, обновлённый текст ответа с перемапленными индексами)
        """
        if not results:
            return [], answer_text

        sources = []
        citation_counts = {}  # {source_index: count}

        # 1. Подсчитываем упоминания каждого источника в ответе
        if answer_text:
            import re
            # Находим все упоминания вида [1], [2], [1][3], и т.д.
            mentions = re.findall(r'\[(\d+)\]', answer_text)
            for idx_str in mentions:
                idx = int(idx_str) - 1  # Конвертируем в 0-based индекс
                citation_counts[idx] = citation_counts.get(idx, 0) + 1

        # 2. Создаём источники с метаданными (сохраняем original_rank для перемаппинга)
        for i, result in enumerate(results[:10]):
            source = {
                "id": result.id,
                "filename": result.filename,
                "breadcrumbs": result.breadcrumbs,
                "category": result.category,
                "summary": result.summary,
                "content": result.content,
                "chunk_id": result.metadata.get("chunk_id", ""),
                "score_hybrid": result.score_hybrid,
                "score_semantic": result.score_semantic,
                "score_lexical": result.score_lexical,
                # Добавляем метрики для ранжирования
                "citation_count": citation_counts.get(i, 0),
                "original_rank": i,  # Позиция в исходном поиске (0-based)
            }
            sources.append(source)

        # 3. Если LLM не создал ссылки [1], [2] — возвращаем первые 5 результатов
        if not citation_counts:
            final_sources = []
            for source in sources[:5]:
                final_source = {
                    "id": source["id"],
                    "filename": source["filename"],
                    "breadcrumbs": source["breadcrumbs"],
                    "category": source["category"],
                    "summary": source["summary"],
                    "content": source["content"],
                    "chunk_id": source["chunk_id"],
                    "score_hybrid": source["score_hybrid"],
                    "score_semantic": source["score_semantic"],
                    "score_lexical": source["score_lexical"],
                }
                final_sources.append(final_source)
            return final_sources, answer_text

        # 4. Отбираем только те источники, на которые есть ссылки в ответе
        cited_sources = [s for s in sources if s["citation_count"] > 0]

        # 5. Сортируем цитируемые источники по комбинированному рейтингу
        def compute_ranking_score(source):
            """
            Вычисляет рейтинг источника.
            Формула: citation_count × 0.5 + score_hybrid × 0.5
            """
            citation_score = min(source["citation_count"], 5) * 0.5  # Максимум 2.5
            importance_score = source["score_hybrid"]
            return citation_score + importance_score * 0.5

        cited_sources.sort(key=lambda x: compute_ranking_score(x), reverse=True)

        # 6. Создаём маппинг: old_index (1-based) → new_index (1-based)
        index_mapping = {}
        for new_idx, source in enumerate(cited_sources):
            old_idx = source["original_rank"] + 1  # Конвертируем в 1-based
            new_idx = new_idx + 1  # Конвертируем в 1-based
            index_mapping[old_idx] = new_idx

        # 7. Перемапливаем индексы в ответе
        updated_answer = answer_text
        if answer_text and index_mapping:
            import re

            def replace_index(match):
                old_num = int(match.group(1))
                new_num = index_mapping.get(old_num, old_num)
                return f"[{new_num}]"

            updated_answer = re.sub(r'\[(\d+)\]', replace_index, answer_text)

        # 8. Возвращаем только цитируемые источники
        final_sources = []
        for source in cited_sources:
            final_source = {
                "id": source["id"],
                "filename": source["filename"],
                "breadcrumbs": source["breadcrumbs"],
                "category": source["category"],
                "summary": source["summary"],
                "content": source["content"],
                "chunk_id": source["chunk_id"],
                "score_hybrid": source["score_hybrid"],
                "score_semantic": source["score_semantic"],
                "score_lexical": source["score_lexical"],
            }
            final_sources.append(final_source)

        return final_sources, updated_answer
    
    def generate_clarification_response(
        self,
        user_query: str,
        clarification_questions: List[str]
    ) -> str:
        """
        Генерация ответа с уточняющими вопросами.
        
        Args:
            user_query: Исходный вопрос
            clarification_questions: Список уточняющих вопросов
        
        Returns:
            Текст ответа
        """
        if not clarification_questions:
            return ""
        
        # Формирование дружелюбного сообщения
        intro = "Здравствуйте! "
        
        if len(clarification_questions) == 1:
            return f"{intro}Чтобы я мог точно ответить на ваш вопрос, уточните, пожалуйста: {clarification_questions[0]}"
        
        message = f"{intro}Чтобы я мог точно ответить на ваш вопрос «{user_query}», мне нужно немного уточнить:\n\n"
        for i, q in enumerate(clarification_questions, 1):
            message += f"{i}. {q}\n"
        
        message += "\nПожалуйста, ответьте на эти вопросы, и я с радостью помогу вам!"
        return message
