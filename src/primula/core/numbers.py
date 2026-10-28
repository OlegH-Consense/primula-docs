"""Numbers: arithmetic, comparison and rounding (specification 12.4; decisions 41, 108).

There is one exact number type, ``decimal``; an integer is a ``decimal``
with scale 0.  Internally an integer value is kept as a Python ``int``
(fast, and ``5 == 5.00`` with equal hashes holds in Python), every other
``decimal`` as :class:`decimal.Decimal`.  ``type()`` reports both as
``"decimal"``.

Rules:

* ``decimal`` op ``decimal`` -> ``decimal``; ``/`` is a ``decimal`` division
  (``7 / 2`` -> 3.5, 28 significant digits); ``decimal ** negative
  integer`` gives a fraction (``2 ** -1`` -> 0.5);
* the result of any exact operation has at most 64 significant digits;
  more is the error "number overflow" (P2309); for ``**`` the size is
  estimated before computing;
* ``decimal`` with ``float`` -> ``float``: the ``decimal`` is converted
  automatically, also in comparisons (``5 == 5.0``);
* ``//`` and ``%`` round down, the remainder has the sign of the divisor;
* ``bool`` takes no part in arithmetic;
* rounding is half away from zero for ``decimal`` and ``float`` (for
  ``float`` by its shortest decimal representation): ``round(2.675, 2)`` ->
  2.68, ``round(-2.5)`` -> -3.

Functions raise :class:`NumberError` with a diagnostic code; the
interpreter adds the position.
"""

from __future__ import annotations

import decimal
import math
import re
from decimal import Decimal
from typing import Any

from primula.core.values import (
    DECIMAL_CONTEXT, EXACT_CONTEXT, MAX_DIGITS, digits_ok, is_number, type_name,
)

_CTX = DECIMAL_CONTEXT
#: Rounding/quantizing up to 64 digits without the ``Inexact`` trap.
_ROUND_CTX = decimal.Context(prec=MAX_DIGITS, rounding=decimal.ROUND_HALF_UP, Emax=999_999,
                             Emin=-999_999, traps=[decimal.InvalidOperation, decimal.Overflow])

#: A decimal integer as written in Python (underscores between digits).
_INT_RE = re.compile(r"[+-]?\d+(?:_\d+)*")


class NumberError(Exception):
    """An arithmetic error; ``code`` and ``args`` form the diagnostic."""

    def __init__(self, code: str, **args: object) -> None:
        super().__init__(code)
        self.code = code
        self.args_ = args


def _kind(value: Any) -> str:
    """``int`` (integer decimal), ``dec`` or ``float`` of a number (``bool`` is rejected)."""
    if isinstance(value, bool):
        raise NumberError("P2304")
    if isinstance(value, int):
        return "int"
    if isinstance(value, Decimal):
        return "dec"
    return "float"


def _common(left: Any, right: Any, op: str) -> str:
    """The result kind of a binary operation on two numbers (12.4 table)."""
    kinds = {_kind(left), _kind(right)}
    if "float" in kinds:
        return "float"
    if "dec" in kinds:
        return "dec"
    return "int"


def check_digits(value: Any) -> Any:
    """Return a ``decimal`` result or raise "number overflow" (P2309, 64 digits)."""
    if not digits_ok(value):
        raise NumberError("P2309", limit=MAX_DIGITS)
    return value


def as_integer(value: Any) -> int | None:
    """An integer value of a number (``2``, ``2.0``, ``Decimal("2.00")``), else ``None``.

    Indexes, slices, ``range`` and repetition accept such numbers (12.4).
    """
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, Decimal):
        return int(value) if value.is_finite() and value == value.to_integral_value() else None
    if isinstance(value, float):
        return int(value) if value.is_integer() else None
    return None


def _dec(value: Any) -> Decimal:
    return value if isinstance(value, Decimal) else Decimal(value)


def _floor_div_dec(left: Decimal, right: Decimal) -> Decimal:
    """Floor division of decimals (Decimal's own ``//`` truncates)."""
    quotient = _CTX.divide(left, right)
    return quotient.to_integral_value(rounding=decimal.ROUND_FLOOR, context=_CTX)


def arith(op: str, left: Any, right: Any) -> Any:
    """Apply ``+ - * / // % **`` to two numbers.

    Args:
        op: the operator symbol.
        left: left number.
        right: right number.

    Returns:
        The result by the rules of the module.

    Raises:
        NumberError: number overflow (P2309), bool (P2304), division by
            zero (P2303), invalid operation (P2308).
    """
    kind = _common(left, right, op)
    try:
        if kind == "int":
            return check_digits(_arith_int(op, left, right))
        if kind == "dec":
            return check_digits(_arith_dec(op, _dec(left), _dec(right)))
        return _arith_float(op, float(left), float(right))
    except ZeroDivisionError:
        raise NumberError("P2303") from None
    except decimal.DivisionByZero:
        raise NumberError("P2303") from None
    except decimal.Inexact:
        raise NumberError("P2309", limit=MAX_DIGITS) from None
    except (decimal.InvalidOperation, decimal.Overflow, OverflowError, ValueError) as exc:
        raise NumberError("P2308", detail=type(exc).__name__) from None


def _arith_int(op: str, left: int, right: int) -> Any:
    if op == "+":
        return left + right
    if op == "-":
        return left - right
    if op == "*":
        return left * right
    if op == "/":
        if right == 0:
            raise ZeroDivisionError
        return _CTX.divide(Decimal(left), Decimal(right))
    if op == "//":
        return left // right
    if op == "%":
        return left % right
    if op == "**":
        if right < 0:
            if left == 0:
                raise ZeroDivisionError
            return _CTX.power(Decimal(left), right)
        # Estimate the digits before computing (12.4).
        if abs(left) > 1 and right * math.log10(abs(left)) > MAX_DIGITS:
            raise NumberError("P2309", limit=MAX_DIGITS)
        return left ** right
    raise NumberError("P2301", op=op, left="decimal", right="decimal")  # pragma: no cover


def _arith_dec(op: str, left: Decimal, right: Decimal) -> Decimal:
    if op == "+":
        return EXACT_CONTEXT.add(left, right)
    if op == "-":
        return EXACT_CONTEXT.subtract(left, right)
    if op == "*":
        return EXACT_CONTEXT.multiply(left, right)
    if op == "/":
        return _CTX.divide(left, right)
    if op == "//":
        return _floor_div_dec(left, right)
    if op == "%":
        if right == 0:
            raise ZeroDivisionError
        return _CTX.subtract(left, _CTX.multiply(right, _floor_div_dec(left, right)))
    if op == "**":
        exponent = as_integer(right)
        if exponent is not None and exponent >= 0:
            # Integer power: exact up to 64 digits; estimate first (12.4).
            if abs(left) not in (0, 1) and exponent * max(abs(left.adjusted()) + 1, 1) > 4 * MAX_DIGITS:
                raise NumberError("P2309", limit=MAX_DIGITS)
            return EXACT_CONTEXT.power(left, exponent)
        return _CTX.power(left, right)
    raise NumberError("P2301", op=op, left="decimal", right="decimal")  # pragma: no cover


def _arith_float(op: str, left: float, right: float) -> float:
    if op == "+":
        result = left + right
    elif op == "-":
        result = left - right
    elif op == "*":
        result = left * right
    elif op == "/":
        result = left / right
    elif op == "//":
        result = left // right
    elif op == "%":
        result = left % right
    elif op == "**":
        result = left ** right
        if isinstance(result, complex):
            raise ValueError("complex result")
    else:  # pragma: no cover
        raise NumberError("P2301", op=op, left="float", right="float")
    return result


def negate(value: Any) -> Any:
    """Unary minus of a number."""
    kind = _kind(value)
    return _CTX.minus(value) if kind == "dec" else -value


def compare(op: str, left: Any, right: Any) -> bool:
    """Compare two numbers (``== != < <= > >=``).

    A ``decimal`` compared with a ``float`` is converted to ``float`` first
    (12.3: ``5 == 5.0``, ``0.1 == 0.1e0``).
    """
    if _common(left, right, op) == "float":
        left, right = float(left), float(right)
    if op == "==":
        return left == right
    if op == "!=":
        return left != right
    if op == "<":
        return left < right
    if op == "<=":
        return left <= right
    if op == ">":
        return left > right
    return left >= right


def round_number(value: Any, digits: int | None) -> Any:
    """``round(x, n)``: half away from zero for all numbers (decision 41).

    Args:
        value: ``decimal`` or ``float``.
        digits: digits after the point; ``None`` returns a ``decimal``
            with scale 0.

    Returns:
        A ``decimal`` with scale 0 without ``digits``; otherwise a
        ``decimal`` with ``digits`` places, or a ``float`` for a ``float``.
    """
    kind = _kind(value)
    if kind == "float":
        if math.isnan(value) or math.isinf(value):
            raise NumberError("P2308", detail="non-finite float")
        exact = Decimal(repr(value))
    else:
        exact = Decimal(value)
    if digits is None:
        return check_digits(int(exact.to_integral_value(rounding=decimal.ROUND_HALF_UP, context=_ROUND_CTX)))
    quantum = Decimal(1).scaleb(-digits)
    try:
        rounded = exact.quantize(quantum, rounding=decimal.ROUND_HALF_UP, context=_ROUND_CTX)
    except decimal.InvalidOperation:
        raise NumberError("P2309", limit=MAX_DIGITS) from None
    if kind == "float":
        return float(rounded)
    if digits <= 0:
        return check_digits(int(rounded))  # round(1234, -2) -> 1200, scale 0
    return check_digits(rounded)


def to_int(value: Any) -> int:
    """``int(x)``: truncates the fraction (a ``decimal`` with scale 0, 12.4).

    Accepts numbers, ``bool`` and a decimal integer string.
    """
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, Decimal):
        return check_digits(int(value))
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            raise NumberError("P2307", value=repr(value), type="decimal")
        return check_digits(int(value))
    if isinstance(value, str):
        text = value.strip().replace("_", "")
        if _INT_RE.fullmatch(value.strip()) is None:
            raise NumberError("P2307", value=value, type="decimal")
        if len(text.lstrip("+-")) > MAX_DIGITS + 1:
            raise NumberError("P2309", limit=MAX_DIGITS)
        return check_digits(int(text))
    raise NumberError("P2307", value=type_name(value), type="decimal")


def to_decimal(value: Any) -> Any:
    """``dec(x)``: from ``float`` (shortest repr: ``dec(0.1)`` -> 0.1), numeric string.

    A ``decimal`` is returned unchanged (an integer stays an integer).
    """
    if isinstance(value, bool):
        raise NumberError("P2307", value=repr(value), type="decimal")
    if isinstance(value, (Decimal, int)):
        return value
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            raise NumberError("P2307", value=repr(value), type="decimal")
        return check_digits(Decimal(repr(value)))
    if isinstance(value, str):
        try:
            result = Decimal(value.strip().replace("_", ""))
        except decimal.InvalidOperation:
            raise NumberError("P2307", value=value, type="decimal") from None
        if not result.is_finite():
            raise NumberError("P2307", value=value, type="decimal")
        return check_digits(result)
    raise NumberError("P2307", value=type_name(value), type="decimal")


def to_float(value: Any) -> float:
    """``float(x)``: from ``decimal``, numeric string (``datetime``: in builtins)."""
    if isinstance(value, bool):
        raise NumberError("P2307", value=repr(value), type="float")
    if is_number(value):
        try:
            return float(value)
        except OverflowError:
            raise NumberError("P2308", detail="overflow") from None
    if isinstance(value, str):
        try:
            return float(value.strip())
        except ValueError:
            raise NumberError("P2307", value=value, type="float") from None
    raise NumberError("P2307", value=type_name(value), type="float")
