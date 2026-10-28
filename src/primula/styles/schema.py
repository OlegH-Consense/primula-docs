"""Style kinds, properties and value formats (specification 11.2-11.3, decision 57).

Every property value is checked and normalised when a style is defined
(YAML group or ``paragraph_style(…)`` and similar calls):

* lengths: a string (``"2mm"``, ``"11pt"``) or a core ``length`` -> :class:`Length`;
* colours: ``"#RRGGBB"`` (``"#RGB"`` expanded) or ``"none"`` -> upper-case string;
* borders: ``"<width> <type> [<colour>]"`` or ``"none"`` -> :class:`Border`
  (the colour defaults to black: section 7.5 writes ``rule="0.5pt solid"``);
* ``line_height``: ``"115%"`` / a length / ``"at_least 5mm"`` -> :class:`LineHeight`;
* enumerations, booleans, integers, BCP 47 tags as listed in the table;
* ``odf``: attribute names are checked against the ODF 1.3 schema.

:func:`check_property` raises :class:`PropertyError` with a message key;
callers turn it into P3101/P3102 with the position of the value.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
from typing import Any, Callable

from primula.core.values import Length, PDict, PList, Record, parse_length
from primula.unicode import is_identifier

#: Style kinds and their YAML groups (11.2).
KINDS: dict[str, str] = {
    "paragraphs": "paragraph", "characters": "character", "blocks": "block", "tables": "table",
    "lists": "list", "frames": "frame", "pages": "page",
}


class PropertyError(Exception):
    """An unknown property (``unknown``) or a wrong value (``value``)."""

    def __init__(self, kind: str, problem: str = "") -> None:
        super().__init__(problem)
        self.kind = kind
        self.problem = problem


@dataclass(frozen=True)
class Border:
    """A border line: width, type, colour (decision 57); ``width`` None = no line."""

    width: Length | None
    type: str = "solid"
    color: str = "#000000"


@dataclass(frozen=True)
class LineHeight:
    """``line_height``: ``percent`` (Decimal), ``exact`` or ``at_least`` (Length)."""

    mode: str
    value: Any


# ----------------------------------------------------------------------
# Value parsers
# ----------------------------------------------------------------------


def _length(value: Any) -> Length:
    if isinstance(value, Length):
        return value
    if isinstance(value, int) and not isinstance(value, bool) and value == 0:
        return Length(Decimal(0), "mm")
    if isinstance(value, str):
        parsed = parse_length(value)
        if parsed is not None:
            return parsed
    raise PropertyError("value", "a length such as \"2mm\" or 2*mm")


def _non_negative_length(value: Any) -> Length:
    length = _length(value)
    if length.inches < 0:
        raise PropertyError("value", "a length that is not negative")
    return length


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    raise PropertyError("value", "true or false")


def _int(value: Any) -> int:
    if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
        return value
    raise PropertyError("value", "an integer >= 0")


_COLOR_RE = re.compile(r"^#([0-9A-Fa-f]{3}|[0-9A-Fa-f]{6})$")


def _color(value: Any) -> str:
    if value in ("none", "transparent"):  # transparent — the ODF spelling (П-Н8)
        return "none"
    if isinstance(value, str) and _COLOR_RE.match(value):
        digits = value[1:]
        if len(digits) == 3:
            digits = "".join(c * 2 for c in digits)
        return "#" + digits.upper()
    raise PropertyError("value", "a colour \"#RRGGBB\", \"#RGB\" or \"none\"")


def _enum(*choices: str) -> Callable[[Any], str]:
    def check(value: Any) -> str:
        if isinstance(value, str) and value in choices:
            return value
        raise PropertyError("value", "one of " + ", ".join(choices))
    return check


def _text(value: Any) -> str:
    if isinstance(value, str) and value:
        return value
    raise PropertyError("value", "a non-empty string")


_LANGUAGE_RE = re.compile(r"^[A-Za-z]{2,3}(-[A-Za-z0-9]{2,8})*$")


def _language(value: Any) -> str:
    if isinstance(value, str) and _LANGUAGE_RE.match(value):
        return value
    raise PropertyError("value", "a BCP 47 language tag such as \"uk-UA\"")


def _underline(value: Any) -> Any:
    if isinstance(value, bool) or value == "double":
        return value
    raise PropertyError("value", "true, false or \"double\"")


_BORDER_TYPES = ("solid", "dashed", "dotted", "double")


def parse_border(value: Any) -> Border:
    """``"0.5pt solid #000000"`` / ``"0.5pt solid"`` / ``"none"`` -> :class:`Border`."""
    if value == "none":
        return Border(None)
    if isinstance(value, str):
        parts = value.split()
        if len(parts) in (2, 3) and parts[1] in _BORDER_TYPES:
            width = _non_negative_length(parts[0])
            color = _color(parts[2]) if len(parts) == 3 else "#000000"
            return Border(width, parts[1], color)
    raise PropertyError("value", "a border \"<width> <type> <colour>\" (solid, dashed, dotted, double) or \"none\"")


def _line_height(value: Any) -> LineHeight:
    if isinstance(value, str):
        text = value.strip()
        if text.endswith("%"):
            try:
                return LineHeight("percent", Decimal(text[:-1]))
            except ArithmeticError:
                pass
        elif text.startswith("at_least "):
            return LineHeight("at_least", _non_negative_length(text[len("at_least "):]))
        else:
            return LineHeight("exact", _non_negative_length(text))
    if isinstance(value, Length):
        return LineHeight("exact", value)
    raise PropertyError("value", "a percentage \"115%\", a length or \"at_least 5mm\"")


def _width(value: Any) -> Any:
    """Table/frame width: a length or a percentage string."""
    if isinstance(value, str) and value.endswith("%"):
        try:
            return ("percent", Decimal(value[:-1]))
        except ArithmeticError:
            pass
    return _non_negative_length(value)


def _padding(value: Any) -> Any:
    if isinstance(value, (PList, list, tuple)):
        if len(value) != 4:
            raise PropertyError("value", "one length or a list of four lengths")
        return tuple(_non_negative_length(item) for item in value)
    return _non_negative_length(value)


def _style_name(value: Any) -> str:
    # A style name is a Unicode identifier with hyphens (3.3, 3.9, 11.2).
    if isinstance(value, str) and is_identifier(value, "-"):
        return value
    raise PropertyError("value", "a style name")


def _any(value: Any) -> Any:
    return value


#: Properties elements that may receive ``odf=`` attributes, by style kind.
ODF_GROUPS: dict[str, tuple[str, ...]] = {
    "paragraph": ("paragraph", "text"), "character": ("text",), "block": ("paragraph", "text"),
    "table": ("table", "table-cell"), "list": ("list-level",), "frame": ("graphic",),
    "page": ("page-layout",),
}


def _odf(value: Any, kind: str) -> dict[str, str]:
    mapping = value.fields if isinstance(value, Record) else value
    if not isinstance(mapping, (dict, PDict)):
        raise PropertyError("value", "a mapping of ODF attribute names to strings")
    result: dict[str, str] = {}
    groups = odf_properties()
    known = {name for group in ODF_GROUPS[kind] for name in groups[group]}
    for key, item in mapping.items():
        if not isinstance(key, str) or key not in known:
            if isinstance(key, str) and key in odf_attributes():
                raise PropertyError("value", f"ODF attribute '{key}' does not belong to a {kind} style")
            raise PropertyError("value", f"unknown ODF attribute '{key}'")
        if not isinstance(item, str):
            raise PropertyError("value", f"the value of '{key}' must be a string")
        result[key] = item
    return result


def _string(value: Any) -> str:
    if isinstance(value, str):
        return value
    raise PropertyError("value", "a string")


def _letters(value: Any) -> str:
    """``letters="абв…"`` of a list level (П1): the allowed letters in order, each once."""
    if not isinstance(value, str) or not value or len(set(value)) != len(value) or not value.isalpha():
        raise PropertyError("value", "a string of distinct letters")
    return value


def _table_cols(value: Any) -> tuple[Any, ...]:
    """``cols`` of a table style (decision 120): the default of ``|table(cols=…)``.

    Elements: a width (``"52%"``, ``"30mm"``, ``"*"``), ``col(…)`` or a
    mapping of ``col`` arguments; only widths and cell formatting —
    ``id``, ``type``, ``currency``, ``digits`` describe content and belong
    to the table itself.
    """
    from primula.tables.columns import CELL_PROPS, Column, parse_width

    if not isinstance(value, (list, tuple, PList)) or not value:
        raise PropertyError("value", "a list of column widths or col(…)")
    result = []
    for item in value:
        fields = dict(item.fields.items()) if isinstance(item, Record) else (
            {str(k): v for k, v in item.items()} if isinstance(item, (dict, PDict)) else {"width": item})
        if set(fields) - {"width", "min", "max", *CELL_PROPS}:
            raise PropertyError("value", "column widths and formatting only (no id, type, currency, digits)")
        try:
            parse_width(fields.get("width", "*"), fields.get("min"), fields.get("max"))
        except (ValueError, TypeError):
            raise PropertyError("value", f"a column width, not {fields.get('width')!r}") from None
        result.append(Column(fields))
    return tuple(result)


_LEVEL_PROPERTIES: dict[str, Callable[[Any], Any]] = {
    "type": _enum("number", "bullet"), "format": _enum("1", "a", "A", "i", "I", "а", "А"),  # а, А — Cyrillic (11.3, decision 115)
    "prefix": _string, "suffix": _string, "letters": _letters, "bullet": _text, "left": _length, "hanging": _length, "start": _int, "paragraph": _style_name,
}


def _levels(value: Any) -> dict[int, dict[str, Any]]:
    mapping = value.fields if isinstance(value, Record) else value
    if not isinstance(mapping, (dict, PDict)):
        raise PropertyError("value", "a mapping \"level 1-10 -> properties\"")
    result: dict[int, dict[str, Any]] = {}
    for level, properties in mapping.items():
        number = int(level) if isinstance(level, (int, str)) and str(level).isdigit() else 0
        if not 1 <= number <= 10:
            raise PropertyError("value", f"list levels are 1-10, not {level!r}")
        props = properties.fields if isinstance(properties, Record) else properties
        if not isinstance(props, (dict, PDict)):
            raise PropertyError("value", f"properties of level {number} must be a mapping")
        checked: dict[str, Any] = {}
        for key, item in props.items():
            if key not in _LEVEL_PROPERTIES:
                raise PropertyError("value", f"unknown list level property '{key}'")
            checked[key] = _LEVEL_PROPERTIES[key](item)
        result[number] = checked
    return result


# ----------------------------------------------------------------------
# Property tables (11.3)
# ----------------------------------------------------------------------

_CHARACTER: dict[str, Callable[[Any], Any]] = {
    "font": _text, "size": _non_negative_length, "bold": _bool, "italic": _bool, "color": _color,
    "background": _color, "underline": _underline, "strike": _bool, "language": _language,
    "position": _enum("super", "sub", "normal"),
}
_PARAGRAPH: dict[str, Callable[[Any], Any]] = {
    **{k: v for k, v in _CHARACTER.items() if k != "position"},
    "align": _enum("left", "center", "right", "justify"), "line_height": _line_height,
    "space_before": _non_negative_length, "space_after": _non_negative_length,
    "left": _length, "right": _length, "first_line": _length,
    "keep_with_next": _bool, "keep_together": _bool, "page_break_before": _bool,
    "widows": _int, "orphans": _int,
}
_CELL: dict[str, Callable[[Any], Any]] = {
    "align": _enum("left", "center", "right", "justify"), "valign": _enum("top", "middle", "bottom"),
    "padding": _padding, "background": _color, "paragraph": _style_name,
    "border": parse_border, "border_top": parse_border, "border_bottom": parse_border,
    "border_left": parse_border, "border_right": parse_border,
}
_TABLE: dict[str, Callable[[Any], Any]] = {
    "width": _width, "align": _enum("left", "center", "right"), "frame": parse_border,
    "rules": _enum("all", "rows", "cols", "none"), "border": parse_border, "padding": _padding,
    "background": _color, "paragraph": _style_name, "repeat_header": _bool, "keep_rows": _bool,
    "may_break": _bool, "space_before": _non_negative_length, "space_after": _non_negative_length,
    "cols": lambda value: _table_cols(value),
}
_BLOCK: dict[str, Callable[[Any], Any]] = {
    "paragraph": _style_name, "space_before": _non_negative_length, "space_after": _non_negative_length,
    "keep_together": _bool,
}
_LIST: dict[str, Callable[[Any], Any]] = {"paragraph": _style_name, "levels": _levels}
_FRAME: dict[str, Callable[[Any], Any]] = {
    "place": _enum("inline", "left", "center", "right", "inside", "outside"),
    "valign": _enum("top", "middle", "bottom"), "x": _length, "y": _length,
    "rel": _enum("para", "area", "page"), "anchor": _enum("char", "para", "page"),
    "wrap": _enum("none", "side", "both", "auto", "through", "contour"), "layer": _enum("front", "back"),
    "gap": _padding, "width": _width, "height": _width, "rotate": _any, "mirror": _any, "crop": _any,
    "opacity": _any, "border": parse_border, "padding": _padding,
}
_PAGE: dict[str, Callable[[Any], Any]] = {
    "size": lambda value: check_page_size(value), "orientation": _enum("portrait", "landscape"), "margin": _padding,
    "margin_top": _length, "margin_right": _length, "margin_bottom": _length, "margin_left": _length,
    "cols": _int, "col_gap": _length, "col_rule": parse_border, "header_gap": _length,
    "header_min_height": _length, "footer_gap": _length, "footer_min_height": _length,
    "number_format": _enum("1", "i", "I", "a", "A"), "restart": _int, "next": _style_name,
    "background": _color, "watermark": _any, "mirror": _bool,
}
PROPERTIES: dict[str, dict[str, Callable[[Any], Any]]] = {
    "paragraph": _PARAGRAPH, "character": _CHARACTER, "block": _BLOCK, "table": _TABLE,
    "list": _LIST, "frame": _FRAME, "page": _PAGE,
}

#: Properties of every kind besides the table ones.
COMMON = ("parent", "odf")


def check_property(kind: str, name: str, value: Any) -> Any:
    """Check and normalise one property of a style of ``kind``.

    Args:
        kind: style kind (``paragraph``…).
        name: property name.
        value: the value (YAML data or a core value).

    Returns:
        The normalised value.

    Raises:
        PropertyError: ``unknown`` property or a wrong ``value``.
    """
    if name == "parent":
        return _style_name(value)
    if name == "odf":
        return _odf(value, kind)
    table = PROPERTIES[kind]
    if name in table:
        return table[name](value)
    if kind == "table":
        for prefix in ("header_", "footer_"):
            if name.startswith(prefix):
                inner = name[len(prefix):]
                for group in (_CELL, _PARAGRAPH):
                    if inner in group:
                        return group[inner](value)
    raise PropertyError("unknown")


def check_page_size(value: Any) -> Any:
    """``size`` of a page: a name or a pair of lengths (7.2)."""
    if value in ("A4", "A5", "A3", "Letter"):
        return value
    if isinstance(value, (PList, list, tuple)) and len(value) == 2:
        return (_non_negative_length(value[0]), _non_negative_length(value[1]))
    raise PropertyError("value", "\"A4\", \"A5\", \"A3\", \"Letter\" or (width, height)")


_ATTRIBUTES: frozenset[str] | None = None
_PROPERTIES: dict[str, frozenset[str]] | None = None


def odf_properties() -> dict[str, frozenset[str]]:
    """Attribute names of each ``style:*-properties`` element (``odf_properties.json``)."""
    global _PROPERTIES
    if _PROPERTIES is None:
        import json

        data = json.loads(Path(__file__).with_name("odf_properties.json").read_text(encoding="utf-8"))
        _PROPERTIES = {group: frozenset(names) for group, names in data.items()}
    return _PROPERTIES


def odf_attributes() -> frozenset[str]:
    """Attribute names of ODF 1.3 (``odf_attributes.txt``, generated from the schema)."""
    global _ATTRIBUTES
    if _ATTRIBUTES is None:
        path = Path(__file__).with_name("odf_attributes.txt")
        _ATTRIBUTES = frozenset(line.strip() for line in path.read_text(encoding="utf-8").splitlines()
                                if line.strip() and not line.startswith("#"))
    return _ATTRIBUTES
