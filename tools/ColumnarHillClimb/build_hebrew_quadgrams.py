"""
Builds a quadgram occurrence count file (see solve_columnar.py's docstring
for the exact file format) from a plain Hebrew text corpus. Every character
that is not a Hebrew letter (spaces, punctuation, digits, niqqud, other
scripts, etc.) is discarded, and final-form letters are folded to their base
letter -- the same normalization solve_columnar.py applies to ciphertext, so
the resulting counts and any ciphertext the solver reads share one alphabet.
Lines whose first non-blank character is '#' are treated as comments and
skipped entirely.

Usage:
    python build_hebrew_quadgrams.py <corpus_file> <output_file>
"""

import argparse
import os
import re
import sys
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'Library'))

from hebrew_text import normalize_finals

HEBREW_LETTER_PATTERN = re.compile('[א-ת]')


def strip_comment_lines(raw_text: str) -> str:
    lines = (line for line in raw_text.splitlines() if not line.lstrip().startswith('#'))
    return '\n'.join(lines)


def extract_letters(raw_text: str) -> str:
    letters = ''.join(HEBREW_LETTER_PATTERN.findall(strip_comment_lines(raw_text)))
    return normalize_finals(letters)


def count_quadgrams(letters: str) -> Counter:
    return Counter(letters[i:i + 4] for i in range(len(letters) - 3))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("corpus_file", help="UTF-8 text file containing Hebrew text")
    parser.add_argument("output_file", help="Where to write the quadgram count file")
    args = parser.parse_args()

    with open(args.corpus_file, encoding='utf-8') as f:
        raw_text = f.read()

    letters = extract_letters(raw_text)
    print(f"Kept {len(letters)} Hebrew letters (final forms normalized) out of {len(raw_text)} characters read.")

    quadgram_counts = count_quadgrams(letters)
    print(f"Found {len(quadgram_counts)} unique quadgrams.")

    with open(args.output_file, 'w', encoding='utf-8') as f:
        for quadgram, count in quadgram_counts.most_common():
            f.write(f"{quadgram}\t{count}\n")


if __name__ == "__main__":
    main()
