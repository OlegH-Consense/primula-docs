#include "AiCompare.h"

#include <QCoreApplication>
#include <QHash>
#include <QRegularExpression>

namespace AiCompare {

QString normalize(const QString &text)
{
    return text.simplified();
}

QList<QList<Verdict>> compare(const QList<Answer> &answers)
{
    // Per answer: normalized ORIGINAL -> the replacement of its first edit for that place.
    QList<QHash<QString, QString>> byPlace;
    for (const Answer &answer : answers) {
        QHash<QString, QString> places;
        for (const AiEdit &edit : answer.edits)
            if (!places.contains(normalize(edit.original))) places.insert(normalize(edit.original), edit.replacement);
        byPlace.append(places);
    }
    QList<QList<Verdict>> result;
    for (int a = 0; a < answers.size(); ++a) {
        QList<Verdict> verdicts;
        for (const AiEdit &edit : answers.at(a).edits) {
            Verdict verdict;
            verdict.total = int(answers.size());
            verdict.present = 1;
            verdict.agreeing = 1;
            const QString key = normalize(edit.original);
            bool allEqual = true;
            for (int b = 0; b < answers.size(); ++b) {
                if (b == a || !byPlace.at(b).contains(key)) continue;
                const QString other = byPlace.at(b).value(key);
                verdict.others.append({answers.at(b).tool, other});
                ++verdict.present;
                if (normalize(other) == normalize(edit.replacement)) ++verdict.agreeing;
                else allEqual = false;
            }
            if (verdict.total < 2) verdict.kind = Kind::Single;
            else if (!allEqual) verdict.kind = Kind::Differ;
            else verdict.kind = verdict.present == verdict.total ? Kind::Agree : Kind::Partial;
            verdicts.append(verdict);
        }
        result.append(verdicts);
    }
    return result;
}

QString summary(const QList<Verdict> &verdicts)
{
    int agree = 0, differ = 0, partial = 0;
    for (const Verdict &verdict : verdicts) {
        agree += verdict.kind == Kind::Agree;
        differ += verdict.kind == Kind::Differ;
        partial += verdict.kind == Kind::Partial;
    }
    if (verdicts.isEmpty() || verdicts.first().kind == Kind::Single) return {};
    return QCoreApplication::translate("AiCompare", "Compared with the other tools: %1 of %2 agree, %3 differ, %4 are in some answers only.")
        .arg(agree).arg(verdicts.size()).arg(differ).arg(partial);
}

namespace {

QString escape(const QString &text)
{
    return text.toHtmlEscaped();
}

} // namespace

QString diffHtml(const QString &from, const QString &to)
{
    // Words with the whitespace after them are the tokens; the longest common subsequence keeps the common ones.
    static const QRegularExpression token(QStringLiteral(R"(\S+\s*)"));
    auto split = [](const QString &text) {
        QStringList parts;
        for (QRegularExpressionMatchIterator it = token.globalMatch(text); it.hasNext();) parts << it.next().captured();
        return parts;
    };
    const QStringList a = split(from), b = split(to);
    const int n = int(a.size()), m = int(b.size());
    QList<QList<int>> lcs(n + 1, QList<int>(m + 1, 0));
    auto same = [&](int i, int j) { return a.at(i).trimmed() == b.at(j).trimmed(); };
    for (int i = n - 1; i >= 0; --i)
        for (int j = m - 1; j >= 0; --j)
            lcs[i][j] = same(i, j) ? lcs[i + 1][j + 1] + 1 : qMax(lcs[i + 1][j], lcs[i][j + 1]);
    QString html;
    int i = 0, j = 0;
    while (i < n || j < m) {
        if (i < n && j < m && same(i, j)) {
            html += escape(b.at(j));
            ++i; ++j;
        } else if (j < m && (i == n || lcs[i][j + 1] >= lcs[i + 1][j])) {
            html += QStringLiteral("<ins style=\"background:#d4f4d4\">%1</ins>").arg(escape(b.at(j)));
            ++j;
        } else {
            html += QStringLiteral("<del style=\"background:#f8d0d0\">%1</del>").arg(escape(a.at(i)));
            ++i;
        }
    }
    return html;
}

} // namespace AiCompare
