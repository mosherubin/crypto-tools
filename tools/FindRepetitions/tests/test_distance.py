import os
import subprocess
import sys

HERE = os.path.dirname(__file__)
CLI = os.path.join(HERE, '..', 'run_find_repetitions.py')


def _run_cli(tmp_path, *contents):
    paths = []
    for index, content in enumerate(contents):
        path = tmp_path / f"ct{index}.txt"
        path.write_text(content, encoding='utf-8')
        paths.append(str(path))
    completed = subprocess.run([sys.executable, CLI, "--min-length", "5", *paths], capture_output=True, text=True)
    assert completed.returncode == 0
    return completed.stdout.splitlines()


def _rows(lines):
    start = lines.index("REPETITIONS FOUND") + 2
    end = lines.index("", start)
    return lines[start:end]


def test_header_has_dist_between_len_and_text(tmp_path):
    lines = _run_cli(tmp_path, "XXBROWNFOXYYBROWNFOXZZ")
    header = lines[lines.index("REPETITIONS FOUND") + 1]
    assert header.split() == ["MSG", "A", "MSG", "B", "POS", "A", "POS", "B", "LEN", "DIST", "TEXT"]


def test_same_message_repetition_reports_position_b_minus_position_a(tmp_path):
    rows = _rows(_run_cli(tmp_path, "XXBROWNFOXYYBROWNFOXZZ"))
    assert rows == ["     0      0      3     13    8     10   BROWNFOX"]


def test_cross_message_repetition_leaves_dist_empty(tmp_path):
    rows = _rows(_run_cli(tmp_path, "XXBROWNFOXYY", "QQBROWNFOXRR"))
    assert rows == ["     0      1      3      3    8          BROWNFOX"]


def test_mixed_rows_keep_text_aligned(tmp_path):
    rows = _rows(_run_cli(tmp_path, "BROWNFOXYYBROWNFOX", "BROWNFOX"))
    assert len({row.index("BROWNFOX") for row in rows}) == 1
