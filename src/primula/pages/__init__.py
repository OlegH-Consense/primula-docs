"""Pages and graphics (stage 13.8; specification 7, 8; decisions 84-89).

* :mod:`~primula.pages.images` — image files: format, size, DPI, EXIF;
* :mod:`~primula.pages.frames` — placement parameters (8.5) -> frame model;
* :mod:`~primula.pages.watermark` — the SVG of a text watermark (8.6);
* :mod:`~primula.pages.flow` — page changes, breaks, sections, headers and
  footers, watermarks per page style: the pages phase.
"""


def build_pages(evaluation, sink):  # noqa: ANN001, ANN201 - see the module description
    """Run the pages phase; set and return ``evaluation.pages``.

    Args:
        evaluation: :class:`~primula.evaluate.evaluator.EvaluationResult`.
        sink: diagnostics receiver.
    """
    from primula.pages.flow import PagesBuilder

    system = evaluation.styles
    font = system.defaults.get("font") if isinstance(system.defaults.get("font"), str) else "Liberation Sans"
    builder = PagesBuilder(system, sink, font)
    # --review (9.2): the "not for release" mark replaces every other watermark.
    builder.review_mark = getattr(evaluation, "review_watermark", None)
    evaluation.pages = builder.build(evaluation.document)
    return evaluation.pages
