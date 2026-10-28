"""Data model of document evaluation (stage 13.3).

The evaluated tree reuses the node classes of :mod:`primula.syntax.nodes`
(so that :mod:`primula.syntax.regions` organises it and later stages read
one set of classes), with these differences:

* ``args`` of a node holds :class:`EArgs` — evaluated argument values —
  instead of :class:`~primula.syntax.pyfrag.PyArgs`;
* control constructs (``|if``, ``|for``, ``|def``, ``|code:``, ``|let``,
  ``|include``, ``|import``, macro calls) are expanded or removed;
* expressions ``|(…)`` are replaced by text or by inserted content;
* formulas ``|=(…)`` stay and carry the environment of their row
  (attribute ``env``, evaluated at stage 13.7);
* blocks excluded by ``when=`` are removed — or, in review mode (9.2,
  ``--review``), kept with the attribute ``condition`` (source text of the
  condition) for marking at stage 13.10.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from primula.core.values import Builtin, Content, to_repr
from primula.source import Span
from primula.syntax.pyfrag import PyArgs


@dataclass(eq=False)
class EArgs:
    """Evaluated arguments of a markup command.

    Attributes:
        span: the argument list in the source (with brackets).
        positional: positional values.
        keywords: keyword values in order.
        source: the parsed arguments (for positions of single arguments).
    """

    span: Span
    positional: list[Any] = field(default_factory=list)
    keywords: dict[str, Any] = field(default_factory=dict)
    source: PyArgs | None = None

    def get(self, name: str, default: Any = None) -> Any:
        """Value of a keyword argument."""
        return self.keywords.get(name, default)

    def dump_text(self) -> str:
        """Text for tree dumps: ``"a.png", height="8mm"`` with values."""
        parts = [to_repr(value) for value in self.positional]
        parts += [f"{name}={to_repr(value)}" for name, value in self.keywords.items()]
        return ", ".join(parts)


@dataclass(eq=False)
class Macro(Builtin):
    """A ``|def`` macro: a function value whose call returns ``content``.

    It is a :class:`~primula.core.values.Builtin` for the interpreter (so
    code can call it, decision 48); ``impl`` is bound by the evaluator.

    Attributes:
        definition: the ``DefBlock`` node.
        closure: environment of the definition (lexical scope).
        file: the :class:`~primula.evaluate.loader.LoadedFile` of the definition.
    """

    definition: Any = None
    closure: Any = None
    file: Any = None


def content_blocks(nodes: list[Any]) -> Content:
    """Content made of blocks (macro body, ``markup()`` result)."""
    return Content(list(nodes), "blocks")


def content_inline(nodes: list[Any]) -> Content:
    """Content made of inline nodes (an inline body ``{…}``)."""
    return Content(list(nodes), "inline")
