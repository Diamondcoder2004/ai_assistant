---
date: 2026-05-01
topic: "Compact Search Params Panel"
status: validated
---

# Compact Search Params Panel — Design

## Problem Statement

Текущая `SearchParamsPanel` показывает **4 технических параметра** с ползунками: количество документов, температура, длина ответа, порог сходства. Это занимает ~20% ширины экрана и создаёт «лабораторный» вид. Для клиентов Башкирэнерго (ФЛ, ИП, ЮЛ) это отпугивает — они не знают, что такое «температура 0.8».

## Constraints

- **Vue 3 Composition API**, Pinia, `v-model` с объектом `{ k, temperature, max_tokens, min_score }`
- **Backward compatibility** — `Home.vue` использует `searchParams` ref, API не меняется
- **Mobile-first** — на `< 768px` левая панель уже проблемна
- **Пресеты** должны соответствовать домену (технологическое присоединение)

## Approach

**Два режима: Compact (default) и Expanded.**

| Режим | Что видит пользователь | Когда используется |
|---|---|---|
| **Compact** | 1 строка: «Поиск: стандартный • 10 док.» + кнопка ⚙️ + пресеты «Кратко / Стандартно / Подробно» | Всегда по умолчанию |
| **Expanded** | Все 4 параметра с ползунками, как сейчас, но в выпадающей/overlay панели | По клику на ⚙️ или «Custom» |

### Пресеты

| Пресет | `temperature` | `max_tokens` | `k` | Описание для пользователя |
|---|---|---|---|---|
| **Кратко** | 0.3 | 800 | 5 | Короткий ответ, только факты |
| **Стандартно** | 0.8 | 2000 | 10 | Баланс точности и объёма |
| **Подробно** | 1.0 | 4000 | 15 | Развёрнутый ответ с деталями |

### Ключевые решения

- Пресеты показываем **chip-кнопками** над полем ввода, а не в боковой панели — ближе к действию
- При ручном изменении параметра в Expanded → активный пресет сбрасывается в «Custom»
- Если ручные значения совпадают с пресетом → подсвечиваем этот пресет
- `min_score` убираем из Compact вообще — это expert-only параметр, оставляем только в Expanded

## Architecture

```
Home.vue
├── sidebar-left
│   └── SearchParamsPanel.vue  (compact/expanded toggle)
│       ├── SearchParamsCompact.vue   (индикатор + кнопка ⚙️)
│       └── SearchParamsExpanded.vue  (все 4 параметра, overlay)
└── chat-area
    └── ChatInputArea.vue
        └── PresetSelector.vue        (chip-кнопки пресетов)
```

## Components

| Компонент | Назначение |
|---|---|
| `SearchParamsPanel.vue` | Корневой. Управляет compact/expanded state, рендерит либо Compact, либо Expanded |
| `SearchParamsCompact.vue` | Одна строка-индикатор + кнопка «⚙️ Настроить» |
| `PresetSelector.vue` | Горизонтальный ряд chip-кнопок «Кратко / Стандартно / Подробно / Custom» |
| `SearchParamsExpanded.vue` | Вынесенная текущая логика с 4 параметрами и ползунками |

## Data Flow

```
User clicks "Подробно" preset
  → PresetSelector emits { temperature: 1.0, max_tokens: 4000, k: 15 }
  → SearchParamsPanel merges with existing modelValue (min_score preserved)
  → emits update:modelValue to Home.vue
  → Next chat query uses new params

User clicks "⚙️ Настроить"
  → SearchParamsPanel toggles isExpanded = true
  → Renders SearchParamsExpanded overlay (desktop: flyout, mobile: bottom sheet)

User drags slider in Expanded
  → SearchParamsExpanded emits update:modelValue
  → SearchParamsPanel checks if values match any preset
  → If no match → informs PresetSelector to show "Custom" active
```

## Mobile Behavior

- **Compact view** — chip-пресеты переносятся на новую строку под полем ввода (рядом с быстрыми вопросами)
- **Expanded view** — открывается как **bottom sheet** (`position: fixed; bottom: 0`) на весь экран, закрывается по «Готово» или свайпу вниз

## Error Handling

- Пресет-значения валидированы теми же `min/max/step` правилами, что и сейчас
- Ручной ввод в Expanded mode → та же валидация (`clamp` + `round`)
- Если `min_score` скрыт из Compact — он сохраняет текущее значение (default 0.0), не сбрасывается

## Testing Strategy

- **Unit:** `PresetSelector` emits правильный объект для каждого пресета
- **Unit:** при ручном изменении `temperature` → активный пресет становится «Custom»
- **E2E:** mobile bottom sheet открывается/закрывается, параметры применяются к запросу
- **E2E:** переключение пресета → следующий ответ использует новые `max_tokens`

## Open Questions

- Нужен ли пресет «Только из документов» (temperature 0, высокий min_score)? — можно добавить позже по фидбеку.
