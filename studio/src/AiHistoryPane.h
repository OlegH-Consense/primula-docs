#pragma once
#include <QWidget>
#include "AiHistory.h"
class QTextBrowser;
class QLineEdit;
class QLabel;
class AiEditsPanel;

class AiHistoryPane : public QWidget
{
    Q_OBJECT
public:
    explicit AiHistoryPane(const AiExchange &exchange, const QString &path, QWidget *parent = nullptr);
    QString filePath() const { return m_path; }
    QString title() const;
    AiExchange exchange() const { return m_exchange; }
    bool saveCopy();
    /// The proposed edits of the answer (the tab «Edits»); null when the answer has none.
    AiEditsPanel *editsPanel() const { return m_edits; }
signals:
    void fileSaved();
private:
    AiExchange m_exchange;
    QString m_path;
    QTextBrowser *m_preview;
    QLineEdit *m_search;
    QLabel *m_location;
    AiEditsPanel *m_edits = nullptr;
    void findNext();

};
