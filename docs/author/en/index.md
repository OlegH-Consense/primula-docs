<!-- translation: source=docs/author/ru/index.md sections=2e58fbdc ed5fa76d a9526cee 00bf2b23 -->
<!-- spec: 1 2 14 -->
# Primula author guide

A guide for those who write documents in Primula: contracts, acts, letters, instructions and reports. It explains how to solve a typical task and does not repeat the reference tables. The complete lists of constructs, functions, header keys, messages and styles are in the appendices, which are generated from the translator and always match its version.

The normative documents are the specification `primula-spec-v1.1-draft.ru.md` and the description of the standard library `primula-stdlib-v1.1-draft.ru.md`; their English translations are `primula-spec-v1.1-draft.en.md` and `primula-stdlib-v1.1-draft.en.md`. A comment at the top of every page of the guide names the specification sections it relies on.

## Pages

| Page | About |
| --- | --- |
| [First document](01-start.md) | a `.prml` file, the YAML header, paragraphs, headings, clauses, check and build |
| [Contract](02-contract.md) | parameters, place and date, preamble, sections and clauses, references to clauses, sums in words, requisites, appendix |
| [Act and tables with totals](03-tables.md) | tables, typed columns, formulas and totals, rows from data |
| [Official letter](04-letter.md) | the `letter` styles set: letterhead, addressee, number and date, signature |
| [Technical documentation](05-technical.md) | admonitions, conditional variants, abbreviations, index, figures |
| [Project of several documents](06-project.md) | `project.p.prml`, shared parameters, fragments, modules, build targets, orders |
| [Styles](07-styles.md) | styles sets of the kit, your own styles module, applying styles, moving from Kit |
| [Messages of the translator](08-messages.md) | how to read messages, common errors and what to do |
| [Parallel texts](09-parallel.md) | bilingual agreement, protocol of disagreements: tracks and segments, language and numbering of a track, correspondence check, confirmation of a translation |
| [Code: the Python dialect](10-code.md) | `decimal` numbers, strings, collections, records, dates, functions, lazy immutable global names, modules and export from a fragment (`@export`), values in the text, what the core does not have |
| [Libraries: development and use](11-libraries.md) | a library of modules and data, what it can and cannot use, the directory layout, test documents with `fail()`, linking by a symbolic link, a copy or a Git submodule (decision 136), data with a date of effect, release |
| [Importing documents](12-import.md) | `primula import`: DOCX, ODT, DOC, Markdown, HTML → a Primula draft; recognition of the structure, Word styles, `import-styles.yaml`, what to do after the import |

Appendices (generated, not edited by hand): [constructs](generated/constructs.md), [functions of expressions](generated/functions.md), [header keys](generated/header-keys.md), [messages](generated/diagnostics.md), [styles of the kit](generated/styles.md). Terms follow the [glossary](../glossary.md).

## What you need

- The translator `primula` — from the package or from the source tree (`./primula`). PDF needs LibreOffice.
- An editor: Primula Studio (highlighting, hints, check, PDF preview) or any text editor with UTF-8.

Studio is described in its own help (F1 in Studio); the guide shows the translator commands that Studio runs for you.

## How a document is made

A document is a plain text file. Text is written as it is, and everything that belongs to markup starts with a vertical bar `|`: `|<` — a heading, `|>` — a clause of a contract, `|(сума)` — a value from code, `|*{важливо}` — emphasis. The translator checks the file, computes the values, numbers the clauses and references and writes an ODT document (and a PDF through LibreOffice). The look is set by styles, not in the text: the same document prints differently when another styles set is used.
