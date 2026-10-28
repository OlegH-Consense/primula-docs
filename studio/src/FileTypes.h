#pragma once

// File types of the project (iteration I1, item С2): which files the Files panel
// shows and how a file opens — the editor, the PDF preview, the program of the
// desktop or a command of the user. Three layers, later ones override earlier ones
// by pattern: built in (:/config/file-types.json), the user file
// (~/.config/primula-docs/file-types.json) and the project file
// (.primula-studio/file-types.json; it cannot run commands).

#include <QList>
#include <QString>
#include <QStringList>

struct FileType
{
    QString name;
    QStringList patterns;
    /// editor, preview, system or command.
    QString open;
    /// Program and arguments; %f, %d, %r are replaced when the command starts.
    QStringList command;
    /// Where the type comes from: builtin, user or project (messages, the context menu).
    QString origin;
};

class FileTypes
{
public:
    /// Load the built-in types, then the user file and the project file (an empty root: none).
    /// Problems of the files (invalid JSON, a command in a project file) go to problems().
    void load(const QString &userFile, const QString &projectRoot);
    /// Add the types of a JSON text; ``origin`` is user or project. Returns false for invalid JSON.
    bool addJson(const QByteArray &json, const QString &origin, const QString &file);
    /// Patterns of every type, for the name filters of the Files panel.
    QStringList patterns() const;
    /// The type of a file name (the last layer wins), or nullptr.
    const FileType *typeOf(const QString &fileName) const;
    /// Problems found while loading, one line each.
    QStringList problems() const { return m_problems; }

    /// The command of a type with %f, %d, %r replaced for a file.
    static QStringList expand(const QStringList &command, const QString &file, const QString &projectRoot);
    /// The user file: XDG_CONFIG_HOME/primula-docs/file-types.json.
    static QString userFile();
    /// The project file: ROOT/.primula-studio/file-types.json.
    static QString projectFile(const QString &projectRoot);

private:
    QList<FileType> m_types;
    QStringList m_problems;
};
