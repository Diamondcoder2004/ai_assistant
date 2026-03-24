# ИИ-ассистент по технологическому присоединению (Башкирэнерго)

Проект для разворачивания сервера на Docker-compose. ИИ-ассистент для поддержки клиентов по вопросам технологического присоединения.

## 📋 Описание

Система представляет собой RAG (Retrieval-Augmented Generation) приложение с использованием:
- **FastAPI** — бэкенд API
- **Vue.js 3** — фронтенд
- **Qdrant** — векторная база данных (существующий экземпляр)
- **Supabase** — база данных и аутентификация
- **RouterAI** — LLM и эмбеддинги

## 🏗️ Архитектура

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Frontend  │────▶│   Backend    │────▶│   Qdrant    │
│  (Vue.js)   │     │  (FastAPI)   │     │  (Vector)   │
│   Port 80   │     │   Port 8880  │     │   Port 6333 │
└─────────────┘     └──────────────┘     └─────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │   Supabase   │
                    │  (PostgreSQL)│
                    └──────────────┘
```

## 📁 Структура проекта

```
ai_assistant/
├── backend/              # FastAPI приложение (Agentic RAG)
│   ├── api/             # API endpoints
│   ├── agents/          # Агенты (Search, Response, Query Generator)
│   ├── tools/           # Инструменты (Search Tool)
│   ├── prompts/         # Системные промпты
│   ├── utils/           # Утилиты (Embeddings)
│   ├── config.py        # Конфигурация
│   ├── main.py          # Точка входа
│   ├── requirements.txt # Зависимости Python
│   └── Dockerfile
├── frontend/            # Vue.js приложение
│   ├── src/
│   │   ├── components/  # Vue компоненты
│   │   ├── views/       # Страницы
│   │   ├── stores/      # Pinia stores
│   │   ├── services/    # API сервисы
│   │   └── router/      # Роутинг
│   ├── package.json
│   ├── Dockerfile
│   └── nginx.conf
├── database/            # SQL скрипты
│   └── init.sql
├── docker-compose.yml   # Основная конфигурация Docker
├── .env                 # Переменные окружения
└── README.md
```

## 🚀 Быстрый старт

### 1. Предварительные требования

- Docker Desktop (или Docker + Docker Compose)
- Node.js 20+ (для локальной разработки)
- Python 3.11+ (для локальной разработки)
- API ключ RouterAI
- Запущенный Qdrant на порту 6333

### 2. Настройка переменных окружения

Скопируйте `.env.example` в `.env` и заполните значения:

```bash
cp .env.example .env
```

**Обязательные переменные:**
- `ROUTERAI_API_KEY` — ваш API ключ RouterAI
- `SUPABASE_URL` — URL Supabase (локальный или облачный)
- `SUPABASE_SERVICE_ROLE_KEY` — сервисный ключ Supabase
- `SUPABASE_JWT_SECRET` — секрет JWT для аутентификации

### 3. Инициализация базы данных

Выполните SQL скрипт в Supabase:

1. Откройте Supabase Studio
2. Перейдите в SQL Editor
3. Выполните содержимое `database/init.sql`

Или через CLI:
```bash
psql -h <host> -U postgres -d postgres -f database/init.sql
```

### 4. Запуск через Docker Compose

```bash
# Запуск всех сервисов
docker-compose up -d

# Просмотр логов
docker-compose logs -f

# Остановка
docker-compose down

# Пересборка (после изменений)
docker-compose up -d --build
```

**Сервисы будут доступны по адресам:**
- Фронтенд: http://localhost
- Бэкенд API: http://localhost:8880
- Qdrant: http://localhost:6333 (существующий)

## 🔧 Локальная разработка

### Бэкенд

```bash
cd backend

# Создание виртуального окружения
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Установка зависимостей
pip install -r requirements.txt

# Запуск сервера
uvicorn api.api:app --reload --host 0.0.0.0 --port 8880
```

### Фронтенд

```bash
cd frontend

# Установка зависимостей
npm install

# Запуск dev-сервера
npm run dev

# Сборка для production
npm run build

# Preview production сборки
npm run preview
```

## 🌐 Доступ из интернета

Для предоставления доступа из интернета используйте один из вариантов:

### Вариант 1: Ngrok (быстро для тестирования)

```bash
# Установка ngrok
npm install -g ngrok

# Запуск туннеля
ngrok http 80
```

### Вариант 2: Cloudflare Tunnel

```bash
# Установка cloudflared
# Запуск туннеля
cloudflared tunnel --url http://localhost:80
```

### Вариант 3: Свой сервер с nginx

Настройте reverse proxy на вашем сервере:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 📊 API Endpoints

### Health Check
```
GET /health
```

### Query (поиск и генерация ответа)
```
POST /query
Authorization: Bearer <JWT_TOKEN>

{
  "query": "Как подать заявку на подключение?",
  "k": 10,
  "temperature": 0.8,
  "max_tokens": 2000,
  "session_id": "uuid"
}
```

### Streaming Query (SSE)
```
POST /query/stream
Authorization: Bearer <JWT_TOKEN>
```

### История чатов
```
GET /history?limit=50
Authorization: Bearer <JWT_TOKEN>
```

### Фидбек
```
POST /feedback
GET /feedback/{query_id}
DELETE /feedback/{query_id}
```

## 🔐 Аутентификация

Система использует JWT токены Supabase для аутентификации.

### Регистрация
```
POST /auth/v1/signup
{
  "email": "user@example.com",
  "password": "securepassword",
  "data": { "full_name": "Имя Фамилия" }
}
```

### Вход
```
POST /auth/v1/token?grant_type=password
{
  "email": "user@example.com",
  "password": "securepassword"
}
```

## 🧪 Тестирование

### Бэкенд
```bash
cd backend
pytest
```

### Фронтенд
```bash
cd frontend
npm run test:unit
```

## 📝 Конфигурация поиска

В `.env` можно настроить веса гибридного поиска:

- `RETRIEVE_PREF_WEIGHT` — вес семантического поиска (summary + content)
- `RETRIEVE_HYPE_WEIGHT` — вес семантического поиска (hypothetical questions)
- `RETRIEVE_LEXICAL_WEIGHT` — вес лексического поиска (BM25)
- `RETRIEVE_CONTEXTUAL_WEIGHT` — вес контекстного поиска

Сумма всех весов должна быть равна 1.0.

## 🔧 Troubleshooting

### Ошибка подключения к Qdrant
```
# Проверьте, что Qdrant запущен
docker-compose ps

# Проверьте логи
docker-compose logs backend
```

### Ошибка аутентификации
```
# Проверьте JWT_SECRET в .env
# Убедитесь, что SUPABASE_JWT_SECRET совпадает с Supabase
```

### Ошибка CORS
```
# Бэкенд настроен на разрешение всех origin
# Проверьте настройки в api/api.py
```

## 📄 Лицензия

Проект создан для внутреннего использования Башкирэнерго.

## 📞 Контакты

По вопросам обращайтесь в отдел разработки.
