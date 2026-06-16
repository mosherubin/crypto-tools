#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CheckTetragram.py — Look up a (possibly wildcard) tetragram against the
frequency data used by the Quagmire solver.

Usage:
    python CheckTetragram.py <tetragram> <grade_cutoff>

Arguments:
    tetragram      Four characters, A-Z or '.' for wildcard (e.g. "..QE", "TION").
    grade_cutoff   A single letter A-Z.  Grades *above* this are considered valid
                   (same semantics as 'tetragram_grade_cutoff' in SolveQuagmire).

Examples:
    python CheckTetragram.py TION A    -> True; TION and its grade
    python CheckTetragram.py ..QE A    -> True/False; list all xxQE above cutoff
    python CheckTetragram.py ..QE B    -> stricter: only grades C and above qualify
"""

import os
import sys
from itertools import product as itertools_product

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'Library'))
from reconstruction_matrix import is_tetragram_valid

_TETRAGRAM_DATA_FILE = os.path.join(
    os.path.dirname(__file__), '..', 'Library', 'tetragram_frequency_data.txt')


def load_data():
    with open(_TETRAGRAM_DATA_FILE, 'r', encoding='utf-8') as fh:
        return fh.read().strip()


def grade_at(data, c0, c1, c2, c3):
    """Return the frequency grade character for the tetragram (c0..c3 are 0-based ints)."""
    return data[c0 * 17576 + c1 * 676 + c2 * 26 + c3]


def expand_matches(tetragram, cutoff, data):
    """
    Return a sorted list of (grade, expanded_tetragram) pairs for every
    concrete expansion of `tetragram` whose grade is strictly above `cutoff`.
    Wildcards ('.') are substituted with every letter A-Z.
    """
    tetragram = tetragram.upper()
    cutoff    = cutoff.upper()

    wildcard_positions = [i for i, ch in enumerate(tetragram) if ch == '.']
    fixed              = [None if ch == '.' else ord(ch) - 65
                          for ch in tetragram]

    matches = []
    for vals in itertools_product(range(26), repeat=len(wildcard_positions)):
        chars = list(fixed)
        for pos, val in zip(wildcard_positions, vals):
            chars[pos] = val
        grade = grade_at(data, *chars)
        if grade > cutoff:
            matches.append((grade, ''.join(chr(65 + c) for c in chars)))

    matches.sort(key=lambda x: (-ord(x[0]), x[1]))   # best grade first, alpha within grade
    return matches


def main():
    if len(sys.argv) != 3:
        print("Usage: CheckTetragram.py <tetragram> <grade_cutoff>", file=sys.stderr)
        print("  tetragram   : 4 characters, A-Z or '.' for wildcard", file=sys.stderr)
        print("  grade_cutoff: single letter A-Z", file=sys.stderr)
        sys.exit(1)

    raw_tg, raw_cutoff = sys.argv[1], sys.argv[2]

    # --- Validate tetragram ---
    tg = raw_tg.upper()
    if len(tg) != 4:
        print("ERROR: tetragram must be exactly 4 characters; got {!r}.".format(raw_tg),
              file=sys.stderr)
        sys.exit(1)
    for ch in tg:
        if ch != '.' and not ('A' <= ch <= 'Z'):
            print("ERROR: tetragram contains invalid character {!r}; "
                  "only A-Z and '.' are allowed.".format(ch), file=sys.stderr)
            sys.exit(1)

    # --- Validate cutoff ---
    if len(raw_cutoff) != 1 or not ('A' <= raw_cutoff.upper() <= 'Z'):
        print("ERROR: grade_cutoff must be a single letter A-Z; got {!r}.".format(raw_cutoff),
              file=sys.stderr)
        sys.exit(1)
    cutoff = raw_cutoff.upper()

    # --- Call is_tetragram_valid for the official verdict ---
    cache  = {}
    result = is_tetragram_valid(tg, cache, cutoff=cutoff)

    dot_count = tg.count('.')

    print("Tetragram : {}".format(tg))
    print("Cutoff    : {} (grades above '{}' are valid)".format(cutoff, cutoff))
    print("Valid     : {}".format(result))
    print()

    if not result:
        if dot_count >= 3:
            # should never reach here (always True), but handle gracefully
            print("(Result is always True for 3+ wildcards.)")
        else:
            print("No expansions of {!r} have a grade above {!r}.".format(tg, cutoff))
        return

    # --- List all matching expansions ---
    data = cache['data']   # already loaded by is_tetragram_valid

    if dot_count == 0:
        # Single tetragram — just show its grade
        c = [ord(ch) - 65 for ch in tg]
        grade = grade_at(data, *c)
        print("Grade: {}".format(grade))
    elif dot_count >= 3:
        print("(3 or more wildcards — result is always True; "
              "listing {} expansions would be impractical.)".format(26 ** dot_count))
    else:
        matches = expand_matches(tg, cutoff, data)
        print("{} expansion(s) above cutoff {!r}:".format(len(matches), cutoff))
        print()
        # Print in columns: grade then tetragram, grouped by grade
        current_grade = None
        for grade, expanded in matches:
            if grade != current_grade:
                current_grade = grade
                print("  Grade {}:".format(grade))
            print("    {}".format(expanded))


if __name__ == "__main__":
    main()
