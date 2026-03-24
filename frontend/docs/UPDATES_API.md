# Обновления API и Frontend — 2026-03-22

## 🎯 Исправления

### 1. Параметры поиска (SearchParamsPanel.vue)

**Проблема:** `min_score` округлялся до 0 или 1 вместо шага 0.05

**Решение:**
```javascript
// ❌ До
function updateParam(key, value, min, max) {
  // Округление только по min/max
}

// ✅ После
function updateParam(key, value, min, max, step) {
  // Округление по шагу
  if (step) {
    numValue = Math.round(numValue / step) * step
    numValue = Math.round(numValue * 100) / 100
  }
}
```

**Обновленные параметры:**

| Параметр | Min | Max | Step | Пример |
|----------|-----|-----|------|--------|
| `k` | 5 | 50 | 1 | 5, 6, 7... 50 |
| `rerank_top_k` | 1 | 10 | 1 | 1, 2, 3... 10 |
| `temperature` | 0 | 1.5 | 0.1 | 0.0, 0.1, 0.2... 1.5 |
| `max_tokens` | 500 | 4000 | 100 | 500, 600, 700... 4000 |
| `min_score` | 0 | 1 | **0.05** | 0.00, 0.05, 0.10... 1.00 |

---

### 2. SSE Streaming (supabase.js)

**Проблема:** Неправильный формат парсинга SSE событий

**Решение:** Обновлён парсинг согласно документации API:

```javascript
// ✅ Правильный формат SSE
event: token
data: Для

event: token
data: подачи

event: sources
data: [{"id":1,"filename":"doc.pdf",...}]

event: session_id
data: 550e8400-e29b-41d4-a716-446655440001

event: done
data: {"answer":"Полный ответ..."}
```

**Обновлённый парсинг:**
```javascript
// Обработка event: строки
if (line.startsWith('event: ')) {
  currentEvent = line.slice(7).trim();
  continue;
}

// Обработка data: строки
if (line.startsWith('data: ')) {
  const data = line.slice(6).trim();
  
  // token - простая строка
  if (currentEvent === 'token') {
    onToken?.(data);
    continue;
  }
  
  // Остальные - JSON
  if (data.startsWith('{') || data.startsWith('[')) {
    const parsed = JSON.parse(data);
    // ...
  }
}
```

---

### 3. API Endpoints

Согласно документации `DOCS_API/API.md`:

#### POST /query/stream

**Request:**
```json
{
  "query": "Как подать заявку?",
  "k": 30,
  "rerank_top_k": 3,
  "temperature": 0.8,
  "max_tokens": 2000,
  "min_score": 0.0,
  "session_id": null
}
```

**Response (SSE):**
```
event: status
data: 🔍 Поиск документов...

event: sources
data: [{"id":1,"filename":"861_Постановление",...}]

event: session_id
data: 550e8400-e29b-41d4-a716-446655440001

event: token
data: Для

event: token
data: подачи

event: done
data: {"answer":"Для подачи заявки..."}
```

---

## 📦 Обновлённые файлы

| Файл | Изменения |
|------|-----------|
| `src/components/chat/SearchParamsPanel.vue` | Добавлен параметр `step` в `updateParam()` |
| `src/services/supabase.js` | Обновлён SSE парсинг, добавлен `onStatus` |
| `src/stores/chatStore.js` | Готов к использованию `onStatus` |

---

## ✅ Проверка

### Параметры поиска
```javascript
// min_score теперь работает корректно:
0.00 → 0.05 → 0.10 → 0.15 → ... → 0.95 → 1.00
```

### Streaming
```javascript
// Токены приходят по одному:
onToken('Для')
onToken(' ')
onToken('подачи')
onToken(' ')
onToken('заявки')
```

### Источники
```javascript
// Массив источников одним событием:
onSources([
  {
    "id": 1,
    "filename": "861_Постановление",
    "breadcrumbs": "Раздел II → Пункт 8",
    "score_hybrid": 0.85,
    "score_rerank": 0.92
  }
])
```

---

## 🔧 Соответствие API

### Поддерживаемые диапазоны

| Параметр | API限制 | Frontend |
|----------|---------|----------|
| `k` | 1-100 | 5-50 ✅ |
| `rerank_top_k` | 1-10 | 1-10 ✅ |
| `temperature` | 0.0-2.0 | 0-1.5 ✅ |
| `max_tokens` | 100-8000 | 500-4000 ✅ |
| `min_score` | 0.0-1.0 | 0-1 ✅ |

### Аутентификация
```javascript
headers: {
  'Content-Type': 'application/json',
  'Authorization': `Bearer ${session.access_token}`
}
```

### История
```javascript
GET /history?limit=50
Authorization: Bearer <token>
```

### Фидбек
```javascript
POST /feedback
{
  "chat_id": "uuid",
  "feedback_type": "like",  // or "dislike", "star"
  "rating": 5,              // for "star"
  "comment": "..."
}
```

---

## 📊 Сборка

```
✓ 141 modules transformed
✓ built in 409ms

dist/assets/Home-BPXLUeb3.js    25.98 kB │ gzip: 7.81 kB
```

---

## 🎨 UI Обновления

### Приветственное окно
```
👋 Добро пожаловать в чат-бот Башкирэнерго!

Попробуйте спросить:
[📋 Как подать заявку?] [📄 Какие документы?]
[⏱️ Сроки] [💰 Стоимость]
```

### Параметры поиска
- ✅ Slider + Number input синхронизированы
- ✅ Шаг 0.05 для `min_score`
- ✅ Валидация диапазона
- ✅ Подсказки для каждого параметра

---

## 📝 Заметки

### EventSource vs Fetch Streaming

**EventSource:**
```javascript
const es = new EventSource('/stream');
es.addEventListener('token', (e) => {...});
```

**Fetch (используется у нас):**
```javascript
const response = await fetch('/stream');
const reader = response.body.getReader();
// Ручной парсинг SSE
```

**Почему Fetch:**
- Лучше контроль над заголовками (Authorization)
- Поддержка CORS
- Возможность отмены через AbortController

---

## 🚀 Следующие шаги

1. ✅ Протестировать streaming в браузере
2. ✅ Проверить синхронизацию параметров
3. ✅ Проверить работу session_id
4. ⏳ Добавить индикатор статуса (status events)
5. ⏳ Добавить обработку ошибок (error events)
