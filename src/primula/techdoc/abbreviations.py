"""Abbreviations: ``|abbr`` and ``|list_of("abbr")`` (9.4, 5.9; decision 116).

Forms: ``|abbr("ПЗ", "програмне забезпечення")`` — a definition and a use
in this place; ``|abbr("ПЗ")`` — a use of an abbreviation defined earlier
or later; ``show=False`` — a definition only (with an expansion only).
``text=`` gives the form of the expansion in this place (a case).

The first use in the text of the resulting ODT (after ``|include`` and
``when=``) expands the abbreviation: «програмне забезпечення (ПЗ)»; later
uses and uses in headings, captions, contents and lists give the short
form and do not count as the first.  ``abbreviations(first="short")``
always writes the short form.

``|list_of("abbr")`` becomes a title paragraph and a borderless two-column
table ``AbbreviationList`` computed here (not an updatable Writer index):
all definitions, ``show=False`` included, sorted by the alphabet of the
language (``sort="alpha"``, :func:`primula.library.text.sort_key`) or by
the first use (``sort="order"``).

Diagnostics: P9201 unknown abbreviation, P9202 different expansions,
P9203 ``show=False`` without an expansion, P9204 ``first="short"`` without a
list, P9205 a list without abbreviations, P9206 invalid settings, P9207
invalid arguments.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from primula.diagnostics import DiagnosticSink, error, warning
from primula.evaluate.model import EArgs
from primula.syntax import nodes as N
from primula.techdoc.texts import GENERATED, TITLES

#: Width of the abbreviation column of the list.
ABBR_COLUMN = "30mm"


@dataclass
class _Definition:
    name: str
    expansion: str
    span: Any
    used: bool = False
    order: int = 10 ** 9


@dataclass
class _Walk:
    """State of the walk in document order."""

    uses: list[tuple[N.InlineCommand, bool]] = field(default_factory=list)
    lists: list[N.Command] = field(default_factory=list)


class AbbreviationTransform:
    """Resolves ``|abbr`` uses and builds ``|list_of("abbr")``.

    Args:
        settings: merged settings of the styles modules (``abbreviations``,
            ``structure_styles``).
        lang: language code (uk, ru, en).
        sink: diagnostics receiver.
    """

    def __init__(self, settings: dict[str, Any], lang: str, sink: DiagnosticSink) -> None:
        options = settings.get("abbreviations") if isinstance(settings.get("abbreviations"), dict) else {}
        self.first = options.get("first", "expand")
        self.sort = options.get("sort", "alpha")
        self.lang = lang
        self.sink = sink
        self.settings = settings
        self.definitions: dict[str, _Definition] = {}
        if self.first not in ("expand", "short"):
            sink.emit(error("P9206", None, key="first", value=str(self.first), allowed="expand, short"))
            self.first = "expand"
        if self.sort not in ("alpha", "order"):
            sink.emit(error("P9206", None, key="sort", value=str(self.sort), allowed="alpha, order"))
            self.sort = "alpha"

    def apply(self, document: N.Document) -> None:
        walk = _Walk()
        self._blocks(document.children, walk, counts=True)
        order = 0
        for node, counts in walk.uses:
            name, expansion, args = _parts(node)
            if not isinstance(name, str) or not name:
                self.sink.emit(error("P9207", node.span))
                node.abbr_text = ""  # type: ignore[attr-defined]
                continue
            definition = self.definitions.get(name)
            if definition is None:
                self.sink.emit(error("P9201", node.span, name=name).hint("help.abbr_define"))
                node.abbr_text = name  # type: ignore[attr-defined]
                continue
            if args.get("show", True) is False:
                node.abbr_text = ""  # type: ignore[attr-defined]
                continue
            text = args.get("text")
            if counts and not definition.used:
                definition.used, definition.order = True, order
                order += 1
                if self.first == "expand":
                    full = text if isinstance(text, str) and text else definition.expansion
                    node.abbr_text = f"{full} ({name})"  # type: ignore[attr-defined]
                    continue
            node.abbr_text = name  # type: ignore[attr-defined]
        if self.first == "short" and self.definitions and not walk.lists:
            self.sink.emit(warning("P9204", next(iter(self.definitions.values())).span))
        for block in walk.lists:
            self._list(block)

    # --- walk in document order ------------------------------------------------------

    def _blocks(self, blocks: list[Any], walk: _Walk, counts: bool) -> None:
        for block in blocks:
            self._block(block, walk, counts)

    def _block(self, block: Any, walk: _Walk, counts: bool) -> None:
        if isinstance(block, N.Heading):
            self._inlines(block.body, walk, False)
            return
        if isinstance(block, N.Command):
            if block.name == "list_of" and _list_kind(block) == "abbr":
                walk.lists.append(block)
                return
            if block.name == "abbr":  # a definition on its own line: |abbr("ЄДРПОУ", "…", show=False)
                self._collect(block)
                walk.uses.append((block, counts))  # type: ignore[arg-type]
                return
            caption = block.name in ("caption", "figure")
            self._inlines(block.body, walk, counts and not caption)
            self._blocks(block.children, walk, counts and not caption)
            return
        if isinstance(block, N.ListBlock):
            for item in block.items:
                self._inlines(item.body, walk, counts)
                self._blocks(item.children, walk, counts)
            return
        if isinstance(block, N.TableRow):
            for cell in block.cells:
                self._inlines(cell.body, walk, counts)
            return
        self._inlines(getattr(block, "body", None) or [], walk, counts)
        self._blocks(getattr(block, "children", None) or [], walk, counts)

    def _inlines(self, nodes: list[Any], walk: _Walk, counts: bool) -> None:
        for node in nodes:
            if isinstance(node, N.InlineCommand) and node.name == "abbr":
                self._collect(node)
                walk.uses.append((node, counts))
                continue
            body = getattr(node, "body", None)
            if isinstance(body, list):
                self._inlines(body, walk, counts)

    def _collect(self, node: Any) -> None:
        """Register a definition (two positional arguments)."""
        name, expansion, args = _parts(node)
        if expansion is None:
            if args.get("show", True) is False:
                self.sink.emit(error("P9203", node.span, name=str(name)))
            return
        if not isinstance(name, str) or not isinstance(expansion, str):
            return
        existing = self.definitions.get(name)
        if existing is None:
            self.definitions[name] = _Definition(name, expansion, node.span)
        elif existing.expansion != expansion:
            self.sink.emit(error("P9202", node.span, name=name).note("note.first_definition", existing.span))

    # --- the list ---------------------------------------------------------------------

    def _list(self, block: N.Command) -> None:
        """Replace ``|list_of("abbr")`` by a title and a table (or nothing)."""
        span = block.span
        if not self.definitions:
            self.sink.emit(warning("P9205", span))
            block.name, block.children, block.body, block.args = GENERATED, [], [], None
            return
        entries = list(self.definitions.values())
        if self.sort == "alpha":
            from primula.library.text import sort_key_of

            entries.sort(key=lambda d: sort_key_of(d.name, self.lang))
        else:
            entries.sort(key=lambda d: d.order)
        args = block.args if isinstance(block.args, EArgs) else None
        title = args.get("title") if args is not None else None
        if title is None:
            title = TITLES[self.lang]["abbr"]
        rows = []
        for entry in entries:
            cells = [N.Command(span, "cell", span, EArgs(span, [], {}), "line", [N.Text(span, text)])  # type: ignore[arg-type]
                     for text in (entry.name, entry.expansion)]
            rows.append(N.Command(span, "row", span, EArgs(span, [], {}), "env", [], cells))  # type: ignore[arg-type]
        table_args = EArgs(span, [], {"cols": [ABBR_COLUMN, "*"], "header": 0, "style": "AbbreviationList"})
        table = N.Command(span, "table", span, table_args, "env", [], rows)  # type: ignore[arg-type]
        children: list[Any] = []
        if title:
            style = _list_title_style(self.settings)
            children.append(N.StyleBlock(span, N.StyleRef(span, style), None, "line", [N.Text(span, title)], []))
        children.append(table)
        block.name, block.args, block.body, block.children, block.form = GENERATED, None, [], children, "env"


def _parts(node: Any) -> tuple[Any, Any, dict[str, Any]]:
    args = node.args if isinstance(node.args, EArgs) else None
    positional = args.positional if args is not None else []
    keywords = dict(args.keywords) if args is not None else {}
    name = positional[0] if positional else None
    expansion = positional[1] if len(positional) > 1 else None
    return name, expansion, keywords


def _list_kind(block: N.Command) -> Any:
    args = block.args
    return args.positional[0] if isinstance(args, EArgs) and args.positional else None


def _list_title_style(settings: dict[str, Any]) -> str:
    styles = settings.get("structure_styles") if isinstance(settings.get("structure_styles"), dict) else {}
    list_of = styles.get("list_of") if isinstance(styles.get("list_of"), dict) else {}
    return str(list_of.get("title") or "ContentsTitle")
