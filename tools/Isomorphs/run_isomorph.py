"""
Standalone isomorph search driver.
Usage: python run_isomorph.py --min-isolen 8 --max-expected 10 --pruning raw shallow deep <ct-file> [<ct-file> ...]

Each <ct-file> is a plain text file containing one ciphertext. Whitespace is
silently ignored; every other character must belong to --alphabet.
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'Library'))

from isomorph_search import locate_isomorphs, prune_candidates, PRUNE_MODES
from isomorph_evaluation import evaluate_isomorph

DEFAULT_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

# Output order is fixed regardless of the order --pruning is given in.
MODE_DISPLAY_ORDER = ('deep', 'shallow', 'raw')
MODE_HEADINGS = {'raw': 'RAW (NO PRUNING)', 'shallow': 'SHALLOW PRUNING', 'deep': 'DEEP PRUNING'}


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


def find_significant_isomorphs_for_mode(candidates: list, mode: str, ciphertexts: list, alphabet_size: int,
                                         min_isolen: int, max_expected: float) -> list:
    """Prune (per mode) and evaluate a pre-located candidate list, returning only
    the significant ones as (candidate, significance) pairs."""
    results = []
    for pruned in prune_candidates(candidates, mode, min_isolen):
        self_search = pruned.message_a == pruned.message_b
        significance = evaluate_isomorph(
            pruned.text_a, alphabet_size,
            len(ciphertexts[pruned.message_a]), len(ciphertexts[pruned.message_b]),
            self_search, max_expected,
        )
        if significance.significant:
            results.append((pruned, significance))

    return results


def format_results(results: list, min_isolen: int, max_expected: float) -> str:
    lines = [f"SIGNIFICANT ISOMORPHS  (minimum length {min_isolen}, maximum expected {max_expected})"]
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


def format_report(candidates: list, modes: list, ciphertexts: list, alphabet_size: int,
                   min_isolen: int, max_expected: float) -> str:
    sections = []
    for mode in MODE_DISPLAY_ORDER:
        if mode not in modes:
            continue
        results = find_significant_isomorphs_for_mode(
            candidates, mode, ciphertexts, alphabet_size, min_isolen, max_expected
        )
        heading = MODE_HEADINGS[mode]
        sep = '=' * 80
        sections.append(f"{sep}\n{heading}\n{sep}\n{format_results(results, min_isolen, max_expected)}")
    return "\n\n".join(sections)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("inputs", nargs="+", help="Plain-text ciphertext files")
    parser.add_argument("--min-isolen", type=int, default=8)
    parser.add_argument("--max-expected", type=float, default=10.0)
    parser.add_argument("--alphabet", default=DEFAULT_ALPHABET)
    parser.add_argument("--pruning", nargs="+", choices=PRUNE_MODES, default=["raw"],
                         help="One or more of: raw shallow deep (default: raw)")
    args = parser.parse_args()

    alphabet = args.alphabet.upper()
    ciphertexts = [load_ciphertext(path, alphabet) for path in args.inputs]

    for path, letters in zip(args.inputs, ciphertexts):
        print(f"{path}: {len(letters)} letters")
    print()

    candidates = locate_isomorphs(ciphertexts, args.min_isolen)
    print(format_report(candidates, args.pruning, ciphertexts, len(alphabet), args.min_isolen, args.max_expected))


if __name__ == "__main__":
    main()
