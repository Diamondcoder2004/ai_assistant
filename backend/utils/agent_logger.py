"""
Логирование ответов агентов в JSON формате
"""
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class AgentLogger:
    """
    Логгер для записи ответов агентов в JSON формате.
    
    Записывает:
    - Входные данные (query, history, parameters)
    - Промежуточные результаты (queries_used, search_params)
    - Финальный ответ (answer, sources, confidence)
    - Метрики (timing, tokens)
    """
    
    def __init__(self, log_dir: str = "logs/agent_responses"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Файл для общего лога всех ответов
        self.main_log_file = self.log_dir / f"agent_responses_{datetime.now().strftime('%Y%m%d')}.jsonl"
        
        logger.info(f"AgentLogger инициализирован, директория: {self.log_dir}")
    
    def log_response(
        self,
        query_id: str,
        session_id: str,
        user_query: str,
        response_data: Dict[str, Any],
        timing_info: Optional[Dict[str, float]] = None,
        extra_metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Логирование ответа агента.
        
        Args:
            query_id: Уникальный ID запроса
            session_id: ID сессии
            user_query: Исходный вопрос пользователя
            response_data: Данные ответа (answer, sources, queries_used, и т.д.)
            timing_info: Информация о времени выполнения
            extra_metadata: Дополнительные метаданные
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "query_id": query_id,
            "session_id": session_id,
            "user_query": user_query,
            "response": {
                "answer": response_data.get("answer", ""),
                "sources": [
                    {
                        "id": src.get("id"),
                        "filename": src.get("filename"),
                        "breadcrumbs": src.get("breadcrumbs"),
                        "score_hybrid": src.get("score_hybrid"),
                        "score_semantic": src.get("score_semantic"),
                        "score_lexical": src.get("score_lexical"),
                    }
                    for src in response_data.get("sources", [])
                ],
                "queries_used": response_data.get("queries_used", []),
                "search_params": response_data.get("search_params", {}),
                "confidence": response_data.get("confidence", 0.0),
                "reasoning": response_data.get("reasoning", ""),
                "clarification_needed": response_data.get("clarification_needed", False),
                "clarification_questions": response_data.get("clarification_questions", []),
            },
            "timing": timing_info or {},
            "metadata": extra_metadata or {}
        }
        
        # Запись в JSONL файл (одна строка = один JSON объект)
        try:
            with open(self.main_log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False, default=str) + "\n")
            
            logger.debug(f"Записан ответ для query_id={query_id}")
            
            # Также создаём отдельный файл для детального просмотра (опционально)
            # self._write_detailed_log(query_id, log_entry)
            
        except Exception as e:
            logger.error(f"Ошибка записи лога агента: {e}")
    
    def _write_detailed_log(self, query_id: str, log_entry: Dict[str, Any]):
        """Запись детального лога в отдельный файл (для отладки)"""
        detailed_file = self.log_dir / f"query_{query_id}.json"
        try:
            with open(detailed_file, "w", encoding="utf-8") as f:
                json.dump(log_entry, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Ошибка записи детального лога: {e}")
    
    def get_logs_for_query(self, query_id: str) -> Optional[Dict[str, Any]]:
        """Получение лога для конкретного query_id"""
        try:
            with open(self.main_log_file, "r", encoding="utf-8") as f:
                for line in f:
                    entry = json.loads(line)
                    if entry.get("query_id") == query_id:
                        return entry
        except Exception as e:
            logger.error(f"Ошибка чтения лога: {e}")
        return None
    
    def get_logs_for_session(self, session_id: str, limit: int = 100) -> list:
        """Получение всех логов для сессии"""
        results = []
        try:
            with open(self.main_log_file, "r", encoding="utf-8") as f:
                for line in f:
                    entry = json.loads(line)
                    if entry.get("session_id") == session_id:
                        results.append(entry)
                        if len(results) >= limit:
                            break
        except Exception as e:
            logger.error(f"Ошибка чтения логов сессии: {e}")
        return results


# Глобальный экземпляр
agent_logger = AgentLogger()


def log_agent_response(
    query_id: str,
    session_id: str,
    user_query: str,
    response_data: Dict[str, Any],
    timing_info: Optional[Dict[str, float]] = None,
    extra_metadata: Optional[Dict[str, Any]] = None
):
    """Удобная функция для логирования ответа агента"""
    agent_logger.log_response(
        query_id=query_id,
        session_id=session_id,
        user_query=user_query,
        response_data=response_data,
        timing_info=timing_info,
        extra_metadata=extra_metadata
    )
