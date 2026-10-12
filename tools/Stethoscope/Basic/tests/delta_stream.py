"""
STETHOSCOPE test: Delta Stream.

Computes the difference stream of a ciphertext with itself at a given offset.
For offset d and position i: delta[i] = alphabet[(val(stream[i+d]) - val(stream[i])) mod c]
where val(x) is the 0-based index of x in the alphabet and c = len(alphabet).
If either stream[i] or stream[i+d] is DIT, the output at that position is DIT.

Fixture entries come from the top-level "delta_stream" key of the JSON file.
Each entry: {"offset": int, "alphabet": str (optional), "stream": str (prefix to verify)}
The fixture stream may contain DIT characters (·) to represent expected DIT positions.

Validation rules:
- offset outside [1, len(stream)-1]: silently skipped
- alphabet (if given) must contain exactly the charset characters, no repeats; else error
- stream characters must belong to the charset or be DIT; else error
- pass/fail: computed[:len(stream)].upper() == stream.upper()
"""

from dataclasses import dataclass, field
from typing import Optional
import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from ciphertext import CiphertextData, DIT

DEFAULT_ALPHABETS = {
    '[A-Z]':       'ABCDEFGHIJKLMNOPQRSTUVWXYZ',
    '[0-9]':       '0123456789',
    '[A-Za-z0-9]': 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
}


@dataclass
class DeltaEntry:
    offset: int
    alphabet: str
    stream: str


@dataclass
class DeltaResult:
    entries: list
    passed: Optional[bool] = None
    errors: list = field(default_factory=list)


def compute_stream(stream: str, alphabet: str, offset: int) -> str:
    """Compute delta stream from position-preserving stream (may contain DIT)."""
    c = len(alphabet)
    val = {ch: i for i, ch in enumerate(alphabet)}
    result = []
    for i in range(len(stream) - offset):
        if stream[i] == DIT or stream[i + offset] == DIT:
            result.append(DIT)
        else:
            result.append(alphabet[(val[stream[i + offset]] - val[stream[i]]) % c])
    return ''.join(result)


def compute_entries(ct: CiphertextData, offsets: list) -> list:
    """Compute delta streams for given offsets using the default alphabet. No validation."""
    default_alpha = DEFAULT_ALPHABETS.get(ct.charset, ct.alphabet)
    stream_len = len(ct.stream)
    entries = []
    for offset in offsets:
        if 1 <= offset <= stream_len - 1:
            s = compute_stream(ct.stream, default_alpha, offset)
            entries.append(DeltaEntry(offset=offset, alphabet=default_alpha, stream=s))
    return entries


def run(ct: CiphertextData) -> DeltaResult:
    fixture_entries = ct.delta_stream
    if not fixture_entries:
        return DeltaResult(entries=[])

    stream_len = len(ct.stream)
    charset_set = set(ct.alphabet)
    default_alpha = DEFAULT_ALPHABETS.get(ct.charset, ct.alphabet)

    computed_entries = []
    errors = []

    for idx, entry in enumerate(fixture_entries):
        offset = entry.get('offset')

        if not isinstance(offset, int) or not (1 <= offset <= stream_len - 1):
            continue

        alpha_str = entry.get('alphabet', default_alpha).upper()
        if set(alpha_str) != charset_set:
            errors.append(f"entry[{idx}] offset={offset}: alphabet characters don't match charset")
            continue
        if len(alpha_str) != len(set(alpha_str)):
            errors.append(f"entry[{idx}] offset={offset}: alphabet has repeated characters")
            continue

        expected_stream = entry.get('stream', '')
        if not set(expected_stream).issubset(charset_set | {DIT}):
            errors.append(f"entry[{idx}] offset={offset}: stream contains characters outside charset")
            continue

        computed = compute_stream(ct.stream, alpha_str, offset)
        computed_entries.append(DeltaEntry(offset=offset, alphabet=alpha_str, stream=computed))

        k = len(expected_stream)
        if computed[:k] != expected_stream:
            errors.append(
                f"entry[{idx}] offset={offset} alphabet={alpha_str}: "
                f"computed prefix {computed[:k]!r}, expected {expected_stream!r}"
            )

    passed = len(errors) == 0
    return DeltaResult(entries=computed_entries, passed=passed, errors=errors)
