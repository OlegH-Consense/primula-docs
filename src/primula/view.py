"""Quick view of a document: ``primula view FILE`` (stage 24.1).

The command builds the document into a temporary directory exactly as
``primula build FILE --pdf`` does, opens the PDF in a viewer and deletes the
files when the viewer is closed.  If the build fails, the build log is shown
instead of the PDF.  It is meant for a file manager: ``View=primula-view %f``
in Midnight Commander (F3), "Open with" of a desktop.

``--text`` is the fast variant without LibreOffice: the document is exported
to plain text through pandoc (stage 19.1) and printed.

The viewer
    A viewer that is given (``--viewer``, ``PRIMULA_VIEWER``) or recognised
    (the PDF viewer of the desktop, then the first known one in ``PATH``) is
    waited for, so the files can be deleted afterwards.  ``xdg-open`` returns
    at once; its files stay in the runtime directory and are removed by a
    later run (after a day) or at logout.

The speed
    LibreOffice needs a user profile; a fresh one costs more than a second.
    The view keeps its profile in ``~/.cache/primula`` (``PRIMULA_LO_PROFILE``
    of :mod:`primula.odf.pdf`); a run that finds it busy takes a temporary one.
"""

from __future__ import annotations

import contextlib
import io
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import TextIO

from primula.i18n import Catalog

EXIT_OK = 0
EXIT_NO_VIEWER = 1
EXIT_FAILED = 2

#: PDF viewers that stay in the foreground until their window is closed, in the order of preference.
KNOWN_VIEWERS = ("okular", "evince", "atril", "xreader", "zathura", "mupdf", "qpdfview")
#: Stale temporary directories of earlier views are removed after this many seconds.
STALE_SECONDS = 24 * 3600


def _user_id() -> str:
    """The numeric user id (POSIX) or the login name (Windows has no ``getuid``)."""
    getuid = getattr(os, "getuid", None)
    return str(getuid()) if getuid else os.environ.get("USERNAME", "user")


def work_root() -> Path:
    """The directory of temporary views, created: ``$XDG_RUNTIME_DIR/primula-view`` (tmpfs, wiped at logout),
    else a private directory in the system temporary directory."""
    candidates = []
    runtime = os.environ.get("XDG_RUNTIME_DIR")
    if runtime:
        candidates.append(Path(runtime) / "primula-view")
    candidates.append(Path(tempfile.gettempdir()) / f"primula-view-{_user_id()}")
    for path in candidates:
        try:
            path.mkdir(parents=True, exist_ok=True, mode=0o700)
        except OSError:
            continue
        if os.access(path, os.W_OK):
            return path
    raise OSError("no writable directory for the view")


def purge_stale(root: Path, now: float | None = None) -> None:
    """Remove the directories of earlier views that nobody has waited for (``xdg-open``)."""
    limit = (time.time() if now is None else now) - STALE_SECONDS
    if not root.is_dir():
        return
    for entry in root.iterdir():
        with contextlib.suppress(OSError):
            if entry.is_dir() and entry.stat().st_mtime < limit:
                shutil.rmtree(entry, ignore_errors=True)


def profile_dir() -> Path:
    """The LibreOffice profile kept between views."""
    base = os.environ.get("XDG_CACHE_HOME") or (os.environ.get("LOCALAPPDATA") if sys.platform == "win32" else None) \
        or str(Path.home() / ".cache")
    return Path(base) / "primula" / "libreoffice-profile"


def desktop_viewer() -> str | None:
    """The PDF viewer of the desktop if it is a known one (``xdg-mime``), else the first known in PATH."""
    default = ""
    if shutil.which("xdg-mime"):
        with contextlib.suppress(OSError, subprocess.SubprocessError):
            default = subprocess.run(["xdg-mime", "query", "default", "application/pdf"],
                                     capture_output=True, text=True, timeout=10, check=False).stdout.lower()
    for name in KNOWN_VIEWERS:
        if name in default and shutil.which(name):
            return name
    return next((name for name in KNOWN_VIEWERS if shutil.which(name)), None)


def choose_viewer(explicit: str | None) -> tuple[list[str], bool]:
    """Pick the viewer command.

    Args:
        explicit: ``--viewer`` value, or ``None``.

    Returns:
        ``(command, wait)``: the command without the file and whether the
        process stays until the window is closed (so the files may be deleted).
    """
    given = explicit or os.environ.get("PRIMULA_VIEWER")
    if given:
        return shlex.split(given), True
    known = desktop_viewer()
    if known:
        return [known], True
    if sys.platform == "win32":    # the program associated with .pdf; does not wait
        return ["cmd", "/c", "start", ""], False
    return ["xdg-open"], False


def forwarded_options(args) -> list[str]:
    """Options of ``view`` that mean the same for ``build``/``export``."""
    options: list[str] = []
    for flag in ("review", "unsafe"):
        if getattr(args, flag, False):
            options.append(f"--{flag}")
    if getattr(args, "build_date", None) is not None:
        options += ["--build-date", args.build_date.isoformat()]
    for style in getattr(args, "style", []):
        options += ["--style", style]
    for param in getattr(args, "param", []):
        options += ["--param", param]
    if getattr(args, "timeout", None) is not None:
        options += ["--timeout", str(args.timeout)]
    if getattr(args, "project", None) is not None:
        options += ["--project", str(args.project)]
    if getattr(args, "no_project", False):
        options.append("--no-project")
    if getattr(args, "lang", None):
        options += ["--lang", args.lang]
    return options


@contextlib.contextmanager
def _shared_profile():
    """Make :mod:`primula.odf.pdf` use the kept profile while the block runs."""
    previous = os.environ.get("PRIMULA_LO_PROFILE")
    os.environ["PRIMULA_LO_PROFILE"] = str(profile_dir())
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop("PRIMULA_LO_PROFILE", None)
        else:
            os.environ["PRIMULA_LO_PROFILE"] = previous


def _run_primula(argv: Sequence[str]) -> tuple[int, str]:
    """Run ``primula`` in this process; return the exit code and everything it wrote."""
    from primula.cli import main

    log = io.StringIO()
    code = main(list(argv), err=log, out=log)
    return code, log.getvalue()


def show_text(title: str, text: str, work: Path, err: TextIO, prompt: str = "Press Enter.") -> bool:
    """Show a text (a build log, a summary): in the terminal if there is one, else in a dialog or a text viewer.

    Args:
        title: the first line.
        text: the text.
        work: the temporary directory (the file for a dialog is written there).
        err: the terminal stream.
        prompt: what the terminal asks before it closes.

    Returns:
        ``True`` if the files in ``work`` must stay (a viewer that does not wait).
    """
    if sys.stdin.isatty() and sys.stderr.isatty():
        print(f"{title}\n\n{text}", file=err)
        print(prompt, file=err, end=" ", flush=True)
        with contextlib.suppress(EOFError, KeyboardInterrupt):
            input()
        return False
    path = work / "view.txt"
    path.write_text(f"{title}\n\n{text}", encoding="utf-8")
    dialogs = (("kdialog", ["--textbox", str(path), "820", "520"]),
               ("zenity", ["--text-info", f"--filename={path}", "--width=820", "--height=520"]))
    for name, arguments in dialogs:
        if shutil.which(name):
            subprocess.run([name, *arguments], check=False)
            return False
    if shutil.which("xdg-open"):
        subprocess.run(["xdg-open", str(path)], check=False)
        return True
    print(f"{title}\n\n{text}", file=err)
    return False


def show_log(text: str, source: Path, work: Path, catalog: Catalog, err: TextIO) -> bool:
    """Show the build log of ``source`` (see :func:`show_text`)."""
    return show_text(catalog.text("view.log_title", file=str(source)), text, work, err,
                     catalog.text("view.press_enter"))


def summary_of(source: Path, catalog: Catalog) -> str | None:
    """The summary of ``source`` if it is a file without an output document, else ``None``.

    A project file, a module and a styles module are described by
    :mod:`primula.describe`; a directory with ``project.p.prml`` stands for the project.
    """
    from primula.describe import describe, render_text

    path = source / "project.p.prml" if source.is_dir() and (source / "project.p.prml").is_file() else source
    if not path.is_file():
        return None
    data = describe(path, catalog)
    return render_text(data, catalog) if data["kind"] in ("module", "styles", "project") else None


def run(args, catalog: Catalog, err: TextIO, out: TextIO,
        launch: Callable[[list[str]], int] | None = None) -> int:
    """``primula view``.

    Args:
        args: parsed arguments (``file``, ``viewer``, ``text``, ``keep`` and the options of ``build``).
        catalog: the message catalogue.
        err: stream for messages.
        out: stream for the text of ``--text``.
        launch: starts the viewer (a test replaces it); the command with the file, returns the exit code.

    Returns:
        0 shown, 2 the build failed (the log was shown), 1 no viewer could be started.
    """
    source: Path = args.file
    summary = summary_of(source, catalog)
    if summary is not None:
        # A module, a styles module or a project has no output document: show what is inside.
        if args.text:
            out.write(summary)
            return EXIT_OK
        root = work_root()
        purge_stale(root)
        work = Path(tempfile.mkdtemp(prefix="v-", dir=root))
        try:
            stay = show_text(catalog.text("view.summary_note"), summary, work, err, catalog.text("view.press_enter"))
        finally:
            if not stay:
                shutil.rmtree(work, ignore_errors=True)
        return EXIT_OK
    root = work_root()
    purge_stale(root)
    work = Path(tempfile.mkdtemp(prefix="v-", dir=root))
    stay = args.keep
    options = forwarded_options(args)
    try:
        if args.text:
            target = work / "document.txt"
            code, log = _run_primula(["export", str(source), "--to", "plain", "-o", str(target), *options])
            if code != 0 or not target.is_file():
                print(f"{catalog.text('view.log_title', file=str(source))}\n\n{log}", file=out)
                return EXIT_FAILED
            out.write(target.read_text(encoding="utf-8"))
            return EXIT_OK
        odt, pdf = work / "document.odt", work / "document.pdf"
        with _shared_profile():
            code, log = _run_primula(["build", str(source), "-o", str(odt), "--pdf", str(pdf), *options])
        if code != 0 or not pdf.is_file():
            stay = show_log(log, source, work, catalog, err) or stay
            return EXIT_FAILED
        if args.keep:
            err.write(log)       # the messages of a successful build are shown only with --keep
        command, wait = choose_viewer(args.viewer)
        stay = stay or not wait
        try:
            (launch or _launch)([*command, str(pdf)])
        except OSError as exc:
            print(catalog.text("view.no_viewer", reason=f"{command[0]}: {exc.strerror or exc}"), file=err)
            return EXIT_NO_VIEWER
        return EXIT_OK
    finally:
        if stay:
            if args.keep:
                print(catalog.text("view.kept", path=str(work)), file=err)
        else:
            shutil.rmtree(work, ignore_errors=True)


def _launch(command: list[str]) -> int:
    """Start the viewer and wait for it."""
    return subprocess.run(command, check=False).returncode
