#include "FileMonitor.h"
#include <QFileInfo>
#include <QDir>
#include <QSet>
FileMonitor::FileMonitor(QObject *parent) : QObject(parent)
{
    m_debounce.setSingleShot(true); m_debounce.setInterval(250);
    connect(&m_watcher, &QFileSystemWatcher::fileChanged, this, [this] { m_debounce.start(); });
    connect(&m_watcher, &QFileSystemWatcher::directoryChanged, this, [this] { m_debounce.start(); });
    connect(&m_debounce, &QTimer::timeout, this, [this] { rearm(); emit checkRequested(); });
    m_poll.setInterval(3000);
    connect(&m_poll, &QTimer::timeout, this, [this] { rearm(); emit checkRequested(); });
}
void FileMonitor::setFiles(const QStringList &paths)
{
    m_paths = paths; m_paths.removeDuplicates();
    if (!m_watcher.files().isEmpty()) m_watcher.removePaths(m_watcher.files());
    if (!m_watcher.directories().isEmpty()) m_watcher.removePaths(m_watcher.directories());
    m_debounce.stop(); rearm();
    if (m_paths.isEmpty()) m_poll.stop(); else m_poll.start();
}
void FileMonitor::rearm()
{
    QSet<QString> paths;
    for (const QString &file : m_paths) {
        if (QFileInfo(file).isFile()) paths.insert(file);
        QDir dir = QFileInfo(file).absoluteDir();
        // cdUp() can fail when the parent also does not exist. Walk lexically
        // so a missing resource below several missing directories never loops.
        while (!dir.exists() && !dir.isRoot()) {
            const QString parent = QFileInfo(dir.absolutePath()).absolutePath();
            if (parent == dir.absolutePath()) break;
            dir.setPath(parent);
        }
        paths.insert(dir.absolutePath());
    }
    const auto watched = m_watcher.files() + m_watcher.directories();
    QStringList add;
    for (const QString &path : paths) if (!watched.contains(path)) add.append(path);
    if (!add.isEmpty()) m_watcher.addPaths(add);
}
