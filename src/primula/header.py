"""YAML header of a source file: splitting, reading, structural checks.

Specification sections 2.2-2.3, 10.6, 11.1 and grammar rule ``Header``::

    Header   ::= "---" EOL YamlLine* "---" EOL
    YamlLine ::= ( [^#xA]* - "---" ) EOL

* The header starts at the first line of the file: the line must be exactly
  ``---``; otherwise the file has no header and everything is body.
* The header ends at the next line that is exactly ``---``.  The end of the
  text counts as the end of that line (a file without a final LF).
* Header values are data only (no expressions); they are read by
  :mod:`primula.yamlio` (YAML 1.2 core + Primula rules, decision 25).

Checks done here (stage 13.0):

* the header is a mapping;
* the file kind: the ``kind`` key if present, otherwise the
  sub-extension of the file name (``.f.prml`` fragment, ``.m.prml``
  module, ``.s.prml`` styles, ``.p.prml`` project), otherwise ``document``
  (section 2.2, decision 100); a ``kind`` that contradicts the
  sub-extension is a warning (P7001);
* ``primula.version`` is the implemented language version — any other,
  including ``1.0``, is an error (decision 114); ``primula.stdlib`` is not
  newer than the shipped standard library; the key ``lines`` of version
  1.0 is an error: the line mode was removed (section 3.4, decision 107);
* the top-level keys are known for the file kind, the keys of
  ``doc`` (``doc_defaults`` of a project) are known metadata keys; a key renamed by
  decision 129 (``document``, ``documents``) is an error naming the new one, the keys of ``primula`` are known —
  an unknown key is a *warning* (it may be a typo; it is not used);
* keys whose value must be a mapping or a list have that type.

Semantic checks of values (parameters, styles, project targets) belong to
later stages (13.3, 13.4, 13.11).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from primula import LANGUAGE_VERSION, STDLIB_VERSION
from primula import yamlio
from primula.diagnostics import DiagnosticSink, error, warning
from primula.i18n import Key
from primula.core.values import DateTime
from primula.source import SourceFile, Span

#: File kinds, specification 2.2.
FILE_KINDS: tuple[str, ...] = ("document", "fragment", "module", "styles", "project")

#: Sub-extensions of the file kinds (section 2.2, decision 100).
SUB_EXTENSIONS: dict[str, str] = {".f": "fragment", ".m": "module", ".s": "styles", ".p": "project"}

#: Language versions this translator implements (specification 0.1).
SUPPORTED_VERSIONS: tuple[str, ...] = (LANGUAGE_VERSION,)

#: Known top-level header keys by file kind (specification 2.3, 10.6, 11.1).
HEADER_KEYS: dict[str, frozenset[str]] = {
    "document": frozenset({"kind", "primula", "doc", "params", "structure", "styles", "references"}),
    "fragment": frozenset({"kind", "primula", "params"}),
    "module": frozenset({"kind", "primula"}),
    "styles": frozenset({"kind", "primula", "extends", "defaults", "paragraphs", "characters",
                         "blocks", "tables", "lists", "frames", "pages"}),
    "project": frozenset({"kind", "primula", "name", "language", "styles", "on_conflict",
                          "params", "keys", "limits", "build_date", "targets", "ref_documents", "extends",
                          "doc_defaults"}),
}

#: Keys renamed by decision 129 (kind, old key) -> new key: the old key is an
#: error naming the new one, not a synonym.
RENAMED_KEYS: dict[tuple[str, str], str] = {
    ("document", "document"): "doc",
    ("project", "document"): "doc_defaults",
    ("project", "documents"): "ref_documents",
}

#: Keys of the ``primula`` declaration (specification 2.3).
PRIMULA_KEYS: frozenset[str] = frozenset({"version", "stdlib"})

#: ODT metadata keys of ``doc`` (specification 2.3), also of ``doc_defaults`` of a project.
DOCUMENT_KEYS: frozenset[str] = frozenset({
    "title", "subject", "description", "creator", "organization", "language",
    "identifier", "revision", "status", "created", "modified", "keywords",
})

#: Expected value types of top-level keys: a type, a tuple of types or
#: ``None`` (empty value) where an empty value is allowed.  Mapping keys
#: accept ``None`` (``params:`` with nothing after it means no params).
_KEY_TYPES: dict[str, tuple[tuple[type, ...], str]] = {
    "kind": ((str,), "type.string"),
    "primula": ((dict, type(None)), "type.mapping"),
    "doc": ((dict, type(None)), "type.mapping"),
    "doc_defaults": ((dict, type(None)), "type.mapping"),
    "params": ((dict, type(None)), "type.mapping"),
    "structure": ((dict, type(None)), "type.mapping"),
    "defaults": ((dict, type(None)), "type.mapping"),
    "paragraphs": ((dict, type(None)), "type.mapping"),
    "characters": ((dict, type(None)), "type.mapping"),
    "blocks": ((dict, type(None)), "type.mapping"),
    "tables": ((dict, type(None)), "type.mapping"),
    "lists": ((dict, type(None)), "type.mapping"),
    "frames": ((dict, type(None)), "type.mapping"),
    "pages": ((dict, type(None)), "type.mapping"),
    "keys": ((dict, type(None)), "type.mapping"),
    "limits": ((dict, type(None)), "type.mapping"),
    "targets": ((list, type(None)), "type.sequence"),
    "ref_documents": ((dict, type(None)), "type.mapping"),
    "extends": ((str,), "type.string"),
    "references": ((list, type(None)), "type.sequence"),
    "styles": ((list, str), "type.sequence"),
    "name": ((str,), "type.string"),
    "language": ((str,), "type.string"),
    "on_conflict": ((str,), "type.string"),
    "build_date": ((DateTime,), "type.datetime"),
}

#: Map of :class:`yamlio.YamlIssue` kinds to diagnostic codes.
_ISSUE_CODES: dict[str, str] = {
    "syntax": "P1102",
    "date": "P1109",
    "zone": "P1119",
    "duplicate": "P1110",
    "tag": "P1111",
    "recursive": "P1112",
    "complex_key": "P1113",
    "bool11": "P1114",
    "leading_zero": "P1115",
}


@dataclass
class Header:
    """The header of a source file.

    Attributes:
        source: the source file.
        present: the file has a header.
        kind: file kind (``kind`` key, else sub-extension, else ``document``).
        version: language version declared or implied.
        data: header mapping (empty without a header or after an error).
        span: the whole header including both ``---`` lines, or ``None``.
        content_start: offset of the YAML text in the source.
        body_start: offset where the body (markup or code) starts.
        yaml: the read YAML document, or ``None``.
    """

    source: SourceFile
    present: bool = False
    kind: str = "document"
    version: str = LANGUAGE_VERSION
    data: dict[Any, Any] = field(default_factory=dict)
    span: Span | None = None
    content_start: int = 0
    body_start: int = 0
    yaml: yamlio.YamlDocument | None = None

    def value_span(self, path: yamlio.YamlPath, *, key: bool = False) -> Span | None:
        """Return the source span of a header value (or of its key).

        Args:
            path: path of the value, for example ``("primula", "version")``.
            key: return the span of the key instead of the value.
        """
        if self.yaml is None:
            return None
        found = self.yaml.span_of(path, key=key)
        if found is None:
            return None
        return Span(self.source, self.content_start + found[0], self.content_start + found[1])


def split_header(source: SourceFile) -> tuple[int, int, int] | None:
    """Locate the header delimiters.

    Args:
        source: the source file.

    Returns:
        ``None`` if the file has no header, otherwise
        ``(content_start, content_end, body_start)``: the YAML text is
        ``text[content_start:content_end]``; ``content_end == -1`` means the
        closing line is missing.
    """
    text = source.text
    first_end = text.find("\n")
    first_line = text if first_end == -1 else text[:first_end]
    if first_line != "---":
        return None
    content_start = len(text) if first_end == -1 else first_end + 1
    position = content_start
    while position <= len(text):
        line_end = text.find("\n", position)
        line = text[position:] if line_end == -1 else text[position:line_end]
        if line == "---":
            body_start = len(text) if line_end == -1 else line_end + 1
            return content_start, position, body_start
        if line_end == -1:
            break
        position = line_end + 1
    return content_start, -1, len(text)


def parse_header(source: SourceFile, sink: DiagnosticSink) -> Header:
    """Split, read and check the header of a source file.

    Errors and warnings go to ``sink``; the function always returns a
    :class:`Header` so that later phases can continue with defaults.

    Args:
        source: the source file.
        sink: diagnostics receiver.

    Returns:
        The header (``present=False`` if the file has none).
    """
    header = Header(source, kind=kind_from_name(source.name) or "document")
    located = split_header(source)
    if located is None:
        return header

    content_start, content_end, body_start = located
    header.present = True
    header.content_start = content_start
    header.body_start = body_start
    opening = Span(source, 0, 3)

    if content_end == -1:
        header.span = Span(source, 0, len(source.text))
        sink.emit(error("P1101", opening).hint("help.header_close"))
        return header
    header.span = Span(source, 0, min(content_end + 3, len(source.text)))

    try:
        document = yamlio.load(source.text[content_start:content_end])
    except yamlio.YamlError as exc:
        _emit_issue(header, sink, exc.issue)
        return header
    header.yaml = document
    for issue in document.warnings:
        _emit_issue(header, sink, issue)

    if document.value is None:
        return header
    if not isinstance(document.value, dict):
        sink.emit(error("P1103", header.value_span(()), found=_type_name(document.value))
                  .note("note.header_opened", opening))
        return header

    header.data = document.value
    _check_structure(header, sink)
    return header


def _emit_issue(header: Header, sink: DiagnosticSink, issue: yamlio.YamlIssue) -> None:
    """Convert a YAML issue to a diagnostic positioned in the source file."""
    base = header.content_start
    span = Span(header.source, base + issue.start, base + max(issue.start, issue.end))
    code = _ISSUE_CODES[issue.kind]
    args = dict(issue.args)
    if issue.kind == "leading_zero":
        args["number"] = int(str(issue.args["value"]), 10)
    make = warning if issue.kind in ("bool11", "leading_zero") else error
    diagnostic = make(code, span, **args)
    if issue.related is not None:
        related = Span(header.source, base + issue.related[0], base + issue.related[1])
        if issue.kind == "duplicate":
            diagnostic.note("note.first_key", related)
        else:
            diagnostic.note("note.yaml_context", related, context=issue.args.get("context", ""))
    if issue.kind == "bool11":
        diagnostic.hint("help.yaml_bool")
    elif issue.kind == "leading_zero":
        diagnostic.hint("help.yaml_quote")
    sink.emit(diagnostic)


def _type_name(value: Any) -> Key:
    """Return the translatable type name of a value (a ``type.*`` key)."""
    return Key(yamlio.type_key(value))


def _check_structure(header: Header, sink: DiagnosticSink) -> None:
    """Check ``kind``, ``primula``, key sets and value types of a header."""
    data = header.data

    # kind (section 2.2): the key wins over the sub-extension.
    kind_ok = True
    by_name = kind_from_name(header.source.name)
    if "kind" in data:
        kind = data["kind"]
        if not isinstance(kind, str):
            _type_error(header, sink, ("kind",), "type.string", kind)
            kind_ok = False
        elif kind not in FILE_KINDS:
            sink.emit(error("P1106", header.value_span(("kind",)), value=kind,
                            expected=", ".join(FILE_KINDS)))
            kind_ok = False
        else:
            header.kind = kind
            # A project file without ``.p.prml`` is a mismatch too (10.6, decision 118).
            implied = by_name if by_name is not None else ("document" if kind == "project" else None)
            if implied is not None and implied != kind:
                sink.emit(warning("P7001", header.value_span(("kind",)), kind=kind,
                                  name=header.source.name, implied=implied))

    # Top-level keys and their types.
    known = HEADER_KEYS[header.kind]
    for key, value in list(data.items()):
        if not isinstance(key, str) or key not in known:
            renamed = RENAMED_KEYS.get((header.kind, key)) if kind_ok and isinstance(key, str) else None
            if renamed is not None:
                sink.emit(error("P1120", header.value_span((key,), key=True), key=key, new=renamed))
            elif kind_ok:
                sink.emit(warning("P1104", header.value_span((key,), key=True),
                                  key=str(key), kind=header.kind))
            continue
        expected = _KEY_TYPES.get(key)
        if expected is not None and not isinstance(value, expected[0]):
            _type_error(header, sink, (key,), expected[1], value)
            # The error is reported; later phases see the key as absent instead of
            # meeting a value of the wrong type (found by the robustness check, 13.15).
            if key != "kind":
                del data[key]

    # primula: {version, stdlib} (sections 0.1, 2.3, 13)
    declaration = data.get("primula")
    if isinstance(declaration, dict):
        _check_declaration(header, sink, declaration)

    # doc: ODT metadata keys (section 2.3); in a project — doc_defaults, their defaults
    # (10.6, decisions 127, 129)
    section = {"document": "doc", "project": "doc_defaults"}.get(header.kind)
    metadata = data.get(section) if section else None
    if isinstance(metadata, dict):
        for key in metadata:
            if not isinstance(key, str) or key not in DOCUMENT_KEYS:
                sink.emit(warning("P1104", header.value_span((section, key), key=True),
                                  key=f"{section}.{key}", kind=header.kind))


def _check_declaration(header: Header, sink: DiagnosticSink, declaration: dict[Any, Any]) -> None:
    """Check the ``primula:`` language declaration."""
    for key, value in declaration.items():
        path = ("primula", key)
        if key == "version":
            # "1.0" quoted is a string; 1.0 unquoted is a decimal (rule 25);
            # an integer (`version: 1`) is a wrong version, not a wrong type.
            if isinstance(value, (str, Decimal, int)) and not isinstance(value, bool):
                text = str(value)
                if text not in SUPPORTED_VERSIONS:
                    diagnostic = error("P1107", header.value_span(path), value=text,
                                       supported=", ".join(SUPPORTED_VERSIONS))
                    if text == "1.0":
                        diagnostic.hint("help.version_10")
                    sink.emit(diagnostic)
                else:
                    header.version = text
            else:
                _type_error(header, sink, path, "type.string", value)
        elif key == "stdlib":
            # The file requires at least this library version (section 13).
            if isinstance(value, (str, Decimal, int)) and not isinstance(value, bool):
                if _version_tuple(str(value)) is None:
                    sink.emit(error("P1117", header.value_span(path), value=str(value)))
                elif _version_tuple(str(value)) > _version_tuple(STDLIB_VERSION):
                    sink.emit(error("P1118", header.value_span(path), value=str(value),
                                    available=STDLIB_VERSION))
            else:
                _type_error(header, sink, path, "type.string", value)
        elif key == "lines":
            # Version 1.0 key: the line mode was removed (decision 107).
            sink.emit(error("P1116", header.value_span(path, key=True)))
        else:
            sink.emit(warning("P1104", header.value_span(path, key=True),
                              key=f"primula.{key}", kind=header.kind))


def kind_from_name(name: str) -> str | None:
    """File kind implied by the sub-extension of ``name`` (section 2.2), or ``None``.

    Only ``.f``, ``.m``, ``.s`` and ``.p`` before ``.prml`` are reserved:
    ``report.f.prml`` is a fragment, ``a.b.prml`` is a document.
    """
    base = name.replace("\\", "/").rsplit("/", 1)[-1]
    if not base.endswith(".prml"):
        return None
    stem = base[:-len(".prml")]
    dot = stem.rfind(".")
    return SUB_EXTENSIONS.get(stem[dot:]) if dot > 0 else None


def _version_tuple(text: str) -> tuple[int, ...] | None:
    """``"1.1"`` -> ``(1, 1)``; ``None`` if the text is not ``MAJOR.MINOR``."""
    parts = text.split(".")
    if len(parts) != 2 or not all(part.isdigit() and part.isascii() for part in parts):
        return None
    return tuple(int(part) for part in parts)


def _type_error(header: Header, sink: DiagnosticSink, path: yamlio.YamlPath,
                expected: str, value: Any) -> None:
    """Report a value of a wrong type (P1105)."""
    sink.emit(error("P1105", header.value_span(path), key=".".join(str(p) for p in path),
                    expected=Key(expected), found=_type_name(value)))
