<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-content star-modal">
      <div class="modal-header">
        <h3>Оцените ответ</h3>
        <button @click="$emit('close')" class="modal-close-btn">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M18 6L6 18M6 6l12 12"/>
          </svg>
        </button>
      </div>
      <div class="modal-body">
        <div class="star-rating">
          <span
            v-for="star in 5"
            :key="star"
            @click="selectStar(star)"
            @mouseover="hoverRating = star"
            @mouseleave="hoverRating = 0"
            :class="{ active: star <= (hoverRating || selectedRating) }"
          >
            <svg width="40" height="40" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" stroke-width="1">
              <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
            </svg>
          </span>
        </div>
        <div class="star-actions">
          <button @click="$emit('close')" class="cancel-btn">Отмена</button>
          <button @click="$emit('submit', selectedRating)" class="submit-btn" :disabled="!selectedRating">
            Оценить
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  selectedStars: {
    type: Number,
    default: 0
  }
})

defineEmits(['close', 'submit'])

const selectedRating = ref(props.selectedStars)
const hoverRating = ref(0)

// Следим за изменениями selectedStars извне
watch(() => props.selectedStars, (newVal) => {
  selectedRating.value = newVal
})

function selectStar(star) {
  selectedRating.value = star
}
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
  max-width: 400px;
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
}

.star-rating {
  display: flex;
  gap: 8px;
  justify-content: center;
  margin: 20px 0;
  cursor: pointer;
}

.star-rating span {
  color: #d1d5db;
  transition: all 0.2s;
}

.star-rating span.active {
  color: #fbbf24;
}

.star-rating span:hover {
  transform: scale(1.1);
}

.star-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

.cancel-btn {
  padding: 10px 20px;
  background: #f3f4f6;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s;
}

.cancel-btn:hover {
  background: #e5e7eb;
}

.submit-btn {
  padding: 10px 24px;
  background: #0066cc;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s;
}

.submit-btn:hover:not(:disabled) {
  background: #0052a3;
}

.submit-btn:disabled {
  background: #d1d5db;
  cursor: not-allowed;
}
</style>
