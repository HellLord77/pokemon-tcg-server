import enum
import functools
from typing import Any
from typing import Mapping

from lupyne.engine.utils import Atomic

from base import ResourceIndexer
from base import ResourcePythonComplexPhraseQueryParser
from core import FieldEX


class SchemaFieldType(enum.Flag):
    GROUP = 0b0001
    TEXT = 0b0010
    TEXT_GROUP = TEXT | GROUP
    NUMERIC = 0b0100
    NUMERIC_GROUP = NUMERIC | GROUP
    NUMERIC_LIKE = 0b1000
    NUMERIC_LIKE_GROUP = NUMERIC_LIKE | GROUP


_SETTERS = {
    SchemaFieldType.TEXT: ResourceIndexer.set_text,
    SchemaFieldType.TEXT_GROUP: functools.partial(ResourceIndexer.set_text, group=True),
    SchemaFieldType.NUMERIC: ResourceIndexer.set_numeric,
    SchemaFieldType.NUMERIC_GROUP: functools.partial(
        ResourceIndexer.set_numeric, group=True
    ),
    SchemaFieldType.NUMERIC_LIKE: ResourceIndexer.set_numeric_like,
    SchemaFieldType.NUMERIC_LIKE_GROUP: functools.partial(
        ResourceIndexer.set_numeric_like, group=True
    ),
}


class SchemaBuilder(dict):
    def add(self, items: Mapping[str, Any]):
        for name, texts in items.items():
            field_type = self.get(name, SchemaFieldType.TEXT)
            group = not isinstance(texts, Atomic)
            if not group:
                texts = (texts,)
            if texts:
                if isinstance(texts[0], int):
                    field_type = SchemaFieldType.NUMERIC
                elif SchemaFieldType.NUMERIC_LIKE not in field_type:
                    is_numeric = map(
                        ResourcePythonComplexPhraseQueryParser.is_numeric, texts
                    )
                    if SchemaFieldType.NUMERIC in field_type:
                        if not all(is_numeric):
                            field_type = SchemaFieldType.NUMERIC_LIKE
                    elif any(is_numeric):
                        field_type = SchemaFieldType.NUMERIC_LIKE
            if group:
                field_type |= SchemaFieldType.GROUP
            self[name] = field_type

    def commit(self, indexer: ResourceIndexer):
        for name, field_type in self.items():
            _SETTERS[field_type](indexer, name)
        indexer.set(ResourceIndexer.FIELD_RAW, FieldEX, stored=True)
