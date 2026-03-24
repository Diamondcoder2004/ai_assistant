# Быстрый старт Agentic RAG

## 1. Установка

```bash
cd agentic_rag
pip install -r requirements.txt
```

## 2. Настройка

Скопируйте `.env.example` в `.env` и заполните:

```bash
cp .env.example .env
```

Заполните `.env`:
```env
ROUTERAI_API_KEY=sk-ваш-ключ
QDRANT_HOST=localhost
QDRANT_PORT=6333
COLLECTION_NAME=BASHKIR_ENERGO_PERPLEXITY
```

## 3. Запуск

### Интерактивный режим

```bash
python main.py
```

### Одноразовый запрос

```bash
python main.py "Как подать заявку на подключение?"
```

### С подробным выводом

```bash
python main.py "Как подать заявку?" --verbose
```

### С категорией клиента

```bash
python main.py "Сколько стоит подключение?" --category "юридическое лицо"
```

## 4. Тесты

```bash
python tests/test_agent.py
```

Или с pytest:

```bash
pytest tests/test_agent.py -v
```

## 5. Benchmark

### С дефолтными примерами

```bash
python benchmark.py --use-default --output results/
```

### С custom примерами

```bash
python benchmark.py --samples tests/benchmark_samples.json
```

## 6. Проверка работы

### Проверка подключения к Qdrant

```python
from tools.search_tool import SearchTool

tool = SearchTool()
tool.load()
print(f"Загружено документов: {len(tool.documents)}")
```

### Проверка генерации запросов

```python
from agents.query_generator import QueryGeneratorAgent

agent = QueryGeneratorAgent()
result = agent.generate("Как подать заявку?")

print(f"Запросы: {[q['text'] for q in result.queries]}")
print(f"Веса: {result.search_params}")
```

### Проверка поиска

```python
from tools.search_tool import SearchTool, SearchRequest

tool = SearchTool()
tool.load()

request = SearchRequest(
    query="подать заявку на подключение",
    k=5,
    pref_weight=0.5,
    hype_weight=0.2,
    lexical_weight=0.2,
    contextual_weight=0.1
)

results = tool.search(request)
print(f"Найдено: {len(results)}")
for r in results:
    print(f"  - {r.filename} | {r.score_hybrid:.3f}")
```

## 7. Логи

Логи сохраняются в `logs/`:

```bash
# Просмотр последних записей
tail -f logs/agent_*.log
```

## 8. Структура проекта

```
agentic_rag/
├── agents/           # Агенты (QueryGenerator, Search, Response)
├── tools/            # Инструменты (SearchTool)
├── prompts/          # Промпты
├── tests/            # Тесты
├── docs/             # Документация
├── logs/             # Логи
├── results/          # Результаты benchmark
├── config.py         # Конфигурация
├── main.py           # Точка входа
├── benchmark.py      # Benchmark
└── requirements.txt  # Зависимости
```

## 9. Примеры запросов

### Физическое лицо

```
Как подать заявку на подключение?
Какие документы нужны для участка?
Сколько стоит подключение для физического лица?
Что делать если отключили свет?
```

### Юридическое лицо

```
Сколько стоит подключение для юридического лица?
Как получить технические условия?
Что такое акт разграничения?
Как изменить категорию потребителя?
```

## 10. Отладка

### Включить подробное логирование

```python
import logging
logging.getLogger().setLevel(logging.DEBUG)
```

### Использовать флаг --verbose

```bash
python main.py "вопрос" --verbose
```

## 11. Частые проблемы

### Ошибка подключения к Qdrant

```
Проверьте:
- Qdrant запущен (docker ps)
- Хост и порт в .env правильные
- Коллекция существует
```

### Ошибка API ключа

```
Проверьте:
- ROUTERAI_API_KEY в .env
- Ключ действителен
- Баланс не нулевой
```

### Мало результатов поиска

```
Решения:
- Увеличьте k в search_params
- Измените веса (больше lexical)
- Используйте стратегию "separate"
```

## 12. Следующие шаги

1. Изучите `docs/ARCHITECTURE.md` для понимания архитектуры
2. Запустите benchmark для оценки качества
3. Настройте промпты под ваши нужды
4. Добавьте свои тестовые примеры
