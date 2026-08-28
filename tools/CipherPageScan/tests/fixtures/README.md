# Test fixtures

`generate_fixtures.py` synthesizes small PDFs into `should_flag/` and
`should_not_flag/` at the start of every test run (see its call in
`test_detection.py`) -- nothing here is committed to git (both are
`.gitignore`d), so no binary PDF data lives in the repo.

- `should_flag/` — PDFs containing synthetic cipher/code group text. Each
  must have at least one page the scanner is expected to flag.
- `should_not_flag/` — synthetic PDFs with no coded content, used to check
  the detector doesn't fire on regular text.

Each fixture targets a specific detection behavior validated against real
archive scans during development (grid/table OCR segmentation, bidi control
character stripping, the strict-majority run requirement, the line-adjacency
requirement, and the Hebrew-prose false-positive pattern) -- see the
docstring on each generator function in `generate_fixtures.py` for exactly
what each one is checking and why.

`test_detection.py` picks up every `.pdf` file in both directories
automatically — no registration needed. To add a fixture, add a new
generator function in `generate_fixtures.py` (and register it in
`GENERATORS`) rather than dropping in a binary PDF file directly.

If you want to spot-check against real archival material, keep those PDFs
outside this repo (e.g. in a separate local folder) rather than adding them
here -- real archive fixtures used during development ran over an hour per
full test run and are not something to commit to version control.
