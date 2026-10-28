#pragma once

// Insertion of construct snippets from `primula commands --format json` (stage 14.8).
// The snippet syntax is the subset of the VS Code / LSP snippet syntax the catalogue
// uses: $0 (final position), $1, ${1:default}, ${1|a,b|} (a choice, the first is
// inserted); \$ and \} are literal. See
// https://code.visualstudio.com/docs/editor/userdefinedsnippets#_snippet-syntax

#include <QList>
#include <QMap>
#include <QPair>
#include <QString>

class QTextCursor;

namespace Snippet {

/// A snippet expanded to plain text.
struct Expansion
{
    QString text;
    /// Placeholder number → [start, end) of its first occurrence in text; 0 is the final position.
    QMap<int, QPair<int, int>> placeholders;
};

/// Expand snippet; the text of the selection (if any) takes the place of $0 when the
/// snippet has it, otherwise of $1 (its default is dropped).
/// @param filled  set to the placeholder number the selection went to (0, 1) or -1.
Expansion expand(const QString &snippet, const QString &selection = QString(), int *filled = nullptr);

/// Insert snippet at cursor as one undo step and leave the first unfilled placeholder
/// selected (the cursor at $0 or after the text when there is none).
/// @return the stops for Tab after the selected placeholder: the [start, end) document
///         ranges of the other unfilled placeholders in number order, then $0 (or the end).
/// @param block  the construct takes whole lines (an environment or a line form): a
///               selection is widened to whole lines and wrapped; without a selection the
///               snippet goes onto its own line (line breaks are added around it as needed).
QList<QPair<int, int>> insert(QTextCursor &cursor, const QString &snippet, bool block);

} // namespace Snippet
