<!-- translation: source=docs/author/ru/05-technical.md sections=02137544 c93230e8 6d9a08cf 2f941822 a38b9b9b 25051b97 87c7e86a d832855d -->
<!-- spec: 5.8 5.9 8.2 8.3 9.1 9.2 9.3 9.4 9.5 11.9 14.1 -->
# Technical documentation

Manuals, instructions and technical descriptions use the styles set `std/styles/technical` (or `report` — for reports after DSTU 3008). Below are the means that technical documents need: admonitions, variants for different versions of a product, abbreviations, an index, figures.

## Admonitions and notes

`|!("kind")` is semantic markup: the author names the kind, and the signal word in the document language, the colour and the look come from the styles.

| Kind | Word (uk) | When |
| --- | --- | --- |
| `danger` | НЕБЕЗПЕКА | imminent danger to life |
| `warning` | ПОПЕРЕДЖЕННЯ | possible danger to life or serious injury |
| `caution` | ОБЕРЕЖНО | possible minor injury |
| `notice` | УВАГА | possible damage to property |
| `note` | Примітка | explanation |
| `tip` | Порада | recommendation |

```prml
|!("warning", hazard="Висока напруга", consequence="Ураження електричним струмом"):
Перед обслуговуванням від'єднайте пристрій від мережі.

|- Вимкніть автоматичний вимикач.
|- Перевірте відсутність напруги.
|end!

|!("notice") Не встановлюйте пристрій поблизу джерел тепла.

|!("note") Значення наведено для температури 20 °C.
|!("note") Допуск — ±5 %.
```

- The line form `|!("kind") text` is a block of one paragraph; the environment `|!(…):` … `|end!` — of several paragraphs and lists.
- `danger` and `warning` need `hazard=` (the kind and source of the hazard); without it the check warns.
- Several `note` blocks in a row form a group “Примітки:” with numbers.

## Variants for different versions

One source text serves several versions of a product. The properties of a version are listed in the parameter `features`, and conditional parts are marked with `when=`:

```prml
---
doc: {title: "Настанова з експлуатації", language: uk-UA}
styles: [std/styles/technical]
params:
  модель: "X300"
  features: [wifi]
---
|< Підключення
|> Під'єднайте кабель живлення.
|>(when=has("wifi")) Підключіть пристрій до мережі Wi-Fi.
|>(when=has("bluetooth")) Увімкніть Bluetooth на телефоні.
|table(header=1, cols=["*", "30%"]):
|: Параметр |& Значення
|: Напруга |& 230|~В
|:(when=модель == "X300") Потужність |& 2,2|~кВт
|end table
|if(has("wifi")):
|< Бездротова мережа
|> Пристрій підтримує стандарт 802.11n.
|endif
```

- `when=` exists on any block command, environment and table row; `|if(…):` … `|endif` — for any group of blocks.
- `has("wifi")` is true when `wifi` is in `features`. The set of properties comes from the document header, the project or a build target of the project (`params: {features: [wifi, bluetooth]}` in `targets`): so the manuals of all versions are built from one text. The command line parameter `--param` does not take lists.
- Removed parts do not reach the ODT; numbering, the table of contents and references are computed over the remaining text. A reference to a removed part is an error.
- `primula build настанова.prml --review` builds all variants at once and marks every conditional part with its condition (green — included in the current version, red — not), and puts the watermark “НЕ ДЛЯ ВИПУСКУ” on the pages. So the whole text is reviewed in one file.

## Abbreviations

```prml
|abbr("ПЗ", "програмне забезпечення") встановлюється з диска.
Оновлення |abbr("ПЗ") виконується автоматично.
|list_of("abbr", title="ПЕРЕЛІК СКОРОЧЕНЬ")
```

At the first use the output is “програмне забезпечення (ПЗ)”, after that only “ПЗ”. The case of the expansion at this place — `text="програмного забезпечення"`. `|list_of("abbr")` builds the list of abbreviations as a table.

## Index, table of contents, lists

```prml
|toc(max_level=2, title="ЗМІСТ")
|< Живлення
Напруга|index("напруга живлення") подається через адаптер.
|list_of("index", title="ПОКАЖЧИК")
```

The table of contents, the lists of figures and tables (`|list_of("figure")`, `|list_of("table")`) and the alphabetical index are indexes that Writer updates; Writer fills their page numbers, or the translator when it builds a PDF.

## Figures

```prml
|figure(svg='<svg xmlns="http://www.w3.org/2000/svg" width="40mm" height="20mm"><rect x="1" y="1" width="38" height="18" fill="none" stroke="black"/></svg>', id="рис-схема"):
Схема підключення
|end figure
Див. |@("рис-схема", "label").
```

- `|figure(path or svg=…, id=…):` … `|end figure` — a numbered figure; the body is the caption (“Рисунок 1 — Схема підключення”). `|img(…)` — an image without number and caption.
- A file path is relative to the document: `|figure("assets/схема.svg", width="120mm")`. Formats — PNG, JPEG, SVG.
- `svg=` — an image from an SVG string computed by code (a chart, a scale, a QR code from a module function).
- Size — `width=` or `height=`; sizes by style — `style="Illustration"` (sets `business`, `letter`).

## Program text and interface

The `technical` set has styles for interface elements and commands:

```prml
---
doc: {title: "Інструкція", language: uk-UA}
styles: [std/styles/technical]
---
|list("StepList"):
|# Натисніть |.Key{Ctrl+S}.
|# Виберіть |.MenuItem{Файл → Зберегти} і вкажіть файл |.FileName{звіт.odt}.
|end list
|.StepResult: Файл буде збережено.

|.Preformatted: primula check звіт.prml
```

Character styles `Key`, `MenuItem`, `FileName`, `Command`, `Variable`; paragraph styles `Preformatted`, `ProgramOutput`, `StepResult`, `DefinitionTerm`/`DefinitionText`; the step list `StepList`; the table `TableRevisions` for a record of revisions. The full list — appendix [“Styles of the kit”](generated/styles.md). Text that must be kept letter for letter (a listing with `|` characters) goes into `|verbatim:` … `|end`.

## Shared fragments and keys

Repeated texts (general safety measures, warranty) go into fragments `*.f.prml` and are inserted with `|include`; in a project they can be swapped per version through the key map `keys:` — page [“Project”](06-project.md). Complete examples — `examples/03-manual` and `examples/06-safety`.
