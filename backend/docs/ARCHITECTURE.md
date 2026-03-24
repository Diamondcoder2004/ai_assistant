# Архитектура Agentic RAG

## Обзор системы

Agentic RAG — это многоагентная система поиска и генерации ответов на основе базы знаний.

### Ключевые компоненты

```
┌─────────────────────────────────────────────────────────────┐
│                     Клиент (Vue 3)                          │
│  - Отображение сообщений                                    │
│  - Ввод вопросов                                            │
│  - Отображение источников                                   │
└─────────────────────────────────────────────────────────────┘
                            ↓ HTTPS
┌─────────────────────────────────────────────────────────────┐
│                  API Gateway (FastAPI)                      │
│  - Аутентификация (JWT)                                     │
│  - Валидация запросов                                       │
│  - Логирование                                              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  Agentic RAG Core                           │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Query Generator Agent                                │  │
│  │  - Анализ вопроса                                     │  │
│  │  - Генерация 2-3 поисковых запросов                   │  │
│  │  - Подбор параметров поиска (веса, k, strategy)       │  │
│  └───────────────────────────────────────────────────────┘  │
│                            ↓                                │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Search Agent                                         │  │
│  │  - Выполнение поиска через Search Tool                │  │
│  │  - Оценка результатов                                 │  │
│  │  - Авто-повтор при плохих результатах                 │  │
│  └───────────────────────────────────────────────────────┘  │
│                            ↓                                │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Response Agent                                       │  │
│  │  - Генерация ответа на основе найденного              │  │
│  │  - Цитирование источников                             │  │
│  │  - Проверка на необходимость уточнения                │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  Search Tool (Hybrid Retrieval)             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Semantic Search (Qdrant)                             │  │
│  │  - pref: эмбеддинг summary + content                  │  │
│  │  - hype: эмбеддинг hypothetical questions             │  │
│  │  - contextual: эмбеддинг соседних чанков              │  │
│  └───────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Lexical Search (BM25)                                │  │
│  │  - Токенизация текста                                 │  │
│  │  - Подсчёт TF-IDF                                     │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## Поток данных

### 1. Пользователь задаёт вопрос

```
POST /query
{
  "query": "Как подать заявку на ТП?",
  "session_id": "uuid-123"
}
```

### 2. API обрабатывает запрос

```python
# api/endpoints.py
@router.post("/query")
async def query(request: QueryRequest):
    # 1. Извлекаем историю из БД
    history = await get_chat_history(request.session_id)
    
    # 2. Формируем рекомендации от пользователя
    user_hints = {
        "k": request.k,
        "temperature": request.temperature,
        "max_tokens": request.max_tokens
    }
    
    # 3. Вызываем Agentic RAG
    result = rag.query(
        user_query=request.query,
        history=history,
        user_hints=user_hints
    )
    
    # 4. Возвращаем ответ
    return result
```

### 3. Agentic RAG обрабатывает вопрос

```python
# main.py
def query(self, user_query, history, user_hints):
    # 1. Search Agent ищет информацию
    search_result = self.search_agent.search(
        user_query=user_query,
        history=history,
        user_hints=user_hints
    )
    
    # 2. Response Agent генерирует ответ
    response_result = self.response_agent.generate_response(
        user_query=user_query,
        search_results=search_result["results"]
    )
    
    # 3. Возвращаем результат
    return {
        "answer": response_result["answer"],
        "sources": response_result["sources"],
        "search_params": search_result["search_params"]
    }
```

### 4. Query Generator генерирует запросы

```python
# agents/query_generator.py
def generate(self, user_query, history, user_hints):
    # Формируем промпт с учётом рекомендаций
    prompt = get_query_generation_prompt(
        user_query=user_query,
        history=history,
        user_hints=user_hints  # Рекомендации как подсказки
    )
    
    # LLM генерирует JSON с запросами и параметрами
    response = self.client.chat.completions.create(
        model=self.model,
        messages=[...],
        response_format={"type": "json_object"}
    )
    
    # Парсим результат
    return QueryGenerationResult(
        queries=["запрос 1", "запрос 2"],
        search_params={
            "k": 12,
            "pref_weight": 0.4,
            "hype_weight": 0.2,
            "lexical_weight": 0.3,
            "contextual_weight": 0.1,
            "strategy": "concat"
        },
        confidence=0.85
    )
```

### 5. Search Agent выполняет поиск

```python
# agents/search_agent.py
def search(self, user_query, user_hints):
    # 1. Генерируем запросы через Query Generator
    gen_result = self.query_generator.generate(
        user_query=user_query,
        user_hints=user_hints  # LLM учитывает но решает сам
    )
    
    # 2. Выполняем поиск через Search Tool
    results = self.search_tool.search_multiple(
        queries=gen_result.queries,
        k_per_query=gen_result.search_params["k"],
        strategy=gen_result.search_params["strategy"]
    )
    
    # 3. Возвращаем результаты
    return {
        "results": results,
        "queries_used": gen_result.queries,
        "search_params": gen_result.search_params,
        "confidence": gen_result.confidence
    }
```

### 6. Search Tool выполняет гибридный поиск

```python
# tools/search_tool.py
def search(self, request):
    # 1. Векторный поиск по 4 компонентам
    pref_hits = self.client.query_points(
        query=query_vector,
        using="pref",
        limit=request.k * 3
    )
    
    hype_hits = self.client.query_points(
        query=query_vector,
        using="hype",
        limit=request.k * 3
    )
    
    contextual_hits = self.client.query_points(
        query=query_vector,
        using="contextual",
        limit=request.k * 3
    )
    
    # 2. BM25 поиск
    bm25_scores = self._get_bm25_scores(request.query)
    
    # 3. Гибридная оценка
    for pid in all_ids:
        combined_scores[pid] = (
            request.pref_weight * pref_scores.get(pid, 0.0) +
            request.hype_weight * hype_scores.get(pid, 0.0) +
            request.contextual_weight * contextual_scores.get(pid, 0.0) +
            request.lexical_weight * bm25_scores.get(pid, 0.0)
        )
    
    # 4. Возвращаем топ-k результатов
    return sorted_results[:request.k]
```

### 7. Response Agent генерирует ответ

```python
# agents/response_agent.py
def generate_response(self, user_query, search_results, history):
    # 1. Формируем контекст из результатов
    context = self._format_context(search_results)
    
    # 2. Формируем историю диалога
    history_context = self._format_history(history)
    
    # 3. Создаём промпт
    prompt = f"""
{history_context}
{context}

Вопрос: {user_query}

Дай развёрнутый ответ с цитированием источников.
"""
    
    # 4. Генерируем ответ через LLM
    response = self.client.chat.completions.create(
        model=self.model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
    )
    
    # 5. Извлекаем источники
    sources = self._extract_sources(search_results)
    
    return {
        "answer": response.choices[0].message.content,
        "sources": sources,
        "confidence": 0.9
    }
```

---

## Структуры данных

### QueryRequest (вход)

```python
{
    "query": str,              # Вопрос пользователя
    "k": Optional[int],        # Рекомендация по количеству документов
    "temperature": Optional[float],  # Рекомендация по температуре
    "max_tokens": Optional[int],     # Рекомендация по токенам
    "session_id": Optional[str]      # ID сессии для контекста
}
```

### QueryResponse (выход)

```python
{
    "query_id": str,           # UUID запроса
    "session_id": str,         # ID сессии
    "answer": str,             # Текст ответа
    "sources": List[Source],   # Источники
    "search_params": {         # Параметры которые LLM подобрал
        "k": int,
        "pref_weight": float,
        "hype_weight": float,
        "lexical_weight": float,
        "contextual_weight": float,
        "strategy": str,
        "queries": List[str]
    },
    "confidence": float,       # Уверенность 0-1
    "clarification_needed": bool,
    "clarification_questions": List[str]
}
```

### SearchResult

```python
{
    "id": str,                 # ID чанка в Qdrant
    "content": str,            # Текст чанка
    "summary": str,            # Краткое содержание
    "category": str,           # Категория документа
    "filename": str,           # Название файла
    "breadcrumbs": str,        # Путь к разделу
    "score_hybrid": float,     # Общая оценка
    "score_semantic": float,   # Смысловая релевантность
    "score_lexical": float,    # Лексическая релевантность
    "chunk_id": Optional[int]  # ID чанка
}
```

---

## База данных

### Chats (Supabase)

```sql
CREATE TABLE chats (
    id BIGSERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    parameters JSONB,
    sources JSONB,
    context TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Индексы
CREATE INDEX idx_chats_user_id ON chats(user_id);
CREATE INDEX idx_chats_session_id ON chats(session_id);
CREATE INDEX idx_chats_created_at ON chats(created_at DESC);
```

### Feedback (Supabase)

```sql
CREATE TABLE feedback (
    id BIGSERIAL PRIMARY KEY,
    query_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    feedback_type TEXT NOT NULL,  -- 'like', 'dislike', 'star'
    rating INTEGER,
    comment TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Индексы
CREATE INDEX idx_feedback_query_id ON feedback(query_id);
CREATE INDEX idx_feedback_user_id ON feedback(user_id);
```

---

## Конфигурация

### Переменные окружения (.env)

```bash
# RouterAI API
ROUTERAI_API_KEY=sk-...
ROUTERAI_BASE_URL=https://routerai.ru/api/v1

# Qdrant
QDRANT_HOST=localhost
QDRANT_PORT=6333
COLLECTION_NAME=BASHKIR_ENERGO_PERPLEXITY

# Embedding
EMBEDDING_MODEL=perplexity/pplx-embed-v1-4b
EMBEDDING_DIM=2560

# LLM
DEFAULT_LLM_MODEL=qwen/qwen3.5-flash-02-23

# Supabase
SUPABASE_URL=http://localhost:8000
SUPABASE_KEY=anon-key
SUPABASE_SERVICE_ROLE_KEY=service-role-key
SUPABASE_JWT_SECRET=jwt-secret

# Hybrid Search Weights (default)
RETRIEVE_PREF_WEIGHT=0.4
RETRIEVE_HYPE_WEIGHT=0.3
RETRIEVE_LEXICAL_WEIGHT=0.2
RETRIEVE_CONTEXTUAL_WEIGHT=0.1
```

---

## Логирование

### Уровни логирования

```python
import logging

logger = logging.getLogger(__name__)

logger.debug("Детальная отладка")      # DEBUG
logger.info("Обычная информация")       # INFO
logger.warning("Предупреждение")        # WARNING
logger.error("Ошибка")                  # ERROR
logger.critical("Критическая ошибка")   # CRITICAL
```

### Формат логов

```
2026-03-23 21:40:09 | INFO | api.endpoints | [query_id] Начат запрос
2026-03-23 21:40:10 | INFO | agents.search | Поиск: 'вопрос...' k=10
2026-03-23 21:40:11 | INFO | agents.response | Генерация ответа...
2026-03-23 21:40:12 | INFO | api.endpoints | [query_id] Завершено за 3.2s
```

---

## Безопасность

### JWT Аутентификация

```python
# api/auth.py
async def get_current_user(credentials: HTTPAuthorizationCredentials):
    token = credentials.credentials
    
    # Декодируем токен
    payload = jwt.decode(
        token,
        SUPABASE_JWT_SECRET,
        algorithms=["HS256"],
        options={"verify_aud": False}
    )
    
    # Извлекаем user_id
    user_id = payload.get("sub")
    
    # Если service_role токен
    if not user_id:
        role = payload.get("role")
        if role == "service_role":
            user_id = "service_user"
    
    return user_id
```

### Валидация запросов

```python
# api/schemas.py
class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=5000)
    k: Optional[int] = Field(None, ge=1, le=100)
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, ge=100, le=8000)
    session_id: Optional[str]
    
    @field_validator('session_id', mode='before')
    @classmethod
    def convert_session_id(cls, v):
        if v is None:
            return None
        return str(v)  # Конвертируем в строку
```

---

## Тестирование

### Unit тесты

```python
# tests/test_query_generator.py
def test_query_generation():
    agent = QueryGeneratorAgent()
    
    result = agent.generate(
        user_query="Как подать заявку на ТП?",
        history="",
        category="ФЛ"
    )
    
    assert result.clarification_needed == False
    assert len(result.queries) >= 2
    assert result.confidence > 0.5
```

### Integration тесты

```python
# tests/test_api.py
def test_query_endpoint():
    response = client.post(
        "/query",
        json={"query": "Как подать заявку?"},
        headers={"Authorization": "Bearer token"}
    )
    
    assert response.status_code == 200
    assert "answer" in response.json()
    assert "sources" in response.json()
```

---

## Развёртывание

### Docker Compose (локально)

```yaml
version: '3.8'

services:
  qdrant:
    image: qdrant/qdrant
    ports:
      - "6333:6333"
    volumes:
      - ./qdrant_storage:/qdrant/storage

  supabase:
    image: supabase/postgres
    ports:
      - "54322:5432"
    environment:
      - POSTGRES_PASSWORD=postgres

  api:
    build: .
    ports:
      - "8880:8880"
    environment:
      - QDRANT_HOST=qdrant
      - SUPABASE_URL=http://supabase:5432
    depends_on:
      - qdrant
      - supabase
```

### Production

```bash
# Бэкенд
uvicorn api.api:app --host 0.0.0.0 --port 8880 --workers 4

# Фронтенд
npm run build
npm run preview
```

---

## Мониторинг

### Метрики

- **Время ответа:** среднее, p95, p99
- **Количество запросов:** в секунду, в минуту
- **Уверенность системы:** средняя по ответам
- **Оценки пользователей:** like/dislike ratio

### Алёрты

- Ошибки > 5% за 5 минут
- Время ответа > 10 секунд
- Недоступность Qdrant/Supabase

---

**Версия документа:** 1.0  
**Дата обновления:** 2026-03-23
