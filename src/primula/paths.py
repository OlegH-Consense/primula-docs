"""The project root boundary of paths (10.1, decisions 50, 106, 136).

A path is inside the project when it lies under the root *as written*:
``..`` is collapsed lexically, symbolic links are not followed.  A link the
author created inside the project (``lib -> ../shared``) therefore opens a
library kept elsewhere (decision 136); ``../`` in the text of a document still
cannot leave the root.  A path that is inside the root only after following
links (the root itself reached through a link, e.g. ``/home/u/dev`` ->
``/works/u/dev``) is inside too.

The files opened are the lexical paths checked here, so the check and the
opening agree even when a link is followed by ``..`` (``lib/../x`` is ``x``).
"""

from __future__ import annotations

import os
from pathlib import Path, PurePosixPath


def lexical(path: Path) -> Path:
    """Absolute normalized path without following symbolic links.

    Args:
        path: a path, absolute or relative to the current directory.

    Returns:
        ``os.path.abspath`` of the path (``..`` and ``.`` collapsed).
    """
    return Path(os.path.normpath(os.path.abspath(path)))


def within(path: Path, root: Path) -> PurePosixPath | None:
    """The path relative to the project root, or ``None`` if it is outside.

    The lexical path is tried first (links inside the project are allowed),
    then the real path (the root or the file reached through another name).

    Args:
        path: the path to test.
        root: the project root.

    Returns:
        The relative POSIX path (``lib/prices.m.prml``), or ``None``.
    """
    candidate = lexical(path)
    for base in (lexical(root), root.resolve()):
        try:
            return PurePosixPath(candidate.relative_to(base).as_posix())
        except ValueError:
            pass
    try:
        return PurePosixPath(path.resolve().relative_to(root.resolve()).as_posix())
    except ValueError:
        return None


def outside_link(path: Path, root: Path) -> tuple[PurePosixPath, Path] | None:
    """The symbolic link through which a path inside the root leaves it.

    Args:
        path: a path for which :func:`within` is not ``None``.
        root: the project root.

    Returns:
        ``(link, target)``: the first link on the way from the root (relative
        to the root) whose target lies outside the real root, and that
        target; ``None`` if the real path of ``path`` is inside the root or
        no such link is found.
    """
    real_root = root.resolve()
    if path.resolve().is_relative_to(real_root):
        return None
    relative = within(path, root)
    if relative is None:
        return None
    current = real_root
    for index, part in enumerate(relative.parts):
        current = current / part
        if current.is_symlink():
            target = current.resolve()
            if not target.is_relative_to(real_root):
                return PurePosixPath(*relative.parts[:index + 1]), target
            current = target
    return None
