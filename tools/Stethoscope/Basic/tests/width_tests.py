"""
STETHOSCOPE test: Width Tests (widths 2-51).
"""

import math
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional
import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from ciphertext import CiphertextData


@dataclass
class WidthEntry:
    width: int
    hits: int
    comparisons: int
    average_ic: float
    sigmage: float


@dataclass
class WidthTestsResult:
    entries: list
    passed: Optional[bool] = None
    errors: list = field(default_factory=list)


def run(ct: CiphertextData, mono_counts: dict) -> WidthTestsResult:
    text = ct.letters
    N = len(text)
    c = len(ct.alphabet)

    S = sum(v * (v - 1) for v in mono_counts.values())
    delta_mono = S * c / (N * (N - 1))

    entries = []
    for w in range(2, 52):
        columns = [text[k::w] for k in range(w)]
        total_hits = 0
        total_comps = 0
        for col in columns:
            Mk = len(col)
            counts = defaultdict(int)
            for ch in col:
                counts[ch] += 1
            pairs = sum(v * (v - 1) // 2 for v in counts.values())
            total_hits += pairs
            total_comps += Mk * (Mk - 1) // 2

        if total_comps == 0:
            break

        avg_ic_precise = c * total_hits / total_comps
        sigmage = N * (avg_ic_precise - delta_mono) / math.sqrt(2 * (c - 1) * w)

        entries.append(WidthEntry(
            width=w,
            hits=total_hits,
            comparisons=total_comps,
            average_ic=round(avg_ic_precise, 3),
            sigmage=round(sigmage, 2),
        ))

    expected_list = ct.expected_results.get('width_tests')
    if not expected_list:
        return WidthTestsResult(entries=entries)

    expected_by_width = {e['width']: e for e in expected_list}
    errors = []
    for entry in entries:
        exp = expected_by_width.get(entry.width)
        if not exp:
            continue
        for field_name, got, want in [
            ('hits',        entry.hits,        exp.get('hits')),
            ('comparisons', entry.comparisons,  exp.get('comparisons')),
            ('average_ic',  entry.average_ic,   exp.get('average_ic')),
            ('sigmage',     entry.sigmage,      exp.get('sigmage')),
        ]:
            if want is not None and got != want:
                errors.append(
                    f"width {entry.width} {field_name}: computed {got}, expected {want}"
                )

    return WidthTestsResult(entries=entries, passed=len(errors) == 0, errors=errors)
