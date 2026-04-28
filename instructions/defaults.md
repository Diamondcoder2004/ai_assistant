# Defaults

## Stack

- **Backend:** Python 3.11+ / FastAPI (`backend/`), point d'entrée `api.api:app`
- **Frontend:** Vue 3 + Vite + Pinia + Tailwind (`frontend/`)
- **DB:** Supabase (auth JWT + PostgreSQL chat history)
- **Vector:** Qdrant (port 6333, collection `BASHKIR_ENERGO_PERPLEXITY`)
- **LLM:** RouterAI (`inception/mercury-2`), embeddings `perplexity/pplx-embed-v1-4b`
- **Judge:** `deepseek/deepseek-v3.2`

## Commands

```bash
# Docker
docker-compose up -d --build   # или start.bat
docker-compose down            # или stop.bat

# Backend local
cd backend && uvicorn api.api:app --reload --host 0.0.0.0 --port 8880

# Frontend local
cd frontend && npm run dev

# Tests
cd backend && pytest
cd frontend && npm run test:unit
cd frontend && npm run lint
cd frontend && npm run format
```

## Encoding

- All Cyrillic in UTF-8
- CSV files: `utf-8-sig` (BOM)
- Windows terminal cp1251 cannot display Cyrillic from Python output — always write to UTF-8 file and read it

## Conventions

- **BM25 normalization:** `score / max_score` (classic), no tanh/softmax
- **Prompts are frozen:** do not change style in `backend/prompts/`
- **Supabase** used for both auth (JWT) and chat history storage
- **Hybrid search weights** must sum to 1.0: PREF(0.4) + HYPE(0.3) + LEXICAL(0.2) + CONTEXTUAL(0.1)
