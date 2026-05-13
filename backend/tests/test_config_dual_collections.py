"""Tests for dual collection config."""
import os
import pytest


def test_normative_collection_default():
    """NORMATIVE_COLLECTION defaults to 'normative_documents'."""
    from config import NORMATIVE_COLLECTION_NAME
    assert NORMATIVE_COLLECTION_NAME == "normative_documents"


def test_operational_collection_default():
    """OPERATIONAL_COLLECTION defaults to 'operational_content'."""
    from config import OPERATIONAL_COLLECTION_NAME
    assert OPERATIONAL_COLLECTION_NAME == "operational_content"


def test_chunks_dir_default():
    """CHUNKS_DIR defaults to 'chunking/enriched_chunks'."""
    from config import CHUNKS_DIR
    assert CHUNKS_DIR == "chunking/enriched_chunks"


def test_collection_name_deprecated_fallback():
    """COLLECTION_NAME falls back to NORMATIVE_COLLECTION_NAME."""
    from config import COLLECTION_NAME, NORMATIVE_COLLECTION_NAME
    assert COLLECTION_NAME == NORMATIVE_COLLECTION_NAME


def test_env_override_normative(monkeypatch):
    """NORMATIVE_COLLECTION can be overridden via env."""
    monkeypatch.setenv("NORMATIVE_COLLECTION", "my_normative")
    # Need to reimport to pick up env change
    import importlib
    import config
    importlib.reload(config)
    assert config.NORMATIVE_COLLECTION_NAME == "my_normative"
    # Cleanup
    monkeypatch.delenv("NORMATIVE_COLLECTION")
    importlib.reload(config)


def test_env_override_operational(monkeypatch):
    """OPERATIONAL_COLLECTION can be overridden via env."""
    monkeypatch.setenv("OPERATIONAL_COLLECTION", "my_operational")
    import importlib
    import config
    importlib.reload(config)
    assert config.OPERATIONAL_COLLECTION_NAME == "my_operational"
    monkeypatch.delenv("OPERATIONAL_COLLECTION")
    importlib.reload(config)
