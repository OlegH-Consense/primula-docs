cmake_minimum_required(VERSION 3.20)

project(primula-studio VERSION 0.1.0 LANGUAGES CXX)

# Primula Studio is versioned together with the translator: the full version
# string (e.g. 0.1.0.dev18) is read from the repository's pyproject.toml.
set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/../pyproject.toml")
file(STRINGS "${CMAKE_CURRENT_SOURCE_DIR}/../pyproject.toml" PRIMULA_VERSION_LINE REGEX "^version = ")
string(REGEX REPLACE "^version = \"([^\"]+)\".*" "\\1" PRIMULA_STUDIO_VERSION "${PRIMULA_VERSION_LINE}")
if(NOT PRIMULA_STUDIO_VERSION)
    set(PRIMULA_STUDIO_VERSION "${PROJECT_VERSION}")
endif()

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTORCC ON)

set(PRIMULA_STUDIO_MIN_QT_VERSION "6.4" CACHE STRING "Minimum supported Qt version")
find_package(Qt6 ${PRIMULA_STUDIO_MIN_QT_VERSION} REQUIRED COMPONENTS
    Core
    Gui
    Widgets
    Pdf
    PdfWidgets
    LinguistTools
)

qt_standard_project_setup()

set(STUDIO_SOURCES
    src/AiContext.cpp
    src/AiContext.h
    src/Backups.cpp
    src/Backups.h
    src/BackupsDialog.cpp
    src/BackupsDialog.h
    src/AiRecipes.cpp
    src/AiRecipes.h
    src/AiAgents.cpp
    src/AiAgents.h
    src/AiEdits.cpp
    src/AiEdits.h
    src/AiEditsPanel.cpp
    src/AiEditsPanel.h
    src/AiController.cpp
    src/AiController.h
    src/AiHistory.cpp
    src/AiHistory.h
    src/AiHistoryPane.cpp
    src/AiHistoryPane.h
    src/AiWorkspace.cpp
    src/AiWorkspace.h
    src/BuildController.cpp
    src/BuildController.h
    src/CodeEditor.cpp
    src/CodeEditor.h
    src/EditorPane.cpp
    src/EditorPane.h
    src/FileMonitor.cpp
    src/FileMonitor.h
    src/EditorAssist.cpp
    src/EditorAssist.h
    src/FilesPanel.cpp
    src/FilesPanel.h
    src/FileTypes.cpp
    src/FileTypes.h
    src/ConsolePanel.cpp
    src/ConsolePanel.h
    src/DocumentInspector.cpp
    src/DocumentInspector.h
    src/StructurePanel.cpp
    src/StructurePanel.h
    src/CommandCatalog.cpp
    src/CommandCatalog.h
    src/PalettePanel.cpp
    src/PalettePanel.h
    src/Snippet.cpp
    src/Snippet.h
    src/StyleEditing.cpp
    src/StyleEditing.h
    src/StylesPanel.cpp
    src/StylesPanel.h
    src/HeaderAssist.cpp
    src/HeaderAssist.h
    src/HelpDialog.cpp
    src/HelpDialog.h
    src/MainWindow.cpp
    src/MainWindow.h
    src/NewFileDialog.cpp
    src/NewFileDialog.h
    src/PdfPreview.cpp
    src/PdfPreview.h
    src/PrimulaHighlighter.cpp
    src/PrimulaHighlighter.h
    src/StudioProject.cpp
    src/StudioProject.h
    src/Templates.cpp
    src/Templates.h
    src/Translator.cpp
    src/Translator.h
    src/StudioVersion.h
    resources/resources.qrc
)

# The version in one generated source: configure_file rewrites it only when the
# version changes, so a version bump recompiles this file alone.
configure_file(src/StudioVersion.cpp.in "${CMAKE_CURRENT_BINARY_DIR}/generated/StudioVersion.cpp" @ONLY)

# The sources are compiled once, into an object library shared by the application
# and the Qt tests (before, each target compiled all of them again).
add_library(primula-studio-core OBJECT ${STUDIO_SOURCES} "${CMAKE_CURRENT_BINARY_DIR}/generated/StudioVersion.cpp")
target_include_directories(primula-studio-core PUBLIC src)
target_link_libraries(primula-studio-core PUBLIC
    Qt6::Core
    Qt6::Gui
    Qt6::Widgets
    Qt6::Pdf
    Qt6::PdfWidgets
)

add_executable(primula-studio src/main.cpp)
target_link_libraries(primula-studio PRIVATE primula-studio-core)
if(WIN32)
    # The icon of primula-studio.exe (windres, MinGW cross-build: studio/windows/build-win.sh).
    enable_language(RC)
    set_target_properties(primula-studio PROPERTIES WIN32_EXECUTABLE ON)   # no console window
    target_sources(primula-studio PRIVATE windows/primula-studio.rc)
    target_include_directories(primula-studio PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/windows")
endif()

# Templates of «File → New» (stage 14.9): every file of templates/ as a resource
# under :/templates/<id>/...; the glob is re-evaluated when templates change.
file(GLOB_RECURSE STUDIO_TEMPLATE_FILES CONFIGURE_DEPENDS RELATIVE "${CMAKE_CURRENT_SOURCE_DIR}" templates/*)
function(primula_studio_templates target)
    qt_add_resources(${target} "${target}_templates" PREFIX "/" FILES ${STUDIO_TEMPLATE_FILES})
endfunction()
primula_studio_templates(primula-studio)


set(TS_FILES
    translations/primula_studio_uk.ts
    translations/primula_studio_ru.ts
)
set_source_files_properties(${TS_FILES} PROPERTIES
    OUTPUT_LOCATION "${CMAKE_CURRENT_BINARY_DIR}/translations"
)
qt_add_translation(QM_FILES ${TS_FILES})
add_custom_target(primula-studio-translations ALL DEPENDS ${QM_FILES})
add_dependencies(primula-studio primula-studio-translations)

include(GNUInstallDirs)
install(TARGETS primula-studio RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR})
install(FILES ${QM_FILES}
    DESTINATION ${CMAKE_INSTALL_DATADIR}/primula-studio/translations
)
install(DIRECTORY help/
    DESTINATION ${CMAKE_INSTALL_DATADIR}/primula-studio/help
    FILES_MATCHING PATTERN "*.md" PATTERN "*.pdf"
)
install(FILES resources/primula-studio.svg
    DESTINATION ${CMAKE_INSTALL_DATADIR}/icons/hicolor/scalable/apps
)
install(FILES resources/org.primula_docs.Studio.desktop
    DESTINATION ${CMAKE_INSTALL_DATADIR}/applications
)

# Stage desktop metadata for client discovery during direct build-tree launches.
# register-desktop.sh registers the build entry in the user desktop directory.
file(MAKE_DIRECTORY "${CMAKE_CURRENT_BINARY_DIR}/share/applications")
set(STUDIO_DESKTOP_EXEC "${CMAKE_CURRENT_BINARY_DIR}/primula-studio")
set(STUDIO_DESKTOP_ICON "${CMAKE_CURRENT_SOURCE_DIR}/resources/primula-studio.svg")
configure_file(resources/org.primula_docs.Studio.desktop.in
    "${CMAKE_CURRENT_BINARY_DIR}/share/applications/org.primula_docs.Studio.desktop" @ONLY)

option(PRIMULA_STUDIO_BUILD_TESTS "Build Qt regression tests" OFF)
# The tests run the translator of this repository (../primula) on temporary projects.
set(PRIMULA_STUDIO_TEST_TRANSLATOR "${CMAKE_CURRENT_SOURCE_DIR}/../primula"
    CACHE FILEPATH "Primula translator used by the Studio tests")
if(PRIMULA_STUDIO_BUILD_TESTS)
    enable_testing()
    find_package(Qt6 REQUIRED COMPONENTS Test)
    add_executable(studio-tests tests/StudioTests.cpp)
    primula_studio_templates(studio-tests)
    target_link_libraries(studio-tests PRIVATE primula-studio-core Qt6::Test)
    target_compile_definitions(studio-tests PRIVATE PRIMULA_TEST_TRANSLATOR="${PRIMULA_STUDIO_TEST_TRANSLATOR}")
    add_test(NAME studio-regressions COMMAND studio-tests)
    set_tests_properties(studio-regressions PROPERTIES ENVIRONMENT "QT_QPA_PLATFORM=offscreen")
endif()
