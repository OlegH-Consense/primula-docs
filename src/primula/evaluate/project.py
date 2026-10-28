"""The project file ``project.p.prml`` (10.6, 10.7, 9.3; decision 117).

A project file has two sections: the YAML header (the descriptive section,
read without running code) and the code section.  This module

* finds the project of a root document (:func:`find_project`): from the
  directory of the document upwards, each directory checked, the search
  stops after a directory with ``.git`` or at the filesystem root; the
  nearest ``project.p.prml`` wins and its directory is the project root;
* reads and checks the descriptive section (:func:`load_project`):
  ``kind: project`` is required; ``name``, ``language``, ``styles``,
  ``on_conflict``, ``params``, ``keys``, ``limits``, ``build_date``,
  ``targets`` (P7101-P7103);
* checks the build targets before a batch build (:func:`check_targets`):
  sources, declared parameters and their types, keys, output paths
  inside the project and without collisions (P7104-P7111);
* produces the JSON summary of ``check --dump-project`` (:func:`dump_project`).

Values of parameters (decision 117): a target (``build()``,
``targets[].params``) overrides the document header, which overrides the
project; a value is replaced as a whole; the type is checked at the top
level (``type()``; ``decimal`` and ``float`` differ; a project ``None``
accepts any type).
"""

from __future__ import annotations

import datetime
import keyword
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from primula.core.limits import Limits
from primula.core.values import DateTime, PDict, Record, from_data, to_repr, type_name
from primula.diagnostics import DiagnosticSink, error
from primula.evaluate.loader import strip_extension
from primula.header import DOCUMENT_KEYS, Header, parse_header
from primula.i18n import Key
from primula.paths import within
from primula.source import SourceDecodeError, SourceFile, SourceManager, SourceReadError, Span
from primula.unicode import is_identifier, nfkc

#: The fixed name of the project file (10.6).
PROJECT_FILE = "project.p.prml"
#: Keys of a build target (10.7).
TARGET_KEYS = ("source", "output", "params", "keys", "pdf")
#: Values of ``on_conflict`` (10.4).
CONFLICT_MODES = ("error", "first", "last")
#: Version of the ``--dump-project`` JSON structure.
DUMP_SCHEMA = 1


@dataclass
class Target:
    """A build target (10.7).

    Attributes:
        source: path of the source document relative to the project root.
        output: path of the ODT relative to the project root.
        params: parameter values (Primula values) by name.
        keys: overridden keys: name -> path relative to the project root.
        pdf: ``None``, ``True`` (next to the ODT) or a path in the project.
        span: position of the target (header entry or ``build()`` call).
        origin: ``"targets"`` (header) or ``"build"`` (code section).
    """

    source: str
    output: str
    params: dict[str, Any] = field(default_factory=dict)
    keys: dict[str, str] = field(default_factory=dict)
    pdf: bool | str | None = None
    span: Span | None = None
    origin: str = "targets"

    def pdf_path(self) -> str | None:
        """The PDF path relative to the project root, or ``None``."""
        if self.pdf is True:
            return str(Path(self.output).with_suffix(".pdf"))
        return self.pdf if isinstance(self.pdf, str) else None


@dataclass
class Project:
    """The descriptive section of a project file.

    Attributes:
        path: resolved path of the project file.
        root: the project root (directory of the file).
        source: the source text; header: its header.
        name, language: name and default language of the project.
        styles: styles modules (paths relative to the project file).
        on_conflict: mode of export conflicts (10.4).
        params: parameter name -> (value as Primula value, span of the key).
        keys: key name -> (path text, span of the value).
        limits: core limits (12.8).
        build_date: fixed build date, or ``None``.
        targets: targets of the header.
        doc_defaults: defaults of the ODT metadata of the documents of the
            project (``doc_defaults`` key, decisions 127, 129): YAML values by key;
            the ``doc`` key of a document header overrides them key by key.
        ref_documents: named documents of the project for references between
            documents (5.7, decision 121): name -> (source, registry), paths
            relative to the project root; ``source`` may be ``None`` (a
            registry of a published edition only).
    """

    path: Path
    root: Path
    source: SourceFile
    header: Header
    name: str | None = None
    language: str | None = None
    styles: list[str] = field(default_factory=list)
    on_conflict: str = "error"
    params: dict[str, tuple[Any, Span | None]] = field(default_factory=dict)
    keys: dict[str, tuple[str, Span | None]] = field(default_factory=dict)
    limits: Limits = field(default_factory=Limits)
    build_date: datetime.date | None = None
    targets: list[Target] = field(default_factory=list)
    ref_documents: dict[str, tuple[str | None, str]] = field(default_factory=dict)
    doc_defaults: dict[str, Any] = field(default_factory=dict)
    #: Base projects of ``extends`` (decision 123), the outermost first: their
    #: code sections run before this one.
    bases: list["Project"] = field(default_factory=list)

    def span(self, *path: Any, key: bool = False) -> Span:
        """Position of a header value (or of the header itself)."""
        return self.header.value_span(tuple(path), key=key) or self.header.span or Span(self.source, 0, 0)

    def contains(self, path: Path) -> bool:
        """Whether a path lies inside the project root (lexically, decision 136)."""
        return within(path, self.root) is not None


# ----------------------------------------------------------------------
# Search and loading
# ----------------------------------------------------------------------

def find_project(document: Path) -> Path | None:
    """The project file of a root document (10.6, decision 117).

    The search starts in the directory of the document and goes up; every
    directory is checked, including the one with ``.git``, after which the
    search stops (as at the filesystem root).

    Args:
        document: path of the root document.

    Returns:
        The nearest ``project.p.prml`` or ``None``.
    """
    directory = document.resolve().parent
    while True:
        candidate = directory / PROJECT_FILE
        if candidate.is_file():
            return candidate
        if (directory / ".git").exists() or directory.parent == directory:
            return None
        directory = directory.parent


def parse_param_option(text: str) -> tuple[str, Any, str] | None:
    """Read one ``--param NAME=VALUE`` (14.1, П2).

    The value is a YAML scalar as in ``load_yaml``: ``42`` is a number,
    ``true`` a boolean, ``2026-10-15`` a date, other text a string; quotes
    are allowed.  A mapping, a list or an empty value is the text itself.

    Returns:
        ``(name, value, text)`` — the name in NFKC, the core value and the
        value text as written without surrounding quotes (a string parameter
        takes it), or ``None`` without ``=`` or a name.
    """
    from primula import yamlio
    from primula.unicode import nfkc

    name, sep, raw = text.partition("=")
    name = name.strip()
    if not sep or not name:
        return None
    try:
        value = yamlio.load("v: " + raw).value
        value = value.get("v") if isinstance(value, dict) else raw
    except yamlio.YamlError:
        value = raw
    if value is None or isinstance(value, (dict, list)):
        value = raw
    plain = raw.strip()
    if len(plain) >= 2 and plain[0] == plain[-1] and plain[0] in "\"'":
        plain = plain[1:-1]
    return nfkc(name), from_data(value), plain


def is_project_file(path: Path) -> bool:
    """Whether ``path`` is a project file: its kind is ``project`` (10.6, decision 118).

    The kind is that of the header (the ``kind`` key, otherwise the
    sub-extension, decision 100), so a project file named without ``.p.prml``
    is built as a project too (its header gives warning P7001).  The header is
    read with a throwaway sink: its messages come when the file is loaded for
    the command.  An unreadable file is not a project file; the command then
    reports the read error.
    """
    from primula.header import kind_from_name, parse_header

    try:
        source = SourceManager().load(path, str(path))
    except Exception:  # noqa: BLE001 - read and decoding errors are reported by the command
        return kind_from_name(path.name) == "project"
    return parse_header(source, DiagnosticSink(error_limit=0)).kind == "project"


def load_project(path: Path, manager: SourceManager, sink: DiagnosticSink) -> Project | None:
    """Read and check the descriptive section of a project file.

    Args:
        path: path of the project file.
        manager: source manager (the file goes to the report).
        sink: diagnostics receiver.

    Returns:
        The project, or ``None`` if the file cannot be read or its header
        is not a project header.  Errors in single values are reported and
        the value is left at its default.
    """
    resolved = path.resolve()
    try:
        source = manager.load(resolved, resolved.name)
    except SourceReadError as exc:
        sink.emit(error("P0101", None, at_file=str(path), path=str(path), reason=exc.reason))
        return None
    except SourceDecodeError as exc:
        manager.add(exc.partial)
        sink.emit(error("P0102", Span(exc.partial, exc.offset, exc.offset), byte_offset=exc.byte_offset))
        return None
    errors = sink.error_count
    header = parse_header(source, sink)
    if sink.error_count > errors and not header.data:
        return None
    if header.data.get("kind") != "project":
        sink.emit(error("P7101", header.value_span(("kind",)) or header.span or Span(source, 0, 0),
                        kind=str(header.data.get("kind", ""))))
        return None
    project = Project(resolved, resolved.parent, source, header)
    _read_header(project, sink)
    extends = header.data.get("extends")
    if isinstance(extends, str) and extends:
        base_path = (resolved.parent / extends).resolve()
        if base_path == resolved or base_path in _EXTENDING:
            sink.emit(error("P7130", project.span("extends"), path=extends))
            return project
        _EXTENDING.add(resolved)
        try:
            base = load_project(base_path, manager, sink)
        finally:
            _EXTENDING.discard(resolved)
        if base is not None:
            _extend(project, base, sink)
    return project


#: Project files being loaded through ``extends`` (a cycle is P7130).
_EXTENDING: set[Path] = set()


def _extend(project: Project, base: Project, sink: DiagnosticSink) -> None:
    """``extends: ../../project.p.prml`` (10.6, decision 123): inherit from the base project.

    The project takes the root of its base (fragments, styles and data of
    the base are inside it); its own paths — styles, keys, reference documents,
    targets — are written relative to its own file and are converted here.
    Parameters, keys, reference documents, metadata defaults and styles are inherited and may be
    extended or overridden; the code section of the base runs before the
    own one (:meth:`DocumentEvaluator._load_project`); ``targets`` are not
    inherited.
    """
    import os
    import posixpath

    own_dir = project.root
    try:
        rel = own_dir.relative_to(base.root)
    except ValueError:
        sink.emit(error("P7131", project.span("extends"), path=str(project.header.data.get("extends"))))
        return

    def from_own(text: str) -> str:
        return text if text.startswith("std/") else posixpath.normpath((rel / text).as_posix())

    base_styles = [text if text.startswith("std/") else os.path.relpath(base.path.parent / text, own_dir)
                   for text in base.styles]
    project.styles = base_styles + project.styles
    project.params = {**base.params, **project.params}
    project.doc_defaults = {**base.doc_defaults, **project.doc_defaults}
    project.keys = {**base.keys, **{name: (from_own(text), span) for name, (text, span) in project.keys.items()}}
    project.ref_documents = {**base.ref_documents,
                         **{name: (from_own(src) if src else None, from_own(reg) if reg else reg)
                            for name, (src, reg) in project.ref_documents.items()}}
    for target in project.targets:
        target.source, target.output = from_own(target.source), from_own(target.output)
        if isinstance(target.pdf, str):
            target.pdf = from_own(target.pdf)
    data = project.header.data
    for key in ("name", "language", "on_conflict", "limits", "build_date"):
        if key not in data:
            setattr(project, key, getattr(base, key))
    project.root = base.root
    project.bases = [*base.bases, base]


def _invalid(project: Project, sink: DiagnosticSink, path: tuple[Any, ...], expected: str) -> None:
    sink.emit(error("P7102", project.span(*path), key=".".join(str(p) for p in path),
                    expected=Key(f"project.{expected}")))


def _read_header(project: Project, sink: DiagnosticSink) -> None:
    """Fill the project from its header; types of top-level keys are checked by :mod:`primula.header`."""
    data = project.header.data
    if isinstance(data.get("name"), str):
        project.name = data["name"]
    if isinstance(data.get("language"), str):
        project.language = data["language"]
    styles = data.get("styles")
    if isinstance(styles, str):
        styles = [styles]
    if isinstance(styles, list):
        for index, item in enumerate(styles):
            if isinstance(item, str) and item:
                project.styles.append(item)
            else:
                _invalid(project, sink, ("styles", index), "path")
    conflict = data.get("on_conflict")
    if conflict is not None:
        if conflict in CONFLICT_MODES:
            project.on_conflict = conflict
        else:
            _invalid(project, sink, ("on_conflict",), "on_conflict")
    metadata = data.get("doc_defaults")
    if isinstance(metadata, dict):
        # Unknown keys are reported by primula.header (P1104) and left out.
        project.doc_defaults = {key: value for key, value in metadata.items()
                            if isinstance(key, str) and key in DOCUMENT_KEYS and value is not None}
    for name, value in (data.get("params") or {}).items() if isinstance(data.get("params"), dict) else ():
        span = project.span("params", name, key=True)
        if not isinstance(name, str) or not is_identifier(name) or keyword.iskeyword(name):
            sink.emit(error("P2634", span, name=str(name)))
            continue
        project.params[nfkc(name)] = (from_data(value), span)
    for name, value in (data.get("keys") or {}).items() if isinstance(data.get("keys"), dict) else ():
        if not isinstance(name, str) or not _key_name(name):
            sink.emit(error("P7102", project.span("keys", name, key=True), key=f"keys.{name}",
                            expected=Key("project.key_name")))
        elif not isinstance(value, str) or not value or value.startswith("#"):
            _invalid(project, sink, ("keys", name), "path")
        else:
            project.keys[nfkc(name)] = (value, project.span("keys", name))
    for name, value in (data.get("ref_documents") or {}).items() if isinstance(data.get("ref_documents"), dict) else ():
        # name: "contract.prml" or {source: …, registry: …} (decision 121).
        source = value if isinstance(value, str) else value.get("source") if isinstance(value, dict) else None
        registry = value.get("registry") if isinstance(value, dict) else None
        if not isinstance(name, str) or not _key_name(name):
            sink.emit(error("P7102", project.span("ref_documents", name, key=True), key=f"ref_documents.{name}",
                            expected=Key("project.key_name")))
        elif not (isinstance(source, str) and source or isinstance(registry, str) and registry) or \
                (source is not None and not isinstance(source, str)) or \
                (registry is not None and not isinstance(registry, str)) or \
                (isinstance(value, dict) and set(value) - {"source", "registry"}):
            _invalid(project, sink, ("ref_documents", name), "document_entry")
        else:
            default = "build/" + strip_extension(Path(source).name) + ".refs.json" if source else ""
            project.ref_documents[nfkc(name)] = (source, registry or default)
    limits = data.get("limits")
    if isinstance(limits, dict):
        valid: dict[str, Any] = {}
        for key, value in limits.items():
            number = _number(value)
            if key not in ("time", "recursion", "size") or number is None or number <= 0 or \
                    (key != "time" and number != int(number)):
                _invalid(project, sink, ("limits", key), "limits")
                continue
            valid[key] = float(number) if key == "time" else int(number)
        project.limits = Limits.from_mapping(valid)
    build_date = data.get("build_date")
    if isinstance(build_date, DateTime):
        project.build_date = build_date.to_python().date()
    targets = data.get("targets")
    if isinstance(targets, list):
        for index, entry in enumerate(targets):
            target = _header_target(project, sink, index, entry)
            if target is not None:
                project.targets.append(target)


def _number(value: Any) -> float | None:
    """A YAML number (``decimal`` or ``float``) as ``float``; ``None`` otherwise."""
    from decimal import Decimal

    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
        return None
    return float(value)


def _key_name(name: str) -> bool:
    """A key name: identifiers separated by dots (``safety.general``, 9.3)."""
    return all(is_identifier(part) for part in name.split("."))


def _header_target(project: Project, sink: DiagnosticSink, index: int, entry: Any) -> Target | None:
    """A ``targets`` entry: ``{source, output, params, keys, pdf}``."""
    where = ("targets", index)
    if not isinstance(entry, dict):
        _invalid(project, sink, where, "target")
        return None
    ok = True
    for key in entry:
        if key not in TARGET_KEYS:
            sink.emit(error("P7102", project.span("targets", index, key, key=True), key=f"targets.{index}.{key}",
                            expected=Key("project.target")))
            ok = False
    for key in ("source", "output"):
        if not isinstance(entry.get(key), str) or not entry.get(key):
            _invalid(project, sink, (*where, key) if key in entry else where, "target_path")
            ok = False
    params = entry.get("params") or {}
    keys = entry.get("keys") or {}
    pdf = entry.get("pdf")
    if not isinstance(params, dict):
        _invalid(project, sink, (*where, "params"), "mapping")
        ok = False
    if not isinstance(keys, dict) or not all(isinstance(v, str) and v for v in keys.values()):
        _invalid(project, sink, (*where, "keys"), "keys")
        ok = False
    if pdf is not None and not isinstance(pdf, (bool, str)):
        _invalid(project, sink, (*where, "pdf"), "pdf")
        ok = False
    if not ok:
        return None
    return Target(entry["source"], entry["output"],
                  {nfkc(str(k)): from_data(v) for k, v in params.items()},
                  {nfkc(str(k)): v for k, v in keys.items()},
                  pdf if pdf is not False else None, project.span(*where), "targets")


def target_from_call(args: list[Any], kwargs: dict[str, Any], span: Span) -> Target:
    """A target of ``build(source, params=…, keys=…, output=…, pdf=…)`` (10.7).

    Raises:
        CoreError: P7103 for a missing ``output`` or invalid arguments.
    """
    from primula.core.errors import core_error

    unknown = [k for k in kwargs if k not in TARGET_KEYS]
    source = args[0] if args else kwargs.get("source")
    if len(args) > 1 or unknown:
        raise core_error("P7103", span, problem=Key("project.build_args"))
    if not isinstance(source, str) or not source:
        raise core_error("P7103", span, problem=Key("project.build_source"))
    output = kwargs.get("output")
    if not isinstance(output, str) or not output:
        raise core_error("P7103", span, problem=Key("project.build_output"))
    params = kwargs.get("params")
    if params is None:
        params = {}
    elif isinstance(params, Record):
        params = dict(params.fields.items())
    elif isinstance(params, (PDict, dict)):
        params = dict(params.items())
    else:
        raise core_error("P7103", span, problem=Key("project.build_params"))
    if not all(isinstance(k, str) for k in params):
        raise core_error("P7103", span, problem=Key("project.build_params"))
    keys = kwargs.get("keys")
    keys = dict(keys.items()) if isinstance(keys, (PDict, dict, Record)) and not isinstance(keys, Record) else \
        (dict(keys.fields.items()) if isinstance(keys, Record) else ({} if keys is None else None))
    if keys is None or not all(isinstance(k, str) and isinstance(v, str) and v for k, v in keys.items()):
        raise core_error("P7103", span, problem=Key("project.build_keys"))
    pdf = kwargs.get("pdf")
    if pdf is not None and not isinstance(pdf, (bool, str)):
        raise core_error("P7103", span, problem=Key("project.build_pdf"))
    return Target(source, output, {nfkc(k): v for k, v in params.items()}, {nfkc(k): v for k, v in keys.items()},
                  pdf if pdf is not False else None, span, "build")


# ----------------------------------------------------------------------
# Parameters (decision 117)
# ----------------------------------------------------------------------

def same_type(value: Any, declared: Any) -> bool:
    """Top-level type check of a parameter value against its declaration.

    ``None`` as the declared value accepts any type; ``record`` and
    ``dict`` are both mappings (a YAML mapping is a record, a ``build()``
    argument is usually a dictionary).
    """
    if declared is None:
        return True
    mapping = ("record", "dict")
    actual, expected = type_name(value), type_name(declared)
    return actual == expected or (actual in mapping and expected in mapping)


def check_target(project: Project, target: Target, sink: DiagnosticSink, manager: SourceManager) -> bool:
    """Check a target before the build (10.7): source, parameters, keys, paths.

    Args:
        project: the project.
        target: the target.
        sink: diagnostics receiver.
        manager: source manager (reads the header of the source).

    Returns:
        ``True`` if the target can be built.
    """
    span = target.span or project.span()
    ok = True
    for text in (target.output, target.pdf_path()):
        if text is not None and not _inside(project, text):
            sink.emit(error("P7108", span, path=text))
            ok = False
    if not _inside(project, target.source):
        sink.emit(error("P7104", span, path=target.source, reason=Key("project.outside")))
        return False
    source_path = (project.root / target.source).resolve()
    if not source_path.is_file():
        sink.emit(error("P7104", span, path=target.source, reason=Key("project.no_file")))
        return False
    try:
        source = manager.load(source_path, str(source_path.relative_to(project.root)))
    except (SourceReadError, SourceDecodeError):
        sink.emit(error("P7104", span, path=target.source, reason=Key("project.no_file")))
        return False
    header = parse_header(source, DiagnosticSink(error_limit=0))
    if header.kind != "document":
        sink.emit(error("P7104", span, path=target.source, reason=Key("project.not_document")))
        return False
    declared = {nfkc(str(k)): v for k, v in (header.data.get("params") or {}).items()} \
        if isinstance(header.data.get("params"), dict) else {}
    for name, value in target.params.items():
        if name in declared:
            expected = from_data(declared[name])
        elif name in project.params:
            expected = project.params[name][0]
        else:
            sink.emit(error("P7105", span, name=name, source=target.source))
            ok = False
            continue
        if not same_type(value, expected):
            sink.emit(error("P7106", span, name=name, type=type_name(value), expected=type_name(expected)))
            ok = False
    for name in target.keys:
        if name not in project.keys:
            sink.emit(error("P7107", span, key=name))
            ok = False
    return ok


def _inside(project: Project, text: str) -> bool:
    if not text or Path(text).is_absolute() or "://" in text:
        return False
    return project.contains(project.root / text)


def check_outputs(project: Project, targets: list[Target], sink: DiagnosticSink) -> set[int]:
    """Collisions of the output paths (ODT and PDF) of all targets (10.7): P7109.

    Returns:
        Indexes of the targets that collide with an earlier one.
    """
    seen: dict[Path, Target] = {}
    bad: set[int] = set()
    for index, target in enumerate(targets):
        for text in (target.output, target.pdf_path()):
            if text is None:
                continue
            path = (project.root / text).resolve()
            first = seen.get(path)
            if first is not None and first is not target:
                diagnostic = error("P7109", target.span or project.span(), path=text)
                if first.span is not None:
                    diagnostic.note("note.first_definition", first.span)
                sink.emit(diagnostic)
                bad.add(index)
            else:
                seen[path] = target
    return bad


# ----------------------------------------------------------------------
# --dump-project (14.1)
# ----------------------------------------------------------------------

def dump_project(path: Path, project: Project | None, sink: DiagnosticSink, catalog: Any) -> dict[str, Any]:
    """The JSON summary of the descriptive section (no code is run).

    Args:
        path: the project file as given.
        project: the loaded project (``None`` after a fatal header error).
        sink: diagnostics of reading the header.
        catalog: message catalogue for the messages.

    Returns:
        ``schema``, ``file``, ``root``, ``name``, ``language``, ``styles``, ``params``
        (name -> ``{type, default}``), ``keys``, ``limits``, ``build_date``,
        ``targets`` of the header, ``ref_documents``, ``doc_defaults`` and ``messages``.
    """
    from primula.diagnostics import to_json

    def value(v: Any) -> Any:
        if v is None or isinstance(v, (bool, str)):
            return v
        if isinstance(v, Record):
            return {k: value(x) for k, x in v.fields.items()}
        if isinstance(v, (list, tuple)):
            return [value(x) for x in v]
        return to_repr(v)

    data: dict[str, Any] = {"schema": DUMP_SCHEMA, "file": str(path)}
    if project is not None:
        limits = project.limits
        data.update({
            # The project root (for ``extends`` — the root of the base project, decision 123):
            # paths of targets and messages are relative to it; Studio keeps its service directory there.
            "root": str(project.root),
            "name": project.name,
            "language": project.language,
            "styles": project.styles,
            "on_conflict": project.on_conflict,
            "params": {name: {"type": type_name(v), "default": value(v)} for name, (v, _s) in project.params.items()},
            "keys": {name: text for name, (text, _s) in project.keys.items()},
            "limits": {"time": limits.time, "recursion": limits.recursion, "size": limits.size},
            "build_date": project.build_date.isoformat() if project.build_date else None,
            "targets": [{"source": t.source, "output": t.output,
                         "params": {k: value(v) for k, v in t.params.items()},
                         "keys": dict(t.keys), "pdf": t.pdf} for t in project.targets],
            "ref_documents": {name: {"source": source or None, "registry": registry or None}
                              for name, (source, registry) in getattr(project, "ref_documents", {}).items()},
            "doc_defaults": {key: v if v is None or isinstance(v, (bool, str)) else v.iso() if isinstance(v, DateTime)
                             else to_repr(from_data(v)) for key, v in project.doc_defaults.items()},
        })
    data["messages"] = [to_json(d, catalog) for d in sink.ordered()]
    return data
