import uuid
from pathlib import Path

import aiofiles

from app.core.config import settings
from app.core.logging import get_logger
from app.shared.exceptions import StorageError

logger = get_logger(__name__)


class LocalStorage:
    """Handles local filesystem storage for uploaded files.

    Designed to be easily swapped with an S3-compatible implementation.
    """

    def __init__(self, base_dir: str | None = None) -> None:
        self.base_dir = Path(base_dir or settings.UPLOAD_DIR)

    def _user_dir(self, user_id: str) -> Path:
        user_path = self.base_dir / user_id
        user_path.mkdir(parents=True, exist_ok=True)
        return user_path

    def generate_filename(self, original_name: str) -> str:
        """Generate a unique safe filename preserving the extension."""
        suffix = Path(original_name).suffix.lower()
        return f"{uuid.uuid4().hex}{suffix}"

    async def save(self, user_id: str, filename: str, content: bytes) -> str:
        """Persist file bytes and return the relative path."""
        user_dir = self._user_dir(user_id)
        file_path = user_dir / filename
        try:
            async with aiofiles.open(file_path, "wb") as f:
                await f.write(content)
            logger.info("file_saved", path=str(file_path), size=len(content))
            return str(file_path)
        except OSError as exc:
            raise StorageError(f"Failed to save file: {exc}") from exc

    def get_full_path(self, file_path: str) -> Path:
        return Path(file_path)

    async def delete(self, file_path: str) -> None:
        """Delete a file from storage."""
        path = Path(file_path)
        try:
            if path.exists():
                path.unlink()
                logger.info("file_deleted", path=str(path))
        except OSError as exc:
            raise StorageError(f"Failed to delete file: {exc}") from exc

    def exists(self, file_path: str) -> bool:
        return Path(file_path).exists()

    def read_bytes(self, file_path: str) -> bytes:
        """Synchronous read for use in background tasks."""
        path = Path(file_path)
        if not path.exists():
            raise StorageError(f"File not found: {file_path}")
        return path.read_bytes()


# Singleton instance
storage = LocalStorage()
