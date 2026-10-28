#pragma once

// A text buffer plus disk revision and search UI; saving must not lose external changes.

#include <QWidget>
#include <QTextDocument>
#include <QVariantMap>

#include "CodeEditor.h"

class EditorPane : public QWidget
{
    Q_OBJECT

public:
    explicit EditorPane(QWidget *parent = nullptr);

    /// Load UTF-8 path using the requested syntax/read-only policy. Return false and set errorMessage on failure.
    bool loadFile(const QString &path, bool readOnly, CodeEditor::Syntax syntax,
                  QString *errorMessage = nullptr);
    /// Show a missing-resource placeholder that Save cannot overwrite. reason is displayed to the user.
    void showUnavailable(const QString &path, CodeEditor::Syntax syntax, const QString &reason);
    bool isUnavailable() const { return m_unavailable; }
    /// Atomically save the buffer. Return false with errorMessage if the disk revision changed or writing fails.
    bool save(QString *errorMessage = nullptr);
    bool isModified() const;
    bool isReadOnly() const;
    QString filePath() const;
    QString text() const;
    QString selectedText() const;
    void insertText(const QString &text);
    CodeEditor *editor() const;
    /// Return cursor, scroll and per-editor search state; no source text is included.
    QVariantMap sessionState() const;
    /// Restore a previously persisted state, clamping positions to the current document.
    void restoreSessionState(const QVariantMap &state);

    /// Return whether the current disk digest differs from the acknowledged revision.
    bool diskChanged() const;
    /// Accept the current disk revision while keeping the buffer dirty; used by explicit Keep editor.
    void acknowledgeDiskChange();
    CodeEditor::Syntax syntax() const { return m_syntax; }
    void showSearch(bool replace = false);
    void closeSearch();
    /// Find the next/previous literal match, wrapping within this editor; return whether a match exists.
    bool findNext(bool backwards = false);
    /// Replace only a matching writable selection; otherwise select the next match. Return success.
    bool replaceCurrent();
    /// Replace literal matches in this writable document in one undo operation; return replacement count.
    int replaceAll();

signals:
    void modificationChanged(bool modified);

private:
    class QWidget *m_searchBar = nullptr;
    class QWidget *m_replaceRow = nullptr;
    class QLineEdit *m_findText = nullptr;
    class QLineEdit *m_replaceText = nullptr;
    class QCheckBox *m_matchCase = nullptr;
    class QCheckBox *m_wholeWords = nullptr;
    class QLabel *m_searchStatus = nullptr;
    QTextDocument::FindFlags searchFlags(bool backwards = false) const;
    CodeEditor *m_editor = nullptr;
    QString m_filePath;
    QByteArray m_diskDigest;
    CodeEditor::Syntax m_syntax = CodeEditor::Syntax::PlainText;
    bool m_readOnly = false;
    bool m_unavailable = false;
    class QLabel *m_unavailableNote = nullptr;
};
