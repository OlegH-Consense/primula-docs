"""Columns of a table: ``col(…)`` and width forms (specification 6.3, decision 78).

Width forms:

==================  ==========================================================
``"40mm"``          fixed (also a length value ``40*mm``)
``"30%"``           share of the table width
``"*"``, ``"2*"``   remainder by weight
``"auto"``          by content, unbounded
``"20mm..60mm"``    by content within bounds; ``"20mm.."``, ``"..60mm"``;
                    bounds may be shares: ``"10%..25%"``, ``"15mm..30%"``
==================  ==========================================================

``col(width, id=…, align=…, valign=…, type=…, currency=…, digits=…,
paragraph=…, min=…, max=…, padding=…, background=…, border…=…)`` returns a
:class:`Column` record; ``col("auto", min="20mm", max="60mm")`` equals
``col("20mm..60mm")``.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
from decimal import Decimal
from typing import Any

from primula.core.errors import core_error
from primula.core.values import Builtin, Length, Record, parse_length
from primula.styles.schema import PropertyError, check_property

#: Value types of columns (6.8; ``int`` and ``date`` of v1.0 are gone).
TYPES = ("decimal", "money", "datetime")
#: Cell properties a column may set (cascade 6.6).
CELL_PROPS = ("align", "valign", "padding", "background", "paragraph", "border", "border_top", "border_bottom",
              "border_left", "border_right")
_OWN = ("id", "type", "currency", "digits", "min", "max")


class Column(Record):
    """A column object made by ``col(…)`` (a record with dot access)."""


@dataclass(frozen=True)
class Bound:
    """A width bound: a length or a share of the table width."""

    length: Length | None = None
    percent: Fraction | None = None

    def mm(self, table_mm: Fraction) -> Fraction:
        """The bound in millimetres for a table width."""
        from primula.odf import units

        if self.length is not None:
            return units.to_mm(self.length)
        return table_mm * (self.percent or Fraction(0)) / 100


@dataclass(frozen=True)
class Width:
    """A parsed column width.

    Attributes:
        kind: ``fixed``, ``percent``, ``star`` or ``auto``.
        length: fixed length.
        share: percentage (``percent``) or weight (``star``).
        low, high: bounds of an ``auto`` column.
    """

    kind: str
    length: Length | None = None
    share: Fraction | None = None
    low: Bound | None = None
    high: Bound | None = None


def _bound(text: str) -> Bound:
    text = text.strip()
    if text.endswith("%"):
        try:
            return Bound(percent=Fraction(Decimal(text[:-1])))
        except ArithmeticError:
            raise ValueError(text) from None
    length = parse_length(text)
    if length is None:
        raise ValueError(text)
    return Bound(length=length)


def parse_width(value: Any, low: Any = None, high: Any = None) -> Width:
    """Parse a width form (6.3).

    Args:
        value: a width string, a length, or ``None`` (``*``).
        low, high: ``min=``/``max=`` of ``col()`` (strings or lengths).

    Raises:
        ValueError: an invalid form.
    """
    def as_bound(item: Any) -> Bound | None:
        if item is None:
            return None
        if isinstance(item, Length):
            return Bound(length=item)
        if isinstance(item, str):
            return _bound(item)
        raise ValueError(str(item))

    if value is None:
        value = "*"
    if isinstance(value, Length):
        width = Width("fixed", length=value)
    elif not isinstance(value, str):
        raise ValueError(str(value))
    elif value == "auto":
        width = Width("auto")
    elif ".." in value:
        left, right = value.split("..", 1)
        width = Width("auto", low=_bound(left) if left.strip() else None,
                      high=_bound(right) if right.strip() else None)
    elif value.endswith("*"):
        weight = value[:-1].strip()
        try:
            width = Width("star", share=Fraction(Decimal(weight)) if weight else Fraction(1))
        except ArithmeticError:
            raise ValueError(value) from None
    elif value.endswith("%"):
        try:
            width = Width("percent", share=Fraction(Decimal(value[:-1])))
        except ArithmeticError:
            raise ValueError(value) from None
    else:
        length = parse_length(value)
        if length is None:
            raise ValueError(value)
        width = Width("fixed", length=length)
    if low is not None or high is not None:
        if width.kind != "auto":
            raise ValueError("min=/max= need an auto width")
        width = Width("auto", low=as_bound(low) or width.low, high=as_bound(high) or width.high)
    return width


def _col(interp: Any, args: list[Any], kwargs: dict[str, Any], span: Any) -> Column:
    """``col(width, …)`` (6.3): check the arguments and return a :class:`Column`."""
    if len(args) > 1:
        raise core_error("P2321", span, function="col", problem="takes one positional argument (the width)")
    width = args[0] if args else kwargs.pop("width", "*")
    fields: dict[str, Any] = {"width": width}
    for name, value in kwargs.items():
        if name in CELL_PROPS:
            try:
                fields[name] = check_property("table", "header_" + name, value)
            except PropertyError:
                raise core_error("P5101", span, name=name, value=str(value)) from None
        elif name in _OWN:
            if name == "type" and value not in TYPES:
                raise core_error("P5101", span, name=name, value=str(value))
            if name == "digits" and isinstance(value, Decimal) and value == value.to_integral_value():
                value = int(value)
            if name == "digits" and (not isinstance(value, int) or isinstance(value, bool) or value < 0):
                raise core_error("P5101", span, name=name, value=str(value))
            if name in ("id", "currency") and not isinstance(value, str):
                raise core_error("P5101", span, name=name, value=str(value))
            fields[name] = value
        else:
            raise core_error("P2321", span, function="col", problem=f"got an unexpected keyword argument '{name}'")
    try:
        parse_width(width, fields.get("min"), fields.get("max"))
    except ValueError:
        raise core_error("P5102", span, value=str(width)) from None
    return Column(fields)


def column_of(value: Any) -> Column:
    """A ``cols`` element as a :class:`Column` (a width string is ``col(width)``)."""
    if isinstance(value, Column):
        return value
    return Column({"width": value})


def make_column_builtins() -> dict[str, Builtin]:
    """The built-in ``col``."""
    return {"col": Builtin("col", _col)}
