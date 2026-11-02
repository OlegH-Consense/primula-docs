#include "AiRecipes.h"

#include <QDir>
#include <QFile>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QStandardPaths>

namespace {

QString localized(const QJsonValue &value, const QString &language)
{
    if (value.isString()) return value.toString();
    const QJsonObject texts = value.toObject();
    const QString text = texts.value(language).toString();
    return text.isEmpty() ? texts.value(QStringLiteral("en")).toString() : text;
}

} // namespace

QString AiRecipes::userFile()
{
    return QDir(QStandardPaths::writableLocation(QStandardPaths::GenericConfigLocation))
        .filePath(QStringLiteral("primula-docs/ai-recipes.json"));
}

QList<AiRecipe> AiRecipes::load(const QString &language, const QString &userPath, QStringList *warnings)
{
    QList<AiRecipe> recipes;
    auto note = [warnings](const QString &text) { if (warnings) warnings->append(text); };
    auto read = [&](const QString &path) {
        QFile file(path);
        if (!file.open(QIODevice::ReadOnly)) return;   // the user file is optional
        QJsonParseError parseError;
        const QJsonDocument json = QJsonDocument::fromJson(file.readAll(), &parseError);
        if (parseError.error != QJsonParseError::NoError || !json.isObject()) {
            note(QStringLiteral("%1: %2").arg(path, parseError.errorString()));
            return;
        }
        int number = 0;
        for (const QJsonValue &entry : json.object().value(QStringLiteral("recipes")).toArray()) {
            ++number;
            const QJsonObject object = entry.toObject();
            AiRecipe recipe;
            recipe.id = object.value(QStringLiteral("id")).toString();
            recipe.title = localized(object.value(QStringLiteral("title")), language);
            recipe.task = localized(object.value(QStringLiteral("task")), language);
            recipe.edits = object.value(QStringLiteral("edits")).toBool();
            recipe.scope = object.value(QStringLiteral("scope")).toString(QStringLiteral("any"));
            recipe.sections = object.value(QStringLiteral("sections")).toString();
            if (recipe.id.isEmpty() || recipe.title.isEmpty() || recipe.task.isEmpty()
                || (recipe.scope != QStringLiteral("selection") && recipe.scope != QStringLiteral("document")
                    && recipe.scope != QStringLiteral("any"))) {
                note(QStringLiteral("%1, recipe %2: id, title, task and scope (selection, document, any) are needed").arg(path).arg(number));
                continue;
            }
            bool replaced = false;
            for (AiRecipe &known : recipes)
                if (known.id == recipe.id) { known = recipe; replaced = true; }
            if (!replaced) recipes.append(recipe);
        }
    };
    read(QStringLiteral(":/ai/ai-recipes.json"));
    if (!userPath.isEmpty()) read(userPath);
    return recipes;
}
