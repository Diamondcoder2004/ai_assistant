import { defineStore } from 'pinia'
import { authService } from '../services/supabase'
import { ref, computed, watch } from 'vue'
import { supabase } from '../services/supabase'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const profile = ref(null)
  const isLoading = ref(false)
  const error = ref(null)
  const isInitialized = ref(false)

  const isAuthenticated = computed(() => !!user.value)

  // Восстановление из localStorage при создании store
  try {
    const savedUser = localStorage.getItem('auth_user')
    if (savedUser) {
      user.value = JSON.parse(savedUser)
      console.log('User restored from localStorage:', user.value?.email)
    }
  } catch (err) {
    console.error('Error restoring user from localStorage:', err)
    localStorage.removeItem('auth_user')
  }

  // Сохранение в localStorage при изменении user
  watch(user, (newUser) => {
    if (newUser) {
      localStorage.setItem('auth_user', JSON.stringify({
        id: newUser.id,
        email: newUser.email,
        user_metadata: newUser.user_metadata
      }))
    } else {
      localStorage.removeItem('auth_user')
    }
  }, { deep: true })

  async function init() {
    try {
      console.log('Инициализация auth store...')
      
      // Сначала пробуем из Supabase (проверка сессии)
      const currentUser = await authService.getCurrentUser()

      if (currentUser) {
        user.value = currentUser
        console.log('User from Supabase:', user.value?.email)
        await loadProfile()
      } else {
        // Если сессия истекла, но есть в localStorage - очищаем
        if (user.value) {
          console.log('Session expired, clearing localStorage')
          user.value = null
          profile.value = null
        }
      }

      console.log('Auth store инициализирован')
      isInitialized.value = true
    } catch (err) {
      console.error('Auth init error:', err)
      user.value = null
      profile.value = null
      isInitialized.value = true
    }
  }

  async function login(email, password) {
    isLoading.value = true
    error.value = null

    try {
      console.log('Attempting login...')
      const { data, error: authError } = await authService.signIn(email, password)
      console.log('Login response:', data ? '✅ success' : '❌ failed', authError)

      if (authError) {
        throw new Error(authError.message || 'Ошибка авторизации')
      }

      user.value = data.user
      console.log('User set in store:', user.value?.email)

      await loadProfile()
      return { success: true }
    } catch (err) {
      console.error('Login error:', err)
      error.value = err.message || 'Неверный email или пароль'
      return { success: false, error: err.message }
    } finally {
      isLoading.value = false
    }
  }
  async function register(email, password, fullName) {
    isLoading.value = true
    error.value = null

    try {
      const { data, error: authError } = await authService.signUp(email, password, fullName)

      if (authError) {
        throw new Error(authError.message || 'Ошибка регистрации')
      }

      user.value = data.user

      // Явно создаём профиль сразу после регистрации
      if (user.value) {
        try {
          await createProfile()
        } catch (profileErr) {
          console.error('Ошибка создания профиля при регистрации:', profileErr)
          // Не блокируем регистрацию из-за ошибки профиля
        }
      }

      return { success: true }
    } catch (err) {
      error.value = err.message || 'Ошибка при регистрации'
      return { success: false, error: err.message }
    } finally {
      isLoading.value = false
    }
  }

  async function logout() {
    try {
      await authService.signOut()
      user.value = null
      profile.value = null
    } catch (err) {
      error.value = err.message
      console.error('Logout error:', err)
    }
  }

  // Загрузка профиля
  async function loadProfile() {
    if (!user.value) {
      profile.value = null
      return
    }

    try {
      const { data, error: profileError } = await supabase
        .from('profiles')
        .select('*')
        .eq('id', user.value.id)
        .single()

      if (profileError) {
        // Если профиля нет, создаем его
        if (profileError.code === 'PGRST116') {
          await createProfile()
          await loadProfile() // Повторно загружаем
        } else {
          console.error('Profile load error:', profileError)
          throw profileError
        }
      } else {
        profile.value = data
        console.log('Profile loaded:', profile.value)
      }
    } catch (err) {
      console.error('Ошибка загрузки профиля:', err)
      profile.value = null
    }
  }
  // Создание профиля
  async function createProfile() {
    if (!user.value) return null

    try {
      console.log('Creating profile for user:', user.value.id)

      const fullName = user.value.user_metadata?.full_name || user.value.email?.split('@')[0] || ''
      const nameParts = fullName.split(' ')

      const profileData = {
        id: user.value.id,
        email: user.value.email,
        full_name: nameParts[0] || fullName,  // первая часть - имя
        last_name: nameParts.slice(1).join(' ') || '',  // остальное - фамилия
        phone: '',
        telegram: '',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      }

      console.log('Profile data:', profileData)

      const { data, error: createError } = await supabase
        .from('profiles')
        .insert([profileData])
        .select()
        .single()

      if (createError) {
        console.error('Create profile error details:', createError)
        throw createError
      }

      profile.value = data
      console.log('Profile created successfully:', data)
      return data
    } catch (err) {
      console.error('Ошибка создания профиля:', err)
      throw err
    }
  }
  // Обновление профиля
  async function updateProfile(profileData) {
    if (!user.value) {
      return { success: false, error: 'Не авторизован' }
    }

    isLoading.value = true
    try {
      console.log('Updating profile with data:', profileData)

      const { data, error: updateError } = await supabase
        .from('profiles')
        .update({
          full_name: profileData.full_name,
          last_name: profileData.last_name,
          phone: profileData.phone,
          telegram: profileData.telegram,
          updated_at: new Date().toISOString()
        })
        .eq('id', user.value.id)
        .select()
        .single()

      if (updateError) {
        console.error('Update error details:', updateError)
        throw updateError
      }

      profile.value = data
      console.log('Profile updated successfully:', data)
      return { success: true, data }
    } catch (err) {
      console.error('Ошибка обновления профиля:', err)
      return { success: false, error: err.message || 'Ошибка обновления профиля' }
    } finally {
      isLoading.value = false
    }
  }
  return {
    user,
    profile,
    isLoading,
    error,
    isInitialized,
    isAuthenticated,
    init,
    login,
    register,
    logout,
    loadProfile,
    updateProfile
  }
})
