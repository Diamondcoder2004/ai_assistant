<template>
  <aside class="sources-panel" v-if="expandedMessage && expandedMessage.sources?.length > 0">
    <div class="sources-header">
      <h3>Источники ответа</h3>
      <button @click="$emit('close')" class="close-sources-btn">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M18 6L6 18M6 6l12 12"/>
        </svg>
      </button>
    </div>
    <div class="sources-list">
      <div
        v-for="(source, idx) in expandedMessage.sources"
        :key="idx"
        :id="'source-' + (idx + 1)"
        class="source-card"
        @click="$emit('openSource', source)"
      >
        <div class="source-number">{{ idx + 1 }}</div>
        <div class="source-info">
          <div class="source-filename">{{ removeExtension(source.filename) }}</div>
          <div class="source-breadcrumbs" v-if="source.breadcrumbs && source.breadcrumbs.trim()">{{ formatBreadcrumbs(source.breadcrumbs) }}</div>
          <div class="source-summary">{{ truncate(source.summary || 'Нет описания', 80) }}</div>
          <div class="source-scores">
            <span class="score semantic">Смысл: {{ formatScore(source.score_semantic) }}</span>
            <span class="score lexical">Слова: {{ formatScore(source.score_lexical) }}</span>
            <span class="score hybrid">Общая: {{ formatScore(source.score_hybrid) }}</span>
          </div>
        </div>
      </div>
    </div>
  </aside>
</template>

<script setup>
defineProps({
  expandedMessage: {
    type: Object,
    default: null
  }
})

defineEmits(['close', 'openSource'])

function truncate(text, length) {
  if (!text) return ''
  return text.length > length ? text.slice(0, length) + '...' : text
}

function removeExtension(filename) {
  if (!filename) return ''
  // Убираем расширение .md и заменяем подчёркивания на пробелы
  return filename
    .replace(/\.md$/i, '')
    .replace(/_/g, ' ')
}

function formatScore(score) {
  if (score === undefined || score === null || score === '') return '0%'
  // Если оценка > 1, значит она уже в процентах
  const normalizedScore = score > 1 ? score : score * 100
  return `${normalizedScore.toFixed(0)}%`
}

function formatBreadcrumbs(breadcrumbs) {
  if (!breadcrumbs) return ''
  // Убираем специальные термины и упрощаем путь
  return breadcrumbs
    .replace(/→/g, ' → ')
}
</script>

<style scoped>
.sources-panel {
  width: 400px;
  background: #ffffff;
  border-left: 1px solid #ddd;
  padding: 0;
  overflow-y: auto;
  flex-shrink: 0;
  height: 100%;
}

.sources-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #e5e7eb;
  background: #f9fafb;
  position: sticky;
  top: 0;
  z-index: 10;
}

.sources-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.close-sources-btn {
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

.close-sources-btn:hover {
  background: #e5e7eb;
  color: #1f2937;
}

.sources-list {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.source-card {
  display: flex;
  gap: 12px;
  padding: 12px;
  background: #f9f9f9;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  scroll-margin-top: 20px;
}

.source-card:target {
  background: #eff6ff;
  border-color: #0066cc;
  box-shadow: 0 0 0 2px rgba(0, 102, 204, 0.2);
}

.source-card.highlight {
  background: #eff6ff;
  border-color: #0066cc;
  box-shadow: 0 0 0 2px rgba(0, 102, 204, 0.2);
}

.source-card:hover {
  background: #eff6ff;
  border-color: #3b82f6;
  transform: translateX(2px);
}

.source-number {
  width: 28px;
  height: 28px;
  background: #0066cc;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 14px;
  flex-shrink: 0;
}

.source-info {
  flex: 1;
  min-width: 0;
}

.source-filename {
  font-weight: 600;
  font-size: 14px;
  color: #1f2937;
  margin-bottom: 4px;
  word-break: break-word;
}

.source-breadcrumbs {
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 4px;
  font-style: italic;
}

.source-summary {
  font-size: 12px;
  color: #4b5563;
  margin-bottom: 6px;
  line-height: 1.4;
}

.source-scores {
  display: flex;
  gap: 8px;
}

.score {
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
}

.score.semantic {
  background: #dbeafe;
  color: #1e40af;
}

.score.lexical {
  background: #fef3c7;
  color: #92400e;
}

.score.hybrid {
  background: #dcfce7;
  color: #166534;
}
</style>
