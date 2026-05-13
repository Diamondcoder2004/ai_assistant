date: 2026-05-13
topic: "Unified Sidebar — объединение панели параметров и источников в один сайдбар"
status: draft

## Problem Statement

Текущий трёхколоночный layout (левая панель параметров | чат | правая панель источников) заставляет пользователя скроллить туда-сюда: когда скроллишь чат вниз и хочешь увидеть источники для нового ответа, приходится либо мотать наверх (где «привязаны» параметры), либо переключать внимание на правую колонку, которая отображается только для конкретного развёрнутого сообщения.

**Ключевая боль:** источники жёстко зафиксированы в правой колонке, но они не синхронизированы с позицией скролла в чате. Chat и источники должны быть раздельными, но удобно доступными.

## Constraints

- Никаких новых зависимостей в package.json
- chatStore, маршруты, модалки — без изменений
- Компоненты SearchParamsPanel и SourcesPanel сохраняют свою логику
- Адаптивность под мобильные (sidebar скрывается на < 768px)
- Сохранить все существующие фичи: фидбек, streaming, quick questions, hotkeys

## Approach

Переходим от трёхколоночного layout к двухколоночному:

```
ДО:
┌──────────┬────────────────────────────┬──────────────┐
│  320px   │         flex:1             │    400px     │
│ Параметры│         Чат                │  Источники   │
│ (sticky) │      (scrollable)          │  (условно)   │
└──────────┴────────────────────────────┴──────────────┘

ПОСЛЕ:
┌───────────────────────────────────────┬──────────────┐
│               flex:1                  │    380px     │
│               Чат                     │  Единый      │
│          (scrollable)                 │  сайдбар     │
│                                       │              │
│  ChatHeader                           │  ⚙️ Параметры│
│  ChatMessages                         │  [Кратко]    │
│   ┌── вопрос ───────────────────┐    │  [Стандартно]│
│   │ ...                          │    │  [Подробно]  │
│   └──────────────────────────────┘    │              │
│   ┌── ответ ─────────────────────┐   │  ──────────  │
│   │ ... [Показать источники]     │   │  📚 Источники│
│   │ [👍][👎][⭐]                 │   │  ┌── src ─┐ │
│   └──────────────────────────────┘   │  │ card    │ │
│                                       │  └─────────┘ │
│  ChatInputArea                        │              │
└───────────────────────────────────────┴──────────────┘
```

**Единый сайдбар** содержит оба раздела: параметры (сворачиваемые) сверху и источники для выбранного ответа снизу.

## Components

### Home.vue (изменения)

- **Удаляем** `<aside class="sidebar-left">` (SearchParamsPanel) и условный `<SourcesPanel>` из основного потока
- **Добавляем** `unified-sidebar` с двумя collapsible секциями
- **Добавляем** ref: `showSidebar` (default: false), `showParams` (default: true)
- **Логика toggleSources(message):** устанавливает `expandedMessage = message`, включает `showSidebar = true`
- **Кнопка закрытия:** крестик в хедере сайдбара → `showSidebar = false`, `expandedMessage = null`
- **Кнопка открытия:** можно не добавлять отдельно — открывается автоматически при клике «Показать источники»

### SourcesPanel.vue (минимальные изменения)

- Принимает опциональный prop `:compact="true"` для работы внутри unified sidebar
- В compact-режиме: убирает внешний `<aside>`, свой sticky header и кнопку закрытия (всё это уже даёт Home.vue)

### SearchParamsPanel.vue (без изменений)

Вписывается в 380px как есть. Только если нужно — убрать внешний `border-radius` и `background`, т.к. контейнер уже есть.

## Data Flow

```
ChatMessages.vue
  @toggleSources(message)
    → Home.vue.handleToggleSources(message)
      → expandedMessage = message
      → showSidebar = true
      → SourcesPanel получает expandedMessage через проп

Sidebar close (✕ button)
  → showSidebar = false
  → expandedMessage = null (очищаем выбор)

Scroll-to-source (из ChatMessages)
  → Home.vue.handleScrollToSource({ sourceNum, messageId })
    → открывает sidebar + показывает источники
    → скроллит к нужному source card внутри сайдбара
```

## Error Handling

- Если expandedMessage есть, но у него нет sources → показываем заглушку «Нет источников для этого ответа»
- Если sidebar открыт, а сообщение было удалено из стора → просто очищаем expandedMessage

## Testing Strategy

- Визуально: проверить, что sidebar открывается/закрывается по клику на «Показать источники»
- Визуально: проверить, что секция параметров сворачивается/разворачивается
- Визуально: проверить адаптивность — sidebar скрывается на мобильных
- Smoke test: send message → show sources → close sidebar → send another message → show sources again

## Files to Modify

| File | Change |
|------|--------|
| `frontend/src/views/Home.vue` | Замена трёхколоночного layout на двухколоночный с unified sidebar |
| `frontend/src/components/chat/SourcesPanel.vue` | Добавить prop `compact` для работы внутри сайдбара |

## Open Questions

- Нужна ли отдельная кнопка для открытия сайдбара без клика на источники? Пока нет — сайдбар открывается только когда есть источники для показа.
