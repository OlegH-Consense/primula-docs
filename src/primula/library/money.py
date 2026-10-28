"""Money and VAT (library 3; decisions 92, 98, 115).

``money``, ``money_words``, ``money_full``, ``vat``, ``with_vat``,
``vat_in``, ``without_vat``, ``split``.

* Every money function rounds to kopecks, half away from zero; ``float``
  is an error with the hint ``dec(…)`` (P2703).
* ``money(12500, "UAH")`` — «12 500,00 грн»; ``currency_style="full"`` —
  the word by the number: «12 500,00 гривень», a fractional sum —
  ``frac`` «12 500,50 гривні» (decision 115).
* ``money_words`` — the contract form: whole units in words, kopecks in
  digits («… гривень 00 копійок»), ``kop="words"`` — in words by the gender
  of the minor unit; ``cap=True`` — a capital first letter.
* VAT: the rate is given explicitly; ``with_vat = net + vat(net)``,
  ``without_vat = gross − vat_in(gross)``: the parts always add up to the
  sum shown in the document.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from primula.core.values import PList
from primula.library import words_en, words_ru, words_uk
from primula.library.context import lib_error, NBSP, Library, exact, keywords, positional
from primula.library.numbers import format_number, money_round

_WORDS = {"uk": words_uk, "ru": words_ru, "en": words_en}


def _forms(currency: dict[str, Any], key: str, lang: str, code: str, span: Any) -> tuple[str, ...]:
    """Forms by number of the unit (``units``) or of the minor unit (``minor``)."""
    forms = tuple(currency.get(key) or ())
    expected = 2 if lang == "en" else 3
    if len(forms) != expected or not all(isinstance(f, str) for f in forms):
        raise lib_error("P2722", span, None, function=f"currency {code}", count=expected, lang=lang, given=len(forms))
    return forms


def count_form(n: int, forms: tuple[str, ...], lang: str) -> str:
    """The word counted by an integer ``n`` in the nominative: 1 / 2–4 / 5+ (en: 1 / many)."""
    if lang == "en":
        return forms[0] if abs(n) == 1 else forms[1]
    return forms[words_uk.plural_class(n)]


def _parts(value: Decimal) -> tuple[str, int, int]:
    """Sign, whole units and kopecks of a rounded sum."""
    sign = "-" if value < 0 else ""
    cents = int(abs(value) * 100)
    whole, minor = divmod(cents, 100)
    return sign, whole, minor


def _money(lib: Library, value: Any, code: str, style: str, lang: str, span: Any) -> str:
    amount = money_round(value)
    currency = lib.currency(code, lang, span)
    text = format_number(amount, 2, lang)
    if style == "short":
        return text + NBSP + str(currency.get("short", code))
    _sign, whole, minor = _parts(amount)
    if minor == 0:
        word = count_form(whole, _forms(currency, "units", lang, code, span), lang)
    elif lang == "en":
        word = _forms(currency, "units", lang, code, span)[1]
    else:
        word = currency.get("frac")
        if not isinstance(word, str):
            raise lib_error("P2719", span, "help.lib_currency", code=code, lang=lang)
    return text + NBSP + word


def _words(lib: Library, value: Any, code: str, kop: str, cap: bool, lang: str, span: Any) -> str:
    amount = money_round(value)
    currency = lib.currency(code, lang, span)
    module = _WORDS[lang]
    sign, whole, minor = _parts(amount)
    if whole >= 10 ** 15:
        raise lib_error("P2704", span, None, function="money_words", value=str(value), range="0 … 10¹⁵ − 1")
    units = _forms(currency, "units", lang, code, span)
    minor_forms = _forms(currency, "minor", lang, code, span)
    gender = str(currency.get("gender", "f"))
    text = module.cardinal(whole, "nom", gender) + " " + count_form(whole, units, lang)
    if kop == "words":
        minor_text = module.cardinal(minor, "nom", str(currency.get("minor_gender", "f")))
    else:
        minor_text = str(minor).zfill(int(currency.get("minor_digits", 2)))
    text += " " + minor_text + " " + count_form(minor, minor_forms, lang)
    if sign:
        text = module.MINUS + " " + text
    if cap:
        text = text[:1].upper() + text[1:]
    return text


def _options(function: str, kwargs: dict[str, Any], allowed: tuple[str, ...], span: Any) -> dict[str, Any]:
    keywords(function, kwargs, allowed + ("lang",), span)
    style = kwargs.get("currency_style", "short")
    if style not in ("short", "full"):
        raise lib_error("P2712", span, None, function=function, format=str(style), allowed="short, full")
    kop = kwargs.get("kop", "digits")
    if kop not in ("digits", "words"):
        raise lib_error("P2712", span, None, function=function, format=str(kop), allowed="digits, words")
    return {"style": style, "kop": kop, "cap": bool(kwargs.get("cap", False))}


def _code(function: str, args: list[Any], span: Any) -> str:
    positional(function, args, 2, 2, span)
    return args[1]


def money(lib: Library, args: list[Any], kwargs: dict[str, Any], span: Any) -> str:
    """``money(x, "UAH", currency_style="short")``."""
    code = _code("money", args, span)
    options = _options("money", kwargs, ("currency_style",), span)
    value = exact("money", "x", args[0], span)
    return _money(lib, value, code, options["style"], lib.lang(kwargs.get("lang"), span), span)


def money_words(lib: Library, args: list[Any], kwargs: dict[str, Any], span: Any) -> str:
    """``money_words(x, "UAH", kop="digits", cap=False)``."""
    code = _code("money_words", args, span)
    options = _options("money_words", kwargs, ("kop", "cap"), span)
    value = exact("money_words", "x", args[0], span)
    return _words(lib, value, code, options["kop"], options["cap"], lib.lang(kwargs.get("lang"), span), span)


def money_full(lib: Library, args: list[Any], kwargs: dict[str, Any], span: Any) -> str:
    """``money_full(x, "UAH")``: «12 500,00 грн (дванадцять тисяч п'ятсот гривень 00 копійок)»."""
    code = _code("money_full", args, span)
    options = _options("money_full", kwargs, ("kop", "cap", "currency_style"), span)
    value = exact("money_full", "x", args[0], span)
    lang = lib.lang(kwargs.get("lang"), span)
    return (_money(lib, value, code, options["style"], lang, span) + " ("
            + _words(lib, value, code, options["kop"], options["cap"], lang, span) + ")")


# --- VAT ------------------------------------------------------------------------------------------

def _two(function: str, args: list[Any], kwargs: dict[str, Any], span: Any) -> tuple[Decimal, Decimal]:
    positional(function, args, 2, 2, span)
    keywords(function, kwargs, (), span)
    return Decimal(exact(function, "x", args[0], span)), Decimal(exact(function, "rate", args[1], span))


def vat(lib: Library, args: list[Any], kwargs: dict[str, Any], span: Any) -> Decimal:
    """``vat(net, rate)``: the tax of a sum without tax."""
    net, rate = _two("vat", args, kwargs, span)
    return money_round(net * rate / 100)


def with_vat(lib: Library, args: list[Any], kwargs: dict[str, Any], span: Any) -> Decimal:
    """``with_vat(net, rate)`` = ``net + vat(net, rate)``."""
    net, rate = _two("with_vat", args, kwargs, span)
    return money_round(net) + money_round(net * rate / 100)


def vat_in(lib: Library, args: list[Any], kwargs: dict[str, Any], span: Any) -> Decimal:
    """``vat_in(gross, rate)``: gross × rate / (100 + rate)."""
    gross, rate = _two("vat_in", args, kwargs, span)
    return money_round(gross * rate / (100 + rate))


def without_vat(lib: Library, args: list[Any], kwargs: dict[str, Any], span: Any) -> Decimal:
    """``without_vat(gross, rate)`` = ``gross − vat_in(gross, rate)``."""
    gross, rate = _two("without_vat", args, kwargs, span)
    return money_round(gross) - money_round(gross * rate / (100 + rate))


def split(lib: Library, args: list[Any], kwargs: dict[str, Any], span: Any) -> PList:
    """``split(total, [30, 70])``: parts by weights; the last part takes the rounding rest."""
    positional("split", args, 2, 2, span)
    keywords("split", kwargs, (), span)
    total = money_round(exact("split", "total", args[0], span))
    weights = args[1]
    if not isinstance(weights, (list, tuple)) or not weights:
        raise lib_error("P2718", span, None)
    values = [Decimal(exact("split", "weights", w, span)) for w in weights]
    if any(w < 0 for w in values) or sum(values) <= 0:
        raise lib_error("P2718", span, None)
    whole = sum(values)
    parts = [money_round(total * w / whole) for w in values[:-1]]
    parts.append(total - sum(parts, Decimal(0)))
    return PList(parts)


FUNCTIONS = {"money": money, "money_words": money_words, "money_full": money_full, "vat": vat,
             "with_vat": with_vat, "vat_in": vat_in, "without_vat": without_vat, "split": split}
