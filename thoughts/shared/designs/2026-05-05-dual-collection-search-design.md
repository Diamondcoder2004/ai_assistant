# Дизайн: Двойная коллекция Qdrant с фильтруемым параллельным поиском

## Дата
2026-05-05

## Статус
Draft

## 1. Проблема (Problem Statement)

Текущая архитектура использует одну коллекцию Qdrant (`BASHKIR_ENERGO_PERPLEXITY_V2`) для ВСЕХ типов контента. Нормативные документы (законы, постановления, приказы) смешиваются с операционными (FAQ, инструкции, описания этапов), что приводит к:

- **Зашумлению поиска** — косинусное расстояние между юридическим текстом и бытовым вопросом слабое, нормативные чанки попадают в выдачу по операционным запросам и наоборот
- **Невозможности целенаправленного поиска** — нельзя сказать «ищи только в нормативе» или «только в FAQ»
- **Блокировке раздельного обновления** — добавление новых FAQ требует переиндексации всей коллекции, включая законы
- **Слабой фильтрации** — поля `client_type`, `power_range`, `category`, `document_type` не проиндексированы и не используются при поиске

Текущий бенчмарк: 39% точности. Основные ошибки — тарифы, льготы, категории мощности — требуют точного попадания в нормативные документы, а не в операционные FAQ.

## 2. Ограничения (Constraints)

- **Не трогаем `llm_chunking`**: enriched chunks уже сгенерированы (482 normative + 222 operational) в `backend/chunking/enriched_chunks/` с полем `source_origin`
- **Prompts frozen**: стиль промптов в `backend/prompts/` не меняем, только добавляем информацию о коллекциях
- **BM25 нормализация**: `score / max_score` — остаётся без изменений
- **Веса поиска**: PREF(0.4) + HYPE(0.3) + LEXICAL(0.2) + CONTEXTUAL(0.1) = 1.0 — без изменений
- **Wiki Router уже генерирует фильтры**: `document_filters` с `client_type`, `power_range`, `category` — используем их
- **Backend entrypoint**: `api.api:app` — не меняется
- **Chunking pipeline не перезапускается**: работаем с существующими чанками

## 3. Подход (Approach)

**Решение: Две коллекции Qdrant + параллельный поиск с Qdrant-фильтрами**

Заменяем одну переменную `COLLECTION_NAME` на две: `NORMATIVE_COLLECTION_NAME` и `OPERATIONAL_COLLECTION_NAME`. Ingestion раскидывает чанки по коллекциям на основе `source_origin`. Runtime search — параллельный запрос в обе коллекции с Qdrant-фильтрами по полям `category`, `client_type`, `power_range`, `document_type`. Wiki Router предоставляет фильтры, поиск их применяет.

**Почему именно этот подход:**
- Минимальные изменения — enriched chunks уже разделены по папкам, Wiki Router уже вычисляет фильтры
- Qdrant нативные фильтры быстрее пост-фильтрации в Python — отсев происходит на уровне индекса
- Параллельный поиск не удваивает latency — запросы уходят одновременно
- Разделение коллекций позволяет независимое обновление и разные стратегии кеширования

**Альтернативы, которые отбросил:**
- *Оставить одну коллекцию с полем `document_type`* — не решает проблему зашумления, косинусное расстояние всё равно смешивает норматив и операционку
- *CLIP-style классификатор запросов* — не нужен, Wiki Router даёт более точный routing через бизнес-концепции и уже интегрирован
- *Переиндексация всех чанков* — избыточно, `source_origin` уже в каждом JSON

## 4. Архитектура (Architecture)

```
User Query
    ↓
Wiki Router → document_filters + wiki_context
    ↓
Query Generator (обогащённый wiki_context)
    ↓
Search Agent → параллельный поиск (ThreadPoolExecutor)
    ├── Qdrant.normative_documents + query_filter(client_type, power_range, category)
    └── Qdrant.operational_content + query_filter(client_type, power_range, category)
    ↓
Merge + rank (единый BM25 + hybrid score)
    ↓
Response Agent (LLM + источники с collection_name)
```

**Что НЕ меняется:**
- `llm_chunking.py` — не трогаем
- `wiki_extractor.py` и `wiki_store.py` — уже работают правильно
- `response_agent.py` — формат результатов не меняется
- Frontend — не трогаем

## 5. Компоненты (Components)

### 5.1. `.env` и `.env.example`

**Было:**
```
COLLECTION_NAME=BASHKIR_ENERGO_PERPLEXITY_V2
```

**Стало:**
```
NORMATIVE_COLLECTION=normative_documents
OPERATIONAL_COLLECTION=operational_content
CHUNKS_DIR=chunking/enriched_chunks
```

Переменная `COLLECTION_NAME` остаётся deprecated для обратной совместимости (fallback на `NORMATIVE_COLLECTION_NAME`).

### 5.2. `config.py`

Добавляем:
- `NORMATIVE_COLLECTION_NAME` — из env, дефолт `"normative_documents"`
- `OPERATIONAL_COLLECTION_NAME` — из env, дефолт `"operational_content"`
- `CHUNKS_DIR` — из env, дефолт `"chunking/enriched_chunks"`
- `COLLECTION_NAME` — оставляем deprecated, fallback на `NORMATIVE_COLLECTION_NAME`

### 5.3. `ingest_qdrant_contextual.py`

**Основные изменения:**

1. **`recreate_collections()` (было `recreate_collection()`)**:
   - Создаёт обе коллекции с идентичной векторной схемой: `pref`, `hype`, `contextual` (2560 dim, Cosine)
   - Создаёт payload индексы: `category`, `document_type`, `client_type`, `power_range` — для обеих коллекций

2. **`load_all_chunks()`**:
   - Уже читает подпапки (normative, operational) — без изменений
   - Добавляем вычисление `collection_name` на основе `source_origin`:
     - `normative` → `normative_documents`
     - `operational` → `operational_content`

3. **Payload enrichment** — добавляем поля, которых не было:
   - `breadcrumbs` — из chunk (уже есть в JSON, не клали в payload)
   - `document_type` — маппинг: normative → `regulation`, operational → из `document_source` или filename
   - `collection_name` — из вычисленного значения
   - `client_type` — дефолт `"any"` (позже обогатим через LLM или metadata)
   - `power_range` — дефолт `"any"`

4. **Upsert routing**: точки upsert-ятся в соответствующую коллекцию по `collection_name`

5. **Статистика в конце**: раздельный count по обеим коллекциям

### 5.4. `search_tool.py`

**Новая архитектура:**

```python
class SearchTool:
    def __init__(self):
        self.client = QdrantClient(...)
        self.collections = [
            config.NORMATIVE_COLLECTION_NAME,
            config.OPERATIONAL_COLLECTION_NAME,
        ]
        self.embedder = get_routerai_embedder()
        self.bm25 = None
        # ...

    def load(self, force=False):
        """Загружает BM25 из ОБЕИХ коллекций с единым пространством."""
        # scroll по обеим коллекциям, единый массив документов

    def search(
        self,
        request: SearchRequest,
        collection_name: Optional[str] = None,
        qf_filter: Optional[models.Filter] = None,
    ) -> List[SearchResult]:
        """Поиск в указанной коллекции с опциональным Qdrant-фильтром."""
        # collection_name = collection_name or config.NORMATIVE_COLLECTION_NAME
        # query_points с параметром query_filter для pref, hype, contextual

    def search_multi(
        self,
        queries: List[str],
        qf_filter: Optional[models.Filter] = None,
        k: int = 10,
        weights: Optional[Dict[str, float]] = None,
    ) -> List[SearchResult]:
        """Параллельный поиск по ОБЕИМ коллекциям с мержем результатов."""
        # ThreadPoolExecutor для параллельных запросов
        # merge + сортировка по гибридному score
```

**Ключевые детали:**

- **BM25 единый**: `load()` скроллит обе коллекции в единый массив документов для глобального BM25 ранжирования
- **Qdrant-фильтры** передаются напрямую в `query_points(query_filter=...)` — отсев на уровне индекса
- **Параллельный поиск**: `ThreadPoolExecutor` с двумя воркерами для одновременного запроса в обе коллекции
- **Каждый результат** содержит поле `collection_name` для отслеживания происхождения
- **Мерж**: все результаты сортируются по `score_hybrid` (единое пространство), берутся top-K

### 5.5. `search_agent.py`

**Изменения:**

- Метод `search()` принимает `document_filters: Optional[Dict[str, List[str]]]`
- Преобразует `document_filters` в `models.Filter`:
  ```python
  conditions = []
  if "category" in filters:
      conditions.append(FieldCondition(key="category", match=MatchAny(any=filters["category"])))
  if "client_type" in filters:
      # Добавляем "any" чтобы не исключать общие документы
      types = filters["client_type"] + (["any"] if "any" not in filters["client_type"] else [])
      conditions.append(FieldCondition(key="client_type", match=MatchAny(any=types)))
  if "power_range" in filters:
      ranges = filters["power_range"] + (["any"] if "any" not in filters["power_range"] else [])
      conditions.append(FieldCondition(key="power_range", match=MatchAny(any=ranges)))
  qf_filter = Filter(must=conditions) if conditions else None
  ```
- Вызывает `search_tool.search_multi(queries, qf_filter=qf_filter)` вместо `search_tool.search_multiple()`
- `_retry_search()` тоже использует фильтры
- Добавляет `collection_name` в логирование результатов

### 5.6. Промпты (`system_prompt.py`, `query_generation.py`)

**`system_prompt.py`** — добавляем секцию:

```
## База знаний (две коллекции)

- **normative_documents** — законы, постановления, приказы, нормативные акты
  (тарифы, льготы, категории заявителей, технические требования)
- **operational_content** — FAQ, инструкции, описания этапов, памятки
  (процедуры подачи заявок, этапы ТП, дополнительные услуги)

При поиске учитывай: тарифы и законы → normative, процедуры и FAQ → operational.
```

**`query_generation.py`** — в промпт добавляем подсказку:

```
## Выбор коллекций

При поиске нормативной информации (тарифы, законы, ставки, льготы, категории) —
указывай в search_params поле "prefer_collection": "normative".
При поиске процедур (как подать, этапы, документы, FAQ) —
указывай "prefer_collection": "operational".
Если не уверен — "prefer_collection": "all".
```

## 6. Поток данных (Data Flow)

### 6.1. Ingestion (однократно)

```
enriched_chunks/
├── normative/*.json (482) → Qdrant.normative_documents
└── operational/*.json (222) → Qdrant.operational_content

Обе коллекции:
  - Векторы: pref, hype, contextual (2560 dim, Cosine)
  - Индексы: category, document_type, client_type, power_range
  - Payload: chunk_id, source_file, content, summary, breadcrumbs,
             keywords, entities, category, collection_name, document_type,
             client_type, power_range
```

### 6.2. Runtime поиск

```
User: "Сколько стоит подключение 10 кВт для частного дома?"

WikiRouter.route(query)
  → concepts: ["ТПП для ФЛ до 15 кВт", "Тарифы и стоимость ТПП"]
  → document_filters: {client_type: ["ФЛ"], power_range: ["<15kW"], category: ["ТПП"]}
  → wiki_context: "Концепция: ТПП для ФЛ до 15 кВт ..."

QueryGenerator.generate(query, wiki_context)
  → queries: ["стоимость ТП до 15 кВт для физических лиц",
              "тарифы на подключение 10 кВт ФЛ Башкирэнерго",
              "льготная ставка ТП ФЛ до 15 кВт 2026"]
  → search_params: {prefer_collection: "normative", strategy: "separate"}

SearchAgent.search(query, document_filters)
  → преобразует filters в Qdrant Filter:
    must=[
      category IN ["ТПП"],
      client_type IN ["ФЛ", "any"],
      power_range IN ["<15kW", "any"]
    ]
  → SearchTool.search_multi(queries, qf_filter)

Parallel:
  ├── Qdrant.normative_documents ← query_vector + filter
  │     возвращает: ПП №861 (тарифы), ГКТ РБ №306 (ставки 2026)
  └── Qdrant.operational_content ← query_vector + filter
        возвращает: FAQ "Сколько стоит подключение", памятка ТП

Merge + rank → top-10 результатов
  → ResponseAgent отвечает
```

## 7. Обработка ошибок (Error Handling)

| Ситуация | Поведение |
|----------|-----------|
| Одна коллекция пуста (0 points) | Поиск продолжается по второй, warning в лог |
| Обе коллекции пусты | Пустой результат, как сейчас |
| Qdrant timeout на одной коллекции | Результаты со второй + warning |
| Некорректное поле в фильтре | Fallback — поиск без фильтра, error в лог |
| Wiki Router не дал фильтров | Поиск без фильтра по обеим коллекциям |
| `COLLECTION_NAME` всё ещё в `.env` | Fallback на `NORMATIVE_COLLECTION_NAME` для обратной совместимости |

## 8. Стратегия тестирования (Testing Strategy)

### 8.1. Ingestion validation
- Запустить `python -m qdrant_ingest.ingest_qdrant_contextual`
- Проверить: `normative_documents.count` ≈ 482, `operational_content.count` ≈ 222
- Проверить payload индексы через `client.get_collection()`

### 8.2. Search без фильтров
- Поиск без фильтра по обеим коллекциям
- Проверить что результаты есть из обеих коллекций (поле `collection_name`)

### 8.3. Search с фильтрами
- `client_type=ФЛ` → все результаты должны иметь `client_type` ∈ {ФЛ, any}
- `power_range=<15kW` → аналогично
- `category=ТПП` → все результаты ТПП

### 8.4. BM25 единое ранжирование
- Проверить что `score_lexical` сравнимы между коллекциями (единый BM25)

### 8.5. Pytest существующие тесты
- `backend/pytest` — все тесты должны проходить
- Мокаем новый метод `search_multi` если нужно

## 9. Файлы для изменений

### Модифицируемые

| Файл | Что меняется |
|------|-------------|
| `.env` | `COLLECTION_NAME` → `NORMATIVE_COLLECTION` + `OPERATIONAL_COLLECTION` + `CHUNKS_DIR` |
| `.env.example` | То же самое |
| `backend/config.py` | Две коллекции + `CHUNKS_DIR` |
| `backend/qdrant_ingest/ingest_qdrant_contextual.py` | Две коллекции, routing, payload enrichment, индексы |
| `backend/tools/search_tool.py` | `search_multi()`, `load()` из двух коллекций, фильтры |
| `backend/agents/search_agent.py` | Приём и преобразование `document_filters`, вызов `search_multi` |
| `backend/prompts/system_prompt.py` | Секция о двух коллекциях |
| `backend/prompts/query_generation.py` | Подсказки по выбору коллекций |

### Не трогаем

| Файл | Причина |
|------|---------|
| `backend/chunking/llm_chunking.py` | Чанки уже готовы |
| `backend/wiki/*` | Уже работает правильно |
| `backend/agents/response_agent.py` | Формат результатов не меняется |
| `frontend/**` | API не меняется |

## 10. Открытые вопросы (Open Questions)

1. **`client_type` и `power_range` в payload**: сейчас дефолт `"any"` для всех чанков. Нужен ли скрипт для обогащения этих полей на основе содержимого чанков? Предложение: сначала проиндексировать как есть, а потом запустить LLM-обогащение (аналогично wiki_extractor) для проставления точных значений.

2. **Коллекция `BASHKIR_ENERGO_PERPLEXITY` (V1)** в Qdrant: удалять или оставить? Предложение: оставить до валидации новых коллекций, потом удалить.

3. **`COLLECTION_NAME` в docker-compose.yml**: нужно обновить ENV переменные в контейнере backend. Сейчас там `COLLECTION_NAME=${COLLECTION_NAME:-BASHKIR_ENERGO_PERPLEXITY}` — заменить на две переменные.

4. **Benchmark после миграции**: ожидаемое улучшение — категорийные и тарифные вопросы должны идти в нормативную коллекцию, процедурные — в операционную. Цель: +10% точности (39% → 49%).

## 11. Порядок выполнения

1. **`.env` + `config.py`**: добавить новые переменные, сохранить backward compatibility
2. **`ingest_qdrant_contextual.py`**: переписать под две коллекции, запустить ingest
3. **`search_tool.py`**: новый метод `search_multi` с фильтрами и параллельным поиском
4. **`search_agent.py`**: интеграция document_filters из Wiki Router
5. **Промпты**: обновить system_prompt и query_generation
6. **Тестирование**: pytest + ручная проверка поиска
7. **docker-compose.yml**: обновить ENV переменные
8. **Benchmark**: запустить полный бенчмарк, сравнить с baseline 39%
