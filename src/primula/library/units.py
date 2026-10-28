"""Values with units (library 6; decisions 93, 96, 115).

``qty(230, "V")`` — «230 В»; ``qty_range(100, 240, "V")`` — «100–240 В»
(both bounds non-negative: an en dash without spaces), otherwise
«−20…+55 °C» (an ellipsis, the sign at the positive bound, zero without a
sign); ``qty(50, "Hz", tol=1)`` — «(50 ± 1) Гц», only a symmetric
tolerance.  The number and the symbol are joined by a no-break space; so
are the parts of a tolerance.

``convert(x, from, to)`` multiplies by the ratio of the factors within one
quantity (``degC`` ↔ ``K`` with the offset 273.15); the result keeps the
type: ``decimal`` (division with 28 significant digits) or ``float``.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from primula.library.context import lib_error, NBSP, Library, keywords, number, positional, to_decimal
from primula.library.numbers import format_number, same_type

EN_DASH = "–"
ELLIPSIS = "…"


def _symbol(lib: Library, code: Any, lang: str, span: Any) -> str:
    unit = lib.unit(code, span)
    symbols = unit["symbol"]
    return str(symbols.get(lang) or symbols.get("en") or code)


def _digits(kwargs: dict[str, Any], span: Any) -> int | None:
    from primula.library.context import integer

    digits = kwargs.get("digits")
    return None if digits is None else integer("qty", "digits", digits, span)


def qty(lib: Library, args: list[Any], kwargs: dict[str, Any], span: Any) -> str:
    """``qty(x, unit, tol=None, digits=None)``."""
    positional("qty", args, 2, 2, span)
    keywords("qty", kwargs, ("tol", "digits", "lang"), span)
    value = number("qty", "x", args[0], span)
    lang = lib.lang(kwargs.get("lang"), span)
    digits = _digits(kwargs, span)
    symbol = _symbol(lib, args[1], lang, span)
    text = format_number(value, digits, lang)
    tol = kwargs.get("tol")
    if tol is not None:
        if isinstance(tol, (list, tuple)):
            raise lib_error("P2720", span, None)
        tolerance = format_number(number("qty", "tol", tol, span), digits, lang)
        return f"({text}{NBSP}±{NBSP}{tolerance}){NBSP}{symbol}"
    return f"{text}{NBSP}{symbol}"


def qty_range(lib: Library, args: list[Any], kwargs: dict[str, Any], span: Any) -> str:
    """``qty_range(a, b, unit)``: «100–240 В», «−20…+55 °C»."""
    positional("qty_range", args, 3, 3, span)
    keywords("qty_range", kwargs, ("digits", "lang"), span)
    low = number("qty_range", "a", args[0], span)
    high = number("qty_range", "b", args[1], span)
    lang = lib.lang(kwargs.get("lang"), span)
    digits = _digits(kwargs, span)
    symbol = _symbol(lib, args[2], lang, span)
    if low >= 0 and high >= 0:
        return f"{format_number(low, digits, lang)}{EN_DASH}{format_number(high, digits, lang)}{NBSP}{symbol}"

    def signed(value: Any) -> str:
        text = format_number(value, digits, lang)
        return "+" + text if value > 0 else text

    return f"{signed(low)}{ELLIPSIS}{signed(high)}{NBSP}{symbol}"


def convert(lib: Library, args: list[Any], kwargs: dict[str, Any], span: Any) -> Any:
    """``convert(x, "kW", "W")``."""
    positional("convert", args, 3, 3, span)
    keywords("convert", kwargs, (), span)
    value = number("convert", "x", args[0], span)
    source, target = lib.unit(args[1], span), lib.unit(args[2], span)
    if source["quantity"] is None or source["quantity"] != target["quantity"]:
        raise lib_error("P2707", span, None, a=str(args[1]), b=str(args[2]))
    factor_from, factor_to = to_decimal(source["factor"]), to_decimal(target["factor"])
    offset_from, offset_to = to_decimal(source["offset"]), to_decimal(target["offset"])
    if isinstance(value, float):
        base = value * float(factor_from) + float(offset_from)
        return (base - float(offset_to)) / float(factor_to)
    base = Decimal(value) * factor_from + offset_from
    return same_type(value, _trim((base - offset_to) / factor_to))


def _trim(value: Decimal) -> Decimal:
    """Drop trailing zeros of a fraction without the exponent form (1500.0 → 1500)."""
    if value == value.to_integral_value():
        return value.quantize(Decimal(1))
    text = format(value, "f").rstrip("0")
    return Decimal(text)


FUNCTIONS = {"qty": qty, "qty_range": qty_range, "convert": convert}
