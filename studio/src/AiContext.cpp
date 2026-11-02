#include "AiContext.h"

#include "CommandCatalog.h"

#include <QFile>
#include <QJsonObject>
#include <QRegularExpression>

namespace {

/// The built-in copy of a help document (resources.qrc), empty when it is missing.
QString resourceText(const QString &path)
{
    QFile file(path);
    return file.open(QIODevice::ReadOnly) ? QString::fromUtf8(file.readAll()) : QString();
}

QString specificationText() { return resourceText(QStringLiteral(":/help/primula-spec.ru.md")); }
QString libraryText() { return resourceText(QStringLiteral(":/help/primula-stdlib.ru.md")); }

/// " [§ 6.8]" or " [§ stdlib 3]": the section in the prompt, independent of the interface language.
QString sectionMark(const QString &section)
{
    if (section.isEmpty()) return {};
    return section.startsWith(QStringLiteral("stdlib:")) ? QStringLiteral(" [§ stdlib %1]").arg(section.mid(7))
                                                          : QStringLiteral(" [§ %1]").arg(section);
}

} // namespace

QString AiContext::reference(const CommandCatalog &catalog)
{
    if (!catalog.isLoaded()) return {};
    QString text = QStringLiteral("### Constructs (spelling — summary [§ specification section])\n");
    for (const CommandCatalog::Category &category : catalog.categories()) {
        QStringList lines;
        for (const CommandCatalog::Entry &entry : catalog.entries())
            if (!entry.function && entry.category == category.id)
                lines << QStringLiteral("- `%1` — %2%3").arg(entry.label, entry.summary, sectionMark(entry.section));
        if (!lines.isEmpty())
            text += QStringLiteral("\n#### ") + category.title + QLatin1Char('\n') + lines.join(QLatin1Char('\n')) + QLatin1Char('\n');
    }
    // Closing markers have no category title: listed apart so the model knows every |end form.
    QStringList closings;
    for (const CommandCatalog::Entry &entry : catalog.entries())
        if (entry.category == QStringLiteral("closing")) closings << QStringLiteral("`%1`").arg(entry.label);
    if (!closings.isEmpty())
        text += QStringLiteral("\n#### Closing markers\n") + closings.join(QStringLiteral(", ")) + QLatin1Char('\n');
    // Keys of the YAML header (14.14): path [kinds] — summary (type; values).
    if (!catalog.headerKeys().isEmpty()) {
        text += QStringLiteral("\n### YAML header keys (path [file kinds] — summary; * recommended)\n");
        for (const CommandCatalog::HeaderKey &key : catalog.headerKeys())
            text += QStringLiteral("- `%1`%2 [%3] — %4%5%6\n")
                        .arg(key.path, key.recommended ? QStringLiteral(" *") : QString(), key.kinds.join(QLatin1Char(',')),
                             key.summary, key.values.isEmpty() ? QString() : QStringLiteral(" (") + key.values.join(QStringLiteral(", ")) + QLatin1Char(')'),
                             sectionMark(key.section));
    }
    if (catalog.functionCategories().isEmpty()) return text;
    text += QStringLiteral("\n### Functions of expressions (signature — summary [§ section]; "
                           "where: styles = styles code only, cell = table formula only, project = project code only)\n");
    for (const CommandCatalog::Category &category : catalog.functionCategories()) {
        QStringList lines;
        for (const CommandCatalog::Entry &entry : catalog.entries()) {
            if (!entry.function || entry.category != category.id) continue;
            const QString where = entry.where.isEmpty() || entry.where == QStringLiteral("any")
                                      ? QString() : QStringLiteral(" (where: %1)").arg(entry.where);
            lines << QStringLiteral("- `%1` — %2%3%4").arg(entry.signature, entry.summary, where, sectionMark(entry.section));
        }
        if (!lines.isEmpty())
            text += QStringLiteral("\n#### ") + category.title + QLatin1Char('\n') + lines.join(QLatin1Char('\n')) + QLatin1Char('\n');
    }
    return text;
}

QString AiContext::section(const QString &markdown, const QString &number)
{
    // A heading "#… N. title"; the section ends at the next heading of its level or a higher one.
    const QRegularExpression heading(QStringLiteral("^(#{1,6}) %1\\. ").arg(QRegularExpression::escape(number)),
                                     QRegularExpression::MultilineOption);
    const QRegularExpressionMatch match = heading.match(markdown);
    if (!match.hasMatch()) return {};
    const int level = match.capturedLength(1);
    const QRegularExpression next(QStringLiteral("^#{1,%1} ").arg(level), QRegularExpression::MultilineOption);
    const QRegularExpressionMatch end = next.match(markdown, match.capturedEnd());
    const qsizetype stop = end.hasMatch() ? end.capturedStart() : markdown.size();
    return markdown.mid(match.capturedStart(), stop - match.capturedStart()).trimmed();
}

QStringList AiContext::parseSections(const QString &text)
{
    static const QRegularExpression valid(QStringLiteral("^(stdlib:)?\\d+(\\.\\d+)*$"));
    QStringList result;
    for (QString part : text.split(QRegularExpression(QStringLiteral("[,;\\s]+")), Qt::SkipEmptyParts)) {
        part = part.trimmed().remove(QRegularExpression(QStringLiteral("^§")));
        while (part.endsWith(QLatin1Char('.'))) part.chop(1);
        if (valid.match(part).hasMatch() && !result.contains(part)) result << part;
    }
    return result;
}

QString AiContext::sections(const QStringList &references)
{
    QString spec;
    QString library;
    QStringList parts;
    for (const QString &reference : references) {
        const bool stdlib = reference.startsWith(QStringLiteral("stdlib:"));
        QString &source = stdlib ? library : spec;
        if (source.isEmpty()) source = stdlib ? libraryText() : specificationText();
        const QString number = stdlib ? reference.mid(7) : reference;
        const QString title = stdlib ? QStringLiteral("Standard library, section %1").arg(number)
                                     : QStringLiteral("Specification, section %1").arg(number);
        const QString body = section(source, number);
        parts << QStringLiteral("## %1\n\n%2").arg(title, body.isEmpty() ? QStringLiteral("(no such section)") : body);
    }
    return parts.join(QStringLiteral("\n\n"));
}

QString AiContext::rules()
{
    const QString skill = resourceText(QStringLiteral(":/ai/primula-docs-skill.md"));
    QStringList parts;
    for (const QString &number : {QStringLiteral("4"), QStringLiteral("5"), QStringLiteral("7")}) {
        const QString text = section(skill, number);
        if (!text.isEmpty()) parts << text;
    }
    return parts.join(QStringLiteral("\n\n"));
}

QString AiContext::fullSpecification()
{
    return QStringLiteral("## Language specification\n\n") + specificationText()
           + QStringLiteral("\n\n## Standard library\n\n") + libraryText();
}

QString AiContext::messages(const QJsonArray &messages)
{
    QStringList lines;
    for (const QJsonValue &value : messages) {
        const QJsonObject message = value.toObject();
        QString place = message.value(QStringLiteral("file")).toString();
        const int line = message.value(QStringLiteral("line")).toInt();
        const int column = message.value(QStringLiteral("column")).toInt();
        if (line > 0) place += QStringLiteral(":%1").arg(line) + (column > 0 ? QStringLiteral(":%1").arg(column) : QString());
        lines << QStringLiteral("%1: %2 [%3] %4").arg(place.isEmpty() ? QStringLiteral("-") : place,
                                                     message.value(QStringLiteral("severity")).toString(),
                                                     message.value(QStringLiteral("code")).toString(),
                                                     message.value(QStringLiteral("message")).toString());
        for (const QJsonValue &note : message.value(QStringLiteral("notes")).toArray())
            lines << QStringLiteral("    note: ") + note.toObject().value(QStringLiteral("message")).toString();
    }
    return lines.join(QLatin1Char('\n'));
}
