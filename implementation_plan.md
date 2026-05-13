# Рефакторинг llm_chunking.py — пайплайн для new_data

## Цель

Переработать `llm_chunking.py` для обработки всех markdown-файлов из `new_data/source/`. Пайплайн: **чтение → сплит крупных файлов (>100k токенов) → LLM-обогащение через deepseek-v4-flash с JSON output → запись в отдельные папки** (normative / operational).

## Входные данные

### Структура `new_data/source/`

```
new_data/source/
├── markdown_data/         ← 21 файл .md (бывшие PDF, нормативка + operational)
│   ├── 1. ФЗ 35.md            (963 KB, ~240k токенов — НУЖНО ДЕЛИТЬ)
│   ├── 2. 861.md               (1.1 MB, ~300k токенов — НУЖНО ДЕЛИТЬ)
│   ├── 9. 442.md               (2.2 MB, ~560k токенов — НУЖНО ДЕЛИТЬ)
│   ├── 1178-cenoobrazovanie.md (334 KB)
│   ├── 186-minenergo.md        (200 KB)
│   ├── passport-*.md           (11 файлов, 24-138 KB)
│   ├── pamyatka-*.md           (2 файла, 15-21 KB)
│   └── faq-kt-tpp-2026.md     (58 KB)
│
├── normative/             ← 7 PDF (оригиналы, НЕ трогаем)
│
└── operational/
    ├── html_pages/        ← 18 файлов .md (бывшие HTML-страницы сайта)
    ├── faq/               ← 1 CSV
    ├── informational/     ← 12 PDF (паспорта, памятки — оригиналы)
    ├── instructions/      ← 2 PDF (инструкции — оригиналы)
    └── metadata.json      ← метаданные html_pages и instructions
```

### Источники и категории

| Источник | Документы | Категория | source_origin |
|----------|-----------|-----------|---------------|
| `markdown_data/` (нормативка) | ФЗ 35, 861, 442, 1178, 186, 490_22, gkt-rb-306 | ТПП / Общая | `normative` |
| `markdown_data/` (operational) | passport-*, pamyatka-*, faq-kt-tpp, Инструкция ЛК, Инструкция самоподкл., Информ.письмо, Заявление ЮЛ, Док из сайта | ТПП / ЛК / ДУ | `operational` |
| `operational/html_pages/` | 18 .md файлов | ТПП / ДУ / ЛК | `operational` |

> [!IMPORTANT]
> **Файлы из `markdown_data/`** содержат как **нормативные** (законы, постановления), так и **операционные** документы. Нужно чётко разделить их. Ниже маппинг.

### Маппинг файлов `markdown_data/` → normative / operational

**Нормативные** (совпадают с PDF из `normative/`):

| Файл .md | PDF в `normative/` | category |
|----------|---------------------|----------|
| `1. ФЗ 35 (28.04.2025).md` | `35-fz-ob-elektroenergetike.pdf` | Общая |
| `2. 861 (28.04.2025).md` | `861-pravila-tp.pdf` | ТПП |
| `1178-cenoobrazovanie.md` | `1178-cenoobrazovanie.pdf` | ТПП |
| `186-minenergo-standarty-kachestva.md` | `186-minenergo-standarty-kachestva.pdf` | Общая |
| `4. 490_22 Методические указания.md` | `490-22-plata-za-tp.pdf` | ТПП |
| `9. 442 О ФУНКЦИОНИРОВАНИИ РОЗНИЧНЫХ РЫНКОВ.md` | `442-o-roznichnyh-rynkah.pdf` | Общая |
| `gkt-rb-306-plata-2026.md` | `gkt-rb-306-plata-2026.pdf` | ТПП |

**Операционные** (остальные из `markdown_data/`):

| Файл .md | category |
|----------|----------|
| `10. Инструкция по работе в ЛК...md` | ЛК |
| `7. Инструкция по самостоятельному подключению.md` | ТПП |
| `faq-kt-tpp-2026.md` | ТПП |
| `passport-*.md` (11 файлов) | ТПП |
| `pamyatka-*.md` (2 файла) | ТПП |

> [!NOTE]
> **ДУ-файлы** — только в `operational/html_pages/`: `katalog-du.md` и `dop-uslugi-pri-tp.md` (оба маленькие).  
> **ЛК-файлы** — `10. Инструкция по работе в ЛК.md` + ничего из html_pages явно ЛК (кроме косвенно).

---

## Proposed Changes

### Шаг 1: Markdown Splitter — предварительная разбивка крупных файлов

#### [MODIFY] [Mardown_splitter.py](file:///d:/ai_assistant/backend/chunking/Mardown_splitter.py)

Добавить **режим pre-split** — разбивка файлов >100k токенов на части перед LLM-обогащением:

- Новая функция `pre_split_large_files(input_dir, output_dir, max_tokens=100_000)`
- Использует `tiktoken` (cl100k_base) для подсчёта токенов
- Файлы ≤100k токенов — копируются as-is
- Файлы >100k токенов — разбиваются по заголовкам `smart_chunking()`, затем группируются в части ≤100k токенов
- Каждая часть сохраняется как `{basename}_part{N}.md`
- Выходная папка: `new_data/source/markdown_data_split/`

Это будет **отдельный скрипт** (`pre_split_for_llm.py`), чтобы не ломать существующий `Mardown_splitter.py`.

#### [NEW] [pre_split_for_llm.py](file:///d:/ai_assistant/backend/chunking/pre_split_for_llm.py)

Скрипт предварительной разбивки:
- Читает все .md из `new_data/source/markdown_data/` и `new_data/source/operational/html_pages/`
- Считает токены каждого файла
- Если >100k — делит через `smart_chunking()` из `Mardown_splitter.py`, группирует в части
- Записывает в `new_data/source/markdown_data_split/` и `new_data/source/html_pages_split/`

---

### Шаг 2: Переработка llm_chunking.py

#### [MODIFY] [llm_chunking.py](file:///d:/ai_assistant/backend/chunking/llm_chunking.py)

Ключевые изменения:

**1. Модель и JSON output:**
- `MODEL_NAME = "deepseek/deepseek-v4-flash"` (или какое точное имя на RouterAI)
- Включить `response_format={"type": "json_object"}` в вызове API
- Retry при невалидном JSON (до 5 попыток)

**2. Входные данные:**
- Читать из подготовленных split-папок
- Два прохода: `markdown_data_split/` (PDF-origin) и `html_pages_split/` (HTML-origin)

**3. Выходные папки:**
```
backend/chunking/enriched_chunks/
├── normative/     ← чанки из нормативных документов
└── operational/   ← чанки из операционных документов
```

**4. Новые поля в JSON-чанке:**
```json
{
  "chunk_content": "...",
  "breadcrumbs": "Глава 1 > Статья 3",
  "chunk_summary": "...",
  "hypothetical_questions": ["..."],
  "keywords": ["..."],
  "entities": ["..."],
  "category": "ТПП",           // ТПП | ДУ | ЛК | Общая
  "source_origin": "normative", // normative | operational
  "document_source": "pdf",     // pdf | html_page
  "source_file": "2. 861.md",
  "chunk_id": "abc123_p1"
}
```

**5. Маппинг категорий** — хардкодед dict в скрипте:

```python
FILE_METADATA = {
    # normative (из markdown_data, совпадают с PDF из normative/)
    "1. ФЗ 35 (28.04.2025).md": {"category": "Общая", "source_origin": "normative"},
    "2. 861 (28.04.2025).md": {"category": "ТПП", "source_origin": "normative"},
    "1178-cenoobrazovanie.md": {"category": "ТПП", "source_origin": "normative"},
    ...
    # operational (из markdown_data)
    "10. Инструкция по работе в ЛК...md": {"category": "ЛК", "source_origin": "operational"},
    ...
}
# html_pages берут metadata из operational/metadata.json
```

**6. Промпт** — полностью переписан:

> [!IMPORTANT]
> Ключевые требования к промпту:
> - **Без бесполезных вопросов** типа "Что написано в этом фрагменте" — только вопросы, помогающие **найти** этот чанк в поиске
> - Вопросы должны быть такими, какие **реальный клиент Башкирэнерго** задал бы в чат
> - Keywords — не абстрактные, а конкретные термины для поиска
> - Entities — законы, постановления, организации, конкретные числа (кВт, суммы)
> - Промпт различает `document_source: pdf` (нормативка, законы) vs `html_page` (операционные страницы сайта)

```
Ты эксперт по обработке документов в сфере электроэнергетики и технологического присоединения (ТП).

## Контекст документа
- Категория: {category} (ТПП / ДУ / ЛК / Общая)
- Тип источника: {document_source} (pdf — нормативный документ / html_page — страница сайта Башкирэнерго)
- Классификация: {source_origin} (normative — нормативная база / operational — операционный документ)
- Файл: {source_file}

## Исходный текст

{chunk_text}

## Задача

Раздели текст на атомарные, самодостаточные фрагменты и для каждого создай JSON-объект.

### Правила деления:
- По заголовкам, статьям, пунктам, логическим блокам
- Таблицы можно делить по строкам если они длинные
- Заявления и формы документов НЕ делить
- Каждый фрагмент должен быть понятен без остального текста

### Поля JSON-объекта:

1. `chunk_content` — полный текст фрагмента с исправленным Markdown
2. `breadcrumbs` — путь заголовков: "Глава X > Статья Y > Пункт Z"
3. `chunk_summary` — краткое описание (2-4 предложения)
4. `hypothetical_questions` — 4-6 вопросов на русском

   КРИТИЧЕСКИ ВАЖНО для вопросов:
   - Формулируй как РЕАЛЬНЫЙ КЛИЕНТ Башкирэнерго, который ищет информацию
   - НЕ ПИШИ абстрактные вопросы ("Что описано в данном разделе?", "О чём этот фрагмент?")
   - ПИШИ конкретные: "Какой срок подключения к электросетям до 15 кВт?", "Сколько стоит технологическое присоединение для физических лиц?"
   - Для НОРМАТИВНЫХ документов: "Что говорит статья 26 ФЗ-35 о технологическом присоединении?"
   - Для ОПЕРАЦИОННЫХ: "Как подать заявку на ТП через личный кабинет?"

5. `keywords` — 5-10 конкретных ключевых фраз для поиска (не абстрактные)
6. `entities` — 3-8 именованных сущностей (законы с номерами, организации, даты, суммы в рублях, мощности в кВт)

Верни строго валидный JSON-массив. Без пояснений, без обёрток ```json.
```

---

### Шаг 3: Маппинг metadata.json для html_pages

Для файлов из `operational/html_pages/` берём category из [metadata.json](file:///d:/ai_assistant/new_data/source/operational/metadata.json):

```python
def load_html_metadata():
    with open("new_data/source/operational/metadata.json") as f:
        meta = json.load(f)
    result = {}
    for item in meta.get("html_pages", []):
        result[item["file"]] = {
            "category": item["category"],  # ТПП, ДУ
            "source_origin": "operational",
            "document_source": "html_page",
            "description": item.get("description", "")
        }
    return result
```

---

## Open Questions

> [!IMPORTANT]
> **1. Точное имя модели deepseek-v4-flash на RouterAI?**
> Текущий скрипт использует `qwen/qwen3.5-flash-02-23` через `routerai.ru/api/v1`. Какое точное имя модели `deepseek-v4-flash` на RouterAI? Например: `deepseek/deepseek-v4-flash`?

> [!IMPORTANT]
> **2. FAQ CSV (`faq/faq-kt-tpp-2026.csv`) — включать ли?**
> В `operational/faq/` есть CSV с FAQ. Нужно ли его тоже обработать через llm_chunking, или он обрабатывается отдельно?

> [!NOTE]
> **3. Файл `markdown_data/faq-kt-tpp-2026.md`** — это markdown-версия того же FAQ CSV, или отдельный документ? Если дубль, исключить один из них.

> [!NOTE]
> **4. Паспорта услуг** (`passport-*.md`) — их 11 штук, все из `markdown_data/`. Они дублируют PDF из `operational/informational/`. Обрабатываем только .md версии?

---

## Verification Plan

### Automated Tests
1. Запустить `pre_split_for_llm.py` — проверить что все файлы ≤100k токенов
2. Запустить `llm_chunking.py` на 2-3 тестовых файлах (1 normative, 1 operational html_page, 1 passport)
3. Проверить JSON-валидность всех выходных файлов
4. Проверить что `hypothetical_questions` не содержат абстрактных вопросов
5. Проверить что `source_origin` корректно `normative` / `operational`

### Manual Verification
- Выборочная проверка 5-10 чанков на качество вопросов и keywords
- Убедиться что крупные файлы (ФЗ-35, 861, 442) корректно разбиты на части
