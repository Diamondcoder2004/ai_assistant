<template>
  <div class="home">
    <Header />

    <div class="main-layout">
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

      <!-- Единый правый сайдбар: параметры + источники -->
      <aside class="unified-sidebar" :class="{ 'is-open': showSidebar }">
        <!-- Хедер сайдбара с кнопкой закрытия -->
        <div class="sidebar-header">
          <button @click="closeSidebar" class="sidebar-close-btn" title="Закрыть">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M18 6L6 18M6 6l12 12"/>
            </svg>
          </button>
        </div>

        <!-- Контент сайдбара -->
        <div class="sidebar-content">
          <!-- Секция параметров (сворачиваемая) -->
          <div class="sidebar-section params-section">
            <div class="section-header" @click="showParams = !showParams">
              <span class="section-title">⚙️ Формат ответа</span>
              <span class="section-toggle">{{ showParams ? '▼' : '▶' }}</span>
            </div>
            <div class="section-body" v-show="showParams">
              <SearchParamsPanel
                v-model="searchParams"
              />
            </div>
          </div>

          <!-- Секция источников (показывается если есть развёрнутое сообщение) -->
          <div v-if="expandedMessage" class="sidebar-section sources-section">
            <div class="section-header">
              <span class="section-title">📚 Источники</span>
            </div>
            <div class="section-body sources-body">
              <SourcesPanel
                :expanded-message="expandedMessage"
                :compact="true"
                @open-source="openSourceModal"
              />
            </div>
          </div>
        </div>
      </aside>
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
const feedbackCooldowns = ref({})

// Развёрнутое сообщение для показа источников
const expandedMessage = ref(null)
const expandedMessageId = computed(() => expandedMessage.value?.id || null)

// Управление единым сайдбаром
const showSidebar = ref(false)
const showParams = ref(true)

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
  showSidebar.value = false
}

// Закрыть сайдбар
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

/* Центральная колонка (чат) */
.chat-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: white;
  min-width: 0;
  overflow: hidden;
}

/* Унифицированный правый сайдбар */
.unified-sidebar {
  width: 0;
  overflow: hidden;
  flex-shrink: 0;
  background: #f8f9fa;
  border-left: none;
  display: flex;
  flex-direction: column;
  transition: width 0.25s ease, border-left 0.25s ease;
}

.unified-sidebar.is-open {
  width: 380px;
  border-left: 1px solid #ddd;
}

/* Хедер сайдбара */
.sidebar-header {
  display: flex;
  justify-content: flex-end;
  padding: 12px 16px;
  border-bottom: 1px solid #e5e7eb;
  background: #f9fafb;
  flex-shrink: 0;
}

.sidebar-close-btn {
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

.sidebar-close-btn:hover {
  background: #e5e7eb;
  color: #1f2937;
}

/* Контент сайдбара (скроллируемый) */
.sidebar-content {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

/* Секции сайдбара */
.sidebar-section {
  border-bottom: 1px solid #e5e7eb;
}

.section-header {
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 16px;
  background: white;
  border-bottom: 1px solid #e5e7eb;
  user-select: none;
  transition: background 0.15s;
}

.section-header:hover {
  background: #f3f4f6;
}

.section-title {
  font-size: 15px;
  font-weight: 600;
  color: #1f2937;
}

.section-toggle {
  font-size: 12px;
  color: #9ca3af;
}

.section-body {
  padding: 14px 16px;
}

/* Секция параметров */
.params-section {
  flex-shrink: 0;
}

/* Секция источников (заполняет оставшееся пространство) */
.sources-section {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.sources-body {
  flex: 1;
  overflow-y: auto;
  padding: 0;
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
@media (max-width: 992px) {
  .unified-sidebar.is-open {
    width: 340px;
  }
}

@media (max-width: 768px) {
  .unified-sidebar {
    display: none;
  }
}
</style>
