# 🚀 Инструкция по запуску

## Требования

1. **Node.js 18+** и **npm**
2. **Python 3.9+** (для бэкенда)
3. **Docker** (для Qdrant, Supabase)

---

## 📦 Быстрый старт

### 1. Установка зависимостей

```bash
# Frontend
npm install
```

### 2. Настройка переменных окружения

```bash
# Скопируйте пример
cp .env.example .env
```

**По умолчанию:**
```env
# Supabase (локальный или облачный)
VITE_SUPABASE_URL=http://localhost:54321
VITE_SUPABASE_ANON_KEY=your-supabase-anon-key

# Backend API (порт 8000)
VITE_API_BASE_URL=http://localhost:8000
```

### 3. Запуск Supabase (аутентификация)

**Вариант A: Локальный Supabase**
```bash
# Установка Supabase CLI
npm install -g supabase

# В отдельной папке (не web_chat_bot)
supabase init
supabase start
```

**Порт:** 54321 (веб-интерфейс), 54322 (база данных)

**Вариант B: Облачный Supabase**
1. Зарегистрируйтесь на https://supabase.com
2. Создайте проект
3. Скопируйте `Project URL` и `anon public key`
4. Вставьте в `.env`:
```env
VITE_SUPABASE_URL=https://xxxxx.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 4. Запуск бэкенда (RAG API)

Согласно [DOCS_API/API.md](./DOCS_API/API.md):

```bash
# Перейдите в директорию бэкенда (bashkir_rag)
cd ../bashkir_rag

# Установите зависимости
pip install -r requirements.txt

# Настройте .env (см. DOCS_API/API.md)

# Запустите FastAPI
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

**Проверка:**
```bash
curl http://localhost:8000/health
# {"status": "ok", "service": "RAG API Башкирэнерго"}
```

### 5. Запуск фронтенда

```bash
# В директории web_chat_bot
npm run dev
```

**Доступ:** `http://localhost:5173`

---

## 🐳 Инфраструктура (Docker)

### Qdrant (векторная БД)

```bash
docker run -d -p 6333:6333 qdrant/qdrant
```

**Проверка:**
```bash
curl http://localhost:6333/collections
```

### Supabase (локально)

```bash
# Установка Supabase CLI
npm install -g supabase

# Запуск
supabase start
```

**Порт:** 54321 (веб-интерфейс), 54322 (база данных)

---

## 🔧 Проверка компонентов

### Бэкенд

```bash
# Health check
curl http://localhost:8000/health

# Тестовый запрос
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT" \
  -d '{"query": "тест", "k": 5}'
```

### Фронтенд

Откройте `http://localhost:5173` и проверьте:
- ✅ Вход/регистрация работают
- ✅ Чат отправляет вопросы
- ✅ Источники отображаются
- ✅ Параметры поиска изменяются

---

## 📊 Архитектура

```
┌─────────────┐     JWT Token      ┌─────────────┐
│   Vue 3     │ ◄────────────────► │  Supabase   │
│  Frontend   │                    │    Auth     │
└──────┬──────┘                    └─────────────┘
       │
       │ HTTP Requests (with JWT)
       ▼
┌─────────────┐     Search         ┌─────────────┐
│  FastAPI    │ ◄────────────────► │   Qdrant    │
│   RAG API   │                    │ Vector DB   │
└──────┬──────┘                    └─────────────┘
       │
       │ LLM Generation
       ▼
┌─────────────┐
│  RouterAI   │
│   (LLM)     │
└─────────────┘
```

---

## 🐛 Отладка

### Ошибка "Failed to fetch"

**Проблема:** Бэкенд не запущен или неправильный порт

**Решение:**
```bash
# Проверьте .env
VITE_API_BASE_URL=http://localhost:8000

# Запустите бэкенд
cd ../bashkir_rag
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

### Ошибка аутентификации

**Проблема:** Неверный JWT токен

**Решение:**
1. Проверьте `VITE_SUPABASE_ANON_KEY` в `.env`
2. Перезайдите в систему (Logout → Login)

### Streaming не работает

**Проблема:** Бэкенд не поддерживает SSE

**Решение:** Убедитесь, что endpoint `/query/stream` реализован в бэкенде.

---

## 📁 Структура проекта

```
web_chat_bot/
├── src/
│   ├── components/
│   │   ├── chat/              # Компоненты чата
│   │   └── ...
│   ├── views/
│   │   ├── Home.vue           # Главная (чат)
│   │   ├── History.vue        # История
│   │   └── ...
│   ├── stores/
│   │   ├── chatStore.js       # Состояние чата
│   │   └── authStore.js       # Аутентификация
│   └── services/
│       └── supabase.js        # API клиент
├── docs/                      # Документация
│   ├── ARCHITECTURE.md
│   ├── COMPONENTS.md
│   ├── UPDATES_API.md
│   └── README.md
├── DOCS_API/                  # Документация бэкенда
│   ├── API.md
│   └── ARCHITECTURE.md
├── .env                       # Переменные окружения
├── .env.example               # Пример
└── package.json
```

---

## 🎯 API Endpoints

Согласно [DOCS_API/API.md](./DOCS_API/API.md):

| Метод | Endpoint | Описание |
|-------|----------|----------|
| POST | `/query` | Обычный запрос |
| POST | `/query/stream` | Streaming (SSE) |
| GET | `/history?limit=50` | История чатов |
| POST | `/feedback` | Создать фидбек |
| GET | `/feedback/{chat_id}` | Получить фидбек |
| DELETE | `/feedback/{chat_id}` | Удалить фидбек |
| GET | `/health` | Проверка сервиса |

---

## 📝 Переменные окружения

### Frontend (.env)

```env
# Supabase
VITE_SUPABASE_URL=http://localhost:8000
VITE_SUPABASE_ANON_KEY=your-key

# Backend API
VITE_API_BASE_URL=http://localhost:8000
```

### Backend (.env)

См. [DOCS_API/API.md](./DOCS_API/API.md#переменные-окружения)

```env
# Qdrant
QDRANT_HOST=localhost
QDRANT_PORT=6333
COLLECTION_NAME=BASHKIR_ENERGO_PERPLEXITY

# RouterAI
ROUTERAI_API_KEY=sk-...
ROUTERAI_BASE_URL=https://routerai.ru/api/v1

# Embedding
EMBEDDING_MODEL=perplexity/pplx-embed-v1-4b
EMBEDDING_DIM=2560

# LLM
DEFAULT_LLM_MODEL=qwen/qwen3.5-flash-02-23
```

---

## 🚀 Production

### Сборка

```bash
npm run build
```

### Preview

```bash
npm run preview
```

### Деплой

1. Настройте `.env` для production
2. Замените `localhost:8000` на реальный URL
3. Настройте HTTPS
4. Используйте CDN для статики

---

## 📞 Поддержка

- 📖 Документация: `docs/`
- 🔌 API: `DOCS_API/API.md`
- 🐛 Issues: GitHub Issues
