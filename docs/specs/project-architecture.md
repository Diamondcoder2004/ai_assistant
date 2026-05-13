# Project Architecture — AI Assistant (Башкирэнерго)

## Purpose

RAG-based intelligent chat-bot for technical connection (технологическое присоединение) support at Bashkirenergo. Serves customer inquiries about: personal account usage, additional services, and the TPP process.

## Architecture

```
Browser -> nginx :80 -> Vue 3 SPA (static)
     \-> nginx :8877 -> FastAPI :8880 -> Qdrant :6333 (vector search)
                                     -> Supabase :8000 (auth + chat history)
                                     -> RouterAI API (LLM + embeddings)
```

## Agent Pipeline (Full Production)

```
User Query
    │
    ▼
WikiRouter (JSON-based document context injection)
    │  - Searches wiki index for relevant documents
    │  - LLM selects top-k by relevance (inception/mercury-2)
    │  - Injects document context before query generation
    │
    ▼
QueryGenerator (search query reformulation)
    │  - Uses document context + user query
    │  - Generates 2-3 targeted search queries
    │  - Model: inception/mercury-2 (speed-critical)
    │
    ▼
SearchAgent (dual-collection hybrid search)
    │  - Searches normative_documents + operational_content
    │  - Hybrid: semantic (pref/hype/contextual) + lexical (BM25)
    │  - Returns top-k chunks with scores
    │
    ▼
ResponseAgent (LLM response generation)
    │  - Synthesizes answer from search results
    │  - Includes source citations with breadcrumbs
    │  - Model: deepseek/deepseek-v4-flash (quality-critical)
    │
    ▼
Final Response (answer + sources)
```

**Hybrid search:** 4 components with configurable weights:
| Component | Weight | Vector Field |
|-----------|--------|------------|
| PREF | 0.4 | `summary` + `content` |
| HYPE | 0.3 | `hypothetical_questions` |
| LEXICAL | 0.2 | BM25 (tokenized text) |
| CONTEXTUAL | 0.1 | Neighbor chunks |

Weights must sum to 1.0. BM25 normalization: `score / max_score` (classic).

## WikiRouter (JSON-based Agentic Knowledge Layer)

The WikiRouter sits between user query and search, acting as an intelligent document selector:

1. **Keyword Search:** Searches the wiki index (`backend/wiki/data/index.json`) for relevant documents by title and keywords
2. **LLM Selection:** Uses `inception/mercury-2` to select top-k (default: 3) most relevant documents
3. **Context Injection:** Brief document context (`wiki_context_short`) is injected before QueryGenerator runs
4. **No Filters:** WikiRouter does NOT pass `document_filters` to search — it guides queries, leaving search unfiltered for maximum recall

**Known pattern:** The `document_filters` parameter in `SearchAgent.search_and_respond()` is kept as optional for future use but currently NOT used in the production pipeline. Dead code in `search_agent.py` has been removed.

## Qdrant Collections

Dual-collection architecture replacing the legacy single collection:

| Collection | Content Types | Purpose |
|---|---|---|
| `normative_documents` | `regulation` | Laws, decrees, regulatory acts |
| `operational_content` | `faq`, `stage_description`, `infomaterial`, `instruction` | FAQs, process stages, guides |

**Vector config:** 2560 dimensions, Cosine distance, HNSW (m=16, ef_construct=100), scalar quantization (int8).

**Indexed fields:** `category` (ЛК/ДУ/ТПП), `document_type`, `client_type` (ФЛ/ИП/ЮЛ), `power_range`.

Full schema: see `docs/specs/qdrant-collections-schema.md`.

## Per-Agent Models

| Agent | Model | Rationale |
|-------|-------|-----------|
| QueryGenerator | `inception/mercury-2` | Fast, intermediate step |
| WikiRouter | `inception/mercury-2` | Fast document selection |
| ResponseAgent | `deepseek/deepseek-v4-flash` | Quality-critical final answer |
| LLM Judge | `deepseek/deepseek-v4-flash` | Evaluation quality |
| LLM Chunking | `deepseek/deepseek-v4-flash` | Semantic quality |

Configured via env vars: `QUERY_GENERATOR_MODEL`, `RESPONSE_AGENT_MODEL`, `JUDGE_LLM_MODEL`, `WIKI_ROUTER_MODEL`.

## Chunking Pipeline

Two-stage pipeline for knowledge base ingestion:

1. **Stage 1 — Pre-split** (`pre_split_for_llm.py`): Token-aware file splitting for LLM context limits (100k tokens per part), strips image references
2. **Stage 2 — LLM Semantic Chunking** (`llm_chunking.py`): `deepseek/deepseek-v4-flash` with JSON output mode splits into atomic fragments + enriches with metadata (summary, hypothetical questions, keywords, entities, breadcrumbs, category)

Output: `enriched_chunks/{normative|operational}/` → Qdrant ingestion.

Full spec: see `docs/specs/chunking-strategy.md`.

## Benchmark Pipeline

```
benchmark.csv (518 questions)
    │
    ▼
benchmark.py → self.rag.query() (full pipeline)
    │
    ▼
Response + Sources + Expected Answer
    │
    ▼
LLM Judge (9 criteria)
    │  - Full source content shown to judge
    │  - Expected answer used for binary correctness
    │  - JSON response_format for structured output
    │
    ▼
Results CSV + Detailed JSON + Stats
```

**Benchmark CSV format:** `question`, `expected_answer`, `source_file` — 518 questions generated by LLM from knowledge base content.

**Run:**
```bash
cd backend
python benchmark.py --csv ../new_data/benchmark_dataset.csv                    # full
python benchmark.py --csv ../new_data/benchmark_dataset.csv --limit 50         # sample
python benchmark.py --csv ../new_data/benchmark_dataset.csv --no-judge         # fast
```

## Judge Evaluation Criteria (9 metrics)

| Criterion | Scale | Description |
|-----------|-------|-------------|
| relevance | 1-5 | How well the answer addresses the question |
| completeness | 1-5 | Coverage of all aspects of the question |
| helpfulness | 1-5 | Usefulness for a Bashkirenergo client |
| clarity | 1-5 | Readability and structure |
| hallucination_risk | 1-5 | Risk of false information (5 = low risk) |
| context_recall | 0-1 | Fraction of answer supported by sources |
| faithfulness | 0-1 | Fraction of claims verifiable against sources |
| currency | 1-5 | Information up-to-dateness |
| binary_correctness | 0-1 | Match with expected answer meaning |
| overall_score | 1-5 | Weighted aggregate |

The judge receives: the question, generated answer, expected answer (from benchmark CSV), and full source content (summary + content for each retrieved chunk). This enables honest evaluation: faithfulness against sources AND correctness against expected.

## Key Directories

| Directory | Purpose |
|-----------|---------|
| `backend/` | FastAPI app — agents, tools, prompts, config |
| `backend/agents/` | search_agent, response_agent, query_generator |
| `backend/api/` | REST endpoints (/query, /query/stream, /history, /feedback) |
| `backend/prompts/` | **Frozen** — system prompts, do not modify style |
| `backend/wiki/` | WikiRouter — JSON index + LLM document selection |
| `backend/chunking/` | Two-stage chunking (pre-split + LLM semantic) |
| `backend/benchmark.py` | Full pipeline benchmark with LLM judge |
| `backend/llm_judge.py` | LLM-as-a-Judge (9 criteria, expected + sources) |
| `frontend/` | Vue 3 SPA — chat UI, history, profile |
| `api_benchmarks/` | Benchmark runs — CSV with judge evaluations |
| `new_data/` | Benchmark datasets + source documents + enriched chunks |
| `practice/` | Test documents and expert review artifacts |
| `scripts/` | Utilities (PDF conversion, slide generation) |
| `supabase/` | Supabase fork (UI, examples, i18n) |

## Domain Categories

- **ЛК** (Личный кабинет) — Personal account operations
- **ДУ** (Дополнительные услуги) — Additional services (paid)
- **ТПП** (Технологическое присоединение) — Core technical connection process

## Related Specs

- `docs/specs/qdrant-collections-schema.md` — Qdrant collections, vectors, indexes
- `docs/specs/chunking-strategy.md` — Two-stage chunking pipeline
- `docs/specs/content-map.md` — Source documents by collection/priority
- `docs/specs/agent-ecosystem.md` — OpenCode agents, skills, plugins

## Critical Constraints

- **Backend entrypoint:** `api.api:app`, NOT `main.py` (main.py is a CLI debug wrapper)
- **BM25 normalization:** `score / max_score` — classic, no tanh/softmax
- **Prompts:** frozen in `backend/prompts/` — do not change writing style
- **Encoding:** all Cyrillic UTF-8, CSV with BOM (`utf-8-sig`), Windows console broken for Cyrillic — write to file
- **Search weights** must sum to 1.0: PREF(0.4) + HYPE(0.3) + LEXICAL(0.2) + CONTEXTUAL(0.1)
- **Collections:** search across `normative_documents` AND `operational_content` simultaneously
