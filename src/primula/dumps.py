"""JSON dumps of ``primula check`` for editors and Primula Studio (14.1; stage 14.2).

``primula check DOC --dump-structure --dump-styles`` prints one JSON object
to stdout (the diagnostics still go to stderr, and are also listed in the
object)::

    {"schema": 1, "file": "doc.prml",
     "structure": {"items": [...], "includes": [...]},     # --dump-structure
     "styles": {"layers": [...], "styles": [...], ...},    # --dump-styles
     "messages": [...]}

A key is ``null`` when the phase that produces it did not run (errors
before the structure phase, for example); Studio then keeps its previous
data and marks it as stale.

Structure items, in document order (``kind``):

* ``heading`` — ``level`` (1-6), ``number``, ``title``, ``id``;
* ``clause`` — ``level`` (depth of the clause), ``number``, ``text`` (the
  beginning of the clause text), ``id``;
* ``appendix`` — ``outline`` (outline level), ``designation``, ``title``, ``id``;
* ``table``, ``figure`` — with a caption: ``number``, ``title``, ``id``;
  without a caption only when they have an ``id``;
* ``list`` — a numbered list with ``id=`` (its sequence name);
* ``admonition``, ``section`` — when they have an ``id``.

Every item and every include has the position ``file`` (display name as in
the diagnostics), ``path`` (absolute) and ``line``/``column`` (from 1), and
``part`` — the scope of the part of a compound document (10.7) or ``null``.
``id`` is the full ID used by ``|@`` (with the ``ns.`` and ``part:``
prefixes), or ``null``.

Includes: ``kind`` (``include`` or ``document``), the position of the
command, ``target`` (absolute path of the included file) and ``ns``,
``part`` (``|include``) or ``scope`` (``|document``).

Styles: every style of the merged system with its ``kind``, ``parent``,
the layers that define it (``definitions``), its own properties with the
layer and position of the definition each one comes from (``own``), and the
effective properties with the style of the inheritance chain that gives
each one (``effective``).  Materialised styles (``derive``, parametric
variants) have ``materialized: true``.  Layer origins: ``project``,
``option`` (``--style``), ``header`` (``styles`` of the document header),
``default`` (``std/styles/default`` by default), ``document``.
"""

from __future__ import annotations

from decimal import Decimal
from fractions import Fraction
from typing import Any

#: Version of the dump format; a change of meaning of a field increases it.
DUMP_SCHEMA = 1
#: Length of the clause text in the structure dump (characters).
_TEXT_LIMIT = 80


def make_dump(result: Any, *, file: str, structure: bool, styles: bool, messages: list[dict[str, Any]]
              ) -> dict[str, Any]:
    """The JSON object of ``--dump-structure``/``--dump-styles``.

    Args:
        result: the front-end result (:class:`~primula.frontend.FrontendResult`) or ``None``.
        file: the document as given on the command line.
        structure: include the structure (``--dump-structure``).
        styles: include the styles (``--dump-styles``).
        messages: diagnostics of the run in the JSON form (14.2).

    Returns:
        A JSON-compatible dictionary (see the module description).
    """
    evaluation = getattr(result, "evaluation", None) if result is not None else None
    data: dict[str, Any] = {"schema": DUMP_SCHEMA, "file": file}
    if structure:
        data["structure"] = _structure(evaluation)
        data["params"] = _params(result)
    if styles:
        system = getattr(evaluation, "styles", None) if evaluation is not None else None
        data["styles"] = _styles(system) if system is not None else None
    data["messages"] = messages
    return data


def _params(result: Any) -> dict[str, Any]:
    """Parameters of the document (decision 127, the build parameters form of Studio).

    The parameters of the project (10.6) and of the document header (2.3) in
    declaration order; a document parameter with the name of a project one
    overrides its value.  Each: ``type``, ``default`` (the text a
    ``--param NAME=VALUE`` takes: strings as they are, ``true``/``false``,
    numbers, ISO dates; other values as in Primula) and ``origin``
    (``project`` or ``document``).
    """
    from primula.core.values import DateTime, decimal_to_str, from_data, to_repr, type_name

    def text(value: Any) -> str:
        if isinstance(value, str):
            return value
        if isinstance(value, bool):
            return "true" if value else "false"
        if value is None:
            return ""
        if isinstance(value, DateTime):
            return value.iso()
        return decimal_to_str(value) if isinstance(value, Decimal) else to_repr(value)

    params: dict[str, Any] = {}
    project = getattr(result, "project", None) if result is not None else None
    for name, (value, _span) in (getattr(project, "params", None) or {}).items():
        params[name] = {"type": type_name(value), "default": text(value), "origin": "project"}
    header = getattr(result, "header", None) if result is not None else None
    declared = header.data.get("params") if header is not None and isinstance(header.data, dict) else None
    for name, raw in (declared or {}).items() if isinstance(declared, dict) else ():
        value = from_data(raw)
        params[str(name)] = {"type": type_name(value), "default": text(value), "origin": "document"}
    return params


# ----------------------------------------------------------------------
# Positions and values
# ----------------------------------------------------------------------

def _position(span: Any) -> dict[str, Any]:
    """``file``, ``path``, ``line``, ``column`` of a span (``None`` values without one)."""
    if span is None:
        return {"file": None, "path": None, "line": None, "column": None}
    source = span.source
    position = span.begin_position
    path = getattr(source, "path", None)
    return {"file": source.name, "path": str(path.resolve()) if path is not None else None,
            "line": position.line, "column": position.column}


def _json(value: Any) -> Any:
    """A property value in JSON form, written as in a styles module.

    Lengths are ``"2mm"``, a line height ``"115%"``/``"5mm"``/``"at_least 5mm"``,
    a border ``"0.5pt solid #000000"`` or ``"none"``, numbers as text.
    """
    from primula.core.values import Length, decimal_to_str, format_length
    from primula.styles.schema import Border, LineHeight

    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        return value
    if isinstance(value, Decimal):
        return decimal_to_str(value)
    if isinstance(value, Fraction):
        return str(value)
    if isinstance(value, Length):
        return format_length(value)
    if isinstance(value, LineHeight):
        if value.mode == "percent":
            return f"{decimal_to_str(value.value)}%"
        text = format_length(value.value)
        return f"at_least {text}" if value.mode == "at_least" else text
    if isinstance(value, Border):
        return "none" if value.width is None else f"{format_length(value.width)} {value.type} {value.color}"
    if isinstance(value, dict):
        return {str(k): _json(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json(v) for v in value]
    from primula.core.values import Record

    if isinstance(value, Record):
        # A column of ``cols`` (decision 120): its width alone, or its fields.
        fields = {str(k): _json(v) for k, v in value.fields.items()}
        return fields["width"] if set(fields) == {"width"} else fields
    return str(value)


# ----------------------------------------------------------------------
# Structure (Т1)
# ----------------------------------------------------------------------

def _structure(evaluation: Any) -> dict[str, Any] | None:
    from primula.syntax import nodes as N

    structure = getattr(evaluation, "structure", None) if evaluation is not None else None
    if structure is None:
        return None
    ids = {target.bookmark: target_id for target_id, target in structure.targets.items()
           if target.bookmark is not None}
    items: list[dict[str, Any]] = []

    def plain(nodes: Any) -> str:
        from primula.structure.tree import plain_text

        return " ".join(plain_text(nodes or []).split())

    track_of: list[str | None] = [None]  # the track block being walked (7.7)
    seen_parallel: set[int] = set()

    def item(kind: str, node: Any, part: str | None, **values: Any) -> None:
        if track_of[-1] is not None and "track" not in values:
            values = {**values, "track": track_of[-1]}
        items.append({"kind": kind, **values, **_position(node.span), "part": part})

    def raw_id(node: Any) -> Any:
        args = getattr(node, "args", None)
        getter = getattr(args, "get", None)
        return getter("id") if getter is not None else None

    def walk(nodes: list[Any], part: str | None) -> None:
        for node in nodes:
            struct = getattr(node, "struct", None)
            if isinstance(node, N.Heading):
                item("heading", node, part, level=node.level, number=getattr(struct, "number", None),
                     title=plain(node.body), id=ids.get(getattr(struct, "bookmark", None)))
            elif isinstance(node, N.Clause):
                text = plain(node.body)
                if not text:
                    # Environment form (``|>:`` … ``|end>``): the number goes to the first
                    # paragraph of the environment, so its text is the clause text.
                    first = next((child for child in node.children if isinstance(child, N.Paragraph)), None)
                    text = plain(first.body) if first is not None else ""
                if len(text) > _TEXT_LIMIT:
                    text = text[:_TEXT_LIMIT - 1].rstrip() + "…"
                item("clause", node, part, level=node.level, number=getattr(struct, "number", None),
                     text=text, id=ids.get(getattr(struct, "bookmark", None)))
            elif isinstance(node, N.Command) and getattr(node, "appendix_info", None) is not None:
                info = node.appendix_info
                item("appendix", node, part, outline=info.outline, designation=info.designation,
                     title=info.title, id=ids.get(info.bookmark))
            elif isinstance(node, N.Command) and getattr(node, "parallel", None) is not None:
                # |parallel (7.7): the environment once, its segments and track blocks.
                spec = node.parallel
                if id(spec) not in seen_parallel:
                    seen_parallel.add(id(spec))
                    item("parallel", node, part, id=spec.id, primary=spec.primary, parity=spec.parity,
                         tracks=[{key: track.fields[key] for key in
                                  ("id", "lang", "title", "role", "primary", "numbered", "optional")}
                                 for track in spec.tracks])
                for row in node.children:
                    segment = getattr(row, "segment", None)
                    if segment is None:
                        continue
                    item("segment", segment, part, id=segment.id, span="all" if segment.full else None,
                         status=segment.status)
                    for cell in row.children:
                        track = getattr(cell, "track", None)
                        track_id = track.fields["id"] if track is not None else None
                        if track_id is not None and track_id in segment.track_spans:
                            args = segment.track_args.get(track_id)
                            item("track_block", cell, part, track=track_id, segment=segment.id,
                                 status=getattr(args, "status", None), rev=getattr(args, "rev", None),
                                 stale=bool(segment.stale.get(track_id)),
                                 changed=bool(segment.changed.get(track_id)))
                        track_of.append(track_id)
                        walk(cell.children, part)
                        track_of.pop()
                continue
            elif isinstance(node, N.Command) and node.name in ("table", "figure"):
                caption = getattr(node, "caption_info", None)
                target_id = ids.get(caption.bookmark) if caption is not None else None
                if target_id is None and raw_id(node) is not None:
                    target_id = next((i for i, t in structure.targets.items()
                                      if t.span is not None and t.kind == node.name
                                      and t.span.source is node.span.source
                                      and node.span.start <= t.span.start < node.span.end), None)
                if caption is not None or target_id is not None:
                    item(node.name, node, part, number=getattr(caption, "number", None),
                         title=plain(caption.title) if caption is not None else None, id=target_id)
            elif isinstance(node, N.ListBlock):
                info = getattr(node, "list_info", None)
                first = node.items[0] if node.items else None
                if info is not None and info.xml_id is not None and first is not None:
                    item("list", node, part, id=raw_id(first))
            elif isinstance(node, N.Admonition) or (isinstance(node, N.Command) and node.name == "section"):
                bookmark = getattr(struct, "bookmark", None)
                if bookmark in ids:
                    item("admonition" if isinstance(node, N.Admonition) else "section", node, part,
                         id=ids[bookmark])
            inner = part
            if isinstance(node, N.Command) and node.name == "document":
                inner = _part_scope(node) or part
            for name in ("children", "items"):
                nested = getattr(node, name, None)
                if isinstance(nested, list):
                    walk(nested, inner)
            if isinstance(node, N.IfBlock):
                for branch in node.branches:
                    walk(branch.children, inner)

    walk(evaluation.document.children, None)
    includes = []
    for entry in getattr(evaluation, "inclusions", []) or []:
        includes.append({"kind": entry["kind"], **_position(entry["span"]),
                         "target": str(entry["path"].resolve()),
                         **{key: entry[key] for key in ("ns", "part", "scope") if key in entry}})
    return {"items": items, "includes": includes}


def _part_scope(node: Any) -> str | None:
    """The ``scope`` of an evaluated ``|document`` node (10.7)."""
    args = getattr(node, "args", None)
    getter = getattr(args, "get", None)
    value = getter("scope") if getter is not None else None
    return value if isinstance(value, str) else None


# ----------------------------------------------------------------------
# Styles (Т2)
# ----------------------------------------------------------------------

def _styles(system: Any) -> dict[str, Any]:
    layers = list(getattr(system, "layers", []) or [])
    styles = []
    for name in sorted(system.styles):
        merged = system.styles[name]
        definitions: list[dict[str, Any]] = []
        own: dict[str, dict[str, Any]] = {}
        for layer in layers:
            definition = layer.styles.get(name)
            if definition is None:
                continue
            where = {"layer": layer.name, "origin": layer.origin, **_position(definition.span)}
            definitions.append({**where, "replace": definition.replace})
            if definition.replace:
                own = {}
            for key, value in definition.props.items():
                own[key] = {"value": None, **where}
            if definition.parent is not None:
                own["parent"] = {"value": definition.parent, **where}
        materialized = merged.layer == -1
        if materialized:
            where = {"layer": None, "origin": "materialized", **_position(merged.span)}
            own = {key: {"value": None, **where} for key in merged.props}
        # Values: the merged ones (a layer may change only a part of a nested property).
        for key, entry in own.items():
            entry["value"] = _json(merged.parent if key == "parent" else merged.props.get(key))
        chain = _chain(system, name)
        effective: dict[str, Any] = {}
        for key, value in system.effective(name).items():
            source = next((style for style in chain if key in system.styles[style].props), name)
            effective[key] = {"value": _json(value), "from": source}
        styles.append({"name": name, "kind": merged.kind, "parent": merged.parent,
                       "materialized": materialized, "broken": name in system.broken,
                       "definitions": definitions, "own": own, "effective": effective,
                       "chain": chain})
    return {"layers": [{"name": layer.name, "origin": layer.origin} for layer in layers],
            "modules": list(system.modules), "defaults": _json(system.defaults), "styles": styles}


def _chain(system: Any, name: str) -> list[str]:
    """The style and its ancestors, nearest first (stops at a missing parent or a cycle)."""
    chain: list[str] = []
    current: str | None = name
    while current is not None and current in system.styles and current not in chain:
        chain.append(current)
        current = system.styles[current].parent
    return chain
