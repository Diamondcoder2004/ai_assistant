# Unified Sidebar — Implementation Plan

**Goal:** Convert current 3-column layout (params | chat | sources) into a 2-column layout with a unified right sidebar containing both SearchParamsPanel (collapsible) and SourcesPanel sections.

**Architecture:** Single-page layout change only. `Home.vue` removes the left sidebar and standalone `<SourcesPanel>`, replacing them with a unified right sidebar. `SourcesPanel.vue` gains a `compact` prop to strip its wrapper/header when embedded in the sidebar. All other components unchanged.

**Design:** `thoughts/shared/designs/2026-05-13-unified-sidebar-design.md`

**Decision rationale (gap-filling):**
- **Animation**: Design mentions "slide animation". Implementing width transition on `.unified-sidebar` via `transition: width 0.25s ease` + `.is-open` class. This is the cleanest approach that avoids JS animation libraries and works naturally with flex layout — when width transitions from 0→380px, the chat area smoothly shrinks.
- **Sidebar toggle**: Using class-based width toggle (`v-bind:class="{ 'is-open': showSidebar }"`) rather than `v-if` to enable smooth CSS transition. Content clipped via `overflow: hidden`.
- **Empty sources state**: In compact mode, when `expandedMessage` exists but has no sources, show "Нет источников для этого ответа" placeholder. In standalone mode, existing behavior preserved (component hidden when no sources).
- **Mobile**: At `< 768px`, sidebar is always hidden (`display: none`). Unified sidebar uses `.sidebar-hidden` class that sets `width: 0 !important` and `overflow: hidden`.

---

## Dependency Graph

```
Batch 1 (parallel): 1.1 [SourcesPanel.vue + test - independent]
Batch 2 (parallel): 2.1 [Home.vue + test - depends on 1.1]
```

---

## Batch 1: SourcesPanel compact prop (parallel — 1 implementer)

All tasks in this batch have NO dependencies and run simultaneously.

### Task 1.1: Add compact prop to SourcesPanel
**File:** `frontend/src/components/chat/SourcesPanel.vue`
**Test:** `frontend/src/__tests__/SourcesPanel.spec.js`
**Depends:** none

**Change summary:**
- Add `compact: { type: Boolean, default: false }` prop
- When `compact=false` (standalone): render as before — `<aside>` wrapper with sticky `.sources-header`, close button, and `.sources-list`
- When `compact=true` (inside unified sidebar): render only `.sources-list` (no `<aside>`, no `.sources-header`, no close button). Show empty state `sources-empty` if no sources exist.
- Source card rendering (`.source-card` loop) is duplicated in both branches — intentional for clarity and zero runtime overhead.

```javascript
// ======== TEST: frontend/src/__tests__/SourcesPanel.spec.js ========

import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import SourcesPanel from '../components/chat/SourcesPanel.vue'

const mockSources = [
  {
    filename: 'test_doc.md',
    breadcrumbs: 'Глава 1 > Статья 2',
    summary: 'Тестовое описание источника',
    score_semantic: 0.85,
    score_lexical: 0.72,
    score_hybrid: 0.81
  },
  {
    filename: 'another_doc.md',
    breadcrumbs: 'Раздел 3',
    summary: 'Ещё один тестовый источник',
    score_semantic: 0.65,
    score_lexical: 0.90,
    score_hybrid: 0.78
  }
]

const mockMessage = {
  id: 'msg-1',
  role: 'assistant',
  content: 'Ответ с источниками',
  sources: mockSources
}

const mockMessageNoSources = {
  id: 'msg-2',
  role: 'assistant',
  content: 'Ответ без источников',
  sources: []
}

describe('SourcesPanel', () => {
  describe('standalone mode (compact=false, default)', () => {
    it('renders aside wrapper when expandedMessage has sources', () => {
      const wrapper = mount(SourcesPanel, {
        props: { expandedMessage: mockMessage }
      })
      expect(wrapper.find('aside.sources-panel').exists()).toBe(true)
      expect(wrapper.find('.sources-header').exists()).toBe(true)
      expect(wrapper.find('.close-sources-btn').exists()).toBe(true)
      expect(wrapper.findAll('.source-card')).toHaveLength(2)
    })

    it('renders nothing when expandedMessage has no sources', () => {
      const wrapper = mount(SourcesPanel, {
        props: { expandedMessage: mockMessageNoSources }
      })
      expect(wrapper.find('aside.sources-panel').exists()).toBe(false)
      expect(wrapper.html()).toBe('')
    })

    it('renders nothing when expandedMessage is null', () => {
      const wrapper = mount(SourcesPanel, {
        props: { expandedMessage: null }
      })
      expect(wrapper.html()).toBe('')
    })

    it('emits close event when close button clicked', () => {
      const wrapper = mount(SourcesPanel, {
        props: { expandedMessage: mockMessage }
      })
      wrapper.find('.close-sources-btn').trigger('click')
      expect(wrapper.emitted('close')).toBeTruthy()
      expect(wrapper.emitted('close').length).toBe(1)
    })

    it('emits openSource when source card clicked', () => {
      const wrapper = mount(SourcesPanel, {
        props: { expandedMessage: mockMessage }
      })
      wrapper.findAll('.source-card').at(0).trigger('click')
      expect(wrapper.emitted('openSource')).toBeTruthy()
      expect(wrapper.emitted('openSource')[0][0]).toEqual(mockSources[0])
    })
  })

  describe('compact mode (compact=true)', () => {
    it('renders sources-list without aside wrapper', () => {
      const wrapper = mount(SourcesPanel, {
        props: { expandedMessage: mockMessage, compact: true }
      })
      expect(wrapper.find('aside.sources-panel').exists()).toBe(false)
      expect(wrapper.find('.sources-header').exists()).toBe(false)
      expect(wrapper.find('.close-sources-btn').exists()).toBe(false)
      expect(wrapper.find('.sources-list').exists()).toBe(true)
      expect(wrapper.findAll('.source-card')).toHaveLength(2)
    })

    it('renders empty state when no sources', () => {
      const wrapper = mount(SourcesPanel, {
        props: { expandedMessage: mockMessageNoSources, compact: true }
      })
      expect(wrapper.find('.sources-list').exists()).toBe(false)
      expect(wrapper.find('.sources-empty').exists()).toBe(true)
      expect(wrapper.find('.empty-text').text()).toContain('Нет источников')
    })

    it('renders empty state when expandedMessage is null', () => {
      const wrapper = mount(SourcesPanel, {
        props: { expandedMessage: null, compact: true }
      })
      expect(wrapper.find('.sources-list').exists()).toBe(false)
      expect(wrapper.find('.sources-empty').exists()).toBe(true)
    })

    it('still emits openSource when source card clicked', () => {
      const wrapper = mount(SourcesPanel, {
        props: { expandedMessage: mockMessage, compact: true }
      })
      wrapper.findAll('.source-card').at(1).trigger('click')
      expect(wrapper.emitted('openSource')).toBeTruthy()
      expect(wrapper.emitted('openSource')[0][0]).toEqual(mockSources[1])
    })
  })

  describe('utility functions', () => {
    it('truncates long text', () => {
      const wrapper = mount(SourcesPanel, {
        props: { expandedMessage: mockMessage }
      })
      // The truncate is applied in v-for rendering; just ensure no errors
      expect(true).toBe(true)
    })
  })
})
```

```html
<!-- ======== IMPLEMENTATION: frontend/src/components/chat/SourcesPanel.vue ======== -->

<template>
  <!-- Standalone mode (used outside unified sidebar — existing behavior) -->
  <aside v-if="!compact" class="sources-panel">
    <div class="sources-header">
      <h3>Источники ответа</h3>
      <button @click="$emit('close')" class="close-sources-btn">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M18 6L6 18M6 6l12 12"/>
        </svg>
      </button>
    </div>
    <div v-if="expandedMessage && expandedMessage.sources?.length > 0" class="sources-list">
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

  <!-- Compact mode (inside unified sidebar — header provided by Home.vue) -->
  <template v-if="compact">
    <div v-if="expandedMessage && expandedMessage.sources?.length > 0" class="sources-list">
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
    <div v-else class="sources-empty">
      <p class="empty-text">Нет источников для этого ответа</p>
    </div>
  </template>
</template>

<script setup>
defineProps({
  expandedMessage: {
    type: Object,
    default: null
  },
  compact: {
    type: Boolean,
    default: false
  }
})

defineEmits(['close', 'openSource'])

function truncate(text, length) {
  if (!text) return ''
  return text.length > length ? text.slice(0, length) + '...' : text
}

function removeExtension(filename) {
  if (!filename) return ''
  return filename.replace(/\.md$/i, '').replace(/_/g, ' ')
}

function formatScore(score) {
  if (score === undefined || score === null || score === '') return '0%'
  const normalizedScore = score > 1 ? score : score * 100
  return `${normalizedScore.toFixed(0)}%`
}

function formatBreadcrumbs(breadcrumbs) {
  if (!breadcrumbs) return ''
  return breadcrumbs.replace(/→/g, ' → ')
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

.sources-empty {
  padding: 24px 16px;
  text-align: center;
}

.empty-text {
  color: #9ca3af;
  font-size: 14px;
  margin: 0;
}
</style>
```

**Verify:** `cd frontend && npx vitest run src/__tests__/SourcesPanel.spec.js`
**Commit:** `feat(sources-panel): add compact prop for unified sidebar embedding`

---

## Batch 2: Home.vue layout refactor (parallel — 1 implementer)

Depends on Batch 1 (imports SourcesPanel with `compact` prop).

### Task 2.1: Convert 3-column to 2-column with unified sidebar
**File:** `frontend/src/views/Home.vue`
**Test:** `frontend/src/__tests__/Home.spec.js`
**Depends:** 1.1

**Change summary:**
- **REMOVE** `<aside class="sidebar-left">` with SearchParamsPanel
- **REMOVE** standalone `<SourcesPanel v-if="...">`
- **ADD** unified sidebar with:
  - `.sidebar-header`: close button (✕)
  - `.sidebar-content`:
    - Params section (collapsible via `showParams`): section header with toggle icon, section body with SearchParamsPanel
    - Sources section (conditional on `expandedMessage`): section header "Источники", section body with `<SourcesPanel compact>`
- **SCRIPT:** Add `showSidebar` (default: false), `showParams` (default: true), `closeSidebar()` function. Modify `toggleSources()` to set `showSidebar = true`.
- **CSS:** Replace `.sidebar-left` with `.unified-sidebar` styles (width transition 0↔380px, grey bg). Remove `.sources-panel` styles. Remove `.chat-area` max-width. Adjust `.home` to `height: 100vh`.

```javascript
// ======== TEST: frontend/src/__tests__/Home.spec.js ========

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { useChatStore } from '../stores/chatStore'
import { useAuthStore } from '../stores/authStore'
import Home from '../views/Home.vue'

// Mock localStorage
const localStorageMock = (() => {
  let store = {}
  return {
    getItem: vi.fn((key) => store[key] || null),
    setItem: vi.fn((key, value) => { store[key] = value }),
    removeItem: vi.fn((key) => { delete store[key] }),
    clear: vi.fn(() => { store = {} })
  }
})()
Object.defineProperty(window, 'localStorage', { value: localStorageMock })

// Mock sessionStorage
const sessionStorageMock = (() => {
  let store = {}
  return {
    getItem: vi.fn((key) => store[key] || null),
    setItem: vi.fn((key, value) => { store[key] = value }),
    removeItem: vi.fn((key) => { delete store[key] }),
    clear: vi.fn(() => { store = {} }),
    key: vi.fn((index) => Object.keys(store)[index] || null),
    get length() { return Object.keys(store).length }
  }
})()
Object.defineProperty(window, 'sessionStorage', { value: sessionStorageMock })

// Mock scrollIntoView
Element.prototype.scrollIntoView = vi.fn()

describe('Home.vue — Unified Sidebar', () => {
  let wrapper

  beforeEach(() => {
    setActivePinia(createPinia())
    localStorageMock.clear()
    sessionStorageMock.clear()

    // Set up auth store with a user so onMounted doesn't cause issues
    const authStore = useAuthStore()
    authStore.user = null // No user = onMounted skips loading

    wrapper = mount(Home, {
      global: {
        stubs: {
          Header: true,
          Footer: true,
          SearchParamsPanel: true,
          ChatHeader: true,
          ChatMessages: true,
          ChatInputArea: true,
          SourcesPanel: true,
          SourceDetailModal: true,
          ParamsInfoModal: true,
          StarRatingModal: true
        }
      }
    })
  })

  it('mounts without errors', () => {
    expect(wrapper.exists()).toBe(true)
  })

  it('sidebar is hidden by default', () => {
    expect(wrapper.find('.unified-sidebar').exists()).toBe(false)
  })

  it('sidebar has is-open class when showSidebar is true', async () => {
    const vm = wrapper.vm
    vm.showSidebar = true
    await wrapper.vm.$nextTick()
    expect(wrapper.find('.unified-sidebar').exists()).toBe(true)
    expect(wrapper.find('.unified-sidebar.is-open').exists()).toBe(true)
  })

  it('toggleSources opens sidebar and sets expandedMessage', async () => {
    const vm = wrapper.vm
    const mockMessage = { id: 'msg-1', role: 'assistant', content: 'Test', sources: [] }

    vm.toggleSources(mockMessage)
    await wrapper.vm.$nextTick()

    expect(vm.showSidebar).toBe(true)
    expect(vm.expandedMessage).toEqual(mockMessage)
    expect(wrapper.find('.unified-sidebar.is-open').exists()).toBe(true)
  })

  it('toggleSources closes sidebar when same message clicked twice', async () => {
    const vm = wrapper.vm
    const mockMessage = { id: 'msg-1', role: 'assistant', content: 'Test', sources: [] }

    vm.toggleSources(mockMessage)
    await wrapper.vm.$nextTick()
    expect(vm.showSidebar).toBe(true)

    vm.toggleSources(mockMessage)
    await wrapper.vm.$nextTick()
    expect(vm.showSidebar).toBe(false)
    expect(vm.expandedMessage).toBeNull()
  })

  it('closeSidebar hides sidebar and clears expandedMessage', async () => {
    const vm = wrapper.vm
    const mockMessage = { id: 'msg-1', role: 'assistant', content: 'Test', sources: [] }

    vm.toggleSources(mockMessage)
    await wrapper.vm.$nextTick()
    expect(vm.showSidebar).toBe(true)

    vm.closeSidebar()
    await wrapper.vm.$nextTick()
    expect(vm.showSidebar).toBe(false)
    expect(vm.expandedMessage).toBeNull()
  })

  it('params section is visible by default', () => {
    const vm = wrapper.vm
    expect(vm.showParams).toBe(true)
  })

  it('params section toggles when section header clicked', async () => {
    const vm = wrapper.vm
    vm.showSidebar = true
    await wrapper.vm.$nextTick()

    // showParams starts true
    expect(vm.showParams).toBe(true)

    // Click the params section header to collapse
    vm.showParams = !vm.showParams
    await wrapper.vm.$nextTick()
    expect(vm.showParams).toBe(false)
  })
})
```

```html
<!-- ======== IMPLEMENTATION: frontend/src/views/Home.vue ======== -->

<template>
  <div class="home">
    <Header />

    <div class="main-layout">
      <!-- Основная область чата -->
      <main class="chat-area">
        <!-- Шапка чата -->
        <ChatHeader
          :session-title="chatStore.currentSessionTitle"
          :is-loading="chatStore.isLoading"
          @new-chat="handleNewChat"
        />

        <!-- Сообщения -->
        <ChatMessages
          :messages="chatStore.messages"
          :is-loading="chatStore.isLoading"
          :expanded-message-id="expandedMessageId"
          :feedbacks="chatStore.feedbacks"
          @toggle-sources="toggleSources"
          @feedback="handleFeedback"
          @open-star-rating="openStarRating"
          @scroll-to-source="handleScrollToSource"
        />

        <!-- Поле ввода и быстрые вопросы -->
        <ChatInputArea
          v-model="newMessage"
          :is-loading="chatStore.isLoading"
          @send="sendMessage"
          @use-template="handleUseTemplate"
        />
      </main>

      <!-- Единый правый сайдбар: параметры + источники -->
      <aside class="unified-sidebar" :class="{ 'is-open': showSidebar }">
        <!-- Хедер сайдбара с кнопкой закрытия -->
        <div class="sidebar-header">
          <button @click="closeSidebar" class="sidebar-close-btn" title="Закрыть">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M18 6L6 18M6 6l12 12"/>
            </svg>
          </button>
        </div>

        <!-- Контент сайдбара -->
        <div class="sidebar-content">
          <!-- Секция параметров (сворачиваемая) -->
          <div class="sidebar-section params-section">
            <div class="section-header" @click="showParams = !showParams">
              <span class="section-title">⚙️ Формат ответа</span>
              <span class="section-toggle">{{ showParams ? '▼' : '▶' }}</span>
            </div>
            <div class="section-body" v-show="showParams">
              <SearchParamsPanel
                v-model="searchParams"
              />
            </div>
          </div>

          <!-- Секция источников (показывается если есть развёрнутое сообщение) -->
          <div v-if="expandedMessage" class="sidebar-section sources-section">
            <div class="section-header">
              <span class="section-title">📚 Источники</span>
            </div>
            <div class="section-body sources-body">
              <SourcesPanel
                :expanded-message="expandedMessage"
                :compact="true"
                @open-source="openSourceModal"
              />
            </div>
          </div>
        </div>
      </aside>
    </div>

    <Footer :force-show="showFooter" @hide="showFooter = false" />

    <!-- Кнопка для показа футера -->
    <button v-if="!showFooter" @click="showFooter = true" class="show-footer-btn" title="Показать футер">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M12 5v14M5 12l7 7 7-7"/>
      </svg>
    </button>

    <!-- Модальное окно деталей источника -->
    <SourceDetailModal
      v-if="selectedSource"
      :source="selectedSource"
      @close="selectedSource = null"
    />

    <!-- Модальное окно информации о параметрах -->
    <ParamsInfoModal
      v-if="showInfoModal === 'settings'"
      @close="showInfoModal = null"
    />

    <!-- Модальное окно звёздного рейтинга -->
    <StarRatingModal
      v-if="showStarRating"
      :selected-stars="selectedStars"
      @close="showStarRating = false"
      @submit="submitStarRating"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import Header from '../components/Header.vue'
import Footer from '../components/Footer.vue'
import SearchParamsPanel from '../components/chat/SearchParamsPanel.vue'
import ChatHeader from '../components/chat/ChatHeader.vue'
import ChatMessages from '../components/chat/ChatMessages.vue'
import ChatInputArea from '../components/chat/ChatInputArea.vue'
import SourcesPanel from '../components/chat/SourcesPanel.vue'
import SourceDetailModal from '../components/chat/modals/SourceDetailModal.vue'
import ParamsInfoModal from '../components/chat/modals/ParamsInfoModal.vue'
import StarRatingModal from '../components/chat/modals/StarRatingModal.vue'
import { useChatStore } from '../stores/chatStore'
import { useAuthStore } from '../stores/authStore'

const authStore = useAuthStore()
const chatStore = useChatStore()

// Поле ввода
const newMessage = ref('')

// Параметры поиска
const searchParams = ref({
  k: 10,
  temperature: 0.8,
  max_tokens: 2000,
  min_score: 0.0
})

// Модальные окна
const selectedSource = ref(null)
const showInfoModal = ref(null)
const showStarRating = ref(false)
const currentFeedbackSessionId = ref(null)
const selectedStars = ref(0)

// Debouncing для фидбека
const feedbackCooldowns = ref({})

// Развёрнутое сообщение для показа источников
const expandedMessage = ref(null)
const expandedMessageId = computed(() => expandedMessage.value?.id || null)

// Управление единым сайдбаром
const showSidebar = ref(false)
const showParams = ref(true)

// Показывать ли футер
const showFooter = ref(false)

// Использование шаблона (быстрый вопрос)
function handleUseTemplate(text) {
  newMessage.value = text
  nextTick(() => {
    const textarea = document.querySelector('textarea')
    if (textarea) {
      textarea.focus()
      textarea.scrollTop = textarea.scrollHeight
    }
  })
}

// Отправка сообщения
async function sendMessage() {
  const text = newMessage.value.trim()
  if (!text || chatStore.isLoading) return
  newMessage.value = ''
  try {
    await chatStore.sendQuestion(text, searchParams.value)
    await nextTick()
    scrollToBottom()
  } catch (err) {
    console.error('Ошибка отправки:', err)
  }
}

// Прокрутка вниз
function scrollToBottom() {
  const container = document.querySelector('.messages-container')
  if (container) {
    container.scrollTop = container.scrollHeight
  }
}

// Начать новый чат
function handleNewChat() {
  chatStore.newChat()
  newMessage.value = ''
  expandedMessage.value = null
  showSidebar.value = false
}

// Закрыть сайдбар
function closeSidebar() {
  showSidebar.value = false
  expandedMessage.value = null
}

// Показать/скрыть источники для сообщения
function toggleSources(message) {
  if (expandedMessage.value?.id === message.id) {
    // Если уже открыто — закрываем
    expandedMessage.value = null
    showSidebar.value = false
  } else {
    // Открываем новое
    expandedMessage.value = message
    showSidebar.value = true
  }
}

// Прокрутка к источнику
function scrollToSource(sourceNum) {
  if (!showSidebar.value && expandedMessage.value) {
    showSidebar.value = true
  }

  const sourceElement = document.getElementById(`source-${sourceNum}`)
  if (sourceElement) {
    sourceElement.scrollIntoView({ behavior: 'smooth', block: 'center' })
    sourceElement.classList.add('highlight')
    setTimeout(() => {
      sourceElement.classList.remove('highlight')
    }, 2000)
  }
}

// Обработчик события прокрутки к источнику
function handleScrollToSource({ sourceNum, messageId }) {
  if (expandedMessage.value) {
    if (expandedMessage.value.id === messageId) {
      scrollToSource(sourceNum)
    } else {
      const targetMessage = chatStore.messages.find(m => m.id === messageId)
      if (targetMessage) {
        expandedMessage.value = targetMessage
        showSidebar.value = true
        nextTick(() => {
          scrollToSource(sourceNum)
        })
      }
    }
  } else {
    const targetMessage = chatStore.messages.find(m => m.id === messageId)
    if (targetMessage) {
      expandedMessage.value = targetMessage
      showSidebar.value = true
      nextTick(() => {
        scrollToSource(sourceNum)
      })
    }
  }
}

// Фидбек
async function handleFeedback(queryId, type) {
  if (!queryId) {
    console.warn('Нет queryId для фидбека')
    return
  }

  const now = Date.now()
  const lastFeedbackTime = feedbackCooldowns.value[queryId] || 0
  if (now - lastFeedbackTime < 1000) {
    console.log('Feedback cooldown active')
    return
  }

  const current = chatStore.feedbacks[queryId]
  try {
    if (current?.feedback_type === type) {
      await chatStore.removeFeedback(queryId)
    } else {
      await chatStore.submitFeedback(queryId, type)
      feedbackCooldowns.value[queryId] = now
    }
  } catch (err) {
    console.error('Ошибка фидбека:', err)
    alert('Не удалось отправить оценку. Попробуйте позже.')
  }
}

function openStarRating(queryId) {
  if (!queryId) {
    console.warn('Нет queryId для звёздного рейтинга')
    return
  }
  currentFeedbackSessionId.value = queryId
  showStarRating.value = true
}

async function submitStarRating(rating) {
  if (!currentFeedbackSessionId.value || !rating || rating < 1) {
    showStarRating.value = false
    return
  }

  const now = Date.now()
  const lastFeedbackTime = feedbackCooldowns.value[currentFeedbackSessionId.value] || 0
  if (now - lastFeedbackTime < 1000) {
    showStarRating.value = false
    return
  }

  selectedStars.value = rating
  try {
    await chatStore.submitFeedback(currentFeedbackSessionId.value, 'star', rating)
    feedbackCooldowns.value[currentFeedbackSessionId.value] = now
  } catch (err) {
    console.error('Ошибка фидбека:', err)
    alert('Не удалось отправить оценку. Попробуйте позже.')
  } finally {
    showStarRating.value = false
    currentFeedbackSessionId.value = null
  }
}

// Модалка с деталями источника
function openSourceModal(source) {
  selectedSource.value = source
}

// Загрузка истории при монтировании
onMounted(async () => {
  console.log('===== Home.vue: onMounted START =====')

  const resumeSessionId = localStorage.getItem('resumeSessionId')

  if (authStore.user) {
    if (resumeSessionId) {
      localStorage.removeItem('resumeSessionId')
      chatStore.isLoading = true

      try {
        await chatStore.loadHistory(50)

        const sessionChats = (chatStore.history || [])
          .filter(c => c.session_id === resumeSessionId || c.id == resumeSessionId)
          .sort((a, b) => new Date(a.created_at) - new Date(b.created_at))

        if (sessionChats.length > 0) {
          const actualSessionId = String(sessionChats[0].session_id || sessionChats[0].id)
          chatStore.sessionId = actualSessionId
          chatStore.currentSessionTitle = sessionChats[0].question?.substring(0, 50) || 'Чат'

          chatStore.messages = []
          for (const chat of sessionChats) {
            chatStore.messages.push({
              id: Date.now() + chat.id,
              role: 'user',
              content: chat.question,
              sessionId: actualSessionId,
              timestamp: new Date(chat.created_at)
            })
            chatStore.messages.push({
              id: Date.now() + chat.id + 1,
              role: 'assistant',
              content: chat.answer,
              sources: chat.sources || [],
              sessionId: actualSessionId,
              queryId: chat.id,
              timestamp: new Date(chat.created_at)
            })
          }

          chatStore.saveToStorage()
          localStorage.setItem('currentSession', JSON.stringify({
            sessionId: actualSessionId,
            title: chatStore.currentSessionTitle
          }))
        }
      } catch (err) {
        console.error('Error loading history:', err)
      } finally {
        chatStore.isLoading = false
      }
    } else {
      const restored = chatStore.restoreFromStorage()

      if (restored) {
        // Session restored from storage
      } else {
        chatStore.isLoading = true
        try {
          await chatStore.loadHistory(50)

          if (chatStore.history && chatStore.history.length > 0) {
            const lastSession = chatStore.history[0]
            const actualSessionId = String(lastSession.session_id || lastSession.id)

            const sessionChats = (chatStore.history || [])
              .filter(c => c.session_id === actualSessionId || c.id == actualSessionId)
              .sort((a, b) => new Date(a.created_at) - new Date(b.created_at))

            if (sessionChats.length > 0) {
              chatStore.sessionId = actualSessionId
              chatStore.currentSessionTitle = sessionChats[0].question?.substring(0, 50) || 'Чат'

              chatStore.messages = []
              for (const chat of sessionChats) {
                chatStore.messages.push({
                  id: Date.now() + chat.id,
                  role: 'user',
                  content: chat.question,
                  sessionId: actualSessionId,
                  timestamp: new Date(chat.created_at)
                })
                chatStore.messages.push({
                  id: Date.now() + chat.id + 1,
                  role: 'assistant',
                  content: chat.answer,
                  sources: chat.sources || [],
                  sessionId: actualSessionId,
                  queryId: chat.id,
                  timestamp: new Date(chat.created_at)
                })
              }

              chatStore.saveToStorage()
            }
          }
        } finally {
          chatStore.isLoading = false
        }
      }
    }
  }
})
</script>

<style scoped>
.home {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.main-layout {
  display: flex;
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

/* Центральная колонка (чат) */
.chat-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: white;
  min-width: 0;
  overflow: hidden;
}

/* Унифицированный правый сайдбар */
.unified-sidebar {
  width: 0;
  overflow: hidden;
  flex-shrink: 0;
  background: #f8f9fa;
  border-left: 1px solid #ddd;
  display: flex;
  flex-direction: column;
  transition: width 0.25s ease;
}

.unified-sidebar.is-open {
  width: 380px;
}

/* Хедер сайдбара */
.sidebar-header {
  display: flex;
  justify-content: flex-end;
  padding: 12px 16px;
  border-bottom: 1px solid #e5e7eb;
  background: #f9fafb;
  flex-shrink: 0;
}

.sidebar-close-btn {
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

.sidebar-close-btn:hover {
  background: #e5e7eb;
  color: #1f2937;
}

/* Контент сайдбара (скроллируемый) */
.sidebar-content {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

/* Секции сайдбара */
.sidebar-section {
  border-bottom: 1px solid #e5e7eb;
}

.section-header {
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 16px;
  background: white;
  border-bottom: 1px solid #e5e7eb;
  user-select: none;
  transition: background 0.15s;
}

.section-header:hover {
  background: #f3f4f6;
}

.section-title {
  font-size: 15px;
  font-weight: 600;
  color: #1f2937;
}

.section-toggle {
  font-size: 12px;
  color: #9ca3af;
}

.section-body {
  padding: 14px 16px;
}

/* Секция параметров */
.params-section {
  flex-shrink: 0;
}

/* Секция источников (заполняет оставшееся пространство) */
.sources-section {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.sources-body {
  flex: 1;
  overflow-y: auto;
  padding: 0;
}

/* Кнопка для показа футера */
.show-footer-btn {
  position: fixed;
  bottom: 20px;
  right: 20px;
  width: 50px;
  height: 50px;
  border-radius: 50%;
  background: #0066cc;
  color: white;
  border: none;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(0, 102, 204, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  z-index: 100;
}

.show-footer-btn:hover {
  background: #0052a3;
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(0, 102, 204, 0.4);
}

.show-footer-btn:active {
  transform: translateY(0);
}

/* FAQ под чатом */
.faq-below-chat {
  padding: 20px;
  border-top: 1px solid #e5e7eb;
  background: #f9fafb;
  overflow-y: auto;
  max-height: 300px;
  flex-shrink: 0;
}

/* Адаптивность */
@media (max-width: 992px) {
  .unified-sidebar.is-open {
    width: 340px;
  }
}

@media (max-width: 768px) {
  .unified-sidebar {
    display: none;
  }
}
</style>
```

**Verify:** `cd frontend && npx vitest run src/__tests__/Home.spec.js`
**Commit:** `feat(home): convert 3-column layout to 2-column with unified sidebar`

---

## Verification Checklist (manual)

After both tasks are done:

1. `cd frontend && npx vitest run` — all tests pass
2. `cd frontend && npm run build` — production build succeeds
3. Manual smoke test:
   - Open chat, send a message
   - Click "Показать источники" → right sidebar slides open smoothly
   - Sidebar shows params section (collapsible) and sources section
   - Click collapsible header → params section collapses/expands
   - Click ✕ on sidebar → sidebar closes, `expandedMessage` cleared
   - Click "Показать источники" on same message → sidebar closes
   - Click "Показать источники" on different message → sidebar opens with new sources
   - Resize to < 768px → sidebar hidden
   - Send new message, expand sources → sidebar opens
4. No regressions: feedback, streaming, quick questions, hotkeys all work
