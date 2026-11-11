"""``primula import SOURCE [-o OUT.prml]``: a document of another format → Primula text (stage 19.3).

The steps: the source is read by pandoc (:mod:`primula.importer.reader`), the tree is converted
(:class:`~primula.importer.convert.Converter`), the YAML header is made from the metadata, the images go to
``assets/`` next to the result, the result is written (an existing file is not replaced without ``--force``)
and checked by ``primula check``; the report says what was converted and what was left out.
"""

from __future__ import annotations

import io
import json
from pathlib import Path
from typing import Any, TextIO

from primula.diagnostics import DiagnosticSink, error
from primula.importer.convert import Converter, Report, string
from primula.importer.normalize import Options, normalize
from primula.importer.styles import StyleMap, apply_styles, describe_styles_used, find_map_file, load_map, skeleton
from primula.importer.reader import ImportFailure, read_ast


def _meta_text(meta: dict, key: str) -> str:
    """The text of a metadata field of the AST (a string, inlines or a list of them), or ``""``."""
    value = meta.get(key)
    if value is None:
        return ""

    def text(node: Any) -> str:
        if isinstance(node, dict):
            kind, content = node.get("t"), node.get("c")
            if kind == "Str":
                return content
            if kind in ("Space", "SoftBreak", "LineBreak"):
                return " "
            if kind == "MetaString":
                return content
            if kind in ("MetaInlines", "MetaBlocks", "Para", "Plain", "Emph", "Strong", "Span", "Quoted", "Link"):
                if kind in ("Span", "Link"):
                    content = content[1]
                if kind == "Quoted":
                    content = content[1]
                return text(content)
            if kind == "MetaList":
                return ", ".join(t for t in (text(item) for item in content) if t)
            return ""
        if isinstance(node, list):
            return "".join(text(item) for item in node).strip()
        return ""

    return " ".join(text(value).split())


#: Vector formats of Word that Primula cannot use; LibreOffice makes SVG of them.
_CONVERTED = {".emf", ".wmf"}


def _image_paths(node: Any) -> list[str]:
    """Paths of all images of an AST (an inline ``Image`` has the path in ``c[2][0]``)."""
    found: list[str] = []
    if isinstance(node, dict):
        if node.get("t") == "Image":
            found.append(node["c"][2][0])
        for value in node.values():
            found += _image_paths(value)
    elif isinstance(node, list):
        for value in node:
            found += _image_paths(value)
    return found


def convert_vector_images(ast: dict, directory: Path, report: Report) -> dict[str, str]:
    """SVG made by LibreOffice from the images of the source in EMF and WMF; returns old path → new path.

    An image that cannot be converted stays as it is (the check of the result reports it) and is noted.
    """
    from primula.odf.pdf import find_soffice

    import subprocess
    import tempfile

    mapping: dict[str, str] = {}
    wanted = sorted({p for p in _image_paths(ast["blocks"]) if Path(p).suffix.lower() in _CONVERTED})
    if not wanted:
        return mapping
    soffice = find_soffice()
    for path in wanted:
        source = directory / path
        if soffice is None or not source.is_file():
            report.note(f"an image in {Path(path).suffix.upper()[1:]} (Primula needs PNG, JPEG or SVG; LibreOffice converts it)")
            continue
        with tempfile.TemporaryDirectory(prefix="primula-import-") as temporary:
            command = [soffice, f"-env:UserInstallation=file://{temporary}/profile", "--headless", "--convert-to", "svg",
                       "--outdir", str(source.parent), str(source)]
            try:
                subprocess.run(command, capture_output=True, timeout=120, check=False)
            except (OSError, subprocess.TimeoutExpired):
                pass
        converted = source.with_suffix(".svg")
        if converted.is_file():
            mapping[path] = str(Path(path).with_suffix(".svg"))
            report.count("images converted to SVG")
        else:
            report.note(f"an image in {Path(path).suffix.upper()[1:]} that could not be converted")
    return mapping


def _guess_title(blocks: list) -> str:
    """The title of a document without metadata: a short line in capitals before the first heading ("ДОГОВІР ПОСТАВКИ № 15"),
    else the text of the first heading."""
    from primula.importer.normalize import plain

    for block in blocks:
        if block["t"] == "Header":
            return " ".join(plain(block["c"][2]).split())
        if block["t"] in ("Para", "Plain"):
            text = " ".join(plain(block["c"]).split())
            letters = [c for c in text if c.isalpha()]
            if 0 < len(text) <= 100 and len(letters) >= 4 and text.upper() == text:
                return text
    return ""


def header(meta: dict, source: Path, language: str, blocks: list | None = None) -> str:
    """The YAML header of the result: ``doc`` with the title, the language and the author of the source.

    The title is the metadata field ``title``, else the text of the first heading, else the name of the file.
    """
    from primula.importer.normalize import plain

    title = _meta_text(meta, "title") or _guess_title(blocks or []) or source.stem
    fields = [f"title: {json.dumps(title, ensure_ascii=False)}", f"language: {language}"]
    author = _meta_text(meta, "author")
    if author:
        fields.append(f"creator: {json.dumps(author, ensure_ascii=False)}")
    return "---\ndoc:\n" + "".join(f"  {field}\n" for field in fields) + "---\n"


def convert_file(source: Path, output: Path, *, language: str, fmt: str | None = None, media: str = "assets",
                 numbered: bool = True, structure: bool = True, styles_file: Path | None = None
                 ) -> tuple[str, Report, StyleMap]:
    """Read ``source`` and return the Primula text of the result and the report.

    Args:
        source: the document to import.
        output: the file to be written (its directory is where the images go and where the paths are relative to).
        language: ``doc.language`` of the result.
        fmt: the pandoc reader instead of the one of the extension.
        media: the directory of the extracted images, relative to the directory of ``output``.
        numbered: the typed numbers are removed and Primula numbers the headings and clauses; ``False`` — the typed
            numbers stay in the text and the headings get ``number=False``.
        structure: recognize the headings, clauses and the table of contents (:mod:`primula.importer.normalize`).

    Raises:
        ImportFailure: the source cannot be read.
    """
    output.parent.mkdir(parents=True, exist_ok=True)
    ast = read_ast(source, fmt, Path(media), output.parent)
    report = Report()
    converter = Converter(numbered=numbered, report=report, images=convert_vector_images(ast, output.parent, report))
    map_path = styles_file or find_map_file(output)
    style_map, problems = load_map(map_path)
    for problem in problems:
        report.note(problem)
    blocks = apply_styles(ast["blocks"], style_map, report)
    blocks = normalize(blocks, report, Options(keep_numbers=not numbered, structure=structure))
    body = "\n".join(converter.blocks(blocks)).rstrip("\n")
    return header(ast.get("meta", {}), source, language, blocks) + body + "\n", report, style_map


def run_import(args: Any, catalog: Any, stream: TextIO, out: TextIO) -> int:
    """The command ``primula import``; returns the exit code."""
    from primula.cli import EXIT_ERROR, EXIT_OK

    source: Path = args.source
    if not source.is_file():
        print(error_text(catalog, "P0101", file=str(source)), file=stream)
        return EXIT_ERROR
    output: Path = args.output or source.with_suffix(".prml")
    listing = args.list_styles
    if output.exists() and not args.force and not listing:
        print(error_text(catalog, "P8205", file=str(output)), file=stream)
        return EXIT_ERROR
    if args.write_styles is not None and args.write_styles.exists() and not args.force:
        print(error_text(catalog, "P8205", file=str(args.write_styles)), file=stream)
        return EXIT_ERROR
    try:
        if listing:
            # Only the styles: the conversion runs in a temporary directory, nothing is written next to the source.
            import tempfile

            with tempfile.TemporaryDirectory(prefix="primula-import-") as temporary:
                text, report, style_map = convert_file(source, Path(temporary) / "x.prml", language=args.language, fmt=args.format_from,
                                                       media=args.media, numbered=not args.keep_numbers,
                                                       structure=not args.no_structure, styles_file=args.styles)
        else:
            text, report, style_map = convert_file(source, output, language=args.language, fmt=args.format_from, media=args.media,
                                                   numbered=not args.keep_numbers, structure=not args.no_structure,
                                                   styles_file=args.styles)
    except ImportFailure as failure:
        print(error_text(catalog, failure.code, **failure.fields), file=stream)
        return EXIT_ERROR
    if args.write_styles is not None:
        args.write_styles.write_text(skeleton(report, style_map), encoding="utf-8", newline="\n")
        print(catalog.text("import.written", file=str(args.write_styles)), file=out)
    if listing:
        found = describe_styles_used(report, style_map)
        print("\n".join(found) if found else catalog.text("import.no_styles"), file=out)
        return EXIT_OK
    output.write_text(text, encoding="utf-8", newline="\n")
    print(catalog.text("import.written", file=str(output)), file=out)
    for line in report.lines():
        print(line, file=out)
    # The check of the result: a draft without parsing errors is what the import promises.
    from primula.cli import main as run_cli

    buffer = io.StringIO()
    code = run_cli(["check", str(output), "--lang", catalog.language], out=buffer, err=buffer)
    last = [line for line in buffer.getvalue().splitlines() if line.strip()]
    print(catalog.text("import.check", summary=last[-1] if last else ""), file=out)
    if code != EXIT_OK:
        print(buffer.getvalue().rstrip(), file=stream)
    return EXIT_OK if code == EXIT_OK else EXIT_ERROR


def error_text(catalog: Any, code: str, **fields: str) -> str:
    """One line of an error for the output of the command."""
    return f"primula: error[{code}]: {catalog.text(code, **fields)}"
