"""Entry point of parsing: source + header -> :class:`~primula.syntax.nodes.Document`.

* Markup files (kinds ``document``, ``fragment``, ``module``): the body is
  parsed by :class:`~primula.syntax.blocks.BlockParser`, then implicit
  regions and lists are built by :func:`~primula.syntax.regions.organize`.
* Styles modules and projects (kinds ``styles``, ``project``): everything
  after the header is code (specification 2.2, grammar ``Body``
  constraint); the document holds one :class:`CodeBlock`.

``organize=False`` returns the flat block lists; evaluation (stage 13.3)
inserts ``|include`` fragments into them and organises afterwards, because
``|include`` is transparent for implicit regions (decision 31).
"""

from __future__ import annotations

from primula.diagnostics import DiagnosticSink
from primula.header import Header
from primula.source import Span
from primula.syntax import pyfrag, regions
from primula.syntax.blocks import BlockParser
from primula.syntax.nodes import CodeBlock, Document

#: File kinds whose body is code rather than markup.
CODE_KINDS = frozenset({"styles", "project"})


def parse(header: Header, sink: DiagnosticSink, *, organize: bool = True) -> Document:
    """Parse the body of a source file.

    Args:
        header: the parsed header of the file (gives the source, the body
            start and the kind).
        sink: diagnostics receiver.
        organize: build implicit regions and lists (default); ``False``
            keeps the flat block lists of the parser.

    Returns:
        The document tree.  Syntax errors are reported to ``sink``; the
        tree contains everything that could be parsed.
    """
    source = header.source
    document = Document(Span(source, header.body_start, len(source.text)), source, header.kind)
    if header.kind in CODE_KINDS:
        document.children.append(_code_body(header, sink))
        return document
    flat = BlockParser(header, sink).parse_document()
    document.children = regions.organize(flat, sink) if organize else flat
    return document


def _code_body(header: Header, sink: DiagnosticSink) -> CodeBlock:
    """Parse the body of a styles module or project as statements."""
    source = header.source
    start = header.body_start
    lines: list[tuple[int, int, str]] = []
    position = start
    while position <= len(source.text):
        end = source.text.find("\n", position)
        end = len(source.text) if end == -1 else end
        lines.append((position, 0, source.text[position:end]))
        if end >= len(source.text):
            break
        position = end + 1
    span = Span(source, start, len(source.text))
    try:
        code = pyfrag.parse_code(source, lines, span)
    except pyfrag.PySyntaxError as exc:
        sink.emit(exc.diagnostic)
        code = None
    return CodeBlock(span, code)
