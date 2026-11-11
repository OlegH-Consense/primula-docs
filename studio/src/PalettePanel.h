#pragma once

// The Palette panel (stage 14.8, remark З7): the constructs of the language by
// category from CommandCatalog, with a search over forms and descriptions; since
// stage 14.13 also the functions of expressions ("Functions: Numbers"…).
// Double-click or Enter inserts the construct at the editor cursor (MainWindow
// does the insertion with Snippet::insert).

#include <QWidget>

class CommandCatalog;
class QLabel;
class QLineEdit;
class QTreeWidget;

class PalettePanel : public QWidget
{
    Q_OBJECT

public:
    explicit PalettePanel(QWidget *parent = nullptr);

    /// Show the entries of catalog (it must outlive the panel's use of it).
    void setCatalog(const CommandCatalog *catalog);
    /// Show why there is no catalogue instead of the list.
    void setError(const QString &message);
    QTreeWidget *tree() const { return m_tree; }
    QLineEdit *filter() const { return m_filter; }

signals:
    /// Insert entry index of the catalogue at the editor cursor.
    void insertRequested(int index);
    /// Open the specification at section (e.g. "4.2").
    void sectionRequested(const QString &section);
    /// Open the file of a library command at the line of its |def (stage 28.0).
    void definitionRequested(const QString &path, int line);

private:
    void fill();

    const CommandCatalog *m_catalog = nullptr;
    QLabel *m_state = nullptr;
    QLineEdit *m_filter = nullptr;
    QTreeWidget *m_tree = nullptr;
};
