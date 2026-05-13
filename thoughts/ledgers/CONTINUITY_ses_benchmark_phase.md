# Session: Benchmark & Retrieval Quality Improvement Phase
Updated: 2026-05-13T16:00:00Z

## Goal
Fix the Bashkirenergo RAG assistant's low binary correctness (25.2%) through retrieval quality improvements, WikiRouter elimination, and post-retrieval relevance filtering.

## Constraints
- **Search weights must sum to 1.0**: PREF(0.4) + HYPE(0.3) + LEXICAL(0.2) + CONTEXTUAL(0.1)
- **BM25 normalization**: `score / max_score` — classic, no tanh/softmax
- **Prompts frozen**: in `backend/prompts/` — do not change writing style
- **Backend entrypoint**: `api.api:app`, NOT `main.py`
- **Dual Qdrant collections**: `normative_documents` + `operational_content`
- **Controller**: `inception/mercury-2` (QueryGen, WikiRouter), `deepseek/deepseek-v4-flash` (ResponseAgent, Judge)

## Progress
### Done
- [x] **Benchmark Failure Analysis** — Root cause: completeness + context_recall are dominant predictors; more retrieved chunks → lower correctness
- [x] **Phase 1 — Observability**: WikiRouter tracing (`@observe_rag`), per-chunk relevance score logging
- [x] **Phase 2 — Retrieval Quality**: Post-retrieval relevance filter (`tools/relevance_filter.py`), adaptive BM25 boost, domain-specific query expansion (client_type + power_range in wiki_context_short)
- [x] **Phase 3 — Failure Pattern Fixes**: FAQ-to-regulation linking (regulatory query boost, `REGULATORY_QUERY_BOOST_FACTOR=1.15`), source quality scoring (`SOURCE_QUALITY_THRESHOLD=0.25`)
- [x] **WikiRouter removal design** — design doc validated, plan written
- [x] **WikiRouter files deleted** — entire `backend/wiki/` directory and 7 test files deleted from working tree
- [x] **New specs written**: `benchmark-failure-analysis.md`, `content-map.md`, `qdrant-collections-schema.md`, `agent-ecosystem.md`
- [x] **Dual-collection migration**: collections created, search tool updated, dual-collection tests passing
- [x] **Two-stage chunking** (`pre_split_for_llm.py` + `llm_chunking.py`): token-aware pre-split (100k token limit), deepseek-v4-flash semantic chunking, enriched output to `enriched_chunks/{normative|operational}/`

### In Progress
- [ ] **WikiRouter reference cleanup** — `wiki_context` and `document_filters` parameters still present in `search_agent.py`, `search_tool.py`, `response_agent.py`, `query_generator.py` — need to strip vestigial params from code
- [ ] **Final benchmark run** after WikiRouter removal + all Phase 2/3 improvements applied
- [ ] **`project-architecture.md` de-WikiRouter'ing** — currently updated spec still references WikiRouter
- [ ] **Stage and commit** all working tree changes as a coherent commit

### Blocked
- **No current blockers** — working tree has all changes applied but uncommitted

## Key Decisions
- **Remove WikiRouter entirely** (not just disable): Too much dead code (`document_filters` always None, `business_rules` always empty), adds latency/cost per query for uncertain value, and `document_filters` conflicts with the need to search all categories for any query
- **Post-retrieval relevance filter over re-ranking**: Token overlap via pymorphy3 (same lib as BM25) — zero LLM latency, drops chunks with zero shared lemmas between query and content
- **Adaptive BM25 weight boost**: When max `pref_score < 0.7`, shift 0.2 weight from HYPE → LEXICAL (0.2→0.4) — if semantic search is uncertain, lean harder on lexical matching
- **Regulatory query boost**: Detect regulatory keywords, boost `normative_documents` chunk scores ×1.15 — many questions look like FAQ but are answered in regulations
- **Dual collections with 2560-dim embeddings**: Split regulatory (`normative_documents`) from operational (`operational_content`) for independent tuning

## Next Steps
1. Complete `wiki_context` and `document_filters` parameter removal from all agent files
2. Run final benchmark to measure binary correctness improvement
3. Stage and commit all working tree changes
4. Run full benchmark (518 questions) with LLM Judge on cleaned pipeline
5. Phase 4: per-source relevance annotations in benchmark.py for deeper diagnostics

## File Operations
### Read
- `thoughts/shared/designs/2026-05-13-remove-wikirouter-design.md`
- `thoughts/shared/plans/2026-05-13-remove-wikirouter.md`
- `docs/specs/benchmark-failure-analysis.md`
- `docs/specs/project-architecture.md`
- `backend/main.py`
- `backend/agents/search_agent.py`
- `backend/tools/search_tool.py`
- `backend/tools/relevance_filter.py`
- `thoughts/ledgers/CONTINUITY_ses_21cc.md`
- `thoughts/ledgers/CONTINUITY_ses_21ba.md`

### Modified
- Several previous ledgers (were broken/malformed)
- `backend/wiki/` directory (deleted working tree — 6 files)
- `backend/tests/test_wiki_*.py` (deleted working tree — 7 files)
- `backend/main.py` (WikiRouter import and instantiation removed)
- `backend/config.py` (WikiRouter config section removed)
- `backend/agents/search_agent.py` (relevance filter, score logging, regulatory boost)
- `backend/agents/response_agent.py` (source quality warning)
- `backend/agents/query_generator.py` (param cleanup)
- `backend/tools/search_tool.py` (adaptive BM25 boost, filter builder)
- `backend/tools/relevance_filter.py` (NEW — post-retrieval filter + regulatory detection + source scoring)
- `backend/benchmark.py` (restructured for dual collections)
- `backend/llm_judge.py` (dual-collection aware evaluation)
- `backend/chunking/llm_chunking.py` (token-based safety truncation)
- `backend/chunking/Mardown_splitter.py` (pre-split fixes)
- `backend/prompts/system_prompt.py` (response mode support)
- `backend/prompts/query_generation.py` (domain metadata context)
- `docs/specs/project-architecture.md` (de-WikiRouter'd, dual collection docs)
- `docker-compose.yml` (Supabase service added)

## Critical Context
- **WikiRouter deletion is DESIGN doc + PLAN committed** (`815bdc2`) but working tree deletions are NOT staged yet
- **Better retrieval correlated with higher binary correctness** — best results when 1-2 highly relevant chunks instead of 5+ noisy ones
- **Phase 2/3 config keys** in `config.py`: `ADAPTIVE_BM25_BOOST`, `REGULATORY_QUERY_BOOST`, `SOURCE_QUALITY_THRESHOLD` — all loaded from env with defaults
- **Benchmark dataset** has 518-541 questions in `new_data/benchmark_dataset.csv`
- **Latest benchmark run**: `api_benchmarks/benchmark_20260513_001947.csv` — post-Phase 2/3, pre-WikiRouter removal
- **Encoding**: All Cyrillic UTF-8, CSV with BOM (`utf-8-sig`)
- **No A/B test** was ever done on `wiki_context_short` — its impact is unmeasured
- The `document_filters` parameter remains in agents as `Optional` dead code (never passed) — intentionally kept vs aggressively stripped

## Working Set
- Branch: `beta`
- Key files: `backend/main.py`, `backend/agents/search_agent.py`, `backend/tools/search_tool.py`, `backend/tools/relevance_filter.py`, `backend/config.py`, `backend/agents/response_agent.py`, `backend/agents/query_generator.py`, `backend/benchmark.py`, `backend/llm_judge.py`, `backend/chunking/llm_chunking.py`
- Specs: `docs/specs/benchmark-failure-analysis.md`, `docs/specs/project-architecture.md`, `docs/specs/qdrant-collections-schema.md`, `docs/specs/chunking-strategy.md`, `docs/specs/content-map.md`
- Designs: `thoughts/shared/designs/2026-05-13-remove-wikirouter-design.md`
