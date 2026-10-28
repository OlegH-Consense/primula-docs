"""Second pass over flat block lists: implicit regions and lists.

The block parser returns flat lists of blocks.  :func:`organize` builds:

1. **implicit regions** of the line forms of ``|>`` and ``|!``
   (specification 3.6, decision 31): all following blocks belong to the
   region except those that close it:

   * a paragraph and a paragraph with a style ``|.Name:``;
   * a heading;
   * a clause of the same or a higher level (a smaller or equal number of
     ``>``);
   * the structural and page commands :data:`STRUCTURAL_COMMANDS`;
   * an ``|if``/``|for`` environment that has a heading or a clause of the
     same or a higher level at its top level;
   * the end of the enclosing environment or file.

   For an admonition region (9.1: "the same rule") any clause and the next
   admonition close the region, as a clause of the same level would;

2. **lists** (5.4, decision 32): consecutive items form a list, a blank
   line ends it; deeper items nest under the last item of the previous
   level; ``|list("Name")`` before a list sets its style.  Errors: a
   skipped level (P1232, also a list that starts below level 1), a marker
   prefix that does not match the parent items (P1233), bullet and
   numbered items mixed on one level of one list (P1234), a
   ``|list(…)`` command not followed by a list (P1239);

3. **list environments** ``|list(…):`` (decision 33): blank lines do not
   split the list; any other block belongs to the last item of the top
   level of the environment (the level of its first item); the
   environment must start with an item (P1241).

``|include`` is transparent for regions (decision 31): the content of a
fragment is treated as if it stood in its place.  Fragments are inserted
at stage 13.3, so this pass is applied to the *flat* lists after the
insertion; at stage 13.1 an ``|include`` is an ordinary block that belongs
to the region.

Blank lines are removed from the result; comments are kept.

The pass does not modify its input: nodes that get new children are
copied (:func:`dataclasses.replace`), so the same flat tree can be
organised for ``primula check`` and evaluated afterwards.
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from dataclasses import replace as _replace

from primula.diagnostics import DiagnosticSink, error
from primula.source import Span
from primula.syntax.nodes import (
    Admonition, BlankLine, Block, Clause, Command, Comment, DefBlock, ForBlock, Heading,
    IfBlock, ListBlock, ListItem, Paragraph, StyleBlock,
)

def replace(node, **changes):  # noqa: ANN001, ANN201 - same signature as dataclasses.replace
    """:func:`dataclasses.replace` that keeps extra attributes of evaluated
    nodes (``condition`` of ``--review``, ``env`` of formulas)."""
    copy = _replace(node, **changes)
    names = {item.name for item in fields(node)}
    for key, value in vars(node).items():
        if key not in names:
            setattr(copy, key, value)
    return copy


#: Commands that close an implicit region (decision 31).
STRUCTURAL_COMMANDS = frozenset({"page", "newpage", "section", "appendix", "scope", "document",
                                 "toc", "list_of", "header", "footer"})


def organize(blocks: list[Block], sink: DiagnosticSink) -> list[Block]:
    """Build implicit regions and lists in a flat block list (recursively).

    Args:
        blocks: flat blocks of one container, as returned by the parser.
        sink: receiver of list errors.

    Returns:
        The organised blocks (blank lines removed).
    """
    nested = [_organize_inside(block, sink) for block in blocks]
    regions = _build_regions(nested)
    return _group_lists(regions.top, sink, regions)


# ----------------------------------------------------------------------
# Containers
# ----------------------------------------------------------------------


def _organize_inside(block: Block, sink: DiagnosticSink) -> Block:
    """Organise the children of environments; convert ``|list:`` environments.

    Returns a copy of the block when its children change (the input tree is
    not modified); line forms of ``|>``/``|!`` are copied too, because their
    regions are filled by :func:`_build_regions`.
    """
    if isinstance(block, (Clause, Admonition, StyleBlock)) and block.form == "env":
        return replace(block, children=organize(block.children, sink))
    if isinstance(block, Command) and block.form == "env":
        if block.name == "list":
            return _list_environment(block, sink)
        return replace(block, children=organize(block.children, sink))
    if isinstance(block, IfBlock):
        return replace(block, branches=[replace(branch, children=organize(branch.children, sink))
                                        for branch in block.branches])
    if isinstance(block, (ForBlock, DefBlock)):
        return replace(block, children=organize(block.children, sink))
    if isinstance(block, (Clause, Admonition)):
        return replace(block, children=list(block.children))
    if isinstance(block, ListItem):
        return replace(block, children=list(block.children))
    return block


# ----------------------------------------------------------------------
# Implicit regions
# ----------------------------------------------------------------------


@dataclass
class _Regions:
    """Result of region building: top-level blocks and the region owners."""

    top: list[Block] = field(default_factory=list)
    owners: list[Block] = field(default_factory=list)


def _opens_region(block: Block) -> bool:
    return isinstance(block, (Clause, Admonition)) and block.form == "line"


def _top_blocks(block: Block) -> list[Block]:
    """Blocks at the top level of an ``|if``/``|for`` environment."""
    if isinstance(block, IfBlock):
        return [child for branch in block.branches for child in branch.children]
    if isinstance(block, ForBlock):
        return list(block.children)
    return []


def _closes(region: Block, block: Block) -> bool:
    """Does ``block`` close the implicit region of ``region``?"""
    if isinstance(block, (Paragraph, StyleBlock, Heading)):
        return True
    if isinstance(block, Command) and block.name in STRUCTURAL_COMMANDS:
        return True
    if isinstance(block, Clause):
        return isinstance(region, Admonition) or block.level <= region.level  # type: ignore[union-attr]
    if isinstance(block, Admonition):
        return isinstance(region, Admonition)
    if isinstance(block, (IfBlock, ForBlock)):
        for child in _top_blocks(block):
            if isinstance(child, Heading):
                return True
            if isinstance(child, Command) and child.name in STRUCTURAL_COMMANDS:
                return True  # e.g. |document in a loop over acts (decision 118)
            if isinstance(child, Clause) and (isinstance(region, Admonition)
                                              or child.level <= region.level):  # type: ignore[union-attr]
                return True
    return False


def _build_regions(blocks: list[Block]) -> _Regions:
    """Move blocks into the implicit regions of ``|>`` and ``|!`` line forms."""
    result = _Regions()
    stack: list[Block] = []
    for block in blocks:
        while stack and _closes(stack[-1], block):
            stack.pop()
        target = stack[-1].children if stack else result.top  # type: ignore[union-attr]
        target.append(block)
        if _opens_region(block):
            stack.append(block)
            result.owners.append(block)
    return result


# ----------------------------------------------------------------------
# Lists
# ----------------------------------------------------------------------


class _ListBuilder:
    """Places list items of one list into nested :class:`ListBlock` levels.

    Args:
        root: the top-level list.
        sink: receiver of P1232-P1234.
        base: level of the first item of the list (1 for implicit lists,
            the level of the first item in a ``|list:`` environment).
    """

    def __init__(self, root: ListBlock, sink: DiagnosticSink, base: int = 1) -> None:
        self.root = root
        self.sink = sink
        self.base = base
        self.levels: list[ListBlock] = []
        self.last: list[ListItem] = []

    def add(self, item: ListItem) -> None:
        """Add an item, checking level, prefix and type."""
        depth = item.level - self.base + 1
        if depth > len(self.levels) + 1 or depth < 1:
            self.sink.emit(error("P1232", item.span, level=item.level,
                                 previous=len(self.levels) + self.base - 1))
            depth = max(1, min(depth, len(self.levels) + 1))
        if depth == len(self.levels) + 1:
            if depth == 1:
                target = self.root
            else:
                target = ListBlock(item.span)
                self.last[depth - 2].children.append(target)
            self.levels.append(target)
            self.last.append(item)
        else:
            del self.levels[depth:]
            del self.last[depth:]
            target = self.levels[depth - 1]
            self.last[depth - 1] = item
        expected = "".join(parent.marker[-1] for parent in self.last[:depth - 1])
        prefix = item.marker[:-1][-(depth - 1):] if depth > 1 else ""
        if depth > 1 and prefix != expected:
            self.sink.emit(error("P1233", item.span, marker=item.marker,
                                 expected=item.marker[:-1][:-(depth - 1)] + expected + item.marker[-1]))
        if target.items and target.items[0].kind != item.kind:
            self.sink.emit(error("P1234", item.span, level=item.level).hint("help.split_lists"))
        target.items.append(item)
        # Implicit lists span from their first item to the last item added
        # at any depth; an environment list keeps the span of |list:.
        for level in self.levels:
            if level.form != "env":
                level.span = Span(item.span.source, level.items[0].span.start, item.span.end)


def _group_lists(blocks: list[Block], sink: DiagnosticSink, regions: _Regions | None = None) -> list[Block]:
    """Group consecutive items into lists in ``blocks`` and in region owners."""
    if regions is not None:
        for owner in regions.owners:
            owner.children = _group_sequence(owner.children, sink)  # type: ignore[union-attr]
    return _group_sequence(blocks, sink)


def _group_sequence(blocks: list[Block], sink: DiagnosticSink) -> list[Block]:
    """Group list items of one sequence; remove blank lines."""
    result: list[Block] = []
    builder: _ListBuilder | None = None
    pending: Command | None = None
    for block in blocks:
        if isinstance(block, ListItem):
            if builder is None:
                root = ListBlock(block.span, style=pending)
                pending = None
                builder = _ListBuilder(root, sink)
                result.append(root)
            builder.add(block)
            continue
        if isinstance(block, BlankLine):
            builder = None
            continue
        if isinstance(block, Comment) and builder is not None:
            continue
        builder = None
        if isinstance(block, Command) and block.name == "list" and block.form == "bare":
            if pending is not None:
                sink.emit(error("P1239", pending.span))
            pending = block
            continue
        if pending is not None:
            sink.emit(error("P1239", pending.span))
            pending = None
        result.append(block)
    if pending is not None:
        sink.emit(error("P1239", pending.span))
    return result


def _list_environment(command: Command, sink: DiagnosticSink) -> ListBlock:
    """Convert a ``|list(…):`` environment to a :class:`ListBlock` (decision 33)."""
    children = [_organize_inside(child, sink) for child in command.children]
    root = ListBlock(command.span, style=replace(command, children=[]), form="env")
    builder: _ListBuilder | None = None
    for child in children:
        if isinstance(child, (BlankLine, Comment)):
            continue
        if isinstance(child, ListItem):
            if builder is None:
                builder = _ListBuilder(root, sink, base=child.level)
            builder.add(child)
            continue
        if builder is None:
            sink.emit(error("P1241", child.span))
            continue
        builder.last[0].children.append(child)
    if builder is None:
        sink.emit(error("P1241", command.span))
    root.span = command.span
    return root
