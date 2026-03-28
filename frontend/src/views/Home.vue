<template>
  <div class="home">
    <Header />

    <div class="main-layout">
      <!-- Левая колонка: параметры поиска -->
      <aside class="sidebar-left">
        <SearchParamsPanel
          v-model="searchParams"
          @show-info="showInfoModal = 'settings'"
        />
      </aside>

      <!-- Основная область чата -->
      <main class="chat-area">
        <!-- Шапка чата -->
        <ChatHeader
          :session-title="chatStore.currentSessionTitle"
          :is-loading="chatStore.isLoading"
          @new-chat="handleNewChat"
        />

        <!-- Сообщения -->
        <ChatMessages
          :messages="chatStore.messages"
          :is-loading="chatStore.isLoading"
          :expanded-message-id="expandedMessageId"
          :feedbacks="chatStore.feedbacks"
          @toggle-sources="toggleSources"
          @feedback="handleFeedback"
          @open-star-rating="openStarRating"
          @scroll-to-source="handleScrollToSource"
        />

        <!-- Поле ввода и быстрые вопросы -->
        <ChatInputArea
          v-model="newMessage"
          :is-loading="chatStore.isLoading"
          @send="sendMessage"
          @use-template="handleUseTemplate"
        />
      </main>

      <!-- Правая колонка: источники -->
      <SourcesPanel
        v-if="expandedMessage && showSourcesPanel"
        :expanded-message="expandedMessage"
        @close="expandedMessage = null; showSourcesPanel = false"
        @open-source="openSourceModal"
      />
    </div>

    <Footer :force-show="showFooter" @hide="showFooter = false" />

    <!-- Кнопка для показа футера -->
    <button v-if="!showFooter" @click="showFooter = true" class="show-footer-btn" title="Показать футер">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M12 5v14M5 12l7 7 7-7"/>
      </svg>
    </button>

    <!-- Модальное окно деталей источника -->
    <SourceDetailModal
      v-if="selectedSource"
      :source="selectedSource"
      @close="selectedSource = null"
    />

    <!-- Модальное окно информации о параметрах -->
    <ParamsInfoModal
      v-if="showInfoModal === 'settings'"
      @close="showInfoModal = null"
    />

    <!-- Модальное окно звёздного рейтинга -->
    <StarRatingModal
      v-if="showStarRating"
      :selected-stars="selectedStars"
      @close="showStarRating = false"
      @submit="submitStarRating"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import Header from '../components/Header.vue'
import Footer from '../components/Footer.vue'
import SearchParamsPanel from '../components/chat/SearchParamsPanel.vue'
import ChatHeader from '../components/chat/ChatHeader.vue'
import ChatMessages from '../components/chat/ChatMessages.vue'
import ChatInputArea from '../components/chat/ChatInputArea.vue'
import SourcesPanel from '../components/chat/SourcesPanel.vue'
import SourceDetailModal from '../components/chat/modals/SourceDetailModal.vue'
import ParamsInfoModal from '../components/chat/modals/ParamsInfoModal.vue'
import StarRatingModal from '../components/chat/modals/StarRatingModal.vue'
import { useChatStore } from '../stores/chatStore'
import { useAuthStore } from '../stores/authStore'

const authStore = useAuthStore()
const chatStore = useChatStore()

// Поле ввода
const newMessage = ref('')

// Параметры поиска
const searchParams = ref({
  k: 10,
  temperature: 0.8,
  max_tokens: 2000,
  min_score: 0.0
})

// Модальные окна
const selectedSource = ref(null)
const showInfoModal = ref(null)
const showStarRating = ref(false)
const currentFeedbackSessionId = ref(null)
const selectedStars = ref(0)

// Debouncing для фидбека
const feedbackCooldowns = ref({}) // { sessionId: timestamp }

// Развёрнутое сообщение для показа источников
const expandedMessage = ref(null)
const expandedMessageId = computed(() => expandedMessage.value?.id || null)
const showSourcesPanel = ref(false) // Показывать ли панель источников

// Показывать ли футер
const showFooter = ref(false)

// Использование шаблона (быстрый вопрос)
function handleUseTemplate(text) {
  newMessage.value = text
  nextTick(() => {
    const textarea = document.querySelector('textarea')
    if (textarea) {
      textarea.focus()
      textarea.scrollTop = textarea.scrollHeight
    }
  })
}

// Отправка сообщения
async function sendMessage() {
  const text = newMessage.value.trim()
  if (!text || chatStore.isLoading) return
  newMessage.value = ''
  try {
    await chatStore.sendQuestion(text, searchParams.value)
    await nextTick()
    scrollToBottom()
  } catch (err) {
    console.error('Ошибка отправки:', err)
  }
}

// Прокрутка вниз
function scrollToBottom() {
  const container = document.querySelector('.messages-container')
  if (container) {
    container.scrollTop = container.scrollHeight
  }
}

// Начать новый чат
function handleNewChat() {
  chatStore.newChat()
  newMessage.value = ''
  expandedMessage.value = null
}

// Показать/скрыть источники для сообщения
function toggleSources(message) {
  if (expandedMessage.value?.id === message.id) {
    // Если уже открыто — закрываем
    expandedMessage.value = null
    showSourcesPanel.value = false
  } else {
    // Открываем новое
    expandedMessage.value = message
    showSourcesPanel.value = true
  }
}

// Прокрутка к источнику
function scrollToSource(sourceNum) {
  // Сначала открываем панель источников если закрыта
  if (!showSourcesPanel.value && expandedMessage.value) {
    showSourcesPanel.value = true
  }
  
  const sourceElement = document.getElementById(`source-${sourceNum}`)
  if (sourceElement) {
    sourceElement.scrollIntoView({ behavior: 'smooth', block: 'center' })
    sourceElement.classList.add('highlight')
    setTimeout(() => {
      sourceElement.classList.remove('highlight')
    }, 2000)
  }
}

// Обработчик события прокрутки к источнику
function handleScrollToSource({ sourceNum, messageId }) {
  if (expandedMessage.value) {
    // Если панель уже открыта, проверяем, то ли это сообщение
    if (expandedMessage.value.id === messageId) {
      scrollToSource(sourceNum)
    } else {
      // Если другое сообщение — переключаемся на него
      const targetMessage = chatStore.messages.find(m => m.id === messageId)
      if (targetMessage) {
        expandedMessage.value = targetMessage
        showSourcesPanel.value = true
        nextTick(() => {
          scrollToSource(sourceNum)
        })
      }
    }
  } else {
    // Если панель закрыта, находим нужное сообщение
    const targetMessage = chatStore.messages.find(m => m.id === messageId)
    if (targetMessage) {
      expandedMessage.value = targetMessage
      showSourcesPanel.value = true
      nextTick(() => {
        scrollToSource(sourceNum)
      })
    }
  }
}

// Фидбек
async function handleFeedback(queryId, type) {
  if (!queryId) {
    console.warn('Нет queryId для фидбека')
    return
  }

  // Проверка cooldown (1 секунда задержка)
  const now = Date.now()
  const lastFeedbackTime = feedbackCooldowns.value[queryId] || 0
  if (now - lastFeedbackTime < 1000) {
    console.log('Feedback cooldown active')
    return
  }

  const current = chatStore.feedbacks[queryId]
  try {
    // Если кликнули на ту же кнопку — снимаем фидбек
    if (current?.feedback_type === type) {
      await chatStore.removeFeedback(queryId)
    } else {
      // Иначе ставим новый фидбек
      await chatStore.submitFeedback(queryId, type)
      feedbackCooldowns.value[queryId] = now
    }
  } catch (err) {
    console.error('Ошибка фидбека:', err)
    alert('Не удалось отправить оценку. Попробуйте позже.')
  }
}

function openStarRating(queryId) {
  if (!queryId) {
    console.warn('Нет queryId для звёздного рейтинга')
    return
  }
  currentFeedbackSessionId.value = queryId
  showStarRating.value = true
}

async function submitStarRating(rating) {
  console.log('submitStarRating called with:', rating, 'queryId:', currentFeedbackSessionId.value)
  if (!currentFeedbackSessionId.value || !rating || rating < 1) {
    console.warn('Invalid rating or queryId:', { rating, queryId: currentFeedbackSessionId.value })
    showStarRating.value = false
    return
  }

  // Проверка cooldown
  const now = Date.now()
  const lastFeedbackTime = feedbackCooldowns.value[currentFeedbackSessionId.value] || 0
  if (now - lastFeedbackTime < 1000) {
    console.log('Star rating cooldown active')
    showStarRating.value = false
    return
  }

  selectedStars.value = rating
  try {
    await chatStore.submitFeedback(currentFeedbackSessionId.value, 'star', rating)
    feedbackCooldowns.value[currentFeedbackSessionId.value] = now
  } catch (err) {
    console.error('Ошибка фидбека:', err)
    alert('Не удалось отправить оценку. Попробуйте позже.')
  } finally {
    showStarRating.value = false
    currentFeedbackSessionId.value = null
  }
}

// Модалка с деталями источника
function openSourceModal(source) {
  selectedSource.value = source
}

// Загрузка истории при монтировании
onMounted(async () => {
  console.log('===== Home.vue: onMounted START =====')
  console.log('Home mounted, checking for resumeSessionId...')
  
  // 1. Сначала пробуем восстановить сессию из History.vue
  const resumeSessionId = localStorage.getItem('resumeSessionId')
  console.log('resumeSessionId:', resumeSessionId)
  console.log('authStore.user:', authStore.user)
  console.log('chatStore.messages before:', chatStore.messages?.length || 0)
  console.log('chatStore.sessionId before:', chatStore.sessionId)

  if (authStore.user) {
    if (resumeSessionId) {
      console.log('=== RESUME SESSION MODE ===')
      localStorage.removeItem('resumeSessionId')

      // 1. Включаем лоадер, чтобы UI сразу отреагировал на переход
      chatStore.isLoading = true
      console.log('chatStore.isLoading set to:', chatStore.isLoading)

      try {
        // 2. Делаем тяжелый запрос к истории
        console.log('Loading history for session:', resumeSessionId)
        await chatStore.loadHistory(50)
        console.log('chatStore.history loaded:', chatStore.history?.length || 0)

        // Находим записи для этой сессии
        const sessionChats = (chatStore.history || [])
          .filter(c => c.session_id === resumeSessionId || c.id == resumeSessionId)
          .sort((a, b) => new Date(a.created_at) - new Date(b.created_at))

        console.log('sessionChats found:', sessionChats.length)
        if (sessionChats.length > 0) {
          console.log('First chat:', sessionChats[0])
        }

        if (sessionChats.length > 0) {
          const actualSessionId = String(sessionChats[0].session_id || sessionChats[0].id)
          chatStore.sessionId = actualSessionId
          chatStore.currentSessionTitle = sessionChats[0].question?.substring(0, 50) || 'Чат'

          // Очищаем и добавляем все сообщения из сессии
          chatStore.messages = []
          for (const chat of sessionChats) {
            chatStore.messages.push({
              id: Date.now() + chat.id,
              role: 'user',
              content: chat.question,
              sessionId: actualSessionId,
              timestamp: new Date(chat.created_at)
            })
            chatStore.messages.push({
              id: Date.now() + chat.id + 1,
              role: 'assistant',
              content: chat.answer,
              sources: chat.sources || [],
              sessionId: actualSessionId,
              queryId: chat.id,
              timestamp: new Date(chat.created_at)
            })
          }
          console.log('Session restored from History.vue:', chatStore.messages.length, 'messages')
          console.log('Messages:', chatStore.messages)
          
          // Сохраняем в sessionStorage для последующего восстановления после F5
          chatStore.saveToStorage()
          console.log('Saved to sessionStorage')
          
          // Сохраняем текущую сессию для быстрого доступа
          localStorage.setItem('currentSession', JSON.stringify({
            sessionId: actualSessionId,
            title: chatStore.currentSessionTitle
          }))
        } else {
          console.warn('No chats found for session:', resumeSessionId)
        }
      } catch (err) {
        console.error('Error loading history:', err)
      } finally {
        // 3. Гарантированно выключаем лоадер
        chatStore.isLoading = false
        console.log('chatStore.isLoading set to:', chatStore.isLoading)
      }
    } 
    // 2. Если resumeSessionId нет, пробуем восстановить из sessionStorage (после F5)
    else {
      console.log('=== F5 REFRESH MODE ===')
      console.log('No resumeSessionId, trying to restore from sessionStorage...')
      
      // Проверяем, что есть в sessionStorage
      console.log('sessionStorage keys:', Object.keys(sessionStorage))
      console.log('sessionStorage.chat_messages:', sessionStorage.getItem('chat_messages'))
      console.log('sessionStorage.chat_session_id:', sessionStorage.getItem('chat_session_id'))
      
      const restored = chatStore.restoreFromStorage()
      console.log('restoreFromStorage returned:', restored)
      console.log('chatStore.messages after restore:', chatStore.messages?.length || 0)
      console.log('chatStore.sessionId after restore:', chatStore.sessionId)
      
      if (restored) {
        console.log('Session restored from sessionStorage:', chatStore.messages.length, 'messages')
      } else {
        // Если нет сохранённой сессии, просто загружаем историю
        console.log('No saved session in sessionStorage, loading history...')
        chatStore.isLoading = true
        try {
          if ((chatStore.history?.length || 0) === 0) {
            await chatStore.loadHistory(50)
          }
        } finally {
          chatStore.isLoading = false
        }
      }
    }
  } else {
    console.log('User not authenticated')
  }
  
  console.log('===== Home.vue: onMounted END =====')
  console.log('Final state:')
  console.log('  chatStore.messages:', chatStore.messages?.length || 0)
  console.log('  chatStore.sessionId:', chatStore.sessionId)
  console.log('  chatStore.isLoading:', chatStore.isLoading)
})
</script>

<style scoped>
.home {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.main-layout {
  display: flex;
  flex: 1;
  min-height: 0;
  height: calc(100vh - 180px);
  overflow: hidden;
}

/* Кнопка для показа футера */
.show-footer-btn {
  position: fixed;
  bottom: 20px;
  right: 20px;
  width: 50px;
  height: 50px;
  border-radius: 50%;
  background: #0066cc;
  color: white;
  border: none;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(0, 102, 204, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  z-index: 100;
}

.show-footer-btn:hover {
  background: #0052a3;
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(0, 102, 204, 0.4);
}

.show-footer-btn:active {
  transform: translateY(0);
}

/* Левая колонка с параметрами - фиксированная */
.sidebar-left {
  width: 320px;
  background: #f8f9fa;
  border-right: 1px solid #ddd;
  padding: 20px;
  overflow-y: auto;
  flex-shrink: 0;
  position: sticky;
  left: 0;
  top: 0;
  height: 100%;
  max-height: 100%;
}

/* Центральная колонка (чат) - скроллится */
.chat-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: white;
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
  min-width: 0;
  height: 100%;
  overflow: hidden;
}

/* Правая колонка с источниками - фиксированная */
.sources-panel {
  width: 400px;
  background: #ffffff;
  border-left: 1px solid #ddd;
  padding: 0;
  overflow-y: auto;
  flex-shrink: 0;
  height: 100%;
}

.sources-panel .sources-header {
  position: sticky;
  top: 0;
  z-index: 10;
  background: #f9fafb;
}

/* FAQ под чатом */
.faq-below-chat {
  padding: 20px;
  border-top: 1px solid #e5e7eb;
  background: #f9fafb;
  overflow-y: auto;
  max-height: 300px;
  flex-shrink: 0;
}

/* Адаптивность */
@media (max-width: 1200px) {
  .sidebar-left {
    width: 280px;
  }
}

@media (max-width: 992px) {
  .sidebar-left {
    display: none;
  }
}

@media (max-width: 768px) {
  .chat-area {
    max-width: 100%;
  }
}
</style>
