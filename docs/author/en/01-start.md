<!-- translation: source=docs/author/ru/01-start.md sections=94ebfc53 9efb2beb 576d9a8e bfecfea0 1e33b025 9613b006 1d9db58e -->
<!-- spec: 2.1 2.2 2.3 3.1 3.3 3.4 3.5 3.6 4.1 4.2 5.2 5.3 5.4 14.1 -->
# First document

## File

A Primula document is a text file in UTF-8 with the extension `.prml`. Files of other kinds may lie next to it; the sub-extension tells them apart:

| File | Kind |
| --- | --- |
| `договір.prml` | document — an ODT is built from it |
| `умови.f.prml` | fragment — a piece of text inserted with `\|include` |
| `бізнес.m.prml` | module — macros and functions for `\|import` |
| `стилі.s.prml` | styles module |
| `project.p.prml` | project file |

## YAML header

The file starts with a header between `---` lines. It holds the data of the document, without computations:

```prml
---
doc:
  title: "Довідка про співпрацю"
  language: uk-UA
params:
  організація: "ТОВ «Приклад»"
  рік: 2026
---
|(організація) співпрацює з нами з |(рік) року.
```

- `doc:` — ODT metadata: title, language, author, number, revision and so on. In the text they are available as `|(doc.title)`. The language `uk-UA` sets the quotes, hyphenation, the format of dates and of sums in words.
- `params:` — parameters of the document. The text and the code see them by name. A parameter can be replaced when building: `primula build довідка.prml --param рік=2027`.

All keys are listed in the appendix [“Header keys”](generated/header-keys.md).

## Text and paragraphs

Paragraphs are separated by a blank line. A line break inside a paragraph is a space, so a long paragraph can be wrapped as convenient.

Everything that is not plain text starts with `|`. What follows the bar defines the construct:

- a letter — a command: `|toc`, `|table(…)`;
- `(` — the value of an expression: `|(організація)`;
- a punctuation mark — a short form: `|<` heading, `|>` clause, `|*{…}` bold;
- a second bar — the bar itself: `||`.

Inline formatting (the placeholder in this example gives the expected warning P2635):

```prml error=P2635
Строк дії — |*{до 31.12.2026}, умови — |/{див. додаток}, код |`{UA-17}.
Назва документа в лапках мови документа: |"{Положення про закупівлі}.
Незаповнене місце в чернетці: |?{прізвище}.
```

Quotes `|"{…}` follow the document language («…» for Ukrainian). A placeholder `|?{…}` is highlighted and gives a warning in the check, so a draft does not reach a release unnoticed (`--strict` turns the warning into an error).

## Headings, clauses, lists

```prml
|<(number=False) Положення про відрядження
|< Загальні положення
|> Положення визначає порядок направлення працівників у відрядження.
|> Строк відрядження не перевищує 30 календарних днів.
|>> Строк може бути продовжено наказом керівника.
|< Документи
Працівник отримує:
|- посвідчення про відрядження;
|- кошторис витрат.
```

- `|<` is a level 1 heading, `|<<` — level 2, and so on up to six. The translator sets the numbers; `number=False` — a heading without a number (the title of the document).
- `|>` is a clause, `|>>` — a subclause. Clauses are numbered within a section: “1.1.”, “1.2.”, “1.2.1.” (the styles set decides the look of the numbers: in a report after DSTU 3008 there is no final period).
- `|-` is a bulleted list item, `|#` — a numbered one; `|--`, `|##` — the next level.

A clause, a heading and a list item are line forms: they end at the end of the line. A clause of several paragraphs is written as an environment and closed with `|end>`:

```prml
|>:
Перший абзац пункту.

Другий абзац того ж пункту.
|end>
```

A list and a table right after a clause belong to it; an ordinary paragraph after a clause is no longer part of it.

## Check and build

```sh
primula check довідка.prml          # check without writing a file
primula build довідка.prml          # довідка.odt next to the source
primula build довідка.prml --pdf    # a PDF as well (needs LibreOffice)
```

The check reports errors and warnings with the line and column; what to do with them is on the page [“Messages of the translator”](08-messages.md). In Studio the same commands are “Check document” (`Ctrl+Shift+Enter`) and “Build document (ODT and PDF)” (`F9`); a click on a message opens its line.

## Default look

When a document names no styles, the built-in set `std/styles/default` applies: Liberation Sans 11 pt, A4 margins, the look of headings, tables, footnotes. For business documents, letters, instructions and reports the kit has ready sets; one header line names one, for example `styles: [std/styles/business]`. More — on the page [“Styles”](07-styles.md).
