---
name: primula-library
description: Develop, test and release a Primula library — a directory of .m.prml modules with data, shared by several Primula projects (checks of requisites, names in cases, payment QR codes, schedules, rates with a date of effect) — and connect it to a project by a symbolic link, a copy or a Git submodule. Use when a task asks for a reusable Primula module or library, for tests of .m.prml modules, or for one of the planned libraries (ua_ids, names, payment_qr, schema, legal, finance, charts and others).
---

# Primula libraries

A Primula library is a directory of modules (`*.m.prml`) and their data that several
projects import. It is plain Primula: no Python code, no build of the translator. It is
developed and tested on its own and connected to a project as `lib/` (decision 136).
For writing documents and the language itself follow the skill `primula-docs`; this
skill adds what is specific to libraries.

**Never hand over a library whose tests have not passed `primula check`.**

## 1. Before writing

- Find the translator as in `primula-docs` (`primula --version`, or the launcher of a
  source checkout). Read the task statement if the library is a planned one:
  `docs/libraries/<name>.md` in the Primula source tree.
- Libraries that already exist are in `libraries/` of the source tree and in
  `share/primula-docs/libraries/` of an installation (ua_ids, names, ua_data, legal,
  finance, payment_qr, epc_qr, codes, charts, stats, electronics, vcs). Look at what
  one contains before writing another: `primula describe libraries/<name>/<name>.m.prml`
  lists its public functions with signatures and descriptions, constants and the
  version (the code is not run). Write a docstring for every public function: it is the
  text `describe` shows.
- Check what the core and the standard library already give:
  `primula commands --functions`, `primula commands --format json --lang en` (`functions`).
  Do not reimplement money, words, cases of numbers, dates, workdays, VAT — call them.
- Find the source of every rule (standard, law, NBU regulation) and write it with the
  date you checked it into the README. Do not invent algorithms, codes or real
  requisites; if a rule cannot be verified, say so and leave a placeholder.

## 2. Layout

Start from [assets/template/](assets/template/) (copy it, rename `mylib`):

```text
mylib/
  README.md            purpose, version, licence, functions, sources of the rules
  project.p.prml       makes this directory the root for tests/ (they import ../mylib)
  mylib.m.prml         public module: the file name is the namespace (mylib.*)
  data/rates.yaml      data of the module, read with load_yaml("data/…")
  tests/mylib-test.prml  test documents
  run-tests.sh         primula check for every tests/*.prml
```

- Public names have no leading `_`; `_name` is private (`mylib._x` is an error).
- `VERSION = "0.1.0"` in the main module and in the README; an incompatible change of a
  public name gets a new major number.
- The first line of every public function is an English docstring; code comments are
  English. Messages for the author (`fail`, returned reasons) are in the document
  language, Ukrainian by default.
- Paths of `load_*` and `|import` are relative to the module file and stay inside the
  library directory.

## 3. What a module can and cannot do

A module holds only definitions: `|code:` (functions, constants), `|def` macros,
`|import`, comments. Text is an error. It is evaluated once per build and does not see
`doc.*` of the document.

| Missing | Use |
| --- | --- |
| Python `import`, I/O, network, clock, random | data files next to the module; dates as arguments |
| `doc.language`, `doc.created` | arguments (`lang="uk"`, `day`); library functions such as `words`, `money_full` follow the document language by themselves |
| `ord`, `chr`, bitwise operators, sets | `"ABC…".find(ch)`, dictionaries, lookup tables |
| `assert`, `try`/`raise` | `fail("message")` — stops the build with the message and the call chain |
| `lambda`, generators, `class`, `global` | `def`, list comprehensions, records and dictionaries |
| heavy loops | the core runs some tens of thousands of loop steps per second, 20 s per evaluation; if an algorithm needs hundreds of thousands of steps (QR, hashes), stop and ask for a translator primitive instead of writing it in Primula |

Global names of a module are lazy and frozen: build lists with comprehensions or inside
functions, never by `append` at the top level (P2318). Numbers are `decimal`; money must
stay `decimal` (`dec("0.20")`, not `0.2e0`).

## 4. Errors for the author

- A wrong input of a document → `fail(f"mylib: … «{value}»: reason")`. The build stops
  at the call in the document with the library message.
- Offer a soft variant next to it: `problem(x)` returning the reason or `""`, and
  `is_valid(x)` returning `True`/`False`, so a document can choose the text itself.

## 5. Tests

A test is a document in `tests/` that imports `../mylib`, compares results with
`expect(name, got, wanted)` (a function calling `fail` on a difference; top-level calls
in `|code:` are actions and run at every check) and prints a few results for a reader.
Cover edge cases and errors, not only the happy path: boundaries, wrong lengths,
wrong check digits, dates before the first value of the data.

```sh
PRIMULA=primula ./run-tests.sh                   # every tests/*.prml, exit 1 on a failure
primula check tests/mylib-test.prml --lang en    # one test with its diagnostics
```

A failing expectation is `P2340 fail: <name>: отримано …, очікувалося …` with the line of
the `expect` call. Fix the module or — only if the rule was misread — the expectation.

## 6. Data with a date of effect

Rates, calendars and reference lists change; an old document must build the same.
Store rows `{from: YYYY-MM-DD, value: …}`, add new rows, never edit old ones, and select
by the date the document passes (`doc.created`, a contract date), never by the build date.

## 7. Connecting to a project

| Way | Command | Note |
| --- | --- | --- |
| symbolic link | `ln -s ../shared/mylib lib` in the project root | development; the build gives warning P2639 once |
| copy | copy the directory to `lib/mylib` | released documents rebuild without outside directories |
| Git submodule | `git submodule add <url> lib/mylib` | the version is pinned by a commit |

The document: `|import("lib/mylib")` (or `"lib/mylib/mylib"` when the whole directory
is `lib/mylib`). The root boundary is checked on the written path: a link inside the
project may lead outside it; `../` in the text cannot. The build report lists the library
files as `lib/…` with hashes.

## 8. Release checklist

1. `run-tests.sh` passes; a document of a real project that uses the library passes
   `primula check` (only the expected P2639 when linked).
2. `VERSION`, README version and the list of functions agree with the module.
3. README names the sources of the rules with the date checked, and the licence.
4. No real personal data or requisites in examples and tests (use training values;
   for IBAN the sample `UA213223130000026007233566001` is a published example).

A complete sample: `examples/11-library` in the Primula source tree (library
`shared/ua-iban`, project `project/` with the link `lib`). Guide page for authors:
`docs/author/en/11-libraries.md`.
