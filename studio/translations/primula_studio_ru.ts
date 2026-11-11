<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE TS>
<TS version="2.1" language="ru_RU">
<context>
    <name>AiAgents</name>
    <message>
        <location filename="../src/AiAgents.cpp" line="226"/>
        <source>The output of the tool is not JSON.</source>
        <translation>Вывод программы не является JSON.</translation>
    </message>
</context>
<context>
    <name>AiEditsPanel</name>
    <message>
        <location filename="../src/AiEditsPanel.cpp" line="37"/>
        <source>Edits proposed by AI. Choose the ones to apply; they are applied to the editor as one step that Undo takes back.</source>
        <translation>Правки, предложенные AI. Отметьте те, что нужно применить; они применяются к редактору одним шагом, который отменяет Undo.</translation>
    </message>
    <message>
        <location filename="../src/AiEditsPanel.cpp" line="55"/>
        <source>Check the chosen edits</source>
        <translation>Проверить отмеченные правки</translation>
    </message>
    <message>
        <location filename="../src/AiEditsPanel.cpp" line="57"/>
        <source>Runs the translator check on the document with each chosen edit, and with all of them: an edit that brings new errors is marked.</source>
        <translation>Запускает проверку транслятором для документа с каждой отмеченной правкой отдельно и со всеми вместе: правка, вносящая новые ошибки, будет помечена.</translation>
    </message>
    <message>
        <location filename="../src/AiEditsPanel.cpp" line="59"/>
        <source>Apply the chosen edits</source>
        <translation>Применить отмеченные правки</translation>
    </message>
    <message>
        <location filename="../src/AiEditsPanel.cpp" line="92"/>
        <source>applied</source>
        <translation>применено</translation>
    </message>
    <message numerus="yes">
        <location filename="../src/AiEditsPanel.cpp" line="95"/>
        <source>brings %n new error(s)</source>
        <translation>
            <numerusform>вносит %n новую ошибку</numerusform>
            <numerusform>вносит %n новые ошибки</numerusform>
            <numerusform>вносит %n новых ошибок</numerusform>
        </translation>
    </message>
    <message>
        <location filename="../src/AiEditsPanel.cpp" line="96"/>
        <source>checked, no new errors</source>
        <translation>проверено, новых ошибок нет</translation>
    </message>
    <message>
        <location filename="../src/AiEditsPanel.cpp" line="97"/>
        <source>ready</source>
        <translation>готова</translation>
    </message>
    <message>
        <location filename="../src/AiEditsPanel.cpp" line="98"/>
        <source>not found in the document</source>
        <translation>в документе не найдено</translation>
    </message>
    <message>
        <location filename="../src/AiEditsPanel.cpp" line="99"/>
        <source>occurs several times</source>
        <translation>встречается несколько раз</translation>
    </message>
    <message>
        <location filename="../src/AiEditsPanel.cpp" line="100"/>
        <source>changes nothing</source>
        <translation>ничего не меняет</translation>
    </message>
    <message>
        <location filename="../src/AiEditsPanel.cpp" line="101"/>
        <source>overlaps another edit</source>
        <translation>пересекается с другой правкой</translation>
    </message>
    <message numerus="yes">
        <location filename="../src/AiEditsPanel.cpp" line="167"/>
        <source>%n edit(s): %1 ready, %2 applied; chosen %3.</source>
        <translation>
            <numerusform>%n правка: готово %1, применено %2; отмечено %3.</numerusform>
            <numerusform>%n правки: готово %1, применено %2; отмечено %3.</numerusform>
            <numerusform>%n правок: готово %1, применено %2; отмечено %3.</numerusform>
        </translation>
    </message>
    <message>
        <location filename="../src/AiEditsPanel.cpp" line="168"/>
        <source>The document is not available, so the edits cannot be applied.</source>
        <translation>Документ недоступен, поэтому правки нельзя применить.</translation>
    </message>
    <message>
        <location filename="../src/AiEditsPanel.cpp" line="169"/>
        <source>The check is not available (the translator or the file type).</source>
        <translation>Проверка недоступна (транслятор или тип файла).</translation>
    </message>
    <message>
        <location filename="../src/AiEditsPanel.cpp" line="228"/>
        <source>Nothing is checked: choose at least one ready edit.</source>
        <translation>Ничего не проверено: отметьте хотя бы одну готовую правку.</translation>
    </message>
    <message>
        <location filename="../src/AiEditsPanel.cpp" line="236"/>
        <location filename="../src/AiEditsPanel.cpp" line="296"/>
        <source>The check did not run: %1</source>
        <translation>Проверка не запустилась: %1</translation>
    </message>
    <message numerus="yes">
        <location filename="../src/AiEditsPanel.cpp" line="247"/>
        <source>Checked %n edit(s): %1 bring new errors. All chosen together: %2 new error(s).</source>
        <translation>
            <numerusform>Проверено правок: %n. Вносят новые ошибки: %1. Все отмеченные вместе: новых ошибок — %2.</numerusform>
            <numerusform>Проверено правок: %n. Вносят новые ошибки: %1. Все отмеченные вместе: новых ошибок — %2.</numerusform>
            <numerusform>Проверено правок: %n. Вносят новые ошибки: %1. Все отмеченные вместе: новых ошибок — %2.</numerusform>
        </translation>
    </message>
    <message>
        <location filename="../src/AiEditsPanel.cpp" line="259"/>
        <location filename="../src/AiEditsPanel.cpp" line="265"/>
        <source>Apply edits</source>
        <translation>Применение правок</translation>
    </message>
    <message>
        <location filename="../src/AiEditsPanel.cpp" line="259"/>
        <source>No edit is chosen: nothing is applied.</source>
        <translation>Ни одной правки не отмечено: ничего не применено.</translation>
    </message>
    <message numerus="yes">
        <location filename="../src/AiEditsPanel.cpp" line="266"/>
        <source>The chosen edits bring %n new error(s) to the document:

%1

Apply them anyway?</source>
        <translation>
            <numerusform>Отмеченные правки вносят в документ новых ошибок: %n:

%1

Применить всё равно?</numerusform>
            <numerusform>Отмеченные правки вносят в документ новых ошибок: %n:

%1

Применить всё равно?</numerusform>
            <numerusform>Отмеченные правки вносят в документ новых ошибок: %n:

%1

Применить всё равно?</numerusform>
        </translation>
    </message>
    <message>
        <location filename="../src/AiEditsPanel.cpp" line="276"/>
        <source>Apply this edit</source>
        <translation>Применить эту правку</translation>
    </message>
    <message>
        <location filename="../src/AiEditsPanel.cpp" line="278"/>
        <source>Check this edit</source>
        <translation>Проверить эту правку</translation>
    </message>
    <message>
        <location filename="../src/AiEditsPanel.cpp" line="281"/>
        <source>Copy the replacement</source>
        <translation>Копировать замену</translation>
    </message>
    <message>
        <location filename="../src/AiEditsPanel.cpp" line="283"/>
        <source>Copy the original text</source>
        <translation>Копировать исходный текст</translation>
    </message>
    <message>
        <location filename="../src/AiEditsPanel.cpp" line="286"/>
        <source>Choose all</source>
        <translation>Отметить все</translation>
    </message>
    <message>
        <location filename="../src/AiEditsPanel.cpp" line="287"/>
        <source>Clear the choice</source>
        <translation>Снять отметки</translation>
    </message>
</context>
<context>
    <name>AiHistoryPane</name>
    <message>
        <location filename="../src/AiHistoryPane.cpp" line="31"/>
        <source>Not saved — use Save copy</source>
        <translation>Не сохранено — нажмите «Сохранить копию»</translation>
    </message>
    <message>
        <location filename="../src/AiHistoryPane.cpp" line="36"/>
        <source>Copy task</source>
        <translation>Копировать задание</translation>
    </message>
    <message>
        <location filename="../src/AiHistoryPane.cpp" line="38"/>
        <source>Copy answer (Markdown)</source>
        <translation>Копировать ответ (Markdown)</translation>
    </message>
    <message>
        <location filename="../src/AiHistoryPane.cpp" line="40"/>
        <source>Save copy…</source>
        <translation>Сохранить копию…</translation>
    </message>
    <message>
        <location filename="../src/AiHistoryPane.cpp" line="55"/>
        <source>Task</source>
        <translation>Задание</translation>
    </message>
    <message>
        <location filename="../src/AiHistoryPane.cpp" line="56"/>
        <source>Response</source>
        <translation>Ответ</translation>
    </message>
    <message>
        <location filename="../src/AiHistoryPane.cpp" line="63"/>
        <source>Preview</source>
        <translation>Просмотр</translation>
    </message>
    <message>
        <location filename="../src/AiHistoryPane.cpp" line="67"/>
        <source>Edits (%1)</source>
        <translation>Правки (%1)</translation>
    </message>
    <message>
        <location filename="../src/AiHistoryPane.cpp" line="78"/>
        <source>Markdown</source>
        <translation>Markdown</translation>
    </message>
    <message>
        <location filename="../src/AiHistoryPane.cpp" line="79"/>
        <source>Complete request</source>
        <translation>Полный запрос</translation>
    </message>
    <message>
        <location filename="../src/AiHistoryPane.cpp" line="81"/>
        <source>Find in AI response…</source>
        <translation>Найти в ответе AI…</translation>
    </message>
    <message>
        <location filename="../src/AiHistoryPane.cpp" line="82"/>
        <source>Find next</source>
        <translation>Найти далее</translation>
    </message>
    <message>
        <location filename="../src/AiHistoryPane.cpp" line="99"/>
        <source>AI %1 · %2 [RO]</source>
        <translation>AI %1 · %2 [RO]</translation>
    </message>
    <message>
        <location filename="../src/AiHistoryPane.cpp" line="110"/>
        <source>Save AI exchange</source>
        <translation>Сохранить диалог AI</translation>
    </message>
    <message>
        <location filename="../src/AiHistoryPane.cpp" line="112"/>
        <source>Markdown files (*.md);;All files (*)</source>
        <translation>Файлы Markdown (*.md);;Все файлы (*)</translation>
    </message>
    <message>
        <location filename="../src/AiHistoryPane.cpp" line="115"/>
        <source>Cannot save AI exchange</source>
        <translation>Не удалось сохранить диалог AI</translation>
    </message>
</context>
<context>
    <name>AiWorkspace</name>
    <message>
        <location filename="../src/AiWorkspace.cpp" line="15"/>
        <source>Saved AI requests:</source>
        <translation>Сохранённые запросы AI:</translation>
    </message>
    <message>
        <location filename="../src/AiWorkspace.cpp" line="24"/>
        <source>Close AI tab; saved files stay on disk</source>
        <translation>Закрыть вкладку AI; сохранённые файлы останутся на диске</translation>
    </message>
    <message>
        <location filename="../src/AiWorkspace.cpp" line="25"/>
        <source>Close AI tab</source>
        <translation>Закрыть вкладку AI</translation>
    </message>
</context>
<context>
    <name>BackupsDialog</name>
    <message>
        <location filename="../src/BackupsDialog.cpp" line="23"/>
        <source>Backups of the project</source>
        <translation>Резервные копии проекта</translation>
    </message>
    <message>
        <location filename="../src/BackupsDialog.cpp" line="33"/>
        <source>Time</source>
        <translation>Время</translation>
    </message>
    <message>
        <location filename="../src/BackupsDialog.cpp" line="33"/>
        <source>Reason</source>
        <translation>Причина</translation>
    </message>
    <message>
        <location filename="../src/BackupsDialog.cpp" line="33"/>
        <source>Note</source>
        <translation>Примечание</translation>
    </message>
    <message>
        <location filename="../src/BackupsDialog.cpp" line="33"/>
        <source>Size</source>
        <translation>Размер</translation>
    </message>
    <message>
        <location filename="../src/BackupsDialog.cpp" line="41"/>
        <location filename="../src/BackupsDialog.cpp" line="160"/>
        <source>Back up the project now</source>
        <translation>Сделать копию проекта сейчас</translation>
    </message>
    <message>
        <location filename="../src/BackupsDialog.cpp" line="42"/>
        <location filename="../src/BackupsDialog.cpp" line="155"/>
        <source>Compare with the current file…</source>
        <translation>Сравнить с текущим файлом…</translation>
    </message>
    <message>
        <location filename="../src/BackupsDialog.cpp" line="43"/>
        <location filename="../src/BackupsDialog.cpp" line="156"/>
        <source>Restore this version</source>
        <translation>Восстановить эту версию</translation>
    </message>
    <message>
        <location filename="../src/BackupsDialog.cpp" line="44"/>
        <location filename="../src/BackupsDialog.cpp" line="157"/>
        <source>Delete the backup</source>
        <translation>Удалить копию</translation>
    </message>
    <message>
        <location filename="../src/BackupsDialog.cpp" line="45"/>
        <source>Open the folder</source>
        <translation>Открыть папку</translation>
    </message>
    <message>
        <location filename="../src/BackupsDialog.cpp" line="46"/>
        <source>Close</source>
        <translation>Закрыть</translation>
    </message>
    <message>
        <location filename="../src/BackupsDialog.cpp" line="73"/>
        <source>Before applying AI edits</source>
        <translation>Перед применением правок AI</translation>
    </message>
    <message>
        <location filename="../src/BackupsDialog.cpp" line="74"/>
        <source>Before saving</source>
        <translation>Перед сохранением</translation>
    </message>
    <message>
        <location filename="../src/BackupsDialog.cpp" line="75"/>
        <source>Before a restore</source>
        <translation>Перед восстановлением</translation>
    </message>
    <message>
        <location filename="../src/BackupsDialog.cpp" line="76"/>
        <source>Manual</source>
        <translation>Вручную</translation>
    </message>
    <message>
        <location filename="../src/BackupsDialog.cpp" line="101"/>
        <source>There are no backups yet. They are made before AI edits are applied and on request; «Back up the project now» copies the source files of the project.</source>
        <translation>Копий ещё нет. Их создают перед применением правок AI и по требованию; «Сделать копию проекта сейчас» копирует исходные файлы проекта.</translation>
    </message>
    <message numerus="yes">
        <location filename="../src/BackupsDialog.cpp" line="103"/>
        <source>%n backup(s), %1 in all. Restoring a version first makes a backup of the current file.</source>
        <translation>
            <numerusform>Копий: %n, всего %1. Восстановление версии сначала делает копию текущего файла.</numerusform>
            <numerusform>Копий: %n, всего %1. Восстановление версии сначала делает копию текущего файла.</numerusform>
            <numerusform>Копий: %n, всего %1. Восстановление версии сначала делает копию текущего файла.</numerusform>
        </translation>
    </message>
    <message>
        <location filename="../src/BackupsDialog.cpp" line="113"/>
        <source>Choose a backup in the list.</source>
        <translation>Выберите копию в списке.</translation>
    </message>
    <message numerus="yes">
        <location filename="../src/BackupsDialog.cpp" line="123"/>
        <source>This backup holds %n file(s): choose one of them.</source>
        <translation>
            <numerusform>В этой копии файлов: %n. Выберите один из них.</numerusform>
            <numerusform>В этой копии файлов: %n. Выберите один из них.</numerusform>
            <numerusform>В этой копии файлов: %n. Выберите один из них.</numerusform>
        </translation>
    </message>
    <message>
        <location filename="../src/BackupsDialog.cpp" line="142"/>
        <source>Delete the backup of %1?</source>
        <translation>Удалить копию от %1?</translation>
    </message>
</context>
<context>
    <name>BuildController</name>
    <message>
        <location filename="../src/BuildController.cpp" line="18"/>
        <source>Failed to start the translator: %1
</source>
        <translation>Не удалось запустить транслятор: %1
</translation>
    </message>
    <message>
        <location filename="../src/BuildController.cpp" line="28"/>
        <source>Finished successfully.
</source>
        <translation>Завершено успешно.
</translation>
    </message>
    <message>
        <location filename="../src/BuildController.cpp" line="29"/>
        <source>Finished with errors (exit code %1).
</source>
        <translation>Завершено с ошибками (код завершения %1).
</translation>
    </message>
    <message>
        <location filename="../src/BuildController.cpp" line="50"/>
        <source>The Primula translator is not found: install &apos;primula&apos; into PATH or set its path in Settings.
</source>
        <translation>Транслятор Primula не найден: установите &apos;primula&apos; в PATH или укажите путь в настройках.
</translation>
    </message>
    <message>
        <location filename="../src/BuildController.cpp" line="57"/>
        <source>Starting: %1 %2
</source>
        <translation>Запуск: %1 %2
</translation>
    </message>
</context>
<context>
    <name>CliAgentBackend</name>
    <message>
        <location filename="../src/AiController.cpp" line="20"/>
        <source>Cannot start %1: %2</source>
        <translation>Не удаётся запустить %1: %2</translation>
    </message>
    <message>
        <location filename="../src/AiController.cpp" line="32"/>
        <source>%1 finished without a usable response (exit code %2).</source>
        <translation>%1: работа завершена без пригодного ответа (код выхода %2).</translation>
    </message>
    <message>
        <location filename="../src/AiController.cpp" line="58"/>
        <source>AI request started.
</source>
        <translation>AI-запрос запущен.
</translation>
    </message>
</context>
<context>
    <name>CodeEditor</name>
    <message>
        <location filename="../src/CodeEditor.cpp" line="258"/>
        <source>Context of the open help window</source>
        <translation>Контекст открытого окна справки</translation>
    </message>
</context>
<context>
    <name>CommandCatalog</name>
    <message>
        <location filename="../src/CommandCatalog.cpp" line="40"/>
        <location filename="../src/CommandCatalog.cpp" line="95"/>
        <source>Specification, section %1</source>
        <translation>Спецификация, раздел %1</translation>
    </message>
    <message>
        <location filename="../src/CommandCatalog.cpp" line="52"/>
        <source>Only in styles code: a styles module, the project, the document</source>
        <translation>Только в коде стилей: модуль стилей, проект, документ</translation>
    </message>
    <message>
        <location filename="../src/CommandCatalog.cpp" line="53"/>
        <source>Only in a table cell formula |=(…)</source>
        <translation>Только в формуле ячейки таблицы |=(…)</translation>
    </message>
    <message>
        <location filename="../src/CommandCatalog.cpp" line="54"/>
        <source>Only in the code of a project file</source>
        <translation>Только в коде файла проекта</translation>
    </message>
    <message>
        <location filename="../src/CommandCatalog.cpp" line="58"/>
        <source>Example: %1</source>
        <translation>Пример: %1</translation>
    </message>
    <message>
        <location filename="../src/CommandCatalog.cpp" line="94"/>
        <source>Standard library, section %1</source>
        <translation>Стандартная библиотека, раздел %1</translation>
    </message>
    <message>
        <location filename="../src/CommandCatalog.cpp" line="124"/>
        <source>The translator is not found.</source>
        <translation>Транслятор не найден.</translation>
    </message>
    <message>
        <location filename="../src/CommandCatalog.cpp" line="135"/>
        <source>primula commands failed: %1</source>
        <translation>Ошибка primula commands: %1</translation>
    </message>
    <message>
        <location filename="../src/CommandCatalog.cpp" line="236"/>
        <source>The catalogue of constructs is empty.</source>
        <translation>Справочник конструкций пуст.</translation>
    </message>
</context>
<context>
    <name>ConsolePanel</name>
    <message>
        <location filename="../src/ConsolePanel.cpp" line="65"/>
        <source>Console — Primula Studio</source>
        <translation>Консоль — Primula Studio</translation>
    </message>
    <message>
        <location filename="../src/ConsolePanel.cpp" line="70"/>
        <source>Context:</source>
        <translation>Контекст:</translation>
    </message>
    <message>
        <location filename="../src/ConsolePanel.cpp" line="73"/>
        <source>Current file</source>
        <translation>Текущий файл</translation>
    </message>
    <message>
        <location filename="../src/ConsolePanel.cpp" line="74"/>
        <source>Project</source>
        <translation>Проект</translation>
    </message>
    <message>
        <location filename="../src/ConsolePanel.cpp" line="75"/>
        <source>Library only</source>
        <translation>Только библиотека</translation>
    </message>
    <message>
        <location filename="../src/ConsolePanel.cpp" line="76"/>
        <source>The names the console has: those of the current file (a document with its parameters and code, a module, a styles module, the project file), of the project, or of the standard library only</source>
        <translation>Имена, которые есть в консоли: текущего файла (документ с параметрами и кодом, модуль, модуль стилей, файл проекта), проекта или только стандартной библиотеки</translation>
    </message>
    <message>
        <location filename="../src/ConsolePanel.cpp" line="84"/>
        <source>Restart</source>
        <translation>Перезапустить</translation>
    </message>
    <message>
        <location filename="../src/ConsolePanel.cpp" line="85"/>
        <source>A new session in the selected context; the names of the console are lost</source>
        <translation>Новый сеанс в выбранном контексте; имена консоли теряются</translation>
    </message>
    <message>
        <location filename="../src/ConsolePanel.cpp" line="86"/>
        <source>Interrupt</source>
        <translation>Прервать</translation>
    </message>
    <message>
        <location filename="../src/ConsolePanel.cpp" line="87"/>
        <source>Stop the running input; the names of the console stay (Ctrl+C in the input)</source>
        <translation>Остановить текущий ввод; имена консоли остаются (Ctrl+C в строке ввода)</translation>
    </message>
    <message>
        <location filename="../src/ConsolePanel.cpp" line="124"/>
        <source>Double click puts the example into the input; the context menu has more</source>
        <translation>Двойной щелчок вставляет пример в строку ввода; больше — в контекстном меню</translation>
    </message>
    <message>
        <location filename="../src/ConsolePanel.cpp" line="135"/>
        <source>Functions</source>
        <translation>Функции</translation>
    </message>
    <message>
        <location filename="../src/ConsolePanel.cpp" line="142"/>
        <source>Search names…</source>
        <translation>Поиск имён…</translation>
    </message>
    <message>
        <location filename="../src/ConsolePanel.cpp" line="146"/>
        <source>Name</source>
        <translation>Имя</translation>
    </message>
    <message>
        <location filename="../src/ConsolePanel.cpp" line="146"/>
        <source>Type</source>
        <translation>Тип</translation>
    </message>
    <message>
        <location filename="../src/ConsolePanel.cpp" line="146"/>
        <source>Value</source>
        <translation>Значение</translation>
    </message>
    <message>
        <location filename="../src/ConsolePanel.cpp" line="149"/>
        <source>Names of the inputs (bold) and of the context; double click inserts the name, the context menu shows the value</source>
        <translation>Имена вводов (жирным) и контекста; двойной щелчок вставляет имя, контекстное меню показывает значение</translation>
    </message>
    <message>
        <location filename="../src/ConsolePanel.cpp" line="153"/>
        <source>Names</source>
        <translation>Имена</translation>
    </message>
    <message>
        <location filename="../src/ConsolePanel.cpp" line="276"/>
        <source>Put the example into the input</source>
        <translation>Вставить пример в строку ввода</translation>
    </message>
    <message>
        <location filename="../src/ConsolePanel.cpp" line="277"/>
        <location filename="../src/ConsolePanel.cpp" line="293"/>
        <source>Insert the name</source>
        <translation>Вставить имя</translation>
    </message>
    <message>
        <location filename="../src/ConsolePanel.cpp" line="278"/>
        <source>Run :help %1</source>
        <translation>Выполнить :help %1</translation>
    </message>
    <message>
        <location filename="../src/ConsolePanel.cpp" line="280"/>
        <source>Open the section %1</source>
        <translation>Открыть раздел %1</translation>
    </message>
    <message>
        <location filename="../src/ConsolePanel.cpp" line="283"/>
        <location filename="../src/ConsolePanel.cpp" line="296"/>
        <source>Copy the name</source>
        <translation>Копировать имя</translation>
    </message>
    <message>
        <location filename="../src/ConsolePanel.cpp" line="294"/>
        <source>Show the value</source>
        <translation>Показать значение</translation>
    </message>
    <message>
        <location filename="../src/ConsolePanel.cpp" line="298"/>
        <source>Copy the value</source>
        <translation>Копировать значение</translation>
    </message>
    <message>
        <location filename="../src/ConsolePanel.cpp" line="313"/>
        <source>(not evaluated yet)</source>
        <translation>(ещё не вычислено)</translation>
    </message>
    <message>
        <location filename="../src/ConsolePanel.cpp" line="326"/>
        <source>Names (%1)</source>
        <translation>Имена (%1)</translation>
    </message>
    <message>
        <location filename="../src/ConsolePanel.cpp" line="537"/>
        <source>%1 names in the context (the Names tab)</source>
        <translation>имён в контексте: %1 (вкладка «Имена»)</translation>
    </message>
    <message>
        <location filename="../src/ConsolePanel.cpp" line="88"/>
        <source>Clear</source>
        <translation>Очистить</translation>
    </message>
    <message>
        <location filename="../src/ConsolePanel.cpp" line="89"/>
        <source>Clear the transcript; the names of the console stay</source>
        <translation>Очистить журнал; имена консоли остаются</translation>
    </message>
    <message>
        <location filename="../src/ConsolePanel.cpp" line="106"/>
        <source>Primula code; Enter runs, Shift+Enter breaks the line, Ctrl+↑/↓ — history, :help NAME</source>
        <translation>Код Primula; Enter выполняет, Shift+Enter — новая строка, Ctrl+↑/↓ — история, :help ИМЯ</translation>
    </message>
    <message>
        <location filename="../src/ConsolePanel.cpp" line="119"/>
        <source>Search functions…</source>
        <translation>Поиск функций…</translation>
    </message>
    <message>
        <location filename="../src/ConsolePanel.cpp" line="421"/>
        <source>The session has ended (exit code %1). Restart starts a new one.</source>
        <translation>Сеанс завершён (код выхода %1). «Перезапустить» начинает новый.</translation>
    </message>
    <message>
        <location filename="../src/ConsolePanel.cpp" line="426"/>
        <source>Cannot start the translator: %1</source>
        <translation>Не удалось запустить транслятор: %1</translation>
    </message>
    <message>
        <location filename="../src/ConsolePanel.cpp" line="535"/>
        <source>The translator is not found.</source>
        <translation>Транслятор не найден.</translation>
    </message>
    <message>
        <location filename="../src/ConsolePanel.cpp" line="535"/>
        <source>not started</source>
        <translation>не запущена</translation>
    </message>
    <message>
        <location filename="../src/ConsolePanel.cpp" line="536"/>
        <source>starting…</source>
        <translation>запуск…</translation>
    </message>
    <message>
        <location filename="../src/ConsolePanel.cpp" line="538"/>
        <source>running…</source>
        <translation>выполняется…</translation>
    </message>
</context>
<context>
    <name>DocumentInspector</name>
    <message>
        <location filename="../src/DocumentInspector.cpp" line="16"/>
        <source>Cannot start the translator: %1</source>
        <translation>Не удалось запустить транслятор: %1</translation>
    </message>
    <message>
        <location filename="../src/DocumentInspector.cpp" line="33"/>
        <source>The translator stopped abnormally.</source>
        <translation>Транслятор аварийно завершился.</translation>
    </message>
    <message>
        <location filename="../src/DocumentInspector.cpp" line="34"/>
        <source>The translator output is not JSON.</source>
        <translation>Вывод транслятора — не JSON.</translation>
    </message>
    <message>
        <location filename="../src/DocumentInspector.cpp" line="79"/>
        <source>The translator is not found.</source>
        <translation>Транслятор не найден.</translation>
    </message>
</context>
<context>
    <name>EditorAssist</name>
    <message>
        <location filename="../src/EditorAssist.cpp" line="264"/>
        <source>Type: %1</source>
        <translation>Тип: %1</translation>
    </message>
    <message>
        <location filename="../src/EditorAssist.cpp" line="266"/>
        <source>Values: %1</source>
        <translation>Значения: %1</translation>
    </message>
    <message>
        <location filename="../src/EditorAssist.cpp" line="266"/>
        <source>For example: %1</source>
        <translation>Например: %1</translation>
    </message>
    <message>
        <location filename="../src/EditorAssist.cpp" line="267"/>
        <source>Example: %1</source>
        <translation>Пример: %1</translation>
    </message>
    <message>
        <location filename="../src/EditorAssist.cpp" line="268"/>
        <source>Recommended for a finished ODT.</source>
        <translation>Рекомендуется для готового ODT.</translation>
    </message>
    <message>
        <location filename="../src/EditorAssist.cpp" line="274"/>
        <source>Not filled: %1 (context menu or Insert → Header: add missing fields)</source>
        <translation>Не заполнено: %1 (контекстное меню или Вставка → Заголовок: добавить недостающие поля)</translation>
    </message>
    <message>
        <location filename="../src/EditorAssist.cpp" line="276"/>
        <source>A document overrides these values key by key in its own doc:.</source>
        <translation>Документ заменяет эти значения поштучно в собственном doc:.</translation>
    </message>
    <message>
        <location filename="../src/EditorAssist.cpp" line="290"/>
        <source>The document has no style %1.</source>
        <translation>В документе нет стиля %1.</translation>
    </message>
    <message>
        <location filename="../src/EditorAssist.cpp" line="296"/>
        <source>The document has no element with ID %1.</source>
        <translation>В документе нет элемента с ID %1.</translation>
    </message>
    <message>
        <location filename="../src/EditorAssist.cpp" line="306"/>
        <source>Closes line %1: %2</source>
        <translation>Закрывает строку %1: %2</translation>
    </message>
    <message>
        <location filename="../src/EditorAssist.cpp" line="566"/>
        <source>closes line %1: %2</source>
        <translation>закрывает строку %1: %2</translation>
    </message>
    <message>
        <location filename="../src/EditorAssist.cpp" line="804"/>
        <source>Insert key into %1:</source>
        <translation>Вставить ключ в %1:</translation>
    </message>
    <message>
        <location filename="../src/EditorAssist.cpp" line="805"/>
        <source>Insert key</source>
        <translation>Вставить ключ</translation>
    </message>
    <message>
        <location filename="../src/EditorAssist.cpp" line="805"/>
        <source>Insert top-level key</source>
        <translation>Вставить ключ верхнего уровня</translation>
    </message>
    <message>
        <location filename="../src/EditorAssist.cpp" line="811"/>
        <source>Value of %1</source>
        <translation>Значение %1</translation>
    </message>
    <message>
        <location filename="../src/EditorAssist.cpp" line="826"/>
        <source>Add missing metadata fields (none missing)</source>
        <translation>Добавить недостающие поля метаданных (все заполнены)</translation>
    </message>
    <message>
        <location filename="../src/EditorAssist.cpp" line="827"/>
        <source>Add missing metadata fields: %1</source>
        <translation>Добавить недостающие поля метаданных: %1</translation>
    </message>
    <message>
        <location filename="../src/EditorAssist.cpp" line="834"/>
        <source>All header keys (%1)</source>
        <translation>Все ключи заголовка (%1)</translation>
    </message>
    <message>
        <location filename="../src/EditorAssist.cpp" line="965"/>
        <source>Hint (no construct here)</source>
        <translation>Подсказка (здесь нет конструкции)</translation>
    </message>
    <message>
        <location filename="../src/EditorAssist.cpp" line="965"/>
        <source>Hint: %1</source>
        <translation>Подсказка: %1</translation>
    </message>
    <message>
        <location filename="../src/EditorAssist.cpp" line="973"/>
        <source>Specification section</source>
        <translation>Раздел спецификации</translation>
    </message>
    <message>
        <location filename="../src/EditorAssist.cpp" line="981"/>
        <source>Complete here</source>
        <translation>Дополнить здесь</translation>
    </message>
</context>
<context>
    <name>EditorPane</name>
    <message>
        <location filename="../src/EditorPane.cpp" line="104"/>
        <source>Cannot open %1: %2</source>
        <translation>Не удалось открыть %1: %2</translation>
    </message>
    <message>
        <location filename="../src/EditorPane.cpp" line="150"/>
        <location filename="../src/EditorPane.cpp" line="156"/>
        <source>Cannot save %1: %2</source>
        <translation>Не удалось сохранить %1: %2</translation>
    </message>
    <message>
        <location filename="../src/EditorPane.cpp" line="36"/>
        <location filename="../src/EditorPane.cpp" line="37"/>
        <source>Find text…</source>
        <translation>Найти текст…</translation>
    </message>
    <message>
        <location filename="../src/EditorPane.cpp" line="38"/>
        <source>Previous</source>
        <translation>Назад</translation>
    </message>
    <message>
        <location filename="../src/EditorPane.cpp" line="39"/>
        <source>Next</source>
        <translation>Далее</translation>
    </message>
    <message>
        <location filename="../src/EditorPane.cpp" line="40"/>
        <source>Close</source>
        <translation>Закрыть</translation>
    </message>
    <message>
        <location filename="../src/EditorPane.cpp" line="47"/>
        <source>Match case</source>
        <translation>Учитывать регистр</translation>
    </message>
    <message>
        <location filename="../src/EditorPane.cpp" line="49"/>
        <source>Whole words</source>
        <translation>Слова целиком</translation>
    </message>
    <message>
        <location filename="../src/EditorPane.cpp" line="65"/>
        <location filename="../src/EditorPane.cpp" line="66"/>
        <source>Replace with…</source>
        <translation>Заменить на…</translation>
    </message>
    <message>
        <location filename="../src/EditorPane.cpp" line="67"/>
        <source>Replace</source>
        <translation>Заменить</translation>
    </message>
    <message>
        <location filename="../src/EditorPane.cpp" line="68"/>
        <source>Replace all</source>
        <translation>Заменить всё</translation>
    </message>
    <message>
        <location filename="../src/EditorPane.cpp" line="144"/>
        <source>File changed outside Studio: %1. Reload or choose Keep editor before saving.</source>
        <translation>Файл изменён вне Studio: %1. Перечитайте его или выберите «Оставить текст» перед сохранением.</translation>
    </message>
    <message>
        <location filename="../src/EditorPane.cpp" line="246"/>
        <source>Text not found</source>
        <translation>Текст не найден</translation>
    </message>
    <message>
        <location filename="../src/EditorPane.cpp" line="249"/>
        <source>Search wrapped</source>
        <translation>Поиск продолжен с другой границы файла</translation>
    </message>
    <message>
        <location filename="../src/EditorPane.cpp" line="286"/>
        <source>Replaced: %1</source>
        <translation>Заменено: %1</translation>
    </message>
</context>
<context>
    <name>HelpDialog</name>
    <message>
        <location filename="../src/HelpDialog.cpp" line="24"/>
        <source>Quick help</source>
        <translation>Краткая справка</translation>
    </message>
    <message>
        <location filename="../src/HelpDialog.cpp" line="48"/>
        <source>%1 — context: %2</source>
        <translation>%1 — контекст: %2</translation>
    </message>
    <message>
        <location filename="../src/HelpDialog.cpp" line="90"/>
        <source>Find in help…</source>
        <translation>Поиск в справке…</translation>
    </message>
    <message>
        <location filename="../src/HelpDialog.cpp" line="91"/>
        <source>Find next</source>
        <translation>Найти далее</translation>
    </message>
</context>
<context>
    <name>MainWindow</name>
    <message>
        <location filename="../src/MainWindow.cpp" line="343"/>
        <source>Fit width</source>
        <translation>По ширине</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="341"/>
        <location filename="../src/MainWindow.cpp" line="907"/>
        <source>PDF preview</source>
        <translation>Просмотр PDF</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="518"/>
        <location filename="../src/MainWindow.cpp" line="520"/>
        <source>Messages</source>
        <translation>Панель сообщений</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2725"/>
        <source>AI result was not saved</source>
        <translation>Результат AI не сохранён</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2726"/>
        <source>The response remains in its tab. Use Save copy to choose another location.
%1</source>
        <translation>Ответ остаётся во вкладке. Нажмите «Сохранить копию», чтобы выбрать другое место.
%1</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2728"/>
        <source>AI request and response saved: %1</source>
        <translation>Запрос и ответ AI сохранены: %1</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="554"/>
        <source>&amp;File</source>
        <translation>&amp;Файл</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="506"/>
        <source>Message</source>
        <translation>Сообщение</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="506"/>
        <source>File</source>
        <translation>Файл</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="506"/>
        <source>Line</source>
        <translation>Строка</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="519"/>
        <source>Log</source>
        <translation>Журнал</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="574"/>
        <source>Recent projects</source>
        <translation>Недавние проекты</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="601"/>
        <source>E&amp;xit</source>
        <translation>Вы&amp;ход</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="636"/>
        <source>&amp;Build</source>
        <translation>С&amp;борка</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="637"/>
        <source>&amp;Check document</source>
        <translation>&amp;Проверить документ</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="687"/>
        <source>Open ODT in Writer</source>
        <translation>Открыть ODT в Writer</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="691"/>
        <source>Open project directory</source>
        <translation>Открыть каталог проекта</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="742"/>
        <source>&amp;AI</source>
        <translation>&amp;AI</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="743"/>
        <source>Ask AI about the document…</source>
        <translation>Задать AI вопрос о документе…</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="745"/>
        <source>Show AI history</source>
        <translation>Показать историю AI</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="695"/>
        <source>&amp;View</source>
        <translation>&amp;Вид</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="721"/>
        <source>Layout</source>
        <translation>Компоновка</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="730"/>
        <source>Increase editor font</source>
        <translation>Увеличить шрифт редактора</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="732"/>
        <source>Decrease editor font</source>
        <translation>Уменьшить шрифт редактора</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="734"/>
        <source>Reset editor font size</source>
        <translation>Вернуть размер шрифта редактора</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="736"/>
        <source>Interface language</source>
        <translation>Язык интерфейса</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="737"/>
        <source>System language</source>
        <translation>Язык системы</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="748"/>
        <source>&amp;Help</source>
        <translation>&amp;Справка</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="749"/>
        <source>Quick help</source>
        <translation>Краткая справка</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="755"/>
        <location filename="../src/MainWindow.cpp" line="757"/>
        <source>About Primula Studio</source>
        <translation>О программе Primula Studio</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="763"/>
        <source>Main toolbar</source>
        <translation>Главная панель</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="820"/>
        <source>Editor font:</source>
        <translation>Шрифт редактора:</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="828"/>
        <source> pt</source>
        <translation> пт</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="237"/>
        <source>Building…</source>
        <translation>Сборка…</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1959"/>
        <source>Build completed</source>
        <translation>Сборка завершена</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1960"/>
        <source>Build failed</source>
        <translation>Ошибка сборки</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="854"/>
        <source>Cannot open project</source>
        <translation>Не удалось открыть проект</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1406"/>
        <source>All files saved</source>
        <translation>Все файлы сохранены</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="948"/>
        <location filename="../src/MainWindow.cpp" line="1350"/>
        <source>Unsaved changes</source>
        <translation>Несохранённые изменения</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="949"/>
        <source>Some AI results have not been saved. Save a copy before leaving this project.</source>
        <translation>Некоторые ответы AI не сохранены. Сохраните копию перед закрытием проекта.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1039"/>
        <source>Cannot restore project</source>
        <translation>Не удалось восстановить проект</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1714"/>
        <source>Build parameters of %1</source>
        <translation>Параметры сборки %1</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1718"/>
        <source>Default (declared in)</source>
        <translation>По умолчанию (где объявлен)</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1718"/>
        <source>✎ Value for Check and Build</source>
        <translation>✎ Значение для проверки и сборки</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1746"/>
        <source>Empty — the default %1</source>
        <translation>Пусто — значение по умолчанию %1</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1772"/>
        <source>&lt;b&gt;What this is.&lt;/b&gt; The parameters (&lt;code&gt;params:&lt;/code&gt;) that the project and the document &lt;b&gt;%1&lt;/b&gt; declare, with their defaults. Here you give them other values for this document without editing any file — as &lt;code&gt;primula build %1 --param NAME=VALUE&lt;/code&gt; would.&lt;br&gt;&lt;b&gt;Where they act.&lt;/b&gt; Check, Build and the document inspection in Studio, and the console with the context «Current file». Building all targets of the project does not use them: a target sets its own &lt;code&gt;params&lt;/code&gt;.&lt;br&gt;&lt;b&gt;How.&lt;/b&gt; Click a cell of the last column and type; an empty cell keeps the default. Values are written as in &lt;code&gt;--param&lt;/code&gt;: text, &lt;code&gt;true&lt;/code&gt;/&lt;code&gt;false&lt;/code&gt;, numbers, dates &lt;code&gt;2026-10-16&lt;/code&gt;. They are kept in &lt;code&gt;.primula-studio/settings.json&lt;/code&gt; of the project; Reset clears them. «Default (declared in)» tells whether the project or the document declares the parameter; a document parameter overrides that of the project.</source>
        <translation>&lt;b&gt;Что это.&lt;/b&gt; Параметры (&lt;code&gt;params:&lt;/code&gt;), которые объявляют проект и документ &lt;b&gt;%1&lt;/b&gt;, со значениями по умолчанию. Здесь вы задаёте им другие значения для этого документа, не меняя ни одного файла, — как &lt;code&gt;primula build %1 --param ИМЯ=ЗНАЧЕНИЕ&lt;/code&gt;.&lt;br&gt;&lt;b&gt;Где действуют.&lt;/b&gt; Проверка, сборка и разбор документа в Studio, а также консоль с контекстом «Текущий файл». Сборка всех целей проекта их не использует: цель задаёт свои &lt;code&gt;params&lt;/code&gt;.&lt;br&gt;&lt;b&gt;Как.&lt;/b&gt; Щёлкните ячейку последнего столбца и введите значение; пустая ячейка — значение по умолчанию. Значения пишутся как в &lt;code&gt;--param&lt;/code&gt;: текст, &lt;code&gt;true&lt;/code&gt;/&lt;code&gt;false&lt;/code&gt;, числа, даты &lt;code&gt;2026-10-16&lt;/code&gt;. Они хранятся в &lt;code&gt;.primula-studio/settings.json&lt;/code&gt; проекта; «Сбросить» их очищает. «По умолчанию (где объявлен)» показывает, объявляет параметр проект или документ; параметр документа заменяет параметр проекта.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1784"/>
        <source>Neither the project nor the document &lt;b&gt;%1&lt;/b&gt; declares parameters (&lt;code&gt;params:&lt;/code&gt;): there is nothing to set here.</source>
        <translation>Ни проект, ни документ &lt;b&gt;%1&lt;/b&gt; не объявляют параметров (&lt;code&gt;params:&lt;/code&gt;): здесь нечего задавать.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1851"/>
        <source>%1 is a file of kind %2: document metadata belong to a document (doc:) or to a project file (doc_defaults:).</source>
        <translation>%1 — файл вида %2: метаданные документа относятся к документу (doc:) или к файлу проекта (doc_defaults:).</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1884"/>
        <source>Nothing to add: %1: in %2 already has %3.</source>
        <translation>Добавлять нечего: %1: в %2 уже содержит %3.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1886"/>
        <source>%1: in %2 is written as {…}; add the fields by hand.</source>
        <translation>%1: в %2 записан как {…}; добавьте поля вручную.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1897"/>
        <source>Added to %1, %2: %3.
The values are proposals: Tab goes from one to the next.</source>
        <translation>Добавлено в %1, %2: %3.
Значения — предложения: Tab переходит к следующему.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1988"/>
        <source>Error</source>
        <translation>Ошибка</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1989"/>
        <source>Warning</source>
        <translation>Предупреждение</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2029"/>
        <source>This works in a writable .prml editor.</source>
        <translation>Это работает в редакторе .prml, доступном для записи.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2440"/>
        <source>Ask AI about the document</source>
        <translation>Запрос к AI по документу</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2443"/>
        <source>Describe what should be checked, rewritten, or prepared…</source>
        <translation>Опишите, что нужно проверить, переписать или подготовить…</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2445"/>
        <source>Selected text</source>
        <translation>Выделенный текст</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2519"/>
        <source>Send</source>
        <translation>Отправить</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2549"/>
        <source>Task:</source>
        <translation>Задание:</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2574"/>
        <source>Text scope:</source>
        <translation>Объём текста:</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2591"/>
        <source>Empty task</source>
        <translation>Пустое задание</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2591"/>
        <source>Enter a task for AI.</source>
        <translation>Введите задание для AI.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2683"/>
        <source>Waiting for AI response…</source>
        <translation>Ожидание ответа AI…</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2684"/>
        <source>Cancel</source>
        <translation>Отмена</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2738"/>
        <location filename="../src/MainWindow.cpp" line="2775"/>
        <source>AI request failed</source>
        <translation>Ошибка AI-запроса</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1419"/>
        <source> [missing]</source>
        <translation> [нет файла]</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2446"/>
        <source>Entire file</source>
        <translation>Весь файл</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2487"/>
        <source>Include the styles modules of the project</source>
        <translation>Добавить модули стилей проекта</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2488"/>
        <source>Include the other open files</source>
        <translation>Добавить другие открытые файлы</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3075"/>
        <source>AI</source>
        <translation>AI</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3111"/>
        <source>Document &amp;parameters: %1 (%2 set)…</source>
        <translation>&amp;Параметры документа: %1 (задано %2)…</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3112"/>
        <source>Document &amp;parameters: %1…</source>
        <translation>&amp;Параметры документа: %1…</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3338"/>
        <source>Language changed</source>
        <translation>Язык изменён</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3338"/>
        <source>Restart Studio to apply the new interface language.</source>
        <translation>Перезапустите Studio, чтобы применить новый язык интерфейса.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1073"/>
        <source>No recent projects</source>
        <translation>Нет недавних проектов</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="238"/>
        <source>Running primula parallel…</source>
        <translation>Выполняется primula parallel…</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="381"/>
        <source>Files changed outside Studio:</source>
        <translation>Файлы изменены вне Studio:</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="386"/>
        <source>Reload selected</source>
        <translation>Перечитать выбранный</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="387"/>
        <source>Keep editor</source>
        <translation>Оставить текст</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="388"/>
        <source>Keep the editor text; a later Save may overwrite the changed disk file.</source>
        <translation>Оставить текст редактора; последующее сохранение может перезаписать изменённый файл на диске.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="409"/>
        <source>Structure</source>
        <translation>Структура</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="414"/>
        <source>Styles</source>
        <translation>Стили</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="419"/>
        <source>Palette</source>
        <translation>Палитра</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="464"/>
        <source>Parallel tracks</source>
        <translation>Параллельные потоки</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="556"/>
        <source>&amp;New</source>
        <translation>&amp;Создать</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="557"/>
        <source>&amp;Document…</source>
        <translation>&amp;Документ…</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="559"/>
        <source>&amp;Fragment…</source>
        <translation>&amp;Фрагмент…</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="560"/>
        <source>&amp;Module of definitions…</source>
        <translation>&amp;Модуль определений…</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="561"/>
        <source>&amp;Styles module…</source>
        <translation>Модуль &amp;стилей…</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="563"/>
        <source>&amp;Project…</source>
        <translation>&amp;Проект…</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="564"/>
        <source>&amp;Order project…</source>
        <translation>Проект &amp;заказа…</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="566"/>
        <source>Open the folder of user templates</source>
        <translation>Открыть папку шаблонов пользователя</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="621"/>
        <source>&amp;Insert</source>
        <translation>Вс&amp;тавка</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="627"/>
        <source>F&amp;ormat</source>
        <translation>Ф&amp;ормат</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="628"/>
        <source>&amp;Apply style…</source>
        <translation>&amp;Применить стиль…</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="631"/>
        <source>&amp;Remove style at the cursor</source>
        <translation>&amp;Снять стиль у курсора</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="639"/>
        <source>&amp;Build document (ODT and PDF)</source>
        <translation>&amp;Собрать документ (ODT и PDF)</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="641"/>
        <source>Build all &amp;targets of the project</source>
        <translation>Собрать все &amp;цели проекта</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="643"/>
        <location filename="../src/MainWindow.cpp" line="3110"/>
        <source>Document &amp;parameters…</source>
        <translation>&amp;Параметры документа…</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="646"/>
        <source>Parallel &amp;tracks</source>
        <translation>Параллельные &amp;потоки</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="660"/>
        <source>&amp;Strict: warnings are errors</source>
        <translation>&amp;Строго: предупреждения — ошибки</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="669"/>
        <source>Show PDF after a successful build</source>
        <translation>Показывать PDF после успешной сборки</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="671"/>
        <source>If the PDF was visible</source>
        <translation>Если PDF был виден</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="672"/>
        <source>Always</source>
        <translation>Всегда</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="673"/>
        <source>Never</source>
        <translation>Никогда</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="696"/>
        <source>Switch source / PDF</source>
        <translation>Переключить исходник / PDF</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="698"/>
        <source>Open files…</source>
        <translation>Открытые файлы…</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="705"/>
        <source>&amp;Console</source>
        <translation>&amp;Консоль</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="709"/>
        <source>The evaluator console: a window of its own for trying code and functions</source>
        <translation>Консоль вычислителя: отдельное окно для проб кода и функций</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="723"/>
        <source>Source and PDF side by side</source>
        <translation>Исходник и PDF рядом</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="726"/>
        <source>PDF as a tab</source>
        <translation>PDF отдельной вкладкой</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="746"/>
        <source>Edit AI context of the project</source>
        <translation>Редактировать контекст AI проекта</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="750"/>
        <source>Help at the cursor</source>
        <translation>Справка по месту курсора</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="751"/>
        <source>Language specification</source>
        <translation>Спецификация языка</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="752"/>
        <source>Standard library</source>
        <translation>Стандартная библиотека</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="753"/>
        <source>Command cheat sheet (PDF)</source>
        <translation>Шпаргалка команд (PDF)</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="754"/>
        <source>Author guide (PDF)</source>
        <translation>Руководство автора (PDF)</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1124"/>
        <source>A name in PATH or a path. The tool is run read-only: see its description in agents.json.</source>
        <translation>Имя в PATH или путь. Инструмент запускается только для чтения: см. его описание в agents.json.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1134"/>
        <source>found: %1</source>
        <translation>найдено: %1</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1141"/>
        <source>%1:</source>
        <translation>%1:</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2454"/>
        <source>Local skill primula-docs (the agent loads it; to compare with the reference)</source>
        <translation>Локальный skill primula-docs (агент загружает его сам; для сравнения со справочником)</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2584"/>
        <source>AI tools (programs: File → Settings):</source>
        <translation>Инструменты AI (программы: Файл → Настройки):</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2586"/>
        <source>AI receives the text in read-only mode; it cannot change project files.</source>
        <translation>AI получает текст только для чтения; оно не может менять файлы проекта.</translation>
    </message>
    <message numerus="yes">
        <location filename="../src/MainWindow.cpp" line="2601"/>
        <source>The request, with the text of the document and the context of the project, will be sent to %n service(s): %1.

Send it?</source>
        <translation>
            <numerusform>Запрос с текстом документа и контекстом проекта будет отправлен сервисам: %n (%1).

Отправить?</numerusform>
            <numerusform>Запрос с текстом документа и контекстом проекта будет отправлен сервисам: %n (%1).

Отправить?</numerusform>
            <numerusform>Запрос с текстом документа и контекстом проекта будет отправлен сервисам: %n (%1).

Отправить?</numerusform>
        </translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2682"/>
        <source>Waiting for the answers of %1…</source>
        <translation>Ожидание ответов: %1…</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2709"/>
        <source>Received %1 of %2. Waiting for: %3…</source>
        <translation>Получено %1 из %2. Ожидается: %3…</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2762"/>
        <source>no answer</source>
        <translation>ответа нет</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2776"/>
        <source>Some tools gave no answer:

%1</source>
        <translation>Некоторые инструменты не дали ответа:

%1</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3329"/>
        <source>Author guide</source>
        <translation>Руководство автора</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3330"/>
        <source>The PDF of the author guide is not found. It is part of the installation package (guide/&lt;language&gt;/) and of the source tree (docs/author/&lt;language&gt;/).

Looked in:
%1</source>
        <translation>PDF руководства автора не найден. Он входит в пакет установки (guide/&lt;язык&gt;/) и в дерево исходников (docs/author/&lt;язык&gt;/).

Искали в:
%1</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="760"/>
        <source>Translator: not found</source>
        <translation>Транслятор: не найден</translation>
    </message>
    <message>
        <source>Insert command bar |</source>
        <translation>Вставить управляющий символ |</translation>
    </message>
    <message>
        <source>Insert the command bar | at the cursor in any layout (Ctrl+\ or Alt+\)</source>
        <translation>Вставить управляющий символ | в позицию курсора в любой раскладке (Ctrl+\ или Alt+\)</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="807"/>
        <source>Switch layout</source>
        <translation>Переключить раскладку</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="811"/>
        <source>Switch between source and PDF side by side and PDF as a tab</source>
        <translation>Переключить: исходник и PDF рядом или PDF отдельной вкладкой</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="855"/>
        <source>Cannot read the project of %1.</source>
        <translation>Не удаётся прочитать проект %1.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="888"/>
        <source>Opened: %1</source>
        <translation>Открыто: %1</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="950"/>
        <source>Some files have unsaved changes.</source>
        <translation>В некоторых файлах есть несохранённые изменения.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="988"/>
        <source>Cannot save the workspace: %1</source>
        <translation>Не удаётся сохранить рабочее место: %1</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1040"/>
        <source>The file is unavailable: %1
The saved path has been kept. Check the file or mount, then open it again.</source>
        <translation>Файл недоступен: %1
Сохранённый путь оставлен. Проверьте файл или монтирование и откройте его снова.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1078"/>
        <source>Open project or document</source>
        <translation>Открыть проект или документ</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1080"/>
        <source>Primula projects and documents (*.prml);;All files (*)</source>
        <translation>Проекты и документы Primula (*.prml);;Все файлы (*)</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1087"/>
        <source>Open file</source>
        <translation>Открыть файл</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1089"/>
        <source>Text files (*.prml *.yaml *.yml *.csv *.json *.md *.txt);;PDF (*.pdf);;All files (*)</source>
        <translation>Текстовые файлы (*.prml *.yaml *.yml *.csv *.json *.md *.txt);;PDF (*.pdf);;Все файлы (*)</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1102"/>
        <source>Settings</source>
        <translation>Настройки</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1105"/>
        <location filename="../src/MainWindow.cpp" line="1134"/>
        <source>not found</source>
        <translation>не найден</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1106"/>
        <source>Empty: &apos;primula&apos; from PATH, or the launcher of the source tree.</source>
        <translation>Пусто — &apos;primula&apos; из PATH или запускатель из дерева исходников.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1107"/>
        <source>Browse…</source>
        <translation>Обзор…</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1115"/>
        <source>Primula translator:</source>
        <translation>Транслятор Primula:</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1158"/>
        <source>Translator version:</source>
        <translation>Версия транслятора:</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1184"/>
        <location filename="../src/MainWindow.cpp" line="1224"/>
        <source>Cannot create the AI context</source>
        <translation>Не удаётся создать контекст AI</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1235"/>
        <source>The Primula translator is not found: Check and Build are unavailable. Install &apos;primula&apos; into PATH or set its path in File → Settings.</source>
        <translation>Транслятор Primula не найден: проверка и сборка недоступны. Установите &apos;primula&apos; в PATH или укажите путь в Файл → Настройки.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1315"/>
        <location filename="../src/MainWindow.cpp" line="3609"/>
        <location filename="../src/MainWindow.cpp" line="3614"/>
        <source>Cannot open file</source>
        <translation>Не удаётся открыть файл</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1351"/>
        <source>Save changes to %1?</source>
        <translation>Сохранить изменения в %1?</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1383"/>
        <source>Cannot save file</source>
        <translation>Не удаётся сохранить файл</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1451"/>
        <source>PDF</source>
        <translation>PDF</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1571"/>
        <source>(do not change the status)</source>
        <translation>(не менять состояние)</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1574"/>
        <source>Status to write (or type your own):</source>
        <translation>Состояние для записи (или введите своё):</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1575"/>
        <source>Expected status:</source>
        <translation>Ожидаемое состояние:</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1588"/>
        <source>The document has no |parallel (or it is not inspected yet)</source>
        <translation>В документе нет |parallel (или он ещё не проверен)</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1594"/>
        <source>Track:</source>
        <translation>Поток:</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1600"/>
        <source>Confirm the translation of segment %1, track %2…</source>
        <translation>Подтвердить перевод сегмента %1, поток %2…</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1601"/>
        <source>Confirm the translation of this segment (put the cursor into a block of a translation)</source>
        <translation>Подтвердить перевод этого сегмента (поставьте курсор в блок перевода)</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1603"/>
        <source>Confirm the translation</source>
        <translation>Подтвердить перевод</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1611"/>
        <source>Confirm all blocks of a track…</source>
        <translation>Подтвердить все блоки потока…</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1612"/>
        <source>Confirm all blocks of a track</source>
        <translation>Подтвердить все блоки потока</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1614"/>
        <source>Confirm all blocks of %1</source>
        <translation>Подтвердить все блоки %1</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1620"/>
        <source>Write blank blocks of a track…</source>
        <translation>Дописать заготовки блоков потока…</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1621"/>
        <source>Write blank blocks</source>
        <translation>Дописать заготовки</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1625"/>
        <source>Check the status of the translations…</source>
        <translation>Проверить состояние переводов…</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1626"/>
        <source>Check the status of the translations</source>
        <translation>Проверить состояние переводов</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1702"/>
        <source>The saved file is read; unsaved changes of the header are not taken into account.</source>
        <translation>Читается сохранённый файл; несохранённые изменения заголовка не учтены.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1706"/>
        <source>Document parameters</source>
        <translation>Параметры документа</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1707"/>
        <source>The translator did not report the parameters of the document.
%1</source>
        <translation>Транслятор не сообщил параметры документа.
%1</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1718"/>
        <source>Parameter</source>
        <translation>Параметр</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1718"/>
        <source>Type</source>
        <translation>Тип</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1742"/>
        <source>project</source>
        <translation>проект</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1742"/>
        <source>document</source>
        <translation>документ</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1817"/>
        <source>Console: the standard library</source>
        <translation>Консоль: стандартная библиотека</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1825"/>
        <source>Console: the project %1</source>
        <translation>Консоль: проект %1</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1832"/>
        <source>Console: %1 (%2)</source>
        <translation>Консоль: %1 (%2)</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1869"/>
        <source>Author</source>
        <translation>Автор</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1870"/>
        <source>Organization</source>
        <translation>Организация</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1850"/>
        <location filename="../src/MainWindow.cpp" line="1882"/>
        <location filename="../src/MainWindow.cpp" line="1896"/>
        <source>Header fields</source>
        <translation>Поля заголовка</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="580"/>
        <source>&amp;Backups</source>
        <translation>&amp;Резервные копии</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="581"/>
        <source>Back up the project &amp;now</source>
        <translation>Сделать копию проекта &amp;сейчас</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="583"/>
        <source>&amp;Show backups…</source>
        <translation>&amp;Показать копии…</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="585"/>
        <source>Back up a file &amp;before saving it</source>
        <translation>Копировать файл &amp;перед сохранением</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="588"/>
        <source>The version on the disk is kept in .primula-studio/backups before a save replaces it.</source>
        <translation>Версия на диске сохраняется в .primula-studio/backups, прежде чем сохранение её заменит.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1144"/>
        <source>More tools: %1</source>
        <translation>Другие инструменты: %1</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1151"/>
        <source>Skipped in agents.json:
%1</source>
        <translation>Пропущено в agents.json:
%1</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1190"/>
        <location filename="../src/MainWindow.cpp" line="1216"/>
        <source>AI context of the project</source>
        <translation>Контекст AI проекта</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1198"/>
        <source>What AI should know about the documents: purpose, parties, terms, style of language. The text is added to every request.</source>
        <translation>Что AI должно знать о документах: назначение, стороны, термины, стиль языка. Текст добавляется к каждому запросу.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1216"/>
        <source>The file could not be saved: %1</source>
        <translation>Не удалось сохранить файл: %1</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1944"/>
        <source>primula parallel completed</source>
        <translation>primula parallel завершена</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1944"/>
        <source>primula parallel found problems</source>
        <translation>primula parallel нашла проблемы</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1959"/>
        <source>Check completed</source>
        <translation>Проверка завершена</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1960"/>
        <source>Check found errors</source>
        <translation>Проверка нашла ошибки</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2048"/>
        <source>Style %1 applied</source>
        <translation>Применён стиль %1</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2064"/>
        <source>Style removed</source>
        <translation>Стиль снят</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2064"/>
        <source>Style %1 removed</source>
        <translation>Стиль %1 снят</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2072"/>
        <source>No styles yet: the document has not been inspected.</source>
        <translation>Стилей пока нет: документ ещё не проверен.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2077"/>
        <source>Apply style</source>
        <translation>Применить стиль</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2079"/>
        <source>Style name</source>
        <translation>Имя стиля</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2083"/>
        <source>paragraph</source>
        <translation>абзацный</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2084"/>
        <source>character</source>
        <translation>символьный</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2085"/>
        <source>block</source>
        <translation>блочный</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2155"/>
        <source>&amp;Function</source>
        <translation>&amp;Функция</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2172"/>
        <source>The catalogue of constructs is not available</source>
        <translation>Справочник конструкций недоступен</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2175"/>
        <source>&amp;Header: add missing fields</source>
        <translation>&amp;Заголовок: добавить недостающие поля</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2177"/>
        <source>&amp;Image…</source>
        <translation>&amp;Изображение…</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2218"/>
        <location filename="../src/MainWindow.cpp" line="2223"/>
        <location filename="../src/MainWindow.cpp" line="2234"/>
        <source>Insert image</source>
        <translation>Вставить изображение</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2219"/>
        <source>Images (*.png *.jpg *.jpeg *.svg *.gif *.bmp *.tif *.tiff);;All files (*)</source>
        <translation>Изображения (*.png *.jpg *.jpeg *.svg *.gif *.bmp *.tif *.tiff);;Все файлы (*)</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2224"/>
        <source>The image is outside the project. Copy it into %1?</source>
        <translation>Изображение вне проекта. Скопировать его в %1?</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2234"/>
        <source>Cannot copy the image to %1.</source>
        <translation>Не удалось скопировать изображение в %1.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2275"/>
        <source>%1 — no PDF yet (Build: F9)</source>
        <translation>%1 — PDF ещё нет (собрать: F9)</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2411"/>
        <source>Reload changed file</source>
        <translation>Перечитать изменённый файл</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2412"/>
        <source>Reload %1 and discard its unsaved editor changes?</source>
        <translation>Перечитать %1, отбросив несохранённые изменения редактора?</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2417"/>
        <source>Cannot reload file</source>
        <translation>Не удалось перечитать файл</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2451"/>
        <source>Reference: constructs and functions</source>
        <translation>Справочник: конструкции и функции</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2452"/>
        <source>Whole specification and library (about 100k tokens)</source>
        <translation>Вся спецификация и библиотека (около 100 тыс. токенов)</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2453"/>
        <source>None</source>
        <translation>Ничего</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2455"/>
        <source>What AI receives about the Primula language. The reference is the catalogue of the translator: every construct and function with its summary and section. With the skill the agent loads its own installed skill primula-docs (skills/README.md tells how to install it); it should write «Skill: loaded» on the first line, else the skill is not available to it.</source>
        <translation>Что AI получает о языке Primula. Справочник — каталог транслятора: каждая конструкция и функция с кратким описанием и разделом. С skill агент загружает собственный установленный skill primula-docs (как его установить — в skills/README.md); в первой строке ответа он должен написать «Skill: loaded», иначе skill ему недоступен.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2462"/>
        <source>e.g. 6.8, 10.5, stdlib:3</source>
        <translation>напр. 6.8, 10.5, stdlib:3</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2463"/>
        <source>Sections of the specification (and of the standard library with &apos;stdlib:&apos;) sent in full; the section of the construct at the cursor is proposed.</source>
        <translation>Разделы спецификации (и стандартной библиотеки с «stdlib:»), отправляемые полностью; предлагается раздел конструкции под курсором.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2469"/>
        <source>Include the messages of the last check or build (%1)</source>
        <translation>Добавить сообщения последней проверки или сборки (%1)</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2471"/>
        <source>Include the messages of the last check or build (none)</source>
        <translation>Добавить сообщения последней проверки или сборки (нет)</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2475"/>
        <source>Include the project file</source>
        <translation>Добавить файл проекта</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2478"/>
        <source>Writing rules of Primula (from the skill: what not to change, frequent mistakes)</source>
        <translation>Правила записи Primula (из skill: что нельзя менять, частые ошибки)</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2480"/>
        <source>About 6 thousand characters from the skill primula-docs built into Studio; not sent with the skill level.</source>
        <translation>Около 6 тысяч знаков из skill primula-docs, встроенного в Studio; не отправляются с уровнем «skill».</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2482"/>
        <source>Ask for edits that can be checked and applied (tab «Edits» of the answer)</source>
        <translation>Просить правки, которые можно проверить и применить (вкладка «Правки» ответа)</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2484"/>
        <source>AI answers with blocks «was → now». Studio finds them in the document, checks the result with the translator and applies the chosen ones as one step of Undo.</source>
        <translation>AI отвечает блоками «было → стало». Studio находит их в документе, проверяет результат транслятором и применяет отмеченные одним шагом Undo.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2501"/>
        <source>%1 (not found)</source>
        <translation>%1 (не найдено)</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2506"/>
        <source>The request goes to this tool. With several tools, every one answers in its own tab.</source>
        <translation>Запрос идёт к этому инструменту. С несколькими инструментами каждый отвечает в своей вкладке.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2507"/>
        <source>The program «%1» is not found: set it in File → Settings.</source>
        <translation>Программа «%1» не найдена: укажите её в Файл → Настройки.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2522"/>
        <location filename="../src/MainWindow.cpp" line="2600"/>
        <source>Ask AI</source>
        <translation>Запрос к AI</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2522"/>
        <source>Choose at least one AI tool.</source>
        <translation>Выберите хотя бы один инструмент AI.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2533"/>
        <source>(own task)</source>
        <translation>(своя задача)</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2535"/>
        <source>A ready task; you can edit its text. More recipes: %1</source>
        <translation>Готовая задача; её текст можно изменить. Другие рецепты: %1</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2536"/>
        <source>Skipped in ai-recipes.json:
%1</source>
        <translation>Пропущено в ai-recipes.json:
%1</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2547"/>
        <source>Recipe:</source>
        <translation>Рецепт:</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2555"/>
        <source>Edit AI context…</source>
        <translation>Редактировать контекст AI…</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2557"/>
        <source>What AI should know about the documents of the project (purpose, parties, terms, style); it is added to every request. The same file as AI → Edit AI context of the project.</source>
        <translation>Что AI должно знать о документах проекта (назначение, стороны, термины, стиль); добавляется к каждому запросу. Тот же файл, что и AI → Редактировать контекст AI проекта.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2562"/>
        <source>The AI context of the project is empty: nothing about the project is sent.</source>
        <translation>Контекст AI проекта пуст: ничего о проекте не отправляется.</translation>
    </message>
    <message numerus="yes">
        <location filename="../src/MainWindow.cpp" line="2563"/>
        <source>The AI context of the project is included (%n character(s)).</source>
        <translation>
            <numerusform>Контекст AI проекта добавляется (знаков: %n).</numerusform>
            <numerusform>Контекст AI проекта добавляется (знаков: %n).</numerusform>
            <numerusform>Контекст AI проекта добавляется (знаков: %n).</numerusform>
        </translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2575"/>
        <source>Primula language:</source>
        <translation>Язык Primula:</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2576"/>
        <source>Sections in full:</source>
        <translation>Разделы полностью:</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2788"/>
        <location filename="../src/MainWindow.cpp" line="2976"/>
        <source>No project is open.</source>
        <translation>Проект не открыт.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2824"/>
        <location filename="../src/MainWindow.cpp" line="2828"/>
        <source>Backups</source>
        <translation>Резервные копии</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2824"/>
        <source>The project has no source files to back up.</source>
        <translation>В проекте нет исходных файлов для копирования.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2828"/>
        <source>The backup could not be made:
%1</source>
        <translation>Не удалось создать копию:
%1</translation>
    </message>
    <message numerus="yes">
        <location filename="../src/MainWindow.cpp" line="2831"/>
        <source>Backed up %n file(s) of the project.</source>
        <translation>
            <numerusform>Скопировано файлов проекта: %n.</numerusform>
            <numerusform>Скопировано файлов проекта: %n.</numerusform>
            <numerusform>Скопировано файлов проекта: %n.</numerusform>
        </translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2858"/>
        <location filename="../src/MainWindow.cpp" line="2868"/>
        <location filename="../src/MainWindow.cpp" line="2872"/>
        <source>Compare with the backup</source>
        <translation>Сравнение с копией</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2858"/>
        <source>The file does not exist now: %1</source>
        <translation>Файла сейчас нет: %1</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2865"/>
        <source>backup %1: %2</source>
        <translation>копия %1: %2</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2866"/>
        <source>current: %1</source>
        <translation>текущий: %1</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2868"/>
        <source>The comparison could not be made: %1</source>
        <translation>Не удалось сравнить: %1</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2872"/>
        <source>The file is the same as in the backup.</source>
        <translation>Файл такой же, как в копии.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2876"/>
        <source>Backup and the current file</source>
        <translation>Копия и текущий файл</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2887"/>
        <source>«-» is the backup, «+» is the current file.</source>
        <translation>«-» — копия, «+» — текущий файл.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2897"/>
        <location filename="../src/MainWindow.cpp" line="2901"/>
        <location filename="../src/MainWindow.cpp" line="2907"/>
        <location filename="../src/MainWindow.cpp" line="2923"/>
        <source>Restore</source>
        <translation>Восстановление</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2897"/>
        <source>The copy is missing or unreadable: %1</source>
        <translation>Копии нет или её нельзя прочитать: %1</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2902"/>
        <source>Restore %1 as it was at %2?

The current state is backed up first.</source>
        <translation>Восстановить %1 в виде на %2?

Текущее состояние сначала будет сохранено в копии.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2907"/>
        <source>A backup of the current file could not be made:
%1

Restore anyway?</source>
        <translation>Не удалось сделать копию текущего файла:
%1

Всё равно восстановить?</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2917"/>
        <source>Restored in the editor: %1 (not saved; Undo takes it back).</source>
        <translation>Восстановлено в редакторе: %1 (не сохранено; Undo вернёт).</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2923"/>
        <source>The file could not be written: %1</source>
        <translation>Не удалось записать файл: %1</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2926"/>
        <source>Restored: %1</source>
        <translation>Восстановлено: %1</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2982"/>
        <source>There is no document to check this file in.</source>
        <translation>Нет документа, в котором можно проверить этот файл.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2998"/>
        <source>Cannot write a temporary file.</source>
        <translation>Не удаётся записать временный файл.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3008"/>
        <source>The translator gave no result (exit code %1).</source>
        <translation>Транслятор не дал результата (код выхода %1).</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3024"/>
        <location filename="../src/MainWindow.cpp" line="3036"/>
        <location filename="../src/MainWindow.cpp" line="3045"/>
        <source>Apply edits</source>
        <translation>Применение правок</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3024"/>
        <source>The file cannot be edited: %1</source>
        <translation>Файл нельзя редактировать: %1</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3037"/>
        <source>None of the chosen edits can be applied now: the text of the document has changed.</source>
        <translation>Ни одну из отмеченных правок сейчас нельзя применить: текст документа изменился.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3046"/>
        <source>A backup of the file could not be made:
%1

Apply the edits anyway?</source>
        <translation>Не удалось сделать копию файла:
%1

Всё равно применить правки?</translation>
    </message>
    <message numerus="yes">
        <location filename="../src/MainWindow.cpp" line="3065"/>
        <source>Applied %n edit(s), %1 skipped; the file is not saved (Undo takes the edits back).</source>
        <translation>
            <numerusform>Применено правок: %n, пропущено: %1; файл не сохранён (Undo вернёт правки).</numerusform>
            <numerusform>Применено правок: %n, пропущено: %1; файл не сохранён (Undo вернёт правки).</numerusform>
            <numerusform>Применено правок: %n, пропущено: %1; файл не сохранён (Undo вернёт правки).</numerusform>
        </translation>
    </message>
    <message numerus="yes">
        <location filename="../src/MainWindow.cpp" line="3066"/>
        <source>Applied %n edit(s); the file is not saved (Undo takes the edits back).</source>
        <translation>
            <numerusform>Применено правок: %n; файл не сохранён (Undo вернёт правки).</numerusform>
            <numerusform>Применено правок: %n; файл не сохранён (Undo вернёт правки).</numerusform>
            <numerusform>Применено правок: %n; файл не сохранён (Undo вернёт правки).</numerusform>
        </translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3182"/>
        <source>No construct at the cursor: the quick help is open.</source>
        <translation>Под курсором нет конструкции: открыта краткая справка.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3191"/>
        <source>No construct here: there is no section to show.</source>
        <translation>Здесь нет конструкции: показывать нечего.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3206"/>
        <source>library section %1</source>
        <translation>раздел библиотеки %1</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3206"/>
        <source>section %1</source>
        <translation>раздел %1</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3208"/>
        <source>Shown: %1 for “%2” (line %3, marked in the editor). The quick help is Help → Quick help.</source>
        <translation>Показан: %1 для «%2» (строка %3, отмечено в редакторе). Краткая справка — Справка → Краткая справка.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3241"/>
        <source>Primula language specification</source>
        <translation>Спецификация языка Primula</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3258"/>
        <source>Primula standard library</source>
        <translation>Стандартная библиотека Primula</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3281"/>
        <source>Command cheat sheet</source>
        <translation>Шпаргалка команд</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3281"/>
        <source>Cannot write %1.</source>
        <translation>Не удалось записать %1.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3400"/>
        <source>Cannot create files</source>
        <translation>Не удаётся создать файлы</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3410"/>
        <source>Created: %1</source>
        <translation>Создано: %1</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3417"/>
        <source>Order project created</source>
        <translation>Проект заказа создан</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3418"/>
        <source>Open the order project %1 now? Its targets are built with Shift+F9.</source>
        <translation>Открыть проект заказа %1 сейчас? Его цели собираются через Shift+F9.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3435"/>
        <source>New in this folder</source>
        <translation>Создать в этой папке</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3436"/>
        <source>Document…</source>
        <translation>Документ…</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3437"/>
        <source>Fragment…</source>
        <translation>Фрагмент…</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3438"/>
        <source>Module of definitions…</source>
        <translation>Модуль определений…</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3439"/>
        <source>Styles module…</source>
        <translation>Модуль стилей…</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3441"/>
        <source>Folder…</source>
        <translation>Папку…</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3445"/>
        <source>Open</source>
        <translation>Открыть</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3458"/>
        <source>Open in an external application</source>
        <translation>Открыть во внешней программе</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3462"/>
        <source>Copy under a new name…</source>
        <translation>Копировать под новым именем…</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3463"/>
        <source>Rename…</source>
        <translation>Переименовать…</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3464"/>
        <location filename="../src/MainWindow.cpp" line="3846"/>
        <source>Move to trash</source>
        <translation>Переместить в корзину</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3467"/>
        <source>Open the folder in the file manager</source>
        <translation>Открыть папку в файловом менеджере</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3626"/>
        <source>New folder</source>
        <translation>Новая папка</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3626"/>
        <source>Name of the folder:</source>
        <translation>Имя папки:</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3631"/>
        <source>Cannot create the folder</source>
        <translation>Не удаётся создать папку</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3651"/>
        <location filename="../src/MainWindow.cpp" line="3773"/>
        <source>The name is empty, contains / or is taken: %1</source>
        <translation>Имя пустое, содержит / или уже занято: %1</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3656"/>
        <location filename="../src/MainWindow.cpp" line="3673"/>
        <source>Cannot copy %1 to %2</source>
        <translation>Не удаётся скопировать %1 в %2</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3595"/>
        <location filename="../src/MainWindow.cpp" line="3664"/>
        <source>Cannot create %1</source>
        <translation>Не удаётся создать %1</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3727"/>
        <source>Copy under a new name</source>
        <translation>Копировать под новым именем</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3728"/>
        <source>New name of the copy of %1:</source>
        <translation>Новое имя копии %1:</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3734"/>
        <source>Cannot copy</source>
        <translation>Не удаётся скопировать</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3747"/>
        <source>Replace the old name</source>
        <translation>Заменить старое имя</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3748"/>
        <source>Replace «%1» with «%2» in the files of the copy?</source>
        <translation>Заменить «%1» на «%2» в файлах копии?</translation>
    </message>
    <message numerus="yes">
        <location filename="../src/MainWindow.cpp" line="3751"/>
        <source>%n file(s) contain the old name; see the details.</source>
        <translation>
            <numerusform>%n файл содержит старое имя; см. подробности.</numerusform>
            <numerusform>%n файла содержат старое имя; см. подробности.</numerusform>
            <numerusform>%n файлов содержат старое имя; см. подробности.</numerusform>
        </translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3753"/>
        <source>Cannot replace</source>
        <translation>Не удаётся заменить</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3758"/>
        <source>Copied: %1</source>
        <translation>Скопировано: %1</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3768"/>
        <location filename="../src/MainWindow.cpp" line="3816"/>
        <source>Save or close %1 first.</source>
        <translation>Сначала сохраните или закройте %1.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3793"/>
        <source>Cannot rename %1 to %2</source>
        <translation>Не удаётся переименовать %1 в %2</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3802"/>
        <source>Rename</source>
        <translation>Переименовать</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3802"/>
        <source>New name of %1:</source>
        <translation>Новое имя %1:</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3808"/>
        <source>Cannot rename</source>
        <translation>Не удаётся переименовать</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3828"/>
        <source>Cannot move %1 to the trash.</source>
        <translation>Не удаётся переместить %1 в корзину.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3828"/>
        <source>Cannot delete %1.</source>
        <translation>Не удаётся удалить %1.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3846"/>
        <source>Move %1 to the trash?</source>
        <translation>Переместить %1 в корзину?</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3854"/>
        <location filename="../src/MainWindow.cpp" line="3858"/>
        <source>Cannot move to trash</source>
        <translation>Не удаётся переместить в корзину</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3859"/>
        <source>%1
Delete %2 permanently? This cannot be undone.</source>
        <translation>%1
Удалить %2 окончательно? Это нельзя отменить.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3862"/>
        <source>Cannot delete</source>
        <translation>Не удаётся удалить</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="758"/>
        <source>Primula Studio %1
An editor and build interface for Primula documents.</source>
        <translation>Primula Studio %1
Редактор и интерфейс сборки документов Primula.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="603"/>
        <source>&amp;Edit</source>
        <translation>Пр&amp;авка</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="240"/>
        <source>Checking…</source>
        <translation>Проверка…</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="319"/>
        <source>Close</source>
        <translation>Закрыть</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="320"/>
        <source>Close other tabs</source>
        <translation>Закрыть другие вкладки</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="321"/>
        <source>Copy path</source>
        <translation>Копировать путь</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="400"/>
        <source>Files</source>
        <translation>Файлы</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="514"/>
        <source>Double-click a message to open its source location.</source>
        <translation>Двойной щелчок по сообщению открывает место в исходнике.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="570"/>
        <source>&amp;Open project or document…</source>
        <translation>&amp;Открыть проект или документ…</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="572"/>
        <source>Open &amp;file…</source>
        <translation>Открыть &amp;файл…</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="576"/>
        <source>&amp;Save</source>
        <translation>&amp;Сохранить</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="578"/>
        <source>Save a&amp;ll</source>
        <translation>Сохранить &amp;все</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="592"/>
        <source>&amp;Close tab</source>
        <translation>&amp;Закрыть вкладку</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="594"/>
        <source>Close &amp;other tabs</source>
        <translation>Закрыть &amp;другие вкладки</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="596"/>
        <source>Close &amp;project</source>
        <translation>Закрыть &amp;проект</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="598"/>
        <source>Se&amp;ttings…</source>
        <translation>&amp;Настройки…</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="611"/>
        <source>&amp;Find…</source>
        <translation>&amp;Найти…</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="613"/>
        <source>Find &amp;next</source>
        <translation>Найти &amp;далее</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="615"/>
        <source>Find &amp;previous</source>
        <translation>Найти &amp;предыдущее</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="617"/>
        <source>&amp;Replace…</source>
        <translation>&amp;Заменить…</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3600"/>
        <source>Created %1 from the template: edit it and save</source>
        <translation>Создан %1 из шаблона: измените и сохраните</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="599"/>
        <source>File &amp;types…</source>
        <translation>&amp;Типы файлов…</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3595"/>
        <source>File types</source>
        <translation>Типы файлов</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1393"/>
        <source>File types applied</source>
        <translation>Типы файлов применены</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1394"/>
        <source>File types applied with problems (see the Log)</source>
        <translation>Типы файлов применены с проблемами (см. «Журнал»)</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3584"/>
        <source>File types: %1</source>
        <translation>Типы файлов: %1</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3453"/>
        <source>Open as text in the editor</source>
        <translation>Открыть как текст в редакторе</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3449"/>
        <source>Open with %1</source>
        <translation>Открыть с помощью %1</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3619"/>
        <source>Opened with %1: %2</source>
        <translation>Открыто с помощью %1: %2</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3615"/>
        <source>The command of the file type %1 did not start:
%2

Check it in %3 (File → File types…).</source>
        <translation>Команда типа файлов %1 не запустилась:
%2

Проверьте её в %3 (Файл → Типы файлов…).</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3609"/>
        <source>The file type %1 has no command.</source>
        <translation>У типа файлов %1 нет команды.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3527"/>
        <source>&amp;DOCX (Word)</source>
        <translation>&amp;DOCX (Word)</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3526"/>
        <source>&amp;HTML (one file)</source>
        <translation>&amp;HTML (один файл)</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3525"/>
        <source>&amp;Markdown</source>
        <translation>&amp;Markdown</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3532"/>
        <source>Another &amp;format…</source>
        <translation>Другой &amp;формат…</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="654"/>
        <source>E&amp;xport</source>
        <translation>Э&amp;кспорт</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="324"/>
        <location filename="../src/MainWindow.cpp" line="1914"/>
        <location filename="../src/MainWindow.cpp" line="1926"/>
        <location filename="../src/MainWindow.cpp" line="3455"/>
        <location filename="../src/MainWindow.cpp" line="3537"/>
        <location filename="../src/MainWindow.cpp" line="3551"/>
        <source>Export</source>
        <translation>Экспорт</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3542"/>
        <source>Export &amp;as…</source>
        <translation>Экспортировать &amp;как…</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3544"/>
        <location filename="../src/MainWindow.cpp" line="3565"/>
        <source>Export as</source>
        <translation>Экспортировать как</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1934"/>
        <source>Export failed</source>
        <translation>Экспорт не удался</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1925"/>
        <source>Export needs pandoc</source>
        <translation>Для экспорта нужен pandoc</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1927"/>
        <source>Export to this format needs pandoc, and it is not found.

Install pandoc (https://pandoc.org; openSUSE: zypper install pandoc; Debian: apt install pandoc) and export again. The format JSON (the pandoc AST) needs no pandoc.</source>
        <translation>Для экспорта в этот формат нужен pandoc, а он не найден.

Установите pandoc (https://pandoc.org; openSUSE: zypper install pandoc; Debian: apt install pandoc) и повторите экспорт. Для формата JSON (AST pandoc) pandoc не нужен.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3552"/>
        <source>Export writes the evaluated document through pandoc: numbers of clauses, references, footnotes, tables and captions are kept; page layout (headers, footers, columns, page numbers) is not. Paragraph and character styles go to DOCX by name. Markdown, HTML, DOCX and other formats need pandoc (https://pandoc.org); JSON is the pandoc AST itself.</source>
        <translation>Экспорт записывает вычисленный документ через pandoc: номера пунктов, ссылки, сноски, таблицы и подписи сохраняются, разметка страниц (колонтитулы, колонки, номера страниц) — нет. Стили абзацев и символов переходят в DOCX по именам. Для Markdown, HTML, DOCX и других форматов нужен pandoc (https://pandoc.org); JSON — это сам AST pandoc.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1913"/>
        <source>Exported: %1</source>
        <translation>Экспортировано: %1</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="239"/>
        <source>Exporting…</source>
        <translation>Экспорт…</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3538"/>
        <source>Format (a writer of pandoc; json — the pandoc AST, no pandoc needed):</source>
        <translation>Формат (writer pandoc; json — AST pandoc, pandoc не нужен):</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3544"/>
        <source>Format:</source>
        <translation>Формат:</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3521"/>
        <source>Open a document of the project to export it</source>
        <translation>Откройте документ проекта, чтобы его экспортировать</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1917"/>
        <source>Open the file</source>
        <translation>Открыть файл</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1918"/>
        <source>Open the folder</source>
        <translation>Открыть каталог</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1914"/>
        <source>The document is exported to
%1</source>
        <translation>Документ экспортирован в
%1</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3550"/>
        <source>What is exported…</source>
        <translation>Что экспортируется…</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="327"/>
        <location filename="../src/MainWindow.cpp" line="3457"/>
        <source>File summary…</source>
        <translation>Сводка о файле…</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3478"/>
        <source>File summary</source>
        <translation>Сводка о файле</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3483"/>
        <source>File summary — %1</source>
        <translation>Сводка о файле — %1</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3479"/>
        <source>The translator could not describe %1:
%2</source>
        <translation>Транслятор не смог описать %1:
%2</translation>
    </message>
</context>
<context>
    <name>NewFileDialog</name>
    <message>
        <location filename="../src/NewFileDialog.cpp" line="29"/>
        <source>Document</source>
        <translation>Документ</translation>
    </message>
    <message>
        <location filename="../src/NewFileDialog.cpp" line="30"/>
        <source>Fragment</source>
        <translation>Фрагмент</translation>
    </message>
    <message>
        <location filename="../src/NewFileDialog.cpp" line="31"/>
        <source>Module of definitions</source>
        <translation>Модуль определений</translation>
    </message>
    <message>
        <location filename="../src/NewFileDialog.cpp" line="32"/>
        <source>Styles module</source>
        <translation>Модуль стилей</translation>
    </message>
    <message>
        <location filename="../src/NewFileDialog.cpp" line="33"/>
        <source>Project</source>
        <translation>Проект</translation>
    </message>
    <message>
        <location filename="../src/NewFileDialog.cpp" line="34"/>
        <source>Order project (extends)</source>
        <translation>Проект заказа (extends)</translation>
    </message>
    <message>
        <location filename="../src/NewFileDialog.cpp" line="43"/>
        <source>New</source>
        <translation>Создать</translation>
    </message>
    <message>
        <location filename="../src/NewFileDialog.cpp" line="64"/>
        <source>the name, when empty</source>
        <translation>имя, если пусто</translation>
    </message>
    <message>
        <location filename="../src/NewFileDialog.cpp" line="72"/>
        <source>Browse…</source>
        <translation>Обзор…</translation>
    </message>
    <message>
        <location filename="../src/NewFileDialog.cpp" line="74"/>
        <source>Place</source>
        <translation>Место</translation>
    </message>
    <message>
        <location filename="../src/NewFileDialog.cpp" line="84"/>
        <source>Kind:</source>
        <translation>Вид:</translation>
    </message>
    <message>
        <location filename="../src/NewFileDialog.cpp" line="85"/>
        <source>Template:</source>
        <translation>Шаблон:</translation>
    </message>
    <message>
        <location filename="../src/NewFileDialog.cpp" line="87"/>
        <source>Name:</source>
        <translation>Имя:</translation>
    </message>
    <message>
        <location filename="../src/NewFileDialog.cpp" line="88"/>
        <source>Title:</source>
        <translation>Заголовок:</translation>
    </message>
    <message>
        <location filename="../src/NewFileDialog.cpp" line="89"/>
        <source>Language of the texts:</source>
        <translation>Язык текстов:</translation>
    </message>
    <message>
        <location filename="../src/NewFileDialog.cpp" line="93"/>
        <source>Place:</source>
        <translation>Место:</translation>
    </message>
    <message>
        <location filename="../src/NewFileDialog.cpp" line="94"/>
        <source>Files to create:</source>
        <translation>Будет создано:</translation>
    </message>
    <message>
        <location filename="../src/NewFileDialog.cpp" line="97"/>
        <source>Create</source>
        <translation>Создать</translation>
    </message>
    <message>
        <location filename="../src/NewFileDialog.cpp" line="124"/>
        <source> (user)</source>
        <translation> (пользователя)</translation>
    </message>
    <message>
        <location filename="../src/NewFileDialog.cpp" line="196"/>
        <location filename="../src/NewFileDialog.cpp" line="201"/>
        <source>No templates of this kind.</source>
        <translation>Шаблонов этого вида нет.</translation>
    </message>
    <message>
        <location filename="../src/NewFileDialog.cpp" line="203"/>
        <source>Enter a name.</source>
        <translation>Введите имя.</translation>
    </message>
    <message>
        <location filename="../src/NewFileDialog.cpp" line="205"/>
        <source>The name must not contain / \ : * ? &quot; &lt; &gt; | or start with a dot.</source>
        <translation>Имя не может содержать / \ : * ? &quot; &lt; &gt; | или начинаться с точки.</translation>
    </message>
    <message>
        <location filename="../src/NewFileDialog.cpp" line="207"/>
        <source>Choose the place.</source>
        <translation>Выберите место.</translation>
    </message>
    <message>
        <location filename="../src/NewFileDialog.cpp" line="216"/>
        <source>Some files already exist; choose another name or place.</source>
        <translation>Некоторые файлы уже существуют — выберите другое имя или место.</translation>
    </message>
</context>
<context>
    <name>PalettePanel</name>
    <message>
        <location filename="../src/PalettePanel.cpp" line="29"/>
        <source>Search constructs and functions</source>
        <translation>Поиск конструкций и функций</translation>
    </message>
    <message>
        <location filename="../src/PalettePanel.cpp" line="33"/>
        <source>Construct</source>
        <translation>Конструкция</translation>
    </message>
    <message>
        <location filename="../src/PalettePanel.cpp" line="33"/>
        <source>Description</source>
        <translation>Описание</translation>
    </message>
    <message>
        <location filename="../src/PalettePanel.cpp" line="66"/>
        <source>Insert at the cursor</source>
        <translation>Вставить у курсора</translation>
    </message>
    <message>
        <location filename="../src/PalettePanel.cpp" line="68"/>
        <source>Copy the form %1</source>
        <translation>Копировать форму %1</translation>
    </message>
    <message>
        <location filename="../src/PalettePanel.cpp" line="68"/>
        <source>Copy the name %1</source>
        <translation>Копировать имя %1</translation>
    </message>
    <message>
        <location filename="../src/PalettePanel.cpp" line="70"/>
        <source>Copy the template</source>
        <translation>Копировать заготовку</translation>
    </message>
    <message>
        <location filename="../src/PalettePanel.cpp" line="74"/>
        <source>Specification section</source>
        <translation>Раздел спецификации</translation>
    </message>
    <message>
        <location filename="../src/PalettePanel.cpp" line="102"/>
        <source>Functions: %1</source>
        <translation>Функции: %1</translation>
    </message>
</context>
<context>
    <name>QObject</name>
    <message>
        <location filename="../src/AiHistory.cpp" line="50"/>
        <source>Task</source>
        <translation>Задание</translation>
    </message>
    <message>
        <location filename="../src/AiHistory.cpp" line="51"/>
        <source>Response</source>
        <translation>Ответ</translation>
    </message>
    <message>
        <location filename="../src/AiHistory.cpp" line="52"/>
        <source>Complete request</source>
        <translation>Полный запрос</translation>
    </message>
    <message>
        <location filename="../src/AiHistory.cpp" line="61"/>
        <source>Cannot save AI exchange: %1</source>
        <translation>Не удалось сохранить диалог AI: %1</translation>
    </message>
    <message>
        <location filename="../src/AiHistory.cpp" line="75"/>
        <location filename="../src/AiHistory.cpp" line="84"/>
        <source>Cannot create AI history file: %1</source>
        <translation>Не удалось создать файл истории AI: %1</translation>
    </message>
    <message>
        <location filename="../src/AiHistory.cpp" line="92"/>
        <source>Cannot choose an unused AI history filename.</source>
        <translation>Не удалось подобрать свободное имя файла истории AI.</translation>
    </message>
    <message>
        <location filename="../src/AiHistory.cpp" line="113"/>
        <source>Unrecognized AI history file: %1</source>
        <translation>Неизвестный формат файла истории AI: %1</translation>
    </message>
    <message>
        <location filename="../src/AiHistory.cpp" line="137"/>
        <source>AI history sections are incomplete: %1</source>
        <translation>В истории AI отсутствуют разделы: %1</translation>
    </message>
    <message>
        <location filename="../src/AiHistory.cpp" line="143"/>
        <source>AI history metadata is invalid: %1</source>
        <translation>Некорректные метаданные истории AI: %1</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1109"/>
        <source>Primula translator</source>
        <translation>Транслятор Primula</translation>
    </message>
    <message>
        <location filename="../src/AiEdits.cpp" line="170"/>
        <source>Edit</source>
        <translation>Правка</translation>
    </message>
    <message>
        <location filename="../src/AiEdits.cpp" line="171"/>
        <source>Was:</source>
        <translation>Было:</translation>
    </message>
    <message>
        <location filename="../src/AiEdits.cpp" line="172"/>
        <source>Now:</source>
        <translation>Стало:</translation>
    </message>
</context>
<context>
    <name>StructurePanel</name>
    <message>
        <location filename="../src/StructurePanel.cpp" line="55"/>
        <source>Table %1</source>
        <translation>Таблица %1</translation>
    </message>
    <message>
        <location filename="../src/StructurePanel.cpp" line="56"/>
        <source>Figure %1</source>
        <translation>Рисунок %1</translation>
    </message>
    <message>
        <location filename="../src/StructurePanel.cpp" line="57"/>
        <source>Numbered list %1</source>
        <translation>Нумерованный список %1</translation>
    </message>
    <message>
        <location filename="../src/StructurePanel.cpp" line="58"/>
        <source>Section %1</source>
        <translation>Секция %1</translation>
    </message>
    <message>
        <location filename="../src/StructurePanel.cpp" line="59"/>
        <source>Note %1</source>
        <translation>Примечание %1</translation>
    </message>
    <message>
        <location filename="../src/StructurePanel.cpp" line="61"/>
        <source>Parallel tracks: %1</source>
        <translation>Параллельные потоки: %1</translation>
    </message>
    <message>
        <location filename="../src/StructurePanel.cpp" line="66"/>
        <source>Full-width segment</source>
        <translation>Сегмент на всю ширину</translation>
    </message>
    <message>
        <location filename="../src/StructurePanel.cpp" line="67"/>
        <source>Segment %1</source>
        <translation>Сегмент %1</translation>
    </message>
    <message>
        <location filename="../src/StructurePanel.cpp" line="70"/>
        <source>Track %1</source>
        <translation>Поток %1</translation>
    </message>
    <message>
        <location filename="../src/StructurePanel.cpp" line="71"/>
        <source> — outdated</source>
        <translation> — устарел</translation>
    </message>
    <message>
        <location filename="../src/StructurePanel.cpp" line="72"/>
        <source> — changed after confirmation</source>
        <translation> — изменён после подтверждения</translation>
    </message>
    <message>
        <location filename="../src/StructurePanel.cpp" line="91"/>
        <source>Element</source>
        <translation>Элемент</translation>
    </message>
    <message>
        <location filename="../src/StructurePanel.cpp" line="91"/>
        <source>File</source>
        <translation>Файл</translation>
    </message>
    <message>
        <location filename="../src/StructurePanel.cpp" line="116"/>
        <source>Go to the line</source>
        <translation>Перейти к строке</translation>
    </message>
    <message>
        <location filename="../src/StructurePanel.cpp" line="117"/>
        <source>Insert a reference (no ID)</source>
        <translation>Вставить ссылку (нет ID)</translation>
    </message>
    <message>
        <location filename="../src/StructurePanel.cpp" line="117"/>
        <source>Insert the reference %1 at the cursor</source>
        <translation>Вставить ссылку %1 у курсора</translation>
    </message>
    <message>
        <location filename="../src/StructurePanel.cpp" line="120"/>
        <source>Copy the number</source>
        <translation>Копировать номер</translation>
    </message>
    <message>
        <location filename="../src/StructurePanel.cpp" line="120"/>
        <source>Copy the number %1</source>
        <translation>Копировать номер %1</translation>
    </message>
    <message>
        <location filename="../src/StructurePanel.cpp" line="122"/>
        <source>Copy a reference (no ID)</source>
        <translation>Копировать ссылку (нет ID)</translation>
    </message>
    <message>
        <location filename="../src/StructurePanel.cpp" line="122"/>
        <source>Copy the reference %1</source>
        <translation>Копировать ссылку %1</translation>
    </message>
    <message>
        <location filename="../src/StructurePanel.cpp" line="124"/>
        <source>Copy the ID</source>
        <translation>Копировать ID</translation>
    </message>
    <message>
        <location filename="../src/StructurePanel.cpp" line="185"/>
        <source>Outdated: %1</source>
        <translation>Устарело: %1</translation>
    </message>
</context>
<context>
    <name>StudioProject</name>
    <message>
        <location filename="../src/StudioProject.cpp" line="186"/>
        <location filename="../src/StudioProject.cpp" line="210"/>
        <source>Cannot create %1</source>
        <translation>Не удаётся создать %1</translation>
    </message>
    <message>
        <location filename="../src/StudioProject.cpp" line="218"/>
        <source># AI context of the project

What the AI should know about these documents: purpose, parties, terms, style of language.
</source>
        <translation># Контекст AI проекта

Что AI должен знать об этих документах: назначение, стороны, термины, стиль языка.
</translation>
    </message>
</context>
<context>
    <name>StyleEditing</name>
    <message>
        <location filename="../src/StyleEditing.cpp" line="294"/>
        <source>The arguments of the line %1 are not closed.</source>
        <translation>Аргументы в строке %1 не закрыты.</translation>
    </message>
    <message>
        <location filename="../src/StyleEditing.cpp" line="481"/>
        <source>The selection has only spaces.</source>
        <translation>В выделении только пробелы.</translation>
    </message>
    <message>
        <location filename="../src/StyleEditing.cpp" line="486"/>
        <source>A character style covers text of one paragraph; the selection crosses an empty line.</source>
        <translation>Символьный стиль действует в пределах абзаца, а выделение пересекает пустую строку.</translation>
    </message>
    <message>
        <location filename="../src/StyleEditing.cpp" line="490"/>
        <source>The selection cuts an inline form {…}; select whole forms.</source>
        <translation>Выделение разрезает строчную форму {…}; выделите формы целиком.</translation>
    </message>
    <message>
        <location filename="../src/StyleEditing.cpp" line="502"/>
        <source>Nothing to style: the line is empty.</source>
        <translation>Нечего оформлять: строка пуста.</translation>
    </message>
    <message>
        <location filename="../src/StyleEditing.cpp" line="580"/>
        <source>Style %1 has a computed or invalid name.</source>
        <translation>У стиля %1 вычисляемое или недопустимое имя.</translation>
    </message>
    <message>
        <location filename="../src/StyleEditing.cpp" line="593"/>
        <source>A table, list, frame or page style is set by the style= argument of its command.</source>
        <translation>Стиль таблицы, списка, рамки или страницы задаётся аргументом style= его команды.</translation>
    </message>
    <message>
        <location filename="../src/StyleEditing.cpp" line="652"/>
        <source>The environment opened on line %1 has no closing line.</source>
        <translation>У окружения, открытого в строке %1, нет строки закрытия.</translation>
    </message>
    <message>
        <location filename="../src/StyleEditing.cpp" line="661"/>
        <source>No style is applied at the cursor.</source>
        <translation>У курсора нет применённого стиля.</translation>
    </message>
    <message>
        <location filename="../src/StyleEditing.cpp" line="662"/>
        <source>Style %1 is not applied at the cursor.</source>
        <translation>Стиль %1 у курсора не применён.</translation>
    </message>
</context>
<context>
    <name>StylesPanel</name>
    <message>
        <location filename="../src/StylesPanel.cpp" line="27"/>
        <source>Paragraph styles</source>
        <translation>Стили абзацев</translation>
    </message>
    <message>
        <location filename="../src/StylesPanel.cpp" line="28"/>
        <source>Character styles</source>
        <translation>Стили символов</translation>
    </message>
    <message>
        <location filename="../src/StylesPanel.cpp" line="29"/>
        <source>Table styles</source>
        <translation>Стили таблиц</translation>
    </message>
    <message>
        <location filename="../src/StylesPanel.cpp" line="30"/>
        <source>List styles</source>
        <translation>Стили списков</translation>
    </message>
    <message>
        <location filename="../src/StylesPanel.cpp" line="31"/>
        <source>Page styles</source>
        <translation>Стили страниц</translation>
    </message>
    <message>
        <location filename="../src/StylesPanel.cpp" line="32"/>
        <source>Block styles</source>
        <translation>Стили блоков</translation>
    </message>
    <message>
        <location filename="../src/StylesPanel.cpp" line="39"/>
        <source>project</source>
        <translation>проект</translation>
    </message>
    <message>
        <location filename="../src/StylesPanel.cpp" line="40"/>
        <source>--style option</source>
        <translation>параметр --style</translation>
    </message>
    <message>
        <location filename="../src/StylesPanel.cpp" line="41"/>
        <source>document header</source>
        <translation>заголовок документа</translation>
    </message>
    <message>
        <location filename="../src/StylesPanel.cpp" line="42"/>
        <source>built-in</source>
        <translation>встроенный</translation>
    </message>
    <message>
        <location filename="../src/StylesPanel.cpp" line="43"/>
        <source>base (extends)</source>
        <translation>основа (extends)</translation>
    </message>
    <message>
        <location filename="../src/StylesPanel.cpp" line="44"/>
        <source>document code</source>
        <translation>код документа</translation>
    </message>
    <message>
        <location filename="../src/StylesPanel.cpp" line="80"/>
        <source>Filter styles</source>
        <translation>Фильтр стилей</translation>
    </message>
    <message>
        <location filename="../src/StylesPanel.cpp" line="84"/>
        <source>Style</source>
        <translation>Стиль</translation>
    </message>
    <message>
        <location filename="../src/StylesPanel.cpp" line="84"/>
        <source>Parent</source>
        <translation>Родитель</translation>
    </message>
    <message>
        <location filename="../src/StylesPanel.cpp" line="89"/>
        <source>Property</source>
        <translation>Свойство</translation>
    </message>
    <message>
        <location filename="../src/StylesPanel.cpp" line="89"/>
        <source>Value</source>
        <translation>Значение</translation>
    </message>
    <message>
        <location filename="../src/StylesPanel.cpp" line="89"/>
        <location filename="../src/StylesPanel.cpp" line="284"/>
        <source>Set in</source>
        <translation>Где задано</translation>
    </message>
    <message>
        <location filename="../src/StylesPanel.cpp" line="125"/>
        <source>Apply %1 at the cursor</source>
        <translation>Применить %1 у курсора</translation>
    </message>
    <message>
        <location filename="../src/StylesPanel.cpp" line="128"/>
        <source>Apply %1 (set by style= of its command)</source>
        <translation>Применить %1 (задаётся style= команды)</translation>
    </message>
    <message>
        <location filename="../src/StylesPanel.cpp" line="129"/>
        <source>Remove %1 at the cursor</source>
        <translation>Снять %1 у курсора</translation>
    </message>
    <message>
        <location filename="../src/StylesPanel.cpp" line="132"/>
        <source>Go to the definition</source>
        <translation>Перейти к определению</translation>
    </message>
    <message>
        <location filename="../src/StylesPanel.cpp" line="134"/>
        <source>Select the parent style %1</source>
        <translation>Выбрать родительский стиль %1</translation>
    </message>
    <message>
        <location filename="../src/StylesPanel.cpp" line="136"/>
        <source>Copy the name</source>
        <translation>Копировать имя</translation>
    </message>
    <message>
        <location filename="../src/StylesPanel.cpp" line="151"/>
        <source>Outdated: %1</source>
        <translation>Устарело: %1</translation>
    </message>
    <message>
        <location filename="../src/StylesPanel.cpp" line="230"/>
        <source>broken: Build → Check document shows why</source>
        <translation>сломан: причину покажет Сборка → Проверить документ</translation>
    </message>
    <message>
        <location filename="../src/StylesPanel.cpp" line="335"/>
        <source>paragraph style</source>
        <translation>абзацный стиль</translation>
    </message>
    <message>
        <location filename="../src/StylesPanel.cpp" line="335"/>
        <source>character style</source>
        <translation>символьный стиль</translation>
    </message>
    <message>
        <location filename="../src/StylesPanel.cpp" line="179"/>
        <source>Layers</source>
        <translation>Слои</translation>
    </message>
    <message>
        <location filename="../src/StylesPanel.cpp" line="193"/>
        <source>Document defaults</source>
        <translation>Значения документа по умолчанию</translation>
    </message>
    <message>
        <location filename="../src/StylesPanel.cpp" line="220"/>
        <source>defined in %1, line %2</source>
        <translation>определён в %1, строка %2</translation>
    </message>
    <message>
        <location filename="../src/StylesPanel.cpp" line="226"/>
        <source>made by the translator (derive, variant)</source>
        <translation>создан транслятором (derive, вариант)</translation>
    </message>
    <message>
        <location filename="../src/StylesPanel.cpp" line="248"/>
        <source>Own</source>
        <translation>Собственные</translation>
    </message>
    <message>
        <location filename="../src/StylesPanel.cpp" line="255"/>
        <source>translator</source>
        <translation>транслятор</translation>
    </message>
    <message>
        <location filename="../src/StylesPanel.cpp" line="261"/>
        <source>Inherited</source>
        <translation>Унаследованные</translation>
    </message>
</context>
<context>
    <name>Templates</name>
    <message>
        <location filename="../src/Templates.cpp" line="135"/>
        <source>The file already exists: %1</source>
        <translation>Файл уже существует: %1</translation>
    </message>
    <message>
        <location filename="../src/Templates.cpp" line="144"/>
        <source>Cannot read the template file %1</source>
        <translation>Не удаётся прочитать файл шаблона %1</translation>
    </message>
    <message>
        <location filename="../src/Templates.cpp" line="146"/>
        <source>Cannot create %1</source>
        <translation>Не удаётся создать %1</translation>
    </message>
</context>
<context>
    <name>Translator</name>
    <message>
        <location filename="../src/Translator.cpp" line="37"/>
        <source>The Primula translator is not found: install &apos;primula&apos; into PATH or set its path in the settings.</source>
        <translation>Транслятор Primula не найден: установите &apos;primula&apos; в PATH или укажите путь в настройках.</translation>
    </message>
    <message>
        <location filename="../src/Translator.cpp" line="46"/>
        <source>Cannot start %1: %2</source>
        <translation>Не удаётся запустить %1: %2</translation>
    </message>
    <message>
        <location filename="../src/Translator.cpp" line="54"/>
        <source>%1 did not finish in %2 s</source>
        <translation>%1 не завершился за %2 с</translation>
    </message>
    <message>
        <location filename="../src/Translator.cpp" line="86"/>
        <source>The translator gave no project description.</source>
        <translation>Транслятор не выдал описания проекта.</translation>
    </message>
    <message>
        <location filename="../src/Translator.cpp" line="104"/>
        <source>The translator gave no summary of the file.</source>
        <translation>Транслятор не выдал сводку о файле.</translation>
    </message>
</context>
</TS>
