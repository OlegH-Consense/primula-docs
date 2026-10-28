"""Data functions (library 8): ``group_by``, ``sum_by``, ``distinct``.

``key`` and ``value`` are a field name or a function (``def`` of the
document or module; the core has no ``lambda``).  Items are records (from
``load_csv``/``load_yaml``) or dictionaries.

* ``group_by(items, key)`` — a dictionary «key value → list of items» in
  the order of first appearance;
* ``sum_by(items, key, value)`` — sums of ``value`` by groups (exact for
  ``decimal``; mixing with ``float`` gives ``float``, 12.4);
* ``distinct(items, key)`` — unique values in the order of first
  appearance.
"""

from __future__ import annotations

from typing import Any

from primula.core import numbers as core_numbers
from primula.core.values import PDict, PList, Record, is_valid_key, type_name
from primula.library.context import Library, expect, is_number, keywords, lib_error, positional
from primula.unicode import nfkc


def _items(function: str, value: Any, span: Any) -> list[Any]:
    expect(function, "items", value, isinstance(value, (list, tuple)), "sequence", span)
    return list(value)


def _getter(lib: Library, function: str, arg: str, selector: Any, span: Any):
    """A function ``item -> value`` from a field name or a Primula function."""
    if isinstance(selector, str):
        name = nfkc(selector)

        def field(item: Any) -> Any:
            if isinstance(item, Record) and name in item.fields:
                return item.fields[name]
            if isinstance(item, (dict, PDict)) and selector in item:
                return item[selector]
            raise lib_error("P2724", span, None, function=function, key=selector)
        return field
    # A function value: the interpreter reports a value that cannot be called.
    return lambda item: lib.interp.call(selector, [item], {}, span)


def _key(function: str, value: Any, span: Any) -> Any:
    if not is_valid_key(value):
        raise lib_error("P2725", span, None, function=function, type=type_name(value))
    return value


def group_by(lib: Library, args: list[Any], kwargs: dict[str, Any], span: Any) -> PDict:
    """``group_by(items, key)``."""
    positional("group_by", args, 2, 2, span)
    keywords("group_by", kwargs, (), span)
    get = _getter(lib, "group_by", "key", args[1], span)
    groups = PDict()
    for item in _items("group_by", args[0], span):
        groups.setdefault(_key("group_by", get(item), span), PList()).append(item)
    return groups


def sum_by(lib: Library, args: list[Any], kwargs: dict[str, Any], span: Any) -> PDict:
    """``sum_by(items, key, value)``."""
    positional("sum_by", args, 3, 3, span)
    keywords("sum_by", kwargs, (), span)
    get_key = _getter(lib, "sum_by", "key", args[1], span)
    get_value = _getter(lib, "sum_by", "value", args[2], span)
    sums = PDict()
    for item in _items("sum_by", args[0], span):
        key = _key("sum_by", get_key(item), span)
        value = get_value(item)
        if value is None:
            value = 0
        expect("sum_by", "value", value, is_number(value), "number", span)
        sums[key] = core_numbers.arith("+", sums[key], value) if key in sums else value
    return sums


def distinct(lib: Library, args: list[Any], kwargs: dict[str, Any], span: Any) -> PList:
    """``distinct(items, key)``."""
    positional("distinct", args, 2, 2, span)
    keywords("distinct", kwargs, (), span)
    get = _getter(lib, "distinct", "key", args[1], span)
    seen: dict[Any, None] = {}
    for item in _items("distinct", args[0], span):
        seen.setdefault(_key("distinct", get(item), span), None)
    return PList(seen)


FUNCTIONS = {"group_by": group_by, "sum_by": sum_by, "distinct": distinct}
