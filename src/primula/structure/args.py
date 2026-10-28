"""Arguments of structure commands (specification 5.2-5.10, 7.5, 9.1).

The parser accepts any Python call arguments; the meaning of the
arguments of structure constructs is checked here: unknown keyword
arguments (P4104) and value types (P4105).  Arguments of tables, figures
and admonitions that belong to later stages are not checked here, only
the ones the structure phase reads (``id``, ``caption``).
"""

from __future__ import annotations

from typing import Any, Callable

from primula.diagnostics import DiagnosticSink, error
from primula.i18n import Key
from primula.unicode import is_identifier, nfkc

def valid_id(value: str) -> bool:
    """ID format (5.6, 3.9): a Unicode identifier with ``-`` and ``.`` after the first character."""
    return is_identifier(value, "-.")


def _is_str(value: Any) -> bool:
    return isinstance(value, str)


def _is_bool(value: Any) -> bool:
    return isinstance(value, bool)


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _is_str_or_none(value: Any) -> bool:
    return value is None or isinstance(value, str)


#: Type checks: name -> (check, expected-type message key).
_TYPES: dict[str, tuple[Callable[[Any], bool], str]] = {
    "id": (_is_str, "type.string"), "number": (_is_bool, "type.boolean"), "level": (_is_int, "type.integer"),
    "toc": (_is_bool, "type.boolean"), "toc_title": (_is_str, "type.string"), "continues": (_is_str, "type.string"),
    "title": (_is_str_or_none, "type.string"), "subtitle": (_is_str_or_none, "type.string"),
    "letter": (_is_str, "type.string"), "prefix": (_is_str, "type.string"),
    "max_level": (_is_int, "type.integer"), "page_break": (_is_bool, "type.boolean"), "start": (_is_int, "type.integer"),
    "case": (_is_str, "type.string"), "caption": (_is_str_or_none, "type.string"),
    "style": (_is_str, "type.string"),
    "toc_level": (_is_int, "type.integer"), "track": (_is_str, "type.string"),
}

#: Allowed keyword arguments of the constructs (``when`` is removed by evaluation).
ALLOWED: dict[str, tuple[str, ...]] = {
    "heading": ("id", "number", "level", "toc", "toc_title", "toc_level", "style"),
    "clause": ("id", "continues", "block", "style", "toc", "toc_title", "toc_level"),
    "appendix": ("id", "title", "subtitle", "number", "letter", "page", "block", "toc", "toc_title", "toc_level"),
    "toc_entry": ("level",),
    "scope": ("prefix",),
    "toc": ("max_level", "title", "page_break", "track"),
    "list_of": ("title", "page_break", "track"),
    "footnote": ("id",),
    "endnote": ("id",),
    "ref": ("case",),
    "list_item": ("id", "start", "continues"),
}


def check_args(args: Any, construct: str, command: str, sink: DiagnosticSink,
               *, types_only: tuple[str, ...] | None = None) -> dict[str, Any]:
    """Check keyword arguments of a construct; return the valid ones.

    Args:
        args: :class:`~primula.evaluate.model.EArgs` or ``None``.
        construct: key of :data:`ALLOWED`.
        command: name for messages (``|<``, ``|appendix``…).
        sink: diagnostics receiver.
        types_only: check only the types of these arguments (constructs
            whose other arguments belong to later stages).

    Returns:
        The keyword arguments with valid values (invalid ones dropped).
    """
    if args is None:
        return {}
    result: dict[str, Any] = {}
    allowed = ALLOWED.get(construct, ())
    span = args.span
    for name, value in args.keywords.items():
        if types_only is not None:
            if name not in types_only:
                continue
        elif name not in allowed:
            sink.emit(error("P4104", _arg_span(args, name) or span, name=name, command=command))
            continue
        check = _TYPES.get(name)
        if name == "number" and construct == "appendix":
            check = (_is_int, "type.integer")
        if check is not None and not check[0](value):
            sink.emit(error("P4105", _arg_span(args, name) or span, name=name, command=command,
                            expected=Key(check[1])))
            continue
        if name == "id" and not valid_id(value):
            sink.emit(error("P4101", _arg_span(args, name) or span, id=value))
            continue
        if name == "id":
            value = nfkc(value)  # IDs compare by NFKC (5.6)
        result[name] = value
    return result


def _arg_span(args: Any, name: str) -> Any:
    """Span of a keyword argument value in the source, if known."""
    source = getattr(args, "source", None)
    if source is None:
        return None
    node = source.keyword(name)
    return source.fragment.span_of(node) if node is not None else None
