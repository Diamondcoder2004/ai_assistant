"""
LLM-as-a-Judge для честной оценки качества RAG-ответов.

Ключевые улучшения v2:
- Видит ожидаемый эталонный ответ (expected) для binary correctness
- Видит полный контент источников (content), не только метаданные
- Оценивает faithfulness на основе совпадения с источниками, а не с эталоном
- Binary correctness сравнивает смысл ответа с эталоном
"""
import logging
import json
import time
from typing import Dict, Any, List
from dataclasses import dataclass
from langfuse.openai import OpenAI

import config

logger = logging.getLogger(__name__)


@dataclass
class LLMEvaluation:
    """Результат оценки LLM Judge."""
    relevance: float = 3.0
    completeness: float = 3.0
    helpfulness: float = 3.0
    clarity: float = 3.0
    hallucination_risk: float = 3.0
    context_recall: float = 3.0
    faithfulness: float = 3.0
    currency: float = 3.0
    binary_correctness: int = 0
    overall_score: float = 3.0
    reasoning: str = ""


EVALUATION_PROMPT = """Ты — строгий эксперт-аудитор RAG системы поддержки клиентов Башкирэнерго по вопросам техприсоединения к электросетям.

## Твоя задача
Оцени сгенерированный ответ на основе ВСЕХ предоставленных данных:
1. Насколько ответ соответствует вопросу (relevance)
2. Насколько полно раскрыта тема (completeness)  
3. Насколько ответ полезен (helpfulness)
4. Насколько ясно изложен (clarity)
5. Есть ли галлюцинации — информация не из источников (hallucination_risk)
6. Есть ли в источниках информация для ответа (context_recall)
7. Насколько ответ следует источникам, а не придумывает (faithfulness)
8. Актуальность информации (currency)
9. Смысловая правильность относительно эталона (binary_correctness)

## ВХОДНЫЕ ДАННЫЕ

### Вопрос пользователя:
{question}

### Ожидаемый эталонный ответ (что должно быть сказано):
{expected}

### Сгенерированный ответ (оцениваем):
{answer}

### Контекст из поиска (что видел ResponseAgent):
{sources}

## КРИТЕРИИ ОЦЕНКИ (шкала 1-5)

### 1. Relevance — Релевантность вопросу
- 5: Ответ точно по вопросу, без отвлечений
- 3: Частично по теме, есть лишнее
- 1: Ответ не про то, что спросили

### 2. Completeness — Полнота
- 5: Раскрыты все ключевые аспекты из эталонного ответа
- 3: Основное сказано, но упущены важные детали
- 1: Ответ поверхностный, большинство аспектов не раскрыто

### 3. Helpfulness — Полезность
- 5: Даёт конкретные действия, шаги, ссылки — клиент может действовать
- 3: Информация есть, но без чётких инструкций
- 1: Бесполезный ответ

### 4. Clarity — Ясность
- 5: Чёткая структура, понятный язык, нет путаницы
- 3: В целом понятно, но есть неясные места
- 1: Хаотично, непонятно

### 5. Hallucination Risk — Риск галлюцинаций (5 = НИЗКИЙ риск)
- 5: Всё строго из источников, нет выдумок
- 3: Часть информации не подтверждается источниками
- 1: Много выдуманной информации, отсутствующей в источниках

### 6. Context Recall — Полнота контекста
- 5: В предоставленных источниках есть ВСЯ информация для полного ответа
- 3: В источниках есть часть информации, но многого не хватает
- 1: В источниках практически нет нужной информации

### 7. Faithfulness — Верность источникам
- 5: Ответ на 100% основан на предоставленных источниках
- 3: Ответ частично расходится с источниками
- 1: Ответ противоречит источникам или полностью выдуман

### 8. Currency — Актуальность
- 5: Информация актуальна, упоминаются правильные процедуры и сроки
- 3: Частично устаревшая информация
- 1: Явно устаревшие данные

### 9. Binary Correctness — Смысловая правильность (0 или 1)
Сравни СМЫСЛ ответа с эталоном. Ответ считается правильным (1), если:
- Передаёт ТУ ЖЕ СУТЬ, что и эталонный ответ
- Не противоречит эталону в ключевых фактах
- Лишние подробности, вежливые формулировки и дополнительные советы НЕ снижают оценку
Ответ считается неправильным (0), если:
- Противоречит эталону в важных деталях
- Даёт неверную процедуру, сроки, контакты
- Утверждает то, чего нет в эталоне

### Overall Score
Среднее арифметическое всех оценок (binary_correctness умножается на 5 для приведения к шкале 1-5).

## ФОРМАТ ОТВЕТА — ТОЛЬКО JSON:
```json
{{
  "relevance": 4,
  "completeness": 3,
  "helpfulness": 4,
  "clarity": 4,
  "hallucination_risk": 4,
  "context_recall": 3,
  "faithfulness": 4,
  "currency": 4,
  "binary_correctness": 0,
  "overall_score": 3.3,
  "reasoning": "Краткое обоснование на русском: что хорошо, что плохо, почему binary=0/1."
}}
```

Будь СТРОГИМ. Если ответ не совпадает с эталоном по сути — binary_correctness = 0.
Если в ответе есть факты, которых нет в источниках — снижай faithfulness.
Не завышай оценки из вежливости."""


class LLMJudge:
    """LLM Judge v2 — видит контекст и эталон."""

    def __init__(self):
        self.client = OpenAI(
            api_key=config.ROUTERAI_API_KEY,
            base_url=config.ROUTERAI_BASE_URL
        )
        self.model = config.JUDGE_LLM_MODEL
        logger.info(f"LLMJudge v2: {self.model}")

    def evaluate(
        self,
        question: str,
        answer: str,
        expected: str,
        sources: List[Dict[str, Any]],
        temperature: float = 0.2,
        max_attempts: int = 3
    ) -> LLMEvaluation:
        """Оценка ответа с полным контекстом."""

        sources_text = self._format_sources_full(sources)

        prompt = EVALUATION_PROMPT.format(
            question=question,
            expected=expected[:2000],
            answer=answer[:4000],
            sources=sources_text
        )

        for attempt in range(max_attempts):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "Ты строгий LLM Judge. Отвечай ТОЛЬКО JSON. Никаких пояснений вне JSON."
                        },
                        {"role": "user", "content": prompt}
                    ],
                    temperature=temperature,
                    max_tokens=2000,
                    response_format={"type": "json_object"}
                )

                result_text = response.choices[0].message.content
                cleaned = self._extract_json(result_text)
                data = json.loads(cleaned)

                # Приведение типов
                for field in ["relevance", "completeness", "helpfulness", "clarity",
                              "hallucination_risk", "context_recall", "faithfulness",
                              "currency", "overall_score"]:
                    if field in data:
                        data[field] = float(data[field])
                if "binary_correctness" in data:
                    data["binary_correctness"] = int(data["binary_correctness"])

                logger.info(f"  Judge OK (attempt {attempt + 1})")

                return LLMEvaluation(
                    relevance=data.get("relevance", 3.0),
                    completeness=data.get("completeness", 3.0),
                    helpfulness=data.get("helpfulness", 3.0),
                    clarity=data.get("clarity", 3.0),
                    hallucination_risk=data.get("hallucination_risk", 3.0),
                    context_recall=data.get("context_recall", 3.0),
                    faithfulness=data.get("faithfulness", 3.0),
                    currency=data.get("currency", 3.0),
                    binary_correctness=data.get("binary_correctness", 0),
                    overall_score=data.get("overall_score", 3.0),
                    reasoning=data.get("reasoning", "")
                )

            except Exception as e:
                logger.warning(f"  Judge attempt {attempt + 1} failed: {e}")
                if attempt == max_attempts - 1:
                    return self._default_evaluation(f"Ошибка: {e}")
                time.sleep(2 ** attempt)

        return self._default_evaluation("max attempts exceeded")

    def _extract_json(self, text: str) -> str:
        """Извлечь JSON из ответа модели."""
        text = text.strip()
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1:
            return text[start:end + 1]
        return text

    def _format_sources_full(self, sources: List[Dict[str, Any]]) -> str:
        """Форматирование источников с ПОЛНЫМ контентом."""
        if not sources:
            return "⚠️ ИСТОЧНИКИ НЕ ПРЕДОСТАВЛЕНЫ. Ответ сгенерирован без контекста."

        parts = []
        for i, src in enumerate(sources[:10], 1):
            filename = src.get('filename', src.get('source_file', 'Неизвестно'))
            breadcrumbs = src.get('breadcrumbs', '')
            category = src.get('category', '')
            content = src.get('content', src.get('chunk_content', ''))
            summary = src.get('summary', src.get('chunk_summary', ''))
            score = src.get('score_hybrid', src.get('score', 0))

            # Используем summary + content, но обрезаем длинные тексты
            text = ""
            if summary:
                text = f"Краткое содержание: {summary}\n\n"
            if content:
                text += content

            # Обрезаем до разумного размера
            if len(text) > 2000:
                text = text[:2000] + "..."

            part = (
                f"### Источник [{i}] — {filename}\n"
                f"Навигация: {breadcrumbs}\n"
                f"Категория: {category}\n"
                f"Релевантность: {score:.3f}\n"
                f"Текст:\n{text}\n"
            )
            parts.append(part)

        return "\n---\n".join(parts)

    def _default_evaluation(self, reason: str = "") -> LLMEvaluation:
        """Заглушка при ошибке."""
        return LLMEvaluation(
            relevance=3.0, completeness=3.0, helpfulness=3.0,
            clarity=3.0, hallucination_risk=3.0, context_recall=3.0,
            faithfulness=3.0, currency=3.0, binary_correctness=0,
            overall_score=3.0,
            reasoning=reason or "Оценка не выполнена из-за ошибки парсинга."
        )


def get_llm_judge() -> LLMJudge:
    """Фабрика."""
    return LLMJudge()
