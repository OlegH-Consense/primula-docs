#pragma once

// The YAML header of a Primula file as Studio's assist sees it (stage 14.14, decision 127):
// where the header is, which key path a position belongs to, and the edit that adds the
// missing recommended fields. Plain text logic without a YAML library: the header of a
// Primula file is short, written by hand, and uses block mappings, block lists ("- ")
// and one level of flow mappings or lists on a line ({time: 20}, [a, b]).
//
//   targets:                 path "targets"
//     - source: a.prml       path "targets[].source"
//       output: out/a.odt    path "targets[].output"
//   limits: {time: 20}       path "limits.time" inside the braces

#include <QString>
#include <QStringList>

class QTextDocument;

namespace HeaderAssist {

/// Block numbers of the header lines between the two "---" (first > last when the header
/// is empty); first = -1 when the file has no closed header.
struct Range
{
    int first = -1;
    int last = -1;
    int close = -1;   ///< block number of the closing "---"
    bool contains(int block) const { return first >= 0 && block >= first && block <= last; }
};
Range range(const QTextDocument *document);

/// What a position of a header line is.
struct Place
{
    bool valid = false;
    bool onKey = false;     ///< the key itself (or its beginning while typing)
    bool inValue = false;   ///< after "key:" (the value of path)
    QString parent;         ///< path of the mapping the key belongs to ("" at the top)
    QString key;            ///< the key at or before the position (may be partial while typing)
    QString path;           ///< parent + key ("targets[].source")
    QString prefix;         ///< the text typed before the position (the key or the value part)
    int indent = 0;         ///< indentation of the key (block mappings)
    bool flow = false;      ///< inside {…} or […] of the line
};

/// The place of column in block blockNumber of the header.
Place placeAt(const QTextDocument *document, int blockNumber, int column);

/// Keys already present in the mapping at parent (block mappings; also the flow mapping
/// of the line when the place is inside one).
QStringList siblings(const QTextDocument *document, const Place &place, int blockNumber);

/// The file kind: the top-level "kind:" of the header, else fallback (by the file name).
QString kind(const QTextDocument *document, const QString &fallback);

/// Path of the key on line blockNumber ("" when the line has no key).
QString pathOfLine(const QTextDocument *document, int blockNumber);

/// One key to add: its leaf name, the proposed value and whether it is written in quotes.
/// Each value becomes a placeholder of the snippet (Tab goes from one to the next).
struct Field
{
    QString name;
    QString value;
    bool quoted = false;
};

/// The metadata key of a file kind (decision 129): "doc" (a document), "doc_defaults" (a
/// project), "" otherwise.
QString metadataKey(const QString &fileKind);

/// The edit that adds the fields missing from the metadata mapping of the header ("doc:" of
/// a document, "doc_defaults:" of a project): position and the snippet to insert there
/// (Snippet syntax: placeholders for the values). Without a header a new one is made (with
/// "kind: project" for a project); without the metadata key it is added at the end of the
/// header.
/// @param added  the names of the fields added (for the report to the author)
/// @return false when there is nothing to add (all fields present, or the kind has no
///         metadata) or the key is a flow mapping ({…}, error set) — the author edits it by
///         hand then.
bool addFields(const QTextDocument *document, const QString &fileKind, const QList<Field> &fields,
               int *position, QString *snippet, QString *error = nullptr, QStringList *added = nullptr);

/// A text edit of the header: remove `removed` characters at `position`, insert `text`; the
/// cursor goes to position + cursor afterwards.
struct Edit
{
    int position = 0;
    int removed = 0;
    QString text;
    int cursor = 0;
};

/// The mapping a new key written at line blockNumber belongs to (the context menu "Insert
/// key"): on a key without a value ("doc:") its children, on another key its siblings, on
/// a blank line the block of the line above; "" — the top level (also inside list items).
QString enclosing(const QTextDocument *document, int blockNumber);

/// The edit that adds key under the mapping parent ("" — the top level): on the blank line
/// blockNumber when it lies in that mapping, else as the first child of the parent (at the
/// end of the header for the top level). mapping: the key takes a block of its own
/// ("key:\n  "), else "key: ". False when parent is written as {…} or has a value.
bool insertKey(const QTextDocument *document, int blockNumber, const QString &parent, const QString &key,
               bool mapping, Edit *edit);

/// The edit that sets the value of the key on line blockNumber (the old value replaced, a
/// comment kept; a value YAML would read otherwise is quoted).
bool valueEdit(const QTextDocument *document, int blockNumber, const QString &value, Edit *edit);

} // namespace HeaderAssist
