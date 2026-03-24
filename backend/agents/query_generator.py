"""
Query Generator Agent — генерация поисковых запросов
"""
import logging
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from openai import OpenAI
import config
from prompts.query_generation import get_query_generation_prompt
from utils.timing import timing

logger = logging.getLogger(__name__)


@dataclass
class QueryGenerationResult:
    """Результат генерации запросов."""
    clarification_needed: bool
    clarification_questions: List[str]
    queries: List[Dict[str, str]]
    search_params: Dict[str, Any]
    confidence: float
    reasoning: str
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "QueryGenerationResult":
        """Создание из словаря."""
        return cls(
            clarification_needed=data.get("clarification_needed", False),
            clarification_questions=data.get("clarification_questions", []),
            queries=data.get("queries", []),
            search_params=data.get("search_params", {}),
            confidence=data.get("confidence", 0.5),
            reasoning=data.get("reasoning", "")
        )


class QueryGeneratorAgent:
    """
    Агент для генерации поисковых запросов.
    
    Использует LLM для:
    - Переформулирования пользовательских запросов
    - Генерации 2-3 поисковых запросов
    - Подбора параметров поиска (веса, k)
    - Определения необходимости уточняющих вопросов
    """
    
    def __init__(self):
        self.client = OpenAI(
            api_key=config.ROUTERAI_API_KEY,
            base_url=config.ROUTERAI_BASE_URL
        )
        self.model = config.DEFAULT_LLM_MODEL
        logger.info(f"QueryGeneratorAgent инициализирован: {self.model}")
    
    @timing("QueryGenerator.generate")
    def generate(
        self,
        user_query: str,
        history: str = "",
        category: str = "не известна",
        temperature: float = 0.7,
        max_attempts: int = 3,
        user_hints: Optional[Dict[str, Any]] = None
    ) -> QueryGenerationResult:
        """
        Генерация поисковых запросов.

        Args:
            user_query: Вопрос пользователя
            history: История диалога
            category: Категория клиента
            temperature: Температура генерации
            max_attempts: Максимальное количество попыток
            user_hints: Рекомендации от пользователя (k, temperature, и т.д.)

        Returns:
            Результат генерации запросов
        """
        prompt = get_query_generation_prompt(
            user_query=user_query,
            history=history,
            category=category,
            user_hints=user_hints  # Передаём рекомендации
        )

        logger.info(f"Генерация запросов для: '{user_query[:50]}...'")
        if user_hints:
            logger.info(f"Рекомендации от пользователя: {user_hints}")
        
        for attempt in range(max_attempts):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "Ты эксперт по генерации поисковых запросов. Отвечай ТОЛЬКО в формате JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=temperature,
                    max_tokens=1500,
                    response_format={"type": "json_object"}
                )
                
                result_text = response.choices[0].message.content
                
                # Парсинг JSON
                result_data = json.loads(result_text)
                
                # Валидация
                if "queries" not in result_data and not result_data.get("clarification_needed"):
                    logger.warning(f"Попытка {attempt + 1}: Неверный формат ответа")
                    continue
                
                # Если queries пустой — создаем дефолтный запрос
                if not result_data.get("queries") and not result_data.get("clarification_needed"):
                    result_data["queries"] = [{"text": user_query, "reason": "дефолтный запрос"}]
                    result_data["search_params"] = {
                        "k": 10,
                        "pref_weight": config.RETRIEVE_PREF_WEIGHT,
                        "hype_weight": config.RETRIEVE_HYPE_WEIGHT,
                        "lexical_weight": config.RETRIEVE_LEXICAL_WEIGHT,
                        "contextual_weight": config.RETRIEVE_CONTEXTUAL_WEIGHT,
                        "strategy": "concat"
                    }
                    result_data["confidence"] = 0.5
                    result_data["reasoning"] = "Использован дефолтный запрос"

                logger.info(f"Генерация успешна с попытки {attempt + 1}")
                return QueryGenerationResult.from_dict(result_data)
                
            except json.JSONDecodeError as e:
                logger.warning(f"Попытка {attempt + 1}: Ошибка парсинга JSON: {e}")
                if attempt == max_attempts - 1:
                    # Возврат дефолтного результата
                    return self._default_result(user_query)
            except Exception as e:
                logger.error(f"Попытка {attempt + 1}: Ошибка генерации: {e}")
                if attempt == max_attempts - 1:
                    return self._default_result(user_query)
        
        return self._default_result(user_query)
    
    def _default_result(self, user_query: str) -> QueryGenerationResult:
        """Возвращает дефолтный результат при ошибке."""
        return QueryGenerationResult(
            clarification_needed=False,
            clarification_questions=[],
            queries=[{"text": user_query, "reason": "дефолтный запрос"}],
            search_params={
                "k": 10,
                "pref_weight": config.RETRIEVE_PREF_WEIGHT,
                "hype_weight": config.RETRIEVE_HYPE_WEIGHT,
                "lexical_weight": config.RETRIEVE_LEXICAL_WEIGHT,
                "contextual_weight": config.RETRIEVE_CONTEXTUAL_WEIGHT,
                "strategy": "separate"
            },
            confidence=0.5,
            reasoning="Использован дефолтный запрос из-за ошибки генерации"
        )
    
    def needs_clarification(self, result: QueryGenerationResult) -> bool:
        """Проверка необходимости уточнения."""
        return result.clarification_needed and len(result.clarification_questions) > 0
    
    def get_queries_text(self, result: QueryGenerationResult) -> List[str]:
        """Получение списка текстов запросов."""
        return [q["text"] for q in result.queries]
    
    def format_clarification_message(self, result: QueryGenerationResult) -> str:
        """Форматирование сообщения с уточняющими вопросами."""
        if not result.clarification_questions:
            return ""
        
        questions = result.clarification_questions
        if len(questions) == 1:
            return questions[0]
        
        message = "Чтобы я мог точнее ответить, уточните, пожалуйста:\n"
        for i, q in enumerate(questions, 1):
            message += f"{i}. {q}\n"
        return message
