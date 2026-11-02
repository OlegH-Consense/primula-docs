<!-- translation: source=primula-spec-v1.1-draft.ru.md sections=1f60b6f5 505324eb a2308543 684dfb65 cf123f98 2807bbcf e73d946e 93a53c09 5412bed4 b0a8c9aa 9737aa74 d933012b 655eea51 04af28c7 40c8ec5c 0db714ba 857c4563 f3787e61 83c45290 80276b2c 78ee5e9c c2d79cdf f5155d41 -->
# Primula — a document markup language: specification v1.1-draft

14.10.2026 · name: Primula Documenting System (`primula-docs`), the language is Primula, file extension `.prml` (with sub-extensions `.f`, `.m`, `.s`, `.p`); ngml is the internal working name · English translation of the Russian original `primula-spec-v1.1-draft.ru.md` (where they differ, the original is normative); examples of business documents are in Ukrainian

## Contents

0. Status, language version, normative references, conventions
1. Overview and principles
2. Files: encoding, kinds of files, YAML header
3. Lexical structure
4. Text markup
5. Document structure
6. Tables
7. Pages, sections, headers and footers
8. Graphics and frames
9. Technical documentation tools
10. Modules, project, data, build
11. Styles
12. Computation core
13. Standard library (a separate document)
14. Diagnostics, build report, modes
15. Mapping to ODF

Appendices: 1 — grammar (EBNF); 2 — built-in commands and reserved names; 3 — differences from ODT Markdown Kit 0.4 and conversion rules; 4 — decision log and open questions; 5 — end-to-end examples.

The standard library is described in a separate document, `primula-stdlib-v1.1-draft.en.md` (section 13).

## 0. Status, language version, normative references, conventions

### 0.1. Status

This document is the consolidated draft of specification v1.1-draft.

Language version: `1.1`; Unicode version 15.1 (the definitions of the classes `XID_Start`/`XID_Continue`, the categories `P*`/`S*` and the normalization forms NFC/NFKC). A file without an explicit version declaration is read by the rules of this version; the default rules (for example, the Unicode version for character classes and identifiers, section 3.9) are fixed by the language version and are not changed by system or project settings.

The standard library is versioned separately (section 13).

### 0.2. Normative references

| Designation | Use |
| --- | --- |
| OASIS ODF 1.3 | output format: ODT text documents |
| Unicode, normalization form NFC | text encoding and normalization |
| Unicode, UAX #31 (identifiers), UAX #15 (NFKC) | names entered by the author; comparison of names (section 3.9) |
| YAML 1.2 | file headers, data |
| Python 3.11 grammar (`ast`) | syntax of the computation core: the Python 3.11 grammar with the whitelist of section 12.2; an f-string contains no nested quotes of the same kind (no PEP 701); the translator checks this regardless of the interpreter version |
| Starlark specification | reference point for the semantics of the core; differences are in section 12 |
| W3C EBNF (XML 1.0, section 6) | grammar notation, appendix 1 |
| DSTU 4163:2020 | structure profile `business`, date formats |
| DSTU 3008:2015 | structure profile `report` |
| Resolution of the Cabinet of Ministers of Ukraine No. 55 of 27.01.2010 | romanization of the Ukrainian alphabet |
| ISO 3864-2, ANSI Z535.6, IEC/IEEE 82079-1 | hierarchy of signal words of admonitions |

### 0.3. Conventions

- "Must", "shall", "is forbidden" are mandatory requirements; "may", "is recommended" are optional.
- "Error" is a build error: the result is not written, the exit code is 2. "Warning" is a message in the report; with the `--strict` option a warning becomes an error.
- The descriptive texts of the original are in Russian (this translation is in English); document examples are in Ukrainian.
- In the tables of this document the character `|` inside code is written as `\|` because of the limits of the Markdown table syntax.

## 1. Overview and principles

### 1.1. Purpose

Primula is a command-based document markup language with a built-in computation core. The translator compiles source files into an editable ODT with named styles. The language is the next generation of ODT Markdown Kit (Kit 0.4.1): it removes the limits of extended Markdown for complex tables, parametrization, assembly from fragments, conditional text and computation.

Target documents:

- business and legal: contracts, acts, letters, requisites, amounts in words; the Ukrainian locale and formatting norms;
- technical, with complex parametrization and assembly from fragments: operating manuals, technical descriptions (datasheets), information sheets.

A subsystem for mathematical formulas is not included. Superscripts and subscripts, units of measurement and non-breaking spaces are supported.

### 1.2. Positioning

Between Markdown with Pandoc (simple but weak) and LaTeX or Typst (powerful, but the result is PDF typesetting) there is no programmable language for business documents whose result is an editable office document. Primula fills this niche: "Typst for office paperwork", compiled business and technical documents → ODF. The result stays a Writer document: its styles can be adjusted and its text edited.

### 1.3. Survey of existing languages and technologies

| Language, system | Entry into command mode | Model | What was taken | What was avoided |
| --- | --- | --- | --- | --- |
| troff/groff (tbl, pic, eqn) | `.cmd` at line start, `\x` inside a line | macro substitution | line commands without closing; column specification separate from data (tbl) | implicit font state (`\fB…\fP`), weak diagnostics |
| TeX, LaTeX, ConTeXt | `\cmd`, groups `{}` | macro expansion | key=value parameters, `\setup…` (ConTeXt), references through auxiliary files, tabularray | macro expansion errors, hard debugging, catcodes |
| Texinfo, Scribe (1980) | `@cmd{…}`, `@@` is a literal | declarative markup | a single control character, doubling as escaping | — |
| Scribble (Racket) | `@cmd[args]{text}` | evaluation of a full program | separation of data arguments and text arguments | the author does not need a full programming language |
| Pollen | `◊cmd{…}` | X-expression tree | the document as a tree, tag functions | the `◊` character is awkward to type |
| Typst | `#` is code, `[…]` returns to text | evaluated tree of typed values | `set`/`show` rules for styles; content as a value; `table`/`cell` with spans; page changes in the middle of a document; modules | aimed at PDF typesetting, not an editable format |
| AsciiDoc | attributes `[…]`, blocks `====` | markup and attributes | cell specifiers (spans, complex content), `include::[tag=…]`, conditions | the syntax grew unevenly |
| reStructuredText | directives `.. name::` | docutils tree | roles and directives as an extensible model | sensitivity to indentation, tables drawn as pictures |
| Org-mode | `#+KEY:` | markup and Emacs Lisp | table formulas (`#+TBLFM`, cell references) | tied to Emacs |
| Djot | — | lightweight markup | grammar without ambiguity, linear parsing | — |
| Markdoc, MDX | `{% tag %}`, JSX | Markdown and tags | limited logic (Markdoc) is safer than full JS | hybrid syntax reads badly |
| Jinja, Liquid, m4 | `{{ }}`, `{% %}` | text templating | filters, loops, sandbox (Liquid) | "text to text" substitution without structure (m4) |
| DocBook, SGML, XSL-FO | tags | strict schema | schema validation; SGML short forms (SHORTREF) | verbosity |
| DITA | tags, profiling attributes | topic model | conditional build (ditaval), reuse by keys (conref, keys) | complex infrastructure |
| Pandoc, Quarto | — | AST pipeline | the split "parse → AST → filters → output" | limited by the source Markdown |
| Starlark | — | restricted Python-like dialect | determinism, frozen values, no input/output | — |

The limit of what the result can do is set by the ODF model: anchored frames with wrapping, sections with columns, master pages for changing the format, tables with spans and borders of individual sides, Writer fields.

### 1.4. Principles

1. A single control character `|`; `||` is a literal `|`. Everything else is text.
2. The markup is entirely command-based; frequent commands have short forms. The characters `*`, `_`, `#`, `1.` do not change the meaning of text.
3. What follows `|` is determined by the syntax alone, without a command reference: this is needed for highlighting, tree-sitter and LSP.
4. Command names are static; computed behaviour is given by expressions in the arguments.
5. The computation core is a subset of Python with semantics modelled on Starlark: determinism, no input/output, limits.
6. The language describes only what ODF expresses natively.
7. Three levels of abstraction: semantic constructs (library functions that can be redefined), named styles (the main working layer), direct ODF properties (explicitly marked, checked).
8. The result is an editable ODT with a finite set of named styles.
9. Diagnostics give the file, line and column through all inclusions and macros.
10. Profiles and formatting standards (DSTU 3008, the business profile) set defaults, not rigid rules: each of their decisions — a style, a format, the split of an element into paragraphs — is overridden by a setting when something else matters more to the document (for example, space on the page).

## 2. Files: encoding, kinds of files, YAML header

### 2.1. Encoding

- Source files are UTF-8; line breaks are normalized to LF.
- The text of source files and loaded data is brought to the Unicode normalization form NFC at the lexical stage: a letter with a diacritic ("й", "ї") is always one character.

### 2.2. Kinds of files

| Kind | `kind` | Sub-extension | Purpose | After the header |
| --- | --- | --- | --- | --- |
| document | `document` (default) | none: `name.prml` | built into ODT | markup |
| fragment | `fragment` | `.f.prml` | inserted into a document with `\|include` | markup |
| module | `module` | `.m.prml` | definitions: functions, macros, constants; loaded with `\|import` | markup (definitions only) |
| styles module | `styles` | `.s.prml` | styles, structure profile, library dictionaries | code (a subset of Python) |
| project | `project` | `.p.prml` | shared parameters, styles, build targets, batch build | code (a subset of Python) |

- All kinds of files have the extension `.prml`. The kind of a file is determined as follows: the header key `kind`, if present; otherwise the sub-extension; otherwise the file is a document. The sub-extension is optional and duplicates `kind` for convenience (file manager, editor, search by the mask `*.m.prml`).
- If `kind` and the sub-extension disagree, `kind` applies and a warning goes to the report (group `P7`); with `--strict` it is an error.
- Only four sub-extensions are reserved: `.f`, `.m`, `.s`, `.p`. A name like `report.f.prml` is a fragment; `a.b.prml` is a document named `a.b`.
- The module name in `\|import` is taken from the file name before the sub-extension: the file `vat.m.prml` is loaded as `vat` (section 10.3).
- An unclosed `|code:` up to the end of the file is forbidden in every kind of file.
- In styles modules and the project the whole content after the header is code; the `|code:` … `|end` wrapper is not needed; comments are `#`.

### 2.3. YAML header

Static data are written as a YAML header between `---` lines at the very beginning of the file. The header is read without executing code: Studio and external programs use it. Header values are data only, without expressions. The header is optional; in a styles module and a project it holds the main description.

Keys of a document header:

| Key | Meaning |
| --- | --- |
| `kind` | kind of file |
| `primula` | language declaration: `{version: "1.1"}`. The translator accepts only the version it implements (now 1.1); any other, including `1.0`, is an error "language version not supported" listing the incompatibilities of version 1.0 (the `para` mode, the types `int`, `date`, `days`, `style`, step limits); there is no compatibility mode. A missing declaration is allowed. The key `lines` of version 1.0 has been removed: its presence is an error "line mode removed" (section 3.4) |
| `doc` | ODT metadata: `title`, `subject`, `description`, `creator`, `organization`, `language`, `identifier`, `revision`, `status`, `created`, `modified`, `keywords`; in text and code under the same name: `\|(doc.title)`; the document language and the mapping to `meta.xml` are in section 15. Defaults come from the project key `doc_defaults` (section 10.6): a document key replaces the project key of the same name, the others are taken from the project |
| `params` | document parameters with default values |
| `structure` | an override of the structure profile, for example `{numbering: {headings: false}}` |
| `styles` | styles modules of the document: a list of paths or one string; added as layers after the project modules and before the definitions in the document code (section 11.7) |
| `references` | project documents whose targets the document refers to: `[contract]` — names from the project's `ref_documents` (sections 5.7, 10.6) |

```
---
doc:
  title: "Договір поставки"
  identifier: "Д-2026-017"
  language: uk-UA
  status: "проєкт"
  created: 2026-10-12
params:
  vat: true
  delivery_days: 5
---
```

Names of header keys (decision 129): the metadata section is named the same as the name under which its values are seen in text and code — `doc:` and `doc.title`; parameters (`params`) are seen simply by their names (`vat`), project parameters as `project.*`. The keys `document` (document metadata and their defaults in the project) and `documents` (project documents for references) of earlier drafts have been renamed to `doc`, `doc_defaults` and `ref_documents`; the old name is an error that names the new one (P1120); there are no synonyms.

Header values are converted by the rules of `load_yaml` (section 12.6): mappings become records (`record`) with dot access, for example `|(buyer.name)`; values like `2026-10-12` and `2026-10-12T14:30` become `datetime` values (section 12.3). Header keys without a predefined meaning (user keys) may be Unicode identifiers (section 3.9).

A fragment header contains only `params` (and, if needed, `primula`, `kind`). The keys of a project header are in section 10.6, of a styles module in section 11.1.

## 3. Lexical structure

### 3.1. The character after `|`

| Next character | Meaning |
| --- | --- |
| `\|` | literal `\|` |
| a letter (Unicode `XID_Start`, section 3.9) | long command (identifier) |
| `(` | expression |
| an ASCII punctuation character or a single Unicode character of the categories `P*` (punctuation) and `S*` (symbols) | short form (section 3.3), including `\|—` (em dash U+2014, category `Pd`) |
| space, end of line, digit, control character, a character of other categories | error |

An undefined short form is an error: this keeps a reserve for future versions, and a typo does not silently turn into text. For `P*` and `S*` characters that look like defined forms (`–` U+2013, `−` U+2212 instead of `|—`), the error contains a hint. Reserved: `|$`, `|[`, `|]` and any other `P*`/`S*` character not listed in section 3.3.

The Unicode version (15.1) that defines the character categories and identifier properties is fixed by the language version (section 0.1); an update of the Unicode tables in the runtime environment does not change the behaviour of a file.

### 3.2. Long form of commands

```
command    := "|" name arguments? body?
name       := identifier ("." identifier)*             ; Unicode identifier (section 3.9), dots — modules
arguments  := "(" Python-call-arguments ")"
body       := "{" content "}"                          ; inline
            | ":" " " rest-of-line                     ; line
            | ":" line-break block closing             ; environment
```

- There are no spaces between the name, `(` and `{`.
- Forms with `:` are recognized only when the command is the first thing on the line; in the middle of a line a `:` after a command is text.
- A literal colon after a command at the start of a line is written after the empty separator: `|seller|;: код ЄДРПОУ …`. Otherwise the build reports "the command takes no body" with a hint about `|;`.
- A body `{…}` may span several lines; braces inside are counted for balance; an unbalanced brace is written as `|{` or `|}`. Outside a body `{` and `}` are text.
- A name ends at the first character that cannot be part of an identifier. If a letter (including a Cyrillic one) follows the command immediately, the separator `|;` is needed: the text "`|seller`ом" is read as the command `sellerом`. If the name is not found but its beginning matches a known command or variable, the error contains the hint "`|;` needed".
- Arguments `(…)` are parsed by the parser of the Python subset: strings, lists, dictionaries and nested brackets work naturally.
- Arguments are core expressions. They are evaluated in the evaluation phase (section 3.8). When the tree is built, only `path`, `part` and `key` of `|include` (section 10.2) are known statically: inclusion is transparent for clause scopes (section 3.6). There are no other such arguments: a heading closes a clause scope at any level, so `level=` is evaluated in the evaluation phase like any expression, including from a macro parameter. If `path`, `part` or `key` cannot be evaluated statically, the build reports: "the value must be known when the tree is built". The argument of any future form that changes scope boundaries must be static.
- Arguments `(…)` may span several lines: inside the brackets a line break does not end a line form. The same holds for `|(…)` and `|=(…)`. The end of the command is the closing bracket of the arguments.
- A long command at the start of a line is a block command if the line ends right after its arguments or continues with forms with `:`; otherwise the line is text and the command is inline (`|img("logo.png", height="8mm") в тексті`).
- User commands are functions: a call of a built-in command and of a user command look the same; the body is passed as the parameter `body`.
- The way a macro result is inserted is determined by the form of the call: a line command or an environment inserts the blocks of the macro body; a call inside a line inserts inline content if the macro body consists of one paragraph, otherwise it is an error.
- If a call passes a body (`{…}` or an environment), the macro must have a parameter `body` (its value is `content`), otherwise it is an error; a `body` parameter without a default requires a body in the call. Inside the macro the body is inserted with the expression `|(body)`.
- A `|def` macro is a value of type `function`; a call from code returns `content`. A `def` function from a code block called as a markup command inserts its result by the rules of section 4.2.
- The scope of a macro body is lexical: the parameters, its own local names and the global names of the module or document where the macro is defined; the local names of the call site are not visible.
- A dynamic call is possible only through an expression: `|(fn(args))` or `|call(fn, args){…}`.

### 3.3. Short forms

A short form is `|` and a single character: an ASCII punctuation character or a Unicode character of the categories `P*`/`S*` (section 3.1). Any short form accepts optional `(arguments)`. The heading level is given either by the number of `<` (`|<<<<`) or by an argument with a single `<` (`|<(level=4) Назва`); both at once is an error. The table below is the only complete list of short forms; other sections refer to it.

| Form | Where | Meaning | Environment closing |
| --- | --- | --- | --- |
| `\|\|` | everywhere | literal `\|` | — |
| `\|{` `\|}` | everywhere | literal braces | — |
| `\|;` | everywhere | empty separator (command boundary) | — |
| `\|%` | everywhere | comment to the end of the line; a line consisting of a comment disappears completely | — |
| `\|(expression)` | everywhere | value of the expression | — |
| `\|\` | in a line | line break inside a paragraph | — |
| `\|~` | in a line | non-breaking space | — |
| `\|*{…}` | in a line | bold (style `Strong`) | — |
| `\|/{…}` | in a line | italic (style `Emphasis`) | — |
| `\|_{…}` | in a line | underline (style `Underline`) | — |
| `\|^{…}` | in a line | superscript (style `Superscript`) | — |
| `\|,{…}` | in a line | subscript (style `Subscript`) | — |
| `\|—{…}` | in a line | strikethrough (style `StrikeText`) | — |
| ``\|`{…}`` | in a line | monospace: designations, codes (style `Code`) | — |
| `\|"{…}` | in a line | quotation marks of the document language («…» for uk); no style | — |
| `\|?{…}` | in a line | draft placeholder (style `Placeholder`) | — |
| `\|.Ім'я{…}`, `\|.(expression){…}` | in a line | character style | — |
| `\|.Ім'я:`, `\|.(expression):` | line start | paragraph style (a line or an environment) | `style` (`\|end.Ім'я`) |
| `\|@("id")`, `\|@("id", "mode")` | in a line | cross reference | — |
| `\|<` … `\|<<<<<<`, `\|<(level=N)` | line start | heading; the level equals the number of `<` or `level=N` with a single `<` (1–6) | — |
| `\|>`, `\|>>` … | line start | clause; the level equals the number of `>` | `clause` (`\|end>`) |
| `\|-`, `\|#`, `\|--`, `\|#-` … | line start | list item; the length is the level, the last character is the type (`-` bullet, `#` number) | — |
| `\|!("kind")` | line start | admonition or note | `admonition` (`\|end!`) |
| `\|:` | line start, in a table | table row | — |
| `\|&` | in a table row | cell | — |
| `\|=(expression)` | in a cell | deferred cell formula | — |

Reserved for future versions: `|$`, `|[`, `|]` and any other `P*`/`S*` characters not listed in the table. `|>`, `|-`, `|#` have no `level` argument: the level equals the number of repetitions of the character.

Inline short forms are written to ODT as named character styles, not as direct formatting. The names are given by the `structure_styles` keys `strong`, `emphasis`, `underline`, `superscript`, `subscript`, `code`, `strike`, `placeholder` (section 11.5); by default they are the names in the table. If the style is missing, it is an error at the first use of the form.

A style name after `|.` and in `|end.` is a Unicode identifier (section 3.9) in which a hyphen is allowed (`Body-bl`, `Основний-текст`, `Body-before-l-after-s`). A style name is always followed by `{`, `:` or `(`, so there is no ambiguity.

### 3.4. Boundaries of line forms

A line form (a clause, a list item, a table row, a line body of a command) ends at the end of the source line. There is no other mode: the `para` mode of version 1.0 has been removed.

- The key `lines` in the `primula:` header is not allowed: error "line mode removed, a line form ends at the end of the line".
- A heading `|<` ends at the end of the line.
- A line that contains only a comment is removed before the boundaries are determined and does not interrupt the form.
- An ordinary line right after a line command starts a new paragraph; the linter warns about this case (a long clause may have been wrapped by hand). A multi-line clause is written as an environment (section 3.5).

### 3.5. Environments and closing

A fragment of several paragraphs is written as an environment — a form with `:` at the end of the line:

```
|>(id="delivery"):
Перший абзац пункту.

Другий абзац.
|- Матеріали.
|end>
```

A closing marker always takes the whole line.

| Notation | Closes |
| --- | --- |
| `\|end` | the nearest environment, unchecked |
| `\|end>`, `\|end>>`, `\|end.Ім'я`, `\|end!` | an environment of a short form, checked |
| `\|endif`, `\|endfor`, `\|enddef` | a control construct, checked |
| `\|end name` | any named environment, including a user one, checked |

- Short forms have canonical names: `|end>` = `|end clause`, `|end!` = `|end admonition`, `|end.Ім'я` = `|end style`. `|end clause` closes the nearest clause of any level; `|end>`, `|end>>`… close a clause of the corresponding level, checked.
- `|end` and `|end name` do not close the control constructs `|if`, `|for`, `|def`: only `|endif`, `|endfor`, `|enddef` close them. If the nearest open construct is a control construct, an anonymous `|end` is an error with a hint, not the closing of an outer environment. A `|code:` block is closed only by the line `|end`.
- Gluing `end` to an arbitrary name is forbidden: `|endnote` may be a call of the endnote command, not the closing of `note`.
- The linter warns when an environment longer than 30 lines (from the opening line to the closing line inclusive) is closed by an anonymous `|end`. The threshold is set in the project.
- After the arguments of a line command, after the `:` that opens an environment and after a closing marker (including `|endif`, `|endfor`, `|enddef`, `|else:`), spaces and a comment `|% …` are allowed. The exception is the end marker of `|verbatim`: it is compared with the line literally.

### 3.6. Implicit clause scope

A `|>` line implicitly opens a clause scope; the environment `|>:` … `|end>` is the same scope closed explicitly; both forms give the same result. The same rule applies to admonitions `|!`; it does not apply to paragraph styles `|.Ім'я:`.

The implicit scope includes all blocks after the clause line except those that close it: lists (`|-`, `|#`, including with the `|list` command or in the `|list:` environment; a blank line between list items ends one list and starts the next, both stay in the clause), nested clauses `|>>`, tables, figures, admonitions `|!`, line commands, code blocks, comments and blank lines.

The implicit scope is closed by:

- an ordinary paragraph and a paragraph with the style `|.Ім'я:` (a clause of several paragraphs is written as an environment);
- the next clause of the same or a higher level (`|>` after `|>>` closes both scopes);
- a heading `|<`;
- the structural and page commands `|page`, `|newpage`, `|section`, `|appendix`, `|scope`, `|document`, `|toc`, `|list_of`, `|header`, `|footer`;
- an environment `|if(…):` or `|for(…):` whose top level contains a heading or a clause of the same or a higher level; otherwise the environment belongs to the scope as a whole;
- the end of the enclosing environment or of the file.

`|include` is transparent for a scope: the content of the fragment is treated as if it stood in place of `|include`, and a block of the fragment that closes the scope closes it at that place. This is why the path, `part` and `key` of `|include` must be known when the tree is built (section 10.2).

Blank lines do not close a scope.

Admonitions `|!` have no level. A `|!` scope is closed by all blocks that close a clause scope, and also by any clause `|>`, `|>>`…, the next `|!` block and `|if`/`|for` environments with a heading or any clause at the top level. Lists, tables and figures after a `|!` line belong to its scope. A `|!` scope opened inside a clause scope is closed by a clause of any level; a deeper clause after it then goes into the scope of the outer clause.

```
|>(id="docs") Постачальник передає документи:
|- накладну;
|- сертифікат.

Інші документи передаються на запит.

|> Наступний пункт.
```

Here "Інші документи…" is free text between clauses. To include it in the clause `docs`, the environment `|>(id="docs"):` … `|end>` is needed. The formatter converts the implicit form into the explicit one and back (`primula fmt --explicit-clauses`); Studio shows the scope boundaries in the structure tree.

### 3.7. Code, comments, verbatim blocks

- Line comment: `|%` to the end of the line.
- Block comment: `|comment:` … `|end`. Inside, only the balance of environments is checked; unknown commands and variables are not checked.
- Verbatim block: `|verbatim:` … `|end`. If the text contains `|end`, its own marker is set: `|verbatim(end="EOF"):` … `EOF`.
- The indentation of the line that opens the block is removed from the lines of `|code:` and `|verbatim:` blocks — the same prefix character for character. A non-blank line with a smaller or different indentation (for example, a tab instead of spaces) is an error. Python indentation inside code is kept relative to the opening line. Positions in diagnostics refer to the source file.
- Code block: `|code:` … `|end`. Inside, `|` is not markup; the block ends only at a line consisting of `|end`.

### 3.8. Processing phases

1. Lexical pass: header, normalization, comments, verbatim blocks, code blocks, balance of brackets and environments.
2. Building the document tree.
3. Collecting definitions in the whole project, including included files.
4. Evaluation (command arguments and expressions are evaluated here, section 3.2), selection of variants, numbering, table formulas, ODT generation.

All phases keep the file, line and column for diagnostics, including through inclusions and macros.

### 3.9. Identifiers and names

Names entered by the author are Unicode identifiers per UAX #31: the first character is `XID_Start`, the others `XID_Continue` (including `_`). The Unicode version (15.1) is fixed by the language version (section 0.1).

- Scope of application: variables, parameters, functions, macros (`|def`), record fields and data keys (CSV, YAML, including user header keys), module names (from file names), scopes (`scope`), dictionary keys, `id=` values, style names, `col(id=…)`.
- Style names additionally allow a hyphen; `id=` values allow a hyphen and a dot (section 5.6).
- ASCII only: built-in commands, predefined header keys (`kind`, `doc`, `params`, …), core keywords, names of standard library functions.
- Names are compared in the normalization form NFKC; case is significant. Record and data keys are normalized to NFKC when loaded; two keys that coincide after normalization are an error.
- The linter warns about an identifier that mixes alphabets (Latin and Cyrillic) and about a pair of identifiers that differ only in homoglyphs (Cyrillic "а" and Latin "a").
- A command name ends at the first character not in `XID_Continue`; text glued to it is separated with `|;` (section 3.2).

## 4. Text markup

### 4.1. Paragraphs

- A blank line separates paragraphs — this is the only implicit rule.
- A single line break inside a paragraph gives a space; indentation at the start of a line has no meaning.
- A line break inside a paragraph is `|\`; a non-breaking space is `|~`. A source line break right after `|\` does not give a space: `|\` inserts only the line break.

### 4.2. Inline forms

```
Постачальник передає |*{Товар} у кількості |(qty)|~шт.
Позначення: U|,{ном}, площа 2|~м|^{2}.
Надалі — |.DefinedTerm{«Товар»}.
Адреса доставки: |?{УТОЧНИТИ}.
Модель |`{X300-EU}.
```

- `|"{…}` puts quotation marks of the document language: for uk and ru «…», inside „…“; for en “…”, inside ‘…’. The nesting level is counted by nested `|"{…}`; the third level repeats the first. Quotation marks of other languages are set in a styles module: `quotes("de", ("„", "“"), ("‚", "‘"))`.
- `|?{…}` is a draft placeholder: each placeholder left in gives a warning, with `--strict` an error. The styles module setting `placeholders("final")` (default `"mark"`) outputs the content of placeholders as ordinary text, without the placeholder style and without warnings: one form gives both a template (in a contract, with highlighted fields) and a filled-in document (in an order project, section 10.6).
- `|link("https://…"){text}` is an external hyperlink (ODF `text:a`); without a body the link text is the address itself: `|link("https://consense.com.ua/doc/CA102-26-1.pdf")`. The address is one string (a core expression); the character style is `structure_styles(link=…)`, by default the reference style `reference`. Links to targets inside the document are `|@` (section 5.7).
- The value of an expression `|(…)` is inserted as text and is not parsed again as markup. Only the explicit function `markup(…)` turns a string into markup.
- A value is converted to text by the rules of the core `str()`: numbers with a dot, `datetime` in ISO format (a date without time if the time is 00:00:00), a length with its unit. Local formatting is done by library functions (`num`, `money`, `fmt_date`, `fmt_datetime`, section 13). `content` is inserted as markup. `None`, `bool`, a list, tuple, dictionary, record and function in `|(…)` are an error with a hint (`|(x or "")`, `join_list(…)`, an explicit `str(…)`).
- The linter warns when a `decimal` with a fractional part (scale greater than zero), a `float`, `datetime` or `length` is inserted into text without a formatting function: in a Ukrainian document `|(qty)` gives "2.20" with a dot. Integral `decimal` values (scale 0) are not checked: years, numbers and codes must not give false alarms.

### 4.3. Applying styles

`|.` is followed either by a style name or by `(expression)`:

```
|.DefinedTerm{«Товар»}
|.Note: Примітка в одному рядку.
|.Note:
Перший абзац.

Другий абзац.
|end.Note
|.("Clause" if level == 1 else "ClauseContinuation"):
…
|end style
```

- The kind of style is determined by the form: `{…}` is a character style, `:` a paragraph style; the build checks that the style matches the form.
- The expression returns a style name — a string. The functions `derive(...)` and `Indented(...)` return a deterministic style name and register the name; the style is written to ODT at its first use: `|.(Indented("Clause", 2)):`.
- Parameters in place: `|.Body(before="l", after="s"):`, `|.Clause(indent=2): Текст` (section 11.4).
- A static name is checked by the editor and LSP while typing, a computed one only at build time; an unknown style is an error with the position of the expression.
- With a computed style the environment is closed by `|end` or `|end style`.

A block style (a group of elements: spacing at the group boundaries, keeping on one page) is applied by the environment `|block("Ім'я"):` … `|end block` or by the argument `block="Ім'я"` in `|>`, `|!`, `|table`, `|figure`, `|appendix`.

### 4.4. Direct formatting

`|fmt(color="#C00000", bold=True){…}` is direct formatting of a fragment. It is allowed with a warning: a change of the style in Writer no longer affects such text. Character styles are recommended.

### 4.5. Context defaults: set

`|set(…)` sets which styles format the constructs up to the end of the enclosing environment; at the top level up to the next `|set` with the same key or to the end of the document. Style definitions do not change; an explicit style in the text takes precedence.

```
|appendix(title="Специфікація"):
|set(paragraph="Note", list="DashList", table="TableCompact")
…текст додатка без окремих позначок…
|end appendix
```

The keys are the names of constructs from `structure_styles` (section 11.5).

- The values of `|set` are as in `structure_styles`: a style name (a string), and for `heading` and `clause` also a dictionary "level → style"; one name for `heading` or `clause` applies to all levels. An unknown key is an error.
- The bodies of `|if`, `|for`, `|def` do not create a scope for `|set`. The scope is the nearest enclosing structural environment (`|>:`, `|!:`, `|.Ім'я:`, `|appendix:`, `|block:`, `|list:`, a table cell and so on) or the document.
- `|set(list=None)` restores the value from `structure_styles` up to the end of the scope.
- `|set` in a fragment of `|include` applies up to the end of the fragment: an inclusion is transparent for clause scopes but not for `|set`.

## 5. Document structure

### 5.1. Structure profiles

There are no common rules for numbering appendices and captions for all documents, so the language does not fix a standard. The default is set by the structure profile in a styles module: `structure_profile("business")`.

| Profile | Reference | Appendices | Captions |
| --- | --- | --- | --- |
| `business` | DSTU 4163:2020 (organizational and administrative documents) | by numbers: «Додаток 1» | if needed, the format as in `report` |
| `report` | DSTU 3008:2015 (reports, technical documentation) | by letters: А, Б, В, Г, Д, Е, Ж, К, Л… (without Ґ, Є, З, І, Ї, Й, О, Ч, Ь) | «Рисунок 1.1 — …» below a figure, «Таблиця 1.1 — …» above a table |

The business styles set uses `business`, the technical one `report`. Any profile parameter is overridden by the functions `numbering`, `captions`, `ref_labels`, `footnotes`.

- In the `business` profile figures and tables are numbered throughout the document (`numbering(figures="document", tables="document")`), in `report` by chapter (`"by_chapter"`); without numbered headings `by_chapter` acts as `document`. In an appendix the counters restart with a prefix: «Таблиця А.1» (both profiles).
- The designation of appendices is set by the function `appendices(designation=…, numbering=…, letters=…, page_break=True, toc="{designation} {title}", title_format=None)`. Without `title_format` the designation and the title of an appendix are two paragraphs (styles `AppendixDesignation`, `AppendixTitle`); with `title_format="{designation} {title}"` they are one paragraph of the style `AppendixTitle` («ДОДАТОК 1. Форма Замовлення»), for example to save space when the appendix is a form template. Profile values: `business` — `designation="Додаток {n}"`, `numbering="numbers"`; `report` — `designation="ДОДАТОК {n}"`, `numbering="letters"`, `letters="АБВГДЕЖКЛМНПРСТУФХЦШЩЮЯ"`.
- `captions`, `appendices` and `ref_labels` take the language as the first argument: `captions("ru", table={"format": "Таблица {n} — {title}"})`; a call without a language sets the format for all languages. The built-in module contains settings for uk, ru, en.

### 5.2. Headings and their numbering

```python
numbering(headings=True, heading_format="{n}.", clause_format="{n}.")
```

- `|<` … `|<<<<<<` are headings of levels 1–6 with a real Writer outline level. The level is given either by the number of `<` or by the argument `level=` with a single `<` (`|<(level=4) Назва`); both at once (`|<<(level=4)`) is an error. `level=` is a core expression evaluated in the evaluation phase (section 3.2); a value outside 1–6 is an error. Combining `level=` with several `<` is detected by the presence of the key and is a syntax error. `|>`, `|-`, `|#` have no such argument.
- Headings are numbered by default; a document may override this in its file header: `structure: {numbering: {headings: false}}`.
- A single heading: `|<(number=False) Довідка`. An unnumbered heading does not advance the counters.
- Skipping a level in a numbered zone is an error.
- The linter warns when the text of a numbered heading starts with a number (probably a number typed by hand).
- `style="Name"` is the paragraph style of this heading instead of the level style from `structure_styles` (the outline level and the numbering do not change).
- Heading arguments: `id`, `number`, `level`, `toc`, `toc_title`, `style`, `when`.

- `{n}` in numbering formats is the compound number with the scope prefix: «1.2», «А.1.2». The format is given for all levels by one string or by a dictionary of levels: `heading_format={1: "{n}.", 2: "{n}"}`.
- One space is put after the formatted number unless the format ends with a space or a tab; a tab (`"{n}.\t"`) aligns the text at the hanging indent of the paragraph.
- The number is ordinary paragraph text, not a Writer field; it is not part of `|@(id, "title")`. The character style of the number (together with the space or tab after it) is set by `structure_styles(clause_number=…)` for clauses and `heading_number=…` for headings; by default the number is formatted as the paragraph text.

### 5.3. Clauses

- `|>` is numbered relative to the last numbered heading of any level in its scope: under «2» — 2.1, 2.2; under «2.1» — 2.1.1, 2.1.2 (section → subsection → clause → subclause, as in DSTU 3008:2015); `|>>` adds a level. Without a numbered heading clauses are numbered from the root: 1, 2, 3. If the clauses of a section are followed by its subsection and the numbers may coincide (clause 2.1 and subsection 2.1), a warning is given.
- A clause starts as an ordinary paragraph; the number is added to the first paragraph. Headings inside a clause are forbidden.
- Continuing a clause after intermediate text: `|>(continues="services")` — the number is kept, the subclause counter continues. The target of the continuation is a clause of the same section, scope and level.
- `style="Name"` is the paragraph style of this clause (the paragraph with the number and the continuation paragraphs in an environment) instead of the level style from `structure_styles`: `|>(id="writing", style="ClauseChanged") …`.
- Clause arguments: `id`, `continues`, `block`, `style`, `when`. The name `continue` is impossible: it is a Python keyword, and command arguments are parsed as the arguments of a Python call.

### 5.4. Lists

- `|-` is a bulleted item, `|#` a numbered one; the length of the sequence is the level, the last character the type: `|#-` is a bulleted item of the second level under a numbered one.
- The prefix characters of the marker must match the types of the parent items. Mixing bulleted and numbered items at one level of one list and skipping a level (including a list that starts at the second level) are errors; for mixing, with a hint to separate the lists with a blank line.
- The list style comes from `structure_styles` or `|set(list=…)` (for all lists of the environment).
- The style of a single list is the command `|list("LetterList")` on the line before the first item. It applies to the nearest list and ends with it: at a blank line between items, at an ordinary paragraph, at the end of the clause scope. A list with blank lines or continuation paragraphs of items is written as the environment `|list("LetterList"):` … `|end list`.
- The type of an item is given by the marker (`#` number, `-` bullet), the style gives the formatting of the levels. If the type of a level in the style does not match the marker, the translator materializes a derived variant of the style.
- In a `|list(…):` environment blank lines do not split the list. A paragraph or another block (a table, `|!`, `|img` and so on) belongs to the last item of the top level of the environment — the level of its first item. To continue a nested item, a nested `|list:` environment is used (without an argument the style is inherited); its top level is the level of its first item. A heading and a clause `|>` in a list environment are errors.
- The `|list` command exists only in markup; in code `list` is a built-in function of the core.
- A named sequence: `|#(id="stages", start=3)`; continuation after intermediate text: `|#(continues="stages")`. `start` and `continues` together are an error. List names form a separate registry and do not overlap with reference IDs.
- Letter numbering that skips letters: the level property `letters="абвгдежиклмнп…"` — the allowed letters in order (section 11.3). Writer does not skip letters, so the number of such a level is written as text (the label, then a tab to the text position), and the level of the list style in ODT stays without automatic numbering; when the list is edited in Writer the numbers are not recalculated. The letter case follows `format` (`А` is uppercase). The `report` profile for uk gives levels with `format: а`/`А` the letters without `ґ`, `є`, `з`, `і`, `ї`, `й`, `о`, `ч`, `ь` (DSTU 3008:2015; the set is to be checked against the text of the standard); the `business` profile the full Writer alphabet. An item for which there are not enough letters is an error. Counting starts at `start` (of the level or `|#(start=…)`); a continuation `continues=` is not taken into account for letters.

### 5.5. Numbering scopes and appendices

A scope with independent counters:

```
|scope("app-a", prefix="А"):
…
|end scope
```

The semantic construct of an appendix is built on top of a scope:

```
|appendix(id="app-spec", title="Специфікація робіт"):
|< Склад робіт
|> Перелік…
|end appendix
```

- It starts a new page (the page style is the parameter `page=`).
- It outputs the designation and the title: «ДОДАТОК 1» (`business`) or «ДОДАТОК А» (`report`).
- It opens a scope with a prefix: headings 1.1 or А.1, clauses 1.1.1 or А.1.1, figures «Рисунок А.1».
- The number or letter is assigned automatically; an explicit value is `number=3` or `letter="Б"`.
- After closing, the counters of the main scope are restored. Scope names are unique; the name `document` is reserved.
- The tracks of `|parallel` are each numbered with their own set of counters taken on entering the environment; after leaving it, the numbering continues from the primary track (section 7.7).

- The argument `|appendix(subtitle="…")` is a line between the designation and the title: «(обов'язковий)», «до Договору № 12 від 01.10.2026»; values are substituted by an expression in the argument (`subtitle=f"до Договору № {doc.identifier}"`).
- In the table of contents an appendix is one level-1 entry in the `toc` format of the function `appendices` («Додаток А Назва»); headings inside the appendix are entries of levels 2 and below with numbers «А.1». The arguments `toc=False`, `toc_title=`, `toc_level=` change this entry (section 5.9); the designation of the appendix (or the single paragraph of `title_format`) is a heading of the document outline: the Writer navigator, PDF bookmarks.

### 5.6. IDs

- An ID is given by the argument `id=` of a heading, clause, figure, table, appendix, footnote, section, admonition.
- Format: a Unicode identifier (section 3.9) with the additional characters `-` and `.` after the first one: `delivery`, `розділ-1`, `fig-scheme`. Comparison is by NFKC, case is significant. The character `:` separates a part of a compound document from the ID: `act1:items`.
- IDs are unique in the document, including included fragments; a duplicate is an error with the positions of both definitions.
- A fragment with IDs included twice without `ns=` is an error with the positions of both inclusions. With `ns="wa"` all IDs of the fragment get the prefix `wa.` (`wa.warranty`); references inside the fragment to its own IDs are resolved first with the prefix, then without it. A computed ID (`id=f"{prefix}-warranty"`) is allowed too.
- The ID of a block inside a `|parallel` track gets the track prefix: `uk.services`, `en.services` (section 7.7).
- An ID does not change when items are reordered and renumbered.

### 5.7. Cross references

| Notation | Result |
| --- | --- |
| `\|@("pay")` | the number: «1.2» |
| `\|@("pay", "label")` | the number with a label: «п. 1.2», «розд. 2», «рис. 3», «табл. 1», «дод. А» |
| `\|@("pay", "title")` | the title of a heading, figure, table, or the text of the first paragraph of a clause |
| `\|@("pay", "page")` | the page number — a Writer field (`text:bookmark-ref`), updated by Writer |

- The number, label and title are computed at build time and written as text with a hyperlink to a bookmark.
- A reference may stand before its target and in another included file. An unknown target, an unsuitable mode (a number for an unnumbered target), a reference to a target removed by a condition are errors.
- Labels are abbreviated by default and not inflected. The full form takes a case: `|@("sec", "label", case="loc")` → «розділі 2». Cases: `nom`, `gen`, `dat`, `acc`, `ins`, `loc`.
- The label dictionary is in the styles module, per document language:

```python
ref_labels("uk",
    section={"short": "розд.", "nom": "розділ", "gen": "розділу", "loc": "розділі"},
    clause={"short": "п.", "nom": "пункт", "gen": "пункту", "loc": "пункті"})
```

- Label keys: `section` (a level-1 heading), `subsection` (level 2 and below), `clause` (`|>`), `subclause` (`|>>` and deeper), `appendix`, `figure`, `table`; forms: `short`, `nom`, `gen`, `dat`, `acc`, `ins`, `loc`. A missing case is an error with the position of the reference. The built-in module contains dictionaries for uk, ru, en (en only `short` and `nom`).
- The label and the number are separated by a non-breaking space (U+00A0): «п. 1.2» is not broken between lines.
- If there is no dictionary for the document language, the `label` mode is an error at its first use; the number, `title` and `page` modes work.
- `|@(id)` outputs `{n}` without the numbering format: «1.2»; the reference format is set by `numbering(ref_format="{n}")`.
- `|@(…)` has no body: braces placed right after `)` do not belong to the reference and are output as text (`|@("a"){text}` gives «1{text}»); the translator warns (P1245, decision 141). Braces after a space are ordinary text without a warning. The text of a reference, if needed, is given by `|link(…){text}` (an external address) or by the mode `"title"`.
- Inside a `|parallel` track a short ID is looked up in that track, then in the primary one, then among the document IDs; the label is in the language of the track (section 7.7).
- A target removed by a condition is recognized by the literal `id="…"` of the removed block (`when=` or an `|if` branch): error "target removed by a condition" with a note about the condition; a reference to a computed ID of a removed block is "unknown target". In `--review` mode removed blocks stay in the document, and a reference to them is resolved with a warning.

References to another document of the project. A document that declares `references: [contract]` in its header may refer to targets of the project documents with these names (`ref_documents`, section 10.6): an ID missing in the document itself is looked up in them. A typical case is a form that is part of a contract as an appendix and is also built as a separate document: in the contract `|@("acceptance", "label")` is an internal reference, in the separate form it is «п. 2.5» from the contract.

- The reference text is taken from the reference registry of the document (the file `*.refs.json`: targets — kind, number, label key, title — and the SHA-256 of the files it was built from). If the registry is missing or outdated (files changed, another translator version) and the source is available, the translator computes the structure of that document without writing ODT and updates the registry (on `build`; `check` writes no files). If there is no source, the registry is used as it is (the published edition); if the source is named but not found, with a warning.
- The label and the number format follow the settings of the referring document (language, `ref_format`).
- A reference to another document is text without a hyperlink; the `page` mode is an error; a target found in several documents of `references` is an error; an unknown name in `references` and a document that could not be computed are errors.
- The build report lists such references and the origin of their text (`computed` or `registry`).

### 5.8. Figures and tables: numbering and captions

- The `figure` and `table` counters obey scopes; numbering by chapter: `numbering(figures="by_chapter", tables="by_chapter")` → «Рисунок 2.3».
- The format and position of captions are set by the profile and the function `captions`:

```python
captions(
    figure={"format": "Рисунок {n} — {title}", "position": "below"},
    table={"format": "Таблиця {n} — {title}", "position": "above"},
)
```

- The caption of a figure is the body of `|figure:` (section 8). The caption of a table is the parameter `|table(caption="…", id=…)` or the environment `|caption:` inside the table for a caption with markup.
- A caption is not separated from its figure or table.

### 5.9. Table of contents and lists

```
|toc(max_level=3, title="ЗМІСТ")
|list_of("figure", title="ПЕРЕЛІК РИСУНКІВ")
|list_of("table", title="ПЕРЕЛІК ТАБЛИЦЬ")
|list_of("abbr", title="ПЕРЕЛІК СКОРОЧЕНЬ")
|list_of("index", title="ПОКАЖЧИК")
```

- The translator writes the table of contents, the lists of figures and tables and the alphabetical index as updatable Writer indexes with a visible list of entries; Writer updates the page numbers. The list of abbreviations (`abbr`) is a table computed at build time (section 9.4).
- Indexes are built from marks (`text:toc-mark`, marks of a user index), not from outline levels. The content of the table of contents is controlled explicitly:
  - `|<(toc=False)` excludes a heading; `|<(toc=True)` includes it even if it is deeper than `max_level`; `|<(toc_title="Коротка назва")` gives another entry text; `|<(toc_level=2)` gives the level of the entry regardless of the heading level (1–10);
  - the same `toc`, `toc_title`, `toc_level` exist for `|appendix` (by default a level-1 entry in the format `appendices(toc=…)`) and for a clause `|>`: a clause goes into the table of contents only with `toc=True`, `toc_title=` or `toc_level=` (the text is the number and the first paragraph of the clause or `toc_title`; the level is the section level plus the clause level);
  - `|toc_entry("Текст", level=1)` on its own line is a table of contents entry with a bookmark at the start of the next paragraph: for something that is not a heading (a formatted paragraph, a section of a form).
- Entries included explicitly (`toc=True`, `|toc_entry`) are output regardless of `max_level`.
- The document navigation (the Writer navigator, PDF bookmarks) is built from the outline headings: `|<` headings and appendices (`|appendix` — the paragraph with the designation or the single paragraph of `title_format`; the level is `toc_level`, by default 1). `|toc_entry` entries and clauses are not part of the navigation.
- Clauses `|>` do not go into the table of contents.
- The argument `track=` of `|toc` and `|list_of` gives a list with the blocks of the given `|parallel` track instead of the primary one (section 7.7); headings of non-primary tracks are not part of the document navigation.
- The parameter `page_break` (by default from the style) starts the table of contents on a new page.

### 5.10. Footnotes

- `|footnote{text}` is a footnote at the bottom of the page, `|endnote{text}` an endnote. The body is inline markup.
- `|footnote(id="fn-vat"){…}` is a reference target; `|@("fn-vat")` outputs the footnote number.
- Settings in the styles module: `footnotes(numbering="document", restart="none", format="1", separator="0.5pt solid")`; `restart`: `"none"`, `"page"`, `"chapter"`.

- `|@("fn-vat")` is written as the Writer field `text:note-ref` (Writer updates the number) with the value computed at build time for `restart="none"`; `|@("fn-vat", "page")` is the page of the footnote; the modes `label` and `title` for footnotes and `|!` notes are an error "unsuitable mode".
- Footnotes in non-primary `|parallel` tracks are numbered by the track counter with an explicit label (section 7.7).
- `numbering="document"` is the only value in version 1.1; `format` is an ODF number format (`1`, `i`, `I`, `a`, `A`) or `"*"` (symbols).

## 6. Tables

### 6.1. Capabilities

The syntax expresses only what ODF can do natively:

- columns: absolute or relative width, column style;
- rows: minimum or exact height, no breaking of a row, header rows repeated on every page;
- cells: horizontal and vertical spans, borders of each side, padding, background, vertical alignment, any block content (including nested tables), a typed value;
- table: width, alignment, permission to break between pages.

### 6.2. Table

A table is the environment `|table(…):` … `|end table`.

| Parameter | Meaning | Default |
| --- | --- | --- |
| `cols` | list of columns (section 6.3) | equal columns by the number of cells of the first row |
| `style` | a named or parametric table style | from `structure_styles` |
| `width` | table width: `"100%"`, `"150mm"`; percentages are of the width of the text area, inside `\|section(cols=…)` of the column width (section 7.5) | `"100%"` |
| `align` | position of the table: `left`, `center`, `right` | `left` |
| `header` | number of header rows; `0` is a table without a header | `1` |
| `footer` | number of closing rows (totals); not part of `body_rows()` | `0` |
| `repeat_header` | repeat the header on every page | `True` |
| `keep_rows` | do not break a row between pages | `True` |
| `may_break` | allow the table to break between pages | `True` |
| `frame`, `rules` | outer frame and inner lines (section 6.7) | from the style |
| `caption`, `id` | caption, automatic numbering, reference target | none |
| `block`, `when` | block style, inclusion condition | none |
| `data`, `fields`, `titles` | rows from data (section 6.9) | none |

Inside the environment only rows (`|:`, `|row:`), `|caption:` environments, control constructs (`|for`, `|if`), code blocks, `|include`, comments and blank lines are allowed. Ordinary text outside a row is an error. Blocks inserted by `|include` obey the same restrictions. In the body of `|row:` the command `|include` inserts cells. `|let` and `|set` in the body of a table or a row are errors (instead of `|let`, a `|code:` block).

### 6.3. Columns

`cols` is a list; an element is a string with a width or a `col(…)` object.

| Notation | Width |
| --- | --- |
| `"40mm"` | fixed |
| `"30%"` | share of the table width |
| `"*"`, `"2*"` | the remainder, divided in proportion to the weight |
| `"auto"` | by content, unlimited |
| `"20mm..60mm"` | by content, within limits |
| `"20mm.."` / `"..60mm"` | only the lower / only the upper limit |
| `"10%..25%"`, `"15mm..30%"` | limits as shares of the table; mixing units is allowed |

A column object: `col(width, id=…, align=…, valign=…, type=…, currency=…, digits=…, paragraph=…, …)`. The notations `col("20mm..60mm")` and `col("auto", min="20mm", max="60mm")` are equivalent. `id` is used in formulas.

Width calculation:

1. Fixed and percentage columns get their width.
2. For each `auto` column a minimum width (the longest unbreakable word) and a desired width (the longest line without wrapping) are computed, plus the cell padding. Images give an exact width, nested tables are computed recursively. Spanned cells do not take part in the calculation in version 1.1.
3. An `auto` column gets its desired width limited by its range if everything fits; otherwise its minimum width, and the remainder is divided in proportion to the difference between the desired and the minimum width.
4. `*` columns take the remainder.
5. If there are no `*` columns and space is left, the upper limits are not violated: the table becomes narrower than the given width and is aligned by `align`.
6. If the sum of the lower limits exceeds the available width, a warning with the column numbers is given, and the columns are narrowed proportionally below their minimum.

Character widths are taken from font files (fontTools); the same fonts as in Writer are needed. If a font is not found, an approximate calculation by the average character width is used with a warning. The computed fixed widths are written to ODT; they go into the build report.

### 6.4. Rows and cells

Compact form:

```
|: Робота / послуга |& Кількість |& Ціна |& Сума
|:(keep=True) Тестування |&(align="right") 2 |& 200,00 |& 400,00
```

- `|:` at the start of a line opens a table row; `|&` separates cells.
- The arguments of `|:(…)` belong to the row, those of `|&(…)` to the cell that follows it.
- Arguments of the first cell: `|:|&(span=3) Разом` — `|&` right after `|:` (or after the row arguments), without a space, belongs to the first cell. With a space, `|: |& Б`, the row starts with an empty cell.
- An empty cell is `|&` without content.
- A table row ends at the end of the source line (section 3.4).
- A cell can be given by a body spanning several lines: `|& |cell(span=2){…}`.

Expanded form:

```
|row:
|cell(rows=2, valign="top"):
Перший абзац.

|- пункт списку;
|- ще пункт.
|end cell
|cell: Короткий текст
|end row
```

A cell in the expanded form may contain paragraphs, lists, clauses, images and nested tables. Compact and expanded rows can be mixed in one table.

### 6.5. Spans

- `span=N` is a horizontal span, `rows=N` a vertical one.
- Positions covered by a span are skipped automatically: such cells are not written in the following rows.
- At build time the number of cells of each row is checked against the number of columns taking spans into account; the error names the row and the expected number of cells. Both fewer and more cells are an error; an empty cell is written explicitly — `|&` without content.

### 6.6. Formatting cascade

Order of application: table style → column → row → cell; each level refines the previous one. Cells of header and footer rows additionally get the properties `header_*` and `footer_*` from the table style.

| Property | Purpose |
| --- | --- |
| `align`, `valign` | horizontal and vertical alignment of the content |
| `padding` | cell padding |
| `background` | background |
| `paragraph` | paragraph style of the content |
| `height`, `min_height` | row height (row only) |
| `keep` | do not break the row (row only) |
| `border`, `border_top`, `border_bottom`, `border_left`, `border_right` | borders |

### 6.7. Borders

- At the table level: `frame` is the outer frame, `rules` the inner lines (`"all"`, `"rows"`, `"cols"`, `"none"`).
- At the column, row and cell levels: `border` and the sides `border_top` … `border_right`. The value is a string like `"0.5pt solid #000000"` or `"none"`; line types: `solid`, `dashed`, `dotted`, `double`.
- The translator distributes the result over the sides of each ODF cell. On the shared edge of two cells the more specific level wins; with equal levels, the cell that is lower or further right.

### 6.8. Values and formulas

- A literal in a cell is text. A cell gets a typed value if its content is an expression (`|(dec("300"))`) or its column declares a type: `type="decimal"`, `"money"`, `"datetime"`. With a declared type the cell text is parsed by the document locale; a parse error is a build error with the position of the cell.
- `type="money"` is a `decimal` value, output with `num(x, 2)`; the currency symbol is the column parameter `currency=`.
- `|=(expression)` is a deferred cell formula: it is evaluated after all ordinary cells of the table are known. It is allowed only in a table cell.
- Formulas are evaluated lazily, with the result remembered: if a formula refers to a cell with a formula, that one is evaluated first; each formula is evaluated exactly once; referring again to a cell being evaluated is a cycle, an error with the chain of cells.
- Dependencies are found during evaluation, not from the formula text, because references may be computed. There is no iterative recalculation until values stabilize.
- Formula functions (row and column numbers start at 1; a column may be given by its `id`):

| Function | Meaning |
| --- | --- |
| `this_row(c)` | the value in column `c` of the current row |
| `cell(r, c)` | the value of a cell |
| `column(c, rows=…)` | list of the values of a column |
| `body_rows()` | the rows between the header and the totals |
| `sum`, `min`, `max`, `avg`, `count` | aggregates |

- The computed text and the value type of the cell are written to ODT. A Writer formula is added only with the explicit table parameter `live=True`.

Allowed notations in a typed column (by document language):

| Type | uk, ru | en |
| --- | --- | --- |
| `decimal`, `money` | `1234`, `1 234`, `1 234,56` (groups: space, U+00A0, U+202F), and also the canonical form `1234.56` without groups | `1234`, `1,234`, `1,234.56`, `1234.56` |
| `datetime` | `12.10.2026`, `12.10.2026 14:30`, ISO `2026-10-12`, `2026-10-12T14:30[:00]` | ISO only (the notation `10/12/2026` is ambiguous) |

The minus when parsing is `-` or `−` (U+2212); on output it is always `−` (standard library, section 2), in `str()` and in ODF values the ASCII `-`. An empty cell is `None`, not an error.

Output of values:

- In a typed column any value — literal, expression, formula — is output by the column type: `decimal` — `num(x)` with the number of digits of the value or the column's `digits=` (an integral value without a fractional part); `money` — `num(x, 2)` and the currency symbol; `datetime` — `fmt_date(x, "short")` if the time is 00:00:00, otherwise `fmt_datetime(x, "short")`. A literal is brought to the common form: «1500» in a `money` column → «1 500,00».
- `currency=` is a code from the currency dictionary of the library (`"UAH"` → «грн», standard library, section 3) or an arbitrary string («у.о.»); the symbol follows the number after a non-breaking space for all languages. Without `currency=` only the number is output.
- A cell has a value only if its content is exactly one expression `|(…)` or one formula `|=(…)` (ignoring spaces), or a literal in a typed column. A mixed cell («Разом: |=(…)») is a string; the formula in it is output by the formatting rules of its type.
- Outside a typed column a value is output by its own type: `decimal` — `num(x)`; `datetime` — as in a typed column; a string as it is. The warning about an unformatted value (section 4.2) is not given for a table cell.
- In ODT a cell with a value gets `office:value-type` (`float`, `currency`, `date`) and `office:value`; a cell without a value is `string`.

Formula functions:

- Rows are numbered throughout from 1, including header and footer rows; rows inserted by `|for` and `|include` in place. `body_rows()` is the list of row numbers between the header and the totals.
- `column(c)` without `rows=` gives the values of the rows `body_rows()`; `rows=` is a list of numbers or a `range`.
- An empty cell is `None`. A position covered by a span: for `cell()` and `this_row()` the value of the owner cell, in `column()` `None` (the sum is not doubled).
- `sum`, `min`, `max`, `avg` skip `None`; `sum([])` = 0; `avg`, `min`, `max` of an empty list are an error; `count` is the number of non-empty values. A string in an aggregate is a type error with the position of the cell.
- `this_row` and the other table functions outside a cell formula are an error.

With `live=True` the following are translated into Writer formulas: numeric constants, `+ - * /`, brackets, unary minus; `this_row(c)` and `cell(r, c)` become cell references (`<C2>`); `sum`, `min`, `max`, `avg`, `count` of `column(c)`, `column(c, rows=body_rows())`, `column(c, rows=range(a, b))` become ranges (`<D2:D5>`). A formula outside this list is an error with a hint to remove `live=True`. Both the formula (`table:formula="ooow:…"`) and the computed value are written to ODT.

### 6.9. Table from data

```
|table(cols=[col("*"), col("15mm..25mm", id="qty", type="decimal", align="right"), col("20mm..35mm", id="sum", type="money", align="right")], header=1, footer=1):
|: Найменування |& Кількість |& Сума
|for(it in items):
|: |(it.name) |& |(it.qty) |& |(it.qty * it.price)
|endfor
|:|&(span=2, align="right") Разом |& |=(sum(column("sum", rows=body_rows())))
|end table
```

`items` comes from a code block or from external data (section 10.5).

Rows from data without a loop — the arguments `data`, `fields`, `titles`:

```
|table(data=items, fields=["name", "qty", "sum"], titles=["Найменування", "Кількість", "Сума"], cols=[col("*"), col("20mm", type="decimal", align="right"), col("30mm", id="sum", type="money", align="right")], footer=1):
|:|&(span=2, align="right") Разом |& |=(sum(column("sum", rows=body_rows())))
|end table
```

- `data` is a list of records, dictionaries or lists; `fields` are the fields by column (by default all fields of the first record; for lists all elements of the first one); `titles` is the header row (by default the field names; for list data without `titles` there is no header row, and `header=0` is needed), one title per field.
- Cell values are field values: the column type formats them as it formats `|(…)` in a cell (section 6.8); a `content` value is inserted as markup.
- The rows of the environment body (totals, formulas `|=`) follow the data rows. The line form without a body is allowed: `|table(data=rows, header=0)`.
- A field missing in a record is an error with the number of the data row; `data` of another kind, `fields` not made of strings, `titles` of another length are argument errors.

## 7. Pages, sections, headers and footers

### 7.1. The ODF model

- Page layout: size, orientation, margins, columns across the whole page, background, border, space for headers and footers.
- Master page: refers to a layout, contains headers and footers (common, left and right, first page), may name the next master page.
- A change of the master page in the middle of the document is assigned to the first paragraph or table after the place of the change.
- Section (`text:section`): columns inside a page.
- ODF has no rotation of content: a landscape page is a landscape sheet, and its headers and footers run along the long side.

### 7.2. Page styles

Page styles are set by the `pages` group of the YAML header or by the function `page_style(…)` of a styles module (section 11). A document may define its own page styles and headers and footers in a code block — as the last layer on top of the project modules (section 11.7).

```python
page_style("Portrait", size="A4", margin=("20mm", "15mm", "15mm", "25mm"))
page_style("Landscape", parent="Portrait", orientation="landscape")
page_style("Appendix", parent="Portrait", number_format="1", restart=1)
```

| Parameter | Meaning |
| --- | --- |
| `parent` | the page style the properties are inherited from |
| `size` | `"A4"`, `"A5"`, `"A3"`, `"Letter"` or `(width, height)` |
| `orientation` | `"portrait"`, `"landscape"` |
| `margin` | `(top, right, bottom, left)`, as in CSS; or separately `margin_top` … `margin_left` |
| `cols`, `col_gap`, `col_rule` | columns across the whole page |
| `header_gap`, `header_min_height`, `footer_gap`, `footer_min_height` | space for headers and footers |
| `number_format` | page number format: `"1"`, `"i"`, `"I"`, `"a"`, `"A"` |
| `restart` | the number of the first page when switching to this style |
| `next` | the style of the next page |
| `background` | page background |
| `watermark` | watermark (section 8.6) |
| `mirror` | `True` — mirrored margins of even and odd pages (`style:page-usage="mirrored"`); only on such pages do `place="inside"`/`"outside"` make sense |

A document without an explicit page change uses the default page style: the key `page` in `structure_styles` (usually `Portrait`).

### 7.3. Changing the page

A switch: from this place to the next change the new style applies:

```
|page("Appendix")
|page("Appendix", restart=1, number_format="i")
```

An environment: after `|end page` the previous style is restored:

```
|page("Landscape"):
|table(…):
…
|end table
|end page
```

- `restart=` in `|page` is the number of the first page of this change (`style:page-number` of the first paragraph); in a page style it is the default for each change to this style. A `number_format=` in `|page` that differs from the format of the style creates a derived page style named by the rules of section 11.4 (`Appendix-number_format-i`), which applies until the next change.
- The translator assigns the master page to the first paragraph or table after the place of the change. If the command is not followed by content up to the end of the document or the environment, it is an error.
- A page change inside a clause, a table cell or a section with columns is an error.

### 7.4. Breaks

- `|newpage` is a page break without a style change.
- `|newcolumn` moves to the next column of the section or page.

A break is attached to the following content; no empty paragraph is created. A break inside a group kept together by a block style is an error.

### 7.5. Sections with columns

```
|section(cols=2, gap="6mm", rule="0.5pt solid", balance=True):
Текст у дві колонки…
|newcolumn
Продовження в другій колонці.
|end section
```

| Parameter | Meaning |
| --- | --- |
| `cols` | number of columns |
| `widths` | widths of unequal columns, for example `["60%", "40%"]` |
| `gap` | gap between the columns |
| `rule` | separator line, for example `"0.5pt solid"` |
| `balance` | balance the column heights at the end of the section; default `True` |
| `id` | ID of the section |

A table inside a section with columns gets the column width: `width="100%"` and the column percentages are computed from `(area width − gaps) / cols`, with unequal `widths` from the narrowest column (decision 132). The default gap is 5 mm.

Conditional content is given with `|if` or `when=`, not with hidden ODF sections: a hidden section stays in the ODT file, which creates a risk of leaking text.

### 7.6. Headers and footers

Headers and footers are set by an environment on a page style; the content is ordinary markup.

```
|header("Portrait"):
|.Header: Договір № |(doc.identifier)
|end header

|footer("Portrait"):
|.Footer: Сторінка |field.page з |field.pages
|end footer

|footer("Portrait", which="first"):
|end footer
```

- `which`: `"all"` (default), `"first"`, `"left"`, `"right"`. An empty environment removes the header or footer on the corresponding pages.
- The translator chooses how the first-page header or footer is implemented (with ODF 1.3 means or a separate master page).
- `which="first"` is the first page of each run of this style (like `style:header-first` in ODF 1.3), for example the first page of each appendix. For the first page of the document only, a separate style is used: `page_style("Title", parent="Portrait", next="Portrait")`.
- `which="left"` or `"right"` turns on separate headers and footers of even and odd pages of the style; `"all"` sets both, `"left"`/`"right"` overrides one. Margins are mirrored only with `mirror=True` (section 7.2).
- Headers and footers are inherited through the `parent` of the page style and can be overridden.
- Headers and footers are set in the document or in a styles module (the function `header(…)`/`footer(…)` with markup in the string argument `markup(…)`).
- `|(…)` in a header or footer is evaluated at build time.

Writer fields are recalculated by Writer itself:

| Command | Field |
| --- | --- |
| `\|field.page` | number of the current page |
| `\|field.pages` | number of pages |
| `\|field.chapter(level=1)` | title of the current heading of the given level |
| `\|field.title` | document title from the metadata |

### 7.7. Parallel tracks

The environment `|parallel` outputs two or more coherent texts — tracks — side by side and aligns vertically the beginnings of their semantic blocks — segments (decision 134). Typical cases: a bilingual contract, "before / after" and a protocol of disagreements, a norm and a commentary, a requirement and a detailed answer. The columns of a section (7.5) flow independently and do not align the beginnings of blocks; a table (section 6) is a grid of values without numbering, IDs and language by column. `|parallel` is output as an ODF table, but the tracks, segments, their IDs and languages stay in the document model: numbering and references are counted per track, the library takes the track language into account, the tracks are checked against each other.

**Model.**

- A track (`track`) is a named column: `id`, optional `lang` (language), `title` (the name in the header row), `width`, `block` (block style for the track cells), `role` (a free label: `translation`, `old`, `note` and so on), the flags `primary`, `numbered`, `optional`. There are two or more tracks.
- The primary track (`primary`; by default the first) gives the document navigation and serves as the reference for the correspondence check and the freshness control. The primary track cannot be `optional` and `numbered=False`.
- A segment is a group of blocks, one per track; it corresponds to a table row. The beginning of a segment is the same in all tracks; inside a segment the blocks of the tracks flow independently; the height is that of the longest block, empty space stays empty. A segment is a semantic block of any length: a heading with clauses, a table, a figure.
- A full-width segment (`span="all"`) is content common to all tracks: a common heading, a preamble, a figure, a table of signatures.

**Syntax.**

```
|parallel(langs=["uk", "en"], gap="8mm", rule="0.3pt solid #999999", parity="translation"):

|segment(span="all"):
|.DocumentTitle: ДОГОВІР № |(doc.identifier) / AGREEMENT No. |(doc.identifier)
|end segment

|segment(id="city") |track("uk"){м. Харків} |track("en"){Kharkiv}

|segment(id="subject"):
|track("uk"):
|< Предмет договору
|>(id="services") Виконавець надає послуги, а Замовник сплачує |(money_full(price, "UAH")).
|track("en"):
|< Subject of the Agreement
|>(id="services") The Contractor provides services, and the Customer pays |(money_full(price, "UAH")).
|end segment

|end parallel
```

| Argument of `\|parallel` | Meaning | Default |
| --- | --- | --- |
| `tracks` | list of tracks: `track(…)` values or strings (track id) | — |
| `langs` | shorthand: `langs=["uk", "en"]` ≡ `tracks=[track("uk", lang="uk"), track("en", lang="en")]`; `tracks` and `langs` together are an error | — |
| `primary` | id of the primary track (or `primary=True` in `track(…)`) | the first track |
| `widths` | track widths (`"50%"`, `"60mm"`, `"*"`, `"2*"` — as `cols` of a table, section 6.3); `width` of a track takes precedence | equal |
| `gap` | gap between tracks | `"6mm"` |
| `rule` | separator line between tracks, for example `"0.3pt solid #999999"` | none |
| `header` | row with the track names (`title`), repeated on every page | `True` if any track has a `title` |
| `parity` | profile of the correspondence check: `"translation"`, `"structure"`, `"none"` | `"structure"` |
| `style` | table style of the output | `ParallelTable` |
| `keep_rows` | do not break segments between pages | `False` |
| `id` | ID of the environment (for messages and the structure dump) | — |

The code function `track(id, lang=None, title=None, width=None, block=None, role=None, primary=False, numbered=True, optional=False)` returns a track description (like `col(…)` of a table). `id` is a Unicode identifier (section 3.9), unique in the environment. `numbered=False`: the blocks of the track are not numbered and do not advance counters (commentaries, margin notes). `optional=True`: the track may have no block in a segment (the cell is empty without a warning). `lang` is a language tag, like `doc.language` (section 2.3).

| Argument of `\|segment` | Meaning |
| --- | --- |
| `id` | ID of the segment, unique in the document; messages, `primula parallel` and the editor find the segment by it; it is not a reference target |
| `span` | `"all"` is a full-width segment, its body is ordinary blocks without `\|track`; by default a segment by tracks |
| `when` | condition; the segment is excluded as a whole |
| `parity` | check profile for this segment (for example `"none"` for a free translation) |
| `keep` | do not break the segment between pages |
| `status` | status label of the segment (`draft`, `translated`, `reviewed` or your own), written to the structure dump |

- A track block `|track("id"):` is an environment inside a segment; its body is ordinary blocks. It is closed by the next `|track(…)`, the closing of the segment or the end of the segment. The implicit clause scope of `|>` (section 3.6) also ends at the boundary of a track block. Arguments of a track block: `when` (a condition for one track), `status` and `rev` (freshness control).
- The line form of a segment has the track bodies in braces on the same line: `|segment(id="city") |track("uk"){…} |track("en"){…}`; the body is inline markup of one paragraph.
- A track block without content (`|track("en"):` immediately followed by closing) is an empty cell; a missing track block in a segment gives the message "no track block" (P5301; a placeholder in the cell).
- `|end` without a name closes the nearest environment; `|end segment` and `|end parallel` are checked.

**Content.** Inside `|parallel` the following are allowed: `|segment`, `|if`/`|for` with segments, `|code:`, `|include` (the inserted blocks obey the same restrictions), comments and blank lines; any other block is an error. In a track block and in a full-width segment the following are allowed: paragraphs, headings, clauses, lists, tables (including nested ones), images and figures (anchored "as character" and "to paragraph"), `|!` notes, fields, footnotes, `|include`, `|if`/`|for`, `|code:`, `|set`, `|let`. Forbidden inside a segment: `|page`, `|newpage`, `|newcolumn`, `|section`, `|appendix`, `|scope`, `|header`, `|footer`, `|document`, `|toc`, `|list_of`, `|frame` anchored to the page, `|watermark`, a nested `|parallel`. Between segments `|page` and `|newpage` are allowed: the table is closed and continues after the break with a new one, and the header row is repeated. A parallel appendix is an `|appendix` that encloses a `|parallel`: the designation and title of the appendix are common.

**Values in code.** In the body of a track block the records `track` (`track.id`, `track.lang`, `track.title`, `track.role`, `track.primary`) and `segment` (`segment.id`, `segment.status`) are available. Outside `|parallel` and in full-width segments these names do not exist (P2201). Document parameters are common to all tracks; a value per language is chosen by code: `customer: {uk: "ТОВ «Замовник»", en: "Zamovnyk LLC"}` and `|(getattr(customer, track.id))`.

**Track language.** A track block with `lang` is evaluated in the track language: quotation marks (section 4.2), typography, library functions without `lang=` (`money_full`, `fmt_date`, `plural`, `words` …), reference labels and captions, designations. In ODT the language is written to the text properties of the cell paragraphs (`fo:language`, `fo:country`), so spelling and hyphenation in Writer follow the track language. The language and metadata of the document do not change. A wrong language tag is error P5305; a language the library does not support is warning P5308, and the forms are English (like P2701 for the document language). Without `lang` the track is written in the document language.

**Numbering.** Each numbered track has its own set of counters: headings, clauses, lists, figures, tables, footnotes (as a numbering scope, section 5.5). On entering `|parallel` each track gets a copy of the document counters; a full-width segment is numbered by the counters of the primary track, and after it the numbered tracks continue from the counters of the primary one; on leaving, the document counters continue from the primary track. `|newpage` between segments does not change counters. In a track with `numbered=False` headings and clauses are formatted without numbers.

**IDs and references.**

- The ID of a block inside a track gets the track prefix: the full ID is `<track id>.<id>` (`uk.services`, `en.services`), like `ns=` of a fragment (section 5.6). The same short `id=` is written in all tracks of a segment. An ID in a full-width segment is an ordinary document ID.
- A short ID in `|@` inside a track is looked up in that track, then in the primary one, then among the document IDs; the label and number are in the language of the track where the reference stands: «п. 1.1» in a Ukrainian block, «cl. 1.1» in an English one (the `ref_labels` dictionary of the track language; if it is missing, P4305).
- Outside tracks (and in full-width segments) a short ID is looked up among the document IDs, then in the primary track; an ID of another track is written in full (`|@("en.services")`).

**Headings and navigation.** Headings of the primary track are headings of the document outline (`text:h`): the Writer navigator, PDF bookmarks, the field `|field.chapter`. Headings of the other tracks are written as paragraphs with the heading style but without an outline level (`text:p`): they look the same but are not part of the navigation, so the document outline is not doubled (checked in Writer and PDF, decision 134). `|toc` and `|list_of` outside `|parallel` build the document list with the blocks of the primary track; `track="en"` with the blocks of the given track (`|toc(track="en")`; the default title is in the track language); a bilingual table of contents is two calls. The list of a non-primary track is written as a Writer user index with its own marks (checked in Writer: the index updates with levels and page numbers); `track=` with a track that is in no `|parallel` is error P5302.

**Footnotes.** A footnote in a numbered non-primary track gets a number from the counter of its track and is written with an explicit label (`text:note-citation text:label`): the numbers in the Ukrainian and English blocks coincide, and Writer's automatic numbering skips such footnotes (checked in Writer and PDF). If `footnotes(restart=…)` sets a restart per page or chapter, the number on the page is unknown at build time: Writer numbers the track footnotes in sequence with the primary track, and the translator gives warning P5316. In a track with `numbered=False` footnotes are error P5304. Endnotes are numbered the same way.

**Formatting.** The output table has the table style `ParallelTable` (in the built-in module: no borders, padding 0, spacing before and after 3 mm); the row of track names has the paragraph style `ParallelHeader`; the style of a track is the block style `block=` (section 11.2), applied to the cells of the track as an enclosing layer of the cascade (section 11.6). `gap` is divided equally into the padding of neighbouring cells; `rule` is the left border of the cells of all tracks except the first. The style names are set in `structure_styles(parallel_table=…, parallel_header=…)` (section 11.5).

**Correspondence check (`parity`).** The profile sets what is compared between each numbered track and the primary one:

| Profile | What is checked |
| --- | --- |
| `structure` | presence of a block of each mandatory track in a segment; the sequence of structural blocks: a heading and its level, a clause and its level, a list item with its level and kind, a table with the number of rows and columns, a figure, a `\|!` note and its kind; plain paragraphs are not compared |
| `translation` | everything of `structure`, and: the sets of block IDs; the sets of reference targets of `\|@`; the sets of value names (parameters, variables) in `\|(…)` — function names are not compared, a translation may format the same value with another function; numbers and identifiers written in the text; equal counters of the numbered mandatory tracks on leaving `\|parallel` |
| `none` | no checks except the correctness of the commands themselves |

- Numbers and identifiers are extracted from the text of a block (outside `|(…)`; the text of inserted fragments is not taken into account): e-mail addresses and URLs as written; a number — groups of digits joined by one separator (space, non-breaking space, `.`, `,`) — is reduced to its digits, so «12 500,00» and «12,500.00» are equal; tokens are compared as multisets. The values of `|(…)` are common and are not compared.
- Tracks with `numbered=False` and empty blocks of tracks with `optional=True` are not compared; segments with `parity="none"` and those excluded by a condition are not checked.
- The messages of the check are warnings; with `--strict` they become errors.

**Freshness control.** It is independent of `parity`: the correspondence check compares the tracks in the current text, the freshness control compares the text of the primary block with the text at which the translation was confirmed.

- The `status` of a track block (and of a segment) is a status label; the translator does not interpret it, but outputs it in `--review`, in the structure dump and in the check `primula parallel --check-status` (section 14.1).
- `rev="3f9a2c/81b0d4"` is two hashes at the moment of confirmation: of the normalized text of the primary track block and of the normalized text of the block itself. If the primary block changed: warning P5320 "the translation is outdated" with the positions of both blocks; if the block itself changed after the confirmation: P5321 "confirmed translation changed". `rev` in a block of the primary track and a value of another form are error P5307.
- The hash is the first 6 hexadecimal digits of SHA-256 (lowercase) of the UTF-8 of the normalized source text of the block body: the body without the `|track(…)` line (for the line form, the text in braces); `|include` lines are supplemented with the text of the included fragment without its header (recursively); comments `|%` and `|comment:` environments are removed; the text is brought to NFC; leading and trailing white space is removed from each line, inner runs of spaces and tabs are replaced by one space; consecutive blank lines become one, blank lines at the beginning and end are removed; lines are joined with `LF`. Expressions `|(…)` enter the hash as written: editing an expression is a change, a change of a parameter value is not. The arguments of `|track` are not part of the hash.
- The confirmation is written by `primula parallel --stamp` (section 14.1): a person decides that "the translation matches the original", and the command records that decision with hashes.

**Messages** (codes follow the prototype registry):

| Message | Severity | Code |
| --- | --- | --- |
| a segment has no block of a mandatory track (a placeholder in the cell) | warning | P5301 |
| a block of an unknown track, `track=` of an index with an unknown track; `\|segment` outside `\|parallel`, `\|track` outside a segment, `\|track` in a full-width segment | error | P5302 |
| invalid content of `\|parallel` | error | P5303 |
| a command forbidden inside a segment; a footnote in a track with `numbered=False` | error | P5304 |
| track description: repeated `id`, two primary tracks, `tracks` and `langs` together, fewer than two tracks, primary track `optional` or `numbered=False`, wrong language tag | error | P5305 |
| repeated segment `id` | error | P5306 |
| wrong `rev`; `rev` in the primary track | error | P5307 |
| the track language is not supported by the library | warning | P5308 |
| structure mismatch (the first mismatched block, positions in both tracks) | warning | P5310 |
| mismatch of numbers and identifiers (extra and missing) | warning | P5311 |
| mismatch of block IDs | warning | P5312 |
| mismatch of reference targets | warning | P5313 |
| mismatch of names in `\|(…)` | warning | P5314 |
| track counters differ on leaving | warning | P5315 |
| Writer numbers the track footnotes (restart per page or chapter) | warning | P5316 |
| the translation is outdated: the primary block changed after the confirmation | warning | P5320 |
| a confirmed block changed after the confirmation | warning | P5321 |

**Mapping to ODF.**

| Element | ODF |
| --- | --- |
| `\|parallel` | `table:table` of the style `ParallelTable`; a column per track; breaking a row between pages is allowed |
| row of track names | `table:table-header-rows`, repeated on every page |
| segment | `table:table-row`, a cell per track; `keep`/`keep_rows` — `fo:keep-together` of the row |
| full-width segment | a cell with `table:number-columns-spanned` over all tracks |
| track block | the cell content: paragraphs, nested tables, figures; an empty block is an empty paragraph |
| heading of a non-primary track | `text:p` with the heading style, without `text:outline-level`; ID bookmark |
| footnote of a numbered non-primary track | `text:note` with `text:note-citation text:label` |
| track language | `fo:language`, `fo:country` in the text properties of the cell paragraphs |
| `\|page`/`\|newpage` between segments | the table is closed, a break, a new table with the same row of names |
| `\|toc(track=…)`, `\|list_of(…, track=…)` of a non-primary track | `text:user-index` with its own name over the marks `text:user-index-mark` with a level |

Limitations: a heading left last in a table row is not kept with the next segment (a table row has no "keep with next") — the heading is written in one segment with the first clause. Outside version 1.1: export of segments to CSV or XLIFF for translation systems, paragraph-to-paragraph alignment inside a segment, different page layouts of the tracks, a "requirement / answer" profile with a typed status.

## 8. Graphics and frames

### 8.1. The ODF model

All floating objects are ODF frames (`draw:frame`):

- anchoring: as character, to character, to paragraph, to page, to another frame;
- horizontal and vertical position: alignment or offset relative to the paragraph, the line, the text area, the page or its margin;
- wrapping: none, on one side, on both sides, optimal, through (in front of the text or behind it), contour;
- properties: size, spacing around, border, rotation, mirroring, cropping, transparency;
- content: an image (PNG, JPEG, SVG) or a text box; a caption is a paragraph inside the frame, the number in it is computed text, not a field (section 5.2).

ODF anchoring "to page" fixes the page number. Therefore a position relative to the page (`rel="page"`) is implemented by the translator as anchoring to a paragraph with a position measured from the page: the frame stands at the right place on the sheet and moves to another page together with its paragraph. Literal anchoring to a page number is only possible with an explicit `anchor="page"`.

Image formats: PNG, JPEG, SVG; other formats are not converted. Image paths are relative to the file with the command and do not go outside the project root. An SVG image may also be a string computed by code (`svg=`, section 8.2).

### 8.2. Image

`|img(path, …)`, `|img(key=…, …)`, `|img(svg=text, …)` or `|img(value, …)` is an image without a caption and number: logos, icons, photos in the text, a stamp or a signature in the requisites. An image is given in exactly one way (otherwise error P6113): a path, a key (section 9.3), an SVG string or an image value `img(…)` (section 8.6).

```
Логотип |img("assets/logo.png", height="8mm") у тексті.

|img("assets/device.jpg", width="60mm", place="right", wrap="side", gap="3mm")
Опис пристрою, що обтікає зображення зліва…
```

If `place` (other than `"inline"`) or `x`/`y` is given, the image becomes a floating frame anchored to the next paragraph.

Size without `width` and `height`: for raster images by the DPI from the file (PNG `pHYs`, JPEG JFIF/EXIF), without DPI 96; for SVG by the `width`/`height` of the root element, otherwise by the `viewBox` at 96 DPI. An image wider or taller than the text area is scaled down proportionally to fit it without a warning. EXIF rotation is not applied (the translator does not re-encode images); with an orientation other than 1 a warning is given with a hint to rotate the file.

An image computed by code (decision 131): `svg=` is a string with an SVG document built by code, for example by a function of a project module (a chart, a QR code, a barcode). Code still writes no files: the translator puts the string into the ODT as it is (UTF-8) under a name derived from the content hash; identical images are stored once. The size is as for an SVG file. The string is checked so that the document stays self-contained and safe to open:

- the root element is `<svg>`, the XML has no errors, there is `width`/`height` or `viewBox` (P6110);
- no `DOCTYPE` and `ENTITY` declarations (P6111);
- only internal references: `#id` and `data:`; an external reference (`href`, `xlink:href`, `url(…)` in attributes and `<style>`, `<?xml-stylesheet?>`) is error P6112: Writer must not access the network or files when showing the image.

```
|code:
def полоса(ширина):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{ширина}mm" height="4mm"><rect width="100%" height="100%" fill="#0b5563"/></svg>'
|end
Виконання: |img(svg=полоса(30)) 60 %.
```

An image value `img(…)` (section 8.6) in the position of the path: `|img(лого)`, `|figure(діаграма(дані), width="120mm"):`. The parameters of the value (`img(svg=…, height="10mm")`) are the defaults of the command parameters; an explicit command parameter takes precedence. This way a module function returns a whole image, together with its size.

### 8.3. Figure

`|figure(path, …):` or `|figure(key=…, …):` … `|end figure` is a numbered illustration: a frame with an image and a caption. The image is given as for `|img` (section 8.2): a path, a key, `svg=` or an `img(…)` value. The body of the environment is the caption text, with markup.

```
|figure("assets/scheme.svg", width="120mm", id="fig-scheme"):
Схема підключення пристрою
|end figure

Див. |@("fig-scheme", "label").
```

- The caption is output in the format of the structure profile, by default «Рисунок 1 — Схема підключення пристрою»; a reference with a label is «рис. 1».
- A figure is a cross reference target and an entry of the list of figures.
- By default a figure stands as a separate centred block without wrapping; the caption is not separated from the image.

### 8.4. Text box

```
|frame(rel="page", x="120mm", y="25mm", width="70mm", wrap="through", layer="front"):
|.Approval: ЗАТВЕРДЖУЮ
|end frame
```

### 8.5. Placement parameters

The parameters describe the frame itself, not the surrounding text.

| Parameter | Meaning |
| --- | --- |
| `place` | `"inline"`, `"left"`, `"center"`, `"right"`, `"inside"`, `"outside"` |
| `valign` | `"top"`, `"middle"`, `"bottom"` |
| `x`, `y` | exact offset instead of `place` / `valign` |
| `rel` | reference point: `"para"` (default), `"area"` (text area), `"page"` |
| `anchor` | explicit ODF anchoring: `"char"`, `"para"`, `"page"`; usually not given |
| `wrap` | wrapping mode (table below) |
| `layer` | `"front"`, `"back"` — for `wrap="through"` |
| `gap` | spacing between the text and the frame; one value or four sides |
| `width`, `height` | `"60mm"` or `"50%"` of the text area; one side keeps the proportions |
| `rotate`, `mirror`, `crop`, `opacity` | rotation, mirroring, cropping, transparency |
| `border`, `padding` | frame border and padding |
| `style` | frame or image style; the style properties are the parameter defaults, an explicit parameter takes precedence: `\|img("logo.png", style="LogoSmall")` gets the width of the style `LogoSmall` |
| `alt` | alternative text |

The wrapping mode is given without a side: the translator derives the side of the text from the position of the frame.

| `wrap` | Meaning | Writer wrapping with `place="right"` |
| --- | --- | --- |
| `"none"` | text above and below | none |
| `"side"` | text on the free side | left |
| `"both"` | text on both sides if there is space | parallel |
| `"auto"` | Writer chooses the side with more space | optimal |
| `"through"` | the frame in front of the text or behind it (`layer`) | through |
| `"contour"` | along the contour of the image | contour |

### 8.6. Watermark

Two equivalent forms:

- a page style parameter: `page_style("Portrait", …, watermark="ПРОЄКТ")` or `watermark=img("assets/stamp.png")`; in a styles module also the function `watermark("ПРОЄКТ", pages=[…])`;
- the document command `|watermark("ПРОЄКТ", pages=[…])`: the mark is put on all page styles or only on the listed ones.

The translator places the mark as a frame behind the text on each page of the corresponding style. Conditional inclusion is done with `|if(draft)`.

- A text mark is output as an SVG image created by the translator (text with rotation and transparency), in a frame behind the text — the same way as an image mark.
- Parameters of a text mark: `angle=45` (degrees counterclockwise), `color="#C8C8C8"`, `size=None` (chosen so that the text takes about 80 % of the diagonal of the text area; otherwise a length, for example `"72pt"`), `opacity=50` (percentage of opacity), `font=None` (the font of the default style).
- `img(path, …)` or `img(svg=text, …)` in code is an image value (the path is checked by the rules of section 10.1, the string by the rules of section 8.2; a path and `svg=` together are an error); it is used in `watermark=`, in `|watermark(…)`, as the image of `|img(value)` and `|figure(value)` (section 8.2) and in `markup(…)` markup.
- `pages=[…]` is a list of page style names.

## 9. Technical documentation tools

### 9.1. Admonitions and notes

`|!("kind")` is semantic markup of a message: the author gives the kind, and the signal word, formatting and symbol are taken from the styles module.

| Kind | Signal word (uk) | Meaning |
| --- | --- | --- |
| `danger` | НЕБЕЗПЕКА | imminent danger to life |
| `warning` | ПОПЕРЕДЖЕННЯ | possible danger to life or serious injury |
| `caution` | ОБЕРЕЖНО | possible minor injury |
| `notice` | УВАГА | possible damage to property, no danger to people |
| `note` | Примітка | explanation |
| `tip` | Порада | recommendation |

```
|!("warning") Перед обслуговуванням від'єднайте пристрій від мережі.

|!("danger", hazard="Висока напруга"):
Дотик до струмопровідних частин призводить до смерті.

|- Вимкніть живлення.
|- Перевірте відсутність напруги.
|end!
```

| Parameter | Meaning |
| --- | --- |
| `hazard` | kind and source of the hazard |
| `consequence` | consequences |
| `symbol` | symbol: a file path or a name from the symbol dictionary |
| `id`, `block`, `when` | reference target, block style, condition |

- The scope of the block follows the rule of the implicit clause scope (section 3.6).
- The formatting in version 1.1 is built in and controlled by the styles and settings of the styles module: a table with 3 mm spacing before and after (the properties `space_before`, `space_after` of the style `AdmonitionTable`) so that neighbouring blocks do not touch; the symbol (`symbol=`) is the left column spanning all rows of the block; without a symbol, one column with the coloured left border of the kind; the symbol is not separated from the text. Styles: paragraph styles `AdmonitionDanger`, `AdmonitionWarning`, `AdmonitionCaution`, `AdmonitionNotice` (signal word), `AdmonitionText` (the rest of the block text), table styles `AdmonitionTable…` per kind; colours per ANSI Z535 (red, orange, yellow, blue) are overridden in the styles module. The overridable function `admonition(kind, body, …)` is postponed until the operations on `content` (section 4.3); a definition of `admonition` in a styles module is not used (a warning of group `P9`).
- Order of the parts of the block (ISO 3864-2, ANSI Z535.6): the signal word (`Admonition<Kind>`, bold, the colour of the kind) → `hazard`, if given (`AdmonitionText`, bold) → `consequence`, if given → the body of the block (measures, lists). In the line form the body is one paragraph. A block without a body, `hazard` and `consequence` is an error.
- Safety signs are not part of the kit (the ISO 7010 pictograms are copyrighted by ISO); a project connects its own files: `admonition_symbols(danger="assets/signs/w012.svg", …)`. Paths in `admonition_symbols` are relative to the file of the styles module with this call, `symbol=` of a block to the file with the block (section 10.1).
- The linter requires `hazard` in `danger` and `warning` (a warning of group `P9`); an unknown kind is an error listing the kinds; `hazard` and `consequence` in `note` and `tip` give a warning, the parameters are ignored.
- Signal words depend on the document language and are overridden in the styles module: `admonition_words("ru", warning="…")` (the language is the first argument, as in `captions`; a call without a language sets the word for all languages).

| Kind | uk | ru | en |
| --- | --- | --- | --- |
| `danger` | НЕБЕЗПЕКА | ОПАСНО | DANGER |
| `warning` | ПОПЕРЕДЖЕННЯ | ПРЕДУПРЕЖДЕНИЕ | WARNING |
| `caution` | ОБЕРЕЖНО | ОСТОРОЖНО | CAUTION |
| `notice` | УВАГА | ВНИМАНИЕ | NOTICE |
| `note` | Примітка | Примечание | Note |
| `tip` | Порада | Совет | Tip |
| `notes` (heading of a group of notes) | Примітки | Примечания | Notes |

- `note` and `tip` are paragraphs without a table and a symbol. A single `note`: «Примітка. Текст.» (the word has the character style `NoteLabel`, the paragraph `Note`, the same as `|.Note:`). Several `note` blocks in a row (only blank lines between them): a paragraph with the group heading (the word `notes`, for example «Примітки:») and a Writer list with the style `NoteList`; the numbering of each group starts at 1. `tip` is not grouped: «Порада. Текст.». A `note` block of several paragraphs: the word is in the first one, the others have the style `Note`; in a group, paragraphs of the list item. The number format is taken from the list style; conformance to DSTU 3008:2015 is in the open question about the formats of the `report` profile (section 4.3). The reference modes `label` and `title` for notes are an error (section 5.10).
- The paragraph style `|.Note:` remains for cases where only the look is needed without the meaning of a note.

### 9.2. Conditional build of variants

The main mechanism is the core's `|if` and `|for`; the parameters of a variant are set in the document, the project or the batch build (`build()`).

The argument `when=` is a shorthand for any block command, environment and table row:

```
|>(when=has("wifi")) Пристрій підключається до мережі Wi-Fi.
|:(when=model == "X300") Потужність |& 2,2|~кВт
```

- The value of `when=` is a boolean core expression. The source text of the expression is used for the report and the labels of the `--review` mode. A string instead of a boolean is an error with a hint.
- The set of product features is the parameter `features` (`features: [wifi, bluetooth]`); the function `has(name)` checks whether a feature is present. If the parameter `features` is not set, `has(name)` returns `False`; `features` that is not a list of strings is an error.
- Removed content does not go into the ODT. Numbering, the table of contents, lists and table formulas are computed after the selection.
- A reference to a removed target is an error naming the condition.
- The build report lists the parameters of the variant and the conditions that applied.
- The `--review` check mode: the conditional fragments of all variants are included in the build and marked with their condition; the result is marked with a watermark as unfit for release. This affects `when=` and the constructs `|if`/`|elif`/`|else` whose branches contain only markup; an `|if` with definitions in its branches (`|let`, `|code:`, macros) is evaluated as usual (a warning of group `P9`: otherwise including all branches would give repeated definitions).
- Marks: a green background means the condition is true in the current variant, red that it is false (the fragment is included only because of `--review`). A block: before it, a paragraph `ReviewLabel` «[when: has("wifi")] — так» / «— ні» (ru: да/нет, en: true/false), and a background on the paragraphs of the block; a table row: a background on its cells. Inside a line: the character style `ReviewTrue`/`ReviewFalse` and a Writer comment (`office:annotation`) with the text of the condition; `|elif`/`|else` branches with their condition («else: …»).
- The watermark is put on all page styles: «НЕ ДЛЯ ВИПУСКУ» (uk), «НЕ ДЛЯ ВЫПУСКА» (ru), «NOT FOR RELEASE» (en and other languages); the document's own watermark is replaced. The texts of the marks and the watermark are set by the styles module function `review_marks("uk", true=…, false=…, watermark=…)` (the language is the first argument, as in `captions`); the background colours are set by the styles `ReviewTrue`, `ReviewFalse` and `ReviewLabel`.
- In the check mode numbering, references and the table of contents are computed over the included content and may differ from the release; the report contains `review: true`. `|if` branches not chosen in the current variant are marked with their condition; a reference to a target in such a branch is a warning, as for a disabled `when=` (section 5.7).

### 9.3. Key map

Indirect references to fragments and resources (modelled on DITA keys). The map is set in the project header; a variant overrides keys in the parameters of the batch build.

```yaml
keys:
  safety.general: fragments/safety-eu.f.prml#general
  logo: assets/logo-x300.svg
```

```
|include(key="safety.general")
|img(key="logo", height="10mm")
```

- `file#part` points to the part of a file marked with `|part("part"):`.
- An unknown key is an error; key values are paths inside the project, relative to the project root (not to the file with the command). Without a project file there is no key map: `key=` is an error "no key map".
- `file#part` is allowed only in `|include`; a key with `#` in `|img(key=…)` is an error; `key=` together with `part=` in `|include` is an error.
- A build target overrides keys: `build("doc.prml", …, keys={"logo": "assets/logo-eu.svg"})` and `keys` in `targets`; only keys declared in the project's `keys` may be overridden. The key in `|include(key=…)` is static (section 10.2); overridden keys are known before the tree is built.

### 9.4. Abbreviations

```
|abbr("ПЗ", "програмне забезпечення")
|abbr("ЄДРПОУ", "Єдиний державний реєстр підприємств та організацій України", show=False)
```

- Three forms: `|abbr("ПЗ", "програмне забезпечення")` is a definition and a use at this place; `|abbr("ПЗ")` is a use of a defined abbreviation (the definition may come earlier or later in the text); `show=False` is a definition without output to the text (allowed only in the form with the expansion). Ordinary text «ПЗ» is not a use.
- At the first use the expansion is output with the abbreviation in brackets, later only the abbreviation. "First" means first in the text of the resulting ODT after expanding `|include`/`|document` and selecting by `when=`. In a compound document the abbreviation dictionary and the list are common (like the table of contents), and the expansion is output once for the whole ODT. A use in a heading, a caption, the table of contents and lists outputs only the abbreviation and does not count as the first one.
- `text="програмного забезпечення"` is the form of the expansion at this place (grammatical case); without it, the form from the definition.
- An unknown abbreviation is an error. Literally repeated definitions (a fragment included twice) are allowed; a different expansion is an error with the positions of both definitions. Abbreviation names are case-sensitive.
- The mode is set in the styles module: `abbreviations(first="expand", sort="alpha")`. `first`: `"expand"` gives «програмне забезпечення (ПЗ)» (default), `"short"` always only the abbreviation (the expansion is in the list; without `|list_of("abbr")`, a warning of group `P9`). `sort`: `"alpha"` — alphabetically in the document language (`sort_key`, default), `"order"` — in the order of first use. Any other value is an error.
- The list `|list_of("abbr")` is a two-column table without borders (table style `AbbreviationList`): the abbreviation and its expansion; the heading is as for the other lists. The list is computed at build time, is not updated in Writer and shows no page numbers; it contains all defined abbreviations, including `show=False`. If there are no abbreviations, a warning is given and the list (with its heading) is not output.

### 9.5. Alphabetical index

```
|index("напруга живлення")
|index("живлення", sub="напруга")
|list_of("index", title="ПОКАЖЧИК")
```

The translator writes ODF alphabetical index marks (`text:alphabetical-index-mark`) and a Writer index; Writer updates the page numbers (for PDF output, the translator does it through LibreOffice). An index entry that has only subentries is output without a page number (Writer behaviour).

## 10. Modules, project, data, build

### 10.1. Inclusion mechanisms

| Mechanism | What it does | Namespace |
| --- | --- | --- |
| `\|include("path", …)` | inserts the content of a fragment at the place of the call | isolated, only an explicit export reaches the document |
| `\|import("path", …)` | loads a module of definitions | separate: `module.name` |
| `\|document("path", …)` | inserts a whole document as part of a compound one | isolated, with its own parameters |

Common rules for paths: a path is relative to the file with the command and does not go outside the project root; URLs, absolute paths and cycles are errors. Leaving the root is checked on the written path without resolving symbolic links (decision 136): `..` is collapsed textually, so `../` does not lead outside the root, while a symbolic link created by the author inside the project (`lib` → `../shared`) may lead to a shared library outside it. A file taken through such a link gives a warning with the name of the link and its target (once per link): a directory outside the project is not part of the source archive and must be kept together with the project to rebuild it. In messages, the report (section 14.3) and `--embed-sources` such a file is written with its path inside the project (`lib/prices.m.prml`); paths inside the library are relative to the written path and obey the same rule. The project file is found by the rules of section 10.6; without it the project root is the directory of the root document. The extension `.prml` in a path may be omitted; then a file with the sub-extension matching the command is looked for first (`.f.prml` for `\|include`, `.m.prml` for `\|import`, `.s.prml` for styles modules, section 2.2), then a file without a sub-extension (`name.prml`).

### 10.2. Fragments: include

```
|include("fragments/warranty.f.prml", months=24)
|include("lib/clauses.f.prml", part="liability")
|include("a/warranty.f.prml", ns="wa")
|include("b/warranty.f.prml", rename={"months": "months_b"})
|include(key="safety.general")
```

- The parameters of a fragment are declared in its header (`params:` with defaults) and given by the arguments of `|include`; an unknown parameter is an error.
- The path, `part` and `key` must be known when the tree is built (section 3.6): allowed are literals, parameters of the headers of the file with the command and of the root document, project parameters `project.*`, keys of the map and expressions over them (`"fragments/" + lang + ".f.prml"`). Referring to another name is an error "the value must be known when the tree is built" (section 3.2). The other arguments, including the fragment parameters, are arbitrary core expressions evaluated in the evaluation phase.
- A fragment included twice is evaluated for each inclusion separately, with its own parameters; the exports of two inclusions conflict by the rules of `on_conflict` unless they are separated with `ns=` or `rename=`. The IDs of a fragment with `ns=` get a prefix (section 5.6).
- `part` inserts only the part of a file marked with `|part("name"):` … `|end part` (reuse by keys, like conref in DITA).
- `ns` and `rename` resolve conflicts of exported names (section 10.4).
- `level_shift=n` (an integer 0–5) shifts the headings of the inserted content `n` levels down — after the number of `<` and `level=` have been applied; the shifts of nested inclusions add up. A level above 6 is an error (the heading stays at level 6). Clauses `|>` are not shifted: they are counted from the heading. The value is an expression of the evaluation phase.

Example: one warranty fragment for two items.

```
|include("fragments/guarantee.f.prml", item="Позиція 1", months=12)
|include("fragments/guarantee.f.prml", item="Позиція 2", months=24)
```

The fragment `guarantee.f.prml` declares `params: {item, months}` and may have its own `|let`. It exports nothing, so the inclusions are independent and there is no repeated definition. If the fragment exports a name (`|export(total=…)`), the two inclusions conflict and are separated at the place of inclusion: `ns="g1"` and `ns="g2"` (names `g1.total`, `g2.total`) or `rename={"total": "total_1"}`.

### 10.3. Modules: import

```
|import("lib/business")                          |% |business.sign(…)
|import("lib/business", "sign", "requisites")    |% |sign(…)
|import("lib/business", alias="b")               |% |b.sign(…)
|import("std/math")
```

- A module is evaluated once; the values are frozen after loading.
- A module outputs no content: text outside definitions is an error. A module header is optional.
- An alias is given with `alias=` because `as` is a Python keyword.
- The namespace name is the base of the file name without the extension and sub-extension: `lib/business.m.prml` → `business`, `lib/договір.m.prml` → `договір`, `std/math` → `math`. If it is not an identifier (section 3.9) or is a reserved name, it is an error with a hint about `alias=`.
- Module content: `|def`, `|let`, `|code:` (definitions and actions, section 12.7), `|import`, comments, blank lines. Text, `|include` and other markup blocks are errors.
- The names of a module are available as `module.name` in expressions and as commands `|module.name(…)`; after selecting names, without the prefix. No export is needed: all names are open except those starting with `_` (`@export` in a module gives a warning, section 10.4). Referring to `module._name` is an error with a hint that the name is private.
- `|import` in a document also applies in its fragments (a fragment reads the names of the document); `|import` in a fragment applies only in that fragment.

### 10.4. Scopes

Levels, from general to specific: project → styles (public names of the styles modules in the order of the list) → document → fragment and module → local (the body of `|for`, of a macro, of a function). Name lookup: local → fragment → document → styles → project → built-in. Between styles modules the layer rules apply: a name of a later module replaces the same name of an earlier one. A document name that coincides with a name of the "styles" level is shadowing, not a repeated definition.

Global definitions of a document:

- `|let(…)`, top-level assignments in `|code:` and header parameters define the global names of their file: document, fragment or module. Each file has its own namespace; in a fragment `|let` writes to the namespace of the fragment, not of the document (see "Isolation of fragments").
- Names are visible in the whole document regardless of the place of definition; values are computed lazily, in the order of dependencies; a cycle is an error.
- Values are immutable; a repeated definition is an error with the positions of both definitions.

Isolation of fragments:

- By default the definitions of a fragment are visible only inside it; the fragment reads the global names of the document and the project freely. `|let` without `export` in a fragment does not affect the document, so including the same fragment again creates no conflict.
- Only explicitly exported names reach the namespace of the document: `|export(months=12)` or `|let(months=12, export=True)`.
- A function of a code block is exported at the place of definition by a decorator (decision 135): `@export` under its own name, `@export(name="triple")` under the given one (the value is an identifier string); the name of the function itself stays private in the fragment. The decorator is allowed only on a top-level `def` of a `|code:` block; in a nested function, in the body of an action (a top-level `if`, `for`) and in another form it is an error; other decorators are forbidden (section 12.2).
- An already defined name of a fragment — a `|def` macro, a function, a `|let` name or a parameter — is exported under the same name with a string: `|export("підпис", "triple")` (decision 135). String and keyword arguments of `|export` can be combined; a name that does not exist in the fragment is an error. The notation `|export(f=f)` remains a repeated definition.
- `@export` and `|export` outside a fragment are the same error as `|let(…, export=True)`: in a document, project, styles module, the code of a `|for`/`|def` body. In an `|import` module the decorator changes nothing — all names without `_` are open (section 10.3) — and gives a warning.
- A conflict of the exports of two fragments is resolved at the place of inclusion, without editing the fragments: `ns="wa"` puts the export into the namespace `wa.*`, `rename={…}` renames individual names.
- The author of a document may deliberately override an export of a fragment: `|let(months=24, override=True)`. Without `override` a repeated definition is an error.
- `export` and `override` are reserved service arguments of `|let`.
- The project parameter `on_conflict`: `"error"` (default), `"first"`, `"last"`; the last two give a warning.
- Local names of macros and loops may shadow global ones.
- `|let` and `|code:` outside the bodies of `|if`, `|for`, `|def` (including in tables, clauses, appendices) define global names; their place in the text does not matter. In the body of `|for` and `|def` they create local names up to the end of the body (per iteration or call), and actions are executed in place. In a branch of a top-level `|if`, `|let` and `|code:` (including actions, for example `paragraph_style`) are an error with a hint to write a conditional expression: `|let(rate=20 if vat else 0)`; in an `|if` nested in `|for` or `|def` they are local. `export=True` is allowed only in a global `|let`.
- A fragment sees its own definitions and parameters, then the global names of the root document (including the exports of all fragments), then of the project. The non-exported names of an intermediate fragment in a chain of inclusions are not visible.

A document parameter with the name of a project parameter overrides its value for this document (section 10.6): `city` is the value of the document, `project.city` the value of the project.

Access to the levels: `|(project.city)` — project parameters, `|(doc.title)` — document metadata; document parameters and exports of fragments by name.

### 10.5. External data

```
|code:
items = load_csv("data/items.csv", types={"qty": "decimal", "price": "money"})
seller = load_yaml("data/seller.yaml")
|end
```

- `load_csv`, `load_yaml`, `load_json`, `load_ods`, `load_xlsx`, `load_text` are read-only, only for files inside the project (the path is relative to the file whose code calls the function); the result is records (`record`) and lists, for `load_text` a string.
- `load_text(path)` (decision 140) is the whole text file as one string, without parsing: UTF-8 (a BOM is dropped; another encoding is a read error), line ends LF, NFC normalization, as for source files; the length is within the string limit of the core. It is meant for texts that are more convenient to keep as a separate file: SVG for `svg=` (`|img(svg=load_text("img/знак.svg"))`, SVG checks in section 8.2), text templates for library functions.
- The hashes of the files read are written to the build report: the same input data give the same result.
- `load_csv`: UTF-8 (a BOM is allowed), the first line has the field names, quoting per RFC 4180. The separator is `,` or `;`: determined from the first line (whichever occurs more) or given by the argument `sep=`.
- Without `types` all CSV values are strings: automatic recognition of numbers would spoil codes with leading zeros. Types in `types`: `"str"`, `"decimal"` (an integer is a value with scale 0), `"money"` (`decimal` with two digits; more than two digits is an error), `"float"`, `"datetime"` (`YYYY-MM-DD`, `DD.MM.YYYY`, `YYYY-MM-DDTHH:MM[:SS]`, `DD.MM.YYYY HH:MM[:SS]`; a value with a time zone is an error), `"bool"` (`true`/`false`, `1`/`0`).
- Numbers in typed columns: one decimal separator, `.` or `,`; digit groups only with a space or a non-breaking space (`12 500,00`); a notation like `1,234.56` is an error. An empty cell of a typed column is `None`.
- The result of `load_csv` is a frozen list of records; a parse error gives the file, line and column of the CSV.
- CSV column names and YAML and JSON keys are the field names of a record: they may be Unicode identifiers (section 3.9); a name that is not an identifier is available as `r["name"]`. Names are normalized to NFKC; two columns or keys that coincide after normalization are an error.

ODS and XLSX spreadsheets (decision 138):

```
|code:
items = load_ods("data/items.ods", sheet="Позиції", types={"price": "money"})
rates = load_xlsx("data/rates.xlsx", range="A3:C40", header=False)
|end
```

- The file is a ZIP archive with XML parts (ODS — ODF 1.3, XLSX — ECMA-376); it is read without external programs. The hash of the file is written to the build report, as for other data.
- `sheet` is the sheet name or its number from 1 (default the first sheet); `range` is the cells `"A1:D20"` or a starting cell `"A3"` (to the end of the filled area; by default the whole filled area); `header=True`: the first row of the range gives the field names (non-empty, unique after NFKC), `header=False`: the fields are named by the column letters `A`, `B`, …; rows whose cells are all empty are skipped; a merged cell gives a value only for its top left cell.
- The value of a formula is the result stored in the file by the program that wrote it (LibreOffice and Excel store it); the translator does not evaluate formulas, so the result does not depend on the machine. A formula without a stored result is an error with the sheet and cell name: the file must be saved by a spreadsheet program.
- Cell types: a number is a `decimal` rounded to 15 significant digits (the precision of spreadsheet programs: a stored 0.30000000000000004 is read as 0.3; an integer has scale 0); a date and a date with time are `datetime` (XLSX — a number with a date format, the 1900 and 1904 systems); a boolean is `bool` (LibreOffice writes booleans as the numbers 1 and 0 — `types` converts them); text is a string (the paragraphs of a cell joined by line breaks); a time without a date is a string `HH:MM:SS`; an empty cell is `None`; an error value (`#DIV/0!`, `Err:502`) is an error with the sheet and cell name.
- `types` is as in `load_csv` but converts cell values: number → `decimal`, `money` (at most two digits), `float`, `str`; an XLSX date number → `datetime`; 1 and 0 → `bool`; a text cell by the CSV rules. A value that cannot be converted is an error with the cell.
- Protection: an archive whose parts unpack to more than 200 MB, an XML part with `DOCTYPE` or `ENTITY`, a damaged archive are errors; cells count toward the collection size limit. The binary XLS format is not supported: it is saved to XLSX or ODS with a spreadsheet program.

### 10.6. Project file

Two sections in one file `project.p.prml`: a YAML header and code. The file name is fixed; `kind: project` is mandatory, a mismatch is an error.

```
---
kind: project
name: "Договори 2026"
language: uk-UA
doc_defaults: {organization: "ТОВ «Постачальник»", creator: "Відділ договорів"}
styles: [styles/business.s.prml, styles/local.s.prml]
on_conflict: error
params:
  city: "м. Харків"
  seller: {name: "ТОВ «Постачальник»", code: "01234567"}
keys:
  logo: assets/logo.svg
limits: {time: 20, recursion: 500, size: 10_000_000}
targets:
  - {source: contract.prml, output: out/contract.odt}
---
# Пакетне збирання актів
for row in load_csv("data/acts.csv"):
    build("act.prml", params=row, output=f"out/act-{row.no}.odt")
```

| Header key | Meaning |
| --- | --- |
| `kind` | `project` |
| `extends` | the base project: the path to its file (`../../project.p.prml`); see below |
| `name`, `language` | name and default language of the project |
| `styles` | ordered list of styles modules; one string is allowed as a shorthand |
| `on_conflict` | conflict mode for fragment exports |
| `params` | project parameters; a document parameter with the same name overrides the value for that document, the other document parameters are its own |
| `keys` | key map (section 9.3) |
| `limits` | core limits: `time`, `recursion`, `size` (section 12.8) |
| `build_date` | fixed build date (section 12.7) |
| `targets` | build targets: `source`, `output`, `params`, `keys`, `pdf` (section 10.7) |
| `doc_defaults` | default ODT metadata of the documents of the project — the same keys as `doc` of a document header (section 2.3); a document replaces them one by one; `language` here takes precedence over the project `language` |
| `ref_documents` | documents referred to by other documents of the project (section 5.7; their names are listed in `references` of the header of the referring document): `name: path` or `name: {source: path, registry: path}`; the default registry is `build/<base name>.refs.json`; an entry with only `registry` is a published edition without a source. `primula build` of a document from `ref_documents` writes its registry |

- The descriptive section is read by Studio and external programs without executing code; the dump is `primula check project.p.prml --dump-project` (section 14.1).
- `extends:` — the project inherits the base one (decision 123): the project root is the root of the base (fragments, styles, data and documents of the base are available); parameters, keys, documents for references (`ref_documents`), metadata defaults (`doc_defaults`) and styles modules are inherited, and the project's own ones add to and override them (the styles modules of the project come as layers after the base ones); `name`, `language`, `on_conflict`, `limits`, `build_date` are the project's own, otherwise those of the base; targets (`targets`) are not inherited. The project's own paths (styles, keys, documents, targets, data of the code section) are relative to the project file. The code section of the base project is executed before the project's own one, at its own name level: the project's own section may override its name (`order = load_yaml("order.yaml")` instead of the sample). The project must lie inside the root of the base; an `extends` cycle is an error. A typical case is a contract and orders: the contract project (`project.p.prml`: the contract, forms, styles, permanent data, `order = load_yaml("orders/sample.yaml")`) and an order project in the directory `orders/<order>/` (`extends: ../../project.p.prml`, `order.yaml` with the customer's data, `placeholders("final")`, targets — the filled-in forms).
- The code section sees the descriptive one as `project.*`, may add targets and computed parameters, but cannot change the values of the descriptive section. The definitions of the code section are available as `project.*` on a par with the parameters of the descriptive section (names in both are a repeated definition error). The section is executed in any build of a project document (computed parameters as definitions, lazily; top-level actions immediately); `build(…)` only registers a target, and targets are ignored when one document is built. An error in the code section is a build error: the build does not start (in a batch build, no target). The batch build is enabled by the file kind `kind: project`, not by the name; `--project FILE` does not check the name, `kind: project` is mandatory; a sub-extension other than `.p.prml` is a warning of group `P7` (section 2.2). The function `batch_mode()` (only in the code section of a project) returns `True` for `primula build project.p.prml`, otherwise `False`: `if batch_mode(): …` keeps a loop over data from running when one document is built.

Finding the project file:

- The search starts at the directory of the root document and goes up, checking each directory; it stops after a directory with `.git` or at the root of the file system. The nearest `project.p.prml` wins (nested projects are allowed); its directory is the project root. The file found is named in an informational message and in the report.
- `--project FILE` sets the project explicitly (a document outside its directory is an error); `--no-project` turns off the search (the root is the directory of the root document). The search concerns only the root document of the build; `primula fmt` does not use the project.
- Precedence of parameter values: build target (`build()`, `targets[].params`) → document header → project. A value is replaced as a whole, dictionaries are not merged. The type is checked at the top level (`type()`; `decimal` and `float` are different types); `None` in the project allows any type. An unknown target parameter or a type mismatch is an error.

### 10.7. Compound documents and batch build

```
|document("contract.prml", scope="contract")
|document("act-1.prml", scope="act1", params={"act_no": 1})
```

- A part is a full document with its own header (the YAML header of a part is not output to the text: the heading of the part is in its text), namespace and parameters; the numbering of a part runs in its own `scope`; a cross reference between parts uses the full identifier `|@("act1:items")`; the table of contents is common; the result is one ODT.
- Each part is evaluated separately, in its own namespace: the `|let` and exports of one part are not visible to the other parts, there is no repeated definition between parts. Shared data are passed with `params=` or taken from the project (`project.*`). Example — a contract and two acts:

```
|document("contract.prml", scope="contract")
|document("act-1.prml", scope="act1", params={"act_no": 1})
|document("act-2.prml", scope="act2", params={"act_no": 2})
```

- The styles of a compound document are those of the root document and the project; `styles` and `structure` in the header of a part give a warning of group `P7`, and the keys are ignored; of the header keys of a part, `params`, `doc` (the metadata of the part) and `primula` apply. Styles defined by the code of a part go into the document layer of the resulting ODT (section 11.7); identical definitions are allowed, different ones under one name are an error. Headers and footers are those of the root document.
- `doc.*` in a part are the metadata of the part; the ODT metadata are those of the root document. Library functions in a part use the `language` of its header (if absent, of the root); the spell-check language in the ODT is set by the styles of the root.
- The numbering scope of a part without `scope=` is the base of the file name without sub-extensions (`act-1.prml` → `act-1`); the scope name is written by the identifier rules without `:`; an invalid name (a space, `:`) or a repeated scope name is an error with a hint to set `scope=`.
- `|document` is written on its own line in the text of the root document, including inside `|if`/`|for` and with `when=`; inside environments (a table, a list, `|!`, `|frame`), in a part and in a fragment it is an error: there are no nested parts, and a fragment may also be included in a part. The command closes the implicit clause scope (section 3.6).
- The actions of the code sections of parts are executed after the actions of the root, in the order of the parts in the text.
- Appendices are numbered anew in each part (their own designations and scopes); footnotes run through the whole ODT (section 5.10).
- A reference inside a part looks first for the identifier of the part (`scope:id` by default), then for the identifier of the root; an identifier with `:` is a full one.
- `level_shift=n` of `|document` shifts the headings of the part, as for `|include` (section 10.2); the heading numbering of the part then continues the numbers of the enclosing document: a part with shift 2 after the heading «1.2» is numbered «1.2.1», not from the start of level 3 (otherwise its first headings would skip levels).
- A part always starts on a new page. `|document(…, page="Landscape")` sets the page style of the part; without `page=`, the default page style of the root document. Page numbering runs throughout; a restart is `|page(restart=…)` in the part itself.

- `build(source, params=…, keys=…, output=…, pdf=…)` is available only in the code section of the project file and registers a target; `output` is mandatory (there is no implicit name). A target can also be given in the header: `{source, output, params, keys, pdf}`; paths are relative to the project root. Each target builds a separate ODT; the `params` and `keys` of a target are only the declared parameters of the source document or of the project (section 10.6) and the project keys (section 9.3); values are checked against the type of the declaration; for CSV strings the types are given in `load_csv(…, types={…})`.
- `pdf: true` gives a PDF next to the ODT (the same name, `.pdf`); a string is the PDF path inside the project.
- `primula build project.p.prml` builds all targets: first the `targets` of the header, then `build()` in the order of the calls. Coinciding output paths of ODT and PDF are an error, checked after the code section has run, before the build starts; output files are created only inside the project directory. An error of one target does not stop the others; the exit code is 2 if at least one target has an error. `primula check project.p.prml` runs the code in check mode: it registers the targets and checks the sources, parameters and output paths without writing anything.

## 11. Styles

### 11.1. Styles module

Styles are kept in styles modules (`kind: styles`, files `*.s.prml`) loaded by the list `styles` in the project header and, in addition, by the key `styles` in the document header (section 2.3). If neither the project, nor the document, nor the option `--style` (section 14.1) names styles modules, the built-in module `std/styles/default` applies (profile `business`; base styles `Body`, `Heading1`–`Heading6`, `Clause`, `SubClause`, lists, `TableGrid`, `Note`, `NoteLabel`, `NoteList`, `AdmonitionDanger`, `AdmonitionWarning`, `AdmonitionCaution`, `AdmonitionNotice`, `AdmonitionText`, `AbbreviationList`, `ReviewLabel`, `ReviewTrue`, `ReviewFalse`, `DefinedTerm`, `StrikeText`, `Placeholder`, `Strong`, `Emphasis`, `Underline`, `Superscript`, `Subscript`, `Code`, `TableCaption`, `FigureCaption`, `Footnote`, `Endnote`, `NoteAnchor`, `AppendixDesignation`, `AppendixSubtitle`, `AppendixTitle`, `ContentsTitle`, `Contents1`–`Contents6`, `IndexEntry`, `Reference` (no formatting: references in a contract are not highlighted), `Header`, `Footer`, common variants `BodyLeft`, `BodyCentered`, `BodyRight`, `BodyIndented`, `BodyCompact`, `Quote`, `SmallPrint`, `Preformatted`, `ListText`, `TableHeader`, `TableTextCompact`, `TableHeaderCompact`, `SmallText`, lists `DashList`, `LetterList`, `LatinLetterList`, `MixedList`, `Checklist`, tables `TableCompact`, `TableNoBorders`, parallel tracks `ParallelTable`, `ParallelHeader` (section 7.7); pages `Portrait` and `Landscape` A4). Besides it, the kit includes styles sets for business, office, technical documents and reports (section 11.9).

A styles module may declare its base with the header key `extends` (decision 133): a path to another styles module (`std/…`, or relative to the module file). The base is loaded as a layer right before the module (section 11.7), and its own base before it. So a document names only the set it needs or its own module and does not list the built-in one:

```
---
kind: styles
extends: std/styles/business
defaults: {size: 11pt}
paragraphs:
  Requisites: {parent: Details, keep_together: true}
---
```

A module without `extends` has no base; it can also be loaded on top of the built-in one explicitly: `styles: [std/styles/default, styles/local.s.prml]`. A module consists of two sections:

- the YAML header — static styles; Studio and external programs read it without executing code;
- the code after the header — generation and parametrization of styles, the structure profile, library dictionaries, library functions (`captions`, `footnotes` and so on).

```
---
kind: styles
defaults: {font: Roboto, size: 11pt, language: uk-UA}
paragraphs:
  Body:   {align: justify, line_height: "115%", space_after: 2mm}
  Clause: {parent: Body}
  Note:   {parent: Body, size: 9pt, italic: true, align: left}
characters:
  DefinedTerm: {bold: true}
---
structure_profile("business")
spacing = {"0": 0*mm, "s": 1*mm, "m": 2*mm, "l": 4*mm, "xl": 6*mm}
indent_step = 5*mm

# Variants with spacing before the paragraph
for name in ["Body", "Clause", "Note"]:
    for b in ["0", "m", "l"]:
        paragraph_style(f"{name}-b{b}", parent=name, space_before=spacing[b])
```

### 11.2. Kinds of styles

| Kind | YAML group | Function in code |
| --- | --- | --- |
| paragraph | `paragraphs` | `paragraph_style(…)` |
| character | `characters` | `character_style(…)` |
| block (group of elements) | `blocks` | `block_style(…)` |
| table | `tables` | `table_style(…)` |
| list | `lists` | `list_style(…)` |
| frame and image | `frames` | `frame_style(…)` |
| page | `pages` | `page_style(…)` |

- Inheritance is the single key `parent` for all kinds.
- Property names use underscores (`line_height`, `space_after`), the same in YAML and in arguments.
- Style names are Unicode identifiers with hyphens (section 3.9): `Body`, `Основний-текст`. The style namespace is common to all kinds: one name is one style (in `|.Name` the kind of the style is determined by its definition). When styles are moved from systems with separate namespaces (Kit: a paragraph style and a list style `NoneList`), coinciding names are renamed.

### 11.3. Properties

| Kind | Properties |
| --- | --- |
| paragraph | `font`, `size`, `bold`, `italic`, `color`, `background`, `underline`, `strike`, `language`, `align`, `line_height`, `space_before`, `space_after`, `left`, `right`, `first_line`, `keep_with_next`, `keep_together`, `page_break_before`, `widows`, `orphans` |
| character | `font`, `size`, `bold`, `italic`, `color`, `background`, `underline`, `strike`, `language`, `position` (`super`, `sub`) |
| block | `paragraph`, `space_before`, `space_after`, `keep_together` |
| table | `width`, `align`, `frame`, `rules`, `border`, `padding`, `background`, `header_*`, `footer_*`, `paragraph`, `repeat_header`, `keep_rows`, `may_break`, `space_before`, `space_after`, `cols` |
| list | `paragraph`, `levels`: `type` (`number`, `bullet`), `format` (`1`, `a`, `A`, `i`, `I`, and also the Cyrillic `а`, `А`; `i` and `I` are Roman numerals; Cyrillic letters number by the alphabet of the document language uk or ru without gaps; a list with such a style in a document of another language is an error with a hint about `a`, an unused style is not an error, decision 133), `prefix`, `suffix`, `letters`, `bullet`, `left`, `hanging` |
| frame | the placement parameters of section 8.5 |
| page | the parameters of section 7.2 |

Formats of property values:

| Property | Value |
| --- | --- |
| `size` | a length (`11pt`, `10.5pt`) |
| `space_before`, `space_after`, `left`, `right`, `first_line` | a length; `first_line` may be negative (hanging) |
| `line_height` | a percentage (`"115%"`), a length (`"5mm"` — exact height) or `"at_least 5mm"` |
| `font` | name of the typeface |
| `bold`, `italic`, `strike`, `keep_with_next`, `keep_together`, `page_break_before` | `true` / `false` |
| `underline` | `true` / `false` or `"double"` |
| `color`, `background` | `"#RRGGBB"` (the short `"#RGB"` is expanded to the full form) or `"none"` (synonym `"transparent"`, as in ODF) |
| `cols` (table style) | a list of columns — the default `cols=` value of the table: widths (`"52%"`, `"30mm"`, `"*"`), `col(…)` or dictionaries of `col` arguments; only widths and cell formatting, without `id`, `type`, `currency`, `digits` (those belong to the table content); an explicit `cols=` takes precedence |
| `replace` (any style) | `true`: the definition replaces the style of the same name in lower layers entirely, without merging (section 11.7) |
| `align` | `left`, `center`, `right`, `justify` |
| `position` | `super`, `sub`, `normal` |
| `language` | a BCP 47 tag (`uk-UA`) |
| `widows`, `orphans` | an integer ≥ 0 |
| `border`, `border_*`, `frame` | a string `"<width> <type> <colour>"`, for example `"0.5pt solid #000000"`; type `solid`, `dashed`, `dotted`, `double`; `"none"` — no line |
| `rules` | `all`, `rows`, `cols`, `none` |
| `padding` | one length or a list of four (top, right, bottom, left) |
| `header_*`, `footer_*` | any paragraph, character or cell property with the prefix: `header_bold`, `header_background`, `header_align`, `header_paragraph` |
| `paragraph` (in table, list, block styles) | name of a paragraph style |
| `levels` (list style) | a mapping "level 1–10 → level properties": `type` (`number` / `bullet`), `format` (`1`, `a`, `A`, `i`, `I`, and also the Cyrillic `а`, `А`; `i` and `I` are Roman numerals; Cyrillic letters number by the alphabet of the document language uk or ru without gaps; a list with such a style in a document of another language is an error with a hint about `a`, an unused style is not an error, decision 133), `prefix`, `suffix`, `letters` (a string of distinct letters — numbering as text that skips letters, section 5.4), `bullet` (a character), `left`, `hanging` (lengths), `start` (an integer) |
| `space_before`, `space_after` (table style) | a non-negative length: spacing before and after the table (ODF `fo:margin-top`, `fo:margin-bottom`) |
| `odf` | a mapping "ODF attribute → string"; the names are checked against the ODF 1.3 schema |

Length properties accept both a string (`"2mm"`) and a core `length` value (`2*mm`). An unknown property or a value in a wrong format is an error with a position (in YAML, the position of the value).

Properties of a block style: `space_before` applies to the first element of the group, `space_after` to the last one (if the last one is a list, to the last paragraph of the list); `keep_together` binds the elements of the group without forbidding a break in a group longer than a page.

### 11.4. Variants: spacing and indents

Scales are set in the styles module: `spacing` — the steps of vertical spacing, `indent_step` — the step of horizontal indentation. Two mechanisms, both allowed:

1. Generated named styles — a finite set of variants (`Body-b0`, `Body-bl`) visible in Writer; in the text: `|.Body-bl:`.
2. Parameters at the place of use — for rare combinations.

Built-in parameters of any paragraph style:

| Parameter | Meaning |
| --- | --- |
| `before` | spacing before the paragraph: a step of the scale (`"l"`) or a length (`"3mm"`) |
| `after` | spacing after the paragraph |
| `indent` | horizontal indent: a number of steps or a length |

The translator materializes each combination used as a named style with a deterministic name: `Body-before-l-after-s`, `Clause-indent-2`; the parameters in the name come in the order `before`, `after`, `indent`.

Your own parametric styles are functions of a styles module:

```python
def Indented(base, n=1):
    return derive(base, left=n * indent_step)
```

Use: `|.(Indented("Clause", 2)):`. A style is always a string with a name: `derive(...)` and functions like `Indented(...)` return a deterministic style name and register it: the name is reserved at the call (to detect a conflict — the same name with other properties), and the style itself is written to the ODT and the report at its first use, like the styles of the parameters `before`, `after`, `indent`. A style defined by `paragraph_style(…)` and the like is always written. A call of `derive(…)` without a later use leaves no trace in the ODT.

Names of materialized and derived styles (visible in Writer, the same in every build):

- Parameters `before`, `after`, `indent`: `Base-before-<v>-after-<v>-indent-<v>` in this order; the value is a scale key (`l`) or a length in the unit written; a dot is replaced by `_`, a minus by `m`: `before="3.5mm"` → `Body-before-3_5mm`.
- `derive(base, name=None, **props)`: with `name`, that name; without `name`, `Base-<property>-<value>…`, properties in alphabetical order, values by the same rules; `#C00000` → `C00000`, `True` → `on`, `False` → `off`. It returns the name (a string) of the materialized style.
- Values may contain Unicode letters and digits, `_` and `-`; any other character is replaced by `_` (the typeface `Times New Roman` → `Times_New_Roman`).
- If the name is longer than 128 characters, it takes the form `Base-x<8 hex of the sha256 of the canonical notation of the properties>`.
- Identical properties give one name and one style in the ODT. If the name is already taken by a style with other properties (for example, `Times New Roman` and `Times_New_Roman`), it is an error with a hint to set `name=`.
- A variant of a list style when the level type differs: `List-l<level><b|n>` for each differing level in turn: `LetterList-l2b-l3n`. Spacing around a whole fragment (a clause with a list, a block of requisites) is set by a block style.

### 11.5. Binding constructs to styles

```python
structure_styles(
    paragraph="Body",
    heading={1: "Heading1", 2: "Heading2", 3: "Heading3"},
    clause={1: "Clause", 2: "SubClause"},
    list="BulletList",
    numbered_list="NumberedList",
    table="TableGrid",
    figure="Figure",
    admonition="Admonition",
    page="Portrait",
    caption={"table": "TableCaption", "figure": "FigureCaption"},
    footnote="Footnote", endnote="Endnote", note_anchor="NoteAnchor",
    appendix={"designation": "AppendixDesignation", "subtitle": "AppendixSubtitle", "title": "AppendixTitle"},
    toc={"title": "ContentsTitle", 1: "Contents1", 2: "Contents2", 3: "Contents3"},
    list_of={"title": "ContentsTitle", "entry": "IndexEntry"},
    reference="Reference",
    parallel_table="ParallelTable", parallel_header="ParallelHeader",   # |parallel (section 7.7)
    link="Reference",                 # external links |link (default: reference)
    clause_number=None, heading_number=None,   # character style of automatic numbers
    strong="Strong", emphasis="Emphasis", underline="Underline",
    superscript="Superscript", subscript="Subscript",
    code="Code", strike="StrikeText", placeholder="Placeholder",
)
```

Semantic constructs take their default styles from here; `|set(…)` changes them within an environment; an explicit style in the text takes precedence.

### 11.6. Cascade

The cascading mode is the only one. For each paragraph:

1. the style of the construct is taken (from `structure_styles` or `|set`);
2. the active styles of the enclosing `|.Ім'я:` environments and the block style are applied, from the outer to the inner;
3. the own properties of the inner style override the outer ones; inherited properties fill only those not yet defined;
4. explicit `false`, `0mm` count as values;
5. the text style of list items and the styles of table cells are applied as the inner layer; the cell alignment last.

The translator writes one automatic paragraph style with a named parent to the ODT; the cascade is computed by the translator, not by Writer. The parent style is the deepest explicit paragraph style (`|.Ім'я`, a parametric variant, `derive`), and if there is none, the style of the construct. The automatic style contains only the own properties of the outer layers (outer `|.Ім'я:`, the block style, the construct style, the cell style) that are not in the `parent` chain of the parent style; the cell alignment last. If there are no such properties, the paragraph refers to the named style directly: a change of the style in Writer applies to the text marked with this style.

### 11.7. Style layers

- Layers are applied in order from early to late; a later one adds to and overrides the earlier ones:
  1. the modules of the project's `styles` list (in turn);
  2. the files of the option `--style FILE` (in turn, in the order given; section 14.1);
  3. the modules of the key `styles` of the document header;
  4. the definitions in the code of the document and its fragments (the last layer).
- If styles are named in at least one of these ways, the built-in `std/styles/default` is not loaded automatically; to build on top of it, it is named as a base (`extends`) or given explicitly (section 11.1).
- The base of a module (`extends`, decision 133) is a separate layer right before the module; the chain of bases is expanded to the end (`std/styles/letter` → `std/styles/business` → `std/styles/default`). Each module is one layer at the first place where it occurs: a module already loaded as a base or earlier in the list is not loaded again. A cycle of bases is an error "inclusion cycle"; a base of another kind of file is an error. The path of a base is like an `|import` path (section 10.1); for a module from `--style` outside the project root a relative base is looked for next to it. In `--dump-styles` the layer of a base has the origin `extends`.
- A style with the same name is merged with the previous one: dictionaries are merged, scalar values and lists are replaced entirely. The own properties of the lower layer are kept and take precedence over those inherited from a new `parent`: `AppendixSubtitle: {parent: DocumentSubtitle}` on top of `std/styles/default` keeps its `align: right`. To replace a style entirely, the definition is marked `replace: true` (`paragraph_style("AppendixSubtitle", replace=True, parent="DocumentSubtitle")`); the kind of the style does not change on replacement.
- The last layer is the style definitions in the document itself (a `|code:` block with `paragraph_style`, `page_style` and so on, and also `|header`/`|footer`).
- A shared module is not modified; a local module or document contains only the differences.
- A repeated definition of a style within one file is an error.
- Styles and structure settings (`paragraph_style`, `structure_styles`, `numbering` and so on) can be defined by styles modules (each its own layer), the project code, the document and its fragments (the common last layer of the document; a repeated definition of a style in this layer is an error, even in different fragments).
- The place of execution is checked, not the place of writing: a call at the top level of an `|import` module (when it is loaded) is an error; a function of an `|import` module called by an action of the document defines a style in the document layer. Functions may also return styles through `derive(…)` — that is not a definition.

### 11.8. Direct ODF properties

- ODF properties missing from the language dictionary are given explicitly in style definitions: `odf={"fo:hyphenation-ladder-count": "2"}`; the names are checked against the known set of ODF attributes.
- Direct formatting in the text (`|fmt(…){…}`) is allowed with a warning.
- Inserting raw ODF XML is possible only with the unsafe build option `--unsafe`.

### 11.9. Styles of the kit

The translator kit contains styles sets — the modules `std/styles/…` built on `std/styles/default` through `extends` (decision 133). A document or project names one set (`styles: [std/styles/business]`); your own module is built on top of a set (`extends: std/styles/business`) and contains only the differences (section 11.7). The style names of the sets are in Latin letters, as in the built-in module; the description of each set with its list of styles is generated from the modules (the appendix "Styles of the kit" of the author guide).

| Module | Purpose | Base, font | Main styles |
| --- | --- | --- | --- |
| `std/styles/default` | built-in base: styles of the constructs (section 11.5) and common variants | —, Liberation Sans 11 pt | section 11.1 |
| `std/styles/business` | contracts, acts, invoices, minutes | `default`, Liberation Serif 12 pt | `OrganizationName`, `DocumentTitle`, `DocumentSubtitle`, `DocumentVersion`, `DatePlace`, `Approval`, `ApprovalTitle`, `Preamble`, `ClauseContinuation`, `AttachmentLabel`, `FormLabel`, `Details`, `DetailsTitle`, `SignatureRole`, `SignatureLine`; tables `TableForm`, `TableParties`, `TableServices`, `TableSchedule`; image sizes `LogoSmall`, `Logo`, `IllustrationSmall`, `Illustration`, `IllustrationWide`; page number and count at the bottom |
| `std/styles/letter` | official letters | `business` | `LetterheadName`, `LetterheadDetails`, `OutgoingNumber`, `Recipient`, `LetterSubject`, `Salutation`, `Executor`; text `BodyIndented`; page `LetterFirst` (no number), numbers from the second page at the top centre |
| `std/styles/technical` | manuals, instructions, technical descriptions | `default`, Liberation Sans 10.5 pt; profile `report` | `ProgramOutput`, `StepResult`, `DefinitionTerm`, `DefinitionText`, character styles `Key`, `MenuItem`, `FileName`, `Command`, `Variable`; list `StepList`; table `TableRevisions`; numbered headings |
| `std/styles/report` | reports in science and technology | `default`, Liberation Serif 14 pt; profile `report` | `StructuralHeading`, `TitlePageText`, `TitlePageName`; page `ReportTitle` (no number); page number at the top right |
| `std/styles/compact` | memos, reference sheets, cheat sheets | `default`, Liberation Sans 9 pt | smaller font size, spacing and margins; two columns are set in the document with `\|section(cols=2)` (section 7.5) |

Parameters of the sets:

- `business` and `letter` follow DSTU 4163:2020 (documents of organizations): top and bottom margins 20 mm, left 30 mm, right 10 mm; paragraph indent 10 mm (`BodyIndented`); the addressee 90 mm from the left margin, the approval stamp 100 mm; no number on the first page of a letter. Contracts are not covered by the standard; its margins and indents are adopted as the usual practice of business documents.
- `report` follows section 7 of DSTU 3008:2015: Times New Roman (the metrically compatible Liberation Serif) 14 pt, 1.5 line spacing; margins at least 20 mm at the top and bottom, 25 mm on the left, 10 mm on the right; paragraph indent 12.5 mm (five characters); headings of sections and structural elements in bold capitals, numbers of sections and subsections without a final dot; the page number at the top right, not on the title page; the title of a table above it from the paragraph indent, the title of a figure below it in the centre; notes and footnotes 12 pt single-spaced, footnotes numbered within a page.

The Liberation fonts are metrically compatible with Times New Roman and Arial; another font is set by one line `defaults: {font: …}` of your own module.

## 12. Computation core

### 12.1. Status and use

The core has its own normative specification; its semantics are modelled on Starlark, the differences are listed in section 12.11. The syntax is a subset of the Python grammar: parsing is done by `ast.parse`, and only the allowed nodes are executed by the project's own interpreter. The specification does not depend on the implementation.

The core is used in expressions `|(…)`, command arguments, conditions and loops, `|code:` blocks, `|def` macros, the code section of the project and of styles modules.

Levels of code in markup:

| Level | Notation | Purpose |
| --- | --- | --- |
| expression | `\|(total * 1.2)` | output a value |
| content control | `\|if(cond){…} \|elif(cond){…} \|else{…}`, `\|for(x in items){…}` | a condition or a loop whose body is marked-up text |
| the same as an environment | `\|if(cond):` … `\|else:` … `\|endif`, `\|for(…):` … `\|endfor` | branches of several paragraphs |
| code block | `\|code:` … `\|end` | definitions, calculations, functions |
| variable from the text | `\|let(x=5)` | a definition along the text |
| macro with a content body | `\|def sign(role, name):` … `\|enddef` | user command |

The inline forms `|if(…){…}` (with `|elif`, `|else`) and `|for(…){…}` are allowed anywhere in a line of text and in a table cell; the bodies may contain markup. Spaces between `}` and `|elif`/`|else` belong to the construct and are not output. A paragraph consisting only of such forms and spaces that contains no content after evaluation is not output. The environments `|if(…):` and `|for(…):` stay block forms, including in the body of `|table` for conditional and repeated rows.

```
Поставка здійснюється протягом |(n) |if(n == 1){робочого дня}|else{робочих днів}.
|: Живлення |& |if(has("ac")){230|~В}|else{24|~В}
```

### 12.2. Syntax

| Group | Allowed |
| --- | --- |
| literals | `None`, `True`, `False`, integers (including `1_000`), fractional numbers, strings `'…'`, `"…"`, triple-quoted, `r"…"`, f-strings, lists, tuples, dictionaries |
| expressions | `+ - * / // % **`, unary `- +`, comparisons (including chains), `and`, `or`, `not`, `in`, `not in`, `is None`, `is not None`, `x if c else y` |
| access | indexing, slices, attributes, calls with positional and keyword arguments, `*args`, `**kwargs` |
| comprehensions | list and dictionary comprehensions, generator expressions |
| statements | assignment, unpacking, `+=` and the like, `if`/`elif`/`else`, `for`, `while`, `break`, `continue`, `pass`, `return` |
| functions | `def` with defaults, `*args`, `**kwargs`, keyword-only parameters; recursion |

Forbidden: `class`, decorators (except `@export` in the code of a fragment, section 10.4), type annotations, `import`, `from`, `try`, `except`, `raise`, `with`, `global`, `nonlocal`, `del`, `lambda`, `yield`, `async`, `await`, `:=`, `match`, set literals, `else` in loops. A forbidden construct is an error with its position.

### 12.3. Types

| Type | Description |
| --- | --- |
| `None` | no value |
| `bool` | `True`, `False` |
| `decimal` | a decimal number, exact, up to 64 significant digits, keeping the number of digits; an integer is a value with scale 0 (there is no separate `int` type) |
| `float` | a binary floating-point number (IEEE 754, double precision) |
| `str` | a string of Unicode characters |
| `list`, `tuple`, `dict` | as in Python; the order of a dictionary is the insertion order |
| `record` | an immutable record with dot access |
| `datetime` | a moment in time without a time zone, to the second; a date is the moment at 00:00:00 |
| `length` | a length with a unit (`10*mm`, `"10mm"`) |
| `content` | marked-up content (a macro body, the result of `markup(…)`) |
| `function` | a function or a macro |

A style has no type of its own: a style is a string with its name (section 11.4).

Lengths are written as a string `"10mm"` or as an expression with a constant: `10*mm`; the built-in constants are `mm`, `cm`, `pt`, `inch` (not `in`: it is a Python keyword). A literal `10mm` without quotes is not supported.

The type `length` stores a decimal value and the unit it was written in. Conversion between units uses fixed factors: 1 inch = 25.4 mm = 2.54 cm = 72 pt. The result of an operation with different units is in the unit of the left operand. The conversion uses `decimal` division (section 12.4), so the result may be a fraction with 28 significant digits; for output use `round(x.mm, 2)` and the formatting functions. `==` and `!=` compare with a tolerance of 0.001 mm (`72*pt == inch` is true); `<`, `<=`, `>`, `>=` take the same tolerance into account: `a < b` is true if `b - a` is greater than 0.001 mm. `str(x)` writes the value in its unit.

Operations of types:

- `type(x)` returns the type name from the table as a string: `"NoneType"`, `"bool"`, `"decimal"`, `"float"`, `"str"`, `"list"`, `"tuple"`, `"dict"`, `"record"`, `"datetime"`, `"length"`, `"content"`, `"function"`.
- `datetime` is a built-in class with overloaded operators. The representation model is `float64`: the integer part is days from the epoch 30.12.1899, the fraction is the time of day; an implementation may store an integer number of seconds if the observable results (comparison, hash, `float(dt)`, arithmetic) match the model after normalization to the second. A value is normalized to a whole second, so `==` and the hash are exact. The allowed range of years is 1–9999; time zones are not supported.
  - Constructors: `date(y, m, d)`, `datetime(y, m, d, h, mi, s)`, `datetime(serial)`, and also `date("YYYY-MM-DD")` and `datetime("YYYY-MM-DDTHH:MM[:SS]")` (parsing a string); a non-existent date and a string with a time zone are errors.
  - Attributes: `year`, `month`, `day`, `hour`, `minute`, `second`, `weekday` (1–7, Monday is 1).
  - `dt - dt` → `decimal` (days, possibly fractional): the exact number of seconds divided by 86400, with a precision of 28 significant digits; `dt + n` and `dt - n`, where `n` is `decimal` or `float`, add `n` days; the result is rounded to the second (half away from zero); `dt + dt`, `dt * n` are errors. Calendar shifts (`add_months`) and `weeks(n)`, `hours(n)`, `minutes(n)` (a number of days) are library functions (standard library, section 5): `dt + hours(36)`.
  - `float(dt)` is the serial number (days from the epoch); `datetime(serial)` is the inverse conversion.
  - `str(dt)` is ISO: `YYYY-MM-DD` if the time is 00:00:00, otherwise `YYYY-MM-DDTHH:MM:SS`.
- `length`: `+` and `-` with a `length`; `*` and `/` by a number (`decimal`, and a `float` after conversion to `decimal` by its shortest decimal notation, like `dec(x)`; `nan` and `inf` are errors; the result is a `length` in the unit of the operand); `length / length` → `decimal`; `length * length` is an error; comparisons; the attributes `x.mm`, `x.cm`, `x.pt`, `x.inch` → `decimal` (the value in that unit); converting a string: `length("10mm")`.
- `content` is opaque in the core; concatenation with `str` and `content` is defined together with `markup(…)` when the document is evaluated.
- `==` and `!=` between values of different types give `False`, except for numbers: `decimal` and `float` are compared by value after converting the `decimal` to `float` (`5 == 5.0` is true, section 12.4). `<`, `>`, `<=`, `>=` between different types and with `None` are errors.
- `in` for a `record` is an error; the presence of a field is checked with `hasattr(r, "name")`.
- Dictionary keys are immutable values: `None`, `bool`, `decimal`, `str`, `datetime`, and also `tuple` and `record` of such values. The hash of a `decimal` is determined by its value (`5` and `5.00` are one key). `float` and `length` as a key are an error.

### 12.4. Numbers

- An integer literal (`12`, `1_000`) and a literal with a dot without an exponent (`12.50`) are `decimal`; the number of digits is kept: `2.20` is output as «2,20», `12` as «12».
- A literal with an exponent (`1.5e3`) is a `float`.
- Explicit conversions: `dec(x)` to `decimal` (from `float` by the shortest decimal notation of the value: `dec(0.1)` → 0.1), `float(x)` to `float`, `int(x)` drops the fractional part (the result is a `decimal` with scale 0).
- The ceiling is 64 significant digits of the result of any operation; exceeding it is an error "number overflow". For `**` the estimate is made before the computation.
- Indexes, slices, `range(…)`, repetition (`"x" * n`, `[0] * n`) accept a number with an integral value (`2`, `2.0`); a fractional value is an error.
- `==` compares numbers by value, and the hash is determined by the value: `5 == 5.0`, `5 == 5.00`.

| Operands | Result |
| --- | --- |
| `decimal` and `decimal` | `decimal`; division `/` gives `decimal` (`7 / 2` → 3.5) |
| `decimal` and `float` | `float`: the `decimal` is converted to `float` automatically |
| `float` and `float` | `float` |

- The money functions of the library reject `float` (standard library, sections 3 and 4); the functions of `std/math` accept `decimal` and `float`.
- A `float` gets into the text of a document only rounded or through a formatting function; the linter warns about a `float` in `|(…)` (section 4.2).
- Rounding `round(x, n)` for `decimal` and `float` is mathematical: half away from zero (`round(2.5)` → 3, `round(-2.5)` → −3); for `float` by the decimal notation of the value (`round(2.675, 2)` → 2.68). `round(x)` without `n` returns a `decimal` with scale 0. This is the only rounding rule in the language. The precision of `decimal` division is 28 significant digits.
- Floor division `//` and the remainder `%` for `decimal` are computed with rounding down (`-7 // 2` → −4); the sign of the remainder is that of the divisor.
- `decimal ** negative integer` gives a `decimal` (`2 ** -1` → 0.5). `decimal ** decimal` with a fractional exponent is allowed, 28 significant digits.
- `bool` does not take part in arithmetic: `True + 1` is an error; the conversion is `int(True)`.
- `str(decimal)` writes the number without an exponent, keeping the number of digits: `"10"`, `"0.000001"`, `"2.20"`.

### 12.5. Strings

- A string is a sequence of Unicode characters (code points), like `str` in Python 3: `len("Київ") == 4`, `"Київ"[0] == "К"`; slices, iteration and methods work with characters, not bytes.
- NFC normalization is done at the lexical stage (section 2.1).
- Strings are immutable. f-strings support core expressions and Python format specifiers; locale formatting is done by the functions of the standard library.

### 12.6. Records

- `record` is an immutable record with fields: `r.name` and `r["name"]`. Field names are Unicode identifiers (section 3.9): `r.назва`; keys are normalized to NFKC, a conflict after normalization is an error.
- `load_csv`, `load_yaml`, `load_json` return records; nested structures are records and lists.
- YAML (file headers and `load_yaml`) is read by the YAML 1.2 core schema with two Primula rules: a number with a fractional part without an exponent is a `decimal` with the number of digits as written; an unquoted scalar of the form `YYYY-MM-DD` is a `datetime` (00:00:00), of the form `YYYY-MM-DDTHH:MM[:SS]` a `datetime` with time, and a non-existent date of this form (`2026-13-45`) is an error; a value with a time zone (`Z`, `+02:00`) is an error "time zones are not supported". Integers are `decimal` with scale 0; numbers with an exponent, `.inf`, `.nan` are `float`; a quoted scalar is always a string; booleans are only `true` and `false` (not `yes`, `no`, `on`, `off`).
- In `load_json` an integer and a number with a dot without an exponent are `decimal`; JSON has no dates.
- Constructor: `record(name="…", qty=3)`; a new record with changed fields: `r.replace(qty=4)`.
- A dictionary stays a dictionary, without dot access.
- Access to a missing field is an error; `getattr(r, "name", default)` returns the default value.
- In a track block of `|parallel` the records `track` and `segment` are available (section 7.7).

### 12.7. Semantics

- The global names of a document are lazy and immutable (section 10.4).
- The top-level statements of a code block, an `|import` module, a styles module and a project are divided into definitions and actions; the rules are the same for all kinds of files.
- Definitions: `name = expression`, unpacking into names (`a, b = …`), `def`, and also `|let`. They are registered lazily, evaluated at the first access and frozen. `x += …` at the top level is an error (a repeated definition).
- Actions are all other top-level statements (`for`, `if`, `while`, calls, for example `paragraph_style(…)`, `debug(…)`). They are executed in document order after all definitions have been collected and see any global names, including those defined further down in the text. Names bound inside an action (a loop variable, an assignment in `if`) are local to it and do not become global names.
- Order of phases: collecting definitions from the whole document and the inserted fragments; executing all top-level actions in document order (including in fragments); evaluating the markup. Actions in the bodies of `|for` and `|def` are executed in place, when the markup is evaluated.
- A conditional definition is written as a conditional expression: `rate = 20 if vat else 0`; an assignment in a top-level `if` creates no global name. The linter warns if a name assigned in an action is not used in it and suggests a conditional expression.
- Accumulating a value in a top-level loop (`rows.append(…)`) is an error of changing a frozen value; instead use a list comprehension (`rows = [it for it in items]`) or a function that builds and returns the value (`def build(): …` and `d = build()`). The error message suggests these forms.
- Inside functions variables are mutable, as in Python; a function sees the global names of its module or document read-only.
- Freezing: the value of a definition is frozen after it is computed, the value of a module after it is loaded; changing a frozen list or dictionary is an error.
- Default parameter values are computed when the function is defined and are frozen; changing them inside the function is an error.
- Determinism: no input/output except `load_*`; no random numbers; no access to the clock.
- Build date: `build_date()` returns the date the build started (a `datetime` with the time 00:00:00); it can be fixed — `--build-date 2026-10-12` or `build_date: 2026-10-12` in the project header — to rebuild a document without changes.

### 12.8. Limits

There are three limits. The defaults are set by the language version; a project may change them with the key `limits` (section 10.6):

| Limit | Key | Default | What it limits |
| --- | --- | --- | --- |
| time | `time` | 20 s | one evaluation: an expression, a code block or a chain of macro calls; the count starts anew for each evaluation |
| recursion | `recursion` | 500 | depth of function and macro calls, including `\|include` |
| value size | `size` | 10 000 000 | the length of a string (in characters) and the number of elements of a list, tuple, dictionary |

- The size is checked before a value is created, from the sizes of the operands: `[0] * n`, `"x" * n`, `range(n)`, `a + b` for lists and strings, `join`. A value that would exceed the limit is not created.
- The time of the whole build is limited by the command-line option `--timeout SEC` (section 14.1); by default the total time is not limited. The time limit depends on the machine and serves as a safeguard, not as part of the semantics.
- The language does not set a memory limit: the implementation limits the process (recommendation: 1 GiB); running out of memory is a build error of group `P0`.
- The use of the limits (the greatest call depth, the greatest value size, the longest evaluation time) is written to the build report (section 14.3).
- Exceeding a limit is an error with the call stack through macros and inclusions.

### 12.9. Errors and debugging

- `fail("message")` is a build error at the position of the call.
- `debug(x)` puts a value into the build report, not into the document.
- A runtime error contains the file, line, column and call stack, including through `|include`, `|import` and macros.

### 12.10. Built-in functions and methods

Functions: `len`, `range`, `enumerate`, `zip`, `sorted`, `reversed`, `min`, `max`, `sum`, `any`, `all`, `abs`, `round`, `int`, `float`, `dec`, `str`, `bool`, `list`, `tuple`, `dict`, `record`, `date`, `datetime`, `type`, `getattr`, `hasattr`, `repr`, `fail`, `debug`, `markup`, `build_date`.

String methods: `split`, `rsplit`, `splitlines`, `join`, `strip`, `lstrip`, `rstrip`, `replace`, `startswith`, `endswith`, `find`, `rfind`, `count`, `upper`, `lower`, `capitalize`, `title`, `isdigit`, `isalpha`, `isspace`, `zfill`, `format`.

`format`: only positional and named fields, with indexes `[0]`, `["key"]` and a format specification; attribute access in a format string (`{0.name}`) is an error, a record field is accessed by key: `"{0[name]}".format(r)`. Formatting with the `%` operator (`"%s: %d" % (name, n)`) is allowed.

List methods: `append`, `extend`, `insert`, `pop`, `remove`, `index`, `count`, `sort`, `reverse`. Dictionary methods: `get`, `keys`, `values`, `items`, `update`, `pop`, `setdefault`.

### 12.11. Differences from Starlark

| Question | Starlark | Primula |
| --- | --- | --- |
| Parsing | its own grammar | the Python grammar (`ast.parse`) |
| `while`, recursion | forbidden (by default) | allowed, protected by limits |
| `lambda` | yes | no |
| Numbers | `int` of arbitrary length and `float` | `decimal` (integers have scale 0, up to 64 significant digits) and `float`; `float` is a literal with an exponent and `float(…)`; mixing gives `float` |
| Fractional literals | `float` | `decimal` |
| `decimal`, `datetime`, `length`, `content`, `record` | no | built-in types |
| Strings | iteration forbidden; length in bytes or UTF-16 depending on the implementation | Unicode characters, NFC, iterable |
| f-strings | no | yes |
| Global names | sequential | lazy, immutable, visible in the whole document |
| Changing global values | allowed until the module is frozen | forbidden: a definition is frozen after it is computed |
| `round` | banker's rounding of `float` | half away from zero for all numbers |
| Loading modules | `load(…)` | `\|import(…)` in markup |

## 13. Standard library

The standard library is described in a separate document, `primula-stdlib-v1.1-draft.en.md` (the original is `primula-stdlib-v1.1-draft.ru.md`). It evolves and is versioned independently of this specification.

The contract binding on an implementation of the language:

- the prelude is the library functions available without loading; special modules are loaded explicitly: `|import("std/math")`; the names of library modules start with `std/`;
- the functions are deterministic, do no input/output (except the core's `load_*`) and take into account the document language (`uk`, `ru`, `en`), which is overridden by the argument `lang=`;
- the library dictionaries (currencies, units, case forms, months) are extended and overridden in a styles module with the functions `currency`, `unit`, `month_names`, `typography`;
- values that change by law (tax rates, the holiday calendar) are not built into the library;
- a file may require a minimum library version with the header key `primula: {stdlib: "1.1"}`; the library version is written to the build report (section 14.3);
- the result of a library function is the same for the same arguments and library version.

In the text of this specification, references like "standard library, section N" refer to the corresponding section of the library document.

## 14. Diagnostics, build report, modes

### 14.1. Command line

| Command, option | Purpose |
| --- | --- |
| `primula build file -o result.odt` | build a document or a project |
| `primula check file` | check without writing ODT |
| `primula check project.p.prml --dump-project` | JSON of the descriptive section of the project to standard output without executing code: `schema`, `file`, `root` (absolute path of the project root; for a project with `extends`, the root of the base), `name`, `language`, `styles`, `params` (type and default value), `keys`, `limits`, `build_date`, `targets` of the header (paths from the project root), `ref_documents` (name → `source`, `registry`), `doc_defaults` (metadata defaults), messages; targets from `build()` are not included; an invalid header gives exit code 2 |
| `primula check file --dump-structure`, `--dump-styles` | JSON for editors and Studio to standard output (`schema: 1`); messages go both to the error stream and into the object (`messages`). Structure (`structure`): `items` in document order — `heading` (`level`, `number`, `title`), `clause` (`level`, `number`, the beginning of the text `text`), `appendix` (`outline`, `designation`, `title`), `table`/`figure` with a caption or ID (`number`, `title`), `list` (numbered with `id=`), `admonition`/`section` with an ID, `parallel` (`id`, tracks: `id`, `lang`, `title`, `role`, `primary`, `numbered`, `optional`), `segment` (`id`, `span`, `status`) and `track_block` (track, segment, `status`, `rev`, the flags `stale` — the primary block changed after the confirmation, and `changed` — the block itself changed, section 7.7); elements inside a track have the field `track`; each has the full `id` (with the prefixes `ns.` and `part:`) or `null`, the position `file`, `path`, `line`, `column` and `part` — the scope of a part of a compound document; `includes` — the places of `\|include` and `\|document`: position, `target`, `ns`/`part`/`scope`. With `--dump-structure` the document parameters (`params`) are output too: the parameters of the project and of the document header in the order of declaration — `type`, `default` (the text of the value in the form of `--param NAME=VALUE`: a string as it is, `true`/`false`, a number, an ISO date) and `origin` (`project` or `document`; a document parameter replaces the project parameter of the same name). Styles (`styles`): `layers` (name, origin: `project`, `option` — `--style`, `header`, `default`, `document`), `defaults`, `styles` — `name`, `kind`, `parent`, `materialized`, `definitions` (the layer and position of each definition, `replace`), `own` (the value, layer and position of the definition of each property), `effective` (the value and the style of the chain it is taken from), `chain`. Values are as in a styles module (`"2mm"`, `"115%"`). A key is `null` if the phase was not run (an error before the structure). Both options together give one object; for a project file it is an error |
| `--overlay FILE=BUFFER` | only for `check`: the text of `FILE` is read from `BUFFER` (an unsaved editor buffer); the name, positions, messages and report refer to `FILE`; the option repeats; the argument is split at the last `=`; a non-existent buffer is an error. A reference registry (section 5.7) whose files are replaced by a buffer is considered outdated |
| `primula commands [--format text\|json] [--functions\|--header]` | reference of constructs: built-in commands (appendix 2.1), short forms (section 3.3) and closing markers (section 3.5) with arguments (name, type, default, description), forms of notation, a snippet to insert, a short description and the section of the specification; and also expression functions (`functions`): built-in functions and methods of the core (section 12.10), the prelude and `std/math` of the standard library, `load_*` (section 10.5), functions of styles code (section 11 and the settings of sections 4–9), functions of table formulas (section 6.8) and of the project (section 10.7) — with the signature, arguments, result type, a short description, the document and the section (specification or library), where the call is allowed, and an example; an example that does not need a document is evaluated by the translator in the language of the reference, the result is in the field `result`. Texts are in the message language (`--lang`). Keys of the YAML header (`header_keys`): the key path (`doc.title`, `doc_defaults.creator`, `targets[].source`), kinds of files, value type, allowed (`closed`) or suggested values, the "recommended" flag (`recommended`: in `doc` — `title`, `creator`, `language`, `created`, needed by a finished ODT; in a project's `doc_defaults` — `creator`, `organization`; the translator does not require them), description, section and example. `--functions` in the text form prints the list of functions, `--header` the list of header keys instead of the constructs. Used by the palette, hints, completion and help of Studio |
| `primula console [FILE] [--json] [--param NAME=VALUE…] [--project FILE\|--no-project]` | evaluator console — trying out code and library functions. The context is the names of FILE: a document or fragment (header parameters, `doc`, project, styles, definitions and actions of code without evaluating the text), a project file (parameters, `project`, the code section), a module (as after `\|import`), a styles module (its names and styles); without FILE, only the standard library. The module `std/math` is always loaded in the console under the name `math` (decision 130; a context name `math` is kept); in the text of a document `|import("std/math")` is still required. Input is Primula code (section 12): definitions are kept for later inputs, an input with definitions opens a new name level over the previous ones (a name can be defined again — only in the console), definitions are evaluated immediately; the value of the final expression is shown, `debug(…)` is the output of the input; limits (section 12.8) apply per input; `build()` registers no targets. Console commands (not code): `:help NAME`, `:functions [TEXT]`, `:vars`, `:reset`, `:context`, `:quit`. A line ending with `:` or with an open bracket continues up to a blank line. SIGINT interrupts the current input (P0006), names are kept. `--json` is the protocol for Studio: the first line `{"ready": true, "context": {kind, file, project, names}, "messages": […]}`, then for each line `{"input": "code"}` a line `{"ok", "value", "output", "messages", "text", "names"}`; `names` (also in the first line) are the names visible to the next input (decision 129): `{name, type, value, origin}`, first the names of inputs (`origin: "input"`, the latest level first), then of the context (`"context"`); `type` and `value` (at most 80 characters) only for computed names: a lazy definition of the context is not computed for the sake of the list (`type: ""`, `value: null`) |
| `primula parallel --stub FILE --track ID` | for segments without a block of track `ID` adds a block: a copy of the structure of the primary block (headings, clauses, list items, table rows, lines with a style, environment lines) with placeholders `\|?{…}` instead of the text, a paragraph as one placeholder; for a segment in the line form `\|track("ID"){\|?{…}}`; the file is rewritten in place, nothing else changes (section 7.7) |
| `primula parallel --stamp FILE --track ID [--segment ID…] [--status S]` | confirmation of a translation: writes the `rev` hashes of the current text of the primary block and of its own block to the blocks of track `ID`, with `--status` also the status; only these arguments change. Without `--segment` all blocks of the track are confirmed, and the command lists the confirmed segments, marking those that were outdated; `--segment` (repeated) confirms only the named segments. Running it again changes nothing |
| `primula parallel --check-status S FILE` | all blocks of non-primary tracks (except missing `optional` blocks) are in status `S` — their own or that of the segment — without outdated `rev`; otherwise a list and exit code 2. The `primula parallel` commands write the file only if the document has no errors and the file is in normal form (LF, NFC, no BOM); only the named file is rewritten, blocks from inserted fragments are listed and not changed |
| `primula export FILE [--to FORMAT] [-o OUTPUT] [--pandoc-arg ARGUMENT]…` | export of a document through the pandoc AST (decision 139): the document is evaluated as for `build` (values, conditions, fragments, numbering, captions, references, footnotes, tables) and written as pandoc JSON AST (`pandoc-api-version` 1.23); `--to json` writes the AST, other formats (`markdown`/`md`, `gfm`, `html`, `docx`, `latex`, `epub`, `rst`, `plain` and other pandoc writers) are produced by the installed pandoc. Headings with numbers and bookmark identifiers, `\|@` references become links to bookmarks with the computed text, footnotes become pandoc footnotes, tables come from the computed grid, captions become table and figure captions, the table of contents and lists become lists of links without page numbers, `doc.*` metadata become pandoc metadata; paragraph and character styles become `custom-style` attributes (for `docx`, `odt` and the AST). Page layout (page styles, columns, headers and footers, watermarks, page numbers, page references) is not exported — a warning once per construct. Without pandoc, formats other than `json` are an error; a pandoc error is passed on with its message. A paragraph is written as one line (`--wrap=none`), standalone HTML with a text width of 60em; `--pandoc-arg` (repeated) passes your own arguments to pandoc after those of the translator, for example `--pandoc-arg=-Vmaxwidth=none` or `--pandoc-arg=--reference-doc=template.docx`. The default output file is the source name with the extension of the format; nothing is written if the document has errors |
| `--project FILE`, `--no-project` | explicit project file; turning off the search (section 10.6) |
| `primula fmt file` | formatting; `--explicit-clauses` |
| `--strict` | warnings become errors |
| `--report file.json` | build report; for a project build, one report with a list of targets (section 14.3) |
| `--review` | variant check mode (section 9.2); the `status` of the blocks of `\|parallel` tracks is shown as a label at the start of the cell |
| `--build-date YYYY-MM-DD` | fixed build date |
| `--style FILE` | an additional styles module; the option repeats. Layers: project → `--style` (in the order given) → `styles` in the document header → document code (section 11.7). A `--style` given turns off the automatic loading of `std/styles/default`; if the built-in one is needed, it is given explicitly (`--style std/styles/default`). The path is relative to the current directory; a file outside the project root is allowed; paths and hashes go into the report (section 14.3) |
| `--timeout SEC` | time limit of the whole build (section 12.8) |
| `--unsafe` | permission to insert raw ODF XML |
| `--embed-sources` | embed the source files in the ODT (`Primula/sources/`) |
| `--no-embed-report` | do not embed the short report in the ODT |
| `--param NAME=VALUE` | a parameter of the root document (repeated). The value is a YAML scalar, as in `load_yaml`: `42` is `decimal`, `true`, `2026-10-15` is `datetime`, other text is a string; quotes are allowed. A string parameter gets the text as written (`--param номер=17` is the string «17»). A name declared neither in the document nor in the project and a value of another type are errors; in a project build `--param` is an error (target parameters are in `targets` and `build()`) |
| `--format text\|json` | message format: `text` (default, to the error stream) or `json` — one JSON array to standard output (fields in section 14.2), in a project build together with the messages of the targets; together with `--dump-*` it is an error (both write to standard output) |
| `--pdf [file]` | PDF export through LibreOffice (as in Kit); in a project build, PDFs of all targets next to the ODT; a file name and `-o` in a project build are an error |

Exit code: 0 — success, 2 — build error.

### 14.2. Messages

Each message contains a code, a severity (error or warning), the file, line, column and, for runtime errors, the call stack through inclusions and macros.

- Lines and columns are numbered from 1. A column is the number of the Unicode character (code point) in the line; a tab is one character. The position refers to the source file before NFC normalization. In the JSON report the position also contains the end of the range.
- The code is `P` and four digits; the first digit is the group: `P0` — command line, input/output, internal errors; `P1` — lexical structure and syntax; `P2` — names, evaluation, core, limits; `P3` — styles; `P4` — structure, numbering, IDs, references; `P5` — tables; `P6` — pages and graphics; `P7` — modules, project, data, build; `P8` — ODF generation; `P9` — technical documentation tools.
- The code does not depend on the message language and on the severity: `--strict` changes the severity, not the code. Codes are stable; a removed code is not reused. Message texts come from the catalogues en (main), uk, ru.
- Text format: `file:line:column: error[P1003]: text` (or `warning[…]`), then the source line with the underline `^^^`, notes with other positions (`note:`) and the call stack.
- JSON format (`--format json`, the messages of the report): an object per message — `code`, `severity`, `message`, `file`, `line`, `column`, the end of the range, `escalated` (a warning that became an error because of `--strict`), `notes` (text and position), `stack` (kind, name, text, position). The format is meant for editors and Studio.
- Core messages about function calls and command arguments are translated into the message language like the others; a text that has no translation is output in English.
- The list of codes is maintained by the prototype; before the v1.0 release it moves to a separate appendix "Diagnostic codes".

Warnings (errors with `--strict`):

- a placeholder `|?{…}` left in;
- direct formatting `|fmt`;
- a `decimal`, `float`, `datetime` or `length` in `|(…)` without a formatting function;
- a long environment closed by an anonymous `|end`;
- an ordinary line right after a line command (section 3.4);
- the text of a numbered heading starts with a number;
- `auto` columns do not fit; font metrics are approximate;
- an export conflict in the `on_conflict` modes `first`/`last`;
- `danger` or `warning` without `hazard`; `hazard` in `note`/`tip`; a definition of `admonition` in a styles module; `|if` with definitions in `--review` mode; `first="short"` without `|list_of("abbr")`; a list of abbreviations without definitions (group `P9`);
- `styles` in the header of a `|document` part (group `P7`);
- a mismatch between the key `kind` and the sub-extension of the file (group `P7`, section 2.2);
- an identifier that mixes alphabets and a pair of identifiers that differ in homoglyphs (section 3.9);
- no track block in a segment, track mismatches by the `parity` profile, a translation that is outdated or changed after the confirmation, track footnotes numbered by Writer (group `P5`, section 7.7).

### 14.3. Build report

The JSON report contains: the language and translator versions; the standard library version; the list of source files (including styles modules loaded with `--style`, with paths and hashes) and the hashes of the data read; the variables and parameters used; the parameters of the variant and the conditions that applied; the computed column widths; the materialized styles; the use of limits; the messages; the flag `review: true` in check mode. The build report of a project contains information about the project (file, parameters, keys) and the list of targets: `source`, `output`, the outcome, messages and the nested report of the target.

- The full report is written only to an external file (`--report file.json`).
- By default a short report `Primula/report.json` is embedded in the ODT (with an entry in the manifest): the language and translator versions, the source files with relative paths and hashes (a `--style` file outside the project root by its name without the directory, and its hash), the names of the variant parameters without values, the materialized styles, the use of limits, the warnings. It contains no values of parameters and variables and no `debug` output: they may contain prices, requisites, personal data and data of branches not chosen. `--no-embed-report` turns off embedding.
- Source files (document, fragments, modules, data) are embedded only with `--embed-sources`, in `Primula/sources/` with paths relative to the project root.
- The embedded parts contain no absolute paths. Writer ignores these parts and removes them when saving.
- References to other documents of the project (section 5.7) are listed in the report: the ID, the document, the origin of the text (`computed` or `registry`) and the path of the registry. The reference registry `*.refs.json` is a separate build file (not part of the ODT): schema, translator version, name and path of the document, SHA-256 of the project files read, targets.

## 15. Mapping to ODF

| Construct | ODF elements |
| --- | --- |
| paragraph | `text:p` with an automatic style whose parent is a named style |
| heading | `text:h` with `text:outline-level`; the number is computed text; a bookmark |
| clause | `text:p` with a computed number and a bookmark |
| list | `text:list` with the style `text:list-style` |
| table | `table:table`, `table:table-column` with computed widths; spans — `table:number-columns-spanned`, `table:number-rows-spanned`, `table:covered-table-cell` |
| cell value | `office:value-type`, `office:value`; a Writer formula only with `live=True` |
| page style | `style:page-layout` and `style:master-page`; a change — `style:master-page-name` in the style of the first paragraph or table |
| section with columns | `text:section` with `style:columns` |
| parallel tracks | `table:table` of the style `ParallelTable`: a row per segment, a cell per track (section 7.7) |
| headers and footers | `style:header`, `style:footer`, `style:header-left`, `style:header-first` and so on |
| fields | `text:page-number`, `text:page-count`, `text:chapter`, `text:title`, `text:bookmark-ref` |
| image, figure, frame | `draw:frame` with `draw:image` or `draw:text-box`; the caption inside the frame |
| watermark | a frame behind the text with an SVG image (a text mark) or the given image, anchored in the header of the master page |
| footnotes | `text:note` (`footnote`, `endnote`) |
| table of contents | `text:table-of-content` over the marks `text:toc-mark` |
| lists of figures and tables | `text:user-index` over the marks `text:user-index-mark` |
| alphabetical index | `text:alphabetical-index` over the marks `text:alphabetical-index-mark` |
| list of abbreviations | generated text (there is no separate ODF index) |
| cross reference | text with `text:a` to a bookmark; the `page` mode — `text:bookmark-ref` |
| styles | `office:styles` (named), `office:automatic-styles` (cascade) |
| metadata | `meta.xml` |

The document language: `doc.language`, otherwise the project's `doc_defaults.language`, otherwise the project's `language`, otherwise `defaults.language` of the styles modules, otherwise `uk-UA`. It is written to the default style of the ODT (`fo:language`, `fo:country`) and to `dc:language`; quotation marks (section 4.2) and the library functions (section 13) depend on it.

Mapping of the `doc` keys (and the project's `doc_defaults`) to the elements of `meta.xml`:

| Key | `meta.xml` |
| --- | --- |
| `title`, `subject`, `description` | `dc:title`, `dc:subject`, `dc:description` |
| `creator` | `meta:initial-creator` and `dc:creator` |
| `language` | `dc:language` |
| `keywords` (a string or a list) | `meta:keyword`, one per word |
| `created` | `meta:creation-date` (`datetime`: a date without time → `YYYY-MM-DDT00:00:00`); if not given, the build date |
| `modified` | `dc:date`; if not given, the build date |
| `organization`, `identifier`, `revision`, `status` | `meta:user-defined meta:name="<key>"` (in Writer, "Properties → Custom Properties") |

`meta:generator` is `Primula Documenting System/<version>`. There are no other dates and no random identifiers in the ODT, and the time of the ZIP entries is fixed: with the same source data and build date the file is identical byte for byte.

## Appendix 1. Grammar (EBNF)

The grammar of the lexical structure and the markup is written in the W3C EBNF notation (XML 1.0, section 6). The computation core is given by reference to the Python grammar with the whitelist of nodes of section 12. Restrictions that the grammar does not express are marked `[C: …]` and are normative. The same text is supplied as a separate file `primula-grammar-v1.1.ebnf` for tools; the comments of the grammar are in English.

```ebnf
/* ==========================================================================
   Primula — grammar of the lexical structure and markup, v1.1-draft
   Date: 2026-10-14. Primula Documenting System (primula-docs);
   file extension .prml (sub-extensions .f .m .s .p); internal working
   name: ngml.

   Notation: W3C EBNF as defined in XML 1.0 (Fifth Edition), section 6:
     Name ::= expr        rule
     "x" 'x'              literal
     [a-z] [^a-z]         character class / negated class
     #xN                  character by code point
     A?  A*  A+           optional, zero or more, one or more
     A | B                alternative
     A - B                A that does not match B
     slash-asterisk ... asterisk-slash   comment (comments do not nest)
   [C: ...] marks a constraint that the grammar cannot express and that
   the translator checks after parsing; the constraint text is normative.

   The computing core (expressions, arguments, code blocks) is a subset of
   the Python grammar restricted by the node whitelist of the core
   specification (spec section 12). Those parts are referenced here as
   opaque nonterminals:
     PyExpr       Python expression
     PyArgs       Python call arguments (positional, key=value, *a, **k)
     PyParams     Python function parameters
     PyTarget     Python for-loop target
     PyStatements Python statements (block of code)
     PyString     Python string literal
   They are parsed with ast.parse; bracket and string nesting inside them
   follows Python rules, so a ')' inside a string does not end the args.

   Preprocessing before this grammar applies (spec sections 2 and 3):
     1. decoding UTF-8, line ends normalised to LF (#xA);
     2. Unicode normalisation NFC;
     3. the YAML header (if any) is split off.
   Names written by the author are compared after NFKC normalisation
   (spec section 3.9); the Unicode version is fixed by the language
   version.
   ========================================================================== */


/* --------------------------------------------------------------------------
   1. File
   -------------------------------------------------------------------------- */

File          ::= Header? Body
Header        ::= "---" EOL YamlLine* "---" EOL
                  /* [C: the header starts at the first line of the file;
                      its content is YAML 1.2 data, no expressions] */
YamlLine      ::= ( [^#xA]* - "---" ) EOL

Body          ::= Block*
                  /* [C: for kind: project the body is PyStatements,
                      not markup] */

EOL           ::= #xA
WS            ::= ( #x20 | #x9 )
Indent        ::= WS*
BlankLine     ::= Indent EOL
LineEnd       ::= WS* Comment? EOL
                  /* end of a command line: optional spaces and a
                     line comment (decision 34) */


/* --------------------------------------------------------------------------
   2. Names
   -------------------------------------------------------------------------- */

XidStart      ::= [A-Za-z] | [#x80-#x10FFFF]
                  /* [C: the code point has the Unicode property
                      XID_Start (UAX #31); the Unicode version is fixed
                      by the language version] */
XidContinue   ::= XidStart | [0-9] | "_" | [#x80-#x10FFFF]
                  /* [C: the code point has the property XID_Continue] */
Ident         ::= XidStart XidContinue*
                  /* [C: names are compared after NFKC normalisation,
                      case is significant; built-in commands and the
                      predefined header keys are ASCII] */
Name          ::= Ident ( "." Ident )*
                  /* command name; dots separate module names */
StyleName     ::= XidStart ( XidContinue | "-" )*
                  /* style name; may contain '-' (#x2D).
                     Used only after '|.' and in '|end.' */
Args          ::= "(" PyArgs ")"
                  /* [C: no whitespace between a name and '(';
                      the arguments may span several lines: a line break
                      inside the brackets does not end a line form;
                      the same holds for '|(' and '|='] */
Expr          ::= "|(" PyExpr ")"
                  /* [C: the arguments of commands are core expressions
                      evaluated in the evaluation phase; only path, part
                      and key of |include must be known when the tree is
                      built (spec sections 3.2, 3.6, 10.2)] */


/* --------------------------------------------------------------------------
   3. Blocks (line level)
   A block construct starts at the beginning of a source line after
   optional indentation. A line form ends at the end of the source line;
   there is no other line mode.
   [C: the key 'lines' in the header 'primula:' is an error; a comment-only
       line is removed before boundaries are determined]
   -------------------------------------------------------------------------- */

/* [C: the alternatives of Block are an ordered choice (as in PEG): the
    first alternative that matches the line wins. A long command at the
    start of a line is a LineCommand only when the line ends after its
    arguments or continues with the ':' forms; otherwise the line is text
    and the command is inline (for example '|img("a.png") у тексті')] */

Block         ::= BlankLine
                | LineComment
                | CommentBlock
                | VerbatimBlock
                | CodeBlock
                | Heading
                | Clause
                | ListItem
                | Admonition
                | ParagraphStyle
                | TableRow
                | IfBlock
                | ForBlock
                | DefBlock
                | ParallelBlock
                | LineCommand
                | Paragraph

Paragraph     ::= TextLine+
                  /* consecutive text lines form one paragraph;
                     a single EOL inside a paragraph is a space */
TextLine      ::= Indent Inline+ EOL
                  /* tried after all other Block alternatives */

LineComment   ::= Indent "|%" [^#xA]* EOL
                  /* a line consisting only of a comment disappears */


/* 3.1 Headings, clauses, list items, admonitions ------------------------- */

Heading       ::= Indent "|" "<"+ Args? WS+ Inline+ EOL
                  /* [C: the level is the number of '<' (1..6), or, with a
                      single '<', the argument level=N (1..6), a core
                      expression evaluated in the evaluation phase; both
                      at once is an error. '|>', '|-', '|#' have no level
                      argument. Always ends at the end of the source
                      line] */

Clause        ::= Indent "|" ">"+ Args? ( LineBody | EnvBody CloseClause )
                  /* level = number of '>'.
                     [C: implicit clause region (spec section 3.6): all
                      following blocks belong to the clause except those
                      that close it: a Paragraph or ParagraphStyle, a
                      Heading, a Clause of the same or higher level, the
                      structural and page commands page, newpage, section,
                      appendix, scope, document, toc, list_of, header,
                      footer, an IfBlock or ForBlock that has a Heading or
                      a Clause of the same or higher level at its top
                      level, the end of the enclosing environment or file.
                      |include is transparent: the blocks of the fragment
                      are treated as if they stood in its place] */

ListItem      ::= Indent "|" ListMarker Args? WS+ Inline+ EOL
                  /* [C: the prefix characters of the marker must match
                      the types of the parent items; mixing bullet and
                      numbered items on one level of one list and skipping
                      a level are errors] */
ListMarker    ::= [#x2D#x23]+
                  /* characters '-' and '#'; length = level,
                     the last character = item type:
                     '-' bullet, '#' numbered */

Admonition    ::= Indent "|!" Args ( LineBody | EnvBody CloseAdm )
                  /* first positional argument = kind:
                     danger | warning | caution | notice | note | tip.
                     [C: implicit region as for Clause] */

ParagraphStyle ::= Indent "|." StyleRef Args? ( ColonLineBody | EnvBody CloseStyle )
                  /* '|.Note: текст' or '|.Note:' ... '|end.Note' */
StyleRef      ::= StyleName | "(" PyExpr ")"


/* 3.2 Bodies ------------------------------------------------------------- */

LineBody      ::= WS+ Inline+ EOL
                  /* single-line form */
EnvBody       ::= ":" LineEnd Block*
                  /* environment form: ':' at the end of the line */
ColonLineBody ::= ":" WS+ Inline+ EOL
                  /* line form of a long command: '|name: text'
                     [C: recognised only when the command is the first
                      thing on the line; elsewhere ':' is text.
                      A literal colon after such a command is written
                      after an empty separator: '|name|;: text'] */


/* 3.3 Closing environments ----------------------------------------------- */

Close         ::= Indent "|end" ( CloseTag )? LineEnd
CloseTag      ::= ">"+                     /* clause of that level */
                | "!"                      /* admonition */
                | "." StyleName            /* paragraph style */
                | WS+ Name                 /* named environment */
CloseClause   ::= Close
CloseAdm      ::= Close
CloseStyle    ::= Close
                  /* [C: '|end' without a tag closes the nearest open
                      environment; with a tag the tag must match it.
                      Canonical names: '>' = clause, '!' = admonition,
                      '|end clause' closes the nearest clause of any
                      level, '|end>', '|end>>' ... check the level;
                      '.Name' or 'style' = paragraph style.
                      A closing marker always occupies a whole line.
                      Gluing 'end' to an arbitrary name is not allowed;
                      only '|endif', '|endfor', '|enddef' exist.
                      '|end' and '|end name' never close |if, |for, |def;
                      if the nearest open construct is one of them, an
                      anonymous '|end' is an error] */


/* 3.4 Long line commands and environments --------------------------------- */

LineCommand   ::= Indent "|" Name Args? ( LineEnd
                                        | ColonLineBody
                                        | EnvBody Close )
                  /* examples: |page("Landscape"):  ...  |end page
                               |list("LetterList")
                               |newpage
                               |include("fragments/warranty.f.prml")
                               |table(...):  rows  |end table
                     [C: '|end name' must name the command] */


/* 3.5 Tables --------------------------------------------------------------
   Inside '|table(...):' ... '|end table' only these blocks are allowed:
   TableRow, Row environments ('|row:'), '|caption:' environment,
   IfBlock, ForBlock, CodeBlock, '|include' (the inserted blocks are
   subject to the same restrictions), comments and blank lines.
   Inside '|row:' ... '|end row' '|include' may insert cells.
   [C: '|let' and '|set' in a table or row body are errors]            */

TableRow      ::= Indent "|:" Args? Cells EOL
Cells         ::= ( WS* Cell )*
Cell          ::= ( "|&" Args? )? CellContent
                  /* the first cell has no '|&' unless it carries
                     arguments: '|:|&(span=3) Разом'.
                     [C: '|&' directly after '|:' (or after the row
                      Args), without white space, belongs to the
                      first cell; '|: |& Б' — with a space — starts
                      with an empty first cell] */
CellContent   ::= ( Inline - "|&" )*
Formula       ::= "|=(" PyExpr ")"
                  /* [C: allowed only in a table cell] */


/* 3.5a Parallel tracks (spec section 7.7) ---------------------------------
   Inside '|parallel(...):' ... '|end parallel' only these blocks are
   allowed: SegmentBlock, IfBlock, ForBlock, CodeBlock, '|include' (the
   inserted blocks are subject to the same restrictions), comments and
   blank lines.                                                           */

ParallelBlock ::= Indent "|parallel" Args? ":" LineEnd ParallelItem* Close
                  /* [C: '|end' or '|end parallel'; at least two tracks] */
ParallelItem  ::= BlankLine | LineComment | CommentBlock | SegmentBlock
                | IfBlock | ForBlock | CodeBlock | LineCommand
                  /* [C: LineCommand only '|include'; IfBlock, ForBlock and
                      included blocks contain only ParallelItem] */

SegmentBlock  ::= Indent "|segment" Args? ( ":" LineEnd SegmentBody Close
                                          | ( WS+ TrackInline )+ EOL )
SegmentBody   ::= ( BlankLine | LineComment )* TrackBlock+
                | Block*
                  /* [C: Block* only with span="all", TrackBlock otherwise;
                      the forbidden commands of spec section 7.7 are
                      errors in both; '|end' or '|end segment'] */
TrackBlock    ::= Indent "|track" Args ":" LineEnd Block*
                  /* [C: a track block ends before the next TrackBlock or
                      before the close of the segment; the implicit clause
                      region (spec section 3.6) ends there too] */
TrackInline   ::= "|track" Args InlineBody
                  /* the body is the inline markup of one paragraph */


/* 3.6 Control constructs -------------------------------------------------- */

IfBlock       ::= Indent "|if(" PyExpr ")" EnvBody ElseEnv* Indent "|endif" LineEnd
ElseEnv       ::= Indent ( "|elif(" PyExpr ")" | "|else" ) ":" LineEnd Block*

ForBlock      ::= Indent "|for(" PyTarget WS+ "in" WS+ PyExpr ")"
                  EnvBody Indent "|endfor" LineEnd
                  /* block forms are environments only; '|if(c){...}' and
                     '|for(...){...}' at the start of a line are inline
                     forms (InlineIf, InlineFor) inside a Paragraph or a
                     table cell */

DefBlock      ::= Indent "|def" WS+ Ident "(" PyParams ")" ":" LineEnd
                  Block* Indent "|enddef" LineEnd
                  /* user command (macro); the body is markup and is
                     passed to the function as parameter 'body' */

LetCommand    ::= "|let(" PyArgs ")"
                  /* [C: 'export' and 'override' are reserved keyword
                      arguments of |let] */


/* 3.7 Code, comments, verbatim --------------------------------------------- */

CodeBlock     ::= Indent "|code:" LineEnd CodeLine* Indent "|end" LineEnd
CodeLine      ::= ( [^#xA]* - ( Indent "|end" WS* Comment? ) ) EOL
                  /* the lines form PyStatements; '|' is not markup
                     inside a code block.
                     [C: the indentation of the opening line (the same
                      prefix, character by character) is removed from
                      every line; a non-empty line with a smaller or
                      different indentation is an error. The same rule
                      applies to VerbatimBlock] */

CommentBlock  ::= Indent "|comment:" LineEnd Block* Close
                  /* only environment balance is checked inside */

VerbatimBlock ::= Indent "|verbatim" ( "(end=" PyString ")" )? ":" LineEnd
                  VerbatimLine* EndMarker
VerbatimLine  ::= [^#xA]* EOL
                  /* [C: the block ends at the first line equal to the
                      end marker; default marker is '|end'; the end
                      marker is compared literally, no comment may follow
                      it] */
EndMarker     ::= Indent [^#xA]+ EOL


/* --------------------------------------------------------------------------
   4. Inline level
   -------------------------------------------------------------------------- */

Inline        ::= Text
                | Escape
                | Expr
                | Formula
                | InlineIf
                | InlineFor
                | InlineShort
                | StyleSpan
                | Reference
                | InlineCommand
                | Comment

Text          ::= TextChar+
TextChar      ::= [^|#xA]
                  /* '{' and '}' are text outside bodies;
                     inside InlineBody they must be balanced */

Escape        ::= "||"          /* literal '|'                 */
                | "|{" | "|}"   /* literal braces              */
                | "|;"          /* empty separator             */
                | "|~"          /* no-break space              */
                | "|\"          /* line break inside paragraph */

Comment       ::= "|%" [^#xA]*  /* to the end of the line      */

InlineIf      ::= "|if(" PyExpr ")" InlineBody InlineElse*
InlineElse    ::= WS* ( "|elif(" PyExpr ")" InlineBody | "|else" InlineBody )
                  /* whitespace between '}' and '|elif' / '|else' belongs
                     to the construct and is not output.
                     [C: a paragraph consisting only of InlineIf,
                      InlineFor and whitespace that is empty after
                      evaluation is not output] */
InlineFor     ::= "|for(" PyTarget WS+ "in" WS+ PyExpr ")" InlineBody

InlineShort   ::= "|" InlineMark Args? InlineBody
InlineMark    ::= "*"   /* bold                    */
                | "/"   /* italic                  */
                | "_"   /* underline               */
                | "^"   /* superscript             */
                | ","   /* subscript               */
                | "`"   /* monospace               */
                | '"'   /* quotes of the language  */
                | "?"   /* draft placeholder       */
                | #x2014 /* strikethrough: em dash U+2014, "|—{…}" */

StyleSpan     ::= "|." StyleRef Args? InlineBody
                  /* character style */

Reference     ::= "|@" Args
                  /* |@("id"), |@("id", "label"|"title"|"page") */

InlineCommand ::= "|" Name Args? InlineBody?
                  /* examples: |img("logo.png", height="8mm")
                               |footnote{текст}
                               |field.page
                     [C: a letter directly after a command name needs the
                      empty separator '|;'] */

InlineBody    ::= "{" BodyItem* "}"
BodyItem      ::= Inline | "{" BodyItem* "}" | EOL
                  /* may span lines; braces are counted by balance */


/* --------------------------------------------------------------------------
   5. Character after '|'
   -------------------------------------------------------------------------- */

ShortChar     ::= [#x21-#x2F#x3A-#x40#x5B-#x60#x7B-#x7E] | [#x80-#x10FFFF]
                  /* [C: ASCII punctuation, or a single code point of the
                      Unicode general category P* or S*; the Unicode
                      version is fixed by the language version] */

/* [C: the character after '|' decides the construct by syntax alone:
       '|'                 literal
       XidStart            long command
       '('                 expression
       ShortChar           short form; a short form that is not defined is
                           an error (this includes the em dash U+2014,
                           category Pd, defined as strikethrough)
       space, end of line, digit, control character, other categories
                           error
       Reserved short forms: '|$', '|[', '|]' and any other P*/S*
       character not listed in spec section 3.3] */


/* --------------------------------------------------------------------------
   6. Reserved names
   [C: user definitions (|def, |let, code) may not use:
       if elif else endif for endfor def enddef let code end comment
       verbatim, Python keywords, names of built-in commands.
       Built-in command names (table, page, newpage, newcolumn, section,
       header, footer, img, figure, frame, include, import, document,
       part, scope, appendix, toc, list_of, footnote, endnote, set,
       block, list, row, cell, caption, field.*, watermark, abbr, index,
       export, fmt, call) are not overridable; library functions of style
       modules (for example admonition) are overridable]
   -------------------------------------------------------------------------- */
```

## Appendix 2. Built-in commands and reserved names

The complete list of short forms is in section 3.3.

### 2.1. Built-in commands

`table`, `row`, `cell`, `caption`, `page`, `newpage`, `newcolumn`, `section`, `header`, `footer`, `field.page`, `field.pages`, `field.chapter`, `field.title`, `img`, `figure`, `frame`, `watermark`, `include`, `import`, `document`, `part`, `scope`, `appendix`, `parallel`, `segment`, `track`, `toc`, `list_of`, `footnote`, `endnote`, `set`, `block`, `list`, `fmt`, `abbr`, `index`, `link`, `toc_entry`, `export`, `let`, `call`, `code`, `comment`, `verbatim`, `if`, `elif`, `else`, `for`, `def`.

Built-in commands cannot be redefined. Library functions of styles modules (for example, `captions`) can be redefined.

### 2.2. Reserved names

User definitions (`|def`, `|let`, code) cannot use the names: `if`, `elif`, `else`, `endif`, `for`, `endfor`, `def`, `enddef`, `let`, `code`, `end`, `comment`, `verbatim`, Python keywords, names of built-in commands. `export` and `override` are service arguments of `|let`.

## Appendix 3. Differences from ODT Markdown Kit 0.4 and conversion rules

| Kit 0.4 (Markdown + YAML) | Primula |
| --- | --- |
| `# Заголовок`, `## …` | `\|< Заголовок`, `\|<< …` |
| `{#id number=true}` in a heading | `\|<(id="id", number=True)` |
| paragraph, blank line | unchanged |
| `**ж**`, `*к*`, `` `код` `` | `\|*{ж}`, `\|/{к}`, ``\|`{код}`` |
| `~~закреслений~~` | `\|—{…}` (character style `StrikeText`) |
| `[текст]{cstyle="X"}` | `\|.X{текст}` |
| `::: {pstyle="X"}` … `:::` | `\|.X:` … `\|end.X`; around a clause `\|>(…, style="X")`, around a heading `\|<(…, style="X")` |
| `[текст](url)` | `\|link("url"){текст}` |
| `columns: [52, 48]` of a table preset | `cols: ["52%", "48%"]` of a table style |
| `transparent` | `transparent` or `none` |
| `::: {bstyle="X"}` … `:::` | `\|block("X"):` … `\|end block` |
| `- пункт`, `1. пункт` | `\|- пункт`, `\|# пункт` |
| `::: {list="X"}` | `\|list("X")` before the list, the environment `\|list("X"):` … `\|end list` or `\|set(list="X")` |
| `list-id`, `start`, `continue` | `\|#(id=…, start=…)`, `\|#(continues=…)` |
| `::: {table="X"}` + a pipe table | `\|table(style="X"):` with rows `\|:` and `\|&`; alignment `:---:` → `col(align=…)` |
| `::: {clause id="x"}` | `\|>(id="x"):` … `\|end>` |
| `[[ref:x]]`, `[[ref:x\|label]]`, `[[ref:x\|title]]` | `\|@("x")`, `\|@("x", "label")`, `\|@("x", "title")` |
| `::: {scope="a" prefix="А"}` | `\|scope("a", prefix="А"):` |
| `[[toc]]` | `\|toc()` |
| `break-before="page"` | `\|newpage` |
| `![alt](шлях){image="X"}` | `\|img("шлях", alt="alt", style="X")` |
| `{{var.x}}`, `var:` in the front matter | `\|(x)`, `params:` in the header |
| `{{document.title}}` | `\|(doc.title)` |
| `{{include: f.md}}` | `\|include("f.f.prml")` |
| `::: {comment}` | `\|comment:` … `\|end` |
| `\{{…}}`, `1\.` (escaping) | not needed: Markdown characters are ordinary text |
| style YAML (`line-height`, `space-after`) | a styles module (`line_height`, `space_after`) |
| `--styles` + `--styles-override` | the ordered list `styles` in the project, the repeatable option `--style`, layers without a limit on their number |
| `style-mode: legacy/cascade` | cascade only |
| `numbering.headings` (off by default) | heading numbering is on by default |
| `DraftPlaceholder` | `\|?{…}` |

The converter `primula convert file.md` translates a Kit document into Primula by this table; constructs without an unambiguous counterpart are marked with the comment `|% TODO`.

## Appendix 4. Decision log and open questions

### 4.1. Key decisions

| Area | Decision |
| --- | --- |
| Control character | `\|`; `\|\|` is a literal |
| Modes | text with commands plus blocks of pure code |
| Lightweight layer | none; the markup is entirely command-based, frequent commands have short forms |
| Core | a subset of Python, its own interpreter on `ast`, semantics modelled on Starlark |
| Levels of abstraction | semantic constructs, named styles, direct ODF properties |
| Heading, clause, lists | `\|<`, `\|>`, `\|-`, `\|#`; the level by repeating the character |
| Boundary of a line form | the end of the source line; there is no `para` mode |
| List in a clause | the implicit clause scope; an environment is an equivalent explicit form |
| Closing environments | `\|end`, `\|end>`, `\|end!`, `\|end.Ім'я`, `\|endif`, `\|endfor`, `\|enddef`, `\|end name` |
| Tables | `\|:`, `\|&`, `\|=`; compact and expanded forms; `span`, `rows`; `auto` columns with ranges; formulas in the order of dependencies |
| Pages | `\|page` (a switch and an environment), `\|newpage`, `\|newcolumn`, `\|section`, `\|header`, `\|footer`, fields `\|field.…` |
| Graphics | `\|img`, `\|figure`, `\|frame`; the parameters describe the frame; `wrap` without a side |
| Files | extension `.prml`, sub-extensions `.f`, `.m`, `.s`, `.p`; `kind` takes precedence |
| Names | Unicode identifiers of the author (UAX #31, NFKC); built-in commands and header keys are ASCII |
| Modules | `\|include`, `\|import`, `\|document`; isolation of fragments, explicit export |
| Project | YAML header and code; batch build `build()` |
| Styles | styles module (YAML and code), `parent`, underscores in property names, spacing variants, cascade, `\|set`, layers with overriding (including `--style`); a style is a string with a name |
| Structure | profiles `business` (DSTU 4163:2020) and `report` (DSTU 3008:2015); heading numbering on; references with modes; table of contents by marks; footnotes |
| Technical documents | `\|!` (6 kinds), `when=`, `--review`, key map, abbreviations, index |
| Numbers | `decimal` for integer and fractional literals without an exponent (up to 64 significant digits), `float` with an exponent; mixing gives `float`; date and time — `datetime` |
| Strings | Unicode characters, NFC |
| Limits | time, recursion, value size; memory at the process level |
| Library | the prelude and `std/…`; the contract form of an amount; rates and the calendar are project data; described in a separate document |
| Language of the specification | Russian; translation into Ukrainian and English after stabilization |

### 4.2. Decisions taken during consolidation

| No. | Discrepancy | Decision |
| --- | --- | --- |
| 1 | style names with a hyphen | after `\|.` and in `\|end.` a style name with a hyphen; since version 1.1 a Unicode identifier with a hyphen (decision 102) |
| 2 | `\|break` is a Python keyword | `\|newpage`, `\|newcolumn` |
| 3 | `col` is both a column description and a formula function | the formula function is `column(c, rows=…)` |
| 4 | page styles and headers/footers in a document | allowed as the last style layer |
| 5 | page numbering parameters | `number_format`, `restart` everywhere |
| 6 | `doc.number` | `doc.identifier` |
| 7 | module header | optional; for a styles module, by the styles schema |
| 8 | `styles:` a string or a list | a list; a string is a shorthand |
| 9 | `pstyle` in tables | `paragraph` |
| 10 | `\|caption:` in a table | allowed in the table environment |
| 11 | declaring the line mode | in the header: `primula: {lines: para}` — withdrawn by decision 107 (the `para` mode removed) |
| 12 | `export`, `override` in `\|let` | reserved service arguments |
| 13 | place of `\|watermark` | a document command and a styles module function |
| 14 | column type `money` | `decimal`, output `num(x, 2)`, `currency=` |
| 15 | `\|img(key=…)` | a path or `key=`, exactly one of the two |
| 16 | applying a block style was not defined | `\|block("Ім'я"):` and the argument `block=` |
| 17 | the style of a single list | the command `\|list("Ім'я")` before the list (applies to the nearest list) and the environment `\|list("Ім'я"):` … `\|end list`; `\|#(style=…)` is not used |
| 18 | strikethrough from Kit (`~~…~~`) | the short form `\|—{…}` (em dash U+2014; the character is available from the Studio palette), formatting — the character style `StrikeText`; since version 1.1 `—` is an ordinary case of the class `P*`/`S*` (decision 101) |
| 19 | headers and footers in a styles module | functions `header(…)`, `footer(…)` with `markup(…)` |
| 20 | name and extension | Primula Documenting System (`primula-docs`), the language Primula, extension `.prml` for all kinds of files (sub-extensions — decision 100), header key `primula:`; ngml is the internal working name |
| 21 | conditions and loops inside a line | inline `\|if(…){…}`, `\|elif`, `\|else`, `\|for(…){…}` in `Inline`; in `IfBlock` and `ForBlock` only environments; a paragraph empty after evaluation is not output |
| 22 | arguments on several lines | allowed for `(…)`, `\|(…)`, `\|=(…)` (there is one line mode) |
| 23 | a line with a line command in the `para` mode | any alternative of `Block` except `Paragraph` and `LineComment`; a comment line is removed before the boundaries are determined — withdrawn by decision 107 |
| 24 | indentation in `\|code:` and `\|verbatim:` | the prefix of the opening line is removed; a smaller or different indentation is an error |
| 25 | YAML and JSON data types | core YAML 1.2, fractional numbers without an exponent are `decimal`, unquoted `YYYY-MM-DD` is `datetime` (decision 109); a non-existent date is an error |
| 26 | column unit in diagnostics | Unicode code points from 1, a tab is one character, positions of the source file |
| 27 | diagnostic codes and format | `P` + 4 digits by groups, severity separate from the code, a format as in gcc/rustc; the list is in the prototype, an appendix before v1.0 |
| 28 | closing control constructs | only `\|endif`, `\|endfor`, `\|enddef`; an anonymous `\|end` before them is an error |
| 29 | value type of `when=` | a boolean core expression; a string is an error |
| 30 | Python grammar version | Python 3.11 without PEP 701; checked regardless of the interpreter version |
| 31 | content of the implicit clause scope | all blocks belong to it except the closing ones: a paragraph and `\|.Ім'я:`, a heading, a clause of the same or a higher level, structural and page commands, `\|if`/`\|for` with a heading or a clause of such a level at the top level, the end of the environment; `\|include` is transparent, its path is known when the tree is built |
| 32 | consistency of list markers | a mismatching prefix, mixing types at a level, skipping a level are errors |
| 33 | content of the `\|list(…):` environment | blank lines do not split it; blocks belong to the last item of the top level of the environment; a nested item is continued by a nested `\|list:`; a heading and `\|>` are errors |
| 34 | end of a command line | spaces and a comment `\|%` after the arguments, `:` and closing markers (`LineEnd`); except the end marker of `\|verbatim` |
| 35 | threshold of an anonymous `\|end` | 30 lines inclusive; set in the project |
| 36 | `continue` is a Python keyword | the continuation argument of a clause and a list is `continues=`; the Kit converter translates `continue` into `continues=` |
| 37 | `\|include` in the body of a table | allowed in `\|table:` and `\|row:`, the inserted blocks have the same restrictions; `\|let`, `\|set` are errors |
| 38 | the scope of `\|!` | closed by any clause, the next `\|!`, `\|if`/`\|for` with a clause or a heading at the top level and everything that closes a clause scope |
| 39 | `\|end clause` | closes the nearest clause of any level; `\|end>`, `\|end>>`… check the level |
| 40 | the top level of code with lazy global names | definitions (`=`, unpacking, `def`, `\|let`) are lazy and frozen; actions are executed in document order after the definitions are collected, their names are local; changing a frozen value is an error; the rules are the same for all kinds of files |
| 41 | arithmetic | `//` and `%` for `decimal` round down; `decimal ** -n` → `decimal` (`int` merged into `decimal`, decision 108); `bool` in arithmetic is an error; `round` is half away from zero by the decimal notation; `str(decimal)` without an exponent |
| 42 | limits and the step model | in version 1.0: steps, recursion, collection, string, integer, time; replaced by decision 113 (three limits, the step model removed) |
| 43 | operations of types | `type()` gives the name as a string; attributes and operations of `datetime`, `length`; comparison of different types; dictionary keys are immutable values, `float` and `length` are an error |
| 44 | representation of `length` | in version 1.0: a rational value in inches and the unit written; changed by decision 110 |
| 45 | `format` and `%` | `format` without attribute access; `%` formatting allowed |
| 46 | default parameter values | computed when the function is defined and frozen |
| 47 | the value of `\|(…)` in text | by the rules of the core `str()`; `content` is markup; `None`, `bool`, collections, a record, a function are errors; a warning for `decimal`, `float`, `datetime`, `length` without formatting |
| 48 | macros | insertion by the form of the call (in a line only a body of one paragraph); rules of the `body` parameter; a call from code returns `content`; lexical scope |
| 49 | `\|let` and `\|code:` in environments | outside `\|if`/`\|for`/`\|def` global; in `\|for`/`\|def` local; in a top-level `\|if` an error |
| 50 | `\|include`: visibility, root, static path | a fragment sees its own names, the root document, the project; the root without a project file is the directory of the root document; the path is made of literals, header parameters, `project.*`, keys; a repeated inclusion is evaluated separately |
| 51 | CSV format | UTF-8, a header line, RFC 4180, separator `,`/`;`; without `types` strings; one decimal separator, groups by spaces |
| 52 | name and content of a module | the name is the base of the file name without the extension and sub-extension, otherwise `alias=`; only definitions, code, `\|import`; names with `_` are not exported |
| 53 | `has()` without `features` | `False`; `features` that is not a list of strings is an error |
| 54 | order of phases | definitions → top-level actions in document order → evaluation of the markup |
| 55 | document styles without a project file | the built-in `std/styles/default` if no modules are named; the key `styles` in the document header; on top of the built-in one by naming it explicitly; the option `--style` and the order of layers — decision 106 |
| 56 | names of materialized and derived styles | deterministic replacement rules, alphabetical order, a hash for names longer than 128 characters (decision 103); list variants `-l<n><b\|n>` |
| 57 | formats of property values | the table of section 11.3; borders as a string; `#RGB` is expanded to `#RRGGBB` |
| 58 | visibility of the names of styles modules | the "styles" level between the document and the project; shadowing, not a repeated definition |
| 59 | who defines styles | styles modules, the project, the document and fragments; the place of execution is checked; the top level of an `\|import` module is an error |
| 60 | `\|set` | values as in `structure_styles`; the scope is a structural environment; `None` resets; in a fragment up to the end of the fragment |
| 61 | parent style of the automatic paragraph style | the deepest explicit paragraph style, otherwise the style of the construct |
| 62 | inline short forms | named character styles; the `structure_styles` keys `strong`, `emphasis`, `underline`, `superscript`, `subscript`, `code`, `strike`, `placeholder` |
| 63 | quotation marks | uk, ru «…» and „…“; en “…” and ‘…’; the third level repeats the first; `quotes(…)` in a styles module |
| 64 | default page style | the key `page` in `structure_styles`, usually `Portrait` |
| 65 | document language | `document.language` → the project's `language` → `defaults.language` → `uk-UA` |
| 66 | ODT metadata | mapping of keys to `meta.xml`, the rest to `meta:user-defined`; `created` and `modified` default to the build date; byte-for-byte reproducibility |
| 67 | report and source files in the ODT | a short report without values by default (`--no-embed-report`); the full one only as an external file; source files with `--embed-sources` |
| 68 | numbering of clauses under subsections | from the nearest numbered heading of any level; a warning about possibly coinciding numbers |
| 69 | `{n}`, separator, number in a reference | a compound number with the scope prefix; a space unless the format ends with a space or a tab; a reference without the format (`ref_format`) |
| 70 | styles of new constructs | the `structure_styles` keys `caption`, `footnote`, `endnote`, `note_anchor`, `appendix`, `toc`, `list_of`, `reference` and the styles of the built-in module |
| 71 | designation of an appendix | the function `appendices(…)`, the argument `subtitle=`, one level-1 entry in the table of contents |
| 72 | reference labels | keys by kind of target; dictionaries uk, ru, en; a non-breaking space; without a dictionary an error only for `label` |
| 73 | captions and languages | `business` numbers throughout, `report` by chapter; in an appendix with a prefix; the language as the first argument of `captions`, `appendices` |
| 74 | IDs in a fragment | a repetition without `ns=` is an error; with `ns=` the prefix `ns.` |
| 75 | a target removed by a condition | recognized by the literal `id`; in `--review` a warning |
| 76 | references to footnotes | the field `text:note-ref`; `label` and `title` are an error; `numbering="document"` in 1.1 |
| 77 | notations in a typed column | the locale form and the canonical one; for en dates only ISO; minus `-` or `−`; an empty cell is `None` |
| 78 | output in a typed column | by the column type; the parameter `digits=` |
| 79 | `currency=` | a currency code or a string; after the number following a non-breaking space |
| 80 | cell value | only one expression or formula, or a literal in a typed column; a mixed cell is a string with a formatted formula; outside a typed column by the value type without a warning |
| 81 | formula functions | row numbering throughout; `column()` defaults to `body_rows()`; `None` and covered positions; aggregates and `count` |
| 82 | `live=True` | the list of constructs translated into Writer formulas; anything else is an error; the formula and the value together |
| 83 | number of cells | both fewer and more are an error |
| 84 | watermark | a text mark is an SVG image created by the translator; parameters `angle`, `color`, `size`, `opacity`, `font`; `img(path)` in code; `pages` are page style names |
| 85 | image size, DPI, EXIF | DPI from the file, otherwise 96; scaling down to the text area; EXIF rotation not applied, a warning |
| 86 | number in a figure caption | computed text, not a field |
| 87 | `restart`, `number_format` in `\|page` | `restart` only for this change; another `number_format` gives a derived page style |
| 88 | first-page header/footer | the first page of each run of the style; for the first page of the document a separate style with `next=` |
| 89 | left and right headers/footers | separate headers/footers of even and odd pages; mirrored margins with `mirror=True` |
| 90 | type `days` | a duration in days; `date ± days`; `date - date` → `int`; `date + int` is an error — withdrawn by decision 109 |
| 91 | extending the library dictionaries | styles module functions `currency`, `unit`, `month_names`, `typography` (library document, section 1) |
| 92 | currencies | a dictionary of UAH, USD, EUR with forms and genders; the fractional part in digits or `kop="words"` (library document, section 3) |
| 93 | units | an initial dictionary; `convert` within one quantity; `degC` ↔ `K` with an offset (library document, section 6) |
| 94 | calendar | the scheme `weekend`, `holidays`, `workdays`, `rest_days`; no automatic transfers (library document, section 5) |
| 95 | `fmt_date` | placeholders; forms `short`, `long`, `contract` for uk, ru, en; `date_words` en (library document, section 5) |
| 96 | typography | `percent_space`, `nbsp_words`, `nbsp_short`; a space before `%` and `°C` per DSTU ISO 80000-1 (library document, section 7) |
| 97 | `translit` | uk — Resolution No. 55; ru — ICAO Doc 9303; en — unchanged (library document, section 7) |
| 98 | `words` and money functions | up to 10¹⁵ − 1, 6 fractional digits, «мінус»; `float` in money functions is an error; `with_vat` and `without_vat` are symmetric (library document, sections 3, 4) |
| 99 | organization of the documents | the specification is kept in Russian (translation into uk and en after stabilization); the list of short forms is one table in section 3.3; appendices are numbered with digits; the standard library is moved to a separate document `primula-stdlib` with its own version (section 13) |
| 100 | kinds of files and extensions | sub-extensions `.f.prml` (fragment), `.m.prml` (module), `.s.prml` (styles), `.p.prml` (project); a document has no sub-extension; precedence: `kind`, otherwise the sub-extension, otherwise a document; a mismatch is a warning (`--strict` makes it an error, `P7`); the module name is taken before the sub-extension; a path without an extension: first the sub-extension of the command, then `name.prml`; only four sub-extensions are reserved |
| 101 | the character after `\|` | after `\|` a single Unicode character of the categories `P*` and `S*` is allowed; an undefined form is an error; the Unicode version is fixed by the language version; the special case for `—` is removed |
| 102 | Unicode names of the author | UAX #31 (`XID_Start`, `XID_Continue`), comparison by NFKC, case-sensitive; variables, parameters, functions, macros, record fields and data keys, module names, scopes, map keys, `id=`, styles, `col(id=…)`; built-in commands and predefined header keys are ASCII; record keys are normalized, a conflict is an error; linter: homoglyphs and mixed alphabets; the hint "`\|;` needed" |
| 103 | names of materialized styles | values may contain Unicode letters and digits, `_`, `-`; other characters → `_`; the hash `Base-x<8 hex>` only for names longer than 128 characters; a taken name with other properties is an error |
| 104 | command arguments | core expressions evaluated in the evaluation phase; when the tree is built only `path`, `part`, `key` of `\|include` are known (refined by decision 114: `level=` is an ordinary expression); otherwise an error "the value must be known when the tree is built" |
| 105 | `level=` of a heading | either the number of `<` or `level=` with a single `<` (both at once is an error); range 1–6; `\|>`, `\|-`, `\|#` have no `level` argument |
| 106 | option `--style` | repeatable; layers: project → `--style` → the document's `styles` → document code; a `--style` given turns off the automatic loading of `std/styles/default`; the path is relative to the current directory, a file outside the project root is allowed; paths and hashes go into the report |
| 107 | line mode | the `para` mode removed, one mode left (end of line); the key `lines` is an error "mode removed"; removed `--lines`, the warnings about `para`, the restrictions on the choice of `Block`; decisions 11 and 23 withdrawn |
| 108 | numbers | `int` merged into `decimal` (an integer has scale 0); a ceiling of 64 significant digits; indexes, slices, `range`, repetition accept a number with an integral value; `5 == 5.0`, hash by value; mixing `decimal` and `float` gives `float`; `dec(float)` by the shortest decimal notation; money functions reject `float`; `std/math` accepts `decimal` |
| 109 | `datetime` | a built-in class on `float64` (days from 30.12.1899), normalized to the second, no time zones; `dt - dt` → `decimal` days; `dt ± n` in days; `float(dt)`, `datetime(serial)`; constructors `date(y,m,d)`, `datetime(y,m,d,h,mi,s)`; YAML `2026-10-12` and `2026-10-12T14:30[:00]`; the types `date` and `days` removed, decision 90 withdrawn |
| 110 | `length` | a separate type: a decimal value and a unit; 1 in = 25.4 mm = 72 pt; the result in the unit of the left operand; `==` with a tolerance of 0.001 mm; the "up to three digits" rule removed |
| 111 | type `style` | removed: a style is a string with a name; `derive(…)` and `Indented(…)` return the name and register it; the style is written at its first use (decision 114) |
| 112 | type `content` | unchanged |
| 113 | limits | three: time (20 s per evaluation, `--timeout` per build), recursion 500, value size 10 million checked before creation; memory at the process level; `steps`, `collection`, `string`, `int_digits` and the step model removed |
| 114 | refinements when the implementation adopted the specification (sub-stage 13.8a) | Unicode version 15.1; `-` and `.` are allowed in `id=`; `level=` is an ordinary expression (a heading closes a scope at any level), only `path`, `part`, `key` of `\|include` are static; a declared language version other than the implemented one is an error, there is no compatibility mode; a style from `derive(…)` is written to the ODT at its first use, the name is reserved at the call; `dt - dt` is the exact number of seconds / 86400; `dt ± n` is rounded to the second (half away from zero); `length * float` goes through `dec()`, `nan`/`inf` are errors |
| 115 | refinements during the implementation of the library (sub-stage 13.9) | `\|\` gives no space after itself; the warning about an unformatted number is for `decimal` with a fractional part, `float`, `datetime`, `length`, integers are not checked; the minus is output as U+2212; Cyrillic formats `а`, `А` in `levels.format`; skipping letters is an open question; `\|let` in a fragment and `\|document` refined (sections 10.2, 10.4, 10.7); details in library document 0.4 |
| 116 | technical documentation tools (sub-stage 13.10) | built-in formatting of `\|!` (a table, styles `Admonition*`), `admonition(…)` postponed until the `content` operations; order: signal word → `hazard` → `consequence` → body; signal words ru/en, `admonition_words`; `note`/`tip` are paragraphs, the group «Примітки:» with the list `NoteList`; `\|abbr` — three forms and `text=`, `abbreviations(first, sort)`, the list of abbreviations is a table; `--review`: marks of `when=` and `\|if` without definitions, `review_marks`, watermark; linter for `hazard` |
| 117 | project and build (sub-stage 13.11) | the file `project.p.prml`, searched upwards to `.git`, `--project`/`--no-project`; a document parameter with the name of a project parameter overrides the value (no merging, the type is checked); target parameters and keys only if declared; the code section always runs, `batch_mode()`; the target `{source, output, params, keys, pdf}`, `output` mandatory, target errors do not stop the build; `\|document` parts: the styles of the root, a new page, `page=`, the language of the part; keys relative to the project root; `--dump-project` |
| 118 | interpretations of the implementation 13.10–13.11 (after sub-stage 13.11) | confirmed: the word `notes` of a group of notes; `review_marks` are texts, colours are styles; symbol paths relative to the calling file; `\|if` branches in `--review`; `project.*` includes the definitions of the code section, an error of the code section stops the build; the batch build by `kind: project`; the scope of a part by the file name; `\|document` in the root document, including in `\|if`/`\|for`, without nested parts; `structure` in the header of a part is ignored; the order of the actions of the parts' code; appendices per part, footnotes throughout; reference lookup in a part |
| 119 | proposals after sub-stage 13.11 implemented in 13.9d (proposals П1–П5, П7 of the answer of the specification thread; confirmed by the user on 15.10.2026) | `letters=` of a list level — a number as text skipping letters, the `report` profile for uk without ґ, є, з, і, ї, й, о, ч, ь (5.4, 11.3); `--param NAME=VALUE`, a string parameter gets the text as written (14.1); `level_shift=` of `\|include` and `\|document`, a shifted part continues the numbers (10.2, 10.7); `\|table(data=…, fields=…, titles=…)` (6.2, 6.9); `space_before`/`space_after` of a table style, 3 mm each for `AdmonitionTable` (9.1, 11.3); `--format json` (14.1, 14.2); core message texts are translated (14.2); frame style properties are the defaults of the parameters of `\|img`/`\|figure` (8.5, a correction); `typography(nbsp_short=True)` follows the language of the root document (library document, 7) |
| 120 | gaps in the language found when translating a contract from Kit (sub-stage 13.12; accepted by the user on 15.10.2026) | principle 10 (1.4): profiles are defaults, not rigid rules; `\|link("url"){text}` (4.2); `structure_styles(link=…, clause_number=…, heading_number=…)` — the style of external links and numbers (5.2, 11.5); `style=` of `\|<` and `\|>` (5.2, 5.3); `replace: true` — replacing a style of lower layers (11.3, 11.7); `\|: \|& …` — an empty first cell (6.4, grammar); `cols` of a table style (11.3); `appendices(title_format=…)` — the designation and title on one line (5.1); `transparent` = `none` (11.3); the common style namespace is kept (11.2); a summary of warnings of one kind is an open question |
| 121 | references to another document of the project (sub-stage 13.12; accepted by the user on 15.10.2026) | the project's `documents` and the document header's `references`; the text from the registry `*.refs.json` with a check of the SHA-256 of the sources, when outdated the structure of the document is computed and the registry updated on `build`; without a source, the registry of the published edition; a reference is text without a hyperlink, `page` is an error, an ambiguous target is an error; the origin of the text is in the report (2.3, 5.7, 10.6, 14.3) |
| 122 | table of contents control and navigation (sub-stage 13.12; accepted by the user on 15.10.2026) | `toc=True` beyond `max_level`, `toc_level=` of a heading; `toc`, `toc_title`, `toc_level` of `\|appendix` and of a clause `\|>` (a clause only on request); the command `\|toc_entry("…", level=…)`; an appendix is an outline heading (the Writer navigator, PDF bookmarks), the index «ЗМІСТ» is still built from marks (5.9) |
| 123 | the order project and filled-in forms (sub-stage 13.12; accepted by the user on 15.10.2026) | `extends:` of a project file: the root, parameters, keys, documents, styles and the code section of the base are inherited, targets are not, the project's own paths are relative to its own file (10.6); `placeholders("final")` — placeholders as ordinary text without warnings (4.2) |
| 124 | dumps for editors and Primula Studio (sub-stage 14.2; improvements Т1–Т3, Т5 of the Studio plan, accepted by the user on 15.10.2026) | `primula check document --dump-structure` — the structure in JSON: headings, clauses, appendices, tables, figures, lists and admonitions with IDs, numbers, positions and the scope of the part, the places of `\|include`/`\|document`; `--dump-styles` — styles in JSON: kind, layers and their origin, parent, own properties with the position of the definition, effective ones with the style of the chain; both options together give one JSON object, only for a document; `--overlay FILE=BUFFER` of `check` — the text of a file from an unsaved editor buffer, positions and messages by the original path, a reference registry with a buffer is considered outdated; `primula commands [--format json]` — a reference of built-in commands, short forms and closing markers with arguments, defaults, descriptions (en/uk/ru) and the section of the specification (14.1) |
| 125 | project dump for Primula Studio (sub-stage 14.3; accepted by the user on 15.10.2026 together with the Studio plan: a service directory `.primula-studio/` in the project root, for `extends` in the root of the base) | `check project.p.prml --dump-project` also outputs `root` — the absolute path of the project root (for `extends`, of the root of the base; target and message paths are relative to it) — and `documents` (14.1) |
| 126 | reference of expression functions for Primula Studio (sub-stage 14.13; accepted by the user on 16.10.2026 together with the stages of the library help, project properties and the evaluator console) | `primula commands` also outputs `function_categories` and `functions`: each name available in code (core functions and methods, the prelude, `std/math`, `load_*`, styles code, table formulas, the project) with the signature, arguments, result, description (en/uk/ru), document and section, the place of call (`any`, `styles`, `cell`, `project`) and an example; examples without a document are evaluated by the translator (`result`); `--functions` gives a text list of functions (14.1) |
| 127 | project and document properties (sub-stage 14.14; accepted by the user on 16.10.2026) | the key `document` of the project header gives the default ODT metadata for all documents of the project; a document replaces them one by one; inherited through `extends`; the project's `document.language` takes precedence over the project's `language` (2.3, 10.6); `--dump-structure` outputs the document parameters (`params`: type, default in the `--param` form, origin) for the build parameters form of Studio; `primula commands` also outputs `header_keys` — a reference of the YAML header keys by kind of file with type, values, the `recommended` flag, description (en/uk/ru), section and example; `--header` gives a text list (14.1); `--dump-project` outputs `document` |
| 128 | evaluator console (sub-stage 14.15; accepted by the user on 16.10.2026: a terminal-like window, a series of inputs with results, a common name context, help on the library) | `primula console [FILE] [--json]`: the context of a document, fragment, project, module or styles module (without evaluating the text), input is Primula code, definitions are kept in levels (in the console a name can be defined again), the value of the final expression is shown, `debug` is output; commands `:help`, `:functions`, `:vars`, `:reset`, `:context`, `:quit`; limits per input; SIGINT interrupts an input (P0006); a JSON line protocol for Studio (14.1) |
| 129 | names of header keys (sub-stage 14.16; accepted by the user on 16.10.2026 after remarks on 14.14) | the metadata section is named the same as the name of its values in text and code: `document:` → `doc:` (`\|(doc.title)`); in a project `document:` → `doc_defaults:`, `documents:` → `ref_documents:` (the pair of the document's `references`); the old names are error P1120 with the new name, no synonyms; the recommended fields of the project's `doc_defaults` are `creator`, `organization`; the console protocol `--json` got `names` (names for the Studio list) |
| 130 | `std/math` in the console (sub-stage 14.12; the user's variant of 16.10.2026) | in `primula console` the module `std/math` is always loaded under the name `math` (a context name `math` is kept); in a document `\|import("std/math")` is still required; the descriptions of the `math.*` functions in the reference (`primula commands`) name this import |
| 131 | an image computed by code (sub-stage 14.12; accepted by the user on 16.10.2026) | `svg=` of `\|img`, `\|figure` and `img(…)` is an SVG string built by code; code writes no files, the string is put into the ODT by the content hash; checks: XML with the root `<svg>` and a size (P6110), no `DOCTYPE`/`ENTITY` (P6111), only `#…` and `data:` references (P6112); an `img(…)` value is accepted by `\|img` and `\|figure` in the position of the path, its parameters are the defaults of the command parameters; an image is given in exactly one way — path, key, `svg=`, value (P6113) |
| 132 | table width in a section with columns (confirmed by the user on 16.10.2026; found when translating the cheat sheet into Primula) | percentages of the table and column widths inside `\|section(cols=…)` are of the column width: `(area width − gaps) / cols`, with unequal `widths` of the narrowest one; the default gap is 5 mm |
| 133 | base of a styles module and the styles of the kit (stage 15.3; the user's variant of 21.10.2026) | the key `extends` of the header of a styles module: the base is a layer before the module, the chain is expanded, each module is one layer at the first place, a cycle is "inclusion cycle"; the sets `std/styles/business`, `letter`, `technical`, `report`, `compact` based on `std/styles/default` (section 11.9; `business` and `letter` per DSTU 4163:2020, `report` per DSTU 3008:2015); the built-in module got common variants (`BodyLeft` … `Landscape`), `Body` has an explicit `first_line: 0mm`; the Cyrillic list format is checked only for the styles the document uses |
| 134 | parallel tracks (stage 16; a proposal of the specification thread of 19.10.2026, the user's decisions of 21–22.10.2026) | the environment `\|parallel` with tracks `track` and segments `\|segment` (section 7.7): output as an ODF table, the track language, counters and IDs `<track>.<id>` per track, references inside a track, the correspondence check profiles `parity` (`structure`, `translation`, `none`), freshness control `status`/`rev`, the command `primula parallel` (`--stub`, `--stamp` with `--segment`, `--check-status`), codes P5301–P5321; the unit of alignment is named "segment" (`\|segment`), not "unit"; after a check in Writer: headings of non-primary tracks are paragraphs with a heading style without an outline level (not part of the navigation), footnotes of numbered non-primary tracks carry the track number as an explicit label, with a restart per page or chapter Writer numbers them with a warning; an unsupported track language is a warning; `rev` keeps two hashes — of the primary block and of its own (a change of a confirmed translation is detected too); the text normalization for the hash is defined; a "requirement / answer" profile with a typed status is outside version 1.1; refined during the implementation (stages 16.3–16.5): a full-width segment is numbered by the primary track, numbered tracks continue from it; the track index is a Writer user index (checked), its title is in the track language; P5314 compares value names, not functions; a number is compared by its digits; the counters on leaving are those of numbered mandatory tracks; `primula parallel` writes only the named file, in normal form and without errors, `--check-status` checks the blocks of non-primary tracks |
| 135 | exporting functions from a fragment (operational remark Э2, the user's decision of 22.10.2026) | the decorator `@export` / `@export(name="…")` on a top-level `def` of the code of a fragment; `\|export("name", …)` exports already defined names (macros, functions) under the same name; outside a fragment an error, in a module a warning; `module._name` gives a hint about a private name; the document's `\|import` is visible in fragments | 10.3, 10.4, 12.2 |
| 136 | shared libraries through symbolic links (direction 18, Д4; the user's decision of 26.10.2026) | the root boundary is checked on the written path without resolving links (`..` textually): a link created by the author inside the project may lead outside the root; a file through such a link gives warning P2639 once per link, with its target; in messages, the report and `--embed-sources` the path inside the project; `../` in the text still does not go outside the root (10.1) |
| 137 | QR codes and Base64URL in the standard library (direction 18, item 18.3; the user's decision of 26.10.2026) | the functions `qr_matrix`, `qr_svg` (byte mode of DSTU ISO/IEC 18004:2019, the smallest version in the given range, a deterministic mask, a white circle `circle` in the centre) and `base64url` (encodings `utf-8`, `cp1251`, without `=`) — section 10 of the library document; formats on top of QR (the NBU payment QR) are user libraries |
| 138 | ODS and XLSX spreadsheets (direction 21, item 21.1; the user's decision of 26.10.2026) | `load_ods`, `load_xlsx`: sheet `sheet`, range `range`, `header`, `types` as in `load_csv`; formula values are those stored in the file, a formula without a result is an error; numbers are `decimal` up to 15 significant digits, dates `datetime`; errors name the sheet and cell; XLS is not supported (10.5) |
| 139 | export through pandoc (direction 19, item 19.1; the user's decision of 26.10.2026) | the command `primula export FILE --to FORMAT`: the evaluated document → pandoc JSON AST (`--to json` without pandoc), other formats through pandoc; the mapping of constructs is in 14.1; page layout is not exported; import from other formats later (a pandoc writer in Lua, `docs/dev/pandoc.md`) |
| 140 | reading a text file (the user's remark of 27.10.2026) | `load_text(path)`: the whole file as one string — UTF-8 without BOM, line ends LF, NFC; no parsing; paths and hash in the build report as for the other `load_*` (10.5) |
| 141 | warning for a body of `\|@` (a finding of AI proofreading, 02.11.2026) | `\|@(…){text}`: a reference has no body, a brace right after `)` is text, the translator warns (P1245, a parse warning); a brace after a space is ordinary text without a warning (5.7) |

### 4.3. Open questions

Checks of support in Writer:

- the attribute `style:use-optimal-column-width`, recalculation of `live=True` formulas;
- the first-page header/footer per ODF 1.3;
- wrapping of the first paragraph only, a contour by transparency;
- a table of contents by `text:toc-mark`, lists by the marks of a user index, the field `text:bookmark-ref` with a page number, subentries of the alphabetical index;
- text rotation in a cell and diagonal lines.

Language and library:

- taking spanned cells into account in the `auto` calculation;
- groups of images and subfigures «а», «б»;
- computed document metadata;
- the search order for the standard library and shared modules outside the project;
- visible names of materialized styles;
- a summary of warnings of one kind (for example, "N placeholders" instead of a separate message for each `|?{…}` outside `--strict`; the positions in the report);
- moving the Kit business style catalogue with spacing variants;
- the exact formats of the `report` profile by the text of DSTU 3008:2015; the designation of an appendix in a header (sub-stage 13.8);
- a list of warnings `|list_of("safety")`;
- `content` operations outside the core (together with `markup(…)` and the overridable formatting function `admonition(…)`, section 9.1);
- checking the letter set of the `report` profile (section 5.4) against the text of DSTU 3008:2015; for the designations of appendices (`appendices.letters`) «И» is excluded as well;
- the canonical form of `primula fmt`: the notation of arguments, closing forms, indentation, the modes `--check`/`--diff`/stdin, guarantees of idempotence and of an unchanged ODT;
- a closing character and a paired notation of emphasis (`|*жирний|*`): sugar over `|*{…}` or a replacement of the braces — no decision;
- the time of day without a date as a separate value; time zones and offsets; fractions of a second in `datetime`;
- trigonometry and other functions in `std/math`.

Questions about the content of the standard library are kept in the library document.

## Appendix 5. End-to-end examples

### 5.1. Supply contract

```
---
doc:
  title: "Договір поставки"
  identifier: "Д-2026-017"
  language: uk-UA
params:
  delivery_days: 5
  vat_rate: 20
  buyer: {name: "ТОВ «Покупець»", code: "12345678"}
---
|code:
items = load_csv("data/items.csv", types={"qty": "decimal", "price": "money"})
net = sum(it.qty * it.price for it in items)
total = with_vat(net, vat_rate)
|end

|.DocumentTitle: ДОГОВІР ПОСТАВКИ № |(doc.identifier)
|.DatePlace: |(project.city), |(fmt_date(build_date(), "contract"))

|.Preamble:
|(project.seller.name) (далі — |.DefinedTerm{«Постачальник»}) і |(buyer.name)
(далі — |.DefinedTerm{«Покупець»}) уклали цей договір про таке.
|end.Preamble

|<(id="subject") Предмет договору

|>(id="delivery") Постачальник передає Покупцеві товар згідно зі специфікацією (|@("app-spec", "label")).
|> Загальна вартість товару становить |(money_full(total, "UAH")), зокрема ПДВ |(money(vat(net, vat_rate), "UAH")).

|<(id="terms") Умови поставки

|>(id="term") Поставка здійснюється протягом |(delivery_days) |(plural(delivery_days, "робочого дня", "робочих днів", "робочих днів")) з дати оплати.
|> Адреса доставки: |?{УТОЧНИТИ}.

|<(number=False) Реквізити і підписи сторін

|table(cols=["50%", "50%"], style="TableParties"):
|: ПОСТАЧАЛЬНИК |& ПОКУПЕЦЬ
|: |(project.seller.name)|\ Код ЄДРПОУ |(project.seller.code) |& |(buyer.name)|\ Код ЄДРПОУ |(buyer.code)
|end table

|appendix(id="app-spec", title="Специфікація"):
|table(cols=[col("*"), col("15mm..25mm", id="qty", type="decimal", align="right"), col("20mm..35mm", id="price", type="money", align="right"), col("20mm..35mm", id="sum", type="money", align="right")], style="TableServices", footer=1):
|: Найменування |& Кількість |& Ціна, грн |& Сума, грн
|for(it in items):
|: |(it.name) |& |(it.qty) |& |(it.price) |& |=(this_row("qty") * this_row("price"))
|endfor
|:|&(span=3, align="right") Разом без ПДВ |& |=(sum(column("sum", rows=body_rows())))
|end table
|end appendix
```

### 5.2. A fragment of an operating manual

```
---
doc: {title: "Настанова з експлуатації", language: uk-UA}
params:
  model: "X300"
  features: [wifi]
---
|code:
spec = load_yaml("data/x300.yaml")
|end

|< Вказівки з безпеки

|include(key="safety.general")

|!("danger", hazard="Висока напруга"):
Дотик до струмопровідних частин призводить до смерті.

|- Вимкніть живлення перед обслуговуванням.
|- Перевірте відсутність напруги.
|end!

|< Технічні характеристики

|table(cols=["*", "35mm..60mm"], caption="Основні параметри", id="tbl-params"):
|: Параметр |& Значення
|: Напруга живлення |& |(qty_range(spec.u_min, spec.u_max, "V"))
|: Частота |& |(qty(50, "Hz", tol=1))
|:(when=has("wifi")) Бездротовий зв'язок |& Wi-Fi 802.11 b/g/n
|end table

|figure(key="scheme", width="120mm", id="fig-scheme"):
Схема підключення пристрою |(model)
|end figure

Підключення виконують за |@("fig-scheme", "label"); параметри наведено в |@("tbl-params", "label").
```

### 5.3. Protocol of disagreements

Three tracks: the supplier's wording, the buyer's wording (the primary track) and an unnumbered commentary; the segment `p-4-3` is a new clause, the cells of the optional tracks are empty (section 7.7).

```
---
kind: document
doc: {title: "Протокол розбіжностей", language: uk-UA}
---
|parallel(tracks=[track("old", title="Редакція Постачальника", optional=True),
                  track("new", title="Редакція Покупця", primary=True),
                  track("note", title="Коментар", width="28%", numbered=False, optional=True)],
          parity="structure"):

|segment(id="p-4-2"):
|track("old"):
|> Оплата здійснюється протягом 5 банківських днів.
|track("new"):
|> Оплата здійснюється протягом 30 календарних днів.
|track("note"):
|.Note: Відстрочку погоджено листом від 12.10.2026.
|end segment

|segment(id="p-4-3"):
|track("new"):
|> Покупець має право на дострокову оплату без штрафних санкцій.
|end segment

|end parallel
```
