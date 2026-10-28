"""Catalogue of the YAML header keys (stage 14.14; decisions 127, 129).

Part of ``primula commands --format json`` (key ``header_keys``): every key
the translator knows in the header of a file of each kind — document,
fragment, module, styles module, project — with nested keys of ``primula``,
``doc`` (ODT metadata; ``doc_defaults`` in a project), ``limits``, ``targets``
and ``ref_documents``.
Primula Studio uses it for hints, completion and F1 inside the header and
for the skeleton of a header; it is the same table as the checks of
:mod:`primula.header` and :mod:`primula.evaluate.project`, and tests keep
them in line.

Each entry::

    {"path": "doc.title", "kinds": ["document"], "type": "string",
     "values": [], "closed": false, "recommended": true, "section": "2.3",
     "summary": "...", "example": "title: \\"Договір поставки\\""}

``path``: dotted key path; ``targets[]`` stands for each element of the
list.  ``kinds``: file kinds whose header takes the key.  ``type``:
``string``, ``path``, ``paths`` (a list of paths or one path), ``mapping``,
``list``, ``number``, ``int``, ``bool``, ``date``, ``language``,
``strings`` (a string or a list of strings), ``any``.  ``values``: the
allowed values when ``closed``, else suggestions.  ``recommended``: a field
a finished ODT is expected to have (``doc``), or a default worth giving in a
project (``doc_defaults``); Studio offers to add the missing ones, the
translator requires none of them.  ``example``: one YAML line.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from primula.commands import T

ALL_KINDS = ("document", "fragment", "module", "styles", "project")

#: Language tags suggested for ``language`` (any BCP 47 tag is allowed).
LANGUAGES = ("uk-UA", "en-US", "en-GB", "ru-RU", "pl-PL", "de-DE")


@dataclass(frozen=True)
class HeaderKey:
    """A key of the YAML header.

    Attributes:
        path: dotted path (``doc.title``, ``targets[].source``).
        kinds: file kinds whose header takes the key.
        type: value type (see the module description).
        section: specification section.
        text: short description (en, uk, ru).
        example: one YAML line, as written under its parent.
        values: allowed values (``closed``) or suggestions.
        recommended: expected in a finished ODT (document metadata).
    """

    path: str
    kinds: tuple[str, ...]
    type: str
    section: str
    text: T
    example: str
    values: tuple[str, ...] = ()
    closed: bool = False
    recommended: bool = False


#: Recommended defaults of a project (``doc_defaults``): the same for every document.
PROJECT_RECOMMENDED = ("creator", "organization")


def _meta(name: str, type_: str, text: T, example: str, recommended: bool = False,
          values: tuple[str, ...] = ()) -> tuple[HeaderKey, HeaderKey]:
    """A metadata key: ``doc.NAME`` of a document and ``doc_defaults.NAME`` of a project
    (its default for every document; decisions 127, 129)."""
    return (HeaderKey(f"doc.{name}", ("document",), type_, "2.3", text, example, values,
                      recommended=recommended),
            HeaderKey(f"doc_defaults.{name}", ("project",), type_, "10.6", text, example, values,
                      recommended=name in PROJECT_RECOMMENDED))


HEADER_KEYS: tuple[HeaderKey, ...] = (
    # --- every kind ---------------------------------------------------------------------------
    HeaderKey("kind", ALL_KINDS, "string", "2.2",
              ("file kind; implied by the sub-extension (.f, .m, .s, .p), required in a project",
               "вид файлу; випливає з підрозширення (.f, .m, .s, .p), у проєкті обов'язковий",
               "вид файла; следует из подрасширения (.f, .m, .s, .p), в проекте обязателен"),
              "kind: document", ("document", "fragment", "module", "styles", "project"), closed=True),
    HeaderKey("primula", ALL_KINDS, "mapping", "2.3",
              ("language declaration: {version: \"1.1\"}, optionally the library version",
               "оголошення мови: {version: \"1.1\"}, за потреби версія бібліотеки",
               "объявление языка: {version: \"1.1\"}, при необходимости версия библиотеки"),
              'primula: {version: "1.1"}'),
    HeaderKey("primula.version", ALL_KINDS, "string", "2.3",
              ("language version; only 1.1 is accepted", "версія мови; приймається лише 1.1",
               "версия языка; принимается только 1.1"), 'version: "1.1"', ("1.1",), closed=True),
    HeaderKey("primula.stdlib", ALL_KINDS, "string", "13",
              ("minimal version of the standard library", "мінімальна версія стандартної бібліотеки",
               "минимальная версия стандартной библиотеки"), 'stdlib: "1.1"', ("1.1",)),
    # --- document -----------------------------------------------------------------------------
    HeaderKey("doc", ("document",), "mapping", "2.3",
              ("ODT metadata of the document; in the text |(doc.title)",
               "метадані ODT документа; у тексті |(doc.title)",
               "метаданные ODT документа; в тексте |(doc.title)"),
              "doc:"),
    HeaderKey("doc_defaults", ("project",), "mapping", "10.6",
              ("defaults of the metadata (doc:) of every document of the project; a document overrides them key by key",
               "типові значення метаданих (doc:) усіх документів проєкту; документ перевизначає їх поштучно",
               "значения по умолчанию метаданных (doc:) всех документов проекта; документ переопределяет их поштучно"),
              "doc_defaults:"),
    *_meta("title", "string", ("title (dc:title)", "назва (dc:title)", "название (dc:title)"),
          'title: "Договір поставки"', recommended=True),
    *_meta("subject", "string", ("subject (dc:subject)", "тема (dc:subject)", "тема (dc:subject)"),
          'subject: "Поставка обладнання"'),
    *_meta("description", "string", ("description (dc:description)", "опис (dc:description)",
                                     "описание (dc:description)"), 'description: "Типова форма"'),
    *_meta("creator", "string", ("author (meta:initial-creator, dc:creator)", "автор (meta:initial-creator, dc:creator)",
                                 "автор (meta:initial-creator, dc:creator)"), 'creator: "Іван Петренко"',
          recommended=True),
    *_meta("organization", "string", ("organization (user-defined property)", "організація (користувацька властивість)",
                                      "организация (пользовательское свойство)"),
          'organization: "ТОВ «Постачальник»"'),
    *_meta("language", "language", ("document language (dc:language); else the project language",
                                   "мова документа (dc:language); інакше мова проєкту",
                                   "язык документа (dc:language); иначе язык проекта"),
          "language: uk-UA", recommended=True, values=LANGUAGES),
    *_meta("identifier", "string", ("document number (user-defined property)", "номер документа (користувацька властивість)",
                                    "номер документа (пользовательское свойство)"), 'identifier: "Д-2026-017"'),
    *_meta("revision", "string", ("revision (user-defined property)", "редакція (користувацька властивість)",
                                  "редакция (пользовательское свойство)"), 'revision: "2"'),
    *_meta("status", "string", ("status (user-defined property)", "статус (користувацька властивість)",
                                "статус (пользовательское свойство)"), 'status: "проєкт"',
          values=("проєкт", "чинний", "draft", "final")),
    *_meta("created", "date", ("creation date (meta:creation-date); else the build date",
                               "дата створення (meta:creation-date); інакше дата збирання",
                               "дата создания (meta:creation-date); иначе дата сборки"),
          "created: 2026-10-12", recommended=True),
    *_meta("modified", "date", ("modification date (dc:date); else the build date",
                                "дата зміни (dc:date); інакше дата збирання",
                                "дата изменения (dc:date); иначе дата сборки"), "modified: 2026-10-16"),
    *_meta("keywords", "strings", ("keywords (meta:keyword): a string or a list",
                                   "ключові слова (meta:keyword): рядок або список",
                                   "ключевые слова (meta:keyword): строка или список"),
          "keywords: [договір, поставка]"),
    HeaderKey("params", ("document", "fragment", "project"), "mapping", "10.6",
              ("parameters with default values; a target or --param overrides them",
               "параметри зі значеннями за замовчуванням; ціль або --param їх перевизначає",
               "параметры со значениями по умолчанию; цель или --param их переопределяет"),
              "params: {vat: true, delivery_days: 5}"),
    HeaderKey("structure", ("document",), "mapping", "5.1",
              ("structure profile settings of the document", "налаштування профілю структури документа",
               "настройки профиля структуры документа"), "structure: {numbering: {headings: false}}"),
    HeaderKey("styles", ("document", "project"), "paths", "11.7",
              ("styles modules: a list of paths or one path (std/styles/default — the built-in one)",
               "модулі стилів: список шляхів або один шлях (std/styles/default — вбудований)",
               "модули стилей: список путей или один путь (std/styles/default — встроенный)"),
              "styles: [styles/business.s.prml]", ("std/styles/default",)),
    HeaderKey("references", ("document",), "list", "5.7",
              ("documents of the project whose targets the document refers to (names from ref_documents of the project)",
               "документи проєкту, на цілі яких посилається документ (імена з ref_documents проєкту)",
               "документы проекта, на цели которых ссылается документ (имена из ref_documents проекта)"),
              "references: [contract]"),
    # --- styles module ------------------------------------------------------------------------
    HeaderKey("defaults", ("styles",), "mapping", "11.1",
              ("default properties: font, size, language", "типові властивості: шрифт, розмір, мова",
               "свойства по умолчанию: шрифт, размер, язык"), "defaults: {font: Roboto, size: 11pt, language: uk-UA}"),
    HeaderKey("paragraphs", ("styles",), "mapping", "11.2",
              ("paragraph styles", "стилі абзаців", "стили абзацев"), "paragraphs:"),
    HeaderKey("characters", ("styles",), "mapping", "11.2",
              ("character styles", "стилі символів", "стили символов"), "characters:"),
    HeaderKey("blocks", ("styles",), "mapping", "11.2",
              ("block styles", "стилі блоків", "стили блоков"), "blocks:"),
    HeaderKey("tables", ("styles",), "mapping", "11.2",
              ("table styles", "стилі таблиць", "стили таблиц"), "tables:"),
    HeaderKey("lists", ("styles",), "mapping", "11.2",
              ("list styles", "стилі списків", "стили списков"), "lists:"),
    HeaderKey("frames", ("styles",), "mapping", "11.2",
              ("frame styles", "стилі врізок", "стили врезок"), "frames:"),
    HeaderKey("extends", ("styles",), "path", "11.7",
              ("base styles module, loaded as the layer before this one (decision 133)",
               "базовий модуль стилів, підключається шаром перед цим (рішення 133)",
               "базовый модуль стилей, подключается слоем перед этим (решение 133)"),
              "extends: std/styles/business"),
    HeaderKey("pages", ("styles",), "mapping", "11.2",
              ("page styles", "стилі сторінок", "стили страниц"), "pages:"),
    # --- project ------------------------------------------------------------------------------
    HeaderKey("name", ("project",), "string", "10.6",
              ("project name", "назва проєкту", "название проекта"), 'name: "Договори 2026"'),
    HeaderKey("language", ("project",), "language", "10.6",
              ("default language of the documents", "типова мова документів", "язык документов по умолчанию"),
              "language: uk-UA", LANGUAGES),
    HeaderKey("extends", ("project",), "path", "10.6",
              ("base project: its parameters, keys, reference documents, styles and metadata defaults are inherited",
               "базовий проєкт: його параметри, ключі, документи для посилань, стилі й типові метадані успадковуються",
               "базовый проект: его параметры, ключи, документы для ссылок, стили и метаданные по умолчанию наследуются"),
              "extends: ../../project.p.prml"),
    HeaderKey("on_conflict", ("project",), "string", "10.4",
              ("export conflicts of fragments: error, first, last", "конфлікти експорту фрагментів: error, first, last",
               "конфликты экспорта фрагментов: error, first, last"), "on_conflict: error",
              ("error", "first", "last"), closed=True),
    HeaderKey("keys", ("project",), "mapping", "9.3",
              ("key map: name → path", "карта ключів: ім'я → шлях", "карта ключей: имя → путь"),
              "keys: {logo: assets/logo.svg}"),
    HeaderKey("limits", ("project",), "mapping", "12.8",
              ("core limits: time, recursion, size", "ліміти ядра: time, recursion, size",
               "лимиты ядра: time, recursion, size"), "limits: {time: 20, recursion: 500, size: 10_000_000}"),
    HeaderKey("limits.time", ("project",), "number", "12.8",
              ("time limit, seconds", "ліміт часу, секунди", "лимит времени, секунды"), "time: 20"),
    HeaderKey("limits.recursion", ("project",), "int", "12.8",
              ("recursion depth limit", "ліміт глибини рекурсії", "лимит глубины рекурсии"), "recursion: 500"),
    HeaderKey("limits.size", ("project",), "int", "12.8",
              ("size limit of values", "ліміт розміру значень", "лимит размера значений"), "size: 10_000_000"),
    HeaderKey("build_date", ("project",), "date", "12.7",
              ("fixed build date (today() and the default dates)", "фіксована дата збирання (today() і типові дати)",
               "фиксированная дата сборки (today() и даты по умолчанию)"), "build_date: 2026-10-12"),
    HeaderKey("targets", ("project",), "list", "10.7",
              ("build targets of primula build project.p.prml", "цілі збирання primula build project.p.prml",
               "цели сборки primula build project.p.prml"),
              "targets:"),
    HeaderKey("targets[].source", ("project",), "path", "10.7",
              ("source document", "вихідний документ", "исходный документ"), "- source: contract.prml"),
    HeaderKey("targets[].output", ("project",), "path", "10.7",
              ("output ODT", "вихідний ODT", "выходной ODT"), "output: out/contract.odt"),
    HeaderKey("targets[].params", ("project",), "mapping", "10.7",
              ("parameter values of the target", "значення параметрів цілі", "значения параметров цели"),
              "params: {vat: false}"),
    HeaderKey("targets[].keys", ("project",), "mapping", "10.7",
              ("keys of the target", "ключі цілі", "ключи цели"), "keys: {logo: assets/other.svg}"),
    HeaderKey("targets[].pdf", ("project",), "any", "10.7",
              ("also a PDF: true or its path", "також PDF: true або його шлях", "также PDF: true или его путь"),
              "pdf: true", ("true",)),
    HeaderKey("ref_documents", ("project",), "mapping", "10.6",
              ("documents referred to by others (references: of a document): name: path or {source, registry}",
               "документи, на які посилаються інші (references: документа): ім'я: шлях або {source, registry}",
               "документы, на которые ссылаются другие (references: документа): имя: путь или {source, registry}"),
              "ref_documents: {contract: contract.prml}"),
)

#: Keys of a ``targets`` element and of a ``ref_documents`` entry, and of ``limits`` (for tests).
TARGET_PREFIX = "targets[]."


def recommended(kind: str) -> list[HeaderKey]:
    """The recommended keys of a file kind (document metadata)."""
    return [key for key in HEADER_KEYS if key.recommended and kind in key.kinds]


def header_catalogue(index: int) -> dict[str, Any]:
    """The ``header_keys`` key of the catalogue in the language ``index`` (en, uk, ru)."""
    return {"header_keys": [{"path": k.path, "kinds": list(k.kinds), "type": k.type, "values": list(k.values),
                             "closed": k.closed, "recommended": k.recommended, "section": k.section,
                             "summary": k.text[index], "example": k.example} for k in HEADER_KEYS]}


def render_text(data: dict[str, Any]) -> str:
    """A plain-text listing of the header keys (``primula commands --header``)."""
    lines: list[str] = []
    for kind in ALL_KINDS:
        entries = [k for k in data["header_keys"] if kind in k["kinds"]]
        lines.append(f"{kind}:")
        for entry in entries:
            mark = " *" if entry["recommended"] else ""
            lines.append(f"  {entry['path']}{mark}  ({entry['type']})  {entry['summary']}  [{entry['section']}]")
            # The example of kind is the kind being listed.
            example = f"kind: {kind}" if entry["path"] == "kind" else entry["example"]
            lines.append(f"      {example}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
