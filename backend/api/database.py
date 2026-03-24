"""
База данных: Supabase клиент и функции для работы с БД
"""
import logging
import time
from supabase import create_client, Client
import config

logger = logging.getLogger(__name__)
db_logger = logging.getLogger(__name__ + ".database")

# =============================================================================
# ИНИЦИАЛИЗАЦИЯ SUPABASE КЛИЕНТА
# =============================================================================

SUPABASE_URL = config.SUPABASE_URL
SUPABASE_SERVICE_ROLE_KEY = config.SUPABASE_SERVICE_ROLE_KEY

supabase: Client = None


def init_supabase():
    """Инициализация Supabase клиента"""
    global supabase
    
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        raise ValueError("Missing required environment variables for Supabase")
    
    logger.info("Инициализация Supabase клиента...")
    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    logger.info("Supabase клиент инициализирован успешно")
    
    return supabase


def get_supabase() -> Client:
    """Получение Supabase клиента"""
    if supabase is None:
        init_supabase()
    return supabase


# =============================================================================
# CHAT FUNCTIONS
# =============================================================================

async def save_chat_to_supabase(
    user_id: str,
    session_id: str,
    question: str,
    answer: str,
    parameters: dict,
    sources: list,
    context: str = None
):
    """
    Сохраняет чат и источники в Supabase с полным логированием
    """
    db_logger.info(f"Начало сохранения чата для пользователя {user_id[:8]}...")
    start_time = time.time()

    try:
        chat_data = {
            "user_id": user_id,
            "session_id": session_id,
            "question": question,
            "answer": answer,
            "parameters": parameters,
            "context": context,
            "sources": sources
        }

        db_logger.debug(
            f"Данные чата: question_len={len(question)}, answer_len={len(answer)}, sources_count={len(sources)}")

        result = supabase.table("chats").insert(chat_data).execute()

        save_time = time.time() - start_time
        db_logger.info(
            f"Чат сохранён успешно за {save_time:.3f}s, ID: {result.data[0]['id'] if result.data else 'N/A'}")

        return result

    except Exception as e:
        save_time = time.time() - start_time
        db_logger.error(f"Ошибка сохранения в Supabase: {e}", exc_info=True)
        db_logger.error(f"Время попытки сохранения: {save_time:.3f}s")
        if hasattr(e, 'response'):
            db_logger.error(f"Ответ Supabase: {e.response.json() if e.response else 'No response'}")
        return None


async def get_chat_history(session_id: str, limit: int = 10):
    """Возвращает список сообщений диалога (вопрос-ответ)"""
    result = supabase.table("chats") \
        .select("question, answer, created_at") \
        .eq("session_id", session_id) \
        .order("created_at", desc=False) \
        .limit(limit) \
        .execute()

    history = []
    for row in result.data:
        history.append({"role": "user", "content": row["question"]})
        history.append({"role": "assistant", "content": row["answer"]})
    return history


async def get_user_chats(user_id: str, limit: int = 50):
    """Получение истории чатов пользователя"""
    result = supabase.table("chats") \
        .select("*") \
        .eq("user_id", user_id) \
        .order("created_at", desc=True) \
        .limit(limit) \
        .execute()
    
    return result.data


async def get_chat_by_id(chat_id: int, user_id: str):
    """Получение конкретного чата по ID"""
    result = supabase.table("chats") \
        .select("*") \
        .eq("id", chat_id) \
        .eq("user_id", user_id) \
        .execute()
    
    return result.data[0] if result.data else None


async def get_chat_by_session_id(session_id: str, user_id: str):
    """Получение чата по session_id"""
    result = supabase.table("chats") \
        .select("*") \
        .eq("session_id", session_id) \
        .eq("user_id", user_id) \
        .execute()
    
    return result.data[0] if result.data else None


# =============================================================================
# FEEDBACK FUNCTIONS
# =============================================================================

async def save_feedback(query_id: str, user_id: str, feedback_type: str, rating: int = None, comment: str = None):
    """Сохранение или обновление фидбека для конкретного запроса"""
    # Проверка существующего фидбека
    existing = supabase.table("feedback") \
        .select("*") \
        .eq("query_id", query_id) \
        .eq("user_id", user_id) \
        .execute()

    data = {
        "query_id": query_id,
        "user_id": user_id,
        "feedback_type": feedback_type,
        "rating": rating,
        "comment": comment
    }

    if existing.data:
        result = supabase.table("feedback") \
            .update(data) \
            .eq("id", existing.data[0]["id"]) \
            .execute()
    else:
        result = supabase.table("feedback").insert(data).execute()

    return result.data[0] if result.data else None


async def get_feedback_by_query_id(query_id: str, user_id: str):
    """Получение фидбека по query_id (возвращает массив всех фидбеков)"""
    result = supabase.table("feedback") \
        .select("*") \
        .eq("query_id", query_id) \
        .eq("user_id", user_id) \
        .execute()

    return result.data if result.data else []


async def delete_feedback_by_query_id(query_id: str, user_id: str, feedback_type: str = None):
    """
    Удаление фидбека по query_id.
    
    Args:
        query_id: UUID запроса
        user_id: ID пользователя
        feedback_type: Опционально - удалить только определённый тип
    """
    query = supabase.table("feedback").delete().eq("query_id", query_id).eq("user_id", user_id)
    
    if feedback_type:
        query = query.eq("feedback_type", feedback_type)
    
    result = query.execute()
    
    # Возвращаем количество удалённых записей
    return len(result.data) if result.data else 0


# =============================================================================
# DEPRECATED: старые функции для совместимости
# =============================================================================

async def get_feedback_by_session_id(session_id: str, user_id: str):
    """Устарело. Используйте get_feedback_by_query_id."""
    # Находим последний chat для сессии
    chat_result = supabase.table("chats") \
        .select("id") \
        .eq("session_id", session_id) \
        .eq("user_id", user_id) \
        .order("created_at", desc=True) \
        .limit(1) \
        .execute()

    if not chat_result.data:
        return None

    # Получаем query_id из parameters
    chat = supabase.table("chats") \
        .select("parameters") \
        .eq("id", chat_result.data[0]["id"]) \
        .execute()
    
    if not chat.data or not chat.data[0].get("parameters"):
        return None
    
    query_id = chat.data[0]["parameters"].get("query_id")
    if not query_id:
        return None

    return await get_feedback_by_query_id(query_id, user_id)


async def delete_feedback_by_session_id(session_id: str, user_id: str):
    """Устарело. Используйте delete_feedback_by_query_id."""
    # Находим последний chat для сессии
    chat_result = supabase.table("chats") \
        .select("parameters") \
        .eq("session_id", session_id) \
        .eq("user_id", user_id) \
        .order("created_at", desc=True) \
        .limit(1) \
        .execute()

    if not chat_result.data or not chat_result.data[0].get("parameters"):
        return False
    
    query_id = chat_result.data[0]["parameters"].get("query_id")
    if not query_id:
        return False

    return await delete_feedback_by_query_id(query_id, user_id)
