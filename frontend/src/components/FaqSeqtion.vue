<template>
  <div class="faq-section">
    <h3 class="faq-title">Частые вопросы (FAQ)</h3>

    <!-- Поиск по FAQ -->
    <div class="faq-search-box">
      <input
        v-model="searchQuery"
        placeholder="Поиск в FAQ..."
        @input="filterFaq"
        class="faq-search-input"
      >
      <span class="faq-count">Найдено: {{ filteredFaq.length }}</span>
    </div>

    <!-- Список FAQ с прокруткой -->
    <div class="faq-list-container">
      <div v-if="loading" class="loading-faq">
        <span class="spinner"></span>
        Загрузка FAQ...
      </div>

      <div v-else-if="error" class="error-faq">
        <p>❌ Ошибка загрузки: {{ error }}</p>
        <button @click="loadFaqFromCsv" class="retry-btn">Повторить</button>
      </div>

      <div v-else-if="filteredFaq.length === 0" class="empty-faq">
        Нет вопросов для отображения
      </div>

      <div v-else class="faq-cards-container">
        <div
          v-for="item in filteredFaq"
          :key="item.id"
          class="faq-card"
          :class="{ 'active': openFaqId === item.id }"
        >
          <div class="faq-question" @click="toggleFaq(item.id)">
            <div class="question-content">
              <span class="question-icon">❓</span>
              <span class="question-text">{{ item.question }}</span>
            </div>
            <span class="faq-toggle" :class="{ 'rotated': openFaqId === item.id }">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                <path d="M6 9l6 6 6-6"/>
              </svg>
            </span>
          </div>
          <div v-if="openFaqId === item.id" class="faq-answer">
            <div class="answer-content">
              <span class="answer-icon">💡</span>
              <p class="answer-text">{{ item.answer }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import {computed, onMounted, ref} from 'vue'
import {supabase} from '../services/supabase'

const faqData = ref([])
const searchQuery = ref('')
const openFaqId = ref(null)
const loading = ref(false)
const error = ref(null)

// Фильтрация FAQ
const filteredFaq = computed(() => {
  if (!searchQuery.value.trim()) {
    return faqData.value
  }

  const query = searchQuery.value.toLowerCase()
  return faqData.value.filter(item =>
    item.question.toLowerCase().includes(query) ||
    item.answer.toLowerCase().includes(query)
  )
})

// Загрузка FAQ из CSV файла
async function loadFaqFromCsv() {
  loading.value = true
  error.value = null

  try {
    console.log('Загрузка FAQ из Supabase Storage...')

    const { data, error } = await supabase.storage
      .from('df')
      .download('faq_question.csv')

    if (error) {
      console.error('Ошибка загрузки CSV:', error)
      throw new Error(`Ошибка загрузки: ${error.message || 'неизвестная ошибка'}`)
    }

    console.log('CSV файл загружен, размер:', data.size, 'байт')

    const text = await data.text()
    console.log('Первые 200 символов CSV:', text.substring(0, 200))

    const parsedData = parseCsv(text)
    console.log(`Распарсено ${parsedData.length} вопросов`)

    if (parsedData.length === 0) {
      console.warn('CSV файл пуст или не удалось распарсить')
      const lines = text.split('\n').slice(0, 5)
      console.log('Первые 5 строк CSV:', lines)
    }

    faqData.value = parsedData

  } catch (err) {
    console.error('Ошибка обработки FAQ:', err)
    error.value = err.message || 'Неизвестная ошибка'
    faqData.value = getDefaultFaq()
  } finally {
    loading.value = false
  }
}

// Улучшенный парсинг CSV
function parseCsv(csvText) {
  const lines = csvText.split('\n')
  const result = []

  console.log(`Всего строк в CSV: ${lines.length}`)

  const firstLine = lines[0].toLowerCase()
  const hasHeader = firstLine.includes('вопрос') || firstLine.includes('question')
  const startIndex = hasHeader ? 1 : 0

  console.log(`Есть заголовок: ${hasHeader}, начинаем с индекса ${startIndex}`)

  for (let i = startIndex; i < lines.length; i++) {
    const line = lines[i].trim()
    if (!line) continue

    let question, answer

    if (line.includes('","')) {
      const parts = line.split('","')
      if (parts.length >= 2) {
        question = parts[0].replace(/^"/, '').trim()
        answer = parts[1].replace(/"$/, '').trim()
      }
    } else if (line.includes(',')) {
      const firstComma = line.indexOf(',')
      question = line.substring(0, firstComma).trim()
      answer = line.substring(firstComma + 1).trim()

      question = question.replace(/^"|"$/g, '')
      answer = answer.replace(/^"|"$/g, '')
    }

    if (question && answer) {
      result.push({
        id: i + 1,
        question: question,
        answer: answer
      })
    } else {
      console.warn(`Строка ${i + 1} не распарсена:`, line)
    }
  }

  return result
}

// Заглушка FAQ если CSV не загрузился
function getDefaultFaq() {
  return [
    { id: 1, question: 'Как подать заявку на технологическое присоединение?', answer: 'Заявку можно подать через личный кабинет на сайте или в клиентском офисе компании.' },
    { id: 2, question: 'Какие документы нужны для подключения?', answer: 'Паспорт, право собственности на объект, схема расположения энергопринимающих устройств.' },
    { id: 3, question: 'Сроки технологического присоединения?', answer: 'Стандартные сроки составляют от 3 до 30 рабочих дней в зависимости от категории заявителя.' },
    { id: 4, question: 'Сколько стоит подключение?', answer: 'Стоимость зависит от мощности и удаленности. Для физических лиц до 15 кВт – 550 рублей.' },
    { id: 5, question: 'Как проверить статус заявки?', answer: 'Статус заявки можно проверить в личном кабинете или по телефону горячей линии.' }
  ]
}

// Переключение FAQ
function toggleFaq(id) {
  openFaqId.value = openFaqId.value === id ? null : id
}

function filterFaq() {
  // Автоматически фильтруется через computed свойство
}

onMounted(() => {
  loadFaqFromCsv()
})
</script>

<style scoped>
.faq-section {
  margin-top: 0;
  background: transparent;
  border: none;
  padding: 0;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.faq-title {
  color: #1e3a8a;
  margin-bottom: 20px;
  font-size: 20px;  /* Увеличили */
  font-weight: 700;
  padding-bottom: 12px;
  border-bottom: 2px solid #e2e8f0;
  flex-shrink: 0;
}

.faq-search-box {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
  background: white;
  padding: 10px 15px;  /* Увеличили отступы */
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
  flex-shrink: 0;
}

.faq-search-input {
  flex: 1;
  padding: 10px 14px;  /* Увеличили */
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  font-size: 15px;  /* Увеличили */
  transition: all 0.2s;
}

.faq-search-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
}

.faq-count {
  font-size: 14px;  /* Увеличили */
  color: #4b5563;
  font-weight: 500;
  white-space: nowrap;
  background: #f1f5f9;
  padding: 6px 12px;  /* Увеличили */
  border-radius: 8px;
}

/* Контейнер с прокруткой */
.faq-list-container {
  flex: 1;
  overflow-y: auto;
  min-height: 0;
  padding-right: 6px;
  margin-right: -6px;
}

/* Стилизация скроллбара */
.faq-list-container::-webkit-scrollbar {
  width: 8px;  /* Увеличили */
}

.faq-list-container::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 10px;
}

.faq-list-container::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 10px;
}

.faq-list-container::-webkit-scrollbar-thumb:hover {
  background: #a1a1a1;
}

.loading-faq, .empty-faq, .error-faq {
  text-align: center;
  padding: 40px 20px;  /* Увеличили */
  color: #6b7280;
  font-size: 15px;  /* Увеличили */
  background: #f9fafb;
  border-radius: 10px;
  border: 1px dashed #d1d5db;
}

.error-faq {
  color: #b91c1c;
  background: #fee2e2;
  border-color: #fecaca;
}

.loading-faq {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

.spinner {
  width: 24px;  /* Увеличили */
  height: 24px;  /* Увеличили */
  border: 3px solid #e2e8f0;  /* Увеличили */
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.retry-btn {
  margin-top: 12px;
  padding: 10px 20px;  /* Увеличили */
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 15px;  /* Увеличили */
}

.retry-btn:hover {
  background: #2563eb;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.faq-cards-container {
  display: flex;
  flex-direction: column;
  gap: 12px;  /* Увеличили */
  padding-bottom: 15px;
}

.faq-card {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 12px;  /* Увеличили */
  overflow: hidden;
  transition: all 0.2s ease;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);  /* Увеличили */
}

.faq-card:hover {
  border-color: #9ca3af;
  box-shadow: 0 6px 12px rgba(0, 0, 0, 0.1);  /* Увеличили */
  transform: translateY(-2px);  /* Увеличили */
}

.faq-card.active {
  border-color: #3b82f6;
  box-shadow: 0 6px 16px rgba(59, 130, 246, 0.25);  /* Увеличили */
}

.faq-question {
  padding: 18px 20px;  /* Увеличили */
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  transition: background 0.2s;
  background: white;
  border-left: 4px solid transparent;
}

.faq-question:hover {
  background: #f8fafc;
  border-left-color: #3b82f6;
}

.question-content {
  display: flex;
  align-items: flex-start;
  gap: 14px;  /* Увеличили */
  flex: 1;
}

.question-icon {
  font-size: 18px;  /* Увеличили */
  flex-shrink: 0;
  color: #3b82f6;
}

.question-text {
  font-weight: 600;
  color: #1f2937;
  flex: 1;
  font-size: 15px;  /* Увеличили */
  line-height: 1.5;
}

.faq-toggle {
  width: 28px;  /* Увеличили */
  height: 28px;  /* Увеличили */
  display: flex;
  align-items: center;
  justify-content: center;
  color: #6b7280;
  transition: transform 0.3s ease;
  flex-shrink: 0;
  background: #f1f5f9;
  border-radius: 50%;
}

.faq-toggle.rotated {
  transform: rotate(180deg);
  color: #3b82f6;
  background: #dbeafe;
}

.faq-answer {
  background: #f9fafb;
  border-top: 1px solid #e5e7eb;
  animation: slideDown 0.3s ease-out;
}

.answer-content {
  padding: 18px 20px;  /* Увеличили */
  display: flex;
  gap: 14px;  /* Увеличили */
  align-items: flex-start;
}

.answer-icon {
  font-size: 18px;  /* Увеличили */
  flex-shrink: 0;
  color: #10b981;
}

.answer-text {
  color: #374151;
  line-height: 1.7;
  font-size: 15px;  /* Увеличили */
  margin: 0;
  white-space: pre-wrap;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Адаптивность */
@media (max-width: 768px) {
  .faq-section {
    padding: 0;
    height: auto;
  }

  .faq-title {
    font-size: 18px;
  }

  .faq-search-box {
    flex-direction: column;
    align-items: stretch;
    gap: 8px;
  }

  .faq-count {
    align-self: flex-start;
  }

  .faq-list-container {
    max-height: 400px;
  }

  .question-text {
    font-size: 14px;
  }

  .answer-text {
    font-size: 14px;
  }

  .faq-question {
    padding: 14px;
  }

  .answer-content {
    padding: 14px;
  }
}
</style>
