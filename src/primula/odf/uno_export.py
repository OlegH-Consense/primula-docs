"""PDF export with updated indexes and fields through the LibreOffice UNO bridge.

Page numbers of a table of contents, of lists and of ``page`` references
(``text:bookmark-ref``, ``text:note-ref``) are known only after Writer
lays the document out; ``soffice --convert-to pdf`` does not update them.
This script starts LibreOffice headless with a private profile, loads the
ODT hidden, updates every document index and refreshes the text fields
(twice: an updated table of contents may move pages), and stores the PDF.

It runs as a separate process with the Python interpreter that has the
``uno`` module (``python3-uno`` in Debian, ``libreoffice-pyuno`` in
openSUSE); :mod:`primula.odf.pdf` decides whether it is available.

Usage::

    python3 uno_export.py SOFFICE INPUT.odt OUTPUT.pdf PROFILE_DIR

References: LibreOffice API — ``com.sun.star.text.XDocumentIndexesSupplier``,
``com.sun.star.util.XRefreshable``,
https://api.libreoffice.org/docs/idl/ref/namespacecom_1_1sun_1_1star_1_1text.html
"""

from __future__ import annotations

import subprocess
import sys
import time
import uuid
from pathlib import Path


def _connect(pipe: str, deadline: float):  # pragma: no cover - needs LibreOffice
    """Connect to the started office through the named pipe (retries until ``deadline``)."""
    import uno
    from com.sun.star.connection import NoConnectException

    local = uno.getComponentContext()
    resolver = local.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", local)
    while True:
        try:
            return resolver.resolve(f"uno:pipe,name={pipe};urp;StarOffice.ComponentContext")
        except NoConnectException:
            if time.monotonic() > deadline:
                raise
            time.sleep(0.2)


def _property(name: str, value: object):  # pragma: no cover - needs LibreOffice
    from com.sun.star.beans import PropertyValue

    item = PropertyValue()
    item.Name, item.Value = name, value
    return item


def export(soffice: str, source: Path, target: Path, profile: Path, timeout: float = 120) -> None:  # pragma: no cover
    """Convert ``source`` to ``target`` (PDF) with updated indexes and fields.

    Args:
        soffice: LibreOffice executable.
        source: the ODT file.
        target: the PDF file to write.
        profile: directory of a private LibreOffice user profile.
        timeout: seconds to wait for LibreOffice.
    """
    import uno

    pipe = f"primula-{uuid.uuid4().hex}"
    office = subprocess.Popen(
        [soffice, f"-env:UserInstallation={profile.as_uri()}", "--headless", "--invisible", "--norestore",
         "--nologo", "--nodefault", f"--accept=pipe,name={pipe};urp;"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    desktop = None
    try:
        context = _connect(pipe, time.monotonic() + timeout)
        desktop = context.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", context)
        document = desktop.loadComponentFromURL(uno.systemPathToFileUrl(str(source.resolve())), "_blank", 0,
                                                (_property("Hidden", True),))
        try:
            for _ in range(2):
                indexes = document.getDocumentIndexes()
                for number in range(indexes.getCount()):
                    indexes.getByIndex(number).update()
                document.getTextFields().refresh()
            document.storeToURL(uno.systemPathToFileUrl(str(target.resolve())),
                                (_property("FilterName", "writer_pdf_Export"),))
        finally:
            document.close(True)
    finally:
        if desktop is not None:
            try:
                desktop.terminate()
            except Exception:  # noqa: BLE001 - the connection drops while the office exits
                pass
        try:
            office.wait(timeout=30)
        except subprocess.TimeoutExpired:
            office.kill()


if __name__ == "__main__":  # pragma: no cover
    export(sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4]))
