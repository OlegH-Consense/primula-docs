"""XML of ODF 1.3 documents: namespaces, element building, serialisation.

ODF parts are built with :mod:`xml.etree.ElementTree`.  Element and
attribute names are written as ``"prefix:name"`` and expanded with
:func:`qn`; the prefixes are registered so that the output uses the usual
ODF prefixes.  Attributes keep their insertion order, and nothing in the
output depends on dictionaries without order or on time: the same tree
always serialises to the same bytes.

Reference: OASIS ODF 1.3, part 3 (schema), https://docs.oasis-open.org/office/OpenDocument/v1.3/
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any

#: Namespaces of ODF 1.3 used by the generator.
NAMESPACES: dict[str, str] = {
    "office": "urn:oasis:names:tc:opendocument:xmlns:office:1.0",
    "style": "urn:oasis:names:tc:opendocument:xmlns:style:1.0",
    "text": "urn:oasis:names:tc:opendocument:xmlns:text:1.0",
    "table": "urn:oasis:names:tc:opendocument:xmlns:table:1.0",
    "draw": "urn:oasis:names:tc:opendocument:xmlns:drawing:1.0",
    "fo": "urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0",
    "svg": "urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0",
    "xlink": "http://www.w3.org/1999/xlink",
    "dc": "http://purl.org/dc/elements/1.1/",
    "meta": "urn:oasis:names:tc:opendocument:xmlns:meta:1.0",
    "number": "urn:oasis:names:tc:opendocument:xmlns:datastyle:1.0",
    "manifest": "urn:oasis:names:tc:opendocument:xmlns:manifest:1.0",
}

for _prefix, _uri in NAMESPACES.items():
    ET.register_namespace(_prefix, _uri)

#: ODF version written to every part.
ODF_VERSION = "1.3"


def qn(name: str) -> str:
    """Clark name of ``"prefix:local"`` (``{uri}local``)."""
    prefix, local = name.split(":", 1)
    if prefix == "xml":  # xml:id; the prefix is predefined in ElementTree
        return f"{{http://www.w3.org/XML/1998/namespace}}{local}"
    return f"{{{NAMESPACES[prefix]}}}{local}"


def el(tag: str, attrs: dict[str, Any] | None = None, *children: ET.Element, text: str | None = None) -> ET.Element:
    """Create an element with prefixed attribute names; ``None`` values are skipped."""
    element = ET.Element(qn(tag))
    for name, value in (attrs or {}).items():
        if value is not None:
            element.set(qn(name), str(value))
    for child in children:
        element.append(child)
    if text is not None:
        element.text = text
    return element


def sub(parent: ET.Element, tag: str, attrs: dict[str, Any] | None = None, text: str | None = None) -> ET.Element:
    """Append a new child element and return it."""
    child = el(tag, attrs, text=text)
    parent.append(child)
    return child


def append_text(parent: ET.Element, text: str) -> None:
    """Append character data after the last child of ``parent`` (or as its text)."""
    if not text:
        return
    if len(parent):
        last = parent[-1]
        last.tail = (last.tail or "") + text
    else:
        parent.text = (parent.text or "") + text


def serialize(root: ET.Element) -> bytes:
    """Serialise a part with an XML declaration (UTF-8)."""
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)
