"""
Pre-commit hook: regenerates tools/CryptML/input/index.json whenever a
.cryptml file is among the staged changes, and stages the manifest into
the same commit.

Trigger: any staged file under tools/CryptML/input/
Action:  node generate-manifest.js  ->  git add the regenerated manifest
         into this commit.

If a staged .cryptml file fails validation, the commit is blocked with the
errors printed -- same purpose as tools/Stethoscope's hook, just for
CryptML. If Node.js isn't installed locally, this is a warning, not a
blocker: the GitHub Action (.github/workflows/cryptml-manifest.yml) is the
safety net for anyone -- including external contributors -- without Node
or this hook installed.
"""
import subprocess
import sys
import os
import shutil


def repo_root() -> str:
    r = subprocess.run(['git', 'rev-parse', '--show-toplevel'],
                       capture_output=True, text=True)
    return r.stdout.strip()


ROOT = repo_root()
INPUT_DIR_PREFIXES = ('tools/CryptML/input/', 'tools\\CryptML\\input\\')
GENERATE_SCRIPT = os.path.join(ROOT, 'tools', 'CryptML', 'generate-manifest.js')
MANIFEST_FILE = os.path.join(ROOT, 'tools', 'CryptML', 'input', 'index.json')


def staged_files():
    r = subprocess.run(['git', 'diff', '--cached', '--name-only'],
                       capture_output=True, text=True, cwd=ROOT)
    return r.stdout.splitlines()


def is_cryptml_commit(files):
    return any(f.startswith(p) for f in files for p in INPUT_DIR_PREFIXES)


def main():
    files = staged_files()
    if not is_cryptml_commit(files):
        sys.exit(0)

    if shutil.which('node') is None:
        print('[cryptml] WARNING: Node.js not found -- skipping manifest '
              'regeneration for this commit. The GitHub Action will catch '
              'a stale or invalid manifest on push.', file=sys.stderr)
        sys.exit(0)

    result = subprocess.run(['node', GENERATE_SCRIPT], cwd=ROOT,
                            capture_output=True, text=True)
    print(result.stdout, end='')
    if result.returncode != 0:
        print(result.stderr, end='', file=sys.stderr)
        print('[cryptml] Commit blocked: a staged .cryptml file failed validation.',
              file=sys.stderr)
        sys.exit(1)

    subprocess.run(['git', 'add', MANIFEST_FILE], cwd=ROOT)
    sys.exit(0)


if __name__ == '__main__':
    main()
