#!/bin/sh
# Build the Primula examples with the source tree of the prototype (no install):
# the launcher ../primula runs the translator from ../src.
#
# Usage: ./run.sh [--pdf] [--lang en|uk|ru]
#   --pdf    also export PDF through LibreOffice (soffice must be in PATH;
#            python UNO bridge is optional, it fills page numbers in the TOC)
#   --lang   language of the diagnostics (default: from the environment)
#
# Results go to examples/out/: <name>.odt, <name>.pdf, <name>.report.json
# (example 8: styles-<set>.*, one document per styles set of the kit; example 9:
# parallel-agreement.*, parallel-protocol.*; example 10: code.*; example 11:
# library-invoice.*, a document using the shared library 11-library/shared/ua-iban
# through the link 11-library/project/lib, warning P2639 expected; example 12:
# payment-qr-invoice.*, an invoice with the NBU payment QR code of the library
# libraries/payment_qr; example 13: estimate.*, an estimate with the library libraries/estimate;
# example 14: bibliography.*, citations and references with libraries/bib (the accumulator
# collect/collected); example 15: own-commands.*, a module with own commands and a glossary;
# example 16: import-*.*, the documents that "primula import" made from Markdown, HTML and DOCX),
# basics.tree.txt (evaluated document tree), project.report.json (example 7:
# a project, its targets go to 07-project/out/), two variants built with options:
# basics-print (an extra styles layer, --style) and manual-review (all
# variants marked, --review).  Example 04 only runs 'check' and prints its
# diagnostics: it contains deliberate mistakes and warnings; the same for
# 10-code/forbidden.prml and 10-code/mistakes.prml (Python habits that fail).
set -u
here=$(cd "$(dirname "$0")" && pwd)
launcher="$here/../primula"
out="$here/out"
pdf=0
lang="${PRIMULA_LANG:-}"
while [ $# -gt 0 ]; do
    case "$1" in
        --pdf) pdf=1 ;;
        --lang) shift; lang="${1:-en}" ;;
        *) echo "unknown option: $1" >&2; exit 2 ;;
    esac
    shift
done
mkdir -p "$out"

# primula <args...>: run the CLI from the source tree through the launcher.
primula() { PRIMULA_LANG="$lang" python3 "$launcher" "$@"; }

# build <dir/name> <output name> [options...]: build one document into out/.
build() {
    doc=$1 name=$2
    shift 2
    echo "=== $doc.prml -> $name.odt${*:+ ($*)}"
    (
        cd "$here/$(dirname "$doc")" || exit 2
        set -- build "$(basename "$doc").prml" -o "$out/$name.odt" --report "$out/$name.report.json" \
            --build-date 2026-10-12 "$@"
        [ "$pdf" = 1 ] && set -- "$@" --pdf "$out/$name.pdf"
        primula "$@"
    )
}

status=0
for doc in 01-basics/basics 02-contract/contract 03-manual/manual 05-loan/loan 06-safety/safety; do
    build "$doc" "$(basename "$doc")" || status=1
done
for doc in business letter technical report compact; do
    build "08-styles/$doc" "styles-$doc" || status=1
done
for doc in agreement protocol; do
    build "09-parallel/$doc" "parallel-$doc" || status=1
done
build 10-code/code code || status=1
build 11-library/project/рахунок library-invoice || status=1
build 12-payment-qr/рахунок payment-qr-invoice || status=1
build 13-estimate/кошторис estimate || status=1
build 14-bibliography/реферат bibliography || status=1
build 15-own-commands/власні-команди own-commands || status=1
# Example 16: the documents made by "primula import" from the sources next to them are built like any other.
build 16-import/договір import-contract || status=1
build 16-import/інструкція import-manual || status=1
build 16-import/акт import-act || status=1
build 01-basics/basics basics-print --style std/styles/default --style styles/print.s.prml || status=1
build 03-manual/manual manual-review --review || status=1

# Example 7 is a project: its targets are written inside the project
# directory (07-project/out/), the report of the batch build goes to out/.
echo "=== 07-project/project.p.prml -> 07-project/out/ (batch build of the project)"
(
    cd "$here/07-project" || exit 2
    set -- build project.p.prml --report "$out/project.report.json" --build-date 2026-10-12
    [ "$pdf" = 1 ] && set -- "$@" --pdf
    primula "$@"
) || status=1

echo "=== 01-basics: evaluated tree -> out/basics.tree.txt"
(cd "$here/01-basics" && primula check --dump-tree basics.prml > "$out/basics.tree.txt") || status=1

for doc in syntax evaluation warnings; do
    echo "=== 04-errors/$doc.prml (diagnostics expected)"
    (cd "$here/04-errors" && primula check "$doc.prml")
done
for doc in forbidden mistakes; do
    echo "=== 10-code/$doc.prml (diagnostics expected)"
    (cd "$here/10-code" && primula check "$doc.prml")
done

echo "=== 11-library/shared/ua-iban: tests of the library"
PRIMULA="$launcher" "$here/11-library/shared/ua-iban/run-tests.sh" || status=1
echo "=== libraries/payment_qr: tests of the library"
PRIMULA="$launcher" "$here/../libraries/payment_qr/run-tests.sh" || status=1
for library in estimate bib; do
    echo "=== libraries/$library: tests of the library"
    PRIMULA="$launcher" "$here/../libraries/$library/run-tests.sh" || status=1
done
exit $status
