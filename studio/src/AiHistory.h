#pragma once
#include <QDateTime>
#include <QString>

struct AiExchange
{
    QString task;
    QString response;
    QString prompt;
    QString documentPath;
    QString scope;
    QString backend = QStringLiteral("codex-exec");
    QDateTime receivedAt;
};

namespace AiHistory {
/// Serialize task, response and exact prompt as a readable Markdown archive; return its UTF-8 text representation.
QString markdown(const AiExchange &exchange);
/// Create a unique timestamped archive in directory (beside the source document when empty);
/// return its path or empty with error.
QString save(const AiExchange &exchange, const QString &directory, QString *error);
/// Atomically write an exchange to explicit path; return false with error on failure.
bool saveCopy(const QString &path, const AiExchange &exchange, QString *error);
/// Parse a Studio archive into exchange; return false with error for unrelated/malformed files.
bool load(const QString &path, AiExchange *exchange, QString *error);
/// Wrap arbitrary text using a fence longer than embedded backticks so the archive remains valid Markdown.
QString fenced(const QString &text);
}
