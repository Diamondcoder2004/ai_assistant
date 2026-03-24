"""
Timing utilities — утилиты для замера времени выполнения
"""
import time
import logging
import json
from pathlib import Path
from datetime import datetime
from functools import wraps
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field, asdict
from threading import Lock

logger = logging.getLogger(__name__)


# =============================================================================
# GLOBAL STATISTICS
# =============================================================================

@dataclass
class TimingStats:
    """Статистика по одному методу/операции."""
    name: str
    call_count: int = 0
    total_time_ms: float = 0.0
    min_time_ms: float = float('inf')
    max_time_ms: float = 0.0
    last_time_ms: float = 0.0
    
    @property
    def avg_time_ms(self) -> float:
        """Среднее время выполнения."""
        if self.call_count == 0:
            return 0.0
        return self.total_time_ms / self.call_count
    
    def update(self, elapsed_ms: float):
        """Обновление статистики."""
        self.call_count += 1
        self.total_time_ms += elapsed_ms
        self.min_time_ms = min(self.min_time_ms, elapsed_ms)
        self.max_time_ms = max(self.max_time_ms, elapsed_ms)
        self.last_time_ms = elapsed_ms
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в словарь."""
        return {
            "name": self.name,
            "call_count": self.call_count,
            "avg_time_ms": round(self.avg_time_ms, 2),
            "min_time_ms": round(self.min_time_ms, 2) if self.min_time_ms != float('inf') else 0,
            "max_time_ms": round(self.max_time_ms, 2),
            "last_time_ms": round(self.last_time_ms, 2),
            "total_time_ms": round(self.total_time_ms, 2)
        }


class TimingStatistics:
    """Глобальная статистика таймингов."""
    
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.stats: Dict[str, TimingStats] = {}
        self.requests: List[Dict[str, Any]] = []
        self._lock = Lock()
    
    def record(self, name: str, elapsed_ms: float):
        """Запись времени выполнения операции."""
        with self._lock:
            if name not in self.stats:
                self.stats[name] = TimingStats(name=name)
            self.stats[name].update(elapsed_ms)
    
    def record_request(self, method: str, path: str, elapsed_ms: float, 
                       agent_times: Optional[Dict[str, float]] = None):
        """Запись информации о HTTP запросе."""
        with self._lock:
            request_data = {
                "timestamp": datetime.now().isoformat(),
                "method": method,
                "path": path,
                "total_time_ms": round(elapsed_ms, 2),
                "agent_times": agent_times or {}
            }
            self.requests.append(request_data)
            # Храним только последние 1000 запросов
            if len(self.requests) > 1000:
                self.requests = self.requests[-1000:]
    
    def get_stats(self) -> Dict[str, Dict[str, Any]]:
        """Получение всей статистики."""
        with self._lock:
            return {
                name: stat.to_dict() 
                for name, stat in sorted(
                    self.stats.items(), 
                    key=lambda x: x[1].total_time_ms, 
                    reverse=True
                )
            }
    
    def get_request_stats(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Получение статистики по запросам."""
        with self._lock:
            return self.requests[-limit:]
    
    def save_to_file(self, filepath: str = "logs/timing_stats.json"):
        """Сохранение статистики в файл."""
        with self._lock:
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)
            data = {
                "generated_at": datetime.now().isoformat(),
                "operations": self.get_stats(),
                "recent_requests": self.get_request_stats(100)
            }
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"📊 Статистика таймингов сохранена в {filepath}")
    
    def reset(self):
        """Сброс статистики."""
        with self._lock:
            self.stats.clear()
            self.requests.clear()
            logger.info("📊 Статистика таймингов сброшена")
    
    def print_summary(self):
        """Вывод сводки в лог."""
        with self._lock:
            logger.info("=" * 60)
            logger.info("📊 СТАТИСТИКА ТАЙМИНГОВ")
            logger.info("=" * 60)
            
            if not self.stats:
                logger.info("Нет данных")
                return
            
            # Сортировка по общему времени
            sorted_stats = sorted(
                self.stats.values(),
                key=lambda x: x.total_time_ms,
                reverse=True
            )
            
            for stat in sorted_stats:
                logger.info(
                    f"{stat.name:40s} | "
                    f"calls: {stat.call_count:5d} | "
                    f"avg: {stat.avg_time_ms:8.2f}ms | "
                    f"min: {stat.min_time_ms:8.2f}ms | "
                    f"max: {stat.max_time_ms:8.2f}ms | "
                    f"total: {stat.total_time_ms:10.2f}ms"
                )
            
            logger.info("=" * 60)


# Глобальный экземпляр
timing_stats = TimingStatistics()


# =============================================================================
# DECORATOR
# =============================================================================

def timing(name: Optional[str] = None, log_level: str = "info"):
    """
    Декоратор для замера времени выполнения функции.
    
    Args:
        name: Имя операции для логирования (если None, используется имя функции)
        log_level: Уровень логирования ("debug", "info", "warning")
    
    Пример:
        @timing("QueryGenerator.generate")
        def generate(self, ...): ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            operation_name = name or func.__name__
            start = time.perf_counter()
            
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                elapsed_ms = (time.perf_counter() - start) * 1000
                timing_stats.record(operation_name, elapsed_ms)
                
                # Логирование
                log_func = getattr(logger, log_level, logger.info)
                log_func(f"⏱️ {operation_name}: {elapsed_ms:.2f}ms")
        
        return wrapper
    return decorator


# =============================================================================
# CONTEXT MANAGER
# =============================================================================

from contextlib import contextmanager

@contextmanager
def timing_context(operation_name: str, details: Optional[Dict[str, Any]] = None):
    """
    Контекстный менеджер для замера времени выполнения блока кода.
    
    Args:
        operation_name: Имя операции
        details: Дополнительные детали для логирования
    
    Пример:
        with timing_context("SearchAgent.search", {"queries": 3}):
            results = search_tool.search(...)
    """
    start = time.perf_counter()
    logger.info(f"🚀 Начало: {operation_name}")
    
    try:
        yield
        elapsed_ms = (time.perf_counter() - start) * 1000
        timing_stats.record(operation_name, elapsed_ms)
        
        extra = f" | {details}" if details else ""
        logger.info(f"✅ Завершено: {operation_name} за {elapsed_ms:.2f}ms{extra}")
    except Exception as e:
        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.error(f"❌ Ошибка: {operation_name} после {elapsed_ms:.2f}ms - {e}")
        raise


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_timing_stats() -> Dict[str, Dict[str, Any]]:
    """Получить текущую статистику таймингов."""
    return timing_stats.get_stats()


def print_timing_stats():
    """Вывести сводку таймингов в лог."""
    timing_stats.print_summary()


def save_timing_stats(filepath: str = "logs/timing_stats.json"):
    """Сохранить статистику таймингов в файл."""
    timing_stats.save_to_file(filepath)


def reset_timing_stats():
    """Сбросить статистику таймингов."""
    timing_stats.reset()


# =============================================================================
# PERIODIC SAVE
# =============================================================================

import threading

def start_periodic_save(interval_seconds: int = 300, filepath: str = "logs/timing_stats.json"):
    """
    Запуск периодического сохранения статистики.
    
    Args:
        interval_seconds: Интервал сохранения в секундах (по умолчанию 5 минут)
        filepath: Путь к файлу для сохранения
    """
    def periodic_save():
        while True:
            time.sleep(interval_seconds)
            try:
                save_timing_stats(filepath)
            except Exception as e:
                logger.error(f"Ошибка сохранения статистики: {e}")
    
    thread = threading.Thread(target=periodic_save, daemon=True)
    thread.start()
    logger.info(f"🕐 Запущено периодическое сохранение статистики (каждые {interval_seconds}с)")
