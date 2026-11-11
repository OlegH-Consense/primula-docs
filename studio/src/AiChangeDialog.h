#pragma once

// "Change the project with AI" (stage 27, second step). The user describes the change and chooses which files
// of the project go to the tool (a privacy choice: they are sent to its service). The tool works read-only and
// answers with the new text of the files it changes, adds or deletes (AiProject::parseFiles). The changes are
// put into a work directory that is a copy of the project (the project itself is not touched), the
// translator checks the result there, the dialog shows the differences file by file with the errors before
// and after, can send the errors back to the tool, and returns the changes that the user chooses.
// MainWindow applies them (a backup first, open files change in the editor and stay unsaved).

#include "AiController.h"
#include "AiProject.h"

#include <QDialog>
#include <QMap>
#include <QTemporaryDir>

#include <memory>

class QComboBox;
class QLabel;
class QListWidget;
class QPlainTextEdit;
class QPushButton;
class QStackedWidget;
class QTimer;

class AiChangeDialog : public QDialog
{
    Q_OBJECT

public:
    enum class Kind { Added, Changed, Deleted };
    struct Change
    {
        QString path;          ///< relative to the project, with '/'
        Kind kind = Kind::Changed;
        QByteArray before;     ///< the text in the project (empty for an added file)
        QByteArray after;      ///< the new text (empty for a deleted file)
    };

    /// @param context  the Primula context of the request (reference, rules); the dialog adds the task and the files.
    AiChangeDialog(const AiRequest &context, const QString &projectRoot, QWidget *parent = nullptr);
    ~AiChangeDialog() override;

    void setTask(const QString &task);
    bool setTool(const QString &id);
    /// Choose whether a file of the project is sent to the tool (the project file and the Primula files are by default).
    void setFileSent(const QString &path, bool sent);
    QStringList sentFiles() const;

    bool startRun(QString *error = nullptr);
    bool isRunning() const;
    /// Send the errors of the check back to the tool (the sent files in their changed state).
    bool fixErrors(QString *error = nullptr);

    const QList<Change> &changes() const { return m_changes; }
    const AiProject::Check &checkBefore() const { return m_before; }
    const AiProject::Check &checkAfter() const { return m_after; }
    const QString &answer() const { return m_answer; }
    void setChangeChosen(const QString &path, bool chosen);
    /// The chosen changes as files (a deletion has remove set).
    QList<AiProject::File> chosenChanges() const;

signals:
    void resultShown();
    void runFailed(const QString &reason);

private:
    AiRequest m_context;
    QString m_root;
    std::unique_ptr<QTemporaryDir> m_work;
    CliAgentBackend *m_backend = nullptr;
    AiAgent m_agent;
    QMap<QString, AiProject::File> m_proposed;   ///< the changes of the tool so far, by path
    QMap<QString, QByteArray> m_sent;            ///< the original text of the files that were sent
    QList<Change> m_changes;
    QStringList m_problems;
    AiProject::Check m_before, m_after;
    QString m_answer;
    bool m_haveBaseline = false;
    bool m_cancelled = false;

    QStackedWidget *m_pages = nullptr;
    QPlainTextEdit *m_task = nullptr;
    QComboBox *m_tools = nullptr;
    QListWidget *m_files = nullptr;
    QLabel *m_filesLabel = nullptr;
    QPushButton *m_start = nullptr;
    QLabel *m_progress = nullptr;
    QTimer *m_clock = nullptr;
    int m_seconds = 0;
    QListWidget *m_list = nullptr;
    QPlainTextEdit *m_diff = nullptr;
    QLabel *m_summary = nullptr;
    QPlainTextEdit *m_answerView = nullptr;
    QPushButton *m_fix = nullptr;
    QPushButton *m_apply = nullptr;

    void buildUi();
    void fillFiles();
    void updateButtons();
    void updateFilesLabel();
    void begin(const QString &task, const QStringList &paths, bool fix);
    void finished(bool success, const QString &response, const QString &error);
    void showResult();
    void showDiff();
    QByteArray currentText(const QString &path) const;
    void reject() override;
};
