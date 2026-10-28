"""Correspondence checks of parallel tracks: ``parity`` (specification 7.7, decision 134; stage 16.4).

Every numbered track is compared with the primary track, segment by
segment; a track ``numbered=False`` and the empty block of an
``optional=True`` track are not compared, nor are segments with
``parity="none"`` or excluded by a condition.

* ``structure`` — the sequence of structural blocks: headings and their
  levels, clauses and their levels, list items with level and kind, tables
  with their rows and columns, figures, admonitions and their kinds; plain
  paragraphs are not compared (P5310, the first block that differs);
* ``translation`` — ``structure`` and the sets of IDs (P5312), of targets
  of references (P5313), of names used in ``|(…)`` (P5314), the multiset of
  numbers and identifiers written in the text (P5311), and the counters of
  the tracks at the end of the environment (P5315).

The facts that need the source text — names inside ``|(…)`` and the numbers
written literally, before the values of expressions are merged into the
text — are collected by the evaluator (:func:`source_facts`); the structure
and the counters are compared by the structure phase, where lists are
grouped and tables have their grids.
"""

from __future__ import annotations

import ast
import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable

from primula.diagnostics import DiagnosticSink, warning
from primula.i18n import Key
from primula.structure.tree import iter_tree
from primula.syntax import nodes as N

#: E-mail addresses and URLs: identifiers compared as written (7.7).
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
_URL = re.compile(r"\bhttps?://[^\s<>«»\"]+[^\s<>«»\".,;:!?)]")
#: A number: digit groups joined by one separator (space, no-break spaces, '.', ',').
_NUMBER = re.compile(r"\d+(?:[   .,]\d+)*")


@dataclass
class TrackFacts:
    """What a track block contains for the ``translation`` profile.

    Attributes:
        ids: IDs given in the block (without the track prefix).
        targets: IDs referred to by ``|@`` (a track prefix removed).
        names: names used in ``|(…)``.
        tokens: numbers (digits only) and identifiers written in the text.
    """

    ids: set[str] = field(default_factory=set)
    targets: set[str] = field(default_factory=set)
    names: set[str] = field(default_factory=set)
    tokens: Counter = field(default_factory=Counter)


def text_tokens(text: str) -> list[str]:
    """Numbers and identifiers of a text (7.7).

    E-mail addresses and URLs are taken as written; a number is reduced to
    its digits, so «12 500,00», «12,500.00» and «12500.00» are equal and a
    date «12.10.2026» equals itself whatever the language.
    """
    tokens: list[str] = []
    for pattern in (_EMAIL, _URL):
        tokens += pattern.findall(text)
        text = pattern.sub(" ", text)
    tokens += [re.sub(r"\D", "", match) for match in _NUMBER.findall(text)]
    return tokens


def source_facts(source: N.Command, evaluated: list[Any], track_ids: Iterable[str],
                 is_value: Callable[[str], bool] = lambda name: True) -> TrackFacts:
    """The facts of a track block.

    Args:
        source: the parsed track block (``Expr`` nodes and literal text still apart).
        evaluated: its evaluated blocks (IDs and targets of references).
        track_ids: the ids of the tracks of the environment (prefixes removed from targets).
        is_value: whether a name in ``|(…)`` is a value (a parameter, a variable) and not a
            function: a translation may format the same value with another function.
    """
    facts = TrackFacts()
    prefixes = tuple(f"{track}." for track in track_ids)
    for node in iter_tree(list(source.children) + list(source.body or [])):
        if isinstance(node, N.Expr) and node.expr is not None:
            facts.names |= {n.id for n in ast.walk(node.expr.node)
                             if isinstance(n, ast.Name) and is_value(n.id)}
        elif isinstance(node, N.Text):
            facts.tokens.update(text_tokens(node.value))
    for node in iter_tree(evaluated):
        args = getattr(node, "args", None)
        keywords = getattr(args, "keywords", None)
        if isinstance(node, N.Reference):
            positional = getattr(args, "positional", None) or []
            if positional and isinstance(positional[0], str):
                target = positional[0]
                facts.targets.add(target[len(next(p for p in prefixes if target.startswith(p))):]
                                  if target.startswith(prefixes) else target)
        elif isinstance(keywords, dict) and isinstance(keywords.get("id"), str):
            facts.ids.add(keywords["id"])
    return facts


def structure_signature(blocks: list[Any]) -> list[tuple[tuple[Any, ...], Any]]:
    """The structural blocks of a track block in document order: ``(key, span)``.

    Keys are written like the markup: ``("|<<",)`` — a heading of level 2,
    ``("|>",)`` — a clause, ``("|#",)`` — a numbered list item,
    ``("|table", rows, cols)``, ``("|figure",)``, ``('|!("note")',)``.
    """
    result: list[tuple[tuple[Any, ...], Any]] = []
    for node in iter_tree(blocks):
        if isinstance(node, N.Heading):
            result.append((("|" + "<" * node.level,), node.span))
        elif isinstance(node, N.Clause):
            result.append((("|" + ">" * node.level,), node.span))
        elif isinstance(node, N.ListItem):
            result.append((("|" + ("#" if node.kind == "number" else "-") * node.level,), node.span))
        elif isinstance(node, N.Admonition):
            args = getattr(node, "args", None)
            kind = args.positional[0] if args is not None and getattr(args, "positional", None) else "note"
            result.append(((f'|!("{kind}")',), node.span))
        elif isinstance(node, N.Command) and node.name == "table":
            grid = getattr(node, "table_grid", None)
            rows, cols = (len(grid.rows), grid.count) if grid is not None else (0, 0)
            result.append((("|table", rows, cols), node.span))
        elif isinstance(node, N.Command) and node.name == "figure":
            result.append((("|figure",), node.span))
    return result


def _key_text(key: tuple[Any, ...] | None) -> str:
    if key is None:
        return "—"
    if key[0] == "|table":
        return f"|table {key[1]}×{key[2]}"
    return str(key[0])


def _listed(values: Iterable[Any]) -> str:
    items = sorted(str(v) for v in values)
    return ", ".join(items) if items else "—"


def check_structure(segment: str, track: str, primary_blocks: list[Any], track_blocks: list[Any],
                    where: Any, sink: DiagnosticSink) -> None:
    """P5310: the first structural block of the track that differs from the primary track."""
    expected = structure_signature(primary_blocks)
    found = structure_signature(track_blocks)
    for index in range(max(len(expected), len(found))):
        want = expected[index] if index < len(expected) else None
        have = found[index] if index < len(found) else None
        if want is not None and have is not None and want[0] == have[0]:
            continue
        diagnostic = warning("P5310", have[1] if have is not None else where, segment=segment, track=track,
                             found=_key_text(have[0] if have else None),
                             expected=_key_text(want[0] if want else None))
        if want is not None:
            diagnostic.note("note.primary_track", want[1])
        sink.emit(diagnostic)
        return


def check_translation(segment: str, track: str, primary: TrackFacts, other: TrackFacts, where: Any,
                      primary_where: Any, sink: DiagnosticSink) -> None:
    """P5311-P5314: numbers and identifiers, IDs, targets of references, names in ``|(…)``."""
    checks = (("P5311", primary.tokens, other.tokens), ("P5312", Counter(primary.ids), Counter(other.ids)),
              ("P5313", Counter(primary.targets), Counter(other.targets)),
              ("P5314", Counter(primary.names), Counter(other.names)))
    for code, want, have in checks:
        missing, extra = want - have, have - want
        if missing or extra:
            sink.emit(warning(code, where, segment=segment, track=track, missing=_listed(missing.elements()),
                              extra=_listed(extra.elements())).note("note.primary_track", primary_where))


def counters(scopes: list[Any], notes: dict[str, int]) -> dict[str, str]:
    """The counters of a track at the end of ``|parallel``: heading, clause, table, figure, footnote."""
    scope = scopes[-1]
    return {"heading": scope.section or "0", "clause": ".".join(str(c) for c in scope.clauses) or "0",
            "table": str(scope.tables), "figure": str(scope.figures), "footnote": str(notes.get("footnote", 0))}


def check_counters(track: str, primary: dict[str, str], other: dict[str, str], where: Any,
                   sink: DiagnosticSink) -> None:
    """P5315: the counters of a track at the end differ from the primary track."""
    for kind, value in primary.items():
        if other.get(kind) != value:
            sink.emit(warning("P5315", where, track=track, kind=Key("parallel.counter." + kind),
                              value=other.get(kind), primary=value))
