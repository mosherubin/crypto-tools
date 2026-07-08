"""
Standalone isomorph search driver.
Usage: python run_isomorph.py --min-isolen 8 --max-expected 10 <ct-file> [<ct-file> ...]

Each <ct-file> is a plain text file containing one ciphertext. Whitespace is
silently ignored; every other character must belong to --alphabet.
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'Library'))

from isomorph_search import locate_isomorphs
from isomorph_evaluation import evaluate_isomorph

DEFAULT_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def load_ciphertext(path: str, alphabet: str) -> str:
    with open(path, encoding='utf-8') as f:
        raw = f.read()

    letters = []
    for ch in raw:
        if ch.isspace():
            continue
        folded = ch.upper()
        if folded not in alphabet:
            raise ValueError(f"Invalid character {ch!r} in {path}: not in alphabet {alphabet!r}")
        letters.append(folded)

    return ''.join(letters)


def find_significant_isomorphs(ciphertexts: list, alphabet_size: int,
                                min_isolen: int, max_expected: float) -> list:
    """Locate and evaluate isomorphs across a list of ciphertext strings, returning
    only the significant ones as (candidate, significance) pairs."""
    candidates = locate_isomorphs(ciphertexts, min_isolen)

    results = []
    for candidate in candidates:
        self_search = candidate.message_a == candidate.message_b
        significance = evaluate_isomorph(
            candidate.text_a, alphabet_size,
            len(ciphertexts[candidate.message_a]), len(ciphertexts[candidate.message_b]),
            self_search, max_expected,
        )
        if significance.significant:
            results.append((candidate, significance))

    return results


def format_results(results: list) -> str:
    lines = ["SIGNIFICANT ISOMORPHS"]
    lines.append(f"{'MSG A':>6} {'MSG B':>6} {'POS A':>6} {'POS B':>6} {'LEN':>4} {'EXPECTED':>12}   STRINGS")
    for candidate, significance in sorted(results, key=lambda r: r[1].expected_occurrences):
        lines.append(
            f"{candidate.message_a:>6} {candidate.message_b:>6} "
            f"{candidate.position_a + 1:>6} {candidate.position_b + 1:>6} "
            f"{candidate.length:>4} {significance.expected_occurrences:>12.4f}   "
            f"{candidate.text_a} / {candidate.text_b}"
        )
    if not results:
        lines.append("(none found)")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("inputs", nargs="+", help="Plain-text ciphertext files")
    parser.add_argument("--min-isolen", type=int, default=8)
    parser.add_argument("--max-expected", type=float, default=10.0)
    parser.add_argument("--alphabet", default=DEFAULT_ALPHABET)
    args = parser.parse_args()

    alphabet = args.alphabet.upper()
    ciphertexts = [load_ciphertext(path, alphabet) for path in args.inputs]

    for path, letters in zip(args.inputs, ciphertexts):
        print(f"{path}: {len(letters)} letters")
    print()

    results = find_significant_isomorphs(ciphertexts, len(alphabet), args.min_isolen, args.max_expected)
    print(format_results(results))


if __name__ == "__main__":
    main()
