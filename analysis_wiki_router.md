# Диагностика: почему WikiRouter не улучшает качество ответов

## Общая картина

Ты добавил `WikiRouterAgent` как нулевой шаг перед поиском. Идея правильная —
предварительно обогатить запрос бизнес-контекстом. Но в текущей реализации
WikiRouter **добавляет шум и сужает поиск**, а не помогает ему.

---

## Найденные проблемы (в порядке критичности)

### 🔴 Критично: `search_agent.py` содержит мёртвый код — весь pipeline дублирован

**Файл:** [search_agent.py](file:///d:/ai_assistant/backend/agents/search_agent.py#L236-L344), строки 236–344.

После `return result` (строка 234) идёт точная копия всей логики с шагами 2–5.
Этот блок **никогда не выполняется**.

```python
# строка 234
return result  # ← вот отсюда возвращается результат

# строки 236-344 — весь код МЁРТВ, никогда не выполняется
if self.query_generator.needs_clarification(gen_result):
    ...
```

---

### 🔴 Критично: `document_filters` из WikiRouter **жёстко обрезают** Qdrant-поиск

В [main.py](file:///d:/ai_assistant/backend/main.py#L116-L127):
```python
document_filters = wiki_result.document_filters
# Например: {"client_type": ["ФЛ"], "power_range": ["<15kW"], "category": ["ТПП"]}
```

`build_qdrant_filter()` создаёт `models.Filter(must=conditions)` — жёсткое AND.
Если WikiRouter ошибся с категорией или типом клиента → Qdrant пропускает нужные чанки.

> **Пример:** Вопрос «Какой порядок технологического присоединения?»
> WikiRouter выдаёт `category: ["ТПП"]` → фильтр исключает ФЗ-35 и ПП-861
> у которых `category: "Общая"`, хотя именно они содержат нужные ответы.

---

### 🟠 Высокое: WikiRouter добавляет 3-й LLM-вызов на каждый запрос

| # | Агент | Модель |
|---|-------|--------|
| 0 | WikiRouterAgent._llm_route() | inception/mercury-2 |
| 1 | QueryGeneratorAgent.generate() | inception/mercury-2 |
| 2 | ResponseAgent.generate_response() | deepseek/deepseek-v4-flash |

Mercury-2 нестабилен и может возвращать некорректные `business_rules` / `key_terms`,
которые затем «отравляют» QueryGenerator.

---

### 🟠 Высокое: Категория `"Общая"` не включается в фильтр по категории

В [search_tool.py](file:///d:/ai_assistant/backend/tools/search_tool.py#L76-L98)
для `client_type` есть хак `types.append("any")`, но для `category` его нет.
Нормативные документы (ФЗ-35, ПП-442, ПП-861) все имеют `category: "Общая"` —
при любом запросе на ТПП/ЛК/ДУ они вылетают из выборки.

---

### 🟡 Среднее: `wiki_context` слишком большой для QueryGenerator

`_build_result_from_docs()` строит контекст из 3 документов: title + summary (полный) +
business_rules + key_terms. Размер достигает **2–4KB** в промпте QueryGenerator.

Промпт в [query_generation.py](file:///d:/ai_assistant/backend/prompts/query_generation.py#L16):
> «Контекст Wiki — ТВОЙ ГЛАВНЫЙ ПОМОЩНИК. Wiki знает бизнес-логику — доверяй ей.»

Это значит QueryGenerator жёстко следует терминам Wiki, даже если они ошибочны.

---

### 🟡 Среднее: `search_multi()` объединяет все запросы в одну строку для BM25

```python
request = SearchRequest(
    query=" ".join(queries),  # Combined query for BM25
    ...
)
```

При стратегии `separate` (2–3 запроса) BM25 получает одну размытую строку.
С Wiki термины ещё длиннее — BM25-компонент теряет точность.

---

## Ключевой вывод

**WikiRouter в текущем виде работает как «умный фильтр, который ошибается»:**

```
Ошибка WikiRouter → неправильный фильтр → Qdrant пропускает чанки
                  → неправильный wiki_context → QueryGenerator генерирует нерелевантные запросы
                                              → плохие источники → плохой ответ
```

**Без Wiki (прежнее поведение):**
- QueryGenerator без ограничений, BM25 + семантика по всей базе
- Qdrant возвращает полную выборку

---

## Рекомендации (в порядке приоритета)

### 🔥 1. Убрать `document_filters` из поиска (самый быстрый фикс)

```python
# backend/main.py — изменить строку 116
wiki_context = wiki_result.wiki_context
document_filters = None  # WikiRouter даёт только контекст, не фильтры
```

Или сделать фильтры опциональными через конфиг:
```
WIKI_ENABLE_FILTERS=false
```

### 🔥 2. Удалить мёртвый код в `search_agent.py` (строки 236–344)

Убрать дублирующийся блок после `return result` на строке 234.

### 📌 3. Добавить `"Общая"` в category-фильтр

```python
# build_qdrant_filter() в search_tool.py:
if "category" in document_filters and document_filters["category"]:
    categories = list(document_filters["category"])
    if "Общая" not in categories:
        categories.append("Общая")  # нормативные документы всегда нужны
```

### 💡 4. Разделить wiki_context: краткий для QueryGenerator, полный для ResponseAgent

```python
# main.py:
wiki_context_short = "\n".join([
    f"Тема: {doc.title}. Термины: {', '.join(doc.key_terms[:8])}"
    for doc in wiki_result.concepts
])
wiki_context_full = wiki_result.wiki_context

# Передать разные контексты:
# search_agent.search(wiki_context=wiki_context_short, ...)
# response_agent.generate_response(wiki_context=wiki_context_full, ...)
```

---

## Быстрая проверка гипотезы

Временно добавь в `.env`:
```
ENABLE_WIKI_ROUTER=false
```

Прогони те же вопросы из `benchmark_dataset.csv`.
Если оценки вернутся к прежнему уровню — проблема точно в `document_filters`.
