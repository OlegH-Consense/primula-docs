"""Catalogue of the functions of expressions (stage 14.13; decision 126).

Part of ``primula commands --format json`` (key ``functions``): every name
that can be called in Primula code — the prelude of the standard library
(library 2–8), the built-in functions of the core (12.10), the data
loaders (10.5), ``std/math`` (library 9), the functions of styles code
(11, settings of sections 5, 7–9), the project functions (10.7), the
functions of table formulas (6.8) and the methods of strings, lists and
dictionaries (12.10).

Each entry::

    {"name": "money", "kind": "function", "module": "", "receiver": "",
     "category": "money", "where": "any", "doc": "stdlib", "section": "3",
     "summary": "...", "returns": "str", "signature": "money(x, code, currency_style=\\"short\\", lang=None)",
     "args": [...as in commands...], "example": "money(12500, \\"UAH\\")",
     "result": "\\"12 500,00 грн\\""}

``kind``: ``function``, ``constant`` or ``method`` (``receiver``: ``str``,
``list``, ``dict``).  ``module``: ``std/math`` for the names of
``|import("std/math")`` (written ``math.sqrt``), else empty.  ``where``:
``any``, ``styles`` (styles code: styles module, project, document — not
an ``|import`` module), ``project`` (the code of a project file), ``cell``
(a table cell formula).  ``doc``: ``spec`` (main specification) or
``stdlib`` (the standard library document), with the ``section`` there.
``result``: the example evaluated by the translator in the catalogue
language (the language of the messages), ``null`` for examples that need a
document (data files, markup, styles).

The table is checked against the translator by tests: every built-in name
is described, and the positional and keyword arguments are those the
functions accept.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass
from typing import Any, Callable

from primula.commands import Arg, T

#: Categories of functions, in menu order.
CATEGORIES: list[tuple[str, T]] = [
    ("numbers", ("Numbers", "Числа", "Числа")),
    ("money", ("Money and VAT", "Гроші й ПДВ", "Деньги и НДС")),
    ("words", ("In words", "Прописом", "Прописью")),
    ("dates", ("Dates and time", "Дати й час", "Даты и время")),
    ("units", ("Units and lengths", "Одиниці й довжини", "Единицы и длины")),
    ("text", ("Text", "Текст", "Текст")),
    ("collections", ("Lists and records", "Списки й записи", "Списки и записи")),
    ("data", ("Data", "Дані", "Данные")),
    ("math", ("Mathematics (std/math)", "Математика (std/math)", "Математика (std/math)")),
    ("codes", ("QR codes and encodings", "QR-коди й кодування", "QR-коды и кодировки")),
    ("core", ("Checks and document", "Перевірки й документ", "Проверки и документ")),
    ("tables", ("Table formulas", "Формули таблиць", "Формулы таблиц")),
    ("styles", ("Styles code", "Код стилів", "Код стилей")),
    ("project", ("Project", "Проєкт", "Проект")),
    ("methods", ("Methods", "Методи", "Методы")),
]


@dataclass(frozen=True)
class Function:
    """A function, constant or method of expressions.

    Attributes:
        name: the name (``money``, ``sqrt``, ``split``).
        category: a key of :data:`CATEGORIES`.
        doc: ``spec`` or ``stdlib``; section: the section there.
        text: short description (en, uk, ru).
        args: arguments in call order (positional first).
        returns: the type of the result (``str``, ``decimal``…, ``any``).
        example: a call; run: the translator evaluates it for ``result``.
        kind, module, receiver, where: see the module description.
    """

    name: str
    category: str
    doc: str
    section: str
    text: T
    args: tuple[Arg, ...] = ()
    returns: str = "any"
    example: str = ""
    run: bool = True
    kind: str = "function"
    module: str = ""
    receiver: str = ""
    where: str = "any"


def _p(name: str, type_: str, text: T, default: str | None = None) -> Arg:
    return Arg(name, type_, default, text, positional=True)


def _k(name: str, type_: str, text: T, default: str | None = None) -> Arg:
    return Arg(name, type_, default, text)


def _lib(name: str, category: str, section: str, text: T, args: tuple[Arg, ...], returns: str,
         example: str, run: bool = True) -> Function:
    return Function(name, category, "stdlib", section, text, args, returns, example, run)


def _core(name: str, category: str, section: str, text: T, args: tuple[Arg, ...], returns: str,
          example: str, run: bool = True, where: str = "any") -> Function:
    return Function(name, category, "spec", section, text, args, returns, example, run, where=where)


# Examples with Ukrainian words give lang="uk" explicitly: the same result in every catalogue language.

# --- shared arguments ------------------------------------------------------------------------

LANG = _k("lang", "string", ("language instead of the document language: uk, ru, en",
                             "мова замість мови документа: uk, ru, en",
                             "язык вместо языка документа: uk, ru, en"))
X = _p("x", "number", ("number", "число", "число"))
MONEY_X = _p("x", "decimal", ("amount (decimal, not float)", "сума (decimal, не float)", "сумма (decimal, не float)"))
CODE = _p("code", "string", ("currency code: UAH, USD, EUR or one of the styles module",
                             "код валюти: UAH, USD, EUR або з модуля стилів",
                             "код валюты: UAH, USD, EUR или из модуля стилей"))
RATE = _p("rate", "decimal", ("tax rate in percent: 20", "ставка податку у відсотках: 20",
                              "ставка налога в процентах: 20"))
KOP = _k("kop", "string", ("the minor unit in \"digits\" or \"words\"", "копійки \"digits\" (цифрами) або \"words\" (прописом)",
                           "копейки \"digits\" (цифрами) или \"words\" (прописью)"), '"digits"')
CAP = _k("cap", "bool", ("capital first letter", "велика перша літера", "заглавная первая буква"), "False")
CURRENCY_STYLE = _k("currency_style", "string", ("\"short\" (грн) or \"full\" (гривень)",
                                                 "\"short\" (грн) або \"full\" (гривень)",
                                                 "\"short\" (грн) или \"full\" (гривень)"), '"short"')
GENDER = _k("gender", "string", ("gender: \"m\", \"f\", \"n\" (uk, ru)", "рід: \"m\", \"f\", \"n\" (uk, ru)",
                                 "род: \"m\", \"f\", \"n\" (uk, ru)"), '"m"')
CASE = _k("case", "string", ("case: nom, gen, dat, acc, ins, loc", "відмінок: nom, gen, dat, acc, ins, loc",
                             "падеж: nom, gen, dat, acc, ins, loc"), '"nom"')
DT = _p("dt", "datetime", ("date or moment", "дата або момент", "дата или момент"))
DIGITS = _k("digits", "int", ("digits after the comma; None — as the value has",
                              "знаків після коми; None — як у значення",
                              "знаков после запятой; None — как у значения"), "None")
FORMAT = _p("format", "string", ("\"short\", \"long\", \"contract\" or a template \"{d} {month_gen} {y}\"",
                                 "\"short\", \"long\", \"contract\" або шаблон \"{d} {month_gen} {y}\"",
                                 "\"short\", \"long\", \"contract\" или шаблон \"{d} {month_gen} {y}\""), '"short"')
CALENDAR = _k("calendar", "record", ("calendar of the project: load_yaml(\"data/calendar-2026.yaml\")",
                                     "календар проєкту: load_yaml(\"data/calendar-2026.yaml\")",
                                     "календарь проекта: load_yaml(\"data/calendar-2026.yaml\")"))
ITEMS = _p("items", "list", ("list of records", "список записів", "список записей"))
KEY_FIELD = _p("key", "any", ("field name or function", "ім'я поля або функція", "имя поля или функция"))
S = _p("s", "string", ("string", "рядок", "строка"))
UNIT = _p("unit", "string", ("unit code: V, kW, mm, degC…", "код одиниці: V, kW, mm, degC…",
                             "код единицы: V, kW, mm, degC…"))
N = _p("n", "number", ("number", "число", "число"))
VALUE = _p("x", "any", ("value", "значення", "значение"))
SEQ = _p("seq", "list", ("list, tuple, string, dict or range", "список, кортеж, рядок, словник або range",
                         "список, кортеж, строка, словарь или range"))
PATH = _p("path", "path", ("file path (10.1)", "шлях до файлу (10.1)", "путь к файлу (10.1)"))
NAME = _p("name", "string", ("style name", "ім'я стилю", "имя стиля"))
LANG_FIRST = _p("lang", "string", ("language: uk, ru, en", "мова: uk, ru, en", "язык: uk, ru, en"))
COLUMN = _p("c", "any", ("column number from 1 or its id", "номер стовпця з 1 або його id",
                         "номер столбца с 1 или его id"))


SHEET = _k("sheet", "any", ("sheet name or number from 1; the first sheet by default",
                            "назва аркуша або номер з 1; типово перший аркуш",
                            "имя листа или номер с 1; по умолчанию первый лист"))
SHEET_RANGE = _k("range", "string", ("cells \"A1:D20\" or a start cell \"A3\"; the used area by default",
                                     "клітинки \"A1:D20\" або початкова \"A3\"; типово заповнена область",
                                     "ячейки \"A1:D20\" или начальная \"A3\"; по умолчанию заполненная область"))
SHEET_HEADER = _k("header", "bool", ("the first row gives field names; False — fields A, B, …",
                                     "перший рядок дає імена полів; False — поля A, B, …",
                                     "первая строка даёт имена полей; False — поля A, B, …"), "True")
QR_DATA = _p("data", "string", ("text to encode", "текст для кодування", "текст для кодирования"))
QR_ECC = _k("ecc", "string", ("error correction: L, M, Q, H", "корекція помилок: L, M, Q, H",
                              "коррекция ошибок: L, M, Q, H"), '"M"')
QR_MIN = _k("min_version", "int", ("smallest QR version, 1..40", "найменша версія QR, 1..40", "наименьшая версия QR, 1..40"),
            "1")
QR_MAX = _k("max_version", "int", ("largest QR version, 1..40", "найбільша версія QR, 1..40",
                                   "наибольшая версия QR, 1..40"), "40")
QR_ENCODING = _k("encoding", "string", ("bytes of the text: \"utf-8\" or \"cp1251\"",
                                        "байти тексту: \"utf-8\" або \"cp1251\"",
                                        "байты текста: \"utf-8\" или \"cp1251\""), '"utf-8"')


def _style_definer(name: str, kind: T) -> Function:
    return Function(name, "styles", "spec", "11.2",
                    (f"define a {kind[0]} style: name, parent=…, properties (11.3)",
                     f"визначити {kind[1]} стиль: ім'я, parent=…, властивості (11.3)",
                     f"определить {kind[2]} стиль: имя, parent=…, свойства (11.3)"),
                    (NAME, _k("parent", "style", ("parent style", "батьківський стиль", "родительский стиль")),
                     _k("**props", "any", ("properties of the kind: font_size=\"11pt\", space_after=\"6pt\"…",
                                           "властивості виду: font_size=\"11pt\", space_after=\"6pt\"…",
                                           "свойства вида: font_size=\"11pt\", space_after=\"6pt\"…"))),
                    "None", f'{name}("MyStyle", parent="…")', False, where="styles")


def _setting(name: str, section: str, text: T, keys: tuple[str, ...], example: str,
             lang_first: bool = False, doc: str = "spec") -> Function:
    args: tuple[Arg, ...] = (LANG_FIRST,) if lang_first else ()
    args += tuple(_k(key, "any", ("see section " + section, "див. розділ " + section, "см. раздел " + section))
                  for key in keys)
    return Function(name, "styles", doc, section, text, args, "None", example, False, where="styles")


def _method(receiver: str, name: str, text: T, args: tuple[Arg, ...], returns: str, example: str) -> Function:
    # In-place methods return None: their example is shown, not evaluated.
    return Function(name, "methods", "spec", "12.10", text, args, returns, example, returns != "None",
                    kind="method", receiver=receiver)


#: The note of every std/math name (decision 130): the console has ``math`` at once,
#: a document needs the import.
_MATH_NOTE = ('; in a document: |import("std/math")', '; у документі: |import("std/math")',
              '; в документе: |import("std/math")')


def _math_text(text: T) -> T:
    return tuple(part + note for part, note in zip(text, _MATH_NOTE))  # type: ignore[return-value]


def _math(name: str, text: T, arity: int = 1, returns: str = "float", example: str = "") -> Function:
    args = (X,) if arity == 1 else (_p("y", "number", ("y", "y", "y")), _p("x", "number", ("x", "x", "x")))
    return Function(name, "math", "stdlib", "9", _math_text(text), args, returns, example or f"math.{name}(2)",
                    module="std/math")


FUNCTIONS: tuple[Function, ...] = (
    # --- numbers (library 2, spec 12.4) --------------------------------------------------------
    _lib("num", "numbers", "2", ("number by the rules of the language: groups, decimal comma",
                                 "число за правилами мови: групи розрядів, кома",
                                 "число по правилам языка: группы разрядов, запятая"),
         (X, _p("digits", "int", ("digits after the comma", "знаків після коми", "знаков после запятой"), "None"),
          DIGITS, LANG), "str", "num(12500, digits=2)"),
    _lib("percent", "numbers", "2", ("percent with a no-break space: «20 %»", "відсоток з нерозривним пробілом: «20 %»",
                                     "процент с неразрывным пробелом: «20 %»"),
         (X, _p("digits", "int", ("digits after the comma", "знаків після коми", "знаков после запятой"), "None"),
          DIGITS, LANG), "str", "percent(20)"),
    _lib("round_to", "numbers", "2", ("round to a step, half away from zero", "округлити до кроку, половина від нуля",
                                      "округлить до шага, половина от нуля"),
         (X, _p("step", "number", ("step > 0", "крок > 0", "шаг > 0"))), "number", "round_to(1234, 50)"),
    _lib("ceil_to", "numbers", "2", ("round up to a step", "округлити до кроку вгору", "округлить до шага вверх"),
         (X, _p("step", "number", ("step > 0", "крок > 0", "шаг > 0"))), "number", "ceil_to(1201, 100)"),
    _lib("floor_to", "numbers", "2", ("round down to a step", "округлити до кроку вниз", "округлить до шага вниз"),
         (X, _p("step", "number", ("step > 0", "крок > 0", "шаг > 0"))), "number", "floor_to(1299, 100)"),
    _lib("round_money", "numbers", "2", ("round to hundredths, half away from zero",
                                         "округлити до сотих, половина від нуля",
                                         "округлить до сотых, половина от нуля"),
         (MONEY_X,), "decimal", "round_money(dec(\"10.005\"))"),
    _core("round", "numbers", "12.4", ("round, half away from zero; without ndigits — an integer",
                                       "округлити, половина від нуля; без ndigits — ціле",
                                       "округлить, половина от нуля; без ndigits — целое"),
          (X, _p("ndigits", "int", ("digits after the point", "знаків після крапки", "знаков после точки"), "None"),
           _k("ndigits", "int", ("digits after the point", "знаків після крапки", "знаков после точки"), "None")),
          "number", "round(2.675, 2)"),
    _core("abs", "numbers", "12.10", ("absolute value", "модуль числа", "модуль числа"), (X,), "number", "abs(-5)"),
    _core("min", "numbers", "12.10", ("smallest of the arguments or of a list", "найменше з аргументів або списку",
                                      "наименьшее из аргументов или списка"),
          (_p("*values", "any", ("values or one list", "значення або один список", "значения или один список")),
           _k("key", "function", ("key function", "функція ключа", "функция ключа")),
           _k("default", "any", ("value for an empty list", "значення для порожнього списку",
                                 "значение для пустого списка"))), "any", "min(3, 1, 2)"),
    _core("max", "numbers", "12.10", ("largest of the arguments or of a list", "найбільше з аргументів або списку",
                                      "наибольшее из аргументов или списка"),
          (_p("*values", "any", ("values or one list", "значення або один список", "значения или один список")),
           _k("key", "function", ("key function", "функція ключа", "функция ключа")),
           _k("default", "any", ("value for an empty list", "значення для порожнього списку",
                                 "значение для пустого списка"))), "any", "max([3, 1, 2])"),
    _core("sum", "numbers", "12.10", ("sum of a list", "сума списку", "сумма списка"),
          (SEQ, _p("start", "number", ("initial value", "початкове значення", "начальное значение"), "0"),
           _k("start", "number", ("initial value", "початкове значення", "начальное значение"), "0")),
          "number", "sum([1.50, 2.25])"),
    _core("dec", "numbers", "12.4", ("to decimal (from float — the shortest decimal form)",
                                     "у decimal (з float — найкоротший десятковий запис)",
                                     "в decimal (из float — кратчайшая десятичная запись)"),
          (VALUE,), "decimal", "dec(0.1)"),
    _core("float", "numbers", "12.4", ("to float; a datetime gives its serial number",
                                       "у float; datetime дає серійне число",
                                       "в float; datetime даёт серийное число"), (VALUE,), "float", "float(\"2.5\")"),
    _core("int", "numbers", "12.4", ("drop the fractional part (a decimal with scale 0)",
                                     "відкинути дробову частину (decimal з масштабом 0)",
                                     "отбросить дробную часть (decimal с масштабом 0)"), (VALUE,), "decimal", "int(7.9)"),
    # --- money and VAT (library 3) ---------------------------------------------------------------
    _lib("money", "money", "3", ("amount with the currency: «12 500,00 грн»", "сума з валютою: «12 500,00 грн»",
                                 "сумма с валютой: «12 500,00 грн»"),
         (MONEY_X, CODE, CURRENCY_STYLE, LANG), "str", 'money(12500, "UAH")'),
    _lib("money_words", "money", "3", ("amount in words", "сума прописом", "сумма прописью"),
         (MONEY_X, CODE, KOP, CAP, LANG), "str", 'money_words(12500, "UAH")'),
    _lib("money_full", "money", "3", ("amount in figures and in words in brackets (contract form)",
                                      "сума цифрами і прописом у дужках (договірна форма)",
                                      "сумма цифрами и прописью в скобках (договорная форма)"),
         (MONEY_X, CODE, KOP, CAP, CURRENCY_STYLE, LANG), "str", 'money_full(12500.50, "UAH")'),
    _lib("vat", "money", "3", ("tax on an amount without tax", "податок із суми без податку",
                               "налог с суммы без налога"), (MONEY_X, RATE), "decimal", "vat(1000, 20)"),
    _lib("with_vat", "money", "3", ("amount with tax", "сума з податком", "сумма с налогом"),
         (MONEY_X, RATE), "decimal", "with_vat(1000, 20)"),
    _lib("vat_in", "money", "3", ("tax contained in an amount with tax", "податок, що міститься в сумі з податком",
                                  "налог, содержащийся в сумме с налогом"),
         (MONEY_X, RATE), "decimal", "vat_in(1200, 20)"),
    _lib("without_vat", "money", "3", ("amount without tax from an amount with tax", "сума без податку із суми з податком",
                                       "сумма без налога из суммы с налогом"),
         (MONEY_X, RATE), "decimal", "without_vat(1200, 20)"),
    _lib("split", "money", "3", ("split an amount by shares; the parts add up to the total",
                                 "поділити суму за частками; частини дають суму",
                                 "разделить сумму по долям; части дают сумму"),
         (_p("total", "decimal", ("amount", "сума", "сумма")),
          _p("shares", "list", ("shares: [30, 70]", "частки: [30, 70]", "доли: [30, 70]"))), "list",
         "split(100, [1, 1, 1])"),
    # --- in words (library 4) ---------------------------------------------------------------------
    _lib("words", "words", "4", ("number in words; words(x, \"UAH\") — an amount",
                                 "число прописом; words(x, \"UAH\") — сума",
                                 "число прописью; words(x, \"UAH\") — сумма"),
         (X, _p("code", "string", ("currency code (as money_words)", "код валюти (як money_words)",
                                   "код валюты (как money_words)"), "None"), GENDER, CASE, LANG), "str", "words(21, gender=\"f\")"),
    _lib("ordinal", "words", "4", ("ordinal number in words", "порядковий числівник прописом",
                                   "порядковое числительное прописью"),
         (_p("n", "int", ("number 1 … 10¹⁵ − 1", "число 1 … 10¹⁵ − 1", "число 1 … 10¹⁵ − 1")), GENDER, CASE, LANG),
         "str", "ordinal(21, case=\"gen\")"),
    _lib("date_words", "words", "4", ("date in words", "дата прописом", "дата прописью"),
         (DT, LANG), "str", "date_words(date(2026, 10, 12))"),
    # --- dates (library 5, spec 12.3) --------------------------------------------------------------
    _core("date", "dates", "12.3", ("date: date(y, m, d) or date(\"YYYY-MM-DD\")",
                                    "дата: date(y, m, d) або date(\"YYYY-MM-DD\")",
                                    "дата: date(y, m, d) или date(\"YYYY-MM-DD\")"),
          (_p("y", "int", ("year or an ISO string", "рік або рядок ISO", "год или строка ISO")),
           _p("m", "int", ("month", "місяць", "месяц")), _p("d", "int", ("day", "день", "день"))),
          "datetime", "date(2026, 10, 12)"),
    _core("datetime", "dates", "12.3", ("moment: datetime(y, m, d, h, mi, s), an ISO string or a serial number",
                                        "момент: datetime(y, m, d, h, mi, s), рядок ISO або серійне число",
                                        "момент: datetime(y, m, d, h, mi, s), строка ISO или серийное число"),
          (_p("y", "int", ("year, ISO string or serial number", "рік, рядок ISO або серійне число",
                           "год, строка ISO или серийное число")),
           _p("m", "int", ("month", "місяць", "месяц")), _p("d", "int", ("day", "день", "день")),
           _p("h", "int", ("hour", "година", "час"), "0"), _p("mi", "int", ("minute", "хвилина", "минута"), "0"),
           _p("s", "int", ("second", "секунда", "секунда"), "0")), "datetime", "datetime(\"2026-10-12T14:30\")"),
    _core("build_date", "dates", "12.7", ("date of the build start (--build-date, build_date: of the project)",
                                          "дата початку збирання (--build-date, build_date: проєкту)",
                                          "дата начала сборки (--build-date, build_date: проекта)"),
          (), "datetime", "build_date()"),
    _lib("weeks", "dates", "5", ("number of days in n weeks: dt + weeks(2)", "кількість діб у n тижнях: dt + weeks(2)",
                                 "число суток в n неделях: dt + weeks(2)"), (N,), "number", "weeks(2)"),
    _lib("hours", "dates", "5", ("number of days in n hours: dt + hours(36)", "кількість діб у n годинах: dt + hours(36)",
                                 "число суток в n часах: dt + hours(36)"), (N,), "number", "hours(36)"),
    _lib("minutes", "dates", "5", ("number of days in n minutes", "кількість діб у n хвилинах",
                                   "число суток в n минутах"), (N,), "number", "date(2026, 10, 12) + minutes(90)"),
    _lib("add_months", "dates", "5", ("shift by months (31 → the last day of the month)",
                                      "зсув на місяці (31 → останній день місяця)",
                                      "сдвиг на месяцы (31 → последний день месяца)"),
         (DT, N), "datetime", "add_months(date(2026, 1, 31), 1)"),
    _lib("add_years", "dates", "5", ("shift by years", "зсув на роки", "сдвиг на годы"),
         (DT, N), "datetime", "add_years(date(2028, 2, 29), 1)"),
    _lib("fmt_date", "dates", "5", ("date as text: short, long, contract or a template (ДСТУ 4163:2020)",
                                    "дата текстом: short, long, contract або шаблон (ДСТУ 4163:2020)",
                                    "дата текстом: short, long, contract или шаблон (ДСТУ 4163:2020)"),
         (DT, FORMAT, LANG), "str", 'fmt_date(date(2026, 10, 12), "contract")'),
    _lib("fmt_time", "dates", "5", ("time as text: short or a template {hh}:{mi}", "час текстом: short або шаблон {hh}:{mi}",
                                    "время текстом: short или шаблон {hh}:{mi}"),
         (DT, _p("format", "string", ("\"short\" or a template", "\"short\" або шаблон", "\"short\" или шаблон"),
                 '"short"'), LANG), "str", 'fmt_time(datetime(2026, 10, 12, 14, 30, 0))'),
    _lib("fmt_datetime", "dates", "5", ("date and time as text", "дата й час текстом", "дата и время текстом"),
         (DT, FORMAT, LANG), "str", 'fmt_datetime(datetime(2026, 10, 12, 14, 30, 0), "long")'),
    _lib("weekday", "dates", "5", ("name of the day of the week (case nom or acc)", "назва дня тижня (відмінок nom або acc)",
                                   "название дня недели (падеж nom или acc)"),
         (DT, _k("case", "string", ("nom or acc", "nom або acc", "nom или acc"), '"nom"'), LANG), "str",
         "weekday(date(2026, 10, 12))"),
    _lib("month_name", "dates", "5", ("name of the month (case nom, gen, loc)", "назва місяця (відмінок nom, gen, loc)",
                                      "название месяца (падеж nom, gen, loc)"),
         (DT, _k("case", "string", ("nom, gen or loc", "nom, gen або loc", "nom, gen или loc"), '"nom"'), LANG), "str",
         'month_name(date(2026, 10, 12), case="gen")'),
    _lib("is_workday", "dates", "5", ("whether the day is a working day (by the calendar of the project)",
                                      "чи робочий день (за календарем проєкту)",
                                      "рабочий ли день (по календарю проекта)"),
         (DT, CALENDAR), "bool", "is_workday(date(2026, 10, 10))"),
    _lib("workdays", "dates", "5", ("the date n working days after dt (n < 0 — before)",
                                    "дата через n робочих днів після dt (n < 0 — до)",
                                    "дата через n рабочих дней после dt (n < 0 — до)"),
         (DT, N, CALENDAR), "datetime", "workdays(date(2026, 10, 9), 1)"),
    # --- units and lengths (library 6, spec 12.3) ------------------------------------------------
    _lib("qty", "units", "6", ("value with a unit: «230 В», tol= — tolerance", "значення з одиницею: «230 В», tol= — допуск",
                               "значение с единицей: «230 В», tol= — допуск"),
         (X, UNIT, _k("tol", "number", ("symmetric tolerance: (50 ± 1) Гц", "симетричний допуск: (50 ± 1) Гц",
                                        "симметричный допуск: (50 ± 1) Гц")), DIGITS, LANG), "str", 'qty(230, "V")'),
    _lib("qty_range", "units", "6", ("range with a unit: «100–240 В»", "діапазон з одиницею: «100–240 В»",
                                     "диапазон с единицей: «100–240 В»"),
         (_p("low", "number", ("lower bound", "нижня межа", "нижняя граница")),
          _p("high", "number", ("upper bound", "верхня межа", "верхняя граница")), UNIT, DIGITS, LANG), "str",
         'qty_range(-20, 55, "degC")'),
    _lib("convert", "units", "6", ("convert between units of one quantity", "перерахувати між одиницями однієї величини",
                                   "пересчитать между единицами одной величины"),
         (X, _p("from", "string", ("unit of x", "одиниця x", "единица x")),
          _p("to", "string", ("target unit", "цільова одиниця", "целевая единица"))), "number",
         'convert(1.5, "kW", "W")'),
    _core("length", "units", "12.3", ("length from a string: length(\"10mm\")", "довжина з рядка: length(\"10mm\")",
                                      "длина из строки: length(\"10mm\")"),
          (_p("text", "string", ("\"10mm\", \"2.5cm\", \"12pt\"", "\"10mm\", \"2.5cm\", \"12pt\"",
                                 "\"10mm\", \"2.5cm\", \"12pt\"")),), "length", 'length("10mm") + 5*mm'),
    *(Function(unit, "units", "spec", "12.3",
               (f"length constant: 10*{unit}", f"константа довжини: 10*{unit}", f"константа длины: 10*{unit}"),
               returns="length", example=f"10*{unit}", kind="constant") for unit in ("mm", "cm", "pt", "inch")),
    # --- text (library 7, spec 12.5) ---------------------------------------------------------------
    _lib("plural", "text", "7", ("word form by the number: plural(n, \"день\", \"дні\", \"днів\")",
                                 "форма слова за числом: plural(n, \"день\", \"дні\", \"днів\")",
                                 "форма слова по числу: plural(n, \"день\", \"дня\", \"дней\")"),
         (N, _p("*forms", "string", ("forms for 1, 2–4, 5+ (en: 1 and many)", "форми для 1, 2–4, 5+ (en: 1 і багато)",
                                     "формы для 1, 2–4, 5+ (en: 1 и много)")),
          _k("frac", "string", ("form for a fractional number", "форма для дробового числа", "форма для дробного числа")),
          LANG), "str", 'plural(5, "день", "дні", "днів", lang="uk")'),
    _lib("join_list", "text", "7", ("join a list: «А, Б та В»", "з'єднати список: «А, Б та В»",
                                    "соединить список: «А, Б и В»"),
         (_p("items", "list", ("list of strings", "список рядків", "список строк")),
          _k("last", "string", ("conjunction before the last item", "сполучник перед останнім", "союз перед последним")),
          _k("sep", "string", ("separator", "роздільник", "разделитель"), '", "'), LANG), "str",
         'join_list(["А", "Б", "В"], last="та")'),
    _lib("cap", "text", "7", ("capital first letter", "велика перша літера", "заглавная первая буква"),
         (S,), "str", 'cap("київ")'),
    _lib("translit", "text", "7", ("transliteration (uk — КМУ № 55, ru — ICAO Doc 9303)",
                                   "транслітерація (uk — постанова КМУ № 55, ru — ICAO Doc 9303)",
                                   "транслитерация (uk — постановление КМУ № 55, ru — ICAO Doc 9303)"),
         (S, LANG), "str", 'translit("Згорани", lang="uk")'),
    _lib("sort_key", "text", "7", ("sort key by the alphabet of the language: sorted(names, key=sort_key)",
                                   "ключ сортування за абеткою мови: sorted(names, key=sort_key)",
                                   "ключ сортировки по алфавиту языка: sorted(names, key=sort_key)"),
         (S, LANG), "any", 'sorted(["Ґава", "Гора", "Єва", "Есе"], key=sort_key)'),
    _lib("nbsp_short", "text", "7", ("no-break space after short prepositions and conjunctions",
                                     "нерозривний пробіл після коротких прийменників і сполучників",
                                     "неразрывный пробел после коротких предлогов и союзов"),
         (S, LANG), "str", 'nbsp_short("в домі та у дворі", lang="uk")'),
    _core("str", "text", "12.10", ("value as a string (dates — ISO, numbers — with a point)",
                                   "значення рядком (дати — ISO, числа — з крапкою)",
                                   "значение строкой (даты — ISO, числа — с точкой)"), (VALUE,), "str", "str(2.20)"),
    _core("repr", "text", "12.10", ("value as code", "значення у вигляді коду", "значение в виде кода"),
          (VALUE,), "str", 'repr("a")'),
    # --- lists and records (spec 12.10, 12.6) ------------------------------------------------------
    _core("len", "collections", "12.10", ("length: characters, items, keys", "довжина: символи, елементи, ключі",
                                          "длина: символы, элементы, ключи"), (SEQ,), "decimal", 'len("Київ")'),
    _core("range", "collections", "12.10", ("numbers from start to stop (not included) with a step",
                                            "числа від start до stop (не включно) з кроком",
                                            "числа от start до stop (не включительно) с шагом"),
          (_p("start", "int", ("start (or stop alone)", "початок (або лише stop)", "начало (или только stop)")),
           _p("stop", "int", ("stop", "кінець", "конец")), _p("step", "int", ("step", "крок", "шаг"), "1")), "list",
          "range(1, 10, 3)"),
    _core("enumerate", "collections", "12.10", ("pairs (number, item)", "пари (номер, елемент)", "пары (номер, элемент)"),
          (SEQ, _p("start", "int", ("first number", "перший номер", "первый номер"), "0"),
           _k("start", "int", ("first number", "перший номер", "первый номер"), "0")), "list",
          'enumerate(["a", "b"], start=1)'),
    _core("zip", "collections", "12.10", ("tuples of items with the same index", "кортежі елементів з однаковим індексом",
                                          "кортежи элементов с одинаковым индексом"),
          (_p("*lists", "list", ("lists", "списки", "списки")),), "list", "zip([1, 2], [\"a\", \"b\"])"),
    _core("sorted", "collections", "12.10", ("sorted list", "відсортований список", "отсортированный список"),
          (SEQ, _k("key", "function", ("key function: sort_key, a field…", "функція ключа: sort_key, поле…",
                                       "функция ключа: sort_key, поле…")),
           _k("reverse", "bool", ("descending", "за спаданням", "по убыванию"), "False")), "list", "sorted([3, 1, 2])"),
    _core("reversed", "collections", "12.10", ("list in reverse order", "список у зворотному порядку",
                                               "список в обратном порядке"), (SEQ,), "list", "reversed([1, 2, 3])"),
    _core("any", "collections", "12.10", ("whether at least one item is true", "чи є хоч один істинний елемент",
                                          "есть ли хоть один истинный элемент"), (SEQ,), "bool", "any([0, 1])"),
    _core("all", "collections", "12.10", ("whether all items are true", "чи всі елементи істинні",
                                          "все ли элементы истинны"), (SEQ,), "bool", "all([1, 2])"),
    _core("list", "collections", "12.10", ("a list (of a sequence)", "список (з послідовності)",
                                           "список (из последовательности)"), (SEQ,), "list", 'list("abc")'),
    _core("tuple", "collections", "12.10", ("a tuple", "кортеж", "кортеж"), (SEQ,), "tuple", "tuple([1, 2])"),
    _core("dict", "collections", "12.10", ("a dictionary: from pairs, a record or key=value",
                                           "словник: з пар, запису або key=value",
                                           "словарь: из пар, записи или key=value"),
          (_p("source", "any", ("pairs, dict or record", "пари, словник або запис", "пары, словарь или запись"), "None"),
           _k("**items", "any", ("keys and values", "ключі й значення", "ключи и значения"))), "dict",
          'dict(a=1, b=2)'),
    _core("record", "collections", "12.6", ("a record with access through a point: r.name",
                                            "запис з доступом через крапку: r.name",
                                            "запись с доступом через точку: r.name"),
          (_p("source", "any", ("dict or record", "словник або запис", "словарь или запись"), "None"),
           _k("**fields", "any", ("fields", "поля", "поля"))), "record", 'record(name="Кабель", qty=3)'),
    _core("bool", "collections", "12.10", ("truth value", "логічне значення", "логическое значение"),
          (VALUE,), "bool", 'bool("")'),
    _core("getattr", "collections", "12.6", ("field of a record by name, with a default",
                                             "поле запису за ім'ям, зі значенням за замовчуванням",
                                             "поле записи по имени, со значением по умолчанию"),
          (_p("r", "record", ("record", "запис", "запись")), _p("name", "string", ("field name", "ім'я поля", "имя поля")),
           _p("default", "any", ("value when there is no field", "значення, якщо поля немає",
                                 "значение, если поля нет"))), "any", 'getattr(record(a=1), "b", 0)'),
    _core("hasattr", "collections", "12.6", ("whether a record has a field", "чи має запис поле", "есть ли у записи поле"),
          (_p("r", "record", ("record", "запис", "запись")), _p("name", "string", ("field name", "ім'я поля", "имя поля"))),
          "bool", 'hasattr(record(a=1), "a")'),
    _core("type", "collections", "12.3", ("name of the type: \"decimal\", \"str\", \"datetime\"…",
                                          "ім'я типу: \"decimal\", \"str\", \"datetime\"…",
                                          "имя типа: \"decimal\", \"str\", \"datetime\"…"), (VALUE,), "str", "type(1.5e3)"),
    # --- data (library 8, spec 10.5) -----------------------------------------------------------------
    _lib("group_by", "data", "8", ("dictionary «key value → list of records»", "словник «значення ключа → список записів»",
                                   "словарь «значение ключа → список записей»"),
         (ITEMS, KEY_FIELD), "dict", 'group_by([record(k="a", v=1), record(k="a", v=2)], "k")'),
    _lib("sum_by", "data", "8", ("sums of a field by groups", "суми поля за групами", "суммы поля по группам"),
         (ITEMS, KEY_FIELD, _p("value", "any", ("field to sum or function", "поле для суми або функція",
                                                "поле для суммы или функция"))), "dict",
         'sum_by([record(k="a", v=1), record(k="a", v=2)], "k", "v")'),
    _lib("distinct", "data", "8", ("unique values of a field", "унікальні значення поля", "уникальные значения поля"),
         (ITEMS, KEY_FIELD), "list", 'distinct([record(k="a"), record(k="b"), record(k="a")], "k")'),
    _core("load_csv", "data", "10.5", ("rows of a CSV file as records", "рядки файлу CSV як записи",
                                       "строки файла CSV как записи"),
          (PATH, _k("types", "dict", ("column types: {\"qty\": \"decimal\"}", "типи стовпців: {\"qty\": \"decimal\"}",
                                      "типы столбцов: {\"qty\": \"decimal\"}")),
           _k("sep", "string", ("separator \",\" or \";\"", "роздільник \",\" або \";\"", "разделитель \",\" или \";\""))),
          "list", 'load_csv("data/items.csv")', False),
    _core("load_yaml", "data", "10.5", ("data of a YAML file (records and lists)", "дані файлу YAML (записи й списки)",
                                        "данные файла YAML (записи и списки)"), (PATH,), "any",
          'load_yaml("data/order.yaml")', False),
    _core("load_json", "data", "10.5", ("data of a JSON file", "дані файлу JSON", "данные файла JSON"), (PATH,), "any",
          'load_json("data/order.json")', False),
    _core("load_text", "data", "10.5", ("the whole text file as a string (UTF-8; e.g. SVG for |img(svg=…))",
                                        "увесь текстовий файл як рядок (UTF-8; наприклад, SVG для |img(svg=…))",
                                        "весь текстовый файл как строка (UTF-8; например, SVG для |img(svg=…))"),
          (PATH,), "str", 'load_text("img/sign.svg")', False),
    *(_core(name, "data", "10.5", (f"rows of a sheet of an {kind} file as records (saved results of formulas)",
                                   f"рядки аркуша файлу {kind} як записи (збережені результати формул)",
                                   f"строки листа файла {kind} как записи (сохранённые результаты формул)"),
            (PATH, SHEET, SHEET_RANGE, SHEET_HEADER,
             _k("types", "dict", ("column types as in load_csv", "типи стовпців, як у load_csv",
                                  "типы столбцов, как в load_csv"))),
            "list", f'{name}("data/items.{kind.lower()}", sheet="Позиції")', False)
      for name, kind in (("load_ods", "ODS"), ("load_xlsx", "XLSX"))),
    # --- std/math (library 9) -------------------------------------------------------------------------
    _math("sqrt", ("square root", "квадратний корінь", "квадратный корень")),
    _math("exp", ("e to the power x", "e в степені x", "e в степени x"), example="math.exp(1)"),
    _math("log", ("natural logarithm", "натуральний логарифм", "натуральный логарифм"), example="math.log(math.e)"),
    _math("log10", ("decimal logarithm", "десятковий логарифм", "десятичный логарифм"), example="math.log10(1000)"),
    _math("sin", ("sine (radians)", "синус (радіани)", "синус (радианы)"), example="math.sin(math.pi / 2)"),
    _math("cos", ("cosine (radians)", "косинус (радіани)", "косинус (радианы)"), example="math.cos(0)"),
    _math("tan", ("tangent (radians)", "тангенс (радіани)", "тангенс (радианы)"), example="math.tan(0)"),
    _math("atan2", ("angle of the point (x, y), radians", "кут точки (x, y), радіани", "угол точки (x, y), радианы"),
          2, example="math.atan2(1, 1)"),
    _math("floor", ("round down to an integer (decimal)", "округлити вниз до цілого (decimal)",
                    "округлить вниз до целого (decimal)"), returns="decimal", example="math.floor(-2.5)"),
    _math("ceil", ("round up to an integer (decimal)", "округлити вгору до цілого (decimal)",
                   "округлить вверх до целого (decimal)"), returns="decimal", example="math.ceil(2.1)"),
    Function("pi", "math", "stdlib", "9", _math_text(("the number π (float)", "число π (float)", "число π (float)")),
             returns="float", example="math.pi", kind="constant", module="std/math"),
    Function("e", "math", "stdlib", "9", _math_text(("the number e (float)", "число e (float)", "число e (float)")),
             returns="float", example="math.e", kind="constant", module="std/math"),
    # --- QR codes and encodings (library 10, decision 137) ------------------------------------------------
    _lib("qr_matrix", "codes", "10", ("QR code of a text (byte mode): {version, ecc, mask, size, rows}",
                                      "QR-код тексту (байтовий режим): {version, ecc, mask, size, rows}",
                                      "QR-код текста (байтовый режим): {version, ecc, mask, size, rows}"),
         (QR_DATA, QR_ECC, QR_MIN, QR_MAX, QR_ENCODING), "record", 'qr_matrix("https://primula.example").version'),
    _lib("qr_svg", "codes", "10", ("QR code as SVG for |img(svg=…); circle= leaves a white circle in the centre",
                                   "QR-код як SVG для |img(svg=…); circle= лишає біле коло в центрі",
                                   "QR-код как SVG для |img(svg=…); circle= оставляет белый круг в центре"),
         (QR_DATA, QR_ECC, QR_MIN, QR_MAX, QR_ENCODING,
          _k("size", "length", ("width and height of the image", "ширина й висота зображення",
                                "ширина и высота изображения"), '"30mm"'),
          _k("quiet", "int", ("quiet zone in modules", "тиха зона в модулях", "тихая зона в модулях"), "4"),
          _k("circle", "int", ("diameter of the white circle in modules, 0 — none", "діаметр білого кола в модулях, 0 — немає",
                               "диаметр белого круга в модулях, 0 — нет"), "0")), "str",
         'len(qr_svg("https://primula.example")) > 0'),
    _lib("base64url", "codes", "10", ("Base64URL of the bytes of a text, without = padding",
                                      "Base64URL байтів тексту, без доповнення =",
                                      "Base64URL байтов текста, без дополнения ="),
         (_p("text", "string", ("text", "текст", "текст")), QR_ENCODING), "str", 'base64url("Київ")'),
    # --- checks and the document (spec 12.9, 9.2, 4.2, 8.6, 6.3) ---------------------------------------
    _core("fail", "core", "12.9", ("stop the build with an error at this place", "зупинити збирання з помилкою в цьому місці",
                                   "остановить сборку с ошибкой в этом месте"),
          (_p("*message", "any", ("message", "повідомлення", "сообщение")),), "None", 'fail("no price")', False),
    _core("debug", "core", "12.9", ("write values into the build report, not into the document",
                                    "записати значення у звіт збирання, а не в документ",
                                    "записать значения в отчёт сборки, а не в документ"),
          (_p("*values", "any", ("values", "значення", "значения")),), "None", "debug(total)", False),
    _core("has", "core", "9.2", ("whether the product variant has a feature (keys: of the project, --feature)",
                                 "чи має варіант виробу функцію (keys: проєкту, --feature)",
                                 "есть ли у варианта изделия функция (keys: проекта, --feature)"),
          (_p("feature", "string", ("feature name", "назва функції", "название функции")),), "bool", 'has("wifi")', False),
    _core("markup", "core", "4.2", ("Primula markup from a string (content)", "розмітка Primula з рядка (content)",
                                    "разметка Primula из строки (content)"),
          (_p("text", "string", ("markup text", "текст розмітки", "текст разметки")),), "content",
          'markup("|*{" + name + "}")', False),
    _core("img", "core", "8.6", ("image value for watermark=, |img(value), |figure(value); a path or svg=",
                                 "значення-зображення для watermark=, |img(значення), |figure(значення); шлях або svg=",
                                 "значение-изображение для watermark=, |img(значение), |figure(значение); путь или svg="),
          (PATH, _k("svg", "string", ("SVG text computed by code instead of a path",
                                      "текст SVG, обчислений кодом, замість шляху",
                                      "текст SVG, вычисленный кодом, вместо пути")),
           _k("**options", "any", ("width=, height=…", "width=, height=…", "width=, height=…"))), "record",
          'img("assets/stamp.png")', False),
    _core("col", "core", "6.3", ("table column: col(width, id=…, type=…, align=…)",
                                 "стовпець таблиці: col(width, id=…, type=…, align=…)",
                                 "столбец таблицы: col(width, id=…, type=…, align=…)"),
          (_p("width", "string", ("\"30mm\", \"20mm..60mm\", \"*\", \"auto\"", "\"30mm\", \"20mm..60mm\", \"*\", \"auto\"",
                                  "\"30mm\", \"20mm..60mm\", \"*\", \"auto\"")),
           _k("id", "string", ("column id for formulas", "id стовпця для формул", "id столбца для формул")),
           _k("type", "string", ("str, decimal, money, float, datetime, bool", "str, decimal, money, float, datetime, bool",
                                 "str, decimal, money, float, datetime, bool")),
           _k("**props", "any", ("align=, valign=, currency=, digits=, paragraph=… (6.6)",
                                 "align=, valign=, currency=, digits=, paragraph=… (6.6)",
                                 "align=, valign=, currency=, digits=, paragraph=… (6.6)"))), "record",
          'col("20mm..35mm", id="sum", type="money", align="right")', False),
    _core("track", "core", "7.7", ("track of |parallel: track(id, lang=…, title=…, width=…, primary=…)",
                                   "потік |parallel: track(id, lang=…, title=…, width=…, primary=…)",
                                   "поток |parallel: track(id, lang=…, title=…, width=…, primary=…)"),
          (_p("id", "string", ("track id", "id потоку", "id потока")),
           _k("lang", "string", ("language of the track: library, quotes, spelling", "мова потоку: бібліотека, лапки, орфографія",
                                 "язык потока: библиотека, кавычки, орфография")),
           _k("title", "string", ("title in the row of track titles", "назва в рядку назв потоків",
                                  "название в строке названий потоков")),
           _k("**props", "any", ("width=, block=, role=, primary=, numbered=, optional= (7.7)",
                                 "width=, block=, role=, primary=, numbered=, optional= (7.7)",
                                 "width=, block=, role=, primary=, numbered=, optional= (7.7)"))), "record",
          'track("note", title="Коментар", width="28%", numbered=False, optional=True)', False),
    # --- table formulas (spec 6.8) -----------------------------------------------------------------------
    _core("this_row", "tables", "6.8", ("value in column c of the current row", "значення в стовпці c поточного рядка",
                                        "значение в столбце c текущей строки"), (COLUMN,), "any",
          'this_row("qty") * this_row("price")', False, where="cell"),
    _core("cell", "tables", "6.8", ("value of a cell", "значення клітинки", "значение ячейки"),
          (_p("r", "int", ("row number from 1", "номер рядка з 1", "номер строки с 1")), COLUMN), "any",
          'cell(2, "sum")', False, where="cell"),
    _core("column", "tables", "6.8", ("list of the values of a column (body rows or rows=)",
                                      "список значень стовпця (рядки тіла або rows=)",
                                      "список значений столбца (строки тела или rows=)"),
          (COLUMN, _k("rows", "list", ("row numbers or range", "номери рядків або range", "номера строк или range"))),
          "list", 'sum(column("sum"))', False, where="cell"),
    _core("body_rows", "tables", "6.8", ("numbers of the rows between the header and the totals",
                                         "номери рядків між заголовком і підсумками",
                                         "номера строк между заголовком и итогами"), (), "list", "body_rows()",
          False, where="cell"),
    _core("avg", "tables", "6.8", ("average of a list", "середнє значення списку", "среднее значение списка"),
          (SEQ,), "number", 'avg(column("qty"))', False, where="cell"),
    _core("count", "tables", "6.8", ("number of non-empty values", "кількість непорожніх значень",
                                     "количество непустых значений"), (SEQ,), "decimal", 'count(column("qty"))',
          False, where="cell"),
    # --- styles code (spec 11, settings of 4–9) ----------------------------------------------------------
    _style_definer("paragraph_style", ("paragraph", "абзацний", "абзацный")),
    _style_definer("character_style", ("character", "символьний", "символьный")),
    _style_definer("block_style", ("block", "блоковий", "блочный")),
    _style_definer("table_style", ("table", "табличний", "табличный")),
    _style_definer("list_style", ("list", "списковий", "списочный")),
    _style_definer("frame_style", ("frame", "фреймовий", "фреймовый")),
    _style_definer("page_style", ("page", "сторінковий", "страничный")),
    Function("derive", "styles", "spec", "11.4", ("derived style: its deterministic name for |.(…)",
                                                  "похідний стиль: його детерміноване ім'я для |.(…)",
                                                  "производный стиль: его детерминированное имя для |.(…)"),
             (_p("base", "style", ("base style", "базовий стиль", "базовый стиль")),
              _k("name", "string", ("explicit name", "явне ім'я", "явное имя")),
              _k("**props", "any", ("changed properties", "змінені властивості", "изменённые свойства"))), "str",
             'derive("Clause", left="10mm")', False),
    _setting("structure_styles", "11.5", ("styles of structure constructs: paragraph=, heading=, clause=…",
                                          "стилі конструкцій структури: paragraph=, heading=, clause=…",
                                          "стили конструкций структуры: paragraph=, heading=, clause=…"),
             (), 'structure_styles(paragraph="Body")'),
    _setting("structure_profile", "5.1", ("structure profile: \"business\" or \"report\"",
                                          "профіль структури: \"business\" або \"report\"",
                                          "профиль структуры: \"business\" или \"report\""), (),
             'structure_profile("business")'),
    _setting("numbering", "5.2", ("numbering of headings, clauses, figures and tables",
                                  "нумерація заголовків, пунктів, рисунків і таблиць",
                                  "нумерация заголовков, пунктов, рисунков и таблиц"),
             ("headings", "heading_format", "clause_format", "figures", "tables", "ref_format"),
             'numbering(figures="by_chapter")'),
    _setting("captions", "5.8", ("caption words of figures and tables", "слова підписів рисунків і таблиць",
                                 "слова подписей рисунков и таблиц"), ("figure", "table"),
             'captions("uk", figure="Рисунок", table="Таблиця")', True),
    _setting("appendices", "5.9", ("designation and layout of appendices", "позначення й оформлення додатків",
                                   "обозначение и оформление приложений"),
             ("designation", "numbering", "letters", "page_break", "toc", "title_format"),
             'appendices("uk", designation="ДОДАТОК")', True),
    _setting("ref_labels", "5.7", ("words of references |@(id, \"label\")", "слова посилань |@(id, \"label\")",
                                   "слова ссылок |@(id, \"label\")"), (), 'ref_labels("uk", clause="п.")', True),
    _setting("footnotes", "5.10", ("numbering and separator of footnotes", "нумерація й роздільник виносок",
                                   "нумерация и разделитель сносок"),
             ("numbering", "restart", "format", "separator"), 'footnotes(restart="page")'),
    _setting("abbreviations", "9.4", ("first use and sorting of abbreviations", "перше вживання й сортування скорочень",
                                      "первое употребление и сортировка сокращений"), ("first", "sort"),
             'abbreviations(first="expand")'),
    _setting("typography", "7", ("typography: percent_space, nbsp_short, nbsp_words",
                                 "типографіка: percent_space, nbsp_short, nbsp_words",
                                 "типографика: percent_space, nbsp_short, nbsp_words"),
             ("percent_space", "nbsp_short", "nbsp_words"), "typography(nbsp_short=True)", doc="stdlib"),
    _setting("admonition_symbols", "9.1", ("safety sign images of admonitions", "зображення знаків безпеки попереджень",
                                           "изображения знаков безопасности предупреждений"),
             ("danger", "warning", "caution", "notice", "note", "tip"),
             'admonition_symbols(danger="assets/signs/w012.svg")'),
    _setting("admonition_words", "9.1", ("signal words of admonitions", "сигнальні слова попереджень",
                                         "сигнальные слова предупреждений"),
             ("danger", "warning", "caution", "notice", "note", "tip", "notes"),
             'admonition_words("uk", danger="НЕБЕЗПЕКА")', True),
    _setting("review_marks", "9.2", ("texts of the --review marks and watermark", "тексти позначок і водяного знака --review",
                                     "тексты пометок и водяного знака --review"), ("true", "false", "watermark"),
             'review_marks("uk", watermark="НЕ ДЛЯ ВИПУСКУ")', True),
    _setting("watermark", "8.6", ("watermark on the page styles", "водяний знак на стилях сторінок",
                                  "водяной знак на стилях страниц"), (), 'watermark("ПРОЄКТ")'),
    _setting("header", "7.6", ("header of a page style", "верхній колонтитул стилю сторінки",
                               "верхний колонтитул стиля страницы"), (), 'header("Portrait", markup("…"))'),
    _setting("footer", "7.6", ("footer of a page style", "нижній колонтитул стилю сторінки",
                               "нижний колонтитул стиля страницы"), (), 'footer("Portrait", markup("…"))'),
    _setting("placeholders", "4.2", ("|?{…} placeholders: \"mark\" (draft) or \"final\"",
                                     "заповнювачі |?{…}: \"mark\" (чернетка) або \"final\"",
                                     "заполнители |?{…}: \"mark\" (черновик) или \"final\""), (),
             'placeholders("final")'),
    _setting("quotes", "4.2", ("quotation marks of a language for |\"{…}", "лапки мови для |\"{…}",
                               "кавычки языка для |\"{…}"), (), 'quotes("de", ("„", "“"), ("‚", "‘"))'),
    Function("currency", "styles", "stdlib", "1", ("add or change a currency of the library", "додати або змінити валюту бібліотеки",
                                                   "добавить или изменить валюту библиотеки"),
             (CODE, LANG_FIRST, *(_k(key, "any", ("see library section 1", "див. розділ 1 бібліотеки",
                                                  "см. раздел 1 библиотеки"))
                                  for key in ("short", "units", "frac", "gender", "minor", "minor_gender", "minor_digits"))),
             "None", 'currency("PLN", "uk", short="zł")', False, where="styles"),
    Function("unit", "styles", "stdlib", "1", ("add or change a unit of the library", "додати або змінити одиницю бібліотеки",
                                               "добавить или изменить единицу библиотеки"),
             (UNIT, LANG_FIRST, *(_k(key, "any", ("see library section 1", "див. розділ 1 бібліотеки",
                                                  "см. раздел 1 библиотеки"))
                                  for key in ("symbol", "quantity", "factor", "offset"))),
             "None", 'unit("rpm", "uk", symbol="об/хв", quantity="frequency", factor=1/60)', False, where="styles"),
    Function("month_names", "styles", "stdlib", "1", ("names of the months of a language", "назви місяців мови",
                                                      "названия месяцев языка"),
             (LANG_FIRST, *(_k(key, "list", ("12 names", "12 назв", "12 названий")) for key in ("nom", "gen", "loc"))),
             "None", 'month_names("uk", gen=["січня", …])', False, where="styles"),
    # --- project (spec 10.7) ------------------------------------------------------------------------------
    _core("build", "project", "10.7", ("register a build target of the project", "зареєструвати ціль збирання проєкту",
                                       "зарегистрировать цель сборки проекта"),
          (_p("source", "path", ("document", "документ", "документ")),
           _k("output", "path", ("ODT file (required)", "файл ODT (обов'язково)", "файл ODT (обязательно)")),
           _k("params", "dict", ("parameters of the document", "параметри документа", "параметры документа")),
           _k("keys", "dict", ("keys of the key map", "ключі карти ключів", "ключи карты ключей")),
           _k("pdf", "bool", ("also export PDF", "також експортувати PDF", "также экспортировать PDF"))), "None",
          'build("act.prml", params=row, output=f"out/act-{row.no}.odt")', False, where="project"),
    _core("batch_mode", "project", "10.6", ("True while the whole project is built", "True під час збирання всього проєкту",
                                            "True во время сборки всего проекта"), (), "bool", "batch_mode()",
          False, where="project"),
    # --- methods (spec 12.10) -------------------------------------------------------------------------------
    *(_method("str", name, text, args, returns, example) for name, text, args, returns, example in (
        ("split", ("split by a separator (by spaces without it)", "розбити за роздільником (без нього — за пробілами)",
                   "разбить по разделителю (без него — по пробелам)"),
         (_p("sep", "string", ("separator", "роздільник", "разделитель"), "None"),
          _p("maxsplit", "int", ("at most splits", "щонайбільше розбиттів", "не более разбиений"), "-1")), "list",
         '"a, b".split(", ")'),
        ("rsplit", ("split from the right", "розбити справа", "разбить справа"),
         (_p("sep", "string", ("separator", "роздільник", "разделитель"), "None"),
          _p("maxsplit", "int", ("at most splits", "щонайбільше розбиттів", "не более разбиений"), "-1")), "list",
         '"a.b.c".rsplit(".", 1)'),
        ("splitlines", ("list of lines", "список рядків", "список строк"),
         (_p("keepends", "bool", ("keep line ends", "зберегти кінці рядків", "сохранить концы строк"), "False"),), "list",
         '"a\\nb".splitlines()'),
        ("join", ("join strings with this string between them", "з'єднати рядки цим рядком",
                  "соединить строки этой строкой"),
         (_p("items", "list", ("strings", "рядки", "строки")),), "str", '", ".join(["a", "b"])'),
        ("strip", ("without spaces (or the characters) at both ends", "без пробілів (або символів) з обох кінців",
                   "без пробелов (или символов) с обоих концов"),
         (_p("chars", "string", ("characters", "символи", "символы"), "None"),), "str", '"  a ".strip()'),
        ("lstrip", ("without spaces at the start", "без пробілів на початку", "без пробелов в начале"),
         (_p("chars", "string", ("characters", "символи", "символы"), "None"),), "str", '"  a".lstrip()'),
        ("rstrip", ("without spaces at the end", "без пробілів у кінці", "без пробелов в конце"),
         (_p("chars", "string", ("characters", "символи", "символы"), "None"),), "str", '"a  ".rstrip()'),
        ("replace", ("replace a substring", "замінити підрядок", "заменить подстроку"),
         (_p("old", "string", ("what", "що", "что")), _p("new", "string", ("with what", "чим", "чем")),
          _p("count", "int", ("at most times", "щонайбільше разів", "не более раз"), "-1")), "str", '"a-b".replace("-", "/")'),
        ("startswith", ("whether it starts with a prefix", "чи починається з префікса", "начинается ли с префикса"),
         (_p("prefix", "string", ("prefix or tuple", "префікс або кортеж", "префикс или кортеж")),), "bool",
         '"ДСТУ 3008".startswith("ДСТУ")'),
        ("endswith", ("whether it ends with a suffix", "чи закінчується суфіксом", "заканчивается ли суффиксом"),
         (_p("suffix", "string", ("suffix or tuple", "суфікс або кортеж", "суффикс или кортеж")),), "bool",
         '"act.prml".endswith(".prml")'),
        ("find", ("index of a substring or −1", "індекс підрядка або −1", "индекс подстроки или −1"),
         (_p("sub", "string", ("substring", "підрядок", "подстрока")), _p("start", "int", ("from", "від", "от"), "None"),
          _p("end", "int", ("to", "до", "до"), "None")), "decimal", '"abc".find("c")'),
        ("rfind", ("index of the last occurrence or −1", "індекс останнього входження або −1",
                   "индекс последнего вхождения или −1"),
         (_p("sub", "string", ("substring", "підрядок", "подстрока")), _p("start", "int", ("from", "від", "от"), "None"),
          _p("end", "int", ("to", "до", "до"), "None")), "decimal", '"abca".rfind("a")'),
        ("count", ("number of occurrences", "кількість входжень", "количество вхождений"),
         (_p("sub", "string", ("substring", "підрядок", "подстрока")), _p("start", "int", ("from", "від", "от"), "None"),
          _p("end", "int", ("to", "до", "до"), "None")), "decimal", '"banana".count("a")'),
        ("upper", ("upper case", "великими літерами", "заглавными буквами"), (), "str", '"київ".upper()'),
        ("lower", ("lower case", "малими літерами", "строчными буквами"), (), "str", '"КИЇВ".lower()'),
        ("capitalize", ("first letter capital, the rest small", "перша велика, решта малі",
                        "первая заглавная, остальные строчные"), (), "str", '"кИЇВ".capitalize()'),
        ("title", ("each word with a capital letter", "кожне слово з великої", "каждое слово с заглавной"), (), "str",
         '"нова пошта".title()'),
        ("isdigit", ("whether only digits", "чи лише цифри", "только ли цифры"), (), "bool", '"2026".isdigit()'),
        ("isalpha", ("whether only letters", "чи лише літери", "только ли буквы"), (), "bool", '"Київ".isalpha()'),
        ("isspace", ("whether only spaces", "чи лише пробіли", "только ли пробелы"), (), "bool", '" ".isspace()'),
        ("zfill", ("pad with zeros on the left", "доповнити нулями зліва", "дополнить нулями слева"),
         (_p("width", "int", ("width", "ширина", "ширина")),), "str", '"7".zfill(3)'),
        ("format", ("substitute values: \"{0} — {name}\"", "підставити значення: \"{0} — {name}\"",
                    "подставить значения: \"{0} — {name}\""),
         (_p("*args", "any", ("values", "значення", "значения")),
          _k("**kwargs", "any", ("named values", "іменовані значення", "именованные значения"))), "str",
         '"{0} шт.".format(3)'),
    )),
    *(_method("list", name, text, args, returns, example) for name, text, args, returns, example in (
        ("append", ("add an item (inside functions)", "додати елемент (усередині функцій)",
                    "добавить элемент (внутри функций)"), (VALUE,), "None", "[1].append(2)"),
        ("extend", ("add the items of a list", "додати елементи списку", "добавить элементы списка"),
         (SEQ,), "None", "[1].extend([2, 3])"),
        ("insert", ("insert an item at an index", "вставити елемент за індексом", "вставить элемент по индексу"),
         (_p("i", "int", ("index", "індекс", "индекс")), VALUE), "None", "[1].insert(0, 0)"),
        ("pop", ("remove and return an item (the last one)", "вилучити й повернути елемент (останній)",
                 "удалить и вернуть элемент (последний)"),
         (_p("i", "int", ("index", "індекс", "индекс"), "-1"),), "any", "[1, 2].pop()"),
        ("remove", ("remove the first equal item", "вилучити перший рівний елемент", "удалить первый равный элемент"),
         (VALUE,), "None", "[1, 2].remove(1)"),
        ("index", ("index of an item", "індекс елемента", "индекс элемента"), (VALUE,), "decimal", '["a", "b"].index("b")'),
        ("count", ("number of equal items", "кількість рівних елементів", "количество равных элементов"),
         (VALUE,), "decimal", "[1, 1, 2].count(1)"),
        ("sort", ("sort in place", "відсортувати на місці", "отсортировать на месте"),
         (_k("key", "function", ("key function", "функція ключа", "функция ключа")),
          _k("reverse", "bool", ("descending", "за спаданням", "по убыванию"), "False")), "None", "[2, 1].sort()"),
        ("reverse", ("reverse in place", "обернути на місці", "обратить на месте"), (), "None", "[1, 2].reverse()"),
    )),
    *(_method("dict", name, text, args, returns, example) for name, text, args, returns, example in (
        ("get", ("value by a key or a default", "значення за ключем або типове", "значение по ключу или по умолчанию"),
         (_p("key", "any", ("key", "ключ", "ключ")), _p("default", "any", ("default", "типове", "по умолчанию"), "None")),
         "any", '{"a": 1}.get("b", 0)'),
        ("keys", ("list of the keys", "список ключів", "список ключей"), (), "list", '{"a": 1}.keys()'),
        ("values", ("list of the values", "список значень", "список значений"), (), "list", '{"a": 1}.values()'),
        ("items", ("pairs (key, value)", "пари (ключ, значення)", "пары (ключ, значение)"), (), "list",
         '{"a": 1}.items()'),
        ("update", ("add the pairs of another dictionary", "додати пари іншого словника", "добавить пары другого словаря"),
         (_p("other", "dict", ("dictionary", "словник", "словарь")),), "None", '{"a": 1}.update({"b": 2})'),
        ("pop", ("remove a key and return its value", "вилучити ключ і повернути значення",
                 "удалить ключ и вернуть значение"),
         (_p("key", "any", ("key", "ключ", "ключ")), _p("default", "any", ("default", "типове", "по умолчанию"))),
         "any", '{"a": 1}.pop("a")'),
        ("setdefault", ("value by a key; absent — set the default", "значення за ключем; відсутнє — встановити типове",
                        "значение по ключу; отсутствует — установить по умолчанию"),
         (_p("key", "any", ("key", "ключ", "ключ")), _p("default", "any", ("default", "типове", "по умолчанию"), "None")),
         "any", '{}.setdefault("a", 1)'),
    )),
)


def signature(function: Function) -> str:
    """``money(x, code, currency_style="short", lang)``: the call form of a function."""
    if function.kind == "constant":
        return (f"math.{function.name}" if function.module else function.name)
    parts: list[str] = []
    seen: set[str] = set()
    for arg in function.args:
        if arg.name in seen:   # the same argument given by position or by keyword (round, sum…)
            continue
        seen.add(arg.name)
        parts.append(arg.name if arg.default is None else f"{arg.name}={arg.default}")
    prefix = "math." if function.module else ("." if function.kind == "method" else "")
    owner = function.receiver if function.kind == "method" else ""
    return f"{owner}{prefix}{function.name}(" + ", ".join(parts) + ")"


def show(value: Any) -> str:
    """A value as the console shows it: strings in double quotes, the rest as ``repr``."""
    from primula.core.values import to_repr

    if isinstance(value, str):
        return '"' + value + '"'
    return to_repr(value)


def example_runner(language: str) -> Callable[[str], Any]:
    """An evaluator of expressions with the prelude and ``math`` (std/math) in ``language``.

    The examples of the catalogue need no document: no data files, styles or
    markup.  The build date is fixed (12.10.2026) so that results do not
    depend on the day.

    Returns:
        ``run(expression)`` → the value; errors are raised as ``CoreError``.
    """
    from primula.core.errors import CoreError
    from primula.core.interp import EvalContext, Interpreter
    from primula.core.limits import Limits, Meter
    from primula.core.program import Program
    from primula.core.values import Record
    from primula.diagnostics import DiagnosticSink, Severity
    from primula.library.context import Library
    from primula.library.prelude import make_library_builtins, std_module
    from primula.source import SourceFile, Span
    from primula.syntax import pyfrag

    sink = DiagnosticSink(error_limit=0)
    library = Library(lambda: {}, lambda: language, sink)
    builtins: dict[str, Any] = dict(make_library_builtins(library))
    builtins["math"] = Record(std_module(library, "std/math") or {})
    interp = Interpreter(EvalContext(meter=Meter(Limits()), build_date=datetime.date(2026, 10, 12),
                                     sink=sink, extra_builtins=builtins))

    def run(expression: str) -> Any:
        # A definition r = … in a fresh scope, evaluated on lookup.
        source = SourceFile.from_text("<example>", f"r = {expression}\n")
        scope = interp.new_globals()
        program = Program(interp, scope)
        static = DiagnosticSink(error_limit=0)   # parse errors of this expression only
        program.add_code(pyfrag.parse_code(source, [(0, 0, source.text.rstrip("\n"))],
                                           Span(source, 0, len(source.text))), static)
        errors = [d for d in static.diagnostics if d.severity is Severity.ERROR]
        if errors:
            raise CoreError(errors[0])
        return scope.lookup("r", None)

    return run


def evaluate_examples(language: str) -> dict[str, str]:
    """Run the examples that need no document in ``language``.

    Returns:
        ``{example: result}``; an example that fails is left out (tests
        require every example to run).
    """
    from primula.core.errors import CoreError

    run = example_runner(language)
    results: dict[str, str] = {}
    for function in FUNCTIONS:
        if function.run and function.example and function.example not in results:
            try:
                results[function.example] = show(run(function.example))
            except CoreError:
                continue
    return results


def _arg(arg: Arg, index: int) -> dict[str, Any]:
    return {"name": arg.name, "positional": arg.positional, "type": arg.type, "default": arg.default,
            "summary": arg.text[index]}


def functions_catalogue(index: int, language: str) -> dict[str, Any]:
    """The ``function_categories`` and ``functions`` keys of the catalogue."""
    try:
        results = evaluate_examples(language)
    except Exception:   # pragma: no cover - a broken example never breaks the catalogue
        results = {}
    functions = [{"name": f.name, "kind": f.kind, "module": f.module, "receiver": f.receiver,
                  "category": f.category, "where": f.where, "doc": f.doc, "section": f.section,
                  "summary": f.text[index], "returns": f.returns, "signature": signature(f),
                  "args": [_arg(a, index) for a in f.args], "example": f.example,
                  "result": results.get(f.example) if f.run else None} for f in FUNCTIONS]
    return {"function_categories": [{"id": key, "title": titles[index]} for key, titles in CATEGORIES],
            "functions": functions}


def render_text(data: dict[str, Any]) -> str:
    """A plain-text listing of the functions (``primula commands --functions``)."""
    lines: list[str] = []
    for category in data["function_categories"]:
        entries = [f for f in data["functions"] if f["category"] == category["id"]]
        if not entries:
            continue
        lines.append(f"{category['title']}:")
        for entry in entries:
            section = ("stdlib " if entry["doc"] == "stdlib" else "") + entry["section"]
            lines.append(f"  {entry['signature']}")
            lines.append(f"      {entry['summary']}  [{section}]")
            if entry["example"]:
                result = f"  →  {entry['result']}" if entry["result"] is not None else ""
                lines.append(f"      {entry['example']}{result}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
