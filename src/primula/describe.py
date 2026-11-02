"""Summary of a Primula file that is not built into a document: ``primula describe FILE`` (stage 18.9).

A module, a styles module and a project have no output document, so there
is nothing to show in a viewer; this command tells what is inside::

    module    the leading comment, ``VERSION``, public functions with their
              signatures and one-line descriptions, constants, the number of
              private names (the code is not run: the source is read with
              :mod:`ast`)
    styles    ``extends``, ``defaults`` and the styles the module defines
              (name, kind, parent), found through the style system
    project   name, language, parameters, keys, styles, targets
    document  the metadata and the parameters of the header (a fragment too)

The JSON form (``--format json``) is meant for Studio (help on the functions
of the modules of a project, decision of the plan: Д3); ``schema`` changes
when the meaning of a field changes.

A description of a function comes from its docstring (the first paragraph);
without one, from the comment lines right above ``def``.
"""

from __future__ import annotations

import ast
import re
import tempfile
from pathlib import Path
from typing import Any

from primula.diagnostics import DiagnosticSink, to_json
from primula.i18n import Catalog
from primula.source import SourceManager

#: Version of the JSON form.
DESCRIBE_SCHEMA = 1
#: Length limit of a constant's value and of a one-line description.
_VALUE_LIMIT = 70
_SUMMARY_LIMIT = 120


def _first_paragraph(text: str) -> str:
    """The first paragraph of a docstring or a comment as one line, cut to the limit."""
    paragraph = re.split(r"\n\s*\n", text.strip(), maxsplit=1)[0]
    line = " ".join(paragraph.split())
    return line if len(line) <= _SUMMARY_LIMIT else line[:_SUMMARY_LIMIT - 1] + "…"


def _comment_above(lines: list[str], line: int) -> str:
    """The consecutive ``#`` comment lines right above the 1-based ``line``, joined; ``""`` if none."""
    found: list[str] = []
    index = line - 2
    while index >= 0 and lines[index].lstrip().startswith("#"):
        found.append(lines[index].lstrip().lstrip("#").strip())
        index -= 1
    return " ".join(reversed(found))


def code_blocks(text: str) -> list[tuple[int, str]]:
    """The ``|code:`` … ``|end`` blocks of a module body.

    Args:
        text: the body (after the header).

    Returns:
        ``(first line number of the block's code, code)`` pairs; the number is
        1-based in ``text``.  An unclosed block runs to the end of the text.
    """
    blocks: list[tuple[int, str]] = []
    current: list[str] | None = None
    start = 0
    for number, line in enumerate(text.splitlines(), 1):
        if current is None:
            if line.rstrip() == "|code:":
                current, start = [], number + 1
        elif line.rstrip() == "|end":
            blocks.append((start, "\n".join(current)))
            current = None
        else:
            current.append(line)
    if current is not None:
        blocks.append((start, "\n".join(current)))
    return blocks


def leading_comment(text: str) -> list[str]:
    """The ``|%`` comment lines at the top of a module body (before the first non-comment line)."""
    found: list[str] = []
    for line in text.splitlines():
        if line.startswith("|%"):
            found.append(line[2:].strip())
        elif line.strip():
            break
    return found


def _signature(node: ast.FunctionDef) -> str:
    return f"{node.name}({ast.unparse(node.args)})"


def describe_module(body: str, line_offset: int, problems: list[str]) -> dict[str, Any]:
    """Summary of a module by its source (the code is not run).

    Args:
        body: text after the header.
        line_offset: lines of the file before ``body`` (for the line numbers).
        problems: receives the description of a block that cannot be parsed.

    Returns:
        ``summary`` (leading comment lines), ``version``, ``functions``,
        ``constants``, ``private`` (count).
    """
    comment = leading_comment(body)
    functions: list[dict[str, Any]] = []
    constants: list[dict[str, Any]] = []
    private = 0
    version = None
    for first_line, code in code_blocks(body):
        lines = code.splitlines()
        try:
            tree = ast.parse(code)
        except SyntaxError as exc:
            problems.append(f"{line_offset + first_line + (exc.lineno or 1) - 1}: {exc.msg}")
            continue
        for node in tree.body:
            line = line_offset + first_line + node.lineno - 1
            if isinstance(node, ast.FunctionDef):
                if node.name.startswith("_"):
                    private += 1
                    continue
                doc = ast.get_docstring(node) or ""
                summary = _first_paragraph(doc) if doc else _first_paragraph(_comment_above(lines, node.lineno))
                functions.append({"name": node.name, "signature": _signature(node), "summary": summary,
                                  "exported": any(ast.unparse(d).startswith("export") for d in node.decorator_list),
                                  "line": line})
            elif isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                name = node.targets[0].id
                if name.startswith("_"):
                    private += 1
                    continue
                value = ast.unparse(node.value)
                shown = value if len(value) <= _VALUE_LIMIT else value[:_VALUE_LIMIT - 1] + "…"
                if name == "VERSION" and isinstance(node.value, ast.Constant):
                    version = str(node.value.value)
                constants.append({"name": name, "value": shown,
                                  "summary": _first_paragraph(_comment_above(lines, node.lineno)), "line": line})
    return {"summary": comment, "version": version, "functions": functions, "constants": constants,
            "private": private}


def describe_styles(path: Path, header_data: dict[Any, Any], manager: SourceManager,
                    sink: DiagnosticSink) -> dict[str, Any]:
    """Summary of a styles module: ``extends``, ``defaults`` and the styles defined by this file.

    The styles come from the style system itself (a throw-away document that
    names the module with ``--style``), so inheritance and ``extends`` are
    resolved as in a build; a style belongs to the module when one of its
    definitions lies in the file.
    """
    from primula.dumps import make_dump
    from primula.frontend import analyze

    own: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="primula-describe-") as work:
        document = Path(work) / "probe.prml"
        document.write_text("---\ndoc:\n  title: probe\n---\nprobe\n", encoding="utf-8")
        result = analyze(document, DiagnosticSink(), SourceManager(), styles=[path])
        dump = make_dump(result, file=str(document), structure=False, styles=True, messages=[])
    styles = (dump.get("styles") or {}).get("styles") or []
    target = path.resolve()
    for style in styles:
        if any(Path(d.get("path", "")).resolve() == target for d in style.get("definitions", [])):
            own.append({"name": style["name"], "kind": style["kind"], "parent": style.get("parent")})
    extends = header_data.get("extends")
    defaults = header_data.get("defaults")
    return {"extends": extends if isinstance(extends, (str, list)) else None,
            "defaults": {str(k): str(v) for k, v in defaults.items()} if isinstance(defaults, dict) else {},
            "styles": own}


def describe_project(path: Path, manager: SourceManager, sink: DiagnosticSink, catalog: Catalog) -> dict[str, Any]:
    """Summary of a project: the descriptive section as read by ``--dump-project``."""
    from primula.evaluate.project import dump_project, load_project

    project = load_project(path, manager, sink)
    data = dump_project(path, project, sink, catalog)
    return {key: data.get(key) for key in ("name", "language", "styles", "params", "keys", "targets",
                                           "ref_documents", "doc_defaults", "build_date")}


def describe(path: Path, catalog: Catalog) -> dict[str, Any]:
    """Describe a file by its kind.

    Args:
        path: the file.
        catalog: the message catalogue (for the messages of reading the header and the project).

    Returns:
        ``schema``, ``file``, ``kind`` and the fields of the kind (see the
        module description); ``messages`` — diagnostics of reading the file
        (an unreadable file gives ``kind: null``).
    """
    from primula.header import parse_header
    from primula.frontend import load_root

    sink = DiagnosticSink()
    manager = SourceManager()
    data: dict[str, Any] = {"schema": DESCRIBE_SCHEMA, "file": str(path), "kind": None}
    source = load_root(path, sink, manager)
    if source is not None:
        header = parse_header(source, sink)
        data["kind"] = header.kind
        text = source.text
        body = text[header.body_start:]
        offset = text.count("\n", 0, header.body_start)
        problems: list[str] = []
        if header.kind == "module":
            data.update(describe_module(body, offset, problems))
        elif header.kind == "styles":
            data.update(describe_styles(path, header.data, manager, sink))
        elif header.kind == "project":
            data.update(describe_project(path, manager, sink, catalog))
        else:
            doc = header.data.get("doc") if isinstance(header.data.get("doc"), dict) else {}
            params = header.data.get("params") if isinstance(header.data.get("params"), dict) else {}
            data["doc"] = {str(k): str(v) for k, v in doc.items()}
            data["params"] = {str(k): (v if isinstance(v, (str, int, float, bool, type(None))) else "…")
                              for k, v in params.items()}
        if problems:
            data["parse_problems"] = problems
    data["messages"] = [to_json(d, catalog) for d in sink.ordered()]
    return data


def render_text(data: dict[str, Any], catalog: Catalog) -> str:
    """The text form of :func:`describe` in the language of the catalogue."""
    t = catalog.text
    kind = data.get("kind")
    out: list[str] = []
    if kind is None:
        out.append(t("describe.unreadable", file=data["file"]))
        out += [f"  {m.get('code', '')}: {m.get('message', '')}" for m in data.get("messages", [])]
        return "\n".join(out) + "\n"
    out.append(f"{t('describe.kind.' + kind) if kind in ('module', 'styles', 'project') else t('describe.kind.document')}"
               f": {data['file']}")
    none = t("describe.none")
    if kind == "module":
        if data.get("summary"):
            out += ["", *data["summary"]]
        if data.get("version"):
            out.append(t("describe.version", version=data["version"]))
        out += ["", t("describe.functions", n=len(data["functions"]))]
        for f in data["functions"]:
            out.append(f"  {f['signature']}" + (f" — {f['summary']}" if f["summary"] else f"  [{t('describe.undocumented')}]"))
        if not data["functions"]:
            out.append(f"  {none}")
        if data["constants"]:
            out += ["", t("describe.constants", n=len(data["constants"]))]
            for c in data["constants"]:
                out.append(f"  {c['name']} = {c['value']}" + (f" — {c['summary']}" if c["summary"] else ""))
        out += ["", t("describe.private", n=data["private"])]
    elif kind == "styles":
        extends = data.get("extends")
        out.append(t("describe.extends", names=", ".join(extends) if isinstance(extends, list) else extends or none))
        if data.get("defaults"):
            out.append(t("describe.defaults", values=", ".join(f"{k}: {v}" for k, v in data["defaults"].items())))
        out += ["", t("describe.styles", n=len(data["styles"]))]
        by_kind: dict[str, list[str]] = {}
        for s in data["styles"]:
            by_kind.setdefault(s["kind"], []).append(s["name"] + (f" ← {s['parent']}" if s.get("parent") else ""))
        for style_kind, names in sorted(by_kind.items()):
            out.append(f"  {style_kind} ({len(names)}): " + "; ".join(names))
        if not data["styles"]:
            out.append(f"  {none}")
    elif kind == "project":
        out.append(t("describe.name", name=data.get("name") or none))
        out.append(t("describe.language", language=data.get("language") or none))
        out.append(t("describe.styles_used", styles=", ".join(data.get("styles") or []) or none))
        params = data.get("params") or {}
        out += ["", t("describe.params", n=len(params))]
        out += [f"  {name}: {info.get('type')}" for name, info in params.items()] or [f"  {none}"]
        keys = data.get("keys") or {}
        out += ["", t("describe.keys", n=len(keys))]
        out += [f"  {key} → {value}" for key, value in keys.items()] or [f"  {none}"]
        targets = data.get("targets") or []
        out += ["", t("describe.targets", n=len(targets))]
        out += [f"  {target['source']} → {target['output']}" for target in targets] or [f"  {none}"]
    else:
        doc = data.get("doc") or {}
        out += [f"  {k}: {v}" for k, v in doc.items()]
        params = data.get("params") or {}
        if params:
            out += ["", t("describe.params", n=len(params))] + [f"  {k}: {v}" for k, v in params.items()]
    for problem in data.get("parse_problems", []):
        out += ["", t("describe.parse_problem", problem=problem)]
    return "\n".join(out) + "\n"
