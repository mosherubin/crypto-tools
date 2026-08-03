"""
Hill-climbing search for the columnar transposition key, using the segment
slide and segment swap transformations from Lasry's thesis (Chapter 5,
"Case Study - The Columnar Transposition Cipher").

Both transformations operate on contiguous runs of key elements rather than
single elements, which preserves most column-adjacency relationships even
when many key positions change at once -- this is what lets hill climbing
escape local optima that trap single-element-swap search.

- Segment swap: exchange two non-overlapping contiguous runs of length l.
- Segment slide: take a contiguous run of length l starting at p, and slide
  it s positions to the right; equivalently, left-rotate the sub-array
  key[p : p+l+s] by l positions.

At each iteration, every possible segment slide and segment swap of the
current key is tried (steepest-ascent: the single best-scoring transformation
is adopted, if any improves on the current score); this repeats until no
transformation improves the score, i.e. a local maximum is reached.

Decryption and scoring for a whole round of candidates are batched into
single NumPy array operations rather than looped over in Python, since a
round can hold thousands of candidates (O(|K|^3)) and each requires
decrypting and rescoring the full ciphertext.
"""

import random

import numpy as np

from columnar_transposition import random_key


def segment_swap_candidates(key: list) -> list:
    n = len(key)
    candidates = []
    for length in range(1, n // 2 + 1):
        for p1 in range(0, n - length + 1):
            for p2 in range(p1 + length, n - length + 1):
                candidate = list(key)
                candidate[p1:p1 + length], candidate[p2:p2 + length] = (
                    candidate[p2:p2 + length], candidate[p1:p1 + length]
                )
                candidates.append(candidate)
    return candidates


def segment_slide_candidates(key: list) -> list:
    n = len(key)
    candidates = []
    for start in range(n):
        for length in range(1, n - start):
            for shift in range(1, n - start - length + 1):
                end = start + length + shift
                candidate = list(key)
                segment = candidate[start:start + length]
                rest = candidate[start + length:end]
                candidate[start:end] = rest + segment
                candidates.append(candidate)
    return candidates


def decrypt_batch(cipher_codes: np.ndarray, key_batch: np.ndarray) -> np.ndarray:
    """Vectorized equivalent of columnar_transposition.decrypt, for a batch of
    candidate keys at once. cipher_codes: shape (L,) alphabet-code array.
    key_batch: shape (num_candidates, |K|), each row a permutation with
    key[p] = ciphertext column that plaintext column p is transposed to.
    Returns shape (num_candidates, L): decrypted plaintext codes per row."""
    num_candidates, key_length = key_batch.shape
    text_length = cipher_codes.shape[0]
    rows, long_columns = divmod(text_length, key_length)

    inverse_batch = np.argsort(key_batch, axis=1)  # inverse[cand, cipher_col] = plaintext_col
    is_long_column = inverse_batch < long_columns
    column_lengths = np.where(is_long_column, rows + 1, rows)
    column_offsets = np.cumsum(column_lengths, axis=1) - column_lengths

    plaintext_col_start = np.take_along_axis(column_offsets, key_batch, axis=1)  # (num_candidates, |K|)

    row_offsets = np.arange(rows)[None, :, None]
    full_row_positions = plaintext_col_start[:, None, :] + row_offsets  # (num_candidates, rows, |K|)
    full_row_positions = full_row_positions.reshape(num_candidates, rows * key_length)

    if long_columns:
        last_row_positions = plaintext_col_start[:, :long_columns] + rows
        positions = np.concatenate([full_row_positions, last_row_positions], axis=1)
    else:
        positions = full_row_positions

    return cipher_codes[positions]


def _best_neighbor(key: list, cipher_codes: np.ndarray, scorer, current_score: float):
    candidates = segment_slide_candidates(key) + segment_swap_candidates(key)
    key_batch = np.array(candidates, dtype=np.int64)
    plaintext_batch = decrypt_batch(cipher_codes, key_batch)
    scores = scorer.score_encoded(plaintext_batch)

    best_index = int(np.argmax(scores))
    best_score = float(scores[best_index])
    if best_score > current_score:
        return candidates[best_index], best_score
    return None, current_score


def hill_climb(ciphertext: str, key_length: int, scorer, rng: random.Random):
    """Single hill-climbing run from a random initial key to a local maximum."""
    cipher_codes = scorer.encode(ciphertext)
    key = random_key(key_length, rng)
    score = float(scorer.score_encoded(decrypt_batch(cipher_codes, np.array([key], dtype=np.int64)))[0])
    while True:
        candidate, candidate_score = _best_neighbor(key, cipher_codes, scorer, score)
        if candidate is None:
            return key, score
        key, score = candidate, candidate_score
