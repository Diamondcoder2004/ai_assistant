<template>
  <footer class="footer" :class="{ 'visible': isScrolledToBottom }">
    <div class="container">
      <p>2026 Интеллектуальный Ассистент по Технологическому присоединению</p>
      <p>Для связи: almaz_sabitov04@mail.ru</p>
    </div>
  </footer>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

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
  margin-top: 50px;
  text-align: center;
  opacity: 0.3;
  transition: opacity 0.3s ease;
}

.footer.visible {
  opacity: 1;
}

.footer p {
  margin: 5px 0;
  color: #666;
  font-size: 14px;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
}
</style>
