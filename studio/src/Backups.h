#pragma once

// Backup copies of the files of a project (stage 25.1): snapshots in `.primula-studio/backups/`,
// made before the edits of AI are applied, before a file is saved (an option), before a restore,
// and on demand. A snapshot is a directory `YYYYMMDD-HHMMSS-mmm-REASON/` with the copies of the
// files at their relative paths and `backup.json` (reason, note, time, hashes). Files outside the
// project are stored under `_external/` and restored to their own path.

#include <QByteArray>
#include <QDateTime>
#include <QList>
#include <QString>
#include <QStringList>

struct BackupFile
{
    QString source;   ///< absolute path of the file when the copy was made
    QString stored;   ///< path of the copy inside the snapshot directory
    QString sha256;
    qint64 size = 0;
};

struct BackupInfo
{
    QString id;          ///< the name of the snapshot directory
    QString directory;   ///< its absolute path
    QString reason;      ///< "manual", "before-ai-apply", "before-save", "before-restore"
    QString note;
    QDateTime created;
    QList<BackupFile> files;
    qint64 size() const;
};

namespace Backups {

/// One file to put into a snapshot: its path and the bytes (the text of an editor or the file).
struct Item
{
    QString path;
    QByteArray data;
};

/// `<project>/.primula-studio/backups`.
QString directory(const QString &projectRoot);

/// Make a snapshot of the items.
/// @param duplicate  set when the newest snapshot of the same reason holds the same files with the same
///                   contents: nothing is written then, and the result is that snapshot's directory.
/// @return the directory of the snapshot, or empty with error.
QString create(const QString &projectRoot, const QList<Item> &items, const QString &reason, const QString &note,
               QString *error, bool *duplicate = nullptr);

/// The snapshots, the newest first; a directory without a valid `backup.json` is skipped.
QList<BackupInfo> list(const QString &projectRoot);

/// The bytes of a copy; empty when it is missing.
QByteArray read(const BackupInfo &info, const BackupFile &file);

/// Delete a snapshot. @return false with error on failure.
bool remove(const BackupInfo &info, QString *error);

/// Delete the oldest automatic snapshots beyond `keep`; "manual" ones are never deleted.
/// @return the number of deleted snapshots.
int prune(const QString &projectRoot, int keep);

/// The source files of a project (text of documents, modules, data, notes), without service,
/// build and version-control directories and without files above 5 MB.
QStringList sourceFiles(const QString &projectRoot);

/// `diff -u` of two texts, with the labels in the header; empty when they are the same.
/// @param error  receives the reason when `diff` could not be run.
QString unifiedDiff(const QByteArray &before, const QByteArray &after, const QString &beforeLabel,
                    const QString &afterLabel, QString *error);

} // namespace Backups
