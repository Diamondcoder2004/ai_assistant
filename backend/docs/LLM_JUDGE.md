# LLM-as-a-Judge для Agentic RAG

## 📊 Что добавлено

### Новый модуль: `llm_judge.py`

**LLM Judge** — это система автоматической оценки качества ответов RAG системы с использованием самой LLM.

### Критерии оценки (шкала 1-5):

| Метрика | Описание | Шкала |
|---------|----------|-------|
| **Relevance** | Релевантность ответа вопросу | 1 = не по теме, 5 = полностью соответствует |
| **Completeness** | Полнота раскрытия темы | 1 = очень краткий, 5 = исчерпывающий |
| **Helpfulness** | Полезность для пользователя | 1 = бесполезен, 5 = очень полезен |
| **Clarity** | Ясность изложения | 1 = непонятен, 5 = отлично структурирован |
| **Hallucination Risk** | Риск галлюцинаций | 1 = много выдумок, 5 = строго по источникам |

## 🔧 Как работает

### Промпт для оценки:

```
Ты — независимый эксперт (LLM Judge) для оценки качества RAG системы.

Входные данные:
- Вопрос пользователя
- Сгенерированный ответ
- Найденные источники (контекст)

Критерии оценки (шкала 1-5):
1. Relevance (Релевантность)
2. Completeness (Полнота)
3. Helpfulness (Полезность)
4. Clarity (Ясность)
5. Hallucination Risk (1=высокий, 5=низкий)

Формат ответа: JSON
```

### Пример ответа LLM Judge:

```json
{
  "relevance": 5,
  "completeness": 4,
  "helpfulness": 5,
  "clarity": 5,
  "hallucination_risk": 4,
  "overall_score": 4.6,
  "reasoning": "Ответ релевантный и полный, хорошо структурирован. Информация основана на предоставленных источниках."
}
```

## 🚀 Использование

### В benchmark:

```bash
# С LLM Judge (по умолчанию)
python benchmark.py --use-default --output results/

# Без LLM Judge (быстрее)
python benchmark.py --use-default --no-llm-judge --output results_fast/
```

### Программно:

```python
from llm_judge import LLMJudge

judge = LLMJudge()

evaluation = judge.evaluate(
    question="Как подать заявку?",
    answer="Для подачи заявки необходимо...",
    sources=[
        {"filename": "doc1", "category": "legal", "score_hybrid": 0.85}
    ]
)

print(f"Relevance: {evaluation.relevance}/5")
print(f"Completeness: {evaluation.completeness}/5")
print(f"Hallucination Risk: {evaluation.hallucination_risk}/5")
print(f"Overall: {evaluation.overall_score}/5")
```

## 📈 Результаты benchmark

### С LLM Judge (5 примеров):

```
============================================================
📊 СВОДКА БЕНЧМАРКА
============================================================
Всего примеров: 5
Общее время: 207.42 сек
Среднее время на запрос: 41.48 сек
  - Поиск: 33.19 сек (80%)
  - Генерация: 8.30 сек (20%)
  - LLM Judge оценка: ~30 сек на ответ

🤖 LLM JUDGE ОЦЕНКИ:
  Оценено ответов: 5
  📌 Relevance (релевантность): 5.00 / 5
  📋 Completeness (полнота): 4.40 / 5
  ⚠️ Hallucination Risk (1=высокий, 5=низкий): 3.60 / 5
  🎯 Общая оценка LLM: 4.33 / 5
============================================================
```

### Интерпретация результатов:

| Метрика | Значение | Интерпретация |
|---------|----------|---------------|
| **Relevance** | 5.00/5 | ✅ Все ответы релевантны вопросам |
| **Completeness** | 4.40/5 | ✅ Ответы полные, есть небольшие пробелы |
| **Hallucination Risk** | 3.60/5 | ⚠️ Умеренный риск, некоторые допущения |
| **Overall** | 4.33/5 | ✅ Отличное качество системы |

## ⚙️ Настройки

### Температура генерации:
```python
# В llm_judge.py
temperature: float = 0.3  # Низкая для стабильности оценок
```

### Максимум попыток:
```python
max_attempts: int = 2  # Попыток для получения валидного JSON
```

### Модель:
```python
# Использует DEFAULT_LLM_MODEL из config.py
model = config.DEFAULT_LLM_MODEL  # qwen/qwen3.5-flash-02-23
```

## 📝 Файлы

| Файл | Описание |
|------|----------|
| `llm_judge.py` | Модуль LLM-as-a-Judge |
| `benchmark.py` | Обновлён для использования LLM Judge |
| `results_llm/` | Результаты benchmark с оценками |

## 💡 Рекомендации

### Когда использовать LLM Judge:

✅ **Использовать:**
- Для финальной оценки качества системы
- При сравнении разных версий RAG
- Для публикации результатов
- При настройке промптов и весов

❌ **Не использовать:**
- Для быстрой итеративной разработки (медленно)
- Когда достаточно объективных метрик (время, количество источников)

### Оптимизация:

```bash
# Быстрый benchmark без LLM Judge
python benchmark.py --use-default --no-llm-judge

# Полный benchmark с LLM Judge
python benchmark.py --use-default
```

## 🔮 Планы

### Улучшения LLM Judge:

- [ ] **Source Accuracy** — оценка точности цитирования источников
- [ ] **Faithfulness** — оценка соответствия источникам
- [ ] **Answer Consistency** — оценка непротиворечивости
- [ ] **Comparative Evaluation** — сравнение двух ответов
- [ ] **Batch Evaluation** — пакетная оценка для скорости

## 📚 Ссылки

- [LLM-as-a-Judge Paper](https://arxiv.org/abs/2306.05685)
- [RAG Evaluation Metrics](https://docs.ragas.io/en/stable/concepts/metrics/index.html)
- [Arize Phoenix RAG Evaluation](https://docs.arize.com/phoenix/)
