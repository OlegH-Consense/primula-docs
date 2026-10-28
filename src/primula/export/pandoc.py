"""Export of an evaluated document as a pandoc AST (stage 19.1, decision 139).

``primula export FILE --to FORMAT`` evaluates the document exactly as
``build`` does — values, conditions, fragments, numbering, captions,
references, notes — and writes the result as the JSON AST of pandoc
(https://pandoc.org/filters.html, ``pandoc-api-version`` 1.23): ``--to json``
writes the AST itself, any other format is made by ``pandoc -f json -t
FORMAT`` (Markdown, HTML, DOCX, LaTeX, EPUB…).  The translator needs no
pandoc library: the AST is plain JSON.

What becomes what:

* headings — ``Header`` with the number of the structure in the text
  («2.1 Ціна») and the bookmark as the identifier; clauses, admonitions and
  styled blocks — paragraphs with their numbers; a paragraph style becomes
  ``Div`` with ``custom-style`` (the DOCX writer of pandoc applies it), a
  character style — ``Span`` with ``custom-style``; admonitions — ``Div``
  with the class of the kind (``note``, ``warning``…);
* short forms — ``Strong``, ``Emph``, ``Underline``, ``Superscript``,
  ``Subscript``, ``Code``, ``Strikeout``, quotes in the characters of the
  document language, placeholders — ``Span`` of class ``placeholder``;
* lists — ``BulletList`` / ``OrderedList`` (start number kept); tables — a
  ``Table`` from the computed grid (header rows, spans, cell texts as
  displayed); captions «Таблиця 1 — …» — the caption of the table or the
  figure; images — ``Image`` (a file path relative to the output, an SVG
  string as a ``data:`` URI);
* references ``|@`` — ``Link`` to ``#bookmark`` with the computed text;
  ``|link`` — ``Link``; footnotes and endnotes — ``Note``; a table of
  contents and lists of figures and tables — a list of links to the
  entries (no page numbers); verbatim blocks — ``CodeBlock``;
* page layout (page styles, columns, frames, headers and footers,
  watermarks, page fields) has no counterpart: page breaks and columns are
  dropped, headers, footers and page numbers are not exported (warning
  P8101 once per construct).

Metadata ``doc.*`` become ``title``, ``author``, ``date``, ``lang``,
``subject``, ``description``, ``keywords``.
"""

from __future__ import annotations

import base64
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from primula.diagnostics import DiagnosticSink, error, warning
from primula.syntax import nodes as N

#: The pandoc API version of the AST (pandoc 3.x).
API_VERSION = [1, 23, 1]
#: Output file extensions by pandoc format (``--to``); others use the format name.
EXTENSIONS = {"json": "json", "markdown": "md", "md": "md", "gfm": "md", "commonmark": "md", "html": "html",
              "html5": "html", "docx": "docx", "odt": "odt", "latex": "tex", "epub": "epub", "rst": "rst",
              "org": "org", "plain": "txt", "asciidoc": "adoc", "mediawiki": "wiki", "rtf": "rtf", "typst": "typ"}
#: Short names accepted by ``--to``.
ALIASES = {"md": "markdown"}
#: Formats that use ``custom-style`` (the DOCX and ODT writers of pandoc; the AST keeps it for filters).
STYLED = {"json", "docx", "odt"}
#: Formats written as a standalone document (with metadata and a head).
_STANDALONE = {"html", "html5", "latex", "rtf", "typst"}
_SHORT = {"*": "Strong", "/": "Emph", "_": "Underline", "^": "Superscript", ",": "Subscript", "—": "Strikeout"}
_QUOTES = {"uk": ("«", "»", "„", "“"), "ru": ("«", "»", "„", "“"), "en": ("“", "”", "‘", "’")}
#: Commands whose children are written as they are.
_TRANSPARENT = {"block", "part", "scope", "list", "caption", "generated", "section", "page", "frame", "document"}
#: Commands without a counterpart in pandoc (layout): dropped silently or with P8101.
_DROPPED_SILENT = {"newpage", "newcolumn", "set", "index", "toc_entry", "abbr"}
_DROPPED_WARN = {"header", "footer", "watermark"}


def _attr(ident: str = "", classes: list[str] | None = None, pairs: list[list[str]] | None = None) -> list[Any]:
    return [ident or "", classes or [], pairs or []]


def _str(text: str) -> list[dict[str, Any]]:
    """Inlines of plain text: words as ``Str``, runs of spaces as one ``Space``."""
    out: list[dict[str, Any]] = []
    for part in re.split(r"( +|\n)", text):
        if not part:
            continue
        if part == "\n":
            out.append({"t": "LineBreak"})
        elif part.startswith(" "):
            out.append({"t": "Space"})
        else:
            out.append({"t": "Str", "c": part})
    return out


class PandocWriter:
    """Builds the pandoc AST of an evaluated document.

    Args:
        language: the document language (``uk-UA``): quotes and ``lang``.
        sink: receiver of P8101 warnings.
        output_dir: the directory of the output file: image paths are made relative to it
            when it lies inside ``root`` (else they are absolute).
    """

    def __init__(self, language: str | None, sink: DiagnosticSink, output_dir: Path, styles: bool = True,
                 root: Path | None = None) -> None:
        self.language = language or "uk-UA"
        self.quotes = _QUOTES.get(self.language.split("-")[0].lower(), _QUOTES["uk"])
        self.sink = sink
        self.output_dir = output_dir
        #: The project root: images get paths relative to the output only when it is inside the root.
        self.root = root
        #: Write paragraph and character styles as ``custom-style`` (DOCX, ODT, the AST).
        self.styles = styles
        self._warned: set[str] = set()
        #: Numbers and bookmarks of an enclosing clause environment for its first paragraph.
        self.pending: list[Any] = []

    # --- document ---------------------------------------------------------------------------

    def document(self, document: N.Document, meta: dict[str, Any]) -> dict[str, Any]:
        """The AST: ``{"pandoc-api-version", "meta", "blocks"}``."""
        return {"pandoc-api-version": API_VERSION, "meta": self._meta(meta), "blocks": self.blocks(document.children)}

    def _meta(self, meta: dict[str, Any]) -> dict[str, Any]:
        def inlines(text: Any) -> dict[str, Any]:
            return {"t": "MetaInlines", "c": _str(str(text))}

        result: dict[str, Any] = {"lang": {"t": "MetaString", "c": self.language}}
        for key, name in (("title", "title"), ("subject", "subtitle"), ("description", "abstract"),
                          ("creator", "author"), ("organization", "organization"), ("identifier", "identifier")):
            if meta.get(key):
                result[name] = inlines(meta[key])
        if meta.get("created") is not None:
            result["date"] = {"t": "MetaString", "c": str(meta["created"])[:10]}
        keywords = meta.get("keywords")
        if keywords:
            items = keywords if isinstance(keywords, (list, tuple)) else [keywords]
            result["keywords"] = {"t": "MetaList", "c": [inlines(k) for k in items]}
        return result

    def _warn(self, node: Any, construct: str) -> None:
        if construct not in self._warned:
            self._warned.add(construct)
            self.sink.emit(warning("P8101", node.span, construct=construct))

    # --- blocks --------------------------------------------------------------------------------

    def blocks(self, nodes: list[Any]) -> list[Any]:
        out: list[Any] = []
        for node in nodes:
            out.extend(self.block(node))
        return out

    def _lead(self, info: Any = None) -> tuple[str, list[Any]]:
        """Bookmark and number inlines of a paragraph: the pending ones of an environment, then its own."""
        items = [*self.pending, info] if info is not None else list(self.pending)
        self.pending = []
        ident = ""
        prefix: list[Any] = []
        for item in items:
            if item is None:
                continue
            if getattr(item, "bookmark", None) and not ident:
                ident = item.bookmark
            if getattr(item, "prefix", None):
                prefix.extend(_str(item.prefix))
        return ident, prefix

    def _para(self, inlines: list[Any], info: Any = None, style: Any = None) -> list[Any]:
        ident, prefix = self._lead(info)
        content = prefix + self.inlines(inlines)
        if ident:
            content = [{"t": "Span", "c": [_attr(ident), []]}] + content
        block = {"t": "Para", "c": content}
        name = getattr(style, "parent", None) if style is not None and self.styles else None
        if name:
            return [{"t": "Div", "c": [_attr(pairs=[["custom-style", name]]), [block]]}]
        return [block]

    def block(self, node: Any) -> list[Any]:
        if isinstance(node, N.Paragraph):
            return self._para(node.body, style=getattr(node, "style_use", None))
        if isinstance(node, N.Heading):
            ident, prefix = self._lead(getattr(node, "struct", None))
            return [{"t": "Header", "c": [node.level, _attr(ident), prefix + self.inlines(node.body)]}]
        if isinstance(node, (N.Clause, N.Admonition, N.StyleBlock)):
            if getattr(node, "struct", None) is not None:
                self.pending.append(node.struct)
            inner: list[Any] = []
            if node.form == "line":
                inner.extend(self._para(node.body, style=getattr(node, "style_use", None)))
            inner.extend(self.blocks(node.children))
            if isinstance(node, N.Admonition):
                kind = getattr(node, "admonition_kind", None) or _first_string(node.args) or "note"
                return [{"t": "Div", "c": [_attr(classes=["admonition", str(kind)]), inner]}]
            return inner
        if isinstance(node, N.ListBlock):
            return [self._list(node)]
        if isinstance(node, N.Verbatim):
            return [{"t": "CodeBlock", "c": [_attr(), node.text]}]
        if isinstance(node, N.Command):
            return self._command(node)
        return []

    def _list(self, node: N.ListBlock) -> dict[str, Any]:
        items = []
        for item in node.items:
            content = self._para(item.body, info=getattr(item, "struct", None))
            content[0]["t"] = "Plain" if content[0]["t"] == "Para" else content[0]["t"]
            for child in item.children:
                content.extend(self.block(child))
            items.append(content)
        if node.items and node.items[0].kind == "number":
            info = getattr(node, "list_info", None)
            start = (info.start if info is not None and info.start else None) or 1
            return {"t": "OrderedList", "c": [[start, {"t": "Decimal"}, {"t": "Period"}], items]}
        return {"t": "BulletList", "c": items}

    def _command(self, node: N.Command) -> list[Any]:
        name = node.name
        if getattr(node, "skip_output", False) or name in _DROPPED_WARN:
            self._warn(node, "|" + name)
            return []
        if name in _DROPPED_SILENT:
            if name == "toc_entry" and getattr(node, "struct", None) is not None:
                self.pending.append(node.struct)
            if name == "abbr" and getattr(node, "abbr_text", ""):
                return [{"t": "Para", "c": _str(node.abbr_text)}]
            return []
        if name == "table":
            return self._table(node)
        if name == "figure":
            return self._figure(node)
        if name == "img":
            image = self._image(node)
            return [{"t": "Para", "c": [image]}] if image else []
        if name == "appendix":
            return self._appendix(node)
        if getattr(node, "index_info", None) is not None:
            return self._index(node)
        if name == "section" and getattr(node, "struct", None) is not None:
            self.pending.append(node.struct)
        if name in _TRANSPARENT:
            return self.blocks(node.children)
        out: list[Any] = []
        if node.body:
            out.extend(self._para(node.body, style=getattr(node, "style_use", None)))
        out.extend(self.blocks(node.children))
        return out

    def _appendix(self, node: N.Command) -> list[Any]:
        info = getattr(node, "appendix_info", None)
        if info is None:
            return self.blocks(node.children)
        out: list[Any] = []
        if info.combined is not None:
            out.append({"t": "Header", "c": [info.outline, _attr(info.bookmark or ""), _str(info.combined)]})
            if info.subtitle:
                out.append({"t": "Para", "c": _str(info.subtitle)})
        else:
            out.append({"t": "Header", "c": [info.outline, _attr(info.bookmark or ""), _str(info.designation)]})
            for text in (info.subtitle, info.title):
                if text:
                    out.append({"t": "Para", "c": [{"t": "Strong", "c": _str(text)}]})
        return out + self.blocks(node.children)

    def _index(self, node: N.Command) -> list[Any]:
        """A table of contents or a list of figures/tables: links to the entries, nested by level."""
        info = node.index_info
        out: list[Any] = []
        if info.title:
            out.append({"t": "Para", "c": [{"t": "Strong", "c": _str(info.title)}]})
        root: list[Any] = []
        stack: list[tuple[int, list[Any]]] = [(0, root)]
        for entry in info.entries:
            text = _str(entry.text)
            item = [{"t": "Plain", "c": [{"t": "Link", "c": [_attr(), text, ["#" + entry.bookmark, ""]]}]
                     if entry.bookmark else text}]
            while len(stack) > 1 and stack[-1][0] >= entry.level:
                stack.pop()
            stack[-1][1].append(item)
            children: list[Any] = []
            item.append({"t": "BulletList", "c": children})
            stack.append((entry.level, children))

        def prune(items: list[Any]) -> list[Any]:
            for item in items:
                nested = item[-1]
                if not nested["c"]:
                    item.pop()
                else:
                    prune(nested["c"])
            return items

        if root:
            out.append({"t": "BulletList", "c": prune(root)})
        return out

    def _caption(self, node: N.Command) -> list[Any]:
        info = getattr(node, "caption_info", None)
        if info is None:
            return [None, []]
        content = _str(info.before) + self.inlines(info.title) + _str(info.after)
        return [None, [{"t": "Plain", "c": content}]]

    def _figure(self, node: N.Command) -> list[Any]:
        image = self._image(node)
        info = getattr(node, "caption_info", None)
        ident = info.bookmark if info is not None and info.bookmark else ""
        body = [{"t": "Plain", "c": [image]}] if image else []
        return [{"t": "Figure", "c": [_attr(ident), self._caption(node), body]}]

    def _image(self, node: Any) -> dict[str, Any] | None:
        """An ``Image``: a file path relative to the output, an SVG string as a ``data:`` URI."""
        frame = getattr(node, "frame", None)
        image = getattr(frame, "image", None)
        if image is None:
            return None
        if image.format == "svg" and not Path(image.path).is_file():
            url = "data:image/svg+xml;base64," + base64.b64encode(image.data).decode("ascii")
        else:
            path = Path(image.path).resolve()
            inside = self.root is not None and self.output_dir.resolve().is_relative_to(self.root.resolve())
            url = Path(os.path.relpath(path, self.output_dir.resolve())).as_posix() if inside else path.as_posix()
        pairs = []
        if frame.width is not None:
            pairs.append(["width", f"{float(frame.width):g}mm"])
        if frame.height is not None:
            pairs.append(["height", f"{float(frame.height):g}mm"])
        alt = _str(frame.alt) if getattr(frame, "alt", None) else []
        return {"t": "Image", "c": [_attr(pairs=pairs), alt, [url, ""]]}

    def _table(self, node: N.Command) -> list[Any]:
        grid = getattr(node, "table_grid", None)
        info = getattr(node, "caption_info", None)
        if getattr(node, "struct", None) is not None and info is None:
            self.pending.append(node.struct)
        if grid is None or not grid.rows:
            return []
        total = sum(float(w) for w in grid.widths) if grid.widths else 0
        colspecs = [[{"t": "AlignDefault"},
                     {"t": "ColWidth", "c": float(w) / total} if total else {"t": "ColWidthDefault"}]
                    for w in (grid.widths or [None] * grid.count)]
        rows = [self._row(grid, row) for row in grid.rows]
        head = rows[:grid.header]
        foot = rows[len(rows) - grid.footer:] if grid.footer else []
        body = rows[grid.header:len(rows) - grid.footer if grid.footer else len(rows)]
        ident = info.bookmark if info is not None and info.bookmark else ""
        return [{"t": "Table", "c": [_attr(ident), self._caption(node), colspecs, [_attr(), head],
                                     [[_attr(), 0, [], body]], [_attr(), foot]]}]

    def _row(self, grid: Any, row: Any) -> list[Any]:
        cells = []
        for column in range(grid.count):
            owner = grid.owners.get((row.index, column))
            if owner is None:
                cells.append([_attr(), {"t": "AlignDefault"}, 1, 1, []])
            elif (owner.row, owner.col) == (row.index, column):
                if owner.inlines is not None:
                    content = [{"t": "Plain", "c": self.inlines(owner.display if owner.display is not None
                                                                else owner.inlines)}]
                else:
                    content = self.blocks([b for b in owner.blocks or [] if not isinstance(b, N.BlankLine)])
                cells.append([_attr(), {"t": "AlignDefault"}, owner.rows, owner.span, content])
        return [_attr(), cells]

    # --- inlines -------------------------------------------------------------------------------

    def inlines(self, nodes: list[Any], depth: int = 0) -> list[Any]:
        out: list[Any] = []
        for node in nodes:
            if isinstance(node, N.Text):
                out.extend(_str(node.value))
            elif isinstance(node, N.LineBreak):
                out.append({"t": "LineBreak"})
            elif isinstance(node, N.Short):
                out.extend(self._short(node, depth))
            elif isinstance(node, N.StyleSpan):
                content = self.inlines(node.body, depth)
                style = getattr(node, "char_style", None) or (node.style.name if node.style else None)
                if style and self.styles:
                    out.append({"t": "Span", "c": [_attr(pairs=[["custom-style", str(style)]]), content]})
                else:
                    out.extend(content)
            elif isinstance(node, N.Reference):
                out.extend(self._reference(node))
            elif isinstance(node, N.InlineCommand):
                out.extend(self._inline_command(node, depth))
            elif isinstance(node, N.Formula):
                out.extend(_str(getattr(node, "text", "") or ""))
        return out

    def _short(self, node: N.Short, depth: int) -> list[Any]:
        if node.mark == '"':
            opening, closing = self.quotes[0:2] if depth % 2 == 0 else self.quotes[2:4]
            return [{"t": "Str", "c": opening}, *self.inlines(node.body, depth + 1), {"t": "Str", "c": closing}]
        if node.mark == "`":
            return [{"t": "Code", "c": [_attr(), _plain(node.body)]}]
        if node.mark == "?":
            return [{"t": "Span", "c": [_attr(classes=["placeholder"]), self.inlines(node.body, depth)]}]
        kind = _SHORT.get(node.mark)
        content = self.inlines(node.body, depth)
        return [{"t": kind, "c": content}] if kind else content

    def _reference(self, node: N.Reference) -> list[Any]:
        resolved = getattr(node, "resolved", None)
        if resolved is None:
            return []
        if resolved.mode == "page":
            self._warn(node, "|@(…, \"page\")")
            return _str(resolved.text)
        target = resolved.bookmark or (resolved.note_id if resolved.note_id else None)
        if target is None:
            return _str(resolved.text)
        return [{"t": "Link", "c": [_attr(), _str(resolved.text), ["#" + str(target), ""]]}]

    def _inline_command(self, node: N.InlineCommand, depth: int) -> list[Any]:
        name = node.name
        if name in ("footnote", "endnote") and getattr(node, "note_info", None) is not None:
            return [{"t": "Note", "c": [{"t": "Para", "c": self.inlines(node.body or [], depth)}]}]
        if name == "link":
            url = node.args.positional[0] if node.args is not None and node.args.positional else ""
            text = self.inlines(node.body, depth) if node.body else _str(str(url))
            return [{"t": "Link", "c": [_attr(), text, [str(url), ""]]}]
        if name == "img":
            image = self._image(node)
            return [image] if image else []
        if name == "abbr":
            return _str(getattr(node, "abbr_text", ""))
        if name == "fmt":
            return self.inlines(node.body or [], depth)
        if name.startswith("field.") or name == "review_note":
            self._warn(node, "|" + name)
            return []
        if name == "index":
            return []
        return self.inlines(node.body or [], depth)


def _plain(nodes: list[Any]) -> str:
    """Plain text of inline nodes (``Code``)."""
    parts = []
    for node in nodes:
        if isinstance(node, N.Text):
            parts.append(node.value)
        elif hasattr(node, "body") and isinstance(node.body, list):
            parts.append(_plain(node.body))
    return "".join(parts)


def _first_string(args: Any) -> str | None:
    if args is None or not getattr(args, "positional", None):
        return None
    value = args.positional[0]
    return value if isinstance(value, str) else None


#: Width of the text of a standalone HTML file: the template of pandoc limits it to 36em
#: (a third of a wide screen); a document page reads better wider.
HTML_MAX_WIDTH = "60em"


def run_pandoc(ast: str, fmt: str, output: Path, resource_dir: Path, sink: DiagnosticSink,
               extra: list[str] | None = None) -> bool:
    """Convert the JSON AST with ``pandoc -f json -t FORMAT -o OUTPUT``.

    A paragraph is one line of the output (``--wrap=none``: pandoc wraps text formats at
    72 columns by default); a standalone HTML file is ``HTML_MAX_WIDTH`` wide.  ``extra``
    (``--pandoc-arg``) comes last and overrides these defaults (``--wrap=auto``,
    ``--reference-doc=…``); a ``maxwidth`` of the user replaces the default width.

    Returns:
        ``True`` when the file is written; errors are P8102 (no pandoc) and P8103 (pandoc failed).
    """
    pandoc = shutil.which("pandoc")
    if pandoc is None:
        sink.emit(error("P8102", None, at_file=str(output)))
        return False
    command = [pandoc, "-f", "json", "-t", fmt, "-o", str(output), "--resource-path", str(resource_dir),
               "--wrap=none"]
    if fmt in _STANDALONE:
        command.append("--standalone")
    extra = list(extra or [])
    if fmt in ("html", "html5"):
        command.append("--embed-resources")
        # A repeated -V joins the values in pandoc: the default only without the user's own.
        if not any("maxwidth" in argument for argument in extra):
            command += ["-V", "maxwidth=" + HTML_MAX_WIDTH]
    command += extra
    try:
        result = subprocess.run(command, input=ast.encode("utf-8"), capture_output=True, timeout=300, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        sink.emit(error("P8103", None, at_file=str(output), reason=str(exc)))
        return False
    if result.returncode != 0:
        reason = result.stderr.decode("utf-8", "replace").strip().splitlines()
        sink.emit(error("P8103", None, at_file=str(output), reason=reason[-1] if reason else f"exit {result.returncode}"))
        return False
    return True
