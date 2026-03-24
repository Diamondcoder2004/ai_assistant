# Agentic RAG with Tool Calling

Автономная RAG система с использованием LLM агентов для генерации поисковых запросов и подбора параметров поиска.

## 📖 Описание

Система использует LLM для:
- Переформулирования пользовательских запросов в поисковые вопросы
- Генерации нескольких поисковых запросов из одного запроса пользователя
- Подбора оптимальных весов для гибридного поиска
- Выбора стратегии поиска (конкатенация запросов, раздельный поиск)
- Дружелюбного общения с пользователем и задания уточняющих вопросов
- **LLM-as-a-Judge** для оценки качества ответов

## 🏗️ Архитектура

```
agentic_rag/
├── agents/
│   ├── __init__.py
│   ├── query_generator.py      # Генерация поисковых запросов
│   ├── search_agent.py         # Агент поиска с Tool Calling
│   └── response_agent.py       # Агент формирования ответов
├── tools/
│   ├── __init__.py
│   └── search_tool.py          # Инструмент поиска в базе знаний
├── prompts/
│   ├── __init__.py
│   ├── system_prompt.py        # Системный промпт
│   └── query_generation.py     # Промпты для генерации запросов
├── config.py                   # Конфигурация проекта
├── main.py                     # Точка входа
├── benchmark.py                # Тестирование качества + LLM Judge
├── llm_judge.py                # LLM-as-a-Judge для оценки ответов
├── test_agent.py               # Юнит тесты
└── logs/                       # Логи работы
```

## 🚀 Быстрый старт

### Установка зависимостей

```bash
cd agentic_rag
pip install -r requirements.txt
```

### Настройка окружения

Создайте файл `.env`:

```env
# RouterAI API
ROUTERAI_API_KEY=sk-...
ROUTERAI_BASE_URL=https://routerai.ru/api/v1

# Qdrant
QDRANT_HOST=localhost
QDRANT_PORT=6333
COLLECTION_NAME=BASHKIR_ENERGO_PERPLEXITY

# Embedding
EMBEDDING_MODEL=perplexity/pplx-embed-v1-4b
EMBEDDING_DIM=2560

# LLM
DEFAULT_LLM_MODEL=qwen/qwen3.5-flash-02-23

# Поиск
RETRIEVE_PREF_WEIGHT=0.4
RETRIEVE_HYPE_WEIGHT=0.3
RETRIEVE_LEXICAL_WEIGHT=0.2
RETRIEVE_CONTEXTUAL_WEIGHT=0.1
```

### Запуск

```bash
# Тестовый запуск
python main.py "Как подать заявку на подключение?"

# Запуск benchmark
python benchmark.py

# Запуск тестов
python test_agent.py
```

## 📊 Benchmark

### Метрики качества

**Традиционные:**
- Время выполнения (retrieval, generation, total)
- Количество поисковых запросов
- Количество источников

**LLM-as-a-Judge (оценка 1-5):**
- **Relevance** — релевантность ответа вопросу
- **Completeness** — полнота раскрытия темы
- **Helpfulness** — полезность для пользователя
- **Clarity** — ясность изложения
- **Hallucination Risk** — риск галлюцинаций (5 = низкий риск)

### Запуск benchmark

```bash
# С LLM Judge оценкой (по умолчанию)
python benchmark.py --use-default --output results/

# Без LLM Judge (быстрее)
python benchmark.py --use-default --no-llm-judge

# С кастомными примерами
python benchmark.py --samples tests/benchmark_samples.json
```

### Пример результатов LLM Judge:

```
🤖 LLM JUDGE ОЦЕНКИ:
  Оценено ответов: 5
  📌 Relevance (релевантность): 5.00 / 5
  📋 Completeness (полнота): 4.40 / 5
  ⚠️ Hallucination Risk (1=высокий, 5=низкий): 3.60 / 5
  🎯 Общая оценка LLM: 4.33 / 5
```

### Файлы результатов:
- `results/results_*.csv` — детальные результаты по каждому запросу
- `results/stats_*.json` — сводная статистика

## 🔧 Конфигурация

### Веса поиска

LLM может автоматически подбирать веса для:
- `pref_weight` - семантический вектор (summary + content)
- `hype_weight` - семантический вектор (hypothetical questions)
- `lexical_weight` - BM25 (токенизированный текст)
- `contextual_weight` - семантический вектор (соседние чанки)

### Стратегии генерации запросов

1. **Single Query** - один точный запрос
2. **Multi Query** - несколько запросов (2-3) с конкатенацией
3. **Clarification** - запрос уточняющих вопросов у пользователя

## 📝 Логирование

Все запросы логируются в `logs/`:
- `agent_{date}.log` - логи работы агентов
- `search_{date}.log` - логи поиска
- `errors_{date}.log` - ошибки

## 📄 Лицензия

Внутренний проект для Башкирэнерго
