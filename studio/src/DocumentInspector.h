#pragma once

// Asynchronous structure and styles dumps of a document (stage 14.6).
//
// Runs `primula check DOC --dump-structure --dump-styles --overlay FILE=BUFFER…`
// (specification 14.1, Т1–Т3, decision 124): unsaved editor buffers are written
// to a private temporary directory and passed as overlays, so the panels follow
// the text being typed without saving it. Only one run at a time; a request made
// during a run replaces any earlier pending one and starts when the run ends.

#include <QHash>
#include <QJsonObject>
#include <QObject>
#include <QString>

class QProcess;
class QTemporaryDir;

class DocumentInspector : public QObject
{
    Q_OBJECT

public:
    explicit DocumentInspector(QObject *parent = nullptr);
    ~DocumentInspector() override;

    /// Ask for the dumps of a document.
    /// @param root  project root: the working directory of the translator.
    /// @param document  absolute path of the document (.prml, not a project file).
    /// @param buffers  unsaved texts by absolute file path; written as overlays.
    /// @param extra  more arguments of `check` (the build parameters of the document: --param N=V).
    void request(const QString &root, const QString &document, const QHash<QString, QString> &buffers,
                 const QStringList &extra = {});
    /// Stop a run and forget a pending request (closing the project).
    void cancel();
    bool isRunning() const;

signals:
    /// A run ended. dump is the translator JSON (schema, file, structure, styles, messages);
    /// structure/styles are null when that phase did not run. On a failure to start or
    /// unreadable output, dump is empty and errorMessage says why.
    void finished(const QString &document, const QJsonObject &dump, const QString &errorMessage);

private:
    struct Request {
        QString root;
        QString document;
        QHash<QString, QString> buffers;
        QStringList extra;
    };
    void start(const Request &request);

    QProcess *m_process = nullptr;
    QTemporaryDir *m_buffers = nullptr;
    QString m_document;
    Request m_pending;
    bool m_hasPending = false;
};
