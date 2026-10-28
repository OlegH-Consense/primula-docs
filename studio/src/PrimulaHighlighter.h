#pragma once

// Syntax highlighting of Primula files (stage 14.5, remark З6).
//
// The model follows the specification v1.1 (sections 2, 3, 12, appendices 1-2)
// and the highlighting definitions for Kate/mcedit/Geany of the specification
// thread (primula-syntax-highlighting.md):
//
// * the YAML header `---` … `---` at the start of a file: keys (predefined keys
//   stronger), strings, comments;
// * `|% comment`, `|comment:` … `|end` (environments inside are balanced);
// * escapes `||` `|{` `|}` `|;` `|~` `|\`;
// * structural forms at the start of a line: headings `|<` (the line bold),
//   clauses `|>`, list items `|-` `|#`, admonitions `|!`, table rows `|:`,
//   cells `|&`; closing markers `|end…`;
// * commands `|name`, `|module.name` (control, built-in and user commands told
//   apart), styles `|.Name`, references `|@(…)`, expressions `|(…)`, formulas
//   `|=(…)`, arguments `(…)` as Python (strings, numbers, keywords; over lines);
// * inline forms `|*{…}` `|/{…}` `|_{…}` `|^{…}` `|,{…}` `|—{…}` ``|`{…}``
//   `|"{…}` `|?{…}` with nesting, also over lines;
// * `|code:` … `|end` and the code part of `*.s.prml`/`*.p.prml` as Python;
//   `|verbatim:` … `|end` and `|verbatim(end="EOF"):` … `EOF` literally;
// * invalid forms (`|` before a space, a digit or the end of the line,
//   reserved `|$ |[ |]`, other unlisted symbols) — red wavy underline.
//
// The state of a line (open bodies, depth of parentheses, block kind) is kept
// in QTextBlockUserData; the block state is its hash, so a change re-highlights
// the following lines.

#include <QStringList>
#include <QSyntaxHighlighter>
#include <QList>
#include <QPair>
#include <QTextBlock>
#include <QTextCharFormat>

class PrimulaHighlighter final : public QSyntaxHighlighter
{
    Q_OBJECT

public:
    /// @param codeFile  the text after the YAML header is code (`*.s.prml`, `*.p.prml`).
    PrimulaHighlighter(QTextDocument *document, bool codeFile);

    /// Formats by role; public for tests.
    enum class Role {
        Comment, Escape, HeaderDelimiter, HeaderKey, KnownHeaderKey, YamlValue, Heading, Clause, ListMarker,
        Admonition, Table, Control, Builtin, Command, Style, Reference, Expression, InlineMarker,
        PyString, PyNumber, PyKeyword, Verbatim, Invalid
    };
    QTextCharFormat format(Role role) const;
    /// Whether column of block is inside code: a code block, the code part of a code file,
    /// command arguments or an expression |(…) — where the functions of expressions are
    /// written (stage 14.13). False for a block not highlighted by a PrimulaHighlighter.
    static bool isCode(const QTextBlock &block, int column);
    /// The top-level header keys shown as known (bold); for the test against the catalogue.
    static QStringList knownHeaderKeys();

protected:
    void highlightBlock(const QString &text) override;

private:
    struct State;
    bool m_codeFile = false;
    bool m_dark = false;
    QList<QPair<int, int>> m_code;   ///< code ranges [from, to) of the line being highlighted

    void highlightMarkup(const QString &text, int from, State &state, const QTextCharFormat &base);
    int highlightArguments(const QString &text, int from, State &state);
    void highlightPython(const QString &text, int from, int to);
    void highlightYaml(const QString &text);
    void mark(int start, int length, Role role);
    void mergeFormat(int start, int length, const QTextCharFormat &format);
};
