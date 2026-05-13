---
date: 2026-05-13
topic: "Category-Aware Partial Filtering for Qdrant Search"
status: draft
---

## Problem Statement

Текущий поиск не фильтрует чанки по категории (ЛК/ДУ/ТПП). Вопросы про «как войти в ЛК» получают чанки с `category=ТПП`, вопросы про «пакет Минимум» — чанки с `category=ЛК`. Это снижает precision ретривала: 22.4% ответов (69/308 в benchmark) — отказ «нет в источниках», хотя информация в KB есть, но buried в неправильной категории.

**Ключевое наблюдение:** вся цепочка фильтрации уже построена, но `document_filters` никто не передаёт:
- `QueryGenerator` уже принимает `category` на вход, но не выводит её обратно
- `SearchAgent.search()` уже принимает `document_filters`, но всегда получает `None`
- `build_qdrant_filter()` уже умеет конвертировать `{"category": ["ЛК"]}` в Qdrant Filter
- `search_tool.search_multi()` уже принимает `qf_filter` и передаёт в Qdrant

Нужно замкнуть эту цепочку.

---

## Constraints

- **Нельзя терять recall:** только часть результатов (30%) фильтруется по категории, остальные 70% — обычный полный поиск (blended approach)
- **Никаких новых LLM-вызовов:** категория детектится в том же вызове QueryGenerator, без отдельного дорогого запроса
- **Только ЛК и ДУ:** ТПП — слишком широкая категория, фильтр по ней не даст выгоды
- **Существующий API не меняется:** фронтенд, endpoints, схемы остаются без изменений
- **Graceful degradation:** при `detected_category="не известна"` или пустом filtered-результате pipeline работает как сейчас

---

## Approach

**Chosen: Blended Retrieval с детекцией категории в QueryGenerator**

QueryGenerator определяет категорию вопроса в том же LLM-вызове (новое поле `detected_category` в JSON-ответе). SearchAgent, получив категорию ЛК или ДУ, запускает два параллельных поиска — один с category-фильтром, другой без — и смешивает результаты в пропорции 30/70.

**Почему не жёсткий фильтр (100%):**
- ТПП-документы иногда содержат ответы на ЛК-вопросы (и наоборот)
- WikiRouter может решить, что тема ТПП, когда вопрос на самом деле про ЛК
- Blended approach сохраняет recall для граничных случаев

---

## Architecture

```
User Query
    │
    ▼
WikiRouter (existing)
    │  ── category="не известна" (как сейчас)
    ▼
QueryGenerator ─── LLM определяет detected_category ───┐
    │  (в том же JSON-ответе, без дополнительного вызова)  │
    ▼                                                     ▼
SearchAgent.check_category() ──► "ЛК" или "ДУ"?       "не известна"?
    │                                                     │
    ├── search_multi (без фильтра)  70% k                 │ (один поиск, как сейчас)
    ├── search_multi (filter: category=ЛК)  30% k         │
    │                                                     │
    └── blend_results() ──► dedup ──► sort ──► top-k      │
                                                          ▼
                                              filter_by_overlap()
                                              regulatory_boost()
                                              compute_source_quality()
                                                          │
                                                          ▼
                                              ResponseAgent
```

### Data Flow

```
QueryGenerator._parse_response()
    │
    ├── "detected_category": "ЛК"     # NEW field from LLM
    ├── "queries": [...]
    ├── "search_params": {...}
    └── "confidence": 0.85
         │
         ▼
SearchAgent.search()
    │
    ├── gen_result = self.query_generator.generate()
    ├── detected_cat = gen_result.detected_category
    │
    ├── if detected_cat in ("ЛК", "ДУ"):
    │       self._blended_search(queries, k, category=detected_cat)
    │   else:
    │       self.search_tool.search_multi(queries, k=k)
    │
    └── continue with filter_by_overlap → regulatory_boost → source_quality
```

---

## Components

### 1. QueryGenerationResult — новое поле `detected_category`

**Файл:** `backend/agents/query_generator.py`

Добавить поле в датакласс:

```python
@dataclass
class QueryGenerationResult:
    clarification_needed: bool
    clarification_questions: List[str]
    queries: List[Dict[str, str]]
    search_params: Dict[str, Any]
    confidence: float
    reasoning: str
    # ── NEW ──
    detected_category: str = "не известна"
```

Обновить `from_dict()` и `_default_result()`:

```python
from_dict:
    detected_category = data.get("detected_category", "не известна")

_default_result:
    detected_category = "не известна"
```

---

### 2. QueryGenerator Prompt — инструкция по детекции категории

**Файл:** `backend/prompts/query_generation.py`

Добавить в промпт:

```
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
```

Добавить в пример JSON-формата (демонстрация поля):

```json
{
  "clarification_needed": false,
  "clarification_questions": [],
  "queries": [...],
  "search_params": {...},
  "detected_category": "ЛК",
  "confidence": 0.85,
  "reasoning": "краткое объяснение стратегии"
}
```

---

### 3. SearchAgent — Blended Search

**Файл:** `backend/agents/search_agent.py`

**Новый метод `_blended_search()`:**

```python
def _blended_search(
    self,
    queries: List[str],
    k: int,
    category: str,
    qf_filter: Optional[models.Filter] = None,
    weights: Optional[Dict[str, float]] = None,
) -> List[SearchResult]:
    """
    Двухфазный поиск с блендингом filtered и unfiltered результатов.
    
    30% top-k берётся из поиска с фильтром по category,
    70% — из обычного поиска без фильтра.
    """
    blend_ratio = config.CATEGORY_FILTER_BLEND_RATIO  # 0.3
    filtered_k = max(1, ceil(k * blend_ratio))
    unfiltered_k = k  # запрашиваем полный k для unfiltered
    
    # Фильтр по категории (через существующий build_qdrant_filter)
    category_filter = build_qdrant_filter({"category": [category]})
    
    # Параллельные поиски (ThreadPoolExecutor)
    with ThreadPoolExecutor(max_workers=2) as executor:
        f_future = executor.submit(
            self.search_tool.search_multi,
            queries=queries,
            qf_filter=category_filter,
            k=filtered_k,
            weights=weights,
        )
        u_future = executor.submit(
            self.search_tool.search_multi,
            queries=queries,
            qf_filter=qf_filter,  # existing non-category filter (e.g. collection)
            k=unfiltered_k,
            weights=weights,
        )
        filtered_results = f_future.result()
        unfiltered_results = u_future.result()
    
    # Блендинг
    return blend_results(
        filtered=filtered_results,
        unfiltered=unfiltered_results,
        total_k=k,
    )
```

**Новая функция `blend_results()`:**

```python
def blend_results(
    filtered: List[SearchResult],
    unfiltered: List[SearchResult],
    total_k: int,
) -> List[SearchResult]:
    """
    Смешивание filtered и unfiltered результатов.
    - filtered приоритетны: все filtered идут в итог
    - unfiltered дополняют до total_k
    - Декдупликация по chunk_id (filtered приоритетен при дубликатах)
    - Сортировка по score_hybrid
    """
    # Берём все filtered
    blended = list(filtered)
    seen_ids = {r.id for r in blended}
    
    # Дополняем из unfiltered (пропуская дубликаты)
    for r in unfiltered:
        if len(blended) >= total_k:
            break
        if r.id not in seen_ids:
            blended.append(r)
            seen_ids.add(r.id)
    
    # Сортируем по hybrid score
    blended.sort(key=lambda r: r.score_hybrid, reverse=True)
    return blended[:total_k]
```

**Изменение основного `search()` метода — после строки получения gen_result (строка 143):**

```python
# 2.5 Category-aware blended search
detected_category = gen_result.detected_category if not skip_query_generator else "не известна"
if detected_category in ("ЛК", "ДУ") and config.CATEGORY_FILTER_ENABLED:
    logger.info(f"Category-aware search: detected={detected_category}, k={k_per_query}")
    results = self._blended_search(
        queries=queries,
        k=k_per_query,
        category=detected_category,
        qf_filter=qf_filter,
    )
else:
    # Existing single search
    with timing_context("SearchAgent.tool_search"):
        results = self.search_tool.search_multi(
            queries=queries,
            qf_filter=qf_filter,
            k=k_per_query * len(queries) if strategy == "separate" else k_per_query,
        )
```

---

### 4. Config — новые переменные

**Файл:** `backend/config.py`

```python
# Category-aware partial filtering
CATEGORY_FILTER_ENABLED = os.getenv("CATEGORY_FILTER_ENABLED", "true").lower() in ("1", "true", "yes")
# Proportion of results taken from the filtered search (0.0-1.0)
CATEGORY_FILTER_BLEND_RATIO = float(os.getenv("CATEGORY_FILTER_BLEND_RATIO", "0.3"))
```

---

### 5. k по режимам — сколько filtered-кандидатов нужно

SearchAgent наследует `k` от user_hints (фронтенд):

| Mode | k итог | filtered (30%) | unfiltered (100%) | После dedup |
|---|---|---|---|---|
| **brief** | 5 | ceil(5×0.3) = **2** | 5 | 2+3=5 |
| **standard** | 10 | ceil(10×0.3) = **3** | 10 | 3+7=10 |
| **detailed** | 15 | ceil(15×0.3) = **5** | 15 | 5+10=15 |

SearchTool при `k=3` (filtered) запрашивает из Qdrant: `3 × 3 = 9` кандидатов per vector type. Соответственно при `k=5`: `5 × 3 = 15`. Это несущественная дополнительная нагрузка.

---

## Error Handling

| Сценарий | Поведение |
|---|---|
| `detected_category="не известна"` | Фильтр не применяется, single search как сейчас |
| `detected_category="ТПП"` | Фильтр не применяется (категория слишком широкая) |
| QueryGenerator вернул confidence < 0.6 | Фильтр не применяется (ненадёжная детекция) |
| `filtered_results` пустой | Используются только unfiltered — graceful degradation |
| `len(unfiltered) < total_k` | Берётся сколько есть |
| search_tool.search_multi выбросил исключение | Ловится, filtered_results = [] |

---

## Testing Strategy

### Unit tests

1. **`test_blend_results`**: проверить что blend сохраняет ratio, дедуплицирует, сортирует
   - filtered = [A(score=0.9), B(score=0.8)]
   - unfiltered = [B(score=0.8), C(score=0.7)]
   - total_k = 3 → expected = [A, B, C] (B deduped from unfiltered)

2. **`test_detected_category_from_dict`**: проверить парсинг нового поля из JSON LLM

3. **`test_no_filter_for_tpp`**: при `detected_category="ТПП"` фильтр не применяется

4. **`test_empty_filtered_graceful`**: при пустом filtered падаем обратно на unfiltered

### Integration

- Запустить benchmark на 100 вопросах (все категории)
- Проверить что binary correctness для вопросов категорий ЛК/ДУ повысилась
- Проверить что recall для ТПП-вопросов не упал

### Manual

- Отправить вопрос «как войти в личный кабинет?» — убедиться что в sources есть чанки с category=ЛК
- Отправить вопрос «пакет минимум что входит» — проверить category=ДУ в результатах
- Отправить вопрос «сроки технологического присоединения» — проверить что category не повлияла на результаты (ТПП → фильтр не применяется)

---

## Files to Modify

| File | Change | Complexity |
|---|---|---|
| `backend/agents/query_generator.py` | Добавить поле `detected_category` в dataclass + `from_dict` | Low |
| `backend/prompts/query_generation.py` | Добавить инструкцию по детекции категории в промпт | Low |
| `backend/agents/search_agent.py` | Добавить `_blended_search()`, `blend_results()`, встроить в `search()` | Medium |
| `backend/config.py` | Добавить `CATEGORY_FILTER_ENABLED`, `CATEGORY_FILTER_BLEND_RATIO` | Low |

**No new files.** No changes to frontend, API, or schemas.

---

## Expected Impact

| Metric | Before | After (estimate) |
|---|---|---|
| **Binary correctness** | 27.2% | 32-37% (+5-10 pp) |
| **Отказы «нет в источниках»** | 22.4% | 15-18% (-4-7 pp) |
| **Completeness low (1-2)** | 29.3% | 22-25% |

**Основной профит:** вопросы по ЛК и ДУ (∼25% отказов), где контент есть в KB но buried в operational_content с неправильной категорией.

---

## Alternatives Considered

| Alternative | Why Rejected |
|---|---|
| **Жёсткий фильтр (100%)** | Слишком агрессивно — убьёт recall для cross-domain вопросов |
| **Category-weighted scoring** | Сложнее дебажить, неочевидный эффект. Blended approach прозрачнее |
| **WikiRouter-based классификация** | WikiRouter ещё не реализован. QueryGenerator уже есть и уже принимает category |
| **Только unfiltered + post-filter** | Пост-фильтрация не меняет ранжирование — category-aware search находит совсем другие чанки |
| **Отдельный LLM-вызов для классификации** | Лишние затраты и задержка. Детекция в том же вызове бесплатна |

---

## Open Questions

1. **Blend ratio 0.3 — оптимально?** Может потребоваться тюнинг после первых benchmark-запусков.
2. **Нужен ли `document_type` в фильтре параллельно?** Например, для ЛК-вопросов искать только `faq` и `instruction`. Пока не добавляем — YAGNI.
