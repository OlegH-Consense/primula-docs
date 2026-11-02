#include "Backups.h"

#include <QCryptographicHash>
#include <QDir>
#include <QDirIterator>
#include <QFile>
#include <QFileInfo>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QProcess>
#include <QSaveFile>
#include <QTemporaryDir>

namespace {

const QString kManifest = QStringLiteral("backup.json");
const qint64 kMaxFileSize = 5 * 1024 * 1024;

QString hashOf(const QByteArray &data)
{
    return QString::fromLatin1(QCryptographicHash::hash(data, QCryptographicHash::Sha256).toHex());
}

/// The path of a copy inside a snapshot: relative to the project, or under `_external/`.
QString storedName(const QString &root, const QString &path)
{
    const QString absolute = QFileInfo(path).absoluteFilePath();
    const QString relative = QDir(root).relativeFilePath(absolute);
    if (!relative.startsWith(QStringLiteral("..")) && !QFileInfo(relative).isAbsolute())
        return relative;
    QString flat = absolute;
    while (flat.startsWith(QLatin1Char('/'))) flat.remove(0, 1);
    return QStringLiteral("_external/") + flat;
}

QString slug(const QString &reason)
{
    QString result;
    for (const QChar c : reason) result += c.isLetterOrNumber() || c == QLatin1Char('-') ? c : QLatin1Char('-');
    return result.isEmpty() ? QStringLiteral("backup") : result;
}

bool readManifest(const QString &directory, BackupInfo *info)
{
    QFile file(QDir(directory).filePath(kManifest));
    if (!file.open(QIODevice::ReadOnly)) return false;
    const QJsonObject object = QJsonDocument::fromJson(file.readAll()).object();
    if (object.value(QStringLiteral("schema")).toInt() != 1) return false;
    info->directory = directory;
    info->id = QFileInfo(directory).fileName();
    info->reason = object.value(QStringLiteral("reason")).toString();
    info->note = object.value(QStringLiteral("note")).toString();
    info->created = QDateTime::fromString(object.value(QStringLiteral("created")).toString(), Qt::ISODateWithMs);
    info->files.clear();
    for (const QJsonValue &value : object.value(QStringLiteral("files")).toArray()) {
        const QJsonObject entry = value.toObject();
        BackupFile item;
        item.source = entry.value(QStringLiteral("source")).toString();
        item.stored = entry.value(QStringLiteral("stored")).toString();
        item.sha256 = entry.value(QStringLiteral("sha256")).toString();
        item.size = entry.value(QStringLiteral("size")).toInteger();
        info->files.append(item);
    }
    return !info->files.isEmpty();
}

} // namespace

qint64 BackupInfo::size() const
{
    qint64 total = 0;
    for (const BackupFile &file : files) total += file.size;
    return total;
}

QString Backups::directory(const QString &projectRoot)
{
    return QDir(projectRoot).filePath(QStringLiteral(".primula-studio/backups"));
}

QString Backups::create(const QString &projectRoot, const QList<Item> &items, const QString &reason, const QString &note,
                        QString *error, bool *duplicate)
{
    if (duplicate) *duplicate = false;
    if (items.isEmpty()) {
        if (error) *error = QStringLiteral("no files");
        return {};
    }
    // The same files with the same contents as the newest snapshot of this reason: nothing new to keep.
    const QList<BackupInfo> known = list(projectRoot);
    for (const BackupInfo &previous : known) {
        if (previous.reason != reason) continue;
        bool same = previous.files.size() == items.size();
        for (int i = 0; same && i < items.size(); ++i) {
            const QString source = QFileInfo(items.at(i).path).absoluteFilePath();
            bool found = false;
            for (const BackupFile &file : previous.files)
                found = found || (file.source == source && file.sha256 == hashOf(items.at(i).data));
            same = found;
        }
        if (same) {
            if (duplicate) *duplicate = true;
            return previous.directory;
        }
        break;   // only the newest of this reason is compared
    }
    const QDateTime now = QDateTime::currentDateTime();
    const QString base = now.toString(QStringLiteral("yyyyMMdd-HHmmss-zzz")) + QLatin1Char('-') + slug(reason);
    QDir root(directory(projectRoot));
    QString name = base;
    for (int n = 2; root.exists(name); ++n) name = base + QLatin1Char('-') + QString::number(n);
    const QString snapshot = root.filePath(name);
    if (!QDir().mkpath(snapshot)) {
        if (error) *error = QStringLiteral("cannot create %1").arg(snapshot);
        return {};
    }
    QJsonArray files;
    for (const Item &item : items) {
        const QString stored = storedName(projectRoot, item.path);
        const QString target = QDir(snapshot).filePath(stored);
        QDir().mkpath(QFileInfo(target).absolutePath());
        QSaveFile out(target);
        if (!out.open(QIODevice::WriteOnly) || out.write(item.data) != item.data.size() || !out.commit()) {
            if (error) *error = QStringLiteral("cannot write %1").arg(target);
            QDir(snapshot).removeRecursively();
            return {};
        }
        files.append(QJsonObject{{QStringLiteral("source"), QFileInfo(item.path).absoluteFilePath()},
                                 {QStringLiteral("stored"), stored},
                                 {QStringLiteral("sha256"), hashOf(item.data)},
                                 {QStringLiteral("size"), qint64(item.data.size())}});
    }
    const QJsonObject manifest{{QStringLiteral("schema"), 1}, {QStringLiteral("reason"), reason},
                               {QStringLiteral("note"), note},
                               {QStringLiteral("created"), now.toString(Qt::ISODateWithMs)},
                               {QStringLiteral("files"), files}};
    QSaveFile out(QDir(snapshot).filePath(kManifest));
    if (!out.open(QIODevice::WriteOnly) || out.write(QJsonDocument(manifest).toJson()) < 0 || !out.commit()) {
        if (error) *error = QStringLiteral("cannot write the description of %1").arg(snapshot);
        QDir(snapshot).removeRecursively();
        return {};
    }
    return snapshot;
}

QList<BackupInfo> Backups::list(const QString &projectRoot)
{
    QList<BackupInfo> result;
    const QDir root(directory(projectRoot));
    for (const QString &name : root.entryList(QDir::Dirs | QDir::NoDotAndDotDot, QDir::Name | QDir::Reversed)) {
        BackupInfo info;
        if (readManifest(root.filePath(name), &info)) result.append(info);
    }
    return result;
}

QByteArray Backups::read(const BackupInfo &info, const BackupFile &file)
{
    QFile in(QDir(info.directory).filePath(file.stored));
    return in.open(QIODevice::ReadOnly) ? in.readAll() : QByteArray();
}

bool Backups::remove(const BackupInfo &info, QString *error)
{
    if (!QDir(info.directory).removeRecursively()) {
        if (error) *error = QStringLiteral("cannot delete %1").arg(info.directory);
        return false;
    }
    return true;
}

int Backups::prune(const QString &projectRoot, int keep)
{
    int automatic = 0, removed = 0;
    for (const BackupInfo &info : list(projectRoot)) {   // the newest first
        if (info.reason == QStringLiteral("manual")) continue;
        if (++automatic > keep && remove(info, nullptr)) ++removed;
    }
    return removed;
}

QStringList Backups::sourceFiles(const QString &projectRoot)
{
    static const QStringList skipped = {QStringLiteral(".primula-studio"), QStringLiteral(".git"), QStringLiteral("build"),
                                        QStringLiteral("out"), QStringLiteral("node_modules"), QStringLiteral("__pycache__")};
    static const QStringList suffixes = {QStringLiteral("prml"), QStringLiteral("yaml"), QStringLiteral("yml"), QStringLiteral("md"),
                                         QStringLiteral("txt"), QStringLiteral("csv"), QStringLiteral("json")};
    QStringList files;
    const QDir root(projectRoot);
    QDirIterator it(projectRoot, QDir::Files | QDir::NoSymLinks, QDirIterator::Subdirectories);
    while (it.hasNext()) {
        const QString path = it.next();
        const QStringList parts = root.relativeFilePath(path).split(QLatin1Char('/'));
        bool skip = false;
        for (int i = 0; i + 1 < parts.size(); ++i) skip = skip || skipped.contains(parts.at(i));
        if (!skip && suffixes.contains(QFileInfo(path).suffix().toLower()) && QFileInfo(path).size() <= kMaxFileSize)
            files.append(path);
    }
    files.sort();
    return files;
}

QString Backups::unifiedDiff(const QByteArray &before, const QByteArray &after, const QString &beforeLabel,
                             const QString &afterLabel, QString *error)
{
    QTemporaryDir directory;
    if (!directory.isValid()) {
        if (error) *error = QStringLiteral("no temporary directory");
        return {};
    }
    auto write = [&](const QString &name, const QByteArray &data) {
        QFile file(QDir(directory.path()).filePath(name));
        file.open(QIODevice::WriteOnly);
        file.write(data);
        return file.fileName();
    };
    const QString a = write(QStringLiteral("a"), before), b = write(QStringLiteral("b"), after);
    QProcess process;
    process.start(QStringLiteral("diff"), {QStringLiteral("-u"), QStringLiteral("--label"), beforeLabel,
                                           QStringLiteral("--label"), afterLabel, a, b});
    if (!process.waitForFinished(15000)) {
        process.kill();
        if (error) *error = QStringLiteral("diff did not finish");
        return {};
    }
    // diff: 0 the same, 1 different, 2 trouble.
    if (process.exitStatus() != QProcess::NormalExit || process.exitCode() > 1) {
        if (error) *error = process.errorString() + QLatin1Char(' ') + QString::fromUtf8(process.readAllStandardError());
        return {};
    }
    return QString::fromUtf8(process.readAllStandardOutput());
}
