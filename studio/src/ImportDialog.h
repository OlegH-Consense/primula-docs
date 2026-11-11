#pragma once

// "File → Import a document…" (stage 19.3.4): a document of another format (DOCX, ODT, old DOC, RTF, Markdown,
// HTML, EPUB) is turned into a Primula draft by `primula import`. The dialog asks for the result, the language of
// the document and the options of the command, shows the styles of the source on request, runs the command in the
// background and shows its summary: what was converted and what was left out, and the check of the result.

#include <QDialog>
#include <QProcess>

class QCheckBox;
class QComboBox;
class QLabel;
class QLineEdit;
class QPlainTextEdit;
class QPushButton;

class ImportDialog : public QDialog
{
    Q_OBJECT

public:
    /// @param source  the document to import.
    /// @param defaultDirectory  where the result goes by default (empty: next to the source).
    /// @param interfaceLanguage  en, uk or ru: the language of the messages of the translator.
    ImportDialog(const QString &source, const QString &defaultDirectory, const QString &interfaceLanguage, QWidget *parent = nullptr);
    ~ImportDialog() override;

    /// The extensions that `primula import` reads.
    static QStringList sourceSuffixes();
    /// A file dialog filter of them.
    static QString fileFilter();

    // The inputs (also set by tests).
    void setResult(const QString &path);
    void setLanguage(const QString &language);
    void setStructure(bool recognize);
    void setKeepNumbers(bool keep);
    void setStylesFile(const QString &path);
    QString resultPath() const;

    /// Run `primula import`; false with the reason when it cannot start.
    bool startImport(QString *error = nullptr);
    /// Only list the styles of the source (`--list-styles`).
    bool listStyles(QString *error = nullptr);
    bool isRunning() const { return m_process.state() != QProcess::NotRunning; }
    /// The text the command printed.
    QString output() const { return m_text; }
    /// The exit code of the last run (-1 before it); 0 — imported and the check found no errors, 2 — see the output.
    int exitCode() const { return m_exitCode; }
    /// The result was written (the command ran and the file exists).
    bool resultWritten() const { return m_written; }

signals:
    void finished(int exitCode);

private:
    QString m_source;
    QString m_interfaceLanguage;
    QProcess m_process;
    QString m_text;
    int m_exitCode = -1;
    bool m_written = false;
    bool m_listing = false;
    QLineEdit *m_result = nullptr;
    QComboBox *m_language = nullptr;
    QCheckBox *m_structure = nullptr;
    QCheckBox *m_keep = nullptr;
    QLineEdit *m_styles = nullptr;
    QLabel *m_note = nullptr;
    QPlainTextEdit *m_view = nullptr;
    QPushButton *m_import = nullptr;
    QPushButton *m_list = nullptr;
    QPushButton *m_open = nullptr;

    bool run(bool listing, QString *error);
    void updateNote();
    void processFinished(int code, QProcess::ExitStatus status);
};
