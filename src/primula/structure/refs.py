"""Cross-references ``|@(id, mode, case=…)`` (specification 5.7, 5.10).

Modes (decisions 69, 72, 76):

* ``number`` (default) — the composite number in ``ref_format`` («1.2»);
* ``label`` — the label of the target kind and the number, separated by a
  no-break space («п. 1.2»); ``case=`` selects a grammatical form;
* ``title`` — the title of a heading, annex, figure or table, or the text
  of the first paragraph of a clause;
* ``page`` — a Writer page-number field.

A reference to a note is a ``text:note-ref`` field (number or page).  The
target ID is looked up with the ``ns.`` prefixes of the inclusion of the
reference first, then without them (decision 74).  An unknown target
excluded by a condition is reported as such (decision 75).
"""

from __future__ import annotations

from typing import Any

from primula.diagnostics import DiagnosticSink, error, warning
from primula.i18n import Key
from primula.source import Span
from primula.structure.args import check_args
from primula.structure.model import Resolved, Target
from primula.structure.settings import CASES, StructureSettings
from primula.unicode import nfkc

MODES = ("number", "label", "title", "page")
#: Kinds whose numbers and titles cannot be referenced (page only).
_PAGE_ONLY = ("admonition", "section")


def _candidates(node: Any, raw: str) -> list[str]:
    """IDs to try: with the inclusion prefixes (longest first), then plain.

    In a part of a compound document (10.7) the IDs of the part
    (``scope:id``) are tried first, then those of the root document; an ID
    with ``:`` is a full ID of a part and is used as is.
    """
    if ":" in raw:
        return [raw]
    scopes = [entry for entry in getattr(node, "id_scopes", []) if entry[0]]
    prefixes = [ns for ns, _span, _path in scopes]
    plain = [".".join([*prefixes[:k], raw]) for k in range(len(prefixes), -1, -1)]
    primary = getattr(node, "track_primary", None)
    if primary is not None:
        # A reference in a non-primary track of |parallel (7.7): its own track,
        # then the primary track, then the IDs outside the tracks.
        own = next((k for k, entry in enumerate(scopes) if str(entry[2]).startswith("<track ")), None)
        if own is not None:
            swapped = [*prefixes[:own], primary, *prefixes[own + 1:]]
            plain.insert(1, ".".join([*swapped, raw]))
    part = getattr(node, "part_scope", None)
    return [f"{part}:{c}" for c in plain] + plain if part else plain


def _external(node: Any, raw: str, mode: str, entry: dict[str, Any], values: dict[str, Any],
              settings: StructureSettings, sink: DiagnosticSink) -> Resolved | None:
    """A target of another document of the project: text without a hyperlink (decision 121)."""
    if mode == "page":
        sink.emit(error("P4308", node.span, id=raw))
        return None
    number = entry.get("number")
    if mode == "title":
        return Resolved("title", str(entry.get("title") or ""))
    if number is None:
        sink.emit(error("P4304", node.span, mode=mode, kind=str(entry.get("kind")), id=raw))
        return None
    text = str(settings.numbering.get("ref_format", "{n}")).replace("{n}", str(number))
    if mode == "number":
        return Resolved("number", text)
    if settings.labels is None:
        sink.emit(error("P4305", node.span, language=settings.language))
        return None
    case = values.get("case", "short")
    label = (settings.labels.get(entry.get("label_key") or "") or {}).get(case) if case in CASES else None
    if not isinstance(label, str):
        sink.emit(error("P4306", node.span, case=case, key=entry.get("label_key") or entry.get("kind"),
                        language=settings.language))
        return None
    return Resolved("label", f"{label}\u00a0{text}")  # a no-break space, as for own targets (5.7)


def resolve_references(references: list[Any], targets: dict[str, Target], settings: StructureSettings,
                       sink: DiagnosticSink, excluded: dict[str, tuple[str, Span]], external: Any = None,
                       primaries: list[str] | None = None) -> None:
    """Resolve every ``|@`` node; set ``node.resolved`` (``None`` after an error).

    ``external`` (:class:`~primula.xrefs.ExternalReferences`) holds the targets
    of other documents of the project; they are used for IDs the document
    itself does not have (decision 121).  ``primaries`` — the primary tracks
    of ``|parallel``: a short ID found nowhere else is an ID of a primary
    track (7.7).  A reference written in a track block uses the settings of
    the language of the track (``node.ref_settings``: labels, formats).
    """
    for node in references:
        own = getattr(node, "ref_settings", None) or settings
        node.resolved = _resolve(node, targets, own, sink, excluded, external, primaries or [])


def _resolve(node: Any, targets: dict[str, Target], settings: StructureSettings, sink: DiagnosticSink,
             excluded: dict[str, tuple[str, Span]], external: Any = None,
             primaries: list[str] | None = None) -> Resolved | None:
    args = node.args
    positional = list(args.positional) if args is not None else []
    values = check_args(args, "ref", "|@", sink)
    if not positional or not isinstance(positional[0], str) or len(positional) > 2:
        sink.emit(error("P4105", node.span, name="id", command="|@", expected=Key("type.string")))
        return None
    raw = nfkc(positional[0])  # IDs compare by NFKC (5.6)
    mode = positional[1] if len(positional) > 1 else "number"
    if mode not in MODES:
        sink.emit(error("P4307", node.span, mode=str(mode)))
        return None
    candidates = _candidates(node, raw)
    if ":" not in raw:
        candidates += [f"{primary}.{raw}" for primary in primaries or []]
    target = next((targets[c] for c in candidates if c in targets), None)
    if target is None:
        excluded_id = next((c for c in _candidates(node, raw) if c in excluded), None)
        if excluded_id is not None:
            condition, span = excluded[excluded_id]
            sink.emit(error("P4302", node.span, id=raw).note("note.condition", span, condition=condition))
            return None
        found = external.lookup(raw) if external is not None else []
        if not found:
            sink.emit(error("P4301", node.span, id=raw))
            return None
        if len(found) > 1:
            sink.emit(error("P4309", node.span, id=raw, documents=", ".join(name for name, _entry in found)))
            return None
        name, entry = found[0]
        external.record(raw, name)
        return _external(node, raw, mode, entry, values, settings, sink)
    if target.condition is not None:
        sink.emit(warning("P4303", node.span, id=raw, condition=target.condition))

    if target.note is not None:
        if mode in ("label", "title"):
            sink.emit(error("P4304", node.span, mode=mode, kind=target.kind, id=raw))
            return None
        return Resolved(mode, target.note.citation if mode == "number" else "?",
                        note_class=target.note.note_class, note_id=target.note.note_id)
    if mode == "page":
        return Resolved("page", "?", bookmark=target.bookmark)
    if target.kind in _PAGE_ONLY or (mode != "title" and target.number is None):
        sink.emit(error("P4304", node.span, mode=mode, kind=target.kind, id=raw))
        return None
    if mode == "title":
        text = target.title() if callable(target.title) else (target.title or "")
        return Resolved("title", text, bookmark=target.bookmark)
    number = str(settings.numbering.get("ref_format", "{n}")).replace("{n}", target.number or "")
    if mode == "number":
        return Resolved("number", number, bookmark=target.bookmark)
    # label
    if settings.labels is None:
        sink.emit(error("P4305", node.span, language=settings.language))
        return None
    case = values.get("case", "short")
    if case not in CASES:
        sink.emit(error("P4306", node.span, case=case, key=target.label_key or target.kind,
                        language=settings.language))
        return None
    forms = settings.labels.get(target.label_key or "") or {}
    label = forms.get(case)
    if not isinstance(label, str):
        sink.emit(error("P4306", node.span, case=case, key=target.label_key or target.kind,
                        language=settings.language))
        return None
    return Resolved("label", f"{label} {number}", bookmark=target.bookmark)
