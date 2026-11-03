class GeminiAPIError(Exception):
    """Raised when the Gemini API returns an unexpected error."""
    def __init__(self, message: str, status_code: int | None = None):
        self.status_code = status_code
        super().__init__(message)


class GeminiRateLimitError(GeminiAPIError):
    """Raised when the Gemini API rate limit is exceeded."""
    pass


class GeminiTimeoutError(GeminiAPIError):
    """Raised when a Gemini API call times out."""
    pass
