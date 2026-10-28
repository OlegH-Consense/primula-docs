<!-- translation: source=primula-stdlib-v1.1-draft.ru.md sections=c006468f 71e8934f 703190a3 346d6868 9960ef22 8cc8e550 8f407fc9 0ef0e9b4 eb2f9192 1d0e8302 34437321 7a203b13 afcbcb88 -->
# Primula — standard library: specification v1.1-draft

14.10.2026 · an appendix to the specification of the Primula language v1.1-draft (`primula-spec-v1.1-draft.en.md`, the original is `primula-spec-v1.1-draft.ru.md`); English translation of the Russian original `primula-stdlib-v1.1-draft.ru.md` (where they differ, the original is normative); examples of business documents are in Ukrainian

## Contents

0. Status, versioning, order of implementation
1. Inclusion and language
2. Numbers
3. Money and VAT
4. In words
5. Dates and time
6. Values with units
7. Text
8. Data
9. Mathematics: `std/math`
10. QR codes and encodings

## 0. Status, versioning, order of implementation

### 0.1. Status

The document describes the standard library of the Primula language: the functions of the prelude and the modules `std/…`. The library evolves independently of the main specification: adding, extending and correcting functions needs no new release of the language specification unless it touches the core (section 12 of the main specification) and the grammar.

The main specification fixes only the contract of the library: the prelude is available without inclusion, modules are included with `|import("std/…")`, functions are deterministic and do no input or output (except `load_*` of the core). Everything else is in this document.

### 0.2. Versioning and compatibility

- The library version is `MAJOR.MINOR` (now `1.1-draft`; the numbering follows the language version); while the modules have the status `draft`, incompatible changes are allowed with a record in section 0.4.
- A file may require a minimum library version with the header key `primula: {stdlib: "1.1"}`; an older library is an error naming the missing function.
- Once a module has the status `stable`: adding functions and optional arguments — `MINOR`; changing the result of an existing function — `MAJOR`.
- The result of a library function is the same for the same arguments and the same library version (reproducible builds, section 14.3 of the main specification). The library version is written into the build report.
- Values that change by law (tax rates, the calendar of holidays) are not built into the library.

### 0.3. Order of implementation

The modules are independent and are implemented in stages. A stage is complete when the functions of its sections, tests after the examples of the tables and the behaviour for `uk`, `ru`, `en` are implemented.

| Stage | Sections | Content | Depends on |
| --- | --- | --- | --- |
| L1 | 1, 2, 4 | inclusion and language, numbers, numbers in words | — |
| L2 | 3 | money, VAT, currencies | L1 |
| L3 | 5 | dates and calendar | L1 (month names, dates in words) |
| L4 | 6 | values with units | L1 |
| L5 | 7 | text and typography | L1 |
| L6 | 8, 9 | data, `std/math` | — |

Status of modules: `draft` — content and results may change; `stable` — changes only by the rules of 0.2. All sections now have the status `draft`.

### 0.4. Changes from 0.1-draft

- Numbers (sections 2, 3, 4, 9): the type `int` is merged into `decimal`; an integer is a `decimal` with scale 0 (decision 108 of the main specification).
- Dates (section 5): the built-in type `datetime` instead of `date` and `days`; arithmetic — built-in operations; added `weeks`, `hours`, `minutes`, `fmt_time`, `fmt_datetime` and time placeholders.
- `date_words` (section 4) takes a `datetime`; the time of day is ignored.
- `std/math` (section 9) takes `decimal`.
- The minus sign on output is U+2212 (section 2); `percent` got `digits`; `round_to`, `split` refined.
- Fractional numbers: `frac` in `plural` and in the dictionary of currencies (sections 1, 3, 7); fractions and `ordinal` in section 4.
- A language other than uk, ru, en and a tag with a region (section 1); cases of `month_name` and `weekday`, `workdays(d, 0)`, priority and validation of the calendar (section 5); `qty_range`, `tol`, `convert` (section 6); `join_list`, `typography` (section 7).

## 1. Inclusion and language

- The prelude — the functions of sections 2–8 — is available without inclusion; special modules are included explicitly: `|import("std/math")`. Names of standard library modules start with `std/`.
- Functions follow the language of the document (`uk`, `ru`, `en`); the argument `lang=` overrides it. A tag with a region is reduced to the language (`uk-UA` → `uk`). If the document language is another one (`de-DE`), functions work as `en` and give a warning with a hint about `lang=` once per document; an unknown value of `lang=` is an error.
- The dictionaries of the library (currencies, units, case forms, months) are extended and overridden in a styles module.
- Values that change by law (tax rates, the calendar of holidays) are not built into the library: they are passed as arguments or taken from project data.

Functions of a styles module for the dictionaries of the library (settings merge by layers, like `numbering`, section 11.7 of the main specification); a call for an already known code or unit overrides only the given fields:

```python
currency("PLN", "uk", short="zł", units=("злотий", "злоті", "злотих"), frac="злотого", gender="m",
         minor=("грош", "гроші", "грошів"), minor_gender="m", minor_digits=2)
unit("rpm", "uk", symbol="об/хв", quantity="frequency", factor=1/60)
month_names("uk", nom=["січень", …], gen=["січня", …], loc=["січні", …])
typography(percent_space=True, nbsp_short=False, nbsp_words=["в", "у", …])
```

`units`, `minor` — three forms for uk and ru (1, 2–4, 5+), two for en; case forms in words are built by gender. `frac` — the genitive singular form for a fractional sum («12 500,50 гривні»); for uk and ru it is required for user currencies and is given for the built-in ones.

## 2. Numbers

| Function | Result (uk) |
| --- | --- |
| `num(12500, digits=2)` | «12 500,00» — groups separated by a no-break space, decimal comma |
| `num(x, digits=None)` | as many decimals as the value has |
| `percent(20)`, `percent(x, digits=None)` | «20 %» — a no-break space before the sign (DSTU ISO 80000-1); without the space — `typography(percent_space=False)`; decimals — as in `num` |
| `round_to(x, step)`, `ceil_to`, `floor_to` | rounding to a step: `round_to` — half away from zero; the result has the type of `x`; `step ≤ 0` — error |
| `round_money(x)` | rounding to hundredths, half away from zero |

Negative numbers are written with the minus sign U+2212 («−1 500,00») for uk, ru and en in `num`, `money`, `percent`, `qty` and table columns (DSTU ISO 80000-1). Parsing accepts both `-` and `−`; `str()` and ODF values keep the ASCII `-`.

## 3. Money and VAT

| Function | Result |
| --- | --- |
| `money(12500, "UAH")` | «12 500,00 грн» |
| `money_words(12500, "UAH")` | «дванадцять тисяч п'ятсот гривень 00 копійок» |
| `money_full(12500, "UAH")` | «12 500,00 грн (дванадцять тисяч п'ятсот гривень 00 копійок)» |

- The contract form by default: the sum in figures first, then in brackets in words, kopecks in figures.
- Parameters: `kop="digits"` (default) or `"words"`; `cap=True` — a capital first letter of the words; `currency_style="short"` («грн») or `"full"` («гривень»). With `"full"` the form of the word depends on the fractional part: zero — the form by the integer part («12 500,00 гривень»), otherwise `frac` («12 500,50 гривні»); for en a fractional sum is plural.
- Currencies: `UAH` (hryvnia, kopiyka — feminine), `USD` (US dollar, cent), `EUR` (euro — indeclinable, cent); the dictionary is extended in a styles module.
- `words(x, "UAH")` — the same as `money_words(x, "UAH")`.

VAT — the rate is passed explicitly (as an argument or from the project parameters); there is no default:

| Function | Value |
| --- | --- |
| `vat(net, rate)` | tax from the sum without tax |
| `with_vat(net, rate)` | sum with tax |
| `vat_in(gross, rate)` | tax contained in the sum with tax: `gross × rate / (100 + rate)` |
| `without_vat(gross, rate)` | sum without tax |

Results are rounded to kopecks. `split(total, [30, 70])` divides a sum by shares; the parts are rounded to kopecks, the rounding remainder is added to the last part, the parts add up to `total`.

Initial dictionary of currencies (the abbreviation follows the number after a no-break space in all languages):

| Code | uk: abbreviation / forms / minor unit | ru | en |
| --- | --- | --- | --- |
| UAH | грн / гривня, гривні, гривень (f) / копійка, копійки, копійок (f) | грн / гривна, гривны, гривен / копейка | UAH / hryvnia, hryvnias / kopiyka, kopiykas |
| USD | дол. США / долар США, долари США, доларів США (m) / цент, центи, центів (m) | долл. США / доллар США / цент | USD / US dollar, US dollars / cent, cents |
| EUR | євро / євро (indeclinable, n) / цент, центи, центів (m) | евро / евро / цент | EUR / euro, euros / cent, cents |

- The fractional part of any currency of the dictionary is written in figures («00 центів»), with `kop="words"` — in words by the gender of the minor unit. `currency_style="full"` — the form by the number («12 500,00 гривень»). An unknown code is an error; extension — `currency(…)`.
- A `float` in `money*`, `vat*`, `split`, `round_money` is an error with a hint about `dec(…)`; `decimal` is allowed (an integer is a `decimal` with scale 0). All money functions round to kopecks, half away from zero.
- `with_vat(net, rate)` = `net + vat(net, rate)`; `without_vat(gross, rate)` = `gross − vat_in(gross, rate)`: after rounding, the components always add up to the sum given in the document.

## 4. In words

| Function | Result |
| --- | --- |
| `words(21)` | «двадцять один» |
| `words(21, gender="f")` | «двадцять одна» |
| `words(5, case="gen")` | «п'яти» |
| `words(2.5)` | «дві цілих п'ять десятих» |
| `ordinal(3)` | «третій» |
| `ordinal(21, gender="m", case="gen")` | «двадцять першого» |
| `date_words(date(2026, 10, 12))` | «дванадцятого жовтня дві тисячі двадцять шостого року» (the time of day is ignored) |

`gender`: `"m"`, `"f"`, `"n"`; `case`: `nom`, `gen`, `dat`, `acc`, `ins`, `loc`; languages uk, ru, en (for en gender and case do not apply).

- `words` — integers up to 10¹⁵ − 1; a fractional part up to 6 digits («десятих» … «мільйонних»); negative numbers — «мінус …»; anything else is an error.
- Fractions: by the scale of the `decimal` value (`2.50` → «дві цілих п'ятдесят сотих»; for a `float` — its shortest decimal notation). A zero fractional part reads as an integer. A scale above 6 after dropping trailing zeros is an error. `case=` applies to all parts («двох цілих п'яти десятих»); `gender=` does not apply to fractions: the numerator agrees with the word «ціла/частина» («одна ціла п'ять десятих», «нуль цілих п'ять десятих»). en: «two point five», the digits of the fractional part one by one (2.05 → «two point zero five»).
- `ordinal(n)`: range 1 … 10¹⁵ − 1; zero, negative and fractional numbers are errors. The last word is inflected. Round thousands, millions and billions are one compound word, the forms are data of the library. uk (as estimated by the compiler, to be checked against the Ukrainian orthography of 2019): «двотисячний», «тритисячний», «чотиритисячний», «п'ятитисячний», «двадцятип'ятитисячний», «мільйонний», hundreds — «двохсотий», «трьохсотий», «чотирьохсотий», «п'ятисотий»; ru — «двухтысячный»; en — «twenty-first», «two thousandth».
- `date_words` for en: «the twelfth of October, two thousand twenty-six».

## 5. Dates and time

Date and time is the built-in type `datetime` (section 12.3 of the main specification): a moment without a time zone, precise to a second; a date is the moment at 00:00:00. There are no separate types `date` and `days`. Arithmetic — built-in operations: `dt ± n` — a shift by `n` days (`decimal` or `float`), `dt2 - dt1` — a `decimal` number of days, `float(dt)` — the serial number.

| Function | Result |
| --- | --- |
| `date(2026, 10, 12)`, `datetime(2026, 10, 12, 14, 30, 0)` | constructors of the type `datetime` |
| `date("2026-10-12")`, `datetime("2026-10-12T14:30")` | parsing an ISO string; a string with a time zone is an error |
| `dt + 5`, `dt - 5` | a shift by 5 days |
| `weeks(n)`, `hours(n)`, `minutes(n)` | a number of days: `dt + weeks(2)`, `dt + hours(36)` |
| `add_months(dt, 1)`, `add_years(dt, 1)` | a shift by months and years (31 → the last day of the month), the time is kept |
| `dt2 - dt1` | days, `decimal` (`date(2026, 10, 12) - date(2026, 10, 7)` → 5) |
| `fmt_date(dt, "short")` | «12.10.2026» |
| `fmt_date(dt, "long")` | «12 жовтня 2026 року» |
| `fmt_date(dt, "contract")` | «12» жовтня 2026 р. |
| `fmt_date(dt, "{d} {month_gen} {y} р.")` | any template |
| `fmt_time(dt, "short")` | «14:30» (with seconds when they are not zero: «14:30:15»); a template is allowed, the form `long` is an error |
| `fmt_datetime(dt, "short")` | «12.10.2026 14:30» |
| `fmt_datetime(dt, "long")` | «12 жовтня 2026 року, 14:30» |
| `fmt_datetime(dt, "{d}.{m}.{y} {hh}:{mi}")` | any template |
| `weekday(dt)`, `weekday(dt, case="acc")`, `month_name(dt, case="gen")` | name of the day of the week (`nom`, `acc` — «у понеділок»), name of the month (`nom`, `gen`, `loc` — «у жовтні»; other cases are errors) |

The formats `short` and `long` of `fmt_date` follow the numeric and the verbal-numeric ways of DSTU 4163:2020. `fmt_date` uses only the date; a time of day in a `fmt_date` template (`{hh}` etc.) is an error with a hint about `fmt_datetime`. The attribute `dt.weekday` (main specification, section 12.3) is the number of the day of the week 1–7, Monday is 1; the function `weekday(dt)` returns the name.

Working days: `workdays(d, 5, calendar=cal)`, `is_workday(d, calendar=cal)`. The calendar is project data (`cal = load_yaml("data/calendar-2026.yaml")`): weekly days off, holidays and transferred days. There is no built-in calendar, because the set of holidays and their effect change by law. The time of day of the argument `d` is ignored; `workdays` returns a date (00:00:00).

The number of whole days between dates: `int(d2 - d1)`. Moments are compared with the ordinary operators: values are normalised to a second, so `==` is exact.

Placeholders of the `fmt_date` and `fmt_datetime` templates: `{d}`, `{dd}` — day («2», «02»); `{m}`, `{mm}` — month as a number; `{y}`, `{yy}` — year («2026», «26»); `{month}`, `{month_gen}` — name of the month («жовтень», «жовтня»); `{weekday}` — day of the week; `{{` and `}}` — literal braces. Only for `fmt_datetime` and `fmt_time`: `{h}`, `{hh}` — hour 0–23 («9», «09»); `{mi}` — minute («5», «05» — always two digits); `{s}`, `{ss}` — second («7», «07»).

| Format | uk | ru | en |
| --- | --- | --- | --- |
| `fmt_date` `short` | 12.10.2026 | 12.10.2026 | 2026-10-12 |
| `fmt_date` `long` | 12 жовтня 2026 року | 12 октября 2026 года | 12 October 2026 |
| `fmt_date` `contract` | «12» жовтня 2026 р. | «12» октября 2026 г. | 12 October 2026 |
| `fmt_datetime` `short` | 12.10.2026 14:30 | 12.10.2026 14:30 | 2026-10-12 14:30 |
| `fmt_datetime` `long` | 12 жовтня 2026 року, 14:30 | 12 октября 2026 года, 14:30 | 12 October 2026, 14:30 |

YAML schema of a calendar (all keys are optional):

```yaml
weekend: [sat, sun]          # weekly days off (default)
holidays: [2026-01-01]       # public holidays, days off (datetime values without time)
workdays: [2026-01-10]       # working days on weekends (transfers)
rest_days: [2026-01-02]      # additional days off (transfers)
```

- `workdays(d, n, calendar=cal)` — `n` working days after `d` (`d` itself is not counted); `n < 0` — backwards; `n = 0` — `d` unchanged (00:00:00), even if `d` is a day off. Without `calendar=` all days except `sat` and `sun` are working days.
- Priority in a calendar: `workdays`, `holidays` and `rest_days` win over `weekend`. A date both in `workdays` and in `holidays` or `rest_days` is a contradiction of the data: an error of the calendar check.
- The library does not move days off automatically when a holiday falls on a weekend: the rules of transfer change by law and do not apply under martial law. All transfers are given by the data explicitly (`rest_days`, `workdays`).

## 6. Values with units

| Function | Result (uk) |
| --- | --- |
| `qty(230, "V")` | «230 В» — a no-break space |
| `qty_range(100, 240, "V")` | «100–240 В» (both bounds non-negative: an en dash without spaces); with a negative bound — «−20…+55 °C» (an ellipsis, a sign at the positive bound, zero without a sign) |
| `qty(50, "Hz", tol=1)` | «(50 ± 1) Гц» — only a symmetric tolerance; a tuple in `tol=` is an error |
| `qty(20, "degC")` | «20 °C» |
| `convert(1.5, "kW", "W")` | 1500: `decimal` for `decimal` (division — 28 significant digits), `float` for `float` |

Unit symbols are a dictionary by language, extended in a styles module. `convert` works within one physical quantity; incompatible units are an error.

Initial dictionary of units (symbols of DSTU ISO 80000 / SI; uk and ru in Cyrillic, en in Latin):

| Quantity | Units (code → uk) |
| --- | --- |
| voltage | `mV` мВ, `V` В, `kV` кВ |
| current | `mA` мА, `A` А |
| power | `W` Вт, `kW` кВт, `MW` МВт; apparent — `VA` В·А, `kVA` кВ·А (a separate quantity) |
| energy | `Wh` Вт·год, `kWh` кВт·год |
| frequency | `Hz` Гц, `kHz` кГц, `MHz` МГц |
| resistance | `Ohm` Ом, `kOhm` кОм, `MOhm` МОм |
| length | `mm` мм, `cm` см, `m` м, `km` км |
| area, volume | `m2` м², `m3` м³, `l` л, `ml` мл |
| mass | `g` г, `kg` кг, `t` т |
| time | `s` с, `min` хв, `h` год |
| pressure | `Pa` Па, `kPa` кПа, `MPa` МПа, `bar` бар |
| temperature | `degC` °C, `K` К |
| share | `%` % |

`convert` multiplies by the ratio of the factors within a quantity (`convert(1, "kVA", "W")` is an error); `degC` ↔ `K` — with the offset 273.15. A no-break space goes before `°C` and `%` (DSTU ISO 80000-1): «20 °C».

## 7. Text

| Function | Result |
| --- | --- |
| `plural(n, "день", "дні", "днів", frac="дня")` | the form by the number (uk, ru — three forms; en — two). A fractional `n`: the form `frac`; without it in uk and ru — an error with a hint; in en — the plural. A zero fractional part — the form by the integer |
| `join_list(["А", "Б", "В"], last="та")` | «А, Б та В»; the default conjunction: uk — «і», ru — «и», en — «and» (no Oxford comma); separator `sep=", "` |
| `cap(s)` | a capital first letter |
| `translit(s)` | transliteration by the document language or `lang=`: uk — Resolution of the Cabinet of Ministers of Ukraine No 55 («Київ» → «Kyiv», «зг» → «zgh», special initial «є, ї, й, ю, я»); ru — ICAO Doc 9303; en — unchanged |
| `sort_key(s)` | a sort key by the alphabet of the language: `sorted(names, key=sort_key)` |
| `nbsp_short(s)` | a no-break space after short prepositions and conjunctions («в», «з», «та», «і») |

Applying `nbsp_short` to all the text is turned on in a styles module: `typography(nbsp_short=True)`.

- `typography(percent_space=True)` — a space before `%` (default); `False` — «20%».
- `nbsp_words` by default: uk — а, в, є, і, й, о, у, з, зі, із, та, до, на, по, за, не, ні, що, як, від; ru — а, в, и, к, о, с, у, во, за, из, на, не, ни, по, со, то, что, как, от, до; en — a, an, the, of, to, in, on, at, by, or.
- `typography(nbsp_short=True)` replaces the spaces in all the text of the document when the ODT is written, including tables, headers and footers, captions and footnotes; it does not apply in verbatim blocks, code, monospaced ``|`{…}`` and Writer fields. `nbsp_short(s)` — to one string. The words come from `nbsp_words` or by the language of the root document (a part of a compound document with its own language gets the words of the root; a language other than uk, ru, en — the words of en). The spaces after a short word are replaced by one no-break space; the word boundary is seen through the boundaries of inline forms (`в |*{домі}`), a Writer field counts as a non-space character.

## 8. Data

| Function | Value |
| --- | --- |
| `group_by(items, key)` | a dictionary «key value → list of records», in the order of first appearance |
| `sum_by(items, key, value)` | sums of the field `value` by groups |
| `distinct(items, key)` | unique values of a field |

`key` and `value` — a field name or a function.

## 9. Mathematics: std/math

`sqrt`, `exp`, `log`, `log10`, `sin`, `cos`, `tan`, `atan2`, `pi`, `e` — the result is a `float`; `floor`, `ceil` — the result is a `decimal` with scale 0. The functions take `decimal` and `float`; a `decimal` is converted to `float` automatically (section 12.4 of the main specification), `floor` and `ceil` of a `decimal` are computed exactly. The set of functions (trigonometry in particular) is being refined — an open question in appendix 4.3 of the main specification. In a document the module is included explicitly: `|import("std/math")`; in the console of the evaluator (`primula console`, section 14.1 of the main specification) `math` is always available (decision 130).

## 10. QR codes and encodings

Decision 137. Building a QR code takes hundreds of thousands of steps that would take seconds in the core, so the encoder is a library function, and the formats on top of it (the NBU payment QR and others) are user libraries of modules.

| Function | Result |
| --- | --- |
| `qr_matrix(data, ecc="M", min_version=1, max_version=40, encoding="utf-8")` | the QR code of a text in byte mode (DSTU ISO/IEC 18004:2019): a record `{version, ecc, mask, size, rows}`; `rows` — strings of `"1"` (dark module) and `"0"` without the quiet zone |
| `qr_svg(data, ecc=…, min_version=…, max_version=…, encoding=…, size="30mm", quiet=4, circle=0)` | the same code as an SVG string for `\|img(svg=…)` (decision 131): dark modules as one path, `viewBox` in modules with the quiet zone `quiet`, width and height `size`; `circle` > 0 — a white circle of this diameter (in modules) in the centre |
| `base64url(text, encoding="utf-8")` | Base64URL (RFC 4648, section 5) of the bytes of a text, without the padding `=` |

- The version is the smallest of `min_version…max_version` that holds the bytes of `data` at the error correction level `ecc` (`L`, `M`, `Q`, `H`); if they do not fit — an error with the size of the data. The mask has the smallest penalty by the rules of the standard (the first one on a tie); the result is deterministic.
- `encoding` — `"utf-8"` or `"cp1251"` (Windows-1251); a character missing from the encoding is an error naming it.
- The circle `circle` hides the modules of the centre; the error correction level must cover them (for the NBU circle of 17–25 modules in versions 10–17 — `M` or `Q`). The image in the circle (a sign) is added to the SVG string by the library itself.
- A wrong level, encoding, version range, `size`, `quiet` (0–16) or a `circle` larger than the side of the code is an error «value out of range».
