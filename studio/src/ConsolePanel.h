#pragma once

// The evaluator console (stage 14.15, decision 128; a window of its own since 14.16): a
// terminal-like window over `primula console --json` — one translator process per context,
// whose names live between inputs.
//
//   transcript   the inputs (>>> …), the output of debug(…), the values and the messages
//   input        a code editor (Primula code highlighting, hints and completion of functions
//                by EditorAssist); Enter runs a complete input, Shift+Enter breaks the line,
//                a line ending with ':' or an open bracket continues; Ctrl+Up/Down — history
//   context      the current file (document, fragment, module, styles module, project),
//                the project, or the library only; Restart starts a new session
//   Interrupt    SIGINT to the translator: the running input stops (P0006), names stay
//   Functions    the functions of the catalogue with a search and their description; double
//                click or the context menu puts the example into the input, the context menu
//                also opens the section
//   Names        the names visible to the next input (the "names" of the protocol, decision
//                129): those of the inputs first, then those of the context; double click
//                inserts the name, the context menu also shows its value
//   zoom         Ctrl+wheel, Ctrl++ / Ctrl+- / Ctrl+0 — the font of the whole window
//   history      the last inputs in .primula-studio/console-history.json
//
// The window is non-modal and belongs to the main window (it stays above it and has no button
// of its own in the task bar); its geometry, splitter and font size are kept in QSettings
// (console/…).

#include <QJsonArray>
#include <QJsonObject>
#include <QStringList>
#include <QWidget>

#include <functional>

class CodeEditor;
class CommandCatalog;
class QCompleter;
class QComboBox;
class QLabel;
class QLineEdit;
class QListWidget;
class QPlainTextEdit;
class QProcess;
class QPushButton;
class QSplitter;
class QTabWidget;
class QTextBrowser;
class QTreeWidget;

class ConsolePanel : public QWidget
{
    Q_OBJECT

public:
    /// What the console runs in: the translator arguments after `console --json`, the working
    /// directory, and a short description of the context for the window.
    struct Target
    {
        QStringList arguments;
        QString directory;
        QString description;
    };
    /// mode: "file" (the current file), "project" or "library".
    using TargetProvider = std::function<Target(const QString &mode)>;

    /// parent: the main window; the console is a window of its own above it.
    explicit ConsolePanel(QWidget *parent = nullptr);
    ~ConsolePanel() override;

    void setTargetProvider(TargetProvider provider) { m_target = std::move(provider); }
    /// The catalogue for the function list, nullptr when unavailable.
    void setCatalog(const CommandCatalog *catalog);
    /// Where the history of inputs is kept (empty: not kept).
    void setHistoryPath(const QString &path);
    /// The completion list of the editor assist attached to the input: it takes Enter first.
    void setCompleter(QCompleter *completer) { m_completer = completer; }
    CodeEditor *input() const { return m_input; }

    /// Start (or restart) the session for the selected context.
    void restart();
    /// Run text as an input (also from the input editor); false while one is running.
    bool submit(const QString &text);
    /// Interrupt the running input.
    void interrupt();
    /// Stop the session (a project is closed).
    void stop();
    bool isBusy() const { return m_busy; }
    bool isRunning() const;
    QPlainTextEdit *transcript() const { return m_transcript; }
    /// The last result object of the translator (for tests).
    QJsonObject lastResult() const { return m_lastResult; }
    QStringList history() const { return m_history; }
    /// The list of names (for tests).
    QTreeWidget *namesList() const { return m_namesList; }
    /// The point size of the window font; zoom changes it by steps.
    int fontSize() const { return m_fontSize; }
    void zoom(int steps);
    /// Save the geometry, the splitter and the font size (also done when the window hides).
    void saveWindowState() const;

signals:
    /// A result (or the ready line) arrived.
    void resultReceived(const QJsonObject &result);
    /// Open the section of the library or the specification ("stdlib:3", "12.10").
    void sectionRequested(const QString &section);
    /// The window was shown or hidden (the check mark of View → Console).
    void visibilityChanged(bool visible);

protected:
    bool eventFilter(QObject *watched, QEvent *event) override;
    void showEvent(QShowEvent *event) override;
    void hideEvent(QHideEvent *event) override;

private:
    void readOutput();
    void showResult(const QJsonObject &result);
    void append(const QString &text, const QString &color = QString());
    void fillHelp();
    void fillNames();
    void insertIntoInput(const QString &text, bool replace);
    void showFunctionMenu(const QPoint &point);
    void showNameMenu(const QPoint &point);
    void applyFont();
    void browseHistory(int step);
    void saveHistory() const;
    void updateState();

    TargetProvider m_target;
    const CommandCatalog *m_catalog = nullptr;
    QProcess *m_process = nullptr;
    QByteArray m_buffer;
    bool m_busy = false;
    bool m_ready = false;
    QStringList m_history;
    int m_historyIndex = -1;
    QString m_historyPath;
    QJsonObject m_lastResult;
    QCompleter *m_completer = nullptr;
    int m_names = 0;           ///< names of the context (the ready line)
    QJsonArray m_nameRows;     ///< "names" of the last answer
    int m_fontSize = 11;
    int m_wheelRemainder = 0;

    QComboBox *m_context = nullptr;
    QLabel *m_status = nullptr;
    QPushButton *m_restart = nullptr;
    QPushButton *m_interrupt = nullptr;
    QPlainTextEdit *m_transcript = nullptr;
    CodeEditor *m_input = nullptr;
    QSplitter *m_splitter = nullptr;
    QTabWidget *m_side = nullptr;
    QLineEdit *m_search = nullptr;
    QListWidget *m_functions = nullptr;
    QTextBrowser *m_help = nullptr;
    QLineEdit *m_nameSearch = nullptr;
    QTreeWidget *m_namesList = nullptr;
};
