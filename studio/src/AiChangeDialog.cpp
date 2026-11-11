#include "AiChangeDialog.h"

#include "Backups.h"

#include <QComboBox>
#include <QDir>
#include <QFile>
#include <QFileInfo>
#include <QHBoxLayout>
#include <QLabel>
#include <QListWidget>
#include <QMessageBox>
#include <QPlainTextEdit>
#include <QPushButton>
#include <QSplitter>
#include <QStackedWidget>
#include <QStandardPaths>
#include <QTimer>
#include <QVBoxLayout>

namespace {

constexpr qint64 kMaxSentFile = 100 * 1024;
constexpr qint64 kMaxSentTotal = 600 * 1024;

QByteArray readFile(const QString &path)
{
    QFile file(path);
    return file.open(QIODevice::ReadOnly) ? file.readAll() : QByteArray();
}

} // namespace

AiChangeDialog::AiChangeDialog(const AiRequest &context, const QString &projectRoot, QWidget *parent)
    : QDialog(parent), m_context(context), m_root(projectRoot)
{
    setObjectName(QStringLiteral("aiChangeDialog"));
    setWindowTitle(tr("Change the project with AI"));
    resize(980, 700);
    m_backend = new CliAgentBackend(this);
    connect(m_backend, &IAiBackend::finished, this, [this](bool ok, const QString &response, const QString &error) {
        finished(ok, response, error);
    });
    m_clock = new QTimer(this);
    m_clock->setInterval(1000);
    connect(m_clock, &QTimer::timeout, this, [this] {
        ++m_seconds;
        m_progress->setText(tr("The tool is working: %1 s. Your project is not touched.").arg(m_seconds));
    });
    buildUi();
}

AiChangeDialog::~AiChangeDialog()
{
    if (m_backend->isRunning()) {
        m_backend->disconnect(this);
        m_backend->cancel();
    }
}

void AiChangeDialog::buildUi()
{
    auto *layout = new QVBoxLayout(this);
    m_pages = new QStackedWidget(this);
    layout->addWidget(m_pages, 1);

    auto *input = new QWidget(m_pages);
    auto *form = new QVBoxLayout(input);
    auto *intro = new QLabel(tr("Describe the change: what to add, rewrite, rename or remove in the project. The tool answers with the "
                                "new text of the files; you see the differences and the check of the translator before anything "
                                "changes in your project."), input);
    intro->setWordWrap(true);
    form->addWidget(intro);
    m_task = new QPlainTextEdit(input);
    m_task->setObjectName(QStringLiteral("aiChangeTask"));
    m_task->setPlaceholderText(tr("For example: add an appendix with the table of goods to the contract and a build target for it; "
                                  "move the payment terms to a fragment."));
    form->addWidget(m_task, 1);
    auto *toolRow = new QHBoxLayout;
    toolRow->addWidget(new QLabel(tr("Tool:"), input));
    m_tools = new QComboBox(input);
    m_tools->setObjectName(QStringLiteral("aiChangeTool"));
    for (const AiAgent &agent : AiAgents::all())
        if (!QStandardPaths::findExecutable(AiAgents::program(agent)).isEmpty()) m_tools->addItem(agent.name, agent.id);
    toolRow->addWidget(m_tools);
    toolRow->addStretch();
    form->addLayout(toolRow);
    m_filesLabel = new QLabel(input);
    m_filesLabel->setObjectName(QStringLiteral("aiChangeFilesLabel"));
    m_filesLabel->setWordWrap(true);
    form->addWidget(m_filesLabel);
    m_files = new QListWidget(input);
    m_files->setObjectName(QStringLiteral("aiChangeFiles"));
    form->addWidget(m_files, 2);
    auto *inputButtons = new QHBoxLayout;
    inputButtons->addStretch();
    m_start = new QPushButton(tr("Change with AI"), input);
    m_start->setObjectName(QStringLiteral("aiChangeStart"));
    auto *cancel = new QPushButton(tr("Cancel"), input);
    inputButtons->addWidget(m_start);
    inputButtons->addWidget(cancel);
    form->addLayout(inputButtons);
    m_pages->addWidget(input);

    auto *work = new QWidget(m_pages);
    auto *workLayout = new QVBoxLayout(work);
    workLayout->addStretch();
    m_progress = new QLabel(work);
    m_progress->setObjectName(QStringLiteral("aiChangeProgress"));
    m_progress->setAlignment(Qt::AlignCenter);
    workLayout->addWidget(m_progress);
    auto *stop = new QPushButton(tr("Stop"), work);
    workLayout->addWidget(stop, 0, Qt::AlignCenter);
    workLayout->addStretch();
    m_pages->addWidget(work);

    auto *result = new QWidget(m_pages);
    auto *resultLayout = new QVBoxLayout(result);
    auto *splitter = new QSplitter(Qt::Horizontal, result);
    m_list = new QListWidget(splitter);
    m_list->setObjectName(QStringLiteral("aiChangeList"));
    m_diff = new QPlainTextEdit(splitter);
    m_diff->setObjectName(QStringLiteral("aiChangeDiff"));
    m_diff->setReadOnly(true);
    m_diff->setLineWrapMode(QPlainTextEdit::NoWrap);
    splitter->setStretchFactor(0, 1);
    splitter->setStretchFactor(1, 3);
    resultLayout->addWidget(splitter, 1);
    m_summary = new QLabel(result);
    m_summary->setObjectName(QStringLiteral("aiChangeSummary"));
    m_summary->setWordWrap(true);
    resultLayout->addWidget(m_summary);
    m_answerView = new QPlainTextEdit(result);
    m_answerView->setObjectName(QStringLiteral("aiChangeAnswer"));
    m_answerView->setReadOnly(true);
    m_answerView->setMaximumHeight(100);
    resultLayout->addWidget(m_answerView);
    auto *resultButtons = new QHBoxLayout;
    m_fix = new QPushButton(tr("Ask the tool to fix the errors"), result);
    m_fix->setObjectName(QStringLiteral("aiChangeFix"));
    m_apply = new QPushButton(tr("Apply the chosen changes"), result);
    m_apply->setObjectName(QStringLiteral("aiChangeApply"));
    auto *more = new QPushButton(tr("Add to the task"), result);
    auto *close = new QPushButton(tr("Close"), result);
    resultButtons->addWidget(m_fix);
    resultButtons->addWidget(m_apply);
    resultButtons->addStretch();
    resultButtons->addWidget(more);
    resultButtons->addWidget(close);
    resultLayout->addLayout(resultButtons);
    m_pages->addWidget(result);

    fillFiles();
    connect(m_task, &QPlainTextEdit::textChanged, this, [this] { updateButtons(); });
    connect(m_files, &QListWidget::itemChanged, this, [this] { updateFilesLabel(); updateButtons(); });
    connect(m_start, &QPushButton::clicked, this, [this] {
        QString error;
        if (!startRun(&error)) QMessageBox::warning(this, tr("Change the project with AI"), error);
    });
    connect(cancel, &QPushButton::clicked, this, &QDialog::reject);
    connect(stop, &QPushButton::clicked, this, [this] {
        m_cancelled = true;
        m_backend->cancel();
    });
    connect(m_list, &QListWidget::currentRowChanged, this, [this] { showDiff(); });
    connect(m_list, &QListWidget::itemChanged, this, [this] { updateButtons(); });
    connect(m_fix, &QPushButton::clicked, this, [this] {
        QString error;
        if (!fixErrors(&error)) QMessageBox::warning(this, tr("Change the project with AI"), error);
    });
    connect(m_apply, &QPushButton::clicked, this, [this] {
        if (m_after.errors > m_before.errors &&
            QMessageBox::question(this, tr("Change the project with AI"),
                                  tr("The changed project has more errors (%1) than the project had (%2). Apply anyway?")
                                      .arg(m_after.errors).arg(m_before.errors)) != QMessageBox::Yes)
            return;
        accept();
    });
    connect(more, &QPushButton::clicked, this, [this] { m_pages->setCurrentIndex(0); });
    connect(close, &QPushButton::clicked, this, &QDialog::reject);
    updateFilesLabel();
    updateButtons();
}

void AiChangeDialog::fillFiles()
{
    // The text files of the project; the ones that are sent by default: the project file and the Primula files, within the budget.
    const QDir root(m_root);
    QStringList files = Backups::sourceFiles(m_root);
    std::sort(files.begin(), files.end(), [&](const QString &a, const QString &b) {
        auto rank = [&](const QString &p) { return root.relativeFilePath(p) == QStringLiteral("project.p.prml") ? 0 : p.endsWith(QStringLiteral(".prml")) ? 1 : 2; };
        return rank(a) != rank(b) ? rank(a) < rank(b) : a < b;
    });
    qint64 total = 0;
    const QSignalBlocker blocker(m_files);
    for (const QString &path : files) {
        const qint64 size = QFileInfo(path).size();
        const QString relative = root.relativeFilePath(path);
        auto *item = new QListWidgetItem(QStringLiteral("%1  (%2 KB)").arg(relative).arg((size + 1023) / 1024), m_files);
        item->setData(Qt::UserRole, relative);
        item->setFlags(item->flags() | Qt::ItemIsUserCheckable);
        const bool primula = relative.endsWith(QStringLiteral(".prml"));
        const bool send = primula && size <= kMaxSentFile && total + size <= kMaxSentTotal;
        if (send) total += size;
        item->setCheckState(send ? Qt::Checked : Qt::Unchecked);
    }
}

QStringList AiChangeDialog::sentFiles() const
{
    QStringList paths;
    for (int row = 0; row < m_files->count(); ++row)
        if (m_files->item(row)->checkState() == Qt::Checked) paths << m_files->item(row)->data(Qt::UserRole).toString();
    return paths;
}

void AiChangeDialog::setFileSent(const QString &path, bool sent)
{
    for (int row = 0; row < m_files->count(); ++row)
        if (m_files->item(row)->data(Qt::UserRole).toString() == path) m_files->item(row)->setCheckState(sent ? Qt::Checked : Qt::Unchecked);
}

void AiChangeDialog::updateFilesLabel()
{
    qint64 total = 0;
    for (const QString &path : sentFiles()) total += QFileInfo(QDir(m_root).filePath(path)).size();
    m_filesLabel->setText(tr("These files are sent to the service of the chosen tool (%1 KB). The list of all files of the project is sent too; "
                             "the files you do not tick keep their text to yourself.").arg((total + 1023) / 1024));
}

void AiChangeDialog::updateButtons()
{
    m_start->setEnabled(m_tools->count() > 0 && !m_task->toPlainText().trimmed().isEmpty());
    m_start->setToolTip(m_tools->count() == 0 ? tr("No AI tool is installed (File → Settings).") : QString());
    if (m_list) {
        int chosen = 0;
        for (int row = 0; row < m_list->count(); ++row) chosen += m_list->item(row)->checkState() == Qt::Checked;
        m_apply->setEnabled(chosen > 0);
        m_fix->setEnabled(m_after.errors > 0);
    }
}

void AiChangeDialog::setTask(const QString &task) { m_task->setPlainText(task); }

bool AiChangeDialog::setTool(const QString &id)
{
    const int index = m_tools->findData(id);
    if (index < 0) return false;
    m_tools->setCurrentIndex(index);
    return true;
}

bool AiChangeDialog::isRunning() const { return m_backend->isRunning(); }

QByteArray AiChangeDialog::currentText(const QString &path) const
{
    const auto it = m_proposed.constFind(path);
    if (it != m_proposed.constEnd()) return it->remove ? QByteArray() : it->data;
    return readFile(QDir(m_root).filePath(path));
}

bool AiChangeDialog::startRun(QString *error)
{
    if (m_tools->count() == 0 || m_task->toPlainText().trimmed().isEmpty()) {
        if (error) *error = tr("Describe the change and choose a tool.");
        return false;
    }
    m_work = std::make_unique<QTemporaryDir>(QDir::temp().filePath(QStringLiteral("primula-ai-XXXXXX")));
    if (!m_work->isValid()) {
        if (error) *error = tr("Cannot make a temporary directory: %1").arg(m_work->errorString());
        return false;
    }
    QString failure;
    if (!AiProject::mirror(m_root, m_work->path(), &failure)) {
        if (error) *error = failure;
        return false;
    }
    m_proposed.clear();
    m_changes.clear();
    m_problems.clear();
    m_after = {};
    m_haveBaseline = false;
    begin(m_task->toPlainText().trimmed(), sentFiles(), false);
    if (!m_backend->isRunning()) {
        if (error) *error = tr("The tool could not be started: %1").arg(AiAgents::program(m_agent));
        m_pages->setCurrentIndex(0);
        return false;
    }
    return true;
}

void AiChangeDialog::begin(const QString &task, const QStringList &paths, bool fix)
{
    m_agent = AiAgents::byId(m_tools->currentData().toString());
    AiRequest request = m_context;
    request.task = task;
    request.createProject = true;
    request.filesInAnswer = true;
    request.changeProject = true;
    request.projectDirectory = m_work->path();
    request.proposeEdits = false;
    // The list of all files of the project, then the sent ones (in the state they have now: after the changes of a fix round).
    QStringList all;
    for (const QString &path : Backups::sourceFiles(m_root)) all << QDir(m_root).relativeFilePath(path);
    for (auto it = m_proposed.begin(); it != m_proposed.end(); ++it)
        if (!it->remove && !all.contains(it.key())) all << it.key();
    all.sort();
    QString listing = QStringLiteral("PROJECT FILES:\n") + all.join(QLatin1Char('\n'));
    QString contents;
    for (const QString &path : paths) {
        if (fix && m_proposed.contains(path) && m_proposed.value(path).remove) continue;
        const QByteArray text = currentText(path);
        m_sent.insert(path, readFile(QDir(m_root).filePath(path)));
        contents += QStringLiteral("\n\n<<<<<<< FILE %1\n%2\n>>>>>>> END FILE").arg(path, QString::fromUtf8(text).trimmed());
    }
    if (fix)
        for (auto it = m_proposed.begin(); it != m_proposed.end(); ++it)
            if (!it->remove && !paths.contains(it.key()))
                contents += QStringLiteral("\n\n<<<<<<< FILE %1\n%2\n>>>>>>> END FILE").arg(it.key(), QString::fromUtf8(it->data).trimmed());
    request.fragments = listing + contents;
    m_cancelled = false;
    m_seconds = 0;
    m_progress->setText(tr("The tool is working: %1 s. Your project is not touched.").arg(0));
    m_pages->setCurrentIndex(1);
    m_clock->start();
    m_backend->start(request, m_agent);
}

bool AiChangeDialog::fixErrors(QString *error)
{
    if (m_after.errors == 0 || !m_work) {
        if (error) *error = tr("There are no errors to fix.");
        return false;
    }
    QStringList errors;
    for (const QString &line : m_after.lines)
        if (errors.size() < 40) errors << line;
    QStringList paths = sentFiles();
    for (const QString &path : m_proposed.keys())
        if (!paths.contains(path) && !m_proposed.value(path).remove) paths << path;
    begin(tr("The project below was changed and the translator found errors (the changed files are in their new state). Fix them; answer with the blocks of the files "
             "you change, each with its whole text.\nThe errors:\n%1").arg(errors.join(QLatin1Char('\n'))), paths, true);
    if (!m_backend->isRunning()) {
        if (error) *error = tr("The tool could not be started: %1").arg(AiAgents::program(m_agent));
        m_clock->stop();
        showResult();
        return false;
    }
    return true;
}

void AiChangeDialog::finished(bool success, const QString &response, const QString &errorMessage)
{
    m_clock->stop();
    if (!success) {
        const QString reason = m_cancelled ? tr("Stopped.") : (errorMessage.isEmpty() ? tr("The tool gave no answer.") : errorMessage);
        if (!m_changes.isEmpty()) {
            showResult();
            m_summary->setText(tr("The last request failed: %1").arg(reason) + QLatin1Char('\n') + m_summary->text());
        } else {
            m_pages->setCurrentIndex(0);
        }
        emit runFailed(reason);
        return;
    }
    // The baseline: the errors of the project as it is (the work directory has not changed yet).
    if (!m_haveBaseline) {
        m_before = AiProject::check(m_work->path());
        m_haveBaseline = true;
    }
    m_answer = AiProject::withoutFiles(response);
    QStringList problems;
    const QList<AiProject::File> parsed = AiProject::parseFiles(response, &problems);
    for (const AiProject::File &file : parsed) {
        if (!AiProject::changeAllowed(m_root, file.path)) {
            problems << tr("%1: the path is not allowed in this project (a link, hidden or unsafe)").arg(file.path);
            continue;
        }
        QString failure;
        if (!AiProject::putChange(m_work->path(), file, &failure)) {
            problems << failure;
            continue;
        }
        m_proposed.insert(file.path, file);
    }
    m_problems += problems;
    showResult();
}

void AiChangeDialog::showResult()
{
    m_changes.clear();
    for (auto it = m_proposed.begin(); it != m_proposed.end(); ++it) {
        const QByteArray before = readFile(QDir(m_root).filePath(it.key()));
        const bool existed = QFileInfo::exists(QDir(m_root).filePath(it.key()));
        if (it->remove && !existed) continue;
        if (!it->remove && existed && before == it->data) continue;   // the same text: no change
        Change change;
        change.path = it.key();
        change.before = before;
        change.after = it->remove ? QByteArray() : it->data;
        change.kind = it->remove ? Kind::Deleted : existed ? Kind::Changed : Kind::Added;
        m_changes.append(change);
    }
    m_after = m_changes.isEmpty() ? m_before : AiProject::check(m_work->path());
    const QSignalBlocker blocker(m_list);
    m_list->clear();
    for (const Change &change : m_changes) {
        const QString mark = change.kind == Kind::Added ? tr("new") : change.kind == Kind::Deleted ? tr("deleted") : tr("changed");
        auto *item = new QListWidgetItem(QStringLiteral("%1  [%2]").arg(change.path, mark), m_list);
        item->setData(Qt::UserRole, change.path);
        item->setFlags(item->flags() | Qt::ItemIsUserCheckable);
        item->setCheckState(Qt::Checked);
    }
    m_answerView->setPlainText(m_answer);
    QStringList lines;
    lines << (m_changes.isEmpty() ? tr("The tool proposed no changes.") : tr("%n file(s) changed.", nullptr, int(m_changes.size())));
    if (!m_changes.isEmpty()) {
        if (!m_after.ran) lines << tr("The check did not run: %1").arg(m_after.failure);
        else lines << tr("Errors of the translator: %1 in the project, %2 after the changes (warnings %3).").arg(m_before.errors).arg(m_after.errors).arg(m_after.warnings)
                          + (m_after.errors > 0 ? QLatin1Char('\n') + m_after.lines.mid(0, 5).join(QLatin1Char('\n')) : QString());
    }
    if (!m_problems.isEmpty()) lines << tr("Left out: %1").arg(m_problems.mid(0, 5).join(QStringLiteral("; ")));
    m_summary->setText(lines.join(QLatin1Char('\n')));
    m_pages->setCurrentIndex(2);
    if (m_list->count() > 0) m_list->setCurrentRow(0);
    showDiff();
    updateButtons();
    emit resultShown();
}

void AiChangeDialog::showDiff()
{
    const int row = m_list->currentRow();
    if (row < 0 || row >= m_changes.size()) {
        m_diff->clear();
        return;
    }
    const Change &change = m_changes.at(row);
    QString error;
    const QString diff = Backups::unifiedDiff(change.before, change.after, QStringLiteral("a/") + change.path,
                                              QStringLiteral("b/") + change.path, &error);
    m_diff->setPlainText(diff.isEmpty() ? (error.isEmpty() ? tr("(no differences)") : error) : diff);
}

void AiChangeDialog::setChangeChosen(const QString &path, bool chosen)
{
    for (int row = 0; row < m_list->count(); ++row)
        if (m_list->item(row)->data(Qt::UserRole).toString() == path) m_list->item(row)->setCheckState(chosen ? Qt::Checked : Qt::Unchecked);
}

QList<AiProject::File> AiChangeDialog::chosenChanges() const
{
    QList<AiProject::File> result;
    for (int row = 0; row < m_list->count() && row < m_changes.size(); ++row) {
        if (m_list->item(row)->checkState() != Qt::Checked) continue;
        const Change &change = m_changes.at(row);
        result.append({change.path, change.after, change.kind == Kind::Deleted});
    }
    return result;
}

void AiChangeDialog::reject()
{
    if (m_backend->isRunning()) {
        if (QMessageBox::question(this, tr("Change the project with AI"), tr("The tool is still working. Stop it and close?")) != QMessageBox::Yes)
            return;
        m_backend->disconnect(this);
        m_backend->cancel();
    }
    QDialog::reject();
}
