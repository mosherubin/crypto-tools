"""
Builds a quadgram occurrence count file (see solve_columnar.py's docstring
for the exact file format) from one or more Hebrew text corpus files -- both
plain text files and raw MediaWiki XML exports (e.g. a Wikipedia dump,
identified by a ".xml" extension) are accepted directly.

For plain text files: every character that is not a Hebrew letter (spaces,
punctuation, digits, niqqud, other scripts, etc.) is discarded, and
final-form letters are folded to their base letter -- the same
normalization solve_columnar.py applies to ciphertext, so the resulting
counts and any ciphertext the solver reads share one alphabet. Lines whose
first non-blank character is '#' are treated as comments and skipped.

For MediaWiki XML files: only the wikitext inside <page><revision><text> is
considered -- article titles, <siteinfo>, and namespace declarations are
never touched, since they aren't the article author's prose. File/Image/
Category/Template links (e.g. "[[File:x.png|thumb|caption]]") are removed
entirely, since their pipe-separated parameters (size, alignment, etc.) are
not prose either and mwparserfromhell does not know to treat them
specially. What remains is run through mwparserfromhell to strip wiki
markup ([[links]], {{templates}}, '''formatting''', tables, HTML comments,
etc.) down to plain prose before counting quadgrams.

Each input file is counted separately and the counts are summed, so
quadgrams never span the boundary between two files -- nor, for XML files,
between two different <page> elements, since unrelated articles becoming
artificially adjacent would fabricate letter sequences nobody ever wrote.
Files are streamed rather than loaded whole into memory, so even
multi-gigabyte corpora are safe to feed in directly.

Usage:
    python build_hebrew_quadgrams.py <output_file> <corpus_file> [<corpus_file> ...]
        [--heartbeat MB]
"""

import argparse
import os
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter

import mwparserfromhell

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'Library'))

from hebrew_text import normalize_finals

HEBREW_LETTER_PATTERN = re.compile('[א-ת]')

FULL_HEBREW_ALPHABET = sorted(set(normalize_finals(chr(c)) for c in range(0x05D0, 0x05EA + 1)))
THEORETICAL_QUADGRAM_SPACE = len(FULL_HEBREW_ALPHABET) ** 4

QUADGRAM_LENGTH = 4
CARRY_LENGTH = QUADGRAM_LENGTH - 1

NON_PROSE_LINK_PREFIXES = (
    'קובץ:', 'תמונה:', 'קטגוריה:', 'תבנית:',  # Hebrew: File, Image, Category, Template
    'file:', 'image:', 'media:', 'category:', 'template:',  # English aliases
)

OCCURRENCE_BUCKETS = [
    ("seen exactly once", lambda count: count == 1),
    ("seen 2-4 times", lambda count: 2 <= count <= 4),
    ("seen 5-9 times", lambda count: 5 <= count <= 9),
    ("seen 10+ times", lambda count: count >= 10),
]


def extract_hebrew_letters(text: str) -> str:
    return normalize_finals(''.join(HEBREW_LETTER_PATTERN.findall(text)))


def extract_letters_from_line(line: str) -> str:
    if line.lstrip().startswith('#'):
        return ''
    return extract_hebrew_letters(line)


def wikitext_to_plain_text(wikitext: str) -> str:
    wikicode = mwparserfromhell.parse(wikitext)
    for link in wikicode.ifilter_wikilinks():
        if str(link.title).strip().lower().startswith(NON_PROSE_LINK_PREFIXES):
            try:
                wikicode.remove(link)
            except ValueError:
                pass  # already removed as part of an outer link's parameters
    return wikicode.strip_code()


def update_quadgram_counts(quadgram_counts: Counter, letters: str) -> None:
    quadgram_counts.update(
        letters[i:i + QUADGRAM_LENGTH] for i in range(len(letters) - QUADGRAM_LENGTH + 1)
    )


def _local_tag(tag: str) -> str:
    return tag.rsplit('}', 1)[-1]


def process_plain_text_file(path: str, heartbeat_mb: float) -> tuple:
    """Stream a corpus file line by line rather than loading it whole, so
    multi-gigabyte corpora don't exhaust memory. Returns (quadgram_counts,
    chars_read, letters_kept). A small carry-over buffer of the last
    CARRY_LENGTH letters preserves quadgrams that span a line break, since
    only the boundary between two separate files should break them."""
    quadgram_counts = Counter()
    chars_read = 0
    letters_kept = 0
    bytes_read = 0
    carry = ''

    heartbeat_bytes = heartbeat_mb * 1024 * 1024 if heartbeat_mb > 0 else None
    next_heartbeat = heartbeat_bytes

    with open(path, encoding='utf-8') as f:
        for line in f:
            chars_read += len(line)
            bytes_read += len(line.encode('utf-8'))
            letters = extract_letters_from_line(line)
            letters_kept += len(letters)

            combined = carry + letters
            update_quadgram_counts(quadgram_counts, combined)
            carry = combined[-CARRY_LENGTH:]

            if next_heartbeat is not None and bytes_read >= next_heartbeat:
                print(f"[heartbeat] {path}: {bytes_read / (1024 * 1024):,.1f} MB read, "
                      f"{letters_kept:,} letters kept, {len(quadgram_counts):,} unique quadgrams so far")
                next_heartbeat += heartbeat_bytes

    return quadgram_counts, chars_read, letters_kept


def process_wikipedia_xml_file(path: str, heartbeat_mb: float) -> tuple:
    """Stream a MediaWiki XML export, considering only the wikitext inside
    <page><revision><text> elements (see module docstring for what's
    excluded and why). Returns (quadgram_counts, chars_read, letters_kept),
    where chars_read counts the plain text examined per article, not raw XML
    bytes -- the XML itself is mostly tags and markup, not prose, so a ratio
    against raw file size would not mean much. Quadgrams do not span the
    boundary between two different <page> elements."""
    quadgram_counts = Counter()
    chars_read = 0
    letters_kept = 0
    pages_processed = 0

    file_size = os.path.getsize(path)
    heartbeat_bytes = heartbeat_mb * 1024 * 1024 if heartbeat_mb > 0 else None
    next_heartbeat = heartbeat_bytes

    with open(path, 'rb') as raw_file:
        for _, elem in ET.iterparse(raw_file, events=('end',)):
            tag = _local_tag(elem.tag)

            if tag == 'text' and elem.text:
                plain_text = wikitext_to_plain_text(elem.text)
                letters = extract_hebrew_letters(plain_text)
                chars_read += len(plain_text)
                letters_kept += len(letters)
                update_quadgram_counts(quadgram_counts, letters)
                pages_processed += 1

            if tag == 'page':
                elem.clear()  # release this page's parsed content; iterparse keeps building the tree otherwise

                if next_heartbeat is not None:
                    bytes_read = raw_file.tell()
                    if bytes_read >= next_heartbeat:
                        percent = 100 * bytes_read / file_size if file_size else 0
                        print(f"[heartbeat] {path}: {bytes_read / (1024 * 1024):,.1f} MB "
                              f"({percent:.1f}%) read, {pages_processed:,} pages, "
                              f"{letters_kept:,} letters kept, {len(quadgram_counts):,} unique quadgrams so far")
                        next_heartbeat += heartbeat_bytes

    return quadgram_counts, chars_read, letters_kept


def process_corpus_file(path: str, heartbeat_mb: float) -> tuple:
    if path.lower().endswith('.xml'):
        return process_wikipedia_xml_file(path, heartbeat_mb)
    return process_plain_text_file(path, heartbeat_mb)


def print_diagnostics(quadgram_counts: Counter) -> None:
    unique_count = len(quadgram_counts)
    total_instances = sum(quadgram_counts.values())
    coverage = unique_count / THEORETICAL_QUADGRAM_SPACE

    print(f"Theoretical quadgram space: {THEORETICAL_QUADGRAM_SPACE} "
          f"({len(FULL_HEBREW_ALPHABET)}-letter alphabet)")
    print(f"Coverage: {unique_count} / {THEORETICAL_QUADGRAM_SPACE} ({coverage:.1%})")
    if unique_count:
        print(f"Average occurrences per unique quadgram: {total_instances / unique_count:.2f}")

    print("Occurrence distribution:")
    for label, in_bucket in OCCURRENCE_BUCKETS:
        bucket_count = sum(1 for count in quadgram_counts.values() if in_bucket(count))
        fraction = bucket_count / unique_count if unique_count else 0
        print(f"  {label:<20} {bucket_count:>8} ({fraction:.1%})")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("output_file", help="Where to write the quadgram count file")
    parser.add_argument("corpus_files", nargs='+',
                         help="One or more UTF-8 corpus files: plain text, or a MediaWiki XML "
                              "export (.xml extension)")
    parser.add_argument("--heartbeat", type=float, default=100, metavar="MB",
                         help="Print progress every MB megabytes read per file, 0 to disable (default: 100)")
    args = parser.parse_args()

    quadgram_counts = Counter()
    total_chars_read = 0
    total_letters_kept = 0
    for corpus_file in args.corpus_files:
        file_counts, chars_read, letters_kept = process_corpus_file(corpus_file, args.heartbeat)
        quadgram_counts.update(file_counts)
        total_chars_read += chars_read
        total_letters_kept += letters_kept
        print(f"{corpus_file}: kept {letters_kept} Hebrew letters out of {chars_read} characters read.")

    print(f"Total: {total_letters_kept} Hebrew letters from {len(args.corpus_files)} file(s) "
          f"({total_chars_read} characters read).")
    print(f"Found {len(quadgram_counts)} unique quadgrams.")
    print()
    print_diagnostics(quadgram_counts)

    with open(args.output_file, 'w', encoding='utf-8') as f:
        for quadgram, count in quadgram_counts.most_common():
            f.write(f"{quadgram}\t{count}\n")


if __name__ == "__main__":
    main()
