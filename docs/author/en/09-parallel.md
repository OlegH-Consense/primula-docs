<!-- translation: source=docs/author/ru/09-parallel.md sections=0d6476ab ca9ff07c 85956d13 34198e13 930e5d30 2cb449c7 a4d1e26e cc96e807 744c808e -->
<!-- spec: 5.5 5.6 5.7 5.9 5.10 7.7 11.5 14.1 -->
# Parallel texts

The environment `|parallel` puts two or more texts — tracks — side by side and aligns horizontally the starts of their blocks of meaning — segments. This is how a bilingual agreement, a protocol of disagreements ("old / new") or a text with a comment in the margin are written. Columns of a section (`|section(cols=2)`) do not fit: they flow independently. A table looks right, but it has no notion of "a clause and its translation": numbering, references and language are common to the whole table.

The translator writes `|parallel` as a table without borders, but it knows the tracks: every track is numbered with its own counters, evaluated in its own language and compared with the primary track.

## Example

```prml
---
doc: {title: "Договір / Agreement", identifier: "ДП-2026/017", language: uk-UA}
params:
  ціна: 48000.00
  виконавець: {uk: "ТОВ «Виконавець»", en: "Vykonavets LLC"}
styles: [std/styles/business]
---
|parallel(tracks=[track("uk", lang="uk", title="Українською мовою"), track("en", lang="en", title="In English")],
          gap="8mm", rule="0.3pt solid #999999", parity="translation"):

|segment(span="all"):
|.DocumentTitle: ДОГОВІР № |(doc.identifier) / AGREEMENT No. |(doc.identifier)
|end segment

|segment(id="subject"):
|track("uk"):
|<(id="subject") Предмет договору
|>(id="services") |(getattr(виконавець, track.id)) надає послуги з розроблення документації.
|> Ціна послуг — |(money_full(ціна, "UAH")) (див. |@("services", "label")).
|track("en"):
|<(id="subject") Subject of the Agreement
|>(id="services") |(getattr(виконавець, track.id)) provides the services of developing documentation.
|> The price of the services is |(money_full(ціна, "UAH")) (see |@("services", "label")).
|end segment

|end parallel
```

In the Ukrainian column the sum reads «сорок вісім тисяч гривень 00 копійок» and the reference «п. 1.1»; in the English one — "forty-eight thousand hryvnias 00 kopiykas" and "cl. 1.1". Clauses are numbered alike in both columns.

## Tracks

A track is described by the function `track(id, …)` in the argument `tracks=`:

| Argument | What it sets |
| --- | --- |
| `lang` | language of the track: sums in words, dates, quotes, labels of references, spell checking in Writer |
| `title` | title above the column; the row of titles is repeated on every page |
| `width` | width of the column, as for a table column: `"30%"`, `"60mm"`, `"*"` |
| `primary=True` | the primary track (the first by default): the numbering of the document, the table of contents and the navigation follow it, the other tracks are compared with it |
| `numbered=False` | a track without numbering: comments, notes in the margin |
| `optional=True` | the track may have no block in a segment — the cell stays empty |
| `block` | a block style for all cells of the track (background, padding) |

When only languages are needed, the short form `langs=["uk", "en"]` is enough. The gap between the columns is `gap=`, the line — `rule=`.

Parameters of the document are common to all tracks. A value in the language of the track is chosen by code: a track block has the record `track` (`track.id`, `track.lang`), so `|(getattr(виконавець, track.id))` takes the field `uk` or `en`.

## Segments

A segment is a row of alignment: the block of every track starts at the same level, the end follows the longest block. A segment is usually a section of an agreement or a clause.

- **Environment:** `|segment(id="…"):`, then the track blocks `|track("uk"):`, `|track("en"):` and `|end segment`. A track block ends at the next `|track` or at the closing of the segment.
- **Line** — for short blocks:

```prml
|parallel(langs=["uk", "en"]):
|segment(id="city") |track("uk"){м. Харків} |track("en"){Kharkiv}
|end parallel
```

- **Full width** — text common to all tracks (the title of the agreement, the table of signatures): `|segment(span="all"):` without track blocks.

Inside a track block you write ordinary text: headings, clauses, lists, tables, figures, footnotes. Not allowed: a change of page, sections with columns, appendices, headers and footers, a table of contents, a nested `|parallel` (message P5304). Between segments `|newpage` and `|page(…)` are allowed: the table goes on on a new page with the row of titles.

A heading left last on a page is not moved by Writer to the next segment. Write a heading in the same segment as the first clause of its section.

## Numbering, references, footnotes

- Every track has its own counters: on entering `|parallel` they are copied from the document; after the environment the document goes on with the numbering of the primary track.
- An ID inside a track gets the name of the track: `id="services"` in the Ukrainian block is `uk.services`, in the English one — `en.services`. So equal `id=` in both tracks do not conflict.
- `|@("services")` inside a track looks for the target in its own track, then in the primary one, then in the whole document. A target of another track is written in full: `|@("uk.services")`.
- A footnote of a non-primary track gets the number of its track: the numbers are the same in both columns.
- Headings of non-primary tracks look like headings, but they are not in the Writer navigator and the PDF bookmarks — only the primary track is there.

The table of contents of the document takes the headings of the primary track. The table of contents of another track is `|toc(track="en")`; its default title is in the language of the track ("CONTENTS"):

```prml
|toc(title="ЗМІСТ")
|toc(track="en")
|parallel(langs=["uk", "en"]):
|segment:
|track("uk"):
|< Предмет договору
|track("en"):
|< Subject of the Agreement
|end segment
|end parallel
```

## Correspondence check

The argument `parity=` compares every numbered track with the primary one in every segment:

| Profile | What is checked |
| --- | --- |
| `structure` (default) | whether every required track has a block; the sequence of headings, clauses, list items, tables, figures, admonitions |
| `translation` | the same, and also IDs, targets of references, names of parameters in `\|(…)`, numbers and addresses in the text, the counters of the tracks at the end |
| `none` | nothing |

A segment may set its own profile: `|segment(id="idiom", parity="none")` — for a free translation. Differences are warnings P5310–P5315; with `--strict` they become errors.

```prml error=P5311
|parallel(langs=["uk", "en"], parity="translation"):
|segment(id="term") |track("uk"){Строк — 5 днів.} |track("en"){The term is 7 days.}
|end parallel
```

## Translation: blanks, confirmation, freshness

When a document is being translated, it helps to keep the state of every block:

1. **Blanks.** `primula parallel договір.prml --stub --track en` writes into the segments without an English block a copy of the structure of the primary block with placeholders `|?{…}`. Placeholders are warnings, with `--strict` errors, so an unfilled translation does not get into a release.
2. **Confirmation.** A checked translation is recorded: `primula parallel договір.prml --stamp --track en --status reviewed` writes `status="reviewed"` and `rev="…/…"` into the blocks — the hashes of the text of the primary block and of the translation itself. `--segment ID` confirms only the named segments.
3. **A changed original.** If the Ukrainian text is changed after the confirmation, `check` gives P5320 "the translation is outdated"; if the translation itself is changed — P5321. The warning stays until the translation is fixed and confirmed again.
4. **Before a release.** `primula parallel договір.prml --check-status reviewed` ends with an error if some block is not in this state or is outdated.

In Studio the same actions are in the menu "Build → Parallel tracks" and in the context menu of the editor ("Confirm the translation of segment …" for the block under the cursor). The Structure panel shows segments and track blocks with their status and marks the outdated ones.

The hash is computed over the text of the block without comments and extra spaces, so reformatting does not make a translation outdated. Expressions `|(…)` enter the hash as written: a changed value of a parameter does not outdate a translation — the values are common to the tracks.

## Protocol of disagreements

Three tracks: the wording of the supplier (optional — a new clause is not in it), the wording of the buyer (the primary track) and a comment of a lawyer (not numbered, a narrow column). The numbers of the clauses of the contract are written explicitly:

```prml
|parallel(tracks=[track("old", title="Редакція Постачальника", optional=True),
                  track("new", title="Редакція Покупця", primary=True),
                  track("note", title="Коментар", width="30%", numbered=False, optional=True)]):
|segment(id="p-4-2"):
|track("old"):
|*{4.2.} Оплата здійснюється протягом 5 банківських днів.
|track("new"):
|*{4.2.} Оплата здійснюється протягом 30 календарних днів.
|track("note"):
|.SmallPrint: Відстрочку погоджено листом від 12.10.2026.
|end segment
|segment(id="p-4-3"):
|track("new"):
|*{4.3.} Покупець має право на дострокову оплату.
|end segment
|end parallel
```

Complete examples: `examples/09-parallel/agreement.prml` (a bilingual agreement with confirmed translations) and `protocol.prml`.

## Styles

The output table has the style `ParallelTable` (no borders), the row of track titles — `ParallelHeader`; both are in every styles set of the kit (appendix [styles of the kit](generated/styles.md)). Own names are set in a styles module: `structure_styles(parallel_table="…", parallel_header="…")` or by the argument `style=` of `|parallel`.
