<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-content settings-modal">
      <div class="modal-header">
        <h3>⚙️ Настройки</h3>
        <button @click="$emit('close')" class="modal-close-btn">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M18 6L6 18M6 6l12 12"/>
          </svg>
        </button>
      </div>

      <div class="modal-body">
        <!-- Вкладки настроек -->
        <div class="settings-tabs">
          <button 
            :class="['tab-btn', { active: activeTab === 'hotkeys' }]"
            @click="activeTab = 'hotkeys'"
          >
            ⌨️ Горячие клавиши
          </button>
          <button 
            :class="['tab-btn', { active: activeTab === 'general' }]"
            @click="activeTab = 'general'"
          >
            📋 Общие
          </button>
        </div>

        <!-- Контент вкладок -->
        <div class="tab-content">
          <!-- Горячие клавиши -->
          <div v-show="activeTab === 'hotkeys'" class="tab-pane">
            <HotkeysEditor />
          </div>

          <!-- Общие настройки -->
          <div v-show="activeTab === 'general'" class="tab-pane">
            <div class="general-settings">
              <h4>📋 Общие настройки</h4>
              <p class="settings-hint">Здесь будут общие настройки приложения</p>
              
              <div class="setting-item">
                <label class="setting-label">
                  <input type="checkbox" v-model="autoSaveEnabled" />
                  Автоматическое сохранение черновиков
                </label>
                <p class="setting-description">
                  Черновики ответов будут сохраняться автоматически
                </p>
              </div>

              <div class="setting-item">
                <label class="setting-label">
                  <input type="checkbox" v-model="notificationsEnabled" />
                  Уведомления
                </label>
                <p class="setting-description">
                  Показывать уведомления о новых сообщениях
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="modal-footer">
        <button @click="$emit('close')" class="btn-close">Закрыть</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import HotkeysEditor from './HotkeysEditor.vue'

defineEmits(['close'])

const activeTab = ref('hotkeys')
const autoSaveEnabled = ref(true)
const notificationsEnabled = ref(true)
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 12px;
  max-width: 700px;
  width: 90%;
  max-height: 80vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #e5e7eb;
  background: #f9fafb;
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
}

.modal-close-btn {
  background: none;
  border: none;
  cursor: pointer;
  color: #6b7280;
  padding: 4px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.modal-close-btn:hover {
  background: #e5e7eb;
  color: #1f2937;
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.settings-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
  border-bottom: 1px solid #e5e7eb;
  padding-bottom: 10px;
}

.tab-btn {
  padding: 10px 16px;
  background: #f3f4f6;
  border: 1px solid #e5e7eb;
  border-radius: 6px 6px 0 0;
  font-size: 14px;
  font-weight: 500;
  color: #6b7280;
  cursor: pointer;
  transition: all 0.2s;
}

.tab-btn:hover {
  background: #e5e7eb;
}

.tab-btn.active {
  background: white;
  border-bottom-color: white;
  color: #1f2937;
}

.tab-content {
  background: white;
}

.tab-pane {
  animation: fadeIn 0.2s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(5px); }
  to { opacity: 1; transform: translateY(0); }
}

.general-settings {
  padding: 10px;
}

.general-settings h4 {
  margin: 0 0 15px 0;
  font-size: 16px;
  color: #1f2937;
}

.settings-hint {
  color: #6b7280;
  font-size: 14px;
  margin-bottom: 20px;
}

.setting-item {
  margin-bottom: 20px;
  padding: 15px;
  background: #f9fafb;
  border-radius: 6px;
  border: 1px solid #e5e7eb;
}

.setting-label {
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 500;
  color: #1f2937;
  font-size: 14px;
  cursor: pointer;
}

.setting-label input[type="checkbox"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
}

.setting-description {
  margin: 8px 0 0 28px;
  font-size: 13px;
  color: #6b7280;
  line-height: 1.5;
}

.modal-footer {
  padding: 16px 20px;
  border-top: 1px solid #e5e7eb;
  background: #f9fafb;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.btn-close {
  padding: 10px 20px;
  background: #f3f4f6;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  color: #4b5563;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-close:hover {
  background: #e5e7eb;
  border-color: #9ca3af;
}
</style>
