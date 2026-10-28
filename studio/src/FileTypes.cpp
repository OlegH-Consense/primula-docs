#include "FileTypes.h"

#include <QDir>
#include <QFile>
#include <QFileInfo>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QRegularExpression>
#include <QStandardPaths>

namespace {

const QStringList kOpenModes{QStringLiteral("editor"), QStringLiteral("preview"), QStringLiteral("system"),
                             QStringLiteral("command")};

QByteArray readFile(const QString &path)
{
    QFile file(path);
    return file.open(QIODevice::ReadOnly) ? file.readAll() : QByteArray();
}

} // namespace

void FileTypes::load(const QString &userFile, const QString &projectRoot)
{
    m_types.clear();
    m_problems.clear();
    addJson(readFile(QStringLiteral(":/config/file-types.json")), QStringLiteral("builtin"),
            QStringLiteral(":/config/file-types.json"));
    if (!userFile.isEmpty() && QFileInfo::exists(userFile))
        addJson(readFile(userFile), QStringLiteral("user"), userFile);
    if (!projectRoot.isEmpty()) {
        const QString project = projectFile(projectRoot);
        if (QFileInfo::exists(project))
            addJson(readFile(project), QStringLiteral("project"), project);
    }
}

bool FileTypes::addJson(const QByteArray &json, const QString &origin, const QString &file)
{
    QJsonParseError error;
    const QJsonDocument document = QJsonDocument::fromJson(json, &error);
    if (!document.isObject()) {
        m_problems << QStringLiteral("%1: %2").arg(file, error.errorString());
        return false;
    }
    const QJsonArray types = document.object().value(QStringLiteral("types")).toArray();
    for (const QJsonValue &value : types) {
        const QJsonObject object = value.toObject();
        FileType type;
        type.name = object.value(QStringLiteral("name")).toString();
        for (const QJsonValue &pattern : object.value(QStringLiteral("patterns")).toArray())
            if (!pattern.toString().trimmed().isEmpty()) type.patterns << pattern.toString().trimmed();
        type.open = object.value(QStringLiteral("open")).toString(QStringLiteral("editor"));
        for (const QJsonValue &part : object.value(QStringLiteral("command")).toArray())
            type.command << part.toString();
        type.origin = origin;
        if (type.patterns.isEmpty())
            continue;
        if (!kOpenModes.contains(type.open)) {
            m_problems << QStringLiteral("%1: %2: unknown open mode '%3'").arg(file, type.name, type.open);
            continue;
        }
        // A project is shared and may come from anyone: it chooses how to show its files,
        // but it cannot make Studio run a program.
        if (origin == QStringLiteral("project") && (type.open == QStringLiteral("command") || !type.command.isEmpty())) {
            m_problems << QStringLiteral("%1: %2: a project file cannot run commands; set them in %3")
                              .arg(file, type.name, userFile());
            if (type.open == QStringLiteral("command"))
                type.open = QStringLiteral("system");
            type.command.clear();
        }
        if (type.open == QStringLiteral("command") && type.command.isEmpty()) {
            m_problems << QStringLiteral("%1: %2: open is command, but the command is empty").arg(file, type.name);
            continue;
        }
        // A later layer replaces an earlier type pattern by pattern.
        for (FileType &earlier : m_types)
            for (const QString &pattern : std::as_const(type.patterns))
                earlier.patterns.removeAll(pattern);
        if (object.value(QStringLiteral("enabled")).toBool(true))
            m_types << type;
    }
    m_types.removeIf([](const FileType &type) { return type.patterns.isEmpty(); });
    return true;
}

QStringList FileTypes::patterns() const
{
    QStringList result;
    for (const FileType &type : m_types)
        for (const QString &pattern : type.patterns)
            if (!result.contains(pattern)) result << pattern;
    return result;
}

const FileType *FileTypes::typeOf(const QString &fileName) const
{
    const QString name = QFileInfo(fileName).fileName();
    for (auto it = m_types.crbegin(); it != m_types.crend(); ++it)
        for (const QString &pattern : it->patterns)
            if (QDir::match(pattern, name)) return &*it;
    return nullptr;
}

QStringList FileTypes::expand(const QStringList &command, const QString &file, const QString &projectRoot)
{
    const QFileInfo info(file);
    const QString relative = projectRoot.isEmpty() ? info.absoluteFilePath() : QDir(projectRoot).relativeFilePath(file);
    QStringList result;
    for (QString part : command) {
        part.replace(QStringLiteral("%f"), info.absoluteFilePath());
        part.replace(QStringLiteral("%d"), info.absolutePath());
        part.replace(QStringLiteral("%r"), relative);
        result << part;
    }
    return result;
}

QString FileTypes::userFile()
{
    return QDir(QStandardPaths::writableLocation(QStandardPaths::GenericConfigLocation))
        .filePath(QStringLiteral("primula-docs/file-types.json"));
}

QString FileTypes::projectFile(const QString &projectRoot)
{
    return QDir(projectRoot).filePath(QStringLiteral(".primula-studio/file-types.json"));
}
