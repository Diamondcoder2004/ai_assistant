# 🧪 Тестовый режим (Test Mode)

## Проблема
Ошибка `Failed to fetch` при попытке входа — Supabase не запущен.

## Решение: Тестовый режим

### Быстрый старт без Supabase

1. **Включите тестовый режим в `.env`:**
```env
VITE_TEST_MODE=true
```

2. **Перезапустите dev сервер:**
```bash
npm run dev
```

3. **Войдите с любыми данными:**
- Email: любой (например, `test@test.com`)
- Пароль: любой (например, `123456`)

✅ **Готово!** Вы вошли в систему с mock-аутентификацией.

---

## Как это работает

### Test Mode = `true`

```javascript
// supabase.js
if (TEST_MODE) {
  // Mock аутентификация
  const user = { id: 'test-user-id', email, ... }
  const session = { access_token: 'mock-jwt-token', user }
  localStorage.setItem('mock-user', JSON.stringify(user))
  return { data: { user, session }, error: null }
}
```

**Что происходит:**
- ✅ Вход/регистрация работают без сервера
- ✅ JWT токен сохраняется в localStorage
- ✅ Данные пользователя сохраняются
- ✅ Можно тестировать UI чата
- ❌ Бэкенд API всё ещё нужен для запросов

### Test Mode = `false` (production)

```env
VITE_TEST_MODE=false
```

**Требуется:**
- ✅ Запущенный Supabase (локальный или облачный)
- ✅ Правильный `VITE_SUPABASE_URL` и `VITE_SUPABASE_ANON_KEY`

---

## Сравнение режимов

| Функция | Test Mode | Production |
|---------|-----------|------------|
| Аутентификация | Mock (localStorage) | Supabase Auth |
| JWT токен | `mock-jwt-token` | Реальный JWT |
| Данные пользователя | Фиктивные | Из Supabase |
| Чат с бэкендом | ✅ Работает | ✅ Работает |
| История чатов | ✅ Работает | ✅ Работает |
| Фидбек | ✅ Работает | ✅ Работает |

---

## Настройки для разных сред

### Разработка (локально)

```env
# .env
VITE_TEST_MODE=true
VITE_SUPABASE_URL=http://localhost:54321  # не используется
VITE_API_BASE_URL=http://localhost:8000
```

### Production

```env
# .env.production
VITE_TEST_MODE=false
VITE_SUPABASE_URL=https://xxxxx.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
VITE_API_BASE_URL=https://api.yourdomain.com
```

---

## Проверка работы

### 1. Откройте консоль браузера

**Test Mode включён:**
```
Supabase URL: http://localhost:54321
Test Mode: ✅ ON (Mock Auth)
⚠️ TEST MODE: Supabase disabled, using mock authentication
```

**Test Mode выключен:**
```
Supabase URL: http://localhost:54321
Test Mode: ❌ OFF
Supabase client created successfully
```

### 2. Проверьте localStorage

**После входа в тестовом режиме:**
```javascript
localStorage.getItem('mock-user')
// {"id":"test-user-id","email":"test@test.com",...}

localStorage.getItem('mock-session')
// {"access_token":"mock-jwt-token","user":{...}}
```

---

## Ограничения тестового режима

### ❌ Не работает
- Реальная аутентификация через Supabase
- Синхронизация между устройствами
- Восстановление пароля
- Email подтверждения

### ✅ Работает
- Вход/регистрация (mock)
- Чат с бэкендом
- История запросов
- Фидбек (лайк/дизлайк/звёзды)
- Параметры поиска

---

## Переключение режимов

### Включить Test Mode
```bash
# .env
VITE_TEST_MODE=true

# Перезапуск
npm run dev
```

### Выключить Test Mode
```bash
# .env
VITE_TEST_MODE=false

# Убедитесь, что Supabase запущен
supabase start

# Перезапуск
npm run dev
```

---

## Интеграция с бэкендом

Даже в тестовом режиме бэкенд API нужен для:
- 📡 RAG запросов (`/query`, `/query/stream`)
- 📜 Истории чатов (`/history`)
- ⭐ Фидбека (`/feedback`)

**Проверка бэкенда:**
```bash
curl http://localhost:8000/health
# {"status": "ok", "service": "RAG API Башкирэнерго"}
```

---

## Сброс тестовых данных

```javascript
// В консоли браузера
localStorage.removeItem('mock-user')
localStorage.removeItem('mock-session')
location.reload()
```

---

## Безопасность

⚠️ **Важно:** Никогда не используйте `VITE_TEST_MODE=true` в production!

**Test Mode только для:**
- ✅ Локальной разработки
- ✅ Тестирования UI
- ✅ Демонстрации функционала

**Для production:**
- ❌ Отключите тестовый режим
- ✅ Используйте облачный Supabase
- ✅ Настройте HTTPS
- ✅ Используйте реальные JWT токены

---

## Поддержка

- 📖 [Quick Start](./QUICKSTART.md)
- 🚀 [Run Instructions](./RUN_INSTRUCTIONS.md)
- 🔌 [API Docs](./DOCS_API/API.md)
