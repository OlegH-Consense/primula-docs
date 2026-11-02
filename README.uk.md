# Primula Documenting System

[English](README.md)

Primula — мова текстової розмітки для ділових і технічних документів (договорів, актів, рахунків, листів, настанов) і транслятор, який будує з неї редагований **ODT** для LibreOffice Writer, а через LibreOffice — **PDF**. **Primula Studio** — настільне робоче місце для написання, перевірки й збирання документів Primula.

```prml
---
doc: {title: "Договір поставки", language: uk-UA}
params: {сума: 30444.96}
---
|<(number=False) Договір поставки
|< Ціна
|>(id="pay") Покупець оплачує |(money_full(сума, "UAH")) протягом 10 банківських днів.
|> Строк оплати — див. п. |@("pay").
```

**Стан: 0.3.0, попередній випуск (другий публічний; див. [CHANGELOG.md](CHANGELOG.md)).** Мова (специфікація 1.1, чернетка), транслятор і Studio придатні для реальних документів, але ще змінюються; файли, написані сьогодні, згодом можуть потребувати невеликих правок.

## Що вміє

- **Структура ділових документів:** нумеровані розділи, пункти й підпункти, списки, додатки, зміст, перехресні посилання (`|@("id")` → «п. 2.1», «табл. 1.1»), виноски; типово — нумерація за українськими стандартами (ДСТУ 3008, ДСТУ 4163).
- **Обчислювані значення:** невелика безпечна підмножина Python із десятковою арифметикою — суми, ПДВ, суми прописом, дати й робочі дні, форми слів за числом; дані з файлів CSV, YAML, JSON, ODS і XLSX; умови й варіанти одного документа.
- **Стилі окремо від тексту:** модулі стилів (`.s.prml`) замість оформлення в тексті; вбудовані набори для ділових документів, листів, технічних настанов і звітів.
- **Проєкти:** спільні фрагменти й модулі, параметри, файл проєкту з цілями збирання (договір і замовлення до нього), зведені документи, паралельні двомовні тексти.
- **Підсвічування для редакторів:** Kate/KWrite/KDevelop, Midnight Commander (mcedit), Geany і VS Code (`editors/`, будується зі довідника транслятора).
- **Бібліотеки модулів:** дванадцять багаторазових бібліотек `.m.prml` поза транслятором (`libraries/`): реквізити (ЄДРПОУ, РНОКПП, IBAN UA), імена у відмінках, ставки й дані законів з датою чинності, пеня й строки, фінансові графіки, QR-коди платежів (НБУ, SEPA), штрихкоди, діаграми, статистика, електроніка, таблиці змін із Git.
- **Експорт:** Markdown, HTML, DOCX та інші формати через [pandoc](https://pandoc.org) (`primula export`).
- **Primula Studio** (Qt 6): підсвічування, підказки, доповнення й контекстна довідка, панелі «Структура», «Стилі», «Палітра», перевірка й збирання, перегляд PDF, консоль обчислювача, допомога AI через Codex CLI або Claude CLI.
- **Повідомлення** у формі компіляторів (`файл:рядок:стовпець: error[P2201]: …`) англійською, українською й російською.

## Початок роботи

### Із пакета випуску (Linux)

Пакети випуску збираються кожен для одного дистрибутива (наприклад, openSUSE Tumbleweed, Debian 12 або 13); візьміть пакет для своєї системи в [Releases](https://github.com/OlegH-Consense/primula-docs/releases).

```sh
tar xf primula-docs-0.3.0-<дистрибутив>-x86_64.tar.gz
cd primula-docs-0.3.0-<дистрибутив>-x86_64
./check-dependencies.sh --install     # Python 3.11+, PyYAML, Qt 6, LibreOffice
./install.sh                          # у ~/.local; приклади — у ~/Primula/examples
primula-studio                        # або з меню: Primula Studio
```

### Із вихідних текстів

Транслятору потрібні Python 3.11+ і PyYAML; LibreOffice — лише для PDF.

```sh
./primula build examples/02-contract/contract.prml --pdf
./primula check examples/02-contract/contract.prml --lang uk
./primula --help
```

Primula Studio потребує Qt 6.4+ (Core, Gui, Widgets, Pdf, PdfWidgets, LinguistTools), CMake 3.20+, Ninja і компілятора C++20:

```sh
studio/build-studio.sh                # збирання в studio/build
studio/install-local.sh               # або встановлення в ~/.local
studio/make-distribution.sh --archive # пакет випуску для цього дистрибутива
```

## Документація

| | |
| --- | --- |
| [Посібник автора](docs/author/uk/index.md) ([en](docs/author/en/index.md), [ru](docs/author/ru/index.md)); одним PDF: [uk](docs/author/uk/primula-author-guide-uk.pdf), [en](docs/author/en/primula-author-guide-en.pdf), [ru](docs/author/ru/primula-author-guide-ru.pdf) | мова з прикладами: від першого документа до проєктів, стилів, бібліотек і діалекту Python ядра |
| [Приклади](examples/README.md) | дванадцять документів і проєктів: договір, настанова, позика з графіком, набори стилів, паралельні тексти, бібліотеки, рахунок із QR-кодом платежу |
| [Специфікація](primula-spec-v1.1-draft.uk.md) ([en](primula-spec-v1.1-draft.en.md), [ru](primula-spec-v1.1-draft.ru.md)), [стандартна бібліотека](primula-stdlib-v1.1-draft.uk.md) ([en](primula-stdlib-v1.1-draft.en.md), [ru](primula-stdlib-v1.1-draft.ru.md)) | нормативні тексти; нормативними є російські оригінали, переклади оновлюються за ними розділ за розділом |
| [Primula Studio](studio/README.md), [довідка](studio/help/studio-user-guide.uk.md), [шпаргалка](studio/help/primula-cheatsheet.uk.pdf) | настільна програма |
| [Skills для AI-агентів](skills/README.md) | інструкції для Claude Code, Codex та інших агентів: написання документів і бібліотек |
| [Нотатки розробника](docs/dev/architecture.md) | будова транслятора, [діагностика](docs/dev/diagnostics.md), [експорт через pandoc](docs/dev/pandoc.md) |

## Плани

Розробка йде ітераціями; наступні напрями:

- нові бібліотеки модулів і перевірка їхніх правових та інформаційних джерел (бібліотеки версії 0.1.0); схеми файлів даних;
- перетворення в Primula з інших форматів (DOCX, ODT, Markdown) і експорт зі Studio;
- сервер мови та форматувальник для редакторів (підсвічування вже є: `editors/`);
- допомога AI у Studio на основі перевірок транслятора;
- Primula Studio й транслятор для Windows.

Плани змінюються з досвідом реальних документів; питання й пропозиції — у Issues.

## Ліцензії

Код (транслятор, Studio, бібліотеки) — за [Apache License 2.0](LICENSE), документація — [CC BY 4.0](LICENSES/CC-BY-4.0.txt), приклади й шаблони — [CC0 1.0](LICENSES/CC0-1.0.txt): їх можна вільно копіювати у свої документи. Подробиці — у [LICENSING.md](LICENSING.md). Як долучитися — [CONTRIBUTING.md](CONTRIBUTING.md).
