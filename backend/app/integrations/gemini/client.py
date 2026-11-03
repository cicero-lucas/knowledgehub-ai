from functools import lru_cache

import google.generativeai as genai

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def _configure_genai() -> None:
    """Configure the Google Generative AI SDK with the API key from settings."""
    genai.configure(api_key=settings.GEMINI_API_KEY)
    logger.info(
        "gemini_configured",
        generation_model=settings.GEMINI_GENERATION_MODEL,
        embedding_model=settings.GEMINI_EMBEDDING_MODEL,
    )


@lru_cache(maxsize=1)
def get_generation_model() -> genai.GenerativeModel:
    """Return a cached GenerativeModel instance."""
    _configure_genai()
    return genai.GenerativeModel(model_name=settings.GEMINI_GENERATION_MODEL)


def get_genai_module():
    """Return the configured genai module for embedding calls."""
    _configure_genai()
    return genai
