import os
from typing import Final
from typing import Optional

LOGGING_LEVEL: Final[str] = os.getenv("LOGGING_LEVEL", "INFO").upper()

FASTAPI_DEBUG: Final[bool] = os.getenv("FASTAPI_DEBUG", "false").lower() == "true"

LUCENE_COUNT: Final[Optional[int]] = int(os.getenv("LUCENE_COUNT", "0")) or None
LUCENE_TIMEOUT: Final[Optional[int]] = int(os.getenv("LUCENE_TIMEOUT", "0")) or None

DATA_DIRECTORY: Final[str] = os.getenv("DATA_DIRECTORY", "data")
INDEX_DIRECTORY: Final[str] = os.getenv("INDEX_DIRECTORY", "index")

CORS_ALLOW_ORIGIN: Final[str] = os.getenv("CORS_ALLOW_ORIGIN", "*")
CORS_ALLOW_METHOD: Final[str] = os.getenv("CORS_ALLOW_METHOD", "*")
CORS_ALLOW_HEADER: Final[str] = os.getenv("CORS_ALLOW_HEADER", "*")

MAX_PAGE_SIZE: Final[int] = int(os.getenv("MAX_PAGE_SIZE", 250))
IMAGE_URL_BASE: Final[Optional[str]] = os.getenv("IMAGE_URL_BASE")
