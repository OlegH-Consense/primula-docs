"""Static check of Python fragments against the whitelist (specification 12.2).

Allowed: literals (``None``, ``True``, ``False``, integers, decimals,
strings, f-strings, lists, tuples, dictionaries); operators
``+ - * / // % **``, unary ``- +``, comparisons (including chains),
``and``, ``or``, ``not``, ``in``, ``not in``, ``is None``, ``is not None``,
``x if c else y``; indexing, slicing, attributes, calls with ``*args`` and
``**kwargs``; list and dict comprehensions, generator expressions;
assignment, unpacking, ``+=`` and similar, ``if``/``elif``/``else``,
``for``, ``while``, ``break``, ``continue``, ``pass``, ``return``; ``def``
with defaults, ``*args``, ``**kwargs``, keyword-only parameters.

Not allowed (error at the position of the construct, P2101): ``class``,
decorators other than ``@export`` (decision 135), annotations, ``import``, ``from``, ``try``, ``raise``,
``with``, ``global``, ``nonlocal``, ``del``, ``lambda``, ``yield``,
``async``, ``await``, ``:=``, ``match``, set literals, ``else`` on loops,
``assert``, bitwise operators and ``@``, bytes, complex numbers, ``...``.

Additional checks: ``@export`` / ``@export(name="…")`` only on a ``def``
at the top level of a code block (P2106, decision 135);
``is``/``is not`` only with ``None`` (P2103); names
and attributes with double underscores and attributes starting with ``_``
(P2102) — they could reach Python internals; ``return`` outside a function
and ``break``/``continue`` outside a loop (P2104), which :func:`ast.parse`
does not reject.

The check runs over the whole document before evaluation (from stage 13.2
in ``primula check``), so a forbidden construct is reported even in code
that is never executed.
"""

from __future__ import annotations

import ast

from primula.diagnostics import Diagnostic, error
from primula.syntax.pyfrag import PyCode, PyFragment

_EXPRESSIONS: frozenset[type] = frozenset({
    ast.BoolOp, ast.BinOp, ast.UnaryOp, ast.IfExp, ast.Dict, ast.List, ast.Tuple,
    ast.ListComp, ast.DictComp, ast.GeneratorExp, ast.comprehension, ast.Compare, ast.Call,
    ast.keyword, ast.Starred, ast.FormattedValue, ast.JoinedStr, ast.Constant, ast.Attribute,
    ast.Subscript, ast.Slice, ast.Name, ast.Load, ast.Store,
    ast.And, ast.Or, ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow,
    ast.UAdd, ast.USub, ast.Not, ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE,
    ast.In, ast.NotIn, ast.Is, ast.IsNot,
})
_STATEMENTS: frozenset[type] = frozenset({
    ast.Module, ast.Expression, ast.FunctionDef, ast.arguments, ast.arg, ast.Return, ast.Assign,
    ast.AugAssign, ast.For, ast.While, ast.If, ast.Expr, ast.Pass, ast.Break, ast.Continue,
})
ALLOWED: frozenset[type] = _EXPRESSIONS | _STATEMENTS

#: Operator and context nodes: they have no position of their own.
_OPERATOR_NODES = (ast.operator, ast.unaryop, ast.cmpop, ast.boolop, ast.expr_context)

#: Names of forbidden constructs for messages.
_CONSTRUCTS: dict[str, str] = {
    "ClassDef": "class", "Lambda": "lambda", "Import": "import", "ImportFrom": "from … import",
    "Try": "try", "TryStar": "try", "Raise": "raise", "With": "with", "AsyncWith": "async with",
    "Global": "global", "Nonlocal": "nonlocal", "Delete": "del", "Yield": "yield",
    "YieldFrom": "yield from", "AsyncFunctionDef": "async def", "AsyncFor": "async for",
    "Await": "await", "NamedExpr": ":=", "Match": "match", "Set": "set literal",
    "SetComp": "set comprehension", "Assert": "assert", "AnnAssign": "annotation",
    "BitOr": "|", "BitAnd": "&", "BitXor": "^", "LShift": "<<", "RShift": ">>", "Invert": "~",
    "MatMult": "@", "TypeAlias": "type", "MatchAs": "match",
}


def _dunder(name: str | None) -> bool:
    return bool(name) and name.startswith("__") and name.endswith("__")  # type: ignore[union-attr]


def export_name(node: ast.FunctionDef) -> str | None:
    """The exported name of a ``def`` decorated with ``@export`` (decision 135), else ``None``.

    ``@export`` exports the function under its own name, ``@export(name="x")``
    under ``x``.  Any other decorator, or a malformed ``@export``, gives
    ``None``; the checker reports it.
    """
    if len(node.decorator_list) != 1:
        return None
    decorator = node.decorator_list[0]
    if isinstance(decorator, ast.Name) and decorator.id == "export":
        return node.name
    if (isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Name) and decorator.func.id == "export"
            and not decorator.args and len(decorator.keywords) == 1 and decorator.keywords[0].arg == "name"):
        value = decorator.keywords[0].value
        if isinstance(value, ast.Constant) and isinstance(value.value, str) and value.value.isidentifier():
            return value.value
    return None


def _is_export(decorator: ast.expr) -> bool:
    """``@export`` or ``@export(…)`` in any form (to tell a misplaced export from another decorator)."""
    func = decorator.func if isinstance(decorator, ast.Call) else decorator
    return isinstance(func, ast.Name) and func.id == "export"


class _Checker:
    """Walks an AST and collects diagnostics."""

    def __init__(self, fragment: PyFragment) -> None:
        self.fragment = fragment
        self.problems: list[Diagnostic] = []
        #: ``def`` statements directly in the module body: the only place of ``@export``.
        self.top_level: set[int] = set()

    def report(self, code: str, node: ast.AST, **args: object) -> None:
        self.problems.append(error(code, self.fragment.span_of(node), **args))

    def forbidden(self, node: ast.AST, construct: str | None = None) -> None:
        name = construct or _CONSTRUCTS.get(type(node).__name__, type(node).__name__.lower())
        self.report("P2101", node, construct=name)

    def visit(self, node: ast.AST, *, function: bool, loop: bool) -> None:
        """Check ``node`` and its children.

        Args:
            node: the node.
            function: inside a ``def`` body (``return`` allowed).
            loop: inside a loop of the current function (``break`` allowed).
        """
        kind = type(node)
        if isinstance(node, ast.Module):
            self.top_level = {id(s) for s in node.body if isinstance(s, ast.FunctionDef)}
        if isinstance(node, _OPERATOR_NODES):
            return  # operators are checked (and reported) on their expression
        if kind not in ALLOWED:
            self.forbidden(node)
            return
        if isinstance(node, (ast.BinOp, ast.AugAssign, ast.UnaryOp)) and type(node.op) not in ALLOWED:
            self.forbidden(node, _CONSTRUCTS.get(type(node.op).__name__))
            return
        if isinstance(node, ast.Constant):
            self._constant(node)
        elif isinstance(node, ast.Compare):
            self._compare(node)
        elif isinstance(node, ast.Name) and _dunder(node.id):
            self.report("P2102", node, name=node.id)
        elif isinstance(node, ast.Attribute) and node.attr.startswith("_"):
            self.report("P2102", node, name=node.attr)
            if not _dunder(node.attr):
                # module._name: a private name of a module (10.3), not only a Python internal.
                self.problems[-1].hint("help.private_name")
        elif isinstance(node, ast.keyword) and _dunder(node.arg):
            self.report("P2102", node, name=node.arg)
        elif isinstance(node, ast.comprehension) and node.is_async:
            self.forbidden(node, "async for")
        elif isinstance(node, (ast.For, ast.While)) and node.orelse:
            self.forbidden(node, "else on a loop")
        elif isinstance(node, ast.Return) and not function:
            self.report("P2104", node, statement="return")
        elif isinstance(node, (ast.Break, ast.Continue)) and not loop:
            self.report("P2104", node, statement="break" if isinstance(node, ast.Break) else "continue")
        elif isinstance(node, ast.FunctionDef):
            self._function(node)
            return
        elif isinstance(node, ast.arg):
            if node.annotation is not None:
                self.forbidden(node.annotation, "annotation")
            if _dunder(node.arg):
                self.report("P2102", node, name=node.arg)
            return

        inner_loop = loop or isinstance(node, (ast.For, ast.While))
        for child in ast.iter_child_nodes(node):
            if isinstance(node, (ast.For, ast.While)) and child in getattr(node, "orelse", []):
                continue
            # The loop condition and iterable are not inside the loop body.
            child_loop = inner_loop
            if isinstance(node, ast.For) and child in (node.target, node.iter):
                child_loop = loop
            if isinstance(node, ast.While) and child is node.test:
                child_loop = loop
            self.visit(child, function=function, loop=child_loop)

    def _constant(self, node: ast.Constant) -> None:
        value = node.value
        if isinstance(value, bytes):
            self.forbidden(node, "bytes")
        elif isinstance(value, complex):
            self.forbidden(node, "complex number")
        elif value is Ellipsis:
            self.forbidden(node, "...")

    def _compare(self, node: ast.Compare) -> None:
        operands = [node.left, *node.comparators]
        for index, op in enumerate(node.ops):
            if isinstance(op, (ast.Is, ast.IsNot)):
                right = operands[index + 1]
                if not (isinstance(right, ast.Constant) and right.value is None):
                    self.report("P2103", node)

    def _function(self, node: ast.FunctionDef) -> None:
        if node.decorator_list:
            # The only decorator is @export on a top-level def (decision 135).
            if not any(_is_export(d) for d in node.decorator_list):
                self.forbidden(node.decorator_list[0], "decorator")
            elif id(node) not in self.top_level or export_name(node) is None:
                self.report("P2106", node.decorator_list[0])
        if node.returns is not None:
            self.forbidden(node.returns, "annotation")
        if _dunder(node.name):
            self.report("P2102", node, name=node.name)
        self.visit(node.args, function=True, loop=False)
        for statement in node.body:
            self.visit(statement, function=True, loop=False)


def check_tree(tree: ast.AST, fragment: PyFragment, *, function: bool = False) -> list[Diagnostic]:
    """Check an AST of a fragment against the whitelist.

    Args:
        tree: the AST (module, expression, call, ``for``/``def`` wrapper).
        fragment: its position map.
        function: treat the code as a function body (``return`` allowed).

    Returns:
        Diagnostics in source order (empty if the code is allowed).
    """
    checker = _Checker(fragment)
    checker.visit(tree, function=function, loop=False)
    return checker.problems


def check_call_args(call: ast.Call, fragment: PyFragment) -> list[Diagnostic]:
    """Check the arguments of a command (``_(…)`` wrapper; the wrapper is not user code)."""
    problems: list[Diagnostic] = []
    for node in [*call.args, *call.keywords]:
        problems.extend(check_tree(node, fragment))
    return problems


def check_loop_head(node: ast.For, fragment: PyFragment) -> list[Diagnostic]:
    """Check the target and the iterable of ``|for(…)`` (body is the wrapper's ``pass``)."""
    return check_tree(node.target, fragment) + check_tree(node.iter, fragment)


def check_macro_head(node: ast.FunctionDef, fragment: PyFragment) -> list[Diagnostic]:
    """Check the parameters of ``|def name(params):`` (body is markup)."""
    problems = check_tree(node.args, fragment)
    if _dunder(node.name):
        problems.append(error("P2102", fragment.span_of(node), name=node.name))
    return problems


# ----------------------------------------------------------------------
# Whole documents
# ----------------------------------------------------------------------


def check_code_block(code: PyCode) -> list[Diagnostic]:
    """Check a code block: whitelist plus top-level ``x += …`` (P2105, decision 40)."""
    problems = check_tree(code.module, code.fragment)
    for statement in code.module.body:
        if isinstance(statement, ast.AugAssign) and isinstance(statement.target, ast.Name):
            problems.append(error("P2105", code.fragment.span_of(statement), name=statement.target.id))
    return problems


def check_document(document: object) -> list[Diagnostic]:
    """Check every Python fragment of a parsed document (12.2).

    Walks the tree generically and checks command arguments, expressions,
    loop heads, macro headers and code blocks, so that forbidden
    constructs are reported even in code that is never evaluated.

    Args:
        document: a :class:`~primula.syntax.nodes.Document`.

    Returns:
        Diagnostics in tree order.
    """
    from primula.syntax.pyfrag import PyArgs, PyDef, PyExpr, PyFor

    problems: list[Diagnostic] = []

    def visit(value: object) -> None:
        if isinstance(value, PyArgs):
            problems.extend(check_call_args(value.call, value.fragment))
        elif isinstance(value, PyExpr):
            problems.extend(check_tree(value.node, value.fragment))
        elif isinstance(value, PyFor):
            problems.extend(check_loop_head(value.node, value.fragment))
        elif isinstance(value, PyDef):
            problems.extend(check_macro_head(value.node, value.fragment))
        elif isinstance(value, PyCode):
            problems.extend(check_code_block(value))
        elif isinstance(value, list):
            for item in value:
                visit(item)
        elif hasattr(value, "__dataclass_fields__") and hasattr(value, "span"):
            for name in value.__dataclass_fields__:  # type: ignore[attr-defined]
                if name not in ("span", "source", "name_span"):
                    visit(getattr(value, name))

    visit(document)
    return problems
