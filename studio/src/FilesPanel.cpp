#include "FilesPanel.h"

#include <QFileSystemModel>
#include <QHeaderView>
#include <QTreeView>
#include <QVBoxLayout>

FilesPanel::FilesPanel(QWidget *parent) : QWidget(parent)
{
    m_model = new QFileSystemModel(this);
    // Directories always; files of the kinds a Primula project uses. Hidden
    // entries (.git, .primula-studio) stay hidden: the AI context has a menu item.
    m_model->setFilter(QDir::AllDirs | QDir::Files | QDir::NoDotAndDotDot);
    m_model->setNameFilters({QStringLiteral("*.prml"), QStringLiteral("*.yaml"), QStringLiteral("*.yml"),
                             QStringLiteral("*.csv"), QStringLiteral("*.json"), QStringLiteral("*.md"),
                             QStringLiteral("*.txt"), QStringLiteral("*.svg"), QStringLiteral("*.png"),
                             QStringLiteral("*.jpg"), QStringLiteral("*.jpeg"), QStringLiteral("*.pdf"),
                             QStringLiteral("*.odt")});
    m_model->setNameFilterDisables(false);
    m_view = new QTreeView(this);
    m_view->setObjectName(QStringLiteral("filesTree"));
    m_view->setModel(m_model);
    m_view->setHeaderHidden(true);
    for (int column = 1; column < m_model->columnCount(); ++column)
        m_view->hideColumn(column);
    m_view->setRootIsDecorated(true);
    auto *layout = new QVBoxLayout(this);
    layout->setContentsMargins(0, 0, 0, 0);
    layout->addWidget(m_view);
    connect(m_view, &QTreeView::activated, this, [this](const QModelIndex &index) {
        if (!m_model->isDir(index))
            emit openRequested(m_model->filePath(index));
    });
    // New, copy, rename and delete are offered by the window (remark З9).
    m_view->setContextMenuPolicy(Qt::CustomContextMenu);
    connect(m_view, &QWidget::customContextMenuRequested, this, [this](const QPoint &point) {
        if (m_root.isEmpty()) return;
        const QModelIndex index = m_view->indexAt(point);
        emit contextMenuRequested(index.isValid() ? m_model->filePath(index) : m_root,
                                  m_view->viewport()->mapToGlobal(point));
    });
    setRoot({});
}

void FilesPanel::setRoot(const QString &root)
{
    m_root = root;
    if (root.isEmpty()) {
        m_view->setRootIndex(m_model->setRootPath(QString()));
        m_view->setEnabled(false);
        return;
    }
    m_view->setEnabled(true);
    m_view->setRootIndex(m_model->setRootPath(root));
}

void FilesPanel::setNameFilters(const QStringList &patterns)
{
    m_model->setNameFilters(patterns);
}

void FilesPanel::reveal(const QString &path)
{
    const QModelIndex index = m_model->index(path);
    if (!index.isValid())
        return;
    m_view->setCurrentIndex(index);
    m_view->scrollTo(index);
}
