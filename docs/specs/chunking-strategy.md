# Chunking Strategy Specification

**Project:** AI Assistant (Башкирэнерго) — RAG-based Technical Connection Support  
**Date:** 2026-05-03  
**Version:** 2.0 (corrected from v1.0 which misunderstood the pipeline)  
**Status:** Draft  
**Related:** `backend/chunking/Mardown_splitter.py`, `backend/chunking/llm_chunking.py`, Ubiquitous Language glossary

---

## 1. Overview: Two-Stage Chunking Pipeline

The Bashkirenergo AI Assistant uses a **two-stage chunking pipeline**:

```
Raw Document
       │
       ▼
┌─────────────────────────────────────────────┐
│ STAGE 1: Physical Pre-Split (Mardown_splitter.py)  │
│   - Purpose: Fit chunks within LLM token limit     │
│   - Method: MarkdownHeaderTextSplitter              │
│             + RecursiveCharacterTextSplitter        │
│   - Output: .md files with "---CHUNK---" separators│
│   - chunk_size: 1,000–20,000 chars                  │
│   - chunk_overlap: 0                                │
└─────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────┐
│ STAGE 2: LLM Semantic Chunking (llm_chunking.py)   │
│   - Purpose: Atomic semantic fragments             │
│             + metadata enrichment                  │
│   - Method: qwen/qwen3.5-flash-02-23 via RouterAI  │
│   - Input: pre-chunks from Stage 1                 │
│   - Output: 1–N atomic JSON chunks per pre-chunk   │
│   - chunk_id: {parent_md5}_p{idx}                 │
│   - Enriched with: summary, questions, keywords,   │
│     entities, breadcrumbs, category                │
└─────────────────────────────────────────────┘
       │
       ▼
    Qdrant Ingestion
```

### 1.1 Why Two Stages?

- Documents (laws, regulations, FAQ collections) can be too large to feed into an LLM directly. Stage 1 guarantees each chunk stays within the 80k-token limit of the LLM model.
- Stage 1 is a **rough physical split** — boundaries may be imperfect, but that's acceptable.
- Stage 2 is the **semantic split** — the LLM re-divides each pre-chunk into **atomic, self-contained fragments** with proper metadata. This is where real chunk quality is achieved.
- The LLM has full context of its pre-chunk and produces optimally sized, semantically coherent sub-chunks. Rules about tables, numbered clauses, and Q&A pairs are enforced in the LLM prompt, not in the physical splitter.

---

## 2. Stage 1: Physical Pre-Split (Mardown_splitter.py)

### 2.1 Purpose

Reduce document size to fit within the LLM's token limit (80k tokens for `qwen3.5-flash-02-23`). The output is an intermediate `.md` file with chunks separated by `\n\n---CHUNK---\n\n`.

### 2.2 Configuration

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| `MIN_CHUNK_SIZE` | 1,000 chars | Avoids information fragmentation. Smaller chunks waste LLM calls. |
| `MAX_CHUNK_SIZE` | 20,000 chars | Fits within 80k token LLM limit. **Do NOT reduce** — this is a technical constraint, not a quality parameter. |
| `chunk_overlap` | 0 | **Not needed.** The LLM in Stage 2 re-chunks everything semantically. Overlap would be wasteful noise. |
| `SEPARATOR` | `\n\n---CHUNK---\n\n` | Token marking chunk boundaries in output files. Used by Stage 2 to split back into individual chunks. |

### 2.3 Splitter Strategy

```
┌─────────────────────────────────────────┐
│ MarkdownHeaderTextSplitter (Primary)    │
│   - Splits on h1–h5 headers             │
│   - Preserves header structure          │
│   - Keeps headers in chunk content      │
│   - respects document hierarchy         │
└─────────────────────────────────────────┘
              │
       ┌──────┴──────┐
       │              │
  Some sections   No headers
  exceed 20k       found
       │              │
       ▼              ▼
┌─────────────────────────────────────────┐
│ RecursiveCharacterTextSplitter (Fallback)│
│   - chunk_size: 20,000                  │
│   - chunk_overlap: 0                    │
│   - separators: \n\n, \n, . ,           │
│   - table-aware (\n\| separator)        │
└─────────────────────────────────────────┘
```

### 2.4 Post-Split Merge

Small chunks (< 1,000 chars) are merged with neighbors to avoid wasting LLM calls on tiny fragments. Merged chunks stay under 20,000 chars.

### 2.5 What Stage 1 Does NOT Do

- Does **not** guarantee semantic chunk boundaries — that's Stage 2's job
- Does **not** produce final chunk sizes — the LLM further subdivides
- Does **not** add overlap — the LLM has full context of its pre-chunk
- Does **not** add metadata (except file structure via headers)

### 2.6 Correctness

The current values (`MIN=1000`, `MAX=20000`, `overlap=0`) are **correct and should NOT be changed**. The pipeline was correctly designed — the misunderstanding was about what stage produces the final chunks.

---

## 3. Stage 2: LLM Semantic Chunking (llm_chunking.py)

### 3.1 Purpose

Take a pre-chunk from Stage 1 and produce 1–N **atomic, self-contained semantic fragments** enriched with metadata. This is the **primary chunking step** — the chunks that go into Qdrant come from this stage.

### 3.2 How It Works

1. Read `.md` file produced by Stage 1
2. Split on `\n\n---CHUNK---\n\n` into pre-chunks
3. For each pre-chunk:
   - Generate `parent_chunk_id` = MD5(source_file + first 100 chars)[:12]
   - Truncate to 20,000 chars if needed (safety)
   - Send to LLM with enrichment prompt
   - LLM splits into atomic fragments and generates metadata
   - Each output fragment gets `chunk_id` = `{parent_id}_p{idx}` (e.g., `a3f7e2d9b1c4_p1`)
4. Output: individual JSON files per chunk in `chechov/{category}/`

### 3.3 LLM Configuration

| Parameter | Value | Notes |
|-----------|-------|-------|
| Model | `qwen/qwen3.5-flash-02-23` | Via RouterAI API |
| Max tokens | 80,000 | Input limit |
| Temperature | 0.15 | Low for deterministic output |
| Max retries | 5 | With exponential backoff |
| Concurrency | 3 | Semaphore-limited async |
| Category | `legal` (current) | Will support: `faq`, `stage_description`, `infomaterial`, `instruction` |

### 3.4 Metadata Enrichment

Each atomic chunk gets these fields from the LLM:

| Field | Type | Description |
|-------|------|-------------|
| `chunk_id` | string | `{parent_id}_p{idx}` — unique identifier |
| `source_file` | string | Original Markdown filename |
| `chunk_content` | string | Full text of the fragment with corrected Markdown |
| `breadcrumbs` | string | Header path from root, e.g. "Глава 1 > Статья 3" (generated by LLM from the text) |
| `chunk_summary` | string | 2–4 sentence summary in Russian |
| `hypothetical_questions` | array | 4–5 questions a user might ask to find this fragment |
| `keywords` | array | 5–10 key phrases in Russian |
| `entities` | array | 3–8 named entities (organizations, laws, dates, terms) |
| `category` | string | Domain category: ЛК / ДУ / ТПП |

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
- [ ] All pre-chunks ≤ 20,000 chars
- [ ] No pre-chunk < 1,000 chars (except genuine small documents)
- [ ] `---CHUNK---` separator present between chunks

### 8.2 Stage 2 Validation
- [ ] Calculate average output chunks per input pre-chunk
- [ ] Spot-check: at least 3 random chunks manually verified for semantic coherence
- [ ] All required fields present in JSON output
- [ ] `chunk_id` follows `{parent_id}_p{idx}` format
- [ ] Zero failed chunks (or all failures retried/recovered)

### 8.3 End-to-End Validation
- [ ] Run benchmark on final Qdrant collections
- [ ] Compare `context_recall` with baseline (39%)
- [ ] Check that `power_range` and `client_type` filters return expected results

---

## 9. Glossary

| Term | Definition |
|------|------------|
| **Pre-chunk** | A physical text fragment from Stage 1 (Mardown_splitter), sized 1,000–20,000 chars, separated by `---CHUNK---` |
| **Atomic chunk** | A semantically self-contained fragment from Stage 2 (LLM), stored as JSON and ingested into Qdrant |
| **Parent chunk** | The pre-chunk that an atomic chunk was derived from (identified by MD5 prefix in chunk_id) |
| **Breadcrumbs** | Header hierarchy path (e.g., "Глава 1 > Статья 2") generated by the LLM from the chunk's content |
| **Two-stage pipeline** | Physical pre-split for LLM token limits → LLM semantic split for quality |

---

## 10. References

- `backend/chunking/Mardown_splitter.py` — Stage 1: physical pre-split
- `backend/chunking/llm_chunking.py` — Stage 2: LLM semantic chunking
- `backend/chunking/repair_json.py` — JSON recovery fallback
- `backend/chunking/token_count.py` — token counting utilities
- `docs/specs/qdrant-collections-schema.md` — final Qdrant collections schema
- `UBIQUITOUS_LANGUAGE.md` — domain terminology glossary

---

## 11. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-05-02 | AI Assistant | Initial version — incorrectly described single-stage chunking with overlap |
| 2.0 | 2026-05-03 | AI Assistant | Complete rewrite — correct two-stage pipeline, retains existing parameters, adds LLM-based chunking as primary method |
