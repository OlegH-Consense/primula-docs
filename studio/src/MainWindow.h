#pragma once

#include <optional>

#include "AiProject.h"
#include "CommandCatalog.h"

// The workspace of Primula Studio (stages 14.3, 14.3а, 14.4).
//
// The translator owns the document semantics; Studio edits files, runs
// `primula check|build` and shows the messages and the PDF. Any number of
// files is open in closable tabs; the «Files» panel opens the others on
// request. The session (open files, positions, layout, PDF) is kept in
// .primula-studio/settings.json of the project (StudioProject).

#include <QHash>
#include <QJsonArray>
#include <QJsonObject>
#include <QList>
#include <QMainWindow>
#include <QMap>
#include <QPointer>
#include <QProcess>

#include "AiContext.h"
#include "AiEditsPanel.h"
#include "Backups.h"
#include "AiHistory.h"
#include "BuildController.h"
#include "DocumentInspector.h"
#include "FileTypes.h"
#include "StudioProject.h"
#include "Templates.h"

struct AiRequest;
class CodeEditor;
class AiController;
class AiHistoryPane;
class AiWorkspace;
class EditorPane;
class FileMonitor;
class FilesPanel;
class QMessageBox;
class HelpDialog;
class PdfPreview;
class QAction;
class QActionGroup;
class QComboBox;
class QDockWidget;
class QFontComboBox;
class QLabel;
class QMenu;
class QPdfBookmarkModel;
class QPdfDocument;
class QPlainTextEdit;
class QProgressDialog;
class QSpinBox;
class QSplitter;
class QTabWidget;
class QTreeWidget;
class QTreeWidgetItem;

class MainWindow : public QMainWindow
{
    Q_OBJECT

public:
    /// The PDF of the author guide in ``language`` (else English), or an empty string;
    /// ``tried`` receives the paths looked at (tools/author_docs.py pdf builds the files).
    static QString authorGuidePath(const QString &language, QStringList *tried = nullptr);
    explicit MainWindow(QWidget *parent = nullptr);
    ~MainWindow() override;
    /// Open explicitPath if given, otherwise the last project; a missing path is reported.
    void restoreStartupProject(const QString &explicitPath = {});
    /// Open a project file or a document (its project is found as the translator finds it).
    /// The previous project is closed first (unsaved changes are asked about).
    bool openProject(const QString &path);
    /// Open a file in a tab (or select its tab); a PDF goes to the preview, an ODT to Writer.
    /// @return the editor, or null for a PDF/ODT or a file that cannot be read.
    EditorPane *openFile(const QString &path, bool activate = true);
    /// Open a file in the text editor whatever its type (the user file of file types, an SVG as text).
    EditorPane *openFileAsText(const QString &path, bool activate = true);

protected:
    void closeEvent(QCloseEvent *event) override;

private:
    friend class StudioTests;
    enum class LayoutMode { Split, Tabbed };

    StudioProject m_project;
    LayoutMode m_layoutMode = LayoutMode::Split;
    bool m_shuttingDown = false;
    bool m_restoring = false;

    // Workspace
    QTabWidget *m_tabs = nullptr;
    QWidget *m_pdfContainer = nullptr;
    QSplitter *m_splitter = nullptr;
    QPdfDocument *m_pdfDocument = nullptr;
    QPdfBookmarkModel *m_bookmarks = nullptr;
    PdfPreview *m_pdfView = nullptr;
    QLabel *m_pdfLabel = nullptr;
    QList<int> m_splitterSizes = {900, 600};
    FilesPanel *m_files = nullptr;
    /// The file being written by the running export, and the dialog shown after it (tests read it).
    QString m_exportTarget;
    QPointer<QMessageBox> m_exportNotice;
    FileTypes m_fileTypes;
    QDockWidget *m_filesDock = nullptr;
    QPointer<EditorPane> m_lastEditor;
    /// The document whose PDF is shown (absolute), or empty for a PDF opened directly.
    QString m_previewDocument;

    // Messages
    QPlainTextEdit *m_output = nullptr;
    QTreeWidget *m_diagnostics = nullptr;
    QDockWidget *m_outputDock = nullptr;
    QAction *m_insertBarAction = nullptr;
    QAction *m_consoleAction = nullptr;   ///< View → Console (the console window)
    class ConsolePanel *m_console = nullptr;
    QWidget *m_externalBanner = nullptr;
    QComboBox *m_externalFiles = nullptr;
    QWidget *m_projectWarning = nullptr;
    QLabel *m_projectWarningText = nullptr;
    FileMonitor *m_fileMonitor = nullptr;

    // Translator runs
    BuildController *m_buildController = nullptr;
    QString m_buildDocument;
    // Structure and Styles panels (14.6): dumps of the current document with unsaved buffers.
    DocumentInspector *m_inspector = nullptr;
    class QTimer *m_inspectTimer = nullptr;
    class StructurePanel *m_structurePanel = nullptr;
    class StylesPanel *m_stylesPanel = nullptr;
    class PalettePanel *m_palettePanel = nullptr;
    QDockWidget *m_paletteDock = nullptr;
    QMenu *m_insertMenu = nullptr;
    CommandCatalog m_catalog;
    QDockWidget *m_structureDock = nullptr;
    QDockWidget *m_stylesDock = nullptr;
    QJsonArray m_structure;
    QString m_structureDocument;

    // AI
    AiController *m_aiController = nullptr;
    AiWorkspace *m_aiWorkspace = nullptr;
    QList<AiHistoryPane *> m_aiHistoryPanes;
    AiExchange m_pendingAiExchange;
    QString m_pendingAiProject;
    bool m_hasPendingAi = false;
    struct AiAgentResult { bool success = false; QString response; QString error; };
    QStringList m_aiAgentOrder;                 ///< the tools of the running request, as chosen
    QMap<QString, AiAgentResult> m_aiResults;   ///< their answers as they arrive
    QProgressDialog *m_aiProgress = nullptr;
    HelpDialog *m_helpDialog = nullptr;
    HelpDialog *m_specDialog = nullptr;
    HelpDialog *m_libraryDialog = nullptr;   ///< the standard library document (14.13)
    QPointer<class CodeEditor> m_contextEditor;   ///< the editor with the mark of context help
    QPointer<HelpDialog> m_contextDialog;         ///< the window showing that context
    QMetaObject::Connection m_contextConnection;  ///< its destroyed() → remove the mark
    class EditorAssist *m_assist = nullptr;
    bool m_catalogFailed = false;

    // Actions
    QMenu *m_recentMenu = nullptr;
    QAction *m_saveAction = nullptr;
    QAction *m_saveAllAction = nullptr;
    QAction *m_closeTabAction = nullptr;
    QAction *m_closeOthersAction = nullptr;
    QAction *m_closeProjectAction = nullptr;
    QAction *m_checkAction = nullptr;
    QAction *m_buildAction = nullptr;
    QAction *m_buildProjectAction = nullptr;
    QAction *m_paramsAction = nullptr;
    QAction *m_openOdtAction = nullptr;
    QAction *m_openDirectoryAction = nullptr;
    QAction *m_strictAction = nullptr;
    QActionGroup *m_pdfAfterBuild = nullptr;
    QAction *m_splitAction = nullptr;
    QAction *m_tabbedAction = nullptr;
    QAction *m_togglePdfAction = nullptr;
    QAction *m_aiAction = nullptr;
    QAction *m_backupNowAction = nullptr;
    QAction *m_backupsAction = nullptr;
    QAction *m_backupBeforeSaveAction = nullptr;
    QAction *m_aiHistoryAction = nullptr;
    QAction *m_aiChangeProjectAction = nullptr;
    QAction *m_aiCompareAction = nullptr;   ///< the answers of the last request to several tools (22.7)
    QList<QPair<QString, QString>> m_lastAiAnswers;   ///< tool, answer text of the last request
    QAction *m_aiContextAction = nullptr;
    QAction *m_newOrderAction = nullptr;
    QFontComboBox *m_fontCombo = nullptr;
    QSpinBox *m_fontSize = nullptr;

    void createUi();
    void createActions();
    void stopBackgroundWork();

    // Project and session
    bool hasProject() const { return m_project.isOpen(); }
    bool confirmDiscardChanges();
    void closeProject();
    void clearWorkspace();
    void saveSession();
    void restoreSession();
    void addRecentProject(const QString &path);
    void seedExamples();
    void rebuildRecentMenu();
    void openProjectDialog();
    void createProjectWithAi();
    /// File → Import a document…: the document of another format → a Primula draft (stage 19.3.4); source empty — ask for it.
    void importDocument(const QString &source = QString(), const QString &directory = QString());
    void changeProjectWithAi();
    /// Put the changes of the AI dialog into the project: a backup first, open files change in the editor (unsaved),
    /// the others are written, a deleted file goes to the trash (stage 27, the second step).
    /// @return the number of changes applied.
    int applyAiProjectChanges(const QList<AiProject::File> &changes);
    void openFileDialog();
    void showSettings();
    /// Export a document through pandoc (primula export, decision 139): FORMAT is a pandoc writer;
    /// the file goes next to the ODT of the document, or where the user chooses (askPath).
    void runExport(const QString &document, const QString &format, bool askPath = false);
    /// The submenu Export for a document: Markdown, HTML, DOCX, another format, "Export as…".
    void fillExportMenu(QMenu *menu, const QString &document);
    /// The output file of an export: the ODT path of the document with the extension of the format.
    QString exportPath(const QString &document, const QString &format) const;
    /// Reload the file types (built in, user, project) and filter the Files panel by them (С2).
    void reloadFileTypes();
    /// Open the user file of file types in the editor, created from the template when absent (С2).
    void editFileTypes();
    /// Run the command of a file type for a file; a failure is explained in a message box.
    bool runFileCommand(const FileType &type, const QString &path);
    void editAiContext();
    void updateProjectWarning();

    // Tabs and editors
    /// Tab titles of files: names without `.prml` and the sub-extension, a common
    /// prefix of several names removed, equal names told apart by their directory.
    static QStringList tabTitles(const QStringList &paths);
    QList<EditorPane *> editors() const;
    EditorPane *editorFor(const QString &path) const;
    EditorPane *currentEditor() const;
    bool closeEditor(EditorPane *pane);
    void closeOtherEditors(EditorPane *keep);
    bool saveEditor(EditorPane *pane);
    bool saveAll();
    void updateTabTitles();
    void showOpenFilesMenu();
    void setLayoutMode(LayoutMode mode, bool persist = true);
    void togglePdf();
    void showPdfTab();

    // New files and file operations (stage 14.9, remark З9)
    /// uk, ru or en for template texts: the project language, else the interface language, else uk.
    QString templateLanguage() const;
    /// «New»: the dialog of templates; directory — the default place.
    void newFile(const QString &kind, const QString &directory = {});
    /// Create the files of a template and open them (a new project or order is offered to open).
    bool createFromTemplate(const FileTemplate &tpl, const QString &directory, const QHash<QString, QString> &values,
                            const QString &language, QString *errorMessage);
    void showFilesMenu(const QString &path, const QPoint &position);
    /// "File summary…": `primula describe` of a Primula file in a read-only window (stage 18.9).
    void showFileSummary(const QString &path);
    void newFolderDialog(const QString &directory);
    void copyDialog(const QString &path);
    void renameDialog(const QString &path);
    void trashDialog(const QString &path);
    /// Copy a file or a directory next to it under newName; returns the new path or empty with errorMessage.
    QString copyPath(const QString &path, const QString &newName, QString *errorMessage);
    /// Text files under directory that contain text, with the number of occurrences.
    static QList<QPair<QString, int>> occurrences(const QString &directory, const QString &text);
    /// Replace text in files; false with errorMessage at the first failure.
    static bool replaceInFiles(const QStringList &files, const QString &from, const QString &to, QString *errorMessage);
    /// Rename a file or directory; open editors follow it (refused while one of them has unsaved changes).
    bool renamePath(const QString &path, const QString &newName, QString *errorMessage);
    /// Move a file or directory to the trash, or delete it for good (toTrash false); its editors are
    /// closed (refused while one has unsaved changes). The trash of another partition than the home
    /// directory may be unavailable: then false and the caller may offer deleting for good.
    bool removePath(const QString &path, bool toTrash, QString *errorMessage);
    /// Editors of path itself or of files inside the directory path.
    QList<EditorPane *> editorsUnder(const QString &path) const;

    // Build, check, messages
    QString currentDocument() const;
    void runCheck();
    // Parallel tracks (7.7, stage 16.6): primula parallel from the Build menu and the editor menu.
    /// Fill menu with the actions on the tracks; line — the cursor line for "this segment", or -1.
    void fillParallelMenu(QMenu *menu, const QString &path, int line);
    /// The non-primary tracks of the |parallel environments of the inspected document.
    QStringList parallelTracks() const;
    /// The segment and the track block at line of path (from the last inspection), or empty.
    QPair<QString, QString> parallelPlaceAt(const QString &path, int line) const;
    /// Ask for a status: an empty string — keep it; nullopt — cancelled.
    std::optional<QString> askTrackStatus(const QString &title, bool keepChoice);
    /// Run primula parallel on the current document with options.
    void runParallelTool(const QStringList &options);
    void runBuild(bool wholeProject);
    void buildFinished(bool success, BuildController::Kind kind);
    void showMessages(const QJsonArray &messages);
    void markEditorDiagnostics(const QJsonArray &messages);
    void navigateToDiagnostic(QTreeWidgetItem *item);
    void navigateTo(const QString &path, int line, int column);
    void setPreviewDocument(const QString &document);
    void reloadPdf();
    /// Ask for the dumps of the current document after a pause (typing, tab change, build).
    void scheduleInspection();
    /// Run the dumps now: the current document, with every modified editor buffer as an overlay.
    void inspectDocument();
    void inspectionFinished(const QString &document, const QJsonObject &dump, const QString &errorMessage);
    void setLibraryCommands(const QJsonArray &commands, const QString &baseDir);
    int pdfPageForCursor() const;

    // External changes
    void checkExternalFiles();
    void resolveExternalFile(bool reload);

    // AI
    void showAiDialog();
    void startAiRequest(const AiRequest &request, const QString &scope, const QStringList &agents);
    void closeAiProgress();
    void aiAgentFinished(const QString &agentId, bool success, const QString &response, const QString &errorMessage);
    /// Save the answer of one tool to the history and open it as a tab; null when it has no tab.
    AiHistoryPane *storeAiResult(AiExchange exchange, const QString &response);
    void showAiResults();
    void compareAiAnswers();
    /// The text of path: the open editor's, else the file's (empty when unreadable).
    QString fileText(const QString &path);
    /// Primula context of an AI request (stage 14.10): the project file, the messages of the
    /// last check or build, the catalogue of the translator (Reference, Full), the chosen
    /// sections or the whole specification and library (Full); see AiContext.
    void addPrimulaContext(AiRequest *request, AiContext::Level level, const QStringList &sections,
                           bool messages, bool projectFile);
    void showAiResult(bool success, const QString &response, const QString &errorMessage);
    void loadAiHistory();
    /// The AI context of the project edited in a dialog (from the request window); saved on «Save».
    void editAiContextInDialog(QWidget *parent);
    /// Give the edits of an answer their document, the check and the way to apply (stage 22.3).
    void connectAiEdits(AiHistoryPane *pane, const QString &documentPath);
    /// `primula check` of the text of a file (as the file's text) with the unsaved buffers of the open files.
    AiEditsPanel::CheckReport checkTextForAi(const QString &path, const QString &text);
    /// Apply the edits of the rows to the editor of the file as one undo step.
    void applyAiEdits(AiEditsPanel *panel, const QString &path, const QList<int> &rows, const QString &note = QString());

    // Backup copies (stage 25.1).
    /// Make a snapshot of the files: from the editors' buffers (those that are open) or from the disk.
    /// @return false with error when it could not be made; a snapshot equal to the last one counts as made.
    bool backupFiles(const QStringList &paths, const QString &reason, const QString &note, bool fromBuffers, QString *error = nullptr);
    void backupProjectNow();
    void showBackups();
    void compareWithBackup(const BackupInfo &info, const BackupFile &file);
    /// Put the copy back: into the open editor (as an edit that Undo takes back), else onto the disk.
    /// The current state is saved as a backup first.
    bool restoreBackup(const BackupInfo &info, const BackupFile &file, bool confirm = true);
    AiHistoryPane *addAiHistory(const AiExchange &exchange, const QString &path);
    void showAiHistory();
    void closeAiHistory();

    // Presentation
    void updateUiState();
    void updateWindowTitle();
    void setEditorFontSize(int size);
    void applyEditorFont();
    /// Help → Quick help: always the Studio guide.
    void showQuickHelp();
    /// F1 (Help → Help at the cursor): the section of the construct at the cursor of a Primula
    /// editor — the construct is marked in the editor and named in the help window; without a
    /// construct the Studio guide, with a status bar message saying so.
    void showContextHelp();
    /// Context help for the construct at position of editor (F1, the context menu).
    void showContextSection(class CodeEditor *editor, int position);
    /// Remove the mark of context help from its editor and the context from its window.
    void clearContextHelp();
    /// Help → Language specification: the specification (Russian) at section (empty — the start).
    /// Open the specification at section; "stdlib:N" opens the standard library at section N.
    void showSpecification(const QString &section);
    void showLibrary(const QString &section);
    /// Opens the built-in command cheat sheet (PDF) in the system viewer; the resource is
    /// copied to the cache directory first, since a viewer needs a file.
    void showCheatSheet();
    void showAuthorGuide();
    void setLanguage(const QString &language);
    QString pdfAfterBuildMode() const;
    /// The writable Primula editor that style edits and insertions go to (the current or
    /// the last one); nullptr with a status message when there is none.
    EditorPane *editTarget();
    /// Insert → Header: add missing fields (14.14, 14.16): the recommended metadata of a
    /// document (doc: title, creator, language, created) or the defaults of a project
    /// (doc_defaults: creator, organization) that the header lacks, as a snippet; a message
    /// box tells what was added where, or why nothing was.
    /// @param target  the editor of the context menu; nullptr — the current editor
    void addHeaderFields(CodeEditor *target = nullptr);
    /// Build → Document parameters… (С-В5): the parameters of the project and of the document
    /// header (check --dump-structure) with their defaults; the values set here are kept in
    /// settings.json (build/params/<document>) and passed to Check, Build and the inspection.
    void showBuildParameters();
    /// The saved parameter values of document: name → the text of --param NAME=VALUE.
    QJsonObject savedParameters(const QString &document) const;
    void setSavedParameters(const QString &document, const QJsonObject &values);
    /// "--param", "name=value" for each saved value of document.
    QStringList parameterArguments(const QString &document) const;
    /// The evaluator console (14.15): the arguments of `primula console` for mode — the
    /// current file ("file", with the document parameters), the project, or the library.
    struct ConsoleTargetData { QStringList arguments; QString directory; QString description; };
    ConsoleTargetData consoleTarget(const QString &mode);
    /// Apply style name of dump kind at the cursor of the style target (StyleEditing::apply).
    void applyStyle(const QString &name, const QString &kind);
    /// Remove style name (empty — the innermost style) around the cursor of the style target.
    void removeStyle(const QString &name);
    /// Format → Apply style…: choose a style of the last dump by name, then apply it.
    void chooseStyle();
    /// Load the construct catalogue once (`primula commands`); false with a status message.
    bool ensureCatalog();
    /// Rebuild the Insert menu from the catalogue: a submenu per category, then Image….
    void fillInsertMenu();
    /// Insert entry index of the catalogue at the cursor of the edit target (Snippet::insert).
    void insertConstruct(int index);
    /// Insert plain text at the cursor of the edit target (a reference from the Structure panel).
    void insertText(const QString &text);
    /// Insert → Image…: choose an image, copy it into assets/ of the project when it is
    /// outside the project (after a question), insert |img("path") relative to the file.
    void insertImage();
};
