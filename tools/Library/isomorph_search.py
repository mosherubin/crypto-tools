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


def _is_disguised_repetition(candidate: IsomorphCandidate, min_isolen: int) -> bool:
    """True when this isomorph is a plain repetition wearing mismatched characters
    at the boundary -- e.g. MHTZAITYDZYB / FHTZAITYDZYG is just the repeated
    string HTZAITYDZY with a different letter tacked onto each end.

    Trims the mismatched head and tail (positions where text_a[i] != text_b[i]);
    if what remains is an unbroken exact match and is itself long enough to be
    independently notable (>= min_isolen), the isomorph carries no substitution
    evidence beyond what an ordinary repeat already shows, so it is discarded."""
    text_a, text_b = candidate.text_a, candidate.text_b
    length = len(text_a)

    start = 0
    while start < length and text_a[start] != text_b[start]:
        start += 1

    end = length
    while end > start and text_a[end - 1] != text_b[end - 1]:
        end -= 1

    if end - start < min_isolen:
        return False

    return all(text_a[i] == text_b[i] for i in range(start, end))


def locate_isomorphs(ciphertexts: list, min_isolen: int) -> list:
    """
    Locate every maximal isomorphic sequence pair of length >= min_isolen, both within
    each ciphertext (self-search) and between every pair of ciphertexts (cross-search).
    Isomorphs that are really just a repetition wearing mismatched boundary characters
    (see _is_disguised_repetition) are discarded, since they carry no substitution
    evidence beyond what an ordinary repeat search already shows.
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

    maximal = _filter_maximal(results)
    return [c for c in maximal if not _is_disguised_repetition(c, min_isolen)]


def prune_shallow(text: str) -> tuple:
    """
    Trim a leading and trailing run of "singleton" characters -- those occurring
    exactly once anywhere in `text` -- using text's own letter-frequency count
    (fixed before trimming starts, so removing one singleton cannot expose a
    "new" one further in; trimming always stops at the first character, from
    each side, that recurs elsewhere in the original text).

    Returns (start, end): the surviving span as a [start, end) slice of `text`.
    """
    freq: dict = {}
    for ch in text:
        freq[ch] = freq.get(ch, 0) + 1

    length = len(text)
    start = 0
    while start < length and freq[text[start]] == 1:
        start += 1

    end = length
    while end > start and freq[text[end - 1]] == 1:
        end -= 1

    return start, end


def prune_deep(text: str) -> tuple:
    """
    Find the single largest connected region of overlapping repeat-pairs within
    `text`. Each character's occurrence and its next occurrence define an
    interval [i, j] -- "this letter recurs here"; overlapping intervals (e.g.
    R's pair and O's pair both spanning some of the same ground) are merged,
    and the largest merged interval survives. An isolated bounded pair that
    does not overlap anything else (e.g. a repeated letter with nothing else
    recurring nearby) is discarded even though it is not a singleton, in favor
    of a longer interlaced region elsewhere in the text.

    Returns (start, end): the surviving span as a [start, end) slice of `text`,
    or (0, 0) if no character in `text` repeats at all.
    """
    last_seen: dict = {}
    intervals = []
    for i, ch in enumerate(text):
        if ch in last_seen:
            intervals.append((last_seen[ch], i))
        last_seen[ch] = i

    if not intervals:
        return 0, 0

    intervals.sort()

    best_start, best_end = intervals[0]
    cur_start, cur_end = intervals[0]

    def _span(s, e):
        return e - s

    for s, e in intervals[1:]:
        if s <= cur_end:
            cur_end = max(cur_end, e)
        else:
            if _span(cur_start, cur_end) > _span(best_start, best_end):
                best_start, best_end = cur_start, cur_end
            cur_start, cur_end = s, e

    if _span(cur_start, cur_end) > _span(best_start, best_end):
        best_start, best_end = cur_start, cur_end

    return best_start, best_end + 1  # convert inclusive end -> exclusive


PRUNE_MODES = ('raw', 'shallow', 'deep')


def apply_pruning(candidate: IsomorphCandidate, mode: str, min_isolen: int) -> Optional[IsomorphCandidate]:
    """
    Apply a pruning mode to a located candidate, returning a new (shrunk)
    IsomorphCandidate with adjusted position/length/text, or None if the
    pruned result falls below min_isolen (including vanishing to nothing).
    'raw' returns the candidate unchanged. Only text_a is used to determine
    the trim span -- the pattern (and hence the span) is identical in text_b
    by definition of isomorphism -- and the same span is applied to both.
    """
    if mode == 'raw':
        return candidate

    if mode == 'shallow':
        start, end = prune_shallow(candidate.text_a)
    elif mode == 'deep':
        start, end = prune_deep(candidate.text_a)
    else:
        raise ValueError(f"unknown pruning mode {mode!r}")

    length = end - start
    if length < min_isolen:
        return None

    return IsomorphCandidate(
        message_a=candidate.message_a, message_b=candidate.message_b,
        position_a=candidate.position_a + start, position_b=candidate.position_b + start,
        length=length,
        text_a=candidate.text_a[start:end], text_b=candidate.text_b[start:end],
    )


def prune_candidates(candidates: list, mode: str, min_isolen: int) -> list:
    """
    Apply a pruning mode to every candidate in a located list, dropping any that
    fall below min_isolen and de-duplicating any that converge on the same
    pruned span. Distinct raw maximal candidates (e.g. two overlapping but
    non-nested isomorphs at different alignments) can legitimately prune down
    to an identical result -- shallow trimming or deep pruning's largest-
    connected-region search may land on the same core letters from either
    starting point -- so the same pruned isomorph must not be reported twice.
    """
    seen: set = set()
    pruned = []
    for candidate in candidates:
        result = apply_pruning(candidate, mode, min_isolen)
        if result is None:
            continue
        key = (result.message_a, result.message_b, result.position_a, result.position_b, result.length)
        if key in seen:
            continue
        seen.add(key)
        pruned.append(result)
    return pruned
