"""Style registry and the resolved style system (specification 11, decisions 55-61).

:class:`StyleRegistry` collects definitions layer by layer while styles
modules, the project (13.11) and the document are evaluated:

* every styles module is one layer, in the order of the ``styles`` lists
  (project first, then the document header key ``styles``, decision 55);
* the document and its fragments form the last layer (11.7, decision 59);
* defining a style twice in one layer is an error (P3103), also when the
  calls stand in different fragments;
* settings (``structure_styles``, ``numbering``…) are merged key by key.

:meth:`StyleRegistry.finalize` merges the layers into a
:class:`StyleSystem` (11.7: dictionaries are merged, scalars and lists
replaced), checks parents (existence, kind, cycles) and the shared name
space of paragraph and character styles.  The system then materialises
variants on demand: parameters ``before``/``after``/``indent`` (11.4),
``derive(…)`` names and list variants, with deterministic names
(decisions 56, 103).

A style is a string with its name (decision 111).  ``derive(…)`` reserves
the deterministic name at the call (:meth:`StyleRegistry.reserve`, a
conflict with other properties is an error at once); the style itself is
written to the ODT at its first use (:meth:`StyleSystem.ensure`,
decision 114).  The reservations are shared by the registry and the
system, because ``derive`` may also run after the layers are merged.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from decimal import Decimal
from fractions import Fraction
from typing import Any, Callable

from primula.core.errors import CoreError, core_error
from primula.core.values import Length, format_length
from primula.diagnostics import DiagnosticSink, error
from primula.source import Span
from primula.styles.schema import Border, LineHeight, PropertyError, check_property
from primula.unicode import is_identifier, is_xid_continue, nfkc

#: Longest readable materialised name (decision 103); longer names are hashed.
MAX_NAME = 128


def valid_style_name(name: Any) -> bool:
    """A style name: a Unicode identifier with hyphens (3.3, 3.9, 11.2)."""
    return isinstance(name, str) and is_identifier(name, "-")


@dataclass
class Reservation:
    """A name reserved by ``derive(…)`` (11.4): base, raw properties, position."""

    base: str
    props: dict[str, Any]
    span: Span | None


@dataclass(eq=False)
class StyleDef:
    """One definition of a style in one layer.

    Attributes:
        kind: ``paragraph``, ``character``, ``block``, ``table``, ``list``,
            ``frame`` or ``page``.
        name: style name.
        props: own normalised properties (without ``parent``).
        parent: name of the parent style, if any.
        span: position of the definition.
        layer: index of the layer.
    """

    kind: str
    name: str
    props: dict[str, Any]
    parent: str | None
    span: Span | None
    layer: int
    #: ``replace: true`` — the definition replaces the one of lower layers
    #: instead of being merged into it (11.7, decision 120).
    replace: bool = False


@dataclass
class Layer:
    """A layer of style definitions (a styles module or the document).

    ``origin``: where the layer comes from (11.7) — ``project``, ``option``
    (``--style``), ``header`` (``styles`` of the document header),
    ``default`` (``std/styles/default`` by default) or ``document``.
    """

    name: str
    styles: dict[str, StyleDef] = field(default_factory=dict)
    origin: str = "document"


def merge_props(base: dict[str, Any], update: dict[str, Any]) -> dict[str, Any]:
    """Merge properties: dictionaries merged recursively, other values replaced (11.7)."""
    result = dict(base)
    for key, value in update.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = merge_props(result[key], value)
        else:
            result[key] = value
    return result


class StyleRegistry:
    """Collects style definitions and settings by layers.

    Attributes:
        layers: the layers in order.
        current: index of the layer that receives definitions, or ``None``
            where definitions are not allowed (top level of an ``|import``
            module, decision 59).
        settings: merged settings (``structure_styles``, ``profile``…).
        defaults: merged ``defaults`` (font, size, language).
    """

    def __init__(self) -> None:
        self.layers: list[Layer] = []
        self.current: int | None = None
        self.settings: dict[str, Any] = {}
        self.setting_spans: dict[str, Span | None] = {}
        self.defaults: dict[str, Any] = {}
        self.modules: list[str] = []
        #: Identical definitions from different files are allowed (parts, 10.7).
        self.allow_identical = False
        #: Names reserved by ``derive(…)`` (shared with the system).
        self.reserved: dict[str, Reservation] = {}

    def reserve(self, base: Any, name: Any, props: dict[str, Any], span: Span | None) -> str:
        """``derive(base, name=None, **props)``: reserve and return the style name (11.4).

        Without ``name`` the name is ``Base-<property>-<value>…`` with the
        properties in alphabetical order (decision 103).  The same name with
        other properties is an error (P3111) with a hint to give ``name=``.
        Nested ``derive(derive(…))`` combines the properties on the same base.

        Raises:
            CoreError: P3110 (invalid name), P3111 (name taken).
        """
        if not valid_style_name(base):
            raise core_error("P3110", span, name=str(base))
        base = nfkc(base)
        earlier = self.reserved.get(base)
        if earlier is not None:
            props = {**earlier.props, **props}
            base = earlier.base
        if name is not None:
            if not valid_style_name(name):
                raise core_error("P3110", span, name=str(name))
            result = nfkc(name)
        else:
            parts: list[str | None] = []
            for key in sorted(props):
                parts += [key, name_part(props[key])]
            result = compose(base, parts, props)
        reservation = Reservation(base, props, span)
        previous = self.reserved.get(result)
        if previous is not None and (previous.base != base or previous.props != props):
            diagnostic = error("P3111", span, name=result).hint("help.derive_name")
            if previous.span is not None:
                diagnostic.note("note.first_definition", previous.span)
            raise CoreError(diagnostic)
        self.reserved.setdefault(result, reservation)
        return result

    def begin_layer(self, name: str, origin: str = "document") -> int:
        """Start a new layer; it becomes current."""
        self.layers.append(Layer(name, origin=origin))
        self.current = len(self.layers) - 1
        return self.current

    def _layer(self, span: Span | None) -> Layer:
        if self.current is None:
            raise core_error("P3114", span)
        return self.layers[self.current]

    def define(self, kind: str, name: Any, props: dict[str, Any], span: Span | None,
               value_span: Callable[[str], Span | None] | None = None) -> StyleDef:
        """Define a style in the current layer.

        Args:
            kind: style kind.
            name: style name (checked, P3110).
            props: raw properties (``parent`` included).
            span: position of the definition.
            value_span: position of a property value (YAML), for errors.

        Raises:
            CoreError: P3101-P3103, P3110, P3114.
        """
        layer = self._layer(span)
        if not valid_style_name(name):
            raise core_error("P3110", span, name=str(name))
        name = nfkc(name)
        props = dict(props)
        replace = props.pop("replace", False)
        if not isinstance(replace, bool):
            raise core_error("P3102", (value_span("replace") if value_span else None) or span, prop="replace",
                             expected="true or false")
        checked: dict[str, Any] = {}
        for key, value in props.items():
            where = (value_span(key) if value_span else None) or span
            try:
                checked[key] = check_property(kind, key, value)
            except PropertyError as exc:
                if exc.kind == "unknown":
                    raise core_error("P3101", where, prop=key, kind=kind, name=name) from None
                raise core_error("P3102", where, prop=key, expected=exc.problem) from None
        existing = layer.styles.get(name)
        if existing is not None and self.allow_identical and existing.kind == kind and \
                existing.props == {k: v for k, v in checked.items() if k != "parent"} and \
                existing.parent == checked.get("parent") and existing.span is not None and span is not None and \
                existing.span.source is not span.source:
            # Parts of a compound document may repeat a definition (10.7, decision 117).
            return existing
        if existing is not None:
            diagnostic = error("P3103", span, name=name)
            if existing.span is not None:
                diagnostic.note("note.first_definition", existing.span)
            raise CoreError(diagnostic)
        parent = checked.pop("parent", None)
        definition = StyleDef(kind, name, checked, parent, span, self.current, replace)  # type: ignore[arg-type]
        layer.styles[name] = definition
        return definition

    def set_setting(self, key: str, values: dict[str, Any], span: Span | None) -> None:
        """Merge a settings group (``structure_styles``, ``numbering``…)."""
        self._layer(span)
        current = self.settings.get(key, {})
        self.settings[key] = merge_props(current, values) if isinstance(current, dict) else values
        self.setting_spans[key] = span

    def set_value(self, key: str, value: Any, span: Span | None) -> None:
        """Set a scalar setting (``profile``)."""
        self._layer(span)
        self.settings[key] = value
        self.setting_spans[key] = span

    def set_defaults(self, values: dict[str, Any], span: Span | None,
                     value_span: Callable[[str], Span | None] | None = None) -> None:
        """Merge ``defaults`` (character properties of the document)."""
        for key, value in values.items():
            where = (value_span(key) if value_span else None) or span
            try:
                self.defaults[key] = check_property("character", key, value)
            except PropertyError as exc:
                if exc.kind == "unknown":
                    raise core_error("P3101", where, prop=key, kind="defaults", name="defaults") from None
                raise core_error("P3102", where, prop=key, expected=exc.problem) from None

    def finalize(self, sink: DiagnosticSink) -> "StyleSystem":
        """Merge the layers into a :class:`StyleSystem` and check it."""
        merged: dict[str, StyleDef] = {}
        for layer in self.layers:
            for name, definition in layer.styles.items():
                previous = merged.get(name)
                if previous is None or definition.replace and previous.kind == definition.kind:
                    merged[name] = StyleDef(definition.kind, name, dict(definition.props),
                                            definition.parent, definition.span, definition.layer)
                    continue
                if previous.kind != definition.kind:
                    code = "P3104" if {previous.kind, definition.kind} == {"paragraph", "character"} else "P3106"
                    diagnostic = error(code, definition.span, name=name, parent=name,
                                       kind=definition.kind, expected=previous.kind)
                    if previous.span is not None:
                        diagnostic.note("note.first_definition", previous.span)
                    sink.emit(diagnostic)
                    continue
                previous.props = merge_props(previous.props, definition.props)
                if definition.parent is not None:
                    previous.parent = definition.parent
                previous.span = definition.span
        system = StyleSystem(merged, dict(self.settings), dict(self.defaults), list(self.modules),
                             self.reserved)
        # The layers stay for the provenance of properties (``check --dump-styles``).
        system.layers = self.layers
        system.check(sink)
        return system


class StyleSystem:
    """Merged styles with inheritance and materialisation.

    Attributes:
        styles: name -> merged definition.
        settings: merged settings.
        defaults: document defaults.
        modules: names of the styles modules applied (for the report).
        materialized: names of styles created by materialisation, in order.
    """

    def __init__(self, styles: dict[str, StyleDef], settings: dict[str, Any], defaults: dict[str, Any],
                 modules: list[str], reserved: dict[str, Reservation] | None = None) -> None:
        self.styles = styles
        self.reserved = reserved if reserved is not None else {}
        #: Reserved names already materialised (or found in conflict).
        self._ensured: set[str] = set()
        self.settings = settings
        self.defaults = defaults
        self.modules = modules
        self.materialized: list[str] = []
        #: Layers of the registry (set by :meth:`StyleRegistry.finalize`).
        self.layers: list[Layer] = []
        self._effective: dict[str, dict[str, Any]] = {}
        self.broken: set[str] = set()

    # ------------------------------------------------------------------
    # Checks and inheritance
    # ------------------------------------------------------------------

    def check(self, sink: DiagnosticSink) -> None:
        """Parents exist, have the same kind, and form no cycles (P3105-P3107)."""
        for name, definition in self.styles.items():
            parent = definition.parent
            if parent is None:
                continue
            target = self.styles.get(parent)
            if target is None:
                sink.emit(error("P3105", definition.span, parent=parent, name=name))
                self.broken.add(name)
            elif target.kind != definition.kind:
                sink.emit(error("P3106", definition.span, parent=parent, name=name, kind=target.kind,
                                expected=definition.kind))
                self.broken.add(name)
        for name in self.styles:
            chain: list[str] = []
            current: str | None = name
            while current is not None and current in self.styles:
                if current in chain:
                    if current == name:
                        sink.emit(error("P3107", self.styles[name].span, chain=" -> ".join(chain + [current])))
                        self.broken.add(name)
                    break
                chain.append(current)
                current = self.styles[current].parent

    def ensure(self, name: str, span: Span | None) -> None:
        """Materialise a name reserved by ``derive(…)`` at its first use (11.4).

        Raises:
            CoreError: unknown base (P3108), invalid properties (P3101,
                P3102), name taken by other properties (P3111).
        """
        if name not in self.reserved or name in self._ensured:
            return
        self._ensured.add(name)
        reservation = self.reserved[name]
        base = reservation.base
        if base not in self.styles:
            self.ensure(base, span)
        if base not in self.styles:
            raise core_error("P3108", span, name=base)
        kind = self.styles[base].kind
        props: dict[str, Any] = {}
        for key, raw in reservation.props.items():
            try:
                props[key] = check_property(kind, key, raw)
            except PropertyError as exc:
                if exc.kind == "unknown":
                    raise core_error("P3101", span, prop=key, kind=kind, name=base) from None
                raise core_error("P3102", span, prop=key, expected=exc.problem) from None
        self.register(kind, name, base, props, span)

    def kind(self, name: str) -> str | None:
        """Kind of a style, or ``None`` if it does not exist."""
        definition = self.styles.get(name)
        return definition.kind if definition else None

    def effective(self, name: str) -> dict[str, Any]:
        """Properties of a style with its parent chain (own ones override)."""
        cached = self._effective.get(name)
        if cached is not None:
            return cached
        chain: list[StyleDef] = []
        current: str | None = name
        seen: set[str] = set()
        while current is not None and current in self.styles and current not in seen:
            seen.add(current)
            chain.append(self.styles[current])
            current = self.styles[current].parent
        props: dict[str, Any] = {}
        for definition in reversed(chain):
            props = merge_props(props, definition.props)
        self._effective[name] = props
        return props

    # ------------------------------------------------------------------
    # Materialisation (11.4, decision 56)
    # ------------------------------------------------------------------

    def register(self, kind: str, name: str, parent: str, props: dict[str, Any], span: Span | None) -> str:
        """Add a materialised style; P3111 if the name is taken by other properties."""
        existing = self.styles.get(name)
        if existing is not None:
            if existing.kind == kind and existing.parent == parent and existing.props == props:
                return name
            raise CoreError(error("P3111", span, name=name).hint("help.derive_name"))
        self.styles[name] = StyleDef(kind, name, props, parent, span, -1)
        self.materialized.append(name)
        return name

    def variant(self, base: str, params: dict[str, Any], scale: Callable[..., Any], span: Span | None) -> str:
        """Paragraph style with parameters ``before``/``after``/``indent`` (11.4)."""
        props: dict[str, Any] = {}
        parts: list[str] = []
        for key in ("before", "after", "indent"):
            if key not in params:
                continue
            value = params[key]
            parts += [key, name_part(value)]
            if key == "indent":
                props["left"] = scale("indent", value, span)
            else:
                props["space_before" if key == "before" else "space_after"] = scale("spacing", value, span)
        name = compose(base, parts, props)
        return self.register("paragraph", name, base, props, span)

    def list_variant(self, base: str, levels: dict[int, str], span: Span | None) -> str:
        """List style with level types changed (5.4): ``List-l2b-l3n`` (decision 56)."""
        suffix = "-".join(f"l{level}{'b' if kind == 'bullet' else 'n'}" for level, kind in sorted(levels.items()))
        props = {"levels": {level: {"type": kind} for level, kind in levels.items()}}
        return self.register("list", f"{base}-{suffix}", base, props, span)


def name_part(value: Any) -> str | None:
    """A value written into a style name (11.4, decision 103).

    ``True``/``False`` -> ``on``/``off``; ``#C00000`` -> ``C00000``; a length
    in its unit; a minus sign -> ``m``; a point -> ``_``; any character
    other than a Unicode letter or digit, ``_`` and ``-`` -> ``_``
    (``Times New Roman`` -> ``Times_New_Roman``).  ``None`` for values that
    have no text form (mappings, lists): the name is then hashed.
    """
    if isinstance(value, bool):
        text = "on" if value else "off"
    elif isinstance(value, Length):
        text = format_length(value)
    elif isinstance(value, (int, Decimal)):
        text = str(value)
    elif isinstance(value, str):
        text = value[1:] if value.startswith("#") else value
    else:
        return None
    if text.startswith("-"):
        text = "m" + text[1:]
    text = "".join(char if char == "-" or is_xid_continue(char) else "_" for char in text)
    return text or None


def _canonical(value: Any) -> Any:
    """JSON-compatible canonical form of a property value (for hashes)."""
    if isinstance(value, Length):
        return ["length", str(value.value), value.unit]
    if isinstance(value, (Decimal, Fraction)):
        return str(value)
    if isinstance(value, Border):
        return ["border", _canonical(value.width), value.type, value.color]
    if isinstance(value, LineHeight):
        return ["line_height", value.mode, _canonical(value.value)]
    if isinstance(value, dict):
        return {str(k): _canonical(v) for k, v in sorted(value.items(), key=lambda kv: str(kv[0]))}
    if isinstance(value, (list, tuple)):
        return [_canonical(v) for v in value]
    return value


def compose(base: str, parts: list[str | None], props: dict[str, Any]) -> str:
    """``Base-part-part…``, or ``Base-x<hash>`` beyond 128 characters (decision 103)."""
    name = "-".join([base, *[part or "" for part in parts]])
    if all(part for part in parts) and len(name) <= MAX_NAME:
        return name
    digest = hashlib.sha256(json.dumps(_canonical(props), sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    return f"{base}-x{digest[:8]}"

