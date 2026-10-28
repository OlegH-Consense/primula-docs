#pragma once

// A Primula project as Primula Studio sees it (stage 14.3).
//
// Studio has no project file of its own: the user opens a Primula project file
// (`project.p.prml`) or any document; the project is found as the translator
// finds it (specification 10.6: upwards from the document, stopping after a
// directory with `.git`). Everything about the documents — root, targets,
// styles, documents — comes from `primula check project.p.prml --dump-project`.
//
// Studio keeps its own data in the service directory `.primula-studio/` in the
// project root; for a project with `extends` that is the root of the base
// project, so a contract and all its orders share one directory (decision of
// the user, 15.10.2026):
//
//   .primula-studio/settings.json   sessions of opened files, build and AI settings
//   .primula-studio/ai-context.md   AI context of the project (Markdown, edited as a tab)
//   .primula-studio/ai-history/     AI requests and responses
//
// settings.json (schema 1):
//   {"schema": 1,
//    "sessions": {"<opened path relative to the root>": {...workspace state...}},
//    "build": {"pdfAfterBuild": "never" | "always" | "visible", "strict": false},
//    "ai": {"backend": "codex-exec", ...}}

#include <QJsonObject>
#include <QList>
#include <QString>
#include <QStringList>

struct BuildTarget
{
    QString source;  ///< absolute path of the source document
    QString output;  ///< absolute path of the ODT
    QString pdf;     ///< absolute path of the PDF written by `build --pdf`
};

class StudioProject
{
public:
    /// The project file for path: path itself when it is a project file
    /// (`*.p.prml`), otherwise `project.p.prml` searched upwards from its
    /// directory; the search stops after a directory containing `.git`.
    /// Empty when there is no project.
    static QString findProjectFile(const QString &path);

    /// Open path (a project file or a document) and read the project with the
    /// translator; settings.json is read when present.
    /// @return false with errorMessage when the project description cannot be read
    /// (the translator is missing or the project header is invalid).
    bool open(const QString &path, QString *errorMessage = nullptr);

    bool isOpen() const { return !m_opened.isEmpty(); }
    /// The file the user opened (absolute).
    QString openedPath() const { return m_opened; }
    /// The project file (absolute) or empty for a document without a project.
    QString projectFile() const { return m_projectFile; }
    bool hasProjectFile() const { return !m_projectFile.isEmpty(); }
    /// Project root: paths of messages and targets are relative to it.
    QString root() const { return m_root; }
    QString name() const { return m_name; }
    /// The project language (`language` of the project header), e.g. "uk-UA"; empty without one.
    QString language() const { return m_language; }
    /// Whether the project names styles modules itself (else the built-in default applies).
    bool declaresStyles() const { return m_declaresStyles; }
    QList<BuildTarget> targets() const { return m_targets; }
    /// Absolute paths of the styles modules of the project (built-in `std/…` excluded).
    QStringList styleModules() const { return m_styles; }
    /// Messages of reading the project header (translator JSON form).
    QList<QJsonObject> messages() const { return m_messages; }

    /// The document opened, or the source of the first target of an opened project.
    QString primaryDocument() const;
    /// The ODT and PDF of a document: its target outputs, or `build/<name>.odt|.pdf` in the root.
    BuildTarget outputsFor(const QString &document) const;
    /// Whether document is the source of a target of the project.
    bool isTarget(const QString &document) const;

    /// Path relative to the root (with '/'), or the absolute path for a file outside it.
    QString relative(const QString &path) const;
    /// Absolute path of a path relative to the root (absolute paths are kept).
    QString absolute(const QString &path) const;

    QString serviceDirectory() const;
    QString settingsPath() const;
    QString aiContextPath() const;
    QString aiHistoryDirectory() const;

    /// The workspace state of the opened path (empty object when none).
    QJsonObject session() const;
    void setSession(const QJsonObject &state);
    /// A group of settings.json shared by all sessions ("build", "ai").
    QJsonObject group(const QString &name) const;
    void setGroup(const QString &name, const QJsonObject &value);
    /// Write settings.json atomically, creating the service directory.
    bool saveSettings(QString *errorMessage = nullptr) const;
    /// Create ai-context.md with a short heading when it does not exist.
    bool ensureAiContext(QString *errorMessage = nullptr) const;

private:
    QString m_opened;
    QString m_projectFile;
    QString m_root;
    QString m_name;
    QString m_language;
    bool m_declaresStyles = false;
    QList<BuildTarget> m_targets;
    QStringList m_styles;
    QList<QJsonObject> m_messages;
    QJsonObject m_settings;

    QString sessionKey() const;
};
