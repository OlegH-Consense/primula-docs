#include "HelpDialog.h"

#include <QAbstractTextDocumentLayout>
#include <QDesktopServices>
#include <QScrollBar>
#include <QTextBlock>
#include <QDialogButtonBox>
#include <QFile>
#include <QFont>
#include <QSettings>
#include <QHBoxLayout>
#include <QLabel>
#include <QLineEdit>
#include <QPushButton>
#include <QRegularExpression>
#include <QShortcut>
#include <QTextBrowser>
#include <QTextCursor>
#include <QUrl>
#include <QVBoxLayout>

HelpDialog::HelpDialog(const QString &language, QWidget *parent) : QDialog(parent)
{
    setWindowTitle(tr("Quick help"));
    QFile file(QStringLiteral(":/help/studio-user-guide.%1.md").arg(language));
    if (!file.open(QIODevice::ReadOnly)) {
        // The English guide is always compiled into the resources.
        file.setFileName(QStringLiteral(":/help/studio-user-guide.en.md"));
        if (!file.open(QIODevice::ReadOnly))
            qWarning("Studio help resource is missing");
    }
    build(QString::fromUtf8(file.readAll()));
}

HelpDialog::HelpDialog(const QString &resource, const QString &title, QWidget *parent) : QDialog(parent)
{
    m_title = title;
    setWindowTitle(title);
    QFile file(resource);
    if (!file.open(QIODevice::ReadOnly)) qWarning("Studio help resource is missing");
    build(QString::fromUtf8(file.readAll()));
}

void HelpDialog::setContext(const QString &context, const QString &note)
{
    m_context = context;
    const QString base = m_title.isEmpty() ? windowTitle() : m_title;
    setWindowTitle(context.isEmpty() ? base : tr("%1 — context: %2").arg(base, context));
    m_contextLine->setText(note);
    m_contextLine->setVisible(!note.isEmpty());
}

bool HelpDialog::showSection(const QString &section)
{
    // Markdown headings become blocks with a heading level; their text starts with the number.
    const QString prefix = section + QStringLiteral(". ");
    for (QTextBlock block = m_browser->document()->begin(); block.isValid(); block = block.next()) {
        if (block.blockFormat().headingLevel() == 0 || !block.text().startsWith(prefix)) continue;
        m_browser->setTextCursor(QTextCursor(block));
        const qreal top = m_browser->document()->documentLayout()->blockBoundingRect(block).top();
        m_browser->verticalScrollBar()->setValue(int(top));
        return true;
    }
    return false;
}

void HelpDialog::build(const QString &markdown)
{
    resize(850, 650);
    setAttribute(Qt::WA_DeleteOnClose);
    m_browser = new QTextBrowser(this);
    m_browser->setObjectName(QStringLiteral("helpBrowser"));
    m_browser->setReadOnly(true);
    QFont helpFont = m_browser->font();
    helpFont.setPointSize(qMax(11, QSettings().value(QStringLiteral("editor/fontSize"), 11).toInt()));
    m_browser->setFont(helpFont);
    m_browser->setOpenLinks(false);
    connect(m_browser, &QTextBrowser::anchorClicked, this, [this](const QUrl &url) {
        if (url.scheme() == QStringLiteral("http") || url.scheme() == QStringLiteral("https"))
            QDesktopServices::openUrl(url);
        else if (url.scheme().isEmpty() && !url.fragment().isEmpty())
            m_browser->scrollToAnchor(url.fragment());
    });
    // HTML comments are service marks (the translation mark of tools/author_docs.py,
    // stage 15.5); the Markdown reader of Qt may show them as text, so drop them.
    QString text = markdown;
    text.remove(QRegularExpression(QStringLiteral("<!--.*?-->\\n?"), QRegularExpression::DotMatchesEverythingOption));
    m_browser->setMarkdown(text);
    m_search = new QLineEdit(this);
    m_search->setPlaceholderText(tr("Find in help…"));
    auto *next = new QPushButton(tr("Find next"), this);
    connect(m_search, &QLineEdit::returnPressed, this, &HelpDialog::findNext);
    connect(next, &QPushButton::clicked, this, &HelpDialog::findNext);
    auto *findShortcut = new QShortcut(QKeySequence::Find, this);
    connect(findShortcut, &QShortcut::activated, this, [this] { m_search->setFocus(); m_search->selectAll(); });
    auto *nextShortcut = new QShortcut(QKeySequence::FindNext, this);
    connect(nextShortcut, &QShortcut::activated, this, &HelpDialog::findNext);
    auto *buttons = new QDialogButtonBox(QDialogButtonBox::Close, this);
    connect(buttons, &QDialogButtonBox::rejected, this, &QDialog::close);
    auto *findRow = new QHBoxLayout;
    findRow->addWidget(m_search, 1);
    findRow->addWidget(next);
    // The line of context help: what text of the editor the section was opened for.
    m_contextLine = new QLabel(this);
    m_contextLine->setObjectName(QStringLiteral("helpContext"));
    m_contextLine->setWordWrap(true);
    m_contextLine->setTextFormat(Qt::PlainText);
    m_contextLine->setStyleSheet(QStringLiteral("QLabel { background: rgba(255, 193, 7, 0.35); "
                                                "border: 1px dotted #b45309; padding: 4px; }"));
    m_contextLine->hide();
    auto *layout = new QVBoxLayout(this);
    layout->addWidget(m_contextLine);
    layout->addLayout(findRow);
    layout->addWidget(m_browser, 1);
    layout->addWidget(buttons);
}

void HelpDialog::findNext()
{
    if (m_search->text().isEmpty())
        return;
    if (!m_browser->find(m_search->text())) {
        m_browser->moveCursor(QTextCursor::Start);
        m_browser->find(m_search->text());
    }
}
