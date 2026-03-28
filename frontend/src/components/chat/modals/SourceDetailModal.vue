<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-content source-detail">
      <div class="modal-header">
        <h3>Детали источника</h3>
        <button @click="$emit('close')" class="modal-close-btn">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M18 6L6 18M6 6l12 12"/>
          </svg>
        </button>
      </div>

      <div class="modal-body">
        <div class="detail-section">
          <h4>Файл</h4>
          <p class="filename">{{ formatFilename(source.filename) || 'Не указан' }}</p>
        </div>

        <div class="detail-section" v-if="source.breadcrumbs">
          <h4>Раздел</h4>
          <p>{{ source.breadcrumbs }}</p>
        </div>

        <!-- <div class="detail-section" v-if="source.category">
          <h4>Категория</h4>
          <p>{{ source.category }}</p>
        </div> -->

        <div class="detail-section" v-if="source.summary">
          <h4>Краткое содержание</h4>
          <p>{{ source.summary }}</p>
        </div>

        <div class="detail-section" v-if="source.content">
          <h4>Полное содержание</h4>
          <div class="full-content" v-html="renderedContent"></div>
        </div>

        <div class="detail-section">
          <div class="score-header-container">
            <h4>Оценки релевантности</h4>
            <button @click="showScoreInfo = true" class="info-icon-btn" title="Что означают оценки">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="10"></circle>
                <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path>
                <line x1="12" y1="17" x2="12.01" y2="17"></line>
              </svg>
            </button>
          </div>
          <div class="scores-grid">
            <div v-if="source.score_semantic !== undefined" class="score-card semantic">
              <span class="score-label">Смысловая</span>
              <span class="score-value">{{ formatScore(source.score_semantic) }}</span>
            </div>
            <div v-if="source.score_lexical !== undefined" class="score-card lexical">
              <span class="score-label">Словесная</span>
              <span class="score-value">{{ formatScore(source.score_lexical) }}</span>
            </div>
            <div v-if="source.score_hybrid !== undefined" class="score-card hybrid">
              <span class="score-label">Общая</span>
              <span class="score-value">{{ formatScore(source.score_hybrid) }}</span>
            </div>
          </div>
        </div>

        <!-- Модальное окно с информацией об оценках -->
        <div v-if="showScoreInfo" class="score-info-overlay" @click.self="showScoreInfo = false">
          <div class="score-info-modal">
            <div class="score-info-header">
              <h4>Что означают оценки</h4>
              <button @click="showScoreInfo = false" class="score-info-close-btn">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M18 6L6 18M6 6l12 12"/>
                </svg>
              </button>
            </div>
            <div class="score-info-body">
              <div class="info-section">
                <h5>Как работает оценка релевантности</h5>
                <p>В нашей системе используется гибридная модель поиска, которая объединяет несколько способов анализа текста. Это позволяет находить точные ответы, даже если пользователь использует разговорные выражения или специфические технические термины.</p>
                <p>Итоговая оценка релевантности (Hybrid Score) складывается из четырех независимых компонентов, каждый из которых имеет свой «вес» в принятии решения.</p>
              </div>

              <div class="info-section">
                <h5>Смысловая оценка (Semantic Score)</h5>
                <p>Анализирует смысл запроса и документа с помощью векторных представлений. Позволяет находить документы, которые семантически близки к запросу, даже если они используют другие слова и формулировки.</p>
              </div>

              <div class="info-section">
                <h5>Словесная оценка (Lexical Score)</h5>
                <p>Оценивает точное совпадение слов и терминов между запросом и документом. Помогает находить документы с точными вхождениями ключевых слов, что особенно важно для технических терминов и специфических понятий.</p>
              </div>

              <div class="info-section">
                <h5>Общая оценка (Hybrid Score)</h5>
                <p>Комбинирует смысловую и словесную оценки с учётом их весовых коэффициентов. Это финальная оценка релевантности, которая используется для ранжирования документов и определения их соответствия запросу.</p>
              </div>
            </div>
          </div>
        </div>

        <!-- <div class="detail-section" v-if="source.chunk_id">
          <h4>Chunk ID</h4>
          <p class="chunk-id">{{ source.chunk_id }}</p>
        </div> -->
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { renderMarkdown } from '../../../utils/markdownRenderer'

const props = defineProps({
  source: {
    type: Object,
    required: true,
    default: () => ({})
  }
})

const emit = defineEmits(['close'])

const showScoreInfo = ref(false)

// Рендерим контент через markdownRenderer (поддержка таблиц, LaTeX, markdown)
const renderedContent = computed(() => {
  if (!props.source?.content) return ''
  return renderMarkdown(props.source.content)
})

function formatScore(score) {
  if (score === undefined || score === null || score === '') return '0%'
  // Если оценка > 1, значит она уже в процентах (0-100)
  const normalizedScore = score > 1 ? score : score * 100
  return `${normalizedScore.toFixed(0)}%`
}

function formatFilename(filename) {
  if (!filename) return ''
  // Убираем расширение .md и заменяем подчёркивания на пробелы
  return filename
    .replace(/\.md$/i, '')
    .replace(/_/g, ' ')
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
  max-width: 700px;
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

/* Контейнер для заголовка и кнопки */
.score-header-container {
  display: flex;
  align-items: flex-start;
  gap: 6px; /* Расстояние между текстом и иконкой */
  margin-bottom: 10px;
}

.score-header-container h4 {
  margin: 0;
  color: #374151;
  font-size: 15px;
  font-weight: 600;
  line-height: 16px;
}

/* Стили кнопки-иконки */
.info-icon-btn {
  background: none;
  border: none;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #9ca3af; /* Спокойный серый цвет по умолчанию */
  cursor: pointer;
  transition: all 0.2s ease;
  border-radius: 50%;
  outline: none;
}

.info-icon-btn:hover {
  color: #2563eb; /* Цвет становится синим при наведении */
  transform: scale(1.1); /* Легкое увеличение */
}

/* Дополнительно: небольшая пульсация при фокусе для доступности */
.info-icon-btn:focus-visible {
  box-shadow: 0 0 0 2px #dbeafe;
  color: #2563eb;
}

/* Убедимся, что сетка оценок стоит ровно под заголовком */
.scores-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 10px;
}

.section-header-with-help {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.section-header-with-help h4 {
  margin: 0;
  color: #374151;
  font-size: 15px;
  font-weight: 600;
}

.section-header-with-help .help-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  flex-shrink: 0;
}

.section-header-with-help .help-btn:hover {
  background: #eff6ff;
}

.section-header-with-help .help-btn img {
  opacity: 0.6;
  transition: opacity 0.2s;
}

.section-header-with-help .help-btn:hover img {
  opacity: 1;
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

.detail-section {
  margin-bottom: 20px;
}

.detail-section h4 {
  color: #374151;
  font-size: 15px;
  font-weight: 600;
  margin: 0 0 6px 0;
}

.detail-section p {
  margin: 0;
  color: #4b5563;
  line-height: 1.6;
  font-size: 14px;
}

.detail-section .filename {
  font-weight: 500;
  color: #0066cc;
  word-break: break-word;
}

.detail-section .full-content {
  background: #f9fafb;
  padding: 16px;
  border-radius: 6px;
  border: 1px solid #e5e7eb;
  max-height: 400px;
  overflow-y: auto;
  font-size: 14px;
  line-height: 1.6;
}

.detail-section .full-content h1,
.detail-section .full-content h2,
.detail-section .full-content h3,
.detail-section .full-content h4,
.detail-section .full-content h5,
.detail-section .full-content h6 {
  margin-top: 1em;
  margin-bottom: 0.5em;
  font-weight: 600;
  color: #1f2937;
}

.detail-section .full-content h1 { font-size: 1.5em; }
.detail-section .full-content h2 { font-size: 1.3em; }
.detail-section .full-content h3 { font-size: 1.2em; }
.detail-section .full-content h4 { font-size: 1.1em; }

.detail-section .full-content p {
  margin: 0.5em 0;
  color: #4b5563;
}

.detail-section .full-content ul,
.detail-section .full-content ol {
  margin: 0.5em 0;
  padding-left: 1.5em;
}

.detail-section .full-content li {
  margin: 0.25em 0;
}

.detail-section .full-content strong {
  font-weight: 600;
  color: #1f2937;
}

.detail-section .full-content code {
  background: #e5e7eb;
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
  font-size: 0.9em;
  color: #dc2626;
}

.detail-section .full-content pre {
  background: #1f2937;
  color: #f9fafb;
  padding: 12px;
  border-radius: 6px;
  overflow-x: auto;
  margin: 0.5em 0;
}

.detail-section .full-content pre code {
  background: none;
  padding: 0;
  color: inherit;
}

.detail-section .full-content a {
  color: #0066cc;
  text-decoration: underline;
}

.detail-section .full-content a:hover {
  text-decoration: none;
}

.detail-section .full-content table {
  width: 100%;
  border-collapse: collapse;
  margin: 1em 0;
  font-size: 13px;
}

.detail-section .full-content th,
.detail-section .full-content td {
  border: 1px solid #d1d5db;
  padding: 8px 12px;
  text-align: left;
}

.detail-section .full-content th {
  background: #f3f4f6;
  font-weight: 600;
  color: #1f2937;
}

.detail-section .full-content tr:nth-child(even) {
  background: #f9fafb;
}

.detail-section .full-content tr:hover {
  background: #f3f4f6;
}

.detail-section .chunk-id {
  font-family: monospace;
  background: #f3f4f6;
  padding: 6px 10px;
  border-radius: 4px;
  font-size: 13px;
  color: #4b5563;
}

.scores-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 12px;
  margin-top: 8px;
}

.score-card {
  padding: 12px;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.score-card.semantic {
  background: #dbeafe;
  color: #1e40af;
}

.score-card.lexical {
  background: #fef3c7;
  color: #92400e;
}

.score-card.hybrid {
  background: #dcfce7;
  color: #166534;
}

.score-card .score-label {
  font-size: 12px;
  font-weight: 500;
  margin-bottom: 4px;
}

.score-card .score-value {
  font-size: 16px;
  font-weight: 700;
}

/* Стили для модального окна с информацией об оценках */
.score-info-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1001;
}

.score-info-modal {
  background: white;
  border-radius: 12px;
  max-width: 500px;
  width: 90%;
  max-height: 80vh;
  overflow: hidden;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
}

.score-info-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #e5e7eb;
  background: #f9fafb;
}

.score-info-header h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.score-info-close-btn {
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

.score-info-close-btn:hover {
  background: #e5e7eb;
  color: #1f2937;
}

.score-info-body {
  padding: 20px;
  max-height: calc(80vh - 70px);
  overflow-y: auto;
}

.score-info-body .info-section {
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid #e5e7eb;
}

.score-info-body .info-section:last-child {
  border-bottom: none;
  margin-bottom: 0;
  padding-bottom: 0;
}

.score-info-body .info-section h5 {
  color: #1e3a8a;
  font-size: 14px;
  font-weight: 600;
  margin: 0 0 6px 0;
}

.score-info-body .info-section p {
  margin: 0;
  color: #4b5563;
  line-height: 1.6;
  font-size: 13px;
}
</style>
