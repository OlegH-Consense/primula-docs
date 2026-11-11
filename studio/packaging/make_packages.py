#!/usr/bin/env python3
"""Make system packages (.deb and .rpm) from the runtime package of Primula Docs (stage 26.1).

The input is the directory that ``make-distribution.sh`` (packaging/make_distribution.py) creates.
The packages install under /usr:

  /usr/share/primula-docs/        the translator, Studio, manuals, examples, libraries (the package
                                  without its installer; the launchers find it from their own place)
  /usr/bin/primula, primula-view, primula-studio     launchers
  /usr/libexec/primula-studio     link to the Studio binary in /usr/share/primula-docs/libexec
  /usr/share/applications/…, /usr/share/icons/hicolor/scalable/apps/…     the menu entry and the icon
  /usr/share/doc/primula-docs/copyright           the licence (Apache-2.0)

The translator runs on the Python 3 of the system with PyYAML (no private environment); Studio links
to the Qt 6 of the system, so a package is for the family of systems it was built on
(``distribution.json`` tells which); the dependencies are the generic names of the family.

The .deb is written by this script (the formats ar and tar of the standard library, xz): ``dpkg-deb``
is not needed, so it can be made on any system.  The .rpm is made by ``rpmbuild`` (a spec file is written).
Only the standard library is used.

    make_packages.py --package dist/primula-docs-0.4.4-debian12-x86_64 --output dist/packages
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import lzma
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time

NAME = 'primula-docs'
HOMEPAGE = 'https://github.com/OlegH-Consense/primula-docs'
SUMMARY = 'Primula document translator (ODT/PDF) and Primula Studio editor'
DESCRIPTION = ('Primula is a plain-text markup language for business and technical documents (contracts, acts, '
               'invoices, letters, manuals).\nThe translator builds an editable ODT for LibreOffice Writer, and a PDF '
               'through LibreOffice.\nPrimula Studio is a desktop workplace for writing, checking and building the '
               'documents, with an AI assistant.')
#: Left out of /usr/share/primula-docs: what the installer needs and what lies elsewhere in the system.
NOT_SHARED = {'install.sh', 'uninstall.sh', 'check-dependencies.sh', 'runtime', 'bin', 'MANIFEST.sha256'}
NOT_SHARED_SUB = {Path('share/icons'), Path('share/applications')}
DEB_ARCHITECTURE = {'x86_64': 'amd64', 'aarch64': 'arm64', 'armv7l': 'armhf', 'i686': 'i386'}
#: Dependencies by family of systems: the generic names of the Qt 6 libraries and of Python.
DEB_DEPENDS = ['python3 (>= 3.11)', 'python3-yaml', 'libqt6widgets6 (>= 6.4)', 'libqt6pdf6 (>= 6.4)',
               'libqt6pdfwidgets6 (>= 6.4)', 'libqt6svg6 (>= 6.4)']
#: Recommends are installed by apt by default, so only what a document build needs. python3-fonttools is left
#: out: its own Recommends pull python3-scipy, python3-sympy and pythran (the widths of `auto` columns fall back
#: to an estimate without it, P5112); qt6-wayland is in the Plasma/GNOME desktops that run Wayland already.
DEB_RECOMMENDS = ['libreoffice-writer', 'python3-uno', 'fonts-liberation', 'qt6-qpa-plugins']
DEB_SUGGESTS = ['pandoc', 'python3-fonttools', 'qt6-wayland']
#: ID / ID_LIKE of /etc/os-release of the systems that use each package format.
DEB_FAMILY = {'debian', 'ubuntu', 'raspbian', 'devuan'}
RPM_FAMILY = {'opensuse', 'suse', 'sles', 'fedora', 'rhel', 'centos'}
RPM_REQUIRES = ['python3 >= 3.11', 'python3dist(pyyaml)']
#: libQt6Svg6 (openSUSE) / qt6-qtsvg (Fedora): the SVG icon engine of the toolbar is a Qt plugin that rpm does not see as a
#: library dependency (the .deb names libqt6svg6 in Depends); a name unknown to a system is skipped in Recommends.
RPM_RECOMMENDS = ['libreoffice-writer', 'libreoffice-pyuno', 'python3dist(fonttools)', 'liberation-fonts', 'libQt6Svg6', 'qt6-qtsvg']
RPM_SUGGESTS = ['pandoc']


class Entry:
    """A path of the package: a directory, a file (with its bytes) or a link."""

    def __init__(self, path: str, kind: str, mode: int, data: bytes = b'', link: str = '') -> None:
        self.path, self.kind, self.mode, self.data, self.link = path, kind, mode, data, link


def epoch() -> int:
    """The time stamp of the files: SOURCE_DATE_EPOCH (reproducible packages), else now."""
    return int(os.environ.get('SOURCE_DATE_EPOCH', int(time.time())))


def minimal_glibc(binary: Path, fallback: str) -> str:
    """The oldest glibc that runs the Studio binary: the highest GLIBC_x.y symbol version it uses."""
    try:
        text = subprocess.run(['objdump', '-T', str(binary)], capture_output=True, text=True, timeout=60, check=True).stdout
    except (OSError, subprocess.SubprocessError):
        return fallback
    # The rows of the table carry the version in parentheses: "... *UND* 0000 (GLIBC_2.34) __libc_start_main".
    versions = {tuple(int(part) for part in match.split('.')) for match in re.findall(r'GLIBC_(\d+(?:\.\d+)+)', text)}
    return '.'.join(map(str, max(versions))) if versions else fallback


def strip_binary(entry: 'Entry') -> None:
    """Clean the Studio binary: ``strip --strip-unneeded`` (smaller package) and ``patchelf --remove-rpath`` when installed.

    The Qt CMake targets give the link a RUNPATH of 25 empty entries («::::»); an empty entry is the current directory
    (rpmlint E: binary-or-shlib-defines-rpath), and the libraries are those of the system.
    """
    with tempfile.TemporaryDirectory(prefix='primula-strip-') as work:
        source = Path(work) / 'binary'
        source.write_bytes(entry.data)
        changed = False
        for tool, options in (('strip', ['--strip-unneeded']), ('patchelf', ['--remove-rpath'])):
            if shutil.which(tool):
                changed |= subprocess.run([tool, *options, str(source)], capture_output=True, timeout=120).returncode == 0
        if changed:
            entry.data = source.read_bytes()


def collect(package: Path, licence: Path | None) -> list[Entry]:
    """The files of the packages, from the runtime package directory (directories first, sorted)."""
    files: dict[str, Entry] = {}

    def add_file(path: str, source: Path, mode: int | None = None) -> None:
        executable = os.access(source, os.X_OK)
        files[path] = Entry(path, 'file', mode if mode is not None else (0o755 if executable else 0o644), source.read_bytes())

    for source in sorted(package.rglob('*')):
        relative = source.relative_to(package)
        if relative.parts[0] in NOT_SHARED or any(parent in NOT_SHARED_SUB for parent in (relative, *relative.parents)):
            continue
        if source.is_symlink():
            raise RuntimeError(f'The package holds a link, not a file: {relative}')
        if source.is_file():
            add_file(f'usr/share/{NAME}/{relative.as_posix()}', source)
    for name in ('primula', 'primula-view', 'primula-studio'):
        add_file(f'usr/bin/{name}', package / 'bin' / name, 0o755)
        # The interpreter by a fixed path: rpmlint/lintian reject `/usr/bin/env` in an installed script.
        entry = files[f'usr/bin/{name}']
        entry.data = entry.data.replace(b'#!/usr/bin/env bash\n', b'#!/bin/bash\n', 1).replace(b'#!/usr/bin/env python3\n', b'#!/usr/bin/python3\n', 1)
    strip_binary(files[f'usr/share/{NAME}/libexec/primula-studio']) if f'usr/share/{NAME}/libexec/primula-studio' in files else None
    files['usr/libexec/primula-studio'] = Entry('usr/libexec/primula-studio', 'link', 0o777,
                                                link=f'../share/{NAME}/libexec/primula-studio')
    add_file('usr/share/applications/org.primula_docs.Studio.desktop',
             package / 'share/applications/org.primula_docs.Studio.desktop', 0o644)
    add_file('usr/share/icons/hicolor/scalable/apps/primula-studio.svg',
             package / 'share/icons/hicolor/scalable/apps/primula-studio.svg', 0o644)
    if licence is not None and licence.is_file():
        add_file(f'usr/share/doc/{NAME}/copyright', licence, 0o644)
    if f'usr/share/{NAME}/libexec/primula-studio' not in files:
        raise RuntimeError('The package has no libexec/primula-studio: is it the output of make-distribution.sh?')
    # The directories of all the paths, parents first.
    directories: dict[str, Entry] = {}
    for path in files:
        parent = Path(path).parent
        while str(parent) != '.':
            directories[str(parent)] = Entry(str(parent), 'dir', 0o755)
            parent = parent.parent
    return sorted(directories.values(), key=lambda e: e.path) + sorted(files.values(), key=lambda e: e.path)


def tar_bytes(entries: list[Entry], stamp: int, prefix: str = './') -> bytes:
    """A tar archive of the entries, owned by root:root, names with the prefix (``./usr/…`` as in .deb)."""
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode='w', format=tarfile.GNU_FORMAT) as archive:
        for entry in entries:
            info = tarfile.TarInfo(prefix + entry.path)
            info.mtime, info.uid, info.gid, info.uname, info.gname, info.mode = stamp, 0, 0, 'root', 'root', entry.mode
            if entry.kind == 'dir':
                info.type = tarfile.DIRTYPE
                archive.addfile(info)
            elif entry.kind == 'link':
                info.type, info.linkname = tarfile.SYMTYPE, entry.link
                archive.addfile(info)
            else:
                info.size = len(entry.data)
                archive.addfile(info, io.BytesIO(entry.data))
    return buffer.getvalue()


def ar_member(name: str, data: bytes, stamp: int) -> bytes:
    """A member of an ar archive (the container of a .deb): 60 bytes of header, the data, padding to even."""
    header = f'{name:<16}{stamp:<12}{0:<6}{0:<6}{"100644":<8}{len(data):<10}`\n'.encode('ascii')
    return header + data + (b'\n' if len(data) % 2 else b'')


def deb_control(info: dict, entries: list[Entry], glibc: str, maintainer: str, revision: str) -> str:
    size = -(-sum(len(e.data) for e in entries if e.kind == 'file') // 1024)
    architecture = DEB_ARCHITECTURE.get(info['architecture'], info['architecture'])
    depends = [f'libc6 (>= {glibc})', 'libstdc++6', *DEB_DEPENDS]
    description = DESCRIPTION.replace('\n\n', '\n.\n').splitlines()
    description += ['.', f'Built on {info.get("os_name", "?")} with Qt {info.get("qt_build", "?")}: Studio uses the Qt 6 of the system.']
    lines = [f'Package: {NAME}', f'Version: {info["version"]}-{revision}', 'Section: text', 'Priority: optional',
             f'Architecture: {architecture}', f'Maintainer: {maintainer}', f'Installed-Size: {size}',
             'Depends: ' + ', '.join(depends), 'Recommends: ' + ', '.join(DEB_RECOMMENDS),
             'Suggests: ' + ', '.join(DEB_SUGGESTS), f'Homepage: {HOMEPAGE}',
             f'Description: {SUMMARY}']
    lines += [' ' + line for line in description]
    return '\n'.join(lines) + '\n'


def make_deb(info: dict, entries: list[Entry], output: Path, glibc: str, maintainer: str, revision: str) -> Path:
    """Write ``NAME_VERSION-REVISION_ARCH.deb``: ar archive of debian-binary, control.tar.xz and data.tar.xz."""
    stamp = epoch()
    architecture = DEB_ARCHITECTURE.get(info['architecture'], info['architecture'])
    md5sums = ''.join(f'{hashlib.md5(e.data).hexdigest()}  {e.path}\n' for e in entries if e.kind == 'file')
    control = [Entry('control', 'file', 0o644, deb_control(info, entries, glibc, maintainer, revision).encode()),
               Entry('md5sums', 'file', 0o644, md5sums.encode())]
    control_tar = lzma.compress(tar_bytes(control, stamp), preset=6)
    data_tar = lzma.compress(tar_bytes(entries, stamp), preset=6)
    target = output / f'{NAME}_{info["version"]}-{revision}_{architecture}.deb'
    target.write_bytes(b'!<arch>\n' + ar_member('debian-binary', b'2.0\n', stamp) + ar_member('control.tar.xz', control_tar, stamp)
                       + ar_member('data.tar.xz', data_tar, stamp))
    return target


def rpm_spec(info: dict, entries: list[Entry], revision: str, packager: str) -> str:
    stamp = time.gmtime(epoch())
    files = ['%defattr(-,root,root,-)', f'/usr/share/{NAME}', '/usr/bin/primula', '/usr/bin/primula-view',
             '/usr/bin/primula-studio', '/usr/libexec/primula-studio', '/usr/share/applications/org.primula_docs.Studio.desktop',
             '/usr/share/icons/hicolor/scalable/apps/primula-studio.svg']
    if any(e.path == f'usr/share/doc/{NAME}/copyright' for e in entries):
        files.append(f'%license /usr/share/doc/{NAME}/copyright')
    lines = ['# Written by studio/packaging/make_packages.py; the files are staged by the script, not built here.',
             '%global debug_package %{nil}', '%define __os_install_post %{nil}', '%define _build_id_links none',
             '%define _binary_payload w9.xzdio',
             f'Name: {NAME}', f'Version: {info["version"]}', f'Release: {revision}', f'Summary: {SUMMARY}',
             'License: Apache-2.0', f'URL: {HOMEPAGE}', 'Group: Productivity/Publishing',
             *[f'Requires: {item}' for item in RPM_REQUIRES], *[f'Recommends: {item}' for item in RPM_RECOMMENDS],
             *[f'Suggests: {item}' for item in RPM_SUGGESTS], '', '%description',
             DESCRIPTION, '', f'Built on {info.get("os_name", "?")} with Qt {info.get("qt_build", "?")}: Studio uses the Qt 6 of the system.',
             '', '%prep', '%build', '%install', 'cp -a %{stagedir}/. %{buildroot}/', '', '%files', *files, '',
             '%changelog', f'* {time.strftime("%a %b %d %Y", stamp)} {packager} - {info["version"]}-{revision}',
             '- Package made from the runtime package of Primula Docs.']
    return '\n'.join(lines) + '\n'


def sign_rpm(rpm: Path, key: str, gpg_home: str | None) -> None:
    """Sign ``rpm`` in place with the GnuPG key ``key`` (id, fingerprint or user id) by ``rpmsign --addsign``.

    The key stays in the keyring of the user (``gpg_home`` or the default ``~/.gnupg``); the passphrase, if there is
    one, is asked by gpg-agent (pinentry) - nothing secret passes through this script.  The public key is written
    next to the package by main() so that a user can ``rpm --import`` it.
    """
    if not shutil.which('rpmsign'):
        raise RuntimeError('rpmsign is not installed (package rpm-sign on openSUSE/Fedora): the .rpm is not signed')
    command = ['rpmsign', '--addsign', '--define', f'_gpg_name {key}']
    if gpg_home:
        command += ['--define', f'_gpg_path {gpg_home}']
    result = subprocess.run(command + [str(rpm)], capture_output=True, text=True, timeout=300)
    if result.returncode != 0:
        raise RuntimeError('rpmsign failed:\n' + (result.stdout + result.stderr)[-2000:])


def export_public_key(key: str, gpg_home: str | None, target: Path) -> None:
    """Write the public key (ASCII armor) of ``key`` to ``target``."""
    command = ['gpg'] + (['--homedir', gpg_home] if gpg_home else []) + ['--armor', '--export', key]
    result = subprocess.run(command, capture_output=True, timeout=60)
    if result.returncode != 0 or not result.stdout:
        raise RuntimeError('gpg could not export the public key ' + key)
    target.write_bytes(result.stdout)


def make_rpm(info: dict, entries: list[Entry], output: Path, revision: str, packager: str) -> Path:
    """Run rpmbuild on a staged tree. Raises RuntimeError when it is not installed or fails."""
    if not shutil.which('rpmbuild'):
        raise RuntimeError('rpmbuild is not installed (package rpm-build / rpm): the .rpm is not made')
    stamp = epoch()
    with tempfile.TemporaryDirectory(prefix='primula-rpm-') as work:
        work_path = Path(work)
        stage = work_path / 'stage'
        for entry in entries:
            target = stage / entry.path
            if entry.kind == 'dir':
                target.mkdir(parents=True, exist_ok=True)
            elif entry.kind == 'link':
                target.parent.mkdir(parents=True, exist_ok=True)
                target.symlink_to(entry.link)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(entry.data)
                target.chmod(entry.mode)
        spec = work_path / f'{NAME}.spec'
        spec.write_text(rpm_spec(info, entries, revision, packager), encoding='utf-8')
        command = ['rpmbuild', '-bb', str(spec), '--define', f'_topdir {work_path / "rpmbuild"}',
                   '--define', f'stagedir {stage}', '--define', 'clamp_mtime_to_source_date_epoch 1',
                   '--define', 'use_source_date_epoch_as_buildtime 1', '--define', '_buildhost primula-docs',
                   '--target', f'{info["architecture"]}-linux']
        result = subprocess.run(command, capture_output=True, text=True, timeout=900, env=dict(os.environ, SOURCE_DATE_EPOCH=str(stamp)))
        if result.returncode != 0:
            raise RuntimeError('rpmbuild failed:\n' + (result.stdout + result.stderr)[-3000:])
        built = sorted((work_path / 'rpmbuild/RPMS').rglob('*.rpm'))
        if not built:
            raise RuntimeError('rpmbuild made no package')
        target = output / built[0].name
        shutil.copy2(built[0], target)
        return target


def family_warning(info: dict, fmt: str) -> str:
    """A line for the user when the package format does not belong to the system that built Studio.

    The Studio binary is linked to the Qt 6, libstdc++ and glibc of the build system, so a package built
    on openSUSE (Qt 6.12, GCC 15) cannot run on Debian 12/13 whatever its Depends say.
    """
    ids = {str(info.get('os_id', '')).lower(), *str(info.get('os_like', '')).lower().split()}
    own = DEB_FAMILY if fmt == 'deb' else RPM_FAMILY
    if ids & own:
        return ''
    return (f'warning: the .{fmt} is made on {info.get("os_name") or info.get("os_id", "?")}: Studio inside is linked to the '
            f'libraries of this system and will not run on the systems of the .{fmt} family. '
            f'Make the .{fmt} on Debian 12 (it runs on Debian 12 and 13) or on openSUSE for the .rpm.')


def main() -> int:
    parser = argparse.ArgumentParser(description='Make .deb and .rpm packages from the runtime package of Primula Docs.')
    parser.add_argument('--package', type=Path, required=True, help='the directory made by make-distribution.sh')
    parser.add_argument('--output', type=Path, required=True, help='where the packages are written (made if missing)')
    parser.add_argument('--format', choices=['deb', 'rpm', 'all'], default='all')
    parser.add_argument('--licence', type=Path, help='the licence text (default: LICENSES/Apache-2.0.txt of the source tree)')
    parser.add_argument('--revision', default='1', help='the revision of the package (default 1)')
    parser.add_argument('--maintainer', default=os.environ.get('PRIMULA_PACKAGER', 'Primula Docs <noreply@users.noreply.github.com>'),
                        help='Maintainer of the .deb and the name in the .rpm changelog (default: $PRIMULA_PACKAGER)')
    parser.add_argument('--sign', metavar='KEY', help='sign the .rpm with this GnuPG key (id, fingerprint or user id) from your keyring; '
                        'the public key is written next to the package as RPM-GPG-KEY-primula-docs.asc')
    parser.add_argument('--gpg-home', help='GnuPG home directory with the key (default ~/.gnupg)')
    args = parser.parse_args()

    package = args.package.resolve()
    info = json.loads((package / 'distribution.json').read_text(encoding='utf-8'))
    source = Path(__file__).resolve().parents[2]
    licence = args.licence or source / 'docs/github/LICENSES/Apache-2.0.txt'
    entries = collect(package, licence)
    glibc = minimal_glibc(package / 'libexec/primula-studio', str(info.get('libc', ['glibc', '2.34'])[1]))
    args.output.mkdir(parents=True, exist_ok=True)
    status = 0
    # `all` makes the formats of the family of this system; a format of another family is named explicitly.
    wanted = [fmt for fmt in ('deb', 'rpm') if args.format == fmt or args.format == 'all' and not family_warning(info, fmt)]
    for fmt in ('deb', 'rpm'):
        if args.format in (fmt, 'all') and family_warning(info, fmt):
            print(family_warning(info, fmt) + (' Skipped.' if fmt not in wanted else ''), file=sys.stderr)
    if 'deb' in wanted:
        print('deb:', make_deb(info, entries, args.output, glibc, args.maintainer, args.revision))
    if 'rpm' in wanted:
        try:
            rpm = make_rpm(info, entries, args.output, args.revision, args.maintainer)
            if args.sign:
                sign_rpm(rpm, args.sign, args.gpg_home)
                export_public_key(args.sign, args.gpg_home, args.output / 'RPM-GPG-KEY-primula-docs.asc')
            print('rpm:', rpm, '(signed with ' + args.sign + ')' if args.sign else '')
        except RuntimeError as exc:
            print(f'rpm: {exc}', file=sys.stderr)
            status = 1 if args.format == 'rpm' else 0
    return status


if __name__ == '__main__':
    sys.exit(main())
