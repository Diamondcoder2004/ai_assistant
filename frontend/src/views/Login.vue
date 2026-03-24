<template>
  <div class="login-page">
    <div class="container">
      <div class="login-card">
        <!-- Шапка формы -->
        <div class="form-header">
          <!-- <img src="../assets/images/logo.png" alt="Логотип" class="form-logo"> -->
          <h1>Вход в систему</h1>
          <p>Введите данные для доступа к ассистенту</p>
        </div>

        <!-- Форма входа -->
        <form @submit.prevent="handleLogin" class="login-form">
          <!-- Сообщение об ошибке -->
          <div v-if="authStore.error" class="error-message">
            {{ authStore.error }}
          </div>

          <!-- Поля формы -->
          <div class="form-group">
            <label for="email">Email</label>
            <input
              id="email"
              v-model="form.email"
              type="email"
              required
              placeholder="example@mail.ru"
              :disabled="authStore.isLoading"
            >
          </div>

          <div class="form-group">
            <label for="password">Пароль</label>
            <input
              id="password"
              v-model="form.password"
              type="password"
              required
              placeholder="Ваш пароль"
              :disabled="authStore.isLoading"
            >
          </div>

          <button type="submit" class="submit-btn" :disabled="authStore.isLoading">
            {{ authStore.isLoading ? 'Вход...' : 'Войти' }}
          </button>

          <div class="form-footer">
            <p>Нет аккаунта? <router-link to="/register">Зарегистрироваться</router-link></p>
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
  email: '',
  password: ''
})

async function handleLogin() {
  const result = await authStore.login(form.value.email, form.value.password)
  if (result.success) {
    router.push('/')
  }
}
</script>

<style scoped>
.login-page {
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

.login-card {
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

.login-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
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

.back-link {
  display: inline-block;
  color: #666;
  font-size: 14px;
}

.back-link:hover {
  color: #0066cc;
}

@media (max-width: 480px) {
  .login-card {
    padding: 30px 20px;
  }

  .form-header h1 {
    font-size: 24px;
  }
}
</style>
