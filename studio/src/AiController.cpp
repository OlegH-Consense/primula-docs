#include "AiController.h"

#include <QJsonDocument>
#include <QJsonObject>
#include <QSettings>

CodexExecBackend::CodexExecBackend(QObject *parent) : IAiBackend(parent)
{
    m_process.setProcessChannelMode(QProcess::SeparateChannels);
    connect(&m_process, &QProcess::readyReadStandardOutput, this, &CodexExecBackend::consumeOutput);
    connect(&m_process, &QProcess::readyReadStandardError, this, [this] {
        const QString text = QString::fromUtf8(m_process.readAllStandardError());
        m_errors += text;
        emit progress(text);
    });
    connect(&m_process, &QProcess::errorOccurred, this, [this](QProcess::ProcessError error) {
        if (error == QProcess::FailedToStart)
            emit finished(false, {}, tr("Cannot start Codex: %1").arg(m_process.errorString()));
    });
    connect(&m_process, qOverload<int, QProcess::ExitStatus>(&QProcess::finished),
            this, [this](int exitCode, QProcess::ExitStatus status) {
        consumeOutput();
        if (!m_stdoutBuffer.trimmed().isEmpty()) {
            m_stdoutBuffer.append('\n');
            consumeOutput();
        }
        const bool success = status == QProcess::NormalExit && exitCode == 0 && !m_lastAgentMessage.isEmpty();
        QString error = m_errors.trimmed();
        if (!success && error.isEmpty())
            error = tr("Codex finished without a usable response (exit code %1).").arg(exitCode);
        emit finished(success, m_lastAgentMessage, error);
    });
}

void CodexExecBackend::start(const AiRequest &request)
{
    if (isRunning())
        return;
    m_stdoutBuffer.clear();
    m_lastAgentMessage.clear();
    m_errors.clear();

    QSettings settings;
    const QString executable = settings.value(QStringLiteral("tools/codex"), QStringLiteral("codex")).toString();
    const QStringList arguments = {
        QStringLiteral("exec"), QStringLiteral("--ephemeral"), QStringLiteral("--json"),
        QStringLiteral("--sandbox"), QStringLiteral("read-only"),
        QStringLiteral("--skip-git-repo-check"), QStringLiteral("-")
    };
    m_process.setWorkingDirectory(request.projectDirectory);
    m_process.start(executable, arguments);
    if (!m_process.waitForStarted(3000))
        return;
    m_process.write(AiController::makePrompt(request));
    m_process.closeWriteChannel();
    emit progress(tr("AI request started.\n"));
}

void CodexExecBackend::cancel()
{
    if (!isRunning())
        return;
    m_process.terminate();
    if (!m_process.waitForFinished(1500))
        m_process.kill();
}

bool CodexExecBackend::isRunning() const
{
    return m_process.state() != QProcess::NotRunning;
}

void CodexExecBackend::consumeOutput()
{
    m_stdoutBuffer += m_process.readAllStandardOutput();
    while (true) {
        const qsizetype newline = m_stdoutBuffer.indexOf('\n');
        if (newline < 0)
            break;
        const QByteArray line = m_stdoutBuffer.left(newline).trimmed();
        m_stdoutBuffer.remove(0, newline + 1);
        if (line.isEmpty())
            continue;

        QJsonParseError parseError;
        const QJsonDocument json = QJsonDocument::fromJson(line, &parseError);
        if (parseError.error != QJsonParseError::NoError || !json.isObject())
            continue;
        const QJsonObject object = json.object();
        const QString type = object.value(QStringLiteral("type")).toString();
        if (type == QStringLiteral("item.completed")) {
            const QJsonObject item = object.value(QStringLiteral("item")).toObject();
            if (item.value(QStringLiteral("type")).toString() == QStringLiteral("agent_message"))
                m_lastAgentMessage = item.value(QStringLiteral("text")).toString();
        } else if (type == QStringLiteral("error")) {
            m_errors += object.value(QStringLiteral("message")).toString() + QLatin1Char('\n');
        }
    }
}

// ----------------------------------------------------------------------
// Claude Code (print mode)
// ----------------------------------------------------------------------

ClaudePrintBackend::ClaudePrintBackend(QObject *parent) : IAiBackend(parent)
{
    m_process.setProcessChannelMode(QProcess::SeparateChannels);
    connect(&m_process, &QProcess::readyReadStandardOutput, this, [this] { m_stdout += m_process.readAllStandardOutput(); });
    connect(&m_process, &QProcess::readyReadStandardError, this, [this] {
        const QString text = QString::fromUtf8(m_process.readAllStandardError());
        m_errors += text;
        emit progress(text);
    });
    connect(&m_process, &QProcess::errorOccurred, this, [this](QProcess::ProcessError error) {
        if (error == QProcess::FailedToStart)
            emit finished(false, {}, tr("Cannot start Claude CLI: %1").arg(m_process.errorString()));
    });
    connect(&m_process, qOverload<int, QProcess::ExitStatus>(&QProcess::finished),
            this, [this](int exitCode, QProcess::ExitStatus status) {
        m_stdout += m_process.readAllStandardOutput();
        QString response;
        QString error;
        const bool parsed = parseOutput(m_stdout, &response, &error);
        const bool success = status == QProcess::NormalExit && exitCode == 0 && parsed;
        if (!success) {
            error = QStringList{error, m_errors.trimmed()}.join(QLatin1Char('\n')).trimmed();
            if (error.isEmpty()) error = tr("Claude CLI finished without a usable response (exit code %1).").arg(exitCode);
        }
        emit finished(success, response, success ? QString() : error);
    });
}

void ClaudePrintBackend::start(const AiRequest &request)
{
    if (isRunning())
        return;
    m_stdout.clear();
    m_errors.clear();
    const QString executable = QSettings().value(QStringLiteral("tools/claude"), QStringLiteral("claude")).toString();
    // Print mode without a saved session; only the tools that read the project, and no
    // permission prompts: anything else is refused (dontAsk). The prompt comes on stdin.
    // See https://docs.claude.com/en/docs/claude-code/cli-reference
    const QStringList arguments = {
        QStringLiteral("-p"), QStringLiteral("--output-format"), QStringLiteral("json"),
        QStringLiteral("--no-session-persistence"),
        QStringLiteral("--tools"), QStringLiteral("Read,Grep,Glob"),
        QStringLiteral("--permission-mode"), QStringLiteral("dontAsk")
    };
    m_process.setWorkingDirectory(request.projectDirectory);
    m_process.start(executable, arguments);
    if (!m_process.waitForStarted(3000))
        return;
    m_process.write(AiController::makePrompt(request));
    m_process.closeWriteChannel();
    emit progress(tr("AI request started.\n"));
}

void ClaudePrintBackend::cancel()
{
    if (!isRunning())
        return;
    m_process.terminate();
    if (!m_process.waitForFinished(1500))
        m_process.kill();
}

bool ClaudePrintBackend::isRunning() const
{
    return m_process.state() != QProcess::NotRunning;
}

bool ClaudePrintBackend::parseOutput(const QByteArray &output, QString *response, QString *error)
{
    const QByteArray trimmed = output.trimmed();
    if (trimmed.isEmpty()) return false;
    QJsonParseError parseError;
    QJsonDocument json = QJsonDocument::fromJson(trimmed, &parseError);
    if (parseError.error != QJsonParseError::NoError) {
        // Lines of events (stream-json): the last one is the result.
        const QList<QByteArray> lines = trimmed.split('\n');
        json = QJsonDocument::fromJson(lines.last().trimmed(), &parseError);
    }
    if (parseError.error != QJsonParseError::NoError || !json.isObject()) {
        *response = QString::fromUtf8(trimmed);   // --output-format text of an older CLI
        return true;
    }
    const QJsonObject object = json.object();
    const QString result = object.value(QStringLiteral("result")).toString();
    if (object.value(QStringLiteral("is_error")).toBool() || result.trimmed().isEmpty()) {
        *error = result.trimmed().isEmpty() ? object.value(QStringLiteral("subtype")).toString() : result;
        return false;
    }
    *response = result;
    return true;
}

// ----------------------------------------------------------------------
// The prompt and the controller
// ----------------------------------------------------------------------

QByteArray AiController::makePrompt(const AiRequest &request)
{
    auto block = [](const QString &title, const QString &body) {
        return body.trimmed().isEmpty() ? QString()
                                        : QStringLiteral("\n\n") + title + QStringLiteral(":\n---\n") + body.trimmed() + QStringLiteral("\n---");
    };
    QString prompt;
    prompt += QStringLiteral(
        "You are assisting with a document in the Primula markup language (.prml files, translated to "
        "ODT). Do not edit files or run commands. Answer with a concrete proposed text or editorial advice, "
        "in the language of the user task. Write only Primula constructs and functions that the PRIMULA "
        "REFERENCE or the SPECIFICATION below define; when unsure, name the specification section to check. "
        "Preserve Primula constructs (commands |name(...), short forms such as |> |< |*{...}, environments "
        "closed by |end) unless the user explicitly asks to change them.\n\nUSER TASK:\n");
    prompt += request.task.trimmed();
    prompt += block(QStringLiteral("PROJECT CONTEXT (notes of the author)"), request.projectContext);
    prompt += block(QStringLiteral("DOCUMENT OR SELECTED TEXT"), request.document);
    prompt += block(QStringLiteral("MESSAGES OF THE LAST CHECK OR BUILD"), request.messages);
    prompt += block(QStringLiteral("PROJECT FILE"), request.projectFile);
    prompt += block(QStringLiteral("STYLES MODULES"), request.styles);
    prompt += block(QStringLiteral("AUTHORING RULES"), request.rules);
    prompt += block(QStringLiteral("EXAMPLE DOCUMENT"), request.example);
    prompt += block(QStringLiteral("OTHER PROJECT FILES"), request.fragments);
    prompt += block(QStringLiteral("PRIMULA REFERENCE (constructs and functions of the translator)"), request.reference);
    prompt += block(QStringLiteral("SPECIFICATION"), request.specification);
    return (prompt + QLatin1Char('\n')).toUtf8();
}

AiController::AiController(QObject *parent) : QObject(parent)
{
    m_codex = new CodexExecBackend(this);
    m_claude = new ClaudePrintBackend(this);
    m_backend = m_codex;
    for (IAiBackend *backend : {static_cast<IAiBackend *>(m_codex), static_cast<IAiBackend *>(m_claude)}) {
        connect(backend, &IAiBackend::progress, this, &AiController::progress);
        connect(backend, &IAiBackend::finished, this, &AiController::finished);
    }
}

QString AiController::tool()
{
    return QSettings().value(QStringLiteral("ai/tool")).toString() == QStringLiteral("claude") ? QStringLiteral("claude")
                                                                                              : QStringLiteral("codex");
}

QString AiController::backendName(const QString &tool)
{
    return tool == QStringLiteral("claude") ? QStringLiteral("claude-print") : QStringLiteral("codex-exec");
}

void AiController::start(const AiRequest &request)
{
    if (isRunning()) return;
    m_backend = tool() == QStringLiteral("claude") ? static_cast<IAiBackend *>(m_claude) : m_codex;
    m_backend->start(request);
}

void AiController::cancel() { m_backend->cancel(); }
bool AiController::isRunning() const { return m_codex->isRunning() || m_claude->isRunning(); }
