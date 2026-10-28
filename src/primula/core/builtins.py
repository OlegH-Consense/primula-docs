"""Built-in functions, methods and attributes (specification 12.10, decisions 43-45).

Functions: ``len``, ``range``, ``enumerate``, ``zip``, ``sorted``,
``reversed``, ``min``, ``max``, ``sum``, ``any``, ``all``, ``abs``,
``round``, ``int``, ``float``, ``dec``, ``str``, ``bool``, ``list``,
``tuple``, ``dict``, ``record``, ``type``, ``getattr``, ``hasattr``,
``repr``, ``fail``, ``debug``, ``build_date``, ``date``, ``datetime``;
plus the ``length`` constructor and the constants ``mm``, ``cm``, ``pt``,
``inch`` (12.3).  ``markup`` is added by document evaluation
(stage 13.3).

Methods: strings — ``split rsplit splitlines join strip lstrip rstrip
replace startswith endswith find rfind count upper lower capitalize title
isdigit isalpha isspace zfill format``; lists — ``append extend insert pop
remove index count sort reverse``; dictionaries — ``get keys values items
update pop setdefault``; records — ``replace``.

Attributes: record fields (names compared after NFKC, 3.9);
``datetime.year/month/day/hour/minute/second/weekday``;
``length.mm/cm/pt/inch`` (12.3).

This module is the *only* way Primula code reaches Python objects: an
attribute that is not listed here does not exist (P2313), so Python
internals (``__class__``…) are unreachable.  ``str.format`` does not allow
attribute access in fields (decision 45); widths in format specifications
are checked against the string limit before formatting.
"""

from __future__ import annotations

import _string
import functools
import re
import string
from decimal import Decimal
from fractions import Fraction
from typing import Any, Callable

from primula.core import numbers
from primula.core.errors import CoreError, core_error, resolve
from primula.core.values import (
    DATETIME_ATTRIBUTES, UNIT_INCHES, BoundMethod, Builtin, DateTime, DateTimeError, Length, ModuleValue,
    PDict, PList, Record, convert_length, datetime_attribute, fraction_to_decimal, is_valid_key,
    parse_iso_datetime, parse_length, to_repr, to_str, type_name,
)
from primula.unicode import nfkc
from primula.diagnostics import error
from primula.source import Span

# ----------------------------------------------------------------------
# Argument helpers
# ----------------------------------------------------------------------


def _arity(name: str, args: list[Any], kwargs: dict[str, Any], span: Span, low: int, high: int,
           keywords: tuple[str, ...] = ()) -> None:
    """Check the number of positional arguments and allowed keywords."""
    if not low <= len(args) <= high:
        expected = str(low) if low == high else f"{low}..{high}"
        raise core_error("P2321", span, function=name,
                         problem=f"takes {expected} positional arguments but {len(args)} were given")
    for key in kwargs:
        if key not in keywords:
            raise core_error("P2321", span, function=name, problem=f"got an unexpected keyword argument '{key}'")


def _expect(name: str, value: Any, kinds: tuple[type, ...], what: str, span: Span) -> Any:
    """Check the type of an argument (``bool`` is never an ``int``)."""
    if isinstance(value, bool) and bool not in kinds:
        ok = False
    else:
        ok = isinstance(value, kinds)
    if not ok:
        raise core_error("P2322", span, function=name, problem=f"expected {what}, not {type_name(value)}")
    return value


def _int(name: str, value: Any, span: Span) -> int:
    """A number with an integer value (``2``, ``2.0``, 12.4) as a Python ``int``."""
    result = numbers.as_integer(value)
    if result is None:
        raise core_error("P2322", span, function=name,
                         problem=f"expected an integer, not {type_name(value)} {to_repr(value)}")
    return result


def _str(name: str, value: Any, span: Span) -> str:
    return _expect(name, value, (str,), "str", span)


def _number_call(function: Callable[..., Any], span: Span, *args: Any) -> Any:
    try:
        return function(*args)
    except numbers.NumberError as exc:
        raise core_error(exc.code, span, **{"op": "", "left": "", "right": "", **exc.args_}) from None


def _sort_key(interp: Any, key: Any, span: Span) -> Callable[[Any], Any]:
    """A Python sort key that compares by Primula rules (decision 43)."""

    class _Key:
        __slots__ = ("value",)

        def __init__(self, item: Any) -> None:
            self.value = interp.call(key, [item], {}, span) if key is not None else item

        def __lt__(self, other: "_Key") -> bool:
            return interp.less(self.value, other.value, span)

    return _Key


# ----------------------------------------------------------------------
# Built-in functions
# ----------------------------------------------------------------------


def _len(interp: Any, args: list[Any], kwargs: dict[str, Any], span: Span) -> int:
    _arity("len", args, kwargs, span, 1, 1)
    value = args[0]
    if isinstance(value, (str, PList, tuple, PDict)):
        return len(value)
    raise core_error("P2322", span, function="len", problem=f"{type_name(value)} has no length")


def _range(interp: Any, args: list[Any], kwargs: dict[str, Any], span: Span) -> PList:
    _arity("range", args, kwargs, span, 1, 3)
    values = [_int("range", value, span) for value in args]
    if len(values) == 3 and values[2] == 0:
        raise core_error("P2322", span, function="range", problem="step cannot be zero")
    sequence = range(*values)
    interp.meter.check_collection(len(sequence), span)
    interp.meter.step(span, len(sequence))
    return PList(sequence)


def _enumerate(interp: Any, args: list[Any], kwargs: dict[str, Any], span: Span) -> PList:
    _arity("enumerate", args, kwargs, span, 1, 2, ("start",))
    start = _int("enumerate", kwargs.get("start", args[1] if len(args) > 1 else 0), span)
    items = interp.materialize(args[0], span)
    return PList((start + index, item) for index, item in enumerate(items))


def _zip(interp: Any, args: list[Any], kwargs: dict[str, Any], span: Span) -> PList:
    _arity("zip", args, kwargs, span, 0, 64)
    sequences = [interp.materialize(value, span) for value in args]
    return PList(zip(*sequences))


def _sorted(interp: Any, args: list[Any], kwargs: dict[str, Any], span: Span) -> PList:
    _arity("sorted", args, kwargs, span, 1, 1, ("key", "reverse"))
    items = interp.materialize(args[0], span)
    key = kwargs.get("key")
    reverse = interp.truthy(kwargs.get("reverse", False))
    interp.meter.step(span, len(items) * max(1, len(items).bit_length()))
    wrapper = _sort_key(interp, key, span)
    return PList(sorted(items, key=wrapper, reverse=reverse))


def _reversed(interp: Any, args: list[Any], kwargs: dict[str, Any], span: Span) -> PList:
    _arity("reversed", args, kwargs, span, 1, 1)
    return PList(reversed(interp.materialize(args[0], span)))


def _min_max(name: str, pick_less: bool) -> Callable[..., Any]:
    def impl(interp: Any, args: list[Any], kwargs: dict[str, Any], span: Span) -> Any:
        _arity(name, args, kwargs, span, 1, 1 << 20, ("key", "default"))
        items = interp.materialize(args[0], span) if len(args) == 1 else list(args)
        if not items:
            if "default" in kwargs:
                return kwargs["default"]
            raise core_error("P2322", span, function=name, problem="empty sequence")
        key = kwargs.get("key")
        keyed = [(interp.call(key, [item], {}, span) if key is not None else item, item) for item in items]
        best_key, best = keyed[0]
        for item_key, item in keyed[1:]:
            better = interp.less(item_key, best_key, span) if pick_less else interp.less(best_key, item_key, span)
            if better:
                best_key, best = item_key, item
        return best
    return impl


def _sum(interp: Any, args: list[Any], kwargs: dict[str, Any], span: Span) -> Any:
    _arity("sum", args, kwargs, span, 1, 2, ("start",))
    total = kwargs.get("start", args[1] if len(args) > 1 else 0)
    for item in interp.materialize(args[0], span):
        if isinstance(total, int) and not isinstance(total, bool) and total == 0 and isinstance(item, Length):
            total = Length(Decimal(0), item.unit)
        total = interp.binary("+", total, item, span)
    return total


def _any_all(name: str, want: bool) -> Callable[..., bool]:
    def impl(interp: Any, args: list[Any], kwargs: dict[str, Any], span: Span) -> bool:
        _arity(name, args, kwargs, span, 1, 1)
        for item in interp.materialize(args[0], span):
            if interp.truthy(item) == want:
                return want
        return not want
    return impl


def _abs(interp: Any, args: list[Any], kwargs: dict[str, Any], span: Span) -> Any:
    _arity("abs", args, kwargs, span, 1, 1)
    value = args[0]
    if isinstance(value, Length):
        return Length(abs(value.value), value.unit)
    _expect("abs", value, (int, Decimal, float), "a number", span)
    return abs(value)


def _round(interp: Any, args: list[Any], kwargs: dict[str, Any], span: Span) -> Any:
    _arity("round", args, kwargs, span, 1, 2, ("ndigits",))
    digits = kwargs.get("ndigits", args[1] if len(args) > 1 else None)
    if digits is not None:
        _int("round", digits, span)
    _expect("round", args[0], (int, Decimal, float), "a number", span)
    return _number_call(numbers.round_number, span, args[0], digits)


def _conversion(name: str, function: Callable[[Any], Any]) -> Callable[..., Any]:
    def impl(interp: Any, args: list[Any], kwargs: dict[str, Any], span: Span) -> Any:
        _arity(name, args, kwargs, span, 1, 1)
        return _number_call(function, span, args[0])
    return impl


def _str_builtin(interp: Any, args: list[Any], kwargs: dict[str, Any], span: Span) -> str:
    _arity("str", args, kwargs, span, 0, 1)
    return to_str(args[0]) if args else ""


def _repr(interp: Any, args: list[Any], kwargs: dict[str, Any], span: Span) -> str:
    _arity("repr", args, kwargs, span, 1, 1)
    return to_repr(args[0])


def _bool(interp: Any, args: list[Any], kwargs: dict[str, Any], span: Span) -> bool:
    _arity("bool", args, kwargs, span, 0, 1)
    return interp.truthy(args[0]) if args else False


def _list(interp: Any, args: list[Any], kwargs: dict[str, Any], span: Span) -> PList:
    _arity("list", args, kwargs, span, 0, 1)
    return PList(interp.materialize(args[0], span)) if args else PList()


def _tuple(interp: Any, args: list[Any], kwargs: dict[str, Any], span: Span) -> tuple:
    _arity("tuple", args, kwargs, span, 0, 1)
    return tuple(interp.materialize(args[0], span)) if args else ()


def _dict(interp: Any, args: list[Any], kwargs: dict[str, Any], span: Span) -> PDict:
    _arity("dict", args, {}, span, 0, 1)
    result = PDict()
    if args:
        source = args[0]
        if isinstance(source, PDict):
            result.update(source)
        elif isinstance(source, Record):
            result.update(source.fields)
        else:
            for pair in interp.materialize(source, span):
                if not isinstance(pair, (tuple, PList)) or len(pair) != 2:
                    raise core_error("P2322", span, function="dict", problem="expected pairs (key, value)")
                if not is_valid_key(pair[0]):
                    raise core_error("P2317", span, type=type_name(pair[0]))
                result[pair[0]] = pair[1]
    result.update(kwargs)
    interp.meter.check_collection(len(result), span)
    return result


def _record(interp: Any, args: list[Any], kwargs: dict[str, Any], span: Span) -> Record:
    _arity("record", args, {}, span, 0, 1)
    fields: dict[str, Any] = {}
    if args:
        source = args[0]
        if isinstance(source, Record):
            fields.update(source.fields)
        elif isinstance(source, PDict):
            for key, value in source.items():
                name = nfkc(_str("record", key, span))
                if name in fields:
                    raise core_error("P2325", span, name=name)
                fields[name] = value
        else:
            raise core_error("P2322", span, function="record", problem=f"expected a dict, not {type_name(source)}")
    fields.update(kwargs)
    return Record(fields)


def _type(interp: Any, args: list[Any], kwargs: dict[str, Any], span: Span) -> str:
    _arity("type", args, kwargs, span, 1, 1)
    return type_name(args[0])


def _getattr(interp: Any, args: list[Any], kwargs: dict[str, Any], span: Span) -> Any:
    _arity("getattr", args, kwargs, span, 2, 3)
    name = _str("getattr", args[1], span)
    try:
        return get_attribute(interp, args[0], name, span)
    except CoreError as exc:
        if len(args) == 3 and exc.diagnostic.code in ("P2313", "P2314"):
            return args[2]
        raise


def _hasattr(interp: Any, args: list[Any], kwargs: dict[str, Any], span: Span) -> bool:
    _arity("hasattr", args, kwargs, span, 2, 2)
    name = _str("hasattr", args[1], span)
    try:
        get_attribute(interp, args[0], name, span)
    except CoreError as exc:
        if exc.diagnostic.code in ("P2313", "P2314"):
            return False
        raise
    return True


def _fail(interp: Any, args: list[Any], kwargs: dict[str, Any], span: Span) -> None:
    _arity("fail", args, kwargs, span, 0, 64)
    raise core_error("P2340", span, message=" ".join(to_str(value) for value in args))


def _debug(interp: Any, args: list[Any], kwargs: dict[str, Any], span: Span) -> None:
    _arity("debug", args, kwargs, span, 0, 64)
    interp.ctx.debug.append((resolve(span), " ".join(to_repr(value) for value in args)))
    return None


def _build_date(interp: Any, args: list[Any], kwargs: dict[str, Any], span: Span) -> DateTime:
    """``build_date()``: the date of the build start, 00:00:00 (12.7)."""
    _arity("build_date", args, kwargs, span, 0, 0)
    return DateTime.from_python(interp.ctx.build_date)


def _length(interp: Any, args: list[Any], kwargs: dict[str, Any], span: Span) -> Length:
    _arity("length", args, kwargs, span, 1, 1)
    if isinstance(args[0], Length):
        return args[0]
    value = parse_length(_str("length", args[0], span))
    if value is None:
        raise core_error("P2307", span, value=args[0], type="length")
    return value


def _date(interp: Any, args: list[Any], kwargs: dict[str, Any], span: Span) -> DateTime:
    """``date(y, m, d)`` and ``date("YYYY-MM-DD")``: a ``datetime`` at 00:00:00 (12.3)."""
    _arity("date", args, kwargs, span, 1, 3)
    try:
        if len(args) == 1:
            return parse_iso_datetime(_str("date", args[0], span), time=False)
        if len(args) != 3:
            raise DateTimeError("date(year, month, day)")
        return DateTime.of(*(_int("date", value, span) for value in args))
    except DateTimeError as exc:
        raise _datetime_error(exc, args, span) from None


def _datetime(interp: Any, args: list[Any], kwargs: dict[str, Any], span: Span) -> DateTime:
    """``datetime(y, m, d, h, mi, s)``, ``datetime("…T…")``, ``datetime(serial)`` (12.3)."""
    _arity("datetime", args, kwargs, span, 1, 6)
    try:
        if len(args) == 1 and isinstance(args[0], str):
            return parse_iso_datetime(args[0])
        if len(args) == 1 and numbers.is_number(args[0]):
            serial = args[0]
            exact = Fraction(Decimal(repr(serial))) if isinstance(serial, float) else Fraction(serial)
            seconds = exact * 86400
            whole = int(seconds)
            if abs(seconds - whole) >= Fraction(1, 2):
                whole += 1 if seconds > 0 else -1
            return DateTime.from_seconds(whole)
        if len(args) < 3:
            raise DateTimeError("datetime(year, month, day, hour, minute, second)")
        return DateTime.of(*(_int("datetime", value, span) for value in args))
    except DateTimeError as exc:
        raise _datetime_error(exc, args, span) from None


def _datetime_error(exc: DateTimeError, args: list[Any], span: Span) -> CoreError:
    """P2307 for an invalid moment; P2310 for a value with a time zone."""
    text = ", ".join(to_str(value) for value in args)
    if str(exc) == "time zone":
        return core_error("P2310", span, value=text)
    return core_error("P2307", span, value=text, type="datetime")


def _float(interp: Any, args: list[Any], kwargs: dict[str, Any], span: Span) -> float:
    """``float(x)``: numbers and strings; ``float(dt)`` is the serial number (12.3)."""
    _arity("float", args, kwargs, span, 1, 1)
    if isinstance(args[0], DateTime):
        return float(args[0].serial())
    return _number_call(numbers.to_float, span, args[0])


def make_builtins() -> dict[str, Any]:
    """The built-in names of the core (functions and constants)."""
    functions: dict[str, Callable[..., Any]] = {
        "len": _len, "range": _range, "enumerate": _enumerate, "zip": _zip, "sorted": _sorted,
        "reversed": _reversed, "min": _min_max("min", True), "max": _min_max("max", False),
        "sum": _sum, "any": _any_all("any", True), "all": _any_all("all", False), "abs": _abs,
        "round": _round, "int": _conversion("int", numbers.to_int),
        "float": _float, "dec": _conversion("dec", numbers.to_decimal), "datetime": _datetime,
        "str": _str_builtin, "bool": _bool, "list": _list, "tuple": _tuple, "dict": _dict,
        "record": _record, "type": _type, "getattr": _getattr, "hasattr": _hasattr, "repr": _repr,
        "fail": _fail, "debug": _debug, "build_date": _build_date, "length": _length, "date": _date,
    }
    names: dict[str, Any] = {name: Builtin(name, impl) for name, impl in functions.items()}
    for unit in UNIT_INCHES:
        names[unit] = Length(Decimal(1), unit)
    return names


# ----------------------------------------------------------------------
# Attributes and methods
# ----------------------------------------------------------------------


def get_attribute(interp: Any, value: Any, name: str, span: Span) -> Any:
    """``value.name``: record fields, date/length attributes, methods."""
    if name.startswith("_"):
        raise core_error("P2313", span, type=type_name(value), name=name)
    if isinstance(value, Record):
        name = nfkc(name)
        if name == "replace" and "replace" not in value.fields:
            return BoundMethod("replace", value, _record_replace)
        if name in value.fields:
            return value.fields[name]
        raise core_error("P2314", span, name=name)
    if isinstance(value, ModuleValue):
        try:
            return value.lookup(name, span)
        except CoreError as exc:
            if exc.diagnostic.code == "P2201" and exc.diagnostic.args.get("name") == name:
                raise core_error("P2624", span, name=name, module=value.name) from None
            raise
    if isinstance(value, DateTime) and name in DATETIME_ATTRIBUTES:
        return datetime_attribute(value, name)
    if isinstance(value, Length) and name in UNIT_INCHES:
        return convert_length(value, name)
    table = None
    if isinstance(value, str):
        table = _STR_METHODS
    elif isinstance(value, PList):
        table = _LIST_METHODS
    elif isinstance(value, PDict):
        table = _DICT_METHODS
    if table is not None and name in table:
        return BoundMethod(name, value, table[name])
    raise core_error("P2313", span, type=type_name(value), name=name)


def _record_replace(interp: Any, record: Record, args: list[Any], kwargs: dict[str, Any], span: Span) -> Record:
    _arity("replace", args, {}, span, 0, 0)
    kwargs = {nfkc(key): value for key, value in kwargs.items()}
    for key in kwargs:
        if key not in record.fields:
            raise core_error("P2314", span, name=key)
    return Record({**record.fields, **kwargs})


# --- strings ----------------------------------------------------------


def _str_method(name: str, *, result_list: bool = False, size: Callable[..., int] | None = None,
                arg_kinds: tuple[tuple[type, ...], ...] = (), low: int = 0) -> Callable[..., Any]:
    """Wrap a Python ``str`` method with argument checks."""
    def impl(interp: Any, receiver: str, args: list[Any], kwargs: dict[str, Any], span: Span) -> Any:
        _arity(name, args, kwargs, span, low, len(arg_kinds))
        for value, kinds in zip(args, arg_kinds):
            _expect(name, value, kinds, " or ".join(k.__name__ if k is not type(None) else "None" for k in kinds), span)
        if size is not None:
            interp.meter.check_string(size(receiver, *args), span)
        interp.meter.step(span, len(receiver) // 16)
        result = getattr(receiver, name)(*args)
        return PList(result) if result_list else result
    return impl


def _replace_size(receiver: str, old: str, new: str, count: int = -1) -> int:
    occurrences = receiver.count(old) if old else len(receiver) + 1
    if count >= 0:
        occurrences = min(occurrences, count)
    return len(receiver) + occurrences * max(0, len(new) - len(old))


def _join(interp: Any, receiver: str, args: list[Any], kwargs: dict[str, Any], span: Span) -> str:
    _arity("join", args, kwargs, span, 1, 1)
    items = interp.materialize(args[0], span)
    for item in items:
        _str("join", item, span)
    interp.meter.check_string(sum(len(item) for item in items) + len(receiver) * max(0, len(items) - 1), span)
    return receiver.join(items)


def _str_format(interp: Any, receiver: str, args: list[Any], kwargs: dict[str, Any], span: Span) -> str:
    return format_string(interp, receiver, (args, kwargs), span, percent=False)


_OPT_STR = (str, type(None))
_STR_METHODS: dict[str, Callable[..., Any]] = {
    "split": _str_method("split", result_list=True, arg_kinds=(_OPT_STR, (int,))),
    "rsplit": _str_method("rsplit", result_list=True, arg_kinds=(_OPT_STR, (int,))),
    "splitlines": _str_method("splitlines", result_list=True, arg_kinds=((bool,),)),
    "join": _join,
    "strip": _str_method("strip", arg_kinds=(_OPT_STR,)),
    "lstrip": _str_method("lstrip", arg_kinds=(_OPT_STR,)),
    "rstrip": _str_method("rstrip", arg_kinds=(_OPT_STR,)),
    "replace": _str_method("replace", arg_kinds=((str,), (str,), (int,)), low=2, size=_replace_size),
    "startswith": _str_method("startswith", arg_kinds=((str, tuple),), low=1),
    "endswith": _str_method("endswith", arg_kinds=((str, tuple),), low=1),
    "find": _str_method("find", arg_kinds=((str,), (int,), (int,)), low=1),
    "rfind": _str_method("rfind", arg_kinds=((str,), (int,), (int,)), low=1),
    "count": _str_method("count", arg_kinds=((str,), (int,), (int,)), low=1),
    "upper": _str_method("upper"), "lower": _str_method("lower"),
    "capitalize": _str_method("capitalize"), "title": _str_method("title"),
    "isdigit": _str_method("isdigit"), "isalpha": _str_method("isalpha"),
    "isspace": _str_method("isspace"),
    "zfill": _str_method("zfill", arg_kinds=((int,),), low=1, size=lambda s, w: max(len(s), w)),
    "format": _str_format,
}


# --- lists ------------------------------------------------------------


def _mutating(function: Callable[..., Any]) -> Callable[..., Any]:
    @functools.wraps(function)
    def impl(interp: Any, receiver: Any, args: list[Any], kwargs: dict[str, Any], span: Span) -> Any:
        interp.check_mutable(receiver, span)
        return function(interp, receiver, args, kwargs, span)
    return impl


@_mutating
def _append(interp: Any, xs: PList, args: list[Any], kwargs: dict[str, Any], span: Span) -> None:
    _arity("append", args, kwargs, span, 1, 1)
    interp.meter.check_collection(len(xs) + 1, span)
    xs.append(args[0])


@_mutating
def _extend(interp: Any, xs: PList, args: list[Any], kwargs: dict[str, Any], span: Span) -> None:
    _arity("extend", args, kwargs, span, 1, 1)
    items = interp.materialize(args[0], span)
    interp.meter.check_collection(len(xs) + len(items), span)
    xs.extend(items)


@_mutating
def _insert(interp: Any, xs: PList, args: list[Any], kwargs: dict[str, Any], span: Span) -> None:
    _arity("insert", args, kwargs, span, 2, 2)
    interp.meter.check_collection(len(xs) + 1, span)
    xs.insert(_int("insert", args[0], span), args[1])


@_mutating
def _list_pop(interp: Any, xs: PList, args: list[Any], kwargs: dict[str, Any], span: Span) -> Any:
    _arity("pop", args, kwargs, span, 0, 1)
    index = _int("pop", args[0], span) if args else -1
    try:
        return xs.pop(index)
    except IndexError:
        raise core_error("P2311", span, index=index, size=len(xs)) from None


def _position(interp: Any, xs: PList, value: Any, span: Span) -> int:
    for index, item in enumerate(xs):
        if interp.equals(item, value, span):
            return index
    return -1


@_mutating
def _remove(interp: Any, xs: PList, args: list[Any], kwargs: dict[str, Any], span: Span) -> None:
    _arity("remove", args, kwargs, span, 1, 1)
    index = _position(interp, xs, args[0], span)
    if index < 0:
        raise core_error("P2312", span, key=to_repr(args[0]))
    del xs[index]


def _index(interp: Any, xs: PList, args: list[Any], kwargs: dict[str, Any], span: Span) -> int:
    _arity("index", args, kwargs, span, 1, 1)
    index = _position(interp, xs, args[0], span)
    if index < 0:
        raise core_error("P2312", span, key=to_repr(args[0]))
    return index


def _list_count(interp: Any, xs: PList, args: list[Any], kwargs: dict[str, Any], span: Span) -> int:
    _arity("count", args, kwargs, span, 1, 1)
    return sum(1 for item in xs if interp.equals(item, args[0], span))


@_mutating
def _sort(interp: Any, xs: PList, args: list[Any], kwargs: dict[str, Any], span: Span) -> None:
    _arity("sort", args, kwargs, span, 0, 0, ("key", "reverse"))
    result = _sorted(interp, [xs], kwargs, span)
    xs[:] = result


@_mutating
def _reverse(interp: Any, xs: PList, args: list[Any], kwargs: dict[str, Any], span: Span) -> None:
    _arity("reverse", args, kwargs, span, 0, 0)
    xs.reverse()


_LIST_METHODS: dict[str, Callable[..., Any]] = {
    "append": _append, "extend": _extend, "insert": _insert, "pop": _list_pop, "remove": _remove,
    "index": _index, "count": _list_count, "sort": _sort, "reverse": _reverse,
}


# --- dictionaries -----------------------------------------------------


def _key(value: Any, span: Span) -> Any:
    if not is_valid_key(value):
        raise core_error("P2317", span, type=type_name(value))
    return value


def _get(interp: Any, d: PDict, args: list[Any], kwargs: dict[str, Any], span: Span) -> Any:
    _arity("get", args, kwargs, span, 1, 2)
    return d.get(_key(args[0], span), args[1] if len(args) > 1 else None)


def _keys(interp: Any, d: PDict, args: list[Any], kwargs: dict[str, Any], span: Span) -> PList:
    _arity("keys", args, kwargs, span, 0, 0)
    return PList(d.keys())


def _values(interp: Any, d: PDict, args: list[Any], kwargs: dict[str, Any], span: Span) -> PList:
    _arity("values", args, kwargs, span, 0, 0)
    return PList(d.values())


def _items(interp: Any, d: PDict, args: list[Any], kwargs: dict[str, Any], span: Span) -> PList:
    _arity("items", args, kwargs, span, 0, 0)
    return PList(d.items())


@_mutating
def _update(interp: Any, d: PDict, args: list[Any], kwargs: dict[str, Any], span: Span) -> None:
    update = _dict(interp, args, kwargs, span)
    interp.meter.check_collection(len(d) + len(update), span)
    d.update(update)


@_mutating
def _dict_pop(interp: Any, d: PDict, args: list[Any], kwargs: dict[str, Any], span: Span) -> Any:
    _arity("pop", args, kwargs, span, 1, 2)
    key = _key(args[0], span)
    if key in d:
        return d.pop(key)
    if len(args) > 1:
        return args[1]
    raise core_error("P2312", span, key=to_repr(key))


def _setdefault(interp: Any, d: PDict, args: list[Any], kwargs: dict[str, Any], span: Span) -> Any:
    _arity("setdefault", args, kwargs, span, 1, 2)
    key = _key(args[0], span)
    if key not in d:
        interp.check_mutable(d, span)
        d[key] = args[1] if len(args) > 1 else None
    return d[key]


_DICT_METHODS: dict[str, Callable[..., Any]] = {
    "get": _get, "keys": _keys, "values": _values, "items": _items, "update": _update,
    "pop": _dict_pop, "setdefault": _setdefault,
}


# ----------------------------------------------------------------------
# Formatting
# ----------------------------------------------------------------------

_SPEC_WIDTH = re.compile(r"(\d+)")
_PERCENT_FIELD = re.compile(r"%(?:\([^)]*\))?[-#0 +]*(\*|\d+)?(?:\.(\*|\d+))?[a-zA-Z%]")


def _check_widths(interp: Any, numbers_in_spec: list[str], span: Span) -> None:
    for text in numbers_in_spec:
        if text and text.isdigit() and int(text) > interp.meter.limits.size:
            interp.meter.check_string(int(text), span)


class _Shown:
    """A non-primitive value shown by ``%`` formatting through str/repr."""

    __slots__ = ("value",)

    def __init__(self, value: Any) -> None:
        self.value = value

    def __str__(self) -> str:
        return to_str(self.value)

    def __repr__(self) -> str:
        return to_repr(self.value)


def _plain(value: Any) -> Any:
    """Value passed to Python formatting: primitives as is, others wrapped."""
    if value is None or isinstance(value, (bool, int, float, Decimal, str)):
        return value
    return _Shown(value)


def format_value(interp: Any, value: Any, spec: str, span: Span) -> str:
    """Format one value by a format specification (f-strings, ``format``)."""
    _check_widths(interp, _SPEC_WIDTH.findall(spec), span)
    if not (value is None or isinstance(value, (bool, int, float, Decimal, str))):
        value = to_str(value)
    elif isinstance(value, Decimal) and not spec:
        value = to_str(value)
    try:
        text = format(value, spec)
    except (ValueError, TypeError) as exc:
        raise core_error("P2331", span, problem=str(exc)) from None
    interp.meter.check_string(len(text), span)
    return text


class _SafeFormatter(string.Formatter):
    """``str.format`` without attribute access in fields (decision 45)."""

    def __init__(self, interp: Any, span: Span) -> None:
        self.interp = interp
        self.span = span

    def get_field(self, field_name: str, args: Any, kwargs: Any) -> Any:
        first, rest = _string.formatter_field_name_split(field_name)
        obj = self.get_value(first, args, kwargs)
        for is_attribute, key in rest:
            if is_attribute:
                raise CoreError(error("P2330", resolve(self.span), field=field_name))
            obj = self.interp.index(obj, key, self.span)
        return obj, first

    def format_field(self, value: Any, format_spec: str) -> str:
        return format_value(self.interp, value, format_spec, self.span)

    def convert_field(self, value: Any, conversion: str | None) -> Any:
        if conversion == "r":
            return to_repr(value)
        if conversion in ("s", "a"):
            return to_str(value)
        return value


def format_string(interp: Any, template: str, values: Any, span: Span, *, percent: bool) -> str:
    """``%`` formatting (``percent=True``) or ``str.format`` (``values=(args, kwargs)``)."""
    if percent:
        _check_widths(interp, [w for match in _PERCENT_FIELD.finditer(template)
                               for w in match.groups() if w], span)
        if isinstance(values, tuple):
            operand: Any = tuple(_plain(value) for value in values)
        elif isinstance(values, PDict):
            operand = {key: _plain(value) for key, value in values.items()}
        else:
            operand = _plain(values)
        try:
            text = template % operand
        except (TypeError, ValueError, KeyError) as exc:
            raise core_error("P2331", span, problem=str(exc)) from None
    else:
        args, kwargs = values
        try:
            text = _SafeFormatter(interp, span).vformat(template, list(args), dict(kwargs))
        except CoreError:
            raise
        except (ValueError, TypeError, KeyError, IndexError) as exc:
            raise core_error("P2331", span, problem=str(exc) or type(exc).__name__) from None
    interp.meter.check_string(len(text), span)
    return text

