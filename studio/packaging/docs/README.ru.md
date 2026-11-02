# Primula Docs — транслятор и Primula Studio

Primula — язык разметки деловых и технических документов: текст с командами `|…`
(заголовки, нумерованные пункты, таблицы, ссылки, данные, условия), оформление —
в отдельных модулях стилей. **Транслятор** `primula` собирает из `.prml`
редактируемый **ODT** для LibreOffice Writer и, при наличии LibreOffice, **PDF**.
**Primula Studio** — рабочая среда: редактор с подсветкой, подсказками и
дополнением, проверка и сборка, просмотр PDF, панели структуры, стилей и палитры.

Пакет собран под конкретный дистрибутив (см. `distribution.json`): Studio
использует системные библиотеки Qt 6. Компилятор и пакеты разработки не нужны.

## Что читать

| Файл | Содержание |
| --- | --- |
| [guide/ru/index.md](guide/ru/index.md) | руководство автора: первый документ, договор, акт и таблицы, письмо, техдокументация, проект, стили, сообщения транслятора |
| [guide/ru/primula-author-guide-ru.pdf](guide/ru/primula-author-guide-ru.pdf) | то же руководство одним PDF с приложениями и глоссарием (в Studio — «Справка → Руководство автора (PDF)»); есть и на украинском и английском |
| [STUDIO-GUIDE.ru.md](STUDIO-GUIDE.ru.md) | справка Primula Studio (то же — F1 в программе) |
| [primula-cheatsheet.ru.pdf](primula-cheatsheet.ru.pdf) | шпаргалка команд языка ([uk](primula-cheatsheet.uk.pdf), [en](primula-cheatsheet.en.pdf)) |
| [primula-spec-v1.1-draft.ru.md](primula-spec-v1.1-draft.ru.md) | спецификация языка (черновик 1.1; переводы — [uk](primula-spec-v1.1-draft.uk.md), [en](primula-spec-v1.1-draft.en.md)) |
| [primula-stdlib-v1.1-draft.ru.md](primula-stdlib-v1.1-draft.ru.md) | стандартная библиотека: стили, модули ([uk](primula-stdlib-v1.1-draft.uk.md), [en](primula-stdlib-v1.1-draft.en.md)) |
| [examples/README.md](examples/README.md) | примеры: от простого документа до проекта с договором и заказами |
| [editors/README.md](editors/README.md) | подсветка `.prml` для Kate, mcedit, Geany и VS Code (`editors/install.sh`) |

## Требования

- Python 3.11+ с PyYAML 6 (`python3-yaml` в Debian, `python3XY-PyYAML` в openSUSE);
- Qt 6.4+ (Core, Gui, Widgets, Pdf, PdfWidgets, модуль платформы, SVG-иконки);
- LibreOffice Writer — для PDF; шрифт Liberation Sans — для стандартных стилей;
- Codex CLI — только для запросов AI (необязательно).

## Установка

```sh
./check-dependencies.sh               # проверка; ничего не устанавливает
./check-dependencies.sh --print-plan  # какие системные пакеты нужны
./check-dependencies.sh --install     # установить их (sudo)
./install.sh                          # установка в ~/.local
```

`install.sh` проверяет контрольные суммы пакета, создаёт окружение Python
`~/.local/share/primula-python` (видит системный PyYAML; если его нет — ставит
PyYAML через pip, `--offline --wheelhouse КАТАЛОГ` — из локальных файлов),
копирует пакет в `~/.local/share/primula-docs`, команды `primula` и
`primula-studio` — в `~/.local/bin`, ярлык — в меню. Другой каталог:
`--prefix КАТАЛОГ`. Без графической среды: `--translator-only`.

Обновление — `./install.sh` из нового пакета (поверх прежней установки).

Удаление — `./uninstall.sh` из пакета или из установленной копии
(`~/.local/share/primula-docs/uninstall.sh`, каталог установки она находит сама;
то же — `./install.sh --uninstall`). Удаляется всё, что установка положила в
`~/.local` (верхняя часть таблицы ниже); `--keep-python` оставляет окружение Python.
Настройки Studio и примеры остаются. `./uninstall.sh --purge` удаляет и их — настройки,
свои типы файлов и шаблоны, кэш, копии примеров с их изменениями: сначала показывает
список и спрашивает подтверждение (`--yes` — без вопроса). Ваши проекты в других
каталогах не затрагиваются никогда.

## Работа

```sh
primula-studio                         # Studio (или из меню: Primula Studio)
primula build документ.prml --pdf      # ODT и PDF
primula check документ.prml            # только проверка
primula --help                         # все команды; primula commands — справочник конструкций
```

Примеры установка копирует в видимый рабочий каталог `~/Primula/examples` (другой — `--examples-dir КАТАЛОГ`, без копии — `--no-examples`); там их можно собирать и менять. Все примеры попадают в меню «Файл → Недавние проекты». Если настроек Primula Studio ещё нет, `install.sh` создаёт их, и при первом запуске открывается первый пример; в существующие настройки недостающие примеры дописываются в конец списка после ваших проектов, пока в нём есть место (Studio хранит 20), остальное в настройках не меняется. Устанавливайте при закрытой Studio. При обновлении изменённая копия примеров (в том числе результатами сборки) сохраняется как `~/Primula/examples.old-<время>`, а новые примеры копируются заново; `--uninstall` копию примеров не удаляет.

## Где что лежит

Каталоги по умолчанию (`--prefix`, `--examples-dir` и переменные `XDG_*_HOME` их меняют).

| Путь | Что там | `--uninstall` |
| --- | --- | --- |
| `~/.local/share/primula-docs/` | установленный пакет: транслятор, Studio, руководства, спецификация, примеры и библиотеки (исходные), `uninstall.sh` | удаляет |
| `~/.local/share/primula-python/` | окружение Python транслятора (PyYAML) | удаляет (кроме `--keep-python`) |
| `~/.local/bin/primula`, `~/.local/bin/primula-view`, `~/.local/bin/primula-studio` | команды | удаляет |
| `~/.local/libexec/primula-studio` | ссылка на программу Studio в пакете | удаляет |
| `~/.local/share/applications/org.primula_docs.Studio.desktop`, `~/.local/share/icons/hicolor/scalable/apps/primula-studio.svg` | ярлык в меню и значок | удаляет |
| `~/Primula/examples/`, `~/Primula/examples.old-<время>/` | рабочая копия примеров и прежние копии | `--purge` |
| `~/.config/primula-docs/Primula Studio.conf` | настройки Studio: недавние проекты, окна, путь к транслятору | `--purge` |
| `~/.config/primula-docs/file-types.json`, `~/.config/primula-docs/templates/` | свои типы файлов и шаблоны Studio | `--purge` |
| `~/.cache/primula-docs/` | кэш Studio (копия шпаргалки) | `--purge` |
| каталоги ваших проектов | документы, `.primula-studio/` проекта, результаты сборки | никогда |

## Ограничения

- Studio использует системные Qt 6, glibc и libstdc++, а они совместимы снизу вверх:
  пакет, собранный на более старой системе (например, Debian 12), рассчитан и на более
  новые, но не наоборот. `install.sh` предупреждает о другом дистрибутиве и проверяет
  библиотеки и запуск Studio; если проверка не прошла — соберите Studio на месте
  (`studio/build-debian.sh` или `studio/build-studio.sh` в исходниках).
- Язык (спецификация 1.1, черновик) и формат файлов ещё могут меняться.
