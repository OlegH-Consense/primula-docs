"""Unicode rules of the language: identifiers, short-form characters, NFKC.

Specification 0.1, 3.1, 3.9 (decisions 101, 102, 114):

* the language fixes Unicode 15.1; the property tables are shipped with
  the translator (:mod:`primula.unicode_data`) instead of being taken
  from the running interpreter;
* names written by the author are identifiers by UAX #31: the first
  character has ``XID_Start``, the others ``XID_Continue`` (with ``_``);
  names are compared after NFKC normalisation, case is significant;
* after ``|`` an ASCII punctuation character or a single character of the
  general categories ``P*`` and ``S*`` is a short form.

NFC/NFKC normalisation itself comes from :mod:`unicodedata`; the version of
the running interpreter is recorded in the build report
(:func:`runtime_version`).  Differences can only concern characters added
after the interpreter's Unicode version.

The lint helpers (:func:`scripts`, :func:`skeleton`) implement the warnings
of section 3.9 about identifiers that mix alphabets and identifiers that
differ only by homoglyphs.  Python has no Unicode ``Script`` property, so
the script is taken from the character name (``LATIN``, ``CYRILLIC``,
``GREEK``); the homoglyph table covers the Latin/Cyrillic/Greek letters
that look alike in common fonts — a simplification of UTS #39.
"""

from __future__ import annotations

import bisect
import unicodedata

from primula import unicode_data

#: Unicode version of the language (decision 114).
UNICODE_VERSION = unicode_data.UNICODE_VERSION


def _starts(table: tuple[tuple[int, int], ...]) -> list[int]:
    return [first for first, _last in table]


_XS = unicode_data.XID_START
_XS_FIRST = _starts(_XS)
_XC = unicode_data.XID_CONTINUE
_XC_FIRST = _starts(_XC)
_PS = unicode_data.PUNCT_SYMBOL
_PS_FIRST = _starts(_PS)


def _in(code: int, table: tuple[tuple[int, int], ...], firsts: list[int]) -> bool:
    """Whether ``code`` lies in one of the sorted inclusive ranges."""
    index = bisect.bisect_right(firsts, code) - 1
    return index >= 0 and code <= table[index][1]


def is_xid_start(char: str) -> bool:
    """``XID_Start`` (grammar ``XidStart``); ``_`` is not a start character."""
    if char < "\x80":
        return ("a" <= char <= "z") or ("A" <= char <= "Z")
    return _in(ord(char), _XS, _XS_FIRST)


def is_xid_continue(char: str) -> bool:
    """``XID_Continue`` (grammar ``XidContinue``): letters, digits, ``_``…"""
    if char < "\x80":
        return ("a" <= char <= "z") or ("A" <= char <= "Z") or ("0" <= char <= "9") or char == "_"
    return _in(ord(char), _XC, _XC_FIRST)


def is_short_char(char: str) -> bool:
    """``ShortChar``: ASCII punctuation or a character of category ``P*``/``S*``."""
    if char < "\x80":
        return char.isprintable() and not char.isalnum() and not char.isspace() and char != ""
    return _in(ord(char), _PS, _PS_FIRST)


def is_identifier(text: str, extra: str = "") -> bool:
    """Whether ``text`` is an author identifier (section 3.9).

    Args:
        text: the name.
        extra: additional characters allowed after the first one
            (``"-"`` for style names, ``"-."`` for ``id=`` values).
    """
    if not text or not is_xid_start(text[0]):
        return False
    return all(is_xid_continue(char) or char in extra for char in text[1:])


def nfkc(text: str) -> str:
    """NFKC normal form used to compare names (UAX #15, section 3.9)."""
    return text if text.isascii() else unicodedata.normalize("NFKC", text)


def runtime_version() -> str:
    """Unicode version of the running interpreter's :mod:`unicodedata`."""
    return unicodedata.unidata_version


# ----------------------------------------------------------------------
# Lint helpers (section 3.9)
# ----------------------------------------------------------------------

_SCRIPT_PREFIXES = ("LATIN", "CYRILLIC", "GREEK")


def scripts(text: str) -> set[str]:
    """Alphabets (``LATIN``, ``CYRILLIC``, ``GREEK``) of the letters of ``text``."""
    found: set[str] = set()
    for char in text:
        if char < "\x80":
            if char.isalpha():
                found.add("LATIN")
            continue
        if not char.isalpha():
            continue
        name = unicodedata.name(char, "")
        for prefix in _SCRIPT_PREFIXES:
            if name.startswith(prefix):
                found.add(prefix)
                break
    return found


#: Cyrillic and Greek letters that look like Latin ones (simplified UTS #39).
_HOMOGLYPHS = str.maketrans({
    # Cyrillic lower case
    "а": "a", "е": "e", "о": "o", "р": "p", "с": "c", "у": "y", "х": "x", "і": "i",
    "ј": "j", "ѕ": "s", "ԁ": "d", "һ": "h", "ӏ": "l", "ԛ": "q", "ԝ": "w",
    # Cyrillic upper case
    "А": "A", "В": "B", "Е": "E", "К": "K", "М": "M", "Н": "H", "О": "O", "Р": "P",
    "С": "C", "Т": "T", "Х": "X", "І": "I", "Ј": "J", "Ѕ": "S", "Ԛ": "Q", "Ԝ": "W",
    "У": "Y",
    # Greek
    "ο": "o", "ν": "v", "Α": "A", "Β": "B", "Ε": "E", "Ζ": "Z", "Η": "H", "Ι": "I",
    "Κ": "K", "Μ": "M", "Ν": "N", "Ο": "O", "Ρ": "P", "Τ": "T", "Υ": "Y", "Χ": "X",
})


def skeleton(text: str) -> str:
    """Name with homoglyphs replaced by Latin letters (for confusable pairs)."""
    return nfkc(text).translate(_HOMOGLYPHS)
