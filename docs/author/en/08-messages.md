<!-- translation: source=docs/author/ru/08-messages.md sections=73eebe0a 800e73b1 bfcaf4da f1e4f272 1623949a -->
<!-- spec: 3.1 3.2 3.4 3.5 4.2 5.2 5.6 5.7 6.4 6.5 14.1 14.2 -->
# Messages of the translator

The translator checks the whole document — from the encoding to references and tables — and reports everything it finds, not only the first error. A document with errors is not built; with warnings it is built, but a warning almost always points to a real problem.

## How to read a message

```
договір.prml:6:9: error[P2201]: name 'сумма' is not defined
 6 | Сума: |(сумма).
   |         ^^^^^
договір.prml: 1 error, 0 warnings
```

- `договір.prml:6:9` — file, line, column. An error in a fragment or a module names its file and the place where it is included.
- `error` — an error, `warning` — a warning.
- `P2201` — the code. The first digit is the area: P0 command line and files, P1 syntax, P2 names and evaluation, P3 styles, P4 structure and references, P5 tables, P6 pages and graphics, P7 modules and project, P8 writing the ODT, P9 technical documentation. The full list with the texts — appendix [“Messages”](generated/diagnostics.md).
- The line with `^^^` shows the place; lines `= help:` and `= note:` are a hint and an explanation.

The language of messages — `--lang uk|ru|en` or the variable `PRIMULA_LANG`. For programs and editors — `--format json`: a list of messages with the fields `code`, `severity`, `message`, `file`, `line`, `column`. Exit code: 0 — no errors, 2 — there are errors.

In Studio the messages of a check are collected in a panel; a click opens the place in the editor, F1 on a construct — its specification section.

## Warnings and the release

`--strict` turns warnings into errors with the same code. This is how the final version is built: unfilled places `|?{…}`, unformatted numbers and direct formatting do not pass.

```sh
primula build договір.prml --strict --pdf
```

## Common errors

### A style without text — P1209

The style name after `|.` is an identifier, not text. If it changed during editing (“Місце-дата” → “Місце і дата”), the line is no longer a style:

```prml error=P1209
|.Місце-дата
```

Restore the style name and write the text after the colon: `|.Місце-дата: м. Харків, 12.10.2026`. The list of style names — the “Styles” panel of Studio or `--dump-styles`.

### Name not defined — P2201

```prml error=P2201
Сума: |(сумма).
```

A typo in the name of a parameter or variable, a parameter not declared in `params:` of the document or the project, a module function without `|import`. In a document the module `std/math` is imported explicitly: `|import("std/math")`.

### A command “swallowed” a word — P2601

```prml error=P2601
|(1)|sellerом
```

A letter right after a command name continues the name: `|sellerом` is the command `sellerом`. The separator `|;` ends the name: `|seller|;ом`.

### A space after the bar — P1201

```prml error=P1201
Ціна | 100 грн.
```

After `|` there must be a letter, `(` or the sign of a short form. The bar itself is written in text as two bars: `||`.

### Wrong closing — P1218, P1219, P1224

`|end` closes the nearest environment, but not control constructs: `|if` is closed by `|endif`, `|for` — `|endfor`, `|def` — `|enddef`. A block `|code:` is closed by a line with a bare `|end`, without a name (`|end code` is the error P1224). A clause in the line form (`|> text`) is not an environment, and `|end` after it is superfluous (P1218).

```prml error=P1218
|> Пункт.
|end
```

### A value cannot be written out — P2603, P2604

`|(…)` writes out a string, a number, a date or markup. `None`, a boolean, a list or a record is the error P2603: use `str()`, `join_list()` or a field of the record.

A fractional number, a sum or a date without a formatting function is the warning P2604:

```prml error=P2604
|(dec("1.5"))
```

Format with the library: `num(x, 2)`, `money(x, "UAH")`, `fmt_date(d, "long")`.

### Unknown style — P3108

```prml error=P3108
|.Невідомий: текст
```

No loaded module has the style: a typo or the set is not named (`styles:`). Which modules are loaded — `--dump-styles` or the “Styles” panel.

### Reference and ID — P4301, P4102

```prml error=P4301
Див. |@("оплата").
```

No target has this `id=`: a typo, or the target is removed or excluded by a condition. A repeated `id=` is the error P4102 with the positions of both places.

### A skipped level — P4201

```prml error=P4201
|< Розділ
|<<< Підрозділ
```

Headings go level by level: after `|<` comes `|<<`, not `|<<<`. The same holds for lists and clauses.

### Table — P5103, P1226

```prml error=P5103
|table(cols=["*", "*"]):
|: а |& б |& в
|end table
```

The number of cells of a row does not match the number of columns (counting `span=`). An empty cell is written explicitly: `|&` without text. Text inside a table outside a row `|:` is the error P1226.

### A header key was renamed — P1120

The keys `document:` and `documents:` of earlier versions were renamed: metadata — `doc:`, in a project — `doc_defaults:` and `ref_documents:`.

### Placeholder — P2635

`|?{…}` was left in the document. In a draft build it is a warning, with `--strict` — an error.

## When it is not clear what is wrong

- Check the piece separately: `primula console документ.prml` opens the evaluator console with the names of the document — an expression can be evaluated there (`:help name` — the description of a function).
- `primula check документ.prml --dump-tree` shows how the translator understood the structure: where a clause ends, what went into a table.
- In Studio the right mouse button on a construct gives a hint and the specification section.
