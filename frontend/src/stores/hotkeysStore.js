import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

// Горячие клавиши по умолчанию (временно отключены)
const DEFAULT_HOTKEYS = {
  sendMessage: '',           // Отправить сообщение (отключено)
  newLine: '',               // Новая строка (отключено)
  newChat: '',               // Новый чат (отключено)
  showHistory: '',           // Показать историю (отключено)
  copyLastAnswer: '',        // Копировать последний ответ (отключено)
  focusInput: '',            // Фокус на поле ввода (отключено)
  toggleSources: '',         // Показать/скрыть источники (отключено)
}

// Допустимые модификаторы
const ALLOWED_MODIFIERS = ['Ctrl', 'Alt', 'Shift', 'Meta']

// Допустимые клавиши (коды)
const ALLOWED_KEYS = [
  // Буквы
  'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M',
  'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
  // Цифры
  '0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
  // Функциональные
  'F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8', 'F9', 'F10', 'F11', 'F12',
  // Специальные
  'Enter', 'Escape', 'Tab', 'Space', 'ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight',
  'Home', 'End', 'PageUp', 'PageDown', 'Delete', 'Backspace',
  // Другие
  'Plus', 'Minus', 'Equal', 'Comma', 'Period', 'Slash', 'Backslash'
]

export const useHotkeysStore = defineStore('hotkeys', () => {
  // Загружаем из localStorage или используем значения по умолчанию
  const hotkeys = ref({ ...DEFAULT_HOTKEYS })
  const isLoading = ref(false)
  
  // Загрузка из localStorage (отключено)
  function loadFromStorage() {
    // Горячие клавиши временно отключены - не загружаем из localStorage
    try {
      const saved = localStorage.getItem('hotkeys')
      if (saved) {
        // Очищаем сохранённые горячие клавиши
        localStorage.removeItem('hotkeys')
      }
    } catch (e) {
      console.error('Error clearing hotkeys from localStorage:', e)
    }
  }
  
  // Сохранение в localStorage
  function saveToLocalStorage() {
    try {
      localStorage.setItem('hotkeys', JSON.stringify(hotkeys.value))
    } catch (e) {
      console.error('Ошибка сохранения в localStorage:', e)
    }
  }
  
  // Сохранение (localStorage)
  function saveToStorage() {
    saveToLocalStorage()
  }
  
  // Сброс к настройкам по умолчанию
  function resetToDefaults() {
    hotkeys.value = { ...DEFAULT_HOTKEYS }
    saveToStorage()
  }
  
  // Обновление горячей клавиши
  function updateHotkey(action, keyCombination) {
    if (validateKeyCombination(keyCombination)) {
      hotkeys.value[action] = keyCombination
      saveToStorage()
      return true
    }
    return false
  }
  
  // Валидация комбинации клавиш
  function validateKeyCombination(combination) {
    if (!combination || typeof combination !== 'string') {
      return false
    }

    const parts = combination.split('+')
    const modifiers = []
    let key = null

    // Разбираем комбинацию
    for (const part of parts) {
      const trimmed = part.trim()
      if (ALLOWED_MODIFIERS.includes(trimmed)) {
        modifiers.push(trimmed)
      } else {
        key = trimmed
      }
    }

    // Должна быть хотя бы одна клавиша (не модификатор)
    if (!key) {
      return false
    }

    // Проверяем что клавиша допустима
    if (!ALLOWED_KEYS.includes(key)) {
      return false
    }

    // Проверяем что нет дубликатов модификаторов
    if (modifiers.length !== new Set(modifiers).size) {
      return false
    }

    return true
  }
  
  // Получение названия клавиши для отображения
  function getKeyName(key) {
    const names = {
      'Ctrl': 'Ctrl',
      'Alt': 'Alt',
      'Shift': 'Shift',
      'Meta': 'Win',
      'Enter': 'Enter',
      'Escape': 'Esc',
      'Space': 'Пробел',
      'ArrowUp': '↑',
      'ArrowDown': '↓',
      'ArrowLeft': '←',
      'ArrowRight': '→',
      'Backspace': 'Backspace',
      'Delete': 'Delete'
    }
    return names[key] || key
  }
  
  // Форматирование комбинации для отображения
  function formatCombination(combination) {
    return combination.split('+')
      .map(key => getKeyName(key.trim()))
      .join(' + ')
  }
  
  // Проверка конфликта
  function checkConflict(combination, excludeAction = null) {
    for (const [action, existingCombination] of Object.entries(hotkeys.value)) {
      if (action !== excludeAction && existingCombination === combination) {
        return action
      }
    }
    return null
  }
  
  // Захват комбинации клавиш (для UI)
  function captureKeyCombination(event) {
    const parts = []

    // Добавляем модификаторы
    if (event.ctrlKey) parts.push('Ctrl')
    if (event.altKey) parts.push('Alt')
    if (event.shiftKey) parts.push('Shift')
    if (event.metaKey) parts.push('Meta')

    // Используем event.code для надёжности
    let code = event.code
    let key = null

    // Коды клавиш
    const codeMap = {
      // Буквы KeyA-KeyZ → A-Z
      'KeyA': 'A', 'KeyB': 'B', 'KeyC': 'C', 'KeyD': 'D', 'KeyE': 'E', 'KeyF': 'F',
      'KeyG': 'G', 'KeyH': 'H', 'KeyI': 'I', 'KeyJ': 'J', 'KeyK': 'K', 'KeyL': 'L',
      'KeyM': 'M', 'KeyN': 'N', 'KeyO': 'O', 'KeyP': 'P', 'KeyQ': 'Q', 'KeyR': 'R',
      'KeyS': 'S', 'KeyT': 'T', 'KeyU': 'U', 'KeyV': 'V', 'KeyW': 'W', 'KeyX': 'X',
      'KeyY': 'Y', 'KeyZ': 'Z',
      // Цифры Digit0-Digit9 → 0-9
      'Digit0': '0', 'Digit1': '1', 'Digit2': '2', 'Digit3': '3', 'Digit4': '4',
      'Digit5': '5', 'Digit6': '6', 'Digit7': '7', 'Digit8': '8', 'Digit9': '9',
      // Функциональные F1-F12
      'F1': 'F1', 'F2': 'F2', 'F3': 'F3', 'F4': 'F4', 'F5': 'F5', 'F6': 'F6',
      'F7': 'F7', 'F8': 'F8', 'F9': 'F9', 'F10': 'F10', 'F11': 'F11', 'F12': 'F12',
      // Специальные
      'Enter': 'Enter',
      'Space': 'Space',
      'Tab': 'Tab',
      'Escape': 'Escape',
      'Backspace': 'Backspace',
      'Delete': 'Delete',
      'ArrowUp': 'ArrowUp',
      'ArrowDown': 'ArrowDown',
      'ArrowLeft': 'ArrowLeft',
      'ArrowRight': 'ArrowRight',
      'Home': 'Home',
      'End': 'End',
      'PageUp': 'PageUp',
      'PageDown': 'PageDown'
    }

    key = codeMap[code]

    if (key && !ALLOWED_MODIFIERS.includes(key)) {
      parts.push(key)
    }

    return parts.join('+')
  }
  
  // Вычисление доступных действий
  const availableActions = computed(() => [
    { key: 'sendMessage', label: 'Отправить сообщение', default: DEFAULT_HOTKEYS.sendMessage },
    { key: 'newLine', label: 'Новая строка', default: DEFAULT_HOTKEYS.newLine },
    { key: 'newChat', label: 'Новый чат', default: DEFAULT_HOTKEYS.newChat },
    { key: 'showHistory', label: 'Показать историю', default: DEFAULT_HOTKEYS.showHistory },
    { key: 'copyLastAnswer', label: 'Копировать последний ответ', default: DEFAULT_HOTKEYS.copyLastAnswer },
    { key: 'focusInput', label: 'Фокус на поле ввода', default: DEFAULT_HOTKEYS.focusInput },
    { key: 'toggleSources', label: 'Показать/скрыть источники', default: DEFAULT_HOTKEYS.toggleSources },
  ])
  
  // Загрузка при инициализации
  loadFromStorage()
  
  return {
    hotkeys,
    availableActions,
    DEFAULT_HOTKEYS,
    ALLOWED_MODIFIERS,
    ALLOWED_KEYS,
    updateHotkey,
    resetToDefaults,
    validateKeyCombination,
    formatCombination,
    checkConflict,
    captureKeyCombination,
    getKeyName,
    saveToStorage
  }
})
