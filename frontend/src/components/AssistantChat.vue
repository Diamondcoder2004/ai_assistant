<template>
  <div class="fixed bottom-6 right-6 z-50">
    <!-- Кнопка открытия чата -->
    <button
      v-if="!isOpen"
      @click="openChat"
      class="bg-primary text-white rounded-full w-16 h-16 flex items-center justify-center shadow-lg hover:shadow-xl transition-shadow"
      aria-label="Открыть ассистент"
    >
      <svg class="w-8 h-8" fill="currentColor" viewBox="0 0 20 20">
        <path fill-rule="evenodd" d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z" clip-rule="evenodd"/>
      </svg>
    </button>

    <!-- Окно чата -->
    <div
      v-else
      class="bg-white rounded-lg shadow-2xl w-96 h-[600px] flex flex-col"
    >
      <!-- Заголовок -->
      <div class="bg-primary text-white p-4 rounded-t-lg flex justify-between items-center">
        <div class="flex items-center gap-2">
          <span>🤖</span>
          <h3 class="font-semibold">Ассистент Башкирэнерго</h3>
        </div>
        <button @click="closeChat" class="text-white hover:text-gray-200">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
          </svg>
        </button>
      </div>

      <!-- История сообщений -->
      <div ref="messagesContainer" class="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
        <!-- Приветствие -->
        <div v-if="messages.length === 0" class="text-center py-8">
          <div class="text-4xl mb-2">👋</div>
          <p class="text-sm text-gray-600">Здравствуйте! Задайте вопрос о подключении к электросетям.</p>
        </div>

        <div v-for="(message, index) in messages" :key="index">
          <!-- Сообщение пользователя -->
          <div v-if="message.role === 'user'" class="flex justify-end mb-2">
            <div class="bg-primary text-white rounded-lg rounded-tr-none p-3 max-w-[80%] shadow-sm">
              {{ message.content }}
            </div>
          </div>

          <!-- Сообщение ассистента -->
          <div v-else class="flex justify-start mb-2">
            <div class="bg-white text-gray-800 rounded-lg rounded-tl-none p-3 max-w-[85%] shadow-sm border border-gray-200">
              <!-- Индикатор streaming -->
              <div v-if="message.content === '' && chatStore.isLoading" class="typing-indicator">
                <span class="dot"></span>
                <span class="dot"></span>
                <span class="dot"></span>
              </div>
              <div v-else class="whitespace-pre-wrap">{{ message.content }}</div>

              <!-- Источники -->
              <div v-if="message.sources && message.sources.length > 0" class="mt-3 pt-3 border-t border-gray-200">
                <p class="text-xs font-semibold text-gray-600 mb-2 uppercase tracking-wide">Источники:</p>
                <div class="space-y-2">
                  <div
                    v-for="(source, i) in message.sources"
                    :key="i"
                    class="source-card text-xs bg-blue-50 border border-blue-200 rounded-md p-2 hover:bg-blue-100 transition-colors cursor-pointer"
                    @click="showSourceDetails(source)"
                  >
                    <div class="flex items-start gap-2">
                      <span class="source-number flex-shrink-0 w-5 h-5 bg-primary text-white text-xs rounded-full flex items-center justify-center font-bold">
                        {{ i + 1 }}
                      </span>
                      <div class="flex-1 min-w-0">
                        <div class="font-medium text-gray-800 truncate" :title="source.filename">{{ source.filename || 'Документ' }}</div>
                        <div v-if="source.breadcrumbs" class="text-gray-500 text-xs mt-0.5 truncate">{{ source.breadcrumbs }}</div>
                        <div v-if="source.summary" class="text-gray-600 mt-1 line-clamp-2">{{ truncateText(source.summary, 150) }}</div>
                        <div class="flex gap-2 mt-1">
                          <span v-if="source.score_hybrid" class="inline-flex items-center px-1.5 py-0.5 bg-green-100 text-green-700 text-xs rounded">
                            {{ (source.score_hybrid * 100).toFixed(0) }}%
                          </span>
                          <span v-if="source.score_rerank" class="inline-flex items-center px-1.5 py-0.5 bg-purple-100 text-purple-700 text-xs rounded">
                            {{ (source.score_rerank * 100).toFixed(0) }}%
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Фидбек кнопки -->
              <div v-if="message.sessionId" class="mt-3 pt-2 border-t border-gray-200 flex items-center gap-2">
                <span class="text-xs text-gray-500">Оцените:</span>
                <button
                  @click="handleFeedback(message, 'like')"
                  class="feedback-btn"
                  :class="{ 'active': getFeedbackStatus(message) === 'like' }"
                  title="Полезно"
                >
                  👍
                </button>
                <button
                  @click="handleFeedback(message, 'dislike')"
                  class="feedback-btn"
                  :class="{ 'active': getFeedbackStatus(message) === 'dislike' }"
                  title="Не полезно"
                >
                  👎
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Индикатор загрузки -->
        <div v-if="isLoading" class="flex justify-start">
          <div class="bg-white border border-gray-200 rounded-lg rounded-tl-none p-3 shadow-sm">
            <div class="flex space-x-1">
              <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
              <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.1s"></div>
              <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- Поле ввода -->
      <div class="border-t p-4 bg-white">
        <form @submit.prevent="sendMessage" class="flex space-x-2">
          <input
            v-model="inputMessage"
            type="text"
            placeholder="Задайте вопрос о подключении..."
            class="flex-1 border rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary"
            :disabled="isLoading"
          />
          <button
            type="submit"
            class="bg-primary text-white px-4 py-2 rounded-lg hover:bg-secondary transition-colors disabled:opacity-50"
            :disabled="isLoading || !inputMessage.trim()"
          >
            Отправить
          </button>
        </form>
      </div>
    </div>

    <!-- Модальное окно для деталей источника -->
    <div v-if="selectedSource" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" @click="selectedSource = null">
      <div class="bg-white rounded-lg max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto" @click.stop>
        <div class="p-4 border-b flex justify-between items-center">
          <h4 class="font-semibold text-lg">Детали источника</h4>
          <button @click="selectedSource = null" class="text-gray-500 hover:text-gray-700">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>
        <div class="p-4">
          <div class="mb-3">
            <span class="text-sm font-medium text-gray-500">Файл:</span>
            <p class="text-base">{{ selectedSource.filename || 'Не указано' }}</p>
          </div>
          <div v-if="selectedSource.breadcrumbs" class="mb-3">
            <span class="text-sm font-medium text-gray-500">Раздел:</span>
            <p class="text-base">{{ selectedSource.breadcrumbs }}</p>
          </div>
          <div v-if="selectedSource.summary" class="mb-3">
            <span class="text-sm font-medium text-gray-500">Содержание:</span>
            <p class="text-base whitespace-pre-wrap">{{ selectedSource.summary }}</p>
          </div>
          <div class="grid grid-cols-2 gap-3 mb-3">
            <div v-if="selectedSource.score_hybrid" class="bg-green-50 p-2 rounded">
              <span class="text-xs text-gray-500">Hybrid Score:</span>
              <p class="text-lg font-semibold text-green-700">{{ (selectedSource.score_hybrid * 100).toFixed(2) }}%</p>
            </div>
            <div v-if="selectedSource.score_rerank" class="bg-purple-50 p-2 rounded">
              <span class="text-xs text-gray-500">Rerank Score:</span>
              <p class="text-lg font-semibold text-purple-700">{{ (selectedSource.score_rerank * 100).toFixed(2) }}%</p>
            </div>
          </div>
          <div v-if="selectedSource.chunk_id" class="mb-3">
            <span class="text-sm font-medium text-gray-500">Chunk ID:</span>
            <p class="text-xs font-mono bg-gray-100 p-1 rounded">{{ selectedSource.chunk_id }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, watch, computed } from 'vue'
import { useChatStore } from '../stores/chatStore'

const chatStore = useChatStore()

const isOpen = ref(false)
const inputMessage = ref('')
const messagesContainer = ref(null)
const selectedSource = ref(null)

// Получаем сообщения из store
const messages = computed(() => chatStore.messages)
const isLoading = computed(() => chatStore.isLoading)

// Приветственное сообщение
onMounted(() => {
  if (messages.value.length === 0) {
    chatStore.addMessage('assistant', 'Здравствуйте! Я ассистент Башкирэнерго. Задайте мне вопрос о технологическом присоединении, тарифах или услугах компании.')
  }
})

function openChat() {
  isOpen.value = true
}

function closeChat() {
  isOpen.value = false
}

async function sendMessage() {
  if (!inputMessage.value.trim() || isLoading.value) return

  const userMessage = inputMessage.value.trim()
  inputMessage.value = ''

  try {
    await chatStore.sendQuestion(userMessage)
  } catch (error) {
    console.error('Send message error:', error)
  } finally {
    scrollToBottom()
  }
}

// Обработка фидбека (лайк/дизлайк)
async function handleFeedback(message, type) {
  const currentStatus = getFeedbackStatus(message)
  const chatId = message.sessionId

  if (!chatId) {
    console.warn('No sessionId available for feedback')
    return
  }

  try {
    if (currentStatus === type) {
      await chatStore.removeFeedback(chatId)
    } else {
      await chatStore.submitFeedback(chatId, type)
    }
  } catch (err) {
    console.error('Feedback error:', err)
  }
}

// Получить статус фидбека для сообщения
function getFeedbackStatus(message) {
  const chatId = message.sessionId
  if (!chatId) return null

  const feedback = chatStore.feedbacks[chatId]
  if (!feedback) return null

  return feedback.feedback_type
}

// Показать детали источника
function showSourceDetails(source) {
  selectedSource.value = source
}

// Обрезка текста
function truncateText(text, maxLength) {
  if (!text) return ''
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}

function scrollToBottom() {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

// Автоматическая прокрутка при новых сообщениях
watch(messages, () => {
  scrollToBottom()
}, { deep: true })
</script>

<style scoped>
.feedback-btn {
  padding: 4px 8px;
  border-radius: 4px;
  border: 1px solid #e5e7eb;
  background: white;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 18px;
}

.feedback-btn:hover {
  background: #f3f4f6;
  transform: scale(1.1);
}

.feedback-btn.active {
  background: #dbeafe;
  border-color: #3b82f6;
  transform: scale(1.1);
}

.source-number {
  width: 24px;
  height: 24px;
  background: #0066cc;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 12px;
  flex-shrink: 0;
}

.source-card {
  transition: all 0.2s;
}

.source-card:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* Индикатор набора текста */
.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 4px 0;
}

.typing-indicator .dot {
  width: 8px;
  height: 8px;
  background: #9ca3af;
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out;
}

.typing-indicator .dot:nth-child(1) { animation-delay: -0.32s; }
.typing-indicator .dot:nth-child(2) { animation-delay: -0.16s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}
</style>
