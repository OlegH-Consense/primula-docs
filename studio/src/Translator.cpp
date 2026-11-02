#include "Translator.h"

#include <QCoreApplication>
#include <QDir>
#include <QFileInfo>
#include <QJsonDocument>
#include <QProcess>
#include <QSettings>
#include <QStandardPaths>

namespace Translator {

QString program()
{
    const QString configured = QSettings().value(QStringLiteral("tools/primula")).toString().trimmed();
    if (!configured.isEmpty())
        return configured;
    const QString found = QStandardPaths::findExecutable(QStringLiteral("primula"));
    if (!found.isEmpty())
        return found;
    // A development build inside the repository: studio/build/primula-studio.
    const QDir application(QCoreApplication::applicationDirPath());
    for (const QString &relative : {QStringLiteral("../../primula"), QStringLiteral("../primula")}) {
        const QFileInfo launcher(application.filePath(relative));
        if (launcher.isFile() && launcher.isExecutable())
            return launcher.canonicalFilePath();
    }
    return {};
}

int run(const QStringList &arguments, const QString &workingDirectory, QByteArray *output,
        QString *errors, int timeoutMs)
{
    const QString executable = program();
    if (executable.isEmpty()) {
        if (errors)
            *errors = QCoreApplication::translate("Translator",
                "The Primula translator is not found: install 'primula' into PATH or set its path in the settings.");
        return -1;
    }
    QProcess process;
    process.setWorkingDirectory(workingDirectory);
    process.start(executable, arguments);
    if (!process.waitForStarted(5000)) {
        if (errors)
            *errors = QCoreApplication::translate("Translator", "Cannot start %1: %2")
                          .arg(executable, process.errorString());
        return -1;
    }
    if (!process.waitForFinished(timeoutMs)) {
        process.kill();
        process.waitForFinished(1000);
        if (errors)
            *errors = QCoreApplication::translate("Translator", "%1 did not finish in %2 s")
                          .arg(executable).arg(timeoutMs / 1000);
        return -1;
    }
    if (output)
        *output = process.readAllStandardOutput();
    if (errors)
        *errors = QString::fromUtf8(process.readAllStandardError());
    return process.exitStatus() == QProcess::NormalExit ? process.exitCode() : -1;
}

QString version()
{
    QByteArray output;
    if (run({QStringLiteral("--version")}, QDir::currentPath(), &output, nullptr, 15000) != 0)
        return {};
    return QString::fromUtf8(output).trimmed();
}

QJsonObject dumpProject(const QString &projectFile, QString *errorMessage)
{
    const QFileInfo file(projectFile);
    QByteArray output;
    QString errors;
    // Exit code 2 still prints the object (an invalid header has messages).
    const int code = run({QStringLiteral("check"), file.fileName(), QStringLiteral("--dump-project")},
                         file.absolutePath(), &output, &errors);
    QJsonParseError parse;
    const QJsonDocument document = QJsonDocument::fromJson(output, &parse);
    if (code < 0 || parse.error != QJsonParseError::NoError || !document.isObject()) {
        if (errorMessage)
            *errorMessage = errors.trimmed().isEmpty()
                ? QCoreApplication::translate("Translator", "The translator gave no project description.")
                : errors.trimmed();
        return {};
    }
    return document.object();
}

QString describeFile(const QString &file, const QString &language, QString *errorMessage)
{
    const QFileInfo info(file);
    QByteArray output;
    QString errors;
    const int code = run({QStringLiteral("describe"), info.fileName(), QStringLiteral("--lang"), language},
                         info.absolutePath(), &output, &errors);
    // Exit code 2 still prints the reason (an unreadable file).
    if (code < 0 || output.isEmpty()) {
        if (errorMessage)
            *errorMessage = errors.trimmed().isEmpty()
                ? QCoreApplication::translate("Translator", "The translator gave no summary of the file.")
                : errors.trimmed();
        return {};
    }
    return QString::fromUtf8(output);
}

} // namespace Translator
