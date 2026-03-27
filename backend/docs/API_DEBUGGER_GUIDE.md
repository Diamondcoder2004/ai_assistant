# 🔌 API Debugger - Тестирование через реальный API

**Назначение:** Тестирование работы Agentic RAG через HTTP API с записью всех запросов и ответов в JSON.

---

## 🚀 Быстрый старт

### 1. Запуск с автоматической аутентификацией

```bash
cd backend

# Запуск с тестовым аккаунтом
python agent_debugger_api.py "как подать заявку на ТП"
```

### 2. Запуск с токеном из переменных окружения

```bash
# Установить токен
export SUPABASE_ACCESS_TOKEN="your-access-token"

# Запустить
python agent_debugger_api.py "ваш вопрос"
```

### 3. Запуск с ручным указанием токена

Отредактируйте `agent_debugger_api.py`:

```python
API_TOKEN = "your-access-token-here"
```

---

## 📋 Что тестируется

Автоматически выполняются 3 шага:

### Шаг 1: Health Check
```
GET /health
```
Проверка доступности API.

### Шаг 2: BM25 Status
```
GET /bm25/status
```
Проверка статуса кэша BM25 (загружен/загружается).

### Шаг 3: Query Stream
```
POST /query/stream
```
Основной запрос с потоковой передачей ответа.

---

## 📁 Выходные данные

### Консольный вывод

```
======================================================================
🎯 API Debugger
======================================================================
Запрос: как определить необходимую мощность
API URL: http://localhost:8880
Время: 2026-03-28 00:27:05
======================================================================

======================================================================
🚀 НАЧАЛО ТЕСТИРОВАНИЯ API
======================================================================
Session ID: 20260328_002705
Query: как определить необходимую мощность
API URL: http://localhost:8880

======================================================================
ШАГ 1: Health Check
======================================================================

============================================================
🏥 Health Check: /health
============================================================
HTTP 200 | 189 ms
Ответ: {'status': 'ok', 'timestamp': '2026-03-27T19:27:05.785290Z'}

======================================================================
ШАГ 2: BM25 Status
======================================================================

============================================================
📊 BM25 Status: /bm25/status
============================================================
HTTP 200 | 36 ms
Ответ: {'loaded': False, 'loading': True}

======================================================================
ШАГ 3: Query Stream
======================================================================

============================================================
📤 ЗАПРОС: /query/stream
============================================================
URL: http://localhost:8880/query/stream
Данные:
   query: как определить необходимую мощность
   k: 10
   temperature: 0.8
   max_tokens: 2000

============================================================
📥 ОТВЕТ: HTTP 200
============================================================
⏱️ Время: 5234 ms
Данные:
   events_count: 150
   sources_count: 10
   answer_length: 1247
   answer_preview: Для определения необходимой мощности...

Шаг 3: API - POST /query/stream
  ⏱️ 5234 ms | HTTP 200

======================================================================
💾 Лог сохранён: debug_logs/api_debug_20260328_002705.json
======================================================================

📊 Сводка:
  Всего шагов: 3
  Общее время: 5459 ms
  Источников: 10
  Длина ответа: 1247 символов
  Ошибок: 0

======================================================================
✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО
======================================================================
```

### JSON файл

**Файл:** `debug_logs/api_debug_20260328_002705.json`

```json
{
  "session_id": "20260328_002705",
  "query": "как определить необходимую мощность",
  "api_url": "http://localhost:8880",
  "total_duration_ms": 5459,
  "steps_count": 3,
  "steps": [
    {
      "step_num": 1,
      "component": "API",
      "action": "GET /health",
      "timestamp": "2026-03-28T00:27:05.123456",
      "duration_ms": 189,
      "request_data": {},
      "response_data": {
        "status": "ok",
        "timestamp": "2026-03-27T19:27:05.785290Z"
      },
      "http_status": 200
    },
    {
      "step_num": 2,
      "component": "API",
      "action": "GET /bm25/status",
      "duration_ms": 36,
      "request_data": {},
      "response_data": {
        "loaded": false,
        "loading": true
      },
      "http_status": 200
    },
    {
      "step_num": 3,
      "component": "API",
      "action": "POST /query/stream",
      "duration_ms": 5234,
      "request_data": {
        "query": "как определить необходимую мощность",
        "k": 10,
        "temperature": 0.8,
        "max_tokens": 2000
      },
      "response_data": {
        "events_count": 150,
        "sources_count": 10,
        "answer_length": 1247,
        "answer_preview": "Для определения..."
      },
      "http_status": 200
    }
  ],
  "final_answer": "Для определения необходимой мощности...",
  "final_sources_count": 10,
  "errors": []
}
```

---

## 🔧 Настройка аутентификации

### Вариант 1: Переменные окружения (рекомендуется)

```bash
# Windows (PowerShell)
$env:SUPABASE_ACCESS_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
python agent_debugger_api.py "вопрос"

# Linux/Mac
export SUPABASE_ACCESS_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
python agent_debugger_api.py "вопрос"
```

### Вариант 2: Тестовый аккаунт

Отредактируйте `agent_debugger_api.py`:

```python
# Строки 103-104
email = os.getenv("SUPABASE_TEST_EMAIL", "your-email@example.com")
password = os.getenv("SUPABASE_TEST_PASSWORD", "your-password")
```

### Вариант 3: Прямое указание токена

```python
# В main() добавьте:
debugger = APIDebugger(api_token="your-access-token")
```

---

## 🐛 Отладка ошибок

### Ошибка 401 Unauthorized

```
HTTP 401 | 66 ms
```

**Причина:** Неверный или отсутствующий токен.

**Решение:**
1. Проверьте токен через `/health` - должен возвращать 200
2. Убедитесь, что токен не истёк
3. Используйте переменные окружения

### Ошибка подключения

```
ConnectionError: HTTPConnectionPool(host='localhost', port=8880)
```

**Причина:** Backend не запущен.

**Решение:**
```bash
docker-compose up -d backend
```

### BM25 не загружен

```json
{"loaded": false, "loading": true}
```

**Это нормально** - кэш загружается в фоне при старте.

**Подождите 20-30 секунд** и повторите запрос.

---

## 📊 Анализ результатов

### Просмотр JSON в браузере

```bash
# Windows
start debug_logs\api_debug_*.json

# Linux/Mac
open debug_logs/api_debug_*.json
```

### Использование jq

```bash
# Показать все шаги
jq '.steps[]' debug_logs/api_debug_*.json

# Показать только длительность
jq '.steps[] | {action, duration_ms, http_status}' debug_logs/api_debug_*.json

# Найти ошибки
jq '.errors' debug_logs/api_debug_*.json

# Статистика по сессиям
jq '{query, total_ms: .total_duration_ms, sources: .final_sources_count}' debug_logs/*.json
```

### Python скрипт для анализа

```python
import json
from pathlib import Path

# Загрузка последнего лога
logs = sorted(Path("debug_logs").glob("api_debug_*.json"))
latest = logs[-1]

with open(latest) as f:
    data = json.load(f)

print(f"Запрос: {data['query']}")
print(f"Время: {data['total_duration_ms']:.0f} ms")
print(f"Источников: {data['final_sources_count']}")

for step in data['steps']:
    print(f"\n{step['action']}: {step['duration_ms']:.0f} ms (HTTP {step['http_status']})")
```

---

## 🎯 Примеры использования

### 1. Тестирование производительности

```bash
# Запустить 5 раз
for i in {1..5}; do
    python agent_debugger_api.py "как подать заявку на ТП"
done

# Сравнить времена
jq '.steps[] | select(.action == "POST /query/stream") | .duration_ms' debug_logs/*.json
```

### 2. Проверка разных типов запросов

```bash
# Короткий запрос
python agent_debugger_api.py "график работы"

# Средний запрос
python agent_debugger_api.py "какие документы нужны для ТП"

# Длинный запрос
python agent_debugger_api.py "как определить необходимую мощность для подключения к электросети частного дома"
```

### 3. Тестирование с разными параметрами

Отредактируйте `test_query_stream()`:

```python
payload = {
    "query": query,
    "k": 30,  # Больше источников
    "temperature": 0.5,  # Меньше креативности
    "max_tokens": 3000  # Больше токенов
}
```

---

## 📁 Расположение файлов

```
backend/
├── agent_debugger_api.py      # Скрипт отладки
└── debug_logs/
    ├── api_debug_20260328_002705.json
    ├── api_debug_20260328_003112.json
    └── api_debug_20260328_004523.json
```

---

## 🔗 Связанные документы

- [PLAYGROUND_GUIDE.md](PLAYGROUND_GUIDE.md) - Тестирование компонентов напрямую
- [AGENT_DEBUGGER.md](AGENT_DEBUGGER.md) - Пошаговое логирование агента (без API)

---

**Документ обновлён:** 28 марта 2026 г.  
**Файл:** `backend/agent_debugger_api.py`
