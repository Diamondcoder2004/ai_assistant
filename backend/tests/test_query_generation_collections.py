"""Tests for query generation prompt with collection hints."""
from prompts.query_generation import get_query_generation_prompt, QUERY_GENERATION_PROMPT


def test_query_generation_prompt_contains_collection_hints():
    """Query generation prompt mentions collection selection."""
    assert "prefer_collection" in QUERY_GENERATION_PROMPT


def test_query_generation_prompt_contains_normative_hint():
    """Query generation prompt mentions normative collection."""
    assert "normative" in QUERY_GENERATION_PROMPT


def test_query_generation_prompt_contains_operational_hint():
    """Query generation prompt mentions operational collection."""
    assert "operational" in QUERY_GENERATION_PROMPT


def test_query_generation_prompt_preserves_existing_sections():
    """Query generation prompt still has all original sections."""
    assert "ВАЖНО" in QUERY_GENERATION_PROMPT
    assert "УТОЧНЯЮЩИЕ ВОПРОСЫ" in QUERY_GENERATION_PROMPT
    assert "ФОРМАТ ОТВЕТА" in QUERY_GENERATION_PROMPT


def test_get_query_generation_prompt_returns_string():
    """get_query_generation_prompt returns a non-empty string."""
    prompt = get_query_generation_prompt(
        user_query="тест",
        history="",
        category="ТПП",
    )
    assert isinstance(prompt, str)
    assert len(prompt) > 0
