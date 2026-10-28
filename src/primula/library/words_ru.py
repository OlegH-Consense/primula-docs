"""Numbers in words, Russian (standard library 4; decisions 97, 115).

The same model as :mod:`primula.library.words_uk`: six cases, gender of
the last word, scale nouns (тысяча — feminine, миллион, миллиард, триллион
— masculine), fractions («две целых пять десятых»), ordinals with the last
word inflected and compound round thousands («двухтысячный»).  «ё» is
written as «е», as is usual in business documents.
"""

from __future__ import annotations

from primula.library.words_uk import CASES, plural_class

_UNITS = {
    0: ("ноль", "ноля", "нолю", "ноль", "нолем", "ноле"),
    1: ("один", "одного", "одному", "один", "одним", "одном"),
    2: ("два", "двух", "двум", "два", "двумя", "двух"),
    3: ("три", "трех", "трем", "три", "тремя", "трех"),
    4: ("четыре", "четырех", "четырем", "четыре", "четырьмя", "четырех"),
    5: ("пять", "пяти", "пяти", "пять", "пятью", "пяти"),
    6: ("шесть", "шести", "шести", "шесть", "шестью", "шести"),
    7: ("семь", "семи", "семи", "семь", "семью", "семи"),
    8: ("восемь", "восьми", "восьми", "восемь", "восемью", "восьми"),
    9: ("девять", "девяти", "девяти", "девять", "девятью", "девяти"),
}
_ONE_F = ("одна", "одной", "одной", "одну", "одной", "одной")
_ONE_N = ("одно", "одного", "одному", "одно", "одним", "одном")
_TWO_F = ("две", "двух", "двум", "две", "двумя", "двух")


def _dtsat(word: str) -> tuple[str, ...]:
    """Numerals in -дцать/-десять: «одиннадцать», «двадцать», «десять»."""
    base = word[:-1]
    return (word, base + "и", base + "и", word, word + "ю", base + "и")


_TEENS = {n: _dtsat(w) for n, w in {
    10: "десять", 11: "одиннадцать", 12: "двенадцать", 13: "тринадцать", 14: "четырнадцать",
    15: "пятнадцать", 16: "шестнадцать", 17: "семнадцать", 18: "восемнадцать", 19: "девятнадцать"}.items()}
_TENS = {
    2: _dtsat("двадцать"), 3: _dtsat("тридцать"),
    4: ("сорок", "сорока", "сорока", "сорок", "сорока", "сорока"),
    5: ("пятьдесят", "пятидесяти", "пятидесяти", "пятьдесят", "пятьюдесятью", "пятидесяти"),
    6: ("шестьдесят", "шестидесяти", "шестидесяти", "шестьдесят", "шестьюдесятью", "шестидесяти"),
    7: ("семьдесят", "семидесяти", "семидесяти", "семьдесят", "семьюдесятью", "семидесяти"),
    8: ("восемьдесят", "восьмидесяти", "восьмидесяти", "восемьдесят", "восемьюдесятью", "восьмидесяти"),
    9: ("девяносто", "девяноста", "девяноста", "девяносто", "девяноста", "девяноста"),
}
_HUNDREDS = {
    1: ("сто", "ста", "ста", "сто", "ста", "ста"),
    2: ("двести", "двухсот", "двумстам", "двести", "двумястами", "двухстах"),
    3: ("триста", "трехсот", "тремстам", "триста", "тремястами", "трехстах"),
    4: ("четыреста", "четырехсот", "четыремстам", "четыреста", "четырьмястами", "четырехстах"),
    5: ("пятьсот", "пятисот", "пятистам", "пятьсот", "пятьюстами", "пятистах"),
    6: ("шестьсот", "шестисот", "шестистам", "шестьсот", "шестьюстами", "шестистах"),
    7: ("семьсот", "семисот", "семистам", "семьсот", "семьюстами", "семистах"),
    8: ("восемьсот", "восьмисот", "восьмистам", "восемьсот", "восемьюстами", "восьмистах"),
    9: ("девятьсот", "девятисот", "девятистам", "девятьсот", "девятьюстами", "девятистах"),
}


def _masculine(word: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Singular and plural of «миллион»-type nouns."""
    return ((word, word + "а", word + "у", word, word + "ом", word + "е"),
            (word + "ы", word + "ов", word + "ам", word + "ы", word + "ами", word + "ах"))


_SCALES = [
    (10 ** 12, "m", *_masculine("триллион")),
    (10 ** 9, "m", *_masculine("миллиард")),
    (10 ** 6, "m", *_masculine("миллион")),
    (10 ** 3, "f", ("тысяча", "тысячи", "тысяче", "тысячу", "тысячей", "тысяче"),
     ("тысячи", "тысяч", "тысячам", "тысячи", "тысячами", "тысячах")),
]

MINUS = "минус"


def noun_form(n: int, case: str, singular: tuple[str, ...], plural: tuple[str, ...]) -> str:
    """The form of a noun counted by ``n`` in ``case``."""
    index = CASES.index(case)
    kind = plural_class(n)
    if kind == 0:
        return singular[index]
    if case in ("nom", "acc"):
        return singular[1] if kind == 1 else plural[1]  # «две тысячи», «пять тысяч»
    return plural[index]


def _triple(n: int, case: str, gender: str) -> list[str]:
    index = CASES.index(case)
    out: list[str] = []
    hundreds, rest = divmod(n, 100)
    if hundreds:
        out.append(_HUNDREDS[hundreds][index])
    if 10 <= rest <= 19:
        out.append(_TEENS[rest][index])
        return out
    tens, units = divmod(rest, 10)
    if tens:
        out.append(_TENS[tens][index])
    if units:
        if units == 1 and gender == "f":
            out.append(_ONE_F[index])
        elif units == 1 and gender == "n":
            out.append(_ONE_N[index])
        elif units == 2 and gender == "f":
            out.append(_TWO_F[index])
        else:
            out.append(_UNITS[units][index])
    return out


def cardinal(n: int, case: str = "nom", gender: str = "m") -> str:
    """An integer 0 ≤ n < 10¹⁵ in words."""
    if n == 0:
        return _UNITS[0][CASES.index(case)]
    out: list[str] = []
    rest = n
    for scale, scale_gender, singular, plural in _SCALES:
        count, rest = divmod(rest, scale)
        if count:
            out += _triple(count, case, scale_gender)
            out.append(noun_form(count, case, singular, plural))
    if rest:
        out += _triple(rest, case, gender)
    return " ".join(out)


# --- fractions -------------------------------------------------------------------------------

_WHOLE = (("целая", "целой", "целой", "целую", "целой", "целой"),
          ("целых", "целых", "целым", "целых", "целыми", "целых"))
_DENOMINATORS = {1: "десят", 2: "сот", 3: "тысячн", 4: "десятитысячн", 5: "стотысячн", 6: "миллионн"}
_ADJ_F = ("ая", "ой", "ой", "ую", "ой", "ой")
_ADJ_PL = ("ых", "ых", "ым", "ых", "ыми", "ых")


def _feminine_count(n: int, case: str, forms: tuple[tuple[str, ...], tuple[str, ...]]) -> str:
    singular, plural = forms
    index = CASES.index(case)
    word = singular[index] if plural_class(n) == 0 else plural[index]
    return cardinal(n, case, "f") + " " + word


def fraction(whole: int, numerator: int, places: int, case: str = "nom") -> str:
    """«две целых пять десятых»."""
    stem = _DENOMINATORS[places]
    denominator = (tuple(stem + e for e in _ADJ_F), tuple(stem + e for e in _ADJ_PL))
    return _feminine_count(whole, case, _WHOLE) + " " + _feminine_count(numerator, case, denominator)


# --- ordinals ---------------------------------------------------------------------------------

# Stem and adjective type: "y" (-ый), "o" (-ой, stressed ending), "soft" (третий).
_ORD_UNITS = {1: ("перв", "y"), 2: ("втор", "o"), 3: ("трет", "soft"), 4: ("четверт", "y"), 5: ("пят", "y"),
              6: ("шест", "o"), 7: ("седьм", "o"), 8: ("восьм", "o"), 9: ("девят", "y")}
_ORD_TEENS = {10: "десят", 11: "одиннадцат", 12: "двенадцат", 13: "тринадцат", 14: "четырнадцат", 15: "пятнадцат",
              16: "шестнадцат", 17: "семнадцат", 18: "восемнадцат", 19: "девятнадцат"}
_ORD_TENS = {2: ("двадцат", "y"), 3: ("тридцат", "y"), 4: ("сороков", "o"), 5: ("пятидесят", "y"),
             6: ("шестидесят", "y"), 7: ("семидесят", "y"), 8: ("восьмидесят", "y"), 9: ("девяност", "y")}
_ORD_HUNDREDS = {1: "сот", 2: "двухсот", 3: "трехсот", 4: "четырехсот", 5: "пятисот", 6: "шестисот", 7: "семисот",
                 8: "восьмисот", 9: "девятисот"}
_ORD_SCALES = {10 ** 3: "тысячн", 10 ** 6: "миллионн", 10 ** 9: "миллиардн", 10 ** 12: "триллионн"}

_ENDINGS = {
    "y": {"m": ("ый", "ого", "ому", "ый", "ым", "ом"), "f": ("ая", "ой", "ой", "ую", "ой", "ой"),
          "n": ("ое", "ого", "ому", "ое", "ым", "ом")},
    "o": {"m": ("ой", "ого", "ому", "ой", "ым", "ом"), "f": ("ая", "ой", "ой", "ую", "ой", "ой"),
          "n": ("ое", "ого", "ому", "ое", "ым", "ом")},
    "soft": {"m": ("ий", "ьего", "ьему", "ий", "ьим", "ьем"), "f": ("ья", "ьей", "ьей", "ью", "ьей", "ьей"),
             "n": ("ье", "ьего", "ьему", "ье", "ьим", "ьем")},
}
_COMBINING_UNITS = {1: "одно", 2: "двух", 3: "трех", 4: "четырех"}


def _adjective(stem: str, kind: str, case: str, gender: str) -> str:
    return stem + _ENDINGS[kind][gender][CASES.index(case)]


def _combining(n: int) -> str:
    """First part of a compound ordinal: «двух», «пяти», «двадцатипяти», «двухсот»."""
    parts: list[str] = []
    hundreds, rest = divmod(n, 100)
    if hundreds:
        parts.append("сто" if hundreds == 1 else _HUNDREDS[hundreds][1])
    if 10 <= rest <= 19:
        parts.append(_TEENS[rest][1])
    else:
        tens, units = divmod(rest, 10)
        if tens:
            parts.append(_TENS[tens][1])
        if units:
            parts.append(_COMBINING_UNITS.get(units, _UNITS[units][1]))
    return "".join(parts)


def ordinal(n: int, case: str = "nom", gender: str = "m") -> str:
    """An ordinal 1 ≤ n < 10¹⁵: «двадцать первый», «двухтысячный»."""
    for scale in sorted(_ORD_SCALES, reverse=True):
        if n % scale == 0:
            head, count = divmod(n // scale, 1000)
            words = [cardinal(head * scale * 1000)] if head else []
            prefix = "" if count == 1 else _combining(count)
            return " ".join(words + [_adjective(prefix + _ORD_SCALES[scale], "y", case, gender)])
    head, last = divmod(n, 100)
    words = [cardinal(head * 100)] if head else []
    if last == 0:
        hundreds = (n // 100) % 10
        words = [cardinal(n - hundreds * 100)] if n - hundreds * 100 else []
        return " ".join(words + [_adjective(_ORD_HUNDREDS[hundreds], "y", case, gender)])
    if 10 <= last <= 19:
        stem, kind = _ORD_TEENS[last], "y"
    else:
        tens, units = divmod(last, 10)
        if units == 0:
            stem, kind = _ORD_TENS[tens]
        else:
            if tens:
                words.append(_TENS[tens][0])
            stem, kind = _ORD_UNITS[units]
    return " ".join(words + [_adjective(stem, kind, case, gender)])


def date_words(day: int, month_gen: str, year: int) -> str:
    """«двенадцатого октября две тысячи двадцать шестого года»."""
    return f"{ordinal(day, 'gen', 'n')} {month_gen} {ordinal(year, 'gen', 'm')} года"
