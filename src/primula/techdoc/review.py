"""Marks of the ``--review`` mode (9.2, decision 116).

The evaluator keeps every conditional fragment in this mode and records on
each block ``review = (label, truth)``: ``label`` is «when: has("wifi")»,
«if: …», «elif: …» or «else», ``truth`` — whether the fragment is in the
current variant.  Inline ``|if`` branches are wrapped by the evaluator in
the character styles ``ReviewTrue``/``ReviewFalse`` with a Writer comment.

Here, before the styles are applied (:meth:`ReviewMarks.before_styles`):

* a block gets a label paragraph ``ReviewLabel`` before it:
  «[when: has("wifi")] — так» / «— ні» (words of ``review_marks``);
* a table row gets the background of its cells (the cascade of 6.6).

After the styles (:meth:`ReviewMarks.after_styles`) every paragraph of a
marked block gets the background of ``ReviewTrue``/``ReviewFalse``: green —
the condition holds in the current variant, red — the fragment is here only
because of ``--review``.
"""

from __future__ import annotations

from typing import Any, Callable

from primula.evaluate.model import EArgs
from primula.structure.tree import iter_tree
from primula.syntax import nodes as N
from primula.techdoc.texts import REVIEW, by_language

#: Backgrounds when the styles ReviewTrue/ReviewFalse have none.
DEFAULT_COLORS = {True: "#D9F2D9", False: "#F8D7D7"}


class ReviewMarks:
    """Labels and backgrounds of the ``--review`` mode.

    Args:
        settings: merged settings (``review_marks``).
        effective: ``effective(style) -> properties`` of the style system.
        lang: language code.
    """

    def __init__(self, settings: dict[str, Any], effective: Callable[[str], dict[str, Any]], lang: str) -> None:
        self.words = by_language(REVIEW, settings.get("review_marks"), lang)
        self.colors = {truth: effective("ReviewTrue" if truth else "ReviewFalse").get("background")
                       or DEFAULT_COLORS[truth] for truth in (True, False)}
        self.marked: list[tuple[Any, bool]] = []

    @property
    def watermark(self) -> str:
        return self.words["watermark"]

    # --- before the styles --------------------------------------------------------------

    def before_styles(self, document: N.Document) -> None:
        document.children = self._blocks(document.children)

    def _blocks(self, blocks: list[Any]) -> list[Any]:
        out: list[Any] = []
        for block in blocks:
            mark = getattr(block, "review", None)
            if isinstance(block, (N.TableRow,)) or (isinstance(block, N.Command) and block.name == "row"):
                if mark is not None:
                    self._row(block, mark[1])
                out.append(block)
                continue
            if mark is not None:
                label, truth, first = mark if len(mark) == 3 else (*mark, True)
                if first:
                    word = self.words["true" if truth else "false"]
                    text = f"[{label}] — {word}"
                    out.append(N.StyleBlock(block.span, N.StyleRef(block.span, "ReviewLabel"), None, "line",
                                            [N.Text(block.span, text)], []))
                self.marked.append((block, truth))
            self._descend(block)
            out.append(block)
        return out

    def _descend(self, block: Any) -> None:
        children = getattr(block, "children", None)
        if isinstance(children, list) and children:
            block.children = self._blocks(children)
        if isinstance(block, N.ListBlock):
            for item in block.items:
                if item.children:
                    item.children = self._blocks(item.children)

    def _row(self, row: Any, truth: bool) -> None:
        """A conditional table row: the background of its cells."""
        args = row.args if isinstance(row.args, EArgs) else EArgs(row.span, [], {})
        args.keywords = {**args.keywords, "background": self.colors[truth]}
        row.args = args

    # --- after the styles ----------------------------------------------------------------

    def after_styles(self) -> None:
        for block, truth in self.marked:
            for node in iter_tree([block]):
                use = getattr(node, "style_use", None)
                if use is not None and hasattr(use, "extra"):
                    # A new object: a StyleUse may be shared by several nodes.
                    node.style_use = type(use)(use.parent, {**use.extra, "background": self.colors[truth]})
