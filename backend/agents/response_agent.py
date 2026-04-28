"""
Response Agent — агент формирования ответов
"""
import logging
import json
import re
from typing import List, Optional, Dict, Any

from openai import OpenAI
import config
from prompts.synthesis_prompt import get_synthesis_prompt
from tools.search_tool import SearchResult
from agents.search_agent import SearchAgent
from utils.timing import timing, timing_context
from utils.agent_logger import log_agent_response

logger = logging.getLogger(__name__)


def fix_latex_in_text(text: str) -> str:
    """
    Конвертирует формулы из (C_1) в \(C_1\) для правильного рендеринга.

    Обрабатывает:
    - (C_{1.1}) → \(C_{1.1}\)
    - (C_1) → \(C_1\)
    - (P_{\text{...}}) → \(P_{\text{...}}\)
    """
    if not text:
        return text

    # Паттерн для сложных формул с индексами: (C_{1.1}), (P_{\text{...}})
    result = re.sub(r'\(([A-Za-z]_\{[^}]+\})\)', r'\\(\1\\)', text)

    # Паттерн для простых индексов: (C_1), (P_max)
    result = re.sub(r'\(([A-Za-z]_[A-Za-z0-9]+)\)', r'\\(\1\\)', result)

    return result


def filter_technical_phrases(text: str) -> str:
    """
    Удаляет технические фразы и внутренние рассуждения модели из ответа.

    Обрабатывает:
    - Фразы о поиске: "Let's search", "We need to call search", "Searching for"
    - Технические комментарии: "Поиск завершен", "Я нашел информацию"
    - Пустые строки в начале ответа
    """
    if not text:
        return text

    lines = text.split('\n')
    filtered_lines = []

    # Паттерны для фильтрации технических фраз
    technical_patterns = [
        r"^Let's\s+(search|do\s+search|call|use|find)",
        r"^We\s+need\s+to\s+(search|call|find|use)",
        r"^Searching\s+for",
        r"^Search\s+completed",
        r"^Поиск\s+завершен",
        r"^Я\s+нашел\s+информацию",
        r"^Вызываю\s+инструмент",
        r"^Использую\s+поиск",
        r"^Сначала\s+найду",
        r"^Теперь\s+поищу",
    ]

    skip_until_content = True

    for line in lines:
        stripped = line.strip()

        # Пропускаем пустые строки в начале
        if skip_until_content and not stripped:
            continue

        # Проверяем на технические фразы
        is_technical = False
        for pattern in technical_patterns:
            if re.search(pattern, stripped, re.IGNORECASE):
                is_technical = True
                break

        if not is_technical:
            filtered_lines.append(line)
            skip_until_content = False

    return '\n'.join(filtered_lines)


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
        user_hints: Optional[Dict[str, Any]] = None,
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

        # Системный промпт для синтеза ответа (не для поиска!)
        system_prompt = get_synthesis_prompt()

        # Пользовательский промпт
        with timing_context("ResponseAgent.create_prompt"):
            user_prompt = self._create_user_prompt(
                user_query=user_query,
                context=context,
                history=history_context,
                user_hints=user_hints
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
                        
                        if response and hasattr(response, 'choices') and response.choices:
                            break
                        
                        logger.warning(f"Attempt {attempt + 1}: Empty response or choices")
                        if attempt < max_retries - 1:
                            time.sleep(base_delay * (attempt + 1))
                            continue
                        raise ValueError("Empty response from LLM")

                    except Exception as e:
                        if attempt == max_retries - 1:
                            raise
                        logger.warning(f"Attempt {attempt + 1} failed: {e}")
                        time.sleep(base_delay * (attempt + 1))

            if not response or not response.choices:
                raise ValueError("Failed to get response after retries")

            answer = response.choices[0].message.content or ""

            # Логирование частичного ответа (первые 200 символов)
            logger.info(f"LLM answer preview: {answer[:200]}...")

            # Фильтрация технических фраз
            answer = filter_technical_phrases(answer)
            logger.info(f"Filtered answer preview: {answer[:200]}...")

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
            # Исправляем LaTeX формулы в контенте источника
            fixed_content = fix_latex_in_text(result.content)
            
            part = (
                f"[src_{i}]\n"
                f"Файл: {result.filename}\n"
                f"Раздел: {result.breadcrumbs}\n"
                f"Категория: {result.category if result.category else 'не указана'}\n"
                f"Текст:\n{fixed_content}\n"
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
        history: str,
        user_hints: Optional[Dict[str, Any]] = None
    ) -> str:
        """Создание пользовательского промпта."""
        brevity_instruction = ""
        if user_hints and (user_hints.get("max_tokens", 2000) < 1000 or user_hints.get("length") == "short"):
            brevity_instruction = "\nВАЖНО: Отвечай максимально КРАТКО и по существу. Уложись в 1-2 абзаца.\n"

        return f"""
{history}

{context}

---
Вопрос пользователя: {user_query}
{brevity_instruction}
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
