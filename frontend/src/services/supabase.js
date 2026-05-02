import { createClient } from '@supabase/supabase-js'

// Безопасно получаем переменные окружения
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || 'http://localhost:54321'
const supabaseAnonKey =
  import.meta.env.VITE_SUPABASE_ANON_KEY ||
  'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0'

// Флаг для тестового режима (без Supabase)
const TEST_MODE = import.meta.env.VITE_TEST_MODE === 'true'

console.log('Supabase URL:', supabaseUrl)
console.log('Test Mode:', TEST_MODE ? '✅ ON (Mock Auth)' : '❌ OFF')

// Создаем клиент с обработкой ошибок
let supabase = null
if (!TEST_MODE) {
  try {
    supabase = createClient(supabaseUrl, supabaseAnonKey, {
      auth: {
        autoRefreshToken: true,
        persistSession: true,
        detectSessionInUrl: true,
      },
    })
    console.log('Supabase client created successfully')
  } catch (error) {
    console.error('Error creating Supabase client:', error)
  }
} else {
  console.warn('⚠️ TEST MODE: Supabase disabled, using mock authentication')
}

// Функции для работы с аутентификацией
export const authService = {
  async signUp(email, password, fullName) {
    if (TEST_MODE) {
      // Mock регистрация
      const user = { id: 'test-user-id', email, user_metadata: { full_name: fullName } }
      const session = { access_token: 'mock-jwt-token', user }
      localStorage.setItem('mock-user', JSON.stringify(user))
      localStorage.setItem('mock-session', JSON.stringify(session))
      return { data: { user, session }, error: null }
    }

    if (!supabase) {
      console.warn('Supabase client not initialized')
      return { data: null, error: 'Supabase not initialized' }
    }

    try {
      const { data, error } = await supabase.auth.signUp({
        email,
        password,
        options: {
          data: {
            full_name: fullName,
          },
        },
      })
      return { data, error }
    } catch (error) {
      console.error('Sign up error:', error)
      return { data: null, error }
    }
  },

  async signIn(email, password) {
    if (TEST_MODE) {
      // Mock вход
      const user = { id: 'test-user-id', email, user_metadata: { full_name: 'Test User' } }
      const session = { access_token: 'mock-jwt-token', user }
      localStorage.setItem('mock-user', JSON.stringify(user))
      localStorage.setItem('mock-session', JSON.stringify(session))
      return { data: { user, session }, error: null }
    }

    if (!supabase) {
      console.warn('Supabase client not initialized')
      return { data: null, error: 'Supabase not initialized' }
    }

    try {
      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password,
      })
      return { data, error }
    } catch (error) {
      console.error('Sign in error:', error)
      return { data: null, error }
    }
  },

  async signOut() {
    if (TEST_MODE) {
      // Mock выход
      localStorage.removeItem('mock-user')
      localStorage.removeItem('mock-session')
      return { error: null }
    }

    if (!supabase) {
      console.warn('Supabase client not initialized')
      return { error: 'Supabase not initialized' }
    }

    try {
      const { error } = await supabase.auth.signOut()
      return { error }
    } catch (error) {
      console.error('Sign out error:', error)
      return { error }
    }
  },

  async getCurrentUser() {
    if (TEST_MODE) {
      // Mock пользователь
      const user = localStorage.getItem('mock-user')
      return user ? JSON.parse(user) : null
    }

    if (!supabase) {
      console.warn('Supabase client not initialized')
      return null
    }

    try {
      const {
        data: { user },
      } = await supabase.auth.getUser()
      return user
    } catch (error) {
      console.error('Get current user error:', error)
      return null
    }
  },

  async getSession() {
    if (TEST_MODE) {
      // Mock сессия
      const session = localStorage.getItem('mock-session')
      if (session) {
        const parsed = JSON.parse(session)
        console.log('Mock session: ✅ exists')
        console.log('Token preview:', parsed.access_token.substring(0, 20) + '...')
        return parsed
      }
      return null
    }

    if (!supabase) {
      console.warn('Supabase client not initialized')
      return null
    }

    try {
      await supabase.auth.getUser()
      const {
        data: { session },
      } = await supabase.auth.getSession()
      console.log('Session from Supabase:', session ? '✅ exists' : '❌ null')
      if (session) {
        console.log('Token preview:', session.access_token.substring(0, 20) + '...')
      }
      return session
    } catch (error) {
      console.error('Get session error:', error)
      return null
    }
  },
}

// Сервис для работы с фидбеком (через FastAPI)
export const feedbackService = {
  async createFeedback(queryId, feedbackType, rating, comment) {
    const session = await authService.getSession()
    if (!session) throw new Error('Not authenticated')

    const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/feedback`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${session.access_token}`,
      },
      body: JSON.stringify({
        query_id: queryId,
        feedback_type: feedbackType,
        rating,
        comment,
      }),
    })

    if (!response.ok) {
      const error = await response.text()
      throw new Error(`Feedback error: ${error}`)
    }

    return response.json()
  },

  async getFeedback(queryId) {
    const session = await authService.getSession()
    if (!session) throw new Error('Not authenticated')

    const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/feedback/${queryId}`, {
      headers: {
        Authorization: `Bearer ${session.access_token}`,
      },
    })

    if (!response.ok) {
      if (response.status === 404) return null
      const error = await response.text()
      throw new Error(`Feedback error: ${error}`)
    }

    return response.json()
  },

  async deleteFeedback(queryId) {
    const session = await authService.getSession()
    if (!session) throw new Error('Not authenticated')

    const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/feedback/${queryId}`, {
      method: 'DELETE',
      headers: {
        Authorization: `Bearer ${session.access_token}`,
      },
    })

    if (!response.ok) {
      const error = await response.text()
      throw new Error(`Feedback error: ${error}`)
    }

    return response.json()
  },
}

// Сервис для работы с чатами (FastAPI)
export const chatService = {
  async sendQuery(query, params = {}) {
    const session = await authService.getSession()
    console.log('Session in sendQuery:', session ? '✅' : '❌')
    if (!session) throw new Error('Not authenticated')

    console.log('Sending token:', session.access_token.substring(0, 20) + '...')

    // Создаём AbortController для установки таймаута
    const controller = new AbortController()
    // Таймаут 120 секунд для долгих запросов к LLM
    const timeoutId = setTimeout(() => controller.abort(), 120000)

    try {
      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${session.access_token}`,
        },
        body: JSON.stringify({
          query,
          k: params.k || 10,
          temperature: params.temperature || 0.8,
          max_tokens: params.max_tokens || 2000,
          min_score: params.min_score || 0.0,
          mode: params.mode || 'standard',
          session_id: params.session_id || null,
        }),
        signal: controller.signal,
      })

      clearTimeout(timeoutId)

      console.log('Response status:', response.status)

      if (!response.ok) {
        const error = await response.text()
        console.error('API error response:', error)
        throw new Error(`API error: ${error}`)
      }

      return response.json()
    } catch (err) {
      clearTimeout(timeoutId)
      if (err.name === 'AbortError') {
        throw new Error('Превышено время ожидания ответа. Попробуйте позже.')
      }
      throw err
    }
  },

  // Streaming запрос с чтением токенов (SSE)
  async sendQueryStream(query, params = {}, onToken, onSources, onSessionId, onStatus) {
    const session = await authService.getSession()
    if (!session) throw new Error('Not authenticated')

    // Создаём AbortController для установки таймаута
    const controller = new AbortController()
    // Таймаут 120 секунд для долгих запросов к LLM
    const timeoutId = setTimeout(() => controller.abort(), 120000)

    try {
      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/query/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${session.access_token}`,
        },
        body: JSON.stringify({
          query,
          k: params.k || 10,
          temperature: params.temperature || 0.8,
          max_tokens: params.max_tokens || 2000,
          min_score: params.min_score || 0.0,
          mode: params.mode || 'standard',
          session_id: params.session_id || null,
        }),
        signal: controller.signal,
      })

      clearTimeout(timeoutId)

      if (!response.ok) {
        const error = await response.text()
        throw new Error(`API error: ${error}`)
      }

      // Читаем поток данных (SSE format)
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      let sources = []
      let sessionId = null
      let currentEvent = null

      try {
        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          const chunk = decoder.decode(value, { stream: true })
          buffer += chunk

          // Разделяем по строкам SSE формата
          const lines = buffer.split('\n')
          buffer = lines.pop() // Последняя неполная строка остаётся в буфере

          for (const line of lines) {
            // Пропускаем пустые строки
            if (!line.trim()) continue

            // Обработка event: строки
            if (line.startsWith('event: ')) {
              currentEvent = line.slice(7).trim()
              continue
            }

            // Обработка data: строки
            if (line.startsWith('data: ')) {
              const data = line.slice(6).trim()

              try {
                // Для token событий данные могут быть простой строкой
                if (currentEvent === 'token') {
                  onToken?.(data)
                  continue
                }

                // Для остальных событий парсим JSON
                if (data.startsWith('{') || data.startsWith('[')) {
                  const parsed = JSON.parse(data)

                  if (currentEvent === 'sources') {
                    sources = parsed
                    onSources?.(sources)
                  } else if (currentEvent === 'session_id') {
                    sessionId = parsed
                    onSessionId?.(sessionId)
                  } else if (currentEvent === 'status') {
                    onStatus?.(parsed)
                  } else if (currentEvent === 'done') {
                    // Завершение, данные - полный ответ
                    return {
                      session_id: sessionId,
                      sources,
                      answer: parsed,
                    }
                  } else if (currentEvent === 'error') {
                    throw new Error(parsed)
                  }
                }
              } catch {
                // Игнорируем ошибки парсинга для неполных данных
              }
            }
          }
        }
      } catch (err) {
        console.error('Stream reading error:', err)
        throw err
      }

      return {
        session_id: sessionId,
        sources,
      }
    } catch (err) {
      clearTimeout(timeoutId)
      if (err.name === 'AbortError') {
        throw new Error('Превышено время ожидания ответа. Попробуйте позже.')
      }
      throw err
    }
  },

  async getHistory(limit = 20, offset = 0) {
    const session = await authService.getSession()
    if (!session) throw new Error('Not authenticated')

    const apiBase =
      location.hostname === 'localhost'
        ? 'http://localhost:8880'
        : import.meta.env.VITE_API_BASE_URL
    const response = await fetch(`${apiBase}/history?limit=${limit}&offset=${offset}`, {
      headers: {
        Authorization: `Bearer ${session.access_token}`,
      },
    })

    if (!response.ok) {
      const error = await response.text()
      throw new Error(`API error: ${error}`)
    }

    return response.json()
  },

  async getHistorySessions(
    search = null,
    startDate = null,
    endDate = null,
    limit = 20,
    offset = 0,
  ) {
    console.log('getHistorySessions: получение сессии...')
    const session = await authService.getSession()
    console.log('getHistorySessions: session =', session ? '✅ exists' : '❌ null')

    if (!session) {
      console.error('getHistorySessions: Not authenticated')
      throw new Error('Not authenticated')
    }

    const params = new URLSearchParams()
    if (search) params.append('search', search)
    if (startDate) params.append('start_date', startDate)
    if (endDate) params.append('end_date', endDate)
    params.append('limit', limit.toString())
    params.append('offset', offset.toString())

    const url = `${import.meta.env.VITE_API_BASE_URL}/history/sessions?${params}`
    console.log('getHistorySessions: URL =', url)
    console.log(
      'getHistorySessions: Token preview =',
      session.access_token.substring(0, 20) + '...',
    )

    const response = await fetch(url, {
      headers: {
        Authorization: `Bearer ${session.access_token}`,
      },
    })

    console.log('getHistorySessions: Response status =', response.status)

    if (!response.ok) {
      const error = await response.text()
      console.error('getHistorySessions: API error =', error)
      throw new Error(`API error: ${error}`)
    }

    return response.json()
  },
}

// Сервис для работы с профилем (Supabase напрямую)
export const profileService = {
  async getProfile(userId) {
    if (!supabase) {
      console.warn('Supabase client not initialized')
      return { data: null, error: 'Supabase not initialized' }
    }

    try {
      const { data, error } = await supabase.from('profiles').select('*').eq('id', userId).single()

      // Если таблицы нет, создадим её автоматически через API позже
      if (error && error.code === '42P01') {
        console.warn('Profiles table does not exist. Create it in Supabase Studio.')
        return { data: null, error: 'Profiles table not created yet' }
      }

      return { data, error }
    } catch (error) {
      console.error('Get profile error:', error)
      return { data: null, error }
    }
  },

  async updateProfile(userId, profileData) {
    if (!supabase) {
      console.warn('Supabase client not initialized')
      return { data: null, error: 'Supabase not initialized' }
    }

    try {
      const { data, error } = await supabase
        .from('profiles')
        .update({
          ...profileData,
          updated_at: new Date().toISOString(),
        })
        .eq('id', userId)
        .select()
        .single()
      return { data, error }
    } catch (error) {
      console.error('Update profile error:', error)
      return { data: null, error }
    }
  },

  async createProfile(userId, fullName) {
    if (!supabase) {
      console.warn('Supabase client not initialized')
      return { data: null, error: 'Supabase not initialized' }
    }

    try {
      const { data, error } = await supabase
        .from('profiles')
        .insert([
          {
            id: userId,
            full_name: fullName,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          },
        ])
        .select()
        .single()
      return { data, error }
    } catch (error) {
      console.error('Create profile error:', error)
      return { data: null, error }
    }
  },
}

export { supabase }
