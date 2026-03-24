<template>
  <header class="header">
    <div class="header-content">
      <!-- Навигация -->
      <nav class="nav">
        <router-link to="/" class="nav-link">Главная</router-link>
        <router-link to="/history" class="nav-link">История</router-link>
        <router-link to="/profile" class="nav-link">Профиль</router-link>
      </nav>

      <!-- Кнопки входа/выхода и настроек -->
      <div class="auth">
        <button v-if="authStore.user" @click="showSettings = true" class="btn-settings" title="Настройки">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="3"/>
            <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
          </svg>
        </button>
        
        <span v-if="authStore.user" class="user-email">{{ authStore.user.email }}</span>
        <button v-if="authStore.user" @click="logout" class="btn-logout">Выйти</button>
        <router-link v-else to="/login" class="btn-login">Войти</router-link>
      </div>
    </div>

    <!-- Модальное окно настроек -->
    <SettingsModal v-if="showSettings" @close="showSettings = false" />
  </header>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/authStore'
import SettingsModal from './settings/SettingsModal.vue'

const router = useRouter()
const authStore = useAuthStore()
const showSettings = ref(false)

async function logout() {
  await authStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.header {
  background: white;
  border-bottom: 1px solid #ddd;
  padding: 15px 20px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.header-content {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  text-decoration: none;
}

.logo-img {
  height: 40px;
  width: auto;
}

.logo-text {
  font-size: 18px;
  font-weight: 600;
  color: #003366;
}

.nav {
  display: flex;
  gap: 30px;
}

.nav-link {
  color: #333;
  text-decoration: none;
  padding: 8px 0;
  font-size: 16px;
  position: relative;
}

.nav-link:hover {
  color: #0066cc;
}

.nav-link.router-link-active {
  color: #0066cc;
  font-weight: 500;
}

.nav-link.router-link-active::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: #0066cc;
}

.auth {
  display: flex;
  align-items: center;
  gap: 15px;
}

.btn-settings {
  background: #f3f4f6;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  padding: 8px;
  cursor: pointer;
  color: #4b5563;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-settings:hover {
  background: #e5e7eb;
  border-color: #9ca3af;
  color: #1f2937;
}

.user-email {
  font-size: 14px;
  color: #666;
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.btn-logout, .btn-login {
  background: #0066cc;
  color: white;
  border: none;
  padding: 8px 20px;
  border-radius: 4px;
  cursor: pointer;
  text-decoration: none;
  font-size: 14px;
  transition: background 0.2s;
}

.btn-logout:hover, .btn-login:hover {
  background: #0052a3;
}

@media (max-width: 768px) {
  .header-content {
    flex-direction: column;
    gap: 15px;
  }

  .nav {
    gap: 15px;
  }

  .logo-text {
    display: none;
  }
}
</style>
