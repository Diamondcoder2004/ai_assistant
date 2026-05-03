# Дизайн-документ: Перестройка базы знаний для повышения точности бенчмарка

## Дата
2026-05-02

## Статус
Draft

## 1. Проблема (Problem Statement)

Текущая точность AI-ассистента по бенчмарку составляет **39%** (308 вопросов, judge: DeepSeek-v3.2):
- ЛК (Личный кабинет): 54.7%
- ДУ (Дополнительные услуги): 32.8%
- ТПП (Технологическое присоединение): 36.7%

Основные паттерны ошибок:
1. Терминология и классификации (36.7%) — путаница между ФЛ/ИП/ЮЛ, классами напряжения
2. Стоимость и расчеты (22.9%) — неверные тарифы, границы льгот
3. Мощностные и категорийные лимиты (21.8%) — неправильные границы по мощности
4. Ставки льгот (11.7%) — неверные коэффициенты

Причина: текущая база знаний недостаточно структурирована для точного ретривала процедурной и нормативной информации. Необходима перестройка с учетом множественных коллекций Qdrant, обогащенной метадаты и стратегии чанкинга.

## 2. Ограничения (Constraints)

- **Prompts frozen**: стиль промптов в `backend/prompts/` не изменяется
- **Существующая инфраструктура**: используем текущий `llm_chunking.py` (RouterAI/qwen3.5-flash для обогащения)
- **Кодировка**: весь кириллический контент в UTF-8
- **BM25 нормализация**: `score / max_score` (классическая), без tanh/softmax
- **Веса поиска**: PREF(0.4) + HYPE(0.3) + LEXICAL(0.2) + CONTEXTUAL(0.1) = 1.0
- **Backend entrypoint**: `api.api:app`
- **Множественные коллекции Qdrant**: требуется разделение документов по типам
- **Breadcrumbs в метадате**: обязательное требование для отслеживания контекста
- **Neighbor chunk IDs**: добавляем prev/next для контекстного ретривала
- **Parent-child чанкинг**: отложен до Phase 2 (необходимость не доказана)
- **PDF парсинг**: автоматизировать вместо ручного копирования в DeepSeek

## 3. Выбранный подход (Approach)

**Решение: Множественные коллекции Qdrant с обогащенной метадатой**

Вместо единой коллекции создаем 2 специализированные коллекции, разделяющие нормативную и операционную информацию. Это повышает точность ретривала, так как запросы к нормативной базе (тарифы, льготы, законодательство) и операционной (пошаговые инструкции, FAQ) имеют разную семантику и требуют разного контекста.

**Почему не единая коллекция?**
- В единой коллекции нормативные документы "зашумляют" операционные запросы и наоборот
- Разделение позволяет настроить гибридный поиск с разными весами под тип документа
- Упрощает обновление: можно перестраивать операционную коллекцию без затрагивания нормативной базы

**Почему откладываем parent-child чанкинг?**
- Добавляет сложность в индексацию и ретривал
- Neighbor chunk IDs (prev/next) решают 80% проблемы фрагментации контекста
- Внедрим parent-child, если бенчмарк покажет фрагментацию контекста после Phase 1

## 4. Архитектура (Architecture)

```
Источники контента:
├── Нормативные документы (PDF, DOCX)
│   └── Постановления, правила, законы
├── Операционные документы (PDF, DOCX, Markdown)
│   ├── FAQ
│   ├── Этапы процедур
│   ├── Инфоматериалы
│   └── Инструкции
│
Процессинг:
├── PDF Parser (RouterAI API + PyMuPDF fallback)
├── Markdown Splitter (MarkdownHeaderTextSplitter + RecursiveCharacterTextSplitter)
├── LLM Enrichment (RouterAI/qwen3.5-flash)
│   ├── chunk_summary
│   ├── hypothetical_questions
│   ├── keywords
│   ├── entities
│   ├── category
│   └── breadcrumbs
└── Metadata Injector
    ├── neighbor_chunk_ids (prev, next)
    ├── collection_name
    ├── document_type
    ├── power_range
    └── client_type

Хранение:
├── Qdrant Collection: normative_documents
│   ├── Нормативные чанки с полной метадатой
│   └── Отдельные веса для гибридного поиска
└── Qdrant Collection: operational_content
    ├── Операционные чанки с полной метадатой
    └── Отдельные веса для гибридного поиска

Поиск (Runtime):
├── QueryClassifier (на основе категории и ключевых слов)
│   ├── Нормативный запрос → normative_documents
│   └── Операционный запрос → operational_content
├── Hybrid Search (4 компонента × BM25)
│   ├── PREF(0.4) + HYPE(0.3) + LEXICAL(0.2) + CONTEXTUAL(0.1)
│   └── Нормализация: score / max_score
└── ResponseAgent (LLM + sources)
```

## 5. Компоненты (Components)

### 5.1. PDF Parser
**Назначение**: Извлечение структурированного текста из PDF-файлов с сайта bashkirenergo.ru

**Стратегия**:
- **Primary**: RouterAI API для структурированного извлечения (заголовки, секции, таблицы)
- **Fallback**: PyMuPDF для извлечения сырого текста, когда RouterAI недоступен или стоимость критична

**Почему RouterAI?**
- Уже интегрирован в `llm_chunking.py`
- Умеет извлекать структуру (breadcrumbs, заголовки)
- Поддерживает кириллицу

**Почему PyMuPDF fallback?**
- Быстрее и дешевле для простых документов
- Не требует API-ключей
- Работает оффлайн

### 5.2. Two-Stage Chunking Pipeline (исправлено — v2)

**Stage 1 — Markdown Splitter (Mardown_splitter.py) — физический пре-сплит**

**Назначение**: Разделить документ на куски, которые влезают в 80k токен-лимит LLM. Это грубый сплит.

**Стратегия**:
- **MarkdownHeaderTextSplitter**: для структурированных markdown-документов (сохраняет иерархию заголовков)
- **RecursiveCharacterTextSplitter**: fallback для неструктурированного текста
- Разделитель между чанками: `\n\n---CHUNK---\n\n`

**Параметры (НЕ менять — это правильные значения)**:
- MIN_CHUNK_SIZE: 1000 символов (избегаем фрагментации)
- MAX_CHUNK_SIZE: 20 000 символов (технический лимит — 80k токенов LLM)
- chunk_overlap: 0 (не нужен — LLM перераспределяет чанки в Stage 2)

**Stage 2 — LLM Enrichment (llm_chunking.py) — смысловой чанкинг**

**Назначение**: LLM разбивает каждый pre-chunk на атомарные смысловые фрагменты + генерирует метадату. Это настоящий чанкинг.

**Как работает**:
1. Читает pre-chunks из Stage 1 по разделителю `---CHUNK---`
2. Отправляет каждый pre-chunk в LLM (qwen3.5-flash, 80k лимит)
3. LLM разбивает на атомарные фрагменты и генерирует метадату
4. Каждый фрагмент: `chunk_id = {parent_md5}_p{idx}` (1–N на pre-chunk)
5. Output: JSON-файлы с полной метадатой для Qdrant

**Размеры Stage 2 чанков**: определяются LLM семантически (обычно 500–5000 символов)

### 5.3. LLM Enrichment (Metadata Generator)
**Назначение**: Обогащение чанков метадатой для улучшения поиска

**Существующие поля (сохраняем)**:
- `chunk_id`
- `source_file`
- `chunk_content`
- `breadcrumbs` (структурированный путь)
- `chunk_summary`
- `hypothetical_questions`
- `keywords`
- `entities`
- `category` (ЛК / ДУ / ТПП)

**Новые поля**:
- `neighbor_chunk_ids`: `{ "prev": "chunk_001", "next": "chunk_003" }`
- `collection_name`: `"normative_documents"` или `"operational_content"`
- `document_type`: `"regulation"`, `"faq"`, `"stage_description"`, `"infomaterial"`, `"instruction"`
- `power_range`: `"<15kW"`, `"15-150kW"`, `"150-670kW"`, `">670kW"`, `"any"` (для ТПП)
- `client_type`: `"ФЛ"`, `"ИП"`, `"ЮЛ"`, `"any"`

### 5.4. Query Classifier
**Назначение**: Определение типа запроса для выбора коллекции

**Логика**:
- Анализирует запрос на наличие ключевых слов нормативного характера ("тариф", "постановление", "льгота", "ставка", "закон")
- Анализирует запрос на операционные ключевые слова ("как подать", "этап", "документ", "срок", "стоимость")
- При неопределенности: ищет в обеих коллекциях, объединяет результаты

### 5.5. Hybrid Search (Runtime)
**Назначение**: Поиск по чанкам с учетом множественных коллекций

**Изменения**:
- Добавить параметр `collection` в API поиска
- SearchAgent должен выбирать коллекцию на основе Query Classifier
- Возможность поиска по обеим коллекциям с объединением результатов

## 6. Поток данных (Data Flow)

### 6.1. Инжестия нового документа
```
PDF/DOCX/Markdown файл
    ↓
PDF Parser (RouterAI / PyMuPDF)
    ↓
Сырой текст + структура (заголовки)
    ↓
Markdown Splitter (MarkdownHeaderTextSplitter / RecursiveCharacterTextSplitter)
    ↓
Список чанков (chunk_id, content, breadcrumbs)
    ↓
LLM Enrichment (RouterAI API)
    ↓
Чанки с обогащенной метадатой
    ↓
Metadata Injector (neighbor_chunk_ids, collection_name, document_type, power_range, client_type)
    ↓
Qdrant (соответствующая коллекция: normative_documents или operational_content)
```

### 6.2. Обработка пользовательского запроса (Runtime)
```
User Query
    ↓
Query Classifier (ЛК/ДУ/ТПП + нормативный/операционный)
    ↓
SearchAgent (генерация поисковых запросов)
    ↓
Hybrid Search по выбранной коллекции (или обеим)
    ↓
Ранжирование результатов (PREF + HYPE + LEXICAL + CONTEXTUAL)
    ↓
ResponseAgent (LLM-ответ с источниками)
    ↓
User Response
```

## 7. Обработка ошибок (Error Handling)

### 7.1. PDF Parsing Failures
- **RouterAI timeout / error**: Автоматический fallback на PyMuPDF
- **PyMuPDF fails**: Логирование ошибки, документ помечается как "needs_manual_review"
- **Структура не распознана**: Fallback на RecursiveCharacterTextSplitter без заголовков

### 7.2. LLM Enrichment Failures
- **RouterAI API error**: Retry с exponential backoff (3 попытки)
- **JSON parse error**: Используем `repair_json.py` для восстановления
- **Partial enrichment**: Чанк помечается как "partial_metadata", инжестится без необязательных полей

### 7.3. Qdrant Ingestion Failures
- **Collection not found**: Автосоздание коллекции с правильной схемой
- **Duplicate chunk_id**: Upsert вместо insert
- **Vector dimension mismatch**: Логирование, блокировка инжестии до фикса конфигурации

### 7.4. Runtime Search Failures
- **Query Classifier неопределен**: Поиск по обеим коллекциям с объединением
- **Collection пустая**: Поиск по альтернативной коллекции с warning-логом
- **Zero results**: Расширение поиска (увеличение top_k, уменьшение threshold)

## 8. Стратегия тестирования (Testing Strategy)

### 8.1. Unit Tests
- **PDF Parser**: Тесты на извлечение текста из образцов PDF (проверка сохранения структуры)
- **Markdown Splitter**: Тесты на корректность разбиения, сохранение заголовков, размер чанков
- **LLM Enrichment**: Mock-тесты на генерацию метадаты (проверка JSON-структуры)
- **Metadata Injector**: Тесты на корректность neighbor_chunk_ids и валидацию полей

### 8.2. Integration Tests
- **End-to-end ingestion**: PDF → чанки → Qdrant → retrieve
- **Multi-collection search**: Проверка выбора коллекции и объединения результатов
- **Hybrid search weights**: Проверка, что веса суммируются в 1.0

### 8.3. Benchmark Regression Tests
- **Baseline**: 39% (текущий бенчмарк)
- **Target**: >70% (минимально приемлемый уровень для продакшена)
- **Phase 1 target**: >50% (улучшение ретривала за счет коллекций и метадаты)
- **Phase 2 target**: >65% (добавление PDF-контента и улучшение чанкинга)
- **Phase 3 target**: >75% (итерации на основе анализа ошибок)

### 8.4. Validation Criteria
После каждой фазы запускаем полный бенчмарк (308 вопросов) и анализируем:
- Общую точность
- Точность по категориям (ЛК, ДУ, ТПП)
- Распределение ошибок (терминология, стоимость, мощность, льготы)
- Количество "hallucination" ошибок

## 9. Этапы выполнения (Execution Phases)

### Phase 1: Foundation & Domain Language
- [ ] Извлечь ubiquitous language из benchmark dataset
- [ ] Создать `UBIQUITOUS_LANGUAGE.md` с глоссарием терминов
- [ ] Спроектировать схему коллекций Qdrant (поля, индексы, векторные параметры)
- [ ] Определить финальную спецификацию чанкинга (размер, overlap, splitters)
- [ ] Создать спецификацию метадаты (все поля, типы, обязательность)
- [ ] Обновить `knowledge-base-schema.md` с новой архитектурой

### Phase 2: Content Ingestion
- [ ] Добавить PDF-файлы от пользователя в проект
- [ ] Реализовать PDF Parser (RouterAI + PyMuPDF fallback)
- [ ] Обновить Markdown Splitter с новыми параметрами
- [ ] Обновить LLM Enrichment с новыми полями метадаты
- [ ] Реализовать Metadata Injector (neighbor_chunk_ids, collection_name, и т.д.)
- [ ] Создать скрипт массовой инжестии (batch ingestion)
- [ ] Запустить инжестию в Qdrant (обе коллекции)

### Phase 3: Validation & Iteration
- [ ] Обновить SearchAgent для работы с множественными коллекциями
- [ ] Реализовать Query Classifier
- [ ] Запустить бенчмарк
- [ ] Анализировать результаты
- [ ] Итерировать на основе ошибок (корректировка чанкинга, весов, метадаты)

## 10. Открытые вопросы (Open Questions)

1. **Файлы PDF**: Ожидаем добавления PDF-файлов от пользователя для начала Phase 2
2. **Parent-child чанкинг**: Будет принято решение после результатов бенчмарка Phase 1
3. **Размер вектора**: Необходимо подтвердить размерность embedding model (pplx-embed-v1-4b)
4. **Qdrant версия**: Необходимо проверить поддержку множественных коллекций в текущей версии Qdrant (port 6333)
5. **Дублирование контента**: Если один документ содержит и нормативную, и операционную информацию — инжестим в обе коллекции или разделяем?

## 11. Файлы и директории

### Новые файлы (будут созданы)
- `UBIQUITOUS_LANGUAGE.md` — доменный глоссарий
- `docs/specs/chunking-strategy.md` — спецификация чанкинга
- `docs/specs/qdrant-collections-schema.md` — схема коллекций Qdrant
- `backend/chunking/pdf_parser.py` — парсер PDF
- `backend/chunking/metadata_injector.py` — инжектор метадаты
- `backend/chunking/batch_ingest.py` — скрипт массовой инжестии

### Модифицируемые файлы
- `backend/chunking/Mardown_splitter.py` — обновить параметры чанкинга
- `backend/chunking/llm_chunking.py` — добавить новые поля метадаты
- `backend/agents/search_agent.py` — добавить выбор коллекции
- `docs/diagrams/knowledge-base-schema.drawio` — обновить диаграмму
- `docs/diagrams/knowledge-base-schema.md` — обновить документацию

## 12. Метрики успеха

- **Phase 1**: Документация готова, схема коллекций утверждена, ubiquitous language извлечен
- **Phase 2**: Все PDF-файлы спарсены, проинжестированы в Qdrant, обе коллекции содержат >1000 чанков каждая
- **Phase 3**: Бенчмарк показывает улучшение точности минимум на 10% относительно baseline (39% → >49%)
- **Target**: Итоговая точность >70% после всех итераций
