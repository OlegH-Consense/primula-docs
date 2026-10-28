"""Python fragments of Primula sources: parsing with :mod:`ast`, positions.

The computing core uses the Python grammar (specification 12.1-12.2,
decision 30: Python 3.11).  Fragments occur in several places:

==========================  ==============================  ==================
Source construct            Text given to ``ast.parse``     Result
==========================  ==============================  ==================
arguments ``(a, k=v)``      ``_(a, k=v)`` (eval)            :class:`PyArgs`
``|(e)``, ``|=(e)``, ...    ``(e)`` (eval)                  :class:`PyExpr`
``|for(t in e)``            ``for t in e: pass``            :class:`PyFor`
``|def name(params):``      ``def name(params): pass``      :class:`PyDef`
``|code:`` block, code      statements, indentation of the  :class:`PyCode`
section of styles/project   opening line removed
==========================  ==============================  ==================

A :class:`PyFragment` keeps the text given to :mod:`ast` together with a
map back to the source file, so that every AST node and every syntax error
gets an exact :class:`~primula.source.Span`.  :mod:`ast` reports node
columns as UTF-8 byte offsets and :class:`SyntaxError` columns as
characters; both are converted here.

Only syntax is checked at this stage, plus the Python 3.11 restriction on
f-strings (no nested quotes of the same kind, PEP 701).  The whitelist of
allowed nodes (specification 12.2) is applied by the computing core
(stage 13.2).
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field

from primula.diagnostics import Diagnostic, error
from primula.source import SourceFile, Span, utf8_column_to_chars
from primula.syntax import pyscan


#: A string prefix containing ``f`` directly before a quote (``f"``, ``rf'``…).
_FSTRING_PREFIX = re.compile(r"(?:[fF][rRbB]?|[rRbB][fF])[\"']")


class PySyntaxError(Exception):
    """A Python fragment cannot be parsed; carries the diagnostic.

    Args:
        diagnostic: the error to report.
    """

    def __init__(self, diagnostic: Diagnostic) -> None:
        super().__init__(diagnostic.code)
        self.diagnostic = diagnostic


@dataclass(eq=False)
class PyFragment:
    """Python text given to :mod:`ast` and its map to the source file.

    Attributes:
        source: the source file.
        text: the text given to :func:`ast.parse` (with wrappers).
        bases: for every line of ``text`` (index = ``lineno - 1``) the
            source offset that corresponds to character column 0 of that
            line.  For a wrapped first line the base lies before the real
            start (the wrapper characters have no source text).
        start: first source offset of the fragment (clamping bound).
        end: source offset after the fragment (clamping bound).
    """

    source: SourceFile
    text: str
    bases: list[int]
    start: int
    end: int
    _lines: list[str] = field(default_factory=list, repr=False)

    def __post_init__(self) -> None:
        self._lines = self.text.split("\n")

    def offset(self, lineno: int, char_column: int) -> int:
        """Map a 1-based line and a 0-based character column to a source offset."""
        index = min(max(lineno, 1), len(self.bases)) - 1
        return min(max(self.bases[index] + char_column, self.start), self.end)

    def byte_offset(self, lineno: int, byte_column: int) -> int:
        """Map a line and a UTF-8 byte column (as in AST nodes) to a source offset."""
        index = min(max(lineno, 1), len(self._lines)) - 1
        return self.offset(lineno, utf8_column_to_chars(self._lines[index], byte_column))

    def span_of(self, node: ast.AST) -> Span:
        """Return the source span of an AST node of this fragment."""
        start = self.byte_offset(node.lineno, node.col_offset)  # type: ignore[attr-defined]
        end_line = getattr(node, "end_lineno", None) or node.lineno  # type: ignore[attr-defined]
        end_column = getattr(node, "end_col_offset", None)
        end = self.byte_offset(end_line, end_column) if end_column is not None else start
        return Span(self.source, start, max(start, end))

    def segment(self, node: ast.AST) -> str:
        """Return the fragment text of an AST node (text given to ``ast``)."""
        return ast.get_source_segment(self.text, node) or ""


@dataclass(eq=False)
class PyArgs:
    """Parsed call arguments ``(…)`` of a command.

    Attributes:
        span: the arguments including both brackets.
        call: the ``ast.Call`` of ``_(…)``; ``args`` and ``keywords`` are the
            positional and keyword arguments.
        fragment: position map.
    """

    span: Span
    call: ast.Call
    fragment: PyFragment

    @property
    def text(self) -> str:
        """Source text between the brackets."""
        return self.span.source.text[self.span.start + 1:self.span.end - 1]

    @property
    def positional(self) -> list[ast.expr]:
        """Positional argument expressions."""
        return list(self.call.args)

    def keyword(self, name: str) -> ast.expr | None:
        """Return the expression of keyword argument ``name``, if present."""
        for keyword in self.call.keywords:
            if keyword.arg == name:
                return keyword.value
        return None

    def keyword_names(self) -> list[str]:
        """Names of keyword arguments in order (``**kwargs`` excluded)."""
        return [keyword.arg for keyword in self.call.keywords if keyword.arg is not None]


@dataclass(eq=False)
class PyExpr:
    """A parsed expression (``|(…)``, ``|=(…)``, conditions, style refs).

    Attributes:
        span: the expression including its brackets.
        node: the expression AST.
        fragment: position map.
    """

    span: Span
    node: ast.expr
    fragment: PyFragment

    @property
    def text(self) -> str:
        """Source text between the brackets."""
        return self.span.source.text[self.span.start + 1:self.span.end - 1]


@dataclass(eq=False)
class PyFor:
    """A parsed loop head ``|for(target in iterable)``.

    Attributes:
        span: the head including its brackets.
        node: ``ast.For`` with ``target`` and ``iter``.
        fragment: position map.
    """

    span: Span
    node: ast.For
    fragment: PyFragment

    @property
    def text(self) -> str:
        """Source text between the brackets."""
        return self.span.source.text[self.span.start + 1:self.span.end - 1]


@dataclass(eq=False)
class PyDef:
    """A parsed macro header ``|def name(params):``.

    Attributes:
        span: ``name(params)`` in the source.
        node: ``ast.FunctionDef`` (body is ``pass``).
        fragment: position map.
    """

    span: Span
    node: ast.FunctionDef
    fragment: PyFragment


@dataclass(eq=False)
class PyCode:
    """A parsed block of statements.

    Attributes:
        span: the code lines in the source.
        module: the ``ast.Module``.
        fragment: position map (indentation removed per line).
    """

    span: Span
    module: ast.Module
    fragment: PyFragment


# ----------------------------------------------------------------------
# Errors
# ----------------------------------------------------------------------


def scan_error(source: SourceFile, exc: pyscan.ScanError) -> Diagnostic:
    """Convert a lexical scan error to a diagnostic (P1204-P1206)."""
    if exc.kind == "unclosed_bracket":
        return error("P1204", Span(source, exc.offset, exc.offset + 1), bracket=source.text[exc.offset])
    if exc.kind == "mismatched_bracket":
        diagnostic = error("P1205", Span(source, exc.offset, exc.offset + 1),
                           found=exc.found, expected=exc.expected)
        if exc.related is not None:
            diagnostic.note("note.opened_here", Span(source, exc.related, exc.related + 1))
        return diagnostic
    return error("P1206", Span(source, exc.offset, exc.offset + 1))


def _syntax_error(fragment: PyFragment, exc: SyntaxError) -> PySyntaxError:
    """Convert :class:`SyntaxError` (columns in characters) to P1207."""
    lineno = exc.lineno or 1
    start = fragment.offset(lineno, max((exc.offset or 1) - 1, 0))
    end = start
    if exc.end_lineno and exc.end_offset:
        end = max(start, fragment.offset(exc.end_lineno, max(exc.end_offset - 1, 0)))
    problem = exc.msg or "invalid syntax"
    return PySyntaxError(error("P1207", Span(fragment.source, start, max(end, start)), problem=problem))


def _parse(fragment: PyFragment, mode: str) -> ast.AST:
    """Run :func:`ast.parse` and check f-strings; raise :class:`PySyntaxError`."""
    try:
        tree = ast.parse(fragment.text, mode=mode, feature_version=(3, 11))
    except SyntaxError as exc:
        raise _syntax_error(fragment, exc) from None
    _check_fstrings(fragment, tree)
    return tree


def _check_fstrings(fragment: PyFragment, tree: ast.AST) -> None:
    """Reject f-strings with nested quotes of their own kind (decision 30).

    Python 3.12+ (PEP 701) reads ``f"{d["k"]}"`` as one f-string; the
    Python 3.11 tokenizer — and Primula — read it as two strings with
    ``k`` between them.  An f-string node whose source text is not made of
    complete string literals for the 3.11 scanner is therefore an error.
    Format specifications (nested ``JoinedStr`` inside ``{x:…}``) are not
    checked separately: they are part of the outer literal.
    """
    if _FSTRING_PREFIX.search(fragment.text) is None:
        return  # no f-string literal at all (the common case)
    nodes = list(ast.walk(tree))
    specs = {id(node.format_spec) for node in nodes
             if isinstance(node, ast.FormattedValue) and node.format_spec is not None}
    for node in nodes:
        if isinstance(node, ast.JoinedStr) and id(node) not in specs:
            text = fragment.segment(node)
            if text and not pyscan.strings_only(text):
                raise PySyntaxError(error("P1208", fragment.span_of(node)))


# ----------------------------------------------------------------------
# Fragment constructors
# ----------------------------------------------------------------------


def _wrapped(source: SourceFile, inner_start: int, inner_end: int, prefix: str,
             suffix: str) -> PyFragment:
    """Build a fragment ``prefix + source[inner_start:inner_end] + suffix``.

    The prefix sits on the first line, so the base of the first line is
    shifted left by its length; following lines map to their source lines.
    """
    inner = source.text[inner_start:inner_end]
    text = prefix + inner + suffix
    bases = [inner_start - len(prefix)]
    position = inner_start
    while True:
        newline = source.text.find("\n", position, inner_end)
        if newline == -1:
            break
        bases.append(newline + 1)
        position = newline + 1
    return PyFragment(source, text, bases, inner_start, inner_end)


def parse_args(source: SourceFile, open_offset: int, close_offset: int) -> PyArgs:
    """Parse command arguments between brackets.

    Args:
        source: the source file.
        open_offset: offset of ``(``.
        close_offset: offset of the matching ``)``.

    Returns:
        The parsed arguments.

    Raises:
        PySyntaxError: invalid argument syntax (P1207, P1208).
    """
    fragment = _wrapped(source, open_offset + 1, close_offset, "_(", ")")
    tree = _parse(fragment, "eval")
    call = tree.body  # type: ignore[attr-defined]
    return PyArgs(Span(source, open_offset, close_offset + 1), call, fragment)


def parse_expr(source: SourceFile, open_offset: int, close_offset: int) -> PyExpr:
    """Parse an expression between brackets (``|(…)``, ``|=(…)``, conditions).

    Raises:
        PySyntaxError: invalid syntax or an empty expression (P1207, P1208).
    """
    fragment = _wrapped(source, open_offset + 1, close_offset, "(", ")")
    if not source.text[open_offset + 1:close_offset].strip():
        raise PySyntaxError(error("P1207", Span(source, open_offset, close_offset + 1),
                                  problem="empty expression"))
    tree = _parse(fragment, "eval")
    return PyExpr(Span(source, open_offset, close_offset + 1), tree.body, fragment)  # type: ignore[attr-defined]


def parse_for(source: SourceFile, open_offset: int, close_offset: int) -> PyFor:
    """Parse a loop head ``target in iterable`` between brackets.

    Raises:
        PySyntaxError: not of the form ``target in expression`` (P1207).
    """
    fragment = _wrapped(source, open_offset + 1, close_offset, "for ", ": pass")
    tree = _parse(fragment, "exec")
    body = tree.body  # type: ignore[attr-defined]
    if len(body) != 1 or not isinstance(body[0], ast.For):  # pragma: no cover - guaranteed by syntax
        raise PySyntaxError(error("P1207", Span(source, open_offset, close_offset + 1),
                                  problem="expected 'target in expression'"))
    return PyFor(Span(source, open_offset, close_offset + 1), body[0], fragment)


def parse_def(source: SourceFile, name_start: int, close_offset: int) -> PyDef:
    """Parse a macro header ``name(params)`` (``|def`` already consumed).

    Args:
        source: the source file.
        name_start: offset of the macro name.
        close_offset: offset of the ``)`` closing the parameters.

    Raises:
        PySyntaxError: invalid parameters (P1207).
    """
    fragment = _wrapped(source, name_start, close_offset + 1, "def ", ": pass")
    tree = _parse(fragment, "exec")
    node = tree.body[0]  # type: ignore[attr-defined]
    return PyDef(Span(source, name_start, close_offset + 1), node, fragment)


def parse_code(source: SourceFile, lines: list[tuple[int, int, str]], span: Span) -> PyCode:
    """Parse a block of statements.

    Args:
        source: the source file.
        lines: for every code line ``(line_start_offset, removed_indent,
            text)``; ``text`` is the line without the removed indentation.
        span: span of the code lines.

    Raises:
        PySyntaxError: invalid syntax (P1207, P1208).
    """
    text = "\n".join(line_text for _, _, line_text in lines)
    bases = [line_start + indent for line_start, indent, _ in lines] or [span.start]
    fragment = PyFragment(source, text, bases, span.start, span.end)
    tree = _parse(fragment, "exec")
    return PyCode(span, tree, fragment)  # type: ignore[arg-type]
