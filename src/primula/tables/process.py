"""The table phase over an evaluated, styled document (stage 13.7, specification 6).

For every table (outer tables before nested ones):

1. values of cells without formulas (:mod:`~primula.tables.values`);
2. formulas, lazily (:mod:`~primula.tables.formulas`), then formulas inside
   mixed cells («Разом: |=(…)», decision 80);
3. the text of valued cells by the column type and the ODF value type;
4. Writer formulas for ``live=True`` (:mod:`~primula.tables.live`);
5. column widths (:mod:`~primula.tables.widths`): an outer table by the
   width of the text area of the default page style, a nested table by
   the width of its cell.

The grid and the cascade are built earlier by the styles pass
(:class:`~primula.styles.apply.StyleApplier`), which needs the cell
paragraph styles; they are ``block.table_grid``.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Any

from primula.core.errors import CoreError
from primula.diagnostics import DiagnosticSink, error
from primula.odf import units
from primula.structure.settings import document_language
from primula.structure.tree import iter_tree
from primula.styles.system import StyleSystem, merge_props
from primula.syntax import nodes as N
from primula.tables.formulas import TableFormulas
from primula.tables.grid import MISSING, CellModel, Grid
from primula.tables.live import LiveError, translate
from primula.tables.metrics import FontKey
from primula.tables.values import (ParseError, column_type, format_value, literal_value, number_format,
                                   odf_value)
from primula.tables.widths import WidthCalculator, points


class TableProcessor:
    """Values, formulas and widths of the tables of a document.

    Args:
        interp: the core interpreter (formulas).
        system: the style system (fonts, page width).
        sink: diagnostics receiver.
        header_data: YAML header of the root document (the language).
        library: the standard library (currency symbols of ``money``
            columns with ``currency(…)`` of the styles modules), or ``None``.
        project_language: ``language`` of the project file (10.6), or ``None``.
    """

    def __init__(self, interp: Any, system: StyleSystem, sink: DiagnosticSink, header_data: dict[str, Any],
                 library: Any = None, project_language: str | None = None) -> None:
        self.interp = interp
        self.system = system
        self.sink = sink
        self.lang = document_language(header_data, system.defaults, project_language)
        self.symbols = None
        if library is not None:
            from primula.library.context import language_code

            self.symbols = lambda code, lang: library.currency_symbol(code, language_code(lang))
        self.widths = WidthCalculator(self._font, sink, lambda block: getattr(block, "table_grid", None))
        self.available: dict[int, Fraction] = {}

    def process(self, document: N.Document) -> list[dict[str, Any]]:
        """Process every table; return the report entries (6.3: computed widths)."""
        text_width = self._text_width(document)
        self._page_widths(document.children, text_width)
        report: list[dict[str, Any]] = []
        for node in iter_tree(document.children):
            grid = getattr(node, "table_grid", None) if isinstance(node, N.Command) and node.name == "table" else None
            if grid is None:
                continue
            self._values(grid)
            available = self.available.get(id(node), text_width)
            self.widths.compute(grid, self._table_width(grid, available))
            self._nested_widths(grid)
            position = node.span.source.position(node.span.start) if node.span is not None else None
            report.append({
                "file": node.span.source.name if node.span is not None else None,
                "line": position.line if position is not None else None,
                "widths_mm": [str(round(float(w), 2)) for w in grid.widths],
            })
        return report

    # --- widths ------------------------------------------------------------------------

    def _text_width(self, document: N.Document) -> Fraction:
        from primula.odf.styles_xml import page_geometry

        page = getattr(document, "page_style", None)
        if page and self.system.kind(page) == "page":
            return page_geometry(self.system.effective(page))["text_width"]
        return Fraction(170)

    def _page_widths(self, blocks: list[Any], width: Fraction) -> None:
        """Available width of top-level tables by the page style in force (7.3, 10.7).

        ``|page("Style")`` switches the style for the following blocks,
        ``|page("Style"):`` for its body; ``|appendix(page=…)`` and
        ``|document(page=…)`` for their bodies.  Nested tables get the width
        of their cell later (:meth:`_nested_widths`).
        """
        from primula.odf.styles_xml import page_geometry

        def page_width(name: Any) -> Fraction | None:
            if isinstance(name, str) and self.system.kind(name) == "page":
                return page_geometry(self.system.effective(name))["text_width"]
            return None

        for block in blocks:
            if not isinstance(block, N.Command):
                for children in (getattr(block, "children", None),):
                    if isinstance(children, list):
                        self._page_widths(children, width)
                continue
            if block.name == "table":
                self.available.setdefault(id(block), width)
                continue
            args = block.args
            if block.name == "section":
                # A table in a section with columns takes the width of a column (decision 132).
                self._page_widths(block.children or [], self._column_width(args, width))
                continue
            style = None
            if block.name == "page" and args is not None and getattr(args, "positional", None):
                style = args.positional[0]
            elif block.name in ("appendix", "document") and args is not None:
                style = getattr(args, "keywords", {}).get("page")
            inner = page_width(style) if style is not None else None
            if block.name == "page" and block.form != "env":
                width = inner or width
                continue
            self._page_widths(block.children, inner or width)

    @staticmethod
    def _column_width(args: Any, width: Fraction) -> Fraction:
        """The width of a column of ``|section(cols=…, widths=…, gap=…)`` (7.5, decision 132).

        Args:
            args: the evaluated arguments of the section.
            width: the width available to the section.

        Returns:
            ``(width - gaps) / cols``; with ``widths=`` (percentages) the
            narrowest column, since a table may stand in any of them.  Invalid
            arguments (reported by the page phase) leave ``width``.  The gap
            is 5 mm by default, as in the ODT.
        """
        from primula.styles.schema import PropertyError, check_property

        keywords = getattr(args, "keywords", {}) if args is not None else {}
        cols = keywords.get("cols", 1)
        if isinstance(cols, bool) or not isinstance(cols, int) or cols < 2:
            return width
        gap = Fraction(5)
        if keywords.get("gap") is not None:
            try:
                gap = Fraction(units.to_mm(check_property("page", "col_gap", keywords["gap"])))
            except (PropertyError, ValueError, TypeError):
                return width
        inner = width - gap * (cols - 1)
        if inner <= 0:
            return width
        shares = keywords.get("widths")
        if isinstance(shares, (list, tuple)) and len(shares) == cols:
            try:
                return inner * min(Fraction(str(share)[:-1]) for share in shares if str(share).endswith("%")) / 100
            except (ValueError, ArithmeticError):
                return width
        return inner / cols

    def _table_width(self, grid: Grid, available: Fraction) -> Fraction:
        args = grid.node.args
        style = getattr(grid.node, "table_style", None)
        props = self.system.effective(style) if style else {}
        value = args.get("width") if args is not None else None
        width: Any = props.get("width", ("percent", 100))
        if isinstance(value, str) and value.endswith("%"):
            try:
                width = ("percent", Fraction(value[:-1]))
            except ValueError:
                pass
        elif isinstance(value, str):
            from primula.core.values import parse_length

            width = parse_length(value) or width
        elif value is not None and hasattr(value, "inches"):
            width = value
        if isinstance(width, tuple):
            return available * Fraction(width[1]) / 100
        return units.to_mm(width)

    def _nested_widths(self, grid: Grid) -> None:
        """Available width of tables nested in cells: the cell width without padding."""
        from primula.tables.widths import _padding

        for cell in grid.cells():
            if not cell.blocks:
                continue
            width = sum(grid.widths[cell.col:cell.col + cell.span]) - _padding(cell.props)
            for block in iter_tree(cell.blocks):
                if isinstance(block, N.Command) and block.name == "table":
                    self.available.setdefault(id(block), max(width, Fraction(0)))

    def _font(self, cell: CellModel, style_use: Any) -> tuple[FontKey, Fraction]:
        """Font and size of a cell paragraph: style chain, cascade extras, ``header_*`` text."""
        props: dict[str, Any] = dict(self.system.defaults)
        if style_use is not None:
            props = merge_props(props, self.system.effective(style_use.parent))
            props = merge_props(props, style_use.extra)
        props = merge_props(props, cell.text_props)
        family = props.get("font") if isinstance(props.get("font"), str) else "Liberation Sans"
        return FontKey(family, bool(props.get("bold")), bool(props.get("italic"))), points(props.get("size"))

    # --- values and formulas -----------------------------------------------------------

    def _values(self, grid: Grid) -> None:
        values: dict[int, Any] = {}
        kinds = {id(cell): row.kind for row in grid.rows for cell in row.cells}
        for cell in grid.cells():
            if cell.formula is not None:
                continue
            # Column types apply to literals of body rows; header and total
            # rows hold labels («Кількість» above an int column, 6.9).
            column = grid.columns[cell.col] if cell.col < grid.count and kinds[id(cell)] == "body" else None
            try:
                values[id(cell)] = literal_value(cell, column, self.lang)
            except ParseError:
                self.sink.emit(error("P5105", cell.node.span, type=column_type(column) or "", text=str(
                    "".join(n.value for n in cell.inlines or [] if isinstance(n, N.Text)).strip())))
                values[id(cell)] = None
        formulas = TableFormulas(grid, self.interp, self.sink, values)
        formulas.run()
        live = bool(grid.node.args.get("live")) if grid.node.args is not None else False
        for cell in grid.cells():
            column = grid.columns[cell.col] if cell.col < grid.count else None
            body = kinds[id(cell)] == "body"
            self._mixed(formulas, cell)
            valued = cell.formula is not None or cell.value is not MISSING or (
                body and column_type(column) is not None and cell.inlines is not None
                and all(isinstance(n, N.Text) for n in cell.inlines))
            if not valued:
                continue
            value = formulas.values.get(id(cell))
            cell.typed = value
            span = cell.formula.span if cell.formula is not None else cell.node.span
            cell.display = [N.Text(span, format_value(value, column, self.lang, self.symbols))] if value is not None else []
            odf_value(cell, value, column)
            if live and cell.value_type in ("float", "currency"):
                cell.number_format = number_format(value, column, self.lang, self.symbols)
            if live and cell.formula is not None:
                try:
                    cell.live_formula = "ooow:" + translate(cell.formula.expr.node, grid, cell)
                except LiveError:
                    self.sink.emit(error("P5114", cell.formula.span).hint("help.live_formula"))

    def _mixed(self, formulas: TableFormulas, cell: CellModel) -> None:
        """Formulas inside mixed cells: text by the type of the value (decision 80)."""
        nodes = []
        if cell.inlines is not None:
            nodes = [n for n in cell.inlines if isinstance(n, N.Formula)] if cell.formula is None else []
        else:
            nodes = [n for n in _without_tables(cell.blocks or []) if isinstance(n, N.Formula)]
        for node in nodes:
            try:
                value = formulas.evaluate(cell, node)
            except CoreError as exc:
                self.sink.emit(exc.diagnostic)
                value = None
            finally:
                formulas.state[id(cell)] = formulas.DONE
            node.text = format_value(value, None, self.lang, self.symbols)


def _without_tables(blocks: list[Any]) -> list[Any]:
    """Nodes of cell blocks, not descending into nested tables (they have their own formulas)."""
    result: list[Any] = []
    for block in blocks:
        if isinstance(block, N.Command) and block.name == "table":
            continue
        result.extend(n for n in iter_tree([block]))
    return result
