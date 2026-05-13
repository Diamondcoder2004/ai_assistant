# Qdrant Collections Schema Specification

## 1. Overview

This document defines the Qdrant vector database collections schema for the Bashkirenergo AI Assistant RAG system. The schema is designed to support hybrid semantic and lexical search across two distinct content domains: regulatory/legal documents and operational/FAQ content.

### Embedding Configuration (from `config.py`)

| Parameter | Value | Source |
|---|---|---|
| **Embedding Model** | `perplexity/pplx-embed-v1-4b` | `EMBEDDING_MODEL` env var |
| **Embedding Dimension** | **2560** | `EMBEDDING_DIM` env var |
| **Distance Metric** | **Cosine** | Design spec §5.3 |
| **Qdrant Host** | `localhost` | `QDRANT_HOST` env var |
| **Qdrant Port** | `6333` | `QDRANT_PORT` env var |

> **Note:** The embedding dimension of 2560 is specific to the `perplexity/pplx-embed-v1-4b` model. All vector configurations must use `size=2560` and `distance=Cosine`.

---

## 2. Collections Summary

| Collection | Purpose | Content Types | Use Case |
|---|---|---|---|
| `normative_documents` | Regulatory and legal documents | `regulation` | Постановления, правила, законы, нормативные акты |
| `operational_content` | Operational materials and FAQs | `faq`, `stage_description`, `infomaterial`, `instruction` | FAQ, описания этапов, информационные материалы, инструкции |

---

## 3. Common Vector Configuration

Both collections share identical vector configuration:

```json
{
  "vectors": {
    "size": 2560,
    "distance": "Cosine",
    "hnsw_config": {
      "m": 16,
      "ef_construct": 100
    }
  }
}
```

### HNSW Parameters

| Parameter | Value | Description |
|---|---|---|
| `m` | 16 | Maximum number of connections per node (Qdrant default) |
| `ef_construct` | 100 | Build-time search depth (Qdrant default) |
| `ef` (search) | 64 | Search-time accuracy vs. speed tradeoff |

### Quantization Recommendation

For production deployments, **scalar quantization** is recommended to reduce memory footprint:

```json
{
  "vectors": {
    "size": 2560,
    "distance": "Cosine",
    "quantization_config": {
      "scalar": {
        "type": "int8",
        "always_ram": true
      }
    }
  }
}
```

---

## 4. Collection 1: `normative_documents`

### 4.1 Purpose

Stores regulatory and legal documents governing the technical connection (технологическое присоединение) process at Bashkirenergo. These are authoritative sources: постановления правительства, правила технологического присоединения, законы, нормативные акты.

### 4.2 Content Types

| Content Type | Description |
|---|---|
| `regulation` | Regulatory and legal documents (Постановления, правила, законы) |

### 4.3 Payload Schema

All payload fields for `normative_documents`:

| Field | Type | Required | Description |
|---|---|---|---|
| `chunk_id` | `keyword` | ✅ Yes | Unique identifier for the chunk (e.g., `doc123_chunk_0`) |
| `source_file` | `keyword` | ✅ Yes | Original document filename or URI |
| `chunk_content` | `text` | ✅ Yes | Full text content of the chunk |
| `breadcrumbs` | `keyword[]` or `text` | ✅ Yes | Document navigation path (e.g., `["Глава 2", "Раздел 3"]` ) |
| `chunk_summary` | `text` | No | Brief summary of the chunk content |
| `hypothetical_questions` | `text` or `text[]` | No | LLM-generated questions this chunk could answer |
| `keywords` | `keyword[]` | No | Extracted keywords/tags for the chunk |
| `entities` | `keyword[]` | No | Named entities mentioned in the chunk (organizations, laws, etc.) |
| `category` | `keyword` | ✅ Yes | Domain category: `ЛК` / `ДУ` / `ТПП` |
| `neighbor_chunk_ids` | `object` (`{prev, next}`) | No | IDs of adjacent chunks for context retrieval |
| `collection_name` | `keyword` | ✅ Yes | Fixed value: `normative_documents` |
| `document_type` | `keyword` | ✅ Yes | Fixed value: `regulation` |
| `power_range` | `keyword` | No | Applicable power range: `<15kW`, `15-150kW`, `150-670kW`, `>670kW`, `any` |
| `client_type` | `keyword` | No | Applicable client type: `ФЛ`, `ИП`, `ЮЛ`, `any` |

### 4.4 Payload Indexes

Fields indexed for filtering:

| Field | Index Type | Purpose |
|---|---|---|
| `category` | `keyword` | Filter by domain category (ЛК/ДУ/ТПП) |
| `document_type` | `keyword` | Filter by document subtype |
| `client_type` | `keyword` | Filter by client category |
| `power_range` | `keyword` | Filter by applicable power range |

### 4.5 Collection Creation — REST API

```bash
curl -X PUT 'http://localhost:6333/collections/normative_documents' \
  -H 'Content-Type: application/json' \
  -d '{
    "vectors": {
      "size": 2560,
      "distance": "Cosine",
      "hnsw_config": {
        "m": 16,
        "ef_construct": 100
      }
    },
    "quantization_config": {
      "scalar": {
        "type": "int8",
        "always_ram": true
      }
    }
  }'
```

### 4.6 Create Payload Indexes — REST API

```bash
# category index
curl -X PUT 'http://localhost:6333/collections/normative_documents/index' \
  -H 'Content-Type: application/json' \
  -d '{
    "field_name": "category",
    "field_schema": "keyword"
  }'

# document_type index
curl -X PUT 'http://localhost:6333/collections/normative_documents/index' \
  -H 'Content-Type: application/json' \
  -d '{
    "field_name": "document_type",
    "field_schema": "keyword"
  }'

# client_type index
curl -X PUT 'http://localhost:6333/collections/normative_documents/index' \
  -H 'Content-Type: application/json' \
  -d '{
    "field_name": "client_type",
    "field_schema": "keyword"
  }'

# power_range index
curl -X PUT 'http://localhost:6333/collections/normative_documents/index' \
  -H 'Content-Type: application/json' \
  -d '{
    "field_name": "power_range",
    "field_schema": "keyword"
  }'
```

---

## 5. Collection 2: `operational_content`

### 5.1 Purpose

Stores operational materials that help clients navigate the technical connection process: frequently asked questions, stage descriptions, informational materials, and step-by-step instructions.

### 5.2 Content Types

| Content Type | Description |
|---|---|
| `faq` | Frequently asked questions and answers |
| `stage_description` | Description of stages in the TPP process |
| `infomaterial` | Informational materials and reference content |
| `instruction` | Step-by-step instructions for clients |

### 5.3 Payload Schema

All payload fields for `operational_content`:

| Field | Type | Required | Description |
|---|---|---|---|
| `chunk_id` | `keyword` | ✅ Yes | Unique identifier for the chunk (e.g., `faq_42_chunk_0`) |
| `source_file` | `keyword` | ✅ Yes | Original document filename or URI |
| `chunk_content` | `text` | ✅ Yes | Full text content of the chunk |
| `breadcrumbs` | `keyword[]` or `text` | ✅ Yes | Document navigation path (e.g., `["FAQ", "Заявки"]` ) |
| `chunk_summary` | `text` | No | Brief summary of the chunk content |
| `hypothetical_questions` | `text` or `text[]` | No | LLM-generated questions this chunk could answer |
| `keywords` | `keyword[]` | No | Extracted keywords/tags for the chunk |
| `entities` | `keyword[]` | No | Named entities mentioned in the chunk |
| `category` | `keyword` | ✅ Yes | Domain category: `ЛК` / `ДУ` / `ТПП` |
| `neighbor_chunk_ids` | `object` (`{prev, next}`) | No | IDs of adjacent chunks for context retrieval |
| `collection_name` | `keyword` | ✅ Yes | Fixed value: `operational_content` |
| `document_type` | `keyword` | ✅ Yes | One of: `faq`, `stage_description`, `infomaterial`, `instruction` |
| `power_range` | `keyword` | No | Applicable power range: `<15kW`, `15-150kW`, `150-670kW`, `>670kW`, `any` |
| `client_type` | `keyword` | No | Applicable client type: `ФЛ`, `ИП`, `ЮЛ`, `any` |

### 5.4 Payload Indexes

Fields indexed for filtering:

| Field | Index Type | Purpose |
|---|---|---|
| `category` | `keyword` | Filter by domain category (ЛК/ДУ/ТПП) |
| `document_type` | `keyword` | Filter by content subtype (faq/stage_description/infomaterial/instruction) |
| `client_type` | `keyword` | Filter by client category |
| `power_range` | `keyword` | Filter by applicable power range |

### 5.5 Collection Creation — REST API

```bash
curl -X PUT 'http://localhost:6333/collections/operational_content' \
  -H 'Content-Type: application/json' \
  -d '{
    "vectors": {
      "size": 2560,
      "distance": "Cosine",
      "hnsw_config": {
        "m": 16,
        "ef_construct": 100
      }
    },
    "quantization_config": {
      "scalar": {
        "type": "int8",
        "always_ram": true
      }
    }
  }'
```

### 5.6 Create Payload Indexes — REST API

```bash
# category index
curl -X PUT 'http://localhost:6333/collections/operational_content/index' \
  -H 'Content-Type: application/json' \
  -d '{
    "field_name": "category",
    "field_schema": "keyword"
  }'

# document_type index
curl -X PUT 'http://localhost:6333/collections/operational_content/index' \
  -H 'Content-Type: application/json' \
  -d '{
    "field_name": "document_type",
    "field_schema": "keyword"
  }'

# client_type index
curl -X PUT 'http://localhost:6333/collections/operational_content/index' \
  -H 'Content-Type: application/json' \
  -d '{
    "field_name": "client_type",
    "field_schema": "keyword"
  }'

# power_range index
curl -X PUT 'http://localhost:6333/collections/operational_content/index' \
  -H 'Content-Type: application/json' \
  -d '{
    "field_name": "power_range",
    "field_schema": "keyword"
  }'
```

---

## 6. Python Client Examples (`qdrant-client`)

### 6.1 Create Collections

```python
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    HnswConfigDiff,
    ScalarQuantization,
    ScalarQuantizationConfig,
    ScalarType,
)

client = QdrantClient(host="localhost", port=6333)

# Common vector parameters
vector_params = VectorParams(
    size=2560,
    distance=Distance.COSINE,
    hnsw_config=HnswConfigDiff(
        m=16,
        ef_construct=100,
    ),
    quantization_config=ScalarQuantization(
        scalar=ScalarQuantizationConfig(
            type=ScalarType.INT8,
            always_ram=True,
        )
    ),
)

# Create normative_documents collection
client.create_collection(
    collection_name="normative_documents",
    vectors_config=vector_params,
)

# Create operational_content collection
client.create_collection(
    collection_name="operational_content",
    vectors_config=vector_params,
)
```

### 6.2 Create Payload Indexes

```python
from qdrant_client.models import PayloadSchemaType

INDEXED_FIELDS = ["category", "document_type", "client_type", "power_range"]

for collection in ["normative_documents", "operational_content"]:
    for field in INDEXED_FIELDS:
        client.create_payload_index(
            collection_name=collection,
            field_name=field,
            field_schema=PayloadSchemaType.KEYWORD,
        )
```

### 6.3 Upsert Points

```python
from qdrant_client.models import PointStruct

# Example: upsert a point into normative_documents
point = PointStruct(
    id="post_1547_chunk_0",
    vector=[0.01, -0.02, ...],  # 2560-dimensional embedding vector
    payload={
        "chunk_id": "post_1547_chunk_0",
        "source_file": "postanovlenie_1547.pdf",
        "chunk_content": "Правила технологического присоединения энергопринимающих устройств...",
        "breadcrumbs": ["Глава 1", "Общие положения"],
        "chunk_summary": "Общие положения правил технологического присоединения",
        "hypothetical_questions": [
            "Какие документы нужны для технологического присоединения?",
            "Кто утвердил правила технологического присоединения?",
        ],
        "keywords": ["присоединение", "правила", "постановление"],
        "entities": ["Правительство РФ", "ФАС России"],
        "category": "ТПП",
        "neighbor_chunk_ids": {"prev": None, "next": "post_1547_chunk_1"},
        "collection_name": "normative_documents",
        "document_type": "regulation",
        "power_range": "any",
        "client_type": "any",
    },
)

client.upsert(
    collection_name="normative_documents",
    points=[point],
)
```

### 6.4 Search with Filters

```python
from qdrant_client.models import Filter, FieldCondition, MatchValue

# Search in operational_content for FAQ items related to TPP
# for individual clients with power < 15kW
search_result = client.search(
    collection_name="operational_content",
    query_vector=[0.01, -0.02, ...],  # 2560-dim embedding of the query
    query_filter=Filter(
        must=[
            FieldCondition(
                key="category",
                match=MatchValue(value="ТПП"),
            ),
            FieldCondition(
                key="document_type",
                match=MatchValue(value="faq"),
            ),
            FieldCondition(
                key="client_type",
                match=MatchValue(value="ФЛ"),
            ),
            FieldCondition(
                key="power_range",
                match=MatchValue(value="<15kW"),
            ),
        ]
    ),
    limit=10,
    with_payload=True,
)

for scored_point in search_result:
    print(f"Score: {scored_point.score}")
    print(f"Content: {scored_point.payload['chunk_content'][:200]}...")
    print(f"Source: {scored_point.payload['source_file']}")
```

### 6.5 Search Across Both Collections

```python
from typing import List
from qdrant_client.models import ScoredPoint

def search_both_collections(
    query_vector: List[float],
    category: str = None,
    client_type: str = None,
    power_range: str = None,
    limit: int = 10,
) -> dict[str, List[ScoredPoint]]:
    """
    Search across both normative_documents and operational_content.
    Returns results grouped by collection.
    """
    conditions = []
    if category:
        conditions.append(
            FieldCondition(key="category", match=MatchValue(value=category))
        )
    if client_type:
        conditions.append(
            FieldCondition(key="client_type", match=MatchValue(value=client_type))
        )
    if power_range:
        conditions.append(
            FieldCondition(key="power_range", match=MatchValue(value=power_range))
        )

    query_filter = Filter(must=conditions) if conditions else None

    results = {}
    for collection in ["normative_documents", "operational_content"]:
        results[collection] = client.search(
            collection_name=collection,
            query_vector=query_vector,
            query_filter=query_filter,
            limit=limit,
            with_payload=True,
        )

    return results
```

---

## 7. Collections Comparison

| Aspect | `normative_documents` | `operational_content` |
|---|---|---|
| **Purpose** | Regulatory/legal documents | Operational materials and FAQs |
| **Content Types** | `regulation` | `faq`, `stage_description`, `infomaterial`, `instruction` |
| **Vector Size** | 2560 | 2560 |
| **Distance Metric** | Cosine | Cosine |
| **HNSW `m`** | 16 | 16 |
| **HNSW `ef_construct`** | 100 | 100 |
| **Quantization** | Scalar (int8) recommended | Scalar (int8) recommended |
| **Required Fields** | `chunk_id`, `source_file`, `chunk_content`, `breadcrumbs`, `category`, `collection_name`, `document_type` | `chunk_id`, `source_file`, `chunk_content`, `breadcrumbs`, `category`, `collection_name`, `document_type` |
| **Optional Fields** | `chunk_summary`, `hypothetical_questions`, `keywords`, `entities`, `neighbor_chunk_ids`, `power_range`, `client_type` | `chunk_summary`, `hypothetical_questions`, `keywords`, `entities`, `neighbor_chunk_ids`, `power_range`, `client_type` |
| **Indexed Fields** | `category`, `document_type`, `client_type`, `power_range` | `category`, `document_type`, `client_type`, `power_range` |
| **Typical Source** | Постановления, законы, правила | FAQ, инструкции, описания этапов |
| **Update Frequency** | Low (when regulations change) | Medium (when new FAQs/stages added) |

---

## 8. Field Value Reference

### 8.1 `category` — Domain Categories

| Value | Description |
|---|---|
| `ЛК` | Личный кабинет — Personal account operations |
| `ДУ` | Дополнительные услуги — Additional paid services |
| `ТПП` | Технологическое присоединение — Core technical connection process |

### 8.2 `document_type` — Document/Content Types

| Value | Collection | Description |
|---|---|---|
| `regulation` | `normative_documents` | Regulatory and legal documents |
| `faq` | `operational_content` | Frequently asked questions |
| `stage_description` | `operational_content` | Process stage descriptions |
| `infomaterial` | `operational_content` | Informational reference materials |
| `instruction` | `operational_content` | Step-by-step instructions |

### 8.3 `power_range` — Power Categories

| Value | Description |
|---|---|
| `<15kW` | Up to 15 kW |
| `15-150kW` | 15 kW to 150 kW |
| `150-670kW` | 150 kW to 670 kW |
| `>670kW` | Over 670 kW |
| `any` | Applicable to all power ranges |

### 8.4 `client_type` — Client Categories

| Value | Description |
|---|---|
| `ФЛ` | Физическое лицо — Individual |
| `ИП` | Индивидуальный предприниматель — Individual entrepreneur |
| `ЮЛ` | Юридическое лицо — Legal entity |
| `any` | Applicable to all client types |

---

## 9. Data Ingestion Checklist

Before upserting points into either collection, ensure:

- [ ] Text is chunked appropriately (recommended: 512-1024 tokens per chunk with overlap)
- [ ] Each chunk has a unique `chunk_id` (format: `{source_id}_chunk_{index}`)
- [ ] `breadcrumbs` reflect the document structure for context
- [ ] `chunk_summary` is generated for semantic search enhancement
- [ ] `hypothetical_questions` are generated via LLM for improved retrieval
- [ ] `keywords` and `entities` are extracted for lexical filtering
- [ ] `category`, `power_range`, and `client_type` are correctly classified
- [ ] `neighbor_chunk_ids` links adjacent chunks for context-aware retrieval
- [ ] Embedding vector is generated using `perplexity/pplx-embed-v1-4b` (2560 dimensions)
- [ ] `collection_name` and `document_type` match the target collection

---

## 10. Migration Notes

### From Single Collection (`BASHKIR_ENERGO_PERPLEXITY`)

The legacy single-collection approach stored all content types in one collection. The new dual-collection schema separates regulatory and operational content for:

1. **Improved filtering precision** — `document_type` queries are scoped to relevant content
2. **Different update cadences** — normative documents update rarely; operational content updates frequently
3. **Access control** — potential for different read permissions per collection
4. **Optimized HNSW parameters** — each collection can be tuned independently if needed

### Migration Steps

1. Create `normative_documents` and `operational_content` with schemas above
2. Re-index all points from `BASHKIR_ENERGO_PERPLEXITY`
3. Assign `collection_name` and `document_type` per content type
4. Create payload indexes on both collections
5. Update application search logic to query both collections
6. Validate search quality with benchmark dataset
7. Retire `BASHKIR_ENERGO_PERPLEXITY` after validation

---

## 11. Related Documents

- `config.py` — Embedding model and Qdrant connection configuration
- `docs/specs/project-architecture.md` — Overall system architecture
- Design doc §5.3 — Original vector store design specification
