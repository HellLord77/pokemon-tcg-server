from __future__ import annotations

import os.path
from typing import Iterable
from typing import Mapping

from base import ResourceIndexer
from common import json
from common import logger
from schema import SchemaBuilder
from schema import SchemaFieldType


class SimpleResource:
    def __init__(self, path: str):
        self._path = path
        if os.path.exists(path):
            self.load()

    def dump(self):
        obj = self.get_state()
        logger.debug("dump%s", {"path": self._path, "obj": obj})
        os.makedirs(os.path.dirname(self._path), exist_ok=True)
        with open(self._path, "w") as file:
            json.dump(obj, file, indent=2)

    def load(self):
        with open(self._path, "r") as file:
            obj = json.load(file)
        logger.debug("load%s", {"path": self._path, "obj": obj})
        self.set_state(obj)

    def get_state(self) -> SimpleResource:
        return self

    def set_state(self, state):
        raise NotImplementedError


class SchemaBuilderResource(SimpleResource, SchemaBuilder):
    def get_state(self) -> dict[str, str]:
        return {name: field_type.name for name, field_type in self.items()}

    def set_state(self, state: Mapping[str, str]):
        self.clear()
        for name, field_type in state.items():
            self[name] = SchemaFieldType[field_type]


class SchemaResource(ResourceIndexer):
    RESOURCE: str

    def __init__(self, directory: str, mode: str = "r"):
        directory = os.path.join(directory, self.RESOURCE)
        super().__init__(directory, mode)
        self.schema_builder = SchemaBuilderResource(
            os.path.join(directory, "schema.json")
        )
        self.add_schema = self.schema_builder.add
        self.commit_schema()

    def commit_schema(self):
        self.schema_builder.commit(self)


class CardResource(SchemaResource):
    RESOURCE = "card"


class SetResource(SchemaResource):
    RESOURCE = "set"


class StringSetResource(SimpleResource, set[str]):
    RESOURCE: str

    def __init__(self, directory: str):
        super().__init__(os.path.join(directory, self.RESOURCE + ".json"))

    def get_state(self) -> list[str]:
        return sorted(self)

    def set_state(self, state: Iterable[str]):
        self.clear()
        self.update(state)


class TypeResource(StringSetResource):
    RESOURCE = "type"


class SubTypeResource(StringSetResource):
    RESOURCE = "subtype"


class SuperTypeResource(StringSetResource):
    RESOURCE = "supertype"


class RarityResource(StringSetResource):
    RESOURCE = "rarity"
