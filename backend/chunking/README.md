# Chunking Pipeline — Bashkirenergo AI Assistant

## Пайплайн (v5)

```
Markdown файлы (.md)
   ├── new_data/source/markdown_data/       (бывшие PDF)
   └── new_data/source/operational/html_pages/  (бывшие HTML)
       │
       ▼
┌──────────────────────────────────────────────┐
│ STAGE 1: Pre-split (pre_split_for_llm.py)    │
│   - Файлы ≤50k токенов → копируются as-is    │
│   - Файлы >50k токенов → делятся по заголов- │
│     кам на _partN.md файлы                   │
│   - Удаляет markdown-изображения             │
│   - Выход: markdown_data_split/              │
│            html_pages_split/                 │
│   - Лимит: 50,000 токенов на часть           │
└──────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────┐
│ STAGE 2: LLM Chunking (llm_chunking.py)      │
│   - ВЕСЬ файл (или _partN.md) отправляется   │
│     LLM как ЕДИНОЕ ЦЕЛОЕ                     │
│   - LLM САМ делит на атомарные смысловые     │
│     чанки и возвращает массив JSON           │
│   - chunk_content сохраняется СЛОВО В СЛОВО  │
│   - Средний размер чанка ~1000 токенов       │
│   - Модель: qwen/qwen3.5-flash-02-23         │
│   - Выход: enriched_chunks/{normative|       │
│     operational}/ — отдельные JSON файлы     │
└──────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────┐
│ STAGE 3: Qdrant Ingestion                    │
│   ingest_qdrant_contextual.py                │
│   - Читает JSON из enriched_chunks/          │
│   - Генерирует эмбеддинги                    │
│   - Upsert в Qdrant коллекции                │
└──────────────────────────────────────────────┘
```

## Ключевые принципы

### STAGE 1: Pre-split
- **Цель:** уместить файл в контекстное окно LLM (50k токенов)
- **Метод:** разбиение по markdown-заголовкам (h1-h5)
- **НЕ делает:** НЕ добавляет `---CHUNK---` разделители
- **НЕ делает:** НЕ гарантирует семантические границы — это задача Stage 2

### STAGE 2: LLM Chunking
- **Цель:** атомарные смысловые чанки с метаданными
- **Принцип:** LLM получает ВЕСЬ текст файла и САМ решает где границы чанков
- **НЕЛЬЗЯ:** резать текст ДО отправки LLM (никакого split_into_sections)
- **chunk_content:** сохраняется СЛОВО В СЛОВО, без сокращений
- **Средний размер:** ~1000 токенов (~4000 символов)
- **Неделимые блоки:** если статья/раздел целостный — оставлять целиком

## Формат выходных чанков

Каждый JSON-файл содержит один чанк со следующими полями:

### Общие поля (все чанки)
| Поле | Тип | Описание |
|------|-----|----------|
| `chunk_id` | string | `{parent_md5}_p{idx}` — уникальный ID |
| `source_file` | string | **Чистое название документа** (без `_partN`, без `.md`) |
| `chunk_content` | string | Полный текст чанка, слово в слово |
| `breadcrumbs` | string | Путь заголовков: "Глава X > Статья Y > Пункт Z" |
| `chunk_summary` | string | Краткое описание (2-4 предложения) |
| `hypothetical_questions` | array | 4-6 конкретных поисковых вопросов клиента |
| `keywords` | array | 5-10 ключевых фраз |
| `entities` | array | 3-8 именованных сущностей |
| `category` | string | `ТПП` / `ДУ` / `ЛК` |
| `collection_name` | string | `normative_documents` / `operational_content` |
| `document_type` | string | `regulation` / `faq` / `stage_description` / `infomaterial` / `instruction` |
| `power_range` | string | `<15kW` / `15-150kW` / `150-670kW` / `>670kW` / `any` |
| `client_type` | string | `ФЛ` / `ИП` / `ЮЛ` / `any` |

### source_file — ВАЖНО
Поле `source_file` используется на frontend для отображения источника.
**Должно содержать только название документа**, без:
- ❌ `_part1`, `_part2` суффиксов
- ❌ `.md` расширений
- ❌ полных путей

Примеры:
- ✅ `"gkt-rb-306-plata-2026"`
- ✅ `"passport-tp-do-15kvt"`
- ❌ `"gkt-rb-306-plata-2026_part1.md"`
- ❌ `"gkt-rb-306-plata-2026_part1"`

## Запуск

```bash
cd backend

# Stage 1: Pre-split
python chunking/pre_split_for_llm.py

# Stage 2: LLM Chunking
python chunking/llm_chunking.py

# Stage 3: Qdrant Ingestion
python qdrant_ingest/ingest_qdrant_contextual.py
```

## Конфигурация

| Параметр | Значение | Где |
|----------|----------|-----|
| `MAX_TOKENS` (pre-split) | 50,000 | `pre_split_for_llm.py` |
| `CHUNKING_LLM_MODEL` | `qwen/qwen3.5-flash-02-23` | `.env` |
| `MAX_OUTPUT_TOKENS` | 80,000 | `llm_chunking.py` |
| `MAX_CONCURRENT_REQUESTS` | 8 | `llm_chunking.py` |
| `TEMPERATURE` | 0.15 | `llm_chunking.py` |
| `MAX_RETRIES` | 5 | `llm_chunking.py` |

## Маппинг файлов

Файлы маппятся на метаданные через словари в `llm_chunking.py`:
- `NORMATIVE_FILES` — нормативные документы → `normative_documents`
- `OPERATIONAL_MD_FILES` — операционные документы → `operational_content`
- `HTML_METADATA` — загружается из `new_data/source/operational/metadata.json`

При добавлении нового файла — добавить запись в соответствующий словарь.

## Ошибки и восстановление

- **Failed chunks:** логируются в `logs/failed_chunks_v5.json`
- **Raw responses:** сохраняются в `raw_responses_v5/` для отладки
- **Resume:** уже обработанные файлы пропускаются (проверка по existing JSON)
- **JSON repair:** при ошибке парсинга — автоматический repair с regex

## История версий

| Версия | Дата | Изменения |
|--------|------|-----------|
| v1 | 2026-05-02 | Одностадийный чанкинг с overlap |
| v2 | 2026-05-03 | Двухстадийный: Mardown_splitter + LLM |
| v3 | 2026-05-04 | pre_split_for_llm.py, deepseek-v4-flash |
| v4 | 2026-05-12 | split_into_sections (ОШИБОЧНО — резало по заголовкам) |
| v5 | 2026-05-12 | LLM сам делит на чанки, 50k лимит, новые поля |
