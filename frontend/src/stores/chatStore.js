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

  const STORAGE_KEY_MESSAGES = 'chat_messages'
  const STORAGE_KEY_SESSION_ID = 'chat_session_id'
  const STORAGE_KEY_SESSION_TITLE = 'chat_session_title'
  const STORAGE_KEY_HISTORY_SESSIONS = 'chat_history_sessions'
  const STORAGE_KEY_HISTORY_LOADED_AT = 'chat_history_loaded_at'

  const authStore = useAuthStore()

  // Сохранение состояния в sessionStorage
  function saveToStorage() {
    try {
      console.log('[chatStore.saveToStorage] Called, messages:', messages.value?.length || 0, 'sessionId:', sessionId.value)

      if (messages.value.length > 0) {
        sessionStorage.setItem(STORAGE_KEY_MESSAGES, JSON.stringify(messages.value))
        console.log('[chatStore.saveToStorage] Saved messages:', messages.value.length)
      } else {
        sessionStorage.removeItem(STORAGE_KEY_MESSAGES)
        console.log('[chatStore.saveToStorage] Removed messages (empty)')
      }

      if (sessionId.value) {
        sessionStorage.setItem(STORAGE_KEY_SESSION_ID, String(sessionId.value))
        console.log('[chatStore.saveToStorage] Saved session_id:', sessionId.value)
      } else {
        sessionStorage.removeItem(STORAGE_KEY_SESSION_ID)
        console.log('[chatStore.saveToStorage] Removed session_id (null)')
      }

      if (currentSessionTitle.value) {
        sessionStorage.setItem(STORAGE_KEY_SESSION_TITLE, currentSessionTitle.value)
        console.log('[chatStore.saveToStorage] Saved title:', currentSessionTitle.value)
      } else {
        sessionStorage.removeItem(STORAGE_KEY_SESSION_TITLE)
        console.log('[chatStore.saveToStorage] Removed title (empty)')
      }
      
      // Сохраняем историю сессий для History.vue
      if (chatSessions.value.length > 0) {
        sessionStorage.setItem(STORAGE_KEY_HISTORY_SESSIONS, JSON.stringify(chatSessions.value))
        sessionStorage.setItem(STORAGE_KEY_HISTORY_LOADED_AT, Date.now().toString())
        console.log('[chatStore.saveToStorage] Saved history sessions:', chatSessions.value.length)
      }
      
      console.log('[chatStore.saveToStorage] Complete')
    } catch (err) {
      console.error('[chatStore.saveToStorage] Error:', err)
    }
  }

  // Восстановление состояния из sessionStorage
  function restoreFromStorage() {
    try {
      console.log('[chatStore.restoreFromStorage] Called')
      
      const savedMessages = sessionStorage.getItem(STORAGE_KEY_MESSAGES)
      const savedSessionId = sessionStorage.getItem(STORAGE_KEY_SESSION_ID)
      const savedTitle = sessionStorage.getItem(STORAGE_KEY_SESSION_TITLE)
      const savedHistorySessions = sessionStorage.getItem(STORAGE_KEY_HISTORY_SESSIONS)
      const historyLoadedAt = sessionStorage.getItem(STORAGE_KEY_HISTORY_LOADED_AT)
      
      console.log('[chatStore.restoreFromStorage] Found messages:', !!savedMessages, 'sessionId:', !!savedSessionId, 'title:', !!savedTitle, 'historySessions:', !!savedHistorySessions)

      if (savedMessages) {
        messages.value = JSON.parse(savedMessages)
        console.log('[chatStore.restoreFromStorage] Restored messages:', messages.value.length, 'messages')
      } else {
        console.log('[chatStore.restoreFromStorage] No saved messages')
      }

      if (savedSessionId) {
        sessionId.value = savedSessionId
        console.log('[chatStore.restoreFromStorage] Restored session_id:', sessionId.value)
      } else {
        console.log('[chatStore.restoreFromStorage] No saved session_id')
      }

      if (savedTitle) {
        currentSessionTitle.value = savedTitle
        console.log('[chatStore.restoreFromStorage] Restored title:', currentSessionTitle.value)
      } else {
        console.log('[chatStore.restoreFromStorage] No saved title')
      }
      
      // Восстанавливаем историю сессий если она загружена недавно (< 5 минут)
      if (savedHistorySessions && historyLoadedAt) {
        const loadedTime = parseInt(historyLoadedAt)
        const now = Date.now()
        const ageMinutes = (now - loadedTime) / 1000 / 60
        
        if (ageMinutes < 5) {
          chatSessions.value = JSON.parse(savedHistorySessions)
          console.log('[chatStore.restoreFromStorage] Restored history sessions:', chatSessions.value.length, '(age:', Math.round(ageMinutes * 10) / 10, 'min)')
        } else {
          console.log('[chatStore.restoreFromStorage] History too old, clearing:', ageMinutes.toFixed(1), 'min')
          sessionStorage.removeItem(STORAGE_KEY_HISTORY_SESSIONS)
          sessionStorage.removeItem(STORAGE_KEY_HISTORY_LOADED_AT)
        }
      } else {
        console.log('[chatStore.restoreFromStorage] No saved history sessions')
      }

      const result = !!(savedMessages || savedSessionId || savedHistorySessions)
      console.log('[chatStore.restoreFromStorage] Result:', result)
      return result
    } catch (err) {
      console.error('[chatStore.restoreFromStorage] Error:', err)
      return false
    }
  }

  // Очистка sessionStorage
  function clearStorage() {
    try {
      sessionStorage.removeItem(STORAGE_KEY_MESSAGES)
      sessionStorage.removeItem(STORAGE_KEY_SESSION_ID)
      sessionStorage.removeItem(STORAGE_KEY_SESSION_TITLE)
    } catch (err) {
      console.error('Error clearing chat storage:', err)
    }
  }

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
    // Сохраняем после добавления сообщения
    saveToStorage()
  }

  // Начать новый чат (очистить всё и сбросить sessionId)
  function newChat() {
    messages.value = []
    sessionId.value = null
    error.value = null
    currentSessionTitle.value = ''
    clearStorage()
  }

  // Загрузить сессию чата
  async function loadSession(session) {
    sessionId.value = session.id
    currentSessionTitle.value = session.question?.substring(0, 50) || 'Чат'

    // Если сессия содержит массив messages (многосообщенческая история) — загружаем все
    if (session.messages && session.messages.length > 0) {
      const msgs = []
      let baseId = Date.now()
      session.messages.forEach((msg, idx) => {
        msgs.push({
          id: baseId + idx * 2,
          role: 'user',
          content: msg.question,
          sources: [],
          sessionId: session.id,
          timestamp: new Date(msg.created_at)
        })
        msgs.push({
          id: baseId + idx * 2 + 1,
          role: 'assistant',
          content: msg.answer,
          sources: msg.sources || [],
          sessionId: session.id,
          timestamp: new Date(msg.created_at)
        })
      })
      messages.value = msgs
    } else {
      // Fallback: одна пара Q&A (старый формат)
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
    saveToStorage()
  }

  // Обновить список сессий из истории
  function updateSessionsFromHistory(historyData) {
    // Группируем по session_id, сохраняя ВСЕ сообщения
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
          messagesCount: 1,
          messages: [{
            question: chat.question,
            answer: chat.answer,
            sources: chat.sources,
            created_at: chat.created_at
          }]
        })
      } else {
        const session = sessionsMap.get(chat.session_id)
        session.messagesCount++
        session.messages.push({
          question: chat.question,
          answer: chat.answer,
          sources: chat.sources,
          created_at: chat.created_at
        })
        // Обновляем заголовок на последнее сообщение
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
    console.log('[chatStore.sendQuestion] Called with:', question.substring(0, 50), 'sessionId:', sessionId.value)
    
    isLoading.value = true
    error.value = null

    try {
      addMessage('user', question)
      console.log('[chatStore.sendQuestion] Added user message, messages count:', messages.value.length)

      const params = {
        k: parameters.k || 10,
        temperature: parameters.temperature || 0.8,
        max_tokens: parameters.max_tokens || 2000,
        min_score: parameters.min_score || 0.0,
        mode: parameters.mode || 'standard'
      }

      // Добавляем session_id только если он есть, иначе не передаём
      if (sessionId.value) {
        params.session_id = String(sessionId.value)
        console.log('[chatStore.sendQuestion] sending with session_id:', params.session_id)
      } else {
        console.log('[chatStore.sendQuestion] no session_id, starting new session')
      }

      // Запускаем обычный запрос
      const response = await chatService.sendQuery(question, params)
      console.log('[chatStore.sendQuestion] response session_id:', response.session_id)

      // Сохраняем session_id
      if (response.session_id) {
        sessionId.value = String(response.session_id)
        console.log('[chatStore.sendQuestion] saved session_id:', sessionId.value)
      }

      // Добавляем сообщение с ответом и источниками, сохраняем query_id для фидбека
      addMessage('assistant', response.answer, response.sources || [], response.session_id, response.query_id)
      console.log('[chatStore.sendQuestion] Added assistant message, messages count:', messages.value.length)

      return response
    } catch (err) {
      error.value = err.message || 'Ошибка при обработке вопроса'
      console.error('[chatStore.sendQuestion] Error:', err)
      addMessage('assistant', 'Извините, произошла ошибка. Пожалуйста, попробуйте позже.')
      throw err
    } finally {
      isLoading.value = false
      console.log('[chatStore.sendQuestion] Complete, isLoading:', isLoading.value)
    }
  }

  // Отправить фидбек (лайк/дизлайк/звезда)
  async function submitFeedback(queryId, type, rating = null, comment = null) {
    // Конвертируем queryId в строку (бэкенд ожидает string)
    const queryIdStr = String(queryId)
    
    // Проверка на уже существующий фидбек того же типа
    const existing = feedbacks.value[queryIdStr]
    if (existing && existing.feedback_type === type) {
      // Если такой же тип — ничего не делаем (уже проголосовано)
      return existing
    }

    try {
      // Если есть существующий фидбек — сначала удаляем его
      if (existing) {
        await feedbackService.deleteFeedback(queryIdStr)
      }

      const result = await feedbackService.createFeedback(queryIdStr, type, rating, comment)
      feedbacks.value[queryIdStr] = result
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
    loadFeedback,
    restoreFromStorage,
    clearStorage,
    saveToStorage
  }
})
