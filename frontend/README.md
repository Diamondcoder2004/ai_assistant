# 💬 BashkirEnergo Chat Bot

Чат-бот для клиентов Башкирэнерго по вопросам технологического присоединения к электрическим сетям.

## 🚀 Быстрый старт

### Требования
- Node.js 18+ 
- Python 3.9+ (для бэкенда)
- Supabase (локально или облако)

### Установка и запуск

```bash
# Установка зависимостей
npm install

# Запуск разработки
npm run dev

# Сборка production
npm run build
```

## 📋 Возможности

### 💬 Чат
- Streaming токенов в реальном времени
- Гибридный поиск (семантический + лексический)
- Источники с оценками релевантности
- Фидбек (лайк/дизлайк/звёзды)
- LaTeX формулы

### ⚙️ Параметры поиска
- Количество документов: 1–15 (рекомендуется: 8)
- Температура: 0–1.5 (рекомендуется: 0.7–0.8)
- Длина ответа (макс.): 500–4000 токенов (~375–3000 слов)
- Порог сходства: 0–1 (рекомендуется: 0–0.2)

### 📜 История
- Просмотр всех чатов
- Поиск по вопросам и ответам
- Возобновление сессий

## 🏗 Архитектура

```
web_chat_bot/
├── src/
│   ├── components/
│   │   ├── chat/              # Компоненты чата
│   │   │   ├── SearchParamsPanel.vue   # Параметры поиска
│   │   │   ├── ChatMessages.vue        # Сообщения с markdown/LaTeX
│   │   │   ├── ChatInputArea.vue       # Поле ввода
│   │   │   ├── ChatHeader.vue          # Шапка
│   │   │   ├── SourcesPanel.vue        # Источники
│   │   │   └── modals/                 # Модальные окна
│   ├── views/
│   │   ├── Home.vue           # Главная (чат)
│   │   ├── History.vue        # История чатов
│   │   ├── Login.vue          # Вход
│   │   ├── Register.vue       # Регистрация
│   │   └── Profile.vue        # Профиль
│   ├── stores/
│   │   ├── chatStore.js       # Состояние чата
│   │   └── authStore.js       # Аутентификация
│   ├── services/
│   │   └── supabase.js        # API клиенты
│   └── router/
│       └── index.js           # Маршруты
├── docs/                      # Документация фронтенда
├── DOCS_API/                  # Документация бэкенда
└── package.json
```

## 🔧 Технологический стек

| Компонент | Технология |
|-----------|------------|
| Frontend | Vue.js 3 (Composition API) |
| State | Pinia |
| Routing | Vue Router |
| Backend API | FastAPI |
| Auth/DB | Supabase |
| LLM | RouterAI (Qwen, Saiga) |
| Vector DB | Qdrant |
| Embeddings | Perplexity pplx-embed-v1-4b |
| Markdown | marked |
| LaTeX | KaTeX |

## 🔌 API Endpoints

| Метод | Endpoint | Описание |
|-------|----------|----------|
| POST | `/query` | Обычный запрос |
| POST | `/query/stream` | Streaming (SSE) |
| GET | `/history?limit=50` | История чатов |
| POST | `/feedback` | Создать фидбек (query_id) |
| GET | `/feedback/{query_id}` | Получить фидбек |
| DELETE | `/feedback/{query_id}` | Удалить фидбек |

## 📚 Документация

- [Архитектура](docs/ARCHITECTURE.md) — структура проекта, stores, API
- [Компоненты](docs/COMPONENTS.md) — справочник компонентов с примерами
- [API документация](DOCS_API/README.md) — бэкенд API
- [Быстрый старт](QUICKSTART.md) — установка и запуск
- [Инструкции по запуску](RUN_INSTRUCTIONS.md) — подробные инструкции

## 🎨 Стилевые соглашения

### Цвета
```css
--primary: #0066cc;
--primary-hover: #0052a3;
--background: #f8f9fa;
--border: #e5e7eb;
```

### Breakpoints
- Mobile: < 768px
- Tablet: 768–992px
- Desktop: 992–1200px

## 🐛 Отладка

### Логирование
```javascript
// Включить debug
localStorage.setItem('DEBUG', 'chat')
```

### Частые проблемы

| Проблема | Решение |
|----------|---------|
| Фидбек не работает | Проверить query_id в ответе API |
| Формулы не отображаются | Проверить KaTeX установку |
| JWT истёк | Перезайти в систему |

## 📝 Формат запроса к API

```json
{
  "query": "Как подать заявку на подключение?",
  "k": 10,
  "temperature": 0.8,
  "max_tokens": 2000,
  "min_score": 0.0,
  "session_id": null
}
```

## 📝 Формат фидбека

```json
{
  "query_id": "c653eca5-5015-47c1-80aa-0ddeff459d02",
  "feedback_type": "like",
  "rating": 5,
  "comment": "Отлично!"
}
```

## 📞 Поддержка

Для вопросов и предложений:
1. Проверьте документацию
2. Откройте Issue в репозитории
3. Обратитесь к CHANGELOG для истории изменений

---

**Последнее обновление:** 2026-03-22
