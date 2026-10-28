<!-- translation: source=docs/author/ru/04-letter.md sections=aab2f7f4 7b6865b3 d22812c2 a2e9c85a -->
<!-- spec: 4.3 7.2 7.6 11.5 11.9 13 -->
# Official letter

A letter uses the styles set `std/styles/letter`. It builds on the business set `business` and follows DSTU 4163:2020: margins — left 30 mm, right 10 mm, top and bottom 20 mm; text with a paragraph indent of 10 mm, the addressee as a block 90 mm from the left margin, the page number from the second page at the top in the middle.

## Example

```prml
---
doc:
  title: "Щодо графіка технічної підтримки"
  language: uk-UA
styles: [std/styles/letter]
params:
  номер: "12/3"
  дата: 2026-10-16
  відправник: {назва: "ТОВ «Виконавець»", адреса: "вул. Сумська, 1, м. Харків, 61000", телефон: "+380 57 000 00 00", код: "00000000", керівник: "Петро ПЕТРЕНКО"}
  адресат: {посада: "Директору", назва: "ТОВ «Замовник»", особа: "Івану ІВАНЕНКУ"}
---
|.LetterheadName: |(відправник.назва)
|.LetterheadDetails: |(відправник.адреса), тел. |(відправник.телефон)
|.LetterheadDetails: Код ЄДРПОУ |(відправник.код)
|.OutgoingNumber: Вих. № |(номер) від |(fmt_date(дата, "short"))

|.Recipient: |(адресат.посада) |(адресат.назва)
|.Recipient: |(адресат.особа)

|.LetterSubject: |(doc.title)

|.Salutation: Шановний пане Іване!

Повідомляємо, що роботи з налаштування обладнання завершено, акт приймання-передачі підписано сторонами.

Пропонуємо погодити графік технічної підтримки на листопад — грудень 2026 року. Проєкт графіка додається.

|.AttachmentLabel: Додаток: проєкт графіка на 1 арк. в 1 прим.

|table(style="TableParties", header=0, cols=["60%", "40%"]):
|: Директор |& |(відправник.керівник)
|end table

|.Executor: Олена Коваленко +380 57 000 00 01
```

## Parts of the letter

| Part | Style | Note |
| --- | --- | --- |
| name and details of the sender | `LetterheadName`, `LetterheadDetails` | on the left, lines up to 73 mm |
| number and date | `OutgoingNumber` | “Вих. № … від …”; the date — `fmt_date(дата, "short")` |
| addressee | `Recipient` | each line is a separate paragraph of this style |
| heading of the text | `LetterSubject` | “Щодо …”, without a period |
| salutation | `Salutation` | centred |
| text | no style | ordinary paragraphs get `BodyIndented` — the set binds the text to it |
| attachments | `AttachmentLabel` | |
| signature | table `TableParties` | the position on the left, the name on the right on one line |
| executor | `Executor` | in small print at the end |

The first page of the letter has the page style `LetterFirst` without a number; the following pages are `Portrait` with the number at the top. The set does this; nothing needs writing in the text.

## Your own differences

If the organisation uses another letterhead, do not edit the set of the kit: make your own module over it and name it instead of the set (page [“Styles”](07-styles.md)):

```prml file=styles/бланк.s.prml
---
kind: styles
extends: std/styles/letter
paragraphs:
  LetterheadName: {size: 13pt, color: "#1F4E79"}
---
```

```prml
---
doc: {title: "Лист", language: uk-UA}
styles: [styles/бланк.s.prml]
---
|.LetterheadName: ТОВ «Приклад»

Текст листа.
```

A logo on the letterhead — `|img("assets/логотип.svg", style="LogoSmall")` at the beginning of the letter; the sizes of logos and illustrations (`LogoSmall`, `Logo`, `Illustration` …) are in the `business` set.
