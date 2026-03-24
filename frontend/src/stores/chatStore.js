import { defineStore } from 'pinia'
import { ref } from 'vue'
import { chatService, feedbackService } from '../services/supabase'
import { useAuthStore } from './authStore'

export const useChatStore = defineStore('chat', () => {
  const messages = ref([])
  const isLoading = ref(false)
  const error = ref(null)
  const history = ref([])
  const sessionId = ref(null)               // идентификатор текущего диалога
  const feedbacks = ref({})                  // key: chatId, value: feedback object
  const chatSessions = ref([])               // список сессий чатов
  const currentSessionTitle = ref('')        // заголовок текущей сессии
  const isLoadingHistory = ref(false)        // флаг загрузки истории

  const authStore = useAuthStore()

  // Добавить сообщение в локальный список
  function addMessage(role, content, sources = [], msgSessionId = null, queryId = null) {
    messages.value.push({
      id: Date.now(),
      role,
      content,
      sources,
      sessionId: msgSessionId,
      queryId, // ID конкретного ответа для фидбека
      timestamp: new Date()
    })
  }

  // Начать новый чат (очистить всё и сбросить sessionId)
  function newChat() {
    messages.value = []
    sessionId.value = null
    error.value = null
    currentSessionTitle.value = ''
  }

  // Загрузить сессию чата
  async function loadSession(session) {
    sessionId.value = session.id
    currentSessionTitle.value = session.question?.substring(0, 50) || 'Чат'
    messages.value = [
      {
        id: Date.now() - 1,
        role: 'user',
        content: session.question,
        sources: [],
        sessionId: session.id,
        timestamp: new Date(session.created_at)
      },
      {
        id: Date.now(),
        role: 'assistant',
        content: session.answer,
        sources: session.sources || [],
        sessionId: session.id,
        timestamp: new Date(session.created_at)
      }
    ]
  }

  // Обновить список сессий из истории
  function updateSessionsFromHistory(historyData) {
    // Группируем по session_id
    const sessionsMap = new Map()
    historyData.forEach(chat => {
      if (!chat.session_id) return
      if (!sessionsMap.has(chat.session_id)) {
        sessionsMap.set(chat.session_id, {
          id: chat.session_id,
          question: chat.question,
          answer: chat.answer,
          sources: chat.sources,
          created_at: chat.created_at,
          messagesCount: 1
        })
      } else {
        const session = sessionsMap.get(chat.session_id)
        session.messagesCount++
        // Обновляем последний вопрос/ответ
        session.question = chat.question
        session.answer = chat.answer
        session.sources = chat.sources
      }
    })
    chatSessions.value = Array.from(sessionsMap.values()).sort(
      (a, b) => new Date(b.created_at) - new Date(a.created_at)
    )
  }

  // Отправить вопрос (без streaming)
  async function sendQuestion(question, parameters = {}) {
    isLoading.value = true
    error.value = null

    try {
      addMessage('user', question)

      const params = {
        k: parameters.k || 10,
        temperature: parameters.temperature || 0.8,
        max_tokens: parameters.max_tokens || 2000,
        min_score: parameters.min_score || 0.0
      }

      // Добавляем session_id только если он есть, иначе не передаём
      if (sessionId.value) {
        params.session_id = String(sessionId.value)
        console.log('sendQuestion: sending with session_id:', params.session_id)
      } else {
        console.log('sendQuestion: no session_id, starting new session')
      }

      // Запускаем обычный запрос
      const response = await chatService.sendQuery(question, params)
      console.log('sendQuestion: response session_id:', response.session_id)

      // Сохраняем session_id
      if (response.session_id) {
        sessionId.value = String(response.session_id)
        console.log('sendQuestion: saved session_id:', sessionId.value)
      }

      // Добавляем сообщение с ответом и источниками, сохраняем query_id для фидбека
      addMessage('assistant', response.answer, response.sources || [], response.session_id, response.query_id)

      return response
    } catch (err) {
      error.value = err.message || 'Ошибка при обработке вопроса'
      console.error('Send question error:', err)
      addMessage('assistant', 'Извините, произошла ошибка. Пожалуйста, попробуйте позже.')
      throw err
    } finally {
      isLoading.value = false
    }
  }

  // Отправить фидбек (лайк/дизлайк/звезда)
  async function submitFeedback(queryId, type, rating = null, comment = null) {
    // Проверка на уже существующий фидбек того же типа
    const existing = feedbacks.value[queryId]
    if (existing && existing.feedback_type === type) {
      // Если такой же тип — ничего не делаем (уже проголосовано)
      return existing
    }

    try {
      // Если есть существующий фидбек — сначала удаляем его
      if (existing) {
        await feedbackService.deleteFeedback(queryId)
      }

      const result = await feedbackService.createFeedback(queryId, type, rating, comment)
      feedbacks.value[queryId] = result
      return result
    } catch (err) {
      console.error('Failed to submit feedback:', err)
      throw err
    }
  }

  // Удалить фидбек
  async function removeFeedback(queryId) {
    try {
      await feedbackService.deleteFeedback(queryId)
      delete feedbacks.value[queryId]
    } catch (err) {
      console.error('Failed to delete feedback:', err)
      throw err
    }
  }

  // Загрузить фидбек для конкретного query
  async function loadFeedback(queryId) {
    try {
      const result = await feedbackService.getFeedback(queryId)
      if (result) feedbacks.value[queryId] = result
    } catch (err) {
      console.error('Failed to load feedback:', err)
    }
  }

  // Загрузить историю чатов пользователя (с пагинацией)
  async function loadHistory(limit = 20, offset = 0, append = false) {
    console.log('loadHistory called, isLoadingHistory:', isLoadingHistory.value, 'history.length:', history.value?.length)

    if (!authStore.user) {
      console.log('User not authenticated, skipping history load')
      return
    }

    // Защита от повторных вызовов
    if (isLoadingHistory.value) {
      console.log('History already loading, skipping')
      return
    }

    // Если история уже загружена и это не append, не загружаем снова
    if (history.value.length > 0 && !append && offset === 0) {
      console.log('History already loaded:', history.value.length, 'items')
      return
    }

    isLoadingHistory.value = true

    try {
      const data = await chatService.getHistory(limit, offset)
      console.log('loadHistory: received data:', data?.length, 'items')
      
      if (append) {
        history.value = [...history.value, ...(data || [])]
      } else {
        history.value = data || []
      }
      
      console.log('loadHistory: set history.value to:', history.value.length, 'items')
      console.log('Chat history loaded:', history.value.length, 'items')
      console.log('History data:', history.value)
      
      // Обновляем сессии из истории
      updateSessionsFromHistory(history.value)
      
      return data?.length || 0 // Возвращаем количество загруженных элементов
    } catch (err) {
      console.error('Failed to load chat history:', err)
      throw err
    } finally {
      isLoadingHistory.value = false
    }
  }

  // Загрузить больше истории (для infinite scroll)
  async function loadMoreHistory(pageSize = 20) {
    const currentLength = history.value.length
    const loadedCount = await loadHistory(pageSize, currentLength, true)
    return loadedCount
  }

  // Очистить текущий чат (синоним newChat)
  function clearChat() {
    newChat()
  }

  return {
    messages,
    isLoading,
    error,
    history,
    sessionId,
    feedbacks,
    chatSessions,
    currentSessionTitle,
    isLoadingHistory,
    addMessage,
    sendQuestion,
    newChat,
    clearChat,
    loadSession,
    loadHistory,
    loadMoreHistory,
    submitFeedback,
    removeFeedback,
    loadFeedback
  }
})
