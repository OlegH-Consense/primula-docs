#include "EditorPane.h"

#include <QFile>
#include <QCryptographicHash>
#include <QCheckBox>
#include <QLineEdit>
#include <QPushButton>
#include <QShortcut>
#include <QHBoxLayout>
#include <QLabel>
#include <QFileInfo>
#include <QSaveFile>
#include <QScrollBar>
#include <QTextCursor>
#include <QTextDocument>
#include <QVBoxLayout>

EditorPane::EditorPane(QWidget *parent) : QWidget(parent), m_editor(new CodeEditor(this))
{
    auto *layout = new QVBoxLayout(this);
    layout->setContentsMargins(0, 0, 0, 0);
    m_unavailableNote = new QLabel(this);
    m_unavailableNote->setTextFormat(Qt::PlainText);
    m_unavailableNote->setWordWrap(true);
    m_unavailableNote->setTextInteractionFlags(Qt::TextSelectableByMouse);
    m_unavailableNote->hide();
    layout->addWidget(m_unavailableNote);
    layout->addWidget(m_editor);
    m_searchBar = new QWidget(this);
    m_searchBar->setObjectName(QStringLiteral("editorSearchBar"));
    auto *searchLayout = new QVBoxLayout(m_searchBar);
    searchLayout->setContentsMargins(4, 4, 4, 4);
    auto *findRow = new QHBoxLayout;
    m_findText = new QLineEdit(m_searchBar);
    m_findText->setObjectName(QStringLiteral("editorFindText"));
    m_findText->setPlaceholderText(tr("Find text…"));
    m_findText->setAccessibleName(tr("Find text…"));
    auto *previous = new QPushButton(tr("Previous"), m_searchBar);
    auto *next = new QPushButton(tr("Next"), m_searchBar);
    auto *close = new QPushButton(tr("Close"), m_searchBar);
    findRow->addWidget(m_findText, 1);
    findRow->addWidget(previous);
    findRow->addWidget(next);
    findRow->addWidget(close);
    searchLayout->addLayout(findRow);
    auto *options = new QHBoxLayout;
    m_matchCase = new QCheckBox(tr("Match case"), m_searchBar);
    m_matchCase->setObjectName(QStringLiteral("editorMatchCase"));
    m_wholeWords = new QCheckBox(tr("Whole words"), m_searchBar);
    m_wholeWords->setObjectName(QStringLiteral("editorWholeWords"));
    m_searchStatus = new QLabel(m_searchBar);
    m_searchStatus->setObjectName(QStringLiteral("editorSearchStatus"));
    m_searchStatus->setTextFormat(Qt::PlainText);
    m_searchStatus->setWordWrap(true);
    m_searchStatus->setSizePolicy(QSizePolicy::Ignored, QSizePolicy::Preferred);
    options->addWidget(m_matchCase);
    options->addWidget(m_wholeWords);
    options->addWidget(m_searchStatus, 1);
    searchLayout->addLayout(options);
    m_replaceRow = new QWidget(m_searchBar);
    auto *replaceLayout = new QHBoxLayout(m_replaceRow);
    replaceLayout->setContentsMargins(0, 0, 0, 0);
    m_replaceText = new QLineEdit(m_replaceRow);
    m_replaceText->setObjectName(QStringLiteral("editorReplaceText"));
    m_replaceText->setPlaceholderText(tr("Replace with…"));
    m_replaceText->setAccessibleName(tr("Replace with…"));
    auto *replace = new QPushButton(tr("Replace"), m_replaceRow);
    auto *all = new QPushButton(tr("Replace all"), m_replaceRow);
    replaceLayout->addWidget(m_replaceText, 1);
    replaceLayout->addWidget(replace);
    replaceLayout->addWidget(all);
    searchLayout->addWidget(m_replaceRow);
    layout->addWidget(m_searchBar);
    m_searchBar->hide();
    connect(previous, &QPushButton::clicked, this, [this] { findNext(true); });
    connect(next, &QPushButton::clicked, this, [this] { findNext(); });
    connect(close, &QPushButton::clicked, this, &EditorPane::closeSearch);
    connect(m_findText, &QLineEdit::returnPressed, this, [this] { findNext(); });
    connect(m_findText, &QLineEdit::textChanged, m_searchStatus, &QLabel::clear);
    connect(m_matchCase, &QCheckBox::toggled, m_searchStatus, &QLabel::clear);
    connect(m_wholeWords, &QCheckBox::toggled, m_searchStatus, &QLabel::clear);
    connect(replace, &QPushButton::clicked, this, [this] { replaceCurrent(); });
    connect(all, &QPushButton::clicked, this, [this] { replaceAll(); });
    auto shortcut = [this](const QKeySequence &key, auto callback) {
        auto *action = new QShortcut(key, this);
        action->setContext(Qt::WidgetWithChildrenShortcut);
        connect(action, &QShortcut::activated, this, callback);
    };
    shortcut(QKeySequence::Find, [this] { showSearch(); });
    shortcut(QKeySequence(Qt::CTRL | Qt::Key_H), [this] { showSearch(true); });
    shortcut(QKeySequence(Qt::Key_F3), [this] { findNext(); });
    shortcut(QKeySequence(Qt::SHIFT | Qt::Key_F3), [this] { findNext(true); });
    shortcut(QKeySequence(Qt::Key_Escape), [this] { if (m_searchBar->isVisible()) closeSearch(); });
    connect(m_editor->document(), &QTextDocument::modificationChanged,
            this, &EditorPane::modificationChanged);
}

bool EditorPane::loadFile(const QString &path, bool readOnly, CodeEditor::Syntax syntax,
                          QString *errorMessage)
{
    QFile file(path);
    if (!file.open(QIODevice::ReadOnly | QIODevice::Text)) {
        if (errorMessage)
            *errorMessage = tr("Cannot open %1: %2").arg(path, file.errorString());
        return false;
    }

    m_unavailable = false;
    m_unavailableNote->hide();
    m_searchBar->hide();
    m_filePath = QFileInfo(path).absoluteFilePath();
    m_readOnly = readOnly;
    const QByteArray bytes = file.readAll();
    m_diskDigest = QCryptographicHash::hash(bytes, QCryptographicHash::Sha256);
    m_syntax = syntax;
    m_editor->setPlainText(QString::fromUtf8(bytes));
    m_editor->setReadOnly(readOnly);
    m_editor->setSyntax(syntax);
    m_editor->document()->setModified(false);
    return true;
}

void EditorPane::showUnavailable(const QString &path, CodeEditor::Syntax syntax, const QString &reason)
{
    m_searchBar->hide();
    m_unavailable = true;
    m_syntax = syntax;
    m_diskDigest.clear();
    m_readOnly = true;
    m_filePath = QFileInfo(path).absoluteFilePath();
    m_editor->clear();
    m_editor->setReadOnly(true);
    m_editor->setSyntax(syntax);
    m_editor->document()->setModified(false);
    m_unavailableNote->setText(reason);
    m_unavailableNote->show();
}

bool EditorPane::save(QString *errorMessage)
{
    if (m_editor->isReadOnly() || !isModified())
        return true;
    if (diskChanged()) {
        if (errorMessage) *errorMessage = tr("File changed outside Studio: %1. Reload or choose Keep editor before saving.").arg(m_filePath);
        return false;
    }
    QSaveFile file(m_filePath);
    // Binary mode: a text-mode write would turn "\n" into "\r\n" on Windows (documents are LF).
    if (!file.open(QIODevice::WriteOnly)) {
        if (errorMessage)
            *errorMessage = tr("Cannot save %1: %2").arg(m_filePath, file.errorString());
        return false;
    }
    const QByteArray data = m_editor->toPlainText().toUtf8();
    if (file.write(data) != data.size() || !file.commit()) {
        if (errorMessage)
            *errorMessage = tr("Cannot save %1: %2").arg(m_filePath, file.errorString());
        return false;
    }
    m_diskDigest = QCryptographicHash::hash(data, QCryptographicHash::Sha256);
    m_editor->document()->setModified(false);
    return true;
}

bool EditorPane::isModified() const { return m_editor->document()->isModified(); }
bool EditorPane::isReadOnly() const { return m_editor->isReadOnly(); }
QString EditorPane::filePath() const { return m_filePath; }
QString EditorPane::text() const { return m_editor->toPlainText(); }
QString EditorPane::selectedText() const
{
    QString text = m_editor->textCursor().selectedText();
    text.replace(QChar::ParagraphSeparator, QLatin1Char('\n'));
    return text;
}
CodeEditor *EditorPane::editor() const { return m_editor; }

void EditorPane::insertText(const QString &text)
{
    m_editor->insertPlainText(text);
}

QVariantMap EditorPane::sessionState() const
{
    const QTextCursor cursor = m_editor->textCursor();
    return {
        {QStringLiteral("cursor"), cursor.position()},
        {QStringLiteral("anchor"), cursor.anchor()},
        {QStringLiteral("vscroll"), m_editor->verticalScrollBar()->value()},
        {QStringLiteral("hscroll"), m_editor->horizontalScrollBar()->value()}
    };
}

void EditorPane::restoreSessionState(const QVariantMap &state)
{
    QTextCursor cursor(m_editor->document());
    const int maximum = qMax(0, m_editor->document()->characterCount() - 1);
    const int anchor = qBound(0, state.value(QStringLiteral("anchor")).toInt(), maximum);
    const int position = qBound(0, state.value(QStringLiteral("cursor")).toInt(), maximum);
    cursor.setPosition(anchor);
    cursor.setPosition(position, QTextCursor::KeepAnchor);
    m_editor->setTextCursor(cursor);
    m_editor->verticalScrollBar()->setValue(state.value(QStringLiteral("vscroll")).toInt());
    m_editor->horizontalScrollBar()->setValue(state.value(QStringLiteral("hscroll")).toInt());
}

QTextDocument::FindFlags EditorPane::searchFlags(bool backwards) const
{
    QTextDocument::FindFlags flags;
    if (backwards) flags |= QTextDocument::FindBackward;
    if (m_matchCase->isChecked()) flags |= QTextDocument::FindCaseSensitively;
    if (m_wholeWords->isChecked()) flags |= QTextDocument::FindWholeWords;
    return flags;
}

void EditorPane::showSearch(bool replace)
{
    if (m_unavailable) return;
    const QString selection = selectedText();
    if (!selection.isEmpty() && !selection.contains(QLatin1Char('\n')))
        m_findText->setText(selection);
    m_replaceRow->setVisible(replace && !m_editor->isReadOnly());
    m_searchBar->show();
    m_findText->setFocus();
    m_findText->selectAll();
}

void EditorPane::closeSearch()
{
    m_searchBar->hide();
    m_editor->setFocus();
}

bool EditorPane::findNext(bool backwards)
{
    if (m_unavailable) return false;
    const QString query = m_findText->text();
    if (query.isEmpty()) { showSearch(); return false; }
    QTextCursor start = m_editor->textCursor();
    start.setPosition(backwards ? start.selectionStart() : start.selectionEnd());
    QTextCursor found = m_editor->document()->find(query, start, searchFlags(backwards));
    bool wrapped = false;
    if (found.isNull()) {
        start.movePosition(backwards ? QTextCursor::End : QTextCursor::Start);
        found = m_editor->document()->find(query, start, searchFlags(backwards));
        wrapped = !found.isNull();
    }
    if (found.isNull()) { m_searchStatus->setText(tr("Text not found")); return false; }
    m_editor->setTextCursor(found);
    m_editor->ensureCursorVisible();
    m_searchStatus->setText(wrapped ? tr("Search wrapped") : QString());
    return true;
}

bool EditorPane::replaceCurrent()
{
    if (m_unavailable || m_editor->isReadOnly() || m_findText->text().isEmpty()) return false;
    QTextCursor cursor = m_editor->textCursor();
    // Validate the actual selected occurrence, including case and word boundaries.
    const QTextCursor match = m_editor->document()->find(m_findText->text(), cursor.selectionStart(), searchFlags());
    if (!cursor.hasSelection() || match.isNull() || match.selectionStart() != cursor.selectionStart()
            || match.selectionEnd() != cursor.selectionEnd()) {
        findNext();
        return false;
    }
    cursor.insertText(m_replaceText->text());
    m_editor->setTextCursor(cursor);
    findNext();
    return true;
}

int EditorPane::replaceAll()
{
    if (m_unavailable || m_editor->isReadOnly() || m_findText->text().isEmpty()) return 0;
    QTextCursor transaction(m_editor->document());
    transaction.beginEditBlock();
    QTextCursor cursor(m_editor->document());
    int count = 0;
    while (true) {
        QTextCursor match = m_editor->document()->find(m_findText->text(), cursor, searchFlags());
        if (match.isNull()) break;
        match.insertText(m_replaceText->text());
        cursor = match; // Continue after inserted text, never search the replacement again.
        ++count;
    }
    transaction.endEditBlock();
    if (count) { m_editor->setTextCursor(cursor); m_editor->ensureCursorVisible(); }
    m_searchStatus->setText(tr("Replaced: %1").arg(count));
    return count;
}

bool EditorPane::diskChanged() const
{
    if (m_filePath.isEmpty()) return false;
    QFile file(m_filePath);
    const auto digest = file.open(QIODevice::ReadOnly)
        ? QCryptographicHash::hash(file.readAll(), QCryptographicHash::Sha256) : QByteArray();
    return digest != m_diskDigest;
}
void EditorPane::acknowledgeDiskChange()
{
    QFile file(m_filePath);
    m_diskDigest = file.open(QIODevice::ReadOnly)
        ? QCryptographicHash::hash(file.readAll(), QCryptographicHash::Sha256) : QByteArray();
    if (!m_editor->isReadOnly()) m_editor->document()->setModified(true);
}
