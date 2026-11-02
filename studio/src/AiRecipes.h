#pragma once

// Ready tasks of «Ask AI» (stage 22.4): the built-in ones (studio/resources/ai-recipes.json) and those of the
// user file (~/.config/primula-docs/ai-recipes.json, the same format: a recipe with the same id replaces).

#include <QList>
#include <QString>
#include <QStringList>

struct AiRecipe
{
    QString id;
    QString title;       ///< in the language asked for
    QString task;        ///< the same
    bool edits = false;  ///< ask for edits that can be checked and applied
    QString scope = QStringLiteral("any");   ///< "selection", "document" or "any"
    QString sections;    ///< sections of the specification for «Sections in full»
};

namespace AiRecipes {

QString userFile();

/// The built-in recipes, then those of the user file.
/// @param language  en, uk or ru; a text that is missing in it is taken from en.
/// @param warnings  receives a line for each file or entry that is skipped; may be null.
QList<AiRecipe> load(const QString &language, const QString &userPath, QStringList *warnings = nullptr);

} // namespace AiRecipes
