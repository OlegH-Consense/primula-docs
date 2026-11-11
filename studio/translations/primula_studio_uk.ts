<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE TS>
<TS version="2.1" language="uk_UA">
<context>
    <name>AiAgents</name>
    <message>
        <location filename="../src/AiAgents.cpp" line="226"/>
        <source>The output of the tool is not JSON.</source>
        <translation>Вивід програми не є JSON.</translation>
    </message>
</context>
<context>
    <name>AiEditsPanel</name>
    <message>
        <location filename="../src/AiEditsPanel.cpp" line="37"/>
        <source>Edits proposed by AI. Choose the ones to apply; they are applied to the editor as one step that Undo takes back.</source>
        <translation>Правки, запропоновані AI. Позначте ті, що слід застосувати; вони застосовуються до редактора одним кроком, який скасовує Undo.</translation>
    </message>
    <message>
        <location filename="../src/AiEditsPanel.cpp" line="55"/>
        <source>Check the chosen edits</source>
        <translation>Перевірити позначені правки</translation>
    </message>
    <message>
        <location filename="../src/AiEditsPanel.cpp" line="57"/>
        <source>Runs the translator check on the document with each chosen edit, and with all of them: an edit that brings new errors is marked.</source>
        <translation>Запускає перевірку транслятором для документа з кожною позначеною правкою окремо й з усіма разом: правку, що вносить нові помилки, буде позначено.</translation>
    </message>
    <message>
        <location filename="../src/AiEditsPanel.cpp" line="59"/>
        <source>Apply the chosen edits</source>
        <translation>Застосувати позначені правки</translation>
    </message>
    <message>
        <location filename="../src/AiEditsPanel.cpp" line="92"/>
        <source>applied</source>
        <translation>застосовано</translation>
    </message>
    <message numerus="yes">
        <location filename="../src/AiEditsPanel.cpp" line="95"/>
        <source>brings %n new error(s)</source>
        <translation>
            <numerusform>вносить %n нову помилку</numerusform>
            <numerusform>вносить %n нові помилки</numerusform>
            <numerusform>вносить %n нових помилок</numerusform>
        </translation>
    </message>
    <message>
        <location filename="../src/AiEditsPanel.cpp" line="96"/>
        <source>checked, no new errors</source>
        <translation>перевірено, нових помилок немає</translation>
    </message>
    <message>
        <location filename="../src/AiEditsPanel.cpp" line="97"/>
        <source>ready</source>
        <translation>готова</translation>
    </message>
    <message>
        <location filename="../src/AiEditsPanel.cpp" line="98"/>
        <source>not found in the document</source>
        <translation>у документі не знайдено</translation>
    </message>
    <message>
        <location filename="../src/AiEditsPanel.cpp" line="99"/>
        <source>occurs several times</source>
        <translation>зустрічається кілька разів</translation>
    </message>
    <message>
        <location filename="../src/AiEditsPanel.cpp" line="100"/>
        <source>changes nothing</source>
        <translation>нічого не змінює</translation>
    </message>
    <message>
        <location filename="../src/AiEditsPanel.cpp" line="101"/>
        <source>overlaps another edit</source>
        <translation>перетинається з іншою правкою</translation>
    </message>
    <message numerus="yes">
        <location filename="../src/AiEditsPanel.cpp" line="167"/>
        <source>%n edit(s): %1 ready, %2 applied; chosen %3.</source>
        <translation>
            <numerusform>%n правка: готових %1, застосовано %2; позначено %3.</numerusform>
            <numerusform>%n правки: готових %1, застосовано %2; позначено %3.</numerusform>
            <numerusform>%n правок: готових %1, застосовано %2; позначено %3.</numerusform>
        </translation>
    </message>
    <message>
        <location filename="../src/AiEditsPanel.cpp" line="168"/>
        <source>The document is not available, so the edits cannot be applied.</source>
        <translation>Документ недоступний, тому правки не можна застосувати.</translation>
    </message>
    <message>
        <location filename="../src/AiEditsPanel.cpp" line="169"/>
        <source>The check is not available (the translator or the file type).</source>
        <translation>Перевірка недоступна (транслятор або тип файлу).</translation>
    </message>
    <message>
        <location filename="../src/AiEditsPanel.cpp" line="228"/>
        <source>Nothing is checked: choose at least one ready edit.</source>
        <translation>Нічого не перевірено: позначте хоча б одну готову правку.</translation>
    </message>
    <message>
        <location filename="../src/AiEditsPanel.cpp" line="236"/>
        <location filename="../src/AiEditsPanel.cpp" line="296"/>
        <source>The check did not run: %1</source>
        <translation>Перевірка не запустилась: %1</translation>
    </message>
    <message numerus="yes">
        <location filename="../src/AiEditsPanel.cpp" line="247"/>
        <source>Checked %n edit(s): %1 bring new errors. All chosen together: %2 new error(s).</source>
        <translation>
            <numerusform>Перевірено правок: %n. Вносять нові помилки: %1. Усі позначені разом: нових помилок — %2.</numerusform>
            <numerusform>Перевірено правок: %n. Вносять нові помилки: %1. Усі позначені разом: нових помилок — %2.</numerusform>
            <numerusform>Перевірено правок: %n. Вносять нові помилки: %1. Усі позначені разом: нових помилок — %2.</numerusform>
        </translation>
    </message>
    <message>
        <location filename="../src/AiEditsPanel.cpp" line="259"/>
        <location filename="../src/AiEditsPanel.cpp" line="265"/>
        <source>Apply edits</source>
        <translation>Застосування правок</translation>
    </message>
    <message>
        <location filename="../src/AiEditsPanel.cpp" line="259"/>
        <source>No edit is chosen: nothing is applied.</source>
        <translation>Жодної правки не позначено: нічого не застосовано.</translation>
    </message>
    <message numerus="yes">
        <location filename="../src/AiEditsPanel.cpp" line="266"/>
        <source>The chosen edits bring %n new error(s) to the document:

%1

Apply them anyway?</source>
        <translation>
            <numerusform>Позначені правки вносять до документа нових помилок: %n:

%1

Застосувати все одно?</numerusform>
            <numerusform>Позначені правки вносять до документа нових помилок: %n:

%1

Застосувати все одно?</numerusform>
            <numerusform>Позначені правки вносять до документа нових помилок: %n:

%1

Застосувати все одно?</numerusform>
        </translation>
    </message>
    <message>
        <location filename="../src/AiEditsPanel.cpp" line="276"/>
        <source>Apply this edit</source>
        <translation>Застосувати цю правку</translation>
    </message>
    <message>
        <location filename="../src/AiEditsPanel.cpp" line="278"/>
        <source>Check this edit</source>
        <translation>Перевірити цю правку</translation>
    </message>
    <message>
        <location filename="../src/AiEditsPanel.cpp" line="281"/>
        <source>Copy the replacement</source>
        <translation>Копіювати заміну</translation>
    </message>
    <message>
        <location filename="../src/AiEditsPanel.cpp" line="283"/>
        <source>Copy the original text</source>
        <translation>Копіювати початковий текст</translation>
    </message>
    <message>
        <location filename="../src/AiEditsPanel.cpp" line="286"/>
        <source>Choose all</source>
        <translation>Позначити всі</translation>
    </message>
    <message>
        <location filename="../src/AiEditsPanel.cpp" line="287"/>
        <source>Clear the choice</source>
        <translation>Зняти позначки</translation>
    </message>
</context>
<context>
    <name>AiHistoryPane</name>
    <message>
        <location filename="../src/AiHistoryPane.cpp" line="31"/>
        <source>Not saved — use Save copy</source>
        <translation>Не збережено — натисніть «Зберегти копію»</translation>
    </message>
    <message>
        <location filename="../src/AiHistoryPane.cpp" line="36"/>
        <source>Copy task</source>
        <translation>Копіювати завдання</translation>
    </message>
    <message>
        <location filename="../src/AiHistoryPane.cpp" line="38"/>
        <source>Copy answer (Markdown)</source>
        <translation>Копіювати відповідь (Markdown)</translation>
    </message>
    <message>
        <location filename="../src/AiHistoryPane.cpp" line="40"/>
        <source>Save copy…</source>
        <translation>Зберегти копію…</translation>
    </message>
    <message>
        <location filename="../src/AiHistoryPane.cpp" line="55"/>
        <source>Task</source>
        <translation>Завдання</translation>
    </message>
    <message>
        <location filename="../src/AiHistoryPane.cpp" line="56"/>
        <source>Response</source>
        <translation>Відповідь</translation>
    </message>
    <message>
        <location filename="../src/AiHistoryPane.cpp" line="63"/>
        <source>Preview</source>
        <translation>Перегляд</translation>
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
        <translation>Повний запит</translation>
    </message>
    <message>
        <location filename="../src/AiHistoryPane.cpp" line="81"/>
        <source>Find in AI response…</source>
        <translation>Знайти у відповіді AI…</translation>
    </message>
    <message>
        <location filename="../src/AiHistoryPane.cpp" line="82"/>
        <source>Find next</source>
        <translation>Знайти далі</translation>
    </message>
    <message>
        <location filename="../src/AiHistoryPane.cpp" line="99"/>
        <source>AI %1 · %2 [RO]</source>
        <translation>AI %1 · %2 [RO]</translation>
    </message>
    <message>
        <location filename="../src/AiHistoryPane.cpp" line="110"/>
        <source>Save AI exchange</source>
        <translation>Зберегти діалог AI</translation>
    </message>
    <message>
        <location filename="../src/AiHistoryPane.cpp" line="112"/>
        <source>Markdown files (*.md);;All files (*)</source>
        <translation>Файли Markdown (*.md);;Усі файли (*)</translation>
    </message>
    <message>
        <location filename="../src/AiHistoryPane.cpp" line="115"/>
        <source>Cannot save AI exchange</source>
        <translation>Не вдалося зберегти діалог AI</translation>
    </message>
</context>
<context>
    <name>AiWorkspace</name>
    <message>
        <location filename="../src/AiWorkspace.cpp" line="15"/>
        <source>Saved AI requests:</source>
        <translation>Збережені запити AI:</translation>
    </message>
    <message>
        <location filename="../src/AiWorkspace.cpp" line="24"/>
        <source>Close AI tab; saved files stay on disk</source>
        <translation>Закрити вкладку AI; збережені файли залишаться на диску</translation>
    </message>
    <message>
        <location filename="../src/AiWorkspace.cpp" line="25"/>
        <source>Close AI tab</source>
        <translation>Закрити вкладку AI</translation>
    </message>
</context>
<context>
    <name>BackupsDialog</name>
    <message>
        <location filename="../src/BackupsDialog.cpp" line="23"/>
        <source>Backups of the project</source>
        <translation>Резервні копії проєкту</translation>
    </message>
    <message>
        <location filename="../src/BackupsDialog.cpp" line="33"/>
        <source>Time</source>
        <translation>Час</translation>
    </message>
    <message>
        <location filename="../src/BackupsDialog.cpp" line="33"/>
        <source>Reason</source>
        <translation>Причина</translation>
    </message>
    <message>
        <location filename="../src/BackupsDialog.cpp" line="33"/>
        <source>Note</source>
        <translation>Примітка</translation>
    </message>
    <message>
        <location filename="../src/BackupsDialog.cpp" line="33"/>
        <source>Size</source>
        <translation>Розмір</translation>
    </message>
    <message>
        <location filename="../src/BackupsDialog.cpp" line="41"/>
        <location filename="../src/BackupsDialog.cpp" line="160"/>
        <source>Back up the project now</source>
        <translation>Зробити копію проєкту зараз</translation>
    </message>
    <message>
        <location filename="../src/BackupsDialog.cpp" line="42"/>
        <location filename="../src/BackupsDialog.cpp" line="155"/>
        <source>Compare with the current file…</source>
        <translation>Порівняти з поточним файлом…</translation>
    </message>
    <message>
        <location filename="../src/BackupsDialog.cpp" line="43"/>
        <location filename="../src/BackupsDialog.cpp" line="156"/>
        <source>Restore this version</source>
        <translation>Відновити цю версію</translation>
    </message>
    <message>
        <location filename="../src/BackupsDialog.cpp" line="44"/>
        <location filename="../src/BackupsDialog.cpp" line="157"/>
        <source>Delete the backup</source>
        <translation>Видалити копію</translation>
    </message>
    <message>
        <location filename="../src/BackupsDialog.cpp" line="45"/>
        <source>Open the folder</source>
        <translation>Відкрити теку</translation>
    </message>
    <message>
        <location filename="../src/BackupsDialog.cpp" line="46"/>
        <source>Close</source>
        <translation>Закрити</translation>
    </message>
    <message>
        <location filename="../src/BackupsDialog.cpp" line="73"/>
        <source>Before applying AI edits</source>
        <translation>Перед застосуванням правок AI</translation>
    </message>
    <message>
        <location filename="../src/BackupsDialog.cpp" line="74"/>
        <source>Before saving</source>
        <translation>Перед збереженням</translation>
    </message>
    <message>
        <location filename="../src/BackupsDialog.cpp" line="75"/>
        <source>Before a restore</source>
        <translation>Перед відновленням</translation>
    </message>
    <message>
        <location filename="../src/BackupsDialog.cpp" line="76"/>
        <source>Manual</source>
        <translation>Вручну</translation>
    </message>
    <message>
        <location filename="../src/BackupsDialog.cpp" line="101"/>
        <source>There are no backups yet. They are made before AI edits are applied and on request; «Back up the project now» copies the source files of the project.</source>
        <translation>Копій ще немає. Їх створюють перед застосуванням правок AI і на вимогу; «Зробити копію проєкту зараз» копіює вихідні файли проєкту.</translation>
    </message>
    <message numerus="yes">
        <location filename="../src/BackupsDialog.cpp" line="103"/>
        <source>%n backup(s), %1 in all. Restoring a version first makes a backup of the current file.</source>
        <translation>
            <numerusform>Копій: %n, разом %1. Відновлення версії спершу робить копію поточного файлу.</numerusform>
            <numerusform>Копій: %n, разом %1. Відновлення версії спершу робить копію поточного файлу.</numerusform>
            <numerusform>Копій: %n, разом %1. Відновлення версії спершу робить копію поточного файлу.</numerusform>
        </translation>
    </message>
    <message>
        <location filename="../src/BackupsDialog.cpp" line="113"/>
        <source>Choose a backup in the list.</source>
        <translation>Виберіть копію у списку.</translation>
    </message>
    <message numerus="yes">
        <location filename="../src/BackupsDialog.cpp" line="123"/>
        <source>This backup holds %n file(s): choose one of them.</source>
        <translation>
            <numerusform>У цій копії файлів: %n. Виберіть один з них.</numerusform>
            <numerusform>У цій копії файлів: %n. Виберіть один з них.</numerusform>
            <numerusform>У цій копії файлів: %n. Виберіть один з них.</numerusform>
        </translation>
    </message>
    <message>
        <location filename="../src/BackupsDialog.cpp" line="142"/>
        <source>Delete the backup of %1?</source>
        <translation>Видалити копію від %1?</translation>
    </message>
</context>
<context>
    <name>BuildController</name>
    <message>
        <location filename="../src/BuildController.cpp" line="18"/>
        <source>Failed to start the translator: %1
</source>
        <translation>Не вдалося запустити транслятор: %1
</translation>
    </message>
    <message>
        <location filename="../src/BuildController.cpp" line="28"/>
        <source>Finished successfully.
</source>
        <translation>Завершено успішно.
</translation>
    </message>
    <message>
        <location filename="../src/BuildController.cpp" line="29"/>
        <source>Finished with errors (exit code %1).
</source>
        <translation>Завершено з помилками (код завершення %1).
</translation>
    </message>
    <message>
        <location filename="../src/BuildController.cpp" line="50"/>
        <source>The Primula translator is not found: install &apos;primula&apos; into PATH or set its path in Settings.
</source>
        <translation>Транслятор Primula не знайдено: установіть &apos;primula&apos; у PATH або вкажіть шлях у налаштуваннях.
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
        <translation>Не вдається запустити %1: %2</translation>
    </message>
    <message>
        <location filename="../src/AiController.cpp" line="32"/>
        <source>%1 finished without a usable response (exit code %2).</source>
        <translation>%1: роботу завершено без придатної відповіді (код виходу %2).</translation>
    </message>
    <message>
        <location filename="../src/AiController.cpp" line="58"/>
        <source>AI request started.
</source>
        <translation>AI-запит запущено.
</translation>
    </message>
</context>
<context>
    <name>CodeEditor</name>
    <message>
        <location filename="../src/CodeEditor.cpp" line="258"/>
        <source>Context of the open help window</source>
        <translation>Контекст відкритого вікна довідки</translation>
    </message>
</context>
<context>
    <name>CommandCatalog</name>
    <message>
        <location filename="../src/CommandCatalog.cpp" line="40"/>
        <location filename="../src/CommandCatalog.cpp" line="95"/>
        <source>Specification, section %1</source>
        <translation>Специфікація, розділ %1</translation>
    </message>
    <message>
        <location filename="../src/CommandCatalog.cpp" line="52"/>
        <source>Only in styles code: a styles module, the project, the document</source>
        <translation>Лише в коді стилів: модуль стилів, проєкт, документ</translation>
    </message>
    <message>
        <location filename="../src/CommandCatalog.cpp" line="53"/>
        <source>Only in a table cell formula |=(…)</source>
        <translation>Лише у формулі клітинки таблиці |=(…)</translation>
    </message>
    <message>
        <location filename="../src/CommandCatalog.cpp" line="54"/>
        <source>Only in the code of a project file</source>
        <translation>Лише в коді файлу проєкту</translation>
    </message>
    <message>
        <location filename="../src/CommandCatalog.cpp" line="58"/>
        <source>Example: %1</source>
        <translation>Приклад: %1</translation>
    </message>
    <message>
        <location filename="../src/CommandCatalog.cpp" line="94"/>
        <source>Standard library, section %1</source>
        <translation>Стандартна бібліотека, розділ %1</translation>
    </message>
    <message>
        <location filename="../src/CommandCatalog.cpp" line="124"/>
        <source>The translator is not found.</source>
        <translation>Транслятор не знайдено.</translation>
    </message>
    <message>
        <location filename="../src/CommandCatalog.cpp" line="135"/>
        <source>primula commands failed: %1</source>
        <translation>Помилка primula commands: %1</translation>
    </message>
    <message>
        <location filename="../src/CommandCatalog.cpp" line="236"/>
        <source>The catalogue of constructs is empty.</source>
        <translation>Довідник конструкцій порожній.</translation>
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
        <translation>Поточний файл</translation>
    </message>
    <message>
        <location filename="../src/ConsolePanel.cpp" line="74"/>
        <source>Project</source>
        <translation>Проєкт</translation>
    </message>
    <message>
        <location filename="../src/ConsolePanel.cpp" line="75"/>
        <source>Library only</source>
        <translation>Лише бібліотека</translation>
    </message>
    <message>
        <location filename="../src/ConsolePanel.cpp" line="76"/>
        <source>The names the console has: those of the current file (a document with its parameters and code, a module, a styles module, the project file), of the project, or of the standard library only</source>
        <translation>Імена, які має консоль: поточного файлу (документ із параметрами й кодом, модуль, модуль стилів, файл проєкту), проєкту або лише стандартної бібліотеки</translation>
    </message>
    <message>
        <location filename="../src/ConsolePanel.cpp" line="84"/>
        <source>Restart</source>
        <translation>Перезапустити</translation>
    </message>
    <message>
        <location filename="../src/ConsolePanel.cpp" line="85"/>
        <source>A new session in the selected context; the names of the console are lost</source>
        <translation>Новий сеанс у вибраному контексті; імена консолі втрачаються</translation>
    </message>
    <message>
        <location filename="../src/ConsolePanel.cpp" line="86"/>
        <source>Interrupt</source>
        <translation>Перервати</translation>
    </message>
    <message>
        <location filename="../src/ConsolePanel.cpp" line="87"/>
        <source>Stop the running input; the names of the console stay (Ctrl+C in the input)</source>
        <translation>Зупинити поточне введення; імена консолі залишаються (Ctrl+C у рядку введення)</translation>
    </message>
    <message>
        <location filename="../src/ConsolePanel.cpp" line="124"/>
        <source>Double click puts the example into the input; the context menu has more</source>
        <translation>Подвійне клацання вставляє приклад у рядок введення; більше — у контекстному меню</translation>
    </message>
    <message>
        <location filename="../src/ConsolePanel.cpp" line="135"/>
        <source>Functions</source>
        <translation>Функції</translation>
    </message>
    <message>
        <location filename="../src/ConsolePanel.cpp" line="142"/>
        <source>Search names…</source>
        <translation>Пошук імен…</translation>
    </message>
    <message>
        <location filename="../src/ConsolePanel.cpp" line="146"/>
        <source>Name</source>
        <translation>Ім&apos;я</translation>
    </message>
    <message>
        <location filename="../src/ConsolePanel.cpp" line="146"/>
        <source>Type</source>
        <translation>Тип</translation>
    </message>
    <message>
        <location filename="../src/ConsolePanel.cpp" line="146"/>
        <source>Value</source>
        <translation>Значення</translation>
    </message>
    <message>
        <location filename="../src/ConsolePanel.cpp" line="149"/>
        <source>Names of the inputs (bold) and of the context; double click inserts the name, the context menu shows the value</source>
        <translation>Імена введень (жирним) і контексту; подвійне клацання вставляє ім&apos;я, контекстне меню показує значення</translation>
    </message>
    <message>
        <location filename="../src/ConsolePanel.cpp" line="153"/>
        <source>Names</source>
        <translation>Імена</translation>
    </message>
    <message>
        <location filename="../src/ConsolePanel.cpp" line="276"/>
        <source>Put the example into the input</source>
        <translation>Вставити приклад у рядок введення</translation>
    </message>
    <message>
        <location filename="../src/ConsolePanel.cpp" line="277"/>
        <location filename="../src/ConsolePanel.cpp" line="293"/>
        <source>Insert the name</source>
        <translation>Вставити ім&apos;я</translation>
    </message>
    <message>
        <location filename="../src/ConsolePanel.cpp" line="278"/>
        <source>Run :help %1</source>
        <translation>Виконати :help %1</translation>
    </message>
    <message>
        <location filename="../src/ConsolePanel.cpp" line="280"/>
        <source>Open the section %1</source>
        <translation>Відкрити розділ %1</translation>
    </message>
    <message>
        <location filename="../src/ConsolePanel.cpp" line="283"/>
        <location filename="../src/ConsolePanel.cpp" line="296"/>
        <source>Copy the name</source>
        <translation>Копіювати ім&apos;я</translation>
    </message>
    <message>
        <location filename="../src/ConsolePanel.cpp" line="294"/>
        <source>Show the value</source>
        <translation>Показати значення</translation>
    </message>
    <message>
        <location filename="../src/ConsolePanel.cpp" line="298"/>
        <source>Copy the value</source>
        <translation>Копіювати значення</translation>
    </message>
    <message>
        <location filename="../src/ConsolePanel.cpp" line="313"/>
        <source>(not evaluated yet)</source>
        <translation>(ще не обчислено)</translation>
    </message>
    <message>
        <location filename="../src/ConsolePanel.cpp" line="326"/>
        <source>Names (%1)</source>
        <translation>Імена (%1)</translation>
    </message>
    <message>
        <location filename="../src/ConsolePanel.cpp" line="537"/>
        <source>%1 names in the context (the Names tab)</source>
        <translation>імен у контексті: %1 (вкладка «Імена»)</translation>
    </message>
    <message>
        <location filename="../src/ConsolePanel.cpp" line="88"/>
        <source>Clear</source>
        <translation>Очистити</translation>
    </message>
    <message>
        <location filename="../src/ConsolePanel.cpp" line="89"/>
        <source>Clear the transcript; the names of the console stay</source>
        <translation>Очистити журнал; імена консолі залишаються</translation>
    </message>
    <message>
        <location filename="../src/ConsolePanel.cpp" line="106"/>
        <source>Primula code; Enter runs, Shift+Enter breaks the line, Ctrl+↑/↓ — history, :help NAME</source>
        <translation>Код Primula; Enter виконує, Shift+Enter — новий рядок, Ctrl+↑/↓ — історія, :help ІМ&apos;Я</translation>
    </message>
    <message>
        <location filename="../src/ConsolePanel.cpp" line="119"/>
        <source>Search functions…</source>
        <translation>Пошук функцій…</translation>
    </message>
    <message>
        <location filename="../src/ConsolePanel.cpp" line="421"/>
        <source>The session has ended (exit code %1). Restart starts a new one.</source>
        <translation>Сеанс завершено (код виходу %1). «Перезапустити» починає новий.</translation>
    </message>
    <message>
        <location filename="../src/ConsolePanel.cpp" line="426"/>
        <source>Cannot start the translator: %1</source>
        <translation>Не вдалося запустити транслятор: %1</translation>
    </message>
    <message>
        <location filename="../src/ConsolePanel.cpp" line="535"/>
        <source>The translator is not found.</source>
        <translation>Транслятор не знайдено.</translation>
    </message>
    <message>
        <location filename="../src/ConsolePanel.cpp" line="535"/>
        <source>not started</source>
        <translation>не запущено</translation>
    </message>
    <message>
        <location filename="../src/ConsolePanel.cpp" line="536"/>
        <source>starting…</source>
        <translation>запуск…</translation>
    </message>
    <message>
        <location filename="../src/ConsolePanel.cpp" line="538"/>
        <source>running…</source>
        <translation>виконується…</translation>
    </message>
</context>
<context>
    <name>DocumentInspector</name>
    <message>
        <location filename="../src/DocumentInspector.cpp" line="16"/>
        <source>Cannot start the translator: %1</source>
        <translation>Не вдалося запустити транслятор: %1</translation>
    </message>
    <message>
        <location filename="../src/DocumentInspector.cpp" line="33"/>
        <source>The translator stopped abnormally.</source>
        <translation>Транслятор аварійно завершився.</translation>
    </message>
    <message>
        <location filename="../src/DocumentInspector.cpp" line="34"/>
        <source>The translator output is not JSON.</source>
        <translation>Вивід транслятора — не JSON.</translation>
    </message>
    <message>
        <location filename="../src/DocumentInspector.cpp" line="79"/>
        <source>The translator is not found.</source>
        <translation>Транслятор не знайдено.</translation>
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
        <translation>Значення: %1</translation>
    </message>
    <message>
        <location filename="../src/EditorAssist.cpp" line="266"/>
        <source>For example: %1</source>
        <translation>Наприклад: %1</translation>
    </message>
    <message>
        <location filename="../src/EditorAssist.cpp" line="267"/>
        <source>Example: %1</source>
        <translation>Приклад: %1</translation>
    </message>
    <message>
        <location filename="../src/EditorAssist.cpp" line="268"/>
        <source>Recommended for a finished ODT.</source>
        <translation>Рекомендовано для готового ODT.</translation>
    </message>
    <message>
        <location filename="../src/EditorAssist.cpp" line="274"/>
        <source>Not filled: %1 (context menu or Insert → Header: add missing fields)</source>
        <translation>Не заповнено: %1 (контекстне меню або Вставка → Заголовок: додати відсутні поля)</translation>
    </message>
    <message>
        <location filename="../src/EditorAssist.cpp" line="276"/>
        <source>A document overrides these values key by key in its own doc:.</source>
        <translation>Документ замінює ці значення поштучно у власному doc:.</translation>
    </message>
    <message>
        <location filename="../src/EditorAssist.cpp" line="290"/>
        <source>The document has no style %1.</source>
        <translation>У документі немає стилю %1.</translation>
    </message>
    <message>
        <location filename="../src/EditorAssist.cpp" line="296"/>
        <source>The document has no element with ID %1.</source>
        <translation>У документі немає елемента з ID %1.</translation>
    </message>
    <message>
        <location filename="../src/EditorAssist.cpp" line="306"/>
        <source>Closes line %1: %2</source>
        <translation>Закриває рядок %1: %2</translation>
    </message>
    <message>
        <location filename="../src/EditorAssist.cpp" line="566"/>
        <source>closes line %1: %2</source>
        <translation>закриває рядок %1: %2</translation>
    </message>
    <message>
        <location filename="../src/EditorAssist.cpp" line="804"/>
        <source>Insert key into %1:</source>
        <translation>Вставити ключ у %1:</translation>
    </message>
    <message>
        <location filename="../src/EditorAssist.cpp" line="805"/>
        <source>Insert key</source>
        <translation>Вставити ключ</translation>
    </message>
    <message>
        <location filename="../src/EditorAssist.cpp" line="805"/>
        <source>Insert top-level key</source>
        <translation>Вставити ключ верхнього рівня</translation>
    </message>
    <message>
        <location filename="../src/EditorAssist.cpp" line="811"/>
        <source>Value of %1</source>
        <translation>Значення %1</translation>
    </message>
    <message>
        <location filename="../src/EditorAssist.cpp" line="826"/>
        <source>Add missing metadata fields (none missing)</source>
        <translation>Додати відсутні поля метаданих (усі заповнено)</translation>
    </message>
    <message>
        <location filename="../src/EditorAssist.cpp" line="827"/>
        <source>Add missing metadata fields: %1</source>
        <translation>Додати відсутні поля метаданих: %1</translation>
    </message>
    <message>
        <location filename="../src/EditorAssist.cpp" line="834"/>
        <source>All header keys (%1)</source>
        <translation>Усі ключі заголовка (%1)</translation>
    </message>
    <message>
        <location filename="../src/EditorAssist.cpp" line="965"/>
        <source>Hint (no construct here)</source>
        <translation>Підказка (тут немає конструкції)</translation>
    </message>
    <message>
        <location filename="../src/EditorAssist.cpp" line="965"/>
        <source>Hint: %1</source>
        <translation>Підказка: %1</translation>
    </message>
    <message>
        <location filename="../src/EditorAssist.cpp" line="973"/>
        <source>Specification section</source>
        <translation>Розділ специфікації</translation>
    </message>
    <message>
        <location filename="../src/EditorAssist.cpp" line="981"/>
        <source>Complete here</source>
        <translation>Доповнити тут</translation>
    </message>
</context>
<context>
    <name>EditorPane</name>
    <message>
        <location filename="../src/EditorPane.cpp" line="104"/>
        <source>Cannot open %1: %2</source>
        <translation>Не вдалося відкрити %1: %2</translation>
    </message>
    <message>
        <location filename="../src/EditorPane.cpp" line="150"/>
        <location filename="../src/EditorPane.cpp" line="156"/>
        <source>Cannot save %1: %2</source>
        <translation>Не вдалося зберегти %1: %2</translation>
    </message>
    <message>
        <location filename="../src/EditorPane.cpp" line="36"/>
        <location filename="../src/EditorPane.cpp" line="37"/>
        <source>Find text…</source>
        <translation>Знайти текст…</translation>
    </message>
    <message>
        <location filename="../src/EditorPane.cpp" line="38"/>
        <source>Previous</source>
        <translation>Назад</translation>
    </message>
    <message>
        <location filename="../src/EditorPane.cpp" line="39"/>
        <source>Next</source>
        <translation>Далі</translation>
    </message>
    <message>
        <location filename="../src/EditorPane.cpp" line="40"/>
        <source>Close</source>
        <translation>Закрити</translation>
    </message>
    <message>
        <location filename="../src/EditorPane.cpp" line="47"/>
        <source>Match case</source>
        <translation>Враховувати регістр</translation>
    </message>
    <message>
        <location filename="../src/EditorPane.cpp" line="49"/>
        <source>Whole words</source>
        <translation>Цілі слова</translation>
    </message>
    <message>
        <location filename="../src/EditorPane.cpp" line="65"/>
        <location filename="../src/EditorPane.cpp" line="66"/>
        <source>Replace with…</source>
        <translation>Замінити на…</translation>
    </message>
    <message>
        <location filename="../src/EditorPane.cpp" line="67"/>
        <source>Replace</source>
        <translation>Замінити</translation>
    </message>
    <message>
        <location filename="../src/EditorPane.cpp" line="68"/>
        <source>Replace all</source>
        <translation>Замінити все</translation>
    </message>
    <message>
        <location filename="../src/EditorPane.cpp" line="144"/>
        <source>File changed outside Studio: %1. Reload or choose Keep editor before saving.</source>
        <translation>Файл змінено поза Studio: %1. Перечитайте його або оберіть «Залишити текст» перед збереженням.</translation>
    </message>
    <message>
        <location filename="../src/EditorPane.cpp" line="246"/>
        <source>Text not found</source>
        <translation>Текст не знайдено</translation>
    </message>
    <message>
        <location filename="../src/EditorPane.cpp" line="249"/>
        <source>Search wrapped</source>
        <translation>Пошук продовжено з іншої межі файлу</translation>
    </message>
    <message>
        <location filename="../src/EditorPane.cpp" line="286"/>
        <source>Replaced: %1</source>
        <translation>Замінено: %1</translation>
    </message>
</context>
<context>
    <name>HelpDialog</name>
    <message>
        <location filename="../src/HelpDialog.cpp" line="24"/>
        <source>Quick help</source>
        <translation>Коротка довідка</translation>
    </message>
    <message>
        <location filename="../src/HelpDialog.cpp" line="48"/>
        <source>%1 — context: %2</source>
        <translation>%1 — контекст: %2</translation>
    </message>
    <message>
        <location filename="../src/HelpDialog.cpp" line="90"/>
        <source>Find in help…</source>
        <translation>Пошук у довідці…</translation>
    </message>
    <message>
        <location filename="../src/HelpDialog.cpp" line="91"/>
        <source>Find next</source>
        <translation>Знайти далі</translation>
    </message>
</context>
<context>
    <name>MainWindow</name>
    <message>
        <location filename="../src/MainWindow.cpp" line="343"/>
        <source>Fit width</source>
        <translation>За шириною</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="341"/>
        <location filename="../src/MainWindow.cpp" line="907"/>
        <source>PDF preview</source>
        <translation>Перегляд PDF</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="518"/>
        <location filename="../src/MainWindow.cpp" line="520"/>
        <source>Messages</source>
        <translation>Панель повідомлень</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2725"/>
        <source>AI result was not saved</source>
        <translation>Результат AI не збережено</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2726"/>
        <source>The response remains in its tab. Use Save copy to choose another location.
%1</source>
        <translation>Відповідь залишається у вкладці. Натисніть «Зберегти копію», щоб вибрати інше місце.
%1</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2728"/>
        <source>AI request and response saved: %1</source>
        <translation>Запит і відповідь AI збережено: %1</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="554"/>
        <source>&amp;File</source>
        <translation>&amp;Файл</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="506"/>
        <source>Message</source>
        <translation>Повідомлення</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="506"/>
        <source>File</source>
        <translation>Файл</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="506"/>
        <source>Line</source>
        <translation>Рядок</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="519"/>
        <source>Log</source>
        <translation>Журнал</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="574"/>
        <source>Recent projects</source>
        <translation>Недавні проєкти</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="601"/>
        <source>E&amp;xit</source>
        <translation>Ви&amp;хід</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="636"/>
        <source>&amp;Build</source>
        <translation>З&amp;бирання</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="637"/>
        <source>&amp;Check document</source>
        <translation>&amp;Перевірити документ</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="687"/>
        <source>Open ODT in Writer</source>
        <translation>Відкрити ODT у Writer</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="691"/>
        <source>Open project directory</source>
        <translation>Відкрити каталог проєкту</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="742"/>
        <source>&amp;AI</source>
        <translation>&amp;AI</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="743"/>
        <source>Ask AI about the document…</source>
        <translation>Запитати AI про документ…</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="745"/>
        <source>Show AI history</source>
        <translation>Показати історію AI</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="695"/>
        <source>&amp;View</source>
        <translation>&amp;Вигляд</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="721"/>
        <source>Layout</source>
        <translation>Компонування</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="730"/>
        <source>Increase editor font</source>
        <translation>Збільшити шрифт редактора</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="732"/>
        <source>Decrease editor font</source>
        <translation>Зменшити шрифт редактора</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="734"/>
        <source>Reset editor font size</source>
        <translation>Повернути розмір шрифту редактора</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="736"/>
        <source>Interface language</source>
        <translation>Мова інтерфейсу</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="737"/>
        <source>System language</source>
        <translation>Мова системи</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="748"/>
        <source>&amp;Help</source>
        <translation>&amp;Довідка</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="749"/>
        <source>Quick help</source>
        <translation>Коротка довідка</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="755"/>
        <location filename="../src/MainWindow.cpp" line="757"/>
        <source>About Primula Studio</source>
        <translation>Про Primula Studio</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="763"/>
        <source>Main toolbar</source>
        <translation>Головна панель</translation>
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
        <translation>Збирання…</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1959"/>
        <source>Build completed</source>
        <translation>Збирання завершено</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1960"/>
        <source>Build failed</source>
        <translation>Помилка збирання</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="854"/>
        <source>Cannot open project</source>
        <translation>Не вдалося відкрити проєкт</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1406"/>
        <source>All files saved</source>
        <translation>Усі файли збережено</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="948"/>
        <location filename="../src/MainWindow.cpp" line="1350"/>
        <source>Unsaved changes</source>
        <translation>Незбережені зміни</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="949"/>
        <source>Some AI results have not been saved. Save a copy before leaving this project.</source>
        <translation>Деякі відповіді AI не збережено. Збережіть копію перед закриттям проєкту.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1039"/>
        <source>Cannot restore project</source>
        <translation>Не вдалося відновити проєкт</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1714"/>
        <source>Build parameters of %1</source>
        <translation>Параметри збирання %1</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1718"/>
        <source>Default (declared in)</source>
        <translation>Типове (де оголошено)</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1718"/>
        <source>✎ Value for Check and Build</source>
        <translation>✎ Значення для перевірки й збирання</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1746"/>
        <source>Empty — the default %1</source>
        <translation>Порожнє — типове значення %1</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1772"/>
        <source>&lt;b&gt;What this is.&lt;/b&gt; The parameters (&lt;code&gt;params:&lt;/code&gt;) that the project and the document &lt;b&gt;%1&lt;/b&gt; declare, with their defaults. Here you give them other values for this document without editing any file — as &lt;code&gt;primula build %1 --param NAME=VALUE&lt;/code&gt; would.&lt;br&gt;&lt;b&gt;Where they act.&lt;/b&gt; Check, Build and the document inspection in Studio, and the console with the context «Current file». Building all targets of the project does not use them: a target sets its own &lt;code&gt;params&lt;/code&gt;.&lt;br&gt;&lt;b&gt;How.&lt;/b&gt; Click a cell of the last column and type; an empty cell keeps the default. Values are written as in &lt;code&gt;--param&lt;/code&gt;: text, &lt;code&gt;true&lt;/code&gt;/&lt;code&gt;false&lt;/code&gt;, numbers, dates &lt;code&gt;2026-10-16&lt;/code&gt;. They are kept in &lt;code&gt;.primula-studio/settings.json&lt;/code&gt; of the project; Reset clears them. «Default (declared in)» tells whether the project or the document declares the parameter; a document parameter overrides that of the project.</source>
        <translation>&lt;b&gt;Що це.&lt;/b&gt; Параметри (&lt;code&gt;params:&lt;/code&gt;), які оголошують проєкт і документ &lt;b&gt;%1&lt;/b&gt;, з типовими значеннями. Тут ви задаєте їм інші значення для цього документа, не змінюючи жодного файлу, — як &lt;code&gt;primula build %1 --param ІМ&apos;Я=ЗНАЧЕННЯ&lt;/code&gt;.&lt;br&gt;&lt;b&gt;Де діють.&lt;/b&gt; Перевірка, збирання й розбір документа в Studio, а також консоль із контекстом «Поточний файл». Збирання всіх цілей проєкту їх не використовує: ціль задає власні &lt;code&gt;params&lt;/code&gt;.&lt;br&gt;&lt;b&gt;Як.&lt;/b&gt; Клацніть клітинку останнього стовпця й введіть значення; порожня клітинка — типове значення. Значення пишуться як у &lt;code&gt;--param&lt;/code&gt;: текст, &lt;code&gt;true&lt;/code&gt;/&lt;code&gt;false&lt;/code&gt;, числа, дати &lt;code&gt;2026-10-16&lt;/code&gt;. Вони зберігаються в &lt;code&gt;.primula-studio/settings.json&lt;/code&gt; проєкту; «Скинути» їх очищає. «Типове (де оголошено)» показує, чи параметр оголошує проєкт, чи документ; параметр документа заміщує параметр проєкту.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1784"/>
        <source>Neither the project nor the document &lt;b&gt;%1&lt;/b&gt; declares parameters (&lt;code&gt;params:&lt;/code&gt;): there is nothing to set here.</source>
        <translation>Ні проєкт, ні документ &lt;b&gt;%1&lt;/b&gt; не оголошують параметрів (&lt;code&gt;params:&lt;/code&gt;): тут нічого задавати.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1851"/>
        <source>%1 is a file of kind %2: document metadata belong to a document (doc:) or to a project file (doc_defaults:).</source>
        <translation>%1 — файл виду %2: метадані документа належать документу (doc:) або файлу проєкту (doc_defaults:).</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1884"/>
        <source>Nothing to add: %1: in %2 already has %3.</source>
        <translation>Додавати нічого: %1: у %2 уже має %3.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1886"/>
        <source>%1: in %2 is written as {…}; add the fields by hand.</source>
        <translation>%1: у %2 записано як {…}; додайте поля вручну.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1897"/>
        <source>Added to %1, %2: %3.
The values are proposals: Tab goes from one to the next.</source>
        <translation>Додано в %1, %2: %3.
Значення — пропозиції: Tab переходить до наступного.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1988"/>
        <source>Error</source>
        <translation>Помилка</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1989"/>
        <source>Warning</source>
        <translation>Попередження</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2029"/>
        <source>This works in a writable .prml editor.</source>
        <translation>Це працює в редакторі .prml, доступному для запису.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2440"/>
        <source>Ask AI about the document</source>
        <translation>Запит до AI щодо документа</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2443"/>
        <source>Describe what should be checked, rewritten, or prepared…</source>
        <translation>Опишіть, що потрібно перевірити, переписати або підготувати…</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2445"/>
        <source>Selected text</source>
        <translation>Виділений текст</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2519"/>
        <source>Send</source>
        <translation>Надіслати</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2549"/>
        <source>Task:</source>
        <translation>Завдання:</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2574"/>
        <source>Text scope:</source>
        <translation>Обсяг тексту:</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2591"/>
        <source>Empty task</source>
        <translation>Порожнє завдання</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2591"/>
        <source>Enter a task for AI.</source>
        <translation>Введіть завдання для AI.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2683"/>
        <source>Waiting for AI response…</source>
        <translation>Очікування відповіді AI…</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2684"/>
        <source>Cancel</source>
        <translation>Скасувати</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2738"/>
        <location filename="../src/MainWindow.cpp" line="2775"/>
        <source>AI request failed</source>
        <translation>Помилка AI-запиту</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1419"/>
        <source> [missing]</source>
        <translation> [немає файла]</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2446"/>
        <source>Entire file</source>
        <translation>Увесь файл</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2487"/>
        <source>Include the styles modules of the project</source>
        <translation>Додати модулі стилів проєкту</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2488"/>
        <source>Include the other open files</source>
        <translation>Додати інші відкриті файли</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3075"/>
        <source>AI</source>
        <translation>AI</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3111"/>
        <source>Document &amp;parameters: %1 (%2 set)…</source>
        <translation>&amp;Параметри документа: %1 (задано %2)…</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3112"/>
        <source>Document &amp;parameters: %1…</source>
        <translation>&amp;Параметри документа: %1…</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3338"/>
        <source>Language changed</source>
        <translation>Мову змінено</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3338"/>
        <source>Restart Studio to apply the new interface language.</source>
        <translation>Перезапустіть Studio, щоб застосувати нову мову інтерфейсу.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1073"/>
        <source>No recent projects</source>
        <translation>Немає недавніх проєктів</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="238"/>
        <source>Running primula parallel…</source>
        <translation>Виконується primula parallel…</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="381"/>
        <source>Files changed outside Studio:</source>
        <translation>Файли змінено поза Studio:</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="386"/>
        <source>Reload selected</source>
        <translation>Перечитати обраний</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="387"/>
        <source>Keep editor</source>
        <translation>Залишити текст</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="388"/>
        <source>Keep the editor text; a later Save may overwrite the changed disk file.</source>
        <translation>Залишити текст редактора; наступне збереження може перезаписати змінений файл на диску.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="409"/>
        <source>Structure</source>
        <translation>Структура</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="414"/>
        <source>Styles</source>
        <translation>Стилі</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="419"/>
        <source>Palette</source>
        <translation>Палітра</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="464"/>
        <source>Parallel tracks</source>
        <translation>Паралельні потоки</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="556"/>
        <source>&amp;New</source>
        <translation>&amp;Створити</translation>
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
        <translation>&amp;Модуль визначень…</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="561"/>
        <source>&amp;Styles module…</source>
        <translation>Модуль &amp;стилів…</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="563"/>
        <source>&amp;Project…</source>
        <translation>&amp;Проєкт…</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="564"/>
        <source>&amp;Order project…</source>
        <translation>Проєкт &amp;замовлення…</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="566"/>
        <source>Open the folder of user templates</source>
        <translation>Відкрити теку шаблонів користувача</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="621"/>
        <source>&amp;Insert</source>
        <translation>Вс&amp;тавлення</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="627"/>
        <source>F&amp;ormat</source>
        <translation>Ф&amp;ормат</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="628"/>
        <source>&amp;Apply style…</source>
        <translation>&amp;Застосувати стиль…</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="631"/>
        <source>&amp;Remove style at the cursor</source>
        <translation>&amp;Зняти стиль біля курсора</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="639"/>
        <source>&amp;Build document (ODT and PDF)</source>
        <translation>&amp;Зібрати документ (ODT і PDF)</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="641"/>
        <source>Build all &amp;targets of the project</source>
        <translation>Зібрати всі &amp;цілі проєкту</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="643"/>
        <location filename="../src/MainWindow.cpp" line="3110"/>
        <source>Document &amp;parameters…</source>
        <translation>&amp;Параметри документа…</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="646"/>
        <source>Parallel &amp;tracks</source>
        <translation>Паралельні &amp;потоки</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="660"/>
        <source>&amp;Strict: warnings are errors</source>
        <translation>&amp;Суворо: попередження — помилки</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="669"/>
        <source>Show PDF after a successful build</source>
        <translation>Показувати PDF після успішного збирання</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="671"/>
        <source>If the PDF was visible</source>
        <translation>Якщо PDF був видимий</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="672"/>
        <source>Always</source>
        <translation>Завжди</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="673"/>
        <source>Never</source>
        <translation>Ніколи</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="696"/>
        <source>Switch source / PDF</source>
        <translation>Перемкнути джерело / PDF</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="698"/>
        <source>Open files…</source>
        <translation>Відкриті файли…</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="705"/>
        <source>&amp;Console</source>
        <translation>&amp;Консоль</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="709"/>
        <source>The evaluator console: a window of its own for trying code and functions</source>
        <translation>Консоль обчислювача: окреме вікно для проб коду й функцій</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="723"/>
        <source>Source and PDF side by side</source>
        <translation>Джерело й PDF поруч</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="726"/>
        <source>PDF as a tab</source>
        <translation>PDF окремою вкладкою</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="746"/>
        <source>Edit AI context of the project</source>
        <translation>Редагувати контекст AI проєкту</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="750"/>
        <source>Help at the cursor</source>
        <translation>Довідка за місцем курсора</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="751"/>
        <source>Language specification</source>
        <translation>Специфікація мови</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="752"/>
        <source>Standard library</source>
        <translation>Стандартна бібліотека</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="753"/>
        <source>Command cheat sheet (PDF)</source>
        <translation>Шпаргалка команд (PDF)</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="754"/>
        <source>Author guide (PDF)</source>
        <translation>Посібник автора (PDF)</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1124"/>
        <source>A name in PATH or a path. The tool is run read-only: see its description in agents.json.</source>
        <translation>Ім'я в PATH або шлях. Інструмент запускається лише для читання: див. його опис в agents.json.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1134"/>
        <source>found: %1</source>
        <translation>знайдено: %1</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1141"/>
        <source>%1:</source>
        <translation>%1:</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2454"/>
        <source>Local skill primula-docs (the agent loads it; to compare with the reference)</source>
        <translation>Локальний skill primula-docs (агент завантажує його сам; для порівняння із довідником)</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2584"/>
        <source>AI tools (programs: File → Settings):</source>
        <translation>Інструменти AI (програми: Файл → Налаштування):</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2586"/>
        <source>AI receives the text in read-only mode; it cannot change project files.</source>
        <translation>AI отримує текст лише для читання; він не може змінювати файли проєкту.</translation>
    </message>
    <message numerus="yes">
        <location filename="../src/MainWindow.cpp" line="2601"/>
        <source>The request, with the text of the document and the context of the project, will be sent to %n service(s): %1.

Send it?</source>
        <translation>
            <numerusform>Запит із текстом документа й контекстом проєкту буде надіслано до сервісів: %n (%1).

Надіслати?</numerusform>
            <numerusform>Запит із текстом документа й контекстом проєкту буде надіслано до сервісів: %n (%1).

Надіслати?</numerusform>
            <numerusform>Запит із текстом документа й контекстом проєкту буде надіслано до сервісів: %n (%1).

Надіслати?</numerusform>
        </translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2682"/>
        <source>Waiting for the answers of %1…</source>
        <translation>Очікування відповідей: %1…</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2709"/>
        <source>Received %1 of %2. Waiting for: %3…</source>
        <translation>Отримано %1 з %2. Очікується: %3…</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2762"/>
        <source>no answer</source>
        <translation>відповіді немає</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2776"/>
        <source>Some tools gave no answer:

%1</source>
        <translation>Деякі інструменти не дали відповіді:

%1</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3329"/>
        <source>Author guide</source>
        <translation>Посібник автора</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3330"/>
        <source>The PDF of the author guide is not found. It is part of the installation package (guide/&lt;language&gt;/) and of the source tree (docs/author/&lt;language&gt;/).

Looked in:
%1</source>
        <translation>PDF посібника автора не знайдено. Він входить до пакета встановлення (guide/&lt;мова&gt;/) і до дерева сирців (docs/author/&lt;мова&gt;/).

Шукали в:
%1</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="760"/>
        <source>Translator: not found</source>
        <translation>Транслятор: не знайдено</translation>
    </message>
    <message>
        <source>Insert command bar |</source>
        <translation>Вставити керівний символ |</translation>
    </message>
    <message>
        <source>Insert the command bar | at the cursor in any layout (Ctrl+\ or Alt+\)</source>
        <translation>Вставити керівний символ | у позицію курсора в будь-якій розкладці (Ctrl+\ або Alt+\)</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="807"/>
        <source>Switch layout</source>
        <translation>Перемкнути розкладку</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="811"/>
        <source>Switch between source and PDF side by side and PDF as a tab</source>
        <translation>Перемкнути: джерело й PDF поруч або PDF окремою вкладкою</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="855"/>
        <source>Cannot read the project of %1.</source>
        <translation>Не вдається прочитати проєкт %1.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="888"/>
        <source>Opened: %1</source>
        <translation>Відкрито: %1</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="950"/>
        <source>Some files have unsaved changes.</source>
        <translation>Деякі файли мають незбережені зміни.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="988"/>
        <source>Cannot save the workspace: %1</source>
        <translation>Не вдається зберегти робоче місце: %1</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1040"/>
        <source>The file is unavailable: %1
The saved path has been kept. Check the file or mount, then open it again.</source>
        <translation>Файл недоступний: %1
Збережений шлях залишено. Перевірте файл або монтування й відкрийте його знову.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1078"/>
        <source>Open project or document</source>
        <translation>Відкрити проєкт або документ</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1080"/>
        <source>Primula projects and documents (*.prml);;All files (*)</source>
        <translation>Проєкти й документи Primula (*.prml);;Усі файли (*)</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1087"/>
        <source>Open file</source>
        <translation>Відкрити файл</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1089"/>
        <source>Text files (*.prml *.yaml *.yml *.csv *.json *.md *.txt);;PDF (*.pdf);;All files (*)</source>
        <translation>Текстові файли (*.prml *.yaml *.yml *.csv *.json *.md *.txt);;PDF (*.pdf);;Усі файли (*)</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1102"/>
        <source>Settings</source>
        <translation>Налаштування</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1105"/>
        <location filename="../src/MainWindow.cpp" line="1134"/>
        <source>not found</source>
        <translation>не знайдено</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1106"/>
        <source>Empty: &apos;primula&apos; from PATH, or the launcher of the source tree.</source>
        <translation>Порожньо — &apos;primula&apos; з PATH або запускач із дерева вихідних файлів.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1107"/>
        <source>Browse…</source>
        <translation>Огляд…</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1115"/>
        <source>Primula translator:</source>
        <translation>Транслятор Primula:</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1158"/>
        <source>Translator version:</source>
        <translation>Версія транслятора:</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1184"/>
        <location filename="../src/MainWindow.cpp" line="1224"/>
        <source>Cannot create the AI context</source>
        <translation>Не вдається створити контекст AI</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1235"/>
        <source>The Primula translator is not found: Check and Build are unavailable. Install &apos;primula&apos; into PATH or set its path in File → Settings.</source>
        <translation>Транслятор Primula не знайдено: перевірка й збирання недоступні. Установіть &apos;primula&apos; у PATH або вкажіть шлях у Файл → Налаштування.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1315"/>
        <location filename="../src/MainWindow.cpp" line="3609"/>
        <location filename="../src/MainWindow.cpp" line="3614"/>
        <source>Cannot open file</source>
        <translation>Не вдається відкрити файл</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1351"/>
        <source>Save changes to %1?</source>
        <translation>Зберегти зміни в %1?</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1383"/>
        <source>Cannot save file</source>
        <translation>Не вдається зберегти файл</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1451"/>
        <source>PDF</source>
        <translation>PDF</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1571"/>
        <source>(do not change the status)</source>
        <translation>(не змінювати стан)</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1574"/>
        <source>Status to write (or type your own):</source>
        <translation>Стан, який записати (або введіть свій):</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1575"/>
        <source>Expected status:</source>
        <translation>Очікуваний стан:</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1588"/>
        <source>The document has no |parallel (or it is not inspected yet)</source>
        <translation>У документі немає |parallel (або його ще не перевірено)</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1594"/>
        <source>Track:</source>
        <translation>Потік:</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1600"/>
        <source>Confirm the translation of segment %1, track %2…</source>
        <translation>Підтвердити переклад сегмента %1, потік %2…</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1601"/>
        <source>Confirm the translation of this segment (put the cursor into a block of a translation)</source>
        <translation>Підтвердити переклад цього сегмента (поставте курсор у блок перекладу)</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1603"/>
        <source>Confirm the translation</source>
        <translation>Підтвердити переклад</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1611"/>
        <source>Confirm all blocks of a track…</source>
        <translation>Підтвердити всі блоки потоку…</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1612"/>
        <source>Confirm all blocks of a track</source>
        <translation>Підтвердити всі блоки потоку</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1614"/>
        <source>Confirm all blocks of %1</source>
        <translation>Підтвердити всі блоки %1</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1620"/>
        <source>Write blank blocks of a track…</source>
        <translation>Дописати заготовки блоків потоку…</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1621"/>
        <source>Write blank blocks</source>
        <translation>Дописати заготовки</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1625"/>
        <source>Check the status of the translations…</source>
        <translation>Перевірити стан перекладів…</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1626"/>
        <source>Check the status of the translations</source>
        <translation>Перевірити стан перекладів</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1702"/>
        <source>The saved file is read; unsaved changes of the header are not taken into account.</source>
        <translation>Читається збережений файл; незбережені зміни заголовка не враховано.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1706"/>
        <source>Document parameters</source>
        <translation>Параметри документа</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1707"/>
        <source>The translator did not report the parameters of the document.
%1</source>
        <translation>Транслятор не повідомив параметрів документа.
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
        <translation>проєкт</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1742"/>
        <source>document</source>
        <translation>документ</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1817"/>
        <source>Console: the standard library</source>
        <translation>Консоль: стандартна бібліотека</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1825"/>
        <source>Console: the project %1</source>
        <translation>Консоль: проєкт %1</translation>
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
        <translation>Організація</translation>
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
        <translation>&amp;Резервні копії</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="581"/>
        <source>Back up the project &amp;now</source>
        <translation>Зробити копію проєкту &amp;зараз</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="583"/>
        <source>&amp;Show backups…</source>
        <translation>&amp;Показати копії…</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="585"/>
        <source>Back up a file &amp;before saving it</source>
        <translation>Копіювати файл &amp;перед збереженням</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="588"/>
        <source>The version on the disk is kept in .primula-studio/backups before a save replaces it.</source>
        <translation>Версія на диску зберігається в .primula-studio/backups, перш ніж збереження її замінить.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1144"/>
        <source>More tools: %1</source>
        <translation>Інші інструменти: %1</translation>
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
        <translation>Контекст AI проєкту</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1198"/>
        <source>What AI should know about the documents: purpose, parties, terms, style of language. The text is added to every request.</source>
        <translation>Що AI має знати про документи: призначення, сторони, терміни, стиль мови. Текст додається до кожного запиту.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1216"/>
        <source>The file could not be saved: %1</source>
        <translation>Не вдалося зберегти файл: %1</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1944"/>
        <source>primula parallel completed</source>
        <translation>primula parallel завершено</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1944"/>
        <source>primula parallel found problems</source>
        <translation>primula parallel знайшла проблеми</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1959"/>
        <source>Check completed</source>
        <translation>Перевірку завершено</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1960"/>
        <source>Check found errors</source>
        <translation>Перевірка знайшла помилки</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2048"/>
        <source>Style %1 applied</source>
        <translation>Застосовано стиль %1</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2064"/>
        <source>Style removed</source>
        <translation>Стиль знято</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2064"/>
        <source>Style %1 removed</source>
        <translation>Стиль %1 знято</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2072"/>
        <source>No styles yet: the document has not been inspected.</source>
        <translation>Стилів поки немає: документ ще не перевірено.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2077"/>
        <source>Apply style</source>
        <translation>Застосувати стиль</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2079"/>
        <source>Style name</source>
        <translation>Ім’я стилю</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2083"/>
        <source>paragraph</source>
        <translation>абзацний</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2084"/>
        <source>character</source>
        <translation>символьний</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2085"/>
        <source>block</source>
        <translation>блоковий</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2155"/>
        <source>&amp;Function</source>
        <translation>&amp;Функція</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2172"/>
        <source>The catalogue of constructs is not available</source>
        <translation>Довідник конструкцій недоступний</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2175"/>
        <source>&amp;Header: add missing fields</source>
        <translation>&amp;Заголовок: додати відсутні поля</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2177"/>
        <source>&amp;Image…</source>
        <translation>&amp;Зображення…</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2218"/>
        <location filename="../src/MainWindow.cpp" line="2223"/>
        <location filename="../src/MainWindow.cpp" line="2234"/>
        <source>Insert image</source>
        <translation>Вставити зображення</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2219"/>
        <source>Images (*.png *.jpg *.jpeg *.svg *.gif *.bmp *.tif *.tiff);;All files (*)</source>
        <translation>Зображення (*.png *.jpg *.jpeg *.svg *.gif *.bmp *.tif *.tiff);;Усі файли (*)</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2224"/>
        <source>The image is outside the project. Copy it into %1?</source>
        <translation>Зображення поза проєктом. Скопіювати його до %1?</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2234"/>
        <source>Cannot copy the image to %1.</source>
        <translation>Не вдалося скопіювати зображення до %1.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2275"/>
        <source>%1 — no PDF yet (Build: F9)</source>
        <translation>%1 — PDF ще немає (зібрати: F9)</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2411"/>
        <source>Reload changed file</source>
        <translation>Перечитати змінений файл</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2412"/>
        <source>Reload %1 and discard its unsaved editor changes?</source>
        <translation>Перечитати %1, відкинувши незбережені зміни редактора?</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2417"/>
        <source>Cannot reload file</source>
        <translation>Не вдалося перечитати файл</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2451"/>
        <source>Reference: constructs and functions</source>
        <translation>Довідник: конструкції та функції</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2452"/>
        <source>Whole specification and library (about 100k tokens)</source>
        <translation>Уся специфікація та бібліотека (близько 100 тис. токенів)</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2453"/>
        <source>None</source>
        <translation>Нічого</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2455"/>
        <source>What AI receives about the Primula language. The reference is the catalogue of the translator: every construct and function with its summary and section. With the skill the agent loads its own installed skill primula-docs (skills/README.md tells how to install it); it should write «Skill: loaded» on the first line, else the skill is not available to it.</source>
        <translation>Що AI отримує про мову Primula. Довідник — каталог транслятора: кожна конструкція й функція з коротким описом і розділом. Зі skill агент завантажує власний встановлений skill primula-docs (як його встановити — у skills/README.md); у першому рядку відповіді він має написати «Skill: loaded», інакше skill йому недоступний.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2462"/>
        <source>e.g. 6.8, 10.5, stdlib:3</source>
        <translation>напр. 6.8, 10.5, stdlib:3</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2463"/>
        <source>Sections of the specification (and of the standard library with &apos;stdlib:&apos;) sent in full; the section of the construct at the cursor is proposed.</source>
        <translation>Розділи специфікації (і стандартної бібліотеки з «stdlib:»), що надсилаються повністю; пропонується розділ конструкції під курсором.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2469"/>
        <source>Include the messages of the last check or build (%1)</source>
        <translation>Додати повідомлення останньої перевірки чи збирання (%1)</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2471"/>
        <source>Include the messages of the last check or build (none)</source>
        <translation>Додати повідомлення останньої перевірки чи збирання (немає)</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2475"/>
        <source>Include the project file</source>
        <translation>Додати файл проєкту</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2478"/>
        <source>Writing rules of Primula (from the skill: what not to change, frequent mistakes)</source>
        <translation>Правила запису Primula (зі skill: що не можна змінювати, часті помилки)</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2480"/>
        <source>About 6 thousand characters from the skill primula-docs built into Studio; not sent with the skill level.</source>
        <translation>Близько 6 тисяч знаків зі skill primula-docs, вбудованого в Studio; не надсилаються з рівнем «skill».</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2482"/>
        <source>Ask for edits that can be checked and applied (tab «Edits» of the answer)</source>
        <translation>Просити правки, які можна перевірити й застосувати (вкладка «Правки» відповіді)</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2484"/>
        <source>AI answers with blocks «was → now». Studio finds them in the document, checks the result with the translator and applies the chosen ones as one step of Undo.</source>
        <translation>AI відповідає блоками «було → стало». Studio знаходить їх у документі, перевіряє результат транслятором і застосовує позначені одним кроком Undo.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2501"/>
        <source>%1 (not found)</source>
        <translation>%1 (не знайдено)</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2506"/>
        <source>The request goes to this tool. With several tools, every one answers in its own tab.</source>
        <translation>Запит іде до цього інструмента. З кількома інструментами кожен відповідає у своїй вкладці.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2507"/>
        <source>The program «%1» is not found: set it in File → Settings.</source>
        <translation>Програму «%1» не знайдено: вкажіть її в Файл → Налаштування.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2522"/>
        <location filename="../src/MainWindow.cpp" line="2600"/>
        <source>Ask AI</source>
        <translation>Запит до AI</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2522"/>
        <source>Choose at least one AI tool.</source>
        <translation>Виберіть хоча б один інструмент AI.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2533"/>
        <source>(own task)</source>
        <translation>(власне завдання)</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2535"/>
        <source>A ready task; you can edit its text. More recipes: %1</source>
        <translation>Готове завдання; його текст можна змінити. Інші рецепти: %1</translation>
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
        <translation>Редагувати контекст AI…</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2557"/>
        <source>What AI should know about the documents of the project (purpose, parties, terms, style); it is added to every request. The same file as AI → Edit AI context of the project.</source>
        <translation>Що AI має знати про документи проєкту (призначення, сторони, терміни, стиль); додається до кожного запиту. Той самий файл, що й AI → Редагувати контекст AI проєкту.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2562"/>
        <source>The AI context of the project is empty: nothing about the project is sent.</source>
        <translation>Контекст AI проєкту порожній: нічого про проєкт не надсилається.</translation>
    </message>
    <message numerus="yes">
        <location filename="../src/MainWindow.cpp" line="2563"/>
        <source>The AI context of the project is included (%n character(s)).</source>
        <translation>
            <numerusform>Контекст AI проєкту додається (знаків: %n).</numerusform>
            <numerusform>Контекст AI проєкту додається (знаків: %n).</numerusform>
            <numerusform>Контекст AI проєкту додається (знаків: %n).</numerusform>
        </translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2575"/>
        <source>Primula language:</source>
        <translation>Мова Primula:</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2576"/>
        <source>Sections in full:</source>
        <translation>Розділи повністю:</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2788"/>
        <location filename="../src/MainWindow.cpp" line="2976"/>
        <source>No project is open.</source>
        <translation>Проєкт не відкрито.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2824"/>
        <location filename="../src/MainWindow.cpp" line="2828"/>
        <source>Backups</source>
        <translation>Резервні копії</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2824"/>
        <source>The project has no source files to back up.</source>
        <translation>У проєкті немає вихідних файлів для копіювання.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2828"/>
        <source>The backup could not be made:
%1</source>
        <translation>Не вдалося створити копію:
%1</translation>
    </message>
    <message numerus="yes">
        <location filename="../src/MainWindow.cpp" line="2831"/>
        <source>Backed up %n file(s) of the project.</source>
        <translation>
            <numerusform>Скопійовано файлів проєкту: %n.</numerusform>
            <numerusform>Скопійовано файлів проєкту: %n.</numerusform>
            <numerusform>Скопійовано файлів проєкту: %n.</numerusform>
        </translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2858"/>
        <location filename="../src/MainWindow.cpp" line="2868"/>
        <location filename="../src/MainWindow.cpp" line="2872"/>
        <source>Compare with the backup</source>
        <translation>Порівняння з копією</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2858"/>
        <source>The file does not exist now: %1</source>
        <translation>Файла зараз немає: %1</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2865"/>
        <source>backup %1: %2</source>
        <translation>копія %1: %2</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2866"/>
        <source>current: %1</source>
        <translation>поточний: %1</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2868"/>
        <source>The comparison could not be made: %1</source>
        <translation>Не вдалося порівняти: %1</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2872"/>
        <source>The file is the same as in the backup.</source>
        <translation>Файл такий самий, як у копії.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2876"/>
        <source>Backup and the current file</source>
        <translation>Копія й поточний файл</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2887"/>
        <source>«-» is the backup, «+» is the current file.</source>
        <translation>«-» — копія, «+» — поточний файл.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2897"/>
        <location filename="../src/MainWindow.cpp" line="2901"/>
        <location filename="../src/MainWindow.cpp" line="2907"/>
        <location filename="../src/MainWindow.cpp" line="2923"/>
        <source>Restore</source>
        <translation>Відновлення</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2897"/>
        <source>The copy is missing or unreadable: %1</source>
        <translation>Копії немає або її не можна прочитати: %1</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2902"/>
        <source>Restore %1 as it was at %2?

The current state is backed up first.</source>
        <translation>Відновити %1 у вигляді на %2?

Поточний стан спершу буде збережено в копії.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2907"/>
        <source>A backup of the current file could not be made:
%1

Restore anyway?</source>
        <translation>Не вдалося зробити копію поточного файлу:
%1

Все одно відновити?</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2917"/>
        <source>Restored in the editor: %1 (not saved; Undo takes it back).</source>
        <translation>Відновлено в редакторі: %1 (не збережено; Undo поверне).</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2923"/>
        <source>The file could not be written: %1</source>
        <translation>Не вдалося записати файл: %1</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2926"/>
        <source>Restored: %1</source>
        <translation>Відновлено: %1</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2982"/>
        <source>There is no document to check this file in.</source>
        <translation>Немає документа, у якому можна перевірити цей файл.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="2998"/>
        <source>Cannot write a temporary file.</source>
        <translation>Не вдається записати тимчасовий файл.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3008"/>
        <source>The translator gave no result (exit code %1).</source>
        <translation>Транслятор не дав результату (код виходу %1).</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3024"/>
        <location filename="../src/MainWindow.cpp" line="3036"/>
        <location filename="../src/MainWindow.cpp" line="3045"/>
        <source>Apply edits</source>
        <translation>Застосування правок</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3024"/>
        <source>The file cannot be edited: %1</source>
        <translation>Файл не можна редагувати: %1</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3037"/>
        <source>None of the chosen edits can be applied now: the text of the document has changed.</source>
        <translation>Жодну з позначених правок зараз не можна застосувати: текст документа змінився.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3046"/>
        <source>A backup of the file could not be made:
%1

Apply the edits anyway?</source>
        <translation>Не вдалося зробити копію файлу:
%1

Все одно застосувати правки?</translation>
    </message>
    <message numerus="yes">
        <location filename="../src/MainWindow.cpp" line="3065"/>
        <source>Applied %n edit(s), %1 skipped; the file is not saved (Undo takes the edits back).</source>
        <translation>
            <numerusform>Застосовано правок: %n, пропущено: %1; файл не збережено (Undo поверне правки).</numerusform>
            <numerusform>Застосовано правок: %n, пропущено: %1; файл не збережено (Undo поверне правки).</numerusform>
            <numerusform>Застосовано правок: %n, пропущено: %1; файл не збережено (Undo поверне правки).</numerusform>
        </translation>
    </message>
    <message numerus="yes">
        <location filename="../src/MainWindow.cpp" line="3066"/>
        <source>Applied %n edit(s); the file is not saved (Undo takes the edits back).</source>
        <translation>
            <numerusform>Застосовано правок: %n; файл не збережено (Undo поверне правки).</numerusform>
            <numerusform>Застосовано правок: %n; файл не збережено (Undo поверне правки).</numerusform>
            <numerusform>Застосовано правок: %n; файл не збережено (Undo поверне правки).</numerusform>
        </translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3182"/>
        <source>No construct at the cursor: the quick help is open.</source>
        <translation>Під курсором немає конструкції: відкрито коротку довідку.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3191"/>
        <source>No construct here: there is no section to show.</source>
        <translation>Тут немає конструкції: показувати нема чого.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3206"/>
        <source>library section %1</source>
        <translation>розділ бібліотеки %1</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3206"/>
        <source>section %1</source>
        <translation>розділ %1</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3208"/>
        <source>Shown: %1 for “%2” (line %3, marked in the editor). The quick help is Help → Quick help.</source>
        <translation>Показано: %1 для «%2» (рядок %3, позначено в редакторі). Коротка довідка — Довідка → Коротка довідка.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3241"/>
        <source>Primula language specification</source>
        <translation>Специфікація мови Primula</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3258"/>
        <source>Primula standard library</source>
        <translation>Стандартна бібліотека Primula</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3281"/>
        <source>Command cheat sheet</source>
        <translation>Шпаргалка команд</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3281"/>
        <source>Cannot write %1.</source>
        <translation>Не вдалося записати %1.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3400"/>
        <source>Cannot create files</source>
        <translation>Не вдається створити файли</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3410"/>
        <source>Created: %1</source>
        <translation>Створено: %1</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3417"/>
        <source>Order project created</source>
        <translation>Проєкт замовлення створено</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3418"/>
        <source>Open the order project %1 now? Its targets are built with Shift+F9.</source>
        <translation>Відкрити проєкт замовлення %1 зараз? Його цілі збираються через Shift+F9.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3435"/>
        <source>New in this folder</source>
        <translation>Створити в цій теці</translation>
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
        <translation>Модуль визначень…</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3439"/>
        <source>Styles module…</source>
        <translation>Модуль стилів…</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3441"/>
        <source>Folder…</source>
        <translation>Теку…</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3445"/>
        <source>Open</source>
        <translation>Відкрити</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3458"/>
        <source>Open in an external application</source>
        <translation>Відкрити у зовнішній програмі</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3462"/>
        <source>Copy under a new name…</source>
        <translation>Копіювати під новою назвою…</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3463"/>
        <source>Rename…</source>
        <translation>Перейменувати…</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3464"/>
        <location filename="../src/MainWindow.cpp" line="3846"/>
        <source>Move to trash</source>
        <translation>Перемістити в смітник</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3467"/>
        <source>Open the folder in the file manager</source>
        <translation>Відкрити теку у файловому менеджері</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3626"/>
        <source>New folder</source>
        <translation>Нова тека</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3626"/>
        <source>Name of the folder:</source>
        <translation>Назва теки:</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3631"/>
        <source>Cannot create the folder</source>
        <translation>Не вдається створити теку</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3651"/>
        <location filename="../src/MainWindow.cpp" line="3773"/>
        <source>The name is empty, contains / or is taken: %1</source>
        <translation>Назва порожня, містить / або вже зайнята: %1</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3656"/>
        <location filename="../src/MainWindow.cpp" line="3673"/>
        <source>Cannot copy %1 to %2</source>
        <translation>Не вдається скопіювати %1 у %2</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3595"/>
        <location filename="../src/MainWindow.cpp" line="3664"/>
        <source>Cannot create %1</source>
        <translation>Не вдається створити %1</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3727"/>
        <source>Copy under a new name</source>
        <translation>Копіювати під новою назвою</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3728"/>
        <source>New name of the copy of %1:</source>
        <translation>Нова назва копії %1:</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3734"/>
        <source>Cannot copy</source>
        <translation>Не вдається скопіювати</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3747"/>
        <source>Replace the old name</source>
        <translation>Замінити стару назву</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3748"/>
        <source>Replace «%1» with «%2» in the files of the copy?</source>
        <translation>Замінити «%1» на «%2» у файлах копії?</translation>
    </message>
    <message numerus="yes">
        <location filename="../src/MainWindow.cpp" line="3751"/>
        <source>%n file(s) contain the old name; see the details.</source>
        <translation>
            <numerusform>%n файл містить стару назву; див. подробиці.</numerusform>
            <numerusform>%n файли містять стару назву; див. подробиці.</numerusform>
            <numerusform>%n файлів містять стару назву; див. подробиці.</numerusform>
        </translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3753"/>
        <source>Cannot replace</source>
        <translation>Не вдається замінити</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3758"/>
        <source>Copied: %1</source>
        <translation>Скопійовано: %1</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3768"/>
        <location filename="../src/MainWindow.cpp" line="3816"/>
        <source>Save or close %1 first.</source>
        <translation>Спершу збережіть або закрийте %1.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3793"/>
        <source>Cannot rename %1 to %2</source>
        <translation>Не вдається перейменувати %1 на %2</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3802"/>
        <source>Rename</source>
        <translation>Перейменувати</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3802"/>
        <source>New name of %1:</source>
        <translation>Нова назва %1:</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3808"/>
        <source>Cannot rename</source>
        <translation>Не вдається перейменувати</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3828"/>
        <source>Cannot move %1 to the trash.</source>
        <translation>Не вдається перемістити %1 у смітник.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3828"/>
        <source>Cannot delete %1.</source>
        <translation>Не вдається видалити %1.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3846"/>
        <source>Move %1 to the trash?</source>
        <translation>Перемістити %1 у смітник?</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3854"/>
        <location filename="../src/MainWindow.cpp" line="3858"/>
        <source>Cannot move to trash</source>
        <translation>Не вдається перемістити в смітник</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3859"/>
        <source>%1
Delete %2 permanently? This cannot be undone.</source>
        <translation>%1
Видалити %2 остаточно? Це не можна скасувати.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3862"/>
        <source>Cannot delete</source>
        <translation>Не вдається видалити</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="758"/>
        <source>Primula Studio %1
An editor and build interface for Primula documents.</source>
        <translation>Primula Studio %1
Редактор та інтерфейс збирання документів Primula.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="603"/>
        <source>&amp;Edit</source>
        <translation>&amp;Редагування</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="240"/>
        <source>Checking…</source>
        <translation>Перевірка…</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="319"/>
        <source>Close</source>
        <translation>Закрити</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="320"/>
        <source>Close other tabs</source>
        <translation>Закрити інші вкладки</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="321"/>
        <source>Copy path</source>
        <translation>Копіювати шлях</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="400"/>
        <source>Files</source>
        <translation>Файли</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="514"/>
        <source>Double-click a message to open its source location.</source>
        <translation>Подвійне клацання по повідомленню відкриває місце в джерелі.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="570"/>
        <source>&amp;Open project or document…</source>
        <translation>&amp;Відкрити проєкт або документ…</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="572"/>
        <source>Open &amp;file…</source>
        <translation>Відкрити &amp;файл…</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="576"/>
        <source>&amp;Save</source>
        <translation>&amp;Зберегти</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="578"/>
        <source>Save a&amp;ll</source>
        <translation>Зберегти &amp;все</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="592"/>
        <source>&amp;Close tab</source>
        <translation>&amp;Закрити вкладку</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="594"/>
        <source>Close &amp;other tabs</source>
        <translation>Закрити &amp;інші вкладки</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="596"/>
        <source>Close &amp;project</source>
        <translation>Закрити &amp;проєкт</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="598"/>
        <source>Se&amp;ttings…</source>
        <translation>&amp;Налаштування…</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="611"/>
        <source>&amp;Find…</source>
        <translation>&amp;Знайти…</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="613"/>
        <source>Find &amp;next</source>
        <translation>Знайти &amp;далі</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="615"/>
        <source>Find &amp;previous</source>
        <translation>Знайти &amp;попереднє</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="617"/>
        <source>&amp;Replace…</source>
        <translation>За&amp;мінити…</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3600"/>
        <source>Created %1 from the template: edit it and save</source>
        <translation>Створено %1 із шаблону: змініть і збережіть</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="599"/>
        <source>File &amp;types…</source>
        <translation>&amp;Типи файлів…</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3595"/>
        <source>File types</source>
        <translation>Типи файлів</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1393"/>
        <source>File types applied</source>
        <translation>Типи файлів застосовано</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1394"/>
        <source>File types applied with problems (see the Log)</source>
        <translation>Типи файлів застосовано з проблемами (див. «Журнал»)</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3584"/>
        <source>File types: %1</source>
        <translation>Типи файлів: %1</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3453"/>
        <source>Open as text in the editor</source>
        <translation>Відкрити як текст у редакторі</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3449"/>
        <source>Open with %1</source>
        <translation>Відкрити за допомогою %1</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3619"/>
        <source>Opened with %1: %2</source>
        <translation>Відкрито за допомогою %1: %2</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3615"/>
        <source>The command of the file type %1 did not start:
%2

Check it in %3 (File → File types…).</source>
        <translation>Команда типу файлів %1 не запустилася:
%2

Перевірте її в %3 (Файл → Типи файлів…).</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3609"/>
        <source>The file type %1 has no command.</source>
        <translation>Тип файлів %1 не має команди.</translation>
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
        <translation>Інший &amp;формат…</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="654"/>
        <source>E&amp;xport</source>
        <translation>Е&amp;кспорт</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="324"/>
        <location filename="../src/MainWindow.cpp" line="1914"/>
        <location filename="../src/MainWindow.cpp" line="1926"/>
        <location filename="../src/MainWindow.cpp" line="3455"/>
        <location filename="../src/MainWindow.cpp" line="3537"/>
        <location filename="../src/MainWindow.cpp" line="3551"/>
        <source>Export</source>
        <translation>Експорт</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3542"/>
        <source>Export &amp;as…</source>
        <translation>Експортувати &amp;як…</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3544"/>
        <location filename="../src/MainWindow.cpp" line="3565"/>
        <source>Export as</source>
        <translation>Експортувати як</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1934"/>
        <source>Export failed</source>
        <translation>Експорт не вдався</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1925"/>
        <source>Export needs pandoc</source>
        <translation>Для експорту потрібен pandoc</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1927"/>
        <source>Export to this format needs pandoc, and it is not found.

Install pandoc (https://pandoc.org; openSUSE: zypper install pandoc; Debian: apt install pandoc) and export again. The format JSON (the pandoc AST) needs no pandoc.</source>
        <translation>Для експорту в цей формат потрібен pandoc, а його не знайдено.

Встановіть pandoc (https://pandoc.org; openSUSE: zypper install pandoc; Debian: apt install pandoc) і повторіть експорт. Для формату JSON (AST pandoc) pandoc не потрібен.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3552"/>
        <source>Export writes the evaluated document through pandoc: numbers of clauses, references, footnotes, tables and captions are kept; page layout (headers, footers, columns, page numbers) is not. Paragraph and character styles go to DOCX by name. Markdown, HTML, DOCX and other formats need pandoc (https://pandoc.org); JSON is the pandoc AST itself.</source>
        <translation>Експорт записує обчислений документ через pandoc: номери пунктів, посилання, виноски, таблиці й підписи зберігаються, розмітка сторінок (колонтитули, колонки, номери сторінок) — ні. Стилі абзаців і символів переходять у DOCX за іменами. Для Markdown, HTML, DOCX та інших форматів потрібен pandoc (https://pandoc.org); JSON — це сам AST pandoc.</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1913"/>
        <source>Exported: %1</source>
        <translation>Експортовано: %1</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="239"/>
        <source>Exporting…</source>
        <translation>Експорт…</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3538"/>
        <source>Format (a writer of pandoc; json — the pandoc AST, no pandoc needed):</source>
        <translation>Формат (writer pandoc; json — AST pandoc, pandoc не потрібен):</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3544"/>
        <source>Format:</source>
        <translation>Формат:</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3521"/>
        <source>Open a document of the project to export it</source>
        <translation>Відкрийте документ проєкту, щоб його експортувати</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1917"/>
        <source>Open the file</source>
        <translation>Відкрити файл</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1918"/>
        <source>Open the folder</source>
        <translation>Відкрити каталог</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="1914"/>
        <source>The document is exported to
%1</source>
        <translation>Документ експортовано в
%1</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3550"/>
        <source>What is exported…</source>
        <translation>Що експортується…</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="327"/>
        <location filename="../src/MainWindow.cpp" line="3457"/>
        <source>File summary…</source>
        <translation>Зведення про файл…</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3478"/>
        <source>File summary</source>
        <translation>Зведення про файл</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3483"/>
        <source>File summary — %1</source>
        <translation>Зведення про файл — %1</translation>
    </message>
    <message>
        <location filename="../src/MainWindow.cpp" line="3479"/>
        <source>The translator could not describe %1:
%2</source>
        <translation>Транслятор не зміг описати %1:
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
        <translation>Модуль визначень</translation>
    </message>
    <message>
        <location filename="../src/NewFileDialog.cpp" line="32"/>
        <source>Styles module</source>
        <translation>Модуль стилів</translation>
    </message>
    <message>
        <location filename="../src/NewFileDialog.cpp" line="33"/>
        <source>Project</source>
        <translation>Проєкт</translation>
    </message>
    <message>
        <location filename="../src/NewFileDialog.cpp" line="34"/>
        <source>Order project (extends)</source>
        <translation>Проєкт замовлення (extends)</translation>
    </message>
    <message>
        <location filename="../src/NewFileDialog.cpp" line="43"/>
        <source>New</source>
        <translation>Створити</translation>
    </message>
    <message>
        <location filename="../src/NewFileDialog.cpp" line="64"/>
        <source>the name, when empty</source>
        <translation>назва, якщо порожньо</translation>
    </message>
    <message>
        <location filename="../src/NewFileDialog.cpp" line="72"/>
        <source>Browse…</source>
        <translation>Огляд…</translation>
    </message>
    <message>
        <location filename="../src/NewFileDialog.cpp" line="74"/>
        <source>Place</source>
        <translation>Місце</translation>
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
        <translation>Назва:</translation>
    </message>
    <message>
        <location filename="../src/NewFileDialog.cpp" line="88"/>
        <source>Title:</source>
        <translation>Заголовок:</translation>
    </message>
    <message>
        <location filename="../src/NewFileDialog.cpp" line="89"/>
        <source>Language of the texts:</source>
        <translation>Мова текстів:</translation>
    </message>
    <message>
        <location filename="../src/NewFileDialog.cpp" line="93"/>
        <source>Place:</source>
        <translation>Місце:</translation>
    </message>
    <message>
        <location filename="../src/NewFileDialog.cpp" line="94"/>
        <source>Files to create:</source>
        <translation>Буде створено:</translation>
    </message>
    <message>
        <location filename="../src/NewFileDialog.cpp" line="97"/>
        <source>Create</source>
        <translation>Створити</translation>
    </message>
    <message>
        <location filename="../src/NewFileDialog.cpp" line="124"/>
        <source> (user)</source>
        <translation> (користувача)</translation>
    </message>
    <message>
        <location filename="../src/NewFileDialog.cpp" line="196"/>
        <location filename="../src/NewFileDialog.cpp" line="201"/>
        <source>No templates of this kind.</source>
        <translation>Шаблонів цього виду немає.</translation>
    </message>
    <message>
        <location filename="../src/NewFileDialog.cpp" line="203"/>
        <source>Enter a name.</source>
        <translation>Введіть назву.</translation>
    </message>
    <message>
        <location filename="../src/NewFileDialog.cpp" line="205"/>
        <source>The name must not contain / \ : * ? &quot; &lt; &gt; | or start with a dot.</source>
        <translation>Назва не може містити / \ : * ? &quot; &lt; &gt; | або починатися з крапки.</translation>
    </message>
    <message>
        <location filename="../src/NewFileDialog.cpp" line="207"/>
        <source>Choose the place.</source>
        <translation>Виберіть місце.</translation>
    </message>
    <message>
        <location filename="../src/NewFileDialog.cpp" line="216"/>
        <source>Some files already exist; choose another name or place.</source>
        <translation>Деякі файли вже існують — виберіть іншу назву чи місце.</translation>
    </message>
</context>
<context>
    <name>PalettePanel</name>
    <message>
        <location filename="../src/PalettePanel.cpp" line="29"/>
        <source>Search constructs and functions</source>
        <translation>Пошук конструкцій і функцій</translation>
    </message>
    <message>
        <location filename="../src/PalettePanel.cpp" line="33"/>
        <source>Construct</source>
        <translation>Конструкція</translation>
    </message>
    <message>
        <location filename="../src/PalettePanel.cpp" line="33"/>
        <source>Description</source>
        <translation>Опис</translation>
    </message>
    <message>
        <location filename="../src/PalettePanel.cpp" line="66"/>
        <source>Insert at the cursor</source>
        <translation>Вставити біля курсора</translation>
    </message>
    <message>
        <location filename="../src/PalettePanel.cpp" line="68"/>
        <source>Copy the form %1</source>
        <translation>Копіювати форму %1</translation>
    </message>
    <message>
        <location filename="../src/PalettePanel.cpp" line="68"/>
        <source>Copy the name %1</source>
        <translation>Копіювати ім&apos;я %1</translation>
    </message>
    <message>
        <location filename="../src/PalettePanel.cpp" line="70"/>
        <source>Copy the template</source>
        <translation>Копіювати заготовку</translation>
    </message>
    <message>
        <location filename="../src/PalettePanel.cpp" line="74"/>
        <source>Specification section</source>
        <translation>Розділ специфікації</translation>
    </message>
    <message>
        <location filename="../src/PalettePanel.cpp" line="102"/>
        <source>Functions: %1</source>
        <translation>Функції: %1</translation>
    </message>
</context>
<context>
    <name>QObject</name>
    <message>
        <location filename="../src/AiHistory.cpp" line="50"/>
        <source>Task</source>
        <translation>Завдання</translation>
    </message>
    <message>
        <location filename="../src/AiHistory.cpp" line="51"/>
        <source>Response</source>
        <translation>Відповідь</translation>
    </message>
    <message>
        <location filename="../src/AiHistory.cpp" line="52"/>
        <source>Complete request</source>
        <translation>Повний запит</translation>
    </message>
    <message>
        <location filename="../src/AiHistory.cpp" line="61"/>
        <source>Cannot save AI exchange: %1</source>
        <translation>Не вдалося зберегти діалог AI: %1</translation>
    </message>
    <message>
        <location filename="../src/AiHistory.cpp" line="75"/>
        <location filename="../src/AiHistory.cpp" line="84"/>
        <source>Cannot create AI history file: %1</source>
        <translation>Не вдалося створити файл історії AI: %1</translation>
    </message>
    <message>
        <location filename="../src/AiHistory.cpp" line="92"/>
        <source>Cannot choose an unused AI history filename.</source>
        <translation>Не вдалося підібрати вільну назву файла історії AI.</translation>
    </message>
    <message>
        <location filename="../src/AiHistory.cpp" line="113"/>
        <source>Unrecognized AI history file: %1</source>
        <translation>Невідомий формат файла історії AI: %1</translation>
    </message>
    <message>
        <location filename="../src/AiHistory.cpp" line="137"/>
        <source>AI history sections are incomplete: %1</source>
        <translation>В історії AI бракує розділів: %1</translation>
    </message>
    <message>
        <location filename="../src/AiHistory.cpp" line="143"/>
        <source>AI history metadata is invalid: %1</source>
        <translation>Некоректні метадані історії AI: %1</translation>
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
        <translation>Було:</translation>
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
        <translation>Таблиця %1</translation>
    </message>
    <message>
        <location filename="../src/StructurePanel.cpp" line="56"/>
        <source>Figure %1</source>
        <translation>Рисунок %1</translation>
    </message>
    <message>
        <location filename="../src/StructurePanel.cpp" line="57"/>
        <source>Numbered list %1</source>
        <translation>Нумерований список %1</translation>
    </message>
    <message>
        <location filename="../src/StructurePanel.cpp" line="58"/>
        <source>Section %1</source>
        <translation>Секція %1</translation>
    </message>
    <message>
        <location filename="../src/StructurePanel.cpp" line="59"/>
        <source>Note %1</source>
        <translation>Примітка %1</translation>
    </message>
    <message>
        <location filename="../src/StructurePanel.cpp" line="61"/>
        <source>Parallel tracks: %1</source>
        <translation>Паралельні потоки: %1</translation>
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
        <translation>Потік %1</translation>
    </message>
    <message>
        <location filename="../src/StructurePanel.cpp" line="71"/>
        <source> — outdated</source>
        <translation> — застарів</translation>
    </message>
    <message>
        <location filename="../src/StructurePanel.cpp" line="72"/>
        <source> — changed after confirmation</source>
        <translation> — змінено після підтвердження</translation>
    </message>
    <message>
        <location filename="../src/StructurePanel.cpp" line="91"/>
        <source>Element</source>
        <translation>Елемент</translation>
    </message>
    <message>
        <location filename="../src/StructurePanel.cpp" line="91"/>
        <source>File</source>
        <translation>Файл</translation>
    </message>
    <message>
        <location filename="../src/StructurePanel.cpp" line="116"/>
        <source>Go to the line</source>
        <translation>Перейти до рядка</translation>
    </message>
    <message>
        <location filename="../src/StructurePanel.cpp" line="117"/>
        <source>Insert a reference (no ID)</source>
        <translation>Вставити посилання (немає ID)</translation>
    </message>
    <message>
        <location filename="../src/StructurePanel.cpp" line="117"/>
        <source>Insert the reference %1 at the cursor</source>
        <translation>Вставити посилання %1 біля курсора</translation>
    </message>
    <message>
        <location filename="../src/StructurePanel.cpp" line="120"/>
        <source>Copy the number</source>
        <translation>Копіювати номер</translation>
    </message>
    <message>
        <location filename="../src/StructurePanel.cpp" line="120"/>
        <source>Copy the number %1</source>
        <translation>Копіювати номер %1</translation>
    </message>
    <message>
        <location filename="../src/StructurePanel.cpp" line="122"/>
        <source>Copy a reference (no ID)</source>
        <translation>Копіювати посилання (немає ID)</translation>
    </message>
    <message>
        <location filename="../src/StructurePanel.cpp" line="122"/>
        <source>Copy the reference %1</source>
        <translation>Копіювати посилання %1</translation>
    </message>
    <message>
        <location filename="../src/StructurePanel.cpp" line="124"/>
        <source>Copy the ID</source>
        <translation>Копіювати ID</translation>
    </message>
    <message>
        <location filename="../src/StructurePanel.cpp" line="185"/>
        <source>Outdated: %1</source>
        <translation>Застаріло: %1</translation>
    </message>
</context>
<context>
    <name>StudioProject</name>
    <message>
        <location filename="../src/StudioProject.cpp" line="186"/>
        <location filename="../src/StudioProject.cpp" line="210"/>
        <source>Cannot create %1</source>
        <translation>Не вдається створити %1</translation>
    </message>
    <message>
        <location filename="../src/StudioProject.cpp" line="218"/>
        <source># AI context of the project

What the AI should know about these documents: purpose, parties, terms, style of language.
</source>
        <translation># Контекст AI проєкту

Що AI має знати про ці документи: призначення, сторони, терміни, стиль мови.
</translation>
    </message>
</context>
<context>
    <name>StyleEditing</name>
    <message>
        <location filename="../src/StyleEditing.cpp" line="294"/>
        <source>The arguments of the line %1 are not closed.</source>
        <translation>Аргументи в рядку %1 не закрито.</translation>
    </message>
    <message>
        <location filename="../src/StyleEditing.cpp" line="481"/>
        <source>The selection has only spaces.</source>
        <translation>У виділенні лише пробіли.</translation>
    </message>
    <message>
        <location filename="../src/StyleEditing.cpp" line="486"/>
        <source>A character style covers text of one paragraph; the selection crosses an empty line.</source>
        <translation>Символьний стиль діє в межах абзацу, а виділення перетинає порожній рядок.</translation>
    </message>
    <message>
        <location filename="../src/StyleEditing.cpp" line="490"/>
        <source>The selection cuts an inline form {…}; select whole forms.</source>
        <translation>Виділення розрізає рядкову форму {…}; виділіть форми повністю.</translation>
    </message>
    <message>
        <location filename="../src/StyleEditing.cpp" line="502"/>
        <source>Nothing to style: the line is empty.</source>
        <translation>Нічого оформлювати: рядок порожній.</translation>
    </message>
    <message>
        <location filename="../src/StyleEditing.cpp" line="580"/>
        <source>Style %1 has a computed or invalid name.</source>
        <translation>Стиль %1 має обчислюване або неприпустиме ім’я.</translation>
    </message>
    <message>
        <location filename="../src/StyleEditing.cpp" line="593"/>
        <source>A table, list, frame or page style is set by the style= argument of its command.</source>
        <translation>Стиль таблиці, списку, рамки чи сторінки задається аргументом style= його команди.</translation>
    </message>
    <message>
        <location filename="../src/StyleEditing.cpp" line="652"/>
        <source>The environment opened on line %1 has no closing line.</source>
        <translation>Оточення, відкрите в рядку %1, не має рядка закриття.</translation>
    </message>
    <message>
        <location filename="../src/StyleEditing.cpp" line="661"/>
        <source>No style is applied at the cursor.</source>
        <translation>Біля курсора немає застосованого стилю.</translation>
    </message>
    <message>
        <location filename="../src/StyleEditing.cpp" line="662"/>
        <source>Style %1 is not applied at the cursor.</source>
        <translation>Стиль %1 біля курсора не застосовано.</translation>
    </message>
</context>
<context>
    <name>StylesPanel</name>
    <message>
        <location filename="../src/StylesPanel.cpp" line="27"/>
        <source>Paragraph styles</source>
        <translation>Стилі абзаців</translation>
    </message>
    <message>
        <location filename="../src/StylesPanel.cpp" line="28"/>
        <source>Character styles</source>
        <translation>Стилі символів</translation>
    </message>
    <message>
        <location filename="../src/StylesPanel.cpp" line="29"/>
        <source>Table styles</source>
        <translation>Стилі таблиць</translation>
    </message>
    <message>
        <location filename="../src/StylesPanel.cpp" line="30"/>
        <source>List styles</source>
        <translation>Стилі списків</translation>
    </message>
    <message>
        <location filename="../src/StylesPanel.cpp" line="31"/>
        <source>Page styles</source>
        <translation>Стилі сторінок</translation>
    </message>
    <message>
        <location filename="../src/StylesPanel.cpp" line="32"/>
        <source>Block styles</source>
        <translation>Стилі блоків</translation>
    </message>
    <message>
        <location filename="../src/StylesPanel.cpp" line="39"/>
        <source>project</source>
        <translation>проєкт</translation>
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
        <translation>вбудований</translation>
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
        <translation>Фільтр стилів</translation>
    </message>
    <message>
        <location filename="../src/StylesPanel.cpp" line="84"/>
        <source>Style</source>
        <translation>Стиль</translation>
    </message>
    <message>
        <location filename="../src/StylesPanel.cpp" line="84"/>
        <source>Parent</source>
        <translation>Батьківський</translation>
    </message>
    <message>
        <location filename="../src/StylesPanel.cpp" line="89"/>
        <source>Property</source>
        <translation>Властивість</translation>
    </message>
    <message>
        <location filename="../src/StylesPanel.cpp" line="89"/>
        <source>Value</source>
        <translation>Значення</translation>
    </message>
    <message>
        <location filename="../src/StylesPanel.cpp" line="89"/>
        <location filename="../src/StylesPanel.cpp" line="284"/>
        <source>Set in</source>
        <translation>Де задано</translation>
    </message>
    <message>
        <location filename="../src/StylesPanel.cpp" line="125"/>
        <source>Apply %1 at the cursor</source>
        <translation>Застосувати %1 біля курсора</translation>
    </message>
    <message>
        <location filename="../src/StylesPanel.cpp" line="128"/>
        <source>Apply %1 (set by style= of its command)</source>
        <translation>Застосувати %1 (задається style= команди)</translation>
    </message>
    <message>
        <location filename="../src/StylesPanel.cpp" line="129"/>
        <source>Remove %1 at the cursor</source>
        <translation>Зняти %1 біля курсора</translation>
    </message>
    <message>
        <location filename="../src/StylesPanel.cpp" line="132"/>
        <source>Go to the definition</source>
        <translation>Перейти до визначення</translation>
    </message>
    <message>
        <location filename="../src/StylesPanel.cpp" line="134"/>
        <source>Select the parent style %1</source>
        <translation>Вибрати батьківський стиль %1</translation>
    </message>
    <message>
        <location filename="../src/StylesPanel.cpp" line="136"/>
        <source>Copy the name</source>
        <translation>Копіювати ім&apos;я</translation>
    </message>
    <message>
        <location filename="../src/StylesPanel.cpp" line="151"/>
        <source>Outdated: %1</source>
        <translation>Застаріло: %1</translation>
    </message>
    <message>
        <location filename="../src/StylesPanel.cpp" line="230"/>
        <source>broken: Build → Check document shows why</source>
        <translation>зламаний: причину покаже Збирання → Перевірити документ</translation>
    </message>
    <message>
        <location filename="../src/StylesPanel.cpp" line="335"/>
        <source>paragraph style</source>
        <translation>абзацний стиль</translation>
    </message>
    <message>
        <location filename="../src/StylesPanel.cpp" line="335"/>
        <source>character style</source>
        <translation>символьний стиль</translation>
    </message>
    <message>
        <location filename="../src/StylesPanel.cpp" line="179"/>
        <source>Layers</source>
        <translation>Шари</translation>
    </message>
    <message>
        <location filename="../src/StylesPanel.cpp" line="193"/>
        <source>Document defaults</source>
        <translation>Типові значення документа</translation>
    </message>
    <message>
        <location filename="../src/StylesPanel.cpp" line="220"/>
        <source>defined in %1, line %2</source>
        <translation>визначено в %1, рядок %2</translation>
    </message>
    <message>
        <location filename="../src/StylesPanel.cpp" line="226"/>
        <source>made by the translator (derive, variant)</source>
        <translation>створено транслятором (derive, варіант)</translation>
    </message>
    <message>
        <location filename="../src/StylesPanel.cpp" line="248"/>
        <source>Own</source>
        <translation>Власні</translation>
    </message>
    <message>
        <location filename="../src/StylesPanel.cpp" line="255"/>
        <source>translator</source>
        <translation>транслятор</translation>
    </message>
    <message>
        <location filename="../src/StylesPanel.cpp" line="261"/>
        <source>Inherited</source>
        <translation>Успадковані</translation>
    </message>
</context>
<context>
    <name>Templates</name>
    <message>
        <location filename="../src/Templates.cpp" line="135"/>
        <source>The file already exists: %1</source>
        <translation>Файл уже існує: %1</translation>
    </message>
    <message>
        <location filename="../src/Templates.cpp" line="144"/>
        <source>Cannot read the template file %1</source>
        <translation>Не вдається прочитати файл шаблону %1</translation>
    </message>
    <message>
        <location filename="../src/Templates.cpp" line="146"/>
        <source>Cannot create %1</source>
        <translation>Не вдається створити %1</translation>
    </message>
</context>
<context>
    <name>Translator</name>
    <message>
        <location filename="../src/Translator.cpp" line="37"/>
        <source>The Primula translator is not found: install &apos;primula&apos; into PATH or set its path in the settings.</source>
        <translation>Транслятор Primula не знайдено: установіть &apos;primula&apos; у PATH або вкажіть шлях у налаштуваннях.</translation>
    </message>
    <message>
        <location filename="../src/Translator.cpp" line="46"/>
        <source>Cannot start %1: %2</source>
        <translation>Не вдається запустити %1: %2</translation>
    </message>
    <message>
        <location filename="../src/Translator.cpp" line="54"/>
        <source>%1 did not finish in %2 s</source>
        <translation>%1 не завершився за %2 с</translation>
    </message>
    <message>
        <location filename="../src/Translator.cpp" line="86"/>
        <source>The translator gave no project description.</source>
        <translation>Транслятор не видав опису проєкту.</translation>
    </message>
    <message>
        <location filename="../src/Translator.cpp" line="104"/>
        <source>The translator gave no summary of the file.</source>
        <translation>Транслятор не видав зведення про файл.</translation>
    </message>
</context>
</TS>
