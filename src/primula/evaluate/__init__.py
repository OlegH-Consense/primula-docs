"""Document evaluation (stage 13.3, specification 4.2, 9.2, 10, 12.7).

* :mod:`~primula.evaluate.loader` — project root, path rules, loading and
  flat parsing of fragments and modules (10.1, decision 50);
* :mod:`~primula.evaluate.data` — ``load_yaml``, ``load_json``,
  ``load_csv`` (10.5, decisions 25, 51);
* :mod:`~primula.evaluate.model` — evaluated arguments, macros, content;
* :mod:`~primula.evaluate.evaluator` — the three phases of decision 54:
  definitions, actions, markup; fragments, modules, macros, ``when=``.
"""
