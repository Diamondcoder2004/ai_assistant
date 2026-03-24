# Быстрый старт для Agentic RAG Benchmark

## 🚀 Запуск бенчмарка

### 1. Настройка окружения

```bash
cd d:\PythonProjects\agentic_rag
cp .env.example .env
```

Заполните `.env`:
```env
ROUTERAI_API_KEY=sk-ваш-ключ
QDRANT_HOST=localhost
QDRANT_PORT=6333
COLLECTION_NAME=BASHKIR_ENERGO_PERPLEXITY
```

### 2. Запуск оптимизированного бенчмарка

```bash
# На всех вопросах из benchmark_results.csv
python benchmarks/agentic_benchmark_optimized.py

# С кастомным файлом вопросов
python benchmarks/agentic_benchmark_optimized.py --input ваш_файл.csv
```

## 📊 Структура результатов

После запуска в папке `agentic_benchmarks/agentic_benchmark_TIMESTAMP/`:

```
agentic_benchmark_20260323_120000/
├── config.json              # Конфигурация бенчмарка
└── results.csv              # Результаты по каждому вопросу
```

### Поля results.csv:

| Поле | Описание |
|------|----------|
| `index` | Номер вопроса |
| `question` | Вопрос |
| `expected` | Ожидаемый ответ |
| `answer` | Сгенерированный ответ |
| `time_total_sec` | Общее время |
| `num_hits` | Количество источников |
| `confidence` | Уверенность системы |
| `queries_used` | Поисковые запросы (JSON) |
| `judge_relevance` | Релевантность (1-5) |
| `judge_completeness` | Полнота (1-5) |
| `judge_helpfulness` | Полезность (1-5) |
| `judge_clarity` | Ясность (1-5) |
| `judge_hallucination_risk` | Риск галлюцинаций (1-5) |
| `judge_overall_score` | Общая оценка (1-5) |
| `judge_justification` | Обоснование оценки |

## 🎯 Сравнение с benchmark_optimized.py

| Характеристика | benchmark_optimized.py | agentic_benchmark_optimized.py |
|----------------|------------------------|--------------------------------|
| **RAG система** | Классическая | Agentic (LLM агенты) |
| **Генерация запросов** | Один запрос | 2-3 запроса от LLM |
| **Подбор весов** | Фиксированные | Автоматический |
| **Стиль ответа** | Технический | Дружелюбный |
| **Цитирование** | Простое | С ссылками на документы |
| **LLM Judge** | Отдельный промпт | Встроенный модуль |
| **Время** | ~22 сек/вопрос | ~45 сек/вопрос |
| **Качество** | Хорошее | Отличное |

## 📈 Метрики

### Временные:
- `time_retrieve_sec` — поиск документов
- `time_generation_sec` — генерация ответа
- `time_total_sec` — общее время

### LLM Judge (1-5):
- **Relevance** — релевантность вопросу
- **Completeness** — полнота ответа
- **Helpfulness** — полезность
- **Clarity** — ясность изложения
- **Hallucination Risk** — риск галлюцинаций (5 = низкий)
- **Overall Score** — средняя оценка

## 🔧 Настройки

В начале `agentic_benchmark_optimized.py`:

```python
PARALLEL_REQUESTS = 2  # Параллельных запроса
RETRIEVE_K = 30  # Количество документов для поиска
ENABLE_JUDGE = True  # LLM Judge оценка
JUDGE_MODEL = "qwen/qwen3.5-flash-02-23"  # Модель для судьи
```

## 💡 Примеры использования

### Быстрый тест (5 вопросов):
```python
# В agentic_benchmark_optimized.py изменить:
FAQ_FILE = Path("d:/PythonProjects/bashkir_rag/benchmarks/benchmark_results.csv")

# Или создать копию с ограничением:
questions = questions[:5]
```

### Без LLM Judge (быстрее):
```python
ENABLE_JUDGE = False
```

### С кастомными весами:
```python
RETRIEVE_PREF_WEIGHT = 0.5
RETRIEVE_HYPE_WEIGHT = 0.2
RETRIEVE_LEXICAL_WEIGHT = 0.2
RETRIEVE_CONTEXTUAL_WEIGHT = 0.1
```

## 📊 Анализ результатов

После бенчмарка можно проанализировать результаты:

```python
import pandas as pd

df = pd.read_csv("agentic_benchmarks/agentic_benchmark_TIMESTAMP/results.csv")

# Средняя оценка
print(f"Overall Score: {df['judge_overall_score'].mean():.2f}/5")

# Распределение оценок
print(df['judge_relevance'].value_counts())

# Корреляция времени и качества
print(df[['time_total_sec', 'judge_overall_score']].corr())
```

## 🎯 Интерпретация результатов

| Оценка | Интерпретация |
|--------|---------------|
| **4.5-5.0** | Отличное качество |
| **4.0-4.5** | Хорошее качество |
| **3.5-4.0** | Удовлетворительное |
| **< 3.5** | Требует улучшений |

## ⚠️ Возможные проблемы

### Медленная скорость:
- Уменьшите `PARALLEL_REQUESTS` до 1
- Отключите LLM Judge (`ENABLE_JUDGE = False`)
- Уменьшите `RETRIEVE_K`

### Ошибки API:
- Проверьте `ROUTERAI_API_KEY`
- Проверьте подключение к Qdrant
- Увеличьте `JUDGE_RETRY_DELAY`

### Мало источников:
- Увеличьте `RETRIEVE_K`
- Измените веса поиска
- Проверьте коллекцию Qdrant
