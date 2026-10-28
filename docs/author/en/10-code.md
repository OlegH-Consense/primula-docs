<!-- translation: source=docs/author/ru/10-code.md sections=403505f3 ef79757d 7f337785 a64a6c40 d8f2341f c0847abb 8efc1a56 cd2ef759 e1a7a8d0 bf19ac8e 4a44f173 f66d664d -->
<!-- spec: 3.7 4.2 10.3 10.4 12 -->
# Code: the Python dialect

Primula code is written like Python: expressions `|(…)`, arguments of commands, `|code:` blocks, functions and macros. The syntax is a subset of Python 3.11, but the meaning differs in places: numbers are decimal, global names are immutable, there is no output (`print`). This page lists what an author who knows Python needs to know; what works as in Python is not repeated here.

A complete example with tables "expression → Primula → Python 3" is `examples/10-code` (the document `code.prml`, fragments by topic, the error files `forbidden.prml` and `mistakes.prml`). The example shows the source text: code and definitions are not printed in the PDF, so the PDF is read together with the source. Library functions are in the appendix ["Functions of expressions"](generated/functions.md).

## Where code is written

| Form | Purpose |
| --- | --- |
| `\|(сума * 2)` | put a value into the text |
| `\|table(cols=["*", "30mm"])` | arguments of commands are expressions |
| `\|if(n == 1){день}\|else{дні}`, `\|for(p in позиції){…}` | condition and loop; the body is markup, not code |
| `\|code:` … `\|end` | definitions, functions, calculations |
| `\|let(n=5)` | a definition in the middle of the text |
| `\|def підпис(роль):` … `\|enddef` | macro: a function whose body is markup |

## Numbers: decimal instead of int and float

An integer and a number with a point and no exponent are `decimal`: an exact decimal number of up to 64 significant digits that keeps the number of digits after the point. There is no separate `int`: `type(5)` is `"decimal"`. A binary `float` comes only from a literal with an exponent (`1.5e3`) or `float(x)`; `decimal` together with `float` gives `float`.

| Expression | Primula | Python 3 |
| --- | --- | --- |
| `0.1 + 0.2 == 0.3` | `True` | `False` |
| `2.20 * 3` | `6.60` | `6.6000000000000005` |
| `7 / 2` | `3.5` (`decimal`) | `3.5` (`float`) |
| `round(2.5)` | `3` | `2` |
| `round(2.675e0, 2)` | `2.68` | `2.67` |
| `10 ** 70` | error P2309 | an integer of 71 digits |
| `True + 1` | error P2304 | `2` |

There is one rounding for all numbers — half away from zero; a `float` is rounded by its decimal representation. Money is `decimal` only: money functions do not accept `float`.

```prml
Ціна: |(money(2.20 * 3, "UAH")), разом із ПДВ |(money(round(2.20 * 3 * 1.2, 2), "UAH")).
```

## Strings

A string is Unicode characters, as in Python 3: `len("Київ") == 4`. Differences:

- only the methods listed in the specification (section 12.10) exist: `split`, `join`, `strip`, `replace`, `startswith`, `find`, `upper`, `lower`, `title`, `zfill`, `format` and a few others; `center`, `partition`, `encode` are error P2313;
- f-strings follow the Python 3.11 syntax: inside the braces a quote of the same kind as around the string is not allowed (P1208); write `f"{d['k']}"`;
- `"{0.name}".format(r)` is error P2330; a field of a record is read by key: `"{0[name]}"`;
- a format spec (`f"{x:,.2f}"`) is English and knows nothing of the document language; for the text there are `num()`, `money()`, `fmt_date()`.

```prml
|code:
сума = 1234.5
|end
Python-формат: |(f"{сума:,.2f}"); формат документа: |(num(сума, 2)).
```

## Lists, tuples, dictionaries

As in Python, including list and dict comprehensions and unpacking. Differences:

- there are no sets: `{1, 2}` is error P2101; uniqueness — with a dictionary or `not in`;
- there are no operators `|`, `&`, `^`, `<<`, `~`; dictionaries are merged with `{**a, **b}`;
- `is` only with `None` (P2103);
- a dictionary key is an immutable value; `float` and a length cannot be keys (P2317); `5` and `5.00` are one key;
- `range()` and `reversed()` return a list;
- there is no `lambda`: a function for `key=` is an ordinary `def`.

```prml
|code:
def мінус(x):
    return -x
порядок = sorted([3, 1, 2], key=мінус)
|end
|(join_list([str(x) for x in порядок]))
```

## Records

A record (`record`) is an immutable value with fields: `r.назва` or `r["назва"]`. Parameters of the YAML header, project data and the results of `load_csv`, `load_yaml`, `load_json` become records. In Python `namedtuple` is similar, but a record is not a sequence:

- `"назва" in r` and `len(r)` are errors; a field is tested with `hasattr(r, "назва")`;
- a missing field is error P2314; `getattr(r, "ціна", 0)` gives a default value;
- a new record with a changed field is `r.replace(кількість=4)`; into a dictionary — `dict(r)`.

```prml
---
doc: {language: uk-UA}
params:
  сторона: {назва: "ТОВ «Альфа»", код: "12345678"}
---
|(сторона.назва), ІПН: |(getattr(сторона, "ІПН", None) or "—").
```

YAML is read by the rules of Primula: `15.00` is a `decimal` with two digits, a date without quotes is a `datetime`.

## Dates and lengths

A date and a moment are one built-in type `datetime`, without `import`; the precision is a second, there are no time zones.

- `дата + 30`, `дата - 30` shift by days; `дата - дата` is a number of days (`decimal`), not a `timedelta`;
- `hours(36)`, `weeks(2)` are numbers of days: `дата + hours(36)`; calendar months — `add_months(дата, 1)` (31 January + 1 month = 28 February);
- `weekday` is an attribute from 1 (Monday) to 7, not a method from 0;
- a date goes into the text with `fmt_date(дата, "contract")`.

A length is a number with a unit: `10*mm` or `"10mm"`; the constants are `mm`, `cm`, `pt`, `inch` (not `in`). The result is in the unit of the left operand; comparison has a tolerance of 0.001 mm.

```prml
|code:
підписано = date(2026, 10, 12)
оплата = підписано + 10
|end
Оплата до |(fmt_date(оплата, "contract")) — через |(оплата - підписано) днів, |(fmt_date(add_months(підписано, 1), "long")) — через місяць.
```

## Functions

`def` with defaults, `*args`, `**kwargs`, keyword-only parameters, recursion, nested functions and closures; inside a function variables are mutable, and there is `while`. Differences:

- there is no `lambda`, no generators (`yield`), no `global`, `nonlocal`; the only decorator is `@export` (section "Modules and fragments");
- default values are computed once and frozen: the Python trap `def f(x, acc=[])` is error P2318 here at the first `append`;
- a global list passed to a function is frozen too: build a new list;
- instead of Python's recursion limit there are limits: depth 500, 20 s for one evaluation, 10 000 000 elements.

```prml
---
doc: {language: uk-UA}
params:
  позиції:
    - {назва: "Папір", кількість: 20, ціна: 120.50}
    - {назва: "Ручки", кількість: 100, ціна: 15.00}
---
|code:
def рядки(позиції):
    result = []
    for i, p in enumerate(позиції, 1):
        result.append(record(n=i, назва=p.назва, сума=p.кількість * p.ціна))
    return result
|end
|table(cols=["10mm", "*", "35mm"]):
|: № |& Найменування |& Сума, грн
|for(р in рядки(позиції)):
|: |(р.n) |& |(р.назва) |& |(num(р.сума, 2))
|endfor
|end table
```

## Global names: lazy and immutable

This is the second big difference after numbers. Python runs a module from top to bottom and lets a name be reassigned. In Primula the top-level definitions — `x = …`, `def`, `|let`, header parameters — are collected from the whole file in advance, computed on first use and frozen.

- The order in the text does not matter: a name can be used above its definition.
- A second definition is error P2203, `x += 1` at the top level is P2105, a cycle of definitions is P2204. A header parameter cannot be redefined in code either.
- A definition nobody reads is not computed — and its error does not show until the name is needed.
- The other top-level statements (`for`, `if`, calls) are actions: they run after the definitions are collected, and the names inside them are local (warning P2501).
- A conditional value is a conditional expression: `ставка = 20 if платник_пдв else 0`.
- Accumulation is a list comprehension or a function, not `append` in a top-level loop (P2318).

```prml
|code:
разом = ціна * кількість
ціна = 250.00
кількість = 4
ставка = 20 if разом > 500 else 0
|end
Разом |(num(разом, 2)), ПДВ |(ставка) %.
```

```prml error=P2203
|code:
x = 1
x = 2
|end
```

## Modules and fragments

A **module** (`.m.prml`, `|import`) contains only definitions. All its names without a leading `_` are public, nothing needs to be exported; a name with `_` is really private (`модуль._имя` is an error).

```prml file=lib/ціни.m.prml
|code:
_ставка = 20

def з_пдв(сума, ставка=_ставка):
    return round(сума * (100 + ставка) / 100, 2)
|end
```

| Import | Access |
| --- | --- |
| `\|import("lib/ціни")` | `ціни.з_пдв(…)`, a macro — `\|ціни.ім'я(…)` |
| `\|import("lib/ціни", "з_пдв")` | `з_пдв(…)` without the prefix |
| `\|import("lib/ціни", alias="ц")` | `ц.з_пдв(…)` (`as` is a Python keyword) |

An `|import` of the document also works in the fragments the document includes; an `|import` inside a fragment works only in that fragment. A path is written from the file with the command.

```prml
|import("lib/ціни")
Разом із ПДВ: |(num(ціни.з_пдв(1000.00), 2)) грн.
```

A **fragment** (`.f.prml`, `|include`) is document text with its own definitions, and they are private: one fragment can be included twice without a conflict. The document sees only what is exported (decision 135):

| In the fragment | What is exported |
| --- | --- |
| `@export` above a top-level `def f(…)` of `\|code:` | the function under its own name |
| `@export(name="g")` above `def _f(…)` | the function under the name `g`; `_f` stays private |
| `\|export("підпис", "f")` | names already defined: macros `\|def`, functions, `\|let` |
| `\|let(x=…, export=True)`, `\|export(x=…)` | a new value |

```prml file=fragments/знижки.f.prml
---
kind: fragment
---
|code:
@export
def знижка(сума, відсоток):
    return round(сума * (100 - відсоток) / 100, 2)
|end
|def рядок(назва, сума):
|(назва) — |(num(сума, 2)) грн
|enddef
|export("рядок")
```

```prml
|include("fragments/знижки")
|рядок("Папір зі знижкою", знижка(2410.00, 5))
```

If two fragments export the same name, the conflict is resolved where they are included: `|include(…, ns="f")` puts the exports into `f.*`, `rename={…}` renames them. `@export` outside a fragment is error P2610, above a nested function P2106, in a module warning P2638 (everything is public there anyway). Functions used by several documents belong in a module; a fragment exports what belongs to its text.

## Values in the text and macros

There is no output: a value reaches the document only through the expression `|(…)`, and the type decides how.

- A string, a number, a date, markup (`content`) are inserted. A fractional number or a date without formatting is warning P2604: format them with `num()`, `money()`, `fmt_date()`.
- `None`, `bool`, a list, a dictionary, a record are error P2603, not "None" or "[1, 2]" as `str()` would give. An optional value — `|(x or "—")`, a list — `join_list()`.
- Markup is opaque: `markup("…") + "…"` is an error; join the strings first, then call `markup()`.
- A function from `|code:` called as a command `|f(…)` inserts its result; a macro `|def` receives the body of the call as the parameter `body`.

```prml error=P2603
|(None)
```

```prml
|code:
def жирно(текст):
    return markup("|*{" + текст + "}")
|end
|def позначка(текст, body):
|.Note: |*{|(текст):} |(body)
|enddef
|позначка("Увага"):
Текст із |жирно("виділенням").
|end
```

## What the core does not have

A document must build the same way on any machine, so the core has no input/output (except `load_*`), no clock (`build_date()` is fixed by `--build-date`), no random numbers and no access to Python internals. Forbidden are `import` (modules come in with `|import` in the markup), `class` (data is a `record`), `try`/`raise` (an error stops the build with its position; `fail("…")` is a deliberate error), `lambda`, `yield`, `async`, `global`, `nonlocal`, `del`, `with`, sets, bitwise operators, annotations, `else` on loops, decorators other than `@export`, names like `__class__`. All of this is found when the code is parsed, before evaluation; the full list with replacements is in the example (`forbidden.prml`) and in section 12.2 of the specification.

```prml error=P2101
|code:
квадрат = lambda x: x * x
|end
```
