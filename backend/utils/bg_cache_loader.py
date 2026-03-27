"""
Фоновая загрузка BM25 кэша при старте приложения

Использование:
    from utils.bg_cache_loader import schedule_bm25_warmup
    
    # В main.py при старте приложения
    schedule_bm25_warmup()
"""
import logging
import threading
import time
from typing import Optional

logger = logging.getLogger(__name__)

# Глобальный флаг загрузки
_bm25_loading = False
_bm25_loaded = False
_loading_thread: Optional[threading.Thread] = None


def load_bm25_background():
    """
    Фоновая загрузка BM25 кэша.
    
    Запускается в отдельном потоке, не блокирует основной процесс.
    """
    global _bm25_loading, _bm25_loaded
    
    if _bm25_loading:
        logger.info("BM25 уже загружается в фоновом режиме")
        return
    
    _bm25_loading = True
    
    try:
        from tools.search_tool import SearchTool
        
        logger.info("🔄 Начата фоновая загрузка BM25 кэша...")
        start = time.time()
        
        # Создаём временный экземпляр для загрузки кэша
        tool = SearchTool()
        tool.load(force=True)
        
        elapsed = time.time() - start
        _bm25_loaded = True
        
        logger.info(f"✅ BM25 кэш загружен за {elapsed:.1f}с ({len(tool.documents)} документов)")
        
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки BM25 кэша: {e}")
        _bm25_loaded = False
    finally:
        _bm25_loading = False


def schedule_bm25_warmup(delay: float = 0.5):
    """
    Запланировать загрузку BM25 кэша с задержкой.
    
    Args:
        delay: Задержка перед загрузкой (секунды)
    """
    global _loading_thread
    
    def warmup_with_delay():
        time.sleep(delay)
        load_bm25_background()
    
    _loading_thread = threading.Thread(
        target=warmup_with_delay,
        name="BM25_Warmup",
        daemon=True  # Поток завершится при выходе из программы
    )
    _loading_thread.start()
    
    logger.info(f"📅 Загрузка BM25 кэша запланирована через {delay}с")


def is_bm25_loaded() -> bool:
    """Проверка, загружен ли BM25 кэш."""
    return _bm25_loaded


def is_bm25_loading() -> bool:
    """Проверка, загружается ли BM25 кэш."""
    return _bm25_loading


def get_bm25_status() -> dict:
    """Получить статус BM25 кэша."""
    return {
        "loaded": _bm25_loaded,
        "loading": _bm25_loading,
        "message": (
            "BM25 кэш готов" if _bm25_loaded
            else "BM25 кэш загружается..." if _bm25_loading
            else "BM25 кэш не загружен"
        )
    }
