import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { createPinia } from 'pinia'

// Создаем приложение
const app = createApp(App)

// Используем Pinia для состояния
const pinia = createPinia()
app.use(pinia)

// Используем роутер
app.use(router)

// Монтируем приложение
app.mount('#app')

console.log('Vue app mounted successfully!')
