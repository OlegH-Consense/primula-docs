# Приложение В. Ключи YAML-заголовка

Сгенерировано `tools/author_docs.py appendices` из справочника транслятора; не править вручную.

| Ключ | Файлы | Тип | Назначение | Пример → результат | § |
| --- | --- | --- | --- | --- | --- |
| `kind` | document, fragment, module, styles, project | string | вид файла; следует из подрасширения (.f, .m, .s, .p), в проекте обязателен | `kind: document` | 2.2 |
| `primula` | document, fragment, module, styles, project | mapping | объявление языка: {version: "1.1"}, при необходимости версия библиотеки | `primula: {version: "1.1"}` | 2.3 |
| `primula.version` | document, fragment, module, styles, project | string | версия языка; принимается только 1.1 | `version: "1.1"` | 2.3 |
| `primula.stdlib` | document, fragment, module, styles, project | string | минимальная версия стандартной библиотеки | `stdlib: "1.1"` | 13 |
| `doc` | document | mapping | метаданные ODT документа; в тексте \|(doc.title) | `doc:` | 2.3 |
| `doc_defaults` | project | mapping | значения по умолчанию метаданных (doc:) всех документов проекта; документ переопределяет их поштучно | `doc_defaults:` | 10.6 |
| `doc.title` | document | string | название (dc:title) (рекомендуемый) | `title: "Договір поставки"` | 2.3 |
| `doc_defaults.title` | project | string | название (dc:title) | `title: "Договір поставки"` | 10.6 |
| `doc.subject` | document | string | тема (dc:subject) | `subject: "Поставка обладнання"` | 2.3 |
| `doc_defaults.subject` | project | string | тема (dc:subject) | `subject: "Поставка обладнання"` | 10.6 |
| `doc.description` | document | string | описание (dc:description) | `description: "Типова форма"` | 2.3 |
| `doc_defaults.description` | project | string | описание (dc:description) | `description: "Типова форма"` | 10.6 |
| `doc.creator` | document | string | автор (meta:initial-creator, dc:creator) (рекомендуемый) | `creator: "Іван Петренко"` | 2.3 |
| `doc_defaults.creator` | project | string | автор (meta:initial-creator, dc:creator) (рекомендуемый) | `creator: "Іван Петренко"` | 10.6 |
| `doc.organization` | document | string | организация (пользовательское свойство) | `organization: "ТОВ «Постачальник»"` | 2.3 |
| `doc_defaults.organization` | project | string | организация (пользовательское свойство) (рекомендуемый) | `organization: "ТОВ «Постачальник»"` | 10.6 |
| `doc.language` | document | language | язык документа (dc:language); иначе язык проекта (рекомендуемый) | `language: uk-UA` | 2.3 |
| `doc_defaults.language` | project | language | язык документа (dc:language); иначе язык проекта | `language: uk-UA` | 10.6 |
| `doc.identifier` | document | string | номер документа (пользовательское свойство) | `identifier: "Д-2026-017"` | 2.3 |
| `doc_defaults.identifier` | project | string | номер документа (пользовательское свойство) | `identifier: "Д-2026-017"` | 10.6 |
| `doc.revision` | document | string | редакция (пользовательское свойство) | `revision: "2"` | 2.3 |
| `doc_defaults.revision` | project | string | редакция (пользовательское свойство) | `revision: "2"` | 10.6 |
| `doc.status` | document | string | статус (пользовательское свойство) | `status: "проєкт"` | 2.3 |
| `doc_defaults.status` | project | string | статус (пользовательское свойство) | `status: "проєкт"` | 10.6 |
| `doc.created` | document | date | дата создания (meta:creation-date); иначе дата сборки (рекомендуемый) | `created: 2026-10-12` | 2.3 |
| `doc_defaults.created` | project | date | дата создания (meta:creation-date); иначе дата сборки | `created: 2026-10-12` | 10.6 |
| `doc.modified` | document | date | дата изменения (dc:date); иначе дата сборки | `modified: 2026-10-16` | 2.3 |
| `doc_defaults.modified` | project | date | дата изменения (dc:date); иначе дата сборки | `modified: 2026-10-16` | 10.6 |
| `doc.keywords` | document | strings | ключевые слова (meta:keyword): строка или список | `keywords: [договір, поставка]` | 2.3 |
| `doc_defaults.keywords` | project | strings | ключевые слова (meta:keyword): строка или список | `keywords: [договір, поставка]` | 10.6 |
| `params` | document, fragment, project | mapping | параметры со значениями по умолчанию; цель или --param их переопределяет | `params: {vat: true, delivery_days: 5}` | 10.6 |
| `structure` | document | mapping | настройки профиля структуры документа | `structure: {numbering: {headings: false}}` | 5.1 |
| `styles` | document, project | paths | модули стилей: список путей или один путь (std/styles/default — встроенный) | `styles: [styles/business.s.prml]` | 11.7 |
| `references` | document | list | документы проекта, на цели которых ссылается документ (имена из ref_documents проекта) | `references: [contract]` | 5.7 |
| `defaults` | styles | mapping | свойства по умолчанию: шрифт, размер, язык | `defaults: {font: Roboto, size: 11pt, language: uk-UA}` | 11.1 |
| `paragraphs` | styles | mapping | стили абзацев | `paragraphs:` | 11.2 |
| `characters` | styles | mapping | стили символов | `characters:` | 11.2 |
| `blocks` | styles | mapping | стили блоков | `blocks:` | 11.2 |
| `tables` | styles | mapping | стили таблиц | `tables:` | 11.2 |
| `lists` | styles | mapping | стили списков | `lists:` | 11.2 |
| `frames` | styles | mapping | стили врезок | `frames:` | 11.2 |
| `extends` | styles | path | базовый модуль стилей, подключается слоем перед этим (решение 133) | `extends: std/styles/business` | 11.7 |
| `pages` | styles | mapping | стили страниц | `pages:` | 11.2 |
| `name` | project | string | название проекта | `name: "Договори 2026"` | 10.6 |
| `language` | project | language | язык документов по умолчанию | `language: uk-UA` | 10.6 |
| `extends` | project | path | базовый проект: его параметры, ключи, документы для ссылок, стили и метаданные по умолчанию наследуются | `extends: ../../project.p.prml` | 10.6 |
| `on_conflict` | project | string | конфликты экспорта фрагментов: error, first, last | `on_conflict: error` | 10.4 |
| `keys` | project | mapping | карта ключей: имя → путь | `keys: {logo: assets/logo.svg}` | 9.3 |
| `limits` | project | mapping | лимиты ядра: time, recursion, size | `limits: {time: 20, recursion: 500, size: 10_000_000}` | 12.8 |
| `limits.time` | project | number | лимит времени, секунды | `time: 20` | 12.8 |
| `limits.recursion` | project | int | лимит глубины рекурсии | `recursion: 500` | 12.8 |
| `limits.size` | project | int | лимит размера значений | `size: 10_000_000` | 12.8 |
| `build_date` | project | date | фиксированная дата сборки (today() и даты по умолчанию) | `build_date: 2026-10-12` | 12.7 |
| `targets` | project | list | цели сборки primula build project.p.prml | `targets:` | 10.7 |
| `targets[].source` | project | path | исходный документ | `- source: contract.prml` | 10.7 |
| `targets[].output` | project | path | выходной ODT | `output: out/contract.odt` | 10.7 |
| `targets[].params` | project | mapping | значения параметров цели | `params: {vat: false}` | 10.7 |
| `targets[].keys` | project | mapping | ключи цели | `keys: {logo: assets/other.svg}` | 10.7 |
| `targets[].pdf` | project | any | также PDF: true или его путь | `pdf: true` | 10.7 |
| `ref_documents` | project | mapping | документы, на которые ссылаются другие (references: документа): имя: путь или {source, registry} | `ref_documents: {contract: contract.prml}` | 10.6 |
