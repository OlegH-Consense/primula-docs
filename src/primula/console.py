"""The evaluator console: ``primula console [FILE]`` (stage 14.15; decision 128).

A session evaluates a series of inputs in one context and keeps the names
the inputs define, so that library and own functions can be tried out:

* the **context** is that of FILE — a document or fragment (its header
  parameters, ``doc``, the project, the styles and the definitions of its
  code: phases of definitions and actions, without the text), a project
  file (``project.*``, parameters, its code section), a module (its names,
  as after ``|import``), a styles module (its names and styles); without
  FILE — the standard library only;
* an **input** is Primula code (12): definitions (``x = …``, ``def``) and
  actions run as in a code block; when its last statement is an
  expression, its value is shown.  Each input that defines names opens a
  new level over the previous ones, so a name may be defined again (the
  console is for trying; a document keeps the rule of one definition);
  definitions are evaluated at once, so that their errors appear with the
  input.  ``debug(…)`` lines are the output of the input;
* **console commands** start with ``:`` and are not Primula code:
  ``:help NAME``, ``:functions [TEXT]``, ``:vars``, ``:reset``,
  ``:context``.

Limits (12.8) apply to each input; ``build()`` registers nothing.

Protocol of ``--json`` (Primula Studio): the first line of the output is
``{"ready": true, "context": {...}, "messages": [...], "names": [...]}``;
then each input line ``{"input": "code"}`` gives one output line ``{"ok":
bool, "value": str | null, "output": [str], "messages": [...], "text": str,
"names": [...]}`` (``text`` — the messages and the result of a console
command as text; ``names`` — the names visible to the next input, see
:meth:`ConsoleSession.names`; decision 129).  Without
``--json`` the console reads lines from the terminal (``>>>``; a line
ending with ``:`` or an open bracket continues until an empty line).
"""

from __future__ import annotations

import ast
import datetime
import json
import signal
import sys
import time
from pathlib import Path
from typing import Any, TextIO

from primula.core.errors import CoreError
from primula.core.scope import DONE, Env, GlobalScope
from primula.core.values import type_name
from primula.diagnostics import DiagnosticSink, Severity, error, render_text, to_json
from primula.evaluate.evaluator import DocumentEvaluator, EvalOptions
from primula.evaluate.loader import LoadedFile, Loader
from primula.functions import FUNCTIONS, Function, show, signature
from primula.header import kind_from_name, parse_header
from primula.i18n import Catalog
from primula.source import SourceFile, SourceManager, Span
from primula.syntax import pyfrag

#: Console commands (not Primula code).
COMMANDS = (":help", ":functions", ":vars", ":reset", ":context", ":quit")
_LANGS = ("en", "uk", "ru")


class _Interrupted(Exception):
    """SIGINT during an input (Ctrl+C, or Studio's «Interrupt»)."""


class ConsoleSession:
    """One console: the context of a file and the names of the inputs.

    Args:
        path: the file whose context the console has, or ``None``.
        catalog: messages of the console language.
        manager: source manager.
        project: the project (:class:`~primula.evaluate.project.Project`) or ``None``.
        params: ``--param`` values of a document: name -> (value, text).
        build_date: value of ``build_date()``.
        styles: styles modules of ``--style``.
    """

    def __init__(self, path: Path | None, catalog: Catalog, manager: SourceManager, *, project: Any = None,
                 params: dict[str, tuple[Any, str]] | None = None, build_date: datetime.date | None = None,
                 styles: list[Path] | None = None) -> None:
        self.catalog = catalog
        self.index = _LANGS.index(catalog.language) if catalog.language in _LANGS else 0
        self.path = path
        self.project = project
        self.sink = DiagnosticSink(error_limit=0)
        root = project.root if project is not None else (path.resolve().parent if path else Path.cwd())
        self.loader = Loader(root=root, manager=manager, sink=self.sink)
        options = EvalOptions(build_date=build_date or (project.build_date if project is not None else None)
                              or datetime.date.today(), styles=list(styles or []), project=project,
                              params=dict(params or {}))
        if project is not None:
            options.limits = project.limits
        self.evaluator = DocumentEvaluator(self.loader, self.sink, options)
        self.interp = self.evaluator.interp
        self.kind = "none"
        self.inputs = 0
        self.context_scope = self._with_math(self._context(path, manager))
        self.scope = self.context_scope
        self.ready_messages = list(self.sink.diagnostics)

    # ------------------------------------------------------------------
    # The context
    # ------------------------------------------------------------------

    def _context(self, path: Path | None, manager: SourceManager) -> GlobalScope:
        evaluator = self.evaluator
        if path is None:
            return evaluator.interp.new_globals(parent=evaluator._load_project())
        self.kind = kind_from_name(path.name) or "document"
        if self.kind == "project":
            # The project of a project file is itself (the CLI loads it).
            return evaluator._load_project()
        if self.kind == "module":
            return evaluator.module_scope(path.resolve())
        if self.kind == "styles":
            # The names and styles of the module, through an empty document that uses it.
            evaluator.options.styles = [*evaluator.options.styles, path.resolve()]
            source = SourceFile.from_text(str(path.resolve().parent / "<console>.prml"), "")
            return evaluator.prepare(self._loaded(source))
        source = manager.load(path.resolve(), str(path))
        return evaluator.prepare(self._loaded(source))

    def _with_math(self, scope: GlobalScope) -> GlobalScope:
        """The context with ``math`` (std/math) always available (decision 130).

        In a document ``|import("std/math")`` is still required; the console
        is for trying things, so it binds ``math`` as an import would.  A name
        ``math`` of the context itself (an alias, a parameter) is kept.

        Args:
            scope: the scope of the file, project or library.

        Returns:
            a level above ``scope`` that defines ``math``, or ``scope`` itself.
        """
        from primula.core.values import Record
        from primula.library.prelude import std_module

        if "math" in self._names(scope):
            return scope
        level = self.interp.new_globals(parent=scope)
        level.define_value("math", Record(std_module(self.evaluator.library, "std/math") or {}), None)
        return level

    def _loaded(self, source: SourceFile) -> LoadedFile:
        from primula.syntax.parser import parse

        header = parse_header(source, self.sink)
        document = parse(header, self.sink, organize=False)
        path = getattr(source, "path", None) or Path(source.name)
        loaded = LoadedFile(Path(path), source, header, document)
        self.loader._files[loaded.path] = loaded
        return loaded

    def context(self) -> dict[str, Any]:
        """The description of the context: kind, file, project, names of the context."""
        names = sorted(self._names(self.context_scope))
        return {"kind": self.kind, "file": str(self.path) if self.path else None,
                "project": str(self.project.path) if self.project is not None else None, "names": names}

    def names(self) -> list[dict[str, Any]]:
        """The names visible to the next input, for the «Names» list of Studio (decision 129).

        Returns:
            ``{"name", "type", "value", "origin"}`` for each name: ``origin`` is
            ``input`` (defined by an input; the latest level first) or ``context``
            (the names of the file, the project). ``type`` and ``value`` (shown,
            at most 80 characters) are given only for evaluated names: a lazy
            definition of the context is not evaluated for the list (``type``
            ``""``, ``value`` ``None``).
        """
        rows: list[dict[str, Any]] = []
        seen: set[str] = set()
        scope: GlobalScope | None = self.scope
        while scope is not None:
            origin = "input" if self._is_input_level(scope) else "context"
            for name, definition in scope.definitions.items():
                if name.startswith("_") or name in seen:
                    continue
                seen.add(name)
                done = definition.state == DONE
                value = show(definition.value) if done else None
                if value is not None and len(value) > 80:
                    value = value[:79] + "…"
                rows.append({"name": name, "type": type_name(definition.value) if done else "",
                             "value": value, "origin": origin})
            scope = scope.parent
        return rows

    def _is_input_level(self, scope: GlobalScope) -> bool:
        """The level belongs to an input: it lies above the context scope."""
        level: GlobalScope | None = self.scope
        while level is not None and level is not self.context_scope:
            if level is scope:
                return True
            level = level.parent
        return False

    @staticmethod
    def _names(scope: GlobalScope | None) -> set[str]:
        names: set[str] = set()
        while scope is not None:
            names.update(name for name in scope.definitions if not name.startswith("_"))
            scope = scope.parent
        return names

    # ------------------------------------------------------------------
    # Inputs
    # ------------------------------------------------------------------

    def run(self, text: str) -> dict[str, Any]:
        """Evaluate one input (or run a console command).

        Returns:
            ``ok``, ``value`` (shown value of a final expression or ``None``),
            ``output`` (``debug`` lines), ``messages`` (JSON form, 14.2) and
            ``text`` (the messages, or the answer of a console command).
        """
        if text.strip().startswith(":"):
            answer = self.command(text.strip())
            return {"ok": True, "value": None, "output": [], "messages": [], "text": answer, "names": self.names()}
        self.inputs += 1
        start, debug_start = len(self.sink.diagnostics), len(self.interp.ctx.debug)
        value: str | None = None
        previous = signal.signal(signal.SIGINT, _interrupt) if _main_thread() else None
        try:
            value = self._evaluate(text)
        except _Interrupted:
            self.sink.emit(error("P0006", None, at_file=f"<console-{self.inputs}>"))
        except CoreError as exc:
            self.sink.emit(exc.diagnostic)
        finally:
            if previous is not None:
                signal.signal(signal.SIGINT, previous)
            self.interp.meter.depth = 0
        diagnostics = self.sink.diagnostics[start:]
        output = [line for _span, line in self.interp.ctx.debug[debug_start:]]
        ok = not any(d.severity is Severity.ERROR for d in diagnostics)
        return {"ok": ok, "value": value if ok else None, "output": output,
                "messages": [to_json(d, self.catalog) for d in diagnostics],
                "text": "\n".join(render_text(d, self.catalog) for d in diagnostics), "names": self.names()}

    def _evaluate(self, text: str) -> str | None:
        source = SourceFile.from_text(f"<console-{self.inputs}>", text.rstrip("\n") + "\n")
        try:
            code = pyfrag.parse_code(source, [(0, 0, source.text.rstrip("\n"))], Span(source, 0, len(source.text)))
        except pyfrag.PySyntaxError as exc:
            self.sink.emit(exc.diagnostic)
            return None
        from primula.core.check import check_tree
        from primula.core.program import Program

        problems = check_tree(code.module, code.fragment)
        for problem in problems:
            self.sink.emit(problem)
        if problems:
            return None
        body = code.module.body
        last = body.pop() if body and isinstance(body[-1], ast.Expr) else None
        scope = self.interp.new_globals(parent=self.scope)
        program = Program(self.interp, scope)
        self.interp.meter.begin()
        errors = self.sink.error_count
        program.add_code(code, self.sink)
        for _exported, _name, span in program.exports:
            # The console is no fragment: @export has nowhere to go (decision 135).
            self.sink.emit(error("P2610", span))
        if self.sink.error_count > errors:
            return None
        for action in program.actions:
            program.run_action(action, self.sink)
        # Definitions are evaluated now: their errors belong to this input.
        for name in list(scope.definitions):
            try:
                scope.lookup(name, None)
            except CoreError as exc:
                self.sink.emit(exc.diagnostic)
        if scope.definitions and self.sink.error_count == errors:
            self.scope = scope
        if last is None or self.sink.error_count > errors:
            return None
        # The final expression sees this input's names (and, through the levels, the earlier ones).
        result = self.interp.eval(last.value, Env(scope), code.fragment)
        return None if result is None else show(result)

    # ------------------------------------------------------------------
    # Console commands
    # ------------------------------------------------------------------

    def command(self, text: str) -> str:
        """The answer of a console command (``:help``, ``:functions``, ``:vars``, ``:reset``, ``:context``)."""
        name, _, argument = text.partition(" ")
        argument = argument.strip()
        t = self.catalog.text
        if name == ":help":
            if not argument:
                return t("console.help")
            found = [f for f in FUNCTIONS if f.name == argument.split(".")[-1]]
            return "\n\n".join(self._describe(f) for f in found) if found else t("console.unknown_function", name=argument)
        if name == ":functions":
            needle = argument.casefold()
            rows = [f"{signature(f)}  — {f.text[self.index]}" for f in FUNCTIONS
                    if not needle or needle in f.name.casefold() or needle in f.text[self.index].casefold()]
            return "\n".join(rows) if rows else t("console.no_functions", text=argument)
        if name == ":vars":
            lines = []
            scope: GlobalScope | None = self.scope
            while scope is not None and scope is not self.context_scope:
                for key, definition in scope.definitions.items():
                    value = show(definition.value) if definition.state == DONE else "…"
                    if len(value) > 80:
                        value = value[:79] + "…"
                    lines.append(f"{key}: {type_name(definition.value) if definition.state == DONE else '?'} = {value}")
                scope = scope.parent
            context = ", ".join(sorted(self._names(self.context_scope)))
            return "\n".join([*reversed(lines), t("console.context_names", names=context or "—")])
        if name == ":reset":
            self.scope = self.context_scope
            return t("console.reset")
        if name == ":context":
            info = self.context()
            return t("console.context", kind=info["kind"], file=info["file"] or "—", project=info["project"] or "—")
        return t("console.unknown_command", name=name, commands=", ".join(COMMANDS))

    def _describe(self, function: Function) -> str:
        """``:help``: signature, summary, arguments, where, example with its result, section."""
        from primula.functions import example_runner

        lines = [signature(function), "  " + function.text[self.index]]
        for arg in function.args:
            default = f" = {arg.default}" if arg.default is not None else ""
            lines.append(f"    {arg.name}: {arg.type}{default} — {arg.text[self.index]}")
        if function.example:
            result = ""
            if function.run:
                try:
                    result = "  →  " + show(example_runner(self.catalog.language)(function.example))
                except CoreError:
                    result = ""
            lines.append("  " + self.catalog.text("console.example", example=function.example + result))
        section = ("stdlib " if function.doc == "stdlib" else "") + function.section
        lines.append("  " + self.catalog.text("console.section", section=section))
        return "\n".join(lines)


def _interrupt(signum: int, frame: Any) -> None:
    raise _Interrupted()


def _main_thread() -> bool:
    import threading

    return threading.current_thread() is threading.main_thread()


def _complete(text: str) -> bool:
    """A terminal input is complete: no trailing ':' and no open brackets."""
    stripped = text.rstrip()
    if stripped.endswith(":"):
        return False
    depth = 0
    for char in stripped:
        depth += char in "([{"
        depth -= char in ")]}"
    return depth <= 0


def run_console(session: ConsoleSession, stdin: TextIO, out: TextIO, *, as_json: bool) -> int:
    """Read inputs from stdin until its end (or ``:quit``) and answer each one.

    Returns:
        The exit code: 0.
    """
    if as_json:
        print(json.dumps({"ready": True, "context": session.context(),
                          "messages": [to_json(d, session.catalog) for d in session.ready_messages],
                          "names": session.names()},
                         ensure_ascii=False), file=out, flush=True)
        for line in stdin:
            if not line.strip():
                continue
            try:
                request = json.loads(line)
                text = request.get("input", "") if isinstance(request, dict) else str(request)
            except json.JSONDecodeError:
                text = line.rstrip("\n")
            if text.strip() == ":quit":
                break
            print(json.dumps(session.run(text), ensure_ascii=False), file=out, flush=True)
        return 0
    interactive = stdin.isatty()
    for diagnostic in session.ready_messages:
        print(render_text(diagnostic, session.catalog), file=out)
    if interactive:
        print(session.catalog.text("console.banner", kind=session.kind), file=out)
    buffer: list[str] = []
    while True:
        if interactive:
            print("... " if buffer else ">>> ", end="", file=out, flush=True)
        line = stdin.readline()
        if not line:
            break
        line = line.rstrip("\n")
        if buffer or not _complete(line):
            if line.strip():
                buffer.append(line)
                continue
            text, buffer = "\n".join(buffer), []
        else:
            text = line
        if not text.strip():
            continue
        if text.strip() == ":quit":
            break
        result = session.run(text)
        for output in result["output"]:
            print(output, file=out)
        if result["text"]:
            print(result["text"], file=out)
        if result["value"] is not None:
            print(result["value"], file=out)
        out.flush()
    return 0
