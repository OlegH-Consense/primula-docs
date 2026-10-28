"""Source files, text normalisation and source positions.

Implements the preprocessing steps that precede the grammar (specification
section 2.1, grammar header "Preprocessing"):

1. decoding UTF-8 (a UTF-8 byte order mark is dropped);
2. line ends normalised to LF: CR LF and a lone CR become LF;
3. Unicode normalisation form NFC.

All later phases work on the *normalised* text and address it by character
offsets (``int``, 0-based).  Positions shown to the user follow decision 26
of the specification (section 14.2):

* lines and columns are numbered from 1;
* a column is the number of the Unicode character (code point) in the line,
  a tab is one character;
* a position refers to the source file *before* NFC normalisation.

Line numbers never change during normalisation (CR LF -> LF keeps the line,
NFC never touches LF), so only columns of lines changed by NFC need mapping;
such lines are rare (decomposed letters such as "и" + U+0306 instead of "й")
and get an explicit column table.

Only LF is a line break.  ``str.splitlines`` is deliberately not used: it
also splits at U+2028, U+0085, form feed and others, which are ordinary
characters for Primula.
"""

from __future__ import annotations

import bisect
import hashlib
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

#: UTF-8 encoded byte order mark.
_UTF8_BOM = b"\xef\xbb\xbf"

#: Unsaved editor buffers (``primula check --overlay FILE=BUFFER``, 14.1;
#: Primula Studio, stage 14.2): resolved path of a source file -> the file
#: holding its current text.  The text is read from the buffer, while the
#: name, positions, hashes in the report and the registries of references
#: still refer to the original path.  Set for one run by the CLI.
_OVERLAYS: dict[Path, Path] = {}


def set_overlays(overlays: dict[Path, Path]) -> None:
    """Replace the overlay table (an empty mapping clears it).

    Args:
        overlays: source path -> buffer path; source paths are resolved.
    """
    _OVERLAYS.clear()
    _OVERLAYS.update({source.resolve(): buffer for source, buffer in overlays.items()})


def overlaid(path: Path) -> bool:
    """Whether the text of ``path`` comes from an editor buffer."""
    return bool(_OVERLAYS) and path.resolve() in _OVERLAYS


def read_source_bytes(path: Path) -> bytes:
    """Raw contents of a source file, or of its overlay buffer.

    Raises:
        OSError: the file (or the buffer) cannot be read.
    """
    if _OVERLAYS:
        buffer = _OVERLAYS.get(path.resolve())
        if buffer is not None:
            return buffer.read_bytes()
    return path.read_bytes()


@dataclass(frozen=True)
class Position:
    """A user-visible position in a source file.

    Attributes:
        line: line number, from 1.
        column: column in code points of the original (pre-NFC) line, from 1.
    """

    line: int
    column: int


class SourceReadError(Exception):
    """The file could not be read (missing, no permission, a directory...).

    Attributes:
        path: path that was requested.
        reason: OS error text.
    """

    def __init__(self, path: Path, reason: str) -> None:
        super().__init__(f"{path}: {reason}")
        self.path = path
        self.reason = reason


class SourceDecodeError(Exception):
    """The file is not valid UTF-8.

    Attributes:
        partial: a :class:`SourceFile` made of the valid prefix of the file,
            so that the error can be shown with an ordinary source position.
        offset: offset in ``partial.text`` where the invalid bytes start
            (always the end of the partial text).
        byte_offset: offset of the first invalid byte in the raw file.
    """

    def __init__(self, partial: "SourceFile", offset: int, byte_offset: int) -> None:
        super().__init__(f"{partial.name}: invalid UTF-8 at byte {byte_offset}")
        self.partial = partial
        self.offset = offset
        self.byte_offset = byte_offset


def normalize_newlines(text: str) -> str:
    """Convert CR LF and lone CR line ends to LF.

    Args:
        text: decoded text.

    Returns:
        The text with LF line ends only.
    """
    if "\r" not in text:
        return text
    return text.replace("\r\n", "\n").replace("\r", "\n")


def _nfc_column_map(original: str, normalized: str) -> list[int]:
    """Build the column table of a line changed by NFC normalisation.

    For every offset ``j`` in the normalised line (``0..len(normalized)``)
    the table gives the offset of the original character that produced the
    normalised character ``j``: the smallest original prefix length ``i``
    such that ``NFC(original[:i + 1])`` is longer than ``j``.  For example,
    original ``"и\\u0306x"`` (3 code points) and normalised ``"йx"``
    (2 code points) give ``[0, 2, 3]``.

    The computation is quadratic in the line length, but it runs only for
    lines that NFC actually changed.

    Args:
        original: the line before normalisation (without LF).
        normalized: ``unicodedata.normalize("NFC", original)``.

    Returns:
        A list of ``len(normalized) + 1`` original offsets; the last element
        is ``len(original)``.
    """
    table: list[int] = []
    produced = 0  # length of NFC(original[:i]) for the current i
    for i in range(len(original)):
        now = len(unicodedata.normalize("NFC", original[: i + 1]))
        # Normalised characters that appear when original[i] is included
        # map to offset i.  A combining mark composed into the previous
        # character produces nothing new and gets no table entry.
        while produced < now and len(table) < len(normalized):
            table.append(i)
            produced += 1
        produced = max(produced, now)
    while len(table) < len(normalized):
        table.append(len(original))
    table.append(len(original))
    return table


@dataclass(eq=False)
class SourceFile:
    """A decoded and normalised source text with position mapping.

    Create instances with :meth:`from_bytes` (files) or :meth:`from_text`
    (in-memory text, tests).  The object is immutable after construction.

    Attributes:
        name: display name used in diagnostics (usually the path as given
            on the command line or relative to the project root).
        text: normalised text (LF line ends, NFC, no BOM).
        path: filesystem path, ``None`` for in-memory sources.
        sha256: hex SHA-256 of the raw bytes (for the build report,
            specification section 14.3); for in-memory sources — of the
            UTF-8 encoding of the given text.
        had_bom: the raw data started with a UTF-8 BOM.
    """

    name: str
    text: str
    path: Path | None = None
    sha256: str = ""
    had_bom: bool = False
    # Offsets of line starts in `text`; line_starts[0] == 0.
    _line_starts: list[int] = field(default_factory=list, repr=False)
    # Column tables of lines changed by NFC: 0-based line index -> table.
    _column_maps: dict[int, list[int]] = field(default_factory=dict, repr=False)

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    @classmethod
    def from_text(cls, name: str, text: str, *, path: Path | None = None,
                  sha256: str | None = None, had_bom: bool = False) -> "SourceFile":
        """Normalise a decoded text and build a source file.

        Args:
            name: display name.
            text: decoded text; may still contain CR LF, a BOM character at
                the start and non-NFC sequences.
            path: filesystem path if the text comes from a file.
            sha256: hash of the raw bytes; computed from ``text`` if omitted.
            had_bom: the raw bytes started with a BOM (set by
                :meth:`from_bytes`).

        Returns:
            The new :class:`SourceFile`.
        """
        if sha256 is None:
            sha256 = hashlib.sha256(text.encode("utf-8")).hexdigest()
        if text.startswith("﻿"):
            text = text[1:]
            had_bom = True
        text = normalize_newlines(text)

        # NFC line by line: LF is a starter that never composes, so the
        # result equals NFC of the whole text, and lines keep their numbers.
        column_maps: dict[int, list[int]] = {}
        if not unicodedata.is_normalized("NFC", text):
            lines = text.split("\n")
            for index, line in enumerate(lines):
                if not unicodedata.is_normalized("NFC", line):
                    normalized = unicodedata.normalize("NFC", line)
                    column_maps[index] = _nfc_column_map(line, normalized)
                    lines[index] = normalized
            text = "\n".join(lines)

        line_starts = [0]
        position = text.find("\n")
        while position != -1:
            line_starts.append(position + 1)
            position = text.find("\n", position + 1)

        return cls(name=name, text=text, path=path, sha256=sha256, had_bom=had_bom,
                   _line_starts=line_starts, _column_maps=column_maps)

    @classmethod
    def from_bytes(cls, name: str, data: bytes, *, path: Path | None = None) -> "SourceFile":
        """Decode raw file contents as UTF-8 and normalise them.

        Args:
            name: display name.
            data: raw file contents.
            path: filesystem path.

        Returns:
            The new :class:`SourceFile`.

        Raises:
            SourceDecodeError: the data is not valid UTF-8; the exception
                carries a partial source made of the valid prefix.
        """
        digest = hashlib.sha256(data).hexdigest()
        had_bom = data.startswith(_UTF8_BOM)
        raw = data[len(_UTF8_BOM):] if had_bom else data
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            prefix = raw[: exc.start].decode("utf-8")  # valid by construction
            partial = cls.from_text(name, prefix, path=path, sha256=digest, had_bom=had_bom)
            raise SourceDecodeError(partial, len(partial.text),
                                    exc.start + (len(_UTF8_BOM) if had_bom else 0)) from None
        return cls.from_text(name, text, path=path, sha256=digest, had_bom=had_bom)

    @classmethod
    def from_path(cls, path: Path, name: str | None = None) -> "SourceFile":
        """Read a file and build a source file.

        Args:
            path: file to read.
            name: display name; defaults to ``str(path)``.

        Returns:
            The new :class:`SourceFile`.

        Raises:
            SourceReadError: the file cannot be read.
            SourceDecodeError: the file is not valid UTF-8.
        """
        display = name if name is not None else str(path)
        try:
            data = read_source_bytes(path)
        except OSError as exc:
            raise SourceReadError(path, exc.strerror or str(exc)) from None
        return cls.from_bytes(display, data, path=path)

    # ------------------------------------------------------------------
    # Lines and positions
    # ------------------------------------------------------------------

    @property
    def line_count(self) -> int:
        """Number of lines; a text ending with LF has an empty last line."""
        return len(self._line_starts)

    def line_index(self, offset: int) -> int:
        """Return the 0-based index of the line containing ``offset``.

        Args:
            offset: character offset in :attr:`text`, ``0..len(text)``.
        """
        if not 0 <= offset <= len(self.text):
            raise ValueError(f"offset {offset} out of range 0..{len(self.text)}")
        return bisect.bisect_right(self._line_starts, offset) - 1

    def line_start(self, line: int) -> int:
        """Return the offset of the first character of a line.

        Args:
            line: line number from 1.
        """
        return self._line_starts[line - 1]

    def line_text(self, line: int) -> str:
        """Return the normalised text of a line without its LF.

        Args:
            line: line number from 1.
        """
        start = self._line_starts[line - 1]
        end = self.text.find("\n", start)
        return self.text[start:] if end == -1 else self.text[start:end]

    def position(self, offset: int) -> Position:
        """Convert a character offset to a user-visible position.

        Args:
            offset: character offset in the normalised :attr:`text`.

        Returns:
            Line and original column (both from 1), see the module notes.
        """
        index = self.line_index(offset)
        column0 = offset - self._line_starts[index]
        table = self._column_maps.get(index)
        if table is not None:
            column0 = table[min(column0, len(table) - 1)]
        return Position(index + 1, column0 + 1)

    def normalized_column(self, offset: int) -> int:
        """Return the 1-based column of ``offset`` in the *normalised* line.

        Used to draw the ``^^^`` underline under the normalised line text.
        """
        index = self.line_index(offset)
        return offset - self._line_starts[index] + 1

    def offset_at(self, line: int, column0: int) -> int:
        """Return the offset of a 0-based normalised column in a line.

        Args:
            line: line number from 1.
            column0: 0-based column in the normalised line; clamped to the
                end of the line.
        """
        start = self._line_starts[line - 1]
        return min(start + column0, start + len(self.line_text(line)))


def utf8_column_to_chars(line: str, byte_column: int) -> int:
    """Convert a UTF-8 byte column to a character column.

    Python's :mod:`ast` reports ``col_offset`` / ``end_col_offset`` as UTF-8
    byte offsets within the line (see the ``ast`` module documentation,
    https://docs.python.org/3/library/ast.html#ast.AST.col_offset); Cyrillic
    letters take two bytes, so the values must be converted before they are
    combined with character offsets.

    Args:
        line: the text of the line the column refers to.
        byte_column: 0-based offset in the UTF-8 encoding of ``line``.

    Returns:
        The 0-based character offset.  A byte column inside a multi-byte
        character is rounded down to that character.
    """
    encoded = line.encode("utf-8")
    return len(encoded[:byte_column].decode("utf-8", errors="ignore"))


@dataclass(frozen=True)
class Span:
    """A half-open range ``[start, end)`` of character offsets in a source.

    Attributes:
        source: the source file.
        start: first offset.
        end: offset after the last character; ``start == end`` is a point.
    """

    source: SourceFile
    start: int
    end: int

    @property
    def begin_position(self) -> Position:
        """User-visible position of :attr:`start`."""
        return self.source.position(self.start)

    @property
    def end_position(self) -> Position:
        """User-visible position of :attr:`end`."""
        return self.source.position(self.end)

    def text(self) -> str:
        """Return the normalised source text covered by the span."""
        return self.source.text[self.start:self.end]


class SourceManager:
    """Loads source files once and keeps them for diagnostics and the report.

    The manager caches files by resolved path, so a fragment included twice
    is read once and positions stay consistent (specification 10.2, 14.3).
    """

    def __init__(self) -> None:
        self._by_path: dict[Path, SourceFile] = {}
        self._files: list[SourceFile] = []

    @property
    def files(self) -> list[SourceFile]:
        """Files loaded so far, in loading order."""
        return list(self._files)

    def load(self, path: Path, name: str | None = None) -> SourceFile:
        """Load a file (or return the cached copy).

        Args:
            path: file path.
            name: display name; defaults to ``str(path)``.

        Returns:
            The source file.

        Raises:
            SourceReadError, SourceDecodeError: see :meth:`SourceFile.from_path`.
        """
        key = path.resolve()
        cached = self._by_path.get(key)
        if cached is not None:
            return cached
        source = SourceFile.from_path(path, name)
        self._by_path[key] = source
        self._files.append(source)
        return source

    def add(self, source: SourceFile) -> SourceFile:
        """Register an in-memory source (tests, editor buffers).

        Args:
            source: the source to register.

        Returns:
            The same source.
        """
        self._files.append(source)
        return source
