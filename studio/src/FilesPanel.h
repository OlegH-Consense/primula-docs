#pragma once

// The «Files» panel (stage 14.3а, remark З1): the files of the project root,
// opened on request instead of opening every fragment at once.

#include <QWidget>

class QFileSystemModel;
class QTreeView;

class FilesPanel : public QWidget
{
    Q_OBJECT

public:
    explicit FilesPanel(QWidget *parent = nullptr);
    /// Show the files under root; an empty root clears the panel.
    void setRoot(const QString &root);
    /// The patterns of the files shown (file types, item С2); directories are always shown.
    void setNameFilters(const QStringList &patterns);
    /// Select path in the tree (the active editor) without opening it.
    void reveal(const QString &path);
    /// The shown root (empty when no project).
    QString root() const { return m_root; }

signals:
    /// A file was activated (double click or Enter).
    void openRequested(const QString &path);
    /// The context menu is asked for path (a file or a directory; the root for empty space).
    void contextMenuRequested(const QString &path, const QPoint &globalPosition);

private:
    QFileSystemModel *m_model = nullptr;
    QTreeView *m_view = nullptr;
    QString m_root;
};
