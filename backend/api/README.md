# RAG API — Башкирэнерго (Agentic RAG)

API версии **v1** для интеллектуального поиска и генерации ответов на основе документации компании.

**Базовый URL:** `http://localhost:8880`

## 🚀 Особенности

### Agentic RAG
В отличие от традиционных RAG систем, **Agentic RAG** использует LLM-агентов для:
- 🤖 **Автоматической генерации поисковых запросов** — перефразирование, гипонимы, синонимы
- ⚖️ **Подбора оптимальных весов поиска** — баланс между семантическим и лексическим поиском
- 🔄 **Автоматической повторной попытки** — если результатов мало
- ❓ **Запроса уточнений** — если вопрос слишком общий

### Соответствие API_REQUIREMENTS.md v1
- ✅ `session_id` — строка (string)
- ✅ `query_id` — UUID строка
- ✅ `id` в истории — integer или string
- ✅ Фидбек возвращается массивом
- ✅ DELETE /feedback возвращает `{deleted: true, count: N}`

## 📦 Установка

### 1. Активация виртуального окружения
```bash
# Windows (cmd)
venv\Scripts\activate.bat

# Windows (PowerShell)
.\venv\Scripts\Activate.ps1

# Linux/Mac
source venv/bin/activate
```

### 2. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 3. Настройка переменных окружения
Создайте файл `.env` на основе `.env.example`:
```bash
cp .env.example .env
```

Заполните необходимыми ключами:
```env
# RouterAI API
ROUTERAI_API_KEY=sk-...
ROUTERAI_BASE_URL=https://routerai.ru/api/v1

# Qdrant
QDRANT_HOST=localhost
QDRANT_PORT=6333

# Supabase (Chat History & Feedback)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_JWT_SECRET=your-jwt-secret

# JWT Auth
JWT_SECRET_KEY=your-secret-key-change-in-production
```

## 🔌 Запуск

```bash
# Запуск через uvicorn
uvicorn api.api:app --host 0.0.0.0 --port 8880 --reload
```

**Swagger UI:** http://localhost:8880/docs  
**ReDoc:** http://localhost:8880/redoc

## 📡 Endpoints

### 1. POST /query

**Описание:** Отправка вопроса и получение ответа (без streaming)

**Request:**
```json
{
  "query": "Как оформить заявку на подключение?",
  "k": 10,
  "temperature": 0.8,
  "max_tokens": 2000,
  "min_score": 0.0,
  "session_id": "47"
}
```

**Response 200:**
```json
{
  "query_id": "c653eca5-5015-47c1-80aa-0ddeff459d02",
  "session_id": "47",
  "answer": "Для оформления заявки необходимо...",
  "sources": [
    {
      "id": 1,
      "filename": "Правила ТП",
      "breadcrumbs": "Документы → Нормативные",
      "summary": "Правила технологического присоединения...",
      "content": "",
      "category": "Нормативные",
      "score_hybrid": 0.85,
      "score_semantic": 0.82,
      "score_lexical": 0.78,
      "chunk_id": "12345"
    }
  ],
  "parameters": {
    "k": 10,
    "temperature": 0.8,
    "max_tokens": 2000,
    "min_score": 0.0
  }
}
```

---

### 2. POST /query/stream

**Описание:** Потоковый ответ с использованием Server-Sent Events (SSE)

**Request:** Аналогично `/query`

**Response (SSE Stream):**
```
data: {"token": "Для "}
data: {"token": "оформления "}
data: {"token": "заявки "}
...
data: {"done": true, "query_id": "...", "session_id": "...", "sources": [...]}
```

**Пример JavaScript:**
```javascript
const eventSource = new EventSource('http://localhost:8880/query/stream', {
  headers: { 'Authorization': 'Bearer YOUR_TOKEN' }
});

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.token) {
    console.log('Token:', data.token);
  }
  if (data.done) {
    console.log('Complete!', data);
    eventSource.close();
  }
};
```

---

### 3. GET /history

**Описание:** Получение истории чатов пользователя

**Query Parameters:**
- `limit` (int, default: 50, max: 100)

**Response 200:**
```json
[
  {
    "id": 45,
    "session_id": "47",
    "question": "Как подать заявку?",
    "answer": "Для подачи заявки...",
    "parameters": {
      "k": 10,
      "temperature": 0.8,
      "max_tokens": 2000,
      "min_score": 0.0
    },
    "sources": [...],
    "created_at": "2026-03-23T14:30:00Z"
  }
]
```

---

### 4. GET /history/{chat_id}

**Описание:** Получение деталей конкретного чата

**Path Parameters:**
- `chat_id` (int)

**Response 200:**
```json
{
  "id": 45,
  "session_id": "47",
  "question": "Как подать заявку?",
  "answer": "Для подачи заявки...",
  "parameters": {...},
  "sources": [...],
  "created_at": "2026-03-23T14:30:00Z"
}
```

---

### 5. POST /feedback

**Описание:** Создание или обновление фидбека

**Request:**
```json
{
  "query_id": "c653eca5-5015-47c1-80aa-0ddeff459d02",
  "feedback_type": "like",
  "rating": null,
  "comment": "Отличный ответ!"
}
```

**Возможные `feedback_type`:**
- `like` — лайк
- `dislike` — дизлайк
- `star` — звёздный рейтинг (1-5)

**Response 200:**
```json
{
  "id": 123,
  "query_id": "c653eca5-5015-47c1-80aa-0ddeff459d02",
  "feedback_type": "like",
  "rating": null,
  "comment": "Отличный ответ!",
  "created_at": "2026-03-23T14:30:00Z",
  "updated_at": "2026-03-23T14:30:00Z"
}
```

---

### 6. GET /feedback/{query_id}

**Описание:** Получение фидбека для запроса (возвращает массив)

**Response 200:**
```json
[
  {
    "id": 123,
    "query_id": "c653eca5-5015-47c1-80aa-0ddeff459d02",
    "feedback_type": "like",
    "rating": null,
    "comment": "Отличный ответ!",
    "created_at": "2026-03-23T14:30:00Z",
    "updated_at": "2026-03-23T14:30:00Z"
  }
]
```

---

### 7. DELETE /feedback/{query_id}

**Описание:** Удаление фидбека

**Query Parameters:**
- `feedback_type` (optional) — удалить только определённый тип

**Response 200:**
```json
{
  "deleted": true,
  "count": 1
}
```

---

### 8. GET /health

**Описание:** Проверка здоровья сервиса (без аутентификации)

**Response 200:**
```json
{
  "status": "ok",
  "timestamp": "2026-03-23T14:30:00Z",
  "version": "v1"
}
```

---

## 🔐 Аутентификация

Все endpoints (кроме `/health`) требуют JWT токен в заголовке:

```
Authorization: Bearer <access_token>
```

Токен получается из Supabase Auth session.

**Пример cURL:**
```bash
curl -X POST http://localhost:8880/query \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  -H "Content-Type: application/json" \
  -d '{"query": "Как подключить электричество?"}'
```

---

## 📊 Типы данных

| Поле | Тип | Описание |
|------|-----|----------|
| `session_id` | string | ID сессии (всегда строка!) |
| `query_id` | string (UUID) | Уникальный ID запроса |
| `id` (history) | integer или string | Принимает оба формата |
| `score_*` | float (0.0-1.0) | Оценка релевантности |
| `created_at` | string (ISO 8601) | Дата создания |

---

## 🚨 Обработка ошибок

### 400 Bad Request
```json
{
  "detail": "Validation error message"
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
  "detail": "Internal server error message"
}
```

---

## 📝 Примеры запросов (cURL)

### Отправить вопрос
```bash
curl -X POST http://localhost:8880/query \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Как подать заявку на подключение?",
    "k": 10,
    "temperature": 0.8,
    "max_tokens": 2000,
    "session_id": "47"
  }'
```

### Получить историю
```bash
curl -X GET "http://localhost:8880/history?limit=50" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Отправить фидбек
```bash
curl -X POST http://localhost:8880/feedback \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query_id": "c653eca5-5015-47c1-80aa-0ddeff459d02",
    "feedback_type": "like"
  }'
```

### Удалить фидбек
```bash
curl -X DELETE "http://localhost:8880/feedback/c653eca5-5015-47c1-80aa-0ddeff459d02" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 📚 Архитектура

```
┌─────────────┐
│   Client    │
│  (Request)  │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────┐
│           FastAPI Layer                 │
│  - Аутентификация (JWT)                 │
│  - Валидация (Pydantic)                 │
│  - Логирование                          │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│         Agentic RAG                     │
│  ┌───────────────────────────────────┐  │
│  │  Query Generator Agent            │  │
│  │  - Генерация поисковых запросов   │  │
│  │  - Подбор весов                   │  │
│  │  - Выбор стратегии                │  │
│  └──────────────┬────────────────────┘  │
│                 │                        │
│  ┌──────────────▼────────────────────┐  │
│  │  Search Tool (Hybrid Retrieval)   │  │
│  │  - Pref + Hype + Lexical + Ctx    │  │
│  └──────────────┬────────────────────┘  │
│                 │                        │
│  ┌──────────────▼────────────────────┐  │
│  │  Response Agent                   │  │
│  │  - Генерация ответа               │  │
│  │  - Проверка уточнений             │  │
│  └───────────────────────────────────┘  │
└──────────────┬───────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│         Supabase (PostgreSQL)           │
│  - chats: история диалогов              │
│  - feedback: обратная связь             │
└─────────────────────────────────────────┘
```

---

## 🧪 Тестирование

```bash
# Проверка health
curl http://localhost:8880/health

# Запуск тестов
pytest tests/ -v
```

---

## 📞 Поддержка

- Документация: `/docs` (Swagger UI)
- Версия API: **v1**
- Последнее обновление: 2026-03-23
