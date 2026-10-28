#include "PalettePanel.h"

#include "CommandCatalog.h"
#include "Snippet.h"

#include <QApplication>
#include <QClipboard>
#include <QFontDatabase>
#include <QMenu>
#include <QHeaderView>
#include <QLabel>
#include <QLineEdit>
#include <QTreeWidget>
#include <QTreeWidgetItemIterator>
#include <QVBoxLayout>

namespace {
constexpr int IndexRole = Qt::UserRole;
}

PalettePanel::PalettePanel(QWidget *parent) : QWidget(parent)
{
    m_state = new QLabel(this);
    m_state->setWordWrap(true);
    m_state->setStyleSheet(QStringLiteral("color: #b45309"));
    m_state->hide();
    m_filter = new QLineEdit(this);
    m_filter->setObjectName(QStringLiteral("paletteFilter"));
    m_filter->setPlaceholderText(tr("Search constructs and functions"));
    m_filter->setClearButtonEnabled(true);
    m_tree = new QTreeWidget(this);
    m_tree->setObjectName(QStringLiteral("paletteTree"));
    m_tree->setHeaderLabels({tr("Construct"), tr("Description")});
    m_tree->header()->setSectionResizeMode(QHeaderView::Interactive);
    m_tree->header()->setStretchLastSection(false);
    m_tree->setTextElideMode(Qt::ElideNone);
    m_tree->setColumnWidth(0, 130);
    m_tree->setColumnWidth(1, 420);
    auto *layout = new QVBoxLayout(this);
    layout->setContentsMargins(0, 0, 0, 0);
    layout->addWidget(m_state);
    layout->addWidget(m_filter);
    layout->addWidget(m_tree, 1);

    connect(m_filter, &QLineEdit::textChanged, this, &PalettePanel::fill);
    // Enter in the search field inserts the first visible construct.
    connect(m_filter, &QLineEdit::returnPressed, this, [this] {
        for (QTreeWidgetItemIterator it(m_tree); *it; ++it)
            if ((*it)->data(0, IndexRole).isValid()) {
                emit insertRequested((*it)->data(0, IndexRole).toInt());
                return;
            }
    });
    connect(m_tree, &QTreeWidget::itemActivated, this, [this](QTreeWidgetItem *item) {
        if (item->data(0, IndexRole).isValid()) emit insertRequested(item->data(0, IndexRole).toInt());
    });
    // Context menu of a construct: insert, copy the form or the template, open its section.
    m_tree->setContextMenuPolicy(Qt::CustomContextMenu);
    connect(m_tree, &QWidget::customContextMenuRequested, this, [this](const QPoint &point) {
        QTreeWidgetItem *item = m_tree->itemAt(point);
        if (!item || !item->data(0, IndexRole).isValid() || !m_catalog) return;
        const int index = item->data(0, IndexRole).toInt();
        const CommandCatalog::Entry entry = m_catalog->entries().at(index);
        auto copy = [](const QString &text) { QApplication::clipboard()->setText(text); };
        QMenu menu(this);
        menu.addAction(tr("Insert at the cursor"), this, [this, index] { emit insertRequested(index); });
        menu.addSeparator();
        menu.addAction(entry.function ? tr("Copy the name %1").arg(entry.label) : tr("Copy the form %1").arg(entry.label),
                       this, [copy, entry] { copy(entry.label); });
        menu.addAction(tr("Copy the template"), this, [copy, entry] {
            copy(Snippet::expand(entry.snippet).text);
        });
        menu.addSeparator();
        menu.addAction(entry.section.isEmpty() ? tr("Specification section") : CommandCatalog::sectionLabel(entry.section),
                       this, [this, entry] { emit sectionRequested(entry.section); })
            ->setEnabled(!entry.section.isEmpty());
        menu.exec(m_tree->viewport()->mapToGlobal(point));
    });
}

void PalettePanel::setCatalog(const CommandCatalog *catalog)
{
    m_catalog = catalog;
    m_state->hide();
    fill();
}

void PalettePanel::setError(const QString &message)
{
    m_state->setText(message);
    m_state->show();
}

void PalettePanel::fill()
{
    m_tree->clear();
    if (!m_catalog) return;
    const QString filter = m_filter->text().trimmed();
    // The constructs, then the functions of expressions (14.13) under "Functions: …".
    QList<CommandCatalog::Category> categories = m_catalog->categories();
    for (CommandCatalog::Category category : m_catalog->functionCategories()) {
        category.title = tr("Functions: %1").arg(category.title);
        categories.append(category);
    }
    for (const CommandCatalog::Category &category : categories) {
        QTreeWidgetItem *group = nullptr;
        const QList<CommandCatalog::Entry> &entries = m_catalog->entries();
        for (int index = 0; index < entries.size(); ++index) {
            const CommandCatalog::Entry &entry = entries.at(index);
            if (entry.category != category.id) continue;
            if (!filter.isEmpty() && !entry.label.contains(filter, Qt::CaseInsensitive)
                && !entry.summary.contains(filter, Qt::CaseInsensitive))
                continue;
            if (!group) {
                group = new QTreeWidgetItem(m_tree, {category.title});
                QFont font = group->font(0);
                font.setBold(true);
                group->setFont(0, font);
                group->setFirstColumnSpanned(true);
            }
            auto *item = new QTreeWidgetItem(group, {entry.label, entry.summary});
            // Forms like |,{…} and |.{…} differ by one punctuation sign: a fixed font keeps them apart.
            item->setFont(0, QFontDatabase::systemFont(QFontDatabase::FixedFont));
            item->setData(0, IndexRole, index);
            item->setToolTip(0, entry.tooltip);
            item->setToolTip(1, entry.tooltip);
        }
        if (group) group->setExpanded(true);
    }
}
