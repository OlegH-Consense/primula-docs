# Primula syntax overview (v1.1-draft)

A compact map of the language. Arguments, defaults and function signatures are in the
translator's own reference: `primula commands --format json --lang en` (or `--functions`,
`--header` for text). The normative text is the specification (Russian), sections in `[§ …]`.

## Files and header [§ 2]

- document — `.prml`, built into ODT; after the header: markup
- fragment — `.f.prml`, used by `|include`; markup
- module — `.m.prml`, used by `|import`; definitions only
- styles — `.s.prml`, listed in `styles:` of a project or document; code
- project — `.p.prml`, the file `project.p.prml`; code

```
---
doc: {title: "Договір", language: uk-UA}
params: {vat: true, days: 10}       # |(vat), |(days)
styles: [std/styles/default, styles/contract.s.prml]
references: [contract]              # other documents of the project for |@
---
```

Document keys: `kind primula doc params structure styles references`; `doc:` has `title
subject description creator organization language identifier revision status created
modified keywords`, visible as `doc.title` in code. Project keys add `name language
doc_defaults ref_documents keys targets extends on_conflict build_date limits`.

## After `|` [§ 3]

- `|` → a literal bar: `||`
- `(` → an expression `|(…)`, its value as text
- a letter → a long command `|name`; `|module.name` for a module macro
- punctuation → a short form (below)
- a space, the end of the line, a digit → error

Long form: `|name(args){body}` inline · `|name(args): text` line form (first on the
line) · `|name(args):` … `|end name` environment. No spaces between name, `(` and `{`.
Arguments are core expressions and may span lines. `|;` ends a command name before a
letter: `|seller|;ом`. Single braces in text: `|{` `|}`.

Closing: `|end` — nearest environment (not if/for/def); `|end>` `|end.Name` `|end!` with a
check; `|end name` for any named environment; `|endif` `|endfor` `|enddef`.

## Short forms [§ 3.3, 4, 5]

- `|% text` — comment to the end of the line
- `|\` `|~` — line break · non-breaking space
- `|*{…}` `|/{…}` `|_{…}` — bold · italic · underline (= `|.Strong` `|.Emphasis` `|.Underline`)
- `|^{…}` `|,{…}` `|—{…}` — superscript · subscript · strikethrough (em dash U+2014)
- ``|`{…}`` `|"{…}` `|?{…}` — code · quotes of the document language · draft placeholder
- `|.Name{…}` — character style; `|.(expr){…}` — a computed name
- `|.Name: …` — paragraph style for the line, or an environment closed by `|end.Name`
- `|@("id")`, `|@("id", "label")` (also `"title"`, `"page"`) — cross reference; `case="loc"` etc. for Ukrainian cases
- `|<` … `|<<<<<<` — heading of level 1–6; `|<(number=False)`, `id=`, `toc=`
- `|>` `|>>` … — numbered clause of level n; `|>(id=…)`, `|>(continues="id")`; `|>: … |end>` for several paragraphs
- `|-` `|#` `|--` `|#-` — list items: the length is the level, the last sign the type (`-` bullet, `#` number)
- `|!("note")` — admonition: `danger warning caution notice note tip`; `hazard=` for danger and warning
- `|:` `|&` `|=(expr)` — table row · cell · cell formula

Structural forms (`|< |> |- |# |! |:`) only at the start of a line. A clause's implicit
scope ends at the next paragraph, the next clause of the same or higher level, a heading,
`|page`, `|appendix`, `|toc` and similar; lists, tables, admonitions, figures stay inside.

## Text

Blank line — new paragraph; a line break inside a paragraph is a space. `|(…)` cannot
print `None`, booleans, lists or records; markup from a string only through `markup(…)`.
Fractional numbers and dates go through `num`, `money`, `fmt_date` (else a warning).

## Control, macros, variables [§ 9, 10, 12]

```
|if(vat){з ПДВ}|elif(free){безоплатно}|else{без ПДВ}
|for(x in items){|(x.name); }
|if(cond):
…
|elif(other):
…
|else:
…
|endif
|for(i, it in enumerate(items, 1)):
…
|endfor
|def sign(name, role="директор"):
|(role) ______________ |(name)
|enddef
|sign("П. П. Петренко")
|let(rate=20)
|>(when=has("wifi")) A clause only for products with the feature wifi.
```

`|export(months=12)` — only in a fragment (`.f.prml`): the name becomes visible to the
including document. A function of the fragment's `|code:` is exported with the decorator
`@export` (or `@export(name="other")`) above a top-level `def`; names already defined (a
`|def` macro) with `|export("sign")` (decision 135). A module (`.m.prml`) needs no export:
every name without a leading `_` is public as `module.name`, or without the prefix after
`|import("lib/x", "name")`; an `|import` of the document also works in its fragments. `|let` and `|code:` inside a top-level `|if` are errors. `when=` works on any block command
and on a table row.

## Code [§ 12]

```
|code:
items = load_csv("data/items.csv", types={"qty": "decimal", "price": "money"})
total = sum([it.qty * it.price for it in items])
|end
```

A Python subset: `def while for if`, comprehensions, f-strings, `*args **kw`; no `class
import from try except raise with global del lambda yield async await := match`. Integers
are `decimal`; `2.20` prints as «2,20»; `1.5e3` is a float; `round` rounds half away from
zero. Lengths `10*mm`, `"10mm"`; dates `date(2026, 10, 12)`, `d + 5` adds days. Top-level
definitions are lazy and immutable. Limits per build: time 20 s, recursion 500, size 10⁷.
Built-ins: `len range enumerate zip sorted reversed min max sum any all abs round int float
dec str bool list tuple dict record date datetime type getattr hasattr repr fail debug
markup build_date`. In `.s.prml` and `.p.prml` the whole body is code (comments `#`).

## Tables [§ 6]

```
|table(id="t", caption="Перелік", cols=["10mm", "*", col("25mm", id="sum", type="money", currency="UAH", align="right")], header=1, footer=1):
|: № |& Найменування |& Сума
|: 1 |& Товар |& |(price)
|:|&(span=2, align="right") Разом |& |=(sum(column("sum", rows=body_rows())))
|end table
```

Columns: `"40mm"`, `"30%"`, `"*"`/`"2*"` (rest by weight), `"auto"`, `"20mm..60mm"`,
`col(width, id=, align=, type="decimal|money|datetime", currency=, digits=)`. Table:
`style width align header footer repeat_header frame rules caption id block when live`,
`data= fields= titles=` for a table from records. Cells: `span= rows= align valign padding
background border*`; rows: `height min_height keep when`. Cells per row = columns (with
spans); empty cell `|&`. Full form: `|row:` `|cell:` … `|end cell` `|end row`. Formulas:
`this_row(c)`, `cell(r, c)`, `column(c, rows=…)`, `body_rows()`, `sum min max avg count`.

## Structure, references, includes [§ 5, 9, 10]

`|toc(max_level=3, title="ЗМІСТ")`, `|list_of("figure"|"table"|"abbr"|"index")`,
`|footnote{…}`, `|endnote{…}`, `|abbr("ПЗ", "розшифровка")`, `|index("термін")`.
`|appendix(id=, title=, subtitle=):` … `|end appendix` — new page, «Додаток 1», own
numbering. `|scope("name", prefix="А"):` … `|end scope`.
`|include("part.f.prml", part=, ns=, rename={}, level_shift=n)`, `|include(key="k")`,
`|import("lib/business")` → `|business.sign(…)`, `|import("std/math")` → `math.sqrt(…)`,
`|document("c.prml", params={})` — a part of a combined ODT. Paths are relative to the
file, not above the project root; `.prml` may be omitted. A symbolic link inside the
project (`lib -> ../shared`) may lead to a shared library (warning P2639).

## Pages and graphics [§ 7, 8]

`|page("Landscape")`, `|page("Landscape"): … |end page`, `|newpage`, `|newcolumn`,
`|section(cols=2):` … `|end section`, `|header("Portrait"):` … `|end header`,
`|footer(…)`, fields `|field.page |field.pages |field.chapter |field.title`.
`|img("logo.png", height="8mm")`, `|img(key="logo")`, `|img(svg=text)`,
`|figure("scheme.svg", width="120mm", id="fig"):` caption `|end figure`,
`|frame(rel="page", x=, y=, width=):` … `|end frame`, `|watermark("ПРОЄКТ")`.
Placement: `place valign x y rel anchor wrap layer gap width height style alt`.

## Parallel tracks [§ 7.7]

Texts side by side with aligned starts (bilingual contract, protocol of disagreements):
`|parallel(langs=["uk", "en"]):` or `tracks=[track("uk", lang="uk", title=…), track("note",
numbered=False, optional=True, width="30%")]`, then segments: `|segment(id="s"):` with track
blocks `|track("uk"):` … `|track("en"):` … `|end segment`, the line form
`|segment(id="c") |track("uk"){…} |track("en"){…}`, the full width `|segment(span="all"):`;
`|end parallel`. Each track is numbered and evaluated in its own language; IDs become `uk.id`;
`|toc(track="en")`. `parity="structure"|"translation"|"none"` compares the tracks (P5310–P5315).
`rev=`/`status=` of a track block are written by `primula parallel FILE --stamp --track en` —
never edit `rev` by hand; P5320/P5321 mean the original/translation changed after confirmation.

## Styles modules [§ 11]

YAML groups `paragraphs characters blocks tables lists frames pages` or functions
`paragraph_style character_style … page_style(name, parent=…, …)`. Settings:
`structure_profile("business"|"report")`, `structure_styles(…)`, `numbering`, `captions`,
`appendices`, `quotes`, `typography(…)`, `placeholders("mark"|"final")`. Layers: project →
`--style` → `styles:` of the document → code of the document.

## Standard library (prelude) [library]

Numbers `num percent round_to round_money`; money `money money_words money_full vat
with_vat vat_in without_vat split`; words `words ordinal date_words`; dates `add_months
add_years fmt_date(d, "short|long|contract") fmt_time weekday month_name workdays
is_workday`; units `qty qty_range convert`; text `plural join_list cap translit nbsp_short`;
data `group_by sum_by distinct load_csv load_yaml load_json load_ods load_xlsx load_text` (sheets: `sheet=`, `range="A1:D20"`, `header=`, saved results of formulas; `load_text` — the whole file as a string, e.g. SVG for `svg=`); `std/math` by import.
Language: `lang="uk|ru|en"`, by default the document language. A float in a money function
is an error; the VAT rate is always given explicitly.
