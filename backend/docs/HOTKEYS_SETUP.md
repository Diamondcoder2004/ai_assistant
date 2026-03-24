# Установка и настройка горячих клавиш

## 📦 Установка

### 1. Файлы которые были созданы

```
D:\web_chat_bot\web_chat_bot\src\
├── stores/
│   └── hotkeysStore.js              # Хранилище настроек
├── components/
│   └── settings/
│       ├── HotkeysEditor.vue        # Редактор горячих клавиш
│       └── SettingsModal.vue        # Модальное окно настроек
│   └── Header.vue                   # Обновлён (кнопка настроек)
│   └── chat/
│       └── ChatMessages.vue         # Обновлён (обработка клавиш)
```

### 2. База данных (Supabase)

Выполните SQL скрипт в Supabase SQL Editor:

```bash
# Путь к скрипту
d:\PythonProjects\agentic_rag\docs\supabase_user_settings.sql
```

**Что создаётся:**
- Таблица `user_settings` с полями:
  - `user_id` (TEXT, UNIQUE)
  - `hotkeys` (JSONB)
  - `theme` (TEXT)
  - `language` (TEXT)
  - `created_at`, `updated_at`
- RLS политики (безопасность)
- Триггер для авто-обновления `updated_at`

### 3. Настройка .env

Добавьте в `.env` фронтенда:

```bash
VITE_SUPABASE_URL=http://localhost:8000
VITE_SUPABASE_ANON_KEY=your-anon-key
```

---

## 🚀 Использование

### Для пользователей:

1. **Откройте настройки**
   - Нажмите кнопку **⚙️** в шапке сайта (справа, рядом с email)

2. **Измените горячие клавиши**
   - Перейдите на вкладку **⌨️ Горячие клавиши**
   - Кликните на поле с комбинацией
   - Нажмите новую комбинацию
   - Сохранение автоматическое!

3. **Сбросьте настройки**
   - Нажмите кнопку **🔄 Сбросить** для возврата к настройкам по умолчанию

### Для разработчиков:

#### Импорт хранилища:

```javascript
import { useHotkeysStore } from './stores/hotkeysStore'

const hotkeysStore = useHotkeysStore()

// Доступ к горячим клавишам
console.log(hotkeysStore.hotkeys.sendMessage)  // 'Enter'

// Обновление
hotkeysStore.updateHotkey('newChat', 'Ctrl+K')

// Сброс
hotkeysStore.resetToDefaults()

// Сохранение (автоматически выбирает Supabase или localStorage)
await hotkeysStore.saveToStorage()
```

#### Обработка нажатий:

```javascript
// В компоненте
onMounted(() => {
  window.addEventListener('keydown', (event) => {
    const combination = hotkeysStore.captureKeyCombination(event)
    
    if (combination === hotkeysStore.hotkeys.copyLastAnswer) {
      event.preventDefault()
      copyToClipboard(lastMessage)
    }
  })
})
```

---

## 🔧 Настройки по умолчанию

```javascript
{
  sendMessage: 'Enter',           // Отправить сообщение
  newLine: 'Shift+Enter',         // Новая строка
  newChat: 'Ctrl+N',              // Новый чат
  showHistory: 'Ctrl+H',          // Показать историю
  copyLastAnswer: 'Ctrl+Shift+C', // Копировать последний ответ
  focusInput: 'Ctrl+L',           // Фокус на поле ввода
  toggleSources: 'Ctrl+S'         // Показать/скрыть источники
}
```

---

## 📊 Как работает сохранение

### Авторизованные пользователи:

```
Изменение настройки
    ↓
saveToStorage()
    ↓
saveToSupabase()  →  Supabase (user_settings)
    ↓
saveToLocalStorage()  →  localStorage (кэш)
```

### Неавторизованные:

```
Изменение настройки
    ↓
saveToStorage()
    ↓
saveToLocalStorage()  →  localStorage
```

---

## 🐛 Отладка

### Проверка localStorage:

```javascript
// В консоли браузера
console.log(localStorage.getItem('hotkeys'))
// {"sendMessage":"Enter","newChat":"Ctrl+K",...}
```

### Проверка Supabase:

```sql
-- В Supabase SQL Editor
SELECT user_id, hotkeys, updated_at 
FROM user_settings 
WHERE user_id = 'your-user-id';
```

### Логирование:

Включите логирование в `hotkeysStore.js`:

```javascript
function saveToStorage() {
  console.log('Сохранение горячих клавиш:', hotkeys.value)
  // ...
}
```

---

## ⚠️ Возможные проблемы

### 1. Кнопка настроек не отображается

**Решение:** Убедитесь что вошли в систему (кнопка видна только авторизованным)

### 2. Настройки не сохраняются

**Проверьте:**
- Авторизованы ли вы
- Правильно ли настроен Supabase
- Выполнен ли SQL скрипт

### 3. Конфликт горячих клавиш

**Решение:** Система автоматически обнаружит конфликт и покажет предупреждение

### 4. Горячие клавиши не работают

**Проверьте:**
- Не находится ли фокус в поле ввода (для некоторых комбинаций)
- Не блокирует ли браузер комбинацию (например, `Ctrl+T`)

---

## 📝 Миграция данных

Если у вас уже есть пользователи с настройками в localStorage:

```javascript
// При первом входе пользователя
async function migrateHotkeys() {
  const localHotkeys = localStorage.getItem('hotkeys')
  if (localHotkeys && authStore.user) {
    await hotkeysStore.saveToSupabase()
    console.log('Настройки мигрированы в Supabase')
  }
}
```

---

**Версия:** 1.0  
**Дата:** 2026-03-23
