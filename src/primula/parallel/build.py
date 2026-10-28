"""Evaluated parallel segments as tables (specification 7.7, decision 134; stage 16.2).

A ``|parallel`` becomes an ordinary ``|table`` (6.2), so the styles, table
and ODT phases need no separate code path:

* a column per track: the width of the track, half of ``gap`` as the
  inner padding of each neighbouring cell, ``rule`` as the left border of
  every track but the first (:func:`columns`);
* the row of track titles (``header``) — the header row of the table,
  repeated on every page by the table style;
* a row per segment, a cell per track in the order of the tracks; a cell
  holds the blocks of its track block (wrapped in ``|block`` when the track
  has ``block=``); a missing block of a required track is warning P5301
  and a placeholder ``|?{…}``;
* a segment ``span="all"`` — one cell spanning every column;
* ``|page``/``|newpage`` between segments close the table; the next
  segments make a new table with the same title row.

The nodes keep the parallel attributes: the table ``parallel``
(:class:`~primula.parallel.model.ParallelSpec`), a row ``segment``
(:class:`EvaluatedSegment`), a cell ``track`` (the track record) and
``track_language`` (the language tag of the track, read by the ODT writer).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from primula.diagnostics import DiagnosticSink, warning
from primula.evaluate.model import EArgs
from primula.parallel.model import ParallelSpec, Track, half
from primula.source import Span
from primula.syntax import nodes as N
from primula.tables.columns import Column


@dataclass(eq=False)
class EvaluatedSegment(N.Node):
    """A segment after evaluation, before it becomes a table row.

    Attributes:
        id: the segment id or ``None``.
        full: ``span="all"`` — one cell over every track.
        keep: do not break the row between pages.
        status: the status label (7.7).
        parity: the profile of this segment or ``None`` (the one of ``|parallel``).
        blocks: the blocks of a full-width segment.
        tracks: track id -> evaluated blocks of its track block (present blocks only).
        track_spans: track id -> span of the track block.
        track_args: track id -> checked arguments of the track block.
        facts: track id -> :class:`~primula.parallel.parity.TrackFacts` (the ``translation`` profile).
        sources: track id -> the parsed track block (``primula parallel`` rewrites its arguments).
        hashes: track id -> the hash of the normalized text of the block (:mod:`~primula.parallel.rev`).
        stale, changed: track id -> P5320 / P5321 was found (``--dump-structure``, ``--check-status``).
    """

    id: str | None = None
    full: bool = False
    keep: bool = False
    status: str | None = None
    parity: str | None = None
    blocks: list[Any] = field(default_factory=list)
    tracks: dict[str, list[Any]] = field(default_factory=dict)
    track_spans: dict[str, Span] = field(default_factory=dict)
    track_args: dict[str, Any] = field(default_factory=dict)
    facts: dict[str, Any] = field(default_factory=dict)
    sources: dict[str, Any] = field(default_factory=dict)
    hashes: dict[str, str] = field(default_factory=dict)
    stale: dict[str, bool] = field(default_factory=dict)
    changed: dict[str, bool] = field(default_factory=dict)


def _args(where: Span, *positional: Any, **keywords: Any) -> EArgs:
    return EArgs(where, list(positional), dict(keywords))


def columns(spec: ParallelSpec) -> list[Column]:
    """The ``cols`` of the table: width, gap halves as padding, the rule as the left border."""
    from primula.core.values import Length

    zero = Length(spec.gap.value * 0, spec.gap.unit)
    result = []
    last = len(spec.tracks) - 1
    for index, width in enumerate(spec.widths):
        left = half(spec.gap) if index > 0 else zero
        right = half(spec.gap) if index < last else zero
        fields: dict[str, Any] = {"width": width, "padding": (zero, right, zero, left)}
        if spec.rule is not None and index > 0:
            fields["border_left"] = spec.rule
        result.append(Column(fields))
    return result


def _placeholder(span: Span) -> N.Paragraph:
    """A paragraph with a placeholder ``|?{…}`` (a missing track block)."""
    return N.Paragraph(span, [N.Short(span, "?", None, [N.Text(span, "…")])])


def _cell(where: Span, blocks: list[Any], track: Track | None, **keywords: Any) -> N.Command:
    cell = N.Command(where, "cell", where, _args(where, **keywords), "env", [], list(blocks))
    if track is not None:
        cell.track = track
        cell.track_language = track.fields["lang"]
    return cell


def _segment_row(spec: ParallelSpec, segment: EvaluatedSegment, sink: DiagnosticSink) -> N.Command:
    span = segment.span
    row_args = {"keep": True} if segment.keep or spec.keep_rows else {}
    if segment.full:
        cells = [_cell(span, segment.blocks, None, span=len(spec.tracks))]
    else:
        cells = []
        for track in spec.tracks:
            track_id = track.fields["id"]
            if track_id in segment.tracks:
                blocks = segment.tracks[track_id]
                cell_span = segment.track_spans.get(track_id, span)
                if track.fields["block"]:
                    blocks = [N.Command(cell_span, "block", cell_span, _args(cell_span, track.fields["block"]),
                                        "env", [], blocks)]
            else:
                cell_span = span
                blocks = []
                if not track.fields["optional"] and (segment.parity or spec.parity) != "none":
                    sink.emit(warning("P5301", span, segment=segment.id or "—", track=track_id))
                    blocks = [_placeholder(span)]
            cells.append(_cell(cell_span, blocks, track))
    row = N.Command(span, "row", span, _args(span, **row_args), "env", [], cells)
    row.segment = segment
    return row


def _title_row(spec: ParallelSpec, span: Span) -> N.Command:
    cells = []
    for track in spec.tracks:
        title = track.fields["title"]
        blocks = [N.Paragraph(span, [N.Text(span, title)])] if title else []
        cell = _cell(span, blocks, track)
        cell.parallel_header = True
        cells.append(cell)
    return N.Command(span, "row", span, _args(span), "env", [], cells)


def _table(spec: ParallelSpec, rows: list[N.Command], span: Span) -> N.Command:
    keywords: dict[str, Any] = {"cols": columns(spec), "header": 1 if spec.header else 0}
    if spec.style is not None:
        keywords["style"] = spec.style
    if spec.keep_rows:
        keywords["keep_rows"] = True
    children = ([_title_row(spec, span)] if spec.header else []) + rows
    table = N.Command(span, "table", span, _args(span, **keywords), "env", [], children)
    table.parallel = spec
    return table


def build_tables(spec: ParallelSpec, items: list[Any], span: Span, sink: DiagnosticSink) -> list[Any]:
    """The blocks that replace a ``|parallel``: tables and the page breaks between them.

    Args:
        spec: the checked arguments of ``|parallel``.
        items: the evaluated content — :class:`EvaluatedSegment` objects and
            ``|page``/``|newpage`` commands, in document order (other blocks
            are reported by the evaluator before).
        span: the ``|parallel`` command (positions of the generated nodes).
        sink: receiver of P5301.

    Returns:
        The blocks in document order.
    """
    out: list[Any] = []
    rows: list[N.Command] = []
    for item in items:
        if isinstance(item, EvaluatedSegment):
            rows.append(_segment_row(spec, item, sink))
        elif isinstance(item, N.Command):
            if rows:
                out.append(_table(spec, rows, span))
                rows = []
            out.append(item)
    if rows or not out:
        out.append(_table(spec, rows, span))
    tables = [block for block in out if isinstance(block, N.Command) and block.name == "table"]
    tables[-1].parallel_last = True  # the counters of the tracks are compared after it (P5315)
    return out
