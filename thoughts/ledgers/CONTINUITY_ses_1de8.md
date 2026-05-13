---
session: ses_1de8
updated: 2026-05-13T14:04:05.585Z
---

# Session Summary

## Goal
Разработать механизм категорийной фильтрации поиска в Qdrant: для вопросов по ЛК и ДУ часть чанков (≈30%) искать с фильтром по полю `category`, чтобы повысить precision ретривала при сохранении recall.

## Constraints & Preferences
- QueryGenerator уже принимает `category` на вход — нужно, чтобы он сам детектил категорию (ЛК/ДУ/ТПП) и выводил её для SearchAgent
- Нельзя терять recall: только доля результатов фильтруется (≈30%), остальные — обычный полный поиск
- Категория хранится в Qdrant на уровне chunk-документа, поле `category` в `payload`
- SearchTool уже умеет принимать `query_filter` — нужно только прокинуть его из SearchAgent
- QueryGenerator переиспользует тот же LLM-вызов — категория должна выводиться без отдельных дорогих вызовов

## Progress
### Done
- [x] Проанализирован `benchmark_20260513_075934_enriched.csv` (308 вопросов, 27.2% binary correctness)
- [x] Подсчитано количество отказов модели «нет в источниках»: 69/308 (22.4%), из них 87% (60/69) — ложно-отрицательные (ответ есть в KB, но не дотянулся ретривал)
- [x] Изучен QueryGenerator (`backend/agents/query_generator.py`): уже принимает `category` параметр (дефолт `"не известна"`), передаёт его в промпт; выход — `QueryGenerationResult` с `queries` (List[Dict[str, str]]) и `search_params` (Dict[str, Any])
- [x] Изучен SearchAgent (`backend/agents/search_agent.py`): на вход принимает `query_filter` (опционально), передаёт его в `search_tool`; search_tool уже поддерживает `filter_condition` через `query_filter: dict`
- [x] Изучен SearchTool (`backend/tools/search_tool.py`): `search()` принимает `filter_condition`, пропускает его как `query_filter` в `qdrant_client.query_points()`; supported по версии REST API Qdrant (от 2024)
- [x] Изучен WikiRouter: возвращает `full_analysis` с `category` (ЛК/ДУ/ТПП/..., плюс `"неизвестно"`); принимает на вход `user_query + conversation_history`
- [x] Изучен `backend/prompts/query_generation.py`: шаблон промпта, как category вставляется в секцию контекста

### In Progress
- [ ] Разработка решения: точная схема передачи category от QueryGenerator → SearchAgent → SearchTool → фильтр Qdrant

### Blocked
- (none)

## Key Decisions
- **Фильтровать только часть результатов (blended)**: 30% от top-k будут браться с фильтром по category, 70% — без фильтра. Это компромисс между precision и recall.
- **QueryGenerator сам детектит category** из вопроса + wiki-контекста: выводит новое поле `category` в `search_params`. Без отдельного LLM-вызова — на основе существующего анализа.
- **Категории ЛК и ДУ фильтруются**; ТПП — не фильтруется (очень широкая, нет смысла).
- **Filtering на уровне Qdrant REST API `query_points`**: `must` + `term` фильтр по полю `category` в payload.

## Next Steps
1. Утвердить с пользователем схему: как QueryGenerator должен выдавать category (поле в `search_params` vs новое поле в `QueryGenerationResult`)
2. Детально спроектировать «blended retrieval» в SearchAgent: как смешивать filtered и unfiltered результаты
3. Реализовать QueryGenerator → детекция категории
4. Реализовать SearchAgent → blended retrieval с category filter
5. Проверить на benchmark-сете с категорий ЛК и ДУ

## Critical Context
- **Benchmark факты**: 308 вопросов, 27.2% бинарной корректности, 22.4% отказов «нет в источниках», слабые места — ДУ и ЛК-категории
- **QueryGenerator уже имеет category на входе**, но сейчас категория задаётся снаружи (дефолт `"не известна"`) — нужно, чтобы QueryGenerator сам её детектил И выводил обратно
- **SearchAgent уже фильтрует**: `collection_filter = {"#!collection": "final"}`, может взять `query_filter` через `search_tool`
- **search_tool** поддерживает `filter_condition` с любой структурой
- **Qdrant chunks** — у каждого чанка есть поле `category` в payload, заполняется на этапе энричмента
- Результаты инжектятся в `sources_json`, который передаётся в ResponseAgent — категория может повлиять и на промпт генерации ответа

## File Operations
### Read
- `backend/agents/query_generator.py` — полный код
- `backend/agents/search_agent.py` — полный код
- `backend/tools/search_tool.py` — полный код
- `backend/prompts/query_generation.py` — полный код
- `backend/wiki/wiki_router.py` — полный код
- `D:\ai_assistant\backend\api_benchmarks\benchmark_20260513_075934_enriched.csv` — benchmark-файл (308 строк)

### Modified
- (none)
