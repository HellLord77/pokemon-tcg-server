import functools
import time
from contextlib import asynccontextmanager
from typing import NoReturn
from typing import Optional

import fastapi
import lucene
import uvicorn
from fastapi import FastAPI
from fastapi import Path
from fastapi import Query
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

import config
import description
import exception
import init
from common import JSONResponse
from exception import ExceptionEX
from model import CardModel
from model import ExceptionModel
from model import SearchCardModel
from model import SearchSetModel
from model import SetModel
from model import StringSetModel

RESOURCES = {}


@asynccontextmanager
async def lifespan(_: FastAPI):
    RESOURCES.update(init.load_index())
    yield
    RESOURCES.clear()


app = FastAPI(
    debug=config.FASTAPI_DEBUG,
    title=description.TITLE,
    lifespan=lifespan,
    responses={fastapi.status.HTTP_200_OK: {"description": description.ERROR_200}},
)
# noinspection PyTypeChecker
app.add_middleware(
    CORSMiddleware,
    allow_origins=(config.CORS_ALLOW_ORIGIN,),
    allow_methods=("*",),
    allow_headers=("*",),
)
# noinspection PyTypeChecker
app.add_middleware(GZipMiddleware)

_ = {
    fastapi.status.HTTP_400_BAD_REQUEST: {
        "model": ExceptionModel,
        "description": description.ERROR_400,
    },
    fastapi.status.HTTP_402_PAYMENT_REQUIRED: {
        "model": ExceptionModel,
        "description": description.ERROR_402,
    },
    fastapi.status.HTTP_403_FORBIDDEN: {
        "model": ExceptionModel,
        "description": description.ERROR_403,
    },
    fastapi.status.HTTP_404_NOT_FOUND: {
        "model": ExceptionModel,
        "description": description.ERROR_404,
    },
    fastapi.status.HTTP_429_TOO_MANY_REQUESTS: {
        "model": ExceptionModel,
        "description": description.ERROR_429,
    },
    fastapi.status.HTTP_500_INTERNAL_SERVER_ERROR: {
        "model": ExceptionModel,
        "description": description.ERROR_500,
    },
    fastapi.status.HTTP_502_BAD_GATEWAY: {
        "model": ExceptionModel,
        "description": description.ERROR_500,
    },
    fastapi.status.HTTP_503_SERVICE_UNAVAILABLE: {
        "model": ExceptionModel,
        "description": description.ERROR_500,
    },
    fastapi.status.HTTP_504_GATEWAY_TIMEOUT: {
        "model": ExceptionModel,
        "description": description.ERROR_500,
    },
}


def _get_schema_resource(
    name: str, id_: str, select: Optional[list[str]]
) -> JSONResponse:
    id_ = id_.strip().lower()
    if id_.isdigit():
        id_ = int(id_)
    # noinspection PyUnresolvedReferences
    lucene.getVMEnv().attachCurrentThread()
    resource = RESOURCES[name]
    try:
        hits = (resource[id_],)
    except IndexError:
        raise exception.NotFoundException
    else:
        return JSONResponse({"data": next(resource.iter_hits(hits, select))})


def _search_schema_resource(
    name: str,
    q: Optional[str],
    page: int,
    page_size: int,
    order_by: Optional[list[str]],
    select: Optional[list[str]],
) -> JSONResponse:
    page = max(1, page)
    page_size = max(1, min(page_size, config.MAX_PAGE_SIZE))
    # noinspection PyUnresolvedReferences
    lucene.getVMEnv().attachCurrentThread()
    resource = RESOURCES[name]
    hits = resource.search(q, order_by)
    # noinspection PyTypeChecker
    data = list(
        resource.iter_hits(hits, select, (page - 1) * page_size, page * page_size)
    )
    return JSONResponse(
        {
            "data": data,
            "page": page,
            "pageSize": page_size,
            "count": len(data),
            "totalCount": len(hits),
        }
    )


# noinspection PyShadowingBuiltins
@app.get("/cards/{id}", response_model=CardModel, description=description.ROUTE_CARD)
def get_a_card(
    id: str = Path(description=description.PATH_CARD_ID),
    select: Optional[list[str]] = Query(None, description=description.QUERY_SELECT),
) -> JSONResponse:
    return _get_schema_resource("card", id, select)


# noinspection PyPep8Naming
@app.get(
    "/cards", response_model=SearchCardModel, description=description.ROUTE_SEARCH_CARD
)
def search_cards(
    q: str = Query(None, description=description.QUERY_SEARCH_Q),
    page: int = Query(1, description=description.QUERY_SEARCH_PAGE),
    pageSize: int = Query(
        config.MAX_PAGE_SIZE, description=description.QUERY_SEARCH_PAGESIZE
    ),
    orderBy: Optional[list[str]] = Query(
        None, description=description.QUERY_SEARCH_ORDERBY
    ),
    select: Optional[list[str]] = Query(None, description=description.QUERY_SELECT),
) -> JSONResponse:
    return _search_schema_resource("card", q, page, pageSize, orderBy, select)


# noinspection PyShadowingBuiltins
@app.get("/sets/{id}", response_model=SetModel, description=description.ROUTE_SET)
def get_a_set(
    id: str = Path(description=description.PATH_SET_ID),
    select: Optional[list[str]] = Query(None, description=description.QUERY_SELECT),
) -> JSONResponse:
    return _get_schema_resource("set", id, select)


# noinspection PyPep8Naming
@app.get(
    "/sets", response_model=SearchSetModel, description=description.ROUTE_SEARCH_SET
)
def search_sets(
    q: str = Query(None, description=description.QUERY_SEARCH_Q),
    page: int = Query(1, description=description.QUERY_SEARCH_PAGE),
    pageSize: int = Query(
        config.MAX_PAGE_SIZE, description=description.QUERY_SEARCH_PAGESIZE
    ),
    orderBy: Optional[list[str]] = Query(
        None, description=description.QUERY_SEARCH_ORDERBY
    ),
    select: Optional[list[str]] = Query(None, description=description.QUERY_SELECT),
) -> JSONResponse:
    return _search_schema_resource("set", q, page, pageSize, orderBy, select)


@functools.cache
def _get_string_set_resource_cached(name: str) -> dict[str, list[str]]:
    return {"data": RESOURCES[name].get_state()}


def _get_string_set_resource(name: str) -> JSONResponse:
    return JSONResponse(_get_string_set_resource_cached(name))


@app.get("/types", response_model=StringSetModel, description=description.ROUTE_TYPES)
def get_types() -> JSONResponse:
    return _get_string_set_resource("type")


@app.get(
    "/subtypes",
    response_model=StringSetModel,
    description=description.ROUTE_SUBTYPES,
)
def get_subtypes() -> JSONResponse:
    return _get_string_set_resource("subtype")


@app.get(
    "/supertypes",
    response_model=StringSetModel,
    description=description.ROUTE_SUPERTYPES,
)
def get_supertypes() -> JSONResponse:
    return _get_string_set_resource("supertype")


@app.get(
    "/rarities",
    response_model=StringSetModel,
    description=description.ROUTE_RARITIES,
)
def get_rarities() -> JSONResponse:
    return _get_string_set_resource("rarity")


@app.middleware("http")
async def add_runtime_header_middleware(request: Request, call_next):
    start_time = time.monotonic()
    response = await call_next(request)
    response.headers["X-Runtime"] = str(time.monotonic() - start_time)
    return response


@app.exception_handler(Exception)
async def exception_handler(request: Request, _: Exception) -> JSONResponse:
    return await exception_ex_handler(request, exception.ServerErrorException)


@app.exception_handler(ExceptionEX)
async def exception_ex_handler(_: Request, exc: ExceptionEX) -> JSONResponse:
    return JSONResponse(
        content={"error": {"message": exc.message, "code": exc.code}},
        status_code=exc.code,
    )


@app.exception_handler(RequestValidationError)
async def request_validation_error_handler(
    _: Request, __: RequestValidationError
) -> NoReturn:
    raise exception.BadRequestException


def main():
    uvicorn.run(app)


if __name__ == "__main__":
    main()
