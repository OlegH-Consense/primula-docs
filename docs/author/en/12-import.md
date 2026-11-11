<!-- translation: source=docs/author/ru/12-import.md sections=88ec15de 2f2b198f 8eb312c1 e782dd8a cde3252e ba95d6fa db906f77 -->
<!-- spec: 5.3 5.4 6.2 14.1 -->
# Importing documents from Word and other formats

A finished contract, manual or act lives in Word, ODT, Markdown or HTML. The command `primula import` turns it into a Primula draft: the text, the headings, the numbered clauses, the lists, the tables, the images, the notes and the links. This is the start of the work, not its end: the draft has to be read and brought to the end — but nothing has to be typed again.

A sample is `examples/16-import`: three sources (`договір.md`, `інструкція.html`, `акт.docx`) and the results of the import next to them.

## The command and the Studio window

```sh
primula import договір.docx                 # договір.prml and assets/ next to it
primula import інструкція.odt -o doc/інструкція.prml --language uk-UA
primula import договір.docx --list-styles   # only list the Word styles, write nothing
```

In Studio — "File → Import a document…" (and "Import into Primula…" in the context menu of a file): the window asks for the path of the result, the language and whether to recognize the structure, and shows the summary.

The source is read by pandoc, so it must be installed (https://pandoc.org); an old binary `.doc` is not read by pandoc — LibreOffice turns it into DOCX first. The Windows build has no pandoc: the import is unavailable there. The format is taken from the extension: `.docx`, `.odt`, `.doc`, `.rtf`, `.md`, `.html`, `.epub`, `.txt`; another reader is `--from`.

An existing result is not replaced without `--force`. After writing, the command runs `primula check` itself and prints the summary: what was converted, what was left out and the result of the check. Exit code 2 — errors remain in the draft (the file is written all the same).

## What is carried over

| In the source | In Primula |
| --- | --- |
| paragraphs, bold, italic, underline, superscript and subscript, strikeout | paragraphs, `\|*{}`, `\|/{}`, `\|_{}`, `\|^{}`, `\|,{}`, `\|—{}` |
| headings | `\|<`, `\|<<`… |
| nested lists | `\|-`, `\|#`, `\|--`, `\|#-`… (paragraphs inside an item — the environment `\|list:`) |
| tables, merged cells, alignment, widths | `\|table` with `\|&(span=…, rows=…, align=…)` |
| images | `\|img` with sizes in mm, the files go to `assets/` (EMF and WMF of Word — to SVG through LibreOffice) |
| notes, links, quotes, code | `\|footnote{}`, `\|link`, `\|.Quote:`, `\|verbatim` |
| metadata | `doc.title`, `doc.creator`; the title is also taken from the first line in capitals or from the first heading |

Not carried over, and named in the summary: the page layout (headers, footers, margins, columns), direct formatting without a style, tracked changes and comments, Word fields, formulas (their text stays), a table inside a table cell (the text is joined), raw markup.

## How the structure is recognized

In documents from Word the clause numbers are often typed by hand and the headings are just bold lines. The import restores the structure so that Primula makes the numbers and the references afterwards:

- **Typed numbers.** The paragraph "2.1. Покупець оплачує…" becomes a clause `|>`, "2.1.1." a clause `|>>`, a short line "2. Ціна і порядок розрахунків" a heading `|<`. The number is removed from the text: Primula gives the numbering. The typed numbers are compared with the numbering of the result; if they do not match (a "1.2" is missing, a "4." after a "2."), the summary says how many — the numbers of the result follow the structure.
- **Automatic numbering of Word.** A numbered list of one item — this is how Word and ODT store the numbering of headings — becomes a heading (a short text) or a clause (a long sentence); nested lists are the next levels.
- **Bold lines.** A short line entirely in bold after the first heading is a heading of the next level; the lines of the title page before the first heading ("©…", the title) stay text.
- **Table of contents.** A typed table of contents ("Title ….. 5" in a row or a list of links under "Contents") is replaced by `|toc()`.
- **Levels without skips.** The first heading is of the first level, then not deeper than "the previous one + 1"; clauses likewise.

The rules are heuristic: they err where the author of the document followed no rules. That is why the summary names what was done, `--no-structure` switches the recognition off, and `--keep-numbers` leaves the typed numbers in the text (the headings then have no Primula numbers, `number=False`).

## Word styles

A DOCX stores the names of paragraph and character styles, and the import maps them to the styles of Primula:

- the headings of Word ("Heading 2", "Заголовок 2") are headings; `Clause` and `SubClause` are clauses (this is how a DOCX made by `primula export` comes back); "Quote", "Цитата" is `|.Quote:`; ordinary styles ("Normal", "Body Text", "Hyperlink") are an ordinary paragraph; the names of Primula styles (`Body`, `Requisites`, `Strong`…) stay as they are;
- your own styles are described in `import-styles.yaml` — next to the result or in a directory above it (or `--styles FILE`):

```yaml
paragraphs:
  "Пункт": {clause: 1}          # paragraphs of the style "Пункт" are clauses |>
  "Заголовок договору": {heading: 1}
  "Реквізити": {style: Requisites}   # |.Requisites: …
  "Службовий": ignore           # the paragraph is dropped
characters:
  "Важливе": {style: Strong}    # |.Strong{…}
```

The values: `{heading: N}`, `{clause: N}`, `{style: Name}`, `plain` (an ordinary paragraph), `ignore`. A style that is not mapped stays an ordinary paragraph and is named in the summary; `--list-styles` shows all the styles of the source, `--write-styles import-styles.yaml` writes a skeleton for them. For ODT and other formats pandoc gives no style names — only the rules of the structure work there.

## The result

A typical draft is a document without parameters and references:

```prml
---
doc:
  title: "ДОГОВІР ПОСТАВКИ № 15"
  language: uk-UA
---
ДОГОВІР ПОСТАВКИ № 15

|toc()

|< Предмет договору

|> Постачальник зобов'язується поставити, а Покупець — прийняти й оплатити товар.

|< Ціна і порядок розрахунків

|> Покупець оплачує товар протягом 10 банківських днів.

|>> Зміна ціни можлива лише за згодою сторін.
```

## What to do after the import

1. Run `primula check` (the command already did) and fix the warnings; run `primula build` and look at the result.
2. Replace the references "п. 2.1" in the text with `|@("id")` with an `id=` on the clause (see the page ["Contract"](02-contract.md)): the typed numbers in references do not update themselves.
3. Move the data (parties, dates, amounts) into the parameters of the header or the project and put them in with `|(name)`.
4. Assign styles from the styles of the kit (the page ["Styles"](07-styles.md)) instead of `|.Body:` and ordinary paragraphs; signatures and requisites — a table or a style.
5. With many documents — make `import-styles.yaml` from the results of `--list-styles` and import the rest with the same file.
6. To proofread and finish the result — AI in Studio ("Ask AI…" with the recipes "proofreading", "contract terms"): the edits are applied with the check of the translator.

The limits: the import is a draft. It does not guess the meaning (which line is requisites and which is a condition), does not know the layout and does not replace proofreading.
