"""Diagnostics: messages with codes, positions, notes and call stacks.

Implements specification section 14.2 and decisions 26-27:

* every message has a code ``P`` + 4 digits, a severity (error or warning),
  a file, line and column, and for runtime errors a call stack through
  ``|include``, ``|import`` and macros;
* the severity is a separate attribute: ``--strict`` turns warnings into
  errors without changing the code;
* the text format follows gcc/rustc, so editors can parse it::

      file.prml:12:7: error[P1102]: invalid YAML in the header: ...
         12 | params: a: b
            |       ^
      file.prml:1:1: note: the header starts here
        = help: ...

* the JSON form (build report, Studio) also carries the end of the range.

Message texts are not stored in diagnostics: a diagnostic keeps a catalogue
key and arguments, and the text is produced when rendering, in the language
chosen by the user (:mod:`primula.i18n`).

The list of codes is ``docs/dev/diagnostics.md``.
"""

from __future__ import annotations

from typing import Any

import enum
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field, replace

from primula.i18n import Catalog
from primula.source import Span

#: Width of a tab when a source line is shown under a message.
_TAB_WIDTH = 4


class Severity(str, enum.Enum):
    """Severity of a diagnostic (specification 0.3, 14.2)."""

    ERROR = "error"
    WARNING = "warning"


@dataclass(frozen=True)
class Note:
    """Additional information attached to a diagnostic.

    Attributes:
        key: catalogue key of the text (``note.*`` or ``help.*``).
        args: template arguments.
        span: position the note refers to (``note:`` lines), or ``None``
            for a hint without position (``= help:`` lines).
        kind: ``"note"`` or ``"help"``.
    """

    key: str
    args: Mapping[str, object] = field(default_factory=dict)
    span: Span | None = None
    kind: str = "note"


@dataclass(frozen=True)
class Frame:
    """One entry of the call stack of a runtime error.

    Frames are listed from the innermost call outwards; each points at the
    call site (the ``|include`` line, the macro call...).

    Attributes:
        kind: ``include``, ``import``, ``macro`` or ``call`` (catalogue key
            ``frame.<kind>``).
        span: position of the call site.
        name: macro or function name, empty for inclusions.
    """

    kind: str
    span: Span
    name: str = ""


@dataclass
class Diagnostic:
    """A single message of the translator.

    Build diagnostics with :func:`error` and :func:`warning`, then refine
    them with the chaining helpers :meth:`note`, :meth:`hint`, :meth:`frame`.

    Attributes:
        code: diagnostic code, for example ``"P1102"``.
        severity: effective severity (after ``--strict``).
        span: primary position, or ``None`` when there is no source text
            (a file that cannot be read).
        args: arguments of the message template.
        file: display name used when ``span`` is ``None``.
        notes: notes and hints, in output order.
        stack: call stack, innermost first.
        escalated: the severity was raised from warning by ``--strict``.
    """

    code: str
    severity: Severity
    span: Span | None
    args: dict[str, object] = field(default_factory=dict)
    file: str | None = None
    notes: list[Note] = field(default_factory=list)
    stack: list[Frame] = field(default_factory=list)
    escalated: bool = False

    def note(self, key: str, span: Span | None = None, /, **args: object) -> "Diagnostic":
        """Attach a note with an optional position; returns ``self``."""
        self.notes.append(Note(key, args, span, "note"))
        return self

    def hint(self, key: str, /, **args: object) -> "Diagnostic":
        """Attach a hint (``= help:`` line); returns ``self``."""
        self.notes.append(Note(key, args, None, "help"))
        return self

    def frame(self, kind: str, span: Span, name: str = "") -> "Diagnostic":
        """Append an outer call stack frame; returns ``self``."""
        self.stack.append(Frame(kind, span, name))
        return self

    def message(self, catalog: Catalog) -> str:
        """Return the message text in the catalogue language."""
        return catalog.text(self.code, **self.args)


def error(code: str, span: Span | None, /, *, at_file: str | None = None,
          **args: object) -> Diagnostic:
    """Create an error diagnostic.

    Args:
        code: diagnostic code.
        span: primary position or ``None``.
        at_file: display name for diagnostics without a span.
        **args: message template arguments (any names, including
            ``code``, ``span`` and ``file``).
    """
    return Diagnostic(code, Severity.ERROR, _span(span), dict(args), at_file)


def warning(code: str, span: Span | None, /, *, at_file: str | None = None,
            **args: object) -> Diagnostic:
    """Create a warning diagnostic; arguments as in :func:`error`."""
    return Diagnostic(code, Severity.WARNING, _span(span), dict(args), at_file)


def _span(span: Any) -> Span | None:
    """A span; a lazy position of the core (``core.errors.Where``, callable) is resolved.

    Found by the robustness check of stage 13.15: a library warning was created
    with a lazy position and broke the ordering of the messages.
    """
    return span() if callable(span) else span


class TooManyErrors(Exception):
    """Raised by :class:`DiagnosticSink` when the error limit is exceeded."""


class PrimulaError(Exception):
    """Exception that carries a diagnostic out of a processing phase.

    Used for errors after which a phase cannot continue (for example an
    unreadable root file).  The phase boundary catches it and passes the
    diagnostic to the sink.

    Args:
        diagnostic: the error to report.
    """

    def __init__(self, diagnostic: Diagnostic) -> None:
        super().__init__(diagnostic.code)
        self.diagnostic = diagnostic


class DiagnosticSink:
    """Collects diagnostics of one run and applies ``--strict``.

    Args:
        strict: turn warnings into errors (the code stays the same).
        error_limit: stop the run with :class:`TooManyErrors` after this
            many errors; ``0`` disables the limit.
    """

    def __init__(self, *, strict: bool = False, error_limit: int = 100) -> None:
        self.strict = strict
        self.error_limit = error_limit
        self.diagnostics: list[Diagnostic] = []
        self.error_count = 0
        self.warning_count = 0

    def emit(self, diagnostic: Diagnostic) -> Diagnostic:
        """Record a diagnostic.

        Args:
            diagnostic: the diagnostic; with ``strict`` a warning is
                recorded as an error with ``escalated=True``.

        Returns:
            The recorded diagnostic (a copy when the severity changed).

        Raises:
            TooManyErrors: the error limit is exceeded.
        """
        if self.strict and diagnostic.severity is Severity.WARNING:
            diagnostic = replace(diagnostic, severity=Severity.ERROR, escalated=True)
        self.diagnostics.append(diagnostic)
        if diagnostic.severity is Severity.ERROR:
            self.error_count += 1
            if self.error_limit and self.error_count > self.error_limit:
                raise TooManyErrors(self.error_limit)
        else:
            self.warning_count += 1
        return diagnostic

    def extend(self, diagnostics: Iterable[Diagnostic]) -> None:
        """Record several diagnostics in order."""
        for diagnostic in diagnostics:
            self.emit(diagnostic)

    @property
    def has_errors(self) -> bool:
        """At least one error was recorded."""
        return self.error_count > 0

    def ordered(self) -> list[Diagnostic]:
        """Return the diagnostics in output order.

        Diagnostics without a position come first (they concern the run as
        a whole), then the others by file (in order of first appearance)
        and offset.  The sort is stable: diagnostics at the same place keep
        the order of discovery.
        """
        file_order: dict[str, int] = {}
        for diagnostic in self.diagnostics:
            if diagnostic.span is not None:
                file_order.setdefault(diagnostic.span.source.name, len(file_order))

        def key(diagnostic: Diagnostic) -> tuple[int, int, int]:
            if diagnostic.span is None:
                return (0, 0, 0)
            return (1, file_order[diagnostic.span.source.name], diagnostic.span.start)

        return sorted(self.diagnostics, key=key)

    def codes(self) -> list[str]:
        """Return the codes of recorded diagnostics in order (for tests)."""
        return [d.code for d in self.diagnostics]


# ----------------------------------------------------------------------
# Rendering
# ----------------------------------------------------------------------


def _location(span: Span | None, file: str | None) -> str:
    """Format ``file:line:column`` (or the bare file name, or ``primula``)."""
    if span is not None:
        position = span.begin_position
        return f"{span.source.name}:{position.line}:{position.column}"
    return file if file else "primula"


def _excerpt(span: Span) -> list[str]:
    """Format the source line of a span with a ``^^^`` underline.

    The line is shown in its normalised form; tabs are expanded to a fixed
    width, and the underline is aligned to the expanded text.  A span that
    continues on the next lines is underlined to the end of its first line.

    Args:
        span: the span to show.

    Returns:
        Two output lines (source line, underline).
    """
    source = span.source
    line_number = source.line_index(span.start) + 1
    line = source.line_text(line_number)
    column0 = source.normalized_column(span.start) - 1
    line_end = source.line_start(line_number) + len(line)
    end = min(span.end, line_end)
    length = max(1, end - span.start)

    def expand(text: str) -> str:
        return text.replace("\t", " " * _TAB_WIDTH)

    gutter = str(line_number)
    pad = " " * len(gutter)
    shown = expand(line)
    before = len(expand(line[:column0]))
    width = max(1, len(expand(line[column0:column0 + length])))
    return [f" {gutter} | {shown}".rstrip(), f" {pad} | {' ' * before}{'^' * width}"]


def render_text(diagnostic: Diagnostic, catalog: Catalog, *, excerpt: bool = True) -> str:
    """Render a diagnostic in the gcc/rustc-like text format.

    Args:
        diagnostic: the diagnostic.
        catalog: message catalogue of the output language.
        excerpt: show the source line with an underline.

    Returns:
        The text without a trailing newline.
    """
    lines = [
        f"{_location(diagnostic.span, diagnostic.file)}: "
        f"{diagnostic.severity.value}[{diagnostic.code}]: {diagnostic.message(catalog)}"
    ]
    if excerpt and diagnostic.span is not None:
        lines.extend(_excerpt(diagnostic.span))
    for note in diagnostic.notes:
        text = catalog.text(note.key, **note.args)
        if note.span is not None:
            lines.append(f"{_location(note.span, None)}: {note.kind}: {text}")
        else:
            lines.append(f"  = {note.kind}: {text}")
    for frame in diagnostic.stack:
        text = catalog.text(f"frame.{frame.kind}", name=frame.name)
        lines.append(f"{_location(frame.span, None)}: note: {text}")
    return "\n".join(lines)


def _position_dict(span: Span | None, file: str | None) -> dict[str, object]:
    """Position fields of the JSON form (decision 26: with the range end)."""
    if span is None:
        return {"file": file, "line": None, "column": None, "end_line": None, "end_column": None}
    begin, end = span.begin_position, span.end_position
    return {"file": span.source.name, "line": begin.line, "column": begin.column,
            "end_line": end.line, "end_column": end.column}


def to_json(diagnostic: Diagnostic, catalog: Catalog) -> dict[str, object]:
    """Convert a diagnostic to a JSON-compatible dictionary.

    Args:
        diagnostic: the diagnostic.
        catalog: message catalogue of the output language.

    Returns:
        A dictionary with ``code``, ``severity``, ``message``, position
        fields, ``escalated``, ``notes`` and ``stack``.
    """
    result: dict[str, object] = {
        "code": diagnostic.code,
        "severity": diagnostic.severity.value,
        "message": diagnostic.message(catalog),
        **_position_dict(diagnostic.span, diagnostic.file),
        "escalated": diagnostic.escalated,
    }
    result["notes"] = [
        {"kind": note.kind, "message": catalog.text(note.key, **note.args),
         **(_position_dict(note.span, None) if note.span is not None else {})}
        for note in diagnostic.notes
    ]
    result["stack"] = [
        {"kind": frame.kind, "name": frame.name,
         "message": catalog.text(f"frame.{frame.kind}", name=frame.name),
         **_position_dict(frame.span, None)}
        for frame in diagnostic.stack
    ]
    return result


def summary(sink: DiagnosticSink, catalog: Catalog, file: str) -> str:
    """Format the closing line ``file: N errors, M warnings``.

    Args:
        sink: the diagnostics of the run.
        catalog: message catalogue.
        file: display name of the root file.
    """
    return catalog.text(
        "cli.summary",
        file=file,
        errors=catalog.plural("count.errors", sink.error_count),
        warnings=catalog.plural("count.warnings", sink.warning_count),
    )
