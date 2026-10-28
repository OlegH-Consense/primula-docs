"""Structure settings: profiles, numbering, captions, annexes, labels, notes.

Specification 5.1-5.10 and decisions 68-76.  The settings of the styles
modules and of the document (``numbering``, ``captions``, ``appendices``,
``ref_labels``, ``footnotes``; the ``structure`` key of the document
header) are laid over the defaults of the structure profile
(``business`` or ``report``, 5.1) for the document language.

Language-dependent defaults (caption formats, annex designations, label
dictionaries, titles of the table of contents and of the lists) are part
of the profile for uk, ru and en (decision 73).  A document in another
language uses the English texts for captions and annexes, and has no
label dictionary unless a styles module gives one (decision 72: the
``label`` reference mode is then an error).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from primula.styles.system import merge_props

#: Quotes by language: (outer, inner) pairs (decision 63).
QUOTES: dict[str, tuple[tuple[str, str], tuple[str, str]]] = {
    "uk": (("«", "»"), ("„", "“")), "ru": (("«", "»"), ("„", "“")), "en": (("“", "”"), ("‘", "’")),
}

#: Annex letters (decision 71): Ukrainian per DSTU 3008:2015 (without
#: Ґ, Є, З, І, Ї, Й, О, Ч, Ь), Russian per GOST 2.105 (without Ё, З, Й,
#: О, Ч, Ь, Ы, Ъ), Latin without I and O.
LETTERS = {"uk": "АБВГДЕЖКЛМНПРСТУФХЦШЩЮЯ", "ru": "АБВГДЖИКЛМНПРСТУФХЦШЩЭЮЯ",
           "en": "ABCDEFGHJKLMNPQRSTUVWXYZ"}

#: Texts of the languages: caption formats, designations, index titles.
_TEXTS: dict[str, dict[str, Any]] = {
    "uk": {"figure": "Рисунок {n} — {title}", "table": "Таблиця {n} — {title}",
           "business": "Додаток {n}", "report": "ДОДАТОК {n}",
           "toc": "ЗМІСТ", "figures": "ПЕРЕЛІК РИСУНКІВ", "tables": "ПЕРЕЛІК ТАБЛИЦЬ"},
    "ru": {"figure": "Рисунок {n} — {title}", "table": "Таблица {n} — {title}",
           "business": "Приложение {n}", "report": "ПРИЛОЖЕНИЕ {n}",
           "toc": "СОДЕРЖАНИЕ", "figures": "ПЕРЕЧЕНЬ РИСУНКОВ", "tables": "ПЕРЕЧЕНЬ ТАБЛИЦ"},
    "en": {"figure": "Figure {n} — {title}", "table": "Table {n} — {title}",
           "business": "Appendix {n}", "report": "APPENDIX {n}",
           "toc": "CONTENTS", "figures": "LIST OF FIGURES", "tables": "LIST OF TABLES"},
}

#: Reference label dictionaries (decision 72); en has only short and nominative forms.
LABELS: dict[str, dict[str, dict[str, str]]] = {
    "uk": {
        "section": {"short": "розд.", "nom": "розділ", "gen": "розділу", "dat": "розділу", "acc": "розділ",
                    "ins": "розділом", "loc": "розділі"},
        "subsection": {"short": "підрозд.", "nom": "підрозділ", "gen": "підрозділу", "dat": "підрозділу",
                       "acc": "підрозділ", "ins": "підрозділом", "loc": "підрозділі"},
        "clause": {"short": "п.", "nom": "пункт", "gen": "пункту", "dat": "пункту", "acc": "пункт",
                   "ins": "пунктом", "loc": "пункті"},
        "subclause": {"short": "пп.", "nom": "підпункт", "gen": "підпункту", "dat": "підпункту",
                      "acc": "підпункт", "ins": "підпунктом", "loc": "підпункті"},
        "appendix": {"short": "дод.", "nom": "додаток", "gen": "додатка", "dat": "додатку", "acc": "додаток",
                     "ins": "додатком", "loc": "додатку"},
        "figure": {"short": "рис.", "nom": "рисунок", "gen": "рисунка", "dat": "рисунку", "acc": "рисунок",
                   "ins": "рисунком", "loc": "рисунку"},
        "table": {"short": "табл.", "nom": "таблиця", "gen": "таблиці", "dat": "таблиці", "acc": "таблицю",
                  "ins": "таблицею", "loc": "таблиці"},
    },
    "ru": {
        "section": {"short": "разд.", "nom": "раздел", "gen": "раздела", "dat": "разделу", "acc": "раздел",
                    "ins": "разделом", "loc": "разделе"},
        "subsection": {"short": "подразд.", "nom": "подраздел", "gen": "подраздела", "dat": "подразделу",
                       "acc": "подраздел", "ins": "подразделом", "loc": "подразделе"},
        "clause": {"short": "п.", "nom": "пункт", "gen": "пункта", "dat": "пункту", "acc": "пункт",
                   "ins": "пунктом", "loc": "пункте"},
        "subclause": {"short": "пп.", "nom": "подпункт", "gen": "подпункта", "dat": "подпункту",
                      "acc": "подпункт", "ins": "подпунктом", "loc": "подпункте"},
        "appendix": {"short": "прил.", "nom": "приложение", "gen": "приложения", "dat": "приложению",
                     "acc": "приложение", "ins": "приложением", "loc": "приложении"},
        "figure": {"short": "рис.", "nom": "рисунок", "gen": "рисунка", "dat": "рисунку", "acc": "рисунок",
                   "ins": "рисунком", "loc": "рисунке"},
        "table": {"short": "табл.", "nom": "таблица", "gen": "таблицы", "dat": "таблице", "acc": "таблицу",
                  "ins": "таблицей", "loc": "таблице"},
    },
    "en": {
        "section": {"short": "sec.", "nom": "section"},
        "subsection": {"short": "sec.", "nom": "section"},
        "clause": {"short": "cl.", "nom": "clause"},
        "subclause": {"short": "cl.", "nom": "clause"},
        "appendix": {"short": "app.", "nom": "appendix"},
        "figure": {"short": "fig.", "nom": "figure"},
        "table": {"short": "tab.", "nom": "table"},
    },
}

#: Cases of label forms (5.7).
CASES = ("short", "nom", "gen", "dat", "acc", "ins", "loc")


@dataclass
class StructureSettings:
    """Effective structure settings of a document.

    Attributes:
        profile: ``business`` or ``report``.
        language: language code (``uk``, ``ru``, ``en``…).
        numbering: ``headings``, ``heading_format``, ``clause_format``,
            ``figures``, ``tables``, ``ref_format``.
        captions: ``figure``/``table`` -> ``{"format", "position"}``.
        appendices: ``designation``, ``numbering``, ``letters``,
            ``page_break``, ``toc``.
        labels: label dictionary of the document language or ``None``.
        footnotes: ``numbering``, ``restart``, ``format``, ``separator``.
        titles: default titles of ``|toc`` and ``|list_of`` (``toc``,
            ``figures``, ``tables``).
    """

    profile: str
    language: str
    numbering: dict[str, Any]
    captions: dict[str, dict[str, Any]]
    appendices: dict[str, Any]
    labels: dict[str, dict[str, str]] | None
    footnotes: dict[str, Any]
    titles: dict[str, str] = field(default_factory=dict)


def language_code(language: str | None) -> str:
    """``uk-UA`` -> ``uk``."""
    return (language or "uk").split("-")[0].lower()


def document_language(header_data: dict[str, Any], defaults: dict[str, Any],
                      project_language: str | None = None) -> str:
    """The document language (decision 65, 15).

    ``doc.language`` of the header, then the project language
    (``language`` of ``project.p.prml``), then ``defaults.language`` of the
    styles modules, then ``uk-UA``.
    """
    metadata = header_data.get("doc") or {}
    if isinstance(metadata, dict) and isinstance(metadata.get("language"), str):
        return metadata["language"]
    if isinstance(project_language, str) and project_language:
        return project_language
    if isinstance(defaults.get("language"), str):
        return defaults["language"]
    return "uk-UA"


def _profile_defaults(profile: str, code: str) -> dict[str, Any]:
    """Defaults of a structure profile for a language (5.1, decisions 71, 73)."""
    texts = _TEXTS.get(code, _TEXTS["en"])
    report = profile == "report"
    return {
        "numbering": {"headings": True, "heading_format": "{n}.", "clause_format": "{n}.",
                      "figures": "by_chapter" if report else "document",
                      "tables": "by_chapter" if report else "document", "ref_format": "{n}"},
        "captions": {"figure": {"format": texts["figure"], "position": "below"},
                     "table": {"format": texts["table"], "position": "above"}},
        "appendices": {"designation": texts[profile], "numbering": "letters" if report else "numbers",
                       "letters": LETTERS.get(code, LETTERS["en"]), "page_break": True,
                       "toc": "{designation} {title}"},
        "footnotes": {"numbering": "document", "restart": "none", "format": "1", "separator": "0.5pt solid"},
        "titles": {"toc": texts["toc"], "figures": texts["figures"], "tables": texts["tables"]},
    }


def _for_language(group: Any, code: str) -> dict[str, Any]:
    """A by-language settings group: ``"*"`` first, then the language (decision 73)."""
    if not isinstance(group, dict):
        return {}
    result: dict[str, Any] = {}
    for key in ("*", code):
        value = group.get(key)
        if isinstance(value, dict):
            result = merge_props(result, value)
    return result


def resolve_settings(settings: dict[str, Any], header_structure: Any, language: str) -> StructureSettings:
    """Effective structure settings.

    Args:
        settings: merged settings of the style system (``numbering``,
            ``captions``, ``appendices``, ``ref_labels``, ``footnotes``,
            ``profile``).
        header_structure: the ``structure`` key of the document header (a
            mapping of the same groups, e.g. ``{numbering: {headings: false}}``).
        language: the document language tag.

    Returns:
        The settings for the structure phase.
    """
    profile = settings.get("profile") if settings.get("profile") in ("business", "report") else "business"
    code = language_code(language)
    base = _profile_defaults(profile, code)
    overrides = header_structure if isinstance(header_structure, dict) else {}

    numbering = merge_props(base["numbering"], settings.get("numbering") or {})
    numbering = merge_props(numbering, overrides.get("numbering") or {})
    captions = merge_props(base["captions"], _for_language(settings.get("captions"), code))
    captions = merge_props(captions, overrides.get("captions") or {})
    appendices = merge_props(base["appendices"], _for_language(settings.get("appendices"), code))
    appendices = merge_props(appendices, overrides.get("appendices") or {})
    footnotes = merge_props(base["footnotes"], settings.get("footnotes") or {})
    footnotes = merge_props(footnotes, overrides.get("footnotes") or {})

    labels: dict[str, Any] | None = LABELS.get(code)
    user_labels = (settings.get("ref_labels") or {}).get(code)
    if isinstance(user_labels, dict):
        labels = merge_props(labels or {}, user_labels)
    return StructureSettings(profile, code, numbering, captions, appendices,
                             labels, footnotes, base["titles"])


def format_for_level(value: Any, level: int, fallback: str = "{n}.") -> str:
    """A numbering format: one string, or a mapping by level (decision 69)."""
    if isinstance(value, dict):
        chosen = value.get(level, value.get(str(level)))
        return chosen if isinstance(chosen, str) else fallback
    return value if isinstance(value, str) else fallback


def number_text(fmt: str, number: str) -> str:
    """The number as written before the text: the format and a separator.

    One space follows the formatted number unless the format already ends
    with a space or a tab (decision 69); a tab aligns the text by the
    hanging indent of the paragraph.
    """
    text = fmt.replace("{n}", number)
    return text if text.endswith((" ", "\t")) else text + " "
