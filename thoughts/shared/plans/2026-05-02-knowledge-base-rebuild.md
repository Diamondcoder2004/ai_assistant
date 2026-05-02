# Implementation Plan: Knowledge Base Rebuild

## Based on Design
`thoughts/shared/designs/2026-05-02-knowledge-base-rebuild-design.md`

## Phase 1: Foundation & Domain Language

### Task 1.1: Ubiquitous Language (DONE)
- **File**: `UBIQUITOUS_LANGUAGE.md` — извлечен из benchmark_dataset.csv
- **Contains**: 18 тематических разделов, 7 критических неоднозначностей с исправлениями
- **Status**: ✅ Complete

### Task 1.2: Qdrant Collection Schema Design
- **File to create**: `docs/specs/qdrant-collections-schema.md`
- **Content**: Определить поля, индексы, векторные параметры для 2 коллекций:
  - `normative_documents` — для нормативных документов
  - `operational_content` — для FAQ, этапов, инфоматериалов
- **Key decisions**:
  - Vector size: соответствует `pplx-embed-v1-4b` (проверить в config)
  - Distance: Cosine
  - Payload indexes: category, document_type, client_type, power_range
  - Metadata fields: все из design doc §5.3
- **Dependencies**: None
- **Verification**: Документ содержит полную спецификацию обеих коллекций

### Task 1.3: Chunking Strategy Specification
- **File to create**: `docs/specs/chunking-strategy.md`
- **Content**:
  - chunk_size: 1000-4000 символов (вместо текущих 1000-20000)
  - chunk_overlap: 200 символов
  - Primary splitter: MarkdownHeaderTextSplitter
  - Fallback: RecursiveCharacterTextSplitter
  - Document-type specific rules (нормативные vs операционные документы)
- **Dependencies**: None
- **Verification**: Спецификация согласована с constraints из design doc

### Task 1.4: Update Knowledge Base Schema Diagrams
- **Files to modify**:
  - `docs/diagrams/knowledge-base-schema.drawio`
  - `docs/diagrams/knowledge-base-schema.md`
- **Content**: Обновить схемы согласно новой архитектуре (2 коллекции, enriched metadata, PDF parser)
- **Dependencies**: Task 1.2 (schema design)
- **Verification**: Диаграммы отражают множественные коллекции и новый pipeline

## Phase 2: Content Ingestion Pipeline

### Task 2.1: PDF Parser
- **File to create**: `backend/chunking/pdf_parser.py`
- **Functionality**:
  - Primary: RouterAI API для структурированного извлечения (заголовки, секции, таблицы)
  - Fallback: PyMuPDF для сырого текста
  - Input: PDF file path
  - Output: структурированный текст с breadcrumbs (заголовки как иерархия)
- **Error handling**:
  - RouterAI timeout → retry 3x с exponential backoff → fallback на PyMuPDF
  - PyMuPDF fail → логирование, документ помечается "needs_manual_review"
- **Dependencies**: Task 1.3 (chunking strategy)
- **Verification**: Unit tests на 2-3 образцовых PDF

### Task 2.2: Update Markdown Splitter
- **File to modify**: `backend/chunking/Mardown_splitter.py`
- **Changes**:
  - Уменьшить max chunk size с 20000 до 4000 символов
  - Установить chunk_overlap: 200
  - Добавить поддержку breadcrumbs из pdf_parser
  - Сохранить текущую логику MarkdownHeaderTextSplitter + RecursiveCharacterTextSplitter
- **Constraints**: Не ломать существующую функциональность
- **Dependencies**: Task 1.3
- **Verification**: Тесты на размер чанков, сохранение заголовков

### Task 2.3: Update LLM Enrichment
- **File to modify**: `backend/chunking/llm_chunking.py`
- **Changes**:
  - Сохранить существующие поля (summary, hypothetical_questions, keywords, entities, category, breadcrumbs)
  - Добавить новые поля в промпт: collection_name, document_type, power_range, client_type
  - Обновить JSON schema для валидации
  - Использовать repair_json.py при parse errors
- **Constraints**: Стиль промпта не менять (prompts frozen)
- **Dependencies**: Task 1.2 (schema design)
- **Verification**: Mock-тесты на генерацию метадаты с новыми полями

### Task 2.4: Metadata Injector
- **File to create**: `backend/chunking/metadata_injector.py`
- **Functionality**:
  - Добавляет neighbor_chunk_ids (prev, next) после сплиттинга
  - Валидирует и нормализует поля (power_range, client_type)
  - Определяет collection_name на основе document_type
  - Input: список чанков от splitter
  - Output: чанки с полной метадатой
- **Logic for collection assignment**:
  - regulation → normative_documents
  - faq, stage_description, infomaterial, instruction → operational_content
- **Dependencies**: Task 2.2, Task 2.3
- **Verification**: Тесты на корректность neighbor_chunk_ids и валидацию

### Task 2.5: Batch Ingestion Script
- **File to create**: `backend/chunking/batch_ingest.py`
- **Functionality**:
  - Pipeline: PDF → Parser → Splitter → Enrichment → Injector → Qdrant
  - Поддержка batch processing (множество файлов)
  - Progress logging
  - Resume capability (пропуск уже обработанных)
  - Двухколлекционная инжестия (normative_documents / operational_content)
- **Error handling**:
  - Collection not found → autocreate с правильной схемой
  - Duplicate chunk_id → upsert
  - Vector dimension mismatch → fatal error, stop ingestion
- **Dependencies**: Task 2.1, Task 2.2, Task 2.3, Task 2.4
- **Verification**: End-to-end тест на 1 PDF файле

### Task 2.6: Run Ingestion
- **Action**: Запустить batch_ingest.py на всех доступных PDF/DOCX/Markdown файлах
- **Target**: Обе коллекции содержат >1000 чанков каждая
- **Dependencies**: Task 2.5, наличие PDF файлов от пользователя
- **Verification**: Проверка количества чанков в Qdrant, spot-check метадаты

## Phase 3: Runtime Integration

### Task 3.1: Query Classifier
- **File to create**: `backend/agents/query_classifier.py`
- **Functionality**:
  - Анализирует user query на ключевые слова
  - Нормативные: тариф, постановление, льгота, ставка, закон → normative_documents
  - Операционные: как подать, этап, документ, срок, стоимость → operational_content
  - Неопределенный → обе коллекции
  - Также классифицирует ЛК/ДУ/ТПП
- **Implementation**: Rule-based (keyword matching) с возможностью расширения до LLM-based
- **Dependencies**: None
- **Verification**: Тесты на benchmark questions

### Task 3.2: Update SearchAgent
- **File to modify**: `backend/agents/search_agent.py`
- **Changes**:
  - Интегрировать Query Classifier
  - Добавить параметр collection в вызовы поиска
  - Поддержка multi-collection search (объединение результатов)
  - Сохранить текущую логику генерации search queries
- **Constraints**: Не менять prompts style
- **Dependencies**: Task 3.1, Task 2.6 (коллекции должны существовать)
- **Verification**: Интеграционные тесты поиска

### Task 3.3: Update Search Tool
- **File to modify**: `backend/tools/search_tool.py`
- **Changes**:
  - Добавить параметр collection(s) в API
  - Поддержка поиска по одной или нескольким коллекциям
  - Объединение и ранжирование результатов из множественных коллекций
  - Сохранить BM25 normalization и веса
- **Dependencies**: Task 3.2
- **Verification**: Проверка весов суммируются в 1.0

### Task 3.4: Benchmark Run
- **Action**: Запустить полный бенчмарк (308 вопросов)
- **Baseline**: 39% (текущий)
- **Phase 1 target**: >50%
- **Phase 2 target**: >65%
- **Phase 3 target**: >75%
- **Dependencies**: Task 3.2, Task 3.3
- **Verification**: Сравнение с baseline, анализ по категориям

### Task 3.5: Error Analysis & Iteration
- **Action**: Анализ результатов бенчмарка
- **Focus areas**:
  - Терминология (ФЛ/ИП/ЮЛ) — должно улучшиться за счет метадаты client_type
  - Стоимость/тарифы — должно улучшиться за счет normative_documents collection
  - Мощностные лимиты — должно улучшиться за счет power_range
  - Льготы — должно улучшиться за счет разделения коллекций
- **Iterations**:
  - Корректировка chunk size / overlap
  - Корректировка весов hybrid search
  - Добавление/удаление metadata fields
  - Возможно: parent-child chunking если фрагментация контекста
- **Dependencies**: Task 3.4
- **Verification**: Повторный бенчмарк показывает улучшение

## Files Summary

### New Files (6)
1. `docs/specs/qdrant-collections-schema.md`
2. `docs/specs/chunking-strategy.md`
3. `backend/chunking/pdf_parser.py`
4. `backend/chunking/metadata_injector.py`
5. `backend/chunking/batch_ingest.py`
6. `backend/agents/query_classifier.py`

### Modified Files (4)
1. `backend/chunking/Mardown_splitter.py` — параметры чанкинга
2. `backend/chunking/llm_chunking.py` — новые поля метадаты
3. `backend/agents/search_agent.py` — выбор коллекции
4. `backend/tools/search_tool.py` — multi-collection search

### Already Done (1)
1. `UBIQUITOUS_LANGUAGE.md` — доменный глоссарий ✅

## Execution Order

```
Phase 1 (Documentation):
  Task 1.1 ✅ → Task 1.2 → Task 1.3 → Task 1.4
                              ↓
Phase 2 (Pipeline):           ↓
  Task 2.1 → Task 2.2 → Task 2.3 → Task 2.4 → Task 2.5 → Task 2.6
                ↑                    ↑
                └──── Task 1.3 ──────┘      └──── Task 1.2 ─────┘
                                                        ↓
Phase 3 (Runtime):                                      ↓
  Task 3.1 → Task 3.2 → Task 3.3 → Task 3.4 → Task 3.5
                              ↑
                              └──── Task 2.6 ─────┘
```

## Verification Checklist

- [ ] Qdrant collections created with correct schema
- [ ] PDF parser extracts structure correctly (tested on 3+ files)
- [ ] Chunk sizes are within 1000-4000 chars
- [ ] Metadata contains all required fields (including neighbor_chunk_ids)
- [ ] Batch ingestion completes without fatal errors
- [ ] Both collections have >1000 chunks
- [ ] Query classifier correctly routes 80%+ of test queries
- [ ] Benchmark accuracy improved by at least 10% from baseline
- [ ] No prompt style changes in backend/prompts/
- [ ] Hybrid search weights still sum to 1.0
