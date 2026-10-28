#include "BuildController.h"

#include "Translator.h"

#include <QJsonDocument>

BuildController::BuildController(QObject *parent) : QObject(parent)
{
    m_process.setProcessChannelMode(QProcess::SeparateChannels);
    connect(&m_process, &QProcess::readyReadStandardOutput, this, [this] {
        m_stdout += m_process.readAllStandardOutput();
    });
    connect(&m_process, &QProcess::readyReadStandardError, this, [this] {
        emit outputReceived(QString::fromUtf8(m_process.readAllStandardError()));
    });
    connect(&m_process, &QProcess::errorOccurred, this, [this](QProcess::ProcessError error) {
        if (error == QProcess::FailedToStart) {
            emit outputReceived(tr("Failed to start the translator: %1\n").arg(m_process.errorString()));
            finish(false);
        }
    });
    connect(&m_process, qOverload<int, QProcess::ExitStatus>(&QProcess::finished),
            this, [this](int exitCode, QProcess::ExitStatus status) {
        m_stdout += m_process.readAllStandardOutput();
        const QJsonDocument document = QJsonDocument::fromJson(m_stdout);
        m_messages = document.isArray() ? document.array() : QJsonArray();
        const bool success = status == QProcess::NormalExit && exitCode == 0;
        emit outputReceived(success ? tr("Finished successfully.\n")
                                    : tr("Finished with errors (exit code %1).\n").arg(exitCode));
        finish(success);
    });
}

bool BuildController::isRunning() const
{
    return m_process.state() != QProcess::NotRunning;
}

void BuildController::start(Kind kind, const QStringList &arguments, const QString &workingDirectory)
{
    if (isRunning())
        return;
    m_kind = kind;
    m_stdout.clear();
    m_messages = {};
    m_reported = false;
    const QString program = Translator::program();
    emit started(kind);
    if (program.isEmpty()) {
        emit outputReceived(tr("The Primula translator is not found: install 'primula' into PATH "
                               "or set its path in Settings.\n"));
        finish(false);
        return;
    }
    const QStringList full = arguments + QStringList{QStringLiteral("--format"), QStringLiteral("json")};
    m_process.setWorkingDirectory(workingDirectory);
    emit outputReceived(tr("Starting: %1 %2\n").arg(program, full.join(QLatin1Char(' '))));
    m_process.start(program, full);
}

void BuildController::cancel()
{
    if (!isRunning())
        return;
    m_process.terminate();
    if (!m_process.waitForFinished(1500))
        m_process.kill();
}

void BuildController::finish(bool success)
{
    // FailedToStart and finished() may both arrive; report once.
    if (m_reported)
        return;
    m_reported = true;
    emit completed(success, m_kind);
}
