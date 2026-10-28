"""Text widths from font files (specification 6.3, step 2).

The font file of a family and style is found with fontconfig
(``fc-match -f %{file} "Family:weight=bold:slant=italic"``) — the same
fonts LibreOffice uses on Linux; advance widths come from the ``hmtx`` and
``cmap`` tables read with fontTools (an optional dependency, group
``metrics``).  Kerning is ignored: the widths only size columns, Writer
breaks the lines itself.

Without fontTools, fontconfig or the font file the width is approximated
by an average character width (0.5 em; 0.6 em for monospaced fonts), and
the caller warns once per font (P5112).

References: fontTools ``TTFont``, https://fonttools.readthedocs.io/en/latest/ttLib/ttFont.html;
fontconfig ``fc-match``, https://www.freedesktop.org/software/fontconfig/fontconfig-user.html
"""

from __future__ import annotations

import functools
import shutil
import subprocess
from dataclasses import dataclass
from fractions import Fraction

#: Millimetres in a point.
MM_PER_PT = Fraction(254, 720)


@dataclass(frozen=True)
class FontKey:
    """A font: family, bold, italic."""

    family: str
    bold: bool = False
    italic: bool = False


@functools.cache
def font_file(key: FontKey) -> str | None:
    """Path of the font file of ``key`` by fontconfig, or ``None``."""
    executable = shutil.which("fc-match")
    if executable is None:
        return None
    pattern = key.family + (":weight=bold" if key.bold else "") + (":slant=italic" if key.italic else "")
    try:
        run = subprocess.run([executable, "-f", "%{file}\n%{family}", pattern], capture_output=True, text=True,
                             timeout=10, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return None
    lines = run.stdout.split("\n")
    if run.returncode != 0 or not lines or not lines[0]:
        return None
    # fontconfig always answers with some font; accept it only for the requested family.
    families = [f.strip().lower() for f in (lines[1] if len(lines) > 1 else "").split(",")]
    if key.family.lower() not in families:
        return None
    return lines[0]


class _Font:
    """Advance widths of one font file in em fractions."""

    def __init__(self, path: str) -> None:
        from fontTools.ttLib import TTFont

        font = TTFont(path, lazy=True, fontNumber=0)
        self.units = font["head"].unitsPerEm
        self.cmap = font.getBestCmap() or {}
        self.hmtx = font["hmtx"].metrics
        widths = [advance for advance, _lsb in self.hmtx.values() if advance]
        self.average = Fraction(sum(widths), len(widths) * self.units) if widths else Fraction(1, 2)

    def width(self, text: str) -> Fraction:
        total = Fraction(0)
        for char in text:
            glyph = self.cmap.get(ord(char))
            if glyph is None or glyph not in self.hmtx:
                total += self.average
            else:
                total += Fraction(self.hmtx[glyph][0], self.units)
        return total


@functools.cache
def _load(path: str) -> _Font | None:
    try:
        return _Font(path)
    except Exception:  # noqa: BLE001 - a broken or unsupported font file: approximate
        return None


@functools.cache
def has_fonttools() -> bool:
    try:
        import fontTools.ttLib  # noqa: F401
    except ImportError:
        return False
    return True


def text_width(text: str, key: FontKey, size_pt: Fraction) -> tuple[Fraction, bool]:
    """Width of ``text`` in millimetres.

    Args:
        text: one line of text.
        key: the font.
        size_pt: font size in points.

    Returns:
        ``(width, exact)``: ``exact`` is ``False`` for the approximation.
    """
    font = None
    if has_fonttools():
        path = font_file(key)
        font = _load(path) if path else None
    if font is not None:
        return font.width(text) * size_pt * MM_PER_PT, True
    em = Fraction(3, 5) if "mono" in key.family.lower() else Fraction(1, 2)
    return em * len(text) * size_pt * MM_PER_PT, False
