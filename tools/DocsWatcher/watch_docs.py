"""Rebuild each Markdown page under a folder into HTML with pandoc whenever it is saved.

Usage: python tools/DocsWatcher/watch_docs.py [folder]
With no folder, every Markdown file under the current directory is watched.
"""
import argparse
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

CSS_FOLDER = Path(__file__).resolve().parents[2] / 'docs' / 'css'
STYLESHEETS = [CSS_FOLDER / 'site.css', CSS_FOLDER / 'document.css']
POLL_SECONDS = 0.5


def modification_times(folder):
    return {path: path.stat().st_mtime for path in folder.rglob('*.md')}


def stylesheet_options(markdown):
    # The HTML links the stylesheets by a path relative to its own folder, so pages work when served or opened locally.
    return [option for sheet in STYLESHEETS
            for option in ('--css', Path(os.path.relpath(sheet, markdown.parent)).as_posix())]


def table_of_contents_options(markdown):
    # Pandoc fills in the table of contents only with --toc; "toc: true" in the front matter alone leaves it empty.
    front_matter = markdown.read_text(encoding='utf-8').split('\n---', 1)[0]
    return ['--toc'] if 'toc: true' in front_matter.splitlines() else []


def build(markdown, folder):
    html = markdown.with_suffix('.html')
    result = subprocess.run(['pandoc', '-s', markdown.name, '-o', html.name,
                             *table_of_contents_options(markdown), *stylesheet_options(markdown)],
                            cwd=markdown.parent, capture_output=True, text=True)
    stamp = time.strftime('%H:%M:%S')
    if result.returncode != 0:
        print(f'{stamp}  pandoc FAILED on {markdown.relative_to(folder).as_posix()}:\n{result.stderr.strip()}')
        return
    print(f'{stamp}  rebuilt {html.relative_to(folder).as_posix()}')
    if result.stderr.strip():
        print(result.stderr.strip())


def main():
    parser = argparse.ArgumentParser(description='Rebuild Markdown pages into HTML with pandoc whenever they are saved.')
    parser.add_argument('folder', nargs='?', default='.',
                        help='folder to watch, including its subfolders (default: the current directory)')
    folder = Path(parser.parse_args().folder).resolve()
    if not folder.is_dir():
        sys.exit(f'{folder} is not a folder')
    if shutil.which('pandoc') is None:
        sys.exit('pandoc was not found on the PATH; install it from https://pandoc.org/installing.html')
    seen = modification_times(folder)
    print(f'Watching {len(seen)} Markdown files under {folder}')
    print('Save a .md file to rebuild its .html. Press Ctrl+C to stop.')
    try:
        while True:
            time.sleep(POLL_SECONDS)
            current = modification_times(folder)
            for markdown, modified in current.items():
                if seen.get(markdown) != modified:
                    build(markdown, folder)
            seen = current
    except KeyboardInterrupt:
        print('Stopped.')


if __name__ == '__main__':
    main()
