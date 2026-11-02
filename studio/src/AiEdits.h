#pragma once

// Edits proposed by AI (stage 22.3, decisions D6 and D7): the answer carries blocks
//
//     <<<<<<< ORIGINAL
//     lines copied from the document
//     =======
//     the replacement
//     >>>>>>> REPLACEMENT
//
// Studio finds each ORIGINAL in the document, shows the list, checks the result with the
// translator (`primula check --overlay`) and applies the chosen edits to the editor as one undo step.
// The text of the answer outside the blocks is the explanation.

#include <QList>
#include <QString>
#include <QStringList>

struct AiEdit
{
    QString original;
    QString replacement;
};

enum class AiEditStatus
{
    Ready,       ///< ORIGINAL is found exactly once
    NotFound,    ///< no such text in the document (the document changed, or AI did not copy it)
    Ambiguous,   ///< ORIGINAL occurs more than once
    Unchanged,   ///< the replacement equals the original
    Overlaps     ///< overlaps an edit that is applied before it
};

namespace AiEdits {

/// The instructions that make AI answer with the blocks (added to the prompt on request).
QString instructions();

/// The blocks of an answer, in the order of the answer. Blocks that are not closed, or have an
/// empty ORIGINAL, are ignored; lines of Markdown fences around a block are ignored too.
QList<AiEdit> parse(const QString &response);

/// The answer for the Markdown preview: each block becomes "Edit N" with the two texts as code blocks.
QString previewMarkdown(const QString &response);

/// Where an edit applies in a text.
struct Place
{
    AiEditStatus status = AiEditStatus::NotFound;
    int start = -1;
    int length = 0;
};

/// Find the ORIGINAL of an edit in the text: exactly, else ignoring the whitespace at the ends of
/// lines and the difference between non-breaking and ordinary spaces; the place must be unique.
Place locate(const QString &text, const AiEdit &edit);

/// The text with the edits applied. An edit that is not Ready, or overlaps one applied before, is
/// skipped.
/// @param statuses  receives the status of each edit (Ready for an applied one); may be null.
/// @param places  receives the place of each applied edit in the original text; may be null.
QString apply(const QString &text, const QList<AiEdit> &edits, QList<AiEditStatus> *statuses = nullptr,
              QList<Place> *places = nullptr);

/// "- old" / "+ new" lines for a list.
QString diffText(const AiEdit &edit);

} // namespace AiEdits
