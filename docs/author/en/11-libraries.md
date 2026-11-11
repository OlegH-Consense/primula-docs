<!-- translation: source=docs/author/ru/11-libraries.md sections=1204bd77 c5370488 f1560e95 f2cb4f76 1ff531d8 578f709b 1a348c17 9bb43b07 4e53dd06 c435100e 58de54c0 -->
<!-- spec: 10.1 10.3 10.5 12 -->
# Libraries: development and use

A Primula library is a directory of `.m.prml` modules and their data used by several projects: checking requisites, names in grammatical cases, payment schedules, a payment QR code. It is developed, tested and released apart from the translator and from the documents: a library is ordinary Primula text, it does not change the language and does not need a build of the translator.

A ready sample is `examples/11-library`: the library `shared/ua-iban` (IBAN UA: checking, groups of four characters, building) and the project `project/` that links it with a symbolic link.

## The libraries of the kit

The repository and the installation package (`share/primula-docs/libraries/`) hold ready libraries of version 0.1.0. Each is a directory with its own `README.md` (functions, sources of the rules, the date they were checked, limits), tests and an example in `demo/`.

| Library | What it does | Main functions |
| --- | --- | --- |
| `ua_ids` | checks and formats ЄДРПОУ, РНОКПП, IBAN UA | `edrpou`, `rnokpp`, `iban_grouped`, `iban_make`, `party_code` |
| `names` | full names in cases, initials, signature, positions | `case`, `initials`, `signature`, `position_case` |
| `ua_data` | NBU and VAT rates, minimum wage, subsistence minimum, CPI, calendar — with the date of effect | `discount_rate_on`, `vat_rate_on`, `min_wage_on`, `cpi_on`, `calendar` |
| `legal` | penalty, 3 % per annum, inflation losses, terms | `penalty`, `claim_table`, `annual3`, `inflation_losses`, `deadline` |
| `finance` | annuity, payment schedule, NPV and IRR, straight-line depreciation | `annuity_payment`, `schedule`, `npv`, `irr`, `straight_line` |
| `estimate` | estimate: totals by sections, discount, VAT, amount in words; commands `\|estimate.table(…)`, `\|estimate.total_words(…)` | `table`, `total_words`, `totals`, `section_total` |
| `bib` | bibliography by DSTU 8302:2015: numbered citations `[3, с. 45]` and the list of references; commands `\|bib.cite(…)`, `\|bib.references(…)` | `registry`, `cite`, `references`, `entry` |
| `payment_qr` | payment QR by the rules of the NBU (hryvnia) | `payload`, `svg`, `link` |
| `epc_qr` | SEPA payment QR (euro), EPC069-12 | `payload`, `svg` |
| `codes` | check digits of EAN-13, ISBN, Luhn; EAN-13 bar code | `ean13_check`, `isbn13`, `luhn_check`, `ean13_svg` |
| `charts` | bars, line and pie for `\|figure(svg=…)` | `bar`, `line`, `pie` |
| `stats` | median, mode, variance, percentile, moving average | `median`, `mode`, `variance`, `percentile` |
| `electronics` | E3–E96 series, divider, connections, power, tolerance | `series`, `nearest`, `divider`, `parallel` |
| `vcs` | the change table of a technical document from the Git history | `changes` |

A single library is connected by a link `lib` to its directory and imported as `lib/<name>` (as its `README.md` says); with several libraries each has its own link `lib/<name>` and the import `lib/<name>/<name>` (see "Using a library in a project"):

```sh
ln -s ~/.local/share/primula-docs/libraries/ua_ids lib/ua_ids
```

```prml skip
|import("lib/ua_ids/ua_ids")
ЄДРПОУ |(ua_ids.edrpou(код)), IBAN |(ua_ids.iban_grouped(рахунок)).
```

What to know:

- A module cannot import a neighbouring library (`../` is forbidden), so `legal` gets the data as an argument: `legal.penalty(борг, початок, сплата, ua_data.series("discount"))`.
- `ua_data` keeps values with a start date and a source. A date after the last record of a series is an error, not a silent "last value": the data must be kept up to date (a new row with a new date; old rows do not change). The data of the library was checked on 31.10.2026, the calendar covers 2024–2026.
- `legal` calculates by the formulas and the data of the library; it is not legal advice. The legal grounds of the calculation and their sources are listed in its `README.md` (the laws were checked against the texts on zakon.rada.gov.ua; the positions of the courts come from the announcements of the Supreme Court and from reviews, not from the full texts of the decisions): check them before using the result in a claim.
- Functions with the suffix `_problem` return the reason as text (an empty string when all is well) and stop nothing; functions without it stop the build on an error.

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

## What is inside a file: primula describe

`primula describe FILE` shows a summary of a file that is not built into a document.

```sh
primula describe lib/ua_ids/ua_ids.m.prml        # functions, constants, version of a module
primula describe styles/проєкт.s.prml            # extends, defaults, defined styles
primula describe project.p.prml --format json    # for editors and Studio
```

For a module it prints the leading `|%` comment, `VERSION`, the public functions with the signature and the first line of the description (a docstring, or the comment above `def`), the public constants and the number of private names; the code is not run. So write a docstring for every function: it goes into the summary. `primula view` shows the same summary for a module, a styles module and a project.

## Release

- README: purpose, functions with examples, version, licence, sources of the rules (standard, law, regulation) — and the date they were checked against.
- Before a release: `run-tests.sh` without errors; the number in `VERSION` and in the README match; the changes are described.
- Do not put real personal data and requisites into the examples of a library — use values that are obviously for training.

For developing a library with AI there is the skill `skills/primula-library`: it follows the same scheme — module, tests, check with the translator.

## Commands of a module: `|def`, `param`, the accumulator

A module can define not only functions but **commands**: a `|def` macro is called as `|module.command(…)` (`|estimate.table(…)`, `|bib.cite(…)`). The name of a macro may coincide with the name of a built-in command (`table`, `list`): the call always has the namespace, the built-in command is not touched.

- The description of a command and its parameters is the `|%` comments right above `|def`; a line `|% name: text` describes a parameter. Studio shows them in the Palette, the hint and the completion, and `primula describe module` and `primula commands --document FILE` give them to other programs.
- The settings of a library come from the parameters of the document with the function `param("name", default)` (for example `currency` of `estimate`, `bib_order` of `bib`): a macro does not see the variables of the document, but it sees the parameters.
- Values that depend on the whole document (the numbers of references by the order of the first reference, a list of terms) are collected by the accumulator: `collect("name", value)` in the text and `collected("name")` after the whole document; if `collected` is called, the document is evaluated twice (section 4.6 of the specification).

Samples are the examples `examples/13-estimate` (an estimate), `14-bibliography` (references by the order of mention) and `15-own-commands` (an own command and a glossary).
