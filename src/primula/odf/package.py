"""Packaging of ODT files (ODF 1.3 part 2; decisions 66-67).

* ``mimetype`` is the first entry, stored uncompressed;
* every other part is deflated and listed in ``META-INF/manifest.xml``;
* entry times are the build date at midnight (ZIP has no time zone; dates
  before 1980 are not representable and are raised to 1980-01-01), so the
  same parts give a byte-identical file;
* additional parts (``Primula/report.json``, ``Primula/sources/…``) are
  listed with their media types.
"""

from __future__ import annotations

import datetime
import io
import zipfile
from pathlib import Path

from primula.odf.xml import ODF_VERSION, el, serialize, sub

MIMETYPE = "application/vnd.oasis.opendocument.text"


def _media_type(name: str) -> str:
    if name.startswith("Pictures/"):
        return {"png": "image/png", "jpg": "image/jpeg", "svg": "image/svg+xml"}.get(name.rsplit(".", 1)[-1],
                                                                                "application/octet-stream")
    if name.endswith(".xml"):
        return "text/xml"
    if name.endswith(".json"):
        return "application/json"
    return "text/plain"


def build_package(parts: dict[str, bytes], build_date: datetime.date) -> bytes:
    """ZIP bytes of an ODT from its parts (names -> bytes, in writing order)."""
    manifest = el("manifest:manifest", {"manifest:version": ODF_VERSION})
    sub(manifest, "manifest:file-entry", {"manifest:full-path": "/", "manifest:version": ODF_VERSION,
                                          "manifest:media-type": MIMETYPE})
    for name in parts:
        sub(manifest, "manifest:file-entry", {"manifest:full-path": name, "manifest:media-type": _media_type(name)})
    stamp = max((build_date.year, build_date.month, build_date.day, 0, 0, 0), (1980, 1, 1, 0, 0, 0))
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        def write(name: str, data: bytes, compress: int) -> None:
            info = zipfile.ZipInfo(name, date_time=stamp)
            info.compress_type = compress
            info.external_attr = 0o644 << 16
            archive.writestr(info, data)

        write("mimetype", MIMETYPE.encode("ascii"), zipfile.ZIP_STORED)
        for name, data in parts.items():
            write(name, data, zipfile.ZIP_DEFLATED)
        write("META-INF/manifest.xml", serialize(manifest), zipfile.ZIP_DEFLATED)
    return buffer.getvalue()


def write_file(path: Path, data: bytes) -> None:
    """Write the ODT atomically (a temporary file, then rename)."""
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_bytes(data)
    temporary.replace(path)
