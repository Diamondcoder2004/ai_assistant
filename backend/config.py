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
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "BASHKIR_ENERGO_PERPLEXITY")

# =============================================================================
# EMBEDDING
# =============================================================================

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "perplexity/pplx-embed-v1-4b")
EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "2560"))

# =============================================================================
# LLM
# =============================================================================

DEFAULT_LLM_MODEL = os.getenv("DEFAULT_LLM_MODEL", "qwen/qwen3.5-flash-02-23")
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
