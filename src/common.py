import logging

import lucene

import config

try:
    # noinspection PyPackageRequirements
    import ujson as json
except ImportError:
    import json
    from fastapi.responses import JSONResponse
else:
    from fastapi.responses import UJSONResponse as JSONResponse
try:
    # noinspection PyPackageRequirements
    import orjson
except ImportError:
    pass
else:
    from fastapi.responses import ORJSONResponse as JSONResponse

logger = logging.getLogger(__name__)
logging.basicConfig(level=config.LOGGING_LEVEL)

# noinspection PyUnresolvedReferences
assert lucene.getVMEnv() or lucene.initVM()
