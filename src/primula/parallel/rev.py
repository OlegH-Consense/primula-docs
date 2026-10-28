"""Freshness of translations: ``status`` and ``rev`` of track blocks (specification 7.7, decision 134; stage 16.5).

``rev="3f9a2c/81b0d4"`` holds two hashes taken when a translation was
confirmed: of the normalized text of the block of the primary track and of
the normalized text of the block itself.  A changed primary block is P5320
(the translation is outdated), a changed confirmed block is P5321.

The normalized text of a track block (7.7):

* the body of the block without the ``|track(…)`` line (the line form:
  the text inside the braces);
* every ``|include`` line followed by the text of the included fragment
  without its header (recursively);
* comments ``|%`` and ``|comment:`` environments removed;
* NFC; every line stripped, runs of spaces and tabs inside a line made one
  space; runs of blank lines made one, blank lines at the start and the end
  removed; lines joined by LF.

The hash is the first 6 hexadecimal digits (lower case) of SHA-256 of the
UTF-8 bytes.  Expressions ``|(…)`` take part as written: a changed
expression is a change, a changed value of a parameter is not.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from typing import Any, Callable

from primula.structure.tree import iter_tree
from primula.syntax import nodes as N

#: ``rev`` of a track block: the hash of the primary block / the hash of the block itself.
REV = re.compile(r"^([0-9a-f]{6})/([0-9a-f]{6})$")
#: A comment to the end of the line; ``||`` before ``%`` is a literal bar.
_COMMENT = re.compile(r"(?<!\|)\|%.*$")
_SPACES = re.compile(r"[ \t]+")

#: ``(text of a fragment body, its parsed blocks)`` of an ``|include`` node, or ``None``.
Resolver = Callable[[Any], "tuple[str, int, list[Any]] | None"]


def parse_rev(value: str) -> tuple[str, str] | None:
    """``"3f9a2c/81b0d4"`` -> ``("3f9a2c", "81b0d4")``; ``None`` for another form."""
    match = REV.match(value)
    return (match.group(1), match.group(2)) if match else None


def normalize(text: str) -> str:
    """The normalized form of block text (comments, spaces, blank lines; NFC)."""
    lines = []
    for line in unicodedata.normalize("NFC", text).split("\n"):
        line = _SPACES.sub(" ", _COMMENT.sub("", line)).strip()
        if line or (lines and lines[-1]):
            lines.append(line)
    while lines and not lines[-1]:
        lines.pop()
    return "\n".join(lines)


def text_hash(text: str) -> str:
    """The 6-digit hash of a normalized text."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:6]


def _body_range(block: N.Command, text: str) -> tuple[int, int]:
    """Offsets of the body of a track block in its source text."""
    if block.form == "inline":
        start = text.find("{", block.args.span.end if block.args is not None else block.span.start)
        end = block.span.end - 1 if text[block.span.end - 1:block.span.end] == "}" else block.span.end
        return (start + 1, end) if 0 <= start < end else (end, end)
    start = text.find("\n", block.span.start)
    start = len(text) if start < 0 else start + 1
    children = [child for child in block.children if not isinstance(child, N.BlankLine)]
    end = max((child.span.end for child in children), default=start)
    return start, max(start, end)


def _with_fragments(text: str, start: int, end: int, blocks: list[Any], resolve: Resolver, depth: int) -> str:
    """The text between ``start`` and ``end`` without ``|comment:`` blocks, each ``|include`` line
    followed by the text of its fragment."""
    cuts: list[tuple[int, int, str]] = []
    for node in iter_tree(blocks):
        if not hasattr(node, "span") or not start <= node.span.start < end:
            continue
        if isinstance(node, N.CommentBlock):
            cuts.append((node.span.start, min(node.span.end, end), ""))
        elif isinstance(node, N.Command) and node.name == "include" and depth < 16:
            fragment = resolve(node)
            if fragment is not None:
                body, body_start, children = fragment
                line_end = text.find("\n", node.span.start)
                line_end = end if line_end < 0 or line_end > end else line_end
                inserted = _with_fragments(body, body_start, len(body), children, resolve, depth + 1)
                cuts.append((line_end, line_end, "\n" + inserted))
    pieces, cursor = [], start
    for cut_start, cut_end, insert in sorted(cuts):
        if cut_start < cursor:
            continue
        pieces.append(text[cursor:cut_start])
        pieces.append(insert)
        cursor = max(cursor, cut_end)
    pieces.append(text[cursor:end])
    return "".join(pieces)


def block_hash(block: N.Command, resolve: Resolver) -> str:
    """The hash of a parsed track block (the normalized text of 7.7)."""
    text = block.span.source.text
    start, end = _body_range(block, text)
    body = _with_fragments(text, start, end, list(block.children) + list(block.body or []), resolve, 0)
    return text_hash(normalize(body))
