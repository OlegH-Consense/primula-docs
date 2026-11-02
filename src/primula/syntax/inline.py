"""Inline parsing: text, escapes, short forms, commands, bodies (grammar §4).

:class:`InlineParser` holds the parser state shared with the block parser
(:mod:`primula.syntax.blocks` subclasses it): the source, the current offset
``pos`` and the diagnostics sink.

The character after ``|`` decides the construct by syntax alone
(specification 3.1, grammar section 5):

========================  ===========================================
after ``|``               construct
========================  ===========================================
``|``, ``{``, ``}``       literal character
``;``                     empty separator (no output)
``~``                     no-break space (U+00A0)
``\\``                    line break
``%``                     comment to the end of the line
``(``                     expression ``|(…)``
``=``                     formula ``|=(…)`` (table cells only)
``@``                     reference ``|@(…)``
``.``                     character style ``|.Name{…}`` / ``|.(e){…}``
``* / _ ^ , ` " ?`` ``—``  short forms with a body
``&``                     cell separator (table rows only)
letter (``XID_Start``)    long command; ``if``/``for`` — inline forms
``< > - # ! :``           line-start forms: error in the middle of a line
``–``, ``−`` and similar  error with a hint about ``|—``
other ``P*``/``S*``       undefined short form: error (reserved, 3.1)
other                     error
========================  ===========================================

Where content ends depends on the context (:class:`Context`):

* a ``{…}`` body ends at its matching ``}``; inside, line breaks are spaces
  and nested ``{}`` are counted as text (grammar ``BodyItem``);
* a line form (clause, list item, row, line body, heading) ends at the end
  of the line (section 3.4);
* a paragraph continues on the following lines until a blank line or a
  line that :func:`~primula.syntax.lines.classify` recognises as a block;
  comment-only lines are skipped;
* a compact table row cell also ends at ``|&``.

Text normalisation (section 4.1): a line break inside a paragraph or body
and the indentation after it become one space; spaces before a line break
and at the end of the content are dropped.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from primula.diagnostics import Diagnostic, DiagnosticSink, error, warning
from primula.i18n import Key
from primula.source import SourceFile, Span
from primula.syntax import lines as L
from primula.syntax import pyfrag, pyscan
from primula.syntax.nodes import (
    Comment, Expr, Formula, Inline, InlineBranch, InlineCommand, InlineFor, InlineIf,
    LineBreak, Reference, Short, StyleRef, StyleSpan, Text,
)
from primula.syntax.pyfrag import PyArgs, PyExpr
from primula.unicode import is_short_char

#: Marks of inline short forms with a body (section 3.3).
SHORT_MARKS = frozenset("*/_^,`\"?—")
#: Line-start short forms (error in the middle of a line).
LINE_START_MARKS = frozenset("<>-#!:")
#: Characters similar to the em dash (error with a hint about ``|—``).
DASH_LIKE = frozenset("‐‑‒–―−")
#: Names that are only valid as block constructs at the start of a line.
BLOCK_ONLY_NAMES = frozenset({"end", "endif", "endfor", "enddef", "code", "comment",
                              "verbatim", "def", "parallel", "segment"})
#: Characters of horizontal whitespace (grammar ``WS``).
WS = " \t"


@dataclass(frozen=True)
class Context:
    """Where inline content ends and which forms are allowed.

    Attributes:
        multiline: continue on following text lines (paragraph, body);
            otherwise stop at the end of the line.
        body: inside ``{…}``: stop at the matching ``}``.
        row: in a compact table row: stop at ``|&`` outside bodies.
        cell: inside a table cell: formulas ``|=(…)`` are allowed.
    """

    multiline: bool = False
    body: bool = False
    row: bool = False
    cell: bool = False


class _TextBuffer:
    """Accumulates literal text pieces into one :class:`Text` node."""

    def __init__(self) -> None:
        self.parts: list[str] = []
        self.start = -1
        self.end = -1

    def add(self, value: str, start: int, end: int) -> None:
        if self.start < 0:
            self.start = start
        self.parts.append(value)
        self.end = end

    def rstrip(self) -> None:
        """Drop trailing spaces and tabs (not U+00A0)."""
        while self.parts:
            stripped = self.parts[-1].rstrip(WS)
            if stripped:
                self.parts[-1] = stripped
                return
            self.parts.pop()

    def flush(self, source: SourceFile, out: list[Inline]) -> None:
        if self.parts:
            out.append(Text(Span(source, self.start, max(self.end, self.start)), "".join(self.parts)))
        self.parts = []
        self.start = self.end = -1


class InlineParser:
    """Parser state and inline-level parsing.

    Args:
        source: the source file.
        sink: diagnostics receiver.
    """

    def __init__(self, source: SourceFile, sink: DiagnosticSink) -> None:
        self.source = source
        self.text = source.text
        self.sink = sink
        self.pos = 0
        #: Inside ``|comment:``: inline content is not parsed, only skipped
        #: to the end of the line (section 3.7: only environment balance is
        #: checked there, so an unclosed ``{`` must not swallow lines).
        self.opaque = False

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def span(self, start: int, end: int | None = None) -> Span:
        """Span ``[start, end)`` in the source (``end`` defaults to ``start``)."""
        return Span(self.source, start, start if end is None else end)

    def emit(self, diagnostic: Diagnostic) -> None:
        """Report a diagnostic."""
        self.sink.emit(diagnostic)

    def peek(self, offset: int = 0) -> str:
        """Character at ``pos + offset`` or ``""`` at the end."""
        index = self.pos + offset
        return self.text[index] if index < len(self.text) else ""

    def line_end(self, position: int | None = None) -> int:
        """Offset of the LF ending the line of ``position`` (or end of text)."""
        newline = self.text.find("\n", self.pos if position is None else position)
        return len(self.text) if newline == -1 else newline

    def skip_to_line_end(self) -> None:
        """Move ``pos`` to the end of the current line (recovery)."""
        self.pos = self.line_end()

    def find_closing(self, open_offset: int) -> int | None:
        """Find the matching bracket; report scan errors and return ``None``."""
        try:
            return pyscan.find_closing(self.text, open_offset)
        except pyscan.ScanError as exc:
            self.emit(pyfrag.scan_error(self.source, exc))
            return None

    def parse_args_at(self, open_offset: int) -> PyArgs | None:
        """Parse ``(…)`` arguments at ``open_offset``; move ``pos`` after them.

        On a scan error ``pos`` moves to the end of the line; on a Python
        syntax error it moves after the closing bracket.  Both are reported
        and ``None`` is returned.
        """
        close = self.find_closing(open_offset)
        if close is None:
            self.skip_to_line_end()
            return None
        self.pos = close + 1
        try:
            return pyfrag.parse_args(self.source, open_offset, close)
        except pyfrag.PySyntaxError as exc:
            self.emit(exc.diagnostic)
            return None

    def parse_expr_at(self, open_offset: int) -> PyExpr | None:
        """Parse a bracketed expression at ``open_offset`` (as :meth:`parse_args_at`)."""
        close = self.find_closing(open_offset)
        if close is None:
            self.skip_to_line_end()
            return None
        self.pos = close + 1
        try:
            return pyfrag.parse_expr(self.source, open_offset, close)
        except pyfrag.PySyntaxError as exc:
            self.emit(exc.diagnostic)
            return None

    def parse_for_at(self, open_offset: int) -> pyfrag.PyFor | None:
        """Parse a bracketed loop head at ``open_offset``."""
        close = self.find_closing(open_offset)
        if close is None:
            self.skip_to_line_end()
            return None
        self.pos = close + 1
        try:
            return pyfrag.parse_for(self.source, open_offset, close)
        except pyfrag.PySyntaxError as exc:
            self.emit(exc.diagnostic)
            return None

    def optional_args(self) -> PyArgs | None:
        """Parse arguments if ``(`` follows directly."""
        if self.peek() == "(":
            return self.parse_args_at(self.pos)
        return None

    # ------------------------------------------------------------------
    # Content sequences
    # ------------------------------------------------------------------

    def parse_inlines(self, context: Context) -> list[Inline]:
        """Parse inline content from ``pos`` until the end given by ``context``.

        On return ``pos`` is at the stop point: the ``}`` of a body, the
        ``|&`` of a row cell, or the LF / end of text that ends the content
        (the LF itself is not consumed).

        Args:
            context: stop rules and allowed forms.

        Returns:
            Inline nodes with normalised text.
        """
        if self.opaque:
            self.skip_to_line_end()
            return []
        out: list[Inline] = []
        buffer = _TextBuffer()
        text = self.text
        brace_depth = 0  # nested text braces inside a body
        while self.pos < len(text):
            char = text[self.pos]
            if char == "\n":
                after_break = not buffer.parts and bool(out) and isinstance(out[-1], LineBreak)
                if not self._continue_line(context, buffer, after_break):
                    break
                continue
            if char == "|":
                if context.row and not context.body and self.peek(1) == "&":
                    break
                self._parse_bar(context, buffer, out)
                continue
            if context.body:
                if char == "{":
                    brace_depth += 1
                elif char == "}":
                    if brace_depth == 0:
                        break
                    brace_depth -= 1
            # Plain text run up to the next special character.
            start = self.pos
            self.pos += 1
            while self.pos < len(text) and text[self.pos] not in "|\n{}":
                self.pos += 1
            buffer.add(text[start:self.pos], start, self.pos)
        if not context.body:
            # Spaces at the end of a paragraph or line form carry no
            # meaning (4.1); inside a body they are content ("|(x), ").
            buffer.rstrip()
        buffer.flush(self.source, out)
        if not context.body:
            _strip_trailing(out)
        return out

    def _continue_line(self, context: Context, buffer: _TextBuffer, after_break: bool = False) -> bool:
        """Handle a LF inside content; return ``False`` if the content ends.

        The LF becomes a space (4.1), except right after a line break
        ``|\\``: there the new output line would start with a space.

        Inside a body the content always continues (grammar ``BodyItem``
        allows line breaks), except when the next line can only be a block:
        that is recovery from an unclosed ``{`` (:data:`lines.BLOCK_ONLY`).
        A multiline context continues on text lines.  Comment-only lines
        are skipped in both cases (decision 23); ``pos`` is left at the LF
        when the content ends, so the block parser sees those lines again.
        """
        newline = self.pos
        next_line = newline + 1
        while True:
            if next_line >= len(self.text):
                return False
            info = L.classify(self.text, next_line)
            if info.kind is L.Kind.COMMENT and (context.body or context.multiline):
                next_line = self.line_end(info.content) + 1
                continue
            break
        if context.body:
            if info.kind in L.BLOCK_ONLY:
                return False
        elif not context.multiline or info.kind is not L.Kind.TEXT:
            return False
        buffer.rstrip()
        if not after_break:
            buffer.add(" ", newline, newline + 1)
        self.pos = info.content
        return True

    # ------------------------------------------------------------------
    # Constructs after '|'
    # ------------------------------------------------------------------

    def _parse_bar(self, context: Context, buffer: _TextBuffer, out: list[Inline]) -> None:
        """Parse one construct starting with ``|`` at ``pos``."""
        start = self.pos
        char = self.peek(1)
        literal = {"|": "|", "{": "{", "}": "}", "~": " "}
        if char in literal:
            buffer.add(literal[char], start, start + 2)
            self.pos += 2
            return
        if char == ";":
            self.pos += 2
            return
        if char == "%":
            end = self.line_end()
            buffer.rstrip()
            buffer.flush(self.source, out)
            out.append(Comment(self.span(start, end), self.text[start + 2:end]))
            self.pos = end
            return

        buffer.flush(self.source, out)
        node = self._parse_construct(context, start, char)
        if node is not None:
            out.append(node)

    def _parse_construct(self, context: Context, start: int, char: str) -> Inline | None:
        """Parse a non-literal construct; return a node or ``None`` after an error."""
        if char == "\\":
            self.pos += 2
            return LineBreak(self.span(start, self.pos))
        if char == "(":
            self.pos += 1
            expr = self.parse_expr_at(start + 1)
            return Expr(self.span(start, self.pos), expr) if expr is not None else None
        if char == "=":
            return self._parse_formula(context, start)
        if char == "@":
            self.pos += 2
            if self.peek() != "(":
                self.emit(error("P1242", self.span(start, start + 2), expected=Key("expect.paren"), after="|@"))
                return None
            args = self.parse_args_at(self.pos)
            if args is not None and self.peek() == "{":
                # A reference has no body (5.7, decision 141): the braces are printed as text, which is
                # usually a body that was meant for |link or a leftover of an edit.
                self.emit(warning("P1245", self.span(self.pos, self.pos + 1)))
            return Reference(self.span(start, self.pos), args) if args is not None else None
        if char == ".":
            return self._parse_style_span(context, start)
        if char in SHORT_MARKS:
            return self._parse_short(context, start, char)
        if char == "&":
            self.pos += 2
            self.emit(error("P1227", self.span(start, start + 2)))
            return None
        if L.is_name_start(char):
            return self._parse_command(context, start)
        return self._bad_bar(start, char)

    def _bad_bar(self, start: int, char: str) -> None:
        """Report an invalid character after ``|`` and skip the ``|``."""
        if char in LINE_START_MARKS:
            diagnostic = error("P1210", self.span(start, start + 2), form=char)
            if char == "-":
                diagnostic.hint("help.em_dash")
            self.emit(diagnostic)
            self.pos += 2
        elif char in DASH_LIKE:
            self.emit(error("P1203", self.span(start, start + 2), char=char).hint("help.em_dash"))
            self.pos += 2
        elif char and is_short_char(char):
            # ShortChar (3.1): ASCII punctuation or P*/S*; undefined forms
            # are reserved for future versions.
            self.emit(error("P1202", self.span(start, start + 2), char=char))
            self.pos += 2
        else:
            found = Key("expect.line_end") if char in ("", "\n") else repr(char)
            self.emit(error("P1201", self.span(start, start + 1), found=found).hint("help.literal_bar"))
            self.pos += 1
        return None

    def _parse_formula(self, context: Context, start: int) -> Formula | None:
        """``|=(expr)`` — allowed only in a table cell (section 6.8)."""
        self.pos += 2
        if self.peek() != "(":
            self.emit(error("P1242", self.span(start, start + 2), expected=Key("expect.paren"), after="|="))
            return None
        expr = self.parse_expr_at(self.pos)
        if not context.cell:
            self.emit(error("P1228", self.span(start, self.pos)))
        return Formula(self.span(start, self.pos), expr) if expr is not None else None

    def parse_inline_body(self, context: Context) -> list[Inline] | None:
        """Parse ``{…}`` at ``pos`` (``pos`` must be at ``{``).

        Returns:
            The body content; ``None`` was never returned — an unclosed body
            is reported (P1215) and its content kept.
        """
        open_offset = self.pos
        self.pos += 1
        body_context = replace(context, body=True, multiline=True)
        content = self.parse_inlines(body_context)
        if self.peek() == "}":
            self.pos += 1
        else:
            self.emit(error("P1215", self.span(open_offset, open_offset + 1)))
        return content

    def _require_body(self, context: Context, start: int, form: str) -> list[Inline] | None:
        """Parse a mandatory ``{…}`` body or report P1209."""
        if self.peek() == "{":
            return self.parse_inline_body(context)
        self.emit(error("P1209", self.span(start, self.pos), form=form))
        return None

    def _parse_short(self, context: Context, start: int, mark: str) -> Short | None:
        """``|*{…}`` and the other short forms with a body."""
        self.pos += 2
        args = self.optional_args()
        body = self._require_body(context, start, mark)
        if body is None:
            return None
        return Short(self.span(start, self.pos), mark, args, body)

    def parse_style_ref(self, start: int) -> StyleRef | None:
        """Parse a style reference after ``|.`` (``pos`` after the dot)."""
        if self.peek() == "(":
            expr = self.parse_expr_at(self.pos)
            if expr is None:
                return None
            return StyleRef(self.span(start, self.pos), None, expr)
        end = L.scan_style_name(self.text, self.pos)
        if end == self.pos:
            self.emit(error("P1242", self.span(start, self.pos), expected=Key("expect.style_name"), after="|."))
            return None
        name = self.text[self.pos:end]
        self.pos = end
        return StyleRef(self.span(start + 2, end), name)

    def _parse_style_span(self, context: Context, start: int) -> StyleSpan | None:
        """``|.Name{…}`` / ``|.(expr){…}`` — character style."""
        self.pos += 2
        style = self.parse_style_ref(start)
        if style is None:
            return None
        args = self.optional_args()
        if self.peek() == ":":
            self.emit(error("P1210", self.span(start, self.pos + 1), form=".Name:"))
            return None
        body = self._require_body(context, start, "." + (style.name or "(…)"))
        if body is None:
            return None
        return StyleSpan(self.span(start, self.pos), style, args, body)

    def _parse_command(self, context: Context, start: int) -> Inline | None:
        """``|name(args){body}``, ``|if…``, ``|for…`` inside text."""
        name_start = start + 1
        name_end = L.scan_name(self.text, name_start)
        name = self.text[name_start:name_end]
        name_span = self.span(name_start, name_end)
        self.pos = name_end
        following = self.peek()
        if following and following.isalpha():
            self.emit(error("P1211", self.span(start, name_end + 1), name=name).hint("help.separator"))

        if name == "if":
            return self._parse_inline_if(context, start)
        if name == "for":
            return self._parse_inline_for(context, start)
        if name in ("else", "elif"):
            self.emit(error("P1220", self.span(start, name_end), form=name))
            if name == "elif" and self.peek() == "(":
                self.parse_expr_at(self.pos)
            if self.peek() == "{":
                self.parse_inline_body(context)
            return None
        if name.split(".")[0] in BLOCK_ONLY_NAMES:
            self.emit(error("P1210", self.span(start, name_end), form=name))
            return None

        args = self.optional_args()
        body = self.parse_inline_body(context) if self.peek() == "{" else None
        return InlineCommand(self.span(start, self.pos), name, name_span, args, body)

    def _parse_inline_if(self, context: Context, start: int) -> InlineIf | None:
        """``|if(c){…}`` followed by ``|elif(c){…}`` / ``|else{…}`` (decision 21)."""
        node = InlineIf(self.span(start, start))
        branch = self._inline_branch(context, start, "if")
        if branch is None:
            return None
        node.branches.append(branch)
        # The chain ends after '|else{…}': a following '|elif'/'|else' is
        # not part of it and is reported by the command parser (P1220).
        while node.branches[-1].keyword != "else":
            save = self.pos
            self.pos = L.skip_ws(self.text, self.pos)
            if self.text.startswith("|elif", self.pos) and not L.is_ident_char(self.peek(5)):
                branch = self._inline_branch(context, self.pos, "elif")
            elif self.text.startswith("|else", self.pos) and not L.is_ident_char(self.peek(5)):
                branch = self._inline_branch(context, self.pos, "else")
            else:
                self.pos = save
                break
            if branch is None:
                break
            node.branches.append(branch)
        node.span = self.span(start, self.pos)
        return node

    def _inline_branch(self, context: Context, start: int, keyword: str) -> InlineBranch | None:
        """Parse one branch: keyword, condition (except ``else``), body."""
        self.pos = start + 1 + len(keyword)
        cond = None
        if keyword != "else":
            if self.peek() != "(":
                self.emit(error("P1242", self.span(start, self.pos), expected=Key("expect.paren"), after="|" + keyword))
                return None
            cond = self.parse_expr_at(self.pos)
        body = self._require_body(context, start, keyword + ("(…)" if keyword != "else" else ""))
        if body is None:
            return None
        node = InlineBranch(self.span(start, self.pos), cond, body)
        node.keyword = keyword
        return node

    def _parse_inline_for(self, context: Context, start: int) -> InlineFor | None:
        """``|for(x in items){…}`` (decision 21)."""
        if self.peek() != "(":
            self.emit(error("P1242", self.span(start, self.pos), expected=Key("expect.paren"), after="|for"))
            return None
        loop = self.parse_for_at(self.pos)
        body = self._require_body(context, start, "for(…)")
        if loop is None or body is None:
            return None
        return InlineFor(self.span(start, self.pos), loop, body)


def _strip_trailing(out: list[Inline]) -> None:
    """Drop trailing whitespace of the content (section 4.1)."""
    while out and isinstance(out[-1], Text):
        value = out[-1].value.rstrip(WS)
        if value:
            out[-1].value = value
            return
        out.pop()
