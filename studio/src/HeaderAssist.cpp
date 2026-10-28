#include "HeaderAssist.h"

#include <QRegularExpression>
#include <QTextBlock>
#include <QTextDocument>

namespace {

/// One header line: indentation, a list item "- ", the key and its colon.
struct Line
{
    int raw = 0;           ///< leading spaces
    bool item = false;     ///< starts with "-" (a block list item)
    int content = 0;       ///< column where the content (after "- ") starts
    QString key;           ///< the key of "key:", empty when none
    int colon = -1;        ///< column of the colon of the key
    bool blank = true;     ///< empty or a comment
};

Line parse(const QString &text)
{
    Line line;
    while (line.raw < text.size() && text.at(line.raw) == QLatin1Char(' ')) ++line.raw;
    line.content = line.raw;
    const QString rest = text.mid(line.raw);
    line.blank = rest.isEmpty() || rest.startsWith(QLatin1Char('#'));
    if (line.blank) return line;
    if (rest == QStringLiteral("-") || rest.startsWith(QStringLiteral("- "))) {
        line.item = true;
        line.content = line.raw + 1;
        while (line.content < text.size() && text.at(line.content) == QLatin1Char(' ')) ++line.content;
    }
    // A plain key: no quotes, flow brackets or comment marks; ':' then a space or the end.
    static const QRegularExpression key(QStringLiteral(R"(^([^\s:#{}\[\],"'][^:#{}\[\],]*?)\s*:(?=\s|$))"));
    const QRegularExpressionMatch match = key.match(text.mid(line.content));
    if (match.hasMatch()) {
        line.key = match.captured(1);
        line.colon = line.content + int(match.capturedEnd()) - 1;
    }
    return line;
}

QString lineText(const QTextDocument *document, int block) { return document->findBlockByNumber(block).text(); }

QString join(const QString &parent, const QString &key) { return parent.isEmpty() ? key : parent + QLatin1Char('.') + key; }

int headerFirst(const QTextDocument *document)
{
    const HeaderAssist::Range range = HeaderAssist::range(document);
    return range.first >= 0 ? range.first : 1;
}

QString parentOf(const QTextDocument *document, int block, const Line &line);

/// The path of the list an item line belongs to ("targets[]").
QString itemContainer(const QTextDocument *document, int block, const Line &line)
{
    // The key line above: less indented, or as indented and not an item (targets:\n- …).
    for (int above = block - 1; above >= headerFirst(document); --above) {
        const Line candidate = parse(lineText(document, above));
        if (candidate.blank) continue;
        if (candidate.raw < line.raw || (candidate.raw == line.raw && !candidate.item)) {
            if (candidate.key.isEmpty()) return {};
            const QString base = candidate.item ? join(itemContainer(document, above, candidate), candidate.key)
                                                : join(parentOf(document, above, candidate), candidate.key);
            return base + QStringLiteral("[]");
        }
    }
    return {};
}

/// The path of the mapping holding the key of line (a real one or the one being typed).
QString parentOf(const QTextDocument *document, int block, const Line &line)
{
    if (line.item) return itemContainer(document, block, line);
    if (line.raw == 0) return {};
    for (int above = block - 1; above >= headerFirst(document); --above) {
        const Line candidate = parse(lineText(document, above));
        if (candidate.blank || candidate.raw >= line.raw) continue;
        // A key under the first key of an item ("- source: a" / "  output: b") is its sibling.
        if (candidate.item && candidate.content == line.raw) return itemContainer(document, above, candidate);
        if (candidate.key.isEmpty()) return {};
        return candidate.item ? join(itemContainer(document, above, candidate), candidate.key)
                              : join(parentOf(document, above, candidate), candidate.key);
    }
    return {};
}

/// Unquoted text of a value as typed.
QString unquote(QString text)
{
    text = text.trimmed();
    if (!text.isEmpty() && (text.at(0) == QLatin1Char('"') || text.at(0) == QLatin1Char('\''))) text.remove(0, 1);
    return text;
}

} // namespace

HeaderAssist::Range HeaderAssist::range(const QTextDocument *document)
{
    Range result;
    if (!document || document->blockCount() < 2 || document->firstBlock().text().trimmed() != QStringLiteral("---"))
        return result;
    for (QTextBlock block = document->firstBlock().next(); block.isValid(); block = block.next()) {
        if (block.text().trimmed() == QStringLiteral("---")) {
            result.first = 1;
            result.last = block.blockNumber() - 1;
            result.close = block.blockNumber();
            return result;
        }
    }
    return result;
}

QString HeaderAssist::pathOfLine(const QTextDocument *document, int blockNumber)
{
    const Line line = parse(lineText(document, blockNumber));
    return line.key.isEmpty() ? QString() : join(parentOf(document, blockNumber, line), line.key);
}

HeaderAssist::Place HeaderAssist::placeAt(const QTextDocument *document, int blockNumber, int column)
{
    Place place;
    if (!range(document).contains(blockNumber)) return place;
    const QString text = lineText(document, blockNumber);
    const QString before = text.left(column);
    const Line line = parse(text);
    if (line.raw < before.size() && before.mid(line.raw).startsWith(QLatin1Char('#'))) return place;   // a comment
    place.valid = true;
    place.indent = line.content;

    // Flow mappings and lists of the line: the innermost unclosed bracket before the column.
    QList<int> openers;
    QChar quote;
    for (int i = 0; i < before.size(); ++i) {
        const QChar c = before.at(i);
        if (!quote.isNull()) {
            if (c == quote) quote = QChar();
        } else if (c == QLatin1Char('"') || c == QLatin1Char('\'')) {
            quote = c;
        } else if (c == QLatin1Char('{') || c == QLatin1Char('[')) {
            openers << i;
        } else if ((c == QLatin1Char('}') || c == QLatin1Char(']')) && !openers.isEmpty()) {
            openers.removeLast();
        }
    }
    // "key: {…}" or "key: […]", or a list item "- {…}" (targets: - {source: a, output: b}).
    const bool keyed = openers.size() == 1 && line.colon >= 0 && line.colon < openers.first();
    const bool itemFlow = openers.size() == 1 && line.item && openers.first() == line.content
                          && before.at(openers.first()) == QLatin1Char('{');
    if (keyed || itemFlow) {
        const int opener = openers.first();
        const QString owner = keyed ? join(parentOf(document, blockNumber, line), line.key)
                                    : itemContainer(document, blockNumber, line);
        const int separator = qMax(int(before.lastIndexOf(QLatin1Char(','))), opener);
        const QString segment = before.mid(separator + 1);
        place.flow = true;
        if (before.at(opener) == QLatin1Char('[')) {   // a flow list: values of the owner key
            place.inValue = true;
            place.key = line.key;
            place.parent = parentOf(document, blockNumber, line);
            place.path = owner;
            place.prefix = unquote(segment);
            return place;
        }
        const int colon = int(segment.indexOf(QLatin1Char(':')));
        place.parent = owner;
        if (colon >= 0) {
            place.inValue = true;
            place.key = segment.left(colon).trimmed();
            place.prefix = unquote(segment.mid(colon + 1));
        } else {
            // The whole key (up to its ':'), the typed part as the prefix.
            place.onKey = true;
            place.prefix = segment.trimmed();
            const QString after = text.mid(column);
            const int stop = int(after.indexOf(QRegularExpression(QStringLiteral("[:,}\\]]"))));
            place.key = (segment + (stop < 0 ? after : after.left(stop))).trimmed();
        }
        place.path = join(place.parent, place.key);
        return place;
    }
    if (!openers.isEmpty()) {   // nested flow collections: not assisted
        place.valid = false;
        return place;
    }
    place.parent = parentOf(document, blockNumber, line);
    if (line.colon >= 0 && column > line.colon) {
        place.inValue = true;
        place.key = line.key;
        place.prefix = unquote(before.mid(line.colon + 1));
    } else if (column >= line.content) {
        place.onKey = true;
        place.key = line.colon >= 0 ? line.key : text.mid(line.content).trimmed();
        place.prefix = before.mid(line.content).trimmed();
    } else {
        place.valid = false;
        return place;
    }
    place.path = join(place.parent, place.key);
    return place;
}

QStringList HeaderAssist::siblings(const QTextDocument *document, const Place &place, int blockNumber)
{
    QStringList keys;
    const Range header = range(document);
    if (!header.contains(blockNumber)) return keys;
    if (place.flow) {
        static const QRegularExpression flowKey(QStringLiteral(R"([{,]\s*([^\s:,{}\[\]]+)\s*:)"));
        auto it = flowKey.globalMatch(lineText(document, blockNumber));
        while (it.hasNext()) keys << it.next().captured(1);
        return keys;
    }
    // Lines of the same mapping: in a list item only the lines of that item.
    int from = header.first;
    int to = header.last;
    if (place.parent.endsWith(QStringLiteral("[]"))) {
        int start = blockNumber;
        Line first = parse(lineText(document, start));
        while (start > header.first && !first.item) first = parse(lineText(document, --start));
        from = start;
        for (int below = start + 1; below <= header.last; ++below) {
            const Line next = parse(lineText(document, below));
            if (!next.blank && next.raw <= first.raw) {
                to = below - 1;
                break;
            }
        }
    }
    for (int block = from; block <= to; ++block) {
        if (block == blockNumber) continue;
        const Line line = parse(lineText(document, block));
        if (!line.key.isEmpty() && parentOf(document, block, line) == place.parent) keys << line.key;
    }
    return keys;
}

QString HeaderAssist::kind(const QTextDocument *document, const QString &fallback)
{
    const Range header = range(document);
    static const QRegularExpression kindLine(QStringLiteral(R"(^kind:\s*["']?(\w+))"));
    for (int block = header.first; header.first >= 0 && block <= header.last; ++block) {
        const QRegularExpressionMatch match = kindLine.match(lineText(document, block));
        if (match.hasMatch()) return match.captured(1);
    }
    return fallback;
}

QString HeaderAssist::metadataKey(const QString &fileKind)
{
    // Decision 129: doc: in a document, doc_defaults: (their defaults) in a project.
    if (fileKind == QStringLiteral("document")) return QStringLiteral("doc");
    if (fileKind == QStringLiteral("project")) return QStringLiteral("doc_defaults");
    return {};
}

bool HeaderAssist::addFields(const QTextDocument *document, const QString &fileKind, const QList<Field> &fields,
                             int *position, QString *snippet, QString *error, QStringList *added)
{
    auto lines = [](const QList<Field> &list, const QString &indent) {
        // name: ${n:value} or name: "${n:value}"; $ } \ of the value are escaped for Snippet.
        QString text;
        int number = 0;
        for (const Field &field : list) {
            QString value = field.value;
            value.replace(QLatin1Char('\\'), QStringLiteral("\\\\")).replace(QLatin1Char('$'), QStringLiteral("\\$"))
                 .replace(QLatin1Char('}'), QStringLiteral("\\}"));
            const QString stop = QStringLiteral("${%1:%2}").arg(++number).arg(value);
            text += indent + field.name + QStringLiteral(": ")
                    + (field.quoted ? QLatin1Char('"') + stop + QLatin1Char('"') : stop) + QLatin1Char('\n');
        }
        return text;
    };
    auto names = [](const QList<Field> &list) {
        QStringList result;
        for (const Field &field : list) result << field.name;
        return result;
    };
    const QString section = metadataKey(fileKind);
    if (section.isEmpty() || fields.isEmpty()) return false;
    const Range header = range(document);
    if (header.first < 0) {
        // A new header at the start of the file.
        *position = 0;
        *snippet = QStringLiteral("---\n") + (fileKind == QStringLiteral("project") ? QStringLiteral("kind: project\n") : QString())
                   + section + QStringLiteral(":\n") + lines(fields, QStringLiteral("  ")) + QStringLiteral("---\n");
        if (added) *added = names(fields);
        return true;
    }
    int sectionLine = -1;
    for (int block = header.first; block <= header.last; ++block) {
        const Line line = parse(lineText(document, block));
        if (line.raw == 0 && !line.item && line.key == section) sectionLine = block;
    }
    if (sectionLine < 0) {
        *position = document->findBlockByNumber(header.close).position();
        *snippet = section + QStringLiteral(":\n") + lines(fields, QStringLiteral("  "));
        if (added) *added = names(fields);
        return true;
    }
    const QString own = lineText(document, sectionLine);
    const QString value = own.mid(own.indexOf(QLatin1Char(':')) + 1).trimmed();
    if (!value.isEmpty() && !value.startsWith(QLatin1Char('#'))) {
        if (error) *error = QStringLiteral("flow");
        return false;
    }
    // The children of the section: their keys and indentation; new keys go after the last one.
    QStringList present;
    int indent = 2;
    int last = sectionLine;
    for (int block = sectionLine + 1; block <= header.last; ++block) {
        const Line line = parse(lineText(document, block));
        if (line.blank) continue;
        if (line.raw == 0) break;
        if (present.isEmpty()) indent = line.raw;
        if (line.raw == indent && !line.key.isEmpty()) present << line.key;
        last = block;
    }
    QList<Field> missing;
    for (const Field &field : fields)
        if (!present.contains(field.name)) missing << field;
    if (missing.isEmpty()) return false;
    const QTextBlock after = document->findBlockByNumber(last + 1);
    *position = after.position();
    *snippet = lines(missing, QString(indent, QLatin1Char(' ')));
    if (added) *added = names(missing);
    return true;
}

QString HeaderAssist::enclosing(const QTextDocument *document, int blockNumber)
{
    const Range header = range(document);
    if (!header.contains(blockNumber)) return {};
    // A key line: an opener (no value) takes the new key as its child, another key as its sibling.
    const Line own = parse(lineText(document, blockNumber));
    int from = blockNumber;
    if (own.blank) {
        // A blank line belongs to the block of the line above it.
        from = -1;
        for (int above = blockNumber - 1; above >= header.first; --above)
            if (!parse(lineText(document, above)).blank) {
                from = above;
                break;
            }
        if (from < 0) return {};
    }
    const Line line = parse(lineText(document, from));
    if (line.item || line.key.isEmpty()) return {};   // list items: keys go to the top level
    const QString text = lineText(document, from);
    const QString value = text.mid(line.colon + 1).trimmed();
    const QString path = join(parentOf(document, from, line), line.key);
    if ((value.isEmpty() || value.startsWith(QLatin1Char('#'))) && !path.contains(QStringLiteral("[]"))) return path;
    const QString parent = parentOf(document, from, line);
    return parent.contains(QStringLiteral("[]")) ? QString() : parent;
}

bool HeaderAssist::insertKey(const QTextDocument *document, int blockNumber, const QString &parent, const QString &key,
                             bool mapping, Edit *edit)
{
    const Range header = range(document);
    if (header.first < 0) return false;
    const bool blank = header.contains(blockNumber) && parse(lineText(document, blockNumber)).blank
                       && !lineText(document, blockNumber).trimmed().startsWith(QLatin1Char('#'));
    auto keyText = [&](int indent) {
        const QString pad(indent, QLatin1Char(' '));
        return pad + key + (mapping ? QStringLiteral(":\n") + pad + QStringLiteral("  ") : QStringLiteral(": "));
    };
    // The next non-blank line below a position: its indentation decides whether a key of
    // that indentation can go there without taking the lines below as its children.
    auto nextIndent = [&](int below) {
        for (int block = below; block <= header.last; ++block) {
            const Line line = parse(lineText(document, block));
            if (!line.blank) return line.raw;
        }
        return 0;
    };
    if (parent.isEmpty()) {
        if (blank && nextIndent(blockNumber + 1) == 0) {
            const QTextBlock block = document->findBlockByNumber(blockNumber);
            *edit = {block.position(), int(block.text().size()), keyText(0)};
        } else {
            *edit = {document->findBlockByNumber(header.close).position(), 0, keyText(0) + QLatin1Char('\n')};
        }
        edit->cursor = int(edit->text.size()) - (edit->text.endsWith(QLatin1Char('\n')) ? 1 : 0);
        return true;
    }
    // The line of the parent mapping; a {…} or a scalar value cannot take a block key.
    int opener = -1;
    for (int block = header.first; block <= header.last; ++block)
        if (pathOfLine(document, block) == parent) {
            opener = block;
            break;
        }
    if (opener < 0) return false;
    const Line line = parse(lineText(document, opener));
    const QString value = lineText(document, opener).mid(line.colon + 1).trimmed();
    if (!value.isEmpty() && !value.startsWith(QLatin1Char('#'))) return false;
    int indent = line.raw + 2;
    for (int block = opener + 1; block <= header.last; ++block) {
        const Line child = parse(lineText(document, block));
        if (child.blank) continue;
        if (child.raw > line.raw) indent = child.raw;
        break;
    }
    if (blank && enclosing(document, blockNumber) == parent && nextIndent(blockNumber + 1) <= indent) {
        const QTextBlock block = document->findBlockByNumber(blockNumber);
        *edit = {block.position(), int(block.text().size()), keyText(indent)};
    } else {
        const QTextBlock after = document->findBlockByNumber(opener + 1);
        *edit = {after.position(), 0, keyText(indent) + QLatin1Char('\n')};
    }
    edit->cursor = int(edit->text.size()) - (edit->text.endsWith(QLatin1Char('\n')) ? 1 : 0);
    return true;
}

bool HeaderAssist::valueEdit(const QTextDocument *document, int blockNumber, const QString &value, Edit *edit)
{
    if (!range(document).contains(blockNumber)) return false;
    const QString text = lineText(document, blockNumber);
    const Line line = parse(text);
    if (line.colon < 0) return false;
    // The old value up to a comment (" #") or the end of the line.
    int start = line.colon + 1;
    while (start < text.size() && text.at(start) == QLatin1Char(' ')) ++start;
    int end = int(text.indexOf(QStringLiteral(" #"), start));
    if (end < 0) end = int(text.size());
    while (end > start && text.at(end - 1) == QLatin1Char(' ')) --end;
    // A value YAML would read otherwise is quoted.
    static const QRegularExpression special(QStringLiteral(R"([:#{}\[\],&*!|>'"%@`]|^\s|\s$|^-)"));
    QString written = value;
    if (special.match(value).hasMatch()) written = QLatin1Char('"') + QString(value).replace(QLatin1Char('"'), QStringLiteral("\\\"")) + QLatin1Char('"');
    const int position = document->findBlockByNumber(blockNumber).position();
    *edit = {position + line.colon + 1, end - line.colon - 1, QLatin1Char(' ') + written};
    edit->cursor = int(edit->text.size());
    return true;
}
