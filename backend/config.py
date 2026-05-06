"""
Конфигурация проекта Agentic RAG
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# =============================================================================
# PROJECT PATHS
# =============================================================================

BASE_DIR = Path(__file__).parent
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# =============================================================================
# ROUTER AI
# =============================================================================

ROUTERAI_API_KEY = os.getenv("ROUTERAI_API_KEY")
ROUTERAI_BASE_URL = os.getenv("ROUTERAI_BASE_URL", "https://routerai.ru/api/v1").strip()

# =============================================================================
# QDRANT
# =============================================================================

QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))

# Dual collection names (replacing single COLLECTION_NAME)
NORMATIVE_COLLECTION_NAME = os.getenv("NORMATIVE_COLLECTION", "normative_documents")
OPERATIONAL_COLLECTION_NAME = os.getenv("OPERATIONAL_COLLECTION", "operational_content")

# Directory with enriched chunks (relative to backend/)
CHUNKS_DIR = os.getenv("CHUNKS_DIR", "chunking/enriched_chunks")

# Deprecated: kept for backward compatibility
# If NORMATIVE_COLLECTION is not set, falls back to COLLECTION_NAME
COLLECTION_NAME = os.getenv("COLLECTION_NAME", NORMATIVE_COLLECTION_NAME)

# =============================================================================
# EMBEDDING
# =============================================================================

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "perplexity/pplx-embed-v1-4b")
EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "2560"))

# =============================================================================
# LLM
# =============================================================================

DEFAULT_LLM_MODEL = os.getenv("DEFAULT_LLM_MODEL", "deepseek/deepseek-v4-flash")

# Per-agent LLM models — each agent uses its own model for optimal speed/quality tradeoff
# Speed-critical agents (intermediate steps, user waiting): inception/mercury-2
# Quality-critical agents (final answer, evaluation): deepseek/deepseek-v4-flash
QUERY_GENERATOR_MODEL = os.getenv("QUERY_GENERATOR_MODEL", "inception/mercury-2")
RESPONSE_AGENT_MODEL = os.getenv("RESPONSE_AGENT_MODEL", "deepseek/deepseek-v4-flash")
JUDGE_LLM_MODEL = os.getenv("JUDGE_LLM_MODEL", "deepseek/deepseek-v4-flash")

LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.7"))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "2000"))

# =============================================================================
# SEARCH WEIGHTS (default)
# =============================================================================

RETRIEVE_PREF_WEIGHT = float(os.getenv("RETRIEVE_PREF_WEIGHT", "0.4"))
RETRIEVE_HYPE_WEIGHT = float(os.getenv("RETRIEVE_HYPE_WEIGHT", "0.3"))
RETRIEVE_LEXICAL_WEIGHT = float(os.getenv("RETRIEVE_LEXICAL_WEIGHT", "0.2"))
RETRIEVE_CONTEXTUAL_WEIGHT = float(os.getenv("RETRIEVE_CONTEXTUAL_WEIGHT", "0.1"))

# =============================================================================
# AGENT SETTINGS
# =============================================================================

MAX_QUERY_GENERATION_ATTEMPTS = int(os.getenv("MAX_QUERY_GENERATION_ATTEMPTS", "3"))
ENABLE_CLARIFICATION = os.getenv("ENABLE_CLARIFICATION", "true").lower() == "true"
MAX_CLARIFICATION_QUESTIONS = int(os.getenv("MAX_CLARIFICATION_QUESTIONS", "2"))

# =============================================================================
# WIKI ROUTER (JSON-based Agentic Knowledge Layer)
# =============================================================================

ENABLE_WIKI_ROUTER = os.getenv("ENABLE_WIKI_ROUTER", "true").lower() == "true"
WIKI_INDEX_PATH = Path(os.getenv("WIKI_INDEX_PATH", str(BASE_DIR / "wiki" / "data" / "index.json")))
WIKI_ROUTER_MODEL = os.getenv("WIKI_ROUTER_MODEL", "inception/mercury-2")
WIKI_TOP_K = int(os.getenv("WIKI_TOP_K", "3"))  # LLM-selected documents
WIKI_SEARCH_TOP_K = int(os.getenv("WIKI_SEARCH_TOP_K", "5"))  # Keyword candidates before LLM

# =============================================================================
# LOGGING
# =============================================================================

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# =============================================================================
# SUPABASE (Chat History & Feedback)
# =============================================================================

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# =============================================================================
# JWT AUTH
# =============================================================================

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

# =============================================================================
# LANGFUSE OBSERVABILITY
# =============================================================================

LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY")
LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY")
LANGFUSE_BASE_URL = os.getenv("LANGFUSE_BASE_URL", "https://cloud.langfuse.com")
ENABLE_LANGFUSE = os.getenv("ENABLE_LANGFUSE", "true").lower() == "true"

# Model pricing for Langfuse cost tracking (in rubles per 1 token)
# Format: MODEL_PRICING = [
#   {"model_name": "inception/mercury-2", "match_pattern": "inception/mercury-2",
#    "input_price": 0.0000005, "output_price": 0.000001},
#   ...
# ]
# Prices are per TOKEN. Multiply rub/1M tokens by 1e-6 to convert.
import json as _json
_DEFAULT_MODEL_PRICES = [
    {"model_name": "inception/mercury-2", "match_pattern": "inception/mercury-2", "input_price": 0.0000015, "output_price": 0.0000045},
    {"model_name": "deepseek/deepseek-v4-flash", "match_pattern": "deepseek/deepseek-v4-flash", "input_price": 0.00000075, "output_price": 0.00000225},
    {"model_name": "deepseek/deepseek-v3.2", "match_pattern": "deepseek/deepseek-v3.2", "input_price": 0.00000075, "output_price": 0.00000225},
    {"model_name": "perplexity/pplx-embed-v1-4b", "match_pattern": "perplexity/pplx-embed-v1-4b", "input_price": 0.0000001, "output_price": 0},
]
_raw_prices = os.getenv("LANGFUSE_MODEL_PRICES", "").strip()
LANGFUSE_MODEL_PRICES = _json.loads(_raw_prices) if _raw_prices else _DEFAULT_MODEL_PRICES
