#pragma once
#include <QDialog>

class QTextBrowser;
class QLineEdit;

class HelpDialog : public QDialog
{
    Q_OBJECT
public:
    explicit HelpDialog(const QString &language, QWidget *parent = nullptr);
    /// Show a Markdown resource instead of the user guide (the specification).
    HelpDialog(const QString &resource, const QString &title, QWidget *parent);
    /// Scroll to the heading of section ("4.2" — the heading "4.2. …"); false when absent.
    bool showSection(const QString &section);
    QTextBrowser *browser() const { return m_browser; }
    /// Context help (F1): the window title names the text the section was opened for and a
    /// line above the text says so; an empty context restores the plain title (the menu).
    void setContext(const QString &context, const QString &note);
    QString context() const { return m_context; }
private:
    QString m_title;
    QString m_context;
    class QLabel *m_contextLine = nullptr;
    void build(const QString &markdown);
    QTextBrowser *m_browser = nullptr;
    QLineEdit *m_search = nullptr;
    void findNext();
};
