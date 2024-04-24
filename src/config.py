import os
from typing import Final

LOGGING_LEVEL: Final[str] = os.getenv("LOGGING_LEVEL", "INFO").upper()

DEBUG_FASTAPI: Final[bool] = os.getenv("DEBUG_FASTAPI", "false").lower() == "true"

MAX_PAGE_SIZE: Final[int] = int(os.getenv("MAX_PAGE_SIZE", 250))

DATA_DIRECTORY: Final[str] = os.getenv("DATA_DIRECTORY", "data")
RESOURCE_DIRECTORY: Final[str] = os.getenv("RESOURCE_DIRECTORY", "index")
