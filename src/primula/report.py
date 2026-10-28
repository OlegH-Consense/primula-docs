"""Build report in JSON (specification section 14.3).

The full report contains language and translator versions, source files and
hashes of data read, variables and parameters, variant parameters and
conditions, computed column widths, materialised styles, limit usage and
messages.  The prototype fills the parts that exist so far:

* translator name, version, prototype stage, language version;
* command, root file, options, build date;
* source files with SHA-256 hashes;
* header summary (kind, line mode, language version);
* phase states (which phases ran — :data:`primula.frontend.PHASES`);
* result and message counts, messages with positions (decision 26).

``REPORT_VERSION`` changes whenever the structure changes, so that Studio
and other readers can detect the format.
"""

from __future__ import annotations

import datetime
import json
from pathlib import Path
from typing import Any

from primula import LANGUAGE_VERSION, PROTOTYPE_STAGE, STDLIB_VERSION, __version__
from primula.diagnostics import DiagnosticSink, to_json
from primula.frontend import FrontendResult
from primula.i18n import Catalog
from primula.source import SourceManager
from primula.unicode import UNICODE_VERSION, runtime_version

#: Version of the report structure.
REPORT_VERSION = "0.1"


def make_report(*, command: str, result: FrontendResult | None, sink: DiagnosticSink,
                manager: SourceManager, catalog: Catalog, options: dict[str, Any],
                build_date: datetime.date) -> dict[str, Any]:
    """Assemble the report dictionary.

    Args:
        command: CLI command (``build``, ``check``, ``fmt``).
        result: front-end result, ``None`` if the run stopped before it.
        sink: diagnostics of the run.
        manager: source manager with the files read.
        catalog: catalogue of the message language.
        options: CLI options relevant to the result.
        build_date: build date (fixed by ``--build-date`` or today).

    Returns:
        A JSON-compatible dictionary.
    """
    header = result.header if result is not None else None
    return {
        "report_version": REPORT_VERSION,
        "translator": {"name": "primula-docs", "version": __version__, "stage": PROTOTYPE_STAGE},
        "language_version": LANGUAGE_VERSION,
        "stdlib_version": STDLIB_VERSION,
        "unicode": {"language": UNICODE_VERSION, "runtime": runtime_version()},
        "command": command,
        "source": str(result.path) if result is not None else None,
        "options": options,
        "build_date": build_date.isoformat(),
        "message_language": catalog.language,
        "files": [{"name": source.name, "sha256": source.sha256} for source in manager.files],
        "header": None if header is None else {
            "present": header.present,
            "kind": header.kind,
            "version": header.version,
        },
        "project": _project(result),
        "phases": dict(result.phases) if result is not None else {},
        "evaluation": _evaluation(result.evaluation) if result is not None and result.evaluation else None,
        "result": "error" if sink.has_errors else "ok",
        "counts": {"errors": sink.error_count, "warnings": sink.warning_count},
        "messages": [to_json(diagnostic, catalog) for diagnostic in sink.ordered()],
    }


def write_report(path: Path, report: dict[str, Any]) -> None:
    """Write the report as UTF-8 JSON with stable formatting.

    Args:
        path: output file.
        report: the report dictionary.

    Raises:
        OSError: the file cannot be written.
    """
    text = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=False)
    path.write_text(text + "\n", encoding="utf-8")


def _project(result: FrontendResult | None) -> dict[str, Any] | None:
    """The project of the document (10.6, 14.3): file, parameters, keys."""
    if result is None or getattr(result, "project", None) is None:
        return None
    from primula.batch import project_info

    return project_info(result.project)


def _position(span: object) -> dict[str, object]:
    """File, line and column of a span for the report."""
    if span is None:
        return {"file": None, "line": None, "column": None}
    position = span.begin_position  # type: ignore[attr-defined]
    return {"file": span.source.name, "line": position.line, "column": position.column}  # type: ignore[attr-defined]


def _evaluation(evaluation: Any) -> dict[str, Any]:
    """Parameters, conditions, debug records, limit usage, styles, table widths (14.3, 6.3)."""
    from primula.core.values import from_data, to_repr

    return {
        "params": {name: to_repr(from_data(value)) for name, value in evaluation.params.items()},
        "conditions": [{"condition": text, "result": value, **_position(span)}
                       for text, value, span in evaluation.conditions],
        "debug": [{"value": text, **_position(span)} for span, text in evaluation.debug],
        "limits": evaluation.limits,
        "styles": None if evaluation.styles is None else {
            "modules": evaluation.styles.modules,
            "materialized": evaluation.styles.materialized,
        },
        # Computed column widths of tables (6.3): file, line, widths in mm.
        "tables": list(getattr(evaluation, "tables", []) or []),
        # References to other documents of the project and the origin of their texts (decision 121).
        "external_references": list(getattr(evaluation, "external_references", []) or []),
    }
