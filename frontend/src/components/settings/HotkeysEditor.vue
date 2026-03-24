<template>
  <div class="hotkeys-editor">
    <div class="editor-header">
      <h3>⌨️ Горячие клавиши</h3>
      <button @click="resetToDefaults" class="reset-btn" title="Сбросить к настройкам по умолчанию">
        <img src="../../assets/images/reload_refresh.svg" alt="Сбросить" width="16" height="16" />
        Сбросить
      </button>
    </div>

    <div class="hotkeys-list">
      <div v-for="action in availableActions" :key="action.key" class="hotkey-item">
        <div class="hotkey-info">
          <span class="hotkey-label">{{ action.label }}</span>
          <span class="hotkey-default">По умолчанию: {{ formatCombination(action.default) }}</span>
        </div>
        
        <div class="hotkey-controls">
          <div 
            class="hotkey-capture"
            :class="{ 
              'capturing': capturing === action.key,
              'error': errors[action.key],
              'conflict': conflicts[action.key]
            }"
            @click="startCapture(action.key)"
            @keydown.prevent="captureKey"
            @keyup.prevent="stopCapture"
            tabindex="0"
          >
            <span v-if="capturing === action.key" class="capture-prompt">
              Нажмите комбинацию...
            </span>
            <span v-else class="current-combination">
              {{ formatCombination(hotkeys[action.key]) }}
            </span>
          </div>
          
          <button 
            v-if="hotkeys[action.key] !== action.default"
            @click="resetHotkey(action.key)"
            class="reset-hotkey-btn"
            title="Вернуть значение по умолчанию"
          >
            ↺
          </button>
        </div>
        
        <!-- Ошибки -->
        <div v-if="errors[action.key]" class="hotkey-error">
          {{ errors[action.key] }}
        </div>
        <div v-if="conflicts[action.key]" class="hotkey-conflict">
          ⚠️ Конфликт с: {{ getActionLabel(conflicts[action.key]) }}
        </div>
      </div>
    </div>

    <!-- Подсказка -->
    <div class="hotkeys-hint">
      <h4>💡 Допустимые комбинации:</h4>
      <ul>
        <li>Можно использовать модификаторы: <kbd>Ctrl</kbd>, <kbd>Alt</kbd>, <kbd>Shift</kbd>, <kbd>Win</kbd></li>
        <li>Обязательно должна быть хотя бы одна клавиша (буква, цифра, F1-F12)</li>
        <li>Нельзя использовать только <kbd>Enter</kbd> или <kbd>Пробел</kbd> с модификаторами</li>
        <li>Одна комбинация не может использоваться для нескольких действий</li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useHotkeysStore } from '../../stores/hotkeysStore'

const hotkeysStore = useHotkeysStore()

const capturing = ref(null)
const errors = ref({})
const conflicts = ref({})

const { 
  hotkeys, 
  availableActions, 
  DEFAULT_HOTKEYS,
  updateHotkey, 
  resetToDefaults,
  formatCombination,
  checkConflict,
  captureKeyCombination,
  validateKeyCombination
} = hotkeysStore

// Начало захвата клавиши
function startCapture(actionKey) {
  capturing.value = actionKey
  errors.value[actionKey] = null
  conflicts.value[actionKey] = null
  
  // Фокус на элемент для захвата
  setTimeout(() => {
    const element = document.querySelector('.hotkey-capture.capturing')
    if (element) element.focus()
  }, 0)
}

// Захват клавиши
function captureKey(event) {
  if (!capturing.value) return

  // Предотвращаем стандартное поведение
  event.preventDefault()
  event.stopPropagation()

  const combination = captureKeyCombination(event)

  // Проверяем валидность
  if (!validateKeyCombination(combination)) {
    errors.value[capturing.value] = 'Недопустимая комбинация клавиш'
    return
  }

  // Проверяем конфликты
  const conflict = checkConflict(combination, capturing.value)
  if (conflict) {
    conflicts.value[capturing.value] = conflict
    return
  }

  // Сохраняем
  const success = updateHotkey(capturing.value, combination)
  if (success) {
    errors.value[capturing.value] = null
    conflicts.value[capturing.value] = null
    capturing.value = null
  }
}

// Остановка захвата
function stopCapture() {
  if (capturing.value) {
    capturing.value = null
  }
}

// Сброс конкретной клавиши
function resetHotkey(actionKey) {
  // Сначала очищаем ошибки
  errors.value[actionKey] = null
  conflicts.value[actionKey] = null
  
  // Затем сбрасываем к значению по умолчанию
  const defaultCombination = DEFAULT_HOTKEYS[actionKey]
  updateHotkey(actionKey, defaultCombination)
}

// Получение названия действия
function getActionLabel(actionKey) {
  const action = availableActions.find(a => a.key === actionKey)
  return action ? action.label : actionKey
}
</script>

<style scoped>
.hotkeys-editor {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #e5e7eb;
}

.editor-header h3 {
  margin: 0;
  font-size: 18px;
  color: #1f2937;
}

.reset-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: #f3f4f6;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 13px;
  color: #4b5563;
  cursor: pointer;
  transition: all 0.2s;
}

.reset-btn:hover {
  background: #e5e7eb;
  border-color: #9ca3af;
}

.hotkeys-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
  margin-bottom: 20px;
}

.hotkey-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px;
  background: #f9fafb;
  border-radius: 6px;
  border: 1px solid #e5e7eb;
}

.hotkey-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.hotkey-label {
  font-weight: 500;
  color: #1f2937;
  font-size: 14px;
}

.hotkey-default {
  font-size: 12px;
  color: #6b7280;
  font-style: italic;
}

.hotkey-controls {
  display: flex;
  align-items: center;
  gap: 8px;
}

.hotkey-capture {
  flex: 1;
  padding: 10px 14px;
  background: white;
  border: 2px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  color: #374151;
  cursor: pointer;
  transition: all 0.2s;
  outline: none;
  min-height: 20px;
  display: flex;
  align-items: center;
}

.hotkey-capture:hover {
  border-color: #9ca3af;
  background: #f9fafb;
}

.hotkey-capture:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.hotkey-capture.capturing {
  border-color: #f59e0b;
  background: #fef3c7;
  animation: pulse 1s infinite;
}

.hotkey-capture.error {
  border-color: #ef4444;
  background: #fee2e2;
}

.hotkey-capture.conflict {
  border-color: #f59e0b;
  background: #fef3c7;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

.capture-prompt {
  color: #d97706;
  font-style: italic;
}

.current-combination {
  font-family: 'Courier New', monospace;
}

.reset-hotkey-btn {
  width: 32px;
  height: 38px;
  background: #f3f4f6;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 16px;
  color: #4b5563;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.reset-hotkey-btn:hover {
  background: #e5e7eb;
  border-color: #9ca3af;
}

.hotkey-error,
.hotkey-conflict {
  font-size: 12px;
  padding: 6px 10px;
  border-radius: 4px;
  margin-top: 4px;
}

.hotkey-error {
  background: #fee2e2;
  color: #dc2626;
}

.hotkey-conflict {
  background: #fef3c7;
  color: #d97706;
}

.hotkeys-hint {
  background: #f0f9ff;
  border: 1px solid #bae6fd;
  border-radius: 6px;
  padding: 15px;
  margin-top: 10px;
}

.hotkeys-hint h4 {
  margin: 0 0 10px 0;
  font-size: 14px;
  color: #0369a1;
}

.hotkeys-hint ul {
  margin: 0;
  padding-left: 20px;
  list-style-type: disc;
}

.hotkeys-hint li {
  margin: 6px 0;
  font-size: 13px;
  color: #0c4a6e;
  line-height: 1.5;
}

.hotkeys-hint kbd {
  display: inline-block;
  padding: 2px 6px;
  background: white;
  border: 1px solid #cbd5e1;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-size: 12px;
  font-weight: 500;
  color: #334155;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}
</style>
