"""The structure phase: numbering, IDs, annexes, captions, notes, indexes.

Specification 5.2-5.10, 15; decisions 68-76.  :class:`StructureBuilder`
walks the evaluated and styled tree once, in document order, and

* numbers headings, clauses, annexes, scopes, tables and figures with
  captions, footnotes and endnotes (counters of nested scopes, 5.5);
* registers reference targets by ID (5.6, decision 74 for ``ns=``);
* links named numbered lists (``id``/``start``/``continues``, 5.4);
* collects the entries of the table of contents and of the lists of
  figures and tables (5.9);

then resolves the cross-references ``|@`` (:mod:`primula.structure.refs`),
so a reference may precede its target.  Results are attributes on the
nodes (:mod:`primula.structure.model`).

Numbering rules (implementation notes):

* a heading number is the composite number with the scope prefix
  («2.1», «А.1»); an unnumbered heading (``number=False`` or
  ``numbering(headings=False)``) does not move the counters;
* a clause is numbered from the nearest numbered heading of any level
  (decision 68), from the scope prefix or from the root;
* ``continues=`` continues a clause after intermediate text: the
  continuation has no number of its own, and its subclauses continue the
  counter of the target;
* tables are numbered when they have a caption; figures always (the
  caption is the body of ``|figure:``); in a scope with a prefix (an
  annex) the number is ``prefix.k``, otherwise ``chapter.k``
  (``by_chapter``) or ``k`` (``document``).

Parallel tracks (7.7, decision 134): every track of a ``|parallel`` has its
own counters — a copy of the counters of the document when the environment
starts; a full-width segment is numbered by the primary track and brings
the other tracks to its counters; after the environment the document goes
on from the primary track.  Blocks of a track are numbered in the language
of the track (captions, labels of references).  Headings of non-primary
tracks are not outline headings, their table of contents entries and
list entries belong to the track (``|toc(track=…)``); footnotes of
numbered non-primary tracks get the number of the track as an explicit
label (P5316 when the notes restart by page or chapter); a track
``numbered=False`` numbers nothing and has no footnotes (P5304).
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any, Callable

from primula.diagnostics import DiagnosticSink, error, warning
from primula.i18n import Key
from primula.source import Span
from primula.structure.args import check_args
from primula.structure.model import (
    AppendixInfo, BlockInfo, CaptionInfo, IndexEntry, IndexInfo, IndexMark, ListInfo, NoteInfo, Target,
)
from primula.structure.settings import StructureSettings, format_for_level, number_text
from primula.structure.tree import plain_text
from primula.syntax import nodes as N

_ROMAN = ((1000, "m"), (900, "cm"), (500, "d"), (400, "cd"), (100, "c"), (90, "xc"), (50, "l"),
          (40, "xl"), (10, "x"), (9, "ix"), (5, "v"), (4, "iv"), (1, "i"))


def format_number(value: int, fmt: str) -> str:
    """A counter value in an ODF number format (``1``, ``i``, ``I``, ``a``, ``A``)."""
    if fmt in ("i", "I"):
        text, rest = "", value
        for amount, letters in _ROMAN:
            while rest >= amount:
                text, rest = text + letters, rest - amount
        return text.upper() if fmt == "I" else text
    if fmt in ("a", "A"):
        text, rest = "", value
        while rest > 0:
            rest, digit = divmod(rest - 1, 26)
            text = chr(ord("a") + digit) + text
        return text.upper() if fmt == "A" else text
    return str(value)


@dataclass
class _Clause:
    """A numbered clause: its position for ``continues=`` (5.3)."""

    path: list[int]
    level: int
    section: str
    scope: str
    children: list[int] = field(default_factory=list)


@dataclass
class _Scope:
    """Counters of a numbering scope (5.5)."""

    name: str
    prefix: str = ""
    headings: list[int] = field(default_factory=lambda: [0] * 10)
    section: str = ""
    section_level: int = 0
    section_has_clauses: bool = False
    clauses: list[int] = field(default_factory=list)
    active: list[_Clause] = field(default_factory=list)
    chapter: str = ""
    tables: int = 0
    figures: int = 0
    toc_shift: int = 0


@dataclass
class Structure:
    """Result of the structure phase.

    Attributes:
        settings: effective structure settings.
        targets: reference targets by full ID.
        indexes: tables of contents and lists in document order.
        notes: number of footnotes and endnotes.
    """

    settings: StructureSettings
    targets: dict[str, Target]
    indexes: list[IndexInfo]
    notes: dict[str, int]


class StructureBuilder:
    """Numbers and links an evaluated document (see the module description).

    Args:
        settings: effective structure settings.
        sink: diagnostics receiver.
        excluded_ids: literal IDs of excluded blocks (decision 75).
        review: ``--review``: excluded blocks are kept (decision 75).
        quotes: quote pairs of the document language (plain titles).
    """

    def __init__(self, settings: StructureSettings, sink: DiagnosticSink,
                 excluded_ids: dict[str, tuple[str, Span]], *, review: bool = False,
                 quotes: tuple[tuple[str, str], tuple[str, str]] | None = None, external: Any = None,
                 language_settings: Callable[[str], tuple[StructureSettings, Any]] | None = None) -> None:
        self.settings = settings
        #: Settings and quotes of another language (track blocks of |parallel, 7.7).
        self.language_settings = language_settings
        self.sink = sink
        #: Targets of other documents of the project (``references:``, decision 121).
        self.external = external
        self.excluded_ids = excluded_ids
        self.review = review
        self.quotes = quotes
        self.targets: dict[str, Target] = {}
        self.clauses: dict[str, tuple[_Clause, Span]] = {}
        self.lists: dict[str, str] = {}
        self.scope_names: set[str] = {"document"}
        self.scopes: list[_Scope] = [_Scope("document")]
        self.appendices = 0
        self.notes = {"footnote": 0, "endnote": 0}
        self.note_seq = {"footnote": 0, "endnote": 0}
        self.toc_entries: list[IndexEntry] = []
        self.figure_entries: list[IndexEntry] = []
        self.table_entries: list[IndexEntry] = []
        self.indexes: list[IndexInfo] = []
        self.references: list[Any] = []
        self.auto_bookmarks = 0
        # Holders of index marks and automatic bookmarks by index kind;
        # without a |toc / |list_of of that kind they are removed.
        self.index_holders: list[tuple[str, Any, bool]] = []
        # Marks of the alphabetical index (9.5): (term, subterm or None).
        self.alpha_marks: list[tuple[str, str | None]] = []
        #: Scope of the current part of a compound document (10.7): IDs get "scope:".
        self.part: str | None = None
        #: The track of |parallel whose block is being numbered (7.7), or ``None``.
        self.track: Any = None
        #: Counters of the tracks of every |parallel (by ``id`` of its spec): track id -> (scopes, notes).
        self.parallel_states: dict[int, dict[str, tuple[list[_Scope], dict[str, int]]]] = {}
        #: Ids and languages of the tracks of the document; ids of the primary tracks.
        self.track_languages: dict[str, str | None] = {}
        self.primary_tracks: list[str] = []
        #: (entry, holder, kind) of table of contents and list entries outside tracks:
        #: an index of a track (``|toc(track=…)``) gets marks at them too.
        self.entry_holders: list[tuple[IndexEntry, Any, str]] = []
        self._restart_warned: set[int] = set()

    @property
    def scope(self) -> _Scope:
        return self.scopes[-1]

    # ------------------------------------------------------------------
    # Entry
    # ------------------------------------------------------------------

    def build(self, document: N.Document) -> Structure:
        """Annotate the document in place and resolve references."""
        from primula.structure.refs import resolve_references

        self._blocks(document.children)
        self._track_indexes()
        for index in self.indexes:
            source = {"toc": self.toc_entries, "figure": self.figure_entries, "table": self.table_entries,
                      "index": self._alphabetical_entries()}
            index.entries = [e for e in source[index.kind]
                             if (index.kind != "toc" or e.level <= index.max_level or e.forced)
                             and (e.track is None or (e.track == index.track if index.track else e.primary))]
        # Marks of the kinds no index uses are removed; an automatic bookmark stays
        # while an index of any track shows the entry (7.7).
        used = {index.kind if index.track is None else f"{index.kind}:{index.track}" for index in self.indexes}
        shown = {index.kind for index in self.indexes}
        for kind, holder, auto in self.index_holders:
            holder.marks = [mark for mark in holder.marks
                            if not isinstance(mark, IndexMark) or mark.index in used]
            if auto and kind.split(":")[0] not in shown and kind not in used:
                holder.bookmark = None
        resolve_references(self.references, self.targets, self.settings, self.sink, self.excluded_ids,
                           self.external, primaries=self.primary_tracks)
        return Structure(self.settings, self.targets, self.indexes, dict(self.notes))

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _full_id(self, node: Any, raw: str) -> str:
        """The ID with the ``ns.`` prefixes of its inclusions (decision 74)."""
        prefixes = [ns for ns, _span, _path in getattr(node, "id_scopes", []) if ns]
        full = ".".join([*prefixes, raw])
        return f"{self.part}:{full}" if self.part else full

    def _register(self, node: Any, raw: str | None, kind: str, span: Span | None, **values: Any) -> Target | None:
        """Register a reference target; P4102/P4103 for duplicates."""
        if raw is None:
            return None
        full = self._full_id(node, raw)
        scopes = list(getattr(node, "id_scopes", []))
        existing = self.targets.get(full)
        if existing is not None:
            first, second = existing.scopes, scopes
            if first and second and first[-1][2] == second[-1][2] and first[-1][1] is not second[-1][1]:
                diagnostic = error("P4103", span, id=full)
                diagnostic.note("note.first_inclusion", first[-1][1]).note("note.second_inclusion", second[-1][1])
                diagnostic.hint("help.include_ns")
            else:
                diagnostic = error("P4102", span, id=full).note("note.first_definition", existing.span)
            self.sink.emit(diagnostic)
            return None
        target = Target(full, kind, span, bookmark=full, scopes=scopes,
                        condition=getattr(node, "condition", None), **values)
        self.targets[full] = target
        return target

    def _id_span(self, node: Any) -> Span:
        args = getattr(node, "args", None)
        source = getattr(args, "source", None)
        if source is not None and source.keyword("id") is not None:
            return source.fragment.span_of(source.keyword("id"))
        return node.span

    def _auto_bookmark(self) -> str:
        self.auto_bookmarks += 1
        return f"__toc_{self.auto_bookmarks}"

    def _own_track(self) -> str | None:
        """The id of the current track when it is not the primary one (its own index entries)."""
        track = self.track
        return track.fields["id"] if track is not None and not track.fields["primary"] else None

    def _entry_track(self) -> dict[str, Any]:
        """``track``/``primary`` of an index entry made now (7.7)."""
        if self.track is None:
            return {}
        return {"track": self.track.fields["id"], "primary": bool(self.track.fields["primary"])}

    def _index_kind(self, kind: str) -> str:
        """``toc``/``figure``/``table``, or ``toc:en`` for an entry of a non-primary track (7.7)."""
        own = self._own_track()
        return f"{kind}:{own}" if own else kind

    def _prefixed(self, local: str) -> str:
        return f"{self.scope.prefix}.{local}" if self.scope.prefix and local else (self.scope.prefix or local)

    # ------------------------------------------------------------------
    # Blocks
    # ------------------------------------------------------------------

    def _blocks(self, blocks: list[Any]) -> None:
        for block in blocks:
            self._block(block)

    def _block(self, block: Any) -> None:
        if isinstance(block, N.Heading):
            self._heading(block)
        elif isinstance(block, N.Clause):
            self._clause(block)
        elif isinstance(block, N.Admonition):
            self._target_only(block, "admonition", "|!")
            self._inlines(block.body)
            self._blocks(block.children)
        elif isinstance(block, N.ListBlock):
            self._list(block)
        elif isinstance(block, N.Command):
            self._command(block)
        elif isinstance(block, N.TableRow):
            for cell in block.cells:
                self._inlines(cell.body)
        else:
            self._inlines(getattr(block, "body", None) or [])
            self._blocks(getattr(block, "children", None) or [])

    def _target_only(self, block: Any, kind: str, command: str) -> None:
        """A page-only target (admonition, section): a bookmark at its first paragraph."""
        values = check_args(block.args, kind, command, self.sink, types_only=("id",))
        if "id" in values:
            target = self._register(block, values["id"], kind, self._id_span(block))
            if target is not None:
                block.struct = BlockInfo(bookmark=target.bookmark)

    # --- headings and clauses -----------------------------------------------------

    def _heading(self, block: N.Heading) -> None:
        values = check_args(block.args, "heading", "|<", self.sink)
        scope = self.scope
        level = block.level
        numbered = bool(self.settings.numbering.get("headings", True)) and values.get("number", True)
        if self.track is not None:
            numbered = numbered and self.track.fields["numbered"]
            if not self.track.fields["primary"]:
                block.outline = False  # not in the navigator and PDF bookmarks (7.7, decision 134)
        info = BlockInfo()
        title = plain_text(block.body, self.quotes)
        if numbered:
            if level > 1 and scope.headings[level - 2] == 0:
                previous = max((i + 1 for i in range(level - 1) if scope.headings[i]), default=0)
                self.sink.emit(error("P4201", block.span, level=level, previous=previous))
            if scope.section_has_clauses and scope.section_level == level - 1:
                self.sink.emit(warning("P4203", block.span, number=scope.section))
            scope.headings[level - 1] += 1
            for i in range(level, len(scope.headings)):
                scope.headings[i] = 0
            number = self._prefixed(".".join(str(c) for c in scope.headings[:level]))
            info.number = number
            info.prefix = number_text(format_for_level(self.settings.numbering.get("heading_format"), level), number)
            info.prefix_style = getattr(block, "number_style", None)
            scope.section, scope.section_level = number, level
            scope.section_has_clauses = False
            scope.clauses, scope.active = [], []
            if level == 1:
                scope.chapter = number
                if not scope.prefix:
                    # Chapter numbering restarts the counters (5.8).
                    if self.settings.numbering.get("tables") == "by_chapter":
                        scope.tables = 0
                    if self.settings.numbering.get("figures") == "by_chapter":
                        scope.figures = 0
                if self.settings.footnotes.get("restart") == "chapter":
                    self.notes = {"footnote": 0, "endnote": 0}
            if _starts_with_number(title):
                self.sink.emit(warning("P4202", block.span))
        target = self._register(block, values.get("id"), "heading", self._id_span(block),
                                number=info.number, label_key="section" if level == 1 else "subsection",
                                title=lambda: plain_text(block.body, self.quotes))
        if target is not None:
            info.bookmark = target.bookmark
        if values.get("toc", True):
            text = values.get("toc_title") or title
            if info.prefix:
                text = info.prefix.rstrip() + " " + text
            self._toc_mark(info, text, values.get("toc_level") or level + scope.toc_shift,
                           forced=values.get("toc") is True, span=block.span)
        block.struct = info
        self._inlines(block.body)

    def _toc_mark(self, info: Any, text: str, level: int, *, forced: bool = False, span: Any = None) -> None:
        """A table of contents entry of a heading, clause, appendix or ``|toc_entry`` (5.9, decision 122).

        ``forced`` (``toc=True``) includes the entry although it is deeper
        than ``max_level`` of the ``|toc``; the level is 1–10.
        """
        if not 1 <= int(level) <= 10:
            self.sink.emit(error("P4402", span, setting="toc_level", value=str(level), expected="1–10"))
            level = max(1, min(int(level), 10))
        auto = info.bookmark is None
        if auto:
            info.bookmark = self._auto_bookmark()
        kind = self._index_kind("toc")
        info.marks.append(IndexMark(kind, text, int(level)))
        entry = IndexEntry(int(level), text, info.bookmark, forced, **self._entry_track())
        self.toc_entries.append(entry)
        self.index_holders.append((kind, info, auto))
        if entry.track is None:
            self.entry_holders.append((entry, info, "toc"))

    def _clause(self, block: N.Clause) -> None:
        values = check_args(block.args, "clause", "|>", self.sink)
        scope = self.scope
        level = block.level
        info = BlockInfo()
        continues = values.get("continues")
        record: _Clause | None = None
        if self.track is not None and not self.track.fields["numbered"]:
            pass  # a track numbered=False: clauses without numbers (7.7)
        elif continues is not None:
            record = self._continue_clause(block, continues, level)
        else:
            if level > 1 and (len(scope.clauses) < level - 1 or scope.clauses[level - 2] == 0):
                self.sink.emit(error("P4204", block.span, level=level))
            while len(scope.clauses) < level:
                scope.clauses.append(0)
            scope.clauses = scope.clauses[:level]
            scope.clauses[level - 1] += 1
            base = scope.section or scope.prefix
            local = ".".join(str(c) for c in scope.clauses)
            number = f"{base}.{local}" if base else local
            info.number = number
            info.prefix = number_text(format_for_level(self.settings.numbering.get("clause_format"), level), number)
            info.prefix_style = getattr(block, "number_style", None)
            record = _Clause(list(scope.clauses), level, scope.section, scope.name)
            scope.active = scope.active[:level - 1] + [record]
            for ancestor in scope.active[:-1]:
                ancestor.children = scope.clauses[ancestor.level:]
            scope.section_has_clauses = True
        target = self._register(block, values.get("id"), "clause", self._id_span(block),
                                number=info.number, label_key="clause" if level == 1 else "subclause",
                                title=lambda: plain_text(_clause_text(block), self.quotes))
        if target is not None:
            info.bookmark = target.bookmark
            if record is not None and continues is None:
                self.clauses[target.id] = (record, target.span or block.span)
        if values.get("toc") is True or values.get("toc_title") or values.get("toc_level"):
            # A clause in the table of contents on request (decision 122); by default clauses are not.
            text = values.get("toc_title") or plain_text(_clause_text(block), self.quotes)
            if info.prefix:
                text = info.prefix.rstrip() + " " + text
            self._toc_mark(info, text, values.get("toc_level") or (scope.section_level or 0) + level,
                           forced=True, span=block.span)
        block.struct = info
        self._inlines(block.body)
        self._blocks(block.children)

    def _continue_clause(self, block: N.Clause, name: str, level: int) -> _Clause | None:
        """``|>(continues="id")`` (5.3): restore the counters of the target clause."""
        scope = self.scope
        found = self.clauses.get(self._full_id(block, name)) or self.clauses.get(name)
        if found is None:
            self.sink.emit(error("P4205", block.span, id=name))
            return None
        record, span = found
        if record.scope != scope.name or record.section != scope.section or record.level != level:
            self.sink.emit(error("P4206", block.span, id=name).note("note.target_here", span))
            return None
        scope.clauses = list(record.path) + list(record.children)
        scope.active = scope.active[:level - 1] + [record]
        return record

    # --- lists ---------------------------------------------------------------------

    def _list(self, block: N.ListBlock) -> None:
        if block.items and block.items[0].kind == "number":
            first = block.items[0]
            values = check_args(first.args, "list_item", "|#", self.sink)
            info = ListInfo()
            if "start" in values and "continues" in values:
                self.sink.emit(error("P4207", first.span))
            elif "start" in values:
                info.start = values["start"]
            if "continues" in values:
                xml_id = self.lists.get(values["continues"])
                if xml_id is None:
                    self.sink.emit(error("P4208", first.span, name=values["continues"]))
                info.continue_list = xml_id
            if "id" in values:
                if values["id"] in self.lists:
                    self.sink.emit(error("P4209", first.span, name=values["id"]))
                else:
                    info.xml_id = f"list-{len(self.lists) + 1}"
                    self.lists[values["id"]] = info.xml_id
            if info.xml_id or info.continue_list or info.start is not None:
                block.list_info = info
        for item in block.items:
            note = getattr(item, "admonition", None)
            if note is not None:
                # A note of a group «Примітки: 1. … 2. …» keeps its id= (decision 116).
                self._target_only(note, "admonition", "|!")
                item.struct = getattr(note, "struct", None)
            self._inlines(item.body)
            self._blocks(item.children)

    # --- commands ------------------------------------------------------------------

    def _command(self, block: N.Command) -> None:
        name = block.name
        if name == "appendix":
            self._appendix(block)
        elif name == "scope":
            self._scope(block)
        elif name == "document":
            self._part(block)
        elif name == "table":
            self._table(block)
        elif name == "figure":
            self._figure(block)
        elif name in ("toc", "list_of"):
            self._index(block)
        elif name == "section":
            self._target_only(block, "section", "|section")
            self._inlines(block.body)
            self._blocks(block.children)
        elif name == "index":
            self._index_mark(block)  # |index("…") on its own line: a mark at the next paragraph
        elif name == "toc_entry":
            self._toc_entry(block)
        else:
            self._inlines(block.body)
            self._blocks(block.children)

    def _appendix(self, block: N.Command) -> None:
        """``|appendix(…):`` (5.5, decision 71): designation, scope with a prefix."""
        values = check_args(block.args, "appendix", "|appendix", self.sink)
        settings = self.settings.appendices
        letters = str(settings.get("letters") or "")
        if "letter" in values:
            if values["letter"] in letters:
                self.appendices = letters.index(values["letter"]) + 1
            else:
                self.sink.emit(error("P4211", block.span, letter=values["letter"], letters=letters))
                self.appendices += 1
        elif "number" in values:
            self.appendices = values["number"]
        else:
            self.appendices += 1
        count = self.appendices
        if settings.get("numbering") == "letters" and 0 < count <= len(letters):
            value = letters[count - 1]
        else:
            value = str(count)
        designation = str(settings.get("designation", "{n}")).replace("{n}", value)
        title = values.get("title")
        target = self._register(block, values.get("id"), "appendix", self._id_span(block), number=value,
                                label_key="appendix", title=(lambda: title or designation))
        # Without id= the bookmark is made only for the table of contents (_toc_mark).
        bookmark = target.bookmark if target is not None else None
        toc_text = str(settings.get("toc", "{designation} {title}")).replace("{designation}", designation)
        toc_text = values.get("toc_title") or " ".join(toc_text.replace("{title}", title or "").split())
        title_format = settings.get("title_format")
        combined = None
        if isinstance(title_format, str) and title_format:
            # One paragraph «ДОДАТОК 1. Назва» where space matters (decision 120).
            combined = " ".join(title_format.replace("{designation}", designation)
                                .replace("{title}", title or "").split())
        block.appendix_info = AppendixInfo(designation, values.get("subtitle"), title, bookmark,
                                           bool(settings.get("page_break", True)), [], combined,
                                           outline=int(values.get("toc_level") or 1))
        if values.get("toc", True):
            # toc=False, toc_title=, toc_level= of |appendix (decision 122).
            self._toc_mark(block.appendix_info, toc_text, values.get("toc_level") or 1,
                           forced=values.get("toc") is True, span=block.span)
        scope_name = values.get("id") or f"appendix-{count}"
        self.scopes.append(_Scope(scope_name, prefix=value, toc_shift=1))
        try:
            self._blocks(block.children)
        finally:
            self.scopes.pop()

    def _part(self, block: N.Command) -> None:
        """A part of a compound document (10.7): own numbering scope, IDs ``scope:id``.

        Headings, clauses, tables, figures and annexes are numbered anew;
        ``|scope`` names are checked within the part.  Footnotes, the table
        of contents and the lists are common to the whole document.
        """
        args = block.args
        scope = str(args.keywords.get("scope")) if args is not None else "?"
        saved = self.part, self.appendices, self.scope_names
        self.part, self.appendices, self.scope_names = scope, 0, {"document"}
        new = _Scope(scope)
        # level_shift=n (П3): the part's headings start at level n + 1 under the
        # current heading numbers of the enclosing document («1.2» → «1.2.1»).
        shift = args.keywords.get("level_shift", 0) if args is not None else 0
        for index in range(int(shift) if isinstance(shift, int) else 0):
            new.headings[index] = self.scope.headings[index]
        self.scopes.append(new)
        try:
            self._blocks(block.children)
        finally:
            self.scopes.pop()
            self.part, self.appendices, self.scope_names = saved

    def _scope(self, block: N.Command) -> None:
        """``|scope("name", prefix=…):`` — independent counters (5.5)."""
        values = check_args(block.args, "scope", "|scope", self.sink)
        positional = block.args.positional if block.args is not None else []
        name = positional[0] if positional and isinstance(positional[0], str) else None
        if name is None:
            self.sink.emit(error("P4105", block.span, name="name", command="|scope", expected=Key("type.string")))
        elif name in self.scope_names:
            self.sink.emit(error("P4210", block.span, name=name))
        else:
            self.scope_names.add(name)
        self.scopes.append(_Scope(name or "?", prefix=values.get("prefix", ""), toc_shift=self.scope.toc_shift))
        try:
            self._blocks(block.children)
        finally:
            self.scopes.pop()

    def _next_number(self, kind: str) -> str:
        """Number of the next table or figure (5.8, decision 73)."""
        scope = self.scope
        count = (scope.tables if kind == "table" else scope.figures) + 1
        if kind == "table":
            scope.tables = count
        else:
            scope.figures = count
        if scope.prefix:
            return f"{scope.prefix}.{count}"
        mode = self.settings.numbering.get("tables" if kind == "table" else "figures")
        if mode == "by_chapter" and scope.chapter:
            return f"{scope.chapter}.{count}"
        return str(count)

    def _caption(self, block: N.Command, kind: str, title: list[Any], target_id: str | None) -> None:
        number = self._next_number(kind)
        settings = self.settings.captions.get(kind) or {}
        fmt = str(settings.get("format", "{n} {title}")).replace("{n}", number)
        before, _, after = fmt.partition("{title}")
        if "{title}" not in fmt:
            before, after, title = fmt, "", []
        target = self._register(block, target_id, kind, self._id_span(block), number=number, label_key=kind,
                                title=lambda: plain_text(title, self.quotes))
        entry = " ".join((before + plain_text(title, self.quotes) + after).split())
        bookmark = target.bookmark if target is not None else self._auto_bookmark()
        position = settings.get("position", "above" if kind == "table" else "below")
        index_kind = self._index_kind(kind)
        block.caption_info = CaptionInfo(kind, number, before, title, after, position, bookmark,
                                         [IndexMark(index_kind, entry, 1)])
        index_entry = IndexEntry(1, entry, bookmark, **self._entry_track())
        (self.table_entries if kind == "table" else self.figure_entries).append(index_entry)
        self.index_holders.append((index_kind, block.caption_info, target is None))
        if index_entry.track is None:
            self.entry_holders.append((index_entry, block.caption_info, kind))
        self._inlines(title)

    def _table(self, block: N.Command) -> None:
        if getattr(block, "parallel", None) is not None:
            self._parallel(block)
            return
        values = check_args(block.args, "table", "|table", self.sink, types_only=("id", "caption"))
        caption_env = next((c for c in block.children if isinstance(c, N.Command) and c.name == "caption"), None)
        title: list[Any] | None = None
        if caption_env is not None:
            title = _caption_inlines(caption_env)
        elif values.get("caption"):
            title = [N.Text(block.span, values["caption"])]
        if title is not None:
            self._caption(block, "table", title, values.get("id"))
        elif "id" in values:
            target = self._register(block, values["id"], "table", self._id_span(block))
            if target is not None:
                block.struct = BlockInfo(bookmark=target.bookmark)
        for child in block.children:
            if child is not caption_env:
                self._block(child)

    def _figure(self, block: N.Command) -> None:
        values = check_args(block.args, "figure", "|figure", self.sink, types_only=("id",))
        self._caption(block, "figure", _caption_inlines(block), values.get("id"))

    def _index(self, block: N.Command) -> None:
        """``|toc(…)``, ``|list_of("figure"|"table", …)`` (5.9)."""
        construct = block.name
        values = check_args(block.args, construct, "|" + construct, self.sink)
        kind = "toc"
        if construct == "list_of":
            positional = block.args.positional if block.args is not None else []
            kind = positional[0] if positional else None
            if kind not in ("figure", "table", "index"):
                self.sink.emit(error("P4401", block.span, kind=str(kind)))
                return
        titles = self.settings.titles
        if kind == "index":
            from primula.techdoc.texts import TITLES, language

            default = TITLES[language(self.settings.language)]["index"]
        else:
            default = titles["toc"] if kind == "toc" else titles["figures" if kind == "figure" else "tables"]
        title = values.get("title", default)
        info = IndexInfo(kind, title or "", int(values.get("max_level", 3)), bool(values.get("page_break", False)),
                         [], f"{kind}{len(self.indexes) + 1}", track=values.get("track"))
        if info.track is not None:
            # The default title in the language of the track is known after the document (_track_indexes).
            info.default_title = "title" not in values  # type: ignore[attr-defined]
            info.span = block.span  # type: ignore[attr-defined]
        block.index_info = info
        self.indexes.append(info)

    # --- parallel tracks (7.7, decision 134) ---------------------------------------

    def _parallel(self, block: N.Command) -> None:
        """A table made of ``|parallel``: number every track block with the counters of its track."""
        spec = block.parallel
        primary = spec.primary
        if primary not in self.primary_tracks:
            self.primary_tracks.append(primary)
        for track in spec.tracks:
            self.track_languages.setdefault(track.fields["id"], track.fields["lang"])
        states = self.parallel_states.get(id(spec))
        if states is None:
            # The tracks start from the counters of the document (a page break splits a
            # |parallel into several tables: the states go on in the next one).
            states = {t.fields["id"]: (self.scopes, self.notes) if t.fields["id"] == primary
                      else (copy.deepcopy(self.scopes), dict(self.notes)) for t in spec.tracks}
            self.parallel_states[id(spec)] = states
        tracks = {t.fields["id"]: t for t in spec.tracks}
        saved = self.track, self.settings, self.quotes
        try:
            for row in block.children:
                segment = getattr(row, "segment", None)
                if segment is None:
                    continue  # the row of track titles
                for cell in row.children:
                    track = getattr(cell, "track", None)
                    track_id = track.fields["id"] if track is not None else primary
                    self.scopes, self.notes = states[track_id]
                    self.track = tracks[track_id] if track is not None else None
                    self._language_of(track)
                    self._blocks(cell.children)
                    states[track_id] = (self.scopes, self.notes)
                    self.track, self.settings, self.quotes = saved
                if not segment.full:
                    self._parity(spec, segment, row)
                if segment.full:
                    # A full-width segment moves the counters of all tracks alike: the
                    # numbered tracks continue from the primary one.
                    for track_id, track in tracks.items():
                        if track_id != primary and track.fields["numbered"]:
                            scopes, notes = states[primary]
                            states[track_id] = (copy.deepcopy(scopes), dict(notes))
        finally:
            self.track, self.settings, self.quotes = saved
            self.scopes, self.notes = states[primary]
        if getattr(block, "parallel_last", False) and spec.parity == "translation":
            from primula.parallel.parity import check_counters, counters

            main = counters(*states[primary])
            for track_id, track in tracks.items():
                # An optional track (an old wording, a comment) may lack blocks: its counters may differ.
                if track_id != primary and track.fields["numbered"] and not track.fields["optional"]:
                    check_counters(track_id, main, counters(*states[track_id]), block.span, self.sink)

    def _parity(self, spec: Any, segment: Any, row: N.Command) -> None:
        """The correspondence of the track blocks of a segment to the primary one (7.7, P5310-P5314)."""
        from primula.parallel.parity import check_structure, check_translation

        profile = segment.parity or spec.parity
        primary = spec.primary
        if profile == "none" or primary not in segment.tracks:
            return
        cells = {cell.track.fields["id"]: cell for cell in row.children if getattr(cell, "track", None)}
        name = segment.id or "—"
        for track in spec.tracks:
            track_id = track.fields["id"]
            if track_id == primary or not track.fields["numbered"] or track_id not in segment.tracks:
                continue
            if track.fields["optional"] and not segment.tracks[track_id]:
                continue
            where = segment.track_spans.get(track_id, segment.span)
            check_structure(name, track_id, cells[primary].children, cells[track_id].children, where, self.sink)
            if profile == "translation" and primary in segment.facts and track_id in segment.facts:
                check_translation(name, track_id, segment.facts[primary], segment.facts[track_id], where,
                                  segment.track_spans.get(primary, segment.span), self.sink)

    def _language_of(self, track: Any) -> None:
        """Settings and quotes of the language of a track (captions, labels, titles)."""
        language = track.fields["lang"] if track is not None else None
        if language is not None and self.language_settings is not None:
            self.settings, self.quotes = self.language_settings(language)

    def _track_note_label(self, node: Any, citation: str, label: str | None) -> str | None:
        """The citation of a note in a non-primary track (7.7, decision 134).

        A numbered track writes the number of its own counter as an explicit
        label: Writer leaves labelled notes out of its numbering, so the
        primary track and the rest of the document keep their numbers.  With
        notes restarting by page or chapter the number is unknown at build
        time: Writer numbers the notes, P5316 once per document.  A track
        ``numbered=False`` has no notes (P5304).
        """
        if not self.track.fields["numbered"]:
            self.sink.emit(error("P5304", node.name_span, command=node.name))
            return label
        if self.settings.footnotes.get("restart", "none") != "none":
            if not self._restart_warned:
                self._restart_warned.add(1)
                self.sink.emit(warning("P5316", node.name_span,
                                       restart=str(self.settings.footnotes.get("restart"))))
            return label
        return label or citation

    def _track_indexes(self) -> None:
        """Indexes of a track (``|toc(track="en")``, 7.7): marks outside the tracks, titles, unknown tracks.

        Writer builds the table of contents of the document from
        ``text:toc-mark`` and cannot select marks by track, so the index of
        a non-primary track is a user index with its own name: the entries of
        the track have its marks already, the entries outside the tracks get
        one more mark here.  The index of a primary track is the ordinary one.
        """
        for index in self.indexes:
            track = index.track
            if track is None:
                continue
            if track in self.primary_tracks:
                index.track = None
                continue
            if track not in self.track_languages:
                self.sink.emit(error("P5302", getattr(index, "span", None),
                                     command=f'{"toc" if index.kind == "toc" else "list_of"}(track="{track}")',
                                     where=Key("parallel.unknown_track")).hint("help.parallel"))
                index.track = None
                continue
            kind = f"{index.kind}:{track}"
            if not any(isinstance(m, IndexMark) and m.index == kind
                       for entry, holder, base in self.entry_holders for m in holder.marks):
                for entry, holder, base in self.entry_holders:
                    if base == index.kind:
                        holder.marks.append(IndexMark(kind, entry.text, entry.level))
                        self.index_holders.append((kind, holder, False))
            if getattr(index, "default_title", False):
                language = self.track_languages.get(track)
                settings = self.language_settings(language)[0] if language and self.language_settings else self.settings
                key = "toc" if index.kind == "toc" else ("figures" if index.kind == "figure" else "tables")
                index.title = settings.titles.get(key, index.title)

    # --- inline --------------------------------------------------------------------

    def _alphabetical_entries(self) -> list[IndexEntry]:
        """Visible entries of the alphabetical index (9.5): terms and subterms, sorted by the language."""
        from primula.library.text import sort_key_of
        from primula.techdoc.texts import language

        lang = language(self.settings.language)
        tree: dict[str, set[str]] = {}
        for term, subterm in self.alpha_marks:
            tree.setdefault(term, set())
            if subterm:
                tree[term].add(subterm)
        entries: list[IndexEntry] = []
        for term in sorted(tree, key=lambda t: sort_key_of(t, lang)):
            entries.append(IndexEntry(1, term, None))
            entries += [IndexEntry(2, s, None) for s in sorted(tree[term], key=lambda t: sort_key_of(t, lang))]
        return entries

    def _toc_entry(self, node: Any) -> None:
        """``|toc_entry("Текст", level=1)``: a table of contents entry at the next paragraph (decision 122)."""
        values = check_args(node.args, "toc_entry", "|toc_entry", self.sink)
        args = node.args
        text = args.positional[0] if args is not None and args.positional else None
        if not isinstance(text, str) or not text.strip():
            self.sink.emit(error("P4105", node.span, name="text", command="|toc_entry", expected=Key("type.string")))
            return
        info = BlockInfo()
        self._toc_mark(info, " ".join(text.split()), values.get("level", 1), forced=True, span=node.span)
        node.struct = info

    def _index_mark(self, node: Any) -> None:
        """``|index("term", sub="…")``: a mark of the alphabetical index (9.5)."""
        args = node.args
        term = args.positional[0] if args is not None and args.positional else None
        subterm = args.get("sub") if args is not None else None
        if not isinstance(term, str) or not term.strip() or (subterm is not None and not isinstance(subterm, str)):
            self.sink.emit(error("P9301", node.span))
            return
        node.alpha_mark = (term.strip(), subterm.strip() if subterm else None)
        self.alpha_marks.append(node.alpha_mark)

    def _inlines(self, nodes: list[Any]) -> None:
        for node in nodes:
            if isinstance(node, N.InlineCommand) and node.name == "index":
                self._index_mark(node)
                continue
            if isinstance(node, N.Reference):
                node.part_scope = self.part  # IDs of the part first (10.7)
                node.ref_settings = self.settings  # labels in the language of a track block (7.7)
                self.references.append(node)
            elif isinstance(node, N.InlineCommand) and node.name in ("footnote", "endnote"):
                self._note(node)
            body = getattr(node, "body", None)
            if isinstance(body, list):
                self._inlines(body)

    def _note(self, node: N.InlineCommand) -> None:
        """A footnote or endnote (5.10, decision 76)."""
        kind = node.name
        values = check_args(node.args, kind, "|" + kind, self.sink)
        self.notes[kind] += 1
        self.note_seq[kind] += 1
        fmt = str(self.settings.footnotes.get("format", "1"))
        count = self.notes[kind]
        label = None
        if fmt == "*":
            citation = label = "*" * count
        else:
            citation = format_number(count, fmt)
        if self.track is not None and not self.track.fields["primary"]:
            label = self._track_note_label(node, citation, label)
        info = NoteInfo(kind, f"{'ftn' if kind == 'footnote' else 'edn'}{self.note_seq[kind]}", citation, label)
        node.note_info = info
        self._register(node, values.get("id"), kind, self._id_span(node), number=citation, note=info)


def _starts_with_number(text: str) -> bool:
    """A heading text that looks manually numbered: «1.», «2.3 », «1)»."""
    head = text.split(" ", 1)[0]
    return bool(head) and head[0].isdigit() and all(c.isdigit() or c in ".)" for c in head)


def _clause_text(block: N.Clause) -> list[Any]:
    """The first paragraph of a clause (title of a reference, 5.7)."""
    if block.body:
        return block.body
    for child in block.children:
        if isinstance(child, N.Paragraph):
            return child.body
    return []


def _caption_inlines(block: N.Command) -> list[Any]:
    """Caption markup: the paragraphs of ``|caption:`` / ``|figure:`` joined by spaces."""
    result: list[Any] = list(block.body or [])
    for child in block.children:
        if isinstance(child, N.Paragraph):
            if result:
                result.append(N.Text(child.span, " "))
            result.extend(child.body)
    return result
