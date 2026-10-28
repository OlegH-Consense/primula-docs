"""``|!`` blocks: warnings as tables, notes and tips as paragraphs (9.1, decision 116).

The transform replaces the content of each evaluated
:class:`~primula.syntax.nodes.Admonition` by ordinary nodes; the node
itself stays (its ``id=`` is a reference target, ``block=`` a block style).

* ``danger``, ``warning``, ``caution``, ``notice`` — a table without outer
  margins (style ``AdmonitionTable<Kind>``): the symbol column (``symbol=``
  or ``admonition_symbols(…)``) and the text column; without a symbol one
  column with a left border in the colour of the signal word style.  The
  text column holds, in order (ISO 3864-2, ANSI Z535.6): the signal word
  (``Admonition<Kind>``), ``hazard`` (``AdmonitionText``, bold),
  ``consequence``, the body.
* ``note`` — «Примітка. Текст.»: the word in the character style
  ``NoteLabel``, the paragraph ``Note``; several notes in a row (only blank
  lines between) — «Примітки:» and a numbered list ``NoteList``, each group
  numbered from 1.  ``tip`` — «Порада. Текст.», never grouped.

Diagnostics (group P9): unknown kind P9101, an empty block P9102,
``danger``/``warning`` without ``hazard`` P9103, ``hazard``/``consequence``
of ``note``/``tip`` P9104.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any, Callable

from primula.diagnostics import DiagnosticSink, error, warning
from primula.evaluate.model import EArgs
from primula.syntax import nodes as N
from primula.techdoc.texts import HAZARD_KINDS, KINDS, WORDS, by_language

#: Width of the symbol column and of the symbol image.
SYMBOL_COLUMN = "18mm"
SYMBOL_WIDTH = "13mm"


class AdmonitionTransform:
    """Rewrites the ``|!`` blocks of a document.

    Args:
        settings: merged settings of the styles modules (``admonition_words``,
            ``admonition_symbols``).
        effective: ``effective(style) -> properties`` of the merged style system.
        lang: language code (uk, ru, en).
        sink: diagnostics receiver.
        resolve: ``resolve(path, span) -> Path | None`` of an image path
            relative to the file of ``span`` (10.1).
        symbols_span: position of the ``admonition_symbols(…)`` call: its
            paths are relative to the file of that call.
    """

    def __init__(self, settings: dict[str, Any], effective: Callable[[str], dict[str, Any]], lang: str,
                 sink: DiagnosticSink, resolve: Callable[[str, Any], Any], symbols_span: Any = None) -> None:
        self.words = by_language(WORDS, settings.get("admonition_words"), lang)
        symbols = settings.get("admonition_symbols")
        self.symbols = symbols if isinstance(symbols, dict) else {}
        self.symbols_span = symbols_span
        self.effective = effective
        self.sink = sink
        self.resolve = resolve

    def apply(self, document: N.Document) -> None:
        document.children = self._blocks(document.children)

    # ------------------------------------------------------------------

    def _blocks(self, blocks: list[Any]) -> list[Any]:
        out: list[Any] = []
        i = 0
        while i < len(blocks):
            block = blocks[i]
            if isinstance(block, N.Admonition) and _kind(block) == "note":
                group = [block]
                j = i + 1
                while j < len(blocks):
                    following = blocks[j]
                    if isinstance(following, N.BlankLine):
                        j += 1
                        continue
                    if isinstance(following, N.Admonition) and _kind(following) == "note":
                        group.append(following)
                        j += 1
                        continue
                    break
                if len(group) > 1:
                    for note in group:
                        self._check(note, "note")
                    out.append(self._note_group(group))
                    # Blank lines after the last note stay (they separate the group).
                    i = next(k for k in range(i, len(blocks)) if blocks[k] is group[-1]) + 1
                    continue
            self._descend(block)
            if isinstance(block, N.Admonition):
                self._admonition(block)
            out.append(block)
            i += 1
        return out

    def _descend(self, block: Any) -> None:
        """Rewrite nested block lists (clauses, environments, table cells, list items)."""
        children = getattr(block, "children", None)
        if isinstance(children, list) and children:
            block.children = self._blocks(children)
        if isinstance(block, N.ListBlock):
            for item in block.items:
                if item.children:
                    item.children = self._blocks(item.children)

    # --- checks ------------------------------------------------------------------

    def _check(self, block: N.Admonition, kind: str | None) -> bool:
        """Kind, emptiness and parameters (P9101-P9104); ``False`` if the block is left as is."""
        args = block.args
        if kind not in KINDS:
            self.sink.emit(error("P9101", block.span, kind=str(kind), allowed=", ".join(KINDS)))
            return False
        hazard, consequence = _arg(args, "hazard"), _arg(args, "consequence")
        if kind in ("note", "tip"):
            if hazard is not None or consequence is not None:
                self.sink.emit(warning("P9104", block.span, kind=kind))
        elif kind in ("danger", "warning") and hazard is None:
            self.sink.emit(warning("P9103", block.span, kind=kind))
        if not _has_body(block) and (kind in ("note", "tip") or (hazard is None and consequence is None)):
            self.sink.emit(error("P9102", block.span))
            return False
        return True

    # --- warnings ------------------------------------------------------------------

    def _admonition(self, block: N.Admonition) -> None:
        kind = _kind(block)
        if not self._check(block, kind):
            return
        if kind in ("note", "tip"):
            block.children = self._note_blocks(block, self.words[kind])
        else:
            block.children = [self._table(block, kind)]
        block.form, block.body = "env", []

    def _table(self, block: N.Admonition, kind: str) -> N.Command:
        span = block.span
        name = kind.capitalize()
        lines: list[Any] = [_styled(span, f"Admonition{name}", [N.Text(span, self.words[kind])])]
        hazard, consequence = _arg(block.args, "hazard"), _arg(block.args, "consequence")
        if hazard is not None:
            lines.append(_styled(span, "AdmonitionText", [N.Short(span, "*", None, _inlines(span, hazard))]))
        if consequence is not None:
            lines.append(_styled(span, "AdmonitionText", _inlines(span, consequence)))
        if _meaningful(block.body):
            lines.append(_styled(span, "AdmonitionText", list(block.body)))
        rest = [b for b in block.children if not isinstance(b, N.BlankLine)]
        if rest:
            lines.append(N.StyleBlock(span, N.StyleRef(span, "AdmonitionText"), None, "env", [], rest))
        cells = []
        symbol = self._symbol(block, kind)
        text_args: dict[str, Any] = {}
        if symbol is not None:
            cells.append(_cell(span, {"valign": "top"}, [symbol]))
        else:
            color = self.effective(f"Admonition{name}").get("color") or "#000000"
            text_args["border_left"] = f"2.5pt solid {color}"
        cells.append(_cell(span, text_args, lines))
        row = N.Command(span, "row", span, EArgs(span, [], {}), "env", [], cells)  # type: ignore[arg-type]
        cols = [SYMBOL_COLUMN, "*"] if symbol is not None else ["*"]
        args = EArgs(span, [], {"cols": cols, "header": 0, "style": f"AdmonitionTable{name}"})
        return N.Command(span, "table", span, args, "env", [], [row])  # type: ignore[arg-type]

    def _symbol(self, block: N.Admonition, kind: str) -> N.Command | None:
        """The symbol image: ``symbol=`` (a path or a key of ``admonition_symbols``) or the kind's default."""
        value = _arg(block.args, "symbol")
        span = block.span
        if value is None:
            value = self.symbols.get(kind)
            base = self.symbols_span
        else:
            base = None
            if isinstance(value, str) and value in self.symbols:
                value = self.symbols[value]
        if not isinstance(value, str) or not value:
            return None
        path = self.resolve(value, base or span)
        if path is None:
            return None
        node = N.Command(span, "img", span, EArgs(span, [value], {"width": SYMBOL_WIDTH}), "bare")  # type: ignore[arg-type]
        node.image_path = path  # type: ignore[attr-defined]
        return node

    # --- notes and tips ------------------------------------------------------------

    def _label(self, span: Any, word: str) -> list[Any]:
        return [N.StyleSpan(span, N.StyleRef(span, "NoteLabel"), None, [N.Text(span, word)]), N.Text(span, " ")]

    def _note_blocks(self, block: N.Admonition, word: str) -> list[Any]:
        """«Примітка. Текст.»: the word at the start of the first paragraph; paragraphs in ``Note``."""
        span = block.span
        label = self._label(span, word + ".")
        children = [b for b in block.children]
        if _meaningful(block.body):
            first = _styled(span, "Note", label + list(block.body))
            rest = [b for b in children if not isinstance(b, N.BlankLine)]
            return [first] + ([N.StyleBlock(span, N.StyleRef(span, "Note"), None, "env", [], rest)] if rest else [])
        for index, child in enumerate(children):
            if isinstance(child, N.Paragraph):
                children[index] = replace(child, body=label + list(child.body))
                break
        else:
            children.insert(0, N.Paragraph(span, label))
        return [N.StyleBlock(span, N.StyleRef(span, "Note"), None, "env", [], children)]

    def _note_group(self, notes: list[N.Admonition]) -> N.StyleBlock:
        """Several notes: «Примітки:» and a numbered list ``NoteList`` (numbered from 1)."""
        span = notes[0].span
        heading = N.Paragraph(span, [N.StyleSpan(span, N.StyleRef(span, "NoteLabel"), None,
                                                 [N.Text(span, self.words["notes"] + ":")])])
        items = []
        for note in notes:
            if _meaningful(note.body):
                body, children = list(note.body), [b for b in note.children if not isinstance(b, N.BlankLine)]
            else:
                blocks = [b for b in note.children if not isinstance(b, N.BlankLine)]
                if blocks and isinstance(blocks[0], N.Paragraph):
                    body, children = list(blocks[0].body), blocks[1:]
                else:
                    body, children = [], blocks
            item = N.ListItem(note.span, "#", None, body, children)
            item.admonition = note  # type: ignore[attr-defined]  # id= of the note (decision 116)
            items.append(item)
        style = N.Command(span, "list", span, EArgs(span, ["NoteList"], {}), "bare")  # type: ignore[arg-type]
        listing = N.ListBlock(span, items, style, "env")
        return N.StyleBlock(span, N.StyleRef(span, "Note"), None, "env", [], [heading, listing])


# --- helpers ----------------------------------------------------------------------

def _kind(block: N.Admonition) -> Any:
    args = block.args
    return args.positional[0] if isinstance(args, EArgs) and args.positional else None


def _arg(args: Any, name: str) -> Any:
    return args.get(name) if isinstance(args, EArgs) else None


def _meaningful(inlines: list[Any] | None) -> bool:
    return any(not (isinstance(n, N.Comment) or isinstance(n, N.Text) and not n.value.strip())
               for n in inlines or [])


def _has_body(block: N.Admonition) -> bool:
    return _meaningful(block.body) or any(not isinstance(b, N.BlankLine) for b in block.children)


def _inlines(span: Any, value: Any) -> list[Any]:
    """A text argument (``hazard``, ``consequence``) as inline nodes."""
    nodes = getattr(value, "nodes", None)
    if isinstance(nodes, list) and getattr(value, "kind", None) == "inline":
        return list(nodes)
    return [N.Text(span, value if isinstance(value, str) else str(value))]


def _styled(span: Any, style: str, inlines: list[Any]) -> N.StyleBlock:
    return N.StyleBlock(span, N.StyleRef(span, style), None, "line", inlines, [])


def _cell(span: Any, args: dict[str, Any], children: list[Any]) -> N.Command:
    return N.Command(span, "cell", span, EArgs(span, [], args), "env", [], children)  # type: ignore[arg-type]
