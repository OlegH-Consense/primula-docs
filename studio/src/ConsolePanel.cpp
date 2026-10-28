#include "ConsolePanel.h"

#include "CodeEditor.h"
#include "CommandCatalog.h"
#include "Translator.h"

#include <QAbstractItemView>
#include <QAction>
#include <QApplication>
#include <QClipboard>
#include <QComboBox>
#include <QCompleter>
#include <QDir>
#include <QFile>
#include <QFileInfo>
#include <QFontDatabase>
#include <QHBoxLayout>
#include <QJsonArray>
#include <QJsonDocument>
#include <QKeyEvent>
#include <QLabel>
#include <QLineEdit>
#include <QListWidget>
#include <QMenu>
#include <QProcess>
#include <QPushButton>
#include <QSaveFile>
#include <QScrollBar>
#include <QSettings>
#include <QSplitter>
#include <QTabWidget>
#include <QTextBrowser>
#include <QTreeWidget>
#include <QWheelEvent>
#include <QVBoxLayout>

#include <csignal>

namespace {

constexpr int HistoryLimit = 200;
constexpr int SectionRole = Qt::UserRole;
constexpr int ExampleRole = Qt::UserRole + 1;
constexpr int NameRole = Qt::UserRole + 2;

/// A console input is complete (as in the translator's terminal mode): a block (a line
/// ending with ':') ends with an empty line; otherwise no bracket is left open.
bool complete(const QString &text)
{
    const QString stripped = text.trimmed();
    for (const QString &line : text.split(QLatin1Char('\n')))
        if (line.trimmed().endsWith(QLatin1Char(':'))) return text.endsWith(QLatin1Char('\n'));
    int depth = 0;
    for (const QChar c : stripped) {
        if (c == QLatin1Char('(') || c == QLatin1Char('[') || c == QLatin1Char('{')) ++depth;
        else if (c == QLatin1Char(')') || c == QLatin1Char(']') || c == QLatin1Char('}')) --depth;
    }
    return depth <= 0;
}

} // namespace

ConsolePanel::ConsolePanel(QWidget *parent) : QWidget(parent, Qt::Window)
{
    setWindowTitle(tr("Console — Primula Studio"));
    setObjectName(QStringLiteral("consoleWindow"));
    auto *layout = new QVBoxLayout(this);
    layout->setContentsMargins(4, 4, 4, 4);
    auto *row = new QHBoxLayout;
    row->addWidget(new QLabel(tr("Context:"), this));
    m_context = new QComboBox(this);
    m_context->setObjectName(QStringLiteral("consoleContext"));
    m_context->addItem(tr("Current file"), QStringLiteral("file"));
    m_context->addItem(tr("Project"), QStringLiteral("project"));
    m_context->addItem(tr("Library only"), QStringLiteral("library"));
    m_context->setToolTip(tr("The names the console has: those of the current file (a document with its "
                             "parameters and code, a module, a styles module, the project file), of the "
                             "project, or of the standard library only"));
    row->addWidget(m_context);
    m_status = new QLabel(this);
    m_status->setObjectName(QStringLiteral("consoleStatus"));
    m_status->setTextFormat(Qt::PlainText);
    row->addWidget(m_status, 1);
    m_restart = new QPushButton(tr("Restart"), this);
    m_restart->setToolTip(tr("A new session in the selected context; the names of the console are lost"));
    m_interrupt = new QPushButton(tr("Interrupt"), this);
    m_interrupt->setToolTip(tr("Stop the running input; the names of the console stay (Ctrl+C in the input)"));
    auto *clear = new QPushButton(tr("Clear"), this);
    clear->setToolTip(tr("Clear the transcript; the names of the console stay"));
    row->addWidget(m_restart);
    row->addWidget(m_interrupt);
    row->addWidget(clear);
    layout->addLayout(row);

    m_splitter = new QSplitter(Qt::Horizontal, this);
    m_splitter->setObjectName(QStringLiteral("consoleSplitter"));
    auto *inputSplitter = new QSplitter(Qt::Vertical, m_splitter);
    m_transcript = new QPlainTextEdit(inputSplitter);
    m_transcript->setObjectName(QStringLiteral("consoleTranscript"));
    m_transcript->setReadOnly(true);
    m_transcript->setMaximumBlockCount(5000);
    m_transcript->viewport()->installEventFilter(this);
    m_input = new CodeEditor(inputSplitter);
    m_input->setObjectName(QStringLiteral("consoleInput"));
    m_input->setSyntax(CodeEditor::Syntax::PrimulaCode);
    m_input->setPlaceholderText(tr("Primula code; Enter runs, Shift+Enter breaks the line, Ctrl+↑/↓ — history, :help NAME"));
    m_input->installEventFilter(this);
    inputSplitter->setStretchFactor(0, 4);
    inputSplitter->setStretchFactor(1, 1);

    // The side: the functions of the catalogue and the names of the session.
    m_side = new QTabWidget(m_splitter);
    m_side->setObjectName(QStringLiteral("consoleSide"));
    auto *functionsPage = new QWidget(m_side);
    auto *functionsLayout = new QVBoxLayout(functionsPage);
    functionsLayout->setContentsMargins(2, 2, 2, 2);
    m_search = new QLineEdit(functionsPage);
    m_search->setObjectName(QStringLiteral("consoleHelpSearch"));
    m_search->setPlaceholderText(tr("Search functions…"));
    m_search->setClearButtonEnabled(true);
    m_functions = new QListWidget(functionsPage);
    m_functions->setObjectName(QStringLiteral("consoleFunctions"));
    m_functions->setContextMenuPolicy(Qt::CustomContextMenu);
    m_functions->setToolTip(tr("Double click puts the example into the input; the context menu has more"));
    m_help = new QTextBrowser(functionsPage);
    m_help->setObjectName(QStringLiteral("consoleHelp"));
    m_help->setOpenLinks(false);
    auto *helpSplitter = new QSplitter(Qt::Vertical, functionsPage);
    helpSplitter->addWidget(m_functions);
    helpSplitter->addWidget(m_help);
    helpSplitter->setStretchFactor(0, 2);
    helpSplitter->setStretchFactor(1, 1);
    functionsLayout->addWidget(m_search);
    functionsLayout->addWidget(helpSplitter, 1);
    m_side->addTab(functionsPage, tr("Functions"));

    auto *namesPage = new QWidget(m_side);
    auto *namesLayout = new QVBoxLayout(namesPage);
    namesLayout->setContentsMargins(2, 2, 2, 2);
    m_nameSearch = new QLineEdit(namesPage);
    m_nameSearch->setObjectName(QStringLiteral("consoleNameSearch"));
    m_nameSearch->setPlaceholderText(tr("Search names…"));
    m_nameSearch->setClearButtonEnabled(true);
    m_namesList = new QTreeWidget(namesPage);
    m_namesList->setObjectName(QStringLiteral("consoleNames"));
    m_namesList->setHeaderLabels({tr("Name"), tr("Type"), tr("Value")});
    m_namesList->setRootIsDecorated(false);
    m_namesList->setContextMenuPolicy(Qt::CustomContextMenu);
    m_namesList->setToolTip(tr("Names of the inputs (bold) and of the context; double click inserts the name, "
                               "the context menu shows the value"));
    namesLayout->addWidget(m_nameSearch);
    namesLayout->addWidget(m_namesList, 1);
    m_side->addTab(namesPage, tr("Names"));

    m_splitter->addWidget(inputSplitter);
    m_splitter->addWidget(m_side);
    m_splitter->setStretchFactor(0, 3);
    m_splitter->setStretchFactor(1, 2);
    layout->addWidget(m_splitter, 1);

    // Zoom of the whole window: Ctrl++ / Ctrl+= / Ctrl+- / Ctrl+0; Ctrl+wheel over the
    // transcript and the input.
    auto shortcut = [this](const QKeySequence &keys, int steps) {
        auto *action = new QAction(this);
        action->setShortcut(keys);
        action->setShortcutContext(Qt::WindowShortcut);
        connect(action, &QAction::triggered, this, [this, steps] { zoom(steps); });
        addAction(action);
    };
    shortcut(QKeySequence::ZoomIn, 1);
    shortcut(QKeySequence(Qt::CTRL | Qt::Key_Equal), 1);
    shortcut(QKeySequence::ZoomOut, -1);
    shortcut(QKeySequence(Qt::CTRL | Qt::Key_0), 0);
    connect(m_input, &CodeEditor::fontZoomRequested, this, &ConsolePanel::zoom);

    QSettings settings;
    m_fontSize = settings.value(QStringLiteral("console/fontSize"),
                                qMax(11, QFontDatabase::systemFont(QFontDatabase::FixedFont).pointSize() + 1)).toInt();
    applyFont();
    resize(1000, 640);
    restoreGeometry(settings.value(QStringLiteral("console/geometry")).toByteArray());
    m_splitter->restoreState(settings.value(QStringLiteral("console/splitter")).toByteArray());

    connect(m_context, &QComboBox::currentIndexChanged, this, [this] { if (m_process) restart(); });
    connect(m_restart, &QPushButton::clicked, this, &ConsolePanel::restart);
    connect(m_interrupt, &QPushButton::clicked, this, &ConsolePanel::interrupt);
    connect(clear, &QPushButton::clicked, m_transcript, &QPlainTextEdit::clear);
    connect(m_search, &QLineEdit::textChanged, this, &ConsolePanel::fillHelp);
    connect(m_nameSearch, &QLineEdit::textChanged, this, &ConsolePanel::fillNames);
    connect(m_functions, &QListWidget::currentItemChanged, this, [this](QListWidgetItem *item) {
        m_help->setPlainText(item ? item->toolTip() : QString());
    });
    connect(m_functions, &QListWidget::itemDoubleClicked, this, [this](QListWidgetItem *item) {
        insertIntoInput(item->data(ExampleRole).toString(), true);
    });
    connect(m_functions, &QWidget::customContextMenuRequested, this, &ConsolePanel::showFunctionMenu);
    connect(m_namesList, &QTreeWidget::itemDoubleClicked, this, [this](QTreeWidgetItem *item) {
        insertIntoInput(item->text(0), false);
    });
    connect(m_namesList, &QWidget::customContextMenuRequested, this, &ConsolePanel::showNameMenu);
    updateState();
}

ConsolePanel::~ConsolePanel()
{
    stop();
}

void ConsolePanel::showEvent(QShowEvent *event)
{
    QWidget::showEvent(event);
    emit visibilityChanged(true);
}

void ConsolePanel::hideEvent(QHideEvent *event)
{
    saveWindowState();
    QWidget::hideEvent(event);
    emit visibilityChanged(false);
}

void ConsolePanel::saveWindowState() const
{
    QSettings settings;
    settings.setValue(QStringLiteral("console/geometry"), saveGeometry());
    settings.setValue(QStringLiteral("console/splitter"), m_splitter->saveState());
    settings.setValue(QStringLiteral("console/fontSize"), m_fontSize);
}

void ConsolePanel::zoom(int steps)
{
    // 0 returns to the default size; the size is kept between 7 and 32 points.
    const int base = qMax(11, QFontDatabase::systemFont(QFontDatabase::FixedFont).pointSize() + 1);
    m_fontSize = steps == 0 ? base : qBound(7, m_fontSize + steps, 32);
    applyFont();
    QSettings().setValue(QStringLiteral("console/fontSize"), m_fontSize);
}

void ConsolePanel::applyFont()
{
    // The transcript and the input in the fixed font, the lists and the help in the
    // interface font — all of the same size.
    QFont fixed = QFontDatabase::systemFont(QFontDatabase::FixedFont);
    fixed.setPointSize(m_fontSize);
    m_transcript->setFont(fixed);
    m_input->setEditorFont(fixed);
    m_input->setMinimumHeight(QFontMetrics(fixed).lineSpacing() * 3 + 12);
    QFont plain = font();
    plain.setPointSize(m_fontSize);
    for (QWidget *widget : std::initializer_list<QWidget *>{m_functions, m_help, m_namesList, m_search, m_nameSearch})
        widget->setFont(plain);
}

void ConsolePanel::insertIntoInput(const QString &text, bool replace)
{
    // A function example replaces the input (it is a whole call); a name goes to the cursor.
    if (replace) {
        m_input->setPlainText(text);
        m_input->moveCursor(QTextCursor::End);
    } else {
        m_input->insertPlainText(text);
    }
    raise();
    activateWindow();
    m_input->setFocus();
}

void ConsolePanel::showFunctionMenu(const QPoint &point)
{
    QListWidgetItem *item = m_functions->itemAt(point);
    if (!item) return;
    const QString example = item->data(ExampleRole).toString();
    const QString name = item->data(NameRole).toString();
    const QString section = item->data(SectionRole).toString();
    QMenu menu(this);
    menu.addAction(tr("Put the example into the input"), this, [this, example] { insertIntoInput(example, true); });
    menu.addAction(tr("Insert the name"), this, [this, name] { insertIntoInput(name, false); });
    menu.addAction(tr("Run :help %1").arg(name), this, [this, name] { submit(QStringLiteral(":help ") + name); });
    menu.addSeparator();
    QAction *open = menu.addAction(tr("Open the section %1").arg(CommandCatalog::sectionLabel(section)), this,
                                   [this, section] { emit sectionRequested(section); });
    open->setEnabled(!section.isEmpty());
    menu.addAction(tr("Copy the name"), this, [name] { QApplication::clipboard()->setText(name); });
    menu.exec(m_functions->viewport()->mapToGlobal(point));
}

void ConsolePanel::showNameMenu(const QPoint &point)
{
    QTreeWidgetItem *item = m_namesList->itemAt(point);
    if (!item) return;
    const QString name = item->text(0);
    QMenu menu(this);
    menu.addAction(tr("Insert the name"), this, [this, name] { insertIntoInput(name, false); });
    menu.addAction(tr("Show the value"), this, [this, name] { submit(name); });
    menu.addSeparator();
    menu.addAction(tr("Copy the name"), this, [name] { QApplication::clipboard()->setText(name); });
    const QString value = item->data(2, Qt::UserRole).toString();
    QAction *copy = menu.addAction(tr("Copy the value"), this, [value] { QApplication::clipboard()->setText(value); });
    copy->setEnabled(!value.isEmpty());
    menu.exec(m_namesList->viewport()->mapToGlobal(point));
}

void ConsolePanel::fillNames()
{
    // The "names" of the last answer: those of the inputs first (bold), then the context.
    m_namesList->clear();
    const QString needle = m_nameSearch->text().trimmed();
    for (const QJsonValue &value : m_nameRows) {
        const QJsonObject row = value.toObject();
        const QString name = row.value(QStringLiteral("name")).toString();
        if (!needle.isEmpty() && !name.contains(needle, Qt::CaseInsensitive)) continue;
        const bool evaluated = row.value(QStringLiteral("value")).isString();
        const QString text = evaluated ? row.value(QStringLiteral("value")).toString() : tr("(not evaluated yet)");
        auto *item = new QTreeWidgetItem(m_namesList, {name, row.value(QStringLiteral("type")).toString(), text});
        item->setData(2, Qt::UserRole, evaluated ? text : QString());
        item->setToolTip(2, text);
        if (row.value(QStringLiteral("origin")).toString() == QStringLiteral("input")) {
            QFont bold = item->font(0);
            bold.setBold(true);
            item->setFont(0, bold);
        }
        if (!evaluated) item->setForeground(2, palette().brush(QPalette::Disabled, QPalette::Text));
    }
    m_namesList->resizeColumnToContents(0);
    m_namesList->resizeColumnToContents(1);
    m_side->setTabText(1, tr("Names (%1)").arg(m_nameRows.size()));
}

void ConsolePanel::setCatalog(const CommandCatalog *catalog)
{
    m_catalog = catalog;
    fillHelp();
}

void ConsolePanel::fillHelp()
{
    m_functions->clear();
    if (!m_catalog) return;
    const QString needle = m_search->text().trimmed();
    for (const CommandCatalog::Entry &entry : m_catalog->entries()) {
        if (!entry.function) continue;
        if (!needle.isEmpty() && !entry.label.contains(needle, Qt::CaseInsensitive)
            && !entry.summary.contains(needle, Qt::CaseInsensitive))
            continue;
        auto *item = new QListWidgetItem(entry.signature + QStringLiteral(" — ") + entry.summary, m_functions);
        item->setToolTip(entry.signature + QLatin1Char('\n') + entry.tooltip);
        item->setData(SectionRole, entry.section);
        item->setData(NameRole, entry.name);
        // The example of the tooltip line "Example: …  →  result" (the call alone).
        QString example;
        for (const QString &line : entry.tooltip.split(QLatin1Char('\n'))) {
            const int colon = int(line.indexOf(QStringLiteral(": ")));
            if (colon > 0 && line.contains(QLatin1Char('(')) && (line.contains(QStringLiteral("→")) || example.isEmpty())
                && !line.startsWith(QLatin1Char(' ')))
                example = line.mid(colon + 2).section(QStringLiteral("  →  "), 0, 0);
        }
        item->setData(ExampleRole, example.isEmpty() ? entry.name : example);
    }
}

void ConsolePanel::setHistoryPath(const QString &path)
{
    m_historyPath = path;
    m_history.clear();
    m_historyIndex = -1;
    QFile file(path);
    if (path.isEmpty() || !file.open(QIODevice::ReadOnly)) return;
    for (const QJsonValue &value : QJsonDocument::fromJson(file.readAll()).array()) m_history << value.toString();
}

void ConsolePanel::saveHistory() const
{
    if (m_historyPath.isEmpty()) return;
    QDir().mkpath(QFileInfo(m_historyPath).absolutePath());
    QSaveFile file(m_historyPath);
    if (!file.open(QIODevice::WriteOnly)) return;
    file.write(QJsonDocument(QJsonArray::fromStringList(m_history)).toJson(QJsonDocument::Indented));
    file.commit();
}

bool ConsolePanel::isRunning() const
{
    return m_process && m_process->state() != QProcess::NotRunning;
}

void ConsolePanel::stop()
{
    if (!m_process) return;
    m_process->disconnect(this);
    if (m_process->state() != QProcess::NotRunning) {
        m_process->closeWriteChannel();
        if (!m_process->waitForFinished(1000)) {
            m_process->kill();
            m_process->waitForFinished(1000);
        }
    }
    m_process->deleteLater();
    m_process = nullptr;
    m_busy = m_ready = false;
    updateState();
}

void ConsolePanel::restart()
{
    stop();
    const QString program = Translator::program();
    if (program.isEmpty() || !m_target) {
        updateState();
        return;
    }
    const Target target = m_target(m_context->currentData().toString());
    m_process = new QProcess(this);
    m_process->setProcessChannelMode(QProcess::SeparateChannels);
    m_process->setWorkingDirectory(target.directory);
    connect(m_process, &QProcess::readyReadStandardOutput, this, &ConsolePanel::readOutput);
    connect(m_process, &QProcess::readyReadStandardError, this, [this] {
        const QString text = QString::fromUtf8(m_process->readAllStandardError()).trimmed();
        if (!text.isEmpty()) append(text, QStringLiteral("gray"));
    });
    connect(m_process, &QProcess::finished, this, [this](int code) {
        append(tr("The session has ended (exit code %1). Restart starts a new one.").arg(code), QStringLiteral("gray"));
        m_busy = m_ready = false;
        updateState();
    });
    connect(m_process, &QProcess::errorOccurred, this, [this](QProcess::ProcessError error) {
        if (error == QProcess::FailedToStart) append(tr("Cannot start the translator: %1").arg(m_process->errorString()), QStringLiteral("red"));
    });
    append(QStringLiteral("— ") + target.description, QStringLiteral("gray"));
    m_busy = true;   // until the ready line
    m_process->start(program, QStringList{QStringLiteral("console"), QStringLiteral("--json")} + target.arguments);
    updateState();
}

bool ConsolePanel::submit(const QString &text)
{
    if (text.trimmed().isEmpty()) return false;
    if (!isRunning()) restart();
    if (!isRunning()) return false;
    if (m_busy && m_ready) return false;
    // Before the ready line the input waits in the pipe: the translator reads it next.
    const QString shown = text.trimmed();
    QStringList lines = shown.split(QLatin1Char('\n'));
    for (int i = 0; i < lines.size(); ++i) lines[i].prepend(i ? QStringLiteral("... ") : QStringLiteral(">>> "));
    append(lines.join(QLatin1Char('\n')), QStringLiteral("#2f6f9f"));
    m_history.removeAll(shown);
    m_history.append(shown);
    while (m_history.size() > HistoryLimit) m_history.removeFirst();
    m_historyIndex = -1;
    saveHistory();
    m_process->write(QJsonDocument(QJsonObject{{QStringLiteral("input"), shown}}).toJson(QJsonDocument::Compact) + '\n');
    if (m_ready) m_busy = true;
    updateState();
    return true;
}

void ConsolePanel::interrupt()
{
    // SIGINT stops the running input in the translator (P0006); the session goes on.
    if (isRunning() && m_busy && m_ready) ::kill(pid_t(m_process->processId()), SIGINT);
}

void ConsolePanel::readOutput()
{
    m_buffer += m_process->readAllStandardOutput();
    while (true) {
        const qsizetype newline = m_buffer.indexOf('\n');
        if (newline < 0) break;
        const QByteArray line = m_buffer.left(newline).trimmed();
        m_buffer.remove(0, newline + 1);
        if (line.isEmpty()) continue;
        const QJsonObject result = QJsonDocument::fromJson(line).object();
        if (result.isEmpty()) {
            append(QString::fromUtf8(line), QStringLiteral("gray"));
            continue;
        }
        showResult(result);
    }
}

void ConsolePanel::showResult(const QJsonObject &result)
{
    m_lastResult = result;
    if (result.contains(QStringLiteral("names"))) {
        m_nameRows = result.value(QStringLiteral("names")).toArray();
        fillNames();
    }
    if (result.value(QStringLiteral("ready")).toBool()) {
        m_ready = true;
        m_busy = false;
        const QJsonObject context = result.value(QStringLiteral("context")).toObject();
        m_names = int(context.value(QStringLiteral("names")).toArray().size());
        for (const QJsonValue &value : result.value(QStringLiteral("messages")).toArray()) {
            const QJsonObject message = value.toObject();
            append(QStringLiteral("%1:%2: %3 [%4] %5").arg(message.value(QStringLiteral("file")).toString())
                       .arg(message.value(QStringLiteral("line")).toInt())
                       .arg(message.value(QStringLiteral("severity")).toString(), message.value(QStringLiteral("code")).toString(),
                            message.value(QStringLiteral("message")).toString()),
                   message.value(QStringLiteral("severity")).toString() == QStringLiteral("error") ? QStringLiteral("red")
                                                                                                    : QStringLiteral("#b8860b"));
        }
    } else {
        m_busy = false;
        for (const QJsonValue &value : result.value(QStringLiteral("output")).toArray()) append(value.toString());
        const QString text = result.value(QStringLiteral("text")).toString();
        if (!text.isEmpty())
            append(text, result.value(QStringLiteral("ok")).toBool() ? QString() : QStringLiteral("red"));
        const QJsonValue value = result.value(QStringLiteral("value"));
        if (value.isString()) append(value.toString(), QStringLiteral("#006400"));
    }
    updateState();
    emit resultReceived(result);
}

void ConsolePanel::append(const QString &text, const QString &color)
{
    // Plain text in a colour: escaped, line breaks kept.
    QString html = text.toHtmlEscaped().replace(QLatin1Char('\n'), QStringLiteral("<br>")).replace(QLatin1Char(' '), QStringLiteral("&nbsp;"));
    if (!color.isEmpty()) html = QStringLiteral("<span style='color:%1'>%2</span>").arg(color, html);
    m_transcript->appendHtml(html);
    m_transcript->verticalScrollBar()->setValue(m_transcript->verticalScrollBar()->maximum());
}

void ConsolePanel::browseHistory(int step)
{
    if (m_history.isEmpty()) return;
    if (m_historyIndex < 0) m_historyIndex = int(m_history.size());
    m_historyIndex = qBound(0, m_historyIndex + step, int(m_history.size()));
    m_input->setPlainText(m_historyIndex < m_history.size() ? m_history.at(m_historyIndex) : QString());
    m_input->moveCursor(QTextCursor::End);
}

void ConsolePanel::updateState()
{
    m_interrupt->setEnabled(isRunning() && m_busy && m_ready);
    if (!isRunning()) m_status->setText(Translator::program().isEmpty() ? tr("The translator is not found.") : tr("not started"));
    else if (!m_ready) m_status->setText(tr("starting…"));
    else m_status->setText(tr("%1 names in the context (the Names tab)").arg(m_names)
                           + (m_busy ? QStringLiteral(" — ") + tr("running…") : QString()));
}

bool ConsolePanel::eventFilter(QObject *watched, QEvent *event)
{
    if (watched == m_transcript->viewport() && event->type() == QEvent::Wheel) {
        auto *wheel = static_cast<QWheelEvent *>(event);
        if (wheel->modifiers() & Qt::ControlModifier) {
            m_wheelRemainder += wheel->angleDelta().y() != 0 ? wheel->angleDelta().y() : wheel->pixelDelta().y() * 3;
            const int steps = m_wheelRemainder / 120;
            m_wheelRemainder %= 120;
            if (steps != 0) zoom(steps);
            return true;
        }
    }
    if (watched == m_input && event->type() == QEvent::KeyPress) {
        auto *key = static_cast<QKeyEvent *>(event);
        // The completion list of the editor assist takes its keys first.
        if (m_completer && m_completer->popup()->isVisible()) return false;
        const bool enter = key->key() == Qt::Key_Return || key->key() == Qt::Key_Enter;
        if (enter && !(key->modifiers() & Qt::ShiftModifier)) {
            // The cursor at the end: an open block or bracket continues on a new line.
            QString text = m_input->toPlainText();
            const bool atEnd = m_input->textCursor().atEnd();
            if (atEnd && complete(text)) {
                if (submit(text)) m_input->clear();
                return true;
            }
            return false;
        }
        if (key->modifiers() & Qt::ControlModifier) {
            if (key->key() == Qt::Key_Up) {
                browseHistory(-1);
                return true;
            }
            if (key->key() == Qt::Key_Down) {
                browseHistory(1);
                return true;
            }
            if (key->key() == Qt::Key_C && m_busy && !m_input->textCursor().hasSelection()) {
                interrupt();
                return true;
            }
        }
    }
    return QWidget::eventFilter(watched, event);
}
