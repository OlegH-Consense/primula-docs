# Primula Docs — транслятор і Primula Studio

Primula — мова розмітки ділових і технічних документів: текст із командами `|…`
(заголовки, нумеровані пункти, таблиці, посилання, дані, умови), оформлення —
в окремих модулях стилів. **Транслятор** `primula` збирає з `.prml`
редагований **ODT** для LibreOffice Writer і, за наявності LibreOffice, **PDF**.
**Primula Studio** — робоче середовище: редактор із підсвічуванням, підказками й
доповненням, перевірка і збирання, перегляд PDF, панелі структури, стилів і палітри.

Пакет зібрано під конкретний дистрибутив (див. `distribution.json`): Studio
використовує системні бібліотеки Qt 6. Компілятор і пакети розробки не потрібні.

## Що читати

| Файл | Зміст |
| --- | --- |
| [guide/uk/index.md](guide/uk/index.md) | посібник автора: перший документ, договір, акт і таблиці, лист, технічна документація, проєкт, стилі, повідомлення транслятора |
| [guide/uk/primula-author-guide-uk.pdf](guide/uk/primula-author-guide-uk.pdf) | той самий посібник одним PDF з додатками й глосарієм (у Studio — «Довідка → Посібник автора (PDF)»); є також російською й англійською |
| [STUDIO-GUIDE.uk.md](STUDIO-GUIDE.uk.md) | довідка Primula Studio (те саме — F1 у програмі) |
| [primula-cheatsheet.uk.pdf](primula-cheatsheet.uk.pdf) | шпаргалка команд мови ([en](primula-cheatsheet.en.pdf), [ru](primula-cheatsheet.ru.pdf)) |
| [primula-spec-v1.1-draft.uk.md](primula-spec-v1.1-draft.uk.md) | специфікація мови (чернетка 1.1; переклад, оригінал — [ru](primula-spec-v1.1-draft.ru.md); також [en](primula-spec-v1.1-draft.en.md)) |
| [primula-stdlib-v1.1-draft.uk.md](primula-stdlib-v1.1-draft.uk.md) | стандартна бібліотека: стилі, модулі ([en](primula-stdlib-v1.1-draft.en.md), [ru](primula-stdlib-v1.1-draft.ru.md)) |
| [examples/README.md](examples/README.md) | приклади: від простого документа до проєкту з договором і замовленнями |
| [editors/README.md](editors/README.md) | підсвічування `.prml` для Kate, mcedit, Geany і VS Code (`editors/install.sh`) |

## Вимоги

- Python 3.11+ із PyYAML 6 (`python3-yaml` у Debian, `python3XY-PyYAML` в openSUSE);
- Qt 6.4+ (Core, Gui, Widgets, Pdf, PdfWidgets, модуль платформи, SVG-іконки);
- LibreOffice Writer — для PDF; шрифт Liberation Sans — для стандартних стилів;
- Codex CLI — лише для запитів AI (необов'язково).

## Встановлення

```sh
./check-dependencies.sh               # перевірка; нічого не встановлює
./check-dependencies.sh --print-plan  # які системні пакети потрібні
./check-dependencies.sh --install     # встановити їх (sudo)
./install.sh                          # встановлення в ~/.local
```

`install.sh` перевіряє контрольні суми пакета, створює середовище Python
`~/.local/share/primula-python` (бачить системний PyYAML; якщо його немає —
встановлює PyYAML через pip, `--offline --wheelhouse КАТАЛОГ` — з локальних файлів),
копіює пакет у `~/.local/share/primula-docs`, команди `primula` і
`primula-studio` — у `~/.local/bin`, ярлик — у меню. Інший каталог:
`--prefix КАТАЛОГ`. Без графічного середовища: `--translator-only`.

Оновлення — `./install.sh` з нового пакета (поверх попереднього встановлення).

Видалення — `./uninstall.sh` з пакета або зі встановленої копії
(`~/.local/share/primula-docs/uninstall.sh`, каталог встановлення вона знаходить сама;
те саме — `./install.sh --uninstall`). Видаляється все, що встановлення поклало в
`~/.local` (верхня частина таблиці нижче); `--keep-python` залишає середовище Python.
Налаштування Studio і приклади залишаються. `./uninstall.sh --purge` видаляє і їх —
налаштування, власні типи файлів і шаблони, кеш, копії прикладів з їхніми змінами:
спочатку показує перелік і питає підтвердження (`--yes` — без питання). Ваші проєкти
в інших каталогах не зачіпаються ніколи.

## Робота

```sh
primula-studio                         # Studio (або з меню: Primula Studio)
primula build документ.prml --pdf      # ODT і PDF
primula check документ.prml            # лише перевірка
primula --help                         # усі команди; primula commands — довідник конструкцій
```

Приклади встановлення копіює до видимого робочого каталогу `~/Primula/examples` (інший — `--examples-dir КАТАЛОГ`, без копії — `--no-examples`); там їх можна збирати й змінювати. Усі приклади потрапляють до меню «Файл → Недавні проєкти». Якщо налаштувань Primula Studio ще немає, `install.sh` створює їх, і під час першого запуску відкривається перший приклад; у наявні налаштування відсутні приклади дописуються в кінець переліку після ваших проєктів, поки в ньому є місце (Studio зберігає 20), решта налаштувань не змінюється. Встановлюйте за закритої Studio. Під час оновлення змінена копія прикладів (зокрема результатами збирання) зберігається як `~/Primula/examples.old-<час>`, а нові приклади копіюються заново; `--uninstall` копію прикладів не видаляє.

## Де що лежить

Каталоги за замовчуванням (`--prefix`, `--examples-dir` і змінні `XDG_*_HOME` їх змінюють).

| Шлях | Що там | `--uninstall` |
| --- | --- | --- |
| `~/.local/share/primula-docs/` | встановлений пакет: транслятор, Studio, посібники, специфікація, приклади й бібліотеки (вихідні), `uninstall.sh` | видаляє |
| `~/.local/share/primula-python/` | середовище Python транслятора (PyYAML) | видаляє (крім `--keep-python`) |
| `~/.local/bin/primula`, `~/.local/bin/primula-view`, `~/.local/bin/primula-studio` | команди | видаляє |
| `~/.local/libexec/primula-studio` | посилання на програму Studio в пакеті | видаляє |
| `~/.local/share/applications/org.primula_docs.Studio.desktop`, `~/.local/share/icons/hicolor/scalable/apps/primula-studio.svg` | ярлик у меню й значок | видаляє |
| `~/Primula/examples/`, `~/Primula/examples.old-<час>/` | робоча копія прикладів і попередні копії | `--purge` |
| `~/.config/primula-docs/Primula Studio.conf` | налаштування Studio: недавні проєкти, вікна, шлях до транслятора | `--purge` |
| `~/.config/primula-docs/file-types.json`, `~/.config/primula-docs/templates/` | власні типи файлів і шаблони Studio | `--purge` |
| `~/.cache/primula-docs/` | кеш Studio (копія шпаргалки) | `--purge` |
| каталоги ваших проєктів | документи, `.primula-studio/` проєкту, результати збирання | ніколи |

## Обмеження

- Studio використовує системні Qt 6, glibc і libstdc++, а вони сумісні знизу вгору:
  пакет, зібраний на старішій системі (наприклад, Debian 12), розрахований і на новіші,
  але не навпаки. `install.sh` попереджає про інший дистрибутив і перевіряє бібліотеки
  та запуск Studio; якщо перевірка не пройшла — зберіть Studio на місці
  (`studio/build-debian.sh` або `studio/build-studio.sh` у сирцях).
- Мова (специфікація 1.1, чернетка) і формат файлів ще можуть змінюватися.
