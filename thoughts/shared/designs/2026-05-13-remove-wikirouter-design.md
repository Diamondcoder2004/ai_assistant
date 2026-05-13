---
date: 2026-05-13
topic: "Remove WikiRouter from RAG Pipeline"
status: validated
---

## Problem Statement

WikiRouter (JSON-based agentic knowledge layer) was introduced as a document selector to enrich the RAG pipeline with domain context. In practice, it has several critical issues:

- **document_filters are dead code** — explicitly discarded in `main.py:142` because hard category filters would exclude normative documents with `category="Общая"`, which are needed for any query
- **business_rules are always empty** — all 51 index entries have `[]`, the field is never populated by `build_index.py` or enriched_chunks
- **LLM routing adds latency and cost** — calls `inception/mercury-2` on every query, with 2 retries on failure, for uncertain value
- **wiki_context duplicates SearchAgent output** — summarised document context passed to ResponseAgent overlaps with full chunk content already retrieved by SearchAgent
- **wiki_context_short impact is unmeasured** — may help or hurt QueryGenerator, but no A/B test was ever done
- **The concept is ill-defined** — it's neither Karpathy's LLM Wiki (extracted knowledge patterns) nor a search filter, it's a middle ground that doesn't justify its complexity

## Approach

Clean removal without vestigial parameters. Delete the entire module and all references throughout the codebase.

## Files to Delete (6)

| Path | Reason |
|------|--------|
| `backend/wiki/` (entire directory) | Core WikiRouter module |
| `backend/tests/test_wiki_router.py` | Unit tests for WikiRouterAgent |
| `backend/tests/test_wiki_search_tool.py` | Unit tests for WikiSearchTool |
| `backend/tests/test_wiki_cleanup.py` | Cleanup verification tests (now moot) |
| `backend/tests/test_main_wiki_integration.py` | Integration tests for WikiRouter + main.py |

## Files to Edit (7)

### 1. `backend/main.py`
- Remove `from wiki.wiki_router import WikiRouterAgent` import
- Remove `self.wiki_router = WikiRouterAgent()` from `AgenticRAG.__init__`
- Remove `skip_wiki_router` parameter from `query()`
- Remove the entire WikiRouter block (try/except with `route_with_fallback`, `wiki_context`, `wiki_context_short`, `document_filters`)
- Remove `wiki_context` from `search_agent.search()` and `response_agent.generate_response()` calls
- Update docstrings

### 2. `backend/config.py`
- Remove the `# WIKI ROUTER` section (5 lines: `ENABLE_WIKI_ROUTER`, `WIKI_INDEX_PATH`, `WIKI_ROUTER_MODEL`, `WIKI_TOP_K`, `WIKI_SEARCH_TOP_K`)

### 3. `backend/agents/search_agent.py`
- Remove `wiki_context` parameter from `search()` method signature
- Remove `wiki_context` from `query_generator.generate()` calls within `search()`

### 4. `backend/agents/response_agent.py`
- Remove `wiki_context` parameter from `generate_response()` and `_create_user_prompt()`
- Remove `if wiki_context: wiki_section = ...` logic block
- Simplify prompt construction

### 5. `backend/prompts/query_generation.py`
- Remove `WIKI_CONTEXT_TEMPLATE` constant
- Remove `wiki_context` parameter from `get_query_generation_prompt()`
- Remove `if wiki_context:` conditional block
- Simplify `context` building

### 6. `backend/benchmark.py`
- Remove `skip_wiki_router` from `Benchmark.__init__` and `BenchmarkSample`
- Remove `--no-wiki` argparse argument
- Remove `skip_wiki_router` from `rag.query()` call

### 7. `.env`
- Remove `ENABLE_WIKI_ROUTER=false` and commented `WIKI_TABLE_NAME`, `WIKI_TOP_K_CONCEPTS` lines

## After Removal

The pipeline simplifies from:
```
User Query → WikiRouter → QueryGenerator → SearchAgent → ResponseAgent
```
To:
```
User Query → QueryGenerator → SearchAgent → ResponseAgent
```

- One fewer LLM call per query
- ~0.5s latency saved (WikiRouter LLM routing)
- No config surface area for wiki
- Cleaner codebase with no dead data (document_filters, business_rules)

If the concept is revisited later, it should be built from scratch as a proper knowledge layer (Karpathy's LLM Wiki pattern) with clear instrumentation from day one.

## Open Questions

None. The removal is straightforward.
