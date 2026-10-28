#include "StyleEditing.h"

#include <QCoreApplication>
#include <QList>
#include <QRegularExpression>
#include <QTextBlock>
#include <QTextCursor>
#include <QTextDocument>

#include <algorithm>

namespace StyleEditing {
namespace {

/// Translation context "StyleEditing" for the messages of this file.
struct Text
{
    Q_DECLARE_TR_FUNCTIONS(StyleEditing)
};

/// One replacement in the text of the document: [start, end) becomes text.
struct Edit
{
    int start;
    int end;
    QString text;
};

/// An environment found by the line scanner: kind is ">" (clause), "!" (admonition),
/// "style" (|.X:), "block" or another command name; name is the style of |.X: and |block("X").
struct Environment
{
    QString kind;
    QString name;
    int open = -1;    // block number of the opening line
    int close = -1;   // block number of the closing line; -1 when not closed
};

const QRegularExpression::PatternOption Unicode = QRegularExpression::UseUnicodePropertiesOption;

bool isSpace(QChar c) { return c == QLatin1Char(' ') || c == QLatin1Char('\t'); }

/// Index of the ')' that closes the '(' at open, or -1. Strings in single or double
/// quotes (with backslash escapes) and nested brackets are skipped, as in the
/// Python argument lists of Primula commands (specification 3.2).
int matchParen(const QString &s, int open)
{
    int depth = 0;
    QChar quote;
    for (int i = open; i < s.size(); ++i) {
        const QChar c = s.at(i);
        if (!quote.isNull()) {
            if (c == QLatin1Char('\\')) ++i;
            else if (c == quote) quote = QChar();
            continue;
        }
        if (c == QLatin1Char('"') || c == QLatin1Char('\'')) quote = c;
        else if (c == QLatin1Char('(') || c == QLatin1Char('[') || c == QLatin1Char('{')) ++depth;
        else if (c == QLatin1Char(')') || c == QLatin1Char(']') || c == QLatin1Char('}')) {
            if (--depth == 0) return c == QLatin1Char(')') ? i : -1;
        }
    }
    return -1;
}

/// Index of the '}' that closes the body '{' at open, or -1. In markup a '|' escapes
/// the next character (|{ |} || are literal), so it is skipped with that character.
int matchBrace(const QString &s, int open)
{
    int depth = 0;
    for (int i = open; i < s.size(); ++i) {
        const QChar c = s.at(i);
        if (c == QLatin1Char('|')) ++i;
        else if (c == QLatin1Char('{')) ++depth;
        else if (c == QLatin1Char('}') && --depth == 0) return i;
    }
    return -1;
}

/// Whether the braces of markup s[start, end) are balanced (|{ and |} do not count).
bool balancedBraces(const QString &s, int start, int end)
{
    int depth = 0;
    for (int i = start; i < end; ++i) {
        const QChar c = s.at(i);
        if (c == QLatin1Char('|')) ++i;
        else if (c == QLatin1Char('{')) ++depth;
        else if (c == QLatin1Char('}') && --depth < 0) return false;
    }
    return depth == 0;
}

/// Ranges [start, end) of the top-level arguments between '(' at open and ')' at close.
/// "()" gives no arguments.
QList<QPair<int, int>> splitArgs(const QString &s, int open, int close)
{
    QList<QPair<int, int>> args;
    int depth = 0;
    int start = open + 1;
    QChar quote;
    for (int i = open + 1; i < close; ++i) {
        const QChar c = s.at(i);
        if (!quote.isNull()) {
            if (c == QLatin1Char('\\')) ++i;
            else if (c == quote) quote = QChar();
            continue;
        }
        if (c == QLatin1Char('"') || c == QLatin1Char('\'')) quote = c;
        else if (c == QLatin1Char('(') || c == QLatin1Char('[') || c == QLatin1Char('{')) ++depth;
        else if (c == QLatin1Char(')') || c == QLatin1Char(']') || c == QLatin1Char('}')) --depth;
        else if (c == QLatin1Char(',') && depth == 0) {
            args.append({start, i});
            start = i + 1;
        }
    }
    args.append({start, close});
    if (args.size() == 1 && s.mid(open + 1, close - open - 1).trimmed().isEmpty()) args.clear();
    return args;
}

/// Shrink [start, end) to exclude surrounding white space (including line breaks).
void trim(const QString &s, int &start, int &end)
{
    while (start < end && s.at(start).isSpace()) ++start;
    while (end > start && s.at(end - 1).isSpace()) --end;
}

/// The position just after the marker of a clause or heading line (|>…, |<…), or -1.
int structureMarkerEnd(const QString &line)
{
    static const QRegularExpression marker(QStringLiteral(R"(^[ \t]*\|(>+|<+)(?=[(: \t]|$))"));
    const QRegularExpressionMatch match = marker.match(line);
    return match.hasMatch() ? int(match.capturedEnd()) : -1;
}

/// Opening line of an environment: a command or short form first on the line, optional
/// arguments on the same line, then ':' and nothing but spaces or a |% comment.
/// Returns false for other lines. Control forms |if(…):, |for(…): and |def name(…): are
/// environments of kinds "if", "for", "def" closed only by |endif, |endfor, |enddef
/// (specification 3.5); |elif and |else open nothing.
bool parseOpener(const QString &line, Environment *environment)
{
    static const QRegularExpression definition(QStringLiteral(R"(^[ \t]*\|def[ \t]+[^\W\d][\w]*[ \t]*\(.*\)[ \t]*:[ \t]*(\|%.*)?$)"), Unicode);
    if (definition.match(line).hasMatch()) {
        environment->kind = QStringLiteral("def");
        return true;
    }
    static const QRegularExpression head(QStringLiteral(R"(^[ \t]*\|(>+|!|\.[\w-]+|[^\W\d][\w.]*))"), Unicode);
    static const QRegularExpression tail(QStringLiteral(R"(^:[ \t]*(\|%.*)?$)"));
    static const QRegularExpression blockName(QStringLiteral(R"(^\(\s*(["'])(.*?)\1)"));
    const QRegularExpressionMatch match = head.match(line);
    if (!match.hasMatch()) return false;
    const QString form = match.captured(1);
    if (form == QStringLiteral("elif") || form == QStringLiteral("else") || form == QStringLiteral("def")) return false;
    int end = int(match.capturedEnd());
    QString args;
    if (end < line.size() && line.at(end) == QLatin1Char('(')) {
        const int close = matchParen(line, end);
        if (close < 0) return false;
        args = line.mid(end, close - end + 1);
        end = close + 1;
    }
    if (!tail.match(line.mid(end)).hasMatch()) return false;
    if (form.startsWith(QLatin1Char('>'))) {
        environment->kind = QStringLiteral(">");
        environment->name = form;   // the level: >, >>, …
    }
    else if (form == QStringLiteral("!")) environment->kind = QStringLiteral("!");
    else if (form.startsWith(QLatin1Char('.'))) {
        environment->kind = QStringLiteral("style");
        environment->name = form.mid(1);
    } else {
        environment->kind = form;
        if (form == QStringLiteral("block")) environment->name = blockName.match(args).captured(2);
    }
    return true;
}

/// All environments of the document with their closing lines, found by a stack over
/// the lines: |end closes the innermost one, |end>, |end!, |end.X and |end name the
/// nearest one of their kind.
QList<Environment> environments(const QTextDocument *document)
{
    static const QRegularExpression closer(
        QStringLiteral(R"(^[ \t]*\|end(?:(>+)|(!)|\.([\w-]+)|[ \t]+([^\W\d][\w.]*))?[ \t]*(\|%.*)?$)"), Unicode);
    static const QRegularExpression control(QStringLiteral(R"(^[ \t]*\|end(if|for|def)[ \t]*(\|%.*)?$)"));
    auto isControl = [](const QString &kind) {
        return kind == QStringLiteral("if") || kind == QStringLiteral("for") || kind == QStringLiteral("def");
    };
    QList<Environment> found;
    QList<int> stack;   // indexes into found
    for (QTextBlock block = document->begin(); block.isValid(); block = block.next()) {
        const QString line = block.text();
        Environment opened;
        if (parseOpener(line, &opened)) {
            opened.open = block.blockNumber();
            stack.append(int(found.size()));
            found.append(opened);
            continue;
        }
        if (stack.isEmpty()) continue;
        const QRegularExpressionMatch closing = control.match(line);
        if (closing.hasMatch()) {
            int index = int(stack.size()) - 1;
            while (index >= 0 && found.at(stack.at(index)).kind != closing.captured(1)) --index;
            if (index >= 0) {
                found[stack.at(index)].close = block.blockNumber();
                stack.resize(index);
            }
            continue;
        }
        const QRegularExpressionMatch match = closer.match(line);
        if (!match.hasMatch()) continue;
        QString kind;
        QString name;
        if (!match.captured(1).isEmpty()) kind = QStringLiteral(">");
        else if (!match.captured(2).isEmpty()) kind = QStringLiteral("!");
        else if (!match.captured(3).isEmpty()) {
            kind = QStringLiteral("style");
            name = match.captured(3);
        } else if (!match.captured(4).isEmpty()) {
            kind = match.captured(4);
            if (kind == QStringLiteral("clause")) kind = QStringLiteral(">");
            else if (kind == QStringLiteral("admonition")) kind = QStringLiteral("!");
        }
        int index = int(stack.size()) - 1;
        if (!kind.isEmpty()) {
            while (index >= 0 && (found.at(stack.at(index)).kind != kind
                                  || (!name.isEmpty() && found.at(stack.at(index)).name != name)))
                --index;
        } else {
            // A bare |end never closes |if, |for, |def.
            while (index >= 0 && isControl(found.at(stack.at(index)).kind)) --index;
        }
        if (index < 0) continue;
        found[stack.at(index)].close = block.blockNumber();
        stack.resize(index);
    }
    return found;
}

/// Apply edits as one undo step; returns where the original position pos ends up.
int applyEdits(QTextCursor &cursor, QList<Edit> edits, int pos)
{
    std::sort(edits.begin(), edits.end(), [](const Edit &a, const Edit &b) { return a.start > b.start; });
    // An edit before pos shifts it; an edit over pos moves it to the start of the edit.
    int moved = pos;
    for (const Edit &edit : std::as_const(edits)) {
        if (edit.end <= pos) moved += int(edit.text.size()) - (edit.end - edit.start);
        else if (edit.start < pos) moved -= pos - edit.start;
    }
    QTextCursor editing(cursor.document());
    editing.beginEditBlock();
    for (const Edit &edit : std::as_const(edits)) {
        editing.setPosition(edit.start);
        editing.setPosition(edit.end, QTextCursor::KeepAnchor);
        editing.insertText(edit.text);
    }
    editing.endEditBlock();
    cursor.setPosition(moved);
    return moved;
}

/// The edit that deletes a whole line (block) together with its line break.
Edit deleteLine(const QTextBlock &block)
{
    const int start = block.position();
    const int end = start + block.length();   // includes the line break, except the last block
    if (block.next().isValid()) return {start, end, QString()};
    return {qMax(0, start - 1), end - 1, QString()};
}

/// The arguments of a clause or heading line starting at block: '(' position (or the
/// marker end when there are none), the ')' position, and the argument ranges.
struct StructureArgs
{
    int marker = -1;   // position after |>… / |<…
    int open = -1;     // '(' or -1
    int close = -1;
    QList<QPair<int, int>> args;
    int style = -1;    // index of the style= argument
    int value = -1;    // start of its value
};

bool structureArgs(const QString &s, const QTextBlock &block, StructureArgs *out, QString *error)
{
    const int marker = structureMarkerEnd(block.text());
    if (marker < 0) return false;
    out->marker = block.position() + marker;
    if (out->marker < s.size() && s.at(out->marker) == QLatin1Char('(')) {
        out->open = out->marker;
        out->close = matchParen(s, out->open);
        if (out->close < 0) {
            if (error) *error = Text::tr("The arguments of the line %1 are not closed.").arg(block.blockNumber() + 1);
            return false;
        }
        out->args = splitArgs(s, out->open, out->close);
        static const QRegularExpression style(QStringLiteral(R"(^\s*style\s*=(?!=)\s*)"));
        for (int i = 0; i < out->args.size(); ++i) {
            const QRegularExpressionMatch match =
                style.match(s.mid(out->args.at(i).first, out->args.at(i).second - out->args.at(i).first));
            if (match.hasMatch()) {
                out->style = i;
                out->value = out->args.at(i).first + int(match.capturedEnd());
            }
        }
    }
    return true;
}

/// Edits that set style="name" in the arguments of a clause or heading line.
void setStructureStyle(const QString &s, const StructureArgs &a, const QString &name, QList<Edit> *edits)
{
    const QString value = QStringLiteral("\"%1\"").arg(name);
    if (a.open < 0) {
        edits->append({a.marker, a.marker, QStringLiteral("(style=%1)").arg(value)});
    } else if (a.style >= 0) {
        int start = a.value;
        int end = a.args.at(a.style).second;
        trim(s, start, end);
        edits->append({start, end, value});
    } else {
        edits->append({a.close, a.close, (a.args.isEmpty() ? QString() : QStringLiteral(", ")) + QStringLiteral("style=") + value});
    }
}

/// The literal style name of a style= argument value ("X" or 'X'), or empty.
QString literalName(const QString &s, const StructureArgs &a)
{
    int start = a.value;
    int end = a.args.at(a.style).second;
    trim(s, start, end);
    const QString text = s.mid(start, end - start);
    if (text.size() >= 2 && (text.front() == QLatin1Char('"') || text.front() == QLatin1Char('\''))
        && text.back() == text.front())
        return text.mid(1, text.size() - 2);
    return QString();
}

/// Edits that delete the style= argument (and its comma; the parentheses when it is the only one).
void removeStructureStyle(const QString &s, const StructureArgs &a, QList<Edit> *edits)
{
    if (a.args.size() == 1) {
        edits->append({a.open, a.close + 1, QString()});
        return;
    }
    if (a.style == 0) {
        int next = a.args.at(1).first;
        while (next < a.close && s.at(next).isSpace()) ++next;
        edits->append({a.args.at(0).first, next, QString()});
        return;
    }
    int previousEnd = a.args.at(a.style - 1).second;
    int start = a.args.at(a.style - 1).first;
    trim(s, start, previousEnd);
    int end = a.args.at(a.style).second;
    int dummy = a.args.at(a.style).first;
    trim(s, dummy, end);
    edits->append({previousEnd, end, QString()});
}

/// One-line paragraph style |.X: text (or |.X(args): text): the name range and where the text begins.
struct LineStyle
{
    int nameStart = -1;
    int nameEnd = -1;
    int prefixStart = -1;   // the '|'
    int textStart = -1;     // first character of the text after ": "
};

bool lineStyle(const QTextBlock &block, LineStyle *out)
{
    static const QRegularExpression head(QStringLiteral(R"(^[ \t]*\|\.([\w-]+))"), Unicode);
    const QString line = block.text();
    const QRegularExpressionMatch match = head.match(line);
    if (!match.hasMatch()) return false;
    int end = int(match.capturedEnd());
    if (end < line.size() && line.at(end) == QLatin1Char('(')) {
        const int close = matchParen(line, end);
        if (close < 0) return false;
        end = close + 1;
    }
    if (end >= line.size() || line.at(end) != QLatin1Char(':')) return false;
    int text = end + 1;
    while (text < line.size() && isSpace(line.at(text))) ++text;
    if (text >= line.size() || line.mid(text).startsWith(QStringLiteral("|%"))) return false;   // an environment
    out->nameStart = block.position() + int(match.capturedStart(1));
    out->nameEnd = block.position() + int(match.capturedEnd(1));
    out->prefixStart = block.position() + int(line.indexOf(QLatin1Char('|')));
    out->textStart = block.position() + text;
    return true;
}

/// The lines a paragraph or block style applies to: those of the selection, or the
/// cursor line. A selection ending at the start of a line does not include that line.
/// Blank lines at the edges are left out.
bool selectedLines(const QTextCursor &cursor, QTextBlock *first, QTextBlock *last)
{
    QTextDocument *document = cursor.document();
    QTextBlock a = document->findBlock(cursor.selectionStart());
    QTextBlock b = document->findBlock(cursor.selectionEnd());
    if (cursor.hasSelection() && cursor.selectionEnd() == b.position() && b != a) b = b.previous();
    while (a != b && a.text().trimmed().isEmpty()) a = a.next();
    while (b != a && b.text().trimmed().isEmpty()) b = b.previous();
    *first = a;
    *last = b;
    return !a.text().trimmed().isEmpty();
}

QString indentOf(const QString &line)
{
    int i = 0;
    while (i < line.size() && isSpace(line.at(i))) ++i;
    return line.left(i);
}

/// Whether a line begins with a block form that cannot carry the one-line |.X: prefix:
/// lists, table rows, admonitions, closing markers, comments and long commands.
bool startsWithBlockForm(const QString &line)
{
    static const QRegularExpression form(QStringLiteral(R"(^[ \t]*\|([-#:!%]|end|[^\W\d]))"), Unicode);
    return form.match(line).hasMatch();
}

/// The innermost environment of kind ("style" or "block") around line, optionally of style name.
const Environment *enclosing(const QList<Environment> &all, int line, const QString &kind, const QString &name)
{
    const Environment *best = nullptr;
    for (const Environment &environment : all) {
        if (environment.kind != kind || environment.open > line) continue;
        if (environment.close >= 0 && environment.close < line) continue;
        if (environment.close < 0 && environment.open != line) continue;
        if (!name.isEmpty() && environment.name != name) continue;
        if (!best || environment.open > best->open) best = &environment;
    }
    return best;
}

/// Rename the environment opened at the cursor line (|.Y: or |block("Y"):) to name;
/// returns false when the line opens no such environment.
bool renameEnvironment(QTextCursor &cursor, const QTextBlock &line, const QString &kind,
                       const QString &name)
{
    Environment opened;
    if (!parseOpener(line.text(), &opened) || opened.kind != kind) return false;
    QList<Edit> edits;
    const QString text = line.text();
    if (kind == QStringLiteral("style")) {
        const int at = int(text.indexOf(QStringLiteral("|."))) + 2;
        edits.append({line.position() + at, line.position() + at + int(opened.name.size()), name});
        for (const Environment &environment : environments(cursor.document())) {
            if (environment.open != line.blockNumber() || environment.close < 0) continue;
            const QTextBlock closing = cursor.document()->findBlockByNumber(environment.close);
            const int dot = int(closing.text().indexOf(QStringLiteral("|end.")));
            if (dot >= 0)
                edits.append({closing.position() + dot + 5, closing.position() + dot + 5 + int(opened.name.size()), name});
        }
    } else {
        static const QRegularExpression quoted(QStringLiteral(R"(\|block\(\s*(["'])(.*?)\1)"));
        const QRegularExpressionMatch match = quoted.match(text);
        if (!match.hasMatch()) return false;
        edits.append({line.position() + int(match.capturedStart(2)), line.position() + int(match.capturedEnd(2)), name});
    }
    applyEdits(cursor, edits, cursor.position());
    return true;
}

bool applyCharacter(QTextCursor &cursor, const QString &s, const QString &name, QString *error)
{
    const QString open = QStringLiteral("|.%1{").arg(name);
    if (!cursor.hasSelection()) {
        const int pos = cursor.position();
        applyEdits(cursor, {{pos, pos, open + QStringLiteral("}")}}, pos);
        cursor.setPosition(pos + int(open.size()));
        return true;
    }
    int start = cursor.selectionStart();
    int end = cursor.selectionEnd();
    trim(s, start, end);
    if (start >= end) {
        if (error) *error = Text::tr("The selection has only spaces.");
        return false;
    }
    static const QRegularExpression emptyLine(QStringLiteral(R"(\n[ \t]*\n)"));
    if (s.mid(start, end - start).contains(emptyLine)) {
        if (error) *error = Text::tr("A character style covers text of one paragraph; the selection crosses an empty line.");
        return false;
    }
    if (!balancedBraces(s, start, end) || s.at(end - 1) == QLatin1Char('|')) {
        if (error) *error = Text::tr("The selection cuts an inline form {…}; select whole forms.");
        return false;
    }
    applyEdits(cursor, {{start, start, open}, {end, end, QStringLiteral("}")}}, end);
    return true;
}

/// Paragraph (|.X:) and block (|block("X"):) styles on lines.
bool applyLines(QTextCursor &cursor, const QString &s, const QString &name, Kind kind, QString *error)
{
    QTextBlock first, last;
    if (!selectedLines(cursor, &first, &last)) {
        if (error) *error = Text::tr("Nothing to style: the line is empty.");
        return false;
    }
    const bool paragraph = kind == Kind::Paragraph;

    if (paragraph) {
        // Clauses and headings carry their paragraph style as an argument (specification 5.2, 5.3).
        QList<Edit> edits;
        for (QTextBlock block = first; block.isValid(); block = block.next()) {
            StructureArgs args;
            if (structureArgs(s, block, &args, error)) setStructureStyle(s, args, name, &edits);
            else if (args.marker >= 0) return false;   // unclosed arguments
            if (block == last) break;
        }
        if (!edits.isEmpty()) {
            applyEdits(cursor, edits, cursor.selectionEnd());
            return true;
        }
    }

    if (first == last) {
        // Restyle an existing application on this line instead of nesting a new one.
        if (renameEnvironment(cursor, first, paragraph ? QStringLiteral("style") : QStringLiteral("block"), name))
            return true;
        LineStyle line;
        if (paragraph && lineStyle(first, &line)) {
            applyEdits(cursor, {{line.nameStart, line.nameEnd, name}}, cursor.position());
            return true;
        }
        if (paragraph && !startsWithBlockForm(first.text())) {
            const int at = first.position() + int(indentOf(first.text()).size());
            applyEdits(cursor, {{at, at, QStringLiteral("|.%1: ").arg(name)}}, cursor.position());
            return true;
        }
    }
    const QString indent = indentOf(first.text());
    const QString opener = paragraph ? QStringLiteral("|.%1:").arg(name) : QStringLiteral("|block(\"%1\"):").arg(name);
    const QString closer = paragraph ? QStringLiteral("|end.%1").arg(name) : QStringLiteral("|end block");
    const int lastEnd = last.position() + last.length() - 1;
    applyEdits(cursor, {{first.position(), first.position(), indent + opener + QLatin1Char('\n')},
                        {lastEnd, lastEnd, QLatin1Char('\n') + indent + closer}},
               lastEnd);
    return true;
}

} // namespace

QList<EnvironmentInfo> environmentList(const QTextDocument *document)
{
    QList<EnvironmentInfo> list;
    for (const Environment &environment : environments(document)) {
        EnvironmentInfo info{environment.kind, environment.name, environment.open, environment.close, QString()};
        const QString &kind = environment.kind;
        if (kind == QStringLiteral(">")) info.closing = QStringLiteral("|end") + environment.name;
        else if (kind == QStringLiteral("!")) info.closing = QStringLiteral("|end!");
        else if (kind == QStringLiteral("style")) info.closing = QStringLiteral("|end.") + environment.name;
        else if (kind == QStringLiteral("if") || kind == QStringLiteral("for") || kind == QStringLiteral("def"))
            info.closing = QStringLiteral("|end") + kind;
        else if (kind == QStringLiteral("code") || kind == QStringLiteral("comment") || kind == QStringLiteral("verbatim"))
            info.closing = QStringLiteral("|end");   // closed only by a bare |end
        else info.closing = QStringLiteral("|end ") + kind;
        list.append(info);
    }
    return list;
}

Kind kindFromDump(const QString &kind)
{
    if (kind == QStringLiteral("character")) return Kind::Character;
    if (kind == QStringLiteral("paragraph")) return Kind::Paragraph;
    if (kind == QStringLiteral("block")) return Kind::Block;
    return Kind::Other;
}

bool apply(QTextCursor &cursor, const QString &name, Kind kind, QString *error)
{
    static const QRegularExpression valid(QStringLiteral(R"(^[\w-]+$)"), Unicode);
    if (!valid.match(name).hasMatch()) {
        if (error) *error = Text::tr("Style %1 has a computed or invalid name.").arg(name);
        return false;
    }
    const QString s = cursor.document()->toPlainText();
    switch (kind) {
    case Kind::Character:
        return applyCharacter(cursor, s, name, error);
    case Kind::Paragraph:
    case Kind::Block:
        return applyLines(cursor, s, name, kind, error);
    case Kind::Other:
        break;
    }
    if (error) *error = Text::tr("A table, list, frame or page style is set by the style= argument of its command.");
    return false;
}

bool remove(QTextCursor &cursor, const QString &name, QString *error)
{
    QTextDocument *document = cursor.document();
    const QString s = document->toPlainText();
    const int pos = cursor.selectionStart();
    const QTextBlock line = document->findBlock(pos);

    // 1. The innermost |.X{…} around the cursor (the cursor right after '}' still counts).
    static const QRegularExpression inlineStyle(QStringLiteral(R"(\|\.([\w-]+))"), Unicode);
    int bestStart = -1, bestOpen = -1, bestClose = -1;
    for (auto it = inlineStyle.globalMatch(s); it.hasNext();) {
        const QRegularExpressionMatch match = it.next();
        if (match.capturedStart() > pos) break;
        if (!name.isEmpty() && match.captured(1) != name) continue;
        if (match.capturedStart() > 0 && s.at(match.capturedStart() - 1) == QLatin1Char('|')) continue;   // ||.
        int open = int(match.capturedEnd());
        if (open < s.size() && s.at(open) == QLatin1Char('(')) {
            const int close = matchParen(s, open);
            if (close < 0) continue;
            open = close + 1;
        }
        if (open >= s.size() || s.at(open) != QLatin1Char('{')) continue;
        const int close = matchBrace(s, open);
        if (close < 0 || close + 1 < pos) continue;
        bestStart = int(match.capturedStart());
        bestOpen = open;
        bestClose = close;
    }
    if (bestStart >= 0) {
        applyEdits(cursor, {{bestStart, bestOpen + 1, QString()}, {bestClose, bestClose + 1, QString()}}, pos);
        return true;
    }

    // 2. A form of the cursor line: style= of a clause or heading, or a one-line |.X: prefix.
    StructureArgs args;
    if (structureArgs(s, line, &args, error) && args.style >= 0
        && (name.isEmpty() || literalName(s, args) == name)) {
        QList<Edit> edits;
        removeStructureStyle(s, args, &edits);
        applyEdits(cursor, edits, pos);
        return true;
    }
    LineStyle prefix;
    if (lineStyle(line, &prefix) && (name.isEmpty() || s.mid(prefix.nameStart, prefix.nameEnd - prefix.nameStart) == name)) {
        applyEdits(cursor, {{prefix.prefixStart, prefix.textStart, QString()}}, pos);
        return true;
    }

    // 3. The innermost |.X: … |end.X or |block("X"): … |end block around the cursor line.
    const QList<Environment> all = environments(document);
    const Environment *style = enclosing(all, line.blockNumber(), QStringLiteral("style"), name);
    const Environment *block = enclosing(all, line.blockNumber(), QStringLiteral("block"), name);
    const Environment *target = !style ? block : !block ? style : style->open > block->open ? style : block;
    if (target) {
        if (target->close < 0) {
            if (error) *error = Text::tr("The environment opened on line %1 has no closing line.").arg(target->open + 1);
            return false;
        }
        const QTextBlock opening = document->findBlockByNumber(target->open);
        const QTextBlock closing = document->findBlockByNumber(target->close);
        applyEdits(cursor, {deleteLine(closing), deleteLine(opening)}, pos);
        return true;
    }
    if (error)
        *error = name.isEmpty() ? Text::tr("No style is applied at the cursor.")
                                : Text::tr("Style %1 is not applied at the cursor.").arg(name);
    return false;
}

} // namespace StyleEditing
