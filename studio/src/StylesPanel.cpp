#include "StylesPanel.h"

#include <algorithm>

#include <QApplication>
#include <QClipboard>
#include <QHeaderView>
#include <QMenu>
#include <QJsonArray>
#include <QJsonDocument>
#include <QLabel>
#include <QLineEdit>
#include <QSet>
#include <QSplitter>
#include <QStyle>
#include <QTimer>
#include <QTreeWidget>
#include <QTreeWidgetItemIterator>
#include <QVBoxLayout>

namespace {

enum Role { PathRole = Qt::UserRole, LineRole, ColumnRole, StyleRole, IndexRole, KindRole };

QString kindTitle(const QString &kind)
{
    if (kind == QStringLiteral("paragraph")) return StylesPanel::tr("Paragraph styles");
    if (kind == QStringLiteral("character")) return StylesPanel::tr("Character styles");
    if (kind == QStringLiteral("table")) return StylesPanel::tr("Table styles");
    if (kind == QStringLiteral("list")) return StylesPanel::tr("List styles");
    if (kind == QStringLiteral("page")) return StylesPanel::tr("Page styles");
    if (kind == QStringLiteral("block")) return StylesPanel::tr("Block styles");
    return kind;
}

/// Where a layer comes from (11.7, decision 133): the "origin" of `--dump-styles`.
QString originTitle(const QString &origin)
{
    if (origin == QStringLiteral("project")) return StylesPanel::tr("project");
    if (origin == QStringLiteral("option")) return StylesPanel::tr("--style option");
    if (origin == QStringLiteral("header")) return StylesPanel::tr("document header");
    if (origin == QStringLiteral("default")) return StylesPanel::tr("built-in");
    if (origin == QStringLiteral("extends")) return StylesPanel::tr("base (extends)");
    if (origin == QStringLiteral("document")) return StylesPanel::tr("document code");
    return origin;
}

/// A property value as written in a styles module: scalars as they are, lists by spaces.
QString valueText(const QJsonValue &value)
{
    if (value.isString()) return value.toString();
    if (value.isBool()) return value.toBool() ? QStringLiteral("true") : QStringLiteral("false");
    if (value.isDouble()) return QString::number(value.toDouble());
    if (value.isNull() || value.isUndefined()) return QString();
    if (value.isArray()) {
        QStringList parts;
        for (const QJsonValue &part : value.toArray()) parts << valueText(part);
        return parts.join(QLatin1Char(' '));
    }
    return QString::fromUtf8(QJsonDocument(value.toObject()).toJson(QJsonDocument::Compact));
}

void setPlace(QTreeWidgetItem *item, const QJsonObject &where)
{
    item->setData(0, PathRole, where.value(QStringLiteral("path")).toString());
    item->setData(0, LineRole, where.value(QStringLiteral("line")).toInt());
    item->setData(0, ColumnRole, where.value(QStringLiteral("column")).toInt());
}

} // namespace

StylesPanel::StylesPanel(QWidget *parent) : QWidget(parent)
{
    m_state = new QLabel(this);
    m_state->setWordWrap(true);
    m_state->setStyleSheet(QStringLiteral("color: #b45309"));
    m_state->hide();
    m_filter = new QLineEdit(this);
    m_filter->setObjectName(QStringLiteral("stylesFilter"));
    m_filter->setPlaceholderText(tr("Filter styles"));
    m_filter->setClearButtonEnabled(true);
    m_styles = new QTreeWidget(this);
    m_styles->setObjectName(QStringLiteral("stylesTree"));
    m_styles->setHeaderLabels({tr("Style"), tr("Parent")});
    m_styles->header()->setSectionResizeMode(QHeaderView::Interactive);
    m_styles->setColumnWidth(0, 180);
    m_properties = new QTreeWidget(this);
    m_properties->setObjectName(QStringLiteral("styleProperties"));
    m_properties->setHeaderLabels({tr("Property"), tr("Value"), tr("Set in")});
    m_properties->setRootIsDecorated(true);
    m_properties->header()->setSectionResizeMode(QHeaderView::Interactive);
    m_properties->header()->setStretchLastSection(false);
    // The columns share the width of the panel (fitColumns on every resize), so «Set in»
    // stays visible in a narrow dock; the user may still drag the borders.
    m_properties->installEventFilter(this);
    auto *splitter = new QSplitter(Qt::Vertical, this);
    splitter->addWidget(m_styles);
    splitter->addWidget(m_properties);
    auto *layout = new QVBoxLayout(this);
    layout->setContentsMargins(0, 0, 0, 0);
    layout->addWidget(m_state);
    layout->addWidget(m_filter);
    layout->addWidget(splitter, 1);

    connect(m_filter, &QLineEdit::textChanged, this, &StylesPanel::fill);
    connect(m_styles, &QTreeWidget::currentItemChanged, this, [this](QTreeWidgetItem *item) { showProperties(item); });
    auto navigate = [this](QTreeWidgetItem *item) {
        const QString path = item->data(0, PathRole).toString();
        if (!path.isEmpty())
            emit navigateRequested(path, item->data(0, LineRole).toInt(), item->data(0, ColumnRole).toInt());
    };
    connect(m_styles, &QTreeWidget::itemActivated, this, navigate);
    // Context menu of a style: apply it at the editor cursor or remove it there (14.7),
    // go to the definition, the parent, copy the name.
    m_styles->setContextMenuPolicy(Qt::CustomContextMenu);
    connect(m_styles, &QWidget::customContextMenuRequested, this, [this, navigate](const QPoint &point) {
        QTreeWidgetItem *item = m_styles->itemAt(point);
        if (!item || item->data(0, StyleRole).toString().isEmpty()) return;
        const QString name = item->data(0, StyleRole).toString();
        const QString parent = item->text(1);
        const QString kind = item->data(0, KindRole).toString();
        const bool applicable = kind == QStringLiteral("paragraph") || kind == QStringLiteral("character")
                                || kind == QStringLiteral("block");
        QMenu menu(this);
        QAction *apply = menu.addAction(tr("Apply %1 at the cursor").arg(name), this,
                                        [this, name, kind] { emit applyRequested(name, kind); });
        apply->setEnabled(applicable);
        if (!applicable) apply->setText(tr("Apply %1 (set by style= of its command)").arg(name));
        menu.addAction(tr("Remove %1 at the cursor").arg(name), this, [this, name] { emit removeRequested(name); })
            ->setEnabled(applicable);
        menu.addSeparator();
        menu.addAction(tr("Go to the definition"), this, [item, navigate] { navigate(item); })
            ->setEnabled(!item->data(0, PathRole).toString().isEmpty());
        menu.addAction(tr("Select the parent style %1").arg(parent), this, [this, parent] { selectStyle(parent); })
            ->setEnabled(!parent.isEmpty());
        menu.addAction(tr("Copy the name"), this, [name] { QApplication::clipboard()->setText(name); });
        menu.exec(m_styles->viewport()->mapToGlobal(point));
    });
    connect(m_properties, &QTreeWidget::itemActivated, this, navigate);
}

void StylesPanel::setStyles(const QJsonObject &styles)
{
    m_data = styles;
    m_state->hide();
    fill();
}

void StylesPanel::setStale(const QString &reason)
{
    m_state->setText(tr("Outdated: %1").arg(reason));
    m_state->setToolTip(reason);
    m_state->show();
}

void StylesPanel::clear()
{
    m_data = {};
    m_state->hide();
    fill();
}

void StylesPanel::fill()
{
    // Keep the selected style and the open groups over a refresh.
    const QString selected = m_styles->currentItem() ? m_styles->currentItem()->data(0, StyleRole).toString() : QString();
    QSet<QString> collapsed;
    bool first = m_styles->topLevelItemCount() == 0;
    for (int i = 0; i < m_styles->topLevelItemCount(); ++i)
        if (!m_styles->topLevelItem(i)->isExpanded()) collapsed.insert(m_styles->topLevelItem(i)->text(0));
    m_styles->clear();
    m_properties->clear();
    if (m_data.isEmpty()) return;
    const QString filter = m_filter->text().trimmed();
    const QJsonArray styles = m_data.value(QStringLiteral("styles")).toArray();

    // Layers: lowest first, as the translator applies them; a layer opens at its first definition.
    if (filter.isEmpty()) {
        auto *layers = new QTreeWidgetItem(m_styles, {tr("Layers")});
        for (const QJsonValue &value : m_data.value(QStringLiteral("layers")).toArray()) {
            const QString name = value.toObject().value(QStringLiteral("name")).toString();
            auto *item = new QTreeWidgetItem(layers, {name, originTitle(value.toObject().value(QStringLiteral("origin")).toString())});
            for (const QJsonValue &style : styles)
                for (const QJsonValue &definition : style.toObject().value(QStringLiteral("definitions")).toArray())
                    if (definition.toObject().value(QStringLiteral("layer")).toString() == name
                        && item->data(0, PathRole).toString().isEmpty()) {
                        setPlace(item, definition.toObject());
                        item->setData(0, LineRole, 1);
                        item->setToolTip(0, definition.toObject().value(QStringLiteral("path")).toString());
                    }
        }
        layers->setExpanded(!collapsed.contains(layers->text(0)) && !first);
        auto *defaults = new QTreeWidgetItem(m_styles, {tr("Document defaults")});
        const QJsonObject values = m_data.value(QStringLiteral("defaults")).toObject();
        for (auto it = values.begin(); it != values.end(); ++it)
            new QTreeWidgetItem(defaults, {it.key(), valueText(it.value())});
        defaults->setExpanded(!collapsed.contains(defaults->text(0)) && !first);
    }

    QHash<QString, QTreeWidgetItem *> groups;
    for (int index = 0; index < styles.size(); ++index) {
        const QJsonObject style = styles.at(index).toObject();
        const QString name = style.value(QStringLiteral("name")).toString();
        if (!filter.isEmpty() && !name.contains(filter, Qt::CaseInsensitive)) continue;
        const QString kind = style.value(QStringLiteral("kind")).toString();
        QTreeWidgetItem *&group = groups[kind];
        if (!group) {
            group = new QTreeWidgetItem(m_styles, {kindTitle(kind)});
            group->setExpanded(!filter.isEmpty() || first || !collapsed.contains(group->text(0)));
        }
        auto *item = new QTreeWidgetItem(group, {name, style.value(QStringLiteral("parent")).toString()});
        item->setData(0, StyleRole, name);
        item->setData(0, IndexRole, index);
        item->setData(0, KindRole, kind);
        // A style opens at its highest definition: the layer that decides it.
        const QJsonArray definitions = style.value(QStringLiteral("definitions")).toArray();
        if (!definitions.isEmpty()) setPlace(item, definitions.last().toObject());
        QStringList tip{name};
        for (const QJsonValue &definition : definitions)
            tip << tr("defined in %1, line %2").arg(definition.toObject().value(QStringLiteral("layer")).toString())
                       .arg(definition.toObject().value(QStringLiteral("line")).toInt());
        if (style.value(QStringLiteral("materialized")).toBool()) {
            QFont font = item->font(0);
            font.setItalic(true);
            item->setFont(0, font);
            tip << tr("made by the translator (derive, variant)");
        }
        if (style.value(QStringLiteral("broken")).toBool()) {
            item->setIcon(0, this->style()->standardIcon(QStyle::SP_MessageBoxWarning));
            tip << tr("broken: Build → Check document shows why");
        }
        item->setToolTip(0, tip.join(QLatin1Char('\n')));
        if (name == selected) m_styles->setCurrentItem(item);
    }
    for (QTreeWidgetItem *group : std::as_const(groups)) group->sortChildren(0, Qt::AscendingOrder);
}

void StylesPanel::showProperties(QTreeWidgetItem *item)
{
    m_properties->clear();
    if (!item || item->data(0, StyleRole).toString().isEmpty()) return;
    const QJsonObject style = m_data.value(QStringLiteral("styles")).toArray()
                                  .at(item->data(0, IndexRole).toInt()).toObject();
    const QString name = style.value(QStringLiteral("name")).toString();
    QFont bold = m_properties->font();
    bold.setBold(true);

    auto *own = new QTreeWidgetItem(m_properties, {tr("Own")});
    own->setFont(0, bold);
    const QJsonObject ownProps = style.value(QStringLiteral("own")).toObject();
    for (auto it = ownProps.begin(); it != ownProps.end(); ++it) {
        const QJsonObject entry = it.value().toObject();
        const QString layer = entry.value(QStringLiteral("layer")).toString();
        auto *row = new QTreeWidgetItem(own, {it.key(), valueText(entry.value(QStringLiteral("value"))),
                                              layer.isEmpty() ? tr("translator") : layer});
        setPlace(row, entry);
        setRowTip(row, QStringLiteral("%1:%2").arg(entry.value(QStringLiteral("path")).toString())
                           .arg(entry.value(QStringLiteral("line")).toInt()));
    }
    // Effective values the style does not set itself: inherited along the parent chain.
    auto *inherited = new QTreeWidgetItem(m_properties, {tr("Inherited")});
    inherited->setFont(0, bold);
    const QJsonObject effective = style.value(QStringLiteral("effective")).toObject();
    for (auto it = effective.begin(); it != effective.end(); ++it) {
        const QJsonObject entry = it.value().toObject();
        const QString from = entry.value(QStringLiteral("from")).toString();
        if (from == name && ownProps.contains(it.key())) continue;
        auto *row = new QTreeWidgetItem(inherited, {it.key(), valueText(entry.value(QStringLiteral("value"))), from});
        setRowTip(row, QString());
    }
    const QStringList chain = [&] {
        QStringList names;
        for (const QJsonValue &value : style.value(QStringLiteral("chain")).toArray()) names << value.toString();
        return names;
    }();
    inherited->setToolTip(0, chain.join(QStringLiteral(" → ")));
    if (inherited->childCount() == 0) delete inherited;
    m_properties->expandAll();
}

void StylesPanel::setRowTip(QTreeWidgetItem *row, const QString &place)
{
    // All three columns in one tip: a narrow panel may cut any of them.
    QString tip = QStringLiteral("%1 = %2\n%3: %4").arg(row->text(0), row->text(1), tr("Set in"), row->text(2));
    if (!place.isEmpty()) tip += QStringLiteral(" (%1)").arg(place);
    for (int column = 0; column < 3; ++column) row->setToolTip(column, tip);
}

void StylesPanel::fitColumns()
{
    // Property 40 %, value 35 %, «Set in» the rest of the visible width.
    const int width = m_properties->viewport()->width();
    if (width <= 0) return;
    m_properties->setColumnWidth(0, width * 40 / 100);
    m_properties->setColumnWidth(1, width * 35 / 100);
    m_properties->setColumnWidth(2, width - width * 40 / 100 - width * 35 / 100);
}

bool StylesPanel::eventFilter(QObject *watched, QEvent *event)
{
    if (watched == m_properties && event->type() == QEvent::Resize)
        QTimer::singleShot(0, this, &StylesPanel::fitColumns);   // after the viewport got its size
    return QWidget::eventFilter(watched, event);
}

bool StylesPanel::selectStyle(const QString &name)
{
    for (QTreeWidgetItemIterator it(m_styles); *it; ++it) {
        if ((*it)->data(0, StyleRole).toString() == name) {
            m_styles->setCurrentItem(*it);
            m_styles->scrollToItem(*it);
            return true;
        }
    }
    return false;
}

QList<QPair<QString, QString>> StylesPanel::styleList() const
{
    QList<QPair<QString, QString>> list;
    for (const QJsonValue &value : m_data.value(QStringLiteral("styles")).toArray())
        list.append({value.toObject().value(QStringLiteral("name")).toString(),
                     value.toObject().value(QStringLiteral("kind")).toString()});
    return list;
}

QList<QPair<QString, QString>> StylesPanel::inlineStyleDescriptions() const
{
    QList<QPair<QString, QString>> list;
    for (const QJsonValue &value : m_data.value(QStringLiteral("styles")).toArray()) {
        const QJsonObject style = value.toObject();
        const QString kind = style.value(QStringLiteral("kind")).toString();
        if (kind != QStringLiteral("paragraph") && kind != QStringLiteral("character")) continue;
        const QString parent = style.value(QStringLiteral("parent")).toString();
        QString description = kind == QStringLiteral("paragraph") ? tr("paragraph style") : tr("character style");
        if (!parent.isEmpty()) description += QStringLiteral(" ← ") + parent;
        list.append({style.value(QStringLiteral("name")).toString(), description});
    }
    std::sort(list.begin(), list.end());
    return list;
}
