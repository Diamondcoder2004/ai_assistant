"""Tests for wiki-related config values."""
import pytest
from pathlib import Path
import config


class TestWikiConfig:
    """Tests for wiki configuration."""

    def test_wiki_index_path_default(self):
        """WIKI_INDEX_PATH has a sensible default."""
        # Default should point to wiki/data/index.json relative to backend dir
        expected = config.BASE_DIR / "wiki" / "data" / "index.json"
        assert config.WIKI_INDEX_PATH == expected

    def test_wiki_index_path_is_path(self):
        """WIKI_INDEX_PATH is a Path object."""
        assert isinstance(config.WIKI_INDEX_PATH, Path)

    def test_enable_wiki_router_default(self):
        """ENABLE_WIKI_ROUTER defaults to true."""
        # The new system works without Supabase, so default is True
        assert isinstance(config.ENABLE_WIKI_ROUTER, bool)

    def test_wiki_router_model_default(self):
        """WIKI_ROUTER_MODEL defaults to inception/mercury-2."""
        assert config.WIKI_ROUTER_MODEL == "inception/mercury-2"

    def test_wiki_top_k_default(self):
        """WIKI_TOP_K defaults to 3."""
        assert config.WIKI_TOP_K == 3

    def test_wiki_search_top_k_default(self):
        """WIKI_SEARCH_TOP_K defaults to 5 (candidates before LLM refinement)."""
        assert config.WIKI_SEARCH_TOP_K == 5

    def test_no_supabase_wiki_vars(self):
        """Supabase wiki vars (WIKI_TABLE_NAME) should not exist in config."""
        assert not hasattr(config, "WIKI_TABLE_NAME")
