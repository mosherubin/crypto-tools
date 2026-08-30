"""
SQLite-backed results store for cipher_group_scan. Keeps OCR/text-extraction
results cached per page (so re-tuning thresholds does not require re-OCRing)
and tracks per-PDF completion status (so an interrupted archive scan resumes
instead of restarting).
"""

import csv
import json
import os
import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS pdfs (
    pdf_path TEXT PRIMARY KEY,
    fingerprint TEXT NOT NULL,
    status TEXT NOT NULL,          -- 'done' | 'error'
    stopped_early INTEGER NOT NULL,
    pages_scanned INTEGER NOT NULL,
    error_message TEXT,
    completed_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS pages (
    pdf_path TEXT NOT NULL,
    page_num INTEGER NOT NULL,
    method TEXT NOT NULL,
    text TEXT NOT NULL,
    matched INTEGER NOT NULL,
    best_run INTEGER NOT NULL,
    matched_lines_json TEXT,
    ambivalent_lines_json TEXT,
    PRIMARY KEY (pdf_path, page_num)
);
"""


def open_store(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA)
    _migrate(conn)
    return conn


def _migrate(conn: sqlite3.Connection) -> None:
    """Add columns introduced after a database was first created, so an
    existing results.db keeps working without a full re-extract."""
    columns = {row[1] for row in conn.execute("PRAGMA table_info(pages)")}
    if "matched_lines_json" not in columns:
        conn.execute("ALTER TABLE pages ADD COLUMN matched_lines_json TEXT")
        conn.commit()
    if "ambivalent_lines_json" not in columns:
        conn.execute("ALTER TABLE pages ADD COLUMN ambivalent_lines_json TEXT")
        conn.commit()


def resolve_root(root: str):
    """Ensure <root>/results.db and <root>/logs/ exist, returning (db_path, logs_dir)."""
    os.makedirs(root, exist_ok=True)
    logs_dir = os.path.join(root, "logs")
    os.makedirs(logs_dir, exist_ok=True)
    return os.path.join(root, "results.db"), logs_dir


def log_path_for(pdf_path: str, logs_dir: str) -> str:
    """Mirror the PDF's source path under logs_dir so a log file's location on
    disk matches where its PDF came from (e.g. D:\\Archive\\Batch1\\0001.pdf ->
    <logs_dir>\\D\\Archive\\Batch1\\0001.pdf.output)."""
    drive, tail = os.path.splitdrive(os.path.abspath(pdf_path))
    drive_component = drive.rstrip(":") or "_root"
    tail = tail.lstrip("\\/")
    return os.path.join(logs_dir, drive_component, tail + ".output")


def write_output_log(logs_dir: str, pdf_path: str, start, end, page_results: list,
                      stopped_early: bool, error_message: str = None) -> None:
    log_path = log_path_for(pdf_path, logs_dir)
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    def _line_dicts(lines):
        return [{"line_index": li, "run": run, "text": text} for li, text, run in lines]

    matched_pages = [
        {"page_num": r.page_num, "matched_lines": _line_dicts(r.matched_lines)}
        for r in (page_results or [])
        if r.matched
    ]
    ambivalent_pages = [
        {"page_num": r.page_num, "ambivalent_lines": _line_dicts(r.ambivalent_lines)}
        for r in (page_results or [])
        if r.ambivalent
    ]
    payload = {
        "pdf_path": pdf_path,
        "start_time": start.isoformat(),
        "end_time": end.isoformat(),
        "duration_seconds": (end - start).total_seconds(),
        "status": "error" if error_message else "done",
        "stopped_early": stopped_early,
        "pages_scanned": len(page_results) if page_results else 0,
        "matched_pages": matched_pages,
        "ambivalent_pages": ambivalent_pages,
        "error_message": error_message,
    }
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)


def forget_pdf(conn: sqlite3.Connection, pdf_path: str) -> bool:
    """Delete a PDF's cached pages and status, so a subsequent extract treats
    it as pending again instead of skipping it as already up to date. Returns
    True if there was anything cached to delete."""
    cur = conn.execute("DELETE FROM pdfs WHERE pdf_path = ?", (pdf_path,))
    conn.execute("DELETE FROM pages WHERE pdf_path = ?", (pdf_path,))
    conn.commit()
    return cur.rowcount > 0


def file_fingerprint(path: str) -> str:
    stat = os.stat(path)
    return f"{stat.st_size}:{int(stat.st_mtime)}"


def is_pdf_up_to_date(conn: sqlite3.Connection, pdf_path: str) -> bool:
    row = conn.execute("SELECT fingerprint FROM pdfs WHERE pdf_path = ?", (pdf_path,)).fetchone()
    if row is None:
        return False
    return row[0] == file_fingerprint(pdf_path)


def record_pdf_result(conn: sqlite3.Connection, pdf_path: str, page_results: list,
                       stopped_early: bool, status: str = "done", error_message: str = None) -> None:
    conn.execute("DELETE FROM pages WHERE pdf_path = ?", (pdf_path,))
    conn.executemany(
        "INSERT INTO pages (pdf_path, page_num, method, text, matched, best_run, "
        "matched_lines_json, ambivalent_lines_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        [
            (pdf_path, r.page_num, r.method, r.text, int(r.matched),
             max((run for _, _, run in r.matched_lines), default=0),
             json.dumps(r.matched_lines) if r.matched_lines else None,
             json.dumps(r.ambivalent_lines) if r.ambivalent_lines else None)
            for r in page_results
        ],
    )
    conn.execute(
        "INSERT OR REPLACE INTO pdfs "
        "(pdf_path, fingerprint, status, stopped_early, pages_scanned, error_message, completed_at) "
        "VALUES (?, ?, ?, ?, ?, ?, datetime('now'))",
        (pdf_path, file_fingerprint(pdf_path), status, int(stopped_early), len(page_results), error_message),
    )
    conn.commit()


def update_page_match(conn: sqlite3.Connection, pdf_path: str, page_num: int,
                       matches: list, ambivalent_lines: list) -> None:
    """Used by `detect` to re-evaluate a cached page against a new threshold,
    keeping matched_lines_json/best_run in sync with whatever matched becomes.

    ambivalent_lines_json is sticky: once a page has been flagged ambivalent,
    a later `detect` run only clears it by turning the page into a confirmed
    match. It's never silently cleared back to "nothing found" just because a
    different threshold no longer independently reproduces it -- a curator
    who's already been told "this page is worth a look" shouldn't have that
    withdrawn without a real resolution, since the only way to confirm or
    dismiss it is opening the PDF and looking, not re-running detect."""
    matched = bool(matches)
    best_run = max((run for _, _, run in matches), default=0)
    if matched:
        ambivalent_lines_json = None
    elif ambivalent_lines:
        ambivalent_lines_json = json.dumps(ambivalent_lines)
    else:
        existing = conn.execute(
            "SELECT ambivalent_lines_json FROM pages WHERE pdf_path = ? AND page_num = ?",
            (pdf_path, page_num),
        ).fetchone()
        ambivalent_lines_json = existing[0] if existing else None
    conn.execute(
        "UPDATE pages SET matched = ?, best_run = ?, matched_lines_json = ?, ambivalent_lines_json = ? "
        "WHERE pdf_path = ? AND page_num = ?",
        (int(matched), best_run, json.dumps(matches) if matches else None,
         ambivalent_lines_json, pdf_path, page_num),
    )


def flagged_pdfs(conn: sqlite3.Connection) -> list:
    """Return (pdf_path, matched_pages, stopped_early, pages_scanned) for every
    PDF with at least one matched page, using whatever text is currently cached.
    matched_pages is [{"page_num": ..., "matched_lines": [...]}, ...]."""
    rows = conn.execute(
        "SELECT pdf_path, stopped_early, pages_scanned FROM pdfs WHERE status = 'done'"
    ).fetchall()

    results = []
    for pdf_path, stopped_early, pages_scanned in rows:
        page_rows = conn.execute(
            "SELECT page_num, matched_lines_json FROM pages "
            "WHERE pdf_path = ? AND matched = 1 ORDER BY page_num",
            (pdf_path,),
        ).fetchall()
        if not page_rows:
            continue
        matched_pages = [
            {
                "page_num": page_num,
                "matched_lines": [
                    {"line_index": line_index, "run": run, "text": text}
                    for line_index, text, run in (json.loads(matched_lines_json) if matched_lines_json else [])
                ],
            }
            for page_num, matched_lines_json in page_rows
        ]
        results.append((pdf_path, matched_pages, bool(stopped_early), pages_scanned))
    return results


def export_report(conn: sqlite3.Connection, output_path: str) -> None:
    rows = flagged_pdfs(conn)
    ext = os.path.splitext(output_path)[1].lower()

    if ext == ".json":
        payload = [
            {
                "pdf_path": pdf_path,
                "flagged_pages": matched_pages,
                "stopped_early": stopped_early,
                "pages_scanned": pages_scanned,
            }
            for pdf_path, matched_pages, stopped_early, pages_scanned in rows
        ]
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
    else:
        with open(output_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["pdf_path", "matched_lines", "flagged_pages",
                              "stopped_early", "pages_scanned"])
            for pdf_path, matched_pages, stopped_early, pages_scanned in rows:
                page_nums = ";".join(str(p["page_num"]) for p in matched_pages)
                lines_summary = " | ".join(
                    f"p{p['page_num']}: {line['text']}"
                    for p in matched_pages
                    for line in p["matched_lines"]
                )
                writer.writerow([pdf_path, lines_summary, page_nums, stopped_early, pages_scanned])


def ambivalent_pdfs(conn: sqlite3.Connection) -> list:
    """Return (pdf_path, ambivalent_pages, pages_scanned) for every PDF that
    is NOT flagged but has at least one page with a qualifying line lacking
    an adjacent qualifying neighbor -- the tool found something structurally
    group-shaped but couldn't confirm it, which is a different state from
    "scanned and genuinely found nothing." A PDF that's already flagged is
    excluded here even if it also has an ambivalent page elsewhere, since
    it'll already be opened for review regardless.
    ambivalent_pages is [{"page_num": ..., "ambivalent_lines": [...]}, ...]."""
    rows = conn.execute(
        "SELECT pdf_path, pages_scanned FROM pdfs WHERE status = 'done'"
    ).fetchall()

    results = []
    for pdf_path, pages_scanned in rows:
        matched_count = conn.execute(
            "SELECT COUNT(*) FROM pages WHERE pdf_path = ? AND matched = 1", (pdf_path,)
        ).fetchone()[0]
        if matched_count:
            continue

        page_rows = conn.execute(
            "SELECT page_num, ambivalent_lines_json FROM pages WHERE pdf_path = ? "
            "AND ambivalent_lines_json IS NOT NULL ORDER BY page_num",
            (pdf_path,),
        ).fetchall()
        if not page_rows:
            continue

        ambivalent_pages = [
            {
                "page_num": page_num,
                "ambivalent_lines": [
                    {"line_index": line_index, "run": run, "text": text}
                    for line_index, text, run in json.loads(ambivalent_lines_json)
                ],
            }
            for page_num, ambivalent_lines_json in page_rows
        ]
        results.append((pdf_path, ambivalent_pages, pages_scanned))
    return results


def export_ambivalent_report(conn: sqlite3.Connection, output_path: str) -> None:
    rows = ambivalent_pdfs(conn)
    ext = os.path.splitext(output_path)[1].lower()

    if ext == ".json":
        payload = [
            {"pdf_path": pdf_path, "ambivalent_pages": ambivalent_pages, "pages_scanned": pages_scanned}
            for pdf_path, ambivalent_pages, pages_scanned in rows
        ]
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
    else:
        with open(output_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["pdf_path", "ambivalent_lines", "ambivalent_pages", "pages_scanned"])
            for pdf_path, ambivalent_pages, pages_scanned in rows:
                page_nums = ";".join(str(p["page_num"]) for p in ambivalent_pages)
                lines_summary = " | ".join(
                    f"p{p['page_num']}: {line['text']}"
                    for p in ambivalent_pages
                    for line in p["ambivalent_lines"]
                )
                writer.writerow([pdf_path, lines_summary, page_nums, pages_scanned])


def errored_pdfs(conn: sqlite3.Connection) -> list:
    """Return (pdf_path, error_message, completed_at) for every PDF that failed
    during extract -- never successfully scanned, distinct from a PDF that was
    scanned and found clean."""
    return conn.execute(
        "SELECT pdf_path, error_message, completed_at FROM pdfs WHERE status = 'error' "
        "ORDER BY pdf_path"
    ).fetchall()


def export_errors_report(conn: sqlite3.Connection, output_path: str) -> None:
    rows = errored_pdfs(conn)
    ext = os.path.splitext(output_path)[1].lower()

    if ext == ".json":
        payload = [
            {"pdf_path": pdf_path, "error_message": error_message, "completed_at": completed_at}
            for pdf_path, error_message, completed_at in rows
        ]
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
    else:
        with open(output_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["pdf_path", "error_message", "completed_at"])
            for pdf_path, error_message, completed_at in rows:
                writer.writerow([pdf_path, error_message, completed_at])
