# Коды диагностики Primula

Реестр кодов, которые выдаёт прототип транслятора. Основание — спецификация v1.1-draft, §14.2, решения 26–27 журнала решений (с 13.8a — по v1.1). К выпуску v1.0 реестр переносится в отдельное приложение спецификации «Коди діагностики».

## Правила

- Код — `P` и четыре цифры. Первая цифра — группа.
- Серьёзность (`error` / `warning`) — отдельный признак сообщения, а не часть кода. `--strict` превращает предупреждение в ошибку, код остаётся прежним; в отчёте JSON такое сообщение помечено `"escalated": true`. В таблице ниже указана серьёзность без `--strict`.
- Коды стабильны: удалённый код повторно не используется, а помечается в таблице как удалённый.
- Тексты сообщений находятся в каталогах `src/primula/messages/{en,uk,ru}.py`. Английский каталог основной; uk и ru — переводы. Код не зависит от языка сообщения.
- Позиция: строка и столбец с 1; столбец — номер символа Unicode (кодовой точки), табуляция — один символ; позиция относится к исходному файлу до нормализации NFC. В отчёте JSON есть также конец диапазона (`end_line`, `end_column`).
- Текстовый формат (как у gcc/rustc):

  ```
  файл:строка:столбец: error[P1102]: текст
   строка | исходный текст строки
          |       ^^^
  файл:строка:столбец: note: примечание с позицией
    = help: подсказка без позиции
  файл:строка:столбец: note: in a fragment included here   (стек вызовов, изнутри наружу)
  ```

  Метки `error`, `warning`, `note`, `help` не переводятся: их разбирают редакторы и инструменты сборки.

## Группы

| Группа | Область | Разделы спецификации |
| --- | --- | --- |
| `P0xxx` | командная строка, ввод-вывод, внутренние ошибки | 14.1 |
| `P1xxx` | лексика и синтаксис | 2, 3, приложение 1 |
| `P2xxx` | имена, вычисление, ядро, лимиты | 10.4, 12 |
| `P3xxx` | стили | 11 |
| `P4xxx` | структура: нумерация, ID, ссылки | 5 |
| `P5xxx` | таблицы | 6 |
| `P6xxx` | страницы и графика | 7, 8 |
| `P7xxx` | модули, проект, данные, сборка | 10 |
| `P8xxx` | генерация ODF | 15 |
| `P9xxx` | технические документы | 9 |

Внутри группы вторая цифра обозначает подгруппу: `P11xx` — заголовок YAML, `P12xx` и далее — разбор тела (с подэтапа 13.1).

## Реестр

Таблицу читает тест `tests/test_i18n.py`: каждый код из таблицы должен быть во всех каталогах, и каждый код каталогов — в таблице.

| Код | Серьёзность | Подэтап | Сообщение (en) | Спецификация |
| --- | --- | --- | --- | --- |
| P0001 | error | 13.0 | `'{command}' is not implemented at prototype stage {stage}; no output is written` | — (временный, для команд прототипа) |
| P0002 | error | 13.0 | `internal error of the translator: {detail}` | 14.2 |
| P0004 | error | 13.8a | `the time limit of the build (--timeout) is exceeded` | 12.8, 14.1 (`--timeout`) |
| P0005 | error | 13.8a | `out of memory: the evaluation exceeded the memory limit of the translator process` | 12.8 |
| P0006 | error | 14.15 | `interrupted: the evaluation of the input was stopped` | 14.1 (`primula console`, решение 128) |
| P0101 | error | 13.0 | `cannot read file '{path}': {reason}` | 14.1 |
| P0102 | error | 13.0 | `the file is not valid UTF-8: invalid byte at offset {byte_offset}` | 2.1 |
| P0103 | error | 13.0 | `cannot write file '{path}': {reason}` | 14.3 |
| P0105 | error | 14.2 | `--overlay '{text}' must be written as FILE=BUFFER, and the buffer file must exist` | 14.1, решение 124 |
| P0106 | error | 16.5 | `primula parallel: {problem}{value}` | 7.7, 14.1, решение 134 |
| P0107 | error | 16.5 | `segment {segment}, track '{track}' is not in the state '{expected}': {reason} ({status})` | 7.7, 14.1, решение 134 |
| P1101 | error | 13.0 | `the YAML header is not closed: a line '---' is missing` | 2.3, A `Header` |
| P1102 | error | 13.0 | `invalid YAML in the header: {problem}` | 2.3 |
| P1103 | error | 13.0 | `the YAML header must be a mapping of keys to values, found {found}` | 2.3 |
| P1104 | warning | 13.0 | `unknown key '{key}' in the header of a file of kind '{kind}'` | 2.3, 10.6, 11.1 |
| P1105 | error | 13.0 | `header key '{key}' must be {expected}, found {found}` | 2.3, 10.6, 11.1 |
| P1106 | error | 13.0 | `unknown file kind '{value}'; expected one of: {expected}` | 2.2 |
| P1107 | error | 13.0 | `unsupported language version '{value}'; this translator implements version {supported}` | 0.1, 2.3 |
| P1109 | error | 13.0 | `non-existent date '{value}'` | 12.6 (решение 25) |
| P1110 | error | 13.0 | `duplicate key '{key}'` | YAML 1.2 (уникальность ключей) |
| P1111 | error | 13.0 | `unsupported YAML tag '{tag}'` | 12.6 (схема core) |
| P1112 | error | 13.0 | `recursive YAML alias: a value contains itself` | 12.6 |
| P1113 | error | 13.0 | `a mapping key must be a scalar value` | 12.6 |
| P1114 | warning | 13.0 | `'{value}' is a string in YAML 1.2, not a boolean` | 12.6 (решение 25) |
| P1115 | warning | 13.0 | `'{value}' is read as the integer {number}: the leading zeros are lost` | 12.6 (решение 25) |
| P1116 | error | 13.8a | `the key 'lines' is removed: the line mode was removed in version 1.1, a line form ends at the end of the source line` | 2.3, 3.4, решение 107 |
| P1117 | error | 13.8a | `invalid standard library version '{value}': expected MAJOR.MINOR, for example "1.1"` | 2.3, 13 |
| P1118 | error | 13.8a | `the file requires standard library {value}; this translator has {available}` | 2.3, 13 |
| P1119 | error | 13.8a | `time zones are not supported: '{value}'` | 2.3, 12.6, решение 109 |
| P1120 | error | 14.16 | `header key '{key}' was renamed: write '{new}:' (decision 129)` | 2.3, 10.6, решение 129 |
| P1201 | error | 13.1 | `'\|' must be followed by a command name, '(' or a short form; found {found}` | 3.1 |
| P1202 | error | 13.1 | `unknown short form '\|{char}'` | 3.1, B.1 |
| P1203 | error | 13.1 | `'\|{char}' is not a short form` | 3.1 |
| P1204 | error | 13.1 | `'{bracket}' is not closed` | 3.2, решение 22 |
| P1205 | error | 13.1 | `closing '{found}' does not match the opening bracket; expected '{expected}'` | 3.2 |
| P1206 | error | 13.1 | `the string literal is not closed` | 3.2 |
| P1207 | error | 13.1 | `invalid Python syntax: {problem}` | 12.2 |
| P1208 | error | 13.1 | `an f-string contains nested quotes of its own kind; Primula uses the Python 3.11 syntax` | 0.2, решение 30 |
| P1209 | error | 13.1 | `'\|{form}' needs a body '{{…}}'` | 3.3, A `InlineShort` |
| P1210 | error | 13.1 | `'\|{form}' is allowed only at the start of a line` | 3.3, B.1 |
| P1211 | error | 13.1 | `a letter directly follows the command name '{name}'` | 3.2, A `InlineCommand` |
| P1212 | error | 13.1 | `'\|{form}' must be followed by a space and text` | A `Heading`, `Clause`, `ListItem` |
| P1213 | error | 13.1 | `heading level {level} is too deep; levels 1–6 are allowed` | 5.2 |
| P1214 | error | 13.1 | `'\|!' needs arguments with the kind of the admonition, for example \|!("warning")` | 9.1, A `Admonition` |
| P1215 | error | 13.1 | `'{{' is not closed` | 3.2, A `InlineBody` |
| P1216 | error | 13.1 | `'{name}' is not closed; expected '{close}'` | 3.5 |
| P1217 | error | 13.1 | `'{found}' does not close '{name}'; expected '{expected}'` | 3.5 |
| P1218 | error | 13.1 | `'{found}' has no open environment to close` | 3.5 |
| P1219 | error | 13.1 | `'\|end' cannot close '\|{kind}'; use '\|end{kind}'` | 3.5, решение 28 |
| P1220 | error | 13.1 | `'\|{form}' without a matching '\|if'` | 3.6, решение 21 |
| P1221 | error | 13.1 | `a closing marker must occupy a whole line` | 3.5, решение 34 |
| P1222 | error | 13.1 | `the line has a smaller or different indentation than the line opening the block` | 3.7, решение 24 |
| P1223 | error | 13.1 | `the verbatim block is not closed: no line '{marker}'` | 3.7, решение 34 |
| P1224 | error | 13.1 | `the code block is not closed: no line '\|end'` | 2.2, 3.7 |
| P1225 | error | 13.1 | `'\|verbatim' accepts only the argument end="…" with a non-empty one-line string` | 3.7, A `VerbatimBlock` |
| P1226 | error | 13.1 | `'{what}' is not allowed directly inside '\|{container}'` | 6.2, A 3.5 |
| P1227 | error | 13.1 | `'\|&' is allowed only in a table row` | 6.4 |
| P1228 | error | 13.1 | `a formula '\|=(…)' is allowed only in a table cell` | 6.8 |
| P1229 | error | 13.1 | `invalid macro header; expected '\|def name(parameters):'` | A `DefBlock` |
| P1230 | error | 13.1 | `a heading is not allowed inside a clause environment` | 5.3 |
| P1231 | error | 13.1 | `'{form}' is not allowed inside a list environment` | 5.4, решение 33 |
| P1232 | error | 13.1 | `list level {level} follows level {previous}: a level is skipped` | 5.4, решение 32 |
| P1233 | error | 13.1 | `list marker '{marker}' does not match the parent items; expected '{expected}'` | 5.4, решение 32 |
| P1234 | error | 13.1 | `bullet and numbered items are mixed on level {level} of one list` | 5.4, решение 32 |
| P1235 | error | 13.1 | `'{name}' is a reserved name and cannot be defined` | B.3 |
| P1236 | warning | 13.1 | `this line starts a new paragraph after a line form` | 3.4, 14.2 |
| P1238 | warning | 13.1 | `an environment of {lines} lines is closed with an anonymous '\|end'; write '{close}'` | 3.5, 14.2, решение 35 |
| P1239 | error | 13.1 | `'\|list(…)' is not followed by a list` | 5.4 |
| P1240 | error | 13.1 | `'\|{form}' after '\|else'` | 3.6, A `IfBlock` |
| P1241 | error | 13.1 | `a list environment must start with a list item` | 5.4, решение 33 |
| P1242 | error | 13.1 | `expected {expected} after '{after}'` | A |
| P1243 | error | 13.1 | `a table row '\|:' is allowed only inside '\|table'` | 6.4, A 3.5 |
| P1244 | error | 13.8a | `'level=' cannot be combined with {count} '<': give the level either by the number of '<' or by level= with a single '<'` | 3.3, 5.2, решения 105, 114 |
| P1245 | warning | 2.1 | `'\|@(…)' has no body: the text in braces after it is printed as it is` | 5.7, решение 141 |
| P2101 | error | 13.2 | `'{construct}' is not allowed in Primula code` | 12.2 |
| P2102 | error | 13.2 | `the name '{name}' is not allowed: names with leading underscores reach Python internals` | 12.2, 12.7 |
| P2103 | error | 13.2 | `'is' and 'is not' are allowed only with None` | 12.2 |
| P2104 | error | 13.2 | `'{statement}' outside a function or loop` | 12.2 |
| P2105 | error | 13.2 | `'{name} …=' at the top level redefines a global name; global names are immutable` | 12.7, решение 40 |
| P2106 | error | Э2 | `'@export' is allowed only as '@export' or '@export(name="…")' on a def at the top level of a code block` | 10.4, 12.2, решение 135 |
| P2201 | error | 13.2 | `name '{name}' is not defined` | 10.4 |
| P2202 | error | 13.2 | `local name '{name}' is read before it is assigned` | 12.7 |
| P2203 | error | 13.2 | `'{name}' is already defined` | 10.4 |
| P2204 | error | 13.2 | `cyclic definition: {chain}` | 10.4 |
| P2301 | error | 13.2 | `operation '{op}' is not supported for '{left}' and '{right}'` | 12.3 |
| P2303 | error | 13.2 | `division by zero` | 12.4 |
| P2304 | error | 13.2 | `bool takes no part in arithmetic; convert with int(…)` | 12.4, решение 41 |
| P2305 | error | 13.2 | `'{op}' is not supported between '{left}' and '{right}'` | 12.3, решение 43 |
| P2307 | error | 13.2 | `cannot convert {value} to {type}` | 12.4, 12.10 |
| P2308 | error | 13.2 | `invalid numeric operation ({detail})` | 12.4 |
| P2309 | error | 13.8a | `number overflow: the result has more than {limit} significant digits` | 12.4, решение 108 |
| P2310 | error | 13.8a | `time zones are not supported: {value}` | 12.3, решение 109 |
| P2311 | error | 13.2 | `index {index} is out of range (size {size})` | 12.10 |
| P2312 | error | 13.2 | `key {key} not found` | 12.10 |
| P2313 | error | 13.2 | `'{type}' has no attribute '{name}'` | 12.10, решение 43 |
| P2314 | error | 13.2 | `the record has no field '{name}'` | 12.6 |
| P2315 | error | 13.2 | `'{type}' is not iterable` | 12.10 |
| P2316 | error | 13.2 | `'{type}' does not support '{operation}'` | 12.3 |
| P2317 | error | 13.2 | `'{type}' cannot be a dictionary key` | 12.3, решение 43 |
| P2318 | error | 13.2 | `a frozen {type} cannot be changed` | 12.7, решения 40, 46 |
| P2319 | error | 13.2 | `a {type} cannot be changed while it is being iterated` | 12.7 |
| P2320 | error | 13.2 | `cannot unpack: expected {expected} values, got {got}` | 12.2 |
| P2321 | error | 13.2 | `{function}(): {problem}` | 12.2 |
| P2322 | error | 13.2 | `{function}: {problem}` | 12.10 |
| P2324 | error | 13.2 | `cannot assign to this target` | 12.2 |
| P2325 | error | 13.8a | `the field '{name}' is given twice (names are compared after NFKC normalisation)` | 3.9, 12.6, решение 102 |
| P2330 | error | 13.2 | `attribute access in a format field is not allowed: '{{{field}}}'; use an index, for example {{0[name]}}` | 12.10, решение 45 |
| P2331 | error | 13.2 | `invalid format: {problem}` | 12.10 |
| P2340 | error | 13.2 | `fail: {message}` | 12.9 |
| P2402 | error | 13.2 | `the recursion limit ({limit}) is exceeded` | 12.8 |
| P2403 | error | 13.2 | `a collection of {size} elements exceeds the size limit ({limit})` | 12.8 |
| P2404 | error | 13.2 | `a string of {size} characters exceeds the size limit ({limit})` | 12.8 |
| P2406 | error | 13.2 | `the time limit of one evaluation ({limit} s) is exceeded` | 12.8 |
| P2501 | warning | 13.2 | `'{name}' is assigned in a top-level statement but never used there; it does not become a global name` | 12.7, решение 40 |
| P2502 | warning | 13.8a | `the name '{name}' mixes alphabets ({scripts})` | 3.9, 14.2, решение 102 |
| P2503 | warning | 13.8a | `the name '{name}' differs from '{other}' only by look-alike letters` | 3.9, 14.2, решение 102 |
| P2601 | error | 13.3 | `unknown command '\|{name}': it is neither a built-in command nor a defined macro or function` | 3.2 |
| P2602 | error | 13.3 | `'{name}' is a value of type {type}, not a command` | 3.2 |
| P2603 | error | 13.3 | `a value of type {type} cannot be inserted into text` | 4.2, решение 47 |
| P2604 | warning | 13.3 | `a value of type {type} is inserted into text without formatting` | 4.2, 14.2, решение 47 |
| P2605 | error | 13.3 | `the content of '{name}' has several blocks and cannot be inserted inside a line` | 3.2, решение 48 |
| P2606 | error | 13.3 | `macro '{name}' has no 'body' parameter, but the call passes a body` | 3.2, решение 48 |
| P2608 | error | 13.3 | `'{what}' in a branch of a top-level \|if: a definition cannot be conditional` | 10.4, решение 49 |
| P2609 | error | 13.3 | `\|{command}: {problem}` | 10.4 |
| P2610 | error | 13.3 | `only a fragment included outside \|if, \|for, \|def can export names` | 10.4, решение 49 |
| P2611 | error | 13.3 | `when= must be a boolean, found {type}` | 9.2, решение 29 |
| P2612 | error | 13.3 | `the value must be known when the tree is built: '{name}' is not a header parameter` | 10.2, решение 50 |
| P2613 | error | 13.3 | `invalid path '{path}': URLs, absolute paths and paths outside the project root are not allowed` | 10.1 |
| P2614 | error | 13.3 | `cannot read '{path}': {reason}` | 10.1 |
| P2615 | error | 13.3 | `cycle of inclusion: {chain}` | 10.1; 11.7 — цикл основ `extends` модулей стилей (решение 133) |
| P2616 | error | 13.3 | `'{path}' is a file of kind '{kind}', expected '{expected}'` | 10.2, 10.3; 11.7 — основа `extends` не модуль стилей |
| P2617 | error | 13.3 | `unknown parameter '{name}' of the fragment '{path}'` | 10.2 |
| P2618 | error | 13.3 | `part '{part}' not found in '{path}'` | 10.2 |
| P2619 | error | 13.3 | `unknown key '{key}': it is not in the key map of the project` | 9.3 |
| P2620 | error | 13.3 | `'{name}' is exported by two fragments; separate them with ns= or rename=` | 10.4 |
| P2621 | error | 13.3 | `'{name}' is defined in the document and exported by a fragment; use override=True or rename=` | 10.4 |
| P2622 | error | 13.3 | `the module name '{name}' is not an identifier or is reserved` | 10.3, решение 52 |
| P2623 | error | 13.3 | `only definitions are allowed in a module: \|def, \|let, \|code:, \|import` | 10.3, решение 52 |
| P2624 | error | 13.3 | `'{name}' is not a public name of the module '{module}'` | 10.3, решение 52 |
| P2625 | error | 13.3 | `standard library module '{name}' is not available at this prototype stage` | 13.1 |
| P2626 | error | 13.3 | `the parameter 'features' must be a list of strings` | 9.2, решение 53 |
| P2629 | error | 13.3 | `'{value}' in column '{column}' is not a valid {type}` | 10.5, решение 51 |
| P2630 | error | 13.3 | `invalid data: {problem}` | 10.5, решения 25, 51 |
| P2632 | error | 13.3 | `\|call needs a function as its first argument` | 3.2 |
| P2633 | error | 13.3 | `a computed style must be a style name (a string), found {type}` | 4.3 |
| P2634 | error | 13.3 | `the parameter name '{name}' is not an identifier` | 2.3 |
| P2635 | warning | 13.8a | `placeholder left in the document: '{text}'` | 4.2 |
| P2636 | error | 13.9d | `the heading gets level {level} after level_shift={shift}; the deepest level is 6` | 10.2, 10.7, П3 |
| P2637 | error | Э2 | `'{name}' is not defined in the fragment and cannot be exported` | 10.4, решение 135 |
| P2638 | warning | Э2 | `'@export' in a module has no effect: every name of a module without a leading '_' is public` | 10.3, решение 135 |
| P2639 | warning | 18.1 | `'{path}' lies outside the project: the symbolic link '{link}' leads to '{target}'; keep that directory together with the project to rebuild the document` | 10.1, решение 136 |
| P2701 | warning | 13.9 | `the standard library does not support the document language '{lang}'; English forms are used` | библ. 1, решение 115 |
| P2702 | error | 13.9 | `unknown language '{lang}' in lang=; supported: {allowed}` | библ. 1, решение 115 |
| P2703 | error | 13.9 | `{function}: a float is not accepted in money calculations` | библ. 3 |
| P2704 | error | 13.9 | `{function}: the value {value} is out of range ({range})` | библ. 4, 5 |
| P2705 | error | 13.9 | `unknown currency '{code}'` | библ. 3 |
| P2706 | error | 13.9 | `unknown unit '{code}'` | библ. 6 |
| P2707 | error | 13.9 | `units '{a}' and '{b}' measure different quantities` | библ. 6 |
| P2708 | error | 13.9 | `{function}: the case '{value}' is not supported; allowed: {allowed}` | библ. 4, 5 |
| P2709 | error | 13.9 | `{function}: unknown gender '{value}'; allowed: {allowed}` | библ. 4 |
| P2710 | error | 13.9 | `fmt_date: the template shows the time of day {placeholder}` | библ. 5 |
| P2711 | error | 13.9 | `{function}: unknown placeholder '{placeholder}' in the template` | библ. 5 |
| P2712 | error | 13.9 | `{function}: unknown form '{format}'; allowed: {allowed}` | библ. 3, 5 |
| P2713 | error | 13.9 | `calendar: unknown key '{key}'; allowed: {allowed}` | библ. 5 |
| P2714 | error | 13.9 | `calendar: invalid value of '{key}' (weekend: mon … sun; dates without a time of day)` | библ. 5 |
| P2715 | error | 13.9 | `calendar: the date {date} is both a working day and a day off` | библ. 5, решение 115 |
| P2716 | error | 13.9 | `plural: a fractional number needs the form frac=` | библ. 7, решение 115 |
| P2717 | error | 13.9 | `{function}: the step must be greater than zero` | библ. 2 |
| P2718 | error | 13.9 | `split: the weights must be a non-empty list of non-negative numbers with a positive sum` | библ. 3 |
| P2719 | error | 13.9 | `currency '{code}' has no form frac for the language {lang}` | библ. 1, 3, решение 115 |
| P2720 | error | 13.9 | `qty: only a symmetric tolerance is supported (a number in tol=)` | библ. 6 |
| P2721 | error | 13.9 | `{function}: the argument '{arg}' must be {expected}, not {type}` | библ. 1–7 |
| P2722 | error | 13.9 | `{function}: {count} forms are expected for the language {lang}, {given} given` | библ. 1, 3, 7 |
| P2723 | error | 13.9 | `{function}: the fractional part has more than {places} digits` | библ. 4 |
| P2724 | error | 13.9c | `{function}: an item has no field '{key}'` | библ. 8 |
| P2725 | error | 13.9c | `{function}: a value of type {type} cannot be a group key` | библ. 8 |
| P2727 | error | 13.9c | `{function}: the argument {value} is outside the domain of the function` | библ. 9 |
| P2728 | error | 18.3 | `{function}: {size} bytes do not fit a QR code with error correction {ecc} up to version {version}` | библ. 10, решение 137 |
| P2729 | error | 18.3 | `{function}: the character '{char}' cannot be written in {encoding}` | библ. 10, решение 137 |
| P3101 | error | 13.4 | `unknown property '{prop}' of the {kind} style '{name}'` | 11.3, решение 57 |
| P3102 | error | 13.4 | `invalid value of '{prop}': expected {expected}` | 11.3, решение 57 |
| P3103 | error | 13.4 | `style '{name}' is defined twice in the same layer` | 11.7 |
| P3104 | error | 13.4 | `'{name}' is both a paragraph and a character style` | 11.2 |
| P3105 | error | 13.4 | `unknown parent style '{parent}' of '{name}'` | 11.2 |
| P3106 | error | 13.4 | `the parent '{parent}' of '{name}' is a {kind} style, expected a {expected} style` | 11.2 |
| P3107 | error | 13.4 | `cycle of style inheritance: {chain}` | 11.2 |
| P3108 | error | 13.4 | `unknown style '{name}'` | 4.3 |
| P3109 | error | 13.4 | `'{name}' is a {kind} style; a {expected} style is required here` | 4.3 |
| P3110 | error | 13.4 | `invalid style name '{name}': a letter followed by letters, digits, '_', '-'` | 11.2 |
| P3111 | error | 13.4 | `the style name '{name}' is already used by a style with other properties` | 11.4, решение 56 |
| P3112 | error | 13.4 | `unknown {scale} step '{step}'` | 11.4 |
| P3113 | error | 13.4 | `only the parameters before=, after=, indent= are allowed here, not '{name}'` | 11.4 |
| P3114 | error | 13.4 | `styles cannot be defined here (the top level of an \|import module)` | 11.7, решение 59 |
| P3115 | error | 13.4 | `unknown construct '{key}' for structure_styles / \|set` | 4.5, 11.5, решение 60 |
| P3118 | warning | 13.4 | `direct formatting \|fmt: changing the style in Writer will not affect this text` | 4.4, 11.8, 14.2 |
| P3120 | error | 13.4 | `unknown structure profile '{name}'; expected business or report` | 5.1 |
| P3121 | error | 13.9 | `list style '{name}': the format '{format}' (Cyrillic letters) needs a document in Ukrainian or Russian` | 11.3, решения 115, 133 (только для стилей, которые документ использует) |
| P3122 | error | 13.9d | `list item {number} has no letter: the level allows {count} letters ('{letters}')` | 11.2, 5.4, П1 |
| P4101 | error | 13.6 | `invalid ID '{id}': an ASCII letter followed by letters, digits, '_', '-', '.'` | 5.6 |
| P4102 | error | 13.6 | `duplicate ID '{id}'` | 5.6 |
| P4103 | error | 13.6 | `a fragment with the ID '{id}' is included twice without ns=` | 5.6, решение 74 |
| P4104 | error | 13.6 | `unknown argument '{name}' of {command}` | 5 |
| P4105 | error | 13.6 | `the argument '{name}' of {command} must be {expected}` | 5 |
| P4201 | error | 13.6 | `skipped heading level: level {level} after level {previous}` | 5.2 |
| P4202 | warning | 13.6 | `the text of a numbered heading starts with a number; the number is added automatically` | 5.2 |
| P4203 | warning | 13.6 | `a subsection follows the clauses of section {number}: clause and subsection numbers may coincide` | 5.3, решение 68 |
| P4204 | error | 13.6 | `skipped clause level: a level-{level} clause without a parent clause` | 5.3 |
| P4205 | error | 13.6 | `unknown clause '{id}' in continues= (the clause must precede)` | 5.3 |
| P4206 | error | 13.6 | `continues='{id}': the target must be a clause of the same section, scope and level` | 5.3 |
| P4207 | error | 13.6 | `start= and continues= cannot be used together` | 5.4 |
| P4208 | error | 13.6 | `unknown list '{name}' in continues= (the list must precede)` | 5.4 |
| P4209 | error | 13.6 | `duplicate list name '{name}'` | 5.4 |
| P4210 | error | 13.6 | `duplicate or reserved scope name '{name}'` | 5.5 |
| P4211 | error | 13.6 | `annex letter '{letter}' is not among the annex letters '{letters}'` | 5.5, решение 71 |
| P4212 | error | 13.8a | `heading level {value} is not an integer from 1 to 6` | 5.2, решение 114 |
| P4301 | error | 13.6 | `unknown reference target '{id}'` | 5.7 |
| P4302 | error | 13.6 | `the reference target '{id}' is excluded by a condition` | 5.7, решение 75 |
| P4303 | warning | 13.6 | `the reference target '{id}' is excluded by the condition {condition} (kept by --review)` | 5.7, решение 75 |
| P4304 | error | 13.6 | `unsuitable reference mode '{mode}' for the {kind} '{id}'` | 5.7, решение 76 |
| P4305 | error | 13.6 | `no reference labels for the document language '{language}'` | 5.7, решение 72 |
| P4306 | error | 13.6 | `no form '{case}' of the label '{key}' for the language '{language}'` | 5.7, решение 72 |
| P4307 | error | 13.6 | `unknown reference mode '{mode}'; expected number, label, title or page` | 5.7 |
| P4308 | error | 13.12 | `the reference to '{id}' of another document cannot show a page number (mode 'page')` | 5.7, решение 121 |
| P4309 | error | 13.12 | `the target '{id}' is found in several referenced documents: {documents}` | 5.7, решение 121 |
| P4401 | error | 13.6 | `unknown list kind '{kind}'; expected figure, table, abbr or index` | 5.9 |
| P4402 | error | 13.6 | `invalid structure setting {setting}: '{value}'; expected {expected}` | 5.1–5.10 |
| P5101 | error | 13.7 | `invalid value of '{name}' in col(): '{value}'` | 6.3 |
| P5102 | error | 13.7 | `invalid column width '{value}'; expected "40mm", "30%", "*", "auto" or "20mm..60mm"` | 6.3 |
| P5103 | error | 13.7 | `row {row}: the cells take {used} positions, {free} positions are free (spans counted)` | 6.5, решение 83 |
| P5104 | error | 13.7 | `rows={rows} goes beyond the end of the table ({remaining} rows remain)` | 6.5 |
| P5105 | error | 13.7 | `'{text}' is not a value of the column type {type}` | 6.8, решение 77 |
| P5106 | error | 13.7 | `{name}() is a table formula function; it is allowed only in a cell formula \|=(…)` | 6.8, решение 81 |
| P5107 | error | 13.7 | `unknown table column '{column}'` | 6.8 |
| P5108 | error | 13.7 | `row {row} is outside the table (rows 1–{rows})` | 6.8, решение 81 |
| P5109 | error | 13.7 | `{function}(): a value of type {type} is not a number` | 6.8, решение 81 |
| P5110 | error | 13.7 | `{function}() of no values` | 6.8, решение 81 |
| P5111 | error | 13.7 | `cycle of cell formulas: {chain}` | 6.8 |
| P5112 | warning | 13.7 | `the metrics of the font '{font}' are not available (font file or fontTools missing); column widths are approximate` | 6.3 |
| P5113 | warning | 13.7 | `the minimum widths of the columns {columns} do not fit; the columns are narrowed` | 6.3 |
| P5114 | error | 13.7 | `the formula cannot be written as a Writer formula (live=True)` | 6.8, решение 82 |
| P5115 | error | 13.9d | `\|table(data=…): row {row} has no field '{field}'` | 6.2, П4 |
| P5301 | warning | 16.2 | `segment {segment}: there is no block of the track '{track}'; the cell gets a placeholder` | 7.7, решение 134 |
| P5302 | error | 16.2 | `'\|{command}' {where}` | 7.7, решение 134 |
| P5303 | error | 16.2 | `'{what}' is not allowed directly inside '\|{container}'` | 7.7, решение 134 |
| P5304 | error | 16.2 | `'\|{command}' is not allowed inside a segment of \|parallel` | 7.7, решение 134 |
| P5305 | error | 16.2 | `{command}: {problem}: {value}` | 7.7, решение 134 |
| P5306 | error | 16.2 | `repeated segment ID '{id}'` | 7.7, решение 134 |
| P5307 | error | 16.5 | `\|track("{track}"): {problem}` | 7.7, решение 134 |
| P5308 | warning | 16.2 | `the standard library does not support the language '{lang}' of the track '{track}'; English forms are used` | 7.7, решение 134 |
| P5310 | warning | 16.4 | `segment {segment}, track '{track}': {found} where the primary track has {expected}` | 7.7, решение 134 |
| P5311 | warning | 16.4 | `segment {segment}, track '{track}': numbers and identifiers differ from the primary track: missing {missing}; extra {extra}` | 7.7, решение 134 |
| P5312 | warning | 16.4 | `segment {segment}, track '{track}': IDs differ from the primary track: missing {missing}; extra {extra}` | 7.7, решение 134 |
| P5313 | warning | 16.4 | `segment {segment}, track '{track}': targets of references differ from the primary track: missing {missing}; extra {extra}` | 7.7, решение 134 |
| P5314 | warning | 16.4 | `segment {segment}, track '{track}': names in \|(…) differ from the primary track: missing {missing}; extra {extra}` | 7.7, решение 134 |
| P5315 | warning | 16.4 | `\|parallel: the track '{track}' ends with the {kind} counter {value}, the primary track with {primary}` | 7.7, решение 134 |
| P5316 | warning | 16.3 | `the footnotes restart by {restart}: Writer numbers the notes of the tracks of \|parallel together with the primary track` | 7.7, 5.10, решение 134 |
| P5320 | warning | 16.5 | `segment {segment}, track '{track}': the translation is outdated — the primary block changed after it was confirmed (rev {rev}, now {now})` | 7.7, решение 134 |
| P5321 | warning | 16.5 | `segment {segment}, track '{track}': the confirmed block changed after it was confirmed (rev {rev}, now {now})` | 7.7, решение 134 |
| P6101 | error | 13.8 | `cannot use the image '{path}': {reason}` | 8.1, решение 85 |
| P6102 | error | 13.8 | `invalid value of '{name}' of {command}: '{value}'` | 7, 8 |
| P6103 | error | 13.8 | `unknown page style '{name}'` | 7.2 |
| P6104 | error | 13.8 | `a page change is not allowed inside {where}` | 7.3 |
| P6105 | error | 13.8 | `no content after the page change up to the end of the document or environment` | 7.3 |
| P6106 | error | 13.8 | `{command} inside a group kept together` | 7.4 |
| P6107 | warning | 13.8 | `rotate= is not output yet: the image is written without rotation` | 8.5 |
| P6108 | warning | 13.8 | `the image '{path}' has the EXIF orientation {orientation}; it is not applied — rotate the file itself` | 8.2, решение 85 |
| P6109 | error | 13.8 | `invalid watermark '{value}': a text or img(…) is expected` | 8.6, решение 84 |
| P6110 | error | 14.12 | `invalid SVG text of svg=: {reason}` | 8.2, решение 131 |
| P6111 | error | 14.12 | `the SVG text of svg= must not contain DOCTYPE or ENTITY declarations` | 8.2, решение 131 |
| P6112 | error | 14.12 | `the SVG text of svg= refers to '{ref}' outside it: only '#…' and 'data:' references are allowed` | 8.2, решение 131 |
| P6113 | error | 14.12 | `\|{command}: the image is given by exactly one of a path, an img(…) value, key= or svg=` | 8.2, 8.3, решение 131 |
| P7001 | warning | 13.8a | `kind '{kind}' contradicts the sub-extension of '{name}', which implies '{implied}'; the key 'kind' is used` | 2.2, 14.2, решение 100 |
| P7101 | error | 13.11 | `a project file must have 'kind: project' in its header, found '{kind}'` | 10.6, решение 117 |
| P7102 | error | 13.11 | `invalid value of '{key}' in the project file: expected {expected}` | 10.6, решение 117 |
| P7103 | error | 13.11 | `build(): {problem}` | 10.7, решение 117 |
| P7104 | error | 13.11 | `the source '{path}' of the build target cannot be used: {reason}` | 10.7, решение 117 |
| P7105 | error | 13.11 | `unknown parameter '{name}' of the build target '{source}': it is declared neither in the document nor in the project` | 10.6, 10.7, решение 117 |
| P7106 | error | 13.11 | `the parameter '{name}' gets a value of type {type}, but it is declared with type {expected}` | 10.6, 10.7, решение 117 |
| P7107 | error | 13.11 | `the build target overrides the key '{key}', which is not in the key map of the project` | 9.3, 10.7, решение 117 |
| P7108 | error | 13.11 | `the output '{path}' of the build target is outside the project directory` | 10.7, решение 117 |
| P7109 | error | 13.11 | `the output '{path}' is written by several build targets` | 10.7, решение 117 |
| P7110 | error | 13.11 | `the document parameter '{name}' has type {type}, but the project parameter of the same name has type {expected}` | 10.6, решение 117 |
| P7111 | error | 13.11 | `{function}() is available only in the code section of the project file` | 10.6, 10.7, решение 117 |
| P7112 | error | 13.11 | `no key map: key= needs a project file with 'keys'` | 9.3, решение 117 |
| P7113 | error | 13.11 | `the key '{key}' points to a part of a file ('{value}'); '#part' is allowed only in \|include` | 9.3, решение 117 |
| P7114 | error | 13.11 | `key= cannot be combined with a path or part=` | 9.3, решение 117 |
| P7115 | warning | 13.11 | `'{name}' is exported by several fragments; on_conflict: {mode} keeps the {mode} export` | 10.4, решение 117 |
| P7116 | error | 13.11 | `\|document is allowed only on its own line in the text of the root document (also inside \|if and \|for), not in an environment, a part or a fragment` | 10.7, решения 117, 118 |
| P7117 | warning | 13.11 | `the key '{key}' in the header of a part is ignored: styles and structure settings come from the root document and the project` | 10.7, 14.2, решение 117 |
| P7118 | error | 13.11 | `invalid or repeated scope '{scope}' of \|document` | 10.7, 5.6, решения 117, 118 |
| P7119 | error | 13.11 | `the document '{path}' is outside the directory of the project '{project}'` | 10.6, 14.1, решение 117 |
| P7120 | error | 13.11 | `{option} cannot be used when building a project: the outputs are given by the targets` | 14.1, решение 117 |
| P7121 | error | 13.11 | `--dump-project needs a project file (project.p.prml)` | 14.1, решение 117 |
| P7122 | warning | 13.11 | `the project has no build targets` | 10.7, решение 117 |
| P7123 | error | 13.9d | `--param '{text}' must be written as NAME=VALUE` | 14.1, П2 |
| P7124 | error | 13.9d | `--param: the document '{path}' has no parameter '{name}' (neither its own nor of the project)` | 14.1, П2 |
| P7125 | error | 13.9d | `--param cannot be used when building a project: the parameters of targets are given in 'targets' and build()` | 14.1, 10.6, П2 |
| P7126 | error | 13.12 | `references: '{name}' is not a document of the project (ref_documents: {known})` | 10.6, решения 121, 129 |
| P7127 | error | 13.12 | `the referenced document '{name}' could not be evaluated ({errors} errors); build it on its own to see them` | 10.6, решение 121 |
| P7128 | error | 13.12 | `the referenced document '{name}' has neither a source nor a registry ({registry})` | 10.6, решение 121 |
| P7129 | warning | 13.12 | `the source of the referenced document '{name}' is not found: reference texts come from its registry {registry}` | 10.6, решение 121 |
| P7130 | error | 13.12 | `extends: '{path}' leads to a cycle of project files` | 10.6, решение 123 |
| P7131 | error | 13.12 | `extends: the project must lie inside the root of its base project '{path}'` | 10.6, решение 123 |
| P7132 | error | 14.2 | `--dump-structure and --dump-styles need a document, not a project file` | 14.1, решение 124 |
| P8001 | warning | 13.5 | `'{construct}' is not output yet (stage {stage}); a placeholder marks its place` | 15 |
| P8002 | error | 13.5 | `cannot write '{path}': {reason}` | 14.1 |
| P8003 | error | 13.5 | `PDF export needs LibreOffice: soffice or libreoffice is not found` | 14.1 |
| P8004 | error | 13.5 | `PDF export failed: {reason}` | 14.1 |
| P8006 | warning | 13.5 | `this block cannot be written inside a list item yet and is omitted` | 15 |
| P8007 | warning | 13.5 | `\|fmt: unknown or invalid property '{prop}'` | 4.4 |
| P8008 | warning | 13.6 | `page numbers in the PDF (contents, lists, page references) are not updated: {reason}` | 5.9, 14.1 |
| P8101 | warning | 19.1 | `'{construct}' has no counterpart in the export and is left out (page layout: headers, footers, page numbers)` | 14.1, решение 139 |
| P8102 | error | 19.1 | `the export to this format needs pandoc: pandoc is not found (https://pandoc.org; --to json writes the AST without it)` | 14.1, решение 139 |
| P8103 | error | 19.1 | `pandoc failed: {reason}` | 14.1, решение 139 |
| P9101 | error | 13.10 | `unknown admonition kind '{kind}'; allowed: {allowed}` | 9.1, решение 116 |
| P9102 | error | 13.10 | `the admonition is empty: no text, hazard= or consequence=` | 9.1, решение 116 |
| P9103 | warning | 13.10 | `'{kind}' without hazard=: name the kind and source of the hazard` | 9.1, 14.2, решение 116 |
| P9104 | warning | 13.10 | `hazard= and consequence= are ignored for '{kind}'` | 9.1, решение 116 |
| P9105 | warning | 13.10 | `the styles module function admonition() is not used in language version 1.1; blocks are formatted by styles` | 9.1, решение 116 |
| P9106 | warning | 13.10 | `this \|if defines names in its branches and is not shown with all variants in the --review mode` | 9.2, решение 116 |
| P9201 | error | 13.10 | `unknown abbreviation '{name}'` | 9.4, решение 116 |
| P9202 | error | 13.10 | `the abbreviation '{name}' is defined with different expansions` | 9.4, решение 116 |
| P9203 | error | 13.10 | `show=False needs the expansion: \|abbr("{name}", "…", show=False)` | 9.4, решение 116 |
| P9204 | warning | 13.10 | `abbreviations(first="short") without \|list_of("abbr"): the expansions are written nowhere` | 9.4, решение 116 |
| P9205 | warning | 13.10 | `\|list_of("abbr"): the document defines no abbreviations; the list is not written` | 5.9, 9.4, решение 116 |
| P9206 | error | 13.10 | `abbreviations({key}=…): invalid value '{value}'; allowed: {allowed}` | 9.4, решение 116 |
| P9207 | error | 13.10 | `\|abbr needs the abbreviation as the first argument (a string)` | 9.4, решение 116 |
| P9301 | error | 13.10 | `\|index needs a non-empty term (a string) and an optional sub= string` | 9.5, решение 116 |

### Примечания к кодам

- **P0001** — временный код прототипа: команда принята, но её часть ещё не реализована на текущем подэтапе (`build` до 13.5, `fmt` до 13.13). Перед выпуском удаляется.
- **P0002** — сбой транслятора (исключение Python). Сообщение содержит тип и текст исключения; трассировка выводится с `--debug`.
- **P1102** — текст `{problem}` берётся из PyYAML и не переводится. Если PyYAML сообщает место начала конструкции (например, открывающую `[`), оно добавляется как `note` с позицией.
- **P1104** — предупреждение, а не ошибка: неизвестный ключ не используется, но может быть опечаткой. При неизвестном `kind` (P1106) неизвестные ключи не проверяются, чтобы не дублировать сообщения.
- **P1114, P1115** — предупреждения о значениях, которые в YAML 1.1 (Kit, PyYAML) читались иначе. `vat: yes` в YAML 1.2 — строка `"yes"`; `code: 01234567` — целое 1234567, а код ЄДРПОУ потерял бы ведущий ноль. Спецификация этих предупреждений не требует; прототип добавляет их как защиту от типичных ошибок при переходе с Kit. Подавляются кавычками.
- **P1201–P1206** — лексические ошибки после `|` и во фрагментах Python. P1204–P1206 находит сканер `syntax/pyscan.py` до вызова `ast.parse`; позиция — открывающая скобка или начало строкового литерала.
- **P1207** — `{problem}` — текст `SyntaxError` из `ast` (английский, не переводится); позиция переводится из координат фрагмента в координаты файла.
- **P1208** — решение 30: f-строка, которую Python 3.12+ читает как одну, а токенизатор 3.11 — как несколько, отклоняется независимо от версии интерпретатора.
- **P1216–P1219** — баланс окружений. Закрытие с чужим тегом закрывает ближайшее подходящее внешнее окружение; все вложенные получают P1216. Не подходящее ни к чему закрытие пропускается (P1217/P1218).
- **P1226** — содержимое `|table:` и `|row:` (грамматика, §3.5): блок разбирается, чтобы не сбить синхронизацию, но в дерево не попадает.
- **P5301–P5308** — параллельные потоки (§7.7, решение 134): P5303 выдаёт и парсер (строка, недопустимая в `\|parallel`), и вычислитель (вставка фрагмента, блок вне блока потока в сегменте); P5304 проверяется после вычисления, поэтому находит и команды из фрагментов и макросов; P5305 — единое сообщение об описании потоков и аргументах `\|segment`/`\|track` с переведённой причиной.
- **P1236–P1238** — предупреждения линтера из §14.2. P1236 выдаётся только для строковых форм с текстом (`|>`, `|-`, `|!`, `|.Name:`, `|name:`), не для заголовков и команд без тела.
- **P1242** — общая ошибка «ожидается X после Y»; X — переводимый ключ `expect.*`.
- **P21xx** — статическая проверка белого списка §12.2 (`core/check.py`). Выполняется для всех фрагментов Python документа в `primula check`, даже для кода, который не будет вычисляться. Блок кода с запрещённой конструкцией не регистрируется целиком.
- **P2102** — имена вида `__x__` и атрибуты, начинающиеся с `_`, ведут к внутренним механизмам Python; ядро их не допускает.
- **P2105, P2318, P2501** — решение 40: верхний уровень кода делится на определения (ленивые, замораживаемые) и действия; изменение замороженного значения — P2318 с подсказкой построить значение генератором списка или функцией.
- **P2321, P2322** — текст `{problem}` формирует ядро на английском (как `SyntaxError` в P1207); перевод — при необходимости позже.
- **P24xx** — лимиты §12.8 (решение 113): время одного вычисления (P2406), рекурсия (P2402), размер значения (P2403 — коллекция, P2404 — строка; общий ключ `size`). P2402 срабатывает и как защита, если раньше языкового лимита кончится стек Python. Время всей сборки — P0004 (`--timeout`), память процесса — P0005.
- **P2502, P2503** — линтер имён §3.9 (`evaluate/lint.py`): смесь латиницы, кириллицы и греческого в одном имени (названия алфавитов переводятся: ключи `scripts.*`); пара имён, различающихся только похожими буквами (упрощённая таблица омоглифов вместо полного UTS #39).
- **P7001** — расхождение `kind` и подрасширения файла (§2.2): действует `kind`.
- **P71xx** — файл проекта и сборка (подэтап 13.11, решение 117): заголовок проекта (P7101–P7102), цели и `build()` (P7103–P7109, P7120–P7122), параметры проекта и документа (P7110, P7106), `build()`/`batch_mode()` вне секции кода проекта (P7111), карта ключей (P7112–P7114, неизвестный ключ — P2619), `on_conflict` (P7115), части `|document` (P7116–P7118), `--project` (P7119).
- **P26xx** — вычисление документа (подэтап 13.3, решения 47–54). P2604 — предупреждение линтера (решение 47): число, дата или длина в тексте без функции оформления. P2610 также срабатывает для экспорта из фрагмента, подключённого внутри `|if`/`|for`/`|def`. P2629/P2630 указывают позицию в файле данных, место вызова `load_*` — кадром стека. P2635 — каждый заполнитель `|?{…}`, оставшийся в вычисленном документе (§4.2; с `--strict` — ошибка); заполнитель в неотобранной ветке `|if` не считается.
- **P27xx** — стандартная библиотека (подэтап 13.9, документ библиотеки v1.1, решение 115): язык (P2701 — предупреждение один раз на документ), аргументы и диапазоны, словари валют и единиц, шаблоны дат, календарь. Ошибки числа аргументов функций библиотеки — P2321 ядра.
- **P9xxx** — средства технической документации (подэтап 13.10, решение 116): блоки `|!` (P91xx), сокращения (P92xx), алфавитный указатель (P93xx).
- **P31xx** — стили (подэтап 13.4, решения 55–61). P3108 о неизвестном стиле выдаётся один раз на имя. P3118 — предупреждение о прямом форматировании `|fmt` (§14.2).

## Удалённые коды

- P8005 (warning, 13.5: лишние ячейки строки отбрасывались) — удалён в 13.7: несоответствие числа ячеек — ошибка P5103 (решение 83).
- P1108 (error, 13.0: недопустимый режим строк) — удалён в 13.8a: режим `para` удалён (решение 107), ключ `lines` — ошибка P1116.
- P1237 (warning, 13.1: строка продолжала пункт списка в режиме `para`) — удалён в 13.8a: режим `para` удалён (решение 107).
- P2302 (error, 13.2: смешение `decimal` и `float` — ошибка) — удалён в 13.8a: смешение приводит к `float` (решение 108).
- P2401 (error, 13.2: лимит шагов интерпретатора) — удалён в 13.8a: модель шага убрана, лимитов три (решение 113).
- P2726 (warning, 13.9c: `typography(nbsp_short=True)` к выводу ODT не применялся) — удалён в 13.9d: настройка применяется при записи ODT (документ библиотеки, раздел 7).
- P2405 (error, 13.2: лимит цифр целого числа) — удалён в 13.8a: потолок 64 значащих цифр — правило типа `decimal`, ошибка P2309 (решение 108).
