"""``styles.xml``: named styles of the document (specification 11, 15).

* default paragraph style — ``defaults`` of the styles modules and the
  document language (decision 65: ``fo:language``/``fo:country``);
* named paragraph and character styles with ``style:parent-style-name``
  (one ODF style per Primula style, materialised variants included);
* list styles (``text:list-style``, levels 1-10, label alignment mode);
* page layouts and master pages for every page style (13.5 uses the
  default page style, decision 64; page changes come at stage 13.8);
* configuration of footnotes and endnotes (``text:notes-configuration``)
  and the footnote separator line of page layouts (5.10, decision 76).

Table, block and frame styles of the language have no named ODF
counterparts: they are written as automatic styles in ``content.xml``.
"""

from __future__ import annotations

from decimal import Decimal
from fractions import Fraction
from typing import Any, Callable
import xml.etree.ElementTree as ET

from primula.core.values import Length
from primula.odf import units
from primula.odf.props import Fonts, paragraph_attrs, text_attrs
from primula.odf.xml import ODF_VERSION, el, sub
from primula.styles.system import StyleSystem

#: Paper sizes in millimetres (7.2).
PAPER: dict[str, tuple[Fraction, Fraction]] = {
    "A4": (Fraction(210), Fraction(297)), "A5": (Fraction(148), Fraction(210)),
    "A3": (Fraction(297), Fraction(420)), "Letter": (Fraction(2159, 10), Fraction(2794, 10)),
}
_DEFAULT_MARGIN = Fraction(20)


def page_geometry(props: dict[str, Any]) -> dict[str, Fraction]:
    """Page width, height and margins in millimetres from page style properties."""
    size = props.get("size", "A4")
    if isinstance(size, tuple):
        width, height = units.to_mm(size[0]), units.to_mm(size[1])
    else:
        width, height = PAPER.get(size, PAPER["A4"])
    if props.get("orientation") == "landscape" and width < height:
        width, height = height, width
    margins = {side: _DEFAULT_MARGIN for side in ("top", "right", "bottom", "left")}
    margin = props.get("margin")
    if isinstance(margin, tuple):
        for side, value in zip(("top", "right", "bottom", "left"), margin):
            margins[side] = units.to_mm(value)
    elif isinstance(margin, Length):
        margins = {side: units.to_mm(margin) for side in margins}
    for side in margins:
        if isinstance(props.get(f"margin_{side}"), Length):
            margins[side] = units.to_mm(props[f"margin_{side}"])
    return {"width": width, "height": height, **margins,
            "text_width": width - margins["left"] - margins["right"]}


def _mm(value: Fraction) -> str:
    return units.mm(units.from_mm(value))


def build_styles(system: StyleSystem, language: str | None, fonts: Fonts, structure: Any = None,
                 pages: Any = None, write_part: Callable[..., None] | None = None) -> ET.Element:
    """Build the ``office:document-styles`` element.

    Args:
        system: the style system.
        language: document language tag.
        fonts: font registry.
        structure: result of the structure phase (notes settings) or ``None``.
        pages: result of the pages phase (headers, footers, watermarks) or ``None``.
        write_part: ``write_part(element, blocks, watermark_frame, automatic)``
            writes header/footer content (and a watermark frame) into
            ``element`` with automatic styles in ``automatic`` (7.6, 8.6).
    """
    root = el("office:document-styles", {"office:version": ODF_VERSION})
    font_decls = sub(root, "office:font-face-decls")
    styles = sub(root, "office:styles")

    default = sub(styles, "style:default-style", {"style:family": "paragraph"})
    sub(default, "style:paragraph-properties", {"style:writing-mode": "page"})
    defaults = dict(system.defaults)
    if language:
        defaults["language"] = language
    sub(default, "style:text-properties", text_attrs(defaults, fonts))

    _graphic_defaults(styles)
    for name, definition in system.styles.items():
        if definition.kind == "frame":
            # Frame styles (8.5): border, padding and background; placement
            # comes from the command arguments.
            style = sub(styles, "style:style", {"style:name": name, "style:display-name": name,
                                                "style:family": "graphic",
                                                "style:parent-style-name": definition.parent or "Frame"})
            sub(style, "style:graphic-properties", _frame_attrs(system.effective(name)))
            continue
        if definition.kind in ("paragraph", "character"):
            family = "paragraph" if definition.kind == "paragraph" else "text"
            style = sub(styles, "style:style", {"style:name": name, "style:display-name": name,
                                                "style:family": family,
                                                "style:parent-style-name": definition.parent,
                                                "style:class": "text" if family == "paragraph" else None})
            if family == "paragraph":
                attrs = paragraph_attrs(definition.props)
                if attrs:
                    sub(style, "style:paragraph-properties", attrs)
            attrs = text_attrs(definition.props, fonts, paragraph=family == "paragraph")
            if attrs:
                sub(style, "style:text-properties", attrs)
        elif definition.kind == "list":
            _list_style(styles, name, system.effective(name).get("levels", {}), language,
                        system.settings.get("profile"))

    footnotes = structure.settings.footnotes if structure is not None else {}
    if structure is not None:
        _notes_configuration(styles, system, footnotes)

    automatic = sub(root, "office:automatic-styles")
    masters = sub(root, "office:master-styles")
    for name, definition in system.styles.items():
        if definition.kind != "page":
            continue
        props = system.effective(name)
        geometry = page_geometry(props)
        layout = sub(automatic, "style:page-layout", {"style:name": f"PL-{name}",
                                                      "style:page-usage": "mirrored" if props.get("mirror") else None})
        layout_props = sub(layout, "style:page-layout-properties", {
            "fo:page-width": _mm(geometry["width"]), "fo:page-height": _mm(geometry["height"]),
            "style:num-format": props.get("number_format", "1"),
            "style:print-orientation": "landscape" if geometry["width"] > geometry["height"] else "portrait",
            "fo:margin-top": _mm(geometry["top"]), "fo:margin-bottom": _mm(geometry["bottom"]),
            "fo:margin-left": _mm(geometry["left"]), "fo:margin-right": _mm(geometry["right"]),
            "fo:background-color": units.color(props["background"]) if props.get("background") else None,
        })
        if isinstance(props.get("cols"), int) and props["cols"] > 1:
            from primula.odf.content import columns_element

            columns_element(layout_props, props["cols"], props.get("col_gap"), props.get("col_rule"), None)
        if structure is not None:
            _footnote_separator(layout_props, footnotes.get("separator"))
        info = pages.masters.get(name) if pages is not None else None
        next_style = props.get("next") if system.kind(props.get("next") or "") == "page" else None
        master = sub(masters, "style:master-page", {"style:name": name, "style:display-name": name,
                                                    "style:page-layout-name": f"PL-{name}",
                                                    "style:next-style-name": next_style})
        if info is not None and write_part is not None:
            _master_parts(master, layout, info, props, automatic, write_part)

    for font in fonts.names:
        sub(font_decls, "style:font-face", {"style:name": font, "svg:font-family": units.font_family(font)})
    return root


def _master_parts(master: ET.Element, layout: ET.Element, info: Any, props: dict[str, Any],
                  automatic: ET.Element, write_part: Callable[..., None]) -> None:
    """Headers and footers of a master page and the watermark (7.6, 8.6; decisions 84, 88, 89).

    ``style:header`` holds the content of odd (right) pages or of all
    pages; ``style:header-left`` appears when ``left`` or ``right`` is set
    (decision 89); ``style:header-first`` for ``first`` (decision 88).  A
    watermark is a frame in every header variant; without a header the
    master page gets one with only the watermark.
    """
    from primula.pages.frames import FrameInfo

    watermark = None
    if info.watermark is not None:
        mark = info.watermark
        # Centred on the text area, positioned from the page edges: Writer
        # measures "page-content" of an object anchored in a header from the
        # header, so the exact page position is used.
        geometry = page_geometry(props)
        x = geometry["left"] + (geometry["text_width"] - mark.width) / 2
        text_height = geometry["height"] - geometry["top"] - geometry["bottom"]
        y = geometry["top"] + (text_height - mark.height) / 2
        watermark = FrameInfo("image", "paragraph", mark.width, mark.height, image=mark.image, x=x, y=y, props={
            "style:wrap": "run-through", "style:run-through": "background", "style:horizontal-pos": "from-left",
            "style:horizontal-rel": "page", "style:vertical-pos": "from-top", "style:vertical-rel": "page",
            "style:flow-with-text": "false"})
    for part in ("header", "footer"):
        found = info.parts.get(part, {})
        mark = watermark if part == "header" else None
        if not found and mark is None:
            continue
        main = found.get("right", found.get("all"))
        variants = [("", main if main is not None else [])]
        if "left" in found or "right" in found:
            variants.append(("-left", found.get("left", found.get("all", []))))
        if "first" in found:
            variants.append(("-first", found["first"]))
        only_mark = not found
        gap_key, min_key = f"{part}_gap", f"{part}_min_height"
        style = sub(layout, f"style:{part}-style")
        margin = "fo:margin-bottom" if part == "header" else "fo:margin-top"
        sub(style, "style:header-footer-properties", {
            "fo:min-height": units.mm(props[min_key]) if isinstance(props.get(min_key), Length) else "0mm",
            margin: "0mm" if only_mark else (units.mm(props[gap_key]) if isinstance(props.get(gap_key), Length)
                                              else "2.5mm")})
        for suffix, blocks in variants:
            element = sub(master, f"style:{part}{suffix}")
            write_part(element, blocks, mark, automatic)


def _graphic_defaults(styles: ET.Element) -> None:
    """The graphic styles "Graphics" and "Frame" Writer uses for images and text frames (8.1)."""
    common = {"svg:x": "0mm", "svg:y": "0mm", "style:number-wrapped-paragraphs": "no-limit",
              "style:wrap-contour": "false", "style:vertical-pos": "top", "style:horizontal-pos": "center"}
    for name, rel, wrap in (("Graphics", "paragraph", "none"), ("Frame", "paragraph-content", "parallel")):
        style = sub(styles, "style:style", {"style:name": name, "style:family": "graphic"})
        sub(style, "style:graphic-properties", {"text:anchor-type": "paragraph", **common, "style:wrap": wrap,
                                                "style:vertical-rel": rel, "style:horizontal-rel": rel})


def _frame_attrs(props: dict[str, Any]) -> dict[str, str]:
    """``style:graphic-properties`` of a frame style: border, padding, background."""
    from primula.styles.schema import Border

    attrs: dict[str, str] = {}
    if isinstance(props.get("border"), Border):
        attrs["fo:border"] = units.border(props["border"])
    padding = props.get("padding")
    if isinstance(padding, Length):
        attrs["fo:padding"] = units.mm(padding)
    elif isinstance(padding, tuple):
        for side, value in zip(("top", "right", "bottom", "left"), padding):
            attrs[f"fo:padding-{side}"] = units.mm(value)
    if props.get("background"):
        attrs["fo:background-color"] = units.color(props["background"])
    return attrs


def _structure_style(system: StyleSystem, key: str, fallback: str) -> str | None:
    """A ``structure_styles`` style name if the style exists (decision 70)."""
    name = (system.settings.get("structure_styles") or {}).get(key, fallback)
    return name if isinstance(name, str) and system.kind(name) is not None else None


def _notes_configuration(styles: ET.Element, system: StyleSystem, footnotes: dict[str, Any]) -> None:
    """``text:notes-configuration`` of footnotes and endnotes (5.10, decision 76).

    The numbering restart (``none``/``page``/``chapter``) maps to
    ``text:start-numbering-at`` (``document``/``page``/``chapter``);
    Writer renumbers notes itself.  The ``*`` format writes custom
    citations (``text:label``), so the number format stays ``1``.
    """
    restart = {"none": "document", "page": "page", "chapter": "chapter"}.get(footnotes.get("restart"), "document")
    fmt = footnotes.get("format", "1")
    anchor = _structure_style(system, "note_anchor", "NoteAnchor")
    for note_class, key, fallback in (("footnote", "footnote", "Footnote"), ("endnote", "endnote", "Endnote")):
        sub(styles, "text:notes-configuration", {
            "text:note-class": note_class, "text:citation-style-name": None,
            "text:citation-body-style-name": anchor,
            "text:default-style-name": _structure_style(system, key, fallback),
            "style:num-format": fmt if fmt in ("1", "i", "I", "a", "A") else "1", "text:start-value": 0,
            "text:footnotes-position": "page" if note_class == "footnote" else "document",
            "text:start-numbering-at": restart if note_class == "footnote" else "document",
        })


def _footnote_separator(layout_props: ET.Element, separator: Any) -> None:
    """``style:footnote-sep``: the line above footnotes (``"0.5pt solid"``, ``"none"``)."""
    from primula.styles.schema import PropertyError, parse_border

    try:
        border = parse_border(separator if separator is not None else "0.5pt solid")
    except (PropertyError, ValueError):
        border = parse_border("0.5pt solid")
    sub(layout_props, "style:footnote-sep", {
        "style:width": units.pt(border.width) if border.width is not None else "0pt",
        "style:rel-width": "25%" if border.width is not None else "0%",
        "style:color": border.color, "style:line-style": border.type if border.width is not None else "none",
        "style:adjustment": "left", "style:distance-before-sep": "1mm", "style:distance-after-sep": "1mm",
    })


#: Letters of lettered lists of the profile ``report`` (П1; ДСТУ 3008:2015 — to be
#: checked against the text of the standard): the Ukrainian alphabet without
#: ґ, є, з, і, ї, й, о, ч, ь.
REPORT_LETTERS = {"uk": "абвгдежиклмнпрстуфхцшщюя"}


def level_letters(props: dict[str, Any], profile: str | None, language: str | None) -> str | None:
    """The letters of a list level numbered as text (П1), or ``None`` for Writer numbering.

    Writer cannot skip letters, so a level with ``letters="…"`` (or a
    Cyrillic ``а``/``А`` level of the profile ``report`` in a language of
    :data:`REPORT_LETTERS`) gets no automatic number: the writer puts the
    label in the text.  The case follows ``format`` (``А`` — capitals).
    """
    if props.get("type", "bullet") != "number":
        return None
    letters = props.get("letters")
    code = (language or "").split("-")[0].lower()
    if not letters and profile == "report" and props.get("format") in ("а", "А"):
        letters = REPORT_LETTERS.get(code)
    if not letters:
        return None
    return letters.upper() if props.get("format") in ("A", "А") else letters


def list_num_format(fmt: str, language: str | None) -> str:
    """``style:num-format`` of a list level (11.3, decision 115).

    The Cyrillic formats ``а``/``А`` number by the alphabet of the document
    language without skipping letters; LibreOffice writes them as
    ``"а, б, .., аа, аб, ... (uk)"`` (checked with LibreOffice 26.8; the ODF
    1.3 schema allows any string).  For other languages the evaluator
    reports P3121; the Latin letters are written then.
    """
    if fmt not in ("а", "А"):
        return fmt
    code = (language or "").split("-")[0].lower()
    if code not in ("uk", "ru"):
        return "a" if fmt == "а" else "A"
    return ("а, б, .., аа, аб, ... " if fmt == "а" else "А, Б, .., Аа, Аб, ... ") + f"({code})"


def _list_style(parent: ET.Element, name: str, levels: dict[int, dict[str, Any]], language: str | None = None,
                profile: str | None = None) -> None:
    """``text:list-style`` with the defined levels (label alignment mode).

    A level numbered by letters as text (:func:`level_letters`) has an empty
    ``style:num-format``: the label is in the paragraph, followed by a tab.
    """
    style = sub(parent, "text:list-style", {"style:name": name, "style:display-name": name})
    for level in sorted(levels):
        props = levels[level]
        if props.get("type", "bullet") == "bullet":
            item = sub(style, "text:list-level-style-bullet", {
                "text:level": level, "text:bullet-char": props.get("bullet", "•")})
        elif level_letters(props, profile, language):
            item = sub(style, "text:list-level-style-number", {"text:level": level, "style:num-format": ""})
        else:
            item = sub(style, "text:list-level-style-number", {
                "text:level": level, "style:num-format": list_num_format(props.get("format", "1"), language),
                "style:num-prefix": props.get("prefix") or None, "style:num-suffix": props.get("suffix", "."),
                "text:start-value": props.get("start")})
        left = props.get("left") or Length(Decimal(5 * level), "mm")
        hanging = props.get("hanging") or Length(Decimal(5), "mm")
        level_props = sub(item, "style:list-level-properties",
                          {"text:list-level-position-and-space-mode": "label-alignment"})
        sub(level_props, "style:list-level-label-alignment", {
            "text:label-followed-by": "listtab", "text:list-tab-stop-position": units.mm(left),
            "fo:text-indent": "-" + units.mm(hanging), "fo:margin-left": units.mm(left)})
