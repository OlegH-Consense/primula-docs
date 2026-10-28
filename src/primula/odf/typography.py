"""``typography(nbsp_short=True)``: no-break spaces after short words in the whole ODT (stage 13.9d).

Library 7: «``typography(nbsp_short=True)`` applies the replacement to the
whole text of the document when the ODT is written, including tables,
headers and footers, captions and notes; it is not applied to verbatim
blocks, code, the monospace ``|`{…}`` and Writer fields».

The pass runs over the finished XML of ``content.xml`` and ``styles.xml``
(headers and footers), so it sees text exactly as it is written: words
and the spaces after them may lie in different nodes of the document tree
(«в |*{домі}» — «в » in the paragraph, «домі» in a span).  Each paragraph
(``text:p``, ``text:h``) is read as one flow of characters:

* text of ``text:span`` and ``text:a`` is part of the flow;
* ``text:s``, ``text:tab`` and ``text:line-break`` are whitespace (a no-break
  space is not put before them);
* any other element (fields, notes, frames, bookmarks, index marks) is an
  opaque non-space character: its own text is left as it is, the text after
  it (``tail``) continues the flow;
* elements marked by the content writer as raw (verbatim paragraphs and
  ``|`{…}`` spans) are opaque too.

Paragraphs inside notes, frames and table cells are separate flows; the
paragraphs of ``office:annotation`` (``--review`` comments) are not changed.
The rule of a match is that of :func:`primula.library.text.apply_nbsp`:
a short word as a whole word (case-insensitive), then spaces, then a
non-space character; the spaces become one no-break space.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from typing import Iterable

from primula.library.context import NBSP
from primula.odf.xml import qn

_PARAGRAPHS = {qn("text:p"), qn("text:h")}
_INLINE = {qn("text:span"), qn("text:a")}
_SPACE = {qn("text:s"), qn("text:tab"), qn("text:line-break")}
_SKIP = {qn("office:annotation")}
#: Stand-ins of non-text elements in the flow of a paragraph.
_OPAQUE = "￼"
_WHITESPACE = "\n"


class _Segment:
    """A piece of text of the flow: ``element.text`` or ``element.tail``."""

    __slots__ = ("element", "attr", "start", "end")

    def __init__(self, element: ET.Element, attr: str, start: int, end: int) -> None:
        self.element, self.attr, self.start, self.end = element, attr, start, end


def _pattern(words: list[str]) -> re.Pattern[str] | None:
    """The pattern of short words followed by spaces, or ``None`` for no words."""
    if not words:
        return None
    return re.compile(r"(?<![\w'ʼ’-])(?:" + "|".join(re.escape(w) for w in sorted(words, key=len, reverse=True))
                      + r")( +)(?=[^\s])", re.IGNORECASE)


def apply_nbsp_short(roots: Iterable[ET.Element], words: list[str], raw: set[int],
                     own: dict[int, list[str]] | None = None) -> None:
    """Put no-break spaces after the short ``words`` in every paragraph under ``roots``.

    Args:
        roots: the root elements of ``content.xml`` and ``styles.xml``.
        words: the short words (``typography(nbsp_words=…)`` or the defaults
            of the document language); nothing is done for an empty list.
        raw: ``id()`` of the elements whose text must stay as written
            (verbatim paragraphs, ``|`{…}`` spans).
        own: ``id()`` of elements written in another language (track blocks
            of ``|parallel``, 7.7) -> their short words; the element and its
            content use them instead of ``words``.
    """
    patterns = {key: _pattern(value) for key, value in (own or {}).items()}
    pattern = _pattern(words)
    if pattern is None and not any(patterns.values()):
        return
    for root in roots:
        _walk(root, pattern, raw, patterns)


def _walk(element: ET.Element, pattern: re.Pattern[str] | None, raw: set[int],
          patterns: dict[int, re.Pattern[str] | None]) -> None:
    if element.tag in _SKIP or id(element) in raw:
        return
    if id(element) in patterns:
        pattern = patterns[id(element)]
    if element.tag in _PARAGRAPHS and pattern is not None:
        _paragraph(element, pattern, raw)
    for child in element:
        _walk(child, pattern, raw, patterns)


def _paragraph(paragraph: ET.Element, pattern: re.Pattern[str], raw: set[int]) -> None:
    """Rewrite the flow of one paragraph (its nested paragraphs are separate flows)."""
    chars: list[str] = []
    segments: list[_Segment] = []

    def text_of(element: ET.Element, attr: str) -> None:
        value = getattr(element, attr)
        if value:
            segments.append(_Segment(element, attr, len(chars), len(chars) + len(value)))
            chars.extend(value)

    def inline(element: ET.Element) -> None:
        text_of(element, "text")
        for child in element:
            if child.tag in _INLINE and id(child) not in raw:
                inline(child)
            else:
                chars.append(_WHITESPACE if child.tag in _SPACE else _OPAQUE)
            text_of(child, "tail")

    inline(paragraph)
    flow = "".join(chars)
    changes: dict[int, str] = {}
    for match in pattern.finditer(flow):
        start, end = match.span(1)
        changes[start] = NBSP
        for index in range(start + 1, end):
            changes[index] = ""
    if not changes:
        return
    for segment in segments:
        if any(segment.start <= index < segment.end for index in changes):
            value = "".join(changes.get(i, chars[i]) for i in range(segment.start, segment.end))
            setattr(segment.element, segment.attr, value)
