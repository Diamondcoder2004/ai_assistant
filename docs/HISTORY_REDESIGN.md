# План: История чатов с группировкой по сессиям

## 📋 Задача

Переделать страницу истории чтобы:
1. **1 сессия = 1 карточка** (вместо 1 вопрос = 1 карточка)
2. **Группировка по дням**: Сегодня, Вчера, Раньше
3. **Поиск** по вопросам и ответам внутри сессий
4. **Фильтр по дате/диапазону**

---

## 🔧 Бэкенд (готово)

Endpoint: `GET /history/sessions`

**Параметры:**
- `search` (string, optional): Поиск по тексту
- `start_date` (string, optional): YYYY-MM-DD
- `end_date` (string, optional): YYYY-MM-DD

**Ответ:**
```json
{
  "today": [
    {
      "session_id": "abc123",
      "messages_count": 5,
      "first_question": "Как подать заявку?",
      "updated_at": "2026-03-24T10:30:00Z",
      "preview": [
        {"question": "...", "answer": "..."}
      ]
    }
  ],
  "yesterday": [...],
  "earlier": [...]
}
```

---

## 🎨 Фронтенд (план)

### 1. Структура компонента

```vue
<template>
  <div class="history-page">
    <!-- Поиск и фильтры -->
    <div class="filters-bar">
      <input v-model="searchQuery" placeholder="Поиск по чатам..." />
      <input type="date" v-model="startDate" />
      <input type="date" v-model="endDate" />
      <button @click="applyFilters">Применить</button>
    </div>
    
    <!-- Группы сессий -->
    <div v-if="sessions.today.length" class="sessions-group">
      <h2>Сегодня</h2>
      <div v-for="session in sessions.today" :key="session.session_id" 
           class="session-card"
           @click="openSession(session)">
        <div class="session-header">
          <span class="session-count">{{ session.messages_count }} сообщений</span>
          <span class="session-time">{{ formatTime(session.updated_at) }}</span>
        </div>
        <div class="session-preview">
          {{ session.first_question }}
        </div>
      </div>
    </div>
    
    <div v-if="sessions.yesterday.length" class="sessions-group">
      <h2>Вчера</h2>
      <!-- ... -->
    </div>
    
    <div v-if="sessions.earlier.length" class="sessions-group">
      <h2>Ранее</h2>
      <!-- ... -->
    </div>
  </div>
</template>
```

### 2. API сервис

```javascript
// frontend/src/services/supabase.js
export const chatService = {
  // ...существующие методы...
  
  async getHistorySessions(search = null, startDate = null, endDate = null) {
    const session = await authService.getSession();
    if (!session) throw new Error('Not authenticated');
    
    const params = new URLSearchParams();
    if (search) params.append('search', search);
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    
    const response = await fetch(`${API_BASE_URL}/history/sessions?${params}`, {
      headers: {
        'Authorization': `Bearer ${session.access_token}`
      }
    });
    
    if (!response.ok) {
      const error = await response.text();
      throw new Error(`API error: ${error}`);
    }
    
    return response.json();
  }
};
```

### 3. Стили

```css
.filters-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
  padding: 16px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.sessions-group {
  margin-bottom: 32px;
}

.sessions-group h2 {
  color: #003366;
  margin-bottom: 16px;
  font-size: 20px;
}

.session-card {
  display: block;
  padding: 16px;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  margin-bottom: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.session-card:hover {
  background: #eff6ff;
  border-color: #3b82f6;
  transform: translateX(4px);
  box-shadow: 0 4px 12px rgba(0, 102, 204, 0.1);
}

.session-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.session-count {
  font-size: 13px;
  color: #6b7280;
  background: #f3f4f6;
  padding: 4px 8px;
  border-radius: 6px;
}

.session-time {
  font-size: 13px;
  color: #9ca3af;
}

.session-preview {
  color: #4b5563;
  font-size: 15px;
  line-height: 1.5;
}
```

---

## 📝 Примечания

1. **Открытие сессии:** При клике на сессию — переход на `/` с `sessionId` в localStorage
2. **Пагинация:** Если сессий > 50, добавить "Показать ещё"
3. **Пустое состояние:** Если поиск не дал результатов — показать "Ничего не найдено"
