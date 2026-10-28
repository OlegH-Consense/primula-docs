#include "EditorAssist.h"

#include "CodeEditor.h"
#include "CommandCatalog.h"
#include "HeaderAssist.h"
#include "PrimulaHighlighter.h"
#include "Snippet.h"
#include "StyleEditing.h"

#include <QAbstractItemView>
#include <QCompleter>
#include <QHelpEvent>
#include <QContextMenuEvent>
#include <QCursor>
#include <QDate>
#include <QKeyEvent>
#include <QMenu>
#include <QLabel>
#include <QMouseEvent>
#include <QRegularExpression>
#include <QScrollBar>
#include <QSet>
#include <QStandardItemModel>
#include <QTextBlock>

#include <algorithm>

namespace {

constexpr int NameRole = Qt::UserRole;
constexpr int EntryRole = Qt::UserRole + 1;

const QRegularExpression::PatternOption Unicode = QRegularExpression::UseUnicodePropertiesOption;

/// Whether the '|' at index of line is escaped: it follows an odd run of '|' (||).
bool escapedPipe(const QString &line, int index)
{
    int run = 0;
    while (index - run - 1 >= 0 && line.at(index - run - 1) == QLatin1Char('|')) ++run;
    return run % 2 == 1;
}

/// A tooltip as HTML: the title in bold, then the lines (escaped, line breaks kept).
QString html(const QString &title, const QString &body)
{
    QString text = QStringLiteral("<b>%1</b>").arg(title.toHtmlEscaped());
    if (!body.isEmpty()) text += QStringLiteral("<br>") + body.toHtmlEscaped().replace(QLatin1Char('\n'), QStringLiteral("<br>"));
    return QStringLiteral("<p style='white-space:pre-wrap'>%1</p>").arg(text);
}

} // namespace

EditorAssist::EditorAssist(Providers providers, QObject *parent) : QObject(parent), m_providers(std::move(providers))
{
    m_model = new QStandardItemModel(this);
    m_completer = new QCompleter(m_model, this);
    m_completer->setObjectName(QStringLiteral("primulaCompleter"));
    m_completer->setCompletionRole(NameRole);
    m_completer->setCaseSensitivity(Qt::CaseInsensitive);
    m_completer->setCompletionMode(QCompleter::PopupCompletion);
    m_completer->setWrapAround(false);
    connect(m_completer, qOverload<const QModelIndex &>(&QCompleter::activated), this, &EditorAssist::activated);
    // QCompleter passes Enter on to the editor after completing (a new line); this filter,
    // installed after the completer's own, takes Enter and Tab first and completes itself.
    m_completer->popup()->installEventFilter(this);
}

void EditorAssist::attach(CodeEditor *editor)
{
    editor->installEventFilter(this);
    editor->viewport()->installEventFilter(this);
    // Mouse moves without a button close a hover hint once the mouse leaves its construct.
    editor->viewport()->setMouseTracking(true);
    QPointer<CodeEditor> guarded(editor);
    // Scrolling moves the text under the hint: it closes.
    connect(editor->verticalScrollBar(), &QScrollBar::valueChanged, this, &EditorAssist::hideHint);
    connect(editor->horizontalScrollBar(), &QScrollBar::valueChanged, this, &EditorAssist::hideHint);
    connect(editor->document(), &QTextDocument::contentsChange, this, [this, guarded](int position, int removed, int added) {
        if (guarded) typed(guarded, position, added, removed);
    });
}

// --- tokens and tooltips -------------------------------------------------------------

EditorAssist::Token EditorAssist::tokenAt(const CodeEditor *editor, int position) const
{
    const QTextBlock block = editor->document()->findBlock(position);
    const QString line = block.text();
    const int column = position - block.position();
    if (HeaderAssist::range(editor->document()).contains(block.blockNumber())) {
        // In the YAML header: the key of the line, or the key inside {…} at the position.
        const HeaderAssist::Place place = HeaderAssist::placeAt(editor->document(), block.blockNumber(), column);
        Token token{Token::HeaderKey, place.valid && place.flow && !place.key.isEmpty() ? place.path
                                                                                      : HeaderAssist::pathOfLine(editor->document(), block.blockNumber())};
        token.label = kindOf(editor);
        token.line = block.blockNumber();
        token.start = 0;
        token.end = int(line.size());
        return token.name.isEmpty() ? Token{} : token;
    }
    static const QRegularExpression reference(QStringLiteral(R"(^\|@\(\s*(["'])([^"']*))"));
    for (int i = 0; i < line.size(); ++i) {
        if (line.at(i) != QLatin1Char('|')) continue;
        if (i + 1 >= line.size()) break;
        const QChar c = line.at(i + 1);
        if (c == QLatin1Char('|')) {   // || — a literal bar
            ++i;
            continue;
        }
        Token token;
        int end = i + 2;
        if (c.isLetter() || c == QLatin1Char('_')) {
            while (end < line.size() && (line.at(end).isLetterOrNumber() || line.at(end) == QLatin1Char('_')
                                         || line.at(end) == QLatin1Char('.')))
                ++end;
            token = {Token::Command, line.mid(i + 1, end - i - 1)};
            while (token.name.endsWith(QLatin1Char('.'))) token.name.chop(1);
            // Closing markers: |end, |end>>, |end!, |end.Name, |end name, |endif, |endfor, |enddef.
            if (token.name == QStringLiteral("end") || token.name.startsWith(QStringLiteral("end."))
                || token.name == QStringLiteral("endif") || token.name == QStringLiteral("endfor")
                || token.name == QStringLiteral("enddef")) {
                token.kind = Token::Closing;
                if (token.name.startsWith(QStringLiteral("end."))) {
                    // |end.Name-with-hyphens: the scanner stopped at '-'.
                    while (end < line.size() && (line.at(end).isLetterOrNumber() || line.at(end) == QLatin1Char('_')
                                                 || line.at(end) == QLatin1Char('-')))
                        ++end;
                    token.name = line.mid(i + 1, end - i - 1);
                    token.label = QStringLiteral("|end.Ім'я");
                } else if (token.name != QStringLiteral("end")) {
                    token.label = QLatin1Char('|') + token.name;
                } else if (end < line.size() && (line.at(end) == QLatin1Char('>') || line.at(end) == QLatin1Char('!'))) {
                    const QChar mark = line.at(end);
                    while (end < line.size() && line.at(end) == mark) ++end;
                    token.name = line.mid(i + 1, end - i - 1);
                    token.label = mark == QLatin1Char('!') ? QStringLiteral("|end!") : QStringLiteral("|end>");
                } else if (end + 1 < line.size() && (line.at(end) == QLatin1Char(' ') || line.at(end) == QLatin1Char('\t'))
                           && line.at(end + 1).isLetter()) {
                    int k = end + 1;
                    while (k < line.size() && (line.at(k).isLetterOrNumber() || line.at(k) == QLatin1Char('_')
                                               || line.at(k) == QLatin1Char('.')))
                        ++k;
                    token.name = line.mid(i + 1, k - i - 1);
                    token.label = QStringLiteral("|end name");
                    end = k;
                } else {
                    token.label = QStringLiteral("|end");
                }
            }
        } else if (c == QLatin1Char('.')) {
            while (end < line.size() && (line.at(end).isLetterOrNumber() || line.at(end) == QLatin1Char('_')
                                         || line.at(end) == QLatin1Char('-')))
                ++end;
            token = end > i + 2 ? Token{Token::Style, line.mid(i + 2, end - i - 2)} : Token{Token::ShortForm, QStringLiteral(".")};
        } else if (c == QLatin1Char('@')) {
            const QRegularExpressionMatch match = reference.match(line.mid(i));
            if (match.hasMatch()) {
                end = i + int(match.capturedEnd()) + 1;
                token = {Token::Reference, match.captured(2)};
            } else {
                token = {Token::ShortForm, QStringLiteral("@")};
            }
        } else {
            while (end < line.size() && line.at(end) == c) ++end;   // |<<<, |>>, |--
            token = {Token::ShortForm, QString(c)};
        }
        token.line = block.blockNumber();
        token.start = i;
        token.end = end;
        if (column >= i && column <= end) return token;
        i = end - 1;
    }
    return codeToken(block, column);
}

EditorAssist::Token EditorAssist::codeToken(const QTextBlock &block, int column) const
{
    if (!PrimulaHighlighter::isCode(block, column)) return {};
    const QString line = block.text();
    auto word = [&line](int i) { return i >= 0 && i < line.size() && (line.at(i).isLetterOrNumber() || line.at(i) == QLatin1Char('_')); };
    int start = column, end = column;
    while (word(start - 1)) --start;
    while (word(end)) ++end;
    if (start == end || line.at(start).isDigit()) return {};
    // Inside a string literal: an odd number of quotes of one kind before the word.
    const QString before = line.left(start);
    if (before.count(QLatin1Char('"')) % 2 == 1 || before.count(QLatin1Char('\'')) % 2 == 1) return {};
    Token token{Token::Function, line.mid(start, end - start)};
    token.line = block.blockNumber();
    token.start = start;
    token.end = end;
    if (start > 0 && line.at(start - 1) == QLatin1Char('.')) {
        int owner = start - 1;
        while (word(owner - 1)) --owner;
        token.label = owner < start - 1 ? line.mid(owner, start - 1 - owner) : QStringLiteral(".");
    }
    // A bare name (not a call) that the file defines is a variable, not the function of the
    // same name: `count = len(rows)` — no hint of count() on `count` (remark to 14.13).
    int next = end;
    while (next < line.size() && line.at(next).isSpace()) ++next;
    const bool call = next < line.size() && line.at(next) == QLatin1Char('(');
    if (!call && token.label.isEmpty() && block.document() && definesName(block.document()->toPlainText(), token.name))
        return {};
    return token;
}

bool EditorAssist::definesName(const QString &text, const QString &name)
{
    // Code: name = …, a keyword of |let(name=…), for … name … in, def name(; the header:
    // a parameter "name:" (params:, indented). A comparison name == … is not a definition.
    const QString word = QRegularExpression::escape(name);
    const QRegularExpression code(QStringLiteral(R"((?<![\w.])%1\s*=(?!=)|\bdef\s+%1\b|\bfor\b[^\n:]*(?<![\w.])%1\b[^\n:]*\bin\b)")
                                      .arg(word),
                                  QRegularExpression::UseUnicodePropertiesOption);
    if (code.match(text).hasMatch()) return true;
    if (!text.startsWith(QStringLiteral("---"))) return false;
    const qsizetype close = text.indexOf(QStringLiteral("\n---"), 3);
    const QString header = close < 0 ? QString() : text.left(close);
    const QRegularExpression parameter(QStringLiteral(R"((?m)^\s+%1\s*:)").arg(word),
                                       QRegularExpression::UseUnicodePropertiesOption);
    return parameter.match(header).hasMatch();
}

int EditorAssist::entryFor(const Token &token) const
{
    const CommandCatalog *catalog = m_providers.catalog ? m_providers.catalog() : nullptr;
    if (!catalog) return -1;
    const QList<CommandCatalog::Entry> &entries = catalog->entries();
    if (token.kind == Token::Function) {
        if (token.label.isEmpty()) return catalog->functionIndex(token.name, false, false);
        if (token.label == QStringLiteral("math")) return catalog->functionIndex(token.name, false, true);
        return catalog->functionIndex(token.name, true, false);
    }
    QString shortForm;
    if (token.kind == Token::Command || token.kind == Token::Closing) {
        const QString label = token.kind == Token::Closing ? token.label : QLatin1Char('|') + token.name;
        for (int i = 0; i < entries.size(); ++i)
            if (entries.at(i).label == label && (token.kind == Token::Closing) == (entries.at(i).category == QStringLiteral("closing")))
                return i;
        return -1;
    }
    if (token.kind == Token::ShortForm) shortForm = token.name;
    else if (token.kind == Token::Style) shortForm = QStringLiteral(".");
    else if (token.kind == Token::Reference) shortForm = QStringLiteral("@");
    else return -1;
    for (int i = 0; i < entries.size(); ++i)
        if (entries.at(i).label.startsWith(QLatin1Char('|') + shortForm)
            && (entries.at(i).label.size() < 3 || !entries.at(i).label.at(1).isLetter()))
            return i;
    return -1;
}

QString EditorAssist::kindOf(const CodeEditor *editor) const
{
    return HeaderAssist::kind(editor->document(), m_providers.fileKind ? m_providers.fileKind(editor) : QStringLiteral("document"));
}

QString EditorAssist::headerTooltip(const CodeEditor *editor, const Token &token) const
{
    const CommandCatalog *catalog = m_providers.catalog ? m_providers.catalog() : nullptr;
    const CommandCatalog::HeaderKey *key = catalog ? catalog->headerKey(token.label, token.name) : nullptr;
    if (!key) return QString();
    QStringList lines{key->summary};
    lines << tr("Type: %1").arg(key->type);
    if (!key->values.isEmpty())
        lines << (key->closed ? tr("Values: %1") : tr("For example: %1")).arg(key->values.join(QStringLiteral(", ")));
    lines << tr("Example: %1").arg(key->example);
    if (key->recommended) lines << tr("Recommended for a finished ODT.");
    const QString metadata = HeaderAssist::metadataKey(token.label);
    if (!metadata.isEmpty() && key->path == metadata) {
        // The recommended metadata not filled in this header (doc: / doc_defaults:, decision 129).
        const QStringList missing = missingMetadata(editor);
        if (!missing.isEmpty())
            lines << tr("Not filled: %1 (context menu or Insert → Header: add missing fields)").arg(missing.join(QStringLiteral(", ")));
        if (metadata == QStringLiteral("doc_defaults"))
            lines << tr("A document overrides these values key by key in its own doc:.");
    }
    lines << CommandCatalog::sectionLabel(key->section);
    return html(key->path, lines.join(QLatin1Char('\n')));
}

QString EditorAssist::tooltipAt(const CodeEditor *editor, int position) const
{
    const Token token = tokenAt(editor, position);
    if (token.kind == Token::HeaderKey) return headerTooltip(editor, token);
    if (token.kind == Token::Style) {
        const auto styles = m_providers.styles ? m_providers.styles() : QList<QPair<QString, QString>>();
        for (const auto &[name, description] : styles)
            if (name == token.name) return html(QStringLiteral("|.") + name, description);
        return styles.isEmpty() ? QString() : html(QStringLiteral("|.") + token.name, tr("The document has no style %1.").arg(token.name));
    }
    if (token.kind == Token::Reference) {
        const auto ids = m_providers.ids ? m_providers.ids() : QList<QPair<QString, QString>>();
        for (const auto &[id, text] : ids)
            if (id == token.name) return html(QStringLiteral("|@(\"%1\")").arg(id), QStringLiteral("→ ") + text);
        return ids.isEmpty() ? QString() : html(QStringLiteral("|@(\"%1\")").arg(token.name), tr("The document has no element with ID %1.").arg(token.name));
    }
    const int index = entryFor(token);
    if (index < 0) return QString();
    const CommandCatalog::Entry &entry = m_providers.catalog()->entries().at(index);
    if (token.kind == Token::Closing) {
        // Which opening line this marker closes, by the same scanner as StyleEditing.
        QString body = entry.tooltip;
        for (const StyleEditing::EnvironmentInfo &environment : StyleEditing::environmentList(editor->document()))
            if (environment.close == token.line)
                body += QLatin1Char('\n') + tr("Closes line %1: %2").arg(environment.open + 1)
                                                .arg(editor->document()->findBlockByNumber(environment.open).text().trimmed());
        return html(QLatin1Char('|') + token.name, body);
    }
    if (token.kind == Token::Function) return html(entry.signature, entry.tooltip);
    return html(entry.label, entry.tooltip);
}

QStringList EditorAssist::missingMetadata(const CodeEditor *editor) const
{
    const CommandCatalog *catalog = m_providers.catalog ? m_providers.catalog() : nullptr;
    const QString kind = kindOf(editor);
    const QString metadata = HeaderAssist::metadataKey(kind);
    if (!catalog || metadata.isEmpty()) return {};
    const QTextDocument *document = editor->document();
    QStringList present;
    const HeaderAssist::Range header = HeaderAssist::range(document);
    for (int block = header.first; header.first >= 0 && block <= header.last; ++block) {
        const QString path = HeaderAssist::pathOfLine(document, block);
        if (path.startsWith(metadata + QLatin1Char('.'))) present << path;
        // doc: {title: …} — keys of the flow mapping.
        if (path == metadata) {
            static const QRegularExpression flowKey(QStringLiteral(R"([{,]\s*([^\s:,{}]+)\s*:)"));
            auto it = flowKey.globalMatch(document->findBlockByNumber(block).text());
            while (it.hasNext()) present << metadata + QLatin1Char('.') + it.next().captured(1);
        }
    }
    QStringList missing;
    for (const CommandCatalog::HeaderKey &other : catalog->headerKeys())
        if (other.recommended && other.kinds.contains(kind) && other.path.startsWith(metadata + QLatin1Char('.'))
            && !present.contains(other.path))
            missing << other.path.mid(metadata.size() + 1);
    return missing;
}

QString EditorAssist::headerSection(const CodeEditor *editor, int position) const
{
    // A header line without a key under the cursor (a blank one): the section of the
    // mapping it lies in, else the section of the header of the file kind.
    const QTextBlock block = editor->document()->findBlock(position);
    if (!HeaderAssist::range(editor->document()).contains(block.blockNumber())) return {};
    const QString kind = kindOf(editor);
    const QString parent = HeaderAssist::enclosing(editor->document(), block.blockNumber());
    const CommandCatalog *catalog = m_providers.catalog ? m_providers.catalog() : nullptr;
    if (const CommandCatalog::HeaderKey *key = catalog && !parent.isEmpty() ? catalog->headerKey(kind, parent) : nullptr)
        return key->section;
    if (kind == QStringLiteral("project")) return QStringLiteral("10.6");
    if (kind == QStringLiteral("styles")) return QStringLiteral("11.1");
    return QStringLiteral("2.3");
}

QString EditorAssist::sectionAt(const CodeEditor *editor, int position) const
{
    const Token token = tokenAt(editor, position);
    if (token.kind == Token::HeaderKey) {
        const CommandCatalog *catalog = m_providers.catalog ? m_providers.catalog() : nullptr;
        const CommandCatalog::HeaderKey *key = catalog ? catalog->headerKey(token.label, token.name) : nullptr;
        return key ? key->section : QString();
    }
    if (token.kind == Token::None) {
        const QString section = headerSection(editor, position);
        if (!section.isEmpty()) return section;
    }
    const int index = entryFor(token);
    return index < 0 ? QString() : m_providers.catalog()->entries().at(index).section;
}

EditorAssist::HelpContext EditorAssist::contextAt(const CodeEditor *editor, int position) const
{
    HelpContext context;
    context.section = sectionAt(editor, position);
    if (context.section.isEmpty()) return context;
    const QTextBlock block = editor->document()->findBlock(position);
    const QString line = block.text();
    Token token = tokenAt(editor, position);
    int start = token.start, end = token.end;
    if (start < 0) {
        // The section of the header block around an empty line: the line itself.
        start = 0;
        end = int(line.size());
    } else if ((token.kind == Token::Command || token.kind == Token::Function || token.kind == Token::Style)
               && end < line.size() && line.at(end) == QLatin1Char('(')) {
        // A command or a call with its arguments: up to the matching ')' on this line
        // (strings are skipped, so a bracket inside quotes does not count).
        int depth = 0;
        QChar quote;
        for (int i = end; i < line.size(); ++i) {
            const QChar c = line.at(i);
            if (!quote.isNull()) {
                if (c == quote) quote = QChar();
                continue;
            }
            if (c == QLatin1Char('"') || c == QLatin1Char('\'')) quote = c;
            else if (c == QLatin1Char('(')) ++depth;
            else if (c == QLatin1Char(')') && --depth == 0) {
                end = i + 1;
                break;
            }
        }
    }
    context.start = block.position() + start;
    context.end = block.position() + qMax(start, end);
    context.text = line.mid(start, end - start).trimmed();
    if (context.text.size() > 60) context.text = context.text.left(59) + QChar(0x2026);
    return context;
}

bool EditorAssist::showHint(CodeEditor *editor, int position)
{
    return showHintText(editor, position, tooltipAt(editor, position), true);
}

bool EditorAssist::showHintText(CodeEditor *editor, int position, const QString &text, bool sticky)
{
    hideHint();
    if (text.isEmpty()) return false;
    // A child of the viewport, not a top-level popup: it is not closed together with the
    // context menu and needs no popup permission of the window system.
    QWidget *viewport = editor->viewport();
    auto *panel = new QLabel(viewport);
    panel->setObjectName(QStringLiteral("primulaHint"));
    panel->setTextFormat(Qt::RichText);
    panel->setWordWrap(true);
    panel->setAutoFillBackground(true);
    panel->setForegroundRole(QPalette::ToolTipText);
    panel->setBackgroundRole(QPalette::ToolTipBase);
    panel->setFrameShape(QFrame::Box);
    panel->setMargin(6);
    panel->setText(text);
    panel->setMaximumWidth(qMax(200, qMin(640, viewport->width() - 8)));
    panel->adjustSize();
    QTextCursor cursor(editor->document());
    cursor.setPosition(position);
    const QRect at = editor->cursorRect(cursor);
    QPoint place(at.left(), at.bottom() + 4);
    if (place.y() + panel->height() > viewport->height()) place.setY(qMax(0, at.top() - 4 - panel->height()));
    place.setX(qBound(0, place.x(), qMax(0, viewport->width() - panel->width())));
    panel->move(place);
    panel->show();
    panel->raise();
    m_hint = panel;
    m_hintSticky = sticky;
    return true;
}

QLabel *EditorAssist::hintPanel() const
{
    return m_hint && m_hint->isVisible() ? m_hint.data() : nullptr;
}

void EditorAssist::hideHint()
{
    if (m_hint) m_hint->deleteLater();
    m_hint = nullptr;
}

// --- typing: signatures and completion ----------------------------------------------------

void EditorAssist::typed(CodeEditor *editor, int position, int added, int removed)
{
    if (m_inserting) return;
    const bool ours = m_completer->widget() == editor && m_completer->popup()->isVisible();
    if (!editor->hasFocus() && !ours) return;
    const bool typing = added == 1 && removed == 0;
    const bool erasing = added == 0 && removed == 1;
    if (!(typing || (erasing && ours)) || editor->textCursor().position() != position + added) {
        if (ours) m_completer->popup()->hide();
        return;
    }
    const QTextCursor cursor = editor->textCursor();
    const QString before = cursor.block().text().left(cursor.positionInBlock());
    if (typing && before.endsWith(QLatin1Char('('))) showSignature(editor, before);
    if (!complete(editor, false) && ours) m_completer->popup()->hide();
}

void EditorAssist::showSignature(CodeEditor *editor, const QString &before)
{
    static const QRegularExpression command(QStringLiteral(R"(\|([^\W\d][\w.]*)\($)"), Unicode);
    static const QRegularExpression shortForm(QStringLiteral(R"(\|([^\w\s|])\1*\($)"), Unicode);
    Token token;
    QRegularExpressionMatch match = command.match(before);
    if (match.hasMatch() && !escapedPipe(before, int(match.capturedStart()))) token = {Token::Command, match.captured(1)};
    else if ((match = shortForm.match(before)).hasMatch() && !escapedPipe(before, int(match.capturedStart())))
        token = {Token::ShortForm, match.captured(1)};
    if (token.kind == Token::None && before.size() >= 2) {
        // name( in code: the function before the parenthesis.
        const QTextBlock block = editor->textCursor().block();
        token = codeToken(block, int(before.size()) - 1);
    }
    const int index = entryFor(token);
    if (index < 0) return;
    const CommandCatalog::Entry &entry = m_providers.catalog()->entries().at(index);
    showHintText(editor, editor->textCursor().position(),
                 html(entry.function ? entry.signature : entry.label, entry.tooltip), true);
}

bool EditorAssist::complete(CodeEditor *editor, bool explicitRequest)
{
    static const QRegularExpression reference(QStringLiteral(R"(\|@\(\s*["']([^"']*)$)"));
    static const QRegularExpression style(QStringLiteral(R"(\|\.([\w-]*)$)"), Unicode);
    static const QRegularExpression command(QStringLiteral(R"(\|([^\W\d][\w.]*)$)"), Unicode);
    bool handled = false;
    const bool shown = completeHeader(editor, explicitRequest, &handled);
    if (handled) return shown;
    const QTextCursor cursor = editor->textCursor();
    const QString before = cursor.block().text().left(cursor.positionInBlock());

    Context context = Context::None;
    QString prefix;
    QRegularExpressionMatch match;
    if ((match = reference.match(before)).hasMatch()) {
        context = Context::Reference;
    } else if ((match = style.match(before)).hasMatch()) {
        context = Context::Style;
    } else if ((match = command.match(before)).hasMatch()) {
        context = Context::Command;
    } else if (explicitRequest && before.endsWith(QLatin1Char('|')) && !escapedPipe(before, int(before.size()) - 1)) {
        context = Context::Command;
    }
    if (match.hasMatch()) {
        if (escapedPipe(before, int(match.capturedStart()))) context = Context::None;
        prefix = match.captured(context == Context::Reference ? 1 : 1);
    }
    // Functions in code (14.13): name, owner.name, math.name.
    QString owner;
    if (context == Context::None && PrimulaHighlighter::isCode(cursor.block(), int(before.size()))) {
        static const QRegularExpression call(QStringLiteral(R"((?:([^\W\d]\w*)?\.)?([^\W\d]\w*)?$)"), Unicode);
        const QRegularExpressionMatch found = call.match(before);
        const bool dotted = found.capturedLength(0) > found.capturedLength(2) && found.captured(0).contains(QLatin1Char('.'));
        const bool inString = before.count(QLatin1Char('"')) % 2 == 1 || before.count(QLatin1Char('\'')) % 2 == 1;
        prefix = found.captured(2);
        owner = dotted ? (found.captured(1).isEmpty() ? QStringLiteral(".") : found.captured(1)) : QString();
        // Typing: from three letters (two opened the list on almost every word), or right after
        // owner. ; Ctrl+Space: at once.
        const bool wanted = explicitRequest || prefix.size() >= 3 || (dotted && !found.captured(1).isEmpty());
        if (!inString && wanted && (dotted || !prefix.isEmpty())) {
            context = Context::Function;
            match = found;
        }
    }
    if (context == Context::None) return false;

    m_model->clear();
    if (context == Context::Command) {
        const CommandCatalog *catalog = m_providers.catalog ? m_providers.catalog() : nullptr;
        if (!catalog) return false;
        const QList<CommandCatalog::Entry> &entries = catalog->entries();
        // The closing line of the innermost environment around the cursor comes first, when
        // the line holds nothing but |prefix (a closing marker takes the whole line).
        if (before.trimmed() == QLatin1Char('|') + prefix) {
            const int line = cursor.blockNumber();
            const StyleEditing::EnvironmentInfo *innermost = nullptr;
            const QList<StyleEditing::EnvironmentInfo> all = StyleEditing::environmentList(editor->document());
            for (const StyleEditing::EnvironmentInfo &environment : all)
                if (environment.open < line && (environment.close < 0 || environment.close >= line)
                    && (!innermost || environment.open > innermost->open))
                    innermost = &environment;
            if (innermost) {
                const QString closing = innermost->closing.mid(1);
                auto *item = new QStandardItem(closing + QStringLiteral(" — ")
                                               + tr("closes line %1: %2").arg(innermost->open + 1)
                                                     .arg(editor->document()->findBlockByNumber(innermost->open).text().trimmed()));
                item->setData(closing, NameRole);
                item->setData(-1, EntryRole);
                m_model->appendRow(item);
            }
        }
        for (int i = 0; i < entries.size(); ++i) {
            const CommandCatalog::Entry &entry = entries.at(i);
            if (entry.label.size() < 2 || !entry.label.at(1).isLetter()) continue;   // short forms
            if (entry.category == QStringLiteral("closing")) continue;
            auto *item = new QStandardItem(entry.label.mid(1) + QStringLiteral(" — ") + entry.summary);
            item->setData(entry.label.mid(1), NameRole);
            item->setData(i, EntryRole);
            item->setToolTip(entry.tooltip);
            m_model->appendRow(item);
        }
        m_completer->setFilterMode(Qt::MatchStartsWith);
    } else if (context == Context::Function) {
        const CommandCatalog *catalog = m_providers.catalog ? m_providers.catalog() : nullptr;
        if (!catalog) return false;
        const QList<CommandCatalog::Entry> &entries = catalog->entries();
        QSet<QString> listed;   // a method of several receivers (count, pop) once
        for (int i = 0; i < entries.size(); ++i) {
            const CommandCatalog::Entry &entry = entries.at(i);
            if (!entry.function) continue;
            const bool wanted = owner.isEmpty() ? entry.module.isEmpty() && entry.receiver.isEmpty()
                                : owner == QStringLiteral("math") ? !entry.module.isEmpty()
                                                                  : !entry.receiver.isEmpty();
            if (!wanted || listed.contains(entry.name)) continue;
            listed.insert(entry.name);
            auto *item = new QStandardItem(entry.name + QStringLiteral(" — ")
                                           + (entry.receiver.isEmpty() ? QString() : entry.receiver + QStringLiteral(": "))
                                           + entry.summary);
            item->setData(entry.name, NameRole);
            item->setData(i, EntryRole);
            item->setToolTip(entry.tooltip);
            m_model->appendRow(item);
        }
        m_completer->setFilterMode(Qt::MatchStartsWith);
    } else {
        auto values = context == Context::Style ? (m_providers.styles ? m_providers.styles() : QList<QPair<QString, QString>>())
                                                : (m_providers.ids ? m_providers.ids() : QList<QPair<QString, QString>>());
        // Names that start with the prefix first, then those that only contain it.
        std::stable_sort(values.begin(), values.end(), [&prefix](const auto &a, const auto &b) {
            return a.first.startsWith(prefix, Qt::CaseInsensitive) && !b.first.startsWith(prefix, Qt::CaseInsensitive);
        });
        for (const auto &[name, description] : values) {
            auto *item = new QStandardItem(description.isEmpty() ? name : name + QStringLiteral(" — ") + description);
            item->setData(name, NameRole);
            m_model->appendRow(item);
        }
        m_completer->setFilterMode(Qt::MatchContains);
    }
    m_context = context;
    m_prefix = prefix;
    m_completer->setWidget(editor);
    m_completer->setCompletionPrefix(prefix);
    const int count = m_completer->completionCount();
    // Nothing to offer, or the word is already complete.
    if (count == 0 || (count == 1 && !explicitRequest
                       && m_completer->currentIndex().data(NameRole).toString().compare(prefix, Qt::CaseInsensitive) == 0)) {
        m_completer->popup()->hide();
        return false;
    }
    m_completer->popup()->setCurrentIndex(m_completer->completionModel()->index(0, 0));
    QRect rect = editor->cursorRect();
    rect.setWidth(qMin(560, m_completer->popup()->sizeHintForColumn(0)
                                + m_completer->popup()->verticalScrollBar()->sizeHint().width()));
    m_completer->complete(rect);
    return true;
}

bool EditorAssist::completeHeader(CodeEditor *editor, bool explicitRequest, bool *handled)
{
    const QTextCursor cursor = editor->textCursor();
    const QTextDocument *document = editor->document();
    if (!HeaderAssist::range(document).contains(cursor.blockNumber())) return false;
    *handled = true;
    const CommandCatalog *catalog = m_providers.catalog ? m_providers.catalog() : nullptr;
    if (!catalog || catalog->headerKeys().isEmpty()) return false;
    const HeaderAssist::Place place = HeaderAssist::placeAt(document, cursor.blockNumber(), cursor.positionInBlock());
    if (!place.valid || (!place.onKey && !place.inValue)) return false;
    const QString kind = kindOf(editor);
    const QString line = cursor.block().text();
    const QString before = line.left(cursor.positionInBlock());
    m_model->clear();
    auto add = [this](const QString &shown, const QString &name, const QString &insert, const QString &tip) {
        auto *item = new QStandardItem(shown);
        item->setData(name, NameRole);
        item->setData(insert, EntryRole);
        if (!tip.isEmpty()) item->setToolTip(tip);
        m_model->appendRow(item);
    };
    if (place.onKey) {
        // Typing a key: from the first letter; Ctrl+Space at once (also on an empty line).
        if (!explicitRequest && place.prefix.isEmpty()) return false;
        if (place.prefix.contains(QLatin1Char(' '))) return false;
        const QStringList present = HeaderAssist::siblings(document, place, cursor.blockNumber());
        const bool hasColon = line.indexOf(QLatin1Char(':'), cursor.positionInBlock()) >= 0 && !place.flow;
        const QString childIndent(place.indent + 2, QLatin1Char(' '));
        for (const CommandCatalog::HeaderKey &key : catalog->headerKeys()) {
            if (!key.kinds.contains(kind)) continue;
            const int dot = int(key.path.lastIndexOf(QLatin1Char('.')));
            const QString parent = dot < 0 ? QString() : key.path.left(dot);
            const QString leaf = key.path.mid(dot + 1);
            if (parent != place.parent || present.contains(leaf)) continue;
            QString insert = leaf;
            if (!hasColon) {
                if (place.flow) insert += QStringLiteral(": ");
                else if (key.type == QStringLiteral("mapping")) insert += QStringLiteral(":\n") + childIndent;
                else if (key.type == QStringLiteral("list") && key.path == QStringLiteral("targets"))
                    insert += QStringLiteral(":\n") + childIndent + QStringLiteral("- ");
                else insert += QStringLiteral(": ");
            }
            add(leaf + QStringLiteral(" — ") + key.summary + (key.recommended ? QStringLiteral(" ★") : QString()),
                leaf, insert, key.example);
        }
        m_completer->setFilterMode(Qt::MatchStartsWith);
    } else {
        // A value: from the first character, right after "key: ", or Ctrl+Space.
        const CommandCatalog::HeaderKey *key = catalog->headerKey(kind, place.path);
        if (!key) return false;
        const bool afterColon = before.endsWith(QStringLiteral(": ")) || before.endsWith(QLatin1Char('['))
                                || before.endsWith(QStringLiteral(", "));
        if (!explicitRequest && place.prefix.isEmpty() && !afterColon) return false;
        const QStringList values = headerValues(editor, *key);
        if (values.isEmpty()) return false;
        // Without the typed opening quote: a value of a quoted one closes it.
        const bool quoted = before.mid(before.size() - place.prefix.size() - 1, 1) == QStringLiteral("\"");
        for (const QString &value : values)
            add(value, value, value + (quoted ? QStringLiteral("\"") : QString()), QString());
        m_completer->setFilterMode(key->closed ? Qt::MatchStartsWith : Qt::MatchContains);
    }
    m_context = Context::Header;
    m_prefix = place.prefix;
    m_completer->setWidget(editor);
    m_completer->setCompletionPrefix(place.prefix);
    const int count = m_completer->completionCount();
    if (count == 0 || (count == 1 && !explicitRequest
                       && m_completer->currentIndex().data(NameRole).toString().compare(place.prefix, Qt::CaseInsensitive) == 0)) {
        m_completer->popup()->hide();
        return false;
    }
    m_completer->popup()->setCurrentIndex(m_completer->completionModel()->index(0, 0));
    QRect rect = editor->cursorRect();
    rect.setWidth(qMin(560, m_completer->popup()->sizeHintForColumn(0)
                                + m_completer->popup()->verticalScrollBar()->sizeHint().width()));
    m_completer->complete(rect);
    return true;
}

QStringList EditorAssist::headerValues(CodeEditor *editor, const CommandCatalog::HeaderKey &key) const
{
    // The values offered for a header key: its own list, true/false, today's date, the files
    // of the project of the kind the key takes.
    QStringList values = key.values;
    if (key.type == QStringLiteral("bool")) values << QStringLiteral("true") << QStringLiteral("false");
    if (key.type == QStringLiteral("date")) values.prepend(QDate::currentDate().toString(Qt::ISODate));
    QString suffix;
    if (key.path == QStringLiteral("styles")) suffix = QStringLiteral(".s.prml");
    else if (key.path == QStringLiteral("extends")) suffix = QStringLiteral(".p.prml");
    else if (key.path == QStringLiteral("targets[].source")) suffix = QStringLiteral(".prml");
    if (!suffix.isEmpty() && m_providers.files) {
        static const QRegularExpression special(QStringLiteral(R"(\.(s|p|f|m)\.prml$)"));
        for (const QString &file : m_providers.files(editor))
            if (file.endsWith(suffix) && (suffix != QStringLiteral(".prml") || !special.match(file).hasMatch()))
                values << file;
    }
    return values;
}

void EditorAssist::applyEdit(CodeEditor *editor, const HeaderAssist::Edit &edit)
{
    // One undo step; the cursor goes where the value is to be typed.
    QTextCursor cursor(editor->document());
    m_inserting = true;
    cursor.beginEditBlock();
    cursor.setPosition(edit.position);
    cursor.setPosition(edit.position + edit.removed, QTextCursor::KeepAnchor);
    cursor.insertText(edit.text);
    cursor.endEditBlock();
    m_inserting = false;
    cursor.setPosition(edit.position + edit.cursor);
    editor->setTextCursor(cursor);
    editor->setFocus();
}

void EditorAssist::addHeaderActions(QMenu *menu, QAction *before, CodeEditor *editor, int position)
{
    // The header part of the context menu (14.16): what can be written at this place, also
    // on an empty line — "if you do not know what to do, open the context menu".
    const QTextDocument *document = editor->document();
    const int blockNumber = document->findBlock(position).blockNumber();
    if (!HeaderAssist::range(document).contains(blockNumber)) return;
    const CommandCatalog *catalog = m_providers.catalog ? m_providers.catalog() : nullptr;
    if (!catalog || catalog->headerKeys().isEmpty()) return;
    const QString kind = kindOf(editor);
    QPointer<CodeEditor> guarded(editor);

    // Insert key ▸ — the keys of the mapping at this place, and of the top level.
    auto keyMenu = [&](const QString &title, const QString &parent) {
        auto *sub = new QMenu(title, menu);
        // Keys already present in that mapping are shown disabled.
        QStringList present;
        const HeaderAssist::Range header = HeaderAssist::range(document);
        for (int block = header.first; block <= header.last; ++block) {
            const QString path = HeaderAssist::pathOfLine(document, block);
            const int dot = int(path.lastIndexOf(QLatin1Char('.')));
            if ((dot < 0 ? QString() : path.left(dot)) == parent) present << path.mid(dot + 1);
        }
        for (const CommandCatalog::HeaderKey &key : catalog->headerKeys()) {
            if (!key.kinds.contains(kind)) continue;
            const int dot = int(key.path.lastIndexOf(QLatin1Char('.')));
            if ((dot < 0 ? QString() : key.path.left(dot)) != parent) continue;
            const QString leaf = key.path.mid(dot + 1);
            HeaderAssist::Edit edit;
            const bool mapping = key.type == QStringLiteral("mapping") || key.path == QStringLiteral("targets");
            const bool possible = HeaderAssist::insertKey(document, blockNumber, parent, leaf, mapping, &edit);
            QAction *action = sub->addAction(leaf + QStringLiteral(" — ") + key.summary
                                             + (key.recommended ? QStringLiteral(" ★") : QString()));
            action->setToolTip(key.example);
            action->setEnabled(possible && !present.contains(leaf));
            connect(action, &QAction::triggered, this, [this, guarded, edit, key] {
                if (!guarded) return;
                HeaderAssist::Edit inserted = edit;
                if (key.path == QStringLiteral("targets")) {   // a list: its first item
                    inserted.text.insert(inserted.cursor, QStringLiteral("- "));
                    inserted.cursor += 2;
                }
                applyEdit(guarded, inserted);
            });
        }
        sub->setEnabled(!sub->actions().isEmpty());
        sub->setToolTipsVisible(true);
        menu->insertMenu(before, sub);
    };
    const QString parent = HeaderAssist::enclosing(document, blockNumber);
    if (!parent.isEmpty()) keyMenu(tr("Insert key into %1:").arg(parent), parent);
    keyMenu(parent.isEmpty() ? tr("Insert key") : tr("Insert top-level key"), QString());

    // Value ▸ — the values of the key of this line.
    const QString linePath = HeaderAssist::pathOfLine(document, blockNumber);
    if (const CommandCatalog::HeaderKey *key = linePath.isEmpty() ? nullptr : catalog->headerKey(kind, linePath);
        key && key->type != QStringLiteral("mapping") && key->type != QStringLiteral("list")) {
        auto *sub = new QMenu(tr("Value of %1").arg(key->path), menu);
        for (const QString &value : headerValues(editor, *key)) {
            HeaderAssist::Edit edit;
            if (!HeaderAssist::valueEdit(document, blockNumber, value, &edit)) continue;
            connect(sub->addAction(value), &QAction::triggered, this, [this, guarded, edit] {
                if (guarded) applyEdit(guarded, edit);
            });
        }
        sub->setEnabled(!sub->actions().isEmpty());
        menu->insertMenu(before, sub);
    }

    // The missing recommended metadata and the list of all keys.
    if (!HeaderAssist::metadataKey(kind).isEmpty()) {
        const QStringList missing = missingMetadata(editor);
        QAction *add = new QAction(missing.isEmpty() ? tr("Add missing metadata fields (none missing)")
                                                     : tr("Add missing metadata fields: %1").arg(missing.join(QStringLiteral(", "))),
                                   menu);
        connect(add, &QAction::triggered, this, [this, guarded] { if (guarded) emit addHeaderFieldsRequested(guarded); });
        menu->insertAction(before, add);
    }
    const QString top = kind == QStringLiteral("project") ? QStringLiteral("10.6")
                        : kind == QStringLiteral("styles") ? QStringLiteral("11.1") : QStringLiteral("2.3");
    QAction *all = new QAction(tr("All header keys (%1)").arg(CommandCatalog::sectionLabel(top)), menu);
    connect(all, &QAction::triggered, this, [this, top] { emit sectionRequested(top); });
    menu->insertAction(before, all);
    menu->insertSeparator(before);
}

void EditorAssist::activated(const QModelIndex &index)
{
    auto *editor = qobject_cast<CodeEditor *>(m_completer->widget());
    if (!editor || !index.isValid()) return;
    const QString name = index.data(NameRole).toString();
    QTextCursor cursor = editor->textCursor();
    m_inserting = true;
    if (m_context == Context::Command) {
        // |prefix becomes the snippet of the command; one undo step for both.
        const CommandCatalog *catalog = m_providers.catalog();
        const int entry = index.data(EntryRole).toInt();
        cursor.beginEditBlock();
        cursor.movePosition(QTextCursor::Left, QTextCursor::KeepAnchor, int(m_prefix.size()) + 1);
        cursor.removeSelectedText();
        if (entry < 0) cursor.insertText(QLatin1Char('|') + name);   // a closing line
        else insertSnippet(editor, cursor, catalog->entries().at(entry).snippet, false);
        cursor.endEditBlock();
        editor->setTextCursor(cursor);
    } else if (m_context == Context::Header) {
        // The typed part becomes the key (with ": " or a nested line) or the value.
        cursor.movePosition(QTextCursor::Left, QTextCursor::KeepAnchor, int(m_prefix.size()));
        cursor.insertText(index.data(EntryRole).toString());
        editor->setTextCursor(cursor);
    } else if (m_context == Context::Function) {
        // The typed name becomes the call template; the owner (math., x.) stays.
        const CommandCatalog::Entry &entry = m_providers.catalog()->entries().at(index.data(EntryRole).toInt());
        QString snippet = entry.snippet;
        if (!entry.module.isEmpty() && snippet.startsWith(QStringLiteral("math."))) snippet = snippet.mid(5);
        cursor.beginEditBlock();
        cursor.movePosition(QTextCursor::Left, QTextCursor::KeepAnchor, int(m_prefix.size()));
        cursor.removeSelectedText();
        // Before an existing '(' only the name is inserted.
        const QTextBlock block = cursor.block();
        if (cursor.positionInBlock() < block.text().size() && block.text().at(cursor.positionInBlock()) == QLatin1Char('('))
            cursor.insertText(entry.name);
        else
            insertSnippet(editor, cursor, snippet, false);
        cursor.endEditBlock();
        editor->setTextCursor(cursor);
    } else {
        cursor.movePosition(QTextCursor::Left, QTextCursor::KeepAnchor, int(m_prefix.size()));
        cursor.insertText(name);
        editor->setTextCursor(cursor);
    }
    m_inserting = false;
}

// --- snippets and Tab ------------------------------------------------------------------------

void EditorAssist::insertSnippet(CodeEditor *editor, QTextCursor &cursor, const QString &snippet, bool block)
{
    const bool nested = m_inserting;
    m_inserting = true;
    const QList<QPair<int, int>> stops = Snippet::insert(cursor, snippet, block);
    m_inserting = nested;
    m_stops.clear();
    m_stopsEditor = editor;
    // A lone final stop at the cursor itself gives Tab nothing to do.
    if (stops.size() == 1 && stops.first().first == cursor.position() && !cursor.hasSelection()) return;
    for (const auto &[start, end] : stops) {
        QTextCursor stop(editor->document());
        stop.setPosition(start);
        stop.setPosition(end, QTextCursor::KeepAnchor);
        m_stops.append(stop);
    }
}

bool EditorAssist::nextStop(CodeEditor *editor)
{
    if (editor != m_stopsEditor || m_stops.isEmpty()) {
        m_stops.clear();
        return false;
    }
    editor->setTextCursor(m_stops.takeFirst());
    return true;
}

bool EditorAssist::eventFilter(QObject *watched, QEvent *event)
{
    if (watched == m_completer->popup() && event->type() == QEvent::KeyPress) {
        const int key = static_cast<QKeyEvent *>(event)->key();
        if (key == Qt::Key_Return || key == Qt::Key_Enter || key == Qt::Key_Tab) {
            QModelIndex index = m_completer->popup()->currentIndex();
            if (!index.isValid()) index = m_completer->completionModel()->index(0, 0);
            m_completer->popup()->hide();
            if (index.isValid()) activated(index);
            return true;
        }
        return false;
    }
    if (event->type() == QEvent::ToolTip) {
        auto *editor = qobject_cast<CodeEditor *>(watched->parent());
        if (editor && watched == editor->viewport()) {
            // Hover shows the same panel as the forced hint (no tooltip window, so never two
            // hints at once). A forced hint is kept; over the panel itself nothing changes.
            auto *help = static_cast<QHelpEvent *>(event);
            if (m_hint && (m_hintSticky || m_hint->geometry().contains(help->pos()))) return true;
            const int position = editor->cursorForPosition(help->pos()).position();
            const QString text = tooltipAt(editor, position);
            if (text.isEmpty()) hideHint();
            else if (!m_hint || m_hint->text() != text) showHintText(editor, position, text, false);
            return true;
        }
    }
    if (event->type() == QEvent::ContextMenu) {
        // The standard editor menu with the hint and the specification section of the
        // construct under the mouse at the top.
        auto *editor = qobject_cast<CodeEditor *>(watched->parent());
        if (editor && watched == editor->viewport()) {
            auto *menuEvent = static_cast<QContextMenuEvent *>(event);
            const int position = editor->cursorForPosition(menuEvent->pos()).position();
            QMenu *menu = editor->createStandardContextMenu(menuEvent->pos());
            QAction *first = menu->actions().value(0);
            const Token token = tokenAt(editor, position);
            const QString hint = tooltipAt(editor, position);
            const QString section = sectionAt(editor, position);
            QString title;
            if (token.kind == Token::Command || token.kind == Token::Closing) title = QStringLiteral("|") + token.name;
            else if (token.kind == Token::Style) title = QStringLiteral("|.") + token.name;
            else if (token.kind == Token::Reference) title = QStringLiteral("|@(\"%1\")").arg(token.name);
            else if (token.kind == Token::ShortForm) title = QStringLiteral("|") + token.name;
            else if (token.kind == Token::HeaderKey) title = token.name;
            else if (token.kind == Token::Function)
                title = (token.label.isEmpty() || token.label == QStringLiteral(".") ? QString() : token.label)
                        + (token.label.isEmpty() ? QString() : QStringLiteral(".")) + token.name;
            QAction *hintAction = new QAction(title.isEmpty() ? tr("Hint (no construct here)") : tr("Hint: %1").arg(title), menu);
            hintAction->setEnabled(!hint.isEmpty());
            QPointer<CodeEditor> guarded(editor);
            // Shown after the menu has closed and focus is back in the editor.
            connect(hintAction, &QAction::triggered, this, [this, guarded, position] {
                QMetaObject::invokeMethod(this, [this, guarded, position] { if (guarded) showHint(guarded, position); },
                                          Qt::QueuedConnection);
            });
            QAction *sectionAction = new QAction(section.isEmpty() ? tr("Specification section") : CommandCatalog::sectionLabel(section), menu);
            sectionAction->setEnabled(!section.isEmpty());
            connect(sectionAction, &QAction::triggered, this, [this, guarded, position] {
                if (guarded) emit contextHelpRequested(guarded, position);
            });
            // The keys of these actions are shown in the menu (they work in the editor itself).
            hintAction->setShortcut(QKeySequence(Qt::CTRL | Qt::SHIFT | Qt::Key_Space));
            sectionAction->setShortcut(QKeySequence(Qt::Key_F1));
            QAction *completeAction = new QAction(tr("Complete here"), menu);
            completeAction->setShortcut(QKeySequence(Qt::CTRL | Qt::Key_Space));
            const bool moveCursor = !editor->textCursor().hasSelection();
            connect(completeAction, &QAction::triggered, this, [this, guarded, position, moveCursor] {
                QMetaObject::invokeMethod(this, [this, guarded, position, moveCursor] {
                    if (!guarded) return;
                    if (moveCursor) {
                        QTextCursor cursor = guarded->textCursor();
                        cursor.setPosition(position);
                        guarded->setTextCursor(cursor);
                    }
                    guarded->setFocus();
                    complete(guarded, true);
                }, Qt::QueuedConnection);
            });
            menu->insertAction(first, hintAction);
            menu->insertAction(first, sectionAction);
            menu->insertAction(first, completeAction);
            menu->insertSeparator(first);
            addHeaderActions(menu, first, editor, position);
            if (m_providers.contextMenu) m_providers.contextMenu(menu, editor, position);
            menu->setAttribute(Qt::WA_DeleteOnClose);
            menu->popup(menuEvent->globalPos());
            return true;
        }
    }
    if (event->type() == QEvent::MouseMove && m_hint && !m_hintSticky) {
        // A hover hint closes when the mouse leaves its construct (but not over the panel).
        auto *editor = qobject_cast<CodeEditor *>(watched->parent());
        if (editor && watched == editor->viewport()) {
            const QPoint pos = static_cast<QMouseEvent *>(event)->position().toPoint();
            if (!m_hint->geometry().contains(pos)
                && tooltipAt(editor, editor->cursorForPosition(pos).position()) != m_hint->text())
                hideHint();
        }
    }
    if (event->type() == QEvent::Leave && m_hint && !m_hintSticky && watched != m_hint.data()) {
        auto *editor = qobject_cast<CodeEditor *>(watched->parent());
        if (editor && watched == editor->viewport()
            && !m_hint->rect().contains(m_hint->mapFromGlobal(QCursor::pos())))
            hideHint();
    }
    if (event->type() == QEvent::MouseButtonPress) {
        m_stops.clear();   // a click ends the snippet
        hideHint();
    }
    if (event->type() == QEvent::Wheel || event->type() == QEvent::Resize) hideHint();
    if (event->type() == QEvent::KeyPress) {
        auto *editor = qobject_cast<CodeEditor *>(watched);
        if (!editor) return false;
        auto *key = static_cast<QKeyEvent *>(event);
        if (m_hint) {   // any key closes the forced hint; Esc only closes it
            hideHint();
            if (key->key() == Qt::Key_Escape) return true;
        }
        if (m_completer->popup()->isVisible()) {
            switch (key->key()) {
            case Qt::Key_Enter:
            case Qt::Key_Return:
            case Qt::Key_Escape:
            case Qt::Key_Tab:
            case Qt::Key_Backtab:
                event->ignore();
                return true;   // the completer handles them
            default:
                break;
            }
        }
        if (key->key() == Qt::Key_Space && key->modifiers() == Qt::ControlModifier) {
            complete(editor, true);
            return true;
        }
        if (key->key() == Qt::Key_Space && key->modifiers() == (Qt::ControlModifier | Qt::ShiftModifier)) {
            showHint(editor, editor->textCursor().position());
            return true;
        }
        if (key->key() == Qt::Key_Tab && key->modifiers() == Qt::NoModifier && nextStop(editor)) return true;
        if (key->key() == Qt::Key_Escape) m_stops.clear();
    }
    return false;
}
