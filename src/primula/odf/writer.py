"""Writing an evaluated document as ODT (stage 13.5, specification 15).

:func:`build_odt` assembles the parts:

* ``content.xml`` — :mod:`primula.odf.content`;
* ``styles.xml`` — :mod:`primula.odf.styles_xml`;
* ``meta.xml`` — :mod:`primula.odf.meta`;
* ``Primula/report.json`` — the reduced build report (decision 67): no
  values of parameters and variables, no ``debug`` output; disabled with
  ``--no-embed-report``;
* ``Primula/sources/…`` — source files, only with ``--embed-sources``,
  with paths relative to the project root (built-in ``std/`` modules are
  not embedded).

The document language follows decision 65: ``doc.language`` of the
header, then the project language (stage 13.11), then ``defaults.language``
of the styles modules, then ``uk-UA``.
"""

from __future__ import annotations

import datetime
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from primula import LANGUAGE_VERSION, PROTOTYPE_STAGE, STDLIB_VERSION, __version__
from primula.diagnostics import DiagnosticSink, Severity, to_json
from primula.i18n import Catalog
from primula.odf import units
from primula.odf.content import AutoStyles, ContentWriter
from primula.styles.schema import check_property
from primula.odf.meta import build_meta
from primula.odf.package import build_package
from primula.odf.props import Fonts
from primula.odf.styles_xml import build_styles, page_geometry
from primula.odf.typography import apply_nbsp_short
from primula.odf.xml import serialize, sub
from primula.source import SourceManager
from primula.structure.settings import document_language


@dataclass
class OdtOptions:
    """Options of ODT writing (14.1)."""

    build_date: datetime.date
    embed_report: bool = True
    embed_sources: bool = False


def build_odt(result: Any, sink: DiagnosticSink, manager: SourceManager, root: Path,
              catalog: Catalog, options: OdtOptions) -> bytes:
    """Build the ODT bytes of an evaluated document.

    Args:
        result: the :class:`~primula.frontend.FrontendResult` (evaluated).
        sink: receiver of P8xxx warnings.
        manager: sources read (embedded report and sources).
        root: project root (relative paths).
        catalog: message catalogue (texts of embedded warnings).
        options: writing options.
    """
    evaluation = result.evaluation
    system = evaluation.styles
    header = result.header
    language = document_language(header.data, system.defaults, getattr(evaluation, "project_language", None))
    fonts = Fonts()
    page = getattr(evaluation.document, "page_style", None)
    text_width = page_geometry(system.effective(page))["text_width"] if page else units.to_mm(
        units.from_mm(170))  # A4 with 20 mm margins
    writer = ContentWriter(system, fonts, language, sink, page, text_width, PROTOTYPE_STAGE)
    content = writer.build(evaluation.document)
    parts_writers: dict[int, ContentWriter] = {}

    def write_part(element: Any, blocks: list[Any], watermark: Any, automatic: Any) -> None:
        """Header/footer content in ``styles.xml`` (7.6) with a watermark frame (8.6)."""
        part_writer = parts_writers.get(id(automatic))
        if part_writer is None:
            part_writer = ContentWriter(system, fonts, language, sink, None, text_width, PROTOTYPE_STAGE,
                                        auto=AutoStyles(fonts, automatic, prefix="M"))
            parts_writers[id(automatic)] = part_writer
        if watermark is not None:
            part_writer.pending_frames.append((watermark, None, None))
        if not blocks and watermark is not None:
            # A header with only the watermark: a host paragraph of minimal height.
            tiny = {"size": check_property("paragraph", "size", "1pt"),
                    "line_height": check_property("paragraph", "line_height", "0.5mm"),
                    "space_before": check_property("paragraph", "space_before", "0mm"),
                    "space_after": check_property("paragraph", "space_after", "0mm")}
            host = sub(element, "text:p", {"text:style-name": part_writer.auto.paragraph(None, tiny)})
            part_writer._lead(host)
            return
        part_writer.write_blocks(element, blocks)

    styles = build_styles(system, language, fonts, getattr(evaluation, "structure", None),
                          getattr(evaluation, "pages", None), write_part)
    typography = system.settings.get("typography") or {}
    words = nbsp_words(typography, language)
    if words:
        # typography(nbsp_short=True): the whole text, headers and footers included (library 7);
        # the cells of track blocks of |parallel use the words of their language (7.7).
        raw = set(writer.raw).union(*(w.raw for w in parts_writers.values()))
        own = {key: nbsp_words(typography, tag) for key, tag in writer.languages.items()}
        apply_nbsp_short([content, styles], words, raw, own)
    _fill_fonts(content, fonts)
    _fill_fonts(styles, fonts, replace=True)
    # The metadata of the header over the defaults of the project (10.6, decision 127).
    metadata = header.data.get("doc") or {}
    metadata = {**(getattr(evaluation, "document_defaults", None) or {}),
                **(metadata if isinstance(metadata, dict) else {})}
    meta = build_meta(metadata, language, options.build_date)

    parts: dict[str, bytes] = {
        "content.xml": serialize(content),
        "styles.xml": serialize(styles),
        "meta.xml": serialize(meta),
    }
    pages = getattr(evaluation, "pages", None)
    for image in sorted(pages.images if pages is not None else [], key=lambda i: i.package_name):
        parts[image.package_name] = image.data
    if options.embed_report:
        report = reduced_report(result, sink, manager, root, catalog)
        parts["Primula/report.json"] = (json.dumps(report, ensure_ascii=False, indent=1) + "\n").encode("utf-8")
    if options.embed_sources:
        for source in manager.files:
            relative = _relative(source.path, root)
            if relative is not None and source.path is not None:
                parts[f"Primula/sources/{relative}"] = source.path.read_bytes()
    return build_package(parts, options.build_date)


def nbsp_words(typography: dict[str, Any], language: str | None) -> list[str]:
    """The short words of ``typography(nbsp_short=True)``; empty when the setting is off.

    ``nbsp_words=`` of the setting, otherwise the defaults of the document
    language; a language outside uk, ru, en takes the en words, as the
    library functions do (library 1).
    """
    if typography.get("nbsp_short") is not True:
        return []
    from primula.library.text import SHORT_WORDS

    words = typography.get("nbsp_words")
    if isinstance(words, (list, tuple)) and words:
        return [str(w) for w in words]
    code = (language or "uk").split("-")[0].lower()
    return list(SHORT_WORDS.get(code, SHORT_WORDS["en"]))


def _fill_fonts(root: Any, fonts: Fonts, *, replace: bool = False) -> None:
    """Fill ``office:font-face-decls`` with every font used."""
    from primula.odf.xml import qn

    decls = root.find(qn("office:font-face-decls"))
    if decls is None:
        return
    if replace:
        for child in list(decls):
            decls.remove(child)
    for font in fonts.names:
        sub(decls, "style:font-face", {"style:name": font, "svg:font-family": units.font_family(font)})


def _is_builtin(path: Path) -> bool:
    """A file of the built-in modules (``std/…``), not a project file."""
    from primula.evaluate.loader import STDLIB

    try:
        path.resolve().relative_to(STDLIB)
    except ValueError:
        return False
    return True


def _relative(path: Path | None, root: Path) -> str | None:
    if path is None:
        return None
    from primula.paths import within

    relative = within(path, root)
    return relative.as_posix() if relative is not None else None


def reduced_report(result: Any, sink: DiagnosticSink, manager: SourceManager, root: Path,
                   catalog: Catalog) -> dict[str, Any]:
    """The report embedded in the ODT (decision 67): no values, no debug output."""
    evaluation = result.evaluation
    files = []
    for source in manager.files:
        relative = _relative(source.path, root)
        if relative is not None:
            files.append({"name": relative, "sha256": source.sha256})
        elif source.path is not None and not _is_builtin(source.path):
            # A --style file outside the project root: its name without the
            # directory and its hash, no absolute path (14.3, decision 106).
            files.append({"name": source.path.name, "sha256": source.sha256})
    warnings = []
    for diagnostic in sink.ordered():
        if diagnostic.severity is Severity.WARNING:
            item = to_json(diagnostic, catalog)
            if diagnostic.span is not None and diagnostic.span.source.path is not None:
                item["file"] = _relative(diagnostic.span.source.path, root) or item["file"]
            item.pop("stack", None)
            warnings.append(item)
    return {
        "report_version": "0.1",
        "kind": "reduced",
        "translator": {"name": "primula-docs", "version": __version__, "stage": PROTOTYPE_STAGE},
        "language_version": LANGUAGE_VERSION,
        "stdlib_version": STDLIB_VERSION,
        "files": files,
        "variant_parameters": sorted(evaluation.params),
        # A --style module outside the project root appears by its name only.
        "styles": {"modules": [Path(m).name if Path(m).is_absolute() else m for m in evaluation.styles.modules],
                   "materialized": evaluation.styles.materialized},
        "tables": [{"file": _relative(Path(e["file"]), root) if e.get("file") else None, "line": e.get("line"),
                    "widths_mm": e.get("widths_mm")} for e in getattr(evaluation, "tables", []) or []],
        # The time used depends on the machine: it stays in the external
        # report only, so that the ODT is byte-identical (15).
        "limits": {k: v for k, v in evaluation.limits.items() if k != "max_time"},
        "warnings": warnings,
    }
