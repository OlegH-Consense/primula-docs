"""Pandoc AST → Primula markup (the converter of ``primula import`` and of ``tools/md_to_prml.py``).

pandoc reads the source into its document tree (``pandoc -t json``); :class:`Converter` walks the
tree and writes the Primula text: headings ``|<``, paragraphs, lists ``|-``/``|#``, tables ``|table``
(spans, alignment, column widths), images ``|img``, figures ``|figure``, inline forms ``|*{}``,
``|/{}``, links ``|link``, footnotes ``|footnote{}``.

Text is escaped for Primula: ``|`` → ``||``, ``{``/``}`` → ``|{``/``|}``.  A construct without a
Primula counterpart (raw HTML, horizontal rules, comments) is dropped and counted in :class:`Report`:
the converter never invents markup it cannot express.

pandoc AST reference: https://hackage.haskell.org/package/pandoc-types (Text.Pandoc.Definition).
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Any

#: Primula short forms of the pandoc inline styles.
INLINE_FORMS = {"Strong": "*", "Emph": "/", "Underline": "_", "Superscript": "^", "Subscript": ",",
                "Strikeout": "—"}

#: Units of the sizes that pandoc gives for images (millimetres per unit); ``px`` at 96 dpi.
_UNITS_MM = {"mm": 1.0, "cm": 10.0, "in": 25.4, "pt": 25.4 / 72, "px": 25.4 / 96, "pc": 25.4 / 6}


def escape(text: str) -> str:
    """Text for Primula: a literal bar and literal braces (specification 3.3)."""
    return text.replace("|", "||").replace("{", "|{").replace("}", "|}")


def string(text: str) -> str:
    """A Python string literal of the core (double quotes)."""
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def length_mm(value: str) -> str | None:
    """A size of pandoc (``0.69133in``, ``15.173cm``, ``120px``) as Primula millimetres (``17.6mm``); ``None`` for ``%`` or an unknown form."""
    match = re.fullmatch(r"\s*([0-9]*\.?[0-9]+)\s*([a-z]*)\s*", value or "")
    if match is None:
        return None
    unit = match.group(2) or "px"
    if unit not in _UNITS_MM:
        return None
    millimetres = float(match.group(1)) * _UNITS_MM[unit]
    return f"{millimetres:.1f}".rstrip("0").rstrip(".") + "mm"


@dataclass
class Report:
    """What the conversion did: counts of the converted elements and the notes about what was left out."""

    counts: Counter = field(default_factory=Counter)
    notes: Counter = field(default_factory=Counter)
    #: The styles of the source: (kind, name) → how many times; those that no rule maps.
    styles: Counter = field(default_factory=Counter)
    unmapped: Counter = field(default_factory=Counter)

    def count(self, what: str) -> None:
        self.counts[what] += 1

    def note(self, text: str) -> None:
        self.notes[text] += 1

    def lines(self) -> list[str]:
        """The report as lines of text."""
        done = ", ".join(f"{name} {number}" for name, number in sorted(self.counts.items()))
        out = [f"converted: {done}" if done else "converted: nothing"]
        out += [f"  left out: {text} ({number})" for text, number in sorted(self.notes.items())]
        out += [f"  style not mapped: {kind} '{name}' ({number}) — import-styles.yaml, --write-styles"
                for (kind, name), number in sorted(self.unmapped.items())]
        return out


class Converter:
    """Writes Primula text from pandoc blocks.

    Attributes:
        anchors: pandoc link targets (``#id``, ``file.md``, ``file.md#id``) → Primula IDs;
            filled by the caller for joined documents, used for internal links.
        heading_ids: pandoc heading identifiers of the current file → Primula IDs.
        numbered: whether headings get numbers (``number=False`` otherwise).
        report: the counts and notes of the conversion.
    """

    def __init__(self, numbered: bool = True, report: Report | None = None, images: dict[str, str] | None = None) -> None:
        #: Paths of images as pandoc gives them → the paths to write (a converted image replaces the original).
        self.images = images or {}
        self.anchors: dict[str, str] = {}
        self.heading_ids: dict[str, str] = {}
        self.numbered = numbered
        self.report = report or Report()

    # --- inlines ------------------------------------------------------------------------------

    def inlines(self, items: list) -> str:
        """Primula text of pandoc inlines (one line: soft breaks become spaces)."""
        out = []
        for item in items:
            kind, content = item["t"], item.get("c")
            if kind == "Str":
                out.append(escape(content))
            elif kind in ("Space", "SoftBreak"):
                out.append(" ")
            elif kind == "LineBreak":
                out.append("|\\")
            elif kind in INLINE_FORMS:
                inner = self.inlines(content)
                out.append(f"|{INLINE_FORMS[kind]}{{{inner}}}" if inner.strip() else inner)
            elif kind == "SmallCaps":
                out.append(self.inlines(content))
            elif kind == "Code":
                out.append("|`{" + escape(content[1]) + "}")
            elif kind == "Quoted":
                left, right = ("“", "”") if content[0]["t"] == "DoubleQuote" else ("‘", "’")
                out.append(left + self.inlines(content[1]) + right)
            elif kind == "Link":
                out.append(self.link(content))
            elif kind == "Image":
                out.append(self.image(content))
            elif kind == "StyledSpan":
                inner = self.inlines(content[1])
                out.append(f"|.{content[0]}{{{inner}}}" if inner.strip() else inner)
            elif kind in ("Span", "Cite"):
                out.append(self.inlines(content[1]))
            elif kind == "Note":
                self.report.count("footnotes")
                out.append("|footnote{" + self.flatten(content).strip() + "}")
            elif kind == "Math":
                self.report.note("a formula (its source is kept as text)")
                out.append(escape(content[1]))
            elif kind == "RawInline":
                self.report.note("raw markup of the source format")
        return "".join(out)

    def link(self, content: list) -> str:
        """``|link`` to an internal ID (``#id``) or to an address; a link to a missing anchor stays external."""
        text = self.inlines(content[1])
        target = content[2][0]
        internal = self.anchors.get(target)
        self.report.count("links")
        if internal is not None:
            return f"|link({string('#' + internal)}){{{text}}}"
        if target.startswith("#"):
            return text    # an internal link of the source without a target here: the text stays
        return f"|link({string(target)}){{{text}}}" if text else f"|link({string(target)})"

    def image(self, content: list) -> str:
        """``|img("path", width=…, height=…)``; the size of the source is kept in millimetres."""
        attr, _alt, target = content
        arguments = [string(self.images.get(target[0], target[0]))]
        for key in ("width", "height"):
            for name, value in attr[2]:
                size = length_mm(value) if name == key else None
                if size:
                    arguments.append(f"{key}={string(size)}")
        self.report.count("images")
        return "|img(" + ", ".join(arguments) + ")"

    def flatten(self, blocks: list) -> str:
        """Inline text of blocks joined by line breaks (table cells, footnotes)."""
        parts = []
        for block in blocks:
            kind, content = block["t"], block.get("c")
            if kind in ("Plain", "Para"):
                parts.append(self.inlines(content))
            elif kind == "CodeBlock":
                parts.append("|`{" + escape(content[1]).replace("\n", "}|\\|`{") + "}")
            elif kind in ("BulletList", "OrderedList"):
                items = content if kind == "BulletList" else content[1]
                parts.append("|\\".join("• " + self.flatten(item) for item in items))
            elif kind == "Div":
                parts.append(self.flatten(content[1]))
            elif kind == "Header":
                parts.append("|*{" + self.inlines(content[2]) + "}")
            elif kind == "Figure":
                parts.append(self.flatten(content[2]))
            elif kind == "BlockQuote":
                parts.append(self.flatten(content))
            elif kind == "Table":
                self.report.note("a table inside a table cell (its text is joined)")
        return "|\\".join(p for p in parts if p)

    # --- blocks -------------------------------------------------------------------------------

    def blocks(self, items: list, depth: int = 0) -> list[str]:
        """Primula lines of pandoc blocks; ``depth`` is the list level of the enclosing item."""
        lines: list[str] = []
        for block in items:
            kind, content = block["t"], block.get("c")
            if kind in ("Plain", "Para"):
                text = self.inlines(content)
                if text.strip():
                    self.report.count("paragraphs")
                    lines += [text, ""]
            elif kind == "Header":
                if self.inlines(content[2]).strip():
                    self.report.count("headings")
                    lines += [self.heading(*content), ""]
                else:
                    self.report.note("an empty heading")
            elif kind == "CodeBlock":
                self.report.count("code blocks")
                lines += self.code(content[1]) + [""]
            elif kind in ("BulletList", "OrderedList"):
                self.report.count("lists")
                lines += self.list(kind, content, depth + 1) + [""]
            elif kind == "Table":
                self.report.count("tables")
                lines += self.table(content) + [""]
            elif kind == "Figure":
                lines += self.figure(content) + [""]
            elif kind == "BlockQuote":
                for inner in content:
                    if inner["t"] in ("Plain", "Para"):
                        text = self.inlines(inner["c"])
                        if text.strip():
                            self.report.count("quotes")
                            lines += ["|.Quote: " + text, ""]
                    else:
                        lines += self.blocks([inner], depth)
            elif kind == "Div":
                lines += self.blocks(content[1], depth)
            elif kind == "LineBlock":
                lines += ["|\\".join(self.inlines(line) for line in content), ""]
            elif kind == "DefinitionList":
                for term, definitions in content:
                    lines += ["|.DefinitionTerm: " + self.inlines(term), ""]
                    for definition in definitions:
                        lines += ["|.DefinitionText: " + self.flatten(definition), ""]
            elif kind == "Styled":
                text = self.inlines(content[1])
                if text.strip():
                    self.report.count("styled paragraphs")
                    lines += [f"|.{content[0]}: {text}", ""]
            elif kind == "Clause":
                lines += ["|" + ">" * content[0] + " " + self.inlines(content[1]), ""]
            elif kind == "RawBlock":
                if content[0] == "primula":
                    lines += [content[1], ""]   # written by the normalizer: Primula text as it is
                else:
                    self.report.note("raw markup of the source format")
            elif kind == "HorizontalRule":
                self.report.note("a horizontal rule")
        return lines

    def figure(self, content: list) -> list[str]:
        """A pandoc figure: ``|figure("path", width=…):`` with the caption as its body; without a caption — ``|img``."""
        _attr, caption, blocks = content
        images = [inline for block in blocks if block["t"] in ("Plain", "Para") for inline in block["c"] if inline["t"] == "Image"]
        if not images:
            return self.blocks(blocks)
        text = self.flatten(caption[1]) if caption and len(caption) > 1 else ""
        call = self.image(images[0].get("c"))[len("|img("):-1]
        self.report.count("figures")
        if not text.strip():
            return ["|img(" + call + ")"]
        return [f"|figure({call}):", text, "|end figure"]

    def heading(self, level: int, attr: list, items: list) -> str:
        """``|<…(id=…) text``; the pandoc identifier is mapped through ``heading_ids``."""
        args = []
        target = self.heading_ids.get(attr[0])
        if target:
            args.append(f"id={string(target)}")
        if not self.numbered or "unnumbered" in attr[1]:
            args.append("number=False")
        head = "|" + "<" * min(level, 6) + (f"({', '.join(args)})" if args else "")
        return f"{head} {self.inlines(items)}"

    @staticmethod
    def code(text: str) -> list[str]:
        """A code block: ``|verbatim`` in the paragraph style ``Preformatted``; a marker when the text has ``|end``."""
        end = "|end"
        if any(line.strip() == "|end" for line in text.splitlines()):
            end = "~~~end-of-code~~~"
        opening = "|verbatim:" if end == "|end" else f"|verbatim(end={string(end)}):"
        return ["|.Preformatted:", opening, *text.splitlines(), end, "|end.Preformatted"]

    def list(self, kind: str, content: list, level: int, parents: str = "") -> list[str]:
        """List items ``|-``/``|#`` of a level (specification 5.4).

        An item is its first paragraph on the marker line.  When an item has more blocks
        (paragraphs, code, tables), the list is written as the environment ``|list:`` …
        ``|end list``: there blank lines do not split the list and a block belongs to the
        last item of the top level of the environment; a nested list with such items is
        a nested environment of its own.
        """
        items = content if kind == "BulletList" else content[1]
        marker = ("-" if kind == "BulletList" else "#")
        prefix = "|" + parents + marker   # a nested marker repeats the markers of the parent items

        def lead(item: list) -> bool:
            return bool(item) and item[0]["t"] in ("Plain", "Para")

        def needs_environment(entries: list) -> bool:
            """An item has blocks other than lists, or a nested list needs the environment (a nested
            environment stands inside an environment: the specification 5.4)."""
            for item in entries:
                for b in (item[1:] if lead(item) else item):
                    if b["t"] not in ("BulletList", "OrderedList"):
                        return True
                    if needs_environment(b["c"] if b["t"] == "BulletList" else b["c"][1]):
                        return True
            return False

        complex_ = needs_environment(items)
        lines: list[str] = ["|list:"] if complex_ else []
        for item in items:
            # An item without a leading paragraph still needs text on its line: a no-break space.
            lines.append(prefix + " " + (self.inlines(item[0]["c"]) if lead(item) else "|~"))
            for block in item[1:] if lead(item) else item:
                if block["t"] in ("BulletList", "OrderedList"):
                    lines += self.list(block["t"], block["c"], level + 1, parents + marker)
                else:
                    lines += [""] + self.blocks([block], level)
        if complex_:
            lines.append("|end list")
        return lines

    def table(self, content: list) -> list[str]:
        """``|table`` with a header; spans, alignment and column widths of the source are kept."""
        _attr, _caption, specs, head, bodies, _foot = content
        rows: list[list[tuple[str, str]]] = []   # per row: (cell arguments, text)
        header = 0
        spans = False

        def cell(entry: list) -> tuple[str, str]:
            nonlocal spans
            _a, align, rowspan, colspan, blocks = entry
            args = []
            if colspan > 1:
                args.append(f"span={colspan}")
            if rowspan > 1:
                args.append(f"rows={rowspan}")
            if colspan > 1 or rowspan > 1:
                spans = True
            kind = align["t"]
            if kind in ("AlignCenter", "AlignRight", "AlignLeft"):
                args.append(f'align="{kind[5:].lower()}"')
            return ", ".join(args), self.flatten(blocks)

        for row in head[1]:
            rows.append([cell(c) for c in row[1]])
            header += 1
        for body in bodies:
            for row in body[2] + body[3]:
                rows.append([cell(c) for c in row[1]])
        if not rows:
            return []
        columns = len(specs)
        known = [spec[1].get("c") if isinstance(spec[1], dict) else None for spec in specs]
        if columns and all(isinstance(value, (int, float)) and value > 0 for value in known):
            cols = ", ".join(string(f"{max(1, round(value * 100))}*") for value in known)
        else:
            cols = ", ".join(string(f"{w}*") for w in self._text_widths(rows, columns))
        lines = [f"|table(cols=[{cols}], header={header}):"]
        for row in rows:
            parts = []
            for index, (args, text) in enumerate(row):
                mark = "|&" + (f"({args})" if args else "")
                if index == 0:
                    parts.append(f"|:{mark} {text}" if args else f"|: {text}")
                else:
                    parts.append(f"{mark} {text}".rstrip() if text else mark)
            lines.append(" ".join(parts) if parts else "|:")
        lines.append("|end table")
        return lines

    @staticmethod
    def _text_widths(rows: list[list[tuple[str, str]]], columns: int) -> list[int]:
        """A column is as wide as its typical text (the upper quartile of the lengths), not narrower than its
        longest word (no word is broken), not wider than 60 characters; a short column (all values up to 12
        characters) fits its longest value; two characters more for the padding of the cell."""
        widths = []
        for index in range(columns):
            texts = [row[index][1] for row in rows if index < len(row)]
            lengths = sorted(len(text) for text in texts)
            typical = lengths[len(lengths) * 3 // 4] if lengths else 1
            word = max((len(w) for text in texts for w in text.split()), default=1)
            longest = lengths[-1] if lengths else 1
            short = longest if longest <= 12 else 0
            widths.append(min(max(4, typical, word, short), 60) + 2)
        return widths
