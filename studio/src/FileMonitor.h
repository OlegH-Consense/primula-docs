#pragma once

// Open-resource watcher, not a recursive project/home-directory scanner.
#include <QObject>
#include <QFileSystemWatcher>
#include <QTimer>
class FileMonitor : public QObject
{
    Q_OBJECT
public:
    explicit FileMonitor(QObject *parent = nullptr);
    /// Watch these open-resource paths and nearest existing parents, replacing the previous set.
    void setFiles(const QStringList &paths);
signals:
    void checkRequested();
private:
    QFileSystemWatcher m_watcher;
    QTimer m_debounce;
    QTimer m_poll;
    QStringList m_paths;
    /// Reattach watches after atomic replacements; polling covers events lost by the platform watcher.
    void rearm();
};
