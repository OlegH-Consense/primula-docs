"""Lexical scanning of Python fragments embedded in Primula markup.

Command arguments ``(…)``, expressions ``|(…)`` and formulas ``|=(…)`` are
Python text inside markup.  Before the text is given to :func:`ast.parse`,
its end must be found: the closing bracket that matches the opening one by
the lexical rules of Python, so that a ``)`` inside a string or a nested
bracket does not end the arguments (grammar, notes on ``PyArgs``).

The rules are those of the Python 3.11 tokenizer (decision 30 of the
specification), see https://docs.python.org/3.11/reference/lexical_analysis.html:

* string literals with optional prefixes (``r``, ``b``, ``u``, ``f`` and
  combinations, any case), single or triple quoted; a backslash always
  escapes the next character for the purpose of finding the end, also in
  raw strings; a single-quoted string cannot contain an unescaped newline;
* f-strings are scanned as ordinary strings: in Python 3.11 the first
  unescaped quote of the same kind ends an f-string (PEP 701 nesting of
  the same quotes appeared only in 3.12, see :func:`strings_only`);
* ``#`` starts a comment up to the end of the line;
* brackets ``()``, ``[]``, ``{}`` nest and must match;
* line breaks inside brackets are allowed (decision 22).

The scanner works on the normalised source text and returns offsets in it.
"""

from __future__ import annotations

from dataclasses import dataclass

_OPENERS = {"(": ")", "[": "]", "{": "}"}
_CLOSERS = {")": "(", "]": "[", "}": "{"}
_STRING_PREFIXES = frozenset({
    "r", "u", "b", "f", "br", "rb", "fr", "rf",
})


@dataclass
class ScanError(Exception):
    """A lexical error in a Python fragment.

    Attributes:
        kind: ``unclosed_bracket`` (``offset`` = the opening bracket),
            ``mismatched_bracket`` (``offset`` = the wrong closer,
            ``related`` = the opener), ``unclosed_string`` (``offset`` =
            the start of the literal).
        offset: main position.
        related: related position or ``None``.
        found: the character found (for mismatched brackets).
        expected: the expected closing character.
    """

    kind: str
    offset: int
    related: int | None = None
    found: str = ""
    expected: str = ""

    def __post_init__(self) -> None:
        Exception.__init__(self, self.kind)


def _is_ident_start(char: str) -> bool:
    return char.isalpha() or char == "_"


def _is_ident_char(char: str) -> bool:
    return char.isalnum() or char == "_"


def skip_string(text: str, start: int, quote_at: int) -> int:
    """Skip a string literal and return the offset after it.

    Args:
        text: the text.
        start: offset of the literal (its prefix or its first quote).
        quote_at: offset of the first quote character.

    Returns:
        The offset after the closing quote.

    Raises:
        ScanError: the literal is not closed (``unclosed_string``).
    """
    quote = text[quote_at]
    triple = text.startswith(quote * 3, quote_at)
    delimiter = quote * 3 if triple else quote
    position = quote_at + len(delimiter)
    length = len(text)
    while position < length:
        char = text[position]
        if char == "\\":
            position += 2
            continue
        if text.startswith(delimiter, position):
            return position + len(delimiter)
        if char == "\n" and not triple:
            break
        position += 1
    raise ScanError("unclosed_string", start)


def string_literal_at(text: str, position: int) -> int | None:
    """Return the offset of the opening quote if a string literal starts here.

    Recognises an optional prefix (``r``, ``f``, ``rb``...) followed by a
    quote.  The caller must make sure ``position`` is not inside an
    identifier.

    Args:
        text: the text.
        position: candidate start.

    Returns:
        Offset of the quote, or ``None``.
    """
    if position < len(text) and text[position] in "\"'":
        return position
    end = position
    while end < len(text) and end - position < 2 and text[end].isalpha():
        end += 1
    if end < len(text) and text[end] in "\"'" and text[position:end].lower() in _STRING_PREFIXES:
        return end
    return None


def find_closing(text: str, open_offset: int) -> int:
    """Find the bracket that closes the one at ``open_offset``.

    Args:
        text: the normalised source text.
        open_offset: offset of ``(``, ``[`` or ``{``.

    Returns:
        Offset of the matching closing bracket.

    Raises:
        ScanError: an unclosed bracket or string, or a mismatched bracket.
    """
    stack: list[int] = [open_offset]
    position = open_offset + 1
    length = len(text)
    while position < length:
        char = text[position]
        if char == "#":
            newline = text.find("\n", position)
            position = length if newline == -1 else newline
            continue
        if char in "\"'":
            position = skip_string(text, position, position)
            continue
        if _is_ident_start(char):
            quote = string_literal_at(text, position)
            if quote is not None:
                position = skip_string(text, position, quote)
                continue
            while position < length and _is_ident_char(text[position]):
                position += 1
            continue
        if char in _OPENERS:
            stack.append(position)
        elif char in _CLOSERS:
            opener = stack[-1]
            if text[opener] != _CLOSERS[char]:
                raise ScanError("mismatched_bracket", position, related=opener, found=char,
                                expected=_OPENERS[text[opener]])
            stack.pop()
            if not stack:
                return position
        position += 1
    raise ScanError("unclosed_bracket", stack[-1], expected=_OPENERS[text[stack[-1]]])


def strings_only(text: str) -> bool:
    """Check that a text consists only of string literals and separators.

    Used for the PEP 701 check: an f-string that :mod:`ast` (Python 3.12+)
    reads as one literal must also be one literal (or an implicit
    concatenation of literals) for the Python 3.11 tokenizer.  Otherwise it
    contains nested quotes of its own kind, which Primula does not allow
    (decision 30).

    Args:
        text: source text of a string expression.

    Returns:
        ``True`` if the text is string literals separated by whitespace,
        line continuations and comments only.
    """
    position = 0
    length = len(text)
    while position < length:
        char = text[position]
        if char in " \t\n\\":
            position += 1
            continue
        if char == "#":
            newline = text.find("\n", position)
            position = length if newline == -1 else newline
            continue
        quote = string_literal_at(text, position)
        if quote is None:
            return False
        try:
            position = skip_string(text, position, quote)
        except ScanError:
            return False
    return True
