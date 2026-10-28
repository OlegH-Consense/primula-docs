#pragma once

// Asynchronous runs of the Primula translator for Build and Check (stage 14.4).
//
// The translator is called with `--format json`: stdout is one JSON array of
// messages (specification 14.2: code, severity, message, file, line, column,
// notes, stack), stderr carries the human-readable lines ("written: …", the
// summary), which are shown in the log as they arrive.

#include <QByteArray>
#include <QJsonArray>
#include <QObject>
#include <QProcess>
#include <QStringList>

class BuildController : public QObject
{
    Q_OBJECT

public:
    /// Tool: a command that may rewrite the source (primula parallel, 7.7).
    /// Export: primula export through pandoc (decision 139).
    enum class Kind { Check, Build, Tool, Export };

    explicit BuildController(QObject *parent = nullptr);
    bool isRunning() const;
    /// Start `primula <arguments>` in workingDirectory; `--format json` is appended.
    /// Completion is reported by completed(); a start failure too.
    void start(Kind kind, const QStringList &arguments, const QString &workingDirectory);
    /// Terminate the running translator.
    void cancel();
    /// Messages of the last run (empty when its stdout was not JSON).
    QJsonArray messages() const { return m_messages; }

signals:
    void outputReceived(const QString &text);
    void started(BuildController::Kind kind);
    void completed(bool success, BuildController::Kind kind);

private:
    QProcess m_process;
    QByteArray m_stdout;
    QJsonArray m_messages;
    Kind m_kind = Kind::Check;
    bool m_reported = false;

    void finish(bool success);
};
