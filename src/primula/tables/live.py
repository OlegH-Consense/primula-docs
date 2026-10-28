"""Writer formulas for ``|table(live=True)`` (specification 6.8, decision 82).

Translated constructs:

* numeric constants, ``+ - * /``, brackets, unary minus;
* ``this_row(c)``, ``cell(r, c)`` -> cell references ``<C2>``;
* ``sum``, ``min``, ``max``, ``avg``, ``count`` of ``column(c)``,
  ``column(c, rows=body_rows())``, ``column(c, rows=range(a, b))`` ->
  ranges ``<D2:D5>`` (``avg`` is Writer's ``mean``).

Column and row arguments must be literals (a number or a column ``id``).
Anything else raises :class:`LiveError`; the caller reports P5114.  The
ODT gets both the formula (``table:formula="ooow:…"``) and the computed
value, so the document opens with correct numbers.

Reference: LibreOffice Writer table formulas,
https://help.libreoffice.org/latest/en-US/text/swriter/01/04090000.html
"""

from __future__ import annotations

import ast
from typing import Any

from primula.tables.grid import CellModel, Grid

_OPS = {ast.Add: "+", ast.Sub: "-", ast.Mult: "*", ast.Div: "/"}
_AGGREGATES = {"sum": "sum", "min": "min", "max": "max", "avg": "mean", "count": "count"}


class LiveError(Exception):
    """A formula outside the translatable subset."""


def column_letter(index: int) -> str:
    """0-based column index -> Writer column name (A, B, … Z, AA, …)."""
    text = ""
    index += 1
    while index:
        index, rest = divmod(index - 1, 26)
        text = chr(ord("A") + rest) + text
    return text


def translate(node: ast.expr, grid: Grid, cell: CellModel) -> str:
    """The Writer formula for a formula expression (without the ``ooow:`` prefix)."""
    return _Translator(grid, cell).expr(node)


class _Translator:
    def __init__(self, grid: Grid, cell: CellModel) -> None:
        self.grid = grid
        self.cell = cell

    def ref(self, row: int, column: Any) -> str:
        index = self.grid.column_index(column)
        if index is None:
            raise LiveError("column")
        return f"<{column_letter(index)}{row + 1}>"

    def literal(self, node: ast.expr) -> Any:
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, str)) and not isinstance(node.value, bool):
            return node.value
        raise LiveError("literal")

    def expr(self, node: ast.expr) -> str:
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
            return str(node.value)
        if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
            return f"({self.expr(node.left)}{_OPS[type(node.op)]}{self.expr(node.right)})"
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
            return ("-" if isinstance(node.op, ast.USub) else "") + self.expr(node.operand)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and not node.keywords:
            name, args = node.func.id, node.args
            if name == "this_row" and len(args) == 1:
                return self.ref(self.cell.row, self.literal(args[0]))
            if name == "cell" and len(args) == 2:
                row = self.literal(args[0])
                if not isinstance(row, int) or not 1 <= row <= len(self.grid.rows):
                    raise LiveError("row")
                return self.ref(row - 1, self.literal(args[1]))
            if name in _AGGREGATES and len(args) == 1:
                cells = self.range(args[0])
                if cells is None:
                    # An empty range (a table without body rows): Writer has
                    # no empty range; sum and count of nothing are 0 (6.8).
                    if name in ("sum", "count"):
                        return "0"
                    raise LiveError("range")
                return f"{_AGGREGATES[name]} {cells}"
        raise LiveError("construct")

    def range(self, node: ast.expr) -> str | None:
        """``column(c, rows=…)`` -> ``<D2:D5>``; ``None`` for an empty list of rows."""
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "column"
                and len(node.args) == 1):
            raise LiveError("range")
        column = self.literal(node.args[0])
        rows = self.grid.body_rows()
        for keyword in node.keywords:
            if keyword.arg != "rows":
                raise LiveError("range")
            value = keyword.value
            if isinstance(value, ast.Call) and isinstance(value.func, ast.Name) and value.func.id == "body_rows" \
                    and not value.args:
                continue
            if isinstance(value, ast.Call) and isinstance(value.func, ast.Name) and value.func.id == "range" \
                    and len(value.args) == 2:
                start, stop = self.literal(value.args[0]), self.literal(value.args[1])
                if not isinstance(start, int) or not isinstance(stop, int):
                    raise LiveError("range")
                rows = list(range(start, stop))
                continue
            raise LiveError("range")
        if not rows:
            self.ref(0, column)  # the column must still exist
            return None
        first, last = self.ref(rows[0] - 1, column), self.ref(rows[-1] - 1, column)
        return f"<{first[1:-1]}:{last[1:-1]}>"
