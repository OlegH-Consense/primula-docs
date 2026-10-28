"""Numbers (library 2) and numbers in words (library 4).

``num``, ``percent``, ``round_to``, ``ceil_to``, ``floor_to``,
``round_money``; ``words``, ``ordinal``, ``date_words``.

Output rules: groups of three digits by a no-break space and a decimal
comma (uk, ru), a comma and a point (en); the minus is U+2212 for all
languages (decision 115); ``digits=None`` keeps the places of the value
(a ``float`` — its shortest decimal form).
"""

from __future__ import annotations

import decimal
from decimal import Decimal
from typing import Any

from primula.core.values import DateTime
from primula.library import localefmt, words_en, words_ru, words_uk
from primula.library.context import (
    lib_error,
    CASES, GENDERS, NBSP, Library, choice, integer, is_number, keywords, moment, number, positional,
    to_decimal,
)

_WORDS = {"uk": words_uk, "ru": words_ru, "en": words_en}
#: The largest integer part in words (library 4).
WORDS_LIMIT = 10 ** 15
#: The longest fractional part in words.
WORDS_PLACES = 6


def format_number(value: Any, digits: int | None, lang: str) -> str:
    """«12 500,00», «−1 500»; see :func:`localefmt.format_number`."""
    return localefmt.format_number(value, digits, lang)


def same_type(template: Any, value: Decimal) -> Any:
    """A result of the type of ``template``: ``float`` stays ``float``, an integral ``decimal`` — ``int``."""
    if isinstance(template, float):
        return float(value)
    if value == value.to_integral_value() and value.as_tuple().exponent >= 0:
        return int(value)
    return value


# --- functions --------------------------------------------------------------------------------------

def num(lib: Library, args: list[Any], kwargs: dict[str, Any], span: Any) -> str:
    """``num(x, digits=None, lang=None)``."""
    positional("num", args, 1, 2, span)
    keywords("num", kwargs, ("digits", "lang"), span)
    value = number("num", "x", args[0], span)
    digits = kwargs.get("digits", args[1] if len(args) > 1 else None)
    if digits is not None:
        digits = integer("num", "digits", digits, span)
    return format_number(value, digits, lib.lang(kwargs.get("lang"), span))


def percent(lib: Library, args: list[Any], kwargs: dict[str, Any], span: Any) -> str:
    """``percent(x, digits=None)``: «20 %»; ``typography(percent_space=False)`` — «20%»."""
    positional("percent", args, 1, 2, span)
    keywords("percent", kwargs, ("digits", "lang"), span)
    value = number("percent", "x", args[0], span)
    digits = kwargs.get("digits", args[1] if len(args) > 1 else None)
    if digits is not None:
        digits = integer("percent", "digits", digits, span)
    text = format_number(value, digits, lib.lang(kwargs.get("lang"), span))
    return text + (NBSP if lib.typography().get("percent_space", True) else "") + "%"


def _to_step(name: str, rounding: str):
    def impl(lib: Library, args: list[Any], kwargs: dict[str, Any], span: Any) -> Any:
        positional(name, args, 2, 2, span)
        keywords(name, kwargs, (), span)
        value = number(name, "x", args[0], span)
        step = to_decimal(number(name, "step", args[1], span))
        if step <= 0:
            raise lib_error("P2717", span, None, function=name)
        count = (to_decimal(value) / step).to_integral_value(rounding=rounding)
        result = count * step
        return same_type(value, result)
    return impl


round_to = _to_step("round_to", decimal.ROUND_HALF_UP)
ceil_to = _to_step("ceil_to", decimal.ROUND_CEILING)
floor_to = _to_step("floor_to", decimal.ROUND_FLOOR)


def money_round(value: Any) -> Decimal:
    """Round to kopecks, half away from zero (library 3)."""
    return to_decimal(value).quantize(Decimal("0.01"), rounding=decimal.ROUND_HALF_UP)


def round_money(lib: Library, args: list[Any], kwargs: dict[str, Any], span: Any) -> Decimal:
    """``round_money(x)``: kopecks, half away from zero; ``float`` is P2703."""
    from primula.library.context import exact

    positional("round_money", args, 1, 1, span)
    keywords("round_money", kwargs, (), span)
    return money_round(exact("round_money", "x", args[0], span))


# --- words ------------------------------------------------------------------------------------------

def number_words(value: Any, lang: str, case: str, gender: str, span: Any, function: str = "words") -> str:
    """A number in words: integers, fractions (decision 115), «мінус»."""
    module = _WORDS[lang]
    exact = to_decimal(value)
    sign = ""
    if exact < 0:
        sign, exact = module.MINUS + " ", -exact
    whole = int(exact)
    if whole >= WORDS_LIMIT:
        raise lib_error("P2704", span, None, function=function, value=str(value), range="0 … 10¹⁵ − 1")
    fraction_part = exact - whole
    if fraction_part == 0:
        return sign + module.cardinal(whole, case, gender)
    # The scale of the value (2.50 → «п'ятдесят сотих»); for float — shortest repr.
    exponent = exact.as_tuple().exponent
    places = -exponent if isinstance(exponent, int) else 0
    if places > WORDS_PLACES:
        trimmed = exact.normalize()
        places = -trimmed.as_tuple().exponent
        if places > WORDS_PLACES:
            raise lib_error("P2723", span, None, function=function, places=WORDS_PLACES)
    digits = str(fraction_part.scaleb(places).to_integral_value()).zfill(places)
    if lang == "en":
        return sign + words_en.fraction_digits(whole, digits)
    return sign + module.fraction(whole, int(digits), places, case)


def words(lib: Library, args: list[Any], kwargs: dict[str, Any], span: Any) -> str:
    """``words(x, gender="m", case="nom")``; ``words(x, "UAH")`` — the same as ``money_words``."""
    positional("words", args, 1, 2, span)
    if len(args) == 2:
        from primula.library.money import money_words

        return money_words(lib, args, kwargs, span)
    keywords("words", kwargs, ("gender", "case", "lang"), span)
    value = number("words", "x", args[0], span)
    lang = lib.lang(kwargs.get("lang"), span)
    case = choice("words", kwargs.get("case", "nom"), CASES, "P2708", span)
    gender = choice("words", kwargs.get("gender", "m"), GENDERS, "P2709", span)
    return number_words(value, lang, case, gender, span)


def ordinal(lib: Library, args: list[Any], kwargs: dict[str, Any], span: Any) -> str:
    """``ordinal(n, gender="m", case="nom")``: 1 … 10¹⁵ − 1."""
    positional("ordinal", args, 1, 1, span)
    keywords("ordinal", kwargs, ("gender", "case", "lang"), span)
    value = args[0]
    if not is_number(value) or isinstance(value, float) or to_decimal(value) != int(to_decimal(value)) \
            or not 1 <= int(value) < WORDS_LIMIT:
        if not is_number(value):
            number("ordinal", "n", value, span)
        raise lib_error("P2704", span, None, function="ordinal", value=str(value), range="1 … 10¹⁵ − 1")
    lang = lib.lang(kwargs.get("lang"), span)
    case = choice("ordinal", kwargs.get("case", "nom"), CASES, "P2708", span)
    gender = choice("ordinal", kwargs.get("gender", "m"), GENDERS, "P2709", span)
    return _WORDS[lang].ordinal(int(value), case, gender)


def date_words(lib: Library, args: list[Any], kwargs: dict[str, Any], span: Any) -> str:
    """``date_words(dt)``: «дванадцятого жовтня дві тисячі двадцять шостого року»."""
    positional("date_words", args, 1, 1, span)
    keywords("date_words", kwargs, ("lang",), span)
    value: DateTime = moment("date_words", "dt", args[0], span)
    lang = lib.lang(kwargs.get("lang"), span)
    when = value.to_python()
    months = lib.months(lang)
    month = (months.get("gen") or months["nom"])[when.month - 1]
    return _WORDS[lang].date_words(when.day, month, when.year)


FUNCTIONS = {"num": num, "percent": percent, "round_to": round_to, "ceil_to": ceil_to, "floor_to": floor_to,
             "round_money": round_money, "words": words, "ordinal": ordinal, "date_words": date_words}
