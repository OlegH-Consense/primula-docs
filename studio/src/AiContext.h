#pragma once

// Primula context of an AI request (stage 14.10): the parts of the language a model needs to
// answer about a Primula document without guessing.
//
//   reference   the catalogue of constructs and functions of `primula commands` (decisions
//               124, 126) and the YAML header keys (127), one line per entry — compact and
//               exactly what the translator knows
//   sections    chosen sections of the specification or the standard library ("6.8",
//               "stdlib:3"), cut from the copies built into Studio (:/help/…)
//   full        the whole specification and standard library (about 340 KB, ~100k tokens)
//   messages    the messages of the last check or build, as file:line:column lines
//
// The texts are plain; AiController::makePrompt() places them into the request.

#include <QJsonArray>
#include <QString>
#include <QStringList>

class CommandCatalog;

namespace AiContext {

/// How much of the language the request carries (the AI dialog, settings.json "ai"/"context").
enum class Level { None, Reference, Full };

/// The catalogue as text: constructs by category ("|label — summary [§ section]"), then the
/// functions ("signature — summary [§ section]"); empty for an unloaded catalogue.
QString reference(const CommandCatalog &catalog);

/// Section number of markdown: from its heading ("## 6. …", "### 6.8. …") up to the next
/// heading of the same or a higher level; empty when there is no such heading.
QString section(const QString &markdown, const QString &number);

/// Section references of text: numbers separated by commas, spaces or semicolons, a
/// "stdlib:" prefix for the standard library ("6.8, 10.5 stdlib:3"); invalid parts are dropped.
QStringList parseSections(const QString &text);

/// The texts of references, each under a "## Specification, section N" heading (the label
/// of CommandCatalog::sectionLabel); a missing section is named as missing.
QString sections(const QStringList &references);

/// The specification and the standard library built into Studio, whole.
QString fullSpecification();

/// The messages (translator JSON form) as "file:line:column: severity [code] message" lines.
QString messages(const QJsonArray &messages);

} // namespace AiContext
