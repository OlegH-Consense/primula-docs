"""Batch build of a project: ``primula build|check project.p.prml`` (10.7, 14.1; decision 117).

Order of work:

1. read the descriptive section of the project file (:mod:`primula.evaluate.project`);
   with ``check --dump-project`` print it as JSON and stop (no code is run);
2. run the code section with ``batch_mode() == True``; ``build(…)`` calls
   register targets after the ``targets`` of the header;
3. check every target before building anything: the source is a document
   of the project, the parameters and keys are declared, the types agree,
   the outputs lie inside the project and do not collide (ODT and PDF);
4. ``check`` stops here; ``build`` builds the targets one by one, each with
   its own diagnostics, and an error of one target does not stop the others.

``-o`` and ``--pdf FILE`` are errors for a project (P7120); ``--pdf``
without a value exports a PDF next to the ODT of every target.  The exit
code is 2 if the project or any target has errors.  With ``--report`` one
report is written: the project (file, parameters, keys) and the list of
targets with their own nested reports (14.3).
"""

from __future__ import annotations

import argparse
import datetime
import json
import time
from dataclasses import dataclass, field
from typing import Any, TextIO

from primula.diagnostics import DiagnosticSink, TooManyErrors, error, render_text, summary, to_json, warning
from primula.i18n import Catalog
from primula.source import SourceManager


@dataclass
class ProjectRun:
    """Outcome of a project command.

    Attributes:
        project: the loaded project, ``None`` if it could not be read.
        targets: one entry per target: ``source``, ``output``, ``pdf``,
            ``result`` (``ok``/``error``) and the nested ``report``.
        total: number of targets; failed: targets with errors.
    """

    project: Any
    targets: list[dict[str, Any]] = field(default_factory=list)
    total: int = 0
    failed: int = 0

    def info(self) -> dict[str, Any] | None:
        """The project part of the report (14.3): file, name, parameters, keys."""
        return project_info(self.project)


def project_info(project: Any) -> dict[str, Any] | None:
    """File, name, language, parameters and keys of a project for a report (14.3)."""
    if project is None:
        return None
    from primula.core.values import to_repr

    return {
        "file": project.source.name,
        "sha256": project.source.sha256,
        "name": project.name,
        "language": project.language,
        "params": {name: to_repr(value) for name, (value, _span) in project.params.items()},
        "keys": {name: text for name, (text, _span) in project.keys.items()},
    }


def run_project(args: argparse.Namespace, sink: DiagnosticSink, manager: SourceManager,
                err: TextIO, out: TextIO, catalog: Catalog) -> ProjectRun:
    """Run ``build`` or ``check`` for a project file (see the module description).

    Args:
        args: parsed command line arguments.
        sink: diagnostics of the project itself (header, code section, checks).
        manager: source manager of the project file.
        err: stream for diagnostics of the targets and informational lines.
        out: stream for ``--dump-project``.
        catalog: message catalogue.

    Returns:
        The :class:`ProjectRun`.
    """
    from primula.evaluate.project import check_outputs, check_target, dump_project, load_project

    project = load_project(args.file, manager, sink)
    run = ProjectRun(project)
    if args.command == "check" and getattr(args, "dump_project", False):
        print(json.dumps(dump_project(args.file, project, sink, catalog), ensure_ascii=False, indent=2), file=out)
        return run
    if project is None:
        return run
    if args.command == "build":
        if args.output is not None:
            sink.emit(error("P7120", None, at_file=str(args.file), option="-o"))
        if args.pdf is not None and args.pdf is not True:
            sink.emit(error("P7120", None, at_file=str(args.file), option="--pdf FILE"))
    if getattr(args, "param", None):
        sink.emit(error("P7125", None, at_file=str(args.file)))
    if sink.has_errors:
        return run
    targets = list(project.targets) + _run_code(args, project, sink, manager)
    # Errors of the code section stop the batch: the targets would repeat them.
    code_failed = sink.has_errors
    if not targets:
        sink.emit(warning("P7122", project.span()))
    usable = [check_target(project, target, sink, manager) for target in targets]
    colliding = check_outputs(project, targets, sink)
    usable = [ok and index not in colliding for index, ok in enumerate(usable)]
    run.total = len(targets)
    if args.command == "check" or code_failed:
        for target, ok in zip(targets, usable):
            run.targets.append({**_target_entry(target), "result": "ok" if ok and not code_failed else "error"})
        run.failed = sum(1 for entry in run.targets if entry["result"] == "error")
        return run
    for index, target in enumerate(targets):
        entry = _target_entry(target)
        print(catalog.text("cli.project.target", index=index + 1, source=target.source, output=target.output),
              file=err)
        if not usable[index]:
            entry["result"] = "error"
            run.failed += 1
            run.targets.append(entry)
            continue
        target_sink = DiagnosticSink(strict=args.strict)
        report = _build_target(args, project, target, target_sink, err, catalog)
        entry["result"] = "error" if target_sink.has_errors else "ok"
        entry["report"] = report
        run.failed += target_sink.has_errors
        run.targets.append(entry)
    return run


def _target_entry(target: Any) -> dict[str, Any]:
    return {"source": target.source, "output": target.output, "pdf": target.pdf_path(), "origin": target.origin}


def _run_code(args: argparse.Namespace, project: Any, sink: DiagnosticSink, manager: SourceManager) -> list[Any]:
    """Run the code section with ``batch_mode() == True``; return the ``build()`` targets."""
    from primula.core.limits import limit_memory, restore_memory_limit
    from primula.evaluate.evaluator import DocumentEvaluator, EvalOptions
    from primula.evaluate.loader import Loader

    collected: list[Any] = []
    timeout = getattr(args, "timeout", None)
    options = EvalOptions(build_date=getattr(args, "build_date", None) or project.build_date
                          or datetime.date.today(), project=project, batch=True, targets=collected,
                          limits=project.limits,
                          deadline=time.monotonic() + timeout if timeout is not None else None)
    loader = Loader(root=project.root, manager=manager, sink=sink)
    limit_memory()
    try:
        DocumentEvaluator(loader, sink, options).run_project()
    finally:
        restore_memory_limit()
    return collected


def _build_target(args: argparse.Namespace, project: Any, target: Any, sink: DiagnosticSink, err: TextIO,
                  catalog: Catalog) -> dict[str, Any]:
    """Build one target with its own diagnostics; print them; return its report."""
    from primula.cli import _options_for_report, write_outputs
    from primula.frontend import analyze
    from primula.report import make_report

    manager = SourceManager()
    source = project.root / target.source
    output = project.root / target.output
    pdf_text = target.pdf_path()
    pdf = project.root / pdf_text if pdf_text is not None else (output.with_suffix(".pdf") if args.pdf is True
                                                                else None)
    result = None
    stopped = None
    try:
        result = analyze(source, sink, manager, target.source, build_date=getattr(args, "build_date", None),
                         review=bool(getattr(args, "review", False)), styles=list(getattr(args, "style", []) or []),
                         timeout=getattr(args, "timeout", None), project=project, target=target, batch=True,
                         write_registry=True)
        write_outputs(result, sink, manager, catalog, output, pdf, err,
                      build_date=getattr(args, "build_date", None), embed_report=not args.no_embed_report,
                      embed_sources=args.embed_sources)
    except TooManyErrors as exc:
        stopped = catalog.text("cli.too_many_errors", limit=exc.args[0])
    except MemoryError:
        sink.emit(error("P0005", None, at_file=target.source))
    except Exception as exc:  # noqa: BLE001 - an internal failure of one target is P0002 of that target
        sink.emit(error("P0002", None, at_file=target.source,
                        detail=f"{type(exc).__name__}: {exc}").hint("help.internal"))
    if getattr(args, "format", "text") == "json":
        # --format json (П7): one array for the project and all targets, written by the CLI.
        args.json_messages.extend(to_json(diagnostic, catalog) for diagnostic in sink.ordered())
    else:
        for diagnostic in sink.ordered():
            print(render_text(diagnostic, catalog), file=err)
    if stopped is not None:
        print(stopped, file=err)
    print(summary(sink, catalog, target.source), file=err)
    options = {**_options_for_report(args), "output": str(output), "pdf": str(pdf) if pdf else None}
    report = make_report(command=args.command, result=result, sink=sink, manager=manager, catalog=catalog,
                         options=options, build_date=getattr(args, "build_date", None) or project.build_date
                         or datetime.date.today())
    report["target"] = {"source": target.source, "params": _params(target.params), "keys": dict(target.keys)}
    return report


def _params(values: dict[str, Any]) -> dict[str, str]:
    from primula.core.values import to_repr

    return {name: to_repr(value) for name, value in values.items()}

