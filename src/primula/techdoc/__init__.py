"""Technical documentation tools (specification 9; decision 116, stage 13.10).

* :mod:`admonitions` — ``|!`` blocks: a table by kind, notes and tips;
* :mod:`abbreviations` — ``|abbr`` and ``|list_of("abbr")``;
* :mod:`review` — marks of the ``--review`` mode;
* :mod:`texts` — signal words and other texts by language.

The transforms run on the evaluated tree after the style layers are
merged and before the styles are applied (:mod:`primula.evaluate`), so
they build ordinary nodes (tables, paragraphs with styles, lists) that the
later phases handle as written by an author.  The alphabetical index
(9.5) is part of the structure phase and the ODT writer.
"""
