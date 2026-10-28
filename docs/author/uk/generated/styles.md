# Додаток Д. Стилі комплекту

Згенеровано `tools/author_docs.py appendices` з довідника транслятора; не правити вручну.

## std/styles/default

Вбудована основа: стилі конструкцій, підключається, якщо модулі стилів не названо.

Основа: немає. Типовий шрифт: Liberation Sans, 11pt.

| Стиль | Тип | Властивості в модулі |
| --- | --- | --- |
| `AbbreviationList` | table | frame: none, rules: none, padding: [0.5mm, 2mm, 0.5mm, 0mm], repeat_header: false, parent: TableGrid |
| `Admonition` | paragraph | keep_together: true, parent: Body |
| `AdmonitionCaution` | paragraph | bold: true, color: #9C6500, parent: AdmonitionText |
| `AdmonitionDanger` | paragraph | bold: true, color: #C00000, parent: AdmonitionText |
| `AdmonitionNotice` | paragraph | bold: true, color: #1F4E9E, parent: AdmonitionText |
| `AdmonitionTable` | table | frame: none, rules: none, padding: [1mm, 2mm, 1mm, 2mm], paragraph: AdmonitionText, may_break: false, space_before: 3mm, space_after: 3mm, parent: TableGrid |
| `AdmonitionTableCaution` | table | parent: AdmonitionTable |
| `AdmonitionTableDanger` | table | parent: AdmonitionTable |
| `AdmonitionTableNotice` | table | parent: AdmonitionTable |
| `AdmonitionTableWarning` | table | parent: AdmonitionTable |
| `AdmonitionText` | paragraph | align: left, space_after: 1mm, keep_with_next: false, parent: Body |
| `AdmonitionWarning` | paragraph | bold: true, color: #E36C09, parent: AdmonitionText |
| `AppendixDesignation` | paragraph | align: right, keep_with_next: true, space_after: 0mm, parent: Body |
| `AppendixSubtitle` | paragraph | align: right, keep_with_next: true, space_after: 2mm, parent: Body |
| `AppendixTitle` | paragraph | bold: true, align: center, keep_with_next: true, space_before: 2mm, space_after: 4mm, parent: Body |
| `Body` | paragraph | align: justify, line_height: 115%, space_after: 2mm, first_line: 0mm, widows: 2, orphans: 2 |
| `BodyCentered` | paragraph | align: center, parent: Body |
| `BodyCompact` | paragraph | size: 10pt, line_height: 110%, space_after: 1mm, parent: Body |
| `BodyIndented` | paragraph | first_line: 10mm, parent: Body |
| `BodyLeft` | paragraph | align: left, parent: Body |
| `BodyRight` | paragraph | align: right, parent: Body |
| `BulletList` | list | levels: {1: {type: bullet, bullet: •, left: 5mm, hanging: 5mm}, 2: {type: bullet, bullet: –, left: 10mm, hanging: 5mm}, 3: {type: bullet, bullet: ◦, left: 15mm, hanging: 5mm}} |
| `Checklist` | list | paragraph: ListText, levels: {1: {type: bullet, bullet: ☐, left: 8mm, hanging: 5mm}} |
| `Clause` | paragraph | parent: Body |
| `Code` | character | font: Liberation Mono |
| `Contents1` | paragraph | align: left, space_after: 1mm, parent: Body |
| `Contents2` | paragraph | left: 5mm, parent: Contents1 |
| `Contents3` | paragraph | left: 10mm, parent: Contents1 |
| `Contents4` | paragraph | left: 15mm, parent: Contents1 |
| `Contents5` | paragraph | left: 20mm, parent: Contents1 |
| `Contents6` | paragraph | left: 25mm, parent: Contents1 |
| `ContentsTitle` | paragraph | bold: true, size: 12pt, align: center, keep_with_next: true, space_after: 4mm, parent: Body |
| `DashList` | list | paragraph: ListText, levels: {1: {type: bullet, bullet: –, left: 7mm, hanging: 4mm}, 2: {type: bullet, bullet: –, left: 14mm, hanging: 4mm}} |
| `DefinedTerm` | character | bold: true |
| `Emphasis` | character | italic: true |
| `Endnote` | paragraph | parent: Footnote |
| `Figure` | paragraph | align: center, keep_with_next: true, space_before: 2mm, space_after: 1mm, parent: Body |
| `FigureCaption` | paragraph | align: center, space_before: 1mm, space_after: 2mm, parent: Body |
| `Footer` | paragraph | size: 9pt, align: center, space_after: 0mm, parent: Body |
| `Footnote` | paragraph | size: 9pt, align: left, line_height: 100%, space_after: 0mm, left: 4mm, first_line: -4mm, parent: Body |
| `Group` | block | keep_together: true |
| `Header` | paragraph | size: 9pt, align: center, space_after: 0mm, parent: Body |
| `Heading` | paragraph | bold: true, align: left, keep_with_next: true, space_before: 4mm, space_after: 2mm, parent: Body |
| `Heading1` | paragraph | size: 14pt, parent: Heading |
| `Heading2` | paragraph | size: 13pt, parent: Heading |
| `Heading3` | paragraph | size: 12pt, parent: Heading |
| `Heading4` | paragraph | size: 11pt, parent: Heading |
| `Heading5` | paragraph | size: 11pt, italic: true, parent: Heading |
| `Heading6` | paragraph | size: 11pt, bold: false, italic: true, parent: Heading |
| `IndexEntry` | paragraph | align: left, space_after: 1mm, parent: Body |
| `IndexEntry2` | paragraph | left: 5mm, parent: IndexEntry |
| `Landscape` | page | orientation: landscape, parent: Portrait |
| `LatinLetterList` | list | paragraph: ListText, levels: {1: {type: number, format: a, suffix: ), left: 9mm, hanging: 6mm}, 2: {type: bullet, bullet: –, left: 18mm, hanging: 4mm}} |
| `LetterList` | list | paragraph: ListText, levels: {1: {type: number, format: а, suffix: ), left: 9mm, hanging: 6mm}, 2: {type: bullet, bullet: –, left: 18mm, hanging: 4mm}} |
| `ListText` | paragraph | align: left, space_after: 1mm, parent: Body |
| `MixedList` | list | paragraph: ListText, levels: {1: {type: number, format: 1, suffix: ., left: 9mm, hanging: 6mm}, 2: {type: bullet, bullet: –, left: 18mm, hanging: 4mm}} |
| `Note` | paragraph | size: 9pt, italic: true, align: left, parent: Body |
| `NoteAnchor` | character | position: super |
| `NoteLabel` | character |  |
| `NoteList` | list | paragraph: Note, levels: {1: {type: number, format: 1, suffix: ., left: 5mm, hanging: 5mm}} |
| `NumberedList` | list | levels: {1: {type: number, format: 1, suffix: ., left: 6mm, hanging: 6mm}, 2: {type: number, format: 1, suffix: ., left: 12mm, hanging: 8mm}, 3: {type: number, format: a, suffix: ), left: 18mm, hanging: 6mm}} |
| `ParallelHeader` | paragraph | bold: true, align: left, keep_with_next: true, parent: Body |
| `ParallelTable` | table | width: [percent, 100], frame: none, rules: none, padding: 0mm, repeat_header: true, space_before: 3mm, space_after: 3mm |
| `Placeholder` | character | background: #FFFF00 |
| `Portrait` | page | size: A4, orientation: portrait, margin: [20mm, 15mm, 20mm, 25mm] |
| `Preformatted` | paragraph | font: Liberation Mono, size: 9pt, align: left, line_height: 100%, space_after: 0mm, widows: 1, orphans: 1, parent: Body |
| `Quote` | paragraph | italic: true, left: 7mm, right: 5mm, space_before: 2mm, space_after: 3mm, parent: Body |
| `Reference` | character |  |
| `ReviewFalse` | character | background: #F8D7D7 |
| `ReviewLabel` | paragraph | size: 8pt, italic: true, color: #555555, align: left, space_after: 0mm, keep_with_next: true, parent: Body |
| `ReviewTrue` | character | background: #D9F2D9 |
| `SmallPrint` | paragraph | align: left, size: 9pt, line_height: 110%, space_after: 1.5mm, color: #333333, parent: Body |
| `SmallText` | character | size: 9pt |
| `StrikeText` | character | strike: true |
| `Strong` | character | bold: true |
| `SubClause` | paragraph | left: 5mm, parent: Clause |
| `Subscript` | character | position: sub |
| `Superscript` | character | position: super |
| `TableCaption` | paragraph | align: left, keep_with_next: true, space_before: 2mm, space_after: 1mm, parent: Body |
| `TableCompact` | table | padding: 0.8mm, paragraph: TableTextCompact, header_paragraph: TableHeaderCompact, parent: TableGrid |
| `TableGrid` | table | width: [percent, 100], frame: 0.5pt solid #000000, rules: all, padding: 1mm, paragraph: TableText, header_bold: true, repeat_header: true |
| `TableHeader` | paragraph | bold: true, parent: TableText |
| `TableHeaderCompact` | paragraph | bold: true, parent: TableTextCompact |
| `TableNoBorders` | table | frame: none, rules: none, padding: [1mm, 2mm, 1mm, 0mm], repeat_header: false, header_background: none, parent: TableGrid |
| `TableText` | paragraph | align: left, space_after: 0mm, parent: Body |
| `TableTextCompact` | paragraph | size: 9pt, line_height: 105%, parent: TableText |
| `Underline` | character | underline: true |

## std/styles/business

Договори, акти, рахунки, протоколи; поля й відступи — за ДСТУ 4163:2020.

Основа: `std/styles/default`. Типовий шрифт: Liberation Serif, 12pt.

| Стиль | Тип | Властивості в модулі |
| --- | --- | --- |
| `Approval` | paragraph | left: 100mm, space_after: 0mm, keep_with_next: true, keep_together: true, parent: BodyLeft |
| `ApprovalTitle` | paragraph | bold: true, space_after: 1mm, parent: Approval |
| `AttachmentLabel` | paragraph | size: 10pt, space_before: 3mm, keep_with_next: true, parent: BodyLeft |
| `Body` (доповнює) | paragraph | align: justify, line_height: 115%, space_after: 2mm |
| `ClauseContinuation` | paragraph | left: 7mm, parent: Body |
| `DatePlace` | paragraph | space_before: 2mm, space_after: 4mm, keep_with_next: true, parent: BodyLeft |
| `Details` | paragraph | size: 10pt, line_height: 110%, space_after: 1mm, parent: BodyLeft |
| `DetailsTitle` | paragraph | bold: true, size: 11pt, space_after: 2mm, keep_with_next: true, parent: Details |
| `DocumentSubtitle` | paragraph | space_after: 2mm, keep_with_next: true, keep_together: true, parent: BodyCentered |
| `DocumentTitle` | paragraph | size: 14pt, bold: true, space_before: 3mm, space_after: 2mm, keep_with_next: true, keep_together: true, parent: BodyCentered |
| `DocumentVersion` | paragraph | size: 9pt, color: #444444, space_after: 4mm, keep_with_next: true, parent: BodyCentered |
| `FigureCaption` (доповнює) | paragraph | space_after: 3mm, size: 10pt |
| `Footer` (доповнює) | paragraph | color: #333333 |
| `FormLabel` | paragraph | bold: true, space_after: 1mm, keep_with_next: true, parent: BodyLeft |
| `Header` (доповнює) | paragraph | color: #333333 |
| `Heading` (доповнює) | paragraph | align: left, keep_together: true |
| `Heading1` (доповнює) | paragraph | size: 12pt, space_before: 4mm, space_after: 2mm |
| `Heading2` (доповнює) | paragraph | size: 12pt, space_before: 3mm, space_after: 1.5mm |
| `Heading3` (доповнює) | paragraph | size: 12pt, space_before: 2mm, space_after: 1mm |
| `Heading4` (доповнює) | paragraph | size: 12pt, italic: true, space_before: 2mm, space_after: 1mm |
| `Illustration` | frame | width: 110mm |
| `IllustrationSmall` | frame | width: 70mm |
| `IllustrationWide` | frame | width: 160mm |
| `Logo` | frame | width: 40mm |
| `LogoSmall` | frame | width: 25mm |
| `Note` (доповнює) | paragraph | size: 10pt, italic: false, space_before: 1mm |
| `OrganizationName` | paragraph | bold: true, space_after: 2mm, keep_with_next: true, parent: BodyLeft |
| `Placeholder` (доповнює) | character | background: #FFF2CC |
| `Portrait` (доповнює) | page | margin: [20mm, 10mm, 20mm, 30mm], footer_gap: 3mm, footer_min_height: 5mm |
| `Preamble` | paragraph | space_after: 3mm, parent: Body |
| `SignatureLine` | paragraph | space_after: 3mm, keep_together: true, parent: BodyLeft |
| `SignatureRole` | paragraph | space_before: 5mm, space_after: 2mm, keep_with_next: true, keep_together: true, parent: BodyLeft |
| `TableCaption` (доповнює) | paragraph | space_before: 3mm, space_after: 1.5mm, size: 10pt |
| `TableForm` | table | cols: [30%, 70%], parent: TableGrid |
| `TableGrid` (доповнює) | table | frame: 0.5pt solid #999999, padding: 1.5mm, border: 0.5pt solid #999999, header_background: #EEEEEE, header_paragraph: TableHeader, keep_rows: true, space_before: 1mm, space_after: 3mm |
| `TableParties` | table | cols: [50%, 50%], paragraph: Details, header_paragraph: DetailsTitle, header_background: none, padding: [0.5mm, 3mm, 0.5mm, 0mm], may_break: false, parent: TableNoBorders |
| `TableSchedule` | table | cols: [35%, 45%, 20%], parent: TableGrid |
| `TableServices` | table | cols: [52%, 12%, 18%, 18%], parent: TableGrid |
| `TableText` (доповнює) | paragraph | size: 10pt, line_height: 110%, widows: 1, orphans: 1 |

## std/styles/letter

Службові листи за ДСТУ 4163:2020.

Основа: `std/styles/business`. Типовий шрифт: Liberation Serif, 12pt.

| Стиль | Тип | Властивості в модулі |
| --- | --- | --- |
| `BodyIndented` (доповнює) | paragraph | space_after: 1mm |
| `Executor` | paragraph | space_before: 8mm, space_after: 0mm, keep_together: true, parent: SmallPrint |
| `LetterFirst` | page | next: Portrait, parent: Portrait |
| `LetterSubject` | paragraph | bold: true, space_before: 6mm, space_after: 4mm, right: 97mm, keep_with_next: true, parent: BodyLeft |
| `LetterheadDetails` | paragraph | size: 9pt, line_height: 105%, space_after: 0mm, right: 97mm, parent: BodyLeft |
| `LetterheadName` | paragraph | bold: true, size: 12pt, space_after: 1mm, right: 97mm, parent: BodyLeft |
| `OutgoingNumber` | paragraph | size: 11pt, space_before: 4mm, space_after: 0mm, right: 97mm, parent: BodyLeft |
| `Recipient` | paragraph | left: 90mm, line_height: 100%, space_after: 1.5mm, keep_with_next: true, parent: BodyLeft |
| `Salutation` | paragraph | space_after: 3mm, keep_with_next: true, parent: BodyCentered |

## std/styles/technical

Настанови, інструкції, технічні описи.

Основа: `std/styles/default`. Типовий шрифт: Liberation Sans, 10.5pt.

| Стиль | Тип | Властивості в модулі |
| --- | --- | --- |
| `Body` (доповнює) | paragraph | align: left, line_height: 120%, space_after: 2mm |
| `Code` (доповнює) | character | background: #F2F2F2 |
| `Command` | character | font: Liberation Mono, bold: true |
| `DefinitionTerm` | paragraph | bold: true, space_after: 0.5mm, keep_with_next: true, parent: Body |
| `DefinitionText` | paragraph | left: 8mm, space_after: 2mm, parent: Body |
| `FileName` | character | font: Liberation Mono |
| `Heading1` (доповнює) | paragraph | size: 15pt, space_before: 6mm, space_after: 3mm |
| `Heading2` (доповнює) | paragraph | size: 13pt, space_before: 5mm, space_after: 2mm |
| `Heading3` (доповнює) | paragraph | size: 11.5pt, space_before: 4mm, space_after: 1.5mm |
| `Key` | character | font: Liberation Mono, bold: true, background: #E8E8E8 |
| `MenuItem` | character | bold: true |
| `Portrait` (доповнює) | page | margin: [20mm, 15mm, 20mm, 25mm] |
| `Preformatted` (доповнює) | paragraph | size: 9pt, space_after: 2mm, left: 3mm, right: 3mm, background: #F2F2F2, space_before: 1mm |
| `ProgramOutput` | paragraph | color: #333333, parent: Preformatted |
| `StepList` | list | paragraph: ListText, levels: {1: {type: number, format: 1, suffix: ., left: 8mm, hanging: 8mm}, 2: {type: number, format: а, suffix: ), left: 16mm, hanging: 6mm}} |
| `StepResult` | paragraph | italic: true, left: 8mm, space_after: 2mm, parent: Body |
| `TableGrid` (доповнює) | table | frame: 0.5pt solid #808080, border: 0.5pt solid #808080, header_background: #E6E6E6, header_paragraph: TableHeader |
| `TableRevisions` | table | cols: [16mm, 24mm, *, 40mm], parent: TableCompact |
| `Variable` | character | font: Liberation Mono, italic: true |

## std/styles/report

Звіти за ДСТУ 3008:2015.

Основа: `std/styles/default`. Типовий шрифт: Liberation Serif, 14pt.

| Стиль | Тип | Властивості в модулі |
| --- | --- | --- |
| `AppendixDesignation` (доповнює) | paragraph | align: center, first_line: 0mm, bold: true |
| `AppendixSubtitle` (доповнює) | paragraph | align: center, first_line: 0mm |
| `AppendixTitle` (доповнює) | paragraph | bold: false, first_line: 0mm |
| `Body` (доповнює) | paragraph | align: justify, line_height: 150%, space_after: 0mm, first_line: 12.5mm |
| `Contents1` (доповнює) | paragraph | space_after: 0mm, first_line: 0mm |
| `ContentsTitle` (доповнює) | paragraph | parent: StructuralHeading |
| `Figure` (доповнює) | paragraph | first_line: 0mm |
| `FigureCaption` (доповнює) | paragraph | space_before: 1mm, space_after: 3mm, first_line: 0mm |
| `Footer` (доповнює) | paragraph | first_line: 0mm |
| `Footnote` (доповнює) | paragraph | size: 12pt |
| `Header` (доповнює) | paragraph | size: 12pt, align: right, first_line: 0mm |
| `Heading` (доповнює) | paragraph | align: left, space_before: 7mm, space_after: 7mm, first_line: 12.5mm, keep_together: true |
| `Heading1` (доповнює) | paragraph | size: 14pt, odf: {fo:text-transform: uppercase} |
| `Heading2` (доповнює) | paragraph | size: 14pt |
| `Heading3` (доповнює) | paragraph | size: 14pt |
| `Heading4` (доповнює) | paragraph | size: 14pt, italic: false |
| `ListText` (доповнює) | paragraph | space_after: 0mm, first_line: 0mm, line_height: 150% |
| `Note` (доповнює) | paragraph | size: 12pt, italic: false, align: justify, line_height: 100%, first_line: 12.5mm |
| `ParallelHeader` (доповнює) | paragraph | first_line: 0mm |
| `Portrait` (доповнює) | page | margin: [20mm, 10mm, 20mm, 25mm] |
| `Preformatted` (доповнює) | paragraph | size: 12pt, first_line: 0mm |
| `ReportTitle` | page | next: Portrait, parent: Portrait |
| `StructuralHeading` | paragraph | align: center, first_line: 0mm, page_break_before: true, parent: Heading1 |
| `TableCaption` (доповнює) | paragraph | space_before: 3mm, space_after: 1mm, first_line: 12.5mm |
| `TableText` (доповнює) | paragraph | first_line: 0mm, size: 12pt, line_height: 100% |
| `TitlePageName` | paragraph | bold: true, space_before: 40mm, space_after: 6mm, odf: {fo:text-transform: uppercase}, parent: TitlePageText |
| `TitlePageText` | paragraph | first_line: 0mm, space_after: 2mm, parent: BodyCentered |

## std/styles/compact

Пам'ятки, довідки, шпаргалки.

Основа: `std/styles/default`. Типовий шрифт: Liberation Sans, 9pt.

| Стиль | Тип | Властивості в модулі |
| --- | --- | --- |
| `Body` (доповнює) | paragraph | align: left, line_height: 112%, space_after: 1mm, widows: 1, orphans: 1 |
| `BulletList` (доповнює) | list | levels: {1: {type: bullet, bullet: •, left: 4mm, hanging: 3mm}, 2: {type: bullet, bullet: –, left: 8mm, hanging: 3mm}, 3: {type: bullet, bullet: ◦, left: 12mm, hanging: 3mm}} |
| `Footer` (доповнює) | paragraph | size: 7.5pt |
| `Header` (доповнює) | paragraph | size: 7.5pt |
| `Heading` (доповнює) | paragraph | space_before: 2.5mm, space_after: 1mm |
| `Heading1` (доповнює) | paragraph | size: 12pt |
| `Heading2` (доповнює) | paragraph | size: 10.5pt |
| `Heading3` (доповнює) | paragraph | size: 9.5pt |
| `Heading4` (доповнює) | paragraph | size: 9pt |
| `Heading5` (доповнює) | paragraph | size: 9pt |
| `Heading6` (доповнює) | paragraph | size: 9pt |
| `ListText` (доповнює) | paragraph | space_after: 0.5mm |
| `Note` (доповнює) | paragraph | size: 8pt |
| `Portrait` (доповнює) | page | margin: [12mm, 12mm, 12mm, 12mm] |
| `Preformatted` (доповнює) | paragraph | size: 8pt, background: #F2F2F2, left: 1mm, right: 1mm |
| `SmallPrint` (доповнює) | paragraph | size: 7.5pt |
| `TableGrid` (доповнює) | table | frame: 0.4pt solid #808080, padding: 0.7mm, border: 0.4pt solid #808080, header_background: #E6E6E6, header_paragraph: TableHeader |
| `TableText` (доповнює) | paragraph | size: 8.5pt, line_height: 105% |
| `TableTextCompact` (доповнює) | paragraph | size: 8pt |
