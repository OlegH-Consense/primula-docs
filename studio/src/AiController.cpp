#include "AiController.h"

#include "AiProject.h"

#include "AiEdits.h"

// ----------------------------------------------------------------------
// The agent process
// ----------------------------------------------------------------------

CliAgentBackend::CliAgentBackend(QObject *parent) : IAiBackend(parent)
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
            emit finished(false, {}, tr("Cannot start %1: %2").arg(m_agent.name, m_process.errorString()));
    });
    connect(&m_process, qOverload<int, QProcess::ExitStatus>(&QProcess::finished),
            this, [this](int exitCode, QProcess::ExitStatus status) {
        m_stdout += m_process.readAllStandardOutput();
        QString response;
        QString error;
        const bool parsed = AiAgents::parseOutput(m_agent, m_stdout, &response, &error);
        const bool success = status == QProcess::NormalExit && exitCode == 0 && parsed;
        if (!success) {
            error = QStringList{error, m_errors.trimmed()}.join(QLatin1Char('\n')).trimmed();
            if (error.isEmpty())
                error = tr("%1 finished without a usable response (exit code %2).").arg(m_agent.name).arg(exitCode);
        }
        emit finished(success, response, success ? QString() : error);
    });
}

void CliAgentBackend::start(const AiRequest &request)
{
    start(request, AiAgents::current());
}

void CliAgentBackend::start(const AiRequest &request, const AiAgent &agent)
{
    if (isRunning())
        return;
    m_stdout.clear();
    m_errors.clear();
    m_agent = agent;
    const QByteArray prompt = AiController::makePrompt(request);
    m_process.setWorkingDirectory(request.projectDirectory);
    m_process.start(AiAgents::program(m_agent), AiAgents::commandArguments(m_agent, QString::fromUtf8(prompt), request.useSkill,
                                                                           request.createProject && !request.filesInAnswer));
    if (!m_process.waitForStarted(3000))
        return;
    if (m_agent.prompt == QStringLiteral("stdin"))
        m_process.write(prompt);
    m_process.closeWriteChannel();
    emit progress(tr("AI request started.\n"));
}

void CliAgentBackend::cancel()
{
    if (!isRunning())
        return;
    m_process.terminate();
    if (!m_process.waitForFinished(1500))
        m_process.kill();
}

bool CliAgentBackend::isRunning() const
{
    return m_process.state() != QProcess::NotRunning;
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
    if (request.createProject)
        prompt += QString::fromLatin1(request.changeProject ? "You are changing a project" : "You are creating a project")
                  + QStringLiteral(" in the Primula markup language (.prml files, translated to ODT). Write in the language of the user "
                                   "task. Preserve Primula constructs (commands |name(...), short forms such as |> |< |*{...}, "
                                   "environments closed by |end).\n\n")
                  + (request.changeProject ? AiProject::instructionsForChange()
                     : request.filesInAnswer ? AiProject::instructionsInAnswer() : AiProject::instructions());
    else
    prompt += QStringLiteral(
        "You are assisting with a document in the Primula markup language (.prml files, translated to "
        "ODT). Do not edit files or run commands. Answer with a concrete proposed text or editorial advice, "
        "in the language of the user task. Write only Primula constructs and functions that the PRIMULA "
        "REFERENCE or the SPECIFICATION below define; when unsure, name the specification section to check. "
        "Preserve Primula constructs (commands |name(...), short forms such as |> |< |*{...}, environments "
        "closed by |end) unless the user explicitly asks to change them.");
    if (request.useSkill)
        prompt += QStringLiteral(
            "\n\nSKILL. Load and follow the skill \"primula-docs\" (rules and syntax of Primula) before you answer; it "
            "replaces the reference, which is not attached. If you cannot load it, write \"Skill: not loaded\" on the "
            "first line of the answer; otherwise write \"Skill: loaded\".");
    if (request.proposeEdits)
        prompt += QStringLiteral("\n\n") + AiEdits::instructions();
    prompt += QStringLiteral("\n\nUSER TASK:\n");
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

AiController::AiController(QObject *parent) : QObject(parent) {}

QString AiController::tool() { return AiAgents::current().id; }

QString AiController::toolName() { return AiAgents::current().name; }

QString AiController::backendName(const QString &tool) { return AiAgents::byId(tool).label; }

CliAgentBackend *AiController::backendFor(const QString &agentId)
{
    CliAgentBackend *&backend = m_pool[agentId];
    if (!backend) {
        backend = new CliAgentBackend(this);
        connect(backend, &IAiBackend::progress, this, [this, agentId](const QString &text) {
            // With several tools the lines of the log say whose they are.
            emit progress(!m_many ? text : QStringLiteral("[%1] ").arg(AiAgents::byId(agentId).name) + text);
        });
        connect(backend, &IAiBackend::finished, this, [this, agentId](bool success, const QString &response, const QString &error) {
            agentDone(agentId, success, response, error);
        });
    }
    return backend;
}

void AiController::agentDone(const QString &agentId, bool success, const QString &response, const QString &errorMessage)
{
    if (!m_waiting.contains(agentId)) return;
    m_waiting.removeAll(agentId);
    if (m_single) {
        emit finished(success, response, errorMessage);
        return;
    }
    emit agentFinished(agentId, success, response, errorMessage);
    if (m_waiting.isEmpty()) emit allFinished();
}

void AiController::start(const AiRequest &request)
{
    if (isRunning()) return;
    const QString id = tool();
    m_single = true;
    m_many = false;
    m_waiting = {id};
    backendFor(id)->start(request, AiAgents::byId(id));
}

void AiController::startAgents(const AiRequest &request, const QStringList &agentIds)
{
    if (isRunning() || agentIds.isEmpty()) return;
    m_single = false;
    m_waiting.clear();
    for (const QString &id : agentIds)
        if (!m_waiting.contains(id)) m_waiting << id;
    m_many = m_waiting.size() > 1;
    // A tool that cannot start answers at once: the list is complete before the first start.
    const QStringList ids = m_waiting;
    for (const QString &id : ids)
        backendFor(id)->start(request, AiAgents::byId(id));
}

void AiController::cancel()
{
    for (CliAgentBackend *backend : std::as_const(m_pool))
        backend->cancel();
}

bool AiController::isRunning() const
{
    return !m_waiting.isEmpty();
}
