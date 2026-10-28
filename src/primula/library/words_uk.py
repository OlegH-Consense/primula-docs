"""Numbers in words, Ukrainian (standard library 4; decisions 97, 115).

Cardinal numbers decline in six cases (``nom gen dat acc ins loc``) and
agree in gender (``m f n``) in the last word: «один», «одна», «одне»,
«два»/«дві».  Scale words (тисяча — feminine, мільйон, мільярд, трильйон —
masculine) take the form the preceding number requires: «одна тисяча»,
«дві тисячі», «п'ять тисяч»; in the oblique cases the plural noun takes the
case of the numeral («двох тисяч»).  The accusative is that of inanimate
nouns (equal to the nominative, except feminine «одну»).

Fractions (``words(2.5)``): «дві цілих п'ять десятих»; numerator and the
word «ціла» are feminine; all parts decline.

Ordinal numbers: only the last word is an ordinal adjective («дві тисячі
двадцять шостий»); round thousands and millions form one compound word
(«двотисячний», «двадцятип'ятитисячний»).  The compound forms follow the
library document (decision 115) and are to be checked against Правопис
2019.

Apostrophe: U+0027, as in the specification («п'ять»).
"""

from __future__ import annotations

CASES = ("nom", "gen", "dat", "acc", "ins", "loc")

# Units 0-9: masculine forms; 1 and 2 have gender variants below.
_UNITS = {
    0: ("нуль", "нуля", "нулю", "нуль", "нулем", "нулі"),
    1: ("один", "одного", "одному", "один", "одним", "одному"),
    2: ("два", "двох", "двом", "два", "двома", "двох"),
    3: ("три", "трьох", "трьом", "три", "трьома", "трьох"),
    4: ("чотири", "чотирьох", "чотирьом", "чотири", "чотирма", "чотирьох"),
    5: ("п'ять", "п'яти", "п'яти", "п'ять", "п'ятьма", "п'яти"),
    6: ("шість", "шести", "шести", "шість", "шістьма", "шести"),
    7: ("сім", "семи", "семи", "сім", "сьома", "семи"),
    8: ("вісім", "восьми", "восьми", "вісім", "вісьма", "восьми"),
    9: ("дев'ять", "дев'яти", "дев'яти", "дев'ять", "дев'ятьма", "дев'яти"),
}
_ONE_F = ("одна", "однієї", "одній", "одну", "однією", "одній")
_ONE_N = ("одне", "одного", "одному", "одне", "одним", "одному")
_TWO_F = ("дві", "двох", "двом", "дві", "двома", "двох")


def _tsiat(stem: str) -> tuple[str, ...]:
    """Numerals in -ять/-цять: «одинадцять», «двадцять»."""
    base = stem[:-1]  # without the soft sign
    return (stem, base + "и", base + "и", stem, stem + "ма", base + "и")


_TEENS = {n: _tsiat(w) for n, w in {
    10: "десять", 11: "одинадцять", 12: "дванадцять", 13: "тринадцять", 14: "чотирнадцять",
    15: "п'ятнадцять", 16: "шістнадцять", 17: "сімнадцять", 18: "вісімнадцять", 19: "дев'ятнадцять"}.items()}
_TENS = {
    2: _tsiat("двадцять"), 3: _tsiat("тридцять"),
    4: ("сорок", "сорока", "сорока", "сорок", "сорока", "сорока"),
    5: ("п'ятдесят", "п'ятдесяти", "п'ятдесяти", "п'ятдесят", "п'ятдесятьма", "п'ятдесяти"),
    6: ("шістдесят", "шістдесяти", "шістдесяти", "шістдесят", "шістдесятьма", "шістдесяти"),
    7: ("сімдесят", "сімдесяти", "сімдесяти", "сімдесят", "сімдесятьма", "сімдесяти"),
    8: ("вісімдесят", "вісімдесяти", "вісімдесяти", "вісімдесят", "вісімдесятьма", "вісімдесяти"),
    9: ("дев'яносто", "дев'яноста", "дев'яноста", "дев'яносто", "дев'яноста", "дев'яноста"),
}
_HUNDREDS = {
    1: ("сто", "ста", "ста", "сто", "ста", "ста"),
    2: ("двісті", "двохсот", "двомстам", "двісті", "двомастами", "двохстах"),
    3: ("триста", "трьохсот", "трьомстам", "триста", "трьомастами", "трьохстах"),
    4: ("чотириста", "чотирьохсот", "чотирьомстам", "чотириста", "чотирмастами", "чотирьохстах"),
    5: ("п'ятсот", "п'ятисот", "п'ятистам", "п'ятсот", "п'ятьмастами", "п'ятистах"),
    6: ("шістсот", "шестисот", "шестистам", "шістсот", "шістьмастами", "шестистах"),
    7: ("сімсот", "семисот", "семистам", "сімсот", "сьомастами", "семистах"),
    8: ("вісімсот", "восьмисот", "восьмистам", "вісімсот", "вісьмастами", "восьмистах"),
    9: ("дев'ятсот", "дев'ятисот", "дев'ятистам", "дев'ятсот", "дев'ятьмастами", "дев'ятистах"),
}

# Scale nouns: (gender, singular by case, plural by case).
_SCALES = [
    (10 ** 12, "m", ("трильйон", "трильйона", "трильйону", "трильйон", "трильйоном", "трильйоні"),
     ("трильйони", "трильйонів", "трильйонам", "трильйони", "трильйонами", "трильйонах")),
    (10 ** 9, "m", ("мільярд", "мільярда", "мільярду", "мільярд", "мільярдом", "мільярді"),
     ("мільярди", "мільярдів", "мільярдам", "мільярди", "мільярдами", "мільярдах")),
    (10 ** 6, "m", ("мільйон", "мільйона", "мільйону", "мільйон", "мільйоном", "мільйоні"),
     ("мільйони", "мільйонів", "мільйонам", "мільйони", "мільйонами", "мільйонах")),
    (10 ** 3, "f", ("тисяча", "тисячі", "тисячі", "тисячу", "тисячею", "тисячі"),
     ("тисячі", "тисяч", "тисячам", "тисячі", "тисячами", "тисячах")),
]

MINUS = "мінус"


def plural_class(n: int) -> int:
    """Agreement class of an integer: 0 — «один», 1 — «два-чотири», 2 — «п'ять» and 0."""
    n = abs(n)
    if n % 10 == 1 and n % 100 != 11:
        return 0
    if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14:
        return 1
    return 2


def noun_form(n: int, case: str, singular: tuple[str, ...], plural: tuple[str, ...]) -> str:
    """The form of a noun counted by ``n`` in ``case`` (nominative: 1 / 2-4 / 5+)."""
    index = CASES.index(case)
    kind = plural_class(n)
    if kind == 0:
        return singular[index]
    if case in ("nom", "acc"):
        return plural[0] if kind == 1 else plural[1]
    return plural[index]


def _triple(n: int, case: str, gender: str) -> list[str]:
    """Words of 1..999 in a case and gender."""
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

_WHOLE = (("ціла", "цілої", "цілій", "цілу", "цілою", "цілій"), ("цілих", "цілих", "цілим", "цілих", "цілими", "цілих"))
_DENOMINATORS = {1: "десят", 2: "сот", 3: "тисячн", 4: "десятитисячн", 5: "стотисячн", 6: "мільйонн"}
_ADJ_F = ("а", "ої", "ій", "у", "ою", "ій")
_ADJ_PL = ("их", "их", "им", "их", "ими", "их")


def _feminine_count(n: int, case: str, stem_or_forms: tuple[tuple[str, ...], tuple[str, ...]]) -> str:
    """«одна ціла», «дві цілих» … with the counted word after a feminine numeral."""
    singular, plural = stem_or_forms
    index = CASES.index(case)
    word = singular[index] if plural_class(n) == 0 else plural[index]
    return cardinal(n, case, "f") + " " + word


def fraction(whole: int, numerator: int, places: int, case: str = "nom") -> str:
    """«дві цілих п'ять десятих»: the whole part, then the numerator over 10^places."""
    stem = _DENOMINATORS[places]
    denominator = (tuple(stem + e for e in _ADJ_F), tuple(stem + e for e in _ADJ_PL))
    return _feminine_count(whole, case, _WHOLE) + " " + _feminine_count(numerator, case, denominator)


# --- ordinals ---------------------------------------------------------------------------------

# Ordinal stems with the adjective type: "hard" (-ий) or "soft" (третій).
_ORD_UNITS = {1: "перш", 2: "друг", 3: "трет", 4: "четверт", 5: "п'ят", 6: "шост", 7: "сьом", 8: "восьм", 9: "дев'ят"}
_ORD_TEENS = {10: "десят", 11: "одинадцят", 12: "дванадцят", 13: "тринадцят", 14: "чотирнадцят", 15: "п'ятнадцят",
              16: "шістнадцят", 17: "сімнадцят", 18: "вісімнадцят", 19: "дев'ятнадцят"}
_ORD_TENS = {2: "двадцят", 3: "тридцят", 4: "сорок", 5: "п'ятдесят", 6: "шістдесят", 7: "сімдесят", 8: "вісімдесят",
             9: "дев'яност"}
_ORD_HUNDREDS = {1: "сот", 2: "двохсот", 3: "трьохсот", 4: "чотирьохсот", 5: "п'ятисот", 6: "шестисот", 7: "семисот",
                 8: "восьмисот", 9: "дев'ятисот"}
_ORD_SCALES = {10 ** 3: "тисячн", 10 ** 6: "мільйонн", 10 ** 9: "мільярдн", 10 ** 12: "трильйонн"}

_HARD = {"m": ("ий", "ого", "ому", "ий", "им", "ому"), "f": ("а", "ої", "ій", "у", "ою", "ій"),
         "n": ("е", "ого", "ому", "е", "им", "ому")}
_SOFT = {"m": ("ій", "ього", "ьому", "ій", "ім", "ьому"), "f": ("я", "ьої", "ій", "ю", "ьою", "ій"),
         "n": ("є", "ього", "ьому", "є", "ім", "ьому")}
# «сороковий»: the stem gets -ов-.
_SPECIAL_STEMS = {"сорок": "сороков"}

# First parts of compound ordinals: «дво|тисячний», «п'яти|тисячний» (decision 115).
_COMBINING_UNITS = {1: "одно", 2: "дво", 3: "три", 4: "чотири"}


def _adjective(stem: str, case: str, gender: str) -> str:
    endings = _SOFT if stem == "трет" else _HARD
    stem = _SPECIAL_STEMS.get(stem, stem)
    return stem + endings[gender][CASES.index(case)]


def _combining(n: int) -> str:
    """First part of a compound ordinal for 1..999: «дво», «п'яти», «двадцятип'яти», «двохсот»."""
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
    """An ordinal 1 ≤ n < 10¹⁵: «двадцять перший», «двотисячний»."""
    for scale in sorted(_ORD_SCALES, reverse=True):
        if n % scale == 0:
            head, count = divmod(n // scale, 1000)
            words = [cardinal(head * scale * 1000)] if head else []
            prefix = "" if count == 1 else _combining(count)
            return " ".join(words + [_adjective(prefix + _ORD_SCALES[scale], case, gender)])
    head, last = divmod(n, 100)
    words = [cardinal(head * 100)] if head else []
    if last == 0:
        hundreds = (n // 100) % 10
        words = [cardinal(n - hundreds * 100)] if n - hundreds * 100 else []
        return " ".join(words + [_adjective(_ORD_HUNDREDS[hundreds], case, gender)])
    if last >= 10 and last <= 19:
        stem = _ORD_TEENS[last]
    else:
        tens, units = divmod(last, 10)
        if units == 0:
            stem = _ORD_TENS[tens]
        else:
            if tens:
                words.append(_TENS[tens][0])
            stem = _ORD_UNITS[units]
    return " ".join(words + [_adjective(stem, case, gender)])


# --- dates ------------------------------------------------------------------------------------

def date_words(day: int, month_gen: str, year: int) -> str:
    """«дванадцятого жовтня дві тисячі двадцять шостого року»."""
    return f"{ordinal(day, 'gen', 'n')} {month_gen} {ordinal(year, 'gen', 'm')} року"
