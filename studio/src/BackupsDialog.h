#pragma once

// The list of backup copies of a project (stage 25.1): File → Backups → Show backups…
// The dialog only shows and asks; MainWindow does the work (compare, restore, new backup).

#include "Backups.h"

#include <QDialog>

class QLabel;
class QPushButton;
class QTreeWidget;
class QTreeWidgetItem;

class BackupsDialog : public QDialog
{
    Q_OBJECT

public:
    explicit BackupsDialog(const QString &projectRoot, QWidget *parent = nullptr);
    /// Read the snapshots again.
    void reload();
    /// The name of a reason for the list ("before-ai-apply" → "Before applying AI edits").
    static QString reasonName(const QString &reason);

signals:
    void backupNowRequested();
    void compareRequested(const BackupInfo &info, const BackupFile &file);
    void restoreRequested(const BackupInfo &info, const BackupFile &file);

private:
    QString m_root;
    QList<BackupInfo> m_backups;
    QTreeWidget *m_tree = nullptr;
    QLabel *m_summary = nullptr;
    QPushButton *m_compare = nullptr;
    QPushButton *m_restore = nullptr;
    QPushButton *m_delete = nullptr;

    /// The snapshot and the file of the selected row; false (with a message) when a file cannot be chosen.
    bool selected(BackupInfo *info, BackupFile *file, bool needFile);
    void updateButtons();
    void deleteSelected();
    void contextMenu(const QPoint &position);
};
