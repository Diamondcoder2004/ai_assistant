"""
Post-Retrieval Relevance Filter

Filters search results by token overlap with the query, dropping chunks
that have zero lexical overlap. This catches the case where semantic search
returns chunks with high embedding similarity but zero actual word overlap
— a common failure mode for procedural/regulatory queries.

Strategy:
  1. Lemmatize the query tokens (same pymorphy3 as BM25)
  2. Count lemmatized token overlap with each chunk's content + summary
  3. Drop chunks with overlap below threshold (default: at least 1 shared lemma)
  4. Return up to max_results, preserving original ranking order
"""

import logging
import os
from typing import List

from tools.search_tool import SearchResult, get_morph_analyzer

logger = logging.getLogger(__name__)

# Minimum number of shared lemmatized tokens for a chunk to be considered relevant.
# Set to 0 to disable filtering. Default 1 = at least one word in common.
MIN_OVERLAP = int(os.getenv("RELEVANCE_MIN_OVERLAP", "1"))

# Maximum chunks to return after filtering.
MAX_RESULTS = 5


def _lemmatize(text: str) -> set[str]:
    """Lemmatize text into a set of base forms, excluding stop words."""
    if not text:
        return set()
    morph = get_morph_analyzer()
    # Common Russian stop words + punctuation
    stop_words = {
        "и", "в", "на", "не", "что", "с", "по", "к", "как", "а",
        "то", "это", "за", "от", "для", "из", "о", "же", "ну",
        "бы", "ещё", "всё", "ее", "его", "им", "их", "мы",
        "они", "вы", "она", "он", "я", "ты", "меня", "мне",
        "тебя", "тебе", "быть", "был", "была", "были", "есть",
        "который", "также", "или", "если", "чтобы", "при",
        "у", "во", "со", "ко", "без", "до", "об", "под",
        "перед", "над", "через", "между", "ли", "да", "нет",
    }
    lemmas = set()
    for word in text.lower().split():
        # Skip very short words and numbers-only tokens
        if len(word) < 3 and word not in {"тп", "лк", "ду", "фл", "ип", "юл"}:
            continue
        if word in stop_words:
            continue
        try:
            parsed = morph.parse(word)[0]
            lemma = parsed.normal_form
            lemmas.add(lemma)
        except Exception:
            # Fallback: use the raw lowercase word
            lemmas.add(word.lower())
    return lemmas


def filter_by_overlap(
    results: List[SearchResult],
    query: str,
    min_overlap: int | None = None,
    max_results: int = MAX_RESULTS,
) -> List[SearchResult]:
    """
    Filter search results by token overlap with the query.

    For each result, compute the number of shared lemmatized tokens
    between the query and the chunk's content + summary. Drop chunks
    with overlap below min_overlap.

    Args:
        results: List of SearchResult objects from search_tool
        query: The original user query for overlap calculation
        min_overlap: Minimum shared lemmas to keep a chunk (None → use MIN_OVERLAP)
        max_results: Maximum number of results to return after filtering

    Returns:
        Filtered list of SearchResult objects, preserving original order.
        Never returns more than max_results.
    """
    if not results:
        return []

    if min_overlap is None:
        min_overlap = MIN_OVERLAP  # Read at runtime, allows CLI override

    if min_overlap <= 0:
        logger.info("Relevance filter: disabled (min_overlap=0)")
        return results[:max_results]

    query_lemmas = _lemmatize(query)
    if not query_lemmas:
        logger.warning("Relevance filter: query produced zero lemmas, skipping")
        return results[:max_results]

    kept = []
    dropped = 0
    for r in results:
        # Combine content + summary for overlap check
        chunk_text = (r.content or "") + " " + (r.summary or "")
        chunk_lemmas = _lemmatize(chunk_text)

        overlap = len(query_lemmas & chunk_lemmas)

        if overlap >= min_overlap:
            kept.append(r)
        else:
            dropped += 1

        if len(kept) >= max_results:
            break

    if dropped > 0:
        logger.info(
            f"Relevance filter: kept {len(kept)}, dropped {dropped} "
            f"(min_overlap={min_overlap})"
        )

    return kept


# ---------------------------------------------------------------
# Regulatory query detection
# ---------------------------------------------------------------

REGULATORY_KEYWORDS = {
    "срок", "закон", "постановление", "правило", "норматив",
    "приказ", "регламент", "утвержд", "фз", "пп", "рф",
    "правительство", "указ", "распоряжение", "положение",
    "статья", "пункт", "параграф", "глава", "раздел",
    "методика", "стандарт", "требование", "обязан", "лицензия",
    "гкт", "тариф", "ставка", "плата", "штраф", "санкция",
    "основание", "порядок", "процедура", "регулирование",
}

LEMMATIZED_REGULATORY_KEYWORDS: set[str] | None = None


def _get_regulatory_keywords() -> set[str]:
    """Lazily lemmatize regulatory keywords for matching."""
    global LEMMATIZED_REGULATORY_KEYWORDS
    if LEMMATIZED_REGULATORY_KEYWORDS is None:
        morph = get_morph_analyzer()
        lemmas = set()
        for kw in REGULATORY_KEYWORDS:
            try:
                parsed = morph.parse(kw)[0]
                lemmas.add(parsed.normal_form)
            except Exception:
                lemmas.add(kw.lower())
        LEMMATIZED_REGULATORY_KEYWORDS = lemmas
    return LEMMATIZED_REGULATORY_KEYWORDS


def is_regulatory_query(query: str) -> bool:
    """
    Detect if a query is regulatory/legal in nature.

    Lemmatizes the query and checks for overlap with known regulatory keywords.
    Returns True if the query likely needs normative documents rather than FAQ.
    """
    query_lemmas = _lemmatize(query)
    if not query_lemmas:
        return False

    reg_lemmas = _get_regulatory_keywords()
    overlap = query_lemmas & reg_lemmas
    return len(overlap) >= 1


# ---------------------------------------------------------------
# Source quality scoring
# ---------------------------------------------------------------


def compute_source_quality(
    results: list,
    query: str,
) -> dict:
    """
    Compute quality metrics for the surviving search results.

    Returns a dict with:
        - score: float 0-1, overall quality (higher = better sources)
        - avg_overlap: average normalized overlap across results
        - survived_count: how many results passed relevance filter
        - avg_hybrid_score: average score_hybrid of surviving results
        - is_low_quality: bool, True if below SOURCE_QUALITY_THRESHOLD
    """
    import config

    if not results:
        return {
            "score": 0.0,
            "avg_overlap": 0.0,
            "survived_count": 0,
            "avg_hybrid_score": 0.0,
            "is_low_quality": True,
        }

    query_lemmas = _lemmatize(query)

    overlaps = []
    hybrid_scores = []
    for r in results:
        chunk_text = (r.content or "") + " " + (r.summary or "")
        chunk_lemmas = _lemmatize(chunk_text)
        overlap = len(query_lemmas & chunk_lemmas)
        norm_overlap = overlap / max(len(query_lemmas), 1)
        overlaps.append(norm_overlap)
        hybrid_scores.append(r.score_hybrid)

    avg_overlap = sum(overlaps) / len(overlaps)
    avg_hybrid = sum(hybrid_scores) / len(hybrid_scores)

    # Quality score: blend overlap (40%) + count (20%) + hybrid (40%)
    count_factor = min(len(results) / 5, 1.0)  # 0–1, saturates at 5 results
    score = 0.4 * avg_overlap + 0.2 * count_factor + 0.4 * avg_hybrid
    score = max(0.0, min(1.0, score))

    threshold = config.SOURCE_QUALITY_THRESHOLD
    is_low = score < threshold

    return {
        "score": round(score, 3),
        "avg_overlap": round(avg_overlap, 3),
        "survived_count": len(results),
        "avg_hybrid_score": round(avg_hybrid, 3),
        "is_low_quality": is_low,
    }


def compute_overlap_score(
    results: List[SearchResult],
    query: str,
) -> List[float]:
    """
    Compute token overlap scores for diagnostics (does not filter).

    Returns a list of overlap scores (0.0–1.0) matching the results list.
    """
    query_lemmas = _lemmatize(query)
    if not query_lemmas:
        return [0.0] * len(results)

    scores = []
    for r in results:
        chunk_text = (r.content or "") + " " + (r.summary or "")
        chunk_lemmas = _lemmatize(chunk_text)

        overlap = len(query_lemmas & chunk_lemmas)
        # Normalize by query token count
        norm_score = overlap / max(len(query_lemmas), 1)
        scores.append(norm_score)

    return scores
