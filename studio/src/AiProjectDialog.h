#pragma once

// "Create a project with AI" (stage 27, the first scenario): the user describes the project, the tool
// writes it in a temporary work directory (write mode of the agent), Studio shows the files with the
// check of the translator, lets the tool fix the errors, and only then writes the chosen files into a
// new project directory. The work directory is removed when the dialog ends.

#include "AiController.h"
#include "AiProject.h"

#include <QDialog>
#include <QTemporaryDir>

#include <memory>

class QCheckBox;
class QComboBox;
class QLabel;
class QLineEdit;
class QListWidget;
class QPlainTextEdit;
class QPushButton;
class QStackedWidget;
class QTimer;

class AiProjectDialog : public QDialog
{
    Q_OBJECT

public:
    /// @param context  the Primula context of the request (reference, rules, the specification sections):
    ///                 the dialog adds the task and the work directory.
    /// @param defaultParent  the directory in which the new project directory is made by default.
    AiProjectDialog(const AiRequest &context, const QString &defaultParent, QWidget *parent = nullptr);
    ~AiProjectDialog() override;

    // The inputs (also set by tests).
    void setTask(const QString &task);
    void setTarget(const QString &parentDirectory, const QString &folderName);
    /// Choose the tool by id; false when it has no write mode or its program is not found.
    bool setTool(const QString &id);
    /// How the tool delivers the files: in its answer (read-only run, works with every tool; the default) or by writing them
    /// in the work directory (needs the write mode of the tool, writeArguments).
    void setFilesInAnswer(bool inAnswer);
    QString targetDirectory() const;

    /// Start the tool in a fresh work directory. false with the reason in error when it cannot start.
    bool startRun(QString *error = nullptr);
    bool isRunning() const;
    /// The files of the last answer.
    const QList<AiProject::File> &files() const { return m_files; }
    const AiProject::Check &checkResult() const { return m_check; }
    const QString &answer() const { return m_answer; }
    /// Choose or unchoose a file of the list by its path.
    void setFileChosen(const QString &path, bool chosen);
    /// Ask the tool to fix the errors of the check in the same work directory.
    bool fixErrors(QString *error = nullptr);
    /// Write the chosen files into the target directory.
    /// @param overwrite  replace the files that exist there (the dialog asks the user before).
    /// @return false with the reason in error.
    bool createProject(bool overwrite, QString *error = nullptr);
    /// The file to open after the project is created (empty before).
    QString createdEntry() const { return m_created; }

signals:
    /// The answer is read, the files are listed and checked.
    void resultShown();
    /// The run failed or was cancelled; the dialog is back at the task.
    void runFailed(const QString &reason);

private:
    AiRequest m_context;
    QString m_defaultParent;
    std::unique_ptr<QTemporaryDir> m_work;   ///< the work directory of the tool (removed with the object)
    CliAgentBackend *m_backend = nullptr;
    AiAgent m_agent;
    QList<AiProject::File> m_files;
    QStringList m_skipped;
    AiProject::Check m_check;
    QString m_answer;
    QString m_created;
    bool m_cancelled = false;

    QStackedWidget *m_pages = nullptr;
    QPlainTextEdit *m_task = nullptr;
    QComboBox *m_tools = nullptr;
    QComboBox *m_delivery = nullptr;
    QStringList m_deliveryProblems;   ///< file blocks of the answer that were left out
    QLineEdit *m_parent = nullptr;
    QLineEdit *m_folder = nullptr;
    QLabel *m_targetLabel = nullptr;
    QPushButton *m_start = nullptr;
    QLabel *m_progress = nullptr;
    QTimer *m_clock = nullptr;
    int m_seconds = 0;
    QListWidget *m_list = nullptr;
    QPlainTextEdit *m_preview = nullptr;
    QLabel *m_summary = nullptr;
    QPlainTextEdit *m_answerView = nullptr;
    QPushButton *m_fix = nullptr;
    QPushButton *m_create = nullptr;

    void buildUi();
    void begin(const QString &task);
    void finished(bool success, const QString &response, const QString &error);
    void showResult();
    void updateTarget();
    void updateButtons();
    void showPreview();
    void createClicked();
    void reject() override;
};
