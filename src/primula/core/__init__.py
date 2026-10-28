"""Computing core: interpreter of the Python subset (stage 13.2, specification 12).

* :mod:`~primula.core.check` — whitelist of AST nodes (12.2);
* :mod:`~primula.core.values` — value types (12.3-12.6, decisions 43-44);
* :mod:`~primula.core.numbers` — arithmetic and rounding (12.4, decision 41);
* :mod:`~primula.core.scope` — environments, lazy global scope (10.4, 12.7);
* :mod:`~primula.core.interp` — the evaluator;
* :mod:`~primula.core.builtins` — functions, methods, formatting (12.10, decision 45);
* :mod:`~primula.core.program` — definitions and actions of top-level code (decision 40);
* :mod:`~primula.core.limits` — limits and the step model (12.8, decision 42);
* :mod:`~primula.core.errors` — errors with call stacks (12.9).
"""
