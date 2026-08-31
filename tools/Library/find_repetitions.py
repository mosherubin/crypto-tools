"""
Locates exact repeated sequences shared between ciphertexts, including a
ciphertext compared against itself.

For each candidate offset, sweeps positions left to right in lockstep across
the two letter streams, extending a run of exact matches as far as it goes
and reporting it once it reaches min_length. This is the two-text
generalization of the offset-scan used by STETHOSCOPE's List of Repeats test
(tools/Stethoscope/Basic/tests/list_of_repeats.py).
"""

from dataclasses import dataclass


@dataclass
class Repetition:
    message_a: int
    message_b: int
    position_a: int   # 0-based
    position_b: int   # 0-based
    length: int
    text: str


@dataclass
class RepetitionCount:
    text: str
    count: int


def _scan_alignment(letters_a: str, letters_b: str, offset: int, min_length: int) -> list:
    """offset = position_b - position_a, held fixed across this alignment sweep."""
    len_a, len_b = len(letters_a), len(letters_b)
    position_a = max(0, -offset)
    position_b = position_a + offset

    found = []
    while position_a < len_a and position_b < len_b:
        if letters_a[position_a] == letters_b[position_b]:
            length = 1
            while (position_a + length < len_a and position_b + length < len_b
                   and letters_a[position_a + length] == letters_b[position_b + length]):
                length += 1
            if length >= min_length:
                found.append((position_a, position_b, length))
                position_a += length
                position_b += length
                continue
        position_a += 1
        position_b += 1

    return found


def _find_between(letters_a: str, letters_b: str, min_length: int, self_search: bool) -> list:
    len_a, len_b = len(letters_a), len(letters_b)
    found = []

    if self_search:
        # Offset 1 can only ever match a run of one repeated character (letters[i] ==
        # letters[i+1] == letters[i+2] == ...), never a genuine multi-character
        # sequence, so it is excluded as cryptanalytically uninteresting.
        for offset in range(2, len_a):
            found.extend(_scan_alignment(letters_a, letters_b, offset, min_length))
    else:
        for offset in range(-(len_a - 1), len_b):
            found.extend(_scan_alignment(letters_a, letters_b, offset, min_length))

    return found


def locate_repetitions(ciphertexts: list, min_length: int) -> list:
    """
    Locate every repeated sequence of length >= min_length shared between each pair
    of ciphertexts, including a ciphertext against itself.

    ciphertexts: list of cleaned ciphertext strings (letters only)
    Returns a list of Repetition, each tagged with the indices (into `ciphertexts`)
    of the two messages it was found between.
    """
    results = []
    for i in range(len(ciphertexts)):
        for j in range(i, len(ciphertexts)):
            self_search = (i == j)
            for position_a, position_b, length in _find_between(
                ciphertexts[i], ciphertexts[j], min_length, self_search
            ):
                results.append(Repetition(
                    message_a=i, message_b=j,
                    position_a=position_a, position_b=position_b,
                    length=length, text=ciphertexts[i][position_a:position_a + length],
                ))
    return results


def count_repetitions(results: list) -> list:
    """
    Tally how many times each distinct repeated text occurs among `results`,
    keeping only texts that occur more than twice.

    Returns a list of RepetitionCount sorted by count descending, then by text.
    """
    counts: dict = {}
    for r in results:
        counts[r.text] = counts.get(r.text, 0) + 1

    frequent = [RepetitionCount(text=text, count=count) for text, count in counts.items() if count > 2]
    frequent.sort(key=lambda rc: (-rc.count, rc.text))
    return frequent
