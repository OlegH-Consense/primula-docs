<!-- translation: source=docs/author/ru/07-styles.md sections=f68fb6c9 4304a4cd e72274d0 9146bf14 32d48d11 2fab85ba c0a8fac8 -->
<!-- spec: 3.3 4.3 4.4 4.5 11.1 11.2 11.3 11.4 11.5 11.7 11.9 -->
# Styles

The look of a document is set by styles, not by the text: font, indents, spacing, table frames, page margins. The text says only *what* something is — a heading, a clause, requisites — and the styles module decides *how* it looks. So the same document can be printed differently by naming another set, and changing the look does not touch the text.

## Choosing a set

The kit of the translator has styles sets for typical documents:

| Set | For | Base |
| --- | --- | --- |
| `std/styles/default` | applies by itself when no styles are named | — |
| `std/styles/business` | contracts, acts, invoices, protocols; DSTU 4163:2020 | `default` |
| `std/styles/letter` | official letters; DSTU 4163:2020 | `business` |
| `std/styles/technical` | manuals, instructions, technical descriptions | `default` |
| `std/styles/report` | reports in science and technology; DSTU 3008:2015 | `default` |
| `std/styles/compact` | memos, quick references, cheat sheets | `default` |

A document names a set with one header line:

```prml
---
doc: {title: "Акт", language: uk-UA}
styles: [std/styles/business]
---
|.DocumentTitle: АКТ № 14
```

The base (`default`) need not be listed: the set names it itself. The styles of every set, their properties and the default font are in the appendix [“Styles of the kit”](generated/styles.md); samples — the documents `examples/08-styles` (build them and look at the PDF).

## Applying styles in the text

| Form | What it does |
| --- | --- |
| `\|.DatePlace: м. Харків` | a paragraph style for the paragraph of this line |
| `\|.Note:` … `\|end.Note` | a paragraph style for several paragraphs (environment) |
| `\|.DefinedTerm{Замовник}` | a character style for a fragment inside a line |
| `\|*{…}`, `\|/{…}`, ``\|`{…}`` | bold, italic, monospace — character styles too (`Strong`, `Emphasis`, `Code`) |
| `\|table(style="TableCompact")` | a table style |
| `\|list("DashList")` | the style of the next list |

The style name in `|.Name` is an identifier: it is not translated and does not change when the text is proofread. An unknown name is an error with its position.

Headings, clauses, lists, tables and captions get their styles automatically — the binding of constructs in the styles module sets them (`Heading1`…`Heading6`, `Clause`, `BulletList`, `TableGrid`, `TableCaption` …). The command `|set` changes the style of a construct until the end of the enclosing environment:

```prml
|set(list="DashList")
|- перший пункт;
|- другий пункт.
```

Direct formatting `|fmt(bold=True){…}` exists too, but gives a warning: one-off formatting is lost when the set changes, and equal places end up formatted differently. If a format repeats, make a style.

## Your own styles module

Do not edit the sets of the kit — make your own module over a set. It holds only the differences and names its base with the key `extends`:

```prml file=styles/компанія.s.prml
---
kind: styles
extends: std/styles/business
defaults: {font: Roboto, size: 11pt}
paragraphs:
  Body:        {line_height: "120%"}
  Реквізити:   {parent: Details, keep_together: true}
characters:
  Акцент:      {bold: true, color: "#1F4E79"}
tables:
  TableServices: {header_background: "#DDE6F0"}
---
```

```prml
---
doc: {title: "Договір", language: uk-UA}
styles: [styles/компанія.s.prml]
---
Текст з |.Акцент{акцентом}.

|.Реквізити: Код ЄДРПОУ 00000000
```

- The document (or the project) names only your module: the base and its base (`business` → `default`) are loaded by themselves.
- A style property under the same name adds to the style of the set: `Body: {line_height: "120%"}` changes only the spacing, the rest stays from the set.
- A new style inherits an existing one through `parent`.
- The font of the whole document changes with one line `defaults: {font: …}`. The font must be installed where the document is opened or the PDF is built.

Style groups of a module: `paragraphs` (paragraph styles), `characters` (character styles), `tables`, `lists`, `blocks`, `frames` (size and placement of images), `pages` (pages). Properties — `font`, `size`, `bold`, `align`, `line_height`, `space_before`, `space_after`, `left`, `first_line`, `keep_with_next` and others; the full list is section 11.3 of the specification. Studio gives hints on properties and styles (mouse hover, `Ctrl+Space`).

## Layers

When styles are named in several places, they are applied in layers, from early to late:

1. modules from `styles:` of the project;
2. modules given at build time with `--style FILE`;
3. modules from `styles:` of the document;
4. styles defined by the code of the document itself.

A later layer adds to and overrides the earlier ones. The base of a module (`extends`) is the layer right before it. Which layers are actually loaded and where each style comes from is shown by the “Styles” panel of Studio or by `primula check документ.prml --dump-styles`.

## Pages, headers and footers

Margins and page size are a page style (`pages:` of the module, `Portrait` by default; the sets have `Landscape`). Headers and footers are set in the code of a styles module or in the document:

```prml
|footer("Portrait"):
|.Footer: Договір № П-2026/017 — сторінка |field.page з |field.pages
|end footer
```

A page change from this place — `|page(style="Landscape")`, a page break — `|newpage`.

## Moving from ODT Markdown Kit

The business set of Kit 1.2 (`business-styles.yaml`) is carried over to `std/styles/business` and `default` under the same names, except the ones below:

| Kit | Primula |
| --- | --- |
| `TocTitle`, `TocEntry` | `ContentsTitle`, `Contents1`…`Contents6` |
| `StrongText`, `EmphasisText`, `UnderlinedText` | `Strong`, `Emphasis`, `Underline` (short forms `\|*{}`, `\|/{}`, `\|_{}`) |
| `DraftPlaceholder` | `Placeholder` (short form `\|?{…}`) |
| `BodyRoboto`, `FontCarlito` and similar | none: the font is set by `defaults: {font: …}` of your module |
| `Recipient`, `LetterSubject`, `Salutation` | in the `letter` set |
| `Approval` | in `business`, 100 mm from the left margin (DSTU 4163:2020) |
| `NumberedList` with letters `a)` | `NumberedList` (`1.`, `1.`, `a)`), `LetterList` — letters of the document language «а)», `LatinLetterList` — «a)» |
| image presets `Logo`, `Illustration` … | frame styles with the same names: `\|img(…, style="Logo")` |

Kit wrote clause numbers and references as text; in Primula the translator sets them (`|>`, `|@("id")`), and the style `Clause` is applied to clauses by itself.
