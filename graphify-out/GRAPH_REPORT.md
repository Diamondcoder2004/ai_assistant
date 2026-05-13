# Graph Report - D:/ai_assistant  (2026-05-01)

## Corpus Check
- 147 files · ~126,723 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 943 nodes · 2722 edges · 34 communities detected
- Extraction: 37% EXTRACTED · 63% INFERRED · 0% AMBIGUOUS · INFERRED: 1703 edges (avg confidence: 0.54)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Response Agent|Response Agent]]
- [[_COMMUNITY_Query Generator Agent|Query Generator Agent]]
- [[_COMMUNITY_Benchmark System|Benchmark System]]
- [[_COMMUNITY_FastAPI App Lifecycle|FastAPI App Lifecycle]]
- [[_COMMUNITY_REST API Endpoints|REST API Endpoints]]
- [[_COMMUNITY_Response Post-Processing|Response Post-Processing]]
- [[_COMMUNITY_Timing Utils (3637 files)|Timing Utils (36/37 files)]]
- [[_COMMUNITY_Agent Debug Logger (2526 files)|Agent Debug Logger (25/26 files)]]
- [[_COMMUNITY_Qdrant Ingestion (2324 files)|Qdrant Ingestion (23/24 files)]]
- [[_COMMUNITY_Benchmark Reports (820 files)|Benchmark Reports (8/20 files)]]
- [[_COMMUNITY_LLM Chunking (116 files)|LLM Chunking (1/16 files)]]
- [[_COMMUNITY_API Endpoints (215 files)|API Endpoints (2/15 files)]]
- [[_COMMUNITY_Search Tool (1315 files)|Search Tool (13/15 files)]]
- [[_COMMUNITY_RouterAI Embeddings (1214 files)|RouterAI Embeddings (12/14 files)]]
- [[_COMMUNITY_Tests (1112 files)|Tests (11/12 files)]]
- [[_COMMUNITY_Markdown Splitter (111 files)|Markdown Splitter (1/11 files)]]
- [[_COMMUNITY_API Full Test (99 files)|API Full Test (9/9 files)]]
- [[_COMMUNITY_Frozen Prompts (39 files)|Frozen Prompts (3/9 files)]]
- [[_COMMUNITY_Review Scripts (78 files)|Review Scripts (7/8 files)]]
- [[_COMMUNITY_API Full Test (66 files)|API Full Test (6/6 files)]]
- [[_COMMUNITY_Benchmark Utils (14 files)|Benchmark Utils (1/4 files)]]
- [[_COMMUNITY_Frontend Utils (14 files)|Frontend Utils (1/4 files)]]
- [[_COMMUNITY_Load Tests (33 files)|Load Tests (3/3 files)]]
- [[_COMMUNITY_Fe Appvue (3 nodes)|Fe Appvue (3 nodes)]]
- [[_COMMUNITY_Backend Config (2 nodes)|Backend Config (2 nodes)]]
- [[_COMMUNITY_Api Init Rationale 1 (2 nodes)|Api Init Rationale 1 (2 nodes)]]
- [[_COMMUNITY_Benchmark Utils (12 files)|Benchmark Utils (1/2 files)]]
- [[_COMMUNITY_Query Generator (11 files)|Query Generator (1/1 files)]]
- [[_COMMUNITY_Agent Debug Logger (11 files)|Agent Debug Logger (1/1 files)]]
- [[_COMMUNITY_Timing Utils (11 files)|Timing Utils (1/1 files)]]
- [[_COMMUNITY_Arch Querygenerationresult (1 nodes)|Arch Querygenerationresult (1 nodes)]]
- [[_COMMUNITY_Arch Searchrequest (1 nodes)|Arch Searchrequest (1 nodes)]]
- [[_COMMUNITY_Arch Searchresult (1 nodes)|Arch Searchresult (1 nodes)]]
- [[_COMMUNITY_Fn Convert Embedding (1 nodes)|Fn Convert Embedding (1 nodes)]]

## God Nodes (most connected - your core abstractions)
1. `QueryGeneratorAgent` - 226 edges
2. `SearchAgent` - 208 edges
3. `AgenticRAG` - 190 edges
4. `SearchTool` - 185 edges
5. `SearchRequest` - 182 edges
6. `ResponseAgent` - 168 edges
7. `QueryGenerationResult` - 148 edges
8. `SearchResult` - 146 edges
9. `LLMJudge` - 44 edges
10. `create_mock_llm_response()` - 21 edges

## Surprising Connections (you probably didn't know these)
- `SearchTool.search()` --semantically_similar_to--> `Hybrid Search (4-component)`  [INFERRED] [semantically similar]
  backend/tools/search_tool.py → backend/docs/ARCHITECTURE.md
- `Проверяет, является ли ответ null/пустым/ошибочным` --uses--> `LLMJudge`  [INFERRED]
  backend\benchmarks\retry_null_answers.py → backend\llm_judge.py
- `test_benchmark_questions()` --calls--> `AgenticRAG`  [INFERRED]
  backend\tests\test_load_performance.py → backend\main.py
- `Фоновая загрузка BM25 кэша при старте приложения  Использование:     from uti` --uses--> `SearchTool`  [INFERRED]
  backend\utils\bg_cache_loader.py → backend\tools\search_tool.py
- `Фоновая загрузка BM25 кэша.          Запускается в отдельном потоке, не блокир` --uses--> `SearchTool`  [INFERRED]
  backend\utils\bg_cache_loader.py → backend\tools\search_tool.py

## Hyperedges (group relationships)
- **Agent Pipeline: Query → Search → Response** — arch_QueryGeneratorAgent, arch_SearchAgent, arch_ResponseAgent [EXTRACTED 1.00]
- **Hybrid Search: 4 Vector + Lexical Components** — search_PrefComponent, search_HypeComponent, search_LexicalComponent, search_ContextualComponent [EXTRACTED 1.00]
- **Infrastructure: Nginx → FastAPI → Qdrant + Supabase + RouterAI** — infra_Nginx, infra_FastAPI, infra_Qdrant, infra_Supabase, infra_RouterAI, infra_Vue3_SPA [EXTRACTED 1.00]
- **Domain: ЛК + ДУ + ТПП** — domain_LK, domain_DU, domain_TPP, domain_Bashkirenergo, domain_CustomerCategories [EXTRACTED 1.00]

## Communities

### Community 0 - "Response Agent"
Cohesion: 0.04
Nodes (144): Генерация ответа.          Args:             user_query: Вопрос пользователя, Генерация ответа с уточняющими вопросами.                  Args:, Агент для формирования ответов на основе результатов поиска.          Использу, ResponseAgent, Агент поиска с использованием Tool Calling.          Использует LLM для:, Повторный поиск с изменёнными параметрами., Форматирование результатов для передачи в LLM.                  Args:, Поиск с использованием агента.          Args:             user_query: Вопрос (+136 more)

### Community 1 - "Query Generator Agent"
Cohesion: 0.04
Nodes (78): from_dict(), generate(), QueryGenerationResult, QueryGeneratorAgent, Query Generator Agent — генерация поисковых запросов, Результат генерации запросов., Возвращает дефолтный результат при ошибке., Проверка необходимости уточнения. (+70 more)

### Community 2 - "Benchmark System"
Cohesion: 0.04
Nodes (64): AgenticRAGBenchmark, BenchmarkResult, BenchmarkSample, create_default_samples(), load_benchmark_samples(), main(), Benchmark для оценки качества Agentic RAG, Оценка одного примера. (+56 more)

### Community 3 - "FastAPI App Lifecycle"
Cohesion: 0.06
Nodes (93): global_exception_handler(), lifespan(), log_requests(), RAG API для Башкирэнерго Главный файл приложения FastAPI с интеграцией Agentic, Middleware для логирования всех входящих запросов с таймингами, Глобальный обработчик исключений, Управление жизненным циклом приложения, get_current_user() (+85 more)

### Community 4 - "REST API Endpoints"
Cohesion: 0.05
Nodes (50): GET /health - health check, GET /history - chat history, POST /feedback - user feedback, POST /query - non-streaming, POST /query/stream - SSE streaming, Agentic RAG Pipeline, Query Generator Agent, Response Agent (+42 more)

### Community 5 - "Response Post-Processing"
Cohesion: 0.06
Nodes (26): filter_technical_phrases(), fix_latex_in_text(), generate_response(), Response Agent — агент формирования ответов, Конвертирует формулы из (C_1) в \(C_1\) для правильного рендеринга.      Обраб, Форматирование контекста из результатов поиска., Форматирование истории диалога., Создание пользовательского промпта. (+18 more)

### Community 6 - "Timing Utils (36/37 files)"
Cohesion: 0.07
Nodes (24): get_timing_stats(), print_timing_stats(), Timing utilities — утилиты для замера времени выполнения, Получение всей статистики., Получение статистики по запросам., Сохранение статистики в файл., Декоратор для замера времени выполнения функции.          Args:         name: Им, Статистика по одному методу/операции. (+16 more)

### Community 7 - "Agent Debug Logger (25/26 files)"
Cohesion: 0.09
Nodes (15): AgentDebugLogger, get_debug_logger(), Система детального логирования работы агентов Записывает каждый шаг в JSON форм, Очистка данных для логирования (убираем лишнее)., Установить финальный ответ., Сохранить лог сессии., Логгер для детальной отладки работы агентов.          Записывает в backend/log, Получить глобальный логгер. (+7 more)

### Community 8 - "Qdrant Ingestion (23/24 files)"
Cohesion: 0.12
Nodes (21): get_routerai_embedder(), load_all_chunks(), main(), prepare_text_contextual(), prepare_text_hype(), prepare_text_pref(), Готовит текст для pref‑вектора: summary + content., Готовит текст для hype‑вектора: все гипотетические вопросы. (+13 more)

### Community 9 - "Benchmark Reports (8/20 files)"
Cohesion: 0.13
Nodes (16): extract_category(), generate_report(), is_null_answer(), load_results(), main(), Извлекает категорию из JSON-строки sources, generate_jwt(), is_null_answer() (+8 more)

### Community 10 - "LLM Chunking (1/16 files)"
Cohesion: 0.21
Nodes (15): clean_json_string(), enrich_chunk(), generate_parent_chunk_id(), log_failure(), main(), process_file(), Генерирует идентификатор родительского чанка (первые 12 символов md5)., Очистка JSON от markdown-обёрток и управляющих символов. (+7 more)

### Community 11 - "API Endpoints (2/15 files)"
Cohesion: 0.13
Nodes (13): bm25_status(), Статус BM25 кэша (без аутентификации), get_bm25_status(), is_bm25_loaded(), is_bm25_loading(), load_bm25_background(), Фоновая загрузка BM25 кэша при старте приложения  Использование:     from uti, Фоновая загрузка BM25 кэша.          Запускается в отдельном потоке, не блокир (+5 more)

### Community 12 - "Search Tool (13/15 files)"
Cohesion: 0.14
Nodes (8): get_morph_analyzer(), Search Tool — инструмент поиска в базе знаний, Токенизация текста с лемматизацией., Получение BM25 оценок., Гибридный поиск.                  Args:             request: Запрос на поиск, Получение экземпляра MorphAnalyzer (синглтон)., Поиск по нескольким запросам.                  Args:             queries: Спи, Загрузка документов для BM25.

### Community 13 - "RouterAI Embeddings (12/14 files)"
Cohesion: 0.18
Nodes (9): convert_embedding(), get_routerai_embedder(), RouterAI Embeddings с поддержкой int8 конвертации, Конвертация и нормализация эмбеддинга.          Perplexity API возвращает int8 в, Класс для работы с эмбеддингами через RouterAI API., Получение эмбеддинга для запроса.                  Args:             query: Текс, Получение эмбеддингов для документов.                  Args:             documen, Фабричная функция для получения эмбеддера. (+1 more)

### Community 14 - "Tests (11/12 files)"
Cohesion: 0.17
Nodes (2): Нагрузочные тесты с метриками производительности  Тесты измеряют: - Время отв, test_benchmark_questions()

### Community 15 - "Markdown Splitter (1/11 files)"
Cohesion: 0.27
Nodes (10): merge_small_chunks(), process_directory(), process_file(), Основная функция:     1. Пытается разбить по заголовкам.     2. Если получилос, Объединяет мелкие чанки с соседними, не превышая max_size., Пытается разбить текст по заголовкам Markdown.     Если заголовков нет или разб, Универсальный рекурсивный сплиттер с уважением к таблицам и абзацам., recursive_split() (+2 more)

### Community 16 - "API Full Test (9/9 files)"
Cohesion: 0.31
Nodes (8): analyze_response(), generate_jwt_token(), main(), Полное тестирование API на замечания из документа Testirovanie_II_po_TPP.docx С, Генерируем JWT токен вручную, Тестируем один запрос к API, Анализируем ответ системы на наличие проблем, test_query()

### Community 17 - "Frozen Prompts (3/9 files)"
Cohesion: 0.22
Nodes (6): get_query_generation_prompt(), Промпты для генерации поисковых запросов, Формирует промпт для генерации поисковых запросов.      Args:         user_qu, get_system_prompt(), Системный промпт для Agentic RAG, Возвращает системный промпт.

### Community 19 - "Review Scripts (7/8 files)"
Cohesion: 0.32
Nodes (6): is_answer_not_found(), is_meaning_correct_vs_exact(), my_classification(), Hybrid benchmark review: uses judge's binary_correctness as baseline, then manua, If expected is short (< 50 chars) and answer is much longer (>300 chars),     it, Determine my own binary correctness and classification.     Uses multiple signal

### Community 21 - "API Full Test (6/6 files)"
Cohesion: 0.47
Nodes (5): analyze(), generate_jwt(), main(), Тестирование API на реальных вопросах из документа Testirovanie_II_po_TPP.docx, Проверяем ответ на запрещённые паттерны

### Community 23 - "Benchmark Utils (1/4 files)"
Cohesion: 0.5
Nodes (2): classify(), Classify into:     - exact_match: judge_binary_correctness=1 AND answer is conci

### Community 24 - "Frontend Utils (1/4 files)"
Cohesion: 0.67
Nodes (2): escapeHtml(), renderMarkdown()

### Community 25 - "Load Tests (3/3 files)"
Cohesion: 0.67
Nodes (1): Статический тест: проверка бизнес-правил в промптах

### Community 28 - "Fe Appvue (3 nodes)"
Cohesion: 0.67
Nodes (3): App.vue - Root Component, Tailwind CSS Styling, Vue Router

### Community 29 - "Backend Config (2 nodes)"
Cohesion: 1.0
Nodes (1): Конфигурация проекта Agentic RAG

### Community 30 - "Api Init Rationale 1 (2 nodes)"
Cohesion: 1.0
Nodes (1): API модули для RAG сервиса

### Community 31 - "Benchmark Utils (1/2 files)"
Cohesion: 1.0
Nodes (1): Generate comprehensive markdown benchmark analysis report.

### Community 37 - "Query Generator (1/1 files)"
Cohesion: 1.0
Nodes (1): Генерация поисковых запросов.          Args:             user_query: Вопрос п

### Community 41 - "Agent Debug Logger (1/1 files)"
Cohesion: 1.0
Nodes (1): Контекстный менеджер для автоматического замера времени шага.

### Community 42 - "Timing Utils (1/1 files)"
Cohesion: 1.0
Nodes (1): Среднее время выполнения.

### Community 66 - "Arch Querygenerationresult (1 nodes)"
Cohesion: 1.0
Nodes (1): QueryGenerationResult dataclass

### Community 67 - "Arch Searchrequest (1 nodes)"
Cohesion: 1.0
Nodes (1): SearchRequest dataclass

### Community 68 - "Arch Searchresult (1 nodes)"
Cohesion: 1.0
Nodes (1): SearchResult dataclass

### Community 74 - "Fn Convert Embedding (1 nodes)"
Cohesion: 1.0
Nodes (1): convert_embedding() - int8 normalization

## Knowledge Gaps
- **159 isolated node(s):** `Конфигурация проекта Agentic RAG`, `LLM-as-a-Judge для оценки качества ответов RAG системы  Оценивает ответы по ме`, `Результат оценки LLM Judge.`, `LLM-as-a-Judge для оценки ответов RAG системы.`, `Вырезает JSON из строки, если модель добавила лишний текст или ```json.` (+154 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Tests (11/12 files)`** (12 nodes): `test_load_performance.py`, `avg_latency()`, `error_rate()`, `max_latency()`, `min_latency()`, `p50_latency()`, `p95_latency()`, `p99_latency()`, `Нагрузочные тесты с метриками производительности  Тесты измеряют: - Время отв`, `rps()`, `run_tests()`, `test_benchmark_questions()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Benchmark Utils (1/4 files)`** (4 nodes): `process_benchmark.py`, `classify()`, `get_category()`, `Classify into:     - exact_match: judge_binary_correctness=1 AND answer is conci`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Frontend Utils (1/4 files)`** (4 nodes): `markdownRenderer.js`, `escapeHtml()`, `handleSourceClick()`, `renderMarkdown()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Load Tests (3/3 files)`** (3 nodes): `main()`, `test_static_rules.py`, `Статический тест: проверка бизнес-правил в промптах`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Backend Config (2 nodes)`** (2 nodes): `config.py`, `Конфигурация проекта Agentic RAG`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Api Init Rationale 1 (2 nodes)`** (2 nodes): `API модули для RAG сервиса`, `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Benchmark Utils (1/2 files)`** (2 nodes): `generate_report.py`, `Generate comprehensive markdown benchmark analysis report.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Query Generator (1/1 files)`** (1 nodes): `Генерация поисковых запросов.          Args:             user_query: Вопрос п`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Agent Debug Logger (1/1 files)`** (1 nodes): `Контекстный менеджер для автоматического замера времени шага.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Timing Utils (1/1 files)`** (1 nodes): `Среднее время выполнения.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Arch Querygenerationresult (1 nodes)`** (1 nodes): `QueryGenerationResult dataclass`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Arch Searchrequest (1 nodes)`** (1 nodes): `SearchRequest dataclass`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Arch Searchresult (1 nodes)`** (1 nodes): `SearchResult dataclass`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Fn Convert Embedding (1 nodes)`** (1 nodes): `convert_embedding() - int8 normalization`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `AgenticRAG` connect `Benchmark System` to `Response Agent`, `Query Generator Agent`, `FastAPI App Lifecycle`, `API Endpoints (2/15 files)`, `Tests (11/12 files)`?**
  _High betweenness centrality (0.196) - this node is a cross-community bridge._
- **Why does `QueryGeneratorAgent` connect `Query Generator Agent` to `Response Agent`, `Benchmark System`, `Response Post-Processing`, `Tests (11/12 files)`?**
  _High betweenness centrality (0.081) - this node is a cross-community bridge._
- **Why does `SearchTool` connect `Response Agent` to `Query Generator Agent`, `Benchmark System`, `Response Post-Processing`, `API Endpoints (2/15 files)`, `Search Tool (13/15 files)`, `RouterAI Embeddings (12/14 files)`, `Tests (11/12 files)`?**
  _High betweenness centrality (0.077) - this node is a cross-community bridge._
- **Are the 219 inferred relationships involving `QueryGeneratorAgent` (e.g. with `SearchAgent` and `Search Agent — агент поиска с Tool Calling`) actually correct?**
  _`QueryGeneratorAgent` has 219 INFERRED edges - model-reasoned connections that need verification._
- **Are the 203 inferred relationships involving `SearchAgent` (e.g. with `AgenticRAG` and `Agentic RAG — точка входа`) actually correct?**
  _`SearchAgent` has 203 INFERRED edges - model-reasoned connections that need verification._
- **Are the 181 inferred relationships involving `AgenticRAG` (e.g. with `BenchmarkSample` and `BenchmarkResult`) actually correct?**
  _`AgenticRAG` has 181 INFERRED edges - model-reasoned connections that need verification._
- **Are the 177 inferred relationships involving `SearchTool` (e.g. with `SearchAgent` and `Search Agent — агент поиска с Tool Calling`) actually correct?**
  _`SearchTool` has 177 INFERRED edges - model-reasoned connections that need verification._