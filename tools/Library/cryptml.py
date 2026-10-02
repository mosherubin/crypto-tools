"""
Loader/saver for CryptML (Cryptographic Markup Language) documents.
Format defined in docs/cryptml-spec.md.
"""

import json
import re
from dataclasses import dataclass, field

CRYPTML_VERSION = "1.2"

DEFAULT_SETTINGS = {
    "cipher_system": "unknown",
    "charset": "[A-Z]",
    "casesensitive": False,
    "ditschar": "-",
    "ignorechars": "[\\s]",
    "plaintext_charset": "[A-Z]",
    "unit_type": None,
    "codebook_id": None,
    "unit_length": None,
    "channel": None,
}

_INHERITED_FIELDS = ("cipher_system", "charset", "casesensitive", "ditschar", "ignorechars",
                      "unit_type", "codebook_id", "unit_length", "channel")

DOCUMENT_FIELDS = {
    "cryptml_version", "cryptml_uuid", "title", "defaults", "sources", "references", "notes", "chatter",
    "ciphertexts", "service_records", "plaintext_records",
}
_UUID_RE = re.compile(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', re.IGNORECASE)
DEFAULTS_FIELDS = {
    "cipher_system", "charset", "casesensitive", "ditschar", "ignorechars", "plaintext_charset",
    "unit_type", "codebook_id", "unit_length", "channel",
}
CIPHERTEXT_FIELDS = {
    "id", "raw", "parts", "cipher_system", "charset", "casesensitive", "ditschar", "ignorechars",
    "remove_from_start", "remove_from_end", "origin", "sources", "references", "notes", "chatter",
    "solution", "hints",
    # Archival message metadata (CryptML 1.2) -- see "Archival message metadata" in the spec.
    "is_stub", "isa_file", "isa_page", "image_ref", "indicator_raw", "channel", "serial", "gr_stated",
    "pages", "transcription_state", "legibility", "resend_of", "related", "anomaly_notes",
    "preamble_raw", "service_line_raw",
    "unit_type", "unit_type_asserted", "codebook_id", "unit_length", "extensions",
}
PART_FIELDS = {"part_id", "raw", "remove_from_start", "remove_from_end", "origin", "solution", "hints"}
# Ciphertext-level fields that move onto each part instead, once "parts" is used
PART_ONLY_WHEN_SPLIT = {"remove_from_start", "remove_from_end", "origin", "solution", "hints"}
ORIGIN_FIELDS = {"date", "time", "originator", "addressee", "method", "location", "remarks"}
SOURCE_FIELDS = {"type", "title", "author", "publisher", "date", "page", "url", "note"}
SOURCE_TYPES = {"book", "web", "letter", "periodical", "person", "competition", "other"}
SOLUTION_FIELDS = {"plaintext", "plaintext_charset", "key", "solvers"}
SOLVER_FIELDS = {"solved_by", "solved_date", "method", "notes"}
HINT_FIELDS = {"text", "position", "source", "confidence", "notes"}
REFERENCE_FIELDS = {"citation", "url"}
NOTE_FIELDS = {"title", "text"}
CHATTER_FIELDS = {"author", "date", "text"}

UNIT_TYPE_VALUES = {"codebook", "cipher", "unknown"}
TRANSCRIPTION_STATE_VALUES = {"none", "head_tail", "full"}
LEGIBILITY_VALUES = {"clean", "partial", "poor"}
SERVICE_TYPE_VALUES = {"repeat_request", "receipt", "plain_message", "chatter", "other"}
SERVICE_RECORD_FIELDS = {
    "id", "isa_file", "isa_page", "origin", "service_type", "refers_channel", "refers_serial",
    "text_verbatim", "extensions",
}
PLAINTEXT_RECORD_FIELDS = {"id", "isa_file", "isa_page", "origin", "message_ref", "plaintext_verbatim", "extensions"}
INDICATOR_RE = re.compile(r'^([A-Za-z]+)(\d+)(?:/(\d+))?$')

GAP_MARKER = "[...]"


@dataclass
class Part:
    part_id: str
    raw: str
    remove_from_start: int = 0
    remove_from_end: int = 0
    origin: dict = field(default_factory=dict)
    solution: dict | None = None
    hints: list = field(default_factory=list)


@dataclass
class CiphertextEntry:
    id: str
    cipher_system: str
    charset: str
    casesensitive: bool
    ditschar: str
    ignorechars: str
    raw: str | None = None
    parts: list | None = None  # list[Part], mutually exclusive with raw
    remove_from_start: int = 0
    remove_from_end: int = 0
    origin: dict = field(default_factory=dict)
    solution: dict | None = None
    hints: list = field(default_factory=list)
    sources: list = field(default_factory=list)
    references: list = field(default_factory=list)
    notes: list = field(default_factory=list)
    chatter: list = field(default_factory=list)
    # Archival message metadata (CryptML 1.2)
    is_stub: bool = False
    isa_file: str | None = None
    isa_page: str | None = None
    image_ref: str | None = None
    indicator_raw: str | None = None
    channel: str | None = None
    serial: int | None = None
    gr_stated: int | None = None
    pages: int | None = None
    transcription_state: str | None = None
    legibility: str | None = None
    resend_of: str | None = None
    related: list = field(default_factory=list)
    anomaly_notes: str | None = None
    preamble_raw: str | None = None
    service_line_raw: str | None = None
    unit_type: str | None = None
    unit_type_asserted: str | None = None
    codebook_id: str | None = None
    unit_length: int | None = None
    extensions: dict = field(default_factory=dict)


@dataclass
class ServiceRecord:
    id: str
    isa_file: str = ""
    isa_page: str = ""
    origin: dict = field(default_factory=dict)
    service_type: str = ""
    refers_channel: str | None = None
    refers_serial: int | None = None
    text_verbatim: str = ""
    extensions: dict = field(default_factory=dict)


@dataclass
class PlaintextRecord:
    id: str
    isa_file: str = ""
    isa_page: str = ""
    origin: dict = field(default_factory=dict)
    message_ref: str = ""
    plaintext_verbatim: str = ""
    extensions: dict = field(default_factory=dict)


@dataclass
class CryptMLDocument:
    cryptml_version: str = CRYPTML_VERSION
    cryptml_uuid: str | None = None
    title: str = ""
    defaults: dict = field(default_factory=lambda: dict(DEFAULT_SETTINGS))
    sources: list = field(default_factory=list)
    references: list = field(default_factory=list)
    notes: list = field(default_factory=list)
    chatter: list = field(default_factory=list)
    ciphertexts: list = field(default_factory=list)  # list[CiphertextEntry]
    service_records: list = field(default_factory=list)  # list[ServiceRecord]
    plaintext_records: list = field(default_factory=list)  # list[PlaintextRecord]

    def get(self, id_: str) -> CiphertextEntry:
        for ct in self.ciphertexts:
            if ct.id == id_:
                return ct
        raise KeyError(f"No ciphertext with id {id_!r}")


# ---------- validation ----------

def _is_valid_uuid(value) -> bool:
    return isinstance(value, str) and _UUID_RE.fullmatch(value) is not None


def _is_positive_int(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _is_nonneg_int(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _parse_reference(ref):
    """Splits a cross-document reference "<uuid> :: <id>" into its parts, or treats
    a bare string as a same-document id (uuid: None). Returns None if ref isn't a
    non-empty string."""
    if not isinstance(ref, str) or not ref:
        return None
    sep = ref.find(' :: ')
    if sep != -1 and _is_valid_uuid(ref[:sep]):
        return {'uuid': ref[:sep], 'id': ref[sep + 4:]}
    return {'uuid': None, 'id': ref}


def _check_reference_field(ref, where: str, errors: list):
    if not isinstance(ref, str) or not ref.strip():
        errors.append(f"{where}: expected a non-empty reference string, got {ref!r}")
        return None
    parsed = _parse_reference(ref)
    if not parsed['id']:
        errors.append(f"{where}: reference {ref!r} has no id after ' :: '")
        return None
    return parsed


def _clean_length(raw: str, ignore_re) -> int:
    no_gaps = raw.replace(GAP_MARKER, '')
    return sum(1 for ch in no_gaps if not ignore_re.fullmatch(ch))


def _trim_boundary(raw: str, remove_from_start: int, remove_from_end: int, ignore_re):
    """Strips remove_from_start/remove_from_end non-ignored characters from raw's ends,
    exactly like _strip_ignored_boundary in tools/Stethoscope/Basic/ciphertext.py. Group-structure
    checks must count the message's own content, not an embedded indicator token or other boundary
    material that remove_from_start/remove_from_end trims away (e.g. RCA-Outgoing.cryptml embeds
    the indicator in raw itself and strips it with remove_from_start). Returns None if a trim
    amount exceeds the available non-ignored characters, so the caller skips the check rather than
    guess at a length that can't actually be computed."""
    start = 0
    if remove_from_start:
        seen = 0
        for offset, ch in enumerate(raw):
            if not ignore_re.fullmatch(ch):
                seen += 1
                if seen == remove_from_start:
                    start = offset + 1
                    break
        else:
            return None

    end = len(raw)
    if remove_from_end:
        seen = 0
        for offset in range(len(raw) - 1, -1, -1):
            if not ignore_re.fullmatch(raw[offset]):
                seen += 1
                if seen == remove_from_end:
                    end = offset
                    break
        else:
            return None

    return raw[start:end] if start <= end else None


def _is_single_bracketed_class(pattern: str) -> bool:
    if not (isinstance(pattern, str) and pattern.startswith('[') and pattern.endswith(']')):
        return False
    try:
        re.compile(pattern)
    except re.error:
        return False
    inner = pattern[1:-1]
    i = 0
    while i < len(inner):
        if inner[i] == '\\':
            i += 2
            continue
        if inner[i] == ']':
            return False
        i += 1
    return True


def _check_fields(obj, allowed: set, where: str, errors: list) -> None:
    if not isinstance(obj, dict):
        errors.append(f"{where}: expected an object, got {type(obj).__name__}")
        return
    for key in obj:
        if key not in allowed:
            errors.append(f"{where}: unrecognized field '{key}'")


def _check_origin(origin, where: str, errors: list, required_fields=()) -> None:
    if origin is None:
        if required_fields:
            errors.append(f"{where}: required (missing {', '.join(required_fields)})")
        return
    _check_fields(origin, ORIGIN_FIELDS, where, errors)
    if not isinstance(origin, dict):
        return
    for key in required_fields:
        if not origin.get(key):
            errors.append(f"{where}.{key}: required")


def _check_solution(solution, where: str, errors: list) -> None:
    if solution is None:
        return
    _check_fields(solution, SOLUTION_FIELDS, where, errors)
    if not isinstance(solution, dict):
        return
    solvers = solution.get('solvers', [])
    if not isinstance(solvers, list):
        errors.append(f"{where}.solvers must be an array, got {type(solvers).__name__}")
        return
    for i, sv in enumerate(solvers):
        _check_fields(sv, SOLVER_FIELDS, f"{where}.solvers[{i}]", errors)


def _check_hints(hints, where: str, errors: list) -> None:
    for i, h in enumerate(hints):
        _check_fields(h, HINT_FIELDS, f"{where}[{i}]", errors)


def _check_source_list(sources, where: str, errors: list) -> None:
    for i, s in enumerate(sources):
        _check_fields(s, SOURCE_FIELDS, f"{where}[{i}]", errors)
        if isinstance(s, dict) and 'type' in s and s['type'] not in SOURCE_TYPES:
            errors.append(f"{where}[{i}].type = {s['type']!r} not in {sorted(SOURCE_TYPES)}")


def _check_note_list(notes, where: str, errors: list) -> None:
    for i, n in enumerate(notes):
        _check_fields(n, NOTE_FIELDS, f"{where}[{i}]", errors)


def _check_chatter_list(chatter, where: str, errors: list) -> None:
    for i, c in enumerate(chatter):
        _check_fields(c, CHATTER_FIELDS, f"{where}[{i}]", errors)


def _check_raw_chars(raw: str, charset_re, ignore_re, ditschar: str, where: str, errors: list) -> None:
    if not isinstance(raw, str):
        errors.append(f"{where}: expected a string, got {type(raw).__name__}")
        return
    raw_no_gaps = raw.replace(GAP_MARKER, '')
    bad_chars = sorted(set(
        ch for ch in raw_no_gaps
        if not charset_re.fullmatch(ch) and ch != ditschar and not ignore_re.fullmatch(ch)
    ))
    if bad_chars:
        errors.append(f"{where}: characters not matched by charset/ditschar/ignorechars: {bad_chars!r}")


def _check_service_records(records, where: str, errors: list, ids_seen: set, pending_references: list) -> None:
    if records is None:
        return
    if not isinstance(records, list):
        errors.append(f"{where}: expected an array, got {type(records).__name__}")
        return
    for idx, rec in enumerate(records):
        rwhere = f"{where}[{idx}] (id={rec.get('id', '?') if isinstance(rec, dict) else '?'})"
        _check_fields(rec, SERVICE_RECORD_FIELDS, rwhere, errors)
        if not isinstance(rec, dict):
            continue

        rid = rec.get('id')
        if not rid:
            errors.append(f"{rwhere}: missing required 'id'")
        else:
            if rid in ids_seen:
                errors.append(f"{rwhere}: duplicate id '{rid}'")
            ids_seen.add(rid)

        for key in ('isa_file', 'isa_page', 'service_type', 'text_verbatim'):
            if not rec.get(key):
                errors.append(f"{rwhere}.{key}: required")
        if 'service_type' in rec and rec['service_type'] not in SERVICE_TYPE_VALUES:
            errors.append(f"{rwhere}.service_type = {rec['service_type']!r} not in {sorted(SERVICE_TYPE_VALUES)}")

        # 'addressee' is deliberately not required here: a margin annotation or file note
        # captured as a service record may have no addressee at all, and forcing one would
        # just invite a fabricated value.
        _check_origin(rec.get('origin'), f"{rwhere}.origin", errors, required_fields=('date', 'originator'))

        if 'refers_serial' in rec and not _is_nonneg_int(rec['refers_serial']):
            errors.append(f"{rwhere}.refers_serial must be a non-negative integer, got {rec['refers_serial']!r}")

        extensions = rec.get('extensions')
        if extensions is not None and not isinstance(extensions, dict):
            errors.append(f"{rwhere}.extensions must be an object, got {type(extensions).__name__}")

        # refers_channel/refers_serial are descriptive only -- never required to resolve
        # (service traffic routinely references messages that were never catalogued).


def _check_plaintext_records(records, where: str, errors: list, ids_seen: set, pending_references: list) -> None:
    if records is None:
        return
    if not isinstance(records, list):
        errors.append(f"{where}: expected an array, got {type(records).__name__}")
        return
    for idx, rec in enumerate(records):
        rwhere = f"{where}[{idx}] (id={rec.get('id', '?') if isinstance(rec, dict) else '?'})"
        _check_fields(rec, PLAINTEXT_RECORD_FIELDS, rwhere, errors)
        if not isinstance(rec, dict):
            continue

        rid = rec.get('id')
        if not rid:
            errors.append(f"{rwhere}: missing required 'id'")
        else:
            if rid in ids_seen:
                errors.append(f"{rwhere}: duplicate id '{rid}'")
            ids_seen.add(rid)

        for key in ('isa_file', 'isa_page', 'plaintext_verbatim'):
            if not rec.get(key):
                errors.append(f"{rwhere}.{key}: required")

        _check_origin(rec.get('origin'), f"{rwhere}.origin", errors)

        if not rec.get('message_ref'):
            errors.append(f"{rwhere}.message_ref: required")
        else:
            parsed = _check_reference_field(rec['message_ref'], f"{rwhere}.message_ref", errors)
            if parsed:
                pending_references.append({'parsed': parsed, 'where': f"{rwhere}.message_ref", 'raw': rec['message_ref']})

        extensions = rec.get('extensions')
        if extensions is not None and not isinstance(extensions, dict):
            errors.append(f"{rwhere}.extensions must be an object, got {type(extensions).__name__}")


def validate(data: dict) -> list:
    """Validate a parsed CryptML document against the full spec. Returns a list of
    error strings (empty if valid). Does not raise -- collects every problem found."""
    errors = []

    if not isinstance(data, dict):
        return [f"document: expected an object, got {type(data).__name__}"]

    _check_fields(data, DOCUMENT_FIELDS, "document", errors)

    if 'cryptml_uuid' in data and not _is_valid_uuid(data['cryptml_uuid']):
        errors.append(f"document.cryptml_uuid = {data['cryptml_uuid']!r} is not a valid UUID")

    defaults_raw = data.get('defaults', {})
    _check_fields(defaults_raw, DEFAULTS_FIELDS, "defaults", errors)
    defaults = {**DEFAULT_SETTINGS, **(defaults_raw if isinstance(defaults_raw, dict) else {})}

    for key in ('charset', 'ignorechars'):
        if not _is_single_bracketed_class(defaults[key]):
            errors.append(f"defaults.{key} = {defaults[key]!r} is not a single bracketed character class")
    if not isinstance(defaults['ditschar'], str) or len(defaults['ditschar']) != 1:
        errors.append(f"defaults.ditschar must be exactly one character, got {defaults['ditschar']!r}")

    if defaults.get('unit_type') is not None and defaults['unit_type'] not in UNIT_TYPE_VALUES:
        errors.append(f"defaults.unit_type = {defaults['unit_type']!r} not in {sorted(UNIT_TYPE_VALUES)}")
    if defaults.get('unit_length') is not None and not _is_positive_int(defaults['unit_length']):
        errors.append(f"defaults.unit_length must be a positive integer, got {defaults['unit_length']!r}")

    _check_source_list(data.get('sources', []), "document.sources", errors)
    _check_note_list(data.get('notes', []), "document.notes", errors)
    _check_chatter_list(data.get('chatter', []), "document.chatter", errors)

    ciphertexts = data.get('ciphertexts')
    if not ciphertexts:
        errors.append("document.ciphertexts: required, must have at least one entry")
        return errors

    ids_seen = set()
    pending_references = []
    for idx, ct in enumerate(ciphertexts):
        where = f"ciphertexts[{idx}] (id={ct.get('id', '?') if isinstance(ct, dict) else '?'})"
        _check_fields(ct, CIPHERTEXT_FIELDS, where, errors)
        if not isinstance(ct, dict):
            continue

        cid = ct.get('id')
        if cid is None:
            if len(ciphertexts) > 1:
                errors.append(f"{where}: missing 'id', required when there is more than one ciphertext")
        else:
            if cid in ids_seen:
                errors.append(f"{where}: duplicate id '{cid}'")
            ids_seen.add(cid)

        is_stub = ct.get('is_stub') is True
        if 'is_stub' in ct and not isinstance(ct['is_stub'], bool):
            errors.append(f"{where}.is_stub must be a boolean, got {ct['is_stub']!r}")

        has_raw = 'raw' in ct
        has_parts = 'parts' in ct
        if has_raw and has_parts:
            errors.append(f"{where}: has both 'raw' and 'parts' -- exactly one is required")
        if is_stub and (has_raw or has_parts):
            errors.append(f"{where}: is_stub is true but 'raw'/'parts' is also present -- a stub must have neither")
        elif not is_stub and not has_raw and not has_parts:
            errors.append(f"{where}: has neither 'raw' nor 'parts' -- exactly one is required (or set is_stub: true)")

        for key in ('serial', 'gr_stated', 'pages'):
            if key in ct and not _is_nonneg_int(ct[key]):
                errors.append(f"{where}.{key} must be a non-negative integer, got {ct[key]!r}")
        if 'transcription_state' in ct and ct['transcription_state'] not in TRANSCRIPTION_STATE_VALUES:
            errors.append(f"{where}.transcription_state = {ct['transcription_state']!r} not in {sorted(TRANSCRIPTION_STATE_VALUES)}")
        if 'legibility' in ct and ct['legibility'] not in LEGIBILITY_VALUES:
            errors.append(f"{where}.legibility = {ct['legibility']!r} not in {sorted(LEGIBILITY_VALUES)}")
        if 'unit_type' in ct and ct['unit_type'] not in UNIT_TYPE_VALUES:
            errors.append(f"{where}.unit_type = {ct['unit_type']!r} not in {sorted(UNIT_TYPE_VALUES)}")
        if 'unit_type_asserted' in ct and ct['unit_type_asserted'] not in UNIT_TYPE_VALUES:
            errors.append(f"{where}.unit_type_asserted = {ct['unit_type_asserted']!r} not in {sorted(UNIT_TYPE_VALUES)}")
        if 'unit_length' in ct and not _is_positive_int(ct['unit_length']):
            errors.append(f"{where}.unit_length must be a positive integer, got {ct['unit_length']!r}")

        extensions = ct.get('extensions')
        if extensions is not None and not isinstance(extensions, dict):
            errors.append(f"{where}.extensions must be an object, got {type(extensions).__name__}")

        indicator_raw = ct.get('indicator_raw')
        if isinstance(indicator_raw, str):
            m = INDICATOR_RE.match(indicator_raw)
            if m:
                ind_channel, ind_serial = m.group(1), int(m.group(2))
                ind_gr = int(m.group(3)) if m.group(3) is not None else None
                effective_channel = ct.get('channel', defaults.get('channel'))
                if effective_channel is not None and effective_channel != ind_channel:
                    errors.append(f"{where}: channel = {effective_channel!r} doesn't match indicator_raw {indicator_raw!r} (expected {ind_channel!r})")
                if 'serial' in ct and ct['serial'] != ind_serial:
                    errors.append(f"{where}.serial = {ct['serial']!r} doesn't match indicator_raw {indicator_raw!r} (expected {ind_serial})")
                if ind_gr is not None and 'gr_stated' in ct and ct['gr_stated'] != ind_gr:
                    errors.append(f"{where}.gr_stated = {ct['gr_stated']!r} doesn't match indicator_raw {indicator_raw!r} (expected {ind_gr})")
            # a non-matching indicator_raw is free text by design -- the cross-check is
            # simply skipped, not an error.

        if 'resend_of' in ct:
            parsed = _check_reference_field(ct['resend_of'], f"{where}.resend_of", errors)
            if parsed:
                pending_references.append({'parsed': parsed, 'where': f"{where}.resend_of", 'raw': ct['resend_of']})
        if 'related' in ct:
            related = ct['related']
            if not isinstance(related, list):
                errors.append(f"{where}.related must be an array, got {type(related).__name__}")
            else:
                for ridx, r in enumerate(related):
                    parsed = _check_reference_field(r, f"{where}.related[{ridx}]", errors)
                    if parsed:
                        pending_references.append({'parsed': parsed, 'where': f"{where}.related[{ridx}]", 'raw': r})

        ditschar = ct.get('ditschar', defaults['ditschar'])
        if not isinstance(ditschar, str) or len(ditschar) != 1:
            errors.append(f"{where}.ditschar must be exactly one character, got {ditschar!r}")
            ditschar = defaults['ditschar']

        charset = ct.get('charset', defaults['charset'])
        ignorechars = ct.get('ignorechars', defaults['ignorechars'])
        for fname, fval in (('charset', charset), ('ignorechars', ignorechars)):
            if not _is_single_bracketed_class(fval):
                errors.append(f"{where}.{fname} = {fval!r} is not a single bracketed character class")

        casesensitive = ct.get('casesensitive', defaults['casesensitive'])
        flags = 0 if casesensitive else re.IGNORECASE
        try:
            charset_re = re.compile(charset, flags)
            ignore_re = re.compile(ignorechars, flags)
        except re.error as e:
            errors.append(f"{where}: invalid charset/ignorechars regex: {e}")
            charset_re = ignore_re = None

        if charset_re is not None and ignore_re.fullmatch(ditschar):
            errors.append(f"{where}: ditschar {ditschar!r} is also matched by ignorechars {ignorechars!r}")

        if has_parts:
            for f in PART_ONLY_WHEN_SPLIT:
                if f in ct:
                    errors.append(f"{where}: '{f}' is illegal on a ciphertext that uses 'parts' -- move it to each part")

            parts = ct['parts']
            if not isinstance(parts, list) or len(parts) < 2:
                errors.append(f"{where}.parts: must be an array with at least 2 entries")
            else:
                part_ids_seen = set()
                for pidx, part in enumerate(parts):
                    pwhere = f"{where}.parts[{pidx}]"
                    _check_fields(part, PART_FIELDS, pwhere, errors)
                    if not isinstance(part, dict):
                        continue
                    pid = part.get('part_id')
                    if pid is None:
                        errors.append(f"{pwhere}: missing required 'part_id'")
                    elif pid in part_ids_seen:
                        errors.append(f"{pwhere}: duplicate part_id '{pid}'")
                    else:
                        part_ids_seen.add(pid)
                    if 'raw' not in part:
                        errors.append(f"{pwhere}: missing required 'raw'")
                    elif charset_re is not None:
                        _check_raw_chars(part['raw'], charset_re, ignore_re, ditschar,
                                          f"{pwhere}.raw (part_id={pid})", errors)
                    _check_origin(part.get('origin'), f"{pwhere}.origin", errors)
                    _check_solution(part.get('solution'), f"{pwhere}.solution", errors)
                    _check_hints(part.get('hints', []), f"{pwhere}.hints", errors)
        elif has_raw and charset_re is not None:
            _check_raw_chars(ct['raw'], charset_re, ignore_re, ditschar, f"{where}.raw", errors)
            _check_origin(ct.get('origin'), f"{where}.origin", errors)
            _check_solution(ct.get('solution'), f"{where}.solution", errors)
            _check_hints(ct.get('hints', []), f"{where}.hints", errors)

            effective_unit_type = ct.get('unit_type_asserted', ct.get('unit_type', defaults.get('unit_type')))
            effective_unit_length = ct.get('unit_length', defaults.get('unit_length'))
            effective_codebook_id = ct.get('codebook_id', defaults.get('codebook_id'))
            if effective_unit_type == 'codebook':
                if not effective_codebook_id:
                    errors.append(f"{where}: codebook_id is required when unit_type is 'codebook'")
                if _is_positive_int(effective_unit_length) and isinstance(ct.get('raw'), str):
                    trimmed = _trim_boundary(ct['raw'], ct.get('remove_from_start', 0), ct.get('remove_from_end', 0), ignore_re)
                    if trimmed is not None:
                        length = _clean_length(trimmed, ignore_re)
                        if length % effective_unit_length != 0:
                            errors.append(f"{where}: character count ({length}) is not a multiple of unit_length "
                                          f"({effective_unit_length}) for a codebook channel")
        elif is_stub:
            # No raw to check characters/group-structure against, but origin/solution/hints are
            # still ordinary ciphertext-level objects on a stub and must have their shape checked.
            _check_origin(ct.get('origin'), f"{where}.origin", errors)
            _check_solution(ct.get('solution'), f"{where}.solution", errors)
            _check_hints(ct.get('hints', []), f"{where}.hints", errors)

        _check_source_list(ct.get('sources', []), f"{where}.sources", errors)
        _check_note_list(ct.get('notes', []), f"{where}.notes", errors)
        _check_chatter_list(ct.get('chatter', []), f"{where}.chatter", errors)

    _check_service_records(data.get('service_records'), 'document.service_records', errors, ids_seen, pending_references)
    _check_plaintext_records(data.get('plaintext_records'), 'document.plaintext_records', errors, ids_seen, pending_references)

    for pref in pending_references:
        parsed = pref['parsed']
        if parsed['uuid'] is None or parsed['uuid'] == data.get('cryptml_uuid'):
            if parsed['id'] not in ids_seen:
                errors.append(f"{pref['where']}: reference {pref['raw']!r} does not resolve to any id in this document")

    return errors


def validate_warnings(data: dict) -> list:
    """Advisory findings that never affect validate()'s pass/fail contract: a
    gr_stated mismatch, a poor-legibility-but-fully-transcribed message, or a
    short final group on a cipher channel. See "Archival message metadata" in
    the spec."""
    warnings = []
    if not isinstance(data, dict) or not isinstance(data.get('ciphertexts'), list):
        return warnings

    defaults_raw = data.get('defaults', {})
    defaults = {**DEFAULT_SETTINGS, **(defaults_raw if isinstance(defaults_raw, dict) else {})}

    for idx, ct in enumerate(data['ciphertexts']):
        if not isinstance(ct, dict):
            continue
        where = f"ciphertexts[{idx}] (id={ct.get('id', '?')})"

        if ct.get('legibility') == 'poor' and ct.get('transcription_state') == 'full':
            warnings.append(f"{where}: legibility is 'poor' but transcription_state is 'full' -- "
                            f"a statistic built on this transcription may be unreliable")

        if ct.get('is_stub') is True or not isinstance(ct.get('raw'), str):
            continue

        ignorechars = ct.get('ignorechars', defaults['ignorechars'])
        casesensitive = ct.get('casesensitive', defaults['casesensitive'])
        flags = 0 if casesensitive else re.IGNORECASE
        try:
            ignore_re = re.compile(ignorechars, flags)
        except re.error:
            continue

        effective_unit_type = ct.get('unit_type_asserted', ct.get('unit_type', defaults.get('unit_type')))
        effective_unit_length = ct.get('unit_length', defaults.get('unit_length'))
        if not _is_positive_int(effective_unit_length):
            continue

        trimmed = _trim_boundary(ct['raw'], ct.get('remove_from_start', 0), ct.get('remove_from_end', 0), ignore_re)
        if trimmed is None:
            continue
        length = _clean_length(trimmed, ignore_re)
        remainder = length % effective_unit_length
        if effective_unit_type == 'cipher' and remainder != 0:
            warnings.append(f"{where}: short final group of {remainder} character(s) "
                            f"(group width {effective_unit_length}) -- preserved, not padded or trimmed")

        # Only meaningful on a full transcription: on "head_tail"/"none", the counted total
        # is legitimately partial and disagrees with gr_stated by design, not by error.
        if 'gr_stated' in ct and ct.get('transcription_state') == 'full':
            computed_groups = -(-length // effective_unit_length)  # ceil division
            if computed_groups != ct['gr_stated']:
                warnings.append(f"{where}: gr_stated ({ct['gr_stated']}) doesn't match the "
                                f"counted group total ({computed_groups})")

    return warnings


# ---------- loading ----------

def _resolve_settings(document_defaults: dict) -> dict:
    resolved = dict(DEFAULT_SETTINGS)
    resolved.update(document_defaults)
    return resolved


def _resolve_solution(solution: dict | None, defaults: dict) -> dict | None:
    if solution is None:
        return None
    resolved = dict(solution)
    resolved.setdefault('plaintext_charset', defaults['plaintext_charset'])
    return resolved


def _load_part(p: dict, defaults: dict) -> Part:
    return Part(
        part_id=p['part_id'],
        raw=p['raw'],
        remove_from_start=p.get('remove_from_start', 0),
        remove_from_end=p.get('remove_from_end', 0),
        origin=p.get('origin', {}),
        solution=_resolve_solution(p.get('solution'), defaults),
        hints=p.get('hints', []),
    )


def _load_ciphertext(ct: dict, defaults: dict, sole_ciphertext: bool) -> CiphertextEntry:
    id_ = ct.get('id', "1" if sole_ciphertext else None)

    common = dict(
        id=id_,
        cipher_system=ct.get('cipher_system', defaults['cipher_system']),
        charset=ct.get('charset', defaults['charset']),
        casesensitive=ct.get('casesensitive', defaults['casesensitive']),
        ditschar=ct.get('ditschar', defaults['ditschar']),
        ignorechars=ct.get('ignorechars', defaults['ignorechars']),
        unit_type=ct.get('unit_type', defaults.get('unit_type')),
        codebook_id=ct.get('codebook_id', defaults.get('codebook_id')),
        unit_length=ct.get('unit_length', defaults.get('unit_length')),
        channel=ct.get('channel', defaults.get('channel')),
        sources=ct.get('sources', []),
        references=ct.get('references', []),
        notes=ct.get('notes', []),
        chatter=ct.get('chatter', []),
        is_stub=ct.get('is_stub', False),
        isa_file=ct.get('isa_file'),
        isa_page=ct.get('isa_page'),
        image_ref=ct.get('image_ref'),
        indicator_raw=ct.get('indicator_raw'),
        serial=ct.get('serial'),
        gr_stated=ct.get('gr_stated'),
        pages=ct.get('pages'),
        transcription_state=ct.get('transcription_state'),
        legibility=ct.get('legibility'),
        resend_of=ct.get('resend_of'),
        related=ct.get('related', []),
        anomaly_notes=ct.get('anomaly_notes'),
        preamble_raw=ct.get('preamble_raw'),
        service_line_raw=ct.get('service_line_raw'),
        unit_type_asserted=ct.get('unit_type_asserted'),
        extensions=ct.get('extensions', {}),
    )

    if ct.get('is_stub'):
        return CiphertextEntry(**common)

    if 'parts' in ct:
        return CiphertextEntry(
            **common,
            parts=[_load_part(p, defaults) for p in ct['parts']],
        )

    return CiphertextEntry(
        **common,
        raw=ct['raw'],
        remove_from_start=ct.get('remove_from_start', 0),
        remove_from_end=ct.get('remove_from_end', 0),
        origin=ct.get('origin', {}),
        solution=_resolve_solution(ct.get('solution'), defaults),
        hints=ct.get('hints', []),
    )


def _load_service_record(rec: dict) -> ServiceRecord:
    return ServiceRecord(
        id=rec['id'],
        isa_file=rec.get('isa_file', ''),
        isa_page=rec.get('isa_page', ''),
        origin=rec.get('origin', {}),
        service_type=rec.get('service_type', ''),
        refers_channel=rec.get('refers_channel'),
        refers_serial=rec.get('refers_serial'),
        text_verbatim=rec.get('text_verbatim', ''),
        extensions=rec.get('extensions', {}),
    )


def _load_plaintext_record(rec: dict) -> PlaintextRecord:
    return PlaintextRecord(
        id=rec['id'],
        isa_file=rec.get('isa_file', ''),
        isa_page=rec.get('isa_page', ''),
        origin=rec.get('origin', {}),
        message_ref=rec.get('message_ref', ''),
        plaintext_verbatim=rec.get('plaintext_verbatim', ''),
        extensions=rec.get('extensions', {}),
    )


def load(path: str) -> CryptMLDocument:
    """Load and validate a CryptML file, resolving each ciphertext's (and part's)
    inherited fields against `defaults`. Raises ValueError, listing every problem
    found, if the file doesn't conform to the spec."""
    with open(path, encoding='utf-8') as f:
        data = json.load(f)

    errors = validate(data)
    if errors:
        raise ValueError(f"'{path}' is not valid CryptML:\n" + "\n".join(f"  - {e}" for e in errors))

    defaults = _resolve_settings(data.get('defaults', {}))
    raw_ciphertexts = data['ciphertexts']
    sole = len(raw_ciphertexts) == 1
    ciphertexts = [_load_ciphertext(ct, defaults, sole) for ct in raw_ciphertexts]

    return CryptMLDocument(
        cryptml_version=data.get('cryptml_version', CRYPTML_VERSION),
        cryptml_uuid=data.get('cryptml_uuid'),
        title=data.get('title', ''),
        defaults=defaults,
        sources=data.get('sources', []),
        references=data.get('references', []),
        notes=data.get('notes', []),
        chatter=data.get('chatter', []),
        ciphertexts=ciphertexts,
        service_records=[_load_service_record(r) for r in data.get('service_records', [])],
        plaintext_records=[_load_plaintext_record(r) for r in data.get('plaintext_records', [])],
    )


# ---------- saving ----------
#
# Every field inside origin/solution/solver/hint/source/note/chatter is a
# string, so an empty string always means "not filled in" -- save() omits
# those fields (and drops list items left with nothing) so a hand-inspected
# file only shows what was actually recorded. This mirrors what the browser
# editor's trimObject() already does; the two should stay in sync.

def _strip_empty(obj: dict) -> dict:
    return {k: v for k, v in obj.items() if v != ''}


def _strip_empty_list(items: list) -> list:
    cleaned = [_strip_empty(item) for item in items]
    return [item for item in cleaned if item]


def _serialize_solution(solution: dict, defaults: dict) -> dict | None:
    out = _strip_empty({k: v for k, v in solution.items() if k != 'solvers'})
    if out.get('plaintext_charset') == defaults['plaintext_charset']:
        del out['plaintext_charset']
    solvers = _strip_empty_list(solution.get('solvers', []))
    if solvers:
        out['solvers'] = solvers
    return out or None


def _serialize_part(part: Part, defaults: dict) -> dict:
    out = {'part_id': part.part_id, 'raw': part.raw}
    if part.remove_from_start:
        out['remove_from_start'] = part.remove_from_start
    if part.remove_from_end:
        out['remove_from_end'] = part.remove_from_end
    origin = _strip_empty(part.origin) if part.origin else {}
    if origin:
        out['origin'] = origin
    solution = _serialize_solution(part.solution, defaults) if part.solution else None
    if solution:
        out['solution'] = solution
    hints = _strip_empty_list(part.hints)
    if hints:
        out['hints'] = hints
    return out


# 'channel' cascades the same way 'unit_type' does (see _INHERITED_FIELDS) and so is
# deliberately excluded here, same as 'unit_type'/'codebook_id'/'unit_length'.
_ARCHIVAL_FIELDS = (
    'is_stub', 'isa_file', 'isa_page', 'image_ref', 'indicator_raw', 'serial', 'gr_stated',
    'pages', 'transcription_state', 'legibility', 'resend_of', 'related', 'anomaly_notes',
    'preamble_raw', 'service_line_raw',
    'unit_type_asserted', 'extensions',
)


def _serialize_ciphertext(ct: CiphertextEntry, defaults: dict) -> dict:
    out = {'id': ct.id}
    for name in _INHERITED_FIELDS:
        value = getattr(ct, name)
        if value != defaults.get(name):
            out[name] = value

    if ct.is_stub:
        pass  # a stub has neither raw nor parts
    elif ct.parts is not None:
        out['parts'] = [_serialize_part(p, defaults) for p in ct.parts]
    else:
        out['raw'] = ct.raw
        if ct.remove_from_start:
            out['remove_from_start'] = ct.remove_from_start
        if ct.remove_from_end:
            out['remove_from_end'] = ct.remove_from_end
        origin = _strip_empty(ct.origin) if ct.origin else {}
        if origin:
            out['origin'] = origin
        solution = _serialize_solution(ct.solution, defaults) if ct.solution else None
        if solution:
            out['solution'] = solution
        hints = _strip_empty_list(ct.hints)
        if hints:
            out['hints'] = hints

    for name in _ARCHIVAL_FIELDS:
        value = getattr(ct, name)
        if value is None:
            continue
        if name == 'is_stub' and value is False:
            continue
        if name in ('related', 'extensions') and not value:
            continue
        if isinstance(value, str) and value == '':
            continue
        out[name] = value

    sources = _strip_empty_list(ct.sources)
    if sources:
        out['sources'] = sources
    references = _strip_empty_list(ct.references)
    if references:
        out['references'] = references
    notes = _strip_empty_list(ct.notes)
    if notes:
        out['notes'] = notes
    chatter = _strip_empty_list(ct.chatter)
    if chatter:
        out['chatter'] = chatter
    return out


def _serialize_service_record(rec: ServiceRecord) -> dict:
    out = {'id': rec.id, 'isa_file': rec.isa_file, 'isa_page': rec.isa_page}
    origin = _strip_empty(rec.origin) if rec.origin else {}
    if origin:
        out['origin'] = origin
    out['service_type'] = rec.service_type
    if rec.refers_channel:
        out['refers_channel'] = rec.refers_channel
    if rec.refers_serial is not None:
        out['refers_serial'] = rec.refers_serial
    out['text_verbatim'] = rec.text_verbatim
    if rec.extensions:
        out['extensions'] = rec.extensions
    return out


def _serialize_plaintext_record(rec: PlaintextRecord) -> dict:
    out = {'id': rec.id, 'isa_file': rec.isa_file, 'isa_page': rec.isa_page}
    origin = _strip_empty(rec.origin) if rec.origin else {}
    if origin:
        out['origin'] = origin
    out['message_ref'] = rec.message_ref
    out['plaintext_verbatim'] = rec.plaintext_verbatim
    if rec.extensions:
        out['extensions'] = rec.extensions
    return out


def save(document: CryptMLDocument, path: str) -> None:
    """Write a CryptML file, omitting per-ciphertext fields that equal the
    document defaults and any field/list-item left empty after stripping
    blank strings."""
    data = {
        'cryptml_version': document.cryptml_version,
        'ciphertexts': [_serialize_ciphertext(ct, document.defaults) for ct in document.ciphertexts],
    }
    if document.cryptml_uuid:
        data['cryptml_uuid'] = document.cryptml_uuid
    if document.title:
        data['title'] = document.title
    if document.defaults != DEFAULT_SETTINGS:
        data['defaults'] = document.defaults
    sources = _strip_empty_list(document.sources)
    if sources:
        data['sources'] = sources
    references = _strip_empty_list(document.references)
    if references:
        data['references'] = references
    notes = _strip_empty_list(document.notes)
    if notes:
        data['notes'] = notes
    chatter = _strip_empty_list(document.chatter)
    if chatter:
        data['chatter'] = chatter
    if document.service_records:
        data['service_records'] = [_serialize_service_record(r) for r in document.service_records]
    if document.plaintext_records:
        data['plaintext_records'] = [_serialize_plaintext_record(r) for r in document.plaintext_records]

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write('\n')
