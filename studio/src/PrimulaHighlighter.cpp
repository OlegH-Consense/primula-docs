#include "PrimulaHighlighter.h"

#include <QApplication>
#include <QDataStream>
#include <QPalette>
#include <QRegularExpression>
#include <QSet>
#include <QTextBlockUserData>
#include <QTextDocument>

namespace {

/// Block kinds of a line (what the line belongs to).
enum class Mode : quint8 { Normal, Header, Code, Comment, Verbatim, CodeFile };

/// Built-in commands (appendix 2.1); control commands are shown apart.
const QSet<QString> kControl{QStringLiteral("if"), QStringLiteral("elif"), QStringLiteral("else"),
                             QStringLiteral("for"), QStringLiteral("def"), QStringLiteral("let"),
                             QStringLiteral("export"), QStringLiteral("call"), QStringLiteral("code"),
                             QStringLiteral("comment"), QStringLiteral("verbatim"), QStringLiteral("include"),
                             QStringLiteral("import"), QStringLiteral("document"), QStringLiteral("part")};
const QSet<QString> kBuiltin{
    QStringLiteral("table"), QStringLiteral("row"), QStringLiteral("cell"), QStringLiteral("caption"),
    QStringLiteral("page"), QStringLiteral("newpage"), QStringLiteral("newcolumn"), QStringLiteral("section"),
    QStringLiteral("header"), QStringLiteral("footer"), QStringLiteral("field"), QStringLiteral("img"),
    QStringLiteral("figure"), QStringLiteral("frame"), QStringLiteral("watermark"), QStringLiteral("scope"),
    QStringLiteral("appendix"), QStringLiteral("toc"), QStringLiteral("list_of"), QStringLiteral("footnote"),
    QStringLiteral("endnote"), QStringLiteral("set"), QStringLiteral("block"), QStringLiteral("list"),
    QStringLiteral("fmt"), QStringLiteral("abbr"), QStringLiteral("index"), QStringLiteral("link"),
    QStringLiteral("toc_entry"), QStringLiteral("parallel"), QStringLiteral("segment"), QStringLiteral("track")};
/// Predefined top-level keys of the YAML header (2.3, 10.6, 11.1; names of decision 129).
/// A test keeps the set equal to the top-level keys of the translator's catalogue.
const QSet<QString> kHeaderKeys{
    QStringLiteral("kind"), QStringLiteral("primula"), QStringLiteral("doc"), QStringLiteral("params"),
    QStringLiteral("styles"), QStringLiteral("structure"), QStringLiteral("references"), QStringLiteral("name"),
    QStringLiteral("language"), QStringLiteral("on_conflict"), QStringLiteral("keys"), QStringLiteral("limits"),
    QStringLiteral("build_date"), QStringLiteral("targets"), QStringLiteral("ref_documents"), QStringLiteral("extends"),
    QStringLiteral("doc_defaults"),
    QStringLiteral("paragraphs"), QStringLiteral("characters"), QStringLiteral("blocks"), QStringLiteral("tables"),
    QStringLiteral("lists"), QStringLiteral("frames"), QStringLiteral("pages"), QStringLiteral("defaults")};
/// Python keywords of the computing core (12.2) and constants.
const QSet<QString> kPyKeywords{
    QStringLiteral("and"), QStringLiteral("or"), QStringLiteral("not"), QStringLiteral("in"), QStringLiteral("is"),
    QStringLiteral("if"), QStringLiteral("else"), QStringLiteral("elif"), QStringLiteral("for"),
    QStringLiteral("while"), QStringLiteral("def"), QStringLiteral("return"), QStringLiteral("break"),
    QStringLiteral("continue"), QStringLiteral("pass"), QStringLiteral("lambda"), QStringLiteral("True"),
    QStringLiteral("False"), QStringLiteral("None")};
/// Inline forms with a body and the format of the body.
const QString kInlineMarks = QStringLiteral("*/_^,—`\"?");

} // namespace

/// The state carried from line to line.
struct PrimulaHighlighter::State
{
    Mode mode = Mode::Normal;
    int parens = 0;                 ///< open parentheses of arguments continued on the next line
    QChar quote;                    ///< an open triple-quoted string inside them (' or ")
    int commentDepth = 0;           ///< environments opened inside |comment:
    QString verbatimEnd;            ///< the closing line of |verbatim
    QString bodies;                 ///< open bodies: an inline mark, 'S' (style), 'C' (command), 'B' (brace)
    bool afterHeader = false;       ///< the YAML header is closed (or there is none)
};

/// The state at the end of a line, kept with the line (QTextBlockUserData).
class PrimulaStateData final : public QTextBlockUserData
{
public:
    QByteArray serialized;
    QList<QPair<int, int>> code;   ///< code ranges of the line (not part of the state)
};

PrimulaHighlighter::PrimulaHighlighter(QTextDocument *document, bool codeFile)
    : QSyntaxHighlighter(document), m_codeFile(codeFile)
{
    // Darker or lighter colours by the editor background.
    m_dark = QApplication::palette().color(QPalette::Base).lightness() < 128;
}

QTextCharFormat PrimulaHighlighter::format(Role role) const
{
    auto color = [this](const char *light, const char *dark) {
        return QColor(QString::fromLatin1(m_dark ? dark : light));
    };
    QTextCharFormat f;
    switch (role) {
    case Role::Comment: f.setForeground(color("#707070", "#9a9a9a")); f.setFontItalic(true); break;
    case Role::Escape: f.setForeground(color("#008080", "#4fc1c1")); break;
    case Role::HeaderDelimiter: f.setForeground(color("#707070", "#9a9a9a")); f.setFontWeight(QFont::Bold); break;
    case Role::HeaderKey: f.setForeground(color("#2f6f9f", "#7fb3e0")); break;
    case Role::KnownHeaderKey: f.setForeground(color("#2f6f9f", "#7fb3e0")); f.setFontWeight(QFont::Bold); break;
    case Role::YamlValue: f.setForeground(color("#8b4513", "#d7a574")); break;
    case Role::Heading: f.setForeground(color("#1f4e79", "#9cc9f0")); f.setFontWeight(QFont::Bold); break;
    case Role::Clause: f.setForeground(color("#7a3e9d", "#c792ea")); f.setFontWeight(QFont::Bold); break;
    case Role::ListMarker: f.setForeground(color("#7a3e9d", "#c792ea")); f.setFontWeight(QFont::Bold); break;
    case Role::Admonition: f.setForeground(color("#c2410c", "#f4a261")); f.setFontWeight(QFont::Bold); break;
    case Role::Table: f.setForeground(color("#047857", "#5fd3a8")); f.setFontWeight(QFont::Bold); break;
    case Role::Control: f.setForeground(color("#a3156b", "#f07ac0")); f.setFontWeight(QFont::Bold); break;
    case Role::Builtin: f.setForeground(color("#1d4ed8", "#82aaff")); f.setFontWeight(QFont::Bold); break;
    case Role::Command: f.setForeground(color("#1d4ed8", "#82aaff")); break;
    case Role::Style: f.setForeground(color("#15803d", "#8bd98b")); break;
    case Role::Reference: f.setForeground(color("#0563c1", "#6cb6ff")); f.setFontUnderline(true); break;
    case Role::Expression: f.setForeground(color("#a16207", "#e5c07b")); f.setFontWeight(QFont::Bold); break;
    case Role::InlineMarker: f.setForeground(color("#008080", "#4fc1c1")); f.setFontWeight(QFont::Bold); break;
    case Role::PyString: f.setForeground(color("#9a3412", "#e5a07b")); break;
    case Role::PyNumber: f.setForeground(color("#0e7490", "#56c4d6")); break;
    case Role::PyKeyword: f.setForeground(color("#a3156b", "#f07ac0")); break;
    case Role::Verbatim: f.setForeground(color("#5b5b5b", "#b0b0b0")); f.setBackground(color("#f4f4f4", "#2a2a2a")); break;
    case Role::Invalid:
        f.setUnderlineStyle(QTextCharFormat::WaveUnderline);
        f.setUnderlineColor(QColor(QStringLiteral("#dc2626")));
        f.setForeground(color("#b91c1c", "#ff6b6b"));
        break;
    }
    return f;
}

void PrimulaHighlighter::mark(int start, int length, Role role)
{
    if (length > 0)
        setFormat(start, length, format(role));
}

void PrimulaHighlighter::mergeFormat(int start, int length, const QTextCharFormat &extra)
{
    for (int i = start; i < start + length; ++i) {
        QTextCharFormat current = QSyntaxHighlighter::format(i);
        current.merge(extra);
        setFormat(i, 1, current);
    }
}

// ----------------------------------------------------------------------
// Lines
// ----------------------------------------------------------------------

static QByteArray serializeState(int mode, int parens, QChar quote, int depth, const QString &verbatim,
                                 const QString &bodies, bool afterHeader)
{
    QByteArray data;
    QDataStream stream(&data, QIODevice::WriteOnly);
    stream << mode << parens << quote << depth << verbatim << bodies << afterHeader;
    return data;
}

QStringList PrimulaHighlighter::knownHeaderKeys()
{
    return QStringList(kHeaderKeys.cbegin(), kHeaderKeys.cend());
}

bool PrimulaHighlighter::isCode(const QTextBlock &block, int column)
{
    // Every user data of a document with a PrimulaHighlighter is a PrimulaStateData.
    const auto *data = dynamic_cast<const PrimulaStateData *>(block.userData());
    if (!data) return false;
    for (const auto &[from, to] : data->code)
        if (column >= from && column <= to) return true;
    return false;
}

void PrimulaHighlighter::highlightBlock(const QString &text)
{
    State state;
    m_code.clear();
    const QTextBlock previous = currentBlock().previous();
    if (auto *data = previous.isValid() ? static_cast<PrimulaStateData *>(previous.userData()) : nullptr) {
        QDataStream stream(data->serialized);
        int mode = 0;
        stream >> mode >> state.parens >> state.quote >> state.commentDepth >> state.verbatimEnd >> state.bodies
               >> state.afterHeader;
        state.mode = Mode(mode);
    }
    const bool openingHeader = !previous.isValid() && text.trimmed() == QStringLiteral("---");
    if (!previous.isValid()) {
        // The first line: a YAML header starts only here.
        state.afterHeader = !openingHeader;
        state.mode = openingHeader ? Mode::Header : m_codeFile ? Mode::CodeFile : Mode::Normal;
    }

    if (openingHeader) {
        mark(0, text.size(), Role::HeaderDelimiter);
    } else switch (state.mode) {
    case Mode::Header:
        if (text.trimmed() == QStringLiteral("---") || text.trimmed() == QStringLiteral("...")) {
            mark(0, text.size(), Role::HeaderDelimiter);
            state.afterHeader = true;
            state.mode = m_codeFile ? Mode::CodeFile : Mode::Normal;
        } else {
            highlightYaml(text);
        }
        break;
    case Mode::CodeFile:
        highlightPython(text, 0, text.size());
        break;
    case Mode::Code:
        if (QRegularExpression(QStringLiteral("^\\s*\\|end\\s*$")).match(text).hasMatch()) {
            mark(text.indexOf(QLatin1Char('|')), 4, Role::Control);
            state.mode = Mode::Normal;
        } else {
            highlightPython(text, 0, text.size());
        }
        break;
    case Mode::Verbatim: {
        const bool ownMarker = !state.verbatimEnd.isEmpty();
        const bool closes = ownMarker ? text.trimmed() == state.verbatimEnd
                                      : QRegularExpression(QStringLiteral("^\\s*\\|end\\s*$")).match(text).hasMatch();
        if (closes) {
            mark(0, text.size(), Role::Control);
            state.mode = Mode::Normal;
            state.verbatimEnd.clear();
        } else {
            mark(0, text.size(), Role::Verbatim);
        }
        break;
    }
    case Mode::Comment: {
        mark(0, text.size(), Role::Comment);
        // Only the balance of environments is checked inside a block comment (3.7).
        static const QRegularExpression opens(QStringLiteral("^\\s*\\|[^\\s|%].*:\\s*(\\|%.*)?$"));
        static const QRegularExpression closes(QStringLiteral("^\\s*\\|end(\\b|[>!.\\s]|$)"));
        if (closes.match(text).hasMatch()) {
            if (state.commentDepth == 0) {
                mark(text.indexOf(QLatin1Char('|')), text.trimmed().size(), Role::Control);
                state.mode = Mode::Normal;
            } else {
                --state.commentDepth;
            }
        } else if (opens.match(text).hasMatch()) {
            ++state.commentDepth;
        }
        break;
    }
    case Mode::Normal:
        highlightMarkup(text, 0, state, QTextCharFormat());
        break;
    }

    auto *data = new PrimulaStateData;
    data->serialized = serializeState(int(state.mode), state.parens, state.quote, state.commentDepth,
                                      state.verbatimEnd, state.bodies, state.afterHeader);
    data->code = m_code;
    setCurrentBlockUserData(data);
    setCurrentBlockState(int(qHash(data->serialized) & 0x7fffffff));
}

// ----------------------------------------------------------------------
// Markup
// ----------------------------------------------------------------------

void PrimulaHighlighter::highlightMarkup(const QString &text, int from, State &state, const QTextCharFormat &base)
{
    int i = from;
    QTextCharFormat lineBase = base;
    // Arguments continued from the previous line.
    if (state.parens > 0) {
        i = highlightArguments(text, i, state);
        if (state.parens > 0) return;
    }

    // Forms at the start of a line.
    if (i == 0) {
        static const QRegularExpression leading(QStringLiteral("^(\\s*)\\|"));
        const auto start = leading.match(text);
        if (start.hasMatch()) {
            const int bar = start.capturedLength(1);
            const QString rest = text.mid(bar + 1);
            static const QRegularExpression closing(QStringLiteral("^(end(?:if|for|def)?)(?:(>+|!|\\.[\\p{L}\\p{N}_'-]+)|(\\s+[\\p{L}_][\\p{L}\\p{N}_]*))?\\s*(\\|%.*)?$"));
            const auto end = closing.match(rest);
            if (end.hasMatch()) {
                // `|end`, `|endif`, `|end>`, `|end!`, `|end.Name`, `|end name`: the whole marker.
                const int markerEnd = qMax(end.capturedEnd(1), qMax(end.capturedEnd(2), end.capturedEnd(3)));
                mark(bar, 1 + markerEnd, Role::Control);
                if (!end.captured(4).isEmpty())
                    mark(bar + 1 + end.capturedStart(4), end.capturedLength(4), Role::Comment);
                return;
            }
            static const QRegularExpression block(QStringLiteral("^(code|comment|verbatim)(\\([^)]*\\))?:\\s*(\\|%.*)?$"));
            const auto blockMatch = block.match(rest);
            if (blockMatch.hasMatch()) {
                mark(bar, 1 + blockMatch.capturedLength(1), Role::Control);
                if (!blockMatch.captured(2).isEmpty())
                    highlightPython(text, bar + 1 + blockMatch.capturedStart(2), bar + 1 + blockMatch.capturedEnd(2));
                const QString kind = blockMatch.captured(1);
                if (kind == QStringLiteral("code")) state.mode = Mode::Code;
                else if (kind == QStringLiteral("comment")) { state.mode = Mode::Comment; state.commentDepth = 0; }
                else {
                    state.mode = Mode::Verbatim;
                    static const QRegularExpression endArg(QStringLiteral("end\\s*=\\s*[\"']([^\"']*)[\"']"));
                    state.verbatimEnd = endArg.match(blockMatch.captured(2)).captured(1);
                }
                return;
            }
            const QChar first = rest.isEmpty() ? QChar() : rest.at(0);
            Role role = Role::Heading;
            int length = 0;
            if (first == QLatin1Char('<')) {
                while (length < rest.size() && rest.at(length) == QLatin1Char('<')) ++length;
                role = Role::Heading;
                lineBase = format(Role::Heading);
            } else if (first == QLatin1Char('>')) {
                while (length < rest.size() && rest.at(length) == QLatin1Char('>')) ++length;
                role = Role::Clause;
            } else if (first == QLatin1Char('-') || first == QLatin1Char('#')) {
                while (length < rest.size() && (rest.at(length) == QLatin1Char('-') || rest.at(length) == QLatin1Char('#')))
                    ++length;
                role = Role::ListMarker;
            } else if (first == QLatin1Char('!')) {
                length = 1;
                role = Role::Admonition;
            } else if (first == QLatin1Char(':')) {
                length = 1;
                role = Role::Table;
            }
            if (length > 0) {
                mark(bar, 1 + length, role);
                i = bar + 1 + length;
                if (i < text.size() && text.at(i) == QLatin1Char('(')) {
                    i = highlightArguments(text, i, state);
                    if (state.parens > 0) return;
                }
                if (role == Role::Admonition && i < text.size() && text.at(i) == QLatin1Char(':'))
                    mark(i++, 1, Role::Admonition);
                if (role == Role::Clause && i < text.size() && text.at(i) == QLatin1Char(':'))
                    mark(i++, 1, Role::Clause);
            }
        }
    }

    // The rest of the line: text, inline forms, commands.
    auto bodyFormat = [this, &state, &lineBase]() {
        QTextCharFormat f = lineBase;
        for (const QChar kind : std::as_const(state.bodies)) {
            switch (kind.unicode()) {
            case '*': f.setFontWeight(QFont::Bold); break;
            case '/': f.setFontItalic(true); break;
            case '_': f.setFontUnderline(true); break;
            case '^': f.setVerticalAlignment(QTextCharFormat::AlignSuperScript); break;
            case ',': f.setVerticalAlignment(QTextCharFormat::AlignSubScript); break;
            case 0x2014: f.setFontStrikeOut(true); break;
            case '`': f.setForeground(format(Role::PyString).foreground()); f.setFontFixedPitch(true); break;
            case '?': f.setBackground(QColor(m_dark ? "#5c4a00" : "#fff1a8")); break;
            default: break;
            }
        }
        return f;
    };
    static const QRegularExpression identifier(QStringLiteral("^[\\p{L}\\p{Nl}_][\\p{L}\\p{N}_]*(?:\\.[\\p{L}\\p{Nl}_][\\p{L}\\p{N}_]*)*"));
    static const QRegularExpression styleName(QStringLiteral("^[\\p{L}\\p{Nl}_][\\p{L}\\p{N}_'-]*"));
    int textStart = i;
    auto flushText = [&](int upTo) {
        if (upTo > textStart) {
            const QTextCharFormat f = bodyFormat();
            if (f != QTextCharFormat()) setFormat(textStart, upTo - textStart, f);
        }
    };
    while (i < text.size()) {
        const QChar c = text.at(i);
        if (c == QLatin1Char('}') && !state.bodies.isEmpty()) {
            flushText(i);
            const QChar kind = state.bodies.back();
            state.bodies.chop(1);
            if (kind != QLatin1Char('B'))
                mark(i, 1, kind == QLatin1Char('C') ? Role::Command : kind == QLatin1Char('S') ? Role::Style
                                                                                           : Role::InlineMarker);
            textStart = ++i;
            continue;
        }
        if (c == QLatin1Char('{') && !state.bodies.isEmpty()) {
            // Braces inside a body are counted by balance (3.2).
            state.bodies.append(QLatin1Char('B'));
            ++i;
            continue;
        }
        if (c != QLatin1Char('|')) {
            ++i;
            continue;
        }
        flushText(i);
        const QChar next = i + 1 < text.size() ? text.at(i + 1) : QChar();
        if (next.isNull() || next.isSpace() || next.isDigit()) {
            mark(i, 1, Role::Invalid);
            textStart = ++i;
            continue;
        }
        if (next == QLatin1Char('%')) {
            mark(i, text.size() - i, Role::Comment);
            return;
        }
        if (QStringLiteral("|{};~\\").contains(next)) {
            mark(i, 2, Role::Escape);
            textStart = i += 2;
            continue;
        }
        if (next == QLatin1Char('(') || ((next == QLatin1Char('=') || next == QLatin1Char('@'))
                                         && i + 2 < text.size() && text.at(i + 2) == QLatin1Char('('))) {
            const int open = next == QLatin1Char('(') ? i + 1 : i + 2;
            mark(i, open - i, next == QLatin1Char('@') ? Role::Reference : Role::Expression);
            i = highlightArguments(text, open, state);
            if (state.parens > 0) return;
            textStart = i;
            continue;
        }
        if (next == QLatin1Char('.')) {
            int j = i + 2;
            const auto name = styleName.match(text.mid(j));
            if (name.hasMatch()) {
                j += name.capturedLength();
                mark(i, j - i, Role::Style);
            } else if (j < text.size() && text.at(j) == QLatin1Char('(')) {
                mark(i, 2, Role::Style);
                j = highlightArguments(text, j, state);
                if (state.parens > 0) return;
            } else {
                mark(i, 2, Role::Invalid);
                textStart = i += 2;
                continue;
            }
            if (j < text.size() && text.at(j) == QLatin1Char('(')) {
                j = highlightArguments(text, j, state);
                if (state.parens > 0) return;
            }
            if (j < text.size() && text.at(j) == QLatin1Char('{')) {
                mark(j++, 1, Role::Style);
                state.bodies.append(QLatin1Char('S'));
            } else if (j < text.size() && text.at(j) == QLatin1Char(':')) {
                mark(j++, 1, Role::Style);
            }
            textStart = i = j;
            continue;
        }
        if (kInlineMarks.contains(next)) {
            int j = i + 2;
            if (j < text.size() && text.at(j) == QLatin1Char('(')) {
                j = highlightArguments(text, j, state);
                if (state.parens > 0) return;
            }
            if (j < text.size() && text.at(j) == QLatin1Char('{')) {
                mark(i, 2, Role::InlineMarker);
                mark(j, 1, Role::InlineMarker);
                state.bodies.append(next);
                textStart = i = j + 1;
            } else {
                mark(i, 2, Role::Invalid);
                textStart = i = j;
            }
            continue;
        }
        if (next == QLatin1Char('&')) {
            mark(i, 2, Role::Table);
            int j = i + 2;
            if (j < text.size() && text.at(j) == QLatin1Char('(')) {
                j = highlightArguments(text, j, state);
                if (state.parens > 0) return;
            }
            textStart = i = j;
            continue;
        }
        const auto name = identifier.match(text.mid(i + 1));
        if (name.hasMatch()) {
            const QString command = name.captured();
            const QString head = command.section(QLatin1Char('.'), 0, 0);
            const Role role = kControl.contains(command) ? Role::Control
                            : (kBuiltin.contains(head) && (head != QStringLiteral("field") || command.contains(QLatin1Char('.'))))
                              ? Role::Builtin : Role::Command;
            int j = i + 1 + name.capturedLength();
            mark(i, j - i, role);
            if (j < text.size() && text.at(j) == QLatin1Char('(')) {
                j = highlightArguments(text, j, state);
                if (state.parens > 0) return;
            }
            if (j < text.size() && text.at(j) == QLatin1Char('{')) {
                mark(j++, 1, role);
                state.bodies.append(QLatin1Char('C'));
            } else if (j < text.size() && text.at(j) == QLatin1Char(':') && i == text.indexOf(QLatin1Char('|'))) {
                mark(j++, 1, role);
            }
            textStart = i = j;
            continue;
        }
        // Structural forms inside a line, reserved and unknown symbols.
        mark(i, 2, Role::Invalid);
        textStart = i += 2;
    }
    flushText(text.size());
}

// ----------------------------------------------------------------------
// Arguments and code (the Python subset of 12.2)
// ----------------------------------------------------------------------

int PrimulaHighlighter::highlightArguments(const QString &text, int from, State &state)
{
    // from: an opening parenthesis, or the continuation of arguments (state.parens > 0).
    int i = from;
    if (state.parens == 0) {
        mark(i, 1, Role::Expression);
        state.parens = 1;
        ++i;
    }
    const int start = i;
    while (i < text.size() && state.parens > 0) {
        const QChar c = text.at(i);
        if (!state.quote.isNull()) {
            // Inside a triple-quoted string continued over lines.
            const QString triple(3, state.quote);
            const int close = text.indexOf(triple, i);
            if (close < 0) {
                mark(i, text.size() - i, Role::PyString);
                return text.size();
            }
            mark(i, close + 3 - i, Role::PyString);
            i = close + 3;
            state.quote = QChar();
            continue;
        }
        if (c == QLatin1Char('"') || c == QLatin1Char('\'')) {
            if (text.mid(i, 3) == QString(3, c)) {
                const int close = text.indexOf(QString(3, c), i + 3);
                if (close < 0) {
                    mark(i, text.size() - i, Role::PyString);
                    state.quote = c;
                    return text.size();
                }
                mark(i, close + 3 - i, Role::PyString);
                i = close + 3;
                continue;
            }
            int j = i + 1;
            while (j < text.size() && text.at(j) != c) {
                if (text.at(j) == QLatin1Char('\\')) ++j;
                ++j;
            }
            // An f/r/b prefix belongs to the string.
            int begin = i;
            while (begin > start && QStringLiteral("fFrRbB").contains(text.at(begin - 1))
                   && (begin - 1 == start || !text.at(begin - 2).isLetterOrNumber()))
                --begin;
            mark(begin, qMin(j + 1, int(text.size())) - begin, Role::PyString);
            i = j + 1;
            continue;
        }
        if (c == QLatin1Char('(') || c == QLatin1Char('[') || c == QLatin1Char('{')) {
            ++state.parens;
        } else if (c == QLatin1Char(')') || c == QLatin1Char(']') || c == QLatin1Char('}')) {
            --state.parens;
            if (state.parens == 0) {
                highlightPython(text, start, i);
                mark(i, 1, Role::Expression);
                return i + 1;
            }
        }
        ++i;
    }
    highlightPython(text, start, i);
    return i;
}

void PrimulaHighlighter::highlightPython(const QString &text, int from, int to)
{
    m_code.append({from, to});
    static const QRegularExpression token(QStringLiteral(
        "(#.*$)|([fFrRbB]{0,2}(?:\"\"\"|'''|\"(?:[^\"\\\\]|\\\\.)*\"?|'(?:[^'\\\\]|\\\\.)*'?))"
        "|(\\b\\d[\\d_]*(?:\\.\\d[\\d_]*)?(?:[eE][+-]?\\d+)?\\b)|([\\p{L}_][\\p{L}\\p{N}_]*)"));
    auto matches = token.globalMatch(text.left(to), from);
    while (matches.hasNext()) {
        const auto match = matches.next();
        if (match.capturedLength(1)) {
            // `#` starts a comment only in code blocks; in arguments it is a character of a string.
            mark(match.capturedStart(1), match.capturedLength(1), Role::Comment);
            break;
        }
        if (match.capturedLength(2) && QSyntaxHighlighter::format(match.capturedStart(2)) == format(Role::PyString))
            continue;
        if (match.capturedLength(2)) mark(match.capturedStart(2), match.capturedLength(2), Role::PyString);
        else if (match.capturedLength(3)) mark(match.capturedStart(3), match.capturedLength(3), Role::PyNumber);
        else if (match.capturedLength(4) && kPyKeywords.contains(match.captured(4)))
            mark(match.capturedStart(4), match.capturedLength(4), Role::PyKeyword);
    }
}

void PrimulaHighlighter::highlightYaml(const QString &text)
{
    static const QRegularExpression key(QStringLiteral("^(\\s*-?\\s*)([\\p{L}_][\\p{L}\\p{N}_.-]*)\\s*:"));
    static const QRegularExpression comment(QStringLiteral("(^|\\s)#.*$"));
    static const QRegularExpression scalar(QStringLiteral("([\"']).*?\\1"));
    const auto match = key.match(text);
    if (match.hasMatch()) {
        const bool topLevel = match.capturedLength(1) == 0;
        mark(match.capturedStart(2), match.capturedLength(2),
             topLevel && kHeaderKeys.contains(match.captured(2)) ? Role::KnownHeaderKey : Role::HeaderKey);
    }
    auto strings = scalar.globalMatch(text);
    while (strings.hasNext()) {
        const auto s = strings.next();
        mark(s.capturedStart(), s.capturedLength(), Role::YamlValue);
    }
    const auto c = comment.match(text);
    if (c.hasMatch()) mark(c.capturedStart(), c.capturedLength(), Role::Comment);
}
