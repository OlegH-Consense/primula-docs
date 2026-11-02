#include "AiAgents.h"

#include <QCoreApplication>
#include <QDir>
#include <QFile>
#include <QJsonArray>
#include <QJsonDocument>
#include <QRegularExpression>
#include <QSettings>
#include <QStandardPaths>

namespace {

/// The value at a dotted path ("item.text") of nested objects; undefined when absent.
QJsonValue valueAt(const QJsonObject &object, const QString &path)
{
    QJsonValue current(object);
    for (const QString &part : path.split(QLatin1Char('.'))) {
        if (!current.isObject()) return QJsonValue(QJsonValue::Undefined);
        current = current.toObject().value(part);
    }
    return current;
}

/// Every field of the pattern is present with this value (an empty pattern matches everything).
bool matches(const QJsonObject &object, const QJsonObject &pattern)
{
    for (auto it = pattern.begin(); it != pattern.end(); ++it)
        if (valueAt(object, it.key()) != it.value()) return false;
    return true;
}

/// A field of the pattern that is present has this value (an absent one is not an error).
bool consistent(const QJsonObject &object, const QJsonObject &pattern)
{
    for (auto it = pattern.begin(); it != pattern.end(); ++it) {
        const QJsonValue value = valueAt(object, it.key());
        if (!value.isUndefined() && value != it.value()) return false;
    }
    return true;
}

QJsonObject parseObject(const QByteArray &text)
{
    QJsonParseError parseError;
    const QJsonDocument json = QJsonDocument::fromJson(text.trimmed(), &parseError);
    return parseError.error == QJsonParseError::NoError && json.isObject() ? json.object() : QJsonObject();
}

QStringList stringList(const QJsonValue &value, bool *valid)
{
    QStringList result;
    if (!value.isArray()) { *valid = false; return result; }
    for (const QJsonValue &item : value.toArray()) {
        if (!item.isString()) *valid = false;
        result << item.toString();
    }
    return result;
}

} // namespace

QString AiAgents::userFile()
{
    return QDir(QStandardPaths::writableLocation(QStandardPaths::GenericConfigLocation))
        .filePath(QStringLiteral("primula-docs/agents.json"));
}

AiAgent AiAgents::fromJson(const QJsonObject &object, QString *error)
{
    AiAgent agent;
    auto fail = [&](const QString &reason) { *error = reason; return AiAgent(); };
    agent.id = object.value(QStringLiteral("id")).toString();
    static const QRegularExpression idPattern(QStringLiteral("^[a-z0-9_-]+$"));
    if (!idPattern.match(agent.id).hasMatch()) return fail(QStringLiteral("id must be a-z, 0-9, '-' or '_'"));
    agent.name = object.value(QStringLiteral("name")).toString(agent.id);
    agent.label = object.value(QStringLiteral("label")).toString(agent.id + QStringLiteral("-print"));
    agent.program = object.value(QStringLiteral("program")).toString();
    if (agent.program.trimmed().isEmpty()) return fail(QStringLiteral("program is missing"));
    bool valid = true;
    agent.arguments = stringList(object.value(QStringLiteral("arguments")), &valid);
    if (!valid) return fail(QStringLiteral("arguments must be a list of strings"));
    agent.skillArguments = stringList(object.value(QStringLiteral("skillArguments")), &valid);
    if (!valid && object.contains(QStringLiteral("skillArguments"))) return fail(QStringLiteral("skillArguments must be a list of strings"));
    valid = true;
    agent.prompt = object.value(QStringLiteral("prompt")).toString(QStringLiteral("stdin"));
    if (agent.prompt != QStringLiteral("stdin") && agent.prompt != QStringLiteral("arg"))
        return fail(QStringLiteral("prompt must be \"stdin\" or \"arg\""));
    if (agent.prompt == QStringLiteral("arg") && !agent.arguments.contains(QStringLiteral("{prompt}")))
        return fail(QStringLiteral("prompt \"arg\" needs the item \"{prompt}\" in arguments"));
    const QJsonObject output = object.value(QStringLiteral("output")).toObject();
    agent.format = output.value(QStringLiteral("format")).toString(QStringLiteral("text"));
    agent.field = output.value(QStringLiteral("field")).toString();
    agent.ok = output.value(QStringLiteral("ok")).toObject();
    agent.match = output.value(QStringLiteral("match")).toObject();
    agent.errorMatch = output.value(QStringLiteral("errorMatch")).toObject();
    agent.errorField = output.value(QStringLiteral("errorField")).toString();
    agent.textFallback = output.value(QStringLiteral("textFallback")).toBool();
    if (agent.format != QStringLiteral("text") && agent.format != QStringLiteral("json")
        && agent.format != QStringLiteral("jsonl"))
        return fail(QStringLiteral("output.format must be \"text\", \"json\" or \"jsonl\""));
    if (agent.format != QStringLiteral("text") && agent.field.isEmpty())
        return fail(QStringLiteral("output.field is missing"));
    if (agent.format == QStringLiteral("jsonl") && agent.match.isEmpty())
        return fail(QStringLiteral("output.match is missing (it chooses the event with the answer)"));
    return agent;
}

QList<AiAgent> AiAgents::load(const QString &userPath, QStringList *warnings)
{
    QList<AiAgent> agents;
    auto note = [warnings](const QString &text) { if (warnings) warnings->append(text); };
    auto read = [&](const QString &path, bool user) {
        QFile file(path);
        if (!file.open(QIODevice::ReadOnly)) return;   // the user file is optional
        QJsonParseError parseError;
        const QJsonDocument json = QJsonDocument::fromJson(file.readAll(), &parseError);
        if (parseError.error != QJsonParseError::NoError || !json.isObject()) {
            note(QStringLiteral("%1: %2").arg(path, parseError.error != QJsonParseError::NoError
                                                        ? parseError.errorString() : QStringLiteral("not an object")));
            return;
        }
        int number = 0;
        for (const QJsonValue &entry : json.object().value(QStringLiteral("agents")).toArray()) {
            ++number;
            QString error;
            AiAgent agent = fromJson(entry.toObject(), &error);
            if (agent.id.isEmpty()) {
                note(QStringLiteral("%1, agent %2: %3").arg(path).arg(number).arg(error));
                continue;
            }
            agent.userDefined = user;
            bool replaced = false;
            for (AiAgent &known : agents)
                if (known.id == agent.id) { known = agent; replaced = true; }
            if (!replaced) agents.append(agent);
        }
    };
    read(QStringLiteral(":/config/agents.json"), false);
    if (!userPath.isEmpty()) read(userPath, true);
    return agents;
}

QList<AiAgent> AiAgents::all(QStringList *warnings)
{
    return load(userFile(), warnings);
}

AiAgent AiAgents::byId(const QString &id)
{
    const QList<AiAgent> agents = all();
    for (const AiAgent &agent : agents)
        if (agent.id == id) return agent;
    return agents.value(0);
}

QStringList AiAgents::selected()
{
    const QList<AiAgent> agents = all();
    QStringList wanted = QSettings().value(QStringLiteral("ai/tools")).toStringList();
    if (wanted.isEmpty() && !QSettings().value(QStringLiteral("ai/tool")).toString().isEmpty())
        wanted << QSettings().value(QStringLiteral("ai/tool")).toString();   // the setting of the versions with one tool
    QStringList result;
    for (const AiAgent &agent : agents)
        if (wanted.contains(agent.id)) result << agent.id;
    if (result.isEmpty() && !agents.isEmpty()) result << agents.first().id;
    return result;
}

AiAgent AiAgents::current()
{
    return byId(selected().value(0));
}

QString AiAgents::program(const AiAgent &agent)
{
    const QString chosen = QSettings().value(QStringLiteral("tools/") + agent.id).toString().trimmed();
    return chosen.isEmpty() ? agent.program : chosen;
}

QStringList AiAgents::commandArguments(const AiAgent &agent, const QString &prompt, bool skill)
{
    QStringList result = agent.arguments;
    // A flag of the skill arguments replaces the value of the same flag, else it is added with its value.
    for (int i = 0; skill && i < agent.skillArguments.size(); ++i) {
        const QString flag = agent.skillArguments.at(i);
        const bool hasValue = i + 1 < agent.skillArguments.size() && !agent.skillArguments.at(i + 1).startsWith(QLatin1String("--"));
        const int at = result.indexOf(flag);
        if (at >= 0 && hasValue && at + 1 < result.size()) result[at + 1] = agent.skillArguments.at(i + 1);
        else if (at < 0) result << flag;
        if (at < 0 && hasValue) result << agent.skillArguments.at(i + 1);
        if (hasValue) ++i;
    }
    if (agent.prompt == QStringLiteral("arg"))
        result.replaceInStrings(QStringLiteral("{prompt}"), prompt);
    return result;
}

bool AiAgents::parseOutput(const AiAgent &agent, const QByteArray &output, QString *response, QString *error)
{
    const QByteArray trimmed = output.trimmed();
    response->clear();
    error->clear();
    if (trimmed.isEmpty()) return false;
    if (agent.format == QStringLiteral("text")) {
        *response = QString::fromUtf8(trimmed);
        return true;
    }
    if (agent.format == QStringLiteral("jsonl")) {
        QStringList errors;
        for (const QByteArray &line : trimmed.split('\n')) {
            const QJsonObject event = parseObject(line);
            if (event.isEmpty()) continue;
            if (matches(event, agent.match)) *response = valueAt(event, agent.field).toString();
            else if (!agent.errorMatch.isEmpty() && matches(event, agent.errorMatch))
                errors << valueAt(event, agent.errorField).toString();
        }
        *error = errors.join(QLatin1Char('\n')).trimmed();
        return !response->trimmed().isEmpty();
    }
    // json: one object; an output of events (stream) gives the last line.
    QJsonObject object = parseObject(trimmed);
    if (object.isEmpty()) object = parseObject(trimmed.split('\n').last());
    if (object.isEmpty()) {
        if (!agent.textFallback) {
            *error = QCoreApplication::translate("AiAgents", "The output of the tool is not JSON.");
            return false;
        }
        *response = QString::fromUtf8(trimmed);
        return true;
    }
    const QString text = valueAt(object, agent.field).toString();
    const QString reason = agent.errorField.isEmpty() ? QString() : valueAt(object, agent.errorField).toString();
    if (!consistent(object, agent.ok) || text.trimmed().isEmpty()) {
        *error = !reason.trimmed().isEmpty() ? reason
                 : !object.value(QStringLiteral("subtype")).toString().isEmpty() ? object.value(QStringLiteral("subtype")).toString()
                 : object.value(QStringLiteral("stopReason")).toString();
        return false;
    }
    *response = text;
    return true;
}
