"""Classification of source lines: the ordered choice of ``Block``.

Grammar (appendix 1), section 3: a block construct starts at the beginning of a
line after optional indentation; the alternatives of ``Block`` are an
ordered choice; a long command at the start of a line is a line command
only when the line ends after its arguments (decision 34: trailing
whitespace and a ``|%`` comment are allowed) or continues with the ``:``
forms; otherwise the line is text.

:func:`classify` is the single place where this decision is made.  It is
used:

* by the block parser to dispatch a line;
* to find the end of a paragraph (section 4.1: a line that the ordered
  choice recognises as any alternative other than ``Paragraph`` and
  ``LineComment`` ends it);
* for error recovery inside an unclosed ``{`` (:data:`BLOCK_ONLY` kinds
  cannot occur inside an inline body, so such a line ends it).
"""

from __future__ import annotations

import enum
from dataclasses import dataclass

from primula.syntax import pyscan
from primula.unicode import is_xid_continue, is_xid_start


class Kind(enum.Enum):
    """Kinds of source lines."""

    BLANK = "blank"
    COMMENT = "comment"            # a whole-line |% comment
    TEXT = "text"                  # paragraph text (ordered choice fallback)
    HEADING = "heading"            # |<
    CLAUSE = "clause"              # |>
    LIST = "list"                  # |- |# |#- ...
    ADMONITION = "admonition"      # |!
    ROW = "row"                    # |:
    STYLE = "style"                # |.Name: (paragraph style)
    CLOSE = "close"                # |end..., |endif, |endfor, |enddef
    CODE = "code"                  # |code:
    VERBATIM = "verbatim"          # |verbatim:
    COMMENT_BLOCK = "comment-block"  # |comment:
    IF = "if"                      # |if(c):
    ELSE = "else"                  # |elif(c): / |else:
    FOR = "for"                    # |for(x in xs):
    DEF = "def"                    # |def name(params):
    COMMAND = "command"            # |name(args)  (line command without body)
    ENV = "env"                    # |name(args):  (environment)
    COLON = "colon"                # |name(args): text  (line body)
    SEGMENT = "segment"            # |segment(args) |track(…){…} |track(…){…}  (7.7)


#: Kinds that can never be part of an inline body: such a line ends an
#: unclosed ``{`` during error recovery.  Line commands without a body and
#: ``|name:`` forms are excluded — ``|img("a.png")`` alone on a line is
#: valid inside a multi-line body.
BLOCK_ONLY = frozenset({
    Kind.HEADING, Kind.CLAUSE, Kind.LIST, Kind.ADMONITION, Kind.ROW, Kind.STYLE,
    Kind.CLOSE, Kind.CODE, Kind.VERBATIM, Kind.COMMENT_BLOCK, Kind.IF, Kind.ELSE,
    Kind.FOR, Kind.DEF, Kind.SEGMENT,
})

#: Kinds that continue a paragraph.
CONTINUES = frozenset({Kind.TEXT, Kind.COMMENT})


@dataclass
class LineInfo:
    """Result of :func:`classify`.

    Attributes:
        kind: line kind.
        start: offset of the line.
        content: offset after the indentation.
        name: command name for ``COMMAND``/``ENV``/``COLON``/``CLOSE``
            (close: the word after ``|``, e.g. ``end``, ``endif``).
        name_end: offset after the name.
        args: ``(open, close)`` offsets of the argument brackets, if any.
        after: offset after the name and arguments.
    """

    kind: Kind
    start: int
    content: int
    name: str = ""
    name_end: int = 0
    args: tuple[int, int] | None = None
    after: int = 0


def is_name_start(char: str) -> bool:
    """``XidStart`` (grammar ``Ident``, section 3.9): a Unicode letter."""
    return bool(char) and is_xid_start(char)


def is_ident_char(char: str) -> bool:
    """``XidContinue`` (grammar ``Ident``): letters, digits, ``_`` (Unicode 15.1)."""
    return bool(char) and is_xid_continue(char)


def skip_ws(text: str, position: int) -> int:
    """Skip spaces and tabs (grammar ``WS``)."""
    while position < len(text) and text[position] in " \t":
        position += 1
    return position


def at_line_end(text: str, position: int) -> bool:
    """``LineEnd ::= WS* Comment? EOL`` (decision 34) starts at ``position``."""
    position = skip_ws(text, position)
    return position >= len(text) or text[position] == "\n" or text.startswith("|%", position)


def scan_name(text: str, position: int) -> int:
    """Scan ``Name ::= Ident ("." Ident)*`` from a ``XidStart``; return its end."""
    end = position
    while end < len(text) and is_ident_char(text[end]):
        end += 1
    while end + 1 < len(text) and text[end] == "." and is_name_start(text[end + 1]):
        end += 1
        while end < len(text) and is_ident_char(text[end]):
            end += 1
    return end


def scan_style_name(text: str, position: int) -> int:
    """Scan ``StyleName ::= XidStart ( XidContinue | "-" )*``; return its end."""
    end = position
    if end < len(text) and is_name_start(text[end]):
        end += 1
        while end < len(text) and (is_ident_char(text[end]) or text[end] == "-"):
            end += 1
    return end


def _brackets(text: str, position: int) -> tuple[int, int] | None:
    """Return ``(open, close)`` if a bracket group starts at ``position``.

    ``None`` if there is no ``(`` or it is not closed (the line is then
    treated as text and the inline parser reports the error).
    """
    if position < len(text) and text[position] == "(":
        try:
            return position, pyscan.find_closing(text, position)
        except pyscan.ScanError:
            return None
    return None


def _colon_form(text: str, position: int) -> Kind | None:
    """After a command head: ``:`` + LineEnd is ENV, ``:`` + WS is COLON."""
    if position < len(text) and text[position] == ":":
        if at_line_end(text, position + 1):
            return Kind.ENV
        if position + 1 < len(text) and text[position + 1] in " \t":
            return Kind.COLON
    return None


def classify(text: str, start: int) -> LineInfo:
    """Classify the line starting at ``start`` by the ordered choice of ``Block``.

    Args:
        text: normalised source text.
        start: offset of the beginning of a line.

    Returns:
        The classification; parsing details are left to the parsers.
    """
    content = skip_ws(text, start)
    info = LineInfo(Kind.TEXT, start, content)
    if content >= len(text) or text[content] == "\n":
        info.kind = Kind.BLANK
        return info
    if text[content] != "|" or content + 1 >= len(text):
        return info
    char = text[content + 1]
    simple = {"<": Kind.HEADING, ">": Kind.CLAUSE, "-": Kind.LIST, "#": Kind.LIST,
              "!": Kind.ADMONITION, ":": Kind.ROW}
    if char == "%":
        info.kind = Kind.COMMENT
    elif char in simple:
        info.kind = simple[char]
    elif char == ".":
        info.kind = _classify_style(text, content)
    elif is_name_start(char):
        _classify_command(text, info)
    return info


def _classify_style(text: str, content: int) -> Kind:
    """``|.Name(args)?:`` or ``|.(expr)(args)?:`` is a paragraph style."""
    position = content + 2
    if position < len(text) and text[position] == "(":
        group = _brackets(text, position)
        if group is None:
            return Kind.TEXT
        position = group[1] + 1
    else:
        end = scan_style_name(text, position)
        if end == position:
            return Kind.TEXT
        position = end
    group = _brackets(text, position)
    if group is not None:
        position = group[1] + 1
    form = _colon_form(text, position)
    return Kind.STYLE if form is not None else Kind.TEXT


def _classify_command(text: str, info: LineInfo) -> None:
    """Classify a line starting with ``|`` + a letter (fills ``info``)."""
    name_start = info.content + 1
    # Closing markers first: in '|end.Name' the dot belongs to the closing
    # tag, not to a dotted command name.
    ident_end = name_start
    while ident_end < len(text) and is_ident_char(text[ident_end]):
        ident_end += 1
    if text[name_start:ident_end] in ("end", "endif", "endfor", "enddef"):
        info.kind = Kind.CLOSE
        info.name, info.name_end, info.after = text[name_start:ident_end], ident_end, ident_end
        return

    name_end = scan_name(text, name_start)
    name = text[name_start:name_end]
    info.name, info.name_end, info.after = name, name_end, name_end
    if name in ("code", "comment") and name_end < len(text) and text[name_end] == ":":
        info.kind = Kind.CODE if name == "code" else Kind.COMMENT_BLOCK
        return
    if name == "verbatim":
        info.kind = Kind.VERBATIM
        return
    if name == "def" and name_end < len(text) and text[name_end] in " \t":
        info.kind = Kind.DEF
        return

    group = _brackets(text, name_end)
    after = group[1] + 1 if group is not None else name_end
    info.args, info.after = group, after
    form = _colon_form(text, after)

    if name in ("if", "elif", "for"):
        if group is not None and form is Kind.ENV:
            info.kind = {"if": Kind.IF, "elif": Kind.ELSE, "for": Kind.FOR}[name]
        return
    if name == "else":
        if group is None and form is Kind.ENV:
            info.kind = Kind.ELSE
        return
    if form is not None:
        info.kind = form
    elif at_line_end(text, after):
        info.kind = Kind.COMMAND
    elif name == "segment" and text.startswith("|track", skip_ws(text, after)) and skip_ws(text, after) > after:
        # The line form of a segment (7.7): the bodies of the tracks follow
        # on the same line, '|segment(id="city") |track("uk"){…} |track("en"){…}'.
        info.kind = Kind.SEGMENT
