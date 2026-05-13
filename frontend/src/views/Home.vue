<template>
  <div class="home">
    <Header />

    <div class="main-layout">
      <!-- Левый сайдбар с форматом ответа -->
      <aside class="left-sidebar" :class="{ 'is-open': showLeftSidebar }">
        <div class="sidebar-inner">
          <div class="sidebar-header">
            <span class="sidebar-title">Формат ответа</span>
            <button @click="showLeftSidebar = false" class="close-btn" title="Закрыть">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M18 6L6 18M6 6l12 12"/>
              </svg>
            </button>
          </div>
          <div class="sidebar-params-body">
            <SearchParamsPanel
              v-model="searchParams"
            />
          </div>
        </div>
      </aside>

      <!-- Основная область чата -->
      <main class="chat-area">
        <!-- Шапка чата -->
        <ChatHeader
          :session-title="chatStore.currentSessionTitle"
          :is-loading="chatStore.isLoading"
          @new-chat="handleNewChat"
        >
          <template #left>
            <!-- Гамбургер для левого сайдбара (формат ответа) -->
            <button @click="showLeftSidebar = !showLeftSidebar" class="hamburger-btn" title="Формат ответа">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M3 12h18M3 6h18M3 18h18"/>
              </svg>
            </button>
          </template>
        </ChatHeader>

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

      <!-- Правый сайдбар: только источники -->
      <aside class="right-sidebar" :class="{ 'is-open': showSidebar }">
        <div class="sidebar-header">
          <span class="sidebar-title">📚 Источники</span>
          <button @click="closeSidebar" class="close-btn" title="Закрыть">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M18 6L6 18M6 6l12 12"/>
            </svg>
          </button>
        </div>
        <div class="sidebar-content">
          <div v-if="expandedMessage" class="sources-body">
            <SourcesPanel
              :expanded-message="expandedMessage"
              :compact="true"
              @open-source="openSourceModal"
            />
          </div>
          <div v-else class="sources-empty">
            <p class="empty-text">Нажмите "📄 N источников" под ответом, чтобы увидеть источники</p>
          </div>
        </div>
      </aside>
    </div>

    <Footer />

    <!-- Модальное окно деталей источника -->
    <SourceDetailModal
      v-if="selectedSource"
      :source="selectedSource"
      @close="selectedSource = null"
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
import StarRatingModal from '../components/chat/modals/StarRatingModal.vue'
import { useChatStore } from '../stores/chatStore'
import { useAuthStore } from '../stores/authStore'
import { useRouter } from 'vue-router'

const router = useRouter()
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
const showStarRating = ref(false)
const currentFeedbackSessionId = ref(null)
const selectedStars = ref(0)

// Debouncing для фидбека
const feedbackCooldowns = ref({})

// Развёрнутое сообщение для показа источников
const expandedMessage = ref(null)
const expandedMessageId = computed(() => expandedMessage.value?.id || null)

// Управление левым сайдбаром (формат ответа)
const showLeftSidebar = ref(false)

// Управление правым сайдбаром (только источники)
const showSidebar = ref(false)

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
  showSidebar.value = false
  showLeftSidebar.value = false
}

// Закрыть правый сайдбар
function closeSidebar() {
  showSidebar.value = false
  expandedMessage.value = null
}

// Показать/скрыть источники для сообщения
function toggleSources(message) {
  if (expandedMessage.value?.id === message.id) {
    // Если уже открыто — закрываем
    expandedMessage.value = null
    showSidebar.value = false
  } else {
    // Открываем новое
    expandedMessage.value = message
    showSidebar.value = true
  }
}

// Прокрутка к источнику
function scrollToSource(sourceNum) {
  if (!showSidebar.value && expandedMessage.value) {
    showSidebar.value = true
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
    if (expandedMessage.value.id === messageId) {
      scrollToSource(sourceNum)
    } else {
      const targetMessage = chatStore.messages.find(m => m.id === messageId)
      if (targetMessage) {
        expandedMessage.value = targetMessage
        showSidebar.value = true
        nextTick(() => {
          scrollToSource(sourceNum)
        })
      }
    }
  } else {
    const targetMessage = chatStore.messages.find(m => m.id === messageId)
    if (targetMessage) {
      expandedMessage.value = targetMessage
      showSidebar.value = true
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

  const now = Date.now()
  const lastFeedbackTime = feedbackCooldowns.value[queryId] || 0
  if (now - lastFeedbackTime < 1000) {
    console.log('Feedback cooldown active')
    return
  }

  const current = chatStore.feedbacks[queryId]
  try {
    if (current?.feedback_type === type) {
      await chatStore.removeFeedback(queryId)
    } else {
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
  if (!currentFeedbackSessionId.value || !rating || rating < 1) {
    showStarRating.value = false
    return
  }

  const now = Date.now()
  const lastFeedbackTime = feedbackCooldowns.value[currentFeedbackSessionId.value] || 0
  if (now - lastFeedbackTime < 1000) {
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

  const resumeSessionId = localStorage.getItem('resumeSessionId')

  if (authStore.user) {
    if (resumeSessionId) {
      localStorage.removeItem('resumeSessionId')
      chatStore.isLoading = true

      try {
        await chatStore.loadHistory(50)

        const sessionChats = (chatStore.history || [])
          .filter(c => c.session_id === resumeSessionId || c.id == resumeSessionId)
          .sort((a, b) => new Date(a.created_at) - new Date(b.created_at))

        if (sessionChats.length > 0) {
          const actualSessionId = String(sessionChats[0].session_id || sessionChats[0].id)
          chatStore.sessionId = actualSessionId
          chatStore.currentSessionTitle = sessionChats[0].question?.substring(0, 50) || 'Чат'

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

          chatStore.saveToStorage()
          localStorage.setItem('currentSession', JSON.stringify({
            sessionId: actualSessionId,
            title: chatStore.currentSessionTitle
          }))
        }
      } catch (err) {
        console.error('Error loading history:', err)
      } finally {
        chatStore.isLoading = false
      }
    } else {
      const restored = chatStore.restoreFromStorage()

      if (restored) {
        // Session restored from storage
      } else {
        chatStore.isLoading = true
        try {
          await chatStore.loadHistory(50)

          if (chatStore.history && chatStore.history.length > 0) {
            const lastSession = chatStore.history[0]
            const actualSessionId = String(lastSession.session_id || lastSession.id)

            const sessionChats = (chatStore.history || [])
              .filter(c => c.session_id === actualSessionId || c.id == actualSessionId)
              .sort((a, b) => new Date(a.created_at) - new Date(b.created_at))

            if (sessionChats.length > 0) {
              chatStore.sessionId = actualSessionId
              chatStore.currentSessionTitle = sessionChats[0].question?.substring(0, 50) || 'Чат'

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

              chatStore.saveToStorage()
            }
          }
        } finally {
          chatStore.isLoading = false
        }
      }
    }
  }
})
</script>

<style scoped>
.home {
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.main-layout {
  display: flex;
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

/* ==================================================
   Левый сайдбар — формат ответа
   ================================================== */
.left-sidebar {
  width: 0;
  overflow: hidden;
  flex-shrink: 0;
  background: #f8f9fa;
  border-right: none;
  display: flex;
  flex-direction: column;
  transition: width 0.25s ease, border-right 0.25s ease;
}

.left-sidebar.is-open {
  width: 280px;
  border-right: 1px solid #ddd;
}

.sidebar-inner {
  width: 280px;
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.sidebar-inner .sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #e5e7eb;
  background: #f9fafb;
  flex-shrink: 0;
}

.sidebar-inner .sidebar-title {
  font-size: 15px;
  font-weight: 600;
  color: #1f2937;
}

.sidebar-params-body {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

/* ==================================================
   Правая часть (чат)
   ================================================== */
.chat-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: white;
  min-width: 0;
  overflow: hidden;
}

/* ==================================================
   Правый сайдбар — только источники
   ================================================== */
.right-sidebar {
  width: 0;
  overflow: hidden;
  flex-shrink: 0;
  background: #f8f9fa;
  border-left: none;
  display: flex;
  flex-direction: column;
  transition: width 0.25s ease, border-left 0.25s ease;
}

.right-sidebar.is-open {
  width: 380px;
  border-left: 1px solid #ddd;
}

.right-sidebar .sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #e5e7eb;
  background: #f9fafb;
  flex-shrink: 0;
}

.right-sidebar .sidebar-title {
  font-size: 15px;
  font-weight: 600;
  color: #1f2937;
}

.right-sidebar .sidebar-content {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.right-sidebar .sources-body {
  flex: 1;
  overflow-y: auto;
}

.right-sidebar .sources-empty {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px 16px;
}

.empty-text {
  color: #9ca3af;
  font-size: 13px;
  text-align: center;
  margin: 0;
  line-height: 1.5;
}

/* ==================================================
   Общие кнопки (левый + правый сайдбары)
   ================================================== */
.close-btn {
  background: none;
  border: none;
  cursor: pointer;
  color: #6b7280;
  padding: 4px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.close-btn:hover {
  background: #e5e7eb;
  color: #1f2937;
}

/* Гамбургер */
.hamburger-btn {
  background: none;
  border: none;
  cursor: pointer;
  color: #6b7280;
  padding: 6px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  margin-right: 4px;
}

.hamburger-btn:hover {
  background: #e5e7eb;
  color: #1f2937;
}

/* ==================================================
   Адаптивность
   ================================================== */
@media (max-width: 992px) {
  .left-sidebar.is-open {
    width: 240px;
  }
  .right-sidebar.is-open {
    width: 340px;
  }
}

@media (max-width: 768px) {
  .left-sidebar,
  .right-sidebar {
    display: none;
  }
}
</style>
