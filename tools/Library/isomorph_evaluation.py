"""
Statistical significance evaluation for a located isomorph.

This is a from-scratch Python reimplementation of the probability model
originally derived by Moshe Rubin (1988) in ComputeIsomorphCalculations.cpp;
see compute_prob() there for the original derivation of the formula below.
"""

from collections import Counter
from dataclasses import dataclass
import math

_stirling_cache: dict = {}


def _stirling_second_kind(n: int, k: int) -> int:
    """Number of ways to partition n labeled positions into k non-empty unlabeled
    groups -- equivalently, the number of distinct isomorph patterns of length n
    that use exactly k distinct letters."""
    if k > n:
        return 0
    if k == 0:
        return 1 if n == 0 else 0
    if k == n or k == 1:
        return 1

    key = (n, k)
    cached = _stirling_cache.get(key)
    if cached is not None:
        return cached

    value = k * _stirling_second_kind(n - 1, k) + _stirling_second_kind(n - 1, k - 1)
    _stirling_cache[key] = value
    return value


# Keyed on (isolen, num_distinct, alphabet_size) only -- unlike the original C++,
# this cache never needs to be reset between message pairs, since the shape
# probability does not depend on message length or on which pair is being searched.
_shape_probability_cache: dict = {}


def _probability_of_shape(isolen: int, num_distinct: int, alphabet_size: int) -> float:
    """Probability that two independent, uniformly random strings of length isolen
    over an alphabet of alphabet_size symbols coincidentally share the same isomorph
    pattern, given that the pattern uses exactly num_distinct distinct symbols."""
    key = (isolen, num_distinct, alphabet_size)
    cached = _shape_probability_cache.get(key)
    if cached is not None:
        return cached

    # log(alphabet_size! / (alphabet_size - num_distinct)!), i.e. the log of the number of
    # ways to assign num_distinct distinct concrete letters to the pattern's letter-classes.
    log_falling_factorial = math.lgamma(alphabet_size + 1) - math.lgamma(alphabet_size - num_distinct + 1)
    log_single_pattern_match = log_falling_factorial - isolen * math.log(alphabet_size)

    probability = _stirling_second_kind(isolen, num_distinct) * math.exp(2 * log_single_pattern_match)

    _shape_probability_cache[key] = probability
    return probability


@dataclass
class IsomorphSignificance:
    num_distinct_chars: int
    probability: float
    expected_occurrences: float
    significant: bool


def evaluate_isomorph(text: str, alphabet_size: int, message_length_a: int, message_length_b: int,
                       self_search: bool, max_expected: float = 10.0) -> IsomorphSignificance:
    """
    Evaluate whether a located isomorph is statistically significant.

    text: the isomorph's letters as they appear in the first message (its length is the isomorph length)
    alphabet_size: number of distinct symbols in the cipher's alphabet
    message_length_a, message_length_b: lengths of the two ciphertexts being compared
    self_search: True when comparing a ciphertext against itself
    max_expected: an isomorph is "significant" when the expected number of coincidental
                  occurrences of its pattern shape, across every alignment between
                  the two messages, is at most this value
    """
    isolen = len(text)
    num_distinct = len(Counter(text))

    probability = _probability_of_shape(isolen, num_distinct, alphabet_size)

    if self_search:
        # Number of ways to place two non-overlapping length-isolen windows in one
        # message of length message_length_a is the triangular number T(k), where
        # k = message_length_a - 2*isolen + 1.
        k = message_length_a - (2 * isolen) + 1
        comparisons = k * (k + 1) // 2 if k > 0 else 0
    else:
        comparisons = (message_length_a - isolen + 1) * (message_length_b - isolen + 1)

    expected_occurrences = probability * comparisons

    return IsomorphSignificance(
        num_distinct_chars=num_distinct,
        probability=probability,
        expected_occurrences=expected_occurrences,
        significant=expected_occurrences <= max_expected,
    )
