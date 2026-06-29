"""
STETHOSCOPE test: Polygraphic Hits and IC for lengths 3, 4, and 5.
"""

import math
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional
import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from ciphertext import CiphertextData


@dataclass
class PolygraphicEntry:
    length: int
    total: int
    observed: int
    expected: float
    ic: float
    sigmage: float


@dataclass
class PolygraphicResult:
    entries: list
    passed: Optional[bool] = None
    errors: list = field(default_factory=list)


def run(ct: CiphertextData) -> PolygraphicResult:
    text = ct.letters
    N = len(text)
    c = len(ct.alphabet)

    entries = []
    for m in range(3, 6):
        mN = N - m + 1
        if mN < 2:
            break
        cm = c ** m

        gram_counts = defaultdict(int)
        for i in range(mN):
            gram_counts[text[i:i + m]] += 1

        observed = sum(v * (v - 1) // 2 for v in gram_counts.values())
        expected = mN * (mN - 1) / (2 * cm)
        ic = cm / (mN * (mN - 1)) * 2 * observed if observed > 0 else 0.0
        sigmage = mN * (ic - 1) / math.sqrt(2 * (cm - 1))

        entries.append(PolygraphicEntry(
            length=m,
            total=mN,
            observed=observed,
            expected=round(expected, 2),
            ic=round(ic, 2),
            sigmage=round(sigmage, 1),
        ))

    expected_list = ct.expected_results.get('polygraphic_ic')
    if not expected_list:
        return PolygraphicResult(entries=entries)

    errors = []
    for entry, exp in zip(entries, expected_list):
        for field_name, got, want in [
            ('total',    entry.total,    exp.get('total')),
            ('observed', entry.observed, exp.get('observed')),
            ('expected', entry.expected, exp.get('expected')),
            ('ic',       entry.ic,       exp.get('ic')),
            ('sigmage',  entry.sigmage,  exp.get('sigmage')),
        ]:
            if want is not None and got != want:
                errors.append(
                    f"length {entry.length} {field_name}: computed {got}, expected {want}"
                )

    return PolygraphicResult(entries=entries, passed=len(errors) == 0, errors=errors)
