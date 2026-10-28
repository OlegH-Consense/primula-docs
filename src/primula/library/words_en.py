"""Numbers in words, English (standard library 4; decision 115).

Gender and case do not apply.  Compound numbers are hyphenated
(«twenty-one»), no «and» after hundreds («one hundred twenty-one», as in
«two thousand twenty-six» of ``date_words``).  Fractions are read digit
by digit after «point» («two point zero five»).
"""

from __future__ import annotations

_UNITS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven",
          "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen"]
_TENS = {2: "twenty", 3: "thirty", 4: "forty", 5: "fifty", 6: "sixty", 7: "seventy", 8: "eighty", 9: "ninety"}
_SCALES = [(10 ** 12, "trillion"), (10 ** 9, "billion"), (10 ** 6, "million"), (10 ** 3, "thousand")]
_ORD = {"one": "first", "two": "second", "three": "third", "five": "fifth", "eight": "eighth", "nine": "ninth",
        "twelve": "twelfth"}

MINUS = "minus"


def _triple(n: int) -> list[str]:
    out: list[str] = []
    hundreds, rest = divmod(n, 100)
    if hundreds:
        out += [_UNITS[hundreds], "hundred"]
    if rest:
        if rest < 20:
            out.append(_UNITS[rest])
        else:
            tens, units = divmod(rest, 10)
            out.append(_TENS[tens] + ("-" + _UNITS[units] if units else ""))
    return out


def cardinal(n: int, case: str = "nom", gender: str = "m") -> str:
    """An integer 0 ≤ n < 10¹⁵ in words (``case`` and ``gender`` are ignored)."""
    if n == 0:
        return "zero"
    out: list[str] = []
    rest = n
    for scale, name in _SCALES:
        count, rest = divmod(rest, scale)
        if count:
            out += _triple(count) + [name]
    if rest:
        out += _triple(rest)
    return " ".join(out)


def fraction_digits(whole: int, digits: str) -> str:
    """«two point five», «two point zero five»."""
    return cardinal(whole) + " point " + " ".join(_UNITS[int(d)] for d in digits)


def _ordinal_word(word: str) -> str:
    """The ordinal of the last word: «one» → «first», «twenty» → «twentieth»."""
    if "-" in word:
        head, last = word.rsplit("-", 1)
        return head + "-" + _ordinal_word(last)
    if word in _ORD:
        return _ORD[word]
    if word.endswith("y"):
        return word[:-1] + "ieth"
    return word + "th"


def ordinal(n: int, case: str = "nom", gender: str = "m") -> str:
    """«twenty-first», «two thousandth»."""
    words = cardinal(n).split(" ")
    words[-1] = _ordinal_word(words[-1])
    return " ".join(words)


def date_words(day: int, month: str, year: int) -> str:
    """«the twelfth of October, two thousand twenty-six»."""
    return f"the {ordinal(day)} of {month}, {cardinal(year)}"
