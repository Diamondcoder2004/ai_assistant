<template>
  <div id="app">
    <router-view />
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useAuthStore } from './stores/authStore'

const authStore = useAuthStore()

onMounted(() => {
  console.log('App mounted, initializing auth...')
  authStore.init()
})
</script>

<style>
/* Базовые стили */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: Arial, sans-serif;
  font-size: 16px;
  line-height: 1.5;
  color: #333;
  background-color: #fff;
  min-height: 100vh;
}

#app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

/* Цветовая схема Башкирэнерго */
:root {
  --primary: #0066cc;
  --primary-dark: #003366;
  --accent: #ff6600;
  --gray-light: #f8f9fa;
  --gray: #6c757d;
  --gray-dark: #343a40;
}

/* Контейнер */
.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 15px;
}

/* Утилиты */
.text-center { text-align: center; }
.mt-1 { margin-top: 0.25rem; }
.mt-2 { margin-top: 0.5rem; }
.mt-3 { margin-top: 1rem; }
.mt-4 { margin-top: 1.5rem; }
.mt-5 { margin-top: 3rem; }

.mb-1 { margin-bottom: 0.25rem; }
.mb-2 { margin-bottom: 0.5rem; }
.mb-3 { margin-bottom: 1rem; }
.mb-4 { margin-bottom: 1.5rem; }
.mb-5 { margin-bottom: 3rem; }

.d-none { display: none !important; }
.d-block { display: block !important; }
.d-flex { display: flex !important; }
</style>
