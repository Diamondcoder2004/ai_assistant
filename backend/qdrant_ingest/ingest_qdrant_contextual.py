#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Загрузка чанков в Qdrant с ТРЕМЯ векторами (pref + hype + contextual).
contextual = предыдущий чанк + текущий чанк + следующий чанк
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
EMBEDDING_BATCH_SIZE = 32  # Батч для эмбеддингов (API)
QDRANT_BATCH_SIZE = 50  # Батч для загрузки в Qdrant (уменьшено!)
QDRANT_TIMEOUT = 60  # Timeout в секундах
QDRANT_RETRIES = 3  # Повторы при ошибке upsert
HYPE_JOINER = " | "
CONTEXTUAL_JOINER = "\n\n---\n\n"  # Разделитель для контекстных чанков


# =============================================


# ================= КЛИЕНТ ДЛЯ ЭМБЕДДИНГОВ =================
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
                # Проверка на None
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
                # Логируем проблемные тексты для отладки
                print(f"🔍 Problematic batch texts (first 3):")
                for j, txt in enumerate(batch[:3]):
                    print(f"   Text {j}: len={len(txt)}, preview={txt[:100]}...")
                raise
        return all_embedding


def get_routerai_embedder() -> RouterAIEmbedder:
    """Возвращает экземпляр эмбеддера."""
    return RouterAIEmbedder(
        api_key=cfg.ROUTERAI_API_KEY,
        base_url=cfg.ROUTERAI_BASE_URL,
        model=cfg.EMBEDDING_MODEL,
        batch_size=EMBEDDING_BATCH_SIZE
    )


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
                all_chunks.append(chunk)
            except Exception as e:
                print(f"   ❌ Ошибка чтения {json_path.name}: {e}")

    print(f"✅ Всего загружено чанков: {len(all_chunks)}")
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
    # Замена нулевых байтов и других проблемных символов
    text = text.replace('\x00', '').replace('\ufffd', '')
    # Ограничение длины
    return text[:max_length]


def prepare_text_contextual(
    chunk: Dict[str, Any],
    prev_chunk: Optional[Dict[str, Any]],
    next_chunk: Optional[Dict[str, Any]]
) -> str:
    """
    Готовит текст для contextual-вектора: prev + current + next.
    """
    parts = []

    # Предыдущий чанк
    if prev_chunk:
        prev_content = prev_chunk.get('chunk_content') or prev_chunk.get('content', '')
        if prev_content:
            parts.append(f"[ПРЕДЫДУЩИЙ КОНТЕКСТ]\n{sanitize_text(prev_content, 4000)}")

    # Текущий чанк
    current_content = chunk.get('chunk_content') or chunk.get('content', '')
    if current_content:
        parts.append(f"[ТЕКУЩИЙ КОНТЕКСТ]\n{sanitize_text(current_content, 4000)}")

    # Следующий чанк
    if next_chunk:
        next_content = next_chunk.get('chunk_content') or next_chunk.get('content', '')
        if next_content:
            parts.append(f"[СЛЕДУЮЩИЙ КОНТЕКСТ]\n{sanitize_text(next_content, 4000)}")

    if not parts:
        return "пустой контекст"

    return CONTEXTUAL_JOINER.join(parts)


def sort_chunks_by_context(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Сортирует чанки для правильного контекстного соседства.
    Сначала по категории, потом по source_file, потом по chunk_id.
    """
    return sorted(
        chunks,
        key=lambda c: (
            c.get('category', ''),
            c.get('source_file', ''),
            c.get('chunk_id', '')
        )
    )


def recreate_collection(client: QdrantClient):
    """Удаляет коллекцию и создаёт заново с ТРЕМЯ именованными векторами."""
    print(f"💀 Удаление старой коллекции '{cfg.COLLECTION_NAME}'...")
    try:
        client.delete_collection(cfg.COLLECTION_NAME)
        print("✅ Коллекция удалена")
    except Exception as e:
        print(f"⚠️ Коллекция не существовала или ошибка: {e}")

    print(f"📦 Создание коллекции '{cfg.COLLECTION_NAME}' (размерность {cfg.EMBEDDING_DIM})...")
    client.create_collection(
        collection_name=cfg.COLLECTION_NAME,
        vectors_config={
            "pref": models.VectorParams(size=cfg.EMBEDDING_DIM, distance=models.Distance.COSINE),
            "hype": models.VectorParams(size=cfg.EMBEDDING_DIM, distance=models.Distance.COSINE),
            "contextual": models.VectorParams(size=cfg.EMBEDDING_DIM, distance=models.Distance.COSINE),
        }
    )
    print("✅ Коллекция готова с тремя векторами: pref, hype, contextual")


def upsert_with_retry(client: QdrantClient, points: List, retry_count: int = QDRANT_RETRIES):
    """Upsert с retry логикой при timeout"""
    for attempt in range(retry_count):
        try:
            client.upsert(collection_name=cfg.COLLECTION_NAME, points=points)
            return True
        except (ResponseHandlingException, TimeoutError) as e:
            if attempt == retry_count - 1:
                print(f"\n❌ Upsert failed after {retry_count} retries: {e}")
                return False
            wait_time = 2 ** attempt
            print(f"⚠️ Upsert timeout, retry {attempt + 1}/{retry_count} через {wait_time}с...")
            time.sleep(wait_time)
    return False


def main():
    print("=" * 60)
    print("🚀 ЗАГРУЗКА ЧАНКОВ С ТРЕМЯ ВЕКТОРАМИ (pref + hype + contextual)")
    print("=" * 60)
    print(f"📁 Источник: {cfg.CHUNKS_DIR}")
    print(f"📦 Коллекция: {cfg.COLLECTION_NAME}")
    print(f"🤖 Модель эмбеддингов: {cfg.EMBEDDING_MODEL}")
    print(f"📏 Размерность: {cfg.EMBEDDING_DIM}")
    print(f"🔢 Embedding батч: {EMBEDDING_BATCH_SIZE}")
    print(f"🔢 Qdrant батч: {QDRANT_BATCH_SIZE}")
    print(f"⏱️ Timeout: {QDRANT_TIMEOUT}с")
    print("=" * 60)

    # Подключение к Qdrant с timeout
    print("🔄 Подключение к Qdrant...")
    client = QdrantClient(
        host=cfg.QDRANT_HOST,
        port=cfg.QDRANT_PORT,
        timeout=QDRANT_TIMEOUT
    )

    # Пересоздание коллекции (раскомментируйте, если нужно)
    recreate_collection(client)

    # Загрузка чанков
    chunks = load_all_chunks()
    if not chunks:
        print("❌ Нет чанков для загрузки")
        return

    # Сортировка чанков для правильного контекста
    print("\n🔄 Сортировка чанков для контекстного соседства...")
    chunks = sort_chunks_by_context(chunks)

    # Подготовка текстов для pref, hype и contextual
    pref_texts = []
    hype_texts = []
    hype_indices = []
    contextual_texts = []

    print("\n📝 Подготовка текстов...")
    for idx, chunk in enumerate(tqdm(chunks, desc="Тексты")):
        # Pref
        pref_texts.append(prepare_text_pref(chunk))
        
        # Hype
        hype_text = prepare_text_hype(chunk)
        if hype_text is not None:
            hype_texts.append(hype_text)
            hype_indices.append(idx)
        else:
            print(f"⚠️ Чанк {chunk.get('chunk_id', 'unknown')} без hypothetical_questions")
        
        # Contextual (prev + current + next)
        prev_chunk = chunks[idx - 1] if idx > 0 else None
        next_chunk = chunks[idx + 1] if idx < len(chunks) - 1 else None
        contextual_text = prepare_text_contextual(chunk, prev_chunk, next_chunk)
        contextual_texts.append(contextual_text)

    # Инициализация эмбеддера
    print("\n🤖 Инициализация RouterAI эмбеддера...")
    embedder = get_routerai_embedder()

    # Получение эмбеддингов для contextual (ПЕРВЫМ!)
    print(f"🔄 Создание эмбеддингов contextual ({len(contextual_texts)} шт.)...")
    # Отладка: проверка длин текстов
    lengths = [len(t) for t in contextual_texts]
    print(f"   📊 Статистика длин contextual-текстов: мин={min(lengths)}, макс={max(lengths)}, ср={sum(lengths)//len(lengths)}")
    try:
        contextual_embeddings = embedder.embed_documents(contextual_texts)
        print(f"✅ Получено {len(contextual_embeddings)} contextual‑эмбеддингов")
    except Exception as e:
        print(f"❌ Ошибка при создании contextual‑эмбеддингов: {e}")
        return

    # Получение эмбеддингов для pref
    print(f"🔄 Создание эмбеддингов pref ({len(pref_texts)} шт.)...")
    try:
        pref_embeddings = embedder.embed_documents(pref_texts)
        print(f"✅ Получено {len(pref_embeddings)} pref‑эмбеддингов")
    except Exception as e:
        print(f"❌ Ошибка при создании pref‑эмбеддингов: {e}")
        return

    # Получение эмбеддингов для hype
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

    # Загрузка в Qdrant батчами
    print("\n📤 Загрузка в Qdrant...")
    points = []
    success_count = 0
    fail_count = 0

    for i, chunk in enumerate(tqdm(chunks, total=len(chunks), desc="Загрузка")):
        chunk_id = chunk.get('chunk_id', f"{chunk.get('source_file', '')}_{i}")
        point_id = abs(hash(chunk_id)) % (2 ** 63)

        # Формируем все три вектора
        vectors = {
            "pref": pref_embeddings[i],
            "contextual": contextual_embeddings[i],
        }
        if hype_embeddings_all[i] is not None:
            vectors["hype"] = hype_embeddings_all[i]

        payload = {
            "chunk_id": chunk_id,
            "source_file": chunk.get('source_file', ''),
            "category": chunk.get('category', ''),
            "summary": chunk.get('chunk_summary', '')[:500],
            "content": (chunk.get('chunk_content') or chunk.get('content', ''))[:2000],
            "questions": json.dumps(chunk.get('hypothetical_questions', []), ensure_ascii=False)[:1000],
            "keywords": json.dumps(chunk.get('keywords', []), ensure_ascii=False)[:500],
            "entities": json.dumps(chunk.get('entities', []), ensure_ascii=False)[:500],
        }
        payload = {k: v for k, v in payload.items() if v}

        points.append(models.PointStruct(
            id=point_id,
            vector=vectors,
            payload=payload
        ))

        # Батч + retry
        if len(points) >= QDRANT_BATCH_SIZE:
            if upsert_with_retry(client, points):
                success_count += len(points)
            else:
                fail_count += len(points)
            points = []

    # Остаток
    if points:
        if upsert_with_retry(client, points):
            success_count += len(points)
        else:
            fail_count += len(points)

    # Проверка результата
    count = client.count(collection_name=cfg.COLLECTION_NAME).count
    print(f"\n✅ Загрузка завершена!")
    print(f"   Успешно: {success_count}")
    print(f"   Ошибки: {fail_count}")
    print(f"   Векторов в базе: {count}")

    # Примеры
    print("\n🔍 Примеры загруженных чанков:")
    for i in range(min(3, len(chunks))):
        print(f"\n--- Чанк {i + 1} ---")
        print(f"ID: {chunks[i].get('chunk_id', 'N/A')}")
        print(f"Категория: {chunks[i].get('category', 'N/A')}")
        print(f"Источник: {chunks[i].get('source_file', 'N/A')}")
        has_hype = "✅" if hype_embeddings_all[i] is not None else "❌"
        print(f"hype‑вектор: {has_hype}")
        print(f"contextual‑вектор: ✅ (prev + current + next)")


if __name__ == "__main__":
    main()
