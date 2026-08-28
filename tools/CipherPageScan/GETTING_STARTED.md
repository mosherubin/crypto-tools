# Getting Started (for a new institution)

A step-by-step setup and usage guide for running Cipher Page Scan against
your own PDF archive. For the full technical reference — every option, the
output file formats, and exactly how detection works — see
[README.md](README.md) in this same folder. This document is the shorter
"how do I actually get this running" path.

## 1. Getting the software

The tool lives in a public GitHub repository:
**https://github.com/mosherubin/crypto-tools**

You don't need a GitHub account or git installed. On that page, click
**Code → Download ZIP**, and unzip it anywhere. You only need two folders
from inside it:

- `tools/CipherPageScan/` — the tool itself
- `tools/Library/` — code it depends on

(The rest of the repository is other, unrelated cryptanalysis tools — safe
to ignore or delete if you want a smaller copy.)

If you do have git, `git clone` works the same way and makes it easy to
pull future updates with `git pull`.

## 2. Installing prerequisites

You need three things: Python, Tesseract OCR, and three small Python
packages.

**Python** — version 3.9 or newer. Check with `python --version`
(or `python3 --version` on macOS/Linux). Get it from
[python.org](https://www.python.org/downloads/) if needed.

**Tesseract OCR** — the actual OCR engine, with the language pack(s) your
archive needs (Hebrew is *not* included by default and must be added
explicitly):

- **Windows**: install from the
  [UB Mannheim build](https://github.com/UB-Mannheim/tesseract/wiki) — during
  install, check the box for the Hebrew language pack (English is included
  by default). Let the installer add it to your `PATH` (note: the installer did not offer to add it to PATH; you may have to add it yourself).
- **macOS**: `brew install tesseract tesseract-lang` (the second package
  brings in all language packs, including Hebrew).
- **Linux (Debian/Ubuntu)**: `sudo apt install tesseract-ocr tesseract-ocr-heb`

Verify it worked:
```
tesseract --list-langs
```
You should see `heb` and `eng` in the list.

**Python packages**:
```
pip install pymupdf pytesseract pillow
```

## 3. Verify the install (recommended)

The tool ships with a self-contained test suite that generates its own tiny
test PDFs — no sample data needed, and it takes under a minute:
```
pip install pytest
pytest tools/CipherPageScan/tests -s
```
If all tests pass, your environment is set up correctly. If Tesseract or a
language pack is missing, the tool will tell you exactly what's wrong and
how to fix it the first time you run it for real (see step 4).

## 4. Running it: the four commands

All commands are run from a terminal, from inside the `CipherPageScan`
folder (or give the full path to `scan_pdf_for_ciphertext.py`). Every
command's `--help` gives the complete, current list of options:
```
python scan_pdf_for_ciphertext.py --help
python scan_pdf_for_ciphertext.py extract --help
```

The workflow, in order:

| Command | What it does | How often |
|---|---|---|
| `extract` | Scans PDFs (OCR where needed) and caches results. **This is the slow step.** | Once per batch of PDFs; safe to re-run — already-scanned PDFs are skipped automatically |
| `export` | Writes the report of flagged PDFs (or `--errors` for PDFs that failed to scan) | As often as you like — instant, reads only the cache |
| `detect` | Re-applies the matching rules with different sensitivity, without re-scanning | Only if you want to try a stricter/looser threshold |
| `forget` | Clears one or more PDFs from the cache, forcing a fresh re-scan next time | Rarely — only to force a redo of specific files |

A typical first run:
```
python scan_pdf_for_ciphertext.py extract --root D:\Scan --recursive D:\MyArchive
python scan_pdf_for_ciphertext.py export --root D:\Scan --output flagged.csv
python scan_pdf_for_ciphertext.py export --root D:\Scan --output errors.csv --errors
```

Notes:
- `--root` is a folder *you* choose (created automatically) that holds all
  the tool's own working data — nothing is written into your archive folder.
- `--recursive` scans subfolders too; without it, only PDFs directly inside
  the given folder are scanned.
- For a very large archive, `extract` can take a long time. It's safe to
  interrupt (Ctrl+C) and re-run later — it picks up where it left off.
- `--workers N` controls how many PDFs are processed in parallel (default:
  one less than your CPU's core count). More workers means faster scanning
  on a multi-core machine.

## 5. What to read

- **[README.md](README.md)** — the complete reference: every command-line
  option, the exact output file formats, and a plain-English explanation of
  how a page gets flagged (including its known limitations — worth reading
  so you know what kind of false positives to expect and why).
- `--help` on any command — always the most current and complete option list.

## 6. What comes out, and how to use it

- **`flagged.csv`** — the main deliverable. One row per PDF that may contain
  coded material, including the actual matched text (`matched_lines` column)
  right on the row — you can usually judge true vs. false positive by
  skimming this column alone, without opening a single PDF. Open the PDF at
  the listed page number to confirm.
- **`errors.csv`** — PDFs that failed to scan at all (corrupt, encrypted,
  unreadable format, ...). These were never actually checked for coded
  content and need separate attention (repair, manual inspection, or a
  password) rather than being treated as "clean."
- **`<root>/logs/*.output`** — one JSON file per PDF scanned, mirroring its
  original folder path, recording exactly when it was scanned and — for a
  flagged PDF — the specific matched lines. Useful for auditing a specific
  file without re-running anything.
- **`<root>/results.db`** — the tool's internal cache. You don't need to
  open or understand this; `export`/`detect` read it for you.

**Expect false positives, by design.** The tool deliberately favors
flagging more over missing genuine coded pages, and does not try to
understand *meaning* — only structure. Every flagged PDF should be reviewed
by a person before being treated as confirmed. README.md's "How detection
works" section explains exactly what triggers a flag and the one known
recurring false-positive pattern (ordinary prose that happens to look
grid-like), so reviewers know what to expect.
