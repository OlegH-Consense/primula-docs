"""Parallel tracks: ``|parallel``, ``|segment``, ``|track`` (specification 7.7, decision 134).

* :mod:`model` — the description of the tracks (``track(…)``, the
  arguments of ``|parallel`` and ``|segment``), the records ``track`` and
  ``segment`` of the code of a track block, the commands forbidden inside
  a segment;
* :mod:`build` — the evaluated segments as an ordinary ``|table``: a row
  per segment, a cell per track, a full-width cell for ``span="all"``,
  a new table after a page break between segments.

The evaluator (:mod:`primula.evaluate.evaluator`) parses the arguments,
evaluates every track block in the language of its track and hands the
segments to :mod:`build`; the later phases (styles, tables, structure, ODT)
see a table whose nodes carry the parallel attributes
(``parallel``, ``segment``, ``track``, ``track_language``).
"""
