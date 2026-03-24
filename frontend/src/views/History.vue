<template>
  <div class="history-page">
    <Header />

    <div class="container">
      <div class="page-header">
        <h1>История чатов</h1>
        <button @click="loadHistory" class="refresh-btn" :disabled="loading" title="Обновить">
          <svg :class="{ 'spinning': loading }" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M23 4v6h-6M1 20v-6h6"/>
            <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
          </svg>
        </button>
      </div>

      <div class="search-box">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="11" cy="11" r="8"/>
          <path d="m21 21-4.35-4.35"/>
        </svg>
        <input
          v-model="searchQuery"
          placeholder="Поиск по вопросам и ответам..."
          @input="searchHistory"
        />
      </div>

      <div v-if="loading" class="loading">
        <div class="spinner"></div>
        <p>Загрузка истории...</p>
      </div>

      <div v-else-if="filteredChats.length === 0" class="empty">
        <div class="empty-icon">📭</div>
        <p v-if="searchQuery">Ничего не найдено по запросу "{{ searchQuery }}"</p>
        <p v-else>История чатов пуста</p>
        <p class="hint">Задайте вопрос в чате, чтобы начать историю</p>
      </div>

      <div v-else class="chat-list">
        <div
          v-for="chat in filteredChats"
          :key="chat.id"
          class="chat-item"
          @click="resumeChat(chat)"
        >
          <div class="chat-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
            </svg>
          </div>
          <div class="chat-content">
            <div class="chat-header-row">
              <span class="chat-date">{{ formatDate(chat.created_at) }}</span>
              <span v-if="chat.session_id" class="session-badge">Сессия</span>
            </div>
            <div class="chat-question">
              <strong>Вопрос:</strong> {{ chat.question }}
            </div>
            <div class="chat-answer">
              <strong>Ответ:</strong> <span v-html="renderAnswer(truncate(chat.answer, 150))"></span>
            </div>
          </div>
          <div class="chat-arrow">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M9 18l6-6-6-6"/>
            </svg>
          </div>
        </div>
      </div>
    </div>

    <Footer />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import Header from '../components/Header.vue'
import Footer from '../components/Footer.vue'
import { useAuthStore } from '../stores/authStore'
import { useChatStore } from '../stores/chatStore'
import { chatService } from '../services/supabase'

const router = useRouter()
const authStore = useAuthStore()
const chatStore = useChatStore()
const chats = ref([])
const filteredChats = ref([])
const searchQuery = ref('')
const loading = ref(true)

// Загрузка истории
async function loadHistory() {
  if (!authStore.user) {
    console.log('User not authenticated, cannot load history')
    loading.value = false
    chats.value = []
    filteredChats.value = []
    return
  }

  loading.value = true
  try {
    // Загружаем историю через chatStore, чтобы данные сохранились
    console.log('History.vue: before loadHistory, chatStore.history:', chatStore.history, 'length:', chatStore.history?.length)
    await chatStore.loadHistory(100)
    console.log('History.vue: after loadHistory, chatStore.history:', chatStore.history, 'length:', chatStore.history?.length)
    chats.value = chatStore.history || []
    filteredChats.value = chats.value
    console.log('History.vue: loaded chats:', chats.value.length)
    console.log('History.vue: first chat:', chats.value[0])
    console.log('History.vue: session_ids:', chats.value.map(c => c.session_id))
  } catch (error) {
    console.error('Ошибка загрузки истории:', error)
    chats.value = []
    filteredChats.value = []
  } finally {
    loading.value = false
  }
}

// Поиск по истории
function searchHistory() {
  if (!searchQuery.value.trim()) {
    filteredChats.value = chats.value
    return
  }

  // Нормализуем поисковый запрос: убираем лишние пробелы, приводим к нижнему регистру
  const query = searchQuery.value.toLowerCase().replace(/\s+/g, ' ').trim()
  filteredChats.value = chats.value.filter(chat => {
    // Нормализуем вопрос и ответ для лучшего совпадения
    const question = (chat.question || '').toLowerCase().replace(/\s+/g, ' ').trim()
    const answer = (chat.answer || '').toLowerCase().replace(/\s+/g, ' ').trim()
    return question.includes(query) || answer.includes(query)
  })
}

// Форматирование даты
function formatDate(dateString) {
  const date = new Date(dateString)
  const now = new Date()
  const diff = now - date
  
  // Если сегодня
  if (diff < 24 * 60 * 60 * 1000) {
    return 'Сегодня, ' + date.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })
  }
  
  // Если вчера
  const yesterday = new Date(now)
  yesterday.setDate(yesterday.getDate() - 1)
  if (date.toDateString() === yesterday.toDateString()) {
    return 'Вчера, ' + date.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })
  }
  
  // Если в этом году
  if (date.getFullYear() === now.getFullYear()) {
    return date.toLocaleDateString('ru-RU', { day: '2-digit', month: 'long', hour: '2-digit', minute: '2-digit' })
  }
  
  // Полный формат
  return date.toLocaleDateString('ru-RU', { day: '2-digit', month: 'long', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

// Обрезка текста
function truncate(text, length) {
  if (!text) return ''
  return text.length > length ? text.slice(0, length) + '...' : text
}

// Рендеринг ответа (поддержка HTML и Markdown)
function renderAnswer(text) {
  if (!text) return ''
  
  // Если контент уже содержит HTML-теги, используем его как есть
  if (text.includes('<br>') || text.includes('<table') || text.includes('<tr>') || 
      text.includes('<td>') || text.includes('<h') || text.includes('<p>') || 
      text.includes('<strong>') || text.includes('<ul>') || text.includes('<li>')) {
    return text
  }
  
  let content = text
  
  // Экранируем HTML для безопасности
  content = content
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
  
  // Заголовки
  content = content.replace(/^###### (.*$)/gim, '<h6>$1</h6>')
  content = content.replace(/^##### (.*$)/gim, '<h5>$1</h5>')
  content = content.replace(/^#### (.*$)/gim, '<h4>$1</h4>')
  content = content.replace(/^### (.*$)/gim, '<h3>$1</h3>')
  content = content.replace(/^## (.*$)/gim, '<h2>$1</h2>')
  content = content.replace(/^# (.*$)/gim, '<h1>$1</h1>')
  
  // Жирный текст
  content = content.replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>')
  content = content.replace(/__(.*?)__/gim, '<strong>$1</strong>')
  
  // Курсив
  content = content.replace(/\*(.*?)\*/gim, '<em>$1</em>')
  content = content.replace(/_(.*?)_/gim, '<em>$1</em>')
  
  // Переносы строк
  content = content.replace(/\n/g, '<br>')
  
  return content
}

// Возобновить чат (переход на главную с session_id)
function resumeChat(chat) {
  // Сохраняем session_id в localStorage для восстановления на главной
  // Если session_id нет, используем id записи
  const sessionIdToSave = chat.session_id || chat.id
  console.log('resumeChat: saving sessionId:', sessionIdToSave, 'from chat:', chat)
  if (sessionIdToSave) {
    localStorage.setItem('resumeSessionId', sessionIdToSave)
  }
  router.push('/')
}

onMounted(async () => {
  // Ждем инициализации authStore, если нужно
  if (!authStore.user && authStore.init) {
    await authStore.init()
  }
  loadHistory()
})
</script>

<style scoped>
.history-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.container {
  flex: 1;
  max-width: 900px;
  margin: 0 auto;
  padding: 20px;
  width: 100%;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h1 {
  color: #003366;
  margin: 0;
  font-size: 28px;
}

.refresh-btn {
  background: none;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  padding: 8px;
  cursor: pointer;
  color: #6b7280;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.refresh-btn:hover:not(:disabled) {
  background: #f3f4f6;
  color: #0066cc;
  border-color: #0066cc;
}

.refresh-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.refresh-btn .spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.search-box {
  display: flex;
  align-items: center;
  gap: 12px;
  background: white;
  border: 1px solid #d1d5db;
  border-radius: 12px;
  padding: 12px 16px;
  margin-bottom: 24px;
  transition: all 0.2s;
}

.search-box:focus-within {
  border-color: #0066cc;
  box-shadow: 0 0 0 3px rgba(0, 102, 204, 0.1);
}

.search-box svg {
  color: #9ca3af;
  flex-shrink: 0;
}

.search-box input {
  flex: 1;
  border: none;
  outline: none;
  font-size: 16px;
  background: transparent;
}

.loading, .empty {
  text-align: center;
  padding: 60px 20px;
}

.loading {
  color: #6b7280;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #e5e7eb;
  border-top-color: #0066cc;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 16px;
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 16px;
}

.empty {
  color: #6b7280;
}

.empty p {
  margin: 8px 0;
}

.empty .hint {
  font-size: 14px;
  color: #9ca3af;
}

.chat-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.chat-item {
  display: flex;
  gap: 16px;
  padding: 16px;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.chat-item:hover {
  background: #eff6ff;
  border-color: #3b82f6;
  transform: translateX(4px);
  box-shadow: 0 4px 12px rgba(0, 102, 204, 0.1);
}

.chat-icon {
  width: 44px;
  height: 44px;
  background: #0066cc;
  color: white;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.chat-content {
  flex: 1;
  min-width: 0;
}

.chat-header-row {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-bottom: 8px;
}

.chat-date {
  font-size: 13px;
  color: #6b7280;
}

.session-badge {
  font-size: 11px;
  background: #dbeafe;
  color: #1e40af;
  padding: 2px 8px;
  border-radius: 10px;
  font-weight: 500;
}

.chat-question, .chat-answer {
  margin-bottom: 6px;
  line-height: 1.5;
  font-size: 15px;
}

.chat-question {
  font-size: 16px;
  font-weight: 500;
}

.chat-question strong, .chat-answer strong {
  color: #0066cc;
  margin-right: 4px;
}

.chat-answer {
  color: #4b5563;
}

.chat-answer h1,
.chat-answer h2,
.chat-answer h3,
.chat-answer h4,
.chat-answer h5,
.chat-answer h6 {
  margin: 0.5em 0;
  font-weight: 600;
  color: #1f2937;
  font-size: 1em;
  line-height: 1.4;
}

.chat-answer p {
  margin: 0.5em 0;
}

.chat-answer strong {
  font-weight: 600;
  color: #1f2937;
}

.chat-answer em {
  font-style: italic;
}

.chat-answer code {
  background: #e5e7eb;
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
  font-size: 0.9em;
  color: #dc2626;
}

.chat-answer pre {
  background: #1f2937;
  color: #f9fafb;
  padding: 12px;
  border-radius: 6px;
  overflow-x: auto;
  margin: 0.5em 0;
}

.chat-answer pre code {
  background: none;
  padding: 0;
  color: inherit;
}

.chat-answer ul,
.chat-answer ol {
  margin: 0.5em 0;
  padding-left: 1.5em;
}

.chat-answer li {
  margin: 0.25em 0;
}

.chat-answer table {
  width: 100%;
  border-collapse: collapse;
  margin: 0.5em 0;
  font-size: 13px;
}

.chat-answer th,
.chat-answer td {
  border: 1px solid #d1d5db;
  padding: 6px 10px;
  text-align: left;
}

.chat-answer th {
  background: #f3f4f6;
  font-weight: 600;
}

.chat-answer tr:nth-child(even) {
  background: #f9fafb;
}

.chat-arrow {
  display: flex;
  align-items: center;
  color: #9ca3af;
  flex-shrink: 0;
}

.chat-item:hover .chat-arrow {
  color: #0066cc;
}
</style>
