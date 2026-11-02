#pragma once

// Asynchronous AI transport. The CLI (Codex, Claude, Grok or one of the user file) manages
// credentials; Studio provides only the explicit task and context and runs the tool without the
// right to change files. The tools are described by data (AiAgents.h, agents.json): the program,
// the arguments of a read-only run, how the prompt goes in and how the answer is read.
//
// The tool is chosen in File → Settings (settings "ai/tool", the program "tools/<id>"); the
// prompt is the same for all.

#include "AiAgents.h"

#include <QMap>
#include <QObject>
#include <QProcess>

struct AiRequest
{
    QString task;
    QString projectContext;
    QString document;
    QString styles;
    QString rules;
    QString example;
    QString fragments;
    QString projectFile;    ///< text of the project file (project.p.prml) when it is not the document
    QString reference;      ///< AiContext::reference(): constructs and functions of the translator
    QString specification;  ///< chosen sections or the whole specification (AiContext)
    QString messages;       ///< messages of the last check or build (AiContext::messages)
    QString projectDirectory;
    bool useSkill = false;       ///< the agent loads the local skill primula-docs instead of getting the reference
    bool proposeEdits = false;   ///< ask for ORIGINAL/REPLACEMENT blocks that Studio can apply (AiEdits)
};

class IAiBackend : public QObject
{
    Q_OBJECT

public:
    explicit IAiBackend(QObject *parent = nullptr) : QObject(parent) {}
    ~IAiBackend() override = default;
    virtual void start(const AiRequest &request) = 0;
    virtual void cancel() = 0;
    virtual bool isRunning() const = 0;

signals:
    void progress(const QString &message);
    void finished(bool success, const QString &response, const QString &errorMessage);
};

/// Runs the agent of the settings (AiAgents::current(), read at the start): the prompt on stdin
/// or in an argument, the answer parsed by the rules of the description.
class CliAgentBackend final : public IAiBackend
{
    Q_OBJECT

public:
    explicit CliAgentBackend(QObject *parent = nullptr);
    void start(const AiRequest &request) override;
    /// Start with this agent (not the one of the settings).
    void start(const AiRequest &request, const AiAgent &agent);
    void cancel() override;
    bool isRunning() const override;

private:
    QProcess m_process;
    QByteArray m_stdout;
    QString m_errors;
    AiAgent m_agent;
};

class AiController : public QObject
{
    Q_OBJECT

public:
    explicit AiController(QObject *parent = nullptr);
    /// The id of the first tool chosen by default ("codex" when nothing is chosen).
    static QString tool();
    /// The name of that tool, as File → Settings shows it.
    static QString toolName();
    /// The history label of a tool ("codex-exec", "claude-print", "grok-print").
    static QString backendName(const QString &tool);
    /// The prompt all tools receive: rules, task, project and Primula context, files.
    static QByteArray makePrompt(const AiRequest &request);
    /// Start one tool, the first one chosen by default; the result comes with `finished`.
    void start(const AiRequest &request);
    /// Start the same request with several tools at once (stage 22.6): each has its own process; the
    /// answers come with `agentFinished`, in the order they arrive, and `allFinished` ends the request.
    void startAgents(const AiRequest &request, const QStringList &agentIds);
    void cancel();
    bool isRunning() const;

signals:
    void progress(const QString &message);
    /// The one tool of `start` is done.
    void finished(bool success, const QString &response, const QString &errorMessage);
    /// A tool of `startAgents` is done.
    void agentFinished(const QString &agentId, bool success, const QString &response, const QString &errorMessage);
    /// Every tool of `startAgents` is done (or cancelled).
    void allFinished();

private:
    QMap<QString, CliAgentBackend *> m_pool;   ///< a process runner per tool, kept between requests
    QStringList m_waiting;                     ///< the tools of the running request that have not answered
    bool m_single = false;                     ///< the request was started with `start`
    bool m_many = false;                       ///< the request runs with more than one tool

    CliAgentBackend *backendFor(const QString &agentId);
    void agentDone(const QString &agentId, bool success, const QString &response, const QString &errorMessage);
};
