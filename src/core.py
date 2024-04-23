from typing import Callable
from typing import Iterable
from typing import Iterator
from typing import Mapping
from typing import Optional

import org
from lupyne.engine import Analyzer
from lupyne.engine import Field
from lupyne.engine import Indexer
from lupyne.engine import Query
from org.apache.lucene.analysis.core import KeywordTokenizer
from org.apache.lucene.analysis.core import LetterTokenizer
from org.apache.lucene.analysis.core import LowerCaseFilter
from org.apache.lucene.analysis.core import UnicodeWhitespaceTokenizer
from org.apache.lucene.search import SortField
from org.apache.lucene.search import SortedSetSortField
from org.apache.pylucene.queryparser.classic import PythonQueryParser
from org.apache.pylucene.queryparser.complexPhrase import PythonComplexPhraseQueryParser

from common import logger


class AnalyzerEX(Analyzer):
    @classmethod
    def unicode_whitespace(cls, *filters: Callable) -> Analyzer:
        logger.debug("unicode_whitespace%s", locals())
        return cls(UnicodeWhitespaceTokenizer, *filters)

    @classmethod
    def keyword(cls, *filters: Callable) -> Analyzer:
        logger.debug("keyword%s", locals())
        return cls(KeywordTokenizer, *filters)

    @classmethod
    def simple(cls, *filters: Callable) -> Analyzer:
        logger.debug("simple%s", locals())
        return cls(LetterTokenizer, LowerCaseFilter, *filters)


class PythonQueryParserMixin:
    def __init__(
        self,
        field: str,
        analyzer: Analyzer,
        *,
        use_classic_parser: Optional[bool] = None,
        enable_position_increments: Optional[bool] = None,
        allow_leading_wildcard: Optional[bool] = None,
        auto_generate_multi_term_synonyms_phrase_query: Optional[bool] = None,
        auto_generate_phrase_queries: Optional[bool] = None,
        split_on_whitespace: Optional[bool] = None,
        numeric_fields: Optional[Iterable[str]] = None,
        numeric_like_fields: Optional[Mapping[str, str]] = None,
        field_value_maps: Optional[Mapping[str, Callable[[str], Optional[str]]]] = None,
    ):
        logger.debug("PythonQueryParserMixin%s", locals())
        super().__init__(field, analyzer)
        if use_classic_parser is not None:
            self.useClassicParser = use_classic_parser
        if enable_position_increments is not None:
            self.enablePositionIncrements = enable_position_increments
        if allow_leading_wildcard is not None:
            self.allowLeadingWildcard = allow_leading_wildcard
        if auto_generate_multi_term_synonyms_phrase_query is not None:
            self.autoGenerateMultiTermSynonymsPhraseQuery = (
                auto_generate_multi_term_synonyms_phrase_query
            )
        if auto_generate_phrase_queries is not None:
            self.autoGeneratePhraseQueries = auto_generate_phrase_queries
        if split_on_whitespace is not None:
            self.splitOnWhitespace = split_on_whitespace
        if numeric_fields is None:
            numeric_fields = ()
        if numeric_like_fields is None:
            numeric_like_fields = {}
        if field_value_maps is None:
            field_value_maps = {}
        self.numeric_fields = {*numeric_fields, *numeric_like_fields}
        self.numeric_like_fields = numeric_like_fields
        self.field_value_maps = field_value_maps

    def _get_field_and_texts(
        self, field: str, *texts: Optional[str]
    ) -> Iterator[Optional[str]]:
        yield self.numeric_like_fields.get(field, field)
        for text in texts:
            if text is not None:
                try:
                    field_value_map = self.field_value_maps[field]
                except KeyError:
                    pass
                else:
                    text = field_value_map(text)
            yield text

    # noinspection PyPep8Naming
    def getFuzzyQuery(self, field: str, termText: str, minSimilarity: float) -> Query:
        logger.debug("getFuzzyQuery%s", locals())
        # noinspection PyUnresolvedReferences
        return super().getFuzzyQuery(
            *self._get_field_and_texts(field, termText), minSimilarity
        )

    # noinspection PyPep8Naming
    def getPrefixQuery(self, field: str, termText: str) -> Query:
        logger.debug("getPrefixQuery%s", locals())
        # noinspection PyUnresolvedReferences
        return super().getPrefixQuery(*self._get_field_and_texts(field, termText))

    # noinspection PyPep8Naming
    def getRangeQuery(
        self,
        field: str,
        part1: Optional[str],
        part2: Optional[str],
        startInclusive: bool,
        endInclusive: bool,
    ) -> Query:
        logger.debug("getRangeQuery%s", locals())
        numeric_like_field, part1, part2 = self._get_field_and_texts(
            field, part1, part2
        )
        if field in self.numeric_fields:
            if (part1 is None or self.is_numeric(part1)) and (
                part2 is None or self.is_numeric(part2)
            ):
                if part1 is not None:
                    part1 = self.get_numeric(part1)
                if part2 is not None:
                    part2 = self.get_numeric(part2)
                return Query.ranges(
                    field, (part1, part2), lower=startInclusive, upper=endInclusive
                )
            else:
                field = numeric_like_field
        # noinspection PyUnresolvedReferences
        return super().getRangeQuery(field, part1, part2, startInclusive, endInclusive)

    # noinspection PyPep8Naming
    def getWildcardQuery(self, field: str, termText: str) -> Query:
        logger.debug("getWildcardQuery%s", locals())
        # noinspection PyUnresolvedReferences
        return super().getWildcardQuery(*self._get_field_and_texts(field, termText))

    # noinspection PyPep8Naming
    def getFieldQuery_quoted(self, field: str, queryText: str, quoted: bool) -> Query:
        logger.debug("getFieldQuery_quoted%s", locals())
        numeric_like_field, queryText = self._get_field_and_texts(field, queryText)
        if field in self.numeric_fields:
            if self.is_numeric(queryText):
                return Query.points(field, self.get_numeric(queryText))
            else:
                field = numeric_like_field
        # noinspection PyUnresolvedReferences
        return super().getFieldQuery_quoted_super(field, queryText, quoted)

    # noinspection PyPep8Naming
    def getFieldQuery_slop(self, field: str, queryText: str, slop: int) -> Query:
        logger.debug("getFieldQuery_slop%s", locals())
        # noinspection PyUnresolvedReferences
        return super().getFieldQuery_slop_super(
            *self._get_field_and_texts(field, queryText), slop
        )

    @staticmethod
    def is_numeric(string: str) -> bool:
        try:
            float(string)
        except ValueError:
            return False
        else:
            return True

    @staticmethod
    def get_numeric(string: int | float | str) -> int | float:
        number = float(string)
        if number.is_integer():
            number = int(number)
        return number


class PythonQueryParserEX(PythonQueryParserMixin, PythonQueryParser):
    pass


class PythonComplexPhraseQueryParserEX(
    PythonQueryParserMixin, PythonComplexPhraseQueryParser
):
    pass


class FieldEX(Field):
    # noinspection PyPep8Naming
    def __init__(
        self,
        name: str,
        docValuesType: str = "",
        indexOptions: str = "",
        dimensions: int = 0,
        **settings,
    ):
        super().__init__(name, docValuesType, indexOptions, dimensions, **settings)
        if docValuesType.startswith("SORTED_"):
            self.sort_field_class = getattr(
                org.apache.lucene.search,
                self.docValueClass.__name__.removesuffix("DocValuesField")
                + "SortField",
            )
        else:
            self.sort_field_class = SortField

    # noinspection PyPep8Naming
    @classmethod
    def SortableText(cls, name: str, docValuesType: str = "SORTED", **settings):
        return cls.Text(name, docValuesType=docValuesType, **settings)

    # noinspection PyPep8Naming
    @classmethod
    def SortableTextGroup(
        cls, name: str, docValuesType: str = "SORTED_SET", **settings
    ):
        return cls.Text(name, docValuesType=docValuesType, **settings)

    # noinspection PyPep8Naming
    @classmethod
    def Numeric(cls, name: str, dimension: int = 1, **settings):
        return cls(name, dimensions=dimension, **settings)

    # noinspection PyPep8Naming
    @classmethod
    def SortableNumeric(cls, name: str, docValuesType: str = "NUMERIC", **settings):
        return cls.Numeric(name, docValuesType=docValuesType, **settings)

    # noinspection PyPep8Naming
    @classmethod
    def SortableNumericGroup(
        cls, name: str, docValuesType: str = "SORTED_NUMERIC", **settings
    ):
        return cls.Numeric(name, docValuesType=docValuesType, **settings)


class IndexerEX(Indexer):
    def __init__(
        self,
        directory: str,
        mode: str = "a",
        analyzer=None,
        version=None,
        nrt=False,
        **attrs,
    ):
        super().__init__(directory, mode, analyzer, version, nrt, **attrs)
        self.parser = PythonQueryParserEX

    # noinspection PyShadowingBuiltins
    def sortfield(
        self,
        name: str,
        type: Optional[str | SortField.Type] = None,
        reverse: bool = False,
    ) -> SortField:
        sort_field_class = self.fields[name].sort_field_class
        if sort_field_class is SortedSetSortField:
            arg_type = ()
        else:
            if type is None:
                type = self.fieldinfos[name].docValuesType.toString()
            arg_type = (getattr(SortField.Type, Field.types.get(type, type).upper()),)
        return sort_field_class(name, *arg_type, reverse)

    def parse(self, query: str, spellcheck: bool = False, **kwargs) -> Query:
        kwargs.setdefault("parser", self.parser)
        return super().parse(query, spellcheck, **kwargs)
