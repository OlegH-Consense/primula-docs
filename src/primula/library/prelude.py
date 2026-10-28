"""The prelude of the standard library: built-in names of the core (library 1).

Stages 13.9 and 13.9c: numbers and numbers in words, money and VAT,
dates and the calendar, values with units, text functions, data
functions; ``std/math`` is a built-in module (:func:`std_module`).
Stage 13.9d: ``typography(nbsp_short=True)`` applied to the whole ODT.

Each function is ``impl(lib, args, kwargs, span)``; this module binds it to
a :class:`~primula.library.context.Library` and turns arithmetic errors of
the core into diagnostics.
"""

from __future__ import annotations

from typing import Any, Callable

from primula.core.errors import core_error
from primula.core.numbers import NumberError
from primula.core.values import Builtin
from primula.library import data, dates, money, numbers, qr, std_math, text, units
from primula.library.context import Library

FUNCTIONS: dict[str, Callable[..., Any]] = {
    **numbers.FUNCTIONS, **money.FUNCTIONS, **dates.FUNCTIONS, **units.FUNCTIONS, **text.FUNCTIONS,
    **data.FUNCTIONS, **qr.FUNCTIONS,
}


def _binder(lib: Library) -> Callable[[str, Callable[..., Any]], Builtin]:
    """Bind library functions to ``lib`` as core built-ins."""

    def bind(name: str, function: Callable[..., Any]) -> Builtin:
        def impl(interp: Any, args: list[Any], kwargs: dict[str, Any], span: Any) -> Any:
            lib.meter, lib.interp = interp.meter, interp
            try:
                return function(lib, list(args), dict(kwargs), span)
            except NumberError as exc:
                raise core_error(exc.code, span, **exc.args_) from None
        return Builtin(name, impl)

    return bind


def make_library_builtins(lib: Library) -> dict[str, Builtin]:
    """Built-in functions of the prelude bound to ``lib``."""
    bind = _binder(lib)
    return {name: bind(name, function) for name, function in FUNCTIONS.items()}


def std_module(lib: Library, name: str) -> dict[str, Any] | None:
    """Names of a built-in code module ``std/…`` (``std/math``), or ``None``."""
    if name == "std/math":
        return std_math.module_values(_binder(lib))
    return None
