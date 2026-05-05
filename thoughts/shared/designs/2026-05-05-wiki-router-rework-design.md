---
date: 2026-05-05
topic: "Wiki Router Rework — JSON-based Agentic Knowledge Layer"
status: validated
---

# Wiki Router Rework — JSON-based Agentic Knowledge Layer

## Problem Statement

Current wiki implementation has three critical issues:

1. **Empty data layer** — `wiki_concepts` Supabase table is empty; nobody ran `WikiExtractor`
2. **Wrong abstraction** — per-chunk ILIKE search on Supabase is too low-level and fragile
3. **No Langfuse visibility** — `ENABLE_WIKI_ROUTER=false` means wiki never runs; even if enabled, the rigid class produces empty results instantly

The wiki should be a lightweight, zero-dependency knowledge layer that helps downstream agents (QueryGenerator, SearchAgent, ResponseAgent) understand WHERE to look and WHAT business rules apply.

## Constraints

- **No Supabase** for wiki data — remove `wiki_concepts` dependency entirely
- **Zero extra LLM cost for data** — reuse existing `enriched_chunks/` (already processed by deepseek-v4-flash)
- **Fast LLM for routing** — `inception/mercury-2` (no reasoning, just matching)
- **Simple storage** — JSON file loaded into memory
- **Agent pattern** — WikiRouter must be a proper agent with LLM decision-making, not a keyword-only class

## Approach

Build a **JSON-based wiki index** from enriched chunks, then create a **WikiRouter Agent** that:

1. Loads `index.json` into memory at startup
2. Does fast keyword candidate search
3. Calls `inception/mercury-2` to decide relevance and extract business context
4. Returns structured `WikiRoutingResult` for downstream agents

### Why this approach

- **Reuses sunk cost** — enriched chunks already have summaries, keywords, entities
- **No infra** — JSON file, no Redis/MongoDB/Supabase needed for 30-50 entries
- **Agentic** — LLM understands user intent and matches to concepts, not substring search
- **Traceable** — proper Langfuse span as a distinct pipeline step

## Architecture

```
enriched_chunks/{normative,operational}/*.json
    │
    ▼  build_index.py (1-time script)
    │
backend/wiki/data/index.json
    │
    ▼  WikiSearchTool (keyword search)
    │
WikiRouterAgent
  ├── inception/mercury-2: "Какие документы релевантны запросу?"
  └── Output: WikiRoutingResult
          ├─→ QueryGenerator: key_terms, document_hints
          ├─→ SearchAgent: document_filters (category, client_type, power_range)
          └─→ ResponseAgent: business_rules, concept_descriptions
```

## Components

### 1. Wiki Index (`index.json`)

Aggregated per-document entries:

```json
{
  "version": "1.0",
  "generated_at": "2026-05-05T12:00:00Z",
  "documents": [
    {
      "id": "tp-do-15kvt",
      "title": "Технологическое присоединение до 15 кВт",
      "category": "ТПП",
      "source_origin": "operational",
      "source_file": "tp-do-15kvt.md",
      "url": "https://www.bashkirenergo.ru/consumers/gid-po-tekhnologicheskomu-prisoedineniyu/15kvt/",
      "summary": "Порядок ТП для физических лиц с мощностью до 15 кВт...",
      "business_rules": [
        "Срок выполнения: до 4 месяцев",
        "Ставка платы: 550 руб/кВт (ПГКТ РБ №306, 2026)"
      ],
      "client_types": ["ФЛ"],
      "power_ranges": ["<15kW"],
      "key_terms": ["заявка", "договор", "технические условия", "АРБП"],
      "related_files": ["1-shag-podacha-zayavki.md", "passport-tp-do-15kvt.md"],
      "chunk_count": 8
    }
  ]
}
```

**Fields:**
- `id` — machine-friendly identifier
- `title` — human-readable name
- `category` — ЛК / ДУ / ТПП
- `source_origin` — normative / operational
- `source_file` — original markdown filename
- `url` — source URL on bashkirenergo.ru (when available)
- `summary` — 2-4 sentence high-level description
- `business_rules` — list of key rules/prices/deadlines
- `client_types` — applicable client categories
- `power_ranges` — applicable power ranges
- `key_terms` — domain terms for search query enrichment
- `related_files` — linked documents
- `chunk_count` — how many chunks this document was split into

### 2. WikiSearchTool

```python
class WikiSearchTool:
    def __init__(self, index_path: str)
    def search(self, query: str, top_k: int = 5) -> List[WikiDocument]
```

- Loads `index.json` once at init
- Keyword intersection scoring: query words matched against `title`, `summary`, `key_terms`, `business_rules`
- Fast (microseconds), no LLM call

### 3. WikiRouterAgent

```python
class WikiRouterAgent:
    def __init__(self, index_path: str = None, model: str = None)
    def route(self, user_query: str, top_k: int = 3) -> WikiRoutingResult
```

**Pipeline:**
1. `search_tool.search(query)` → candidate documents (top 5)
2. If no candidates → return empty result
3. Format candidates + user query into LLM prompt
4. Call `inception/mercury-2` with JSON output format
5. Parse response into `WikiRoutingResult`

**LLM Prompt (concise):**
```
Запрос клиента: "{user_query}"

Кандидаты из базы знаний:
{formatted_candidates}

Задача:
1. Выбери 1-3 наиболее релевантных документа
2. Извлеки бизнес-правила, применимые к запросу
3. Определи фильтры: category, client_type, power_range
4. Собери key_terms для поисковых запросов

Верни JSON: {selected_docs, business_rules, filters, key_terms, confidence}
```

### 4. WikiRoutingResult

```python
@dataclass
class WikiRoutingResult:
    concepts: List[WikiDocument]       # Выбранные документы
    wiki_context: str                  # Форматированный контекст для агентов
    search_hints: List[str]            # Подсказки для SearchAgent
    combined_keywords: List[str]       # Ключевые слова для QueryGenerator
    document_filters: Dict[str, List[str]]  # Фильтры для Qdrant
    matched_categories: List[str]      # Категории
    confidence: float                  # Уверенность (0-1)
```

## Data Flow

```
User Query
    │
    ▼
WikiRouterAgent.route()
    ├── WikiSearchTool.search() → candidates
    ├── LLM (inception/mercury-2) → relevance scoring + context extraction
    └── WikiRoutingResult
            │
            ├─→ QueryGenerator: wiki_context + key_terms
            ├─→ SearchAgent: document_filters + search_hints
            └─→ ResponseAgent: wiki_context + business_rules
```

## Error Handling

| Failure | Recovery |
|---------|----------|
| `index.json` missing | Graceful: return empty result, log warning |
| LLM timeout | Return keyword-search candidates without LLM refinement |
| LLM returns invalid JSON | Retry once; on second failure, return candidates raw |
| Empty candidates | Return empty result with `confidence=0` |

## Testing Strategy

1. **Build script validation** — run `build_index.py`, verify `index.json` has expected entries
2. **Search tool validation** — test keyword search with known queries, check recall
3. **Agent validation** — test `WikiRouterAgent.route()` with sample queries, verify Langfuse spans
4. **Integration validation** — run full pipeline, confirm wiki context reaches all downstream agents

## Implementation Order

1. `backend/wiki/build_index.py` — build index from enriched_chunks
2. `backend/wiki/data/index.json` — generated artifact
3. `backend/wiki/search_tool.py` — keyword search
4. Rewrite `backend/wiki/wiki_router.py` — agent with LLM
5. Remove `backend/wiki/wiki_store.py` and `backend/wiki/wiki_extractor.py`
6. Update `backend/config.py` — remove Supabase wiki vars, add `WIKI_INDEX_PATH`
7. Update `backend/main.py` — integrate new WikiRouterAgent
8. Update prompts — consume wiki context properly

## Open Questions

- Should `build_index.py` be run manually or as part of deployment pipeline?
- Should we embed `key_terms` with the same embedding model for semantic search fallback?

## Decisions

- **Storage: JSON file** — approved by user, no Redis/MongoDB needed for ~50 entries
- **Data source: enriched_chunks** — approved by user, zero extra LLM cost
- **Agent LLM: inception/mercury-2** — approved by user, fast, no reasoning
