"""Errors of the computing core (specification 12.9, codes ``P2xxx``).

A runtime error is a :class:`CoreError` that carries a diagnostic.  While
the error propagates out of function calls, every call adds a stack frame
(``frame.call`` — the call site), so the message shows the chain of calls
through the code (and, from stage 13.3, through ``|include``, ``|import``
and macros).

Code groups (see ``docs/dev/diagnostics.md``):

* ``P21xx`` — static check of the AST against the whitelist (12.2);
* ``P22xx`` — names and global definitions (10.4, 12.7);
* ``P23xx`` — types, values and operations (12.3-12.6, 12.10);
* ``P24xx`` — limits (12.8);
* ``P25xx`` — warnings of the core linter.
"""

from __future__ import annotations

from typing import Any

from primula.diagnostics import Diagnostic, error
from primula.source import Span


class Where:
    """A lazily computed position: a node of a Python fragment.

    The interpreter passes ``Where`` objects instead of spans: the span is
    computed only when a diagnostic is created (converting AST byte columns
    is far more expensive than evaluating a node).

    Args:
        frag: the :class:`~primula.syntax.pyfrag.PyFragment`.
        node: the AST node.
    """

    __slots__ = ("frag", "node", "_span")

    def __init__(self, frag: Any, node: Any) -> None:
        self.frag = frag
        self.node = node
        self._span: Span | None = None

    def __call__(self) -> Span:
        if self._span is None:
            self._span = self.frag.span_of(self.node)
        return self._span


def resolve(span: "Span | Where | None") -> Span | None:
    """A span from a span or a :class:`Where` (``None`` stays ``None``)."""
    return span() if isinstance(span, Where) else span


class CoreError(Exception):
    """A runtime or static error of the core.

    Args:
        diagnostic: the diagnostic to report.
    """

    def __init__(self, diagnostic: Diagnostic) -> None:
        super().__init__(diagnostic.code)
        self.diagnostic = diagnostic

    def add_frame(self, kind: str, span: "Span | Where", name: str = "") -> "CoreError":
        """Append an outer call stack frame; returns ``self``."""
        self.diagnostic.frame(kind, resolve(span), name)  # type: ignore[arg-type]
        return self


def core_error(code: str, span: "Span | Where | None", **args: object) -> CoreError:
    """Create a :class:`CoreError` with an error diagnostic.

    Args:
        code: diagnostic code.
        span: position of the failing construct (a span or :class:`Where`).
        **args: message arguments.
    """
    return CoreError(error(code, resolve(span), **args))


class LimitError(CoreError):
    """A limit of section 12.8 was exceeded (``P24xx``)."""
