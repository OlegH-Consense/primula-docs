#pragma once

// The Styles panel (stage 14.6): the style system of a document from
// `primula check --dump-styles` (specification 14.1, Т2). Above — the styles
// grouped by kind with a name filter, plus the layers and the document defaults;
// below — the properties of the selected style: its own ones (with the layer that
// sets them) and the inherited effective ones (with the style they come from).
// The context menu applies a style at the editor cursor or removes it (stage 14.7,
// the edit itself is StyleEditing).

#include <QJsonObject>
#include <QWidget>

class QLabel;
class QLineEdit;
class QTreeWidget;
class QTreeWidgetItem;

class StylesPanel : public QWidget
{
    Q_OBJECT

public:
    explicit StylesPanel(QWidget *parent = nullptr);

    /// Show the `styles` object of a dump (layers, modules, defaults, styles).
    void setStyles(const QJsonObject &styles);
    /// Keep the last list but mark it outdated (the dump failed); reason is the tooltip.
    void setStale(const QString &reason);
    void clear();
    /// Select a style by name; false when there is no such style.
    bool selectStyle(const QString &name);
    QTreeWidget *styleTree() const { return m_styles; }
    QTreeWidget *propertyTree() const { return m_properties; }
    /// Name and kind (`paragraph`, `character`…) of every style of the last dump, in dump order.
    QList<QPair<QString, QString>> styleList() const;
    /// Paragraph and character styles (those written as |.Name) with a short description:
    /// the kind and the parent, for hints and completion.
    QList<QPair<QString, QString>> inlineStyleDescriptions() const;

signals:
    void navigateRequested(const QString &path, int line, int column);
    /// Apply style name of kind (the dump `kind`) at the editor cursor.
    void applyRequested(const QString &name, const QString &kind);
    /// Remove the application of style name around the editor cursor.
    void removeRequested(const QString &name);

protected:
    bool eventFilter(QObject *watched, QEvent *event) override;

private:
    /// Share the width of the properties among the three columns (40/35/25 %).
    void fitColumns();
    /// One tip with property, value and «Set in» (and its place) on every column of row.
    void setRowTip(QTreeWidgetItem *row, const QString &place);
    void fill();
    void showProperties(QTreeWidgetItem *item);

    QJsonObject m_data;
    QLabel *m_state = nullptr;
    QLineEdit *m_filter = nullptr;
    QTreeWidget *m_styles = nullptr;
    QTreeWidget *m_properties = nullptr;
};
