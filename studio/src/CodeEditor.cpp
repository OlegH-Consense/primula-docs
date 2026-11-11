#include "CodeEditor.h"

#include "PrimulaHighlighter.h"

#include <QAbstractTextDocumentLayout>
#include <QFontDatabase>
#include <QPainter>
#include <QPaintEvent>
#include <QRegularExpression>
#include <QResizeEvent>
#include <QSyntaxHighlighter>
#include <QTextBlock>
#include <QTextCharFormat>
#include <QTextDocument>
#include <QJsonObject>
#include <QKeyEvent>
#include <QSignalBlocker>
#include <QWheelEvent>

// Ctrl+wheel changes presentation through the workspace, never document text.
// Accumulate high-resolution wheel deltas so touchpads do not jump every event.
bool CodeEditor::isBarShortcut(const QKeyEvent *event)
{
    const Qt::KeyboardModifiers modifiers = event->modifiers() & (Qt::ControlModifier | Qt::AltModifier | Qt::ShiftModifier | Qt::MetaModifier);
    if (modifiers != Qt::ControlModifier && modifiers != Qt::AltModifier) return false;
    if (event->key() == Qt::Key_Backslash) return true;
    // The backslash key of a PC keyboard: scan code 43 on Windows, 51 (evdev 43 + 8) with X11/Wayland.
#ifdef Q_OS_WIN
    return event->nativeScanCode() == 43;
#else
    return event->nativeScanCode() == 51;
#endif
}

void CodeEditor::keyPressEvent(QKeyEvent *event)
{
    if (!isReadOnly() && isBarShortcut(event)) {
        insertPlainText(QStringLiteral("|"));
        event->accept();
        return;
    }
    QPlainTextEdit::keyPressEvent(event);
}

void CodeEditor::wheelEvent(QWheelEvent *event)
{
    if (!(event->modifiers() & Qt::ControlModifier)) {
        m_zoomWheelRemainder = 0;
        QPlainTextEdit::wheelEvent(event);
        return;
    }
    m_zoomWheelRemainder += event->angleDelta().y() != 0
        ? event->angleDelta().y() : event->pixelDelta().y() * 3;
    const int steps = m_zoomWheelRemainder / 120;
    m_zoomWheelRemainder %= 120;
    if (steps != 0) emit fontZoomRequested(steps);
    event->accept();
}

namespace {

class LineNumberArea final : public QWidget
{
public:
    explicit LineNumberArea(CodeEditor *editor) : QWidget(editor), m_editor(editor) {}
    QSize sizeHint() const override { return {m_editor->lineNumberAreaWidth(), 0}; }

protected:
    void paintEvent(QPaintEvent *event) override { m_editor->lineNumberAreaPaintEvent(event); }

private:
    CodeEditor *m_editor;
};

/// Plain Markdown (README, ai-context.md, AI history): headings, emphasis, code, links, quotes.
class MarkdownHighlighter final : public QSyntaxHighlighter
{
public:
    explicit MarkdownHighlighter(QTextDocument *document) : QSyntaxHighlighter(document) {}

protected:
    void highlightBlock(const QString &text) override
    {
        // Fenced code blocks are literal; the state is the fence character and length.
        const auto fence = QRegularExpression(QStringLiteral("^ {0,3}(`{3,}|~{3,})")).match(text);
        const int previous = previousBlockState();
        if (previous > 0 || fence.hasMatch()) {
            QTextCharFormat literal;
            literal.setForeground(QColor(QStringLiteral("#9a3412")));
            setFormat(0, text.size(), literal);
            int state = previous;
            if (fence.hasMatch()) {
                const QString marker = fence.captured(1);
                const int type = marker.at(0) == QLatin1Char('`') ? 10000 : 20000;
                if (previous <= 0) state = type + marker.size();
                else if (previous / 10000 == type / 10000 && marker.size() >= previous % 10000
                         && text.mid(fence.capturedEnd()).trimmed().isEmpty()) state = -1;
            }
            setCurrentBlockState(state);
            return;
        }
        setCurrentBlockState(-1);
        QTextCharFormat heading;
        heading.setFontWeight(QFont::Bold);
        heading.setForeground(QColor(QStringLiteral("#2f6f9f")));
        apply(QRegularExpression(QStringLiteral("^#{1,6}\\s.*$")), heading, text);
        QTextCharFormat emphasis;
        emphasis.setFontItalic(true);
        apply(QRegularExpression(QStringLiteral("(?<!\\*)\\*[^*]+\\*(?!\\*)")), emphasis, text);
        QTextCharFormat strong;
        strong.setFontWeight(QFont::Bold);
        apply(QRegularExpression(QStringLiteral("\\*\\*[^*]+\\*\\*")), strong, text);
        QTextCharFormat link;
        link.setForeground(QColor(QStringLiteral("#0563c1")));
        link.setFontUnderline(true);
        apply(QRegularExpression(QStringLiteral("!?\\[[^]]*\\]\\([^)]*\\)")), link, text);
        QTextCharFormat quote;
        quote.setForeground(QColor(QStringLiteral("#666666")));
        apply(QRegularExpression(QStringLiteral("^\\s*>.*$")), quote, text);
        QTextCharFormat code;
        code.setForeground(QColor(QStringLiteral("#9a3412")));
        apply(QRegularExpression(QStringLiteral("(`+)(?!`)(.+?)(?<!`)\\1(?!`)")), code, text);
    }

private:
    void apply(const QRegularExpression &expression, const QTextCharFormat &format, const QString &text)
    {
        auto match = expression.globalMatch(text);
        while (match.hasNext()) {
            const auto current = match.next();
            setFormat(current.capturedStart(), current.capturedLength(), format);
        }
    }
};

class YamlHighlighter final : public QSyntaxHighlighter
{
public:
    explicit YamlHighlighter(QTextDocument *document) : QSyntaxHighlighter(document) {}

protected:
    void highlightBlock(const QString &text) override
    {
        QTextCharFormat key;
        key.setForeground(QColor(QStringLiteral("#2f6f9f")));
        key.setFontWeight(QFont::DemiBold);
        apply(QRegularExpression(QStringLiteral("^\\s*[-]?\\s*([A-Za-z_][A-Za-z0-9_-]*)\\s*:")), key, text, 1);

        QTextCharFormat comment;
        comment.setForeground(QColor(QStringLiteral("#707070")));
        comment.setFontItalic(true);
        apply(QRegularExpression(QStringLiteral("#.*$")), comment, text);

        QTextCharFormat scalar;
        scalar.setForeground(QColor(QStringLiteral("#8b4513")));
        apply(QRegularExpression(QStringLiteral("(['\"]).*?\\1")), scalar, text);
    }

private:
    void apply(const QRegularExpression &expression, const QTextCharFormat &format,
               const QString &text, int capture = 0)
    {
        auto match = expression.globalMatch(text);
        while (match.hasNext()) {
            const auto current = match.next();
            setFormat(current.capturedStart(capture), current.capturedLength(capture), format);
        }
    }
};

} // namespace

CodeEditor::CodeEditor(QWidget *parent)
    : QPlainTextEdit(parent), m_lineNumberArea(new LineNumberArea(this))
{
    QFont editorFont = QFontDatabase::systemFont(QFontDatabase::FixedFont);
    editorFont.setPointSize(10);
    setFont(editorFont);
    setLineWrapMode(QPlainTextEdit::WidgetWidth);

    connect(this, &QPlainTextEdit::blockCountChanged, this, &CodeEditor::updateLineNumberAreaWidth);
    connect(this, &QPlainTextEdit::updateRequest, this, &CodeEditor::updateLineNumberArea);
    connect(this, &QPlainTextEdit::cursorPositionChanged, this, &CodeEditor::highlightCurrentLine);

    updateLineNumberAreaWidth();
    highlightCurrentLine();
}

void CodeEditor::setSyntax(Syntax syntax)
{
    delete m_highlighter;
    m_highlighter = nullptr;
    if (syntax == Syntax::Markdown)
        m_highlighter = new MarkdownHighlighter(document());
    else if (syntax == Syntax::Yaml)
        m_highlighter = new YamlHighlighter(document());
    else if (syntax == Syntax::Primula || syntax == Syntax::PrimulaCode)
        m_highlighter = new PrimulaHighlighter(document(), syntax == Syntax::PrimulaCode);
}

void CodeEditor::setEditorFont(const QFont &font)
{
    setFont(font);
    updateLineNumberAreaWidth();
    m_lineNumberArea->update();
}

int CodeEditor::lineNumberAreaWidth() const
{
    int digits = 1;
    for (int count = qMax(1, blockCount()); count >= 10; count /= 10)
        ++digits;
    return 10 + fontMetrics().horizontalAdvance(QLatin1Char('9')) * digits;
}

void CodeEditor::lineNumberAreaPaintEvent(QPaintEvent *event)
{
    QPainter painter(m_lineNumberArea);
    painter.fillRect(event->rect(), palette().alternateBase());

    QTextBlock block = firstVisibleBlock();
    int blockNumber = block.blockNumber();
    int top = qRound(blockBoundingGeometry(block).translated(contentOffset()).top());
    int bottom = top + qRound(blockBoundingRect(block).height());

    while (block.isValid() && top <= event->rect().bottom()) {
        if (block.isVisible() && bottom >= event->rect().top()) {
            painter.setPen(palette().color(QPalette::PlaceholderText));
            painter.drawText(0, top, m_lineNumberArea->width() - 5, fontMetrics().height(),
                             Qt::AlignRight, QString::number(blockNumber + 1));
        }
        block = block.next();
        top = bottom;
        bottom = top + qRound(blockBoundingRect(block).height());
        ++blockNumber;
    }
}

void CodeEditor::resizeEvent(QResizeEvent *event)
{
    QPlainTextEdit::resizeEvent(event);
    const QRect contents = contentsRect();
    m_lineNumberArea->setGeometry(QRect(contents.left(), contents.top(), lineNumberAreaWidth(), contents.height()));
}

void CodeEditor::updateLineNumberAreaWidth()
{
    setViewportMargins(lineNumberAreaWidth(), 0, 0, 0);
}

void CodeEditor::updateLineNumberArea(const QRect &rect, int dy)
{
    if (dy)
        m_lineNumberArea->scroll(0, dy);
    else
        m_lineNumberArea->update(0, rect.y(), m_lineNumberArea->width(), rect.height());
    if (rect.contains(viewport()->rect()))
        updateLineNumberAreaWidth();
}

void CodeEditor::highlightCurrentLine()
{
    QList<QTextEdit::ExtraSelection> selections = m_diagnosticSelections;
    if (!isReadOnly()) {
        QTextEdit::ExtraSelection selection;
        QColor color = palette().color(QPalette::AlternateBase);
        color.setAlpha(110);
        selection.format.setBackground(color);
        selection.format.setProperty(QTextFormat::FullWidthSelection, true);
        selection.cursor = textCursor();
        selection.cursor.clearSelection();
        selections.append(selection);
    }
    if (!m_contextMark.isNull() && m_contextMark.hasSelection()) {
        // The text of context help: an amber background with a dotted underline, drawn
        // over the current line so that it stays visible while the cursor is in it.
        QTextEdit::ExtraSelection mark;
        mark.cursor = m_contextMark;
        mark.format.setBackground(QColor(255, 193, 7, 90));
        mark.format.setUnderlineStyle(QTextCharFormat::DotLine);
        mark.format.setUnderlineColor(QColor(QStringLiteral("#b45309")));
        mark.format.setToolTip(tr("Context of the open help window"));
        selections.append(mark);
    }
    setExtraSelections(selections);
}

void CodeEditor::setContextMark(int start, int end)
{
    m_contextMark = QTextCursor(document());
    m_contextMark.setPosition(qBound(0, start, document()->characterCount() - 1));
    m_contextMark.setPosition(qBound(0, end, document()->characterCount() - 1), QTextCursor::KeepAnchor);
    highlightCurrentLine();
}

void CodeEditor::clearContextMark()
{
    if (m_contextMark.isNull()) return;
    m_contextMark = QTextCursor();
    highlightCurrentLine();
}

void CodeEditor::setDiagnostics(const QJsonArray &messages)
{
    m_diagnosticSelections.clear();
    for (const auto &value : messages) {
        const auto message = value.toObject();
        const auto block = document()->findBlockByNumber(message.value("line").toInt()-1);
        if (!block.isValid()) continue;
        QTextEdit::ExtraSelection selection; selection.cursor = QTextCursor(block);
        selection.cursor.select(QTextCursor::LineUnderCursor);
        selection.format.setUnderlineStyle(QTextCharFormat::WaveUnderline);
        selection.format.setUnderlineColor(QColor(QStringLiteral("#b91c1c")));
        selection.format.setToolTip(message.value("message").toString());
        m_diagnosticSelections.append(selection);
    }
    highlightCurrentLine();
}
