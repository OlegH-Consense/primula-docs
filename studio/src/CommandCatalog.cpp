#include "CommandCatalog.h"

#include "Translator.h"

#include <QCoreApplication>
#include <QDir>
#include <QFileInfo>
#include <QJsonArray>
#include <QJsonDocument>
#include <QSet>

namespace {

/// Translation context "CommandCatalog" for the messages of this file.
struct Text
{
    Q_DECLARE_TR_FUNCTIONS(CommandCatalog)
};

/// Tooltip lines: the summary, one line per argument (name: type = default — summary), the section.
QString tooltip(const QJsonObject &item)
{
    QStringList lines{item.value(QStringLiteral("summary")).toString()};
    for (const QJsonValue &value : item.value(QStringLiteral("args")).toArray()) {
        const QJsonObject arg = value.toObject();
        QString line = arg.value(QStringLiteral("name")).toString();
        const QString type = arg.value(QStringLiteral("type")).toString();
        if (!type.isEmpty()) line += QStringLiteral(": ") + type;
        const QJsonValue def = arg.value(QStringLiteral("default"));
        if (!def.isNull() && !def.isUndefined())
            line += QStringLiteral(" = ")
                    + (def.isString() ? QStringLiteral("\"%1\"").arg(def.toString())
                       : def.isBool() ? QString::fromLatin1(def.toBool() ? "True" : "False")   // Python literals
                       : def.isDouble() ? QString::number(def.toDouble())
                       : QString::fromUtf8(QJsonDocument(QJsonArray{def}).toJson(QJsonDocument::Compact)).mid(1).chopped(1));
        const QString summary = arg.value(QStringLiteral("summary")).toString();
        if (!summary.isEmpty()) line += QStringLiteral(" — ") + summary;
        lines << QStringLiteral("  ") + line;
    }
    const QString section = item.value(QStringLiteral("section")).toString();
    if (!section.isEmpty()) lines << Text::tr("Specification, section %1").arg(section);
    return lines.join(QLatin1Char('\n'));
}

/// Tooltip of a function: the summary, the arguments, where it may be called, the example
/// with the result the translator computed, the section (specification or library).
QString functionTooltip(const QJsonObject &item, const QString &section)
{
    QJsonObject plain = item;
    plain.remove(QStringLiteral("section"));
    QStringList lines{tooltip(plain)};
    const QString where = item.value(QStringLiteral("where")).toString();
    if (where == QStringLiteral("styles")) lines << Text::tr("Only in styles code: a styles module, the project, the document");
    else if (where == QStringLiteral("cell")) lines << Text::tr("Only in a table cell formula |=(…)");
    else if (where == QStringLiteral("project")) lines << Text::tr("Only in the code of a project file");
    const QString example = item.value(QStringLiteral("example")).toString();
    if (!example.isEmpty()) {
        const QJsonValue result = item.value(QStringLiteral("result"));
        lines << Text::tr("Example: %1").arg(example)
                     + (result.isString() ? QStringLiteral("  →  ") + result.toString() : QString());
    }
    lines << CommandCatalog::sectionLabel(section);
    return lines.join(QLatin1Char('\n'));
}

/// The call template of a function: name(${1:x}, ${2:code})$0 with the arguments that have
/// no default (a variadic one as an empty stop); a constant is its name.
QString functionSnippet(const QJsonObject &item)
{
    QString name = item.value(QStringLiteral("name")).toString();
    if (item.value(QStringLiteral("module")).toString() == QStringLiteral("std/math")) name.prepend(QStringLiteral("math."));
    if (item.value(QStringLiteral("kind")).toString() == QStringLiteral("constant")) return name;
    QStringList stops;
    QSet<QString> seen;
    for (const QJsonValue &value : item.value(QStringLiteral("args")).toArray()) {
        const QJsonObject arg = value.toObject();
        const QString argName = arg.value(QStringLiteral("name")).toString();
        if (!arg.value(QStringLiteral("positional")).toBool() || seen.contains(argName)) continue;
        seen.insert(argName);
        if (argName.startsWith(QLatin1Char('*'))) {
            stops << QStringLiteral("$%1").arg(stops.size() + 1);
            break;
        }
        if (!arg.value(QStringLiteral("default")).isNull()) break;   // optional from here on
        stops << QStringLiteral("${%1:%2}").arg(stops.size() + 1).arg(argName);
    }
    return name + QLatin1Char('(') + stops.join(QStringLiteral(", ")) + QStringLiteral(")$0");
}

} // namespace

QString CommandCatalog::sectionLabel(const QString &section)
{
    if (section.startsWith(QStringLiteral("stdlib:")))
        return Text::tr("Standard library, section %1").arg(section.mid(7));
    return Text::tr("Specification, section %1").arg(section);
}

int CommandCatalog::functionIndex(const QString &name, bool method, bool module) const
{
    int fallback = -1;
    for (int i = 0; i < m_entries.size(); ++i) {
        const Entry &entry = m_entries.at(i);
        if (!entry.function || entry.name != name) continue;
        const bool isMethod = !entry.receiver.isEmpty();
        const bool isModule = !entry.module.isEmpty();
        if (isMethod == method && isModule == module) return i;
        // x.name: a method, else a std/math function under an alias (m.sqrt).
        if (method && isModule && fallback < 0) fallback = i;
    }
    return fallback;
}

const CommandCatalog::HeaderKey *CommandCatalog::headerKey(const QString &kind, const QString &path) const
{
    for (const HeaderKey &key : m_headerKeys)
        if (key.path == path && key.kinds.contains(kind)) return &key;
    return nullptr;
}

bool CommandCatalog::load(const QString &language, QString *error)
{
    if (isLoaded()) return true;
    if (Translator::program().isEmpty()) {
        if (error) *error = Text::tr("The translator is not found.");
        return false;
    }
    QByteArray output;
    QString errors;
    const int code = Translator::run({QStringLiteral("commands"), QStringLiteral("--format"), QStringLiteral("json"),
                                      QStringLiteral("--lang"), language},
                                     QDir::tempPath(), &output, &errors, 30000);
    QJsonParseError parse{};
    const QJsonDocument json = QJsonDocument::fromJson(output, &parse);
    if (code != 0 || !json.isObject()) {
        if (error) *error = Text::tr("primula commands failed: %1").arg(errors.trimmed().isEmpty() ? parse.errorString() : errors.trimmed());
        return false;
    }
    return setJson(json.object(), error);
}

bool CommandCatalog::setJson(const QJsonObject &json, QString *error)
{
    m_categories.clear();
    m_entries.clear();
    for (const QJsonValue &value : json.value(QStringLiteral("categories")).toArray())
        m_categories.append({value.toObject().value(QStringLiteral("id")).toString(),
                             value.toObject().value(QStringLiteral("title")).toString()});
    // Commands: a construct without an inline form, or a multi-line or ':' snippet, takes whole lines.
    for (const QJsonValue &value : json.value(QStringLiteral("commands")).toArray()) {
        const QJsonObject item = value.toObject();
        Entry entry;
        entry.label = QStringLiteral("|") + item.value(QStringLiteral("name")).toString();
        entry.category = item.value(QStringLiteral("category")).toString();
        entry.summary = item.value(QStringLiteral("summary")).toString();
        entry.section = item.value(QStringLiteral("section")).toString();
        entry.snippet = item.value(QStringLiteral("snippet")).toString();
        entry.tooltip = tooltip(item);
        const bool inlineForm = item.value(QStringLiteral("forms")).toArray().contains(QStringLiteral("inline"));
        entry.block = !inlineForm || entry.snippet.contains(QLatin1Char('\n')) || entry.snippet.endsWith(QLatin1Char(':'));
        m_entries.append(entry);
    }
    // Short forms: those that stand at the start of a line take whole lines.
    for (const QJsonValue &value : json.value(QStringLiteral("short_forms")).toArray()) {
        const QJsonObject item = value.toObject();
        Entry entry;
        entry.label = item.value(QStringLiteral("form")).toString();
        entry.category = item.value(QStringLiteral("category")).toString();
        entry.summary = item.value(QStringLiteral("summary")).toString();
        entry.section = item.value(QStringLiteral("section")).toString();
        entry.snippet = item.value(QStringLiteral("snippet")).toString();
        entry.tooltip = tooltip(item);
        entry.block = item.value(QStringLiteral("where")).toString() == QStringLiteral("line");
        m_entries.append(entry);
    }
    // Closing markers: not in the menu or the palette (category "closing" has no title),
    // only for hints of |end… lines.
    for (const QJsonValue &value : json.value(QStringLiteral("closings")).toArray()) {
        const QJsonObject item = value.toObject();
        Entry entry;
        entry.label = item.value(QStringLiteral("form")).toString();
        entry.category = QStringLiteral("closing");
        entry.summary = item.value(QStringLiteral("summary")).toString();
        entry.section = item.value(QStringLiteral("section")).toString();
        entry.snippet = entry.label;
        entry.tooltip = tooltip(item);
        entry.block = true;
        m_entries.append(entry);
    }
    // Functions of expressions (14.13): an older translator gives none.
    m_functionCategories.clear();
    for (const QJsonValue &value : json.value(QStringLiteral("function_categories")).toArray())
        m_functionCategories.append({QStringLiteral("fn:") + value.toObject().value(QStringLiteral("id")).toString(),
                                     value.toObject().value(QStringLiteral("title")).toString()});
    for (const QJsonValue &value : json.value(QStringLiteral("functions")).toArray()) {
        const QJsonObject item = value.toObject();
        Entry entry;
        entry.function = true;
        entry.name = item.value(QStringLiteral("name")).toString();
        entry.module = item.value(QStringLiteral("module")).toString();
        entry.receiver = item.value(QStringLiteral("receiver")).toString();
        entry.signature = item.value(QStringLiteral("signature")).toString();
        entry.where = item.value(QStringLiteral("where")).toString();
        entry.label = !entry.module.isEmpty() ? QStringLiteral("math.") + entry.name
                      : !entry.receiver.isEmpty() ? entry.receiver + QLatin1Char('.') + entry.name
                                                  : entry.name;
        entry.category = QStringLiteral("fn:") + item.value(QStringLiteral("category")).toString();
        entry.summary = item.value(QStringLiteral("summary")).toString();
        const QString section = item.value(QStringLiteral("section")).toString();
        entry.section = item.value(QStringLiteral("doc")).toString() == QStringLiteral("stdlib")
                            ? QStringLiteral("stdlib:") + section : section;
        // A method is inserted after the point the author has typed: without the receiver.
        QJsonObject call = item;
        if (!entry.receiver.isEmpty()) call.insert(QStringLiteral("module"), QString());
        entry.snippet = functionSnippet(call);
        entry.tooltip = functionTooltip(item, entry.section);
        m_entries.append(entry);
    }
    // Header keys (14.14): an older translator gives none.
    m_headerKeys.clear();
    for (const QJsonValue &value : json.value(QStringLiteral("header_keys")).toArray()) {
        const QJsonObject item = value.toObject();
        HeaderKey key;
        key.path = item.value(QStringLiteral("path")).toString();
        for (const QJsonValue &kind : item.value(QStringLiteral("kinds")).toArray()) key.kinds << kind.toString();
        key.type = item.value(QStringLiteral("type")).toString();
        for (const QJsonValue &v : item.value(QStringLiteral("values")).toArray()) key.values << v.toString();
        key.closed = item.value(QStringLiteral("closed")).toBool();
        key.recommended = item.value(QStringLiteral("recommended")).toBool();
        key.section = item.value(QStringLiteral("section")).toString();
        key.summary = item.value(QStringLiteral("summary")).toString();
        key.example = item.value(QStringLiteral("example")).toString();
        m_headerKeys.append(key);
    }
    if (m_entries.isEmpty() || m_categories.isEmpty()) {
        m_entries.clear();
        if (error) *error = Text::tr("The catalogue of constructs is empty.");
        return false;
    }
    m_baseEntries = int(m_entries.size());
    m_baseCategories = int(m_categories.size());
    applyLibrary();
    return true;
}

bool CommandCatalog::setLibraryCommands(const QJsonArray &commands, const QString &baseDir)
{
    if (commands == m_library && baseDir == m_libraryBase) return false;
    m_library = commands;
    m_libraryBase = baseDir;
    if (!isLoaded()) return true;   // applied by setJson() later
    applyLibrary();
    return true;
}

void CommandCatalog::applyLibrary()
{
    // Drop the previous library part (it is always the tail), then append the current one.
    while (m_entries.size() > m_baseEntries) m_entries.removeLast();
    while (m_categories.size() > m_baseCategories) m_categories.removeLast();
    for (const QJsonValue &value : m_library) {
        const QJsonObject item = value.toObject();
        const QString name = item.value(QStringLiteral("name")).toString();
        if (name.isEmpty()) continue;
        // One category per module: the namespace, or the file name for names imported one by one.
        const QString module = QFileInfo(item.value(QStringLiteral("file")).toString()).fileName().section(QLatin1Char('.'), 0, 0);
        const QString categoryId = QStringLiteral("lib:") + module;
        bool known = false;
        for (const Category &category : m_categories) known = known || category.id == categoryId;
        if (!known) m_categories.append({categoryId, Text::tr("Library: %1").arg(module)});
        Entry entry;
        entry.library = true;
        entry.label = QStringLiteral("|") + name;
        entry.category = categoryId;
        entry.summary = item.value(QStringLiteral("summary")).toString();
        entry.snippet = item.value(QStringLiteral("snippet")).toString();
        entry.name = name;
        entry.signature = QStringLiteral("|") + name + item.value(QStringLiteral("signature")).toString()
                                                           .mid(item.value(QStringLiteral("macro")).toString().size());
        entry.source = QDir(m_libraryBase).absoluteFilePath(item.value(QStringLiteral("file")).toString());
        entry.line = item.value(QStringLiteral("line")).toInt();
        // A command may be called with a body {…} or as an environment only when its macro takes one.
        const QString body = item.value(QStringLiteral("body")).toString();
        QString argumentLines;
        for (const QJsonValue &param : item.value(QStringLiteral("params")).toArray()) {
            const QString text = param.toObject().value(QStringLiteral("summary")).toString();
            if (!text.isEmpty())
                argumentLines += QStringLiteral("\n  ") + param.toObject().value(QStringLiteral("name")).toString()
                                 + QStringLiteral(" — ") + text;
        }
        entry.tooltip = entry.signature + (entry.summary.isEmpty() ? QString() : QLatin1Char('\n') + entry.summary)
                        + argumentLines
                        + (body == QStringLiteral("required") ? QLatin1Char('\n') + Text::tr("The call needs a body: {…}") : QString())
                        + QLatin1Char('\n') + Text::tr("Defined in %1, line %2").arg(QFileInfo(entry.source).fileName()).arg(entry.line);
        m_entries.append(entry);
    }
}
