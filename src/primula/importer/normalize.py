"""The structure of an imported document: headings, clauses and the table of contents (stage 19.3.2).

Word and ODT documents carry their structure in many ways that pandoc cannot turn into headings: the numbers
are typed by hand ("2.1. Покупець оплачує…"), a numbered list holds a single paragraph that is really a heading
(the automatic numbering of the headings), a short bold line stands for a heading, the table of contents is typed
with dots and page numbers.  :func:`normalize` rewrites the blocks of the pandoc tree so that the converter writes
what the author meant: ``|<`` headings, ``|>`` clauses of the numbering of Primula, ``|toc()``.

Rules (each is told in the report; ``keep_numbers`` keeps the typed numbers in the text):

* a numbered list of one item (the numbering of Word headings) is a heading when its text is short and has no
  sentence end, otherwise a clause; its nested numbered lists are the next levels;
* a paragraph that starts with a typed number ("1.", "2.1.", "2.1.1)") is a heading (short, no sentence end) or a
  clause; the number of components is the level;
* a short paragraph in bold only is a heading of the next level under the last heading;
* the heading levels do not skip: the first heading is level 1, a deeper heading is one level below the last one;
* a typed table of contents (lines "Title ....... 5", or the list of the internal links under "Contents")
  becomes ``|toc()``;
* the numbers of the source are compared with the numbering that Primula will give; the differences are counted
  (the numbers of the result follow the structure, not the typed text).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from primula.importer.convert import Report

#: A typed number: "1", "1.", "2.1", "2.1.", "2.1.1)" — digits separated by dots, an optional final dot or bracket.
_NUMBER = re.compile(r"^(\d{1,3}(?:\.\d{1,3})*)[.)]?$")
#: A number glued to the text: "2.1.Text".
_GLUED = re.compile(r"^(\d{1,3}(?:\.\d{1,3})+)\.([^\W\d].*)$")
_HEADING_WORDS = {"зміст", "содержание", "contents", "table of contents", "оглавление", "зміст:"}
_LEADER = re.compile(r"^.{3,}?(?:\.{3,}|…{2,}|\s\.\s\.\s\.|_{3,})\s*\d{1,4}\s*$")
_SENTENCE_END = (".", ";", ",", ":", "!", "?")
MAX_HEADING = 120


@dataclass
class Options:
    """What the normalizer may do."""

    keep_numbers: bool = False        # the typed numbers stay in the text
    structure: bool = True            # False — the tree is not changed at all


@dataclass
class _State:
    report: Report
    options: Options
    #: The level of the last heading (0 — none yet).
    heading_level: int = 0
    #: Headed document: numbered headings of the first level exist (clauses are numbered under them).
    headed: bool = False
    #: Typed numbers against the numbering of Primula: counters of headings and clauses.
    heading_counters: list[int] = field(default_factory=lambda: [0] * 7)
    clause_counters: list[int] = field(default_factory=lambda: [0] * 8)
    prefix: str = ""
    #: The level of the last clause under the last heading (0 — none): a clause is at most one level below it.
    clause_level: int = 0


def plain(inlines: list) -> str:
    """The text of inlines."""
    out = []
    for item in inlines:
        kind, content = item["t"], item.get("c")
        if kind == "Str":
            out.append(content)
        elif kind in ("Space", "SoftBreak", "LineBreak"):
            out.append(" ")
        elif kind in ("Strong", "Emph", "Underline", "SmallCaps", "Strikeout", "Superscript", "Subscript"):
            out.append(plain(content))
        elif kind in ("Span", "Link", "Quoted", "Cite"):
            out.append(plain(content[1]))
        elif kind == "Code":
            out.append(content[1])
    return "".join(out)


def _is_bold_only(inlines: list) -> bool:
    """Every visible inline is strong (a bold line)."""
    visible = [i for i in inlines if i["t"] not in ("Space", "SoftBreak", "LineBreak")]
    return bool(visible) and all(i["t"] == "Strong" or (i["t"] == "Span" and _is_bold_only(i["c"][1])) for i in visible)


def _heading_like(text: str) -> bool:
    """A short line without a sentence end."""
    text = text.strip()
    return 0 < len(text) <= MAX_HEADING and not text.endswith(_SENTENCE_END)


def _strip_number(inlines: list) -> tuple[str, list] | None:
    """(the typed number, the inlines without it), or ``None`` when the paragraph does not start with a number."""
    if not inlines:
        return None
    first = inlines[0]
    if first["t"] == "Span" and not first["c"][1] and len(inlines) > 1:
        # An empty span is an anchor of the source (a bookmark before the number): it stays where it was.
        inner = _strip_number(inlines[1:])
        return None if inner is None else (inner[0], [first] + inner[1])
    if first["t"] in ("Strong", "Emph", "Span") and first.get("c"):
        content = first["c"] if first["t"] != "Span" else first["c"][1]
        inner = _strip_number(content)
        if inner is None:
            return None
        number, rest = inner
        # "**2.1.** text": the number was the whole strong form; "**2.1. Title**": the rest stays strong.
        if rest:
            replacement = dict(first)
            replacement["c"] = rest if first["t"] != "Span" else [first["c"][0], rest]
            return number, [replacement] + inlines[1:]
        return number, inlines[1:]
    if first["t"] != "Str":
        return None
    match = _NUMBER.match(first["c"])
    if match is not None and len(inlines) > 1 and inlines[1]["t"] == "Space":
        return match.group(1), inlines[2:]
    glued = _GLUED.match(first["c"])
    if glued is not None:
        return glued.group(1), [{"t": "Str", "c": glued.group(2)}] + inlines[1:]
    return None


def _trim(inlines: list) -> list:
    """Without the spaces and line breaks at the ends (a heading of Word often ends with a break)."""
    items = list(inlines)
    while items and items[-1]["t"] in ("Space", "SoftBreak", "LineBreak"):
        items.pop()
    while items and items[0]["t"] in ("Space", "SoftBreak", "LineBreak"):
        items.pop(0)
    return items


def _header(level: int, inlines: list, unnumbered: bool = False) -> dict:
    inlines = _trim(inlines)
    return {"t": "Header", "c": [min(level, 6), ["", ["unnumbered"] if unnumbered else [], []], inlines]}


def _clause(level: int, inlines: list) -> dict:
    return {"t": "Clause", "c": [max(1, min(level, 6)), inlines]}


def _count(state: _State, kind: str, level: int, typed: str | None) -> None:
    """Compare a typed number with the numbering that Primula will give to this heading or clause."""
    if kind == "heading":
        state.heading_counters[level] += 1
        for deeper in range(level + 1, 7):
            state.heading_counters[deeper] = 0
        state.clause_counters = [0] * 8
        state.clause_level = 0
        state.prefix = ".".join(str(state.heading_counters[i]) for i in range(1, level + 1))
        expected = state.prefix
    else:
        state.clause_counters[level] += 1
        for deeper in range(level + 1, 8):
            state.clause_counters[deeper] = 0
        parts = [state.prefix] if state.prefix else []
        parts += [str(state.clause_counters[i]) for i in range(1, level + 1)]
        expected = ".".join(parts)
    if typed is not None and typed != expected:
        state.report.note("a typed number differs from the numbering of Primula (the numbers of the result follow the structure)")


def _emit_heading(state: _State, level: int, inlines: list, typed: str | None, out: list) -> None:
    level = _fix_level(state, level)
    state.heading_level = level
    state.report.count("headings recognized")
    _count(state, "heading", level, typed)
    out.append(_header(level, _with_number(state, typed, inlines)))


def _clause_level(state: _State, level: int) -> int:
    """No skipped clause level (the translator reports P4204): at most one below the last clause."""
    fixed = max(1, min(level, state.clause_level + 1))
    if fixed != level:
        state.report.note("a clause level was corrected (levels do not skip)")
    state.clause_level = fixed
    return fixed


def _emit_clause(state: _State, level: int, inlines: list, typed: str | None, out: list) -> None:
    level = _clause_level(state, level)
    state.report.count("clauses recognized")
    _count(state, "clause", level, typed)
    out.append(_clause(level, _with_number(state, typed, inlines)))


def _with_number(state: _State, typed: str | None, inlines: list) -> list:
    """With ``keep_numbers`` the typed number stays at the beginning of the text."""
    if typed is not None and state.options.keep_numbers:
        return [{"t": "Str", "c": typed + "."}, {"t": "Space"}] + inlines
    return inlines


def _fix_level(state: _State, level: int) -> int:
    """No level skips: the first heading is level 1, a heading is at most one level below the last one."""
    fixed = max(1, min(level, state.heading_level + 1))
    if fixed != level:
        state.report.note("a heading level was corrected (levels do not skip)")
    return fixed


def _list_heading(state: _State, block: dict, depth: int, out: list) -> bool:
    """The numbering of Word headings: a list of one item.  False when the list is a real list (nothing is written)."""
    items = block["c"][1]
    if len(items) != 1:
        return False
    item = items[0]
    lead = item[0] if item and item[0]["t"] in ("Plain", "Para") else None
    rest = item[1:] if lead else item
    nested = [b for b in rest if b["t"] == "OrderedList"]
    others = [b for b in rest if b["t"] != "OrderedList"]
    if lead is None and not nested:
        return False
    if lead is not None:
        text = plain(lead["c"])
        if not text.strip():
            lead = None
        elif _heading_like(text):
            state.headed = True
            _emit_heading(state, depth, lead["c"], None, out)
        else:
            _emit_clause(state, depth - state.heading_level if state.heading_level else depth, lead["c"], None, out)
    for sub in nested:
        if not _list_heading(state, sub, depth + 1, out):
            out.append(sub)
    out.extend(others)
    return True


def _toc_list(block: dict) -> bool:
    """A list of the internal links only — the table of contents made by Word."""
    if block["t"] not in ("BulletList", "OrderedList"):
        return False
    items = block["c"] if block["t"] == "BulletList" else block["c"][1]

    def links(entries: list) -> bool:
        for item in entries:
            for b in item:
                if b["t"] in ("Plain", "Para"):
                    real = [i for i in b["c"] if i["t"] not in ("Space", "SoftBreak")]
                    if not real or not all(i["t"] == "Link" for i in real) or not all(i["c"][2][0].startswith("#") for i in real):
                        return False
                elif b["t"] in ("BulletList", "OrderedList"):
                    if not links(b["c"] if b["t"] == "BulletList" else b["c"][1]):
                        return False
                else:
                    return False
        return True

    return bool(items) and links(items)


def normalize(blocks: list, report: Report, options: Options | None = None) -> list:
    """The blocks with the structure recognized (see the module description).

    Args:
        blocks: the blocks of the pandoc tree (the top level of the document).
        report: receives the counts and the notes.
        options: ``keep_numbers``, ``structure``.

    Returns:
        New blocks; ``Header`` and ``Clause`` (``{"t": "Clause", "c": [level, inlines]}``) blocks stand where the
        structure was recognized, the others are as they were.
    """
    options = options or Options()
    if not options.structure:
        return blocks
    state = _State(report, options)
    blocks = _unwrap(blocks)
    # Is the document headed? (a typed or listed first-level heading exists)
    state.headed = any(_numbered_heading(b) for b in blocks) or any(b["t"] == "Header" for b in blocks) or any(
        b["t"] == "OrderedList" and len(b["c"][1]) == 1 for b in blocks)
    out: list[dict] = []
    index = 0
    while index < len(blocks):
        block = blocks[index]
        kind = block["t"]
        # The typed table of contents: lines with dot leaders, or "Contents" over a list of internal links.
        if kind in ("Plain", "Para") and _LEADER.match(plain(block["c"]).strip()):
            end = index
            while end < len(blocks) and blocks[end]["t"] in ("Plain", "Para") and _LEADER.match(plain(blocks[end]["c"]).strip()):
                end += 1
            if end - index >= 3:
                _toc(out, report)
                index = end
                continue
        if kind in ("Plain", "Para") and plain(block["c"]).strip().lower().rstrip(":") in {w.rstrip(":") for w in _HEADING_WORDS} \
                and index + 1 < len(blocks) and _toc_list(blocks[index + 1]):
            _toc(out, report)
            index += 2
            continue
        if _toc_list(block):
            _toc(out, report)
            index += 1
            continue
        if kind == "OrderedList" and _list_heading(state, block, 1, out):
            index += 1
            continue
        if kind in ("Plain", "Para"):
            handled = _paragraph(state, block, blocks, index, out)
            if handled:
                index += 1
                continue
        if kind == "Header" and not plain(block["c"][2]).strip():
            report.note("an empty heading")
            index += 1
            continue
        if kind == "Header":
            level = _fix_level(state, block["c"][0])
            state.heading_level = level
            inlines = block["c"][2]
            stripped = _strip_number(inlines)
            number = None
            if stripped is not None and plain(stripped[1]).strip():
                number, inlines = stripped[0], _with_number(state, stripped[0], stripped[1])
                state.report.count("typed numbers removed")
            _count(state, "heading", level, number)
            block = {"t": "Header", "c": [level, block["c"][1], inlines]}
        elif kind == "Clause":
            level, inlines = block["c"]
            stripped = _strip_number(inlines)
            number = None
            if stripped is not None and plain(stripped[1]).strip():
                number, inlines = stripped[0], _with_number(state, stripped[0], stripped[1])
                state.report.count("typed numbers removed")
            level = _clause_level(state, level)
            _count(state, "clause", level, number)
            block = {"t": "Clause", "c": [level, inlines]}
        out.append(block)
        index += 1
    return out


def _unwrap(blocks: list) -> list:
    """Divs (the styles of Word) are opened: their content stands in the flow."""
    out = []
    for block in blocks:
        if block["t"] == "Div":
            out += _unwrap(block["c"][1])
        else:
            out.append(block)
    return out


def _numbered_heading(block: dict) -> bool:
    if block["t"] not in ("Plain", "Para"):
        return False
    stripped = _strip_number(block["c"])
    if stripped is None or "." in stripped[0]:
        return False
    text = plain(stripped[1])
    return _heading_like(text) and (_is_bold_only(block["c"]) or text.isupper() or len(text) < 60)


def _toc(out: list, report: Report) -> None:
    # The title above the typed contents is made by |toc() itself.
    if out and out[-1]["t"] in ("Plain", "Para") and plain(out[-1]["c"]).strip().lower().rstrip(":") in {w.rstrip(":") for w in _HEADING_WORDS}:
        out.pop()
    report.count("table of contents → |toc()")
    out.append({"t": "RawBlock", "c": ["primula", "|toc()"]})


def _paragraph(state: _State, block: dict, blocks: list, index: int, out: list) -> bool:
    """A typed number or a bold line.  False when the paragraph is an ordinary one."""
    inlines = block["c"]
    stripped = _strip_number(inlines)
    if stripped is not None:
        number, rest = stripped
        text = plain(rest)
        if not text.strip():
            return False
        components = number.count(".") + 1
        heading = _heading_like(text) and (state.headed or components == 1) and (
            components == 1 or _is_bold_only(inlines) or text.isupper() or _followed_by_deeper(blocks, index, number))
        if heading:
            _emit_heading(state, components, rest, number, out)
        else:
            level = components - state.heading_level if state.headed and state.heading_level else components
            _emit_clause(state, level if level >= 1 else 1, rest, number, out)
        return True
    text_of_line = plain(inlines).strip()
    # A bold line before the first real heading of a headed document is the title page (a copyright, a title), not a heading.
    if _is_bold_only(inlines) and _heading_like(text_of_line) and len(text_of_line) > 2 and not text_of_line.startswith("©") \
            and (state.heading_level >= 1 or not state.headed):
        # A bold line is a heading when a paragraph follows it (not a caption of a table, not a lone label).
        following = blocks[index + 1]["t"] if index + 1 < len(blocks) else None
        if following in ("Para", "Plain", "BulletList", "OrderedList", "Table"):
            text = _strip_bold(inlines)
            _emit_heading(state, state.heading_level + 1 if state.heading_level else 1, text, None, out)
            state.report.count("bold lines → headings")
            return True
    return False


def _strip_bold(inlines: list) -> list:
    """The content of the strong forms of a bold line (the heading is bold already)."""
    out: list = []
    for item in inlines:
        if item["t"] == "Strong":
            out += item["c"]
        elif item["t"] == "Span" and _is_bold_only(item["c"][1]):
            out += _strip_bold(item["c"][1])
        else:
            out.append(item)
    return out


def _followed_by_deeper(blocks: list, index: int, number: str) -> bool:
    """The next paragraph starts with a number one level deeper under this one ("2.1" then "2.1.1")."""
    if index + 1 >= len(blocks) or blocks[index + 1]["t"] not in ("Plain", "Para"):
        return False
    after = _strip_number(blocks[index + 1]["c"])
    return after is not None and after[0].startswith(number + ".")
