"""Formatting cascade and borders of table cells (specification 6.6, 6.7).

Order: table style (and table arguments) → column → row → cell; every level
refines the previous one.  Cells of header and total rows also get the
``header_*`` / ``footer_*`` properties of the table style (on top of the
table level).

Borders (6.7): the table level gives the outer frame (``frame``) and the
inner rules (``rules``: ``all``, ``rows``, ``cols``, ``none``; the line of
inner rules is ``border`` of the table style, otherwise the frame).
Column, row and cell levels give ``border`` and ``border_<side>``.  On an
edge shared by two cells the more specific level wins; at equal levels the
cell further down or to the right wins.

In the ODT an inner vertical edge is written once — as the left border of
the right cell.  An inner horizontal edge is written on both cells — the
bottom border of the upper cell and the top border of the lower one, the same
resolved value: Writer draws cell borders as they are and does not close a
table split between pages, so each part needs its own line at the break
(remark of 27.10.2026).  The table is written with the collapsing border model
(``table:border-model``, ``odf/content.py``), so the two borders of an edge
make one line, not a double one.
"""

from __future__ import annotations

from typing import Any

from primula.styles.schema import Border, PropertyError, check_property
from primula.tables.grid import CellModel, Grid

#: Cascaded cell properties (6.6) other than borders.
CELL_KEYS = ("align", "valign", "padding", "background", "paragraph")
#: Text properties of ``header_*``/``footer_*`` applied to cell paragraphs.
TEXT_KEYS = ("font", "size", "bold", "italic", "color", "underline", "strike")
_SIDES = ("top", "bottom", "left", "right")
_LEVELS = {"table": 0, "column": 1, "row": 2, "cell": 3}


def _checked(props: dict[str, Any]) -> dict[str, Any]:
    """Cell properties of row/cell arguments, normalised (invalid ones dropped)."""
    result: dict[str, Any] = {}
    for key, value in props.items():
        if key in CELL_KEYS or key == "border" or key.startswith("border_"):
            if isinstance(value, Border):  # already normalised by col()
                result[key] = value
                continue
            try:
                result[key] = check_property("table", "header_" + key, value)
            except PropertyError:
                continue
    return result


def _side(props: dict[str, Any], side: str) -> Border | None:
    """Border of a side at one level: ``border_<side>``, otherwise ``border``."""
    value = props.get(f"border_{side}", props.get("border"))
    return value if isinstance(value, Border) else None


def table_level(style_props: dict[str, Any], args: dict[str, Any]) -> dict[str, Any]:
    """Table-level properties: the style, overridden by ``frame``/``rules``/``padding`` arguments."""
    props = dict(style_props)
    for key in ("frame", "rules", "border", "padding", "background"):
        if args.get(key) is not None:
            try:
                props[key] = check_property("table", key, args[key])
            except PropertyError:
                pass
    return props


def apply_cascade(grid: Grid, table_props: dict[str, Any]) -> None:
    """Compute ``props`` (cell properties with borders) and ``text_props`` of every cell."""
    columns = [_checked(dict(column.fields)) for column in grid.columns]
    rows = [_checked(row.args) for row in grid.rows]
    for row in grid.rows:
        prefix = {"header": "header_", "footer": "footer_"}.get(row.kind)
        for cell in row.cells:
            props: dict[str, Any] = {}
            for key in CELL_KEYS:
                if key in table_props and key != "align":
                    props[key] = table_props[key]
            text: dict[str, Any] = {}
            if prefix:
                for key, value in table_props.items():
                    if key.startswith(prefix):
                        inner = key[len(prefix):]
                        if inner in CELL_KEYS:
                            props[inner] = value
                        elif inner in TEXT_KEYS:
                            text[inner] = value
            for level in (columns[cell.col] if cell.col < len(columns) else {}, rows[row.index],
                          _checked(cell.args)):
                for key in CELL_KEYS:
                    if key in level:
                        props[key] = level[key]
            cell.props = props
            cell.text_props = text
    _borders(grid, table_props, columns, rows)


def _borders(grid: Grid, table_props: dict[str, Any], columns: list[dict[str, Any]],
             rows: list[dict[str, Any]]) -> None:
    """Resolve the borders of every cell side (6.7)."""
    frame = table_props.get("frame")
    frame = frame if isinstance(frame, Border) else None
    rules = table_props.get("rules", "all" if frame is not None else "none")
    inner = table_props.get("border", frame)
    inner = inner if isinstance(inner, Border) else None
    last_row, last_col = len(grid.rows), grid.count
    cell_levels = {id(cell): _checked(cell.args) for cell in grid.cells()}

    def levels(cell: CellModel, side: str) -> list[tuple[int, Border | None]]:
        """Values of one side of a cell by level (``None`` = not set)."""
        column = columns[cell.col] if cell.col < len(columns) else {}
        if side == "right":
            column = columns[min(cell.col + cell.span - 1, len(columns) - 1)] if columns else {}
        row = rows[cell.row] if side != "bottom" else rows[min(cell.row + cell.rows - 1, len(rows) - 1)]
        return [(_LEVELS["column"], _side(column, side)), (_LEVELS["row"], _side(row, side)),
                (_LEVELS["cell"], _side(cell_levels[id(cell)], side))]

    def resolve(first: CellModel | None, first_side: str, second: CellModel | None, second_side: str,
                table_value: Border | None) -> Border:
        """The winner on an edge between ``first`` (up/left) and ``second`` (down/right)."""
        best: tuple[int, int, Border | None] = (_LEVELS["table"], 0, table_value)
        for order, (cell, side) in enumerate(((first, first_side), (second, second_side))):
            if cell is None:
                continue
            for level, value in levels(cell, side):
                if value is not None and (level, order) >= best[:2]:
                    best = (level, order, value)
        return best[2] if best[2] is not None else Border(None)

    for cell in grid.cells():
        top, left = cell.row, cell.col
        bottom, right = cell.row + cell.rows, cell.col + cell.span
        above = grid.owners.get((top - 1, left)) if top > 0 else None
        before = grid.owners.get((top, left - 1)) if left > 0 else None
        borders: dict[str, Border] = {}
        horizontal_rule = inner if rules in ("all", "rows") else None
        vertical_rule = inner if rules in ("all", "cols") else None
        borders["top"] = resolve(above, "bottom", cell, "top", frame if top == 0 else horizontal_rule)
        borders["left"] = resolve(before, "right", cell, "left", frame if left == 0 else vertical_rule)
        # The edge below, written also here: the same winner as the top border of the cell below.
        below = grid.owners.get((bottom, left)) if bottom < last_row else None
        borders["bottom"] = (resolve(cell, "bottom", None, "top", frame) if below is None
                             else resolve(cell, "bottom", below, "top", horizontal_rule))
        borders["right"] = resolve(cell, "right", None, "left", frame) if right >= last_col else Border(None)
        for side in _SIDES:
            cell.props[f"border_{side}"] = borders[side]


def text_alignment(cell: CellModel) -> Any:
    """Horizontal alignment of the cell paragraphs (cascade result)."""
    return cell.props.get("align")
