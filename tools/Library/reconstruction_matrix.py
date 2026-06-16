#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Shared library for polyalphabetic reconstruction matrix tools.

Provides parsing, validation, display, and rectangle-finding utilities
used by scripts that work with Quagmire/periodic-polyalphabetic ciphers.
"""

import os
import re
import sys
from datetime import datetime
from itertools import product as itertools_product


# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------

class MatrixContradiction(Exception):
    """
    Raised when a contradiction is detected during matrix expansion.
    Callers doing backtracking search should catch this and try the next
    candidate; callers that treat contradictions as fatal should catch it
    and exit.
    """
    pass


# ---------------------------------------------------------------------------
# Parsing and validation
# ---------------------------------------------------------------------------

def parse_and_validate(lines):
    """
    Parse and validate input lines.

    Returns a list of (name, alphabet) pairs where each alphabet is an
    uppercase string of A-Z and '.' characters, all of the same length.
    """
    rows = []
    seen_names = set()
    expected_length = None

    for raw in lines:
        stripped = raw.strip()
        if not stripped:
            continue
        if stripped.startswith('#'):
            continue

        parts = stripped.split()
        if len(parts) != 2:
            raise ValueError(
                "Each non-blank line must have exactly two whitespace-delimited "
                "tokens (name + alphabet); got: {!r}".format(stripped)
            )

        name, alphabet_raw = parts
        alphabet = alphabet_raw.upper()

        for ch in alphabet:
            if ch != '.' and not ('A' <= ch <= 'Z'):
                raise ValueError(
                    "Row {!r}: alphabet contains invalid character {!r}; "
                    "only A-Z and '.' are allowed.".format(name, ch)
                )

        letters = [ch for ch in alphabet if ch != '.']
        seen_letters = set()
        for ch in letters:
            if ch in seen_letters:
                raise ValueError(
                    "Row {!r}: letter {!r} appears more than once.".format(name, ch)
                )
            seen_letters.add(ch)

        if expected_length is None:
            expected_length = len(alphabet)
        elif len(alphabet) != expected_length:
            raise ValueError(
                "Row {!r}: alphabet length {} does not match "
                "the expected length {} (set by the first row).".format(
                    name, len(alphabet), expected_length)
            )

        if name in seen_names:
            raise ValueError("Duplicate row name: {!r}.".format(name))
        seen_names.add(name)

        rows.append((name, alphabet))

    if not rows:
        raise ValueError("Input contains no valid data rows.")

    return rows


def validate_matrix(rows):
    """
    General matrix validation: for every pair of non-'0' lines, if they share
    at least one position where both have the same known letter, then every
    position where both have known letters must also match.

    Returns (True, None) on success, (False, reason_string) on failure.
    """
    non_zero_rows = [(name, alpha) for name, alpha in rows if name != '0']
    n = len(non_zero_rows)
    for i in range(n):
        name_a, alpha_a = non_zero_rows[i]
        for j in range(i + 1, n):
            name_b, alpha_b = non_zero_rows[j]
            any_match    = False
            any_mismatch = False
            for col_i in range(len(alpha_a)):
                la = alpha_a[col_i]
                lb = alpha_b[col_i]
                if la in ('.', '*') or lb in ('.', '*'):
                    continue
                if la == lb:
                    any_match = True
                else:
                    any_mismatch = True
            if any_match and any_mismatch:
                return (False,
                        "The common letters between lines '{}' and '{}' "
                        "must be identical, but they are not.".format(name_a, name_b))
    return (True, None)


def validate_k3_matrix(rows, is_k3):
    """
    K3 validation: if any line has at least one letter identical to its
    counterpart in line '0', then ALL known letters in that line must be
    identical to their line '0' counterparts.

    Returns (True, None) on success, (False, reason_string) on failure.
    """
    if not is_k3:
        return (True, None)
    name_to_alpha = {name: alpha for name, alpha in rows}
    if '0' not in name_to_alpha:
        return (True, None)
    row0 = name_to_alpha['0']
    for name, alpha in rows:
        if name == '0':
            continue
        any_match    = False
        any_mismatch = False
        for col_i, letter in enumerate(alpha):
            if letter in ('.', '*'):
                continue
            if letter == row0[col_i]:
                any_match = True
            else:
                any_mismatch = True
        if any_match and any_mismatch:
            return (False,
                    "All letters in line '{}' that are known "
                    "should be identical to line '0' but are not.".format(name))
    return (True, None)


# ---------------------------------------------------------------------------
# Display
# ---------------------------------------------------------------------------

def print_matrix(rows):
    """Print the matrix with normalised formatting."""
    max_name_len = max(len(name) for name, _ in rows)
    for name, alphabet in rows:
        print("{:<{}}  {}".format(name, max_name_len, alphabet))


def print_matrix_from_alphabets(rows, alphabets):
    """Print the matrix using mutable per-row character lists."""
    max_name_len = max(len(name) for name, _ in rows)
    for i, (name, _) in enumerate(rows):
        print("{:<{}}  {}".format(name, max_name_len, ''.join(alphabets[i])))


# ---------------------------------------------------------------------------
# Rectangle finding
# ---------------------------------------------------------------------------

def _corner_str(corner):
    """Format a (letter, row_name, col_1based) corner tuple as 'L(row-col)'."""
    letter, row_name, col_1based = corner
    return "{}({}-{})".format(letter, row_name, col_1based)


def _rect_str(rect):
    """Format a 4-corner rectangle tuple as 'c0:c1:c2:c3' for display."""
    return ":".join(_corner_str(c) for c in rect)


def _add_rect_geometry(top_name, top_alpha, bot_name, bot_alpha,
                       col1, col2, rectangles, rect_index, rect_geometries):
    """
    If the geometry (top_name, bot_name, col1, col2) is not yet recorded,
    add its 8 orderings to `rectangles` / `rect_index` and mark it in
    `rect_geometries`.  col1 and col2 are 0-based.

    Called by both find_rectangles (full build) and _update_rect_index
    (incremental update) to keep the logic in one place.
    """
    geom = (top_name, bot_name, col1, col2)
    if geom in rect_geometries:
        return
    rect_geometries.add(geom)

    tl_ch = top_alpha[col1]
    tr_ch = top_alpha[col2]
    bl_ch = bot_alpha[col1]
    br_ch = bot_alpha[col2]

    pos1 = col1 + 1
    pos2 = col2 + 1
    tl = (tl_ch, top_name, pos1)
    tr = (tr_ch, top_name, pos2)
    bl = (bl_ch, bot_name, pos1)
    br = (br_ch, bot_name, pos2)

    for rect in [
        (tl, tr, bl, br),
        (tl, bl, tr, br),
        (tr, tl, br, bl),
        (bl, tl, br, tr),
        (bl, br, tl, tr),
        (tr, br, tl, bl),
        (br, bl, tr, tl),
        (br, tr, bl, tl),
    ]:
        offset = len(rectangles)
        rectangles.append(rect)
        seq = rect[0][0], rect[1][0], rect[2][0], rect[3][0]
        for ki in range(4):
            key = ''.join('.' if j == ki else seq[j] for j in range(4))
            if key not in rect_index:
                rect_index[key] = []
            rect_index[key].append(offset)


def find_rectangles(rows):
    """
    Find all complete rectangles and return them as a flat list of
    pre-parsed tuples, along with an index dictionary for O(1) lookup
    and a geometry set for incremental updates.

    Each rectangle is a 4-tuple of corner tuples (letter, row_name, col_1based).
    Each geometry produces 8 orderings (TL:TR:BL:BR etc.).

    The index maps a 4-character key (one letter replaced with '.') to a list
    of offsets into the rectangles list, enabling lookup by incomplete pattern.

    rect_geometries is a set of (top_name, bot_name, col1_0based, col2_0based)
    tuples recording every geometry already added.  Pass it to
    _update_rect_index to extend the index incrementally after matrix changes.

    Positions are 1-based.

    Returns: (rectangles, rect_index, rect_geometries)
    """
    rectangles     = []
    rect_index     = {}
    rect_geometries = set()
    num_rows = len(rows)

    for top_idx in range(num_rows - 1):
        top_name, top_alpha = rows[top_idx]
        top_positions = [i for i, ch in enumerate(top_alpha) if ch != '.']

        for a in range(len(top_positions)):
            col1 = top_positions[a]

            for b in range(a + 1, len(top_positions)):
                col2 = top_positions[b]

                for bot_idx in range(top_idx + 1, num_rows):
                    bot_name, bot_alpha = rows[bot_idx]

                    if bot_alpha[col1] == '.' or bot_alpha[col2] == '.':
                        continue

                    _add_rect_geometry(top_name, top_alpha, bot_name, bot_alpha,
                                       col1, col2,
                                       rectangles, rect_index, rect_geometries)

    return rectangles, rect_index, rect_geometries


def _update_rect_index(matrix, rectangles, rect_index, rect_geometries, dirty_rows):
    """
    Extend `rectangles` / `rect_index` with any newly-complete rectangles
    that involve at least one row in `dirty_rows`.

    A rectangle can only become newly complete when one of its rows gains a
    new letter.  All other row-pairs were fully processed during the last
    call to find_rectangles or a previous _update_rect_index, so they are
    skipped via the rect_geometries deduplication set.

    Cost: O(D × R × C²) where D = |dirty_rows|, vs O(R² × C²) for a full
    rebuild.  Mutates rectangles, rect_index, and rect_geometries in place.
    """
    name_to_row = {name: alpha for name, alpha in matrix}
    matrix_names = [name for name, _ in matrix]   # preserves row order

    for dirty_name in dirty_rows:
        if dirty_name not in name_to_row:
            continue
        dirty_alpha = name_to_row[dirty_name]
        dirty_order = matrix_names.index(dirty_name)

        for other_name in matrix_names:
            if other_name == dirty_name:
                continue
            other_alpha = name_to_row[other_name]
            other_order = matrix_names.index(other_name)

            # Canonical order: the row that appears earlier in the matrix is "top"
            if dirty_order < other_order:
                top_name, top_alpha = dirty_name, dirty_alpha
                bot_name, bot_alpha = other_name, other_alpha
            else:
                top_name, top_alpha = other_name, other_alpha
                bot_name, bot_alpha = dirty_name, dirty_alpha

            top_positions = [i for i, ch in enumerate(top_alpha) if ch != '.']

            for a in range(len(top_positions)):
                col1 = top_positions[a]

                for b in range(a + 1, len(top_positions)):
                    col2 = top_positions[b]

                    if bot_alpha[col1] == '.' or bot_alpha[col2] == '.':
                        continue

                    _add_rect_geometry(top_name, top_alpha, bot_name, bot_alpha,
                                       col1, col2,
                                       rectangles, rect_index, rect_geometries)


def find_incomplete_rectangles(rows, dirty_rows=None):
    """
    Find all incomplete rectangles (exactly 3 known corners, 1 unknown).

    Each is a 4-tuple of corner tuples (letter, row_name, col_1based), with
    '?' as the letter for the unknown corner.  All 8 orderings per geometry.
    Positions are 1-based.

    When `dirty_rows` is provided (a set of row names), only row-pairs where
    at least one row is in the dirty set are examined.  Row-pairs that have
    not changed since the last pass cannot produce new inferences, so they
    are skipped entirely.  Pass dirty_rows=None to scan all pairs (default).
    """
    incomplete = []
    num_rows = len(rows)
    n = len(rows[0][1])

    for top_idx in range(num_rows - 1):
        top_name, top_alpha = rows[top_idx]
        top_dirty = dirty_rows is None or top_name in dirty_rows

        for bot_idx in range(top_idx + 1, num_rows):
            bot_name, bot_alpha = rows[bot_idx]

            # Skip pairs where neither row has changed since the last pass —
            # any inference they could yield was already made.
            if not top_dirty and dirty_rows is not None and bot_name not in dirty_rows:
                continue

            for col1 in range(n):
                tl_ch = top_alpha[col1]
                tl_known = (tl_ch != '.')

                for col2 in range(col1 + 1, n):
                    tr_ch = top_alpha[col2]
                    tr_known = (tr_ch != '.')
                    bl_ch = bot_alpha[col1]
                    bl_known = (bl_ch != '.')
                    br_ch = bot_alpha[col2]
                    br_known = (br_ch != '.')

                    known_count = tl_known + tr_known + bl_known + br_known
                    if known_count != 3:
                        continue

                    pos1 = col1 + 1
                    pos2 = col2 + 1

                    tl = (tl_ch if tl_known else '?', top_name, pos1)
                    tr = (tr_ch if tr_known else '?', top_name, pos2)
                    bl = (bl_ch if bl_known else '?', bot_name, pos1)
                    br = (br_ch if br_known else '?', bot_name, pos2)

                    incomplete.append((tl, tr, bl, br))
                    incomplete.append((tl, bl, tr, br))
                    incomplete.append((tr, tl, br, bl))
                    incomplete.append((bl, tl, br, tr))
                    incomplete.append((bl, br, tl, tr))
                    incomplete.append((tr, br, tl, bl))
                    incomplete.append((br, bl, tr, tl))
                    incomplete.append((br, tr, bl, tl))

    return incomplete


# ---------------------------------------------------------------------------
# Matrix mutation
# ---------------------------------------------------------------------------

def _check_row_vs_matrix(name_a, alpha_a, matrix):
    """
    Check one row (name_a, alpha_a) against every other non-'0' row in matrix.

    The rule: if two non-'0' rows share at least one position where both carry
    the same known letter, then they must not differ at any position where both
    carry known letters.

    Returns (True, None) on success, (False, reason_string) on failure.
    This is O(R × C) — only the single modified row is re-checked, not all
    R*(R-1)/2 pairs.
    """
    if name_a == '0':
        return (True, None)
    for name_b, alpha_b in matrix:
        if name_b == '0' or name_b == name_a:
            continue
        any_match    = False
        any_mismatch = False
        for col_i in range(len(alpha_a)):
            la = alpha_a[col_i]
            lb = alpha_b[col_i]
            if la in ('.', '*') or lb in ('.', '*'):
                continue
            if la == lb:
                any_match = True
            else:
                any_mismatch = True
        if any_match and any_mismatch:
            return (False,
                    "The common letters between lines '{}' and '{}' "
                    "must be identical, but they are not.".format(name_a, name_b))
    return (True, None)


def _check_row_k3(name, alpha, matrix, is_k3):
    """
    Check one row (name, alpha) for K3 consistency against line '0'.

    The rule: if any known letter in the row matches its counterpart in line
    '0', then all known letters in the row must match their counterparts in
    line '0'.

    Returns (True, None) on success, (False, reason_string) on failure.
    Does nothing when is_k3 is False or the row is line '0' itself.
    """
    if not is_k3 or name == '0':
        return (True, None)
    row0 = next((a for n, a in matrix if n == '0'), None)
    if row0 is None:
        return (True, None)
    any_match    = False
    any_mismatch = False
    for col_i, letter in enumerate(alpha):
        if letter in ('.', '*'):
            continue
        if letter == row0[col_i]:
            any_match = True
        else:
            any_mismatch = True
    if any_match and any_mismatch:
        return (False,
                "All letters in line '{}' that are known "
                "should be identical to line '0' but are not.".format(name))
    return (True, None)


def matrix_insert(matrix, line_name, char, position, is_k3=False):
    """
    Insert `char` at `position` (1-based) in the row named `line_name`.

    Succeeds if the target cell is '.' (unknown) or already holds `char`.
    Fails if the target cell holds a different known letter, or if the
    updated row fails general or K3 validation against the rest of the matrix.

    Only the modified row is re-validated (O(R × C)), not the full matrix
    (O(R² × C)), making this safe to call 26 times per empty cell.

    Returns:
        (True,  updated_matrix)  on success
        (False, reason_string)   on conflict, validation failure, or bad arguments
    """
    col = position - 1  # convert to 0-based

    for i, (name, alpha) in enumerate(matrix):
        if name != line_name:
            continue
        if col < 0 or col >= len(alpha):
            return (False,
                    "Position {} is out of range for line {!r} "
                    "(alphabet length {}).".format(position, line_name, len(alpha)))
        current = alpha[col]
        if current == char:
            return (True, matrix)   # idempotent — nothing to do
        if current != '.':
            return (False,
                    "Conflict in line {!r} at position {}: "
                    "existing={!r}, incoming={!r}.".format(
                        line_name, position, current, char))
        updated_alpha  = alpha[:col] + char + alpha[col + 1:]
        updated_matrix = matrix[:i] + [(name, updated_alpha)] + matrix[i + 1:]
        # Only re-check the modified row — O(R×C) instead of O(R²×C)
        ok, reason = _check_row_vs_matrix(name, updated_alpha, updated_matrix)
        if not ok:
            return (False, "Validation failed after inserting {!r} into line {!r} "
                           "at position {}: {}".format(char, line_name, position, reason))
        ok, reason = _check_row_k3(name, updated_alpha, updated_matrix, is_k3)
        if not ok:
            return (False, "K3 validation failed after inserting {!r} into line {!r} "
                           "at position {}: {}".format(char, line_name, position, reason))
        return (True, updated_matrix)

    return (False, "Line {!r} not found in matrix.".format(line_name))


# ---------------------------------------------------------------------------
# Rectangle string parsing
# ---------------------------------------------------------------------------

# Regex to parse a single corner token, e.g. H(0-8) or ?(10-15)
CORNER_RE = re.compile(r'^(.)(\(.+\))$')


def parse_rect_string(rect_str):
    """
    Parse a rectangle string into a list of (letter, ref) tuples.

    e.g. "H(0-8):E(10-8):O(0-15):?(10-15)"
      -> [('H','(0-8)'), ('E','(10-8)'), ('O','(0-15)'), ('?','(10-15)')]
    """
    tokens = rect_str.split(':')
    result = []
    for token in tokens:
        m = CORNER_RE.match(token)
        if not m:
            raise ValueError("Cannot parse corner token: {!r}".format(token))
        result.append((m.group(1), m.group(2)))
    return result


# ---------------------------------------------------------------------------
# K3 matrix normalisation
# ---------------------------------------------------------------------------

def normalize_matrix(rows, is_k3):
    """
    K3 normalisation: if two non-'0' lines share at least one position where
    both carry the same known letter, they must be the same cipher alphabet,
    so merge all known letters from each into the other.  Repeat until no
    further changes can be made.

    A contradiction occurs when two lines are proven equivalent (share a
    matching letter) but also have different known letters at some other
    position.

    Does nothing when is_k3 is False.

    Returns:
        (True,  updated_rows)   on success
        (False, reason_string)  on contradiction
    """
    if not is_k3:
        return (True, rows)

    while True:
        # Build a mutable working copy indexed by name
        name_to_alpha = {name: list(alpha) for name, alpha in rows}
        non_zero_names = [name for name, _ in rows if name != '0']
        changed = False

        for i in range(len(non_zero_names)):
            name_a = non_zero_names[i]
            for j in range(i + 1, len(non_zero_names)):
                name_b = non_zero_names[j]
                alpha_a = name_to_alpha[name_a]
                alpha_b = name_to_alpha[name_b]
                n_cols  = len(alpha_a)

                # Do the two lines share at least one identical known letter?
                any_match = any(
                    alpha_a[col] not in ('.', '*') and
                    alpha_a[col] == alpha_b[col]
                    for col in range(n_cols)
                )
                if not any_match:
                    continue

                # Lines are equivalent — check for contradictions before merging
                for col in range(n_cols):
                    la, lb = alpha_a[col], alpha_b[col]
                    if la not in ('.', '*') and lb not in ('.', '*') and la != lb:
                        return (False,
                                "Contradiction in normalize_matrix: lines '{}' and '{}' "
                                "are equivalent (share a common letter) but differ at "
                                "position {} (line '{}' has '{}', line '{}' has '{}').".format(
                                    name_a, name_b,
                                    col + 1,
                                    name_a, la, name_b, lb))

                # Merge: propagate each line's known letters into the other
                for col in range(n_cols):
                    la, lb = alpha_a[col], alpha_b[col]
                    if la not in ('.', '*') and lb == '.':
                        name_to_alpha[name_b][col] = la
                        changed = True
                    elif lb not in ('.', '*') and la == '.':
                        name_to_alpha[name_a][col] = lb
                        changed = True

        # Rebuild rows from the (possibly updated) working copy
        rows = [(name, ''.join(name_to_alpha[name])) for name, _ in rows]

        if not changed:
            break

    return (True, rows)


# ---------------------------------------------------------------------------
# Full matrix expansion (loops to convergence)
# ---------------------------------------------------------------------------

def expand_matrix(matrix, allow_row_dups=False, allow_col_dups=False,
                  is_k3=False, debug=False, dirty_rows=None):
    """
    Repeatedly apply indirect symmetry until no new letters can be inferred
    (i.e. run apply_indirect_symmetry in a loop until it reports zero new
    letters, exactly as complete-table.py's main pass loop does).

    `dirty_rows` is the set of row names that changed since the last expansion
    (e.g. the single row just modified by matrix_insert).  It is used to
    limit which row-pairs are scanned for incomplete rectangles on passes 2+.

    IMPORTANT — the first pass always scans ALL row-pairs, ignoring dirty_rows.
    Reason: find_rectangles rebuilds the complete-rectangle index from scratch
    at the start of each expand_matrix call.  That rebuild can add new complete
    rectangles involving rows that weren't recently dirty (e.g. two rows both
    gained letters in an earlier expansion cycle).  Those new complete rectangles
    can enable inferences in row-pairs that appear "clean" — so restricting the
    first pass to dirty_rows would silently miss them.  From the second pass
    onward, only rows that received new letters in the previous pass can unlock
    further inferences, so the dirty-rows filter is safe and cheap.

    Raises MatrixContradiction if any pass detects a contradiction.
    Returns the fully expanded matrix.
    """
    # Build the complete-rectangle index once; update it incrementally each pass
    # instead of rebuilding from scratch (O(R²×C²) → O(D×R×C²) per pass).
    rectangles, rect_index, rect_geometries = find_rectangles(matrix)

    # First pass: always scan all row-pairs so that newly-available complete
    # rectangles (found by the fresh find_rectangles call above) are not missed.
    first_pass = True

    while True:
        effective_dirty = None if first_pass else dirty_rows
        first_pass      = False

        incomplete  = find_incomplete_rectangles(matrix, dirty_rows=effective_dirty)
        prev_matrix = matrix
        matrix, new_letters = apply_indirect_symmetry(
                                  matrix, rectangles, rect_index, incomplete,
                                  allow_row_dups=allow_row_dups,
                                  allow_col_dups=allow_col_dups,
                                  is_k3=is_k3, debug=debug)
        if new_letters == 0:
            break
        # Rows that actually changed this pass are the only ones that can
        # unlock new inferences in the next pass.
        dirty_rows = {
            name
            for (name, new_alpha), (_, old_alpha) in zip(matrix, prev_matrix)
            if new_alpha != old_alpha
        }
        # Extend the rectangle index with geometries made complete by those rows.
        _update_rect_index(matrix, rectangles, rect_index, rect_geometries,
                           dirty_rows)
    return matrix


# ---------------------------------------------------------------------------
# Indirect symmetry expansion
# ---------------------------------------------------------------------------

def apply_indirect_symmetry(rows, rectangles, rect_index, incomplete,
                            allow_row_dups=False, allow_col_dups=False,
                            is_k3=False, debug=True):
    """
    Iterate over incomplete rectangles, find matching complete rectangles by
    letter-order, infer the unknown letter, and update the matrix.

    Returns the (possibly updated) rows and a count of newly added letters.
    """
    # Normalise first: merge lines that are provably the same cipher alphabet
    ok, result = normalize_matrix(rows, is_k3)
    if not ok:
        raise MatrixContradiction("NORMALIZATION CONTRADICTION: {}".format(result))
    rows = result

    name_to_idx = {name: i for i, (name, _) in enumerate(rows)}
    alphabets = [list(alpha) for _, alpha in rows]

    inferred = {}   # maps (row_name, col) -> letter already stored
    new_letters = 0

    for inc_rect in incomplete:
        # Each corner is (letter, row_name, col_1based); '?' marks the unknown
        unknown_idx = None
        for i, (ch, _, _) in enumerate(inc_rect):
            if ch == '?':
                unknown_idx = i
                break

        if unknown_idx is None:
            continue

        unknown_row_name = inc_rect[unknown_idx][1]
        unknown_col      = inc_rect[unknown_idx][2] - 1   # convert to 0-based
        unknown_ref      = "({}-{})".format(unknown_row_name, unknown_col + 1)

        cell_key = (unknown_row_name, unknown_col)
        if cell_key in inferred:
            continue

        # Build lookup key: letters of each corner, '.' where unknown
        lookup_key = ''.join('.' if c[0] == '?' else c[0] for c in inc_rect)

        matched_rect   = None
        inferred_letter = None
        for offset in rect_index.get(lookup_key, []):
            matched_rect    = rectangles[offset]
            inferred_letter = matched_rect[unknown_idx][0]
            break

        if matched_rect is None:
            continue

        row_idx = name_to_idx[unknown_row_name]
        current = alphabets[row_idx][unknown_col]

        if current not in ('.', '*'):
            if current != inferred_letter:
                print("CONFLICT at {}: existing='{}' inferred='{}' from {} -> {}".format(
                    unknown_ref, current, inferred_letter,
                    _rect_str(matched_rect), _rect_str(inc_rect)))
                alphabets[row_idx][unknown_col] = '*'
                inferred[cell_key] = '*'
                new_letters += 1
            continue

        if current == '*':
            continue

        # Rule 1: inferred letter must not already appear in the same row
        row_letters = alphabets[row_idx]
        if not allow_row_dups and inferred_letter in row_letters:
            dup_col = row_letters.index(inferred_letter)
            raise MatrixContradiction(
                "DUPLICATION ERROR (row): inserting '{}' at {} would duplicate "
                "the letter already at 1-based col {} in row '{}'.\n"
                "  Complete:   {}\n  Incomplete: {}".format(
                    inferred_letter, unknown_ref,
                    dup_col + 1, unknown_row_name,
                    _rect_str(matched_rect), _rect_str(inc_rect)))

        # Rule 2: inferred letter must not already appear in the same column
        for chk_row_idx, chk_alpha in enumerate(alphabets):
            chk_row_name = rows[chk_row_idx][0]
            if not allow_col_dups and (chk_alpha[unknown_col] == inferred_letter) and (chk_row_name != "0"):
                raise MatrixContradiction(
                    "DUPLICATION ERROR (column): inserting '{}' at {} would duplicate "
                    "the letter already at row '{}', 1-based col {}.\n"
                    "  Complete:   {}\n  Incomplete: {}".format(
                        inferred_letter, unknown_ref,
                        chk_row_name, unknown_col + 1,
                        _rect_str(matched_rect), _rect_str(inc_rect)))

        # K3 check 1: if inferred letter matches line "0" at this column,
        # all other known letters in the target row must also match line "0".
        if is_k3 and ('0' in name_to_idx):
            row0_alpha = alphabets[name_to_idx['0']]
            line0_letter_at_col = row0_alpha[unknown_col]
            if inferred_letter == line0_letter_at_col:
                target_alpha = alphabets[row_idx]
                mismatch_found = False
                for col_i, letter in enumerate(target_alpha):
                    if letter in ('.', '*'):
                        continue
                    if col_i == unknown_col:
                        continue
                    if letter != row0_alpha[col_i]:
                        mismatch_found = True
                        break
                if mismatch_found:
                    raise MatrixContradiction(
                        "K3 ERROR at {}: inferred '{}' matches line '0' at col {} "
                        "but other letters in row '{}' do not all match line '0'.\n"
                        "  Complete:   {}\n  Incomplete: {}".format(
                            unknown_ref, inferred_letter, unknown_col + 1,
                            unknown_row_name,
                            _rect_str(matched_rect), _rect_str(inc_rect)))

        # K3 check 2: if any known letter in the target row matches line "0",
        # the inferred letter must also match line "0" at its column.
        if is_k3 and ('0' in name_to_idx):
            row0_alpha = alphabets[name_to_idx['0']]
            line0_letter_at_col = row0_alpha[unknown_col]
            if inferred_letter != line0_letter_at_col:
                target_alpha = alphabets[row_idx]
                match_found = False
                for col_i, letter in enumerate(target_alpha):
                    if letter in ('.', '*'):
                        continue
                    if col_i == unknown_col:
                        continue
                    if letter == row0_alpha[col_i]:
                        match_found = True
                        break
                if match_found:
                    raise MatrixContradiction(
                        "K3 ERROR at {}: inferred '{}' does not match line '0' letter '{}' "
                        "at col {}, but other letters in row '{}' are identical to line '0' "
                        "-- the inferred letter should be identical but is not.\n"
                        "  Complete:   {}\n  Incomplete: {}".format(
                            unknown_ref, inferred_letter, line0_letter_at_col,
                            unknown_col + 1, unknown_row_name,
                            _rect_str(matched_rect), _rect_str(inc_rect)))

        if debug:
            print("{} -> {} -> {}({},{})".format(
                _rect_str(matched_rect), _rect_str(inc_rect),
                inferred_letter, row_idx, unknown_col))

        alphabets[row_idx][unknown_col] = inferred_letter
        inferred[cell_key] = inferred_letter
        new_letters += 1

    updated_rows = [(name, ''.join(alphabets[i])) for i, (name, _) in enumerate(rows)]
    return updated_rows, new_letters


# ---------------------------------------------------------------------------
# Tetragram validity check
# ---------------------------------------------------------------------------

_TETRAGRAM_DATA_FILE = os.path.join(os.path.dirname(__file__),
                                    'tetragram_frequency_data.txt')


def is_tetragram_valid(tetragram, cache, cutoff='A'):
    """
    Return True if `tetragram` is a plausible 4-letter English sequence,
    False if every possible interpretation of it falls at or below `cutoff`
    in the frequency table.

    The data file contains a 456,976-character string in which each position
    corresponds to a tetragram in odometer order:
        AAAA (index 0), AAAB (index 1), … ZZZZ (index 456975).
    Each character encodes an occurrence-frequency grade: 'A' means zero
    occurrences; higher letters mean increasingly frequent.

    `cutoff` (default 'A') is the highest grade still considered *invalid*.
    A tetragram is valid when at least one interpretation has a grade strictly
    greater than `cutoff`.  Examples:
        cutoff='A'  →  grade > 'A' required  (any non-zero frequency is OK)
        cutoff='B'  →  grade > 'B' required  (rare occurrences are rejected)

    Index formula for tetragram c0 c1 c2 c3  (A=0, B=1, … Z=25):
        index = c0×17576 + c1×676 + c2×26 + c3

    Periods ('.') are treated as wildcards for unknown plaintext letters:

      0 periods  Direct O(1) lookup; no caching needed.

      1–2 periods  Expand every wildcard substitution (26 or 676 combinations).
                   Return True as soon as any substitution exceeds `cutoff`.
                   Return False only when every substitution is at or below it.
                   The result is stored in `cache` keyed by (tetragram, cutoff)
                   to avoid re-expanding on the next call.

      3–4 periods  Too many unknowns to say anything useful — return True
                   (do not penalise).

    `cache` is a plain dict owned by the caller.  The loaded data string is
    stored under the reserved key 'data'; wildcard results are stored under
    (tetragram, cutoff) tuples.  Pass the same dict on every call.
    """
    # --- Load data on first call ---
    if 'data' not in cache:
        with open(_TETRAGRAM_DATA_FILE, 'r', encoding='utf-8') as fh:
            cache['data'] = fh.read().strip()
    data = cache['data']

    tetragram = tetragram.upper()
    cutoff    = cutoff.upper()

    # --- Count wildcards ---
    dot_count = tetragram.count('.')
    if dot_count >= 3:
        return True                # too sparse to evaluate

    # --- Pure alpha: single direct lookup ---
    if dot_count == 0:
        index = (
            (ord(tetragram[0]) - 65) * 17576 +
            (ord(tetragram[1]) - 65) *   676 +
            (ord(tetragram[2]) - 65) *    26 +
            (ord(tetragram[3]) - 65)
        )
        return data[index] > cutoff

    # --- 1 or 2 wildcards: check cache first ---
    cache_key = (tetragram, cutoff)
    if cache_key in cache:
        return cache[cache_key]

    # Expand all wildcard substitutions; return True the moment any exceeds cutoff
    wildcard_positions = [i for i, ch in enumerate(tetragram) if ch == '.']
    chars = list(tetragram)

    for letters in itertools_product(range(26), repeat=len(wildcard_positions)):
        for pos, val in zip(wildcard_positions, letters):
            chars[pos] = chr(65 + val)
        index = (
            (ord(chars[0]) - 65) * 17576 +
            (ord(chars[1]) - 65) *   676 +
            (ord(chars[2]) - 65) *    26 +
            (ord(chars[3]) - 65)
        )
        if data[index] > cutoff:
            cache[cache_key] = True
            return True

    # Every substitution was at or below cutoff — genuinely invalid
    cache[cache_key] = False
    return False


# ---------------------------------------------------------------------------
# Ciphertext decryption using the current (possibly partial) matrix
# ---------------------------------------------------------------------------

def decrypt_ct(ct, matrix, period):
    """
    Decrypt `ct` using the current reconstruction matrix.

    For each ciphertext position i (0-based):
      - The cipher alphabet is line str((i % period) + 1).
      - Search for ct[i] in that alphabet; if found at column j, the
        plaintext letter is line '0'[j].
      - If ct[i] does not appear in the cipher alphabet (the position is
        still '.'), output '.' to indicate an unknown plaintext letter.

    Returns a string of the same length as `ct`.
    """
    line_0   = next(alpha for name, alpha in matrix if name == '0')
    alpha_map = {name: alpha for name, alpha in matrix}

    plaintext = []
    for i, ct_char in enumerate(ct):
        line_name   = str((i % period) + 1)
        cipher_alpha = alpha_map.get(line_name, '.' * len(line_0))
        col = cipher_alpha.find(ct_char)
        plaintext.append(line_0[col] if col != -1 else '.')

    return ''.join(plaintext)


# ---------------------------------------------------------------------------
# Recursive matrix extension (backtracking search)
# ---------------------------------------------------------------------------

def _valid_candidates(line_0_letters, row_letter_set, col_letter_set,
                      allow_row_dups, allow_col_dups):
    """
    Return the list of line-0 characters that are locally valid for an empty
    cell, using precomputed row and column letter sets for O(1) lookups.

    This gives an upper bound on the true candidate count (cross-row
    consistency and K3 are not checked here — matrix_insert handles those
    when a candidate is actually tried).  Used by ExtendMatrix for the MRV
    cell-selection scan.

    Parameters:
        line_0_letters -- pre-computed list of known letters from line '0'
        row_letter_set -- set of letters already known in the target row
        col_letter_set -- set of letters already known in the target column
                          (across all non-'0' rows)
        allow_row_dups -- if False, row_letter_set letters are excluded
        allow_col_dups -- if False, col_letter_set letters are excluded
    """
    candidates = line_0_letters
    if not allow_row_dups:
        candidates = [ch for ch in candidates if ch not in row_letter_set]
    if not allow_col_dups:
        candidates = [ch for ch in candidates if ch not in col_letter_set]
    return candidates


def ExtendMatrix(matrix, is_k3, allow_row_dups=False, allow_col_dups=False,
                 depth=0, char=None, line_name=None,
                 col_1based=None, debug_level=0, solutions=None,
                 ct=None, period=None,
                 max_tetragram_zeroes=None, tetragram_cache=None,
                 tetragram_grade_cutoff='A'):
    """
    Recursively fill every empty cell in the matrix by trying all valid
    characters, using indirect symmetry to propagate each insertion as far
    as possible before recursing.

    A valid character is any known letter present in line '0'.  Each
    candidate is tested via matrix_insert (which enforces cell-level and
    validation constraints); failures are silently skipped and the next
    candidate is tried (backtracking).

    When a fully populated matrix is reached (no empty cells remain),
    it is printed and appended to `solutions`.  The search always continues
    to find all solutions.

    Parameters:
        matrix                -- list of (name, alphabet) tuples; caller should
                                 pass a copy so the original is not mutated.
        is_k3                 -- True if K3 (Quagmire III) rules apply.
        allow_row_dups        -- True to allow a letter more than once in a row.
        allow_col_dups        -- True to allow a letter more than once in a column.
        depth                 -- current recursion depth (incremented on entry).
        char                  -- character inserted to reach this call (None at top).
        line_name             -- line into which char was inserted (None at top).
        col_1based            -- 1-based column of the insertion (None at top).
        debug_level           -- 0=quiet, N>0=depth trace for depths 1..N,
                                 -1=full verbose (all depth + proportion equations).
        solutions             -- mutable list to which complete matrices are appended;
                                 if None a new list is created (top-level call only).
        ct                    -- original ciphertext string (no spaces); when provided
                                 together with `period`, enables plaintext display and
                                 tetragram pruning.
        period                -- key period (positive int); required when ct is given.
        max_tetragram_zeroes  -- if set (int >= 1), the branch is pruned when the
                                 partial plaintext contains at least this many 4-gram
                                 windows that are flagged invalid by is_tetragram_valid.
        tetragram_cache       -- dict passed to is_tetragram_valid for caching; should
                                 be created once by the caller and reused across calls.
        tetragram_grade_cutoff -- highest frequency grade still considered invalid
                                 (default 'A').  Passed through to is_tetragram_valid.
    """
    if solutions is None:
        solutions = []

    # --- Increment depth and print entry sign-of-life ---
    depth += 1
    trace = (debug_level == -1) or (debug_level > 0 and depth <= debug_level)

    # Decrypt partial plaintext once if needed for display or tetragram pruning
    pt = None
    if ct is not None and period is not None:
        if (trace and debug_level > 0) or max_tetragram_zeroes is not None:
            pt = decrypt_ct(ct, matrix, period)

    if trace:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print("{} [Depth {:4d}] ENTER ExtendMatrix: {}".format(
            ts, depth,
            "initial call" if char is None else
            "inserted '{}' into line '{}' at col {}".format(char, line_name, col_1based)))
        if debug_level > 0:
            print_matrix(matrix)
            if pt is not None:
                pt_grouped = ' '.join(pt[i:i+5] for i in range(0, len(pt), 5))
                print("PT: {}".format(pt_grouped))
            print()

    # --- Tetragram pruning ---
    if pt is not None and max_tetragram_zeroes is not None and tetragram_cache is not None:
        zero_count = 0
        for i in range(len(pt) - 3):
            window = pt[i:i+4]
            if not is_tetragram_valid(window, tetragram_cache, cutoff=tetragram_grade_cutoff):
                zero_count += 1
                if zero_count >= max_tetragram_zeroes:
                    if trace:
                        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        print("{} [Depth {:4d}] RETURN ExtendMatrix "
                              "(tetragram pruning: {} zero windows, last: {!r})".format(
                                  ts, depth, zero_count, window))
                    return

    # --- MRV: pick the empty cell with the fewest locally-valid candidates ---
    line_0_alpha   = next(alpha for name, alpha in matrix if name == '0')
    line_0_letters = [ch for ch in line_0_alpha if ch not in ('.', '*')]
    alpha_len      = len(line_0_alpha)

    # Precompute letter sets once — O(R×C) total — so each cell lookup is O(1).
    row_letters_map = {}          # name  → set of known letters in that row
    col_letters_map = {}          # col   → set of known letters in that column
    if not allow_row_dups:
        row_letters_map = {
            name: {ch for ch in alpha if ch not in ('.', '*')}
            for name, alpha in matrix if name != '0'
        }
    if not allow_col_dups:
        col_letters_map = {
            col: {
                alpha[col]
                for name, alpha in matrix
                if name != '0' and alpha[col] not in ('.', '*')
            }
            for col in range(alpha_len)
        }

    best_line_name  = None
    best_col_1based = None
    best_candidates = None   # list of locally-valid chars for the chosen cell

    for name, alpha in matrix:
        if name == '0':
            continue
        row_ls = row_letters_map.get(name, set())
        for col, ch in enumerate(alpha):
            if ch != '.':
                continue
            candidates = _valid_candidates(
                line_0_letters,
                row_ls,
                col_letters_map.get(col, set()),
                allow_row_dups, allow_col_dups)
            if best_candidates is None or len(candidates) < len(best_candidates):
                best_candidates = candidates
                best_line_name  = name
                best_col_1based = col + 1   # store as 1-based
                if len(candidates) == 0:
                    break   # can't do worse — dead cell found, stop scanning
        if best_candidates is not None and len(best_candidates) == 0:
            break

    # --- Base case: every cell is filled ---
    if best_line_name is None:
        print("SUCCESS!")
        print_matrix(matrix)
        solutions.append(list(matrix))
        if trace:
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print("{} [Depth {:4d}] RETURN ExtendMatrix (solution found)".format(ts, depth))
        return

    # --- Zero candidates: this branch is dead ---
    if len(best_candidates) == 0:
        if trace:
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print("{} [Depth {:4d}] RETURN ExtendMatrix (dead cell: line '{}' col {})".format(
                ts, depth, best_line_name, best_col_1based))
        return

    # --- Try each locally-valid candidate in the most-constrained cell ---
    for char in best_candidates:
        # Attempt insertion; skip silently on any conflict or validation failure
        ok, result = matrix_insert(matrix, best_line_name, char,
                                   best_col_1based, is_k3=is_k3)
        if not ok:
            continue

        # Fully expand via repeated indirect symmetry until convergence.
        # Only the row just inserted into is dirty — no other row changed.
        try:
            expanded = expand_matrix(result,
                                     allow_row_dups=allow_row_dups,
                                     allow_col_dups=allow_col_dups,
                                     is_k3=is_k3,
                                     debug=(debug_level == -1),
                                     dirty_rows={best_line_name})
        except MatrixContradiction:
            continue   # contradiction during expansion — try next candidate

        # Recurse on a fresh copy so backtracking never mutates a parent state
        ExtendMatrix(list(expanded), is_k3,
                     allow_row_dups=allow_row_dups,
                     allow_col_dups=allow_col_dups,
                     depth=depth, char=char,
                     line_name=best_line_name, col_1based=best_col_1based,
                     debug_level=debug_level, solutions=solutions,
                     ct=ct, period=period,
                     max_tetragram_zeroes=max_tetragram_zeroes,
                     tetragram_cache=tetragram_cache,
                     tetragram_grade_cutoff=tetragram_grade_cutoff)

    if trace:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print("{} [Depth {:4d}] RETURN ExtendMatrix (candidates exhausted)".format(ts, depth))
