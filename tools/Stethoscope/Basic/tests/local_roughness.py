"""
STETHOSCOPE test: Local Roughness (offsets 1-33).
"""

import math
from dataclasses import dataclass, field
from typing import Optional
import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from ciphertext import CiphertextData


@dataclass
class LocalRoughnessEntry:
    offset: int
    observed: int
    expected: int
    sigmage: float


@dataclass
class LocalRoughnessResult:
    entries: list
    passed: Optional[bool] = None
    errors: list = field(default_factory=list)


def run(ct: CiphertextData, mono_counts: dict) -> LocalRoughnessResult:
    text = ct.letters
    N = len(text)
    s = len(ct.alphabet)

    S = sum(v * (v - 1) for v in mono_counts.values())
    ic_precise = S * s / (N * (N - 1))

    max_offset = min(33, N - 1)
    entries = []

    for offset in range(1, max_offset + 1):
        P = N - offset
        observed = sum(1 for i in range(P) if text[i] == text[i + offset])
        expected_precise = ic_precise * P / s
        sigmage = (s * (observed - expected_precise)) / math.sqrt(P * ic_precise * (s - ic_precise))

        entries.append(LocalRoughnessEntry(
            offset=offset,
            observed=observed,
            expected=round(expected_precise),
            sigmage=round(sigmage, 1),
        ))

    expected_list = ct.expected_results.get('local_roughness')
    if not expected_list:
        return LocalRoughnessResult(entries=entries)

    errors = []
    for entry, exp in zip(entries, expected_list):
        for field_name, got, want in [
            ('observed', entry.observed, exp.get('observed')),
            ('expected', entry.expected, exp.get('expected')),
            ('sigmage',  entry.sigmage,  exp.get('sigmage')),
        ]:
            if want is not None and got != want:
                errors.append(f"offset {entry.offset} {field_name}: computed {got}, expected {want}")

    return LocalRoughnessResult(entries=entries, passed=len(errors) == 0, errors=errors)
