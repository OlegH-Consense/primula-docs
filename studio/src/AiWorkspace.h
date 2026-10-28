#pragma once
#include <QWidget>
class AiHistoryPane;
class QComboBox;
class QStackedWidget;
class AiWorkspace : public QWidget
{
    Q_OBJECT
public:
    explicit AiWorkspace(QWidget *parent = nullptr);
    void addPane(AiHistoryPane *pane);
    void clear();
    void selectPane(AiHistoryPane *pane);
    AiHistoryPane *currentPane() const;
    int count() const;
signals:
    void closeRequested();
private:
    QComboBox *m_selector;
    QStackedWidget *m_stack;
};
