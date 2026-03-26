<template>
  <div class="messages-container" ref="messagesContainer">
    <!-- Приветственное сообщение, если чат пуст -->
    <div v-if="messages.length === 0" class="welcome-message">
      <div class="welcome-icon">👋</div>
      <h2>Добро пожаловать в чат-бот!</h2>
      <p>Я помогу вам с вопросами о технологическом присоединении, тарифах и услугах компании.</p>
    </div>

    <!-- Сообщения -->
    <div
      v-for="msg in messages"
      :key="msg.id"
      class="message"
      :class="{ 'user-message': msg.role === 'user', 'assistant-message': msg.role === 'assistant' }"
    >
      <div class="message-bubble">
        <div class="message-content" :class="msg.role === 'assistant' ? 'markdown-body' : 'user-content'" @click="(e) => handleSourceClick(e, msg)">
          <!-- Индикатор печати для пустого сообщения во время streaming -->
          <div v-if="msg.content === '' && isLoading" class="typing-indicator">
            <span class="dot"></span>
            <span class="dot"></span>
            <span class="dot"></span>
          </div>
          <template v-else-if="msg.role === 'user'">
            {{ msg.content }}
          </template>
          <div v-else v-html="renderMarkdown(msg.content)"></div>
        </div>

        <!-- Кнопка для показа источников (только для ассистента) -->
        <div v-if="msg.role === 'assistant' && msg.sources?.length" class="message-footer">
          <button
            @click="$emit('toggleSources', msg)"
            class="show-sources-btn"
            :class="{ 'active': expandedMessageId === msg.id }"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M4 6h16v12H4z"/>
              <path d="M8 10h8v2H8z"/>
            </svg>
            {{ expandedMessageId === msg.id ? 'Скрыть источники' : 'Показать источники' }}
          </button>
        </div>

        <!-- Фидбек (только для ассистента) -->
        <div v-if="msg.role === 'assistant' && msg.queryId" class="feedback">
          <!-- Кнопка копирования слева -->
          <button
            @click="copyToClipboard(msg.content)"
            class="feedback-btn copy-btn"
            :class="{ 'copied': copySuccess }"
            title="Копировать ответ"
          >
            <svg v-if="!copySuccess" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
              <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
            </svg>
            <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="20 6 9 17 4 12"/>
            </svg>
            <span class="copy-label">Копировать</span>
          </button>
          
          <div class="feedback-divider"></div>
          
          <!-- Кнопки оценки справа -->
          <span class="feedback-label">Оцените ответ:</span>
          <button
            @click="$emit('feedback', msg.queryId, 'like')"
            class="feedback-btn"
            :class="{ active: feedbacks[msg.queryId]?.feedback_type === 'like' }"
            title="Полезно"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M7 10v12M15 5.88L14 10h5.83a2 2 0 0 1 1.92 2.56l-2.33 8A2 2 0 0 1 17.5 22H4a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2h2.76a2 2 0 0 0 1.79-1.11L12 2a3 3 0 0 1 3 3z"/>
            </svg>
          </button>
          <button
            @click="$emit('feedback', msg.queryId, 'dislike')"
            class="feedback-btn"
            :class="{ active: feedbacks[msg.queryId]?.feedback_type === 'dislike' }"
            title="Не полезно"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M17 14V2M9 18.12L10 14H4.17a2 2 0 0 1-1.92-2.56l2.33-8A2 2 0 0 1 6.5 2H20a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2h-2.76a2 2 0 0 0-1.79 1.11L12 22a3 3 0 0 1-3-3z"/>
            </svg>
          </button>
          <button
            @click="$emit('openStarRating', msg.queryId)"
            class="feedback-btn star-btn"
            :class="{ active: feedbacks[msg.queryId]?.feedback_type === 'star' }"
            title="Оценить звёздами"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
            </svg>
          </button>
        </div>
      </div>
    </div>

    <!-- Индикатор загрузки для streaming -->
    <div v-if="isLoading && messages.length > 0" class="streaming-indicator">
      <span class="pulse-dot"></span>
      <span>Генерация ответа...</span>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { marked } from 'marked'
import katex from 'katex'
import 'katex/dist/katex.min.css'
import { useHotkeysStore } from '../../stores/hotkeysStore'

const props = defineProps({
  messages: {
    type: Array,
    required: true,
    default: () => []
  },
  isLoading: {
    type: Boolean,
    default: false
  },
  expandedMessageId: {
    type: [String, Number],
    default: null
  },
  feedbacks: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['toggleSources', 'feedback', 'openStarRating', 'scrollToSource', 'new-chat', 'show-history', 'focus-input'])

const messagesContainer = ref(null)

// Рендеринг markdown с кликабельными источниками и LaTeX формулами
function renderMarkdown(text) {
  if (!text) return ''
  
  // Преобразуем [1], [2] и т.д. в кликабельные ссылки
  const textWithLinks = text.replace(/\[(\d+)\]/g, (match, num) => {
    return `<a href="#source-${num}" class="source-link" data-source="${num}">${match}</a>`
  })
  
  // Обработка LaTeX формул между $$
  const textWithMath = textWithLinks.replace(/\$\$([\s\S]+?)\$\$/g, (match, formula) => {
    try {
      const html = katex.renderToString(formula.trim(), {
        throwOnError: false,
        displayMode: true
      })
      return html
    } catch (err) {
      console.error('LaTeX render error:', err)
      return match // Возвращаем как есть при ошибке
    }
  })
  
  // Обработка inline формул между $ (но не внутри ссылок)
  const finalText = textWithMath.replace(/\$([^\n$]+?)\$/g, (match, formula) => {
    // Пропускаем, если это уже обработанная формула или ссылка
    if (match.includes('<a') || match.includes('href')) return match
    try {
      const html = katex.renderToString(formula.trim(), {
        throwOnError: false,
        displayMode: false
      })
      return html
    } catch (err) {
      return match
    }
  })
  
  return marked.parse(finalText)
}

// Обработка клика на источник
function handleSourceClick(event, msg) {
  const sourceLink = event.target.closest('.source-link')
  if (sourceLink) {
    event.preventDefault()
    const sourceNum = parseInt(sourceLink.dataset.source)
    emit('scrollToSource', { sourceNum, messageId: msg.id })
  }
}

// Копирование в буфер обмена
const copySuccess = ref(false)

async function copyToClipboard(text) {
  try {
    // Очищаем текст от Markdown для копирования
    const cleanText = text.replace(/\[(\d+)\]/g, '') // Убираем ссылки на источники
    
    // Проверяем поддержку Clipboard API
    if (navigator.clipboard && navigator.clipboard.writeText) {
      await navigator.clipboard.writeText(cleanText)
    } else {
      // Fallback для старых браузеров или HTTP
      const textarea = document.createElement('textarea')
      textarea.value = cleanText
      textarea.style.position = 'fixed'
      textarea.style.opacity = '0'
      document.body.appendChild(textarea)
      textarea.select()
      document.execCommand('copy')
      document.body.removeChild(textarea)
    }

    // Визуальное подтверждение
    copySuccess.value = true
    setTimeout(() => {
      copySuccess.value = false
    }, 2000)
  } catch (err) {
    console.error('Ошибка копирования:', err)
    alert('Не удалось скопировать текст')
  }
}

// Обработка горячих клавиш
const hotkeysStore = useHotkeysStore()

function handleGlobalKeydown(event) {
  // Игнорируем горячие клавиши если фокус в поле ввода
  const activeElement = document.activeElement
  const isInputFocused = activeElement.tagName === 'TEXTAREA' || 
                         activeElement.tagName === 'INPUT' ||
                         activeElement.isContentEditable
  
  // Для sendMessage и newLine всегда игнорируем если фокус в input
  // Для остальных горячих клавиш тоже игнорируем если фокус в input
  if (isInputFocused) {
    return
  }

  const combination = hotkeysStore.captureKeyCombination(event)

  // Проверяем совпадения с горячими клавишами
  for (const [action, keyCombination] of Object.entries(hotkeysStore.hotkeys)) {
    // Пропускаем отключенные горячие клавиши
    if (!hotkeysStore.enabled[action]) {
      continue
    }
    
    if (combination === keyCombination) {
      event.preventDefault()

      switch (action) {
        case 'newChat':
          emit('new-chat')
          break
        case 'showHistory':
          emit('show-history')
          break
        case 'focusInput':
          emit('focus-input')
          break
        case 'toggleSources':
          emit('toggle-sources')
          break
        case 'copyLastAnswer':
          const lastMessage = props.messages.filter(m => m.role === 'assistant').pop()
          if (lastMessage?.content) {
            copyToClipboard(lastMessage.content)
          }
          break
      }

      return false
    }
  }
}

// Подписка на глобальные горячие клавиши
onMounted(() => {
  window.addEventListener('keydown', handleGlobalKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleGlobalKeydown)
})

// Автоматическая прокрутка вниз при новых сообщениях
watch(() => props.messages.length, () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
})
</script>

<style scoped>
.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 15px;
  min-height: 0;
}

/* Приветственное сообщение */
.welcome-message {
  text-align: center;
  padding: 40px 20px;
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
  border-radius: 12px;
  margin: 20px;
}

.welcome-icon {
  font-size: 64px;
  margin-bottom: 16px;
}

.welcome-message h2 {
  color: #0066cc;
  margin: 0 0 12px 0;
  font-size: 24px;
}

.welcome-message > p {
  color: #4b5563;
  margin: 0 0 24px 0;
  font-size: 16px;
  line-height: 1.5;
}

/* Сообщения */
.message {
  display: flex;
  margin-bottom: 10px;
}

.user-message {
  justify-content: flex-end;
}

.assistant-message {
  justify-content: flex-start;
}

.message-bubble {
  max-width: 80%;
  padding: 12px 16px;
  border-radius: 18px;
  background: #f1f1f1;
  color: #333;
  word-wrap: break-word;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(0, 0, 0, 0.05);
}

.user-message .message-bubble {
  background: #0066cc;
  color: white;
  border-bottom-right-radius: 4px;
  border-color: #0052a3;
}

.assistant-message .message-bubble {
  background: #e9ecef;
  border-bottom-left-radius: 4px;
  border-color: #ced4da;
}

.message-content {
  white-space: pre-wrap;
}

/* Стили для markdown */
.markdown-body {
  white-space: normal;
}

.markdown-body :deep(h1),
.markdown-body :deep(h2),
.markdown-body :deep(h3),
.markdown-body :deep(h4),
.markdown-body :deep(h5),
.markdown-body :deep(h6) {
  margin: 16px 0 8px 0;
  font-weight: 600;
  line-height: 1.4;
}

.markdown-body :deep(h1) { font-size: 1.5em; }
.markdown-body :deep(h2) { font-size: 1.3em; }
.markdown-body :deep(h3) { font-size: 1.1em; }
.markdown-body :deep(h4) { font-size: 1em; }

.markdown-body :deep(p) {
  margin: 8px 0;
  line-height: 1.6;
}

.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  margin: 8px 0;
  padding-left: 24px;
}

.markdown-body :deep(li) {
  margin: 4px 0;
}

.markdown-body :deep(strong) {
  font-weight: 600;
}

.markdown-body :deep(blockquote) {
  margin: 12px 0;
  padding: 8px 12px;
  border-left: 3px solid #0066cc;
  background: #f0f9ff;
  border-radius: 4px;
}

.markdown-body :deep(code) {
  background: rgba(0, 0, 0, 0.1);
  padding: 2px 6px;
  border-radius: 3px;
  font-family: monospace;
  font-size: 0.9em;
}

.markdown-body :deep(pre) {
  background: #f6f8fa;
  padding: 12px;
  border-radius: 6px;
  overflow-x: auto;
  margin: 12px 0;
}

.markdown-body :deep(pre code) {
  background: none;
  padding: 0;
}

/* LaTeX формулы */
.markdown-body :deep(.katex-display) {
  margin: 16px 0;
  overflow-x: auto;
  overflow-y: hidden;
}

.markdown-body :deep(.katex) {
  font-size: 1.1em;
}

/* Кликабельные источники */
.markdown-body :deep(.source-link) {
  color: #0066cc;
  text-decoration: none;
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 4px;
  background: rgba(0, 102, 204, 0.1);
  transition: all 0.2s;
  cursor: pointer;
}

.markdown-body :deep(.source-link:hover) {
  background: #0066cc;
  color: white;
}

/* Таблицы */
.markdown-body :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 16px 0;
  font-size: 14px;
  overflow-x: auto;
  display: block;
}

.markdown-body :deep(thead) {
  background: #f0f9ff;
}

.markdown-body :deep(th) {
  border: 1px solid #cbd5e1;
  padding: 10px 12px;
  text-align: left;
  font-weight: 600;
  color: #1e40af;
  background: #dbeafe;
}

.markdown-body :deep(td) {
  border: 1px solid #e2e8f0;
  padding: 10px 12px;
  color: #334155;
}

.markdown-body :deep(tr:nth-child(even)) {
  background: #f8fafc;
}

.markdown-body :deep(tr:hover) {
  background: #f1f5f9;
}

/* Адаптивность для таблиц на мобильных */
@media (max-width: 768px) {
  .markdown-body :deep(table) {
    font-size: 12px;
  }
  
  .markdown-body :deep(th),
  .markdown-body :deep(td) {
    padding: 6px 8px;
  }
}

.markdown-body :deep(hr) {
  border: none;
  border-top: 1px solid #e5e7eb;
  margin: 16px 0;
}

/* Стили для пользовательских сообщений */
.user-content {
  white-space: pre-wrap;
}

.message-footer {
  margin-top: 8px;
  display: flex;
  justify-content: flex-start;
}

.show-sources-btn {
  background: none;
  border: 1px solid #cbd5e1;
  border-radius: 4px;
  padding: 6px 12px;
  font-size: 12px;
  color: #4b5563;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s;
}

.show-sources-btn:hover {
  background: #f1f5f9;
  border-color: #94a3b8;
}

.show-sources-btn.active {
  background: #e0f2fe;
  border-color: #3b82f6;
  color: #1e3a8a;
}

/* Фидбек */
.feedback {
  display: flex;
  gap: 8px;
  margin-top: 8px;
  justify-content: flex-end;
  align-items: center;
}

.feedback-divider {
  width: 1px;
  height: 20px;
  background: #cbd5e1;
  margin: 0 4px;
}

.feedback-label {
  font-size: 12px;
  color: #6b7280;
  margin-right: 4px;
}

.feedback-btn {
  background: none;
  border: 1px solid #cbd5e1;
  border-radius: 4px;
  padding: 4px 8px;
  cursor: pointer;
  color: #64748b;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.feedback-btn.copy-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
}

.feedback-btn.copy-btn .copy-label {
  font-size: 13px;
  font-weight: 500;
}

.feedback-btn.copy-btn:hover {
  background: #f0fdf4;
  border-color: #22c55e;
  color: #16a34a;
}

.feedback-btn.copy-btn.copied {
  background: #dcfce7;
  border-color: #22c55e;
  color: #16a34a;
}

.feedback-btn:hover:not(.active) {
  background: #f1f5f9;
  border-color: #94a3b8;
}

.feedback-btn.active {
  background: #e0f2fe;
  border-color: #3b82f6;
  color: #1e3a8a;
}

.star-btn.active {
  background: #fef9c3;
  border-color: #eab308;
  color: #854d0e;
}

/* Индикатор streaming */
.streaming-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  color: #6b7280;
  font-size: 14px;
}

.pulse-dot {
  width: 8px;
  height: 8px;
  background: #0066cc;
  border-radius: 50%;
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.5;
    transform: scale(1.2);
  }
}

/* Индикатор набора текста */
.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 4px 0;
}

.typing-indicator .dot {
  width: 8px;
  height: 8px;
  background: #6b7280;
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out;
}

.typing-indicator .dot:nth-child(1) { animation-delay: -0.32s; }
.typing-indicator .dot:nth-child(2) { animation-delay: -0.16s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}
</style>
