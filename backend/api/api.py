"""
RAG API для Башкирэнерго
Главный файл приложения FastAPI с интеграцией Agentic RAG
"""
import logging
import os
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .database import init_supabase
from .endpoints import router, get_rag_instance

# =============================================================================
# НАСТРОЙКА ЛОГИРОВАНИЯ
# =============================================================================

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(f'{LOG_DIR}/api_{datetime.now().strftime("%Y%m%d")}.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
error_logger = logging.getLogger(__name__ + ".errors")

# =============================================================================
# LIFESPAN
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    logger.info("=" * 60)
    logger.info("Приложение запускается...")
    logger.info(f"Время запуска: {datetime.now().isoformat()}")

    # Инициализация Supabase
    logger.info("Инициализация Supabase...")
    try:
        init_supabase()
        logger.info("Supabase инициализирован успешно")
    except Exception as e:
        error_logger.error(f"Ошибка инициализации Supabase: {e}", exc_info=True)
        raise

    # Инициализация Agentic RAG
    logger.info("Инициализация Agentic RAG...")
    try:
        rag = get_rag_instance()
        logger.info("Agentic RAG инициализирован успешно")
    except Exception as e:
        error_logger.error(f"Ошибка инициализации Agentic RAG: {e}", exc_info=True)
        raise

    yield

    logger.info("=" * 60)
    logger.info("Приложение завершает работу...")
    logger.info(f"Время остановки: {datetime.now().isoformat()}")


# =============================================================================
# INITIALIZATION
# =============================================================================

app = FastAPI(
    title="RAG API для Башкирэнерго (Agentic RAG)",
    description="""
## API для поиска и генерации ответов на основе документации

**Agentic RAG** — интеллектуальная система поиска с использованием LLM-агентов.

### Особенности:
- 🤖 **LLM подбирает параметры поиска** — веса, количество документов, стратегию
- 🔄 **Автоматическая генерация запросов** — перефразирование, гипонимы, синонимы
- 📚 **Работа с историей диалога** — контекстуальный поиск
- ⚡ **Потоковые ответы (SSE)** — реальное время генерации
- 📊 **Прозрачность** — возвращаем параметры которые LLM подобрал

### Параметры запроса:
Все параметры кроме `query` опциональны. LLM сам подберёт оптимальные значения,
но вы можете переопределить их при необходимости.
    """,
    version="2.0.0",
    lifespan=lifespan
)

logger.info(f"FastAPI приложение инициализировано: {app.title}")

# =============================================================================
# CORS MIDDLEWARE
# =============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)
logger.info("CORS middleware настроен")


# =============================================================================
# REQUEST LOGGING MIDDLEWARE
# =============================================================================

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware для логирования всех входящих запросов с таймингами"""
    import time
    import uuid
    from utils.timing import timing_stats
    
    start_time = time.time()
    request_id = str(uuid.uuid4())
    
    # Снимок статистики таймингов до запроса
    agent_times_before = {name: stat.last_time_ms for name, stat in timing_stats.stats.items()}

    logger.info(f"[{request_id}] {request.method} {request.url.path}")

    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Снимок статистики таймингов после запроса
        agent_times_after = {name: stat.last_time_ms for name, stat in timing_stats.stats.items()}
        
        # Вычисляем время работы агентов для этого запроса
        agent_times = {
            name: elapsed 
            for name, elapsed in agent_times_after.items() 
            if elapsed > agent_times_before.get(name, 0)
        }
        
        # Запись в глобальную статистику
        timing_stats.record_request(
            method=request.method,
            path=request.url.path,
            elapsed_ms=process_time * 1000,
            agent_times=agent_times
        )
        
        logger.info(
            f"[{request_id}] {request.method} {request.url.path} | "
            f"status: {response.status_code} | "
            f"time: {process_time * 1000:.2f}ms"
        )
        
        response.headers["X-Process-Time"] = str(process_time)
        response.headers["X-Request-ID"] = request_id
        return response
        
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(
            f"[{request_id}] {request.method} {request.url.path} | "
            f"time: {process_time * 1000:.2f}ms | "
            f"error: {e}",
            exc_info=True
        )
        raise


# =============================================================================
# ROUTER
# =============================================================================

app.include_router(router, prefix="")

logger.info("API endpoints зарегистрированы")


# =============================================================================
# GLOBAL EXCEPTION HANDLER
# =============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Глобальный обработчик исключений"""
    error_logger.critical(f"Необработанное исключение: {exc}", exc_info=True)
    error_logger.critical(f"Request: {request.method} {request.url}")

    return JSONResponse(
        status_code=500,
        content={"detail": "Внутренняя ошибка сервера", "type": type(exc).__name__}
    )


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    import uvicorn

    logger.info("Запуск сервера")
    uvicorn.run(app, host="0.0.0.0", port=8880)
