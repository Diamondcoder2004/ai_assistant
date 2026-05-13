<template>
  <aside class="left-sidebar" :class="{ 'is-open': isOpen }">
    <div class="sidebar-inner">
      <!-- Заголовок сайдбара -->
      <div class="sidebar-header">
        <span class="sidebar-title">История чатов</span>
        <button @click="$emit('close')" class="close-btn" title="Закрыть">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M18 6L6 18M6 6l12 12"/>
          </svg>
        </button>
      </div>

      <!-- Кнопка нового чата -->
      <button @click="handleNewChat" class="new-chat-btn" :disabled="chatStore.isLoading">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M12 5v14M5 12h14"/>
        </svg>
        Новый чат
      </button>

      <!-- Список сессий -->
      <div class="sessions-list" v-if="sortedSessions.length > 0">
        <div
          v-for="session in sortedSessions"
          :key="session.session_id || session.id"
          class="session-item"
          :class="{ 'is-active': (session.session_id || String(session.id)) === currentSessionId }"
          @click="resumeSession(session)"
        >
          <div class="session-icon">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
            </svg>
          </div>
          <div class="session-info">
            <span class="session-title">{{ sessionTitle(session) }}</span>
            <span class="session-date">{{ formatDate(session.created_at) }}</span>
          </div>
        </div>
      </div>

      <!-- Пустое состояние -->
      <div v-else class="empty-state">
        <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
        </svg>
        <p>История чатов пуста</p>
        <p class="empty-hint">Начните новый диалог</p>
      </div>

      <!-- Индикатор загрузки -->
      <div v-if="chatStore.isLoadingHistory" class="loading-indicator">
        <div class="spinner"></div>
        <span>Загрузка...</span>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { computed } from 'vue'
import { useChatStore } from '../stores/chatStore'

const emit = defineEmits(['close', 'newChat', 'resumeSession'])

defineProps({
  isOpen: {
    type: Boolean,
    default: false
  }
})

const chatStore = useChatStore()

const currentSessionId = computed(() => chatStore.sessionId)

// Сессии, отсортированные по дате (свежие сверху)
const sortedSessions = computed(() => {
  const sessions = chatStore.chatSessions || []
  return [...sessions].sort((a, b) => {
    const dateA = new Date(a.created_at || 0)
    const dateB = new Date(b.created_at || 0)
    return dateB - dateA
  })
})

function sessionTitle(session) {
  return session.question?.substring(0, 50) || session.title || 'Чат'
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  const now = new Date()
  const diff = now - d
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))

  if (days === 0) {
    return d.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })
  }
  if (days === 1) return 'Вчера'
  if (days < 7) return `${days} дн. назад`
  return d.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' })
}

function handleNewChat() {
  emit('newChat')
  emit('close')
}

function resumeSession(session) {
  const sessionId = session.session_id || String(session.id)
  emit('resumeSession', sessionId)
  emit('close')
}
</script>

<style scoped>
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
  width: 300px;
  border-right: 1px solid #ddd;
}

.sidebar-inner {
  width: 300px;
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* Хедер */
.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #e5e7eb;
  background: #f9fafb;
  flex-shrink: 0;
}

.sidebar-title {
  font-size: 15px;
  font-weight: 600;
  color: #1f2937;
}

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

/* Кнопка нового чата */
.new-chat-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin: 12px 16px;
  padding: 10px 16px;
  background: #0066cc;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
  flex-shrink: 0;
}

.new-chat-btn:hover:not(:disabled) {
  background: #0052a3;
}

.new-chat-btn:disabled {
  background: #d1d5db;
  cursor: not-allowed;
}

/* Список сессий */
.sessions-list {
  flex: 1;
  overflow-y: auto;
  padding: 4px 0;
}

.session-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  cursor: pointer;
  transition: background 0.15s;
  border-left: 3px solid transparent;
}

.session-item:hover {
  background: #f3f4f6;
}

.session-item.is-active {
  background: #eff6ff;
  border-left-color: #0066cc;
}

.session-icon {
  flex-shrink: 0;
  color: #9ca3af;
  display: flex;
}

.session-item.is-active .session-icon {
  color: #0066cc;
}

.session-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.session-title {
  font-size: 14px;
  color: #374151;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.session-item.is-active .session-title {
  color: #0066cc;
  font-weight: 500;
}

.session-date {
  font-size: 12px;
  color: #9ca3af;
}

/* Пустое состояние */
.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  color: #9ca3af;
  gap: 8px;
}

.empty-state p {
  margin: 0;
  font-size: 14px;
}

.empty-hint {
  font-size: 12px;
  opacity: 0.7;
}

/* Индикатор загрузки */
.loading-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 16px;
  color: #9ca3af;
  font-size: 13px;
  flex-shrink: 0;
}

.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid #e5e7eb;
  border-top-color: #0066cc;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
