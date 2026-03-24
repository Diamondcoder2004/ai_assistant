# API Требования для BashkirEnergo Chat Bot

## Версия API: v1

## Базовый URL
```
http://localhost:8880
```

## Аутентификация

Все запросы (кроме `/health`) требуют JWT-токен в заголовке:
```
Authorization: Bearer <access_token>
```

Токен получается из Supabase Auth session.

---

## Endpoints

### 1. POST /query

**Описание:** Отправка вопроса и получение ответа (без streaming)

#### Request Body
```json
{
  "query": "string (обязательно)",
  "k": "integer (опционально, default: 10, min: 1, max: 15)",
  "temperature": "number (опционально, default: 0.8, min: 0, max: 1.5)",
  "max_tokens": "integer (опционально, default: 2000, min: 500, max: 4000)",
  "min_score": "number (опционально, default: 0.0, min: 0, max: 1)",
  "session_id": "string (опционально) — ID сессии для контекста"
}
```

**Важно:** 
- `session_id` должен принимать **строку** (string), а не число
- Если `session_id` не передан — начать новую сессию

#### Response 200 OK
```json
{
  "query_id": "uuid (обязательно) — уникальный ID запроса для фидбека",
  "session_id": "string (обязательно) — ID текущей сессии",
  "answer": "string (обязательно) — текст ответа (поддерживает Markdown и HTML)",
  "sources": [
    {
      "id": "string или integer",
      "filename": "string",
      "breadcrumbs": "string (путь к документу)",
      "summary": "string (краткое содержание)",
      "content": "string (полное содержание, опционально)",
      "category": "string (опционально)",
      "score_hybrid": "number (0-1)",
      "score_semantic": "number (0-1, опционально)",
      "score_lexical": "number (0-1, опционально)",
      "chunk_id": "string (опционально)"
    }
  ],
  "parameters": {
    "k": "integer",
    "temperature": "number",
    "max_tokens": "integer",
    "min_score": "number"
  }
}
```

#### Response 400 Bad Request
```json
{
  "detail": "string (ошибка валидации)"
}
```

#### Response 401 Unauthorized
```json
{
  "detail": "Not authenticated"
}
```

#### Response 500 Internal Server Error
```json
{
  "detail": "string (ошибка сервера)"
}
```

---

### 2. POST /query/stream

**Описание:** Отправка вопроса с streaming ответа (Server-Sent Events)

#### Request Body
Аналогично `/query`

#### Response 200 OK (SSE Stream)
```
data: {"token": "часть_ответа"}

data: {"token": "ещё_часть"}

data: {"done": true, "query_id": "uuid", "session_id": "string", "sources": [...]}
```

**Формат:**
- Каждый чанк отправляется как `data: {JSON}`
- Последний чанк содержит `done: true` + метаданные

#### Response 400/401/500
Аналогично `/query`

---

### 3. GET /history

**Описание:** Получение истории чатов пользователя

#### Query Parameters
```
limit: integer (опционально, default: 50, min: 1, max: 100)
```

#### Response 200 OK
```json
[
  {
    "id": "integer или string (уникальный ID записи)",
    "session_id": "string (ID сессии, может быть null)",
    "question": "string",
    "answer": "string",
    "parameters": {
      "k": "integer",
      "temperature": "number",
      "max_tokens": "integer",
      "min_score": "number"
    },
    "sources": [
      {
        "id": "string или integer",
        "filename": "string",
        "breadcrumbs": "string",
        "summary": "string",
        "content": "string (опционально)",
        "category": "string (опционально)",
        "score_hybrid": "number",
        "score_semantic": "number (опционально)",
        "score_lexical": "number (опционально)"
      }
    ],
    "created_at": "string (ISO 8601 datetime)"
  }
]
```

**Важно:**
- `session_id` должен быть **строкой** (string)
- `id` может быть числом (integer) или строкой
- Массив сортируется по `created_at` (новые сверху или снизу — на усмотрение бэкенда)

#### Response 401 Unauthorized
```json
{
  "detail": "Not authenticated"
}
```

---

### 4. GET /history/{chat_id}

**Описание:** Получение деталей конкретного чата

#### Path Parameters
```
chat_id: integer или string (ID записи в истории)
```

#### Response 200 OK
```json
{
  "id": "integer или string",
  "session_id": "string",
  "question": "string",
  "answer": "string",
  "parameters": {...},
  "sources": [...],
  "created_at": "string (ISO 8601)"
}
```

#### Response 404 Not Found
```json
{
  "detail": "Chat not found"
}
```

#### Response 401 Unauthorized
```json
{
  "detail": "Not authenticated"
}
```

---

### 5. POST /feedback

**Описание:** Создание или обновление фидбека (лайк/дизлайк/звёзды)

#### Request Body
```json
{
  "query_id": "string (обязательно) — UUID запроса из /query ответа",
  "feedback_type": "string (обязательно) — 'like', 'dislike', или 'star'",
  "rating": "integer (опционально) — 1-5, только для типа 'star'",
  "comment": "string (опционально) — текст комментария"
}
```

**Важно:**
- Один `query_id` может иметь только один фидбек каждого типа
- При повторной отправке того же типа — обновлять существующий

#### Response 200 OK (создано или обновлено)
```json
{
  "id": "integer или string",
  "query_id": "string",
  "feedback_type": "string",
  "rating": "integer (опционально)",
  "comment": "string (опционально)",
  "created_at": "string (ISO 8601)",
  "updated_at": "string (ISO 8601)"
}
```

#### Response 400 Bad Request
```json
{
  "detail": "string (ошибка валидации)"
}
```

#### Response 401 Unauthorized
```json
{
  "detail": "Not authenticated"
}
```

---

### 6. GET /feedback/{query_id}

**Описание:** Получение фидбека для конкретного запроса

#### Path Parameters
```
query_id: string (UUID запроса)
```

#### Response 200 OK
```json
[
  {
    "id": "integer или string",
    "query_id": "string",
    "feedback_type": "string ('like', 'dislike', или 'star')",
    "rating": "integer (опционально)",
    "comment": "string (опционально)",
    "created_at": "string (ISO 8601)"
  }
]
```

**Важно:**
- Возвращается **массив** фидбеков (может быть несколько типов)
- Если фидбека нет — пустой массив `[]`

#### Response 401 Unauthorized
```json
{
  "detail": "Not authenticated"
}
```

---

### 7. DELETE /feedback/{query_id}

**Описание:** Удаление фидбека для конкретного запроса

#### Path Parameters
```
query_id: string (UUID запроса)
```

#### Query Parameters (опционально)
```
feedback_type: string — удалить только определённый тип (если не указан — все)
```

#### Response 200 OK
```json
{
  "deleted": true,
  "count": "integer — количество удалённых записей"
}
```

#### Response 401 Unauthorized
```json
{
  "detail": "Not authenticated"
}
```

---

### 8. GET /health

**Описание:** Проверка здоровья сервиса (без аутентификации)

#### Response 200 OK
```json
{
  "status": "ok",
  "timestamp": "string (ISO 8601)",
  "version": "string (версия API)"
}
```

---

## Типы данных

### session_id
- **Тип:** `string` (обязательно строка, не число!)
- **Пример:** `"47"`, `"abc123"`, `null`

### query_id
- **Тип:** `string` (UUID формат)
- **Пример:** `"c653eca5-5015-47c1-80aa-0ddeff459d02"`

### id (истории/фидбека)
- **Тип:** `integer` или `string` (принимать оба варианта)
- **Пример:** `45`, `"45"`, `"uuid..."`

### score_*
- **Тип:** `number` (float)
- **Диапазон:** `0.0` — `1.0`
- **Пример:** `0.85`

### created_at
- **Тип:** `string` (ISO 8601 datetime)
- **Пример:** `"2026-03-23T14:30:00Z"`

---

## Обработка ошибок

### 400 Bad Request
```json
{
  "detail": "string | object"
}
```
Для валидации Pydantic:
```json
{
  "detail": [
    {
      "type": "string_type",
      "loc": ["body", "session_id"],
      "msg": "Input should be a valid string",
      "input": 47
    }
  ]
}
```

### 401 Unauthorized
```json
{
  "detail": "Not authenticated"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "string (описание ошибки)"
}
```

---

## Требования к бэкенду

### 1. session_id должен быть string
```python
# ✅ Правильно
session_id: str | None = None

# ❌ Неправильно (вызовет ошибку 422)
session_id: int | None = None
```

Если нужно поддерживать и числа, и строки:
```python
from typing import Union
from pydantic import field_validator

class QueryRequest(BaseModel):
    session_id: Union[str, int, None] = None
    
    @field_validator('session_id', mode='before')
    @classmethod
    def convert_session_id(cls, v):
        if v is None:
            return None
        return str(v)
```

### 2. CORS
Разрешить запросы с фронтенда:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # или "*" для разработки
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 3. Аутентификация через JWT
Парсить токен из заголовка `Authorization: Bearer <token>` и валидировать через Supabase JWKS.

### 4. Логирование
Логировать:
- Запросы (endpoint, user_id, параметры)
- Ошибки (с stack trace)
- Время выполнения запросов

---

## Примеры запросов

### cURL: Отправить вопрос
```bash
curl -X POST http://localhost:8880/query \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Как подать заявку на подключение?",
    "k": 10,
    "temperature": 0.8,
    "max_tokens": 2000,
    "session_id": "47"
  }'
```

### cURL: Получить историю
```bash
curl -X GET "http://localhost:8880/history?limit=50" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

### cURL: Отправить фидбек
```bash
curl -X POST http://localhost:8880/feedback \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  -H "Content-Type: application/json" \
  -d '{
    "query_id": "c653eca5-5015-47c1-80aa-0ddeff459d02",
    "feedback_type": "like"
  }'
```

---

## Чек-лист для бэкенда

- [ ] `session_id` принимает `string` (или `Union[str, int]` с конвертацией)
- [ ] `query_id` возвращается как `string` (UUID)
- [ ] `id` в истории может быть `integer` или `string`
- [ ] CORS настроен для фронтенда
- [ ] JWT аутентификация работает
- [ ] `/health` endpoint без аутентификации
- [ ] Ошибки валидации возвращают понятные сообщения
- [ ] Streaming (SSE) работает корректно
- [ ] Фидбек можно создать, получить и удалить

---

**Последнее обновление:** 2026-03-23
