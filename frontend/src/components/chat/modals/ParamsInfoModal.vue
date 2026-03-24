<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-content info-modal">
      <div class="modal-header">
        <h3>Параметры поиска</h3>
        <button @click="$emit('close')" class="modal-close-btn">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M18 6L6 18M6 6l12 12"/>
          </svg>
        </button>
      </div>

      <div class="modal-body">
        <div class="info-section">
          <h4>Количество документов</h4>
          <p>Сколько документов найдёт система для подготовки ответа. Чем больше число, тем больше информации будет использовано, но поиск займёт больше времени.</p>
          <p class="range-hint">Диапазон: 1–15 | Рекомендуется: 8</p>
        </div>

        <div class="info-section">
          <h4>Температура</h4>
          <p>Определяет, насколько творческими будут ответы. При низком значении (ближе к 0) ответы будут точными и строгими. При высоком (до 1.5) — более свободными и разнообразными.</p>
          <p class="range-hint">Диапазон: 0–1.5 | Рекомендуется: 0.7–0.8</p>
        </div>

        <div class="info-section">
          <h4>Длина ответа (макс.)</h4>
          <p>Максимальный размер ответа в словах. Чем больше значение, тем развёрнутее может быть ответ.</p>
          <p class="range-hint">Диапазон: 375–3000 слов | Рекомендуется: 1500</p>
        </div>

        <div class="info-section">
          <h4>Порог сходства</h4>
          <p>Минимальная точность, с которой документ должен соответствовать вашему вопросу. Чем выше значение, тем строже отбор. При 0 будут использованы все найденные документы, при 1 — только самые точные.</p>
          <p class="range-hint">Диапазон: 0–1 | Рекомендуется: 0–0.2</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineEmits(['close'])
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
  max-width: 500px;
  width: 90%;
  max-height: 80vh;
  overflow: hidden;
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
  padding: 20px;
  max-height: calc(80vh - 70px);
  overflow-y: auto;
}

.info-section {
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid #e5e7eb;
}

.info-section:last-child {
  border-bottom: none;
  margin-bottom: 0;
  padding-bottom: 0;
}

.info-section h4 {
  color: #1e3a8a;
  font-size: 15px;
  font-weight: 600;
  margin: 0 0 6px 0;
}

.info-section p {
  margin: 0;
  color: #4b5563;
  line-height: 1.6;
  font-size: 14px;
}

.range-hint {
  margin-top: 6px;
  font-size: 12px;
  color: #059669;
  font-weight: 500;
}
</style>
