"""
STETHOSCOPE tests: Trigraphic Index of Coincidence (overall, cut_A, cut_B, cut_C).
"""

import math
from collections import defaultdict
from dataclasses import dataclass
from typing import Optional
import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from ciphertext import CiphertextData


@dataclass
class TrigraphicIcResult:
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


def _bigrams_overall(text: str):
    return [(text[i], text[i+1], text[i+2]) for i in range(len(text) - 2)]

def _trigrams_cut_A(text: str):
    return [(text[i], text[i+1], text[i+2]) for i in range(0, len(text) - 2, 3)]

def _trigrams_cut_B(text: str):
    return [(text[i], text[i+1], text[i+2]) for i in range(1, len(text) - 2, 3)]

def _trigrams_cut_C(text: str):
    return [(text[i], text[i+1], text[i+2]) for i in range(2, len(text) - 2, 3)]


def _compute(ct: CiphertextData, trigrams: list, expected: dict) -> TrigraphicIcResult:
    C = len(ct.alphabet)
    M = len(trigrams)

    counts = defaultdict(int)
    for tg in trigrams:
        counts[tg] += 1

    sum_f2 = sum(v * v for v in counts.values())

    ic_precise = (C ** 3) / (M * (M - 1)) * (sum_f2 - M)
    sigmage_precise = (M * (ic_precise - 1)) / math.sqrt(2 * (C ** 3 - 1))
    hits_expected_precise = (M * (M - 1)) / (2 * C ** 3)

    ic = round(ic_precise, 2)
    sigmage = round(sigmage_precise, 1)
    hits_observed = sum(v * (v - 1) for v in counts.values()) // 2
    hits_expected = round(hits_expected_precise, 2)

    result = TrigraphicIcResult(
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


def run_overall(ct: CiphertextData) -> TrigraphicIcResult:
    trigrams = _bigrams_overall(ct.letters)
    expected = ct.expected_results.get('compute_trigraphic_ic_overall', {})
    return _compute(ct, trigrams, expected)

def run_cut_A(ct: CiphertextData) -> TrigraphicIcResult:
    trigrams = _trigrams_cut_A(ct.letters)
    expected = ct.expected_results.get('compute_trigraphic_ic_cut_A', {})
    return _compute(ct, trigrams, expected)

def run_cut_B(ct: CiphertextData) -> TrigraphicIcResult:
    trigrams = _trigrams_cut_B(ct.letters)
    expected = ct.expected_results.get('compute_trigraphic_ic_cut_B', {})
    return _compute(ct, trigrams, expected)

def run_cut_C(ct: CiphertextData) -> TrigraphicIcResult:
    trigrams = _trigrams_cut_C(ct.letters)
    expected = ct.expected_results.get('compute_trigraphic_ic_cut_C', {})
    return _compute(ct, trigrams, expected)
