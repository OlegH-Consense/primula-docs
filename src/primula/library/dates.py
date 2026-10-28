"""Dates and time (library 5; decisions 94, 95, 107, 115).

``weeks``, ``hours``, ``minutes`` (days as a number), ``add_months``,
``add_years``, ``fmt_date``, ``fmt_time``, ``fmt_datetime``, ``weekday``,
``month_name``, ``workdays``, ``is_workday``.

Formats (library 5, table of forms):

==========  ======================  =====================  ==================
format      uk                      ru                     en
==========  ======================  =====================  ==================
short       12.10.2026              12.10.2026             2026-10-12
long        12 жовтня 2026 року     12 октября 2026 года   12 October 2026
contract    «12» жовтня 2026 р.     «12» октября 2026 г.   12 October 2026
==========  ======================  =====================  ==================

``fmt_datetime``: ``short`` — date and «14:30», ``long`` — «…, 14:30»;
seconds are shown only when they are not zero.  Templates use
``{d} {dd} {m} {mm} {y} {yy} {month} {month_gen} {weekday}``, and in
``fmt_time``/``fmt_datetime`` also ``{h} {hh} {mi} {s} {ss}``; ``{{`` and
``}}`` are literal braces.

The calendar is project data (``load_yaml``): ``weekend``, ``holidays``,
``workdays``, ``rest_days``.  ``workdays``, ``holidays`` and ``rest_days``
win over ``weekend``; a date both in ``workdays`` and in ``holidays`` or
``rest_days`` is an error.  Nothing is moved automatically.
"""

from __future__ import annotations

import calendar as pycalendar
from typing import Any

from primula.core import numbers as core_numbers
from primula.core.values import DateTime, DateTimeError, PDict, PList, Record
from primula.library import localefmt
from primula.library.context import (
    lib_error,
    Library, choice, integer, is_number, keywords, moment, number, positional,
)
from primula.library.dictionaries import WEEKDAY_KEYS, WEEKDAYS

_DATE_PLACEHOLDERS = ("d", "dd", "m", "mm", "y", "yy", "month", "month_gen", "weekday")
_TIME_PLACEHOLDERS = ("h", "hh", "mi", "s", "ss")


# --- durations --------------------------------------------------------------------------------------

def _days(name: str, per_day: int):
    """``weeks(n)``, ``hours(n)``, ``minutes(n)``: the number of days (a ``decimal`` or ``float``)."""
    def impl(lib: Library, args: list[Any], kwargs: dict[str, Any], span: Any) -> Any:
        positional(name, args, 1, 1, span)
        keywords(name, kwargs, (), span)
        value = number(name, "n", args[0], span)
        if per_day < 0:
            return core_numbers.arith("*", value, -per_day)
        return core_numbers.arith("/", value, per_day)
    return impl


weeks = _days("weeks", -7)
hours = _days("hours", 24)
minutes = _days("minutes", 1440)


def shift_months(value: DateTime, months: int, span: Any) -> DateTime:
    """Calendar shift; the day is clipped to the month length (31 → 30/28/29); the time is kept."""
    when = value.to_python()
    index = when.year * 12 + when.month - 1 + months
    year, month = divmod(index, 12)
    month += 1
    if not 1 <= year <= 9999:
        raise lib_error("P2704", span, None, function="add_months", value=str(year), range="1 … 9999")
    day = min(when.day, pycalendar.monthrange(year, month)[1])
    try:
        return DateTime.of(year, month, day, when.hour, when.minute, when.second)
    except DateTimeError:  # pragma: no cover - the range is checked above
        raise lib_error("P2704", span, None, function="add_months", value=str(year), range="1 … 9999") from None


def add_months(lib: Library, args: list[Any], kwargs: dict[str, Any], span: Any) -> DateTime:
    """``add_months(dt, n)``."""
    positional("add_months", args, 2, 2, span)
    keywords("add_months", kwargs, (), span)
    return shift_months(moment("add_months", "dt", args[0], span), integer("add_months", "n", args[1], span), span)


def add_years(lib: Library, args: list[Any], kwargs: dict[str, Any], span: Any) -> DateTime:
    """``add_years(dt, n)``: 29.02 + 1 year → 28.02."""
    positional("add_years", args, 2, 2, span)
    keywords("add_years", kwargs, (), span)
    return shift_months(moment("add_years", "dt", args[0], span), 12 * integer("add_years", "n", args[1], span),
                        span)


# --- formatting -------------------------------------------------------------------------------------

def _fields(lib: Library, value: DateTime, lang: str) -> dict[str, str]:
    when = value.to_python()
    months = lib.months(lang)
    return {
        "d": str(when.day), "dd": f"{when.day:02d}", "m": str(when.month), "mm": f"{when.month:02d}",
        "y": f"{when.year:04d}", "yy": f"{when.year % 100:02d}",
        "month": months["nom"][when.month - 1],
        "month_gen": (months.get("gen") or months["nom"])[when.month - 1],
        "weekday": WEEKDAYS[lang]["nom"][when.weekday()],
        "h": str(when.hour), "hh": f"{when.hour:02d}", "mi": f"{when.minute:02d}",
        "s": str(when.second), "ss": f"{when.second:02d}",
    }


def _template(function: str, template: str, fields: dict[str, str], allowed: tuple[str, ...], span: Any) -> str:
    """Fill ``{name}`` placeholders; ``{{``/``}}`` are braces."""
    out: list[str] = []
    i = 0
    while i < len(template):
        char = template[i]
        if char in "{}" and template[i:i + 2] in ("{{", "}}"):
            out.append(char)
            i += 2
            continue
        if char == "}":
            raise lib_error("P2711", span, None, function=function, placeholder="}")
        if char == "{":
            end = template.find("}", i)
            name = template[i + 1:end] if end > 0 else template[i + 1:]
            if end < 0 or name not in fields:
                raise lib_error("P2711", span, None, function=function, placeholder="{" + name + ("}" if end > 0 else ""))
            if name not in allowed:
                raise lib_error("P2710", span, "help.lib_fmt_datetime", placeholder="{" + name + "}")
            out.append(fields[name])
            i = end + 1
            continue
        out.append(char)
        i += 1
    return "".join(out)


def _date_text(lib: Library, value: DateTime, fmt: Any, lang: str, function: str, span: Any) -> str:
    fields = _fields(lib, value, lang)
    if fmt == "short":
        return localefmt.format_date(value, lang)
    if fmt == "long":
        if lang == "en":
            return f"{fields['d']} {fields['month']} {fields['y']}"
        return f"{fields['d']} {fields['month_gen']} {fields['y']} " + ("року" if lang == "uk" else "года")
    if fmt == "contract":
        if lang == "en":
            return f"{fields['d']} {fields['month']} {fields['y']}"
        return f"«{fields['dd']}» {fields['month_gen']} {fields['y']} " + ("р." if lang == "uk" else "г.")
    if isinstance(fmt, str) and "{" in fmt:
        return _template(function, fmt, fields, _DATE_PLACEHOLDERS, span)
    raise lib_error("P2712", span, None, function=function, format=str(fmt), allowed="short, long, contract, {…}")


def _time_text(value: DateTime) -> str:
    return localefmt.format_time(value)


def fmt_date(lib: Library, args: list[Any], kwargs: dict[str, Any], span: Any) -> str:
    """``fmt_date(dt, "short")``; only the date is shown."""
    positional("fmt_date", args, 1, 2, span)
    keywords("fmt_date", kwargs, ("lang",), span)
    value = moment("fmt_date", "dt", args[0], span)
    fmt = args[1] if len(args) > 1 else "short"
    return _date_text(lib, value, fmt, lib.lang(kwargs.get("lang"), span), "fmt_date", span)


def fmt_time(lib: Library, args: list[Any], kwargs: dict[str, Any], span: Any) -> str:
    """``fmt_time(dt, "short")``: «14:30», «14:30:15»; or a template; ``long`` — error."""
    positional("fmt_time", args, 1, 2, span)
    keywords("fmt_time", kwargs, ("lang",), span)
    value = moment("fmt_time", "dt", args[0], span)
    fmt = args[1] if len(args) > 1 else "short"
    if fmt == "short":
        return _time_text(value)
    if isinstance(fmt, str) and "{" in fmt:
        lang = lib.lang(kwargs.get("lang"), span)
        return _template("fmt_time", fmt, _fields(lib, value, lang), _DATE_PLACEHOLDERS + _TIME_PLACEHOLDERS, span)
    raise lib_error("P2712", span, None, function="fmt_time", format=str(fmt), allowed="short, {…}")


def fmt_datetime(lib: Library, args: list[Any], kwargs: dict[str, Any], span: Any) -> str:
    """``fmt_datetime(dt, "short"|"long"|template)``."""
    positional("fmt_datetime", args, 1, 2, span)
    keywords("fmt_datetime", kwargs, ("lang",), span)
    value = moment("fmt_datetime", "dt", args[0], span)
    fmt = args[1] if len(args) > 1 else "short"
    lang = lib.lang(kwargs.get("lang"), span)
    if fmt == "short":
        return _date_text(lib, value, "short", lang, "fmt_datetime", span) + " " + _time_text(value)
    if fmt == "long":
        return _date_text(lib, value, "long", lang, "fmt_datetime", span) + ", " + _time_text(value)
    if isinstance(fmt, str) and "{" in fmt:
        return _template("fmt_datetime", fmt, _fields(lib, value, lang), _DATE_PLACEHOLDERS + _TIME_PLACEHOLDERS,
                         span)
    raise lib_error("P2712", span, None, function="fmt_datetime", format=str(fmt), allowed="short, long, {…}")


def weekday(lib: Library, args: list[Any], kwargs: dict[str, Any], span: Any) -> str:
    """``weekday(dt, case="nom")``: the name; ``acc`` — «у понеділок»."""
    positional("weekday", args, 1, 1, span)
    keywords("weekday", kwargs, ("case", "lang"), span)
    value = moment("weekday", "dt", args[0], span)
    lang = lib.lang(kwargs.get("lang"), span)
    case = choice("weekday", kwargs.get("case", "nom"), ("nom", "acc"), "P2708", span)
    names = WEEKDAYS[lang]
    return (names.get(case) or names["nom"])[value.to_python().weekday()]


def month_name(lib: Library, args: list[Any], kwargs: dict[str, Any], span: Any) -> str:
    """``month_name(dt, case="nom")``: ``nom``, ``gen``, ``loc`` («у жовтні»); a month number is accepted."""
    positional("month_name", args, 1, 1, span)
    keywords("month_name", kwargs, ("case", "lang"), span)
    value = args[0]
    if isinstance(value, DateTime):
        month = value.to_python().month
    elif is_number(value) and not isinstance(value, float) and 1 <= value <= 12 and value == int(value):
        month = int(value)
    else:
        moment("month_name", "dt", value, span)
        raise AssertionError  # pragma: no cover
    lang = lib.lang(kwargs.get("lang"), span)
    case = choice("month_name", kwargs.get("case", "nom"), ("nom", "gen", "loc"), "P2708", span)
    months = lib.months(lang)
    return (months.get(case) or months["nom"])[month - 1]


# --- calendar --------------------------------------------------------------------------------------

class Calendar:
    """A checked calendar: weekend days (0 = Monday), holiday, working and rest dates."""

    def __init__(self, weekend: set[int], holidays: set[int], workdays: set[int], rest_days: set[int]) -> None:
        self.weekend = weekend
        self.off = holidays | rest_days
        self.work = workdays

    def is_workday(self, day_seconds: int) -> bool:
        if day_seconds in self.work:
            return True
        if day_seconds in self.off:
            return False
        return DateTime(day_seconds).to_python().weekday() not in self.weekend


_DEFAULT = Calendar({5, 6}, set(), set(), set())
_KEYS = ("weekend", "holidays", "workdays", "rest_days")


def _date_set(key: str, values: Any, span: Any) -> set[int]:
    if not isinstance(values, (list, tuple, PList)):
        raise lib_error("P2714", span, None, key=key)
    out: set[int] = set()
    for item in values:
        if not isinstance(item, DateTime) or not item.is_date:
            raise lib_error("P2714", span, None, key=key)
        out.add(item.seconds)
    return out


def load_calendar(value: Any, span: Any, cache: dict[int, tuple[Any, Calendar]]) -> Calendar:
    """Check a calendar record (YAML) once per value."""
    if value is None:
        return _DEFAULT
    cached = cache.get(id(value))
    if cached is not None and cached[0] is value:
        return cached[1]
    if isinstance(value, Record):
        data = dict(value.fields)
    elif isinstance(value, (dict, PDict)):
        data = dict(value)
    else:
        raise lib_error("P2714", span, None, key="calendar")
    for key in data:
        if key not in _KEYS:
            raise lib_error("P2713", span, None, key=str(key), allowed=", ".join(_KEYS))
    weekend_names = data.get("weekend", ["sat", "sun"])
    if not isinstance(weekend_names, (list, tuple)) or any(n not in WEEKDAY_KEYS for n in weekend_names):
        raise lib_error("P2714", span, None, key="weekend")
    holidays = _date_set("holidays", data.get("holidays", []), span)
    work = _date_set("workdays", data.get("workdays", []), span)
    rest = _date_set("rest_days", data.get("rest_days", []), span)
    clash = sorted(work & (holidays | rest))
    if clash:
        raise lib_error("P2715", span, None, date=DateTime(clash[0]).iso())
    result = Calendar({WEEKDAY_KEYS.index(n) for n in weekend_names}, holidays, work, rest)
    cache[id(value)] = (value, result)
    return result


def _day(value: DateTime) -> int:
    return value.seconds - value.seconds % 86400


def is_workday(lib: Library, args: list[Any], kwargs: dict[str, Any], span: Any) -> bool:
    """``is_workday(d, calendar=cal)``; the time of day is ignored."""
    positional("is_workday", args, 1, 1, span)
    keywords("is_workday", kwargs, ("calendar",), span)
    value = moment("is_workday", "d", args[0], span)
    return load_calendar(kwargs.get("calendar"), span, lib.calendars).is_workday(_day(value))


def workdays(lib: Library, args: list[Any], kwargs: dict[str, Any], span: Any) -> DateTime:
    """``workdays(d, n, calendar=cal)``: ``n`` working days after ``d`` (``d`` itself not counted)."""
    positional("workdays", args, 2, 2, span)
    keywords("workdays", kwargs, ("calendar",), span)
    value = moment("workdays", "d", args[0], span)
    count = integer("workdays", "n", args[1], span)
    cal = load_calendar(kwargs.get("calendar"), span, lib.calendars)
    day = _day(value)
    step = 86400 if count > 0 else -86400
    left = abs(count)
    while left:
        day += step
        if lib.meter is not None:
            lib.meter.step(span)  # the time limit of the evaluation (12.8)
        try:
            DateTime.from_seconds(day)
        except DateTimeError:
            raise lib_error("P2704", span, None, function="workdays", value=str(count), range="1 … 9999") from None
        if cal.is_workday(day):
            left -= 1
    return DateTime(day)


FUNCTIONS = {"weeks": weeks, "hours": hours, "minutes": minutes, "add_months": add_months, "add_years": add_years,
             "fmt_date": fmt_date, "fmt_time": fmt_time, "fmt_datetime": fmt_datetime, "weekday": weekday,
             "month_name": month_name, "is_workday": is_workday, "workdays": workdays}

