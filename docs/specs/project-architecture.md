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

## Agent Pipeline

```
User Query -> SearchAgent (generates queries -> hybrid search) -> ResponseAgent (LLM response + sources)
```

**Hybrid search:** 4 components (pref/hype/contextual/lexical) × BM25 = final score.

## Key Directories

| Directory | Purpose |
|-----------|---------|
| `backend/` | FastAPI app — agents, tools, prompts, config |
| `backend/agents/` | search_agent, response_agent, query_generator |
| `backend/api/` | REST endpoints (/query, /query/stream, /history, /feedback) |
| `backend/prompts/` | **Frozen** — system prompts, do not modify style |
| `frontend/` | Vue 3 SPA — chat UI, history, profile |
| `api_benchmarks/` | Benchmark runs — CSV with judge evaluations |
| `new_data/` | Benchmark datasets — question + expected answer + source_file |
| `practice/` | Test documents and expert review artifacts |
| `scripts/` | Utilities (PDF conversion, slide generation) |
| `supabase/` | Supabase fork (UI, examples, i18n) |

## Domain Categories

- **ЛК** (Личный кабинет) — Personal account operations
- **ДУ** (Дополнительные услуги) — Additional services (paid)
- **ТПП** (Технологическое присоединение) — Core technical connection process

## Judge Evaluation Criteria

relevance, completeness, helpfulness, clarity, hallucination_risk, context_recall, faithfulness, currency, binary_correctness, overall_score
