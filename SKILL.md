# SKILL — Руководство по проекту AI Assistant

## 📋 Описание

Интеллектуальный чат-бот для Башкирэнерго с RAG (Retrieval-Augmented Generation) архитектурой.

**Стек:**
- **Frontend:** Vue.js 3 + Vite + Pinia
- **Backend:** Python 3.11 + FastAPI
- **БД:** Supabase (Auth + PostgreSQL)
- **Векторный поиск:** Qdrant
- **LLM:** RouterAI (inception/mercury-2)
- **Embeddings:** RouterAI (perplexity/pplx-embed-v1-4b)

---

## 🚀 Быстрый старт

### 1. Требования

- Docker + Docker Compose
- Node.js 20+ (для локальной разработки frontend)
- Python 3.11+ (для локальной разработки backend)
- Qdrant (порт 6333)
- Supabase (порт 8000)

### 2. Конфигурация

**backend/.env:**
```env
# Qdrant
QDRANT_HOST=host.docker.internal
QDRANT_PORT=6333
COLLECTION_NAME=BASHKIR_ENERGO_PERPLEXITY

# RouterAI
ROUTERAI_API_KEY=sk-xxx
ROUTERAI_BASE_URL=https://routerai.ru/api/v1
EMBEDDING_MODEL=perplexity/pplx-embed-v1-4b
EMBEDDING_DIM=2560
DEFAULT_LLM_MODEL=inception/mercury-2

# Supabase
SUPABASE_URL=http://host.docker.internal:8000
SUPABASE_KEY=eyJhbG...
SUPABASE_SERVICE_ROLE_KEY=eyJhbG...
SUPABASE_JWT_SECRET=xxx

# JWT
JWT_SECRET_KEY=xxx
JWT_ALGORITHM=HS256

# Веса поиска
RETRIEVE_PREF_WEIGHT=0.4
RETRIEVE_HYPE_WEIGHT=0.3
RETRIEVE_LEXICAL_WEIGHT=0.2
RETRIEVE_CONTEXTUAL_WEIGHT=0.1
```

**frontend/.env:**
```env
VITE_SUPABASE_URL=http://46.191.174.57:8000
VITE_SUPABASE_ANON_KEY=eyJhbG...
VITE_API_BASE_URL=http://46.191.174.57:8877
VITE_TEST_MODE=false
```

### 3. Запуск

```bash
# Сборка и запуск
docker-compose up -d --build

# Просмотр логов
docker-compose logs -f

# Остановка
docker-compose down
```

**Доступ:** `http://46.191.174.57:8877`

---

## 🏗️ Архитектура

```
┌─────────────┐
│   Browser   │
└──────┬──────┘
       │ HTTP
       ↓
┌─────────────────┐
│  nginx (port 80)│ ← Docker container
└────────┬────────┘
         │
    ┌────┴────┐
    ↓         ↓
┌───────┐ ┌──────────┐
│ Vue   │ │ FastAPI  │
│ :80   │ │ :8880    │
└───────┘ └────┬─────┘
               │
          ┌────┼────┐
          ↓    ↓    ↓
      ┌────┐ ┌────┐ ┌────────┐
      │Supa│ │Qdrant│ │RouterAI│
      │base│ │ :6333│ │  API   │
      └────┘ └────┘ └────────┘
```

---

## 📁 Структура проекта

```
ai_assistant/
├── backend/
│   ├── agents/           # Агенты (search, response, query_generator)
│   ├── api/              # FastAPI endpoints
│   ├── tools/            # Search tool (BM25 + векторный поиск)
│   ├── utils/            # Утилиты
│   ├── prompts/          # Промпты для LLM
│   ├── config.py         # Конфигурация
│   └── main.py           # Точка входа
├── frontend/
│   ├── src/
│   │   ├── components/   # Vue компоненты
│   │   ├── views/        # Страницы (Home, History, Profile)
│   │   ├── stores/       # Pinia stores (auth, chat, hotkeys)
│   │   └── services/     # API клиенты
│   ├── nginx.conf        # nginx конфигурация
│   └── vite.config.js    # Vite конфигурация
├── docker-compose.yml
└── .env
```

---

## 🔧 Ключевые компоненты

### Backend

**agents/search_agent.py** — Поиск документов:
- Генерирует поисковые запросы через LLM
- Гибридный поиск: pref + hype + contextual + BM25
- Возвращает результаты с оценками релевантности

**agents/response_agent.py** — Генерация ответа:
- Получает результаты поиска
- Формирует ответ через LLM
- Извлекает источники для UI

**tools/search_tool.py** — Поиск в Qdrant:
- 4 компонента: pref, hype, contextual, lexical (BM25)
- Нормализация BM25: `score / max_score`
- Гибридная формула: `0.4*pref + 0.3*hype + 0.1*contextual + 0.2*bm25`

### Frontend

**stores/chatStore.js** — Управление состоянием чата:
- `messages` — текущие сообщения
- `history` — история сессий
- `sendQueryStream()` — streaming запрос к API

**components/chat/ChatMessages.vue** — Отображение сообщений:
- Рендеринг Markdown
- Копирование ответа
- Источники (sources panel)
- Feedback (like/dislike)

---

## 🎯 Горячие клавиши

| Клавиша | Действие |
|---------|----------|
| `Enter` | Отправить сообщение |
| `Shift+Enter` | Новая строка |
| `Ctrl+N` | Новый чат |
| `Ctrl+H` | История |
| `Ctrl+L` | Фокус на ввод |
| `Ctrl+S` | Источники |
| `Ctrl+Shift+C` | Копировать ответ |

---

## 🐛 Отладка

### Логи backend

```bash
docker logs ai-assistant-backend --tail 100 -f
```

### Логи frontend

```bash
docker logs ai-assistant-frontend --tail 100 -f
```

### Тестирование API

```bash
# Health check
curl http://localhost:8880/health

# Query (нужен токен)
curl -X POST http://localhost:8880/query \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"query": "Как подать заявку?"}'
```

---

## 📊 BM25 Нормализация

**Классический подход:**
```python
max_score = max(scores)
normalized = score / max_score  # [0, 1]
```

**Гибридная оценка:**
```python
hybrid = (
    0.4 * pref +      # семантический (summary+content)
    0.3 * hype +      # семантический (hypothetical questions)
    0.1 * contextual + # семантический (соседние чанки)
    0.2 * bm25        # лексический (BM25)
)
```

---

## 🔄 Деплой

### Обновление кода

```bash
# 1. Изменить код
# 2. Пересобрать
docker-compose up -d --build

# 3. Очистить кэш браузера
Ctrl+Shift+Delete
```

### Статический IP

1. Купить у провайдера
2. Пробросить порты в роутере:
   - `8877 → 80` (nginx)
   - `8000 → 8000` (Supabase)
3. Обновить `frontend/.env`:
   ```env
   VITE_SUPABASE_URL=http://<IP>:8000
   VITE_API_BASE_URL=http://<IP>:8877
   ```

---

## 📞 Контакты

- **Email:** almaz_sabitov04@mail.ru
- **Документация:** `/backend/docs/`
- **API:** `/backend/api/`

---

## ⚠️ Важно

1. **Не менять стиль агентов** — промпты в `backend/prompts/` зафиксированы
2. **BM25 без tanh/softmax** — классическая нормализация `score / max_score`
3. **Footer появляется при скролле** — не ломать CSS
4. **Hotkeys работают per-message** — copy animation только у конкретного сообщения

---

*Последнее обновление: 2026-03-24*
