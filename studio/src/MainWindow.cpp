#include "MainWindow.h"

#include "AiAgents.h"
#include "AiContext.h"
#include "AiController.h"
#include "AiHistoryPane.h"
#include "AiRecipes.h"
#include "BackupsDialog.h"
#include "AiWorkspace.h"
#include "ConsolePanel.h"
#include "EditorPane.h"
#include "FileMonitor.h"
#include "EditorAssist.h"
#include "FilesPanel.h"
#include "HelpDialog.h"
#include "StudioVersion.h"
#include "HeaderAssist.h"
#include "StructurePanel.h"
#include "PalettePanel.h"
#include "PrimulaHighlighter.h"
#include "Snippet.h"
#include "StyleEditing.h"
#include "StylesPanel.h"
#include "NewFileDialog.h"
#include "PdfPreview.h"
#include "Translator.h"

#include <QAction>
#include <QActionGroup>
#include <QApplication>
#include <QCheckBox>
#include <QClipboard>
#include <QCloseEvent>
#include <QComboBox>
#include <QDesktopServices>
#include <QStandardPaths>
#include <QDialog>
#include <QDialogButtonBox>
#include <QDir>
#include <QDirIterator>
#include <QDockWidget>
#include <QFile>
#include <QFileDialog>
#include <QFileInfo>
#include <QFontComboBox>
#include <QFontDatabase>
#include <QFormLayout>
#include <QHBoxLayout>
#include <QHeaderView>
#include <QIcon>
#include <QInputDialog>
#include <QJsonDocument>
#include <QTableWidget>
#include <QTemporaryDir>
#include <QTextCursor>
#include <QDate>
#include <QKeySequence>
#include <QMap>
#include <QLabel>
#include <QLineEdit>
#include <QListWidget>
#include <QLocale>
#include <QMenu>
#include <QMenuBar>
#include <QMessageBox>
#include <QPdfBookmarkModel>
#include <QPdfDocument>
#include <QPdfView>
#include <QPlainTextEdit>
#include <QProgressDialog>
#include <QPushButton>
#include <QSaveFile>
#include <QSettings>
#include <QSignalBlocker>
#include <QSpinBox>
#include <QSplitter>
#include <QStatusBar>
#include <QStyle>
#include <QTabBar>
#include <QTabWidget>
#include <QTextBlock>
#include <QTextCursor>
#include <QTimer>
#include <QToolBar>
#include <QTreeWidget>
#include <QUrl>
#include <QVBoxLayout>

#include <algorithm>
#include <functional>

namespace {

/// Version of the saved dock layout (QMainWindow::saveState); raise it when docks are added.
constexpr int WindowStateVersion = 4;

/// The interface language for help and the construct catalogue: the setting, else the
/// system language; en when it is neither uk nor ru.
QString interfaceLanguage()
{
    QString language = QSettings().value(QStringLiteral("ui/language")).toString();
    if (language.isEmpty()) language = QLocale::system().name().section(QLatin1Char('_'), 0, 0);
    if (language != QStringLiteral("ru") && language != QStringLiteral("uk")) language = QStringLiteral("en");
    return language;
}

/// Kind of a Primula file by its sub-extension (specification 2.2, decision 100).
QString primulaKind(const QString &path)
{
    const QString name = QFileInfo(path).fileName();
    if (!name.endsWith(QStringLiteral(".prml")))
        return {};
    if (name.endsWith(QStringLiteral(".f.prml"))) return QStringLiteral("fragment");
    if (name.endsWith(QStringLiteral(".m.prml"))) return QStringLiteral("module");
    if (name.endsWith(QStringLiteral(".s.prml"))) return QStringLiteral("styles");
    if (name.endsWith(QStringLiteral(".p.prml"))) return QStringLiteral("project");
    return QStringLiteral("document");
}

/// Highlighting by the file extension: Primula (the code after the header of
/// styles modules and project files, 2.2), YAML, Markdown, plain text.
CodeEditor::Syntax syntaxFor(const QString &path)
{
    const QString kind = primulaKind(path);
    if (kind == QStringLiteral("styles") || kind == QStringLiteral("project"))
        return CodeEditor::Syntax::PrimulaCode;
    if (!kind.isEmpty())
        return CodeEditor::Syntax::Primula;
    const QString suffix = QFileInfo(path).suffix().toLower();
    if (suffix == QStringLiteral("yaml") || suffix == QStringLiteral("yml"))
        return CodeEditor::Syntax::Yaml;
    if (suffix == QStringLiteral("md") || suffix == QStringLiteral("markdown"))
        return CodeEditor::Syntax::Markdown;
    return CodeEditor::Syntax::PlainText;
}

/// The short name of a file: without `.prml` and the sub-extension (remark З1).
QString shortName(const QString &path)
{
    QString name = QFileInfo(path).fileName();
    for (const QString &suffix : {QStringLiteral(".f.prml"), QStringLiteral(".m.prml"), QStringLiteral(".s.prml"),
                                  QStringLiteral(".p.prml"), QStringLiteral(".prml")}) {
        if (name.endsWith(suffix) && name.size() > suffix.size()) {
            name.chop(suffix.size());
            break;
        }
    }
    return name;
}

QJsonObject toJson(const QVariantMap &map) { return QJsonObject::fromVariantMap(map); }

/// A file whose first 8 KiB contain a NUL byte is not text (images, archives, office files).
bool isBinaryFile(const QString &path)
{
    QFile file(path);
    return file.open(QIODevice::ReadOnly) && file.read(8192).contains('\0');
}

bool samePath(const QString &a, const QString &b)
{
    const QFileInfo left(a), right(b);
    if (left.absoluteFilePath() == right.absoluteFilePath())
        return true;
    return !left.canonicalFilePath().isEmpty() && left.canonicalFilePath() == right.canonicalFilePath();
}

} // namespace

// ----------------------------------------------------------------------
// Tab titles
// ----------------------------------------------------------------------

QStringList MainWindow::tabTitles(const QStringList &paths)
{
    QStringList titles;
    for (const QString &path : paths)
        titles.append(shortName(path));
    // A common prefix of several tabs, cut at a separator, says nothing (З1):
    // «Consense-Contract», «Consense-Invoice» → «Contract», «Invoice».
    if (titles.size() > 1) {
        QString prefix = titles.first();
        for (const QString &title : std::as_const(titles)) {
            int length = 0;
            while (length < prefix.size() && length < title.size() && prefix.at(length) == title.at(length))
                ++length;
            prefix.truncate(length);
        }
        int cut = -1;
        for (int i = prefix.size() - 1; i >= 0; --i) {
            if (QStringLiteral("-_. ").contains(prefix.at(i))) {
                cut = i + 1;
                break;
            }
        }
        const bool usable = cut >= 3 && std::all_of(titles.cbegin(), titles.cend(),
                                                    [cut](const QString &title) { return title.size() > cut; });
        if (usable)
            for (QString &title : titles)
                title.remove(0, cut);
    }
    // Equal names in different directories get the directory: «project (cso270101-1)».
    for (int i = 0; i < titles.size(); ++i) {
        QList<int> same;
        for (int j = 0; j < titles.size(); ++j)
            if (titles.at(j) == titles.at(i)) same.append(j);
        if (same.size() < 2)
            continue;
        for (int j : same)
            titles[j] = titles.at(j) + QStringLiteral(" (") + QFileInfo(QFileInfo(paths.at(j)).absolutePath()).fileName()
                      + QLatin1Char(')');
    }
    return titles;
}

// ----------------------------------------------------------------------
// Construction
// ----------------------------------------------------------------------

MainWindow::MainWindow(QWidget *parent) : QMainWindow(parent)
{
    m_buildController = new BuildController(this);
    m_aiController = new AiController(this);
    m_fileMonitor = new FileMonitor(this);
    m_inspector = new DocumentInspector(this);
    m_inspectTimer = new QTimer(this);
    m_inspectTimer->setSingleShot(true);
    m_inspectTimer->setInterval(700);
    createUi();
    createActions();

    connect(m_buildController, &BuildController::outputReceived, this, [this](const QString &text) {
        m_output->moveCursor(QTextCursor::End);
        m_output->insertPlainText(text);
    });
    connect(m_buildController, &BuildController::started, this, [this](BuildController::Kind kind) {
        statusBar()->showMessage(kind == BuildController::Kind::Build ? tr("Building…")
                                 : kind == BuildController::Kind::Tool ? tr("Running primula parallel…")
                                 : kind == BuildController::Kind::Export ? tr("Exporting…")
                                                                        : tr("Checking…"));
        updateUiState();
    });
    connect(m_buildController, &BuildController::completed, this, &MainWindow::buildFinished);
    connect(m_inspectTimer, &QTimer::timeout, this, &MainWindow::inspectDocument);
    connect(m_inspector, &DocumentInspector::finished, this, &MainWindow::inspectionFinished);
    connect(m_aiController, &AiController::progress, this, [this](const QString &text) {
        m_output->moveCursor(QTextCursor::End);
        m_output->insertPlainText(text);
    });
    connect(m_aiController, &AiController::agentFinished, this, &MainWindow::aiAgentFinished);
    connect(m_aiController, &AiController::allFinished, this, &MainWindow::showAiResults);
    connect(m_fileMonitor, &FileMonitor::checkRequested, this, &MainWindow::checkExternalFiles);

    const QString layout = QSettings().value(QStringLiteral("ui/layout"), QStringLiteral("split")).toString();
    setLayoutMode(layout == QStringLiteral("tabs") ? LayoutMode::Tabbed : LayoutMode::Split, false);
    rebuildRecentMenu();
    updateUiState();
    updateWindowTitle();

    const QByteArray geometry = QSettings().value(QStringLiteral("window/geometry")).toByteArray();
    const QByteArray state = QSettings().value(QStringLiteral("window/state")).toByteArray();
    if (!geometry.isEmpty()) restoreGeometry(geometry);
    // Version 1: the Structure and Styles docks (14.6); version 2: the Palette dock (14.8).
    // An older state is refused, so new docks appear as tabs next to Files instead of
    // squeezed below.
    if (!state.isEmpty()) restoreState(state, WindowStateVersion);
}

MainWindow::~MainWindow()
{
    stopBackgroundWork();
}

void MainWindow::stopBackgroundWork()
{
    if (m_shuttingDown) return;
    m_shuttingDown = true;
    disconnect(qApp, nullptr, this, nullptr);
    m_fileMonitor->setFiles({});
    if (m_buildController->isRunning()) m_buildController->cancel();
    if (m_aiController->isRunning()) m_aiController->cancel();
    m_inspectTimer->stop();
    m_inspector->cancel();
}

void MainWindow::createUi()
{
    resize(1500, 900);

    m_tabs = new QTabWidget(this);
    m_tabs->setObjectName(QStringLiteral("editorTabs"));
    m_tabs->setDocumentMode(true);
    m_tabs->setTabsClosable(true);
    m_tabs->setMovable(true);
    m_tabs->setUsesScrollButtons(true);
    m_tabs->setElideMode(Qt::ElideNone);
    connect(m_tabs, &QTabWidget::tabCloseRequested, this, [this](int index) {
        if (auto *pane = qobject_cast<EditorPane *>(m_tabs->widget(index))) closeEditor(pane);
        else if (m_tabs->widget(index) == m_aiWorkspace) closeAiHistory();
    });
    connect(m_tabs, &QTabWidget::currentChanged, this, [this] {
        if (auto *pane = currentEditor()) {
            m_lastEditor = pane;
            m_files->reveal(pane->filePath());
            // A document becomes the PDF shown, when it has one.
            if (primulaKind(pane->filePath()) == QStringLiteral("document") && !m_restoring
                && QFileInfo::exists(m_project.outputsFor(pane->filePath()).pdf))
                setPreviewDocument(pane->filePath());
        }
        scheduleInspection();
        updateUiState();
    });
    m_tabs->tabBar()->setContextMenuPolicy(Qt::CustomContextMenu);
    connect(m_tabs->tabBar(), &QWidget::customContextMenuRequested, this, [this](const QPoint &point) {
        const int index = m_tabs->tabBar()->tabAt(point);
        auto *pane = qobject_cast<EditorPane *>(m_tabs->widget(index));
        if (!pane) return;
        QMenu menu(this);
        menu.addAction(tr("Close"), this, [this, pane] { closeEditor(pane); });
        menu.addAction(tr("Close other tabs"), this, [this, pane] { closeOtherEditors(pane); });
        menu.addAction(tr("Copy path"), this, [pane] { QApplication::clipboard()->setText(pane->filePath()); });
        if (hasProject() && primulaKind(pane->filePath()) == QStringLiteral("document")) {
            menu.addSeparator();
            fillExportMenu(menu.addMenu(tr("Export")), pane->filePath());
        }
        if (!primulaKind(pane->filePath()).isEmpty())
            menu.addAction(tr("File summary…"), this, [this, pane] { showFileSummary(pane->filePath()); });
        menu.exec(m_tabs->tabBar()->mapToGlobal(point));
    });

    m_pdfDocument = new QPdfDocument(this);
    m_bookmarks = new QPdfBookmarkModel(this);
    m_bookmarks->setDocument(m_pdfDocument);
    m_pdfView = new PdfPreview(this);
    m_pdfView->setPdfDocument(m_pdfDocument);
    m_pdfContainer = new QWidget(this);
    m_pdfContainer->setObjectName(QStringLiteral("pdfContainer"));
    auto *pdfLayout = new QVBoxLayout(m_pdfContainer);
    pdfLayout->setContentsMargins(0, 0, 0, 0);
    auto *pdfButtons = new QHBoxLayout;
    m_pdfLabel = new QLabel(tr("PDF preview"), m_pdfContainer);
    m_pdfLabel->setTextFormat(Qt::PlainText);
    auto *fit = new QPushButton(tr("Fit width"), m_pdfContainer);
    auto *zoomOut = new QPushButton(QStringLiteral("−"), m_pdfContainer);
    auto *zoomIn = new QPushButton(QStringLiteral("+"), m_pdfContainer);
    pdfButtons->addWidget(m_pdfLabel, 1);
    pdfButtons->addWidget(fit);
    pdfButtons->addWidget(zoomOut);
    pdfButtons->addWidget(zoomIn);
    pdfLayout->addLayout(pdfButtons);
    pdfLayout->addWidget(m_pdfView, 1);
    connect(fit, &QPushButton::clicked, this, [this] { m_pdfView->setZoomMode(QPdfView::ZoomMode::FitToWidth); });
    connect(zoomIn, &QPushButton::clicked, this, [this] {
        m_pdfView->setZoomMode(QPdfView::ZoomMode::Custom);
        m_pdfView->setZoomFactor(m_pdfView->zoomFactor() * 1.2);
    });
    connect(zoomOut, &QPushButton::clicked, this, [this] {
        m_pdfView->setZoomMode(QPdfView::ZoomMode::Custom);
        m_pdfView->setZoomFactor(m_pdfView->zoomFactor() / 1.2);
    });

    m_splitter = new QSplitter(Qt::Horizontal, this);
    m_splitter->setChildrenCollapsible(false);
    m_splitter->addWidget(m_tabs);
    m_splitter->addWidget(m_pdfContainer);

    auto *central = new QWidget(this);
    auto *centralLayout = new QVBoxLayout(central);
    centralLayout->setContentsMargins(0, 0, 0, 0);
    m_projectWarning = new QWidget(central);
    m_projectWarning->setObjectName(QStringLiteral("projectWarning"));
    auto *warningRow = new QHBoxLayout(m_projectWarning);
    m_projectWarningText = new QLabel(m_projectWarning);
    m_projectWarningText->setTextFormat(Qt::PlainText);
    m_projectWarningText->setWordWrap(true);
    warningRow->addWidget(m_projectWarningText, 1);
    m_projectWarning->hide();
    m_externalBanner = new QWidget(central);
    m_externalBanner->setObjectName(QStringLiteral("externalChanges"));
    auto *row = new QHBoxLayout(m_externalBanner);
    row->addWidget(new QLabel(tr("Files changed outside Studio:"), m_externalBanner));
    m_externalFiles = new QComboBox(m_externalBanner);
    m_externalFiles->setSizeAdjustPolicy(QComboBox::AdjustToMinimumContentsLengthWithIcon);
    m_externalFiles->setMinimumContentsLength(12);
    row->addWidget(m_externalFiles, 1);
    auto *reload = new QPushButton(tr("Reload selected"), m_externalBanner);
    auto *keep = new QPushButton(tr("Keep editor"), m_externalBanner);
    keep->setToolTip(tr("Keep the editor text; a later Save may overwrite the changed disk file."));
    row->addWidget(reload);
    row->addWidget(keep);
    connect(reload, &QPushButton::clicked, this, [this] { resolveExternalFile(true); });
    connect(keep, &QPushButton::clicked, this, [this] { resolveExternalFile(false); });
    m_externalBanner->hide();
    centralLayout->addWidget(m_externalBanner);
    centralLayout->addWidget(m_projectWarning);
    centralLayout->addWidget(m_splitter, 1);
    setCentralWidget(central);

    m_files = new FilesPanel(this);
    m_filesDock = new QDockWidget(tr("Files"), this);
    m_filesDock->setObjectName(QStringLiteral("filesDock"));
    m_filesDock->setWidget(m_files);
    addDockWidget(Qt::LeftDockWidgetArea, m_filesDock);
    connect(m_files, &FilesPanel::openRequested, this, [this](const QString &path) { openFile(path); });
    connect(m_files, &FilesPanel::contextMenuRequested, this, &MainWindow::showFilesMenu);

    // Structure and Styles share the left area with Files, as tabs.
    m_structurePanel = new StructurePanel(this);
    m_structureDock = new QDockWidget(tr("Structure"), this);
    m_structureDock->setObjectName(QStringLiteral("structureDock"));
    m_structureDock->setWidget(m_structurePanel);
    addDockWidget(Qt::LeftDockWidgetArea, m_structureDock);
    m_stylesPanel = new StylesPanel(this);
    m_stylesDock = new QDockWidget(tr("Styles"), this);
    m_stylesDock->setObjectName(QStringLiteral("stylesDock"));
    m_stylesDock->setWidget(m_stylesPanel);
    addDockWidget(Qt::LeftDockWidgetArea, m_stylesDock);
    m_palettePanel = new PalettePanel(this);
    m_paletteDock = new QDockWidget(tr("Palette"), this);
    m_paletteDock->setObjectName(QStringLiteral("paletteDock"));
    m_paletteDock->setWidget(m_palettePanel);
    addDockWidget(Qt::LeftDockWidgetArea, m_paletteDock);
    tabifyDockWidget(m_filesDock, m_structureDock);
    tabifyDockWidget(m_structureDock, m_stylesDock);
    tabifyDockWidget(m_stylesDock, m_paletteDock);
    connect(m_palettePanel, &PalettePanel::insertRequested, this, &MainWindow::insertConstruct);
    connect(m_palettePanel, &PalettePanel::sectionRequested, this, &MainWindow::showSpecification);
    // Hints and completion in Primula editors (14.8a): the catalogue, the styles and the IDs
    // of the last inspection. A failed catalogue is not retried on every hover.
    EditorAssist::Providers providers;
    providers.catalog = [this]() -> const CommandCatalog * {
        if (!m_catalog.isLoaded() && !m_catalogFailed) m_catalogFailed = !ensureCatalog();
        return m_catalog.isLoaded() ? &m_catalog : nullptr;
    };
    providers.styles = [this] { return m_stylesPanel->inlineStyleDescriptions(); };
    providers.ids = [this] {
        QList<QPair<QString, QString>> ids;
        for (const QJsonValue &value : std::as_const(m_structure)) {
            const QJsonObject item = value.toObject();
            const QString id = item.value(QStringLiteral("id")).toString();
            if (id.isEmpty()) continue;
            QStringList text;
            for (const char *key : {"designation", "number", "title", "text"}) {
                const QString part = item.value(QLatin1String(key)).toString();
                if (!part.isEmpty()) text << part;
            }
            if (text.isEmpty()) text << item.value(QStringLiteral("kind")).toString();
            ids.append({id, text.join(QLatin1Char(' '))});
        }
        return ids;
    };
    // The YAML header (14.14): the file kind by name, the project files for path values.
    providers.fileKind = [this](const CodeEditor *editor) {
        for (EditorPane *pane : editors())
            if (pane->editor() == editor) return primulaKind(pane->filePath());
        return QStringLiteral("document");
    };
    providers.contextMenu = [this](QMenu *menu, CodeEditor *editor, int position) {
        QString path;
        for (EditorPane *pane : editors())
            if (pane->editor() == editor) path = pane->filePath();
        if (path.isEmpty() || parallelTracks().isEmpty()) return;   // only where there is a |parallel
        menu->addSeparator();
        QMenu *submenu = menu->addMenu(tr("Parallel tracks"));
        fillParallelMenu(submenu, path, editor->document()->findBlock(position).blockNumber() + 1);
    };
    providers.files = [this](const CodeEditor *editor) {
        QStringList files;
        QString base;
        for (EditorPane *pane : editors())
            if (pane->editor() == editor) base = QFileInfo(pane->filePath()).absolutePath();
        if (!hasProject() || base.isEmpty()) return files;
        const QDir from(base);
        // Links created in the project may lead to shared libraries (decision 136);
        // QDirIterator skips a link it has already visited, the limit below stops the rest.
        QDirIterator it(m_project.root(), {QStringLiteral("*.prml")}, QDir::Files,
                        QDirIterator::Subdirectories | QDirIterator::FollowSymlinks);
        while (it.hasNext() && files.size() < 2000) {
            const QString path = it.next();
            if (path.contains(QStringLiteral("/.primula-studio/")) || path.contains(QStringLiteral("/.git/"))) continue;
            files << from.relativeFilePath(path);
        }
        files.sort();
        return files;
    };
    m_assist = new EditorAssist(providers, this);
    connect(m_assist, &EditorAssist::sectionRequested, this, &MainWindow::showSpecification);
    connect(m_assist, &EditorAssist::contextHelpRequested, this, &MainWindow::showContextSection);
    connect(m_assist, &EditorAssist::addHeaderFieldsRequested, this, [this](CodeEditor *editor) { addHeaderFields(editor); });
    connect(m_paletteDock, &QDockWidget::visibilityChanged, this, [this](bool visible) { if (visible) ensureCatalog(); });
    connect(m_structurePanel, &StructurePanel::insertRequested, this, &MainWindow::insertText);
    m_filesDock->raise();
    connect(m_structurePanel, &StructurePanel::navigateRequested, this, &MainWindow::navigateTo);
    connect(m_stylesPanel, &StylesPanel::navigateRequested, this, &MainWindow::navigateTo);
    connect(m_stylesPanel, &StylesPanel::applyRequested, this, &MainWindow::applyStyle);
    connect(m_stylesPanel, &StylesPanel::removeRequested, this, &MainWindow::removeStyle);
    // A hidden panel costs nothing; showing one brings it up to date.
    for (QDockWidget *dock : {m_structureDock, m_stylesDock})
        connect(dock, &QDockWidget::visibilityChanged, this, [this](bool visible) { if (visible) scheduleInspection(); });

    m_output = new QPlainTextEdit(this);
    m_output->setReadOnly(true);
    m_output->setMaximumBlockCount(3000);
    m_diagnostics = new QTreeWidget(this);
    m_diagnostics->setObjectName(QStringLiteral("diagnostics"));
    m_diagnostics->setHeaderLabels({tr("Message"), tr("File"), tr("Line")});
    m_diagnostics->setRootIsDecorated(false);
    m_diagnostics->header()->setSectionResizeMode(QHeaderView::Interactive);
    m_diagnostics->header()->setStretchLastSection(false);
    m_diagnostics->setColumnWidth(0, 760);
    m_diagnostics->setColumnWidth(1, 360);
    m_diagnostics->setColumnWidth(2, 80);
    m_diagnostics->header()->restoreState(QSettings().value(QStringLiteral("ui/diagnosticsHeader")).toByteArray());
    m_diagnostics->setToolTip(tr("Double-click a message to open its source location."));
    connect(m_diagnostics, &QTreeWidget::itemActivated, this,
            [this](QTreeWidgetItem *item, int) { navigateToDiagnostic(item); });
    auto *outputTabs = new QTabWidget(this);
    outputTabs->addTab(m_diagnostics, tr("Messages"));
    outputTabs->addTab(m_output, tr("Log"));
    m_outputDock = new QDockWidget(tr("Messages"), this);
    m_outputDock->setObjectName(QStringLiteral("outputDock"));
    m_outputDock->setWidget(outputTabs);
    addDockWidget(Qt::BottomDockWidgetArea, m_outputDock);
    m_outputDock->hide();

    // The evaluator console (14.15): a non-modal window of its own above the main one (14.16).
    m_console = new ConsolePanel(this);
    m_console->setTargetProvider([this](const QString &mode) {
        const ConsoleTargetData data = consoleTarget(mode);
        return ConsolePanel::Target{data.arguments, data.directory, data.description};
    });
    m_assist->attach(m_console->input());
    m_console->setCompleter(m_assist->completer());
    connect(m_console, &ConsolePanel::sectionRequested, this, &MainWindow::showSpecification);
    m_console->hide();
    connect(m_console, &ConsolePanel::visibilityChanged, this, [this](bool visible) {
        if (m_consoleAction) {
            const QSignalBlocker blocker(m_consoleAction);
            m_consoleAction->setChecked(visible);
        }
        if (!visible) return;
        if (ensureCatalog()) m_console->setCatalog(&m_catalog);
        if (!m_console->isRunning()) m_console->restart();
        m_console->input()->setFocus();
    });

    m_aiWorkspace = new AiWorkspace(this);
    m_aiWorkspace->hide();
    connect(m_aiWorkspace, &AiWorkspace::closeRequested, this, &MainWindow::closeAiHistory);
}

void MainWindow::createActions()
{
    auto *fileMenu = menuBar()->addMenu(tr("&File"));
    // «New» from templates (stage 14.9, remark З9).
    QMenu *newMenu = fileMenu->addMenu(tr("&New"));
    newMenu->addAction(tr("&Document…"), this, [this] { newFile(QStringLiteral("document")); })
        ->setShortcut(QKeySequence::New);
    newMenu->addAction(tr("&Fragment…"), this, [this] { newFile(QStringLiteral("fragment")); });
    newMenu->addAction(tr("&Module of definitions…"), this, [this] { newFile(QStringLiteral("module")); });
    newMenu->addAction(tr("&Styles module…"), this, [this] { newFile(QStringLiteral("styles")); });
    newMenu->addSeparator();
    newMenu->addAction(tr("&Project…"), this, [this] { newFile(QStringLiteral("project")); });
    m_newOrderAction = newMenu->addAction(tr("&Order project…"), this, [this] { newFile(QStringLiteral("order")); });
    newMenu->addSeparator();
    newMenu->addAction(tr("Open the folder of user templates"), this, [] {
        QDir().mkpath(Templates::userDirectory());
        QDesktopServices::openUrl(QUrl::fromLocalFile(Templates::userDirectory()));
    });
    auto *openProjectAction = fileMenu->addAction(tr("&Open project or document…"), this, &MainWindow::openProjectDialog);
    openProjectAction->setShortcut(QKeySequence::Open);
    auto *openFileAction = fileMenu->addAction(tr("Open &file…"), this, &MainWindow::openFileDialog);
    openFileAction->setShortcut(QKeySequence(Qt::CTRL | Qt::SHIFT | Qt::Key_O));
    m_recentMenu = fileMenu->addMenu(tr("Recent projects"));
    fileMenu->addSeparator();
    m_saveAction = fileMenu->addAction(tr("&Save"), this, [this] { if (auto *pane = currentEditor()) saveEditor(pane); });
    m_saveAction->setShortcut(QKeySequence::Save);
    m_saveAllAction = fileMenu->addAction(tr("Save a&ll"), this, [this] { saveAll(); });
    m_saveAllAction->setShortcut(QKeySequence(Qt::CTRL | Qt::SHIFT | Qt::Key_S));
    QMenu *backupMenu = fileMenu->addMenu(tr("&Backups"));
    m_backupNowAction = backupMenu->addAction(tr("Back up the project &now"), this, &MainWindow::backupProjectNow);
    m_backupNowAction->setShortcut(QKeySequence(Qt::CTRL | Qt::ALT | Qt::Key_B));
    m_backupsAction = backupMenu->addAction(tr("&Show backups…"), this, &MainWindow::showBackups);
    m_backupsAction->setShortcut(QKeySequence(Qt::CTRL | Qt::ALT | Qt::SHIFT | Qt::Key_B));
    m_backupBeforeSaveAction = backupMenu->addAction(tr("Back up a file &before saving it"));
    m_backupBeforeSaveAction->setCheckable(true);
    m_backupBeforeSaveAction->setChecked(QSettings().value(QStringLiteral("backups/beforeSave"), false).toBool());
    m_backupBeforeSaveAction->setToolTip(tr("The version on the disk is kept in .primula-studio/backups before a save replaces it."));
    connect(m_backupBeforeSaveAction, &QAction::toggled, this,
            [](bool on) { QSettings().setValue(QStringLiteral("backups/beforeSave"), on); });
    fileMenu->addSeparator();
    m_closeTabAction = fileMenu->addAction(tr("&Close tab"), this, [this] { if (auto *pane = currentEditor()) closeEditor(pane); });
    m_closeTabAction->setShortcut(QKeySequence(Qt::CTRL | Qt::Key_W));
    m_closeOthersAction = fileMenu->addAction(tr("Close &other tabs"), this,
                                              [this] { if (auto *pane = currentEditor()) closeOtherEditors(pane); });
    m_closeProjectAction = fileMenu->addAction(tr("Close &project"), this, &MainWindow::closeProject);
    fileMenu->addSeparator();
    fileMenu->addAction(tr("Se&ttings…"), this, &MainWindow::showSettings);
    fileMenu->addAction(tr("File &types…"), this, &MainWindow::editFileTypes);
    fileMenu->addSeparator();
    fileMenu->addAction(tr("E&xit"), QKeySequence::Quit, this, &QWidget::close);

    auto *editMenu = menuBar()->addMenu(tr("&Edit"));
    auto searchAction = [this, editMenu](const QString &label, const QKeySequence &key, auto callback) {
        QAction *action = editMenu->addAction(label, this, callback);
        action->setShortcut(key);
        // EditorPane owns scoped shortcuts; the menu displays the same keys.
        action->setShortcutContext(Qt::WidgetShortcut);
        return action;
    };
    searchAction(tr("&Find…"), QKeySequence::Find,
                 [this] { if (auto *pane = currentEditor()) pane->showSearch(); })->setObjectName(QStringLiteral("findAction"));
    searchAction(tr("Find &next"), QKeySequence(Qt::Key_F3),
                 [this] { if (auto *pane = currentEditor()) pane->findNext(); })->setObjectName(QStringLiteral("findNextAction"));
    searchAction(tr("Find &previous"), QKeySequence(Qt::SHIFT | Qt::Key_F3),
                 [this] { if (auto *pane = currentEditor()) pane->findNext(true); })->setObjectName(QStringLiteral("findPreviousAction"));
    searchAction(tr("&Replace…"), QKeySequence(Qt::CTRL | Qt::Key_H),
                 [this] { if (auto *pane = currentEditor()) pane->showSearch(true); })->setObjectName(QStringLiteral("replaceAction"));

    // Insert: the constructs of the language from `primula commands` (stage 14.8).
    m_insertMenu = menuBar()->addMenu(tr("&Insert"));
    m_insertMenu->setObjectName(QStringLiteral("insertMenu"));
    m_insertMenu->setToolTipsVisible(true);
    connect(m_insertMenu, &QMenu::aboutToShow, this, &MainWindow::fillInsertMenu);

    // Format: apply and remove styles at the cursor (stage 14.7).
    auto *formatMenu = menuBar()->addMenu(tr("F&ormat"));
    QAction *applyStyleAction = formatMenu->addAction(tr("&Apply style…"), this, &MainWindow::chooseStyle);
    applyStyleAction->setObjectName(QStringLiteral("applyStyleAction"));
    applyStyleAction->setShortcut(QKeySequence(Qt::CTRL | Qt::SHIFT | Qt::Key_Y));
    QAction *removeStyleAction = formatMenu->addAction(tr("&Remove style at the cursor"), this,
                                                       [this] { removeStyle(QString()); });
    removeStyleAction->setObjectName(QStringLiteral("removeStyleAction"));
    removeStyleAction->setShortcut(QKeySequence(Qt::CTRL | Qt::SHIFT | Qt::ALT | Qt::Key_Y));

    auto *buildMenu = menuBar()->addMenu(tr("&Build"));
    m_checkAction = buildMenu->addAction(tr("&Check document"), this, &MainWindow::runCheck);
    m_checkAction->setShortcut(QKeySequence(Qt::CTRL | Qt::SHIFT | Qt::Key_Return));
    m_buildAction = buildMenu->addAction(tr("&Build document (ODT and PDF)"), this, [this] { runBuild(false); });
    m_buildAction->setShortcut(QKeySequence(Qt::Key_F9));
    m_buildProjectAction = buildMenu->addAction(tr("Build all &targets of the project"), this, [this] { runBuild(true); });
    m_buildProjectAction->setShortcut(QKeySequence(Qt::SHIFT | Qt::Key_F9));
    m_paramsAction = buildMenu->addAction(tr("Document &parameters…"), this, &MainWindow::showBuildParameters);
    m_paramsAction->setObjectName(QStringLiteral("buildParametersAction"));
    // Blanks, confirmation and status of translations in |parallel (7.7): filled when shown.
    QMenu *parallelMenu = buildMenu->addMenu(tr("Parallel &tracks"));
    parallelMenu->setObjectName(QStringLiteral("parallelMenu"));
    connect(parallelMenu, &QMenu::aboutToShow, this, [this, parallelMenu] {
        EditorPane *pane = currentEditor();
        fillParallelMenu(parallelMenu, pane ? pane->filePath() : QString(),
                         pane ? pane->editor()->textCursor().blockNumber() + 1 : -1);
    });
    // Export through pandoc (decision 139): filled for the current document when shown.
    QMenu *exportMenu = buildMenu->addMenu(tr("E&xport"));
    exportMenu->setObjectName(QStringLiteral("exportMenu"));
    connect(exportMenu, &QMenu::aboutToShow, this, [this, exportMenu] {
        fillExportMenu(exportMenu, hasProject() ? currentDocument() : QString());
    });
    buildMenu->addSeparator();
    m_strictAction = buildMenu->addAction(tr("&Strict: warnings are errors"));
    m_strictAction->setCheckable(true);
    connect(m_strictAction, &QAction::toggled, this, [this](bool on) {
        if (!hasProject()) return;
        QJsonObject build = m_project.group(QStringLiteral("build"));
        build.insert(QStringLiteral("strict"), on);
        m_project.setGroup(QStringLiteral("build"), build);
        m_project.saveSettings();
    });
    auto *afterBuild = buildMenu->addMenu(tr("Show PDF after a successful build"));
    m_pdfAfterBuild = new QActionGroup(this);
    for (const auto &[mode, label] : {std::pair{QStringLiteral("visible"), tr("If the PDF was visible")},
                                      std::pair{QStringLiteral("always"), tr("Always")},
                                      std::pair{QStringLiteral("never"), tr("Never")}}) {
        QAction *action = afterBuild->addAction(label);
        action->setCheckable(true);
        action->setData(mode);
        m_pdfAfterBuild->addAction(action);
    }
    connect(m_pdfAfterBuild, &QActionGroup::triggered, this, [this](QAction *action) {
        if (!hasProject()) return;
        QJsonObject build = m_project.group(QStringLiteral("build"));
        build.insert(QStringLiteral("pdfAfterBuild"), action->data().toString());
        m_project.setGroup(QStringLiteral("build"), build);
        m_project.saveSettings();
    });
    buildMenu->addSeparator();
    m_openOdtAction = buildMenu->addAction(tr("Open ODT in Writer"), this, [this] {
        const QString document = m_previewDocument.isEmpty() ? currentDocument() : m_previewDocument;
        QDesktopServices::openUrl(QUrl::fromLocalFile(m_project.outputsFor(document).output));
    });
    m_openDirectoryAction = buildMenu->addAction(tr("Open project directory"), this, [this] {
        QDesktopServices::openUrl(QUrl::fromLocalFile(m_project.root()));
    });

    auto *viewMenu = menuBar()->addMenu(tr("&View"));
    m_togglePdfAction = viewMenu->addAction(tr("Switch source / PDF"), this, &MainWindow::togglePdf);
    m_togglePdfAction->setShortcut(QKeySequence(Qt::Key_F4));
    viewMenu->addAction(tr("Open files…"), this, &MainWindow::showOpenFilesMenu)->setShortcut(QKeySequence(Qt::CTRL | Qt::Key_E));
    viewMenu->addSeparator();
    viewMenu->addAction(m_filesDock->toggleViewAction());
    viewMenu->addAction(m_structureDock->toggleViewAction());
    viewMenu->addAction(m_stylesDock->toggleViewAction());
    viewMenu->addAction(m_paletteDock->toggleViewAction());
    viewMenu->addAction(m_outputDock->toggleViewAction());
    m_consoleAction = viewMenu->addAction(tr("&Console"));
    m_consoleAction->setObjectName(QStringLiteral("consoleAction"));
    m_consoleAction->setCheckable(true);
    m_consoleAction->setShortcut(QKeySequence(Qt::CTRL | Qt::ALT | Qt::Key_C));
    m_consoleAction->setToolTip(tr("The evaluator console: a window of its own for trying code and functions"));
    connect(m_consoleAction, &QAction::toggled, this, [this](bool on) {
        if (!on) {
            m_console->hide();
            return;
        }
        m_console->show();
        m_console->raise();
        m_console->activateWindow();
    });
    // Ctrl+Alt+C also closes the console from its own window.
    m_console->addAction(m_consoleAction);
    auto *layoutMenu = viewMenu->addMenu(tr("Layout"));
    auto *layoutGroup = new QActionGroup(this);
    m_splitAction = layoutMenu->addAction(tr("Source and PDF side by side"), this, [this] { setLayoutMode(LayoutMode::Split); });
    m_splitAction->setCheckable(true);
    layoutGroup->addAction(m_splitAction);
    m_tabbedAction = layoutMenu->addAction(tr("PDF as a tab"), this, [this] { setLayoutMode(LayoutMode::Tabbed); });
    m_tabbedAction->setCheckable(true);
    layoutGroup->addAction(m_tabbedAction);
    viewMenu->addSeparator();
    auto *increaseFont = viewMenu->addAction(tr("Increase editor font"), this, [this] { setEditorFontSize(m_fontSize->value() + 1); });
    increaseFont->setShortcuts(QKeySequence::keyBindings(QKeySequence::ZoomIn));
    auto *decreaseFont = viewMenu->addAction(tr("Decrease editor font"), this, [this] { setEditorFontSize(m_fontSize->value() - 1); });
    decreaseFont->setShortcuts(QKeySequence::keyBindings(QKeySequence::ZoomOut));
    viewMenu->addAction(tr("Reset editor font size"), this, [this] { setEditorFontSize(10); })
        ->setShortcut(QKeySequence(Qt::CTRL | Qt::Key_0));
    auto *languageMenu = viewMenu->addMenu(tr("Interface language"));
    languageMenu->addAction(tr("System language"), this, [this] { setLanguage(QString()); });
    languageMenu->addAction(QStringLiteral("English"), this, [this] { setLanguage(QStringLiteral("en")); });
    languageMenu->addAction(QStringLiteral("Українська"), this, [this] { setLanguage(QStringLiteral("uk")); });
    languageMenu->addAction(QStringLiteral("Русский"), this, [this] { setLanguage(QStringLiteral("ru")); });

    auto *aiMenu = menuBar()->addMenu(tr("&AI"));
    m_aiAction = aiMenu->addAction(tr("Ask AI about the document…"), this, &MainWindow::showAiDialog);
    m_aiAction->setShortcut(QKeySequence(Qt::CTRL | Qt::ALT | Qt::Key_Return));
    m_aiHistoryAction = aiMenu->addAction(tr("Show AI history"), this, &MainWindow::showAiHistory);
    m_aiContextAction = aiMenu->addAction(tr("Edit AI context of the project"), this, &MainWindow::editAiContext);

    auto *helpMenu = menuBar()->addMenu(tr("&Help"));
    helpMenu->addAction(tr("Quick help"), this, &MainWindow::showQuickHelp);
    helpMenu->addAction(tr("Help at the cursor"), this, &MainWindow::showContextHelp)->setShortcut(QKeySequence::HelpContents);
    helpMenu->addAction(tr("Language specification"), this, [this] { showSpecification(QString()); });
    helpMenu->addAction(tr("Standard library"), this, [this] { showLibrary(QString()); });
    helpMenu->addAction(tr("Command cheat sheet (PDF)"), this, &MainWindow::showCheatSheet);
    helpMenu->addAction(tr("Author guide (PDF)"), this, &MainWindow::showAuthorGuide);
    helpMenu->addAction(tr("About Primula Studio"), this, [this] {
        const QString translator = Translator::version();
        QMessageBox::about(this, tr("About Primula Studio"),
            tr("Primula Studio %1\nAn editor and build interface for Primula documents.")
                .arg(QString::fromLatin1(studioVersion()))
            + QStringLiteral("\n\n") + (translator.isEmpty() ? tr("Translator: not found") : translator));
    });

    auto *toolbar = addToolBar(tr("Main toolbar"));
    toolbar->setObjectName(QStringLiteral("mainToolbar"));
    toolbar->setToolButtonStyle(Qt::ToolButtonIconOnly);
    toolbar->setIconSize(QSize(24, 24));
    auto icon = [this](QAction *action, const QString &name, QStyle::StandardPixmap fallback) {
        action->setIcon(QIcon::fromTheme(name, style()->standardIcon(fallback)));
        QString tip = action->text();
        tip.remove(QLatin1Char('&'));
        if (!action->shortcut().isEmpty())
            tip += QStringLiteral(" (") + action->shortcut().toString(QKeySequence::NativeText) + QLatin1Char(')');
        action->setToolTip(tip);
    };
    icon(openProjectAction, QStringLiteral("document-open"), QStyle::SP_DialogOpenButton);
    icon(m_saveAllAction, QStringLiteral("document-save-all"), QStyle::SP_DialogSaveButton);
    icon(m_checkAction, QStringLiteral("dialog-ok-apply"), QStyle::SP_DialogApplyButton);
    icon(m_buildAction, QStringLiteral("run-build"), QStyle::SP_MediaPlay);
    icon(m_openOdtAction, QStringLiteral("x-office-document"), QStyle::SP_FileIcon);
    icon(m_togglePdfAction, QStringLiteral("application-pdf"), QStyle::SP_FileDialogContentsView);
    // Icons of the stages 22 and 25: a theme icon if the theme has one, else an icon of Studio.
    auto themed = [](QAction *action, const QStringList &names, const QString &resource) {
        QIcon fallback(resource);
        QIcon found;
        for (const QString &name : names)
            if (found.isNull() && QIcon::hasThemeIcon(name)) found = QIcon::fromTheme(name);
        action->setIcon(found.isNull() ? fallback : found);
        QString tip = action->text();
        tip.remove(QLatin1Char('&'));
        tip.remove(QStringLiteral("…"));
        if (!action->shortcut().isEmpty())
            tip += QStringLiteral(" (") + action->shortcut().toString(QKeySequence::NativeText) + QLatin1Char(')');
        action->setToolTip(tip);
    };
    // «Ask AI»: a spark (the sign of an assistant) instead of the question mark that read as «information».
    themed(m_aiAction, {QStringLiteral("tools-wizard")}, QStringLiteral(":/icons/ai.svg"));
    themed(m_backupNowAction, {QStringLiteral("archive-insert")}, QStringLiteral(":/icons/backup-create.svg"));
    themed(m_backupsAction, {QStringLiteral("view-history")}, QStringLiteral(":/icons/backup-history.svg"));
    themed(m_consoleAction, {QStringLiteral("utilities-terminal")}, QStringLiteral(":/icons/console.svg"));
    for (QAction *action : {openProjectAction, m_saveAllAction})
        toolbar->addAction(action);
    toolbar->addSeparator();
    for (QAction *action : {m_checkAction, m_buildAction, m_openOdtAction, m_togglePdfAction})
        toolbar->addAction(action);
    auto *toggleLayout = toolbar->addAction(QIcon::fromTheme(QStringLiteral("view-split-left-right"),
                                                             style()->standardIcon(QStyle::SP_FileDialogListView)),
                                            tr("Switch layout"), this, [this] {
        setLayoutMode(m_layoutMode == LayoutMode::Split ? LayoutMode::Tabbed : LayoutMode::Split);
    });
    toggleLayout->setObjectName(QStringLiteral("toggleLayoutAction"));
    toggleLayout->setToolTip(tr("Switch between source and PDF side by side and PDF as a tab"));
    toolbar->addSeparator();
    toolbar->addAction(m_aiAction);
    toolbar->addSeparator();
    toolbar->addAction(m_backupNowAction);
    toolbar->addAction(m_backupsAction);
    toolbar->addSeparator();
    toolbar->addAction(m_consoleAction);
    toolbar->addSeparator();
    toolbar->addWidget(new QLabel(tr("Editor font:"), toolbar));
    m_fontCombo = new QFontComboBox(toolbar);
    m_fontCombo->setMaximumWidth(160);
    const QString defaultFamily = QFontDatabase::systemFont(QFontDatabase::FixedFont).family();
    m_fontCombo->setCurrentFont(QFont(QSettings().value(QStringLiteral("editor/fontFamily"), defaultFamily).toString()));
    toolbar->addWidget(m_fontCombo);
    m_fontSize = new QSpinBox(toolbar);
    m_fontSize->setRange(8, 32);
    m_fontSize->setSuffix(tr(" pt"));
    m_fontSize->setValue(QSettings().value(QStringLiteral("editor/fontSize"), 10).toInt());
    toolbar->addWidget(m_fontSize);
    connect(m_fontCombo, &QFontComboBox::currentFontChanged, this, [this](const QFont &font) {
        QSettings().setValue(QStringLiteral("editor/fontFamily"), font.family());
        applyEditorFont();
    });
    connect(m_fontSize, &QSpinBox::valueChanged, this, &MainWindow::setEditorFontSize);
}

// ----------------------------------------------------------------------
// Project and session
// ----------------------------------------------------------------------

bool MainWindow::openProject(const QString &path)
{
    if (m_aiController->isRunning() || m_buildController->isRunning())
        return false;
    if (hasProject() && !confirmDiscardChanges())
        return false;
    StudioProject project;
    QString error;
    QApplication::setOverrideCursor(Qt::WaitCursor);
    const bool opened = project.open(path, &error);
    QApplication::restoreOverrideCursor();
    if (!opened) {
        QMessageBox::critical(this, tr("Cannot open project"),
                              error.isEmpty() ? tr("Cannot read the project of %1.").arg(path) : error);
        return false;
    }
    if (hasProject())
        saveSession();
    clearWorkspace();
    m_project = project;
    m_files->setRoot(m_project.root());
    reloadFileTypes();
    m_output->clear();
    addRecentProject(m_project.openedPath());
    restoreSession();
    loadAiHistory();
    // The console of the previous project ends; the history is the project's.
    m_console->stop();
    m_console->setHistoryPath(QDir(m_project.serviceDirectory()).filePath(QStringLiteral("console-history.json")));
    if (m_console->isVisible()) m_console->restart();
    const QJsonObject build = m_project.group(QStringLiteral("build"));
    {
        const QSignalBlocker blocker(m_strictAction);
        m_strictAction->setChecked(build.value(QStringLiteral("strict")).toBool());
    }
    const QString mode = pdfAfterBuildMode();
    for (QAction *action : m_pdfAfterBuild->actions())
        action->setChecked(action->data().toString() == mode);
    // Messages of reading the project header (warnings of the description).
    QJsonArray messages;
    for (const QJsonObject &message : m_project.messages())
        messages.append(message);
    showMessages(messages);
    updateProjectWarning();
    updateUiState();
    updateWindowTitle();
    statusBar()->showMessage(tr("Opened: %1").arg(m_project.relative(m_project.openedPath())), 3000);
    scheduleInspection();
    return true;
}

void MainWindow::clearWorkspace()
{
    m_restoring = true;
    for (EditorPane *pane : editors()) {
        m_tabs->removeTab(m_tabs->indexOf(pane));
        pane->deleteLater();
    }
    m_tabs->clear();
    m_restoring = false;
    m_fileMonitor->setFiles({});
    m_externalBanner->hide();
    m_externalFiles->clear();
    m_diagnostics->clear();
    m_pdfView->clear();
    m_pdfLabel->setText(tr("PDF preview"));
    m_previewDocument.clear();
    m_structure = {};
    m_structureDocument.clear();
    m_inspectTimer->stop();
    m_inspector->cancel();
    m_structurePanel->clear();
    m_stylesPanel->clear();
    m_aiWorkspace->clear();
    m_aiWorkspace->hide();
    for (AiHistoryPane *pane : std::as_const(m_aiHistoryPanes)) pane->deleteLater();
    m_aiHistoryPanes.clear();
    m_project = StudioProject();
    m_files->setRoot({});
    reloadFileTypes();
    setLayoutMode(m_layoutMode, false);
}

void MainWindow::closeProject()
{
    if (!hasProject() || m_aiController->isRunning() || m_buildController->isRunning() || !confirmDiscardChanges())
        return;
    saveSession();
    clearWorkspace();
    m_console->stop();
    m_output->clear();
    m_projectWarning->hide();
    QSettings settings;
    settings.remove(QStringLiteral("projects/last"));
    updateUiState();
    updateWindowTitle();
}

bool MainWindow::confirmDiscardChanges()
{
    const QList<EditorPane *> panes = editors();
    const bool modified = std::any_of(panes.cbegin(), panes.cend(), [](EditorPane *pane) { return pane->isModified(); });
    const bool unsavedAi = std::any_of(m_aiHistoryPanes.cbegin(), m_aiHistoryPanes.cend(),
                                       [](const AiHistoryPane *pane) { return pane->filePath().isEmpty(); });
    if (!modified && !unsavedAi)
        return true;
    const auto choice = QMessageBox::warning(this, tr("Unsaved changes"),
        unsavedAi ? tr("Some AI results have not been saved. Save a copy before leaving this project.")
                  : tr("Some files have unsaved changes."),
        QMessageBox::Save | QMessageBox::Discard | QMessageBox::Cancel, QMessageBox::Save);
    if (choice == QMessageBox::Cancel)
        return false;
    return choice == QMessageBox::Discard || saveAll();
}

void MainWindow::saveSession()
{
    if (!hasProject() || m_shuttingDown)
        return;
    QJsonArray files;
    for (EditorPane *pane : editors()) {
        if (pane->isUnavailable()) continue;
        files.append(QJsonObject{{QStringLiteral("path"), m_project.relative(pane->filePath())},
                                 {QStringLiteral("state"), toJson(pane->sessionState())}});
    }
    if (m_layoutMode == LayoutMode::Split && m_splitter->isVisible())
        m_splitterSizes = m_splitter->sizes();
    QJsonArray sizes;
    for (int size : std::as_const(m_splitterSizes)) sizes.append(size);
    EditorPane *active = currentEditor() ? currentEditor() : m_lastEditor.data();
    QJsonObject session{
        {QStringLiteral("files"), files},
        {QStringLiteral("active"), active ? m_project.relative(active->filePath()) : QString()},
        {QStringLiteral("pdfTab"), m_layoutMode == LayoutMode::Tabbed && m_tabs->currentWidget() == m_pdfContainer},
        {QStringLiteral("splitter"), sizes},
        {QStringLiteral("preview"), m_previewDocument.isEmpty()
             ? (m_pdfView->path().isEmpty() ? QString() : m_project.relative(m_pdfView->path()))
             : m_project.relative(m_previewDocument)},
        {QStringLiteral("previewIsPdf"), m_previewDocument.isEmpty() && !m_pdfView->path().isEmpty()},
        {QStringLiteral("pdf"), toJson(m_pdfView->sessionState())},
        {QStringLiteral("messagesVisible"), m_outputDock->isVisible()},
        {QStringLiteral("aiHistoryVisible"), m_tabs->indexOf(m_aiWorkspace) >= 0},
    };
    m_project.setSession(session);
    QString error;
    if (!m_project.saveSettings(&error))
        statusBar()->showMessage(tr("Cannot save the workspace: %1").arg(error), 10000);
}

void MainWindow::restoreSession()
{
    const QJsonObject session = m_project.session();
    m_restoring = true;
    const QJsonArray files = session.value(QStringLiteral("files")).toArray();
    for (const QJsonValue &value : files) {
        const QJsonObject file = value.toObject();
        const QString path = m_project.absolute(file.value(QStringLiteral("path")).toString());
        if (!QFileInfo(path).isFile())
            continue;
        if (EditorPane *pane = openFile(path, false))
            pane->restoreSessionState(file.value(QStringLiteral("state")).toObject().toVariantMap());
    }
    // A new session opens only the main document, not every fragment (remark З1).
    if (editors().isEmpty() && !m_project.primaryDocument().isEmpty())
        openFile(m_project.primaryDocument(), false);
    const QJsonArray sizes = session.value(QStringLiteral("splitter")).toArray();
    if (sizes.size() == 2 && sizes.at(0).toInt() > 0 && sizes.at(1).toInt() > 0)
        m_splitterSizes = {sizes.at(0).toInt(), sizes.at(1).toInt()};
    setLayoutMode(m_layoutMode, false);
    m_restoring = false;
    const QString preview = session.value(QStringLiteral("preview")).toString();
    if (session.value(QStringLiteral("previewIsPdf")).toBool() && !preview.isEmpty()) {
        m_previewDocument.clear();
        m_pdfView->reload(m_project.absolute(preview));
        m_pdfLabel->setText(QFileInfo(preview).fileName());
    } else {
        setPreviewDocument(preview.isEmpty() ? m_project.primaryDocument() : m_project.absolute(preview));
    }
    m_pdfView->restoreSessionState(session.value(QStringLiteral("pdf")).toObject().toVariantMap());
    const QString active = session.value(QStringLiteral("active")).toString();
    if (EditorPane *pane = active.isEmpty() ? nullptr : editorFor(m_project.absolute(active)))
        m_tabs->setCurrentWidget(pane);
    else if (!editors().isEmpty())
        m_tabs->setCurrentWidget(editors().first());
    if (m_layoutMode == LayoutMode::Tabbed && session.value(QStringLiteral("pdfTab")).toBool())
        m_tabs->setCurrentWidget(m_pdfContainer);
    m_outputDock->setVisible(session.value(QStringLiteral("messagesVisible")).toBool());
    updateTabTitles();
}

void MainWindow::restoreStartupProject(const QString &explicitPath)
{
    const QString path = explicitPath.isEmpty()
        ? QSettings().value(QStringLiteral("projects/last")).toString() : explicitPath;
    if (path.isEmpty())
        return;
    if (!QFileInfo(path).isFile()) {
        QMessageBox::warning(this, tr("Cannot restore project"),
            tr("The file is unavailable: %1\nThe saved path has been kept. Check the file or mount, then open it again.")
                .arg(path));
        return;
    }
    openProject(path);
}

void MainWindow::addRecentProject(const QString &path)
{
    QSettings settings;
    QStringList recent = settings.value(QStringLiteral("projects/recent")).toStringList();
    recent.removeAll(path);
    recent.prepend(path);
    // Room for the twelve examples listed by the installer (С1) and the own projects.
    while (recent.size() > 20)
        recent.removeLast();
    settings.setValue(QStringLiteral("projects/recent"), recent);
    settings.setValue(QStringLiteral("projects/last"), path);
    rebuildRecentMenu();
}

void MainWindow::rebuildRecentMenu()
{
    m_recentMenu->clear();
    for (const QString &path : QSettings().value(QStringLiteral("projects/recent")).toStringList()) {
        if (!QFileInfo::exists(path))
            continue;
        QAction *action = m_recentMenu->addAction(QFileInfo(QFileInfo(path).absolutePath()).fileName()
                                                  + QStringLiteral(" / ") + QFileInfo(path).fileName(),
                                                  this, [this, path] { openProject(path); });
        action->setToolTip(path);
    }
    if (m_recentMenu->actions().isEmpty())
        m_recentMenu->addAction(tr("No recent projects"))->setEnabled(false);
}

void MainWindow::openProjectDialog()
{
    const QString path = QFileDialog::getOpenFileName(this, tr("Open project or document"),
        hasProject() ? m_project.root() : QDir::homePath(),
        tr("Primula projects and documents (*.prml);;All files (*)"));
    if (!path.isEmpty())
        openProject(path);
}

void MainWindow::openFileDialog()
{
    const QString path = QFileDialog::getOpenFileName(this, tr("Open file"),
        hasProject() ? m_project.root() : QDir::homePath(),
        tr("Text files (*.prml *.yaml *.yml *.csv *.json *.md *.txt);;PDF (*.pdf);;All files (*)"));
    if (path.isEmpty())
        return;
    // Without a project the file opens as one (its project is found as usual).
    if (!hasProject())
        openProject(path);
    else
        openFile(path);
}

void MainWindow::showSettings()
{
    QDialog dialog(this);
    dialog.setWindowTitle(tr("Settings"));
    auto *form = new QFormLayout;
    auto *translator = new QLineEdit(QSettings().value(QStringLiteral("tools/primula")).toString(), &dialog);
    translator->setPlaceholderText(Translator::program().isEmpty() ? tr("not found") : Translator::program());
    translator->setToolTip(tr("Empty: 'primula' from PATH, or the launcher of the source tree."));
    auto *browse = new QPushButton(tr("Browse…"), &dialog);
    connect(browse, &QPushButton::clicked, &dialog, [&dialog, translator] {
        const QString path = QFileDialog::getOpenFileName(&dialog, QObject::tr("Primula translator"));
        if (!path.isEmpty()) translator->setText(path);
    });
    auto *row = new QHBoxLayout;
    row->addWidget(translator, 1);
    row->addWidget(browse);
    form->addRow(tr("Primula translator:"), row);
    // AI tools (stages 14.10, 22.1, 22.6): the program of each tool of agents.json. Which tools a request goes to
    // is chosen in the request window.
    QStringList agentWarnings;
    const QList<AiAgent> agents = AiAgents::all(&agentWarnings);
    QMap<QString, QLineEdit *> programEdits;
    for (const AiAgent &agent : agents) {
        auto *edit = new QLineEdit(AiAgents::program(agent), &dialog);
        edit->setObjectName(QStringLiteral("aiProgram-") + agent.id);
        edit->setToolTip(tr("A name in PATH or a path. The tool is run read-only: see its description in agents.json."));
        auto *found = new QLabel(&dialog);
        found->setObjectName(QStringLiteral("aiProgramFound-") + agent.id);
        found->setTextFormat(Qt::PlainText);
        found->setMinimumWidth(160);
        auto update = [found, edit] {
            const QString program = edit->text().trimmed();
            const QString path = program.isEmpty() ? QString()
                                 : QFileInfo(program).isAbsolute() ? (QFileInfo(program).isExecutable() ? program : QString())
                                                                   : QStandardPaths::findExecutable(program);
            found->setText(path.isEmpty() ? tr("not found") : tr("found: %1").arg(path));
        };
        connect(edit, &QLineEdit::textChanged, &dialog, update);
        update();
        auto *row = new QHBoxLayout;
        row->addWidget(edit, 1);
        row->addWidget(found, 1);
        form->addRow(tr("%1:").arg(agent.name), row);
        programEdits.insert(agent.id, edit);
    }
    auto *agentFile = new QLabel(tr("More tools: %1").arg(AiAgents::userFile()), &dialog);
    agentFile->setObjectName(QStringLiteral("aiAgentFile"));
    agentFile->setTextFormat(Qt::PlainText);
    agentFile->setTextInteractionFlags(Qt::TextSelectableByMouse);
    agentFile->setWordWrap(true);
    form->addRow(QString(), agentFile);
    if (!agentWarnings.isEmpty()) {
        auto *problems = new QLabel(tr("Skipped in agents.json:\n%1").arg(agentWarnings.join(QLatin1Char('\n'))), &dialog);
        problems->setObjectName(QStringLiteral("aiAgentProblems"));
        problems->setTextFormat(Qt::PlainText);
        problems->setWordWrap(true);
        form->addRow(QString(), problems);
    }
    auto *version = new QLabel(Translator::version(), &dialog);
    form->addRow(tr("Translator version:"), version);
    auto *buttons = new QDialogButtonBox(QDialogButtonBox::Ok | QDialogButtonBox::Cancel, &dialog);
    connect(buttons, &QDialogButtonBox::accepted, &dialog, &QDialog::accept);
    connect(buttons, &QDialogButtonBox::rejected, &dialog, &QDialog::reject);
    auto *layout = new QVBoxLayout(&dialog);
    layout->addLayout(form);
    layout->addWidget(buttons);
    // The default size of a form is too small for the paths and the messages under the AI tool.
    dialog.resize(qMax(900, dialog.sizeHint().width() * 2), qMax(380, dialog.sizeHint().height() * 14 / 10));
    if (dialog.exec() != QDialog::Accepted)
        return;
    QSettings settings;
    settings.setValue(QStringLiteral("tools/primula"), translator->text().trimmed());
    for (const AiAgent &agent : agents) {
        const QString program = programEdits.value(agent.id)->text().trimmed();
        // Only a program that differs from the default is kept, so a new default of the tool applies.
        if (program.isEmpty() || program == agent.program) settings.remove(QStringLiteral("tools/") + agent.id);
        else settings.setValue(QStringLiteral("tools/") + agent.id, program);
    }
    updateUiState();
}

void MainWindow::editAiContextInDialog(QWidget *parent)
{
    QString error;
    if (!hasProject() || !m_project.ensureAiContext(&error)) {
        QMessageBox::warning(parent, tr("Cannot create the AI context"), error);
        return;
    }
    const QString path = m_project.aiContextPath();
    EditorPane *open = editorFor(path);
    QDialog dialog(parent);
    dialog.setWindowTitle(tr("AI context of the project"));
    dialog.resize(720, 460);
    auto *text = new QPlainTextEdit(fileText(path), &dialog);
    text->setObjectName(QStringLiteral("aiContextEditor"));
    auto *buttons = new QDialogButtonBox(QDialogButtonBox::Save | QDialogButtonBox::Cancel, &dialog);
    connect(buttons, &QDialogButtonBox::accepted, &dialog, &QDialog::accept);
    connect(buttons, &QDialogButtonBox::rejected, &dialog, &QDialog::reject);
    auto *layout = new QVBoxLayout(&dialog);
    layout->addWidget(new QLabel(tr("What AI should know about the documents: purpose, parties, terms, style of language. "
                                    "The text is added to every request."), &dialog));
    layout->addWidget(text, 1);
    layout->addWidget(new QLabel(path, &dialog));
    layout->addWidget(buttons);
    if (dialog.exec() != QDialog::Accepted) return;
    if (open) {
        // The file is open in a tab: its buffer takes the text (one Undo step) and is saved.
        QTextCursor cursor(open->editor()->document());
        cursor.beginEditBlock();
        cursor.select(QTextCursor::Document);
        cursor.insertText(text->toPlainText());
        cursor.endEditBlock();
        saveEditor(open);
        return;
    }
    QSaveFile file(path);
    if (!file.open(QIODevice::WriteOnly) || file.write(text->toPlainText().toUtf8()) < 0 || !file.commit())
        QMessageBox::warning(parent, tr("AI context of the project"), tr("The file could not be saved: %1").arg(path));
}

void MainWindow::editAiContext()
{
    if (!hasProject()) return;
    QString error;
    if (!m_project.ensureAiContext(&error)) {
        QMessageBox::warning(this, tr("Cannot create the AI context"), error);
        return;
    }
    openFile(m_project.aiContextPath());
}

void MainWindow::updateProjectWarning()
{
    const bool translatorMissing = Translator::program().isEmpty();
    m_projectWarning->setVisible(translatorMissing);
    if (translatorMissing)
        m_projectWarningText->setText(tr("The Primula translator is not found: Check and Build are unavailable. "
                                         "Install 'primula' into PATH or set its path in File → Settings."));
}

// ----------------------------------------------------------------------
// Tabs and editors
// ----------------------------------------------------------------------

QList<EditorPane *> MainWindow::editors() const
{
    QList<EditorPane *> result;
    for (int i = 0; i < m_tabs->count(); ++i)
        if (auto *pane = qobject_cast<EditorPane *>(m_tabs->widget(i)))
            result.append(pane);
    return result;
}

EditorPane *MainWindow::editorFor(const QString &path) const
{
    for (EditorPane *pane : editors())
        if (samePath(pane->filePath(), path))
            return pane;
    return nullptr;
}

EditorPane *MainWindow::currentEditor() const
{
    if (m_shuttingDown) return nullptr;
    return qobject_cast<EditorPane *>(m_tabs->currentWidget());
}

EditorPane *MainWindow::openFile(const QString &path, bool activate)
{
    const QString absolute = QFileInfo(path).absoluteFilePath();
    const QString suffix = QFileInfo(absolute).suffix().toLower();
    // The file type decides first (С2): a command of the user or the program of the desktop;
    // "editor" and "preview" continue below (the editor still refuses binary files).
    if (const FileType *type = m_fileTypes.typeOf(absolute)) {
        if (type->open == QStringLiteral("command")) {
            runFileCommand(*type, absolute);
            return nullptr;
        }
        if (type->open == QStringLiteral("system")) {
            QDesktopServices::openUrl(QUrl::fromLocalFile(absolute));
            return nullptr;
        }
    }
    if (suffix == QStringLiteral("pdf")) {
        m_previewDocument.clear();
        m_pdfView->reload(absolute);
        m_pdfLabel->setText(QFileInfo(absolute).fileName());
        if (activate) showPdfTab();
        return nullptr;
    }
    // ODT goes to Writer, images and other binary files to the system viewer: the editor is for text.
    static const QStringList external{QStringLiteral("odt"), QStringLiteral("png"), QStringLiteral("jpg"),
                                      QStringLiteral("jpeg"), QStringLiteral("gif"), QStringLiteral("webp"),
                                      QStringLiteral("bmp"), QStringLiteral("tif"), QStringLiteral("tiff"),
                                      QStringLiteral("svg")};
    if (external.contains(suffix) || isBinaryFile(absolute)) {
        QDesktopServices::openUrl(QUrl::fromLocalFile(absolute));
        return nullptr;
    }
    return openFileAsText(absolute, activate);
}

EditorPane *MainWindow::openFileAsText(const QString &path, bool activate)
{
    const QString absolute = QFileInfo(path).absoluteFilePath();
    if (EditorPane *existing = editorFor(absolute)) {
        if (activate) m_tabs->setCurrentWidget(existing);
        return existing;
    }
    auto *pane = new EditorPane(m_tabs);
    QString error;
    // Modules of the standard library (reached from the Styles panel) are shown read-only.
    const bool library = absolute.contains(QStringLiteral("/primula/stdlib/"));
    if (!pane->loadFile(absolute, library, syntaxFor(absolute), &error)) {
        pane->deleteLater();
        if (!m_restoring)
            QMessageBox::warning(this, tr("Cannot open file"), error);
        return nullptr;
    }
    // New tabs go before the PDF tab of the tabbed layout.
    const int pdfIndex = m_tabs->indexOf(m_pdfContainer);
    const int index = m_tabs->insertTab(pdfIndex >= 0 ? pdfIndex : m_tabs->count(), pane, shortName(absolute));
    m_tabs->setTabToolTip(index, absolute);
    connect(pane, &EditorPane::modificationChanged, this, [this] { updateTabTitles(); updateWindowTitle(); });
    connect(pane->editor()->document(), &QTextDocument::contentsChanged, this, &MainWindow::scheduleInspection);
    connect(pane->editor(), &QPlainTextEdit::cursorPositionChanged, this, [this, pane] {
        if (pane == currentEditor())
            m_structurePanel->followCursor(pane->filePath(), pane->editor()->textCursor().blockNumber() + 1);
    });
    // Documents and code files (styles modules, projects: code after the header) alike.
    if (pane->syntax() == CodeEditor::Syntax::Primula || pane->syntax() == CodeEditor::Syntax::PrimulaCode)
        m_assist->attach(pane->editor());
    connect(pane->editor(), &CodeEditor::fontZoomRequested, this,
            [this](int steps) { setEditorFontSize(m_fontSize->value() + steps); });
    applyEditorFont();
    QStringList watched;
    for (EditorPane *editor : editors()) watched.append(editor->filePath());
    m_fileMonitor->setFiles(watched);
    updateTabTitles();
    if (activate) {
        m_tabs->setCurrentWidget(pane);
        pane->editor()->setFocus();
    }
    return pane;
}

bool MainWindow::closeEditor(EditorPane *pane)
{
    if (!pane) return false;
    if (pane->isModified()) {
        m_tabs->setCurrentWidget(pane);
        const auto choice = QMessageBox::warning(this, tr("Unsaved changes"),
            tr("Save changes to %1?").arg(QFileInfo(pane->filePath()).fileName()),
            QMessageBox::Save | QMessageBox::Discard | QMessageBox::Cancel, QMessageBox::Save);
        if (choice == QMessageBox::Cancel || (choice == QMessageBox::Save && !saveEditor(pane)))
            return false;
    }
    m_tabs->removeTab(m_tabs->indexOf(pane));
    pane->deleteLater();
    QStringList watched;
    for (EditorPane *editor : editors()) watched.append(editor->filePath());
    m_fileMonitor->setFiles(watched);
    updateTabTitles();
    updateUiState();
    updateWindowTitle();
    saveSession();
    return true;
}

void MainWindow::closeOtherEditors(EditorPane *keep)
{
    for (EditorPane *pane : editors())
        if (pane != keep && !closeEditor(pane))
            return;
}

bool MainWindow::saveEditor(EditorPane *pane)
{
    QString error;
    // An option: the version on the disk is kept before it is replaced (the same version is not kept twice).
    if (hasProject() && pane->isModified() && QFileInfo::exists(pane->filePath())
        && QSettings().value(QStringLiteral("backups/beforeSave"), false).toBool())
        backupFiles({pane->filePath()}, QStringLiteral("before-save"), QString(), false);
    if (!pane->save(&error)) {
        QMessageBox::critical(this, tr("Cannot save file"), error);
        return false;
    }
    updateTabTitles();
    updateWindowTitle();
    checkExternalFiles();
    const QString saved = QFileInfo(pane->filePath()).absoluteFilePath();
    if (saved == QFileInfo(FileTypes::userFile()).absoluteFilePath()
        || (hasProject() && saved == QFileInfo(FileTypes::projectFile(m_project.root())).absoluteFilePath())) {
        reloadFileTypes();
        statusBar()->showMessage(m_fileTypes.problems().isEmpty() ? tr("File types applied")
                                                                  : tr("File types applied with problems (see the Log)"), 4000);
    }
    return true;
}

bool MainWindow::saveAll()
{
    for (AiHistoryPane *pane : std::as_const(m_aiHistoryPanes))
        if (pane->filePath().isEmpty() && !pane->saveCopy()) return false;
    for (EditorPane *pane : editors())
        if (pane->isModified() && !saveEditor(pane))
            return false;
    statusBar()->showMessage(tr("All files saved"), 2500);
    return true;
}

void MainWindow::updateTabTitles()
{
    const QList<EditorPane *> panes = editors();
    QStringList paths;
    for (EditorPane *pane : panes) paths.append(pane->filePath());
    const QStringList titles = tabTitles(paths);
    for (int i = 0; i < panes.size(); ++i) {
        const int index = m_tabs->indexOf(panes.at(i));
        QString title = titles.at(i);
        if (panes.at(i)->isUnavailable()) title += tr(" [missing]");
        if (panes.at(i)->isModified()) title += QStringLiteral(" *");
        m_tabs->setTabText(index, title);
        m_tabs->setTabToolTip(index, panes.at(i)->filePath());
    }
}

void MainWindow::showOpenFilesMenu()
{
    QMenu menu(this);
    for (int i = 0; i < m_tabs->count(); ++i) {
        QWidget *widget = m_tabs->widget(i);
        QAction *action = menu.addAction(m_tabs->tabText(i), this, [this, widget] {
            m_tabs->setCurrentWidget(widget);
            if (auto *pane = qobject_cast<EditorPane *>(widget)) pane->editor()->setFocus();
        });
        action->setToolTip(m_tabs->tabToolTip(i));
        if (widget == m_tabs->currentWidget()) menu.setActiveAction(action);
    }
    if (menu.isEmpty()) return;
    menu.exec(mapToGlobal(rect().center() - QPoint(menu.sizeHint().width() / 2, menu.sizeHint().height() / 2)));
}

void MainWindow::setLayoutMode(LayoutMode mode, bool persist)
{
    const QVariantMap pdfState = m_pdfView->sessionState();
    if (m_layoutMode == LayoutMode::Split && m_splitter->isVisible() && m_splitter->count() == 2)
        m_splitterSizes = m_splitter->sizes();
    m_layoutMode = mode;
    QWidget *current = m_tabs->currentWidget();
    if (mode == LayoutMode::Tabbed) {
        if (m_tabs->indexOf(m_pdfContainer) < 0) {
            const int index = m_tabs->addTab(m_pdfContainer, tr("PDF"));
            m_tabs->tabBar()->setTabButton(index, QTabBar::RightSide, nullptr);
            m_tabs->tabBar()->setTabButton(index, QTabBar::LeftSide, nullptr);
        }
    } else {
        const int index = m_tabs->indexOf(m_pdfContainer);
        if (index >= 0) m_tabs->removeTab(index);
        m_splitter->addWidget(m_pdfContainer);
        m_pdfContainer->show();
        m_splitter->setSizes(m_splitterSizes);
    }
    if (current && m_tabs->indexOf(current) >= 0)
        m_tabs->setCurrentWidget(current);
    if (m_splitAction) m_splitAction->setChecked(mode == LayoutMode::Split);
    if (m_tabbedAction) m_tabbedAction->setChecked(mode == LayoutMode::Tabbed);
    if (!pdfState.isEmpty()) m_pdfView->restoreSessionState(pdfState);
    if (persist)
        QSettings().setValue(QStringLiteral("ui/layout"), mode == LayoutMode::Tabbed ? QStringLiteral("tabs")
                                                                                       : QStringLiteral("split"));
}

void MainWindow::showPdfTab()
{
    if (m_layoutMode == LayoutMode::Tabbed)
        m_tabs->setCurrentWidget(m_pdfContainer);
    m_pdfView->setFocus();
}

void MainWindow::togglePdf()
{
    const bool pdfActive = m_layoutMode == LayoutMode::Tabbed ? m_tabs->currentWidget() == m_pdfContainer
                                                              : m_pdfView->hasFocus();
    if (pdfActive) {
        if (m_lastEditor) {
            m_tabs->setCurrentWidget(m_lastEditor);
            m_lastEditor->editor()->setFocus();
        }
        return;
    }
    // The page of the heading before the cursor, through the PDF bookmarks (remark З5).
    const int page = pdfPageForCursor();
    if (page >= 0)
        m_pdfView->showPage(page);
    showPdfTab();
}

// ----------------------------------------------------------------------
// Build, check, messages
// ----------------------------------------------------------------------

QString MainWindow::currentDocument() const
{
    EditorPane *pane = currentEditor() ? currentEditor() : m_lastEditor.data();
    if (pane && primulaKind(pane->filePath()) == QStringLiteral("document"))
        return pane->filePath();
    // A fragment, module or styles module is checked within the document shown in the PDF.
    if (!m_previewDocument.isEmpty())
        return m_previewDocument;
    return m_project.primaryDocument();
}

void MainWindow::runCheck()
{
    const QString document = currentDocument();
    if (!hasProject() || document.isEmpty() || m_buildController->isRunning() || !saveAll())
        return;
    QStringList arguments{QStringLiteral("check"), m_project.relative(document)};
    arguments << parameterArguments(document);
    if (m_strictAction->isChecked()) arguments << QStringLiteral("--strict");
    m_buildDocument = document;
    m_output->clear();
    m_buildController->start(BuildController::Kind::Check, arguments, m_project.root());
}

// ----------------------------------------------------------------------
// Parallel tracks (7.7, stage 16.6)
// ----------------------------------------------------------------------

QStringList MainWindow::parallelTracks() const
{
    QStringList tracks;
    if (m_structureDocument != currentDocument()) return tracks;
    for (const QJsonValue &value : m_structure) {
        const QJsonObject item = value.toObject();
        if (item.value(QStringLiteral("kind")).toString() != QStringLiteral("parallel")) continue;
        const QString primary = item.value(QStringLiteral("primary")).toString();
        for (const QJsonValue &track : item.value(QStringLiteral("tracks")).toArray()) {
            const QString id = track.toObject().value(QStringLiteral("id")).toString();
            if (id != primary && !tracks.contains(id)) tracks << id;
        }
    }
    return tracks;
}

QPair<QString, QString> MainWindow::parallelPlaceAt(const QString &path, int line) const
{
    QString segment, track;
    if (m_structureDocument != currentDocument() || line < 1) return {};
    for (const QJsonValue &value : m_structure) {
        const QJsonObject item = value.toObject();
        if (!samePath(item.value(QStringLiteral("path")).toString(), path)
            || item.value(QStringLiteral("line")).toInt() > line)
            continue;
        const QString kind = item.value(QStringLiteral("kind")).toString();
        if (kind == QStringLiteral("parallel")) {
            segment.clear();
            track.clear();
        } else if (kind == QStringLiteral("segment")) {
            segment = item.value(QStringLiteral("id")).toString();
            track.clear();
        } else if (kind == QStringLiteral("track_block")) {
            track = item.value(QStringLiteral("track")).toString();
        }
    }
    return {segment, track};
}

std::optional<QString> MainWindow::askTrackStatus(const QString &title, bool keepChoice)
{
    QStringList items;
    if (keepChoice) items << tr("(do not change the status)");
    items << QStringLiteral("reviewed") << QStringLiteral("translated") << QStringLiteral("draft");
    bool ok = false;
    const QString chosen = QInputDialog::getItem(this, title, keepChoice ? tr("Status to write (or type your own):")
                                                                         : tr("Expected status:"),
                                                 items, 0, true, &ok);
    if (!ok) return std::nullopt;
    if (keepChoice && chosen == items.first()) return QString();
    return chosen.trimmed();
}

void MainWindow::fillParallelMenu(QMenu *menu, const QString &path, int line)
{
    menu->clear();
    const QStringList tracks = parallelTracks();
    if (tracks.isEmpty()) {
        // No silent menu: say why there is nothing to do.
        menu->addAction(tr("The document has no |parallel (or it is not inspected yet)"))->setEnabled(false);
        return;
    }
    auto chooseTrack = [this, tracks](const QString &title) -> QString {
        if (tracks.size() == 1) return tracks.first();
        bool ok = false;
        const QString track = QInputDialog::getItem(this, title, tr("Track:"), tracks, 0, false, &ok);
        return ok ? track : QString();
    };
    const auto [segment, track] = parallelPlaceAt(path, line);
    const bool here = !segment.isEmpty() && tracks.contains(track);
    QAction *stampHere = menu->addAction(
        here ? tr("Confirm the translation of segment %1, track %2…").arg(segment, track)
             : tr("Confirm the translation of this segment (put the cursor into a block of a translation)"),
        this, [this, segment, track] {
            const std::optional<QString> status = askTrackStatus(tr("Confirm the translation"), true);
            if (!status) return;
            QStringList options{QStringLiteral("--stamp"), QStringLiteral("--track"), track,
                                QStringLiteral("--segment"), segment};
            if (!status->isEmpty()) options << QStringLiteral("--status") << *status;
            runParallelTool(options);
        });
    stampHere->setEnabled(here);
    menu->addAction(tr("Confirm all blocks of a track…"), this, [this, chooseTrack] {
        const QString chosen = chooseTrack(tr("Confirm all blocks of a track"));
        if (chosen.isEmpty()) return;
        const std::optional<QString> status = askTrackStatus(tr("Confirm all blocks of %1").arg(chosen), true);
        if (!status) return;
        QStringList options{QStringLiteral("--stamp"), QStringLiteral("--track"), chosen};
        if (!status->isEmpty()) options << QStringLiteral("--status") << *status;
        runParallelTool(options);
    });
    menu->addAction(tr("Write blank blocks of a track…"), this, [this, chooseTrack] {
        const QString chosen = chooseTrack(tr("Write blank blocks"));
        if (!chosen.isEmpty()) runParallelTool({QStringLiteral("--stub"), QStringLiteral("--track"), chosen});
    });
    menu->addSeparator();
    menu->addAction(tr("Check the status of the translations…"), this, [this] {
        const std::optional<QString> status = askTrackStatus(tr("Check the status of the translations"), false);
        if (status && !status->isEmpty()) runParallelTool({QStringLiteral("--check-status"), *status});
    });
}

void MainWindow::runParallelTool(const QStringList &options)
{
    const QString document = currentDocument();
    if (!hasProject() || document.isEmpty() || m_buildController->isRunning() || !saveAll())
        return;
    QStringList arguments{QStringLiteral("parallel"), m_project.relative(document)};
    arguments << options << parameterArguments(document);
    m_buildDocument = document;
    m_output->clear();
    m_buildController->start(BuildController::Kind::Tool, arguments, m_project.root());
}

void MainWindow::runBuild(bool wholeProject)
{
    if (!hasProject() || m_buildController->isRunning() || !saveAll())
        return;
    QStringList arguments{QStringLiteral("build")};
    if (wholeProject) {
        if (!m_project.hasProjectFile()) return;
        arguments << m_project.relative(m_project.projectFile()) << QStringLiteral("--pdf");
        m_buildDocument = m_previewDocument.isEmpty() ? m_project.primaryDocument() : m_previewDocument;
    } else {
        const QString document = currentDocument();
        if (document.isEmpty()) return;
        const BuildTarget outputs = m_project.outputsFor(document);
        arguments << m_project.relative(document) << QStringLiteral("-o") << m_project.relative(outputs.output)
                  << QStringLiteral("--pdf") << m_project.relative(outputs.pdf) << parameterArguments(document);
        m_buildDocument = document;
    }
    if (m_strictAction->isChecked()) arguments << QStringLiteral("--strict");
    m_output->clear();
    m_buildController->start(BuildController::Kind::Build, arguments, m_project.root());
}

QJsonObject MainWindow::savedParameters(const QString &document) const
{
    if (!hasProject() || document.isEmpty()) return {};
    return m_project.group(QStringLiteral("build")).value(QStringLiteral("params")).toObject()
        .value(m_project.relative(document)).toObject();
}

void MainWindow::setSavedParameters(const QString &document, const QJsonObject &values)
{
    QJsonObject build = m_project.group(QStringLiteral("build"));
    QJsonObject all = build.value(QStringLiteral("params")).toObject();
    if (values.isEmpty()) all.remove(m_project.relative(document));
    else all.insert(m_project.relative(document), values);
    if (all.isEmpty()) build.remove(QStringLiteral("params"));
    else build.insert(QStringLiteral("params"), all);
    m_project.setGroup(QStringLiteral("build"), build);
    m_project.saveSettings();
}

QStringList MainWindow::parameterArguments(const QString &document) const
{
    QStringList arguments;
    const QJsonObject values = savedParameters(document);
    for (auto it = values.begin(); it != values.end(); ++it)
        arguments << QStringLiteral("--param") << it.key() + QLatin1Char('=') + it.value().toString();
    return arguments;
}

void MainWindow::showBuildParameters()
{
    const QString document = currentDocument();
    if (!hasProject() || document.isEmpty() || primulaKind(document) != QStringLiteral("document")) return;
    // The declared parameters, read without the saved values (their defaults).
    QByteArray output;
    QString errors;
    QStringList arguments{QStringLiteral("check"), m_project.relative(document), QStringLiteral("--dump-structure")};
    if (EditorPane *open = editorFor(document); open && open->isModified())
        statusBar()->showMessage(tr("The saved file is read; unsaved changes of the header are not taken into account."), 8000);
    Translator::run(arguments, m_project.root(), &output, &errors, 30000);
    const QJsonObject dump = QJsonDocument::fromJson(output).object();
    if (!dump.contains(QStringLiteral("params"))) {
        QMessageBox::warning(this, tr("Document parameters"),
                             tr("The translator did not report the parameters of the document.\n%1").arg(errors.trimmed()));
        return;
    }
    const QJsonObject params = dump.value(QStringLiteral("params")).toObject();
    const QJsonObject saved = savedParameters(document);
    QDialog dialog(this);
    const QString name = QFileInfo(document).fileName();
    dialog.setWindowTitle(tr("Build parameters of %1").arg(name));
    dialog.resize(760, 520);
    auto *table = new QTableWidget(int(params.size()), 4, &dialog);
    table->setObjectName(QStringLiteral("parametersTable"));
    table->setHorizontalHeaderLabels({tr("Parameter"), tr("Type"), tr("Default (declared in)"), tr("✎ Value for Check and Build")});
    table->horizontalHeader()->setSectionResizeMode(QHeaderView::Interactive);
    table->horizontalHeader()->setStretchLastSection(true);
    table->verticalHeader()->hide();
    // The value column is edited at once: a click or typing starts the editor.
    table->setEditTriggers(QAbstractItemView::AllEditTriggers);
    const QBrush fixedText = table->palette().brush(QPalette::Disabled, QPalette::Text);
    const QBrush valueBackground = table->palette().brush(QPalette::AlternateBase);
    int row = 0;
    // Saved values of parameters no longer declared are dropped on OK.
    for (auto it = params.begin(); it != params.end(); ++it, ++row) {
        const QJsonObject param = it.value().toObject();
        auto fixed = [&fixedText](const QString &text) {
            auto *item = new QTableWidgetItem(text);
            item->setFlags(item->flags() & ~Qt::ItemIsEditable);
            item->setForeground(fixedText);
            return item;
        };
        const QString type = param.value(QStringLiteral("type")).toString();
        const QString defaultValue = param.value(QStringLiteral("default")).toString();
        table->setItem(row, 0, fixed(it.key()));
        table->item(row, 0)->setForeground(table->palette().brush(QPalette::Text));
        table->setItem(row, 1, fixed(type));
        const QString origin = param.value(QStringLiteral("origin")).toString() == QStringLiteral("project")
                                   ? tr("project") : tr("document");
        table->setItem(row, 2, fixed(defaultValue + QStringLiteral("  (") + origin + QLatin1Char(')')));
        auto *value = new QTableWidgetItem(saved.value(it.key()).toString());
        value->setBackground(valueBackground);
        value->setToolTip(tr("Empty — the default %1").arg(defaultValue));
        table->setItem(row, 3, value);
        // true/false and dates: a list to choose from (the empty entry keeps the default).
        if (type == QStringLiteral("bool") || type == QStringLiteral("datetime")) {
            auto *choice = new QComboBox(table);
            choice->setEditable(type == QStringLiteral("datetime"));
            choice->addItem(QString());
            if (type == QStringLiteral("bool")) choice->addItems({QStringLiteral("true"), QStringLiteral("false")});
            else choice->addItems({QDate::currentDate().toString(Qt::ISODate), defaultValue});
            choice->setCurrentText(value->text());
            choice->setToolTip(value->toolTip());
            connect(choice, &QComboBox::currentTextChanged, choice, [value](const QString &text) { value->setText(text); });
            table->setCellWidget(row, 3, choice);
        }
    }
    table->resizeColumnsToContents();
    auto *note = new QLabel(&dialog);
    note->setObjectName(QStringLiteral("parametersNote"));
    note->setWordWrap(true);
    note->setTextFormat(Qt::RichText);
    note->setFrameShape(QFrame::StyledPanel);
    note->setMargin(8);
    note->setAutoFillBackground(true);
    note->setBackgroundRole(QPalette::ToolTipBase);
    note->setForegroundRole(QPalette::ToolTipText);
    // What the window is for: the remark of 16.10.2026 — it was not clear from the context.
    note->setText(tr("<b>What this is.</b> The parameters (<code>params:</code>) that the project and the document "
                     "<b>%1</b> declare, with their defaults. Here you give them other values for this document "
                     "without editing any file — as <code>primula build %1 --param NAME=VALUE</code> would.<br>"
                     "<b>Where they act.</b> Check, Build and the document inspection in Studio, and the console "
                     "with the context «Current file». Building all targets of the project does not use them: a "
                     "target sets its own <code>params</code>.<br>"
                     "<b>How.</b> Click a cell of the last column and type; an empty cell keeps the default. Values "
                     "are written as in <code>--param</code>: text, <code>true</code>/<code>false</code>, numbers, "
                     "dates <code>2026-10-16</code>. They are kept in <code>.primula-studio/settings.json</code> of the "
                     "project; Reset clears them. «Default (declared in)» tells whether the project or the document "
                     "declares the parameter; a document parameter overrides that of the project.").arg(name.toHtmlEscaped()));
    if (params.isEmpty())
        note->setText(tr("Neither the project nor the document <b>%1</b> declares parameters (<code>params:</code>): "
                         "there is nothing to set here.").arg(name.toHtmlEscaped()) + QStringLiteral("<br><br>") + note->text());
    auto *buttons = new QDialogButtonBox(QDialogButtonBox::Ok | QDialogButtonBox::Cancel | QDialogButtonBox::Reset, &dialog);
    connect(buttons, &QDialogButtonBox::accepted, &dialog, &QDialog::accept);
    connect(buttons, &QDialogButtonBox::rejected, &dialog, &QDialog::reject);
    connect(buttons->button(QDialogButtonBox::Reset), &QPushButton::clicked, &dialog, [table] {
        for (int i = 0; i < table->rowCount(); ++i) {
            table->item(i, 3)->setText(QString());
            if (auto *choice = qobject_cast<QComboBox *>(table->cellWidget(i, 3))) choice->setCurrentIndex(0);
        }
    });
    auto *layout = new QVBoxLayout(&dialog);
    layout->addWidget(table, 1);
    layout->addWidget(note);
    layout->addWidget(buttons);
    if (dialog.exec() != QDialog::Accepted) return;
    QJsonObject values;
    for (int i = 0; i < table->rowCount(); ++i) {
        const QString value = table->item(i, 3)->text().trimmed();
        if (!value.isEmpty()) values.insert(table->item(i, 0)->text(), value);
    }
    setSavedParameters(document, values);
    updateUiState();
    scheduleInspection();
}

MainWindow::ConsoleTargetData MainWindow::consoleTarget(const QString &mode)
{
    ConsoleTargetData data;
    data.arguments << QStringLiteral("--lang") << interfaceLanguage();
    data.directory = hasProject() ? m_project.root() : QDir::homePath();
    if (mode == QStringLiteral("library") || !hasProject()) {
        data.arguments << QStringLiteral("--no-project");
        data.description = tr("Console: the standard library");
        return data;
    }
    EditorPane *pane = currentEditor() ? currentEditor() : m_lastEditor.data();
    const QString file = mode == QStringLiteral("file") && pane && !primulaKind(pane->filePath()).isEmpty()
                             ? pane->filePath() : QString();
    if (file.isEmpty()) {
        if (m_project.hasProjectFile()) data.arguments << m_project.relative(m_project.projectFile());
        data.description = tr("Console: the project %1").arg(m_project.name());
        return data;
    }
    // The saved file is read; a document gets its build parameters (С-В5).
    if (pane->isModified()) pane->save();
    data.arguments << m_project.relative(file);
    if (primulaKind(file) == QStringLiteral("document")) data.arguments << parameterArguments(file);
    data.description = tr("Console: %1 (%2)").arg(m_project.relative(file), primulaKind(file));
    return data;
}

void MainWindow::addHeaderFields(CodeEditor *target)
{
    // The editor of the context menu, else the current one.
    EditorPane *pane = nullptr;
    if (target) {
        for (EditorPane *candidate : editors())
            if (candidate->editor() == target) pane = candidate;
    }
    if (!pane) pane = editTarget();
    if (!pane) return;
    const QString file = QFileInfo(pane->filePath()).fileName();
    const QString kind = HeaderAssist::kind(pane->editor()->document(), primulaKind(pane->filePath()));
    const QString section = HeaderAssist::metadataKey(kind);
    if (section.isEmpty()) {
        QMessageBox::information(this, tr("Header fields"),
                                 tr("%1 is a file of kind %2: document metadata belong to a document (doc:) "
                                    "or to a project file (doc_defaults:).").arg(file, kind));
        return;
    }
    // The recommended keys of the catalogue (decision 129: doc — title, creator, language,
    // created; doc_defaults — creator, organization) with proposed values.
    QStringList recommended;
    if (ensureCatalog())
        for (const CommandCatalog::HeaderKey &key : m_catalog.headerKeys())
            if (key.recommended && key.kinds.contains(kind) && key.path.startsWith(section + QLatin1Char('.')))
                recommended << key.path.mid(section.size() + 1);
    if (recommended.isEmpty())
        recommended = kind == QStringLiteral("project") ? QStringList{QStringLiteral("creator"), QStringLiteral("organization")}
                                                        : QStringList{QStringLiteral("title"), QStringLiteral("creator"),
                                                                      QStringLiteral("language"), QStringLiteral("created")};
    QList<HeaderAssist::Field> fields;
    for (const QString &name : recommended) {
        if (name == QStringLiteral("title")) fields.append({name, QFileInfo(pane->filePath()).completeBaseName(), true});
        else if (name == QStringLiteral("creator")) fields.append({name, tr("Author"), true});
        else if (name == QStringLiteral("organization")) fields.append({name, tr("Organization"), true});
        else if (name == QStringLiteral("language"))
            fields.append({name, m_project.language().isEmpty() ? QStringLiteral("uk-UA") : m_project.language(), false});
        else if (name == QStringLiteral("created")) fields.append({name, QDate::currentDate().toString(Qt::ISODate), false});
        else fields.append({name, QString(), true});
    }
    int position = 0;
    QString snippet;
    QString error;
    QStringList added;
    if (!HeaderAssist::addFields(pane->editor()->document(), kind, fields, &position, &snippet, &error, &added)) {
        // Always a message: nothing to add is an answer too (remark of 16.10.2026).
        QMessageBox::information(this, tr("Header fields"),
                                 error.isEmpty()
                                     ? tr("Nothing to add: %1: in %2 already has %3.")
                                           .arg(section, file, recommended.join(QStringLiteral(", ")))
                                     : tr("%1: in %2 is written as {…}; add the fields by hand.").arg(section, file));
        return;
    }
    QTextCursor cursor(pane->editor()->document());
    cursor.setPosition(position);
    cursor.beginEditBlock();
    m_assist->insertSnippet(pane->editor(), cursor, snippet, false);
    cursor.endEditBlock();
    pane->editor()->setTextCursor(cursor);
    pane->editor()->ensureCursorVisible();
    QMessageBox::information(this, tr("Header fields"),
                             tr("Added to %1, %2: %3.\nThe values are proposals: Tab goes from one to the next.")
                                 .arg(file, section + QLatin1Char(':'), added.join(QStringLiteral(", "))));
    pane->editor()->setFocus();
}

void MainWindow::buildFinished(bool success, BuildController::Kind kind)
{
    const bool build = kind == BuildController::Kind::Build;
    if (kind == BuildController::Kind::Export) {
        showMessages(m_buildController->messages());
        const QString target = m_exportTarget;
        m_exportTarget.clear();
        bool noPandoc = false;
        for (const QJsonValue &message : m_buildController->messages())
            noPandoc = noPandoc || message.toObject().value(QStringLiteral("code")).toString() == QStringLiteral("P8102");
        if (success && QFileInfo::exists(target)) {
            statusBar()->showMessage(tr("Exported: %1").arg(QFileInfo(target).fileName()), 5000);
            auto *box = new QMessageBox(QMessageBox::Information, tr("Export"), tr("The document is exported to\n%1").arg(target),
                                        QMessageBox::Close, this);
            box->setAttribute(Qt::WA_DeleteOnClose);
            QPushButton *open = box->addButton(tr("Open the file"), QMessageBox::ActionRole);
            QPushButton *folder = box->addButton(tr("Open the folder"), QMessageBox::ActionRole);
            connect(open, &QPushButton::clicked, this, [target] { QDesktopServices::openUrl(QUrl::fromLocalFile(target)); });
            connect(folder, &QPushButton::clicked, this,
                    [target] { QDesktopServices::openUrl(QUrl::fromLocalFile(QFileInfo(target).absolutePath())); });
            m_exportNotice = box;
            box->open();
        } else if (noPandoc) {
            statusBar()->showMessage(tr("Export needs pandoc"), 5000);
            auto *box = new QMessageBox(QMessageBox::Warning, tr("Export"),
                tr("Export to this format needs pandoc, and it is not found.\n\nInstall pandoc (https://pandoc.org; "
                   "openSUSE: zypper install pandoc; Debian: apt install pandoc) and export again. "
                   "The format JSON (the pandoc AST) needs no pandoc."), QMessageBox::Close, this);
            box->setAttribute(Qt::WA_DeleteOnClose);
            m_exportNotice = box;
            box->open();
        } else {
            statusBar()->showMessage(tr("Export failed"), 5000);
            if (m_diagnostics->topLevelItemCount() == 0) {
                static_cast<QTabWidget *>(m_outputDock->widget())->setCurrentWidget(m_output);
            }
            m_outputDock->show();
        }
        updateUiState();
        return;
    }
    if (kind == BuildController::Kind::Tool) {
        statusBar()->showMessage(success ? tr("primula parallel completed") : tr("primula parallel found problems"),
                                 5000);
        // The command lists what it did (stamped segments, blanks): show the log.
        static_cast<QTabWidget *>(m_outputDock->widget())->setCurrentWidget(m_output);
        m_outputDock->show();
        // The file was rewritten by the translator: reload the editors that have no own changes.
        for (EditorPane *pane : editors()) {
            if (!pane->diskChanged() || pane->isModified()) continue;
            const QVariantMap state = pane->sessionState();
            QString error;
            if (pane->loadFile(pane->filePath(), pane->isReadOnly(), pane->syntax(), &error))
                pane->restoreSessionState(state);
        }
        checkExternalFiles();
    } else {
        statusBar()->showMessage(success ? (build ? tr("Build completed") : tr("Check completed"))
                                         : (build ? tr("Build failed") : tr("Check found errors")), 5000);
    }
    showMessages(m_buildController->messages());
    if (!success && m_diagnostics->topLevelItemCount() == 0) {
        // No JSON (the translator did not start or crashed): the log tells why.
        static_cast<QTabWidget *>(m_outputDock->widget())->setCurrentWidget(m_output);
        m_outputDock->show();
    }
    if (build && success) {
        const bool pdfWasVisible = m_layoutMode == LayoutMode::Split || m_tabs->currentWidget() == m_pdfContainer;
        setPreviewDocument(m_buildDocument);
        const QString mode = pdfAfterBuildMode();
        if (mode == QStringLiteral("always") || (mode == QStringLiteral("visible") && pdfWasVisible))
            showPdfTab();
    }
    scheduleInspection();
    updateUiState();
}

void MainWindow::showMessages(const QJsonArray &messages)
{
    m_diagnostics->clear();
    for (const QJsonValue &value : messages) {
        const QJsonObject message = value.toObject();
        const QString severity = message.value(QStringLiteral("severity")).toString();
        const QString file = message.value(QStringLiteral("file")).toString();
        const int line = message.value(QStringLiteral("line")).toInt();
        const QString code = message.value(QStringLiteral("code")).toString();
        const QString label = severity == QStringLiteral("error") ? tr("Error")
                            : severity == QStringLiteral("warning") ? tr("Warning") : severity;
        auto *item = new QTreeWidgetItem(m_diagnostics,
            {QStringLiteral("%1 [%2]: %3").arg(label, code, message.value(QStringLiteral("message")).toString()),
             file, line > 0 ? QString::number(line) : QString()});
        item->setData(0, Qt::UserRole, file.isEmpty() ? QString() : m_project.absolute(file));
        item->setData(0, Qt::UserRole + 1, line);
        item->setData(0, Qt::UserRole + 2, message.value(QStringLiteral("column")).toInt());
        item->setIcon(0, style()->standardIcon(severity == QStringLiteral("error") ? QStyle::SP_MessageBoxCritical
                                                                                   : QStyle::SP_MessageBoxWarning));
        QStringList tip{item->text(0)};
        for (const QJsonValue &note : message.value(QStringLiteral("notes")).toArray())
            tip.append(QStringLiteral("  %1: %2").arg(note.toObject().value(QStringLiteral("kind")).toString(),
                                                    note.toObject().value(QStringLiteral("message")).toString()));
        item->setToolTip(0, tip.join(QLatin1Char('\n')));
        item->setToolTip(1, file);
    }
    markEditorDiagnostics(messages);
    if (m_diagnostics->topLevelItemCount() > 0) {
        static_cast<QTabWidget *>(m_outputDock->widget())->setCurrentWidget(m_diagnostics);
        m_outputDock->show();
    }
}

void MainWindow::markEditorDiagnostics(const QJsonArray &messages)
{
    for (EditorPane *pane : editors()) {
        QJsonArray own;
        for (const QJsonValue &value : messages) {
            const QString file = value.toObject().value(QStringLiteral("file")).toString();
            if (!file.isEmpty() && samePath(m_project.absolute(file), pane->filePath()))
                own.append(value);
        }
        pane->editor()->setDiagnostics(own);
    }
}

EditorPane *MainWindow::editTarget()
{
    EditorPane *pane = currentEditor() ? currentEditor() : m_lastEditor.data();
    if (!pane || pane->syntax() != CodeEditor::Syntax::Primula || pane->isReadOnly() || pane->isUnavailable()) {
        statusBar()->showMessage(tr("This works in a writable .prml editor."), 6000);
        return nullptr;
    }
    return pane;
}

void MainWindow::applyStyle(const QString &name, const QString &kind)
{
    EditorPane *pane = editTarget();
    if (!pane) return;
    QTextCursor cursor = pane->editor()->textCursor();
    QString error;
    if (!StyleEditing::apply(cursor, name, StyleEditing::kindFromDump(kind), &error)) {
        statusBar()->showMessage(error, 8000);
        return;
    }
    pane->editor()->setTextCursor(cursor);
    m_tabs->setCurrentWidget(pane);
    pane->editor()->setFocus();
    statusBar()->showMessage(tr("Style %1 applied").arg(name), 3000);
}

void MainWindow::removeStyle(const QString &name)
{
    EditorPane *pane = editTarget();
    if (!pane) return;
    QTextCursor cursor = pane->editor()->textCursor();
    QString error;
    if (!StyleEditing::remove(cursor, name, &error)) {
        statusBar()->showMessage(error, 8000);
        return;
    }
    pane->editor()->setTextCursor(cursor);
    m_tabs->setCurrentWidget(pane);
    pane->editor()->setFocus();
    statusBar()->showMessage(name.isEmpty() ? tr("Style removed") : tr("Style %1 removed").arg(name), 3000);
}

void MainWindow::chooseStyle()
{
    if (!editTarget()) return;
    const QList<QPair<QString, QString>> styles = m_stylesPanel->styleList();
    if (styles.isEmpty()) {
        statusBar()->showMessage(tr("No styles yet: the document has not been inspected."), 6000);
        return;
    }
    // A filter line over a list of the styles that can be applied in the text.
    QDialog dialog(this);
    dialog.setWindowTitle(tr("Apply style"));
    auto *filter = new QLineEdit(&dialog);
    filter->setPlaceholderText(tr("Style name"));
    auto *list = new QListWidget(&dialog);
    list->setObjectName(QStringLiteral("styleChoice"));
    auto kindName = [](const QString &kind) {
        if (kind == QStringLiteral("paragraph")) return tr("paragraph");
        if (kind == QStringLiteral("character")) return tr("character");
        return tr("block");
    };
    for (const auto &[name, kind] : styles) {
        if (StyleEditing::kindFromDump(kind) == StyleEditing::Kind::Other) continue;
        auto *item = new QListWidgetItem(QStringLiteral("%1  —  %2").arg(name, kindName(kind)), list);
        item->setData(Qt::UserRole, name);
        item->setData(Qt::UserRole + 1, kind);
    }
    list->sortItems();
    auto *buttons = new QDialogButtonBox(QDialogButtonBox::Ok | QDialogButtonBox::Cancel, &dialog);
    auto *layout = new QVBoxLayout(&dialog);
    layout->addWidget(filter);
    layout->addWidget(list);
    layout->addWidget(buttons);
    auto selectFirstVisible = [list] {
        for (int i = 0; i < list->count(); ++i)
            if (!list->item(i)->isHidden()) { list->setCurrentRow(i); return; }
    };
    connect(filter, &QLineEdit::textChanged, &dialog, [list, selectFirstVisible](const QString &text) {
        for (int i = 0; i < list->count(); ++i)
            list->item(i)->setHidden(!list->item(i)->data(Qt::UserRole).toString().contains(text.trimmed(), Qt::CaseInsensitive));
        selectFirstVisible();
    });
    connect(filter, &QLineEdit::returnPressed, &dialog, &QDialog::accept);
    connect(list, &QListWidget::itemActivated, &dialog, &QDialog::accept);
    connect(buttons, &QDialogButtonBox::accepted, &dialog, &QDialog::accept);
    connect(buttons, &QDialogButtonBox::rejected, &dialog, &QDialog::reject);
    selectFirstVisible();
    dialog.resize(360, 420);
    if (dialog.exec() != QDialog::Accepted || !list->currentItem() || list->currentItem()->isHidden()) return;
    applyStyle(list->currentItem()->data(Qt::UserRole).toString(), list->currentItem()->data(Qt::UserRole + 1).toString());
}

bool MainWindow::ensureCatalog()
{
    if (m_catalog.isLoaded()) return true;
    m_catalogFailed = false;
    QString error;
    if (!m_catalog.load(interfaceLanguage(), &error)) {
        m_palettePanel->setError(error);
        statusBar()->showMessage(error, 8000);
        return false;
    }
    m_palettePanel->setCatalog(&m_catalog);
    return true;
}

void MainWindow::fillInsertMenu()
{
    m_insertMenu->clear();
    if (ensureCatalog()) {
        const QList<CommandCatalog::Entry> &entries = m_catalog.entries();
        for (const CommandCatalog::Category &category : m_catalog.categories()) {
            QMenu *submenu = m_insertMenu->addMenu(category.title);
            submenu->setToolTipsVisible(true);
            for (int index = 0; index < entries.size(); ++index) {
                const CommandCatalog::Entry &entry = entries.at(index);
                if (entry.category != category.id) continue;
                // '&' would be a mnemonic; the description goes to the right column.
                QString label = entry.label;
                label.replace(QLatin1Char('&'), QStringLiteral("&&"));
                QString summary = entry.summary;
                if (summary.size() > 60) summary = summary.left(58) + QStringLiteral("…");
                QAction *action = submenu->addAction(label + QLatin1Char('\t') + summary, this,
                                                     [this, index] { insertConstruct(index); });
                action->setToolTip(entry.tooltip);
            }
        }
        // Functions of expressions (14.13): Insert → Function ▸ category ▸ name.
        if (!m_catalog.functionCategories().isEmpty()) {
            QMenu *functions = m_insertMenu->addMenu(tr("&Function"));
            functions->setObjectName(QStringLiteral("insertFunctionMenu"));
            for (const CommandCatalog::Category &category : m_catalog.functionCategories()) {
                QMenu *submenu = functions->addMenu(category.title);
                submenu->setToolTipsVisible(true);
                for (int index = 0; index < entries.size(); ++index) {
                    const CommandCatalog::Entry &entry = entries.at(index);
                    if (entry.category != category.id) continue;
                    QString summary = entry.summary;
                    if (summary.size() > 60) summary = summary.left(58) + QStringLiteral("…");
                    QAction *action = submenu->addAction(entry.label + QLatin1Char('\t') + summary, this,
                                                         [this, index] { insertConstruct(index); });
                    action->setToolTip(entry.tooltip);
                }
            }
        }
    } else {
        m_insertMenu->addAction(tr("The catalogue of constructs is not available"))->setEnabled(false);
    }
    m_insertMenu->addSeparator();
    m_insertMenu->addAction(tr("&Header: add missing fields"), this, [this] { addHeaderFields(); })
        ->setObjectName(QStringLiteral("addHeaderFieldsAction"));
    m_insertMenu->addAction(tr("&Image…"), this, &MainWindow::insertImage)->setObjectName(QStringLiteral("insertImageAction"));
    m_insertMenu->addAction(m_paletteDock->toggleViewAction());
}

void MainWindow::insertConstruct(int index)
{
    if (index < 0 || index >= m_catalog.entries().size()) return;
    EditorPane *pane = editTarget();
    if (!pane) return;
    const CommandCatalog::Entry &entry = m_catalog.entries().at(index);
    QTextCursor cursor = pane->editor()->textCursor();
    QString snippet = entry.snippet;
    // A function of expressions in the text of the document (not in code) becomes an
    // expression |(…); functions of styles code, formulas and the project are inserted as is.
    if (entry.function && entry.receiver.isEmpty() && (entry.where.isEmpty() || entry.where == QStringLiteral("any"))
        && pane->syntax() == CodeEditor::Syntax::Primula
        && !PrimulaHighlighter::isCode(cursor.block(), cursor.positionInBlock()) && !cursor.hasSelection()) {
        if (snippet.endsWith(QStringLiteral("$0"))) snippet.chop(2);
        snippet = QStringLiteral("|(") + snippet + QStringLiteral(")$0");
    }
    m_assist->insertSnippet(pane->editor(), cursor, snippet, entry.block);
    pane->editor()->setTextCursor(cursor);
    m_tabs->setCurrentWidget(pane);
    pane->editor()->setFocus();
}

void MainWindow::insertText(const QString &text)
{
    EditorPane *pane = editTarget();
    if (!pane) return;
    pane->editor()->insertPlainText(text);
    m_tabs->setCurrentWidget(pane);
    pane->editor()->setFocus();
}

void MainWindow::insertImage()
{
    EditorPane *pane = editTarget();
    if (!pane) return;
    const QString root = m_project.isOpen() ? m_project.root() : QFileInfo(pane->filePath()).absolutePath();
    const QString assets = QDir(root).filePath(QStringLiteral("assets"));
    QString image = QFileDialog::getOpenFileName(this, tr("Insert image"), QDir(assets).exists() ? assets : root,
                                                 tr("Images (*.png *.jpg *.jpeg *.svg *.gif *.bmp *.tif *.tiff);;All files (*)"));
    if (image.isEmpty()) return;
    // An image outside the project is copied into assets/ so that the project stays self-contained.
    if (QDir(root).relativeFilePath(image).startsWith(QStringLiteral(".."))) {
        const auto answer = QMessageBox::question(this, tr("Insert image"),
            tr("The image is outside the project. Copy it into %1?").arg(QDir(root).relativeFilePath(assets) + QLatin1Char('/')),
            QMessageBox::Yes | QMessageBox::No | QMessageBox::Cancel, QMessageBox::Yes);
        if (answer == QMessageBox::Cancel) return;
        if (answer == QMessageBox::Yes) {
            const QFileInfo source(image);
            QString target = QDir(assets).filePath(source.fileName());
            // Never overwrite: name-2.png, name-3.png…
            for (int n = 2; QFileInfo::exists(target); ++n)
                target = QDir(assets).filePath(QStringLiteral("%1-%2.%3").arg(source.completeBaseName()).arg(n).arg(source.suffix()));
            if (!QDir().mkpath(assets) || !QFile::copy(image, target)) {
                QMessageBox::warning(this, tr("Insert image"), tr("Cannot copy the image to %1.").arg(target));
                return;
            }
            image = target;
        }
    }
    // Paths in |img are relative to the file that contains them (specification 10.1).
    const QString relative = QDir(QFileInfo(pane->filePath()).absolutePath()).relativeFilePath(image);
    QString quoted = relative;
    quoted.replace(QLatin1Char('\\'), QStringLiteral("\\\\")).replace(QLatin1Char('"'), QStringLiteral("\\\""));
    insertText(QStringLiteral("|img(\"%1\")").arg(quoted));
}

void MainWindow::navigateToDiagnostic(QTreeWidgetItem *item)
{
    const QString path = item->data(0, Qt::UserRole).toString();
    if (!path.isEmpty())
        navigateTo(path, item->data(0, Qt::UserRole + 1).toInt(), item->data(0, Qt::UserRole + 2).toInt());
}

void MainWindow::navigateTo(const QString &path, int line, int column)
{
    EditorPane *pane = openFile(path);
    if (!pane) return;
    QTextBlock block = pane->editor()->document()->findBlockByNumber(qMax(1, line) - 1);
    if (!block.isValid())
        block = pane->editor()->document()->lastBlock();
    QTextCursor cursor(block);
    cursor.setPosition(block.position() + qBound(0, qMax(1, column) - 1, block.length() - 1));
    pane->editor()->setTextCursor(cursor);
    pane->editor()->centerCursor();
    pane->editor()->setFocus();
}

void MainWindow::setPreviewDocument(const QString &document)
{
    if (document.isEmpty())
        return;
    m_previewDocument = document;
    const QString pdf = m_project.outputsFor(document).pdf;
    m_pdfLabel->setText(QFileInfo(pdf).exists() ? m_project.relative(pdf)
                                                : tr("%1 — no PDF yet (Build: F9)").arg(QFileInfo(document).fileName()));
    m_pdfLabel->setToolTip(pdf);
    reloadPdf();
}

void MainWindow::reloadPdf()
{
    if (m_previewDocument.isEmpty()) return;
    const QString pdf = m_project.outputsFor(m_previewDocument).pdf;
    if (QFileInfo::exists(pdf))
        m_pdfView->reload(pdf);
    else
        m_pdfView->clear();
    updateUiState();
}

void MainWindow::scheduleInspection()
{
    if (!m_restoring && hasProject()) m_inspectTimer->start();
}

void MainWindow::inspectDocument()
{
    const QString document = currentDocument();
    if (!hasProject() || document.isEmpty() || primulaKind(document) != QStringLiteral("document"))
        return;
    // The PDF page (F4) needs the structure even when both panels are hidden.
    QHash<QString, QString> buffers;
    for (EditorPane *pane : editors())
        if (pane->isModified() && pane->filePath().endsWith(QStringLiteral(".prml")))
            buffers.insert(pane->filePath(), pane->text());
    m_inspector->request(m_project.root(), document, buffers, parameterArguments(document));
}

void MainWindow::inspectionFinished(const QString &document, const QJsonObject &dump, const QString &errorMessage)
{
    if (!hasProject()) return;
    // The first error of the dump explains an outdated panel.
    QString reason = errorMessage;
    for (const QJsonValue &value : dump.value(QStringLiteral("messages")).toArray()) {
        const QJsonObject message = value.toObject();
        if (reason.isEmpty() && message.value(QStringLiteral("severity")).toString() == QStringLiteral("error"))
            reason = QStringLiteral("%1:%2: [%3] %4").arg(message.value(QStringLiteral("file")).toString())
                         .arg(message.value(QStringLiteral("line")).toInt())
                         .arg(message.value(QStringLiteral("code")).toString(),
                              message.value(QStringLiteral("message")).toString());
    }
    const QJsonObject structure = dump.value(QStringLiteral("structure")).toObject();
    if (!structure.isEmpty()) {
        m_structure = structure.value(QStringLiteral("items")).toArray();
        m_structureDocument = document;
        m_structurePanel->setStructure(document, m_structure);
        if (EditorPane *pane = currentEditor())
            m_structurePanel->followCursor(pane->filePath(), pane->editor()->textCursor().blockNumber() + 1);
    } else {
        m_structurePanel->setStale(reason);
    }
    const QJsonObject styles = dump.value(QStringLiteral("styles")).toObject();
    if (!styles.isEmpty()) m_stylesPanel->setStyles(styles);
    else m_stylesPanel->setStale(reason);
}

int MainWindow::pdfPageForCursor() const
{
    EditorPane *pane = currentEditor() ? currentEditor() : m_lastEditor.data();
    if (!pane || m_structure.isEmpty() || m_previewDocument != m_structureDocument
        || m_pdfDocument->status() != QPdfDocument::Status::Ready)
        return -1;
    const int line = pane->editor()->textCursor().blockNumber() + 1;
    // The last heading or appendix of this file at or before the cursor line, and how many
    // headings with the same title come before it in the document (duplicate titles).
    QString title;
    int occurrence = -1;
    QHash<QString, int> seen;
    for (const QJsonValue &value : m_structure) {
        const QJsonObject item = value.toObject();
        const QString kind = item.value(QStringLiteral("kind")).toString();
        if (kind != QStringLiteral("heading") && kind != QStringLiteral("appendix"))
            continue;
        QString text = item.value(kind == QStringLiteral("appendix") ? QStringLiteral("designation")
                                                                       : QStringLiteral("title")).toString().simplified();
        if (text.isEmpty()) continue;
        const int index = seen.value(text, 0);
        seen.insert(text, index + 1);
        if (samePath(item.value(QStringLiteral("path")).toString(), pane->filePath())
            && item.value(QStringLiteral("line")).toInt() <= line) {
            title = text;
            occurrence = index;
        }
    }
    if (title.isEmpty())
        return -1;
    // Depth-first walk of the bookmarks; Writer writes the heading text with its number.
    int found = 0;
    std::function<int(const QModelIndex &)> walk = [&](const QModelIndex &parent) -> int {
        for (int row = 0; row < m_bookmarks->rowCount(parent); ++row) {
            const QModelIndex index = m_bookmarks->index(row, 0, parent);
            const QString text = index.data(int(QPdfBookmarkModel::Role::Title)).toString().simplified();
            if (text.contains(title) && found++ == occurrence)
                return index.data(int(QPdfBookmarkModel::Role::Page)).toInt();
            const int nested = walk(index);
            if (nested >= 0) return nested;
        }
        return -1;
    };
    return walk(QModelIndex());
}

QString MainWindow::pdfAfterBuildMode() const
{
    const QString mode = m_project.group(QStringLiteral("build")).value(QStringLiteral("pdfAfterBuild")).toString();
    return mode.isEmpty() ? QStringLiteral("visible") : mode;
}

// ----------------------------------------------------------------------
// External changes
// ----------------------------------------------------------------------

void MainWindow::checkExternalFiles()
{
    if (m_shuttingDown || !hasProject()) return;
    const QString current = m_externalFiles->currentData().toString();
    m_externalFiles->clear();
    for (EditorPane *pane : editors())
        if (pane->diskChanged())
            m_externalFiles->addItem(m_project.relative(pane->filePath()), pane->filePath());
    const int index = m_externalFiles->findData(current);
    if (index >= 0) m_externalFiles->setCurrentIndex(index);
    m_externalBanner->setVisible(m_externalFiles->count() > 0);
}

void MainWindow::resolveExternalFile(bool reload)
{
    EditorPane *pane = editorFor(m_externalFiles->currentData().toString());
    if (!pane) return;
    if (reload) {
        if (pane->isModified() && QMessageBox::question(this, tr("Reload changed file"),
                tr("Reload %1 and discard its unsaved editor changes?").arg(pane->filePath())) != QMessageBox::Yes)
            return;
        const QVariantMap state = pane->sessionState();
        QString error;
        if (!pane->loadFile(pane->filePath(), pane->isReadOnly(), pane->syntax(), &error)) {
            QMessageBox::warning(this, tr("Cannot reload file"), error);
            return;
        }
        pane->restoreSessionState(state);
    } else {
        pane->acknowledgeDiskChange();
    }
    checkExternalFiles();
    updateTabTitles();
}

// ----------------------------------------------------------------------
// AI (stage 14.10 extends the context)
// ----------------------------------------------------------------------

void MainWindow::showAiDialog()
{
    EditorPane *pane = currentEditor() ? currentEditor() : m_lastEditor.data();
    if (!hasProject() || !pane || m_aiController->isRunning())
        return;
    // The choices of the last request of the project (settings.json, group "ai").
    const QJsonObject saved = m_project.group(QStringLiteral("ai"));
    QDialog dialog(this);
    dialog.setWindowTitle(tr("Ask AI about the document"));
    dialog.resize(720, 520);
    auto *task = new QPlainTextEdit(&dialog);
    task->setPlaceholderText(tr("Describe what should be checked, rewritten, or prepared…"));
    auto *scope = new QComboBox(&dialog);
    scope->addItem(tr("Selected text"), QStringLiteral("selection"));
    scope->addItem(tr("Entire file"), QStringLiteral("document"));
    if (pane->selectedText().isEmpty())
        scope->setCurrentIndex(1);
    auto *language = new QComboBox(&dialog);
    language->setObjectName(QStringLiteral("aiContextLevel"));
    language->addItem(tr("Reference: constructs and functions"), QStringLiteral("reference"));
    language->addItem(tr("Whole specification and library (about 100k tokens)"), QStringLiteral("full"));
    language->addItem(tr("None"), QStringLiteral("none"));
    language->addItem(tr("Local skill primula-docs (the agent loads it; to compare with the reference)"), QStringLiteral("skill"));
    language->setToolTip(tr("What AI receives about the Primula language. The reference is the catalogue of the "
                            "translator: every construct and function with its summary and section. With the skill "
                            "the agent loads its own installed skill primula-docs (skills/README.md tells how to install it); "
                            "it should write «Skill: loaded» on the first line, else the skill is not available to it."));
    language->setCurrentIndex(qMax(0, language->findData(saved.value(QStringLiteral("context")).toString())));
    auto *sections = new QLineEdit(&dialog);
    sections->setObjectName(QStringLiteral("aiSections"));
    sections->setPlaceholderText(tr("e.g. 6.8, 10.5, stdlib:3"));
    sections->setToolTip(tr("Sections of the specification (and of the standard library with 'stdlib:') "
                            "sent in full; the section of the construct at the cursor is proposed."));
    const bool primula = pane->syntax() == CodeEditor::Syntax::Primula || pane->syntax() == CodeEditor::Syntax::PrimulaCode;
    if (primula && ensureCatalog())
        sections->setText(m_assist->sectionAt(pane->editor(), pane->editor()->textCursor().position()));
    const bool hasMessages = !m_buildController->messages().isEmpty();
    auto *messages = new QCheckBox(hasMessages ? tr("Include the messages of the last check or build (%1)")
                                                     .arg(m_buildController->messages().size())
                                               : tr("Include the messages of the last check or build (none)"), &dialog);
    messages->setEnabled(hasMessages);
    messages->setChecked(hasMessages);
    const bool projectFile = m_project.hasProjectFile() && !samePath(pane->filePath(), m_project.projectFile());
    auto *project = new QCheckBox(tr("Include the project file"), &dialog);
    project->setEnabled(projectFile);
    project->setChecked(projectFile);
    auto *rules = new QCheckBox(tr("Writing rules of Primula (from the skill: what not to change, frequent mistakes)"), &dialog);
    rules->setObjectName(QStringLiteral("aiRules"));
    rules->setToolTip(tr("About 6 thousand characters from the skill primula-docs built into Studio; not sent with the skill level."));
    rules->setChecked(saved.value(QStringLiteral("rules")).toBool(true));
    auto *propose = new QCheckBox(tr("Ask for edits that can be checked and applied (tab «Edits» of the answer)"), &dialog);
    propose->setObjectName(QStringLiteral("aiProposeEdits"));
    propose->setToolTip(tr("AI answers with blocks «was → now». Studio finds them in the document, checks the result "
                           "with the translator and applies the chosen ones as one step of Undo."));
    propose->setChecked(saved.value(QStringLiteral("edits")).toBool());
    auto *styles = new QCheckBox(tr("Include the styles modules of the project"), &dialog);
    auto *others = new QCheckBox(tr("Include the other open files"), &dialog);
    styles->setEnabled(!m_project.styleModules().isEmpty());
    styles->setChecked(false);
    others->setChecked(true);
    // The tools the request goes to (stage 22.6): one or several; the choice is remembered.
    const QList<AiAgent> aiAgents = AiAgents::all();
    const QStringList remembered = AiAgents::selected();
    QList<QCheckBox *> agentChecks;
    auto *agentRow = new QHBoxLayout;
    for (const AiAgent &agent : aiAgents) {
        const QString program = AiAgents::program(agent);
        const bool found = !(QFileInfo(program).isAbsolute() ? (QFileInfo(program).isExecutable() ? program : QString())
                                                             : QStandardPaths::findExecutable(program)).isEmpty();
        auto *check = new QCheckBox(found ? agent.name : tr("%1 (not found)").arg(agent.name), &dialog);
        check->setObjectName(QStringLiteral("aiAgent-") + agent.id);
        check->setProperty("agentId", agent.id);
        check->setEnabled(found);
        check->setChecked(found && remembered.contains(agent.id));
        check->setToolTip(found ? tr("The request goes to this tool. With several tools, every one answers in its own tab.")
                                : tr("The program «%1» is not found: set it in File → Settings.").arg(program));
        agentChecks.append(check);
        agentRow->addWidget(check);
    }
    agentRow->addStretch();
    auto selectedAgents = [&agentChecks] {
        QStringList ids;
        for (QCheckBox *check : agentChecks)
            if (check->isChecked()) ids << check->property("agentId").toString();
        return ids;
    };
    auto *buttons = new QDialogButtonBox(QDialogButtonBox::Ok | QDialogButtonBox::Cancel, &dialog);
    buttons->button(QDialogButtonBox::Ok)->setText(tr("Send"));
    connect(buttons, &QDialogButtonBox::accepted, &dialog, [&dialog, selectedAgents, this] {
        if (selectedAgents().isEmpty()) {
            QMessageBox::warning(&dialog, tr("Ask AI"), tr("Choose at least one AI tool."));
            return;
        }
        dialog.accept();
    });
    connect(buttons, &QDialogButtonBox::rejected, &dialog, &QDialog::reject);
    // Ready tasks (stage 22.4): the text of a recipe goes into the task, which stays editable.
    QStringList recipeProblems;
    const QList<AiRecipe> recipes = AiRecipes::load(interfaceLanguage(), AiRecipes::userFile(), &recipeProblems);
    auto *recipe = new QComboBox(&dialog);
    recipe->setObjectName(QStringLiteral("aiRecipe"));
    recipe->addItem(tr("(own task)"), QString());
    for (const AiRecipe &item : recipes) recipe->addItem(item.title, item.id);
    recipe->setToolTip(recipeProblems.isEmpty() ? tr("A ready task; you can edit its text. More recipes: %1").arg(AiRecipes::userFile())
                                                : tr("Skipped in ai-recipes.json:\n%1").arg(recipeProblems.join(QLatin1Char('\n'))));
    connect(recipe, &QComboBox::currentIndexChanged, &dialog, [&, recipes] {
        for (const AiRecipe &item : recipes) {
            if (item.id != recipe->currentData().toString()) continue;
            task->setPlainText(item.task);
            propose->setChecked(item.edits);
            if (item.scope != QStringLiteral("any")) scope->setCurrentIndex(scope->findData(item.scope == QStringLiteral("selection") ? QStringLiteral("selection") : QStringLiteral("document")));
            if (!item.sections.isEmpty()) sections->setText(item.sections);
        }
    });
    auto *layout = new QVBoxLayout(&dialog);
    layout->addWidget(new QLabel(tr("Recipe:"), &dialog));
    layout->addWidget(recipe);
    layout->addWidget(new QLabel(tr("Task:"), &dialog));
    layout->addWidget(task, 1);
    // The AI context of the project is part of every request: shown here so that it is not forgotten.
    auto *contextRow = new QHBoxLayout;
    auto *contextLabel = new QLabel(&dialog);
    contextLabel->setObjectName(QStringLiteral("aiContextState"));
    auto *contextButton = new QPushButton(tr("Edit AI context…"), &dialog);
    contextButton->setObjectName(QStringLiteral("aiContextButton"));
    contextButton->setToolTip(tr("What AI should know about the documents of the project (purpose, parties, terms, style); "
                                 "it is added to every request. The same file as AI → Edit AI context of the project."));
    auto showContextState = [this, contextLabel] {
        const QString text = QFileInfo::exists(m_project.aiContextPath()) ? fileText(m_project.aiContextPath()) : QString();
        contextLabel->setText(text.trimmed().isEmpty()
                                  ? tr("The AI context of the project is empty: nothing about the project is sent.")
                                  : tr("The AI context of the project is included (%n character(s)).", nullptr, int(text.trimmed().size())));
    };
    showContextState();
    connect(contextButton, &QPushButton::clicked, &dialog, [this, &dialog, showContextState] {
        editAiContextInDialog(&dialog);
        showContextState();
    });
    contextRow->addWidget(contextLabel, 1);
    contextRow->addWidget(contextButton);
    layout->addLayout(contextRow);
    auto *form = new QFormLayout;
    form->addRow(tr("Text scope:"), scope);
    form->addRow(tr("Primula language:"), language);
    form->addRow(tr("Sections in full:"), sections);
    layout->addLayout(form);
    layout->addWidget(rules);
    layout->addWidget(propose);
    layout->addWidget(messages);
    layout->addWidget(project);
    layout->addWidget(styles);
    layout->addWidget(others);
    layout->addWidget(new QLabel(tr("AI tools (programs: File → Settings):"), &dialog));
    layout->addLayout(agentRow);
    layout->addWidget(new QLabel(tr("AI receives the text in read-only mode; it cannot change project files."), &dialog));
    layout->addWidget(buttons);
    if (dialog.exec() != QDialog::Accepted)
        return;
    if (task->toPlainText().trimmed().isEmpty()) {
        QMessageBox::warning(this, tr("Empty task"), tr("Enter a task for AI."));
        return;
    }
    const QStringList agentIds = selectedAgents();
    QSettings().setValue(QStringLiteral("ai/tools"), agentIds);
    if (agentIds.size() > 1) {
        // The text of the document and the context go to several services: asked before it is sent.
        QStringList names;
        for (const QString &id : agentIds) names << AiAgents::byId(id).name;
        if (QMessageBox::question(this, tr("Ask AI"),
                tr("The request, with the text of the document and the context of the project, will be sent to %n service(s): %1.\n\n"
                   "Send it?", nullptr, int(agentIds.size())).arg(names.join(QStringLiteral(", ")))) != QMessageBox::Yes)
            return;
    }
    QJsonObject choices = saved;
    choices.insert(QStringLiteral("context"), language->currentData().toString());
    choices.insert(QStringLiteral("edits"), propose->isChecked());
    choices.insert(QStringLiteral("rules"), rules->isChecked());
    m_project.setGroup(QStringLiteral("ai"), choices);
    m_project.saveSettings();
    AiRequest request;
    request.task = task->toPlainText();
    request.proposeEdits = propose->isChecked();
    request.document = scope->currentData().toString() == QStringLiteral("selection") ? pane->selectedText() : pane->text();
    if (styles->isChecked())
        for (const QString &module : m_project.styleModules())
            request.styles += QStringLiteral("# %1\n").arg(m_project.relative(module)) + fileText(module) + QLatin1Char('\n');
    if (others->isChecked())
        for (EditorPane *open : editors())
            if (open != pane && !samePath(open->filePath(), m_project.aiContextPath())
                && !(project->isChecked() && samePath(open->filePath(), m_project.projectFile())))
                request.fragments += QStringLiteral("\n### %1\n").arg(m_project.relative(open->filePath())) + open->text();
    const QString level = language->currentData().toString();
    addPrimulaContext(&request, level == QStringLiteral("full") ? AiContext::Level::Full
                                : level == QStringLiteral("none") ? AiContext::Level::None
                                : level == QStringLiteral("skill") ? AiContext::Level::Skill : AiContext::Level::Reference,
                      AiContext::parseSections(sections->text()), messages->isChecked(), project->isChecked());
    request.projectDirectory = m_project.root();
    if (rules->isChecked() && !request.useSkill) request.rules = AiContext::rules();
    m_pendingAiExchange = AiExchange();
    m_pendingAiExchange.documentPath = pane->filePath();
    startAiRequest(request, scope->currentData().toString(), agentIds);
}

QString MainWindow::fileText(const QString &path)
{
    if (EditorPane *open = editorFor(path)) return open->text();
    QFile file(path);
    return file.open(QIODevice::ReadOnly) ? QString::fromUtf8(file.readAll()) : QString();
}

void MainWindow::addPrimulaContext(AiRequest *request, AiContext::Level level, const QStringList &sections,
                                   bool messages, bool projectFile)
{
    if (projectFile && m_project.hasProjectFile())
        request->projectFile = QStringLiteral("# %1\n").arg(m_project.relative(m_project.projectFile()))
                               + fileText(m_project.projectFile());
    if (messages)
        request->messages = AiContext::messages(m_buildController->messages());
    if (level == AiContext::Level::Full) {
        // The whole specification holds every chosen section already.
        request->specification = AiContext::fullSpecification();
        if (ensureCatalog()) request->reference = AiContext::reference(m_catalog);
        return;
    }
    if (level == AiContext::Level::Skill)
        request->useSkill = true;   // the agent loads the local skill; no reference is attached
    if (level == AiContext::Level::Reference && ensureCatalog())
        request->reference = AiContext::reference(m_catalog);
    request->specification = AiContext::sections(sections);
}

void MainWindow::startAiRequest(const AiRequest &request, const QString &scope, const QStringList &agents)
{
    AiRequest contextual = request;
    if (QFileInfo::exists(m_project.aiContextPath())) {
        EditorPane *open = editorFor(m_project.aiContextPath());
        QFile file(m_project.aiContextPath());
        contextual.projectContext = open ? open->text()
                                         : (file.open(QIODevice::ReadOnly) ? QString::fromUtf8(file.readAll()) : QString());
    }
    m_pendingAiExchange.task = request.task;
    m_pendingAiExchange.prompt = QString::fromUtf8(AiController::makePrompt(contextual));
    m_pendingAiExchange.scope = scope;
    m_pendingAiExchange.backend = AiController::backendName(agents.value(0));
    m_pendingAiProject = m_project.openedPath();
    m_hasPendingAi = true;
    m_aiAgentOrder = agents;
    m_aiResults.clear();
    QStringList names;
    for (const QString &id : agents) names << AiAgents::byId(id).name;
    m_aiProgress = new QProgressDialog(agents.size() > 1 ? tr("Waiting for the answers of %1…").arg(names.join(QStringLiteral(", ")))
                                                         : tr("Waiting for AI response…"),
                                       tr("Cancel"), 0, 0, this);
    m_aiProgress->setWindowModality(Qt::WindowModal);
    m_aiProgress->setMinimumDuration(0);
    connect(m_aiProgress, &QProgressDialog::canceled, m_aiController, &AiController::cancel);
    m_aiProgress->show();
    m_aiController->startAgents(contextual, agents);
    updateUiState();
}

void MainWindow::closeAiProgress()
{
    if (!m_aiProgress) return;
    m_aiProgress->close();
    m_aiProgress->deleteLater();
    m_aiProgress = nullptr;
}

void MainWindow::aiAgentFinished(const QString &agentId, bool success, const QString &response, const QString &errorMessage)
{
    m_aiResults.insert(agentId, {success, response, errorMessage});
    if (m_aiProgress && m_aiAgentOrder.size() > 1) {
        QStringList waiting;
        for (const QString &id : m_aiAgentOrder)
            if (!m_aiResults.contains(id)) waiting << AiAgents::byId(id).name;
        if (!waiting.isEmpty())
            m_aiProgress->setLabelText(tr("Received %1 of %2. Waiting for: %3…").arg(m_aiResults.size()).arg(m_aiAgentOrder.size())
                                           .arg(waiting.join(QStringLiteral(", "))));
    }
}

AiHistoryPane *MainWindow::storeAiResult(AiExchange exchange, const QString &response)
{
    exchange.response = response;
    exchange.receivedAt = QDateTime::currentDateTime();
    QString error;
    const bool sameProject = hasProject() && m_project.openedPath() == m_pendingAiProject;
    const QString path = AiHistory::save(exchange, sameProject ? m_project.aiHistoryDirectory() : QString(), &error);
    AiHistoryPane *pane = nullptr;
    if (path.isEmpty() || sameProject)
        pane = addAiHistory(exchange, path);
    if (path.isEmpty())
        QMessageBox::warning(this, tr("AI result was not saved"),
            tr("The response remains in its tab. Use Save copy to choose another location.\n%1").arg(error));
    else
        statusBar()->showMessage(tr("AI request and response saved: %1").arg(path), 10000);
    return pane;
}

void MainWindow::showAiResult(bool success, const QString &response, const QString &errorMessage)
{
    closeAiProgress();
    updateUiState();
    if (!success) {
        m_hasPendingAi = false;
        QMessageBox::critical(this, tr("AI request failed"), errorMessage);
        return;
    }
    if (!m_hasPendingAi) return;
    m_hasPendingAi = false;
    if (AiHistoryPane *pane = storeAiResult(m_pendingAiExchange, response)) {
        m_aiWorkspace->selectPane(pane);
        showAiHistory();
    }
}

void MainWindow::showAiResults()
{
    closeAiProgress();
    updateUiState();
    if (!m_hasPendingAi) return;
    m_hasPendingAi = false;
    // Every answer is a tab of its own, in the order the tools were chosen; the failures are told together.
    QStringList failures;
    AiHistoryPane *first = nullptr;
    for (const QString &id : m_aiAgentOrder) {
        const AiAgentResult result = m_aiResults.value(id);
        const AiAgent agent = AiAgents::byId(id);
        if (!result.success) {
            failures << QStringLiteral("%1:\n%2").arg(agent.name, result.error.isEmpty() ? tr("no answer") : result.error);
            continue;
        }
        AiExchange exchange = m_pendingAiExchange;
        exchange.backend = agent.label;
        AiHistoryPane *pane = storeAiResult(exchange, result.response);
        if (pane && !first) first = pane;
    }
    if (first) {
        m_aiWorkspace->selectPane(first);
        showAiHistory();
    }
    if (!failures.isEmpty())
        QMessageBox::warning(this, tr("AI request failed"),
                             first ? tr("Some tools gave no answer:\n\n%1").arg(failures.join(QStringLiteral("\n\n")))
                                   : failures.join(QStringLiteral("\n\n")));
}

// ----------------------------------------------------------------------
// Backup copies (stage 25.1)
// ----------------------------------------------------------------------

bool MainWindow::backupFiles(const QStringList &paths, const QString &reason, const QString &note, bool fromBuffers,
                             QString *error)
{
    if (!hasProject()) {
        if (error) *error = tr("No project is open.");
        return false;
    }
    QList<Backups::Item> items;
    for (const QString &path : paths) {
        QByteArray data;
        if (fromBuffers && editorFor(path)) {
            data = editorFor(path)->text().toUtf8();
        } else {
            QFile file(path);
            if (!file.open(QIODevice::ReadOnly)) continue;   // a file that does not exist yet has nothing to keep
            data = file.readAll();
        }
        items.append({path, data});
    }
    if (items.isEmpty()) return true;
    QString failure;
    bool duplicate = false;
    const QString snapshot = Backups::create(m_project.root(), items, reason, note, &failure, &duplicate);
    if (snapshot.isEmpty()) {
        if (error) *error = failure;
        return false;
    }
    if (!duplicate)
        Backups::prune(m_project.root(), qMax(1, QSettings().value(QStringLiteral("backups/keep"), 100).toInt()));
    return true;
}

void MainWindow::backupProjectNow()
{
    if (!hasProject()) return;
    QStringList files = Backups::sourceFiles(m_project.root());
    for (EditorPane *pane : editors())   // an open file outside the project is kept too
        if (!pane->filePath().isEmpty() && !files.contains(pane->filePath()) && pane->isModified()) files << pane->filePath();
    QString error;
    if (files.isEmpty()) {
        QMessageBox::information(this, tr("Backups"), tr("The project has no source files to back up."));
        return;
    }
    if (!backupFiles(files, QStringLiteral("manual"), QString(), true, &error)) {
        QMessageBox::warning(this, tr("Backups"), tr("The backup could not be made:\n%1").arg(error));
        return;
    }
    statusBar()->showMessage(tr("Backed up %n file(s) of the project.", nullptr, int(files.size())), 6000);
}

void MainWindow::showBackups()
{
    if (!hasProject()) return;
    BackupsDialog dialog(m_project.root(), this);
    connect(&dialog, &BackupsDialog::backupNowRequested, this, [this, &dialog] {
        backupProjectNow();
        dialog.reload();
    });
    connect(&dialog, &BackupsDialog::compareRequested, this, &MainWindow::compareWithBackup);
    connect(&dialog, &BackupsDialog::restoreRequested, this, [this, &dialog](const BackupInfo &info, const BackupFile &file) {
        if (restoreBackup(info, file)) dialog.reload();
    });
    dialog.exec();
}

void MainWindow::compareWithBackup(const BackupInfo &info, const BackupFile &file)
{
    const QByteArray copy = Backups::read(info, file);
    QByteArray current;
    if (EditorPane *open = editorFor(file.source)) {
        current = open->text().toUtf8();
    } else {
        QFile now(file.source);
        if (!now.open(QIODevice::ReadOnly)) {
            QMessageBox::information(this, tr("Compare with the backup"), tr("The file does not exist now: %1").arg(file.source));
            return;
        }
        current = now.readAll();
    }
    QString error;
    const QString label = QDir(m_project.root()).relativeFilePath(file.source);
    const QString diff = Backups::unifiedDiff(copy, current, tr("backup %1: %2").arg(QLocale().toString(info.created, QLocale::ShortFormat), label),
                                              tr("current: %1").arg(label), &error);
    if (!error.isEmpty()) {
        QMessageBox::warning(this, tr("Compare with the backup"), tr("The comparison could not be made: %1").arg(error));
        return;
    }
    if (diff.isEmpty()) {
        QMessageBox::information(this, tr("Compare with the backup"), tr("The file is the same as in the backup."));
        return;
    }
    QDialog dialog(this);
    dialog.setWindowTitle(tr("Backup and the current file"));
    dialog.resize(900, 600);
    auto *text = new QPlainTextEdit(&dialog);
    text->setObjectName(QStringLiteral("backupDiff"));
    text->setReadOnly(true);
    text->setLineWrapMode(QPlainTextEdit::NoWrap);
    text->setFont(QFontDatabase::systemFont(QFontDatabase::FixedFont));
    text->setPlainText(diff);
    auto *buttons = new QDialogButtonBox(QDialogButtonBox::Close, &dialog);
    connect(buttons, &QDialogButtonBox::rejected, &dialog, &QDialog::reject);
    auto *layout = new QVBoxLayout(&dialog);
    layout->addWidget(new QLabel(tr("«-» is the backup, «+» is the current file."), &dialog));
    layout->addWidget(text, 1);
    layout->addWidget(buttons);
    dialog.exec();
}

bool MainWindow::restoreBackup(const BackupInfo &info, const BackupFile &file, bool confirm)
{
    const QByteArray copy = Backups::read(info, file);
    if (copy.isEmpty() && file.size > 0) {
        QMessageBox::warning(this, tr("Restore"), tr("The copy is missing or unreadable: %1").arg(file.stored));
        return false;
    }
    const QString label = QDir(m_project.root()).relativeFilePath(file.source);
    if (confirm && QMessageBox::question(this, tr("Restore"),
            tr("Restore %1 as it was at %2?\n\nThe current state is backed up first.")
                .arg(label, QLocale().toString(info.created, QLocale::ShortFormat))) != QMessageBox::Yes)
        return false;
    QString error;
    if (!backupFiles({file.source}, QStringLiteral("before-restore"), label, true, &error)
        && QMessageBox::question(this, tr("Restore"), tr("A backup of the current file could not be made:\n%1\n\nRestore anyway?").arg(error))
               != QMessageBox::Yes)
        return false;
    if (EditorPane *open = editorFor(file.source)) {
        // As an edit of the open file: Undo takes the restore back; the file is saved by the user.
        QTextCursor cursor(open->editor()->document());
        cursor.beginEditBlock();
        cursor.select(QTextCursor::Document);
        cursor.insertText(QString::fromUtf8(copy));
        cursor.endEditBlock();
        statusBar()->showMessage(tr("Restored in the editor: %1 (not saved; Undo takes it back).").arg(label), 10000);
        return true;
    }
    QSaveFile out(file.source);
    QDir().mkpath(QFileInfo(file.source).absolutePath());
    if (!out.open(QIODevice::WriteOnly) || out.write(copy) != copy.size() || !out.commit()) {
        QMessageBox::warning(this, tr("Restore"), tr("The file could not be written: %1").arg(file.source));
        return false;
    }
    statusBar()->showMessage(tr("Restored: %1").arg(label), 10000);
    return true;
}

void MainWindow::loadAiHistory()
{
    const QDir directory(m_project.aiHistoryDirectory());
    for (const QFileInfo &file : directory.entryInfoList({QStringLiteral("*.md")}, QDir::Files, QDir::Name)) {
        AiExchange exchange;
        QString error;
        if (AiHistory::load(file.absoluteFilePath(), &exchange, &error))
            addAiHistory(exchange, file.absoluteFilePath());
    }
    if (m_project.session().value(QStringLiteral("aiHistoryVisible")).toBool())
        showAiHistory();
}

AiHistoryPane *MainWindow::addAiHistory(const AiExchange &exchange, const QString &path)
{
    auto *pane = new AiHistoryPane(exchange, path, this);
    m_aiHistoryPanes.append(pane);
    m_aiWorkspace->addPane(pane);
    connectAiEdits(pane, exchange.documentPath);
    return pane;
}

void MainWindow::connectAiEdits(AiHistoryPane *pane, const QString &documentPath)
{
    AiEditsPanel *panel = pane->editsPanel();
    if (!panel) return;
    const bool exists = !documentPath.isEmpty() && (editorFor(documentPath) || QFileInfo::exists(documentPath));
    AiEditsPanel::TextProvider text;
    AiEditsPanel::Checker check;
    if (exists) {
        text = [this, documentPath] { return fileText(documentPath); };
        // The check needs the translator and a Primula file of the open project.
        if (!Translator::program().isEmpty() && !primulaKind(documentPath).isEmpty())
            check = [this, documentPath](const QString &changed) { return checkTextForAi(documentPath, changed); };
    }
    panel->setDocument(QFileInfo(documentPath).fileName(), text, check);
    connect(panel, &AiEditsPanel::applyRequested, this,
            [this, panel, pane, documentPath](const QList<int> &rows) {
                applyAiEdits(panel, documentPath, rows, pane->exchange().task.section(QLatin1Char('\n'), 0, 0).left(120));
            });
}

AiEditsPanel::CheckReport MainWindow::checkTextForAi(const QString &path, const QString &text)
{
    AiEditsPanel::CheckReport report;
    if (!hasProject()) {
        report.failure = tr("No project is open.");
        return report;
    }
    // The document that contains the file: the file itself, or the document of the preview or the project.
    const QString document = primulaKind(path) == QStringLiteral("document") ? path : currentDocument();
    if (document.isEmpty()) {
        report.failure = tr("There is no document to check this file in.");
        return report;
    }
    QTemporaryDir directory(QDir::temp().filePath(QStringLiteral("primula-studio-XXXXXX")));
    QStringList arguments{QStringLiteral("check"), m_project.relative(document), QStringLiteral("--format"), QStringLiteral("json")};
    arguments << parameterArguments(document);
    int index = 0;
    auto overlay = [&](const QString &file, const QString &buffer) {
        // A plain name without '=': the translator splits FILE=BUFFER at the last '='.
        const QString name = QDir(directory.path()).filePath(QStringLiteral("buffer-%1.prml").arg(index++));
        QFile out(name);
        if (!out.open(QIODevice::WriteOnly | QIODevice::Truncate) || out.write(buffer.toUtf8()) < 0) return false;
        arguments << QStringLiteral("--overlay") << QStringLiteral("%1=%2").arg(file, name);
        return true;
    };
    if (!directory.isValid() || !overlay(path, text)) {
        report.failure = tr("Cannot write a temporary file.");
        return report;
    }
    for (EditorPane *open : editors())
        if (open->isModified() && !samePath(open->filePath(), path)) overlay(open->filePath(), open->text());
    QByteArray output;
    QString errors;
    const int code = Translator::run(arguments, m_project.root(), &output, &errors, 60000);
    const QJsonDocument json = QJsonDocument::fromJson(output);
    if ((code != 0 && code != 2) || !json.isArray()) {
        report.failure = errors.trimmed().isEmpty() ? tr("The translator gave no result (exit code %1).").arg(code) : errors.trimmed();
        return report;
    }
    report.ran = true;
    for (const QJsonValue &value : json.array()) {
        const QJsonObject message = value.toObject();
        if (message.value(QStringLiteral("severity")).toString() == QStringLiteral("error"))
            report.errors << message.value(QStringLiteral("code")).toString() + QLatin1Char(' ') + message.value(QStringLiteral("message")).toString();
    }
    return report;
}

void MainWindow::applyAiEdits(AiEditsPanel *panel, const QString &path, const QList<int> &rows, const QString &note)
{
    EditorPane *pane = openFile(path, true);
    if (!pane || pane->isReadOnly() || pane->isUnavailable()) {
        QMessageBox::warning(this, tr("Apply edits"), tr("The file cannot be edited: %1").arg(path));
        return;
    }
    QList<AiEdit> chosen;
    for (int row : rows) chosen.append(panel->editAt(row));
    QList<AiEditStatus> statuses;
    QList<AiEdits::Place> places;
    AiEdits::apply(pane->text(), chosen, &statuses, &places);
    QList<int> done;   // positions in `chosen` that are applied, last place first
    for (int i = 0; i < chosen.size(); ++i)
        if (statuses.at(i) == AiEditStatus::Ready) done.append(i);
    if (done.isEmpty()) {
        QMessageBox::information(this, tr("Apply edits"),
                                 tr("None of the chosen edits can be applied now: the text of the document has changed."));
        panel->refresh();
        return;
    }
    std::sort(done.begin(), done.end(), [&](int a, int b) { return places.at(a).start > places.at(b).start; });
    // The file is backed up first: Undo does not outlive the editor, a backup does.
    QString backupError;
    if (hasProject() && !backupFiles({path}, QStringLiteral("before-ai-apply"), note, true, &backupError)
        && QMessageBox::question(this, tr("Apply edits"),
                                 tr("A backup of the file could not be made:\n%1\n\nApply the edits anyway?").arg(backupError))
               != QMessageBox::Yes)
        return;
    QTextCursor cursor(pane->editor()->document());
    cursor.beginEditBlock();   // one step for Undo
    for (int i : done) {
        cursor.setPosition(places.at(i).start);
        cursor.setPosition(places.at(i).start + places.at(i).length, QTextCursor::KeepAnchor);
        cursor.insertText(chosen.at(i).replacement);
    }
    cursor.endEditBlock();
    QTextCursor shown = pane->editor()->textCursor();
    shown.setPosition(places.at(done.last()).start);
    pane->editor()->setTextCursor(shown);
    pane->editor()->centerCursor();
    QList<int> appliedRows;
    for (int i : done) appliedRows.append(rows.at(i));
    panel->markApplied(appliedRows);
    const int skipped = int(rows.size() - done.size());
    statusBar()->showMessage(skipped ? tr("Applied %n edit(s), %1 skipped; the file is not saved (Undo takes the edits back).", nullptr, int(done.size())).arg(skipped)
                                     : tr("Applied %n edit(s); the file is not saved (Undo takes the edits back).", nullptr, int(done.size())),
                             15000);
}

void MainWindow::showAiHistory()
{
    if (m_aiHistoryPanes.isEmpty()) return;
    if (m_tabs->indexOf(m_aiWorkspace) < 0) {
        const int pdfIndex = m_tabs->indexOf(m_pdfContainer);
        m_tabs->insertTab(pdfIndex >= 0 ? pdfIndex : m_tabs->count(), m_aiWorkspace, tr("AI"));
    }
    m_tabs->setCurrentWidget(m_aiWorkspace);
    updateUiState();
}

void MainWindow::closeAiHistory()
{
    // Closing the view keeps unsaved recovery buffers and every archived file.
    const int index = m_tabs->indexOf(m_aiWorkspace);
    if (index >= 0) m_tabs->removeTab(index);
    m_aiWorkspace->hide();
}

// ----------------------------------------------------------------------
// Presentation
// ----------------------------------------------------------------------

void MainWindow::updateUiState()
{
    const bool idle = !m_buildController->isRunning() && !m_aiController->isRunning();
    const bool translator = !Translator::program().isEmpty();
    EditorPane *pane = currentEditor();
    m_saveAction->setEnabled(pane && !pane->isUnavailable());
    m_saveAllAction->setEnabled(hasProject());
    m_closeTabAction->setEnabled(pane);
    m_closeOthersAction->setEnabled(pane && editors().size() > 1);
    m_closeProjectAction->setEnabled(hasProject() && idle);
    const bool document = hasProject() && !currentDocument().isEmpty();
    m_checkAction->setEnabled(document && idle && translator);
    m_buildAction->setEnabled(document && idle && translator);
    m_buildProjectAction->setEnabled(hasProject() && m_project.hasProjectFile() && idle && translator);
    const int parameterCount = int(savedParameters(currentDocument()).size());
    // The name of the document says which one the parameters belong to (also from a project file).
    const QString paramsDocument = QFileInfo(currentDocument()).fileName();
    m_paramsAction->setText(paramsDocument.isEmpty() ? tr("Document &parameters…")
                            : parameterCount ? tr("Document &parameters: %1 (%2 set)…").arg(paramsDocument).arg(parameterCount)
                                             : tr("Document &parameters: %1…").arg(paramsDocument));
    m_paramsAction->setEnabled(hasProject() && translator && primulaKind(currentDocument()) == QStringLiteral("document"));
    m_strictAction->setEnabled(hasProject());
    for (QAction *action : m_pdfAfterBuild->actions()) action->setEnabled(hasProject());
    const QString shown = m_previewDocument.isEmpty() ? currentDocument() : m_previewDocument;
    m_openOdtAction->setEnabled(hasProject() && !shown.isEmpty() && QFileInfo::exists(m_project.outputsFor(shown).output));
    m_openDirectoryAction->setEnabled(hasProject());
    m_aiAction->setEnabled(hasProject() && idle && (pane || m_lastEditor));
    m_aiHistoryAction->setEnabled(!m_aiHistoryPanes.isEmpty());
    m_aiContextAction->setEnabled(hasProject());
    m_backupNowAction->setEnabled(hasProject());
    m_backupsAction->setEnabled(hasProject());
    m_backupBeforeSaveAction->setEnabled(hasProject());
    m_newOrderAction->setEnabled(hasProject() && QFileInfo(QDir(m_project.root()).filePath(QStringLiteral("project.p.prml"))).isFile());
    for (const char *name : {"findAction", "findNextAction", "findPreviousAction", "replaceAction"})
        if (auto *action = findChild<QAction *>(QString::fromLatin1(name))) action->setEnabled(pane && !pane->isUnavailable());
}

void MainWindow::updateWindowTitle()
{
    const QList<EditorPane *> panes = editors();
    setWindowModified(std::any_of(panes.cbegin(), panes.cend(), [](EditorPane *pane) { return pane->isModified(); }));
    setWindowTitle(hasProject() ? QStringLiteral("%1[*] — Primula Studio").arg(m_project.name())
                                : QStringLiteral("Primula Studio"));
}

void MainWindow::setEditorFontSize(int size)
{
    size = qBound(8, size, 32);
    QSettings().setValue(QStringLiteral("editor/fontSize"), size);
    if (m_fontSize->value() != size) {
        const QSignalBlocker blocker(m_fontSize);
        m_fontSize->setValue(size);
    }
    applyEditorFont();
}

void MainWindow::applyEditorFont()
{
    const QString defaultFamily = QFontDatabase::systemFont(QFontDatabase::FixedFont).family();
    QSettings settings;
    QFont font(settings.value(QStringLiteral("editor/fontFamily"), defaultFamily).toString());
    font.setPointSize(settings.value(QStringLiteral("editor/fontSize"), 10).toInt());
    for (EditorPane *pane : editors())
        pane->editor()->setEditorFont(font);
    m_output->setFont(font);
}

void MainWindow::showQuickHelp()
{
    const QString language = interfaceLanguage();
    if (!m_helpDialog) {
        m_helpDialog = new HelpDialog(language, this);
        connect(m_helpDialog, &QObject::destroyed, this, [this] { m_helpDialog = nullptr; });
    }
    m_helpDialog->show();
    m_helpDialog->raise();
    m_helpDialog->activateWindow();
}

void MainWindow::showContextHelp()
{
    // F1 in a Primula editor: the section of the construct at the text cursor.
    if (EditorPane *pane = currentEditor(); pane && pane->editor()->hasFocus()
        && (pane->syntax() == CodeEditor::Syntax::Primula || pane->syntax() == CodeEditor::Syntax::PrimulaCode)) {
        const int position = pane->editor()->textCursor().position();
        if (!m_assist->sectionAt(pane->editor(), position).isEmpty()) {
            showContextSection(pane->editor(), position);
            return;
        }
        statusBar()->showMessage(tr("No construct at the cursor: the quick help is open."), 5000);
    }
    showQuickHelp();
}

void MainWindow::showContextSection(CodeEditor *editor, int position)
{
    const EditorAssist::HelpContext context = m_assist->contextAt(editor, position);
    if (context.section.isEmpty()) {
        statusBar()->showMessage(tr("No construct here: there is no section to show."), 5000);
        return;
    }
    const bool library = context.section.startsWith(QStringLiteral("stdlib:"));
    const QString section = library ? context.section.mid(7) : context.section;
    if (library) showLibrary(section);
    else showSpecification(section);   // clears an earlier context first
    HelpDialog *dialog = library ? m_libraryDialog : m_specDialog;
    if (!dialog) return;
    // The construct is marked in the editor and named in the window, so that it is clear
    // which text the window belongs to (remark of 22.10.2026).
    editor->setContextMark(context.start, context.end);
    m_contextEditor = editor;
    m_contextDialog = dialog;
    const int line = editor->document()->findBlock(context.start).blockNumber() + 1;
    const QString sectionLabel = library ? tr("library section %1").arg(section) : tr("section %1").arg(section);
    dialog->setContext(context.text,
                       tr("Shown: %1 for “%2” (line %3, marked in the editor). The quick help is "
                          "Help → Quick help.").arg(sectionLabel, context.text).arg(line));
    // When the window goes, only the mark in the editor is removed: the window itself is
    // being destroyed (its children and members are gone), so it must not be touched.
    m_contextConnection = connect(dialog, &QObject::destroyed, this, [this] {
        if (m_contextEditor) m_contextEditor->clearContextMark();
        m_contextEditor = nullptr;
        m_contextDialog = nullptr;
    });
}

void MainWindow::clearContextHelp()
{
    if (m_contextEditor) m_contextEditor->clearContextMark();
    if (m_contextDialog) {
        m_contextDialog->setContext(QString(), QString());
        disconnect(m_contextConnection);
    }
    m_contextEditor = nullptr;
    m_contextDialog = nullptr;
}

void MainWindow::showSpecification(const QString &section)
{
    // Opened from the menu, the palette or the console: no editor context any more.
    clearContextHelp();
    if (section.startsWith(QStringLiteral("stdlib:"))) {
        showLibrary(section.mid(7));
        return;
    }
    if (!m_specDialog) {
        // The specification in the interface language (ru — the normative source, uk and en — translations).
        m_specDialog = new HelpDialog(QStringLiteral(":/help/primula-spec.%1.md").arg(interfaceLanguage()),
                                      tr("Primula language specification"), this);
        m_specDialog->setObjectName(QStringLiteral("specificationDialog"));
        connect(m_specDialog, &QObject::destroyed, this, [this] { m_specDialog = nullptr; });
    }
    m_specDialog->show();
    if (!section.isEmpty()) m_specDialog->showSection(section);
    m_specDialog->raise();
    m_specDialog->activateWindow();
}

void MainWindow::showLibrary(const QString &section)
{
    clearContextHelp();
    // The standard library document, built in like the specification.
    if (!m_libraryDialog) {
        // The standard library in the interface language (ru — the source, uk and en — translations).
        m_libraryDialog = new HelpDialog(QStringLiteral(":/help/primula-stdlib.%1.md").arg(interfaceLanguage()),
                                         tr("Primula standard library"), this);
        m_libraryDialog->setObjectName(QStringLiteral("libraryDialog"));
        connect(m_libraryDialog, &QObject::destroyed, this, [this] { m_libraryDialog = nullptr; });
    }
    m_libraryDialog->show();
    if (!section.isEmpty()) m_libraryDialog->showSection(section);
    m_libraryDialog->raise();
    m_libraryDialog->activateWindow();
}

void MainWindow::showCheatSheet()
{
    const QString directory = QStandardPaths::writableLocation(QStandardPaths::CacheLocation);
    // The cheat sheet in the interface language: .ru.pdf is the source, .uk.pdf and .en.pdf are
    // its translations (studio/help/cheatsheet/).
    const QString name = QStringLiteral("primula-cheatsheet.%1.pdf").arg(interfaceLanguage());
    const QString path = QDir(directory).filePath(name);
    QFile source(QStringLiteral(":/help/") + name);
    QFile target(path);
    // Rewritten each time: the copy must follow the version built into Studio.
    // A plain write, not QFile::copy, which fails on file systems without linkat().
    if (!QDir().mkpath(directory) || !source.open(QIODevice::ReadOnly) || !target.open(QIODevice::WriteOnly)
        || target.write(source.readAll()) != source.size()) {
        QMessageBox::warning(this, tr("Command cheat sheet"), tr("Cannot write %1.").arg(path));
        return;
    }
    target.close();
    // The system viewer: the PDF page of Studio belongs to the document being built.
    QDesktopServices::openUrl(QUrl::fromLocalFile(path));
}

QString MainWindow::authorGuidePath(const QString &language, QStringList *tried)
{
    // Where the guide can be:
    // - the installed package: the launcher sets PRIMULA_STUDIO_DATA_DIR to
    //   PREFIX/share/primula-docs/share/primula-studio, the guide is PREFIX/share/primula-docs/guide;
    // - beside the real binary (share/primula-docs/libexec → ../guide): Studio is started through
    //   the symbolic link PREFIX/libexec/primula-studio, so the link is resolved first;
    // - the source tree for a development build (studio/build-*/ → ../../docs/author).
    QStringList bases;
    const QString data = qEnvironmentVariable("PRIMULA_STUDIO_DATA_DIR");
    if (!data.isEmpty())
        bases << QDir(data).filePath(QStringLiteral("../../guide"));
    const QString binary = QFileInfo(QCoreApplication::applicationFilePath()).canonicalPath();
    const QString application = QCoreApplication::applicationDirPath();
    for (const QString &directory : {binary, application}) {
        if (directory.isEmpty()) continue;
        bases << QDir(directory).filePath(QStringLiteral("../guide"))
              << QDir(directory).filePath(QStringLiteral("../../docs/author"));
    }
    for (const QString &candidate : {language, QStringLiteral("en")}) {
        const QString name = QStringLiteral("%1/primula-author-guide-%1.pdf").arg(candidate);
        for (const QString &base : std::as_const(bases)) {
            const QString path = QDir::cleanPath(base + QLatin1Char('/') + name);
            if (QFileInfo(path).isFile())
                return path;
            if (tried && !tried->contains(path)) *tried << path;
        }
    }
    return {};
}

void MainWindow::showAuthorGuide()
{
    // The PDF of the author guide in the interface language; the system viewer, as the cheat sheet.
    QStringList tried;
    const QString path = authorGuidePath(interfaceLanguage(), &tried);
    if (!path.isEmpty()) {
        QDesktopServices::openUrl(QUrl::fromLocalFile(path));
        return;
    }
    QMessageBox::information(this, tr("Author guide"),
        tr("The PDF of the author guide is not found. It is part of the installation package "
           "(guide/<language>/) and of the source tree (docs/author/<language>/).\n\nLooked in:\n%1")
            .arg(tried.join(QLatin1Char('\n'))));
}

void MainWindow::setLanguage(const QString &language)
{
    QSettings().setValue(QStringLiteral("ui/language"), language);
    QMessageBox::information(this, tr("Language changed"), tr("Restart Studio to apply the new interface language."));
}

void MainWindow::closeEvent(QCloseEvent *event)
{
    if (!confirmDiscardChanges()) {
        event->ignore();
        return;
    }
    saveSession();
    if (m_console->isVisible()) m_console->saveWindowState();
    QSettings settings;
    settings.setValue(QStringLiteral("ui/diagnosticsHeader"), m_diagnostics->header()->saveState());
    settings.setValue(QStringLiteral("window/geometry"), saveGeometry());
    settings.setValue(QStringLiteral("window/state"), saveState(WindowStateVersion));
    stopBackgroundWork();
    event->accept();
}

// ----------------------------------------------------------------------
// New files and file operations (stage 14.9, remark З9)
// ----------------------------------------------------------------------

QString MainWindow::templateLanguage() const
{
    const QString project = m_project.language().section(QLatin1Char('-'), 0, 0).toLower();
    if (project == QStringLiteral("uk") || project == QStringLiteral("ru") || project == QStringLiteral("en"))
        return project;
    QString ui = QSettings().value(QStringLiteral("ui/language")).toString();
    if (ui.isEmpty())
        ui = QLocale::system().name().section(QLatin1Char('_'), 0, 0);
    return ui == QStringLiteral("ru") || ui == QStringLiteral("en") ? ui : QStringLiteral("uk");
}

void MainWindow::newFile(const QString &kind, const QString &directory)
{
    QString place = directory;
    if (place.isEmpty())
        place = hasProject() ? m_project.root() : QDir::homePath();
    // The base of an order: the project in the root (for an order project — its base).
    NewFileDialog::OrderBase base;
    const NewFileDialog::OrderBase *basePointer = nullptr;
    const QString baseFile = hasProject() ? QDir(m_project.root()).filePath(QStringLiteral("project.p.prml")) : QString();
    if (!baseFile.isEmpty() && QFileInfo(baseFile).isFile()) {
        StudioProject baseProject;
        if (baseFile == m_project.projectFile() || baseProject.open(baseFile)) {
            const StudioProject &source = baseFile == m_project.projectFile() ? m_project : baseProject;
            base.projectFile = baseFile;
            base.root = m_project.root();
            base.targets = source.targets();
            base.declaresStyles = source.declaresStyles();
            QFile sample(QDir(m_project.root()).filePath(QStringLiteral("orders/sample.yaml")));
            if (sample.open(QIODevice::ReadOnly))
                base.sampleYaml = QString::fromUtf8(sample.readAll());
            basePointer = &base;
        }
    }
    NewFileDialog dialog(kind, place, templateLanguage(), basePointer, this);
    if (dialog.exec() != QDialog::Accepted)
        return;
    QString error;
    if (!createFromTemplate(dialog.selectedTemplate(), dialog.targetDirectory(), dialog.values(), dialog.language(), &error))
        QMessageBox::critical(this, tr("Cannot create files"), error);
}

bool MainWindow::createFromTemplate(const FileTemplate &tpl, const QString &directory,
                                    const QHash<QString, QString> &values, const QString &language,
                                    QString *errorMessage)
{
    QStringList created, toOpen;
    if (!Templates::instantiate(tpl, directory, values, language, &created, &toOpen, errorMessage))
        return false;
    statusBar()->showMessage(tr("Created: %1").arg(created.join(QStringLiteral(", "))), 8000);
    const QString projectFile = QDir(directory).filePath(QStringLiteral("project.p.prml"));
    if (tpl.kind == QStringLiteral("project")) {
        // A new project becomes the open one.
        return openProject(projectFile) || true;
    }
    if (tpl.kind == QStringLiteral("order")) {
        const auto choice = QMessageBox::question(this, tr("Order project created"),
            tr("Open the order project %1 now? Its targets are built with Shift+F9.").arg(m_project.relative(projectFile)));
        if (choice == QMessageBox::Yes)
            return openProject(projectFile) || true;
    }
    if (!hasProject() && !toOpen.isEmpty())
        return openProject(toOpen.first()) || true;
    for (const QString &path : std::as_const(toOpen))
        openFile(path);
    return true;
}

void MainWindow::showFilesMenu(const QString &path, const QPoint &position)
{
    const QFileInfo info(path);
    const QString directory = info.isDir() ? info.absoluteFilePath() : info.absolutePath();
    const bool isRoot = QDir::cleanPath(path) == QDir::cleanPath(m_project.root());
    QMenu menu(this);
    QMenu *create = menu.addMenu(tr("New in this folder"));
    create->addAction(tr("Document…"), this, [this, directory] { newFile(QStringLiteral("document"), directory); });
    create->addAction(tr("Fragment…"), this, [this, directory] { newFile(QStringLiteral("fragment"), directory); });
    create->addAction(tr("Module of definitions…"), this, [this, directory] { newFile(QStringLiteral("module"), directory); });
    create->addAction(tr("Styles module…"), this, [this, directory] { newFile(QStringLiteral("styles"), directory); });
    create->addSeparator();
    create->addAction(tr("Folder…"), this, [this, directory] { newFolderDialog(directory); });
    menu.addSeparator();
    if (!isRoot) {
        if (info.isFile()) {
            menu.addAction(tr("Open"), this, [this, path] { openFile(path); });
            const FileType *type = m_fileTypes.typeOf(path);
            if (type != nullptr && !type->command.isEmpty() && type->open != QStringLiteral("command")) {
                const FileType copy = *type;
                menu.addAction(tr("Open with %1").arg(copy.name.isEmpty() ? copy.command.value(0) : copy.name), this,
                               [this, copy, path] { runFileCommand(copy, path); });
            }
            if (type != nullptr && type->open != QStringLiteral("editor") && !isBinaryFile(path))
                menu.addAction(tr("Open as text in the editor"), this, [this, path] { openFileAsText(path); });
            if (primulaKind(path) == QStringLiteral("document"))
                fillExportMenu(menu.addMenu(tr("Export")), path);
            if (!primulaKind(path).isEmpty())
                menu.addAction(tr("File summary…"), this, [this, path] { showFileSummary(path); });
            menu.addAction(tr("Open in an external application"), this, [path] {
                QDesktopServices::openUrl(QUrl::fromLocalFile(path));
            });
        }
        menu.addAction(tr("Copy under a new name…"), this, [this, path] { copyDialog(path); });
        menu.addAction(tr("Rename…"), this, [this, path] { renameDialog(path); });
        menu.addAction(tr("Move to trash"), this, [this, path] { trashDialog(path); });
        menu.addSeparator();
    }
    menu.addAction(tr("Open the folder in the file manager"), this, [directory] {
        QDesktopServices::openUrl(QUrl::fromLocalFile(directory));
    });
    menu.exec(position);
}

void MainWindow::showFileSummary(const QString &path)
{
    QString reason;
    const QString text = Translator::describeFile(path, interfaceLanguage(), &reason);
    if (text.isEmpty()) {
        QMessageBox::warning(this, tr("File summary"),
                             tr("The translator could not describe %1:\n%2").arg(QFileInfo(path).fileName(), reason));
        return;
    }
    QDialog dialog(this);
    dialog.setWindowTitle(tr("File summary — %1").arg(QFileInfo(path).fileName()));
    auto *layout = new QVBoxLayout(&dialog);
    auto *view = new QPlainTextEdit(&dialog);
    view->setReadOnly(true);
    view->setFont(QFontDatabase::systemFont(QFontDatabase::FixedFont));
    view->setPlainText(text);
    layout->addWidget(view, 1);
    auto *buttons = new QDialogButtonBox(QDialogButtonBox::Close, &dialog);
    connect(buttons, &QDialogButtonBox::rejected, &dialog, &QDialog::reject);
    layout->addWidget(buttons);
    dialog.resize(780, 520);
    dialog.exec();
}

QString MainWindow::exportPath(const QString &document, const QString &format) const
{
    // Extensions of the pandoc writers (as primula export chooses them).
    static const QHash<QString, QString> extensions{
        {QStringLiteral("markdown"), QStringLiteral("md")}, {QStringLiteral("gfm"), QStringLiteral("md")},
        {QStringLiteral("commonmark"), QStringLiteral("md")}, {QStringLiteral("html"), QStringLiteral("html")},
        {QStringLiteral("docx"), QStringLiteral("docx")}, {QStringLiteral("odt"), QStringLiteral("odt")},
        {QStringLiteral("latex"), QStringLiteral("tex")}, {QStringLiteral("epub"), QStringLiteral("epub")},
        {QStringLiteral("rst"), QStringLiteral("rst")}, {QStringLiteral("plain"), QStringLiteral("txt")},
        {QStringLiteral("json"), QStringLiteral("json")}, {QStringLiteral("org"), QStringLiteral("org")},
        {QStringLiteral("asciidoc"), QStringLiteral("adoc")}, {QStringLiteral("typst"), QStringLiteral("typ")},
        {QStringLiteral("rtf"), QStringLiteral("rtf")}};
    const QString odt = m_project.outputsFor(document).output;
    const QFileInfo info(odt);
    const QString name = info.completeBaseName() + QLatin1Char('.') + extensions.value(format, format);
    // An ODT export would replace the ODT of the build: it gets its own name.
    const QString file = format == QStringLiteral("odt") ? info.completeBaseName() + QStringLiteral(".pandoc.odt") : name;
    return QDir(info.absolutePath()).filePath(file);
}

void MainWindow::fillExportMenu(QMenu *menu, const QString &document)
{
    menu->clear();
    if (!hasProject() || document.isEmpty() || primulaKind(document) != QStringLiteral("document")) {
        menu->addAction(tr("Open a document of the project to export it"))->setEnabled(false);
        return;
    }
    const bool idle = !m_buildController->isRunning();
    for (const auto &[label, format] : {std::pair{tr("&Markdown"), QStringLiteral("markdown")},
                                        std::pair{tr("&HTML (one file)"), QStringLiteral("html")},
                                        std::pair{tr("&DOCX (Word)"), QStringLiteral("docx")}}) {
        QAction *action = menu->addAction(label, this, [this, document, format] { runExport(document, format); });
        action->setToolTip(exportPath(document, format));
        action->setEnabled(idle);
    }
    menu->addAction(tr("Another &format…"), this, [this, document] {
        bool ok = false;
        const QStringList formats{QStringLiteral("gfm"), QStringLiteral("latex"), QStringLiteral("epub"),
                                  QStringLiteral("rst"), QStringLiteral("odt"), QStringLiteral("plain"),
                                  QStringLiteral("asciidoc"), QStringLiteral("typst"), QStringLiteral("json")};
        const QString format = QInputDialog::getItem(this, tr("Export"),
            tr("Format (a writer of pandoc; json — the pandoc AST, no pandoc needed):"), formats, 0, true, &ok).trimmed();
        if (ok && !format.isEmpty()) runExport(document, format);
    })->setEnabled(idle);
    menu->addSeparator();
    menu->addAction(tr("Export &as…"), this, [this, document] {
        bool ok = false;
        const QString format = QInputDialog::getItem(this, tr("Export as"), tr("Format:"),
            {QStringLiteral("markdown"), QStringLiteral("html"), QStringLiteral("docx"), QStringLiteral("gfm"),
             QStringLiteral("latex"), QStringLiteral("epub"), QStringLiteral("json")}, 0, true, &ok).trimmed();
        if (ok && !format.isEmpty()) runExport(document, format, true);
    })->setEnabled(idle);
    menu->addSeparator();
    menu->addAction(tr("What is exported…"), this, [this] {
        QMessageBox::information(this, tr("Export"),
            tr("Export writes the evaluated document through pandoc: numbers of clauses, references, footnotes, "
               "tables and captions are kept; page layout (headers, footers, columns, page numbers) is not. "
               "Paragraph and character styles go to DOCX by name. Markdown, HTML, DOCX and other formats need "
               "pandoc (https://pandoc.org); JSON is the pandoc AST itself."));
    });
}

void MainWindow::runExport(const QString &document, const QString &format, bool askPath)
{
    if (!hasProject() || document.isEmpty() || m_buildController->isRunning() || !saveAll())
        return;
    QString target = exportPath(document, format);
    if (askPath) {
        target = QFileDialog::getSaveFileName(this, tr("Export as"), target);
        if (target.isEmpty()) return;
    }
    QDir().mkpath(QFileInfo(target).absolutePath());
    QStringList arguments{QStringLiteral("export"), m_project.relative(document), QStringLiteral("--to"), format,
                          QStringLiteral("-o"), m_project.relative(target)};
    arguments << parameterArguments(document);
    if (m_strictAction->isChecked()) arguments << QStringLiteral("--strict");
    // The translator writes the file only when the document has no errors (exit code 0).
    m_exportTarget = QFileInfo(target).absoluteFilePath();
    m_output->clear();
    m_buildController->start(BuildController::Kind::Export, arguments, m_project.root());
}

void MainWindow::reloadFileTypes()
{
    m_fileTypes.load(FileTypes::userFile(), hasProject() ? m_project.root() : QString());
    m_files->setNameFilters(m_fileTypes.patterns());
    for (const QString &problem : m_fileTypes.problems())
        m_output->appendPlainText(tr("File types: %1").arg(problem));
}

void MainWindow::editFileTypes()
{
    const QString path = FileTypes::userFile();
    if (!QFileInfo::exists(path)) {
        QFile source(QStringLiteral(":/config/file-types.user.json"));
        QFile target(path);
        if (!QDir().mkpath(QFileInfo(path).absolutePath()) || !source.open(QIODevice::ReadOnly)
            || !target.open(QIODevice::WriteOnly)) {
            QMessageBox::warning(this, tr("File types"), tr("Cannot create %1").arg(path));
            return;
        }
        target.write(source.readAll());
        target.close();
        statusBar()->showMessage(tr("Created %1 from the template: edit it and save").arg(path), 6000);
    }
    openFileAsText(path);
}

bool MainWindow::runFileCommand(const FileType &type, const QString &path)
{
    const QStringList command = FileTypes::expand(type.command, path, hasProject() ? m_project.root() : QString());
    if (command.isEmpty() || command.first().isEmpty()) {
        QMessageBox::warning(this, tr("Cannot open file"), tr("The file type %1 has no command.").arg(type.name));
        return false;
    }
    qint64 pid = 0;
    if (!QProcess::startDetached(command.first(), command.mid(1), QFileInfo(path).absolutePath(), &pid)) {
        QMessageBox::warning(this, tr("Cannot open file"),
                             tr("The command of the file type %1 did not start:\n%2\n\nCheck it in %3 (File → File types…).")
                                 .arg(type.name, command.join(QLatin1Char(' ')), FileTypes::userFile()));
        return false;
    }
    statusBar()->showMessage(tr("Opened with %1: %2").arg(type.name, QFileInfo(path).fileName()), 4000);
    return true;
}

void MainWindow::newFolderDialog(const QString &directory)
{
    bool ok = false;
    const QString name = QInputDialog::getText(this, tr("New folder"), tr("Name of the folder:"), QLineEdit::Normal,
                                               QString(), &ok).trimmed();
    if (!ok || name.isEmpty())
        return;
    if (name.contains(QLatin1Char('/')) || name.startsWith(QLatin1Char('.')) || !QDir(directory).mkdir(name))
        QMessageBox::warning(this, tr("Cannot create the folder"), QDir(directory).filePath(name));
}

QList<EditorPane *> MainWindow::editorsUnder(const QString &path) const
{
    const QString base = QDir::cleanPath(QFileInfo(path).absoluteFilePath());
    QList<EditorPane *> result;
    for (EditorPane *pane : editors()) {
        const QString file = QDir::cleanPath(pane->filePath());
        if (file == base || file.startsWith(base + QLatin1Char('/')))
            result.append(pane);
    }
    return result;
}

QString MainWindow::copyPath(const QString &path, const QString &newName, QString *errorMessage)
{
    const QFileInfo info(path);
    const QString target = info.absoluteDir().filePath(newName);
    if (newName.isEmpty() || newName.contains(QLatin1Char('/')) || QFileInfo::exists(target)) {
        if (errorMessage) *errorMessage = tr("The name is empty, contains / or is taken: %1").arg(target);
        return {};
    }
    if (info.isFile()) {
        if (!QFile::copy(path, target)) {
            if (errorMessage) *errorMessage = tr("Cannot copy %1 to %2").arg(path, target);
            return {};
        }
        return target;
    }
    // A directory: every file under it, keeping the tree (hidden files too).
    QDirIterator iterator(path, QDir::AllEntries | QDir::NoDotAndDotDot | QDir::Hidden, QDirIterator::Subdirectories);
    if (!QDir().mkpath(target)) {
        if (errorMessage) *errorMessage = tr("Cannot create %1").arg(target);
        return {};
    }
    while (iterator.hasNext()) {
        const QString source = iterator.next();
        const QString destination = QDir(target).filePath(QDir(path).relativeFilePath(source));
        const bool done = iterator.fileInfo().isDir() ? QDir().mkpath(destination) : QFile::copy(source, destination);
        if (!done) {
            QDir(target).removeRecursively();
            if (errorMessage) *errorMessage = tr("Cannot copy %1 to %2").arg(source, destination);
            return {};
        }
    }
    return target;
}

QList<QPair<QString, int>> MainWindow::occurrences(const QString &directory, const QString &text)
{
    static const QStringList textSuffixes{QStringLiteral("prml"), QStringLiteral("yaml"), QStringLiteral("yml"),
                                          QStringLiteral("csv"), QStringLiteral("json"), QStringLiteral("md"),
                                          QStringLiteral("txt")};
    QList<QPair<QString, int>> result;
    if (text.isEmpty())
        return result;
    QDirIterator iterator(directory, QDir::Files | QDir::Hidden, QDirIterator::Subdirectories);
    while (iterator.hasNext()) {
        const QString file = iterator.next();
        if (!textSuffixes.contains(iterator.fileInfo().suffix().toLower()))
            continue;
        QFile input(file);
        if (!input.open(QIODevice::ReadOnly))
            continue;
        const int count = int(QString::fromUtf8(input.readAll()).count(text));
        if (count > 0)
            result.append({file, count});
    }
    std::sort(result.begin(), result.end());
    return result;
}

bool MainWindow::replaceInFiles(const QStringList &files, const QString &from, const QString &to, QString *errorMessage)
{
    for (const QString &file : files) {
        QFile input(file);
        if (!input.open(QIODevice::ReadOnly)) {
            if (errorMessage) *errorMessage = input.errorString();
            return false;
        }
        const QByteArray text = QString::fromUtf8(input.readAll()).replace(from, to).toUtf8();
        input.close();
        QSaveFile output(file);
        if (!output.open(QIODevice::WriteOnly) || output.write(text) != text.size() || !output.commit()) {
            if (errorMessage) *errorMessage = output.errorString();
            return false;
        }
    }
    return true;
}

void MainWindow::copyDialog(const QString &path)
{
    const QFileInfo info(path);
    bool ok = false;
    const QString name = QInputDialog::getText(this, tr("Copy under a new name"),
        tr("New name of the copy of %1:").arg(info.fileName()), QLineEdit::Normal, info.fileName(), &ok).trimmed();
    if (!ok || name.isEmpty() || name == info.fileName())
        return;
    QString error;
    const QString copy = copyPath(path, name, &error);
    if (copy.isEmpty()) {
        QMessageBox::critical(this, tr("Cannot copy"), error);
        return;
    }
    // A copied directory (an order) usually names itself inside: offer to replace the old name.
    if (info.isDir()) {
        const auto found = occurrences(copy, info.fileName());
        if (!found.isEmpty()) {
            QStringList lines;
            QStringList files;
            for (const auto &[file, count] : found) {
                lines.append(QStringLiteral("%1 — %2").arg(m_project.relative(file)).arg(count));
                files.append(file);
            }
            QMessageBox box(QMessageBox::Question, tr("Replace the old name"),
                tr("Replace «%1» with «%2» in the files of the copy?").arg(info.fileName(), name),
                QMessageBox::Yes | QMessageBox::No, this);
            box.setDetailedText(lines.join(QLatin1Char('\n')));
            box.setInformativeText(tr("%n file(s) contain the old name; see the details.", nullptr, int(found.size())));
            if (box.exec() == QMessageBox::Yes && !replaceInFiles(files, info.fileName(), name, &error))
                QMessageBox::critical(this, tr("Cannot replace"), error);
        }
    } else {
        openFile(copy);
    }
    statusBar()->showMessage(tr("Copied: %1").arg(m_project.relative(copy)), 6000);
}

bool MainWindow::renamePath(const QString &path, const QString &newName, QString *errorMessage)
{
    const QFileInfo info(path);
    const QString target = info.absoluteDir().filePath(newName);
    const QList<EditorPane *> open = editorsUnder(path);
    for (EditorPane *pane : open) {
        if (pane->isModified()) {
            if (errorMessage) *errorMessage = tr("Save or close %1 first.").arg(pane->filePath());
            return false;
        }
    }
    if (newName.isEmpty() || newName.contains(QLatin1Char('/')) || QFileInfo::exists(target)) {
        if (errorMessage) *errorMessage = tr("The name is empty, contains / or is taken: %1").arg(target);
        return false;
    }
    // Remember the editors (position, active tab), close them, rename, reopen at the new paths.
    QList<QPair<QString, QVariantMap>> states;
    QWidget *current = m_tabs->currentWidget();
    QString currentPath;
    for (EditorPane *pane : open) {
        states.append({pane->filePath(), pane->sessionState()});
        if (pane == current) currentPath = pane->filePath();
        m_tabs->removeTab(m_tabs->indexOf(pane));
        pane->deleteLater();
    }
    const bool renamed = info.isDir() ? QDir().rename(path, target) : QFile::rename(path, target);
    for (const auto &[old, state] : std::as_const(states)) {
        const QString moved = renamed ? target + old.mid(QDir::cleanPath(info.absoluteFilePath()).size()) : old;
        if (EditorPane *pane = openFile(moved, old == currentPath))
            pane->restoreSessionState(state);
    }
    if (!renamed && errorMessage)
        *errorMessage = tr("Cannot rename %1 to %2").arg(path, target);
    saveSession();
    return renamed;
}

void MainWindow::renameDialog(const QString &path)
{
    const QFileInfo info(path);
    bool ok = false;
    const QString name = QInputDialog::getText(this, tr("Rename"), tr("New name of %1:").arg(info.fileName()),
                                               QLineEdit::Normal, info.fileName(), &ok).trimmed();
    if (!ok || name.isEmpty() || name == info.fileName())
        return;
    QString error;
    if (!renamePath(path, name, &error))
        QMessageBox::critical(this, tr("Cannot rename"), error);
}

bool MainWindow::removePath(const QString &path, bool toTrash, QString *errorMessage)
{
    const QList<EditorPane *> open = editorsUnder(path);
    for (EditorPane *pane : open) {
        if (pane->isModified()) {
            if (errorMessage) *errorMessage = tr("Save or close %1 first.").arg(pane->filePath());
            return false;
        }
    }
    const QFileInfo info(path);
    bool removed = false;
    if (toTrash)
        removed = QFile::moveToTrash(path);
    else
        removed = info.isDir() ? QDir(path).removeRecursively() : QFile::remove(path);
    if (!removed) {
        if (errorMessage)
            *errorMessage = toTrash ? tr("Cannot move %1 to the trash.").arg(path) : tr("Cannot delete %1.").arg(path);
        return false;
    }
    for (EditorPane *pane : open) {
        m_tabs->removeTab(m_tabs->indexOf(pane));
        pane->deleteLater();
    }
    QStringList watched;
    for (EditorPane *editor : editors()) watched.append(editor->filePath());
    m_fileMonitor->setFiles(watched);
    updateTabTitles();
    updateUiState();
    saveSession();
    return true;
}

void MainWindow::trashDialog(const QString &path)
{
    if (QMessageBox::question(this, tr("Move to trash"), tr("Move %1 to the trash?").arg(m_project.relative(path)))
        != QMessageBox::Yes)
        return;
    QString error;
    if (removePath(path, true, &error))
        return;
    if (!editorsUnder(path).isEmpty() && std::any_of(editorsUnder(path).cbegin(), editorsUnder(path).cend(),
                                                     [](EditorPane *pane) { return pane->isModified(); })) {
        QMessageBox::critical(this, tr("Cannot move to trash"), error);
        return;
    }
    // The trash of this partition is unavailable (no .Trash-<uid> at its top): offer deleting for good.
    if (QMessageBox::warning(this, tr("Cannot move to trash"),
            tr("%1\nDelete %2 permanently? This cannot be undone.").arg(error, m_project.relative(path)),
            QMessageBox::Yes | QMessageBox::No, QMessageBox::No) == QMessageBox::Yes
        && !removePath(path, false, &error))
        QMessageBox::critical(this, tr("Cannot delete"), error);
}
