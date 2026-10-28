"""Applying styles to the evaluated tree (specification 4.3-4.5, 5.4, 11.4-11.6).

The pass walks the evaluated and organised document and annotates nodes:

* ``style_use`` (:class:`StyleUse`) on every paragraph-like node — plain
  paragraphs, headings, clause texts, list item texts, styled paragraphs,
  admonition texts, cell paragraphs: the named parent style and the
  automatic properties of the cascade (decision 61);
* ``char_style`` on character style spans (and ``|—{…}`` -> ``StrikeText``,
  ``|?{…}`` -> ``Placeholder`` if those styles exist, 3.3);
* ``list_style`` on lists (with a materialised variant when level types
  differ from the markers, 5.4, decision 56);
* ``table_style`` on tables, ``block_style`` on block groups;
* styles of structure constructs (decision 70): ``caption_style`` on
  tables and figures, ``appendix_styles`` on annexes, ``index_styles`` on
  ``|toc``/``|list_of``, ``note_style`` on notes, ``char_style`` on
  references ``|@``.

Construct styles come from ``structure_styles`` (11.5) and ``|set`` (4.5,
decision 60): ``|set`` acts until the end of the nearest enclosing
structural environment (or the document); bodies of ``|if``/``|for``/
``|def`` are already expanded and create no region; a ``|set`` of a
fragment acts until the end of the fragment (the evaluator converts it to
``set_overrides`` on the following blocks of the fragment).

Cascade (11.6, decision 61): the parent of the automatic paragraph style is
the innermost explicit paragraph style (``|.Name``, a parametric variant,
``derive``), otherwise the construct style; the automatic properties are
the own properties of the outer layers (outer ``|.Name:`` environments,
the construct style) that the parent chain does not define; cell alignment
comes last.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from primula.core.errors import CoreError, core_error
from primula.core.values import PDict, Record
from primula.diagnostics import DiagnosticSink, warning
from primula.source import Span
from primula.styles.functions import STRUCTURE_KEYS
from primula.styles.system import StyleSystem, merge_props
from primula.syntax import nodes as N

#: Marker "keep the value of the outer region".
_KEEP = object()

#: Construct style names used when ``structure_styles`` does not name them.
FALLBACK = {"paragraph": "Body", "list": "BulletList", "numbered_list": "NumberedList",
            "table": "TableGrid", "admonition": "Admonition", "figure": "Figure", "page": "Portrait",
            "strong": "Strong", "emphasis": "Emphasis", "underline": "Underline",
            "superscript": "Superscript", "subscript": "Subscript", "code": "Code",
            "strike": "StrikeText", "placeholder": "Placeholder",
            "footnote": "Footnote", "endnote": "Endnote", "note_anchor": "NoteAnchor", "reference": "Reference",
            "parallel_table": "ParallelTable", "parallel_header": "ParallelHeader"}

#: Fallback names of the parts of structure constructs (decision 70).
PART_FALLBACK: dict[str, dict[Any, str]] = {
    "caption": {"table": "TableCaption", "figure": "FigureCaption"},
    "appendix": {"designation": "AppendixDesignation", "subtitle": "AppendixSubtitle", "title": "AppendixTitle"},
    "toc": {"title": "ContentsTitle", **{level: f"Contents{level}" for level in range(1, 11)}},
    "list_of": {"title": "ContentsTitle", "entry": "IndexEntry"},
}

#: Character style keys of inline short forms (decision 62); quotes have no style.
SHORT_KEYS = {"*": "strong", "/": "emphasis", "_": "underline", "^": "superscript", ",": "subscript",
              "`": "code", "—": "strike", "?": "placeholder"}


@dataclass
class StyleUse:
    """The style of a paragraph-like node: named parent + automatic properties."""

    parent: str
    extra: dict[str, Any] = field(default_factory=dict)

    def dump_text(self) -> str:
        if not self.extra:
            return self.parent
        return self.parent + " +" + ",".join(sorted(self.extra))


@dataclass
class _Region:
    """Style context of a region of the tree."""

    overrides: dict[str, Any] = field(default_factory=dict)
    explicit: list[str] = field(default_factory=list)  # outer -> inner
    construct_paragraph: str | None = None
    cell_align: str | None = None


class StyleApplier:
    """Annotates an evaluated document with styles.

    Args:
        system: the style system.
        sink: diagnostics receiver.
        scale: ``scale(kind, value)`` — length of a spacing step or an
            indent (``spacing``/``indent_step`` of the styles level, 11.4).
    """

    def __init__(self, system: StyleSystem, sink: DiagnosticSink,
                 scale: Callable[[str, Any], Any]) -> None:
        self.system = system
        self.sink = sink
        self.scale = scale
        self.structure = dict(system.settings.get("structure_styles", {}))
        self._reported: set[str] = set()

    def apply(self, document: N.Document) -> None:
        """Annotate the document in place (and headers/footers of styles modules, 7.6)."""
        page = self._construct("page", _Region())
        document.page_style = self._require(page, "page", document.span)
        self._blocks(document.children, _Region())
        for part in ("header", "footer"):
            for content in (self.system.settings.get(part) or {}).values():
                nodes = getattr(content, "nodes", None)
                if nodes:
                    region = self._part_region(part, _Region())
                    if getattr(content, "kind", "blocks") == "blocks":
                        self._blocks(nodes, region)
                    else:
                        self._current = region
                        self._inlines(nodes)

    def _part_region(self, part: str, region: _Region) -> _Region:
        """Region of header/footer content: paragraphs default to ``Header``/``Footer`` (7.6)."""
        style = "Header" if part == "header" else "Footer"
        if self.system.kind(style) != "paragraph":
            return self._inner(region)
        return self._inner(region, construct_paragraph=style)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def report(self, exc: CoreError) -> None:
        self.sink.emit(exc.diagnostic)

    def _require(self, name: Any, kind: str, span: Span | None) -> str | None:
        """Check that a style exists and has the kind (P3108/P3109)."""
        if not isinstance(name, str):
            return None
        try:
            self.system.ensure(name, span)  # a name reserved by derive(…), 11.4
        except CoreError as exc:
            self.report(exc)
            return None
        actual = self.system.kind(name)
        if actual is None:
            if name not in self._reported:
                self._reported.add(name)
                self.report(core_error("P3108", span, name=name))
            return None
        if actual != kind:
            self.report(core_error("P3109", span, name=name, kind=actual, expected=kind))
            return None
        return name

    def _construct(self, key: str, region: _Region, level: int | None = None) -> Any:
        """Construct style from ``|set`` or ``structure_styles`` (fallback names)."""
        value = region.overrides.get(key, self.structure.get(key))
        if isinstance(value, (dict, PDict, Record)):
            mapping = value.fields if isinstance(value, Record) else value
            value = mapping.get(level) if level is not None else None
            if value is None and level is not None:
                value = mapping.get(str(level))
        if value is None:
            if key == "heading":
                return f"Heading{level}"
            if key == "clause":
                return "Clause" if level == 1 else "SubClause"
            return FALLBACK.get(key)
        return value

    def _number_style(self, key: str, region: _Region, span: Any) -> str | None:
        """Character style of an automatic number (``clause_number``, ``heading_number``; decision 120).

        Not set by default: the number is formatted like its paragraph.
        """
        value = region.overrides.get(key, self.structure.get(key))
        return self._require(value, "character", span) if isinstance(value, str) else None

    def _part(self, key: str, part: Any, region: _Region) -> Any:
        """Style of a part of a structure construct: ``caption={"table": …}`` (decision 70)."""
        value = region.overrides.get(key, self.structure.get(key))
        if isinstance(value, (dict, PDict, Record)):
            mapping = value.fields if isinstance(value, Record) else value
            chosen = mapping.get(part)
            if chosen is None:
                chosen = mapping.get(str(part))
            if chosen is not None:
                return chosen
        return PART_FALLBACK.get(key, {}).get(part)

    def _use(self, construct: str | None, region: _Region, span: Span, own: str | None = None) -> StyleUse | None:
        """Cascade for a paragraph-like node (decision 61)."""
        layers = [name for name in [construct, *region.explicit, own] if name]
        if not layers:
            return None
        parent = layers[-1]
        if self.system.kind(parent) is None:
            return None
        parent_props = self.system.effective(parent)
        extra: dict[str, Any] = {}
        for name in layers[:-1]:
            extra = merge_props(extra, self.system.effective(name))
        extra = {k: v for k, v in extra.items() if k not in parent_props}
        if region.cell_align is not None:
            extra["align"] = region.cell_align
        return StyleUse(parent, extra)

    def _paragraph_style(self, region: _Region, span: Span) -> str | None:
        name = region.construct_paragraph or self._construct("paragraph", region)
        return self._require(name, "paragraph", span) if name else None

    # ------------------------------------------------------------------
    # Blocks
    # ------------------------------------------------------------------

    def _blocks(self, blocks: list[Any], region: _Region) -> None:
        current = region
        for block in blocks:
            overrides = getattr(block, "set_overrides", None)
            target = current
            if overrides is not None:
                target = _Region(merge_overrides(current.overrides, overrides), current.explicit,
                                 current.construct_paragraph, current.cell_align)
            if isinstance(block, N.Command) and block.name == "set":
                current = self._set(block, current)
                continue
            try:
                self._block(block, target)
            except CoreError as exc:
                self.report(exc)

    def _set(self, block: N.Command, region: _Region) -> _Region:
        """``|set(key=value)``: a new region state for the following siblings."""
        args = block.args
        if args is None:
            return region
        try:
            return _Region(merge_overrides(region.overrides, self.check_set(args.keywords, args.span)),
                           region.explicit, region.construct_paragraph, region.cell_align)
        except CoreError as exc:
            self.report(exc)
            return region

    def check_set(self, keywords: dict[str, Any], span: Span) -> dict[str, Any]:
        """Check ``|set`` keys (decision 60); ``None`` values reset."""
        for key in keywords:
            if key not in STRUCTURE_KEYS:
                raise core_error("P3115", span, key=key)
        return dict(keywords)

    def _inner(self, region: _Region, *, explicit: list[str] | None = None,
               construct_paragraph: Any = _KEEP, cell_align: Any = _KEEP) -> _Region:
        """A nested region: ``|set`` overrides are copied and end with the region."""
        return _Region(
            dict(region.overrides),
            list(region.explicit if explicit is None else explicit),
            region.construct_paragraph if construct_paragraph is _KEEP else construct_paragraph,
            region.cell_align if cell_align is _KEEP else cell_align,
        )

    def _block(self, block: Any, region: _Region) -> None:
        self._current = region
        if isinstance(block, N.Paragraph):
            block.style_use = self._use(self._paragraph_style(region, block.span), region, block.span)
            self._inlines(block.body)
        elif isinstance(block, N.Heading):
            # level= is applied by the evaluator (5.2, decision 105), level_shift= after it (П3).
            own = _style_arg(block)  # |<(style="…") — this heading only (decision 120)
            name = self._require(own or self._construct("heading", region, block.level), "paragraph", block.span)
            block.style_use = StyleUse(name) if name else None
            block.number_style = self._number_style("heading_number", region, block.span)
            self._inlines(block.body)
        elif isinstance(block, N.Clause):
            own = _style_arg(block)  # |>(style="…") — this clause only (decision 120)
            construct = self._require(own or self._construct("clause", region, block.level), "paragraph", block.span)
            block.number_style = self._number_style("clause_number", region, block.span)
            if block.form == "line":
                block.style_use = self._use(construct, region, block.span)
                self._inlines(block.body)
                self._blocks(block.children, region)
            else:
                self._blocks(block.children, self._inner(region, construct_paragraph=construct))
            self._block_arg(block)
        elif isinstance(block, N.StyleBlock):
            own = self._explicit(block)
            if block.form == "line":
                block.style_use = self._use(self._paragraph_style(region, block.span), region, block.span, own)
                self._inlines(block.body)
            else:
                explicit = [*region.explicit, own] if own else list(region.explicit)
                self._blocks(block.children, self._inner(region, explicit=explicit))
        elif isinstance(block, N.ListBlock):
            self._list(block, region, None)
        elif isinstance(block, N.Verbatim):
            # Literal lines form one paragraph styled like a paragraph in the
            # same place: |.Зразок: … |verbatim: … |end.Зразок (4.3, 11.6).
            block.style_use = self._use(self._paragraph_style(region, block.span), region, block.span)
        elif isinstance(block, N.Admonition):
            name = self._construct("admonition", region)
            block.admonition_style = name
            if block.form == "line":
                block.style_use = self._use(self._paragraph_style(region, block.span), region, block.span)
                self._inlines(block.body)
            self._blocks(block.children, self._inner(region))
            self._block_arg(block)
        elif isinstance(block, N.Command):
            self._command(block, region)
        elif isinstance(block, N.TableRow):
            self._row(block, region, False)

    def _explicit(self, block: N.StyleBlock) -> str | None:
        """The paragraph style of ``|.Name`` / ``|.(expr)`` with parameters."""
        ref = block.style
        base = self._require(ref.name, "paragraph", ref.span)
        if base is None:
            return None
        args = block.args
        if args is None or (not args.positional and not args.keywords):
            return base
        unknown = [k for k in args.keywords if k not in ("before", "after", "indent")]
        if args.positional or unknown:
            self.report(core_error("P3113", args.span, name=unknown[0] if unknown else "positional"))
            return base
        try:
            return self.system.variant(base, args.keywords, self.scale, args.span)
        except CoreError as exc:
            self.report(exc)
            return base

    def _block_arg(self, block: Any) -> None:
        """``block="Name"`` argument of ``|>``, ``|!``, ``|table``, ``|figure``, ``|appendix``."""
        args = getattr(block, "args", None)
        name = args.get("block") if args is not None and hasattr(args, "get") else None
        if name is not None:
            block.block_style = self._require(name, "block", args.span)

    def _command(self, block: N.Command, region: _Region) -> None:
        name = block.name
        if name == "table":
            self._table(block, region)
            return
        if name == "figure":
            block.caption_style = self._require(self._part("caption", "figure", region), "paragraph", block.span)
            block.image_style = self._require(self._construct("figure", region), "paragraph", block.span)
            self._inline_children(block)
            return
        if name == "appendix":
            block.appendix_styles = {part: self._require(self._part("appendix", part, region), "paragraph", block.span)
                                     for part in ("designation", "subtitle", "title")}
        if name in ("toc", "list_of"):
            self._index_styles(block, region)
            return
        if name == "block" and block.form == "env":
            args = block.args
            style = args.positional[0] if args is not None and args.positional else None
            block.block_style = self._require(style, "block", block.span)
            paragraph = self.system.effective(block.block_style).get("paragraph") if block.block_style else None
            inner = self._inner(region, construct_paragraph=paragraph or region.construct_paragraph)
            self._blocks(block.children, inner)
            return
        self._block_arg(block)
        if name in ("header", "footer") and block.form == "env":
            self._blocks(block.children, self._part_region(name, region))
            return
        if name in ("img", "frame") and block.form != "env":
            # A block image: its own paragraph in the paragraph style of the region.
            block.style_use = self._use(self._paragraph_style(region, block.span), region, block.span)
            return
        if block.body:
            block.style_use = self._use(self._paragraph_style(region, block.span), region, block.span)
            self._inlines(block.body)
        if block.form == "env":
            self._blocks(block.children, self._inner(region))

    def _inline_children(self, block: N.Command) -> None:
        """Caption paragraphs of ``|figure:``/``|caption:``: inline styles only."""
        self._inlines(block.body or [])
        for child in block.children:
            self._inlines(getattr(child, "body", None) or [])

    def _index_styles(self, block: N.Command, region: _Region) -> None:
        """Styles of ``|toc`` (title, levels) and ``|list_of`` (title, entry)."""
        key = block.name
        styles: dict[Any, str | None] = {"title": self._require(self._part(key, "title", region), "paragraph",
                                                                 block.span)}
        if key == "toc":
            max_level = block.args.get("max_level", 3) if block.args is not None else 3
            max_level = max_level if isinstance(max_level, int) and 1 <= max_level <= 10 else 3
            for level in range(1, max_level + 1):
                styles[level] = self._require(self._part(key, level, region), "paragraph", block.span)
        else:
            styles["entry"] = self._require(self._part(key, "entry", region), "paragraph", block.span)
        block.index_styles = styles

    def _table(self, block: N.Command, region: _Region) -> None:
        """A table (6.2, 6.6): style, grid, cell cascade, paragraph styles of cells.

        The grid and the cascade (:mod:`primula.tables`) give each cell its
        paragraph style and alignment (table → column → row → cell,
        ``header_*``/``footer_*``); the cell content is styled in a region
        with them.  ``block.table_grid`` is used by the table phase and the
        ODT writer.
        """
        from primula.tables.cascade import apply_cascade, table_level
        from primula.tables.grid import build_grid

        args = block.args
        style = args.get("style") if args is not None else None
        if style is None:
            # A |parallel is written as a table of its own style (7.7).
            style = self._construct("parallel_table" if getattr(block, "parallel", None) else "table", region)
        block.table_style = self._require(style, "table", block.span)
        caption = args.get("caption") if args is not None else None
        if caption is not None or any(isinstance(c, N.Command) and c.name == "caption" for c in block.children):
            block.caption_style = self._require(self._part("caption", "table", region), "paragraph", block.span)
        self._block_arg(block)
        props = self.system.effective(block.table_style) if block.table_style else {}
        grid = build_grid(block, self.sink, props.get("cols"))
        block.table_grid = grid
        apply_cascade(grid, table_level(props, dict(args.keywords) if args is not None else {}))
        for cell in grid.cells():
            paragraph = cell.props.get("paragraph") or region.construct_paragraph
            if getattr(cell.node, "parallel_header", False):
                paragraph = self._construct("parallel_header", region)  # titles of the tracks (7.7)
            if paragraph is not None and self._require(paragraph, "paragraph", cell.node.span) is None:
                paragraph = region.construct_paragraph
            cell_region = self._inner(region, construct_paragraph=paragraph, cell_align=cell.props.get("align"))
            if cell.inlines is not None:
                cell.style_use = self._use(self._paragraph_style(cell_region, cell.node.span), cell_region,
                                           cell.node.span)
                cell.node.style_use = cell.style_use  # tree dumps and tests show it on the cell
                self._current = cell_region
                self._inlines(cell.inlines)
            else:
                self._blocks(cell.blocks or [], cell_region)
        for child in block.children:
            if isinstance(child, N.Command) and child.name == "caption":
                self._command(child, self._inner(region))

    def _row(self, row: N.TableRow, region: _Region, header: bool) -> None:
        for cell in row.cells:
            align = cell.args.get("align") if cell.args is not None else None
            cell_region = self._inner(region, cell_align=align)
            cell.style_use = self._use(self._paragraph_style(cell_region, cell.span), cell_region, cell.span)
            self._inlines(cell.body)

    def _list(self, block: N.ListBlock, region: _Region, inherited: str | None) -> None:
        """List style (5.4): ``|list("Name")``, ``|set(list=…)``, ``structure_styles``."""
        style_command = block.style
        name: Any = None
        if style_command is not None and style_command.args is not None and style_command.args.positional:
            name = style_command.args.positional[0]
        if name is None:
            name = inherited
        if name is None and block.items:
            name = self._construct("numbered_list" if block.items[0].kind == "number" else "list", region)
        base = self._require(name, "list", block.span)
        if base is None:
            return
        kinds: dict[int, str] = {}
        _collect_levels(block, kinds, 1)
        levels = self.system.effective(base).get("levels", {})
        mismatched = {level: kind for level, kind in kinds.items()
                      if levels.get(level, {}).get("type", kind) != kind}
        style = base
        if mismatched:
            try:
                style = self.system.list_variant(base, mismatched, block.span)
            except CoreError as exc:
                self.report(exc)
        _set_list_style(block, style)
        paragraph = self.system.effective(base).get("paragraph")
        item_region = self._inner(region, construct_paragraph=paragraph or region.construct_paragraph)
        self._items(block, item_region)

    def _items(self, block: N.ListBlock, region: _Region) -> None:
        for item in block.items:
            item.style_use = self._use(self._paragraph_style(region, item.span), region, item.span)
            self._inlines(item.body)
            for child in item.children:
                if isinstance(child, N.ListBlock):
                    if _has_own_style(child):
                        self._list(child, region, None)
                    else:
                        self._items(child, region)
                else:
                    self._block(child, region)

    # ------------------------------------------------------------------
    # Inline
    # ------------------------------------------------------------------

    def _inlines(self, nodes: list[Any]) -> None:
        for node in nodes:
            if isinstance(node, N.StyleSpan):
                if node.args is not None and (node.args.positional or node.args.keywords):
                    self.report(core_error("P3113", node.args.span, name="character style"))
                node.char_style = self._require(node.style.name, "character", node.style.span)
                self._inlines(node.body)
            elif isinstance(node, N.Short):
                key = SHORT_KEYS.get(node.mark)
                if key is not None:
                    region = getattr(self, "_current", None) or _Region()
                    node.char_style = self._require(self._construct(key, region), "character", node.span)
                self._inlines(node.body)
            elif isinstance(node, N.InlineCommand):
                if node.name == "fmt":
                    self.sink.emit(warning("P3118", node.name_span))
                if node.name == "link":
                    # External links: structure_styles(link=…), otherwise the reference style (decision 120).
                    region = getattr(self, "_current", None) or _Region()
                    key = "link" if region.overrides.get("link", self.structure.get("link")) else "reference"
                    node.char_style = self._require(self._construct(key, region), "character", node.span)
                if node.name in ("footnote", "endnote"):
                    region = getattr(self, "_current", None) or _Region()
                    node.note_style = self._require(self._construct(node.name, region), "paragraph", node.span)
                    node.anchor_style = self._require(self._construct("note_anchor", region), "character",
                                                      node.span)
                if node.body:
                    self._inlines(node.body)
            elif isinstance(node, N.Reference):
                region = getattr(self, "_current", None) or _Region()
                node.char_style = self._require(self._construct("reference", region), "character", node.span)


def merge_overrides(base: dict[str, Any], update: dict[str, Any]) -> dict[str, Any]:
    """``|set`` values; ``None`` removes an override (decision 60)."""
    result = dict(base)
    for key, value in update.items():
        if value is None:
            result.pop(key, None)
        else:
            result[key] = value
    return result


def _collect_levels(block: N.ListBlock, kinds: dict[int, str], level: int) -> None:
    for item in block.items:
        kinds.setdefault(level, item.kind)
        for child in item.children:
            if isinstance(child, N.ListBlock):
                _collect_levels(child, kinds, level + 1)


def _has_own_style(block: N.ListBlock) -> bool:
    """A nested ``|list("Name"):`` environment names its own style (decision 33)."""
    command = block.style
    return command is not None and command.args is not None and bool(command.args.positional)


def _set_list_style(block: N.ListBlock, style: str) -> None:
    """The style of a list and of its nested lists without their own style."""
    block.list_style = style
    for item in block.items:
        for child in item.children:
            if isinstance(child, N.ListBlock) and not _has_own_style(child):
                _set_list_style(child, style)


def _style_arg(block: Any) -> str | None:
    """``style="…"`` of a heading or clause (evaluated arguments), or ``None``."""
    args = getattr(block, "args", None)
    value = args.keywords.get("style") if args is not None and hasattr(args, "keywords") else None
    return value if isinstance(value, str) else None
