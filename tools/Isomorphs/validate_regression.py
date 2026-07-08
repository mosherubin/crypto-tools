"""
Isomorph regression validator.
Usage: python validate_regression.py [<fixture.json> ...]

Loads one or more fixture files (see regression-data/*.json), runs
locate_isomorphs()/evaluate_isomorph() against the fixture's ciphertexts, and
diffs the significant isomorphs found against expected_results.

Only the "raw" pruning mode is checked today. A fixture entry's "shallow" or
"deep" key is skipped while it is null; once shallow/deep pruning is
implemented, fill those keys in with the same shape as "raw" and this script
will pick them up without changes.
"""

import argparse
import glob
import json
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'Library'))

from isomorph_search import locate_isomorphs
from isomorph_evaluation import evaluate_isomorph

FLOAT_TOLERANCE = 1e-4
PRUNING_MODES = ("raw", "shallow", "deep")


def _isoclose(a: float, b: float) -> bool:
    return math.isclose(a, b, rel_tol=FLOAT_TOLERANCE, abs_tol=FLOAT_TOLERANCE)


def _key(entry: dict) -> tuple:
    return (entry["message_a"], entry["message_b"], entry["position_a"], entry["position_b"])


def validate_fixture(path: str) -> bool:
    with open(path, encoding="utf-8") as f:
        fixture = json.load(f)

    print(f"=== {fixture.get('test_case_id', path)} ===")

    ciphertexts = [ct["raw"] for ct in fixture["ciphertexts"]]
    alphabet_size = len(fixture["parameters"]["alphabet"])
    min_isolen = fixture["parameters"]["min_isolen"]
    max_expected = fixture["parameters"]["max_expected"]

    candidates = locate_isomorphs(ciphertexts, min_isolen)

    found = {}
    for c in candidates:
        self_search = c.message_a == c.message_b
        sig = evaluate_isomorph(
            c.text_a, alphabet_size,
            len(ciphertexts[c.message_a]), len(ciphertexts[c.message_b]),
            self_search, max_expected,
        )
        if sig.significant:
            found[(c.message_a, c.message_b, c.position_a, c.position_b)] = (c, sig)

    expected_entries = fixture["expected_results"]["significant_isomorphs"]
    expected_by_key = {_key(e): e for e in expected_entries}

    errors = []

    for key in expected_by_key.keys() - found.keys():
        errors.append(f"MISSING expected isomorph at {key}")
    for key in found.keys() - expected_by_key.keys():
        errors.append(f"UNEXPECTED extra isomorph found at {key}")

    for key in expected_by_key.keys() & found.keys():
        expected_entry = expected_by_key[key]
        candidate, sig = found[key]

        expected_raw = expected_entry["pruning"].get("raw")
        if expected_raw is None:
            continue

        if candidate.length != expected_raw["length"]:
            errors.append(f"{key} raw.length: computed {candidate.length}, expected {expected_raw['length']}")
        if candidate.text_a != expected_raw["text_a"] or candidate.text_b != expected_raw["text_b"]:
            errors.append(
                f"{key} raw text: computed {candidate.text_a!r}/{candidate.text_b!r}, "
                f"expected {expected_raw['text_a']!r}/{expected_raw['text_b']!r}"
            )
        if sig.num_distinct_chars != expected_raw["num_distinct_chars"]:
            errors.append(
                f"{key} raw.num_distinct_chars: computed {sig.num_distinct_chars}, "
                f"expected {expected_raw['num_distinct_chars']}"
            )
        if not _isoclose(sig.expected_occurrences, expected_raw["expected_occurrences"]):
            errors.append(
                f"{key} raw.expected_occurrences: computed {sig.expected_occurrences:.6f}, "
                f"expected {expected_raw['expected_occurrences']:.6f}"
            )

        # shallow/deep are validated the same way once populated in the fixture.
        for mode in ("shallow", "deep"):
            if expected_entry["pruning"].get(mode) is not None:
                errors.append(f"{key} {mode}: fixture expects a result but pruning mode '{mode}' is not implemented")

    if errors:
        print(f"FAIL ({len(errors)} errors)")
        for err in errors[:50]:
            print(f"  {err}")
        if len(errors) > 50:
            print(f"  ... and {len(errors) - 50} more")
        return False

    print(f"PASS ({len(expected_by_key)} significant isomorphs matched)")
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
