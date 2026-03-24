<template>
  <div class="chat-input-section">
    <!-- Поле ввода -->
    <div class="input-area">
      <textarea
        ref="textareaRef"
        :value="modelValue"
        @input="$emit('update:modelValue', $event.target.value)"
        @keydown.enter.prevent="$emit('send')"
        placeholder="Введите ваш вопрос..."
        rows="1"
        class="chat-textarea"
        :disabled="isLoading"
      ></textarea>
      <button
        @click="$emit('send')"
        :disabled="!modelValue?.trim() || isLoading"
        class="send-btn"
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z"/>
        </svg>
        Отправить
      </button>
    </div>

    <!-- Быстрые вопросы -->
    <div class="quick-questions-bar">
      <span class="quick-questions-label">Быстрые вопросы:</span>
      <div class="quick-questions">
        <button
          v-for="(question, index) in questions"
          :key="index"
          @click="$emit('useTemplate', question.text)"
          class="quick-question-chip"
        >
          <span class="chip-icon">{{ question.icon }}</span>
          <span class="chip-text">{{ question.label }}</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  isLoading: {
    type: Boolean,
    default: false
  },
  questions: {
    type: Array,
    default: () => [
      { icon: '📋', label: 'Как подать заявку?', text: 'Как подать заявку на подключение?' },
      { icon: '📄', label: 'Какие документы?', text: 'Какие документы нужны для подключения?' },
      { icon: '⏱️', label: 'Сроки', text: 'Сроки подключения' },
      { icon: '💰', label: 'Стоимость', text: 'Стоимость подключения' }
    ]
  }
})

defineEmits(['update:modelValue', 'send', 'useTemplate'])

const textareaRef = ref(null)

// Авто-увеличение высоты textarea
function autoResize() {
  nextTick(() => {
    if (textareaRef.value) {
      textareaRef.value.style.height = 'auto'
      textareaRef.value.style.height = textareaRef.value.scrollHeight + 'px'
    }
  })
}

// Слушаем изменения значения
watch(() => props.modelValue, autoResize)
</script>

<style scoped>
.chat-input-section {
  padding: 16px 20px;
  background: #fff;
  border-top: 1px solid #e5e7eb;
  flex-shrink: 0;
}

.input-area {
  display: flex;
  gap: 10px;
  margin-bottom: 12px;
}

.chat-textarea {
  flex: 1;
  padding: 12px 16px;
  border: 1px solid #d1d5db;
  border-radius: 24px;
  resize: none;
  font-size: 15px;
  font-family: inherit;
  outline: none;
  transition: all 0.2s;
  max-height: 150px;
  min-height: 44px;
}

.chat-textarea:focus {
  border-color: #0066cc;
  box-shadow: 0 0 0 3px rgba(0, 102, 204, 0.1);
}

.chat-textarea:disabled {
  background: #f3f4f6;
  cursor: not-allowed;
}

.send-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 24px;
  background: #0066cc;
  color: white;
  border: none;
  border-radius: 24px;
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.send-btn:hover:not(:disabled) {
  background: #0052a3;
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(0, 102, 204, 0.3);
}

.send-btn:disabled {
  background: #d1d5db;
  cursor: not-allowed;
  opacity: 0.7;
}

/* Быстрые вопросы */
.quick-questions-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.quick-questions-label {
  font-size: 13px;
  color: #6b7280;
  font-weight: 500;
}

.quick-questions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.quick-question-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 16px;
  font-size: 13px;
  color: #374151;
  cursor: pointer;
  transition: all 0.2s;
}

.quick-question-chip:hover {
  background: #eff6ff;
  border-color: #3b82f6;
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.chip-icon {
  font-size: 14px;
}

.chip-text {
  white-space: nowrap;
}
</style>
