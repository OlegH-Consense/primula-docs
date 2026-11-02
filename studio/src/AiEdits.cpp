#include "AiEdits.h"

#include "AiHistory.h"

#include <QRegularExpression>
#include <algorithm>

namespace {

const QRegularExpression &startMarker()
{
    static const QRegularExpression pattern(QStringLiteral("^\\s*<{5,9}\\s*ORIGINAL\\s*$"),
                                            QRegularExpression::CaseInsensitiveOption);
    return pattern;
}

const QRegularExpression &middleMarker()
{
    static const QRegularExpression pattern(QStringLiteral("^\\s*={5,9}\\s*$"));
    return pattern;
}

const QRegularExpression &endMarker()
{
    static const QRegularExpression pattern(QStringLiteral("^\\s*>{5,9}\\s*REPLACEMENT\\s*$"),
                                            QRegularExpression::CaseInsensitiveOption);
    return pattern;
}

bool isFence(const QString &line)
{
    return line.trimmed().startsWith(QStringLiteral("```"));
}

QString trimNewlines(QString text)
{
    while (text.startsWith(QLatin1Char('\n'))) text.remove(0, 1);
    while (text.endsWith(QLatin1Char('\n'))) text.chop(1);
    return text;
}

/// One step of the parser: the blocks, and for the preview the text between them.
struct Piece
{
    QString text;       ///< the text outside blocks (when edit is false)
    bool edit = false;
    AiEdit block;
};

QList<Piece> split(const QString &response)
{
    QList<Piece> pieces;
    QStringList outside;
    QStringList original, replacement;
    enum { Outside, InOriginal, InReplacement } state = Outside;
    bool fenced = false;   // the block is wrapped in a code fence
    const QStringList lines = response.split(QLatin1Char('\n'));
    auto flush = [&] {
        if (!outside.isEmpty()) pieces.append({outside.join(QLatin1Char('\n')), false, {}});
        outside.clear();
    };
    for (int i = 0; i < lines.size(); ++i) {
        QString line = lines.at(i);
        if (line.endsWith(QLatin1Char('\r'))) line.chop(1);
        switch (state) {
        case Outside:
            if (startMarker().match(line).hasMatch()) {
                // A fence line right before the marker belongs to the block.
                fenced = !outside.isEmpty() && isFence(outside.last());
                if (fenced) outside.removeLast();
                flush();
                original.clear();
                replacement.clear();
                state = InOriginal;
            } else {
                outside << line;
            }
            break;
        case InOriginal:
            if (middleMarker().match(line).hasMatch()) state = InReplacement;
            else original << line;
            break;
        case InReplacement:
            if (endMarker().match(line).hasMatch()) {
                AiEdit edit{trimNewlines(original.join(QLatin1Char('\n'))), trimNewlines(replacement.join(QLatin1Char('\n')))};
                if (!edit.original.isEmpty()) pieces.append({{}, true, edit});
                state = Outside;
                // A fence line right after the block closes the one before it.
                if (fenced && i + 1 < lines.size() && isFence(lines.at(i + 1))) ++i;
            } else {
                replacement << line;
            }
            break;
        }
    }
    if (state != Outside) {
        // An unclosed block is not an edit: keep its text as it was written.
        outside << QStringLiteral("<<<<<<< ORIGINAL") << original;
        if (state == InReplacement) outside << QStringLiteral("=======") << replacement;
    }
    flush();
    return pieces;
}

/// A text without the differences that AI does not keep when it copies: the whitespace at the
/// end of a line, CR, and non-breaking spaces. map[i] is the index in the source of the i-th
/// character of the result.
QString normalized(const QString &source, QList<int> *map)
{
    QString result;
    int i = 0;
    while (i < source.size()) {
        QChar c = source.at(i);
        if (c == QLatin1Char('\r')) { ++i; continue; }
        if (c == QChar(0x00A0) || c == QChar(0x202F)) c = QLatin1Char(' ');
        if (c == QLatin1Char(' ') || c == QLatin1Char('\t')) {
            int j = i;
            while (j < source.size() && (source.at(j) == QLatin1Char(' ') || source.at(j) == QLatin1Char('\t')
                                         || source.at(j) == QChar(0x00A0) || source.at(j) == QChar(0x202F)))
                ++j;
            if (j == source.size() || source.at(j) == QLatin1Char('\n') || source.at(j) == QLatin1Char('\r')) {
                i = j;   // spaces at the end of a line
                continue;
            }
        }
        result.append(c);
        if (map) map->append(i);
        ++i;
    }
    return result;
}

} // namespace

QString AiEdits::instructions()
{
    return QStringLiteral(
        "EDIT FORMAT. The user will apply your edits to the document automatically, so give each edit as a block:\n"
        "<<<<<<< ORIGINAL\n"
        "the lines copied exactly from the document\n"
        "=======\n"
        "the replacement\n"
        ">>>>>>> REPLACEMENT\n"
        "Rules: copy ORIGINAL character by character from \"DOCUMENT OR SELECTED TEXT\", including Primula "
        "commands, and make it the shortest fragment that occurs once in the document (add neighbouring words "
        "if needed); one change per block; do not repeat unchanged text outside the changed words; keep Primula "
        "constructs, style names, identifiers and parameter names as they are unless the task asks to change "
        "them; do not change the meaning of legal or technical text when the task is proofreading or style. "
        "Write a short explanation of the changes outside the blocks. Do not put the blocks in a code fence.");
}

QList<AiEdit> AiEdits::parse(const QString &response)
{
    QList<AiEdit> edits;
    for (const Piece &piece : split(response))
        if (piece.edit) edits.append(piece.block);
    return edits;
}

QString AiEdits::previewMarkdown(const QString &response)
{
    QString result;
    int number = 0;
    for (const Piece &piece : split(response)) {
        if (!piece.edit) {
            result += piece.text + QLatin1Char('\n');
            continue;
        }
        ++number;
        result += QStringLiteral("\n**%1 %2**\n\n").arg(QObject::tr("Edit")).arg(number);
        result += QStringLiteral("%1\n\n%2\n\n").arg(QObject::tr("Was:"), AiHistory::fenced(piece.block.original));
        result += QStringLiteral("%1\n\n%2\n\n").arg(QObject::tr("Now:"), AiHistory::fenced(piece.block.replacement));
    }
    return result;
}

AiEdits::Place AiEdits::locate(const QString &text, const AiEdit &edit)
{
    Place place;
    if (edit.original.isEmpty()) return place;
    if (edit.original == edit.replacement) {
        place.status = AiEditStatus::Unchanged;
        return place;
    }
    const int first = text.indexOf(edit.original);
    if (first >= 0) {
        if (text.indexOf(edit.original, first + 1) >= 0) {
            place.status = AiEditStatus::Ambiguous;
            return place;
        }
        place = {AiEditStatus::Ready, first, int(edit.original.size())};
        return place;
    }
    QList<int> map;
    const QString haystack = normalized(text, &map);
    const QString needle = normalized(edit.original, nullptr);
    if (needle.isEmpty()) return place;
    const int at = haystack.indexOf(needle);
    if (at < 0) return place;
    if (haystack.indexOf(needle, at + 1) >= 0) {
        place.status = AiEditStatus::Ambiguous;
        return place;
    }
    const int start = map.at(at);
    const int end = map.at(at + needle.size() - 1) + 1;
    place = {AiEditStatus::Ready, start, end - start};
    return place;
}

QString AiEdits::apply(const QString &text, const QList<AiEdit> &edits, QList<AiEditStatus> *statuses,
                       QList<Place> *places)
{
    QList<Place> found;
    for (const AiEdit &edit : edits) found.append(locate(text, edit));
    // Edits are applied in the order of their places; one that overlaps an earlier one is skipped.
    QList<int> order;
    for (int i = 0; i < found.size(); ++i)
        if (found.at(i).status == AiEditStatus::Ready) order.append(i);
    std::sort(order.begin(), order.end(), [&](int a, int b) { return found.at(a).start < found.at(b).start; });
    QList<int> applied;
    int end = 0;
    for (int index : order) {
        if (found.at(index).start < end) {
            found[index].status = AiEditStatus::Overlaps;
            continue;
        }
        end = found.at(index).start + found.at(index).length;
        applied.append(index);
    }
    QString result = text;
    for (int k = applied.size() - 1; k >= 0; --k) {
        const Place &place = found.at(applied.at(k));
        result.replace(place.start, place.length, edits.at(applied.at(k)).replacement);
    }
    if (statuses) {
        statuses->clear();
        for (const Place &place : found) statuses->append(place.status);
    }
    if (places) *places = found;
    return result;
}

QString AiEdits::diffText(const AiEdit &edit)
{
    QString result;
    for (const QString &line : edit.original.split(QLatin1Char('\n'))) result += QStringLiteral("- ") + line + QLatin1Char('\n');
    for (const QString &line : edit.replacement.split(QLatin1Char('\n'))) result += QStringLiteral("+ ") + line + QLatin1Char('\n');
    return result;
}
