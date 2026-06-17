"""
STETHOSCOPE test: Monographic Index of Coincidence.
"""

import math
from dataclasses import dataclass
from typing import Optional
import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from ciphertext import CiphertextData


@dataclass
class IcMonoResult:
    ic: float
    sigmage: float
    total: int
    hits_observed: int
    hits_expected: int
    passed: Optional[bool] = None
    errors: list = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []


def run(ct: CiphertextData, mono_counts: dict[str, int]) -> IcMonoResult:
    N = len(ct.letters)
    c = len(ct.alphabet)

    S = sum(v * (v - 1) for v in mono_counts.values())

    ic = round(S * c / (N * (N - 1)), 4)
    sd = math.sqrt((2 * (c - 1)) / (N * (N - 1)))
    sigmage = round((ic - 1.0) / sd, 1)
    hits_observed = round(S / 2)
    hits_expected = math.floor((N * (N - 1)) / (2 * c))

    result = IcMonoResult(
        ic=ic,
        sigmage=sigmage,
        total=N,
        hits_observed=hits_observed,
        hits_expected=hits_expected,
    )

    expected = ct.expected_results.get('compute_ic_mono')
    if expected is None:
        return result

    errors = []
    checks = [
        ('ic',            ic,            expected.get('ic')),
        ('sigmage',       sigmage,       expected.get('sigmage')),
        ('total',         N,             expected.get('total')),
        ('hits_observed', hits_observed, expected.get('hits_observed')),
        ('hits_expected', hits_expected, expected.get('hits_expected')),
    ]
    for name, got, exp in checks:
        if exp is not None and got != exp:
            errors.append(f"{name}: computed {got}, expected {exp}")

    result.passed = len(errors) == 0
    result.errors = errors
    return result
