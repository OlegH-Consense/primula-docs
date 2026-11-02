#include "BackupsDialog.h"

#include <QDesktopServices>
#include <QDir>
#include <QHBoxLayout>
#include <QHeaderView>
#include <QLabel>
#include <QLocale>
#include <QMenu>
#include <QMessageBox>
#include <QPushButton>
#include <QTreeWidget>
#include <QUrl>
#include <QVBoxLayout>

namespace {
constexpr int kInfoRole = Qt::UserRole;      // snapshot index in the top-level item
constexpr int kFileRole = Qt::UserRole + 1;  // file index in a child item
}

BackupsDialog::BackupsDialog(const QString &projectRoot, QWidget *parent) : QDialog(parent), m_root(projectRoot)
{
    setWindowTitle(tr("Backups of the project"));
    setObjectName(QStringLiteral("backupsDialog"));
    resize(820, 520);
    auto *layout = new QVBoxLayout(this);
    m_summary = new QLabel(this);
    m_summary->setObjectName(QStringLiteral("backupsSummary"));
    m_summary->setWordWrap(true);
    layout->addWidget(m_summary);
    m_tree = new QTreeWidget(this);
    m_tree->setObjectName(QStringLiteral("backupsTree"));
    m_tree->setHeaderLabels({tr("Time"), tr("Reason"), tr("Note"), tr("Size")});
    m_tree->setRootIsDecorated(true);
    m_tree->setContextMenuPolicy(Qt::CustomContextMenu);
    m_tree->header()->setSectionResizeMode(QHeaderView::ResizeToContents);
    m_tree->header()->setStretchLastSection(false);
    m_tree->header()->setSectionResizeMode(2, QHeaderView::Stretch);
    layout->addWidget(m_tree, 1);
    auto *buttons = new QHBoxLayout;
    auto *now = new QPushButton(tr("Back up the project now"), this);
    m_compare = new QPushButton(tr("Compare with the current file…"), this);
    m_restore = new QPushButton(tr("Restore this version"), this);
    m_delete = new QPushButton(tr("Delete the backup"), this);
    auto *folder = new QPushButton(tr("Open the folder"), this);
    auto *close = new QPushButton(tr("Close"), this);
    for (QPushButton *button : {now, m_compare, m_restore, m_delete, folder}) buttons->addWidget(button);
    buttons->addStretch();
    buttons->addWidget(close);
    layout->addLayout(buttons);
    connect(now, &QPushButton::clicked, this, &BackupsDialog::backupNowRequested);
    connect(m_compare, &QPushButton::clicked, this, [this] {
        BackupInfo info; BackupFile file;
        if (selected(&info, &file, true)) emit compareRequested(info, file);
    });
    connect(m_restore, &QPushButton::clicked, this, [this] {
        BackupInfo info; BackupFile file;
        if (selected(&info, &file, true)) emit restoreRequested(info, file);
    });
    connect(m_delete, &QPushButton::clicked, this, &BackupsDialog::deleteSelected);
    connect(folder, &QPushButton::clicked, this, [this] {
        QDir().mkpath(Backups::directory(m_root));
        QDesktopServices::openUrl(QUrl::fromLocalFile(Backups::directory(m_root)));
    });
    connect(close, &QPushButton::clicked, this, &QDialog::accept);
    connect(m_tree, &QTreeWidget::itemSelectionChanged, this, &BackupsDialog::updateButtons);
    connect(m_tree, &QTreeWidget::customContextMenuRequested, this, &BackupsDialog::contextMenu);
    reload();
}

QString BackupsDialog::reasonName(const QString &reason)
{
    if (reason == QStringLiteral("before-ai-apply")) return tr("Before applying AI edits");
    if (reason == QStringLiteral("before-save")) return tr("Before saving");
    if (reason == QStringLiteral("before-restore")) return tr("Before a restore");
    if (reason == QStringLiteral("manual")) return tr("Manual");
    return reason;
}

void BackupsDialog::reload()
{
    m_backups = Backups::list(m_root);
    m_tree->clear();
    qint64 total = 0;
    for (int i = 0; i < m_backups.size(); ++i) {
        const BackupInfo &info = m_backups.at(i);
        total += info.size();
        auto *top = new QTreeWidgetItem(m_tree, {QLocale().toString(info.created, QLocale::ShortFormat), reasonName(info.reason),
                                                  info.note.section(QLatin1Char('\n'), 0, 0),
                                                  QLocale().formattedDataSize(info.size())});
        top->setData(0, kInfoRole, i);
        for (int f = 0; f < info.files.size(); ++f) {
            auto *child = new QTreeWidgetItem(top, {QDir(m_root).relativeFilePath(info.files.at(f).source), QString(), QString(),
                                                    QLocale().formattedDataSize(info.files.at(f).size)});
            child->setData(0, kInfoRole, i);
            child->setData(0, kFileRole, f);
        }
        if (info.files.size() == 1) top->setToolTip(0, info.files.first().source);
    }
    m_summary->setText(m_backups.isEmpty()
                           ? tr("There are no backups yet. They are made before AI edits are applied and on request; "
                                "«Back up the project now» copies the source files of the project.")
                           : tr("%n backup(s), %1 in all. Restoring a version first makes a backup of the current file.",
                                nullptr, int(m_backups.size())).arg(QLocale().formattedDataSize(total)));
    if (m_tree->topLevelItemCount() > 0) m_tree->setCurrentItem(m_tree->topLevelItem(0));
    updateButtons();
}

bool BackupsDialog::selected(BackupInfo *info, BackupFile *file, bool needFile)
{
    QTreeWidgetItem *item = m_tree->currentItem();
    if (!item) {
        QMessageBox::information(this, windowTitle(), tr("Choose a backup in the list."));
        return false;
    }
    *info = m_backups.at(item->data(0, kInfoRole).toInt());
    if (!needFile) return true;
    if (item->data(0, kFileRole).isValid()) {
        *file = info->files.at(item->data(0, kFileRole).toInt());
    } else if (info->files.size() == 1) {
        *file = info->files.first();
    } else {
        QMessageBox::information(this, windowTitle(), tr("This backup holds %n file(s): choose one of them.", nullptr, int(info->files.size())));
        return false;
    }
    return true;
}

void BackupsDialog::updateButtons()
{
    const bool any = m_tree->currentItem() != nullptr;
    m_compare->setEnabled(any);
    m_restore->setEnabled(any);
    m_delete->setEnabled(any);
}

void BackupsDialog::deleteSelected()
{
    BackupInfo info;
    BackupFile file;
    if (!selected(&info, &file, false)) return;
    if (QMessageBox::question(this, windowTitle(), tr("Delete the backup of %1?").arg(QLocale().toString(info.created, QLocale::ShortFormat)))
        != QMessageBox::Yes)
        return;
    QString error;
    if (!Backups::remove(info, &error)) QMessageBox::warning(this, windowTitle(), error);
    reload();
}

void BackupsDialog::contextMenu(const QPoint &position)
{
    if (QTreeWidgetItem *item = m_tree->itemAt(position)) m_tree->setCurrentItem(item);
    QMenu menu(this);
    const bool any = m_tree->currentItem() != nullptr;
    QAction *compare = menu.addAction(tr("Compare with the current file…"));
    QAction *restore = menu.addAction(tr("Restore this version"));
    QAction *remove = menu.addAction(tr("Delete the backup"));
    for (QAction *action : {compare, restore, remove}) action->setEnabled(any);
    menu.addSeparator();
    QAction *now = menu.addAction(tr("Back up the project now"));
    QAction *picked = menu.exec(m_tree->viewport()->mapToGlobal(position));
    if (picked == compare) m_compare->click();
    else if (picked == restore) m_restore->click();
    else if (picked == remove) deleteSelected();
    else if (picked == now) emit backupNowRequested();
}
