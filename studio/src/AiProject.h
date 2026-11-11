#pragma once

// A project made by AI (stage 27, the first scenario: "create a project from scratch").
//
// The tool works in a temporary work directory that is empty at the start and may write files
// there only (the write arguments of the agent). Studio never lets it near the user's files: after
// the answer it reads the work directory (this file), checks the result with the translator, shows
// the list of files with the check, and writes the files that the user chooses into the new
// project directory.

#include <QByteArray>
#include <QList>
#include <QString>
#include <QStringList>

namespace AiProject {

/// Limits of what is taken from the work directory: more is a runaway tool, not a project.
constexpr int MaxFiles = 200;
constexpr qint64 MaxFileSize = 1024 * 1024;
constexpr qint64 MaxTotalSize = 8 * 1024 * 1024;


/// A file of the proposed project.
struct File
{
    QString path;        ///< relative to the project directory, with '/'
    QByteArray data;     ///< UTF-8 text
    bool remove = false; ///< a change of a project: the file is deleted (a block "<<<<<<< DELETE path")
};

/// What the work directory holds.
struct Scan
{
    QList<File> files;
    QStringList skipped;   ///< a line for each thing that is left out, with the reason
};


/// The rules and the layout for the tool (added to the request of a project): where the files go,
/// what a project file is, what the tool must not do.
QString instructions();

/// The text of the prompt that asks the tool to fix the errors of the check in the same work directory.
QString fixTask(const QStringList &errors);

/// The tool that cannot (or must not) write files delivers them in the answer, each in a block
///
///     <<<<<<< FILE relative/path.ext
///     the text of the file
///     >>>>>>> END FILE
///
/// This works with every tool in its read-only mode and needs no sandbox for writing.
/// The rules and the layout for that delivery (instead of instructions()).
QString instructionsInAnswer();

/// The fix request for the delivery in the answer: the errors and the current files (the tool answers with the changed ones).
QString fixTaskInAnswer(const QStringList &errors, const QList<File> &files);

/// The file blocks of an answer, in the order of the answer; a later block of the same path replaces the earlier one.
/// Blocks that are not closed, or have an unsafe path, are named in `problems`; lines of Markdown fences around a block are ignored.
QList<File> parseFiles(const QString &response, QStringList *problems = nullptr);

/// Changing an existing project (the second step of stage 27): the tool gets the files of the project in the
/// request and answers with the blocks of the files it changes or adds (the WHOLE new text) and with
/// "<<<<<<< DELETE path" / ">>>>>>> END FILE" blocks for the files to delete.
QString instructionsForChange();

/// Can a change of this project path be made: the path is safe and neither it nor a directory above it (inside
/// the project) is a symbolic link, so that writing it cannot reach anything outside the project.
bool changeAllowed(const QString &projectRoot, const QString &relative);

/// A copy of the project in the directory (files are copied, files above 2 MB and links to directories are linked),
/// without the service and build directories: the translator checks the project there while the changes of the
/// tool are put into the copy; the project itself is not touched.
/// @return false with the reason in error.
bool mirror(const QString &projectRoot, const QString &directory, QString *error);

/// Put a change into the mirror: the link is replaced by a real file (never written through the link), or removed.
bool putChange(const QString &directory, const File &change, QString *error);

/// The answer without the file blocks (the explanation of the tool).
QString withoutFiles(const QString &response);

/// Is a relative path acceptable for a file of a project: not absolute, no "..", no drive letter or
/// backslash, no hidden or empty component, plain characters, not too long.
bool safePath(const QString &relative);

/// The files of the directory, recursively: regular text files (UTF-8) with safe paths only; symbolic
/// links, hidden files, binaries, files over MaxFileSize and anything beyond MaxFiles / MaxTotalSize go to `skipped`.
Scan scan(const QString &directory);

/// The result of `primula check` of the proposed project.
struct Check
{
    bool ran = false;
    QString failure;         ///< why the translator did not run
    int errors = 0;
    int warnings = 0;
    QStringList lines;       ///< "file:line: [code] message" for each error and warning
};

/// Check the project in the directory: project.p.prml when it is there, otherwise each top-level document.
Check check(const QString &directory);

/// The files of `files` that already exist in the target directory.
QStringList existing(const QString &target, const QList<File> &files);

/// Write the files into the target directory (created when it does not exist; a file that exists is replaced).
/// @param written  receives the absolute paths written; may be null.
/// @return false with the reason in error; the files written before the failure stay.
bool write(const QString &target, const QList<File> &files, QString *error, QStringList *written = nullptr);

/// The file Studio opens first: project.p.prml, else the first top-level .prml document, else empty.
QString entryFile(const QList<File> &files);

} // namespace AiProject
