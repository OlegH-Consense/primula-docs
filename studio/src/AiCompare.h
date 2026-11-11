#pragma once

// Comparing the answers of several AI tools (stage 22.7): the edit blocks of the answers are matched by the
// place of the document they change (the same ORIGINAL after the whitespace is normalized) and every edit gets
// a verdict: the other tools agree with its replacement, differ from it, or did not touch the place at all.
// There is no "best" answer: the verdict only tells where a look is needed.

#include "AiEdits.h"

#include <QList>
#include <QString>

namespace AiCompare {

/// The edits of one answer and the tool that gave it.
struct Answer
{
    QString tool;
    QList<AiEdit> edits;
};

enum class Kind
{
    Single,   ///< nothing to compare with (one answer)
    Agree,    ///< every tool changed this place, and to the same text
    Differ,   ///< at least one tool changed this place to another text
    Partial   ///< some tools did not touch the place; those that did agree
};

/// The replacement of another tool for the same place.
struct Variant
{
    QString tool;
    QString replacement;
};

struct Verdict
{
    Kind kind = Kind::Single;
    int total = 0;       ///< the tools compared
    int present = 0;     ///< the tools that have an edit for the place (this one included)
    int agreeing = 0;    ///< the tools whose replacement equals this one (this one included)
    QList<Variant> others;   ///< the replacements of the other tools that have the place
};

/// The text for matching: runs of whitespace (non-breaking spaces too) become one space, the ends are cut.
QString normalize(const QString &text);

/// One verdict per edit, for each answer, in the order of its edits. The answers must be the ones that carry edits.
QList<QList<Verdict>> compare(const QList<Answer> &answers);

/// "agree 31 of 35, differ 4, in some only 0" for a list of verdicts of one answer; empty for Single.
QString summary(const QList<Verdict> &verdicts);

/// The words of `to` against `from` as HTML: removed words in <del>, added in <ins>, the rest as they are.
QString diffHtml(const QString &from, const QString &to);

} // namespace AiCompare
