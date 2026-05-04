# Chunking Strategy Specification

**Project:** AI Assistant (Башкирэнерго) — RAG-based Technical Connection Support  
**Date:** 2026-05-04  
**Version:** 3.0 — new `pre_split_for_llm.py` pipeline, deepseek-v4-flash model, enriched output  
**Status:** Active  
**Related:** `backend/chunking/pre_split_for_llm.py`, `backend/chunking/llm_chunking.py`, Ubiquitous Language glossary

---

## 1. Overview: Two-Stage Chunking Pipeline (v3)

The Bashkirenergo AI Assistant uses a **two-stage chunking pipeline** with token-aware splitting:

```
Raw Markdown Files (.md)
   ├── new_data/source/markdown_data/       (former PDFs)
   └── new_data/source/operational/html_pages/  (former HTML pages)
       │
       ▼
┌──────────────────────────────────────────────┐
│ STAGE 1: Pre-split (pre_split_for_llm.py)    │
│   - Purpose: Fit files within LLM context    │
│             window (100k token limit)        │
│   - Method: tiktoken (cl100k_base) counting  │
│             + header/section splitting        │
│   - Split: Files ≤100k tokens → copy as-is   │
│            Files >100k  tokens → split into   │
│            _partN.md files by document        │
│            structure (headings, paragraphs)   │
│   - Image cleanup: strips ![]() markdown     │
│   - Output: markdown_data_split/             │
│             html_pages_split/                │
│   - Token limit: 100,000 per part            │
└──────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────┐
│ STAGE 2: LLM Semantic Chunking               │
│          (llm_chunking.py)                    │
│   - Purpose: Atomic semantic fragments       │
│             + metadata enrichment            │
│   - Model: deepseek/deepseek-v4-flash        │
│            via RouterAI (JSON output mode)   │
│   - Input: each _partN.md as one unit        │
│            (no intermediate splitting)        │
│   - Safety: token-based truncation at 100k   │
│            tokens (defense-in-depth)         │
│   - Output: 1–N atomic JSON chunks per part  │
│   - chunk_id: {parent_md5}_p{idx}            │
│   - Enriched with: summary, questions,       │
│     keywords, entities, breadcrumbs,         │
│     category, source_origin, document_source │
└──────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────┐
│ Output: enriched_chunks/                     │
│   ├── normative/   (laws, regulations)       │
│   └── operational/ (FAQs, instructions, etc) │
└──────────────────────────────────────────────┘
       │
       ▼
    Qdrant Ingestion (future)
```

### 1.1 Why Two Stages?

- Large documents (FZ-35: 240k tokens, PP-861: 291k tokens, PP-442: 549k tokens) must be cut to fit the LLM's context window (128k tokens for deepseek-v4-flash). Stage 1 uses `tiktoken` to count tokens accurately and splits files by header/section structure.
- Stage 1 is a **rough physical split** — boundaries may cut mid-article. This is acceptable because:
  - Stage 2 sees the entire part and re-chunks it semantically
  - The LLM has full context of its part and produces optimally-sized atomic fragments
- Stage 2 is the **semantic split** — the LLM re-divides each part into **atomic, self-contained fragments** with proper metadata. This is where real chunk quality is achieved.
- **Key difference from v2**: `Mardown_splitter.py` (LangChain text splitter with `---CHUNK---` separators) is replaced by `pre_split_for_llm.py` (token-aware file splitting). `llm_chunking.py` now processes each part file as a single unit — there is no intermediate chunk splitting between stages.

---

## 2. Stage 1: Token-Aware Pre-Split (`pre_split_for_llm.py`)

### 2.1 Purpose

Split files exceeding the LLM context window into parts that fit. Files already small enough are copied as-is (with image references removed).

### 2.2 Configuration

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| `MAX_TOKENS` | 100,000 per part | Fits within deepseek-v4-flash 128k context window with room for prompt overhead |
| `ENCODING_NAME` | `cl100k_base` | tiktoken encoding for accurate token counting (Cyrillic: ~1 token/char) |
| `IMAGE_PATTERN` | `!\[.*?\]\(.*?\)` | Strips all markdown images (188 → 0 in original run) |
| Output format | Separate `_partN.md` files | No `---CHUNK---` separators — each part is one LLM input unit |

### 2.3 Splitter Logic

```
┌──────────────────────────────────────────────┐
│ 1. split_into_sections() — Header split      │
│    - Regex on h1–h5 markdown headers          │
│    - Returns [(level, header, body), ...]     │
└──────────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────┐
│ 2. group_sections_into_parts()               │
│    - Groups sections into parts ≤100k tokens  │
│    - Sections exceeding 100k are split by     │
│      paragraphs via split_by_paragraphs()     │
└──────────────────────────────────────────────┘
```

### 2.4 Post-Split: Image Cleanup

Every output part is passed through `strip_images()` which removes `![alt](url)` patterns and collapses triple+ newlines. This ensures the LLM prompt doesn't waste tokens on inaccessible image references.

### 2.5 What Stage 1 Does NOT Do

- Does **not** add `---CHUNK---` separators — each part file IS one processing unit
- Does **not** guarantee semantic chunk boundaries — that's Stage 2's job
- Does **not** produce final chunk sizes — the LLM further subdivides
- Does **not** add metadata (except file naming via `_partN` suffix)

---

## 3. Stage 2: LLM Semantic Chunking (`llm_chunking.py`)

### 3.1 Purpose

Take a part file from Stage 1 and produce 1–N **atomic, self-contained semantic fragments** enriched with metadata. This is the **primary chunking step** — the chunks that go into Qdrant come from this stage.

### 3.2 How It Works

1. Read `.md` part file produced by Stage 1 (e.g., `1. ФЗ 35 (28.04.2025)_part1.md`)
2. The entire file is one input chunk (no intermediate `---CHUNK---` splitting)
3. Safety: if file exceeds 100k tokens, truncate to 100k tokens (defense-in-depth)
4. Send entire part to LLM with enrichment prompt + `response_format={"type":"json_object"}`
5. LLM splits into atomic fragments and generates metadata (summary, questions, keywords, entities, breadcrumbs)
6. Each output fragment gets `chunk_id` = `{parent_id}_p{idx}` (e.g., `a3f7e2d9b1c4_p3`)
7. Output: individual JSON files in `enriched_chunks/{normative|operational}/`

### 3.3 LLM Configuration

| Parameter | Value | Notes |
|-----------|-------|-------|
| Model | `deepseek/deepseek-v4-flash` | Via RouterAI API with JSON output mode |
| Max output tokens | 80,000 | Response limit |
| Input safety limit | 100,000 tokens | Token-based truncation (not char-based) |
| Temperature | 0.15 | Low for deterministic output |
| Max retries | 5 | With exponential backoff (base delay: 2s) |
| Concurrency | 3 | Semaphore-limited async |
| Response format | `json_object` | Forces JSON-only output, LLM wraps in `{"chunks":[...]}` |

### 3.4 Metadata Enrichment

Each atomic chunk gets these fields from the LLM:

| Field | Type | Description |
|-------|------|-------------|
| `chunk_id` | string | `{parent_id}_p{idx}` — unique identifier (e.g., `a3f7e2d9b1c4_p3`) |
| `source_file` | string | Original Markdown filename |
| `chunk_content` | string | Full text of the fragment with corrected Markdown |
| `breadcrumbs` | string | Header path from root, e.g. "Глава 1 > Статья 3" (generated by LLM from the text) |
| `chunk_summary` | string | 2–4 sentence summary in Russian |
| `hypothetical_questions` | array | 4–6 specific search queries a Bashkirenergo client would ask |
| `keywords` | array | 5–10 key phrases for search in Russian |
| `entities` | array | 3–8 named entities (laws with numbers, organizations, dates, kW amounts) |
| `category` | string | Domain category: ЛК / ДУ / ТПП |

Additional fields injected by the pipeline (not LLM-generated):

| Field | Source | Description |
|-------|--------|-------------|
| `source_origin` | File mapping | `normative` or `operational` — determines output directory |
| `document_source` | File mapping | `pdf` or `html_page` — original file format |

### 3.5 LLM Prompt Logic

The prompt instructs the LLM to:

1. **Split** the pre-chunk into atomic, self-contained fragments (by headers, lists, semantic paragraphs)
2. **Preserve tables** — can split by rows, but logically connected lists stay together
3. **Never split forms/applications** — they are atomic
4. **Fix Markdown errors** in each fragment
5. **Generate metadata** for each fragment
6. Return a **valid JSON array** with 1–N objects

### 3.6 Error Handling

| Failure | Recovery |
|---------|----------|
| JSON parse error | 5 retries with exponential backoff |
| All retries fail | `repair_json()` fallback (regex-based recovery) |
| Recovery also fails | Chunk logged in `failed_chunks.json`, re-attempted on next run |
| Raw response saved | `raw_responses_v2/{file}_{parent_id}_attempt{n}.txt` |

### 3.7 Missing Categories

Currently only `CATEGORY = "legal"` is processed. To support all content types, the pipeline needs to be run with different categories:

- `legal` → chunks in `chechov/legal/` → `normative_documents` Qdrant collection
- `faq` → chunks in `chechov/faq/` → `operational_content` Qdrant collection
- `stage_description`, `infomaterial`, `instruction` → same as above

---

## 4. Chunk Size Analysis

### 4.1 Physical Pre-Chunks (Stage 1 Output)

| Statistic | Value |
|-----------|-------|
| Min | 1,000 chars |
| Max | 20,000 chars |
| Median | ~8,000–12,000 chars (depends on document structure) |
| Tokens (approx.) | 2,500–5,000 tokens (Cyrillic, cl100k_base) |
| % of LLM limit | 3–6% of 80k |

### 4.2 Semantic Chunks (Stage 2 Output — Final)

| Statistic | Value |
|-----------|-------|
| Min | ~200–500 chars (single article/section) |
| Max | ~5,000–8,000 chars (complex article with multiple points) |
| Median | ~1,500–3,000 chars |
| Per pre-chunk | 1–10 output chunks |

The LLM determines optimal chunk size based on semantic boundaries. There is **no fixed size target** — the constraint is "atomic and self-contained", not character count. This is the correct approach because:
- Single-article chunks (500 chars) are fully self-contained and answerable
- Multi-point legal articles (5,000 chars) stay together because splitting them loses context
- FAQ answers (800–1,500 chars) form natural units

### 4.3 Why No Manual Size Limits in Stage 2

Adding a character limit would force the LLM to split at arbitrary points, undoing the semantic quality of the LLM-based chunking. If the LLM produces a 6,000-char chunk for a dense legal article, that's the right size — the article needs all its clauses to be self-contained.

---

## 5. Neighbor Chunk Relationships

### 5.1 Parent-Child Structure (Already Implemented)

The `chunk_id` format already encodes parent-child relationships:

```json
{
  "chunk_id": "a3f7e2d9b1c4_p3",
  "source_file": "2. 861 (28.04.2025).md"
}
```

- `a3f7e2d9b1c4` = parent pre-chunk ID (MD5 of source_file + first 100 chars)
- `p3` = 3rd atomic fragment from this parent

All chunks from the same pre-chunk share the same parent prefix.

### 5.2 Adding Neighbor Chunk IDs

Currently **not implemented** but proposed for Phase 2. After Stage 2 produces all chunks, a post-processing step can link neighbors:

```json
{
  "chunk_id": "a3f7e2d9b1c4_p3",
  "neighbor_chunk_ids": {
    "prev": "a3f7e2d9b1c4_p2",
    "next": "a3f7e2d9b1c4_p4"
  }
}
```

This is trivial to compute after sorting by chunk_id within each parent.

---

## 6. Integration with PDF Parser

### 6.1 PDF → Markdown → Pipeline

New PDF documents follow this path:

```
PDF File
    ↓
PDF Parser (to be built — Phase 2)
    ↓
Markdown text with headers + tables
    ↓
Mardown_splitter.py (Stage 1: physical pre-split)
    ↓
llm_chunking.py (Stage 2: semantic chunking + enrichment)
    ↓
Qdrant Ingestion
```

### 6.2 PDF Parser Requirements

The parser must:
1. **Detect headings** and emit them as Markdown headers (`#`, `##`, etc.)
2. **Preserve table structure** as Markdown pipe tables
3. **Emit ordered lists** for numbered clauses
4. Output **clean UTF-8 Markdown** suitable for both splitters

If headings are not detected (scanned/simple PDFs), the RecursiveCharacterTextSplitter fallback handles it in Stage 1, and the LLM still semantically chunks in Stage 2.

---

## 7. New Metadata Fields (Phase 2 Addition)

Stage 2 currently generates these fields via LLM:
- `chunk_id`, `source_file`, `chunk_content`, `breadcrumbs`, `chunk_summary`, `hypothetical_questions`, `keywords`, `entities`, `category`

For Phase 2, additional fields will be injected in a **post-processing step** after Stage 2:

| Field | Source | Description |
|-------|--------|-------------|
| `collection_name` | Derived from category | `normative_documents` or `operational_content` |
| `document_type` | File/directory metadata | `regulation`, `faq`, `stage_description`, `infomaterial`, `instruction` |
| `power_range` | LLM (add to prompt) or manual | `<15kW`, `15-150kW`, `150-670kW`, `>670kW`, `any` |
| `client_type` | LLM (add to prompt) or manual | `ФЛ`, `ИП`, `ЮЛ`, `any` |
| `neighbor_chunk_ids` | Computed post-split | `{prev, next}` chunks within same parent |

These fields are **not** generated by the LLM in the current prompt. Options:
- **A**: Add to LLM prompt (more accurate, but costs tokens)
- **B**: Post-processing inference from chunk_content (cheaper, less accurate)
- **C**: Manual tagging by file path convention (most reliable for `document_type` and `collection_name`)

**Recommendation:** Options A+C — use file path convention for `document_type`/`collection_name`, and add `power_range`/`client_type` to the LLM prompt.

---

## 8. Testing Checklist

### 8.1 Stage 1 Validation
- [ ] Run on PDF-parsed Markdown files — verify output files exist
- [ ] All part files ≤ 100,000 tokens (via tiktoken count)
- [ ] No image references (`![]()` patterns) in output files
- [ ] `_partN` suffix present on split files, non-split files have original names

### 8.2 Stage 2 Validation
- [ ] Calculate average output chunks per input part file
- [ ] Spot-check: at least 3 random chunks manually verified for semantic coherence
- [ ] All required fields present in JSON output
- [ ] `chunk_id` follows `{parent_id}_p{idx}` format
- [ ] Zero failed chunks (or all failures retried/recovered)
- [ ] Chunks correctly placed in `normative/` or `operational/` based on `source_origin`

### 8.3 End-to-End Validation
- [ ] Run benchmark on final Qdrant collections
- [ ] Compare `context_recall` with baseline (39%)
- [ ] Check that `power_range` and `client_type` filters return expected results

---

## 9. Glossary

| Term | Definition |
|------|------------|
| **Part file** | A physical text file from Stage 1 (`pre_split_for_llm.py`), sized ≤100,000 tokens, named `_partN.md` for split documents |
| **Atomic chunk** | A semantically self-contained fragment from Stage 2 (LLM), stored as JSON and ingested into Qdrant |
| **Parent chunk** | The part file that an atomic chunk was derived from (identified by MD5 prefix in chunk_id) |
| **Breadcrumbs** | Header hierarchy path (e.g., "Глава 1 > Статья 2") generated by the LLM from the chunk's content |
| **Two-stage pipeline** | Token-aware file pre-split for LLM context limits → LLM semantic split for quality |

---

## 10. References

- `backend/chunking/pre_split_for_llm.py` — Stage 1: token-aware file splitting
- `backend/chunking/llm_chunking.py` — Stage 2: LLM semantic chunking + enrichment
- `backend/chunking/repair_json.py` — JSON recovery fallback
- `docs/specs/qdrant-collections-schema.md` — final Qdrant collections schema
- `new_data/source/operational/metadata.json` — html_pages category/dtype mapping
- `UBIQUITOUS_LANGUAGE.md` — domain terminology glossary

---

## 11. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-05-02 | AI Assistant | Initial version — incorrectly described single-stage chunking with overlap |
| 2.0 | 2026-05-03 | AI Assistant | Complete rewrite — correct two-stage pipeline, retains existing parameters, adds LLM-based chunking as primary method |
| 3.0 | 2026-05-04 | AI Assistant | New `pre_split_for_llm.py` replaces `Mardown_splitter.py`; model → deepseek-v4-flash; JSON output mode; new fields `source_origin`, `document_source`; output → `enriched_chunks/{normative|operational}/`; removed `---CHUNK---` separator; token-based truncation safety |
