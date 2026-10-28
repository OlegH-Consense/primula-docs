"""``content.xml``: the body of the document (specification 15, stage 13.5).

Mapping of the evaluated tree:

======================  ==========================================================
Node                    ODF
======================  ==========================================================
paragraph               ``text:p`` with the style of ``style_use`` (11.6)
heading                 ``text:h`` with ``text:outline-level``
clause (line form)      ``text:p``; its region follows as siblings
``|.Name:``, ``|!``     ``text:p`` (line form) or the blocks of the environment
list                    ``text:list`` / ``text:list-item`` (nested lists inside items)
character style span    ``text:span`` (decision 62: also every short form)
``|"{…}``               quotes of the document language (decision 63)
``|\\``                 ``text:line-break``; spaces -> ``text:s``; tab -> ``text:tab``
``|field.page`` …       ``text:page-number``, ``text:page-count``, ``text:title``,
                        ``text:chapter``
``|newpage``            ``fo:break-before="page"`` on the next paragraph or table
table (simple)          ``table:table`` with columns, header rows, cell borders by
                        ``frame``/``rules`` — a preview; full tables at stage 13.7
numbers (13.6)          text before the paragraph text (decision 69)
IDs (13.6)              ``text:bookmark`` at the start of the paragraph
``|@`` (13.6)           ``text:a`` to the bookmark; ``page`` — ``text:bookmark-ref``;
                        notes — ``text:note-ref`` (decision 76)
``|appendix`` (13.6)    designation, subtitle, title paragraphs, then the body
captions (13.6)         a paragraph above or below the table (figure placeholder)
``|footnote`` (13.6)    ``text:note`` with ``text:note-citation`` and ``text:note-body``
``|toc`` (13.6)         ``text:table-of-content`` from ``text:toc-mark`` marks and
                        visible entries; ``|list_of`` — ``text:user-index`` from
                        ``text:user-index-mark`` marks (5.9)
======================  ==========================================================

Automatic styles: a paragraph whose cascade adds properties to the named
parent gets an automatic style ``P<n>``; identical combinations share one
style; the first block carries the default master page (decision 64).

Constructs of later stages are reported with warning P8001 and a visible
placeholder marks where content is missing, so a document never silently
loses text.  Since stage 13.11 every construct is output (``_LATER`` is
empty); the mechanism stays for constructs of later language versions.
"""

from __future__ import annotations

import json
from dataclasses import replace
import re
import xml.etree.ElementTree as ET
from fractions import Fraction
from typing import Any

from primula.core.values import Length, parse_length
from primula.diagnostics import DiagnosticSink, error, warning
from primula.odf import units
from primula.odf.props import Fonts, cell_attrs, paragraph_attrs, text_attrs
from primula.odf.xml import ODF_VERSION, append_text, el, sub
from primula.styles.apply import StyleUse
from primula.styles.schema import Border, PropertyError, check_property
from primula.styles.system import StyleSystem, _canonical, merge_props
from primula.structure.settings import QUOTES
from primula.syntax import nodes as N


#: Commands rendered as their content (their own meaning comes later).
_TRANSPARENT = {"block", "part", "scope", "list", "caption", "generated"}
#: Commands of later stages: (stage, keep content).
_LATER: dict[str, tuple[str, bool]] = {}
#: User index names of the lists of figures and tables (5.9).
INDEX_NAMES = {"figure": "Figures", "table": "Tables", "toc": "Contents"}


def index_name(kind: str) -> str:
    """The user index name of marks of ``kind``: ``Figures``, ``Tables``, or ``Contents-en`` — the
    table of contents and lists of a non-primary track of |parallel (``toc:en``, 7.7)."""
    base, _, track = kind.partition(":")
    return INDEX_NAMES[base] + (f"-{track}" if track else "")
_SPACES = re.compile(r"( {2,}|\t)")


#: Namespace of Writer table formulas (``table:formula="ooow:<A1>+<B1>"``).
OOOW_NAMESPACE = "http://openoffice.org/2004/writer"


class AutoStyles:
    """Automatic styles with deduplication.

    Args:
        fonts: font registry.
        element: the ``office:automatic-styles`` element to fill (a new one
            for ``content.xml``; the one of ``styles.xml`` for headers).
        prefix: prefix of the generated names (``M`` for ``styles.xml``, so
            names never clash with those of ``content.xml``).
    """

    def __init__(self, fonts: Fonts, element: ET.Element | None = None, prefix: str = "") -> None:
        self.fonts = fonts
        self.element = element if element is not None else el("office:automatic-styles")
        self.prefix = prefix
        self._names: dict[str, str] = {}
        self._counters: dict[str, int] = {}

    def _name(self, prefix: str, key: Any) -> tuple[str, bool]:
        prefix = self.prefix + prefix
        text = json.dumps(_canonical(key), sort_keys=True, ensure_ascii=False)
        cached = self._names.get(prefix + text)
        if cached is not None:
            return cached, False
        self._counters[prefix] = self._counters.get(prefix, 0) + 1
        name = f"{prefix}{self._counters[prefix]}"
        self._names[prefix + text] = name
        return name, True

    def paragraph(self, parent: str | None, extra: dict[str, Any], *, master: str | None = None,
                  break_before: Any = False, page_number: int | None = None) -> str | None:
        """Style of a paragraph: the named parent or an automatic ``P<n>``.

        ``break_before``: ``True``/``"page"`` or ``"column"`` (7.4);
        ``master`` and ``page_number``: a page change (7.3, decision 87).
        """
        if not extra and master is None and not break_before and page_number is None:
            return parent
        name, new = self._name("P", [parent, extra, master, break_before, page_number])
        if new:
            style = sub(self.element, "style:style", {"style:name": name, "style:family": "paragraph",
                                                      "style:parent-style-name": parent,
                                                      "style:master-page-name": master})
            attrs = paragraph_attrs(extra)
            if break_before:
                attrs["fo:break-before"] = "column" if break_before == "column" else "page"
            if page_number is not None:
                attrs["style:page-number"] = str(page_number)
            if attrs:
                sub(style, "style:paragraph-properties", attrs)
            text = text_attrs(extra, self.fonts, paragraph=True)
            if text:
                sub(style, "style:text-properties", text)
        return name

    def text(self, props: dict[str, Any]) -> str:
        """Automatic text style ``T<n>`` (direct formatting of ``|fmt``)."""
        name, new = self._name("T", props)
        if new:
            style = sub(self.element, "style:style", {"style:name": name, "style:family": "text"})
            sub(style, "style:text-properties", text_attrs(props, self.fonts))
        return name

    def table(self, width: Length, align: str, *, master: str | None, break_before: Any,
              may_break: bool = True, page_number: int | None = None,
              space_before: Length | None = None, space_after: Length | None = None) -> str:
        """Automatic table style; ``space_before``/``space_after`` — outer margins of the table
        (``fo:margin-top``/``fo:margin-bottom`` of ``style:table-properties``, 11.2)."""
        name, new = self._name("Table", [width, align, master, break_before, may_break, page_number,
                                         space_before, space_after, len(self._names)])
        if new:
            style = sub(self.element, "style:style", {"style:name": name, "style:family": "table",
                                                      "style:master-page-name": master})
            # Collapsing borders: an inner horizontal edge is written on both cells (the bottom of
            # the upper one, the top of the lower one, tables/cascade.py) and must stay one line.
            attrs = {"style:width": units.mm(width), "table:align": {"left": "left", "center": "center",
                                                                      "right": "right"}.get(align, "left"),
                     "table:border-model": "collapsing"}
            if break_before:
                attrs["fo:break-before"] = "column" if break_before == "column" else "page"
            if page_number is not None:
                attrs["style:page-number"] = str(page_number)
            if not may_break:
                attrs["style:may-break-between-rows"] = "false"
            if space_before is not None:
                attrs["fo:margin-top"] = units.mm(space_before)
            if space_after is not None:
                attrs["fo:margin-bottom"] = units.mm(space_after)
            sub(style, "style:table-properties", attrs)
        return name

    def graphic(self, props: dict[str, str], parent: str | None) -> str:
        """Automatic graphic style ``fr<n>`` of a frame (8.5)."""
        name, new = self._name("fr", [props, parent])
        if new:
            style = sub(self.element, "style:style", {"style:name": name, "style:family": "graphic",
                                                      "style:parent-style-name": parent})
            sub(style, "style:graphic-properties", dict(props))
        return name

    def section(self, info: Any) -> str:
        """Automatic section style ``Sect<n>`` with columns (7.5)."""
        name, new = self._name("Sect", [info.cols, info.widths, info.gap, info.rule, info.balance])
        if new:
            style = sub(self.element, "style:style", {"style:name": name, "style:family": "section"})
            props = sub(style, "style:section-properties", {
                "text:dont-balance-text-columns": "false" if info.balance else "true"})
            columns_element(props, info.cols, info.gap, info.rule, info.widths)
        return name

    def row(self, height: Length | None, min_height: Length | None, keep: bool) -> str | None:
        """Row style (6.6): exact or minimum height, no break inside the row."""
        if height is None and min_height is None and not keep:
            return None
        name, new = self._name("Row", [height, min_height, keep])
        if new:
            style = sub(self.element, "style:style", {"style:name": name, "style:family": "table-row"})
            sub(style, "style:table-row-properties", {
                "style:row-height": units.mm(height) if height is not None else None,
                "style:min-row-height": units.mm(min_height) if min_height is not None and height is None else None,
                "fo:keep-together": "always" if keep else None})
        return name

    def column(self, table: str, index: int, width: Length) -> str:
        name = f"{table}.C{index}"
        style = sub(self.element, "style:style", {"style:name": name, "style:family": "table-column"})
        sub(style, "style:table-column-properties", {"style:column-width": units.mm(width)})
        return name

    def cell(self, props: dict[str, Any], data_style: str | None = None) -> str:
        """Cell style ``Cell<n>``; ``data_style`` — number format of the value (live tables)."""
        name, new = self._name("Cell", [props, data_style])
        if new:
            style = sub(self.element, "style:style", {"style:name": name, "style:family": "table-cell",
                                                      "style:data-style-name": data_style})
            sub(style, "style:table-cell-properties", cell_attrs(props))
        return name

    def number(self, places: int, symbol: str | None, language: str | None) -> str:
        """Number format ``N<n>`` of a value cell (6.8): groups, places, symbol.

        Writer shows recomputed formulas (``live=True``) by this format; the
        group and decimal separators come from the language of the format,
        as in the text the translator writes (decision 78).
        """
        name, new = self._name("N", [places, symbol, language])
        if new:
            code, _, country = (language or "").partition("-")
            style = sub(self.element, "number:number-style", {
                "style:name": name, "number:language": code or None, "number:country": country or None})
            sub(style, "number:number", {"number:decimal-places": places, "number:min-decimal-places": places,
                                         "number:min-integer-digits": 1, "number:grouping": "true"})
            if symbol:
                sub(style, "number:text", text="\u00a0" + symbol)
        return name


class ContentWriter:
    """Writes the body of an evaluated, styled document.

    Args:
        system: the style system.
        fonts: font registry shared with ``styles.xml``.
        language: document language tag (decision 65).
        sink: receiver of P8xxx warnings.
        page_style: default page style (decision 64).
        text_width: width of the text area in millimetres (table widths).
        stage: prototype stage for warnings.
    """

    def __init__(self, system: StyleSystem, fonts: Fonts, language: str | None, sink: DiagnosticSink,
                 page_style: str | None, text_width: Fraction, stage: str, auto: AutoStyles | None = None) -> None:
        self.system = system
        self.fonts = fonts
        self.sink = sink
        self.auto = auto if auto is not None else AutoStyles(fonts)
        self.page_style = page_style
        self.text_width = text_width
        self.stage = stage
        self.language = language
        #: ``id()`` of elements whose text the typography pass leaves as
        #: written: verbatim paragraphs and ``|`{…}`` spans (library 7).
        self.raw: set[int] = set()
        code = (language or "uk").split("-")[0].lower()
        quotes = dict(QUOTES)
        for lang, pairs in (system.settings.get("quotes") or {}).items():
            quotes[lang] = (tuple(pairs[0]), tuple(pairs[1]))  # type: ignore[assignment]
        self._all_quotes = quotes
        self.quotes = quotes.get(code, quotes["uk"])
        #: The language of the text being written when it differs from the
        #: document: a track block of |parallel (7.7) — ``fo:language`` of its
        #: paragraphs, its quotes and short words.
        self.text_language: str | None = None
        #: ``id()`` of table cells written in a track language -> the tag (typography pass).
        self.languages: dict[int, str] = {}
        self.first_block = True
        self.pending_break: Any = False  # True (page) or "column"
        self.pending_master: str | None = page_style
        self.pending_page_number: int | None = None
        self.tables = 0
        self.frames = 0
        self.sections = 0
        # Frames anchored to the next paragraph (floating images, |frame, 8.1).
        self.pending_frames: list[Any] = []
        self._last_space = False
        self._warned: set[str] = set()
        # Numbers, bookmarks and index marks waiting for the next paragraph
        # (the first paragraph of a clause environment, the first cell of
        # a table without a caption).
        self.pending: list[Any] = []

    # ------------------------------------------------------------------

    def build(self, document: N.Document) -> ET.Element:
        """Build the ``office:document-content`` element."""
        root = el("office:document-content", {"office:version": ODF_VERSION})
        # Writer formulas (live=True, 6.8) are "ooow:…" attribute values; the
        # prefix is resolved through the namespace declarations of the part,
        # and ElementTree declares only prefixes used in names.
        root.set("xmlns:ooow", OOOW_NAMESPACE)
        sub(root, "office:font-face-decls")
        root.append(self.auto.element)
        body = sub(sub(root, "office:body"), "office:text")
        self._blocks(body, document.children)
        if self.first_block or self.pending_frames:
            # An empty document still needs a paragraph for the master page;
            # frames waiting for a paragraph get a host paragraph at the end.
            p = sub(body, "text:p", {"text:style-name": self._paragraph_style(None)})
            self._lead(p)
        return root

    def write_blocks(self, parent: ET.Element, blocks: list[Any]) -> None:
        """Write blocks into ``parent`` (header and footer content, 7.6)."""
        self.first_block = False
        self.pending_master = None
        self._blocks(parent, blocks)
        if self.pending_frames:
            self._lead(sub(parent, "text:p", {"text:style-name": self._paragraph_style(None)}))

    def _warn(self, node: Any, construct: str, stage: str) -> None:
        self.sink.emit(warning("P8001", node.span, construct=construct, stage=stage))

    def _paragraph_style(self, use: Any, extra: dict[str, Any] | None = None) -> str | None:
        parent = use.parent if use is not None else None
        props = dict(use.extra) if use is not None else {}
        if extra:
            props = merge_props(props, extra)
        if self.text_language is not None:
            props = merge_props(props, {"language": self.text_language})
        master, number = self._take_page()
        name = self.auto.paragraph(parent, props, master=master, break_before=self.pending_break,
                                   page_number=number)
        self.first_block = False
        self.pending_break = False
        return name

    def _take_page(self) -> tuple[str | None, int | None]:
        """The pending page change for the next paragraph or table (7.3)."""
        master, number = self.pending_master, self.pending_page_number
        self.pending_master = self.pending_page_number = None
        return master, number

    # ------------------------------------------------------------------
    # Blocks
    # ------------------------------------------------------------------

    def _blocks(self, parent: ET.Element, blocks: list[Any]) -> None:
        for block in blocks:
            self._block(parent, block)

    def _paragraph(self, parent: ET.Element, node: Any, inlines: list[Any], tag: str = "text:p",
                   attrs: dict[str, Any] | None = None, info: Any = None, label: str | None = None) -> ET.Element:
        p = sub(parent, tag, {**(attrs or {}), "text:style-name": self._paragraph_style(getattr(node, "style_use", None))})
        self._last_space = True
        self._lead(p, info)
        if label is not None:
            # A list number written as text (letters=, П1), then the list tab.
            append_text(p, label)
            sub(p, "text:tab")
        self._inlines(p, inlines, 0)
        return p

    def _letter_labels(self, block: N.ListBlock, info: Any) -> list[str] | None:
        """Labels «а)», «б)», «д)»… of a list level numbered by letters as text (П1).

        The letters come from :func:`~primula.odf.styles_xml.level_letters`;
        numbering starts at ``start`` (of the level or of ``|#(start=…)``).
        A list longer than the letters is P3122.
        """
        from primula.odf.styles_xml import level_letters

        style = getattr(block, "list_style", None)
        if not style or not block.items:
            return None
        level = block.items[0].level
        props = (self.system.effective(style).get("levels") or {}).get(level) or {}
        letters = level_letters(props, self.system.settings.get("profile"), self.language)
        if not letters:
            return None
        first = (info.start if info is not None and info.start else None) or props.get("start") or 1
        labels = []
        for index, item in enumerate(block.items):
            number = int(first) + index
            if number > len(letters):
                self.sink.emit(error("P3122", item.span, number=number, count=len(letters), letters=letters))
                number = len(letters)
            labels.append(f"{props.get('prefix') or ''}{letters[number - 1]}{props.get('suffix', '.')}")
        return labels

    def _lead(self, p: ET.Element, info: Any = None) -> None:
        """Bookmarks, index marks and numbers at the start of a paragraph (13.6).

        Pending items (an enclosing clause environment, a table without a
        caption) come first, then ``info`` of the paragraph itself.
        """
        items = [*self.pending, info] if info is not None else list(self.pending)
        self.pending = []
        frames, self.pending_frames = self.pending_frames, []
        for frame in frames:
            self._frame(p, *frame)
        for item in items:
            if item is None:
                continue
            if getattr(item, "bookmark", None):
                sub(p, "text:bookmark", {"text:name": item.bookmark})
            for mark in getattr(item, "marks", None) or []:
                self._mark(p, mark)
            if getattr(item, "prefix", None):
                style = getattr(item, "prefix_style", None)
                # The number in its own character style (structure_styles(clause_number=…), decision 120).
                self._text(sub(p, "text:span", {"text:style-name": style}) if style else p, item.prefix)

    def _mark(self, p: ET.Element, mark: Any) -> None:
        """An index mark: ``text:toc-mark``, ``text:user-index-mark`` (5.9) or alphabetical (9.5)."""
        if isinstance(mark, _AlphaMark):
            _alpha_mark(p, mark.term, mark.subterm)
        elif mark.index == "toc":
            sub(p, "text:toc-mark", {"text:string-value": mark.text, "text:outline-level": mark.level})
        else:
            sub(p, "text:user-index-mark", {"text:string-value": mark.text, "text:outline-level": mark.level,
                                            "text:index-name": index_name(mark.index)})

    def _styled_paragraph(self, parent: ET.Element, style: str | None, outline: int | None = None) -> ET.Element:
        """A paragraph with a named style of a structure construct; ``outline`` makes it a heading
        of the document outline (``text:h``: Writer navigator, PDF bookmarks; decision 122)."""
        attrs = {"text:style-name": self._paragraph_style(StyleUse(style) if style else None)}
        if outline is not None:
            attrs["text:outline-level"] = outline
        p = sub(parent, "text:h" if outline is not None else "text:p", attrs)
        self._last_space = True
        return p

    def _block(self, parent: ET.Element, block: Any) -> None:
        if isinstance(block, N.Paragraph):
            self._paragraph(parent, block, block.body)
        elif isinstance(block, N.Heading):
            if getattr(block, "outline", True):
                self._paragraph(parent, block, block.body, "text:h", {"text:outline-level": block.level},
                                info=getattr(block, "struct", None))
            else:
                # A heading of a non-primary track of |parallel (7.7, decision 134): the
                # heading style without an outline level — not in the navigator and PDF bookmarks.
                self._paragraph(parent, block, block.body, info=getattr(block, "struct", None))
        elif isinstance(block, (N.Clause, N.Admonition, N.StyleBlock)):
            if getattr(block, "struct", None) is not None:
                self.pending.append(block.struct)
            if block.form == "line":
                self._paragraph(parent, block, block.body)
            self._blocks(parent, block.children)
        elif isinstance(block, N.ListBlock):
            self._list(parent, block, top=True)
        elif isinstance(block, N.Verbatim):
            p = sub(parent, "text:p", {"text:style-name": self._paragraph_style(getattr(block, "style_use", None))})
            self.raw.add(id(p))
            for index, line in enumerate(block.text.split("\n")):
                if index:
                    sub(p, "text:line-break")
                self._last_space = True
                self._text(p, line)
        elif isinstance(block, N.Command):
            self._command(parent, block)

    def _command(self, parent: ET.Element, block: N.Command) -> None:
        name = block.name
        if getattr(block, "skip_output", False):
            return  # |header, |footer, |watermark: written with the master pages (7.6, 8.6)
        if name == "newpage":
            self.pending_break = True
            return
        if name == "newcolumn":
            self.pending_break = "column"
            return
        if name == "page":
            self._page(parent, block)
            return
        if name == "section" and getattr(block, "section_info", None) is not None:
            self._section(parent, block)
            return
        if name == "img":
            self._block_image(parent, block)
            return
        if name == "frame" and block.form == "env":
            frame = getattr(block, "frame", None)
            if frame is not None:
                self.pending_frames.append((frame, block, None))
            return
        if name == "set" or (name == "list" and block.form == "bare"):
            return
        if name == "abbr":
            # |abbr(…) on its own line (9.4): usually a definition with show=False.
            text = getattr(block, "abbr_text", "")
            if text:
                self._text(self._styled_paragraph(parent, None), text)
            return
        if name == "index":
            mark = getattr(block, "alpha_mark", None)
            if mark is not None:
                self.pending.append(_Lead(None, [_AlphaMark(*mark)]))
            return
        if name == "toc_entry":
            # |toc_entry("…"): bookmark and mark at the start of the next paragraph (decision 122).
            if getattr(block, "struct", None) is not None:
                self.pending.append(block.struct)
            return
        if name == "table":
            self._table(parent, block)
            return
        if name == "appendix":
            self._appendix(parent, block)
            return
        if name == "document":
            self._document_part(parent, block)
            return
        if name == "figure":
            self._figure(parent, block)
            return
        if getattr(block, "index_info", None) is not None:
            self._index(parent, block)
            return
        if name == "section" and getattr(block, "struct", None) is not None:
            self.pending.append(block.struct)
        if name in _TRANSPARENT:
            self._blocks(parent, block.children)
            return
        stage, keep = _LATER.get(name, (None, False))
        if stage is not None:
            self._warn(block, "|" + name, stage)
            if keep:
                self._blocks(parent, block.children)
            elif name not in ("header", "footer", "watermark"):
                p = sub(parent, "text:p", {"text:style-name": self._paragraph_style(None)})
                append_text(p, f"[|{name} — {stage}]")
            return
        if block.body:
            self._paragraph(parent, block, block.body)
        self._blocks(parent, block.children)

    # ------------------------------------------------------------------
    # Structure constructs (stage 13.6)
    # ------------------------------------------------------------------

    def _appendix(self, parent: ET.Element, block: N.Command) -> None:
        """``|appendix``: designation, subtitle, title, then the body (5.5, decision 71)."""
        info = getattr(block, "appendix_info", None)
        styles = getattr(block, "appendix_styles", None) or {}
        if info is None:
            self._blocks(parent, block.children)
            return
        if info.page_break:
            self.pending_break = True
        change = getattr(block, "page_change", None)
        if change is not None:
            self.pending_master, self.pending_page_number = change.master, change.restart
        if info.combined is not None:
            # appendices(title_format=…): one title paragraph, then the subtitle (decision 120).
            p = self._styled_paragraph(parent, styles.get("title"), info.outline)
            self._lead(p, _Lead(info.bookmark, info.marks))
            self._text(p, info.combined)
            if info.subtitle:
                self._text(self._styled_paragraph(parent, styles.get("subtitle")), info.subtitle)
        else:
            # The designation is the heading of the appendix in the outline (PDF bookmarks).
            p = self._styled_paragraph(parent, styles.get("designation"), info.outline)
            self._lead(p, _Lead(info.bookmark, info.marks))
            self._text(p, info.designation)
            for text, part in ((info.subtitle, "subtitle"), (info.title, "title")):
                if text:
                    self._text(self._styled_paragraph(parent, styles.get(part)), text)
        self._blocks(parent, block.children)
        if change is not None and getattr(block, "page_restore", None):
            self.pending_master = block.page_restore

    def _document_part(self, parent: ET.Element, block: N.Command) -> None:
        """A part of a compound document (10.7): a page break, its page style, its blocks."""
        self.pending_break = True
        change = getattr(block, "page_change", None)
        if change is not None:
            self.pending_master, self.pending_page_number = change.master, change.restart
        self._blocks(parent, block.children)
        if getattr(block, "page_restore", None):
            self.pending_master, self.pending_page_number = block.page_restore, None

    def _caption(self, parent: ET.Element, block: N.Command) -> None:
        """Caption paragraph «Таблиця 1 — Назва» (5.8)."""
        info = block.caption_info
        p = self._styled_paragraph(parent, getattr(block, "caption_style", None))
        self._lead(p, _Lead(info.bookmark, info.marks))
        if info.before:
            self._text(p, info.before)
        self._inlines(p, info.title, 0)
        if info.after:
            self._text(p, info.after)

    def _figure(self, parent: ET.Element, block: N.Command) -> None:
        """``|figure`` (8.3): image paragraph and caption, or a frame with both.

        By default (centred, no wrapping) the figure is a paragraph with the
        image as a character and the caption paragraph after it (the
        ``Figure`` style keeps them together).  With ``place``/``wrap`` the
        figure is a floating frame whose text box holds both paragraphs.
        """
        info = getattr(block, "caption_info", None)
        frame = getattr(block, "frame", None)
        if frame is None:
            p = sub(parent, "text:p", {"text:style-name": self._paragraph_style(None)})
            append_text(p, "[|figure]")  # an image error was reported
            if info is not None:
                self._caption(parent, block)
            return
        inline = replace(frame, anchor="as-char", props={"style:vertical-pos": "top", "style:vertical-rel": "baseline",
                                                         **{k: v for k, v in frame.props.items()
                                                            if k.startswith(("fo:clip", "style:mirror", "draw:image"))}})
        floating = frame.props.get("style:horizontal-pos") not in (None, "center") or \
            frame.props.get("style:wrap", "none") != "none" or frame.x is not None or frame.y is not None
        image_style = getattr(block, "image_style", None)
        if not floating:
            if info is not None and info.position == "above":
                self._caption(parent, block)
            p = self._styled_paragraph(parent, image_style)
            self._lead(p)
            self._frame(p, inline, block, None)
            if info is not None and info.position != "above":
                self._caption(parent, block)
            return
        self.pending_frames.append((replace(frame, kind="text", image=None, height=None), block, (inline, info)))

    # ------------------------------------------------------------------
    # Pages, sections, frames (stage 13.8)
    # ------------------------------------------------------------------

    def _page(self, parent: ET.Element, block: N.Command) -> None:
        """``|page`` switch or environment (7.3): the master page goes to the next paragraph or table."""
        change = getattr(block, "page_change", None)
        if change is None:
            self._blocks(parent, block.children)
            return
        self.pending_master, self.pending_page_number = change.master, change.restart
        if block.form == "env":
            self._blocks(parent, block.children)
            if getattr(block, "page_restore", None):
                self.pending_master, self.pending_page_number = block.page_restore, None

    def _section(self, parent: ET.Element, block: N.Command) -> None:
        """``|section(cols=…)`` -> ``text:section`` with a columns style (7.5)."""
        self.sections += 1
        if getattr(block, "struct", None) is not None:
            self.pending.append(block.struct)
        section = sub(parent, "text:section", {"text:style-name": self.auto.section(block.section_info),
                                               "text:name": f"Section{self.sections}"})
        self._blocks(section, block.children)
        if not len(section):
            sub(section, "text:p", {"text:style-name": self._paragraph_style(None)})

    def _block_image(self, parent: ET.Element, block: N.Command) -> None:
        """A block ``|img``: inline -> its own paragraph; floating -> anchored to the next paragraph (8.2)."""
        frame = getattr(block, "frame", None)
        if frame is None:
            p = sub(parent, "text:p", {"text:style-name": self._paragraph_style(None)})
            append_text(p, "[|img]")
            return
        if frame.anchor == "as-char":
            p = sub(parent, "text:p", {"text:style-name": self._paragraph_style(getattr(block, "style_use", None))})
            self._lead(p)
            self._frame(p, frame, block, None)
        else:
            self.pending_frames.append((frame, block, None))

    def _frame(self, parent: ET.Element, frame: Any, node: Any, figure: Any) -> None:
        """A ``draw:frame``: an image, a text box (``|frame``) or a figure box.

        Args:
            parent: the paragraph that anchors the frame.
            frame: :class:`~primula.pages.frames.FrameInfo`.
            node: the command (children of ``|frame``).
            figure: ``(inner image frame, caption info)`` of a floating figure.
        """
        self.frames += 1
        props = dict(frame.props)
        if frame.image is None:
            # A text box: transparent, without a border unless given.  Writer
            # frame properties only: draw:fill/draw:stroke would make Writer
            # import the frame as a drawing shape, which cannot hold images.
            props.setdefault("fo:background-color", "transparent")
            props.setdefault("fo:border", "none")
            props.setdefault("fo:padding", "0mm")
        # Writer recognises its frames and images by the parent graphic style
        # ("Frame", "Graphics"); without it they are imported as drawing
        # shapes, and images inside a text box are not shown.
        graphic_parent = frame.style if frame.style and self.system.kind(frame.style) == "frame" else (
            "Graphics" if frame.image is not None else "Frame")
        style = self.auto.graphic(props, graphic_parent)
        attrs: dict[str, Any] = {
            "draw:style-name": style,
            "draw:name": f"{'Image' if frame.image is not None else 'Frame'}{self.frames}",
            "text:anchor-type": frame.anchor, "svg:x": units.mm(units.from_mm(frame.x)) if frame.x is not None else None,
            "svg:y": units.mm(units.from_mm(frame.y)) if frame.y is not None else None,
            "svg:width": units.mm(units.from_mm(frame.width)) if frame.width is not None else None,
            "style:rel-width": frame.rel_width,
            "draw:z-index": self.frames,
        }
        if frame.image is not None and frame.height is not None:
            attrs["svg:height"] = units.mm(units.from_mm(frame.height))
        if frame.anchor == "page":
            attrs["text:anchor-page-number"] = 1
        element = sub(parent, "draw:frame", attrs)
        if frame.image is not None:
            sub(element, "draw:image", {"xlink:href": frame.image.package_name, "xlink:type": "simple",
                                        "xlink:show": "embed", "xlink:actuate": "onLoad",
                                        "draw:mime-type": frame.image.media_type})
        else:
            box = sub(element, "draw:text-box", {"fo:min-height": "5mm"})
            saved = (self.pending, self.pending_frames, self._last_space)
            self.pending, self.pending_frames = [], []
            if figure is not None:
                inner, info = figure
                if info is not None and info.position == "above":
                    self._caption(box, node)
                p = self._styled_paragraph(box, getattr(node, "image_style", None))
                self._frame(p, inner, node, None)
                if info is not None and info.position != "above":
                    self._caption(box, node)
            else:
                self._blocks(box, [b for b in node.children if not isinstance(b, N.BlankLine)])
                if not len(box):
                    sub(box, "text:p")
            self.pending, self.pending_frames, self._last_space = saved
        if frame.alt:
            sub(element, "svg:title", None, frame.alt)

    def _index(self, parent: ET.Element, block: N.Command) -> None:
        """``|toc`` / ``|list_of``: an updatable Writer index with visible entries (5.9)."""
        info = block.index_info
        styles = getattr(block, "index_styles", None) or {}
        title_style = styles.get("title")
        if info.kind == "toc" and getattr(info, "track", None) is None:
            index = sub(parent, "text:table-of-content", {"text:name": info.name, "text:protected": "true"})
            source = sub(index, "text:table-of-content-source", {
                "text:outline-level": info.max_level, "text:use-outline-level": "false",
                "text:use-index-marks": "true", "text:use-index-source-styles": "false"})
            sub(source, "text:index-title-template", {"text:style-name": title_style}, info.title or None)
            for level in range(1, info.max_level + 1):
                self._entry_template(source, "text:table-of-content-entry-template", level,
                                     styles.get(level) or styles.get(max((k for k in styles if isinstance(k, int)),
                                                                         default=0)))
        elif info.kind == "index":
            # The alphabetical index (9.5): Writer sorts and fills page numbers.
            index = sub(parent, "text:alphabetical-index", {"text:name": info.name, "text:protected": "true"})
            code, _, country = (self.language or "").partition("-")
            source = sub(index, "text:alphabetical-index-source", {
                "text:ignore-case": "true", "text:combine-entries": "true", "text:alphabetical-separators": "false",
                "fo:language": code or None, "fo:country": country or None})
            sub(source, "text:index-title-template", {"text:style-name": title_style}, info.title or None)
            for level in (1, 2):
                template = sub(source, "text:alphabetical-index-entry-template",
                               {"text:outline-level": level, "text:style-name": self._index_level_style(styles, level)})
                sub(template, "text:index-entry-text")
                sub(template, "text:index-entry-tab-stop", {"style:type": "right", "style:leader-char": "."})
                sub(template, "text:index-entry-page-number")
        else:
            # Lists of figures and tables; the table of contents and the lists of a
            # non-primary track of |parallel (7.7) by the marks of the track.
            track = getattr(info, "track", None)
            index = sub(parent, "text:user-index", {"text:name": info.name, "text:protected": "true"})
            source = sub(index, "text:user-index-source", {
                "text:index-name": index_name(f"{info.kind}:{track}" if track else info.kind),
                "text:use-index-marks": "true"})
            sub(source, "text:index-title-template", {"text:style-name": title_style}, info.title or None)
            if info.kind == "toc":
                for level in range(1, info.max_level + 1):
                    self._entry_template(source, "text:user-index-entry-template", level,
                                         styles.get(level) or styles.get(max((k for k in styles if isinstance(k, int)),
                                                                             default=0)))
            else:
                self._entry_template(source, "text:user-index-entry-template", 1, styles.get("entry"))
        body = sub(index, "text:index-body")
        if info.page_break:
            self.pending_break = True
        if info.title:
            title = sub(body, "text:index-title", {"text:name": info.name + "_Head"})
            self._text(self._styled_paragraph(title, title_style), info.title)
        for entry in info.entries:
            if info.kind == "toc":
                style = styles.get(entry.level)
            elif info.kind == "index":
                style = self._index_level_style(styles, entry.level)
            else:
                style = styles.get("entry")
            p = self._styled_paragraph(body, style or title_style)
            target = sub(p, "text:a", {"xlink:type": "simple", "xlink:href": "#" + entry.bookmark}) \
                if entry.bookmark else p
            self._text(target, entry.text)
        if not info.title and not info.entries:
            self._styled_paragraph(body, title_style)

    def _index_level_style(self, styles: dict[Any, Any], level: int) -> str | None:
        """Style of a level of the alphabetical index: ``IndexEntry2`` for subterms when defined."""
        if level == 2 and "IndexEntry2" in self.system.styles:
            return "IndexEntry2"
        return styles.get("entry")

    @staticmethod
    def _entry_template(source: ET.Element, tag: str, level: int, style: str | None) -> None:
        template = sub(source, tag, {"text:outline-level": level, "text:style-name": style})
        sub(template, "text:index-entry-link-start")
        sub(template, "text:index-entry-text")
        sub(template, "text:index-entry-tab-stop", {"style:type": "right", "style:leader-char": "."})
        sub(template, "text:index-entry-page-number")
        sub(template, "text:index-entry-link-end")

    def _list(self, parent: ET.Element, block: N.ListBlock, *, top: bool) -> None:
        own = top or getattr(block, "list_style", None) != getattr(self, "_list_style", None)
        attrs = {"text:style-name": getattr(block, "list_style", None)} if own else {}
        info = getattr(block, "list_info", None)
        if info is not None:
            attrs.update({"xml:id": info.xml_id, "text:continue-list": info.continue_list})
        previous = getattr(self, "_list_style", None)
        self._list_style = getattr(block, "list_style", None)
        listing = sub(parent, "text:list", attrs)
        labels = self._letter_labels(block, info)
        for index, item in enumerate(block.items):
            start = info.start if info is not None and index == 0 else None
            element = sub(listing, "text:list-item", {"text:start-value": start})
            self._paragraph(element, item, item.body, info=getattr(item, "struct", None),
                            label=labels[index] if labels else None)
            for child in item.children:
                if isinstance(child, N.ListBlock):
                    self._list(element, child, top=False)
                elif isinstance(child, (N.Paragraph, N.Heading)) or (
                        isinstance(child, (N.Clause, N.StyleBlock, N.Admonition)) and child.form == "line"):
                    self._block(element, child)
                else:
                    self.sink.emit(warning("P8006", child.span))
        self._list_style = previous

    # ------------------------------------------------------------------
    # Simple tables (preview of stage 13.7)
    # ------------------------------------------------------------------

    def _table(self, parent: ET.Element, block: N.Command) -> None:
        caption = getattr(block, "caption_info", None)
        if caption is not None and caption.position == "above":
            self._caption(parent, block)
        elif getattr(block, "struct", None) is not None:
            self.pending.append(block.struct)
        grid = getattr(block, "table_grid", None)
        if grid is not None and grid.rows:
            self._table_body(parent, block, grid)
        if caption is not None and caption.position != "above":
            self._caption(parent, block)

    def _table_body(self, parent: ET.Element, block: N.Command, grid: Any) -> None:
        """A table from its grid (6.2-6.8): widths, spans, row and cell styles, values."""
        props = self.system.effective(block.table_style) if getattr(block, "table_style", None) else {}
        args = block.args
        self.tables += 1
        width = units.from_mm(grid.width or self.text_width)
        master, number = self._take_page()
        style = self.auto.table(width, str(_arg(args, "align") or props.get("align") or "left"),
                                master=master, break_before=self.pending_break,
                                may_break=_flag(args, props, "may_break"), page_number=number,
                                space_before=props.get("space_before"), space_after=props.get("space_after"))
        self.first_block = False
        self.pending_break = False
        table = sub(parent, "table:table", {"table:name": f"Table{self.tables}", "table:style-name": style})
        for index, column_width in enumerate(grid.widths, 1):
            sub(table, "table:table-column",
                {"table:style-name": self.auto.column(style, index, units.from_mm(column_width))})
        keep_rows = _flag(args, props, "keep_rows")
        container = table
        if grid.header and _flag(args, props, "repeat_header"):
            container = sub(table, "table:table-header-rows")
        for row in grid.rows:
            if row.index == grid.header and container is not table:
                container = table
            self._grid_row(container, grid, row, keep_rows)

    def _grid_row(self, parent: ET.Element, grid: Any, row: Any, keep_rows: bool) -> None:
        keep = row.args.get("keep", keep_rows)
        height, min_height = _length(row.args.get("height")), _length(row.args.get("min_height"))
        element = sub(parent, "table:table-row", {"table:style-name": self.auto.row(height, min_height, bool(keep))})
        for column in range(grid.count):
            owner = grid.owners.get((row.index, column))
            if owner is None:
                sub(element, "table:table-cell")
            elif (owner.row, owner.col) != (row.index, column):
                sub(element, "table:covered-table-cell")
            else:
                self._grid_cell(element, owner)

    def _grid_cell(self, parent: ET.Element, cell: Any) -> None:
        """A cell: spans, cell style, ODF value, formula, content (6.4-6.8)."""
        data_style = None
        if cell.number_format is not None:
            data_style = self.auto.number(*cell.number_format, self.language)
        attrs: dict[str, Any] = {"table:style-name": self.auto.cell(_cell_style_props(cell.props), data_style)}
        if cell.span > 1:
            attrs["table:number-columns-spanned"] = cell.span
        if cell.rows > 1:
            attrs["table:number-rows-spanned"] = cell.rows
        if cell.live_formula:
            attrs["table:formula"] = cell.live_formula
        attrs["office:value-type"] = cell.value_type
        value = cell.typed
        if cell.value_type in ("float", "currency"):
            attrs["office:value"] = _number(value)
            if cell.currency:
                attrs["office:currency"] = cell.currency
        elif cell.value_type == "date":
            attrs["office:date-value"] = value.iso()  # DateTime: date or date-time (ODF 1.3)
        element = sub(parent, "table:table-cell", attrs)
        if cell.inlines is not None:
            use = cell.style_use
            extra = merge_props(dict(use.extra) if use is not None else {}, cell.text_props)
            p = sub(element, "text:p", {"text:style-name": self.auto.paragraph(use.parent if use else None, extra)})
            self._last_space = True
            self._lead(p)
            self._inlines(p, cell.display if cell.display is not None else cell.inlines, 0)
        else:
            blocks = [b for b in cell.blocks or [] if not isinstance(b, N.BlankLine)]
            language = getattr(cell.node, "track_language", None)
            saved = self.text_language, self.quotes
            if language is not None:
                # A track block of |parallel (7.7): spelling, hyphenation and quotes of its language.
                code = language.split("-")[0].lower()
                self.text_language, self.quotes = language, self._all_quotes.get(code, self.quotes)
                self.languages[id(element)] = language
            try:
                self._blocks(element, blocks)
                if not len(element):
                    sub(element, "text:p", {"text:style-name": self._paragraph_style(None)})
            finally:
                self.text_language, self.quotes = saved

    # ------------------------------------------------------------------
    # Inline
    # ------------------------------------------------------------------

    def _text(self, parent: ET.Element, text: str) -> None:
        """Text with ODF whitespace rules: repeated spaces -> ``text:s``, tabs -> ``text:tab``."""
        for part in _SPACES.split(text):
            if not part:
                continue
            if part == "\t":
                sub(parent, "text:tab")
                self._last_space = False
            elif part.startswith("  "):
                if self._last_space:
                    sub(parent, "text:s", {"text:c": len(part)})
                else:
                    append_text(parent, " ")
                    sub(parent, "text:s", {"text:c": len(part) - 1} if len(part) > 2 else {})
                self._last_space = True
            else:
                if part.startswith(" ") and self._last_space:
                    sub(parent, "text:s")
                    part = part[1:]
                append_text(parent, part)
                self._last_space = part.endswith(" ")

    def _inlines(self, parent: ET.Element, nodes: list[Any], depth: int) -> None:
        for node in nodes:
            if isinstance(node, N.Text):
                self._text(parent, node.value)
            elif isinstance(node, N.LineBreak):
                sub(parent, "text:line-break")
                self._last_space = True
            elif isinstance(node, N.Short) and node.mark == '"':
                opening, closing = self.quotes[depth % 2]
                append_text(parent, opening)
                self._last_space = False
                self._inlines(parent, node.body, depth + 1)
                append_text(parent, closing)
                self._last_space = False
            elif isinstance(node, (N.Short, N.StyleSpan)):
                style = getattr(node, "char_style", None)
                code = isinstance(node, N.Short) and node.mark == "`"
                target = sub(parent, "text:span", {"text:style-name": style}) if style or code else parent
                if code:
                    self.raw.add(id(target))  # monospace code keeps its spaces (library 7)
                self._inlines(target, node.body, depth)
            elif isinstance(node, N.InlineCommand):
                self._inline_command(parent, node, depth)
            elif isinstance(node, N.Reference):
                self._reference(parent, node)
            elif isinstance(node, N.Formula):
                # A formula in a mixed cell (decision 80); outside tables the parser rejects it.
                self._text(parent, getattr(node, "text", "") or "")

    def _reference(self, parent: ET.Element, node: N.Reference) -> None:
        """``|@``: hyperlink, page field or note reference (5.7, decision 76)."""
        resolved = getattr(node, "resolved", None)
        self._last_space = False
        if resolved is None:
            append_text(parent, "[|@]")  # an error was reported; no ODT is written
        elif resolved.note_id is not None:
            sub(parent, "text:note-ref", {"text:note-class": resolved.note_class,
                                          "text:reference-format": "page" if resolved.mode == "page" else "text",
                                          "text:ref-name": resolved.note_id}, resolved.text)
        elif resolved.bookmark is None:
            # A target of another document of the project: text only (decision 121).
            self._text(parent, resolved.text)
        elif resolved.mode == "page":
            sub(parent, "text:bookmark-ref", {"text:reference-format": "page", "text:ref-name": resolved.bookmark},
                resolved.text)
        else:
            style = getattr(node, "char_style", None)
            link = sub(parent, "text:a", {"xlink:type": "simple", "xlink:href": "#" + str(resolved.bookmark),
                                          "text:style-name": style, "text:visited-style-name": style})
            append_text(link, resolved.text)

    def _note(self, parent: ET.Element, node: N.InlineCommand, depth: int) -> None:
        """``|footnote{…}`` / ``|endnote{…}`` → ``text:note`` (5.10)."""
        info = node.note_info
        note = sub(parent, "text:note", {"text:id": info.note_id, "text:note-class": info.note_class})
        sub(note, "text:note-citation", {"text:label": info.label}, info.citation)
        body = sub(note, "text:note-body")
        p = sub(body, "text:p", {"text:style-name": getattr(node, "note_style", None)})
        saved = self._last_space
        self._last_space = True
        self._inlines(p, node.body or [], depth)
        self._last_space = saved

    def _inline_command(self, parent: ET.Element, node: N.InlineCommand, depth: int) -> None:
        name = node.name
        if name == "img":
            frame = getattr(node, "frame", None)
            if frame is None:
                append_text(parent, "[|img]")
            elif frame.anchor == "as-char":
                self._frame(parent, frame, node, None)
            else:
                self.pending_frames.append((frame, node, None))
            self._last_space = False
            return
        if name in ("footnote", "endnote") and getattr(node, "note_info", None) is not None:
            self._note(parent, node, depth)
            return
        if name == "abbr":
            self._text(parent, getattr(node, "abbr_text", ""))  # 9.4: expanded at the first use
            return
        if name == "link":
            # |link("url"){text} (4.2, decision 120): a hyperlink; without a body the text is the address.
            url = node.args.positional[0] if node.args is not None and node.args.positional else ""
            style = getattr(node, "char_style", None)
            link = sub(parent, "text:a", {"xlink:type": "simple", "xlink:href": url,
                                          "text:style-name": style, "text:visited-style-name": style})
            if node.body:
                self._inlines(link, node.body, depth)
            else:
                self._text(link, url)
            self._last_space = False
            return
        if name == "index":
            mark = getattr(node, "alpha_mark", None)
            if mark is not None:
                _alpha_mark(parent, *mark)
            return
        if name == "review_note":
            # --review (9.2): the condition of an inline branch as a Writer comment.
            note = sub(parent, "office:annotation")
            sub(note, "dc:creator", text="Primula --review")
            p = sub(note, "text:p")
            self._text(p, "".join(n.value for n in node.body or [] if isinstance(n, N.Text)))
            self._last_space = False
            return
        if name == "field.page":
            sub(parent, "text:page-number", {"text:select-page": "current"})
        elif name == "field.pages":
            sub(parent, "text:page-count")
        elif name == "field.title":
            sub(parent, "text:title")
        elif name == "field.chapter":
            level = _arg(node.args, "level") or 1
            sub(parent, "text:chapter", {"text:display": "name", "text:outline-level": level})
        elif name == "fmt":
            props: dict[str, Any] = {}
            for key, value in (node.args.keywords.items() if node.args else []):
                try:
                    props[key] = check_property("character", key, value)
                except PropertyError:
                    self.sink.emit(warning("P8007", node.span, prop=key))
            target = sub(parent, "text:span", {"text:style-name": self.auto.text(props)}) if props else parent
            self._inlines(target, node.body or [], depth)
        else:
            stage = _LATER.get(name, ("—", False))[0]
            self._warn(node, "|" + name, stage)
            append_text(parent, f"[|{name}]")
        self._last_space = False


class _AlphaMark:
    """A mark of the alphabetical index waiting for the next paragraph (9.5)."""

    def __init__(self, term: str, subterm: str | None) -> None:
        self.term = term
        self.subterm = subterm


def _alpha_mark(parent: ET.Element, term: str, subterm: str | None) -> None:
    """``text:alphabetical-index-mark``: a subterm is the entry, its term is ``text:key1`` (9.5)."""
    if subterm:
        sub(parent, "text:alphabetical-index-mark", {"text:string-value": subterm, "text:key1": term})
    else:
        sub(parent, "text:alphabetical-index-mark", {"text:string-value": term})


class _Lead:
    """Bookmark and marks written at the start of a construct paragraph."""

    def __init__(self, bookmark: str | None, marks: list[Any]) -> None:
        self.bookmark = bookmark
        self.marks = marks
        self.prefix = None




def _arg(args: Any, name: str) -> Any:
    return args.get(name) if args is not None and hasattr(args, "get") else None


def _flag(args: Any, props: dict[str, Any], name: str) -> bool:
    """A boolean table parameter: the argument, then the table style, default ``True`` (6.2)."""
    value = _arg(args, name)
    if value is None:
        value = props.get(name, True)
    return value is not False


def _length(value: Any) -> Length | None:
    if isinstance(value, Length):
        return value
    if isinstance(value, str):
        return parse_length(value)
    return None


def _number(value: Any) -> str:
    """``office:value`` of a number: plain decimal notation."""
    from decimal import Decimal

    if isinstance(value, Decimal):
        return format(value, "f")
    return str(value)


def _cell_style_props(props: dict[str, Any]) -> dict[str, Any]:
    """Properties of the automatic cell style (alignment and paragraph style go to paragraphs)."""
    return {k: v for k, v in props.items() if k not in ("align", "paragraph")}


def columns_element(parent: ET.Element, cols: int, gap: Any, rule: Any, widths: list[Fraction] | None) -> None:
    """``style:columns`` of a section or a page layout (7.2, 7.5).

    Equal columns use ``fo:column-gap``; unequal ones (``widths`` in
    percent) get ``style:column`` elements with relative widths and half
    the gap on each inner side.
    """
    if cols <= 1:
        sub(parent, "style:columns", {"fo:column-count": "1"})
        return
    gap_text = units.mm(gap) if isinstance(gap, Length) else "5mm"
    columns = sub(parent, "style:columns", {"fo:column-count": str(cols),
                                            "fo:column-gap": gap_text if widths is None else None})
    if isinstance(rule, Border) and rule.width is not None:
        sub(columns, "style:column-sep", {"style:width": units.pt(rule.width), "style:color": rule.color,
                                          "style:height": "100%", "style:style": rule.type})
    if widths is not None:
        half = units.from_mm((units.to_mm(gap) if isinstance(gap, Length) else Fraction(5)) / 2)
        for index, width in enumerate(widths):
            sub(columns, "style:column", {
                "style:rel-width": f"{int(width * 100)}*",
                "fo:start-indent": "0mm" if index == 0 else units.mm(half),
                "fo:end-indent": "0mm" if index == len(widths) - 1 else units.mm(half)})
