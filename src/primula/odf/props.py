"""Style properties -> ODF attributes (specification 11.3, 15; decision 57).

Paragraph and character properties of the language are written to
``style:paragraph-properties`` and ``style:text-properties``; table cell
properties to ``style:table-cell-properties``.  Direct ODF properties
(``odf={…}``, 11.8) go to the properties element whose group lists the
attribute (``odf_properties.json``, generated from the ODF 1.3 schema).

Fonts are collected in a :class:`Fonts` registry: every font name used
gets a ``style:font-face`` declaration.
"""

from __future__ import annotations

from typing import Any

from primula.odf import units
from primula.styles.schema import Border, odf_properties


class Fonts:
    """Font names used by the document (``office:font-face-decls``)."""

    def __init__(self) -> None:
        self.names: list[str] = []

    def use(self, name: str) -> str:
        if name not in self.names:
            self.names.append(name)
        return name


_ALIGN = {"left": "start", "right": "end", "center": "center", "justify": "justify"}


def paragraph_attrs(props: dict[str, Any]) -> dict[str, str]:
    """Attributes of ``style:paragraph-properties``."""
    attrs: dict[str, str] = {}
    if "align" in props:
        attrs["fo:text-align"] = _ALIGN[props["align"]]
    if "line_height" in props:
        name, value = units.line_height(props["line_height"])
        attrs[name] = value
    for key, attr in (("space_before", "fo:margin-top"), ("space_after", "fo:margin-bottom"),
                      ("left", "fo:margin-left"), ("right", "fo:margin-right"), ("first_line", "fo:text-indent")):
        if key in props:
            attrs[attr] = units.mm(props[key])
    if props.get("keep_with_next") is not None:
        attrs["fo:keep-with-next"] = "always" if props["keep_with_next"] else "auto"
    if props.get("keep_together") is not None:
        attrs["fo:keep-together"] = "always" if props["keep_together"] else "auto"
    if props.get("page_break_before"):
        attrs["fo:break-before"] = "page"
    for key in ("widows", "orphans"):
        if key in props:
            attrs[f"fo:{key}"] = str(props[key])
    if "background" in props:
        attrs["fo:background-color"] = units.color(props["background"])
    attrs.update(_odf(props, "paragraph"))
    return attrs


def text_attrs(props: dict[str, Any], fonts: Fonts, *, paragraph: bool = False) -> dict[str, str]:
    """Attributes of ``style:text-properties`` (character properties)."""
    attrs: dict[str, str] = {}
    if "font" in props:
        attrs["style:font-name"] = fonts.use(props["font"])
    if "size" in props:
        attrs["fo:font-size"] = units.pt(props["size"])
    if props.get("bold") is not None:
        weight = "bold" if props["bold"] else "normal"
        attrs.update({"fo:font-weight": weight, "style:font-weight-asian": weight,
                      "style:font-weight-complex": weight})
    if props.get("italic") is not None:
        style = "italic" if props["italic"] else "normal"
        attrs.update({"fo:font-style": style, "style:font-style-asian": style, "style:font-style-complex": style})
    if "color" in props:
        attrs["fo:color"] = props["color"] if props["color"] != "none" else "#000000"
    if "background" in props and not paragraph:
        attrs["fo:background-color"] = units.color(props["background"])
    if "underline" in props:
        value = props["underline"]
        attrs["style:text-underline-style"] = "solid" if value else "none"
        if value:
            attrs["style:text-underline-width"] = "auto"
            attrs["style:text-underline-color"] = "font-color"
            if value == "double":
                attrs["style:text-underline-type"] = "double"
    if "strike" in props:
        attrs["style:text-line-through-style"] = "solid" if props["strike"] else "none"
    if "language" in props:
        language, country = units.language(props["language"])
        attrs["fo:language"] = language or "none"
        attrs["fo:country"] = country or "none"
    if "position" in props:
        attrs["style:text-position"] = {"super": "super 58%", "sub": "sub 58%", "normal": "0% 100%"}[props["position"]]
    attrs.update(_odf(props, "text"))
    return attrs


def cell_attrs(props: dict[str, Any]) -> dict[str, str]:
    """Attributes of ``style:table-cell-properties`` (13.5: background, padding, borders, valign)."""
    attrs: dict[str, str] = {}
    if "background" in props:
        attrs["fo:background-color"] = units.color(props["background"])
    padding = props.get("padding")
    if padding is not None:
        if isinstance(padding, tuple):
            for side, value in zip(("top", "right", "bottom", "left"), padding):
                attrs[f"fo:padding-{side}"] = units.mm(value)
        else:
            attrs["fo:padding"] = units.mm(padding)
    for side in ("top", "bottom", "left", "right"):
        value = props.get(f"border_{side}")
        if isinstance(value, Border):
            attrs[f"fo:border-{side}"] = units.border(value)
    if "valign" in props:
        attrs["style:vertical-align"] = props["valign"]
    attrs.update(_odf(props, "table-cell"))
    return attrs


def _odf(props: dict[str, Any], group: str) -> dict[str, str]:
    """Direct ODF properties of one properties element (11.8)."""
    direct = props.get("odf")
    if not direct:
        return {}
    names = odf_properties()[group]
    return {key: value for key, value in direct.items() if key in names}
