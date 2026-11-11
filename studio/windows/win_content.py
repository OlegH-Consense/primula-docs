#!/usr/bin/env python3
"""Documents and examples of the Windows package (stage 23.6).

The Linux package gets them from ``studio/packaging/make_distribution.py``; the Windows one is
assembled by ``build-win.sh``, which calls this script with the source tree and the application
directory.  The same selection functions are used, so both packages hold the same examples,
libraries and author guide.  Standard library only.

Usage: win_content.py SOURCE_TREE APP_DIR
"""
import json
import sys
from pathlib import Path

LANGUAGES = ('en', 'uk', 'ru')


def main(source, output):
    sys.path.insert(0, str(source/'studio/packaging'))
    import make_distribution as md     # noqa: E402  (path set above)

    studio = source/'studio'
    for relative in md.example_files(source):
        md.copy_file(source/'examples'/relative, output/'examples'/relative)
    for entry in md.EXAMPLE_ENTRIES:
        if not (output/'examples'/entry).is_file():
            raise RuntimeError(f'The example entry {entry} is missing: update EXAMPLE_ENTRIES')
    (output/'examples'/'examples.json').write_text(
        json.dumps({'entries': list(md.EXAMPLE_ENTRIES)}, ensure_ascii=False, indent=1)+'\n', encoding='utf-8')
    for relative in md.library_files(source):
        md.copy_file(source/'libraries'/relative, output/'libraries'/relative)
    guide = source/'docs'/'author'
    for path in sorted([*guide.rglob('*.md'), *guide.rglob('*.pdf')]):
        relative = path.relative_to(guide)
        if relative.as_posix() not in ('README.md', 'translation-prompt.md'):
            md.copy_file(path, output/'guide'/relative)
    for language in LANGUAGES:
        md.copy_file(studio/f'help/studio-user-guide.{language}.md', output/f'STUDIO-GUIDE.{language}.md')
        md.copy_file(studio/f'help/primula-cheatsheet.{language}.pdf', output/f'primula-cheatsheet.{language}.pdf')


if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve())
