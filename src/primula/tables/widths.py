"""Column widths (specification 6.3, steps 1-6).

1. Fixed and percentage columns get their width.
2. For each ``auto`` column the minimum width (the longest unbreakable
   word) and the preferred width (the longest line without wrapping) are
   measured over its cells, plus the cell padding; nested tables count by
   their own minimum and preferred widths; spanned cells are not counted.
3. If the preferred widths (limited by the bounds) of the ``auto`` columns
   fit, they are used; otherwise the minimum widths, and the remainder is
   divided in proportion to the difference between preferred and minimum.
4. ``*`` columns take the remainder by weight.
5. Without ``*`` columns the table may become narrower than its width
   (upper bounds are not exceeded); it is aligned by ``align``.
6. If the minimum widths do not fit, the columns are narrowed
   proportionally and P5113 names them.

Widths are exact fractions of millimetres; the writer rounds them.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Any, Callable

from primula.core.values import Length
from primula.diagnostics import DiagnosticSink, warning
from primula.odf import units
from primula.structure.tree import plain_text
from primula.syntax import nodes as N
from primula.tables.columns import parse_width
from primula.tables.grid import CellModel, Grid
from primula.tables.metrics import MM_PER_PT, FontKey, text_width

#: ``measure(cell) -> (minimum, preferred)`` in millimetres, padding included.
Measure = Callable[[CellModel], tuple[Fraction, Fraction]]


#: Layout tolerance added to measured content (rounding of glyph positions in Writer).
SAFETY_MM = Fraction(1, 2)


def _padding(props: dict[str, Any]) -> Fraction:
    """Horizontal space of a cell besides its content: left and right padding."""
    padding = props.get("padding")
    if isinstance(padding, tuple):
        return units.to_mm(padding[1]) + units.to_mm(padding[3])
    if isinstance(padding, Length):
        return 2 * units.to_mm(padding)
    return Fraction(0)


def _frame(props: dict[str, Any]) -> Fraction:
    """Padding, left and right border lines and the layout tolerance of a cell."""
    total = _padding(props) + SAFETY_MM
    for side in ("left", "right"):
        border = props.get(f"border_{side}")
        if border is not None and getattr(border, "width", None) is not None:
            total += units.to_mm(border.width)
    return total


def _lines(inlines: list[Any]) -> list[str]:
    """Lines of inline content split at ``|\\``."""
    lines: list[list[Any]] = [[]]
    for node in inlines:
        if isinstance(node, N.LineBreak):
            lines.append([])
        else:
            lines[-1].append(node)
    return [plain_text(line) for line in lines]


class WidthCalculator:
    """Measures cells and computes column widths of tables.

    Args:
        font_of: ``font_of(cell, style_use) -> (FontKey, size in points)``.
        sink: receiver of P5112/P5113.
        nested: ``nested(block) -> Grid | None`` — the grid of a nested table.
    """

    def __init__(self, font_of: Callable[[CellModel, Any], tuple[FontKey, Fraction]], sink: DiagnosticSink,
                 nested: Callable[[Any], Grid | None]) -> None:
        self.font_of = font_of
        self.sink = sink
        self.nested = nested
        self.approximate: set[str] = set()

    # --- measuring ---------------------------------------------------------------------

    def _text(self, text: str, cell: CellModel, style_use: Any) -> tuple[Fraction, Fraction]:
        key, size = self.font_of(cell, style_use)
        longest, exact = text_width(text, key, size)
        words = [w for w in text.split() if w]
        word = max((text_width(w, key, size)[0] for w in words), default=Fraction(0))
        if not exact and key.family not in self.approximate:
            self.approximate.add(key.family)
            self.sink.emit(warning("P5112", getattr(cell.node, "span", None), font=key.family))
        return word, longest

    def measure(self, cell: CellModel) -> tuple[Fraction, Fraction]:
        """Minimum and preferred width of a cell's content, padding included."""
        minimum = preferred = Fraction(0)
        items: list[tuple[str, Any]] = []
        if cell.inlines is not None:
            for line in _lines(cell.display if cell.display is not None else cell.inlines):
                items.append((line, cell.style_use))
        for block in cell.blocks or []:
            if isinstance(block, N.Command) and block.name == "table":
                grid = self.nested(block)
                if grid is not None:
                    low, high = self.intrinsic(grid)
                    minimum, preferred = max(minimum, low), max(preferred, high)
                continue
            for node in _paragraph_nodes(block):
                for line in _lines(node.body):
                    items.append((line, getattr(node, "style_use", None)))
        for text, style_use in items:
            low, high = self._text(text, cell, style_use)
            minimum, preferred = max(minimum, low), max(preferred, high)
        frame = _frame(cell.props)
        return minimum + frame, preferred + frame

    def intrinsic(self, grid: Grid) -> tuple[Fraction, Fraction]:
        """Minimum and preferred width of a whole (nested) table."""
        low = high = Fraction(0)
        for index, column in enumerate(grid.columns):
            width = parse_width(column.fields.get("width"), column.fields.get("min"), column.fields.get("max"))
            if width.kind == "fixed" and width.length is not None:
                size = units.to_mm(width.length)
                low, high = low + size, high + size
                continue
            mins, prefs = self._column(grid, index)
            low, high = low + mins, high + prefs
        return low, high

    def _column(self, grid: Grid, index: int) -> tuple[Fraction, Fraction]:
        minimum = preferred = Fraction(0)
        for cell in grid.cells():
            if cell.col == index and cell.span == 1:
                low, high = self.measure(cell)
                minimum, preferred = max(minimum, low), max(preferred, high)
        return minimum, preferred

    # --- the algorithm -----------------------------------------------------------------

    def compute(self, grid: Grid, table_mm: Fraction) -> None:
        """Set ``grid.widths`` and ``grid.width`` (millimetres) for a table width."""
        specs = [parse_width(c.fields.get("width"), c.fields.get("min"), c.fields.get("max")) for c in grid.columns]
        widths: list[Fraction | None] = [None] * len(specs)
        for i, spec in enumerate(specs):
            if spec.kind == "fixed" and spec.length is not None:
                widths[i] = units.to_mm(spec.length)
            elif spec.kind == "percent":
                widths[i] = table_mm * (spec.share or Fraction(0)) / 100
        rest = table_mm - sum(w for w in widths if w is not None)
        autos = [i for i, s in enumerate(specs) if s.kind == "auto"]
        stars = [i for i, s in enumerate(specs) if s.kind == "star"]
        low: dict[int, Fraction] = {}
        high: dict[int, Fraction] = {}
        for i in autos:
            minimum, preferred = self._column(grid, i)
            lo = specs[i].low.mm(table_mm) if specs[i].low else Fraction(0)
            hi = specs[i].high.mm(table_mm) if specs[i].high else None
            preferred = max(preferred, lo) if hi is None else min(max(preferred, lo), hi)
            minimum = max(minimum, lo) if hi is None else min(max(minimum, lo), hi)
            low[i], high[i] = minimum, max(preferred, minimum)
        if sum(high.values()) <= rest:
            for i in autos:
                widths[i] = high[i]
        elif sum(low.values()) <= rest:
            spread = sum(high[i] - low[i] for i in autos)
            extra = rest - sum(low.values())
            for i in autos:
                widths[i] = low[i] + (extra * (high[i] - low[i]) / spread if spread else 0)
        else:
            total = sum(low.values())
            names = ", ".join(str(i + 1) for i in autos)
            self.sink.emit(warning("P5113", grid.node.span, columns=names))
            for i in autos:
                widths[i] = low[i] * max(rest, Fraction(0)) / total if total else Fraction(0)
        remainder = table_mm - sum(w for w in widths if w is not None)
        weights = sum((specs[i].share or Fraction(1)) for i in stars)
        for i in stars:
            widths[i] = max(remainder, Fraction(0)) * (specs[i].share or Fraction(1)) / weights
        grid.widths = [w if w is not None else Fraction(0) for w in widths]
        grid.width = sum(grid.widths)


def _paragraph_nodes(block: Any) -> list[Any]:
    """Paragraph-like nodes of a block (paragraphs, headings, clauses, list items)."""
    if isinstance(block, (N.Paragraph, N.Heading)):
        return [block]
    if isinstance(block, N.ListBlock):
        result = []
        for item in block.items:
            result.append(item)
            for child in item.children:
                result.extend(_paragraph_nodes(child))
        return result
    result = [block] if getattr(block, "body", None) else []
    for child in getattr(block, "children", None) or []:
        result.extend(_paragraph_nodes(child))
    return result


def points(size: Any) -> Fraction:
    """A font size (length) in points."""
    if isinstance(size, Length):
        return units.to_mm(size) / MM_PER_PT
    return Fraction(11)
