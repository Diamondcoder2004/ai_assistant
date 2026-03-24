# Prompts package
from .system_prompt import get_system_prompt
from .query_generation import get_query_generation_prompt

__all__ = ["get_system_prompt", "get_query_generation_prompt"]
