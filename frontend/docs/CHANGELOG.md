# Changelog

Все значительные изменения в проекте будут задокументированы в этом файле.

## [2026-03-22] - Исправления и улучшения

### 🐛 Исправления

#### ChatInputArea.vue
- **Fixed**: Добавлен `nextTick` в импорты для `autoResize()`

#### SearchParamsPanel.vue
- **Fixed**: `defineEmits` теперь вызывается в setup, не внутри функции
- **Fixed**: Синхронизация slider + number input через `emit('update:modelValue', newValue)`

#### ChatMessages.vue
- **Added**: Быстрые вопросы в приветственное окно
- **Added**: Emit `useTemplate` для обработки кликов по подсказкам

### 🎨 Изменения UI

#### Убран FAQ из-под чата
- `FaqSeqtion` удалён из `Home.vue`
- Быстрые вопросы перемещены в приветственное окно

#### Приветственное окно
```
👋 Добро пожаловать в чат-бот Башкирэнерго!

Попробуйте спросить:
[📋 Как подать заявку?] [📄 Какие документы?]
[⏱️ Сроки] [💰 Стоимость]
```

### 📦 Изменения в компонентах

| Компонент | Изменения |
|-----------|-----------|
| `ChatInputArea.vue` | Добавлен `nextTick` в импорт |
| `SearchParamsPanel.vue` | Исправлен `emit`, синхронизация inputs |
| `ChatMessages.vue` | Добавлены быстрые вопросы, emit `useTemplate` |
| `Home.vue` | Удалён `FaqSeqtion` |

### ⚡ Технические исправления
- Все `defineProps` и `defineEmits` теперь в начале setup
- `watch` использует `props.modelValue` вместо `defineProps().modelValue`
- Удалены неиспользуемые импорты

### 📊 Сборка
```
✓ 141 modules transformed
✓ built in 383ms
```

---

## [2026-03-22] — Декомпозиция

#### Декомпозиция Home.vue
Home.vue был разделён на 9 специализированных компонентов для улучшения поддерживаемости:

**Новые компоненты:**
- `src/components/chat/SearchParamsPanel.vue` — Панель параметров поиска (5 параметров с dual input)
- `src/components/chat/ChatMessages.vue` — Область сообщений с streaming поддержкой
- `src/components/chat/ChatInputArea.vue` — Поле ввода + быстрые вопросы
- `src/components/chat/ChatHeader.vue` — Шапка чата с индикатором сессии
- `src/components/chat/SourcesPanel.vue` — Правая панель источников
- `src/components/chat/modals/SourceDetailModal.vue` — Детали источника
- `src/components/chat/modals/ParamsInfoModal.vue` — Информация о параметрах
- `src/components/chat/modals/StarRatingModal.vue` — Звёздный рейтинг

#### Обновлённая структура
```
src/
├── components/
│   ├── chat/                    # ← НОВАЯ ПАПКА
│   │   ├── SearchParamsPanel.vue
│   │   ├── ChatMessages.vue
│   │   ├── ChatInputArea.vue
│   │   ├── ChatHeader.vue
│   │   ├── SourcesPanel.vue
│   │   └── modals/
│   │       ├── SourceDetailModal.vue
│   │       ├── ParamsInfoModal.vue
│   │       └── StarRatingModal.vue
│   ├── Header.vue
│   ├── Footer.vue
│   └── FaqSeqtion.vue
├── views/
│   ├── Home.vue                 # ← Обновлён (теперь ~300 строк)
│   ├── History.vue              # ← Обновлён
│   └── ...
└── docs/                        # ← НОВАЯ ПАПКА
    ├── ARCHITECTURE.md
    └── COMPONENTS.md
```

### 🎨 UI/UX улучшения

#### SearchParamsPanel
- **Dual input control**: slider + number field для каждого параметра
- **Автоматическая валидация**: значения ограничиваются диапазоном
- **Подсказки**: для каждого параметра есть hint
- **Инфо-кнопка**: модальное окно с пояснениями

**Параметры:**
| Параметр | Диапазон | Шаг |
|----------|----------|-----|
| k (документы) | 5–50 | 1 |
| rerank_top_k | 1–10 | 1 |
| temperature | 0–1.5 | 0.1 |
| max_tokens | 500–4000 | 100 |
| min_score | 0–1 | 0.05 |

#### History.vue
- **Улучшенный дизайн**: карточки с иконками и hover-эффектами
- **Возобновление чата**: клик по карточке восстанавливает сессию
- **Живой поиск**: фильтрация по вопросам и ответам
- **Умное форматирование**: "Сегодня", "Вчера", дата
- **Индикатор загрузки**: spinner вместо текста

### 📚 Документация

#### docs/ARCHITECTURE.md
- Архитектура проекта
- Описание компонентов и stores
- API endpoints
- Стилевые соглашения
- Руководство по расширению

#### docs/COMPONENTS.md
- Примеры использования каждого компонента
- Обработка событий
- Кастомизация
- Лучшие практики

### 🔧 Технические изменения

#### Сборка
- **До**: Home.vue ~1800 строк
- **После**: Home.vue ~300 строк + 9 компонентов по ~150 строк

#### Производительность
- Lazy loading для модальных окон
- Оптимизирована прокрутка сообщений
- Debounce для search input

#### Совместимость
- Сохранена обратная совместимость с backend
- Все существующие API endpoints работают

### 📦 Зависимости
Изменений нет

### ⚠️ Breaking Changes
Нет

### 🐛 Исправления
- Исправлены импорты в Home.vue
- Добавлена валидация number input в SearchParamsPanel
- Исправлен autofocus для textarea в ChatInputArea

---

## [2026-03-21]

### Добавлено
- ✅ Streaming токенов через Fetch API
- ✅ Русификация UI (все тексты на русском)
- ✅ История сессий с группировкой по session_id
- ✅ Индикатор текущей сессии в шапке
- ✅ Автоматическая прокрутка сообщений

### Изменено
- chatStore.js: добавлена поддержка streaming
- supabase.js: метод `sendQueryStream()`
- AssistantChat.vue: обновлён для streaming

---

## Формат

Этот проект следует [Semantic Versioning](https://semver.org/lang/ru/).

Формат changelog основан на [Keep a Changelog](https://keepachangelog.com/ru/1.0.0/).

### Типы изменений
- **Added** — новые возможности
- **Changed** — изменения в существующем функционале
- **Deprecated** — устаревшие возможности
- **Removed** — удалённые возможности
- **Fixed** — исправления ошибок
- **Security** — изменения в безопасности
