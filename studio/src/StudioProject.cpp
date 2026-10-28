#include "StudioProject.h"

#include "Translator.h"

#include <QCoreApplication>
#include <QDir>
#include <QFile>
#include <QFileInfo>
#include <QJsonArray>
#include <QJsonDocument>
#include <QSaveFile>

namespace {

const QString kProjectFileName = QStringLiteral("project.p.prml");
const QString kServiceDirectory = QStringLiteral(".primula-studio");

QString clean(const QString &path)
{
    return QDir::cleanPath(QFileInfo(path).absoluteFilePath());
}

} // namespace

QString StudioProject::findProjectFile(const QString &path)
{
    const QFileInfo info(path);
    if (info.isFile() && info.fileName().endsWith(QStringLiteral(".p.prml")))
        return clean(path);
    QDir directory = info.isDir() ? QDir(info.absoluteFilePath()) : info.absoluteDir();
    while (true) {
        const QString candidate = directory.filePath(kProjectFileName);
        if (QFileInfo(candidate).isFile())
            return clean(candidate);
        // The search stops after the directory of a repository (10.6).
        if (QFileInfo(directory.filePath(QStringLiteral(".git"))).exists() || !directory.cdUp())
            return {};
    }
}

bool StudioProject::open(const QString &path, QString *errorMessage)
{
    *this = StudioProject();
    const QString opened = clean(path);
    const QString projectFile = findProjectFile(opened);
    QString root = QFileInfo(opened).absolutePath();
    QString name = QFileInfo(opened).completeBaseName();
    if (!projectFile.isEmpty()) {
        QString error;
        const QJsonObject dump = Translator::dumpProject(projectFile, &error);
        if (dump.isEmpty()) {
            if (errorMessage) *errorMessage = error;
            return false;
        }
        for (const QJsonValue &value : dump.value(QStringLiteral("messages")).toArray())
            m_messages.append(value.toObject());
        // An invalid header gives messages but no root: the project cannot be used.
        if (!dump.contains(QStringLiteral("root"))) {
            if (errorMessage) {
                QStringList texts;
                for (const QJsonObject &message : std::as_const(m_messages))
                    texts.append(message.value(QStringLiteral("message")).toString());
                *errorMessage = texts.join(QLatin1Char('\n'));
            }
            return false;
        }
        root = dump.value(QStringLiteral("root")).toString();
        const QString projectName = dump.value(QStringLiteral("name")).toString();
        name = projectName.isEmpty() ? QFileInfo(QFileInfo(projectFile).absolutePath()).fileName() : projectName;
        const QDir rootDirectory(root);
        const QDir projectDirectory = QFileInfo(projectFile).absoluteDir();
        for (const QJsonValue &value : dump.value(QStringLiteral("targets")).toArray()) {
            const QJsonObject target = value.toObject();
            BuildTarget entry;
            entry.source = clean(rootDirectory.filePath(target.value(QStringLiteral("source")).toString()));
            entry.output = clean(rootDirectory.filePath(target.value(QStringLiteral("output")).toString()));
            const QJsonValue pdf = target.value(QStringLiteral("pdf"));
            // `build --pdf` of a project writes every PDF next to its ODT (14.1).
            entry.pdf = pdf.isString() ? clean(rootDirectory.filePath(pdf.toString()))
                                       : entry.output.left(entry.output.size() - 4) + QStringLiteral(".pdf");
            m_targets.append(entry);
        }
        m_language = dump.value(QStringLiteral("language")).toString();
        m_declaresStyles = !dump.value(QStringLiteral("styles")).toArray().isEmpty();
        for (const QJsonValue &value : dump.value(QStringLiteral("styles")).toArray()) {
            const QString module = value.toString();
            if (!module.startsWith(QStringLiteral("std/")))
                m_styles.append(clean(projectDirectory.filePath(module)));
        }
    }
    m_opened = opened;
    m_projectFile = projectFile;
    m_root = clean(root);
    m_name = name;
    QFile settings(settingsPath());
    if (settings.open(QIODevice::ReadOnly))
        m_settings = QJsonDocument::fromJson(settings.readAll()).object();
    return true;
}

QString StudioProject::primaryDocument() const
{
    if (!m_opened.endsWith(QStringLiteral(".p.prml")))
        return m_opened;
    return m_targets.isEmpty() ? QString() : m_targets.first().source;
}

BuildTarget StudioProject::outputsFor(const QString &document) const
{
    const QString path = clean(document);
    for (const BuildTarget &target : m_targets)
        if (target.source == path)
            return target;
    // A document that is not a target is built into build/ of the root, not next to the source.
    QString stem = QFileInfo(path).fileName();
    if (stem.endsWith(QStringLiteral(".prml")))
        stem.chop(5);
    BuildTarget result;
    result.source = path;
    result.output = clean(QDir(m_root).filePath(QStringLiteral("build/") + stem + QStringLiteral(".odt")));
    result.pdf = result.output.left(result.output.size() - 4) + QStringLiteral(".pdf");
    return result;
}

bool StudioProject::isTarget(const QString &document) const
{
    const QString path = clean(document);
    for (const BuildTarget &target : m_targets)
        if (target.source == path)
            return true;
    return false;
}

QString StudioProject::relative(const QString &path) const
{
    const QString absolutePath = clean(path);
    const QString result = QDir(m_root).relativeFilePath(absolutePath);
    if (result == QStringLiteral("..") || result.startsWith(QStringLiteral("../")))
        return absolutePath;
    return result;
}

QString StudioProject::absolute(const QString &path) const
{
    return QFileInfo(path).isAbsolute() ? clean(path) : clean(QDir(m_root).filePath(path));
}

QString StudioProject::serviceDirectory() const { return QDir(m_root).filePath(kServiceDirectory); }
QString StudioProject::settingsPath() const { return QDir(serviceDirectory()).filePath(QStringLiteral("settings.json")); }
QString StudioProject::aiContextPath() const { return QDir(serviceDirectory()).filePath(QStringLiteral("ai-context.md")); }
QString StudioProject::aiHistoryDirectory() const { return QDir(serviceDirectory()).filePath(QStringLiteral("ai-history")); }

QString StudioProject::sessionKey() const
{
    return relative(m_opened);
}

QJsonObject StudioProject::session() const
{
    return m_settings.value(QStringLiteral("sessions")).toObject().value(sessionKey()).toObject();
}

void StudioProject::setSession(const QJsonObject &state)
{
    QJsonObject sessions = m_settings.value(QStringLiteral("sessions")).toObject();
    sessions.insert(sessionKey(), state);
    m_settings.insert(QStringLiteral("sessions"), sessions);
}

QJsonObject StudioProject::group(const QString &name) const
{
    return m_settings.value(name).toObject();
}

void StudioProject::setGroup(const QString &name, const QJsonObject &value)
{
    m_settings.insert(name, value);
}

bool StudioProject::saveSettings(QString *errorMessage) const
{
    if (!isOpen())
        return false;
    if (!QDir().mkpath(serviceDirectory())) {
        if (errorMessage)
            *errorMessage = QCoreApplication::translate("StudioProject", "Cannot create %1").arg(serviceDirectory());
        return false;
    }
    QJsonObject data = m_settings;
    data.insert(QStringLiteral("schema"), 1);
    QSaveFile file(settingsPath());
    if (!file.open(QIODevice::WriteOnly)) {
        if (errorMessage) *errorMessage = file.errorString();
        return false;
    }
    file.write(QJsonDocument(data).toJson(QJsonDocument::Indented));
    if (!file.commit()) {
        if (errorMessage) *errorMessage = file.errorString();
        return false;
    }
    return true;
}

bool StudioProject::ensureAiContext(QString *errorMessage) const
{
    if (QFileInfo::exists(aiContextPath()))
        return true;
    if (!QDir().mkpath(serviceDirectory())) {
        if (errorMessage)
            *errorMessage = QCoreApplication::translate("StudioProject", "Cannot create %1").arg(serviceDirectory());
        return false;
    }
    QSaveFile file(aiContextPath());
    if (!file.open(QIODevice::WriteOnly)) {
        if (errorMessage) *errorMessage = file.errorString();
        return false;
    }
    file.write(QCoreApplication::translate("StudioProject",
        "# AI context of the project\n\nWhat the AI should know about these documents: purpose, parties, terms, "
        "style of language.\n").toUtf8());
    if (!file.commit()) {
        if (errorMessage) *errorMessage = file.errorString();
        return false;
    }
    return true;
}
