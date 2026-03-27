# 🎮 Playground - Инструмент для тестирования Agentic RAG

**Назначение:** Пошаговое тестирование всех компонентов системы с детальным логированием для отладки ошибок.

---

## 🚀 Быстрый старт

### Запуск полного теста

```bash
cd backend
python playground.py
```

Логирование сохраняется в: `backend/logs/playground_YYYYMMDD_HHMMSS.log`

---

## 📋 Доступные тесты

| № | Тест | Описание | Время выполнения |
|---|------|----------|------------------|
| 1 | **Query Generator** | Генерация поисковых запросов | ~2 сек |
| 2 | **Search Tool** | Поиск в Qdrant с эмбеддингами | ~1-2 сек |
| 3 | **Response Agent** | Генерация ответа LLM | ~2-4 сек |
| 4 | **Full Pipeline** | Полный цикл Agentic RAG | ~5-8 сек |
| 5 | **Long Query** | Обработка длинных запросов | ~5-10 сек |
| 6 | **Special Characters** | Кириллица, эмодзи, спецсимволы | ~10-15 сек |
| 7 | **Timing Stats** | Статистика производительности | ~15-20 сек |
| 8 | **Database** | Сохранение/чтение из Supabase | ~1-2 сек |

---

## 🔧 Как использовать

### 1. Выбор тестов для запуска

Откройте `backend/playground.py`, найдите секцию `MAIN`:

```python
tests = [
    ("Query Generator", test_query_generator, False),      # ← Измените на True
    ("Search Tool", test_search_tool, False),              # ← для запуска
    ("Response Agent", test_response_agent, False),
    ("Full Pipeline", test_full_pipeline, True),           # ← Уже включён
    ("Long Query", test_long_query, False),
    ("Special Characters", test_special_characters, False),
    ("Timing Stats", test_timing_stats, False),
    ("Database", test_database_operations, False),
]
```

Измените `False` на `True` для нужных тестов.

### 2. Запуск конкретного теста

```bash
# Только Query Generator
python -c "from playground import test_query_generator; test_query_generator()"

# Только Search Tool
python -c "from playground import test_search_tool; test_search_tool()"

# Только полный цикл
python -c "from playground import test_full_pipeline; test_full_pipeline()"
```

### 3. Запуск с фильтром логов

```bash
# Только ошибки
python playground.py 2>&1 | grep ERROR

# Только предупреждения
python playground.py 2>&1 | grep WARNING

# Сохранение в файл
python playground.py > test_output.txt 2>&1
```

---

## 📊 Пример вывода

```
============================================================
🎮 AGENTIC RAG PLAYGROUND
============================================================
Время запуска: 2026-03-27 22:30:15
Логирование: logs/playground_20260327_223015.log
============================================================

▶️ Запуск: Full Pipeline

============================================================
ТЕСТ 4: Full Agentic RAG Pipeline
============================================================

📝 Запрос: как определить необходимую мощность для подключения к электросети
------------------------------------------------------------

2026-03-27 22:30:16 | INFO     | main | Запрос: 'как определить необходимую мощность...'
2026-03-27 22:30:16 | INFO     | agents.query_generator | Генерация запросов...
2026-03-27 22:30:18 | INFO     | httpx | HTTP Request: POST https://routerai.ru/api/v1/chat/completions
2026-03-27 22:30:18 | INFO     | agents.search_agent | Поиск по запросам...
2026-03-27 22:30:19 | INFO     | httpx | HTTP Request: POST http://host.docker.internal:6333/collections/...
2026-03-27 22:30:19 | INFO     | agents.response_agent | Генерация ответа...
2026-03-27 22:30:21 | INFO     | httpx | HTTP Request: POST https://routerai.ru/api/v1/chat/completions

============================================================
РЕЗУЛЬТАТЫ
============================================================

⏱️ Общее время: 5.42 сек

🔍 Поисковые запросы:
   1. как рассчитать необходимую мощность для подключения
   2. методика определения мощности подключения
   3. нормативные требования к мощности при присоединении

📊 Параметры поиска:
   - k: 30
   - strategy: concat
   - weights: {'pref': 0.4, 'hype': 0.3, 'contextual': 0.3}

📚 Источники: 30 шт.
   1. FAQ_ТП.pdf (score: 0.923)
   2. Правила_присоединения.md (score: 0.891)
   3. Технические_условия.docx (score: 0.854)

✍️ Ответ (1247 символов):
------------------------------------------------------------
Для определения необходимой мощности необходимо учесть...
...

🎯 Confidence: 0.85

============================================================
✅ Full Pipeline: Full Pipeline: OK
============================================================
```

---

## 🐛 Отладка ошибок

### 1. Поиск в логах

```bash
# Найти все ошибки
grep "ERROR" logs/playground_*.log

# Найти конкретную операцию
grep "SearchAgent" logs/playground_*.log

# Найти таймауты
grep "timeout\|Timeout" logs/playground_*.log
```

### 2. Анализ производительности

```bash
# Найти медленные операции (>2 сек)
grep -E "\|[0-9]{4,}\.ms" logs/playground_*.log

# Статистика по операциям
grep "⏱️" logs/playground_*.log
```

### 3. Тестирование гипотез

**Проблема:** Ответ обрывается

```python
# В playground.py добавьте тест
def test_debug_truncated_answer():
    from main import AgenticRAG
    
    rag = AgenticRAG()
    result = rag.query("тестовый вопрос")
    
    print(f"Длина ответа: {len(result['answer'])}")
    print(f"max_tokens: {result.get('search_params', {}).get('max_tokens')}")
    
    # Проверка: ответ не превышает лимит
    assert len(result['answer']) < 10000, "Ответ слишком длинный!"
```

---

## 📈 Метрики для мониторинга

### Критические

| Метрика | Норма | Критично |
|---------|-------|----------|
| **Время генерации запросов** | <2 сек | >5 сек |
| **Время поиска** | <1 сек | >3 сек |
| **Время генерации ответа** | <3 сек | >10 сек |
| **Общее время** | <6 сек | >15 сек |
| **Длина ответа** | 500-3000 симв. | >10000 симв. |

### Предупреждения

```python
# В логах ищите:
WARNING | Очень длинный ответ: 6234 символов
ERROR | TimeoutError
ERROR | HTTP Request failed
ERROR | Qdrant connection error
```

---

## 🔗 Интеграция с другими тестами

### Запуск вместе с unit-тестами

```bash
# Все тесты
pytest backend/tests/ -v

# Playground + тесты
python backend/playground.py && pytest backend/tests/ -v
```

### Автоматизация в CI/CD

```yaml
# .github/workflows/test.yml
- name: Run Playground Tests
  run: |
    cd backend
    python playground.py
    
- name: Upload Logs
  uses: actions/upload-artifact@v2
  with:
    name: playground-logs
    path: backend/logs/playground_*.log
```

---

## 🛠️ Расширение playground

### Добавление нового теста

```python
# =============================================================================
# TEST 9: Ваш тест
# =============================================================================

def test_your_feature():
    """Описание теста."""
    from your_module import YourClass
    
    print("\n" + "="*60)
    print("ТЕСТ 9: Your Feature")
    print("="*60)
    
    # Тестирование
    obj = YourClass()
    result = obj.your_method("test")
    
    print(f"✅ Результат: {result}")
    
    return "Your Feature: OK"


# В секции MAIN добавьте:
tests = [
    ...
    ("Your Feature", test_your_feature, False),
]
```

---

## 📝 Чек-лист использования

Перед запуском:

- [ ] Проверьте `.env` файл (RouterAI, Qdrant, Supabase)
- [ ] Убедитесь, что Docker контейнеры запущены
- [ ] Проверьте подключение к внешним API

После запуска:

- [ ] Проверьте логи на наличие ERROR
- [ ] Сверьте время выполнения с нормами
- [ ] Сохраните логи для анализа (если найдены проблемы)

---

## 📞 Быстрые команды

```bash
# Запустить полный тест
python backend/playground.py

# Запустить только тест производительности
python -c "from backend.playground import test_timing_stats; test_timing_stats()"

# Найти последнюю ошибку
grep -r "ERROR" backend/logs/playground_*.log | tail -1

# Показать последние 50 строк лога
tail -50 backend/logs/playground_*.log
```

---

**Документ обновлён:** 27 марта 2026 г.  
**Файл:** `backend/playground.py`
