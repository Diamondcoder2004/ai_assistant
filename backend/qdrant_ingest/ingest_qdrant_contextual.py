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
EMBEDDING_BATCH_SIZE = 16
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


def infer_document_type(chunk: Dict[str, Any]) -> Optional[str]:
    """Infer document_type from source_origin and source_file (fallback only)."""
    # Если LLM уже проставил document_type — используем его
    existing = chunk.get("document_type")
    if existing and isinstance(existing, str) and existing.strip():
        return existing.strip()
    
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
    """Determine which Qdrant collection a chunk belongs to (LLM value priority)."""
    # Если LLM уже проставил collection_name — используем его
    existing = chunk.get("collection_name")
    if existing == "normative_documents":
        return cfg.NORMATIVE_COLLECTION_NAME
    if existing == "operational_content":
        return cfg.OPERATIONAL_COLLECTION_NAME
    
    # Fallback: по source_origin
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

        source_origin = "normative" if category == "normative" else "operational"
        for json_path in json_files:
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    chunk = json.load(f)
                chunk['source_origin'] = source_origin
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
        parts.append(content[:30000])
    if not parts:
        return "пустой чанк"
    return "\n\n".join(parts)


def prepare_text_hype(chunk: Dict[str, Any]) -> Optional[str]:
    """Готовит текст для hype‑вектора: все гипотетические вопросы."""
    questions = chunk.get('hypothetical_questions')
    if not questions or not isinstance(questions, list):
        return None
    return HYPE_JOINER.join(q for q in questions if q)


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
            parts.append(f"[ПРЕДЫДУЩИЙ КОНТЕКСТ]\n{sanitize_text(prev_content, 2000)}")
    current_content = chunk.get('chunk_content') or chunk.get('content', '')
    if current_content:
        parts.append(f"[ТЕКУЩИЙ КОНТЕКСТ]\n{sanitize_text(current_content, 2000)}")
    if next_chunk:
        next_content = next_chunk.get('chunk_content') or next_chunk.get('content', '')
        if next_content:
            parts.append(f"[СЛЕДУЮЩИЙ КОНТЕКСТ]\n{sanitize_text(next_content, 2000)}")
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
            "chunk_content": (chunk.get('chunk_content') or chunk.get('content', ''))[:8000],
            "breadcrumbs": chunk.get('breadcrumbs', ''),
            "chunk_summary": chunk.get('chunk_summary', '')[:8000],
            "category": chunk.get('category', ''),
            "collection_name": chunk.get('collection_name', cfg.OPERATIONAL_COLLECTION_NAME),
            "document_type": chunk.get('document_type', 'infomaterial'),
            "client_type": chunk.get('client_type', 'any'),
            "power_range": chunk.get('power_range', 'any'),
            # Legacy fields for backward compatibility
            "summary": chunk.get('chunk_summary', '')[:8000],
            "content": (chunk.get('chunk_content') or chunk.get('content', ''))[:8000],
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
