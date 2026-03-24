# 📖 Документация Web Chat Bot

Добро пожаловать в документацию проекта BashkirEnergo Chat Bot.

## 🗂 Структура документации

| Документ | Описание |
|----------|----------|
| [ARCHITECTURE.md](./ARCHITECTURE.md) | 🏗 Архитектура проекта, компоненты, stores, API |
| [COMPONENTS.md](./COMPONENTS.md) | 🧩 Справочник компонентов с примерами |
| [CHANGELOG.md](./CHANGELOG.md) | 📝 История изменений проекта |

## 🚀 Быстрый старт

### Установка зависимостей
```bash
npm install
```

### Запуск разработки
```bash
npm run dev
```

### Сборка production
```bash
npm run build
```

## 📁 Структура проекта

```
web_chat_bot/
├── src/
│   ├── components/
│   │   ├── chat/              # Компоненты чата
│   │   │   ├── SearchParamsPanel.vue   # Параметры поиска
│   │   │   ├── ChatMessages.vue        # Сообщения
│   │   │   ├── ChatInputArea.vue       # Поле ввода
│   │   │   ├── ChatHeader.vue          # Шапка
│   │   │   ├── SourcesPanel.vue        # Источники
│   │   │   └── modals/                 # Модальные окна
│   │   ├── Header.vue
│   │   ├── Footer.vue
│   │   └── FaqSeqtion.vue
│   ├── views/
│   │   ├── Home.vue           # Главная (чат)
│   │   ├── History.vue        # История
│   │   ├── Login.vue
│   │   ├── Register.vue
│   │   └── Profile.vue
│   ├── stores/
│   │   ├── chatStore.js       # Состояние чата
│   │   └── authStore.js       # Аутентификация
│   ├── services/
│   │   └── supabase.js        # API клиент
│   └── router/
│       └── index.js           # Маршруты
├── docs/                      # Документация
│   ├── ARCHITECTURE.md
│   ├── COMPONENTS.md
│   ├── CHANGELOG.md
│   └── README.md              # Этот файл
├── package.json
└── README.md                  # Основная документация
```

## 🎯 Ключевые возможности

### 💬 Чат
- Streaming токенов в реальном времени
- Гибридный поиск (4 компонента)
- Источники с оценками релевантности
- Фидбек (лайк/дизлайк/звёзды)

### ⚙️ Параметры поиска
- Количество документов: 1–15 (рекомендуется: 8)
- Температура: 0–1.5 (рекомендуется: 0.7–0.8)
- Длина ответа (макс.): 500–4000 токенов (~375–3000 слов, рекомендуется: 2000)
- Порог сходства: 0–1 (рекомендуется: 0–0.2)

### 📜 История
- Просмотр всех чатов
- Поиск по вопросам и ответам
- Возобновление сессий

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

## 📚 Документация по компонентам

### SearchParamsPanel
Панель параметров с dual input (slider + number field).

**Пример:**
```vue
<SearchParamsPanel
  v-model="searchParams"
  @show-info="showHelp"
/>
```

### ChatMessages
Отображение сообщений с streaming поддержкой.

**Пример:**
```vue
<ChatMessages
  :messages="chatStore.messages"
  :is-loading="chatStore.isLoading"
  @toggle-sources="toggleSources"
  @feedback="handleFeedback"
/>
```

### ChatInputArea
Поле ввода с авто-увеличением высоты.

**Пример:**
```vue
<ChatInputArea
  v-model="question"
  :is-loading="isLoading"
  @send="sendMessage"
/>
```

## 🔌 API Endpoints

| Метод | Endpoint | Описание |
|-------|----------|----------|
| POST | `/query` | Обычный запрос |
| POST | `/query/stream` | Streaming (SSE) |
| GET | `/history?limit=50` | История |
| POST | `/feedback` | Создать фидбек |
| GET | `/feedback/{id}` | Получить фидбек |
| DELETE | `/feedback/{id}` | Удалить фидбек |

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
| Streaming не работает | Проверить `/query/stream` на backend |
| Параметры сбрасываются | Проверить валидацию диапазонов |
| JWT истёк | Перезайти в систему |

## 📞 Поддержка

Для вопросов и предложений:
1. Проверьте документацию
2. Откройте Issue в репозитории
3. Обратитесь к CHANGELOG для истории изменений

---

**Последнее обновление:** 2026-03-22
