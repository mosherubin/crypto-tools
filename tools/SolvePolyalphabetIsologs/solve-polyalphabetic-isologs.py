#!/usr/bin/env python3
"""
Cryptanalysis of two periodic polyalphabetic ISOLOG messages
(two ciphertexts whose underlying plaintexts are identical), using the
method described in Abraham Sinkov's "Elementary Cryptanalysis",
section 3.8, pp. 96-110.

Stage 1: Command-line input and validation.
Stage 2: Diagonal insertion of both messages into a 2-D array.
Stage 3: Compress the array by merging columns that share a character
         in the same row, repeating until no merges remain.
"""

import argparse
import sys

# Placeholder used for cells of the array that hold no character.
EMPTY = "."


def parse_arguments():
    """Define and parse the four mandatory command-line options."""
    parser = argparse.ArgumentParser(
        description="Solve two periodic polyalphabetic isolog messages "
                    "(Sinkov, Elementary Cryptanalysis, sec. 3.8)."
    )
    parser.add_argument(
        "--message1", required=True,
        help="First polyalphabetic ciphertext message. "
             "Quote it if it contains spaces."
    )
    parser.add_argument(
        "--period1", required=True, type=int,
        help="Period of message1 (number of alphabets used to encrypt it)."
    )
    parser.add_argument(
        "--message2", required=True,
        help="Second polyalphabetic ciphertext message. "
             "Quote it if it contains spaces."
    )
    parser.add_argument(
        "--period2", required=True, type=int,
        help="Period of message2 (number of alphabets used to encrypt it)."
    )
    return parser.parse_args()


def strip_whitespace(text):
    """Remove ALL whitespace characters (spaces, tabs, newlines) from text."""
    return "".join(text.split())


def build_array(message1, period1, message2, period2):
    """
    Build the (period1 + period2) x N array and fill both messages
    diagonally.

      * message1 occupies rows 0 .. period1-1.
        Character i of message1 is placed at (row = i % period1, col = i).

      * message2 occupies rows period1 .. period1+period2-1.
        Character i of message2 is placed at
        (row = period1 + (i % period2), col = i).

    Every cell not on one of these diagonals keeps the EMPTY placeholder.
    """
    n = len(message1)               # equal to len(message2), already validated
    n_rows = period1 + period2
    array = [[EMPTY for _ in range(n)] for _ in range(n_rows)]

    # ---- message1: diagonals through rows 0 .. period1-1 ----
    for i, ch in enumerate(message1):
        row = i % period1
        array[row][i] = ch

    # ---- message2: diagonals through rows period1 .. period1+period2-1 ----
    for i, ch in enumerate(message2):
        row = period1 + (i % period2)
        array[row][i] = ch

    return array


def print_array(array, period1):
    """Print the array with a column ruler, row labels, and a block divider."""
    n_rows = len(array)
    n_cols = len(array[0]) if n_rows else 0

    row_label_w = len(str(n_rows - 1)) if n_rows else 1
    prefix_pad = " " * (row_label_w + 2)   # aligns ruler with "NN: " row prefix

    # Column ruler: a "tens" line above a "units" line.
    tens = "".join(
        str((c // 10) % 10) if c >= 10 else " " for c in range(n_cols)
    )
    units = "".join(str(c % 10) for c in range(n_cols))
    print(f"{prefix_pad}{tens}")
    print(f"{prefix_pad}{units}")

    for r in range(n_rows):
        # Divider between the message1 block and the message2 block.
        if r == period1:
            print(f"{prefix_pad}{'-' * n_cols}")
        line = "".join(array[r])
        print(f"{r:>{row_label_w}}: {line}")


def find_merge_pair(array):
    """
    Return (i, j) with i < j: the first column pair that shares a
    non-empty character in the same row, or None if no such pair exists.

    Scan order: earlier column i ascending, then later column j ascending.
    """
    n_rows = len(array)
    n_cols = len(array[0]) if n_rows else 0
    for i in range(n_cols):
        for j in range(i + 1, n_cols):
            for r in range(n_rows):
                a = array[r][i]
                if a != EMPTY and a == array[r][j]:
                    return (i, j)
    return None


def merge_columns(array, i, j):
    """
    Merge the later column j into the earlier column i (i < j):

      * Copy every non-empty cell of column j into column i.
      * A conflict (column i already holds a *different* non-empty
        character in the same row) is fatal: report it and stop.
      * Finally remove column j from every row (width shrinks by one;
        no rows are removed).
    """
    n_rows = len(array)

    # Pass 1: detect any conflict before mutating anything, so that on
    # error we stop immediately with the array left intact.
    for r in range(n_rows):
        cj = array[r][j]
        if cj == EMPTY:
            continue
        ci = array[r][i]
        if ci != EMPTY and ci != cj:
            print(
                f"Error: merge conflict while merging column {j} into "
                f"column {i}. Row {r} holds '{ci}' in column {i} but "
                f"'{cj}' in column {j}. Stopping immediately.",
                file=sys.stderr,
            )
            sys.exit(1)

    # Pass 2: copy non-empty cells from column j into column i.
    for r in range(n_rows):
        if array[r][j] != EMPTY:
            array[r][i] = array[r][j]

    # Delete column j from every row.
    for r in range(n_rows):
        del array[r][j]


def compress_array(array):
    """
    Repeatedly merge the leftmost mergeable column pair until a full scan
    finds nothing to merge. Returns the number of merges performed.
    """
    merges = 0
    while True:
        pair = find_merge_pair(array)
        if pair is None:
            break
        merge_columns(array, pair[0], pair[1])
        merges += 1
    return merges


def main():
    args = parse_arguments()

    # Clean both messages by removing every whitespace character.
    message1 = strip_whitespace(args.message1)
    message2 = strip_whitespace(args.message2)
    period1 = args.period1
    period2 = args.period2

    # The two isologs must contain the same number of characters.
    if len(message1) != len(message2):
        print(
            "Error: the two messages have unequal length after whitespace "
            "removal "
            f"(message1 = {len(message1)} characters, "
            f"message2 = {len(message2)} characters). "
            "Isolog messages must be the same length.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Data validated -- echo each message with its period.
    print(f"Message 1 (period {period1}): {message1}")
    print(f"Message 2 (period {period2}): {message2}")
    print()

    # Build the diagonal-filled array and display it for inspection.
    array = build_array(message1, period1, message2, period2)
    print(f"Initial array: {period1 + period2} rows x {len(message1)} columns "
          f"(rows 0..{period1 - 1} = message1, "
          f"rows {period1}..{period1 + period2 - 1} = message2)")
    print()
    print_array(array, period1)

    # Stage 3: compress the array by merging columns that share a
    # character in the same row, until no further merges are possible.
    merges = compress_array(array)
    print()
    print(f"Compressed array after {merges} merge(s): "
          f"{len(array)} rows x {len(array[0])} columns")
    print()
    print_array(array, period1)


if __name__ == "__main__":
    main()












































































































































