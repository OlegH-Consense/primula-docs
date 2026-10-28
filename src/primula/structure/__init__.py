"""Document structure (stage 13.6; specification 5; decisions 68-76).

Numbering of headings, clauses, annexes, tables and figures; IDs and
cross-references; captions; footnotes; tables of contents and lists.  The
phase runs after evaluation and styles and before the ODT writer; see
:mod:`primula.structure.builder`.
"""

from __future__ import annotations

from typing import Any

from primula.diagnostics import DiagnosticSink


def build_structure(evaluation: Any, header_data: dict[str, Any], sink: DiagnosticSink, *,
                    review: bool = False, external: Any = None) -> Any:
    """Run the structure phase on an evaluated document.

    Args:
        evaluation: :class:`~primula.evaluate.evaluator.EvaluationResult`
            (its tree is annotated in place; ``evaluation.structure`` is set).
        header_data: the YAML header of the root document (``structure``,
            ``doc.language``).
        sink: diagnostics receiver.
        review: ``--review`` mode (decision 75).
        external: :class:`~primula.xrefs.ExternalReferences` of ``references:``
            (decision 121) or ``None``.

    Returns:
        The :class:`~primula.structure.builder.Structure`.
    """
    from primula.structure.builder import StructureBuilder
    from primula.structure.settings import QUOTES, document_language, language_code, resolve_settings

    system = evaluation.styles
    settings_source = system.settings if system is not None else {}
    defaults = system.defaults if system is not None else {}
    language = document_language(header_data, defaults, getattr(evaluation, "project_language", None))
    settings = resolve_settings(settings_source, header_data.get("structure"), language)
    _check_settings(settings, evaluation.document, sink)
    quotes = dict(QUOTES)
    for lang, pairs in (settings_source.get("quotes") or {}).items():
        quotes[lang] = (tuple(pairs[0]), tuple(pairs[1]))

    def language_settings(tag: str) -> tuple[Any, Any]:
        """Settings and quotes of a track language of |parallel (7.7)."""
        code = language_code(tag)
        return (resolve_settings(settings_source, header_data.get("structure"), tag),
                quotes.get(code, quotes.get(language_code(language), quotes["uk"])))

    builder = StructureBuilder(settings, sink, evaluation.excluded_ids, review=review,
                               quotes=quotes.get(language_code(language), quotes["uk"]), external=external,
                               language_settings=language_settings)
    evaluation.structure = builder.build(evaluation.document)
    return evaluation.structure


def _check_settings(settings: Any, document: Any, sink: DiagnosticSink) -> None:
    """Values of the structure settings (5.1-5.10): P4402 for invalid ones."""
    from primula.diagnostics import error

    checks = [
        ("numbering", "figures", settings.numbering.get("figures"), ("document", "by_chapter")),
        ("numbering", "tables", settings.numbering.get("tables"), ("document", "by_chapter")),
        ("appendices", "numbering", settings.appendices.get("numbering"), ("numbers", "letters")),
        ("footnotes", "numbering", settings.footnotes.get("numbering"), ("document",)),
        ("footnotes", "restart", settings.footnotes.get("restart"), ("none", "page", "chapter")),
        ("footnotes", "format", settings.footnotes.get("format"), ("1", "i", "I", "a", "A", "*")),
    ]
    for group, key, value, allowed in checks:
        if value not in allowed:
            sink.emit(error("P4402", None, at_file=document.source.name, setting=f"{group}.{key}",
                            value=str(value), expected=", ".join(allowed)))
