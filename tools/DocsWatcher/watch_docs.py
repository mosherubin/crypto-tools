"""Rebuild each Markdown page under docs/ into HTML with pandoc whenever it is saved.

Run from anywhere: python tools/DocsWatcher/watch_docs.py
"""
import shutil
import subprocess
import sys
import time
from pathlib import Path

DOCS = Path(__file__).resolve().parents[2] / 'docs'
POLL_SECONDS = 0.5
# Every Markdown page lives one folder below docs/, so the stylesheets are one level up.
STYLESHEETS = ['../css/site.css', '../css/document.css']


def modification_times():
    return {path: path.stat().st_mtime for path in DOCS.rglob('*.md')}


def build(markdown):
    html = markdown.with_suffix('.html')
    stylesheet_options = [option for sheet in STYLESHEETS for option in ('--css', sheet)]
    result = subprocess.run(['pandoc', '-s', markdown.name, '-o', html.name, *stylesheet_options],
                            cwd=markdown.parent, capture_output=True, text=True)
    stamp = time.strftime('%H:%M:%S')
    if result.returncode != 0:
        print(f'{stamp}  pandoc FAILED on {markdown.relative_to(DOCS).as_posix()}:\n{result.stderr.strip()}')
        return
    print(f'{stamp}  rebuilt {html.relative_to(DOCS).as_posix()}')
    if result.stderr.strip():
        print(result.stderr.strip())


def main():
    if shutil.which('pandoc') is None:
        sys.exit('pandoc was not found on the PATH; install it from https://pandoc.org/installing.html')
    seen = modification_times()
    print(f'Watching {len(seen)} Markdown files under {DOCS}')
    print('Save a .md file to rebuild its .html. Press Ctrl+C to stop.')
    try:
        while True:
            time.sleep(POLL_SECONDS)
            current = modification_times()
            for markdown, modified in current.items():
                if seen.get(markdown) != modified:
                    build(markdown)
            seen = current
    except KeyboardInterrupt:
        print('Stopped.')


if __name__ == '__main__':
    main()
