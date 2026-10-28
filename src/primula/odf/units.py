"""Values of ODF attributes: lengths, sizes, colours, borders, languages.

Lengths are written in millimetres with at most three decimal digits
(trailing zeros removed); font sizes and border widths in points, the
units Writer uses in its own dialogs.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from fractions import Fraction
from typing import Any

from primula.core.values import UNIT_INCHES, Length
from primula.styles.schema import Border, LineHeight


def _number(value: Fraction, digits: int = 3) -> str:
    """A fraction as a decimal string with at most ``digits`` decimals."""
    quantum = Decimal(1).scaleb(-digits)
    text = format((Decimal(value.numerator) / Decimal(value.denominator)).quantize(quantum, ROUND_HALF_UP), "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return "0" if text in ("-0", "") else text


def mm(length: Length) -> str:
    """``12.345mm``."""
    return _number(length.inches / UNIT_INCHES["mm"]) + "mm"


def pt(length: Length) -> str:
    """``10.5pt``."""
    return _number(length.inches / UNIT_INCHES["pt"]) + "pt"


def to_mm(length: Length) -> Fraction:
    """Length in millimetres as an exact fraction."""
    return length.inches / UNIT_INCHES["mm"]


def from_mm(value: Fraction) -> Length:
    """A length from millimetres."""
    return Length.from_inches(value * UNIT_INCHES["mm"], "mm")


def border(value: Border) -> str:
    """``fo:border`` value: ``0.5pt solid #000000`` or ``none``."""
    if value.width is None:
        return "none"
    return f"{pt(value.width)} {value.type} {value.color}"


def line_height(value: LineHeight) -> tuple[str, str]:
    """Attribute name and value for ``line_height``."""
    if value.mode == "percent":
        return "fo:line-height", f"{value.value}%"
    if value.mode == "exact":
        return "fo:line-height", mm(value.value)
    return "style:line-height-at-least", mm(value.value)


def language(tag: str | None) -> tuple[str | None, str | None]:
    """``uk-UA`` -> (``uk``, ``UA``)."""
    if not tag:
        return None, None
    parts = tag.split("-")
    country = next((p for p in parts[1:] if len(p) == 2 and p.isalpha()), None)
    return parts[0].lower(), country.upper() if country else None


def font_family(name: str) -> str:
    """``svg:font-family`` value: names with spaces are quoted."""
    return f"'{name}'" if " " in name else name


def color(value: Any) -> str:
    """Colour value (``none`` becomes ``transparent`` for backgrounds)."""
    return "transparent" if value == "none" else str(value)
