"""Text functions of the first part of stage 13.9 (library 7; decision 115).

``plural(n, one, few, many, frac=None)`` — the form by number (uk, ru:
1 / 2–4 / 5+; en: 1 / many); a fractional ``n`` takes ``frac`` (genitive
singular: «2,5 дня»), without it — an error in uk and ru, the plural in
en; a zero fractional part counts as an integer.

``join_list(items, last=None, sep=", ")`` — «А, Б та В»; the default
conjunction: uk «і», ru «и», en «and» (no Oxford comma).

``cap(s)`` — a capital first letter, the rest unchanged.

``translit(s)`` — romanisation by the language: uk — Resolution of the
Cabinet of Ministers of Ukraine No. 55 of 27.01.2010 (word-initial «є ї й
ю я» → «ye yi y yu ya», elsewhere «ie i i iu ia»; «зг» → «zgh»; «ь» and
the apostrophe are dropped); ru — ICAO Doc 9303 (as in passports); en —
unchanged.  Characters outside the table are kept; the case follows the
source: «Щука» → «Shchuka», «ЩУКА» → «SHCHUKA».

``sort_key(s)`` — a key for ``sorted(names, key=sort_key)`` by the
alphabet of the language: letters of the alphabet in its order without
regard to case (then lower case before upper case as a tie-break), the
apostrophe and the hyphen ignored at the first level; spaces before any
letter, then digits, letters of the alphabet, other letters by code point.

``nbsp_short(s)`` — a no-break space after the short words of
``typography(nbsp_words=…)`` or the defaults of the language («у
власність»).  Applying it to the whole document
(``typography(nbsp_short=True)``) is stage 13.9d.
"""

from __future__ import annotations

import re
from typing import Any

from primula.library import words_uk
from primula.library.context import NBSP, Library, keywords, lib_error, number, positional, string, to_decimal

_AND = {"uk": "і", "ru": "и", "en": "and"}


def plural(lib: Library, args: list[Any], kwargs: dict[str, Any], span: Any) -> str:
    """``plural(n, "день", "дні", "днів", frac="дня")``."""
    keywords("plural", kwargs, ("frac", "lang"), span)
    lang = lib.lang(kwargs.get("lang"), span)
    expected = 2 if lang == "en" else 3
    if len(args) != expected + 1:
        raise lib_error("P2722", span, None, function="plural", count=expected, lang=lang, given=len(args) - 1)
    value = number("plural", "n", args[0], span)
    forms = [string("plural", "forms", form, span) for form in args[1:]]
    exact = to_decimal(value)
    if exact != exact.to_integral_value():
        if lang == "en":
            return forms[1]
        frac = kwargs.get("frac")
        if frac is None:
            raise lib_error("P2716", span, "help.lib_plural_frac")
        return string("plural", "frac", frac, span)
    n = int(exact)
    if lang == "en":
        return forms[0] if abs(n) == 1 else forms[1]
    return forms[words_uk.plural_class(n)]


def join_list(lib: Library, args: list[Any], kwargs: dict[str, Any], span: Any) -> str:
    """``join_list(["А", "Б", "В"], last="та")`` — «А, Б та В»."""
    positional("join_list", args, 1, 1, span)
    keywords("join_list", kwargs, ("last", "sep", "lang"), span)
    items = args[0]
    if not isinstance(items, (list, tuple)):
        from primula.library.context import expect

        expect("join_list", "items", items, False, "sequence", span)
    texts = [string("join_list", "items", item, span) for item in items]
    sep = string("join_list", "sep", kwargs.get("sep", ", "), span)
    last = kwargs.get("last")
    last = _AND[lib.lang(kwargs.get("lang"), span)] if last is None else string("join_list", "last", last, span)
    if len(texts) <= 1:
        return "".join(texts)
    return sep.join(texts[:-1]) + " " + last + " " + texts[-1]


def cap(lib: Library, args: list[Any], kwargs: dict[str, Any], span: Any) -> str:
    """``cap(s)``: a capital first letter."""
    positional("cap", args, 1, 1, span)
    keywords("cap", kwargs, (), span)
    text = string("cap", "s", args[0], span)
    return text[:1].upper() + text[1:]



# --- translit -----------------------------------------------------------------------------------

# КМУ № 55 (27.01.2010): (anywhere, word-initial).
_UK = {"а": "a", "б": "b", "в": "v", "г": "h", "ґ": "g", "д": "d", "е": "e", "є": ("ie", "ye"), "ж": "zh",
       "з": "z", "и": "y", "і": "i", "ї": ("i", "yi"), "й": ("i", "y"), "к": "k", "л": "l", "м": "m", "н": "n",
       "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u", "ф": "f", "х": "kh", "ц": "ts", "ч": "ch",
       "ш": "sh", "щ": "shch", "ь": "", "ю": ("iu", "yu"), "я": ("ia", "ya"), "'": "", "ʼ": "", "’": ""}
# ICAO Doc 9303, 7th edition.
_RU = {"а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e", "ж": "zh", "з": "z", "и": "i",
       "й": "i", "к": "k", "л": "l", "м": "m", "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t",
       "у": "u", "ф": "f", "х": "kh", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "shch", "ъ": "ie", "ы": "y", "ь": "",
       "э": "e", "ю": "iu", "я": "ia"}


def _romanize(text: str, table: dict[str, Any], initial_forms: bool) -> str:
    out: list[str] = []
    for i, char in enumerate(text):
        lower = char.lower()
        if lower not in table:
            out.append(char)
            continue
        if initial_forms and lower == "г" and i > 0 and text[i - 1].lower() == "з":
            mapped = "gh"  # «зг» → «zgh»
        else:
            mapped = table[lower]
            if isinstance(mapped, tuple):
                previous = text[i - 1] if i > 0 else ""
                initial = previous == "" or (not previous.isalpha() and previous not in "'ʼ’")
                mapped = mapped[1] if initial else mapped[0]
        if char != lower and mapped:
            # Upper case: the whole word in capitals → all capitals, else the first letter.
            neighbours = text[i + 1:i + 2] + text[i - 1:i] if i > 0 else text[i + 1:i + 2]
            if any(c.isalpha() and c.isupper() for c in neighbours):
                mapped = mapped.upper()
            else:
                mapped = mapped[0].upper() + mapped[1:]
        out.append(mapped)
    return "".join(out)


def translit(lib: Library, args: list[Any], kwargs: dict[str, Any], span: Any) -> str:
    """``translit(s, lang=None)``."""
    positional("translit", args, 1, 1, span)
    keywords("translit", kwargs, ("lang",), span)
    text = string("translit", "s", args[0], span)
    lang = lib.lang(kwargs.get("lang"), span)
    if lang == "uk":
        return _romanize(text, _UK, True)
    if lang == "ru":
        return _romanize(text, _RU, False)
    return text


# --- sort_key -------------------------------------------------------------------------------------

_ALPHABETS = {
    "uk": "абвгґдеєжзиіїйклмнопрстуфхцчшщьюя",
    "ru": "абвгдеёжзийклмнопрстуфхцчшщъыьэюя",
    "en": "abcdefghijklmnopqrstuvwxyz",
}
_IGNORED = "'ʼ’-‐"


def sort_key(lib: Library, args: list[Any], kwargs: dict[str, Any], span: Any) -> tuple:
    """``sort_key(s, lang=None)``: a tuple comparable with ``<``."""
    positional("sort_key", args, 1, 1, span)
    keywords("sort_key", kwargs, ("lang",), span)
    text = string("sort_key", "s", args[0], span)
    return sort_key_of(text, lib.lang(kwargs.get("lang"), span))


def sort_key_of(text: str, lang: str) -> tuple:
    """The sort key of ``text`` by the alphabet of ``lang`` (uk, ru, en); see :func:`sort_key`."""
    alphabet = _ALPHABETS[lang if lang in _ALPHABETS else "en"]
    primary: list[int] = []
    for char in text:
        lower = char.lower()
        if char in _IGNORED:
            continue
        if char.isspace():
            primary.append(0)
        elif char.isdigit():
            primary.append(10 + int(char) if char.isascii() else 20)
        elif lower in alphabet:
            primary.append(100 + alphabet.index(lower))
        elif char.isalpha():
            primary.append(1000 + ord(lower))
        else:
            primary.append(1 + min(ord(char), 8))
    # Tie-break: lower case before upper case, then the text itself.
    case = tuple(1 if c.isupper() else 0 for c in text if c not in _IGNORED)
    return (tuple(primary), case, text)


# --- nbsp_short -----------------------------------------------------------------------------------

SHORT_WORDS = {
    "uk": ["а", "в", "є", "і", "й", "о", "у", "з", "зі", "із", "та", "до", "на", "по", "за", "не", "ні", "що",
           "як", "від"],
    "ru": ["а", "в", "и", "к", "о", "с", "у", "во", "за", "из", "на", "не", "ни", "по", "со", "то", "что", "как",
           "от", "до"],
    "en": ["a", "an", "the", "of", "to", "in", "on", "at", "by", "or"],
}


def short_words(lib: Library, lang: str) -> list[str]:
    """The short words: ``typography(nbsp_words=…)`` or the defaults of the language (library 7)."""
    words = lib.typography().get("nbsp_words")
    return [str(w) for w in words] if isinstance(words, (list, tuple)) and words else SHORT_WORDS[lang]


def apply_nbsp(text: str, words: list[str]) -> str:
    """Replace the space after a short word by a no-break space (case-insensitive, whole words)."""
    if not words:
        return text
    pattern = r"(?<![\w'ʼ’-])(" + "|".join(re.escape(w) for w in sorted(words, key=len, reverse=True)) + r") +(?=\S)"
    return re.sub(pattern, lambda m: m.group(1) + NBSP, text, flags=re.IGNORECASE)


def nbsp_short(lib: Library, args: list[Any], kwargs: dict[str, Any], span: Any) -> str:
    """``nbsp_short(s, lang=None)``."""
    positional("nbsp_short", args, 1, 1, span)
    keywords("nbsp_short", kwargs, ("lang",), span)
    text = string("nbsp_short", "s", args[0], span)
    return apply_nbsp(text, short_words(lib, lib.lang(kwargs.get("lang"), span)))


FUNCTIONS = {"plural": plural, "join_list": join_list, "cap": cap, "translit": translit, "sort_key": sort_key,
             "nbsp_short": nbsp_short}
