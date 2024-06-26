from __future__ import annotations

import functools
import os.path
import urllib.parse
from typing import Iterable, Optional, Iterator, Any
from typing import Mapping
from typing import MutableMapping

from lupyne.engine.documents import Hit

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

    _IMAGE_URL_BASE = "https://images.pokemontcg.io/"

    def __init__(
        self,
        directory: str,
        mode: str = "r",
        *,
        search_count: Optional[int] = None,
        search_timeout: Optional[int] = None,
        image_url_base: Optional[str] = None,
    ):
        directory = os.path.join(directory, self.RESOURCE)
        super().__init__(directory, mode)
        self.indexSearcher.search = functools.partial(
            self.indexSearcher.search, count=search_count, timeout=search_timeout
        )
        self.image_url_base = image_url_base
        self.schema_builder = SchemaBuilderResource(
            os.path.join(directory, "schema.json")
        )
        self.commit_schema()

    def _replace_image_base_url(self, images: MutableMapping[str, str]):
        if any(url.startswith(self._IMAGE_URL_BASE) for url in images.values()):
            for image, url in images.items():
                images[image] = urllib.parse.urljoin(
                    self.image_url_base, url.removeprefix(self._IMAGE_URL_BASE)
                )

    def _replace_image_base_urls(self, obj: Mapping[str, Any]) -> Mapping[str, Any]:
        try:
            images = obj["images"]
        except KeyError:
            pass
        else:
            self._replace_image_base_url(images)
        return obj

    def iter_hits(
        self,
        hits: Iterable[Hit],
        select: Optional[str | Iterable[str]] = None,
        start: int = 0,
        stop: Optional[int] = None,
    ) -> Iterator[dict[str, Any]]:
        hits = super().iter_hits(hits, select, start, stop)
        if self.image_url_base is not None:
            hits = map(self._replace_image_base_urls, hits)
        return hits

    def add_schema(self, items: Mapping[str, Any]):
        self.schema_builder.add(items)

    def commit_schema(self):
        self.schema_builder.commit(self)


class CardResource(SchemaResource):
    RESOURCE = "card"

    def _replace_image_base_urls(self, obj: Mapping[str, Any]) -> Mapping[str, Any]:
        super()._replace_image_base_urls(obj)
        try:
            set_ = obj["set"]
        except KeyError:
            pass
        else:
            try:
                images = set_["images"]
            except KeyError:
                pass
            else:
                self._replace_image_base_url(images)
        return obj


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
