"""
Ciphertext-only columnar transposition solver, using hill climbing with
segment slide/swap transformations (Lasry thesis, Chapter 5). Supports both
complete (CCT) and incomplete (ICT) transposition rectangles; which case
applies falls out automatically from the ciphertext length and key length.

Tries every key length from <min_key_length> to <max_key_length> inclusive
(pass the same value for both to check a single key length), printing a
banner between each key length's trial.

With --try-bisection and/or --try-reversal, also tries cheap procedural
variants of the ciphertext -- covering tricks like transmitting a message
in two swapped halves, or reversed end-to-end -- before concluding a
ciphertext is unsolved by this algorithm. The untransformed ciphertext is
always tried. Enabling one of the two flags tries that transform in
addition; enabling both tries every combination (as-is, bisected, reversed,
and bisected-then-reversed). Bisection splits the ciphertext into two
halves and swaps their order; for an odd length, both conventions for which
half gets the extra character are tried, since there's no way to know which
one the original encipherer (if any) used.

Usage:
    python solve_columnar.py <ciphertext_file> <min_key_length> <max_key_length> <quadgram_file>
        [--restarts N] [--seed N] [--verbose] [--heartbeat N]
        [--try-bisection] [--try-reversal]

<ciphertext_file> is a plain text file (whitespace ignored); every other
character must appear in <quadgram_file>'s alphabet. Hebrew final-form
letters are normalized to their base letter before matching.

<quadgram_file> is a plain text file, one quadgram per line:
    <4-character quadgram><whitespace><occurrence count>
"""

import argparse
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'Library'))

from columnar_hillclimb import hill_climb
from columnar_transposition import decrypt
from hebrew_text import normalize_finals
from ngram_scoring import NgramScorer, alphabet_from_counts, load_ngram_counts

BANNER_WIDTH = 70


def load_ciphertext(path: str, alphabet: set) -> str:
    with open(path, encoding='utf-8') as f:
        raw = f.read()

    letters = []
    for ch in raw:
        if ch.isspace():
            continue
        folded = normalize_finals(ch)
        if folded not in alphabet:
            raise ValueError(f"Invalid character {ch!r} in {path}: not in the quadgram file's alphabet")
        letters.append(folded)
    return ''.join(letters)


def print_banner(text: str) -> None:
    line = "=" * BANNER_WIDTH
    print(line)
    print(f" {text} ".center(BANNER_WIDTH, "="))
    print(line)


def bisect_text(text: str) -> list:
    """Split text into two halves and swap their order (so B+A). For an odd
    length there's no even split, so both conventions for which half gets
    the extra character are returned."""
    n = len(text)
    if n % 2 == 0:
        half = n // 2
        return [text[half:] + text[:half]]

    lower, upper = n // 2, n // 2 + 1
    first_half_longer = text[upper:] + text[:upper]
    second_half_longer = text[lower:] + text[:lower]
    return [first_half_longer, second_half_longer]


def build_ciphertext_variants(ciphertext: str, try_bisection: bool, try_reversal: bool) -> list:
    """Returns (label, text) pairs for every combination of the enabled
    transforms, always including the untransformed ciphertext."""
    variants = [("as-is", ciphertext)]

    bisected = bisect_text(ciphertext) if try_bisection else []
    for i, text in enumerate(bisected):
        label = "bisected" if len(bisected) == 1 else f"bisected (split variant {i + 1})"
        variants.append((label, text))

    if try_reversal:
        variants.append(("reversed", ciphertext[::-1]))
        for i, text in enumerate(bisected):
            label = "bisected+reversed" if len(bisected) == 1 else f"bisected+reversed (split variant {i + 1})"
            variants.append((label, text[::-1]))

    return variants


def solve_for_key_length(ciphertext: str, key_length: int, scorer, restarts: int,
                          rng: random.Random, verbose: bool, heartbeat: int) -> None:
    rows, long_columns = divmod(len(ciphertext), key_length)
    if long_columns == 0:
        print(f"Complete rectangle (CCT): {rows} rows")
    else:
        print(f"Incomplete rectangle (ICT): {rows} full rows, {long_columns} long columns")
    print()

    best_key, best_score = None, float('-inf')
    for restart in range(restarts):
        key, score = hill_climb(ciphertext, key_length, scorer, rng)
        if score > best_score:
            best_key, best_score = key, score
            if verbose:
                print(f"restart {restart + 1}: new best score {score:.2f}")
                print(decrypt(ciphertext, key))
                print()

        restart_number = restart + 1
        if heartbeat > 0 and restart_number % heartbeat == 0:
            print(f"[heartbeat] restart {restart_number}/{restarts}, best score so far: {best_score:.2f}")

    print()
    key_1indexed = tuple(k + 1 for k in best_key)
    print("Best key (1-indexed):", key_1indexed)
    print(f"Score: {best_score:.2f}")
    print()
    print(decrypt(ciphertext, best_key))
    print()


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("ciphertext_file")
    parser.add_argument("min_key_length", type=int)
    parser.add_argument("max_key_length", type=int)
    parser.add_argument("quadgram_file")
    parser.add_argument("--restarts", type=int, default=50)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--verbose", action="store_true", help="Print every new best result as restarts progress")
    parser.add_argument("--heartbeat", type=int, default=5,
                         help="Print progress every N restarts, 0 to disable (default: 5)")
    parser.add_argument("--try-bisection", action="store_true",
                         help="Also try the ciphertext split into two halves with their order swapped")
    parser.add_argument("--try-reversal", action="store_true",
                         help="Also try the ciphertext reversed end-to-end")
    args = parser.parse_args()

    if args.min_key_length > args.max_key_length:
        parser.error("min_key_length must be <= max_key_length")

    counts = load_ngram_counts(args.quadgram_file)
    scorer = NgramScorer(counts)
    alphabet = alphabet_from_counts(counts)

    ciphertext = load_ciphertext(args.ciphertext_file, alphabet)
    print(f"Ciphertext length: {len(ciphertext)}")
    print()

    variants = build_ciphertext_variants(ciphertext, args.try_bisection, args.try_reversal)

    rng = random.Random(args.seed)
    for label, variant_text in variants:
        if len(variants) > 1:
            print_banner(f"CIPHERTEXT VARIANT: {label}")
            print(f"Variant length: {len(variant_text)}")
            print()
        for key_length in range(args.min_key_length, args.max_key_length + 1):
            print_banner(f"KEY LENGTH {key_length}")
            solve_for_key_length(variant_text, key_length, scorer, args.restarts, rng, args.verbose, args.heartbeat)


if __name__ == "__main__":
    main()
