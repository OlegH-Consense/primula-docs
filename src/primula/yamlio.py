"""YAML reading by the YAML 1.2 core schema with the Primula rules.

Specification section 12.6 (decision 25): YAML in file headers and in
``load_yaml`` is read with the YAML 1.2 core schema plus two rules:

* a number with a fractional part and no exponent is a ``decimal``
  (:class:`decimal.Decimal`) with the number of digits as written;
* an unquoted scalar of the form ``YYYY-MM-DD`` is a ``datetime`` at
  00:00:00, of the form ``YYYY-MM-DDTHH:MM[:SS]`` a ``datetime`` with the
  time (:class:`~primula.core.values.DateTime`, decision 109); a
  non-existent date of that form (``2026-13-45``) is an error, and so is a
  value with a time zone (``Z``, ``+02:00``): zones are not supported.

Integers are ``decimal`` values with scale 0 (Python ``int``); numbers with
an exponent, ``.inf`` and ``.nan`` are ``float``; a quoted scalar is always
a string; booleans are only ``true`` and ``false`` (any capitalisation
allowed by the core schema).  String mapping keys are normalised to NFKC
(section 3.9); keys that coincide after normalisation are duplicates.

PyYAML (https://pyyaml.org/wiki/PyYAMLDocumentation) implements YAML 1.1,
where ``yes``/``no``/``on``/``off`` are booleans, ``010`` is octal and
``1:20`` is sexagesimal.  Therefore only PyYAML's scanner, parser and
composer are used; tag resolution is replaced by :class:`_CoreResolver`
(regular expressions of the YAML 1.2 core schema, YAML 1.2.2 section
10.3.2, https://yaml.org/spec/1.2.2/#1032-tag-resolution), and the node
graph is converted to Python values by this module instead of PyYAML
constructors.  No Python object can be created from YAML: unknown tags are
errors.

Additional checks beyond PyYAML:

* duplicate mapping keys are errors (YAML 1.2 requires unique keys,
  PyYAML silently keeps the last value);
* recursive aliases (``&a [*a]``) are errors;
* complex (non-scalar) mapping keys are errors;
* warnings for values that changed meaning against YAML 1.1 and are
  likely author mistakes: ``yes``/``no``/``on``/``off`` (now strings) and
  integers with leading zeros such as ``01234567`` (an identification code
  would lose its leading zero).

Positions are character offsets in the YAML text (PyYAML ``Mark.index``
counts characters of a ``str`` stream); callers add the offset of the
YAML text in the source file.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

import yaml
from yaml.composer import Composer
from yaml.nodes import MappingNode, Node, ScalarNode, SequenceNode
from yaml.parser import Parser
from yaml.reader import Reader
from yaml.resolver import BaseResolver
from yaml.scanner import Scanner

from primula.core.values import DateTime, DateTimeError, parse_iso_datetime
from primula.unicode import nfkc

#: Path of a value inside a YAML document: mapping keys and list indexes.
YamlPath = tuple[Any, ...]

_TAG_PREFIX = "tag:yaml.org,2002:"
TAG_NULL = _TAG_PREFIX + "null"
TAG_BOOL = _TAG_PREFIX + "bool"
TAG_INT = _TAG_PREFIX + "int"
TAG_FLOAT = _TAG_PREFIX + "float"
TAG_STR = _TAG_PREFIX + "str"
TAG_SEQ = _TAG_PREFIX + "seq"
TAG_MAP = _TAG_PREFIX + "map"
#: Private tag of the Primula date rule.
TAG_DATE = "tag:primula-docs,2026:date"

# YAML 1.2.2 core schema, section 10.3.2 (order matters: int before float).
_RE_NULL = re.compile(r"^(?:~|null|Null|NULL|)$")
_RE_BOOL = re.compile(r"^(?:true|True|TRUE|false|False|FALSE)$")
_RE_INT = re.compile(r"^(?:[-+]?[0-9]+|0o[0-7]+|0x[0-9a-fA-F]+)$")
_RE_FLOAT = re.compile(
    r"^(?:[-+]?(?:\.[0-9]+|[0-9]+(?:\.[0-9]*)?)(?:[eE][-+]?[0-9]+)?"
    r"|[-+]?\.(?:inf|Inf|INF)|\.(?:nan|NaN|NAN))$"
)
_RE_DATE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}(?:T[0-9]{2}:[0-9]{2}(?::[0-9]{2})?"
                      r"(?:Z|[-+][0-9]{2}(?::?[0-9]{2})?)?)?$")

# Plain scalars that were booleans in YAML 1.1 but are strings in 1.2.
_YAML11_BOOLEANS = frozenset(
    "yes Yes YES no No NO on On ON off Off OFF".split()
)
# Decimal integer with a leading zero (not 0 itself): "007", "-01".
_RE_LEADING_ZERO = re.compile(r"^[-+]?0[0-9]+$")


class _CoreResolver(BaseResolver):
    """Implicit tag resolution of the YAML 1.2 core schema + Primula dates."""


# BaseResolver.add_implicit_resolver copies the class registry on first
# use, so these registrations do not affect PyYAML's own loaders.
# `first=None` makes every resolver a candidate for any first character.
for _tag, _regexp in ((TAG_NULL, _RE_NULL), (TAG_BOOL, _RE_BOOL), (TAG_INT, _RE_INT),
                      (TAG_FLOAT, _RE_FLOAT), (TAG_DATE, _RE_DATE)):
    _CoreResolver.add_implicit_resolver(_tag, _regexp, None)


class _ComposeLoader(Reader, Scanner, Parser, Composer, _CoreResolver):
    """PyYAML pipeline up to the node graph, with the core resolver."""

    def __init__(self, stream: str) -> None:
        Reader.__init__(self, stream)
        Scanner.__init__(self)
        Parser.__init__(self)
        Composer.__init__(self)
        _CoreResolver.__init__(self)


@dataclass
class YamlIssue:
    """A problem found while reading YAML.

    Attributes:
        kind: ``syntax``, ``date``, ``zone``, ``duplicate``, ``tag``, ``recursive``,
            ``complex_key`` (errors) or ``bool11``, ``leading_zero``
            (warnings).
        start: offset of the problem in the YAML text.
        end: end offset of the problem.
        args: message arguments (``problem``, ``value``, ``key``, ``tag``).
        related: span of a related place (first occurrence of a
            duplicate key; start of the enclosing construct of a syntax
            error, described by ``args["context"]``), or ``None``.
    """

    kind: str
    start: int
    end: int
    args: dict[str, object] = field(default_factory=dict)
    related: tuple[int, int] | None = None


class YamlError(Exception):
    """Reading stopped at an error.

    Args:
        issue: the error.
    """

    def __init__(self, issue: YamlIssue) -> None:
        super().__init__(issue.kind)
        self.issue = issue


@dataclass
class YamlDocument:
    """Result of reading a YAML text.

    Attributes:
        value: the converted value (``None`` for an empty document).
        value_spans: path -> (start, end) of every value node.
        key_spans: path -> (start, end) of the key of every mapping entry.
        warnings: non-fatal issues in document order.
    """

    value: Any
    value_spans: dict[YamlPath, tuple[int, int]] = field(default_factory=dict)
    key_spans: dict[YamlPath, tuple[int, int]] = field(default_factory=dict)
    warnings: list[YamlIssue] = field(default_factory=list)

    def span_of(self, path: YamlPath, *, key: bool = False) -> tuple[int, int] | None:
        """Return the span of a value (or of its key) by path, if known."""
        return (self.key_spans if key else self.value_spans).get(path)


def load(text: str) -> YamlDocument:
    """Read a YAML text with the YAML 1.2 core schema and Primula rules.

    Args:
        text: YAML text (one document).

    Returns:
        The converted document with positions and warnings.

    Raises:
        YamlError: syntax error or a violation of the rules above.
    """
    loader: _ComposeLoader | None = None
    try:
        # The reader checks for non-printable characters already in the
        # constructor, so the constructor is inside the try block too.
        loader = _ComposeLoader(text)
        root = loader.get_single_node()
    except yaml.MarkedYAMLError as exc:
        mark = exc.problem_mark or exc.context_mark
        offset = mark.index if mark is not None else 0
        problem = exc.problem or exc.context or "syntax error"
        issue = YamlIssue("syntax", offset, offset, {"problem": problem})
        # PyYAML also reports where the enclosing construct started
        # ("while parsing a flow sequence" at the opening bracket).
        if exc.problem and exc.context and exc.context_mark is not None \
                and exc.context_mark is not exc.problem_mark:
            issue.related = (exc.context_mark.index, exc.context_mark.index + 1)
            issue.args["context"] = exc.context
        raise YamlError(issue) from None
    except yaml.reader.ReaderError as exc:
        # Non-printable character (YAML 1.2.2 section 5.1).
        raise YamlError(YamlIssue("syntax", exc.position, exc.position + 1,
                                  {"problem": f"special character #x{exc.character:04X} is not allowed"
                                   if isinstance(exc.character, int)
                                   else str(exc)})) from None
    except yaml.YAMLError as exc:  # pragma: no cover - defensive
        raise YamlError(YamlIssue("syntax", 0, 0, {"problem": str(exc)})) from None
    finally:
        if loader is not None:
            loader.dispose()

    document = YamlDocument(value=None)
    if root is not None:
        document.value = _Converter(document).convert(root, ())
    return document


class _Converter:
    """Converts a PyYAML node graph to Python values and records positions."""

    def __init__(self, document: YamlDocument) -> None:
        self.document = document
        # Node ids on the current conversion path (recursion detection).
        self._active: set[int] = set()

    def convert(self, node: Node, path: YamlPath) -> Any:
        """Convert one node.

        Args:
            node: the node.
            path: its path in the document.

        Returns:
            The Python value.

        Raises:
            YamlError: see :func:`load`.
        """
        start, end = node.start_mark.index, node.end_mark.index
        self.document.value_spans[path] = (start, end)
        if isinstance(node, ScalarNode):
            return self._scalar(node, start, end)
        if id(node) in self._active:
            raise YamlError(YamlIssue("recursive", start, end))
        self._active.add(id(node))
        try:
            if isinstance(node, SequenceNode):
                self._require_tag(node, TAG_SEQ, start, end)
                return [self.convert(item, path + (index,)) for index, item in enumerate(node.value)]
            if isinstance(node, MappingNode):
                self._require_tag(node, TAG_MAP, start, end)
                return self._mapping(node, path)
        finally:
            self._active.discard(id(node))
        raise YamlError(YamlIssue("tag", start, end, {"tag": node.tag}))  # pragma: no cover

    @staticmethod
    def _require_tag(node: Node, expected: str, start: int, end: int) -> None:
        """Reject an explicit tag on a collection other than !!seq / !!map."""
        if node.tag != expected:
            raise YamlError(YamlIssue("tag", start, end, {"tag": node.tag}))

    def _mapping(self, node: MappingNode, path: YamlPath) -> dict[Any, Any]:
        """Convert a mapping, rejecting complex and duplicate keys."""
        result: dict[Any, Any] = {}
        first_seen: dict[Any, tuple[int, int]] = {}
        for key_node, value_node in node.value:
            key_start, key_end = key_node.start_mark.index, key_node.end_mark.index
            if not isinstance(key_node, ScalarNode):
                raise YamlError(YamlIssue("complex_key", key_start, key_end))
            key = self._scalar(key_node, key_start, key_end)
            if isinstance(key, str):
                key = nfkc(key)
            try:
                hash(key)
            except TypeError:  # pragma: no cover - scalars are hashable
                raise YamlError(YamlIssue("complex_key", key_start, key_end)) from None
            if key in first_seen:
                raise YamlError(YamlIssue("duplicate", key_start, key_end, {"key": str(key)},
                                          related=first_seen[key]))
            first_seen[key] = (key_start, key_end)
            self.document.key_spans[path + (key,)] = (key_start, key_end)
            result[key] = self.convert(value_node, path + (key,))
        return result

    def _scalar(self, node: ScalarNode, start: int, end: int) -> Any:
        """Convert a scalar by its (resolved or explicit) tag."""
        value: str = node.value
        tag = node.tag
        if tag == TAG_STR:
            if node.style is None:
                self._warn_plain_string(value, start, end)
            return value
        if tag == TAG_NULL:
            if _RE_NULL.match(value) is None:
                raise _cannot_convert(value, tag, start, end)
            return None
        if tag == TAG_BOOL:
            if _RE_BOOL.match(value) is None:
                raise _cannot_convert(value, tag, start, end)
            return value.lower() == "true"
        if tag == TAG_INT:
            if _RE_INT.match(value) is None:
                raise _cannot_convert(value, tag, start, end)
            if node.style is None and _RE_LEADING_ZERO.match(value):
                self.document.warnings.append(YamlIssue("leading_zero", start, end, {"value": value}))
            return _to_int(value)
        if tag == TAG_FLOAT:
            if _RE_FLOAT.match(value) is None:
                raise _cannot_convert(value, tag, start, end)
            return _to_number(value)
        if tag == TAG_DATE:
            try:
                return parse_iso_datetime(value)
            except DateTimeError as exc:
                kind = "zone" if str(exc) == "time zone" else "date"
                raise YamlError(YamlIssue(kind, start, end, {"value": value})) from None
        raise YamlError(YamlIssue("tag", start, end, {"tag": tag}))

    def _warn_plain_string(self, value: str, start: int, end: int) -> None:
        """Record warnings for plain strings that were booleans in YAML 1.1."""
        if value in _YAML11_BOOLEANS:
            self.document.warnings.append(YamlIssue("bool11", start, end, {"value": value}))


def _cannot_convert(value: str, tag: str, start: int, end: int) -> YamlError:
    """Error for an explicitly tagged scalar that does not fit its tag."""
    short = tag.replace(_TAG_PREFIX, "!!")
    return YamlError(YamlIssue("syntax", start, end, {"problem": f"cannot read '{value}' as {short}"}))


def _to_int(value: str) -> int:
    """Convert a core-schema integer (decimal, ``0o`` octal, ``0x`` hex)."""
    if value.startswith("0o"):
        return int(value[2:], 8)
    if value.startswith("0x"):
        return int(value[2:], 16)
    return int(value, 10)


def _to_number(value: str) -> Decimal | float | int:
    """Convert a core-schema float literal by the Primula rules.

    A fraction without an exponent is a :class:`~decimal.Decimal` keeping
    the digits as written (``12.50`` -> ``Decimal('12.50')``); an exponent,
    ``.inf`` and ``.nan`` give ``float``.  A plain integer written with an
    explicit ``!!float`` tag is a ``Decimal`` as well.
    """
    lowered = value.lower()
    if "e" in lowered or "inf" in lowered or "nan" in lowered:
        if lowered.endswith(".inf"):
            return float("-inf") if lowered.startswith("-") else float("inf")
        if lowered.endswith(".nan"):
            return float("nan")
        return float(value)
    return Decimal(value)


def type_key(value: Any) -> str:
    """Return the catalogue key (``type.*``) naming the type of a value.

    Args:
        value: a value produced by :func:`load`.
    """
    if value is None:
        return "type.null"
    if isinstance(value, bool):
        return "type.boolean"
    if isinstance(value, int):
        return "type.integer"
    if isinstance(value, Decimal):
        return "type.decimal"
    if isinstance(value, float):
        return "type.float"
    if isinstance(value, DateTime):
        return "type.datetime"
    if isinstance(value, str):
        return "type.string"
    if isinstance(value, list):
        return "type.sequence"
    if isinstance(value, dict):
        return "type.mapping"
    return "type.string"  # pragma: no cover - load() produces no other types
