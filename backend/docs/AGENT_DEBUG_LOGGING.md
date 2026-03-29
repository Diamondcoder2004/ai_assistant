# Agent Debug Logging System

Система детального логирования работы агентов для отладки.

## Настройка

### Включение логирования

Добавьте в `.env`:

```bash
# Включить детальное логирование агентов (true/false)
AGENT_DEBUG_ENABLED=true

# Логировать промпты (true/false) - может содержать чувствительные данные
AGENT_DEBUG_LOG_PROMPTS=true
```

**Важно:** По умолчанию логирование **выключено** (`AGENT_DEBUG_ENABLED=false`).

## Структура логов

Логи сохраняются в `backend/logs/agent_debug/{session_id}/debug.json`

### Пример структуры

```
logs/
  agent_debug/
    20260329_143000/
      debug.json
    20260329_143500/
      debug.json
```

## Формат лога

Каждый запрос записывается в формате:

```json
{
  "session_id": "20260329_143000",
  "query": "сроки рассмотрения заявки",
  "started_at": "2026-03-29T14:30:00.000000",
  "completed_at": "2026-03-29T14:30:30.000000",
  "total_duration_ms": 30000.5,
  "steps_count": 2,
  "steps": [
    {
      "step_num": 1,
      "component": "SearchAgent",
      "action": "search",
      "timestamp": "2026-03-29T14:30:10.000000",
      "duration_ms": 10000.2,
      "input_data": {...},
      "output_data": {...},
      "metadata": {...}
    },
    {
      "step_num": 2,
      "component": "ResponseAgent",
      "action": "generate",
      "timestamp": "2026-03-29T14:30:30.000000",
      "duration_ms": 20000.3,
      "input_data": {...},
      "output_data": {...},
      "metadata": {...}
    }
  ],
  "final_answer": "...",
  "final_sources_count": 10,
  "errors": []
}
```

## Использование в коде

### Базовое использование

```python
from utils.agent_debug_logger import get_debug_logger

debug_logger = get_debug_logger()

# В начале запроса
session_logger = debug_logger.create_session_log(session_id, query)

# Логирование шага
with session_logger.step("ComponentName", "action", {"input": "data"}) as step:
    # Выполнение кода
    result = do_something()
    
    # Запись результата
    step.set_output({
        "result": result,
        "count": len(result)
    })

# Финальный ответ
session_logger.set_final_answer(answer, sources_count)

# Сохранение (автоматически в конце запроса)
session_logger.save()
```

### Логирование промптов

Если `AGENT_DEBUG_LOG_PROMPTS=true`, промпты записываются в каждый шаг:

```python
with session_logger.step(
    "ResponseAgent",
    "generate",
    {"query": "..."},
    prompt=system_prompt + user_prompt  # Промпт запишется в лог
) as step:
    ...
```

## Производительность

- Логирование работает **асинхронно** в отдельном потоке
- Не блокирует основной процесс обработки запроса
- Автоматическая очистка больших данных (>500 символов)
- Ограничение списков (макс 20 элементов)

## Отключение

Для продакшена установите в `.env`:

```bash
AGENT_DEBUG_ENABLED=false
```

Логи перестанут записываться, но код продолжит работать.
