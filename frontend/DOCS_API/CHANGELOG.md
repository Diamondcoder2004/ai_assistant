# Changelog

Все изменения в проекте RAG API для Башкирэнерго.

## [2026-03-22]

### Изменения в API

#### Добавлено
- **POST /query/stream** — потоковый endpoint с SSE (Server-Sent Events)
  - События: `status`, `sources`, `session_id`, `token`, `done`, `error`
  - Поддержка возобновления сессий через `session_id`
- **Поле `use_reranker`** в QueryRequest для переопределения глобальной настройки
- **GET /history** — получение истории чатов пользователя
- **POST /feedback** — отправка обратной связи (like/dislike/оценка)

#### Изменено
- **Реранкинг** — теперь управляется переменной `USE_RERANKER` в `.env`
  - Приоритет: `request.use_reranker` > `config.USE_RERANKER`
  - Логирование этапа реранкинга с таймингами
- **BM25 поиск** — использует только поле `content` (без keywords/entities/questions)
  - Улучшено различие документов по уникальным терминам
  - Убрано дублирование терминов из метаданных
- **Нормализация BM25** — изменена с sigmoid на `tanh(x/5)`
  - Лучшее распределение оценок в диапазоне [0, 1)
  - Сохранение относительных различий между документами

#### Улучшения
- Добавлено событие `session_id` в streaming для возобновления чатов
- Улучшено логирование всех этапов обработки запроса
- Добавлена валидация параметров запроса через Pydantic Field

### Изменения в поиске

#### Hybrid Retrieval (`retrieval/hybrid_retrieval.py`)
- **BM25 только по content** — убрано дублирование keywords/entities/questions
- **tanh(x/5) нормализация** — вместо sigmoid для лучшего распределения
- **Лемматизация pymorphy3** — для русского языка

#### Реранкер (`reranker.py`)
- Исправлено сохранение `batch_size` в `__init__`
- Улучшена обработка payload с разными форматами данных

### Конфигурация

#### Добавлено в `.env`
```env
# Reranker
USE_RERANKER=true
```

#### Добавлено в `config.py`
```python
USE_RERANKER = os.getenv("USE_RERANKER", "true").lower() in ("true", "1", "yes")
```

### Документация

#### Создано
- `docs/API.md` — полная документация API
- `docs/CHANGELOG.md` — история изменений (этот файл)
- `docs/ARCHITECTURE.md` — описание архитектуры системы
- `api/README.md` — краткая документация API
- `.env.example` — шаблон переменных окружения

#### Обновлён
- `QWEN.md` — инструкции по работе с проектом

### Удалено
- `app_gradio.py` — перенесён в отдельный проект
- `test_*.py` — тесты вынесены в отдельную директорию
- `benchmarks/` — бенчмарки вынесены для публикации
- `analytics/` — аналитика вынесена для публикации
- `chunks*/` — данные не публикуются
- `TUSKS/` — служебная директория

### .gitignore

Обновлён для исключения:
```
# Данные
chunks*/
*.pkl
*.zip
logs/
bm25_cache.pkl

# Тесты и бенчмарки
test_*.py
benchmarks/
analytics/
TUSKS/

# Временные файлы
$null
*.pyc
__pycache__/
```

---

## [2026-03-21]

### Изменения в обработке эмбеддингов

#### Исправлено
- **Perplexity API** — добавлена конвертация int8 → float32
  - Нормализация на диапазон [-1, 1] (деление на 127.0)
  - L2 нормализация для cosine similarity
- **Централизованный класс** — `RouterAIEmbeddings` в `utils/router_embedding.py`

#### Обновлены файлы
- `utils/router_embedding.py` — класс `RouterAIEmbeddings`
- `qdrant_ingest/ingest_qdrant_hybrid.py` — загрузка документов
- `retrieval/hybrid_retrieval.py` — query векторы

### Benchmark

#### Добавлено
- `benchmarks/run_benchmark_sweep.py` — запуск с разными весами
- Метрики: BLEU, ROUGE-L, Embedding Similarity, LLM Judge
- Выходные файлы: `results.csv`, `contexts_wide.csv`, `summary_stats.*`

#### Исправлено
- Сохранение CSV с явными колонками
- Унификация `get_routerai_embedder()` через `utils/router_embedding`

---

## [2026-03-20]

### Начальная версия

#### Компоненты
- **Hybrid Retrieval** — 4 компонента (pref, hype, lexical, contextual)
- **BM25** — с лемматизацией pymorphy3
- **Reranker** — BAAI/bge-reranker-v2-m3
- **LLM** — RouterAI (Qwen)
- **Qdrant** — векторное хранилище
- **Supabase** — хранение чатов и пользователей

#### API Endpoints
- POST /query
- POST /query/stream
- GET /health
- GET /history
- POST /feedback

#### Веб-интерфейс
- Streaming токенов
- История чатов с возобновлением
- Русификация UI
- Индикаторы генерации и поиска
