from dataclasses import dataclass
from typing import Any

from pokemontcgsdk import Card
from pokemontcgsdk import Set


@dataclass
class SimpleModel:
    data: Any


@dataclass
class SchemaModel(SimpleModel):
    data: Card | Set


@dataclass
class SearchSchemaModel(SimpleModel):
    data: list[Card | Set]
    page: int
    pageSize: int
    count: int
    totalCount: int


@dataclass
class CardModel(SchemaModel):
    data: Card


@dataclass
class SearchCardModel(SearchSchemaModel):
    data: list[Card]


@dataclass
class SetModel(SchemaModel):
    data: Set


@dataclass
class SearchSetModel(SearchSchemaModel):
    data: list[Set]


@dataclass
class StringSetModel(SimpleModel):
    data: list[str]


@dataclass
class ErrorModel:
    message: str
    code: int


@dataclass
class ExceptionModel:
    error: ErrorModel
