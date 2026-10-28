"""Numbers, money and dates by the document language (6.8; decisions 77-79, 109).

Output (``format_*``):

* uk, ru — groups of three digits separated by a no-break space (U+00A0),
  decimal comma: «12 500,00»;
* en — groups separated by a comma, decimal point: «12,500.00»;
* dates — ``short`` form: «12.10.2026» (uk, ru, DSTU 4163:2020), ISO
  «2026-10-12» (en, decision 77); a moment with a time of day adds
  «14:30» (seconds only when not zero), as ``fmt_datetime(x, "short")``;
* money — the number with two digits and the currency symbol after a
  no-break space (decision 79);
* the minus sign is U+2212 «−» (decision 115).

Input (``parse_*``, typed table columns, 6.8): the locale form and the
canonical form (``1234.56`` without groups, ISO dates and moments); minus
``-`` or ``−`` (U+2212).  Invalid text raises :class:`ParseError`.
"""

from __future__ import annotations

import datetime
import re
from decimal import Decimal, InvalidOperation
from typing import Any

from primula.core.values import DateTime, DateTimeError, parse_iso_datetime

NBSP = "\u00a0"
#: The minus sign of the output (decision 115).
MINUS = "\u2212"

#: Separators by language: (group, decimal).
_SEPARATORS = {"uk": (NBSP, ","), "ru": (NBSP, ","), "en": (",", ".")}

#: Short currency names (13.3); stage 13.9 adds full forms and declension.
CURRENCIES: dict[str, dict[str, str]] = {
    "UAH": {"uk": "грн", "ru": "грн", "en": "UAH"},
    "USD": {"uk": "дол. США", "ru": "долл. США", "en": "USD"},
    "EUR": {"uk": "євро", "ru": "евро", "en": "EUR"},
}


class ParseError(ValueError):
    """Text that is not a number or date of the expected form."""


def _language(lang: str | None) -> str:
    code = (lang or "uk").split("-")[0].lower()
    return code if code in _SEPARATORS else "en"


def _group(digits: str, separator: str) -> str:
    """``1234567`` -> ``1 234 567`` (groups of three from the right)."""
    head = len(digits) % 3 or 3
    parts = [digits[:head]] + [digits[i:i + 3] for i in range(head, len(digits), 3)]
    return separator.join(parts)


def format_number(value: Any, digits: int | None = None, lang: str | None = None) -> str:
    """A number by the language: «12 500,00».

    Args:
        value: ``int``, ``Decimal`` or ``float``.
        digits: digits after the decimal separator (rounded half away from
            zero); ``None`` — as many as the value has.
        lang: language tag (``uk``, ``uk-UA``, ``en``…).

    Returns:
        The formatted text; negative numbers start with «−» (U+2212).
    """
    group, point = _SEPARATORS[_language(lang)]
    if isinstance(value, bool):
        raise TypeError("bool")
    number = value if isinstance(value, Decimal) else Decimal(str(value))
    if digits is not None:
        number = number.quantize(Decimal(1).scaleb(-digits), rounding="ROUND_HALF_UP")
    # The minus sign of the output is U+2212 for all languages (decision 115).
    sign, text = (MINUS, format(-number, "f")) if number < 0 else ("", format(number, "f"))
    whole, _, fraction = text.partition(".")
    result = sign + _group(whole, group)
    return result + point + fraction if fraction else result


def currency_symbol(currency: str | None, lang: str | None = None) -> str | None:
    """Symbol of a currency code (``UAH`` -> «грн») or the string itself (decision 79)."""
    if not currency:
        return None
    names = CURRENCIES.get(currency.upper()) if currency.isalpha() and len(currency) == 3 else None
    return names.get(_language(lang), names["en"]) if names else currency


def format_money(value: Any, currency: str | None = None, lang: str | None = None) -> str:
    """«12 500,00 грн»: two digits and the currency after a no-break space."""
    text = format_number(value, 2, lang)
    symbol = currency_symbol(currency, lang)
    return f"{text}{NBSP}{symbol}" if symbol else text


def format_date(value: DateTime | datetime.date, lang: str | None = None) -> str:
    """The short date form: «12.10.2026» (uk, ru), ISO (en); the time is ignored."""
    moment = value.to_python() if isinstance(value, DateTime) else value
    if _language(lang) == "en":
        return f"{moment.year:04d}-{moment.month:02d}-{moment.day:02d}"
    return f"{moment.day:02d}.{moment.month:02d}.{moment.year:04d}"


def format_time(value: DateTime) -> str:
    """«14:30», or «14:30:15» when the seconds are not zero."""
    moment = value.to_python()
    text = f"{moment.hour:02d}:{moment.minute:02d}"
    return text + f":{moment.second:02d}" if moment.second else text


def format_moment(value: DateTime, lang: str | None = None) -> str:
    """A ``datetime`` in a table cell (6.8): the short date, and the time if not 00:00:00."""
    text = format_date(value, lang)
    return text if value.is_date else f"{text} {format_time(value)}"


_GROUPS = "[   ]"


def _number_text(text: str, lang: str | None) -> str:
    """Normalise a number text to the canonical form, or raise :class:`ParseError`."""
    cleaned = text.strip().replace("−", "-")
    if not cleaned:
        raise ParseError(text)
    language = _language(lang)
    if re.fullmatch(r"-?\d+(\.\d+)?", cleaned):  # canonical form
        return cleaned
    if language == "en":
        match = re.fullmatch(r"(-?)(\d{1,3}(?:,\d{3})+|\d+)(?:\.(\d+))?", cleaned)
        if match:
            return match.group(1) + match.group(2).replace(",", "") + ("." + match.group(3) if match.group(3) else "")
    else:
        match = re.fullmatch(rf"(-?)(\d{{1,3}}(?:{_GROUPS}\d{{3}})+|\d+)(?:,(\d+))?", cleaned)
        if match:
            whole = re.sub(_GROUPS, "", match.group(2))
            return match.group(1) + whole + ("." + match.group(3) if match.group(3) else "")
    raise ParseError(text)


def parse_decimal(text: str, lang: str | None = None) -> Any:
    """A ``decimal``: «1 234,56» (uk, ru), «1,234.56» (en), canonical «1234.56».

    An integer text gives an integer value (scale 0, a Python ``int``).
    """
    normal = _number_text(text, lang)
    try:
        return Decimal(normal) if "." in normal else int(normal)
    except InvalidOperation:  # pragma: no cover - the patterns admit only digits
        raise ParseError(text) from None


def parse_datetime(text: str, lang: str | None = None) -> DateTime:
    """A ``datetime`` (6.8): ISO ``2026-10-12``, ``2026-10-12T14:30[:00]`` everywhere;
    «12.10.2026» and «12.10.2026 14:30» for uk and ru."""
    cleaned = text.strip()
    try:
        match = re.fullmatch(r"(\d{1,2})\.(\d{1,2})\.(\d{4})(?: (\d{1,2}):(\d{2})(?::(\d{2}))?)?", cleaned)
        if match and _language(lang) != "en":
            day, month, year, hour, minute, second = match.groups()
            return DateTime.of(int(year), int(month), int(day), int(hour or 0), int(minute or 0),
                               int(second or 0))
        return parse_iso_datetime(cleaned)
    except DateTimeError:
        raise ParseError(text) from None
