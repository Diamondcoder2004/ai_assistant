"""
Langfuse Tracer — observability utility for the Agentic RAG pipeline.

Provides:
- Singleton Langfuse client initialization
- Helper for creating root traces with user/session metadata
- Re-exports observe decorator and trace utilities
"""
import logging
from functools import wraps

import config
from langfuse import Langfuse, observe, propagate_attributes

logger = logging.getLogger(__name__)

_langfuse_client = None


def get_langfuse_client() -> Langfuse:
    """Get or create the singleton Langfuse client."""
    global _langfuse_client

    if _langfuse_client is not None:
        return _langfuse_client

    if not config.ENABLE_LANGFUSE:
        logger.info("Langfuse is disabled (ENABLE_LANGFUSE=false)")
        return None

    required_keys = {
        "LANGFUSE_SECRET_KEY": config.LANGFUSE_SECRET_KEY,
        "LANGFUSE_PUBLIC_KEY": config.LANGFUSE_PUBLIC_KEY,
    }

    missing = [k for k, v in required_keys.items() if not v]
    if missing:
        logger.warning(f"Langfuse disabled: missing env vars: {missing}")
        return None

    try:
        _langfuse_client = Langfuse(
            secret_key=config.LANGFUSE_SECRET_KEY,
            public_key=config.LANGFUSE_PUBLIC_KEY,
            host=config.LANGFUSE_BASE_URL,
        )
        logger.info(
            f"Langfuse client initialized: {config.LANGFUSE_BASE_URL}"
        )
        _register_model_pricing(_langfuse_client)
        return _langfuse_client
    except Exception as e:
        logger.error(f"Failed to initialize Langfuse: {e}")
        return None


def _register_model_pricing(client: Langfuse) -> None:
    """
    Register RouterAI model definitions with pricing in Langfuse
    so that cost tracking works automatically for all LLM calls.

    Pricing is configured via LANGFUSE_MODEL_PRICES env var (list of dicts).
    Uses client.api.models.create() — idempotent (409 on duplicate).
    """
    if not config.LANGFUSE_MODEL_PRICES:
        logger.info("Langfuse: no model pricing configured")
        return

    registered = 0
    skipped = 0
    for mp in config.LANGFUSE_MODEL_PRICES:
        try:
            client.api.models.create(
                model_name=mp["model_name"],
                match_pattern=mp.get("match_pattern", mp["model_name"]),
                start_date=mp.get("start_date", "2025-01-01"),
                unit=mp.get("unit", "TOKENS"),
                tokenizer_id=mp.get("tokenizer_id", "openai"),
                input_price=mp.get("input_price"),
                output_price=mp.get("output_price"),
                total_price=mp.get("total_price"),
            )
            registered += 1
            logger.info(
                f"Langfuse: registered model '{mp['model_name']}' "
                f"(in={mp.get('input_price')}, out={mp.get('output_price')} ₽/token)"
            )
        except Exception as e:
            if "409" in str(e) or "already exists" in str(e).lower():
                skipped += 1
                logger.debug(f"Langfuse: model '{mp['model_name']}' already exists, skipped")
            else:
                logger.warning(f"Langfuse: failed to register model '{mp['model_name']}': {e}")

    if registered or skipped:
        logger.info(
            f"Langfuse model pricing: {registered} registered, {skipped} skipped"
        )


def get_trace_id() -> str | None:
    """Get the current Langfuse trace ID from OpenTelemetry context."""
    client = get_langfuse_client()
    if client is None:
        return None
    try:
        return client.get_current_trace_id()
    except Exception:
        return None


def observe_rag(name: str = None, **kwargs):
    """
    Decorator for RAG pipeline methods that creates a Langfuse observation span.

    Usage:
        @observe_rag(name="SearchAgent.search")
        def search(self, query):
            ...

    The decorated function receives the Langfuse trace_id in kwargs,
    and the decorator sets up user/session context for nested spans.
    """
    def decorator(func):
        @wraps(func)
        @observe(name=name or func.__name__, **kwargs)
        def wrapper(*args, **fn_kwargs):
            # Propagate trace context from parent spans
            trace_id = fn_kwargs.pop("langfuse_trace_id", None)
            user_id = fn_kwargs.pop("langfuse_user_id", None)
            session_id = fn_kwargs.pop("langfuse_session_id", None)

            if user_id or session_id:
                with propagate_attributes(
                    user_id=user_id,
                    session_id=session_id,
                ):
                    return func(*args, **fn_kwargs)
            else:
                return func(*args, **fn_kwargs)

        return wrapper

    return decorator


# Re-export for convenience
__all__ = [
    "get_langfuse_client",
    "get_trace_id",
    "observe_rag",
    "observe",
    "propagate_attributes",
]
