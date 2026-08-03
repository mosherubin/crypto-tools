"""
Columnar transposition cipher mechanics: encryption, decryption, and the
column-length bookkeeping needed for incomplete rectangles (ICT), where the
last row of the plaintext rectangle is only partially filled.

Key representation: key[i] is the 0-indexed ciphertext column position that
plaintext column i is transposed to. len(key) is the key length |K|. This
matches Lasry's notation directly (e.g. numeric key (3,2,7,6,4,5,1) in the
thesis is key = [2,1,6,5,3,4,0] here, 0-indexed).

With ICT, the plaintext rectangle is filled row by row, so the columns that
end up one row longer than the rest are exactly the first u = |text| mod |K|
columns (0-indexed 0..u-1), where u=0 means a complete rectangle (CCT).
"""

import random


def invert(key: list) -> list:
    """inverse[cipher_col] = plaintext_col, given key[plaintext_col] = cipher_col."""
    inverse = [0] * len(key)
    for plaintext_col, cipher_col in enumerate(key):
        inverse[cipher_col] = plaintext_col
    return inverse


def random_key(length: int, rng: random.Random) -> list:
    key = list(range(length))
    rng.shuffle(key)
    return key


def encrypt(plaintext: str, key: list) -> str:
    n = len(key)
    plaintext_columns = [[] for _ in range(n)]
    for index, ch in enumerate(plaintext):
        plaintext_columns[index % n].append(ch)

    inverse = invert(key)
    cipher_chars = []
    for cipher_col in range(n):
        plaintext_col = inverse[cipher_col]
        cipher_chars.extend(plaintext_columns[plaintext_col])
    return ''.join(cipher_chars)


def decrypt(ciphertext: str, key: list) -> str:
    n = len(key)
    rows, long_columns = divmod(len(ciphertext), n)
    inverse = invert(key)

    plaintext_columns = [None] * n
    position = 0
    for cipher_col in range(n):
        plaintext_col = inverse[cipher_col]
        length = rows + 1 if plaintext_col < long_columns else rows
        plaintext_columns[plaintext_col] = ciphertext[position:position + length]
        position += length

    plaintext_chars = []
    for row in range(rows + 1):
        for col in range(n):
            column = plaintext_columns[col]
            if row < len(column):
                plaintext_chars.append(column[row])
    return ''.join(plaintext_chars)
