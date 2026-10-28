"""Functions of styles code and loading of YAML style groups (11.1-11.5, 5.1).

Style definition functions (11.2): ``paragraph_style``, ``character_style``,
``block_style``, ``table_style``, ``list_style``, ``frame_style``,
``page_style`` — ``name`` first, then ``parent=…`` and properties.

Parametric styles: ``derive(base, name=None, **props)`` reserves and
returns the deterministic style name (a string; decisions 59, 111, 114).

Settings: ``structure_styles`` (11.5), ``structure_profile`` (5.1),
``numbering``, ``captions``, ``appendices``, ``ref_labels``, ``footnotes``
(5.1-5.10; decisions 69-73, 76),
``abbreviations`` (9.4), ``typography`` (13.7), ``admonition_symbols``
(9.1), ``watermark`` (8.6), ``header``/``footer`` (7.6, decision 19).
They are stored in the registry (checked keys); structure settings are
interpreted by :mod:`primula.structure.settings` (13.6), the others by
later stages (13.7-13.10).  ``captions``, ``appendices`` and ``ref_labels``
take a language as the first argument (decision 73); without it
``captions``/``appendices`` apply to every language (key ``"*"``).

Definitions are allowed where :attr:`StyleRegistry.current` is set — the
evaluator sets it for styles modules, the project and the document, and
clears it while an ``|import`` module loads (decision 59; P3114).
"""

from __future__ import annotations

from typing import Any, Callable

from primula.core.errors import core_error, resolve
from primula.core.values import Builtin, Content, PDict, Record
from primula.diagnostics import warning
from primula.header import Header
from primula.styles.system import StyleRegistry

#: Keys of ``structure_styles`` and ``|set`` (11.5, 4.5).
#: ``caption`` … ``reference`` — styles of structure constructs (decision 70).
STRUCTURE_KEYS = ("paragraph", "heading", "clause", "list", "numbered_list", "table", "figure", "admonition",
                  "page", "strong", "emphasis", "underline", "superscript", "subscript", "code", "strike",
                  "placeholder", "caption", "footnote", "endnote", "note_anchor", "appendix", "toc", "list_of",
                  "reference", "link", "clause_number", "heading_number", "parallel_table", "parallel_header")
#: Structure profiles (5.1).
PROFILES = ("business", "report")

_SETTINGS: dict[str, tuple[str, ...] | None] = {
    "numbering": ("headings", "heading_format", "clause_format", "figures", "tables", "ref_format"),
    "footnotes": ("numbering", "restart", "format", "separator"),
    "abbreviations": ("first", "sort"),
    "typography": ("percent_space", "nbsp_short", "nbsp_words"),
    "admonition_symbols": ("danger", "warning", "caution", "notice", "note", "tip"),
}
_KIND_FUNCTIONS = {
    "paragraph_style": "paragraph", "character_style": "character", "block_style": "block",
    "table_style": "table", "list_style": "list", "frame_style": "frame", "page_style": "page",
}


def _plain(value: Any) -> Any:
    """Records and frozen dictionaries as plain dictionaries."""
    if isinstance(value, Record):
        return {k: _plain(v) for k, v in value.fields.items()}
    if isinstance(value, (dict, PDict)):
        return {k: _plain(v) for k, v in value.items()}
    return value


def make_style_builtins(registry: StyleRegistry) -> dict[str, Builtin]:
    """Built-in functions of styles code bound to a registry."""

    def definer(kind: str) -> Callable[..., None]:
        def impl(interp: Any, args: list[Any], kwargs: dict[str, Any], span: Any) -> None:
            if len(args) != 1:
                raise core_error("P2321", span, function=f"{kind}_style",
                                 problem="takes the style name as the only positional argument")
            registry.define(kind, args[0], {k: _plain(v) for k, v in kwargs.items()}, resolve(span))
        return impl

    def derive(interp: Any, args: list[Any], kwargs: dict[str, Any], span: Any) -> str:
        if len(args) != 1 or not isinstance(args[0], str):
            raise core_error("P2321", span, function="derive", problem="takes the base style name as the first argument")
        name = kwargs.pop("name", None)
        properties = {k: _plain(v) for k, v in kwargs.items()}
        return registry.reserve(args[0], name, properties, resolve(span))

    def structure_styles(interp: Any, args: list[Any], kwargs: dict[str, Any], span: Any) -> None:
        if args:
            raise core_error("P2321", span, function="structure_styles", problem="takes only keyword arguments")
        for key in kwargs:
            if key not in STRUCTURE_KEYS:
                raise core_error("P3115", span, key=key)
        registry.set_setting("structure_styles", {k: _plain(v) for k, v in kwargs.items()}, resolve(span))

    def structure_profile(interp: Any, args: list[Any], kwargs: dict[str, Any], span: Any) -> None:
        if len(args) != 1 or kwargs or args[0] not in PROFILES:
            raise core_error("P3120", span, name=str(args[0]) if args else "")
        registry.set_value("profile", args[0], resolve(span))

    def placeholders(interp: Any, args: list[Any], kwargs: dict[str, Any], span: Any) -> None:
        """``placeholders("mark" | "final")`` (4.2, decision 123): ``final`` prints ``|?{…}`` as plain text."""
        if len(args) != 1 or kwargs or args[0] not in ("mark", "final"):
            raise core_error("P2321", span, function="placeholders", problem="takes \"mark\" or \"final\"")
        registry.set_value("placeholders", args[0], resolve(span))

    def setting(name: str, keys: tuple[str, ...] | None) -> Callable[..., None]:
        def impl(interp: Any, args: list[Any], kwargs: dict[str, Any], span: Any) -> None:
            if args:
                raise core_error("P2321", span, function=name, problem="takes only keyword arguments")
            for key in kwargs:
                if keys is not None and key not in keys:
                    raise core_error("P2321", span, function=name, problem=f"got an unexpected keyword argument '{key}'")
            registry.set_setting(name, {k: _plain(v) for k, v in kwargs.items()}, resolve(span))
        return impl

    def ref_labels(interp: Any, args: list[Any], kwargs: dict[str, Any], span: Any) -> None:
        if len(args) != 1 or not isinstance(args[0], str):
            raise core_error("P2321", span, function="ref_labels", problem="takes the language as the first argument")
        registry.set_setting("ref_labels", {args[0]: {k: _plain(v) for k, v in kwargs.items()}}, resolve(span))

    def by_language(name: str, keys: tuple[str, ...]) -> Callable[..., None]:
        """``captions``/``appendices``: an optional language, then keyword settings (decision 73)."""
        def impl(interp: Any, args: list[Any], kwargs: dict[str, Any], span: Any) -> None:
            if len(args) > 1 or (args and not isinstance(args[0], str)):
                raise core_error("P2321", span, function=name,
                                 problem="takes an optional language and keyword arguments")
            for key in kwargs:
                if key not in keys:
                    raise core_error("P2321", span, function=name, problem=f"got an unexpected keyword argument '{key}'")
            language = args[0] if args else "*"
            registry.set_setting(name, {language: {k: _plain(v) for k, v in kwargs.items()}}, resolve(span))
        return impl

    def quotes(interp: Any, args: list[Any], kwargs: dict[str, Any], span: Any) -> None:
        """``quotes("de", ("„", "“"), ("‚", "‘"))`` — quotes of a language (decision 63)."""
        pairs = [tuple(pair) if isinstance(pair, (tuple, list)) else None for pair in args[1:]]
        if len(args) != 3 or kwargs or not isinstance(args[0], str) or any(
                p is None or len(p) != 2 or not all(isinstance(c, str) for c in p) for p in pairs):
            raise core_error("P2321", span, function="quotes",
                             problem="takes a language and two pairs: quotes(\"de\", (\"„\", \"“\"), (\"‚\", \"‘\"))")
        registry.set_setting("quotes", {args[0]: (pairs[0], pairs[1])}, resolve(span))

    def watermark(interp: Any, args: list[Any], kwargs: dict[str, Any], span: Any) -> None:
        if len(args) != 1:
            raise core_error("P2321", span, function="watermark", problem="takes the mark as the first argument")
        registry.set_setting("watermark", {"mark": args[0], **kwargs}, resolve(span))

    def page_part(which_name: str) -> Callable[..., None]:
        def impl(interp: Any, args: list[Any], kwargs: dict[str, Any], span: Any) -> None:
            if len(args) != 2 or not isinstance(args[0], str) or not isinstance(args[1], (Content, str)):
                raise core_error("P2321", span, function=which_name,
                                 problem="takes a page style name and content (markup(…))")
            which = kwargs.get("which", "all")
            registry.set_setting(which_name, {(args[0], which): args[1]}, resolve(span))
        return impl

    def dictionary(name: str, keys: tuple[str, ...], lang_first: bool) -> Callable[..., None]:
        """``currency(code, lang, …)``, ``unit(code, lang, …)``, ``month_names(lang, …)`` (library 1).

        The fields are merged by layers: a call for a known code overrides
        only the given fields of that language.
        """
        def impl(interp: Any, args: list[Any], kwargs: dict[str, Any], span: Any) -> None:
            count = 1 if lang_first else 2
            if len(args) != count or not all(isinstance(a, str) for a in args):
                usage = f"{name}(lang, …)" if lang_first else f"{name}(code, lang, …)"
                raise core_error("P2321", span, function=name, problem=f"takes positional arguments {usage}")
            for key in kwargs:
                if key not in keys:
                    raise core_error("P2321", span, function=name, problem=f"got an unexpected keyword argument '{key}'")
            fields = {k: _plain(v) for k, v in kwargs.items()}
            if name == "month_names":
                for case, names in fields.items():
                    if not isinstance(names, (list, tuple)) or len(names) != 12 or not all(
                            isinstance(n, str) for n in names):
                        raise core_error("P2321", span, function=name, problem=f"'{case}' needs a list of 12 names")
                registry.set_setting(name, {args[0]: fields}, resolve(span))
            else:
                registry.set_setting(name, {args[0]: {args[1]: fields}}, resolve(span))
        return impl

    functions: dict[str, Callable[..., Any]] = {name: definer(kind) for name, kind in _KIND_FUNCTIONS.items()}
    functions.update({
        "currency": dictionary("currency", ("short", "units", "frac", "gender", "minor", "minor_gender",
                                            "minor_digits"), False),
        "unit": dictionary("unit", ("symbol", "quantity", "factor", "offset"), False),
        "month_names": dictionary("month_names", ("nom", "gen", "loc"), True),
    })
    functions.update({
        "derive": derive, "structure_styles": structure_styles, "structure_profile": structure_profile,
        "ref_labels": ref_labels, "watermark": watermark, "quotes": quotes,
        "captions": by_language("captions", ("figure", "table")),
        "appendices": by_language("appendices", ("designation", "numbering", "letters", "page_break", "toc", "title_format")),
        # Technical documentation (9.1, 9.2; decision 116); "notes" — the heading of a group of notes.
        "admonition_words": by_language("admonition_words",
                                        ("danger", "warning", "caution", "notice", "note", "tip", "notes")),
        "review_marks": by_language("review_marks", ("true", "false", "watermark")),
        "header": page_part("header"), "footer": page_part("footer"),
        "placeholders": placeholders,
    })
    functions.update({name: setting(name, keys) for name, keys in _SETTINGS.items()})
    return {name: Builtin(name, impl) for name, impl in functions.items()}


def load_yaml_groups(registry: StyleRegistry, header: Header, report: Callable[[Exception], None]) -> None:
    """Define the styles of the YAML header of a styles module (11.1-11.2)."""
    from primula.styles.schema import KINDS

    data = header.data
    defaults = data.get("defaults")
    if isinstance(defaults, dict):
        try:
            registry.set_defaults(defaults, header.value_span(("defaults",), key=True),
                                  lambda key: header.value_span(("defaults", key)))
        except Exception as exc:  # noqa: BLE001 - CoreError reported by the caller
            report(exc)
    for group, kind in KINDS.items():
        styles = data.get(group)
        if not isinstance(styles, dict):
            continue
        for name, props in styles.items():
            span = header.value_span((group, name), key=True)
            if not isinstance(props, dict):
                props = {} if props is None else {"?": props}
            try:
                registry.define(kind, name, props, span,
                                lambda key, g=group, n=name: header.value_span((g, n, key)))
            except Exception as exc:  # noqa: BLE001
                report(exc)
