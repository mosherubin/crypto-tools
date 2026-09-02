"""
Isomorph regression validator.
Usage: python validate_regression.py [<fixture.json> ...]

Loads one or more fixture files (see regression-data/*.json), runs
locate_isomorphs()/apply_pruning()/evaluate_isomorph() against the fixture's
ciphertexts, and diffs the significant isomorphs found against
expected_results.

Each fixture's expected_results holds three INDEPENDENT lists, one per
pruning mode: "raw", "shallow", "deep". They are independent -- not the same
set of isomorphs with per-mode details -- because pruning happens before the
significance filter: a candidate insignificant when raw can become
significant once trimmed, and vice versa, so each mode's significant set can
differ in membership, not just in the details of a shared set. A pruned
entry's position_a/position_b are the pruned (shifted) span's own start, not
the original raw candidate's.
"""

import argparse
import glob
import json
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'Library'))

from isomorph_search import locate_isomorphs, prune_candidates, PRUNE_MODES
from isomorph_evaluation import evaluate_isomorph

FLOAT_TOLERANCE = 1e-4


def _isoclose(a: float, b: float) -> bool:
    return math.isclose(a, b, rel_tol=FLOAT_TOLERANCE, abs_tol=FLOAT_TOLERANCE)


def _key(entry: dict) -> tuple:
    return (entry["message_a"], entry["message_b"], entry["position_a"], entry["position_b"])


def _find_significant_for_mode(candidates: list, mode: str, ciphertexts: list, alphabet_size: int,
                                min_isolen: int, max_expected: float) -> dict:
    found = {}
    for pruned in prune_candidates(candidates, mode, min_isolen):
        self_search = pruned.message_a == pruned.message_b
        sig = evaluate_isomorph(
            pruned.text_a, alphabet_size,
            len(ciphertexts[pruned.message_a]), len(ciphertexts[pruned.message_b]),
            self_search, max_expected,
        )
        if sig.significant:
            found[(pruned.message_a, pruned.message_b, pruned.position_a, pruned.position_b)] = (pruned, sig)

    return found


def _validate_mode(mode: str, found: dict, expected_entries: list, errors: list) -> None:
    expected_by_key = {_key(e): e for e in expected_entries}

    for key in expected_by_key.keys() - found.keys():
        errors.append(f"[{mode}] MISSING expected isomorph at {key}")
    for key in found.keys() - expected_by_key.keys():
        errors.append(f"[{mode}] UNEXPECTED extra isomorph found at {key}")

    for key in expected_by_key.keys() & found.keys():
        expected = expected_by_key[key]
        candidate, sig = found[key]

        if candidate.length != expected["length"]:
            errors.append(f"[{mode}] {key} length: computed {candidate.length}, expected {expected['length']}")
        if candidate.text_a != expected["text_a"] or candidate.text_b != expected["text_b"]:
            errors.append(
                f"[{mode}] {key} text: computed {candidate.text_a!r}/{candidate.text_b!r}, "
                f"expected {expected['text_a']!r}/{expected['text_b']!r}"
            )
        if sig.num_distinct_chars != expected["num_distinct_chars"]:
            errors.append(
                f"[{mode}] {key} num_distinct_chars: computed {sig.num_distinct_chars}, "
                f"expected {expected['num_distinct_chars']}"
            )
        if not _isoclose(sig.expected_occurrences, expected["expected_occurrences"]):
            errors.append(
                f"[{mode}] {key} expected_occurrences: computed {sig.expected_occurrences:.6f}, "
                f"expected {expected['expected_occurrences']:.6f}"
            )


def validate_fixture(path: str) -> bool:
    with open(path, encoding="utf-8") as f:
        fixture = json.load(f)

    print(f"=== {fixture.get('test_case_id', path)} ===")

    ciphertexts = [ct["raw"] for ct in fixture["ciphertexts"]]
    alphabet_size = len(fixture["parameters"]["alphabet"])
    min_isolen = fixture["parameters"]["min_isolen"]
    max_expected = fixture["parameters"]["max_expected"]

    candidates = locate_isomorphs(ciphertexts, min_isolen)

    errors = []
    total_matched = 0
    for mode in PRUNE_MODES:
        expected_entries = fixture["expected_results"].get(mode, [])
        found = _find_significant_for_mode(candidates, mode, ciphertexts, alphabet_size, min_isolen, max_expected)
        before = len(errors)
        _validate_mode(mode, found, expected_entries, errors)
        if len(errors) == before:
            total_matched += len(expected_entries)

    if errors:
        print(f"FAIL ({len(errors)} errors)")
        for err in errors[:50]:
            print(f"  {err}")
        if len(errors) > 50:
            print(f"  ... and {len(errors) - 50} more")
        return False

    print(f"PASS ({total_matched} significant isomorphs matched across raw/shallow/deep)")
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("fixtures", nargs="*", help="Fixture JSON files (default: regression-data/*.json)")
    args = parser.parse_args()

    paths = args.fixtures or sorted(glob.glob(os.path.join(os.path.dirname(__file__), "regression-data", "*.json")))

    all_passed = True
    for path in paths:
        all_passed &= validate_fixture(path)
        print()

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
