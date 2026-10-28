<!-- translation: source=docs/author/ru/02-contract.md sections=dc96385b c690015c e5c19ea3 372056b7 5f79c349 2ae6f229 be504271 b1618116 a2da1f66 05c5d3b3 241ce637 -->
<!-- spec: 2.3 4.2 5.2 5.3 5.5 5.6 5.7 5.10 10.4 11.9 12 13 -->
# Contract

The page shows how to make a contract: data in the header, text with numbered clauses, references to clauses instead of numbers typed by hand, sums in words, requisites of the parties and an appendix. The look is the styles set `std/styles/business`.

## The whole document

```prml
---
doc:
  title: "Договір про надання послуг"
  identifier: "П-2026/017"
  language: uk-UA
styles: [std/styles/business]
params:
  місто: "м. Харків"
  дата: 2026-10-12
  строк_днів: 5
  виконавець: {назва: "ТОВ «Виконавець»", код: "00000000", особа: "директора Петренка Петра Петровича", підписант: "П. П. Петренко"}
  замовник: {назва: "ТОВ «Замовник»", код: "11111111", особа: "директора Іваненка Івана Івановича", підписант: "І. І. Іваненко"}
---
|code:
послуги = [
    record(назва="Налаштування обладнання", кількість=dec("2"), ціна=dec("1500.00")),
    record(назва="Навчання персоналу", кількість=dec("1"), ціна=dec("2400.00")),
]
сума = sum([п.кількість * п.ціна for п in послуги])
|end
|.DocumentTitle: ДОГОВІР № |(doc.identifier)
|.DocumentSubtitle: про надання послуг
|.DatePlace: |(місто), |(fmt_date(дата, "contract"))

|.Preamble: |(виконавець.назва) (далі — |.DefinedTerm{Виконавець}) в особі |(виконавець.особа) та |(замовник.назва) (далі — |.DefinedTerm{Замовник}) в особі |(замовник.особа) уклали цей договір про таке.

|<(id="предмет") Предмет договору
|>(id="послуги") Виконавець надає послуги, перелічені в |@("специфікація", "label"), а Замовник приймає й оплачує їх.

|<(id="ціна") Ціна і розрахунки
|> Ціна послуг становить |(money_full(сума, "UAH")).
|>(id="оплата") Замовник оплачує послуги протягом |(строк_днів) |(plural(строк_днів, "банківського дня", "банківських днів", "банківських днів"))|footnote{Банківський день — день, у який банки України здійснюють розрахунки.} з дати підписання акта.

|<(id="відповідальність") Відповідальність сторін
|> За прострочення оплати (|@("оплата", "label")) Замовник сплачує пеню в розмірі подвійної облікової ставки НБУ.

|<(number=False) Реквізити і підписи сторін
|table(style="TableParties", header=1):
|: Виконавець |& Замовник
|: |(виконавець.назва) |& |(замовник.назва)
|: Код ЄДРПОУ |(виконавець.код) |& Код ЄДРПОУ |(замовник.код)
|: ______________ |(виконавець.підписант) |& ______________ |(замовник.підписант)
|end table

|appendix(id="специфікація", title="Специфікація послуг", subtitle=f"до Договору № {doc.identifier}"):
|table(style="TableServices", header=1, footer=1, cols=["52%", col("12%", id="к", type="decimal", align="right"), col("18%", id="ц", type="money", align="right"), col("18%", id="с", type="money", currency="UAH", align="right")]):
|: Послуга |& Кількість |& Ціна, грн |& Сума, грн
|for(п in послуги):
|: |(п.назва) |& |(п.кількість) |& |(п.ціна) |& |=(this_row("к") * this_row("ц"))
|endfor
|:|&(span=3, align="right") Разом |& |=(sum(column("с", rows=body_rows())))
|end table
|end appendix
```

Below — part by part.

## Data go into the header, not into the text

Everything that changes from contract to contract goes into `params:` of the header: the parties, the city, the date, the terms. The text shows the values with an expression `|(…)`: `|(місто)`, `|(виконавець.назва)`. A nested record (`виконавець: {назва: …, код: …}`) is read with a dot.

So the text needs no editing when a party changes, and Studio shows the parameters as a separate form. With many contracts, the shared data move into a project (page [“Project”](06-project.md)).

Do not put real codes, IBANs and signatures into a template — while the data are missing, use a placeholder `|?{…}`: the check reminds of it, and `--strict` does not let a release build.

## Beginning of the contract

The title, subtitle, place and date, preamble are paragraphs with styles of the `business` set: `|.DocumentTitle: …`, `|.DatePlace: …`, `|.Preamble: …`. A style written at the start of a line as `|.Name:` applies to the whole paragraph of that line; `|.Name{…}` — to a fragment inside a line (here `|.DefinedTerm{Виконавець}` marks a defined term).

The contract date — the function `fmt_date(дата, "contract")`: «12» жовтня 2026 р. Other date formats, and also `fmt_date(дата, "long")` and `"short"`, are in the appendix [“Functions of expressions”](generated/functions.md).

## Sections and clauses

`|<` is a section, `|>` — a clause, `|>>` — a subclause. The translator sets the numbers, so a new clause inserted in the middle needs no manual renumbering.

## References to clauses

Never type the number of a clause. The clause or section referred to gets an `id=`, and the text has a reference:

| Form | Text in the document |
| --- | --- |
| `\|@("оплата")` | 2.2 |
| `\|@("оплата", "label")` | п. 2.2 |
| `\|@("ціна", "label")` | розд. 2 |
| `\|@("специфікація", "label")` | дод. 1 |
| `\|@("ціна", "title")` | Ціна і розрахунки |

A reference may come before its target. If a clause is removed or its `id=` changed, the check reports an unknown target — a document never has dangling references. A label in a grammatical case — `|@("ціна", "label", case="loc")` → «розділі 2».

## Sums and numbers

Money in Primula is a decimal number: write `dec("1500.00")` or a header parameter, not a binary float. Output it with library functions:

```prml
|code:
сума = dec("5400.00")
|end
|(money(сума, "UAH")) — |(money_full(сума, "UAH")).
ПДВ 20 %: |(money(vat(сума, 20), "UAH")), разом з ПДВ |(money(with_vat(сума, 20), "UAH")).
Строк — |(words(5)) |(plural(5, "день", "дні", "днів")).
```

`money` gives “5 400,00 грн”, `money_full` — the sum in figures and in words, `words` — a number in words, `plural` — the word form for a number. A number or date written out without a formatting function gives a warning, so “5400.0” does not get into a contract.

## Requisites and signatures

The requisites of the parties are a table without lines, `TableParties` (two columns of 50 %): the first row — the names of the parties, then a row per requisite. The signature row is in the same table, so the signatures of the parties stand on one level.

## Appendix

`|appendix(…):` … `|end appendix` starts an appendix on a new page, writes “Додаток 1”, the subtitle and the title, and opens its own numbering of sections, figures and tables. The reference `|@("специфікація", "label")` gives “дод. 1”. The table with a total in the appendix is explained on the page [“Act and tables with totals”](03-tables.md).

## Footnotes

`|footnote{text}` puts a footnote at the bottom of the page; Writer counts the number.

## Repeated blocks

If a block of requisites or a signature repeats in many contracts, it becomes a macro in a module (`|def`, page [“Project”](06-project.md)) or a fragment (`|include`). An example from the kit — `examples/02-contract` (the module `lib/business.m.prml` with macros for requisites and signatures).
