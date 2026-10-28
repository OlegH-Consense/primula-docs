#pragma once

// Hints and completion in Primula editors (stage 14.8a, remark З8), without LSP:
// everything comes from the data Studio already has from the translator —
// the construct catalogue (`primula commands`, Т5), the styles (`--dump-styles`, Т2)
// and the structure (`--dump-structure`, Т1).
//
//   hover          the hint for |command, a short form, |.Style, |@("id") and |end…,
//                  in the hint panel (below); it closes when the mouse leaves the construct
//   typing |name(  the signature (arguments with types, defaults and descriptions), in the panel
//   completion     after | (commands, inserted as snippets), |. (styles), |@(" (IDs);
//                  automatically while typing, Ctrl+Space on demand
//   Tab            the next placeholder of the last inserted snippet; Esc ends it
//   F1             the specification section of the construct at the cursor (contextAt: the
//                  section and the text it was taken for, which MainWindow marks in the editor)
//   functions      (stage 14.13) in code — code blocks, code files, command arguments, |(…):
//                  the hint and F1 (library or specification section) for a function, a
//                  method or math.name; the signature on typing name(; completion of names
//                  (from two letters, after x. and math.; Ctrl+Space at once) — from the
//                  functions of the catalogue (`primula commands`, key functions)
//   header         (stage 14.14) in the YAML header: the hint and F1 for a key (summary, type,
//                  values, example; on "doc:" / "doc_defaults:" the recommended fields not filled yet; the context menu of the header (14.16): Insert key, Value, missing metadata),
//                  completion of the keys of the mapping at the cursor (for the file kind,
//                  without those already there) and of values (closed values, suggestions,
//                  today's date, files of the project for paths) — from header_keys
//   hint panel     the only hint window: a frame inside the editor viewport, not a popup
//                  window (a popup closes with the context menu or is refused on Wayland);
//                  a click, a key or scrolling closes it
//   context menu   "Hint" (the panel, kept until a click, a key or scrolling) and
//                  "Specification, section N" for the construct under the mouse;
//                  Ctrl+Shift+Space shows the hint for the construct at the text cursor

#include "CommandCatalog.h"
#include "HeaderAssist.h"

#include <QObject>
#include <QList>
#include <QPair>
#include <QPointer>
#include <QTextCursor>

#include <functional>

class CodeEditor;
class QTextBlock;
class CommandCatalog;
class QCompleter;
class QAction;
class QMenu;
class QStandardItemModel;

class EditorAssist : public QObject
{
    Q_OBJECT
    friend class StudioTests;

public:
    /// Where the assist gets its data; each function may return empty data.
    struct Providers
    {
        /// The catalogue, loaded on first use; nullptr when the translator cannot give it.
        std::function<const CommandCatalog *()> catalog;
        /// Styles that can be written as |.Name: name and a description (kind, parent).
        std::function<QList<QPair<QString, QString>>()> styles;
        /// IDs of the document: id and the text of its element.
        std::function<QList<QPair<QString, QString>>()> ids;
        /// The file kind of an editor by its name (document, fragment, module, styles, project).
        std::function<QString(const CodeEditor *)> fileKind;
        /// Files of the project as paths relative to the directory of the editor's file.
        std::function<QStringList(const CodeEditor *)> files;
        /// More actions at the end of the context menu of an editor at a position
        /// (MainWindow: the submenu of parallel tracks, 7.7).
        std::function<void(class QMenu *, CodeEditor *, int)> contextMenu;
    };

    explicit EditorAssist(Providers providers, QObject *parent = nullptr);

    /// Watch editor for hover, typing, Ctrl+Space, Tab and Esc.
    void attach(CodeEditor *editor);
    /// Insert snippet at cursor (Snippet::insert) and let Tab walk its placeholders.
    void insertSnippet(CodeEditor *editor, QTextCursor &cursor, const QString &snippet, bool block);
    /// The tooltip for the construct at position of editor's document, or empty.
    QString tooltipAt(const CodeEditor *editor, int position) const;
    /// The specification section ("4.2") of the construct at position, or empty.
    QString sectionAt(const CodeEditor *editor, int position) const;
    /// What context help (F1) is taken for: the section and the range of the text it belongs to.
    struct HelpContext
    {
        QString section;   // "4.2", "stdlib:3"; empty — no construct at the position
        int start = -1;    // document positions of the construct (with its arguments (…))
        int end = -1;
        QString text;      // the construct as written, shortened for a title
    };
    HelpContext contextAt(const CodeEditor *editor, int position) const;
    /// Show completions for the text before the editor cursor.
    /// @param explicitRequest  Ctrl+Space: also right after a bare |.
    /// @return whether the popup is shown.
    bool complete(CodeEditor *editor, bool explicitRequest);
    QCompleter *completer() const { return m_completer; }
    bool hasStops() const { return !m_stops.isEmpty(); }
    /// Show the hint for the construct at position at once in a panel inside the editor
    /// viewport, below (or above) the construct; false when there is no hint there.
    bool showHint(CodeEditor *editor, int position);
    /// The hint panel while it is shown, else nullptr.
    class QLabel *hintPanel() const;
    void hideHint();
    /// The hint panel shows a hover hint (closes when the mouse leaves the construct).
    // isNull() lets QLabel stay incomplete here: in older Qt (6.4, 6.8) QPointer has no
    // explicit operator bool, and the conversion through T* needs the full type.
    bool hintIsHover() const { return !m_hint.isNull() && !m_hintSticky; }

signals:
    /// Open the specification at section (the palette, the console).
    void sectionRequested(const QString &section);
    /// Context help for the construct at position of editor (the context menu item
    /// "Specification, section N"; MainWindow marks the construct and opens the section).
    void contextHelpRequested(CodeEditor *editor, int position);
    /// Add the missing recommended metadata to the header of editor (the context menu of the
    /// header; MainWindow does it as Insert → Header: add missing fields).
    void addHeaderFieldsRequested(CodeEditor *editor);

protected:
    bool eventFilter(QObject *watched, QEvent *event) override;

private:
    /// What a token of a line is: a command, a short form, a style or a reference.
    struct Token
    {
        enum Kind { None, Command, ShortForm, Style, Reference, Closing, Function, HeaderKey } kind = None;
        QString name;   // command name, short form character, style name, id; for Closing the text (end.Figure)
        QString label;  // Closing: the catalogue form (|end.Ім'я, |end>, |end name, |endif…);
                        // Function: the owner before the point (math in math.sqrt, x in x.split), "." when
                        // something else stands before the point, empty for a plain call;
                        // HeaderKey: the file kind (name is the key path)
        int line = -1;  // block number of the token
        int start = -1; // columns of the token in its line (start inclusive, end exclusive)
        int end = -1;
    };
    Token tokenAt(const CodeEditor *editor, int position) const;
    /// A function name in code at column of block (Token::Function), or None.
    Token codeToken(const QTextBlock &block, int column) const;
    /// Whether the file text defines the name (code, |let, for, def, a parameter of the header):
    /// then a bare use of it is a variable and gets no function hint.
    static bool definesName(const QString &text, const QString &name);
    /// Index of the catalogue entry of a command or a short form, or -1.
    int entryFor(const Token &token) const;
    void typed(CodeEditor *editor, int position, int added, int removed);
    void showSignature(CodeEditor *editor, const QString &before);
    void activated(const QModelIndex &index);
    bool nextStop(CodeEditor *editor);
    /// Show text in the hint panel below (or above) position; sticky — kept when the mouse
    /// moves (forced hints and signatures), else a hover hint.
    bool showHintText(CodeEditor *editor, int position, const QString &text, bool sticky);

    /// The kind of the file of editor (the header "kind:", else by the file name).
    QString kindOf(const CodeEditor *editor) const;
    /// Completion in the YAML header (14.14); false when the cursor is not in a header.
    bool completeHeader(CodeEditor *editor, bool explicitRequest, bool *handled);
    /// The hint of a header key: summary, type, values, example, section; on "document"
    /// the recommended fields not filled yet.
    QString headerTooltip(const CodeEditor *editor, const Token &token) const;
    /// The recommended metadata keys (leaf names) the header of editor does not fill.
    QStringList missingMetadata(const CodeEditor *editor) const;
    /// The section for a header place without a key (a blank line): its mapping, else the
    /// header of the file kind; "" outside the header.
    QString headerSection(const CodeEditor *editor, int position) const;
    /// The values offered for a header key (completion and the context menu).
    QStringList headerValues(CodeEditor *editor, const CommandCatalog::HeaderKey &key) const;
    /// The header part of the context menu: Insert key ▸, Value ▸, missing metadata, all keys.
    void addHeaderActions(QMenu *menu, QAction *before, CodeEditor *editor, int position);
    /// Apply a header edit as one undo step and put the cursor at its value.
    void applyEdit(CodeEditor *editor, const HeaderAssist::Edit &edit);

    enum class Context { None, Command, Style, Reference, Function, Header };
    Providers m_providers;
    QCompleter *m_completer = nullptr;
    QStandardItemModel *m_model = nullptr;
    Context m_context = Context::None;
    QString m_prefix;
    bool m_inserting = false;
    QPointer<CodeEditor> m_stopsEditor;
    QList<QTextCursor> m_stops;   // remaining placeholders of the last snippet
    QPointer<class QLabel> m_hint;   // the hint panel, a child of an editor viewport
    bool m_hintSticky = false;       // forced or signature: kept when the mouse moves
};
