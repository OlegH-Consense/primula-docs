#include "NewFileDialog.h"

#include <QComboBox>
#include <QDate>
#include <QDialogButtonBox>
#include <QDir>
#include <QFileDialog>
#include <QFileInfo>
#include <QFormLayout>
#include <QHBoxLayout>
#include <QLabel>
#include <QLineEdit>
#include <QListWidget>
#include <QPushButton>
#include <QRegularExpression>
#include <QVBoxLayout>

namespace {

/// A file or directory name: no path separators and no characters awkward in names.
bool validName(const QString &name)
{
    static const QRegularExpression bad(QStringLiteral("[\\\\/:*?\"<>|]"));
    return !name.isEmpty() && !name.startsWith(QLatin1Char('.')) && !name.contains(bad) && name == name.trimmed();
}

QString kindTitle(const QString &kind)
{
    if (kind == QStringLiteral("document")) return NewFileDialog::tr("Document");
    if (kind == QStringLiteral("fragment")) return NewFileDialog::tr("Fragment");
    if (kind == QStringLiteral("module")) return NewFileDialog::tr("Module of definitions");
    if (kind == QStringLiteral("styles")) return NewFileDialog::tr("Styles module");
    if (kind == QStringLiteral("project")) return NewFileDialog::tr("Project");
    return NewFileDialog::tr("Order project (extends)");
}

} // namespace

NewFileDialog::NewFileDialog(const QString &kind, const QString &directory, const QString &language,
                             const OrderBase *base, QWidget *parent)
    : QDialog(parent)
{
    setWindowTitle(tr("New"));
    resize(720, 560);
    if (base) {
        m_base = *base;
        m_hasBase = true;
    }
    m_kind = new QComboBox(this);
    m_kind->setObjectName(QStringLiteral("newKind"));
    for (const QString &k : Templates::kinds())
        if (k != QStringLiteral("order") || m_hasBase)
            m_kind->addItem(kindTitle(k), k);
    m_kind->setCurrentIndex(qMax(0, m_kind->findData(kind)));
    m_templates = new QListWidget(this);
    m_templates->setObjectName(QStringLiteral("newTemplates"));
    m_description = new QLabel(this);
    m_description->setWordWrap(true);
    m_description->setMinimumHeight(48);
    m_name = new QLineEdit(this);
    m_name->setObjectName(QStringLiteral("newName"));
    m_title = new QLineEdit(this);
    m_title->setObjectName(QStringLiteral("newTitle"));
    m_title->setPlaceholderText(tr("the name, when empty"));
    m_language = new QComboBox(this);
    m_language->addItem(QStringLiteral("Українська"), QStringLiteral("uk"));
    m_language->addItem(QStringLiteral("Русский"), QStringLiteral("ru"));
    m_language->addItem(QStringLiteral("English"), QStringLiteral("en"));
    m_language->setCurrentIndex(qMax(0, m_language->findData(language)));
    m_directory = new QLineEdit(QDir::cleanPath(directory), this);
    m_directory->setObjectName(QStringLiteral("newDirectory"));
    m_browse = new QPushButton(tr("Browse…"), this);
    connect(m_browse, &QPushButton::clicked, this, [this] {
        const QString chosen = QFileDialog::getExistingDirectory(this, tr("Place"), m_directory->text());
        if (!chosen.isEmpty()) m_directory->setText(chosen);
    });
    m_preview = new QListWidget(this);
    m_preview->setObjectName(QStringLiteral("newPreview"));
    m_problem = new QLabel(this);
    m_problem->setStyleSheet(QStringLiteral("color: #b91c1c"));
    m_problem->setWordWrap(true);

    auto *form = new QFormLayout;
    form->addRow(tr("Kind:"), m_kind);
    form->addRow(tr("Template:"), m_templates);
    form->addRow(QString(), m_description);
    form->addRow(tr("Name:"), m_name);
    form->addRow(tr("Title:"), m_title);
    form->addRow(tr("Language of the texts:"), m_language);
    auto *place = new QHBoxLayout;
    place->addWidget(m_directory, 1);
    place->addWidget(m_browse);
    form->addRow(tr("Place:"), place);
    form->addRow(tr("Files to create:"), m_preview);
    auto *buttons = new QDialogButtonBox(QDialogButtonBox::Ok | QDialogButtonBox::Cancel, this);
    m_ok = buttons->button(QDialogButtonBox::Ok);
    m_ok->setText(tr("Create"));
    connect(buttons, &QDialogButtonBox::accepted, this, &QDialog::accept);
    connect(buttons, &QDialogButtonBox::rejected, this, &QDialog::reject);
    auto *layout = new QVBoxLayout(this);
    layout->addLayout(form, 1);
    layout->addWidget(m_problem);
    layout->addWidget(buttons);

    connect(m_kind, &QComboBox::currentIndexChanged, this, [this] { fillTemplates(); });
    connect(m_templates, &QListWidget::currentRowChanged, this, &NewFileDialog::update);
    for (QLineEdit *edit : {m_name, m_title, m_directory})
        connect(edit, &QLineEdit::textChanged, this, &NewFileDialog::update);
    connect(m_language, &QComboBox::currentIndexChanged, this, &NewFileDialog::update);
    fillTemplates();
    m_name->setFocus();
}

QString NewFileDialog::kind() const
{
    return m_kind->currentData().toString();
}

void NewFileDialog::fillTemplates()
{
    m_shown = Templates::available(kind());
    m_templates->clear();
    for (const FileTemplate &tpl : std::as_const(m_shown)) {
        auto *item = new QListWidgetItem(tpl.title(language()) + (tpl.user ? tr(" (user)") : QString()), m_templates);
        item->setToolTip(tpl.description(language()));
    }
    m_templates->setCurrentRow(m_shown.isEmpty() ? -1 : 0);
    // An order lives in orders/<name>/ of the base project; the place is fixed.
    const bool order = kind() == QStringLiteral("order");
    m_directory->setReadOnly(order);
    m_browse->setEnabled(!order);
    if (order) m_directory->setText(QDir(m_base.root).filePath(QStringLiteral("orders")));
    m_title->setEnabled(kind() == QStringLiteral("document") || kind() == QStringLiteral("project")
                        || order);
    update();
}

FileTemplate NewFileDialog::selectedTemplate() const
{
    const int row = m_templates->currentRow();
    return row >= 0 && row < m_shown.size() ? m_shown.at(row) : FileTemplate();
}

QString NewFileDialog::language() const
{
    return m_language->currentData().toString();
}

QString NewFileDialog::targetDirectory() const
{
    const QString place = QDir::cleanPath(m_directory->text().trimmed());
    if (kind() == QStringLiteral("project") || kind() == QStringLiteral("order"))
        return QDir(place).filePath(m_name->text().trimmed());
    return place;
}

QHash<QString, QString> NewFileDialog::values() const
{
    const QString name = m_name->text().trimmed();
    QString title = m_title->text().trimmed().isEmpty() ? name : m_title->text().trimmed();
    title.replace(QLatin1Char('\\'), QStringLiteral("\\\\")).replace(QLatin1Char('"'), QStringLiteral("\\\""));
    const QDate today = QDate::currentDate();
    QHash<QString, QString> result{{QStringLiteral("name"), name}, {QStringLiteral("title_yaml"), title},
                                   {QStringLiteral("lang"), Templates::languageTag(language())},
                                   {QStringLiteral("date"), today.toString(Qt::ISODate)},
                                   {QStringLiteral("year"), QString::number(today.year())}};
    if (kind() == QStringLiteral("order")) {
        const QDir order(targetDirectory());
        result.insert(QStringLiteral("base"), order.relativeFilePath(m_base.projectFile));
        // The documents of the base project except its first target (the contract itself).
        QString targets;
        const qsizetype first = m_base.targets.size() > 1 ? 1 : 0;
        for (qsizetype i = first; i < m_base.targets.size(); ++i) {
            QString stem = QFileInfo(m_base.targets.at(i).source).fileName();
            stem.chop(5);   // .prml
            targets += QStringLiteral("  - {source: %1, output: %2-%3.odt, pdf: true}\n")
                           .arg(order.relativeFilePath(m_base.targets.at(i).source), stem, name);
        }
        result.insert(QStringLiteral("targets"), targets);
        result.insert(QStringLiteral("styles"), m_base.declaresStyles ? QStringLiteral("final.s.prml")
                                                                      : QStringLiteral("std/styles/default, final.s.prml"));
        result.insert(QStringLiteral("order_yaml"), m_base.sampleYaml.isEmpty()
            ? QStringLiteral("number: \"%1\"\ndate: %2\n").arg(name, today.toString(Qt::ISODate)) : m_base.sampleYaml);
    }
    return result;
}

QStringList NewFileDialog::plannedFiles() const
{
    return Templates::plannedFiles(selectedTemplate(), targetDirectory(), values());
}

void NewFileDialog::update()
{
    const FileTemplate tpl = selectedTemplate();
    m_description->setText(tpl.id.isEmpty() ? tr("No templates of this kind.") : tpl.description(language()));
    m_preview->clear();
    QString problem;
    const QString name = m_name->text().trimmed();
    if (tpl.id.isEmpty())
        problem = tr("No templates of this kind.");
    else if (name.isEmpty())
        problem = tr("Enter a name.");
    else if (!validName(name))
        problem = tr("The name must not contain / \\ : * ? \" < > | or start with a dot.");
    else if (m_directory->text().trimmed().isEmpty())
        problem = tr("Choose the place.");
    if (problem.isEmpty()) {
        // Paths relative to the chosen place; the full path in the tooltip.
        const QDir place(QDir::cleanPath(m_directory->text().trimmed()));
        for (const QString &path : plannedFiles()) {
            auto *item = new QListWidgetItem(place.relativeFilePath(path), m_preview);
            item->setToolTip(path);
            if (QFileInfo::exists(path)) {
                item->setForeground(QColor(QStringLiteral("#b91c1c")));
                problem = tr("Some files already exist; choose another name or place.");
            }
        }
    }
    m_problem->setText(problem);
    m_ok->setEnabled(problem.isEmpty());
}
