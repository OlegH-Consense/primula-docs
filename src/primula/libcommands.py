"""Commands that a module defines with ``|def`` (macros) and their use by a document (stage 28.0).

A library module extends the language with commands: ``|def note(title, body=None):`` …
``|enddef`` in ``box.m.prml``, imported by ``|import("box")``, is called as ``|box.note(…)``.
Editors and Studio need the signature of such a command without running any code, so the
source is read statically (the way :mod:`primula.describe` reads the functions of a module)::

    scan_macros(text)           the ``|def`` headers of a module body: name, parameters,
                                the kind of the body, the description from the ``|%`` comment
                                right above ``|def``
    document_commands(path)     the commands of the modules that the document imports with
                                ``|import("path")`` (``alias=`` and imported names are honoured; an unsaved buffer of the editor, ``--overlay``, is read instead of the file)

What is not seen: imports in included fragments (``.f.prml``) and in code blocks, modules
under ``std/`` (they have functions, not commands), a path that is not a string literal.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Any

from primula.source import read_source_bytes

#: ``|def name(params):`` at the start of a line (names may be in any script: ``\w`` is Unicode).
_DEF = re.compile(r"^\|def\s+([^\W\d]\w*)\s*\((.*)\)\s*:\s*$")
#: ``|import("path", names…, alias="x")`` — only a string path is understood.
_IMPORT = re.compile(r'\|import\(\s*"([^"]+)"([^)]*)\)')
_ALIAS = re.compile(r'alias\s*=\s*"([^"]+)"')
_NAME = re.compile(r'"([^"]+)"')
_SUMMARY_LIMIT = 120


def _params(text: str) -> tuple[list[dict[str, Any]], str] | None:
    """Parameters of a header as ``({name, default}, signature)``; ``None`` if they do not parse."""
    try:
        node = ast.parse(f"def f({text}): pass").body[0]
    except SyntaxError:
        return None
    assert isinstance(node, ast.FunctionDef)
    args = node.args
    positional = [*args.posonlyargs, *args.args]
    defaults: list[ast.expr | None] = [None] * (len(positional) - len(args.defaults)) + list(args.defaults)
    found = [{"name": a.arg, "default": None if d is None else ast.unparse(d)} for a, d in zip(positional, defaults)]
    found += [{"name": a.arg, "default": None if d is None else ast.unparse(d)}
              for a, d in zip(args.kwonlyargs, args.kw_defaults)]
    return found, ast.unparse(args)


def scan_macros(text: str, line_offset: int = 0) -> list[dict[str, Any]]:
    """The public macros (``|def`` not starting with ``_``) of a module body.

    Args:
        text: the module text after the header.
        line_offset: lines of the file before ``text`` (for the line numbers).

    Returns:
        One dictionary per macro: ``name``, ``signature``, ``params`` (``name``, ``default``, ``summary``),
        ``body`` (``"none"``, ``"optional"`` or ``"required"``: a parameter ``body`` takes
        the body of the call, 4.2), ``summary`` and ``line`` (1-based in the file).  A comment line
        ``|% name: text`` above ``|def`` describes the parameter ``name`` (``params[i]["summary"]``);
        the other comment lines are the summary of the command (decision 145).  A header
        that does not parse as parameters is left out.
    """
    lines = text.splitlines()
    macros: list[dict[str, Any]] = []
    for index, line in enumerate(lines):
        match = _DEF.match(line)
        if match is None or match.group(1).startswith("_"):
            continue
        parsed = _params(match.group(2))
        if parsed is None:
            continue
        params, signature = parsed
        comment: list[str] = []
        above = index - 1
        while above >= 0 and lines[above].startswith("|%"):
            comment.append(lines[above][2:].strip())
            above -= 1
        # Lines «name: text» whose name is a parameter describe that parameter; the others describe the command.
        names = {p["name"] for p in params}
        described: dict[str, str] = {}
        description: list[str] = []
        for text in reversed(comment):
            head, colon, rest = text.partition(":")
            if colon and head.strip() in names and rest.strip():
                described[head.strip()] = rest.strip()
            else:
                description.append(text)
        for param in params:
            param["summary"] = described.get(param["name"], "")
        summary = " ".join(description)
        if len(summary) > _SUMMARY_LIMIT:
            summary = summary[:_SUMMARY_LIMIT - 1] + "…"
        body_param = next((p for p in params if p["name"] == "body"), None)
        body = "none" if body_param is None else "required" if body_param["default"] is None else "optional"
        macros.append({"name": match.group(1), "signature": f"{match.group(1)}({signature})", "params": params,
                       "body": body, "summary": summary, "line": line_offset + index + 1})
    return macros


def _snippet(qualified: str, macro: dict[str, Any]) -> str:
    """An insertion template in the form of the other snippets of the catalogue (``${1:name}``, ``$0``)."""
    required = [p["name"] for p in macro["params"] if p["default"] is None and p["name"] != "body"]
    arguments = ", ".join(f"${{{i}:{name}}}" for i, name in enumerate(required, 1))
    return f"|{qualified}({arguments})" + ("{$0}" if macro["body"] == "required" else "")


def _project_root(start: Path) -> Path:
    """The nearest directory upwards from ``start`` with ``project.p.prml``; ``start`` without one."""
    for directory in (start, *start.parents):
        if (directory / "project.p.prml").is_file():
            return directory
    return start


def _module_file(base: Path, root: Path, text: str) -> Path | None:
    """The file of ``|import("text")`` inside the project root, or ``None`` (10.1: the extension may be omitted)."""
    if text.startswith(("std/", "/", "\\")) or "://" in text or Path(text).is_absolute():
        return None
    from primula.paths import lexical, within

    candidate = lexical(base / text)
    if within(candidate, root) is None:
        return None
    options = [candidate] if candidate.name.endswith(".prml") else \
        [candidate.with_name(candidate.name + ".m.prml"), candidate.with_name(candidate.name + ".prml")]
    return next((p for p in options if p.is_file()), None)


def _strip_header(text: str) -> tuple[str, int]:
    """The text after the YAML header and the number of lines before it."""
    if not text.startswith("---"):
        return text, 0
    end = re.search(r"^---[ \t]*$", text[3:], re.MULTILINE)
    if end is None:
        return text, 0
    start = 3 + end.end()
    return text[start:], text.count("\n", 0, start)


def document_commands(path: Path) -> list[dict[str, Any]]:
    """The commands that the document ``path`` gets from the modules it imports.

    Args:
        path: the document (or a fragment; its own ``|import`` lines are read).

    Returns:
        Entries of the catalogue form for the Studio palette: ``name`` (``namespace.macro``, or
        the macro alone for ``|import("m", macro)``), ``macro`` (the name in the module), the fields of :func:`scan_macros`,
        ``snippet``, ``module`` (the path as written) and ``file`` (relative to the document).
        Modules are listed in the order of the imports; an unreadable module is skipped.
    """
    try:
        text = read_source_bytes(path).decode("utf-8")
    except (OSError, UnicodeDecodeError):
        return []
    root = _project_root(path.resolve().parent)
    entries: list[dict[str, Any]] = []
    for line in text.splitlines():
        if line.startswith("|%"):
            continue
        for match in _IMPORT.finditer(line):
            file = _module_file(path.resolve().parent, root, match.group(1))
            if file is None:
                continue
            try:
                body, offset = _strip_header(read_source_bytes(file).decode("utf-8"))
            except (OSError, UnicodeDecodeError):
                continue
            rest = match.group(2)
            alias = _ALIAS.search(rest)
            names = [n for n in _NAME.findall(_ALIAS.sub("", rest))]
            namespace = alias.group(1) if alias else file.name.split(".")[0]
            for macro in scan_macros(body, offset):
                if names and macro["name"] not in names:
                    continue
                qualified = macro["name"] if names else f"{namespace}.{macro['name']}"
                entries.append({**macro, "macro": macro["name"], "name": qualified, "snippet": _snippet(qualified, macro),
                                "module": match.group(1), "file": str(file.relative_to(path.resolve().parent))
                                if file.is_relative_to(path.resolve().parent) else str(file)})
    return entries
