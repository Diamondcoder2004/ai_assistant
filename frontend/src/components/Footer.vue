<template>
  <footer class="footer" :class="{ 'visible': isVisible }">
    <div class="container">
      <div class="footer-content">
        <div class="footer-text">
          <p>2026 Интеллектуальный Ассистент по Технологическому присоединению</p>
          <p>Для связи: almaz_sabitov04@mail.ru</p>
        </div>
      </div>
    </div>
  </footer>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const isVisible = ref(false)
let lastScrollY = 0
let scrollTimeout = null
const SCROLL_THRESHOLD = 30 // минимальное смещение для срабатывания

const handleScroll = () => {
  const currentScrollY = window.scrollY
  const scrollDelta = currentScrollY - lastScrollY

  // Сброс таймера при каждом скролле
  if (scrollTimeout) clearTimeout(scrollTimeout)

  if (Math.abs(scrollDelta) > SCROLL_THRESHOLD) {
    if (scrollDelta > 0) {
      // Скролл вниз — показываем
      isVisible.value = true
    } else {
      // Скролл вверх — скрываем
      isVisible.value = false
    }
    lastScrollY = currentScrollY
  }

  // Автоскрытие через 3 секунды после последнего скролла
  scrollTimeout = setTimeout(() => {
    isVisible.value = false
  }, 3000)
}

onMounted(() => {
  lastScrollY = window.scrollY
  window.addEventListener('scroll', handleScroll, { passive: true })
})

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll)
  if (scrollTimeout) clearTimeout(scrollTimeout)
})
</script>

<style scoped>
.footer {
  background: #f8f9fa;
  border-top: 1px solid #ddd;
  padding: 12px 20px;
  text-align: center;
  opacity: 0;
  transition: opacity 0.3s ease;
  flex-shrink: 0;
}

.footer.visible {
  opacity: 1;
}

.footer-content {
  display: flex;
  justify-content: center;
  align-items: center;
  max-width: 1200px;
  margin: 0 auto;
}

.footer-text p {
  margin: 3px 0;
  color: #666;
  font-size: 13px;
}
</style>
