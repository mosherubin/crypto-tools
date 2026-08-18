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

Every restart's result, across every variant and key length tried, is a
candidate for a running top-N leaderboard (see --top-n); once everything
finishes, the N best-scoring results seen anywhere in the run are printed
together, best first -- useful for spotting a promising near-miss even when
nothing fully solves.

Usage:
    python solve_columnar.py <ciphertext_file> <min_key_length> <max_key_length> <quadgram_file>
        [--restarts N] [--seed N] [--verbose] [--heartbeat N]
        [--try-bisection] [--try-reversal] [--top-n N] [--rtl]

<ciphertext_file> is a plain text file (whitespace ignored); every other
character must appear in <quadgram_file>'s alphabet. Hebrew final-form
letters are normalized to their base letter before matching.

<quadgram_file> is a plain text file, one quadgram per line:
    <4-character quadgram><whitespace><occurrence count>
"""

import argparse
import heapq
import itertools
import os
import random
import sys
from datetime import datetime

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


def format_key(key: list, rtl: bool) -> tuple:
    """1-indexed key, for display only -- decryption always uses the raw
    0-indexed key regardless of rtl. For rtl, the key is printed in reverse
    order to match reading columns right-to-left."""
    key_1indexed = tuple(k + 1 for k in key)
    return tuple(reversed(key_1indexed)) if rtl else key_1indexed


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


class TopResults:
    """Tracks the N best-scoring restart results seen anywhere in the run,
    across every ciphertext variant and key length -- without duplicate
    entries when more than one restart converges on the same (variant, key
    length, key) result, which happens routinely once a key length actually
    solves the cipher. Backed by a min-heap of size <= capacity, so
    considering a result costs O(log N) and never requires decrypting a
    candidate that won't make the cut."""

    def __init__(self, capacity: int):
        self.capacity = capacity
        self._heap = []
        self._identities = set()  # (variant_label, key_length, key) already present in _heap
        self._tie_breaker = itertools.count()  # avoids ever comparing two entries' key/plaintext

    def consider(self, score: float, key_length: int, key: list, variant_label: str, ciphertext: str) -> None:
        if self.capacity <= 0:
            return
        identity = (variant_label, key_length, tuple(key))
        if identity in self._identities:
            return  # this exact result is already represented in the list

        makes_the_cut = len(self._heap) < self.capacity or score > self._heap[0][0]
        if not makes_the_cut:
            return

        plaintext = decrypt(ciphertext, key)
        entry = (score, next(self._tie_breaker), key_length, tuple(key), variant_label, plaintext)
        if len(self._heap) < self.capacity:
            heapq.heappush(self._heap, entry)
        else:
            evicted = heapq.heapreplace(self._heap, entry)
            self._identities.discard((evicted[4], evicted[2], evicted[3]))
        self._identities.add(identity)

    def best_first(self) -> list:
        return sorted(self._heap, key=lambda entry: entry[0], reverse=True)


def print_top_results(top_results: TopResults, rtl: bool) -> None:
    entries = top_results.best_first()
    if not entries:
        return

    print_banner(f"TOP {len(entries)} RESULT{'S' if len(entries) != 1 else ''}")
    for rank, (score, _, key_length, key, variant_label, plaintext) in enumerate(entries, start=1):
        key_display = format_key(key, rtl)
        print(f"#{rank}  score={score:.2f}  variant={variant_label}  key_length={key_length}  key={key_display}")
        print(f"    {plaintext}")
        print()


def solve_for_key_length(ciphertext: str, key_length: int, scorer, restarts: int, rng: random.Random,
                          verbose: bool, heartbeat: int, top_results: TopResults, variant_label: str,
                          rtl: bool) -> None:
    rows, long_columns = divmod(len(ciphertext), key_length)
    if long_columns == 0:
        print(f"Complete rectangle (CCT): {rows} rows")
    else:
        print(f"Incomplete rectangle (ICT): {rows} full rows, {long_columns} long columns")
    print()

    best_key, best_score = None, float('-inf')
    for restart in range(restarts):
        key, score = hill_climb(ciphertext, key_length, scorer, rng)
        top_results.consider(score, key_length, key, variant_label, ciphertext)
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
    key_display = format_key(best_key, rtl)
    print("Best key (1-indexed):", key_display)
    print(f"Score: {best_score:.2f}")
    print()
    print(decrypt(ciphertext, best_key))
    print()


# argparse converts hyphens in a flag's name to underscores for attribute
# access (e.g. --top-n -> args.top_n); these are the only options where that
# matters for display, since the rest are already single words or were
# defined with underscores directly (the positional arguments).
CLI_DISPLAY_NAME_OVERRIDES = {
    "top_n": "top-n",
    "try_bisection": "try-bisection",
    "try_reversal": "try-reversal",
}


def print_args_summary(args: argparse.Namespace) -> None:
    """Every CLI option's value, name sorted ascending, values aligned in a
    column -- printed first, before any other output."""
    def format_value(value):
        if isinstance(value, bool):
            return "true" if value else "false"
        return str(value)

    rows = sorted(
        (CLI_DISPLAY_NAME_OVERRIDES.get(dest, dest), format_value(value))
        for dest, value in vars(args).items()
    )
    name_width = max(len(name) for name, _ in rows) + 2
    for name, value in rows:
        print(f"{name:<{name_width}}{value}")
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
    parser.add_argument("--top-n", type=int, default=10,
                         help="Number of best results (across every variant and key length) to report at the "
                              "end, 0 to disable (default: 10)")
    parser.add_argument("--rtl", action="store_true",
                         help="Right-to-left language: printed keys are reversed to match reading columns "
                              "right-to-left (decryption itself is unaffected)")
    args = parser.parse_args()

    if args.min_key_length > args.max_key_length:
        parser.error("min_key_length must be <= max_key_length")

    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print()
    print_args_summary(args)

    counts = load_ngram_counts(args.quadgram_file)
    scorer = NgramScorer(counts)
    alphabet = alphabet_from_counts(counts)

    ciphertext = load_ciphertext(args.ciphertext_file, alphabet)
    print(f"Ciphertext length: {len(ciphertext)}")
    print()

    variants = build_ciphertext_variants(ciphertext, args.try_bisection, args.try_reversal)
    top_results = TopResults(args.top_n)

    rng = random.Random(args.seed)
    for label, variant_text in variants:
        if len(variants) > 1:
            print_banner(f"CIPHERTEXT VARIANT: {label}")
            print(f"Variant length: {len(variant_text)}")
            print()
        for key_length in range(args.min_key_length, args.max_key_length + 1):
            print_banner(f"KEY LENGTH {key_length}")
            solve_for_key_length(variant_text, key_length, scorer, args.restarts, rng, args.verbose,
                                  args.heartbeat, top_results, label, args.rtl)

    print_top_results(top_results, args.rtl)


if __name__ == "__main__":
    main()
