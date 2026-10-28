"""QR codes and Base64URL (library 10, decision 137).

``qr_matrix(data, ecc="M", min_version=1, max_version=40)`` — the QR code of
a text in byte mode (ДСТУ ISO/IEC 18004:2019 = ISO/IEC 18004:2015): the
smallest version from ``min_version`` that holds the UTF-8 bytes of
``data`` with the error correction level ``ecc`` (``L``, ``M``, ``Q``,
``H``); a record ``{version, ecc, mask, size, rows}`` where ``rows`` are
strings of ``"1"`` (dark) and ``"0"`` (light) without the quiet zone.

``qr_svg(data, …, size="30mm", quiet=4, circle=0)`` — the same code as an
SVG string for ``|img(svg=…)``: one path of dark modules in a viewBox
measured in modules, the quiet zone of ``quiet`` modules, and, when
``circle`` > 0, a white circle of that diameter (in modules) in the centre
— the place of a sign such as the hryvnia sign of the NBU payment codes;
the level of error correction must cover the modules it hides.

``base64url(text, encoding="utf-8")`` — Base64URL (RFC 4648, section 5)
of the bytes of ``text`` in ``utf-8`` or ``cp1251``, without ``=`` padding
(the structure of the NBU payment QR codes, formats 002 and 003).

The encoder follows the standard step by step — data bits, Reed–Solomon
blocks and their interleaving, function patterns, the zigzag placement,
the eight masks with the penalty rules N1–N4, format and version
information — after the structure of Project Nayuki's "QR Code generator
library" (MIT, https://www.nayuki.io/page/qr-code-generator-library),
reduced to byte mode.  It is checked against an independent decoder
(``zbarimg``) and the ``qrencode`` tool in ``tests/test_library_qr.py``.
"""

from __future__ import annotations

import base64
from decimal import Decimal
from typing import Any

from primula.core.values import Length, PList, Record, freeze, parse_length
from primula.library.context import Library, integer, keywords, lib_error, positional, string

#: Error correction levels: index into the tables and the two format bits.
ECC_LEVELS = {"L": (0, 1), "M": (1, 0), "Q": (2, 3), "H": (3, 2)}

# Error correction codewords per block and the number of blocks, by level
# (L, M, Q, H) and version 1..40 (ISO/IEC 18004, table 9); index 0 unused.
_ECC_PER_BLOCK = (
    (-1, 7, 10, 15, 20, 26, 18, 20, 24, 30, 18, 20, 24, 26, 30, 22, 24, 28, 30, 28, 28, 28, 28, 30, 30, 26, 28, 30,
     30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30),
    (-1, 10, 16, 26, 18, 24, 16, 18, 22, 22, 26, 30, 22, 22, 24, 24, 28, 28, 26, 26, 26, 26, 28, 28, 28, 28, 28, 28,
     28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28),
    (-1, 13, 22, 18, 26, 18, 24, 18, 22, 20, 24, 28, 26, 24, 20, 30, 24, 28, 28, 26, 30, 28, 30, 30, 30, 30, 28, 30,
     30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30),
    (-1, 17, 28, 22, 16, 22, 28, 26, 26, 24, 28, 24, 28, 22, 24, 24, 30, 28, 28, 26, 28, 30, 24, 30, 30, 30, 30, 30,
     30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30),
)
_BLOCKS = (
    (-1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 4, 4, 4, 4, 4, 6, 6, 6, 6, 7, 8, 8, 9, 9, 10, 12, 12, 12, 13, 14, 15, 16, 17, 18,
     19, 19, 20, 21, 22, 24, 25),
    (-1, 1, 1, 1, 2, 2, 4, 4, 4, 5, 5, 5, 8, 9, 9, 10, 10, 11, 13, 14, 16, 17, 17, 18, 20, 21, 23, 25, 26, 28, 29, 31,
     33, 35, 37, 38, 40, 43, 45, 47, 49),
    (-1, 1, 1, 2, 2, 4, 4, 6, 6, 8, 8, 8, 10, 12, 16, 12, 17, 16, 18, 21, 20, 23, 23, 25, 27, 29, 34, 34, 35, 38, 40,
     43, 45, 48, 51, 53, 56, 59, 62, 65, 68),
    (-1, 1, 1, 2, 4, 4, 4, 5, 6, 8, 8, 11, 11, 16, 16, 18, 16, 19, 21, 25, 25, 25, 34, 30, 32, 35, 37, 40, 42, 45, 48,
     51, 54, 57, 60, 63, 66, 70, 74, 77, 81),
)

_PENALTY_N1, _PENALTY_N2, _PENALTY_N3, _PENALTY_N4 = 3, 3, 40, 10

#: Encodings of base64url() and the QR byte data of qr_*(…, encoding=…).
ENCODINGS = ("utf-8", "cp1251")


# --- the encoder --------------------------------------------------------------------------------

def raw_data_modules(version: int) -> int:
    """Modules of a version left for data and error correction (without function patterns)."""
    result = (16 * version + 128) * version + 64
    if version >= 2:
        alignments = version // 7 + 2
        result -= (25 * alignments - 10) * alignments - 55
        if version >= 7:
            result -= 36
    return result


def data_codewords(version: int, level: int) -> int:
    """Data codewords of a version at an error correction level."""
    return raw_data_modules(version) // 8 - _ECC_PER_BLOCK[level][version] * _BLOCKS[level][version]


def _rs_divisor(degree: int) -> list[int]:
    """The Reed–Solomon generator polynomial of ``degree`` over GF(256) (0x11D), leading 1 omitted."""
    result = [0] * (degree - 1) + [1]
    root = 1
    for _ in range(degree):
        for j in range(degree):
            result[j] = _gf_multiply(result[j], root)
            if j + 1 < degree:
                result[j] ^= result[j + 1]
        root = _gf_multiply(root, 0x02)
    return result


def _rs_remainder(data: bytes, divisor: list[int]) -> list[int]:
    """Error correction codewords: the remainder of ``data`` · x^n divided by the generator."""
    result = [0] * len(divisor)
    for byte in data:
        factor = byte ^ result.pop(0)
        result.append(0)
        for i, coefficient in enumerate(divisor):
            result[i] ^= _gf_multiply(coefficient, factor)
    return result


def _gf_multiply(x: int, y: int) -> int:
    """Product in GF(2^8) with the reducing polynomial x^8 + x^4 + x^3 + x^2 + 1."""
    z = 0
    for i in reversed(range(8)):
        z = (z << 1) ^ ((z >> 7) * 0x11D)
        z ^= ((y >> i) & 1) * x
    return z


def _codewords(payload: bytes, version: int, level: int) -> list[int]:
    """Data bits of byte mode, padding, Reed–Solomon blocks, interleaving."""
    capacity = data_codewords(version, level) * 8
    bits: list[int] = []

    def put(value: int, length: int) -> None:
        bits.extend((value >> i) & 1 for i in reversed(range(length)))

    put(0b0100, 4)                                   # byte mode
    put(len(payload), 8 if version <= 9 else 16)    # character count
    for byte in payload:
        put(byte, 8)
    put(0, min(4, capacity - len(bits)))             # terminator
    put(0, -len(bits) % 8)
    pad = 0xEC
    while len(bits) < capacity:
        put(pad, 8)
        pad ^= 0xEC ^ 0x11
    data = bytes(int("".join(map(str, bits[i:i + 8])), 2) for i in range(0, len(bits), 8))

    blocks_count = _BLOCKS[level][version]
    ecc_len = _ECC_PER_BLOCK[level][version]
    raw_codewords = raw_data_modules(version) // 8
    short_count = blocks_count - raw_codewords % blocks_count
    short_len = raw_codewords // blocks_count
    divisor = _rs_divisor(ecc_len)
    blocks: list[list[int]] = []
    k = 0
    for i in range(blocks_count):
        length = short_len - ecc_len + (0 if i < short_count else 1)
        block = list(data[k:k + length])
        k += length
        ecc = _rs_remainder(bytes(block), divisor)
        if i < short_count:
            block.append(-1)                         # placeholder: short blocks have one data codeword less
        blocks.append(block + ecc)
    result = []
    for i in range(len(blocks[0])):
        for j, block in enumerate(blocks):
            if i != short_len - ecc_len or j >= short_count:
                result.append(block[i])
    return result


class _Matrix:
    """The module grid of one version: dark modules and the function-pattern mask."""

    def __init__(self, version: int) -> None:
        self.version = version
        self.size = version * 4 + 17
        self.dark = [[False] * self.size for _ in range(self.size)]
        self.function = [[False] * self.size for _ in range(self.size)]

    def set(self, x: int, y: int, dark: bool) -> None:
        self.dark[y][x] = dark
        self.function[y][x] = True

    def alignment_positions(self) -> list[int]:
        if self.version == 1:
            return []
        count = self.version // 7 + 2
        step = (self.version * 8 + count * 3 + 5) // (count * 4 - 4) * 2
        return [6] + [self.size - 7 - i * step for i in reversed(range(count - 1))]

    def draw_function_patterns(self) -> None:
        size = self.size
        for i in range(size):                          # timing patterns
            self.set(6, i, i % 2 == 0)
            self.set(i, 6, i % 2 == 0)
        for cx, cy in ((3, 3), (size - 4, 3), (3, size - 4)):
            for dy in range(-4, 5):                    # finder with separator
                for dx in range(-4, 5):
                    x, y = cx + dx, cy + dy
                    if 0 <= x < size and 0 <= y < size:
                        distance = max(abs(dx), abs(dy))
                        self.set(x, y, distance not in (2, 4))
        positions = self.alignment_positions()
        last = len(positions) - 1
        for i, cx in enumerate(positions):
            for j, cy in enumerate(positions):
                if (i == 0 and j == 0) or (i == 0 and j == last) or (i == last and j == 0):
                    continue                           # the corners of the finders
                for dy in range(-2, 3):
                    for dx in range(-2, 3):
                        self.set(cx + dx, cy + dy, max(abs(dx), abs(dy)) != 1)
        self.draw_format(0, 0)                         # reserve; drawn again after masking
        self.draw_version()

    def draw_format(self, level_bits: int, mask: int) -> None:
        data = level_bits << 3 | mask
        rem = data
        for _ in range(10):
            rem = (rem << 1) ^ ((rem >> 9) * 0x537)
        bits = (data << 10 | rem) ^ 0x5412
        size = self.size

        def bit(i: int) -> bool:
            return (bits >> i) & 1 != 0

        for i in range(6):
            self.set(8, i, bit(i))
        self.set(8, 7, bit(6))
        self.set(8, 8, bit(7))
        self.set(7, 8, bit(8))
        for i in range(9, 15):
            self.set(14 - i, 8, bit(i))
        for i in range(8):
            self.set(size - 1 - i, 8, bit(i))
        for i in range(8, 15):
            self.set(8, size - 15 + i, bit(i))
        self.set(8, size - 8, True)                   # the dark module

    def draw_version(self) -> None:
        if self.version < 7:
            return
        rem = self.version
        for _ in range(12):
            rem = (rem << 1) ^ ((rem >> 11) * 0x1F25)
        bits = self.version << 12 | rem
        for i in range(18):
            dark = (bits >> i) & 1 != 0
            a, b = self.size - 11 + i % 3, i // 3
            self.set(a, b, dark)
            self.set(b, a, dark)

    def place(self, codewords: list[int]) -> None:
        """The zigzag placement of the data bits in the free modules."""
        size = self.size
        i = 0
        total = len(codewords) * 8
        right = size - 1
        while right >= 1:
            if right == 6:
                right = 5
            for vertical in range(size):
                for j in range(2):
                    x = right - j
                    upward = (right + 1) & 2 == 0
                    y = size - 1 - vertical if upward else vertical
                    if not self.function[y][x] and i < total:
                        self.dark[y][x] = (codewords[i >> 3] >> (7 - (i & 7))) & 1 != 0
                        i += 1
            right -= 2

    def apply_mask(self, mask: int) -> None:
        for y in range(self.size):
            for x in range(self.size):
                if self.function[y][x]:
                    continue
                if mask == 0:
                    invert = (x + y) % 2 == 0
                elif mask == 1:
                    invert = y % 2 == 0
                elif mask == 2:
                    invert = x % 3 == 0
                elif mask == 3:
                    invert = (x + y) % 3 == 0
                elif mask == 4:
                    invert = (x // 3 + y // 2) % 2 == 0
                elif mask == 5:
                    invert = x * y % 2 + x * y % 3 == 0
                elif mask == 6:
                    invert = (x * y % 2 + x * y % 3) % 2 == 0
                else:
                    invert = ((x + y) % 2 + x * y % 3) % 2 == 0
                self.dark[y][x] ^= invert

    def penalty(self) -> int:
        """Penalty points N1–N4 of the current modules (ISO/IEC 18004, 7.8.3)."""
        size = self.size
        result = 0
        for lines in (self.dark, [list(column) for column in zip(*self.dark)]):
            for line in lines:
                run_color = False
                run = 0
                history = [0] * 7
                for value in line:
                    if value == run_color:
                        run += 1
                        if run == 5:
                            result += _PENALTY_N1
                        elif run > 5:
                            result += 1
                    else:
                        self._history_add(run, history)
                        if not run_color:
                            result += self._finder_count(history) * _PENALTY_N3
                        run_color = value
                        run = 1
                result += self._finder_terminate(run_color, run, history) * _PENALTY_N3
        for y in range(size - 1):
            for x in range(size - 1):
                color = self.dark[y][x]
                if color == self.dark[y][x + 1] == self.dark[y + 1][x] == self.dark[y + 1][x + 1]:
                    result += _PENALTY_N2
        dark = sum(row.count(True) for row in self.dark)
        total = size * size
        k = (abs(dark * 20 - total * 10) + total - 1) // total - 1
        result += k * _PENALTY_N4
        return result

    def _history_add(self, run: int, history: list[int]) -> None:
        if history[0] == 0:
            run += self.size                           # the light border before the line
        history.pop()
        history.insert(0, run)

    @staticmethod
    def _finder_count(history: list[int]) -> int:
        n = history[1]
        core = n > 0 and history[2] == history[4] == history[5] == n and history[3] == n * 3
        return ((1 if core and history[0] >= n * 4 and history[6] >= n else 0)
                + (1 if core and history[6] >= n * 4 and history[0] >= n else 0))

    def _finder_terminate(self, run_color: bool, run: int, history: list[int]) -> int:
        if run_color:
            self._history_add(run, history)
            run = 0
        run += self.size                               # the light border after the line
        self._history_add(run, history)
        return self._finder_count(history)


def encode(payload: bytes, ecc: str = "M", min_version: int = 1, max_version: int = 40) -> _Matrix | None:
    """The QR code of ``payload`` in byte mode, or ``None`` if it does not fit ``max_version``.

    Args:
        payload: the bytes to encode.
        ecc: ``L``, ``M``, ``Q`` or ``H``.
        min_version, max_version: the range of versions (1..40).

    Returns:
        The matrix with the best mask (lowest penalty, the first on a tie).
    """
    level, level_bits = ECC_LEVELS[ecc]
    for version in range(min_version, max_version + 1):
        count_bits = 8 if version <= 9 else 16
        if len(payload) < 1 << count_bits and 4 + count_bits + len(payload) * 8 <= data_codewords(version, level) * 8:
            break
    else:
        return None
    codewords = _codewords(payload, version, level)
    best: tuple[int, int] | None = None
    for mask in range(8):
        matrix = _built(version, codewords, level_bits, mask)
        score = matrix.penalty()
        if best is None or score < best[0]:
            best = (score, mask)
    assert best is not None
    result = _built(version, codewords, level_bits, best[1])
    result.mask = best[1]  # type: ignore[attr-defined]
    return result


def _built(version: int, codewords: list[int], level_bits: int, mask: int) -> _Matrix:
    matrix = _Matrix(version)
    matrix.draw_function_patterns()
    matrix.place(codewords)
    matrix.apply_mask(mask)
    matrix.draw_format(level_bits, mask)
    return matrix


def svg(matrix: _Matrix, size: Length, quiet: int, circle: Decimal) -> str:
    """SVG of a matrix: dark modules as one path, the quiet zone, an optional white circle.

    The viewBox is in modules, the width and height are ``size``; horizontal
    runs of dark modules are joined into one rectangle each.
    """
    side = matrix.size + 2 * quiet
    parts = []
    for y, row in enumerate(matrix.dark):
        x = 0
        while x < matrix.size:
            if row[x]:
                start = x
                while x < matrix.size and row[x]:
                    x += 1
                parts.append(f"M{start + quiet} {y + quiet}h{x - start}v1h-{x - start}z")
            else:
                x += 1
    width = f"{_number(size.value)}{size.unit if size.unit != 'inch' else 'in'}"
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{width}" viewBox="0 0 {side} {side}" '
           f'shape-rendering="crispEdges">',
           f'<rect width="{side}" height="{side}" fill="#fff"/>',
           f'<path fill="#000" d="{"".join(parts)}"/>']
    if circle > 0:
        centre = _number(Decimal(side) / 2)
        out.append(f'<circle cx="{centre}" cy="{centre}" r="{_number(circle / 2)}" fill="#fff"/>')
    out.append("</svg>")
    return "".join(out)


def _number(value: Decimal) -> str:
    text = format(value.normalize(), "f")
    return text


# --- library functions ---------------------------------------------------------------------------

_QR_KEYS = ("ecc", "min_version", "max_version", "encoding")


def _qr_args(function: str, args: list[Any], kwargs: dict[str, Any], extra: tuple[str, ...], span: Any
             ) -> tuple[_Matrix, dict[str, Any]]:
    positional(function, args, 1, 1, span)
    keywords(function, kwargs, _QR_KEYS + extra, span)
    data = string(function, "data", args[0], span)
    ecc = string(function, "ecc", kwargs.get("ecc", "M"), span)
    if ecc not in ECC_LEVELS:
        raise lib_error("P2704", span, None, function=function, value=ecc, range="L, M, Q, H")
    low = integer(function, "min_version", kwargs.get("min_version", Decimal(1)), span)
    high = integer(function, "max_version", kwargs.get("max_version", Decimal(40)), span)
    if not 1 <= low <= high <= 40:
        raise lib_error("P2704", span, None, function=function, value=f"{low}..{high}", range="1 ≤ min_version ≤ "
                        "max_version ≤ 40")
    payload = _bytes(function, data, kwargs.get("encoding", "utf-8"), span)
    matrix = encode(payload, ecc, low, high)
    if matrix is None:
        raise lib_error("P2728", span, None, function=function, size=len(payload), ecc=ecc, version=high)
    return matrix, kwargs


def _bytes(function: str, text: str, encoding: Any, span: Any) -> bytes:
    encoding = string(function, "encoding", encoding, span)
    if encoding not in ENCODINGS:
        raise lib_error("P2704", span, None, function=function, value=encoding, range=", ".join(ENCODINGS))
    try:
        return text.encode(encoding)
    except UnicodeEncodeError as exc:
        raise lib_error("P2729", span, None, function=function, char=text[exc.start],
                        encoding=encoding) from None


def qr_matrix(lib: Library, args: list[Any], kwargs: dict[str, Any], span: Any) -> Record:
    """``qr_matrix(data, ecc="M", min_version=1, max_version=40, encoding="utf-8")``."""
    matrix, _ = _qr_args("qr_matrix", args, kwargs, (), span)
    rows = PList("".join("1" if dark else "0" for dark in row) for row in matrix.dark)
    return freeze(Record({"version": Decimal(matrix.version), "ecc": kwargs.get("ecc", "M"),
                          "mask": Decimal(matrix.mask), "size": Decimal(matrix.size),  # type: ignore[attr-defined]
                          "rows": rows}))


def qr_svg(lib: Library, args: list[Any], kwargs: dict[str, Any], span: Any) -> str:
    """``qr_svg(data, …, size="30mm", quiet=4, circle=0)``."""
    matrix, _ = _qr_args("qr_svg", args, kwargs, ("size", "quiet", "circle"), span)
    size = kwargs.get("size", "30mm")
    length = size if isinstance(size, Length) else parse_length(string("qr_svg", "size", size, span))
    if length is None or length.value <= 0:
        raise lib_error("P2704", span, None, function="qr_svg", value=str(size), range="> 0mm")
    quiet = integer("qr_svg", "quiet", kwargs.get("quiet", Decimal(4)), span)
    if not 0 <= quiet <= 16:
        raise lib_error("P2704", span, None, function="qr_svg", value=str(quiet), range="0..16")
    circle = kwargs.get("circle", Decimal(0))
    integer("qr_svg", "circle", circle, span)
    circle = Decimal(circle)
    if not 0 <= circle <= matrix.size:
        raise lib_error("P2704", span, None, function="qr_svg", value=str(circle), range=f"0..{matrix.size}")
    return svg(matrix, length, quiet, circle)


def base64url(lib: Library, args: list[Any], kwargs: dict[str, Any], span: Any) -> str:
    """``base64url(text, encoding="utf-8")``."""
    positional("base64url", args, 1, 1, span)
    keywords("base64url", kwargs, ("encoding",), span)
    text = string("base64url", "text", args[0], span)
    payload = _bytes("base64url", text, kwargs.get("encoding", "utf-8"), span)
    return base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")


FUNCTIONS = {"qr_matrix": qr_matrix, "qr_svg": qr_svg, "base64url": base64url}
