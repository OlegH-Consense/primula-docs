#pragma once

// The list of edits that AI proposed in an answer (stage 22.3): each edit is shown with its status
// against the document, can be checked with the translator (decision D6) and applied (D7).
// The panel does not touch the document itself: MainWindow gives it the text, the check and takes
// the request to apply (a tab of an AI answer, AiHistoryPane).

#include "AiEdits.h"

#include <QWidget>
#include <functional>

class QLabel;
class QListWidget;
class QListWidgetItem;
class QPlainTextEdit;
class QPushButton;

class AiEditsPanel : public QWidget
{
    Q_OBJECT

public:
    /// The result of `primula check` of a text: the errors as "CODE message" (without the position).
    struct CheckReport
    {
        bool ran = false;       ///< false when the translator could not be run
        QString failure;        ///< the reason when it did not run
        QStringList errors;
    };
    using TextProvider = std::function<QString()>;
    using Checker = std::function<CheckReport(const QString &text)>;

    explicit AiEditsPanel(const QList<AiEdit> &edits, QWidget *parent = nullptr);

    /// The document the edits belong to: its current text and the check of a changed text.
    /// An empty checker (no translator, not a Primula file) leaves the edits unchecked.
    void setDocument(const QString &name, TextProvider text, Checker check);
    /// Locate the edits in the current text of the document and show their statuses.
    void refresh();
    /// Edits that are applied (the row numbers); they are marked and cannot be chosen again.
    void markApplied(const QList<int> &rows);

    int count() const { return m_edits.size(); }
    AiEdit editAt(int row) const { return m_edits.at(row); }
    bool isApplied(int row) const { return m_applied.at(row); }
    /// The edits that are chosen and ready: their numbers.
    QList<int> chosenRows() const;
    /// The check of the chosen edits, each alone and all together (the Check button).
    void checkChosen();
    /// New errors that the edits at these rows cause together (a check of the text with all applied);
    /// -1 when it could not be checked.
    int newErrorsOf(const QList<int> &rows, QStringList *messages = nullptr);

signals:
    /// The user asks to apply the edits at these rows to the document.
    void applyRequested(const QList<int> &rows);

protected:
    /// The document may have changed while the tab was hidden: the statuses are found again.
    void showEvent(QShowEvent *event) override;

private:
    QList<AiEdit> m_edits;
    QList<AiEditStatus> m_status;
    QList<bool> m_applied;
    QList<int> m_newErrors;   ///< per edit: -1 not checked, else the number of new errors it brings
    QList<QStringList> m_messages;   ///< per edit: the new errors
    QString m_name;
    TextProvider m_text;
    Checker m_check;
    QListWidget *m_list = nullptr;
    QPlainTextEdit *m_detail = nullptr;
    QLabel *m_summary = nullptr;
    QPushButton *m_apply = nullptr;
    QPushButton *m_checkButton = nullptr;

    void rebuild();
    void showDetail();
    void updateButtons();
    void contextMenu(const QPoint &position);
    QString statusText(int row) const;
    void setAllChosen(bool chosen);
    void applyRows(const QList<int> &rows);
    /// The new errors of the text with these edits applied, against a check of the text itself.
    int newErrorsAgainst(const CheckReport &baseline, const QString &text, const QList<int> &rows, QStringList *messages);
};
