import os
import subprocess
import sys

import pytest

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, '..', '..', 'Library'))
sys.path.insert(0, os.path.join(HERE, '..'))

from find_repetitions import DIT, count_repetitions, locate_repetitions, RepetitionCount
from run_find_repetitions import DEFAULT_ALPHABET, load_ciphertext

CLI = os.path.join(HERE, '..', 'run_find_repetitions.py')


def _found(ciphertexts, min_length):
    results = locate_repetitions(ciphertexts, min_length)
    return sorted((r.message_a, r.message_b, r.position_a, r.position_b, r.length, r.text) for r in results)


def _write(tmp_path, name, content):
    path = tmp_path / name
    path.write_text(content, encoding='utf-8')
    return str(path)


def _run_cli(*args):
    return subprocess.run([sys.executable, CLI, *args], capture_output=True, text=True)


def test_dit_free_input_is_unchanged():
    found = _found(["XXXXXBROWNFOXYYYYYBROWNFOXZZZZZ", "QQQBROWNFOXRRR"], 5)
    assert found == [
        (0, 0, 5, 18, 8, "BROWNFOX"),
        (0, 1, 5, 3, 8, "BROWNFOX"),
        (0, 1, 18, 3, 8, "BROWNFOX"),
    ]


def test_dit_slot_splits_a_repetition_and_is_never_reported():
    found = _found([f"ABCD{DIT}FGH", "ABCDXFGH"], 3)
    assert found == [
        (0, 1, 0, 0, 4, "ABCD"),
        (0, 1, 5, 5, 3, "FGH"),
    ]


def test_two_aligned_dits_do_not_match():
    assert _found([f"AB{DIT}CD", f"EF{DIT}GH"], 1) == []
    assert _found([f"AB{DIT}{DIT}CD", f"AB{DIT}{DIT}CD"], 2) == [
        (0, 1, 0, 0, 2, "AB"),
        (0, 1, 4, 4, 2, "CD"),
    ]


def test_dit_at_the_very_start_and_very_end():
    assert _found([f"{DIT}ABCDE{DIT}", f"{DIT}ABCDE{DIT}"], 3) == [(0, 1, 1, 1, 5, "ABCDE")]


def test_positions_stay_true_when_a_dit_shifts_the_alignment():
    assert _found([f"{DIT}ABC", f"ABC{DIT}"], 3) == [(0, 1, 1, 0, 3, "ABC")]


def test_self_search_keeps_true_offsets_across_dits():
    found = _found([f"ABC{DIT}EABC{DIT}E"], 3)
    assert found == [(0, 0, 0, 5, 3, "ABC")]


def test_counts_never_include_a_text_containing_a_dit():
    ciphertexts = [f"XABC{DIT}", f"{DIT}ABCY", f"ABC{DIT}Z"]
    results = locate_repetitions(ciphertexts, 3)
    assert all(DIT not in r.text for r in results)
    assert count_repetitions(results) == [RepetitionCount(text="ABC", count=3)]


def test_different_dit_characters_give_identical_results(tmp_path):
    dotted = _write(tmp_path, "dotted.txt", "ABCD.FGH")
    dashed = _write(tmp_path, "dashed.txt", "ABCD-FGH")
    mixed = [load_ciphertext(dotted, DEFAULT_ALPHABET, "."), load_ciphertext(dashed, DEFAULT_ALPHABET, "-")]
    same = [load_ciphertext(dotted, DEFAULT_ALPHABET, "."), load_ciphertext(dotted, DEFAULT_ALPHABET, ".")]

    assert mixed == same == [f"ABCD{DIT}FGH"] * 2
    assert _found(mixed, 3) == _found(same, 3)


def test_loader_rejects_an_undeclared_dit_character(tmp_path):
    path = _write(tmp_path, "undeclared.txt", "ABC.DEF")
    with pytest.raises(ValueError):
        load_ciphertext(path, DEFAULT_ALPHABET)


def test_cli_reports_dits_beside_the_letter_count(tmp_path):
    with_dits = _write(tmp_path, "with_dits.txt", "ABC.DEF.GHI")
    one_dit = _write(tmp_path, "one_dit.txt", "ABC.DEF")
    without = _write(tmp_path, "without.txt", "ABCDEF")
    completed = _run_cli("--ditschar", ".", with_dits, one_dit, without)

    assert completed.returncode == 0
    lines = completed.stdout.splitlines()
    assert lines[0] == f"{with_dits}: 9 letters, 2 dits"
    assert lines[1] == f"{one_dit}: 6 letters, 1 dit"
    assert lines[2] == f"{without}: 6 letters"


def test_cli_rejects_a_dit_character_longer_than_one_character(tmp_path):
    path = _write(tmp_path, "ct.txt", "ABCDEF")
    completed = _run_cli("--ditschar", "..", path)

    assert completed.returncode != 0
    assert "single character" in completed.stderr
