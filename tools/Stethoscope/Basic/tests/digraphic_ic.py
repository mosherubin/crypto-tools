"""
STETHOSCOPE tests: Digraphic Index of Coincidence (overall, cut_a, cut_b).
"""

import math
from collections import defaultdict
from dataclasses import dataclass
from typing import Optional
import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from ciphertext import CiphertextData, DIT


@dataclass
class DigraphicIcResult:
    ic: float
    sigmage: float
    total: int
    hits_observed: int
    hits_expected: float
    passed: Optional[bool] = None
    errors: list = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []


def _bigrams_overall(stream: str):
    return [(stream[i], stream[i + 1]) for i in range(len(stream) - 1)
            if stream[i] != DIT and stream[i + 1] != DIT]

def _bigrams_cut_a(stream: str):
    return [(stream[i], stream[i + 1]) for i in range(0, len(stream) - 1, 2)
            if stream[i] != DIT and stream[i + 1] != DIT]

def _bigrams_cut_b(stream: str):
    return [(stream[i], stream[i + 1]) for i in range(1, len(stream) - 1, 2)
            if stream[i] != DIT and stream[i + 1] != DIT]


def _compute(ct: CiphertextData, bigrams: list, sigmage_type: str, expected: dict) -> DigraphicIcResult:
    C = len(ct.alphabet)
    M = len(bigrams)

    if M < 2:
        result = DigraphicIcResult(ic=0.0, sigmage=0.0, total=M,
                                   hits_observed=0, hits_expected=0)
        if expected:
            errors = []
            for name, got, exp in [('total', M, expected.get('total'))]:
                if exp is not None and got != exp:
                    errors.append(f"{name}: computed {got}, expected {exp}")
            result.passed = len(errors) == 0
            result.errors = errors
        return result

    counts = defaultdict(int)
    for bg in bigrams:
        counts[bg] += 1

    sum_f2 = sum(v * v for v in counts.values())

    ic = round((C ** 2) / (M * (M - 1)) * (sum_f2 - M), 3)

    if sigmage_type == 'overall':
        sigmage = round((M * (ic - 1)) / math.sqrt(2 * C * (C + 2)), 1)
    else:
        sigmage = round((M * (ic - 1)) / math.sqrt(2 * (C ** 2 - 1)), 1)

    hits_observed = sum(v * (v - 1) for v in counts.values()) // 2
    hits_expected = round((M * (M - 1)) / (2 * C ** 2))

    result = DigraphicIcResult(
        ic=ic,
        sigmage=sigmage,
        total=M,
        hits_observed=hits_observed,
        hits_expected=hits_expected,
    )

    if not expected:
        return result

    errors = []
    checks = [
        ('ic',            ic,            expected.get('ic')),
        ('sigmage',       sigmage,       expected.get('sigmage')),
        ('total',         M,             expected.get('total')),
        ('hits_observed', hits_observed, expected.get('hits_observed')),
        ('hits_expected', hits_expected, expected.get('hits_expected')),
    ]
    for name, got, exp in checks:
        if exp is not None and got != exp:
            errors.append(f"{name}: computed {got}, expected {exp}")

    result.passed = len(errors) == 0
    result.errors = errors
    return result


def run_overall(ct: CiphertextData) -> DigraphicIcResult:
    bigrams = _bigrams_overall(ct.stream)
    expected = ct.expected_results.get('compute_digraphic_ic_overall', {})
    return _compute(ct, bigrams, 'overall', expected)

def run_cut_a(ct: CiphertextData) -> DigraphicIcResult:
    bigrams = _bigrams_cut_a(ct.stream)
    expected = ct.expected_results.get('compute_digraphic_ic_cut_a', {})
    return _compute(ct, bigrams, 'onoff', expected)

def run_cut_b(ct: CiphertextData) -> DigraphicIcResult:
    bigrams = _bigrams_cut_b(ct.stream)
    expected = ct.expected_results.get('compute_digraphic_ic_cut_b', {})
    return _compute(ct, bigrams, 'onoff', expected)
