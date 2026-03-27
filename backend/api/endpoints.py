"""
Endpoints для RAG API с интеграцией Agentic RAG
Согласно API_REQUIREMENTS.md v1
"""
import logging
import time
import uuid
import json
import asyncio
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request, Query
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse

from .schemas import (
    QueryRequest, QueryResponse, SourceResponse, SearchParameters,
    ChatHistoryItem, HistorySource,
    FeedbackRequest, FeedbackResponse, FeedbackType, DeleteFeedbackResponse,
    HealthResponse
)
from .database import (
    save_chat_to_supabase, get_chat_history,
    get_user_chats, get_chat_by_id,
    save_feedback, get_feedback_by_query_id, delete_feedback_by_query_id
)
from main import AgenticRAG
import config
from .auth import get_current_user
from utils.timing import get_timing_stats, print_timing_stats, save_timing_stats, reset_timing_stats
from datetime import datetime, timedelta
import re
from utils.bg_cache_loader import get_bm25_status, is_bm25_loaded

logger = logging.getLogger(__name__)
retrieval_logger = logging.getLogger(__name__ + ".retrieval")
llm_logger = logging.getLogger(__name__ + ".llm")
db_logger = logging.getLogger(__name__ + ".database")
error_logger = logging.getLogger(__name__ + ".errors")

# =============================================================================
# ROUTER
# =============================================================================

router = APIRouter()

# Глобальный экземпляр AgenticRAG (инициализируется при старте)
rag_instance: Optional[AgenticRAG] = None


def get_rag_instance() -> AgenticRAG:
    """Получение экземпляра AgenticRAG"""
    global rag_instance
    if rag_instance is None:
        rag_instance = AgenticRAG()
    return rag_instance


# =============================================================================
# HEALTH CHECK
# =============================================================================

@router.get("/health", response_model=HealthResponse)
async def health():
    """Проверка здоровья сервиса (без аутентификации)"""
    logger.debug("Health check запрос")
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": "v1"
    }


@router.get("/bm25/status")
async def bm25_status():
    """Статус BM25 кэша (без аутентификации)"""
    return get_bm25_status()


@router.post("/bm25/warmup")
async def bm25_warmup():
    """Принудительная загрузка BM25 кэша"""
    from utils.bg_cache_loader import load_bm25_background
    
    # Запускаем в фоне
    load_bm25_background()
    
    return {
        "status": "loading",
        "message": "BM25 кэш загружается в фоновом режиме"
    }


# =============================================================================
# QUERY ENDPOINTS
# =============================================================================

@router.post("/query/stream")
async def stream_query(
    request: QueryRequest,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_current_user)
):
    """
    Потоковый endpoint с SSE.
    Agentic RAG сам подбирает параметры поиска.
    """
    query_id = str(uuid.uuid4())
    session_id = request.session_id or str(uuid.uuid4())
    rag = get_rag_instance()
    
    start_time = time.time()
    retrieval_logger.info(f"[{query_id}] Начат потоковый запрос от пользователя {user_id[:8]}")

    async def event_generator():
        nonlocal start_time

        try:
            # Этап 1: Поиск через Agentic RAG
            retrieval_logger.info(f"[{query_id}] 🔍 Agentic RAG поиск...")
            yield {"event": "message", "data": json.dumps({"token": "⏳ Анализ запроса..."})}

            result = rag.query(
                user_query=request.query,
                auto_retry=True
            )

            # Проверка на уточнение
            if result.get("clarification_needed"):
                yield {
                    "event": "message",
                    "data": json.dumps({
                        "token": "❓ Требуется уточнение: " + ", ".join(result.get("clarification_questions", []))
                    })
                }
                return

            # Этап 2: Формирование источников
            retrieval_logger.info(f"[{query_id}] 📋 Формирование источников...")
            sources_for_response = []
            sources_for_db = []

            for i, src in enumerate(result.get("sources", [])):
                source_item = {
                    "chunk_id": src.get("chunk_id"),
                    "id": i + 1,
                    "filename": src.get("filename", "Неизвестно"),
                    "breadcrumbs": src.get("breadcrumbs", ""),
                    "summary": src.get("summary", "")[:200],
                    "content": src.get("content", ""),
                    "category": src.get("category", ""),
                    "score_hybrid": src.get("score_hybrid", 0.0),
                    "score_semantic": src.get("score_semantic", 0.0),
                    "score_lexical": src.get("score_lexical", 0.0),
                }
                sources_for_response.append(SourceResponse(**source_item))
                sources_for_db.append(source_item)

            # Отправляем источники
            yield {
                "event": "message",
                "data": json.dumps({"sources": [s.dict() for s in sources_for_response]}, ensure_ascii=False)
            }

            # Этап 3: Генерация ответа по токену
            retrieval_logger.info(f"[{query_id}] ✍️ Генерация ответа...")
            answer = result.get("answer", "")
            
            # Отправляем ответ по словам (эмуляция стрима)
            for word in answer.split(" "):
                yield {"event": "message", "data": json.dumps({"token": word + " "})}
                await asyncio.sleep(0.02)

            total_time = time.time() - start_time
            retrieval_logger.info(f"[{query_id}] Завершено за {total_time:.3f}s")

            # Логирование ответа LLM
            retrieval_logger.info(f"[{query_id}] LLM ответ (длина: {len(answer)}): {answer[:500]}...")
            retrieval_logger.info(f"[{query_id}] Источники: {len(sources_for_response)} шт.")

            # Финальный чанк с метаданными
            yield {
                "event": "message",
                "data": json.dumps({
                    "done": True,
                    "query_id": query_id,
                    "session_id": session_id,
                    "sources": [s.dict() for s in sources_for_response]
                }, ensure_ascii=False)
            }

            # Сохранение в БД
            background_tasks.add_task(
                save_chat_to_supabase,
                user_id,
                session_id,
                request.query,
                answer,
                {
                    "k": request.k or 10,
                    "temperature": request.temperature or 0.8,
                    "max_tokens": request.max_tokens or 2000,
                    "min_score": request.min_score or 0.0,
                    "query_id": query_id
                },
                sources_for_db,
                ""
            )

        except Exception as e:
            error_logger.error(f"[{query_id}] Критическая ошибка: {e}", exc_info=True)
            yield {"event": "message", "data": json.dumps({"error": str(e)})}

    return EventSourceResponse(event_generator())


@router.post("/query", response_model=QueryResponse)
async def query(
    request: QueryRequest,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_current_user)
):
    """
    Непотоковый endpoint.
    Agentic RAG сам подбирает параметры поиска.
    """
    query_id = str(uuid.uuid4())
    session_id = request.session_id or str(uuid.uuid4())
    rag = get_rag_instance()
    start_time = time.time()

    retrieval_logger.info(f"[{query_id}] Начат запрос от пользователя {user_id[:8]}")
    retrieval_logger.info(f"[{query_id}] Session ID: {session_id}")

    try:
        # Получаем историю диалога из БД если session_id существует
        history = []
        if request.session_id:
            history = await get_chat_history(session_id, limit=10)
            retrieval_logger.info(f"[{query_id}] Загружено {len(history)//2} сообщений истории")

        # Формируем рекомендации от пользователя для LLM
        user_hints = {}
        if request.k:
            user_hints["k"] = request.k
        if request.temperature:
            user_hints["temperature"] = request.temperature
        if request.max_tokens:
            user_hints["max_tokens"] = request.max_tokens
        
        if user_hints:
            retrieval_logger.info(f"[{query_id}] Рекомендации от пользователя: {user_hints}")

        # Выполняем запрос через Agentic RAG с историей и рекомендациями
        result = rag.query(
            user_query=request.query,
            auto_retry=True,
            history=history,  # Передаём историю из БД
            user_hints=user_hints if user_hints else None  # Передаём рекомендации
        )

        # Формирование источников
        sources_for_response = []
        sources_for_db = []

        for i, src in enumerate(result.get("sources", [])):
            source_item = {
                "chunk_id": src.get("chunk_id"),
                "id": i + 1,
                "filename": src.get("filename", "Неизвестно"),
                "breadcrumbs": src.get("breadcrumbs", ""),
                "summary": src.get("summary", "")[:200],
                "content": src.get("content", ""),
                "category": src.get("category", ""),
                "score_hybrid": src.get("score_hybrid", 0.0),
                "score_semantic": src.get("score_semantic", 0.0),
                "score_lexical": src.get("score_lexical", 0.0),
            }
            sources_for_response.append(SourceResponse(**source_item))
            sources_for_db.append(source_item)

        # Параметры поиска
        parameters = SearchParameters(
            k=request.k or 10,
            temperature=request.temperature or 0.8,
            max_tokens=request.max_tokens or 2000,
            min_score=request.min_score or 0.0
        )

        # Сохранение в БД
        db_logger.info(f"[{query_id}] Начало сохранения в БД: user_id={user_id[:8]}, session_id={session_id}")
        background_tasks.add_task(
            save_chat_to_supabase,
            user_id,
            session_id,
            request.query,
            result.get("answer", ""),
            {
                "k": parameters.k,
                "temperature": parameters.temperature,
                "max_tokens": parameters.max_tokens,
                "min_score": parameters.min_score,
                "query_id": query_id
            },
            sources_for_db,
            ""
        )
        db_logger.info(f"[{query_id}] Задача сохранения добавлена в background_tasks")

        total_time = time.time() - start_time
        retrieval_logger.info(f"[{query_id}] Завершено за {total_time:.3f}s")

        # Логирование ответа LLM
        answer = result.get("answer", "")
        retrieval_logger.info(f"[{query_id}] LLM ответ (длина: {len(answer)}): {answer[:500]}...")
        retrieval_logger.info(f"[{query_id}] Источники: {len(sources_for_response)} шт.")
        if result.get("queries_used"):
            retrieval_logger.info(f"[{query_id}] Запросы: {result.get('queries_used')}")

        return QueryResponse(
            query_id=query_id,
            session_id=session_id,
            answer=answer,
            sources=sources_for_response,
            parameters=parameters
        )

    except Exception as e:
        error_logger.error(f"[{query_id}] Ошибка: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка: {str(e)}")


# =============================================================================
# HISTORY ENDPOINTS
# =============================================================================

@router.get("/history", response_model=List[ChatHistoryItem])
async def get_history(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user_id: str = Depends(get_current_user)
):
    """Получение истории чатов пользователя с пагинацией"""
    db_logger.info(f"Запрос истории для пользователя {user_id[:8]}, limit={limit}, offset={offset}")

    try:
        chats_result = await get_user_chats(user_id, limit, offset)
        db_logger.info(f"Получено чатов: {len(chats_result)}")

        history = []
        for chat in chats_result:
            sources_list = []
            for src in chat.get("sources", []):
                sources_list.append(HistorySource(
                    id=src.get("id", src.get("chunk_id", "unknown")),
                    filename=src["filename"],
                    breadcrumbs=src["breadcrumbs"],
                    summary=src["summary"],
                    content=src.get("content", ""),
                    category=src.get("category", ""),
                    score_hybrid=src.get("score_hybrid", 0.0),
                    score_semantic=src.get("score_semantic", 0.0),
                    score_lexical=src.get("score_lexical", 0.0),
                ))

            history.append(ChatHistoryItem(
                id=chat["id"],
                session_id=str(chat.get("session_id", "")),
                question=chat["question"],
                answer=chat["answer"],
                parameters=chat.get("parameters", {}),
                sources=sources_list,
                created_at=chat["created_at"]
            ))

        return history

    except Exception as e:
        db_logger.error(f"Ошибка получения истории: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching history: {e}")


@router.get("/history/sessions")
async def get_history_sessions(
    search: Optional[str] = Query(None, description="Поиск по вопросам и ответам"),
    start_date: Optional[str] = Query(None, description="Начальная дата (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Конечная дата (YYYY-MM-DD)"),
    user_id: str = Depends(get_current_user)
):
    """
    Получение истории чатов с группировкой по сессиям и дням.

    - search: поиск по тексту вопросов и ответов
    - start_date: фильтр по начальной дате
    - end_date: фильтр по конечной дате
    """
    db_logger.info(f"Запрос сгруппированной истории для пользователя {str(user_id)[:8]}")
    db_logger.info(f"Параметры: search={search}, start_date={start_date}, end_date={end_date}")

    try:
        # Получаем все чаты пользователя
        all_chats = await get_user_chats(user_id, limit=1000, offset=0)
        db_logger.info(f"Получено чатов: {len(all_chats)}")

        # Фильтрация по дате
        if start_date:
            try:
                start = datetime.strptime(start_date, "%Y-%m-%d")
                all_chats = [c for c in all_chats if datetime.strptime(c["created_at"][:10], "%Y-%m-%d") >= start]
            except ValueError:
                pass

        if end_date:
            try:
                end = datetime.strptime(end_date, "%Y-%m-%d")
                all_chats = [c for c in all_chats if datetime.strptime(c["created_at"][:10], "%Y-%m-%d") <= end]
            except ValueError:
                pass

        # Поиск по тексту
        if search:
            search_lower = search.lower()
            all_chats = [
                c for c in all_chats
                if search_lower in c.get("question", "").lower() or search_lower in c.get("answer", "").lower()
            ]
        
        db_logger.info(f"Чатов после фильтрации: {len(all_chats)}")
        
        # Группировка по сессиям
        sessions_map = {}
        for chat in all_chats:
            session_id = str(chat.get("session_id", chat.get("id", "unknown")))
            if session_id not in sessions_map:
                sessions_map[session_id] = {
                    "session_id": session_id,
                    "messages": [],
                    "created_at": chat["created_at"],
                    "updated_at": chat["created_at"],
                    "first_question": chat["question"]
                }
            
            sessions_map[session_id]["messages"].append({
                "id": chat["id"],
                "question": chat["question"],
                "answer": chat["answer"],
                "created_at": chat["created_at"],
                "sources": chat.get("sources", [])
            })
            
            # Обновляем дату обновления сессии
            if chat["created_at"] > sessions_map[session_id]["updated_at"]:
                sessions_map[session_id]["updated_at"] = chat["created_at"]
        
        # Группировка сессий по дням
        grouped = {
            "today": [],
            "yesterday": [],
            "earlier": []
        }
        
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)

        db_logger.info(f"Группировка сессий: today={today}, yesterday={yesterday}")
        db_logger.info(f"Всего сессий для группировки: {len(sessions_map)}")

        for session_id, session in sessions_map.items():
            session_date = datetime.strptime(session["updated_at"][:10], "%Y-%m-%d").date()
            
            db_logger.info(f"Сессия {session_id[:8]}: updated_at={session['updated_at']}, date={session_date}")
            
            # Формируем превью сообщений
            messages_preview = []
            messages = session["messages"]
            
            if len(messages) > 0:
                # Первый вопрос
                messages_preview.append({
                    "type": "question",
                    "text": messages[0]["question"][:150] if len(messages[0]["question"]) > 150 else messages[0]["question"]
                })
                
                # Первый ответ (если есть)
                if len(messages) > 1:
                    messages_preview.append({
                        "type": "answer",
                        "text": messages[0]["answer"][:200] if len(messages[0]["answer"]) > 200 else messages[0]["answer"]
                    })
                
                # Последнее сообщение (если это не первое сообщение)
                if len(messages) > 2:
                    last_msg = messages[-1]
                    preview_text = last_msg["question"] if last_msg["id"] % 2 == 1 else last_msg["answer"]
                    messages_preview.append({
                        "type": "last",
                        "text": preview_text[:150] if len(preview_text) > 150 else preview_text
                    })
            
            session_data = {
                "session_id": session_id,
                "messages_count": len(session["messages"]),
                "first_question": session["first_question"],
                "updated_at": session["updated_at"],
                "preview": messages_preview
            }
            
            if session_date == today:
                grouped["today"].append(session_data)
            elif session_date == yesterday:
                grouped["yesterday"].append(session_data)
            else:
                grouped["earlier"].append(session_data)
        
        # Сортировка сессий внутри групп по дате (новые первые)
        for key in grouped:
            grouped[key].sort(key=lambda x: x["updated_at"], reverse=True)
        
        return grouped

    except Exception as e:
        db_logger.error(f"Ошибка получения сгруппированной истории: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching grouped history: {e}")


@router.get("/history/{chat_id}", response_model=ChatHistoryItem)
async def get_chat(
    chat_id: int,
    user_id: str = Depends(get_current_user)
):
    """Получение деталей конкретного чата"""
    db_logger.info(f"Запрос чата {chat_id} для пользователя {user_id[:8]}")

    try:
        chat = await get_chat_by_id(chat_id, user_id)

        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")

        sources_list = []
        for src in chat.get("sources", []):
            sources_list.append(HistorySource(
                id=src.get("id", src.get("chunk_id", "unknown")),
                filename=src["filename"],
                breadcrumbs=src["breadcrumbs"],
                summary=src["summary"],
                content=src.get("content", ""),
                category=src.get("category", ""),
                score_hybrid=src.get("score_hybrid", 0.0),
                score_semantic=src.get("score_semantic", 0.0),
                score_lexical=src.get("score_lexical", 0.0),
            ))

        return ChatHistoryItem(
            id=chat["id"],
            session_id=str(chat.get("session_id", "")),
            question=chat["question"],
            answer=chat["answer"],
            parameters=chat.get("parameters", {}),
            sources=sources_list,
            created_at=chat["created_at"]
        )

    except HTTPException:
        raise
    except Exception as e:
        db_logger.error(f"Ошибка в get_chat/{chat_id}: {e}", exc_info=True)
        raise HTTPException(status_code=404, detail="Chat not found")


# =============================================================================
# FEEDBACK ENDPOINTS
# =============================================================================

@router.post("/feedback", response_model=FeedbackResponse)
async def create_or_update_feedback(
    feedback: FeedbackRequest,
    user_id: str = Depends(get_current_user)
):
    """Создание или обновление фидбека"""
    db_logger.info(f"Фидбек для запроса {feedback.query_id} от пользователя {user_id[:8]}")

    try:
        result = await save_feedback(
            query_id=feedback.query_id,
            user_id=user_id,
            feedback_type=feedback.feedback_type.value,
            rating=feedback.rating,
            comment=feedback.comment
        )

        if not result:
            raise HTTPException(status_code=500, detail="Failed to save feedback")

        return {
            "id": result["id"],
            "query_id": feedback.query_id,
            "feedback_type": feedback.feedback_type.value,
            "rating": feedback.rating,
            "comment": feedback.comment,
            "created_at": result.get("created_at"),
            "updated_at": result.get("updated_at")
        }

    except HTTPException:
        raise
    except Exception as e:
        db_logger.error(f"Ошибка сохранения фидбека: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error saving feedback: {e}")


@router.get("/feedback/{query_id}", response_model=List[FeedbackResponse])
async def get_feedback(
    query_id: str,
    user_id: str = Depends(get_current_user)
):
    """Получение фидбека для запроса (возвращает массив)"""
    try:
        result = await get_feedback_by_query_id(query_id, user_id)

        if result:
            return [{
                "id": r["id"],
                "query_id": r["query_id"],
                "feedback_type": r["feedback_type"],
                "rating": r["rating"],
                "comment": r["comment"],
                "created_at": r["created_at"],
                "updated_at": r.get("updated_at")
            } for r in result]

        return []

    except Exception as e:
        db_logger.error(f"Ошибка получения фидбека: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching feedback: {e}")


@router.delete("/feedback/{query_id}", response_model=DeleteFeedbackResponse)
async def delete_feedback(
    query_id: str,
    feedback_type: Optional[str] = Query(None, description="Удалить только определённый тип"),
    user_id: str = Depends(get_current_user)
):
    """Удаление фидбека"""
    db_logger.info(f"Удаление фидбека для запроса {query_id}, type={feedback_type}")

    try:
        count = await delete_feedback_by_query_id(query_id, user_id, feedback_type)

        return DeleteFeedbackResponse(
            deleted=True,
            count=count
        )

    except Exception as e:
        db_logger.error(f"Ошибка удаления фидбека: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error deleting feedback: {e}")


# =============================================================================
# TIMING STATISTICS ENDPOINTS
# =============================================================================

@router.get("/timing/stats")
async def get_timing_statistics():
    """Получение статистики таймингов по агентам и операциям"""
    return get_timing_stats()


@router.get("/timing/stats/print")
async def print_timing_statistics():
    """Вывод сводки таймингов в лог"""
    print_timing_stats()
    return {"status": "ok", "message": "Statistics printed to log"}


@router.post("/timing/stats/save")
async def save_timing_statistics(filepath: Optional[str] = "logs/timing_stats.json"):
    """Сохранение статистики таймингов в файл"""
    save_timing_stats(filepath)
    return {"status": "ok", "filepath": filepath}


@router.post("/timing/stats/reset")
async def reset_timing_statistics():
    """Сброс статистики таймингов"""
    reset_timing_stats()
    return {"status": "ok", "message": "Statistics reset"}
