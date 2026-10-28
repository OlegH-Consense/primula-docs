"""Typed values of table cells and their text (specification 6.8; decisions 77-80).

* A cell has a value if its content is exactly one expression ``|(…)``
  (computed by the evaluator), one formula ``|=(…)``, or a literal in a
  typed column (parsed by the document language, decision 77).
* In a typed column every value is output by the column type (decision
  78, v1.1): ``decimal`` — the number by the language with its own digits
  or ``digits=`` (an integer value without a fraction), ``money`` — two
  digits and the currency (decision 79), ``datetime`` — the short date,
  with the time when it is not 00:00:00.
* Outside typed columns a value is output by its own type (decision 80);
  a mixed cell is a string, a formula in it is formatted by its type.
* ODT value types: ``float``, ``currency`` (with a known currency code),
  ``date``; otherwise ``string``.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from primula.core.values import DateTime
from primula.library import localefmt
from primula.library.localefmt import ParseError
from primula.structure.tree import plain_text
from primula.syntax import nodes as N
from primula.tables.columns import Column
from primula.tables.grid import MISSING, CellModel


def column_type(column: Column | None) -> str | None:
    return column.fields.get("type") if column is not None else None


def parse_literal(text: str, kind: str, lang: str) -> Any:
    """A literal of a typed column; empty text is ``None`` (decision 77).

    Raises:
        ParseError: the text is not of the column type.
    """
    if not text.strip():
        return None
    if kind in ("decimal", "money"):
        return localefmt.parse_decimal(text, lang)
    return localefmt.parse_datetime(text, lang)


def is_number(value: Any) -> bool:
    return isinstance(value, (int, Decimal, float)) and not isinstance(value, bool)


def format_value(value: Any, column: Column | None, lang: str, symbols: Any = None) -> str:
    """Text of a value by the column type or by its own type (decisions 78, 80).

    ``symbols(code, lang)`` gives the currency symbol of a ``money`` column:
    the dictionary of the standard library with ``currency(…)`` of the styles
    modules (library 3); without it — the built-in table of ``localefmt``.
    """
    if value is None:
        return ""
    kind = column_type(column)
    fields = column.fields if column is not None else {}
    if kind == "money" and is_number(value):
        text = localefmt.format_number(value, 2, lang)
        symbol = (symbols or localefmt.currency_symbol)(fields.get("currency"), lang)
        return f"{text}{localefmt.NBSP}{symbol}" if symbol else text
    if kind == "decimal" and is_number(value):
        return localefmt.format_number(value, fields.get("digits"), lang)
    if isinstance(value, DateTime):
        return localefmt.format_moment(value, lang)
    if is_number(value):
        return localefmt.format_number(value, None, lang)
    if isinstance(value, str):
        return value
    from primula.core.values import to_str

    return to_str(value)


def number_format(value: Any, column: Column | None, lang: str, symbols: Any = None) -> tuple[int, str | None]:
    """ODF number format of a numeric cell of a ``live=True`` table.

    Writer recomputes formula cells when the document is loaded and shows
    the result by the cell's data style; without one it prints a bare
    number («4000.5»).  The format repeats :func:`format_value`: the decimal
    places of the displayed text and, in a ``money`` column, the currency
    symbol after a no-break space.

    Returns:
        ``(decimal places, currency symbol or None)``.
    """
    kind = column_type(column)
    fields = column.fields if column is not None else {}
    if kind == "money":
        return 2, (symbols or localefmt.currency_symbol)(fields.get("currency"), lang)
    digits = fields.get("digits") if kind == "decimal" else None
    if digits is None:
        # As many places as the value has (the canonical text of the number).
        text = localefmt.format_number(value, None, "en")
        digits = len(text.partition(".")[2])
    return int(digits), None


def odf_value(cell: CellModel, value: Any, column: Column | None) -> None:
    """Set the ODF value type of a cell with a value (decision 80)."""
    if isinstance(value, DateTime):
        cell.value_type = "date"
    elif is_number(value):
        currency = column.fields.get("currency") if column is not None and column_type(column) == "money" else None
        if currency and currency.isalpha() and len(currency) == 3:
            cell.value_type, cell.currency = "currency", currency.upper()
        else:
            cell.value_type = "float"
    else:
        cell.value_type = "string"


def literal_value(cell: CellModel, column: Column | None, lang: str) -> Any:
    """Initial value of a cell without a formula.

    Returns:
        The value of a single expression, the parsed literal of a typed
        column, the plain text of other cells (``None`` if empty).

    Raises:
        ParseError: a literal that does not match the column type.
    """
    if cell.value is not MISSING:
        return cell.value
    if cell.inlines is None:
        text = " ".join(plain_text(b.body) for b in cell.blocks or [] if isinstance(b, N.Paragraph))
    else:
        if any(isinstance(n, N.Formula) for n in cell.inlines):
            return None  # a mixed cell with a formula: a string, valued after formulas
        text = plain_text(cell.inlines)
    kind = column_type(column)
    if kind is not None and (cell.inlines is not None and all(isinstance(n, N.Text) for n in cell.inlines)):
        return parse_literal(text, kind, lang)
    return text or None


__all__ = ["ParseError", "column_type", "format_value", "is_number", "literal_value", "odf_value", "parse_literal"]
