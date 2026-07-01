#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Polyalphabetic Reconstruction Matrix - Stage 4
Reads, validates, and prints a reconstruction matrix from STDIN,
finds complete and incomplete rectangles, then applies indirect symmetry
of position to fill in unknown letters, iterating until no new letters
are discovered.

Input format (one row per line, blank lines ignored):
    <name> <alphabet>
where:
  - <name>     is any whitespace-free string; names must be unique
  - <alphabet> is a string of length N composed of A-Z (case-insensitive)
               and/or '.' (unknown); no A-Z letter may appear more than once
               per row; all rows must share the same length N
"""

import argparse
import sys
from datetime import datetime

# Allow the Library folder to be found when running from any working directory.
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'Library'))

from reconstruction_matrix import (
    parse_and_validate,
    validate_matrix,
    validate_k3_matrix,
    print_matrix,
    print_matrix_from_alphabets,
    find_rectangles,
    find_incomplete_rectangles,
    parse_rect_string,
    apply_indirect_symmetry,
    MatrixContradiction,
)


def main():
    parser = argparse.ArgumentParser(
        description="Complete a polyalphabetic reconstruction matrix using "
                    "indirect symmetry of position.")
    parser.add_argument(
        "--ignore",
        metavar="LINE_NAME",
        action="append",
        default=[],
        help="Name of a line to ignore (may be specified multiple times).")
    parser.add_argument(
        "--allow_row_dups",
        action="store_true",
        default=False,
        help="Allow a letter to appear more than once in the same row.")
    parser.add_argument(
        "--allow_col_dups",
        action="store_true",
        default=False,
        help="Allow a letter to appear more than once in the same column.")
    parser.add_argument(
        "--k3",
        action="store_true",
        default=False,
        help="Enable K3 mode.")
    args = parser.parse_args()

    ignored        = set(args.ignore)
    allow_row_dups = args.allow_row_dups
    allow_col_dups = args.allow_col_dups
    is_k3          = args.k3

    try:
        rows = parse_and_validate(sys.stdin.readlines())
    except ValueError as exc:
        print("ERROR: {}".format(exc), file=sys.stderr)
        sys.exit(1)

    known_names = {name for name, _ in rows}
    for name in ignored:
        if name not in known_names:
            print("ERROR: --ignore {!r} does not match any line name in the input.".format(name),
                  file=sys.stderr)
            sys.exit(1)

    if ignored:
        rows = [(name, alpha) for name, alpha in rows if name not in ignored]
        print("Ignoring line(s): {}".format(", ".join(sorted(ignored))))
        print()

    ok, reason = validate_matrix(rows)
    if not ok:
        print("VALIDATION ERROR: {}".format(reason), file=sys.stderr)
        sys.exit(1)

    ok, reason = validate_k3_matrix(rows, is_k3)
    if not ok:
        print("K3 VALIDATION ERROR: {}".format(reason), file=sys.stderr)
        sys.exit(1)

    start_time = datetime.now()
    print("Start time: {}".format(start_time.strftime("%Y-%m-%d %H:%M:%S")))
    print()

    print("=== Initial Matrix ===")
    print_matrix(rows)
    print()

    pass_num = 0
    while True:
        pass_num += 1
        print("=== Pass {} ===".format(pass_num))

        rectangles, rect_index, _ = find_rectangles(rows, is_k3=is_k3)
        print("Complete rectangles: {}".format(len(rectangles)))

        incomplete = find_incomplete_rectangles(rows, is_k3=is_k3)
        print("Incomplete rectangles: {}".format(len(incomplete)))
        print()

        try:
            rows, new_letters = apply_indirect_symmetry(
                rows, rectangles, rect_index, incomplete,
                allow_row_dups=allow_row_dups,
                allow_col_dups=allow_col_dups,
                is_k3=is_k3)
        except MatrixContradiction as exc:
            print("CONTRADICTION: {}".format(exc))
            print()
            print("Matrix at point of error:")
            print_matrix(rows)
            sys.exit(1)

        print()
        print("New letters added this pass: {}".format(new_letters))
        print()

        if new_letters == 0:
            print("No new letters found. Stopping.")
            break

        print("=== Interim Matrix ===")
        print_matrix(rows)
        print()

    print()
    print("=== Final Matrix ===")
    print_matrix(rows)

    # Remove duplicate columns (columns that are identical across all rows).
    n_cols = len(rows[0][1])
    seen_cols = {}   # col_tuple -> first 1-based position that had it
    keep = []        # 0-based indices of columns to retain
    for col in range(n_cols):
        col_tuple = tuple(alpha[col] for _, alpha in rows)
        if col_tuple not in seen_cols:
            seen_cols[col_tuple] = col + 1
            keep.append(col)

    dropped = n_cols - len(keep)
    if dropped:
        dedup_rows = [(name, ''.join(alpha[c] for c in keep))
                      for name, alpha in rows]
        header_row = [('0', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'[:len(keep)])]
        dropped_positions = [c + 1 for c in range(n_cols) if c not in set(keep)]
        print()
        print("=== Deduplicated Matrix ({} duplicate column(s) removed: {}) ===".format(
            dropped, ", ".join(str(p) for p in dropped_positions)))
        print_matrix(header_row + dedup_rows)
    else:
        print()
        print("(No duplicate columns found.)")

    end_time = datetime.now()
    print()
    print("End time:   {}".format(end_time.strftime("%Y-%m-%d %H:%M:%S")))
    print("Elapsed:    {}".format(end_time - start_time))


if __name__ == "__main__":
    main()
