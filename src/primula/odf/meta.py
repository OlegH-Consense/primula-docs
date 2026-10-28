"""``meta.xml``: document metadata (specification 2.3, 15; decision 66).

Mapping of the ``document`` header keys:

* ``title``, ``subject``, ``description`` -> ``dc:title``, ``dc:subject``, ``dc:description``;
* ``creator`` -> ``meta:initial-creator`` and ``dc:creator``;
* ``language`` -> ``dc:language`` (the document language, decision 65);
* ``keywords`` (string or list) -> ``meta:keyword``, one per word;
* ``created`` -> ``meta:creation-date``; ``modified`` -> ``dc:date``; both
  default to the build date;
* ``organization``, ``identifier``, ``revision``, ``status`` ->
  ``meta:user-defined`` (Writer: Properties -> Custom Properties).

``meta:generator`` is ``Primula Documenting System/<version>``.  No other
dates or random identifiers are written (byte-identical rebuilds).
"""

from __future__ import annotations

import datetime
import xml.etree.ElementTree as ET
from typing import Any

from primula import __version__
from primula.core.values import DateTime, to_str
from primula.odf.xml import ODF_VERSION, el, sub

_USER_DEFINED = ("organization", "identifier", "revision", "status")


def _datetime(value: Any) -> str:
    """``meta:creation-date``/``dc:date``: a date without time -> ``T00:00:00`` (15)."""
    if isinstance(value, DateTime):
        moment = value.to_python()
        return moment.isoformat(timespec="seconds")
    if isinstance(value, datetime.date):
        return value.isoformat() + "T00:00:00"
    return str(value)


def build_meta(metadata: dict[str, Any], language: str | None, build_date: datetime.date) -> ET.Element:
    """Build the ``office:document-meta`` element."""
    root = el("office:document-meta", {"office:version": ODF_VERSION})
    meta = sub(root, "office:meta")
    sub(meta, "meta:generator", text=f"Primula Documenting System/{__version__}")
    for key in ("title", "subject", "description"):
        if metadata.get(key) is not None:
            sub(meta, f"dc:{key}", text=to_str(metadata[key]))
    keywords = metadata.get("keywords")
    if isinstance(keywords, str):
        keywords = keywords.split()
    for word in keywords or []:
        sub(meta, "meta:keyword", text=to_str(word))
    if metadata.get("creator") is not None:
        sub(meta, "meta:initial-creator", text=to_str(metadata["creator"]))
        sub(meta, "dc:creator", text=to_str(metadata["creator"]))
    sub(meta, "meta:creation-date", text=_datetime(metadata.get("created") or build_date))
    sub(meta, "dc:date", text=_datetime(metadata.get("modified") or build_date))
    if language:
        sub(meta, "dc:language", text=language)
    for key in _USER_DEFINED:
        if metadata.get(key) is not None:
            sub(meta, "meta:user-defined", {"meta:name": key}, text=to_str(metadata[key]))
    return root
