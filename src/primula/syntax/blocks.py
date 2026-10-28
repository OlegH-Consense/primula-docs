"""Block-level parsing: lines, line forms, environments, closing (grammar §3).

:class:`BlockParser` extends :class:`~primula.syntax.inline.InlineParser`
with the block level.  It reads the body of a file line by line; each line
is dispatched by :func:`~primula.syntax.lines.classify` (the ordered choice
of ``Block``).  The result is a *flat* list of blocks per container: the
implicit regions of ``|>`` and ``|!`` and the grouping of list items are
built afterwards by :mod:`primula.syntax.regions`, because ``|include`` is
transparent for regions (decision 31) and the final grouping is computed
again after fragments are inserted (stage 13.3).

Environments and closing (section 3.5, decisions 28 and 34):

* every open environment is a :class:`Frame` on a stack;
* ``|end`` closes the innermost environment, but never ``|if``/``|for``/
  ``|def`` (error P1219); tagged markers (``|end>``, ``|end!``,
  ``|end.Name``, ``|end name``, ``|endif``…) close the innermost matching
  environment; environments above it are reported as not closed (P1216);
* a marker that matches nothing is an error (P1217/P1218) and is skipped;
* at the end of the file every open environment is reported (P1216).

Restrictions checked here: table and row content (grammar 3.5), table rows
only in tables, headings inside clause environments (5.3), headings and
clauses inside list environments (decision 33), reserved macro names (B.3),
indentation of code and verbatim blocks (decision 24).
"""

from __future__ import annotations

import ast
import keyword
from dataclasses import dataclass

from primula.diagnostics import Diagnostic, DiagnosticSink, error, warning
from primula.i18n import Key
from primula.header import Header
from primula.source import Span
from primula.syntax import lines as L
from primula.syntax import pyfrag
from primula.syntax.inline import WS, Context, InlineParser
from primula.syntax.nodes import (
    Admonition, BlankLine, Block, Cell, Clause, CodeBlock, Command, Comment, CommentBlock,
    DefBlock, ForBlock, Heading, IfBlock, IfBranch, ListItem, Paragraph, StyleBlock, StyleRef,
    TableRow, Verbatim,
)

#: Threshold of the anonymous ``|end`` warning, in lines (decision 35).
LONG_ENVIRONMENT_LINES = 30

#: Built-in command names (appendix 2.1); they cannot be redefined.
BUILTIN_COMMANDS = frozenset({
    "table", "row", "cell", "caption", "page", "newpage", "newcolumn", "section", "header",
    "footer", "field", "img", "figure", "frame", "watermark", "include", "import", "document",
    "part", "scope", "appendix", "toc", "list_of", "footnote", "endnote", "set", "block",
    "list", "fmt", "abbr", "index", "link", "toc_entry", "export", "let", "call", "code", "comment", "verbatim",
    "if", "elif", "else", "for", "def", "parallel", "segment", "track",
})

#: Reserved names that user definitions may not use (appendix 2.2).
RESERVED_NAMES = (frozenset({"if", "elif", "else", "endif", "for", "endfor", "def", "enddef",
                             "let", "code", "end", "comment", "verbatim"})
                  | frozenset(keyword.kwlist) | BUILTIN_COMMANDS)

#: Kinds of blocks allowed directly in a table and in a row (grammar 3.5).
_TABLE_KINDS = frozenset({L.Kind.ROW, L.Kind.IF, L.Kind.FOR, L.Kind.CODE, L.Kind.COMMENT,
                          L.Kind.COMMENT_BLOCK, L.Kind.BLANK})
_ROW_KINDS = frozenset({L.Kind.IF, L.Kind.FOR, L.Kind.CODE, L.Kind.COMMENT,
                        L.Kind.COMMENT_BLOCK, L.Kind.BLANK})
#: Kinds of blocks allowed directly in ``|parallel`` (7.7, grammar 3.5a).
_PARALLEL_KINDS = frozenset({L.Kind.SEGMENT, L.Kind.IF, L.Kind.FOR, L.Kind.CODE, L.Kind.COMMENT,
                             L.Kind.COMMENT_BLOCK, L.Kind.BLANK})
#: Line commands allowed directly in ``|parallel``: fragments of segments and
#: page breaks between segments (7.7).
_PARALLEL_COMMANDS = frozenset({"include", "page", "newpage"})
_CONTROL = frozenset({"if", "for", "def"})
#: Diagnostics that remain inside ``|comment:`` (balance only, section 3.7).
_BALANCE_CODES = frozenset({"P1216", "P1217", "P1218", "P1219", "P1223", "P1224"})


@dataclass(eq=False)
class Frame:
    """An open environment.

    Attributes:
        kind: ``root``, ``clause``, ``admonition``, ``style``, ``command``,
            ``if``, ``for``, ``def``, ``comment``.
        name: command name (``command``), static style name (``style``).
        level: clause level.
        opener: span of the opening marker.
        line: line number of the opening line.
        closed: a closing marker was consumed for this frame.
        close_span: span of that marker.
    """

    kind: str
    opener: Span
    line: int
    name: str = ""
    level: int = 0
    closed: bool = False
    close_span: Span | None = None

    def canonical_close(self) -> str:
        """The closing marker that matches this frame (for messages)."""
        if self.kind == "clause":
            return "|end" + ">" * self.level
        if self.kind == "admonition":
            return "|end!"
        if self.kind == "style":
            return f"|end.{self.name}" if self.name else "|end style"
        if self.kind in _CONTROL:
            return f"|end{self.kind}"
        if self.kind == "comment":
            return "|end comment"
        return f"|end {self.name}"

    def opener_text(self) -> str:
        """The opening construct, for messages (``|>``, ``|table``…)."""
        return {"clause": "|" + ">" * self.level, "admonition": "|!", "if": "|if",
                "for": "|for", "def": "|def", "comment": "|comment",
                "style": f"|.{self.name or '(…)'}"}.get(self.kind, f"|{self.name}")


class _BalanceSink(DiagnosticSink):
    """Sink used inside ``|comment:``: only balance errors pass through."""

    def __init__(self, target: DiagnosticSink) -> None:
        super().__init__(strict=target.strict, error_limit=0)
        self.target = target

    def emit(self, diagnostic: Diagnostic) -> Diagnostic:  # noqa: D102
        if diagnostic.code in _BALANCE_CODES:
            return self.target.emit(diagnostic)
        return diagnostic


@dataclass
class _CloseTag:
    """A parsed closing marker: ``kind`` as :class:`Frame` kinds or ``anon``."""

    kind: str
    name: str = ""
    level: int = 0


class BlockParser(InlineParser):
    """Parses the body of a markup file into flat block lists.

    Args:
        header: the parsed header (kind, body start).
        sink: diagnostics receiver.
    """

    def __init__(self, header: Header, sink: DiagnosticSink) -> None:
        super().__init__(header.source, sink)
        self.header = header
        self.stack: list[Frame] = []
        #: Index of the frame the parser unwinds to after a closing marker
        #: for an outer frame (or an ``|else`` inside an inner frame).
        self.unwind_to: int | None = None
        self._handlers = self._make_handlers()

    # ------------------------------------------------------------------
    # Entry and bodies
    # ------------------------------------------------------------------

    def parse_document(self) -> list[Block]:
        """Parse the body of the file; return the top-level blocks (flat)."""
        self.pos = self.header.body_start
        root = Frame("root", self.span(self.pos), 1)
        return self.parse_body(root)

    def parse_body(self, frame: Frame) -> list[Block]:
        """Parse blocks until ``frame`` is closed, unwound or the text ends.

        For an ``if`` frame the body also ends before an ``|elif``/``|else``
        line (the caller starts the next branch).
        """
        self.stack.append(frame)
        index = len(self.stack) - 1
        children: list[Block] = []
        try:
            while True:
                if self.unwind_to is not None:
                    if self.unwind_to == index:
                        self.unwind_to = None
                    return children
                if self.pos >= len(self.text):
                    if frame.kind != "root" and not _is_track(frame):
                        self._report_unclosed(frame, self.span(len(self.text)))
                    return children
                info = L.classify(self.text, self.pos)
                if info.kind is L.Kind.CLOSE:
                    self._handle_close(info, index)
                    continue
                if info.kind is L.Kind.ENV and info.name == "track" and self._end_track(info, index):
                    if self.unwind_to is None:
                        return children  # this frame is the track block: the next one starts
                    continue
                if info.kind is L.Kind.ELSE:
                    if frame.kind == "if":
                        return children
                    if self._unwind_to_if(info, index):
                        continue
                    self.emit(error("P1220", self._line_span(info), form=info.name))
                    self._next_line()
                    continue
                block = self._parse_block(info)
                if block is not None:
                    children.append(block)
        finally:
            self.stack.pop()

    def _end_track(self, info: L.LineInfo, index: int) -> bool:
        """A ``|track(…):`` line ends the open track block (7.7, grammar ``TrackBlock``).

        Returns ``True`` when a track block is open: if it is the frame at
        ``index``, its body ends here; if environments inside it are still
        open, they are reported (P1216) and the parser unwinds to it.  The
        segment then reads the line as its next track block.
        """
        for j in range(index, 0, -1):
            frame = self.stack[j]
            if _is_track(frame):
                if j == index:
                    return True
                for k in range(index, j, -1):
                    self._report_unclosed(self.stack[k], self._line_span(info))
                self.unwind_to = j
                return True
            if frame.kind == "command" and frame.name in ("segment", "parallel"):
                return False
        return False

    def _unwind_to_if(self, info: L.LineInfo, index: int) -> bool:
        """An ``|else`` inside an inner environment of an ``|if``: unwind."""
        for j in range(index - 1, -1, -1):
            if self.stack[j].kind == "if":
                for k in range(index, j, -1):
                    self._report_unclosed(self.stack[k], self._line_span(info))
                self.unwind_to = j
                return True
            if self.stack[j].kind in ("for", "def"):
                return False
        return False

    # ------------------------------------------------------------------
    # Closing markers
    # ------------------------------------------------------------------

    def _parse_close_tag(self, info: L.LineInfo) -> tuple[_CloseTag, int]:
        """Parse the tag of a closing marker; return it and the offset after it."""
        position = info.name_end
        if info.name in ("endif", "endfor", "enddef"):
            return _CloseTag(info.name[3:]), position
        char = self.text[position] if position < len(self.text) else ""
        if char == ">":
            end = position
            while end < len(self.text) and self.text[end] == ">":
                end += 1
            return _CloseTag("clause", level=end - position), end
        if char == "!":
            return _CloseTag("admonition"), position + 1
        if char == ".":
            end = L.scan_style_name(self.text, position + 1)
            return _CloseTag("style", name=self.text[position + 1:end]), end
        after_ws = L.skip_ws(self.text, position)
        if after_ws > position and after_ws < len(self.text) and L.is_name_start(self.text[after_ws]):
            end = L.scan_name(self.text, after_ws)
            name = self.text[after_ws:end]
            if name == "clause":
                return _CloseTag("clause"), end
            if name in ("admonition", "style", "comment"):
                return _CloseTag(name), end
            return _CloseTag("command", name=name), end
        return _CloseTag("anon"), position

    @staticmethod
    def _matches(frame: Frame, tag: _CloseTag) -> bool:
        """Does a tagged closing marker close ``frame``?"""
        if frame.kind != tag.kind:
            return False
        if tag.kind == "clause":
            return tag.level in (0, frame.level)
        if tag.kind == "style":
            return not tag.name or tag.name == frame.name
        if tag.kind == "command":
            return tag.name == frame.name
        return True

    def _handle_close(self, info: L.LineInfo, index: int) -> None:
        """Process a closing line for the frame at ``index`` (top of stack)."""
        tag, after = self._parse_close_tag(info)
        marker_span = self.span(info.content, after)
        if not L.at_line_end(self.text, after):
            self.emit(error("P1221", self.span(after, self.line_end(after))))
        top = self.stack[index]
        if tag.kind == "anon" and _is_track(top) and index > 1 \
                and self.stack[index - 1].kind == "command" and self.stack[index - 1].name == "segment":
            # A track block has no closing marker of its own (7.7): '|end' in it
            # closes the segment, the track block ends with it.
            index -= 1
            top = self.stack[index]

        if tag.kind == "anon":
            if top.kind in _CONTROL:
                self.emit(error("P1219", marker_span, kind=top.kind).note("note.opened_here", top.opener))
                self._next_line()
                return
            if top.kind == "root":
                self.emit(error("P1218", marker_span, found="|end"))
                self._next_line()
                return
            target = index
            line = self.source.position(info.start).line
            if line - top.line + 1 > LONG_ENVIRONMENT_LINES:
                self.emit(warning("P1238", marker_span, lines=line - top.line + 1,
                                  close=top.canonical_close()))
        else:
            target = -1
            for j in range(index, 0, -1):
                if self._matches(self.stack[j], tag):
                    target = j
                    break
            if target < 0:
                found = self.text[info.content:after]
                if top.kind == "root":
                    self.emit(error("P1218", marker_span, found=found))
                else:
                    self.emit(error("P1217", marker_span, found=found, name=top.opener_text(),
                                    expected=top.canonical_close()).note("note.opened_here", top.opener))
                self._next_line()
                return
            for k in range(index, target, -1):
                if not _is_track(self.stack[k]):  # track blocks end with their segment (7.7)
                    self._report_unclosed(self.stack[k], marker_span)

        frame = self.stack[target]
        frame.closed = True
        frame.close_span = marker_span
        self.unwind_to = target
        self._next_line()

    def _report_unclosed(self, frame: Frame, where: Span) -> None:
        """P1216 for an environment that was not closed."""
        self.emit(error("P1216", frame.opener, name=frame.opener_text(), close=frame.canonical_close())
                  .note("note.expected_close_here", where, close=frame.canonical_close()))

    # ------------------------------------------------------------------
    # Line helpers
    # ------------------------------------------------------------------

    def _line_span(self, info: L.LineInfo) -> Span:
        """Span of the content of a line (after indentation, without LF)."""
        return self.span(info.content, self.line_end(info.content))

    def _next_line(self) -> None:
        """Move ``pos`` to the start of the next line."""
        end = self.line_end()
        self.pos = min(end + 1, len(self.text))

    def _finish_line(self, what: str = "") -> None:
        """Expect ``LineEnd`` at ``pos`` (decision 34) and move to the next line."""
        if not L.at_line_end(self.text, self.pos):
            self.emit(error("P1242", self.span(self.pos, self.line_end()), expected=Key("expect.line_end"),
                            after=what or "|"))
        self._next_line()

    def _after_line_form(self, info: L.LineInfo) -> None:
        """Finish a line form; warn about a text line right after it (3.4)."""
        if self.peek() == "\n":
            self.pos += 1
        if self.pos < len(self.text):
            following = L.classify(self.text, self.pos)
            if following.kind is L.Kind.TEXT and not self._in_table_context():
                self.emit(warning("P1236", self._line_span(following)).hint("help.eol_mode"))

    def _content_context(self, *, row: bool = False, cell: bool = False) -> Context:
        """Context of the text of a line form (ends at the end of the line, 3.4).

        ``cell``: the text of a ``|cell:`` line form; formulas are also
        allowed anywhere inside a ``|cell:`` environment (6.8).
        """
        return Context(row=row, cell=row or cell or self._in_cell())

    def _in_cell(self) -> bool:
        """Inside a ``|cell:`` environment (formulas ``|=(…)`` allowed, 6.8)."""
        return any(frame.kind == "command" and frame.name == "cell" for frame in self.stack)

    def _container(self) -> Frame:
        """The innermost frame that is not a control construct."""
        for frame in reversed(self.stack):
            if frame.kind not in _CONTROL:
                return frame
        return self.stack[0]

    def _in_table_context(self) -> bool:
        container = self._container()
        return container.kind == "command" and container.name in ("table", "row")

    def _inside(self, kind: str) -> Frame | None:
        """The nearest open frame of ``kind`` (any depth)."""
        for frame in reversed(self.stack):
            if frame.kind == kind:
                return frame
        return None

    # ------------------------------------------------------------------
    # Dispatch
    # ------------------------------------------------------------------

    def _parse_block(self, info: L.LineInfo) -> Block | None:
        """Parse one block starting at the line ``info``; return it or ``None``."""
        container = self._container()
        if container.kind == "command" and container.name == "parallel" and not self._allowed_in_parallel(info):
            # Parse to stay in sync, then drop the block (7.7).
            what = "|" + info.name if info.name else _KIND_LABELS.get(info.kind, "text")
            self.emit(error("P5303", self._line_span(info), what=what, container="parallel").hint("help.parallel"))
            self._dispatch(info)
            return None
        allowed = self._allowed_in_container(container, info)
        if not allowed:
            # Parse to stay in sync, then drop the block (P1226 reported).
            what = "|" + info.name if info.name else _KIND_LABELS.get(info.kind, "text")
            self.emit(error("P1226", self._line_span(info), what=what, container=container.name))
            self._dispatch(info)
            return None
        if info.kind is L.Kind.ROW and not (container.kind == "command" and container.name == "table") \
                and not (container.kind == "root" and self.header.kind == "fragment"):
            # A fragment may consist of rows inserted into a table by
            # |include; they are checked on insertion (decision 37).
            self.emit(error("P1243", self._line_span(info)))
        if info.kind is L.Kind.HEADING and self._inside("clause") is not None:
            self.emit(error("P1230", self._line_span(info)))
        if info.kind in (L.Kind.HEADING, L.Kind.CLAUSE) and container.kind == "command" \
                and container.name == "list":
            self.emit(error("P1231", self._line_span(info), form="|<" if info.kind is L.Kind.HEADING else "|>"))
        return self._dispatch(info)

    @staticmethod
    def _allowed_in_parallel(info: L.LineInfo) -> bool:
        """Content of ``|parallel`` (7.7): segments, control, code, comments, includes, page breaks.

        A fragment included here is checked again when it is inserted (stage 13.3).
        """
        if info.kind in _PARALLEL_KINDS:
            return True
        if info.kind is L.Kind.COMMAND and info.name in _PARALLEL_COMMANDS:
            return True
        return info.kind is L.Kind.ENV and info.name == "segment"

    def _allowed_in_container(self, container: Frame, info: L.LineInfo) -> bool:
        """Table and row content restrictions (grammar 3.5, decision 37).

        ``|include`` is allowed in a table and a row body: the inserted
        blocks are checked against the same restrictions when the fragment
        is inserted (stage 13.3).  ``|let`` and ``|set`` are errors.
        """
        if container.kind != "command" or container.name not in ("table", "row"):
            return True
        kinds = _TABLE_KINDS if container.name == "table" else _ROW_KINDS
        if info.kind in kinds:
            return True
        if info.kind is L.Kind.COMMAND and info.name == "include":
            return True
        names = ("row", "caption") if container.name == "table" else ("cell",)
        return info.kind in (L.Kind.ENV, L.Kind.COLON) and info.name in names

    def _dispatch(self, info: L.LineInfo) -> Block | None:
        kind = info.kind
        if kind is L.Kind.BLANK:
            span = self.span(info.start, self.line_end(info.start))
            self._next_line()
            return BlankLine(span)
        if kind is L.Kind.COMMENT:
            end = self.line_end(info.content)
            node = Comment(self.span(info.content, end), self.text[info.content + 2:end])
            self._next_line()
            return node
        return self._handlers[kind](info)

    def _make_handlers(self) -> dict:
        """Map line kinds to their parsing methods (built once per parser)."""
        return {
            L.Kind.TEXT: self._paragraph, L.Kind.HEADING: self._heading,
            L.Kind.CLAUSE: self._clause, L.Kind.LIST: self._list_item,
            L.Kind.ADMONITION: self._admonition, L.Kind.ROW: self._row,
            L.Kind.STYLE: self._style, L.Kind.CODE: self._code, L.Kind.VERBATIM: self._verbatim,
            L.Kind.COMMENT_BLOCK: self._comment_block, L.Kind.IF: self._if,
            L.Kind.FOR: self._for, L.Kind.DEF: self._def, L.Kind.COMMAND: self._command,
            L.Kind.ENV: self._command, L.Kind.COLON: self._command, L.Kind.SEGMENT: self._segment_line,
        }

    # ------------------------------------------------------------------
    # Paragraphs and line forms
    # ------------------------------------------------------------------

    def _paragraph(self, info: L.LineInfo) -> Paragraph:
        """Consecutive text lines (4.1): continue until a blank line or a block line."""
        self.pos = info.content
        body = self.parse_inlines(Context(multiline=True, cell=self._in_cell()))
        node = Paragraph(self.span(info.content, self.pos), body)
        self._next_line()
        return node

    def _text_after_marker(self, info: L.LineInfo, marker_end: int, form: str,
                           *, multiline: bool) -> list:
        """Parse ``WS+ Inline+`` after a marker; report P1212 if missing."""
        if self.peek() not in (" ", "\t") or L.at_line_end(self.text, self.pos):
            self.emit(error("P1212", self.span(info.content, max(marker_end, self.pos)), form=form))
            self.skip_to_line_end()
            return []
        self.pos = L.skip_ws(self.text, self.pos)
        return self.parse_inlines(Context(multiline=multiline))

    def _heading(self, info: L.LineInfo) -> Heading:
        """``|<``… — always ends at the end of the line (3.4)."""
        start = info.content
        end = start + 1
        while end < len(self.text) and self.text[end] == "<":
            end += 1
        level = end - start - 1
        self.pos = end
        args = self.optional_args()
        if level > 6:
            self.emit(error("P1213", self.span(start, end), level=level))
        if level > 1 and args is not None and args.keyword("level") is not None:
            # The level is either the number of '<' or level= with a single
            # '<' (3.3, 5.2); the key alone decides (decision 114).
            self.emit(error("P1244", args.span, count=level))
        body = self._text_after_marker(info, end, "<" * level, multiline=False)
        node = Heading(self.span(start, self.pos), level, args, body)
        self._next_line()
        return node

    def _env_or_text(self) -> str | None:
        """After a marker and arguments: ``env`` for ``:``+LineEnd, ``line`` for WS+."""
        if self.peek() == ":" and L.at_line_end(self.text, self.pos + 1):
            self.pos += 1
            self._next_line()
            return "env"
        return "line"

    def _clause(self, info: L.LineInfo) -> Clause:
        """``|>`` line form or ``|>:`` … ``|end>`` (3.6, 5.3)."""
        start = info.content
        end = start + 1
        while end < len(self.text) and self.text[end] == ">":
            end += 1
        level = end - start - 1
        self.pos = end
        args = self.optional_args()
        line = self.source.position(start).line
        if self._env_or_text() == "env":
            frame = Frame("clause", self.span(start, end), line, level=level)
            children = self.parse_body(frame)
            return Clause(self.span(start, self.pos), level, args, "env", [], children)
        body = self._text_after_marker(info, end, ">" * level, multiline=False)
        node = Clause(self.span(start, self.pos), level, args, "line", body)
        self._after_line_form(info)
        return node

    def _admonition(self, info: L.LineInfo) -> Admonition:
        """``|!("kind")`` line form or environment (9.1)."""
        start = info.content
        self.pos = start + 2
        if self.peek() != "(":
            self.emit(error("P1214", self.span(start, start + 2)))
        args = self.optional_args()
        line = self.source.position(start).line
        if self._env_or_text() == "env":
            frame = Frame("admonition", self.span(start, start + 2), line)
            children = self.parse_body(frame)
            return Admonition(self.span(start, self.pos), args, "env", [], children)
        body = self._text_after_marker(info, start + 2, "!", multiline=False)
        node = Admonition(self.span(start, self.pos), args, "line", body)
        self._after_line_form(info)
        return node

    def _list_item(self, info: L.LineInfo) -> ListItem:
        """``|-``, ``|#``, ``|#-``… (5.4); ends at the end of the line."""
        start = info.content
        end = start + 1
        while end < len(self.text) and self.text[end] in "-#":
            end += 1
        marker = self.text[start + 1:end]
        self.pos = end
        args = self.optional_args()
        body = self._text_after_marker(info, end, marker, multiline=False)
        node = ListItem(self.span(start, self.pos), marker, args, body)
        self._after_line_form(info)
        return node

    def _style(self, info: L.LineInfo) -> StyleBlock | None:
        """``|.Name: text`` or ``|.Name:`` … ``|end.Name`` (4.3)."""
        start = info.content
        self.pos = start + 2
        style = self.parse_style_ref(start)
        if style is None:
            self._next_line()
            return None
        args = self.optional_args()
        line = self.source.position(start).line
        self.pos += 1  # ':' (guaranteed by classify)
        if L.at_line_end(self.text, self.pos):
            self._next_line()
            frame = Frame("style", style.span, line, name=style.name or "")
            children = self.parse_body(frame)
            return StyleBlock(self.span(start, self.pos), style, args, "env", [], children)
        self.pos = L.skip_ws(self.text, self.pos)
        body = self.parse_inlines(self._content_context())
        node = StyleBlock(self.span(start, self.pos), style, args, "line", body)
        self._after_line_form(info)
        return node

    def _row(self, info: L.LineInfo) -> TableRow:
        """``|:`` compact table row with ``|&`` cells (6.4).

        The first cell has no ``|&`` unless it carries arguments
        (``|:|&(span=3) Разом``): ``|&`` directly after ``|:`` (or after the
        row arguments), without a space, belongs to the first cell.  With a
        space, ``|: |& Б`` starts with an empty first cell (decision 120).
        A row without any content has no cells.
        """
        start = info.content
        self.pos = start + 2
        args = self.optional_args()
        context = self._content_context(row=True)
        cells: list[Cell] = []
        first_args = self.text.startswith("|&", self.pos)
        self.pos = L.skip_ws(self.text, self.pos)
        cell_start, cell_args = self.pos, None
        if first_args:
            self.pos += 2
            cell_args = self.optional_args()
        while True:
            self.pos = L.skip_ws(self.text, self.pos)
            body = self.parse_inlines(context)
            more = self.text.startswith("|&", self.pos)
            if body or cell_args is not None or cells or more:
                cells.append(Cell(self.span(cell_start, self.pos), cell_args, body))
            if not more:
                break
            cell_start = self.pos
            self.pos += 2
            cell_args = self.optional_args()
        node = TableRow(self.span(start, self.pos), args, cells)
        if self.peek() == "\n":
            self.pos += 1
        return node

    # ------------------------------------------------------------------
    # Commands and environments
    # ------------------------------------------------------------------

    def _command(self, info: L.LineInfo) -> Command:
        """Line command, ``|name: text`` or ``|name:`` … ``|end name`` (3.4)."""
        start = info.content
        name_span = self.span(start + 1, info.name_end)
        self.pos = info.name_end
        args = self.optional_args()
        if info.kind is L.Kind.COMMAND:
            node = Command(self.span(start, self.pos), info.name, name_span, args, "bare")
            self._finish_line("|" + info.name)
            return node
        self.pos += 1  # ':'
        if info.kind is L.Kind.ENV:
            self._next_line()
            frame = Frame("command", self.span(start, info.name_end), self.source.position(start).line,
                          name=info.name)
            children = self.parse_body(frame)
            return Command(self.span(start, self.pos), info.name, name_span, args, "env", [], children)
        self.pos = L.skip_ws(self.text, self.pos)
        body = self.parse_inlines(self._content_context(cell=info.name == "cell"))
        node = Command(self.span(start, self.pos), info.name, name_span, args, "line", body)
        self._after_line_form(info)
        return node

    def _segment_line(self, info: L.LineInfo) -> Command:
        """``|segment(args) |track("uk"){…} |track("en"){…}`` — the line form of a segment (7.7).

        The tracks become ``Command("track", form="inline")`` children with
        their inline bodies; the segment has the form ``line``.
        """
        start = info.content
        segment_name = self.span(start + 1, info.name_end)
        self.pos = info.name_end
        args = self.optional_args()
        tracks: list[Block] = []
        while True:
            self.pos = L.skip_ws(self.text, self.pos)
            if L.at_line_end(self.text, self.pos) or not self.text.startswith("|track", self.pos) \
                    or L.is_ident_char(self.peek(6)):
                break
            track_start = self.pos
            self.pos += len("|track")
            track_args = self.optional_args()
            body: list = []
            if self.peek() == "{":
                body = self.parse_inline_body(Context()) or []
            else:
                self.emit(error("P1209", self.span(track_start, self.pos), form="track"))
            name_span = self.span(track_start + 1, track_start + len("|track"))
            tracks.append(Command(self.span(track_start, self.pos), "track", name_span, track_args, "inline", body))
        node = Command(self.span(start, self.pos), "segment", segment_name, args, "line", [], tracks)
        self._finish_line("|track")
        return node

    def _if(self, info: L.LineInfo) -> IfBlock:
        """``|if(c):`` … ``|elif(c):`` … ``|else:`` … ``|endif`` (3.6)."""
        start = info.content
        frame = Frame("if", self.span(start, info.name_end), self.source.position(start).line)
        assert info.args is not None
        cond = self.parse_expr_at(info.args[0])
        self.pos = info.after + 1
        self._finish_line("|if(…):")
        node = IfBlock(self.span(start, start))
        branch = IfBranch(self.span(start, info.after + 1), cond)
        node.branches.append(branch)
        seen_else = False
        while True:
            branch.children = self.parse_body(frame)
            if frame.closed or self.unwind_to is not None or self.pos >= len(self.text):
                break
            else_info = L.classify(self.text, self.pos)
            if seen_else:
                self.emit(error("P1240", self._line_span(else_info), form=else_info.name))
            seen_else = seen_else or else_info.name == "else"
            cond = None
            if else_info.name == "elif":
                assert else_info.args is not None
                cond = self.parse_expr_at(else_info.args[0])
            self.pos = else_info.after + 1
            branch = IfBranch(self.span(else_info.content, else_info.after + 1), cond)
            self._finish_line("|" + else_info.name)
            node.branches.append(branch)
        node.span = self.span(start, self.pos)
        return node

    def _for(self, info: L.LineInfo) -> ForBlock | None:
        """``|for(x in items):`` … ``|endfor``."""
        start = info.content
        assert info.args is not None
        loop = self.parse_for_at(info.args[0])
        self.pos = info.after + 1
        self._finish_line("|for(…):")
        frame = Frame("for", self.span(start, info.name_end), self.source.position(start).line)
        children = self.parse_body(frame)
        if loop is None:
            return None
        return ForBlock(self.span(start, self.pos), loop, children)

    def _def(self, info: L.LineInfo) -> DefBlock | None:
        """``|def name(params):`` … ``|enddef`` — user command (3.6, B.3)."""
        start = info.content
        name_start = L.skip_ws(self.text, info.name_end)
        name_end = name_start
        if name_end < len(self.text) and L.is_name_start(self.text[name_end]):
            while name_end < len(self.text) and L.is_ident_char(self.text[name_end]):
                name_end += 1
        name = self.text[name_start:name_end]
        func = None
        header_ok = False
        if name and name_end < len(self.text) and self.text[name_end] == "(":
            close = self.find_closing(name_end)
            if close is not None:
                self.pos = close + 1
                if self.peek() == ":" and L.at_line_end(self.text, self.pos + 1):
                    header_ok = True
                    if name in RESERVED_NAMES:
                        # Python keywords would also fail ast.parse; one
                        # message about the name is enough.
                        self.emit(error("P1235", self.span(name_start, name_end), name=name))
                    else:
                        try:
                            func = pyfrag.parse_def(self.source, name_start, close)
                        except pyfrag.PySyntaxError as exc:
                            self.emit(exc.diagnostic)
        if not header_ok:
            self.emit(error("P1229", self._line_span(info)))
        self._next_line()
        frame = Frame("def", self.span(start, info.name_end), self.source.position(start).line)
        children = self.parse_body(frame)
        if func is None:
            return None
        return DefBlock(self.span(start, self.pos), name, func, children)

    def _comment_block(self, info: L.LineInfo) -> CommentBlock:
        """``|comment:`` … ``|end`` — only environment balance is checked (3.7)."""
        start = info.content
        self.pos = info.name_end + 1
        self._finish_line("|comment:")
        frame = Frame("comment", self.span(start, info.name_end), self.source.position(start).line)
        real_sink, real_opaque = self.sink, self.opaque
        self.sink, self.opaque = _BalanceSink(real_sink), True
        try:
            self.parse_body(frame)
        finally:
            self.sink, self.opaque = real_sink, real_opaque
        return CommentBlock(self.span(start, self.pos))

    # ------------------------------------------------------------------
    # Raw blocks: code and verbatim
    # ------------------------------------------------------------------

    def _raw_lines(self, info: L.LineInfo, is_end) -> tuple[list[tuple[int, int, str]], int | None, int]:
        """Collect the lines of a raw block after its opening line.

        The indentation of the opening line is removed from every line
        (decision 24); a non-empty line with a smaller or different
        indentation is an error (P1222).

        Args:
            info: the opening line.
            is_end: predicate ``(line_start, content_offset) -> bool``.

        Returns:
            ``(lines, end_line_start, content_end)``: lines as
            ``(line_start, removed, text)``; the start of the closing line
            or ``None`` if the text ended; the offset after the content.
        """
        prefix = self.text[info.start:info.content]
        collected: list[tuple[int, int, str]] = []
        position = self.pos
        content_end = position
        while position < len(self.text):
            line_end = self.line_end(position)
            line = self.text[position:line_end]
            if is_end(position, L.skip_ws(self.text, position)):
                return collected, position, content_end
            if not line.strip(WS):
                collected.append((position, 0, ""))
            elif line.startswith(prefix):
                collected.append((position, len(prefix), line[len(prefix):]))
            else:
                self.emit(error("P1222", self.span(position, line_end)))
                removed = len(line) - len(line.lstrip(WS))
                removed = min(removed, len(prefix))
                collected.append((position, removed, line[removed:]))
            content_end = line_end
            position = line_end + 1
        return collected, None, content_end

    def _code(self, info: L.LineInfo) -> CodeBlock:
        """``|code:`` … ``|end`` — statements of the computing core (3.7)."""
        start = info.content
        self.pos = info.name_end + 1
        self._finish_line("|code:")
        body_start = self.pos

        def is_end(_line: int, content: int) -> bool:
            return (self.text.startswith("|end", content)
                    and L.at_line_end(self.text, content + 4))

        collected, end_line, content_end = self._raw_lines(info, is_end)
        if end_line is None:
            self.emit(error("P1224", self.span(start, info.name_end + 1)))
            self.pos = len(self.text)
        else:
            self.pos = end_line
            self._next_line()
        code = None
        try:
            code = pyfrag.parse_code(self.source, collected,
                                     self.span(body_start, max(body_start, content_end)))
        except pyfrag.PySyntaxError as exc:
            self.emit(exc.diagnostic)
        return CodeBlock(self.span(start, self.pos), code)

    def _verbatim(self, info: L.LineInfo) -> Verbatim:
        """``|verbatim:`` … ``|end`` or ``|verbatim(end="EOF"):`` … ``EOF`` (3.7).

        The end marker is compared literally (decision 34): after the
        indentation the line must equal the marker; no comment may follow.
        """
        start = info.content
        self.pos = info.name_end
        marker = "|end"
        if self.peek() == "(":
            args = self.parse_args_at(self.pos)
            value = _verbatim_marker(args)
            if value is None:
                self.emit(error("P1225", args.span if args else self.span(start, self.pos)))
            else:
                marker = value
        if self.peek() != ":":
            self.emit(error("P1242", self.span(start, self.pos), expected=Key("expect.colon"), after="|verbatim"))
        else:
            self.pos += 1
        self._finish_line("|verbatim:")

        def is_end(_line: int, content: int) -> bool:
            return self.text[content:self.line_end(content)] == marker

        collected, end_line, _ = self._raw_lines(info, is_end)
        if end_line is None:
            self.emit(error("P1223", self.span(start, info.name_end), marker=marker))
            self.pos = len(self.text)
        else:
            self.pos = end_line
            self._next_line()
        return Verbatim(self.span(start, self.pos), "\n".join(text for _, _, text in collected), marker)


def _verbatim_marker(args) -> str | None:
    """Return the ``end="…"`` string of ``|verbatim(…)`` or ``None`` if invalid."""
    if args is None or args.positional or len(args.call.keywords) != 1:
        return None
    value = args.keyword("end")
    if isinstance(value, ast.Constant) and isinstance(value.value, str) and value.value \
            and "\n" not in value.value:
        return value.value
    return None


_KIND_LABELS = {
    L.Kind.TEXT: "text", L.Kind.HEADING: "|<", L.Kind.CLAUSE: "|>", L.Kind.LIST: "|-",
    L.Kind.ADMONITION: "|!", L.Kind.ROW: "|:", L.Kind.STYLE: "|.", L.Kind.VERBATIM: "|verbatim",
}


def _is_track(frame: Frame) -> bool:
    """The frame of a track block ``|track(…):`` (7.7)."""
    return frame.kind == "command" and frame.name == "track"
