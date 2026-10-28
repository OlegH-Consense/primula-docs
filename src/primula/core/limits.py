"""Limits of the computing core (specification 12.8, decision 113).

==============  ==============  ============================================
Limit (key)     Default         Meaning
==============  ==============  ============================================
``time``        20 s            one evaluation: an expression, a code block
                                or a chain of macro calls; the clock starts
                                anew for every evaluation
``recursion``   500             depth of function and macro calls,
                                including ``|include``
``size``        10 000 000      length of a string (characters) and number
                                of elements of a list, tuple, dictionary
==============  ==============  ============================================

* Sizes are checked *before* a value is created, from the sizes of the
  operands (``[0] * n``, ``"x" * n``, ``range(n)``, ``a + b``, ``join``).
* The time limit depends on the machine and is a safeguard, not part of the
  semantics.  The interpreter counts evaluated nodes ("ticks") only to look
  at the clock every :data:`TIME_CHECK_INTERVAL` ticks.
* The time of the whole build is limited by ``--timeout`` (:attr:`Meter.deadline`).
* Memory is limited at the process level (:func:`limit_memory`).
* The 64-digit ceiling of numbers is a rule of the number type
  (:mod:`primula.core.numbers`), not a configurable limit.
"""

from __future__ import annotations

import sys
import time
from dataclasses import dataclass, field

from primula.core.errors import LimitError, resolve
from primula.diagnostics import error
from primula.source import Span

#: Ticks (evaluated nodes and loop items) between checks of the clock.
TIME_CHECK_INTERVAL = 4096

#: Recommended memory limit of the translator process (12.8): 1 GiB.
MEMORY_LIMIT = 1 << 30


@dataclass
class Limits:
    """Configured limits (defaults of language version 1.1).

    A project may change them with the ``limits`` header key (10.6).
    """

    time: float = 20.0
    recursion: int = 500
    size: int = 10_000_000

    @classmethod
    def from_mapping(cls, values: dict[str, object] | None) -> "Limits":
        """Build limits from a ``limits`` mapping; unknown keys are ignored."""
        limits = cls()
        for key, value in (values or {}).items():
            if hasattr(limits, str(key)) and isinstance(value, (int, float)) and not isinstance(value, bool):
                setattr(limits, str(key), type(getattr(limits, str(key)))(value))
        return limits


@dataclass
class Meter:
    """Checks the limits of :class:`Limits` and records their use.

    Attributes:
        limits: the limits.
        steps: ticks counted since the last clock check point (internal;
            the interpreter increments it on its hot path).
        depth: current call depth.
        max_depth: deepest call depth reached (for the report).
        max_size: largest value size checked (for the report).
        max_time: longest single evaluation in seconds (for the report).
        deadline: ``time.monotonic()`` value at which the whole build
            stops (``--timeout``), or ``None``.
    """

    limits: Limits = field(default_factory=Limits)
    steps: int = 0
    depth: int = 0
    max_depth: int = 0
    max_size: int = 0
    max_time: float = 0.0
    deadline: float | None = None
    _started: float = field(default_factory=time.monotonic)
    _next_time_check: int = TIME_CHECK_INTERVAL

    def begin(self) -> None:
        """Start the clock of a new evaluation (12.8: the count starts anew).

        Called by document evaluation for each top-level expression, code
        block and macro call chain; nested evaluations do not restart it.
        """
        if self.depth == 0:
            self._record_time()
            self._started = time.monotonic()

    def _record_time(self) -> None:
        self.max_time = max(self.max_time, time.monotonic() - self._started)

    def step(self, span: Span | None, count: int = 1) -> None:
        """Count ``count`` ticks; look at the clock periodically (P2406, P0004)."""
        self.steps += count
        if self.steps >= self._next_time_check:
            self._next_time_check = self.steps + TIME_CHECK_INTERVAL
            now = time.monotonic()
            if now - self._started > self.limits.time:
                raise LimitError(error("P2406", resolve(span), limit=self.limits.time))
            if self.deadline is not None and now > self.deadline:
                raise LimitError(error("P0004", resolve(span)))

    def enter(self, span: Span | None) -> None:
        """Enter a call; raise P2402 when the recursion limit is exceeded."""
        self.depth += 1
        self.max_depth = max(self.max_depth, self.depth)
        if self.depth > self.limits.recursion:
            self.depth -= 1
            raise LimitError(error("P2402", resolve(span), limit=self.limits.recursion))

    def leave(self) -> None:
        """Leave a call."""
        self.depth -= 1

    def check_size(self, size: int, span: Span | None, *, string: bool = False) -> None:
        """Check the size of a value before it is created (P2404 string, P2403 other)."""
        if size > self.max_size:
            self.max_size = size
        if size > self.limits.size:
            code = "P2404" if string else "P2403"
            raise LimitError(error(code, resolve(span), size=size, limit=self.limits.size))

    def check_collection(self, size: int, span: Span | None) -> None:
        """Check the number of elements of a list, tuple or dictionary (P2403)."""
        self.check_size(size, span)

    def check_string(self, size: int, span: Span | None) -> None:
        """Check the length of a string (P2404)."""
        self.check_size(size, span, string=True)

    def usage(self) -> dict[str, object]:
        """Limit usage for the build report (12.8, 14.3)."""
        self._record_time()
        return {"max_depth": self.max_depth, "recursion_limit": self.limits.recursion,
                "max_size": self.max_size, "size_limit": self.limits.size,
                "max_time": round(self.max_time, 3), "time_limit": self.limits.time}


def limit_memory(limit: int = MEMORY_LIMIT) -> bool:
    """Limit the memory of the evaluation (12.8: about 1 GiB); Linux only.

    The language leaves the memory limit to the implementation.  Here the
    address space (``RLIMIT_AS``) may grow by ``limit`` over what the
    process already uses when the evaluation starts; ``RLIMIT_AS`` counts
    virtual memory, so the headroom is measured from the current virtual
    size (``/proc/self/statm``).  The limit is set only for the evaluation
    (:func:`restore_memory_limit` afterwards), so LibreOffice started for
    the PDF export is not affected.  Exhaustion raises ``MemoryError``,
    reported as P0005.

    Returns:
        ``True`` if the limit was set.
    """
    if not sys.platform.startswith("linux"):
        return False
    try:
        import os
        import resource
        soft, hard = resource.getrlimit(resource.RLIMIT_AS)
        global _SAVED_LIMIT
        _SAVED_LIMIT = (soft, hard)
        with open("/proc/self/statm", encoding="ascii") as statm:
            current = int(statm.read().split()[0]) * os.sysconf("SC_PAGE_SIZE")
        limit += current
        new = limit if hard == resource.RLIM_INFINITY else min(limit, hard)
        if soft == resource.RLIM_INFINITY or soft > new:
            resource.setrlimit(resource.RLIMIT_AS, (new, hard))
        return True
    except (ImportError, ValueError, OSError):
        return False


_SAVED_LIMIT: tuple[int, int] | None = None


def restore_memory_limit() -> None:
    """Restore the address-space limit saved by :func:`limit_memory`."""
    global _SAVED_LIMIT
    if _SAVED_LIMIT is None:
        return
    try:
        import resource
        resource.setrlimit(resource.RLIMIT_AS, _SAVED_LIMIT)
    except (ImportError, ValueError, OSError):
        pass
    _SAVED_LIMIT = None
