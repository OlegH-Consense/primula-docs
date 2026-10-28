#pragma once

// Asynchronous AI transport. The CLI (Codex or Claude) manages credentials; Studio provides only
// the explicit task and context and runs the tool without the right to change files.
//
//   codex   codex exec --ephemeral --json --sandbox read-only -        (settings: tools/codex)
//   claude  claude -p --output-format json --no-session-persistence
//                  --tools Read,Grep,Glob --permission-mode dontAsk    (settings: tools/claude)
//
// The tool is chosen in File → Settings (settings "ai/tool"); the prompt is the same for both.

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

class CodexExecBackend final : public IAiBackend
{
    Q_OBJECT

public:
    explicit CodexExecBackend(QObject *parent = nullptr);
    void start(const AiRequest &request) override;
    void cancel() override;
    bool isRunning() const override;

private:
    QProcess m_process;
    QByteArray m_stdoutBuffer;
    QString m_lastAgentMessage;
    QString m_errors;

    /// Parse incremental Codex JSON events, retaining complete lines between reads.
    void consumeOutput();
};

/// Claude Code in print mode: the prompt on stdin, one JSON result on stdout
/// ({"type":"result","is_error":false,"result":"…"}); only the read-only tools.
class ClaudePrintBackend final : public IAiBackend
{
    Q_OBJECT

public:
    explicit ClaudePrintBackend(QObject *parent = nullptr);
    void start(const AiRequest &request) override;
    void cancel() override;
    bool isRunning() const override;
    /// The answer of the CLI output: "result" of the JSON object; plain text of an older CLI as is.
    /// @return false with error when the CLI reports an error or gives nothing.
    static bool parseOutput(const QByteArray &output, QString *response, QString *error);

private:
    QProcess m_process;
    QByteArray m_stdout;
    QString m_errors;
};

class AiController : public QObject
{
    Q_OBJECT

public:
    explicit AiController(QObject *parent = nullptr);
    /// The tool of the settings: "codex" (default) or "claude".
    static QString tool();
    /// The history label of a tool ("codex-exec", "claude-print").
    static QString backendName(const QString &tool);
    /// The prompt both tools receive: rules, task, project and Primula context, files.
    static QByteArray makePrompt(const AiRequest &request);
    /// Start with the tool of the settings (read at each request).
    void start(const AiRequest &request);
    void cancel();
    bool isRunning() const;

signals:
    void progress(const QString &message);
    void finished(bool success, const QString &response, const QString &errorMessage);

private:
    CodexExecBackend *m_codex = nullptr;
    ClaudePrintBackend *m_claude = nullptr;
    IAiBackend *m_backend = nullptr;   ///< the one that runs or ran last
};

