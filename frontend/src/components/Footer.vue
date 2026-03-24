<template>
  <footer class="footer" :class="{ 'visible': isScrolledToBottom || forceShow }">
    <div class="container">
      <div class="footer-content">
        <div class="footer-text">
          <p>2026 Интеллектуальный Ассистент по Технологическому присоединению</p>
          <p>Для связи: almaz_sabitov04@mail.ru</p>
        </div>
        <button @click="$emit('hide')" class="hide-footer-btn" title="Скрыть футер" v-if="forceShow">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M18 6L6 18M6 6l12 12"/>
          </svg>
        </button>
      </div>
    </div>
  </footer>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

defineProps({
  forceShow: {
    type: Boolean,
    default: false
  }
})

defineEmits(['hide'])

const isScrolledToBottom = ref(false)

const handleScroll = () => {
  const scrollPosition = window.innerHeight + window.scrollY
  const documentHeight = document.documentElement.scrollHeight

  // Показываем footer когда пользователь прокрутил до конца страницы
  isScrolledToBottom.value = scrollPosition >= documentHeight - 100
}

onMounted(() => {
  window.addEventListener('scroll', handleScroll)
  handleScroll() // Проверить текущую позицию при загрузке
})

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll)
})
</script>

<style scoped>
.footer {
  background: #f8f9fa;
  border-top: 1px solid #ddd;
  padding: 20px;
  margin-top: 40px;
  text-align: center;
  opacity: 0.3;
  transition: opacity 0.3s ease;
  flex-shrink: 0;
}

.footer.visible {
  opacity: 1;
}

.footer-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 1200px;
  margin: 0 auto;
  gap: 20px;
}

.footer-text {
  flex: 1;
}

.footer-text p {
  margin: 5px 0;
  color: #666;
  font-size: 14px;
}

.hide-footer-btn {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: #e5e7eb;
  color: #6b7280;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.hide-footer-btn:hover {
  background: #d1d5db;
  color: #1f2937;
}
</style>
