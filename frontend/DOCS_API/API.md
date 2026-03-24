# API Документация RAG API для фронтенда

**Base URL:** `http://localhost:8880`

**Аутентификация:** Bearer Token (JWT)

```
Authorization: Bearer YOUR_JWT_SECRET
```

---

## 🔌 Endpoints

### POST /query/stream

**Потоковый запрос с использованием Server-Sent Events (SSE).**

Рекомендуется для фронтенда — показывает прогресс обработки и потоковый вывод ответа.

#### Request

```json
{
  "query": "Как подать заявку на технологическое присоединение?",
  "k": 30,
  "rerank_top_k": 3,
  "temperature": 0.8,
  "max_tokens": 2000,
  "min_score": 0.0,
  "session_id": null
}
```

#### Параметры запроса

| Поле | Тип | По умолчанию | Описание |
|------|-----|--------------|----------|
| `query` | string | - | Текст вопроса (1-5000 символов) |
| `k` | integer | 30 | Количество документов для поиска (1-100) |
| `rerank_top_k` | integer | 3 | Количество документов после реранка (1-10) |
| `temperature` | float | 0.8 | Температура генерации LLM (0.0-2.0) |
| `max_tokens` | integer | 2000 | Максимум токенов в ответе (100-8000) |
| `min_score` | float | 0.0 | Минимальный порог релевантности (0.0-1.0) |
| `session_id` | string\|null | null | ID сессии для возобновления диалога |

#### Response (SSE Stream)

```
event: status
data: 🔍 Поиск документов...

event: status
data: ⚖️ Оценка релевантности...

event: sources
data: [{"id":1,"filename":"861_Постановление",...}]

event: session_id
data: 550e8400-e29b-41d4-a716-446655440001

event: status
data: ✍️ Генерация ответа...

event: token
data: Для

event: token
data: подачи

event: token
data: заявки

...

event: done
data: Для подачи заявки необходимо...
```

#### События SSE

| Событие | Описание | Формат данных |
|---------|----------|---------------|
| `status` | Статус обработки | Текст |
| `sources` | Список источников | JSON массив |
| `session_id` | ID сессии | UUID строка |
| `token` | Токен ответа | Строка |
| `done` | Завершение | Полный ответ (строка) |
| `error` | Ошибка | Текст ошибки |

#### Формат источника (sources)

```json
{
  "id": 1,
  "filename": "861_Постановление",
  "breadcrumbs": "Раздел II → Пункт 8",
  "summary": "Порядок подачи заявки...",
  "score_hybrid": 0.85,
  "score_rerank": 0.92,
  "score_pref": 0.78,
  "score_bm25": 0.65,
  "score_hype": 0.72
}
```

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | integer | Порядковый номер |
| `filename` | string | Имя файла (без расширения) |
| `breadcrumbs` | string | Путь к разделу |
| `summary` | string | Краткое содержание |
| `score_hybrid` | float | Общая оценка |
| `score_rerank` | float | Оценка реранкера |
| `score_pref` | float | Оценка pref-вектора |
| `score_bm25` | float | Оценка BM25 |
| `score_hype` | float | Оценка hype-вектора |

---

### POST /query

**Непотоковый запрос.** Возвращает полный ответ одним запросом.

Используйте, если потоковый вывод не нужен.

#### Request

Аналогичен `/query/stream`.

#### Response

```json
{
  "query_id": "550e8400-e29b-41d4-a716-446655440000",
  "answer": "Для подачи заявки...",
  "sources": [...],
  "parameters": {...},
  "session_id": "550e8400-e29b-41d4-a716-446655440001"
}
```

---

### GET /history

**Получение истории чатов пользователя.**

#### Request

```
GET /history?limit=50
```

#### Response

```json
[
  {
    "id": 1,
    "question": "Как подать заявку?",
    "answer": "Для подачи заявки...",
    "parameters": {...},
    "sources": [...],
    "created_at": "2026-03-22T12:00:00"
  }
]
```

---

### POST /feedback

**Отправка обратной связи.**

#### Request

```json
{
  "chat_id": "550e8400-e29b-41d4-a716-446655440000",
  "feedback_type": "like",
  "rating": 5,
  "comment": "Отличный ответ!"
}
```

| Поле | Тип | Описание |
|------|-----|----------|
| `chat_id` | UUID | ID чата |
| `feedback_type` | enum | `like`, `dislike`, `star` |
| `rating` | integer\|null | Оценка 1-5 (для `star`) |
| `comment` | string\|null | Комментарий (макс. 1000 символов) |

---

### GET /health

**Проверка здоровья сервиса.**

```json
{
  "status": "ok",
  "timestamp": "2026-03-22T12:00:00.000Z",
  "service": "RAG API Башкирэнерго"
}
```

---

## 💻 Примеры для фронтенда

### JavaScript (EventSource)

```javascript
const API_URL = 'http://localhost:8880';
const JWT_TOKEN = 'YOUR_JWT_SECRET';

function queryStream(question, sessionId = null) {
  return new Promise((resolve, reject) => {
    const url = new URL(`${API_URL}/query/stream`);
    
    const eventSource = new EventSource(url, {
      headers: {
        'Authorization': `Bearer ${JWT_TOKEN}`,
        'Content-Type': 'application/json'
      }
    });

    const result = {
      sessionId: null,
      sources: [],
      answer: ''
    };

    eventSource.addEventListener('status', (e) => {
      console.log('Status:', e.data);
      // Обновить UI со статусом
    });

    eventSource.addEventListener('sources', (e) => {
      result.sources = JSON.parse(e.data);
      // Показать источники
    });

    eventSource.addEventListener('session_id', (e) => {
      result.sessionId = e.data;
      // Сохранить session_id для следующих запросов
    });

    eventSource.addEventListener('token', (e) => {
      result.answer += e.data;
      // Добавить токен к ответу (печатная машинка)
    });

    eventSource.addEventListener('done', (e) => {
      result.answer = e.data;
      eventSource.close();
      resolve(result);
    });

    eventSource.addEventListener('error', (e) => {
      eventSource.close();
      reject(new Error(e.data));
    });

    // Отправить запрос
    fetch(url, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${JWT_TOKEN}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        query: question,
        session_id: sessionId
      })
    }).catch(reject);
  });
}

// Использование
queryStream('Как подать заявку?')
  .then(result => {
    console.log('Ответ:', result.answer);
    console.log('Источники:', result.sources);
    console.log('Сессия:', result.sessionId);
  })
  .catch(console.error);
```

### React (хук)

```jsx
import { useState, useCallback } from 'react';

function useRAGQuery() {
  const [loading, setLoading] = useState(false);
  const [answer, setAnswer] = useState('');
  const [sources, setSources] = useState([]);
  const [sessionId, setSessionId] = useState(null);
  const [status, setStatus] = useState('');
  const [error, setError] = useState(null);

  const query = useCallback((question, prevSessionId = null) => {
    setLoading(true);
    setError(null);
    setAnswer('');
    setSources([]);
    setStatus('');

    return new Promise((resolve, reject) => {
      const eventSource = new EventSource(
        'http://localhost:8880/query/stream',
        {
          headers: {
            'Authorization': 'Bearer YOUR_JWT_TOKEN',
            'Content-Type': 'application/json'
          }
        }
      );

      eventSource.addEventListener('status', (e) => setStatus(e.data));
      
      eventSource.addEventListener('sources', (e) => 
        setSources(JSON.parse(e.data))
      );
      
      eventSource.addEventListener('session_id', (e) => 
        setSessionId(e.data)
      );
      
      eventSource.addEventListener('token', (e) => 
        setAnswer(prev => prev + e.data)
      );
      
      eventSource.addEventListener('done', (e) => {
        setAnswer(e.data);
        setLoading(false);
        eventSource.close();
        resolve({ answer: e.data, sources, sessionId: e.data });
      });
      
      eventSource.addEventListener('error', (e) => {
        setError(e.data);
        setLoading(false);
        eventSource.close();
        reject(new Error(e.data));
      });

      fetch('http://localhost:8880/query/stream', {
        method: 'POST',
        headers: {
          'Authorization': 'Bearer YOUR_JWT_TOKEN',
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          query: question,
          session_id: prevSessionId
        })
      });
    });
  }, []);

  return { loading, answer, sources, sessionId, status, error, query };
}

// Использование в компоненте
function ChatComponent() {
  const { loading, answer, sources, sessionId, query } = useRAGQuery();

  const handleSubmit = async (question) => {
    try {
      await query(question, sessionId);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div>
      <input onKeyPress={(e) => handleSubmit(e.target.value)} />
      <div>{answer}</div>
      <div>{sources.map(s => s.filename).join(', ')}</div>
    </div>
  );
}
```

### Vue 3 (Composition API)

```vue
<script setup>
import { ref } from 'vue';

const loading = ref(false);
const answer = ref('');
const sources = ref([]);
const sessionId = ref(null);
const status = ref('');
const error = ref(null);

async function query(question, prevSessionId = null) {
  loading.value = true;
  error.value = null;
  answer.value = '';
  sources.value = [];

  return new Promise((resolve, reject) => {
    const eventSource = new EventSource(
      'http://localhost:8880/query/stream',
      {
        headers: {
          'Authorization': 'Bearer YOUR_JWT_TOKEN',
          'Content-Type': 'application/json'
        }
      }
    );

    eventSource.addEventListener('status', (e) => {
      status.value = e.data;
    });

    eventSource.addEventListener('sources', (e) => {
      sources.value = JSON.parse(e.data);
    });

    eventSource.addEventListener('session_id', (e) => {
      sessionId.value = e.data;
    });

    eventSource.addEventListener('token', (e) => {
      answer.value += e.data;
    });

    eventSource.addEventListener('done', (e) => {
      answer.value = e.data;
      loading.value = false;
      eventSource.close();
      resolve({ answer: answer.value, sources: sources.value });
    });

    eventSource.addEventListener('error', (e) => {
      error.value = e.data;
      loading.value = false;
      eventSource.close();
      reject(new Error(e.data));
    });

    fetch('http://localhost:8880/query/stream', {
      method: 'POST',
      headers: {
        'Authorization': 'Bearer YOUR_JWT_TOKEN',
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        query: question,
        session_id: prevSessionId
      })
    });
  });
}

defineExpose({ query, loading, answer, sources, sessionId, status, error });
</script>
```

---

## 🔄 Сессионность

### Первый запрос

```json
{
  "query": "Как подать заявку?",
  "session_id": null
}
```

**Ответ:**
```json
{
  "session_id": "abc-123-def",
  ...
}
```

### Возобновление диалога

```json
{
  "query": "А какие документы нужны?",
  "session_id": "abc-123-def"
}
```

Сервер загрузит последние 10 сообщений из истории сессии.

---

## ⚙️ Конфигурация

### Переменные окружения (для разработчиков)

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `QDRANT_HOST` | Хост Qdrant | localhost |
| `QDRANT_PORT` | Порт Qdrant | 6333 |
| `COLLECTION_NAME` | Коллекция для поиска | BASHKIR_ENERGO_PERPLEXITY |
| `ROUTERAI_API_KEY` | API ключ RouterAI | - |
| `SUPABASE_URL` | URL Supabase | - |
| `SUPABASE_SERVICE_ROLE_KEY` | Service role ключ | - |

### Реранкер

**Реранкер отключен по умолчанию.** Для включения нужно программно вызвать `enable_reranker()` при старте API.

---

## ⚠️ Коды ошибок

| Код | Описание |
|-----|----------|
| 200 | Успешный запрос |
| 400 | Неверный запрос |
| 401 | Ошибка аутентификации |
| 404 | Ресурс не найден |
| 500 | Внутренняя ошибка сервера |

---

## 📏 Ограничения

| Параметр | Ограничение |
|----------|-------------|
| Длина запроса | 1-5000 символов |
| k (документы) | 1-100 |
| rerank_top_k | 1-10 |
| Температура | 0.0-2.0 |
| max_tokens | 100-8000 |
