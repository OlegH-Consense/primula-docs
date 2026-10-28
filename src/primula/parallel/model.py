"""The description of parallel tracks (specification 7.7, decision 134; stage 16.2).

``track(id, lang=None, title=None, width=None, block=None, role=None,
primary=False, numbered=True, optional=False)`` returns a :class:`Track`
record (like ``col(…)`` of a table).  :func:`parallel_spec` checks the
arguments of ``|parallel`` and gives a :class:`ParallelSpec`;
:func:`segment_args` and :func:`track_args` check the arguments of
``|segment`` and of a track block.  Every problem is error P5305 with the
construct, a translated description and the value.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from primula.core.errors import CoreError, core_error
from primula.core.values import Builtin, Length, PList, Record, parse_length
from primula.i18n import Key
from primula.library.context import LANGUAGES, language_code
from primula.unicode import is_identifier

#: Profiles of the correspondence check (7.7).
PARITY = ("structure", "translation", "none")
#: Arguments of ``|parallel`` (7.7).
PARALLEL_ARGS = ("tracks", "langs", "primary", "widths", "gap", "rule", "header", "parity", "style",
                 "keep_rows", "id")
#: Arguments of ``|segment`` (``when`` is handled by the evaluator).
SEGMENT_ARGS = ("id", "span", "parity", "keep", "status")
#: Arguments of a track block ``|track("id", …)`` besides the id (``when`` by the evaluator).
TRACK_BLOCK_ARGS = ("status", "rev")
#: Keyword arguments of ``track(…)``.
TRACK_ARGS = ("lang", "title", "width", "block", "role", "primary", "numbered", "optional")
#: Commands that may not stand inside a segment (7.7): page structure,
#: indexes and nested parallel texts.  Frames anchored to the page too.
FORBIDDEN = frozenset({"page", "newpage", "newcolumn", "section", "appendix", "scope", "header", "footer",
                       "document", "toc", "list_of", "watermark", "parallel"})
#: The default gap between the tracks (7.7).
DEFAULT_GAP = "6mm"


class Track(Record):
    """A track made by ``track(…)``: fields ``id``, ``lang``, ``title``, ``width``, ``block``,
    ``role``, ``primary``, ``numbered``, ``optional`` (dot access in code: ``track.lang``)."""


@dataclass
class ParallelSpec:
    """The checked arguments of one ``|parallel``.

    Attributes:
        tracks: the tracks in column order.
        primary: id of the primary track.
        widths: column width of every track (``width`` of the track, else ``widths``, else ``"*"``).
        gap: the gap between tracks.
        rule: the rule between tracks (a border value) or ``None``.
        header: write the row of track titles.
        parity: the correspondence profile (checked at stage 16.4).
        style: the table style name, or ``None`` for ``structure_styles(parallel_table=…)``.
        keep_rows: do not break segments between pages.
        id: the identifier of the environment, or ``None``.
        unsupported: ids of tracks whose language the library does not support (P5308).
    """

    tracks: list[Track]
    primary: str
    widths: list[Any]
    gap: Length
    rule: Any = None
    header: bool = False
    parity: str = "structure"
    style: str | None = None
    keep_rows: bool = False
    id: str | None = None
    unsupported: list[str] = field(default_factory=list)

    def track(self, track_id: str) -> Track | None:
        """The track with this id, or ``None``."""
        return next((t for t in self.tracks if t.fields["id"] == track_id), None)


def problem(span: Any, command: str, key: str, value: Any = "") -> CoreError:
    """Error P5305 for ``command`` (``|parallel``, ``|segment``, ``track()``…)."""
    return core_error("P5305", span, command=command, problem=Key("parallel." + key), value=str(value))


def _flag(value: Any, name: str, command: str, span: Any) -> bool:
    if not isinstance(value, bool):
        raise problem(span, command, "bad_arg", name)
    return value


def _text(value: Any, name: str, command: str, span: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise problem(span, command, "bad_arg", name)
    return value


def _identifier(value: Any, name: str, command: str, span: Any) -> str:
    # IDs of tracks and segments follow the IDs of blocks (5.6): '-' and '.' after the first letter.
    if not isinstance(value, str) or not is_identifier(value, "-."):
        raise problem(span, command, "bad_id", f"{name}={value!r}" if not isinstance(value, str) else value)
    return value


def check_language(value: Any, command: str, span: Any) -> str | None:
    """A BCP 47 tag like ``doc.language`` (2.3), or ``None``; a malformed tag is P5305."""
    if value is None:
        return None
    from primula.styles.schema import PropertyError, check_property

    try:
        return check_property("paragraph", "language", value)
    except PropertyError:
        raise problem(span, command, "bad_lang", value) from None


def _width(value: Any, command: str, span: Any) -> Any:
    from primula.tables.columns import parse_width

    try:
        parse_width(value)
    except (ValueError, TypeError):
        raise problem(span, command, "bad_arg", f"width={value}") from None
    return value


def _track(interp: Any, args: list[Any], kwargs: dict[str, Any], span: Any) -> Track:
    """``track(id, …)`` (7.7): check the arguments and return a :class:`Track`."""
    if len(args) != 1 and not (not args and "id" in kwargs):
        raise problem(span, "track()", "track_id", "")
    track_id = _identifier(args[0] if args else kwargs.pop("id"), "id", "track()", span)
    fields: dict[str, Any] = {"id": track_id, "lang": None, "title": None, "width": None, "block": None,
                              "role": None, "primary": False, "numbered": True, "optional": False}
    for name, value in kwargs.items():
        if name not in TRACK_ARGS:
            raise problem(span, "track()", "bad_arg", name)
        if name == "lang":
            fields[name] = check_language(value, "track()", span)
        elif name in ("primary", "numbered", "optional"):
            fields[name] = _flag(value, name, "track()", span)
        elif name == "width":
            fields[name] = _width(value, "track()", span) if value is not None else None
        else:
            fields[name] = _text(value, name, "track()", span)
    return Track(fields)


def make_parallel_builtins() -> dict[str, Builtin]:
    """The built-in ``track``."""
    return {"track": Builtin("track", _track)}


def parallel_spec(keywords: dict[str, Any], positional: list[Any], span: Any) -> ParallelSpec:
    """Check the arguments of ``|parallel`` (7.7).

    Args:
        keywords: evaluated keyword arguments.
        positional: evaluated positional arguments (none are allowed).
        span: the position for errors.

    Raises:
        CoreError: P5305 for the first problem found.
    """
    command = "|parallel"
    if positional:
        raise problem(span, command, "bad_arg", positional[0])
    for name in keywords:
        if name not in PARALLEL_ARGS:
            raise problem(span, command, "bad_arg", name)
    tracks_arg, langs = keywords.get("tracks"), keywords.get("langs")
    if tracks_arg is not None and langs is not None:
        raise problem(span, command, "tracks_and_langs", "tracks=, langs=")
    tracks: list[Track] = []
    if langs is not None:
        if not isinstance(langs, (list, tuple, PList)):
            raise problem(span, command, "bad_arg", "langs")
        for lang in langs:
            tag = check_language(lang, command, span)
            tracks.append(_track(None, [tag], {"lang": tag}, span))
    elif tracks_arg is not None:
        if not isinstance(tracks_arg, (list, tuple, PList)):
            raise problem(span, command, "bad_arg", "tracks")
        for item in tracks_arg:
            if isinstance(item, Track):
                tracks.append(item)
            elif isinstance(item, str):
                tracks.append(_track(None, [item], {}, span))
            else:
                raise problem(span, command, "bad_track", item)
    if len(tracks) < 2:
        raise problem(span, command, "few_tracks", len(tracks))
    seen: set[str] = set()
    for track in tracks:
        track_id = track.fields["id"]
        if track_id in seen:
            raise problem(span, command, "dup_track", track_id)
        seen.add(track_id)

    marked = [t.fields["id"] for t in tracks if t.fields["primary"]]
    primary = keywords.get("primary")
    if primary is not None:
        if not isinstance(primary, str) or primary not in seen:
            raise problem(span, command, "unknown_primary", primary)
        if marked and marked != [primary]:
            raise problem(span, command, "two_primary", ", ".join([primary, *marked]))
    elif len(marked) > 1:
        raise problem(span, command, "two_primary", ", ".join(marked))
    else:
        primary = marked[0] if marked else tracks[0].fields["id"]
    main = next(t for t in tracks if t.fields["id"] == primary)
    if main.fields["optional"] or not main.fields["numbered"]:
        raise problem(span, command, "primary_optional", primary)
    tracks = [Track({**t.fields, "primary": t.fields["id"] == primary}) for t in tracks]

    widths_arg = keywords.get("widths")
    if widths_arg is not None and (not isinstance(widths_arg, (list, tuple, PList)) or len(widths_arg) != len(tracks)):
        raise problem(span, command, "bad_widths", len(tracks))
    widths = []
    for index, track in enumerate(tracks):
        width = track.fields["width"]
        if width is None and widths_arg is not None:
            width = _width(widths_arg[index], command, span)
        widths.append(width if width is not None else "*")

    gap = _length(keywords.get("gap", DEFAULT_GAP), "gap", command, span)
    rule = None
    if keywords.get("rule") is not None:
        from primula.styles.schema import PropertyError, check_property

        try:
            rule = check_property("table", "header_border_left", keywords["rule"])
        except PropertyError:
            raise problem(span, command, "bad_arg", f"rule={keywords['rule']}") from None
    header = keywords.get("header")
    header = any(t.fields["title"] for t in tracks) if header is None else _flag(header, "header", command, span)
    parity = keywords.get("parity", "structure")
    if parity not in PARITY:
        raise problem(span, command, "bad_parity", parity)
    style = _text(keywords.get("style"), "style", command, span)
    keep_rows = _flag(keywords.get("keep_rows", False), "keep_rows", command, span)
    env_id = keywords.get("id")
    env_id = _identifier(env_id, "id", command, span) if env_id is not None else None
    unsupported = [t.fields["id"] for t in tracks
                   if t.fields["lang"] is not None and language_code(t.fields["lang"]) not in LANGUAGES]
    return ParallelSpec(tracks, primary, widths, gap, rule, header, parity, style, keep_rows, env_id, unsupported)


def _length(value: Any, name: str, command: str, span: Any) -> Length:
    if isinstance(value, Length):
        length = value
    elif isinstance(value, str):
        length = parse_length(value)
    else:
        length = None
    if length is None or length.value < 0:
        raise problem(span, command, "bad_arg", f"{name}={value}")
    return length


def half(length: Length) -> Length:
    """Half of a length in its unit (each side of a gap, 7.7)."""
    return Length(length.value / Decimal(2), length.unit)


@dataclass
class SegmentArgs:
    """Checked arguments of ``|segment``."""

    id: str | None = None
    full: bool = False
    parity: str | None = None
    keep: bool = False
    status: str | None = None


def segment_args(keywords: dict[str, Any], positional: list[Any], span: Any) -> SegmentArgs:
    """Check the arguments of ``|segment`` (7.7)."""
    command = "|segment"
    if positional:
        raise problem(span, command, "bad_arg", positional[0])
    for name in keywords:
        if name not in SEGMENT_ARGS:
            raise problem(span, command, "bad_arg", name)
    result = SegmentArgs()
    if keywords.get("id") is not None:
        result.id = _identifier(keywords["id"], "id", command, span)
    span_value = keywords.get("span")
    if span_value is not None:
        if span_value != "all":
            raise problem(span, command, "bad_arg", f"span={span_value}")
        result.full = True
    if keywords.get("parity") is not None:
        if keywords["parity"] not in PARITY:
            raise problem(span, command, "bad_parity", keywords["parity"])
        result.parity = keywords["parity"]
    result.keep = _flag(keywords.get("keep", False), "keep", command, span)
    result.status = _text(keywords.get("status"), "status", command, span)
    return result


@dataclass
class TrackBlockArgs:
    """Checked arguments of a track block ``|track("id", status=…, rev=…)``."""

    track: str
    status: str | None = None
    rev: str | None = None


def track_args(keywords: dict[str, Any], positional: list[Any], span: Any) -> TrackBlockArgs:
    """Check the arguments of a track block (7.7); ``rev`` is checked at stage 16.5."""
    command = "|track"
    if len(positional) != 1 or not isinstance(positional[0], str):
        raise problem(span, command, "track_id", positional[0] if positional else "")
    for name in keywords:
        if name not in TRACK_BLOCK_ARGS:
            raise problem(span, command, "bad_arg", name)
    return TrackBlockArgs(positional[0], _text(keywords.get("status"), "status", command, span),
                          _text(keywords.get("rev"), "rev", command, span))


def segment_record(args: SegmentArgs) -> Record:
    """The record ``segment`` of the code of a track block (7.7)."""
    return Record({"id": args.id, "status": args.status})
