#!/usr/bin/env python3
"""Runtime checks of the Primula Docs package and optional installation of what it
needs from the system (stage 14.11). No compiler or Qt development tools are needed.

The translator needs Python 3.11+ with PyYAML 6; Primula Studio needs the Qt 6
runtime (Core, Gui, Widgets, Pdf, PdfWidgets, a platform plugin, the SVG icon
plugin); PDF export needs LibreOffice Writer. Only the standard library is used.
"""
import argparse
import json
import os
from pathlib import Path
import platform
import shlex
import shutil
import subprocess
import sys

PYTHON_MINIMUM = (3, 11)
# The only required third-party module of the translator (pyproject.toml: PyYAML>=6.0,<7).
REQUIREMENT = 'PyYAML>=6.0,<7'


def run(command, **kwargs):
    """Run a command and capture its text output; timeout 30 s unless given."""
    return subprocess.run(list(map(str, command)), text=True, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, timeout=kwargs.pop('timeout', 30), **kwargs)


def distribution_id():
    """Fields of /etc/os-release (ID, VERSION_ID, ID_LIKE, PRETTY_NAME)."""
    values = {}
    path = Path('/etc/os-release')
    if path.is_file():
        for line in path.read_text().splitlines():
            if '=' in line:
                key, value = line.split('=', 1)
                values[key] = value.strip('"\'')
    return values


def default_prefix():
    """Installation prefix: PRIMULA_INSTALL_PREFIX or ~/.local."""
    return Path(os.environ.get('PRIMULA_INSTALL_PREFIX', str(Path.home()/'.local'))).expanduser().absolute()


def python_command(prefix):
    """The interpreter of the translator: the private environment of prefix, else PRIMULA_PYTHON or this one."""
    private = prefix/'share/primula-python/bin/python3'
    if private.is_file():
        return str(private)
    return os.environ.get('PRIMULA_PYTHON', sys.executable)


def modules_status(python):
    """Whether python can run the translator: (True, versions) or (False, reason)."""
    probe = '''import sys, json, importlib.metadata as m
if sys.version_info < (3, 11): raise RuntimeError("Python 3.11+ is required, found " + sys.version.split()[0])
import yaml
version = m.version("PyYAML")
if not (6,) <= tuple(int(p) for p in version.split(".")[:1]) < (7,): raise RuntimeError("PyYAML 6 is required, found " + version)
result = {"python": sys.version.split()[0], "PyYAML": version}
try:
    result["fonttools"] = m.version("fonttools")
except m.PackageNotFoundError:
    result["fonttools"] = None
print(json.dumps(result))
'''
    try:
        result = run([python, '-c', probe])
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, str(exc)
    if result.returncode == 0:
        return True, json.loads(result.stdout)
    lines = result.stderr.strip().splitlines()
    return False, lines[-1] if lines else 'the interpreter failed'


def platform_plugins(name):
    """Files of the Qt platform plugin ``name``, any of which is enough.

    Older Qt 6 (Debian 12 and 13) ships Wayland as ``wayland-generic`` and ``wayland-egl``
    (``wayland`` picks one); newer Qt has the single plugin ``libqwayland.so`` (seen on
    openSUSE Tumbleweed with Qt 6.12, 27.10.2026).
    """
    if name == 'wayland':
        return ['platforms/libqwayland.so', 'platforms/libqwayland-generic.so', 'platforms/libqwayland-egl.so']
    return ['platforms/libq'+name+'.so']


def runtime_checks(package, translator_only=False):
    """Errors and warnings for running the package on this system."""
    errors, warnings = [], []
    metadata = json.loads((package/'distribution.json').read_text())
    if sys.version_info < PYTHON_MINIMUM:
        errors.append('Python 3.11+ is required.')
    if not translator_only:
        if metadata['architecture'] != platform.machine():
            errors.append(f'Architecture mismatch: package={metadata["architecture"]}, system={platform.machine()}.')
        host = distribution_id()
        if metadata['os_id'] != host.get('ID') or metadata['os_version'] != host.get('VERSION_ID'):
            warnings.append(f'The package was built on {metadata["os_name"]}. If the library checks fail, '
                            'build Studio on this system (studio/build-debian.sh or studio/build-studio.sh).')
        binary = package/'libexec/primula-studio'
        if not shutil.which('ldd'):
            errors.append('ldd is required for shared-library checks (libc runtime tools).')
        else:
            linked = run(['ldd', binary])
            if linked.returncode or 'not found' in linked.stdout or 'version `' in linked.stderr:
                errors.append('Studio shared-library/ABI check failed:\n'+linked.stdout.strip()+'\n'+linked.stderr.strip())
        try:
            info = run([binary, '--runtime-info'])
            if info.returncode:
                errors.append('Cannot start Studio: '+info.stderr.strip())
            else:
                data = json.loads(info.stdout)
                plugins = Path(data['plugin_path'])
                override = os.environ.get('QT_PLUGIN_PATH')
                roots = [Path(p) for p in override.split(os.pathsep)] if override else []
                roots.append(plugins)

                def plugin(relative):
                    return next((root/relative for root in roots if (root/relative).is_file()), None)
                platform_name = os.environ.get('QT_QPA_PLATFORM', '').split(':', 1)[0]
                if not platform_name:
                    platform_name = ('wayland' if os.environ.get('WAYLAND_DISPLAY')
                                     else 'xcb' if os.environ.get('DISPLAY') else 'offscreen')
                candidates = platform_plugins(platform_name)
                if not any(plugin(relative) for relative in candidates):
                    errors.append('Missing Qt platform plugin: '+' or '.join(candidates))
                if not plugin('iconengines/libqsvgicon.so'):
                    warnings.append('Qt SVG icon plugin is missing; the Studio icon may not display inside the application.')
                smoke = run([binary, '--check-runtime'], env=dict(os.environ, QT_QPA_PLATFORM=platform_name))
                if smoke.returncode:
                    errors.append(f'Qt platform check failed ({platform_name}): '
                                  + (smoke.stderr.strip() or f'exit code {smoke.returncode}'))
        except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
            errors.append('Cannot check Studio: '+str(exc))
    if not (shutil.which('libreoffice') or shutil.which('soffice')):
        warnings.append('LibreOffice Writer is missing: ODT is built, PDF export does not work.')
    if not translator_only and not shutil.which('codex'):
        warnings.append('Codex CLI is missing: editing and building work, AI needs a separate Codex installation and login.')
    if shutil.which('fc-match'):
        font = run(['fc-match', '-f', '%{family}', 'Liberation Sans'])
        if font.returncode == 0 and 'Liberation Sans' not in font.stdout:
            warnings.append('Liberation Sans is missing: the standard styles use a substitute font, pagination may change.')
    return errors, warnings


def system_install_plan(osinfo=None, bits=None):
    """Package-manager commands for the runtime dependencies (openSUSE, Debian/Ubuntu)."""
    osinfo = osinfo or distribution_id()
    identities = {osinfo.get('ID', ''), *osinfo.get('ID_LIKE', '').split()}
    if any('suse' in item for item in identities):
        # Shared-library capabilities avoid distribution-specific Qt PDF package names.
        suffix = '()(64bit)' if (bits or platform.architecture()[0]) == '64bit' else ''
        libraries = ['libQt6Core.so.6', 'libQt6Gui.so.6', 'libQt6Widgets.so.6',
                     'libQt6Pdf.so.6', 'libQt6PdfWidgets.so.6', 'libQt6Svg.so.6']
        python_flavor = f'python{sys.version_info.major}{sys.version_info.minor}'
        if shutil.which('rpm'):
            owner = run(['rpm', '-qf', str(Path(sys.executable).resolve()), '--qf', '%{NAME}'])
            if owner.returncode == 0 and owner.stdout.strip().startswith('python'):
                python_flavor = owner.stdout.strip().removesuffix('-base')
        packages = ['python3', python_flavor+'-PyYAML', *[library+suffix for library in libraries],
                    'qt6-base', 'qt6-wayland',
                    ('/usr/lib64' if suffix else '/usr/lib')+'/qt6/plugins/iconengines/libqsvgicon.so',
                    'libreoffice-writer', 'libreoffice-pyuno', python_flavor+'-FontTools',
                    'desktop-file-utils', 'liberation-fonts']
        return [['zypper', 'install', *packages]]
    if identities.intersection({'debian', 'ubuntu'}):
        # Widgets/Pdf pull the right Core/Gui package names of each release (t64 in Debian 13).
        # python3-uno fills page numbers of the contents in PDF, fonttools sizes 'auto' columns;
        # the private environment sees both through --system-site-packages.
        packages = ['python3', 'python3-venv', 'python3-yaml',
                    'libqt6widgets6', 'libqt6pdf6', 'libqt6pdfwidgets6',
                    'libqt6svg6', 'qt6-qpa-plugins', 'qt6-wayland', 'libreoffice-writer',
                    'python3-uno', 'python3-fonttools', 'desktop-file-utils', 'fonts-liberation']
        version = osinfo.get('VERSION_ID', '').split('.')[0]
        if osinfo.get('ID') == 'debian' and version.isdigit() and int(version) >= 13:
            packages.append('qt6-svg-plugins')
        return [['apt-get', 'update'], ['apt-get', 'install', *packages]]
    raise RuntimeError('Automatic installation supports openSUSE and Debian/Ubuntu. Install Python 3.11+ with PyYAML 6, '
                       'Qt 6 Core/Gui/Widgets/Pdf/PdfWidgets with a platform plugin and LibreOffice Writer '
                       'with your package manager.')


def setup_python(prefix, offline=False, wheelhouse=None):
    """Create PREFIX/share/primula-python (a venv that also sees the system site-packages)
    and install PyYAML into it only when the system has none: from PyPI, or from wheelhouse."""
    environment = prefix/'share/primula-python'
    executable = environment/'bin/python3'
    created = not executable.is_file()
    try:
        if created:
            environment.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run([sys.executable, '-m', 'venv', '--system-site-packages', str(environment)], check=True)
        ok, detail = modules_status(executable)
        if ok:
            print('Python environment: ready ('+str(environment)+')')
            return
        if offline and wheelhouse is None:
            raise RuntimeError('PyYAML is missing and the installation is offline: install the system package '
                               '(python3-yaml / python3-PyYAML) or pass --wheelhouse DIRECTORY.')
        arguments = [str(executable), '-m', 'pip', 'install', '--only-binary=:all:']
        if wheelhouse is not None:
            arguments += ['--no-index', '--find-links', str(wheelhouse.resolve())]
        subprocess.run(arguments+[REQUIREMENT], check=True)
        ok, detail = modules_status(executable)
        if not ok:
            raise RuntimeError('Python dependency check failed: '+str(detail))
    except BaseException:
        if created and environment.exists():
            shutil.rmtree(environment)
        raise


def check(package, prefix, translator_only=False, require_pdf=False):
    """Print the state of the dependencies; True when nothing blocks the work."""
    errors, warnings = runtime_checks(package, translator_only)
    ok, detail = modules_status(python_command(prefix))
    if not ok:
        errors.append('The translator cannot run: '+str(detail))
    else:
        print('Python: '+json.dumps(detail))
    if require_pdf and not (shutil.which('libreoffice') or shutil.which('soffice')):
        errors.append('LibreOffice Writer is required for PDF export.')
    for warning in warnings:
        print('WARNING: '+warning)
    for error in errors:
        print('ERROR: '+error)
    if not errors:
        print('Runtime dependencies: OK')
    return not errors


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--package-dir', type=Path, required=True)
    parser.add_argument('--prefix', type=Path, default=default_prefix())
    parser.add_argument('--install', action='store_true', help='Install the system runtime packages (sudo) and the Python environment.')
    parser.add_argument('--yes', action='store_true', help='Noninteractive package manager.')
    parser.add_argument('--print-plan', action='store_true', help='Print the system commands without running them.')
    parser.add_argument('--translator-only', action='store_true', help='Check only the translator, not Studio.')
    parser.add_argument('--require-pdf', action='store_true', help='Treat a missing LibreOffice as an error.')
    parser.add_argument('--wheelhouse', type=Path, help='Local Python wheels for PyYAML (pip --no-index).')
    args = parser.parse_args()
    try:
        if args.install or args.print_plan:
            commands = system_install_plan()
            for command in commands:
                print('System packages: '+shlex.join(command), flush=True)
            if args.print_plan:
                return 0
            privilege = [] if os.geteuid() == 0 else ['sudo']
            if privilege and not shutil.which('sudo'):
                raise RuntimeError('sudo is missing. Ask your administrator to run the printed commands, then rerun this script.')
            for command in commands:
                if args.yes:
                    if command[0] == 'zypper':
                        command.insert(1, '--non-interactive')
                    elif command[1] == 'install':
                        command.insert(2, '-y')
                subprocess.run(privilege+command, check=True)
            setup_python(args.prefix.expanduser().absolute(), wheelhouse=args.wheelhouse)
        return 0 if check(args.package_dir.resolve(), args.prefix.expanduser().absolute(),
                          args.translator_only, args.require_pdf) else 1
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        print('ERROR: '+str(exc), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
