#include "AiProject.h"

#include "Translator.h"

#include <QCoreApplication>
#include <QDir>
#include <QDirIterator>
#include <QFile>
#include <QFileInfo>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QSaveFile>
#include <QStringDecoder>

namespace AiProject {

QString instructions()
{
    return QStringLiteral(
        "PROJECT MADE BY YOU. You create a new Primula project in the CURRENT DIRECTORY, an empty work "
        "directory. Use only your file tools to create text files there (UTF-8, LF line ends). Do not run "
        "commands, do not write outside this directory, do not create hidden files, links or binary files, "
        "keep to at most %1 files.\n"
        "Layout of a project (decide the names and the structure by the task):\n"
        "- project.p.prml — the project file. A YAML header between '---' lines with 'kind: project', "
        "'name', 'language' (uk-UA for Ukrainian business documents), 'styles' (a list: std/styles/default, "
        "std/styles/business, … or your own styles modules), 'params' (the data that change: parties, "
        "dates, amounts), 'keys' (a map of names to files or fragments) and 'targets' (a list of "
        "'{source: document.prml, output: out/document.odt}'); after the header, optionally, code "
        "(definitions common to the whole project).\n"
        "- document.prml — a document: a YAML header with 'doc' (title, language, creator, created) and the text in "
        "Primula markup; use the names of the project params in the text, do not copy the data into it.\n"
        "- fragments/*.f.prml (parts included with |include), lib/*.m.prml (modules of definitions imported with "
        "|import), styles/*.s.prml (styles modules), data/ (CSV, YAML) — only what the task needs.\n"
        "Write only the constructs and functions that the PRIMULA REFERENCE or the SPECIFICATION define. After "
        "the files, answer with a short summary in the language of the task: the files and what each one is for. "
        "Studio checks the project with the translator after your answer and may send the errors back to you.")
        .arg(MaxFiles);
}

QString fixTask(const QStringList &errors)
{
    return QStringLiteral(
               "The project in the current directory was checked with the translator and has errors. Fix them by "
               "editing the files (do not start a new project). The errors:\n%1\nAnswer with a short summary of "
               "what you changed.")
        .arg(errors.join(QLatin1Char('\n')));
}

QString instructionsInAnswer()
{
    return QStringLiteral(
        "PROJECT MADE BY YOU. You create a new Primula project. Do NOT use file tools or commands: deliver every file of the "
        "project in your answer, each in a block of exactly this form (the path is relative to the project directory, with '/'):\n"
        "<<<<<<< FILE project.p.prml\nthe whole text of the file\n>>>>>>> END FILE\n"
        "Write text files only (UTF-8), no hidden files, no '..' in paths, at most %1 files. Outside the blocks write a short summary "
        "in the language of the task: the files and what each one is for.\n"
        "Layout of a project (decide the names and the structure by the task):\n"
        "- project.p.prml — the project file. A YAML header between '---' lines with 'kind: project', "
        "'name', 'language' (uk-UA for Ukrainian business documents), 'styles' (a list: std/styles/default, "
        "std/styles/business, … or your own styles modules), 'params' (the data that change: parties, "
        "dates, amounts), 'keys' (a map of names to files or fragments) and 'targets' (a list of "
        "'{source: document.prml, output: out/document.odt}'); after the header, optionally, code "
        "(definitions common to the whole project).\n"
        "- document.prml — a document: a YAML header with 'doc' (title, language, creator, created) and the text in "
        "Primula markup; use the names of the project params in the text, do not copy the data into it.\n"
        "- fragments/*.f.prml (parts included with |include), lib/*.m.prml (modules of definitions imported with "
        "|import), styles/*.s.prml (styles modules), data/ (CSV, YAML) — only what the task needs.\n"
        "Write only the constructs and functions that the PRIMULA REFERENCE or the SPECIFICATION define. Studio checks the "
        "project with the translator after your answer and may send the errors back to you.")
        .arg(MaxFiles);
}

QString fixTaskInAnswer(const QStringList &errors, const QList<File> &files)
{
    QString text = QStringLiteral(
                       "The project below was checked with the translator and has errors. Fix them. Answer with the blocks "
                       "(<<<<<<< FILE path … >>>>>>> END FILE) of the files that you change, each with its WHOLE new text; "
                       "files that stay as they are need no block. The errors:\n%1\n\nTHE FILES OF THE PROJECT:")
                       .arg(errors.join(QLatin1Char('\n')));
    for (const File &file : files)
        text += QStringLiteral("\n\n<<<<<<< FILE %1\n%2\n>>>>>>> END FILE").arg(file.path, QString::fromUtf8(file.data).trimmed());
    return text;
}

QList<File> parseFiles(const QString &response, QStringList *problems)
{
    static const QString opening = QStringLiteral("<<<<<<< FILE ");
    static const QString closing = QStringLiteral(">>>>>>> END FILE");
    QList<File> files;
    const QStringList lines = response.split(QLatin1Char('\n'));
    for (int i = 0; i < lines.size(); ++i) {
        const QString head = lines.at(i).trimmed();
        const bool deletion = head.startsWith(QStringLiteral("<<<<<<< DELETE "));
        if (!head.startsWith(opening) && !deletion) continue;
        const QString path = head.mid(deletion ? QStringLiteral("<<<<<<< DELETE ").size() : opening.size()).trimmed();
        QStringList body;
        int j = i + 1;
        while (j < lines.size() && lines.at(j).trimmed() != closing) body << lines.at(j++);
        if (j >= lines.size()) {
            if (problems) *problems << QCoreApplication::translate("AiProject", "%1: the block is not closed").arg(path);
            break;
        }
        i = j;
        if (!safePath(path)) {
            if (problems) *problems << QCoreApplication::translate("AiProject", "%1: a path that is not allowed (hidden, absolute or with special characters)").arg(path);
            continue;
        }
        if (deletion) {
            bool replacedDeletion = false;
            for (File &file : files)
                if (file.path == path) { file.data.clear(); file.remove = true; replacedDeletion = true; }
            if (!replacedDeletion && files.size() < MaxFiles) files.append({path, QByteArray(), true});
            continue;
        }
        QString text = body.join(QLatin1Char('\n'));
        while (text.endsWith(QLatin1Char('\r'))) text.chop(1);
        const QByteArray data = (text + QLatin1Char('\n')).toUtf8();
        if (data.size() > MaxFileSize) {
            if (problems) *problems << QCoreApplication::translate("AiProject", "%1: larger than %2 KB").arg(path).arg(MaxFileSize / 1024);
            continue;
        }
        bool replaced = false;
        for (File &file : files)
            if (file.path == path) { file.data = data; file.remove = false; replaced = true; }
        if (!replaced && files.size() < MaxFiles) files.append({path, data, false});
        else if (!replaced && problems) *problems << QCoreApplication::translate("AiProject", "%1: more than %n file(s) (the limit)", nullptr, MaxFiles).arg(path);
    }
    return files;
}

QString instructionsForChange()
{
    return QStringLiteral(
        "CHANGING A PROJECT. The project is described below: the list of its files and the text of the files that the user "
        "sent. Do NOT use file tools or commands: deliver the changes in your answer. For every file that you change or add, "
        "write a block of exactly this form (the path is relative to the project directory, with '/'; the WHOLE new text of "
        "the file, not a fragment):\n"
        "<<<<<<< FILE fragments/payment.f.prml\nthe whole new text of the file\n>>>>>>> END FILE\n"
        "For a file that must be deleted write:\n<<<<<<< DELETE old.prml\n>>>>>>> END FILE\n"
        "Files that stay as they are need no block. Do not touch what the task does not ask for: keep the names of styles, "
        "ids, parameters and the form of the constructs. Text files only (UTF-8), no hidden files, no '..' in paths, at most "
        "%1 files. Outside the blocks write a short summary in the language of the task: what you changed and why. Write only "
        "the constructs and functions that the PRIMULA REFERENCE or the SPECIFICATION define. Studio checks the changed project "
        "with the translator after your answer, shows the user the differences and may send the errors back to you.")
        .arg(MaxFiles);
}

bool changeAllowed(const QString &projectRoot, const QString &relative)
{
    if (!safePath(relative)) return false;
    const QDir root(projectRoot);
    QString current = projectRoot;
    const QStringList parts = relative.split(QLatin1Char('/'));
    for (const QString &part : parts) {
        current = QDir(current).filePath(part);
        if (QFileInfo(current).isSymLink()) return false;
    }
    return true;
}

bool mirror(const QString &projectRoot, const QString &directory, QString *error)
{
    static const QStringList skipped = {QStringLiteral(".primula-studio"), QStringLiteral(".git"), QStringLiteral("build"),
                                        QStringLiteral("out"), QStringLiteral("node_modules"), QStringLiteral("__pycache__")};
    const QDir root(projectRoot);
    QDirIterator it(projectRoot, QDir::Files | QDir::Dirs | QDir::NoDotAndDotDot | QDir::Hidden | QDir::System,
                    QDirIterator::Subdirectories);
    while (it.hasNext()) {
        it.next();
        const QFileInfo info = it.fileInfo();
        const QString relative = root.relativeFilePath(info.filePath());
        const QStringList parts = relative.split(QLatin1Char('/'));
        bool skip = false;
        for (const QString &part : parts) skip = skip || skipped.contains(part);
        if (skip || (parts.size() == 1 && parts.first().startsWith(QLatin1Char('.')))) continue;
        const QString target = QDir(directory).filePath(relative);
        if (info.isSymLink() || info.isFile()) {
            // A link of the project (lib → a library) is linked as it is; a file is copied (the translator resolves
            // links: a project file that is a link would put the documents "outside the project"); a large file
            // (an image, a PDF) is linked: no document reads it as text.
            const bool link = info.isSymLink() || info.size() > 2 * 1024 * 1024;
            const QString destination = info.isSymLink() ? info.symLinkTarget() : info.absoluteFilePath();
            if (!QDir().mkpath(QFileInfo(target).absolutePath())
                || !(link ? QFile::link(destination, target) : QFile::copy(destination, target))) {
                if (error) *error = QCoreApplication::translate("AiProject", "Cannot link %1 into the work directory.").arg(relative);
                return false;
            }
        } else if (info.isDir() && !QDir().mkpath(target)) {
            if (error) *error = QCoreApplication::translate("AiProject", "Cannot create the directory %1.").arg(target);
            return false;
        }
    }
    return true;
}

bool putChange(const QString &directory, const File &change, QString *error)
{
    const QString target = QDir(directory).filePath(change.path);
    QFile::remove(target);   // a link is removed, never written through
    if (change.remove) return true;
    if (!QDir().mkpath(QFileInfo(target).absolutePath())) {
        if (error) *error = QCoreApplication::translate("AiProject", "Cannot create the directory of %1.").arg(change.path);
        return false;
    }
    QFile out(target);
    if (!out.open(QIODevice::WriteOnly) || out.write(change.data) != change.data.size()) {
        if (error) *error = QCoreApplication::translate("AiProject", "Cannot write %1: %2").arg(change.path, out.errorString());
        return false;
    }
    return true;
}

QString withoutFiles(const QString &response)
{
    static const QString opening = QStringLiteral("<<<<<<< FILE ");
    static const QString closing = QStringLiteral(">>>>>>> END FILE");
    QStringList kept;
    bool inside = false;
    for (const QString &line : response.split(QLatin1Char('\n'))) {
        const QString trimmed = line.trimmed();
        if (!inside && (trimmed.startsWith(opening) || trimmed.startsWith(QStringLiteral("<<<<<<< DELETE ")))) inside = true;
        else if (inside && trimmed == closing) inside = false;
        else if (!inside && !trimmed.startsWith(QLatin1String("```"))) kept << line;
    }
    return kept.join(QLatin1Char('\n')).trimmed();
}

bool safePath(const QString &relative)
{
    if (relative.isEmpty() || relative.size() > 200) return false;
    if (relative.startsWith(QLatin1Char('/')) || relative.contains(QLatin1Char('\\')) || relative.contains(QLatin1Char(':')))
        return false;
    const QStringList parts = relative.split(QLatin1Char('/'));
    for (const QString &part : parts) {
        if (part.isEmpty() || part == QLatin1String(".") || part == QLatin1String("..") || part.startsWith(QLatin1Char('.')))
            return false;
        for (const QChar c : part)
            if (c.unicode() < 0x20 || QStringLiteral("<>\"|?*").contains(c)) return false;
    }
    return true;
}

Scan scan(const QString &directory)
{
    Scan result;
    const QDir root(directory);
    qint64 total = 0;
    QStringList paths;
    // Symbolic links are listed to be skipped, hidden entries too: the tool must not bring anything of the sort.
    QDirIterator it(directory, QDir::Files | QDir::Dirs | QDir::NoDotAndDotDot | QDir::Hidden | QDir::System,
                    QDirIterator::Subdirectories);
    while (it.hasNext()) {
        it.next();
        const QFileInfo info = it.fileInfo();
        const QString relative = root.relativeFilePath(info.filePath());
        if (info.isSymLink()) {
            result.skipped << QCoreApplication::translate("AiProject", "%1: a symbolic link").arg(relative);
        } else if (info.isFile()) {
            paths << relative;
        }
    }
    paths.sort();
    for (const QString &relative : paths) {
        if (!safePath(relative)) {
            result.skipped << QCoreApplication::translate("AiProject", "%1: a path that is not allowed (hidden, absolute or with special characters)").arg(relative);
            continue;
        }
        QFile file(root.filePath(relative));
        const qint64 size = file.size();
        if (result.files.size() >= MaxFiles) {
            result.skipped << QCoreApplication::translate("AiProject", "%1: more than %n file(s) (the limit)", nullptr, MaxFiles).arg(relative);
            continue;
        }
        if (size > MaxFileSize) {
            result.skipped << QCoreApplication::translate("AiProject", "%1: larger than %2 KB").arg(relative).arg(MaxFileSize / 1024);
            continue;
        }
        if (total + size > MaxTotalSize) {
            result.skipped << QCoreApplication::translate("AiProject", "%1: the total size is over %2 MB").arg(relative).arg(MaxTotalSize / (1024 * 1024));
            continue;
        }
        if (!file.open(QIODevice::ReadOnly)) {
            result.skipped << QCoreApplication::translate("AiProject", "%1: cannot be read").arg(relative);
            continue;
        }
        const QByteArray data = file.readAll();
        QStringDecoder decoder(QStringDecoder::Utf8, QStringDecoder::Flag::Stateless);
        const QString decoded = decoder(data);   // the conversion is lazy: the error is known after it
        if (decoder.hasError() || decoded.contains(QChar(0)) || data.contains('\0')) {
            result.skipped << QCoreApplication::translate("AiProject", "%1: not a UTF-8 text file").arg(relative);
            continue;
        }
        total += size;
        result.files.append({relative, data, false});
    }
    return result;
}

namespace {

bool isSubExtension(const QString &name)
{
    return name.endsWith(QStringLiteral(".f.prml")) || name.endsWith(QStringLiteral(".m.prml")) || name.endsWith(QStringLiteral(".s.prml"))
           || name.endsWith(QStringLiteral(".p.prml"));
}

void collectMessages(const QByteArray &output, Check *check)
{
    const QJsonDocument json = QJsonDocument::fromJson(output);
    for (const QJsonValue &value : json.array()) {
        const QJsonObject message = value.toObject();
        const QString severity = message.value(QStringLiteral("severity")).toString();
        if (severity != QStringLiteral("error") && severity != QStringLiteral("warning")) continue;
        (severity == QStringLiteral("error") ? check->errors : check->warnings)++;
        check->lines << QStringLiteral("%1:%2: [%3] %4").arg(message.value(QStringLiteral("file")).toString())
                            .arg(message.value(QStringLiteral("line")).toInt())
                            .arg(message.value(QStringLiteral("code")).toString(), message.value(QStringLiteral("message")).toString());
    }
}

} // namespace

Check check(const QString &directory)
{
    Check result;
    if (Translator::program().isEmpty()) {
        result.failure = QCoreApplication::translate("AiProject", "The translator is not found.");
        return result;
    }
    // `check project.p.prml` checks the project file, the targets and the outputs, not the text of the
    // documents: so the sources of the targets are checked one by one, after the project file itself.
    QStringList targets;
    const QString projectFile = QDir(directory).filePath(QStringLiteral("project.p.prml"));
    if (QFileInfo::exists(projectFile)) {
        targets << QStringLiteral("project.p.prml");
        const QJsonObject dump = Translator::dumpProject(projectFile);
        for (const QJsonValue &target : dump.value(QStringLiteral("targets")).toArray()) {
            const QString source = target.toObject().value(QStringLiteral("source")).toString();
            if (!source.isEmpty() && !targets.contains(source) && AiProject::safePath(source)) targets << source;
        }
    }
    if (targets.size() <= 1)
        for (const QFileInfo &info : QDir(directory).entryInfoList({QStringLiteral("*.prml")}, QDir::Files, QDir::Name))
            if (!isSubExtension(info.fileName()) && !targets.contains(info.fileName())) targets << info.fileName();
    if (targets.isEmpty()) {
        result.failure = QCoreApplication::translate("AiProject", "There is no project file or document to check.");
        return result;
    }
    for (const QString &target : targets) {
        QByteArray output;
        QString errors;
        const int code = Translator::run({QStringLiteral("check"), target, QStringLiteral("--format"), QStringLiteral("json")},
                                         directory, &output, &errors, 120000);
        if (code < 0) {
            result.failure = errors.isEmpty() ? QCoreApplication::translate("AiProject", "The check did not finish.") : errors;
            return result;
        }
        collectMessages(output, &result);
    }
    result.ran = true;
    return result;
}

QStringList existing(const QString &target, const QList<File> &files)
{
    QStringList found;
    const QDir root(target);
    for (const File &file : files)
        if (QFileInfo::exists(root.filePath(file.path))) found << file.path;
    return found;
}

bool write(const QString &target, const QList<File> &files, QString *error, QStringList *written)
{
    const QDir root(target);
    if (!QDir().mkpath(target)) {
        if (error) *error = QCoreApplication::translate("AiProject", "Cannot create the directory %1.").arg(target);
        return false;
    }
    for (const File &file : files) {
        if (file.remove) continue;   // a deletion is a change of a project, not a file to write
        if (!safePath(file.path)) {
            if (error) *error = QCoreApplication::translate("AiProject", "The path %1 is not allowed.").arg(file.path);
            return false;
        }
        const QString absolute = root.filePath(file.path);
        if (!QDir().mkpath(QFileInfo(absolute).absolutePath())) {
            if (error) *error = QCoreApplication::translate("AiProject", "Cannot create the directory of %1.").arg(file.path);
            return false;
        }
        QSaveFile out(absolute);
        if (!out.open(QIODevice::WriteOnly) || out.write(file.data) != file.data.size() || !out.commit()) {
            if (error) *error = QCoreApplication::translate("AiProject", "Cannot write %1: %2").arg(file.path, out.errorString());
            return false;
        }
        if (written) written->append(absolute);
    }
    return true;
}

QString entryFile(const QList<File> &files)
{
    for (const File &file : files)
        if (file.path == QStringLiteral("project.p.prml")) return file.path;
    for (const File &file : files)
        if (!file.path.contains(QLatin1Char('/')) && file.path.endsWith(QStringLiteral(".prml")) && !isSubExtension(file.path)) return file.path;
    return {};
}

} // namespace AiProject
