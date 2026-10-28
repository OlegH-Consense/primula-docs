"""Scopes: local environments and the lazy global scope (10.4, 12.7, decision 40).

Name lookup goes from the innermost environment outwards:

1. the local environment (function call, comprehension, top-level action);
2. enclosing function environments (closures, read-only);
3. the global scope (:class:`GlobalScope`): lazy, immutable definitions;
4. built-in names.

Python scoping rules apply inside functions and actions: a name that is
bound anywhere in the body is local to the whole body, and reading it
before it is bound is an error (P2202) instead of silently reading the
global name.

Global definitions (decision 40) are registered without being evaluated.
The first access evaluates the definition, freezes the value and keeps it;
a definition that is reached again while it is being evaluated is a cycle
(P2204, with the chain of names); a second definition of a name is an
error with the positions of both (P2203).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from primula.core.errors import CoreError, core_error, resolve
from primula.core.values import freeze
from primula.diagnostics import error
from primula.source import Span

#: States of a global definition.
PENDING, EVALUATING, DONE, FAILED = "pending", "evaluating", "done", "failed"


@dataclass(eq=False)
class Definition:
    """A lazily evaluated global definition.

    Attributes:
        name: the defined name.
        span: position of the definition (for P2203 and cycles).
        compute: ``compute() -> value``; for unpacking, several names share
            one :class:`Shared` computation.
        state: ``pending``, ``evaluating``, ``done`` or ``failed``.
        value: the frozen value once ``done``.
        error: the error of a failed evaluation (reported once).
    """

    name: str
    span: Span | None
    compute: Callable[[], Any]
    state: str = PENDING
    value: Any = None
    error: CoreError | None = None


@dataclass(eq=False)
class Shared:
    """One right-hand side shared by the names of an unpacking definition."""

    compute: Callable[[], Any]
    done: bool = False
    value: Any = None

    def get(self) -> Any:
        if not self.done:
            self.value = self.compute()
            self.done = True
        return self.value


class GlobalScope:
    """Global names of a document, module, styles module or project.

    Args:
        parent: an outer global scope whose names are visible read-only
            (project parameters for a document; stage 13.3).
        builtins: built-in names.
    """

    def __init__(self, parent: "GlobalScope | None" = None,
                 builtins: dict[str, Any] | None = None) -> None:
        self.parent = parent
        self.builtins = builtins if builtins is not None else (parent.builtins if parent else {})
        self.definitions: dict[str, Definition] = {}
        self._evaluating: list[Definition] = []

    # ------------------------------------------------------------------

    def define(self, name: str, compute: Callable[[], Any], span: Span | None) -> Definition:
        """Register a lazy definition; P2203 if the name is already defined."""
        existing = self.definitions.get(name)
        if existing is not None:
            diagnostic = error("P2203", resolve(span), name=name)
            if existing.span is not None:
                diagnostic.note("note.first_definition", existing.span)
            raise CoreError(diagnostic)
        definition = Definition(name, span, compute)
        self.definitions[name] = definition
        return definition

    def define_value(self, name: str, value: Any, span: Span | None) -> Definition:
        """Register an already computed value (header parameter, export)."""
        definition = self.define(name, lambda: value, span)
        definition.state, definition.value = DONE, freeze(value)
        return definition

    def has(self, name: str) -> bool:
        """The name is defined here or in a parent scope."""
        return name in self.definitions or (self.parent is not None and self.parent.has(name))

    def lookup(self, name: str, span: Span | None) -> Any:
        """Return the value of a global name, evaluating it on first access.

        Raises:
            CoreError: undefined name (P2201), cycle (P2204), or the error
                of the definition's evaluation.
        """
        definition = self.definitions.get(name)
        if definition is None:
            if self.parent is not None and self.parent.has(name):
                return self.parent.lookup(name, span)
            if name in self.builtins:
                return self.builtins[name]
            raise core_error("P2201", span, name=name)
        if definition.state == DONE:
            return definition.value
        if definition.state == FAILED:
            assert definition.error is not None
            raise definition.error
        if definition.state == EVALUATING:
            chain = [d.name for d in self._evaluating[self._evaluating.index(definition):]] + [name]
            diagnostic = error("P2204", resolve(span), chain=" -> ".join(chain))
            if definition.span is not None:
                diagnostic.note("note.definition_here", definition.span, name=name)
            raise CoreError(diagnostic)
        definition.state = EVALUATING
        self._evaluating.append(definition)
        try:
            value = definition.compute()
        except CoreError as exc:
            definition.state, definition.error = FAILED, exc
            raise
        finally:
            self._evaluating.pop()
        definition.state, definition.value = DONE, freeze(value)
        return definition.value


class Env:
    """A local environment (function call, comprehension, action).

    Args:
        globals_: the global scope.
        parent: the enclosing environment (closure) or ``None``.
        local_names: names bound in the body; reading one of them before
            it is bound is P2202.  ``None`` means "all bound names are
            local" without the before-assignment check (comprehensions).
    """

    __slots__ = ("globals", "parent", "vars", "local_names")

    def __init__(self, globals_: GlobalScope, parent: "Env | None" = None,
                 local_names: frozenset[str] | None = None) -> None:
        self.globals = globals_
        self.parent = parent
        self.vars: dict[str, Any] = {}
        self.local_names = local_names

    def lookup(self, name: str, span: Span | None) -> Any:
        """Look a name up through the environment chain and the globals."""
        env: Env | None = self
        while env is not None:
            if name in env.vars:
                return env.vars[name]
            if env.local_names is not None and name in env.local_names:
                raise core_error("P2202", span, name=name)
            env = env.parent
        return self.globals.lookup(name, span)

    def assign(self, name: str, value: Any) -> None:
        """Bind a local name."""
        self.vars[name] = value
