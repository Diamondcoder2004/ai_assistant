# ⚡ Быстрый старт

## Проблема
Ошибка `401 Unauthorized` при входе — Supabase не запущен.

## Решение

### 1. Запустите Supabase (аутентификация)

**Вариант A: Локальный (рекомендуется для разработки)**

```bash
# В отдельной папке (НЕ web_chat_bot)
mkdir supabase-local
cd supabase-local

# Инициализация
supabase init

# Запуск
supabase start
```

**После запуска получите:**
- `API URL`: http://localhost:54321
- `anon key`: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

**Вариант B: Облачный (production)**

1. https://supabase.com → New Project
2. Settings → API
3. Скопируйте:
   - Project URL
   - `anon` public key

### 2. Настройте .env

```bash
# В директории web_chat_bot
cp .env.example .env
```

**Отредактируйте `.env`:**
```env
# Supabase (из шага 1)
VITE_SUPABASE_URL=http://localhost:54321
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Backend API
VITE_API_BASE_URL=http://localhost:8000
```

### 3. Запустите бэкенд (RAG API)

```bash
# В директории bashkir_rag
cd ../bashkir_rag

# Запуск FastAPI
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

**Проверка:**
```bash
curl http://localhost:8000/health
```

### 4. Запустите фронтенд

```bash
# В директории web_chat_bot
npm run dev
```

**Доступ:** http://localhost:5173

---

## ✅ Проверка работы

### 1. Аутентификация

1. Откройте http://localhost:5173
2. Нажмите "Регистрация"
3. Введите email и пароль
4. Должна произойти авторизация

### 2. Чат

1. Введите вопрос
2. Нажмите "Отправить"
3. Должен появиться ответ с источниками

### 3. Параметры

1. Двигайте ползунки слева
2. Числа должны синхронизироваться
3. `min_score` должен меняться с шагом 0.05 (0.00, 0.05, 0.10...)

---

## 🐛 Отладка

### Ошибка "Failed to fetch"

**Проблема:** Бэкенд не запущен

```bash
# Проверьте
curl http://localhost:8000/health

# Если ошибка — запустите бэкенд
cd ../bashkir_rag
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

### Ошибка "401 Unauthorized"

**Проблема:** Supabase не запущен или неверный ключ

```bash
# Проверьте .env
VITE_SUPABASE_URL=http://localhost:54321  # или ваш облачный URL
VITE_SUPABASE_ANON_KEY=...  # скопируйте из Dashboard

# Проверьте Supabase
curl http://localhost:54321/rest/v1/
```

### Streaming не работает

**Проблема:** Бэкенд не возвращает SSE

**Проверьте:**
1. Endpoint `/query/stream` реализован в бэкенде
2. Бэкенд запущен на порту 8000
3. JWT токен валиден

---

## 📁 Структура сервисов

```
┌─────────────────┐
│   Frontend      │  port 5173
│  (Vue 3 + Vite) │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌─────────┐ ┌──────────┐
│Supabase │ │ FastAPI  │
│ port    │ │ port 8000│
│ 54321   │ │          │
└─────────┘ └────┬─────┘
                 │
            ┌────┴────┐
            │         │
            ▼         ▼
       ┌────────┐ ┌────────┐
       │ Qdrant │ │RouterAI│
       │:6333   │ │  API   │
       └────────┘ └────────┘
```

---

## 📊 Команды

### Frontend
```bash
npm run dev      # Разработка
npm run build    # Сборка
npm run preview  # Preview
npm run lint     # Linting
```

### Backend
```bash
uvicorn api.main:app --reload  # Запуск
pytest                         # Тесты
```

### Supabase
```bash
supabase start    # Запуск
supabase stop     # Остановка
supabase status   # Статус
```

### Qdrant
```bash
docker run -p 6333:6333 qdrant/qdrant  # Запуск
docker ps                               # Проверка
```

---

## 🔗 Документация

- [API Documentation](./DOCS_API/API.md)
- [Architecture](./DOCS_API/ARCHITECTURE.md)
- [Components](./docs/COMPONENTS.md)
- [Updates](./docs/UPDATES_API.md)
