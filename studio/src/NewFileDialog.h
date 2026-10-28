#pragma once

// «File → New» (stage 14.9, remark З9): the kind, a template of that kind, the
// name, the title, the language and the place; the files to be created are
// listed before anything is written.

#include <QDialog>
#include <QHash>

#include "StudioProject.h"
#include "Templates.h"

class QComboBox;
class QLabel;
class QLineEdit;
class QListWidget;
class QPushButton;

class NewFileDialog : public QDialog
{
    Q_OBJECT

public:
    /// The base of an order project: the contract project the order extends.
    struct OrderBase
    {
        QString projectFile;          ///< absolute path of the base project.p.prml
        QString root;                 ///< its root (orders/ is created there)
        QList<BuildTarget> targets;   ///< its targets (all but the first become order targets)
        bool declaresStyles = false;
        QString sampleYaml;           ///< orders/sample.yaml of the base, if any
    };

    /// @param kind       the kind selected first (Templates::kinds()).
    /// @param directory  the default place (the project root or a directory of the Files panel).
    /// @param language   uk, ru or en: the language of the template texts.
    /// @param base       the base for an order project; without it the order kind is not offered.
    NewFileDialog(const QString &kind, const QString &directory, const QString &language,
                  const OrderBase *base, QWidget *parent = nullptr);

    FileTemplate selectedTemplate() const;
    /// The directory the template files are created in (for a project and an order — the new one).
    QString targetDirectory() const;
    QString language() const;
    QHash<QString, QString> values() const;
    /// Absolute paths of the files to be created.
    QStringList plannedFiles() const;

private:
    QComboBox *m_kind = nullptr;
    QListWidget *m_templates = nullptr;
    QLabel *m_description = nullptr;
    QLineEdit *m_name = nullptr;
    QLineEdit *m_title = nullptr;
    QComboBox *m_language = nullptr;
    QLineEdit *m_directory = nullptr;
    QPushButton *m_browse = nullptr;
    QListWidget *m_preview = nullptr;
    QLabel *m_problem = nullptr;
    QPushButton *m_ok = nullptr;
    QList<FileTemplate> m_shown;
    OrderBase m_base;
    bool m_hasBase = false;

    void fillTemplates();
    void update();
    QString kind() const;
};
