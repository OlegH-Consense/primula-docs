#pragma once

#include <QPlainTextEdit>
#include <QTextCursor>
#include <QJsonArray>
#include <QHash>
#include <QSet>

class QKeyEvent;
class QPaintEvent;
class QResizeEvent;
class QSyntaxHighlighter;

class CodeEditor : public QPlainTextEdit
{
    Q_OBJECT

public:
    enum class Syntax { PlainText, Markdown, Yaml, Primula, PrimulaCode };

    explicit CodeEditor(QWidget *parent = nullptr);
    /// Select highlighting rules; syntax changes presentation, not source text.
    void setSyntax(Syntax syntax);
    /// Apply the workspace font and recalculate the line-number gutter.
    void setEditorFont(const QFont &font);
    /// Underline the lines of translator messages (JSON form, 14.2) without changing the text.
    void setDiagnostics(const QJsonArray &messages);
    /// Mark the text that context help (F1) was taken for: a framed background over
    /// [start, end) that follows edits; it stays until clearContextMark().
    void setContextMark(int start, int end);
    void clearContextMark();
    /// The marked range (an empty cursor when there is no mark).
    QTextCursor contextMark() const { return m_contextMark; }
    /// True for Ctrl+\ or Alt+\ (no other modifiers) pressed on the physical key of the backslash: the key code of
    /// the layout (a Latin layout) or the scan code (a layout where this key types another letter, e.g. Ukrainian «ґ»).
    static bool isBarShortcut(const QKeyEvent *event);
    int lineNumberAreaWidth() const;
    void lineNumberAreaPaintEvent(QPaintEvent *event);

signals:
    // Signed point-size steps; the workspace owns the persisted shared font.
    void fontZoomRequested(int steps);

protected:
    void resizeEvent(QResizeEvent *event) override;
    /// Ctrl+\ and Alt+\ insert the command bar «|» at the cursor in any keyboard layout.
    void keyPressEvent(QKeyEvent *event) override;
    void wheelEvent(QWheelEvent *event) override;

private:
    QWidget *m_lineNumberArea = nullptr;
    QList<QTextEdit::ExtraSelection> m_diagnosticSelections;
    QTextCursor m_contextMark;
    QSyntaxHighlighter *m_highlighter = nullptr;
    int m_zoomWheelRemainder = 0;

    void updateLineNumberAreaWidth();
    void updateLineNumberArea(const QRect &rect, int dy);
    void highlightCurrentLine();
};
