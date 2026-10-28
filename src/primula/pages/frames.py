"""Placement parameters of images, figures and text boxes (specification 8.5).

:func:`frame_info` turns the arguments of ``|img``, ``|figure`` and
``|frame`` into a :class:`FrameInfo` the ODT writer maps to ``draw:frame``
attributes and a graphic style:

==============  ==============================================================
``place``       ``inline`` -> anchored as a character; ``left``/``center``/
                ``right``/``inside``/``outside`` -> ``style:horizontal-pos``
``valign``      ``style:vertical-pos`` (``top``, ``middle``, ``bottom``)
``x``, ``y``    ``from-left``/``from-top`` with ``svg:x``/``svg:y``
``rel``         ``para`` -> ``paragraph``, ``area`` -> ``page-content``,
                ``page`` -> ``page``; anchored to the paragraph (8.1)
``anchor``      explicit ODF anchoring ``char``, ``para``, ``page``
``wrap``        mode without a side; the side follows ``place`` (table 8.5)
``layer``       ``front``/``back`` for ``wrap="through"``
``gap``         ``fo:margin-*``; ``border``, ``padding`` of the frame
``width``,      ``"60mm"`` or ``"50%"`` of the text area; one side keeps the
``height``      proportions of the image
``mirror``,     ``style:mirror``, ``fo:clip``, ``draw:image-opacity``
``crop``,
``opacity``
``alt``         ``svg:title`` of the frame
==============  ==============================================================

Images larger than the text area are scaled down proportionally (decision
85).  ``rotate`` is reported as not supported yet (P6107): Writer keeps
rotation of image frames in its own extension attributes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from fractions import Fraction
from typing import Any

from primula.core.values import Length, parse_length
from primula.diagnostics import DiagnosticSink, error, warning
from primula.odf import units
from primula.pages.images import ImageInfo
from primula.styles.schema import Border, PropertyError, check_property

PLACES = ("inline", "left", "center", "right", "inside", "outside")
WRAPS = ("none", "side", "both", "auto", "through", "contour")
_REL = {"para": "paragraph", "area": "page-content", "page": "page"}
_ANCHORS = {"char": "char", "para": "paragraph", "page": "page"}
#: Arguments of the frame commands besides the placement ones.
_OTHER = {"img": ("key",), "figure": ("key", "id", "block", "caption"), "frame": ("id", "block")}
PLACEMENT = ("place", "valign", "x", "y", "rel", "anchor", "wrap", "layer", "gap", "width", "height", "rotate",
             "mirror", "crop", "opacity", "border", "padding", "style", "alt")


@dataclass
class FrameInfo:
    """A frame of an image, a figure or a text box.

    Attributes:
        kind: ``image``, ``figure`` or ``text``.
        anchor: ``as-char``, ``char``, ``paragraph`` or ``page``.
        width, height: size in millimetres (``None`` — automatic height of a text box).
        rel_width: ``"50%"`` for widths given as a share of the text area.
        props: attributes of ``style:graphic-properties``.
        x, y: offsets for ``from-left``/``from-top``.
        image: the image file (images and figures).
        alt: alternative text.
        style: a named frame style (parent of the automatic style).
    """

    kind: str
    anchor: str
    width: Fraction | None
    height: Fraction | None
    rel_width: str | None = None
    props: dict[str, str] = field(default_factory=dict)
    x: Fraction | None = None
    y: Fraction | None = None
    image: ImageInfo | None = None
    alt: str | None = None
    style: str | None = None


def _size(value: Any, area: Fraction) -> tuple[Fraction | None, str | None]:
    """A width or height: a length or a percentage of the text area."""
    if value is None:
        return None, None
    if isinstance(value, Length):
        return units.to_mm(value), None
    if isinstance(value, str) and value.endswith("%"):
        share = Fraction(Decimal(value[:-1]))
        return area * share / 100, value
    length = parse_length(value) if isinstance(value, str) else None
    if length is None:
        raise ValueError(str(value))
    return units.to_mm(length), None


def _offset(value: Any) -> Fraction:
    length = value if isinstance(value, Length) else parse_length(value) if isinstance(value, str) else None
    if length is None:
        raise ValueError(str(value))
    return units.to_mm(length)


def frame_info(command: str, args: dict[str, Any], image: ImageInfo | None, area: tuple[Fraction, Fraction],
               sink: DiagnosticSink, span: Any) -> FrameInfo:
    """Build the frame of ``|img``/``|figure``/``|frame`` from its keyword arguments.

    Args:
        command: ``img``, ``figure`` or ``frame``.
        args: keyword arguments (evaluated).
        image: the image (``img``, ``figure``) or ``None``.
        area: width and height of the text area in millimetres.
        sink: diagnostics receiver (P6102 invalid values, P6107 rotate).
        span: position for diagnostics.
    """
    def invalid(name: str) -> None:
        sink.emit(error("P6102", span, name=name, value=str(args.get(name)), command="|" + command))

    for name in args:
        if name not in PLACEMENT and name not in _OTHER.get(command, ()):
            sink.emit(error("P4104", span, name=name, command="|" + command))
    place = args.get("place", "inline" if command == "img" else "center")
    if place not in PLACES:
        invalid("place")
        place = "center"
    floating = command != "img" or place != "inline" or "x" in args or "y" in args
    if command == "figure" and place == "inline":
        place = "center"
    anchor = "paragraph" if floating else "as-char"
    if "anchor" in args:
        if args["anchor"] in _ANCHORS:
            anchor = _ANCHORS[args["anchor"]]
        else:
            invalid("anchor")

    # Size: explicit, proportional to the image, natural; scaled into the text area.
    width = height = None
    rel_width = None
    try:
        width, rel_width = _size(args.get("width"), area[0])
    except (ValueError, ArithmeticError):
        invalid("width")
    try:
        height, _rel = _size(args.get("height"), area[1])
    except (ValueError, ArithmeticError):
        invalid("height")
    if image is not None:
        ratio = image.height_mm / image.width_mm if image.width_mm else Fraction(1)
        if width is None and height is None:
            width, height = image.width_mm, image.height_mm
        elif width is None:
            width = height / ratio if ratio else height
        elif height is None:
            height = width * ratio
        if width > area[0] or height > area[1]:  # decision 85
            scale = min(area[0] / width, area[1] / height)
            width, height = width * scale, height * scale
    elif width is None and command == "frame":
        width = area[0]

    info = FrameInfo("figure" if command == "figure" else ("image" if image is not None else "text"), anchor,
                     width, height, rel_width, image=image)
    props = info.props
    rel = args.get("rel", "para")
    if rel not in _REL:
        invalid("rel")
        rel = "para"
    if floating:
        if "x" in args:
            try:
                info.x = _offset(args["x"])
                props["style:horizontal-pos"] = "from-left"
            except ValueError:
                invalid("x")
        else:
            props["style:horizontal-pos"] = {"inline": "center"}.get(place, place)
        props["style:horizontal-rel"] = _REL[rel]
        if "y" in args:
            try:
                info.y = _offset(args["y"])
                props["style:vertical-pos"] = "from-top"
            except ValueError:
                invalid("y")
        else:
            valign = args.get("valign", "top")
            if valign not in ("top", "middle", "bottom"):
                invalid("valign")
                valign = "top"
            props["style:vertical-pos"] = valign
        props["style:vertical-rel"] = _REL[rel]
        if rel == "page":
            # A position on the sheet (8.1): Writer must not keep the frame
            # inside the text area of its anchor paragraph.
            props["style:flow-with-text"] = "false"
    else:
        props["style:vertical-pos"] = "top"
        props["style:vertical-rel"] = "baseline"

    wrap = args.get("wrap", "none")
    if wrap not in WRAPS:
        invalid("wrap")
        wrap = "none"
    if floating:
        side = {"right": "left", "left": "right"}.get(place, "parallel")
        props["style:wrap"] = {"none": "none", "side": side, "both": "parallel", "auto": "dynamic",
                               "through": "run-through", "contour": "dynamic"}[wrap]
        if wrap == "through":
            layer = args.get("layer", "front")
            if layer not in ("front", "back"):
                invalid("layer")
                layer = "front"
            props["style:run-through"] = "foreground" if layer == "front" else "background"
        if wrap == "contour":
            props["style:wrap-contour"] = "true"

    for name in ("gap", "padding", "border"):
        if name in args:
            try:
                value = check_property("frame", name, args[name])
            except PropertyError:
                invalid(name)
                continue
            if name == "border":
                props["fo:border"] = units.border(value) if isinstance(value, Border) else "none"
            else:
                prefix = "fo:margin" if name == "gap" else "fo:padding"
                sides = value if isinstance(value, tuple) else (value,) * 4
                for side, length in zip(("top", "right", "bottom", "left"), sides):
                    props[f"{prefix}-{side}"] = units.mm(length)
    if "mirror" in args:
        mirror = {True: "horizontal", "horizontal": "horizontal", "vertical": "vertical",
                  "both": "horizontal vertical"}.get(args["mirror"])
        if mirror is None:
            invalid("mirror")
        else:
            props["style:mirror"] = mirror
    if "crop" in args:
        crop = args["crop"]
        try:
            sides = crop if isinstance(crop, (list, tuple)) else [crop] * 4
            if len(sides) != 4:
                raise ValueError
            props["fo:clip"] = "rect(" + ", ".join(units.mm(units.from_mm(_offset(s))) for s in sides) + ")"
        except ValueError:
            invalid("crop")
    if "opacity" in args:
        opacity = args["opacity"]
        if isinstance(opacity, int) and not isinstance(opacity, bool) and 0 <= opacity <= 100:
            props["draw:image-opacity"] = f"{opacity}%"
        else:
            invalid("opacity")
    if "rotate" in args:
        sink.emit(warning("P6107", span))
    if isinstance(args.get("alt"), str):
        info.alt = args["alt"]
    if isinstance(args.get("style"), str):
        info.style = args["style"]
    return info
