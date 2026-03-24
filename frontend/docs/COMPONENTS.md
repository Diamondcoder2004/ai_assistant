# 🧩 Справочник компонентов

## Быстрый старт

### Использование в Home.vue

```vue
<template>
  <div class="home">
    <Header />
    
    <div class="main-layout">
      <!-- Левая панель: параметры -->
      <aside class="sidebar-left">
        <SearchParamsPanel
          v-model="searchParams"
          @show-info="showInfoModal = 'settings'"
        />
      </aside>
      
      <!-- Чат -->
      <main class="chat-area">
        <ChatHeader
          :session-title="chatStore.currentSessionTitle"
          :is-loading="chatStore.isLoading"
          @new-chat="handleNewChat"
        />
        
        <ChatMessages
          :messages="chatStore.messages"
          :is-loading="chatStore.isLoading"
          :expanded-message-id="expandedMessageId"
          :feedbacks="chatStore.feedbacks"
          @toggle-sources="toggleSources"
          @feedback="handleFeedback"
          @open-star-rating="openStarRating"
        />
        
        <ChatInputArea
          v-model="newMessage"
          :is-loading="chatStore.isLoading"
          @send="sendMessage"
          @use-template="useTemplate"
        />
        
        <FaqSeqtion />
      </main>
      
      <!-- Правая панель: источники -->
      <SourcesPanel
        v-if="expandedMessage"
        :expanded-message="expandedMessage"
        @close="expandedMessage = null"
        @open-source="openSourceModal"
      />
    </div>
    
    <!-- Модальные окна -->
    <SourceDetailModal v-if="selectedSource" :source="selectedSource" @close="selectedSource = null" />
    <ParamsInfoModal v-if="showInfoModal === 'settings'" @close="showInfoModal = null" />
    <StarRatingModal v-if="showStarRating" @close="showStarRating = false" @submit="submitStarRating" />
  </div>
</template>
```

---

## SearchParamsPanel

### Пример с кастомными значениями

```vue
<template>
  <SearchParamsPanel
    :model-value="searchParams"
    @update:model-value="updateParam"
    @show-info="showHelp"
  />
</template>

<script setup>
import { ref } from 'vue'
import SearchParamsPanel from './chat/SearchParamsPanel.vue'

const searchParams = ref({
  k: 30,
  rerank_top_k: 3,
  temperature: 0.8,
  max_tokens: 2000,
  min_score: 0.0
})

function updateParam({ key, value }) {
  searchParams.value[key] = value
  console.log(`Параметр ${key} изменён на ${value}`)
}

function showHelp() {
  // Открыть модальное окно
}
</script>
```

### Валидация значений

Компонент автоматически валидирует значения:

| Параметр | Мин | Макс | Шаг | Тип |
|----------|-----|------|-----|-----|
| `k` | 5 | 50 | 1 | int |
| `rerank_top_k` | 1 | 10 | 1 | int |
| `temperature` | 0 | 1.5 | 0.1 | float |
| `max_tokens` | 500 | 4000 | 100 | int |
| `min_score` | 0 | 1 | 0.05 | float |

---

## ChatMessages

### Обработка событий

```vue
<template>
  <ChatMessages
    :messages="messages"
    :is-loading="isLoading"
    :expanded-message-id="expandedId"
    :feedbacks="feedbacks"
    @toggle-sources="handleToggleSources"
    @feedback="handleFeedback"
    @open-star-rating="handleStarRating"
  />
</template>

<script setup>
const messages = ref([
  {
    id: 1,
    role: 'user',
    content: 'Как подать заявку?',
    sessionId: 'abc-123',
    timestamp: new Date()
  },
  {
    id: 2,
    role: 'assistant',
    content: 'Для подачи заявки...',
    sources: [...],
    sessionId: 'abc-123',
    timestamp: new Date()
  }
])

function handleToggleSources(message) {
  console.log('Источники:', message.sources)
}

function handleFeedback(sessionId, type) {
  console.log(`Фидбек ${type} для ${sessionId}`)
}

function handleStarRating(sessionId) {
  console.log(`Открыть рейтинг для ${sessionId}`)
}
</script>
```

---

## ChatInputArea

### Кастомизация быстрых вопросов

```vue
<template>
  <ChatInputArea
    v-model="question"
    :is-loading="isLoading"
    :questions="customQuestions"
    @send="sendQuestion"
    @use-template="insertTemplate"
  />
</template>

<script setup>
const customQuestions = [
  { icon: '🔌', label: 'Подключение', text: 'Технологическое присоединение' },
  { icon: '📊', label: 'Тарифы', text: 'Тарифы на электроэнергию' },
  { icon: '📞', label: 'Контакты', text: 'Контакты службы поддержки' }
]

const question = ref('')
const isLoading = ref(false)

function sendQuestion() {
  // Отправка вопроса
}

function insertTemplate(text) {
  question.value = text
}
</script>
```

---

## SourcesPanel

### Условное отображение

```vue
<template>
  <!-- Показывать только если есть источники -->
  <SourcesPanel
    v-if="expandedMessage?.sources?.length > 0"
    :expanded-message="expandedMessage"
    @close="closeSources"
    @open-source="openSourceDetail"
  />
</template>

<script setup>
const expandedMessage = ref(null)

function closeSources() {
  expandedMessage.value = null
}

function openSourceDetail(source) {
  selectedSource.value = source
}
</script>
```

---

## Модальные окна

### Паттерн использования

```vue
<template>
  <!-- SourceDetailModal -->
  <SourceDetailModal
    v-if="selectedSource"
    :source="selectedSource"
    @close="selectedSource = null"
  />
  
  <!-- ParamsInfoModal -->
  <ParamsInfoModal
    v-if="showParamsInfo"
    @close="showParamsInfo = false"
  />
  
  <!-- StarRatingModal -->
  <StarRatingModal
    v-if="showStarModal"
    :selected-stars="selectedStars"
    @close="showStarModal = false"
    @submit="submitRating"
  />
</template>

<script setup>
const selectedSource = ref(null)
const showParamsInfo = ref(false)
const showStarModal = ref(false)
const selectedStars = ref(0)

function submitRating(rating) {
  console.log(`Рейтинг: ${rating}`)
  showStarModal.value = false
}
</script>
```

---

## Состояние (Pinia)

### Использование chatStore

```vue
<script setup>
import { useChatStore } from '@/stores/chatStore'

const chatStore = useChatStore()

// Отправка вопроса
await chatStore.sendQuestion('Как подключить?', {
  k: 30,
  rerank_top_k: 3,
  temperature: 0.8,
  max_tokens: 2000,
  min_score: 0.0
})

// Новый чат
chatStore.newChat()

// Загрузка истории
await chatStore.loadHistory(50)

// Фидбек
await chatStore.submitFeedback(sessionId, 'like')
await chatStore.submitFeedback(sessionId, 'star', 5)
await chatStore.removeFeedback(sessionId)
</script>
```

---

## Стили

### Переопределение тем

```css
/* Глобальные переменные */
:root {
  --chat-primary: #0066cc;
  --chat-primary-hover: #0052a3;
  --chat-bg: #f8f9fa;
  --chat-border: #e5e7eb;
}

/* Переопределение для тёмной темы */
.dark-theme {
  --chat-primary: #3b82f6;
  --chat-bg: #1f2937;
  --chat-border: #374151;
}
```

### Адаптивность

```css
/* Скрыть левую панель на мобильных */
@media (max-width: 768px) {
  .sidebar-left {
    display: none;
  }
}

/* Скрыть правую панель на планшетах */
@media (max-width: 992px) {
  .sidebar-right {
    display: none;
  }
}
```

---

## Лучшие практики

### 1. Валидация параметров
Всегда проверяйте диапазон значений перед отправкой на бэкенд.

### 2. Обработка ошибок
```javascript
try {
  await chatStore.sendQuestion(text, params)
} catch (err) {
  console.error('Ошибка:', err)
  alert('Не удалось отправить вопрос')
}
```

### 3. Дебаунс для поиска
```javascript
import { debounce } from 'lodash'

const searchHistory = debounce((query) => {
  // Поиск
}, 300)
```

### 4. Очистка памяти
```javascript
onUnmounted(() => {
  chatStore.newChat()
})
```
