"""Annotations of the structure phase (stage 13.6) read by the ODT writer.

The structure phase does not rebuild the evaluated tree: it sets
attributes on its nodes (as the styles phase sets ``style_use``):

========================  =================================================
Attribute                 Node and meaning
========================  =================================================
``struct``                headings, clauses, admonitions, sections:
                          :class:`BlockInfo` (number text, bookmark, index
                          mark)
``appendix_info``         ``|appendix``: :class:`AppendixInfo`
``caption_info``          ``|table``, ``|figure``: :class:`CaptionInfo`
``note_info``             ``|footnote``, ``|endnote``: :class:`NoteInfo`
``resolved``              ``|@``: :class:`Resolved`
``list_info``             numbered lists with ``id``/``start``/``continues``:
                          :class:`ListInfo`
``index_info``            ``|toc``, ``|list_of``: :class:`IndexInfo`
========================  =================================================
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from primula.source import Span


@dataclass
class IndexMark:
    """An index entry mark: ``text:toc-mark`` or ``text:user-index-mark``.

    Attributes:
        index: ``toc``, ``figure`` or ``table``.
        text: entry text (``text:string-value``).
        level: outline level of the entry.
    """

    index: str
    text: str
    level: int = 1


@dataclass
class BlockInfo:
    """Number and anchors written at the start of a paragraph.

    Attributes:
        number: composite number («1.2», «А.1») or ``None``.
        prefix: text written before the paragraph text: the formatted
            number with its separator (decision 69).
        bookmark: bookmark name (the ID or an automatic name) or ``None``.
        marks: index marks written at the start of the paragraph.
    """

    number: str | None = None
    prefix: str | None = None
    #: Character style of the number in ``prefix`` (``structure_styles(clause_number=…)``).
    prefix_style: str | None = None
    bookmark: str | None = None
    marks: list[IndexMark] = field(default_factory=list)


@dataclass
class AppendixInfo:
    """``|appendix``: designation, subtitle and title paragraphs (5.5, decision 71)."""

    designation: str
    subtitle: str | None
    title: str | None
    bookmark: str | None
    page_break: bool
    marks: list[IndexMark] = field(default_factory=list)
    #: ``appendices(title_format=…)``: designation and title as one paragraph (decision 120).
    combined: str | None = None
    #: Outline level of the appendix heading (Writer navigator, PDF bookmarks; decision 122).
    outline: int = 1


@dataclass
class CaptionInfo:
    """Caption of a table or figure (5.8).

    The caption is ``before`` + title markup + ``after``: the format
    «Таблиця {n} — {title}» is split at ``{title}``.

    Attributes:
        kind: ``table`` or ``figure``.
        number: composite number.
        before: text before the title (the number substituted).
        title: inline nodes of the title.
        after: text after the title.
        position: ``above`` or ``below``.
        bookmark: bookmark name or ``None``.
        marks: index marks (lists of figures and tables).
    """

    kind: str
    number: str | None
    before: str
    title: list[Any]
    after: str
    position: str
    bookmark: str | None
    marks: list[IndexMark] = field(default_factory=list)


@dataclass
class NoteInfo:
    """A footnote or endnote (5.10, decision 76).

    Attributes:
        note_class: ``footnote`` or ``endnote``.
        note_id: ``text:id`` of the note (``ftn1``, ``edn1``).
        citation: the computed citation («1», «ii»).
        label: a custom citation (``format="*"``) or ``None``.
    """

    note_class: str
    note_id: str
    citation: str
    label: str | None = None


@dataclass
class Resolved:
    """A resolved cross-reference (5.7, decisions 72, 75, 76).

    Attributes:
        mode: ``number``, ``label``, ``title`` or ``page``.
        text: the computed text (for ``page`` — a placeholder Writer replaces).
        bookmark: target bookmark (hyperlink or ``text:bookmark-ref``).
        note_class, note_id: for references to notes (``text:note-ref``).
    """

    mode: str
    text: str
    bookmark: str | None = None
    note_class: str | None = None
    note_id: str | None = None


@dataclass
class ListInfo:
    """Named numbered list sequence (5.4): ``xml:id`` and continuation."""

    xml_id: str | None = None
    continue_list: str | None = None
    start: int | None = None


@dataclass
class IndexEntry:
    """A visible entry of a table of contents or list.

    ``forced``: included by ``toc=True`` although deeper than ``max_level``
    of the ``|toc`` (decision 122).
    """

    level: int
    text: str
    bookmark: str | None
    forced: bool = False
    #: The track of ``|parallel`` the entry belongs to (7.7), ``None`` outside the tracks;
    #: ``primary``: it is the primary track (the entry is in the indexes of the document).
    track: str | None = None
    primary: bool = False


@dataclass
class IndexInfo:
    """``|toc`` or ``|list_of("figure"|"table")`` (5.9).

    Attributes:
        kind: ``toc``, ``figure`` or ``table``.
        title: index title.
        max_level: deepest outline level (``toc``).
        page_break: start the index on a new page.
        entries: visible entries (filled after the whole document is seen).
        name: unique index name in the document.
        track: ``track=`` — the entries of this non-primary track of ``|parallel``
            instead of the primary one (7.7); written as a user index.
    """

    kind: str
    title: str
    max_level: int
    page_break: bool
    entries: list[IndexEntry]
    name: str
    track: str | None = None


@dataclass
class Target:
    """A reference target registered by its ID (5.6).

    Attributes:
        id: full ID (with the ``ns.`` prefix of the inclusion).
        kind: ``heading``, ``clause``, ``appendix``, ``figure``, ``table``,
            ``footnote``, ``endnote``, ``admonition``, ``section``.
        span: position of the ``id=`` argument.
        number: composite number or ``None`` (unnumbered target).
        label_key: key of the label dictionary (decision 72) or ``None``.
        title: function returning the title text, or ``None``.
        bookmark: bookmark name.
        note: :class:`NoteInfo` of a note target.
        condition: condition text when kept by ``--review`` although excluded.
        scopes: inclusion scopes of the definition (decision 74).
    """

    id: str
    kind: str
    span: Span | None
    number: str | None = None
    label_key: str | None = None
    title: Any = None
    bookmark: str | None = None
    note: NoteInfo | None = None
    condition: str | None = None
    scopes: list[Any] = field(default_factory=list)
