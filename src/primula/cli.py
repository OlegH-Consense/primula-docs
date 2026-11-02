"""Command line interface ``primula`` (specification section 14.1).

Commands::

    primula build FILE [-o result.odt] [--strict] [--report r.json] [--review]
                       [--build-date YYYY-MM-DD] [--unsafe] [--pdf [FILE]]
    primula check FILE [--strict] [--report r.json] [--review]
                       [--build-date YYYY-MM-DD] [--unsafe]
    primula fmt FILE   [--explicit-clauses]

Common options: ``--lang en|uk|ru`` (language of messages, default from the
environment), ``--debug`` (traceback of internal errors), ``--version``.

Exit codes (section 14.1): 0 — success, 2 — build error.  Usage errors
reported by :mod:`argparse` also exit with 2; an internal error of the
translator is reported as diagnostic P0002 and exits with 2.

State at prototype stage 13.1:

* ``check`` reads the file (UTF-8, normalisation), checks the YAML header,
  parses the body and evaluates the document (stage 13.3: fragments,
  modules, macros, data); ``--dump-tree`` prints the evaluated tree
  (``--dump-parsed`` — the tree after parsing);
* ``build`` writes the ODT (stage 13.5) unless there are errors, with
  ``--pdf`` also a PDF through LibreOffice; ``--embed-sources`` and
  ``--no-embed-report`` control the embedded parts (decision 67);
* ``fmt`` runs the checks and reports P0001 (formatter: stage 13.13).

Diagnostics and the summary go to stderr; stdout is reserved for command
output (``fmt`` to stdout, later stages).
"""

from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
import traceback
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any, TextIO

from primula import PROTOTYPE_STAGE, __version__
from primula.diagnostics import DiagnosticSink, TooManyErrors, error, render_text, summary, to_json, warning
from primula.frontend import DONE, FAILED, SKIPPED, FrontendResult, analyze
from primula.i18n import SUPPORTED_LANGUAGES, Catalog, detect_language
from primula.report import make_report, write_report
from primula.source import SourceManager, set_overlays
from primula.syntax.nodes import dump
from primula.odf.package import write_file
from primula.odf.pdf import PdfError, export_pdf
from primula.odf.writer import OdtOptions, build_odt

#: Exit code of a successful run.
EXIT_OK = 0
#: Exit code of a build error (section 14.1).
EXIT_ERROR = 2

_DATE_PATTERN = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")


def _prescan_language(argv: Sequence[str]) -> str | None:
    """Find ``--lang`` before full parsing, so that help texts are localised.

    Args:
        argv: command line arguments without the program name.

    Returns:
        The requested language or ``None``.
    """
    for index, item in enumerate(argv):
        if item == "--lang" and index + 1 < len(argv):
            return argv[index + 1]
        if item.startswith("--lang="):
            return item.split("=", 1)[1]
    return None


def _date_type(catalog: Catalog) -> Callable[[str], datetime.date]:
    """Return an argparse type converter for ``--build-date``."""

    def convert(value: str) -> datetime.date:
        if _DATE_PATTERN.match(value):
            try:
                return datetime.date.fromisoformat(value)
            except ValueError:
                pass
        raise argparse.ArgumentTypeError(catalog.text("cli.error.build_date", value=value))

    return convert


def _seconds_type(catalog: Catalog) -> Callable[[str], float]:
    """Return an argparse type converter for ``--timeout`` (positive seconds)."""

    def convert(value: str) -> float:
        try:
            seconds = float(value)
        except ValueError:
            seconds = -1.0
        if seconds > 0:
            return seconds
        raise argparse.ArgumentTypeError(catalog.text("cli.error.timeout", value=value))

    return convert


#: argparse's own texts (``argparse._`` is gettext) -> catalogue keys.
_ARGPARSE_TEXTS = {
    "usage: ": "argparse.usage",
    "options": "argparse.options",
    "positional arguments": "argparse.positional",
    "show this help message and exit": "argparse.help",
    "%(prog)s: error: %(message)s\n": "argparse.error",
    "invalid choice: %(value)r (choose from %(choices)s)": "argparse.invalid_choice",
    "the following arguments are required: %s": "argparse.required",
    "unrecognized arguments: %s": "argparse.unrecognized",
    "expected one argument": "argparse.expected_one",
    "argument %(argument_name)s: %(message)s": "argparse.argument",
    "not allowed with argument %s": "argparse.not_allowed",
    "ambiguous option: %(option)s could match %(matches)s": "argparse.ambiguous",
    "invalid %(type)s value: %(value)r": "argparse.invalid_value",
}


def _localize_argparse(catalog: Catalog) -> None:
    """Translate the texts argparse writes itself (``usage:``, ``options``, its errors).

    argparse takes them through the module-level gettext function ``_``;
    it is replaced by a lookup in the message catalogue (unknown texts stay
    English).  See https://docs.python.org/3/library/argparse.html.
    """
    def translate(text: str) -> str:
        key = _ARGPARSE_TEXTS.get(text)
        return catalog.text(key) if key is not None else text

    argparse._ = translate  # type: ignore[attr-defined]


def build_parser(catalog: Catalog) -> argparse.ArgumentParser:
    """Create the argument parser with texts from the message catalogue.

    Args:
        catalog: catalogue of the interface language.

    Returns:
        The configured parser.
    """
    t = catalog.text
    # Before any parser is made: group titles ("options") are taken at creation.
    _localize_argparse(catalog)
    file_ = t("cli.metavar.file")

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--strict", action="store_true", help=t("cli.help.strict"))
    common.add_argument("--report", type=Path, metavar=file_, help=t("cli.help.report"))
    common.add_argument("--lang", choices=SUPPORTED_LANGUAGES, help=t("cli.help.lang"))
    common.add_argument("--debug", action="store_true", help=t("cli.help.debug"))
    # Machine-readable messages for editors and Studio (14.1, 14.2; П7).
    common.add_argument("--format", choices=("text", "json"), default="text", help=t("cli.help.format"))

    evaluation = argparse.ArgumentParser(add_help=False)
    evaluation.add_argument("--review", action="store_true", help=t("cli.help.review"))
    evaluation.add_argument("--build-date", type=_date_type(catalog), metavar=t("cli.metavar.date"),
                            help=t("cli.help.build_date"))
    evaluation.add_argument("--unsafe", action="store_true", help=t("cli.help.unsafe"))
    # Additional styles modules, repeatable (11.7, 14.1; decision 106).
    evaluation.add_argument("--style", action="append", default=[], metavar=file_,
                            help=t("cli.help.style"))
    # Parameters of the root document, repeatable (14.1, П2).
    evaluation.add_argument("--param", action="append", default=[], metavar=t("cli.metavar.param"),
                            help=t("cli.help.param"))
    evaluation.add_argument("--timeout", type=_seconds_type(catalog), metavar=t("cli.metavar.seconds"),
                            help=t("cli.help.timeout"))
    # The project file (10.6, 14.1; decision 117).
    project = evaluation.add_mutually_exclusive_group()
    project.add_argument("--project", type=Path, metavar=file_, help=t("cli.help.project"))
    project.add_argument("--no-project", action="store_true", help=t("cli.help.no_project"))

    # Long help (description, epilog with options, examples, exit codes) keeps its line breaks.
    raw = argparse.RawDescriptionHelpFormatter
    parser = argparse.ArgumentParser(prog="primula", description=t("cli.description"),
                                     epilog=t("cli.epilog.main"), formatter_class=raw)
    parser.add_argument("--version", action="version",
                        version=f"primula-docs {__version__} (stage {PROTOTYPE_STAGE})",
                        help=t("cli.help.version"))
    # --lang also before the command ("primula --lang uk --help"); the
    # language is taken by _prescan_language before parsing.
    parser.add_argument("--lang", dest="top_lang", choices=SUPPORTED_LANGUAGES, help=t("cli.help.lang"))
    commands = parser.add_subparsers(dest="command", metavar=t("cli.metavar.command"),
                                     title=t("cli.help.command"), required=True)

    build = commands.add_parser("build", parents=[common, evaluation], help=t("cli.help.build"),
                                description=t("cli.help.build"), epilog=t("cli.epilog.build"),
                                formatter_class=raw)
    build.add_argument("file", type=Path, metavar=file_, help=t("cli.help.file"))
    build.add_argument("-o", "--output", type=Path, metavar=file_, help=t("cli.help.output"))
    build.add_argument("--pdf", nargs="?", const=True, default=None, metavar=file_,
                       help=t("cli.help.pdf"))
    build.add_argument("--embed-sources", action="store_true", help=t("cli.help.embed_sources"))
    build.add_argument("--no-embed-report", action="store_true", help=t("cli.help.no_embed_report"))

    check = commands.add_parser("check", parents=[common, evaluation], help=t("cli.help.check"),
                                description=t("cli.help.check"), epilog=t("cli.epilog.check"),
                                formatter_class=raw)
    check.add_argument("file", type=Path, metavar=file_, help=t("cli.help.file"))
    check.add_argument("--dump-tree", action="store_true", help=t("cli.help.dump_tree"))
    check.add_argument("--dump-parsed", action="store_true", help=t("cli.help.dump_parsed"))
    check.add_argument("--dump-project", action="store_true", help=t("cli.help.dump_project"))
    # Structure and styles for editors and Primula Studio (14.1; stage 14.2, Т1, Т2).
    check.add_argument("--dump-structure", action="store_true", help=t("cli.help.dump_structure"))
    check.add_argument("--dump-styles", action="store_true", help=t("cli.help.dump_styles"))
    # Unsaved editor buffers: the text of FILE is read from BUFFER (Т3).
    check.add_argument("--overlay", action="append", default=[], metavar=t("cli.metavar.overlay"),
                       help=t("cli.help.overlay"))

    # The catalogue of constructs for editors and Studio (Т5).
    catalogue = commands.add_parser("commands", help=t("cli.help.commands"), description=t("cli.help.commands"),
                                    epilog=t("cli.epilog.commands"), formatter_class=raw)
    catalogue.add_argument("--format", choices=("text", "json"), default="text", help=t("cli.help.commands_format"))
    catalogue.add_argument("--lang", choices=SUPPORTED_LANGUAGES, help=t("cli.help.lang"))
    catalogue.add_argument("--functions", action="store_true", help=t("cli.help.commands_functions"))
    catalogue.add_argument("--header", action="store_true", help=t("cli.help.commands_header"))

    # The evaluator console (stage 14.15; decision 128).
    console = commands.add_parser("console", parents=[evaluation], help=t("cli.help.console"),
                                  description=t("cli.help.console"), epilog=t("cli.epilog.console"),
                                  formatter_class=raw)
    console.add_argument("file", type=Path, nargs="?", metavar=file_, help=t("cli.help.console_file"))
    console.add_argument("--lang", choices=SUPPORTED_LANGUAGES, help=t("cli.help.lang"))
    console.add_argument("--json", action="store_true", help=t("cli.help.console_json"))

    # Blanks, confirmation and status of the track blocks of |parallel (7.7, 14.1; stage 16.5).
    parallel = commands.add_parser("parallel", parents=[common, evaluation], help=t("cli.help.parallel"),
                                   description=t("cli.help.parallel"), epilog=t("cli.epilog.parallel"),
                                   formatter_class=raw)
    parallel.add_argument("file", type=Path, metavar=file_, help=t("cli.help.file"))
    action = parallel.add_mutually_exclusive_group(required=True)
    action.add_argument("--stub", action="store_true", help=t("cli.help.parallel_stub"))
    action.add_argument("--stamp", action="store_true", help=t("cli.help.parallel_stamp"))
    action.add_argument("--check-status", metavar=t("cli.metavar.status"), help=t("cli.help.parallel_check"))
    parallel.add_argument("--track", metavar="ID", help=t("cli.help.parallel_track"))
    parallel.add_argument("--segment", action="append", default=[], metavar="ID",
                          help=t("cli.help.parallel_segment"))
    parallel.add_argument("--status", metavar=t("cli.metavar.status"), help=t("cli.help.parallel_status"))

    # Export through the pandoc AST (stage 19.1, decision 139).
    export = commands.add_parser("export", parents=[common, evaluation], help=t("cli.help.export"),
                                 description=t("cli.help.export"), epilog=t("cli.epilog.export"),
                                 formatter_class=raw)
    export.add_argument("file", type=Path, metavar=file_, help=t("cli.help.file"))
    export.add_argument("--to", default="markdown", metavar=t("cli.metavar.format"), help=t("cli.help.export_to"))
    export.add_argument("-o", "--output", type=Path, metavar=file_, help=t("cli.help.export_output"))
    export.add_argument("--pandoc-arg", action="append", default=[], metavar=t("cli.metavar.argument"),
                        help=t("cli.help.export_pandoc_arg"))

    # Quick view of the built document, for F3 of a file manager (stage 24.1).
    view = commands.add_parser("view", parents=[evaluation], help=t("cli.help.view"),
                               description=t("cli.help.view"), epilog=t("cli.epilog.view"),
                               formatter_class=raw)
    view.add_argument("file", type=Path, metavar=file_, help=t("cli.help.file"))
    view.add_argument("--lang", choices=SUPPORTED_LANGUAGES, help=t("cli.help.lang"))
    view.add_argument("--viewer", metavar=t("cli.metavar.command"), help=t("cli.help.view_viewer"))
    view.add_argument("--text", action="store_true", help=t("cli.help.view_text"))
    view.add_argument("--keep", action="store_true", help=t("cli.help.view_keep"))

    # Summary of a file without an output document: module, styles, project (stage 18.9).
    describe = commands.add_parser("describe", help=t("cli.help.describe"), description=t("cli.help.describe"),
                                   epilog=t("cli.epilog.describe"), formatter_class=raw)
    describe.add_argument("file", type=Path, metavar=file_, help=t("cli.help.file"))
    describe.add_argument("--lang", choices=SUPPORTED_LANGUAGES, help=t("cli.help.lang"))
    describe.add_argument("--format", choices=("text", "json"), default="text", help=t("cli.help.format"))

    fmt = commands.add_parser("fmt", parents=[common], help=t("cli.help.fmt"),
                              description=t("cli.help.fmt"), epilog=t("cli.epilog.fmt"),
                              formatter_class=raw)
    fmt.add_argument("file", type=Path, metavar=file_, help=t("cli.help.file"))
    fmt.add_argument("--explicit-clauses", action="store_true",
                     help=t("cli.help.explicit_clauses"))
    return parser


def _options_for_report(args: argparse.Namespace) -> dict[str, object]:
    """Collect options that affect the result, in JSON-compatible form."""
    options: dict[str, object] = {"strict": args.strict}
    for name in ("review", "unsafe", "explicit_clauses", "style", "timeout", "no_project", "param"):
        if hasattr(args, name):
            options[name] = getattr(args, name)
    if getattr(args, "output", None) is not None or (args.command == "build" and not _is_project(args)):
        options["output"] = str(_output_path(args))
    if getattr(args, "pdf", None) is not None:
        options["pdf"] = True if args.pdf is True else str(args.pdf)
    return options


def _param_options(args: argparse.Namespace, sink: DiagnosticSink) -> dict[str, tuple[Any, str]]:
    """``--param NAME=VALUE`` options: name -> (value, text as written); P7123 for a bad one."""
    from primula.evaluate.project import parse_param_option

    params: dict[str, tuple[Any, str]] = {}
    for text in getattr(args, "param", None) or []:
        parsed = parse_param_option(text)
        if parsed is None:
            sink.emit(error("P7123", None, at_file=str(args.file), text=text))
            continue
        name, value, plain = parsed
        params[name] = (value, plain)
    return params


def _console(args: argparse.Namespace, catalog: Catalog, err: TextIO, out: TextIO, inp: TextIO) -> int:
    """``primula console [FILE]`` (decision 128): a session in the context of FILE.

    The project is the file itself for a project file, otherwise ``--project``
    or the one found upwards from FILE (or the current directory).
    """
    from primula.console import ConsoleSession, run_console
    from primula.evaluate.project import find_project, is_project_file, load_project

    sink = DiagnosticSink(error_limit=0)
    manager = SourceManager()
    path: Path | None = args.file
    if path is not None and not path.is_file():
        print(render_text(error("P0101", None, at_file=str(path), path=str(path), reason="not a file"), catalog),
              file=err)
        return EXIT_ERROR
    project = None
    if path is not None and is_project_file(path):
        project = load_project(path, manager, sink)
    elif not args.no_project:
        found = args.project or find_project(path if path is not None else Path.cwd() / "console.prml")
        if found is not None and (path is None or found.resolve() != path.resolve()):
            project = load_project(found, manager, sink)
    args.file = path if path is not None else Path("<console>")
    session = ConsoleSession(path, catalog, manager, project=project, params=_param_options(args, sink),
                             build_date=args.build_date, styles=[Path(p) for p in args.style])
    session.ready_messages[:0] = sink.diagnostics
    return run_console(session, inp, out, as_json=args.json)


def _overlays(args: argparse.Namespace, sink: DiagnosticSink) -> dict[Path, Path]:
    """``--overlay FILE=BUFFER`` options (Т3): source path -> buffer path; P0105 for a bad one.

    The text is split at the last ``=``: the buffer is a temporary file
    made by the editor, the source path may itself contain ``=``.
    """
    overlays: dict[Path, Path] = {}
    for text in getattr(args, "overlay", None) or []:
        source, separator, buffer = text.rpartition("=")
        if not separator or not source or not buffer or not Path(buffer).is_file():
            sink.emit(error("P0105", None, at_file=str(args.file), text=text))
            continue
        overlays[Path(source)] = Path(buffer)
    return overlays


def _is_project(args: argparse.Namespace) -> bool:
    from primula.evaluate.project import is_project_file

    return is_project_file(args.file)


def _output_path(args: argparse.Namespace) -> Path:
    """Return the ODT output path: ``-o`` or the source name with ``.odt``."""
    output = getattr(args, "output", None)
    return output if output is not None else args.file.with_suffix(".odt")


def _find_project(args: argparse.Namespace, sink: DiagnosticSink, manager: SourceManager,
                  err: TextIO, catalog: Catalog) -> Any:
    """The project of the root document (10.6): ``--project``, the search upwards, or none.

    The project file found is named in an informational line (decision 117),
    so that an unexpected ``project.p.prml`` in a parent directory is seen.
    """
    from primula.evaluate.project import find_project, load_project

    if args.command == "fmt" or getattr(args, "no_project", False):
        return None
    path = getattr(args, "project", None) or find_project(args.file)
    if path is None:
        return None
    if getattr(args, "project", None) is None and path.resolve() == args.file.resolve():
        # A file named project.p.prml whose kind is not project (decision 118)
        # is built as what its kind says; it is not its own project.
        return None
    project = load_project(path, manager, sink)
    if project is None:
        return None
    print(catalog.text("cli.project.found", file=str(path)), file=err)
    if not project.contains(args.file):
        sink.emit(error("P7119", None, at_file=str(args.file), path=str(args.file), project=str(path)))
    return project


def _run_command(args: argparse.Namespace, sink: DiagnosticSink, manager: SourceManager,
                 err: TextIO, out: TextIO, catalog: Catalog) -> Any:
    """Execute the selected command (front end + stage-specific part).

    Args:
        args: parsed arguments.
        sink: diagnostics receiver.
        manager: source manager.
        err: stream for informational lines.
        out: stream for command output (``--dump-tree``).
        catalog: message catalogue.

    Returns:
        The front-end result, or a :class:`~primula.batch.ProjectRun` for a
        project file.
    """
    from primula.evaluate.project import is_project_file

    dumps = bool(getattr(args, "dump_structure", False) or getattr(args, "dump_styles", False))
    if args.command in ("build", "check") and is_project_file(args.file):
        if dumps:
            # The structure and the styles belong to a document (Studio asks for each one).
            sink.emit(error("P7132", None, at_file=str(args.file)))
            return None
        from primula.batch import run_project

        return run_project(args, sink, manager, err, out, catalog)
    if getattr(args, "dump_project", False):
        sink.emit(error("P7121", None, at_file=str(args.file)))
        return None
    project = _find_project(args, sink, manager, err, catalog)
    result = analyze(args.file, sink, manager, build_date=getattr(args, "build_date", None),
                     review=bool(getattr(args, "review", False)),
                     styles=list(getattr(args, "style", []) or []),
                     timeout=getattr(args, "timeout", None), project=project,
                     params=_param_options(args, sink), write_registry=args.command == "build")
    if args.command == "check":
        if result.source is not None:
            print(catalog.text("cli.check.partial", file=result.source.name,
                               stage=PROTOTYPE_STAGE), file=err)
        if args.dump_tree or args.dump_parsed:
            tree = result.document
            if args.dump_tree and result.evaluation is not None:
                tree = result.evaluation.document
            if tree is not None:
                print(dump(tree), file=out)
        if dumps:
            # Printed by main() after the run, with the messages of the whole run.
            args.dump_result = result
    elif args.command == "build":
        _build(args, result, sink, manager, err, catalog)
    elif args.command == "export":
        _export(args, result, sink, err, catalog)
    elif args.command == "parallel":
        from primula.parallel.tool import run as run_parallel

        # With --format json stdout holds the JSON messages: the report lines go to stderr.
        run_parallel(args, result, sink, err if args.format == "json" else out, catalog)
    else:
        # fmt: the formatter comes at stage 13.13.
        sink.emit(error("P0001", None, at_file=str(args.file), command=args.command,
                        stage=PROTOTYPE_STAGE))
    return result


def _build(args: argparse.Namespace, result: FrontendResult, sink: DiagnosticSink, manager: SourceManager,
           err: TextIO, catalog: Catalog) -> None:
    """Write the ODT (and PDF) of an evaluated document (stage 13.5).

    Nothing is written when the build has errors (0.3); warnings become
    errors with ``--strict`` and then stop the build as well.
    """
    output = _output_path(args)
    pdf = None if args.pdf is None else (output.with_suffix(".pdf") if args.pdf is True else Path(args.pdf))
    write_outputs(result, sink, manager, catalog, output, pdf, err,
                  build_date=getattr(args, "build_date", None), embed_report=not args.no_embed_report,
                  embed_sources=args.embed_sources)


def _export(args: argparse.Namespace, result: FrontendResult, sink: DiagnosticSink, err: TextIO,
            catalog: Catalog) -> None:
    """Write the document through the pandoc AST (stage 19.1, decision 139).

    ``--to json`` writes the AST; other formats are made by pandoc. Nothing
    is written when the document has errors.
    """
    import json

    from primula.export.pandoc import ALIASES, EXTENSIONS, STYLED, PandocWriter, run_pandoc
    from primula.structure.settings import document_language

    if sink.has_errors or result.evaluation is None:
        return
    fmt = ALIASES.get(args.to, args.to)
    output = args.output or args.file.with_suffix("." + EXTENSIONS.get(args.to, EXTENSIONS.get(fmt, fmt)))
    evaluation = result.evaluation
    header = result.header
    language = document_language(header.data, evaluation.styles.defaults, getattr(evaluation, "project_language", None))
    metadata = header.data.get("doc") or {}
    metadata = {**(getattr(evaluation, "document_defaults", None) or {}),
                **(metadata if isinstance(metadata, dict) else {})}
    project = getattr(result, "project", None)
    root = project.root if project is not None else result.path.resolve().parent
    writer = PandocWriter(language, sink, output.parent, styles=fmt in STYLED, root=root)
    ast = json.dumps(writer.document(evaluation.document, metadata), ensure_ascii=False)
    if sink.has_errors:
        return
    try:
        output.parent.mkdir(parents=True, exist_ok=True)
        if fmt == "json":
            output.write_text(ast + "\n", encoding="utf-8")
        elif not run_pandoc(ast, fmt, output, args.file.resolve().parent, sink, args.pandoc_arg):
            return
    except OSError as exc:
        sink.emit(error("P0103", None, at_file=str(output), path=str(output), reason=exc.strerror or str(exc)))
        return
    print(catalog.text("cli.build.written", file=str(output)), file=err)


def write_outputs(result: FrontendResult, sink: DiagnosticSink, manager: SourceManager, catalog: Catalog,
                  output: Path, pdf: Path | None, err: TextIO, *, build_date: datetime.date | None,
                  embed_report: bool, embed_sources: bool) -> None:
    """Write the ODT and, optionally, the PDF of an evaluated document.

    Args:
        result: the front-end result.
        sink: diagnostics receiver.
        manager: source manager (embedded report and sources).
        catalog: message catalogue.
        output: ODT path.
        pdf: PDF path or ``None``.
        err: stream for the "written" lines.
        build_date: ``--build-date`` (else the project's or today).
        embed_report: embed the short report (decision 67).
        embed_sources: embed the sources.
    """
    if sink.has_errors or result.evaluation is None:
        result.phases["odf"] = SKIPPED
        return
    # Until the ODT (and the PDF) is written the phase counts as failed;
    # the report written after the build records the final state.
    result.phases["odf"] = FAILED
    project = getattr(result, "project", None)
    root = project.root if project is not None else result.path.resolve().parent
    if build_date is None and project is not None:
        build_date = project.build_date
    options = OdtOptions(build_date=build_date or datetime.date.today(),
                         embed_report=embed_report, embed_sources=embed_sources)
    data = build_odt(result, sink, manager, root, catalog, options)
    if sink.has_errors:  # P8xxx warnings with --strict
        return
    try:
        output.parent.mkdir(parents=True, exist_ok=True)
        write_file(output, data)
    except OSError as exc:
        sink.emit(error("P8002", None, at_file=str(output), path=str(output), reason=exc.strerror or str(exc)))
        return
    print(catalog.text("cli.build.written", file=str(output)), file=err)
    if pdf is None:
        result.phases["odf"] = DONE
        return
    target = pdf
    try:
        not_updated = export_pdf(output, target, update=_needs_layout(result))
    except PdfError as exc:
        if exc.reason == "missing":
            sink.emit(error("P8003", None, at_file=str(target)))
        else:
            sink.emit(error("P8004", None, at_file=str(target), reason=exc.reason))
        return
    if not_updated is not None:
        sink.emit(warning("P8008", None, at_file=str(target), reason=not_updated))
    print(catalog.text("cli.build.written", file=str(target)), file=err)
    result.phases["odf"] = DONE


def _needs_layout(result: FrontendResult) -> bool:
    """Whether the PDF needs Writer page numbers: indexes or ``page`` references (5.7, 5.9)."""
    structure = getattr(result.evaluation, "structure", None)
    if structure is None:
        return False
    if structure.indexes:
        return True
    from primula.structure.tree import iter_tree

    return any(getattr(getattr(node, "resolved", None), "mode", None) == "page"
               for node in iter_tree(result.evaluation.document.children))


def main(argv: Sequence[str] | None = None, *, err: TextIO | None = None,
         out: TextIO | None = None, inp: TextIO | None = None) -> int:
    """Run the ``primula`` command.

    Args:
        argv: arguments without the program name; ``sys.argv[1:]`` if
            ``None``.
        err: stream for diagnostics; ``sys.stderr`` if ``None``.
        out: stream for command output; ``sys.stdout`` if ``None``.
        inp: input of ``primula console``; ``sys.stdin`` if ``None``.

    Returns:
        The exit code (0 or 2).  ``argparse`` usage errors and ``--help``
        / ``--version`` raise :class:`SystemExit` as usual.
    """
    arguments = list(sys.argv[1:] if argv is None else argv)
    stream = sys.stderr if err is None else err
    output = sys.stdout if out is None else out
    catalog = Catalog(detect_language(_prescan_language(arguments)))
    parser = build_parser(catalog)
    args = parser.parse_args(arguments)
    if args.command == "commands":
        from primula.commands import catalogue, render_text
        from primula.functions import render_text as render_functions
        from primula.header_keys import render_text as render_header

        data = catalogue(catalog.language)
        text = render_header(data) if args.header else render_functions(data) if args.functions else render_text(data)
        print(json.dumps(data, ensure_ascii=False, indent=1) if args.format == "json" else text,
              file=output, end="\n" if args.format == "json" else "")
        return EXIT_OK
    if args.command == "describe":
        from primula.describe import describe, render_text

        data = describe(args.file, catalog)
        print(json.dumps(data, ensure_ascii=False, indent=1) if args.format == "json" else render_text(data, catalog),
              file=output, end="\n" if args.format == "json" else "")
        return EXIT_ERROR if data["kind"] is None else EXIT_OK
    if args.command == "view":
        from primula.view import run as run_view

        return run_view(args, catalog, stream, output)
    if args.command == "console":
        return _console(args, catalog, stream, output, sys.stdin if inp is None else inp)
    if args.format == "json" and any(getattr(args, name, False) for name in (
            "dump_tree", "dump_parsed", "dump_project", "dump_structure", "dump_styles")):
        parser.error(catalog.text("cli.format.dump"))
    #: Messages of --format json: those of the targets of a project are added by batch.py.
    args.json_messages = []

    sink = DiagnosticSink(strict=args.strict)
    manager = SourceManager()
    result: FrontendResult | None = None
    args.dump_result = None
    set_overlays(_overlays(args, sink))
    build_date = getattr(args, "build_date", None) or datetime.date.today()

    stopped: str | None = None
    try:
        if not sink.has_errors:
            result = _run_command(args, sink, manager, stream, output, catalog)
    except TooManyErrors as exc:
        # The run stops, but the diagnostics so far and the report are kept.
        stopped = catalog.text("cli.too_many_errors", limit=exc.args[0])
    except MemoryError:
        # The process memory limit of 12.8 (core.limits.limit_memory).
        sink.emit(error("P0005", None, at_file=str(args.file)))
    except Exception as exc:  # noqa: BLE001 - every internal failure becomes P0002
        sink.emit(error("P0002", None, at_file=str(args.file),
                        detail=f"{type(exc).__name__}: {exc}").hint("help.internal"))
        if args.debug:
            traceback.print_exc(file=stream)
    finally:
        set_overlays({})

    from primula.batch import ProjectRun

    run = result if isinstance(result, ProjectRun) else None
    if run is not None:
        result = None
    if args.report is not None:
        report = make_report(command=args.command, result=result, sink=sink, manager=manager,
                             catalog=catalog, options=_options_for_report(args),
                             build_date=build_date)
        if run is not None:
            # The project report (14.3): the project and the list of targets.
            report["project"] = run.info()
            report["targets"] = run.targets
            if run.failed:
                report["result"] = "error"
        try:
            write_report(args.report, report)
        except OSError as exc:
            sink.emit(error("P0103", None, at_file=str(args.report), path=str(args.report),
                            reason=exc.strerror or str(exc)))

    if getattr(args, "dump_structure", False) or getattr(args, "dump_styles", False):
        from primula.dumps import make_dump

        data = make_dump(args.dump_result, file=str(args.file), structure=args.dump_structure,
                         styles=args.dump_styles,
                         messages=[to_json(diagnostic, catalog) for diagnostic in sink.ordered()])
        print(json.dumps(data, ensure_ascii=False, indent=1), file=output)
    if args.format == "json":
        messages = [to_json(diagnostic, catalog) for diagnostic in sink.ordered()] + args.json_messages
        print(json.dumps(messages, ensure_ascii=False, indent=1), file=output)
    else:
        _print_diagnostics(sink, catalog, stream)
    if stopped is not None:
        print(stopped, file=stream)
    if run is not None and run.total:
        print(catalog.text("cli.project.summary", file=str(args.file), total=run.total, failed=run.failed),
              file=stream)
    print(summary(sink, catalog, str(args.file)), file=stream)
    return EXIT_ERROR if sink.has_errors or (run is not None and run.failed) else EXIT_OK


def _print_diagnostics(sink: DiagnosticSink, catalog: Catalog, stream: TextIO) -> None:
    """Print all diagnostics of the run in the text format."""
    for diagnostic in sink.ordered():
        print(render_text(diagnostic, catalog), file=stream)
