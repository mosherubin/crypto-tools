"""
Locates raw isomorphic sequence pairs within and across ciphertexts.

Two windows of equal length are isomorphic when a single consistent letter
substitution maps one onto the other -- equivalently, when they share the same
"next repeat of this letter" distance at every position. Comparing these
forward-repeat distances (the "delta" array) is far cheaper than comparing
substitution mappings directly, and is the basis of the search below.

This is a from-scratch Python reimplementation of the search algorithm
originally written in C++ by Moshe Rubin (1988), in IsomorphAlgorithm.cpp.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class IsomorphCandidate:
    message_a: int
    message_b: int
    position_a: int   # 0-based
    position_b: int   # 0-based
    length: int
    text_a: str
    text_b: str


def _build_delta(letters: str) -> list:
    """delta[i] = distance to the next occurrence of letters[i], or None if it never repeats again."""
    delta: list = [None] * len(letters)
    last_seen: dict = {}
    for i, ch in enumerate(letters):
        if ch in last_seen:
            delta[last_seen[ch]] = i - last_seen[ch]
        last_seen[ch] = i
    return delta


def _extend_isomorph(delta_a: list, delta_b: list, start_a: int, start_b: int, max_extent: int) -> int:
    """Longest length <= max_extent for which the windows starting at start_a (in a)
    and start_b (in b) share an identical repetition pattern."""
    limit = max_extent
    length = 0
    while length < limit:
        da = delta_a[start_a + length]
        db = delta_b[start_b + length]
        if da != db:
            nearest_repeat = min(d for d in (da, db) if d is not None)
            limit = min(limit, length + nearest_repeat)
            if length >= limit:
                break
        length += 1
    return length


def _scan_alignment(letters_a: str, delta_a: list, letters_b: str, delta_b: list,
                     offset: int, min_isolen: int, self_search: bool) -> list:
    """offset = position_b - position_a, held fixed across this alignment sweep."""
    len_a, len_b = len(letters_a), len(letters_b)
    candidates = []

    position_a = max(0, -offset)
    position_b = position_a + offset

    while position_a < len_a and position_b < len_b:
        room = min(len_a - position_a, len_b - position_b)
        if self_search:
            room = min(room, offset)

        length = _extend_isomorph(delta_a, delta_b, position_a, position_b, room)
        if length >= min_isolen:
            candidates.append(IsomorphCandidate(
                message_a=0, message_b=0,   # filled in by locate_isomorphs
                position_a=position_a, position_b=position_b, length=length,
                text_a=letters_a[position_a:position_a + length],
                text_b=letters_b[position_b:position_b + length],
            ))

        position_a += 1
        position_b += 1

    return candidates


def _find_isomorphs_between(letters_a: str, delta_a: list, letters_b: str, delta_b: list,
                             min_isolen: int, self_search: bool) -> list:
    len_a, len_b = len(letters_a), len(letters_b)
    candidates = []

    if self_search:
        # Only positive offsets are needed: negative offsets would just re-find the
        # same pairs mirrored, and any offset < min_isolen can only yield isomorphs
        # shorter than min_isolen (a self-match can never be longer than its own offset,
        # or the two occurrences would overlap in the source text).
        for offset in range(min_isolen, len_a):
            candidates.extend(_scan_alignment(letters_a, delta_a, letters_b, delta_b, offset, min_isolen, True))
    else:
        for offset in range(-(len_a - 1), len_b):
            candidates.extend(_scan_alignment(letters_a, delta_a, letters_b, delta_b, offset, min_isolen, False))

    return candidates


def _filter_maximal(candidates: list) -> list:
    """Discard any candidate whose span is entirely contained within another
    candidate's span at the same alignment (same message pair and offset).

    Sliding the scan forward one position at a time necessarily re-reports every
    suffix of an isomorph that has no room left to grow past the earlier one's
    right edge -- those suffixes carry no information beyond the longer isomorph
    that already covers them, so only the maximal ones are kept."""
    groups: dict = {}
    for c in candidates:
        offset = c.position_b - c.position_a
        groups.setdefault((c.message_a, c.message_b, offset), []).append(c)

    maximal = []
    for group in groups.values():
        for c in group:
            contained = any(
                other is not c
                and other.position_a <= c.position_a
                and other.position_a + other.length >= c.position_a + c.length
                for other in group
            )
            if not contained:
                maximal.append(c)

    return maximal


def locate_isomorphs(ciphertexts: list, min_isolen: int) -> list:
    """
    Locate every maximal isomorphic sequence pair of length >= min_isolen, both within
    each ciphertext (self-search) and between every pair of ciphertexts (cross-search).
    No significance filtering is applied here -- see isomorph_evaluation.evaluate_isomorph.

    ciphertexts: list of cleaned ciphertext strings (letters only)
    Returns a list of IsomorphCandidate, each tagged with the indices (into `ciphertexts`)
    of the two messages it was found between.
    """
    deltas = [_build_delta(letters) for letters in ciphertexts]
    results = []

    for i in range(len(ciphertexts)):
        for j in range(i, len(ciphertexts)):
            self_search = (i == j)
            found = _find_isomorphs_between(
                ciphertexts[i], deltas[i], ciphertexts[j], deltas[j], min_isolen, self_search
            )
            for candidate in found:
                candidate.message_a = i
                candidate.message_b = j
            results.extend(found)

    return _filter_maximal(results)
