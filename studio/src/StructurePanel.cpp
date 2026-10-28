#include "StructurePanel.h"

#include <QApplication>
#include <QClipboard>
#include <QColor>
#include <QFileInfo>
#include <QMenu>
#include <QHeaderView>
#include <QJsonObject>
#include <QLabel>
#include <QScrollBar>
#include <QSet>
#include <QTreeWidget>
#include <QTreeWidgetItemIterator>
#include <QVBoxLayout>

namespace {

enum Role { PathRole = Qt::UserRole, LineRole, ColumnRole, NumberRole, IdRole };

/// Nesting rank of an item: an item becomes a child of the nearest earlier item of a
/// smaller rank. Headings rank by level, appendices as top headings, clauses below
/// any heading; tables, figures and the rest are leaves (-1).
int rank(const QJsonObject &item)
{
    const QString kind = item.value(QStringLiteral("kind")).toString();
    if (kind == QStringLiteral("heading")) return item.value(QStringLiteral("level")).toInt(1);
    if (kind == QStringLiteral("appendix")) return 1;
    if (kind == QStringLiteral("clause")) return 100 + item.value(QStringLiteral("level")).toInt(1);
    return -1;
}

/// Ids of the tracks of a |parallel item, separated by " | " (7.7).
QString trackList(const QJsonObject &item)
{
    QStringList ids;
    for (const QJsonValue &track : item.value(QStringLiteral("tracks")).toArray())
        ids << track.toObject().value(QStringLiteral("id")).toString();
    return ids.join(QStringLiteral(" | "));
}

QString text(const QJsonObject &item)
{
    const QString kind = item.value(QStringLiteral("kind")).toString();
    const QString number = item.value(QStringLiteral("number")).toString();
    const QString title = item.value(QStringLiteral("title")).toString();
    const QString id = item.value(QStringLiteral("id")).toString();
    auto joined = [](const QString &a, const QString &b) {
        return a.isEmpty() ? b : b.isEmpty() ? a : a + QLatin1Char(' ') + b;
    };
    if (kind == QStringLiteral("heading")) return joined(number, title);
    if (kind == QStringLiteral("clause")) return joined(number, item.value(QStringLiteral("text")).toString());
    if (kind == QStringLiteral("appendix"))
        return joined(item.value(QStringLiteral("designation")).toString(), title);
    if (kind == QStringLiteral("table")) return joined(StructurePanel::tr("Table %1").arg(number).trimmed(), title);
    if (kind == QStringLiteral("figure")) return joined(StructurePanel::tr("Figure %1").arg(number).trimmed(), title);
    if (kind == QStringLiteral("list")) return StructurePanel::tr("Numbered list %1").arg(id);
    if (kind == QStringLiteral("section")) return StructurePanel::tr("Section %1").arg(id);
    if (kind == QStringLiteral("admonition")) return StructurePanel::tr("Note %1").arg(id);
    // Parallel tracks (7.7): the environment, its segments and the blocks of the tracks.
    if (kind == QStringLiteral("parallel")) return StructurePanel::tr("Parallel tracks: %1").arg(trackList(item));
    const QString status = item.value(QStringLiteral("status")).toString();
    const QString state = status.isEmpty() ? QString() : QStringLiteral(" [%1]").arg(status);
    if (kind == QStringLiteral("segment")) {
        if (item.value(QStringLiteral("span")).toString() == QStringLiteral("all"))
            return StructurePanel::tr("Full-width segment");
        return StructurePanel::tr("Segment %1").arg(id.isEmpty() ? QStringLiteral("—") : id) + state;
    }
    if (kind == QStringLiteral("track_block")) {
        QString result = StructurePanel::tr("Track %1").arg(item.value(QStringLiteral("track")).toString()) + state;
        if (item.value(QStringLiteral("stale")).toBool()) result += StructurePanel::tr(" — outdated");
        else if (item.value(QStringLiteral("changed")).toBool()) result += StructurePanel::tr(" — changed after confirmation");
        return result;
    }
    return joined(kind, id);
}

} // namespace

StructurePanel::StructurePanel(QWidget *parent) : QWidget(parent)
{
    m_state = new QLabel(this);
    m_state->setWordWrap(true);
    m_state->setStyleSheet(QStringLiteral("color: #b45309"));
    m_state->hide();
    m_tree = new QTreeWidget(this);
    m_tree->setObjectName(QStringLiteral("structureTree"));
    // Visible, mouse-resizable columns and no eliding: clause texts are long, and a
    // horizontal scroll bar is clearer than "1.2 Замовлення — по…". The full text is
    // also in the tooltip.
    m_tree->setHeaderLabels({tr("Element"), tr("File")});
    m_tree->setTextElideMode(Qt::ElideNone);
    m_tree->setHorizontalScrollBarPolicy(Qt::ScrollBarAsNeeded);
    m_tree->header()->setStretchLastSection(false);
    m_tree->header()->setSectionResizeMode(QHeaderView::Interactive);
    m_tree->setColumnWidth(0, 520);
    m_tree->setColumnWidth(1, 160);
    auto *layout = new QVBoxLayout(this);
    layout->setContentsMargins(0, 0, 0, 0);
    layout->addWidget(m_state);
    layout->addWidget(m_tree);
    connect(m_tree, &QTreeWidget::itemActivated, this, [this](QTreeWidgetItem *item) {
        emit navigateRequested(item->data(0, PathRole).toString(), item->data(0, LineRole).toInt(),
                               item->data(0, ColumnRole).toInt());
    });
    // Context menu: copy the number, the ID or a ready cross-reference |@("id") (section 5.4).
    m_tree->setContextMenuPolicy(Qt::CustomContextMenu);
    connect(m_tree, &QWidget::customContextMenuRequested, this, [this](const QPoint &point) {
        QTreeWidgetItem *item = m_tree->itemAt(point);
        if (!item) return;
        const QString number = item->data(0, NumberRole).toString();
        const QString id = item->data(0, IdRole).toString();
        const QString reference = QStringLiteral("|@(\"%1\")").arg(id);
        auto copy = [](const QString &text) { QApplication::clipboard()->setText(text); };
        QMenu menu(this);
        menu.addAction(tr("Go to the line"), this, [this, item] { emit m_tree->itemActivated(item, 0); });
        menu.addAction(id.isEmpty() ? tr("Insert a reference (no ID)") : tr("Insert the reference %1 at the cursor").arg(reference),
                       this, [this, reference] { emit insertRequested(reference); })->setEnabled(!id.isEmpty());
        menu.addSeparator();
        menu.addAction(number.isEmpty() ? tr("Copy the number") : tr("Copy the number %1").arg(number), this,
                       [copy, number] { copy(number); })->setEnabled(!number.isEmpty());
        menu.addAction(id.isEmpty() ? tr("Copy a reference (no ID)") : tr("Copy the reference %1").arg(reference), this,
                       [copy, reference] { copy(reference); })->setEnabled(!id.isEmpty());
        menu.addAction(tr("Copy the ID"), this, [copy, id] { copy(id); })->setEnabled(!id.isEmpty());
        menu.exec(m_tree->viewport()->mapToGlobal(point));
    });
}

void StructurePanel::setStructure(const QString &document, const QJsonArray &items)
{
    // Keep the open branches and the scroll position over a refresh: the tree is
    // rebuilt after every pause in typing.
    QSet<QString> collapsed;
    for (QTreeWidgetItemIterator it(m_tree); *it; ++it)
        if ((*it)->childCount() > 0 && !(*it)->isExpanded()) collapsed.insert((*it)->text(0));
    const int scroll = m_tree->verticalScrollBar() ? m_tree->verticalScrollBar()->value() : 0;
    const bool sameDocument = document == m_document;

    m_tree->clear();
    m_followed = nullptr;
    m_document = document;
    m_state->hide();
    QList<QPair<int, QTreeWidgetItem *>> stack;
    QString primary;   // the primary track of the last |parallel (7.7)
    for (const QJsonValue &value : items) {
        const QJsonObject item = value.toObject();
        const QString kind = item.value(QStringLiteral("kind")).toString();
        if (kind == QStringLiteral("parallel")) primary = item.value(QStringLiteral("primary")).toString();
        const int r = rank(item);
        while (!stack.isEmpty() && (r < 0 ? false : stack.last().first >= r)) stack.removeLast();
        QTreeWidgetItem *parent = stack.isEmpty() ? nullptr : stack.last().second;
        auto *node = parent ? new QTreeWidgetItem(parent) : new QTreeWidgetItem(m_tree);
        const QString path = item.value(QStringLiteral("path")).toString();
        // An element of a non-primary track is marked with its track: «[en] 2. Subject».
        const QString track = item.value(QStringLiteral("track")).toString();
        const bool own = !track.isEmpty() && track != primary && kind != QStringLiteral("track_block");
        node->setText(0, own ? QStringLiteral("[%1] %2").arg(track, text(item)) : text(item));
        if (kind == QStringLiteral("track_block") && (item.value(QStringLiteral("stale")).toBool()
                                                      || item.value(QStringLiteral("changed")).toBool()))
            node->setForeground(0, QColor(0xb4, 0x53, 0x09));
        if (QFileInfo(path) != QFileInfo(document)) node->setText(1, QFileInfo(path).fileName());
        node->setData(0, PathRole, path);
        node->setData(0, LineRole, item.value(QStringLiteral("line")).toInt());
        node->setData(0, ColumnRole, item.value(QStringLiteral("column")).toInt());
        node->setData(0, NumberRole, item.value(QStringLiteral("kind")).toString() == QStringLiteral("appendix")
                                         ? item.value(QStringLiteral("designation")).toString()
                                         : item.value(QStringLiteral("number")).toString());
        node->setData(0, IdRole, item.value(QStringLiteral("id")).toString());
        QStringList tip{node->text(0), QStringLiteral("%1:%2").arg(item.value(QStringLiteral("file")).toString())
                                           .arg(item.value(QStringLiteral("line")).toInt())};
        if (!item.value(QStringLiteral("id")).toString().isEmpty())
            tip << QStringLiteral("id: %1").arg(item.value(QStringLiteral("id")).toString());
        node->setToolTip(0, tip.join(QLatin1Char('\n')));
        node->setToolTip(1, path);
        if (r >= 0) stack.append({r, node});
    }
    // Clauses stay folded on a first show: a contract has hundreds of them.
    for (QTreeWidgetItemIterator it(m_tree); *it; ++it)
        (*it)->setExpanded(sameDocument ? !collapsed.contains((*it)->text(0)) : (*it)->parent() == nullptr);
    if (sameDocument && m_tree->verticalScrollBar()) m_tree->verticalScrollBar()->setValue(scroll);
}

void StructurePanel::setStale(const QString &reason)
{
    m_state->setText(tr("Outdated: %1").arg(reason));
    m_state->setToolTip(reason);
    m_state->show();
}

void StructurePanel::clear()
{
    m_tree->clear();
    m_followed = nullptr;
    m_document.clear();
    m_state->hide();
}

void StructurePanel::followCursor(const QString &path, int line)
{
    QTreeWidgetItem *best = nullptr;
    for (QTreeWidgetItemIterator it(m_tree); *it; ++it)
        if (QFileInfo((*it)->data(0, PathRole).toString()) == QFileInfo(path) && (*it)->data(0, LineRole).toInt() <= line)
            best = *it;   // items come in document order
    if (!best || best == m_followed) return;
    m_followed = best;
    const QSignalBlocker blocker(m_tree);
    m_tree->setCurrentItem(best);
    m_tree->scrollToItem(best);
}
