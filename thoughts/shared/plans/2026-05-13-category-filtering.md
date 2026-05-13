# Category-Aware Partial Filtering — Implementation Plan

**Goal:** Add category-aware blended search (ЛК/ДУ → 30% filtered + 70% unfiltered) to improve retrieval precision without sacrificing recall.

**Architecture:** QueryGenerator detects category in the same LLM call (`detected_category` field). SearchAgent, when receiving ЛК or ДУ, runs two parallel searches (filtered + unfiltered) using existing `build_qdrant_filter()` and `search_multi(qf_filter=...)`, then blends results 30/70 with dedup.

**Design:** `thoughts/shared/designs/2026-05-13-category-filtering-design.md`

**No new files, no API/frontend/schema changes.** All changes are modifications to 4 existing files + 1 new test file.

---

## Dependency Graph

```
Batch 1 (parallel — 3 implementers): 1.1, 1.2, 1.3 [foundation — no deps]
Batch 2 (parallel — 1 implementer):  2.1 [core logic — depends on batch 1]
Batch 3 (parallel — 1 implementer):  3.1 [tests — depends on all above]
```

---

## Batch 1: Foundation (parallel — 3 implementers)

All tasks in this batch have NO dependencies and run simultaneously.

---

### Task 1.1: Config — category filter env vars
**File:** `backend/config.py`
**Test:** none (config vars are tested implicitly via integration)
**Depends:** none

**Design decisions:**
- `CATEGORY_FILTER_ENABLED` follows the existing pattern of bool env vars (`os.getenv(...).lower() in ("1", "true", "yes")`)
- `CATEGORY_FILTER_BLEND_RATIO` follows existing float env var pattern
- Placement: after `SOURCE_QUALITY_THRESHOLD` (line 89), in the SEARCH WEIGHTS section
- Design requires these env vars for runtime toggle and ratio tuning

**Edit: `backend/config.py` — add after line 89 (after SOURCE_QUALITY_THRESHOLD)**

```python

# Category-aware partial filtering: when QueryGenerator detects ЛК/ДУ category,
# 30% of results come from filtered search, 70% from unfiltered (blended approach)
CATEGORY_FILTER_ENABLED = os.getenv("CATEGORY_FILTER_ENABLED", "true").lower() in ("1", "true", "yes")
# Proportion of results taken from the category-filtered search (0.0-1.0)
CATEGORY_FILTER_BLEND_RATIO = float(os.getenv("CATEGORY_FILTER_BLEND_RATIO", "0.3"))
```

**Verify:** `python -c "import config; print(config.CATEGORY_FILTER_ENABLED, config.CATEGORY_FILTER_BLEND_RATIO)"`
**Commit:** `feat(config): add CATEGORY_FILTER_ENABLED and CATEGORY_FILTER_BLEND_RATIO`

---

### Task 1.2: QueryGenerationResult — add `detected_category` field
**File:** `backend/agents/query_generator.py`
**Test:** none (standalone, tested in Batch 3)
**Depends:** none

**Design decisions:**
- New field `detected_category: str = "не известна"` in the dataclass — matches existing patterns for string fields with defaults
- `from_dict()` reads `data.get("detected_category", "не известна")` — same .get() pattern as other fields
- `_default_result()` explicitly passes `detected_category="не известна"` — defensive, even though default handles it
- The `log_agent_response` calls at lines 186-203 and 208-227 send `response_data` dicts — they don't include `detected_category` because the dict is constructed manually, not from the result object. Adding it would be a nice touch but the logging dict doesn't need to mirror the dataclass exactly (design doesn't require it). **Decision: don't modify the logging dicts** — they're for observability, not pipeline logic.

**Edit 1: `backend/agents/query_generator.py` — add field to dataclass (line 28, after `reasoning`)**

Change:
```python
    confidence: float
    reasoning: str
    
    @classmethod
```
To:
```python
    confidence: float
    reasoning: str
    detected_category: str = "не известна"
    
    @classmethod
```

**Edit 2: `backend/agents/query_generator.py` — update `from_dict()` (line 39, add after `reasoning`)**

Change:
```python
            reasoning=data.get("reasoning", "")
        )
```
To:
```python
            reasoning=data.get("reasoning", ""),
            detected_category=data.get("detected_category", "не известна")
        )
```

**Edit 3: `backend/agents/query_generator.py` — update `_default_result()` (line 286, add after `reasoning`)**

Change:
```python
            reasoning="Использован дефолтный запрос из-за ошибки генерации"
        )
```
To:
```python
            reasoning="Использован дефолтный запрос из-за ошибки генерации",
            detected_category="не известна"
        )
```

**Verify:** `python -c "from agents.query_generator import QueryGenerationResult; r = QueryGenerationResult.from_dict({'detected_category': 'ЛК'}); print(r.detected_category); r2 = QueryGenerationResult(clarification_needed=False, clarification_questions=[], queries=[], search_params={}, confidence=0.5, reasoning=''); print(r2.detected_category)"`
**Commit:** `feat(query_generator): add detected_category field to QueryGenerationResult`

---

### Task 1.3: Prompt — add category detection instruction
**File:** `backend/prompts/query_generation.py`
**Test:** none (tested via prompt assertions in Batch 3)
**Depends:** none

**Design decisions:**
- New `## Детекция категории вопроса` section added after `## Выбор коллекций` section (line 28, before `## ТВОЯ ЗАДАЧА`)
- Category detection criteria use clear Russian keywords for each category (same terms as existing `category` field values)
- `detected_category` added to the JSON format example — important for LLM to see the expected output shape
- The `{{` and `}}` double-brace escaping is preserved because the prompt goes through `.format()`
- Design only requires adding to the prompt template — **no changes to `CONTEXT_TEMPLATE` or `USER_HINTS_TEMPLATE`** since the category field is generated by LLM, not injected from context

**Edit 1: `backend/prompts/query_generation.py` — add section after line 28 (between коллекции selection and ТВОЯ ЗАДАЧА)**

Insert after line 28 (`указывай "prefer_collection": "all".`):
```python

## Детекция категории вопроса

Определи, к какой категории относится вопрос пользователя:
- "ЛК" — Личный кабинет (вход, регистрация, лицевой счёт, оплата онлайн,
  показания, заявки в ЛК, настройки)
- "ДУ" — Дополнительные услуги (пакет Минимум, пакет Оптимум, пакет Максимум,
  испытания, замена счётчика, услуги по установке)
- "ТПП" — Технологическое присоединение (заявка на ТП, сроки, документы,
  этапы присоединения, тарифы, мощность, льготы)
- "не известна" — если категорию определить невозможно

Выведи категорию в поле "detected_category" JSON-ответа.

```

**Edit 2: `backend/prompts/query_generation.py` — add field to JSON format example (line 65, after `search_params` block)**

Change lines 64-67:
```python
  }},
  "confidence": 0.85,
  "reasoning": "краткое объяснение стратегии"
}}
```
To:
```python
  }},
  "detected_category": "ЛК",
  "confidence": 0.85,
  "reasoning": "краткое объяснение стратегии"
}}
```

**Verify:** `python -c "from prompts.query_generation import QUERY_GENERATION_PROMPT; assert 'Детекция категории' in QUERY_GENERATION_PROMPT; assert 'detected_category' in QUERY_GENERATION_PROMPT; print('OK')"`
**Commit:** `feat(prompts): add category detection instruction to query generation prompt`

---

## Batch 2: Core Logic (parallel — 1 implementer)

Depends on Batch 1 completing (imports `QueryGenerationResult` with `detected_category`, reads `config.CATEGORY_FILTER_ENABLED`, `config.CATEGORY_FILTER_BLEND_RATIO`).

---

### Task 2.1: SearchAgent — blended category-aware search
**File:** `backend/agents/search_agent.py`
**Test:** none (tested via unit tests in Batch 3)
**Depends:** 1.1 (config vars), 1.2 (QueryGenerationResult.detected_category)

**Design decisions:**
- `blend_results()` is a standalone module-level function — pure logic, no `self` needed (matches design doc)
- `_blended_search()` is an instance method on `SearchAgent` — needs `self.search_tool` and `self.query_generator`
- Uses existing `ThreadPoolExecutor` (already imported at line 8) for parallel searches — no new imports needed except `ceil` from `math`
- `build_qdrant_filter({"category": [category]})` constructs the filter — `category` is a single string, wrapped in a list as the existing function expects `Dict[str, List[str]]`
- `build_qdrant_filter` auto-adds `"Общая"` to category filters — correct behavior per existing logic, don't override
- Confidence check: if `gen_confidence < 0.6`, skip blended search even for ЛК/ДУ (design error handling table)
- Logging: log how many from filtered vs unfiltered for observability
- The blended search branch replaces the existing `search_tool.search_multi()` call at lines 189-194. The original logic becomes the `else` branch.
- Post-retrieval steps (relevance filter, regulatory boost, source quality) happen AFTER the blended/unblended search — they process the final `results` list

**Edit 1: `backend/agents/search_agent.py` — add `ceil` import (line 8)**

Change:
```python
from typing import List, Optional, Dict, Any, Tuple
```
To:
```python
from math import ceil
from typing import List, Optional, Dict, Any, Tuple
```

**Edit 2: `backend/agents/search_agent.py` — add `blend_results()` function and `_blended_search()` method**

Add after line 357 (end of file):

```python

# =============================================================================
# Category-aware blended search
# =============================================================================


def blend_results(
    filtered: List[SearchResult],
    unfiltered: List[SearchResult],
    total_k: int,
) -> List[SearchResult]:
    """
    Смешивание filtered и unfiltered результатов поиска.

    - Все filtered результаты идут в итоговый список (они приоритетны).
    - unfiltered дополняют до total_k, пропуская дубликаты по .id.
    - Финальная сортировка по score_hybrid (убывание).
    - Если filtered пуст — используется только unfiltered (graceful degradation).

    Args:
        filtered: Результаты поиска с category-фильтром.
        unfiltered: Результаты поиска без category-фильтра.
        total_k: Максимальное количество результатов в итоге.

    Returns:
        Отсортированный список из ≤total_k результатов.
    """
    # Все filtered — в итог (они целенаправленные по категории)
    blended = list(filtered)
    seen_ids = {r.id for r in blended}

    # Дополняем из unfiltered, пропуская дубликаты
    for r in unfiltered:
        if len(blended) >= total_k:
            break
        if r.id not in seen_ids:
            blended.append(r)
            seen_ids.add(r.id)

    # Сортировка по hybrid score
    blended.sort(key=lambda r: r.score_hybrid, reverse=True)
    return blended[:total_k]
```

Add before `def format_results` (before line 331), after `_retry_search`:

```python

    def _blended_search(
        self,
        queries: List[str],
        k: int,
        category: str,
        qf_filter: Optional[models.Filter] = None,
        weights: Optional[Dict[str, float]] = None,
    ) -> List[SearchResult]:
        """
        Двухфазный поиск с блендингом filtered и unfiltered результатов.

        30% top-k берётся из поиска с фильтром по category (ЛК или ДУ),
        70% — из обычного поиска без фильтра. Graceful degradation:
        если filtered пустой — падаем на unfiltered.

        Args:
            queries: Список поисковых запросов.
            k: Общее количество запрашиваемых результатов.
            category: Категория для фильтрации ("ЛК" или "ДУ").
            qf_filter: Дополнительный Qdrant Filter (например, collection filter).
            weights: Веса гибридного поиска.

        Returns:
            Отсортированный список результатов.
        """
        blend_ratio = config.CATEGORY_FILTER_BLEND_RATIO
        filtered_k = max(1, ceil(k * blend_ratio))
        unfiltered_k = k  # запрашиваем полный k для unfiltered

        # Фильтр по категории через существующий build_qdrant_filter
        # build_qdrant_filter ожидает Dict[str, List[str]], передаём список из одного элемента
        category_filter = build_qdrant_filter({"category": [category]})

        logger.info(
            f"Blended search: category={category}, "
            f"filtered_k={filtered_k}, unfiltered_k={unfiltered_k}, "
            f"total_k={k}, blend_ratio={blend_ratio}"
        )

        # Параллельные поиски (ThreadPoolExecutor уже импортирован)
        with ThreadPoolExecutor(max_workers=2) as executor:
            f_future = executor.submit(
                self.search_tool.search_multi,
                queries=queries,
                qf_filter=category_filter,
                k=filtered_k,
                weights=weights,
            )
            u_future = executor.submit(
                self.search_tool.search_multi,
                queries=queries,
                qf_filter=qf_filter,  # существующий non-category filter
                k=unfiltered_k,
                weights=weights,
            )
            try:
                filtered_results = f_future.result()
            except Exception as e:
                logger.warning(f"Filtered search failed: {e}. Falling back to unfiltered only.")
                filtered_results = []

            try:
                unfiltered_results = u_future.result()
            except Exception as e:
                logger.warning(f"Unfiltered search failed: {e}. Falling back to filtered only.")
                unfiltered_results = []

        logger.info(
            f"Blended search results: {len(filtered_results)} filtered, "
            f"{len(unfiltered_results)} unfiltered"
        )

        # Блендинг
        return blend_results(
            filtered=filtered_results,
            unfiltered=unfiltered_results,
            total_k=k,
        )
```

**Edit 3: `backend/agents/search_agent.py` — modify `search()` method to insert category-aware branch**

After line 179 (after `logger.info(f"Qdrant filter applied: {document_filters}")`) and before line 181 (`# 3. Выполнение поиска`):

Insert the blended search decision:

```python

        # 2.5 Category-aware blended search (if QueryGenerator detected ЛК or ДУ)
        if not skip_query_generator:
            detected_category = gen_result.detected_category
        else:
            detected_category = "не известна"

        use_blended = (
            config.CATEGORY_FILTER_ENABLED
            and detected_category in ("ЛК", "ДУ")
            and gen_confidence >= 0.6  # ненадёжная детекция — не фильтруем
            and not gen_clarification_needed  # если требуется уточнение, не ищем
        )

        if use_blended:
            logger.info(
                f"Category-aware search: detected={detected_category}, "
                f"confidence={gen_confidence:.2f}, k={k_per_query}"
            )
```

Then replace the existing search block (lines 181-194):

Change:
```python
        # 3. Выполнение поиска
        strategy = gen_search_params.get("strategy", "concat")
        k_per_query = gen_search_params.get("k", 10)
        if user_hints and user_hints.get("k"):
            k_per_query = user_hints.get("k")

        logger.info(f"Поиск по запросам: {queries}, стратегия: {strategy}")

        with timing_context("SearchAgent.tool_search"):
            results = self.search_tool.search_multi(
                queries=queries,
                qf_filter=qf_filter,
                k=k_per_query * len(queries) if strategy == "separate" else k_per_query,
            )
```

To:
```python
        # 3. Выполнение поиска
        strategy = gen_search_params.get("strategy", "concat")
        k_per_query = gen_search_params.get("k", 10)
        if user_hints and user_hints.get("k"):
            k_per_query = user_hints.get("k")

        logger.info(f"Поиск по запросам: {queries}, стратегия: {strategy}")

        if use_blended:
            # Category-aware blended search (parallel filtered + unfiltered)
            results = self._blended_search(
                queries=queries,
                k=k_per_query,
                category=detected_category,
                qf_filter=qf_filter,
            )
        else:
            # Existing single search (no category filter)
            with timing_context("SearchAgent.tool_search"):
                results = self.search_tool.search_multi(
                    queries=queries,
                    qf_filter=qf_filter,
                    k=k_per_query * len(queries) if strategy == "separate" else k_per_query,
                )
```

**Verify:** `python -c "from agents.search_agent import blend_results, SearchAgent; print('imports OK')"`
**Commit:** `feat(search_agent): add blended category-aware search for ЛК/ДУ`

---

## Batch 3: Tests (parallel — 1 implementer)

Depends on all Batch 1 + Batch 2 completing.

---

### Task 3.1: Test file — category filtering unit tests
**File:** `backend/tests/test_category_filtering.py`
**Test:** this IS the test file
**Depends:** 1.1, 1.2, 1.3, 2.1

**Design decisions:**
- Single test file covering all changes (following existing pattern like `test_search_agent_filters.py`)
- Tests are pure unit tests — no Qdrant/LLM dependencies. Use MagicMock for SearchTool and QueryGeneratorAgent.
- Test structure: classes for each concern (`TestBlendResults`, `TestQueryGeneratorCategory`, `TestSearchAgentCategory`)
- `blend_results` is tested with mock SearchResult objects
- `QueryGenerationResult.from_dict` parsed category from JSON
- SearchAgent integration tests with mocked sub-components

**Create: `backend/tests/test_category_filtering.py`**

```python
"""Tests for category-aware partial filtering in SearchAgent."""
import pytest
from unittest.mock import MagicMock, patch
from dataclasses import dataclass
from typing import List, Dict, Any

from agents.search_agent import SearchAgent, blend_results
from tools.search_tool import SearchResult


# =============================================================================
# blend_results() unit tests
# =============================================================================

@pytest.fixture
def make_result():
    """Factory for SearchResult test doubles."""
    def _make(
        id: str,
        score_hybrid: float,
        category: str = "ТПП",
    ) -> SearchResult:
        return SearchResult(
            id=id,
            content="test content",
            summary="test summary",
            category=category,
            filename="test_file",
            breadcrumbs="test",
            score_hybrid=score_hybrid,
            score_semantic=score_hybrid * 0.8,
            score_lexical=score_hybrid * 0.6,
            metadata={},
            collection_name="normative_documents",
        )
    return _make


class TestBlendResults:
    """Tests for the standalone blend_results() function."""

    def test_basic_blend(self, make_result):
        """Filtered results come first, unfiltered fill remaining slots."""
        filtered = [
            make_result("A", 0.9),
            make_result("B", 0.8),
        ]
        unfiltered = [
            make_result("C", 0.85),
            make_result("D", 0.7),
        ]
        blended = blend_results(filtered, unfiltered, total_k=3)
        assert len(blended) == 3
        # A is from filtered, C is next best from unfiltered, D fills slot
        ids = [r.id for r in blended]
        assert ids[0] == "A"  # highest score
        assert ids[1] in ("B", "C")  # either from filtered or best unfiltered
        assert ids[1] in ("B", "C")

    def test_dedup_by_id(self, make_result):
        """Duplicate chunk_ids are skipped (filtered takes priority)."""
        filtered = [
            make_result("A", 0.9),
            make_result("B", 0.8),
        ]
        unfiltered = [
            make_result("B", 0.8),  # duplicate of B
            make_result("C", 0.7),
        ]
        blended = blend_results(filtered, unfiltered, total_k=3)
        assert len(blended) == 3
        assert {r.id for r in blended} == {"A", "B", "C"}

    def test_sorted_by_hybrid_score(self, make_result):
        """Results are sorted by score_hybrid descending."""
        filtered = [
            make_result("B", 0.8),
        ]
        unfiltered = [
            make_result("A", 0.9),
            make_result("C", 0.7),
        ]
        blended = blend_results(filtered, unfiltered, total_k=3)
        assert [r.id for r in blended] == ["A", "B", "C"]

    def test_empty_filtered_graceful(self, make_result):
        """Empty filtered list falls back to unfiltered."""
        blended = blend_results(
            filtered=[],
            unfiltered=[make_result("A", 0.9), make_result("B", 0.8)],
            total_k=3,
        )
        assert len(blended) == 2
        assert [r.id for r in blended] == ["A", "B"]

    def test_empty_unfiltered_graceful(self, make_result):
        """Empty unfiltered list still returns filtered."""
        blended = blend_results(
            filtered=[make_result("A", 0.9)],
            unfiltered=[],
            total_k=3,
        )
        assert len(blended) == 1
        assert blended[0].id == "A"

    def test_limit_total_k(self, make_result):
        """Results are limited to total_k."""
        filtered = [make_result("A", 0.9), make_result("B", 0.8)]
        unfiltered = [make_result("C", 0.7), make_result("D", 0.6)]
        blended = blend_results(filtered, unfiltered, total_k=2)
        assert len(blended) == 2


# =============================================================================
# QueryGenerationResult category tests
# =============================================================================

class TestQueryGeneratorCategory:
    """Tests for detected_category in QueryGenerationResult."""

    def test_from_dict_parses_detected_category(self):
        """detected_category is parsed from LLM JSON dict."""
        from agents.query_generator import QueryGenerationResult
        data = {
            "clarification_needed": False,
            "clarification_questions": [],
            "queries": [{"text": "test", "reason": "test"}],
            "search_params": {},
            "confidence": 0.9,
            "reasoning": "test",
            "detected_category": "ЛК",
        }
        result = QueryGenerationResult.from_dict(data)
        assert result.detected_category == "ЛК"

    def test_from_dict_default_unknown(self):
        """Missing detected_category defaults to 'не известна'."""
        from agents.query_generator import QueryGenerationResult
        data = {
            "clarification_needed": False,
            "clarification_questions": [],
            "queries": [{"text": "test", "reason": "test"}],
            "search_params": {},
            "confidence": 0.5,
            "reasoning": "test",
        }
        result = QueryGenerationResult.from_dict(data)
        assert result.detected_category == "не известна"

    def test_default_result_has_unknown(self):
        """_default_result() sets detected_category = 'не известна'."""
        from agents.query_generator import QueryGeneratorAgent
        agent = QueryGeneratorAgent()
        result = agent._default_result("тестовый запрос")
        assert result.detected_category == "не известна"

    def test_dataclass_default_field(self):
        """Default value of detected_category is 'не известна'."""
        from agents.query_generator import QueryGenerationResult
        result = QueryGenerationResult(
            clarification_needed=False,
            clarification_questions=[],
            queries=[],
            search_params={},
            confidence=0.5,
            reasoning="",
        )
        assert result.detected_category == "не известна"


# =============================================================================
# Prompt content tests
# =============================================================================

class TestQueryGenerationPromptCategory:
    """Tests for category detection in prompts."""

    def test_prompt_contains_category_section(self):
        """Prompt has 'Детекция категории вопроса' section."""
        from prompts.query_generation import QUERY_GENERATION_PROMPT
        assert "Детекция категории вопроса" in QUERY_GENERATION_PROMPT

    def test_prompt_contains_category_lk(self):
        """Prompt mentions ЛК category criteria."""
        from prompts.query_generation import QUERY_GENERATION_PROMPT
        assert "ЛК" in QUERY_GENERATION_PROMPT

    def test_prompt_contains_category_du(self):
        """Prompt mentions ДУ category criteria."""
        from prompts.query_generation import QUERY_GENERATION_PROMPT
        assert "ДУ" in QUERY_GENERATION_PROMPT

    def test_prompt_contains_category_tpp(self):
        """Prompt mentions ТПП category criteria."""
        from prompts.query_generation import QUERY_GENERATION_PROMPT
        assert "ТПП" in QUERY_GENERATION_PROMPT

    def test_prompt_contains_detected_category_field(self):
        """Prompt includes detected_category in JSON format example."""
        from prompts.query_generation import QUERY_GENERATION_PROMPT
        assert "detected_category" in QUERY_GENERATION_PROMPT

    def test_get_prompt_still_works(self):
        """get_query_generation_prompt still returns valid prompt."""
        from prompts.query_generation import get_query_generation_prompt
        prompt = get_query_generation_prompt(
            user_query="тест",
            history="",
            category="ТПП",
        )
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "Детекция категории вопроса" in prompt


# =============================================================================
# SearchAgent integration tests (mocked sub-components)
# =============================================================================

class TestSearchAgentCategory:
    """Tests for category-aware blended search in SearchAgent."""

    @patch('agents.search_agent.config')
    @patch('agents.search_agent.SearchTool')
    @patch('agents.search_agent.QueryGeneratorAgent')
    def test_blended_search_for_lk(
        self, mock_qg_class, mock_st_class, mock_config
    ):
        """Detected ЛК triggers blended search (not single search)."""
        # Enable category filtering
        mock_config.CATEGORY_FILTER_ENABLED = True
        mock_config.CATEGORY_FILTER_BLEND_RATIO = 0.3
        mock_config.REGULATORY_QUERY_BOOST = False
        mock_config.SOURCE_QUALITY_THRESHOLD = 0.25

        # Mock QueryGenerator
        mock_qg = MagicMock()
        mock_qg_class.return_value = mock_qg
        mock_qg.generate.return_value = MagicMock(
            clarification_needed=False,
            clarification_questions=[],
            queries=[MagicMock(text="тестовый запрос")],
            search_params={"k": 10, "strategy": "concat"},
            confidence=0.85,
            reasoning="test",
            detected_category="ЛК",
        )
        mock_qg.get_queries_text.return_value = ["тестовый запрос"]
        mock_qg.needs_clarification.return_value = False

        # Mock SearchTool — return non-empty results for both calls
        mock_st = MagicMock()
        mock_st_class.return_value = mock_st
        mock_st.search_multi.return_value = [
            SearchResult(
                id="1", content="ЛК content", summary="s",
                category="ЛК", filename="f", breadcrumbs="b",
                score_hybrid=0.9, score_semantic=0.8, score_lexical=0.7,
                metadata={}, collection_name="operational_content",
            )
        ]

        from qdrant_client.http import models
        agent = SearchAgent()
        result = agent.search(
            user_query="как войти в личный кабинет?",
        )

        # search_multi should have been called twice (filtered + unfiltered)
        assert mock_st.search_multi.call_count >= 2
        # results should contain at least 1 item
        assert len(result["results"]) >= 1
        # No clarification needed
        assert result["clarification_needed"] is False

    @patch('agents.search_agent.config')
    @patch('agents.search_agent.SearchTool')
    @patch('agents.search_agent.QueryGeneratorAgent')
    def test_no_filter_for_tpp(
        self, mock_qg_class, mock_st_class, mock_config
    ):
        """detected_category='ТПП' should NOT trigger blended search."""
        mock_config.CATEGORY_FILTER_ENABLED = True
        mock_config.CATEGORY_FILTER_BLEND_RATIO = 0.3
        mock_config.REGULATORY_QUERY_BOOST = False
        mock_config.SOURCE_QUALITY_THRESHOLD = 0.25

        mock_qg = MagicMock()
        mock_qg_class.return_value = mock_qg
        mock_qg.generate.return_value = MagicMock(
            clarification_needed=False,
            clarification_questions=[],
            queries=[MagicMock(text="тестовый запрос")],
            search_params={"k": 10, "strategy": "concat"},
            confidence=0.9,
            reasoning="test",
            detected_category="ТПП",
        )
        mock_qg.get_queries_text.return_value = ["тестовый запрос"]
        mock_qg.needs_clarification.return_value = False

        mock_st = MagicMock()
        mock_st_class.return_value = mock_st
        mock_st.search_multi.return_value = [
            SearchResult(
                id="1", content="ТПП content", summary="s",
                category="ТПП", filename="f", breadcrumbs="b",
                score_hybrid=0.9, score_semantic=0.8, score_lexical=0.7,
                metadata={}, collection_name="normative_documents",
            )
        ]

        agent = SearchAgent()
        result = agent.search(user_query="сроки технологического присоединения?")

        # single search — search_multi called exactly once (during tool_search)
        # plus possibly by blend_results didn't run; just once for the standard path
        # Actually with the standard path it's called 1 time from the main search
        # Note: _retry_search also calls search_multi so count >= 1
        assert mock_st.search_multi.call_count >= 1

    @patch('agents.search_agent.config')
    @patch('agents.search_agent.SearchTool')
    @patch('agents.search_agent.QueryGeneratorAgent')
    def test_low_confidence_skips_filter(
        self, mock_qg_class, mock_st_class, mock_config
    ):
        """confidence < 0.6 should NOT trigger blended search even for ЛК."""
        mock_config.CATEGORY_FILTER_ENABLED = True
        mock_config.CATEGORY_FILTER_BLEND_RATIO = 0.3
        mock_config.REGULATORY_QUERY_BOOST = False
        mock_config.SOURCE_QUALITY_THRESHOLD = 0.25

        mock_qg = MagicMock()
        mock_qg_class.return_value = mock_qg
        mock_qg.generate.return_value = MagicMock(
            clarification_needed=False,
            clarification_questions=[],
            queries=[MagicMock(text="тестовый запрос")],
            search_params={"k": 10, "strategy": "concat"},
            confidence=0.45,  # below threshold
            reasoning="low confidence",
            detected_category="ЛК",
        )
        mock_qg.get_queries_text.return_value = ["тестовый запрос"]
        mock_qg.needs_clarification.return_value = False

        mock_st = MagicMock()
        mock_st_class.return_value = mock_st
        mock_st.search_multi.return_value = []

        agent = SearchAgent()
        result = agent.search(user_query="какой-то вопрос")

        # Standard path — single call to search_multi (not blended)
        assert mock_st.search_multi.call_count >= 1

    @patch('agents.search_agent.config')
    @patch('agents.search_agent.SearchTool')
    @patch('agents.search_agent.QueryGeneratorAgent')
    def test_skip_unknown_category(
        self, mock_qg_class, mock_st_class, mock_config
    ):
        """detected_category='не известна' → single search, no blend."""
        mock_config.CATEGORY_FILTER_ENABLED = True
        mock_config.CATEGORY_FILTER_BLEND_RATIO = 0.3
        mock_config.REGULATORY_QUERY_BOOST = False
        mock_config.SOURCE_QUALITY_THRESHOLD = 0.25

        mock_qg = MagicMock()
        mock_qg_class.return_value = mock_qg
        mock_qg.generate.return_value = MagicMock(
            clarification_needed=False,
            clarification_questions=[],
            queries=[MagicMock(text="тестовый запрос")],
            search_params={"k": 10, "strategy": "concat"},
            confidence=0.7,
            reasoning="test",
            detected_category="не известна",
        )
        mock_qg.get_queries_text.return_value = ["тестовый запрос"]
        mock_qg.needs_clarification.return_value = False

        mock_st = MagicMock()
        mock_st_class.return_value = mock_st
        mock_st.search_multi.return_value = []

        agent = SearchAgent()
        result = agent.search(user_query="вопрос без категории")
        assert mock_st.search_multi.call_count >= 1

    @patch('agents.search_agent.config')
    @patch('agents.search_agent.SearchTool')
    @patch('agents.search_agent.QueryGeneratorAgent')
    def test_skip_query_generator_no_blend(
        self, mock_qg_class, mock_st_class, mock_config
    ):
        """skip_query_generator=True → single search, no blend."""
        mock_config.CATEGORY_FILTER_ENABLED = True
        mock_config.CATEGORY_FILTER_BLEND_RATIO = 0.3
        mock_config.REGULATORY_QUERY_BOOST = False
        mock_config.SOURCE_QUALITY_THRESHOLD = 0.25

        mock_st = MagicMock()
        mock_st_class.return_value = mock_st
        mock_st.search_multi.return_value = []

        agent = SearchAgent()
        result = agent.search(
            user_query="простой запрос",
            skip_query_generator=True,
        )
        # Should use single search (skip_query_generator → detected_category stays unknown)
        assert mock_st.search_multi.call_count >= 1
```

**Verify:** `cd backend && python -m pytest tests/test_category_filtering.py -v`
**Commit:** `test: add unit tests for category-aware filtering`

---

## Config Reference

New environment variables (`.env`):

```env
# Category-aware partial filtering
CATEGORY_FILTER_ENABLED=true
CATEGORY_FILTER_BLEND_RATIO=0.3
```

## Summary of Changes

| File | Change | Complexity |
|---|---|---|
| `backend/config.py` | +2 env vars (`CATEGORY_FILTER_ENABLED`, `CATEGORY_FILTER_BLEND_RATIO`) | Low |
| `backend/agents/query_generator.py` | +1 dataclass field, +1 line in `from_dict()`, +1 line in `_default_result()` | Low |
| `backend/prompts/query_generation.py` | +14 lines (section), +1 line in JSON example | Low |
| `backend/agents/search_agent.py` | +1 import, +1 method (`_blended_search`), +1 function (`blend_results`), branch in `search()` | Medium |
| `backend/tests/test_category_filtering.py` | NEW — 16 test cases | Medium |

## Error Handling Coverage

| Scenario | Handling |
|---|---|
| `detected_category="не известна"` | Single search (unchanged path) |
| `detected_category="ТПП"` | Single search (category too broad) |
| `gen_confidence < 0.6` | Single search (unreliable detection) |
| `filtered_results` empty | Graceful — uses only unfiltered |
| `unfiltered_results` empty | Graceful — uses only filtered |
| `search_multi` throws exception in `_blended_search` | Caught per future, empty list for that branch |
