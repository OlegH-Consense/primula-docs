"""Standard library support (stage 13.7 base; the full library comes at 13.9).

:mod:`primula.library.localefmt` formats and parses numbers, money and
dates by the document language (specification 13.2, 13.3, 13.5; decisions
77-80).  Stage 13.7 uses it for typed table cells; stage 13.9 builds the
user functions ``num``, ``money``, ``fmt_date`` on top of it.
"""
