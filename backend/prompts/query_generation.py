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
Задавай ТОЛЬКО если вопрос НЕВОЗМОЖНО понять («привет», «???», одно слово без контекста).
Если есть хоть какие-то ключевые слова — clarification_needed = false.

## Выбор коллекций

При поиске нормативной информации (тарифы, законы, ставки, льготы, категории, номера документов) —
указывай в search_params поле "prefer_collection": "normative".
При поиске процедур (как подать, этапы, документы, FAQ, инструкции) —
указывай "prefer_collection": "operational".
Если не уверен — "prefer_collection": "all".

## Детекция категории вопроса

Определи, к какой категории относится вопрос пользователя:
- "ЛК" — Личный кабинет (вход, регистрация, лицевой счёт, оплата онлайн,
  показания, заявки в ЛК, настройки)
- "ДУ" — Дополнительные услуги (пакет Минимум, пакет Оптимум, пакет Максимум,
  испытания, замена счётчика, услуги по установке)
- "ТПП" — Технологическое присоединение (заявка на ТП, сроки, документы,
  этапы присоединения, тарифы, мощность, льготы)
- "не известна" — если категорию определить невозможно

Выведи категорию в поле "detected_category" JSON-ответа.

## ТВОЯ ЗАДАЧА

1. Определи сложность:
   - Простой (1 тема) → 1–2 запроса, k=8–10, strategy=concat
   - Сложный (2+ темы) → 2–3 запроса, k=5–7, strategy=separate
   - Очень сложный (3+ темы) → 3 запроса, k=5, strategy=separate

2. Сгенерируй запросы:
   - Конкретные, с ключевыми терминами и синонимами.
   - Для юридических вопросов добавляй номера документов.
    - Используй точные термины и синонимы — это гарантирует попадание в нужные документы.

3. Подбери веса (сумма = 1.0):
    - Точные запросы: pref=0.25, hype=0.25, lexical=0.25, contextual=0.25
    - Общие запросы: pref=0.25, hype=0.25, lexical=0.25, contextual=0.25
    - Запросы с терминами: pref=0.25, hype=0.25, lexical=0.25, contextual=0.25

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
  "detected_category": "ЛК",
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
  "confidence": 0.9,
  "reasoning": "Вопрос конкретный, semantic-heavy веса"
}}
```

### Сложный запрос (2 темы → separate)
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
  "confidence": 0.9,
  "reasoning": "Две темы, ищем отдельно"
}}
```

### Непонятный запрос
Вопрос: "???"
```json
{{
  "clarification_needed": true,
  "clarification_questions": ["Что именно вас интересует? Задайте конкретный вопрос о технологическом присоединении, документах, тарифах или услугах."],
  "queries": [],
  "search_params": {{"k": 5, "pref_weight": 0.25, "hype_weight": 0.25, "lexical_weight": 0.25, "contextual_weight": 0.25, "strategy": "separate"}},
  "confidence": 0.1,
  "reasoning": "Вопрос не содержит информации"
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
