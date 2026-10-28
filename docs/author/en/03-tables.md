<!-- translation: source=docs/author/ru/03-tables.md sections=bc520c72 cc7853f5 5045f396 7af0edfa 5448e54e be145f29 -->
<!-- spec: 5.8 6.2 6.3 6.4 6.5 6.6 6.7 6.8 6.9 10.5 -->
# Act and tables with totals

A table is an environment `|table(…):` … `|end table`. A row starts with `|:`, cells are separated by `|&`. The translator computes totals by formulas, checks the number of cells in rows and formats numbers and sums by the document language.

## A simple table

```prml
|table(cols=["40%", "*"], header=1):
|: Показник |& Значення
|: Строк поставки |& 10 робочих днів
|: Місце поставки |& склад Покупця
|end table
```

- `header=1` — one header row; it repeats on the following pages.
- `cols` — column widths: `"40mm"` — fixed, `"30%"` — a share of the table, `"*"` — the rest, `"auto"` — by content, `"20mm..60mm"` — by content within limits.
- The number of cells of every row must match the number of columns; an extra or missing cell is an error with the row number. An empty cell is `|&` without text.

## Act: rows from data and a total

Let the items of the act lie in a CSV file:

```csv file=data/позиції.csv
назва,кількість,ціна
Налаштування обладнання,2,1500.00
Навчання персоналу,1,2400.00
Виїзд спеціаліста,3,350.00
```

The table of the act with a total and VAT:

```prml
|code:
позиції = load_csv("data/позиції.csv", types={"кількість": "decimal", "ціна": "money"})
|end
|table(id="т-акт", caption="Перелік наданих послуг", header=1, footer=3, cols=["10mm", "*", col("18mm", id="к", type="decimal", align="right"), col("26mm", id="ц", type="money", align="right"), col("30mm", id="с", type="money", currency="UAH", align="right")]):
|: № |& Послуга |& К-сть |& Ціна |& Сума
|for(н, п in enumerate(позиції, 1)):
|: |(н) |& |(п.назва) |& |(п.кількість) |& |(п.ціна) |& |=(this_row("к") * this_row("ц"))
|endfor
|:|&(span=4, align="right") Разом без ПДВ |& |=(sum(column("с", rows=body_rows())))
|:|&(span=4, align="right") ПДВ 20 % |& |=(round(cell(len(позиції) + 2, "с") * dec("0.20"), 2))
|:|&(span=4, align="right") |*{Усього} |& |=(cell(len(позиції) + 2, "с") + cell(len(позиції) + 3, "с"))
|end table
Див. |@("т-акт", "label").
```

What happens here:

- `load_csv` reads the file; `types=` declares the column types, otherwise everything is read as strings. The path is relative to the document and does not leave the project root. `load_yaml` and `load_json` work the same way.
- `col(width, id=…, type=…, currency=…, align=…)` describes a column. `id` is the name of the column in formulas. `type="money"` shows the value with two decimals (“1 500,00”), `currency="UAH"` adds “грн”, `type="decimal"` — a number with digit groups.
- `|for(…):` … `|endfor` repeats the row for every item.
- `|=(…)` is a cell formula. It is computed when all ordinary cells are known: `this_row("к")` — the value of column `к` in this row, `column("с", rows=body_rows())` — the column over the body rows (without header and totals), `cell(row, column)` — a cell by row number (from 1, counting the header) and column.
- `footer=3` — three footer rows; they are not part of `body_rows()`.
- `|:|&(span=4, align="right")` — the arguments of the first cell are written right after `|:`; `span=4` merges four columns.
- `caption=` and `id=` give the caption “Таблиця 1 — Перелік наданих послуг” and the reference target “табл. 1”.

Money is computed with decimal numbers, so kopecks are not lost. Rounding — `round(x, 2)`; the rounding of accounting sums and VAT — the library functions `round_money`, `vat`, `with_vat` (appendix [“Functions”](generated/functions.md)).

## A table without a loop

When the rows are whole records, no loop is needed:

```prml
|code:
склад = [record(назва="Кабель", к=dec("120")), record(назва="Роз'єм", к=dec("40"))]
|end
|table(data=склад, fields=["назва", "к"], titles=["Найменування", "Кількість"], cols=["*", col("30mm", id="к", type="decimal", align="right")], footer=1):
|:|&(align="right") Разом |& |=(sum(column("к", rows=body_rows())))
|end table
```

## A cell of several paragraphs

A compact row `|:` fits in one source line. A cell with a list or several paragraphs uses the expanded form:

```prml
|table(cols=["35%", "*"], header=0):
|row:
|cell: Обов'язки Виконавця
|cell:
Виконавець зобов'язується:

|- надати послуги в строк;
|- передати звіт.
|end cell
|end row
|end table
```

Compact and expanded rows can be mixed in one table.

## Look of a table

The look of a table is set by its style: `|table(style="TableCompact", …)`. The styles sets of the kit have ready ones: `TableGrid` (default), `TableCompact`, `TableNoBorders`; `business` adds `TableServices`, `TableSchedule`, `TableForm`, `TableParties` with set column widths (the table's own `cols` replace them). One-off differences are arguments of the table, the row (`|:(background="#EEEEEE")`) and the cell (`|&(align="center")`): table style → column → row → cell, each level refines the previous one. Lines — `frame=` (outer frame) and `rules=` (`"all"`, `"rows"`, `"cols"`, `"none"`).

A table inside a section with columns (`|section(cols=2)`) takes the width of a column.
