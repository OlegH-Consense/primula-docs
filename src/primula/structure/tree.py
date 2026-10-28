"""Walking document trees (parsed or evaluated) in document order.

The structure phase (stage 13.6) and the evaluator need every node of a
subtree: blocks, their inline bodies, list items, table cells and the
branches of control constructs.  :func:`iter_tree` yields them depth-first
in the order of the source, so counters and "first definition" rules see
nodes as the reader does.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Iterator
from typing import Any

#: Attributes that hold nested nodes, in document order.
_NESTED = ("body", "cells", "items", "branches", "children")


def iter_tree(nodes: Iterable[Any]) -> Iterator[Any]:
    """Yield every node of ``nodes`` and of their subtrees (pre-order).

    Args:
        nodes: top-level nodes (blocks or inline nodes).

    Returns:
        An iterator over the nodes; a node comes before its body, its body
        (the paragraph text of a clause) before its children.
    """
    stack: list[Iterator[Any]] = [iter(nodes)]
    while stack:
        try:
            node = next(stack[-1])
        except StopIteration:
            stack.pop()
            continue
        yield node
        nested: list[Any] = []
        for name in _NESTED:
            value = getattr(node, name, None)
            if isinstance(value, list):
                nested.extend(value)
        if nested:
            stack.append(iter(nested))


def plain_text(nodes: Iterable[Any], quotes: tuple[tuple[str, str], tuple[str, str]] | None = None,
               depth: int = 0) -> str:
    """Plain text of inline nodes (reference titles, index entries).

    Formatting is dropped; ``|"{…}`` gets the quotes of the document
    language; notes, comments and unresolved forms give no text; a
    resolved reference gives its text.

    Args:
        nodes: inline nodes of the evaluated tree.
        quotes: (outer, inner) quote pairs of the document language.
        depth: nesting depth of quotes.

    Returns:
        The text with runs of spaces, tabs and line ends collapsed.
    """
    from primula.syntax import nodes as N

    parts: list[str] = []
    for node in nodes:
        if isinstance(node, N.Text):
            parts.append(node.value)
        elif isinstance(node, N.LineBreak):
            parts.append(" ")
        elif isinstance(node, N.Short) and node.mark == '"':
            pair = (quotes or (("«", "»"), ("„", "“")))[depth % 2]
            parts.append(pair[0] + plain_text(node.body, quotes, depth + 1) + pair[1])
        elif isinstance(node, (N.Short, N.StyleSpan)):
            parts.append(plain_text(node.body, quotes, depth))
        elif isinstance(node, N.InlineCommand):
            if node.name not in ("footnote", "endnote", "index", "abbr") and node.body:
                parts.append(plain_text(node.body, quotes, depth))
        elif isinstance(node, N.Reference):
            resolved = getattr(node, "resolved", None)
            if resolved is not None and resolved.text:
                parts.append(resolved.text)
    # Collapse ordinary whitespace only: no-break spaces (U+00A0, U+202F)
    # of numbers and labels are kept.
    return re.sub(r"[ \t\n\r]+", " ", "".join(parts)).strip(" ")
