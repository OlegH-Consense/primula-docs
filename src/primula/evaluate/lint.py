"""Lint of author names: mixed alphabets and homoglyphs (specification 3.9, 14.2).

Names written by the author may be Unicode identifiers (decision 102).  Two
warnings protect against look-alike names:

* P2502 — a name mixes alphabets (Latin, Cyrillic, Greek): ``cityМісто``;
* P2503 — two different names differ only by homoglyphs, for example a
  Cyrillic «а» and a Latin «a»: ``vat`` and ``vаt``.

The checked names are the global definitions of the evaluated files
(document, fragments, modules, styles modules: parameters, ``|let``,
code, macros) and the style names defined by the author.  Built-in modules
(``std/…``) are not checked.  The alphabets and homoglyphs come from
:mod:`primula.unicode` (a simplified UTS #39).
"""

from __future__ import annotations

from typing import Iterable

from primula.diagnostics import DiagnosticSink, warning
from primula.i18n import Key
from primula.source import Span
from primula.unicode import scripts, skeleton


def lint_names(names: Iterable[tuple[str, Span | None]], sink: DiagnosticSink) -> None:
    """Report mixed alphabets (P2502) and homoglyph pairs (P2503).

    Args:
        names: ``(name, definition span)`` pairs; repeated names are
            checked once (the first span is used).
        sink: receiver of the warnings.
    """
    seen: dict[str, Span | None] = {}
    for name, span in names:
        if name not in seen:
            seen[name] = span
    by_skeleton: dict[str, str] = {}
    for name, span in seen.items():
        if not name.isascii():
            found = scripts(name)
            if len(found) > 1:
                # The alphabets are a translated catalogue entry: "кирилиця, латиниця".
                sink.emit(warning("P2502", span, name=name, scripts=Key("scripts." + "+".join(sorted(found)))))
        key = skeleton(name)
        other = by_skeleton.get(key)
        if other is None:
            by_skeleton[key] = name
            continue
        # The later of the two names gets the warning, the earlier is a note.
        diagnostic = warning("P2503", span, name=name, other=other)
        if seen.get(other) is not None:
            diagnostic.note("note.definition_here", seen[other], name=other)
        sink.emit(diagnostic)
