"""Loading of source files referenced by a document (10.1-10.3, decision 50).

Path rules:

* a path is relative to the file containing the command;
* it must not leave the project root; without a project file the root is
  the directory of the root document (decision 50); the root is checked on
  the path as written, so a symbolic link created inside the project may
  lead to a library elsewhere (warning P2639, decision 136;
  :mod:`primula.paths`);
* URLs, absolute paths and cycles of inclusion are errors;
* the extension ``.prml`` may be omitted: then the file with the
  sub-extension of the command is looked for first (``.f.prml`` for
  ``|include``, ``.m.prml`` for ``|import``, ``.s.prml`` for styles
  modules), then ``name.prml`` (10.1, decision 100; :meth:`Loader.find`);
* ``--style`` files are given relative to the current directory and may lie
  outside the project root (14.1, decision 106; :meth:`Loader.resolve_option`).

Every file is read once (:class:`~primula.source.SourceManager` cache),
its header parsed and its body parsed *flat* (``organize=False``): implicit
regions are built after fragments are inserted (decision 31).
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path

from primula.core.errors import core_error
from primula.diagnostics import DiagnosticSink, warning
from primula.header import Header, parse_header
from primula.source import SourceDecodeError, SourceFile, SourceManager, SourceReadError, Span, read_source_bytes
from primula.syntax.nodes import Document
from primula.paths import lexical, outside_link, within
from primula.syntax.parser import parse

_URL = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*://")
#: Directory of built-in modules (``std/…`` paths).
STDLIB = Path(__file__).resolve().parent.parent / "stdlib"
#: Sub-extensions looked for when ``.prml`` is omitted, by expected kind (10.1).
KIND_SUFFIX = {"fragment": ".f", "module": ".m", "styles": ".s", "project": ".p"}


def strip_extension(name: str) -> str:
    """File name without ``.prml`` and a reserved sub-extension (2.2, 10.3).

    ``business.m.prml`` -> ``business``; ``a.b.prml`` -> ``a.b``.
    """
    if name.endswith(".prml"):
        name = name[:-len(".prml")]
        for suffix in KIND_SUFFIX.values():
            if name.endswith(suffix) and len(name) > len(suffix):
                return name[:-len(suffix)]
    return name


@dataclass(eq=False)
class LoadedFile:
    """A parsed source file.

    Attributes:
        path: resolved filesystem path.
        source: the source text.
        header: the parsed header.
        document: the flat parsed tree (``organize=False``).
    """

    path: Path
    source: SourceFile
    header: Header
    document: Document


@dataclass
class Loader:
    """Resolves and loads files inside a project root.

    Attributes:
        root: the project root directory.
        manager: source cache (shared with the report).
        sink: receiver of syntax diagnostics of loaded files.
    """

    root: Path
    manager: SourceManager
    sink: DiagnosticSink
    _files: dict[Path, LoadedFile] = field(default_factory=dict)
    #: Links leaving the root already reported (P2639 once per link).
    _links: set[str] = field(default_factory=set)
    #: Binary data files already registered with the source manager.
    _binary: set[Path] = field(default_factory=set)

    def resolve(self, text: str, base: SourceFile, span: Span) -> Path:
        """Resolve a path of ``|include``/``|import``/``load_*``.

        Args:
            text: the path as written.
            base: the source file containing the command (relative base).
            span: position for errors.

        Returns:
            The path inside the project root, symbolic links not followed.

        Raises:
            CoreError: P2613 for URLs, absolute paths and paths outside the
                project root.
        """
        if text.startswith("std/"):
            # Built-in modules of the language (std/styles/default, decision 55).
            return STDLIB / text[len("std/"):]
        base_dir = base.path.parent if base.path is not None else self.root
        return self._inside(text, base_dir, span)

    def resolve_root(self, text: str, span: Span) -> Path:
        """Resolve a path of the key map (9.3): relative to the project root.

        Raises:
            CoreError: P2613 as :meth:`resolve`.
        """
        return self._inside(text, self.root, span)

    def _inside(self, text: str, base_dir: Path, span: Span) -> Path:
        """``base_dir / text`` if it stays inside the project root (P2613 otherwise).

        The check is lexical (decision 136): a link inside the project may
        lead outside it; such a file is reported once per link (P2639).
        """
        if not text or _URL.match(text) or text.startswith(("/", "\\")) or Path(text).is_absolute():
            raise core_error("P2613", span, path=text)
        candidate = lexical(base_dir / text)
        if within(candidate, self.root) is None:
            raise core_error("P2613", span, path=text)
        link = outside_link(candidate, self.root)
        if link is not None and str(link[0]) not in self._links:
            self._links.add(str(link[0]))
            self.sink.emit(warning("P2639", span, path=text, link=str(link[0]), target=str(link[1])))
        return candidate

    def find(self, path: Path, kind: str | None) -> Path:
        """Add the omitted extension (10.1): ``name.<sub>.prml``, then ``name.prml``.

        Args:
            path: the resolved path as written.
            kind: the kind the command expects (selects the sub-extension).

        Returns:
            ``path`` itself if it ends with ``.prml``; otherwise the first
            existing candidate, or ``name.prml`` (its absence is reported by
            :meth:`load`).
        """
        if path.name.endswith(".prml"):
            return path
        suffix = KIND_SUFFIX.get(kind or "")
        if suffix is not None:
            candidate = path.with_name(path.name + suffix + ".prml")
            if candidate.is_file():
                return candidate
        return path.with_name(path.name + ".prml")

    def resolve_option(self, text: str) -> Path:
        """A ``--style FILE`` path: ``std/…`` or relative to the current directory (14.1)."""
        if text.startswith("std/"):
            return self.find(STDLIB / text[len("std/"):], "styles")
        return self.find(Path(text).resolve(), "styles")

    def load(self, path: Path, span: Span) -> LoadedFile:
        """Load and parse a source file (cached).

        Raises:
            CoreError: P2614 if the file cannot be read or decoded.
        """
        path = self.find(path, None)
        cached = self._files.get(path)
        if cached is not None:
            return cached
        try:
            source = self.manager.load(path, self.display_name(path))
        except SourceReadError as exc:
            raise core_error("P2614", span, path=self.display_name(path), reason=exc.reason) from None
        except SourceDecodeError:
            raise core_error("P2614", span, path=self.display_name(path), reason="not valid UTF-8") from None
        header = parse_header(source, self.sink)
        document = parse(header, self.sink, organize=False)
        loaded = LoadedFile(path, source, header, document)
        self._files[path] = loaded
        return loaded

    def display_name(self, path: Path) -> str:
        """Path relative to the project root for messages and the report."""
        try:
            return "std/" + strip_extension(str(path.resolve().relative_to(STDLIB)))
        except ValueError:
            pass
        relative = within(path, self.root)
        return str(relative) if relative is not None else str(path)

    def read_binary(self, text: str, base: SourceFile, span: Span) -> bytes:
        """Read a binary data file for ``load_ods``/``load_xlsx`` (decision 138).

        The file is registered with the source manager as an empty source
        with the SHA-256 of its bytes, so it appears in the build report like
        the text data files.
        """
        path = self.resolve(text, base, span)
        try:
            data = read_source_bytes(path)
        except OSError as exc:
            raise core_error("P2614", span, path=text, reason=exc.strerror or str(exc)) from None
        if path not in self._binary:
            self._binary.add(path)
            self.manager.add(SourceFile.from_text(self.display_name(path), "", path=path,
                                                  sha256=hashlib.sha256(data).hexdigest()))
        return data

    def read_data(self, text: str, base: SourceFile, span: Span) -> SourceFile:
        """Read a data file for ``load_*`` (UTF-8, NFC; cached; hash recorded)."""
        path = self.resolve(text, base, span)
        try:
            return self.manager.load(path, self.display_name(path))
        except SourceReadError as exc:
            raise core_error("P2614", span, path=text, reason=exc.reason) from None
        except SourceDecodeError:
            raise core_error("P2614", span, path=text, reason="not valid UTF-8") from None

