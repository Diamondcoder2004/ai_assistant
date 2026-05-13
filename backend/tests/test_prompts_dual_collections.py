"""Tests for system prompt with dual collections."""
from prompts.system_prompt import get_system_prompt, SYSTEM_PROMPT


def test_system_prompt_contains_dual_collections():
    """System prompt mentions both collections."""
    prompt = get_system_prompt()
    assert "normative_documents" in prompt
    assert "operational_content" in prompt


def test_system_prompt_contains_collection_guidance():
    """System prompt has guidance on which collection to use."""
    prompt = get_system_prompt()
    assert "тарифы и законы" in prompt
    assert "процедуры и FAQ" in prompt


def test_system_prompt_preserves_existing_content():
    """System prompt still has all original sections."""
    prompt = get_system_prompt()
    assert "БИЗНЕС-ПРАВИЛА" in prompt
    assert "Терминология" in prompt
    assert "Параметры поиска" in prompt
    assert "Правила оформления ссылок" in prompt
