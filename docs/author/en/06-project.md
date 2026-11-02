<!-- translation: source=docs/author/ru/06-project.md sections=ac21902d ed618ab9 0f2d968f 0ecf8e58 28139212 4c88988a 4666df39 42f79e1f 8f03baf2 a698ee9f 448f3597 9fe170b6 abc8222f -->
<!-- spec: 5.7 9.3 10.1 10.2 10.3 10.4 10.5 10.6 10.7 11.7 -->
# Project of several documents

When there are several documents — a contract, acts, invoices, letters of one company — the shared data, styles and repeated texts are collected in a project. A project is a directory with the file `project.p.prml`. The translator finds it itself, going up from the document (up to a directory with `.git`).

```
договори-2026/
  project.p.prml        parameters, styles, keys, build targets
  договір.prml
  акт.prml
  fragments/            texts for |include (*.f.prml)
  lib/                  macros and functions for |import (*.m.prml)
  styles/               your own styles module (*.s.prml)
  data/                 CSV, YAML, JSON
```

## Project file

```prml file=project.p.prml
---
kind: project
name: "Договори 2026"
language: uk-UA
styles: [styles/компанія.s.prml]
doc_defaults: {organization: "ТОВ «Виконавець»", creator: "Відділ договорів"}
params:
  місто: "м. Харків"
  виконавець: {назва: "ТОВ «Виконавець»", код: "00000000", директор: "П. П. Петренко"}
  ставка_пдв: 20
targets:
  - {source: договір.prml, output: out/договір.odt, pdf: true}
---
```

- `params:` — shared parameters. A document sees them by name (`|(місто)`) and as `|(project.місто)`. A document parameter with the same name replaces the project value for that document.
- `doc_defaults:` — default ODT metadata for all documents; the `doc:` key of a document replaces them one by one.
- `styles:` — styles modules of the project; they apply to all documents.
- `targets:` — targets of the batch build.

The project's own styles module builds on a set of the kit (page [“Styles”](07-styles.md)):

```prml file=styles/компанія.s.prml
---
kind: styles
extends: std/styles/business
paragraphs:
  Реквізити: {parent: Details, keep_together: true}
---
```

## A document of the project

```prml
---
doc: {title: "Договір про надання послуг"}
---
|(виконавець.назва), |(місто). Ставка ПДВ — |(percent(ставка_пдв)).

|.Реквізити: Код ЄДРПОУ |(виконавець.код)
```

The document names neither styles nor a language: everything comes from the project.

## Fragments: shared text

A fragment `*.f.prml` is a piece of text to insert. The parameters of a fragment are declared in its header and passed as arguments of `|include`:

```prml file=fragments/гарантія.f.prml
---
params: {місяців: 12}
---
|> Гарантійний строк становить |(місяців) |(plural(місяців, "місяць", "місяці", "місяців")).
```

```prml
|< Гарантія
|include("fragments/гарантія.f.prml", місяців=24)
```

- The path is relative to the file with the command; the extension may be omitted (`fragments/гарантія`).
- Names defined in a fragment are not visible to the document; to pass a value out, the fragment exports it: `|export(строк=…)`, a function — with the decorator `@export` above `def`, a ready macro — `|export("підпис")` (page ["Code"](10-code.md#modules-and-fragments)).
- A part of a fragment is marked `|part("назва"):` … `|end part` and inserted with `|include("file", part="назва")`.

## Modules: macros and functions

A module `*.m.prml` holds only definitions — macros `|def`, functions and data in `|code:`. It has no text.

```prml file=lib/підписи.m.prml
|def підпис(сторона, особа):
|.SignatureRole: |(сторона)
|.SignatureLine: ______________ |(особа)
|enddef
```

```prml
|import("lib/підписи")
|підписи.підпис("Виконавець", виконавець.директор)
```

After `|import("lib/підписи")` the definitions are available as `підписи.name`; `|import("lib/підписи", "підпис")` — without the prefix, `alias="п"` — under a short name. Nothing needs to be exported from a module: all names except those starting with `_` are public. An `|import` of the document also works in its fragments. A module is evaluated once per build.

### A library shared by several projects

An `|import` path does not leave the project root, but a symbolic link created inside the project may lead to a shared directory (decision 136):

```sh
ln -s ../shared-lib lib     # in the project root
```

Then `|import("lib/ціни")` takes the module from `../shared-lib`. The build gives warning P2639 with the name of the link and its target: a directory outside the project is not in the source archive, so keep it together with the projects (or in the same repository). Paths inside the library are counted from `lib/…`, and `../` in the text still does not leave the root. In the report and messages the file is written as `lib/ціни.m.prml`.

## Data from files

```csv file=data/акти.csv
номер,дата,сума
1,2026-10-31,5400.00
2,2026-11-30,5400.00
```

```prml
|code:
акти = load_csv("data/акти.csv", types={"номер": "decimal", "дата": "datetime", "сума": "money"})
|end
|for(а in акти):
|- Акт № |(а.номер) від |(fmt_date(а.дата, "short")) на |(money(а.сума, "UAH")).
|endfor
```

Without `types=` all CSV values are strings (codes with leading zeros stay intact). YAML and JSON are read by `load_yaml` and `load_json`; mappings become records with dot access.

Spreadsheets of LibreOffice Calc and Excel are read by `load_ods` and `load_xlsx` (decision 138): the sheet — `sheet="Позиції"` or a number from 1, the range — `range="A1:D20"`, the first row — field names (`header=False` — fields `A`, `B`, …), `types` — as for CSV.

```prml skip
|code:
позиції = load_ods("data/позиції.ods", sheet="Позиції", types={"ціна": "money"})
|end
```

Formulas are not computed: the result saved in the file is taken — save the spreadsheet in Calc or Excel after editing it. Numbers are `decimal` of up to 15 significant digits, dates are `datetime`; an error in a cell (`#DIV/0!`) or a formula without a result stops the build with the name of the sheet and the cell. Save `.xls` files as `.xlsx` or `.ods` first.

`load_text` returns the whole text file as one string (decision 140): UTF-8, line ends LF, no parsing. It keeps the SVG of a picture, a sign or a diagram outside the document, to be put in with `svg=`:

```prml skip
|img(svg=load_text("img/знак.svg"), width="12mm")
```

## Building the project

```sh
primula build project.p.prml --pdf      # all targets of the project
primula check project.p.prml            # check all targets without writing
primula build договір.prml              # one document (with the project's parameters and styles)
primula check project.p.prml --dump-project   # the project description as JSON
```

Targets can be made by code: the code section of the project file (after the header) reads data and calls `build()` — for example, an act per CSV row:

```prml skip
---
kind: project
---
for row in load_csv("data/акти.csv", types={"номер": "decimal", "сума": "money"}):
    build("акт.prml", params={"номер": row.номер, "сума": row.сума}, output=f"out/акт-{row.номер}.odt", pdf=True)
```

An error in one target does not stop the others. A complete example with a contract, acts from CSV, a key map and an assembled package — `examples/07-project`.

## Export to Markdown, HTML, DOCX

`primula export` writes the evaluated document to other formats through [pandoc](https://pandoc.org): numbers of clauses, references, notes, tables and captions are kept, page layout (headers, footers, columns, page numbers) is not.

```sh
primula export договір.prml                    # договір.md
primula export договір.prml --to html          # one HTML file with the images
primula export договір.prml --to docx          # paragraph styles by name (custom-style)
primula export договір.prml --to json          # the pandoc AST, no pandoc needed
```

## Quick view: primula view

`primula view` builds the document in a temporary directory (ODT and PDF, as `build --pdf` does), opens the PDF in a viewer and deletes the files when the window is closed. If the build fails, the build log is shown instead of the PDF, in the terminal or in a window. The command is meant for file managers: the short name `primula-view` lies next to `primula`.

```sh
primula view договір.prml
primula view договір.prml --param номер=12 --viewer "okular --unique"
primula view --text договір.prml | less        # no LibreOffice: plain text through pandoc, about a second
```

The viewer is taken from `--viewer`, then from the variable `PRIMULA_VIEWER`, then it is the PDF viewer of the desktop (okular, evince, atril, xreader, zathura, mupdf, qpdfview), then `xdg-open`. A viewer that is given or recognised is waited for; `xdg-open` returns at once, so its files stay in `$XDG_RUNTIME_DIR/primula-view` and are deleted later. LibreOffice starts with a profile in `~/.cache/primula`, which speeds up repeated runs a little; most of the time goes to the layout in LibreOffice, so a document of several pages takes a few seconds, and `--text` is for a quick look at the text.

F3 in Midnight Commander goes into `~/.config/mc/mc.ext.ini`:

```ini
[primula]
Extensions=prml
View=primula-view %f
```

For the text in the terminal itself: `View=%view{ascii} primula view --text %f`.

## Assembled document

Several documents are built into one ODT with the command `|document`:

```prml skip
|document("договір.prml", scope="договір")
|document("акт.prml", scope="акт1", params={"номер": 1})
```

Every part starts on a new page, is numbered in its own scope and evaluated separately; the table of contents and the page numbering are shared. A reference into another part uses the full ID: `|@("акт1:перелік")`.

## References to another document

An act can refer to a clause of the contract when the contract is named in `ref_documents:` of the project and the act lists it in `references:` of its header: `|@("оплата", "label")` in the act gives “п. 2.2” of the contract. The text of the reference comes from the registry of the contract, which the translator updates when building.

## Key map

The `keys:` of a project give names to resources and fragments: `|img(key="логотип")`, `|include(key="умови.оплата")`. A build target can override a key (`keys:` of the target) — so one text is built with different logos or variants of terms.

## Order project

For a series of orders under one contract, a project is made in a subdirectory with `extends: ../../project.p.prml`: it inherits the parameters, styles, keys and documents of the base project and adds the data of the order. In Studio — “File → New → Order project”.
