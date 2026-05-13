# Session: ses_2210
Updated: 2026-05-13T02:50:00+00:00

## Goal
Production-ready RAG chatbot for Bashkirenergo technical connection support — achieve >50% binary correctness on benchmark (518 questions) through dual-collection Qdrant search, JSON-based WikiRouter, and retrieval quality improvements.

## Constraints
- **Backend entrypoint:** `api.api:app`, NOT `main.py` (main.py is CLI debug wrapper)
- **Prompts frozen:** do not modify style in `backend/prompts/`
- **BM25 normalization:** `score / max_score` (classic), no tanh/softmax
- **Search weights** must sum to 1.0: PREF(0.4) + HYPE(0.3) + LEXICAL(0.2) + CONTEXTUAL(0.1)
- **Dual Qdrant collections:** `normative_documents` + `operational_content` (both 2560-dim, Cosine, 3 named vectors: pref/hype/contextual)
- **Encoding:** all Cyrillic UTF-8, CSV utf-8-sig (BOM), Windows console broken for Cyrillic; use `sys.stdout.reconfigure(encoding='utf-8')` in Python scripts
- **Supabase** used for JWT auth + chat history (not wiki — replaced by JSON WikiRouter)
- **No git commits without explicit user request**

## Progress
### Done
- [x] WikiRouter: replaced Supabase-wiki storage with local JSON-based agentic knowledge layer (`backend/wiki/data/index.json`)
- [x] WikiRouter observability: added `@observe_rag` tracing to `route()` and `_llm_route()` methods
- [x] Two-stage chunking pipeline: `pre_split_for_llm.py` (token-aware, 100k limit) → `llm_chunking.py` (deepseek-v4-flash, JSON output, semantic enrichment)
- [x] Knowledge base content collected: normative PDFs (35-ФЗ, 861, 442, 1178, 490/22, 186, ГКТ РБ №306), TP stage HTML pages (8 pages), passport PDFs (9 files), FAQ, forms-documents, metadata.json
- [x] Post-retrieval relevance filter (`tools/relevance_filter.py`): lemmatized token overlap, drops zero-overlap chunks
- [x] Adaptive BM25 weight boost: shifts 0.2 from HYPE→LEXICAL when pref_score < 0.7
- [x] Domain-specific query context: WikiRouter injects `client_type` + `power_range` metadata into QueryGenerator context
- [x] Regulatory query boost (×1.15) for `normative_documents` chunks when regulation keywords detected
- [x] Source quality scoring with low-quality warning injected into ResponseAgent prompt when quality < 0.25
- [x] Agent pipeline: WikiRouter → QueryGenerator → SearchAgent (dual-collection) → ResponseAgent (with source citations)
- [x] Chunking: pre-split pipeline fixes (char→token truncation, `cl100k_base` encoding, image stripping)
- [x] Benchmark failure analysis completed (binary_correctness=25.2%, root cause: completeness + context_recall)
- [x] New spec docs: `project-architecture.md`, `qdrant-collections-schema.md`, `chunking-strategy.md`, `content-map.md`, `benchmark-failure-analysis.md`, `agent-ecosystem.md`
- [x] SearchAgent refactored for dual-collection: `search_multi()` replaces `search_multiple()`, Qdrant filter building, per-chunk component score logging in traces
- [x] `main.py`: added `skip_wiki_router`/`skip_query_generator` params for ablation; wiki_context_short for QueryGenerator; `source_quality` passthrough to ResponseAgent
- [x] `ingest_qdrant_contextual.py` refactored to dual-collection routing: `recreate_collections()`, `infer_collection_name()`/`infer_document_type()`, payload indexes, per-collection batch flush
- [x] `config.py`: env vars for adaptive BM25, regulatory boost factor, source quality threshold
- [x] Tests added: dual-collection config, dual-collection search tool, prompt tests, integration tests
- [x] Small benchmark run (20 samples, 15.8% binary correctness, 2026-05-13) — diagnostic quality check
- [x] **llm_chunking.py v6 rewrite**: Complete pipeline overhaul — removed static file-category mapping, LLM now determines ALL metadata (category, collection_name, document_type, power_range, client_type) from content context; dynamic chunk count estimation (len/3500 ±3); post-validation splitting of chunks >8000 chars; `chunk_content` preserved verbatim; Windows console encoding fix
- [x] **Full enriched chunk generation run**: Produced 1007 total chunks (782 normative + 225 operational) from all available source documents

### In Progress
- [ ] Full benchmark re-run needed (~518 questions) to measure combined impact of all retrieval improvements
- [ ] Qdrant ingestion of enriched chunks (782 normative + 225 operational) into dual collections
- [ ] Per-source relevance annotations in benchmark.py (Phase 4, P4.1 — TODO)
- [ ] Knowledge base still missing some priority sources (ДУ/ЛК content, remaining normative PDFs like ПП РФ №184, №24, №937, №86, №85, Распоряжение №147-р)

### Blocked
- (none)

## Key Decisions
- **JSON-based WikiRouter over Supabase wiki**: Local JSON index (`backend/wiki/data/index.json`) with LLM document selection replaces Supabase-stored wiki. Rationale: lower latency, simpler deployment, no DB dependency for routing.
- **Dual Qdrant collections over single collection**: `normative_documents` (regulations) + `operational_content` (FAQ/stages/instructions). Rationale: improved filtering precision, different update cadences, access control.
- **Two-stage chunking over single-stage**: Pre-split (token-aware, 100k limit) → LLM semantic split (deepseek-v4-flash with JSON mode). Rationale: fits LLM context window for large docs, produces atomic self-contained fragments with metadata.
- **llm_chunking.py v6: LLM-determined metadata instead of static mapping**: Removed all hardcoded NORMATIVE_FILES/OPERATIONAL_MD_FILES dictionaries. Rationale: LLM can infer category, collection_name, document_type, power_range, client_type more accurately from document content and filename context than static rules.
- **llm_chunking.py v6: Dynamic chunk count estimation**: Target = len/3500 ±3 chunks per part, with post-validation splitting of any chunk >8000 chars. Rationale: avoids LLM over/under-splitting, produces consistent atomic chunk sizes.
- **BM25 normalization `score/max_score`**: Classic normalization, no tanh/softmax. Rationale: proven approach, keeps score distribution interpretable.
- **Post-retrieval relevance filter**: Drops chunks with zero lemmatized token overlap with query. Rationale: eliminates noise from hybrid search (more sources = lower correctness).
- **Adaptive BM25 boost**: When semantic search confidence is low (<0.7), boost lexical weight from 0.2→0.4. Rationale: BM25 is more reliable for specific terminology queries.
- **Per-agent model assignment**: QueryGenerator/WikiRouter on `inception/mercury-2` (speed), ResponseAgent/Judge on `deepseek/deepseek-v4-flash` (quality).
- **`skip_query_generator` in main pipeline**: Added as configurable flag to enable ablation testing (raw user query vs LLM reformulated). Default: use QueryGenerator.
- **Document type inference in ingestion**: `infer_document_type()` uses LLM-generated `document_type` first, falls back to filename pattern matching. Rationale: avoids LLM re-query cost at ingestion time.
- **Per-component score logging**: `pref_score`, `hype_score`, `contextual_score`, `bm25_score` from each chunk's metadata logged in Langfuse traces. Rationale: enables diagnosis of which search component drives irrelevant results.

## Next Steps
1. Ingest enriched chunks (782 normative + 225 operational) into Qdrant dual collections via `ingest_qdrant_contextual.py`
2. Run full benchmark (~518 questions) to measure combined impact of all retrieval improvements + new chunking pipeline
3. Implement per-source relevance annotations in benchmark.py (P4.1)
4. Address remaining P0-P1 knowledge base gaps (ДУ/ЛК content, remaining normative PDFs: ПП РФ №184, №24, №937, №86, №85, Распоряжение №147-р)
5. Validate WikiRouter document selection quality via Langfuse traces
6. Merge `beta` branch improvements to `main` after benchmark validation

## File Operations
### Read
- `thoughts/ledgers/CONTINUITY_ses_2210.md`
- `api_benchmarks/latest_stats.json`
- `api_benchmarks/benchmark_20260513_001947.csv`
- `backend/chunking/enriched_chunks/{normative|operational}/*.json`

### Modified
- **`backend/chunking/llm_chunking.py`** — v6 rewrite: removed static mapping, LLM-determined metadata (category, collection_name, document_type, power_range, client_type), dynamic chunk count (len/3500 ±3), post-validation for >8000-char chunks, verbatim content preservation, Windows console encoding fix
- `backend/agents/search_agent.py` — Legacy collection → dual-collection; per-chunk score logging; relevance filter wiring; regulatory query boost; source quality call; @observe_rag; skip_query_generator
- `backend/agents/response_agent.py` — Source quality confidence check in user prompt
- `backend/agents/query_generator.py` — Domain-specific query context integration
- `backend/main.py` — Wiki context enrichment with client_type/power_range; skip_wiki_router/skip_query_generator params; source_quality passthrough
- `backend/tools/search_tool.py` — Adaptive BM25 weight boost; `search_multi()` with Qdrant filter support
- `backend/tools/relevance_filter.py` — NEW: post-retrieval filter, regulatory keyword detection, source quality scoring
- `backend/wiki/wiki_router.py` — JSON-based knowledge layer; @observe_rag tracing
- `backend/config.py` — Env vars for adaptive BM25, regulatory boost, source quality threshold
- `backend/chunking/pre_split_for_llm.py` — NEW: token-aware file splitting (cl100k_base, 100k limit)
- `backend/qdrant_ingest/ingest_qdrant_contextual.py` — Dual-collection routing, `recreate_collections()`, `infer_collection_name()`/`infer_document_type()`, payload indexes, per-collection batch flush
- `backend/benchmark.py` — Dual-collection benchmark pipeline
- `backend/llm_judge.py` — 9-criteria evaluation with source content + expected answer
- `backend/api/endpoints.py` — API endpoint refinements
- `backend/prompts/query_generation.py` — Prompt adjustments for dual-collection context
- `backend/prompts/system_prompt.py` — Response mode support (brief/standard/detailed)
- `backend/requirements.txt` — Dependency updates
- `backend/Dockerfile` — Build updates
- `docker-compose.yml` — Service configuration updates
- `docs/specs/project-architecture.md` — Updated for WikiRouter + dual-collection + agent pipeline
- `docs/specs/chunking-strategy.md` — (needs update for v6 pipeline changes)
- `AGENTS.md` — Updated project contract
- `backend/chunking/enriched_chunks/normative/` — 782 enriched chunk JSON files (35-ФЗ parts 1-5, 861 parts 1-8, 442 parts 1-15, 1178 parts 1-2, 490/22, 186 parts 1-2, gkt-rb-306, normative-base, passport-tp-15-150kvt, tp-do-15kvt)
- `backend/chunking/enriched_chunks/operational/` — 225 enriched chunk JSON files (1-shag, 2-shag, 3-shag, gid-po-tp, faq-kt-tpp-2026, both pamyatkas, all 9 passports, all TP stage pages, LK instruction, DU catalog, calc, cok, map, status, forms-documents, normative-base)
- `backend/chunking/raw_responses_v6/` — NEW: raw LLM responses from v6 chunking run
- `backend/chunk_stats.py` — NEW: chunk statistics script
- `backend/analyze_v3.py` — NEW: chunk analysis script
- `backend/tests/test_config_dual_collections.py` — NEW
- `backend/tests/test_search_tool_dual.py` — NEW
- `backend/tests/test_search_agent_filters.py` — NEW
- `backend/tests/test_prompts_dual_collections.py` — NEW
- `backend/tests/test_ingest_dual_collections.py` — NEW
- `backend/tests/test_integration_dual_collections.py` — NEW
- `backend/tests/test_price_list_formatter.py` — NEW
- `backend/utils/langfuse_tracer.py` — NEW: Langfuse tracing utility
- `backend/agents/price_list_formatter.py` — NEW: price list formatting agent

## Critical Context
- **Binary correctness was 25.2%** (last full benchmark). Latest small run (20 samples, 2026-05-13) showed 15.8% — tiny sample, not statistically significant.
- **llm_chunking.py v6 rewrite is the major change in this session**: Removed all hardcoded file-to-metadata mapping. LLM now determines ALL metadata fields dynamically from document content + filename context. Dynamic chunk count (target len/3500 ±3 chunks per part). Post-validation splits any chunk >8000 chars into smaller pieces. `chunk_content` is now preserved verbatim (no truncation/paraphrasing). Keywords merged into single field combining key phrases + named entities.
- **Enriched chunks: 782 normative + 225 operational = 1007 total** — generated in this session with v6 pipeline. Data sources covered: all 7 PDF-regulations, all 8 TP stage HTML pages, all 9 passport PDFs, FAQ, forms-documents, LK instructions, DU catalog, both pamyatkas, calc, cok, map, status, normative-base.
- **Pipeline not yet ingested into Qdrant** — enriched chunks sitting in `enriched_chunks/{normative|operational}/` as JSON files, awaiting ingestion run via `ingest_qdrant_contextual.py`.
- **WikiRouter replaced Supabase wiki** — now uses `backend/wiki/data/index.json` with keyword search + LLM selection. No longer passes `document_filters` to search.
- **Two Qdrant collections** — `normative_documents` (regulations) and `operational_content` (FAQ/instructions/stages). Both use `perplexity/pplx-embed-v1-4b` (2560-dim, Cosine). Three named vectors per collection: pref, hype, contextual.
- **Source data**: `new_data/source/normative/` — 7 PDFs (35-ФЗ, 861, 442, 1178, 490/22, 186, ГКТ РБ №306); `new_data/source/operational/` — HTML→Markdown pages, FAQ, passports, pamyatkas, forms-documents.
- **Many files uncommitted** on `beta` branch — ~30 modified files + many untracked files (enriched chunks, raw_responses_v6, benchmark results, tests, analysis scripts, spec docs).
- **Latest HEAD**: `6cbcb6c` "feat(wiki): replace Supabase wiki with JSON-based agentic knowledge layer" — uncommitted work on top includes the llm_chunking.py v6 rewrite and full enriched chunk generation.

## Working Set
- Branch: `beta`
- Key files: `backend/chunking/llm_chunking.py`, `backend/chunking/enriched_chunks/`, `backend/chunking/raw_responses_v6/`, `backend/chunking/pre_split_for_llm.py`, `backend/qdrant_ingest/ingest_qdrant_contextual.py`, `backend/main.py`, `backend/agents/search_agent.py`, `backend/agents/response_agent.py`, `backend/agents/query_generator.py`, `backend/wiki/wiki_router.py`, `backend/tools/search_tool.py`, `backend/tools/relevance_filter.py`, `backend/config.py`, `backend/benchmark.py`, `new_data/source/`, `docs/specs/`
