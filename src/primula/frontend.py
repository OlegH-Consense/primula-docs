"""Front end of the processing pipeline (specification section 3.8).

The pipeline phases are: lexical pass (header, normalisation, comments,
verbatim and code blocks, balance) -> document tree -> collecting
definitions -> evaluation, variant selection, numbering, formulas -> ODT.

Implemented so far: reading the root file (UTF-8, LF, NFC —
:mod:`primula.source`), the YAML header (:mod:`primula.header`, stage
13.0) and parsing into the document tree (:mod:`primula.syntax`, stage
13.1).  Later stages extend :func:`analyze` with evaluation (13.3) and ODT
generation (13.5); :data:`PHASES` lists the phases and
:class:`FrontendResult.phases` records which of them ran, so the CLI and
the build report state honestly what was checked.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import datetime
import time
from dataclasses import replace

from primula.core.check import check_document
from primula.core.limits import limit_memory, restore_memory_limit
from primula.diagnostics import DiagnosticSink, error
from primula.evaluate.evaluator import DocumentEvaluator, EvalOptions, EvaluationResult
from primula.evaluate.loader import LoadedFile, Loader
from primula.header import Header, parse_header
from primula.source import SourceDecodeError, SourceFile, SourceManager, SourceReadError, Span
from primula.pages import build_pages
from primula.structure import build_structure
from primula.syntax.nodes import Document
from primula.syntax import regions
from primula.syntax.parser import CODE_KINDS, parse

#: Phase names in pipeline order (used in the build report).
PHASES: tuple[str, ...] = ("source", "header", "parse", "definitions", "evaluate", "structure", "pages", "odf")

#: Phase states recorded in :attr:`FrontendResult.phases`.
DONE = "done"
FAILED = "failed"
NOT_IMPLEMENTED = "not-implemented"
SKIPPED = "skipped"


@dataclass
class FrontendResult:
    """Outcome of the front end for one root file.

    Attributes:
        path: the requested path.
        source: the loaded source, ``None`` if it could not be read.
        header: the header, ``None`` if the source was not loaded.
        document: the document tree, ``None`` if parsing did not run.
        evaluation: the evaluated document (stage 13.3), ``None`` if
            evaluation did not run.
        phases: phase name -> state (``done``, ``failed``,
            ``not-implemented``, ``skipped``).
    """

    path: Path
    source: SourceFile | None = None
    header: Header | None = None
    document: Document | None = None
    evaluation: EvaluationResult | None = None
    phases: dict[str, str] = field(default_factory=dict)
    #: The project of the document (10.6), or ``None``.
    project: Any = None


def load_root(path: Path, sink: DiagnosticSink, manager: SourceManager,
              name: str | None = None) -> SourceFile | None:
    """Load a root source file, reporting read and decoding errors.

    Args:
        path: file path.
        sink: diagnostics receiver.
        manager: source manager that keeps the file.
        name: display name; defaults to the path as given.

    Returns:
        The source file or ``None`` after an error (P0101, P0102).
    """
    display = name if name is not None else str(path)
    try:
        return manager.load(path, display)
    except SourceReadError as exc:
        sink.emit(error("P0101", None, at_file=display, path=display, reason=exc.reason))
    except SourceDecodeError as exc:
        manager.add(exc.partial)
        sink.emit(error("P0102", Span(exc.partial, exc.offset, exc.offset),
                        byte_offset=exc.byte_offset).hint("help.utf8"))
    return None


def _write_own_registry(project: Any, path: Path, manager: SourceManager, structure: Any) -> None:
    """``build`` of a document named in ``ref_documents`` of the project writes its registry (decision 121)."""
    from primula.xrefs import make_registry, source_files, write_registry

    for name, (source, registry) in project.ref_documents.items():
        if source and (project.root / source).resolve() == path.resolve() and registry:
            write_registry(project.root / registry,
                           make_registry(name, source, structure, source_files(manager, project.root)))


def analyze(path: Path, sink: DiagnosticSink, manager: SourceManager,
            name: str | None = None, *, build_date: datetime.date | None = None,
            review: bool = False, styles: list[Path] | None = None,
            timeout: float | None = None, project: Any = None, target: Any = None,
            batch: bool = False, params: dict[str, tuple[Any, str]] | None = None,
            write_registry: bool = False) -> FrontendResult:
    """Run the implemented front-end phases for a root file.

    Args:
        path: root file path.
        sink: diagnostics receiver.
        manager: source manager.
        name: display name of the file.
        build_date: value of ``build_date()`` (``--build-date``).
        review: ``--review`` mode (9.2).
        styles: styles modules of ``--style`` in the given order (11.7,
            decision 106), paths relative to the current directory.
        timeout: limit of the whole build in seconds (``--timeout``, 12.8).
        project: the project (:class:`~primula.evaluate.project.Project`,
            10.6) or ``None``: its root, parameters, keys, styles, limits.
        target: the build target of a batch build (10.7) or ``None``.
        batch: value of ``batch_mode()`` (``primula build project.p.prml``).
        params: ``--param`` values of the root document: name -> (value,
            text as written) (14.1, П2).
        write_registry: ``build`` — write the reference registry of a named
            document of the project and refresh stale registries of the
            documents in ``references:`` (decision 121); ``check`` writes nothing.

    Returns:
        The front-end result; errors are in ``sink``.
    """
    result = FrontendResult(path, project=project)
    for phase in PHASES:
        result.phases[phase] = SKIPPED

    result.source = load_root(path, sink, manager, name)
    if result.source is None:
        result.phases["source"] = FAILED
        return result
    result.phases["source"] = DONE

    errors_before = sink.error_count
    result.header = parse_header(result.source, sink)
    result.phases["header"] = FAILED if sink.error_count > errors_before else DONE

    errors_before = sink.error_count
    # Parse once without regions: the flat tree is what evaluation needs
    # (regions are built after fragments are inserted, decision 31).
    flat = parse(result.header, sink, organize=False)
    # Whitelist of the computing core (12.2) over every Python fragment.
    for problem in check_document(flat):
        sink.emit(problem)
    parse_failed = sink.error_count > errors_before
    evaluate = not parse_failed and result.header.kind in ("document", "fragment")
    # The organised tree (for --dump-parsed and when evaluation does not
    # run) reports list errors only if evaluation will not report them on
    # the evaluated tree.
    organize_sink = DiagnosticSink(error_limit=0) if evaluate else sink
    result.document = replace(flat, children=regions.organize(flat.children, organize_sink)) \
        if result.header.kind not in CODE_KINDS else flat
    result.phases["parse"] = FAILED if sink.error_count > errors_before else DONE

    result.phases["odf"] = NOT_IMPLEMENTED
    if not evaluate:
        # Syntax errors would cause cascades; styles modules and projects
        # are evaluated by stages 13.4 and 13.11, a module by its importer.
        result.phases["definitions"] = result.phases["evaluate"] = SKIPPED
        return result

    # Evaluation (stage 13.3).
    source, header = result.source, result.header
    root = project.root if project is not None else path.resolve().parent
    loader = Loader(root=root, manager=manager, sink=sink)
    loaded = LoadedFile(path.resolve(), source, header, flat)
    loader._files[loaded.path] = loaded
    deadline = time.monotonic() + timeout if timeout is not None else None
    options = EvalOptions(build_date=build_date or (project.build_date if project is not None else None)
                          or datetime.date.today(), review=review,
                          styles=[Path(p) for p in styles or []], deadline=deadline,
                          project=project, target=target, batch=batch, params=dict(params or {}))
    if project is not None:
        options.limits = project.limits
    errors_before = sink.error_count
    # The memory limit of 12.8 covers the evaluation only.
    limit_memory()
    try:
        result.evaluation = DocumentEvaluator(loader, sink, options).evaluate(loaded)
    finally:
        restore_memory_limit()
    state = FAILED if sink.error_count > errors_before else DONE
    result.phases["definitions"] = result.phases["evaluate"] = state
    if state == FAILED or result.header.kind != "document":
        # Structure errors after evaluation errors would be cascades; a
        # fragment built on its own is checked, not numbered.
        result.phases["structure"] = result.phases["pages"] = SKIPPED
        return result

    # Structure (stage 13.6): numbering, IDs, references, notes, indexes.
    errors_before = sink.error_count
    external = None
    references = header.data.get("references")
    if references:
        # Targets of other documents of the project (5.7, decision 121).
        from primula.xrefs import ExternalReferences

        external = ExternalReferences(project, list(references), sink,
                                      header.value_span(("references",), key=True), path.resolve(),
                                      write_registry)
    build_structure(result.evaluation, header.data, sink, review=review, external=external)
    result.evaluation.external_references = external.origins if external is not None else []
    result.phases["structure"] = FAILED if sink.error_count > errors_before else DONE
    if write_registry and project is not None and sink.error_count == errors_before:
        _write_own_registry(project, path, manager, result.evaluation.structure)

    # Pages and graphics (stage 13.8): page changes, sections, headers, frames.
    errors_before = sink.error_count
    build_pages(result.evaluation, sink)
    result.phases["pages"] = FAILED if sink.error_count > errors_before else DONE
    return result
