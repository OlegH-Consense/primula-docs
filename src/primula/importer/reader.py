"""Reading a source document into the pandoc AST (``pandoc -f FORMAT -t json``).

Formats are chosen by the extension: DOCX, ODT, RTF, Markdown (GFM), HTML, EPUB read directly;
the old binary ``.doc`` is converted to DOCX by LibreOffice first (pandoc cannot read it).  Images
of the source are extracted by pandoc into a directory (``--extract-media``); the paths in the tree are
relative to the directory in which pandoc runs, so the converted text refers to them from the result.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

#: Extension → pandoc reader.
READERS = {".docx": "docx", ".odt": "odt", ".rtf": "rtf", ".md": "gfm", ".markdown": "gfm", ".html": "html",
           ".htm": "html", ".epub": "epub", ".txt": "markdown"}
#: Formats that LibreOffice converts to DOCX before pandoc.
LEGACY = {".doc"}


class ImportFailure(Exception):
    """The source cannot be read: ``code`` is the diagnostic code, ``fields`` its message arguments."""

    def __init__(self, code: str, **fields: str) -> None:
        super().__init__(code)
        self.code = code
        self.fields = fields


def reader_for(source: Path, fmt: str | None) -> str | None:
    """The pandoc reader for the source (``fmt`` overrides the extension); ``None`` for an unknown format."""
    if fmt:
        return fmt
    return READERS.get(source.suffix.lower())


def _convert_legacy(source: Path, directory: Path) -> Path:
    """DOCX made from an old ``.doc`` by LibreOffice, in ``directory``."""
    from primula.odf.pdf import find_soffice

    soffice = find_soffice()
    if soffice is None:
        raise ImportFailure("P8204", file=str(source))
    profile = directory / "profile"
    command = [soffice, f"-env:UserInstallation=file://{profile}", "--headless", "--convert-to", "docx", "--outdir",
               str(directory), str(source)]
    try:
        result = subprocess.run(command, capture_output=True, timeout=300, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ImportFailure("P8202", reason=str(exc)) from None
    converted = directory / (source.stem + ".docx")
    if result.returncode != 0 or not converted.is_file():
        raise ImportFailure("P8202", reason="LibreOffice could not convert " + source.name)
    return converted


def read_ast(source: Path, fmt: str | None, media_directory: Path | None, run_in: Path) -> dict:
    """The pandoc AST of the source.

    Args:
        source: the file to read.
        fmt: the pandoc reader, or ``None`` to choose by the extension.
        media_directory: where pandoc extracts the images of the source (a path relative to ``run_in``); ``None`` — not at all.
        run_in: the working directory of pandoc: the paths of the extracted media in the tree are relative to it.

    Raises:
        ImportFailure: P8201 (pandoc is not found), P8202 (pandoc failed), P8203 (unknown format), P8204 (an old ``.doc`` without LibreOffice).
    """
    pandoc = shutil.which("pandoc")
    if pandoc is None:
        raise ImportFailure("P8201")
    with tempfile.TemporaryDirectory(prefix="primula-import-") as temporary:
        path = source.resolve()
        reader = reader_for(path, fmt)
        if reader is None and path.suffix.lower() in LEGACY:
            path, reader = _convert_legacy(path, Path(temporary)), "docx"
        if reader is None:
            raise ImportFailure("P8203", suffix=path.suffix or "(none)")
        # A DOCX keeps its styles as custom-style attributes (primula.importer.styles maps them).
        command = [pandoc, "-f", "docx+styles" if reader == "docx" else reader, "-t", "json", str(path)]
        if media_directory is not None:
            command.append(f"--extract-media={media_directory}")
        try:
            result = subprocess.run(command, capture_output=True, cwd=run_in, timeout=300, check=False)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise ImportFailure("P8202", reason=str(exc)) from None
    if result.returncode != 0:
        lines = result.stderr.decode("utf-8", "replace").strip().splitlines()
        raise ImportFailure("P8202", reason=lines[-1] if lines else f"exit {result.returncode}")
    return json.loads(result.stdout)
