"""
LLM-as-a-Judge для оценки качества ответов RAG системы

Оценивает ответы по метрикам:
- Relevance (релевантность вопросу)
- Completeness (полнота ответа)
- Helpfulness (полезность)
- Clarity (ясность изложения)
- Hallucination Risk (риск галлюцинаций)
"""
import logging
import json
from typing import Dict, Any, List
from dataclasses import dataclass
from openai import OpenAI

import config

logger = logging.getLogger(__name__)


@dataclass
class LLMEvaluation:
    """Результат оценки LLM Judge."""
    relevance: float  # 1-5
    completeness: float  # 1-5
    helpfulness: float  # 1-5
    clarity: float  # 1-5
    hallucination_risk: float  # 1-5
    context_recall: float  # 1-5 (Есть ли ответ в чанках)
    faithfulness: float  # 1-5 (Насколько ответ следует чанкам)
    currency: float  # 1-5 (Актуальность/соответствие ожидаемому)
    binary_correctness: int  # 0 или 1
    overall_score: float
    reasoning: str


EVALUATION_PROMPT = """Ты — независимый эксперт (LLM Judge) для оценки качества RAG системы.
Твоя задача — оценить сгенерированный ответ на вопрос пользователя.

## Входные данные:

**Вопрос пользователя:**
{question}

**Сгенерированный ответ:**
{answer}

**Ожидаемый эталонный ответ:**
{expected}

**Найденные источники (контекст):**
{sources}

## Критерии оценки (шкала 1-5):

### 1. Relevance (Релевантность)
Насколько ответ соответствует вопросу?
- 1: Ответ не по теме
- 2: Ответ частично по теме, много лишнего
- 3: Ответ в основном по теме
- 4: Ответ релевантный, есть небольшие отклонения
- 5: Ответ полностью соответствует вопросу

### 2. Completeness (Полнота)
Насколько полно раскрыта тема?
- 1: Ответ очень краткий, не раскрыта тема
- 2: Ответ неполный, упущены важные детали
- 3: Ответ достаточно полный, есть пробелы
- 4: Ответ полный, раскрыты основные аспекты
- 5: Ответ исчерпывающий, раскрыты все аспекты

### 3. Helpfulness (Полезность)
Насколько ответ полезен пользователю?
- 1: Ответ бесполезен
- 2: Ответ мало полезен
- 3: Ответ умеренно полезен
- 4: Ответ полезен
- 5: Ответ очень полезен, даёт конкретные действия/информацию

### 4. Clarity (Ясность)
Насколько ясно изложен ответ?
- 1: Ответ непонятен, хаотичен
- 2: Ответ трудно понять
- 3: Ответ достаточно ясный
- 4: Ответ ясный, хорошо структурирован
- 5: Ответ очень ясный, отлично структурирован

### 5. Hallucination Risk (Риск галлюцинаций)
Насколько ответ основан на источниках? (5 = низкий риск, 1 = высокий)
- 1: Много информации не из источников, выдумки
- 2: Значительная часть информации не подтверждена
- 3: Большая часть из источников, есть домыслы
- 4: В основном по источникам, minor допущения
- 5: Строго по источникам, нет выдумок

### 6. Context Recall (Наличие ответа в чанках)
Есть ли в предоставленных ИСТОЧНИКАХ фактическая информация для ответа на вопрос?
- 1: В источниках вообще нет информации для ответа.
- 5: В источниках содержится исчерпывающая информация для ответа.

### 7. Faithfulness (Верность источникам)
Насколько ответ СТРОГО следует предоставленному контексту, не привнося внешних знаний или галлюцинаций?
- 1: Ответ противоречит источникам или полностью выдуман.
- 5: Ответ на 100% основан на предоставленных источниках.

### 8. Currency & Correctness (Актуальность и Правильность)
Насколько информация в ответе актуальна на текущий момент и соответствует эталонному (expected) ответу?
- 1: Информация устарела или содержит фактические ошибки.
- 5: Информация абсолютно актуальна и фактически верна.


## Формат ответа (JSON):

```json
{{
  "relevance": 5,
  "completeness": 5,
  "helpfulness": 5,
  "clarity": 5,
  "hallucination_risk": 5,
  "context_recall": 5,
  "faithfulness": 5,
  "currency": 5,
  "binary_correctness": 1,
  "overall_score": 5.0,
  "reasoning": "Причина оценки..."
}}
```

## Важно:

- Оценивай объективно
- Учитывай, что ответ должен быть основан на источниках
- Hallucination Risk: 5 = низкий риск (ответ по источникам), 1 = высокий риск (выдумки)
- Overall Score = среднее арифметическое всех оценок
"""


class LLMJudge:
    """
    LLM-as-a-Judge для оценки ответов RAG системы.
    """
    
    def __init__(self):
        self.client = OpenAI(
            api_key=config.ROUTERAI_API_KEY,
            base_url=config.ROUTERAI_BASE_URL
        )
        self.model = config.JUDGE_LLM_MODEL
        logger.info(f"LLM Judge инициализирован: {self.model}")
    
    def evaluate(
        self,
        question: str,
        answer: str,
        expected: str,
        sources: List[Dict[str, Any]],
        temperature: float = 0.3,
        max_attempts: int = 3
    ) -> LLMEvaluation:
        """
        Оценка ответа.
        """
        # Форматирование источников
        sources_text = self._format_sources(sources)
        
        # Формирование промпта
        prompt = EVALUATION_PROMPT.format(
            question=question,
            answer=answer[:4000],
            expected=expected[:4000],
            sources=sources_text
        )
        
        logger.info(f"Оценка ответа для вопроса: '{question[:50]}...'")
        
        for attempt in range(max_attempts):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "Ты LLM Judge. Твоя задача - строгий аудит RAG. Отвечай ТОЛЬКО в формате JSON. Не пиши ничего, кроме JSON."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=temperature,
                    max_tokens=1500,
                    response_format={"type": "json_object"}
                )
                
                result_text = response.choices[0].message.content
                
                # Очистка текста от возможных артефактов DeepSeek
                cleaned_text = self._extract_json_string(result_text)
                
                # Парсинг JSON
                result_data = json.loads(cleaned_text)
                
                # Принудительное приведение типов
                for field in ["relevance", "completeness", "helpfulness", "clarity", 
                            "hallucination_risk", "context_recall", "faithfulness", "currency"]:
                    if field in result_data:
                        result_data[field] = float(result_data[field])

                if "binary_correctness" in result_data:
                    result_data["binary_correctness"] = int(result_data["binary_correctness"])

                # Валидация полей
                required_fields = ["relevance", "completeness", "helpfulness", 
                                   "clarity", "hallucination_risk", "overall_score", "reasoning"]
                
                if not all(field in result_data for field in required_fields):
                    logger.warning(f"Попытка {attempt + 1}: Не все поля в ответе")
                    continue
                
                logger.info(f"Оценка успешна с попытки {attempt + 1}")
                return LLMEvaluation(
                    relevance=result_data["relevance"],
                    completeness=result_data["completeness"],
                    helpfulness=result_data["helpfulness"],
                    clarity=result_data["clarity"],
                    hallucination_risk=result_data["hallucination_risk"],
                    context_recall=result_data.get("context_recall", 3.0),
                    faithfulness=result_data.get("faithfulness", 3.0),
                    currency=result_data.get("currency", 3.0),
                    binary_correctness=result_data.get("binary_correctness", 0),
                    overall_score=result_data["overall_score"],
                    reasoning=result_data["reasoning"]
                )
                
            except Exception as e:
                logger.warning(f"Попытка {attempt + 1}: Ошибка оценки/парсинга: {e}")
                if attempt == max_attempts - 1:
                    return self._default_evaluation()
        
        return self._default_evaluation()

    def _extract_json_string(self, text: str) -> str:
        """Вырезает JSON из строки, если модель добавила лишний текст или ```json."""
        text = text.strip()
        # Ищем начало и конец JSON объекта
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1:
            return text[start:end+1]
        return text
    
    def _format_sources(self, sources: List[Dict[str, Any]]) -> str:
        """Форматирование источников."""
        if not sources:
            return "Источники не предоставлены."
        
        parts = []
        for i, src in enumerate(sources[:5], 1):
            part = (
                f"[{i}] {src.get('filename', 'Неизвестно')}\n"
                f"    Категория: {src.get('category', 'не указана')}\n"
                f"    Раздел: {src.get('breadcrumbs', 'не указан')}\n"
                f"    Релевантность: {src.get('score_hybrid', 0):.3f}\n"
            )
            parts.append(part)
        
        return "\n".join(parts)
    
    def _default_evaluation(self) -> LLMEvaluation:
        """Возвращает дефолтную оценку при ошибке."""
        return LLMEvaluation(
            relevance=3.0, completeness=3.0, helpfulness=3.0, clarity=3.0,
            hallucination_risk=3.0, context_recall=3.0, faithfulness=3.0,
            currency=3.0, binary_correctness=0, overall_score=3.0,
            reasoning="Оценка не выполнена из-за ошибки. Возвращена дефолтная оценка."
        )
    
    def evaluate_batch(
        self,
        samples: List[Dict[str, Any]]
    ) -> List[LLMEvaluation]:
        """
        Пакетная оценка образцов.
        
        Args:
            samples: Список образцов с полями question, answer, sources
        
        Returns:
            Список оценок
        """
        evaluations = []
        for sample in samples:
            evaluation = self.evaluate(
                question=sample["question"],
                answer=sample["answer"],
                sources=sample["sources"]
            )
            evaluations.append(evaluation)
        return evaluations


def get_llm_judge() -> LLMJudge:
    """Фабричная функция для получения LLM Judge."""
    return LLMJudge()
