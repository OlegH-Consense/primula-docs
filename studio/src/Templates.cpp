#include "Templates.h"

#include <QCoreApplication>
#include <QDir>
#include <QFile>
#include <QFileInfo>
#include <QJsonArray>
#include <QJsonDocument>
#include <QRegularExpression>
#include <QSaveFile>
#include <QStandardPaths>

#include <algorithm>

QString FileTemplate::title(const QString &language) const
{
    const QString text = titles.value(language).toString();
    return text.isEmpty() ? titles.value(QStringLiteral("en")).toString() : text;
}

QString FileTemplate::description(const QString &language) const
{
    const QString text = descriptions.value(language).toString();
    return text.isEmpty() ? descriptions.value(QStringLiteral("en")).toString() : text;
}

namespace Templates {

namespace {

bool readTemplate(const QString &directory, bool user, FileTemplate *result)
{
    QFile file(QDir(directory).filePath(QStringLiteral("template.json")));
    if (!file.open(QIODevice::ReadOnly))
        return false;
    const QJsonObject data = QJsonDocument::fromJson(file.readAll()).object();
    FileTemplate tpl;
    tpl.id = QFileInfo(directory).fileName();
    tpl.kind = data.value(QStringLiteral("kind")).toString();
    tpl.order = data.value(QStringLiteral("order")).toInt();
    tpl.directory = directory;
    tpl.user = user;
    tpl.titles = data.value(QStringLiteral("title")).toObject();
    tpl.descriptions = data.value(QStringLiteral("description")).toObject();
    tpl.strings = data.value(QStringLiteral("strings")).toObject();
    for (const QJsonValue &value : data.value(QStringLiteral("files")).toArray()) {
        const QJsonObject entry = value.toObject();
        tpl.files.append({entry.value(QStringLiteral("from")).toString(), entry.value(QStringLiteral("to")).toString(),
                          entry.value(QStringLiteral("open")).toBool()});
    }
    if (!kinds().contains(tpl.kind) || tpl.files.isEmpty())
        return false;
    *result = tpl;
    return true;
}

} // namespace

QStringList kinds()
{
    return {QStringLiteral("document"), QStringLiteral("fragment"), QStringLiteral("module"),
            QStringLiteral("styles"), QStringLiteral("project"), QStringLiteral("order")};
}

QString userDirectory()
{
    return QDir(QStandardPaths::writableLocation(QStandardPaths::GenericConfigLocation))
        .filePath(QStringLiteral("primula-docs/templates"));
}

QList<FileTemplate> available(const QString &kind)
{
    QHash<QString, FileTemplate> byId;
    for (const auto &[root, user] : {std::pair{QStringLiteral(":/templates"), false}, std::pair{userDirectory(), true}}) {
        const QDir directory(root);
        for (const QString &entry : directory.entryList(QDir::Dirs | QDir::NoDotAndDotDot, QDir::Name)) {
            FileTemplate tpl;
            if (readTemplate(directory.filePath(entry), user, &tpl) && (kind.isEmpty() || tpl.kind == kind))
                byId.insert(tpl.id, tpl);   // a user template replaces a built-in one
        }
    }
    QList<FileTemplate> result = byId.values();
    std::sort(result.begin(), result.end(), [](const FileTemplate &a, const FileTemplate &b) {
        return a.kind != b.kind ? kinds().indexOf(a.kind) < kinds().indexOf(b.kind)
             : a.order != b.order ? a.order < b.order : a.id < b.id;
    });
    return result;
}

QString languageTag(const QString &language)
{
    if (language == QStringLiteral("ru")) return QStringLiteral("ru-RU");
    if (language == QStringLiteral("en")) return QStringLiteral("en-US");
    return QStringLiteral("uk-UA");
}

QString fill(const QString &text, const QHash<QString, QString> &values, const QJsonObject &strings)
{
    static const QRegularExpression placeholder(QStringLiteral("\\{\\{([A-Za-z0-9_.]+)\\}\\}"));
    QString result;
    qsizetype last = 0;
    auto matches = placeholder.globalMatch(text);
    while (matches.hasNext()) {
        const auto match = matches.next();
        const QString key = match.captured(1);
        result += text.mid(last, match.capturedStart() - last);
        if (key.startsWith(QStringLiteral("s.")) && strings.contains(key.mid(2)))
            result += strings.value(key.mid(2)).toString();
        else if (values.contains(key))
            result += values.value(key);
        else
            result += match.captured();
        last = match.capturedEnd();
    }
    return result + text.mid(last);
}

QStringList plannedFiles(const FileTemplate &tpl, const QString &directory, const QHash<QString, QString> &values)
{
    QStringList result;
    for (const TemplateFile &file : tpl.files)
        result.append(QDir::cleanPath(QDir(directory).filePath(fill(file.to, values, {}))));
    return result;
}

bool instantiate(const FileTemplate &tpl, const QString &directory, const QHash<QString, QString> &values,
                 const QString &language, QStringList *created, QStringList *toOpen, QString *errorMessage)
{
    const QJsonObject strings = tpl.strings.value(language).toObject().isEmpty()
        ? tpl.strings.value(QStringLiteral("en")).toObject() : tpl.strings.value(language).toObject();
    const QStringList targets = plannedFiles(tpl, directory, values);
    for (const QString &target : targets) {
        if (QFileInfo::exists(target)) {
            if (errorMessage)
                *errorMessage = QCoreApplication::translate("Templates", "The file already exists: %1").arg(target);
            return false;
        }
    }
    QStringList written;
    for (int i = 0; i < tpl.files.size(); ++i) {
        QFile source(QDir(tpl.directory).filePath(tpl.files.at(i).from));
        QString error;
        if (!source.open(QIODevice::ReadOnly)) {
            error = QCoreApplication::translate("Templates", "Cannot read the template file %1").arg(source.fileName());
        } else if (!QDir().mkpath(QFileInfo(targets.at(i)).absolutePath())) {
            error = QCoreApplication::translate("Templates", "Cannot create %1").arg(QFileInfo(targets.at(i)).absolutePath());
        } else {
            QSaveFile target(targets.at(i));
            const QByteArray text = fill(QString::fromUtf8(source.readAll()), values, strings).toUtf8();
            if (!target.open(QIODevice::WriteOnly) || target.write(text) != text.size() || !target.commit())
                error = target.errorString();
        }
        if (!error.isEmpty()) {
            // Leave nothing half made.
            for (const QString &path : std::as_const(written)) QFile::remove(path);
            if (errorMessage) *errorMessage = error;
            return false;
        }
        written.append(targets.at(i));
        if (tpl.files.at(i).open && toOpen) toOpen->append(targets.at(i));
    }
    if (created) *created = written;
    return true;
}

} // namespace Templates
