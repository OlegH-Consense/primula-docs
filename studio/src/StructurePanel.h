#pragma once

// The Structure panel (stage 14.6): headings, clauses, appendices, tables, figures,
// lists and labelled blocks of a document from `primula check --dump-structure`
// (specification 14.1, Т1). Studio does not parse Primula: the tree is built only
// from the dump. Items of fragments show their file name.

#include <QJsonArray>
#include <QWidget>

class QLabel;
class QTreeWidget;
class QTreeWidgetItem;

class StructurePanel : public QWidget
{
    Q_OBJECT

public:
    explicit StructurePanel(QWidget *parent = nullptr);

    /// Show the structure of a document.
    /// @param document  absolute path of the document; items of other files show their name.
    /// @param items  the `structure.items` array of the dump.
    void setStructure(const QString &document, const QJsonArray &items);
    /// Keep the last tree but mark it outdated (the dump failed); reason is the tooltip.
    void setStale(const QString &reason);
    /// Empty the panel (no project or no document).
    void clear();
    /// Select the last item of file path at or before line (the place of the editor cursor).
    void followCursor(const QString &path, int line);
    QString document() const { return m_document; }
    QTreeWidget *tree() const { return m_tree; }

signals:
    void navigateRequested(const QString &path, int line, int column);
    /// Insert text (a reference |@("id")) at the editor cursor.
    void insertRequested(const QString &text);

private:
    QTreeWidgetItem *m_followed = nullptr;
    QLabel *m_state = nullptr;
    QTreeWidget *m_tree = nullptr;
    QString m_document;
};
