#pragma once

// Templates of new files and projects (stage 14.9, remark З9).
//
// A template is a directory with `template.json` and the files to copy:
//
//   {"kind": "document" | "fragment" | "module" | "styles" | "project" | "order",
//    "order": 10,                                  // position in the list
//    "title": {"en": …, "uk": …, "ru": …}, "description": {…},
//    "files": [{"from": "doc.prml", "to": "{{name}}.prml", "open": true}, …],
//    "strings": {"en": {"key": "text"}, "uk": {…}, "ru": {…}}}
//
// Placeholders in file names and texts: {{name}}, {{title_yaml}} (the title
// with " and \ escaped for a YAML double-quoted string), {{lang}} (uk-UA,
// ru-RU, en-US), {{date}} (ISO), {{year}}, {{s.<key>}} (a string of the
// template in the chosen language); an order project also has {{base}},
// {{targets}}, {{styles}} and {{order_yaml}}.
//
// Built-in templates are resources of Studio (studio/templates/); the user's
// own ones are read from ~/.config/primula-docs/templates/<id>/ and replace a
// built-in template with the same id.

#include <QHash>
#include <QJsonObject>
#include <QList>
#include <QString>
#include <QStringList>

struct TemplateFile
{
    QString from;
    QString to;
    bool open = false;
};

struct FileTemplate
{
    QString id;
    QString kind;
    QString directory;   ///< where the template files are (a resource or the user directory)
    int order = 0;
    bool user = false;
    QJsonObject titles;
    QJsonObject descriptions;
    QJsonObject strings;
    QList<TemplateFile> files;

    QString title(const QString &language) const;
    QString description(const QString &language) const;
};

namespace Templates {

/// The kinds in menu order.
QStringList kinds();
/// Templates of a kind (all kinds for an empty one), by order.
QList<FileTemplate> available(const QString &kind = {});
/// The user directory of templates (~/.config/primula-docs/templates).
QString userDirectory();
/// Language tag of the document header for a template language (uk -> uk-UA).
QString languageTag(const QString &language);
/// Replace the placeholders of text.
QString fill(const QString &text, const QHash<QString, QString> &values, const QJsonObject &strings);
/// Absolute paths the template creates in directory.
QStringList plannedFiles(const FileTemplate &tpl, const QString &directory, const QHash<QString, QString> &values);
/// Create the files (refusing to overwrite any existing file).
/// @param created  receives the created paths; @param toOpen receives those marked "open".
bool instantiate(const FileTemplate &tpl, const QString &directory, const QHash<QString, QString> &values,
                 const QString &language, QStringList *created, QStringList *toOpen, QString *errorMessage);

} // namespace Templates
