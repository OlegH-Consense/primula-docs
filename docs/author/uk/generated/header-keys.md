# Додаток В. Ключі YAML-заголовка

Згенеровано `tools/author_docs.py appendices` з довідника транслятора; не правити вручну.

| Ключ | Файли | Тип | Призначення | Приклад → результат | § |
| --- | --- | --- | --- | --- | --- |
| `kind` | document, fragment, module, styles, project | string | вид файлу; випливає з підрозширення (.f, .m, .s, .p), у проєкті обов'язковий | `kind: document` | 2.2 |
| `primula` | document, fragment, module, styles, project | mapping | оголошення мови: {version: "1.1"}, за потреби версія бібліотеки | `primula: {version: "1.1"}` | 2.3 |
| `primula.version` | document, fragment, module, styles, project | string | версія мови; приймається лише 1.1 | `version: "1.1"` | 2.3 |
| `primula.stdlib` | document, fragment, module, styles, project | string | мінімальна версія стандартної бібліотеки | `stdlib: "1.1"` | 13 |
| `doc` | document | mapping | метадані ODT документа; у тексті \|(doc.title) | `doc:` | 2.3 |
| `doc_defaults` | project | mapping | типові значення метаданих (doc:) усіх документів проєкту; документ перевизначає їх поштучно | `doc_defaults:` | 10.6 |
| `doc.title` | document | string | назва (dc:title) (рекомендований) | `title: "Договір поставки"` | 2.3 |
| `doc_defaults.title` | project | string | назва (dc:title) | `title: "Договір поставки"` | 10.6 |
| `doc.subject` | document | string | тема (dc:subject) | `subject: "Поставка обладнання"` | 2.3 |
| `doc_defaults.subject` | project | string | тема (dc:subject) | `subject: "Поставка обладнання"` | 10.6 |
| `doc.description` | document | string | опис (dc:description) | `description: "Типова форма"` | 2.3 |
| `doc_defaults.description` | project | string | опис (dc:description) | `description: "Типова форма"` | 10.6 |
| `doc.creator` | document | string | автор (meta:initial-creator, dc:creator) (рекомендований) | `creator: "Іван Петренко"` | 2.3 |
| `doc_defaults.creator` | project | string | автор (meta:initial-creator, dc:creator) (рекомендований) | `creator: "Іван Петренко"` | 10.6 |
| `doc.organization` | document | string | організація (користувацька властивість) | `organization: "ТОВ «Постачальник»"` | 2.3 |
| `doc_defaults.organization` | project | string | організація (користувацька властивість) (рекомендований) | `organization: "ТОВ «Постачальник»"` | 10.6 |
| `doc.language` | document | language | мова документа (dc:language); інакше мова проєкту (рекомендований) | `language: uk-UA` | 2.3 |
| `doc_defaults.language` | project | language | мова документа (dc:language); інакше мова проєкту | `language: uk-UA` | 10.6 |
| `doc.identifier` | document | string | номер документа (користувацька властивість) | `identifier: "Д-2026-017"` | 2.3 |
| `doc_defaults.identifier` | project | string | номер документа (користувацька властивість) | `identifier: "Д-2026-017"` | 10.6 |
| `doc.revision` | document | string | редакція (користувацька властивість) | `revision: "2"` | 2.3 |
| `doc_defaults.revision` | project | string | редакція (користувацька властивість) | `revision: "2"` | 10.6 |
| `doc.status` | document | string | статус (користувацька властивість) | `status: "проєкт"` | 2.3 |
| `doc_defaults.status` | project | string | статус (користувацька властивість) | `status: "проєкт"` | 10.6 |
| `doc.created` | document | date | дата створення (meta:creation-date); інакше дата збирання (рекомендований) | `created: 2026-10-12` | 2.3 |
| `doc_defaults.created` | project | date | дата створення (meta:creation-date); інакше дата збирання | `created: 2026-10-12` | 10.6 |
| `doc.modified` | document | date | дата зміни (dc:date); інакше дата збирання | `modified: 2026-10-16` | 2.3 |
| `doc_defaults.modified` | project | date | дата зміни (dc:date); інакше дата збирання | `modified: 2026-10-16` | 10.6 |
| `doc.keywords` | document | strings | ключові слова (meta:keyword): рядок або список | `keywords: [договір, поставка]` | 2.3 |
| `doc_defaults.keywords` | project | strings | ключові слова (meta:keyword): рядок або список | `keywords: [договір, поставка]` | 10.6 |
| `params` | document, fragment, project | mapping | параметри зі значеннями за замовчуванням; ціль або --param їх перевизначає | `params: {vat: true, delivery_days: 5}` | 10.6 |
| `structure` | document | mapping | налаштування профілю структури документа | `structure: {numbering: {headings: false}}` | 5.1 |
| `styles` | document, project | paths | модулі стилів: список шляхів або один шлях (std/styles/default — вбудований) | `styles: [styles/business.s.prml]` | 11.7 |
| `references` | document | list | документи проєкту, на цілі яких посилається документ (імена з ref_documents проєкту) | `references: [contract]` | 5.7 |
| `defaults` | styles | mapping | типові властивості: шрифт, розмір, мова | `defaults: {font: Roboto, size: 11pt, language: uk-UA}` | 11.1 |
| `paragraphs` | styles | mapping | стилі абзаців | `paragraphs:` | 11.2 |
| `characters` | styles | mapping | стилі символів | `characters:` | 11.2 |
| `blocks` | styles | mapping | стилі блоків | `blocks:` | 11.2 |
| `tables` | styles | mapping | стилі таблиць | `tables:` | 11.2 |
| `lists` | styles | mapping | стилі списків | `lists:` | 11.2 |
| `frames` | styles | mapping | стилі врізок | `frames:` | 11.2 |
| `extends` | styles | path | базовий модуль стилів, підключається шаром перед цим (рішення 133) | `extends: std/styles/business` | 11.7 |
| `pages` | styles | mapping | стилі сторінок | `pages:` | 11.2 |
| `name` | project | string | назва проєкту | `name: "Договори 2026"` | 10.6 |
| `language` | project | language | типова мова документів | `language: uk-UA` | 10.6 |
| `extends` | project | path | базовий проєкт: його параметри, ключі, документи для посилань, стилі й типові метадані успадковуються | `extends: ../../project.p.prml` | 10.6 |
| `on_conflict` | project | string | конфлікти експорту фрагментів: error, first, last | `on_conflict: error` | 10.4 |
| `keys` | project | mapping | карта ключів: ім'я → шлях | `keys: {logo: assets/logo.svg}` | 9.3 |
| `limits` | project | mapping | ліміти ядра: time, recursion, size | `limits: {time: 20, recursion: 500, size: 10_000_000}` | 12.8 |
| `limits.time` | project | number | ліміт часу, секунди | `time: 20` | 12.8 |
| `limits.recursion` | project | int | ліміт глибини рекурсії | `recursion: 500` | 12.8 |
| `limits.size` | project | int | ліміт розміру значень | `size: 10_000_000` | 12.8 |
| `build_date` | project | date | фіксована дата збирання (today() і типові дати) | `build_date: 2026-10-12` | 12.7 |
| `targets` | project | list | цілі збирання primula build project.p.prml | `targets:` | 10.7 |
| `targets[].source` | project | path | вихідний документ | `- source: contract.prml` | 10.7 |
| `targets[].output` | project | path | вихідний ODT | `output: out/contract.odt` | 10.7 |
| `targets[].params` | project | mapping | значення параметрів цілі | `params: {vat: false}` | 10.7 |
| `targets[].keys` | project | mapping | ключі цілі | `keys: {logo: assets/other.svg}` | 10.7 |
| `targets[].pdf` | project | any | також PDF: true або його шлях | `pdf: true` | 10.7 |
| `ref_documents` | project | mapping | документи, на які посилаються інші (references: документа): ім'я: шлях або {source, registry} | `ref_documents: {contract: contract.prml}` | 10.6 |
