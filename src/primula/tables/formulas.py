"""Deferred cell formulas ``|=(…)`` (specification 6.8, decision 81).

A formula is evaluated after all ordinary cells of its table are known,
lazily with memoisation: a reference to a cell with a formula evaluates
that formula first; each formula is evaluated once; a reference to a cell
under evaluation is a cycle (P5111 with the chain of cells).

Formula functions (rows and columns from 1; a column also by ``id``):

* ``this_row(c)`` — value in column ``c`` of the formula's row;
* ``cell(r, c)`` — value of a cell (a covered position gives the value of
  the spanning cell);
* ``column(c, rows=…)`` — list of values (default rows: ``body_rows()``;
  covered positions give ``None``);
* ``body_rows()`` — numbers of the rows between header and footer;
* ``sum``, ``min``, ``max``, ``avg`` skip ``None``; ``sum([])`` is 0;
  ``avg``/``min``/``max`` of nothing are errors; ``count`` counts
  non-empty values; a string in an aggregate is an error.

Outside a formula these functions are errors (P5106): the global
built-ins only report it; inside a formula an environment layer shadows
them with the working versions.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Callable

from primula.core.errors import CoreError, core_error

from primula.core.scope import Env
from primula.core.values import DECIMAL_CONTEXT, Builtin, PList
from primula.diagnostics import DiagnosticSink
from primula.tables.grid import CellModel, Grid
from primula.tables.values import is_number

#: Names of the formula functions (outside formulas: P5106).
TABLE_FUNCTIONS = ("this_row", "cell", "column", "body_rows", "avg", "count")


def make_table_builtins() -> dict[str, Builtin]:
    """Global stubs of the table functions: an error outside a cell formula."""
    def stub(name: str) -> Callable[..., Any]:
        def impl(interp: Any, args: list[Any], kwargs: dict[str, Any], span: Any) -> Any:
            raise core_error("P5106", span, name=name)
        return impl
    return {name: Builtin(name, stub(name)) for name in TABLE_FUNCTIONS}


def _cell_name(cell: CellModel) -> str:
    return f"r{cell.row + 1}c{cell.col + 1}"


class TableFormulas:
    """Values and formulas of one table.

    Args:
        grid: the table grid.
        interp: the core interpreter.
        sink: diagnostics receiver.
        values: initial values of cells without formulas (by ``id(cell)``).
    """

    PENDING, RUNNING, DONE = 0, 1, 2

    def __init__(self, grid: Grid, interp: Any, sink: DiagnosticSink, values: dict[int, Any]) -> None:
        self.grid = grid
        self.interp = interp
        self.sink = sink
        self.values = values
        self.state: dict[int, int] = {}
        self.stack: list[CellModel] = []

    # --- evaluation ---------------------------------------------------------------------

    def value(self, cell: CellModel | None) -> Any:
        """The value of a cell, evaluating its formula if needed.

        ``None`` (a position no cell covers: a row with missing cells, already
        reported as P5103) is an empty cell, as in 6.8.
        """
        if cell is None:
            return None
        if cell.formula is None:
            return self.values.get(id(cell))
        state = self.state.get(id(cell), self.PENDING)
        if state == self.DONE:
            return self.values.get(id(cell))
        if state == self.RUNNING:
            chain = " -> ".join(_cell_name(c) for c in [*self.stack[self.stack.index(cell):], cell])
            raise core_error("P5111", cell.formula.span, chain=chain)
        try:
            self.values[id(cell)] = self.evaluate(cell, cell.formula)
        except CoreError:
            # Every cell on the failing chain is finished without a value, so
            # the error (e.g. a cycle) is reported once, at the outermost cell.
            self.values[id(cell)] = None
            raise
        finally:
            self.state[id(cell)] = self.DONE
        return self.values[id(cell)]

    def evaluate(self, cell: CellModel, formula: Any) -> Any:
        """Evaluate a formula node in the context of ``cell``."""
        self.state[id(cell)] = self.RUNNING
        self.stack.append(cell)
        try:
            env = Env(formula.env.globals, formula.env, None)
            for name, impl in self._functions(cell).items():
                env.vars[name] = Builtin(name, impl)
            return self.interp.eval(formula.expr.node, env, formula.expr.fragment)
        finally:
            self.stack.pop()

    def run(self) -> None:
        """Evaluate every single-formula cell (errors are reported, the value is ``None``)."""
        for cell in self.grid.cells():
            if cell.formula is not None:
                try:
                    self.value(cell)
                except CoreError as exc:
                    self.sink.emit(exc.diagnostic)
                    self.values[id(cell)] = None
                    self.state[id(cell)] = self.DONE

    # --- functions ----------------------------------------------------------------------

    def _column(self, ref: Any, span: Any) -> int:
        index = self.grid.column_index(ref)
        if index is None:
            raise core_error("P5107", span, column=str(ref))
        return index

    def _row(self, ref: Any, span: Any) -> int:
        if not isinstance(ref, int) or isinstance(ref, bool) or not 1 <= ref <= len(self.grid.rows):
            raise core_error("P5108", span, row=str(ref), rows=len(self.grid.rows))
        return ref - 1

    def _functions(self, current: CellModel) -> dict[str, Callable[..., Any]]:
        grid = self.grid

        def this_row(interp: Any, args: list[Any], kwargs: dict[str, Any], span: Any) -> Any:
            if len(args) != 1 or kwargs:
                raise core_error("P2321", span, function="this_row", problem="takes one column")
            return self.value(grid.owners.get((current.row, self._column(args[0], span))))

        def cell(interp: Any, args: list[Any], kwargs: dict[str, Any], span: Any) -> Any:
            if len(args) != 2 or kwargs:
                raise core_error("P2321", span, function="cell", problem="takes a row and a column")
            return self.value(grid.owners.get((self._row(args[0], span), self._column(args[1], span))))

        def column(interp: Any, args: list[Any], kwargs: dict[str, Any], span: Any) -> Any:
            if len(args) != 1 or set(kwargs) - {"rows"}:
                raise core_error("P2321", span, function="column", problem="takes a column and rows=…")
            index = self._column(args[0], span)
            rows = kwargs.get("rows")
            numbers = grid.body_rows() if rows is None else list(rows)
            result = []
            for number in numbers:
                r = self._row(number, span)
                owner = grid.owners.get((r, index))
                result.append(self.value(owner) if owner is not None and (owner.row, owner.col) == (r, index) else None)
            return PList(result)

        def body_rows(interp: Any, args: list[Any], kwargs: dict[str, Any], span: Any) -> Any:
            return PList(grid.body_rows())

        def numbers(name: str, values: Any, span: Any) -> list[Any]:
            items = [v for v in (values if isinstance(values, (list, tuple)) else [values]) if v is not None]
            for item in items:
                if not is_number(item):
                    raise core_error("P5109", span, function=name, type=type(item).__name__)
            return items

        def aggregate(name: str) -> Callable[..., Any]:
            def impl(interp: Any, args: list[Any], kwargs: dict[str, Any], span: Any) -> Any:
                values = args[0] if len(args) == 1 else PList(args)
                items = numbers(name, values, span)
                if name == "count":
                    return len(items)
                if name == "sum":
                    return _total(items)
                if not items:
                    raise core_error("P5110", span, function=name)
                if name == "min":
                    return min(items)
                if name == "max":
                    return max(items)
                total = _total(items)
                if isinstance(total, float):
                    return total / len(items)
                return DECIMAL_CONTEXT.divide(Decimal(total), Decimal(len(items)))
            return impl

        functions: dict[str, Callable[..., Any]] = {
            "this_row": this_row, "cell": cell, "column": column, "body_rows": body_rows,
        }
        for name in ("sum", "min", "max", "avg", "count"):
            functions[name] = aggregate(name)
        return functions


def _total(items: list[Any]) -> Any:
    """Sum of numbers; ``int`` stays ``int``, decimals stay decimal."""
    total: Any = 0
    for item in items:
        if isinstance(item, float) or isinstance(total, float):
            total = float(total) + float(item)
        elif isinstance(item, Decimal) or isinstance(total, Decimal):
            total = DECIMAL_CONTEXT.add(Decimal(total), Decimal(item))
        else:
            total += item
    return total
