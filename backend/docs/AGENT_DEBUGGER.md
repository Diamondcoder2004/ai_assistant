# 🐞 Agent Debugger - Пошаговое логирование агента

**Назначение:** Детальная запись каждого шага работы Agentic RAG в JSON формат для удобного анализа ошибок.

---

## 🚀 Быстрый старт

```bash
cd backend

# Запуск с вопросом
python agent_debugger.py "как определить необходимую мощность для подключения"

# Запуск с длинным вопросом
python agent_debugger.py "какие документы нужны для технологического присоединения к электросети частного дома"
```

---

## 📁 Выходные данные

### 1. Консольный вывод

```
======================================================================
🎯 Agent Debugger
======================================================================
Запрос: как определить необходимую мощность для подключения
Время: 2026-03-27 23:15:30
======================================================================

======================================================================
🚀 НАЧАЛО ТРАССИРОВКИ ЗАПРОСА
======================================================================
Session ID: 20260327_231530
Query: как определить необходимую мощность для подключения
Time: 2026-03-27T23:15:30.123456

============================================================
🔹 QueryGenerator: Генерация поисковых запросов
============================================================
📥 Входные данные:
   query: как определить необходимую мощность для подключения
   user_hints: {}
✅ Завершено за 1740 ms
📤 Выходные данные:
   queries: ['как рассчитать необходимую мощность...', ...]
   search_params: {'k': 30, 'weights': {...}, ...}
   clarification_needed: False

============================================================
🔹 SearchTool: Поиск в Qdrant
============================================================
📥 Входные данные:
   queries: ['как рассчитать необходимую мощность...', ...]
   search_params: {'k': 30, 'weights': {...}}
✅ Завершено за 634 ms
📤 Выходные данные:
   total_results: 30
   top_5_sources: [{...}, {...}, ...]

============================================================
🔹 ResponseAgent: Генерация ответа
============================================================
📥 Входные данные:
   query: как определить необходимую мощность...
   sources_count: 30
   max_tokens: 2000
✅ Завершено за 2150 ms
📤 Выходные данные:
   answer_length: 1247
   answer_preview: Для определения необходимой мощности...
   sources_used: 5
   confidence: 0.85

======================================================================
💾 Лог сохранён: debug_logs/debug_20260327_231530.json
======================================================================

📊 Сводка:
  Всего шагов: 3
  Общее время: 4524 ms
  Источников: 30
  Длина ответа: 1247 символов
  Ошибок: 0

======================================================================
✅ ТРАССИРОВКА ЗАВЕРШЕНА
======================================================================

📝 Ответ (1247 символов):
----------------------------------------------------------------------
Для определения необходимой мощности необходимо учесть следующие факторы:

1. Суммарную мощность всех электроприемников...
...
----------------------------------------------------------------------

💾 Файл: debug_logs/debug_20260327_231530.json
======================================================================
```

---

### 2. JSON файл (структура)

**Файл:** `debug_logs/debug_20260327_231530.json`

```json
{
  "session_id": "20260327_231530",
  "query": "как определить необходимую мощность для подключения",
  "started_at": "2026-03-27T23:15:30.123456",
  "completed_at": "2026-03-27T23:15:34.647890",
  "total_duration_ms": 4524.32,
  "steps_count": 3,
  "steps": [
    {
      "step_num": 1,
      "component": "QueryGenerator",
      "action": "generate",
      "timestamp": "2026-03-27T23:15:30.125000",
      "duration_ms": 1740.89,
      "input_data": {
        "query": "как определить необходимую мощность для подключения",
        "user_hints": {}
      },
      "output_data": {
        "queries": [
          "как рассчитать необходимую мощность для подключения к электросети",
          "методика определения мощности подключения",
          "нормативные требования к мощности при присоединении"
        ],
        "search_params": {
          "k": 30,
          "weights": {
            "pref": 0.4,
            "hype": 0.3,
            "contextual": 0.3
          },
          "strategy": "concat"
        },
        "clarification_needed": false,
        "clarification_questions": [],
        "confidence": 0.85
      },
      "metadata": {}
    },
    {
      "step_num": 2,
      "component": "SearchTool",
      "action": "search",
      "timestamp": "2026-03-27T23:15:31.866000",
      "duration_ms": 633.83,
      "input_data": {
        "queries": [...],
        "search_params": {...}
      },
      "output_data": {
        "total_results": 30,
        "top_5_sources": [
          {
            "filename": "FAQ_ТП.pdf",
            "breadcrumbs": "Главная > ТП > Заявка",
            "score_hybrid": 0.923,
            "score_semantic": 0.912,
            "score_lexical": 0.845
          },
          ...
        ]
      },
      "metadata": {
        "all_results_count": 30
      }
    },
    {
      "step_num": 3,
      "component": "ResponseAgent",
      "action": "generate",
      "timestamp": "2026-03-27T23:15:32.500000",
      "duration_ms": 2150.45,
      "input_data": {
        "query": "как определить необходимую мощность для подключения",
        "sources_count": 30,
        "max_tokens": 2000
      },
      "output_data": {
        "answer_length": 1247,
        "answer_preview": "Для определения необходимой мощности необходимо...",
        "sources_used": 5,
        "confidence": 0.82
      },
      "metadata": {}
    }
  ],
  "final_answer": "Для определения необходимой мощности необходимо учесть следующие факторы:\n\n1. Суммарную мощность всех электроприемников...\n...",
  "final_sources_count": 30,
  "errors": []
}
```

---

## 🔍 Анализ JSON лога

### 1. Просмотр в браузере

Откройте файл в любом браузере для красивого форматирования:

```bash
# Windows
start debug_logs\debug_20260327_231530.json

# Linux/Mac
open debug_logs/debug_20260327_231530.json
```

### 2. Использование jq для анализа

```bash
# Установить jq (если нет)
# Windows: choco install jq
# Linux: sudo apt install jq
# Mac: brew install jq

# Извлечь все шаги
jq '.steps[]' debug_logs/debug_*.json

# Показать только длительность операций
jq '.steps[] | {component, action, duration_ms}' debug_logs/debug_*.json

# Найти медленные операции (>1000ms)
jq '.steps[] | select(.duration_ms > 1000)' debug_logs/debug_*.json

# Показать ошибки
jq '.errors' debug_logs/debug_*.json

# Статистика по сессиям
jq '{session: .session_id, total_ms: .total_duration_ms, steps: .steps_count}' debug_logs/debug_*.json
```

### 3. Python скрипт для анализа

```python
import json
from pathlib import Path

# Загрузка последнего лога
logs = sorted(Path("debug_logs").glob("debug_*.json"))
latest = logs[-1]

with open(latest) as f:
    data = json.load(f)

print(f"Запрос: {data['query']}")
print(f"Время: {data['total_duration_ms']:.0f} ms")
print(f"Шагов: {data['steps_count']}")

for step in data['steps']:
    print(f"\n{step['step_num']}. {step['component']} - {step['action']}")
    print(f"   ⏱️ {step['duration_ms']:.0f} ms")
```

---

## 🛠️ Расширенная отладка

### 1. Трассировка с ошибками

```bash
# Запрос с потенциальной ошибкой
python agent_debugger.py "очень длинный запрос который может вызвать ошибку при обработке" * 50

# Проверка ошибок в JSON
jq '.errors' debug_logs/debug_*.json
```

### 2. Сравнение нескольких запусков

```bash
# Запустить несколько раз
python agent_debugger.py "тестовый вопрос"
python agent_debugger.py "тестовый вопрос"
python agent_debugger.py "тестовый вопрос"

# Сравнить времена
jq '.steps[] | {component, duration_ms}' debug_logs/debug_*.json
```

### 3. Поиск проблем производительности

```bash
# Найти все операции >2 сек
jq '.steps[] | select(.duration_ms > 2000) | {session: .session_id, component, duration_ms}' debug_logs/*.json

# Средняя длительность по компонентам
jq '[.steps[] | {component, duration_ms}] | group_by(.component) | map({component: .[0].component, avg_ms: (map(.duration_ms) | add / length)})' debug_logs/*.json
```

---

## 📊 Структура JSON

| Поле | Тип | Описание |
|------|-----|----------|
| `session_id` | string | Уникальный ID сессии (timestamp) |
| `query` | string | Исходный запрос пользователя |
| `started_at` | string | Время начала (ISO 8601) |
| `completed_at` | string | Время завершения (ISO 8601) |
| `total_duration_ms` | number | Общее время в мс |
| `steps_count` | number | Количество шагов |
| `steps` | array | Массив шагов (см. ниже) |
| `final_answer` | string | Финальный ответ агента |
| `final_sources_count` | number | Количество источников |
| `errors` | array | Список ошибок |

### Структура Step

| Поле | Тип | Описание |
|------|-----|----------|
| `step_num` | number | Номер шага |
| `component` | string | Компонент (QueryGenerator, SearchTool, ResponseAgent) |
| `action` | string | Действие (generate, search) |
| `timestamp` | string | Время шага (ISO 8601) |
| `duration_ms` | number | Длительность в мс |
| `input_data` | object | Входные данные |
| `output_data` | object | Выходные данные |
| `metadata` | object | Дополнительные метаданные |

---

## 🎯 Примеры использования

### 1. Отладка медленных запросов

```bash
# Запустить трассировку
python agent_debugger.py "сложный вопрос"

# Найти медленную операцию
jq '.steps[] | select(.duration_ms > 2000)' debug_logs/debug_*.json
```

### 2. Проверка параметров поиска

```bash
# Показать все параметры поиска
jq '.steps[] | select(.component == "QueryGenerator") | .output_data.search_params' debug_logs/debug_*.json
```

### 3. Анализ источников

```bash
# Показать топ источников
jq '.steps[] | select(.component == "SearchTool") | .output_data.top_5_sources' debug_logs/debug_*.json
```

### 4. Проверка ошибок

```bash
# Запустить с заведомо проблемным запросом
python agent_debugger.py ""

# Проверить ошибки
jq '.errors' debug_logs/debug_*.json
```

---

## 📁 Расположение файлов

```
backend/
├── agent_debugger.py          # Скрипт отладки
└── debug_logs/
    ├── debug_20260327_231530.json
    ├── debug_20260327_232045.json
    └── debug_20260327_233112.json
```

---

## 🔗 Интеграция с другими инструментами

### 1. Экспорт в CSV для анализа в Excel

```python
import json
import csv
from pathlib import Path

with open("debug_logs/debug_20260327_231530.json") as f:
    data = json.load(f)

# Экспорт шагов в CSV
with open("steps.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["Step", "Component", "Action", "Duration (ms)", "Input", "Output"])
    
    for step in data["steps"]:
        writer.writerow([
            step["step_num"],
            step["component"],
            step["action"],
            f"{step['duration_ms']:.0f}",
            str(step["input_data"])[:100],
            str(step["output_data"])[:100]
        ])

print("Экспортировано в steps.csv")
```

### 2. Визуализация временной шкалы

```python
import json
import matplotlib.pyplot as plt

with open("debug_logs/debug_20260327_231530.json") as f:
    data = json.load(f)

components = [s["component"] for s in data["steps"]]
times = [s["duration_ms"] for s in data["steps"]]

plt.bar(components, times)
plt.xticks(rotation=45)
plt.ylabel("Время (мс)")
plt.title(f"Время выполнения по компонентам\n{data['query'][:50]}...")
plt.tight_layout()
plt.savefig("timeline.png")
plt.show()
```

---

**Документ обновлён:** 27 марта 2026 г.  
**Файл:** `backend/agent_debugger.py`
