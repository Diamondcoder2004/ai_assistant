# AGENTS.md — AI Assistant (Башкирэнерго)

## Primary Goal

RAG chat-bot for **technical connection support** (технологическое присоединение к электросетям) at Bashkirenergo. Answers customer questions about personal account operations, additional paid services, and the TPP process. Accuracy is critical — incorrect procedure advice has real operational consequences.

## Repository Structure

```
ai_assistant/
├── backend/              # FastAPI — agents, tools, prompts, config
│   ├── agents/           # SearchAgent + ResponseAgent + QueryGenerator
│   ├── api/              # REST: /query, /query/stream, /history, /feedback
│   ├── prompts/          # FROZEN — do not modify style
│   ├── tools/            # Hybrid search tool (Qdrant + BM25)
│   └── utils/            # Embeddings, debug logging
├── frontend/             # Vue 3 + Vite + Pinia + Tailwind SPA
├── api_benchmarks/       # Benchmark results (CSV with judge scores)
├── new_data/             # Benchmark datasets (question + expected + source)
├── practice/             # Test documents, expert review artifacts (.docx)
├── docs/specs/           # Durable project specifications
├── .opencode/            # OpenCode layer: agents, skills
│   ├── agents/           # Role-based sub-agents (doc-specialist)
│   └── skills/           # Playbooks (matt-*, doc-specialist, docx, pdf, pptx)
├── instructions/         # Base rules loaded by opencode.json
├── AGENTS.md             # This file — project contract
├── opencode.json         # OpenCode control plane
└── SKILL.md              # Legacy detailed guide (being absorbed into docs/specs/)
```

## Architecture

```
Browser → nginx :80 → Vue SPA (static files)
Browser → nginx :8877 → FastAPI :8880
                           ├── Qdrant :6333  (vector search, collection: BASHKIR_ENERGO_PERPLEXITY)
                           ├── Supabase :8000 (JWT auth + PostgreSQL chat history)
                           └── RouterAI API   (LLM: inception/mercury-2, embeddings: pplx-embed-v1-4b)
```

**Agent pipeline:** User Query → SearchAgent (generates search queries → hybrid search) → ResponseAgent (LLM response with sources).

## Delivery Workflow

1. **Clarify the task** — what domain category? ЛК / ДУ / ТПП?
2. **Consult `docs/specs/`** for relevant architecture or domain spec before modifying code
3. **Implement minimal working slice** — one vertical slice at a time
4. **Test**: `cd backend && pytest` + `cd frontend && npm run lint && npm run test:unit`
5. **Update documentation** if architecture/hard rules changed

## Task Routing by Role

| Task type | Use |
|-----------|-----|
| Code review | Load `adk-code-review-pr` skill |
| Feature development | Load `adk-dev-build` skill |
| Refactoring | Load `adk-dev-refactor` skill |
| Document creation (docx/pdf/pptx) | Load `doc-specialist` skill |
| Architecture improvement | Load `matt-improve-architecture` skill |
| TDD | Load `matt-tdd` skill |
| Planning/brainstorming | Load `matt-grill-me` skill |
| Domain modeling | Load `matt-ubiquitous-language` skill |
| PRD generation | Load `matt-to-prd` skill |
| Benchmark analysis | See `docs/specs/project-architecture.md` |

## Critical Constraints

- **Backend entrypoint:** `api.api:app`, NOT `main.py` (main.py is a CLI debug wrapper)
- **BM25 normalization:** `score / max_score` — classic, no tanh/softmax
- **Prompts:** frozen in `backend/prompts/` — do not change writing style
- **Encoding:** all Cyrillic UTF-8, CSV with BOM (`utf-8-sig`), Windows console broken for Cyrillic — write to file
- **Search weights** must sum to 1.0: PREF(0.4) + HYPE(0.3) + LEXICAL(0.2) + CONTEXTUAL(0.1)
- **Supabase** serves dual role: JWT auth + chat history storage
- **Config:** copy `.env.example` → `.env`, fill `ROUTERAI_API_KEY`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_JWT_SECRET`

## Definition of Success

A correct answer means: the model's response matches the expected procedure, uses correct terminology, respects domain constraints (ФЛ/ИП/ЮЛ categories, power limits, voltage classes), and does not hallucinate non-existent features or steps.
