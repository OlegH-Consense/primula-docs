#!/usr/bin/env python3
"""Assemble the native Linux runtime package of Primula Docs: the translator (as a
Python package with launcher) and Primula Studio (the built binary), with manuals,
examples, an installer and a manifest (stage 14.11). Standard library only.

The package is built on the target distribution: Studio links to the system Qt,
nothing of the system is bundled. The translator needs Python 3.11+ and PyYAML.

Layout of the package directory:
  README*.md, STUDIO-GUIDE.*.md, primula-spec-v1.1-draft.<lang>.md, primula-stdlib-v1.1-draft.<lang>.md,
  primula-cheatsheet.<lang>.pdf, examples/, guide/    manuals, examples, the author guide
  install.sh, uninstall.sh, check-dependencies.sh, runtime/  installation
  bin/primula, bin/primula-view, bin/primula-studio  launchers
  libexec/primula-studio                       the Studio binary
  lib/python/primula/                          the translator package
  share/primula-studio/{translations,help}/, share/icons/…, share/applications/…
  distribution.json, MANIFEST.sha256
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import tarfile
import tempfile

LANGUAGES = ('en', 'ru', 'uk')


def os_release():
    result = {}
    path = Path('/etc/os-release')
    if path.is_file():
        for line in path.read_text().splitlines():
            if '=' in line:
                key, value = line.split('=', 1)
                result[key] = value.strip('"\'')
    return result


def project_version(source):
    """The version of pyproject.toml; Studio has the same one (studio/CMakeLists.txt reads it)."""
    return re.search(r'^version = "([^"]+)"', (source/'pyproject.toml').read_text(), re.M)[1]


def copy_file(source, target, executable=False):
    if not source.is_file():
        raise RuntimeError(f'Required file is missing: {source}')
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    if executable:
        target.chmod(0o755)


def translator_files(source):
    """Files of the translator package: sources and data, without caches."""
    root = source/'src/primula'
    for path in sorted(root.rglob('*')):
        if path.is_file() and '__pycache__' not in path.parts and path.suffix not in ('.pyc', '.pyo'):
            yield path.relative_to(root)


#: The entry documents of the examples, in the order of examples/README.md: Studio lists
#: them under "Recent projects" after the first installation (С1).
EXAMPLE_ENTRIES = ('01-basics/basics.prml', '02-contract/contract.prml', '03-manual/manual.prml',
                   '04-errors/syntax.prml', '05-loan/loan.prml', '06-safety/safety.prml',
                   '07-project/project.p.prml', '08-styles/business.prml', '09-parallel/agreement.prml',
                   '10-code/code.prml', '11-library/project/рахунок.prml', '12-payment-qr/рахунок.prml')


def example_files(source):
    """The examples without their build results (out/) and the source-tree runner.

    Symbolic links of the examples (``lib`` of examples 11 and 12, decision 136) are
    followed: the package holds copies of the linked libraries, so the examples build
    after installation without the links (the manifest admits regular files only).
    """
    root = source/'examples'
    found = []
    for directory, subdirectories, names in os.walk(root, followlinks=True):
        subdirectories.sort()
        for name in names:
            path = Path(directory)/name
            relative = path.relative_to(root)
            if relative.parts[0] == 'out' or 'out' in relative.parts[1:2]:
                continue
            if relative.name in ('.gitignore', 'run.sh') or '__pycache__' in relative.parts:
                continue
            if path.is_file():
                found.append(relative)
    return sorted(found)


def library_files(source):
    """The libraries of modules (``libraries/``, stage 18.3) as they are in the source tree."""
    root = source/'libraries'
    for path in sorted(root.rglob('*')) if root.is_dir() else []:
        relative = path.relative_to(root)
        # Not shipped: caches, the results of the demo builds (demo/build/) and the state file of the library work.
        if path.is_file() and '__pycache__' not in path.parts and 'build' not in relative.parts \
                and relative.name != 'CHECKPOINT.md':
            yield relative


def editor_files(source):
    """The highlighting for editors (``editors/``, stage 20.1): the definitions and the installer, not the generators and checks."""
    root = source/'editors'
    for name in ('README.md', 'install.sh'):
        yield Path(name)
    for folder in ('kate', 'mcedit', 'geany', 'vscode'):
        for path in sorted((root/folder).rglob('*')):
            if path.is_file() and '__pycache__' not in path.parts:
                yield path.relative_to(root)


def assemble(source, build, output):
    version = project_version(source)
    binary = build/'primula-studio'
    info = json.loads(subprocess.check_output([str(binary), '--runtime-info'], text=True))
    if info['studio_version'] != version:
        raise RuntimeError(f'The Studio binary is {info["studio_version"]}, the source is {version}. Rebuild Studio first.')
    osinfo = os_release()
    studio = source/'studio'
    packaging = studio/'packaging'

    # The translator.
    for relative in translator_files(source):
        copy_file(source/'src/primula'/relative, output/'lib/python/primula'/relative)
    copy_file(packaging/'primula', output/'bin/primula', executable=True)
    copy_file(packaging/'primula-view', output/'bin/primula-view', executable=True)
    # Primula Studio.
    copy_file(binary, output/'libexec/primula-studio', executable=True)
    copy_file(packaging/'primula-studio', output/'bin/primula-studio', executable=True)
    for language in ('ru', 'uk'):
        copy_file(build/f'translations/primula_studio_{language}.qm',
                  output/f'share/primula-studio/translations/primula_studio_{language}.qm')
    for language in LANGUAGES:
        copy_file(studio/f'help/studio-user-guide.{language}.md', output/f'share/primula-studio/help/studio-user-guide.{language}.md')
    for cheatsheet in ('primula-cheatsheet.ru.pdf', 'primula-cheatsheet.uk.pdf', 'primula-cheatsheet.en.pdf'):
        copy_file(studio/'help'/cheatsheet, output/'share/primula-studio/help'/cheatsheet)
    # File types (С2): the built-in ones (also compiled into Studio) and the template of the user file.
    copy_file(studio/'resources/file-types.json', output/'share/primula-studio/file-types.json')
    copy_file(studio/'resources/file-types.user.json', output/'share/primula-studio/file-types.example.json')
    copy_file(studio/'resources/primula-studio.svg', output/'share/icons/hicolor/scalable/apps/primula-studio.svg')
    copy_file(studio/'resources/org.primula_docs.Studio.desktop', output/'share/applications/org.primula_docs.Studio.desktop')
    # Manuals and examples at the top, where the user looks first.
    copy_file(packaging/'docs/README.en.md', output/'README.md')
    for language in LANGUAGES:
        copy_file(packaging/f'docs/README.{language}.md', output/f'README.{language}.md')
        copy_file(studio/f'help/studio-user-guide.{language}.md', output/f'STUDIO-GUIDE.{language}.md')
    # The specification and the standard library: the Russian originals and their translations.
    for language in LANGUAGES:
        for name in (f'primula-spec-v1.1-draft.{language}.md', f'primula-stdlib-v1.1-draft.{language}.md'):
            copy_file(source/name, output/name)
    for cheatsheet in ('primula-cheatsheet.ru.pdf', 'primula-cheatsheet.uk.pdf', 'primula-cheatsheet.en.pdf'):
        copy_file(studio/'help'/cheatsheet, output/cheatsheet)
    for relative in example_files(source):
        copy_file(source/'examples'/relative, output/'examples'/relative)
    for entry in EXAMPLE_ENTRIES:
        if not (output/'examples'/entry).is_file():
            raise RuntimeError(f'The example entry {entry} is missing: update EXAMPLE_ENTRIES')
    (output/'examples'/'examples.json').write_text(
        json.dumps({'entries': list(EXAMPLE_ENTRIES)}, ensure_ascii=False, indent=1)+'\n', encoding='utf-8')
    for relative in editor_files(source):
        copy_file(source/'editors'/relative, output/'editors'/relative, executable=relative.name == 'install.sh')
    for relative in library_files(source):
        copy_file(source/'libraries'/relative, output/'libraries'/relative)
    # The author guide (stage 15.4-15.5): ru/ (source), uk/, en/ with the same layout, generated
    # appendices, the glossary and the PDF of each language (tools/author_docs.py pdf; Help → Author
    # guide in Studio); the rules for its maintainers, the translation prompt and the records of the
    # sources of the PDF (*.pdf.sources) stay out.
    guide = source/'docs'/'author'
    for path in sorted([*guide.rglob('*.md'), *guide.rglob('*.pdf')]):
        relative = path.relative_to(guide)
        if relative.as_posix() not in ('README.md', 'translation-prompt.md'):
            copy_file(path, output/'guide'/relative)
    # Installation.
    for name in ('install.sh', 'uninstall.sh', 'check-dependencies.sh'):
        copy_file(packaging/name, output/name, executable=True)
    for name in ('install.py', 'dependencies.py'):
        copy_file(packaging/'runtime'/name, output/'runtime'/name)
    # Exact build platform: a record of where it was built, not a portability claim.
    metadata = {'format': 2, 'version': version, 'studio_version': info['studio_version'],
                'architecture': platform.machine(), 'os_id': osinfo.get('ID', 'linux'),
                'os_version': osinfo.get('VERSION_ID', ''), 'os_name': osinfo.get('PRETTY_NAME', ''),
                'qt_build': info['qt_build'], 'libc': list(platform.libc_ver()),
                'system_libraries_bundled': False, 'python_minimum': '3.11'}
    (output/'distribution.json').write_text(json.dumps(metadata, indent=2, ensure_ascii=False)+'\n')
    manifest = []
    for path in sorted(output.rglob('*')):
        if path.is_file():
            manifest.append(hashlib.sha256(path.read_bytes()).hexdigest()+'  '+path.relative_to(output).as_posix())
    (output/'MANIFEST.sha256').write_text('\n'.join(manifest)+'\n')
    return metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--source', type=Path, required=True, help='the source tree (with pyproject.toml)')
    parser.add_argument('--build-dir', type=Path, required=True, help='the Studio build directory')
    parser.add_argument('--output', type=Path, help='the package directory (default dist/primula-docs-VERSION-DISTRO-ARCH)')
    parser.add_argument('--archive', action='store_true', help='also make DIRECTORY.tar.gz')
    args = parser.parse_args()
    source, build = args.source.resolve(), args.build_dir.resolve()
    osinfo = os_release()
    distro = re.sub(r'[^a-zA-Z0-9_.-]', '-', osinfo.get('ID', 'linux') + osinfo.get('VERSION_ID', ''))
    name = f'primula-docs-{project_version(source)}-{distro}-{platform.machine()}'
    output = (args.output or source/'dist'/name).resolve()
    if output.exists():
        raise SystemExit(f'Refusing to overwrite an existing directory: {output}')
    archive = output.with_name(output.name+'.tar.gz')
    if args.archive and archive.exists():
        raise SystemExit(f'Refusing to overwrite an existing archive: {archive}')
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.primula-distribution-', dir=output.parent) as temporary:
        staged = Path(temporary)/output.name
        staged.mkdir()
        metadata = assemble(source, build, staged)
        staged.rename(output)
    if args.archive:
        try:
            with tarfile.open(archive, 'x:gz') as tar:
                tar.add(output, arcname=output.name)
        except BaseException:
            archive.unlink(missing_ok=True)
            raise
    print(f'Package: {output}')
    if args.archive:
        print(f'Archive: {archive}')
    print(f'Built for {metadata["os_name"]}, {metadata["architecture"]}, Qt {metadata["qt_build"]}; '
          'the system provides the shared libraries.')


if __name__ == '__main__':
    main()
