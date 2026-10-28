"""Interpreter of the computing core (specification 12, decisions 40-46).

A tree-walking evaluator over Python ``ast`` nodes that passed the
whitelist check (:mod:`primula.core.check`).  It never executes Python
code itself: every operation is implemented here or in
:mod:`primula.core.builtins` by the rules of the language:

* numbers by :mod:`primula.core.numbers` (decimal literals, mixing rules);
* strings are Unicode characters; ``%`` formatting and f-strings with
  width checks against the string limit;
* lists and dictionaries are :class:`~primula.core.values.PList` and
  :class:`~primula.core.values.PDict`; frozen values and collections being
  iterated cannot be changed (P2318, P2319);
* names follow Python scoping (:mod:`primula.core.scope`);
* every evaluated node is a step (decision 42); sizes are checked before
  values are created.

Positions: every node belongs to a :class:`~primula.syntax.pyfrag.PyFragment`
passed along as ``frag``; spans are computed only when an error is raised.
"""

from __future__ import annotations

import ast
import datetime
import decimal
import operator
import sys
from dataclasses import dataclass, field
from decimal import Decimal
from fractions import Fraction
from typing import Any, Iterator

from primula.core import numbers
from primula.core.errors import CoreError, LimitError, Where, core_error, resolve
from primula.core.limits import Meter
from primula.core.scope import Env, GlobalScope
from primula.core.values import (
    EXACT_CONTEXT, LENGTH_TOLERANCE, BoundMethod, Builtin, DateTime, DateTimeError, Function, Length, PDict,
    PList, Record, convert_length, digits_ok, fraction_to_decimal, freeze,
    is_number, is_valid_key, to_repr, to_str, type_name,
)
from primula.diagnostics import DiagnosticSink, error
from primula.unicode import nfkc
from primula.source import Span
from primula.syntax.pyfrag import PyFragment

#: Fast-path operations (no division: zero checks stay in numbers.arith).
_FAST_INT = {"+": operator.add, "-": operator.sub, "*": operator.mul}
_FAST_INT_DIV = {"//": operator.floordiv, "%": operator.mod}
_INT_FAST_BOUND = 10 ** 18
_FAST_COMPARE = {"==": operator.eq, "!=": operator.ne, "<": operator.lt, "<=": operator.le,
                 ">": operator.gt, ">=": operator.ge}
#: Operand type pairs compared directly by Python with the language's result.
_FAST_COMPARE_TYPES = frozenset({(int, int), (Decimal, Decimal), (Decimal, int), (int, Decimal),
                                 (float, float), (float, int), (int, float), (str, str)})
_FAST_DEC = {"+": EXACT_CONTEXT.add, "-": EXACT_CONTEXT.subtract, "*": EXACT_CONTEXT.multiply}
_DEC_OPERANDS = (Decimal, int)
_FAST_FLOAT = {"+": operator.add, "-": operator.sub, "*": operator.mul}
_FLOAT_OPERANDS = (float, int, Decimal)

#: Python frames allowed per Primula call (measured: 10-20).
_FRAMES_PER_CALL = 40

_BINOPS = {ast.Add: "+", ast.Sub: "-", ast.Mult: "*", ast.Div: "/", ast.FloorDiv: "//",
           ast.Mod: "%", ast.Pow: "**"}
_CMPOPS = {ast.Eq: "==", ast.NotEq: "!=", ast.Lt: "<", ast.LtE: "<=", ast.Gt: ">", ast.GtE: ">=",
           ast.In: "in", ast.NotIn: "not in", ast.Is: "is", ast.IsNot: "is not"}


@dataclass
class EvalContext:
    """Environment of an evaluation run.

    Attributes:
        meter: limits (time, recursion, size) and their use.
        build_date: value of ``build_date()`` (12.7).
        sink: receiver of warnings (linter, P25xx); errors are raised.
        debug: ``debug(x)`` records ``(span, text)`` for the report (12.9).
        extra_builtins: names added by document evaluation (``load_*``,
            ``markup``…; stage 13.3) and the standard library (13.9).
    """

    meter: Meter = field(default_factory=Meter)
    build_date: datetime.date = field(default_factory=datetime.date.today)
    sink: DiagnosticSink | None = None
    debug: list[tuple[Span | None, str]] = field(default_factory=list)
    extra_builtins: dict[str, Any] = field(default_factory=dict)


class _Return(Exception):
    def __init__(self, value: Any) -> None:
        self.value = value


class _Break(Exception):
    pass


class _Continue(Exception):
    pass


def bound_names(statements: list[ast.stmt], *, include_params: ast.arguments | None = None) -> frozenset[str]:
    """Names bound in a body (Python scoping): assignment and loop targets,
    ``def`` names, parameters.  Nested function bodies and comprehensions
    have their own scopes and are not searched."""
    names: set[str] = set()
    if include_params is not None:
        params = include_params
        for arg in [*params.posonlyargs, *params.args, *params.kwonlyargs]:
            names.add(arg.arg)
        for arg in (params.vararg, params.kwarg):
            if arg is not None:
                names.add(arg.arg)

    def walk(node: ast.AST) -> None:
        if isinstance(node, ast.FunctionDef):
            names.add(node.name)
            return
        if isinstance(node, (ast.ListComp, ast.DictComp, ast.GeneratorExp, ast.SetComp)):
            return
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            names.add(node.id)
        for child in ast.iter_child_nodes(node):
            walk(child)

    for statement in statements:
        walk(statement)
    return frozenset(names)


class Interpreter:
    """Evaluates expressions and statements of the computing core.

    Args:
        context: the evaluation context (limits, build date, hooks).
    """

    def __init__(self, context: EvalContext | None = None) -> None:
        from primula.core import builtins as _builtins  # cyclic import guard

        self.ctx = context or EvalContext()
        self.meter = self.ctx.meter
        # One Primula call takes about 10-20 Python frames of this tree-walking
        # interpreter; the language limit (12.8) must be reached before
        # Python's own limit.  The setting is process-wide and only raised.
        needed = self.meter.limits.recursion * _FRAMES_PER_CALL + 2000
        if sys.getrecursionlimit() < needed:
            sys.setrecursionlimit(needed)
        self.builtins: dict[str, Any] = {**_builtins.make_builtins(), **self.ctx.extra_builtins}
        self._attr = _builtins.get_attribute
        self._format_string = _builtins.format_string
        self._format_value = _builtins.format_value
        self._eval_dispatch = {
            ast.Constant: self._constant, ast.Name: self._name, ast.BinOp: self._binop,
            ast.UnaryOp: self._unaryop, ast.BoolOp: self._boolop, ast.Compare: self._compare,
            ast.IfExp: self._ifexp, ast.Call: self._call, ast.Attribute: self._attribute,
            ast.Subscript: self._subscript, ast.List: self._list, ast.Tuple: self._tuple,
            ast.Dict: self._dict, ast.ListComp: self._listcomp, ast.GeneratorExp: self._listcomp,
            ast.DictComp: self._dictcomp, ast.JoinedStr: self._joinedstr,
            ast.FormattedValue: self._formatted,
        }
        self._exec_dispatch = {
            ast.Expr: self._s_expr, ast.Assign: self._s_assign, ast.AugAssign: self._s_augassign,
            ast.If: self._s_if, ast.For: self._s_for, ast.While: self._s_while,
            ast.Pass: self._s_pass, ast.Break: self._s_break, ast.Continue: self._s_continue,
            ast.Return: self._s_return, ast.FunctionDef: self._s_def,
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def new_globals(self, parent: GlobalScope | None = None) -> GlobalScope:
        """Create a global scope with the built-in names of this interpreter."""
        return GlobalScope(parent, self.builtins)

    def eval(self, node: ast.expr, env: Env, frag: PyFragment) -> Any:
        """Evaluate an expression node."""
        meter = self.meter
        meter.steps += 1
        if meter.steps >= meter._next_time_check:
            meter.steps -= 1
            meter.step(Where(frag, node))
        handler = self._eval_dispatch.get(type(node))
        if handler is None:  # pragma: no cover - excluded by the whitelist
            raise core_error("P2101", Where(frag, node), construct=type(node).__name__.lower())
        return handler(node, env, frag)

    def exec_block(self, statements: list[ast.stmt], env: Env, frag: PyFragment) -> None:
        """Execute statements (``break``/``continue``/``return`` propagate)."""
        for statement in statements:
            meter = self.meter
            meter.steps += 1
            if meter.steps >= meter._next_time_check:
                meter.steps -= 1
                meter.step(Where(frag, statement))
            self._exec_dispatch[type(statement)](statement, env, frag)

    def span(self, node: ast.AST, frag: PyFragment) -> Span:
        """Source span of a node."""
        return frag.span_of(node)

    # ------------------------------------------------------------------
    # Values used by builtins
    # ------------------------------------------------------------------

    def truthy(self, value: Any) -> bool:
        """Truth value (12.7): empty, zero and ``None`` are false."""
        if value is None or value is False:
            return False
        if value is True:
            return True
        if is_number(value):
            return value != 0
        if isinstance(value, (str, PList, tuple, PDict)):
            return len(value) > 0
        if isinstance(value, Length):
            return value.value != 0
        return True

    def iterate(self, value: Any, span: Span | None) -> Iterator[Any]:
        """Iterate a value; lists and dictionaries are guarded against changes."""
        if isinstance(value, (PList, PDict)):
            value.iterating += 1
            try:
                for item in value:
                    yield item
            finally:
                value.iterating -= 1
        elif isinstance(value, (str, tuple)):
            yield from value
        else:
            raise core_error("P2315", span, type=type_name(value))

    def materialize(self, value: Any, span: Span | None) -> list[Any]:
        """All items of an iterable as a Python list (size-checked)."""
        if isinstance(value, (PList, tuple, str, PDict)):
            self.meter.step(span, len(value))
            return list(value)
        items = list(self.iterate(value, span))
        return items

    def equals(self, left: Any, right: Any, span: Span | None) -> bool:
        """``==`` by the rules of 12.3 (numbers by value, lengths with a tolerance)."""
        if is_number(left) and is_number(right):
            return self._num(numbers.compare, "==", left, right, span)
        if type_name(left) != type_name(right):
            return False
        if isinstance(left, Length):
            return abs(left.inches - right.inches) <= LENGTH_TOLERANCE
        if isinstance(left, (PList, tuple)):
            return len(left) == len(right) and all(self.equals(a, b, span) for a, b in zip(left, right))
        return bool(left == right)

    def less(self, left: Any, right: Any, span: Span | None) -> bool:
        """``<`` by the rules of decision 43 (used by ``sorted``, ``min``…)."""
        return self.compare("<", left, right, span)

    def compare(self, op: str, left: Any, right: Any, span: Span | None) -> bool:
        """Comparison operators of decision 43."""
        if (type(left), type(right)) in _FAST_COMPARE_TYPES and op in _FAST_COMPARE:
            return _FAST_COMPARE[op](left, right)
        if op == "==":
            return self.equals(left, right, span)
        if op == "!=":
            return not self.equals(left, right, span)
        if op in ("is", "is not"):
            return (left is None) == (op == "is") if right is None else left is right
        if op in ("in", "not in"):
            return self._contains(right, left, span) == (op == "in")
        if is_number(left) and is_number(right):
            return self._num(numbers.compare, op, left, right, span)
        kind = type_name(left)
        if kind != type_name(right) or kind not in ("str", "list", "tuple", "datetime", "length"):
            raise core_error("P2305", span, op=op, left=kind, right=type_name(right))
        if kind == "length":
            # Ordering with the tolerance of 0.001 mm (12.3): a < b if b - a > 0.001 mm.
            difference = right.inches - left.inches
            if op == "<":
                return difference > LENGTH_TOLERANCE
            if op == ">":
                return -difference > LENGTH_TOLERANCE
            if op == "<=":
                return difference >= -LENGTH_TOLERANCE
            return -difference >= -LENGTH_TOLERANCE
        if kind == "datetime":
            left, right = left.seconds, right.seconds
        elif kind in ("list", "tuple"):
            for a, b in zip(left, right):
                if not self.equals(a, b, span):
                    return self.compare(op, a, b, span)
            left, right = len(left), len(right)
        return {"<": left < right, "<=": left <= right, ">": left > right, ">=": left >= right}[op]

    def _contains(self, container: Any, item: Any, span: Span | None) -> bool:
        if isinstance(container, str):
            if not isinstance(item, str):
                raise core_error("P2301", span, op="in", left=type_name(item), right="str")
            return item in container
        if isinstance(container, (PList, tuple)):
            self.meter.step(span, len(container))
            return any(self.equals(item, element, span) for element in container)
        if isinstance(container, PDict):
            if not is_valid_key(item):
                raise core_error("P2317", span, type=type_name(item))
            return item in container
        raise core_error("P2301", span, op="in", left=type_name(item), right=type_name(container))

    def _num(self, function: Any, op: str, left: Any, right: Any, span: Span | None) -> Any:
        """Call a :mod:`numbers` function, converting its errors."""
        try:
            return function(op, left, right)
        except numbers.NumberError as exc:
            raise core_error(exc.code, span, **_number_args(exc, op, left, right)) from None

    # ------------------------------------------------------------------
    # Expressions
    # ------------------------------------------------------------------

    def _constant(self, node: ast.Constant, env: Env, frag: PyFragment) -> Any:
        cached = getattr(node, "_primula_value", _MISSING)
        if cached is not _MISSING:
            return cached
        value = node.value
        if isinstance(value, float):
            text = frag.segment(node).replace("_", "")
            if text and "e" not in text.lower():
                value = Decimal(text)  # 12.50 -> Decimal('12.50') (12.4)
        elif isinstance(value, int) and not isinstance(value, bool) and not digits_ok(value):
            raise core_error("P2309", Where(frag, node), limit=64)
        node._primula_value = value  # type: ignore[attr-defined]
        return value

    def _name(self, node: ast.Name, env: Env, frag: PyFragment) -> Any:
        try:
            return env.lookup(node.id, None)
        except CoreError as exc:
            if exc.diagnostic.span is None:
                exc.diagnostic.span = frag.span_of(node)
            raise

    def _binop(self, node: ast.BinOp, env: Env, frag: PyFragment) -> Any:
        left = self.eval(node.left, env, frag)
        right = self.eval(node.right, env, frag)
        return self.binary(_BINOPS[type(node.op)], left, right, Where(frag, node))

    def binary(self, op: str, left: Any, right: Any, where: Any) -> Any:
        """Binary operation; ``where`` is a span or a :class:`Where`."""
        # Fast paths for the most frequent operand types (exact type checks:
        # bool is not int here).  They follow numbers.arith exactly; every
        # other case goes through the general path below.
        tl, tr = type(left), type(right)
        if tl is int and tr is int and op in _FAST_INT_DIV and right != 0:
            return _FAST_INT_DIV[op](left, right)
        if tl is int and tr is int and op in _FAST_INT:
            result = _FAST_INT[op](left, right)
            if -_INT_FAST_BOUND < result < _INT_FAST_BOUND or digits_ok(result):
                return result
            raise core_error("P2309", where, limit=64)
        if (tl is Decimal or tr is Decimal) and tl in _DEC_OPERANDS and tr in _DEC_OPERANDS \
                and op in _FAST_DEC:
            try:
                result = _FAST_DEC[op](left if tl is Decimal else Decimal(left),
                                       right if tr is Decimal else Decimal(right))
            except decimal.Inexact:
                raise core_error("P2309", where, limit=64) from None
            if digits_ok(result):
                return result
            raise core_error("P2309", where, limit=64)
        if (tl is float or tr is float) and tl in _FLOAT_OPERANDS and tr in _FLOAT_OPERANDS \
                and op in _FAST_FLOAT:
            return _FAST_FLOAT[op](float(left), float(right))
        if is_number(left) and is_number(right):
            return self._num(numbers.arith, op, left, right, where)
        return self._binary_other(op, left, right, where)

    def _binary_other(self, op: str, left: Any, right: Any, span: Span) -> Any:
        meter = self.meter
        if op == "+":
            if isinstance(left, str) and isinstance(right, str):
                meter.check_string(len(left) + len(right), span)
                return left + right
            if isinstance(left, PList) and isinstance(right, PList):
                meter.check_collection(len(left) + len(right), span)
                meter.step(span, len(left) + len(right))
                return PList(left + right)
            if isinstance(left, tuple) and isinstance(right, tuple):
                meter.check_collection(len(left) + len(right), span)
                return left + right
            if isinstance(left, Length) and isinstance(right, Length):
                return self._length(left, "+", right, span)
            if isinstance(left, DateTime) and is_number(right):
                return self._shift(left, right, span)
            if is_number(left) and isinstance(right, DateTime):
                return self._shift(right, left, span)
        elif op == "-":
            if isinstance(left, Length) and isinstance(right, Length):
                return self._length(left, "-", right, span)
            if isinstance(left, DateTime) and isinstance(right, DateTime):
                # Days, possibly fractional: exact seconds / 86400, 28 digits (12.3).
                difference = left.seconds - right.seconds
                if difference % 86400 == 0:
                    return difference // 86400
                return fraction_to_decimal(Fraction(difference, 86400))
            if isinstance(left, DateTime) and is_number(right):
                return self._shift(left, -right, span)
        elif op == "*":
            if isinstance(right, (str, PList, tuple)) and is_number(left):
                left, right = right, left
            if isinstance(left, (str, PList, tuple)) and is_number(right):
                count = numbers.as_integer(right)
                if count is None:
                    raise core_error("P2322", span, function="*", problem="the repeat count must be an integer")
                count = max(count, 0)
                if isinstance(left, str):
                    meter.check_string(len(left) * count, span)
                else:
                    meter.check_collection(len(left) * count, span)
                meter.step(span, len(left) * count)
                result = left * count
                return PList(result) if isinstance(left, PList) else result
            if isinstance(left, Length) and is_number(right):
                return self._scale(left, "*", right, span)
            if is_number(left) and isinstance(right, Length):
                return self._scale(right, "*", left, span)
        elif op == "/":
            if isinstance(left, Length) and is_number(right):
                return self._scale(left, "/", right, span)
            if isinstance(left, Length) and isinstance(right, Length):
                if right.value == 0:
                    raise core_error("P2303", span)
                return fraction_to_decimal(left.inches / right.inches)
        elif op == "%" and isinstance(left, str):
            return self._format_string(self, left, right, span, percent=True)
        if (isinstance(left, bool) or isinstance(right, bool)) and \
                all(is_number(v) or isinstance(v, bool) for v in (left, right)):
            raise core_error("P2304", span)  # bool takes no part in arithmetic (decision 41)
        raise core_error("P2301", span, op=op, left=type_name(left), right=type_name(right))

    def _length(self, left: Length, op: str, right: Length, span: Span) -> Length:
        """``length ± length``: the result is in the unit of the left operand (12.3)."""
        other = convert_length(right, left.unit)
        value = self._num(numbers.arith, op, left.value, other, span)
        return Length(Decimal(value) if isinstance(value, int) else value, left.unit)

    def _scale(self, length: Length, op: str, factor: Any, span: Span) -> Length:
        """``length * number`` and ``length / number`` (12.3)."""
        factor = _length_factor(factor, span)
        if op == "/" and factor == 0:
            raise core_error("P2303", span)
        value = self._num(numbers.arith, op, length.value, factor, span)
        return Length(Decimal(value) if isinstance(value, int) else value, length.unit)

    def _shift(self, moment: DateTime, days: Any, span: Span) -> DateTime:
        """``dt ± n``: add ``n`` days, rounded to the second, half away from zero (12.3)."""
        if isinstance(days, float):
            if days != days or days in (float("inf"), float("-inf")):
                raise core_error("P2308", span, detail="non-finite float")
            exact = Fraction(Decimal(repr(days)))
        else:
            exact = Fraction(days)
        seconds = exact * 86400
        whole = int(seconds)  # towards zero
        if abs(seconds - whole) >= Fraction(1, 2):
            whole += 1 if seconds > 0 else -1
        try:
            return DateTime.from_seconds(moment.seconds + whole)
        except DateTimeError:
            raise core_error("P2307", span, value=f"{moment.iso()} + {to_repr(days)}", type="datetime") from None

    def _unaryop(self, node: ast.UnaryOp, env: Env, frag: PyFragment) -> Any:
        value = self.eval(node.operand, env, frag)
        if isinstance(node.op, ast.Not):
            return not self.truthy(value)
        if isinstance(value, Length):
            return value if isinstance(node.op, ast.UAdd) else Length(-value.value, value.unit)
        if not is_number(value):
            code = "P2304" if isinstance(value, bool) else "P2301"
            raise core_error(code, Where(frag, node), op="-" if isinstance(node.op, ast.USub) else "+",
                             left=type_name(value), right="")
        if isinstance(node.op, ast.UAdd):
            return value
        return numbers.negate(value)

    def _boolop(self, node: ast.BoolOp, env: Env, frag: PyFragment) -> Any:
        is_and = isinstance(node.op, ast.And)
        value = None
        for operand in node.values:
            value = self.eval(operand, env, frag)
            if self.truthy(value) != is_and:
                return value
        return value

    def _compare(self, node: ast.Compare, env: Env, frag: PyFragment) -> bool:
        left = self.eval(node.left, env, frag)
        for op_node, right_node in zip(node.ops, node.comparators):
            right = self.eval(right_node, env, frag)
            if not self.compare(_CMPOPS[type(op_node)], left, right, Where(frag, node)):
                return False
            left = right
        return True

    def _ifexp(self, node: ast.IfExp, env: Env, frag: PyFragment) -> Any:
        branch = node.body if self.truthy(self.eval(node.test, env, frag)) else node.orelse
        return self.eval(branch, env, frag)

    def _attribute(self, node: ast.Attribute, env: Env, frag: PyFragment) -> Any:
        value = self.eval(node.value, env, frag)
        return self._attr(self, value, node.attr, Where(frag, node))

    def _subscript(self, node: ast.Subscript, env: Env, frag: PyFragment) -> Any:
        value = self.eval(node.value, env, frag)
        span = Where(frag, node)
        if isinstance(node.slice, ast.Slice):
            bounds = [None if part is None else self.eval(part, env, frag)
                      for part in (node.slice.lower, node.slice.upper, node.slice.step)]
            return self.slice(value, bounds, span)
        key = self.eval(node.slice, env, frag)
        return self.index(value, key, span)

    def index(self, value: Any, key: Any, span: Span) -> Any:
        """``value[key]`` for lists, tuples, strings, dictionaries, records."""
        if isinstance(value, (PList, tuple, str)):
            index = numbers.as_integer(key)
            if index is None:
                raise core_error("P2322", span, function="[]",
                                 problem=f"index must be an integer, not {type_name(key)} {to_repr(key)}")
            key = index
            try:
                return value[key]
            except IndexError:
                raise core_error("P2311", span, index=key, size=len(value)) from None
        if isinstance(value, PDict):
            if not is_valid_key(key):
                raise core_error("P2317", span, type=type_name(key))
            if key not in value:
                raise core_error("P2312", span, key=to_repr(key))
            return value[key]
        if isinstance(value, Record):
            name = nfkc(key) if isinstance(key, str) else key
            if not isinstance(name, str) or name not in value.fields:
                raise core_error("P2314", span, name=to_str(key))
            return value.fields[name]
        raise core_error("P2316", span, type=type_name(value), operation="[]")

    def slice(self, value: Any, bounds: list[Any], span: Span) -> Any:
        """``value[a:b:c]`` for lists, tuples, strings."""
        if not isinstance(value, (PList, tuple, str)):
            raise core_error("P2316", span, type=type_name(value), operation="[:]")
        for position, bound in enumerate(bounds):
            if bound is not None:
                bounds[position] = numbers.as_integer(bound)
                if bounds[position] is None:
                    raise core_error("P2322", span, function="[:]", problem="slice bounds must be integers")
        if bounds[2] == 0:
            raise core_error("P2322", span, function="[:]", problem="slice step cannot be zero")
        result = value[slice(*bounds)]
        self.meter.step(span, len(result))
        return PList(result) if isinstance(value, PList) else result

    def _list(self, node: ast.List, env: Env, frag: PyFragment) -> PList:
        return PList(self._elements(node.elts, env, frag, node))

    def _tuple(self, node: ast.Tuple, env: Env, frag: PyFragment) -> tuple:
        return tuple(self._elements(node.elts, env, frag, node))

    def _elements(self, elements: list[ast.expr], env: Env, frag: PyFragment, node: ast.AST) -> list[Any]:
        items: list[Any] = []
        for element in elements:
            if isinstance(element, ast.Starred):
                items.extend(self.materialize(self.eval(element.value, env, frag), Where(frag, element)))
            else:
                items.append(self.eval(element, env, frag))
        self.meter.check_collection(len(items), Where(frag, node) if len(items) > 1000 else None)
        return items

    def _dict(self, node: ast.Dict, env: Env, frag: PyFragment) -> PDict:
        result = PDict()
        for key_node, value_node in zip(node.keys, node.values):
            if key_node is None:  # {**other}
                other = self.eval(value_node, env, frag)
                pairs = other.fields.items() if isinstance(other, Record) else (
                    other.items() if isinstance(other, PDict) else None)
                if pairs is None:
                    raise core_error("P2322", Where(frag, value_node), function="{**}",
                                     problem=f"expected a dict or record, not {type_name(other)}")
                result.update(pairs)
                continue
            key = self.eval(key_node, env, frag)
            if not is_valid_key(key):
                raise core_error("P2317", Where(frag, key_node), type=type_name(key))
            result[key] = self.eval(value_node, env, frag)
        self.meter.check_collection(len(result), Where(frag, node))
        return result

    def _comprehension(self, generators: list[ast.comprehension], env: Env, frag: PyFragment,
                       emit: Any) -> None:
        """Run nested comprehension loops in a new scope, calling ``emit(env)``."""
        scope = Env(env.globals, env, None)

        def loop(index: int) -> None:
            if index == len(generators):
                emit(scope)
                return
            generator = generators[index]
            iterable = self.eval(generator.iter, scope if index else env, frag)
            span = Where(frag, generator.iter)
            for item in self.iterate(iterable, span):
                self.meter.step(span)
                self.assign(generator.target, item, scope, frag)
                if all(self.truthy(self.eval(cond, scope, frag)) for cond in generator.ifs):
                    loop(index + 1)

        loop(0)

    def _listcomp(self, node: ast.ListComp | ast.GeneratorExp, env: Env, frag: PyFragment) -> PList:
        # Generator expressions are evaluated eagerly into a list (no side
        # effects exist, so only the order of errors could differ).
        result = PList()
        limit = self.meter.limits.size

        def emit(scope: Env) -> None:
            result.append(self.eval(node.elt, scope, frag))
            if len(result) > limit:
                self.meter.check_collection(len(result), Where(frag, node))

        self._comprehension(node.generators, env, frag, emit)
        return result

    def _dictcomp(self, node: ast.DictComp, env: Env, frag: PyFragment) -> PDict:
        result = PDict()

        def emit(scope: Env) -> None:
            key = self.eval(node.key, scope, frag)
            if not is_valid_key(key):
                raise core_error("P2317", Where(frag, node.key), type=type_name(key))
            result[key] = self.eval(node.value, scope, frag)
            if len(result) > self.meter.limits.size:
                self.meter.check_collection(len(result), Where(frag, node))

        self._comprehension(node.generators, env, frag, emit)
        return result

    def _joinedstr(self, node: ast.JoinedStr, env: Env, frag: PyFragment) -> str:
        parts: list[str] = []
        size = 0
        for value in node.values:
            text = value.value if isinstance(value, ast.Constant) else self.eval(value, env, frag)
            size += len(text)
            self.meter.check_string(size, Where(frag, node))
            parts.append(text)
        return "".join(parts)

    def _formatted(self, node: ast.FormattedValue, env: Env, frag: PyFragment) -> str:
        value = self.eval(node.value, env, frag)
        span = Where(frag, node)
        if node.conversion == ord("r"):
            value = to_repr(value)
        elif node.conversion in (ord("s"), ord("a")):
            value = to_str(value) if node.conversion == ord("s") else ascii(to_repr(value))
        spec = self.eval(node.format_spec, env, frag) if node.format_spec is not None else ""
        return self._format_value(self, value, spec, span)

    # ------------------------------------------------------------------
    # Calls
    # ------------------------------------------------------------------

    def _call(self, node: ast.Call, env: Env, frag: PyFragment) -> Any:
        function = self.eval(node.func, env, frag)
        args, kwargs = self.eval_arguments(node.args, node.keywords, env, frag, _callable_name(function))
        return self.call(function, args, kwargs, Where(frag, node))

    def eval_arguments(self, positional: list[ast.expr], keywords: list[ast.keyword], env: Env,
                       frag: PyFragment, function_name: str = "") -> tuple[list[Any], dict[str, Any]]:
        """Evaluate call arguments (``*args``, ``**kwargs`` expanded).

        Used for calls in code and for arguments of markup commands.

        Args:
            positional: positional argument nodes (may contain ``Starred``).
            keywords: keyword nodes (``arg`` is ``None`` for ``**``).
            env: evaluation environment.
            frag: position map.
            function_name: name for messages.

        Returns:
            ``(args, kwargs)``.
        """
        args: list[Any] = []
        for arg in positional:
            if isinstance(arg, ast.Starred):
                args.extend(self.materialize(self.eval(arg.value, env, frag), Where(frag, arg)))
            else:
                args.append(self.eval(arg, env, frag))
        kwargs: dict[str, Any] = {}
        for keyword in keywords:
            value = self.eval(keyword.value, env, frag)
            if keyword.arg is None:
                pairs = value.fields.items() if isinstance(value, Record) else (
                    value.items() if isinstance(value, PDict) else None)
                if pairs is None:
                    raise core_error("P2322", Where(frag, keyword), function="**",
                                     problem=f"expected a dict or record, not {type_name(value)}")
                for key, item in pairs:
                    if not isinstance(key, str):
                        raise core_error("P2322", Where(frag, keyword), function="**",
                                         problem="keyword names must be strings")
                    if key in kwargs:
                        raise core_error("P2321", Where(frag, keyword), function=function_name,
                                         problem=f"got multiple values for '{key}'")
                    kwargs[key] = item
            else:
                if keyword.arg in kwargs:
                    raise core_error("P2321", Where(frag, keyword), function=function_name,
                                     problem=f"got multiple values for '{keyword.arg}'")
                kwargs[keyword.arg] = value
        return args, kwargs

    def call(self, function: Any, args: list[Any], kwargs: dict[str, Any], span: Span) -> Any:
        """Call a Primula function value.

        Args:
            function: :class:`Function`, :class:`Builtin` or :class:`BoundMethod`.
            args: positional arguments.
            kwargs: keyword arguments.
            span: position of the call (errors, stack frame).
        """
        if isinstance(function, Builtin):
            return function.impl(self, args, kwargs, span)
        if isinstance(function, BoundMethod):
            return function.impl(self, function.receiver, args, kwargs, span)
        if not isinstance(function, Function):
            raise core_error("P2316", span, type=type_name(function), operation="()")
        self.meter.enter(span)
        try:
            env = Env(function.closure if isinstance(function.closure, GlobalScope) else function.closure.globals,
                      None if isinstance(function.closure, GlobalScope) else function.closure,
                      function.local_names)
            self._bind(function, args, kwargs, env, span)
            try:
                self.exec_block(function.node.body, env, function.fragment)
            except _Return as result:
                return result.value
            return None
        except CoreError as exc:
            if not isinstance(exc, LimitError) or len(exc.diagnostic.stack) < 20:
                exc.add_frame("call", span, function.name)
            raise
        except RecursionError:
            # Safety net: Python's stack ended before the language limit.
            raise LimitError(error("P2402", resolve(span), limit=self.meter.limits.recursion)) from None
        finally:
            self.meter.leave()

    def _bind(self, function: Function, args: list[Any], kwargs: dict[str, Any], env: Env,
              span: Span) -> None:
        """Bind call arguments to parameters (Python rules)."""
        params = function.node.args
        positional = [*params.posonlyargs, *params.args]
        names = [arg.arg for arg in positional]
        name = function.name
        if len(args) > len(names) and params.vararg is None:
            raise core_error("P2321", span, function=name,
                             problem=f"takes {len(names)} positional arguments but {len(args)} were given")
        for param, value in zip(names, args):
            env.assign(param, value)
        if params.vararg is not None:
            env.assign(params.vararg.arg, tuple(args[len(names):]))
        extra = PDict()
        kwonly = [arg.arg for arg in params.kwonlyargs]
        posonly = {arg.arg for arg in params.posonlyargs}
        for key, value in kwargs.items():
            if key in names and key not in posonly or key in kwonly:
                if key in env.vars:
                    raise core_error("P2321", span, function=name, problem=f"got multiple values for '{key}'")
                env.assign(key, value)
            elif params.kwarg is not None:
                extra[key] = value
            else:
                raise core_error("P2321", span, function=name, problem=f"got an unexpected keyword argument '{key}'")
        defaults = function.defaults
        first_default = len(names) - len(defaults)
        for index, param in enumerate(names):
            if param not in env.vars:
                if index >= first_default:
                    env.assign(param, defaults[index - first_default])
                else:
                    raise core_error("P2321", span, function=name, problem=f"missing argument '{param}'")
        for param, default in zip(kwonly, function.kw_defaults):
            if param not in env.vars:
                if default is _NO_DEFAULT:
                    raise core_error("P2321", span, function=name, problem=f"missing argument '{param}'")
                env.assign(param, default)
        if params.kwarg is not None:
            env.assign(params.kwarg.arg, extra)

    def make_function(self, node: ast.FunctionDef, closure: Env | GlobalScope, frag: PyFragment) -> Function:
        """Create a function value; defaults are evaluated now and frozen (decision 46)."""
        env = closure if isinstance(closure, Env) else Env(closure)
        defaults = [freeze(self.eval(value, env, frag)) for value in node.args.defaults]
        kw_defaults = [_NO_DEFAULT if value is None else freeze(self.eval(value, env, frag))
                       for value in node.args.kw_defaults]
        return Function(node.name, node, frag, closure, defaults, kw_defaults,
                        bound_names(node.body, include_params=node.args))

    # ------------------------------------------------------------------
    # Statements
    # ------------------------------------------------------------------

    def _s_expr(self, node: ast.Expr, env: Env, frag: PyFragment) -> None:
        self.eval(node.value, env, frag)

    def _s_assign(self, node: ast.Assign, env: Env, frag: PyFragment) -> None:
        value = self.eval(node.value, env, frag)
        for target in node.targets:
            self.assign(target, value, env, frag)

    def assign(self, target: ast.expr, value: Any, env: Env, frag: PyFragment) -> None:
        """Assign to a target: name, unpacking, item (``x[k] = v``)."""
        if isinstance(target, ast.Name):
            env.assign(target.id, value)
        elif isinstance(target, (ast.Tuple, ast.List)):
            self._unpack(target, value, env, frag)
        elif isinstance(target, ast.Subscript):
            container = self.eval(target.value, env, frag)
            span = Where(frag, target)
            if isinstance(target.slice, ast.Slice):
                raise core_error("P2322", span, function="[:]=", problem="slice assignment is not supported")
            key = self.eval(target.slice, env, frag)
            self.set_item(container, key, value, span)
        else:
            raise core_error("P2324", Where(frag, target))

    def set_item(self, container: Any, key: Any, value: Any, span: Span) -> None:
        """``container[key] = value`` with frozen and iteration checks."""
        if isinstance(container, PList):
            self.check_mutable(container, span)
            if not isinstance(key, int) or isinstance(key, bool):
                raise core_error("P2322", span, function="[]=", problem=f"index must be int, not {type_name(key)}")
            try:
                container[key] = value
            except IndexError:
                raise core_error("P2311", span, index=key, size=len(container)) from None
        elif isinstance(container, PDict):
            self.check_mutable(container, span)
            if not is_valid_key(key):
                raise core_error("P2317", span, type=type_name(key))
            container[key] = value
            self.meter.check_collection(len(container), span)
        else:
            raise core_error("P2316", span, type=type_name(container), operation="[]=")

    def check_mutable(self, value: PList | PDict, span: Span) -> None:
        """P2318 for a frozen value, P2319 during iteration."""
        if value.frozen:
            raise CoreError(error("P2318", resolve(span), type=type_name(value)).hint("help.frozen"))
        if value.iterating:
            raise core_error("P2319", span, type=type_name(value))

    def _unpack(self, target: ast.Tuple | ast.List, value: Any, env: Env, frag: PyFragment) -> None:
        span = Where(frag, target)
        items = self.materialize(value, span)
        starred = [i for i, element in enumerate(target.elts) if isinstance(element, ast.Starred)]
        if not starred:
            if len(items) != len(target.elts):
                raise core_error("P2320", span, expected=len(target.elts), got=len(items))
            for element, item in zip(target.elts, items):
                self.assign(element, item, env, frag)
            return
        star = starred[0]
        after = len(target.elts) - star - 1
        if len(items) < star + after:
            raise core_error("P2320", span, expected=f"{star + after}+", got=len(items))
        for element, item in zip(target.elts[:star], items[:star]):
            self.assign(element, item, env, frag)
        self.assign(target.elts[star].value, PList(items[star:len(items) - after]), env, frag)  # type: ignore[attr-defined]
        for element, item in zip(target.elts[star + 1:], items[len(items) - after:]):
            self.assign(element, item, env, frag)

    def _s_augassign(self, node: ast.AugAssign, env: Env, frag: PyFragment) -> None:
        op = _BINOPS[type(node.op)]
        target = node.target
        span = Where(frag, node)
        if isinstance(target, ast.Name):
            current = env.lookup(target.id, Where(frag, target))
            value = self.eval(node.value, env, frag)
            if op == "+" and isinstance(current, PList):
                # In place, as in Python and Starlark: aliases see the change.
                self.check_mutable(current, span)
                items = self.materialize(value, span)
                self.meter.check_collection(len(current) + len(items), span)
                current.extend(items)
                env.assign(target.id, current)
                return
            env.assign(target.id, self.binary(op, current, value, span))
        elif isinstance(target, ast.Subscript) and not isinstance(target.slice, ast.Slice):
            container = self.eval(target.value, env, frag)
            key = self.eval(target.slice, env, frag)
            current = self.index(container, key, span)
            value = self.eval(node.value, env, frag)
            self.set_item(container, key, self.binary(op, current, value, span), span)
        else:
            raise core_error("P2324", span)

    def _s_if(self, node: ast.If, env: Env, frag: PyFragment) -> None:
        branch = node.body if self.truthy(self.eval(node.test, env, frag)) else node.orelse
        self.exec_block(branch, env, frag)

    def _s_for(self, node: ast.For, env: Env, frag: PyFragment) -> None:
        iterable = self.eval(node.iter, env, frag)
        span = Where(frag, node.iter)
        for item in self.iterate(iterable, span):
            self.meter.step(span)
            self.assign(node.target, item, env, frag)
            try:
                self.exec_block(node.body, env, frag)
            except _Break:
                break
            except _Continue:
                continue

    def _s_while(self, node: ast.While, env: Env, frag: PyFragment) -> None:
        while self.truthy(self.eval(node.test, env, frag)):
            try:
                self.exec_block(node.body, env, frag)
            except _Break:
                break
            except _Continue:
                continue

    def _s_pass(self, node: ast.Pass, env: Env, frag: PyFragment) -> None:
        return None

    def _s_break(self, node: ast.Break, env: Env, frag: PyFragment) -> None:
        raise _Break()

    def _s_continue(self, node: ast.Continue, env: Env, frag: PyFragment) -> None:
        raise _Continue()

    def _s_return(self, node: ast.Return, env: Env, frag: PyFragment) -> None:
        raise _Return(None if node.value is None else self.eval(node.value, env, frag))

    def _s_def(self, node: ast.FunctionDef, env: Env, frag: PyFragment) -> None:
        if node.decorator_list:
            # @export in code that runs in place (a |code block in the body of
            # |for or |def): only a fragment's top level exports (decision 135).
            raise core_error("P2610", frag.span_of(node.decorator_list[0]))
        env.assign(node.name, self.make_function(node, env, frag))


class _Missing:
    pass


_MISSING = _Missing()
_NO_DEFAULT = _Missing()


def _length_factor(value: Any, span: Span) -> Decimal | int:
    """A number as a ``decimal`` factor of a length (12.3).

    A ``float`` is converted by its shortest decimal representation, as
    ``dec(x)``; ``nan`` and ``inf`` are errors.
    """
    if isinstance(value, float):
        try:
            return numbers.to_decimal(value)
        except numbers.NumberError as exc:
            raise core_error(exc.code, span, **exc.args_) from None
    return value


def _callable_name(function: Any) -> str:
    return getattr(function, "name", type_name(function))


def _number_args(exc: numbers.NumberError, op: str, left: Any, right: Any) -> dict[str, object]:
    """Message arguments of a number error."""
    args = dict(exc.args_)
    args.setdefault("op", op)
    args.setdefault("left", type_name(left))
    args.setdefault("right", type_name(right))
    return args

