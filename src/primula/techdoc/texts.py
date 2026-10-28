"""Texts of the technical documentation tools by language (9.1, 9.2, 9.4, 9.5).

Signal words (decision 116): ISO 3864-2 / ANSI Z535 for en; the ru row
parallels uk.  ``notes`` — the heading of a group of notes («Примітки:»),
an extension key of ``admonition_words`` (the specification names the
kinds only).  The styles module overrides them with
``admonition_words(lang, kind="word")`` and ``review_marks(lang, true=…,
false=…, watermark=…)``; a call without a language sets all languages.
"""

from __future__ import annotations

from typing import Any

#: Name of a command built by the transforms: its content is written as is.
GENERATED = "generated"

KINDS = ("danger", "warning", "caution", "notice", "note", "tip")
#: Kinds written as a table with the signal word; note and tip are paragraphs.
HAZARD_KINDS = ("danger", "warning", "caution", "notice")

WORDS: dict[str, dict[str, str]] = {
    "uk": {"danger": "НЕБЕЗПЕКА", "warning": "ПОПЕРЕДЖЕННЯ", "caution": "ОБЕРЕЖНО", "notice": "УВАГА",
           "note": "Примітка", "tip": "Порада", "notes": "Примітки"},
    "ru": {"danger": "ОПАСНО", "warning": "ПРЕДУПРЕЖДЕНИЕ", "caution": "ОСТОРОЖНО", "notice": "ВНИМАНИЕ",
           "note": "Примечание", "tip": "Совет", "notes": "Примечания"},
    "en": {"danger": "DANGER", "warning": "WARNING", "caution": "CAUTION", "notice": "NOTICE",
           "note": "Note", "tip": "Tip", "notes": "Notes"},
}

REVIEW: dict[str, dict[str, str]] = {
    "uk": {"true": "так", "false": "ні", "watermark": "НЕ ДЛЯ ВИПУСКУ"},
    "ru": {"true": "да", "false": "нет", "watermark": "НЕ ДЛЯ ВЫПУСКА"},
    "en": {"true": "true", "false": "false", "watermark": "NOT FOR RELEASE"},
}

TITLES: dict[str, dict[str, str]] = {
    "uk": {"abbr": "ПЕРЕЛІК СКОРОЧЕНЬ", "index": "ПОКАЖЧИК"},
    "ru": {"abbr": "ПЕРЕЧЕНЬ СОКРАЩЕНИЙ", "index": "УКАЗАТЕЛЬ"},
    "en": {"abbr": "ABBREVIATIONS", "index": "INDEX"},
}


def language(tag: str | None) -> str:
    """``uk-UA`` → ``uk``; other languages → ``en``."""
    code = (tag or "").split("-")[0].lower()
    return code if code in WORDS else "en"


def by_language(defaults: dict[str, dict[str, str]], settings: Any, lang: str) -> dict[str, str]:
    """Defaults of a language merged with settings ``{"*": {...}, "uk": {...}}`` of the styles modules."""
    result = dict(defaults[lang])
    if isinstance(settings, dict):
        for key in ("*", lang):
            values = settings.get(key)
            if isinstance(values, dict):
                result.update({k: str(v) for k, v in values.items()})
    return result
