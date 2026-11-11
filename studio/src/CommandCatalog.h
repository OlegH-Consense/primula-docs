#pragma once

// The catalogue of Primula constructs from `primula commands --format json`
// (stage 14.8, translator feature Т5): commands and short forms by category with
// their snippets, short descriptions, arguments and specification sections, in the
// interface language. One source for the Insert menu and the palette (and later for
// hints and completion, 14.8a).
//
// Stage 14.13: also the functions of expressions (`functions`: core, standard library,
// std/math, styles code, table formulas, project, methods) as entries with function set;
// their categories are apart (functionCategories(), ids with the prefix "fn:"), their
// section is "stdlib:N" for the standard library document.

#include <QJsonArray>
#include <QJsonObject>
#include <QList>
#include <QStringList>
#include <QString>

class CommandCatalog
{
public:
    struct Entry
    {
        QString label;      ///< what the user sees: |link, |*{…}, |>
        QString category;   ///< category id; "closing" for closing markers (|end…), shown nowhere but in hints
        QString summary;
        QString section;    ///< specification section, e.g. "4.2"
        QString snippet;
        QString tooltip;    ///< summary, arguments and section, one per line
        bool block = false; ///< takes whole lines (environment or line form)
        // Functions of expressions (stage 14.13):
        bool function = false;
        QString name;       ///< sqrt, money, split
        QString module;     ///< "std/math" (written math.sqrt) or empty
        QString receiver;   ///< str, list, dict for a method, else empty
        QString signature;  ///< money(x, code, currency_style="short", lang=None)
        QString where;      ///< any, styles (styles code), cell (table formula), project
        // A command that a library module defines with |def (stage 28.0):
        bool library = false;
        QString source;     ///< absolute path of the module file
        int line = 0;       ///< line of |def in the file
    };
    struct Category
    {
        QString id;
        QString title;
    };
    /// A key of the YAML header (stage 14.14, decision 127; key header_keys of the catalogue).
    struct HeaderKey
    {
        QString path;        ///< doc.title, targets[].source
        QStringList kinds;   ///< document, fragment, module, styles, project
        QString type;        ///< string, path, paths, mapping, list, number, int, bool, date, language, strings, any
        QStringList values;  ///< allowed (closed) or suggested values
        bool closed = false;
        bool recommended = false;   ///< expected in a finished ODT (document metadata)
        QString section;
        QString summary;
        QString example;     ///< one YAML line
    };

    /// Run the translator once and keep the catalogue; later calls return the kept one.
    /// @param language  en, uk or ru (the interface language).
    /// @return false with error when the translator is missing or its output is not a catalogue.
    bool load(const QString &language, QString *error);
    /// Fill from a parsed `primula commands --format json` object (also for tests).
    bool setJson(const QJsonObject &json, QString *error);
    bool isLoaded() const { return !m_entries.isEmpty(); }

    const QList<Category> &categories() const { return m_categories; }
    const QList<Category> &functionCategories() const { return m_functionCategories; }
    const QList<Entry> &entries() const { return m_entries; }
    /// Commands of the modules that the inspected document imports (`primula check --dump-commands`,
    /// key library_commands): kept apart from the catalogue of the language and shown as the categories
    /// "Library: <module>" after it. An empty list removes them. The list survives setJson().
    /// @param commands  the JSON array of the translator.
    /// @param baseDir  the directory of the document (the files are given relative to it).
    /// @return true when the set of library entries changed (the palette and menus need a refill).
    bool setLibraryCommands(const QJsonArray &commands, const QString &baseDir);
    /// Index of the function name (method of any receiver when method, of std/math when
    /// module), or -1. Methods and functions share names (split, count): method decides.
    int functionIndex(const QString &name, bool method, bool module) const;
    /// Header keys (empty with a translator older than 14.14).
    const QList<HeaderKey> &headerKeys() const { return m_headerKeys; }
    /// The key at path for a file of kind, or nullptr.
    const HeaderKey *headerKey(const QString &kind, const QString &path) const;

    /// "Specification, section 4.2" or "Standard library, section 3" (section "stdlib:3").
    static QString sectionLabel(const QString &section);

private:
    QList<Category> m_categories;
    QList<Category> m_functionCategories;
    QList<Entry> m_entries;
    QList<HeaderKey> m_headerKeys;
    // The base part (the language) ends here; the library entries and categories follow it.
    void applyLibrary();
    int m_baseEntries = 0;
    int m_baseCategories = 0;
    QJsonArray m_library;
    QString m_libraryBase;
};
