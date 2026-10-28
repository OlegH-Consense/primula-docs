<!-- translation: source=docs/author/ru/11-libraries.md sections=1204bd77 f1560e95 f2cb4f76 1ff531d8 578f709b 1a348c17 9bb43b07 c435100e -->
<!-- spec: 10.1 10.3 10.5 12 -->
# Libraries: development and use

A Primula library is a directory of `.m.prml` modules and their data used by several projects: checking requisites, names in grammatical cases, payment schedules, a payment QR code. It is developed, tested and released apart from the translator and from the documents: a library is ordinary Primula text, it does not change the language and does not need a build of the translator.

A ready sample is `examples/11-library`: the library `shared/ua-iban` (IBAN UA: checking, groups of four characters, building) and the project `project/` that links it with a symbolic link.

## What a library can do

A module contains only definitions: functions and constants in `|code:`, macros `|def`, `|import` of other modules (section ["Modules: macros and functions"](06-project.md#modules-macros-and-functions)). It can use the whole core — the Python dialect (page ["Code: the Python dialect"](10-code.md)) — and the functions of the standard library: numbers and money, words and cases, dates and workdays, `load_csv`, `load_yaml`, `load_json`, an image from an SVG string (`img(svg=…)`).

What a module does not have, and what to do instead:

| Not available | Instead |
| --- | --- |
| Python code, `import`, input/output, network, clock | data — files next to the module (`load_yaml("data/…")`), a date — an argument of the function |
| `doc.*` of the document (a module is evaluated once per build) | the document passes the language and the date as arguments (`lang="uk"`); the functions of the standard library inside a module follow the document language themselves |
| `ord()`, `chr()`, bitwise operations | the position in an alphabet string: `"ABC…".find(ch)`; tables of values |
| `assert` | `fail("…")` — stops the build with the message and the place of the call |
| heavy computations | a loop of the core runs some tens of thousands of steps per second, the limit is 20 s per evaluation; an algorithm of hundreds of thousands of steps (a QR code, a hash) is requested as a function of the translator, and the library builds on it |

## Directory layout

```text
ua-iban/                 the library (its own repository or directory)
  README.md              purpose, version, licence, functions, sources of the rules
  project.p.prml         the root for the tests: tests/ imports ../iban
  iban.m.prml            the public module: the file name is the namespace (iban.*)
  _tables.m.prml         a helper module (optional)
  data/                  data of the module: YAML, CSV, JSON
  tests/iban-test.prml   test documents
  run-tests.sh           primula check for every test
```

- Names without a leading `_` are the interface of the library; names with `_` are private (`iban._digits` is an error). Change private names freely, public ones only with a new version.
- The first line of a function body is a description string in English, like code comments: `"""IBAN in groups of four."""`. The source shows it, later — the hints of Studio (direction D3).
- The version is the constant `VERSION = "0.1.0"` in the main module and a line in the README; an incompatible change gets a new major number.
- The project file `project.p.prml` is needed by the tests: without it the root is the directory of the test, and `|import("../iban")` leaves the root (P2613). A project that links the library does not read this file.
- Paths of `load_*` and `|import` inside the library are counted from the module file, without `../` outside the library directory.

## Module

```prml file=lib/iban.m.prml
---
kind: module
---
|code:
VERSION = "0.1.0"
_LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def normalized(text):
    """IBAN without spaces, in capitals."""
    return "".join(text.split()).upper()


def problem(text):
    """Why the text is not an IBAN UA, or "" if it is valid."""
    s = normalized(text)
    if not s.startswith("UA") or len(s) != 29 or not s[2:].isdigit():
        return "очікується UA і 27 цифр"
    digits = "".join([c if c.isdigit() else str(_LETTERS.find(c) + 10) for c in s[4:] + s[:4]])
    return "" if int(digits) % 97 == 1 else "не збігається контрольне число"


def check(text):
    """The normalized IBAN; a wrong one stops the build with the reason."""
    reason = problem(text)
    if reason:
        fail(f"IBAN «{text}»: {reason}")
    return normalized(text)
|end
```

A library reports an error in the data of a document with `fail()`: the build stops with the message of the library, the place of `fail` in the module and the line of the document the call came from. For a soft check a function next to it returns the reason (`problem`) or `True`/`False`.

## Tests

A test is an ordinary document: its code compares the results with the expected ones and calls `fail()` at the first difference. Calls at the top level of `|code:` are actions; they run at every check.

```prml
|import("lib/iban")
|code:
def expect(name, got, wanted):
    if got != wanted:
        fail(f"{name}: отримано {repr(got)}, очікувалося {repr(wanted)}")


expect("check", iban.check("ua21 3223 1300 0002 6007 2335 6600 1"), "UA213223130000026007233566001")
expect("problem", iban.problem("UA223223130000026007233566001"), "не збігається контрольне число")
|end
Бібліотека ua-iban |(iban.VERSION).
```

`primula check tests/iban-test.prml` exits with code 0 when all expectations match, and with code 2 and the message of `fail` otherwise; `run-tests.sh` of the sample checks all `tests/*.prml`. Test edge cases and errors, not only the happy path: a wrong check digit, a wrong length, another country.

## Using a library in a project

Three ways, from the most convenient for development to the most reproducible:

| Way | How | When |
| --- | --- | --- |
| symbolic link | `ln -s ../shared/ua-iban lib` in the project root | development, several projects on one machine; the build gives warning P2639 |
| copy | the library directory is copied to `lib/` of the project | release of a document: the project builds the same without outside directories |
| Git submodule | `git submodule add <url> lib/ua-iban` | a project in Git: the library version is pinned by a commit |

```sh
cd мій-проєкт
ln -s ../shared/ua-iban lib
```

```prml skip
|import("lib/iban")
IBAN: |(iban.grouped(рахунок)) (код банку |(iban.bank_code(рахунок))).
```

The link is checked on the path as written (decision 136): `lib` inside the project may lead anywhere, while `../` in the text of a document or a module still does not leave the root. The files of the library go to the build report and to `--embed-sources` as `lib/iban.m.prml`, with hashes — the report shows which version of the library built the document.

## Data with a date of effect

Rates, reference lists and calendars change over time, and an old document must build as it did at release. Keep values with the date they take effect and select by the date the document passes (the date of the document, not the build date):

```yaml file=lib/data/rates.yaml
vat:
  - {from: 2011-01-01, value: 20}
```

```prml
|code:
_rates = load_yaml("lib/data/rates.yaml")


def vat_on(day):
    """VAT rate on a date; the document passes doc.created or the contract date."""
    found = None
    for r in _rates.vat:
        if r["from"] <= day:
            found = r["value"]
    if found is None:
        fail(f"немає ставки на {fmt_date(day, 'short')}")
    return found
|end
Ставка ПДВ: |(vat_on(date(2026, 10, 26))) %.
```

A new value is added as a row with a new date; old rows do not change.

## Release

- README: purpose, functions with examples, version, licence, sources of the rules (standard, law, regulation) — and the date they were checked against.
- Before a release: `run-tests.sh` without errors; the number in `VERSION` and in the README match; the changes are described.
- Do not put real personal data and requisites into the examples of a library — use values that are obviously for training.

For developing a library with AI there is the skill `skills/primula-library`: it follows the same scheme — module, tests, check with the translator.
