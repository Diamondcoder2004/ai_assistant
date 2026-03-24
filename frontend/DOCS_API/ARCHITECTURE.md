# Архитектура RAG системы

## Обзор

Система представляет собой RAG (Retrieval-Augmented Generation) платформу для интеллектуального поиска и генерации ответов на основе документации Башкирэнерго.

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Client    │────▶│  FastAPI     │────▶│   Qdrant    │
│  (React/JS) │     │   Backend    │     │  (Vectors)  │
└─────────────┘     └──────────────┘     └─────────────┘
                          │
                          ▼
                    ┌──────────────┐
                    │   Supabase   │
                    │   (Storage)  │
                    └──────────────┘
```

---

## Компоненты

### 1. Backend (FastAPI)

**Файл:** `api/api.py`

#### Endpoints
- `POST /query` — непотоковый запрос
- `POST /query/stream` — потоковый запрос (SSE)
- `GET /health` — health check
- `GET /history` — история чатов
- `POST /feedback` — обратная связь

#### Middleware
- CORS
- Логирование запросов
- Аутентификация (JWT)

---

### 2. Гибридный поиск

**Файл:** `retrieval/hybrid_retrieval.py`

#### Компоненты поиска

| Компонент | Вес | Описание |
|-----------|-----|----------|
| **pref** | 0.5 | Вектор summary + content |
| **hype** | 0.3 | Вектор гипотетических вопросов |
| **lexical** | 0.2 | BM25 (лемматизированный) |
| **contextual** | 0.0 | Вектор соседних чанков |

#### Формула

```
score = 0.5 * pref + 0.3 * hype + 0.2 * lexical + 0.0 * contextual
```

#### Нормализация

- **pref/hype/contextual:** cosine similarity из Qdrant (уже в [-1, 1])
- **lexical:** `tanh(BM25 / 5.0)` для приведения к [0, 1)

#### Лемматизация

```python
import pymorphy3

morph = pymorphy3.MorphAnalyzer()
parsed = morph.parse("подал")[0]
lemma = parsed.normal_form  # "подать"
```

---

### 3. Реранкинг

**Файл:** `reranker.py`

#### Модель
- **BAAI/bge-reranker-v2-m3**
- CrossEncoder для ранжирования пар (query, document)

#### Управление

```python
# Глобально (.env)
USE_RERANKER=true

# На уровне запроса
{"query": "...", "use_reranker": false}
```

#### Приоритет
```
request.use_reranker > config.USE_RERANKER
```

---

### 4. Эмбеддинги

**Файл:** `utils/router_embedding.py`

#### Модель
- **perplexity/pplx-embed-v1-4b**
- Размерность: 2560

#### Конвертация

```python
import numpy as np

def convert_embedding(emb: List[float]) -> List[float]:
    emb_array = np.array(emb, dtype=np.float32)
    
    # 1. Нормализация int8 → [-1, 1]
    emb_array = emb_array / 127.0
    
    # 2. L2 нормализация для cosine similarity
    norm = np.linalg.norm(emb_array)
    if norm > 0:
        emb_array = emb_array / norm
    
    return emb_array.tolist()
```

---

### 5. LLM Генерация

**Файл:** `llm.py`

#### Модель по умолчанию
- **qwen/qwen3.5-flash-02-23**

#### Параметры
- temperature: 0.0-2.0 (default: 0.8)
- max_tokens: 100-8000 (default: 2000)

#### Контекст
- История диалога (последние 10 сообщений)
- Найденные документы (top-k после реранка)
- Системный промпт для RAG

---

### 6. Хранилище

#### Qdrant (Векторы)

**Файл:** `qdrant_ingest/ingest_qdrant_hybrid.py`

**Коллекция:** `BASHKIR_ENERGO_PERPLEXITY`

**Векторы:**
- `pref` — summary + content
- `hype` — гипотетические вопросы
- `contextual` — соседние чанки

**Payload:**
```json
{
  "content": "...",
  "chunk_summary": "...",
  "keywords": ["...", "..."],
  "entities": ["...", "..."],
  "questions": ["...", "..."],
  "source_file": "...",
  "breadcrumbs": "...",
  "category": "legal"
}
```

#### Supabase (Данные)

**Таблица:** `chats`

**Поля:**
- `id` — UUID
- `user_id` — UUID пользователя
- `session_id` — UUID сессии
- `question` — текст вопроса
- `answer` — сгенерированный ответ
- `parameters` — параметры запроса (JSON)
- `sources` — источники (JSON)
- `context` — полный контекст (текст)
- `created_at` — timestamp

---

## Поток данных

### Запрос пользователя

```
1. Клиент → POST /query/stream
   {
     "query": "Как подать заявку?",
     "k": 30,
     "rerank_top_k": 3
   }

2. Backend → Hybrid Retrieval
   - Поиск по pref (вектор)
   - Поиск по hype (вектор)
   - Поиск по lexical (BM25)
   - Поиск по contextual (вектор)
   - Объединение с весами

3. Backend → Reranker
   - Ранжирование top-k документов
   - Отсечение по min_score

4. Backend → LLM
   - Формирование контекста
   - Генерация ответа (streaming)

5. Backend → Supabase
   - Сохранение чата (фон)

6. Backend → Клиент (SSE)
   - status: "🔍 Поиск документов..."
   - status: "⚖️ Оценка релевантности..."
   - sources: [...]
   - session_id: "uuid"
   - token: "Часть ответа"
   - done: "Полный ответ"
```

---

## Кэширование

### BM25

**Файл:** `bm25_cache.pkl`

**Содержимое:**
```python
{
  'bm25': BM25Plus объект,
  'point_ids': [...],
  'payloads': {...},
  'documents': [...]
}
```

**Очистка:**
```python
from retrieval.hybrid_retrieval import clear_cache
clear_cache()
```

---

## Логирование

**Директория:** `logs/`

**Файлы:** `api_YYYYMMDD.log`

**Формат:**
```
2026-03-22 12:00:00 | INFO | api.api.retrieval | [query_id] Сообщение
```

**Логгеры:**
- `api.api.database` — операции с БД
- `api.api.llm` — генерация LLM
- `api.api.retrieval` — поиск документов
- `api.api.auth` — аутентификация
- `api.api.errors` — ошибки

---

## Безопасность

### Аутентификация

**Метод:** Bearer Token (JWT)

**Header:**
```
Authorization: Bearer YOUR_JWT_SECRET
```

**Middleware:** `get_current_user()` в `api/auth.py`

### CORS

**Настройки:**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Настроить для production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Масштабирование

### Горизонтальное

- **Backend:** Несколько экземпляров FastAPI за load balancer
- **Qdrant:** Кластер из нескольких узлов
- **Supabase:** Managed решение с автоматическим масштабированием

### Вертикальное

- **GPU:** Для реранкера и LLM (опционально)
- **RAM:** Для кэширования BM25 и векторов
- **CPU:** Для лемматизации и предобработки

---

## Мониторинг

### Метрики

- Время поиска документов
- Время реранкинга
- Время генерации LLM
- Количество токенов
- Длина ответов
- Количество источников

### Логирование

```python
retrieval_logger.info(f"[{query_id}] Поиск: {len(hits)} документов")
retrieval_logger.info(f"[{query_id}] Реранк: {rerank_time:.3f}s")
llm_logger.info(f"[{query_id}] LLM: {token_count} токенов")
```

---

## Развёртывание

### Требования

- Python 3.11+
- Qdrant 1.7+
- Supabase (локальный или cloud)
- GPU (опционально, для реранкера)

### Установка

```bash
# Клонирование
git clone https://github.com/Diamondcoder2004/bashkir_rag.git
cd bashkir_rag

# Установка зависимостей
pip install -r requirements.txt

# Копирование .env
cp .env.example .env

# Запуск
uvicorn api.api:app --host 0.0.0.0 --port 8000
```

### Переменные окружения

См. `.env.example`:
- QDRANT_HOST, QDRANT_PORT
- ROUTERAI_API_KEY
- SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
- USE_RERANKER

---

## Тестирование

### Unit тесты

```bash
pytest tests/
```

### Интеграционные тесты

```bash
python test_api_endpoints.py
```

### Benchmark

```bash
python benchmarks/run_benchmark_sweep.py
```

---

## Структура проекта

```
bashkir_rag/
├── api/
│   ├── api.py              # FastAPI приложение
│   ├── auth.py             # Аутентификация
│   └── README.md           # Документация API
├── retrieval/
│   └── hybrid_retrieval.py # Гибридный поиск
├── utils/
│   └── router_embedding.py # Эмбеддинги RouterAI
├── qdrant_ingest/
│   └── ingest_qdrant_hybrid.py # Загрузка в Qdrant
├── benchmarks/
│   ├── benchmark.py        # Оценка качества
│   └── run_benchmark_sweep.py # Серии запусков
├── docs/
│   ├── API.md              # Документация API
│   ├── CHANGELOG.md        # История изменений
│   └── ARCHITECTURE.md     # Архитектура (этот файл)
├── config.py               # Конфигурация
├── llm.py                  # LLM запросы
├── reranker.py             # Реранкинг
├── .env                    # Переменные окружения
├── .env.example            # Шаблон переменных
├── .gitignore              # Игнорируемые файлы
├── pyproject.toml          # Зависимости
├── QWEN.md                 # Контекст проекта
└── README.md               # Основная документация
```

---

## Контакты

**Репозиторий:** https://github.com/Diamondcoder2004/bashkir_rag

**Документация:** docs/
