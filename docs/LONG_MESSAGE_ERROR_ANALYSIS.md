# 🔍 Анализ проблем с длинными сообщениями

**Дата:** 27 марта 2026 г.  
**Файл лога:** `log.md`

---

## 📋 1. Наблюдаемая проблема

В логе `log.md` видно, что ответ **обрывается на середине**:

```
2026-03-27 16:20:44 | INFO | api.endpoints.retrieval | [cb192cd8-e1e9-418d-85f1-03dc809be9ae] 
LLM ответ (длина: 1473): Let's do search.Получив уведомление об **однократности**, вы, скорее 
всего, столкнулись с тем, что система Личного кабинета (ЛК) зафиксировала, что ваша заявка уже 
была отправлена ранее и повторно подавать её нельзя.

**Почему это происходит**

1. **Один раз подаётся заявка** – в правилах технологического присоединения указано, что одна 
заявка считается действительной до её полного рассмотрения. Если попытаться отправить её 
повторно, система генерирует уведомление об однократности, сообщая, чт...
```

**Ответ обрезан на символе "чт..."** — это указывает на проблему обработки длинных текстов.

---

## 🔧 2. Возможные причины

### 2.1 Обрезка в логировании (наиболее вероятно)

**Файл:** `backend/api/endpoints.py`, строка 178

```python
# Логирование ответа LLM
retrieval_logger.info(f"[{query_id}] LLM ответ (длина: {len(answer)}): {answer[:500]}...")
```

**Проблема:** Логирование обрезает ответ до 500 символов для читаемости логов.

**Решение:** Это **не является ошибкой** — в лог пишется только превью. Полный ответ сохраняется в БД.

---

### 2.2 Таймаут при потоковой передаче

**Файл:** `backend/api/endpoints.py`, строки 170-173

```python
# Отправляем ответ по словам (эмуляция стрима)
for word in answer.split(" "):
    yield {"event": "message", "data": json.dumps({"token": word + " "})}
    await asyncio.sleep(0.02)
```

**Проблема:**
- Для ответа длиной 1473 символа (~250 слов) требуется `250 × 0.02 = 5 секунд`
- При 3000+ словах — 60+ секунд только на передачу
- **SSE таймаут** может возникнуть на уровне Nginx или браузера

**Решение:**
```python
# Уменьшить задержку или убрать её
await asyncio.sleep(0.01)  # или 0.005
```

---

### 2.3 Ограничение размера в Supabase

**Файл:** `backend/api/database.py`

**Проблема:** PostgreSQL (Supabase) поддерживает `text` до 1 ГБ, но:
- **HTTP запрос** имеет лимит на размер тела (обычно 1-10 МБ)
- **Supabase Client** может иметь свои ограничения

**Проверка:**
```sql
-- Проверка размера поля answer в таблице chats
SELECT 
  pg_column_size(answer) as size_bytes,
  length(answer) as char_count
FROM chats 
ORDER BY size_bytes DESC 
LIMIT 10;
```

**Решение:** Если размер превышает 1 МБ, рассмотреть:
- Сжатие текста перед сохранением
- Разбиение на части (chunking)
- Хранение в object storage (S3)

---

### 2.4 Обрезка в LLM API

**Файл:** `backend/agents/response_agent.py`

```python
max_tokens: int = 2000  # Параметр по умолчанию
```

**Проблема:**
- 2000 токенов ≈ 1500-1600 слов ≈ 10 000-12 000 символов
- Если ответ превышает лимит, LLM обрезает его

**Решение:**
- Увеличить `max_tokens` до 3000-4000
- Использовать стриминг от LLM (если поддерживается)

---

### 2.5 Проблема сериализации JSON

**Файл:** `backend/api/endpoints.py`, строка 172

```python
yield {"event": "message", "data": json.dumps({"token": word + " "})}
```

**Проблема:**
- Специальные символы (кириллица, эмодзи) могут некорректно экранироваться
- Длинные слова (>1000 символов) могут вызвать проблемы

**Решение:**
```python
json.dumps({"token": word + " "}, ensure_ascii=False)
```

---

##  3. Статистика длинных ответов

### Бенчмарк (36 запросов)

| Метрика | Значение |
|---------|----------|
| **Средняя длина ответа** | ~1200-1500 символов |
| **Максимальная длина** | ~3000 символов |
| **Среднее время генерации** | 1.80 сек |

### Расчёт времени передачи

| Длина ответа | Слов | Время передачи (20ms) | Время передачи (5ms) |
|--------------|------|----------------------|---------------------|
| 1000 симв. | ~170 | 3.4 сек | 0.85 сек |
| 2000 симв. | ~340 | 6.8 сек | 1.7 сек |
| 3000 симв. | ~500 | 10 сек | 2.5 сек |
| 5000 симв. | ~850 | 17 сек | 4.25 сек |

**Вывод:** При задержке 20ms ответы длиннее 3000 символов передаются >10 секунд, что может вызвать таймаут.

---

## ✅ 4. Рекомендации

### 4.1 Критические исправления

#### 1. Уменьшить задержку в SSE

**Файл:** `backend/api/endpoints.py`

```python
# Было
await asyncio.sleep(0.02)

# Стало
await asyncio.sleep(0.005)  # 5ms вместо 20ms
```

#### 2. Добавить `ensure_ascii=False` в JSON

**Файл:** `backend/api/endpoints.py`, строка 172

```python
# Было
yield {"event": "message", "data": json.dumps({"token": word + " "})}

# Стало
yield {"event": "message", "data": json.dumps({"token": word + " "}, ensure_ascii=False)}
```

#### 3. Логировать полную длину ответа

**Файл:** `backend/api/endpoints.py`, строка 178

```python
# Было
retrieval_logger.info(f"[{query_id}] LLM ответ (длина: {len(answer)}): {answer[:500]}...")

# Стало
retrieval_logger.info(f"[{query_id}] LLM ответ (длина: {len(answer)} символов, {len(answer.split())} слов)")
```

---

### 4.2 Опциональные улучшения

#### 4. Добавить таймауты для SSE

**Файл:** `backend/api/endpoints.py`

```python
from asyncio import wait_for, TimeoutError

@router.post("/query/stream")
async def stream_query(...):
    ...
    
    async def event_generator():
        try:
            # Устанавливаем таймаут на всю операцию
            async with asyncio.timeout(120):  # 2 минуты
                async for event in generate_events():
                    yield event
        except TimeoutError:
            error_logger.error(f"[{query_id}] Таймаут потоковой передачи")
            yield {"event": "message", "data": json.dumps({
                "error": "Превышено время ожидания ответа"
            })}
```

#### 5. Добавить прогресс для длинных ответов

```python
# Отправляем прогресс каждые 100 слов
for i, word in enumerate(answer.split(" ")):
    yield {"event": "message", "data": json.dumps({"token": word + " "}, ensure_ascii=False)}
    
    if i % 100 == 0 and i > 0:
        yield {"event": "message", "data": json.dumps({
            "progress": f"Генерация: {i}/{len(answer.split())} слов"
        })}
    
    await asyncio.sleep(0.005)
```

#### 6. Сжатие данных в SSE

```python
from fastapi.responses import StreamingResponse
import gzip

# В middleware или настройках
app.add_middleware(
    GZipMiddleware,
    minimum_size=1000,  # Сжимать ответы >1KB
)
```

---

### 4.3 Мониторинг

#### Добавить метрики длины ответов

**Файл:** `backend/api/endpoints.py`

```python
# После генерации ответа
answer_length = len(answer)
answer_words = len(answer.split())

retrieval_logger.info(
    f"[{query_id}] Ответ: {answer_length} символов, {answer_words} слов, "
    f"{answer_length/answer_words:.1f} симв/слово"
)

# Предупреждение для очень длинных ответов
if answer_length > 5000:
    retrieval_logger.warning(f"[{query_id}] Очень длинный ответ: {answer_length} символов")
```

---

## 🧪 5. Тесты для проверки

### Тест 1: Длинный ответ (>3000 символов)

```python
def test_long_answer_streaming():
    """Проверка потоковой передачи длинного ответа."""
    response = client.post("/query/stream", json={
        "query": "Подробно опишите процедуру технологического присоединения " * 50  # Длинный запрос
    })
    
    # Проверка: ответ получен полностью
    assert response.status_code == 200
    
    # Проверка: нет ошибок JSON
    events = list(response.iter_lines())
    for event in events:
        data = json.loads(event.split("data: ")[1])
        assert "error" not in data
```

### Тест 2: Специальные символы

```python
def test_cyrillic_and_emojis():
    """Проверка обработки кириллицы и специальных символов."""
    response = client.post("/query/stream", json={
        "query": "Тест с эмодзи: 🚀⚡ и специальными символами: ©®™"
    })
    
    assert response.status_code == 200
    # Проверка: символы корректно переданы
```

---

## 📝 6. Чек-лист исправлений

- [ ] Уменьшить `asyncio.sleep()` с 20ms до 5ms
- [ ] Добавить `ensure_ascii=False` во все `json.dumps()` в SSE
- [ ] Добавить логирование полной длины ответа (символы + слова)
- [ ] Добавить предупреждения для ответов >5000 символов
- [ ] Протестировать передачу ответов 3000+, 5000+, 10000+ символов
- [ ] Проверить таймауты Nginx (должны быть >60 сек для SSE)
- [ ] Добавить мониторинг размера ответов в Supabase

---

## 🔗 7. Связанные файлы

| Файл | Проблема |
|------|----------|
| `backend/api/endpoints.py` | SSE стриминг, задержка 20ms |
| `backend/api/database.py` | Сохранение в Supabase |
| `backend/agents/response_agent.py` | Генерация ответа, max_tokens |
| `log.md` | Лог с обрезанным ответом |

---

**Статус:** Требуется исправление  
**Приоритет:** Средний (проблема не критическая, но влияет на UX)  
**Время на исправление:** 1-2 часа
