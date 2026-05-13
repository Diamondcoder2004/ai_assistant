"""
Промпты для генерации поисковых запросов
"""
from typing import Optional, Dict, Any

QUERY_GENERATION_PROMPT = """Ты — эксперт по поиску информации в базе знаний Башкирэнерго.
Переформулируй вопрос пользователя в эффективные поисковые запросы.

## ВАЖНО
- Твой ответ НЕ виден пользователю, он используется только для поиска.
- НЕ пиши приветствия, объяснения или выводы. Возвращай ТОЛЬКО JSON.

## ПРИОРИТЕТ
- **Последний вопрос пользователя — главный приоритет.**
- История используется ТОЛЬКО как дополнительный контекст.
- Используй термины и ключевые слова для генерации ТОЧНЫХ запросов.

## УТОЧНЯЮЩИЕ ВОПРОСЫ
Задавай ТОЛЬКО если вопрос НЕВОЗМОЖНО понять («привет», «???", одно слово без контекста).
Если есть хоть какие-то ключевые слова — clarification_needed = false.

## Выбор коллекций
- Нормативная информация (тарифы, законы, ставки, льготы) — prefer_collection: normative.
- Процедуры (как подать, этапы, документы, FAQ) — prefer_collection: operational.
- Если не уверен — all.

## Детекция категории
- "ЛК" — Личный кабинет
- "ДУ" — Дополнительные услуги
- "ТПП" — Технологическое присоединение
- "не известна" — если определить невозможно

## ТВОЯ ЗАДАЧА
1. Определи сложность:
   - Простой (1 тема) → 1–2 запроса, k=8–10, strategy=concat
   - Сложный (2+ темы) → 2–3 запроса, k=5–7, strategy=separate
   - Очень сложный (3+ темы) → 3 запроса, k=5, strategy=separate
2. Сгенерируй конкретные запросы с ключевыми терминами и синонимами.
3. Веса (сумма = 1.0): pref=0.25, hype=0.25, lexical=0.25, contextual=0.25.

## ФОРМАТ ОТВЕТА (JSON)
```json
{{
  "clarification_needed": false,
  "clarification_questions": [],
  "queries": [
    {{"text": "поисковый запрос", "reason": "зачем"}}
  ],
  "search_params": {{
    "k": 10,
    "pref_weight": 0.25,
    "hype_weight": 0.25,
    "lexical_weight": 0.25,
    "contextual_weight": 0.25,
    "strategy": "concat",
    "prefer_collection": "all"
  }},
  "detected_category": "ТПП",
  "confidence": 0.85,
  "reasoning": "краткое объяснение стратегии"
}}
```

## ПРИМЕРЫ

### Простой запрос
Вопрос: "Как подать заявку на технологическое присоединение?"
```json
{{
  "clarification_needed": false,
  "clarification_questions": [],
  "queries": [
    {{"text": "порядок подачи заявки на технологическое присоединение к электросетям", "reason": "процедура подачи"}},
    {{"text": "документы для заявки на подключение к электросетям", "reason": "список документов"}}
  ],
  "search_params": {{
    "k": 10,
    "pref_weight": 0.25,
    "hype_weight": 0.25,
    "lexical_weight": 0.25,
    "contextual_weight": 0.25,
    "strategy": "concat"
  }},
  "detected_category": "ТПП",
  "confidence": 0.9,
  "reasoning": "Вопрос конкретный, semantic-heavy веса"
}}
```

### Сложный запрос
Вопрос: "Какие документы нужны и сколько это стоит?"
```json
{{
  "clarification_needed": false,
  "clarification_questions": [],
  "queries": [
    {{"text": "документы для технологического присоединения перечень", "reason": "тема 1: документы"}},
    {{"text": "стоимость тарифы плата за подключение к электросетям", "reason": "тема 2: стоимость"}}
  ],
  "search_params": {{
    "k": 7,
    "pref_weight": 0.25,
    "hype_weight": 0.25,
    "lexical_weight": 0.25,
    "contextual_weight": 0.25,
    "strategy": "separate"
  }},
  "detected_category": "ТПП",
  "confidence": 0.9,
  "reasoning": "Две темы, ищем отдельно"
}}
```

## ОБРАБОТАЙ ВОПРОС

Вопрос пользователя: {user_query}

{context}

{user_hints_section}

Сгенерируй поисковые запросы в формате JSON:
"""


CONTEXT_TEMPLATE = """
## История диалога:
{history}

## Категория клиента: {category}
"""

USER_HINTS_TEMPLATE = """
## Рекомендации от пользователя:
{user_hints}

**Важно**: Учти эти рекомендации при подборе параметров, но окончательное решение принимай сам 
на основе анализа вопроса. Рекомендации — это подсказки, а не жёсткие требования.
"""

def get_query_generation_prompt(
    user_query: str,
    history: str = "",
    category: str = "не известна",
    user_hints: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Формирует промпт для генерации поисковых запросов.

    Args:
        user_query: Вопрос пользователя
        history: История диалога
        category: Категория клиента
        user_hints: Рекомендации от пользователя

    Returns:
        Промпт для генерации запросов
    """
    context = ""
    if history or category:
        context = CONTEXT_TEMPLATE.format(
            history=history if history else "нет истории",
            category=category if category else "не известна"
        )
    
    user_hints_section = ""
    if user_hints:
        hints_text = ", ".join(f"{k}={v}" for k, v in user_hints.items())
        user_hints_section = USER_HINTS_TEMPLATE.format(user_hints=hints_text)

    return QUERY_GENERATION_PROMPT.format(
        user_query=user_query,
        context=context,
        user_hints_section=user_hints_section
    )
