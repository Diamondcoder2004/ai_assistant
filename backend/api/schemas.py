"""
Pydantic модели для запросов и ответов API
Согласно API_REQUIREMENTS.md
"""
from pydantic import BaseModel, Field, field_validator, RootModel
from typing import List, Optional, Dict, Any, Union
from enum import Enum


# =============================================================================
# QUERY MODELS
# =============================================================================

class QueryRequest(BaseModel):
    """
    Запрос на поиск и генерацию ответа.
    Согласно API_REQUIREMENTS.md v1
    """
    query: str = Field(..., min_length=1, max_length=5000, description="Текст запроса")
    k: Optional[int] = Field(default=10, ge=1, le=15, description="Количество документов")
    temperature: Optional[float] = Field(default=0.8, ge=0.0, le=1.5, description="Температура генерации")
    max_tokens: Optional[int] = Field(default=2000, ge=500, le=4000, description="Максимум токенов")
    min_score: Optional[float] = Field(default=0.0, ge=0.0, le=0.95, description="Минимальный порог схожести (0.0-0.95)")
    
    # session_id должен быть строкой (конвертируем из int если нужно)
    session_id: Optional[str] = Field(None, description="ID сессии для контекста")

    @field_validator('session_id', mode='before')
    @classmethod
    def convert_session_id(cls, v):
        if v is None:
            return None
        return str(v)

    class Config:
        json_schema_extra = {
            "example": {
                "query": "Как оформить заявку на подключение?",
                "k": 10,
                "temperature": 0.8,
                "max_tokens": 2000,
                "min_score": 0.0,
                "session_id": "47"
            }
        }


class SourceResponse(BaseModel):
    """Источник в ответе"""
    id: Union[str, int]
    filename: str
    breadcrumbs: str
    summary: str
    content: Optional[str] = ""
    category: Optional[str] = ""
    score_hybrid: float
    score_semantic: Optional[float] = 0.0
    score_lexical: Optional[float] = 0.0
    chunk_id: Optional[str] = None


class SearchParameters(BaseModel):
    """Параметры поиска в ответе"""
    k: int
    temperature: float
    max_tokens: int
    min_score: float


class QueryResponse(BaseModel):
    """Ответ на поисковый запрос"""
    query_id: str  # UUID
    session_id: str  # Обязательно строка
    answer: str
    sources: List[SourceResponse]
    parameters: SearchParameters


# =============================================================================
# STREAMING MODELS
# =============================================================================

class StreamToken(BaseModel):
    """Токен в потоковом ответе"""
    token: str


class StreamDone(BaseModel):
    """Завершение потока"""
    done: bool = True
    query_id: str
    session_id: str
    sources: List[SourceResponse]


# =============================================================================
# CHAT HISTORY MODELS
# =============================================================================

class HistorySource(BaseModel):
    """Источник в истории"""
    id: Union[str, int]
    filename: str
    breadcrumbs: str
    summary: str
    content: Optional[str] = ""
    category: Optional[str] = ""
    score_hybrid: float
    score_semantic: Optional[float] = 0.0
    score_lexical: Optional[float] = 0.0


class ChatHistoryItem(BaseModel):
    """Элемент истории чата"""
    id: Union[int, str]  # Может быть числом или строкой
    session_id: str  # Обязательно строка
    question: str
    answer: str
    parameters: Dict[str, Any]
    sources: List[HistorySource]
    created_at: str  # ISO 8601


# =============================================================================
# FEEDBACK MODELS
# =============================================================================

class FeedbackType(str, Enum):
    """Типы фидбека"""
    like = "like"
    dislike = "dislike"
    star = "star"


class FeedbackRequest(BaseModel):
    """Запрос на создание/обновление фидбека"""
    query_id: str  # UUID запроса
    feedback_type: FeedbackType
    rating: Optional[int] = Field(None, ge=1, le=5, description="Только для типа 'star'")
    comment: Optional[str] = Field(None, max_length=1000)

    class Config:
        json_schema_extra = {
            "example": {
                "query_id": "c653eca5-5015-47c1-80aa-0ddeff459d02",
                "feedback_type": "like",
                "rating": None,
                "comment": "Отличный ответ!"
            }
        }


class FeedbackResponse(BaseModel):
    """Ответ с фидбеком (одиночный)"""
    id: Union[int, str]
    query_id: str
    feedback_type: FeedbackType
    rating: Optional[int]
    comment: Optional[str]
    created_at: str
    updated_at: str


class FeedbackListResponse(RootModel[List[FeedbackResponse]]):
    """Список фидбеков для query_id"""
    root: List[FeedbackResponse]


# =============================================================================
# DELETE FEEDBACK RESPONSE
# =============================================================================

class DeleteFeedbackResponse(BaseModel):
    """Ответ на удаление фидбека"""
    deleted: bool = True
    count: int


# =============================================================================
# HEALTH CHECK
# =============================================================================

class HealthResponse(BaseModel):
    """Ответ health check"""
    status: str = "ok"
    timestamp: str
    version: str = "v1"
