"""References to other documents of a project and their registries (5.7, 10.6; decision 121).

A document of a project may refer to the targets of another document of the
same project: a standalone order form refers to the clauses of the contract
it belongs to («п. 2.5 Договору»).  The project names its documents::

    ref_documents:
      contract: Consense-Contract-UA-CA102-26-1.prml       # registry: build/<stem>.refs.json
      published: {registry: refs/CA102-26-1.refs.json}     # a published edition, no source

and the referring document lists them in its header: ``references:
[contract]``.  A reference whose target is not found in the document itself
is looked up in these documents.

The **registry** of a document (``*.refs.json``) holds its targets (kind,
number, label key, title) and the SHA-256 of the files it was built from.
``primula build`` of a named document writes it.  When a referring document
needs it:

* the registry exists and its files are unchanged — it is used as is;
* it is missing or stale and the source is available — the document is
  evaluated (without writing an ODT), the registry is rewritten (by
  ``build``; ``check`` writes nothing);
* there is no source — the registry is used as it is (a published edition).

A reference to another document is text without a hyperlink; the ``page``
mode is an error (P4308), a target found in several documents too (P4309).
The report lists where every such text came from.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from primula.diagnostics import DiagnosticSink, error, warning
from primula.paths import within
from primula.source import Span, read_source_bytes

SCHEMA = 1
#: Documents being evaluated for their registries (a cycle of references).
_ACTIVE: set[Path] = set()


def make_registry(name: str, source: str, structure: Any, files: dict[str, str]) -> dict[str, Any]:
    """The registry of a built document.

    Args:
        name: the name of the document in ``ref_documents`` of the project.
        source: its path relative to the project root.
        structure: the structure phase result (``targets``).
        files: path relative to the project root -> SHA-256 of every file read.
    """
    from primula import __version__

    targets: dict[str, Any] = {}
    for target_id, target in sorted(structure.targets.items()):
        if target.note is not None or target.kind == "section":
            continue
        title = target.title() if callable(target.title) else target.title
        targets[target_id] = {"kind": target.kind, "number": target.number, "label_key": target.label_key,
                              "title": title}
    return {"schema": SCHEMA, "translator": __version__, "document": name, "source": source,
            "files": files, "targets": targets}


def source_files(manager: Any, root: Path) -> dict[str, str]:
    """Files of the project read by a build: relative path -> SHA-256 (the standard library is not listed)."""
    files: dict[str, str] = {}
    for source in manager.files:
        path = getattr(source, "path", None)
        if path is None:
            continue
        relative = within(Path(path), root)
        if relative is None:
            continue
        files[relative.as_posix()] = source.sha256
    return dict(sorted(files.items()))


def write_registry(path: Path, registry: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(registry, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def _fresh(registry: dict[str, Any], root: Path) -> bool:
    """The files of the registry are unchanged and it was written by this translator version."""
    from primula import __version__

    if registry.get("schema") != SCHEMA or registry.get("translator") != __version__:
        return False
    for relative, digest in (registry.get("files") or {}).items():
        try:
            # An unsaved editor buffer (--overlay) counts as a change.
            data = read_source_bytes(root / relative)
        except OSError:
            return False
        if hashlib.sha256(data).hexdigest() != digest:
            return False
    return True


def _read(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) and isinstance(data.get("targets"), dict) else None


class ExternalReferences:
    """Targets of the documents named in ``references:`` of a document header.

    Args:
        project: the project (``ref_documents``).
        names: the value of ``references:``.
        sink: diagnostics receiver.
        span: position of the ``references`` key (for errors).
        current: resolved path of the document being built (it is not its own source).
        write: ``True`` for ``build`` — stale registries are rewritten.
    """

    def __init__(self, project: Any, names: list[Any], sink: DiagnosticSink, span: Span | None,
                 current: Path, write: bool) -> None:
        self.project = project
        self.sink = sink
        self.span = span
        self.current = current
        self.write = write
        self.names: list[str] = []
        self._registries: dict[str, dict[str, Any]] = {}
        self._origin: dict[str, tuple[str, str]] = {}
        #: Report entries: target, document, origin (``registry``/``computed``), registry path.
        self.origins: list[dict[str, Any]] = []
        documents = getattr(project, "ref_documents", {}) if project is not None else {}
        for name in names:
            if isinstance(name, str) and name in documents:
                self.names.append(name)
            else:
                sink.emit(error("P7126", span, name=str(name),
                                known=", ".join(sorted(documents)) or "—"))

    def lookup(self, target_id: str) -> list[tuple[str, dict[str, Any]]]:
        """``(document name, registry entry)`` of every listed document that has ``target_id``."""
        found = []
        for name in self.names:
            entry = self._registry(name).get(target_id)
            if entry is not None:
                found.append((name, entry))
        return found

    def record(self, target_id: str, name: str) -> None:
        origin, path = self._origin.get(name, ("registry", ""))
        self.origins.append({"id": target_id, "document": name, "origin": origin, "registry": path})

    # ------------------------------------------------------------------

    def _registry(self, name: str) -> dict[str, Any]:
        if name in self._registries:
            return self._registries[name]
        root = self.project.root
        source, registry_text = self.project.ref_documents[name]
        registry_path = root / registry_text
        registry = _read(registry_path) if registry_text else None
        targets: dict[str, Any] = {}
        source_path = (root / source).resolve() if source else None
        if source_path is not None and source_path == self.current:
            pass  # a document is not its own reference source
        elif source_path is not None and source_path.is_file():
            if registry is not None and _fresh(registry, root):
                targets = registry["targets"]
                self._origin[name] = ("registry", registry_text)
            else:
                computed = self._compute(name, source, source_path, registry_path)
                if computed is not None:
                    targets = computed["targets"]
                    self._origin[name] = ("computed", registry_text)
        elif registry is not None:
            if source_path is not None:
                # The source is gone: the texts of the last registry, with a warning.
                self.sink.emit(warning("P7129", self.span, name=name, registry=registry_text))
            targets = registry["targets"]
            self._origin[name] = ("registry", registry_text)
        else:
            self.sink.emit(error("P7128", self.span, name=name, registry=registry_text or "—"))
        self._registries[name] = targets
        return targets

    def _compute(self, name: str, source: str, path: Path, registry_path: Path) -> dict[str, Any] | None:
        """Evaluate the referenced document to its structure; write its registry with ``build``."""
        from primula.frontend import analyze
        from primula.source import SourceManager

        if path in _ACTIVE:
            self.sink.emit(error("P7127", self.span, name=name, errors=0).hint("help.reference_cycle"))
            return None
        quiet = DiagnosticSink(error_limit=0)
        manager = SourceManager()
        _ACTIVE.add(path)
        try:
            result = analyze(path, quiet, manager, source, project=self.project)
        finally:
            _ACTIVE.discard(path)
        structure = getattr(result.evaluation, "structure", None) if result.evaluation is not None else None
        if quiet.has_errors or structure is None:
            self.sink.emit(error("P7127", self.span, name=name, errors=quiet.error_count))
            return None
        registry = make_registry(name, source, structure, source_files(manager, self.project.root))
        if self.write:
            write_registry(registry_path, registry)
        return registry
