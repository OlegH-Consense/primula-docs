#pragma once

// Applying and removing styles in Primula source text (stage 14.7, specification 4.3).
// Studio does not parse Primula: the edits work on the text of the buffer with a small
// scanner (balanced braces and parentheses, quoted strings, environment openers and
// closing lines). The translator checks the result on the next inspection.
//
//   character style  selection → |.X{…}; no selection → |.X{} with the cursor inside
//   paragraph style  one line → |.X: text; several lines → |.X: … |end.X;
//                    clause and heading lines (|>, |<) get style="X" in their arguments
//   block style      lines → |block("X"): … |end block
//
// Every edit is one undo step.

#include <QList>
#include <QString>

class QTextCursor;
class QTextDocument;

namespace StyleEditing {

enum class Kind { Character, Paragraph, Block, Other };

/// An environment of the document found by the line scanner (opening line with ':' at
/// its end, closing line), for completion and hints of closing markers.
struct EnvironmentInfo
{
    QString kind;      ///< ">", "!", "style", "if", "for", "def" or a command name (block, table…)
    QString name;      ///< the style of |.X: and |block("X"), the markers of a clause (>>)
    int open = -1;     ///< block number of the opening line
    int close = -1;    ///< block number of the closing line, -1 when not closed
    QString closing;   ///< the canonical closing line: |end.X, |end>>, |end block, |endif…
};

/// All environments of document in the order of their opening lines.
QList<EnvironmentInfo> environmentList(const QTextDocument *document);

/// The kind of a style from the `kind` field of `--dump-styles`.
Kind kindFromDump(const QString &kind);

/// Apply style name of kind at the cursor or the selection of cursor.
/// @param cursor  the editor cursor; on success it is moved to a natural place
///                (inside an empty |.X{}, or after the edited text).
/// @param error   on failure: a message for the user (translated).
/// @return false when the selection does not fit the kind; the text is unchanged then.
bool apply(QTextCursor &cursor, const QString &name, Kind kind, QString *error);

/// Remove the innermost style application around the cursor: |.X{…} (unwrapped),
/// |.X: at the start of the line, style= of a clause or heading line, or an
/// environment |.X: … |end.X or |block("X"): … |end block (the two lines are deleted).
/// @param name  only an application of this style; empty — any style.
/// @return false with error when there is nothing to remove.
bool remove(QTextCursor &cursor, const QString &name, QString *error);

} // namespace StyleEditing
