# Primula Docs — the translator and Primula Studio

Primula is a markup language for business and technical documents: text with `|…`
commands (headings, numbered clauses, tables, references, data, conditions), with
the formatting kept in separate styles modules. The **translator** `primula` builds
an editable **ODT** for LibreOffice Writer from `.prml` and, with LibreOffice, a **PDF**.
**Primula Studio** is the workplace: an editor with highlighting, hints and completion,
check and build, a PDF view, the Structure, Styles and Palette panels.

The package is built for one distribution (see `distribution.json`): Studio uses the
system Qt 6 libraries. No compiler or development packages are needed.

## What to read

| File | Contents |
| --- | --- |
| [guide/en/index.md](guide/en/index.md) | the author guide: first document, contract, act and tables, letter, technical documentation, project, styles, messages of the translator |
| [guide/en/primula-author-guide-en.pdf](guide/en/primula-author-guide-en.pdf) | the same guide as one PDF with the appendices and the glossary (in Studio — Help → Author guide (PDF)); also in Ukrainian and Russian |
| [STUDIO-GUIDE.en.md](STUDIO-GUIDE.en.md) | the Primula Studio guide (also F1 in the program) |
| [primula-cheatsheet.en.pdf](primula-cheatsheet.en.pdf) | a cheat sheet of the language commands ([uk](primula-cheatsheet.uk.pdf), [ru](primula-cheatsheet.ru.pdf)) |
| [primula-spec-v1.1-draft.en.md](primula-spec-v1.1-draft.en.md) | the language specification (draft 1.1; a translation, the original is [ru](primula-spec-v1.1-draft.ru.md); also [uk](primula-spec-v1.1-draft.uk.md)) |
| [primula-stdlib-v1.1-draft.en.md](primula-stdlib-v1.1-draft.en.md) | the standard library: styles, modules ([uk](primula-stdlib-v1.1-draft.uk.md), [ru](primula-stdlib-v1.1-draft.ru.md)) |
| [examples/README.md](examples/README.md) | examples: from a simple document to a project with a contract and orders |
| [editors/README.md](editors/README.md) | highlighting of `.prml` for Kate, mcedit, Geany and VS Code (`editors/install.sh`) |

## Requirements

- Python 3.11+ with PyYAML 6 (`python3-yaml` on Debian, `python3XY-PyYAML` on openSUSE);
- Qt 6.4+ (Core, Gui, Widgets, Pdf, PdfWidgets, a platform plugin, SVG icons);
- LibreOffice Writer for PDF; the Liberation Sans font for the standard styles;
- Codex CLI only for AI requests (optional).

## Installation

```sh
./check-dependencies.sh               # check; installs nothing
./check-dependencies.sh --print-plan  # which system packages are needed
./check-dependencies.sh --install     # install them (sudo)
./install.sh                          # install into ~/.local
```

`install.sh` verifies the package checksums, creates the Python environment
`~/.local/share/primula-python` (it sees the system PyYAML; without one it installs
PyYAML with pip, `--offline --wheelhouse DIRECTORY` from local files), copies the
package to `~/.local/share/primula-docs`, the `primula` and `primula-studio` commands
to `~/.local/bin` and the menu entry. Another location: `--prefix DIRECTORY`.
Without a desktop: `--translator-only`.

Update: `./install.sh` from the new package (over the previous installation).

Removal: `./uninstall.sh` from the package or from the installed copy
(`~/.local/share/primula-docs/uninstall.sh`, which finds its installation directory
itself; the same as `./install.sh --uninstall`). It removes everything the
installation put into `~/.local` (the upper part of the table below); `--keep-python`
keeps the Python environment. The Studio settings and the examples stay.
`./uninstall.sh --purge` removes them too — the settings, your file types and templates,
the cache, the copies of the examples with your changes: it lists them first and asks
for a confirmation (`--yes` does not ask). Your projects elsewhere are never touched.

## Use

```sh
primula-studio                         # Studio (or from the menu: Primula Studio)
primula build document.prml --pdf      # ODT and PDF
primula check document.prml            # check only
primula --help                         # all commands; primula commands lists the constructs
```

The installation copies the examples to the visible working directory `~/Primula/examples` (another one: `--examples-dir DIRECTORY`, no copy: `--no-examples`); build and change them there. Every example goes under "File → Recent projects". When Primula Studio has no settings yet, `install.sh` creates them, and the first example opens at the first start; in existing settings the missing examples are appended after your projects while the list has room (Studio keeps 20), and nothing else in the settings changes. Install while Studio is closed. On an update a changed copy of the examples (build results included) is kept as `~/Primula/examples.old-<time>` and the new examples are copied again; `--uninstall` does not remove the copy of the examples.

## Where things are

Default locations (`--prefix`, `--examples-dir` and the `XDG_*_HOME` variables change them).

| Path | What is there | `--uninstall` |
| --- | --- | --- |
| `~/.local/share/primula-docs/` | the installed package: translator, Studio, guides, specification, original examples and libraries, `uninstall.sh` | removes |
| `~/.local/share/primula-python/` | Python environment of the translator (PyYAML) | removes (unless `--keep-python`) |
| `~/.local/bin/primula`, `~/.local/bin/primula-view`, `~/.local/bin/primula-studio` | commands | removes |
| `~/.local/libexec/primula-studio` | link to the Studio program in the package | removes |
| `~/.local/share/applications/org.primula_docs.Studio.desktop`, `~/.local/share/icons/hicolor/scalable/apps/primula-studio.svg` | menu entry and icon | removes |
| `~/Primula/examples/`, `~/Primula/examples.old-<time>/` | working copy of the examples and previous copies | `--purge` |
| `~/.config/primula-docs/Primula Studio.conf` | Studio settings: recent projects, windows, translator path | `--purge` |
| `~/.config/primula-docs/file-types.json`, `~/.config/primula-docs/templates/` | your file types and templates of Studio | `--purge` |
| `~/.cache/primula-docs/` | Studio cache (copy of the cheat sheet) | `--purge` |
| your project directories | documents, `.primula-studio/` of a project, build results | never |

## Limitations

- Studio uses the system Qt 6, glibc and libstdc++, which stay compatible upwards: a
  package built on an older system (for example, Debian 12) is meant for newer ones
  too, but not the other way round. `install.sh` warns about another distribution and
  checks the libraries and the start of Studio; if the check fails, build Studio there
  (`studio/build-debian.sh` or `studio/build-studio.sh` in the sources).
- The language (specification 1.1, draft) and the file formats may still change.
