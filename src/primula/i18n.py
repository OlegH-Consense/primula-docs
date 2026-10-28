"""Message catalogues and language selection for diagnostics and the CLI.

Diagnostic texts are looked up by key (a diagnostic code such as ``P1102``
or a dotted key such as ``cli.help.check``) in per-language catalogues:
English is the primary catalogue, Ukrainian and Russian are translations
(specification section 14.2, decision 27).  A missing translation falls
back to English, so a new message only needs the English text to work;
``tests/test_i18n.py`` checks that all catalogues are complete.

Catalogue values are ``str.format`` templates.  Plural-dependent texts are
tuples of forms selected by :func:`plural_index` (English: 2 forms;
Ukrainian and Russian: 3 forms — one, few, many).

The severity labels of the text format (``error``, ``warning``, ``note``,
``help``) are not translated: editors and build tools parse them.
"""

from __future__ import annotations

import os
from collections.abc import Mapping

from primula.messages import en, ru, uk

#: Supported interface languages; the first one is the fallback.
SUPPORTED_LANGUAGES: tuple[str, ...] = ("en", "uk", "ru")

_CATALOGUES: dict[str, Mapping[str, str | tuple[str, ...]]] = {
    "en": en.MESSAGES,
    "uk": uk.MESSAGES,
    "ru": ru.MESSAGES,
}


def detect_language(explicit: str | None = None,
                    environ: Mapping[str, str] | None = None) -> str:
    """Choose the interface language.

    Order: the explicit value (``--lang``), the ``PRIMULA_LANG`` variable,
    then the gettext variables ``LANGUAGE`` (a colon-separated list),
    ``LC_ALL``, ``LC_MESSAGES``, ``LANG``.  A locale such as
    ``uk_UA.UTF-8`` gives ``uk``; ``C``, ``POSIX`` and unsupported
    languages give English.

    Args:
        explicit: language requested on the command line, or ``None``.
        environ: environment mapping; defaults to :data:`os.environ`.

    Returns:
        One of :data:`SUPPORTED_LANGUAGES`.
    """
    if explicit:
        code = _language_of(explicit)
        return code if code in SUPPORTED_LANGUAGES else SUPPORTED_LANGUAGES[0]
    env = os.environ if environ is None else environ
    for variable in ("PRIMULA_LANG", "LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG"):
        value = env.get(variable, "")
        if not value:
            continue
        # LANGUAGE may list several languages in order of preference.
        for item in value.split(":"):
            code = _language_of(item)
            if code in SUPPORTED_LANGUAGES:
                return code
        if variable != "LANGUAGE":
            # The first set locale variable decides, as in gettext.
            break
    return SUPPORTED_LANGUAGES[0]


def _language_of(locale_name: str) -> str:
    """Extract the language part of a locale name (``uk_UA.UTF-8`` -> ``uk``)."""
    return locale_name.strip().split(".")[0].split("@")[0].replace("-", "_").split("_")[0].lower()


def plural_index(language: str, n: int) -> int:
    """Select the plural form for a number.

    Uses the CLDR rules for integers: English has ``one`` (n == 1) and
    ``other``; Ukrainian and Russian have ``one`` (1, 21, 31...), ``few``
    (2-4, 22-24...) and ``many`` (0, 5-20, 25-30...).

    Args:
        language: catalogue language.
        n: the number.

    Returns:
        Index of the form in a catalogue tuple.
    """
    n = abs(n)
    if language in ("uk", "ru"):
        if n % 10 == 1 and n % 100 != 11:
            return 0
        if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14:
            return 1
        return 2
    return 0 if n == 1 else 1


class Key(str):
    """A message argument that is itself a catalogue key.

    Diagnostics keep arguments, not texts.  When an argument must be
    translated too (for example a type name ``type.mapping`` inside
    "must be a mapping"), it is passed as ``Key("type.mapping")`` and
    :meth:`Catalog.text` replaces it with the translated text.
    """


class Catalog:
    """Message lookup for one language with English fallback.

    Args:
        language: one of :data:`SUPPORTED_LANGUAGES`.
    """

    def __init__(self, language: str = "en") -> None:
        if language not in _CATALOGUES:
            language = SUPPORTED_LANGUAGES[0]
        self.language = language
        self._messages = _CATALOGUES[language]
        self._fallback = _CATALOGUES[SUPPORTED_LANGUAGES[0]]

    def text(self, key: str, /, **args: object) -> str:
        """Return the formatted message for ``key``.

        Args:
            key: catalogue key (positional-only, so that a template may
                itself use an argument named ``key``).
            **args: template arguments.

        Returns:
            The formatted text.  An unknown key or a template error never
            raises: the key and the arguments are returned instead, so a
            broken message cannot hide the diagnostic itself.
        """
        args = {name: self.text(value) if isinstance(value, Key) else value
                for name, value in args.items()}
        problem = args.get("problem")
        if isinstance(problem, str) and self.language != "en":
            from primula.messages.problems import CODES, translate

            if key in CODES:
                # English problem texts of core messages (stage 13.9d).
                args["problem"] = translate(self.language, problem)
        template = self._messages.get(key, self._fallback.get(key))
        if template is None:
            return _raw(key, args)
        if isinstance(template, tuple):
            template = template[-1]
        try:
            return template.format(**args)
        except (KeyError, IndexError, ValueError):
            return _raw(key, args)

    def plural(self, key: str, n: int, /, **args: object) -> str:
        """Return the plural form of ``key`` for ``n``; ``{n}`` is available.

        Args:
            key: catalogue key whose value is a tuple of forms.
            n: the number that selects the form.
            **args: other template arguments.
        """
        forms = self._messages.get(key)
        language = self.language
        if not isinstance(forms, tuple):
            forms = self._fallback.get(key)
            language = SUPPORTED_LANGUAGES[0]
        if not isinstance(forms, tuple):
            return self.text(key, n=n, **args)
        index = min(plural_index(language, n), len(forms) - 1)
        try:
            return forms[index].format(n=n, **args)
        except (KeyError, IndexError, ValueError):
            return _raw(key, {"n": n, **args})


def _raw(key: str, args: Mapping[str, object]) -> str:
    """Fallback rendering of a message that cannot be formatted."""
    if not args:
        return key
    rendered = ", ".join(f"{name}={value!r}" for name, value in args.items())
    return f"{key} ({rendered})"


def catalogue(language: str) -> Mapping[str, str | tuple[str, ...]]:
    """Return the raw catalogue of a language (for tests and tools)."""
    return _CATALOGUES[language]
