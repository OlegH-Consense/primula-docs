"""The grid of a table: rows, cells, spans and row kinds (specification 6.2-6.5).

Compact rows (``|: … |& …``) and expanded rows (``|row:`` with ``|cell:``)
are brought to one model:

* :class:`CellModel` — a cell with its grid position, spans, arguments and
  content: inline nodes (compact cells, ``|cell:`` line form, the inline
  body of ``|cell(…){…}``) or blocks (``|cell:`` environment);
* :class:`RowModel` — a row with its kind (``header``, ``body``,
  ``footer``) and arguments;
* :class:`Grid` — columns, rows and the owner of every grid position.

Positions covered by a span are skipped when cells are placed (6.5); every
row must fill exactly the free positions (decision 83: fewer and more
cells are errors, P5103).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from primula.diagnostics import DiagnosticSink, error
from primula.syntax import nodes as N
from primula.tables.columns import Column, column_of

#: Marker: the cell has no value computed by the evaluator.
MISSING = object()


@dataclass(eq=False)
class CellModel:
    """A table cell.

    Attributes:
        row, col: grid position of the top left corner (0-based).
        span, rows: horizontal and vertical span.
        node: the source node (``Cell``, ``InlineCommand`` or ``Command``).
        args: keyword arguments of the cell.
        inlines: inline content, or ``None`` for block content.
        blocks: block content of an expanded cell, or ``None``.
        value: value of a single ``|(…)`` (set by the evaluator) or :data:`MISSING`.
        formula: the single ``|=(…)`` node of the cell, or ``None``.
        span_source: node for diagnostics positions.
    """

    row: int
    col: int
    span: int
    rows: int
    node: Any
    args: dict[str, Any]
    inlines: list[Any] | None
    blocks: list[Any] | None
    value: Any = MISSING
    formula: Any = None
    # Filled by the cascade, values and widths passes:
    props: dict[str, Any] = field(default_factory=dict)
    text_props: dict[str, Any] = field(default_factory=dict)
    style_use: Any = None
    display: list[Any] | None = None
    typed: Any = MISSING
    value_type: str = "string"
    currency: str | None = None
    live_formula: str | None = None
    # (decimal places, currency symbol) of a numeric cell in a live=True
    # table: Writer recomputes formulas and shows them by this format.
    number_format: tuple[int, str | None] | None = None

    @property
    def span_node(self) -> Any:
        return self.node


@dataclass(eq=False)
class RowModel:
    """A table row: its kind, arguments and cells (in placing order)."""

    index: int
    kind: str
    node: Any
    args: dict[str, Any]
    cells: list[CellModel] = field(default_factory=list)


@dataclass(eq=False)
class Grid:
    """Columns, rows and positions of a table.

    Attributes:
        node: the ``|table`` command.
        columns: column objects (``cols``; equal ``*`` columns by default).
        rows: rows in order.
        owners: ``(row, col)`` -> the cell covering the position.
        header, footer: numbers of header and total rows.
        widths: computed column widths in millimetres (set by the widths pass).
        width: computed table width in millimetres.
    """

    node: Any
    columns: list[Column]
    rows: list[RowModel]
    owners: dict[tuple[int, int], CellModel]
    header: int
    footer: int
    widths: list[Any] = field(default_factory=list)
    width: Any = None

    @property
    def count(self) -> int:
        """Number of columns."""
        return len(self.columns)

    def cells(self) -> list[CellModel]:
        """All cells in row order."""
        return [cell for row in self.rows for cell in row.cells]

    def body_rows(self) -> list[int]:
        """1-based numbers of the rows between header and footer (decision 81)."""
        return list(range(self.header + 1, len(self.rows) - self.footer + 1))

    def column_index(self, ref: Any) -> int | None:
        """0-based index of a column given by a 1-based number or an ``id``."""
        if isinstance(ref, int) and not isinstance(ref, bool):
            return ref - 1 if 1 <= ref <= self.count else None
        if isinstance(ref, str):
            for index, column in enumerate(self.columns):
                if column.fields.get("id") == ref:
                    return index
        return None


def _args(node: Any) -> dict[str, Any]:
    args = getattr(node, "args", None)
    return dict(args.keywords) if args is not None and hasattr(args, "keywords") else {}


def _meaningful(inlines: list[Any]) -> list[Any]:
    """Inline nodes without whitespace-only text and comments."""
    return [n for n in inlines if not (isinstance(n, N.Comment) or isinstance(n, N.Text) and not n.value.strip())]


def _cell_from_compact(cell: N.Cell) -> tuple[Any, dict[str, Any], list[Any], Any]:
    """A compact cell; ``|& |cell(span=2){…}`` takes the arguments and body of ``|cell``."""
    args = _args(cell)
    inlines = list(cell.body)
    node: Any = cell
    meaningful = _meaningful(inlines)
    if len(meaningful) == 1 and isinstance(meaningful[0], N.InlineCommand) and meaningful[0].name == "cell":
        node = meaningful[0]
        args.update(_args(node))
        inlines = list(node.body or [])
    return node, args, inlines, getattr(node, "cell_value", MISSING)


def _single_formula(inlines: list[Any] | None) -> Any:
    if inlines is None:
        return None
    meaningful = _meaningful(inlines)
    return meaningful[0] if len(meaningful) == 1 and isinstance(meaningful[0], N.Formula) else None


def table_rows(block: N.Command) -> list[tuple[Any, dict[str, Any], list[tuple[Any, dict[str, Any], Any, Any, Any]]]]:
    """Rows of a table: ``(row node, row args, [(cell node, args, inlines, blocks, value)])``."""
    rows = []
    for child in block.children:
        if isinstance(child, N.TableRow):
            cells = []
            for cell in child.cells:
                node, args, inlines, value = _cell_from_compact(cell)
                cells.append((node, args, inlines, None, value))
            rows.append((child, _args(child), cells))
        elif isinstance(child, N.Command) and child.name == "row":
            cells = []
            for item in child.children:
                if isinstance(item, N.Command) and item.name == "cell":
                    if item.form == "env":
                        cells.append((item, _args(item), None, list(item.children),
                                      getattr(item, "cell_value", MISSING)))
                    else:
                        cells.append((item, _args(item), list(item.body or []), None,
                                      getattr(item, "cell_value", MISSING)))
            rows.append((child, _args(child), cells))
    return rows


def _positive(value: Any, default: int = 1) -> int:
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 1 else default


def _checked_column(value: Any, block: N.Command, sink: DiagnosticSink) -> Any:
    """A ``cols`` element as a column; a width string that is not a width gives P5102.

    ``col(…)`` checks its width when it is called; a plain string in ``cols`` is
    checked here (found by the robustness check of stage 13.15: it reached the
    width calculation and stopped the translator).  The column then counts as
    ``"*"``, so the rest of the table is still checked.
    """
    from primula.tables.columns import Column, parse_width

    if not isinstance(value, Column):
        try:
            parse_width(value)
        except (ValueError, TypeError):
            sink.emit(error("P5102", block.span, value=str(value)))
            value = "*"
    return column_of(value)


def build_grid(block: N.Command, sink: DiagnosticSink, style_cols: Any = None) -> Grid:
    """Build the grid of a ``|table`` and check cell counts (6.4, 6.5, decision 83).

    Args:
        block: the evaluated ``|table`` command.
        sink: diagnostics receiver (P5103, P5104).
        style_cols: ``cols`` of the table style, used when the table has none (decision 120).

    Returns:
        The grid; erroneous rows are kept as placed (the build fails anyway).
    """
    args = _args(block)
    raw_rows = table_rows(block)
    cols = args.get("cols") or style_cols  # cols of the table style are the default (decision 120)
    if isinstance(cols, (list, tuple)) and cols:
        columns = [_checked_column(c, block, sink) for c in cols]
    else:
        first = raw_rows[0][2] if raw_rows else []
        count = sum(_positive(a.get("span")) for _n, a, _i, _b, _v in first) or 1
        columns = [column_of("*") for _ in range(count)]
    width = len(columns)
    header = args.get("header", 1)
    header = header if isinstance(header, int) and not isinstance(header, bool) and header >= 0 else 1
    footer = args.get("footer", 0)
    footer = footer if isinstance(footer, int) and not isinstance(footer, bool) and footer >= 0 else 0
    total = len(raw_rows)

    owners: dict[tuple[int, int], CellModel] = {}
    rows: list[RowModel] = []
    for r, (row_node, row_args, cells) in enumerate(raw_rows):
        kind = "header" if r < header else ("footer" if r >= total - footer else "body")
        row = RowModel(r, kind, row_node, row_args)
        free = [c for c in range(width) if (r, c) not in owners]
        c = 0
        placed = 0
        overflow = False
        for node, cell_args, inlines, blocks, value in cells:
            while (r, c) in owners and c < width:
                c += 1
            span, down = _positive(cell_args.get("span")), _positive(cell_args.get("rows"))
            if c + span > width or any((r, c + k) in owners for k in range(span)):
                overflow = True
                break
            if r + down > total:
                sink.emit(error("P5104", node.span, rows=down, remaining=total - r))
                down = total - r
            cell = CellModel(r, c, span, down, node, cell_args, inlines, blocks, value, _single_formula(inlines))
            row.cells.append(cell)
            for dr in range(down):
                for dc in range(span):
                    owners[(r + dr, c + dc)] = cell
            placed += span
            c += span
        used = sum(_positive(a.get("span")) for _n, a, _i, _b, _v in cells)
        if overflow or placed != len(free):
            sink.emit(error("P5103", row_node.span, row=r + 1, used=used, free=len(free)))
        rows.append(row)
    return Grid(block, columns, rows, owners, header, footer)
