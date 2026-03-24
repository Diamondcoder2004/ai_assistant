<template>
  <div class="register-page">
    <div class="container">
      <div class="register-card">
        <!-- Шапка формы -->
        <div class="form-header">
          <!-- <img src="../assets/images/logo.png" alt="Логотип" class="form-logo"> -->
          <h1>Регистрация</h1>
          <p>Создайте аккаунт для доступа к ассистенту</p>
        </div>

        <!-- Форма регистрации -->
        <form @submit.prevent="handleRegister" class="register-form">
          <!-- Сообщения об ошибках -->
          <div v-if="error" class="error-message">
            {{ error }}
          </div>

          <div v-if="success" class="success-message">
            Регистрация успешна! Выполняется вход...
          </div>

          <!-- Поля формы -->
            <div class="form-group">
              <label for="firstName">Имя *</label>
              <input
                id="firstName"
                v-model="form.firstName"
                type="text"
                required
                placeholder="Иван"
                :disabled="loading"
              >
            </div>

            <div class="form-group">
              <label for="lastName">Фамилия *</label>
              <input
                id="lastName"
                v-model="form.lastName"
                type="text"
                required
                placeholder="Иванов"
                :disabled="loading"
              >
            </div>

          <div class="form-group">
            <label for="email">Email *</label>
            <input
              id="email"
              v-model="form.email"
              type="email"
              required
              placeholder="example@mail.ru"
              :disabled="loading"
            >
          </div>

          <div class="form-group">
            <label for="password">Пароль *</label>
            <input
              id="password"
              v-model="form.password"
              type="password"
              required
              placeholder="Не менее 6 символов"
              :disabled="loading"
            >
          </div>

          <div class="form-group">
            <label for="confirmPassword">Подтвердите пароль *</label>
            <input
              id="confirmPassword"
              v-model="form.confirmPassword"
              type="password"
              required
              placeholder="Повторите пароль"
              :disabled="loading"
            >
          </div>

          <button type="submit" class="submit-btn" :disabled="loading">
            {{ loading ? 'Регистрация...' : 'Зарегистрироваться' }}
          </button>

          <div class="form-footer">
            <p>Уже есть аккаунт? <router-link to="/login">Войти</router-link></p>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/authStore'

const router = useRouter()
const authStore = useAuthStore()

const form = ref({
  firstName: '',
  lastName: '',
  email: '',
  password: '',
  confirmPassword: ''
})
const loading = ref(false)
const error = ref('')
const success = ref(false)

async function handleRegister() {
  // Валидация
  if (form.value.password !== form.value.confirmPassword) {
    error.value = 'Пароли не совпадают'
    return
  }

  if (form.value.password.length < 6) {
    error.value = 'Пароль должен быть не менее 6 символов'
    return
  }

  if (!form.value.firstName.trim() || !form.value.lastName.trim()) {
    error.value = 'Имя и фамилия обязательны для заполнения'
    return
  }

  loading.value = true
  error.value = ''

  try {
    // Сохраняем данные для входа
    const email = form.value.email
    const password = form.value.password

    // Формируем полное имя для метаданных
    const fullName = `${form.value.firstName} ${form.value.lastName}`.trim()

    const result = await authStore.register(
      email,
      password,
      fullName  // Передаем полное имя в метаданные
    )

    if (result.success) {
      success.value = true

      // Пытаемся залогиниться
      const loginResult = await authStore.login(email, password)

      if (loginResult.success) {
        // Даем время на создание профиля
        setTimeout(() => {
          router.push('/')
        }, 1000)
      } else {
        setTimeout(() => router.push('/login'), 2000)
      }
    } else {
      error.value = result.error || 'Ошибка регистрации'
    }
  } catch (err) {
    console.error('Registration error:', err)
    error.value = 'Произошла ошибка при регистрации'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.register-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f5f5;
  padding: 20px;
}

.container {
  width: 100%;
  max-width: 480px;
}

.register-card {
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  padding: 40px;
}

.form-header {
  text-align: center;
  margin-bottom: 30px;
}

.form-logo {
  height: 60px;
  margin-bottom: 20px;
}

.form-header h1 {
  color: #003366;
  margin: 0 0 10px 0;
  font-size: 28px;
}

.form-header p {
  color: #666;
  margin: 0;
  font-size: 16px;
}

.register-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-row {
  display: flex;
  gap: 15px;
}

.form-row .form-group {
  flex: 1;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-weight: 500;
  color: #333;
  font-size: 14px;
}

.form-group input {
  padding: 12px 15px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 16px;
  transition: border-color 0.2s;
}

.form-group input:focus {
  outline: none;
  border-color: #0066cc;
}

.form-group input:disabled {
  background: #f9f9f9;
  cursor: not-allowed;
}

.error-message {
  background: #fee;
  color: #c33;
  padding: 12px 15px;
  border-radius: 6px;
  border: 1px solid #fcc;
  font-size: 14px;
}

.success-message {
  background: #dfd;
  color: #373;
  padding: 12px 15px;
  border-radius: 6px;
  border: 1px solid #afa;
  font-size: 14px;
}

.submit-btn {
  background: #0066cc;
  color: white;
  border: none;
  padding: 14px;
  border-radius: 6px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
  margin-top: 10px;
}

.submit-btn:hover:not(:disabled) {
  background: #0052a3;
}

.submit-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.form-footer {
  text-align: center;
  padding-top: 20px;
  border-top: 1px solid #eee;
}

.form-footer p {
  color: #666;
  margin: 0 0 15px 0;
}

.form-footer a {
  color: #0066cc;
  text-decoration: none;
}

.form-footer a:hover {
  text-decoration: underline;
}

@media (max-width: 480px) {
  .register-card {
    padding: 30px 20px;
  }

  .form-header h1 {
    font-size: 24px;
  }

  .form-row {
    flex-direction: column;
    gap: 20px;
  }
}
</style>
