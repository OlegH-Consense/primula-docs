#include "AiWorkspace.h"
#include "AiHistoryPane.h"
#include <QComboBox>
#include <QHBoxLayout>
#include <QLabel>
#include <QStackedWidget>
#include <QStyle>
#include <QToolButton>
#include <QVBoxLayout>
AiWorkspace::AiWorkspace(QWidget *parent) : QWidget(parent)
{
    auto *layout = new QVBoxLayout(this);
    layout->setContentsMargins(4, 4, 4, 4);
    auto *row = new QHBoxLayout;
    row->addWidget(new QLabel(tr("Saved AI requests:"), this));
    m_selector = new QComboBox(this);
    m_selector->setObjectName(QStringLiteral("aiHistorySelector"));
    m_selector->setSizeAdjustPolicy(QComboBox::AdjustToMinimumContentsLengthWithIcon);
    m_selector->setMinimumContentsLength(16);
    row->addWidget(m_selector, 1);
    auto *close = new QToolButton(this);
    close->setObjectName(QStringLiteral("closeAiTab"));
    close->setIcon(style()->standardIcon(QStyle::SP_TitleBarCloseButton));
    close->setToolTip(tr("Close AI tab; saved files stay on disk"));
    close->setAccessibleName(tr("Close AI tab"));
    row->addWidget(close);
    connect(close, &QToolButton::clicked, this, &AiWorkspace::closeRequested);
    m_stack = new QStackedWidget(this);
    connect(m_selector, &QComboBox::currentIndexChanged, m_stack, &QStackedWidget::setCurrentIndex);
    layout->addLayout(row); layout->addWidget(m_stack, 1);
}
void AiWorkspace::addPane(AiHistoryPane *pane)
{
    m_stack->addWidget(pane);
    const QString task = pane->exchange().task.simplified().left(90);
    m_selector->addItem(pane->title() + QStringLiteral(" — ") + task);
    m_selector->setItemData(m_selector->count() - 1, pane->filePath(), Qt::ToolTipRole);
    connect(pane, &AiHistoryPane::fileSaved, this, [this, pane] {
        const int index = m_stack->indexOf(pane);
        if (index >= 0) m_selector->setItemData(index, pane->filePath(), Qt::ToolTipRole);
    });
}
void AiWorkspace::clear()
{
    m_selector->clear();
    while (m_stack->count()) m_stack->removeWidget(m_stack->widget(0));
}
void AiWorkspace::selectPane(AiHistoryPane *pane)
{
    const int index = m_stack->indexOf(pane);
    if (index >= 0) m_selector->setCurrentIndex(index);
}
AiHistoryPane *AiWorkspace::currentPane() const { return qobject_cast<AiHistoryPane *>(m_stack->currentWidget()); }
int AiWorkspace::count() const { return m_stack->count(); }
