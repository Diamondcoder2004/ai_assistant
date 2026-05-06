"""Tests that legacy wiki modules are removed and new modules work."""
import pytest
import importlib


class TestWikiCleanup:
    """Verify legacy modules are gone and new modules work."""

    def test_wiki_store_removed(self):
        """wiki_store module should not be importable."""
        with pytest.raises(ImportError):
            importlib.import_module("wiki.wiki_store")

    def test_wiki_extractor_removed(self):
        """wiki_extractor module should not be importable."""
        with pytest.raises(ImportError):
            importlib.import_module("wiki.wiki_extractor")

    def test_wiki_models_importable(self):
        """wiki.models should be importable."""
        from wiki.models import WikiDocument, WikiRoutingResult
        assert WikiDocument is not None
        assert WikiRoutingResult is not None

    def test_wiki_search_tool_importable(self):
        """wiki.search_tool should be importable."""
        from wiki.search_tool import WikiSearchTool
        assert WikiSearchTool is not None

    def test_wiki_router_agent_importable(self):
        """wiki.wiki_router should import WikiRouterAgent."""
        from wiki.wiki_router import WikiRouterAgent
        assert WikiRouterAgent is not None

    def test_wiki_build_index_importable(self):
        """wiki.build_index should be importable."""
        from wiki.build_index import WikiIndexBuilder
        assert WikiIndexBuilder is not None

    def test_no_supabase_imports_in_wiki(self):
        """No wiki module should import from supabase."""
        import inspect
        import wiki.models
        import wiki.search_tool
        import wiki.wiki_router
        import wiki.build_index

        for module in [wiki.models, wiki.search_tool, wiki.wiki_router, wiki.build_index]:
            source = inspect.getsource(module)
            assert "from supabase" not in source
            assert "import supabase" not in source
