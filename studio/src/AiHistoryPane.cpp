#include "AiHistoryPane.h"
#include <QApplication>
#include <QClipboard>
#include <QDesktopServices>
#include <QFileDialog>
#include <QFile>
#include <QTextCursor>
#include <QFileInfo>
#include <QFont>
#include <QHBoxLayout>
#include <QLabel>
#include <QLineEdit>
#include <QMessageBox>
#include <QPlainTextEdit>
#include <QPushButton>
#include <QScrollBar>
#include <QSettings>
#include <QShortcut>
#include <QTabWidget>
#include <QTextBrowser>
#include <QUrl>
#include <QVBoxLayout>

AiHistoryPane::AiHistoryPane(const AiExchange &exchange, const QString &path, QWidget *parent)
    : QWidget(parent), m_exchange(exchange), m_path(path)
{
    auto *layout = new QVBoxLayout(this);
    layout->setContentsMargins(4, 4, 4, 4);
    m_location = new QLabel(path.isEmpty() ? tr("Not saved — use Save copy") : path, this);
    m_location->setTextInteractionFlags(Qt::TextSelectableByMouse);
    m_location->setWordWrap(true);
    layout->addWidget(m_location);
    auto *buttons = new QHBoxLayout;
    auto *task = new QPushButton(tr("Copy task"), this);
    task->setObjectName(QStringLiteral("copyTask"));
    auto *answer = new QPushButton(tr("Copy answer (Markdown)"), this);
    answer->setObjectName(QStringLiteral("copyAnswer"));
    auto *save = new QPushButton(tr("Save copy…"), this);
    connect(task, &QPushButton::clicked, this, [this] { QApplication::clipboard()->setText(m_exchange.task); });
    connect(answer, &QPushButton::clicked, this, [this] { QApplication::clipboard()->setText(m_exchange.response); });
    connect(save, &QPushButton::clicked, this, &AiHistoryPane::saveCopy);
    buttons->addWidget(task); buttons->addWidget(answer); buttons->addWidget(save); buttons->addStretch();
    layout->addLayout(buttons);
    auto *tabs = new QTabWidget(this);
    m_preview = new QTextBrowser(tabs);
    m_preview->setObjectName(QStringLiteral("aiPreview"));
    m_preview->setReadOnly(true);
    m_preview->setOpenLinks(false);
    QFont font = m_preview->font();
    font.setPointSize(qMax(11, QSettings().value(QStringLiteral("editor/fontSize"), 11).toInt()));
    m_preview->setFont(font);
    m_preview->setMarkdown(QStringLiteral("# ") + tr("Task") + QStringLiteral("\n\n") + AiHistory::fenced(exchange.task)
        + QStringLiteral("\n\n# ") + tr("Response") + QStringLiteral("\n\n") + exchange.response);
    connect(m_preview, &QTextBrowser::anchorClicked, this, [this](const QUrl &url) {
        if (url.scheme() == QStringLiteral("http") || url.scheme() == QStringLiteral("https"))
            QDesktopServices::openUrl(url);
        else if (url.scheme().isEmpty() && !url.fragment().isEmpty()) m_preview->scrollToAnchor(url.fragment());
    });
    tabs->addTab(m_preview, tr("Preview"));
    auto raw = [tabs](const QString &name, const QString &text) {
        auto *editor = new QPlainTextEdit(tabs);
        editor->setObjectName(name); editor->setReadOnly(true); editor->setPlainText(text);
        return editor;
    };
    QString source = AiHistory::markdown(exchange);
    QFile saved(path);
    if (!path.isEmpty() && saved.open(QIODevice::ReadOnly)) source = QString::fromUtf8(saved.readAll());
    tabs->addTab(raw(QStringLiteral("aiMarkdown"), source), tr("Markdown"));
    tabs->addTab(raw(QStringLiteral("aiRequest"), exchange.prompt), tr("Complete request"));
    m_search = new QLineEdit(this);
    m_search->setPlaceholderText(tr("Find in AI response…"));
    auto *next = new QPushButton(tr("Find next"), this);
    auto *searchRow = new QHBoxLayout;
    searchRow->addWidget(m_search, 1); searchRow->addWidget(next);
    layout->addLayout(searchRow);
    layout->addWidget(tabs, 1);
    auto find = new QShortcut(QKeySequence::Find, this);
    find->setContext(Qt::WidgetWithChildrenShortcut);
    connect(find, &QShortcut::activated, this, [this, tabs] { tabs->setCurrentWidget(m_preview); m_search->setFocus(); m_search->selectAll(); });
    auto again = new QShortcut(QKeySequence::FindNext, this);
    again->setContext(Qt::WidgetWithChildrenShortcut);
    connect(again, &QShortcut::activated, this, &AiHistoryPane::findNext);
    connect(next, &QPushButton::clicked, this, &AiHistoryPane::findNext);
    connect(m_search, &QLineEdit::returnPressed, this, &AiHistoryPane::findNext);
}

QString AiHistoryPane::title() const
{
    return tr("AI %1 [RO]").arg(m_exchange.receivedAt.toString(QStringLiteral("yyyy-MM-dd HH:mm:ss")));
}

void AiHistoryPane::findNext()
{
    if (m_search->text().isEmpty()) return;
    if (!m_preview->find(m_search->text())) { m_preview->moveCursor(QTextCursor::Start); m_preview->find(m_search->text()); }
}

bool AiHistoryPane::saveCopy()
{
    const QString path = QFileDialog::getSaveFileName(this, tr("Save AI exchange"),
        m_path.isEmpty() ? QFileInfo(m_exchange.documentPath).absolutePath() : m_path,
        tr("Markdown files (*.md);;All files (*)"));
    if (path.isEmpty()) return false;
    QString error;
    if (!AiHistory::saveCopy(path, m_exchange, &error)) { QMessageBox::warning(this, tr("Cannot save AI exchange"), error); return false; }
    // Saving a copy of an archive does not move its authoritative history path.
    if (m_path.isEmpty()) { m_path = path; m_location->setText(path); emit fileSaved(); }
    return true;
}
