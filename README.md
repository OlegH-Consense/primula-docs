# Primula Documenting System

[Українською](README.uk.md)

Primula is a plain-text markup language for business and technical documents — contracts, acts, invoices, letters, manuals — and a translator that builds an editable **ODT** for LibreOffice Writer from it, and a **PDF** through LibreOffice. **Primula Studio** is a desktop workplace for writing, checking and building Primula documents.

```prml
---
doc: {title: "Договір поставки", language: uk-UA}
params: {сума: 30444.96}
---
|<(number=False) Договір поставки
|< Ціна
|>(id="pay") Покупець оплачує |(money_full(сума, "UAH")) протягом 10 банківських днів.
|> Строк оплати — див. п. |@("pay").
```

**Status: 0.3.0, a pre-release (the second public one; see [CHANGELOG.md](CHANGELOG.md)).** The language (specification 1.1, draft), the translator and Studio are usable for real documents, but they still change; files written today may need small edits later.

## What it does

- **Structure of business documents:** numbered sections, clauses and subclauses, lists, appendices, tables of contents, cross references (`|@("id")` → «п. 2.1», «табл. 1.1»), footnotes; numbering by Ukrainian standards (ДСТУ 3008, ДСТУ 4163) is the default.
- **Computed values:** a small, safe subset of Python with decimal arithmetic — sums, VAT, amounts in words, dates and workdays, plurals; data from CSV, YAML, JSON, ODS and XLSX files; conditions and variants of one document.
- **Styles kept apart:** styles modules (`.s.prml`) instead of formatting in the text; built-in sets for business documents, letters, technical manuals and reports.
- **Projects:** shared fragments and modules, parameters, a project file with build targets (a contract and its orders), combined documents, parallel bilingual texts.
- **Highlighting for editors:** Kate/KWrite/KDevelop, Midnight Commander (mcedit), Geany and VS Code (`editors/`, built from the reference of the translator).
- **Libraries of modules:** twelve reusable `.m.prml` libraries outside the translator (`libraries/`): requisites (ЄДРПОУ, РНОКПП, IBAN UA), names in cases, rates and law data with a date of effect, penalty and terms, financial schedules, payment QR codes (NBU, SEPA), bar codes, charts, statistics, electronics, change tables from Git.
- **Export:** Markdown, HTML, DOCX and other formats through [pandoc](https://pandoc.org) (`primula export`).
- **Primula Studio** (Qt 6): highlighting, hints, completion and context help, the Structure, Styles and Palette panels, check and build, a PDF view, an evaluator console, AI assistance through Codex CLI or Claude CLI.
- **Messages** like compilers give them (`file:line:column: error[P2201]: …`) in English, Ukrainian and Russian.

## Getting started

### From a release package (Linux)

Release packages are built for one distribution each (for example openSUSE Tumbleweed, Debian 12 or 13); take the one for your system from [Releases](https://github.com/OlegH-Consense/primula-docs/releases).

```sh
tar xf primula-docs-0.3.0-<distribution>-x86_64.tar.gz
cd primula-docs-0.3.0-<distribution>-x86_64
./check-dependencies.sh --install     # Python 3.11+, PyYAML, Qt 6, LibreOffice
./install.sh                          # into ~/.local; the examples go to ~/Primula/examples
primula-studio                        # or from the menu: Primula Studio
```

### From the source tree

The translator needs Python 3.11+ and PyYAML; LibreOffice is needed for PDF only.

```sh
./primula build examples/02-contract/contract.prml --pdf
./primula check examples/02-contract/contract.prml --lang en
./primula --help
```

Primula Studio needs Qt 6.4+ (Core, Gui, Widgets, Pdf, PdfWidgets, LinguistTools), CMake 3.20+, Ninja and a C++20 compiler:

```sh
studio/build-studio.sh                # build into studio/build
studio/install-local.sh               # or install into ~/.local
studio/make-distribution.sh --archive # a release package for this distribution
```

## Documentation

| | |
| --- | --- |
| [Author guide](docs/author/en/index.md) ([uk](docs/author/uk/index.md), [ru](docs/author/ru/index.md)); as one PDF: [en](docs/author/en/primula-author-guide-en.pdf), [uk](docs/author/uk/primula-author-guide-uk.pdf), [ru](docs/author/ru/primula-author-guide-ru.pdf) | the language with examples, from the first document to projects, styles, libraries and the Python dialect of the core |
| [Examples](examples/README.md) | twelve documents and projects: contract, manual, loan with a schedule, styles sets, parallel texts, libraries, an invoice with a payment QR code |
| [Specification](primula-spec-v1.1-draft.en.md) ([uk](primula-spec-v1.1-draft.uk.md), [ru](primula-spec-v1.1-draft.ru.md)), [standard library](primula-stdlib-v1.1-draft.en.md) ([uk](primula-stdlib-v1.1-draft.uk.md), [ru](primula-stdlib-v1.1-draft.ru.md)) | normative texts; the Russian originals are normative, the translations are kept in step with them section by section |
| [Primula Studio](studio/README.md), [user guide](studio/help/studio-user-guide.en.md), [cheat sheet](studio/help/primula-cheatsheet.en.pdf) | the desktop application |
| [Skills for AI agents](skills/README.md) | instructions for Claude Code, Codex and other agents: writing documents and libraries |
| [Developer notes](docs/dev/architecture.md) | architecture of the translator, [diagnostics](docs/dev/diagnostics.md), [export through pandoc](docs/dev/pandoc.md) |

## Plans

Development goes on in iterations; the next directions are:

- more libraries of modules and the check of their legal and data sources (the libraries are 0.1.0); schemas for data files;
- conversion into Primula from other formats (DOCX, ODT, Markdown) and export from Studio;
- a language server and a formatter for editors (highlighting is there: `editors/`);
- AI assistance in Studio built on the checks of the translator;
- Primula Studio and the translator for Windows.

Plans change with the experience of real documents; issues and suggestions are welcome.

## Licences

The code (translator, Studio, libraries) is under the [Apache License 2.0](LICENSE), the documentation under [CC BY 4.0](LICENSES/CC-BY-4.0.txt), the examples and templates under [CC0 1.0](LICENSES/CC0-1.0.txt) — copy them into your documents freely. The details are in [LICENSING.md](LICENSING.md). Contributions: [CONTRIBUTING.md](CONTRIBUTING.md).
