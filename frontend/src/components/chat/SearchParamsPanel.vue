<template>
  <div class="search-params-section">
    <h3>⚙️ Формат ответа</h3>

    <div class="mode-buttons">
      <button
        v-for="mode in modes"
        :key="mode.id"
        :class="['mode-btn', { active: selectedMode === mode.id }]"
        @click="selectMode(mode.id)"
      >
        <span class="mode-icon">{{ mode.icon }}</span>
        <span class="mode-label">{{ mode.label }}</span>
        <span class="mode-desc">{{ mode.desc }}</span>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  modelValue: {
    type: Object,
    required: true,
    default: () => ({
      k: 10,
      temperature: 0.8,
      max_tokens: 2000,
      min_score: 0.0
    })
  }
})

const emit = defineEmits(['update:modelValue'])

const modes = [
  {
    id: 'brief',
    label: 'Кратко',
    desc: 'Самый важный ответ без деталей',
    icon: '📝',
    params: { k: 5, temperature: 0.3, max_tokens: 800, min_score: 0.1 }
  },
  {
    id: 'standard',
    label: 'Стандартно',
    desc: 'Сбалансированный ответ по существу',
    icon: '⚖️',
    params: { k: 10, temperature: 0.8, max_tokens: 2000, min_score: 0.0 }
  },
  {
    id: 'detailed',
    label: 'Подробно',
    desc: 'Развёрнутый ответ со всеми нюансами',
    icon: '📋',
    params: { k: 15, temperature: 1.0, max_tokens: 3500, min_score: 0.0 }
  }
]

// Определяем текущий режим по параметрам при монтировании
const selectedMode = ref('standard')

function selectMode(modeId) {
  selectedMode.value = modeId
  const mode = modes.find(m => m.id === modeId)
  if (mode) {
    emit('update:modelValue', { ...mode.params })
  }
}
</script>

<style scoped>
.search-params-section {
  background: white;
  border-radius: 8px;
  padding: 16px;
  border: 1px solid #e5e7eb;
}

.search-params-section h3 {
  margin: 0 0 14px 0;
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.mode-buttons {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.mode-btn {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 4px;
  width: 100%;
  padding: 12px 14px;
  border: 2px solid #e5e7eb;
  border-radius: 10px;
  background: #fafafa;
  cursor: pointer;
  transition: all 0.2s ease;
  text-align: left;
  font-family: inherit;
}

.mode-btn:hover {
  border-color: #93c5fd;
  background: #eff6ff;
}

.mode-btn.active {
  border-color: #0066cc;
  background: #eff6ff;
  box-shadow: 0 0 0 2px rgba(0, 102, 204, 0.15);
}

.mode-btn.active .mode-label {
  color: #0052a3;
}

.mode-icon {
  font-size: 18px;
  line-height: 1;
}

.mode-label {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
}

.mode-desc {
  font-size: 12px;
  color: #6b7280;
  line-height: 1.4;
}
</style>
