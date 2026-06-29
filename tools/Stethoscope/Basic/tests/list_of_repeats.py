"""
STETHOSCOPE test: List of Repeats.

Finds all repeated sequences of length >= 4 in the ciphertext.
For each offset (2..N-3), scans left-to-right for maximal-length matches.
Sorts by repeated string, then within blocks sharing the same first 4 characters
re-sorts by (position, offset).
Prints up to MAX_REPEATS entries; if more exist prints "MORE (# remaining)".
"""

from dataclasses import dataclass, field
from typing import Optional
import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from ciphertext import CiphertextData

MIN_LENGTH = 4


@dataclass
class Repeat:
    length: int
    position: int   # 1-based
    offset: int
    text: str


@dataclass
class RepeatsResult:
    repeats: list
    total_found: int
    passed: Optional[bool] = None
    errors: list = field(default_factory=list)


def _find_repeats(letters: str) -> list:
    n = len(letters)
    repeats = []
    for offset in range(2, n - 2):
        i = 0
        while i <= n - offset - 1:
            if letters[i] == letters[i + offset]:
                length = 1
                while (i + length < n - offset) and (letters[i + length] == letters[i + offset + length]):
                    length += 1
                if length >= MIN_LENGTH:
                    repeats.append(Repeat(
                        length=length,
                        position=i + 1,
                        offset=offset,
                        text=letters[i:i + length],
                    ))
                    i += length
                else:
                    i += 1
            else:
                i += 1
    return repeats


def _sort_key(r: Repeat):
    return (r.text, r.position, r.offset)


def _sorted_repeats(repeats: list) -> list:
    repeats.sort(key=_sort_key)

    result = []
    i = 0
    while i < len(repeats):
        j = i
        prefix = repeats[i].text[:4]
        while j < len(repeats) and repeats[j].text[:4] == prefix:
            j += 1
        block = repeats[i:j]
        block.sort(key=lambda r: (r.position, r.offset))
        result.extend(block)
        i = j
    return result


def run(ct: CiphertextData, max_repeats: int = 50) -> RepeatsResult:
    raw_repeats = _find_repeats(ct.letters)
    sorted_rep = _sorted_repeats(raw_repeats)
    total = len(sorted_rep)
    displayed = sorted_rep if max_repeats == 0 else sorted_rep[:max_repeats]

    expected_list = ct.expected_results.get('list_of_repeats')
    if not expected_list:
        return RepeatsResult(repeats=displayed, total_found=total)

    errors = []
    exp_displayed = expected_list[:MAX_REPEATS]
    if len(displayed) != len(exp_displayed):
        errors.append(
            f"displayed count: computed {len(displayed)}, expected {len(exp_displayed)}"
        )
    for idx, (got, exp) in enumerate(zip(displayed, exp_displayed)):
        for field_name, gv, ev in [
            ('length',   got.length,   exp.get('length')),
            ('position', got.position, exp.get('position')),
            ('offset',   got.offset,   exp.get('offset')),
            ('text',     got.text,     exp.get('text')),
        ]:
            if ev is not None and (gv != ev if field_name != 'text' else gv.lower() != ev.lower()):
                errors.append(
                    f"repeat[{idx}] {field_name}: computed {gv!r}, expected {ev!r}"
                )


    return RepeatsResult(
        repeats=displayed,
        total_found=total,
        passed=len(errors) == 0,
        errors=errors,
    )


def format_output(result: RepeatsResult) -> str:
    lines = ["LIST OF HITS OF LENGTH 4 OR LONGER"]
    lines.append(f"{'LENGTH':>6}  {'POSITION':>8}  {'OFFSET':>6}  REPEATED TEXT")
    for r in result.repeats:
        spaced = "  ".join(r.text)
        lines.append(f"{r.length:>6}  {r.position:>8}  {r.offset:>6}  {spaced}")
    remaining = result.total_found - len(result.repeats)
    if remaining > 0:
        lines.append(f"MORE ({remaining} remaining)")
    return "\n".join(lines)
