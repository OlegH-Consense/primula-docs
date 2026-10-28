"""Image files: format, pixel size, resolution, EXIF orientation (8.1, 8.2; decision 85).

Formats: PNG, JPEG, SVG (8.1); other formats are not converted (P6101).
The reader uses only the standard library:

* PNG — ``IHDR`` (size) and ``pHYs`` (pixels per metre);
* JPEG — the ``SOFn`` marker (size), JFIF density (``APP0``), EXIF
  ``XResolution``/``ResolutionUnit`` and ``Orientation`` (``APP1``);
* SVG — ``width``/``height`` of the root element (with units), otherwise
  ``viewBox`` at 96 DPI.

An SVG image may also be a string computed by code, ``svg=`` (decision 131):
:func:`svg_from_text` checks it (well-formed, root ``<svg>``, a size, no
DTD, no external references) and gives an image without a file.

Physical size (decision 85): by the DPI of the file, 96 without it.
References: PNG (ISO/IEC 15948) https://www.w3.org/TR/png/; JFIF 1.02;
EXIF 2.32 (CIPA DC-008); SVG 1.1 https://www.w3.org/TR/SVG11/struct.html
"""

from __future__ import annotations

import hashlib
import math
import re
import struct
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path

#: Default resolution without DPI in the file (decision 85).
DEFAULT_DPI = Fraction(96)
MEDIA_TYPES = {"png": "image/png", "jpeg": "image/jpeg", "svg": "image/svg+xml"}
_SVG_UNITS = {"px": Fraction(254, 960), "mm": Fraction(1), "cm": Fraction(10), "in": Fraction(254, 10),
              "pt": Fraction(254, 720), "pc": Fraction(254, 60), "": Fraction(254, 960)}


class ImageError(Exception):
    """An unsupported or unreadable image; ``reason`` names the problem."""


class SvgTextError(Exception):
    """An SVG string of ``svg=`` that cannot be used (decision 131).

    Attributes:
        code: ``P6110`` (not an SVG image: ``reason`` is ``xml``, ``root`` or
            ``size``), ``P6111`` (a DOCTYPE or ENTITY declaration), ``P6112``
            (an external reference, ``reason`` is the reference).
        reason: see ``code``.
    """

    def __init__(self, code: str, reason: str) -> None:
        super().__init__(code, reason)
        self.code = code
        self.reason = reason


@dataclass(frozen=True)
class ImageInfo:
    """An image file.

    Attributes:
        path: the file.
        format: ``png``, ``jpeg`` or ``svg``.
        data: file bytes.
        width_mm, height_mm: natural physical size.
        orientation: EXIF orientation (1 = normal).
    """

    path: Path
    format: str
    data: bytes
    width_mm: Fraction
    height_mm: Fraction
    orientation: int = 1

    @property
    def media_type(self) -> str:
        return MEDIA_TYPES[self.format]

    @property
    def package_name(self) -> str:
        """Deterministic name in the ODT: ``Pictures/<sha256>.<ext>``."""
        extension = {"jpeg": "jpg"}.get(self.format, self.format)
        return f"Pictures/{hashlib.sha256(self.data).hexdigest()}.{extension}"


def _mm(pixels: int, dpi: Fraction) -> Fraction:
    return Fraction(pixels) * Fraction(254, 10) / dpi


def _png(data: bytes) -> tuple[int, int, Fraction]:
    width, height = struct.unpack(">II", data[16:24])
    dpi = DEFAULT_DPI
    pos = 8
    while pos + 8 <= len(data):
        length, kind = struct.unpack(">I4s", data[pos:pos + 8])
        if kind == b"pHYs" and length >= 9:
            per_x, _per_y, unit = struct.unpack(">IIB", data[pos + 8:pos + 17])
            if unit == 1 and per_x:
                dpi = Fraction(per_x) * Fraction(254, 10000)
            break
        if kind == b"IDAT":
            break
        pos += 12 + length
    return width, height, dpi


def _exif(segment: bytes) -> tuple[int, Fraction | None]:
    """Orientation and X resolution in DPI from an EXIF ``APP1`` payload."""
    if not segment.startswith(b"Exif\0\0"):
        return 1, None
    tiff = segment[6:]
    endian = "<" if tiff[:2] == b"II" else ">"
    try:
        offset = struct.unpack(endian + "I", tiff[4:8])[0]
        count = struct.unpack(endian + "H", tiff[offset:offset + 2])[0]
    except struct.error:
        return 1, None
    orientation, resolution, unit = 1, None, 2
    for index in range(count):
        entry = tiff[offset + 2 + 12 * index: offset + 14 + 12 * index]
        if len(entry) < 12:
            break
        tag, kind, _n = struct.unpack(endian + "HHI", entry[:8])
        if tag == 0x0112 and kind == 3:
            orientation = struct.unpack(endian + "H", entry[8:10])[0]
        elif tag == 0x0128 and kind == 3:
            unit = struct.unpack(endian + "H", entry[8:10])[0]
        elif tag == 0x011A and kind == 5:
            pointer = struct.unpack(endian + "I", entry[8:12])[0]
            numerator, denominator = struct.unpack(endian + "II", tiff[pointer:pointer + 8])
            if denominator:
                resolution = Fraction(numerator, denominator)
    if resolution is not None and unit == 3:
        resolution = resolution * Fraction(254, 100)
    return orientation, resolution


def _jpeg(data: bytes) -> tuple[int, int, Fraction, int]:
    pos, width, height = 2, 0, 0
    dpi: Fraction | None = None
    orientation = 1
    while pos + 4 <= len(data):
        if data[pos] != 0xFF:
            raise ImageError("corrupt")
        marker = data[pos + 1]
        if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:
            pos += 2
            continue
        length = struct.unpack(">H", data[pos + 2:pos + 4])[0]
        segment = data[pos + 4:pos + 2 + length]
        if marker == 0xE0 and segment.startswith(b"JFIF\0") and len(segment) >= 12:
            units, density = segment[7], struct.unpack(">H", segment[8:10])[0]
            if density and units in (1, 2):
                dpi = Fraction(density) * (Fraction(254, 100) if units == 2 else 1)
        elif marker == 0xE1:
            orientation, exif_dpi = _exif(segment)
            dpi = dpi or exif_dpi
        elif marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
            height, width = struct.unpack(">HH", segment[1:5])
            break
        pos += 2 + length
    if not width or not height:
        raise ImageError("corrupt")
    return width, height, dpi or DEFAULT_DPI, orientation


def _svg_length(value: str | None) -> Fraction | None:
    if not value:
        return None
    match = re.fullmatch(r"\s*([0-9]*\.?[0-9]+)\s*(px|mm|cm|in|pt|pc)?\s*", value)
    if match is None:
        return None  # percentages and other forms: use the viewBox
    return Fraction(match.group(1)) * _SVG_UNITS[match.group(2) or ""]


def _view_box(value: str | None) -> list[float]:
    """The four numbers of ``viewBox``; an unreadable value counts as absent (13.15)."""
    try:
        box = [float(v) for v in re.split(r"[\s,]+", (value or "").strip()) if v]
    except ValueError:
        return []
    return box if len(box) == 4 and all(math.isfinite(v) for v in box) else []


def _svg(data: bytes) -> tuple[Fraction, Fraction]:
    try:
        root = ET.fromstring(data)
    except ET.ParseError:
        raise ImageError("corrupt") from None
    if not root.tag.endswith("svg"):
        raise ImageError("corrupt")
    width, height = _svg_length(root.get("width")), _svg_length(root.get("height"))
    box = _view_box(root.get("viewBox"))
    if (width is None or height is None) and len(box) == 4 and box[2] > 0 and box[3] > 0:
        ratio = Fraction(box[3]) / Fraction(box[2])
        if width is None and height is None:
            width, height = Fraction(box[2]) * _SVG_UNITS["px"], Fraction(box[3]) * _SVG_UNITS["px"]
        elif width is None:
            width = height / ratio
        else:
            height = width * ratio
    if width is None or height is None:
        raise ImageError("size")
    return width, height


def read_image(path: Path) -> ImageInfo:
    """Read an image file.

    Raises:
        ImageError: ``format`` (not PNG/JPEG/SVG), ``corrupt``, ``size`` (an SVG
            without size), ``read`` (cannot read the file).
    """
    try:
        data = path.read_bytes()
    except OSError:
        raise ImageError("read") from None
    try:
        if data.startswith(b"\x89PNG\r\n\x1a\n"):
            width, height, dpi = _png(data)
            return ImageInfo(path, "png", data, _mm(width, dpi), _mm(height, dpi))
        if data.startswith(b"\xff\xd8"):
            width, height, dpi, orientation = _jpeg(data)
            return ImageInfo(path, "jpeg", data, _mm(width, dpi), _mm(height, dpi), orientation)
    except (struct.error, IndexError):
        raise ImageError("corrupt") from None
    head = data[:512].lstrip()
    if head.startswith(b"<?xml") or head.startswith(b"<svg") or b"<svg" in data[:2048]:
        width_mm, height_mm = _svg(data)
        return ImageInfo(path, "svg", data, width_mm, height_mm)
    raise ImageError("format")


#: References inside an SVG string that stay inside it: fragments and data: URIs.
_LOCAL_REFERENCE = re.compile(r"\s*(#|data:)", re.IGNORECASE)
_CSS_URL = re.compile(r"url\(\s*['\"]?([^'\")]*)", re.IGNORECASE)


def _external_reference(root: ET.Element) -> str | None:
    """The first reference of the SVG that leaves it, or ``None``.

    Checked: ``href``/``xlink:href`` attributes and ``url(…)`` in attributes
    and ``<style>`` texts; a reference is local when it is a fragment
    (``#id``) or a ``data:`` URI.
    """
    for element in root.iter():
        for name, value in element.attrib.items():
            if name.rsplit("}", 1)[-1] == "href" and not _LOCAL_REFERENCE.match(value):
                return value
            for url in _CSS_URL.findall(value):
                if not _LOCAL_REFERENCE.match(url):
                    return url
        for url in _CSS_URL.findall(element.text or ""):
            if not _LOCAL_REFERENCE.match(url):
                return url
    return None


def svg_from_text(text: str) -> ImageInfo:
    """An SVG image from a string computed by code (``svg=``, decision 131).

    The string is written into the ODT as it is (UTF-8), under a name made of
    its hash, so equal images are stored once.  No file is written.  The
    checks keep the document self-contained and safe to open: Writer must not
    fetch anything when it shows the image.

    Args:
        text: the SVG document (the root element ``<svg>``, an XML
            declaration is allowed).

    Returns:
        the image; its ``path`` is ``svg=`` (for messages only).

    Raises:
        SvgTextError: P6110 not well-formed, the root is not ``<svg>``, no
            size; P6111 a DOCTYPE or ENTITY declaration; P6112 an external
            reference (``href``, ``url(…)``, ``<?xml-stylesheet?>``).
    """
    if re.search(r"<!DOCTYPE|<!ENTITY", text, re.IGNORECASE):
        raise SvgTextError("P6111", "")
    stylesheet = re.search(r"<\?xml-stylesheet[^>]*href\s*=\s*['\"]([^'\"]*)", text)
    if stylesheet:
        raise SvgTextError("P6112", stylesheet.group(1))
    data = text.encode("utf-8")
    try:
        root = ET.fromstring(data)
    except ET.ParseError:
        raise SvgTextError("P6110", "xml") from None
    if root.tag.rsplit("}", 1)[-1] != "svg":
        raise SvgTextError("P6110", "root")
    reference = _external_reference(root)
    if reference is not None:
        raise SvgTextError("P6112", reference)
    try:
        width, height = _svg(data)
    except ImageError:
        raise SvgTextError("P6110", "size") from None
    return ImageInfo(Path("svg="), "svg", data, width, height)
