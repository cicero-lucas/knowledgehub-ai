"""
Embedding generation using the Google Generative Language REST API v1.

The google-generativeai SDK defaults to the v1beta endpoint where embedding
models are not available for all API keys. This module calls the stable v1
endpoint directly via httpx to ensure compatibility.
"""

import httpx
from typing import List

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.config import settings
from app.core.logging import get_logger
from app.integrations.gemini.exceptions import GeminiAPIError, GeminiRateLimitError

logger = get_logger(__name__)

# Stable v1 REST endpoint — embedding models are available here
_BASE_URL = "https://generativelanguage.googleapis.com/v1"


def _get_embed_model() -> str:
    """Read embedding model from settings at call time (not import time)."""
    return settings.GEMINI_EMBEDDING_MODEL


def _is_rate_limit(status_code: int, body: str) -> bool:
    return status_code == 429 or "quota" in body.lower()


@retry(
    retry=retry_if_exception_type(GeminiRateLimitError),
    wait=wait_exponential(multiplier=2, min=4, max=60),
    stop=stop_after_attempt(settings.GEMINI_MAX_RETRIES),
    reraise=True,
)
def _embed_single(text: str, task_type: str = "RETRIEVAL_DOCUMENT") -> List[float]:
    """Call the v1 embedContent REST endpoint for a single text."""
    embed_model = _get_embed_model()
    url = f"{_BASE_URL}/{embed_model}:embedContent"
    payload = {
        "model": embed_model,
        "content": {"parts": [{"text": text}]},
        "taskType": task_type,
    }
    params = {"key": settings.GEMINI_API_KEY}

    with httpx.Client(timeout=settings.GEMINI_GENERATION_TIMEOUT) as client:
        response = client.post(url, json=payload, params=params)

    if _is_rate_limit(response.status_code, response.text):
        logger.warning("gemini_rate_limit_embedding", status=response.status_code)
        raise GeminiRateLimitError(f"Rate limit: {response.text[:200]}")

    if response.status_code != 200:
        logger.error(
            "gemini_embedding_error",
            status=response.status_code,
            body=response.text[:300],
        )
        raise GeminiAPIError(f"Embedding API error {response.status_code}: {response.text[:200]}")

    data = response.json()
    embedding = data.get("embedding", {}).get("values", [])
    if not embedding:
        raise GeminiAPIError(f"Empty embedding in response: {data}")

    return embedding


def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings for a list of texts.
    Calls the v1 REST API once per text.
    Returns embeddings in the same order as input.
    """
    if not texts:
        return []

    all_embeddings: List[List[float]] = []
    for i, text in enumerate(texts):
        logger.info("embedding_text", index=i, total=len(texts))
        embedding = _embed_single(text, task_type="RETRIEVAL_DOCUMENT")
        all_embeddings.append(embedding)

    return all_embeddings


def embed_query(query: str) -> List[float]:
    """
    Generate an embedding for a query string.
    Uses RETRIEVAL_QUERY task type for better semantic search matching.
    """
    return _embed_single(query, task_type="RETRIEVAL_QUERY")
