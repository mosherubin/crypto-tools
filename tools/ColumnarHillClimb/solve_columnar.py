"""
Ciphertext-only columnar transposition solver, using hill climbing with
segment slide/swap transformations (Lasry thesis, Chapter 5). Supports both
complete (CCT) and incomplete (ICT) transposition rectangles; which case
applies falls out automatically from the ciphertext length and key length.

Tries every key length from <min_key_length> to <max_key_length> inclusive
(pass the same value for both to check a single key length), printing a
banner between each key length's trial.

Usage:
    python solve_columnar.py <ciphertext_file> <min_key_length> <max_key_length> <quadgram_file>
        [--restarts N] [--seed N] [--verbose]

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


def print_banner(key_length: int) -> None:
    line = "=" * BANNER_WIDTH
    print(line)
    print(f" KEY LENGTH {key_length} ".center(BANNER_WIDTH, "="))
    print(line)


def solve_for_key_length(ciphertext: str, key_length: int, scorer, restarts: int,
                          rng: random.Random, verbose: bool) -> None:
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
                print(f"restart {restart}: new best score {score:.2f}")
                print(decrypt(ciphertext, key))
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
    args = parser.parse_args()

    if args.min_key_length > args.max_key_length:
        parser.error("min_key_length must be <= max_key_length")

    counts = load_ngram_counts(args.quadgram_file)
    scorer = NgramScorer(counts)
    alphabet = alphabet_from_counts(counts)

    ciphertext = load_ciphertext(args.ciphertext_file, alphabet)
    print(f"Ciphertext length: {len(ciphertext)}")
    print()

    rng = random.Random(args.seed)
    for key_length in range(args.min_key_length, args.max_key_length + 1):
        print_banner(key_length)
        solve_for_key_length(ciphertext, key_length, scorer, args.restarts, rng, args.verbose)


if __name__ == "__main__":
    main()
