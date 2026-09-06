# Columnar Transposition Hill-Climbing Solver

A ciphertext-only attack on the columnar transposition cipher, based on the
hill-climbing methodology in George Lasry's thesis (Chapter 5, "Case Study —
The Columnar Transposition Cipher"). Two scripts:

- **`build_hebrew_quadgrams.py`** — builds a quadgram frequency table from a
  text corpus (plain text or a raw MediaWiki XML export).
- **`solve_columnar.py`** — recovers the transposition key and plaintext from
  a ciphertext, given that frequency table.

Both are alphabet-agnostic in principle, but the corpus builder currently
targets Hebrew specifically (final-letter normalization to a 22-letter
alphabet). The solver works for any language whose alphabet is defined by the
quadgram file you give it.

## Requirements

```
pip install numpy mwparserfromhell
```

NumPy is required by the solver (vectorized decrypt/score). `mwparserfromhell`
is only needed if you're building a quadgram file from a MediaWiki XML export.

## 1. Building a quadgram frequency file

```
python build_hebrew_quadgrams.py <output_file> <corpus_file> [<corpus_file> ...]
    [--heartbeat MB]
```

| Argument | Meaning |
|---|---|
| `output_file` | Where to write the quadgram count file. |
| `corpus_file` (1 or more) | UTF-8 corpus files. Plain text, or a MediaWiki XML export (detected by a `.xml` extension). |
| `--heartbeat MB` | Print progress every `MB` megabytes read, per file. `0` disables it. Default `100`. |

### Plain text corpora

Every character that isn't a Hebrew letter (spaces, punctuation, digits,
niqqud, other scripts) is discarded. Final-form letters (ך ם ן ף ץ) are
folded to their base letter, the same normalization the solver applies to
ciphertext, so the two always share one alphabet. Lines whose first
non-blank character is `#` are treated as comments and skipped entirely —
useful for annotating a corpus of individual messages, e.g.:

```
# message 123/50
מציע שתודיע לשרתוק דברי הקונסול...
```

### MediaWiki XML corpora (e.g. a Wikipedia dump)

Only the wikitext inside `<page><revision><text>` is considered — article
titles, `<siteinfo>`, and namespace declarations are never touched, since
none of that is the article author's prose. Within the article text:

- File/Image/Category/Template links (e.g.
  `[[File:x.png|thumb|300px|caption]]`) are removed entirely, including any
  nested links inside them — their pipe-separated parameters (size,
  alignment, etc.) aren't prose, and a generic wikitext parser doesn't know
  to treat them specially.
- Everything else is run through `mwparserfromhell` to strip `[[links]]`
  (resolved to their display text), `{{templates}}`, `'''formatting'''`,
  tables, and HTML comments down to plain prose.

Both file types are streamed rather than loaded whole into memory, so
multi-gigabyte corpora (a full Wikipedia dump is several GB) are safe to feed
in directly. Quadgrams never span the boundary between two files, nor — for
XML files — between two different `<page>` elements, since unrelated
documents or articles becoming artificially adjacent would fabricate letter
sequences nobody ever actually wrote.

### Output format

One quadgram per line, tab-separated from its occurrence count, sorted most
common first:

```
ולהם	4213
אשרי	891
```

### Diagnostics

After processing, the script reports how well-supported the resulting table
is — worth checking before trusting it for a solve:

```
Theoretical quadgram space: 234256 (22-letter alphabet)
Coverage: 228726 / 234256 (97.6%)
Average occurrences per unique quadgram: 5142.37
Occurrence distribution:
  seen exactly once        4029 (1.8%)
  seen 2-4 times           8326 (3.6%)
  seen 5-9 times           8681 (3.8%)
  seen 10+ times         207690 (90.8%)
```

Coverage near the full theoretical space, and a low percentage of
"seen exactly once" entries, both indicate the table is well-supported
rather than relying heavily on the floor value for unseen quadgrams. A
corpus of a few hundred thousand letters (e.g. one small book) is enough to
get started, but a large corpus (Wikipedia-scale, hundreds of millions of
letters) gives much sharper discrimination — see the example above, built
from Hebrew Wikipedia.

## 2. Solving a ciphertext

```
python solve_columnar.py <ciphertext_file> <min_key_length> <max_key_length> <quadgram_file>
    [--restarts N] [--seed N] [--verbose] [--heartbeat N]
    [--try-bisection] [--try-reversal] [--top-n N] [--rtl]
```

| Argument | Meaning |
|---|---|
| `ciphertext_file` | Plain text file (whitespace ignored); every other character must appear in the quadgram file's alphabet. Final-form Hebrew letters are normalized automatically. |
| `min_key_length`, `max_key_length` | Every key length in this inclusive range is tried. Pass the same value twice to check a single length. |
| `quadgram_file` | The frequency table from step 1. |
| `--restarts N` | Random restarts of hill climbing per key length. Default `50`. |
| `--seed N` | Seed the random number generator, for reproducible runs. Default unset (random each run). |
| `--verbose` | Print every new best result as restarts progress, not just the final one per key length. |
| `--heartbeat N` | Print progress every `N` restarts (e.g. `restart 15/50, best score so far: -412.30`). `0` disables it. Default `5`. |
| `--try-bisection` | Also test the ciphertext split into two halves with their order swapped — covers a message transmitted in two swapped blocks. For an odd length, both conventions for which half gets the extra character are tried. |
| `--try-reversal` | Also test the ciphertext reversed end-to-end. |
| `--top-n N` | Track the `N` best-scoring results seen across the *entire* run (every variant, every key length), printed together at the end, best first. `0` disables it. Default `10`. |
| `--rtl` | Right-to-left language: printed keys are shown in reverse order, to match reading columns right-to-left. Decryption itself is unaffected — this is a display convention only. |

### How a run is structured

The solver always tries the ciphertext as given ("as-is"). If
`--try-bisection` and/or `--try-reversal` are set, it also tries every
combination of the enabled transforms (as-is, bisected, reversed,
bisected-then-reversed), each treated as an independent ciphertext to sweep
across the full key-length range. This is meant to catch simple procedural
tricks — a message sent in two swapped halves, or reversed — before
concluding the ciphertext needs a structurally different transposition
variant (e.g. double transposition) to solve at all.

For each ciphertext variant and each key length, the solver runs
`--restarts` independent hill-climbing searches (random initial key,
climbing via segment slide and segment swap transformations to a local
maximum — see [Background](#background) below) and reports the best key and
plaintext found for that combination.

### The top-N leaderboard

Every single restart's result — not just the best-per-key-length — is a
candidate for the top-N leaderboard, deduplicated by
`(variant, key length, key)` so that many restarts independently converging
on the same correct answer don't crowd out genuinely distinct near-misses.
This is most useful when nothing fully solves: it surfaces the most
promising partial results across the whole sweep, e.g.:

```
======================================================================
=========================== TOP 5 RESULTS ===========================
======================================================================
#1  score=-13.58  variant=as-is  key_length=9  key=(9, 3, 7, 2, 8, 6, 5, 1, 4)
    CRIEDTHEBANKERWITHANASHENFACEIWILLTELLYOUTHEN...

#2  score=-16.56  variant=as-is  key_length=9  key=(8, 6, 5, 1, 4, 2, 3, 7, 9)
    DTHEBERIARWITHENKAHENFASNACILLTEWEILUTHENOLYW...
```

### Scoring

Candidates are scored by (negative) cross entropy of their quadgrams against
the reference frequency table — the mean, not the sum, of each quadgram's
log2-probability. Averaging rather than summing matters because it makes
scores comparable across candidates of *different lengths*; a raw sum would
be biased toward shorter candidates purely because they have fewer terms,
regardless of how language-like they actually are. That doesn't affect hill
climbing over keys alone (ciphertext length never changes during one
search), but it will matter for any future length-changing perturbation of
the ciphertext (e.g. insert/delete restarts, to compensate for transcription
errors).

### Run output

Every run starts with a timestamp and a sorted, aligned summary of every CLI
option's value, so a saved run's output is self-describing without also
needing to keep the invoking command line around:

```
Timestamp: 2026-08-18 17:44

ciphertext_file  cables\ct.123-50.txt
heartbeat        5
max_key_length   20
min_key_length   3
quadgram_file    output_quadgrams.txt
restarts         50
rtl              true
seed             1
top-n            10
try-bisection    false
try-reversal     false
verbose          true

Ciphertext length: 123

======================================================================
============================ KEY LENGTH 3 ============================
======================================================================
Complete rectangle (CCT): 41 rows
...
```

## Example end-to-end workflow

```bash
# 1. Build a quadgram table from a corpus (plain text or MediaWiki XML)
python build_hebrew_quadgrams.py output_quadgrams.txt corpus.txt

# 2. Solve, sweeping key lengths 5 through 20
python solve_columnar.py ciphertext.txt 5 20 output_quadgrams.txt --restarts 50

# 3. If nothing fully solves, cast a wider net
python solve_columnar.py ciphertext.txt 5 20 output_quadgrams.txt \
    --restarts 100 --try-bisection --try-reversal --top-n 20
```

## Background

The solver implements the baseline + segment-transformation hill climbing
from Lasry's thesis (Chapter 5): random restarts, and at each step every
possible **segment slide** (cyclically rotate a contiguous run of key
elements) and **segment swap** (exchange two non-overlapping contiguous
runs) is tried, keeping whichever transformation improves the score, until
no transformation helps (a local maximum). Both complete (CCT) and
incomplete (ICT) transposition rectangles are handled automatically, based
on whether the ciphertext length divides evenly by the key length. The more
advanced two-phase adjacency/alignment-score algorithm from later sections
of that chapter (for very long CCT keys, and long ICT keys) is not
implemented here.
