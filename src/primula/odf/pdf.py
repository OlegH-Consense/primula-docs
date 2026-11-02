"""PDF export through LibreOffice (specification 14.1: ``--pdf [file]``).

LibreOffice runs headless with a temporary user profile
(``-env:UserInstallation``), so it neither depends on nor disturbs a
running LibreOffice of the user, and parallel builds do not lock each
other.  The result is moved to the requested path.

Page numbers of tables of contents, lists and ``page`` references are
computed by Writer.  When the document has them (``update=True``), the
export goes through the UNO bridge (:mod:`primula.odf.uno_export`), which
updates indexes and fields first; without the bridge, or if it fails, the
plain conversion is used and the caller warns that the numbers are not
updated (P8008).
"""

from __future__ import annotations

import contextlib
import functools
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    import fcntl
except ImportError:  # pragma: no cover - not on Windows
    fcntl = None  # type: ignore[assignment]

_UNO_SCRIPT = Path(__file__).with_name("uno_export.py")


class PdfError(Exception):
    """PDF export failed; ``reason`` is ``missing`` or the error text."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


@contextlib.contextmanager
def profile_for(work: Path):
    """The LibreOffice user profile of one conversion.

    A new profile costs more than a second of LibreOffice start.  With
    ``PRIMULA_LO_PROFILE`` set (``primula view`` sets it) that directory is
    reused between runs; a lock file keeps two runs from sharing it, and a run
    that finds it busy uses a private profile in ``work``.

    Args:
        work: a temporary directory of the caller.

    Yields:
        The profile directory.
    """
    shared = os.environ.get("PRIMULA_LO_PROFILE")
    lock = None
    if shared and fcntl is not None:
        directory = Path(shared)
        try:
            directory.parent.mkdir(parents=True, exist_ok=True)
            lock = open(directory.parent / (directory.name + ".lock"), "w")  # noqa: SIM115 - closed below
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            if lock is not None:
                lock.close()
            lock = None
    try:
        yield Path(shared) if lock is not None and shared else work / "profile"
    finally:
        if lock is not None:
            lock.close()    # releases the lock


@functools.cache
def uno_python() -> str | None:
    """A Python interpreter with the LibreOffice ``uno`` module, or ``None``."""
    candidates = [sys.executable, shutil.which("python3"), "/usr/bin/python3"]
    for python in dict.fromkeys(c for c in candidates if c):
        try:
            run = subprocess.run([python, "-I", "-c", "import uno"], capture_output=True, timeout=30, check=False)
        except (OSError, subprocess.TimeoutExpired):
            continue
        if run.returncode == 0:
            return python
    return None


def export_pdf(odt: Path, target: Path, timeout: int = 180, *, update: bool = False) -> str | None:
    """Convert an ODT to PDF with LibreOffice.

    Args:
        odt: the ODT file.
        target: the PDF to write.
        timeout: seconds for LibreOffice.
        update: update indexes and fields before the export (UNO bridge).

    Returns:
        ``None`` when nothing needed updating or the update succeeded;
        otherwise the reason why page numbers were not updated.

    Raises:
        PdfError: ``soffice``/``libreoffice`` not found, or conversion failed.
    """
    executable = shutil.which("soffice") or shutil.which("libreoffice")
    if executable is None:
        raise PdfError("missing")
    reason: str | None = None
    if update:
        python = uno_python()
        if python is None:
            reason = "the Python UNO bridge (python3-uno) is not available"
        else:
            with tempfile.TemporaryDirectory(prefix="primula-pdf-") as work, profile_for(Path(work)) as profile:
                produced = Path(work) / "out.pdf"
                try:
                    run = subprocess.run([python, "-I", str(_UNO_SCRIPT), executable, str(odt), str(produced),
                                          str(profile)],
                                         capture_output=True, text=True, timeout=timeout, check=False)
                    if run.returncode == 0 and produced.exists():
                        target.parent.mkdir(parents=True, exist_ok=True)
                        shutil.move(str(produced), target)
                        return None
                    lines = (run.stderr or run.stdout).strip().splitlines()
                    reason = lines[-1] if lines else f"exit code {run.returncode}"
                except subprocess.TimeoutExpired:
                    reason = f"timeout after {timeout} s"
    _convert(executable, odt, target, timeout)
    return reason


def _convert(executable: str, odt: Path, target: Path, timeout: int) -> None:
    """Plain ``soffice --convert-to pdf``."""
    with tempfile.TemporaryDirectory(prefix="primula-pdf-") as work, profile_for(Path(work)) as profile:
        out_dir = Path(work) / "out"
        try:
            run = subprocess.run(
                [executable, f"-env:UserInstallation={profile.as_uri()}", "--headless", "--norestore",
                 "--convert-to", "pdf", "--outdir", str(out_dir), str(odt)],
                capture_output=True, text=True, timeout=timeout, check=False)
        except subprocess.TimeoutExpired:
            raise PdfError(f"timeout after {timeout} s") from None
        produced = out_dir / (odt.stem + ".pdf")
        if run.returncode != 0 or not produced.exists():
            raise PdfError((run.stderr or run.stdout).strip() or f"exit code {run.returncode}")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(produced), target)
