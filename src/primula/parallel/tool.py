"""``primula parallel``: blanks, confirmation and status of track blocks (specification 7.7, 14.1; stage 16.5).

The command evaluates the document like ``check`` and then works with its
segments (:class:`~primula.parallel.build.EvaluatedSegment`):

* ``--stub --track ID`` — in every segment without a block of the track
  ``ID`` a block is written: a copy of the structure of the primary block
  (headings, clauses, list items, styled lines, table rows and the lines of
  environments) with placeholders ``|?{…}`` instead of text; a segment in
  the line form gets ``|track("ID"){|?{…}}``;
* ``--stamp --track ID [--segment SEG…] [--status S]`` — the confirmation of
  a translation: ``rev="<primary>/<own>"`` (and ``status``) is written into
  the arguments of the blocks of the track; without ``--segment`` every
  block is confirmed and the confirmed segments are listed, the outdated
  ones marked;
* ``--check-status S`` — every block of a non-primary track (except an
  absent block of an optional track) has the status ``S`` (its own or the
  one of its segment) and no outdated ``rev``; otherwise P0107 for each.

Only the file named on the command line is rewritten; blocks that come from
included fragments are listed and left as they are.  Changes are written
only when the document has no errors and the file is in normalized form
(LF line ends, NFC, no BOM), so that nothing else changes; a repeated run
changes nothing.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, TextIO

from primula.diagnostics import DiagnosticSink, error
from primula.i18n import Catalog, Key
from primula.structure.tree import iter_tree
from primula.syntax import lines as L
from primula.syntax import nodes as N
from primula.syntax import pyscan

PLACEHOLDER = "|?{…}"


def segments(document: N.Document) -> list[tuple[Any, Any]]:
    """``(spec, segment)`` of every evaluated segment in document order."""
    found: list[tuple[Any, Any]] = []
    seen: set[int] = set()
    for node in iter_tree(document.children):
        spec = getattr(node, "parallel", None) if isinstance(node, N.Command) else None
        if spec is None:
            continue
        for row in node.children:
            segment = getattr(row, "segment", None)
            if segment is not None and id(segment) not in seen:
                seen.add(id(segment))
                found.append((spec, segment))
    return found


def _problem(sink: DiagnosticSink, file: str, key: str, value: str = "") -> None:
    sink.emit(error("P0106", None, at_file=file, problem=Key("parallel.tool." + key), value=value))


def run(args: argparse.Namespace, result: Any, sink: DiagnosticSink, out: TextIO, catalog: Catalog) -> None:
    """Run ``primula parallel`` on the analysed document (see the module description)."""
    file = str(args.file)
    evaluation = getattr(result, "evaluation", None)
    if evaluation is None or sink.has_errors:
        _problem(sink, file, "errors")
        return
    found = segments(evaluation.document)
    tracks = {t.fields["id"]: t for spec, _segment in found for t in spec.tracks}
    if args.check_status is not None:
        _check_status(args.check_status, found, sink, out, catalog, file)
        return
    if not args.track:
        _problem(sink, file, "no_track")
        return
    if args.track not in tracks:
        _problem(sink, file, "unknown_track", args.track)
        return
    known = {segment.id for _spec, segment in found}
    for name in args.segment or []:
        if name not in known:
            _problem(sink, file, "unknown_segment", name)
            return
    source = result.source
    path = Path(source.path) if source.path is not None else Path(file)
    raw = path.read_bytes().decode("utf-8", errors="replace")
    if raw != source.text:
        _problem(sink, file, "not_normalized")
        return
    edits: list[tuple[int, int, str]] = []
    if args.stub:
        _stub(args.track, found, source, edits, out, catalog, file)
    else:
        _stamp(args, found, source, edits, out, catalog, file, sink)
    if sink.has_errors:
        return
    if not edits:
        print(catalog.text("cli.parallel.unchanged", file=file), file=out)
        return
    text = source.text
    for start, end, new in sorted(edits, reverse=True):
        text = text[:start] + new + text[end:]
    path.write_text(text, encoding="utf-8", newline="")
    print(catalog.text("cli.parallel.written", file=file, count=len(edits)), file=out)


# --- --stamp ---------------------------------------------------------------------------------------------


def _argument_text(block: N.Command, updates: dict[str, str]) -> str:
    """The arguments of a track block with ``updates`` (keyword -> value text) applied."""
    args = block.args
    fragment = args.fragment
    parts = [fragment.segment(node) for node in args.call.args]
    written = set()
    for keyword in args.call.keywords:
        if keyword.arg in updates:
            parts.append(f"{keyword.arg}={updates[keyword.arg]}")
            written.add(keyword.arg)
        else:
            parts.append(f"{keyword.arg}={fragment.segment(keyword.value)}" if keyword.arg
                         else f"**{fragment.segment(keyword.value)}")
    parts += [f"{name}={value}" for name, value in updates.items() if name not in written]
    return "(" + ", ".join(parts) + ")"


def _stamp(args: argparse.Namespace, found: list[tuple[Any, Any]], source: Any, edits: list[tuple[int, int, str]],
           out: TextIO, catalog: Catalog, file: str, sink: DiagnosticSink) -> None:
    track = args.track
    for spec, segment in found:
        if spec.track(track) is None or segment.full:
            continue
        if args.segment and segment.id not in args.segment:
            continue
        if track == spec.primary:
            _problem(sink, file, "primary", track)
            return
        block = segment.sources.get(track)
        if block is None or spec.primary not in segment.hashes:
            continue
        name = segment.id or "—"
        if block.span.source is not source:
            print(catalog.text("cli.parallel.in_fragment", segment=name, file=block.span.source.name), file=out)
            continue
        rev = f"{segment.hashes[spec.primary]}/{segment.hashes[track]}"
        updates = {"rev": f'"{rev}"'}
        if args.status is not None:
            updates["status"] = f'"{args.status}"'
        before = segment.track_args[track].rev
        outdated = before is None or segment.stale.get(track) or segment.changed.get(track)
        new = _argument_text(block, updates) if block.args is not None else f'("{track}", rev="{rev}")'
        start = block.args.span.start if block.args is not None else block.span.start + len("|track")
        end = block.args.span.end if block.args is not None else start
        if source.text[start:end] != new:
            edits.append((start, end, new))
        print(catalog.text("cli.parallel.stamped", segment=name, rev=rev)
              + (catalog.text("cli.parallel.was_outdated") if outdated else ""), file=out)


# --- --stub ----------------------------------------------------------------------------------------------


def _head(text: str, start: int) -> int:
    """The end of a line head: the marker characters and a bracket group after them."""
    position = start
    while position < len(text) and text[position] not in " \t\n(":
        position += 1
    if position < len(text) and text[position] == "(":
        try:
            position = pyscan.find_closing(text, position) + 1
        except pyscan.ScanError:
            pass
    return position


def _row_stub(text: str, content: int, end: int) -> str:
    """``|: a |& b`` -> ``|: |?{…} |& |?{…}`` (cell arguments kept)."""
    line = text[content:end]
    head = _head(line, 2) if line.startswith("|:(") else 2
    pieces = ["|:" + line[2:head]]
    rest = line[head:]
    cells = rest.split("|&")
    pieces.append(" " + PLACEHOLDER if cells[0].strip() or len(cells) == 1 else "")
    for cell in cells[1:]:
        args = cell[:_head(cell, 0)] if cell.startswith("(") else ""
        pieces.append(" |&" + args + " " + PLACEHOLDER)
    return "".join(pieces)


def stub_lines(block: N.Command, indent: str) -> list[str]:
    """The lines of a blank copy of a primary track block (``--stub``)."""
    text = block.span.source.text
    if block.form == "inline":
        return [indent + PLACEHOLDER]
    start = text.find("\n", block.span.start) + 1
    children = [c for c in block.children if not isinstance(c, N.BlankLine)]
    end = max((c.span.end for c in children), default=start)
    raw_spans = [(c.span.start, c.span.end) for c in iter_tree(children)
                 if isinstance(c, (N.CodeBlock, N.Verbatim))]
    skipped = [(c.span.start, c.span.end) for c in iter_tree(children) if isinstance(c, N.CommentBlock)]
    result: list[str] = []
    position = start
    paragraph = False
    while position < end:
        line_end = text.find("\n", position)
        line_end = len(text) if line_end < 0 else line_end
        line = text[position:line_end]
        if any(a <= position < b for a, b in skipped):
            pass
        elif any(a <= position < b for a, b in raw_spans):
            result.append(line)
            paragraph = False
        else:
            info = L.classify(text, position)
            pad = text[position:info.content]
            kind = info.kind
            if kind is L.Kind.BLANK:
                result.append("")
                paragraph = False
            elif kind is L.Kind.COMMENT:
                pass
            elif kind is L.Kind.TEXT:
                if not paragraph:
                    result.append(pad + PLACEHOLDER)
                paragraph = True
            elif kind is L.Kind.ROW:
                result.append(pad + _row_stub(text, info.content, line_end))
                paragraph = False
            elif kind in (L.Kind.HEADING, L.Kind.CLAUSE, L.Kind.LIST, L.Kind.ADMONITION):
                head = _head(text, info.content)
                body_line = text[head:line_end].strip()
                result.append(text[position:head] + (" " + PLACEHOLDER if body_line and body_line != ":" else
                                                     body_line and ":"))
                paragraph = False
            elif kind in (L.Kind.STYLE, L.Kind.COLON):
                colon = text.find(":", _head(text, info.content) if kind is L.Kind.COLON else info.content + 2)
                tail = text[colon + 1:line_end].strip()
                # '|.Name: text' gets a placeholder; '|.Name:' (an environment) stays.
                result.append(text[position:colon + 1] + " " + PLACEHOLDER if tail else line)
                paragraph = False
            else:
                result.append(line)  # environments, closings, line commands, control constructs
                paragraph = False
        position = line_end + 1
    while result and not result[-1].strip():
        result.pop()
    return [indent + line if line else line for line in result] if indent else result


def _indent(text: str, offset: int) -> str:
    line_start = text.rfind("\n", 0, offset) + 1
    content = L.skip_ws(text, line_start)
    return text[line_start:content]


def _stub(track: str, found: list[tuple[Any, Any]], source: Any, edits: list[tuple[int, int, str]],
          out: TextIO, catalog: Catalog, file: str) -> None:
    text = source.text
    for spec, segment in found:
        if spec.track(track) is None or segment.full or track in segment.track_args:
            continue
        primary = segment.sources.get(spec.primary)
        if primary is None:
            continue
        name = segment.id or "—"
        if segment.span.source is not source:
            print(catalog.text("cli.parallel.in_fragment", segment=name, file=segment.span.source.name), file=out)
            continue
        end = segment.span.end
        if end and text[end - 1:end] == "\n":
            end -= 1
        line_start = text.rfind("\n", 0, end) + 1
        closing = text[line_start:end].strip()
        if primary.form == "inline":
            # The line form: one more track body at the end of the line.
            line_end = text.find("\n", segment.span.start)
            line_end = len(text) if line_end < 0 else line_end
            edits.append((line_end, line_end, f' |track("{track}"){{{PLACEHOLDER}}}'))
        elif closing.startswith("|end"):
            indent = _indent(text, primary.span.start)
            body = stub_lines(primary, "")
            block = "\n".join([f'{indent}|track("{track}"):', *body]) + "\n"
            edits.append((line_start, line_start, block))
        else:
            continue
        print(catalog.text("cli.parallel.stubbed", segment=name, track=track), file=out)


# --- --check-status --------------------------------------------------------------------------------------


def _check_status(expected: str, found: list[tuple[Any, Any]], sink: DiagnosticSink, out: TextIO,
                  catalog: Catalog, file: str) -> None:
    checked = 0
    for spec, segment in found:
        if segment.full:
            continue
        name = segment.id or "—"
        for track in spec.tracks:
            track_id = track.fields["id"]
            if track_id == spec.primary:
                continue
            args = segment.track_args.get(track_id)
            where = segment.track_spans.get(track_id, segment.span)
            if args is None:
                if not track.fields["optional"]:
                    sink.emit(error("P0107", where, segment=name, track=track_id, expected=expected,
                                    reason=Key("parallel.status.no_block"), status="—"))
                continue
            checked += 1
            status = args.status or segment.status
            if status != expected:
                sink.emit(error("P0107", where, segment=name, track=track_id, expected=expected,
                                reason=Key("parallel.status.other"), status=status or "—"))
            elif segment.stale.get(track_id) or segment.changed.get(track_id):
                sink.emit(error("P0107", where, segment=name, track=track_id, expected=expected,
                                reason=Key("parallel.status.outdated"), status=status))
    if not sink.has_errors:
        print(catalog.text("cli.parallel.status_ok", file=file, count=checked, status=expected), file=out)
