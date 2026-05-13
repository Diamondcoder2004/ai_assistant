# Dual Collection Search Implementation Plan

**Goal:** Replace single Qdrant collection with dual collections (normative_documents + operational_content), add Qdrant payload filters from Wiki Router, and enable parallel search across both collections.

**Architecture:** Two Qdrant collections replace one. Ingestion routes chunks by `source_origin` field. Runtime search queries both collections in parallel with Qdrant-native filters (category, client_type, power_range, document_type). BM25 stays unified across both. Each SearchResult gains a `collection_name` field.

**Design:** [thoughts/shared/designs/2026-05-05-dual-collection-search-design.md](../designs/2026-05-05-dual-collection-search-design.md)

---

## Dependency Graph

```
Batch 1 (parallel): 1.1, 1.2, 1.3 [foundation - no deps]
Batch 2 (parallel): 2.1, 2.2 [core - depends on batch 1]
Batch 3 (parallel): 3.1, 3.2, 3.3 [components - depends on batch 2]
Batch 4 (parallel): 4.1 [integration - depends on batch 3]
```

---

## Batch 1: Foundation (parallel - 3 implementers)

All tasks in this batch have NO dependencies and run simultaneously.

### Task 1.1: `.env` and `.env.example` — Dual Collection Environment Variables

**File:** `.env`
**File:** `.env.example`
**Test:** none (config files)
**Depends:** none

#### `.env` changes

Replace the single `COLLECTION_NAME` line with three new variables. Keep `COLLECTION_NAME` as a comment for reference.

```diff
 # ===========================================
 # Qdrant Vector Database (существующий на хосте)
 # ===========================================
 QDRANT_HOST=host.docker.internal
 QDRANT_PORT=6333
-COLLECTION_NAME=BASHKIR_ENERGO_PERPLEXITY_V2
+NORMATIVE_COLLECTION=normative_documents
+OPERATIONAL_COLLECTION=operational_content
+CHUNKS_DIR=chunking/enriched_chunks
+# COLLECTION_NAME is deprecated — use NORMATIVE_COLLECTION + OPERATIONAL_COLLECTION
```

#### `.env.example` changes

```diff
 # ===========================================
 # Qdrant Vector Database
 # ===========================================
 QDRANT_HOST=qdrant
 QDRANT_PORT=6333
-COLLECTION_NAME=BASHKIR_ENERGO_PERPLEXITY
+NORMATIVE_COLLECTION=normative_documents
+OPERATIONAL_COLLECTION=operational_content
+CHUNKS_DIR=chunking/enriched_chunks
+# COLLECTION_NAME is deprecated — use NORMATIVE_COLLECTION + OPERATIONAL_COLLECTION
```

**Verify:** `grep -c "NORMATIVE_COLLECTION" .env .env.example` returns 2
**Commit:** `feat(config): replace COLLECTION_NAME with NORMATIVE_COLLECTION + OPERATIONAL_COLLECTION + CHUNKS_DIR`

---

### Task 1.2: `backend/config.py` — Dual Collection Config

**File:** `backend/config.py`
**Test:** `backend/tests/test_config_dual_collections.py`
**Depends:** none

#### Implementation

Add three new config variables after the QDRANT section. Keep `COLLECTION_NAME` as deprecated with fallback.

```python
# =============================================================================
# QDRANT
# =============================================================================

QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))

# Dual collection names (replacing single COLLECTION_NAME)
NORMATIVE_COLLECTION_NAME = os.getenv("NORMATIVE_COLLECTION", "normative_documents")
OPERATIONAL_COLLECTION_NAME = os.getenv("OPERATIONAL_COLLECTION", "operational_content")

# Directory with enriched chunks (relative to backend/)
CHUNKS_DIR = os.getenv("CHUNKS_DIR", "chunking/enriched_chunks")

# Deprecated: kept for backward compatibility
# If NORMATIVE_COLLECTION is not set, falls back to COLLECTION_NAME
COLLECTION_NAME = os.getenv("COLLECTION_NAME", NORMATIVE_COLLECTION_NAME)
```

#### Test

```python
"""Tests for dual collection config."""
import os
import pytest


def test_normative_collection_default():
    """NORMATIVE_COLLECTION defaults to 'normative_documents'."""
    from config import NORMATIVE_COLLECTION_NAME
    assert NORMATIVE_COLLECTION_NAME == "normative_documents"


def test_operational_collection_default():
    """OPERATIONAL_COLLECTION defaults to 'operational_content'."""
    from config import OPERATIONAL_COLLECTION_NAME
    assert OPERATIONAL_COLLECTION_NAME == "operational_content"


def test_chunks_dir_default():
    """CHUNKS_DIR defaults to 'chunking/enriched_chunks'."""
    from config import CHUNKS_DIR
    assert CHUNKS_DIR == "chunking/enriched_chunks"


def test_collection_name_deprecated_fallback():
    """COLLECTION_NAME falls back to NORMATIVE_COLLECTION_NAME."""
    from config import COLLECTION_NAME, NORMATIVE_COLLECTION_NAME
    assert COLLECTION_NAME == NORMATIVE_COLLECTION_NAME


def test_env_override_normative(monkeypatch):
    """NORMATIVE_COLLECTION can be overridden via env."""
    monkeypatch.setenv("NORMATIVE_COLLECTION", "my_normative")
    # Need to reimport to pick up env change
    import importlib
    import config
    importlib.reload(config)
    assert config.NORMATIVE_COLLECTION_NAME == "my_normative"
    # Cleanup
    monkeypatch.delenv("NORMATIVE_COLLECTION")
    importlib.reload(config)


def test_env_override_operational(monkeypatch):
    """OPERATIONAL_COLLECTION can be overridden via env."""
    monkeypatch.setenv("OPERATIONAL_COLLECTION", "my_operational")
    import importlib
    import config
    importlib.reload(config)
    assert config.OPERATIONAL_COLLECTION_NAME == "my_operational"
    monkeypatch.delenv("OPERATIONAL_COLLECTION")
    importlib.reload(config)
```

**Verify:** `cd backend && python -m pytest tests/test_config_dual_collections.py -v`
**Commit:** `feat(config): add NORMATIVE_COLLECTION_NAME, OPERATIONAL_COLLECTION_NAME, CHUNKS_DIR to config.py`

---

### Task 1.3: `docker-compose.yml` — Update Environment Variables

**File:** `docker-compose.yml`
**Test:** none (infra config)
**Depends:** none

Replace the `COLLECTION_NAME` env var passthrough with the two new collection variables.

```yaml
version: '3.8'

services:
  # Backend - FastAPI Agentic RAG
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: ai-assistant-backend
    restart: unless-stopped
    env_file:
      - .env
    environment:
      - JUDGE_LLM_MODEL=${JUDGE_LLM_MODEL}
      - AGENT_DEBUG_ENABLED=${AGENT_DEBUG_ENABLED:-true}
      - NORMATIVE_COLLECTION=${NORMATIVE_COLLECTION:-normative_documents}
      - OPERATIONAL_COLLECTION=${OPERATIONAL_COLLECTION:-operational_content}
      - CHUNKS_DIR=${CHUNKS_DIR:-chunking/enriched_chunks}
    ports:
      - "8880:8880"
    volumes:
      - ./backend/logs:/app/logs
    extra_hosts:
      - "host.docker.internal:host-gateway"
    networks:
      - ai-assistant-network

  # Frontend - Vue.js
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      args:
        - VITE_SUPABASE_URL=${VITE_SUPABASE_URL}
        - VITE_SUPABASE_ANON_KEY=${VITE_SUPABASE_ANON_KEY}
        - VITE_API_BASE_URL=
        - VITE_TEST_MODE=${VITE_TEST_MODE:-false}
    container_name: ai-assistant-frontend
    restart: unless-stopped
    ports:
      - "80:80"
    depends_on:
      - backend
    extra_hosts:
      - "host.docker.internal:host-gateway"
    networks:
      - ai-assistant-network

networks:
  ai-assistant-network:
    driver: bridge
```

**Verify:** `docker-compose config` validates without errors
**Commit:** `feat(infra): update docker-compose.yml with dual collection env vars`

---

## Batch 2: Core Modules (parallel - 2 implementers)

All tasks in this batch depend on Batch 1 completing.

### Task 2.1: `backend/qdrant_ingest/ingest_qdrant_contextual.py` — Dual Collection Ingestion

**File:** `backend/qdrant_ingest/ingest_qdrant_contextual.py`
**Test:** `backend/tests/test_ingest_dual_collections.py`
**Depends:** 1.1, 1.2

#### Implementation

Major rewrite of the ingestion script. Key changes:
1. `recreate_collection()` → `recreate_collections()` — creates both collections with identical vector schema + payload indexes
2. `load_all_chunks()` — adds `collection_name` and `document_type` enrichment based on `source_origin`
3. Payload enrichment — adds `breadcrumbs`, `document_type`, `collection_name`, `client_type`, `power_range`
4. Upsert routing — routes points to the correct collection based on `collection_name`
5. Statistics — separate count per collection

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Загрузка чанков в Qdrant с ТРЕМЯ векторами (pref + hype + contextual).
Две коллекции: normative_documents + operational_content.
"""

import json, time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from tqdm import tqdm
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.exceptions import ResponseHandlingException
from openai import OpenAI
import config as cfg

# ================= НАСТРОЙКИ =================
EMBEDDING_BATCH_SIZE = 32
QDRANT_BATCH_SIZE = 50
QDRANT_TIMEOUT = 60
QDRANT_RETRIES = 3
HYPE_JOINER = " | "
CONTEXTUAL_JOINER = "\n\n---\n\n"

# Payload index fields for both collections
PAYLOAD_INDEX_FIELDS = ["category", "document_type", "client_type", "power_range"]

# Document type mapping based on source_origin
DOCUMENT_TYPE_MAP = {
    "normative": "regulation",
    # operational types are inferred from document_source or filename
}

# Default operational document types by filename pattern
OPERATIONAL_TYPE_PATTERNS = {
    "faq": "faq",
    "stage": "stage_description",
    "infomaterial": "infomaterial",
    "instruction": "instruction",
    "passport": "instruction",
    "pamyatka": "infomaterial",
    "gid": "stage_description",
    "shag": "stage_description",
    "map": "infomaterial",
    "calc": "infomaterial",
    "forms": "instruction",
    "cok": "infomaterial",
}


# =============================================


class RouterAIEmbedder:
    def __init__(self, api_key: str, base_url: str, model: str, batch_size: int = 128):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        self.batch_size = batch_size

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Получает эмбеддинги для списка текстов с батчингом."""
        all_embedding = []
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            try:
                response = self.client.embeddings.create(
                    model=self.model,
                    input=batch,
                    encoding_format="float",
                )
                if response.data is None:
                    print(f"⚠️ response.data is None at batch {i}, retrying in 2s...")
                    time.sleep(2)
                    response = self.client.embeddings.create(
                        model=self.model,
                        input=batch,
                        encoding_format="float",
                    )
                    if response.data is None:
                        raise Exception("response.data is None after retry")
                
                batch_embeddings = [item.embedding for item in sorted(response.data, key=lambda x: x.index)]
                all_embedding.extend(batch_embeddings)
            except Exception as e:
                print(f"❌ Batch error at index {i}: {e}")
                for j, txt in enumerate(batch[:3]):
                    print(f"   Text {j}: len={len(txt)}, preview={txt[:100]}...")
                raise
        return all_embedding


def get_routerai_embedder() -> RouterAIEmbedder:
    return RouterAIEmbedder(
        api_key=cfg.ROUTERAI_API_KEY,
        base_url=cfg.ROUTERAI_BASE_URL,
        model=cfg.EMBEDDING_MODEL,
        batch_size=EMBEDDING_BATCH_SIZE
    )


def infer_document_type(chunk: Dict[str, Any]) -> str:
    """Infer document_type from source_origin and source_file."""
    source_origin = chunk.get("source_origin", "operational")
    
    if source_origin == "normative":
        return "regulation"
    
    # For operational, try to infer from source_file or document_source
    source_file = chunk.get("source_file", "").lower()
    document_source = chunk.get("document_source", "").lower()
    
    for pattern, doc_type in OPERATIONAL_TYPE_PATTERNS.items():
        if pattern in source_file:
            return doc_type
    
    # Default operational type
    return "infomaterial"


def infer_collection_name(chunk: Dict[str, Any]) -> str:
    """Determine which Qdrant collection a chunk belongs to."""
    source_origin = chunk.get("source_origin", "operational")
    if source_origin == "normative":
        return cfg.NORMATIVE_COLLECTION_NAME
    return cfg.OPERATIONAL_COLLECTION_NAME


# ================= ЗАГРУЗКА ЧАНКОВ =================
def load_all_chunks() -> List[Dict[str, Any]]:
    """Рекурсивно загружает все JSON-файлы из подпапок cfg.CHUNKS_DIR."""
    chunks_dir = Path(cfg.CHUNKS_DIR)
    if not chunks_dir.exists():
        print(f"❌ Папка {chunks_dir} не найдена")
        return []

    all_chunks = []
    category_dirs = [d for d in chunks_dir.iterdir() if d.is_dir()]
    print(f"📁 Найдено категорий: {len(category_dirs)}")

    for cat_dir in category_dirs:
        category = cat_dir.name
        json_files = list(cat_dir.glob("*.json"))
        print(f"📂 Категория '{category}': {len(json_files)} файлов")

        for json_path in json_files:
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    chunk = json.load(f)
                if 'category' not in chunk:
                    chunk['category'] = category
                # Enrich: collection_name and document_type
                chunk['collection_name'] = infer_collection_name(chunk)
                chunk['document_type'] = infer_document_type(chunk)
                # Default filterable fields
                if 'client_type' not in chunk:
                    chunk['client_type'] = 'any'
                if 'power_range' not in chunk:
                    chunk['power_range'] = 'any'
                all_chunks.append(chunk)
            except Exception as e:
                print(f"   ❌ Ошибка чтения {json_path.name}: {e}")

    print(f"✅ Всего загружено чанков: {len(all_chunks)}")
    normative_count = sum(1 for c in all_chunks if c.get('collection_name') == cfg.NORMATIVE_COLLECTION_NAME)
    operational_count = sum(1 for c in all_chunks if c.get('collection_name') == cfg.OPERATIONAL_COLLECTION_NAME)
    print(f"   📚 Нормативных: {normative_count}")
    print(f"   📋 Операционных: {operational_count}")
    return all_chunks


def prepare_text_pref(chunk: Dict[str, Any]) -> str:
    """Готовит текст для pref‑вектора: summary + content."""
    parts = []
    if chunk.get('chunk_summary'):  
        parts.append(f"Кратко: {chunk['chunk_summary']}")
    content = chunk.get('chunk_content') or chunk.get('content', '')
    if content:
        parts.append(content[:8000])
    if not parts:
        return "пустой чанк"
    return "\n\n".join(parts)


def prepare_text_hype(chunk: Dict[str, Any]) -> Optional[str]:
    """Готовит текст для hype‑вектора: все гипотетические вопросы."""
    questions = chunk.get('hypothetical_questions')
    if not questions or not isinstance(questions, list):
        return None
    return HYPE_JOINER.join(questions)


def sanitize_text(text: str, max_length: int = 8000) -> str:
    """Очищает текст от проблемных символов и ограничивает длину."""
    if not text:
        return ""
    text = text.replace('\x00', '').replace('\ufffd', '')
    return text[:max_length]


def prepare_text_contextual(
    chunk: Dict[str, Any],
    prev_chunk: Optional[Dict[str, Any]],
    next_chunk: Optional[Dict[str, Any]]
) -> str:
    """Готовит текст для contextual-вектора: prev + current + next."""
    parts = []
    if prev_chunk:
        prev_content = prev_chunk.get('chunk_content') or prev_chunk.get('content', '')
        if prev_content:
            parts.append(f"[ПРЕДЫДУЩИЙ КОНТЕКСТ]\n{sanitize_text(prev_content, 4000)}")
    current_content = chunk.get('chunk_content') or chunk.get('content', '')
    if current_content:
        parts.append(f"[ТЕКУЩИЙ КОНТЕКСТ]\n{sanitize_text(current_content, 4000)}")
    if next_chunk:
        next_content = next_chunk.get('chunk_content') or next_chunk.get('content', '')
        if next_content:
            parts.append(f"[СЛЕДУЮЩИЙ КОНТЕКСТ]\n{sanitize_text(next_content, 4000)}")
    if not parts:
        return "пустой контекст"
    return CONTEXTUAL_JOINER.join(parts)


def sort_chunks_by_context(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Сортирует чанки для правильного контекстного соседства."""
    return sorted(
        chunks,
        key=lambda c: (
            c.get('collection_name', ''),
            c.get('category', ''),
            c.get('source_file', ''),
            c.get('chunk_id', '')
        )
    )


def recreate_collections(client: QdrantClient):
    """Удаляет и создаёт обе коллекции с тремя именованными векторами + payload индексы."""
    collections = [cfg.NORMATIVE_COLLECTION_NAME, cfg.OPERATIONAL_COLLECTION_NAME]
    
    for coll_name in collections:
        print(f"💀 Удаление коллекции '{coll_name}' (если существует)...")
        try:
            client.delete_collection(coll_name)
            print(f"✅ Коллекция '{coll_name}' удалена")
        except Exception as e:
            print(f"⚠️ Коллекция '{coll_name}' не существовала или ошибка: {e}")

        print(f"📦 Создание коллекции '{coll_name}' (размерность {cfg.EMBEDDING_DIM})...")
        client.create_collection(
            collection_name=coll_name,
            vectors_config={
                "pref": models.VectorParams(size=cfg.EMBEDDING_DIM, distance=models.Distance.COSINE),
                "hype": models.VectorParams(size=cfg.EMBEDDING_DIM, distance=models.Distance.COSINE),
                "contextual": models.VectorParams(size=cfg.EMBEDDING_DIM, distance=models.Distance.COSINE),
            }
        )
        print(f"✅ Коллекция '{coll_name}' создана с тремя векторами")

        # Create payload indexes
        for field_name in PAYLOAD_INDEX_FIELDS:
            client.create_payload_index(
                collection_name=coll_name,
                field_name=field_name,
                field_schema=models.PayloadSchemaType.KEYWORD,
            )
            print(f"   📇 Индекс '{field_name}' создан в '{coll_name}'")


def upsert_with_retry(client: QdrantClient, collection_name: str, points: List, retry_count: int = QDRANT_RETRIES):
    """Upsert с retry логикой при timeout."""
    for attempt in range(retry_count):
        try:
            client.upsert(collection_name=collection_name, points=points)
            return True
        except (ResponseHandlingException, TimeoutError) as e:
            if attempt == retry_count - 1:
                print(f"\n❌ Upsert to '{collection_name}' failed after {retry_count} retries: {e}")
                return False
            wait_time = 2 ** attempt
            print(f"⚠️ Upsert timeout for '{collection_name}', retry {attempt + 1}/{retry_count} через {wait_time}с...")
            time.sleep(wait_time)
    return False


def main():
    print("=" * 60)
    print("🚀 ЗАГРУЗКА ЧАНКОВ В ДВЕ КОЛЛЕКЦИИ (normative_documents + operational_content)")
    print("=" * 60)
    print(f"📁 Источник: {cfg.CHUNKS_DIR}")
    print(f"📚 Нормативная: {cfg.NORMATIVE_COLLECTION_NAME}")
    print(f"📋 Операционная: {cfg.OPERATIONAL_COLLECTION_NAME}")
    print(f"🤖 Модель эмбеддингов: {cfg.EMBEDDING_MODEL}")
    print(f"📏 Размерность: {cfg.EMBEDDING_DIM}")
    print(f"🔢 Embedding батч: {EMBEDDING_BATCH_SIZE}")
    print(f"🔢 Qdrant батч: {QDRANT_BATCH_SIZE}")
    print(f"⏱️ Timeout: {QDRANT_TIMEOUT}с")
    print("=" * 60)

    # Подключение к Qdrant
    print("🔄 Подключение к Qdrant...")
    client = QdrantClient(
        host=cfg.QDRANT_HOST,
        port=cfg.QDRANT_PORT,
        timeout=QDRANT_TIMEOUT
    )

    # Пересоздание коллекций
    recreate_collections(client)

    # Загрузка чанков
    chunks = load_all_chunks()
    if not chunks:
        print("❌ Нет чанков для загрузки")
        return

    # Сортировка для контекста
    print("\n🔄 Сортировка чанков для контекстного соседства...")
    chunks = sort_chunks_by_context(chunks)

    # Подготовка текстов
    pref_texts = []
    hype_texts = []
    hype_indices = []
    contextual_texts = []

    print("\n📝 Подготовка текстов...")
    for idx, chunk in enumerate(tqdm(chunks, desc="Тексты")):
        pref_texts.append(prepare_text_pref(chunk))
        
        hype_text = prepare_text_hype(chunk)
        if hype_text is not None:
            hype_texts.append(hype_text)
            hype_indices.append(idx)
        else:
            print(f"⚠️ Чанк {chunk.get('chunk_id', 'unknown')} без hypothetical_questions")
        
        prev_chunk = chunks[idx - 1] if idx > 0 else None
        next_chunk = chunks[idx + 1] if idx < len(chunks) - 1 else None
        contextual_text = prepare_text_contextual(chunk, prev_chunk, next_chunk)
        contextual_texts.append(contextual_text)

    # Эмбеддинги
    print("\n🤖 Инициализация RouterAI эмбеддера...")
    embedder = get_routerai_embedder()

    print(f"🔄 Создание эмбеддингов contextual ({len(contextual_texts)} шт.)...")
    lengths = [len(t) for t in contextual_texts]
    print(f"   📊 Статистика длин: мин={min(lengths)}, макс={max(lengths)}, ср={sum(lengths)//len(lengths)}")
    try:
        contextual_embeddings = embedder.embed_documents(contextual_texts)
        print(f"✅ Получено {len(contextual_embeddings)} contextual‑эмбеддингов")
    except Exception as e:
        print(f"❌ Ошибка при создании contextual‑эмбеддингов: {e}")
        return

    print(f"🔄 Создание эмбеддингов pref ({len(pref_texts)} шт.)...")
    try:
        pref_embeddings = embedder.embed_documents(pref_texts)
        print(f"✅ Получено {len(pref_embeddings)} pref‑эмбеддингов")
    except Exception as e:
        print(f"❌ Ошибка при создании pref‑эмбеддингов: {e}")
        return

    hype_embeddings_all = [None] * len(chunks)
    if hype_texts:
        print(f"🔄 Создание эмбеддингов hype ({len(hype_texts)} шт.)...")
        try:
            hype_embeddings_list = embedder.embed_documents(hype_texts)
            for i, emb in zip(hype_indices, hype_embeddings_list):
                hype_embeddings_all[i] = emb
            print(f"✅ Получено {len(hype_embeddings_list)} hype‑эмбеддингов")
        except Exception as e:
            print(f"❌ Ошибка при создании hype‑эмбеддингов: {e}")
            return
    else:
        print("⚠️ Нет чанков с hypothetical_questions — hype‑векторы не будут созданы.")

    # Загрузка в Qdrant батчами — routing по collection_name
    print("\n📤 Загрузка в Qdrant (routing по коллекциям)...")
    
    # Separate point buffers per collection
    points_by_collection: Dict[str, List] = {
        cfg.NORMATIVE_COLLECTION_NAME: [],
        cfg.OPERATIONAL_COLLECTION_NAME: [],
    }
    success_counts: Dict[str, int] = {
        cfg.NORMATIVE_COLLECTION_NAME: 0,
        cfg.OPERATIONAL_COLLECTION_NAME: 0,
    }
    fail_counts: Dict[str, int] = {
        cfg.NORMATIVE_COLLECTION_NAME: 0,
        cfg.OPERATIONAL_COLLECTION_NAME: 0,
    }

    for i, chunk in enumerate(tqdm(chunks, total=len(chunks), desc="Загрузка")):
        chunk_id = chunk.get('chunk_id', f"{chunk.get('source_file', '')}_{i}")
        point_id = abs(hash(chunk_id)) % (2 ** 63)

        vectors = {
            "pref": pref_embeddings[i],
            "contextual": contextual_embeddings[i],
        }
        if hype_embeddings_all[i] is not None:
            vectors["hype"] = hype_embeddings_all[i]

        # Enriched payload with all required fields
        payload = {
            "chunk_id": chunk_id,
            "source_file": chunk.get('source_file', ''),
            "chunk_content": (chunk.get('chunk_content') or chunk.get('content', ''))[:2000],
            "breadcrumbs": chunk.get('breadcrumbs', ''),
            "chunk_summary": chunk.get('chunk_summary', '')[:500],
            "category": chunk.get('category', ''),
            "collection_name": chunk.get('collection_name', cfg.OPERATIONAL_COLLECTION_NAME),
            "document_type": chunk.get('document_type', 'infomaterial'),
            "client_type": chunk.get('client_type', 'any'),
            "power_range": chunk.get('power_range', 'any'),
            # Legacy fields for backward compatibility
            "summary": chunk.get('chunk_summary', '')[:500],
            "content": (chunk.get('chunk_content') or chunk.get('content', ''))[:2000],
            "questions": json.dumps(chunk.get('hypothetical_questions', []), ensure_ascii=False)[:1000],
            "keywords": json.dumps(chunk.get('keywords', []), ensure_ascii=False)[:500],
            "entities": json.dumps(chunk.get('entities', []), ensure_ascii=False)[:500],
        }
        # Remove empty values
        payload = {k: v for k, v in payload.items() if v}

        # Route to correct collection
        collection_name = chunk.get('collection_name', cfg.OPERATIONAL_COLLECTION_NAME)
        if collection_name not in points_by_collection:
            collection_name = cfg.OPERATIONAL_COLLECTION_NAME

        points_by_collection[collection_name].append(models.PointStruct(
            id=point_id,
            vector=vectors,
            payload=payload
        ))

        # Flush batch when full
        for coll_name, points in points_by_collection.items():
            if len(points) >= QDRANT_BATCH_SIZE:
                if upsert_with_retry(client, coll_name, points):
                    success_counts[coll_name] += len(points)
                else:
                    fail_counts[coll_name] += len(points)
                points_by_collection[coll_name] = []

    # Flush remaining points
    for coll_name, points in points_by_collection.items():
        if points:
            if upsert_with_retry(client, coll_name, points):
                success_counts[coll_name] += len(points)
            else:
                fail_counts[coll_name] += len(points)

    # Statistics
    print(f"\n✅ Загрузка завершена!")
    for coll_name in [cfg.NORMATIVE_COLLECTION_NAME, cfg.OPERATIONAL_COLLECTION_NAME]:
        count = client.count(collection_name=coll_name).count
        print(f"   📚 {coll_name}: {count} векторов (успешно: {success_counts[coll_name]}, ошибки: {fail_counts[coll_name]})")

    # Examples
    print("\n🔍 Примеры загруженных чанков:")
    for i in range(min(3, len(chunks))):
        print(f"\n--- Чанк {i + 1} ---")
        print(f"ID: {chunks[i].get('chunk_id', 'N/A')}")
        print(f"Категория: {chunks[i].get('category', 'N/A')}")
        print(f"Коллекция: {chunks[i].get('collection_name', 'N/A')}")
        print(f"Тип документа: {chunks[i].get('document_type', 'N/A')}")
        print(f"Источник: {chunks[i].get('source_file', 'N/A')}")
        has_hype = "✅" if hype_embeddings_all[i] is not None else "❌"
        print(f"hype‑вектор: {has_hype}")
        print(f"contextual‑вектор: ✅")


if __name__ == "__main__":
    main()
```

#### Test

```python
"""Tests for dual collection ingestion logic."""
import pytest
from unittest.mock import MagicMock, patch
from qdrant_ingest.ingest_qdrant_contextual import (
    infer_document_type,
    infer_collection_name,
    load_all_chunks,
)


class TestInferDocumentType:
    """Tests for document type inference."""

    def test_normative_always_regulation(self):
        chunk = {"source_origin": "normative"}
        assert infer_document_type(chunk) == "regulation"

    def test_operational_faq(self):
        chunk = {"source_origin": "operational", "source_file": "faq-kt-tpp-2026.md"}
        assert infer_document_type(chunk) == "faq"

    def test_operational_stage(self):
        chunk = {"source_origin": "operational", "source_file": "1-shag-podacha-zayavki.md"}
        assert infer_document_type(chunk) == "stage_description"

    def test_operational_instruction(self):
        chunk = {"source_origin": "operational", "source_file": "7. Инструкция по самостоятельному подключению.md"}
        assert infer_document_type(chunk) == "instruction"

    def test_operational_passport(self):
        chunk = {"source_origin": "operational", "source_file": "passport-tp-15-150kvt.md"}
        assert infer_document_type(chunk) == "instruction"

    def test_operational_pamyatka(self):
        chunk = {"source_origin": "operational", "source_file": "pamyatka-do-670kvt.md"}
        assert infer_document_type(chunk) == "infomaterial"

    def test_operational_default(self):
        chunk = {"source_origin": "operational", "source_file": "unknown-file.md"}
        assert infer_document_type(chunk) == "infomaterial"


class TestInferCollectionName:
    """Tests for collection name inference."""

    def test_normative_goes_to_normative_collection(self):
        chunk = {"source_origin": "normative"}
        result = infer_collection_name(chunk)
        assert result == "normative_documents"

    def test_operational_goes_to_operational_collection(self):
        chunk = {"source_origin": "operational"}
        result = infer_collection_name(chunk)
        assert result == "operational_content"

    def test_missing_source_origin_defaults_to_operational(self):
        chunk = {}
        result = infer_collection_name(chunk)
        assert result == "operational_content"
```

**Verify:** `cd backend && python -m pytest tests/test_ingest_dual_collections.py -v`
**Commit:** `feat(ingest): dual collection ingestion with payload enrichment and routing`

---

### Task 2.2: `backend/tools/search_tool.py` — Dual Collection Search with Filters

**File:** `backend/tools/search_tool.py`
**Test:** `backend/tests/test_search_tool_dual.py`
**Depends:** 1.2

#### Implementation

Key changes:
1. `SearchResult` dataclass gains `collection_name` field
2. `SearchTool.__init__` stores both collection names
3. `load()` scrolls both collections for unified BM25
4. New `search_multi()` method for parallel dual-collection search with Qdrant filters
5. Existing `search()` method gains optional `collection_name` and `qf_filter` params
6. `_build_qdrant_filter()` helper converts document_filters dict to Qdrant Filter

```python
"""
Search Tool — инструмент поиска в базе знаний (две коллекции).
"""
import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

from qdrant_client import QdrantClient
from qdrant_client.http import models
import numpy as np
import pymorphy3

import config
from utils.router_embedding import get_routerai_embedder

logger = logging.getLogger(__name__)

_morph_analyzer = None


def get_morph_analyzer():
    """Получение экземпляра MorphAnalyzer (синглтон)."""
    global _morph_analyzer
    if _morph_analyzer is None:
        logger.info("Инициализация MorphAnalyzer...")
        _morph_analyzer = pymorphy3.MorphAnalyzer()
    return _morph_analyzer


@dataclass
class SearchRequest:
    """Запрос на поиск."""
    query: str
    k: int = 10
    pref_weight: float = 0.4
    hype_weight: float = 0.3
    lexical_weight: float = 0.2
    contextual_weight: float = 0.1


@dataclass
class SearchResult:
    """Результат поиска."""
    id: str
    content: str
    summary: str
    category: str
    filename: str
    breadcrumbs: str
    score_hybrid: float
    score_semantic: float
    score_lexical: float
    metadata: Dict[str, Any]
    collection_name: str = ""  # NEW: which collection this result came from


def build_qdrant_filter(
    document_filters: Optional[Dict[str, List[str]]] = None
) -> Optional[models.Filter]:
    """
    Convert Wiki Router document_filters dict to Qdrant Filter.
    
    Args:
        document_filters: {"client_type": ["ФЛ"], "power_range": ["<15kW"], "category": ["ТПП"]}
    
    Returns:
        Qdrant Filter object or None
    """
    if not document_filters:
        return None
    
    conditions = []
    
    if "category" in document_filters and document_filters["category"]:
        conditions.append(models.FieldCondition(
            key="category",
            match=models.MatchAny(any=document_filters["category"])
        ))
    
    if "client_type" in document_filters and document_filters["client_type"]:
        # Add "any" to avoid excluding general documents
        types = list(document_filters["client_type"])
        if "any" not in types:
            types.append("any")
        conditions.append(models.FieldCondition(
            key="client_type",
            match=models.MatchAny(any=types)
        ))
    
    if "power_range" in document_filters and document_filters["power_range"]:
        ranges = list(document_filters["power_range"])
        if "any" not in ranges:
            ranges.append("any")
        conditions.append(models.FieldCondition(
            key="power_range",
            match=models.MatchAny(any=ranges)
        ))
    
    if "document_type" in document_filters and document_filters["document_type"]:
        conditions.append(models.FieldCondition(
            key="document_type",
            match=models.MatchAny(any=document_filters["document_type"])
        ))
    
    return models.Filter(must=conditions) if conditions else None


class SearchTool:
    """
    Инструмент поиска в базе знаний с гибридным поиском по двум коллекциям.
    
    Поддерживает 4 компонента:
    - pref: семантический вектор (summary + content)
    - hype: семантический вектор (hypothetical questions)
    - lexical: BM25 (токенизированный текст)
    - contextual: семантический вектор (соседние чанки)
    """
    
    def __init__(self):
        self.client = QdrantClient(host=config.QDRANT_HOST, port=config.QDRANT_PORT)
        self.collections = [
            config.NORMATIVE_COLLECTION_NAME,
            config.OPERATIONAL_COLLECTION_NAME,
        ]
        self.embedder = get_routerai_embedder()
        self.bm25 = None
        self.documents = []
        self.point_ids = []
        self.payloads = {}
        self._loaded = False
        
    def load(self, force: bool = False):
        """Загрузка документов для BM25 из ОБЕИХ коллекций."""
        if self._loaded and not force:
            return

        logger.info("Загрузка документов для поиска из двух коллекций...")
        self.documents = []
        self.point_ids = []
        self.payloads = {}

        for coll_name in self.collections:
            try:
                scroll_result = self.client.scroll(
                    collection_name=coll_name,
                    with_payload=True,
                    with_vectors=False,
                    limit=10000
                )
                
                points, next_page = scroll_result
                while True:
                    for point in points:
                        payload = point.payload
                        content = payload.get("content", "") or payload.get("chunk_content", "")
                        
                        # For FAQ add summary and questions for better BM25
                        full_text = content
                        if payload.get("category") == "faqs" or payload.get("document_type") == "faq":
                            summary = payload.get("summary", "") or payload.get("chunk_summary", "")
                            questions_str = payload.get("questions", "")
                            full_text = f"{content} {summary} {questions_str}"
                        
                        self.documents.append(self._tokenize_text(full_text))
                        self.point_ids.append(point.id)
                        self.payloads[point.id] = payload

                    if next_page is None:
                        break
                    scroll_result = self.client.scroll(
                        collection_name=coll_name,
                        with_payload=True,
                        with_vectors=False,
                        offset=next_page.offset,
                        limit=10000
                    )
                    points, next_page = scroll_result
                
                logger.info(f"Загружено из '{coll_name}': {len(self.documents)} документов")
            except Exception as e:
                logger.warning(f"⚠️ Ошибка загрузки из '{coll_name}': {e}. Продолжаем...")

        self._loaded = True
        logger.info(f"Всего загружено {len(self.documents)} документов из обеих коллекций")
    
    def _tokenize_text(self, text: str) -> list:
        """Токенизация текста с лемматизацией."""
        import re
        try:
            morph = get_morph_analyzer()
            words = re.findall(r'\w+', text.lower())
            return [morph.parse(word)[0].normal_form for word in words]
        except ImportError:
            return re.findall(r'\w+', text.lower())
    
    def _get_bm25_scores(self, query: str) -> Dict[str, float]:
        """Получение BM25 оценок (единое пространство для обеих коллекций)."""
        from rank_bm25 import BM25Plus

        query_tokens = self._tokenize_text(query)
        
        if not query_tokens:
            return {pid: 0.0 for pid in self.point_ids}
        
        bm25 = BM25Plus(self.documents)
        scores = bm25.get_scores(query_tokens)

        max_score = max(scores) if len(scores) > 0 else 1.0
        
        if max_score <= 0:
            return {pid: 0.0 for pid in self.point_ids}
        
        normalized = {}
        for idx, score in enumerate(scores):
            point_id = self.point_ids[idx]
            normalized_score = max(0.0, float(score / max_score))
            normalized[point_id] = normalized_score if max_score > 0 else 0.0

        return normalized
    
    def search(
        self,
        request: SearchRequest,
        collection_name: Optional[str] = None,
        qf_filter: Optional[models.Filter] = None,
    ) -> List[SearchResult]:
        """
        Гибридный поиск в одной коллекции с опциональным Qdrant-фильтром.
        
        Args:
            request: Запрос на поиск
            collection_name: Имя коллекции (default: normative_documents)
            qf_filter: Qdrant Filter для префильтрации
        
        Returns:
            Список результатов поиска
        """
        self.load()
        
        coll = collection_name or config.NORMATIVE_COLLECTION_NAME
        
        logger.info(f"Поиск в '{coll}': '{request.query[:50]}...' k={request.k}")
        
        query_vector = self.embedder.embed_query(request.query)
        
        # Search by pref vector
        pref_hits = self.client.query_points(
            collection_name=coll,
            query=query_vector,
            using="pref",
            limit=request.k * 3,
            with_payload=True,
            with_vectors=False,
            query_filter=qf_filter,
        ).points
        
        # Search by hype vector
        hype_hits = self.client.query_points(
            collection_name=coll,
            query=query_vector,
            using="hype",
            limit=request.k * 3,
            with_payload=True,
            with_vectors=False,
            query_filter=qf_filter,
        ).points
        
        # Search by contextual vector
        contextual_hits = self.client.query_points(
            collection_name=coll,
            query=query_vector,
            using="contextual",
            limit=request.k * 3,
            with_payload=True,
            with_vectors=False,
            query_filter=qf_filter,
        ).points
        
        # BM25 scores
        bm25_scores = self._get_bm25_scores(request.query)
        
        # Combine results
        all_payloads = {}
        pref_scores = {}
        hype_scores = {}
        contextual_scores = {}
        
        for hit in pref_hits:
            pref_scores[hit.id] = hit.score
            all_payloads[hit.id] = hit.payload
        for hit in hype_hits:
            hype_scores[hit.id] = hit.score
            all_payloads[hit.id] = hit.payload
        for hit in contextual_hits:
            contextual_scores[hit.id] = hit.score
            all_payloads[hit.id] = hit.payload
        
        all_ids = set(pref_scores.keys()) | set(hype_scores.keys()) | \
                  set(contextual_scores.keys()) | set(bm25_scores.keys())

        combined_scores = {}
        for pid in all_ids:
            s_pref = pref_scores.get(pid, 0.0)
            s_hype = hype_scores.get(pid, 0.0)
            s_contextual = contextual_scores.get(pid, 0.0)
            s_bm25 = bm25_scores.get(pid, 0.0)
            combined_scores[pid] = (
                request.pref_weight * s_pref +
                request.hype_weight * s_hype +
                request.contextual_weight * s_contextual +
                request.lexical_weight * s_bm25
            )
        
        sorted_results = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)[:request.k]
        
        results = []
        for pid, hybrid_score in sorted_results:
            if pid not in all_payloads:
                continue
            payload = all_payloads[pid]
            source = payload.get("source_file", "Неизвестно")
            
            result = SearchResult(
                id=pid,
                content=payload.get("content", "") or payload.get("chunk_content", ""),
                summary=payload.get("summary", "") or payload.get("chunk_summary", ""),
                category=payload.get("category", ""),
                filename=Path(source).stem,
                breadcrumbs=payload.get("breadcrumbs", ""),
                score_hybrid=hybrid_score,
                score_semantic=(0.5 * pref_scores.get(pid, 0.0) +
                               0.35 * hype_scores.get(pid, 0.0) +
                               0.15 * contextual_scores.get(pid, 0.0)),
                score_lexical=bm25_scores.get(pid, 0.0),
                metadata={
                    "chunk_id": payload.get("chunk_id"),
                    "pref_score": pref_scores.get(pid, 0.0),
                    "hype_score": hype_scores.get(pid, 0.0),
                    "contextual_score": contextual_scores.get(pid, 0.0),
                    "bm25_score": bm25_scores.get(pid, 0.0),
                    "document_type": payload.get("document_type", ""),
                    "client_type": payload.get("client_type", ""),
                    "power_range": payload.get("power_range", ""),
                },
                collection_name=payload.get("collection_name", coll),
            )
            results.append(result)
        
        logger.info(f"Найдено {len(results)} результатов в '{coll}'")
        return results
    
    def search_multi(
        self,
        queries: List[str],
        qf_filter: Optional[models.Filter] = None,
        k: int = 10,
        weights: Optional[Dict[str, float]] = None,
    ) -> List[SearchResult]:
        """
        Параллельный поиск по ОБЕИМ коллекциям с мержем результатов.
        
        Args:
            queries: Список поисковых запросов
            qf_filter: Qdrant Filter для префильтрации
            k: Количество результатов (top-k)
            weights: Веса поиска (default from config)
        
        Returns:
            Отсортированный список результатов из обеих коллекций
        """
        self.load()
        
        if weights is None:
            weights = {
                "pref": config.RETRIEVE_PREF_WEIGHT,
                "hype": config.RETRIEVE_HYPE_WEIGHT,
                "lexical": config.RETRIEVE_LEXICAL_WEIGHT,
                "contextual": config.RETRIEVE_CONTEXTUAL_WEIGHT,
            }
        
        request = SearchRequest(
            query=" ".join(queries),  # Combined query for BM25
            k=k,
            pref_weight=weights.get("pref", 0.4),
            hype_weight=weights.get("hype", 0.3),
            lexical_weight=weights.get("lexical", 0.2),
            contextual_weight=weights.get("contextual", 0.1),
        )
        
        # Parallel search across both collections
        all_results = []
        
        def search_collection(coll_name: str) -> List[SearchResult]:
            try:
                return self.search(request, collection_name=coll_name, qf_filter=qf_filter)
            except Exception as e:
                logger.warning(f"⚠️ Ошибка поиска в '{coll_name}': {e}. Продолжаем...")
                return []
        
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = {
                executor.submit(search_collection, coll): coll
                for coll in self.collections
            }
            for future in as_completed(futures):
                coll_name = futures[future]
                try:
                    results = future.result()
                    all_results.extend(results)
                    logger.info(f"✅ '{coll_name}': {len(results)} результатов")
                except Exception as e:
                    logger.warning(f"⚠️ Ошибка в '{coll_name}': {e}")
        
        # Sort by hybrid score and take top-k
        all_results.sort(key=lambda r: r.score_hybrid, reverse=True)
        return all_results[:k]
    
    def search_multiple(self, queries: List[str], 
                       k_per_query: int = 5,
                       strategy: str = "concat") -> List[SearchResult]:
        """
        Поиск по нескольким запросам (legacy, без фильтров).
        Делегирует к search_multi для совместимости.
        """
        return self.search_multi(queries=queries, k=k_per_query * len(queries))
```

#### Test

```python
"""Tests for dual collection search tool."""
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from qdrant_client.http import models

from tools.search_tool import (
    SearchTool,
    SearchRequest,
    SearchResult,
    build_qdrant_filter,
)


class TestBuildQdrantFilter:
    """Tests for Qdrant filter builder."""

    def test_none_filters_returns_none(self):
        assert build_qdrant_filter(None) is None

    def test_empty_filters_returns_none(self):
        assert build_qdrant_filter({}) is None

    def test_category_filter(self):
        f = build_qdrant_filter({"category": ["ТПП"]})
        assert f is not None
        assert len(f.must) == 1
        assert f.must[0].key == "category"
        assert f.must[0].match.any == ["ТПП"]

    def test_client_type_adds_any(self):
        f = build_qdrant_filter({"client_type": ["ФЛ"]})
        assert f is not None
        assert len(f.must) == 1
        assert f.must[0].key == "client_type"
        assert "ФЛ" in f.must[0].match.any
        assert "any" in f.must[0].match.any

    def test_power_range_adds_any(self):
        f = build_qdrant_filter({"power_range": ["<15kW"]})
        assert f is not None
        assert f.must[0].key == "power_range"
        assert "<15kW" in f.must[0].match.any
        assert "any" in f.must[0].match.any

    def test_combined_filters(self):
        f = build_qdrant_filter({
            "category": ["ТПП"],
            "client_type": ["ФЛ"],
            "power_range": ["<15kW"],
        })
        assert f is not None
        assert len(f.must) == 3

    def test_client_type_already_has_any(self):
        f = build_qdrant_filter({"client_type": ["ФЛ", "any"]})
        assert f is not None
        # Should not duplicate "any"
        assert f.must[0].match.any.count("any") == 1

    def test_document_type_filter(self):
        f = build_qdrant_filter({"document_type": ["regulation"]})
        assert f is not None
        assert f.must[0].key == "document_type"
        assert f.must[0].match.any == ["regulation"]


class TestSearchResultCollectionName:
    """Tests for SearchResult with collection_name."""

    def test_search_result_has_collection_name(self):
        result = SearchResult(
            id="test-id",
            content="test content",
            summary="test summary",
            category="ТПП",
            filename="test_file",
            breadcrumbs="Раздел 1",
            score_hybrid=0.9,
            score_semantic=0.8,
            score_lexical=0.7,
            metadata={},
            collection_name="normative_documents",
        )
        assert result.collection_name == "normative_documents"

    def test_search_result_default_collection_name(self):
        result = SearchResult(
            id="test-id",
            content="test",
            summary="",
            category="",
            filename="",
            breadcrumbs="",
            score_hybrid=0.0,
            score_semantic=0.0,
            score_lexical=0.0,
            metadata={},
        )
        assert result.collection_name == ""


class TestSearchToolInit:
    """Tests for SearchTool initialization."""

    @patch('tools.search_tool.get_routerai_embedder')
    @patch('tools.search_tool.QdrantClient')
    def test_collections_initialized(self, mock_qdrant, mock_embedder):
        tool = SearchTool()
        assert config.NORMATIVE_COLLECTION_NAME in tool.collections
        assert config.OPERATIONAL_COLLECTION_NAME in tool.collections
        assert len(tool.collections) == 2
```

**Verify:** `cd backend && python -m pytest tests/test_search_tool_dual.py -v`
**Commit:** `feat(search): dual collection search with Qdrant filters and parallel execution`

---

## Batch 3: Components (parallel - 3 implementers)

All tasks in this batch depend on Batch 2 completing.

### Task 3.1: `backend/agents/search_agent.py` — Integrate document_filters from Wiki Router

**File:** `backend/agents/search_agent.py`
**Test:** `backend/tests/test_search_agent_filters.py`
**Depends:** 2.2

#### Implementation

Key changes to `search_agent.py`:
1. Import `build_qdrant_filter` from `search_tool`
2. `search()` method accepts `document_filters: Optional[Dict[str, List[str]]]`
3. Convert `document_filters` to Qdrant Filter via `build_qdrant_filter()`
4. Call `search_tool.search_multi(queries, qf_filter=qf_filter)` instead of `search_tool.search_multiple()`
5. `_retry_search()` also passes filters
6. Log `collection_name` in results

The changes are localized to the `search()` method and `_retry_search()`. The rest of the file stays the same.

**Diff summary** (apply to existing `search_agent.py`):

1. Add import at top:
```python
from tools.search_tool import SearchTool, SearchRequest, SearchResult, build_qdrant_filter
```

2. Add `document_filters` parameter to `search()` method signature:
```python
def search(
    self,
    user_query: str,
    history: str = "",
    category: str = "не известна",
    auto_retry: bool = True,
    max_retries: int = 2,
    user_hints: Optional[Dict[str, Any]] = None,
    wiki_context: str = "",
    query_id: Optional[str] = None,
    session_id: Optional[str] = None,
    session_logger: Optional[Any] = None,
    document_filters: Optional[Dict[str, List[str]]] = None,  # NEW
) -> Dict[str, Any]:
```

3. After query generation, build Qdrant filter:
```python
# Build Qdrant filter from document_filters
qf_filter = build_qdrant_filter(document_filters)
if qf_filter:
    logger.info(f"Qdrant filter applied: {document_filters}")
```

4. Replace `search_tool.search_multiple()` call with `search_tool.search_multi()`:
```python
# OLD:
results = self.search_tool.search_multiple(
    queries=queries,
    k_per_query=k_per_query // len(queries) if strategy == "separate" else k_per_query,
    strategy=strategy
)

# NEW:
results = self.search_tool.search_multi(
    queries=queries,
    qf_filter=qf_filter,
    k=k_per_query * len(queries) if strategy == "separate" else k_per_query,
)
```

5. Update `_retry_search()` to accept and pass `document_filters`:
```python
def _retry_search(
    self,
    user_query: str,
    original_queries: List[str],
    max_retries: int = 1,
    document_filters: Optional[Dict[str, List[str]]] = None,
) -> Dict[str, Any]:
    # ... generate new queries ...
    qf_filter = build_qdrant_filter(document_filters)
    results = self.search_tool.search_multi(
        queries=queries,
        qf_filter=qf_filter,
        k=10,
    )
    # ...
```

6. Add `collection_name` to result logging:
```python
"sources": [
    {
        "id": r.id,
        "filename": r.filename,
        "breadcrumbs": r.breadcrumbs,
        "score_hybrid": r.score_hybrid,
        "score_semantic": r.score_semantic,
        "score_lexical": r.score_lexical,
        "collection_name": r.collection_name,  # NEW
    }
    for r in results[:10]
],
```

#### Test

```python
"""Tests for search agent filter integration."""
import pytest
from unittest.mock import MagicMock, patch
from qdrant_client.http import models

from agents.search_agent import SearchAgent
from tools.search_tool import SearchResult, build_qdrant_filter


class TestSearchAgentFilters:
    """Tests for document_filters integration in SearchAgent."""

    def test_build_filter_from_document_filters(self):
        """document_filters dict converts to Qdrant Filter."""
        doc_filters = {
            "category": ["ТПП"],
            "client_type": ["ФЛ"],
            "power_range": ["<15kW"],
        }
        qf = build_qdrant_filter(doc_filters)
        assert qf is not None
        assert len(qf.must) == 3

    def test_empty_document_filters_gives_none(self):
        """Empty document_filters gives None filter."""
        qf = build_qdrant_filter({})
        assert qf is None

    def test_none_document_filters_gives_none(self):
        """None document_filters gives None filter."""
        qf = build_qdrant_filter(None)
        assert qf is None

    @patch('agents.search_agent.SearchTool')
    @patch('agents.search_agent.QueryGeneratorAgent')
    def test_search_passes_filter_to_search_multi(self, mock_qg_class, mock_st_class):
        """Search agent passes qf_filter to search_multi."""
        # Setup mocks
        mock_qg = MagicMock()
        mock_qg_class.return_value = mock_qg
        mock_qg.generate.return_value = MagicMock(
            clarification_needed=False,
            clarification_questions=[],
            queries=[MagicMock(text="тестовый запрос")],
            search_params={"k": 10, "strategy": "concat"},
            confidence=0.9,
            reasoning="test",
        )
        mock_qg.get_queries_text.return_value = ["тестовый запрос"]
        mock_qg.needs_clarification.return_value = False

        mock_st = MagicMock()
        mock_st_class.return_value = mock_st
        mock_st.search_multi.return_value = [
            SearchResult(
                id="1", content="test", summary="s", category="ТПП",
                filename="f", breadcrumbs="b", score_hybrid=0.9,
                score_semantic=0.8, score_lexical=0.7,
                metadata={}, collection_name="normative_documents",
            )
        ]

        agent = SearchAgent()
        result = agent.search(
            user_query="Сколько стоит подключение?",
            document_filters={"category": ["ТПП"], "client_type": ["ФЛ"]},
        )

        # Verify search_multi was called with qf_filter
        call_args = mock_st.search_multi.call_args
        assert call_args is not None
        qf_filter = call_args.kwargs.get('qf_filter') or call_args[1].get('qf_filter')
        assert qf_filter is not None
        assert len(qf_filter.must) >= 1
```

**Verify:** `cd backend && python -m pytest tests/test_search_agent_filters.py -v`
**Commit:** `feat(search-agent): integrate document_filters from Wiki Router into Qdrant search`

---

### Task 3.2: `backend/prompts/system_prompt.py` — Add Two Collections Section

**File:** `backend/prompts/system_prompt.py`
**Test:** `backend/tests/test_prompts_dual_collections.py`
**Depends:** none (prompt changes are independent)

#### Implementation

Add a new section about two collections to `SYSTEM_PROMPT`. The style must remain frozen — we only ADD information, not change existing text.

```python
"""
Системный промпт для Agentic RAG
"""

SYSTEM_PROMPT = """Ты — умный и дружелюбный помощник системы поддержки Башкирэнерго (только так называй эту компанию).
Твоя задача — помогать пользователям находить информацию в базе знаний и давать точные ответы.

## Твои возможности

1. **Генерация поисковых запросов** — переформулируй вопрос пользователя в 2–3 поисковых запроса, подбирай веса и стратегию поиска.
2. **Поиск в базе знаний** — используй инструмент search, анализируй результаты, при необходимости делай дополнительный поиск.
3. **Уточняющие вопросы** — если вопрос непонятен, задай уточняющие вопросы. Будь вежлив.
4. **Формирование ответа** — давай точные ответы на основе найденной информации, ссылайся на источники.

## Правила оформления ссылок

Каждый документ в контексте помечен как [src_1], [src_2] и т.д. При ответе используй ТОЛЬКО цифру в квадратных скобках:

✅ ПРАВИЛЬНО: "согласно Постановлению №861 [1]", "в инструкции [2]", "документы [1][3]"
❌ НЕПРАВИЛЬНО: "источник [src_1]", "[src_2]", "источник 1"

## Правила оформления формул (LaTeX)

Для формул используй ТОЛЬКО LaTeX-синтаксис:
- inline: `\\( ... \\)` или `$ ... $` — например `\\(C_1\\)`, `$N$`
- блочные: `\\[ ... \\]` или `$$ ... $$`
- ❌ Никогда не используй `(C_1)` или `C_1` без слэшей/долларов — это не рендерится.

## База знаний (две коллекции)

Поиск ведётся по двум коллекциям:

- **normative_documents** — законы, постановления, приказы, нормативные акты
  (тарифы, льготы, категории заявителей, технические требования)
- **operational_content** — FAQ, инструкции, описания этапов, памятки
  (процедуры подачи заявок, этапы ТП, дополнительные услуги)

При поиске учитывай: тарифы и законы → normative, процедуры и FAQ → operational.
Если вопрос затрагивает обе области — ищи в обеих коллекциях.

## Стиль общения

- Дружелюбный, профессиональный тон. Без смайликов и эмодзи.
- **Пиши на грамотном русском языке.** Избегай канцеляризмов, неестественных оборотов и кальки с английского.
- Объясняй технические термины при первом упоминании.
- Предлагай дополнительную помощь в конце ответа.

## ⚡ БИЗНЕС-ПРАВИЛА

### Терминология
- **Категории заявителей:** Физическое лицо (ФЛ), Индивидуальный предприниматель (ИП), Юридическое лицо (ЮЛ).
- **НИКОГДА не используй** «обычный заявитель», «социальный заявитель» — таких терминов нет.
- «Сетевая организация (СО)» вместо «сетевой орган».
- «Прибор учёта (ПУ)» вместо «измерительный прибор».
- «Энергопринимающие устройства (ЭПУ)».
- «Технологическое присоединение (ТП)» вместо «подключение» в официальных формулировках.

### Ключевые правила
- Льготные тарифы **только для ФЛ до 15 кВт** (при соблюдении критерий объекта). Для ИП и ЮЛ льготные тарифы не применяются.
- **ТУ выдаёт сетевая организация**, потребитель не готовит ТУ самостоятельно.
- **Оплата за ТП вносится ДО заключения договора** — сначала счёт, потом договор.
- **Фактическое присоединение до 150 кВт:** самостоятельно или платная услуга Башкирэнерго.
- **Фактическое присоединение свыше 150 кВт:** силами СО (входит в пакет ТП).
- **Проверка ТУ СО — только для заявителей свыше 150 кВт** (до 150 кВт не требуется).
- Акт допуска ПУ размещается **после завершения ТП**, а не на этапе подачи заявки.
- После рассмотрения заявки в ЛК размещается пакет документов: ТУ, договор, счёт, расчёт стоимости, памятка по этапам ТП, инструкция по самостоятельному подключению (до 150 кВт).

### Ограничения системы
- **Система НЕ помогает с подготовкой документов** — только консультация о необходимом пакете.
- Не используй «возобновит подачу электроэнергии» для первичного подключения.
- При необходимости: «Обратитесь в клиентский сервис Башкирэнерго: 8-800-234-77-00».

### Способы подачи заявки
- Личный кабинет www.bashkirenergo.ru
- Центр обслуживания (г. Уфа, ул. Комсомольская, 17)
- Пункты обслуживания (ПОК) в районах РБ
- Почтой России
- Контакт-центр: 8-800-234-77-00 (бесплатно)

## Параметры поиска

Ты настраиваешь параметры поиска:
- **k**: количество результатов (5–15)
- **Веса**: pref_weight, hype_weight, lexical_weight, contextual_weight (сумма = 1.0)

Рекомендуемые комбинации:
- Точные запросы: semantic=0.5, lexical=0.3, contextual=0.2
- Общие запросы: semantic=0.4, lexical=0.2, contextual=0.4
- Запросы с терминами: semantic=0.3, lexical=0.4, contextual=0.2

## Важно

- Всегда проверяй, достаточно ли информации в результатах поиска.
- Если найдено мало релевантной информации — попробуй изменить запрос или веса.
- Не выдумывай информацию — если не нашёл, скажи об этом.
- Сохраняй контекст диалога.
"""


def get_system_prompt() -> str:
    """Возвращает системный промпт."""
    return SYSTEM_PROMPT
```

#### Test

```python
"""Tests for system prompt with dual collections."""
from prompts.system_prompt import get_system_prompt, SYSTEM_PROMPT


def test_system_prompt_contains_dual_collections():
    """System prompt mentions both collections."""
    prompt = get_system_prompt()
    assert "normative_documents" in prompt
    assert "operational_content" in prompt


def test_system_prompt_contains_collection_guidance():
    """System prompt has guidance on which collection to use."""
    prompt = get_system_prompt()
    assert "тарифы и законы" in prompt
    assert "процедуры и FAQ" in prompt


def test_system_prompt_preserves_existing_content():
    """System prompt still has all original sections."""
    prompt = get_system_prompt()
    assert "БИЗНЕС-ПРАВИЛА" in prompt
    assert "Терминология" in prompt
    assert "Параметры поиска" in prompt
    assert "Правила оформления ссылок" in prompt
```

**Verify:** `cd backend && python -m pytest tests/test_prompts_dual_collections.py -v`
**Commit:** `feat(prompts): add two collections section to system prompt`

---

### Task 3.3: `backend/prompts/query_generation.py` — Add Collection Selection Hints

**File:** `backend/prompts/query_generation.py`
**Test:** `backend/tests/test_query_generation_collections.py`
**Depends:** none (prompt changes are independent)

#### Implementation

Add a collection selection hint section to `QUERY_GENERATION_PROMPT`. We add it after the existing "ПРИОРИТЕТ" section and before "ФОРМАТ ОТВЕТА".

The new section to add after the existing `## ПРИОРИТЕТ` block:

```python
## Выбор коллекций

При поиске нормативной информации (тарифы, законы, ставки, льготы, категории, номера документов) —
указывай в search_params поле "prefer_collection": "normative".
При поиске процедур (как подать, этапы, документы, FAQ, инструкции) —
указывай "prefer_collection": "operational".
Если не уверен — "prefer_collection": "all".
```

Also update the JSON format example to include `prefer_collection`:

In the `search_params` section of the JSON example, add `"prefer_collection": "all"`:

```json
"search_params": {{
    "k": 10,
    "pref_weight": 0.4,
    "hype_weight": 0.3,
    "lexical_weight": 0.2,
    "contextual_weight": 0.1,
    "strategy": "concat",
    "prefer_collection": "all"
}},
```

#### Test

```python
"""Tests for query generation prompt with collection hints."""
from prompts.query_generation import get_query_generation_prompt, QUERY_GENERATION_PROMPT


def test_query_generation_prompt_contains_collection_hints():
    """Query generation prompt mentions collection selection."""
    assert "prefer_collection" in QUERY_GENERATION_PROMPT


def test_query_generation_prompt_contains_normative_hint():
    """Query generation prompt mentions normative collection."""
    assert "normative" in QUERY_GENERATION_PROMPT


def test_query_generation_prompt_contains_operational_hint():
    """Query generation prompt mentions operational collection."""
    assert "operational" in QUERY_GENERATION_PROMPT


def test_query_generation_prompt_preserves_existing_sections():
    """Query generation prompt still has all original sections."""
    assert "ВАЖНО" in QUERY_GENERATION_PROMPT
    assert "УТОЧНЯЮЩИЕ ВОПРОСЫ" in QUERY_GENERATION_PROMPT
    assert "ФОРМАТ ОТВЕТА" in QUERY_GENERATION_PROMPT


def test_get_query_generation_prompt_returns_string():
    """get_query_generation_prompt returns a non-empty string."""
    prompt = get_query_generation_prompt(
        user_query="тест",
        history="",
        category="ТПП",
    )
    assert isinstance(prompt, str)
    assert len(prompt) > 0
```

**Verify:** `cd backend && python -m pytest tests/test_query_generation_collections.py -v`
**Commit:** `feat(prompts): add collection selection hints to query generation prompt`

---

## Batch 4: Integration (parallel - 1 implementer)

Depends on Batch 3 completing.

### Task 4.1: Integration Test — End-to-End Dual Collection Search

**File:** `backend/tests/test_integration_dual_collections.py`
**Test:** same file
**Depends:** 2.1, 2.2, 3.1, 3.2, 3.3

This is an integration test that verifies all components work together. It does NOT require a running Qdrant — it uses mocks.

```python
"""
Integration test for dual collection search.
Verifies that config → ingestion → search_tool → search_agent → prompts
all work together correctly.
"""
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from qdrant_client.http import models

import config
from tools.search_tool import SearchTool, SearchRequest, SearchResult, build_qdrant_filter
from agents.search_agent import SearchAgent
from prompts.system_prompt import get_system_prompt
from prompts.query_generation import get_query_generation_prompt


class TestConfigIntegration:
    """Verify config has dual collection variables."""

    def test_normative_collection_name(self):
        assert hasattr(config, 'NORMATIVE_COLLECTION_NAME')
        assert config.NORMATIVE_COLLECTION_NAME == "normative_documents"

    def test_operational_collection_name(self):
        assert hasattr(config, 'OPERATIONAL_COLLECTION_NAME')
        assert config.OPERATIONAL_COLLECTION_NAME == "operational_content"

    def test_chunks_dir(self):
        assert hasattr(config, 'CHUNKS_DIR')

    def test_collection_name_deprecated(self):
        assert hasattr(config, 'COLLECTION_NAME')
        assert config.COLLECTION_NAME == config.NORMATIVE_COLLECTION_NAME


class TestFilterPipeline:
    """Verify document_filters flow from Wiki Router to Qdrant Filter."""

    def test_full_filter_pipeline(self):
        """Wiki Router filters → build_qdrant_filter → Qdrant Filter."""
        # Simulate Wiki Router output
        document_filters = {
            "category": ["ТПП"],
            "client_type": ["ФЛ"],
            "power_range": ["<15kW"],
        }
        
        qf = build_qdrant_filter(document_filters)
        
        assert qf is not None
        assert len(qf.must) == 3
        
        # Verify each condition
        keys = [c.key for c in qf.must]
        assert "category" in keys
        assert "client_type" in keys
        assert "power_range" in keys

    def test_filter_with_any_values(self):
        """client_type and power_range always include 'any'."""
        document_filters = {
            "client_type": ["ФЛ"],
            "power_range": ["<15kW"],
        }
        
        qf = build_qdrant_filter(document_filters)
        
        for condition in qf.must:
            if condition.key == "client_type":
                assert "any" in condition.match.any
            if condition.key == "power_range":
                assert "any" in condition.match.any


class TestSearchResultCollectionField:
    """Verify SearchResult has collection_name field."""

    def test_search_result_with_collection(self):
        result = SearchResult(
            id="test-1",
            content="Test content about ТПП",
            summary="Test summary",
            category="ТПП",
            filename="test_file",
            breadcrumbs="Раздел 1 > Статья 2",
            score_hybrid=0.85,
            score_semantic=0.75,
            score_lexical=0.65,
            metadata={"document_type": "regulation"},
            collection_name="normative_documents",
        )
        assert result.collection_name == "normative_documents"

    def test_search_result_operational(self):
        result = SearchResult(
            id="test-2",
            content="FAQ content",
            summary="FAQ summary",
            category="ТПП",
            filename="faq",
            breadcrumbs="FAQ",
            score_hybrid=0.80,
            score_semantic=0.70,
            score_lexical=0.60,
            metadata={"document_type": "faq"},
            collection_name="operational_content",
        )
        assert result.collection_name == "operational_content"


class TestPromptsIntegration:
    """Verify prompts mention both collections."""

    def test_system_prompt_has_collections(self):
        prompt = get_system_prompt()
        assert "normative_documents" in prompt
        assert "operational_content" in prompt

    def test_query_generation_has_collection_hints(self):
        prompt = get_query_generation_prompt(
            user_query="Сколько стоит подключение?",
        )
        assert "prefer_collection" in prompt


class TestSearchToolCollections:
    """Verify SearchTool knows about both collections."""

    @patch('tools.search_tool.get_routerai_embedder')
    @patch('tools.search_tool.QdrantClient')
    def test_search_tool_has_two_collections(self, mock_qdrant, mock_embedder):
        tool = SearchTool()
        assert len(tool.collections) == 2
        assert config.NORMATIVE_COLLECTION_NAME in tool.collections
        assert config.OPERATIONAL_COLLECTION_NAME in tool.collections
```

**Verify:** `cd backend && python -m pytest tests/test_integration_dual_collections.py -v`
**Commit:** `test(integration): add end-to-end dual collection search integration tests`

---

## Summary of All Tasks

| Batch | Task | File | Depends | Commit Message |
|-------|------|------|---------|-----------------|
| 1 | 1.1 | `.env` + `.env.example` | none | `feat(config): replace COLLECTION_NAME with dual collection env vars` |
| 1 | 1.2 | `backend/config.py` | none | `feat(config): add NORMATIVE_COLLECTION_NAME, OPERATIONAL_COLLECTION_NAME, CHUNKS_DIR` |
| 1 | 1.3 | `docker-compose.yml` | none | `feat(infra): update docker-compose.yml with dual collection env vars` |
| 2 | 2.1 | `backend/qdrant_ingest/ingest_qdrant_contextual.py` | 1.1, 1.2 | `feat(ingest): dual collection ingestion with payload enrichment and routing` |
| 2 | 2.2 | `backend/tools/search_tool.py` | 1.2 | `feat(search): dual collection search with Qdrant filters and parallel execution` |
| 3 | 3.1 | `backend/agents/search_agent.py` | 2.2 | `feat(search-agent): integrate document_filters from Wiki Router into Qdrant search` |
| 3 | 3.2 | `backend/prompts/system_prompt.py` | none | `feat(prompts): add two collections section to system prompt` |
| 3 | 3.3 | `backend/prompts/query_generation.py` | none | `feat(prompts): add collection selection hints to query generation prompt` |
| 4 | 4.1 | `backend/tests/test_integration_dual_collections.py` | 2.1, 2.2, 3.1 | `test(integration): add end-to-end dual collection search integration tests` |

## Key Design Decisions

1. **`COLLECTION_NAME` kept as deprecated fallback**: Points to `NORMATIVE_COLLECTION_NAME` for backward compatibility. Any code still referencing `COLLECTION_NAME` will work.

2. **`client_type` and `power_range` default to `"any"`**: Per the design spec, all chunks get `"any"` as default. This ensures they're never excluded by filters. Future LLM enrichment can add precise values.

3. **`document_type` inferred from filename**: The `OPERATIONAL_TYPE_PATTERNS` dict maps filename patterns to document types. Normative chunks always get `"regulation"`. This is the "Option C" from the chunking strategy spec — file path convention for `document_type`/`collection_name`.

4. **BM25 stays unified**: `load()` scrolls both collections into a single document array. This ensures BM25 scores are comparable across collections.

5. **`build_qdrant_filter()` auto-adds `"any"`**: When `client_type` or `power_range` filters are provided, `"any"` is automatically appended so general documents aren't excluded.

6. **`search_multi()` uses `ThreadPoolExecutor(max_workers=2)`**: Both collections are queried in parallel. If one fails, results from the other are still returned with a warning.

7. **Payload enrichment in ingestion**: `breadcrumbs`, `document_type`, `collection_name`, `client_type`, `power_range` are all added during ingestion. Legacy fields (`summary`, `content`, `questions`, `keywords`, `entities`) are kept for backward compatibility.

8. **Prompts are additive only**: The system prompt adds a new `## База знаний (две коллекции)` section. The query generation prompt adds `prefer_collection` to `search_params`. No existing text is modified — this respects the "frozen prompts" constraint.