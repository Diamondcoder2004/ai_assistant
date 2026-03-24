"""
RouterAI Embeddings с поддержкой int8 конвертации
"""
import logging
from typing import List
import numpy as np

from openai import OpenAI
import config

logger = logging.getLogger(__name__)


def convert_embedding(emb: List[float]) -> List[float]:
    """
    Конвертация и нормализация эмбеддинга.
    
    Perplexity API возвращает int8 векторы (диапазон -127 до 127).
    Применяется двухэтапная обработка:
    1. Нормализация на диапазон [-1, 1] (int8 → float)
    2. L2 нормализация для cosine similarity
    """
    emb_array = np.array(emb, dtype=np.float32)
    
    # 1. Нормализация на диапазон [-1, 1] (int8 → float)
    emb_array = emb_array / 127.0
    
    # 2. L2 нормализация для cosine similarity
    norm = np.linalg.norm(emb_array)
    if norm > 0:
        emb_array = emb_array / norm
    
    return emb_array.tolist()


class RouterAIEmbeddings:
    """Класс для работы с эмбеддингами через RouterAI API."""
    
    def __init__(self):
        self.client = OpenAI(
            api_key=config.ROUTERAI_API_KEY,
            base_url=config.ROUTERAI_BASE_URL
        )
        self.model = config.EMBEDDING_MODEL
        logger.info(f"RouterAIEmbeddings инициализирован: {self.model}")
    
    def embed_query(self, query: str) -> List[float]:
        """
        Получение эмбеддинга для запроса.
        
        Args:
            query: Текст запроса
        
        Returns:
            Вектор эмбеддинга (L2 нормализованный)
        """
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=query
            )
            
            embedding = response.data[0].embedding
            
            # Конвертация int8 → float32 с нормализацией
            return convert_embedding(embedding)
            
        except Exception as e:
            logger.error(f"Ошибка получения эмбеддинга: {e}")
            raise
    
    def embed_documents(self, documents: List[str]) -> List[List[float]]:
        """
        Получение эмбеддингов для документов.
        
        Args:
            documents: Список текстов
        
        Returns:
            Список векторов эмбеддингов
        """
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=documents
            )
            
            embeddings = [item.embedding for item in response.data]
            
            # Конвертация каждого эмбеддинга
            return [convert_embedding(emb) for emb in embeddings]
            
        except Exception as e:
            logger.error(f"Ошибка получения эмбеддингов документов: {e}")
            raise


def get_routerai_embedder() -> RouterAIEmbeddings:
    """Фабричная функция для получения эмбеддера."""
    return RouterAIEmbeddings()
