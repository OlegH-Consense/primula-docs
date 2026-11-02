#include "AiEditsPanel.h"

#include <QApplication>
#include <QClipboard>
#include <QHBoxLayout>
#include <QLabel>
#include <QListWidget>
#include <QMap>
#include <QMenu>
#include <QMessageBox>
#include <QPlainTextEdit>
#include <QPushButton>
#include <QSplitter>
#include <QVBoxLayout>

namespace {

QString firstLine(const QString &text)
{
    QString line = text.section(QLatin1Char('\n'), 0, 0).simplified();
    if (line.size() > 60) line = line.left(59) + QStringLiteral("…");
    return line;
}

} // namespace

AiEditsPanel::AiEditsPanel(const QList<AiEdit> &edits, QWidget *parent)
    : QWidget(parent), m_edits(edits)
{
    m_status.fill(AiEditStatus::NotFound, edits.size());
    m_applied.fill(false, edits.size());
    m_newErrors.fill(-1, edits.size());
    m_messages.resize(edits.size());
    setObjectName(QStringLiteral("aiEditsPanel"));
    auto *layout = new QVBoxLayout(this);
    layout->setContentsMargins(4, 4, 4, 4);
    layout->addWidget(new QLabel(tr("Edits proposed by AI. Choose the ones to apply; they are applied to the "
                                    "editor as one step that Undo takes back."), this));
    auto *splitter = new QSplitter(Qt::Vertical, this);
    m_list = new QListWidget(splitter);
    m_list->setObjectName(QStringLiteral("aiEditsList"));
    m_list->setContextMenuPolicy(Qt::CustomContextMenu);
    m_detail = new QPlainTextEdit(splitter);
    m_detail->setObjectName(QStringLiteral("aiEditsDetail"));
    m_detail->setReadOnly(true);
    m_detail->setLineWrapMode(QPlainTextEdit::NoWrap);
    splitter->setStretchFactor(0, 1);
    splitter->setStretchFactor(1, 2);
    layout->addWidget(splitter, 1);
    m_summary = new QLabel(this);
    m_summary->setObjectName(QStringLiteral("aiEditsSummary"));
    m_summary->setWordWrap(true);
    layout->addWidget(m_summary);
    auto *buttons = new QHBoxLayout;
    m_checkButton = new QPushButton(tr("Check the chosen edits"), this);
    m_checkButton->setObjectName(QStringLiteral("aiEditsCheck"));
    m_checkButton->setToolTip(tr("Runs the translator check on the document with each chosen edit, and with all "
                                 "of them: an edit that brings new errors is marked."));
    m_apply = new QPushButton(tr("Apply the chosen edits"), this);
    m_apply->setObjectName(QStringLiteral("aiEditsApply"));
    buttons->addWidget(m_checkButton);
    buttons->addWidget(m_apply);
    buttons->addStretch();
    layout->addLayout(buttons);
    connect(m_list, &QListWidget::currentRowChanged, this, [this] { showDetail(); });
    connect(m_list, &QListWidget::itemChanged, this, [this] { updateButtons(); });
    connect(m_list, &QListWidget::customContextMenuRequested, this, &AiEditsPanel::contextMenu);
    connect(m_checkButton, &QPushButton::clicked, this, &AiEditsPanel::checkChosen);
    connect(m_apply, &QPushButton::clicked, this, [this] { applyRows(chosenRows()); });
    rebuild();
}

void AiEditsPanel::showEvent(QShowEvent *event)
{
    QWidget::showEvent(event);
    if (!m_text) return;
    QList<AiEditStatus> now;
    AiEdits::apply(m_text(), m_edits, &now);
    if (now != m_status) refresh();
}

void AiEditsPanel::setDocument(const QString &name, TextProvider text, Checker check)
{
    m_name = name;
    m_text = std::move(text);
    m_check = std::move(check);
    refresh();
}

QString AiEditsPanel::statusText(int row) const
{
    if (m_applied.at(row)) return tr("applied");
    switch (m_status.at(row)) {
    case AiEditStatus::Ready:
        if (m_newErrors.at(row) > 0) return tr("brings %n new error(s)", nullptr, m_newErrors.at(row));
        if (m_newErrors.at(row) == 0) return tr("checked, no new errors");
        return tr("ready");
    case AiEditStatus::NotFound: return tr("not found in the document");
    case AiEditStatus::Ambiguous: return tr("occurs several times");
    case AiEditStatus::Unchanged: return tr("changes nothing");
    case AiEditStatus::Overlaps: return tr("overlaps another edit");
    }
    return {};
}

void AiEditsPanel::refresh()
{
    const QString text = m_text ? m_text() : QString();
    if (m_text) {
        AiEdits::apply(text, m_edits, &m_status);
    } else {
        m_status.fill(AiEditStatus::NotFound, m_edits.size());
    }
    m_newErrors.fill(-1, m_edits.size());
    for (QStringList &messages : m_messages) messages.clear();
    rebuild();
}

void AiEditsPanel::rebuild()
{
    const int current = m_list->currentRow();
    const QSignalBlocker blocker(m_list);
    m_list->clear();
    for (int row = 0; row < m_edits.size(); ++row) {
        auto *item = new QListWidgetItem(QStringLiteral("%1. %2 — %3").arg(row + 1).arg(firstLine(m_edits.at(row).original), statusText(row)),
                                         m_list);
        const bool usable = m_status.at(row) == AiEditStatus::Ready && !m_applied.at(row);
        item->setFlags(usable ? (item->flags() | Qt::ItemIsUserCheckable) : (item->flags() & ~Qt::ItemIsUserCheckable));
        if (usable) item->setCheckState(m_newErrors.at(row) > 0 ? Qt::Unchecked : Qt::Checked);
    }
    m_list->setCurrentRow(qBound(0, current, m_edits.size() - 1));
    showDetail();
    updateButtons();
}

void AiEditsPanel::showDetail()
{
    const int row = m_list->currentRow();
    if (row < 0 || row >= m_edits.size()) {
        m_detail->clear();
        return;
    }
    QString text = AiEdits::diffText(m_edits.at(row)) + QStringLiteral("\n") + statusText(row);
    for (const QString &message : m_messages.at(row)) text += QStringLiteral("\n  ") + message;
    m_detail->setPlainText(text);
}

QList<int> AiEditsPanel::chosenRows() const
{
    QList<int> rows;
    for (int row = 0; row < m_list->count(); ++row)
        if (m_list->item(row)->flags().testFlag(Qt::ItemIsUserCheckable) && m_list->item(row)->checkState() == Qt::Checked)
            rows.append(row);
    return rows;
}

void AiEditsPanel::updateButtons()
{
    const int chosen = chosenRows().size();
    int ready = 0, applied = 0;
    for (int row = 0; row < m_edits.size(); ++row) {
        ready += m_status.at(row) == AiEditStatus::Ready && !m_applied.at(row);
        applied += m_applied.at(row);
    }
    m_apply->setEnabled(chosen > 0 && m_text);
    m_checkButton->setEnabled(chosen > 0 && m_check);
    QString text = tr("%n edit(s): %1 ready, %2 applied; chosen %3.", nullptr, m_edits.size()).arg(ready).arg(applied).arg(chosen);
    if (!m_text) text += QLatin1Char(' ') + tr("The document is not available, so the edits cannot be applied.");
    else if (!m_check) text += QLatin1Char(' ') + tr("The check is not available (the translator or the file type).");
    m_summary->setText(text);
}

void AiEditsPanel::setAllChosen(bool chosen)
{
    const QSignalBlocker blocker(m_list);
    for (int row = 0; row < m_list->count(); ++row)
        if (m_list->item(row)->flags().testFlag(Qt::ItemIsUserCheckable))
            m_list->item(row)->setCheckState(chosen ? Qt::Checked : Qt::Unchecked);
    updateButtons();
}

void AiEditsPanel::markApplied(const QList<int> &rows)
{
    for (int row : rows)
        if (row >= 0 && row < m_applied.size()) m_applied[row] = true;
    // The text changed: the statuses of the others are found again.
    refresh();
}

int AiEditsPanel::newErrorsAgainst(const CheckReport &baseline, const QString &text, const QList<int> &rows,
                                   QStringList *messages)
{
    QList<AiEdit> chosen;
    for (int row : rows) chosen.append(m_edits.at(row));
    const CheckReport after = m_check(AiEdits::apply(text, chosen));
    if (!after.ran) {
        if (messages) *messages = {after.failure};
        return -1;
    }
    // Errors that the text had before are not the edit's: compare as multisets.
    QMap<QString, int> before;
    for (const QString &error : baseline.errors) ++before[error];
    QStringList added;
    for (const QString &error : after.errors) {
        if (before.value(error) > 0) --before[error];
        else added << error;
    }
    if (messages) *messages = added;
    return int(added.size());
}

int AiEditsPanel::newErrorsOf(const QList<int> &rows, QStringList *messages)
{
    if (!m_check || !m_text) return -1;
    const QString text = m_text();
    const CheckReport baseline = m_check(text);
    if (!baseline.ran) {
        if (messages) *messages = {baseline.failure};
        return -1;
    }
    return newErrorsAgainst(baseline, text, rows, messages);
}

void AiEditsPanel::checkChosen()
{
    const QList<int> rows = chosenRows();
    if (rows.isEmpty() || !m_check || !m_text) {
        m_summary->setText(tr("Nothing is checked: choose at least one ready edit."));
        return;
    }
    QApplication::setOverrideCursor(Qt::WaitCursor);
    const QString text = m_text();
    const CheckReport baseline = m_check(text);
    QString summary;
    if (!baseline.ran) {
        summary = tr("The check did not run: %1").arg(baseline.failure);
    } else {
        int harmful = 0;
        for (int row : rows) {
            QStringList messages;
            m_newErrors[row] = newErrorsAgainst(baseline, text, {row}, &messages);
            m_messages[row] = messages;
            harmful += m_newErrors.at(row) > 0;
        }
        QStringList together;
        const int all = newErrorsAgainst(baseline, text, rows, &together);
        summary = tr("Checked %n edit(s): %1 bring new errors. All chosen together: %2 new error(s).", nullptr, rows.size())
                      .arg(harmful).arg(all);
        if (!together.isEmpty() && all > 0) summary += QLatin1Char('\n') + together.mid(0, 5).join(QLatin1Char('\n'));
    }
    QApplication::restoreOverrideCursor();
    rebuild();
    m_summary->setText(summary);
}

void AiEditsPanel::applyRows(const QList<int> &rows)
{
    if (rows.isEmpty()) {
        QMessageBox::information(this, tr("Apply edits"), tr("No edit is chosen: nothing is applied."));
        return;
    }
    QStringList messages;
    const int added = newErrorsOf(rows, &messages);
    if (added > 0 &&
        QMessageBox::question(this, tr("Apply edits"),
                              tr("The chosen edits bring %n new error(s) to the document:\n\n%1\n\nApply them anyway?", nullptr, added)
                                  .arg(messages.mid(0, 5).join(QLatin1Char('\n')))) != QMessageBox::Yes)
        return;
    emit applyRequested(rows);
}

void AiEditsPanel::contextMenu(const QPoint &position)
{
    const int row = m_list->row(m_list->itemAt(position));
    QMenu menu(this);
    QAction *apply = menu.addAction(tr("Apply this edit"));
    apply->setEnabled(row >= 0 && m_status.value(row) == AiEditStatus::Ready && !m_applied.value(row) && m_text);
    QAction *check = menu.addAction(tr("Check this edit"));
    check->setEnabled(row >= 0 && m_status.value(row) == AiEditStatus::Ready && !m_applied.value(row) && m_check && m_text);
    menu.addSeparator();
    QAction *copyNew = menu.addAction(tr("Copy the replacement"));
    copyNew->setEnabled(row >= 0);
    QAction *copyOld = menu.addAction(tr("Copy the original text"));
    copyOld->setEnabled(row >= 0);
    menu.addSeparator();
    QAction *all = menu.addAction(tr("Choose all"));
    QAction *none = menu.addAction(tr("Clear the choice"));
    QAction *picked = menu.exec(m_list->viewport()->mapToGlobal(position));
    if (!picked) return;
    if (picked == apply) {
        applyRows({row});
    } else if (picked == check) {
        const QString text = m_text();
        const CheckReport baseline = m_check(text);
        if (!baseline.ran) {
            m_summary->setText(tr("The check did not run: %1").arg(baseline.failure));
            return;
        }
        QStringList messages;
        m_newErrors[row] = newErrorsAgainst(baseline, text, {row}, &messages);
        m_messages[row] = messages;
        rebuild();
        m_list->setCurrentRow(row);
    } else if (picked == copyNew) {
        QApplication::clipboard()->setText(m_edits.at(row).replacement);
    } else if (picked == copyOld) {
        QApplication::clipboard()->setText(m_edits.at(row).original);
    } else if (picked == all) {
        setAllChosen(true);
    } else if (picked == none) {
        setAllChosen(false);
    }
}
