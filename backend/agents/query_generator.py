"""
Query Generator Agent — генерация поисковых запросов
"""
import logging
import json
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from openai import OpenAI
import config
from prompts.query_generation import get_query_generation_prompt
from utils.timing import timing
from utils.agent_logger import log_agent_response

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
        user_hints: Optional[Dict[str, Any]] = None,
        query_id: Optional[str] = None,
        session_id: Optional[str] = None
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
            query_id: Уникальный ID запроса (для логирования)
            session_id: ID сессии (для логирования)

        Returns:
            Результат генерации запросов
        """
        import uuid
        
        _query_id = query_id or str(uuid.uuid4())
        _session_id = session_id or "unknown"
        _start_time = time.time()
        
        prompt = get_query_generation_prompt(
            user_query=user_query,
            history=history,
            category=category,
            user_hints=user_hints  # Передаём рекомендации
        )

        logger.info(f"Генерация запросов для: '{user_query[:50]}...'")
        if user_hints:
            logger.info(f"Рекомендации от пользователя: {user_hints}")

        # Retry-логика для обработки 502 ошибок провайдера
        max_retries = 3
        base_delay = 2  # секунды

        for attempt in range(max_attempts):
            try:
                # Внутренний retry для LLM вызова
                for retry in range(max_retries):
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
                        
                        # Логирование ответа от провайдера
                        logger.info(f"QueryGenerator LLM response: id={getattr(response, 'id', 'N/A')}, "
                                   f"choices={getattr(response, 'choices', None)}")

                        # Проверка на валидность ответа
                        if not response.choices:
                            error_info = getattr(response, 'error', {})
                            if error_info and retry < max_retries - 1:
                                logger.warning(f"Attempt {retry + 1}/{max_retries}: Provider error - {error_info}")
                                delay = base_delay * (2 ** retry)
                                logger.info(f"Retrying in {delay}s... (attempt {retry + 2}/{max_retries})")
                                time.sleep(delay)
                                continue
                            
                            logger.error(f"QueryGenerator: LLM returned empty choices. Full response: {response}")
                            raise ValueError(f"LLM returned empty choices: {response}")

                        # Успешный ответ — выходим из внутреннего retry
                        break
                        
                    except Exception as e:
                        if retry == max_retries - 1:
                            raise
                        logger.warning(f"LLM attempt {retry + 1}/{max_retries} failed: {e}")
                        delay = base_delay * (2 ** retry)
                        logger.info(f"Retrying in {delay}s... (attempt {retry + 2}/{max_retries})")
                        time.sleep(delay)

                result_text = response.choices[0].message.content
                
                # Логирование preview ответа
                logger.info(f"QueryGenerator LLM answer preview: {result_text[:200]}...")

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
                
                # Логирование результата
                result = QueryGenerationResult.from_dict(result_data)
                log_agent_response(
                    query_id=_query_id,
                    session_id=_session_id,
                    user_query=user_query,
                    response_data={
                        "answer": "",
                        "sources": [],
                        "queries_used": [q["text"] for q in result.queries],
                        "search_params": result.search_params,
                        "confidence": result.confidence,
                        "reasoning": result.reasoning,
                        "clarification_needed": result.clarification_needed,
                        "clarification_questions": result.clarification_questions
                    },
                    timing_info={"total_time": time.time() - _start_time}
                )
                return result

            except json.JSONDecodeError as e:
                logger.warning(f"Попытка {attempt + 1}: Ошибка парсинга JSON: {e}")
                if attempt == max_attempts - 1:
                    # Возврат дефолтного результата
                    result = self._default_result(user_query)
                    # Логирование ошибки
                    log_agent_response(
                        query_id=_query_id,
                        session_id=_session_id,
                        user_query=user_query,
                        response_data={
                            "answer": "",
                            "sources": [],
                            "queries_used": [q["text"] for q in result.queries],
                            "search_params": result.search_params,
                            "confidence": result.confidence,
                            "reasoning": f"Ошибка парсинга JSON: {e}",
                            "clarification_needed": False,
                            "clarification_questions": []
                        },
                        timing_info={"total_time": time.time() - _start_time}
                    )
                    return result
            except Exception as e:
                logger.error(f"Попытка {attempt + 1}: Ошибка генерации: {e}")
                if attempt == max_attempts - 1:
                    result = self._default_result(user_query)
                    # Логирование ошибки
                    log_agent_response(
                        query_id=_query_id,
                        session_id=_session_id,
                        user_query=user_query,
                        response_data={
                            "answer": "",
                            "sources": [],
                            "queries_used": [q["text"] for q in result.queries],
                            "search_params": result.search_params,
                            "confidence": result.confidence,
                            "reasoning": f"Ошибка генерации: {e}",
                            "clarification_needed": False,
                            "clarification_questions": []
                        },
                        timing_info={"total_time": time.time() - _start_time}
                    )
                    return result
        
        # Достижение конца цикла (не должно произойти)
        result = self._default_result(user_query)
        log_agent_response(
            query_id=_query_id,
            session_id=_session_id,
            user_query=user_query,
            response_data={
                "answer": "",
                "sources": [],
                "queries_used": [q["text"] for q in result.queries],
                "search_params": result.search_params,
                "confidence": result.confidence,
                "reasoning": "Достигнут конец цикла генерации",
                "clarification_needed": False,
                "clarification_questions": []
            },
            timing_info={"total_time": time.time() - _start_time}
        )
        return result

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
