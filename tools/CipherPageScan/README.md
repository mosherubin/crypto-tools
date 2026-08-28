# Cipher Page Scan

Scans large PDF archives for pages that may contain enciphered/encoded
messages, flagged by the presence of multiple consecutive 5-character groups
on a line (any script — Latin, digits, Hebrew, ...). Built for triaging
archives too large to review page by page by hand.

# Requirements

- `pip install pymupdf pytesseract pillow`
- [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki) installed and on `PATH` (or set `TESSERACT_CMD` to the full path of `tesseract.exe`), with the language packs you need — Hebrew is not included by default and must be added explicitly during install or by dropping `heb.traineddata` into Tesseract's `tessdata` directory.

# Root folder

Every subcommand takes `--root <dir>`, which owns everything the tool
produces (created if missing):

```
<root>/
  results.db         SQLite cache: extracted/OCR'd page text, per-PDF status
  logs/               One JSON *.output log per PDF scanned, mirroring its
    D/Archive/          source path -- e.g. D:\Archive\Batch1\0001.pdf scans
      Batch1/           to <root>/logs/D/Archive/Batch1/0001.pdf.output
        0001.pdf.output
```

Each `*.output` file records start/end time, status, and, per flagged page,
every matched line's index, run length, and actual text -- the specific
tokens that triggered the match, not just the page number:

```json
{
  "pdf_path": "...", "start_time": "...", "end_time": "...",
  "duration_seconds": 4.9, "status": "done", "stopped_early": true,
  "pages_scanned": 43,
  "matched_pages": [
    {
      "page_num": 43,
      "matched_lines": [
        {"line_index": 3, "run": 5, "text": "..."},
        {"line_index": 4, "run": 5, "text": "..."}
      ]
    }
  ],
  "error_message": null
}
```

# Specifying input PDFs

Inputs can be given as positional arguments and/or listed one per line in a
`--from-file` text file (blank lines and lines starting with `#` are
ignored; `--from-file` is repeatable). Each entry may be:

- a single PDF file
- a directory — every `*.pdf` directly inside it (add `--recursive` to also
  descend into its subfolders)
- a glob pattern in the *filename* part only, e.g. `D:\Archive\Batch1\0b07*.pdf`
  (`--recursive` applies the pattern to matching files in subfolders too;
  wildcards in the directory part of a spec are rejected, not silently
  ignored)

```
> type batch1.txt
# Everything from the January intake
D:\Archive\Batch1\0b07*.pdf
D:\Archive\Batch1-Rescans

> python scan_pdf_for_ciphertext.py extract --root D:\Scan --from-file batch1.txt --recursive
3214 PDF(s) matched, 3214 pending (0 already cached and unchanged)
[1/3214] D:\Archive\Batch1\0001.pdf: FLAGGED pages [4] (4 pages scanned)
[2/3214] D:\Archive\Batch1\0002.pdf: clean (11 pages scanned)
...
```

# Quick start

Extraction (OCR where needed) and detection are separate passes so that
re-tuning `--min-groups` never requires re-OCRing the archive.

By default, `extract` stops scanning a PDF's remaining pages as soon as one
page is flagged (its purpose is finding *which PDFs* may contain coded
messages, not cataloguing every such page). Pass `--exhaustive` to force a
complete page-by-page scan of every PDF instead.

`--dpi` (default 300) controls the resolution OCR renders each page at
before recognizing it. Higher DPI costs more time and memory per page but
can meaningfully improve accuracy on poor-quality scans -- e.g. a printed
form whose ruled table/cell borders bleed into adjacent digits at 300 DPI
may separate cleanly at 450-600. Worth raising for a specific troublesome
batch, not as a blanket default given the extra cost across a whole archive.

Re-run detection with a different threshold without touching OCR:

```
> python scan_pdf_for_ciphertext.py detect --root D:\Scan --min-groups 4
Re-evaluated 3214 cached PDF(s) with min_groups=4, min_lines=1, min_purity=0.7
```

Note: a PDF that was stopped early under the *original* (stricter) threshold
may have unscanned pages that a *looser* threshold would have caught —
`detect` only re-evaluates what's already cached. Re-run `extract` for those
specific PDFs to backfill them.

`extract` skips a PDF entirely once it's cached and unchanged on disk — that's
what makes interrupted archive runs resumable. To deliberately force a
specific PDF to be re-scanned from scratch (e.g. after a code or threshold
change you want fully re-applied, not just re-evaluated via `detect`), clear
its cached result first:

```
> python scan_pdf_for_ciphertext.py forget --root D:\Scan D:\Archive\Batch1\0001.pdf
Forgot 1/1 PDF(s). They will be re-scanned on the next extract.
```

This deletes the PDF's row from `results.db` and its stale `.output` log, if
one exists. `forget` accepts the same inputs as `extract` -- files,
directories, glob patterns, `--from-file`, `--recursive` -- so a whole
folder can be forgotten at once.

Produce the report for review:

```
> python scan_pdf_for_ciphertext.py export --root D:\Scan --output flagged.csv
187 PDF(s) flagged. Report written to flagged.csv
```

`flagged.csv` includes the actual matched line text (`matched_lines` column,
`p<page>: <text>` per match, `|`-separated) right on each PDF's row -- with
hundreds or thousands of hits, this lets you skim the CSV itself and spot
genuine-looking coded groups vs. likely false positives before opening a
single PDF. If you're reporting from a `results.db` created before this
column existed, run `detect` once first (no re-OCR needed) to backfill it
from the page text that's already cached.

`export` reports flagged PDFs by default -- your hit list. A PDF that failed
during `extract` (corrupt file, encrypted, unsupported format, ...) never
successfully scanned at all, which is a different concern from "scanned and
found clean," and doesn't appear in that hit list either way. Pass `--errors`
to report those instead:

```
> python scan_pdf_for_ciphertext.py export --root D:\Scan --output errors.csv --errors
3 PDF(s) failed to scan. Report written to errors.csv
```

# How detection works

Two lengths matter for a token:
- **group-shaped**: length within 1 of 5 (i.e. 4-6 characters), regardless of
  exact content. OCR/handwriting noise routinely corrupts a character or
  drops/adds one without changing a group's column width, so this tolerant
  test is what both the run-length count and purity use.
- **strict group**: exactly 5 characters and fully alphanumeric
  (`str.isalnum()`, Unicode-aware — Latin, digits, and Hebrew all qualify
  with no special-casing).

A line *qualifies* when:
1. it contains a run of consecutive group-shaped tokens of at least
   `--min-groups` (default 3), **where at least half the tokens in that run
   are strict groups** — tolerating one OCR-corrupted token inside an
   otherwise-real run, without also matching a short run of ordinary words
   that merely happen to be medium-length (see below); and
2. at least `--min-purity` (default 0.7) fraction of *all* tokens on the
   line are group-shaped.

A qualifying line only counts as an actual **match** if an immediately
adjacent line (the one directly before or after it) also independently
qualifies. A genuine coded dispatch runs across multiple consecutive lines;
a single isolated qualifying line — however it arose — is treated as noise
rather than evidence on its own. This means a real one-line-only dispatch
would be missed, but that's a deliberate trade-off: with an estimated 99.9%
of a large archive containing no coded material at all, minimizing false
positives across that overwhelming majority matters more than the rare case
of a single-line dispatch whose PDF contains no other coded page to catch it.

A page is flagged once it has `--min-lines` (default 1) matched lines. This
is a pure structural pattern match — no dictionary or per-word frequency
filtering — by design, since the curator would rather review a false
positive than miss a genuine coded page. Text extraction uses Tesseract PSM
6 ("assume a single uniform block of text"): Tesseract's own default (PSM 3,
automatic layout detection) fragments grid/table-formatted group text into
one word per detected line on many real archive pages, since it tries to
infer columns/paragraphs. Reconstructed OCR text also has Unicode format
characters (category Cf — notably the bidi control marks Tesseract inserts
into RTL-script output) stripped before matching, since they're invisible
but otherwise inflate a token's apparent length.

**Known limitation**: ordinary Hebrew prose can occasionally *qualify*,
because Hebrew word lengths cluster tightly around 4-6 characters — unlike
English/Spanish, where short function words and long words dilute a line's
purity, a genuine Hebrew sentence can have a majority of exactly-5-letter
real words. The adjacency requirement above eliminated every known instance
of this in testing (a qualifying sentence essentially never has an
independently-qualifying neighboring line too), but it's a structural
ambiguity a dictionary-free approach can't rule out entirely, just make
very rare. Accepted as a trade-off, not treated as a bug, consistent with
the project's explicit choice of pattern matching over dictionary/statistical
filtering.

# Tests

`tests/fixtures/generate_fixtures.py` synthesizes small PDFs into
`should_flag/` and `should_not_flag/` at the start of every run — nothing
binary is committed to the repo (see that directory's README). Each fixture
targets a specific detection behavior found against real archive scans
during development (grid/table OCR segmentation, bidi-mark stripping,
strict-majority runs, line adjacency, Hebrew-prose false positives); the
full suite runs in well under a minute. Pass `-s` to see each page as it's
scanned (useful if you point the suite at real archival PDFs locally, which
can take far longer per page):

```
pytest tools/CipherPageScan/tests -s
```
