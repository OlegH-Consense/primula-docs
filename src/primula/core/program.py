"""Top level of code: definitions and actions (specification 12.7, decision 40).

The same rules apply to ``|code:`` blocks of a document, ``|import``
modules, styles modules and projects:

* **definitions** — ``name = expression``, unpacking into names
  (``a, b = …``, also ``a = b = …``), ``def``; and, from stage 13.3,
  ``|let``.  They are registered in the :class:`GlobalScope` lazily:
  evaluated on first access and frozen.  ``x += …`` at the top level is an
  error (a repeated definition, P2105);
* **actions** — all other top-level statements (``for``, ``if``,
  ``while``, calls such as ``paragraph_style(…)``, assignments to items).
  They run in document order after all definitions are collected, so they
  see every global name.  Names bound inside an action are local to it;
  the linter warns when such a name is never read in the action (P2501:
  probably a conditional definition that should be a conditional
  expression ``rate = 20 if vat else 0``).

Usage::

    program = Program(interp, scope)
    program.add_code(code_block)          # for every block, in document order
    program.run_actions(sink)             # after all blocks are added
"""

from __future__ import annotations

import ast
from dataclasses import dataclass

from primula.core.check import check_tree, export_name
from primula.core.errors import CoreError, core_error
from primula.core.interp import Interpreter, bound_names
from primula.core.scope import Env, GlobalScope, Shared
from primula.diagnostics import DiagnosticSink, warning
from primula.syntax.pyfrag import PyCode, PyFragment


@dataclass(eq=False)
class Action:
    """A top-level statement executed in document order."""

    statement: ast.stmt
    fragment: PyFragment


def _target_names(target: ast.expr) -> list[str] | None:
    """Names of a definition target, or ``None`` if it is not names only."""
    if isinstance(target, ast.Name):
        return [target.id]
    if isinstance(target, (ast.Tuple, ast.List)):
        names: list[str] = []
        for element in target.elts:
            inner = element.value if isinstance(element, ast.Starred) else element
            sub = _target_names(inner)
            if sub is None:
                return None
            names.extend(sub)
        return names
    return None


class Program:
    """Definitions and actions of the code of one global scope.

    Args:
        interp: the interpreter.
        scope: the global scope that receives the definitions.
    """

    def __init__(self, interp: Interpreter, scope: GlobalScope) -> None:
        self.interp = interp
        self.scope = scope
        self.actions: list[Action] = []
        #: ``def`` decorated with ``@export`` (decision 135): (exported name, def name, span),
        #: in the order of the code; the evaluator decides whether the file may export.
        self.exports: list[tuple[str, str, object]] = []

    def add_code(self, code: PyCode, sink: DiagnosticSink) -> None:
        """Check a code block, register its definitions, collect its actions.

        Errors (forbidden constructs, repeated definitions, top-level
        ``+=``) are reported to ``sink``; the remaining statements are
        still registered.
        """
        problems = check_tree(code.module, code.fragment)
        for problem in problems:
            sink.emit(problem)
        if problems:
            # Forbidden constructs: the block is not registered at all, so
            # that no half-checked code runs.
            return
        for statement in code.module.body:
            try:
                self._add_statement(statement, code.fragment)
            except CoreError as exc:
                sink.emit(exc.diagnostic)

    def _add_statement(self, statement: ast.stmt, frag: PyFragment) -> None:
        interp, scope = self.interp, self.scope
        if isinstance(statement, ast.Assign):
            target_names = [_target_names(target) for target in statement.targets]
            if all(names is not None for names in target_names):
                self._define_assignment(statement, target_names, frag)  # type: ignore[arg-type]
                return
        elif isinstance(statement, ast.FunctionDef):
            scope.define(statement.name, lambda: interp.make_function(statement, scope, frag),
                         frag.span_of(statement))
            exported = export_name(statement)
            if exported is not None:
                self.exports.append((exported, statement.name, frag.span_of(statement.decorator_list[0])))
            return
        elif isinstance(statement, ast.AugAssign) and isinstance(statement.target, ast.Name):
            raise core_error("P2105", frag.span_of(statement), name=statement.target.id)
        elif isinstance(statement, ast.Pass):
            return
        self.actions.append(Action(statement, frag))

    def _define_assignment(self, statement: ast.Assign, target_names: list[list[str]],
                           frag: PyFragment) -> None:
        """Register the names of ``a = b = …`` / ``a, b = …`` as one shared computation."""
        interp, scope = self.interp, self.scope

        def compute() -> dict[str, object]:
            env = Env(scope, None, None)
            value = interp.eval(statement.value, env, frag)
            for target in statement.targets:
                interp.assign(target, value, env, frag)
            return env.vars

        shared = Shared(compute)
        for names, target in zip(target_names, statement.targets):
            for name in names:
                span = frag.span_of(target) if isinstance(target, ast.Name) else frag.span_of(statement)
                scope.define(name, lambda name=name: shared.get()[name], span)

    def run_actions(self, sink: DiagnosticSink) -> None:
        """Execute the actions in order; report errors and linter warnings.

        An error in one action is reported and the next actions still run,
        so that independent problems are all shown.
        """
        for action in self.actions:
            self.run_action(action, sink)

    def run_action(self, action: Action, sink: DiagnosticSink) -> None:
        """Execute one action (document evaluation interleaves programs, decision 54)."""
        statement, frag = action.statement, action.fragment
        self._lint(statement, frag, sink)
        env = Env(self.scope, None, bound_names([statement]))
        try:
            self.interp.exec_block([statement], env, frag)
        except CoreError as exc:
            sink.emit(exc.diagnostic)

    @staticmethod
    def _lint(statement: ast.stmt, frag: PyFragment, sink: DiagnosticSink) -> None:
        """P2501: a name bound in an action and never read in it."""
        stores: dict[str, ast.AST] = {}
        loads: set[str] = set()
        for node in ast.walk(statement):
            if isinstance(node, ast.Name):
                if isinstance(node.ctx, ast.Store):
                    stores.setdefault(node.id, node)
                else:
                    loads.add(node.id)
        for name, node in stores.items():
            if name not in loads and not name.startswith("_"):
                sink.emit(warning("P2501", frag.span_of(node), name=name).hint("help.conditional_definition"))
