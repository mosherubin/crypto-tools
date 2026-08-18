"""
Scores putative plaintext by (negative) cross entropy of its overlapping
n-grams against a frequency table trained on a language corpus -- i.e. the
mean, not the sum, of each n-gram's log2-probability under the reference
model. N-grams absent from the training corpus are scored with a floor
value, rather than being treated as impossible, since a corpus of realistic
size will never contain every possible n-gram of a given language.

Averaging rather than summing is what makes scores comparable across
candidates of different lengths: a raw sum is biased toward shorter
candidates purely because they have fewer terms, regardless of how
language-like they actually are. That doesn't matter when every candidate
being compared has the same length (e.g. hill climbing over keys alone,
where transposition never changes length), but it matters as soon as
length-changing transformations of the ciphertext are also candidates --
e.g. testing insert/delete perturbations against the correct one.

Scoring is vectorized: the log-frequency table is a dense NumPy array
indexed by n-gram code (the n-gram's characters read as base-|alphabet|
digits), so scoring many candidate plaintexts at once -- as hill climbing
needs to, to evaluate every candidate transformation of a key -- is a single
batched array lookup rather than a per-candidate Python loop.
"""

import math

import numpy as np


def load_ngram_counts(path: str) -> dict:
    """Parse a '<ngram><whitespace><count>' file into {ngram: count}."""
    counts = {}
    with open(path, encoding='utf-8') as f:
        for line_number, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) != 2:
                raise ValueError(f"{path}:{line_number}: expected '<ngram> <count>', got {line!r}")
            ngram, count = parts
            counts[ngram] = int(count)
    return counts


def alphabet_from_counts(counts: dict) -> set:
    return set(''.join(counts.keys()))


class NgramScorer:
    def __init__(self, counts: dict):
        lengths = {len(ngram) for ngram in counts}
        if len(lengths) != 1:
            raise ValueError(f"All n-grams must have the same length, found lengths {lengths}")
        self.n = lengths.pop()

        self.alphabet = ''.join(sorted(set(''.join(counts.keys()))))
        self.char_to_code = {ch: code for code, ch in enumerate(self.alphabet)}
        alphabet_size = len(self.alphabet)

        total = sum(counts.values())
        floor = math.log2(0.01 / total)
        self.log_frequency_table = np.full(alphabet_size ** self.n, floor, dtype=np.float64)
        for ngram, count in counts.items():
            self.log_frequency_table[self._ngram_code(ngram)] = math.log2(count / total)

    def _ngram_code(self, ngram: str) -> int:
        code = 0
        for ch in ngram:
            code = code * len(self.alphabet) + self.char_to_code[ch]
        return code

    def encode(self, text: str) -> np.ndarray:
        """Map each character of text to its 0-indexed alphabet code."""
        return np.array([self.char_to_code[ch] for ch in text], dtype=np.int64)

    def score(self, text: str) -> float:
        return self.score_encoded(self.encode(text)[None, :])[0]

    def score_encoded(self, codes_batch: np.ndarray) -> np.ndarray:
        """codes_batch: shape (num_candidates, text_length) alphabet codes.
        Returns shape (num_candidates,): negative cross entropy, in bits, of
        each candidate's n-grams against the reference model -- higher is
        better, and values are comparable across candidates of different
        text_length (see module docstring)."""
        alphabet_size = len(self.alphabet)
        text_length = codes_batch.shape[1]
        num_ngrams = text_length - self.n + 1
        ngram_codes = np.zeros((codes_batch.shape[0], num_ngrams), dtype=np.int64)
        for offset in range(self.n):
            power = alphabet_size ** (self.n - 1 - offset)
            ngram_codes += codes_batch[:, offset:text_length - self.n + 1 + offset] * power
        return self.log_frequency_table[ngram_codes].sum(axis=1) / num_ngrams
