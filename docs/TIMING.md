# 📊 Система таймингов и статистики

## 🎯 Что это

Система для замера времени выполнения:
- **HTTP запросов** — общее время обработки запроса
- **Агентов** — время работы Query Generator, Search Agent, Response Agent
- **Операций** — детальные замеры по этапам (генерация запросов, поиск, LLM completion, и т.д.)

## 🏗️ Архитектура

```
┌─────────────────────────────────────────────────────────┐
│                  HTTP Request                           │
│              POST /query                                │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼ (middleware)
┌─────────────────────────────────────────────────────────┐
│  ⏱️ Middleware: замер общего времени запроса           │
│  X-Process-Time: 2345.67ms                             │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│  @timing("QueryGenerator.generate")                     │
│  ⏱️ QueryGenerator.generate: 123.45ms                  │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│  with timing_context("SearchAgent.tool_search")         │
│  🚀 Начало: SearchAgent.tool_search                     │
│  ✅ Завершено: SearchAgent.tool_search за 456.78ms     │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│  @timing("ResponseAgent.generate_response")             │
│  ⏱️ ResponseAgent.generate_response: 1234.56ms         │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│  Статистика сохраняется в:                              │
│  - logs/timing_stats.json (периодически)               │
│  - памяти (для API запросов)                            │
└─────────────────────────────────────────────────────────┘
```

## 📁 Файлы

| Файл | Описание |
|------|----------|
| `backend/utils/timing.py` | Основные утилиты: декораторы, контексты, статистика |
| `backend/api/api.py` | Middleware для замера HTTP запросов |
| `backend/api/endpoints.py` | API endpoints для просмотра статистики |
| `backend/agents/*.py` | Декораторы на методах агентов |
| `logs/timing_stats.json` | Файл со статистикой (сохраняется каждые 5 минут) |

## 🔧 Как использовать

### 1. Замер времени функции (декоратор)

```python
from utils.timing import timing

@timing("MyOperation.name")
def my_function(...):
    # ... код
    pass
```

**Лог:**
```
⏱️ MyOperation.name: 123.45ms
```

### 2. Замер блока кода (контекст)

```python
from utils.timing import timing_context

with timing_context("ComplexOperation", {"details": "value"}):
    # ... код
    pass
```

**Лог:**
```
🚀 Начало: ComplexOperation
✅ Завершено: ComplexOperation за 456.78ms | {'details': 'value'}
```

### 3. Просмотр статистики через API

#### Получить текущую статистику

```bash
curl http://localhost:8880/timing/stats
```

**Ответ:**
```json
{
  "ResponseAgent.generate_response": {
    "name": "ResponseAgent.generate_response",
    "call_count": 15,
    "avg_time_ms": 1234.56,
    "min_time_ms": 890.12,
    "max_time_ms": 2345.67,
    "last_time_ms": 1456.78,
    "total_time_ms": 18518.40
  },
  "QueryGenerator.generate": {
    "name": "QueryGenerator.generate",
    "call_count": 15,
    "avg_time_ms": 234.56,
    "min_time_ms": 123.45,
    "max_time_ms": 567.89,
    "last_time_ms": 345.67,
    "total_time_ms": 3518.40
  }
}
```

#### Вывод статистики в лог

```bash
curl http://localhost:8880/timing/stats/print
```

**Лог:**
```
============================================================
📊 СТАТИСТИКА ТАЙМИНГОВ
============================================================
ResponseAgent.generate_response        | calls:    15 | avg:  1234.56ms | min:   890.12ms | max:  2345.67ms | total:   18518.40ms
QueryGenerator.generate                | calls:    15 | avg:   234.56ms | min:   123.45ms | max:   567.89ms | total:    3518.40ms
SearchAgent.search                     | calls:    15 | avg:   567.89ms | min:   234.56ms | max:  1234.56ms | total:    8518.35ms
============================================================
```

#### Сохранить статистику в файл

```bash
curl -X POST http://localhost:8880/timing/stats/save
```

**Ответ:**
```json
{
  "status": "ok",
  "filepath": "logs/timing_stats.json"
}
```

#### Сбросить статистику

```bash
curl -X POST http://localhost:8880/timing/stats/reset
```

## 📊 Формат файла статистики

`logs/timing_stats.json`:

```json
{
  "generated_at": "2026-03-24T17:30:00.000000",
  "operations": {
    "ResponseAgent.generate_response": {
      "name": "ResponseAgent.generate_response",
      "call_count": 15,
      "avg_time_ms": 1234.56,
      "min_time_ms": 890.12,
      "max_time_ms": 2345.67,
      "last_time_ms": 1456.78,
      "total_time_ms": 18518.40
    }
  },
  "recent_requests": [
    {
      "timestamp": "2026-03-24T17:29:55.123456",
      "method": "POST",
      "path": "/query",
      "total_time_ms": 2345.67,
      "agent_times": {
        "QueryGenerator.generate": 123.45,
        "SearchAgent.search": 567.89,
        "ResponseAgent.generate_response": 1456.78
      }
    }
  ]
}
```

## 🎯 Измеряемые операции

### Агенты

| Операция | Описание |
|----------|----------|
| `QueryGenerator.generate` | Генерация поисковых запросов |
| `SearchAgent.search` | Поиск (всё время) |
| `SearchAgent.query_generation` | Генерация запросов (внутри Search) |
| `SearchAgent.tool_search` | Поиск в Qdrant |
| `ResponseAgent.generate_response` | Генерация ответа (всё время) |
| `ResponseAgent.format_context` | Форматирование контекста |
| `ResponseAgent.create_prompt` | Создание промпта |
| `ResponseAgent.llm_completion` | Запрос к LLM |
| `ResponseAgent.extract_sources` | Извлечение и ранжирование источников |

### HTTP запросы

| Endpoint | Описание |
|----------|----------|
| `POST /query` | Обычный запрос |
| `POST /query/stream` | Streaming запрос |
| `GET /history` | История чатов |
| `POST /feedback` | Отправка фидбека |

## 🕐 Автоматическое сохранение

Статистика автоматически сохраняется в `logs/timing_stats.json` каждые **5 минут**.

Для настройки интервала:

```python
from utils.timing import start_periodic_save

# Запуск сохранения каждые 10 минут
start_periodic_save(interval_seconds=600, filepath="logs/timing_stats.json")
```

## 📈 Анализ производительности

### Поиск узких мест

1. Откройте статистику:
   ```bash
   curl http://localhost:8880/timing/stats | python -m json.tool
   ```

2. Найдите операции с наибольшим `total_time_ms` или `avg_time_ms`

3. Проверьте логи для детальной информации

### Пример анализа

```
📊 СТАТИСТИКА ТАЙМИНГОВ
============================================================
ResponseAgent.generate_response        | calls:   100 | avg:  1500.00ms | total: 150000.00ms  ← 75% времени
SearchAgent.search                     | calls:   100 | avg:   400.00ms | total:  40000.00ms  ← 20% времени
QueryGenerator.generate                | calls:   100 | avg:    50.00ms | total:   5000.00ms  ← 5% времени
============================================================
```

**Вывод:** ResponseAgent занимает 75% времени → оптимизировать LLM запросы

## 🛠️ Отладка

### Включить подробное логирование

В `config.py` установите:
```python
LOG_LEVEL = "DEBUG"
```

### Проверка работы декораторов

```bash
docker-compose logs backend | grep "⏱️"
```

**Пример вывода:**
```
⏱️ QueryGenerator.generate: 123.45ms
⏱️ SearchAgent.search: 567.89ms
⏱️ ResponseAgent.generate_response: 1234.56ms
```

### Проверка контекстных замеров

```bash
docker-compose logs backend | grep "🚀\|✅"
```

**Пример вывода:**
```
🚀 Начало: SearchAgent.tool_search
✅ Завершено: SearchAgent.tool_search за 345.67ms
```

## 🎯 Best Practices

1. **Не забывайте про context manager** для сложных операций
2. **Давайте понятные имена** операциям: `SearchAgent.search` вместо `search`
3. **Сохраняйте статистику** перед анализом производительности
4. **Сбрасывайте статистику** после тестов: `POST /timing/stats/reset`
5. **Смотрите на `avg_time_ms`** для типичного времени, `max_time_ms` для худшего случая

## 📚 API Reference

### `GET /timing/stats`

Получение статистики по всем операциям.

**Ответ:** `Dict[str, Dict[str, Any]]`

### `GET /timing/stats/print`

Вывод статистики в лог.

**Ответ:** `{"status": "ok", "message": "Statistics printed to log"}`

### `POST /timing/stats/save`

Сохранение статистики в файл.

**Параметры:**
- `filepath` (query, optional): Путь к файлу. По умолчанию: `logs/timing_stats.json`

**Ответ:** `{"status": "ok", "filepath": "..."}`

### `POST /timing/stats/reset`

Сброс всей статистики.

**Ответ:** `{"status": "ok", "message": "Statistics reset"}`

---

## 📝 Примеры использования

### 1. Мониторинг после деплоя

```bash
# Подождать 5 минут после деплоя
sleep 300

# Получить статистику
curl http://localhost:8880/timing/stats | python -m json.tool > timing_after_deploy.json

# Сравнить с предыдущей версией
diff timing_before.json timing_after_deploy.json
```

### 2. Поиск медленных запросов

```bash
# Получить последние 100 запросов
curl http://localhost:8880/timing/stats | \
  python -c "import sys, json; data=json.load(sys.stdin); \
  print('\n'.join(f\"{r['method']} {r['path']}: {r['total_time_ms']:.2f}ms\" \
                  for r in data.get('recent_requests', [])[-100:]))"
```

### 3. Автоматический алерт при медленных ответах

```python
import requests

stats = requests.get('http://localhost:8880/timing/stats').json()
avg_response_time = stats.get('ResponseAgent.generate_response', {}).get('avg_time_ms', 0)

if avg_response_time > 3000:  # Больше 3 секунд
    print(f"⚠️ ALERT: Average response time is {avg_response_time:.2f}ms!")
    # Отправить уведомление в Slack/Telegram
```
