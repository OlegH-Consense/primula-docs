#include "ImportDialog.h"

#include "Translator.h"

#include <QCheckBox>
#include <QComboBox>
#include <QDialogButtonBox>
#include <QDir>
#include <QFileDialog>
#include <QFileInfo>
#include <QFontDatabase>
#include <QGridLayout>
#include <QHBoxLayout>
#include <QLabel>
#include <QLineEdit>
#include <QPlainTextEdit>
#include <QPushButton>
#include <QStandardPaths>
#include <QVBoxLayout>

QStringList ImportDialog::sourceSuffixes()
{
    return {QStringLiteral("docx"), QStringLiteral("odt"), QStringLiteral("doc"), QStringLiteral("rtf"), QStringLiteral("md"),
            QStringLiteral("markdown"), QStringLiteral("html"), QStringLiteral("htm"), QStringLiteral("epub"), QStringLiteral("txt")};
}

QString ImportDialog::fileFilter()
{
    QStringList patterns;
    for (const QString &suffix : sourceSuffixes()) patterns << QStringLiteral("*.") + suffix;
    return tr("Documents to import (%1);;All files (*)").arg(patterns.join(QLatin1Char(' ')));
}

ImportDialog::ImportDialog(const QString &source, const QString &defaultDirectory, const QString &interfaceLanguage, QWidget *parent)
    : QDialog(parent), m_source(QFileInfo(source).absoluteFilePath()), m_interfaceLanguage(interfaceLanguage)
{
    setObjectName(QStringLiteral("importDialog"));
    setWindowTitle(tr("Import a document — %1").arg(QFileInfo(source).fileName()));
    resize(820, 620);
    auto *layout = new QVBoxLayout(this);
    auto *intro = new QLabel(tr("The document is turned into a Primula draft: the text, the headings (typed numbers become the numbering of "
                                "Primula), the lists, the tables, the images, the notes. The layout of the page is not imported. "
                                "The result is checked and what was left out is told below."), this);
    intro->setWordWrap(true);
    layout->addWidget(intro);
    auto *form = new QGridLayout;
    form->addWidget(new QLabel(tr("Source:"), this), 0, 0);
    auto *sourceLabel = new QLabel(QDir::toNativeSeparators(m_source), this);
    sourceLabel->setTextInteractionFlags(Qt::TextSelectableByMouse);
    form->addWidget(sourceLabel, 0, 1, 1, 2);
    form->addWidget(new QLabel(tr("Result:"), this), 1, 0);
    const QString directory = defaultDirectory.isEmpty() ? QFileInfo(m_source).absolutePath() : defaultDirectory;
    m_result = new QLineEdit(QDir(directory).filePath(QFileInfo(m_source).completeBaseName() + QStringLiteral(".prml")), this);
    m_result->setObjectName(QStringLiteral("importResult"));
    form->addWidget(m_result, 1, 1);
    auto *browse = new QPushButton(tr("Browse…"), this);
    form->addWidget(browse, 1, 2);
    form->addWidget(new QLabel(tr("Language of the document:"), this), 2, 0);
    m_language = new QComboBox(this);
    m_language->setObjectName(QStringLiteral("importLanguage"));
    m_language->setEditable(true);
    m_language->addItems({QStringLiteral("uk-UA"), QStringLiteral("ru-RU"), QStringLiteral("en-US"), QStringLiteral("en-GB")});
    form->addWidget(m_language, 2, 1);
    form->addWidget(new QLabel(tr("Styles of the source:"), this), 3, 0);
    m_styles = new QLineEdit(this);
    m_styles->setObjectName(QStringLiteral("importStyles"));
    m_styles->setPlaceholderText(tr("import-styles.yaml next to the result or above it"));
    form->addWidget(m_styles, 3, 1);
    auto *browseStyles = new QPushButton(tr("Browse…"), this);
    form->addWidget(browseStyles, 3, 2);
    layout->addLayout(form);
    m_structure = new QCheckBox(tr("Recognize the structure (headings, clauses, table of contents)"), this);
    m_structure->setObjectName(QStringLiteral("importStructure"));
    m_structure->setChecked(true);
    m_keep = new QCheckBox(tr("Keep the typed numbers in the text (the headings are not numbered by Primula)"), this);
    m_keep->setObjectName(QStringLiteral("importKeepNumbers"));
    layout->addWidget(m_structure);
    layout->addWidget(m_keep);
    m_note = new QLabel(this);
    m_note->setObjectName(QStringLiteral("importNote"));
    m_note->setWordWrap(true);
    layout->addWidget(m_note);
    m_view = new QPlainTextEdit(this);
    m_view->setObjectName(QStringLiteral("importOutput"));
    m_view->setReadOnly(true);
    m_view->setFont(QFontDatabase::systemFont(QFontDatabase::FixedFont));
    m_view->setPlaceholderText(tr("The summary of the import appears here."));
    layout->addWidget(m_view, 1);
    auto *buttons = new QHBoxLayout;
    m_list = new QPushButton(tr("Styles of the source…"), this);
    m_list->setObjectName(QStringLiteral("importListStyles"));
    m_list->setToolTip(tr("Lists the styles of the source and what they become; nothing is written."));
    m_import = new QPushButton(tr("Import"), this);
    m_import->setObjectName(QStringLiteral("importStart"));
    m_import->setDefault(true);
    m_open = new QPushButton(tr("Open the result"), this);
    m_open->setObjectName(QStringLiteral("importOpen"));
    m_open->setEnabled(false);
    auto *close = new QPushButton(tr("Close"), this);
    buttons->addWidget(m_list);
    buttons->addStretch();
    buttons->addWidget(m_import);
    buttons->addWidget(m_open);
    buttons->addWidget(close);
    layout->addLayout(buttons);

    connect(browse, &QPushButton::clicked, this, [this] {
        const QString chosen = QFileDialog::getSaveFileName(this, tr("Result of the import"), m_result->text(), tr("Primula documents (*.prml)"),
                                                            nullptr, QFileDialog::DontConfirmOverwrite);
        if (!chosen.isEmpty()) m_result->setText(chosen);
    });
    connect(browseStyles, &QPushButton::clicked, this, [this] {
        const QString chosen = QFileDialog::getOpenFileName(this, tr("Map of the styles"), QFileInfo(m_result->text()).absolutePath(),
                                                            tr("YAML (*.yaml *.yml);;All files (*)"));
        if (!chosen.isEmpty()) m_styles->setText(chosen);
    });
    connect(m_result, &QLineEdit::textChanged, this, [this] { updateNote(); });
    connect(m_import, &QPushButton::clicked, this, [this] {
        QString error;
        if (!startImport(&error)) m_view->setPlainText(error);
    });
    connect(m_list, &QPushButton::clicked, this, [this] {
        QString error;
        if (!listStyles(&error)) m_view->setPlainText(error);
    });
    connect(m_open, &QPushButton::clicked, this, [this] { accept(); });
    connect(close, &QPushButton::clicked, this, &QDialog::reject);
    connect(&m_process, QOverload<int, QProcess::ExitStatus>::of(&QProcess::finished), this,
            [this](int code, QProcess::ExitStatus status) { processFinished(code, status); });
    updateNote();
}

ImportDialog::~ImportDialog()
{
    if (isRunning()) {
        m_process.disconnect(this);
        m_process.kill();
        m_process.waitForFinished(2000);
    }
}

void ImportDialog::setResult(const QString &path) { m_result->setText(path); }
void ImportDialog::setLanguage(const QString &language) { m_language->setCurrentText(language); }
void ImportDialog::setStructure(bool recognize) { m_structure->setChecked(recognize); }
void ImportDialog::setKeepNumbers(bool keep) { m_keep->setChecked(keep); }
void ImportDialog::setStylesFile(const QString &path) { m_styles->setText(path); }
QString ImportDialog::resultPath() const { return QFileInfo(m_result->text().trimmed()).absoluteFilePath(); }

void ImportDialog::updateNote()
{
    const bool exists = QFileInfo::exists(resultPath());
    m_note->setText(exists ? tr("The file %1 exists: it is replaced when you import.").arg(QDir::toNativeSeparators(resultPath())) : QString());
}

bool ImportDialog::startImport(QString *error) { return run(false, error); }
bool ImportDialog::listStyles(QString *error) { return run(true, error); }

bool ImportDialog::run(bool listing, QString *error)
{
    if (isRunning()) {
        if (error) *error = tr("The import is running.");
        return false;
    }
    const QString program = Translator::program();
    if (program.isEmpty()) {
        if (error) *error = tr("The translator is not found.");
        return false;
    }
    if (m_result->text().trimmed().isEmpty()) {
        if (error) *error = tr("Give the result a name.");
        return false;
    }
    QStringList arguments{QStringLiteral("import"), m_source, QStringLiteral("-o"), resultPath(), QStringLiteral("--language"),
                          m_language->currentText().trimmed().isEmpty() ? QStringLiteral("uk-UA") : m_language->currentText().trimmed(),
                          QStringLiteral("--lang"), m_interfaceLanguage};
    if (!m_structure->isChecked()) arguments << QStringLiteral("--no-structure");
    if (m_keep->isChecked()) arguments << QStringLiteral("--keep-numbers");
    if (!m_styles->text().trimmed().isEmpty()) arguments << QStringLiteral("--styles") << m_styles->text().trimmed();
    if (listing) arguments << QStringLiteral("--list-styles");
    else arguments << QStringLiteral("--force");   // the dialog told that the file is replaced
    m_listing = listing;
    m_text.clear();
    m_written = false;
    m_exitCode = -1;
    m_open->setEnabled(false);
    m_import->setEnabled(false);
    m_list->setEnabled(false);
    m_view->setPlainText(listing ? tr("Reading the styles of the source…") : tr("Importing… (LibreOffice is started for an old .doc: it takes a while)"));
    m_process.setProcessChannelMode(QProcess::MergedChannels);
    m_process.setWorkingDirectory(QFileInfo(m_source).absolutePath());
    m_process.start(program, arguments);
    if (!m_process.waitForStarted(5000)) {
        m_import->setEnabled(true);
        m_list->setEnabled(true);
        if (error) *error = tr("The translator could not be started: %1").arg(program);
        return false;
    }
    return true;
}

void ImportDialog::processFinished(int code, QProcess::ExitStatus status)
{
    m_text = QString::fromUtf8(m_process.readAll());
    m_exitCode = status == QProcess::NormalExit ? code : -1;
    m_written = !m_listing && QFileInfo::exists(resultPath()) && m_text.contains(QStringLiteral("converted"));
    m_view->setPlainText(m_text);
    m_import->setEnabled(true);
    m_list->setEnabled(true);
    m_open->setEnabled(m_written);
    updateNote();
    emit finished(m_exitCode);
}
