"""Nodes of the Primula document tree (result of parsing, stage 13.1).

The tree follows the grammar of appendix 1 and the region rules of section 3.6.
Every node has a :class:`~primula.source.Span`; Python fragments keep their
AST and position map (:mod:`primula.syntax.pyfrag`).

Conventions:

* *inline* nodes form the content of paragraphs, line bodies and ``{…}``
  bodies; *block* nodes form documents and environments;
* ``form`` of a block construct is ``"line"`` (the single-line form,
  ``|> текст``), ``"env"`` (``:`` … closing marker) or ``"bare"``
  (a line command without a body, ``|newpage``);
* line forms of ``|>`` and ``|!`` own their implicit region: the blocks
  that follow them are moved into ``children`` by
  :mod:`primula.syntax.regions`;
* names of commands are not resolved: by principle 3 of the specification
  the construct is determined by syntax alone; whether ``|img`` or
  ``|sign`` exists is checked at evaluation (stage 13.3).

:func:`dump` writes a tree as indented S-expressions for golden tests and
``primula check --dump-tree``.
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from typing import Union

from primula.source import SourceFile, Span
from primula.syntax.pyfrag import PyArgs, PyCode, PyDef, PyExpr, PyFor


@dataclass(eq=False)
class Node:
    """Base class: every node has a span."""

    span: Span


# ----------------------------------------------------------------------
# Inline nodes (grammar section 4)
# ----------------------------------------------------------------------


@dataclass(eq=False)
class Text(Node):
    """Literal text after escapes and whitespace normalisation.

    ``|~`` is stored as U+00A0, ``||``, ``|{``, ``|}`` as the characters;
    a line break inside a paragraph and the indentation after it become a
    single space (section 4.1).
    """

    value: str


@dataclass(eq=False)
class LineBreak(Node):
    """``|\\`` — line break inside a paragraph."""


@dataclass(eq=False)
class Comment(Node):
    """``|%`` comment (inline or a whole line); no output."""

    text: str


@dataclass(eq=False)
class Expr(Node):
    """``|(expr)`` — value of an expression inserted as text."""

    expr: PyExpr


@dataclass(eq=False)
class Formula(Node):
    """``|=(expr)`` — deferred table cell formula (section 6.8)."""

    expr: PyExpr


@dataclass(eq=False)
class Short(Node):
    """Inline short form ``|*{…}``, ``|/{…}``… (section 3.3).

    Attributes:
        mark: one of ``* / _ ^ , ` " ? —``.
    """

    mark: str
    args: PyArgs | None
    body: list["Inline"] = field(default_factory=list)


@dataclass(eq=False)
class StyleRef(Node):
    """A style reference after ``|.``: a static name or ``(expression)``."""

    name: str | None
    expr: PyExpr | None = None


@dataclass(eq=False)
class StyleSpan(Node):
    """``|.Name{…}`` / ``|.(expr){…}`` — character style (section 4.3)."""

    style: StyleRef
    args: PyArgs | None
    body: list["Inline"] = field(default_factory=list)


@dataclass(eq=False)
class Reference(Node):
    """``|@("id", mode)`` — cross-reference (section 5.7)."""

    args: PyArgs


@dataclass(eq=False)
class InlineCommand(Node):
    """``|name(args){body}`` inside text (section 3.2)."""

    name: str
    name_span: Span
    args: PyArgs | None
    body: list["Inline"] | None = None


@dataclass(eq=False)
class InlineBranch(Node):
    """One branch of :class:`InlineIf`.

    Attributes:
        cond: the condition; ``None`` for ``|else`` (or after an error in it).
        keyword: ``if``, ``elif`` or ``else``.
    """

    cond: PyExpr | None
    body: list["Inline"] = field(default_factory=list)
    keyword: str = "if"


@dataclass(eq=False)
class InlineIf(Node):
    """``|if(c){…} |elif(c){…} |else{…}`` inside text (decision 21)."""

    branches: list[InlineBranch] = field(default_factory=list)


@dataclass(eq=False)
class InlineFor(Node):
    """``|for(x in items){…}`` inside text (decision 21)."""

    loop: PyFor
    body: list["Inline"] = field(default_factory=list)


Inline = Union[Text, LineBreak, Comment, Expr, Formula, Short, StyleSpan, Reference,
               InlineCommand, InlineIf, InlineFor]


# ----------------------------------------------------------------------
# Block nodes (grammar section 3)
# ----------------------------------------------------------------------


@dataclass(eq=False)
class Paragraph(Node):
    """Consecutive text lines (section 4.1)."""

    body: list[Inline] = field(default_factory=list)


@dataclass(eq=False)
class Heading(Node):
    """``|<`` … ``|<<<<<<`` — heading; level by markers (section 5.2)."""

    level: int
    args: PyArgs | None
    body: list[Inline] = field(default_factory=list)


@dataclass(eq=False)
class Clause(Node):
    """``|>`` — clause (sections 3.6, 5.3).

    Line form: ``body`` is the text of the clause line, ``children`` the
    implicit region.  Environment form: ``body`` is empty, ``children``
    the blocks of the environment (the first paragraph gets the number).
    """

    level: int
    args: PyArgs | None
    form: str
    body: list[Inline] = field(default_factory=list)
    children: list["Block"] = field(default_factory=list)


@dataclass(eq=False)
class Admonition(Node):
    """``|!("kind")`` — admonition (section 9.1); forms as :class:`Clause`."""

    args: PyArgs | None
    form: str
    body: list[Inline] = field(default_factory=list)
    children: list["Block"] = field(default_factory=list)


@dataclass(eq=False)
class StyleBlock(Node):
    """``|.Name: …`` or ``|.Name:`` … ``|end.Name`` — paragraph style (4.3)."""

    style: StyleRef
    args: PyArgs | None
    form: str
    body: list[Inline] = field(default_factory=list)
    children: list["Block"] = field(default_factory=list)


@dataclass(eq=False)
class ListItem(Node):
    """``|-``, ``|#``, ``|#-``… — list item (section 5.4).

    Attributes:
        marker: the marker characters; ``len(marker)`` is the level.
        body: the item text.
        children: nested lists and (in a ``|list:`` environment) blocks
            attached to the item.
    """

    marker: str
    args: PyArgs | None
    body: list[Inline] = field(default_factory=list)
    children: list["Block"] = field(default_factory=list)

    @property
    def level(self) -> int:
        """Nesting level, from 1."""
        return len(self.marker)

    @property
    def kind(self) -> str:
        """``bullet`` (``-``) or ``number`` (``#``): the last marker character."""
        return "number" if self.marker.endswith("#") else "bullet"


@dataclass(eq=False)
class ListBlock(Node):
    """A list: consecutive items of one level with their nested lists.

    Attributes:
        items: items of this level.
        style: the ``|list("Name")`` command or environment that sets the
            style of this list, if any.
        form: ``"implicit"`` (items in text) or ``"env"`` (``|list:``).
    """

    items: list[ListItem] = field(default_factory=list)
    style: "Command | None" = None
    form: str = "implicit"


@dataclass(eq=False)
class Cell(Node):
    """A cell of a compact table row; ``args`` belong to the cell (6.4)."""

    args: PyArgs | None
    body: list[Inline] = field(default_factory=list)


@dataclass(eq=False)
class TableRow(Node):
    """``|:`` compact table row (section 6.4)."""

    args: PyArgs | None
    cells: list[Cell] = field(default_factory=list)


@dataclass(eq=False)
class Command(Node):
    """A long line command or environment: ``|name(args)``,
    ``|name(args): text``, ``|name(args):`` … ``|end name``.

    Covers built-in environments (``table``, ``page``, ``row``, ``cell``,
    ``list``…) and calls of user macros alike.
    """

    name: str
    name_span: Span
    args: PyArgs | None
    form: str
    body: list[Inline] = field(default_factory=list)
    children: list["Block"] = field(default_factory=list)


@dataclass(eq=False)
class IfBranch(Node):
    """A branch of :class:`IfBlock`; ``cond`` is ``None`` for ``|else:``."""

    cond: PyExpr | None
    children: list["Block"] = field(default_factory=list)


@dataclass(eq=False)
class IfBlock(Node):
    """``|if(c):`` … ``|elif(c):`` … ``|else:`` … ``|endif``."""

    branches: list[IfBranch] = field(default_factory=list)


@dataclass(eq=False)
class ForBlock(Node):
    """``|for(x in items):`` … ``|endfor``."""

    loop: PyFor
    children: list["Block"] = field(default_factory=list)


@dataclass(eq=False)
class DefBlock(Node):
    """``|def name(params):`` … ``|enddef`` — user command (macro)."""

    name: str
    func: PyDef
    children: list["Block"] = field(default_factory=list)


@dataclass(eq=False)
class CodeBlock(Node):
    """``|code:`` … ``|end``, or the code section of a styles module/project."""

    code: PyCode | None


@dataclass(eq=False)
class Verbatim(Node):
    """``|verbatim:`` … ``|end`` — literal lines (indentation of the opening
    line removed, decision 24)."""

    text: str
    marker: str


@dataclass(eq=False)
class CommentBlock(Node):
    """``|comment:`` … ``|end`` — ignored content (section 3.7)."""


@dataclass(eq=False)
class BlankLine(Node):
    """A blank line; used while grouping lists and removed afterwards."""


Block = Union[Paragraph, Heading, Clause, Admonition, StyleBlock, ListItem, ListBlock,
              TableRow, Command, IfBlock, ForBlock, DefBlock, CodeBlock, Verbatim,
              CommentBlock, Comment, BlankLine]


@dataclass(eq=False)
class Document(Node):
    """Root of a parsed file.

    Attributes:
        source: the source file.
        kind: file kind (header ``kind``, else the sub-extension).
        children: top-level blocks.
    """

    source: SourceFile
    kind: str
    children: list[Block] = field(default_factory=list)


# ----------------------------------------------------------------------
# Dump
# ----------------------------------------------------------------------

_SKIP_FIELDS = {"span", "source", "name_span"}
#: Attributes added by evaluation and styles (shown in dumps when set).
_EXTRA_ATTRIBUTES = ("condition", "style_use", "char_style", "list_style", "table_style", "block_style",
                     "admonition_style", "page_style")


def _node_name(node: Node) -> str:
    """Kebab-case name of a node class (``ListItem`` -> ``list-item``)."""
    name = type(node).__name__
    return "".join("-" + c.lower() if c.isupper() and i else c.lower() for i, c in enumerate(name))


def _quote(text: str) -> str:
    """Quote a string for the dump (JSON-like escapes, non-ASCII kept)."""
    escaped = (text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
               .replace("\t", "\\t").replace("\u00a0", "\\u00a0"))
    return '"' + escaped + '"'


def _python_text(value: object) -> str | None:
    """Source text of a Python wrapper for the dump, or ``None``."""
    if hasattr(value, "dump_text"):
        return value.dump_text()  # evaluated arguments (stage 13.3)
    if isinstance(value, (PyArgs, PyExpr, PyFor)):
        return value.text
    if isinstance(value, PyDef):
        return value.span.text()
    if isinstance(value, PyCode):
        return value.fragment.text
    return None


def dump(node: Node, *, positions: bool = True) -> str:
    """Write a tree as indented S-expressions.

    Each node is ``(name line:col attr=value … children…)``; Python
    fragments are shown as their source text, lists of nodes as nested
    groups.

    Args:
        node: the root node.
        positions: include ``line:col`` of every node.

    Returns:
        The dump text (ends without a newline).
    """
    lines: list[str] = []
    _dump(node, 0, lines, positions)
    return "\n".join(lines)


def _dump(node: Node, depth: int, out: list[str], positions: bool) -> None:
    indent = "  " * depth
    head = [_node_name(node)]
    if positions:
        position = node.span.begin_position
        head.append(f"{position.line}:{position.column}")
    groups: list[tuple[str, list[Node]]] = []
    singles: list[tuple[str, Node]] = []
    for item in fields(node):
        if item.name in _SKIP_FIELDS:
            continue
        value = getattr(node, item.name)
        if value is None or value == [] or (item.name == "form" and value == "implicit"):
            continue
        python = _python_text(value)
        if python is not None:
            head.append(f"{item.name}={_quote(python)}")
        elif isinstance(value, Node):
            singles.append((item.name, value))
        elif isinstance(value, list):
            groups.append((item.name, value))
        elif isinstance(value, str):
            head.append(f"{item.name}={_quote(value)}")
        else:
            head.append(f"{item.name}={value}")
    for name in _EXTRA_ATTRIBUTES:
        value = getattr(node, name, None)
        if value is not None:
            text = value.dump_text() if hasattr(value, "dump_text") else str(value)
            head.append(f"{name}={_quote(text)}")
    if not groups and not singles:
        out.append(f"{indent}({' '.join(head)})")
        return
    out.append(f"{indent}({' '.join(head)}")
    for name, child in singles:
        out.append(f"{indent}  :{name}")
        _dump(child, depth + 2, out, positions)
    for name, children in groups:
        out.append(f"{indent}  :{name}")
        for child in children:
            _dump(child, depth + 2, out, positions)
    out[-1] += ")"
