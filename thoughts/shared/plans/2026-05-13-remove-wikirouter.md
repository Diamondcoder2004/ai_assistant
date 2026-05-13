# Remove WikiRouter — Implementation Plan

**Goal:** Remove the entire WikiRouter module and all references throughout the codebase. Clean removal without vestigial parameters.

**Pipeline after removal:** `User Query → QueryGenerator → SearchAgent → ResponseAgent`

**Design:** `thoughts/shared/designs/2026-05-13-remove-wikirouter-design.md`

**Gap-filling decisions:**
1. **Additional test files:** Design listed 4 test files, but scanning reveals 7 test files import from `wiki.*` — all must be deleted since the entire wiki module is removed.
2. **Additional edit file:** `backend/agents/query_generator.py` has a `wiki_context` parameter (lines 72, 104) — must be removed to complete the chain. Design implicitly handles this via search_agent.py removing its calls to it, but for cleanliness we remove the param too.
3. **`document_filters` kept:** Though dead code (always `None`), design doesn't mention removing it, so it stays as an optional parameter with default `None` in `search_agent.py`.

---

## Dependency Graph

```
Batch 1 (parallel — 4 implementers): 1.1, 1.2, 1.3, 1.4 [deletions + config — no deps]
Batch 2 (parallel — 5 implementers): 2.1, 2.2, 2.3, 2.4, 2.5 [wiki_context param chain — no deps between files]
Batch 3 (parallel — 2 implementers): 3.1, 3.2 [main.py + benchmark — depend on batch 1 + 2]
Batch 4 (verification — 1 implementer): 4.1 [pytest — depends on all prior]
```

---

## Batch 1: Foundations — Deleting & Config (parallel — 4 implementers)

All tasks in this batch have NO dependencies and run simultaneously.

### Task 1.1: Delete entire `backend/wiki/` directory
**File:** `backend/wiki/` (DELETE)
**Test:** none
**Depends:** none

**Implementation:**
```bash
# Remove the entire wiki directory
Remove-Item -Recurse -Force -LiteralPath "backend/wiki"
```

**Verify:** `Test-Path -LiteralPath "backend/wiki"` → `False`
**Commit:** `chore(wiki): delete entire wiki module directory`

### Task 1.2: Delete all wiki-related test files (7 files)
**Files (DELETE):**
1. `backend/tests/test_wiki_router.py`
2. `backend/tests/test_wiki_search_tool.py`
3. `backend/tests/test_wiki_cleanup.py`
4. `backend/tests/test_wiki_models.py`
5. `backend/tests/test_wiki_config.py`
6. `backend/tests/test_main_wiki_integration.py`
7. `backend/tests/test_build_index.py`

**Depends:** none

**Implementation:**
```bash
# Delete all wiki test files
Remove-Item -Force -LiteralPath "backend/tests/test_wiki_router.py"
Remove-Item -Force -LiteralPath "backend/tests/test_wiki_search_tool.py"
Remove-Item -Force -LiteralPath "backend/tests/test_wiki_cleanup.py"
Remove-Item -Force -LiteralPath "backend/tests/test_wiki_models.py"
Remove-Item -Force -LiteralPath "backend/tests/test_wiki_config.py"
Remove-Item -Force -LiteralPath "backend/tests/test_main_wiki_integration.py"
Remove-Item -Force -LiteralPath "backend/tests/test_build_index.py"
```

**Note:** Design listed 4 test files, but scanning found 7 total that import from `wiki.*`. All must be deleted to avoid `ModuleNotFoundError` when running pytest.

**Verify:** `Get-ChildItem -Path "backend/tests" -Filter "*wiki*"` → empty; `Test-Path -LiteralPath "backend/tests/test_build_index.py"` → `False`
**Commit:** `chore(tests): delete all wiki-related test files (7 files)`

### Task 1.3: Edit `.env` — remove WikiRouter env vars
**File:** `.env`
**Test:** none
**Depends:** none

**Changes:** Remove the entire `LLM Wiki Router` section (lines 66-71) — 3 lines of actual content plus header.

**Implementation — edit `.env`:**

Delete lines 66-71:

```
# ===========================================
# LLM Wiki Router (Karpathy-style Knowledge Graph)
# ===========================================
ENABLE_WIKI_ROUTER=false
# WIKI_TABLE_NAME=wiki_concepts
# WIKI_TOP_K_CONCEPTS=3
```

Result: The section header comment block and 3 lines removed.

**Verify:** `Select-String -Path ".env" -Pattern "WIKI"` → 0 matches
**Commit:** `chore(config): remove WikiRouter env vars from .env`

### Task 1.4: Edit `backend/config.py` — remove WikiRouter section
**File:** `backend/config.py`
**Test:** none (test_wiki_config.py is deleted in Task 1.2)
**Depends:** none

**Changes:** Remove the `WIKI ROUTER` section (lines 99-107).

**Implementation — edit `backend/config.py`:**

Old (lines 99-107):
```python
# =============================================================================
# WIKI ROUTER (JSON-based Agentic Knowledge Layer)
# =============================================================================

ENABLE_WIKI_ROUTER = os.getenv("ENABLE_WIKI_ROUTER", "true").lower() == "true"
WIKI_INDEX_PATH = Path(os.getenv("WIKI_INDEX_PATH", str(BASE_DIR / "wiki" / "data" / "index.json")))
WIKI_ROUTER_MODEL = os.getenv("WIKI_ROUTER_MODEL", "inception/mercury-2")
WIKI_TOP_K = int(os.getenv("WIKI_TOP_K", "3"))  # LLM-selected documents
WIKI_SEARCH_TOP_K = int(os.getenv("WIKI_SEARCH_TOP_K", "5"))  # Keyword candidates before LLM
```

New — removed entirely.

**Verify:** `Select-String -Path "backend/config.py" -Pattern "WIKI"` → 0 matches
**Commit:** `chore(config): remove WikiRouter config section`

---

## Batch 2: Remove `wiki_context` Parameter Chain (parallel — 5 implementers)

All tasks in this batch edit ONE file each, removing `wiki_context` from that file's scope. They can all run in parallel because each edit is self-contained within its file. The parameter chain is broken atomically since each file independently removes its own `wiki_context` references.

### Task 2.1: Edit `backend/prompts/query_generation.py` — remove WIKI_CONTEXT_TEMPLATE
**File:** `backend/prompts/query_generation.py`
**Test:** none
**Depends:** none (internal prompt file, no callers execute before batch 2 completes)

**Changes:**
1. Remove `WIKI_CONTEXT_TEMPLATE` constant (lines 158-163)
2. Remove `wiki_context` parameter from `get_query_generation_prompt()` (line 171)
3. Remove `wiki_context: Контекст из LLM Wiki` from docstring (line 181)
4. Remove `wiki_section` logic (lines 198-200)
5. Simplify `context` building — `context + wiki_section` → just `context`

**Implementation — edit `backend/prompts/query_generation.py`:**

1. Remove the prompt text about wiki:

Old (line 16): 
```
- **Контекст Wiki — ТВОЙ ГЛАВНЫЙ ПОМОЩНИК.** Используй термины, ключевые слова и правила из Wiki для генерации ТОЧНЫХ запросов. Wiki знает бизнес-логику Башкирэнерго — доверяй ей.
```

New:
```
- Используй термины, ключевые слова из контекста для генерации ТОЧНЫХ запросов.
```

2. Remove the prompt text at line 40:
Old:
```
    - **ИСПОЛЬЗУЙ термины из Wiki-контекста** (если предоставлен) — это гарантирует попадание в нужные документы.
```
New:
```
    - Это гарантирует попадание в нужные документы.
```

3. Remove `WIKI_CONTEXT_TEMPLATE` constant block (lines 158-163).

4. Remove `wiki_context: str = ""` from function signature (line 171), remove `wiki_context` from docstring (line 181).

5. Remove lines 198-200 (wiki_section building), change line 204 to use `context` directly instead of `context + wiki_section`.

Final function (after edits):

```python
def get_query_generation_prompt(
    user_query: str,
    history: str = "",
    category: str = "не известна",
    user_hints: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Формирует промпт для генерации поисковых запросов.

    Args:
        user_query: Вопрос пользователя
        history: История диалога
        category: Категория клиента
        user_hints: Рекомендации от пользователя

    Returns:
        Промпт для генерации запросов
    """
    context = ""
    if history or category:
        context = CONTEXT_TEMPLATE.format(
            history=history if history else "нет истории",
            category=category if category else "не известна"
        )

    user_hints_section = ""
    if user_hints:
        hints_text = ", ".join(f"{k}={v}" for k, v in user_hints.items())
        user_hints_section = USER_HINTS_TEMPLATE.format(user_hints=hints_text)

    return QUERY_GENERATION_PROMPT.format(
        user_query=user_query,
        context=context,
        user_hints_section=user_hints_section
    )
```

**Verify:** `python -c "from prompts.query_generation import get_query_generation_prompt; print('OK')"` run from `backend/` directory succeeds.
**Commit:** `refactor(prompts): remove WIKI_CONTEXT_TEMPLATE and wiki_context param from query_generation`

### Task 2.2: Edit `backend/agents/query_generator.py` — remove `wiki_context` param
**File:** `backend/agents/query_generator.py`
**Test:** none
**Depends:** none (but reference `get_query_generation_prompt` without wiki_context from 2.1)

**Changes:**
1. Remove `wiki_context: str = ""` from `generate()` signature (line 72)
2. Remove `wiki_context` from docstring (line 86)
3. Remove `wiki_context=wiki_context` from `get_query_generation_prompt()` call (line 104)

**Implementation — edit `backend/agents/query_generator.py`:**

Old (lines 64-105):
```python
    def generate(
        self,
        user_query: str,
        history: str = "",
        category: str = "не известна",
        temperature: float = 0.7,
        max_attempts: int = 3,
        user_hints: Optional[Dict[str, Any]] = None,
        wiki_context: str = "",
        query_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> QueryGenerationResult:
        """
        Генерация поисковых запросов.

        Args:
            user_query: Вопрос пользователя
            history: История диалога
            category: Категория клиента
            temperature: Температура генерации
            max_attempts: Максимальное количество попыток
            user_hints: Рекомендации от пользователя (k, temperature, и т.д.)
            wiki_context: Контекст из LLM Wiki (опционально)
            query_id: Уникальный ID запроса (для логирования)
            session_id: ID сессии (для логирования)

        Returns:
            Результат генерации запросов
        """
        import uuid

        _query_id = query_id or str(uuid.uuid4())
        _session_id = session_id or "unknown"
        _start_time = time.time()

        prompt = get_query_generation_prompt(
            user_query=user_query,
            history=history,
            category=category,
            user_hints=user_hints,  # Передаём рекомендации
            wiki_context=wiki_context  # Передаём контекст Wiki
        )
```

New:
```python
    def generate(
        self,
        user_query: str,
        history: str = "",
        category: str = "не известна",
        temperature: float = 0.7,
        max_attempts: int = 3,
        user_hints: Optional[Dict[str, Any]] = None,
        query_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> QueryGenerationResult:
        """
        Генерация поисковых запросов.

        Args:
            user_query: Вопрос пользователя
            history: История диалога
            category: Категория клиента
            temperature: Температура генерации
            max_attempts: Максимальное количество попыток
            user_hints: Рекомендации от пользователя (k, temperature, и т.д.)
            query_id: Уникальный ID запроса (для логирования)
            session_id: ID сессии (для логирования)

        Returns:
            Результат генерации запросов
        """
        import uuid

        _query_id = query_id or str(uuid.uuid4())
        _session_id = session_id or "unknown"
        _start_time = time.time()

        prompt = get_query_generation_prompt(
            user_query=user_query,
            history=history,
            category=category,
            user_hints=user_hints,
        )
```

**Verify:** `python -c "from agents.query_generator import QueryGeneratorAgent; print('OK')"` run from `backend/` directory succeeds.
**Commit:** `refactor(query_generator): remove wiki_context parameter`

### Task 2.3: Edit `backend/agents/search_agent.py` — remove `wiki_context` param
**File:** `backend/agents/search_agent.py`
**Test:** none
**Depends:** none (but reference query_generator without wiki_context from 2.2)

**Changes:**
1. Remove `wiki_context: str = ""` from `search()` signature (line 52)
2. Remove `wiki_context: Контекст из LLM Wiki` from docstring (line 69)
3. Remove `wiki_context=wiki_context,` from `query_generator.generate()` calls (lines 119, 137)

**Implementation — edit `backend/agents/search_agent.py`:**

Old lines 44-58:
```python
    def search(
        self,
        user_query: str,
        history: str = "",
        category: str = "не известна",
        auto_retry: bool = True,
        max_retries: int = 2,
        user_hints: Optional[Dict[str, Any]] = None,
        wiki_context: str = "",
        query_id: Optional[str] = None,
        session_id: Optional[str] = None,
        session_logger: Optional[Any] = None,
        document_filters: Optional[Dict[str, List[str]]] = None,
        skip_query_generator: bool = False,
    ) -> Dict[str, Any]:
```

New:
```python
    def search(
        self,
        user_query: str,
        history: str = "",
        category: str = "не известна",
        auto_retry: bool = True,
        max_retries: int = 2,
        user_hints: Optional[Dict[str, Any]] = None,
        query_id: Optional[str] = None,
        session_id: Optional[str] = None,
        session_logger: Optional[Any] = None,
        document_filters: Optional[Dict[str, List[str]]] = None,
        skip_query_generator: bool = False,
    ) -> Dict[str, Any]:
```

Old docstring (line 69): `wiki_context: Контекст из LLM Wiki (опционально)` → remove this line

Old line 119:
```python
                        wiki_context=wiki_context,
```
→ Remove.

Old line 137:
```python
                    wiki_context=wiki_context,
```
→ Remove.

**Verify:** `python -c "from agents.search_agent import SearchAgent; print('OK')"` run from `backend/` directory succeeds.
**Commit:** `refactor(search_agent): remove wiki_context parameter`

### Task 2.4: Edit `backend/agents/response_agent.py` — remove `wiki_context` param
**File:** `backend/agents/response_agent.py`
**Test:** none
**Depends:** none

**Changes:**
1. Remove `wiki_context: str = ""` from `generate_response()` signature (line 124)
2. Remove `wiki_context: Контекст из LLM Wiki` from docstring (line 141)
3. Remove `wiki_context=wiki_context,` from `_create_user_prompt()` call (line 178)
4. Remove `wiki_context: str = ""` from `_create_user_prompt()` signature (line 312)
5. Remove wiki_section logic (lines 316-318)
6. Simplify `_create_user_prompt` return value — replace `{wiki_section}{context}` with `{context}`

**Implementation — edit `backend/agents/response_agent.py`:**

Old lines 116-130:
```python
    def generate_response(
        self,
        user_query: str,
        search_results: List[SearchResult],
        history: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2000,
        user_hints: Optional[Dict[str, Any]] = None,
        wiki_context: str = "",
        source_quality: Optional[Dict[str, Any]] = None,
        search_agent_confidence: Optional[float] = None,
        query_id: Optional[str] = None,
        session_id: Optional[str] = None,
        session_logger: Optional[Any] = None
    ) -> Dict[str, Any]:
```

Remove `wiki_context: str = "",` from the signature (line 124). Remove `wiki_context: Контекст из LLM Wiki (опционально)` from docstring (line 141).

Old line 178: `wiki_context=wiki_context,` → remove.

Old lines 306-318:
```python
    def _create_user_prompt(
        self,
        user_query: str,
        context: str,
        history: str,
        user_hints: Optional[Dict[str, Any]] = None,
        wiki_context: str = "",
        source_quality: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Создание пользовательского промпта."""
        wiki_section = ""
        if wiki_context:
            wiki_section = f"\n{wiki_context}\n"
```

New:
```python
    def _create_user_prompt(
        self,
        user_query: str,
        context: str,
        history: str,
        user_hints: Optional[Dict[str, Any]] = None,
        source_quality: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Создание пользовательского промпта."""
```

Old return value (line 340-357):
```python
        return f"""
{history}

{wiki_section}{context}

{low_quality_warning}---
Вопрос пользователя: {user_query}
...
"""
```

New:
```python
        return f"""
{history}

{context}

{low_quality_warning}---
Вопрос пользователя: {user_query}

Используя приведённую выше информацию из базы знаний, дай точный и развёрнутый ответ на вопрос.

ВАЖНО: При ссылке на источник используй ТОЛЬКО цифру в квадратных скобках:
- ✅ ПРАВИЛЬНО: [1], [2], [3], [1][3]
- ❌ НЕПРАВИЛЬНО: "источник 1", "источник [1]", "[src_1]"

Пример: "согласно документу [1] и инструкции [2][3]..."

Если информации недостаточно, честно скажи об этом.
"""
```

**Verify:** `python -c "from agents.response_agent import ResponseAgent; print('OK')"` run from `backend/` directory succeeds.
**Commit:** `refactor(response_agent): remove wiki_context parameter and wiki_section logic`

### Task 2.5: Update `QUERY_GENERATION_PROMPT` — remove wiki references from prompt text
**File:** `backend/prompts/query_generation.py`
**Test:** none
**Depends:** none

Also remove wiki-related instructions from the prompt template text itself.

**Changes to prompt text:**

Line 16, replace:
```
- **Контекст Wiki — ТВОЙ ГЛАВНЫЙ ПОМОЩНИК.** Используй термины, ключевые слова и правила из Wiki для генерации ТОЧНЫХ запросов. Wiki знает бизнес-логику Башкирэнерго — доверяй ей.
```
With:
```
- Используй термины и ключевые слова для генерации ТОЧНЫХ запросов.
```

Line 40, replace:
```
    - **ИСПОЛЬЗУЙ термины из Wiki-контекста** (если предоставлен) — это гарантирует попадание в нужные документы.
```
With:
```
    - Используй точные термины и синонимы — это гарантирует попадание в нужные документы.
```

**Note:** This task could be merged with Task 2.1 since it edits the same file. But since they are logically separate concerns (function signature vs. prompt text), they remain separate for clarity. If implementing in sequence, do Task 2.1 first, then Task 2.5.

**Verify:** Python syntax check passes.
**Commit:** `refactor(prompts): remove wiki references from QUERY_GENERATION_PROMPT text`

---

## Batch 3: Integration Layer (parallel — 2 implementers)

These tasks depend on ALL Batch 1 and Batch 2 tasks completing first.

### Task 3.1: Edit `backend/main.py` — remove all WikiRouter references
**File:** `backend/main.py`
**Test:** none
**Depends:** 1.1 (wiki directory deleted), 1.2 (test files deleted), 1.4 (config vars removed), 2.3 (search_agent wiki_context removed), 2.4 (response_agent wiki_context removed)

**Changes:**
1. Remove `from wiki.wiki_router import WikiRouterAgent` import (line 15)
2. Remove `self.wiki_router = WikiRouterAgent()` from `__init__` (line 48)
3. Update logger message: remove "(Wiki Router включён)" (line 51)
4. Update docstring: remove step 0 (WikiRouter) (lines 39-42)
5. Remove `skip_wiki_router: bool = False` from `query()` signature (line 63)
6. Remove `skip_wiki_router: Пропустить WikiRouter` from docstring (lines 74-75)
7. Remove the entire WikiRouter block (lines 112-154, the try/except with `route_with_fallback`, `wiki_context`, `wiki_context_short`, `document_filters`)
8. Remove `wiki_context=wiki_context_short,` from `search_agent.search()` call (line 173)
9. Remove `document_filters=document_filters,` from `search_agent.search()` call (line 174)
10. Remove `wiki_context=wiki_context,` from `response_agent.generate_response()` call (line 236)

**Implementation — final `backend/main.py`:**

```python
"""
Agentic RAG — точка входа
"""
import logging
import argparse
import uuid
import time
from datetime import datetime
from typing import Optional, List, Dict, Any

import config
from agents.search_agent import SearchAgent
from agents.response_agent import ResponseAgent
from prompts.system_prompt import get_system_prompt
from utils.bg_cache_loader import schedule_bm25_warmup
from utils.agent_debug_logger import get_debug_logger
from utils.langfuse_tracer import observe_rag

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format=config.LOG_FORMAT,
    datefmt=config.LOG_DATE_FORMAT,
    handlers=[
        logging.FileHandler(config.LOGS_DIR / f"agent_{config.DEFAULT_LLM_MODEL.replace('/', '_')}.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
debug_logger = get_debug_logger()


class AgenticRAG:
    """
    Основной класс Agentic RAG системы.
    
    Объединяет всех агентов для полного цикла обработки запроса:
    1. Генерация поисковых запросов
    2. Поиск в базе знаний
    3. Формирование ответа
    """
    
    def __init__(self):
        self.search_agent = SearchAgent()
        self.response_agent = ResponseAgent()
        self.history = ""
        self.category = "не известна"
        logger.info("AgenticRAG инициализирован")
        
        # Фоновая загрузка BM25 кэша
        schedule_bm25_warmup(delay=1.0)
    
    @observe_rag(name="AgenticRAG.query")
    def query(
        self,
        user_query: str,
        auto_retry: bool = True,
        history: List[Dict[str, str]] = None,
        user_hints: Optional[Dict[str, Any]] = None,
        skip_query_generator: bool = True,
    ) -> dict:
        """
        Обработка запроса пользователя.

        Args:
            user_query: Вопрос пользователя
            auto_retry: Автоматическая повторная попытка поиска
            history: История диалога (список сообщений)
            user_hints: Рекомендации от пользователя (k, temperature, и т.д.)
            skip_query_generator: Пропустить QueryGenerator (поиск по сырому запросу)

        Returns:
            Словарь с результатом:
            - answer: текст ответа
            - clarification_needed: bool
            - clarification_questions: List[str]
            - sources: список источников
            - queries_used: использованные запросы
            - confidence: уверенность
        """
        query_id = str(uuid.uuid4())
        session_id = history[0].get("session_id", "unknown") if history else "unknown"
        start_time = time.time()
        
        # Формируем session_id для логирования
        log_session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        logger.info(f"Запрос: '{user_query[:50]}...'")
        if user_hints:
            logger.info(f"Рекомендации от пользователя: {user_hints}")

        # Создаём логгер сессии
        session_logger = debug_logger.create_session_log(log_session_id, user_query)

        # Оптимизация истории: берём только последние 4 сообщения (2 диалога)
        # Это нужно, чтобы QueryGenerator не терялся в большом контексте
        dialog_history = ""
        if history:
            # Берём последние 4 сообщения (последний вопрос + ответ + предыдущий вопрос + ответ)
            recent_history = history[-4:] if len(history) > 4 else history
            for msg in recent_history:
                role = "Пользователь" if msg["role"] == "user" else "Ассистент"
                dialog_history += f"{role}: {msg['content']}\n"
        else:
            dialog_history = self.history

        try:
            # 1. Поиск с использованием Search Agent
            with session_logger.step(
                "SearchAgent", 
                "search",
                {
                    "query": user_query,
                    "history_length": len(dialog_history),
                    "category": self.category,
                    "user_hints": user_hints or {}
                }
            ) as search_step:
                search_result = self.search_agent.search(
                    user_query=user_query,
                    history=dialog_history,
                    category=self.category,
                    auto_retry=auto_retry,
                    user_hints=user_hints,
                    query_id=query_id,
                    session_id=session_id,
                    session_logger=session_logger,
                    skip_query_generator=skip_query_generator,
                )
                
                search_step.set_output({
                    "clarification_needed": search_result["clarification_needed"],
                    "queries_used": search_result.get("queries_used", []),
                    "search_params": search_result.get("search_params", {}),
                    "results_count": len(search_result.get("results", [])),
                    "confidence": search_result.get("confidence", 0),
                    "top_sources": [
                        {
                            "filename": r.filename,
                            "breadcrumbs": r.breadcrumbs,
                            "score_hybrid": r.score_hybrid,
                            "score_semantic": r.score_semantic,
                            "score_lexical": r.score_lexical
                        }
                        for r in search_result.get("results", [])[:10]
                    ]
                }, {
                    "all_results_count": len(search_result.get("results", []))
                })

            # 2. Проверка необходимости уточнения
            if search_result["clarification_needed"]:
                clarification_response = self.response_agent.generate_clarification_response(
                    user_query=user_query,
                    clarification_questions=search_result["clarification_questions"]
                )

                session_logger.set_final_answer(clarification_response, 0)
                session_logger.save()

                return {
                    "answer": clarification_response,
                    "clarification_needed": True,
                    "clarification_questions": search_result["clarification_questions"],
                    "sources": [],
                    "queries_used": [],
                    "confidence": search_result["confidence"]
                }

            # 3. Генерация ответа с использованием Response Agent
            with session_logger.step(
                "ResponseAgent",
                "generate",
                {
                    "query": user_query,
                    "sources_count": len(search_result["results"]),
                    "history_length": len(dialog_history)
                }
            ) as response_step:
                response_result = self.response_agent.generate_response(
                    user_query=user_query,
                    search_results=search_result["results"],
                    history=dialog_history,
                    max_tokens=user_hints.get("max_tokens", 2000) if user_hints else 2000,
                    user_hints=user_hints,
                    source_quality=search_result.get("source_quality"),
                    search_agent_confidence=search_result.get("confidence"),
                    query_id=query_id,
                    session_id=session_id,
                    session_logger=session_logger
                )
                
                response_step.set_output({
                    "answer_length": len(response_result["answer"]),
                    "answer_preview": response_result["answer"][:500] + "..." if len(response_result["answer"]) > 500 else response_result["answer"],
                    "sources_used": len(response_result["sources"]),
                    "confidence": response_result["confidence"]
                })

            # 4. Обновление истории
            self._update_history(user_query, response_result["answer"])

            # Логирование ответа
            logger.info(f"[OK] LLM ответ (длина: {len(response_result['answer'])}): {response_result['answer'][:200]}...")
            logger.info(f"   Источники: {len(response_result['sources'])} шт.")
            logger.info(f"   Уверенность: {response_result['confidence']:.2f}")

            # Сохраняем финальный ответ
            session_logger.set_final_answer(response_result["answer"], len(response_result["sources"]))
            session_logger.save()

            # 5. Формирование результата
            return {
                "answer": response_result["answer"],
                "clarification_needed": False,
                "clarification_questions": [],
                "sources": response_result["sources"],
                "queries_used": search_result["queries_used"],
                "search_params": search_result["search_params"],
                "confidence": response_result["confidence"],
                "reasoning": search_result.get("reasoning", "")
            }
            
        except Exception as e:
            logger.error(f"Error in query: {e}", exc_info=True)
            session_logger.add_error(str(e))
            session_logger.save()
            raise
    
    # _update_history, set_category, reset_history, get_system_prompt remain unchanged
    # main() function remains unchanged
```

Note: `_update_history()`, `set_category()`, `reset_history()`, `get_system_prompt()` methods and the `main()` function remain exactly as before.

**Verify:** `python -c "from main import AgenticRAG; print('OK')"` run from `backend/` directory succeeds.
**Commit:** `refactor(main): remove WikiRouter integration — import, init, query param, and WikiRouter block`

### Task 3.2: Edit `backend/benchmark.py` — remove `skip_wiki_router`
**File:** `backend/benchmark.py`
**Test:** none
**Depends:** 3.1 (main.py's query() no longer accepts skip_wiki_router)

**Changes:**
1. Remove `skip_wiki_router: bool = False` from `BenchmarkSample` — wait, `BenchmarkSample` is a dataclass. The design says:
   - Remove `skip_wiki_router` from `Benchmark.__init__` and `BenchmarkSample`
   - Remove `--no-wiki` argparse argument
   - Remove `skip_wiki_router` from `rag.query()` call

Actually, looking at the code, `BenchmarkSample` doesn't have `skip_wiki_router`. It's `AgenticRAGBenchmark.__init__` that has it:

```python
def __init__(
    self,
    samples: List[BenchmarkSample],
    use_llm_judge: bool = True,
    skip_wiki_router: bool = False,
    skip_query_generator: bool = False,
):
```

So:
1. Remove `skip_wiki_router: bool = False` from `AgenticRAGBenchmark.__init__` (line 95)
2. Remove `self.skip_wiki_router = skip_wiki_router` (line 102)
3. Remove `skip_wiki_router=self.skip_wiki_router,` from `rag.query()` call (line 186)
4. Remove `--no-wiki` argparse argument (lines 479-480)
5. Remove `skip_wiki_router=args.no_wiki,` from `AgenticRAGBenchmark()` construction (line 514)

**Implementation — edit `backend/benchmark.py`:**

Old lines 91-103:
```python
    def __init__(
        self,
        samples: List[BenchmarkSample],
        use_llm_judge: bool = True,
        skip_wiki_router: bool = False,
        skip_query_generator: bool = False,
    ):
        self.samples = samples
        self.rag = AgenticRAG()
        self.llm_judge = LLMJudge() if use_llm_judge else None
        self.use_llm_judge = use_llm_judge
        self.skip_wiki_router = skip_wiki_router
        self.skip_query_generator = skip_query_generator
```

New:
```python
    def __init__(
        self,
        samples: List[BenchmarkSample],
        use_llm_judge: bool = True,
        skip_query_generator: bool = False,
    ):
        self.samples = samples
        self.rag = AgenticRAG()
        self.llm_judge = LLMJudge() if use_llm_judge else None
        self.use_llm_judge = use_llm_judge
        self.skip_query_generator = skip_query_generator
```

Old line 180 (comment):
```
        # Полный запрос через AgenticRAG.query() — включает WikiRouter + Search + Response
```
New:
```
        # Полный запрос через AgenticRAG.query() — включает Search + Response
```

Old lines 183-188:
```python
            response = self.rag.query(
                sample.question,
                auto_retry=True,
                skip_wiki_router=self.skip_wiki_router,
                skip_query_generator=self.skip_query_generator,
            )
```
New:
```python
            response = self.rag.query(
                sample.question,
                auto_retry=True,
                skip_query_generator=self.skip_query_generator,
            )
```

Old lines 479-480:
```python
    parser.add_argument("--no-wiki", action="store_true",
                        help="Пропустить WikiRouter (поиск без document context)")
```
→ Remove both lines.

Old lines 511-516:
```python
    benchmark = AgenticRAGBenchmark(
        samples,
        use_llm_judge=use_judge,
        skip_wiki_router=args.no_wiki,
        skip_query_generator=args.no_query_gen,
    )
```
New:
```python
    benchmark = AgenticRAGBenchmark(
        samples,
        use_llm_judge=use_judge,
        skip_query_generator=args.no_query_gen,
    )
```

**Verify:** `python -c "from benchmark import AgenticRAGBenchmark; print('OK')"` run from `backend/` directory succeeds.
**Commit:** `refactor(benchmark): remove skip_wiki_router param and --no-wiki arg`

---

## Batch 4: Verification (1 implementer)

### Task 4.1: Run pytest and verify import integrity
**File:** none (verification only)
**Depends:** ALL prior tasks

**Implementation:**
```bash
cd backend
pytest
```

Expected: All remaining tests pass. The deleted wiki test files won't be found (since deleted). Integration tests that relied on wiki are gone.

Also verify the import chain works:
```bash
cd backend
python -c "
from main import AgenticRAG
from agents.search_agent import SearchAgent
from agents.response_agent import ResponseAgent
from agents.query_generator import QueryGeneratorAgent
from prompts.query_generation import get_query_generation_prompt
print('All imports OK — WikiRouter fully removed')
"
```

**Verify:** `pytest` exit code = 0 (all tests pass). Import chain succeeds.
**Commit:** `chore: verify WikiRouter removal — all tests pass`

---

## Summary of All Changes

### Files DELETED (8)
| # | Path | Reason |
|---|------|--------|
| 1 | `backend/wiki/` (entire directory) | Core WikiRouter module |
| 2 | `backend/tests/test_wiki_router.py` | WikiRouter unit tests |
| 3 | `backend/tests/test_wiki_search_tool.py` | WikiSearchTool unit tests |
| 4 | `backend/tests/test_wiki_cleanup.py` | Cleanup tests for legacy modules |
| 5 | `backend/tests/test_wiki_models.py` | Wiki data model tests |
| 6 | `backend/tests/test_wiki_config.py` | Wiki config tests |
| 7 | `backend/tests/test_main_wiki_integration.py` | Wiki integration tests |
| 8 | `backend/tests/test_build_index.py` | Wiki index builder tests |

### Files EDITED (8)
| # | File | Key Change |
|---|------|------------|
| 1 | `.env` | Remove ENABLE_WIKI_ROUTER + 2 commented WIKI lines |
| 2 | `backend/config.py` | Remove entire WIKI ROUTER section (5 vars) |
| 3 | `backend/prompts/query_generation.py` | Remove WIKI_CONTEXT_TEMPLATE, wiki_context param, wiki refs in prompt text |
| 4 | `backend/agents/query_generator.py` | Remove wiki_context param from generate() |
| 5 | `backend/agents/search_agent.py` | Remove wiki_context param from search(), remove from query_generator calls |
| 6 | `backend/agents/response_agent.py` | Remove wiki_context from both methods, remove wiki_section logic |
| 7 | `backend/main.py` | Remove import, init, skip_wiki_router, entire WikiRouter block, wiki_context from calls |
| 8 | `backend/benchmark.py` | Remove skip_wiki_router from __init__ and _evaluate_sample, remove --no-wiki arg |

### Pipeline Simplification

Before:
```
User Query → WikiRouter → QueryGenerator → SearchAgent → ResponseAgent
```

After:
```
User Query → QueryGenerator → SearchAgent → ResponseAgent
```

- One fewer LLM call per query (~`inception/mercury-2`)
- ~0.5s latency saved
- No config surface area for wiki
- Cleaner codebase with no dead data
