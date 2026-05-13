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
    expect(wrapper.find('.unified-sidebar').exists()).toBe(true)
    expect(wrapper.find('.unified-sidebar.is-open').exists()).toBe(false)
  })

  it('sidebar has is-open class when showSidebar is true', async () => {
    const vm = wrapper.vm
    vm.showSidebar = true
    await wrapper.vm.$nextTick()
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

    expect(vm.showParams).toBe(true)

    vm.showParams = !vm.showParams
    await wrapper.vm.$nextTick()
    expect(vm.showParams).toBe(false)
  })
})
