"""Message catalogues: ``en`` (primary), ``uk``, ``ru``.

Each module defines ``MESSAGES``: a mapping from a key to a ``str.format``
template or to a tuple of plural forms.  Keys:

* ``Pnxxx`` — diagnostic messages; the list of codes with severities and
  specification references is ``docs/dev/diagnostics.md``;
* ``note.*``, ``help.*`` — notes and hints attached to diagnostics;
* ``frame.*`` — call stack entries (include, import, macro, call);
* ``type.*`` — names of value types used inside messages;
* ``count.*`` — plural forms used in summaries;
* ``cli.*`` — command line interface texts.

See :mod:`primula.i18n` for lookup and fallback rules.
"""
