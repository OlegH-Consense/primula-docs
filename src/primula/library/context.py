"""Shared state of the standard library: language, dictionaries, argument checks.

A :class:`Library` is created by the document evaluator and passed to every
function of the prelude (:mod:`primula.library.prelude`).  It knows

* the document language (header ``doc.language``, then
  ``defaults.language`` of the styles modules, then ``uk-UA``; decision
  65) and resolves ``lang=`` (library 1, decision 115): a tag with a
  region is reduced to the language (``uk-UA`` → ``uk``); a document in
  another language uses ``en`` with one warning P2701; an unknown
  ``lang=`` is error P2702;
* the dictionaries: built-in tables of :mod:`primula.library.dictionaries`
  merged with ``currency(…)``, ``unit(…)``, ``month_names(…)``,
  ``typography(…)`` of the styles modules (settings of the style
  registry, merged by layers).

All library errors are ``P27xx`` diagnostics with translated texts.
"""

from __future__ import annotations

import math
from decimal import Decimal
from typing import Any, Callable

from primula.core.errors import CoreError, core_error, resolve
from primula.core.values import DateTime, type_name
from primula.diagnostics import DiagnosticSink, error, warning
from primula.i18n import Key
from primula.library import dictionaries as D

#: Languages of the library (library 1).
LANGUAGES = ("uk", "ru", "en")
#: Genders and cases of words (library 4).
GENDERS = ("m", "f", "n")
CASES = ("nom", "gen", "dat", "acc", "ins", "loc")
NBSP = " "
MINUS = "−"


def language_code(tag: str | None) -> str:
    """``uk-UA`` → ``uk``; lower case."""
    return (tag or "").split("-")[0].split("_")[0].lower()


class Library:
    """The standard library bound to one document.

    Args:
        settings: returns the merged settings of the style registry (live:
            styles code may still run when a function is called).
        language: returns the document language tag.
        sink: receiver of warnings (P2701).
    """

    def __init__(self, settings: Callable[[], dict[str, Any]], language: Callable[[], str | None],
                 sink: DiagnosticSink | None = None) -> None:
        self._settings = settings
        self._language = language
        self.sink = sink
        self._warned = False
        #: Checked calendars by the identity of the data value (``workdays``).
        self.calendars: dict[int, tuple[Any, Any]] = {}
        #: Meter of the interpreter (time limit of long loops), set by the prelude.
        self.meter: Any = None
        #: The interpreter (calls of key functions in group_by…), set by the prelude.
        self.interp: Any = None

    # --- language ---------------------------------------------------------------------------

    def lang(self, value: Any, span: Any) -> str:
        """The language of a call: ``lang=`` or the document language."""
        if value is not None:
            code = language_code(value) if isinstance(value, str) else ""
            if code not in LANGUAGES:
                raise lib_error("P2702", span, None, lang=str(value), allowed=", ".join(LANGUAGES))
            return code
        tag = self._language()
        code = language_code(tag)
        if code in LANGUAGES:
            return code
        if not self._warned and self.sink is not None:
            self._warned = True
            self.sink.emit(warning("P2701", span, lang=str(tag)).hint("help.lib_lang"))
        return "en"

    def document_lang(self) -> str:
        """The document language reduced to uk/ru/en without warnings (tables)."""
        code = language_code(self._language())
        return code if code in LANGUAGES else "en"

    # --- dictionaries -------------------------------------------------------------------------

    def _setting(self, key: str) -> dict[str, Any]:
        value = self._settings().get(key)
        return value if isinstance(value, dict) else {}

    def currency(self, code: Any, lang: str, span: Any) -> dict[str, Any]:
        """Fields of a currency for a language: built-in table merged with ``currency(…)``."""
        if not isinstance(code, str):
            raise lib_error("P2705", span, "help.lib_currency", code=str(code))
        key = code.upper() if code.isascii() else code
        builtin = D.CURRENCIES.get(key, {})
        own = self._setting("currency").get(key, {})
        if not builtin and not own:
            raise lib_error("P2705", span, "help.lib_currency", code=code)
        fields: dict[str, Any] = dict(builtin.get(lang) or builtin.get("en") or {})
        fields.update(own.get(lang) or {})
        if "units" not in fields:
            raise lib_error("P2705", span, "help.lib_currency", code=code)
        return fields

    def currency_symbol(self, code: str | None, lang: str) -> str | None:
        """Short symbol of a currency for table columns (decision 79); unknown codes as written."""
        if not code:
            return None
        key = code.upper() if code.isascii() else code
        builtin = D.CURRENCIES.get(key, {})
        own = self._setting("currency").get(key, {})
        fields = dict(builtin.get(lang) or builtin.get("en") or {})
        fields.update(own.get(lang) or {})
        return str(fields["short"]) if "short" in fields else code

    def unit(self, code: Any, span: Any) -> dict[str, Any]:
        """A unit: built-in table merged with ``unit(…)`` (symbols by language)."""
        if not isinstance(code, str):
            raise lib_error("P2706", span, None, code=str(code))
        builtin = D.UNITS.get(code)
        own = self._setting("unit").get(code)
        if builtin is None and own is None:
            raise lib_error("P2706", span, None, code=code)
        fields: dict[str, Any] = {"symbol": dict(builtin["symbol"]) if builtin else {},
                                  "quantity": builtin["quantity"] if builtin else None,
                                  "factor": builtin["factor"] if builtin else Decimal(1),
                                  "offset": builtin["offset"] if builtin else Decimal(0)}
        for lang, values in (own or {}).items():
            for name, value in (values or {}).items():
                if name == "symbol":
                    fields["symbol"][lang] = value
                else:
                    fields[name] = value
        return fields

    def months(self, lang: str) -> dict[str, list[str]]:
        result = {k: list(v) for k, v in D.MONTHS[lang].items()}
        for case, names in (self._setting("month_names").get(lang) or {}).items():
            result[case] = list(names)
        return result

    def typography(self) -> dict[str, Any]:
        return {**D.TYPOGRAPHY, **self._setting("typography")}


def lib_error(code: str, span: Any, hint: str | None = None, /, **args: Any) -> CoreError:
    """A library error ``P27xx`` with an optional hint key.

    ``code``, ``span`` and ``hint`` are positional-only, so a message may
    have an argument named ``code`` (a currency or unit code).
    """
    diagnostic = error(code, resolve(span), **args)
    if hint:
        diagnostic.hint(hint)
    return CoreError(diagnostic)


# --- argument helpers ---------------------------------------------------------------------------

def is_number(value: Any) -> bool:
    return isinstance(value, (int, Decimal, float)) and not isinstance(value, bool)


def expect(function: str, arg: str, value: Any, ok: bool, expected: str, span: Any) -> None:
    """Raise P2721 «argument must be …» when ``ok`` is false."""
    if not ok:
        raise lib_error("P2721", span, None, function=function, arg=arg, expected=Key("type." + expected),
                         type=type_name(value))


def number(function: str, arg: str, value: Any, span: Any) -> Any:
    """A ``decimal`` or finite ``float`` argument."""
    expect(function, arg, value, is_number(value) and not (isinstance(value, float) and not math.isfinite(value)),
           "number", span)
    return value


def exact(function: str, arg: str, value: Any, span: Any) -> int | Decimal:
    """A ``decimal`` argument of a money function; ``float`` is P2703 (library 3)."""
    if isinstance(value, float):
        raise lib_error("P2703", span, "help.lib_float_money", function=function)
    expect(function, arg, value, is_number(value), "decimal", span)
    return value


def integer(function: str, arg: str, value: Any, span: Any) -> int:
    """A number with an integer value (``2``, ``2.0``)."""
    if is_number(value) and not isinstance(value, float) and Decimal(value) == Decimal(value).to_integral_value():
        return int(value)
    if isinstance(value, float) and math.isfinite(value) and value.is_integer():
        return int(value)
    expect(function, arg, value, False, "integer", span)
    raise AssertionError  # pragma: no cover


def string(function: str, arg: str, value: Any, span: Any) -> str:
    expect(function, arg, value, isinstance(value, str), "string", span)
    return value


def moment(function: str, arg: str, value: Any, span: Any) -> DateTime:
    expect(function, arg, value, isinstance(value, DateTime), "datetime", span)
    return value


def choice(function: str, value: Any, allowed: tuple[str, ...], code: str, span: Any, **names: str) -> str:
    """A case or gender from ``allowed`` (P2708 for cases, P2709 for genders)."""
    if value not in allowed:
        raise core_error(code, span, function=function, value=str(value), allowed=", ".join(allowed), **names)
    return value


def keywords(function: str, kwargs: dict[str, Any], allowed: tuple[str, ...], span: Any) -> None:
    """Unknown keyword arguments: P2321 of the core."""
    for key in kwargs:
        if key not in allowed:
            raise core_error("P2321", span, function=function, problem=f"got an unexpected keyword argument '{key}'")


def positional(function: str, args: list[Any], low: int, high: int, span: Any) -> None:
    if not low <= len(args) <= high:
        expected = str(low) if low == high else f"{low}..{high}"
        raise core_error("P2321", span, function=function,
                         problem=f"takes {expected} positional arguments but {len(args)} were given")


def to_decimal(value: Any) -> Decimal:
    """An exact ``Decimal`` of a ``decimal`` or the shortest decimal form of a ``float``."""
    if isinstance(value, float):
        return Decimal(repr(value))
    return Decimal(value)


__all__ = ["Library", "CoreError", "LANGUAGES", "GENDERS", "CASES", "NBSP", "MINUS"]
