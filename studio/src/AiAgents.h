#pragma once

// AI agents as data (stage 22.1): a command-line tool that receives the prompt and returns an
// answer is described by an entry of agents.json (built in: studio/resources/agents.json; the user
// file ~/.config/primula-docs/agents.json adds agents or replaces a built-in one with the same id).
// One class runs every agent (CliAgentBackend, AiController.h); this one reads the descriptions,
// builds the argument list and parses the output.

#include <QJsonObject>
#include <QList>
#include <QString>
#include <QStringList>

struct AiAgent
{
    QString id;              ///< a-z, 0-9, '-' and '_'; the value of the setting "ai/tool"
    QString name;            ///< shown in File → Settings
    QString label;           ///< history marker of the answers (AiExchange::backend)
    QString program;         ///< the default program (name in PATH or a path)
    QStringList arguments;   ///< one item per argument; "{prompt}" when prompt == "arg"
    QStringList writeArguments;   ///< the arguments of a run that may write files in its working directory (stage 27); empty — the tool has no write mode
    QStringList skillArguments;   ///< flags and values that replace (or are added to) the arguments when the agent loads the skill
    QString prompt = QStringLiteral("stdin");   ///< "stdin" or "arg"
    QString format = QStringLiteral("text");    ///< output: "text", "json" or "jsonl"
    QString field;           ///< dotted path of the answer text in the object or event
    QJsonObject ok;          ///< json: fields that must have these values when present
    QJsonObject match;       ///< jsonl: fields that choose the event with the answer (the last one)
    QJsonObject errorMatch;  ///< jsonl: fields that choose the events with an error text
    QString errorField;      ///< dotted path of the error text
    bool textFallback = false;   ///< json: an output that is not JSON is the answer itself
    bool userDefined = false;    ///< from the user file
};

class AiAgents
{
public:
    /// The user file ~/.config/primula-docs/agents.json.
    static QString userFile();
    /// Built-in agents, then the user file: the same id replaces, a new one is added.
    /// @param warnings receives a line for each entry or file that is skipped.
    static QList<AiAgent> load(const QString &userPath, QStringList *warnings = nullptr);
    /// load(userFile()).
    static QList<AiAgent> all(QStringList *warnings = nullptr);
    /// The agent with the id; the first one ("codex") when the id is unknown.
    static AiAgent byId(const QString &id);
    /// The ids of the agents chosen by default (the setting "ai/tools", in the order of the agents file);
    /// the first agent when none is chosen. The request window starts from this choice and remembers its own.
    static QStringList selected();
    /// The first of the chosen agents: the tool of a request that names none.
    static AiAgent current();
    /// The program: the setting "tools/<id>", else the default of the agent.
    static QString program(const AiAgent &agent);
    /// The arguments of the process; {prompt} is replaced when the agent takes the prompt in an argument.
    /// @param skill  the request lets the agent load the skill: the skill arguments are applied.
    /// @param write  the run may write files in its working directory (a project made by AI, stage 27): the
    ///               writeArguments are the base instead of the read-only arguments.
    static QStringList commandArguments(const AiAgent &agent, const QString &prompt, bool skill = false, bool write = false);
    /// The answer of the process output.
    /// @return false with error when the tool reports an error or gives nothing.
    static bool parseOutput(const AiAgent &agent, const QByteArray &output, QString *response, QString *error);
    /// An agent of an entry of the file, or an empty id with the reason in error.
    static AiAgent fromJson(const QJsonObject &object, QString *error);
};
