#include "Snippet.h"

#include <QTextBlock>
#include <QTextCursor>
#include <QTextDocument>

namespace Snippet {
namespace {

/// One parsed piece of a snippet: literal text, or a placeholder with its default text.
struct Piece
{
    int number = -1;   // -1 — literal
    QString text;
};

QList<Piece> parse(const QString &snippet)
{
    QList<Piece> pieces;
    auto literal = [&pieces](const QString &text) {
        if (pieces.isEmpty() || pieces.last().number >= 0) pieces.append({-1, QString()});
        pieces.last().text += text;
    };
    for (int i = 0; i < snippet.size(); ++i) {
        const QChar c = snippet.at(i);
        if (c == QLatin1Char('\\') && i + 1 < snippet.size()
            && (snippet.at(i + 1) == QLatin1Char('$') || snippet.at(i + 1) == QLatin1Char('}'))) {
            literal(snippet.at(++i));
            continue;
        }
        if (c != QLatin1Char('$') || i + 1 >= snippet.size()) {
            literal(c);
            continue;
        }
        // $N
        int j = i + 1;
        while (j < snippet.size() && snippet.at(j).isDigit()) ++j;
        if (j > i + 1) {
            pieces.append({snippet.mid(i + 1, j - i - 1).toInt(), QString()});
            i = j - 1;
            continue;
        }
        // ${N:default} or ${N|a,b|}
        if (snippet.at(i + 1) != QLatin1Char('{')) {
            literal(c);
            continue;
        }
        j = i + 2;
        while (j < snippet.size() && snippet.at(j).isDigit()) ++j;
        if (j == i + 2 || j >= snippet.size()) {
            literal(c);
            continue;
        }
        const int number = snippet.mid(i + 2, j - i - 2).toInt();
        if (snippet.at(j) == QLatin1Char('}')) {
            pieces.append({number, QString()});
            i = j;
        } else if (snippet.at(j) == QLatin1Char('|')) {
            const int end = int(snippet.indexOf(QStringLiteral("|}"), j + 1));
            if (end < 0) { literal(c); continue; }
            pieces.append({number, snippet.mid(j + 1, end - j - 1).section(QLatin1Char(','), 0, 0)});
            i = end + 1;
        } else if (snippet.at(j) == QLatin1Char(':')) {
            // The default runs to the matching '}' (braces inside are counted).
            int depth = 1;
            int k = j + 1;
            QString text;
            for (; k < snippet.size(); ++k) {
                const QChar d = snippet.at(k);
                if (d == QLatin1Char('\\') && k + 1 < snippet.size()) { text += snippet.at(++k); continue; }
                if (d == QLatin1Char('{')) ++depth;
                else if (d == QLatin1Char('}') && --depth == 0) break;
                text += d;
            }
            if (k >= snippet.size()) { literal(c); continue; }
            pieces.append({number, text});
            i = k;
        } else {
            literal(c);
        }
    }
    return pieces;
}

} // namespace

Expansion expand(const QString &snippet, const QString &selection, int *filled)
{
    const QList<Piece> pieces = parse(snippet);
    bool hasZero = false, hasOne = false;
    for (const Piece &piece : pieces) {
        hasZero = hasZero || piece.number == 0;
        hasOne = hasOne || piece.number == 1;
    }
    const int target = selection.isEmpty() ? -1 : hasZero ? 0 : hasOne ? 1 : -1;
    if (filled) *filled = target;
    Expansion result;
    for (const Piece &piece : pieces) {
        if (piece.number < 0) {
            result.text += piece.text;
            continue;
        }
        const QString text = piece.number == target ? selection : piece.text;
        if (!result.placeholders.contains(piece.number))
            result.placeholders.insert(piece.number, {int(result.text.size()), int(result.text.size() + text.size())});
        result.text += text;
    }
    return result;
}

QList<QPair<int, int>> insert(QTextCursor &cursor, const QString &snippet, bool block)
{
    QTextDocument *document = cursor.document();
    QString prefix, suffix;
    if (block) {
        if (cursor.hasSelection()) {
            // Widen to whole lines; a selection ending at the start of a line leaves that line out.
            QTextBlock first = document->findBlock(cursor.selectionStart());
            QTextBlock last = document->findBlock(cursor.selectionEnd());
            if (cursor.selectionEnd() == last.position() && last != first) last = last.previous();
            cursor.setPosition(first.position());
            cursor.setPosition(last.position() + last.length() - 1, QTextCursor::KeepAnchor);
        } else {
            // The construct goes onto its own line.
            const QString line = cursor.block().text();
            const int column = cursor.positionInBlock();
            if (!line.left(column).trimmed().isEmpty()) prefix = QStringLiteral("\n");
            if (!line.mid(column).trimmed().isEmpty()) suffix = QStringLiteral("\n");
        }
    }
    const QString selection = cursor.selectedText().replace(QChar::ParagraphSeparator, QLatin1Char('\n'));
    int filled = -1;
    const Expansion expansion = expand(snippet, selection, &filled);
    const int start = cursor.selectionStart() + int(prefix.size());
    cursor.beginEditBlock();
    cursor.insertText(prefix + expansion.text + suffix);
    cursor.endEditBlock();

    // Stops: the unfilled placeholders in number order, then the final position ($0 —
    // after the selection it holds — or the end of the text).
    QList<QPair<int, int>> stops;
    for (auto it = expansion.placeholders.cbegin(); it != expansion.placeholders.cend(); ++it)
        if (it.key() != 0 && it.key() != filled)
            stops.append({start + it.value().first, start + it.value().second});
    const int final = start + (expansion.placeholders.contains(0) ? expansion.placeholders.value(0).second
                                                                   : int(expansion.text.size()));
    stops.append({final, final});
    // Select the first stop; the others are returned for Tab.
    cursor.setPosition(stops.first().first);
    cursor.setPosition(stops.first().second, QTextCursor::KeepAnchor);
    stops.removeFirst();
    return stops;
}

} // namespace Snippet
