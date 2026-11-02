# Changelog

Versions before 1.0 may change the language and the formats of files between releases. The language has its own version (specification 1.1, draft); the program version is below. Development snapshots between releases are marked `.devN` (`0.3.0.dev14` precedes `0.3.0`) and are not published.

## 0.3.0 — 2026-11-02

**Language and translator**
- `primula export` — Markdown, HTML, DOCX and other formats through pandoc (`primula export doc.prml --to docx`).
- `primula view` (and the short command `primula-view`) — builds a document into a temporary directory, opens the PDF in a viewer and deletes the files afterwards; for F3 in Midnight Commander and file managers; `--text` prints the document as plain text without LibreOffice.
- `primula describe` — what a module, a styles module or a project contains: public functions with signatures and descriptions, styles, targets; `--format json` for editors.
- `load_text` (a text file as one string, for example an SVG for `svg=`), `load_ods`, `load_xlsx` for tables, `qr_matrix`, `qr_svg`, `base64url`.
- A table split between pages is closed by a line on both parts of the split.

**Libraries of modules** (`libraries/`, version 0.1.0 each, Apache-2.0; the tables of `ua_data` — CC BY 4.0)
- `ua_ids` (ЄДРПОУ, РНОКПП, IBAN UA), `names` (full names in cases, initials, signature), `ua_data` (NBU and VAT rates, minimum wage, subsistence minimum, CPI, calendar — with the date of effect and the source of every row), `legal` (penalty, 3 % per annum, inflation losses, terms), `finance` (annuity, schedule, NPV/IRR, depreciation), `payment_qr` (NBU), `epc_qr` (SEPA), `codes` (EAN-13, ISBN, Luhn), `charts`, `stats`, `electronics` (E series), `vcs` (change table from Git).
- The laws and figures behind `ua_data` and `legal` were compared with the texts on zakon.rada.gov.ua; what could not be opened is named in each README. The libraries are not legal advice.

**Primula Studio**
- Export (Build → Export), the author guide as a PDF (Help → Author guide), the specification and the standard library in the language of the interface, "File summary…" in the tab and Files menus.
- The installed package finds the PDF of the guide.

**Documentation**
- The author guide in `docs/author/{ru,uk,en}/`, one PDF per language built by Primula itself.
- The specification and the standard library in Ukrainian and English (the Russian text is the original and the normative one); a cheat sheet in three languages.

**Editors**
- Highlighting for Kate/KWrite/KDevelop, Midnight Commander (mcedit), Geany and VS Code/VSCodium (`editors/`, installer `editors/install.sh`); the word list is built from the reference of the translator. Checked by hand in Kate, mcedit (the most complete) and VSCodium (installed from the `.vsix`); Geany is approximate (a borrowed lexer, the colours come from its colour scheme); not checked in Cursor.

**Package**
- `primula-view` and `editors/` in the installation package; the package built on Debian 12 installs on Debian 13 and openSUSE Tumbleweed.

## 0.2.0 — 2026-10-26

The first public pre-release: the translator, Primula Studio, the specification 1.1 (draft), the author guide, the examples, `libraries/payment_qr`, the skills for AI agents.
