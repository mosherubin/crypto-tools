"""
Standalone repetition search driver.
Usage: python run_find_repetitions.py --min-length 5 <ct-file> [<ct-file> ...]

Each <ct-file> is a plain text file containing one ciphertext. Whitespace is
silently ignored; every other character must belong to --alphabet.
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'Library'))

from find_repetitions import locate_repetitions, count_repetitions

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


def format_results(results: list) -> str:
    lines = ["REPETITIONS FOUND"]
    lines.append(f"{'MSG A':>6} {'MSG B':>6} {'POS A':>6} {'POS B':>6} {'LEN':>4}   TEXT")
    for r in sorted(results, key=lambda r: (-r.length, r.message_a, r.message_b, r.position_a)):
        lines.append(
            f"{r.message_a:>6} {r.message_b:>6} "
            f"{r.position_a + 1:>6} {r.position_b + 1:>6} "
            f"{r.length:>4}   {r.text}"
        )
    if not results:
        lines.append("(none found)")
    return "\n".join(lines)


def format_counts(counts: list) -> str:
    lines = ["REPETITION COUNTS (count > 2)"]
    lines.append(f"{'COUNT':>6}  TEXT")
    for c in counts:
        lines.append(f"{c.count:>6}  {c.text}")
    if not counts:
        lines.append("(none found)")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("inputs", nargs="+", help="Plain-text ciphertext files")
    parser.add_argument("--min-length", type=int, default=5)
    parser.add_argument("--alphabet", default=DEFAULT_ALPHABET)
    args = parser.parse_args()

    alphabet = args.alphabet.upper()
    ciphertexts = [load_ciphertext(path, alphabet) for path in args.inputs]

    for path, letters in zip(args.inputs, ciphertexts):
        print(f"{path}: {len(letters)} letters")
    print()

    results = locate_repetitions(ciphertexts, args.min_length)
    print(format_results(results))
    print()
    print(format_counts(count_repetitions(results)))


if __name__ == "__main__":
    main()
