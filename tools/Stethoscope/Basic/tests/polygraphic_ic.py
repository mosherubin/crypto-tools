"""
STETHOSCOPE test: Polygraphic Hits and IC (m = p, p+1, ...).

p is the smallest m >= 3 where mN*(mN-1)/c^m <= 40.
The table continues while mN*(mN-1)/c^m >= 1 (EXPECTED >= 0.5).
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

    # Find p: smallest m >= 3 where mN*(mN-1)/c^m <= 40
    p = None
    for m in range(3, N):
        mN = N - m + 1
        cm = c ** m
        if mN * (mN - 1) / cm <= 40:
            p = m
            break
    if p is None:
        return PolygraphicResult(entries=[])

    entries = []
    m = p
    while True:
        mN = N - m + 1
        if mN < 2:
            break
        cm = c ** m
        ratio = mN * (mN - 1) / cm
        if ratio < 1:
            break

        gram_counts = defaultdict(int)
        for i in range(mN):
            gram_counts[text[i:i + m]] += 1

        observed = sum(v * (v - 1) // 2 for v in gram_counts.values())
        expected = ratio / 2
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
        m += 1

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
