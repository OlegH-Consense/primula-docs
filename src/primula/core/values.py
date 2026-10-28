"""Value types of the computing core (specification 12.3-12.6; v1.1: decisions 108-111).

Python representation of Primula types:

==============  ==========================================================
Primula type    Python value
==============  ==========================================================
``NoneType``    ``None``
``bool``        ``bool``
``decimal``     :class:`decimal.Decimal`, or ``int`` for an integer value
                (scale 0; there is no separate ``int`` type, decision 108);
                at most 64 significant digits
``float``       ``float``
``str``         ``str`` (NFC normalised by the lexical stage)
``list``        :class:`PList` — ``list`` with a frozen flag
``tuple``       ``tuple``
``dict``        :class:`PDict` — ``dict`` with a frozen flag
``record``      :class:`Record`
``datetime``    :class:`DateTime` — whole seconds from 1899-12-30
                (decision 109; a date is the moment 00:00:00)
``length``      :class:`Length` — decimal value + unit (decision 110)
``content``     :class:`Content` (opaque in the core; stage 13.3)
``function``    :class:`Function`, :class:`Builtin`, :class:`BoundMethod`
==============  ==========================================================

The interpreter never reaches Python attributes of these objects directly:
attributes and methods available to Primula code are listed in
:mod:`primula.core.builtins`.  Freezing (12.7) marks lists and
dictionaries immutable; records, tuples, dates and lengths are immutable
by construction.  A style is a plain string with its name (decision 111).
"""

from __future__ import annotations

import ast
import datetime
import decimal
import re
from dataclasses import dataclass, field
from decimal import Decimal
from fractions import Fraction
from typing import Any, Callable

from primula.unicode import is_identifier as _is_identifier
from primula.unicode import nfkc as _nfkc

#: Decimal context of division and other inexact operations: 28
#: significant digits, half away from zero (decision 41, 12.4); invalid
#: operations, division by zero and overflow raise instead of producing
#: NaN or infinity.
DECIMAL_CONTEXT = decimal.Context(
    prec=28, rounding=decimal.ROUND_HALF_UP, Emax=999_999, Emin=-999_999,
    traps=[decimal.InvalidOperation, decimal.DivisionByZero, decimal.Overflow],
)

#: Maximal number of significant digits of a ``decimal`` (12.4, decision 108).
MAX_DIGITS = 64

#: Context of exact operations (``+ - *``, integer powers): a result that
#: needs more than :data:`MAX_DIGITS` digits raises ``Inexact`` — the
#: "number overflow" error of 12.4.
EXACT_CONTEXT = decimal.Context(
    prec=MAX_DIGITS, rounding=decimal.ROUND_HALF_UP, Emax=999_999, Emin=-999_999,
    traps=[decimal.InvalidOperation, decimal.DivisionByZero, decimal.Overflow, decimal.Inexact],
)

#: Integers below this bound fit in :data:`MAX_DIGITS` digits.
INT_BOUND = 10 ** MAX_DIGITS


def digits_ok(value: Any) -> bool:
    """Whether a ``decimal`` (``int`` or ``Decimal``) has at most 64 significant digits.

    An integer written with a positive exponent (``Decimal("1E+70")``)
    counts all digits of its integer value (scale 0).
    """
    if isinstance(value, int):
        return -INT_BOUND < value < INT_BOUND
    if not value.is_finite():
        return False
    sign, digits, exponent = value.as_tuple()
    return len(digits) + max(exponent, 0) <= MAX_DIGITS


class PList(list):
    """A Primula list: a Python list with freezing and iteration guards."""

    __slots__ = ("frozen", "iterating")

    def __init__(self, *args: Any) -> None:
        super().__init__(*args)
        self.frozen = False
        self.iterating = 0


class PDict(dict):
    """A Primula dictionary (insertion order) with freezing and iteration guards."""

    __slots__ = ("frozen", "iterating")

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.frozen = False
        self.iterating = 0


class Record:
    """Immutable record with dot access (12.6).

    Fields keep their order.  Two records are equal when their fields and
    values are equal; a record is hashable when all values are (dictionary
    keys, decision 43).

    Args:
        fields: field name -> value.
    """

    __slots__ = ("_fields",)

    def __init__(self, fields: dict[str, Any]) -> None:
        object.__setattr__(self, "_fields", dict(fields))

    @property
    def fields(self) -> dict[str, Any]:
        """The fields (do not modify)."""
        return self._fields

    def __setattr__(self, name: str, value: Any) -> None:  # pragma: no cover - guard
        raise AttributeError("records are immutable")

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Record) and self._fields == other._fields

    def __hash__(self) -> int:
        return hash(tuple(self._fields.items()))


@dataclass(frozen=True)
class Length:
    """A length: decimal value and the unit of writing (decision 110).

    Units convert with fixed factors (1 inch = 25.4 mm = 2.54 cm = 72 pt);
    the result of an operation with different units is in the unit of the
    left operand (:func:`convert_length`).  In Primula code ``==`` and the
    ordering compare with a tolerance of 0.001 mm (12.3, implemented by
    the interpreter); the Python ``==`` and hash of this class are exact
    and serve internal tables.

    Attributes:
        value: the value in ``unit`` (``Decimal``).
        unit: ``mm``, ``cm``, ``pt`` or ``inch``.
    """

    value: Decimal
    unit: str = "mm"

    @property
    def inches(self) -> Fraction:
        """Exact value in inches (layout code computes with fractions)."""
        return Fraction(self.value) * UNIT_INCHES[self.unit]

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Length) and self.inches == other.inches

    def __hash__(self) -> int:
        return hash(self.inches)

    def in_unit(self, unit: str) -> Fraction:
        """The value in ``unit`` as an exact fraction."""
        return self.inches / UNIT_INCHES[unit]

    @classmethod
    def from_inches(cls, inches: Fraction, unit: str = "mm") -> "Length":
        """A length of ``inches`` written in ``unit`` (28 digits if inexact)."""
        return cls(fraction_to_decimal(inches / UNIT_INCHES[unit]), unit)


def convert_length(length: Length, unit: str) -> Decimal:
    """Value of ``length`` in ``unit`` by decimal division (12.3, 28 digits)."""
    if length.unit == unit:
        return length.value
    return fraction_to_decimal(Fraction(length.value) * UNIT_INCHES[length.unit] / UNIT_INCHES[unit])


#: Tolerance of length comparisons (12.3): 0.001 mm in inches.
LENGTH_TOLERANCE = Fraction(1, 25400)


#: Inches per unit; exact (1 inch = 25.4 mm = 72 pt).
UNIT_INCHES: dict[str, Fraction] = {
    "mm": Fraction(10, 254), "cm": Fraction(100, 254), "pt": Fraction(1, 72), "inch": Fraction(1),
}

_LENGTH_RE = re.compile(r"^\s*([-+]?(?:\d+(?:\.\d*)?|\.\d+))\s*(mm|cm|pt|in|inch)\s*$")


def parse_length(text: str) -> Length | None:
    """Parse ``"10mm"``, ``"2.5 cm"``, ``"12pt"``, ``"1in"``; ``None`` if invalid."""
    match = _LENGTH_RE.match(text)
    if match is None:
        return None
    unit = "inch" if match.group(2) in ("in", "inch") else match.group(2)
    return Length(Decimal(match.group(1)), unit)


def fraction_to_decimal(value: Fraction) -> Decimal:
    """Convert a fraction to ``decimal`` (exact when finite, else 28 digits)."""
    return DECIMAL_CONTEXT.divide(Decimal(value.numerator), Decimal(value.denominator))


def format_length(length: Length) -> str:
    """``str`` of a length (12.3): the value in its unit and the unit.

    Trailing zeros of the fraction are kept as written (``"2.50mm"``).
    """
    return f"{decimal_to_str(length.value)}{length.unit}"


# ----------------------------------------------------------------------
# datetime (12.3, decision 109)
# ----------------------------------------------------------------------

#: Epoch of serial numbers: 1899-12-30 00:00:00 (as in spreadsheets).
EPOCH = datetime.datetime(1899, 12, 30)
_SECONDS_PER_DAY = 86400
_MIN_SECONDS = int((datetime.datetime(1, 1, 1) - EPOCH).total_seconds())
_MAX_SECONDS = int((datetime.datetime(9999, 12, 31, 23, 59, 59) - EPOCH).total_seconds())


class DateTimeError(ValueError):
    """A ``datetime`` outside the years 1-9999 or an invalid date."""


@dataclass(frozen=True, order=True)
class DateTime:
    """A moment without a time zone, to the second (12.3, decision 109).

    The specification models the value as a ``float64`` serial number
    (days from 1899-12-30, the fraction is the time of day) normalised to
    whole seconds; whole seconds are stored here, which gives the same
    observable results (comparison, hash, ``float(dt)``, arithmetic).

    Attributes:
        seconds: whole seconds from :data:`EPOCH`.
    """

    seconds: int

    @classmethod
    def of(cls, year: int, month: int, day: int, hour: int = 0, minute: int = 0,
           second: int = 0) -> "DateTime":
        """Build from parts; raises :class:`DateTimeError` for an invalid moment."""
        try:
            moment = datetime.datetime(year, month, day, hour, minute, second)
        except (ValueError, OverflowError) as exc:
            raise DateTimeError(str(exc)) from None
        return cls.from_python(moment)

    @classmethod
    def from_python(cls, moment: datetime.date) -> "DateTime":
        """From a Python ``date`` or naive ``datetime`` (microseconds are dropped)."""
        if not isinstance(moment, datetime.datetime):
            moment = datetime.datetime(moment.year, moment.month, moment.day)
        if moment.tzinfo is not None:
            raise DateTimeError("time zone")
        delta = moment.replace(microsecond=0) - EPOCH
        return cls(delta.days * _SECONDS_PER_DAY + delta.seconds)

    @classmethod
    def from_seconds(cls, seconds: int) -> "DateTime":
        """From seconds since the epoch; checks the range of years 1-9999."""
        if not _MIN_SECONDS <= seconds <= _MAX_SECONDS:
            raise DateTimeError("year out of range 1-9999")
        return cls(seconds)

    def to_python(self) -> datetime.datetime:
        """The moment as a naive Python ``datetime``."""
        return EPOCH + datetime.timedelta(seconds=self.seconds)

    @property
    def is_date(self) -> bool:
        """The time of day is 00:00:00."""
        return self.seconds % _SECONDS_PER_DAY == 0

    def serial(self) -> Fraction:
        """Days from the epoch as an exact fraction (``float(dt)``, 12.3)."""
        return Fraction(self.seconds, _SECONDS_PER_DAY)

    def __str__(self) -> str:
        return self.iso()

    def iso(self) -> str:
        """``str(dt)``: ``YYYY-MM-DD`` at 00:00:00, else ``YYYY-MM-DDTHH:MM:SS``."""
        moment = self.to_python()
        if self.is_date:
            return f"{moment.year:04d}-{moment.month:02d}-{moment.day:02d}"
        return (f"{moment.year:04d}-{moment.month:02d}-{moment.day:02d}"
                f"T{moment.hour:02d}:{moment.minute:02d}:{moment.second:02d}")


#: Attributes of ``datetime`` (12.3).
DATETIME_ATTRIBUTES = ("year", "month", "day", "hour", "minute", "second", "weekday")


def datetime_attribute(value: DateTime, name: str) -> int:
    """``dt.year`` … ``dt.weekday`` (1-7, Monday is 1)."""
    moment = value.to_python()
    if name == "weekday":
        return moment.isoweekday()
    return getattr(moment, name)


_ISO_DATE_RE = re.compile(r"(\d{4})-(\d{2})-(\d{2})")
_ISO_DATETIME_RE = re.compile(r"(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2})(?::(\d{2}))?")
_ZONE_RE = re.compile(r"(?:Z|[+-]\d{2}(?::?\d{2})?)$")


def parse_iso_datetime(text: str, *, time: bool = True) -> DateTime:
    """Parse ``YYYY-MM-DD`` or (``time=True``) ``YYYY-MM-DDTHH:MM[:SS]``.

    Raises:
        DateTimeError: invalid text or date; the message ``time zone``
            marks a value with a zone (12.3: not supported).
    """
    text = text.strip()
    match = _ISO_DATE_RE.fullmatch(text)
    if match is not None:
        return DateTime.of(int(match.group(1)), int(match.group(2)), int(match.group(3)))
    if time:
        match = _ISO_DATETIME_RE.fullmatch(text)
        if match is not None:
            return DateTime.of(*(int(group or 0) for group in match.groups()))
        if _ISO_DATETIME_RE.match(text) is not None and _ZONE_RE.search(text):
            raise DateTimeError("time zone")
    raise DateTimeError("format")


@dataclass(eq=False)
class Content:
    """Marked-up content (macro body, ``markup(…)``); opaque in the core.

    Attributes:
        nodes: evaluated nodes of the tree.
        kind: ``blocks`` (macro body, ``markup()``) or ``inline`` (an
            inline body ``{…}``).
    """

    nodes: list[Any] = field(default_factory=list)
    kind: str = "blocks"


@dataclass(eq=False)
class ModuleValue:
    """A module connected with ``|import`` (10.3): ``module.name`` access.

    Attributes:
        name: namespace name.
        scope: the module's global scope (a :class:`~primula.core.scope.GlobalScope`).
    """

    name: str
    scope: Any

    def lookup(self, name: str, span: Any) -> Any:
        """Value of an exported name (names with ``_`` are private, decision 52)."""
        return self.scope.lookup(name, span)


@dataclass(eq=False)
class Function:
    """A user function defined with ``def`` (12.2).

    Attributes:
        name: function name.
        node: the ``ast.FunctionDef``.
        fragment: position map of the code containing the definition.
        closure: environment of the definition (enclosing function or
            global scope).
        defaults: frozen default values of positional parameters.
        kw_defaults: frozen default values of keyword-only parameters
            (``None`` entries where there is no default).
        local_names: names bound in the body (Python scoping rules).
    """

    name: str
    node: ast.FunctionDef
    fragment: Any
    closure: Any
    defaults: list[Any]
    kw_defaults: list[Any]
    local_names: frozenset[str]


@dataclass(eq=False)
class Builtin:
    """A built-in function implemented in Python.

    Attributes:
        name: name in Primula code.
        impl: ``impl(interp, args, kwargs, span) -> value``.
    """

    name: str
    impl: Callable[..., Any]


@dataclass(eq=False)
class BoundMethod:
    """A method bound to its receiver (``"a,b".split``)."""

    name: str
    receiver: Any
    impl: Callable[..., Any]


#: Names of types returned by ``type()`` (decision 43).
def type_name(value: Any) -> str:
    """Return the Primula type name of a value (``type(x)``, messages)."""
    if value is None:
        return "NoneType"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, (int, Decimal)):
        return "decimal"
    if isinstance(value, float):
        return "float"
    if isinstance(value, str):
        return "str"
    if isinstance(value, PList):
        return "list"
    if isinstance(value, tuple):
        return "tuple"
    if isinstance(value, PDict):
        return "dict"
    if isinstance(value, Record):
        return "record"
    if isinstance(value, DateTime):
        return "datetime"
    if isinstance(value, Length):
        return "length"
    if isinstance(value, Content):
        return "content"
    if isinstance(value, (Function, Builtin, BoundMethod)):
        return "function"
    if isinstance(value, ModuleValue):
        return "module"
    return type(value).__name__  # pragma: no cover - foreign value


def is_number(value: Any) -> bool:
    """``decimal`` (``int`` or ``Decimal``) or ``float`` (not ``bool``)."""
    return isinstance(value, (int, Decimal, float)) and not isinstance(value, bool)


# ----------------------------------------------------------------------
# Freezing and keys
# ----------------------------------------------------------------------


def freeze(value: Any) -> Any:
    """Freeze a value deeply (12.7); returns the value."""
    if isinstance(value, (PList, PDict)):
        if value.frozen:
            return value
        value.frozen = True
        for item in (value.values() if isinstance(value, PDict) else value):
            freeze(item)
    elif isinstance(value, tuple):
        for item in value:
            freeze(item)
    elif isinstance(value, Record):
        for item in value.fields.values():
            freeze(item)
    return value


def is_valid_key(value: Any) -> bool:
    """Dictionary keys are immutable values; ``float`` and ``length`` are not (12.3)."""
    if value is None or isinstance(value, (bool, int, Decimal, str, DateTime)):
        return True
    if isinstance(value, tuple):
        return all(is_valid_key(item) for item in value)
    if isinstance(value, Record):
        return all(is_valid_key(item) for item in value.fields.values())
    return False


# ----------------------------------------------------------------------
# str() and repr()
# ----------------------------------------------------------------------


def decimal_to_str(value: Decimal) -> str:
    """``str(decimal)``: no exponent, digits kept (decision 41): ``2.20``, ``10``."""
    return format(value, "f")


#: Below Python's 4300-digit limit of ``str(int)`` (with a margin).
_STR_INT_BOUND = 10 ** 4000


def int_to_str(value: int) -> str:
    """``str(int)`` without Python's 4300-digit conversion limit."""
    if -_STR_INT_BOUND < value < _STR_INT_BOUND:
        return str(value)
    return format(Decimal(value), "f")


def to_str(value: Any) -> str:
    """``str(x)`` of a Primula value."""
    if isinstance(value, str):
        return value
    if isinstance(value, DateTime):
        return value.iso()
    if isinstance(value, Length):
        return format_length(value)
    return to_repr(value)


def to_repr(value: Any) -> str:
    """``repr(x)`` of a Primula value (Starlark-like, no Python internals)."""
    if value is None or isinstance(value, bool):
        return str(value)
    if isinstance(value, int):
        return int_to_str(value)
    if isinstance(value, Decimal):
        return decimal_to_str(value)
    if isinstance(value, float):
        return repr(value)
    if isinstance(value, str):
        return repr(value)
    if isinstance(value, PList):
        return "[" + ", ".join(to_repr(item) for item in value) + "]"
    if isinstance(value, tuple):
        inner = ", ".join(to_repr(item) for item in value)
        return f"({inner},)" if len(value) == 1 else f"({inner})"
    if isinstance(value, PDict):
        return "{" + ", ".join(f"{to_repr(k)}: {to_repr(v)}" for k, v in value.items()) + "}"
    if isinstance(value, Record):
        inner = ", ".join(f"{k}={to_repr(v)}" if _is_identifier(k) else f"{k!r}: {to_repr(v)}"
                          for k, v in value.fields.items())
        return f"record({inner})"
    if isinstance(value, DateTime):
        return f'{"date" if value.is_date else "datetime"}("{value.iso()}")'
    if isinstance(value, Length):
        return f'length("{format_length(value)}")'
    if isinstance(value, Content):
        return "<content>"
    if isinstance(value, (Function, Builtin, BoundMethod)):
        return f"<function {value.name}>"
    if isinstance(value, ModuleValue):
        return f"<module {value.name}>"
    return f"<{type_name(value)}>"  # pragma: no cover


# ----------------------------------------------------------------------
# Conversion of data (YAML, JSON, header parameters)
# ----------------------------------------------------------------------


def from_data(value: Any) -> Any:
    """Convert loaded data to Primula values (12.6).

    Mappings become records, sequences lists; scalars stay as they are
    (``yamlio`` already produces ``decimal`` and ``datetime``).  Record keys
    are normalised to NFKC (3.9); keys that coincide after normalisation are
    rejected earlier by the loaders.  The result is frozen.
    """
    return freeze(_from_data(value))


def _from_data(value: Any) -> Any:
    if isinstance(value, dict):
        return Record({_nfkc(str(k)): _from_data(v) for k, v in value.items()})
    if isinstance(value, (list, tuple)):
        return PList(_from_data(item) for item in value)
    return value
