import collections
import functools
import itertools
import re
from typing import Any
from typing import Callable
from typing import Iterable
from typing import Iterator
from typing import Mapping
from typing import MutableMapping
from typing import Optional

import jq
from java.lang import IllegalArgumentException
from java.util import HashMap
from lucene import JavaError
from lupyne.engine import Analyzer
from lupyne.engine import Query
from lupyne.engine.documents import Hit
from lupyne.engine.documents import Hits
from lupyne.engine.utils import Atomic
from org.apache.lucene.analysis.core import LowerCaseFilter
from org.apache.lucene.analysis.miscellaneous import WordDelimiterGraphFilterFactory
from org.apache.lucene.document import Document
from org.apache.lucene.queryparser.classic import ParseException
from org.apache.lucene.queryparser.flexible.standard import QueryParserUtil
from org.apache.lucene.search import BooleanQuery
from org.apache.lucene.search import SortField

from common import json
from common import logger
from core import AnalyzerEX
from core import FieldEX
from core import IndexerEX
from core import PythonComplexPhraseQueryParserEX


class ResourceAnalyzer(AnalyzerEX):
    @classmethod
    def resource(cls, *filters: Callable) -> Analyzer:
        logger.debug("resource%s", locals())
        word_delimiter_graph_filter_factory_args = HashMap()
        word_delimiter_graph_filter_factory_args.put("catenateWords", "1")
        word_delimiter_graph_filter_factory_args.put("catenateNumbers", "1")
        word_delimiter_graph_filter_factory_args.put("catenateAll", "1")
        word_delimiter_graph_filter_factory_args.put("preserveOriginal", "1")
        word_delimiter_graph_filter_factory_args.put("ignoreKeywords", "1")
        return cls.whitespace(
            LowerCaseFilter,
            WordDelimiterGraphFilterFactory(
                word_delimiter_graph_filter_factory_args
            ).create,
            *filters,
        )


class ResourcePythonComplexPhraseQueryParser(PythonComplexPhraseQueryParserEX):
    @staticmethod
    def is_numeric(string: str) -> bool:
        try:
            int(string)
        except ValueError:
            return False
        else:
            return True

    get_numeric = int


class ResourceIndexer(IndexerEX):
    FIELD_RAW = "_raw_"
    FIELD_DEFAULT = "name"
    FIELD_STORED = "id"

    _DELIMITER = ","
    _SEPARATOR = "."
    _SEPARATOR_ESCAPED = re.escape(_SEPARATOR)
    _FIELD_VALUE_MAPS = collections.defaultdict(lambda: str.lower)

    def __init__(self, directory: str, mode: str = "a"):
        analyzer = ResourceAnalyzer.resource()
        super().__init__(directory, mode, analyzer)
        self.shared.add(analyzer)
        self.numeric_fields = set()
        self.numeric_like_fields = {}
        self.parser = functools.partial(
            ResourcePythonComplexPhraseQueryParser,
            numeric_fields=self.numeric_fields,
            numeric_like_fields=self.numeric_like_fields,
            field_value_maps=self._FIELD_VALUE_MAPS,
            allow_leading_wildcard=True,
        )
        self.indices = tuple(self[index][self.FIELD_STORED] for index in self)

    def __getitem__(self, index):
        if isinstance(index, str):
            try:
                index = self.indices.index(index)
            except ValueError:
                raise IndexError
        try:
            return super().__getitem__(index)
        except JavaError as exc:
            java_exc = exc.getJavaException()
            if IllegalArgumentException.instance_(java_exc):
                raise IndexError
            else:
                raise

    @staticmethod
    def _patch_negative_query(query: Query):
        if BooleanQuery.instance_(query):
            boolean_query = BooleanQuery.cast_(query)
            clauses = boolean_query.clauses()
            if clauses.size() == 1:
                clause = clauses.get(0)
                if clause.isProhibited():
                    query = Query.alldocs() - clause.query
        return query

    # noinspection PyMethodOverriding
    def document(self, items: MutableMapping[str, Any]) -> Document:
        for name, texts in tuple(items.items()):
            is_numeric_field = name in self.numeric_fields
            is_numeric_like_field = name in self.numeric_like_fields
            if isinstance(texts, Atomic):
                texts = (texts,)
            field_texts = []
            numeric_like_field_texts = []
            for text in texts:
                if is_numeric_field:
                    field_texts.append(
                        ResourcePythonComplexPhraseQueryParser.get_numeric(text)
                    )
                elif is_numeric_like_field:
                    numeric_like_field_texts.append(str(text))
                    if ResourcePythonComplexPhraseQueryParser.is_numeric(text):
                        field_texts.append(
                            ResourcePythonComplexPhraseQueryParser.get_numeric(text)
                        )
                else:
                    field_texts.append(text)
            if is_numeric_like_field:
                items[self.numeric_like_fields[name]] = numeric_like_field_texts
            items[name] = field_texts
        return super().document(items)

    # noinspection PyMethodOverriding
    def parse(self, query: str) -> Query:
        return self._patch_negative_query(super().parse(query))

    def search(
        self, query: Optional[str] = None, sort: Optional[str | Iterable[str]] = None
    ) -> Hits:
        if query is not None:
            query = self.get_query(query)
        if sort is not None:
            sort = self.get_sort(sort)
        return self.indexSearcher.search(query, sort=sort)

    def set_text(self, field: str, group: bool = False) -> FieldEX:
        return self.set(
            field,
            FieldEX.SortableTextGroup if group else FieldEX.SortableText,
            stored=field == self.FIELD_STORED,
        )

    def set_numeric(self, field: str, group: bool = False) -> FieldEX:
        if field not in self.numeric_like_fields:
            self.numeric_fields.add(field)
        return self.set(
            field,
            FieldEX.SortableNumericGroup if group else FieldEX.SortableNumeric,
            stored=field == self.FIELD_STORED,
        )

    def set_numeric_like(self, field: str, group: bool = False) -> FieldEX:
        numeric_like_field = self.get_numeric_like_field(field)
        self.numeric_like_fields[field] = numeric_like_field
        self.set_text(numeric_like_field, group)
        return self.set_numeric(field, group)

    get_numeric_like_field = "_{}_".format

    def _flatten(self, obj, root: MutableMapping[str, Any], __parent: str = "") -> Any:
        if isinstance(obj, (str, int, float, bool)):
            return obj
        elif isinstance(obj, Iterable):
            if __parent:
                __parent += self._SEPARATOR
            for key, val in obj.items() if isinstance(obj, dict) else enumerate(obj):
                parent = f"{__parent}{key}"
                children = {}
                flattened = self._flatten(val, children, parent)
                if flattened is children:
                    root.update(children)
                else:
                    root[parent] = flattened
            return root

    def _merge(self, obj: Mapping[str, Any]) -> dict[str, Any]:
        merged = {}
        non_digit_keys = set()
        for key in obj.keys():
            parts = key.split(self._SEPARATOR)
            non_digit_parts = [
                part for part in key.split(self._SEPARATOR) if not part.isdigit()
            ]
            non_digit_key = self._SEPARATOR.join(non_digit_parts)
            if parts == non_digit_parts:
                merged[key] = obj[key]
            elif non_digit_key not in non_digit_keys:
                pattern = re.compile(
                    rf"{self._SEPARATOR_ESCAPED}\d+{self._SEPARATOR_ESCAPED}".join(
                        map(re.escape, non_digit_parts)
                    )
                    + rf"(?:{self._SEPARATOR_ESCAPED}\d+)?"
                )
                merged[non_digit_key] = [
                    val for key_, val in obj.items() if pattern.fullmatch(key_)
                ]
                non_digit_keys.add(non_digit_key)
        return merged

    def process(self, items: Mapping[str, Any]) -> dict[str, Any]:
        processed = self._merge(self._flatten(items, {}))
        processed[self.FIELD_RAW] = json.dumps(items, separators=(",", ":"))
        return processed

    @staticmethod
    def unprocess(obj: str, *filters: str):
        return next(
            jq.iter(
                f"with_entries(select(({') or ('.join(f'.key == {json.dumps(filter_)}' for filter_ in filters)})))",
                text=obj,
            )
        )

    @staticmethod
    @functools.cache
    def unprocess_cached(obj: str):
        return json.loads(obj)

    def get_query(self, query: str) -> Query:
        # TODO https://docs.pokemontcg.io/api-reference/cards/search-cards#exact-matching
        query = query.strip()
        if ":" in query:
            try:
                query = self.parse(query)
            except JavaError as exc:
                java_exc = exc.getJavaException()
                if not ParseException.instance_(java_exc):
                    logger.error("get_query%s", {"except": exc}, exc_info=exc)
                query = Query.nodocs()
        elif query:
            query = self.get_query(
                f'{self.FIELD_DEFAULT}:"{QueryParserUtil.escape(query) + "*"}"'
            )
        else:
            query = Query.alldocs()
        logger.debug("get_query%s", {"return": query})
        return query

    def get_sort(self, sorts: str | Iterable[str]) -> Optional[list[SortField]]:
        sort_fields = []
        if isinstance(sorts, str):
            sorts = (sorts,)
        for part in itertools.chain.from_iterable(
            sort.split(self._DELIMITER) for sort in sorts
        ):
            field = part.strip().replace(" ", "")
            name = field.removeprefix("-")
            if name in self.fields:
                sort_fields.append(self.sortfield(name, reverse=field.startswith("-")))
        logger.debug("get_sort%s", {"return": sort_fields})
        if sort_fields:
            return sort_fields

    def get_filter(self, filters: str | Iterable[str]) -> list[str]:
        filter_fields = []
        if isinstance(filters, str):
            filters = (filters,)
        for part in itertools.chain.from_iterable(
            filter_.split(self._DELIMITER) for filter_ in filters
        ):
            field = part.strip().replace(" ", "")
            prefix = field + self._SEPARATOR
            if field in self.fields or any(
                field_.startswith(prefix) for field_ in self.fields
            ):
                filter_fields.append(field)
        logger.debug("get_filter%s", {"return": filter_fields})
        return filter_fields

    def iter_hits(
        self,
        hits: Iterable[Hit],
        select: Optional[str | Iterable[str]] = None,
        start: int = 0,
        stop: Optional[int] = None,
    ) -> Iterator[dict[str, Any]]:
        filter_ = () if select is None else self.get_filter(select)
        unprocess = self.unprocess if filter_ else self.unprocess_cached
        return (
            unprocess(hit[self.FIELD_RAW], *filter_)
            for hit in itertools.islice(hits, start, stop)
        )
