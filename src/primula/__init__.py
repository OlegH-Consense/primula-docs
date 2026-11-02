"""Primula Documenting System — translator of the Primula markup language.

Primula (``.prml``) is a command-based document markup language with an
embedded computing core; the translator compiles sources into editable ODT
(ODF 1.3) documents.  The normative description is the specification
``primula-spec-v1.1-draft.ru.md`` with the standard library
``primula-stdlib-v1.1-draft.ru.md`` and the grammar
``primula-grammar-v1.1.ebnf``.

This package is the prototype of stage 13 of the project plan
(``primula-roadmap.md``; the journal of the substages — ``primula-journal.md``).  Sub-packages are filled stage by stage:

* :mod:`primula.source`, :mod:`primula.diagnostics`, :mod:`primula.i18n`,
  :mod:`primula.yamlio`, :mod:`primula.header`, :mod:`primula.cli` — 13.0;
* :mod:`primula.syntax` — lexer and parser (13.1, done);
* :mod:`primula.core` — computing core interpreter (13.2, done);
* :mod:`primula.evaluate` — document evaluation (13.3, done);
* :mod:`primula.styles` — styles (13.4, done);
* :mod:`primula.structure` — numbering, IDs, references, notes, indexes (13.6, done);
* :mod:`primula.tables`, :mod:`primula.library` — tables, number and date formats (13.7, done);
* :mod:`primula.pages` — pages, headers, images, frames, watermarks (13.8, done);
* :mod:`primula.unicode` — Unicode 15.1 identifiers and short forms (13.8a, spec v1.1);
* :mod:`primula.odf` — ODT generator (13.5 MVP, extended in later stages).
"""

#: Version of the translator (PEP 440).  0.2.0 is the first public release
#: (GitHub, 26.10.2026); 0.2.x — fixes, 0.3.0 — the next iteration, ``.devN`` —
#: builds between releases.  The stage is recorded in the build report.
__version__ = "0.3.0"

#: Prototype stage of the project plan implemented by this version.
PROTOTYPE_STAGE = "19.2"

#: Version of the Primula language implemented by the translator
#: (specification section 0.1).
LANGUAGE_VERSION = "1.1"

#: Version of the standard library shipped with the translator
#: (``primula-stdlib-v1.1-draft.ru.md``, section 0.2); a file may require
#: a minimal version with ``primula: {stdlib: "1.1"}``.
STDLIB_VERSION = "1.1"

__all__ = ["__version__", "PROTOTYPE_STAGE", "LANGUAGE_VERSION", "STDLIB_VERSION"]
