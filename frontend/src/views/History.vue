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

      <!-- Фильтры и поиск -->
      <div class="filters-bar">
        <div class="search-box">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"/>
            <path d="m21 21-4.35-4.35"/>
          </svg>
          <input
            v-model="searchQuery"
            placeholder="Поиск по вопросам и ответам..."
            @input="applyFilters"
          />
        </div>
        
        <div class="date-filters">
          <input
            type="date"
            v-model="startDate"
            @change="applyFilters"
            class="date-input"
            title="Начальная дата"
          />
          <span class="date-separator">—</span>
          <input
            type="date"
            v-model="endDate"
            @change="applyFilters"
            class="date-input"
            title="Конечная дата"
          />
          <button @click="resetFilters" class="reset-filters-btn" title="Сбросить фильтры">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M18 6L6 18M6 6l12 12"/>
            </svg>
          </button>
        </div>
      </div>

      <!-- Загрузка -->
      <div v-if="loading && sessions.today.length === 0 && sessions.yesterday.length === 0 && sessions.earlier.length === 0" class="loading">
        <div class="spinner"></div>
        <p>Загрузка истории...</p>
      </div>

      <!-- Пустое состояние -->
      <div v-else-if="!loading && sessions.today.length === 0 && sessions.yesterday.length === 0 && sessions.earlier.length === 0" class="empty">
        <div class="empty-icon">📭</div>
        <p v-if="searchQuery || startDate || endDate">Ничего не найдено по заданным фильтрам</p>
        <p v-else>История чатов пуста</p>
        <p class="hint">Задайте вопрос в чате, чтобы начать историю</p>
      </div>

      <!-- Сессии: Сегодня -->
      <div v-if="sessions.today.length > 0" class="sessions-group">
        <h2 class="group-title">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <polyline points="12 6 12 12 16 14"/>
          </svg>
          Сегодня
        </h2>
        <div class="sessions-list">
          <div
            v-for="session in sessions.today"
            :key="session.session_id"
            class="session-card"
            @click="resumeSession(session)"
          >
            <div class="session-header">
              <div class="session-info">
                <div class="session-question">{{ session.first_question }}</div>
                <div class="session-preview" v-if="session.preview.length > 0">
                  <span class="preview-label">{{ session.messages_count }} сообщений</span>
                  <div class="preview-messages">
                    <div v-for="(msg, idx) in session.preview" :key="idx" class="preview-message" :class="msg.type">
                      <span class="preview-text">{{ msg.text }}</span>
                    </div>
                  </div>
                </div>
              </div>
              <div class="session-meta">
                <span class="session-time">{{ formatTime(session.updated_at) }}</span>
                <svg class="session-arrow" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M9 18l6-6-6-6"/>
                </svg>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Сессии: Вчера -->
      <div v-if="sessions.yesterday.length > 0" class="sessions-group">
        <h2 class="group-title">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
            <line x1="16" y1="2" x2="16" y2="6"/>
            <line x1="8" y1="2" x2="8" y2="6"/>
            <line x1="3" y1="10" x2="21" y2="10"/>
          </svg>
          Вчера
        </h2>
        <div class="sessions-list">
          <div
            v-for="session in sessions.yesterday"
            :key="session.session_id"
            class="session-card"
            @click="resumeSession(session)"
          >
            <div class="session-header">
              <div class="session-info">
                <div class="session-question">{{ session.first_question }}</div>
                <div class="session-preview" v-if="session.preview.length > 0">
                  <span class="preview-label">{{ session.messages_count }} сообщений</span>
                  <div class="preview-messages">
                    <div v-for="(msg, idx) in session.preview" :key="idx" class="preview-message" :class="msg.type">
                      <span class="preview-text">{{ msg.text }}</span>
                    </div>
                  </div>
                </div>
              </div>
              <div class="session-meta">
                <span class="session-time">{{ formatTime(session.updated_at) }}</span>
                <svg class="session-arrow" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M9 18l6-6-6-6"/>
                </svg>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Сессии: Ранее -->
      <div v-if="sessions.earlier.length > 0" class="sessions-group">
        <h2 class="group-title">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
            <line x1="16" y1="2" x2="16" y2="6"/>
            <line x1="8" y1="2" x2="8" y2="6"/>
            <line x1="3" y1="10" x2="21" y2="10"/>
          </svg>
          Ранее
        </h2>
        <div class="sessions-list">
          <div
            v-for="session in sessions.earlier"
            :key="session.session_id"
            class="session-card"
            @click="resumeSession(session)"
          >
            <div class="session-header">
              <div class="session-info">
                <div class="session-question">{{ session.first_question }}</div>
                <div class="session-preview" v-if="session.preview.length > 0">
                  <span class="preview-label">{{ session.messages_count }} сообщений</span>
                  <div class="preview-messages">
                    <div v-for="(msg, idx) in session.preview" :key="idx" class="preview-message" :class="msg.type">
                      <span class="preview-text">{{ msg.text }}</span>
                    </div>
                  </div>
                </div>
              </div>
              <div class="session-meta">
                <span class="session-date">{{ formatDate(session.updated_at) }}</span>
                <span class="session-time">{{ formatTime(session.updated_at) }}</span>
                <svg class="session-arrow" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M9 18l6-6-6-6"/>
                </svg>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Индикатор загрузки ещё -->
      <div v-if="loadingMore" class="loading-more">
        <div class="spinner"></div>
        <p>Загрузка...</p>
      </div>
      
      <!-- Конец списка -->
      <div v-if="!hasMore && sessions.today.length + sessions.yesterday.length + sessions.earlier.length > 0" class="end-of-list">
        <p>Это все чаты</p>
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
import { chatService } from '../services/supabase'

const router = useRouter()
const authStore = useAuthStore()

const sessions = ref({
  today: [],
  yesterday: [],
  earlier: []
})

const searchQuery = ref('')
const startDate = ref('')
const endDate = ref('')
const loading = ref(true)
const loadingMore = ref(false)
const currentPage = ref(1)
const pageSize = 20
const hasMore = ref(true)

// Установка дат по умолчанию (без фильтрации - показываем все чаты)
function setDefaultDates() {
  // Оставляем даты пустыми - показываем все чаты
  startDate.value = ''
  endDate.value = ''
  console.log('setDefaultDates: даты сброшены, start=', startDate.value, 'end=', endDate.value)
}

// Загрузка истории сессий
async function loadHistory(append = false) {
  if (!authStore.user) {
    console.log('User not authenticated, cannot load history')
    loading.value = false
    return
  }

  if (append) {
    loadingMore.value = true
  } else {
    loading.value = true
    currentPage.value = 1
    hasMore.value = true
  }

  try {
    const params = {}
    if (searchQuery.value) params.search = searchQuery.value
    if (startDate.value) params.start_date = startDate.value
    if (endDate.value) params.end_date = endDate.value
    params.limit = pageSize
    params.offset = append ? currentPage.value * pageSize : 0

    console.log('loadHistory: отправка параметров:', params)
    console.log('loadHistory: startDate=', startDate.value, 'endDate=', endDate.value)

    const data = await chatService.getHistorySessions(
      params.search || null, 
      params.start_date || null, 
      params.end_date || null,
      params.limit,
      params.offset
    )

    const newSessions = data || { today: [], yesterday: [], earlier: [] }
    
    if (append) {
      // Объединяем с существующими
      sessions.value.today = [...sessions.value.today, ...newSessions.today]
      sessions.value.yesterday = [...sessions.value.yesterday, ...newSessions.yesterday]
      sessions.value.earlier = [...sessions.value.earlier, ...newSessions.earlier]
      
      // Проверяем, есть ли ещё данные
      const totalNew = newSessions.today.length + newSessions.yesterday.length + newSessions.earlier.length
      hasMore.value = totalNew >= pageSize
      currentPage.value++
    } else {
      sessions.value = newSessions
      
      // Проверяем, есть ли ещё данные
      const total = sessions.value.today.length + sessions.value.yesterday.length + sessions.value.earlier.length
      hasMore.value = total >= pageSize
    }
    
    console.log('History loaded:', {
      today: sessions.value.today.length,
      yesterday: sessions.value.yesterday.length,
      earlier: sessions.value.earlier.length,
      hasMore: hasMore.value
    })
  } catch (error) {
    console.error('Ошибка загрузки истории:', error)
    if (!append) {
      sessions.value = { today: [], yesterday: [], earlier: [] }
    }
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

// Загрузка ещё (при скролле)
async function loadMoreHistory() {
  if (loadingMore.value || !hasMore.value) return
  await loadHistory(true)
}

// Применение фильтров
function applyFilters() {
  // Валидация дат
  if (startDate.value && endDate.value) {
    const start = new Date(startDate.value)
    const end = new Date(endDate.value)
    const now = new Date()
    now.setHours(23, 59, 59, 999) // Конец текущего дня
    
    if (start > end) {
      alert('Дата начала не может быть позже даты окончания!')
      // Меняем даты местами
      const temp = startDate.value
      startDate.value = endDate.value
      endDate.value = temp
    }
    
    if (end > now) {
      alert('Дата окончания не может быть в будущем!')
      endDate.value = new Date().toISOString().split('T')[0]
    }
  }
  
  loadHistory()
}

// Сброс фильтров
function resetFilters() {
  searchQuery.value = ''
  setDefaultDates()
  loadHistory()
}

// Возобновить сессию
function resumeSession(session) {
  localStorage.setItem('resumeSessionId', session.session_id)
  router.push('/')
}

// Форматирование времени
function formatTime(dateString) {
  const date = new Date(dateString)
  return date.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })
}

// Форматирование даты
function formatDate(dateString) {
  const date = new Date(dateString)
  const now = new Date()

  // Если в этом году
  if (date.getFullYear() === now.getFullYear()) {
    return date.toLocaleDateString('ru-RU', { day: '2-digit', month: 'long' })
  }

  // Полный формат
  return date.toLocaleDateString('ru-RU', { day: '2-digit', month: 'long', year: 'numeric' })
}

onMounted(async () => {
  console.log('History.vue: onMounted, начинаем инициализацию...')

  // Ждём инициализации authStore
  if (!authStore.user && authStore.init) {
    console.log('History.vue: вызываем authStore.init()...')
    await authStore.init()
    console.log('History.vue: authStore.init() завершён, user =', authStore.user?.email)
  }

  // Проверяем аутентификацию
  if (!authStore.user) {
    console.log('History.vue: пользователь не аутентифицирован, редирект на /login')
    router.push('/login')
    return
  }

  console.log('History.vue: загружаем историю...')
  setDefaultDates()
  loadHistory()
  
  // Добавляем обработчик скролла для infinite scroll
  window.addEventListener('scroll', handleScroll)
})

// Обработчик скролла для загрузки ещё
function handleScroll() {
  const scrollTop = window.scrollY
  const windowHeight = window.innerHeight
  const documentHeight = document.documentElement.scrollHeight
  
  // Если доскроллили до конца (за 100px до конца)
  if (scrollTop + windowHeight >= documentHeight - 100) {
    loadMoreHistory()
  }
}
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

/* Фильтры и поиск */
.filters-bar {
  display: flex;
  gap: 16px;
  margin-bottom: 32px;
  flex-wrap: wrap;
}

.search-box {
  flex: 1;
  min-width: 280px;
  display: flex;
  align-items: center;
  gap: 12px;
  background: white;
  border: 1px solid #d1d5db;
  border-radius: 12px;
  padding: 12px 16px;
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
  font-size: 15px;
  background: transparent;
}

.date-filters {
  display: flex;
  align-items: center;
  gap: 8px;
}

.date-input {
  padding: 10px 14px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
  background: white;
}

.date-input:focus {
  border-color: #0066cc;
  box-shadow: 0 0 0 3px rgba(0, 102, 204, 0.1);
}

.date-separator {
  color: #9ca3af;
  font-size: 14px;
}

.reset-filters-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 38px;
  height: 38px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  background: white;
  cursor: pointer;
  color: #6b7280;
  transition: all 0.2s;
}

.reset-filters-btn:hover {
  background: #f3f4f6;
  color: #0066cc;
  border-color: #0066cc;
}

/* Загрузка и пустое состояние */
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

/* Группы сессий */
.sessions-group {
  margin-bottom: 32px;
}

.group-title {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #003366;
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 2px solid #e5e7eb;
}

.group-title svg {
  color: #0066cc;
}

.sessions-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.session-card {
  display: block;
  padding: 16px 20px;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.session-card:hover {
  background: #eff6ff;
  border-color: #3b82f6;
  transform: translateX(4px);
  box-shadow: 0 4px 12px rgba(0, 102, 204, 0.1);
}

.session-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
}

.session-info {
  flex: 1;
  min-width: 0;
}

.session-question {
  font-size: 16px;
  font-weight: 500;
  color: #1f2937;
  margin-bottom: 6px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.session-preview {
  display: flex;
  flex-direction: column;
  gap: 8px;
  font-size: 13px;
  color: #6b7280;
}

.preview-label {
  background: #f3f4f6;
  padding: 2px 8px;
  border-radius: 6px;
  font-weight: 500;
  align-self: flex-start;
  flex-shrink: 0;
  font-size: 12px;
}

.preview-messages {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.preview-message {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  line-height: 1.4;
  font-size: 13px;
}

.preview-message.question {
  color: #0066cc;
  font-weight: 500;
}

.preview-message.answer {
  color: #059669;
}

.preview-message.last {
  color: #6b7280;
  font-style: italic;
}

.preview-text {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 600px;
}

.session-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.session-date {
  font-size: 13px;
  color: #9ca3af;
}

.session-time {
  font-size: 13px;
  color: #6b7280;
  background: #f3f4f6;
  padding: 4px 8px;
  border-radius: 6px;
}

.session-arrow {
  color: #d1d5db;
  transition: all 0.2s;
}

.session-card:hover .session-arrow {
  color: #0066cc;
}

/* Индикатор загрузки ещё */
.loading-more {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 32px 0;
  color: #6b7280;
}

.loading-more .spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #e5e7eb;
  border-top-color: #0066cc;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

/* Конец списка */
.end-of-list {
  text-align: center;
  padding: 32px 0;
  color: #9ca3af;
  font-size: 14px;
}

/* Адаптивность */
@media (max-width: 768px) {
  .filters-bar {
    flex-direction: column;
  }
  
  .search-box {
    min-width: 100%;
  }
  
  .date-filters {
    width: 100%;
    justify-content: space-between;
  }
  
  .date-input {
    flex: 1;
    min-width: 0;
  }
  
  .session-header {
    flex-direction: column;
    gap: 12px;
  }
  
  .session-meta {
    width: 100%;
    justify-content: flex-end;
  }
}
</style>
