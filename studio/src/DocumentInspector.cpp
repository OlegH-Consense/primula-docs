#include "DocumentInspector.h"

#include "Translator.h"

#include <QDir>
#include <QFile>
#include <QJsonDocument>
#include <QProcess>
#include <QTemporaryDir>

DocumentInspector::DocumentInspector(QObject *parent) : QObject(parent)
{
    m_process = new QProcess(this);
    connect(m_process, &QProcess::errorOccurred, this, [this](QProcess::ProcessError error) {
        if (error != QProcess::FailedToStart) return;
        emit finished(m_document, {}, tr("Cannot start the translator: %1").arg(m_process->errorString()));
        if (m_hasPending) {
            m_hasPending = false;
            start(m_pending);
        }
    });
    connect(m_process, qOverload<int, QProcess::ExitStatus>(&QProcess::finished), this,
            [this](int, QProcess::ExitStatus status) {
        QJsonParseError parse{};
        const QJsonDocument json = QJsonDocument::fromJson(m_process->readAllStandardOutput(), &parse);
        // A newer request makes this result obsolete: skip it and run the newer one.
        if (m_hasPending) {
            m_hasPending = false;
            start(m_pending);
            return;
        }
        if (status != QProcess::NormalExit || !json.isObject())
            emit finished(m_document, {}, status != QProcess::NormalExit ? tr("The translator stopped abnormally.")
                                                                         : tr("The translator output is not JSON."));
        else
            emit finished(m_document, json.object(), QString());
    });
}

DocumentInspector::~DocumentInspector()
{
    cancel();
    delete m_buffers;
}

void DocumentInspector::request(const QString &root, const QString &document, const QHash<QString, QString> &buffers,
                                const QStringList &extra)
{
    const Request next{root, document, buffers, extra};
    if (isRunning()) {
        m_pending = next;
        m_hasPending = true;
        return;
    }
    start(next);
}

void DocumentInspector::cancel()
{
    m_hasPending = false;
    if (isRunning()) {
        m_process->blockSignals(true);
        m_process->kill();
        m_process->waitForFinished(1000);
        m_process->blockSignals(false);
    }
}

bool DocumentInspector::isRunning() const
{
    return m_process->state() != QProcess::NotRunning;
}

void DocumentInspector::start(const Request &request)
{
    m_document = request.document;
    const QString program = Translator::program();
    if (program.isEmpty()) {
        emit finished(m_document, {}, tr("The translator is not found."));
        return;
    }
    const QDir root(request.root);
    QStringList arguments{QStringLiteral("check"), root.relativeFilePath(request.document),
                          QStringLiteral("--dump-structure"), QStringLiteral("--dump-styles")};
    arguments << request.extra;
    if (!request.buffers.isEmpty()) {
        if (!m_buffers || !m_buffers->isValid()) {
            delete m_buffers;
            m_buffers = new QTemporaryDir(QDir::temp().filePath(QStringLiteral("primula-studio-XXXXXX")));
        }
        int index = 0;
        for (auto it = request.buffers.cbegin(); it != request.buffers.cend(); ++it) {
            // A plain write: the buffer name has no '=' (the translator splits FILE=BUFFER at the last '=').
            const QString buffer = QDir(m_buffers->path()).filePath(QStringLiteral("buffer-%1.prml").arg(index++));
            QFile file(buffer);
            if (!file.open(QIODevice::WriteOnly | QIODevice::Truncate) || file.write(it.value().toUtf8()) < 0)
                continue;   // the saved file is checked instead
            arguments << QStringLiteral("--overlay") << QStringLiteral("%1=%2").arg(it.key(), buffer);
        }
    }
    m_process->setWorkingDirectory(request.root);
    m_process->start(program, arguments);
}
