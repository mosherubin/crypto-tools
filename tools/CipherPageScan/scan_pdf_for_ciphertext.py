"""
Scans PDF archives for pages that may contain enciphered/encoded text, flagged
by the presence of multiple consecutive 5-character groups on a line (any
script: Latin, digits, Hebrew, ...).

Four subcommands, split so re-tuning thresholds never requires re-OCRing:

  extract  Resolve the given inputs to PDF files, extract or OCR each page,
           and cache the results under --root. By default stops at a PDF's
           first matched page (--exhaustive scans every page instead). Skips
           PDFs already cached and unchanged, so an interrupted run resumes
           rather than restarting.
  detect   Re-run the group-match logic over already-cached page text with a
           new --min-groups/--min-lines/--min-purity, no OCR involved.
  export   Write a CSV or JSON report of every flagged PDF and its matched
           page numbers (or --errors / --ambivalent for the other report
           types).
  forget   Clear cached results (and any stale .output log) for the given
           PDFs, so the next extract re-scans them from scratch instead of
           skipping them as already up to date.

--root <dir> holds everything extract/detect/export produce: <root>/results.db
and, per PDF scanned, a start/end-timestamped <root>/logs/.../<name>.pdf.output
JSON log mirroring the PDF's own source path.

Inputs (positional, and/or listed one per line in a --from-file) may be:
  - a PDF file
  - a directory (every *.pdf directly inside it; add --recursive for subfolders)
  - a glob pattern in the filename part only, e.g. D:\\Archive\\Batch1\\0b07*.pdf
    (--recursive applies the pattern to subfolders too)

Usage:
  python scan_pdf_for_ciphertext.py extract --root D:\\Scan "D:\\Archive\\0b07*.pdf" --recursive
  python scan_pdf_for_ciphertext.py extract --root D:\\Scan --from-file batch1.txt
  python scan_pdf_for_ciphertext.py detect --root D:\\Scan --min-groups 4
  python scan_pdf_for_ciphertext.py export --root D:\\Scan --output report.csv
"""

import argparse
import fnmatch
import multiprocessing
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'Library'))

from cipher_group_scan import (
    DEFAULT_DPI, DEFAULT_LANGS, DEFAULT_MIN_PURITY, DEFAULT_PSM, check_tesseract_available,
    configure_tesseract, scan_pdf, scan_page_text,
)
from cipher_scan_store import (
    ambivalent_pdfs, errored_pdfs, export_ambivalent_report, export_errors_report, export_report,
    flagged_pdfs, forget_pdf, is_pdf_up_to_date, log_path_for, open_store, record_pdf_result,
    resolve_root, update_page_match, write_output_log,
)

DEFAULT_MIN_GROUPS = 3
DEFAULT_MIN_LINES = 1
GLOB_CHARS = set("*?[")


def has_glob_chars(s: str) -> bool:
    return any(ch in GLOB_CHARS for ch in s)


def match_files_in_dir(directory: str, pattern: str, recursive: bool):
    if not os.path.isdir(directory):
        return
    if recursive:
        for root, _, files in os.walk(directory):
            for name in sorted(files):
                if fnmatch.fnmatch(name, pattern):
                    yield os.path.join(root, name)
    else:
        for name in sorted(os.listdir(directory)):
            full = os.path.join(directory, name)
            if os.path.isfile(full) and fnmatch.fnmatch(name, pattern):
                yield full


def resolve_spec(spec: str, recursive: bool):
    directory, pattern = os.path.split(spec)
    if has_glob_chars(directory):
        raise ValueError(
            f"Wildcards are only supported in the filename part of a spec, not the "
            f"directory: {spec!r}"
        )

    if has_glob_chars(pattern):
        yield from match_files_in_dir(directory or ".", pattern, recursive)
    elif os.path.isdir(spec):
        yield from match_files_in_dir(spec, "*.pdf", recursive)
    else:
        yield spec


def resolve_pdf_paths(specs: list, recursive: bool) -> list:
    seen = set()
    result = []
    for spec in specs:
        for path in resolve_spec(spec, recursive):
            key = os.path.normcase(os.path.abspath(path))
            if key not in seen:
                seen.add(key)
                result.append(path)
    return result


def read_spec_file(path: str) -> list:
    specs = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                specs.append(line)
    return specs


def gather_specs(args) -> list:
    specs = list(args.inputs)
    for list_file in (args.from_file or []):
        specs.extend(read_spec_file(list_file))
    return specs


_print_lock = None


def _init_worker(print_lock):
    # Pool workers are separate processes (spawned fresh on Windows) and do not
    # inherit the parent's in-memory tesseract_cmd setting, so it must be
    # rediscovered here. Also cap Tesseract's own threading to avoid
    # oversubscribing cores across many worker processes.
    global _print_lock
    _print_lock = print_lock
    os.environ["OMP_THREAD_LIMIT"] = "1"
    configure_tesseract()


def _scan_worker(task):
    pdf_path, dpi, langs, min_groups, min_lines, stop_at_first_hit, min_purity, psm, logs_dir = task
    # Announce before scanning starts, not after -- the output path only
    # depends on pdf_path/logs_dir, not on results, so there's no need to
    # wait. A shared lock keeps concurrent workers' announcements from
    # interleaving mid-line.
    with _print_lock:
        print(f"\nWriting scan output to {log_path_for(pdf_path, logs_dir)}")

    start = datetime.now(timezone.utc)
    try:
        import fitz
        with fitz.open(pdf_path) as doc:
            total_pages = doc.page_count
        results = list(scan_pdf(pdf_path, dpi, langs, min_groups, min_lines, stop_at_first_hit, min_purity, psm))
        stopped_early = len(results) < total_pages
        return pdf_path, results, stopped_early, None, start, datetime.now(timezone.utc)
    except Exception as exc:
        return pdf_path, None, False, repr(exc), start, datetime.now(timezone.utc)


def cmd_extract(args):
    check_tesseract_available(args.langs)
    db_path, logs_dir = resolve_root(args.root)
    conn = open_store(db_path)

    specs = gather_specs(args)
    if not specs:
        print("No input specs given (use positional arguments and/or --from-file).")
        return

    pdf_paths = resolve_pdf_paths(specs, args.recursive)
    if not pdf_paths:
        print("No PDF files matched the given specs.")
        return

    pending = [p for p in pdf_paths if not is_pdf_up_to_date(conn, p)]
    print(f"{len(pdf_paths)} PDF(s) matched, {len(pending)} pending "
          f"({len(pdf_paths) - len(pending)} already cached and unchanged)")

    tasks = [
        (p, args.dpi, args.langs, args.min_groups, args.min_lines, not args.exhaustive, args.min_purity, args.psm,
         logs_dir)
        for p in pending
    ]

    print_lock = multiprocessing.Lock()
    with multiprocessing.Pool(args.workers, initializer=_init_worker, initargs=(print_lock,)) as pool:
        for i, (pdf_path, results, stopped_early, error, start, end) in enumerate(
                pool.imap_unordered(_scan_worker, tasks), 1):
            write_output_log(logs_dir, pdf_path, start, end, results, stopped_early, error)
            if error:
                record_pdf_result(conn, pdf_path, [], False, status="error", error_message=error)
                print(f"[{i}/{len(pending)}] ERROR {pdf_path}: {error}")
                continue
            record_pdf_result(conn, pdf_path, results, stopped_early)
            matched_pages = [r.page_num for r in results if r.matched]
            status = f"FLAGGED pages {matched_pages}" if matched_pages else "clean"
            print(f"[{i}/{len(pending)}] {pdf_path}: {status} ({len(results)} pages scanned)")

    conn.close()


def cmd_detect(args):
    db_path, _ = resolve_root(args.root)
    conn = open_store(db_path)
    pdf_paths = [row[0] for row in conn.execute("SELECT pdf_path FROM pdfs WHERE status = 'done'")]

    for pdf_path in pdf_paths:
        rows = conn.execute(
            "SELECT page_num, text FROM pages WHERE pdf_path = ? ORDER BY page_num", (pdf_path,)
        ).fetchall()
        for page_num, text in rows:
            matches, ambivalent_lines = scan_page_text(text, args.min_groups, args.min_lines, args.min_purity)
            update_page_match(conn, pdf_path, page_num, matches, ambivalent_lines)
        conn.commit()

    print(f"Re-evaluated {len(pdf_paths)} cached PDF(s) with "
          f"min_groups={args.min_groups}, min_lines={args.min_lines}, min_purity={args.min_purity}")
    print("Note: PDFs that were stopped early under a stricter threshold may have "
          "unscanned pages a looser threshold would catch -- re-run extract for those "
          "PDFs specifically to backfill them.")


def cmd_export(args):
    db_path, _ = resolve_root(args.root)
    conn = open_store(db_path)
    if args.errors:
        export_errors_report(conn, args.output)
        print(f"{len(errored_pdfs(conn))} PDF(s) failed to scan. Report written to {args.output}")
    elif args.ambivalent:
        export_ambivalent_report(conn, args.output)
        print(f"{len(ambivalent_pdfs(conn))} PDF(s) ambivalent (not flagged, but had an unresolved "
              f"near-miss). Report written to {args.output}")
    else:
        export_report(conn, args.output)
        print(f"{len(flagged_pdfs(conn))} PDF(s) flagged. Report written to {args.output}")


def cmd_forget(args):
    db_path, logs_dir = resolve_root(args.root)
    conn = open_store(db_path)

    specs = gather_specs(args)
    if not specs:
        print("No input specs given (use positional arguments and/or --from-file).")
        return

    pdf_paths = resolve_pdf_paths(specs, args.recursive)
    if not pdf_paths:
        print("No PDF files matched the given specs.")
        return

    forgotten = 0
    for pdf_path in pdf_paths:
        if forget_pdf(conn, pdf_path):
            forgotten += 1
            log_path = log_path_for(pdf_path, logs_dir)
            if os.path.isfile(log_path):
                os.remove(log_path)

    conn.close()
    print(f"Forgot {forgotten}/{len(pdf_paths)} PDF(s). They will be re-scanned on the next extract.")


def add_root_argument(subparser):
    subparser.add_argument("--root", required=True,
                            help="Root folder for results.db and per-PDF logs/ (created if missing)")


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    subparsers = parser.add_subparsers(dest="command", required=True)

    extract = subparsers.add_parser("extract", help="Extract/OCR pages and cache results")
    extract.add_argument("inputs", nargs="*",
                          help="PDF files, directories, and/or glob patterns to scan")
    extract.add_argument("--from-file", action="append", metavar="LISTFILE",
                          help="Text file with one input spec per line (blank lines and lines "
                               "starting with # are ignored). Repeatable.")
    extract.add_argument("--recursive", action="store_true",
                          help="Recurse into subfolders for directory inputs and directory-based "
                               "glob patterns (default: top-level only)")
    add_root_argument(extract)
    extract.add_argument("--min-groups", type=int, default=DEFAULT_MIN_GROUPS,
                          help=f"Minimum consecutive 5-char groups per line to flag it (default {DEFAULT_MIN_GROUPS})")
    extract.add_argument("--min-lines", type=int, default=DEFAULT_MIN_LINES,
                          help=f"Minimum flagged lines per page to flag the page (default {DEFAULT_MIN_LINES})")
    extract.add_argument("--min-purity", type=float, default=DEFAULT_MIN_PURITY,
                          help="Minimum fraction of a flagged line's tokens that must be group-shaped "
                               f"(default {DEFAULT_MIN_PURITY}); filters coincidental group-length words "
                               "embedded in ordinary prose")
    extract.add_argument("--langs", default=DEFAULT_LANGS, help=f"Tesseract language codes (default {DEFAULT_LANGS})")
    extract.add_argument("--dpi", type=int, default=DEFAULT_DPI, help=f"OCR render DPI (default {DEFAULT_DPI})")
    extract.add_argument("--psm", type=int, default=DEFAULT_PSM,
                          help="Tesseract page segmentation mode (default %(default)s: assume a single "
                               "uniform block of text -- Tesseract's own default, mode 3, fragments "
                               "grid/table-formatted group text into one word per detected line)")
    extract.add_argument("--workers", type=int, default=max(1, os.cpu_count() - 1),
                          help="Parallel worker processes (default: cpu count - 1)")
    extract.add_argument("--exhaustive", action="store_true",
                          help="Scan every page of every PDF instead of stopping at the first match")
    extract.set_defaults(func=cmd_extract)

    detect = subparsers.add_parser("detect", help="Re-run pattern matching over cached page text")
    add_root_argument(detect)
    detect.add_argument("--min-groups", type=int, default=DEFAULT_MIN_GROUPS,
                         help=f"Minimum consecutive 5-char groups per line to flag it (default {DEFAULT_MIN_GROUPS})")
    detect.add_argument("--min-lines", type=int, default=DEFAULT_MIN_LINES,
                         help=f"Minimum flagged lines per page to flag the page (default {DEFAULT_MIN_LINES})")
    detect.add_argument("--min-purity", type=float, default=DEFAULT_MIN_PURITY,
                         help="Minimum fraction of a flagged line's tokens that must be group-shaped "
                              f"(default {DEFAULT_MIN_PURITY})")
    detect.set_defaults(func=cmd_detect)

    export = subparsers.add_parser("export", help="Write a report of flagged PDFs")
    add_root_argument(export)
    export.add_argument("--output", required=True, help="Report path (.csv or .json)")
    report_type = export.add_mutually_exclusive_group()
    report_type.add_argument("--errors", action="store_true",
                              help="Report PDFs that failed during extract instead of flagged PDFs "
                                   "(pdf_path, error_message, completed_at)")
    report_type.add_argument("--ambivalent", action="store_true",
                              help="Report PDFs that are not flagged but have a qualifying line with "
                                   "no adjacent qualifying neighbor -- structurally group-shaped but "
                                   "unconfirmed, worth opening by hand to check")
    export.set_defaults(func=cmd_export)

    forget = subparsers.add_parser("forget", help="Clear cached results for PDFs, forcing re-extraction")
    forget.add_argument("inputs", nargs="*",
                         help="PDF files, directories, and/or glob patterns to forget")
    forget.add_argument("--from-file", action="append", metavar="LISTFILE",
                         help="Text file with one input spec per line (blank lines and lines "
                              "starting with # are ignored). Repeatable.")
    forget.add_argument("--recursive", action="store_true",
                         help="Recurse into subfolders for directory inputs and directory-based "
                              "glob patterns (default: top-level only)")
    add_root_argument(forget)
    forget.set_defaults(func=cmd_forget)

    return parser


def main():
    args = build_parser().parse_args()
    try:
        args.func(args)
    except (ValueError, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
