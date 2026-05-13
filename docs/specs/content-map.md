# Content Map — Bashkirenergo Knowledge Base

**Project:** AI Assistant (Башкирэнерго) — RAG-based Technical Connection Support  
**Date:** 2026-05-03  
**Status:** Draft  
**Related:** `docs/specs/qdrant-collections-schema.md`, `docs/specs/chunking-strategy.md`

---

## 1. Overview

This document maps content from `bashkirenergo.ru` to the two Qdrant collections:

| Collection | Content Types | Purpose |
|---|---|---|
| `normative_documents` | regulation | Законы, постановления, приказы, нормативные акты |
| `operational_content` | faq, stage_description, infomaterial, instruction | FAQ, этапы ТП, инфоматериалы, инструкции, памятки |

---

## 2. Content by Category

### 2.1 ТПП — Технологическое присоединение (core domain)

#### Нормативные документы → `normative_documents` collection

Документы с раздела "Нормативная база":
https://www.bashkirenergo.ru/consumers/gid-po-tekhnologicheskomu-prisoedineniyu/normative-base/

| # | Документ | URL (file ID) | Приоритет |
|---|---|---|---|
| 1 | ФЗ №35-ФЗ "Об электроэнергетике" | `/?get-file-by-id=3316` | HIGH |
| 2 | ПП РФ №861 (Правила ТП) | `/?get-file-by-id=3317` | HIGH |
| 3 | ПП РФ №442 (Розничные рынки) | `/?get-file-by-id=3318` | HIGH |
| 4 | ПП РФ №1178 (Ценообразование) | `/?get-file-by-id=3319` | HIGH |
| 5 | Приказ ФАС №490/22 (Плата за ТП) | `/?get-file-by-id=3324` | HIGH |
| 6 | ПП РФ №184 (ТСО) | `/?get-file-by-id=3320` | MEDIUM |
| 7 | ПП РФ №24 (Стандарты раскрытия инфо) | `/?get-file-by-id=3321` | MEDIUM |
| 8 | Приказ Минэнерго №186 (Стандарты качества) | `/?get-file-by-id=3322` | MEDIUM |
| 9 | Приказ ФСТ №215-э/1 (Методические указания) | `/?get-file-by-id=3323` | MEDIUM |
| 10 | ПГКТ РБ №306 (Плата за ТП на 2026) | `/?get-file-by-id=23925` | HIGH |
| 11 | ПП РФ №937 | `/?get-file-by-id=5542` | LOW |
| 12 | ПП РФ №86 (Вывод в ремонт) | `/?get-file-by-id=166605197` | LOW |
| 13 | ПП РФ №85 (Допуск в эксплуатацию) | `/?get-file-by-id=17707` | LOW |
| 14 | Распоряжение №147-р (Целевые модели) | `/?get-file-by-id=19544` | LOW |
| 15 | ПП РФ №1178 (Изменения) | `/?get-file-by-id=86829891` | LOW |

#### Описания этапов ТП → `operational_content` (stage_description)

HTML-страницы с гида по ТП. Не PDF — нужно скопировать текст в markdown.

| # | Страница | URL | Приоритет |
|---|---|---|---|
| 1 | Гид по ТП (главная) | `/consumers/gid-po-tekhnologicheskomu-prisoedineniyu/` | HIGH |
| 2 | ТП до 15 кВт (ФЛ) | `/consumers/gid-po-tekhnologicheskomu-prisoedineniyu/15kvt/` | HIGH |
| 3 | ТП от 15 до 150 кВт (ЮЛ/ИП) | `/consumers/gid-po-tekhnologicheskomu-prisoedineniyu/15kvt-150kvt/` | HIGH |
| 4 | ТП от 150 до 670 кВт | `/consumers/gid-po-tekhnologicheskomu-prisoedineniyu/150kvt-670kvt/` | HIGH |
| 5 | ТП свыше 670 кВт | `/consumers/gid-po-tekhnologicheskomu-prisoedineniyu/670kvt/` | HIGH |
| 6 | 1 шаг: подача заявки | `/consumers/gid-po-tekhnologicheskomu-prisoedineniyu/1-shag/` | HIGH |
| 7 | 2 шаг: выполнение работ | `/consumers/gid-po-tekhnologicheskomu-prisoedineniyu/2-shag/` | HIGH |
| 8 | 3 шаг: получение актов | `/consumers/gid-po-tekhnologicheskomu-prisoedineniyu/3-shag/` | HIGH |

#### FAQ → `operational_content` (faq)

| # | Источник | Описание | Приоритет |
|---|---|---|---|
| 1 | `/consumers/gid-po-tekhnologicheskomu-prisoedineniyu/questions/` | ~10+ FAQ вопросов на сайте | HIGH |

#### Паспорта услуг → `operational_content` (instruction / infomaterial)

PDF с раздела "Паспорта услуг":
https://www.bashkirenergo.ru/consumers/gid-po-tekhnologicheskomu-prisoedineniyu/passport/

| # | Документ | URL (file ID) | Приоритет |
|---|---|---|---|
| 1 | Паспорт: ТП ФЛ до 15 кВт | `/?get-file-by-id=3355` | HIGH |
| 2 | Паспорт: ТП ЮЛ/ИП до 150 кВт | `/?get-file-by-id=3396` | HIGH |
| 3 | Паспорт: ТП ЮЛ/ИП 150-670 кВт | `/?get-file-by-id=3398` | HIGH |
| 4 | Паспорт: ТП свыше 670 кВт | `/?get-file-by-id=3397` | HIGH |
| 5 | Паспорт: Перераспределение мощности | `/?get-file-by-id=3401` | MEDIUM |
| 6 | Паспорт: Индивидуальный проект | `/?get-file-by-id=3395` | MEDIUM |
| 7 | Паспорт: Восстановление документов | `/?get-file-by-id=3400` | MEDIUM |
| 8 | Паспорт: Вывод из эксплуатации | `/?get-file-by-id=168342629` | LOW |
| 9 | Паспорт: Временное ТП | `/?get-file-by-id=3399` | LOW |

#### Памятки → `operational_content` (infomaterial)

| # | Документ | URL | Приоритет |
|---|---|---|---|
| 1 | Памятка до 670 кВт | `/consumers/gid-po-tekhnologicheskomu-prisoedineniyu/less670max.pdf` | MEDIUM |
| 2 | Памятка свыше 670 кВт | `/consumers/gid-po-tekhnologicheskomu-prisoedineniyu/more670max.pdf` | MEDIUM |
| 3 | Перераспределение мощности | `/pereraspr/pereraspredelenie2025.pdf` | LOW |

#### Формы заявок/договоров/актов → `operational_content` (instruction)

Страница-агрегатор: `/consumers/gid-po-tekhnologicheskomu-prisoedineniyu/forms-documents/`

~60 PDF/DOC файлов: заявки ФЛ/ЮЛ, доверенности, договоры ТП, акты АТП, акты ТУ, соглашения.
**Приоритет: LOW** — формы нужны в первую очередь для ретривала по вопросам "какую форму заполнять", но не критичны для точности бенчмарка.

---

### 2.2 ДУ — Дополнительные услуги

ВСЁ → `operational_content` collection

| # | Страница | URL | Приоритет |
|---|---|---|---|
| 1 | Каталог ДУ | `/store/` | HIGH |
| 2 | Доп. услуги при ТП (пакеты) | `/store/.../dopolnitelnye-uslugi-pri-tekhnologicheskom-prisoedinenii.php` | HIGH |
| 3 | Прочие ДУ (испытания, ТУ, замена) | `/store/.../another.php` | MEDIUM |
| 4 | Услуги по установке ПУ | `/store/electricmeter/index.php` | MEDIUM |

---

### 2.3 ЛК — Личный кабинет

ВСЁ → `operational_content` collection

Страницы сайта:
| # | Страница | URL | Приоритет |
|---|---|---|---|
| 1 | Видеоинструкции ЛК | `/personal/videoinstruktsii/` | MEDIUM |

**Важно:** ЛК — это авторизованная зона. HTML-страницы ЛК недоступны без логина.

---

## 3. Project Directory Structure

Предлагаемая структура для хранения исходных документов:

```
new_data/
├── source/                          # Исходные файлы (что ты загружаешь)
│   ├── normative/                   # PDF нормативных документов
│   │   ├── 35-fz-ob-elektroenergetike.pdf
│   │   ├── 861-pravila-tp.pdf
│   │   ├── 442-o-roznichnyh-rynkah.pdf
│   │   ├── 1178-cenoobrazovanie.pdf
│   │   ├── 490-22-plata-za-tp.pdf
│   │   └── gkt-rb-306-plata-2026.pdf
│   ├── operational/                 # Операционные документы
│   │   ├── html_pages/              # Ты копируешь HTML → Markdown
│   │   │   ├── gid-po-tp.md
│   │   │   ├── tp-do-15kvt.md
│   │   │   ├── tp-15-150kvt.md
│   │   │   ├── tp-150-670kvt.md
│   │   │   ├── tp-svyshe-670kvt.md
│   │   │   ├── 1-shag-podacha-zayavki.md
│   │   │   ├── 2-shag-vypolnenie-rabot.md
│   │   │   ├── 3-shag-poluchenie-aktov.md
│   │   │   ├── faq.md
│   │   │   ├── dop-uslugi-pri-tp.md
│   │   │   ├── katalog-du.md
│   │   │   └── metadata.json        # URL + метаданные для каждой страницы
│   │   └── pdf/                     # PDF памяток и паспортов
│   │       ├── passport-tp-do-15kvt.pdf
│   │       ├── passport-tp-15-150kvt.pdf
│   │       ├── passport-tp-150-670kvt.pdf
│   │       ├── passport-tp-svyshe-670kvt.pdf
│   │       ├── pamyatka-do-670kvt.pdf
│   │       └── pamyatka-svyshe-670kvt.pdf
│   └── README.md                    # Что и откуда взято
│
└── benchmark_dataset.csv            # Существует — 541 вопрос
```

---

## 4. Pipeline Processing Order

После того, как файлы окажутся в `new_data/source/`:

```
                    ┌──────────────────────────────┐
                    │  new_data/source/  (PDF + .md)│
                    └──────────┬───────────────────┘
                               │
                    ┌──────────▼───────────────────┐
                    │  PDF Parser (future Phase 2)  │
                    │  RouterAI / PyMuPDF           │
                    │  → Markdown text              │
                    └──────────┬───────────────────┘
                               │
                    ┌──────────▼───────────────────┐
                    │  Mardown_splitter.py           │
                    │  (Stage 1: physical pre-split) │
                    │  chunks_universal/{category}/  │
                    └──────────┬───────────────────┘
                               │
                    ┌──────────▼───────────────────┐
                    │  llm_chunking.py               │
                    │  (Stage 2: LLM semantic split  │
                    │   + metadata enrichment)       │
                    │  chechov/{category}/           │
                    └──────────┬───────────────────┘
                               │
                    ┌──────────▼───────────────────┐
                    │  metadata_injector.py          │
                    │  (neighbor_chunk_ids,          │
                    │   collection_name,             │
                    │   document_type,               │
                    │   power_range, client_type)    │
                    └──────────┬───────────────────┘
                               │
                    ┌──────────▼───────────────────┐
                    │  Qdrant Ingestion              │
                    │  normative_documents           │
                    │  operational_content           │
                    └──────────────────────────────┘
```

---

## 5. Priority Matrix for Download

| Priority | Content | Count | Impact on Benchmark |
|----------|---------|-------|-------------------|
| **P0 — Critical** | Нормативные PDF (первые 6: 35-ФЗ, 861, 442, 1178, 490/22, ГКТ РБ №306) | 6 docs | ~40% improvement (тарифы, льготы, правила) |
| **P1 — High** | HTML-страницы этапов ТП (8 страниц) + ТПП FAQ | 9 docs | ~25% improvement (процедуры, сроки) |
| **P1 — High** | Паспорта услуг (6шт: до 15, 15-150, 150-670, >670, индивидуальный, восстановление) | 6 PDF | ~10% improvement |
| **P2 — Medium** | ДУ и ЛК контент (каталог, видеоинструкции) | 3 docs | ~5% improvement |
| **P3 — Low** | Все остальные нормативные PDF (~9 шт) | 9 docs | ~5% improvement |
| **P4 — Nice to have** | Формы заявок/договоров (~60 шт), памятки | ~65 files | ~0% (не влияют на benchmark вопросы) |
