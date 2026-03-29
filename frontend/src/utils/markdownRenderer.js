/**
 * Единый Markdown Renderer с поддержкой LaTeX формул
 * 
 * Использует marked для парсинга markdown и KaTeX для рендеринга LaTeX
 */

import { marked } from 'marked'
import katex from 'katex'
import 'katex/dist/katex.min.css'

// Настройка опций marked
marked.setOptions({
  breaks: true,
  gfm: true,
  headerIds: true,
  mangle: false
})

/**
 * Рендеринг markdown текста с поддержкой LaTeX
 * @param {string} text - Markdown текст
 * @returns {string} - HTML строка
 */
export function renderMarkdown(text) {
  if (!text) return ''

  try {
    let processedText = text

    // 1. Сначала обрабатываем блочные LaTeX формулы $$...$$
    processedText = processedText.replace(/\$\$([\s\S]*?)\$\$/g, (match, latex) => {
      try {
        const rendered = katex.renderToString(latex.trim(), {
          throwOnError: false,
          displayMode: true
        })
        return `<div class="katex-display">${rendered}</div>`
      } catch (e) {
        return match
      }
    })

    // 2. Обрабатываем блочные LaTeX формулы \[...\] (альтернативный синтаксис)
    processedText = processedText.replace(/\\\[([\s\S]*?)\\\]/g, (match, latex) => {
      try {
        const rendered = katex.renderToString(latex.trim(), {
          throwOnError: false,
          displayMode: true
        })
        return `<div class="katex-display">${rendered}</div>`
      } catch (e) {
        return match
      }
    })

    // 3. Сохраняем цитаты [1], [2] во временные плейсхолдеры
    const citations = []
    processedText = processedText.replace(/\[(\d+)\]/g, (match, num) => {
      const index = citations.length
      citations.push(`<a href="#source-${num}" class="source-link" data-source="${num}">${match}</a>`)
      return `__CITATION_${index}__`
    })

    // 4. Обрабатываем inline LaTeX формулы \(...\) (альтернативный синтаксис)
    processedText = processedText.replace(/\\\(.*?\\\)/g, (match, latex) => {
      try {
        const rendered = katex.renderToString(latex.trim(), {
          throwOnError: false,
          displayMode: false
        })
        return `<span class="katex-inline">${rendered}</span>`
      } catch (e) {
        return match
      }
    })

    // 5. Обрабатываем inline LaTeX формулы $...$ (но не внутри ссылок)
    processedText = processedText.replace(/\$([^\n$]+?)\$/g, (match, latex) => {
      // Пропускаем, если это уже обработанная ссылка
      if (match.includes('<a') || match.includes('href') || match.includes('__CITATION_')) return match
      try {
        const rendered = katex.renderToString(latex.trim(), {
          throwOnError: false,
          displayMode: false
        })
        return `<span class="katex-inline">${rendered}</span>`
      } catch (e) {
        return match
      }
    })

    // 6. Восстанавливаем цитаты из плейсхолдеров
    processedText = processedText.replace(/__CITATION_(\d+)__/g, (match, index) => {
      return citations[parseInt(index)] || match
    })

    // 7. Удаляем экранирование для \[ и \] которые остались (не были формулами)
    processedText = processedText.replace(/\\\[/g, '[').replace(/\\\]/g, ']')

    return marked(processedText)
  } catch (e) {
    console.error('Markdown render error:', e)
    return escapeHtml(text)
  }
}

/**
 * Обработчик кликов по источникам в markdown
 * @param {Event} event - Клик событие
 * @param {Object} message - Сообщение с источниками
 * @param {Function} emit - Vue emit функция
 */
export function handleSourceClick(event, message, emit) {
  const sourceLink = event.target.closest('.source-link')
  if (sourceLink) {
    event.preventDefault()
    event.stopPropagation()
    const sourceNum = parseInt(sourceLink.dataset.source)
    if (emit) {
      emit('scrollToSource', { sourceNum, messageId: message.id })
    }
  }
}

// Экранирование HTML
function escapeHtml(html) {
  return html
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

export default {
  renderMarkdown,
  handleSourceClick
}
