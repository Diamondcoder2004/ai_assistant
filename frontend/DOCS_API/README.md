# API Документация (краткая)

## Endpoints

### POST /query
Непотоковый запрос ответа на вопрос.

**Request:**
```json
{
  "query": "Как подать заявку на технологическое присоединение?",
  "k": 10,
  "temperature": 0.8,
  "max_tokens": 2000,
  "min_score": 0.0,
  "session_id": null
}
```

**Response:**
```json
{
  "query_id": "uuid",
  "answer": "Текст ответа...",
  "sources": [
    {
      "id": 1,
      "filename": "861_Постановление",
      "breadcrumbs": "Раздел II → Пункт 8",
      "summary": "Порядок подачи заявки...",
      "score_hybrid": 0.85,
      "score_pref": 0.78,
      "score_bm25": 0.65,
      "score_hype": 0.72
    }
  ],
  "parameters": {...},
  "session_id": "uuid"
}
```

**Параметры:**

| Поле | Тип | Default | Описание |
|------|-----|---------|----------|
| `query` | string | — | Текст вопроса (1-5000 символов) |
| `k` | integer | 10 | Количество документов (1-100) |
| `temperature` | float | 0.8 | Температура LLM (0.0-2.0) |
| `max_tokens` | integer | 2000 | Максимум токенов (100-8000) |
| `min_score` | float | 0.0 | Порог релевантности (0.0-1.0) |
| `session_id` | string\|null | null | ID сессии для диалога |

---

### POST /query/stream
Потоковый запрос с SSE (Server-Sent Events).

**События:**
- `status` — статус обработки (поиск, генерация)
- `sources` — список источников (JSON массив)
- `session_id` — идентификатор сессии
- `token` — очередной токен ответа
- `done` — завершение (полный ответ)
- `error` — ошибка

**Пример потока:**
```
event: status
data: 🔍 Поиск документов...

event: sources
data: [{"id": 1, "filename": "...", ...}]

event: session_id
data: abc-123-def

event: token
data: Для

event: token
data: подачи

event: done
data: Для подачи заявки необходимо...
```

---

### GET /history
Получение истории чатов пользователя.

**Request:**
```
GET /history?limit=50
```

**Response:**
```json
[
  {
    "id": 1,
    "question": "Как подать заявку?",
    "answer": "...",
    "parameters": {...},
    "sources": [...],
    "created_at": "2026-03-22T12:00:00"
  }
]
```

---

### GET /history/{chat_id}
Получение конкретного чата по ID.

---

### POST /feedback
Отправка обратной связи.

**Request:**
```json
{
  "chat_id": "uuid",
  "feedback_type": "like",
  "rating": 5,
  "comment": "Отличный ответ!"
}
```

**feedback_type:** `like`, `dislike`, `star`

---

### GET /feedback/{chat_id}
Получение фидбека для чата.

---

### DELETE /feedback/{chat_id}
Удаление фидбека.

---

### GET /health
Проверка здоровья сервиса.

**Response:**
```json
{
  "status": "ok",
  "timestamp": "2026-03-22T12:00:00",
  "service": "RAG API Башкирэнерго"
}
```

---

## Переменные окружения

| Переменная | Описание | Default |
|------------|----------|---------|
| `QDRANT_HOST` | Хост Qdrant | localhost |
| `QDRANT_PORT` | Порт Qdrant | 6333 |
| `COLLECTION_NAME` | Коллекция для поиска | BASHKIR_ENERGO_PERPLEXITY |
| `ROUTERAI_API_KEY` | API ключ RouterAI | — |
| `SUPABASE_URL` | URL Supabase | — |
| `SUPABASE_SERVICE_ROLE_KEY` | Service role ключ | — |

---

## Сессионность

Для возобновления диалога используйте `session_id`:

1. Первый запрос без `session_id` → сервер создаст новый
2. Сервер вернёт `session_id` в ответе
3. Последующие запросы с тем же `session_id` → история учтена

---

## Форматирование ответов

### Источники
- `filename` — имя файла без расширения
- `breadcrumbs` — путь к разделу в документе
- `summary` — краткое содержание чанка
- `score_*` — оценки релевантности

### Оценки
| Поле | Описание |
|------|----------|
| `score_hybrid` | Общая оценка гибридного поиска |
| `score_pref` | Семантический поиск (summary + content) |
| `score_hype` | Семантический поиск (hypothetical questions) |
| `score_bm25` | Лексический поиск (BM25) |

---

## Примеры

### Python (requests)
```python
import requests

response = requests.post(
    "http://localhost:8880/query",
    json={"query": "Как подать заявку?", "k": 10},
    headers={"Authorization": "Bearer YOUR_JWT_SECRET"}
)

data = response.json()
print(data["answer"])
print(data["sources"])
```

### JavaScript (fetch)
```javascript
// Непотоковый
const response = await fetch('/query', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer YOUR_JWT_SECRET'
  },
  body: JSON.stringify({
    query: 'Как подать заявку?',
    k: 10
  })
});

const data = await response.json();
console.log(data.answer);

// Потоковый (SSE)
const eventSource = new EventSource('/query/stream');

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.event === 'token') {
    console.log(data.data);
  } else if (data.event === 'session_id') {
    console.log('Session:', data.data);
  }
};
```

---

## Логирование

Логи сохраняются в `logs/api_YYYYMMDD.log`

**Уровни:**
- `INFO` — основные этапы
- `DEBUG` — отладка
- `ERROR` — ошибки с traceback
