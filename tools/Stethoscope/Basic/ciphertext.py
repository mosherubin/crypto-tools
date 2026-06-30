"""
Shared foundation for STETHOSCOPE test modules.
Parses a JSON input file and produces a CiphertextData object that all tests consume.
"""

import json
import re
from dataclasses import dataclass, field


@dataclass
class CiphertextData:
    test_case_id: str
    description: str
    raw: str               # original string from JSON, unmodified
    charset: str           # regex pattern used to match valid cipher symbols
    alphabet: str          # ordered string of all symbols matched by charset (e.g. "ABC...Z")
    casesensitive: bool
    ditschar: str          # single character representing a missing symbol
    letters: str           # cleaned text: only charset symbols (dits removed)
    ditscount: int         # number of dits found in the raw (after case-fold)
    expected_results: dict = field(default_factory=dict)
    delta_stream: list = field(default_factory=list)


def _expand_alphabet(charset_re: re.Pattern, casesensitive: bool) -> str:
    """Return all printable ASCII chars (32-126) that match charset_re, in order."""
    candidates = [chr(c) for c in range(32, 127)]
    if not casesensitive:
        # Fold to upper before matching; keep each unique match once
        seen = set()
        result = []
        for ch in candidates:
            folded = ch.upper()
            if charset_re.fullmatch(folded) and folded not in seen:
                seen.add(folded)
                result.append(folded)
        return ''.join(result)
    return ''.join(ch for ch in candidates if charset_re.fullmatch(ch))


def load(path: str) -> CiphertextData:
    """Load and parse a STETHOSCOPE JSON input file."""
    with open(path, encoding='utf-8') as f:
        data = json.load(f)

    ct = data['ciphertext']
    raw: str = ct['raw']

    remove_from_start: int = ct.get('remove_from_start', 0)
    remove_from_end: int = ct.get('remove_from_end', 0)
    if remove_from_start or remove_from_end:
        end = len(raw) - remove_from_end if remove_from_end else len(raw)
        raw = raw[remove_from_start:end]

    charset_pattern: str = ct.get('charset', r'[A-Z]')
    ignorechars_pattern: str = ct.get('ignorechars', r'\s')
    casesensitive: bool = ct.get('casesensitive', False)
    ditschar: str = ct.get('ditschar', '-')

    if len(ditschar) != 1:
        raise ValueError(f"ditschar must be a single character; got '{ditschar}'")

    re_flags = 0 if casesensitive else re.IGNORECASE
    try:
        charset_re = re.compile(charset_pattern, re_flags)
    except re.error as e:
        raise ValueError(f"Invalid charset regex '{charset_pattern}': {e}") from e
    try:
        ignore_re = re.compile(ignorechars_pattern, re_flags)
    except re.error as e:
        raise ValueError(f"Invalid ignorechars regex '{ignorechars_pattern}': {e}") from e

    if ignore_re.fullmatch(ditschar):
        raise ValueError(
            f"ditschar {ditschar!r} will be ignored by the 'ignorechars' regex "
            f"'{ignorechars_pattern}'; modify one of the strings."
        )

    alphabet = _expand_alphabet(charset_re, casesensitive)
    if not alphabet:
        raise ValueError(f"charset regex '{charset_pattern}' matched no printable ASCII characters")

    letters = []
    ditscount = 0
    errors = []

    for offset, ch in enumerate(raw):
        folded = ch if casesensitive else ch.upper()
        if charset_re.fullmatch(folded):
            letters.append(folded)
        elif folded == ditschar:
            ditscount += 1
        elif ignore_re.fullmatch(ch):
            pass  # silently drop
        else:
            errors.append(
                f"Invalid character {ch!r} (offset {offset}) is neither a valid "
                f"cipher symbol, a dit, nor an ignored character"
            )

    if errors:
        raise ValueError(
            f"Ciphertext in '{path}' contains invalid characters:\n"
            + "\n".join(f"  {e}" for e in errors)
        )

    expected_results: dict = data.get('expected_results', {})
    delta_stream: list = data.get('delta_stream', [])

    return CiphertextData(
        test_case_id=data.get('test_case_id', ''),
        description=data.get('description', ''),
        raw=raw,
        charset=charset_pattern,
        alphabet=alphabet,
        casesensitive=casesensitive,
        ditschar=ditschar,
        letters=''.join(letters),
        ditscount=ditscount,
        expected_results=expected_results,
        delta_stream=delta_stream,
    )


def create_from_text(raw: str, charset_pattern: str = '[A-Z]',
                     casesensitive: bool = False,
                     description: str = '',
                     ditschar: str = '-',
                     ignorechars_pattern: str = r'\s') -> CiphertextData:
    """Create CiphertextData directly from a raw string (no JSON file)."""
    re_flags = 0 if casesensitive else re.IGNORECASE
    charset_re = re.compile(charset_pattern, re_flags)
    ignore_re  = re.compile(ignorechars_pattern, re_flags)

    if ignore_re.fullmatch(ditschar):
        raise ValueError(
            f"ditschar {ditschar!r} is matched by ignorechars '{ignorechars_pattern}'"
        )

    alphabet = _expand_alphabet(charset_re, casesensitive)
    if not alphabet:
        raise ValueError(f"charset regex '{charset_pattern}' matched no printable ASCII characters")

    letters = []
    ditscount = 0
    errors = []

    for offset, ch in enumerate(raw):
        folded = ch if casesensitive else ch.upper()
        if charset_re.fullmatch(folded):
            letters.append(folded)
        elif folded == ditschar:
            ditscount += 1
        elif ignore_re.fullmatch(ch):
            pass
        else:
            errors.append(f"Invalid character {ch!r} at position {offset}")

    if errors:
        raise ValueError("Ciphertext contains invalid characters:\n" +
                         "\n".join(f"  {e}" for e in errors[:20]) +
                         (f"\n  ... and {len(errors)-20} more" if len(errors) > 20 else ""))

    return CiphertextData(
        test_case_id='',
        description=description,
        raw=raw,
        charset=charset_pattern,
        alphabet=alphabet,
        casesensitive=casesensitive,
        ditschar=ditschar,
        letters=''.join(letters),
        ditscount=ditscount,
        expected_results={},
    )
