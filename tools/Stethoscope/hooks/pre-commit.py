"""
Pre-commit hook: auto-increments the STETHOSCOPE minor version whenever
stethoscope files are among the staged changes.

Trigger: any staged file under tools/Stethoscope/ or docs/stethoscope.html
Action:  VERSION minor += 1  →  patch (version OLD) → (version NEW) in all
         listed PATCHED_FILES  →  git add those files into the same commit.
"""
import subprocess
import sys
import os


def repo_root() -> str:
    r = subprocess.run(['git', 'rev-parse', '--show-toplevel'],
                       capture_output=True, text=True)
    return r.stdout.strip()


ROOT = repo_root()
VERSION_FILE = os.path.join(ROOT, 'tools', 'Stethoscope', 'VERSION')
PATCHED_FILES = [
    os.path.join(ROOT, 'docs', 'stethoscope.html'),
    os.path.join(ROOT, 'tools', 'Stethoscope', 'Basic', 'server.py'),
]

STETHOSCOPE_PATHS = ('tools/Stethoscope', 'tools\\Stethoscope',
                     'docs/stethoscope.html', 'docs\\stethoscope.html')


def staged_files():
    r = subprocess.run(['git', 'diff', '--cached', '--name-only'],
                       capture_output=True, text=True, cwd=ROOT)
    return r.stdout.splitlines()


def is_stethoscope_commit(files):
    return any(
        any(f.startswith(p) or f == p.lstrip('tools/').lstrip('tools\\')
            for p in STETHOSCOPE_PATHS)
        for f in files
    )


def bump(version: str) -> str:
    parts = version.split('.')
    parts[-1] = str(int(parts[-1]) + 1)
    return '.'.join(parts)


def patch_file(path: str, old_ver: str, new_ver: str) -> bool:
    with open(path, encoding='utf-8') as f:
        text = f.read()
    updated = text.replace(f'(version {old_ver})', f'(version {new_ver})')
    if updated == text:
        print(f'  WARNING: "(version {old_ver})" not found in {os.path.basename(path)}',
              file=sys.stderr)
        return False
    with open(path, 'w', encoding='utf-8') as f:
        f.write(updated)
    return True


def main():
    files = staged_files()
    if not is_stethoscope_commit(files):
        sys.exit(0)

    with open(VERSION_FILE, encoding='utf-8') as f:
        old_ver = f.read().strip()
    new_ver = bump(old_ver)

    print(f'[stethoscope] version {old_ver} -> {new_ver}')

    with open(VERSION_FILE, 'w', encoding='utf-8') as f:
        f.write(new_ver + '\n')

    to_stage = [VERSION_FILE]
    for path in PATCHED_FILES:
        if patch_file(path, old_ver, new_ver):
            to_stage.append(path)

    subprocess.run(['git', 'add'] + to_stage, cwd=ROOT)
    sys.exit(0)


if __name__ == '__main__':
    main()
