#pragma once

// Location and synchronous use of the Primula translator (the `primula` command).
//
// Studio never imports translator modules: it runs the command line and reads
// its JSON (specification 14.1, decision 124). Long runs (build, check) go
// through BuildController; this class serves short queries such as
// `primula --version` and `primula check project.p.prml --dump-project`.

#include <QByteArray>
#include <QJsonObject>
#include <QString>
#include <QStringList>

namespace Translator {

/// The translator program: the user setting `tools/primula`, otherwise `primula`
/// found in PATH, otherwise the `primula` launcher of the source tree next to a
/// development build (studio/build/primula-studio -> ../../primula). Empty if none.
QString program();

/// Run the translator synchronously.
/// @param arguments  command-line arguments after the program.
/// @param workingDirectory  directory of the process (the project root).
/// @param output  receives stdout; may be null.
/// @param errors  receives stderr, or a description of a start failure; may be null.
/// @param timeoutMs  limit of the run; the process is killed after it.
/// @return the exit code, or -1 if the program could not be started or timed out.
int run(const QStringList &arguments, const QString &workingDirectory, QByteArray *output,
        QString *errors, int timeoutMs = 30000);

/// `primula --version` (e.g. "primula-docs 0.1.0.dev18 (stage 14.2)"), or empty.
QString version();

/// `primula check FILE --dump-project`: the descriptive section of a project file as JSON
/// (root, name, language, styles, params, targets, documents, messages).
/// @return the object, or an empty object with errorMessage set when the output is not JSON.
QJsonObject dumpProject(const QString &projectFile, QString *errorMessage = nullptr);

} // namespace Translator
