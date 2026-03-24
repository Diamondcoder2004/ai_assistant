<template>
  <div class="profile">
    <Header />

    <div class="container">
      <h1>Мой профиль</h1>

      <div v-if="loading" class="loading">
        Загрузка профиля...
      </div>

      <div v-else class="profile-card">
        <!-- Режим просмотра -->
        <div v-if="!isEditing" class="profile-view">
          <div class="profile-header">
            <div class="avatar">
              {{ getInitials() }}
            </div>
            <h2>{{ getFullName() }}</h2>
            <p class="user-email">{{ profile.email || authStore.user?.email }}</p>
          </div>

          <div class="profile-details">
            <div class="detail-item">
              <span class="label">Имя:</span>
              <span class="value">{{ profile.full_name || 'Не указано' }}</span>
            </div>

            <div class="detail-item">
              <span class="label">Фамилия:</span>
              <span class="value">{{ profile.last_name || 'Не указано' }}</span>
            </div>

            <div class="detail-item">
              <span class="label">Email:</span>
              <span class="value">{{ profile.email || authStore.user?.email }}</span>
            </div>

            <div class="detail-item">
              <span class="label">Телефон:</span>
              <span class="value">{{ profile.phone || 'Не указан' }}</span>
            </div>

            <div class="detail-item">
              <span class="label">Telegram:</span>
              <span class="value">{{ profile.telegram || 'Не указан' }}</span>
            </div>
          </div>

          <button @click="startEditing" class="btn-edit">
            Редактировать профиль
          </button>
        </div>

        <!-- Режим редактирования -->
        <div v-else class="profile-edit">
          <h3>Редактирование профиля</h3>

          <form @submit.prevent="saveProfile" class="edit-form">
            <div class="form-group">
              <label for="full_name">Имя:</label>
              <input
                id="full_name"
                v-model="editData.full_name"
                type="text"
                placeholder="Введите имя"
              >
            </div>

            <div class="form-group">
              <label for="last_name">Фамилия:</label>
              <input
                id="last_name"
                v-model="editData.last_name"
                type="text"
                placeholder="Введите фамилию"
              >
            </div>

            <div class="form-group">
              <label>Email:</label>
              <div class="email-display">
                {{ authStore.user?.email }}
              </div>
            </div>

            <div class="form-group">
              <label for="phone">Телефон:</label>
              <input
                id="phone"
                v-model="editData.phone"
                type="tel"
                placeholder="+7 (___) ___-__-__"
              >
            </div>

            <div class="form-group">
              <label for="telegram">Telegram:</label>
              <input
                id="telegram"
                v-model="editData.telegram"
                type="text"
                placeholder="@username"
              >
            </div>

            <div class="form-actions">
              <button type="button" @click="cancelEditing" class="btn-cancel">
                Отмена
              </button>
              <button type="submit" :disabled="saveLoading" class="btn-save">
                {{ saveLoading ? 'Сохранение...' : 'Сохранить' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <Footer />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import Header from '../components/Header.vue'
import Footer from '../components/Footer.vue'
import { useAuthStore } from '../stores/authStore'

const authStore = useAuthStore()
const profile = ref({})
const editData = ref({})
const loading = ref(true)
const saveLoading = ref(false)
const isEditing = ref(false)

// Получение инициалов для аватара
function getInitials() {
  const fullName = `${profile.value.full_name || ''} ${profile.value.last_name || ''}`.trim()
  if (!fullName) return authStore.user?.email?.charAt(0).toUpperCase() || '?'

  const parts = fullName.split(' ')
  if (parts.length >= 2) {
    return (parts[0].charAt(0) + parts[1].charAt(0)).toUpperCase()
  }
  return parts[0].charAt(0).toUpperCase()
}

// Получение полного имени
function getFullName() {
  const fullName = `${profile.value.full_name || ''} ${profile.value.last_name || ''}`.trim()
  return fullName || authStore.user?.email || 'Пользователь'
}

// Загрузка профиля
async function loadProfile() {
  if (!authStore.user) return

  loading.value = true
  try {
    // Проверяем, есть ли профиль в authStore
    if (authStore.profile) {
      profile.value = authStore.profile
    } else {
      // Если нет, пытаемся загрузить
      await authStore.loadProfile()
      profile.value = authStore.profile || {}
    }

    // Добавляем email из authStore.user
    profile.value.email = authStore.user?.email || ''

    console.log('Загружен профиль:', profile.value)
  } catch (error) {
    console.error('Ошибка загрузки профиля:', error)
    profile.value = {
      email: authStore.user?.email || ''
    }
  } finally {
    loading.value = false
  }
}

// Начало редактирования
function startEditing() {
  isEditing.value = true
  editData.value = {
    full_name: profile.value.full_name || '',
    last_name: profile.value.last_name || '',
    phone: profile.value.phone || '',
    telegram: profile.value.telegram || ''
  }
}

// Отмена редактирования
function cancelEditing() {
  isEditing.value = false
  editData.value = {}
}

// Сохранение профиля
async function saveProfile() {
  if (!authStore.user) return

  saveLoading.value = true
  try {
    const result = await authStore.updateProfile(editData.value)

    if (result.success) {
      // Обновляем локальные данные
      profile.value = result.data || {
        ...profile.value,
        ...editData.value
      }
      isEditing.value = false
      alert('Профиль успешно сохранен')
    } else {
      alert('Ошибка сохранения: ' + (result.error || 'Неизвестная ошибка'))
    }
  } catch (error) {
    console.error('Ошибка сохранения профиля:', error)
    alert('Произошла ошибка при сохранении: ' + error.message)
  } finally {
    saveLoading.value = false
  }
}

onMounted(() => {
  loadProfile()
})
</script>

<style scoped>
.container {
  max-width: 600px;
  margin: 0 auto;
  padding: 20px;
}

h1 {
  color: #003366;
  margin-bottom: 30px;
  text-align: center;
}

.profile-card {
  background: white;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 30px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.loading {
  text-align: center;
  padding: 40px;
  color: #666;
}

/* Режим просмотра */
.profile-view .profile-header {
  text-align: center;
  margin-bottom: 30px;
}

.avatar {
  width: 80px;
  height: 80px;
  background: linear-gradient(135deg, #0066cc 0%, #003366 100%);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32px;
  font-weight: bold;
  margin: 0 auto 20px;
}

.profile-header h2 {
  color: #333;
  margin: 0 0 5px 0;
  font-size: 24px;
}

.user-email {
  color: #666;
  margin: 0;
  font-size: 16px;
  word-break: break-all;
}

.profile-details {
  margin-bottom: 30px;
}

.detail-item {
  display: flex;
  margin-bottom: 15px;
  padding-bottom: 15px;
  border-bottom: 1px solid #eee;
}

.detail-item:last-child {
  border-bottom: none;
  margin-bottom: 0;
  padding-bottom: 0;
}

.detail-item .label {
  font-weight: 500;
  color: #333;
  width: 120px;
  flex-shrink: 0;
}

.detail-item .value {
  color: #666;
  flex: 1;
}

.btn-edit {
  background: #0066cc;
  color: white;
  border: none;
  padding: 12px 30px;
  border-radius: 6px;
  font-size: 16px;
  cursor: pointer;
  width: 100%;
  transition: background 0.2s;
}

.btn-edit:hover {
  background: #0052a3;
}

/* Режим редактирования */
.profile-edit h3 {
  color: #003366;
  margin-bottom: 25px;
  text-align: center;
}

.edit-form {
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
  padding: 10px 15px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 16px;
  transition: border-color 0.2s;
}

.form-group input:focus {
  outline: none;
  border-color: #0066cc;
}

.email-display {
  padding: 10px 15px;
  background: #f5f5f5;
  border: 1px solid #ddd;
  border-radius: 4px;
  color: #333;
  font-size: 16px;
}

.email-note {
  display: block;
  font-size: 12px;
  color: #666;
  margin-top: 5px;
}

.form-actions {
  display: flex;
  gap: 15px;
  margin-top: 20px;
}

.btn-cancel, .btn-save {
  flex: 1;
  padding: 12px;
  border-radius: 6px;
  font-size: 16px;
  cursor: pointer;
  border: none;
  transition: background 0.2s;
}

.btn-cancel {
  background: #f5f5f5;
  color: #333;
  border: 1px solid #ddd;
}

.btn-cancel:hover {
  background: #e5e5e5;
}

.btn-save {
  background: #0066cc;
  color: white;
}

.btn-save:hover:not(:disabled) {
  background: #0052a3;
}

.btn-save:disabled {
  background: #ccc;
  cursor: not-allowed;
}

@media (max-width: 480px) {
  .container {
    padding: 15px;
  }

  .profile-card {
    padding: 20px;
  }

  .detail-item {
    flex-direction: column;
    gap: 5px;
  }

  .detail-item .label {
    width: auto;
  }

  .form-actions {
    flex-direction: column;
  }
}
</style>
