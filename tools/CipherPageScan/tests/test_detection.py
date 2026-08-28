import os
import sys
from datetime import datetime

import fitz
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'Library'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'fixtures'))

from cipher_group_scan import DEFAULT_DPI, DEFAULT_LANGS, scan_pdf
from generate_fixtures import main as generate_fixtures

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
MIN_GROUPS = 3
MIN_LINES = 1

# Regenerated on every run so the fixtures never drift from the generator
# source and no binary PDF data needs to be committed to the repo.
generate_fixtures()


def _fixture_pdfs(subdir):
    directory = os.path.join(FIXTURES_DIR, subdir)
    if not os.path.isdir(directory):
        return []
    return [
        os.path.join(directory, name)
        for name in sorted(os.listdir(directory))
        if name.lower().endswith(".pdf")
    ]


_run_stats = {"total_pages": 0, "total_seconds": 0.0}


def _scan_with_progress(pdf_path, stop_at_first_hit):
    print(f"\nscanning {pdf_path}")
    with fitz.open(pdf_path) as doc:
        total_pages = doc.page_count

    results = []
    page_durations = []
    next_page_num = 1
    iterator = scan_pdf(pdf_path, DEFAULT_DPI, DEFAULT_LANGS, MIN_GROUPS, MIN_LINES, stop_at_first_hit)
    while next_page_num <= total_pages:
        if results and stop_at_first_hit and results[-1].matched:
            break  # scan_pdf will not process another page; nothing left to time

        start = datetime.now()
        print(f"  page {next_page_num}/{total_pages}: {start:%H:%M:%S.%f} -> ", end="", flush=True)
        try:
            result = next(iterator)
        except StopIteration:
            print("(no result)")
            break
        end = datetime.now()
        duration = (end - start).total_seconds()
        print(f"{end:%H:%M:%S.%f} ({duration:.1f}s, {result.method}, matched={result.matched})")
        results.append(result)
        page_durations.append(duration)
        next_page_num = result.page_num + 1

    if page_durations:
        pdf_average = sum(page_durations) / len(page_durations)
        _run_stats["total_pages"] += len(page_durations)
        _run_stats["total_seconds"] += sum(page_durations)
        running_average = _run_stats["total_seconds"] / _run_stats["total_pages"]
        print(f"  this PDF: {pdf_average:.1f}s/page avg ({len(page_durations)} page(s))  |  "
              f"running average: {running_average:.1f}s/page ({_run_stats['total_pages']} page(s) total)")

    return results


@pytest.mark.parametrize("pdf_path", _fixture_pdfs("should_flag"))
def test_known_cipher_pdf_is_flagged(pdf_path):
    results = _scan_with_progress(pdf_path, stop_at_first_hit=True)
    assert any(r.matched for r in results), f"No page flagged in {pdf_path}"


@pytest.mark.parametrize("pdf_path", _fixture_pdfs("should_not_flag"))
def test_ordinary_pdf_is_not_flagged(pdf_path):
    results = _scan_with_progress(pdf_path, stop_at_first_hit=False)
    assert not any(r.matched for r in results), f"Unexpected flag in {pdf_path}"
