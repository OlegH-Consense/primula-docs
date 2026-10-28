"""Catalogue of the constructs of the language: ``primula commands`` (14.1; stage 14.2, Т5).

One source for the insertion palette, the «Insert» menu, hints and
completion of Primula Studio (decision 124): built-in commands (appendix
2.1), short forms (3.3) and closing markers (3.5) with their arguments,
defaults, short descriptions and the section of the specification.

``primula commands --format json`` prints::

    {"schema": 1, "language": "uk", "version": "0.1.0.dev18",
     "categories": [{"id": "text", "title": "Текст"}, ...],
     "commands": [{"name": "table", "category": "tables", "forms": ["environment"],
                   "section": "6.2", "summary": "...", "close": "|end table",
                   "snippet": "|table($1):\\n$0\\n|end table",
                   "args": [{"name": "cols", "positional": false, "type": "list",
                             "default": null, "summary": "..."}, ...]}, ...],
     "short_forms": [{"form": "|*{…}", "where": "inline", "section": "3.3",
                      "summary": "...", "snippet": "|*{$0}", "style": "Strong"}, ...],
     "closings": [{"form": "|end>", "closes": "|>", "section": "3.5", "summary": "..."}, ...],
     "function_categories": [...], "functions": [...]}

``function_categories`` and ``functions`` — the functions of expressions
(stage 14.13, decision 126; :mod:`primula.functions`).

``forms``: ``inline`` (``|name(…){…}`` in a line), ``line`` (a command on
its own line, with a one-line body after ``:`` where allowed),
``environment`` (``|name(…):`` … ``|end name``).  ``snippet`` uses the
TextMate/VS Code placeholders ``$1``, ``${1:text}``, ``$0`` (the final
cursor).  ``default`` is written as in Primula code (``"1"``, ``True``) or
``null`` when the argument has no default.  The texts are in the language
of the messages (``--lang``, ``PRIMULA_LANG``…; 14.2).

The table is checked against the translator by tests: every built-in
command of :data:`primula.syntax.blocks.BUILTIN_COMMANDS` is described,
and the arguments of structure, frame and inclusion commands are those the
translator accepts.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

#: Version of the catalogue format.
SCHEMA = 1

#: Text in three languages: (en, uk, ru).
T = tuple[str, str, str]

_LANGS = ("en", "uk", "ru")

#: Categories of the «Insert» menu (remark З7), in menu order.
CATEGORIES: list[tuple[str, T]] = [
    ("text", ("Text", "Текст", "Текст")),
    ("structure", ("Structure", "Структура", "Структура")),
    ("tables", ("Tables", "Таблиці", "Таблицы")),
    ("pages", ("Pages and graphics", "Сторінки й графіка", "Страницы и графика")),
    ("techdoc", ("Technical documents", "Технічна документація", "Техническая документация")),
    ("modules", ("Fragments, modules, parts", "Фрагменти, модулі, частини", "Фрагменты, модули, части")),
    ("code", ("Code and data", "Код і дані", "Код и данные")),
]


@dataclass(frozen=True)
class Arg:
    """An argument of a command.

    Attributes:
        name: keyword name; for a positional argument — its name in the
            description (``path``, ``kind``).
        type: ``string``, ``int``, ``bool``, ``length``, ``style``, ``id``,
            ``path``, ``list``, ``dict``, ``expr``, ``any``.
        default: default value as written in Primula code, or ``None``.
        text: short description (en, uk, ru).
        positional: the argument is given by position.
    """

    name: str
    type: str
    default: str | None
    text: T
    positional: bool = False


@dataclass(frozen=True)
class Command:
    """A built-in command (appendix 2.1)."""

    name: str
    category: str
    forms: tuple[str, ...]
    section: str
    text: T
    args: tuple[Arg, ...] = ()
    snippet: str = ""
    close: str | None = None


@dataclass(frozen=True)
class Short:
    """A short form (3.3)."""

    form: str
    where: str
    section: str
    text: T
    snippet: str
    category: str = "text"
    style: str | None = None


@dataclass(frozen=True)
class Closing:
    """A closing marker of an environment (3.5)."""

    form: str
    closes: str
    text: T
    section: str = "3.5"


def _p(name: str, type_: str, text: T, default: str | None = None) -> Arg:
    return Arg(name, type_, default, text, positional=True)


def _k(name: str, type_: str, text: T, default: str | None = None) -> Arg:
    return Arg(name, type_, default, text)


# --- shared arguments ------------------------------------------------------------

WHEN = _k("when", "expr", ("include only when the condition is true (9.2)",
                           "включити, лише якщо умова істинна (9.2)",
                           "включить, только если условие истинно (9.2)"))
ID = _k("id", "id", ("ID — a target of |@ references (5.6)", "ID — ціль посилань |@ (5.6)",
                     "ID — цель ссылок |@ (5.6)"))
BLOCK = _k("block", "style", ("block style: spacing around the group, keep together (4.3)",
                              "стиль блока: відступи навколо групи, утримання разом (4.3)",
                              "стиль блока: отступы вокруг группы, удержание вместе (4.3)"))
STYLE_P = _k("style", "style", ("paragraph style of this element instead of the level style",
                                "абзацний стиль цього елемента замість стилю рівня",
                                "абзацный стиль этого элемента вместо стиля уровня"))
TOC = _k("toc", "bool", ("False: not in the table of contents; True: always in it (5.9)",
                         "False — не в змісті; True — у змісті завжди (5.9)",
                         "False — не в оглавлении; True — в оглавлении всегда (5.9)"))
TOC_TITLE = _k("toc_title", "string", ("other text of the table of contents entry",
                                       "інший текст рядка змісту", "другой текст строки оглавления"))
TOC_LEVEL = _k("toc_level", "int", ("level of the table of contents entry (1–10)",
                                    "рівень рядка змісту (1–10)", "уровень строки оглавления (1–10)"))
TITLE_INDEX = _k("title", "string", ("title of the index (default from the styles module)",
                                     "заголовок покажчика (типово з модуля стилів)",
                                     "заголовок указателя (по умолчанию из модуля стилей)"))
TRACK_INDEX = _k("track", "id", ("entries of this track of |parallel instead of the primary one (7.7)",
                                 "записи цього потоку |parallel замість основного (7.7)",
                                 "записи этого потока |parallel вместо основного (7.7)"))
PAGE_BREAK = _k("page_break", "bool", ("start on a new page", "почати з нової сторінки",
                                       "начать с новой страницы"))
#: svg= of |img and |figure (decision 131): an SVG string computed by code.
SVG = _k("svg", "string", ("SVG text computed by code instead of a path (8.2)",
                           "текст SVG, обчислений кодом, замість шляху (8.2)",
                           "текст SVG, вычисленный кодом, вместо пути (8.2)"))
KEY = _k("key", "string", ("key of the project key map instead of a path (9.3)",
                           "ключ карти ключів проєкту замість шляху (9.3)",
                           "ключ карты ключей проекта вместо пути (9.3)"))
LEVEL_SHIFT = _k("level_shift", "int", ("move the headings n levels down (0–5)",
                                        "зсунути заголовки на n рівнів униз (0–5)",
                                        "сдвинуть заголовки на n уровней вниз (0–5)"), "0")

#: Placement of frames (8.5): ``|img``, ``|figure``, ``|frame``.
PLACEMENT = (
    _k("place", "string", ("inline, left, center, right, inside, outside",
                           "inline, left, center, right, inside, outside",
                           "inline, left, center, right, inside, outside")),
    _k("valign", "string", ("top, middle, bottom", "top, middle, bottom", "top, middle, bottom")),
    _k("x", "length", ("exact horizontal offset instead of place", "точний зсув по горизонталі замість place",
                       "точное смещение по горизонтали вместо place")),
    _k("y", "length", ("exact vertical offset instead of valign", "точний зсув по вертикалі замість valign",
                       "точное смещение по вертикали вместо valign")),
    _k("rel", "string", ("origin: para, area (text area), page", "точка відліку: para, area (область тексту), page",
                         "точка отсчёта: para, area (область текста), page"), '"para"'),
    _k("anchor", "string", ("explicit ODF anchor: char, para, page", "явна прив'язка ODF: char, para, page",
                            "явная привязка ODF: char, para, page")),
    _k("wrap", "string", ("text wrap: none, side, both, auto, through, contour",
                          "обтікання: none, side, both, auto, through, contour",
                          "обтекание: none, side, both, auto, through, contour")),
    _k("layer", "string", ("front or back (for wrap=\"through\")", "front або back (для wrap=\"through\")",
                           "front или back (для wrap=\"through\")")),
    _k("gap", "length", ("distance of the text from the frame (one value or four sides)",
                         "відступ тексту від фрейму (одне значення або чотири сторони)",
                         "отступ текста от фрейма (одно значение или четыре стороны)")),
    _k("width", "length", ("width: \"60mm\" or \"50%\" of the text area", "ширина: \"60mm\" або \"50%\" області тексту",
                           "ширина: \"60mm\" или \"50%\" области текста")),
    _k("height", "length", ("height; one side keeps the proportions", "висота; одна сторона зберігає пропорції",
                            "высота; одна сторона сохраняет пропорции")),
    _k("rotate", "any", ("rotation", "поворот", "поворот")),
    _k("mirror", "any", ("mirroring", "віддзеркалення", "отражение")),
    _k("crop", "any", ("cropping", "обрізання", "обрезка")),
    _k("opacity", "any", ("opacity", "прозорість", "прозрачность")),
    _k("border", "string", ("frame border \"0.5pt solid #000000\"", "рамка фрейму \"0.5pt solid #000000\"",
                            "рамка фрейма \"0.5pt solid #000000\"")),
    _k("padding", "length", ("inner padding of the frame", "внутрішній відступ фрейму", "внутренний отступ фрейма")),
    _k("style", "style", ("frame style; its properties are the defaults of the arguments",
                          "стиль фрейму; його властивості — типові значення аргументів",
                          "стиль фрейма; его свойства — значения аргументов по умолчанию")),
    _k("alt", "string", ("alternative text", "альтернативний текст", "альтернативный текст")),
)

#: Formatting of table columns, rows and cells (6.6).
CASCADE = (
    _k("align", "string", ("horizontal alignment: left, center, right, justify",
                           "вирівнювання по горизонталі: left, center, right, justify",
                           "выравнивание по горизонтали: left, center, right, justify")),
    _k("valign", "string", ("vertical alignment: top, middle, bottom", "вирівнювання по вертикалі: top, middle, bottom",
                            "выравнивание по вертикали: top, middle, bottom")),
    _k("padding", "length", ("cell padding", "внутрішні відступи комірки", "внутренние отступы ячейки")),
    _k("background", "string", ("background colour", "колір фону", "цвет фона")),
    _k("paragraph", "style", ("paragraph style of the content", "абзацний стиль вмісту",
                              "абзацный стиль содержимого")),
    _k("border", "string", ("border \"0.5pt solid #000000\" or \"none\"; also border_top … border_right",
                            "обрамлення \"0.5pt solid #000000\" або \"none\"; також border_top … border_right",
                            "обрамление \"0.5pt solid #000000\" или \"none\"; также border_top … border_right")),
)

_ENV = ("environment",)
_LINE = ("line",)
_INLINE = ("inline",)


def _end(name: str) -> str:
    return f"|end {name}"


COMMANDS: tuple[Command, ...] = (
    # --- text ---------------------------------------------------------------------
    Command("link", "text", _INLINE, "4.2",
            ("external hyperlink; without a body the text is the address",
             "зовнішнє посилання; без тіла текст — сама адреса",
             "внешняя гиперссылка; без тела текст — сам адрес"),
            (_p("url", "string", ("address", "адреса", "адрес")),),
            '|link("${1:https://}"){$0}'),
    Command("fmt", "text", _INLINE, "4.4",
            ("direct formatting of a fragment (a warning: prefer character styles)",
             "пряме форматування фрагмента (попередження: краще символьні стилі)",
             "прямое форматирование фрагмента (предупреждение: лучше символьные стили)"),
            (_k("**props", "any", ("character properties: bold=True, color=\"#C00000\" …",
                                   "властивості символів: bold=True, color=\"#C00000\" …",
                                   "свойства символов: bold=True, color=\"#C00000\" …")),),
            "|fmt($1){$0}"),
    Command("set", "text", _LINE, "4.5",
            ("styles of constructs until the end of the enclosing environment",
             "стилі конструкцій до кінця охопного оточення",
             "стили конструкций до конца охватывающего окружения"),
            (_k("**keys", "style", ("keys of structure_styles: paragraph=, list=, table=, clause= …",
                                    "ключі structure_styles: paragraph=, list=, table=, clause= …",
                                    "ключи structure_styles: paragraph=, list=, table=, clause= …")),),
            "|set($1)"),
    Command("block", "text", _ENV, "4.3",
            ("block style for a group of elements", "стиль блока для групи елементів",
             "стиль блока для группы элементов"),
            (_p("style", "style", ("block style", "стиль блока", "стиль блока")), WHEN),
            '|block("${1:Ім\'я}"):\n$0\n|end block', _end("block")),
    Command("list", "text", ("line", "environment"), "5.4",
            ("style of one list: a line before the first item, or an environment",
             "стиль одного списку: рядок перед першим елементом або оточення",
             "стиль одного списка: строка перед первым элементом или окружение"),
            (_p("style", "style", ("list style", "стиль списку", "стиль списка")),),
            '|list("${1:LetterList}")\n|# $0', _end("list")),
    # --- structure ----------------------------------------------------------------
    Command("appendix", "structure", _ENV, "5.5",
            ("appendix: designation, title, own numbering scope, new page",
             "додаток: позначення, назва, власна область нумерації, нова сторінка",
             "приложение: обозначение, название, своя область нумерации, новая страница"),
            (ID, _k("title", "string", ("title", "назва", "название")),
             _k("subtitle", "string", ("line between the designation and the title",
                                       "рядок між позначенням і назвою", "строка между обозначением и названием")),
             _k("number", "int", ("explicit number", "явний номер", "явный номер")),
             _k("letter", "string", ("explicit letter", "явна літера", "явная буква")),
             _k("page", "string", ("page style of the appendix", "стиль сторінки додатка",
                                   "стиль страницы приложения")),
             BLOCK, TOC, TOC_TITLE, TOC_LEVEL, WHEN),
            '|appendix(title="${1:Назва}"):\n$0\n|end appendix', _end("appendix")),
    Command("scope", "structure", _ENV, "5.5",
            ("numbering scope with independent counters", "область нумерації з незалежними лічильниками",
             "область нумерации с независимыми счётчиками"),
            (_p("name", "string", ("name of the scope", "ім'я області", "имя области")),
             _k("prefix", "string", ("prefix of the numbers: «А» → А.1", "префікс номерів: «А» → А.1",
                                     "префикс номеров: «А» → А.1"))),
            '|scope("${1:app-a}", prefix="${2:А}"):\n$0\n|end scope', _end("scope")),
    Command("toc", "structure", _LINE, "5.9",
            ("table of contents (an index updated by Writer)", "зміст (покажчик, що оновлює Writer)",
             "оглавление (указатель, обновляемый Writer)"),
            (_k("max_level", "int", ("deepest heading level", "найглибший рівень заголовків",
                                     "самый глубокий уровень заголовков"), "3"),
             TITLE_INDEX, PAGE_BREAK, TRACK_INDEX),
            "|toc(max_level=${1:3})"),
    Command("list_of", "structure", _LINE, "5.9",
            ("list of figures, tables, abbreviations or the alphabetical index",
             "перелік рисунків, таблиць, скорочень або абетковий покажчик",
             "перечень рисунков, таблиц, сокращений или алфавитный указатель"),
            (_p("kind", "string", ("figure, table, abbr, index", "figure, table, abbr, index",
                                   "figure, table, abbr, index")), TITLE_INDEX, PAGE_BREAK, TRACK_INDEX),
            '|list_of("${1|figure,table,abbr,index|}")'),
    Command("toc_entry", "structure", _LINE, "5.9",
            ("table of contents entry pointing to the next paragraph",
             "рядок змісту із закладкою на наступний абзац",
             "строка оглавления с закладкой на следующий абзац"),
            (_p("text", "string", ("text of the entry", "текст рядка", "текст строки")),
             _k("level", "int", ("level (1–10)", "рівень (1–10)", "уровень (1–10)"), "1")),
            '|toc_entry("${1:Текст}", level=${2:1})'),
    Command("footnote", "structure", _INLINE, "5.10",
            ("footnote at the bottom of the page", "виноска внизу сторінки", "сноска внизу страницы"),
            (ID,), "|footnote{$0}"),
    Command("endnote", "structure", _INLINE, "5.10",
            ("endnote", "кінцева виноска", "концевая сноска"), (ID,), "|endnote{$0}"),
    # --- tables -------------------------------------------------------------------
    Command("table", "tables", ("environment", "line"), "6.2",
            ("table: rows |: … |& …, or rows from data", "таблиця: рядки |: … |& … або рядки з даних",
             "таблица: строки |: … |& … или строки из данных"),
            (_k("cols", "list", ("columns: widths \"40mm\", \"30%\", \"*\", \"auto\", \"20mm..60mm\" or col(…)",
                                 "стовпці: ширини \"40mm\", \"30%\", \"*\", \"auto\", \"20mm..60mm\" або col(…)",
                                 "столбцы: ширины \"40mm\", \"30%\", \"*\", \"auto\", \"20mm..60mm\" или col(…)")),
             _k("style", "style", ("table style", "стиль таблиці", "стиль таблицы")),
             _k("width", "length", ("width of the table", "ширина таблиці", "ширина таблицы"), '"100%"'),
             _k("align", "string", ("position: left, center, right", "положення: left, center, right",
                                    "положение: left, center, right"), '"left"'),
             _k("header", "int", ("number of header rows; 0 — none", "кількість рядків заголовка; 0 — без нього",
                                  "количество строк заголовка; 0 — без него"), "1"),
             _k("footer", "int", ("number of closing rows (totals)", "кількість завершальних рядків (підсумки)",
                                  "количество завершающих строк (итоги)"), "0"),
             _k("repeat_header", "bool", ("repeat the header on every page", "повторювати заголовок на кожній сторінці",
                                          "повторять заголовок на каждой странице"), "True"),
             _k("keep_rows", "bool", ("do not split a row between pages", "не розривати рядок між сторінками",
                                      "не разрывать строку между страницами"), "True"),
             _k("may_break", "bool", ("allow the table to break between pages",
                                      "дозволити розрив таблиці між сторінками",
                                      "разрешить разрыв таблицы между страницами"), "True"),
             _k("frame", "string", ("outer border", "зовнішня рамка", "внешняя рамка")),
             _k("rules", "string", ("inner lines: all, rows, cols, none", "внутрішні лінії: all, rows, cols, none",
                                    "внутренние линии: all, rows, cols, none")),
             _k("caption", "string", ("caption; numbers the table", "підпис; нумерує таблицю",
                                      "подпись; нумерует таблицу")),
             ID, BLOCK, WHEN,
             _k("data", "list", ("rows from data: a list of records, dictionaries or lists (6.9)",
                                 "рядки з даних: список записів, словників або списків (6.9)",
                                 "строки из данных: список записей, словарей или списков (6.9)")),
             _k("fields", "list", ("fields by columns", "поля за стовпцями", "поля по столбцам")),
             _k("titles", "list", ("header row for data", "рядок заголовка для даних", "строка заголовка для данных")),
             _k("live", "bool", ("also write Writer formulas", "записати також формули Writer",
                                 "записать также формулы Writer"), "False")),
            "|table(cols=[${1:\"*\", \"*\"}]):\n|: ${2:Заголовок} |& ${3:Заголовок}\n|: $0 |& \n|end table",
            _end("table")),
    Command("row", "tables", _ENV, "6.4",
            ("table row in the expanded form", "рядок таблиці в розгорнутій формі",
             "строка таблицы в развёрнутой форме"),
            (*CASCADE,
             _k("height", "length", ("row height", "висота рядка", "высота строки")),
             _k("min_height", "length", ("minimal row height", "мінімальна висота рядка", "минимальная высота строки")),
             _k("keep", "bool", ("do not split the row", "не розривати рядок", "не разрывать строку")), WHEN),
            "|row:\n|cell: $0\n|end row", _end("row")),
    Command("cell", "tables", ("inline", "environment"), "6.4",
            ("table cell in the expanded form", "комірка таблиці в розгорнутій формі",
             "ячейка таблицы в развёрнутой форме"),
            (_k("span", "int", ("merge with the next cells of the row", "об'єднати з наступними комірками рядка",
                                "объединить со следующими ячейками строки"), "1"),
             _k("rows", "int", ("merge with the cells below", "об'єднати з комірками нижче",
                                "объединить с ячейками ниже"), "1"), *CASCADE),
            "|cell(${1:span=2}){$0}", _end("cell")),
    Command("caption", "tables", _ENV, "5.8",
            ("caption of a table with markup", "підпис таблиці з розміткою", "подпись таблицы с разметкой"),
            (), "|caption:\n$0\n|end caption", _end("caption")),
    # --- pages and graphics -----------------------------------------------------------
    Command("page", "pages", ("line", "environment"), "7.3",
            ("change of the page style: from here, or for the environment",
             "зміна стилю сторінки: звідси або для оточення",
             "смена стиля страницы: отсюда или для окружения"),
            (_p("style", "style", ("page style", "стиль сторінки", "стиль страницы")),
             _k("restart", "int", ("number of the first page", "номер першої сторінки", "номер первой страницы")),
             _k("number_format", "string", ("page number format: 1, i, I, a, A", "формат номера: 1, i, I, a, A",
                                            "формат номера: 1, i, I, a, A"))),
            '|page("${1:Landscape}"):\n$0\n|end page', _end("page")),
    Command("newpage", "pages", _LINE, "7.4", ("page break", "розрив сторінки", "разрыв страницы"), (), "|newpage"),
    Command("newcolumn", "pages", _LINE, "7.4", ("column break", "перехід до наступної колонки",
                                                 "переход к следующей колонке"), (), "|newcolumn"),
    Command("section", "pages", _ENV, "7.5",
            ("section with columns", "розділ з колонками", "раздел с колонками"),
            (_k("cols", "int", ("number of columns", "кількість колонок", "количество колонок"), "1"),
             _k("widths", "list", ("widths of unequal columns", "ширини нерівних колонок", "ширины неравных колонок")),
             _k("gap", "length", ("gap between columns", "проміжок між колонками", "промежуток между колонками")),
             _k("rule", "string", ("separator line \"0.5pt solid\"", "розділова лінія \"0.5pt solid\"",
                                   "разделительная линия \"0.5pt solid\"")),
             _k("balance", "bool", ("balance the columns", "вирівнювати колонки за висотою",
                                    "выравнивать колонки по высоте"), "True"), ID, BLOCK, WHEN),
            "|section(cols=${1:2}):\n$0\n|end section", _end("section")),
    Command("header", "pages", _ENV, "7.6",
            ("page header of a page style", "верхній колонтитул стилю сторінки", "верхний колонтитул стиля страницы"),
            (_p("page", "style", ("page style", "стиль сторінки", "стиль страницы")),
             _k("which", "string", ("all, first, left, right", "all, first, left, right", "all, first, left, right"),
                '"all"')),
            '|header("${1:Portrait}"):\n$0\n|end header', _end("header")),
    Command("footer", "pages", _ENV, "7.6",
            ("page footer of a page style", "нижній колонтитул стилю сторінки", "нижний колонтитул стиля страницы"),
            (_p("page", "style", ("page style", "стиль сторінки", "стиль страницы")),
             _k("which", "string", ("all, first, left, right", "all, first, left, right", "all, first, left, right"),
                '"all"')),
            '|footer("${1:Portrait}"):\n$0\n|end footer', _end("footer")),
    Command("field.page", "pages", _INLINE, "7.6", ("page number (Writer field)", "номер сторінки (поле Writer)",
                                                    "номер страницы (поле Writer)"), (), "|field.page"),
    Command("field.pages", "pages", _INLINE, "7.6", ("number of pages (Writer field)",
                                                     "кількість сторінок (поле Writer)",
                                                     "количество страниц (поле Writer)"), (), "|field.pages"),
    Command("field.chapter", "pages", _INLINE, "7.6",
            ("title of the current heading (Writer field)", "назва поточного заголовка (поле Writer)",
             "название текущего заголовка (поле Writer)"),
            (_k("level", "int", ("heading level", "рівень заголовка", "уровень заголовка"), "1"),),
            "|field.chapter(level=${1:1})"),
    Command("field.title", "pages", _INLINE, "7.6",
            ("document title from the metadata (Writer field)", "назва документа з метаданих (поле Writer)",
             "название документа из метаданных (поле Writer)"), (), "|field.title"),
    Command("img", "pages", ("inline", "line"), "8.2",
            ("image without a caption", "зображення без підпису", "изображение без подписи"),
            (_p("path", "path", ("PNG, JPEG or SVG file, or an img(…) value", "файл PNG, JPEG або SVG чи значення img(…)",
                                 "файл PNG, JPEG или SVG либо значение img(…)")),
             KEY, SVG, *PLACEMENT, WHEN),
            '|img("${1:assets/}", height="${2:8mm}")'),
    Command("figure", "pages", _ENV, "8.3",
            ("numbered figure; the body is the caption", "нумерований рисунок; тіло — підпис",
             "нумерованный рисунок; тело — подпись"),
            (_p("path", "path", ("PNG, JPEG or SVG file, or an img(…) value", "файл PNG, JPEG або SVG чи значення img(…)",
                                 "файл PNG, JPEG или SVG либо значение img(…)")),
             KEY, SVG, ID, BLOCK, _k("caption", "string", ("caption text", "текст підпису", "текст подписи")),
             *PLACEMENT, WHEN),
            '|figure("${1:assets/}", width="${2:120mm}"):\n$0\n|end figure', _end("figure")),
    Command("frame", "pages", _ENV, "8.4",
            ("text box", "текстовий блок", "текстовый блок"),
            (ID, BLOCK, *PLACEMENT, WHEN),
            '|frame(rel="${1:page}", x="${2:120mm}", y="${3:25mm}", width="${4:70mm}"):\n$0\n|end frame',
            _end("frame")),
    Command("watermark", "pages", _LINE, "8.6",
            ("watermark on all or the listed page styles", "водяний знак на всіх або перелічених стилях сторінок",
             "водяной знак на всех или перечисленных стилях страниц"),
            (_p("mark", "any", ("text or img(…)", "текст або img(…)", "текст или img(…)")),
             _k("pages", "list", ("page styles", "стилі сторінок", "стили страниц")),
             _k("angle", "int", ("angle in degrees", "кут у градусах", "угол в градусах"), "45"),
             _k("color", "string", ("colour of the text", "колір тексту", "цвет текста"), '"#C8C8C8"'),
             _k("size", "length", ("size of the text", "розмір тексту", "размер текста")),
             _k("opacity", "int", ("opacity, %", "непрозорість, %", "непрозрачность, %"), "50"),
             _k("font", "string", ("font", "шрифт", "шрифт"))),
            '|watermark("${1:ПРОЄКТ}")'),
    # --- parallel tracks (7.7, decision 134) --------------------------------------------
    Command("parallel", "pages", _ENV, "7.7",
            ("parallel tracks: texts side by side whose segments start level (bilingual contract, "
             "old and new wording, text and comment)",
             "паралельні потоки: тексти поруч, сегменти яких починаються на одному рівні (двомовний договір, "
             "стара й нова редакція, текст і коментар)",
             "параллельные потоки: тексты рядом, сегменты которых начинаются на одном уровне (двуязычный договор, "
             "старая и новая редакция, текст и комментарий)"),
            (_k("langs", "list", ("tracks by languages: [\"uk\", \"en\"]", "потоки за мовами: [\"uk\", \"en\"]",
                                  "потоки по языкам: [\"uk\", \"en\"]")),
             _k("tracks", "list", ("tracks: track(…) values or ids", "потоки: значення track(…) або id",
                                   "потоки: значения track(…) или id")),
             _k("primary", "id", ("id of the primary track", "id основного потоку", "id основного потока"),
                "first track"),
             _k("widths", "list", ("widths of the tracks, as cols of a table", "ширини потоків, як cols таблиці",
                                   "ширины потоков, как cols таблицы")),
             _k("gap", "length", ("gap between the tracks", "проміжок між потоками", "промежуток между потоками"),
                '"6mm"'),
             _k("rule", "string", ("separator line \"0.3pt solid #999999\"", "розділова лінія \"0.3pt solid #999999\"",
                                   "разделительная линия \"0.3pt solid #999999\"")),
             _k("header", "bool", ("row of track titles, repeated on every page",
                                   "рядок назв потоків, повторюється на кожній сторінці",
                                   "строка названий потоков, повторяется на каждой странице")),
             _k("parity", "string", ("correspondence check: structure, translation, none",
                                     "перевірка відповідності: structure, translation, none",
                                     "проверка соответствия: structure, translation, none"), '"structure"'),
             _k("style", "style", ("table style of the output", "стиль таблиці виводу", "стиль таблицы вывода"),
                '"ParallelTable"'),
             _k("keep_rows", "bool", ("do not break segments between pages", "не розривати сегменти між сторінками",
                                      "не разрывать сегменты между страницами"), "False"),
             _k("id", "id", ("identifier of the environment", "ідентифікатор оточення", "идентификатор окружения"))),
            '|parallel(langs=["${1:uk}", "${2:en}"]):\n|segment(id="${3:intro}"):\n|track("${1:uk}"):\n$0\n'
            '|track("${2:en}"):\n\n|end segment\n|end parallel', _end("parallel")),
    Command("segment", "pages", _ENV + _LINE, "7.7",
            ("segment of |parallel: a block per track, the starts are level",
             "сегмент |parallel: блок на кожен потік, початки на одному рівні",
             "сегмент |parallel: блок на каждый поток, начала на одном уровне"),
            (_k("id", "id", ("segment id (messages, primula parallel)", "id сегмента (повідомлення, primula parallel)",
                             "id сегмента (сообщения, primula parallel)")),
             _k("span", "string", ("\"all\" — one block over every track", "\"all\" — один блок на всі потоки",
                                   "\"all\" — один блок на все потоки")),
             _k("parity", "string", ("correspondence check of this segment", "перевірка відповідності цього сегмента",
                                     "проверка соответствия этого сегмента")),
             _k("keep", "bool", ("do not break between pages", "не розривати між сторінками",
                                 "не разрывать между страницами"), "False"),
             _k("status", "string", ("status label: draft, translated, reviewed…",
                                     "мітка стану: draft, translated, reviewed…",
                                     "метка состояния: draft, translated, reviewed…")), WHEN),
            '|segment(id="${1:id}"):\n|track("${2:uk}"):\n$0\n|end segment', _end("segment")),
    Command("track", "pages", _ENV + _INLINE, "7.7",
            ("block of a track inside a segment; ends at the next |track or at the end of the segment",
             "блок потоку в сегменті; закінчується наступним |track або кінцем сегмента",
             "блок потока в сегменте; кончается следующим |track или концом сегмента"),
            (_p("track", "id", ("id of the track", "id потоку", "id потока")),
             _k("status", "string", ("status label of the block", "мітка стану блоку", "метка состояния блока")),
             _k("rev", "string", ("hashes of the confirmed translation (primula parallel --stamp)",
                                  "хеші підтвердженого перекладу (primula parallel --stamp)",
                                  "хеши подтверждённого перевода (primula parallel --stamp)")), WHEN),
            '|track("${1:en}"):\n$0'),
    # --- technical documents -------------------------------------------------------------
    Command("abbr", "techdoc", _INLINE, "9.4",
            ("abbreviation: definition and use, or use", "скорочення: визначення й вживання або вживання",
             "сокращение: определение и употребление или употребление"),
            (_p("short", "string", ("abbreviation", "скорочення", "сокращение")),
             _p("full", "string", ("expansion (in the definition)", "розшифрування (у визначенні)",
                                   "расшифровка (в определении)")),
             _k("text", "string", ("form of the expansion here (case)", "форма розшифрування тут (відмінок)",
                                   "форма расшифровки здесь (падеж)")),
             _k("show", "bool", ("False: definition without output", "False — визначення без виведення",
                                 "False — определение без вывода"), "True")),
            '|abbr("${1:ПЗ}", "${2:програмне забезпечення}")'),
    Command("index", "techdoc", ("inline", "line"), "9.5",
            ("entry of the alphabetical index", "елемент абеткового покажчика", "элемент алфавитного указателя"),
            (_p("term", "string", ("term", "термін", "термин")),
             _k("sub", "string", ("subterm", "підтермін", "подтермин"))),
            '|index("${1:термін}")'),
    # --- fragments, modules, parts -----------------------------------------------------------
    Command("include", "modules", _LINE, "10.2",
            ("insert a fragment", "вставити фрагмент", "вставить фрагмент"),
            (_p("path", "path", ("fragment (.f.prml may be omitted)", "фрагмент (.f.prml можна не писати)",
                                 "фрагмент (.f.prml можно не писать)")),
             _k("part", "string", ("only the part |part(\"name\"):", "лише частина |part(\"ім'я\"):",
                                   "только часть |part(\"имя\"):")),
             KEY,
             _k("ns", "string", ("namespace of the exports and prefix of the IDs",
                                 "простір імен експорту й префікс ID", "пространство имён экспорта и префикс ID")),
             _k("rename", "dict", ("renamed exports", "перейменування експорту", "переименование экспорта")),
             LEVEL_SHIFT,
             _k("**params", "any", ("parameters of the fragment", "параметри фрагмента", "параметры фрагмента"))),
            '|include("${1:fragments/}")'),
    Command("import", "modules", _LINE, "10.3",
            ("connect a module of definitions", "підключити модуль визначень", "подключить модуль определений"),
            (_p("path", "path", ("module (.m.prml may be omitted)", "модуль (.m.prml можна не писати)",
                                 "модуль (.m.prml можно не писать)")),
             _p("*names", "string", ("names to use without the prefix", "імена без префікса",
                                     "имена без префикса")),
             _k("alias", "string", ("name of the namespace", "ім'я простору імен", "имя пространства имён"))),
            '|import("${1:lib/}")'),
    Command("document", "modules", _LINE, "10.7",
            ("part of a compound document (own scope, parameters, new page)",
             "частина зведеного документа (своя область, параметри, нова сторінка)",
             "часть сводного документа (своя область, параметры, новая страница)"),
            (_p("path", "path", ("document", "документ", "документ")),
             _k("scope", "string", ("numbering scope and ID prefix", "область нумерації й префікс ID",
                                    "область нумерации и префикс ID")),
             _k("params", "dict", ("parameters of the part", "параметри частини", "параметры части")),
             _k("page", "style", ("page style of the part", "стиль сторінки частини", "стиль страницы части")),
             LEVEL_SHIFT, WHEN),
            '|document("${1:act.prml}", scope="${2:act1}")'),
    Command("part", "modules", _ENV, "10.2",
            ("named part of a fragment for |include(part=…)", "іменована частина фрагмента для |include(part=…)",
             "именованная часть фрагмента для |include(part=…)"),
            (_p("name", "string", ("name of the part", "ім'я частини", "имя части")),),
            '|part("${1:name}"):\n$0\n|end part', _end("part")),
    Command("export", "modules", _LINE, "10.4",
            ("export names of a fragment into the document", "експортувати імена фрагмента в документ",
             "экспортировать имена фрагмента в документ"),
            (_p("*names", "string", ("names the fragment defines, exported as they are (decision 135)",
                                     "імена, визначені у фрагменті, експортуються як є (рішення 135)",
                                     "имена, определённые во фрагменте, экспортируются как есть (решение 135)")),
             _k("**names", "any", ("name=value", "ім'я=значення", "имя=значение"))), "|export(${1:name}=$0)"),
    # --- code and data ---------------------------------------------------------------------
    Command("let", "code", _LINE, "10.4",
            ("define names", "визначити імена", "определить имена"),
            (_k("**names", "any", ("name=value", "ім'я=значення", "имя=значение")),
             _k("export", "bool", ("export from a fragment", "експортувати з фрагмента", "экспортировать из фрагмента"),
                "False"),
             _k("override", "bool", ("override an export of a fragment", "перекрити експорт фрагмента",
                                     "перекрыть экспорт фрагмента"), "False")),
            "|let(${1:name}=$0)"),
    Command("code", "code", _ENV, "3.7",
            ("block of code of the computing core", "блок коду обчислювального ядра",
             "блок кода вычислительного ядра"), (), "|code:\n$0\n|end", "|end"),
    Command("comment", "code", _ENV, "3.7", ("block comment", "блоковий коментар", "блочный комментарий"),
            (), "|comment:\n$0\n|end", "|end"),
    Command("verbatim", "code", _ENV, "3.7",
            ("literal block", "буквальний блок", "буквальный блок"),
            (_k("end", "string", ("own closing marker", "власний маркер кінця", "собственный маркер конца"),
                '"|end"'),),
            "|verbatim:\n$0\n|end", "|end"),
    Command("if", "code", ("inline", "environment"), "9.2",
            ("conditional content", "умовний вміст", "условное содержимое"),
            (_p("condition", "expr", ("condition", "умова", "условие")),),
            "|if(${1:condition}):\n$0\n|endif", "|endif"),
    Command("elif", "code", ("inline", "environment"), "9.2",
            ("another branch of |if", "інша гілка |if", "другая ветка |if"),
            (_p("condition", "expr", ("condition", "умова", "условие")),), "|elif(${1:condition}):"),
    Command("else", "code", ("inline", "environment"), "9.2",
            ("last branch of |if", "остання гілка |if", "последняя ветка |if"), (), "|else:"),
    Command("for", "code", ("inline", "environment"), "6.9",
            ("loop over a list", "цикл за списком", "цикл по списку"),
            (_p("loop", "expr", ("x in items", "x in items", "x in items")),),
            "|for(${1:x} in ${2:items}):\n$0\n|endfor", "|endfor"),
    Command("def", "code", _ENV, "3.2",
            ("macro: a user command", "макрос: команда користувача", "макрос: пользовательская команда"),
            (_p("signature", "expr", ("name(parameters, body=None)", "ім'я(параметри, body=None)",
                                      "имя(параметры, body=None)")),),
            "|def ${1:name}(${2:body}):\n$0\n|enddef", "|enddef"),
    Command("call", "code", ("inline", "environment"), "3.2",
            ("dynamic call of a function as a command", "динамічний виклик функції як команди",
             "динамический вызов функции как команды"),
            (_p("function", "expr", ("function", "функція", "функция")),
             _p("*args", "any", ("arguments", "аргументи", "аргументы"))),
            "|call(${1:fn}){$0}"),
)


SHORT_FORMS: tuple[Short, ...] = (
    Short("||", "anywhere", "3.3", ("literal |", "літерал |", "литерал |"), "||"),
    Short("|{ |}", "anywhere", "3.3", ("literal braces", "літеральні фігурні дужки", "литеральные фигурные скобки"),
          "|{"),
    Short("|;", "anywhere", "3.3", ("empty separator: the end of a command name", "порожній роздільник: межа імені команди",
                                    "пустой разделитель: граница имени команды"), "|;"),
    Short("|%", "anywhere", "3.7", ("comment until the end of the line", "коментар до кінця рядка",
                                    "комментарий до конца строки"), "|% $0", "code"),
    Short("|(…)", "anywhere", "4.2", ("value of an expression as text", "значення виразу як текст",
                                      "значение выражения как текст"), "|($0)", "code"),
    Short("|\\", "inline", "3.3", ("line break in a paragraph", "розрив рядка в абзаці", "разрыв строки в абзаце"),
          "|\\"),
    Short("|~", "inline", "3.3", ("no-break space", "нерозривний пробіл", "неразрывный пробел"), "|~"),
    Short("|*{…}", "inline", "3.3", ("bold", "напівжирний", "полужирный"), "|*{$0}", style="Strong"),
    Short("|/{…}", "inline", "3.3", ("italic", "курсив", "курсив"), "|/{$0}", style="Emphasis"),
    Short("|_{…}", "inline", "3.3", ("underline", "підкреслення", "подчёркивание"), "|_{$0}", style="Underline"),
    Short("|^{…}", "inline", "3.3", ("superscript", "верхній індекс", "верхний индекс"), "|^{$0}",
          style="Superscript"),
    Short("|,{…}", "inline", "3.3", ("subscript", "нижній індекс", "нижний индекс"), "|,{$0}", style="Subscript"),
    Short("|—{…}", "inline", "3.3", ("strike-through", "закреслення", "зачёркивание"), "|—{$0}", style="StrikeText"),
    Short("|`{…}", "inline", "3.3", ("monospace: designations, codes", "моноширинний: позначення, коди",
                                     "моноширинный: обозначения, коды"), "|`{$0}", style="Code"),
    Short("|\"{…}", "inline", "4.2", ("quotes of the document language", "лапки мови документа",
                                      "кавычки языка документа"), "|\"{$0}"),
    Short("|?{…}", "inline", "4.2", ("draft placeholder", "заповнювач чернетки", "заполнитель черновика"), "|?{$0}",
          style="Placeholder"),
    Short("|.Ім'я{…}", "inline", "4.3", ("character style", "символьний стиль", "символьный стиль"),
          "|.${1:Style}{$0}"),
    Short("|.Ім'я:", "line", "4.3", ("paragraph style (a line or an environment |end.Ім'я)",
                                     "абзацний стиль (рядок або оточення |end.Ім'я)",
                                     "абзацный стиль (строка или окружение |end.Ім'я)"), "|.${1:Style}: $0"),
    Short("|@(\"id\")", "inline", "5.7", ("cross-reference: number, label, title, page",
                                          "перехресне посилання: номер, label, title, page",
                                          "перекрёстная ссылка: номер, label, title, page"),
          '|@("${1:id}"${2:, "label"})', "structure"),
    Short("|<", "line", "5.2", ("heading; the number of < is the level (1–6), or level=",
                                "заголовок; кількість < — рівень (1–6) або level=",
                                "заголовок; количество < — уровень (1–6) или level="), "|< $0", "structure"),
    Short("|>", "line", "5.3", ("clause; the number of > is the level (environment |end>)",
                                "пункт; кількість > — рівень (оточення |end>)",
                                "пункт; количество > — уровень (окружение |end>)"), "|> $0", "structure"),
    Short("|-", "line", "5.4", ("bulleted list item; the length is the level",
                                "маркований елемент списку; довжина — рівень",
                                "маркированный элемент списка; длина — уровень"), "|- $0", "structure"),
    Short("|#", "line", "5.4", ("numbered list item; the length is the level",
                                "нумерований елемент списку; довжина — рівень",
                                "нумерованный элемент списка; длина — уровень"), "|# $0", "structure"),
    Short("|!(\"kind\")", "line", "9.1", ("admonition or note: danger, warning, caution, notice, note, tip",
                                          "попередження або примітка: danger, warning, caution, notice, note, tip",
                                          "предупреждение или примечание: danger, warning, caution, notice, note, tip"),
          '|!("${1|note,tip,notice,caution,warning,danger|}") $0', "techdoc"),
    Short("|:", "line", "6.4", ("table row", "рядок таблиці", "строка таблицы"), "|: $0", "tables"),
    Short("|&", "inline", "6.4", ("table cell", "комірка таблиці", "ячейка таблицы"), "|& $0", "tables"),
    Short("|=(…)", "inline", "6.8", ("deferred formula of a cell", "відкладена формула комірки",
                                     "отложенная формула ячейки"), "|=($0)", "tables"),
)

#: Arguments of the short forms that take them (3.3, 5.2-5.4, 9.1).
SHORT_ARGS: dict[str, tuple[Arg, ...]] = {
    "|<": (ID, _k("number", "bool", ("False: unnumbered", "False — без номера", "False — без номера"), "True"),
           _k("level", "int", ("level 1–6 with a single <", "рівень 1–6 при одному <", "уровень 1–6 при одном <")),
           TOC, TOC_TITLE, TOC_LEVEL, STYLE_P, WHEN),
    "|>": (ID, _k("continues", "id", ("continue a clause after other text", "продовжити пункт після іншого тексту",
                                      "продолжить пункт после другого текста")),
           BLOCK, STYLE_P, TOC, TOC_TITLE, TOC_LEVEL, WHEN),
    "|#": (_k("id", "string", ("name of the numbered sequence", "ім'я нумерованої послідовності",
                               "имя нумерованной последовательности")),
           _k("start", "int", ("first number", "перший номер", "первый номер")),
           _k("continues", "string", ("continue the sequence", "продовжити послідовність",
                                      "продолжить последовательность"))),
    "|!(\"kind\")": (_p("kind", "string", ("danger, warning, caution, notice, note, tip",
                                           "danger, warning, caution, notice, note, tip",
                                           "danger, warning, caution, notice, note, tip")),
                     _k("hazard", "string", ("kind and source of the hazard", "вид і джерело небезпеки",
                                             "вид и источник опасности")),
                     _k("consequence", "string", ("consequences", "наслідки", "последствия")),
                     _k("symbol", "path", ("safety sign: file or name", "знак безпеки: файл або ім'я",
                                           "знак безопасности: файл или имя")), ID, BLOCK, WHEN),
    "|@(\"id\")": (_p("id", "id", ("target", "ціль", "цель")),
                   _p("mode", "string", ("number (default), label, title, page", "номер (типово), label, title, page",
                                         "номер (по умолчанию), label, title, page")),
                   _k("case", "string", ("case of the label: nom, gen, dat, acc, ins, loc",
                                         "відмінок мітки: nom, gen, dat, acc, ins, loc",
                                         "падеж метки: nom, gen, dat, acc, ins, loc"))),
    "|:": (*CASCADE, _k("keep", "bool", ("do not split the row", "не розривати рядок", "не разрывать строку")), WHEN),
    "|&": (_k("span", "int", ("merge with the next cells", "об'єднати з наступними комірками",
                              "объединить со следующими ячейками"), "1"),
           _k("rows", "int", ("merge with the cells below", "об'єднати з комірками нижче",
                              "объединить с ячейками ниже"), "1"), *CASCADE),
}

CLOSINGS: tuple[Closing, ...] = (
    Closing("|end", "", ("closes the nearest environment, without a check", "закриває найближче оточення без перевірки",
                         "закрывает ближайшее окружение без проверки")),
    Closing("|end name", "|name:", ("closes a named environment, with a check", "закриває іменоване оточення з перевіркою",
                                    "закрывает именованное окружение с проверкой")),
    Closing("|end>", "|>", ("closes a clause of this level", "закриває пункт цього рівня",
                            "закрывает пункт этого уровня")),
    Closing("|end!", "|!", ("closes an admonition", "закриває попередження", "закрывает предупреждение")),
    Closing("|end.Ім'я", "|.Ім'я:", ("closes a paragraph style", "закриває абзацний стиль",
                                     "закрывает абзацный стиль")),
    Closing("|endif", "|if", ("closes |if", "закриває |if", "закрывает |if")),
    Closing("|endfor", "|for", ("closes |for", "закриває |for", "закрывает |for")),
    Closing("|enddef", "|def", ("closes |def", "закриває |def", "закрывает |def")),
)


def _arg(arg: Arg, index: int) -> dict[str, Any]:
    return {"name": arg.name, "positional": arg.positional, "type": arg.type, "default": arg.default,
            "summary": arg.text[index]}


def catalogue(language: str) -> dict[str, Any]:
    """The catalogue as a JSON-compatible dictionary in ``language`` (en, uk, ru)."""
    from primula import __version__

    index = _LANGS.index(language) if language in _LANGS else 0
    commands = [{"name": c.name, "category": c.category, "forms": list(c.forms), "section": c.section,
                 "summary": c.text[index], "close": c.close, "snippet": c.snippet,
                 "args": [_arg(a, index) for a in c.args]} for c in COMMANDS]
    shorts = [{"form": s.form, "where": s.where, "category": s.category, "section": s.section,
               "summary": s.text[index], "snippet": s.snippet, "style": s.style,
               "args": [_arg(a, index) for a in SHORT_ARGS.get(s.form, ())]} for s in SHORT_FORMS]
    closings = [{"form": c.form, "closes": c.closes, "section": c.section, "summary": c.text[index]}
                for c in CLOSINGS]
    from primula.functions import functions_catalogue
    from primula.header_keys import header_catalogue

    return {"schema": SCHEMA, "language": _LANGS[index], "version": __version__,
            "categories": [{"id": key, "title": titles[index]} for key, titles in CATEGORIES],
            "commands": commands, "short_forms": shorts, "closings": closings,
            **functions_catalogue(index, _LANGS[index]), **header_catalogue(index)}


def render_text(data: dict[str, Any]) -> str:
    """A plain-text listing of the catalogue (``primula commands``)."""
    lines: list[str] = []
    titles = {c["id"]: c["title"] for c in data["categories"]}
    for category in titles:
        entries = [c for c in data["commands"] if c["category"] == category]
        shorts = [s for s in data["short_forms"] if s["category"] == category]
        if not entries and not shorts:
            continue
        lines.append(f"{titles[category]}:")
        rows = [(short["form"], short["summary"], short["section"]) for short in shorts]
        rows += [(f"|{c['name']}(" + ", ".join(a["name"] for a in c["args"]) + ")", c["summary"], c["section"])
                 for c in entries]
        for form, summary, section in rows:
            text = f"{summary}  [{section}]"
            if len(form) <= 22:
                lines.append(f"  {form:<22} {text}")
            else:
                # A long signature on its own line, the description under it.
                lines += [f"  {form}", f"  {'':<22} {text}"]
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
