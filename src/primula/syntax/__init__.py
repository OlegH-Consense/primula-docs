"""Lexer and parser of Primula markup (stage 13.1).

Builds the document tree with positions from the normalised source
(grammar of appendix 1, specification sections 3-4):

* :mod:`~primula.syntax.pyscan` — finds the end of Python fragments
  ``(…)`` by the Python 3.11 lexical rules (decisions 22, 30);
* :mod:`~primula.syntax.pyfrag` — parses fragments with :mod:`ast` and maps
  AST and error positions back to the source;
* :mod:`~primula.syntax.lines` — classification of lines: the ordered
  choice of ``Block`` (decisions 23, 34);
* :mod:`~primula.syntax.inline` — inline content (section 4, decision 21);
* :mod:`~primula.syntax.blocks` — line forms, environments, closing,
  code/verbatim/comment blocks (sections 3.4-3.7, decisions 24, 28, 35);
* :mod:`~primula.syntax.regions` — implicit regions and lists (sections
  3.6, 5.4, decisions 31-33);
* :mod:`~primula.syntax.nodes` — tree nodes and the S-expression dump;
* :mod:`~primula.syntax.parser` — entry point :func:`parse`.
"""
