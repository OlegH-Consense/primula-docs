#include "AiHistory.h"
#include <QDir>
#include <QFile>
#include <QFileInfo>
#include <QJsonDocument>
#include <QJsonObject>
#include <QObject>
#include <QRegularExpression>
#include <QSaveFile>
#include <QUuid>

namespace {
// Markers of an archive: the metadata comment and the section comments. Primula Studio writes
// "primula-…"; archives of Studio 0.4 (ODT Markdown Kit) used "odtkit-…" and are still read.
const QString kHeader = QStringLiteral("<!-- primula-studio-ai ");
const QString kSection = QStringLiteral("primula-ai-");
const QString kOldHeader = QStringLiteral("<!-- odtkit-studio-ai ");
const QString kOldSection = QStringLiteral("odtkit-ai-");
}

QString AiHistory::fenced(const QString &text)
{
    int longest = 2;
    const auto matches = QRegularExpression(QStringLiteral("`+")).globalMatch(text);
    auto iterator = matches;
    while (iterator.hasNext()) longest = qMax(longest, int(iterator.next().capturedLength()));
    const QString fence(longest + 1, QLatin1Char('`'));
    return fence + QStringLiteral("text\n") + text + QLatin1Char('\n') + fence;
}

QString AiHistory::markdown(const AiExchange &exchange)
{
    QString id;
    do { id = QUuid::createUuid().toString(QUuid::WithoutBraces); }
    while (exchange.task.contains(id) || exchange.response.contains(id) || exchange.prompt.contains(id));
    const QJsonObject metadata{{QStringLiteral("version"), 1}, {QStringLiteral("id"), id},
        {QStringLiteral("received_at"), exchange.receivedAt.toString(Qt::ISODateWithMs)},
        {QStringLiteral("document"), QFileInfo(exchange.documentPath).fileName()},
        {QStringLiteral("scope"), exchange.scope}, {QStringLiteral("backend"), exchange.backend}};
    QString text = kHeader
        + QString::fromUtf8(QJsonDocument(metadata).toJson(QJsonDocument::Compact)) + QStringLiteral(" -->\n\n");
    text += QStringLiteral("# AI — ") + exchange.receivedAt.toString(Qt::ISODateWithMs) + QStringLiteral("\n\n");
    // Human-readable Markdown with exact sections; unique comment markers allow
    // reopening even when the response contains headings or fenced examples.
    auto section = [&text, &id](const QString &name, const QString &title, const QString &body) {
        text += QStringLiteral("## ") + title + QStringLiteral("\n\n<!-- ") + kSection + id + QLatin1Char('-')
            + name + QStringLiteral("-start -->\n") + body + QStringLiteral("\n<!-- ") + kSection + id
            + QLatin1Char('-') + name + QStringLiteral("-end -->\n\n");
    };
    section(QStringLiteral("task"), QObject::tr("Task"), fenced(exchange.task));
    section(QStringLiteral("response"), QObject::tr("Response"), exchange.response);
    section(QStringLiteral("prompt"), QObject::tr("Complete request"), fenced(exchange.prompt));
    return text;
}

bool AiHistory::saveCopy(const QString &path, const AiExchange &exchange, QString *error)
{
    QSaveFile file(path);
    const QByteArray content = markdown(exchange).toUtf8();
    if (!file.open(QIODevice::WriteOnly) || file.write(content) != content.size() || !file.commit()) {
        if (error) *error = QObject::tr("Cannot save AI exchange: %1").arg(file.errorString());
        return false;
    }
    return true;
}

QString AiHistory::save(const AiExchange &exchange, const QString &directory, QString *error)
{
    const QFileInfo document(exchange.documentPath);
    const QString base = document.completeBaseName() + QStringLiteral(".ai-")
        + exchange.receivedAt.toString(QStringLiteral("yyyyMMdd-HHmmss-zzz"));
    // Primula Studio keeps the history in .primula-studio/ai-history/ of the project.
    const QDir target(directory.isEmpty() ? document.absolutePath() : directory);
    if (!target.exists() && !QDir().mkpath(target.absolutePath())) {
        if (error) *error = QObject::tr("Cannot create AI history file: %1").arg(target.absolutePath());
        return {};
    }
    for (int index = 0; index < 10000; ++index) {
        const QString path = target.filePath(base
            + (index ? QStringLiteral("-%1").arg(index + 1) : QString()) + QStringLiteral(".md"));
        QFile reservation(path);
        if (!reservation.open(QIODevice::WriteOnly | QIODevice::NewOnly)) {
            if (QFileInfo::exists(path)) continue;
            if (error) *error = QObject::tr("Cannot create AI history file: %1").arg(reservation.errorString());
            return {};
        }
        reservation.close();
        if (saveCopy(path, exchange, error)) return path;
        reservation.remove();
        return {};
    }
    if (error) *error = QObject::tr("Cannot choose an unused AI history filename.");
    return {};
}

bool AiHistory::load(const QString &path, AiExchange *exchange, QString *error)
{
    QFile file(path);
    if (!file.open(QIODevice::ReadOnly)) {
        if (error) *error = file.errorString();
        return false;
    }
    const QString text = QString::fromUtf8(file.readAll());
    const bool old = text.startsWith(kOldHeader);
    const QString prefix = old ? kOldHeader : kHeader;
    const QString marker = old ? kOldSection : kSection;
    const int end = text.indexOf(QStringLiteral(" -->\n"));
    const QJsonObject metadata = text.startsWith(prefix) && end >= 0
        ? QJsonDocument::fromJson(text.mid(prefix.size(), end - prefix.size()).toUtf8()).object() : QJsonObject();
    const QString id = metadata.value(QStringLiteral("id")).toString();
    if (metadata.value(QStringLiteral("version")).toInt() != 1
        || !QRegularExpression(QStringLiteral("^[a-f0-9-]{36}$")).match(id).hasMatch()) {
        if (error) *error = QObject::tr("Unrecognized AI history file: %1").arg(path);
        return false;
    }
    auto section = [&text, &id, &marker](const QString &name, QString *body) {
        const QString start = QStringLiteral("<!-- ") + marker + id + QLatin1Char('-') + name + QStringLiteral("-start -->\n");
        const QString finish = QStringLiteral("\n<!-- ") + marker + id + QLatin1Char('-') + name + QStringLiteral("-end -->");
        const int first = text.indexOf(start);
        const int last = first < 0 ? -1 : text.indexOf(finish, first + start.size());
        if (first < 0 || last < 0) return false;
        *body = text.mid(first + start.size(), last - first - start.size());
        return true;
    };
    AiExchange result;
    auto unfence = [](QString *body) {
        const int newline = body->indexOf('\n');
        if (newline < 0 || !body->left(newline).endsWith(QStringLiteral("text"))) return false;
        const QString fence = body->left(newline - 4);
        if (fence.size() < 3 || !body->endsWith(QLatin1Char('\n') + fence)) return false;
        *body = body->mid(newline + 1, body->size() - newline - 2 - fence.size());
        return true;
    };
    if (!section(QStringLiteral("task"), &result.task) || !unfence(&result.task)
        || !section(QStringLiteral("response"), &result.response)
        || !section(QStringLiteral("prompt"), &result.prompt) || !unfence(&result.prompt)) {
        if (error) *error = QObject::tr("AI history sections are incomplete: %1").arg(path);
        return false;
    }
    result.receivedAt = QDateTime::fromString(metadata.value(QStringLiteral("received_at")).toString(), Qt::ISODateWithMs);
    const QString document = metadata.value(QStringLiteral("document")).toString();
    if (!result.receivedAt.isValid() || document.isEmpty() || QFileInfo(document).fileName() != document) {
        if (error) *error = QObject::tr("AI history metadata is invalid: %1").arg(path);
        return false;
    }
    result.documentPath = QFileInfo(path).absoluteDir().filePath(document);
    result.scope = metadata.value(QStringLiteral("scope")).toString();
    result.backend = metadata.value(QStringLiteral("backend")).toString();
    *exchange = result;
    return true;
}
