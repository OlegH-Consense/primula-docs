"""Module ``std/math`` of the standard library (library 9).

``|import("std/math")`` gives the namespace ``math`` (or ``alias=``):

* ``sqrt``, ``exp``, ``log``, ``log10``, ``sin``, ``cos``, ``tan``,
  ``atan2`` — the result is ``float``; a ``decimal`` argument is converted
  to ``float`` (12.4);
* ``floor``, ``ceil`` — a ``decimal`` with scale 0, exact for ``decimal``;
* ``pi``, ``e`` — ``float`` constants.

A value outside the domain (``sqrt(-1)``, ``log(0)``) is error P2727.  The
set of functions (trigonometry in particular) is an open question of the
specification (appendix 4.3).
"""

from __future__ import annotations

import decimal
import math
from typing import Any, Callable

from primula.core.values import Builtin
from primula.library.context import Library, keywords, lib_error, number, positional, to_decimal


def _float_function(name: str, function: Callable[..., float], arity: int = 1):
    def impl(lib: Library, args: list[Any], kwargs: dict[str, Any], span: Any) -> float:
        positional(name, args, arity, arity, span)
        keywords(name, kwargs, (), span)
        values = [float(number(name, "x", value, span)) for value in args]
        try:
            result = function(*values)
        except (ValueError, OverflowError):
            raise lib_error("P2727", span, None, function=name,
                            value=", ".join(repr(v) for v in values)) from None
        return result
    return impl


def _rounding(name: str, rounding: str):
    def impl(lib: Library, args: list[Any], kwargs: dict[str, Any], span: Any) -> int:
        positional(name, args, 1, 1, span)
        keywords(name, kwargs, (), span)
        value = number(name, "x", args[0], span)
        return int(to_decimal(value).to_integral_value(rounding=rounding))
    return impl


FUNCTIONS: dict[str, Callable[..., Any]] = {
    "sqrt": _float_function("sqrt", math.sqrt), "exp": _float_function("exp", math.exp),
    "log": _float_function("log", math.log), "log10": _float_function("log10", math.log10),
    "sin": _float_function("sin", math.sin), "cos": _float_function("cos", math.cos),
    "tan": _float_function("tan", math.tan), "atan2": _float_function("atan2", math.atan2, 2),
    "floor": _rounding("floor", decimal.ROUND_FLOOR), "ceil": _rounding("ceil", decimal.ROUND_CEILING),
}
CONSTANTS = {"pi": math.pi, "e": math.e}


def module_values(bind: Callable[[str, Callable[..., Any]], Builtin]) -> dict[str, Any]:
    """Names of ``std/math``: functions bound by the prelude, constants."""
    return {**{name: bind(name, function) for name, function in FUNCTIONS.items()}, **CONSTANTS}
