"""
STETHOSCOPE test: Monoalphabetic frequency count.
Counts occurrences of each charset symbol in the cleaned ciphertext.
"""

from dataclasses import dataclass
from typing import Optional
import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from ciphertext import CiphertextData


@dataclass
class MonoCountResult:
    counts: dict[str, int]        # symbol → count, includes zeros for absent symbols
    total_letters: int
    passed: Optional[bool] = None # None if no expected_results to compare against
    errors: list[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []


def run(ct: CiphertextData) -> MonoCountResult:
    counts = {ch: 0 for ch in ct.alphabet}
    for ch in ct.letters:
        counts[ch] += 1

    total = len(ct.letters)
    result = MonoCountResult(counts=counts, total_letters=total)

    expected = ct.expected_results
    errors = []

    if 'ditscount' in expected:
        if ct.ditscount != expected['ditscount']:
            errors.append(
                f"ditscount mismatch: computed {ct.ditscount}, expected {expected['ditscount']}"
            )

    if 'total_letters' in expected:
        if total != expected['total_letters']:
            errors.append(
                f"total_letters mismatch: computed {total}, expected {expected['total_letters']}"
            )

    if 'mono_count' in expected:
        exp_counts = expected['mono_count']['counts']
        for sym, exp_val in exp_counts.items():
            got = counts.get(sym, 0)
            if got != exp_val:
                errors.append(
                    f"mono_count['{sym}']: computed {got}, expected {exp_val}"
                )
        for sym in counts:
            if sym not in exp_counts:
                errors.append(f"mono_count: symbol '{sym}' in charset but missing from expected")

    if expected:
        result.passed = len(errors) == 0
        result.errors = errors

    return result
