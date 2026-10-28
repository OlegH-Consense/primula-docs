"""Translations of the ``problem`` texts of core messages (stage 13.9d).

P2321 (``{function}(): {problem}``), P2322 (``{function}: {problem}``) and
P2609 (``|{command}: {problem}``) are raised in many places of the core,
the library and the evaluator with an English ``problem`` text, often
built with an f-string (``got an unexpected keyword argument 'x'``).
Instead of a catalogue key at every call site, the text is translated
when the message is rendered: :func:`translate` matches it against the
English patterns below and fills the template of the language.  A text
without a pattern (a new message, a text of a Python library) stays in
English, so a missing translation never hides the diagnostic.

Each entry: a regular expression for the whole English text (named
groups are the arguments) and the templates for ``uk`` and ``ru``.  More
specific patterns come before general ones.
"""

from __future__ import annotations

import re

#: Codes whose ``problem`` argument is translated.
CODES = frozenset({"P2321", "P2322", "P2609"})

_T = tuple[str, str, str]  # pattern, uk, ru

_TABLE: list[_T] = [
    # --- arguments of calls -------------------------------------------------------------------
    (r"got an unexpected keyword argument '(?P<a>.+)'",
     "неочікуваний іменований аргумент '{a}'", "неожиданный именованный аргумент '{a}'"),
    (r"takes (?P<n>\d+) positional arguments but (?P<m>\d+) were given",
     "позиційних аргументів має бути {n}, передано {m}", "позиционных аргументов должно быть {n}, передано {m}"),
    (r"takes positional arguments (?P<u>.+)", "позиційні аргументи: {u}", "позиционные аргументы: {u}"),
    (r"got multiple values for '(?P<a>.+)'", "кілька значень для '{a}'", "несколько значений для '{a}'"),
    (r"missing argument '(?P<a>.+)'", "бракує аргументу '{a}'", "не хватает аргумента '{a}'"),
    (r"keyword names must be strings", "імена аргументів мають бути рядками", "имена аргументов должны быть строками"),
    (r"takes no arguments", "не приймає аргументів", "не принимает аргументов"),
    (r"takes only keyword arguments", "приймає лише іменовані аргументи", "принимает только именованные аргументы"),
    (r"only name=value arguments", "лише аргументи ім'я=значення", "только аргументы имя=значение"),
    (r"\*\*mapping is not allowed", "**словник тут не допускається", "**словарь здесь не допускается"),
    (r"unknown argument '(?P<a>.+)'", "невідомий аргумент '{a}'", "неизвестный аргумент '{a}'"),
    (r"'(?P<a>.+)' must be True or False", "'{a}' має бути True або False", "'{a}' должен быть True или False"),
    # --- arguments of style functions and table helpers ----------------------------------------
    (r"takes the style name as the only positional argument",
     "єдиний позиційний аргумент — ім'я стилю", "единственный позиционный аргумент — имя стиля"),
    (r"takes the base style name as the first argument",
     "перший аргумент — ім'я базового стилю", "первый аргумент — имя базового стиля"),
    (r"takes the language as the first argument", "перший аргумент — мова", "первый аргумент — язык"),
    (r"takes an optional language and keyword arguments",
     "приймає необов'язкову мову та іменовані аргументи", "принимает необязательный язык и именованные аргументы"),
    (r"takes a language and two pairs: (?P<x>.+)", "приймає мову і дві пари: {x}", "принимает язык и две пары: {x}"),
    (r"takes \"mark\" or \"final\"", "приймає \"mark\" або \"final\"", "принимает \"mark\" или \"final\""),
    (r"takes the mark as the first argument", "перший аргумент — позначка", "первый аргумент — метка"),
    (r"takes a page style name and content \(markup\(…\)\)",
     "приймає ім'я стилю сторінки та вміст (markup(…))", "принимает имя стиля страницы и содержимое (markup(…))"),
    (r"'(?P<c>.+)' needs a list of 12 names", "для '{c}' потрібен список із 12 назв",
     "для '{c}' нужен список из 12 названий"),
    (r"takes either the image path or svg=, not both",
     "приймає або шлях до зображення, або svg=, не обидва", "принимает либо путь к изображению, либо svg=, не оба"),
    (r"takes the image path as the only positional argument",
     "єдиний позиційний аргумент — шлях до зображення", "единственный позиционный аргумент — путь к изображению"),
    (r"takes one column", "приймає один стовпець", "принимает один столбец"),
    (r"takes a row and a column", "приймає рядок і стовпець", "принимает строку и столбец"),
    (r"takes a column and rows=…", "приймає стовпець і rows=…", "принимает столбец и rows=…"),
    (r"takes one positional argument \(the width\)",
     "приймає один позиційний аргумент (ширину)", "принимает один позиционный аргумент (ширину)"),
    # --- values -------------------------------------------------------------------------------
    (r"expected an integer, not (?P<t>.+)", "очікувалося ціле число, а не {t}", "ожидалось целое число, а не {t}"),
    (r"expected a number, not (?P<t>.+)", "очікувалося число, а не {t}", "ожидалось число, а не {t}"),
    (r"expected str, not (?P<t>.+)", "очікувався рядок, а не {t}", "ожидалась строка, а не {t}"),
    (r"expected a dict or record, not (?P<t>.+)", "очікувався словник або запис, а не {t}",
     "ожидался словарь или запись, а не {t}"),
    (r"expected a dict, not (?P<t>.+)", "очікувався словник, а не {t}", "ожидался словарь, а не {t}"),
    (r"expected (?P<w>.+), not (?P<t>.+)", "очікувалося {w}, а не {t}", "ожидалось {w}, а не {t}"),
    (r"expected pairs \(key, value\)", "очікувалися пари (ключ, значення)", "ожидались пары (ключ, значение)"),
    (r"expected one feature name", "очікувалася одна назва можливості", "ожидалось одно имя возможности"),
    (r"expected one string", "очікувався один рядок", "ожидалась одна строка"),
    (r"needs a document: open the console with a file", "потрібен документ: відкрийте консоль із файлом",
     "нужен документ: откройте консоль с файлом"),
    (r"expected one path string", "очікувався один рядок зі шляхом", "ожидалась одна строка с путём"),
    (r"(?P<t>\S+) has no length", "{t} не має довжини", "{t} не имеет длины"),
    (r"empty sequence", "порожня послідовність", "пустая последовательность"),
    (r"the repeat count must be an integer", "кількість повторень має бути цілим числом",
     "число повторений должно быть целым"),
    (r"index must be (?:an integer|int), not (?P<t>.+)", "індекс має бути цілим числом, а не {t}",
     "индекс должен быть целым числом, а не {t}"),
    (r"slice bounds must be integers", "межі зрізу мають бути цілими числами", "границы среза должны быть целыми числами"),
    (r"slice step cannot be zero", "крок зрізу не може бути нулем", "шаг среза не может быть нулём"),
    (r"step cannot be zero", "крок не може бути нулем", "шаг не может быть нулём"),
    (r"slice assignment is not supported", "присвоєння зрізу не підтримується", "присваивание среза не поддерживается"),
    # --- paths and data -----------------------------------------------------------------------
    (r"one URL string is required", "потрібен один рядок з адресою (URL)", "нужна одна строка с адресом (URL)"),
    (r"a path is required", "потрібен шлях", "нужен путь"),
    (r"one path is required", "потрібен один шлях", "нужен один путь"),
    (r"the path must be a string", "шлях має бути рядком", "путь должен быть строкой"),
    (r"params= must be a mapping of parameter names to values",
     "params= має бути словником «ім'я параметра — значення»", "params= должен быть словарём «имя параметра — значение»"),
    (r"level_shift= must be an integer from 0 to 5", "level_shift= має бути цілим числом від 0 до 5",
     "level_shift= должен быть целым числом от 0 до 5"),
    (r"data= must be a list of records, dicts or lists", "data= має бути списком записів, словників або списків",
     "data= должен быть списком записей, словарей или списков"),
    (r"fields= must be a list of field names", "fields= має бути списком імен полів", "fields= должен быть списком имён полей"),
    (r"titles= must be a list with one title per field", "titles= має бути списком по одному заголовку на поле",
     "titles= должен быть списком по одному заголовку на поле"),
    (r"sep must be ',' or ';'", "sep має бути ',' або ';'", "sep должен быть ',' или ';'"),
    (r"types must be a dict", "types має бути словником", "types должен быть словарём"),
    (r"types: no column '(?P<c>.+)'", "types: немає стовпця '{c}'", "types: нет столбца '{c}'"),
    (r"unknown column type '(?P<k>.+)'; expected one of (?P<l>.+) \(use '(?P<u>.+)'\)",
     "невідомий тип стовпця '{k}'; допустимі: {l} (використайте '{u}')",
     "неизвестный тип столбца '{k}'; допустимы: {l} (используйте '{u}')"),
    (r"unknown column type '(?P<k>.+)'; expected one of (?P<l>.+)",
     "невідомий тип стовпця '{k}'; допустимі: {l}", "неизвестный тип столбца '{k}'; допустимы: {l}"),
]

_COMPILED = [(re.compile(pattern + r"\Z"), {"uk": uk, "ru": ru}) for pattern, uk, ru in _TABLE]


def translate(language: str, text: str) -> str:
    """The ``problem`` text in ``language``; unchanged for ``en`` or an unknown text.

    Args:
        language: catalogue language (``en``, ``uk``, ``ru``).
        text: the English text.

    Returns:
        The translated text, or ``text`` itself.
    """
    if language == "en":
        return text
    for pattern, templates in _COMPILED:
        match = pattern.match(text)
        if match is not None:
            template = templates.get(language)
            return template.format(**match.groupdict()) if template else text
    return text


def patterns() -> list[str]:
    """The English patterns (for tests)."""
    return [pattern for pattern, _uk, _ru in _TABLE]
