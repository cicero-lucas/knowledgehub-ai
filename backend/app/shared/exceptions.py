from fastapi import HTTPException, status


class AppException(Exception):
    """Base application exception."""
    def __init__(self, message: str, code: str = "APP_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)


class NotFoundError(AppException):
    def __init__(self, resource: str, identifier: str | int | None = None):
        msg = f"{resource} not found"
        if identifier:
            msg += f": {identifier}"
        super().__init__(msg, "NOT_FOUND")


class ConflictError(AppException):
    def __init__(self, message: str):
        super().__init__(message, "CONFLICT")


class ForbiddenError(AppException):
    def __init__(self, message: str = "Access denied"):
        super().__init__(message, "FORBIDDEN")


class ValidationError(AppException):
    def __init__(self, message: str):
        super().__init__(message, "VALIDATION_ERROR")


class StorageError(AppException):
    def __init__(self, message: str):
        super().__init__(message, "STORAGE_ERROR")


class GeminiError(AppException):
    def __init__(self, message: str):
        super().__init__(message, "GEMINI_ERROR")


class DocumentProcessingError(AppException):
    def __init__(self, message: str):
        super().__init__(message, "DOCUMENT_PROCESSING_ERROR")


# ─── HTTP Exception Factories ─────────────────────────────────────────────────

def http_not_found(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


def http_conflict(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)


def http_forbidden(detail: str = "Access denied") -> HTTPException:
    return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


def http_unauthorized(detail: str = "Not authenticated") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def http_bad_request(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


def http_unprocessable(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail
    )
