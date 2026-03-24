<template>
  <div class="search-params-section">
    <h3>⚙️ Параметры поиска и ответа</h3>

    <!-- Количество документов -->
    <div class="param-row">
      <div class="param-header">
        <label for="k-param">Количество документов</label>
        <div class="param-input-wrapper">
          <input
            id="k-param"
            type="number"
            :value="modelValue.k"
            :min="1"
            :max="15"
            step="1"
            @input="updateParam('k', $event.target.value, 1, 15, 1)"
            class="param-number-input"
          />
        </div>
      </div>
      <input
        type="range"
        :value="modelValue.k"
        min="1"
        max="15"
        step="1"
        class="param-range"
        @input="updateParam('k', $event.target.value, 1, 15, 1)"
      />
      <span class="param-hint">Рекомендуется: 8</span>
    </div>

    <!-- Температура -->
    <div class="param-row">
      <div class="param-header">
        <label for="temp-param">Температура</label>
        <div class="param-input-wrapper">
          <input
            id="temp-param"
            type="number"
            :value="modelValue.temperature"
            :min="0"
            :max="1.5"
            step="0.1"
            @input="updateParam('temperature', $event.target.value, 0, 1.5, 0.1)"
            class="param-number-input"
          />
        </div>
      </div>
      <input
        type="range"
        :value="modelValue.temperature"
        min="0"
        max="1.5"
        step="0.1"
        class="param-range"
        @input="updateParam('temperature', $event.target.value, 0, 1.5, 0.1)"
      />
      <span class="param-hint">0 = точно, 1.5 = творчески</span>
    </div>

    <!-- Длина ответа -->
    <div class="param-row">
      <div class="param-header">
        <label for="tokens-param">Длина ответа (макс.)</label>
        <div class="param-input-wrapper">
          <input
            id="tokens-param"
            type="number"
            :value="modelValue.max_tokens"
            :min="500"
            :max="4000"
            step="100"
            @input="updateParam('max_tokens', $event.target.value, 500, 4000, 100)"
            class="param-number-input"
          />
        </div>
      </div>
      <input
        type="range"
        :value="modelValue.max_tokens"
        min="500"
        max="4000"
        step="100"
        class="param-range"
        @input="updateParam('max_tokens', $event.target.value, 500, 4000, 100)"
      />
      <span class="param-hint">Рекомендуется: 2000 (~1500 слов)</span>
    </div>

    <!-- Порог сходства -->
    <div class="param-row">
      <div class="param-header">
        <label for="score-param">Порог сходства</label>
        <div class="param-input-wrapper">
          <input
            id="score-param"
            type="number"
            :value="modelValue.min_score"
            :min="0"
            :max="1"
            step="0.05"
            @input="updateParam('min_score', $event.target.value, 0, 1, 0.05)"
            class="param-number-input"
          />
        </div>
      </div>
      <input
        type="range"
        :value="modelValue.min_score"
        min="0"
        max="1"
        step="0.05"
        class="param-range"
        @input="updateParam('min_score', $event.target.value, 0, 1, 0.05)"
      />
      <span class="param-hint">Рекомендуется: 0–0.2</span>
    </div>

    <button @click="$emit('showInfo')" class="info-link">
      <img src="../../assets/images/question-circle-svgrepo-com.svg" alt="?" width="16" height="16" />
      Что означают параметры?
    </button>
  </div>
</template>

<script setup>
const props = defineProps({
  modelValue: {
    type: Object,
    required: true,
    default: () => ({
      k: 8,
      temperature: 0.8,
      max_tokens: 2000,
      min_score: 0.0
    })
  }
})

const emit = defineEmits(['update:modelValue', 'showInfo'])

// Валидация и обновление параметра
function updateParam(key, value, min, max, step) {
  let numValue = parseFloat(value)

  // Если пустое значение - пропускаем
  if (value === '' || value === null || value === undefined) {
    return
  }

  // Проверка на NaN
  if (isNaN(numValue)) {
    return
  }

  // Ограничение диапазона
  numValue = Math.max(min, Math.min(max, numValue))

  // Округление до шага
  if (step) {
    numValue = Math.round(numValue / step) * step
    // Для дробных шагов округляем до 2 знаков
    numValue = Math.round(numValue * 100) / 100
  } else if (Number.isInteger(min) && Number.isInteger(max)) {
    // Для целых чисел
    numValue = Math.round(numValue)
  }

  // Создаём новый объект с обновлённым значением
  const newValue = { ...props.modelValue, [key]: numValue }
  emit('update:modelValue', newValue)
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
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.param-row {
  margin-bottom: 20px;
}

.param-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.param-header label {
  font-size: 13px;
  font-weight: 500;
  color: #374151;
}

.param-input-wrapper {
  flex-shrink: 0;
}

.param-number-input {
  width: 70px;
  padding: 6px 8px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 13px;
  text-align: center;
  transition: all 0.2s;
}

.param-number-input:focus {
  outline: none;
  border-color: #0066cc;
  box-shadow: 0 0 0 3px rgba(0, 102, 204, 0.1);
}

.param-number-input::-webkit-inner-spin-button,
.param-number-input::-webkit-outer-spin-button {
  opacity: 1;
}

.param-range {
  width: 100%;
  height: 6px;
  border-radius: 3px;
  background: #e5e7eb;
  appearance: none;
  cursor: pointer;
}

.param-range::-webkit-slider-thumb {
  appearance: none;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #0066cc;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.param-range::-webkit-slider-thumb:hover {
  background: #0052a3;
  transform: scale(1.1);
}

.param-range::-moz-range-thumb {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #0066cc;
  cursor: pointer;
  border: none;
  transition: all 0.2s;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.param-range::-moz-range-thumb:hover {
  background: #0052a3;
  transform: scale(1.1);
}

.param-hint {
  display: block;
  font-size: 11px;
  color: #6b7280;
  margin-top: 6px;
  font-style: italic;
}

.info-link {
  display: flex;
  align-items: center;
  gap: 6px;
  background: none;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  padding: 8px 12px;
  font-size: 13px;
  color: #0066cc;
  cursor: pointer;
  transition: all 0.2s;
  width: 100%;
  margin-top: 8px;
}

.info-link:hover {
  background: #eff6ff;
  border-color: #3b82f6;
}
</style>
