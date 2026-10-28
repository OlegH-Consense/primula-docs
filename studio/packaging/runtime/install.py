#!/usr/bin/env python3
"""Install, update or remove the Primula Docs runtime package (stage 14.11).

Layout under PREFIX (default ~/.local):
  share/primula-docs/        the whole package (verified against MANIFEST.sha256)
  share/primula-python/      Python environment of the translator (--system-site-packages)
  bin/primula, bin/primula-studio            launchers (copies, not links)
  libexec/primula-studio     link to the Studio binary in share/primula-docs
  share/icons/…/primula-studio.svg, share/applications/org.primula_docs.Studio.desktop
Outside PREFIX, for the user (С1):
  ~/Primula/examples (--examples-dir)   a working copy of the examples in a visible directory;
                                        a changed copy is kept as examples.old-<time> on update
  ~/.config/primula-docs/Primula Studio.conf   the examples under "Recent projects": a new file
                                        also opens the first example at the first start; in an
                                        existing file the missing examples are appended to the list
                                        (up to 20 entries), everything else stays as it is
--uninstall removes what lies under PREFIX; with --purge also the settings and the cache of
Studio and the copies of the examples (after a confirmation, or --yes).
No compiler, Qt development files or source tree are needed. Only the standard library.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile
import time

from dependencies import default_prefix, modules_status, python_command, runtime_checks, setup_python

DESKTOP = 'org.primula_docs.Studio.desktop'
ICON = 'share/icons/hicolor/scalable/apps/primula-studio.svg'
COMMANDS = ('primula', 'primula-studio')


def verified_files(package):
    """Relative paths of MANIFEST.sha256 after checking each file and its digest."""
    files = []
    for line in (package/'MANIFEST.sha256').read_text().splitlines():
        digest, relative = line.split('  ', 1)
        path = Path(relative)
        if path.is_absolute() or '..' in path.parts:
            raise RuntimeError('Unsafe path in the package manifest: '+relative)
        source = package/path
        if not source.is_file() or source.is_symlink():
            raise RuntimeError('Missing or invalid package file: '+relative)
        if hashlib.sha256(source.read_bytes()).hexdigest() != digest:
            raise RuntimeError('Package checksum mismatch: '+relative)
        files.append(path)
    if not files:
        raise RuntimeError('Empty package manifest.')
    return files


def atomic_copy(source, target):
    """Copy source to target through a temporary file of the target directory."""
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix='.primula-', dir=target.parent)
    os.close(descriptor)
    try:
        shutil.copy2(source, temporary)
        os.replace(temporary, target)
    finally:
        Path(temporary).unlink(missing_ok=True)


def desktop_text(package, prefix):
    """The desktop entry with Exec and Icon pointing into prefix (Exec quoting of the
    Desktop Entry Specification: \\, ", `, $ escaped twice, % doubled)."""
    exe = (str(prefix/'bin/primula-studio').replace('\\', '\\\\\\\\').replace('"', '\\\\"')
           .replace('`', '\\\\`').replace('$', '\\\\$').replace('%', '%%'))
    icon = str(prefix/ICON).replace('\\', '\\\\')
    lines = (package/'share/applications'/DESKTOP).read_text().splitlines()
    return '\n'.join(f'Exec="{exe}" %f' if line.startswith('Exec=') else 'Icon='+icon if line.startswith('Icon=')
                     else line for line in lines)+'\n'


def desktop_entries(prefix):
    """Where the desktop entry goes: the prefix and the user's applications directory."""
    return {prefix/'share/applications'/DESKTOP,
            Path(os.environ.get('XDG_DATA_HOME', str(Path.home()/'.local/share')))/'applications'/DESKTOP}


def refresh_desktop(directories):
    if shutil.which('update-desktop-database'):
        for directory in directories:
            if directory.is_dir():
                subprocess.run(['update-desktop-database', str(directory)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def same_tree(first, second):
    """Whether two directories hold the same files with the same contents."""
    def listing(root):
        return {path.relative_to(root): path.read_bytes() for path in root.rglob('*') if path.is_file()}
    return listing(first) == listing(second)


def install_examples(source, target):
    """Copy the examples of the package to a visible working directory.

    An existing copy that differs from the package (edited by the user, or of an older
    version) is renamed to ``examples.old-<time>`` first, so nothing the user wrote is lost.

    Returns:
        The renamed old copy, or ``None``.
    """
    old = None
    if target.exists():
        if target.is_dir() and not target.is_symlink() and same_tree(source, target):
            return None
        old = target.with_name(target.name+'.old-'+time.strftime('%Y%m%d-%H%M%S'))
        target.rename(old)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, target)
    return old


def settings_path():
    """The settings file of Primula Studio (QSettings, native format on Linux)."""
    config = Path(os.environ.get('XDG_CONFIG_HOME') or Path.home()/'.config')
    return config/'primula-docs'/'Primula Studio.conf'


def ini_string(value):
    """A string value of a Qt INI file, always quoted (Qt reads quoted list items).

    A leading ``@`` is doubled: Qt reads ``@Type(...)`` as a typed value.
    """
    if value.startswith('@'):
        value = '@'+value
    return '"'+value.replace('\\', '\\\\').replace('"', '\\"')+'"'


#: Escapes of Qt INI values (qsettings.cpp, iniUnescapedStringList).
INI_ESCAPES = {'a': '\a', 'b': '\b', 'f': '\f', 'n': '\n', 'r': '\r', 't': '\t', 'v': '\v'}


def ini_list(text):
    """The string list of a Qt INI value as QSettings::value().toStringList() reads it.

    Items are separated by commas outside quotes; spaces around unquoted items are dropped;
    backslash escapes (``\\n``, ``\\"``, ``\\xHH``, octal) are decoded; ``@@`` stands for ``@``.

    Args:
        text: the raw value after ``key=``.

    Returns:
        The items; ``[]`` for an empty value or ``@Invalid()``.
    """
    # ``kept`` is the length of the item up to its last quoted, escaped or non-space character:
    # unquoted spaces at both ends of an item are dropped.
    items, chars, quoted, kept, i = [], [], False, 0, 0
    while i < len(text):
        ch = text[i]
        if ch == '"':
            quoted = not quoted
        elif ch == '\\' and i+1 < len(text):
            i += 1
            ch = text[i]
            if ch == 'x' or ch in '01234567':
                digits, allowed = ('', '0123456789abcdefABCDEF') if ch == 'x' else (ch, '01234567')
                while i+1 < len(text) and text[i+1] in allowed:
                    i += 1
                    digits += text[i]
                chars.append(chr(int(digits or '0', 16 if ch == 'x' else 8)))
            else:
                chars.append(INI_ESCAPES.get(ch, ch))
            kept = len(chars)
        elif ch == ',' and not quoted:
            items.append(''.join(chars[:kept]))
            chars, kept = [], 0
        elif quoted or ch not in ' \t':
            chars.append(ch)
            kept = len(chars)
        elif chars:
            chars.append(ch)            # an inner space; dropped if nothing significant follows
        i += 1
    if chars or items:
        items.append(''.join(chars[:kept]))
    values = [item[1:] if item.startswith('@@') else item for item in items]
    return [] if values == ['@Invalid()'] else values


def write_settings(examples, entries, limit=20):
    """Put the examples under "Recent projects" of Primula Studio.

    A new settings file gets every example and opens the first one at the first start.  In an
    existing file the examples missing from the list are appended after the user's own projects
    while the list has room (Studio keeps 20); other lines, ``last`` included, stay as they are.

    Args:
        examples: the working copy of the examples.
        entries: the project files of the examples, relative to ``examples`` (examples.json).
        limit: the length of the list in Studio.

    Returns:
        ``(path, added, skipped)``: the settings file, the examples added and those that did not
        fit; ``path`` is ``None`` when nothing was written.
    """
    path = settings_path()
    paths = [str(examples/entry) for entry in entries if (examples/entry).is_file()]
    if not paths:
        return None, [], []
    if not path.exists():
        text = ('[projects]\n'
                'recent='+', '.join(ini_string(p) for p in paths)+'\n'
                'last='+ini_string(paths[0])+'\n')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')
        return path, paths, []
    lines = path.read_text(encoding='utf-8').splitlines()
    section, start, line_index, recent = None, None, None, []
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('[') and stripped.endswith(']'):
            section = stripped[1:-1]
            if section == 'projects':
                start = index
        elif section == 'projects' and '=' in line and line.split('=', 1)[0].strip() == 'recent':
            line_index, recent = index, ini_list(line.split('=', 1)[1].strip())
    missing = [p for p in paths if p not in recent]
    added = missing[:max(limit-len(recent), 0)]
    skipped = missing[len(added):]
    if not added:
        return None, [], skipped
    value = 'recent='+', '.join(ini_string(p) for p in recent+added)
    if line_index is not None:
        lines[line_index] = value
    elif start is not None:
        lines.insert(start+1, value)
    else:
        lines += ([''] if lines and lines[-1].strip() else [])+['[projects]', value]
    # Replaced atomically: Studio never reads half a file.
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', prefix='.primula-', dir=path.parent,
                                     delete=False) as handle:
        handle.write('\n'.join(lines)+'\n')
        temporary = Path(handle.name)
    os.chmod(temporary, path.stat().st_mode & 0o777)
    os.replace(temporary, path)
    return path, added, skipped


def install(package, prefix, no_python=False, offline=False, wheelhouse=None, translator_only=False,
            examples_dir=None):
    files = verified_files(package)
    errors, warnings = runtime_checks(package, translator_only)
    for warning in warnings:
        print('WARNING: '+warning)
    if errors:
        raise RuntimeError('\n'.join(errors)+'\nRun check-dependencies.sh --install, then retry. A library mismatch '
                           'can require building Studio on the target system.')
    prefix.mkdir(parents=True, exist_ok=True)
    if no_python:
        ok, detail = modules_status(python_command(prefix))
        if not ok:
            raise RuntimeError('Cannot skip the Python environment: '+str(detail))
    else:
        setup_python(prefix, offline, wheelhouse)
    destination = prefix/'share/primula-docs'
    # Updating from the installed copy itself needs no copying.
    if package.resolve() != destination.resolve():
        destination.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='.primula-install-', dir=destination.parent) as temporary:
            staged = Path(temporary)/'payload'
            staged.mkdir()
            for relative in files+[Path('MANIFEST.sha256')]:
                target = staged/relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(package/relative, target)
            previous = Path(temporary)/'previous'
            if destination.is_symlink():
                raise RuntimeError('The installed package must be a directory, not a symlink.')
            if destination.exists():
                destination.rename(previous)
            try:
                staged.rename(destination)
            except BaseException:
                if previous.exists():
                    previous.rename(destination)
                raise
    for command in COMMANDS:
        atomic_copy(destination/'bin'/command, prefix/'bin'/command)
    (prefix/'libexec').mkdir(exist_ok=True)
    executable = prefix/'libexec/primula-studio'
    link = executable.with_name('.primula-studio-new')
    if link.exists() or link.is_symlink():
        link.unlink()
    link.symlink_to('../share/primula-docs/libexec/primula-studio')
    os.replace(link, executable)
    atomic_copy(destination/ICON, prefix/ICON)
    desktop = desktop_text(destination, prefix)
    entries = desktop_entries(prefix)
    for target in entries:
        target.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', prefix='.primula-', dir=target.parent,
                                         delete=False) as handle:
            handle.write(desktop)
            temporary = Path(handle.name)
        os.chmod(temporary, 0o644)
        os.replace(temporary, target)
    refresh_desktop({target.parent for target in entries})
    version = json.loads((destination/'distribution.json').read_text())['version']
    print('Installed Primula Docs '+version+' (translator and Primula Studio)')
    print('Studio: '+str(prefix/'bin/primula-studio'))
    print('Translator: '+str(prefix/'bin/primula'))
    print('Manuals: '+str(destination))
    if examples_dir is not None and (destination/'examples').is_dir():
        old = install_examples(destination/'examples', examples_dir)
        print('Examples: '+str(examples_dir))
        if old is not None:
            print('The previous copy of the examples is kept as '+str(old))
        listing = destination/'examples'/'examples.json'
        entries = json.loads(listing.read_text(encoding='utf-8'))['entries'] if listing.is_file() else []
        written, added, skipped = write_settings(examples_dir, entries)
        if written is not None:
            print(f'Primula Studio settings: {len(added)} examples under "Recent projects": {written}')
        elif not skipped:
            print('Primula Studio settings: the examples are already under "Recent projects"')
        if skipped:
            print(f'"Recent projects" of Primula Studio is full (20): {len(skipped)} examples are not listed; '
                  'open them from '+str(examples_dir))
    if str(prefix/'bin') not in os.environ.get('PATH', '').split(os.pathsep):
        print('Add to your shell PATH if needed: export PATH='+shlex.quote(str(prefix/'bin'))+':"$PATH"')


def uninstall(prefix, keep_python=False):
    """Remove what install() created; user settings, projects and the copy of the examples are not touched."""
    removed = []
    for path in [prefix/'bin'/command for command in COMMANDS]+[prefix/'libexec/primula-studio', prefix/ICON,
                                                                 *desktop_entries(prefix)]:
        if path.is_file() or path.is_symlink():
            path.unlink()
            removed.append(path)
    for directory in [prefix/'share/primula-docs']+([] if keep_python else [prefix/'share/primula-python']):
        if directory.is_dir() and not directory.is_symlink():
            shutil.rmtree(directory)
            removed.append(directory)
    refresh_desktop({entry.parent for entry in desktop_entries(prefix)})
    for path in removed:
        print('Removed: '+str(path))
    if not removed:
        print('Nothing to remove under '+str(prefix))


def purge(examples, assume_yes=False):
    """Remove the user data of Primula Studio outside the prefix, after a confirmation.

    The settings directory (settings, file types and own templates of Studio), the cache, the
    working copy of the examples and its older copies ``examples.old-*``.  A copy of the
    examples is removed only when it has ``examples.json`` of the package: a directory given by
    mistake is left alone.  The projects of the user elsewhere are never touched.

    Args:
        examples: the working copy of the examples (``--examples-dir``).
        assume_yes: do not ask (``--yes``).

    Returns:
        ``True`` when the data were removed or there was nothing to remove.
    """
    cache = Path(os.environ.get('XDG_CACHE_HOME') or Path.home()/'.cache')/'primula-docs'
    candidates = [settings_path().parent, cache]
    for copy in [examples, *sorted(examples.parent.glob(glob_escape(examples.name)+'.old-*'))]:
        if copy.is_dir() and not copy.is_symlink():
            if (copy/'examples.json').is_file():
                candidates.append(copy)
            else:
                print('Kept (not a copy of the examples of the package): '+str(copy))
    found = [path for path in candidates if path.exists() or path.is_symlink()]
    if not found:
        print('No settings, cache or examples of Primula Studio to remove')
        return True
    print('User data of Primula Studio to remove (settings, file types, own templates, the cache, '
          'the examples with your changes in them):')
    for path in found:
        print('  '+str(path))
    if not assume_yes:
        if not sys.stdin.isatty():
            raise RuntimeError('--purge asks for a confirmation: run it in a terminal or add --yes.')
        if input('Remove them? [y/N] ').strip().lower() not in ('y', 'yes'):
            print('The user data are kept')
            return False
    for path in found:
        if path.is_dir() and not path.is_symlink():
            shutil.rmtree(path)
        else:
            path.unlink()
        print('Removed: '+str(path))
    # ~/Primula itself when nothing else is left in it.
    if examples.parent.is_dir() and not any(examples.parent.iterdir()):
        examples.parent.rmdir()
        print('Removed: '+str(examples.parent))
    return True


def glob_escape(name):
    """``name`` with the special characters of glob patterns taken literally."""
    return ''.join('['+ch+']' if ch in '*?[' else ch for ch in name)


def installed_prefix(package):
    """The prefix of an installed copy (``PREFIX/share/primula-docs``), else ``None``."""
    if package.name == 'primula-docs' and package.parent.name == 'share':
        return package.parent.parent
    return None


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--package-dir', type=Path, required=True)
    parser.add_argument('--prefix', type=Path,
                        help='Installation prefix (default ~/.local; --uninstall from an installed copy: its prefix).')
    parser.add_argument('--no-python-install', action='store_true', help='Use an already prepared Python environment.')
    parser.add_argument('--offline', action='store_true', help='No network: the system PyYAML or --wheelhouse.')
    parser.add_argument('--wheelhouse', type=Path, help='Local Python wheels; pip uses --no-index.')
    parser.add_argument('--translator-only', action='store_true', help='Do not check Studio (a system without a desktop).')
    parser.add_argument('--examples-dir', type=Path, default=Path.home()/'Primula'/'examples',
                        help='Visible working copy of the examples (default ~/Primula/examples).')
    parser.add_argument('--no-examples', action='store_true',
                        help='Do not copy the examples and do not create the Studio settings.')
    parser.add_argument('--uninstall', action='store_true', help='Remove the installed package from the prefix.')
    parser.add_argument('--keep-python', action='store_true', help='With --uninstall: keep share/primula-python.')
    parser.add_argument('--purge', action='store_true',
                        help='With --uninstall: also remove the settings and cache of Studio and the copies of '
                             'the examples (asks first).')
    parser.add_argument('--yes', action='store_true', help='With --purge: do not ask.')
    args = parser.parse_args()
    if (args.purge or args.yes) and not args.uninstall:
        parser.error('--purge and --yes go with --uninstall')
    package = args.package_dir.resolve()
    if args.prefix is not None:
        prefix = args.prefix.expanduser().absolute()
    else:
        prefix = (args.uninstall and installed_prefix(package)) or default_prefix()
    try:
        if args.uninstall:
            uninstall(prefix, args.keep_python)
            if args.purge and not purge(args.examples_dir.expanduser().absolute(), args.yes):
                return 1
        else:
            install(package, prefix, args.no_python_install, args.offline, args.wheelhouse,
                    args.translator_only,
                    None if args.no_examples else args.examples_dir.expanduser().absolute())
        return 0
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        print('ERROR: '+str(exc), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
