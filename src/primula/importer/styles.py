"""The styles of the source in the import (stage 19.3.3): Word paragraph and character styles → Primula.

pandoc reads a DOCX with ``+styles``: a paragraph style becomes a ``Div`` and a character style a ``Span`` with
the attribute ``custom-style``.  This module maps the style names to what Primula has:

* the built-in rules know the headings of Word and Primula's own style names (a DOCX made by ``primula export``
  comes back as ``|>`` clauses and ``|.Requisites:`` paragraphs);
* the file ``import-styles.yaml`` (next to the result or in a directory above it, or ``--styles FILE``) adds the
  styles of the author's documents::

      paragraphs:
        "Заголовок 1": {heading: 1}
        "Пункт": {clause: 1}
        "Реквізити": {style: Requisites}
        "Службовий": ignore          # the paragraph is dropped
        "Основний": plain            # an ordinary paragraph
      characters:
        "Важливе": {style: Strong}   # |.Strong{…}

* a style that nothing maps stays an ordinary paragraph and is named in the report (``--list-styles`` shows them
  all, ``--write-styles FILE`` writes a skeleton of the file for them).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from primula.importer.convert import Report

#: Styles of Word that mean "an ordinary paragraph / character": nothing is written for them.
PLAIN = {"normal", "body text", "first paragraph", "compact", "default", "normal (web)", "list paragraph", "table grid",
         "footnote text", "footnote reference", "hyperlink", "default paragraph font", "table paragraph", "text body",
         "standard", "plain text", "no spacing", "основной текст", "обычный", "звичайний", "основний текст",
         "абзац списка", "абзац списку", "table contents", "table heading", "contents heading", "header", "footer",
         "верхний колонтитул", "нижний колонтитул"}
_HEADING = re.compile(r"^(?:heading|заголовок|заголовок)\s*([1-6])$", re.IGNORECASE)
#: Word names of a quote and of code.
_QUOTE = {"quote", "block text", "intense quote", "цитата", "цитата"}
_CODE = {"source code", "code", "preformatted text", "verbatim char"}


def primula_style_names() -> dict[str, set[str]]:
    """The names of the styles of the standard sets (``std/styles/*``) by kind (``paragraph``, ``character``)."""
    from primula.describe import describe_styles
    from primula.diagnostics import DiagnosticSink
    from primula.i18n import Catalog
    from primula.source import SourceManager
    from primula.evaluate.loader import STDLIB

    names: dict[str, set[str]] = {"paragraph": set(), "character": set()}
    # The default styles and the sets of the kit (business, letter, technical, report, compact).
    for path in sorted((STDLIB / "styles").glob("*.s.prml")):
        try:
            data = describe_styles(path, {}, SourceManager(), DiagnosticSink())
        except Exception:  # noqa: BLE001 - without the names only the built-in rules of Word work
            continue
        for style in data.get("styles", []):
            if style.get("kind") in names:
                names[style["kind"]].add(style["name"])
    return names


class StyleMap:
    """What a style name means: ``("heading", N)``, ``("clause", N)``, ``("style", Name)``, ``("plain",)``,
    ``("ignore",)`` or ``None`` (unmapped).  The author's file overrides the built-in rules."""

    def __init__(self, paragraphs: dict[str, tuple] | None = None, characters: dict[str, tuple] | None = None) -> None:
        self.paragraphs = {k.lower(): v for k, v in (paragraphs or {}).items()}
        self.characters = {k.lower(): v for k, v in (characters or {}).items()}
        self._known = primula_style_names()

    def paragraph(self, name: str) -> tuple | None:
        key = name.lower()
        if key in self.paragraphs:
            return self.paragraphs[key]
        match = _HEADING.match(name.strip())
        if match:
            return ("heading", int(match.group(1)))
        if name in ("Clause",):
            return ("clause", 1)
        if name in ("SubClause",):
            return ("clause", 2)
        if re.fullmatch(r"Heading[1-6]", name):
            return ("heading", int(name[-1]))
        if key in PLAIN:
            return ("plain",)
        if key in _QUOTE:
            return ("style", "Quote")
        if key in _CODE:
            return ("plain",)
        if name in self._known["paragraph"]:
            return ("style", name)
        return None

    def character(self, name: str) -> tuple | None:
        key = name.lower()
        if key in self.characters:
            return self.characters[key]
        if key in PLAIN or key in {"strong", "emphasis", "default paragraph font"}:
            return ("plain",)
        if name in self._known["character"]:
            return ("style", name)
        return None


def _entry(value: Any) -> tuple | None:
    """A value of the file: ``{heading: N}``, ``{clause: N}``, ``{style: Name}``, ``plain``, ``ignore``."""
    if value in ("plain", "ignore"):
        return (value,)
    if isinstance(value, dict) and len(value) == 1:
        (key, argument), = value.items()
        if key in ("heading", "clause") and isinstance(argument, int) and 1 <= argument <= 6:
            return (key, argument)
        if key == "style" and isinstance(argument, str) and argument:
            return ("style", argument)
    return None


def load_map(path: Path | None) -> tuple[StyleMap, list[str]]:
    """The style map of a file (or only the built-in rules) and the problems of the file."""
    problems: list[str] = []
    paragraphs: dict[str, tuple] = {}
    characters: dict[str, tuple] = {}
    if path is not None:
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except (OSError, yaml.YAMLError) as exc:
            return StyleMap(), [f"{path}: {exc}"]
        for section, target in (("paragraphs", paragraphs), ("characters", characters)):
            for name, value in (data.get(section) or {}).items():
                entry = _entry(value)
                if entry is None:
                    problems.append(f"{path}: {section}: '{name}': {value!r} is not heading: N, clause: N, style: Name, plain or ignore")
                elif section == "characters" and entry[0] in ("heading", "clause"):
                    problems.append(f"{path}: characters: '{name}': a character style cannot be a heading or a clause")
                else:
                    target[str(name)] = entry
        unknown = set(data) - {"paragraphs", "characters"}
        problems += [f"{path}: unknown section '{key}'" for key in sorted(unknown)]
    return StyleMap(paragraphs, characters), problems


def find_map_file(output: Path) -> Path | None:
    """``import-styles.yaml`` in the directory of the result or above it."""
    for directory in (output.resolve().parent, *output.resolve().parent.parents):
        candidate = directory / "import-styles.yaml"
        if candidate.is_file():
            return candidate
    return None


def _style_of(attr: list) -> str | None:
    for key, value in attr[2]:
        if key == "custom-style":
            return value
    return None


def _inlines(items: list, style_map: StyleMap, report: Report) -> list:
    """The inlines with the character styles mapped (``Span`` with ``custom-style``)."""
    out: list = []
    for item in items:
        kind = item["t"]
        content = item.get("c")
        if kind == "Span":
            inner = _inlines(content[1], style_map, report)
            name = _style_of(content[0])
            if name is None:
                out.append({"t": "Span", "c": [content[0], inner]})
                continue
            report.styles[("character", name)] += 1
            result = style_map.character(name)
            if result is None:
                report.unmapped[("character", name)] += 1
                out += inner
            elif result[0] == "style":
                out.append({"t": "StyledSpan", "c": [result[1], inner]})
            elif result[0] == "ignore":
                report.count("character styles dropped")
            else:
                out += inner
        elif kind in ("Strong", "Emph", "Underline", "Strikeout", "Superscript", "Subscript", "SmallCaps"):
            out.append({"t": kind, "c": _inlines(content, style_map, report)})
        elif kind == "Quoted":
            out.append({"t": kind, "c": [content[0], _inlines(content[1], style_map, report)]})
        elif kind == "Link":
            out.append({"t": kind, "c": [content[0], _inlines(content[1], style_map, report), content[2]]})
        else:
            out.append(item)
    return out


def apply_styles(blocks: list, style_map: StyleMap, report: Report) -> list:
    """The blocks with the paragraph styles mapped: headings and clauses stand as such, ``|.Name:`` paragraphs as
    ``Styled`` blocks, dropped ones are gone, the others are unwrapped; the use of every style is counted."""
    out: list = []
    for block in blocks:
        kind = block["t"]
        content = block.get("c")
        if kind == "Div":
            name = _style_of(content[0])
            inner = apply_styles(content[1], style_map, report)
            if name is None:
                out.append({"t": "Div", "c": [content[0], inner]})
                continue
            report.styles[("paragraph", name)] += 1
            result = style_map.paragraph(name)
            if result is None:
                report.unmapped[("paragraph", name)] += 1
                out += inner
            elif result[0] == "ignore":
                report.count("paragraphs dropped by style")
            elif result[0] in ("heading", "clause", "style"):
                for sub in inner:
                    if sub["t"] in ("Para", "Plain") and any(i["t"] != "Space" for i in sub["c"]):
                        if result[0] == "heading":
                            out.append({"t": "Header", "c": [result[1], ["", [], []], sub["c"]]})
                        elif result[0] == "clause":
                            out.append({"t": "Clause", "c": [result[1], sub["c"]]})
                        else:
                            out.append({"t": "Styled", "c": [result[1], sub["c"]]})
                    else:
                        out.append(sub)
            else:
                out += inner
        elif kind in ("Para", "Plain"):
            out.append({"t": kind, "c": _inlines(content, style_map, report)})
        elif kind == "Header":
            out.append({"t": kind, "c": [content[0], content[1], _inlines(content[2], style_map, report)]})
        elif kind in ("BulletList", "OrderedList"):
            items = content if kind == "BulletList" else content[1]
            mapped = [apply_styles(item, style_map, report) for item in items]
            out.append({"t": kind, "c": mapped if kind == "BulletList" else [content[0], mapped]})
        elif kind == "BlockQuote":
            out.append({"t": kind, "c": apply_styles(content, style_map, report)})
        elif kind == "Table":
            out.append(_table(block, style_map, report))
        else:
            out.append(block)
    return out


def _table(block: dict, style_map: StyleMap, report: Report) -> dict:
    """The styles inside the cells of a table."""
    attr, caption, specs, head, bodies, foot = block["c"]

    def row(r: list) -> list:
        return [r[0], [[c[0], c[1], c[2], c[3], apply_styles(c[4], style_map, report)] for c in r[1]]]

    return {"t": "Table", "c": [attr, caption, specs, [head[0], [row(r) for r in head[1]]],
                                 [[b[0], b[1], [row(r) for r in b[2]], [row(r) for r in b[3]]] for b in bodies],
                                 [foot[0], [row(r) for r in foot[1]]]]}


def describe_styles_used(report: Report, style_map: StyleMap) -> list[str]:
    """The styles of the source with their use and what they became, as lines of text."""
    lines = []
    for (kind, name), count in sorted(report.styles.items(), key=lambda item: (-item[1], item[0])):
        result = style_map.paragraph(name) if kind == "paragraph" else style_map.character(name)
        what = "unmapped" if result is None else "plain" if result[0] == "plain" else \
            f"{result[0]} {result[1]}" if len(result) > 1 else result[0]
        lines.append(f"  {kind} style '{name}': {count} → {what}")
    return lines


def skeleton(report: Report, style_map: StyleMap) -> str:
    """The text of ``import-styles.yaml`` for the styles found: the built-in meaning where there is one, ``plain`` otherwise."""
    sections: dict[str, list[str]] = {"paragraph": [], "character": []}
    for (kind, name), _count in sorted(report.styles.items()):
        result = style_map.paragraph(name) if kind == "paragraph" else style_map.character(name)
        if result is None:
            value = "plain    # not mapped yet: heading: N, clause: N, style: Name, plain or ignore"
        elif result[0] in ("plain", "ignore"):
            value = result[0]
        else:
            value = f"{{{result[0]}: {result[1]}}}"
        sections[kind].append(f'  "{name}": {value}')
    return "paragraphs:\n" + "\n".join(sections["paragraph"] or ["  {}"]) + "\ncharacters:\n" + "\n".join(sections["character"] or ["  {}"]) + "\n"
