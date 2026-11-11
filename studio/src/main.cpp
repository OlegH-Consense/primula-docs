#include "MainWindow.h"
#include "StudioVersion.h"

#include <QApplication>
#include <QDir>
#include <QFileInfo>
#include <QIcon>
#include <QLocale>
#include <QLoggingCategory>
#include <QSettings>
#include <QStandardPaths>
#include <QTranslator>
#include <QTimer>
#include <QLibraryInfo>
#include <QJsonDocument>
#include <QJsonObject>
#include <QTextStream>

#ifdef Q_OS_WIN
#include <windows.h>
#include <cstdio>
#endif

namespace {

QString translationDirectory()
{
    const QString appDirectory = QCoreApplication::applicationDirPath();
    QStringList candidates = {
        QDir(appDirectory).filePath(QStringLiteral("translations")),
        QDir(appDirectory).filePath(QStringLiteral("../share/primula-studio/translations")),
        QDir(appDirectory).filePath(QStringLiteral("../translations"))
    };
    const QString installedData = qEnvironmentVariable("PRIMULA_STUDIO_DATA_DIR");
    if (!installedData.isEmpty()) candidates.prepend(QDir(installedData).filePath(QStringLiteral("translations")));
    for (const QString &candidate : candidates) {
        if (QFileInfo::exists(candidate))
            return QDir::cleanPath(candidate);
    }
    return {};
}

} // namespace

int main(int argc, char *argv[])
{
#ifdef Q_OS_WIN
    // A GUI-subsystem program has no console of its own (no black window behind Studio); when it
    // is started from a terminal, --version and error messages go to that terminal.  Redirected
    // standard handles (a pipe, a file) are left alone.
    if (!GetStdHandle(STD_OUTPUT_HANDLE) && AttachConsole(ATTACH_PARENT_PROCESS)) {
        std::freopen("CONOUT$", "w", stdout);
        std::freopen("CONOUT$", "w", stderr);
    }
#endif
    const QString option = argc > 1 ? QString::fromLocal8Bit(argv[1]) : QString();
    if (option == QStringLiteral("--version")) {
        QTextStream(stdout) << "Primula Studio " << studioVersion() << '\n';
        return 0;
    }
    if (option == QStringLiteral("--runtime-info")) {
        QCoreApplication core(argc, argv);
        const QJsonObject info{
            {QStringLiteral("studio_version"), QString::fromLatin1(studioVersion())},
            {QStringLiteral("qt_build"), QStringLiteral(QT_VERSION_STR)},
            {QStringLiteral("qt_runtime"), QString::fromLatin1(qVersion())},
            {QStringLiteral("plugin_path"), QLibraryInfo::path(QLibraryInfo::PluginsPath)}
        };
        QTextStream(stdout) << QJsonDocument(info).toJson(QJsonDocument::Compact) << '\n';
        return 0;
    }
    // Expose staged metadata to the client for direct build-tree runs.
    // register-desktop.sh provides metadata visible to the separate host portal.
    // This changes only this process environment, never installs into HOME.
    const QString executable = QStandardPaths::findExecutable(QString::fromLocal8Bit(argv[0]));
    const QString buildShare = QDir(QFileInfo(executable).absolutePath()).filePath(QStringLiteral("share"));
    if (QFileInfo::exists(QDir(buildShare).filePath(QStringLiteral("applications/org.primula_docs.Studio.desktop")))) {
        const QByteArray previous = qgetenv("XDG_DATA_DIRS");
        qputenv("XDG_DATA_DIRS", buildShare.toUtf8() + ':'
            + (previous.isEmpty() ? QByteArray("/usr/local/share:/usr/share") : previous));
    }
    // QFontComboBox asks every installed font about writing systems; fonts without
    // OpenType tables (Type 1, bitmap, colour emoji) make Qt print a warning for each.
    // QT_LOGGING_RULES of the environment still takes precedence.
    QLoggingCategory::setFilterRules(QStringLiteral("qt.text.font.db.warning=false"));
    QApplication app(argc, argv);
    QCoreApplication::setOrganizationName(QStringLiteral("primula-docs"));
    QCoreApplication::setApplicationName(QStringLiteral("Primula Studio"));
    QCoreApplication::setApplicationVersion(QString::fromLatin1(studioVersion()));
    QGuiApplication::setDesktopFileName(QStringLiteral("org.primula_docs.Studio"));
    app.setWindowIcon(QIcon(QStringLiteral(":/icons/primula-studio.svg")));

    QSettings settings;
    QString language = settings.value(QStringLiteral("ui/language")).toString();
    if (language.isEmpty())
        language = QLocale::system().name().section('_', 0, 0);

    QTranslator translator;
    QTranslator qtTranslator;
    if (language != QStringLiteral("en")) {
        const QString directory = translationDirectory();
        if (!directory.isEmpty() && translator.load(QStringLiteral("primula_studio_%1").arg(language), directory))
            app.installTranslator(&translator);
        // Standard buttons and dialogs of Qt itself (Cancel, Yes, No, file dialogs).
        if (qtTranslator.load(QStringLiteral("qtbase_%1").arg(language),
                              QLibraryInfo::path(QLibraryInfo::TranslationsPath)))
            app.installTranslator(&qtTranslator);
    }

    if (option == QStringLiteral("--check-runtime")) {
        QTextStream(stdout) << "Qt runtime and platform plugin: OK\n";
        return 0;
    }

    MainWindow window;
    window.show();

    const QStringList arguments = app.arguments();
    const QString explicitPath = arguments.size() > 1 ? arguments.at(1) : QString();
    QTimer::singleShot(0, &window, [&window, explicitPath] {
        window.restoreStartupProject(explicitPath);
    });

    return app.exec();
}
