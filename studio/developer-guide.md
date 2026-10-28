# Primula Studio — руководство разработчика

Настольный редактор документов Primula: Qt 6 (≥ 6.4), C++20, CMake. Пользовательская справка — `help/`, состояние этапов — `README.md`, история — `studio-release-history.md`. Исходник справки — `help/studio-user-guide.ru.md`; украинская и английская — переводы с меткой разделов исходника (этап 15.5): после правки русского текста `python3 tools/author_docs.py translations` (из корня дерева) называет устаревшие разделы, их переводят по `docs/author/translation-prompt.md` и отмечают `translations --stamp studio/help/studio-user-guide.uk.md …`.

## Граница с транслятором

Studio не знает семантики языка и не импортирует модули транслятора: она запускает `primula` как процесс и читает его JSON (спецификация 14.1, решения 124–125).

| Вызов | Где | Зачем |
| --- | --- | --- |
| `primula --version` | `Translator::version` | «О программе», настройки |
| `primula check project.p.prml --dump-project` | `Translator::dumpProject` → `StudioProject::open` | корень (`root`, для `extends` — корень базового), имя, язык, стили, цели, `documents`, сообщения заголовка |
| `primula check|build … --format json` | `BuildController` | проверка и сборка; stdout — массив сообщений (14.2), stderr — журнал |
| `primula check документ --dump-structure --dump-styles --overlay ФАЙЛ=БУФЕР…` | `DocumentInspector` ← `MainWindow::inspectDocument` | панели «Структура» и «Стили», переход F4 к странице PDF; изменённые буферы `.prml` пишутся во временный каталог и передаются как `--overlay`; один запуск за раз, новый запрос во время запуска заменяет отложенный |

Путь к транслятору — `Translator::program()`: настройка `tools/primula`, иначе `primula` из `PATH`, иначе запускатель `../../primula` рядом со сборкой в дереве исходников. Процесс запускается в корне проекта; пути в сообщениях отсчитываются от него.

## Карта исходников (`src/`)

| Файл | Назначение |
| --- | --- |
| `main.cpp` | приложение, переводы (Studio и `qtbase`), фильтр предупреждений `qt.text.font.db`, `--version`, `--runtime-info`, `--check-runtime` |
| `MainWindow.*` | рабочее место: вкладки файлов, раскладки (рядом / PDF вкладкой), панели «Файлы» и «Сообщения», сессия, проверка и сборка, F4, AI, «Создать», операции с файлами; подменю «Параллельные потоки» (`fillParallelMenu`, `runParallelTool`: `BuildController::Kind::Tool`, перечитывание переписанных файлов) |
| `StudioProject.*` | проект как его видит Studio: поиск `project.p.prml` (вверх до `.git`), описание из `--dump-project`, выходные файлы документа, служебный каталог `.primula-studio/` (`settings.json`, `ai-context.md`, `ai-history/`) |
| `Translator.*` | путь к транслятору и короткие синхронные вызовы |
| `BuildController.*` | асинхронные `check`/`build` с `--format json` |
| `DocumentInspector.*` | асинхронные выгрузки структуры и стилей с `--overlay` |
| `StructurePanel.*`, `StylesPanel.*` | панели «Структура» и «Стили» по выгрузкам; меню стиля — применить или снять у курсора (сигналы окну); у свойств стиля столбцы делят ширину панели (`fitColumns` по событию Resize, 40/35/25 %), подсказка строки — все три значения (`setRowTip`); происхождение слоя — на языке интерфейса (`originTitle`: project, option, header, default, extends, document) |
| `EditorAssist.*` | подсказки, сигнатуры, дополнение (`QCompleter`), Tab по заполнителям, раздел для F1 — по справочнику, выгрузке стилей и структуры (`contextAt` — раздел и отрезок текста конструкции с её аргументами; `MainWindow::showContextSection` отмечает его `CodeEditor::setContextMark` и снимает отметку по `destroyed` окна, не обращаясь к самому разрушаемому окну) (поставщики-функции от окна); контекстное меню редактора (подсказка, раздел, «Дополнить здесь»; в заголовке — `addHeaderActions`: вставка ключа, значение, недостающие поля через сигнал `addHeaderFieldsRequested`, все ключи); подключается к редакторам `.prml`; функции в коде дополняются при наборе с трёх букв; имя без вызова, которое файл определяет (`definesName`: `имя =`, `|let(имя=…)`, `for`, `def`, параметр заголовка), подсказки функции не получает (14.12) |
| `CommandCatalog.*` | справочник конструкций из `primula commands --format json --lang …` (Т5): разделы, команды и короткие формы со snippet, описанием, аргументами; с 14.13 — функции выражений (`Entry::function`, категории `fn:…`, раздел `stdlib:N` для документа библиотеки, заготовка вызова из аргументов без умолчания); один раз за сеанс |
| `Snippet.*` | раскрытие snippet (`$0`, `$1`, `${1:…}`, `${1\|a,b\|}`) и вставка: обёртка выделения, окружение вокруг строк, выделение первого аргумента, одна правка — один шаг отмены |
| `PalettePanel.*` | панель «Палитра»: конструкции и функции (разделы «Функции: …») с поиском и контекстным меню, вставка и раздел спецификации или библиотеки — сигналами окну |
| `StyleEditing.*` | назначение и снятие стиля в тексте `.prml` (14.7): `\|.X{…}`, `\|.X:`/`\|end.X`, `style=` у `\|>`/`\|<`, `\|block("X"):`; текстовый сканер скобок и окружений, одна правка — один шаг отмены; тесты `styleEditing*` |
| `FilesPanel.*` | дерево файлов проекта (`QFileSystemModel`), контекстное меню — через сигнал окну |
| `Templates.*`, `NewFileDialog.*` | шаблоны «Создать» (ресурсы `templates/` и `~/.config/primula-docs/templates/`), диалог |
| `EditorPane.*`, `CodeEditor.*` | буфер файла с контролем изменений на диске, поиск и замена, номера строк, подчёркивание строк сообщений |
| `PrimulaHighlighter.*` | подсветка Primula; Markdown и YAML — в `CodeEditor.cpp`; `isCode(block, column)` — диапазоны кода строки, записанные при подсветке (для функций в `EditorAssist`) |
| `PdfPreview.*` | просмотр PDF: сохранение позиции, масштаб вокруг курсора, переход к странице |
| `FileMonitor.*` | наблюдение за открытыми файлами (изменения вне Studio) |
| `AiController.*`, `AiHistory.*`, `AiHistoryPane.*`, `AiWorkspace.*` | запросы к Codex CLI (`codex exec --sandbox read-only`) или Claude CLI (`claude -p --tools Read,Grep,Glob --permission-mode dontAsk`), общий текст запроса (`AiController::makePrompt`), архив запросов и ответов (метки `primula-…`, старые `odtkit-…` читаются) |
| `ConsolePanel.*` | консоль вычислителя (14.15; с 14.16 — окно `Qt::Window` над главным, геометрия, разделитель и шрифт в QSettings `console/…`): процесс `primula console --json` (строка готовности, затем `{"input"}` → результат с `names`), журнал, строка ввода `CodeEditor` с `EditorAssist`, история, прерывание SIGINT, вкладки «Функции» (справочник, контекстное меню) и «Имена» (`names` протокола, решение 129), масштаб; аргументы контекста даёт `MainWindow::consoleTarget`, флажок «Вид → Консоль» — `m_consoleAction` по сигналу `visibilityChanged` |
| `HeaderAssist.*` | YAML-заголовок для помощника (14.14): границы заголовка, путь ключа под курсором (блочные отображения, `- ` списков, `{…}`/`[…]` на строке), соседние ключи, вид файла, вставка недостающих полей `doc:`/`doc_defaults:` (`metadataKey`, решение 129); для контекстного меню (14.16) — блок места вставки (`enclosing`), правка вставки ключа (`insertKey`) и значения (`valueEdit`) |
| `AiContext.*` | контекст Primula для AI (14.10): справочник из `CommandCatalog`, разделы спецификации и библиотеки из встроенных копий (`:/help/…`), вся спецификация, сообщения транслятора строками |
| `HelpDialog.*` | справка из ресурсов `help/`; HTML-комментарии (служебная метка перевода) перед показом удаляются; `setContext` — контекст справки по F1: заголовок «… — контекст: …» и строка `helpContext` над текстом (Э4) |

## Сборка

Зависимости: Qt 6.4+ (Core, Gui, Widgets, Pdf, PdfWidgets, LinguistTools; для тестов — Test), CMake 3.20+, Ninja, компилятор C++20. Транслятор — Python 3.11+ и PyYAML (см. `../README.md`).

```
./build-studio.sh                    # build/primula-studio (каталог — PRIMULA_STUDIO_BUILD_DIR)
./build-and-run-studio.sh            # собрать и запустить
./install-local.sh                   # установить в ~/.local (PRIMULA_STUDIO_INSTALL_PREFIX)
./register-desktop.sh --build        # .desktop для запуска из дерева сборки
```

Версия берётся из `../pyproject.toml` при конфигурации CMake.

Debian 12/13: `./build-debian.sh [--install-deps] [--run]` — проверка инструментов, Python 3.11+ с `python3-yaml`, конфигурация с минимальной Qt 6.4 в `build-debian/`, сборка; `--install-deps` ставит пакеты сборки через `apt-get` (sudo), `--run` регистрирует `.desktop` и запускает Studio. Транслятор при этом работает из дерева исходников (`../primula`).

## Пакет для пользователя (14.11)

```
./make-distribution.sh [--archive] [--skip-build] [--output КАТАЛОГ]
```

собирает Studio (Release) и пакет `../dist/primula-docs-ВЕРСИЯ-ДИСТРИБУТИВВЕРСИЯ-АРХИТЕКТУРА/` (с `--archive` — ещё `.tar.gz`; существующие не перезаписываются). Пакет собирается на целевом дистрибутиве: Studio связана с системной Qt, системные библиотеки не включаются. Состав (`packaging/make_distribution.py`):

| Путь в пакете | Что |
| --- | --- |
| `bin/primula`, `bin/primula-studio` | лаунчеры (`packaging/primula`, `packaging/primula-studio`): транслятор — `python -m primula` с `lib/python` в `PYTHONPATH`; Studio — с `PRIMULA_STUDIO_DATA_DIR` и `PREFIX/bin` в начале `PATH` (транслятор находится и при запуске из меню) |
| `libexec/primula-studio` | двоичный файл Studio |
| `lib/python/primula/` | пакет транслятора (исходники и данные, без кэшей) |
| `share/primula-studio/{translations,help}`, `share/icons/…`, `share/applications/…` | переводы, справка, значок, ярлык |
| `share/primula-studio/file-types.json`, `file-types.example.json` | встроенные типы файлов (они же в ресурсах Studio) и шаблон личного файла типов (С2) |
| `README*.md`, `STUDIO-GUIDE.*.md`, спецификация и stdlib, `primula-cheatsheet.{ru,uk,en}.pdf`, `examples/` | руководства и примеры (без `examples/out` и `run.sh`; библиотеки по ссылкам `lib` примеров 11 и 12 копируются внутрь; `examples/examples.json` — головные документы примеров по порядку, `EXAMPLE_ENTRIES`) |
| `libraries/` | библиотеки модулей (`payment_qr`) со своими тестами |
| `install.sh`, `uninstall.sh`, `check-dependencies.sh`, `runtime/` | установка (`--prefix`, `--offline`, `--wheelhouse`, `--translator-only`, `--examples-dir`, `--no-examples`, `--uninstall`, `--purge`, `--yes`; примеры дописываются в `projects/recent` настроек Studio — `ini_list`/`ini_string` читают и пишут список строк Qt INI), проверка и установка системных зависимостей (`--print-plan`, `--install`) |
| `distribution.json`, `MANIFEST.sha256` | платформа сборки, контрольные суммы (установщик их проверяет) |

Установка в `PREFIX` (по умолчанию `~/.local`): пакет — в `share/primula-docs`, окружение Python — `share/primula-python` (`venv --system-site-packages`: хватает системного PyYAML, иначе pip ставит `PyYAML>=6,<7`), лаунчеры — копиями в `bin/`, `libexec/primula-studio` — ссылка в пакет, ярлык — в `PREFIX/share/applications` и `XDG_DATA_HOME/applications`. Вне `PREFIX` (С1): рабочая копия примеров — `~/Primula/examples` (`--examples-dir`, `--no-examples`; изменённая копия при обновлении переименовывается в `examples.old-<время>`, удаление её не трогает) и, если настроек Studio ещё нет, `XDG_CONFIG_HOME/primula-docs/Primula Studio.conf` с примерами в `projects/recent` и первым примером в `projects/last` (значения в кавычках формата INI Qt; существующие настройки не меняются). Меню «Недавние проекты» хранит до 20 путей. Проверка пакета:

```
python3 tests/test_distribution.py --build-dir build
```

(сборка пакета, состав, ссылки README, контрольные суммы, установка в каталог с пробелами и `%`/`$`, рабочая копия примеров и сборка примеров 01, 11, 12 в ней установленным транслятором, настройки Studio с примерами, запуск Studio, обновление с сохранением изменённой копии примеров и настроек, удаление; планы пакетов Debian 12/13 и openSUSE).

**Нештатный вариант — транслятор Nuitka.** `packaging/build-nuitka-translator.sh [--python ПУТЬ] [--archive]` — по желанию разработчика: автономный каталог `dist/primula-ВЕРСИЯ-nuitka-…` (`bin/primula` + `lib/primula-nuitka/`), работающий без Python. Нужны Nuitka и PyYAML в выбранном Python (или `PYTHONPATH`), компилятор C, `patchelf`, заголовки Python. Замер 15.10.2026 (Nuitka 4.3, CPython 3.13, договор на 30 страниц): медленнее CPython на 15–20 % (с явно включёнными ускорителями `_json`/`_bisect`, которые плагин anti-bloat иначе исключает), ~39 МБ, сборка ~11 мин; привязан к glibc системы сборки. Исполняемый файл не называется `primula` — иначе каталог данных пакета `primula/` с ним совпадает и Nuitka молча не кладёт данные; скрипт проверяет данные и делает пробный запуск. В штатный пакет не входит.

## Тесты

```
cmake -S . -B build -G Ninja -DPRIMULA_STUDIO_BUILD_TESTS=ON
cmake --build build
QT_QPA_PLATFORM=offscreen build/studio-tests
python3 test_studio.py
```

Сборка устроена так, чтобы повторная была быстрой:

- исходники компилируются один раз — в объектную библиотеку `primula-studio-core`, которую подключают и `primula-studio`, и `studio-tests`;
- версия (из `../pyproject.toml`) — не флаг компиляции, а сгенерированный файл `<сборка>/generated/StudioVersion.cpp` (`src/StudioVersion.cpp.in`, функция `studioVersion()`); после повышения версии перекомпилируется только он;
- у каждого, кто собирает, — свой каталог сборки (`PRIMULA_STUDIO_BUILD_DIR`): один каталог, в который собирают по разным путям (например, через символическую ссылку `/home/…` → `/works/…`) или одновременно, CMake перенастраивает, а ninja пересобирает целиком. AI-агент собирает в `build-agent/`, `build/` — каталог пользователя.

- `tests/StudioTests.cpp` запускает транслятор этого репозитория (`PRIMULA_STUDIO_TEST_TRANSLATOR`, по умолчанию `../primula`) на временных проектах; тест сборки с PDF пропускается без `soffice`. Корзина и шаблоны пользователя в тестах — во временном каталоге (`XDG_DATA_HOME`, `XDG_CONFIG_HOME`).
- `test_studio.py` — без Qt: все исходники перечислены в CMake, все строки `tr()`/`translate()` переведены в `translations/*.ts`, ресурсы и сценарии на месте.
- Изолированные среды, где `linkat` из `/proc/self/fd` даёт `EXDEV`, ломают `QFile::copy`/`QSaveFile` Qt 6.11 — это свойство среды.

## Переводы

Интерфейс — английский, переводы uk/ru в `translations/primula_studio_*.ts`. После изменения строк:

```
/usr/lib64/qt6/bin/lupdate -no-obsolete src -ts translations/primula_studio_uk.ts translations/primula_studio_ru.ts
```

затем перевести новые строки (в том числе формы множественного числа `numerusform`); `.qm` собираются CMake.

## Соглашения

- Стандарт кода — как в исходной Studio: отступ 4 пробела, комментарии на английском, контракты функций — в заголовках.
- Studio не повторяет правил языка: всё, что нужно знать о документе, получается от транслятора; недостающие выгрузки добавляются в транслятор (и в спецификацию 14.1).

## Типы файлов (итерация И1, С2)

`src/FileTypes.{h,cpp}`: слои `:/config/file-types.json` (встроенные, `resources/file-types.json`) → личный `QStandardPaths::GenericConfigLocation/primula-docs/file-types.json` → проектный `.primula-studio/file-types.json`; тип — `name`, `patterns`, `open` (`editor`, `preview`, `system`, `command`), `command` (список, `%f`/`%d`/`%r`), `enabled`; более поздний слой снимает шаблон с ранних типов (замена по шаблону). Проектный слой команд не запускает: `command` сбрасывается, `open: command` → `system`, строка в «Журнал». `MainWindow::reloadFileTypes` — при открытии и закрытии проекта и после сохранения личного или проектного файла (фильтр панели «Файлы» — `FilesPanel::setNameFilters`); `openFile` сначала смотрит тип (`command` — `runFileCommand`: `QProcess::startDetached` в каталоге файла, неудача — окно с командой и путём файла типов; `system` — `QDesktopServices`), затем прежние правила; `openFileAsText` — редактор без правил типов. **Файл → Типы файлов…** создаёт личный файл из `:/config/file-types.user.json` (отключённый пример PlantUML) и открывает его. Qt-тесты: `fileTypesLayersAndCommands`, `fileTypeCommandOpensAFile`.
