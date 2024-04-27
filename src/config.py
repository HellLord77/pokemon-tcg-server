import os
from typing import Final
from typing import Optional

LOGGING_LEVEL: Final[str] = os.getenv("LOGGING_LEVEL", "INFO").upper()

DEBUG_FASTAPI: Final[bool] = os.getenv("DEBUG_FASTAPI", "false").lower() == "true"

CORS_ALLOW_ORIGIN: Final[str] = os.getenv("CORS_ALLOW_ORIGIN", "*")
MAX_PAGE_SIZE: Final[int] = int(os.getenv("MAX_PAGE_SIZE", 250))
IMAGE_URL_BASE: Final[Optional[str]] = os.getenv("IMAGE_URL_BASE")

DATA_DIRECTORY: Final[str] = os.getenv("DATA_DIRECTORY", "data")
INDEX_DIRECTORY: Final[str] = os.getenv("INDEX_DIRECTORY", "index")
