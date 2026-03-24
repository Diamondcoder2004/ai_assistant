"""
Response Agent — агент формирования ответов
"""
import logging
from typing import List, Optional, Dict, Any

from openai import OpenAI
import config
from prompts.system_prompt import get_system_prompt
from tools.search_tool import SearchResult
from agents.search_agent import SearchAgent

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
    
    def generate_response(
        self,
        user_query: str,
        search_results: List[SearchResult],
        history: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> Dict[str, Any]:
        """
        Генерация ответа.
        
        Args:
            user_query: Вопрос пользователя
            search_results: Результаты поиска
            history: История диалога
            temperature: Температура генерации
            max_tokens: Максимум токенов
        
        Returns:
            Словарь с ответом:
            - answer: текст ответа
            - sources: список источников
            - confidence: уверенность
        """
        # Формирование контекста из результатов поиска
        context = self._format_context(search_results)
        
        # Формирование истории диалога
        history_context = self._format_history(history)
        
        # Системный промпт
        system_prompt = get_system_prompt()
        
        # Пользовательский промпт
        user_prompt = self._create_user_prompt(
            user_query=user_query,
            context=context,
            history=history_context
        )
        
        logger.info(f"Генерация ответа для '{user_query[:50]}...'")
        
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
            
            answer = response.choices[0].message.content
            
            # Извлечение источников из ответа
            sources = self._extract_sources(search_results)
            
            logger.info(f"Ответ сгенерирован: {len(answer)} символов")
            
            return {
                "answer": answer,
                "sources": sources,
                "confidence": 0.8 if search_results else 0.3,
                "context_used": context
            }
            
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
    
    def _extract_sources(self, results: List[SearchResult]) -> List[Dict[str, Any]]:
        """Извлечение информации об источниках."""
        sources = []
        for result in results[:5]:
            sources.append({
                "id": result.id,
                "filename": result.filename,
                "breadcrumbs": result.breadcrumbs,
                "category": result.category,
                "summary": result.summary,
                "content": result.content,
                "chunk_id": result.metadata.get("chunk_id", ""),
                "score_hybrid": result.score_hybrid,
                "score_semantic": result.score_semantic,
                "score_lexical": result.score_lexical
            })
        return sources
    
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
