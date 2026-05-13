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
      expect(wrapper.find('.sources-header').exists()).toBe(false)
      expect(wrapper.find('.sources-list').exists()).toBe(false)
      expect(wrapper.find('.source-card').exists()).toBe(false)
      // No visible elements rendered aside from Vue comment markers
      expect(wrapper.text()).toBe('')
    })

    it('renders nothing when expandedMessage is null', () => {
      const wrapper = mount(SourcesPanel, {
        props: { expandedMessage: null }
      })
      expect(wrapper.find('aside.sources-panel').exists()).toBe(false)
      expect(wrapper.find('.sources-header').exists()).toBe(false)
      expect(wrapper.find('.sources-list').exists()).toBe(false)
      expect(wrapper.find('.source-card').exists()).toBe(false)
      expect(wrapper.text()).toBe('')
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
})
