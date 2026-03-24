# 📚 Документация проекта Web Chat Bot

## 🏗 Архитектура проекта

### Структура компонентов

```
src/
├── components/
│   ├── chat/                    # Компоненты чата (декомпозированные)
│   │   ├── SearchParamsPanel.vue    # Панель параметров поиска
│   │   ├── ChatMessages.vue         # Область сообщений
│   │   ├── ChatInputArea.vue        # Поле ввода и быстрые вопросы
│   │   ├── ChatHeader.vue           # Шапка чата
│   │   ├── SourcesPanel.vue         # Панель источников (правая)
│   │   └── modals/                  # Модальные окна
│   │       ├── SourceDetailModal.vue    # Детали источника
│   │       ├── ParamsInfoModal.vue      # Информация о параметрах
│   │       └── StarRatingModal.vue      # Звёздный рейтинг
│   ├── Header.vue
│   ├── Footer.vue
│   └── FaqSeqtion.vue
├── views/
│   ├── Home.vue                 # Главная страница чата
│   ├── History.vue              # История чатов
│   ├── Login.vue                # Вход
│   ├── Register.vue             # Регистрация
│   └── Profile.vue              # Профиль
└── stores/
    ├── chatStore.js             # Состояние чата
    └── authStore.js             # Аутентификация
```

---

## 🧩 Компоненты чата

### SearchParamsPanel.vue

**Назначение:** Панель параметров поиска с dual input (slider + number field)

**Props:**
| Prop | Тип | Описание |
|------|-----|----------|
| `modelValue` | `Object` | Объект с параметрами: `{ k, rerank_top_k, temperature, max_tokens, min_score }` |

**Events:**
| Event | Payload | Описание |
|-------|---------|----------|
| `update:modelValue` | `{ key, value }` | Обновление параметра |
| `showInfo` | — | Показать информацию о параметрах |

**Валидация:**
- `k`: 5–50 (целое)
- `rerank_top_k`: 1–10 (целое)
- `temperature`: 0–1.5 (шаг 0.1)
- `max_tokens`: 500–4000 (шаг 100)
- `min_score`: 0–1 (шаг 0.05)

---

### ChatMessages.vue

**Назначение:** Отображение сообщений с поддержкой streaming

**Props:**
| Prop | Тип | Описание |
|------|-----|----------|
| `messages` | `Array` | Массив сообщений |
| `isLoading` | `Boolean` | Индикатор загрузки |
| `expandedMessageId` | `String|Number` | ID развёрнутого сообщения |
| `feedbacks` | `Object` | Объект фидбека |

**Events:**
| Event | Payload | Описание |
|-------|---------|----------|
| `toggleSources` | `message` | Показать/скрыть источники |
| `feedback` | `(sessionId, type)` | Отправить фидбек |
| `openStarRating` | `sessionId` | Открыть звёздный рейтинг |

**Структура сообщения:**
```javascript
{
  id: Number,
  role: 'user' | 'assistant',
  content: String,
  sources: Array,
  sessionId: String,
  timestamp: Date
}
```

---

### ChatInputArea.vue

**Назначение:** Поле ввода с авто-увеличением высоты и быстрые вопросы

**Props:**
| Prop | Тип | Описание |
|------|-----|----------|
| `modelValue` | `String` | Текст вопроса |
| `isLoading` | `Boolean` | Индикатор загрузки |
| `questions` | `Array` | Быстрые вопросы |

**Events:**
| Event | Payload | Описание |
|-------|---------|----------|
| `update:modelValue` | `String` | Обновление текста |
| `send` | — | Отправка вопроса |
| `useTemplate` | `String` | Использование шаблона |

---

### ChatHeader.vue

**Назначение:** Шапка чата с индикатором сессии и кнопкой "Новый чат"

**Props:**
| Prop | Тип | Описание |
|------|-----|----------|
| `sessionTitle` | `String` | Заголовок текущей сессии |
| `isLoading` | `Boolean` | Индикатор загрузки |

**Events:**
| Event | Payload | Описание |
|-------|---------|----------|
| `newChat` | — | Начать новый чат |

---

### SourcesPanel.vue

**Назначение:** Правая панель с источниками ответа

**Props:**
| Prop | Тип | Описание |
|------|-----|----------|
| `expandedMessage` | `Object` | Сообщение с источниками |

**Events:**
| Event | Payload | Описание |
|-------|---------|----------|
| `close` | — | Закрыть панель |
| `openSource` | `source` | Открыть детали источника |

---

## 🔧 Модальные окна

### SourceDetailModal.vue
Детальная информация об источнике (файл, раздел, оценки релевантности)

### ParamsInfoModal.vue
Информация о параметрах поиска с пояснениями

### StarRatingModal.vue
Модальное окно для оценки ответа звёздами (1–5)

---

## 📦 Состояние (Pinia Stores)

### chatStore.js

**State:**
```javascript
{
  messages: [],           // Текущие сообщения
  isLoading: false,       // Индикатор загрузки
  error: null,            // Ошибка
  history: [],            // История чатов
  sessionId: null,        // ID текущей сессии
  feedbacks: {},          // Фидбек по сессиям
  chatSessions: [],       // Список сессий
  currentSessionTitle: '' // Заголовок сессии
}
```

**Actions:**
| Action | Params | Описание |
|--------|--------|----------|
| `sendQuestion` | `(question, parameters)` | Отправить вопрос с streaming |
| `newChat` | — | Начать новый чат |
| `loadSession` | `session` | Загрузить сессию |
| `loadHistory` | `limit` | Загрузить историю |
| `submitFeedback` | `(chatId, type, rating)` | Отправить фидбек |
| `removeFeedback` | `chatId` | Удалить фидбек |

---

## 🎨 Стилевые соглашения

### Цветовая палитра
```css
--primary: #0066cc;       /* Основной синий */
--primary-hover: #0052a3; /* Тёмно-синий */
--background: #f8f9fa;    /* Светлый фон */
--border: #e5e7eb;        /* Границы */
--text: #1f2937;          /* Текст */
--text-secondary: #6b7280; /* Вторичный текст */
```

### Breakpoints
- Mobile: < 768px
- Tablet: 768–992px
- Desktop: 992–1200px
- Large: > 1200px

---

## 🚀 API Endpoints

### FastAPI Backend

| Метод | Endpoint | Описание |
|-------|----------|----------|
| `POST` | `/query` | Обычный запрос |
| `POST` | `/query/stream` | Streaming запрос (SSE) |
| `GET` | `/history` | Получить историю |
| `POST` | `/feedback` | Создать фидбек |
| `GET` | `/feedback/{chat_id}` | Получить фидбек |
| `DELETE` | `/feedback/{chat_id}` | Удалить фидбек |

### Формат streaming ответа
```
data: {"token": "Часть "}
data: {"token": "ответа "}
data: {"sources": [...], "session_id": "..."}
data: [DONE]
```

---

## 📝 Руководство по расширению

### Добавление нового параметра поиска

1. Обновить `chatStore.js`:
```javascript
const searchParams = ref({
  // ... существующие
  new_param: 0.5  // Новый параметр
})
```

2. Добавить в `SearchParamsPanel.vue`:
```vue
<div class="param-row">
  <div class="param-header">
    <label>Название параметра</label>
    <input type="number" ... />
  </div>
  <input type="range" ... />
  <span class="param-hint">Подсказка</span>
</div>
```

3. Обновить `ParamsInfoModal.vue` с описанием

### Добавление нового типа фидбека

1. Обновить `chatStore.submitFeedback()`
2. Добавить кнопку в `ChatMessages.vue`
3. Обновить backend endpoint

---

## 🐛 Отладка

### Логирование
```javascript
// Включить debug режим
localStorage.setItem('DEBUG', 'chat')

// В console.log добавить:
console.log('[CHAT]', data)
```

### Частые проблемы

| Проблема | Решение |
|----------|---------|
| Streaming не работает | Проверить endpoint `/query/stream` на бэкенде |
| Параметры не сохраняются | Проверить валидацию в `SearchParamsPanel.vue` |
| Фидбек не отправляется | Проверить JWT токен в `supabase.js` |

---

## 📄 Changelog

### 2026-03-22
- ✅ Декомпозиция `Home.vue` на 6 компонентов
- ✅ Dual input для параметров (slider + number field)
- ✅ Улучшенная валидация параметров
- ✅ Обновлённый `History.vue` с возобновлением чата
- ✅ Создана документация в `docs/`

### 2026-03-21
- ✅ Streaming токенов через Fetch API
- ✅ Русификация UI
- ✅ История сессий с группировкой
