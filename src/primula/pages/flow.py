"""The pages phase: page changes, breaks, sections, headers, watermarks, frames.

Specification 7, 8; decisions 84-89.  :class:`PagesBuilder` walks the
evaluated tree (after the structure phase) and

* annotates page changes (``|page`` switch and environment, ``|appendix(page=…)``)
  with ``page_change`` (master page, restart) and ``page_restore``;
  creates derived page styles for ``number_format=`` (decision 87);
* checks the rules of 7.3-7.4: a change inside a clause, a table cell or a
  section with columns (P6104); a switch without content after it up to
  the end of the document or environment (P6105); a break inside a group
  kept together (P6106);
* reads ``|section`` parameters (``section_info``, 7.5);
* reads images and builds frames of ``|img``, ``|figure``, ``|frame``
  (``frame``; :mod:`primula.pages.frames`), also inside headers and cells;
* collects headers and footers from styles modules (``header(…)``,
  ``footer(…)``) and from the document (``|header(…):``), resolves them for
  every page style through ``parent`` (7.6, decisions 88-89);
* resolves watermarks per page style: the document command, then the
  ``watermark`` property of the page style, then ``watermark(…)`` of a
  styles module (8.6, decision 84).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from pathlib import Path
from typing import Any

from primula.core.values import Content, Record
from primula.diagnostics import DiagnosticSink, error, warning
from primula.i18n import Key
from primula.pages.frames import frame_info
from primula.pages.images import ImageError, ImageInfo, read_image, svg_from_text
from primula.pages.watermark import Watermark, text_mark, text_svg
from primula.styles.schema import Border, PropertyError, check_property, parse_border
from primula.styles.system import StyleSystem
from primula.syntax import nodes as N

PARTS = ("header", "footer")
WHICH = ("all", "first", "left", "right")
_CONTENT = (N.Paragraph, N.Heading, N.ListBlock, N.Verbatim)


@dataclass
class PageChange:
    """A change of the page style: the master page and the first page number."""

    master: str
    restart: int | None = None


@dataclass
class SectionInfo:
    """A section with columns (7.5)."""

    cols: int
    widths: list[Fraction] | None
    gap: Any
    rule: Border | None
    balance: bool


@dataclass
class MasterInfo:
    """A master page: headers/footers by part and ``which``, and a watermark.

    ``parts[part][which]`` is a list of blocks, ``[]`` for an explicitly
    removed header, missing when not set.
    """

    name: str
    parts: dict[str, dict[str, list[Any]]] = field(default_factory=dict)
    watermark: Watermark | None = None


@dataclass
class Pages:
    """Result of the pages phase."""

    masters: dict[str, MasterInfo]
    images: list[ImageInfo]


@dataclass
class _Context:
    master: str | None
    clause: bool = False
    cell: bool = False
    section: bool = False
    keep: bool = False


class PagesBuilder:
    """See the module description.

    Args:
        system: the style system (page styles, header settings).
        sink: diagnostics receiver.
        default_font: font of the default paragraph style (watermarks).
    """

    def __init__(self, system: StyleSystem, sink: DiagnosticSink, default_font: str) -> None:
        self.system = system
        self.sink = sink
        self.default_font = default_font
        self.pending: list[Any] = []
        self.document_parts: dict[tuple[str, str, str], list[Any]] = {}
        self.document_marks: list[tuple[Any, dict[str, Any], Any, Any]] = []
        self.images: dict[str, ImageInfo] = {}
        self.image_cache: dict[Path, ImageInfo | None] = {}
        #: Watermark text of the --review mode (9.2): replaces every other mark.
        self.review_mark: str | None = None

    # ------------------------------------------------------------------
    # Entry
    # ------------------------------------------------------------------

    def build(self, document: N.Document) -> Pages:
        master = getattr(document, "page_style", None)
        self.default_master = master
        self._blocks(document.children, _Context(master))
        self._unfilled()
        masters = {}
        for name, definition in list(self.system.styles.items()):
            if definition.kind == "page":
                masters[name] = self._master(name)
        for info in masters.values():
            for which_parts in info.parts.values():
                for blocks in which_parts.values():
                    self._blocks(blocks, _Context(info.name))
            self.pending = []
        return Pages(masters, list(self.images.values()))

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _unfilled(self) -> None:
        """P6105 for page switches without content after them."""
        for node in self.pending:
            self.sink.emit(error("P6105", node.span))
        self.pending = []

    def _content(self) -> None:
        self.pending = []

    def _area(self, master: str | None) -> tuple[Fraction, Fraction]:
        """Width and height of the text area of a page style (millimetres)."""
        from primula.odf.styles_xml import page_geometry

        if master and self.system.kind(master) == "page":
            geometry = page_geometry(self.system.effective(master))
        else:
            geometry = page_geometry({})
        return geometry["text_width"], geometry["height"] - geometry["top"] - geometry["bottom"]

    def _page_style(self, name: Any, span: Any) -> str | None:
        if isinstance(name, str) and self.system.kind(name) == "page":
            return name
        self.sink.emit(error("P6103", span, name=str(name)))
        return None

    def _image(self, path: Path | ImageInfo | None, span: Any) -> ImageInfo | None:
        """The image of a frame or watermark: a file read once, or an SVG string already checked (svg=)."""
        if path is None:
            return None
        if isinstance(path, ImageInfo):
            self.images.setdefault(path.package_name, path)
            return path
        if path not in self.image_cache:
            try:
                info = read_image(path)
            except ImageError as exc:
                self.sink.emit(error("P6101", span, path=path.name, reason=Key(f"image.{exc}")))
                info = None
            if info is not None and info.orientation != 1:
                self.sink.emit(warning("P6108", span, path=path.name, orientation=info.orientation))
            self.image_cache[path] = info
        info = self.image_cache[path]
        if info is not None:
            self.images.setdefault(info.package_name, info)
        return info

    # ------------------------------------------------------------------
    # Blocks
    # ------------------------------------------------------------------

    def _blocks(self, blocks: list[Any], ctx: _Context) -> None:
        for block in blocks:
            self._block(block, ctx)

    def _block(self, block: Any, ctx: _Context) -> None:
        if isinstance(block, _CONTENT):
            self._content()
            self._inlines(getattr(block, "body", None) or [], ctx)
            if isinstance(block, N.ListBlock):
                for item in block.items:
                    self._inlines(item.body, ctx)
                    self._blocks(item.children, ctx)
        elif isinstance(block, (N.Clause, N.Admonition, N.StyleBlock)):
            if block.form == "line":
                self._content()
            self._inlines(block.body, ctx)
            inner = _Context(ctx.master, clause=ctx.clause or isinstance(block, N.Clause), cell=ctx.cell,
                             section=ctx.section, keep=ctx.keep)
            self._blocks(block.children, inner)
        elif isinstance(block, N.Command):
            self._command(block, ctx)

    def _command(self, block: N.Command, ctx: _Context) -> None:
        name = block.name
        args = dict(block.args.keywords) if block.args is not None else {}
        if name == "page":
            self._page(block, args, ctx)
        elif name in ("newpage", "newcolumn"):
            if ctx.keep:
                self.sink.emit(error("P6106", block.span, command="|" + name))
        elif name == "section":
            self._section(block, args, ctx)
        elif name in PARTS:
            self._part(block, args)
        elif name == "watermark":
            positional = block.args.positional if block.args is not None else []
            self.document_marks.append((positional[0] if positional else None, args, args.get("pages"), block))
            block.skip_output = True
        elif name == "img":
            self._content()
            self._img(block, args, ctx)
        elif name == "figure":
            self._content()
            block.frame = self._frame("figure", block, args, ctx)
        elif name == "frame":
            block.frame = self._frame("frame", block, args, ctx)
            self._blocks(block.children, _Context(ctx.master, cell=True))
        elif name == "table":
            self._content()
            grid = getattr(block, "table_grid", None)
            inner = _Context(ctx.master, clause=ctx.clause, cell=True, section=ctx.section, keep=ctx.keep)
            for cell in grid.cells() if grid is not None else []:
                if cell.blocks is not None:
                    self._blocks(cell.blocks, inner)
                else:
                    self._inlines(cell.display if cell.display is not None else cell.inlines or [], inner)
        elif name == "appendix":
            self._appendix(block, args, ctx)
        elif name == "document":
            self._document_part(block, args, ctx)
        elif name == "block" and block.form == "env":
            style = getattr(block, "block_style", None)
            keep = bool(style and self.system.effective(style).get("keep_together"))
            self._blocks(block.children, _Context(ctx.master, ctx.clause, ctx.cell, ctx.section, ctx.keep or keep))
        else:
            if block.body or name in ("toc", "list_of"):
                self._content()
            self._inlines(block.body or [], ctx)
            self._blocks(block.children, ctx)

    # --- page changes -----------------------------------------------------------------------

    def _page(self, block: N.Command, args: dict[str, Any], ctx: _Context) -> None:
        """``|page("Style", restart=…, number_format=…)`` switch or environment (7.3, decision 87)."""
        positional = block.args.positional if block.args is not None else []
        style = self._page_style(positional[0] if positional else None, block.span)
        if ctx.clause or ctx.cell or ctx.section:
            where = "clause" if ctx.clause else ("cell" if ctx.cell else "section")
            self.sink.emit(error("P6104", block.span, where=Key(f"where.{where}")))
        if style is None:
            return
        restart = args.get("restart")
        if restart is not None and (isinstance(restart, bool) or not isinstance(restart, int) or restart < 0):
            self.sink.emit(error("P6102", block.span, name="restart", value=str(restart), command="|page"))
            restart = None
        if restart is None:
            own = self.system.effective(style).get("restart")
            restart = own if isinstance(own, int) else None
        fmt = args.get("number_format")
        if fmt is not None:
            try:
                fmt = check_property("page", "number_format", fmt)
            except PropertyError:
                self.sink.emit(error("P6102", block.span, name="number_format", value=str(fmt), command="|page"))
                fmt = None
        if fmt is not None and fmt != self.system.effective(style).get("number_format", "1"):
            style = self.system.register("page", f"{style}-number_format-{fmt}", style, {"number_format": fmt},
                                         block.span)
        block.page_change = PageChange(style, restart)
        if block.form == "env":
            previous = ctx.master
            self.pending = [block]
            self._blocks(block.children, _Context(style, keep=ctx.keep))
            self._unfilled_in(block)
            block.page_restore = previous
        else:
            ctx.master = style
            self.pending = [block]

    def _unfilled_in(self, block: Any) -> None:
        if block in self.pending:
            self.sink.emit(error("P6105", block.span))
        self.pending = []

    def _appendix(self, block: N.Command, args: dict[str, Any], ctx: _Context) -> None:
        """``|appendix(page="Style")``: the annex on its own page style, restored after it."""
        self._content()  # the designation paragraph
        style = args.get("page")
        inner = ctx
        if style is not None:
            master = self._page_style(style, block.span)
            if master is not None:
                block.page_change = PageChange(master)
                block.page_restore = ctx.master
                inner = _Context(master, keep=ctx.keep)
        self._blocks(block.children, inner)

    def _document_part(self, block: N.Command, args: dict[str, Any], ctx: _Context) -> None:
        """A part of a compound document (10.7): always on a new page.

        ``page="Style"`` sets the page style of the part; without it the part
        starts on the default page style of the root document, not on the
        style left by the previous part.  After the part the page style in
        force before it is restored if the part changed it.
        """
        start = self.default_master
        if args.get("page") is not None:
            start = self._page_style(args["page"], block.span) or start
        if start is not None and (start != ctx.master or args.get("page") is not None):
            block.page_change = PageChange(start)
        inner = _Context(start if start is not None else ctx.master, keep=ctx.keep)
        self._blocks(block.children, inner)
        if getattr(block, "page_change", None) is not None or inner.master != start:
            block.page_restore = ctx.master or self.default_master

    # --- sections ----------------------------------------------------------------------------

    def _section(self, block: N.Command, args: dict[str, Any], ctx: _Context) -> None:
        """``|section(cols=…, widths=…, gap=…, rule=…, balance=…):`` (7.5)."""
        def invalid(name: str) -> None:
            self.sink.emit(error("P6102", block.span, name=name, value=str(args.get(name)), command="|section"))

        for name in args:
            if name not in ("cols", "widths", "gap", "rule", "balance", "id", "block"):
                self.sink.emit(error("P4104", block.span, name=name, command="|section"))
        cols = args.get("cols", 1)
        if isinstance(cols, bool) or not isinstance(cols, int) or cols < 1:
            invalid("cols")
            cols = 1
        widths = None
        if args.get("widths") is not None:
            raw = args["widths"]
            try:
                if not isinstance(raw, (list, tuple)) or len(raw) != cols:
                    raise ValueError
                widths = [Fraction(str(w)[:-1]) for w in raw if str(w).endswith("%")]
                if len(widths) != cols:
                    raise ValueError
            except (ValueError, ArithmeticError):
                invalid("widths")
                widths = None
        gap = None
        if args.get("gap") is not None:
            try:
                gap = check_property("page", "col_gap", args["gap"])
            except PropertyError:
                invalid("gap")
        rule = None
        if args.get("rule") is not None:
            try:
                rule = parse_border(args["rule"])
            except PropertyError:
                invalid("rule")
        balance = args.get("balance", True)
        if not isinstance(balance, bool):
            invalid("balance")
            balance = True
        block.section_info = SectionInfo(cols, widths, gap, rule, balance)
        self._blocks(block.children, _Context(ctx.master, ctx.clause, ctx.cell, True, ctx.keep))

    # --- headers and footers --------------------------------------------------------------------

    def _part(self, block: N.Command, args: dict[str, Any]) -> None:
        """``|header("Style", which=…):`` in the document (7.6)."""
        block.skip_output = True
        positional = block.args.positional if block.args is not None else []
        style = self._page_style(positional[0] if positional else None, block.span)
        which = args.get("which", "all")
        if which not in WHICH:
            self.sink.emit(error("P6102", block.span, name="which", value=str(which), command="|" + block.name))
            return
        if style is not None:
            blocks = [b for b in block.children if not isinstance(b, N.BlankLine)]
            self.document_parts[(block.name, style, which)] = blocks

    def _module_part(self, part: str, style: str, which: str) -> list[Any] | None:
        content = (self.system.settings.get(part) or {}).get((style, which))
        if content is None:
            return None
        if isinstance(content, Content):
            return [n for n in content.nodes if not isinstance(n, N.BlankLine)] if content.kind == "blocks" else [
                N.Paragraph(content.nodes[0].span if content.nodes else None, list(content.nodes))]
        return [N.Paragraph(None, [N.Text(None, str(content))])] if content else []

    def _style_part(self, part: str, style: str, which: str) -> list[Any] | None:
        """Blocks of a header or footer of one page style: the document wins over modules."""
        blocks = self.document_parts.get((part, style, which))
        return blocks if blocks is not None else self._module_part(part, style, which)

    def _master(self, name: str) -> MasterInfo:
        """Headers, footers and the watermark of a page style through ``parent`` (7.6)."""
        info = MasterInfo(name)
        chain: list[str] = []
        current: str | None = name
        while current is not None and current not in chain and current in self.system.styles:
            chain.append(current)
            current = self.system.styles[current].parent
        for part in PARTS:
            found: dict[str, list[Any]] = {}
            for which in WHICH:
                for style in chain:
                    blocks = self._style_part(part, style, which)
                    if blocks is not None:
                        found[which] = blocks
                        break
                    if which in ("left", "right") and self._style_part(part, style, "all") is not None:
                        # "all" of a nearer style covers both sides (7.6): the
                        # left/right parts of its parents no longer apply.
                        break
            info.parts[part] = found
        info.watermark = self._watermark(name)
        return info

    # --- watermarks ---------------------------------------------------------------------------

    def _watermark(self, style: str) -> Watermark | None:
        """The watermark of a page style (8.6, decision 84)."""
        candidates: list[tuple[Any, dict[str, Any], Any]] = []
        if self.review_mark:
            candidates.append((self.review_mark, {}, None))
        for mark, options, pages, block in reversed(self.document_marks):
            if pages is None or style in pages:
                candidates.append((mark, options, block.span))
                break
        own = self.system.effective(style).get("watermark")
        if own is not None:
            candidates.append((own, {}, None))
        setting = self.system.settings.get("watermark")
        if isinstance(setting, dict) and (setting.get("pages") is None or style in setting.get("pages")):
            options = {k: v for k, v in setting.items() if k not in ("mark", "pages")}
            candidates.append((setting.get("mark"), options, None))
        if not candidates:
            return None
        mark, options, span = candidates[0]
        area = self._area(style)
        if isinstance(mark, Record) and ("path" in mark.fields or "svg" in mark.fields):
            # img(path) or img(svg=…) (decision 131; the string was checked by img()).
            source = svg_from_text(mark.fields["svg"]) if "svg" in mark.fields else Path(mark.fields["path"])
            image = self._image(source, span)
            if image is None:
                return None
            scale = min(Fraction(1), area[0] / image.width_mm, area[1] / image.height_mm)
            return Watermark(image, image.width_mm * scale, image.height_mm * scale)
        if not isinstance(mark, str) or not mark:
            # One message per mark, not per page style it applies to.
            reported = self.__dict__.setdefault("_bad_marks", set())
            if (id(span), str(mark)) not in reported:
                reported.add((id(span), str(mark)))
                self.sink.emit(error("P6109", span, value=str(mark)))
            return None
        try:
            text = text_mark(mark, options)
        except ValueError as exc:
            self.sink.emit(error("P6102", span, name=str(exc), value=str(options.get(str(exc))), command="watermark"))
            return None
        data = text_svg(text, area, self.default_font)
        image = ImageInfo(Path("watermark.svg"), "svg", data, area[0], area[1])
        self.images.setdefault(image.package_name, image)
        return Watermark(image, area[0], area[1])

    # --- frames ---------------------------------------------------------------------------------

    def _frame(self, command: str, block: Any, args: dict[str, Any], ctx: _Context) -> Any:
        style = args.get("style")
        if isinstance(style, str) and style in self.system.styles:
            # Properties of the frame style are defaults of the arguments (8.5):
            # |img("logo.png", style="LogoSmall") takes the width of LogoSmall.
            own = {key: value for key, value in self.system.effective(style).items() if key != "parent"}
            args = {**own, **args}
        image = None
        if command != "frame":
            image = self._image(getattr(block, "image_path", None), block.span)
            if image is None:
                return None
        return frame_info(command, args, image, self._area(ctx.master), self.sink, block.span)

    def _img(self, block: Any, args: dict[str, Any], ctx: _Context) -> None:
        block.frame = self._frame("img", block, args, ctx)

    def _inlines(self, nodes: list[Any], ctx: _Context) -> None:
        for node in nodes:
            if isinstance(node, N.InlineCommand) and node.name == "img":
                args = dict(node.args.keywords) if node.args is not None else {}
                node.frame = self._frame("img", node, args, ctx)
            body = getattr(node, "body", None)
            if isinstance(body, list):
                self._inlines(body, ctx)
