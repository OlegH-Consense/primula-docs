#include "AiProjectDialog.h"

#include "AiProject.h"

#include <QCheckBox>
#include <QComboBox>
#include <QDialogButtonBox>
#include <QDir>
#include <QFileDialog>
#include <QFileInfo>
#include <QHBoxLayout>
#include <QLabel>
#include <QLineEdit>
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

bool isInstalled(const AiAgent &agent)
{
    return !QStandardPaths::findExecutable(AiAgents::program(agent)).isEmpty();
}

} // namespace

AiProjectDialog::AiProjectDialog(const AiRequest &context, const QString &defaultParent, QWidget *parent)
    : QDialog(parent), m_context(context), m_defaultParent(defaultParent)
{
    setObjectName(QStringLiteral("aiProjectDialog"));
    setWindowTitle(tr("Create a project with AI"));
    resize(900, 640);
    m_backend = new CliAgentBackend(this);
    connect(m_backend, &IAiBackend::finished, this, [this](bool ok, const QString &response, const QString &error) {
        finished(ok, response, error);
    });
    m_clock = new QTimer(this);
    m_clock->setInterval(1000);
    connect(m_clock, &QTimer::timeout, this, [this] {
        ++m_seconds;
        m_progress->setText(tr("The tool is working in a temporary directory: %1 s. Nothing is written to your files yet.").arg(m_seconds));
    });
    buildUi();
}

AiProjectDialog::~AiProjectDialog()
{
    if (m_backend->isRunning()) {
        m_backend->disconnect(this);
        m_backend->cancel();
    }
}

void AiProjectDialog::buildUi()
{
    auto *layout = new QVBoxLayout(this);
    m_pages = new QStackedWidget(this);
    layout->addWidget(m_pages, 1);

    // Page 0: the task.
    auto *input = new QWidget(m_pages);
    auto *form = new QVBoxLayout(input);
    form->addWidget(new QLabel(tr("Describe the project: what documents it holds, for whom and in which language, what data "
                                  "(parties, dates, amounts) change, which output files are needed. The tool writes the "
                                  "files in a temporary directory; you see them and the check of the translator before "
                                  "anything is written to your disk."), input));
    static_cast<QLabel *>(form->itemAt(0)->widget())->setWordWrap(true);
    m_task = new QPlainTextEdit(input);
    m_task->setObjectName(QStringLiteral("aiProjectTask"));
    m_task->setPlaceholderText(tr("For example: a project of supply contracts in Ukrainian: a contract, a specification as an appendix "
                                  "with the table of goods, the parties and the amounts as project parameters, a build target "
                                  "for each document."));
    form->addWidget(m_task, 1);
    auto *toolRow = new QHBoxLayout;
    toolRow->addWidget(new QLabel(tr("Tool:"), input));
    m_tools = new QComboBox(input);
    m_tools->setObjectName(QStringLiteral("aiProjectTool"));
    for (const AiAgent &agent : AiAgents::all())
        if (isInstalled(agent)) m_tools->addItem(agent.name, agent.id);
    toolRow->addWidget(m_tools);
    toolRow->addWidget(new QLabel(tr("Files:"), input));
    m_delivery = new QComboBox(input);
    m_delivery->setObjectName(QStringLiteral("aiProjectDelivery"));
    m_delivery->addItem(tr("in the answer of the tool (read-only, works with every tool)"), true);
    m_delivery->addItem(tr("written by the tool (needs its write mode: check_ai_agent.py --write)"), false);
    m_delivery->setToolTip(tr("In the answer: the tool only answers with the text of the files and Studio makes them; no write "
                              "permission is given. Written by the tool: the tool writes the files in a temporary directory "
                              "(the tool must have writeArguments in agents.json and a sandbox that can start)."));
    toolRow->addWidget(m_delivery);
    toolRow->addStretch();
    form->addLayout(toolRow);
    auto *targetRow = new QHBoxLayout;
    targetRow->addWidget(new QLabel(tr("Create in:"), input));
    m_parent = new QLineEdit(m_defaultParent, input);
    m_parent->setObjectName(QStringLiteral("aiProjectParent"));
    targetRow->addWidget(m_parent, 2);
    auto *browse = new QPushButton(tr("Browse…"), input);
    targetRow->addWidget(browse);
    targetRow->addWidget(new QLabel(tr("Folder:"), input));
    m_folder = new QLineEdit(input);
    m_folder->setObjectName(QStringLiteral("aiProjectFolder"));
    m_folder->setPlaceholderText(tr("project name"));
    targetRow->addWidget(m_folder, 1);
    form->addLayout(targetRow);
    m_targetLabel = new QLabel(input);
    m_targetLabel->setObjectName(QStringLiteral("aiProjectTarget"));
    form->addWidget(m_targetLabel);
    auto *inputButtons = new QHBoxLayout;
    inputButtons->addStretch();
    m_start = new QPushButton(tr("Create with AI"), input);
    m_start->setObjectName(QStringLiteral("aiProjectStart"));
    auto *cancel = new QPushButton(tr("Cancel"), input);
    inputButtons->addWidget(m_start);
    inputButtons->addWidget(cancel);
    form->addLayout(inputButtons);
    m_pages->addWidget(input);

    // Page 1: the work.
    auto *work = new QWidget(m_pages);
    auto *workLayout = new QVBoxLayout(work);
    workLayout->addStretch();
    m_progress = new QLabel(work);
    m_progress->setObjectName(QStringLiteral("aiProjectProgress"));
    m_progress->setWordWrap(true);
    m_progress->setAlignment(Qt::AlignCenter);
    workLayout->addWidget(m_progress);
    auto *stop = new QPushButton(tr("Stop"), work);
    stop->setObjectName(QStringLiteral("aiProjectStop"));
    workLayout->addWidget(stop, 0, Qt::AlignCenter);
    workLayout->addStretch();
    m_pages->addWidget(work);

    // Page 2: the result.
    auto *result = new QWidget(m_pages);
    auto *resultLayout = new QVBoxLayout(result);
    auto *splitter = new QSplitter(Qt::Horizontal, result);
    m_list = new QListWidget(splitter);
    m_list->setObjectName(QStringLiteral("aiProjectFiles"));
    m_preview = new QPlainTextEdit(splitter);
    m_preview->setObjectName(QStringLiteral("aiProjectPreview"));
    m_preview->setReadOnly(true);
    m_preview->setLineWrapMode(QPlainTextEdit::NoWrap);
    splitter->setStretchFactor(0, 1);
    splitter->setStretchFactor(1, 3);
    resultLayout->addWidget(splitter, 1);
    m_summary = new QLabel(result);
    m_summary->setObjectName(QStringLiteral("aiProjectSummary"));
    m_summary->setWordWrap(true);
    resultLayout->addWidget(m_summary);
    m_answerView = new QPlainTextEdit(result);
    m_answerView->setObjectName(QStringLiteral("aiProjectAnswer"));
    m_answerView->setReadOnly(true);
    m_answerView->setMaximumHeight(110);
    resultLayout->addWidget(m_answerView);
    auto *resultButtons = new QHBoxLayout;
    m_fix = new QPushButton(tr("Ask the tool to fix the errors"), result);
    m_fix->setObjectName(QStringLiteral("aiProjectFix"));
    m_create = new QPushButton(tr("Create the project"), result);
    m_create->setObjectName(QStringLiteral("aiProjectCreate"));
    auto *back = new QPushButton(tr("Change the task"), result);
    auto *close = new QPushButton(tr("Close"), result);
    resultButtons->addWidget(m_fix);
    resultButtons->addWidget(m_create);
    resultButtons->addStretch();
    resultButtons->addWidget(back);
    resultButtons->addWidget(close);
    resultLayout->addLayout(resultButtons);
    m_pages->addWidget(result);

    connect(browse, &QPushButton::clicked, this, [this] {
        const QString chosen = QFileDialog::getExistingDirectory(this, tr("Where to create the project directory"), m_parent->text());
        if (!chosen.isEmpty()) m_parent->setText(chosen);
    });
    connect(m_parent, &QLineEdit::textChanged, this, [this] { updateTarget(); });
    connect(m_folder, &QLineEdit::textChanged, this, [this] { updateTarget(); });
    connect(m_task, &QPlainTextEdit::textChanged, this, [this] { updateButtons(); });
    connect(m_start, &QPushButton::clicked, this, [this] {
        QString error;
        if (!startRun(&error)) QMessageBox::warning(this, tr("Create a project with AI"), error);
    });
    connect(cancel, &QPushButton::clicked, this, &QDialog::reject);
    connect(stop, &QPushButton::clicked, this, [this] {
        m_cancelled = true;
        m_backend->cancel();
    });
    connect(m_list, &QListWidget::currentRowChanged, this, [this] { showPreview(); });
    connect(m_list, &QListWidget::itemChanged, this, [this] { updateButtons(); });
    connect(m_fix, &QPushButton::clicked, this, [this] {
        QString error;
        if (!fixErrors(&error)) QMessageBox::warning(this, tr("Create a project with AI"), error);
    });
    connect(m_create, &QPushButton::clicked, this, &AiProjectDialog::createClicked);
    connect(back, &QPushButton::clicked, this, [this] { m_pages->setCurrentIndex(0); });
    connect(close, &QPushButton::clicked, this, &QDialog::reject);
    updateTarget();
    updateButtons();
}

void AiProjectDialog::setTask(const QString &task) { m_task->setPlainText(task); }

void AiProjectDialog::setTarget(const QString &parentDirectory, const QString &folderName)
{
    m_parent->setText(parentDirectory);
    m_folder->setText(folderName);
}

bool AiProjectDialog::setTool(const QString &id)
{
    const int index = m_tools->findData(id);
    if (index < 0) return false;
    m_tools->setCurrentIndex(index);
    return true;
}

QString AiProjectDialog::targetDirectory() const
{
    return QDir(m_parent->text().trimmed()).filePath(m_folder->text().trimmed());
}

void AiProjectDialog::updateTarget()
{
    const QString folder = m_folder->text().trimmed();
    if (folder.isEmpty()) m_targetLabel->setText(tr("Give the folder a name."));
    else m_targetLabel->setText(tr("The project will be created in: %1").arg(QDir::toNativeSeparators(targetDirectory())));
    updateButtons();
}

void AiProjectDialog::updateButtons()
{
    const QString folder = m_folder->text().trimmed();
    const bool folderOk = !folder.isEmpty() && !folder.contains(QLatin1Char('/')) && !folder.contains(QLatin1Char('\\')) && folder != QLatin1String("..")
                          && folder != QLatin1String(".");
    m_start->setEnabled(m_tools->count() > 0 && !m_task->toPlainText().trimmed().isEmpty() && folderOk);
    m_start->setToolTip(m_tools->count() == 0 ? tr("No AI tool is installed (File → Settings).") : QString());
    if (m_list) {
        int chosen = 0;
        for (int row = 0; row < m_list->count(); ++row) chosen += m_list->item(row)->checkState() == Qt::Checked;
        m_create->setEnabled(chosen > 0);
        m_fix->setEnabled(m_check.errors > 0);
    }
}

void AiProjectDialog::setFilesInAnswer(bool inAnswer)
{
    m_delivery->setCurrentIndex(inAnswer ? 0 : 1);
}

bool AiProjectDialog::startRun(QString *error)
{
    const QString folder = m_folder->text().trimmed();
    if (m_tools->count() == 0 || m_task->toPlainText().trimmed().isEmpty() || folder.isEmpty()) {
        if (error) *error = tr("Describe the project, choose a tool and name the folder.");
        return false;
    }
    if (QFileInfo(targetDirectory()).isFile()) {
        if (error) *error = tr("%1 is a file.").arg(QDir::toNativeSeparators(targetDirectory()));
        return false;
    }
    m_work = std::make_unique<QTemporaryDir>(QDir::temp().filePath(QStringLiteral("primula-ai-XXXXXX")));
    if (!m_work->isValid()) {
        if (error) *error = tr("Cannot make a temporary directory: %1").arg(m_work->errorString());
        return false;
    }
    if (!m_delivery->currentData().toBool() && AiAgents::byId(m_tools->currentData().toString()).writeArguments.isEmpty()) {
        if (error) *error = tr("This tool has no write mode (writeArguments in agents.json): choose the files in the answer of the tool.");
        return false;
    }
    m_files.clear();
    m_check = {};
    m_deliveryProblems.clear();
    begin(m_task->toPlainText().trimmed());
    if (!m_backend->isRunning()) {
        if (error) *error = tr("The tool could not be started: %1").arg(AiAgents::program(m_agent));
        m_pages->setCurrentIndex(0);
        return false;
    }
    return true;
}

void AiProjectDialog::begin(const QString &task)
{
    m_agent = AiAgents::byId(m_tools->currentData().toString());
    AiRequest request = m_context;
    request.task = task;
    request.createProject = true;
    request.filesInAnswer = m_delivery->currentData().toBool();
    request.projectDirectory = m_work->path();
    request.proposeEdits = false;
    m_cancelled = false;
    m_seconds = 0;
    m_progress->setText(tr("The tool is working in a temporary directory: %1 s. Nothing is written to your files yet.").arg(0));
    m_pages->setCurrentIndex(1);
    m_clock->start();
    m_backend->start(request, m_agent);
}

bool AiProjectDialog::isRunning() const
{
    return m_backend->isRunning();
}

bool AiProjectDialog::fixErrors(QString *error)
{
    if (m_check.errors == 0 || !m_work || !m_work->isValid()) {
        if (error) *error = tr("There are no errors to fix.");
        return false;
    }
    QStringList errors;
    for (const QString &line : m_check.lines)
        if (errors.size() < 40) errors << line;
    begin(m_delivery->currentData().toBool() ? AiProject::fixTaskInAnswer(errors, m_files) : AiProject::fixTask(errors));
    if (!m_backend->isRunning()) {
        if (error) *error = tr("The tool could not be started: %1").arg(AiAgents::program(m_agent));
        m_clock->stop();
        showResult();
        return false;
    }
    return true;
}

void AiProjectDialog::finished(bool success, const QString &response, const QString &errorMessage)
{
    m_clock->stop();
    if (!success) {
        const QString reason = m_cancelled ? tr("Stopped.") : (errorMessage.isEmpty() ? tr("The tool gave no answer.") : errorMessage);
        // After a fix round the files of the first round are still there: show them, not the task.
        if (!m_files.isEmpty()) {
            showResult();
            m_summary->setText(tr("The last request failed: %1").arg(reason) + QLatin1Char('\n') + m_summary->text());
        } else {
            m_pages->setCurrentIndex(0);
        }
        emit runFailed(reason);
        return;
    }
    m_answer = response;
    if (m_delivery->currentData().toBool()) {
        // The files come in the answer: Studio makes them in the work directory (the same directory the check and the list read).
        QStringList problems;
        const QList<AiProject::File> parsed = AiProject::parseFiles(response, &problems);
        m_deliveryProblems += problems;
        QString error;
        if (!AiProject::write(m_work->path(), parsed, &error)) m_deliveryProblems << error;
        m_answer = AiProject::withoutFiles(response);
    }
    showResult();
}

void AiProjectDialog::showResult()
{
    const AiProject::Scan scan = AiProject::scan(m_work->path());
    m_files = scan.files;
    m_skipped = scan.skipped + m_deliveryProblems;
    m_check = m_files.isEmpty() ? AiProject::Check() : AiProject::check(m_work->path());
    const QSignalBlocker blocker(m_list);
    m_list->clear();
    for (const AiProject::File &file : m_files) {
        auto *item = new QListWidgetItem(file.path, m_list);
        item->setFlags(item->flags() | Qt::ItemIsUserCheckable);
        item->setCheckState(Qt::Checked);
    }
    m_answerView->setPlainText(m_answer);
    QStringList lines;
    if (m_files.isEmpty()) lines << (m_delivery->currentData().toBool() ? tr("The answer of the tool has no files.") : tr("The tool wrote no files."));
    else lines << tr("%n file(s).", nullptr, int(m_files.size()));
    if (!m_files.isEmpty()) {
        if (!m_check.ran) lines << tr("The check did not run: %1").arg(m_check.failure);
        else if (m_check.errors == 0 && m_check.warnings == 0) lines << tr("The translator check: no errors.");
        else lines << tr("The translator check: %1 error(s), %2 warning(s).").arg(m_check.errors).arg(m_check.warnings) + QLatin1Char('\n') + m_check.lines.mid(0, 6).join(QLatin1Char('\n'));
    }
    if (!m_skipped.isEmpty()) lines << tr("Left out: %1").arg(m_skipped.mid(0, 5).join(QStringLiteral("; ")));
    m_summary->setText(lines.join(QLatin1Char('\n')));
    m_pages->setCurrentIndex(2);
    if (m_list->count() > 0) m_list->setCurrentRow(0);
    showPreview();
    updateButtons();
    emit resultShown();
}

void AiProjectDialog::showPreview()
{
    const int row = m_list->currentRow();
    m_preview->setPlainText(row >= 0 && row < m_files.size() ? QString::fromUtf8(m_files.at(row).data) : QString());
}

void AiProjectDialog::setFileChosen(const QString &path, bool chosen)
{
    for (int row = 0; row < m_list->count(); ++row)
        if (m_list->item(row)->text() == path) m_list->item(row)->setCheckState(chosen ? Qt::Checked : Qt::Unchecked);
}

bool AiProjectDialog::createProject(bool overwrite, QString *error)
{
    QList<AiProject::File> chosen;
    for (int row = 0; row < m_list->count() && row < m_files.size(); ++row)
        if (m_list->item(row)->checkState() == Qt::Checked) chosen.append(m_files.at(row));
    if (chosen.isEmpty()) {
        if (error) *error = tr("No file is chosen.");
        return false;
    }
    if (!overwrite && !AiProject::existing(targetDirectory(), chosen).isEmpty()) {
        if (error) *error = tr("Some files already exist in %1.").arg(QDir::toNativeSeparators(targetDirectory()));
        return false;
    }
    if (!AiProject::write(targetDirectory(), chosen, error)) return false;
    const QString entry = AiProject::entryFile(chosen);
    m_created = entry.isEmpty() ? targetDirectory() : QDir(targetDirectory()).filePath(entry);
    return true;
}

void AiProjectDialog::createClicked()
{
    QList<AiProject::File> chosen;
    for (int row = 0; row < m_list->count() && row < m_files.size(); ++row)
        if (m_list->item(row)->checkState() == Qt::Checked) chosen.append(m_files.at(row));
    const QStringList existing = AiProject::existing(targetDirectory(), chosen);
    bool overwrite = false;
    if (!existing.isEmpty()) {
        if (QMessageBox::question(this, tr("Create a project with AI"),
                                  tr("%n file(s) already exist in %1 and will be replaced:\n\n%2\n\nContinue?", nullptr, int(existing.size()))
                                      .arg(QDir::toNativeSeparators(targetDirectory()), existing.mid(0, 8).join(QLatin1Char('\n')))) != QMessageBox::Yes)
            return;
        overwrite = true;
    }
    if (m_check.errors > 0 &&
        QMessageBox::question(this, tr("Create a project with AI"),
                              tr("The check found %n error(s) in the project. Create it anyway?", nullptr, m_check.errors)) != QMessageBox::Yes)
        return;
    QString error;
    if (!createProject(overwrite, &error)) {
        QMessageBox::warning(this, tr("Create a project with AI"), error);
        return;
    }
    accept();
}

void AiProjectDialog::reject()
{
    if (m_backend->isRunning()) {
        if (QMessageBox::question(this, tr("Create a project with AI"), tr("The tool is still working. Stop it and close?")) != QMessageBox::Yes)
            return;
        m_backend->disconnect(this);
        m_backend->cancel();
    }
    QDialog::reject();
}
