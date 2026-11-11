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
#include <QStandardPaths>
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
    flat.remove(QLatin1Char(':'));    // "C:/dir" of Windows: a colon is not allowed in a file name
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

namespace {

/// A unified diff (3 lines of context) made in-process, for systems without `diff` (Windows).
/// Common head and tail are cut first; the middle is matched by the longest common
/// subsequence, and a middle too large for the table is shown as one replaced block.
QString builtInDiff(const QByteArray &before, const QByteArray &after, const QString &beforeLabel,
                    const QString &afterLabel)
{
    auto lines = [](const QByteArray &data) {
        QStringList list = QString::fromUtf8(data).split(QLatin1Char('\n'));
        if (!list.isEmpty() && list.last().isEmpty()) list.removeLast();    // the end of the last line
        return list;
    };
    const QStringList a = lines(before);
    const QStringList b = lines(after);
    const int na = a.size(), nb = b.size();
    int head = 0;
    while (head < na && head < nb && a[head] == b[head]) ++head;
    int tail = 0;
    while (tail < na - head && tail < nb - head && a[na - 1 - tail] == b[nb - 1 - tail]) ++tail;
    if (head == na && head == nb) return {};
    const int ma = na - head - tail, mb = nb - head - tail;
    // Operations of the middle: ' ' equal, '-' removed, '+' added; with the text of the line.
    QList<QPair<QChar, QString>> middle;
    if (qint64(ma) * mb <= 4000000) {
        QList<int> table((ma + 1) * (mb + 1), 0);
        auto at = [&](int i, int j) -> int & { return table[i * (mb + 1) + j]; };
        for (int i = ma - 1; i >= 0; --i)
            for (int j = mb - 1; j >= 0; --j)
                at(i, j) = a[head + i] == b[head + j] ? at(i + 1, j + 1) + 1 : qMax(at(i + 1, j), at(i, j + 1));
        int i = 0, j = 0;
        while (i < ma || j < mb) {
            if (i < ma && j < mb && a[head + i] == b[head + j]) { middle.append({QLatin1Char(' '), a[head + i]}); ++i; ++j; }
            else if (j < mb && (i == ma || at(i, j + 1) > at(i + 1, j))) { middle.append({QLatin1Char('+'), b[head + j]}); ++j; }
            else { middle.append({QLatin1Char('-'), a[head + i]}); ++i; }
        }
    } else {
        for (int i = 0; i < ma; ++i) middle.append({QLatin1Char('-'), a[head + i]});
        for (int j = 0; j < mb; ++j) middle.append({QLatin1Char('+'), b[head + j]});
    }
    // The whole file as operations, then hunks around the changes.
    QList<QPair<QChar, QString>> all;
    for (int i = 0; i < head; ++i) all.append({QLatin1Char(' '), a[i]});
    all += middle;
    for (int i = na - tail; i < na; ++i) all.append({QLatin1Char(' '), a[i]});
    constexpr int Context = 3;
    QString out = QStringLiteral("--- %1\n+++ %2\n").arg(beforeLabel, afterLabel);
    int index = 0;
    const int total = all.size();
    while (index < total) {
        while (index < total && all[index].first == QLatin1Char(' ')) ++index;
        if (index >= total) break;
        const int start = qMax(0, index - Context);
        int end = index, lastChange = index;
        while (end < total && end - lastChange <= 2 * Context) {
            if (all[end].first != QLatin1Char(' ')) lastChange = end;
            ++end;
        }
        end = qMin(total, lastChange + Context + 1);
        int fromA = 1, fromB = 1, countA = 0, countB = 0;
        for (int k = 0; k < start; ++k) {
            if (all[k].first != QLatin1Char('+')) ++fromA;
            if (all[k].first != QLatin1Char('-')) ++fromB;
        }
        QString body;
        for (int k = start; k < end; ++k) {
            body += all[k].first + all[k].second + QLatin1Char('\n');
            if (all[k].first != QLatin1Char('+')) ++countA;
            if (all[k].first != QLatin1Char('-')) ++countB;
        }
        out += QStringLiteral("@@ -%1,%2 +%3,%4 @@\n").arg(fromA).arg(countA).arg(fromB).arg(countB) + body;
        index = end;
    }
    return out;
}

} // namespace

QString Backups::unifiedDiff(const QByteArray &before, const QByteArray &after, const QString &beforeLabel,
                             const QString &afterLabel, QString *error)
{
    if (QStandardPaths::findExecutable(QStringLiteral("diff")).isEmpty())
        return builtInDiff(before, after, beforeLabel, afterLabel);    // Windows has no diff
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
