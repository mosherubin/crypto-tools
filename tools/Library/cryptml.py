"""
Loader/saver for CryptML (Cryptographic Markup Language) documents.
Format defined in docs/cryptml-spec.md.
"""

import json
import re
from dataclasses import dataclass, field

CRYPTML_VERSION = "1.0"

DEFAULT_SETTINGS = {
    "cipher_system": "unknown",
    "charset": "[A-Z]",
    "casesensitive": False,
    "ditschar": "-",
    "ignorechars": "[\\s]",
    "plaintext_charset": "[A-Z]",
}

_INHERITED_FIELDS = ("cipher_system", "charset", "casesensitive", "ditschar", "ignorechars")

DOCUMENT_FIELDS = {"cryptml_version", "cryptml_uuid", "title", "defaults", "sources", "references", "notes", "chatter", "ciphertexts"}
_UUID_RE = re.compile(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', re.IGNORECASE)
DEFAULTS_FIELDS = {"cipher_system", "charset", "casesensitive", "ditschar", "ignorechars", "plaintext_charset"}
CIPHERTEXT_FIELDS = {
    "id", "raw", "parts", "cipher_system", "charset", "casesensitive", "ditschar", "ignorechars",
    "remove_from_start", "remove_from_end", "origin", "sources", "references", "notes", "chatter",
    "solution", "hints",
}
PART_FIELDS = {"part_id", "raw", "remove_from_start", "remove_from_end", "origin", "solution", "hints"}
# Ciphertext-level fields that move onto each part instead, once "parts" is used
PART_ONLY_WHEN_SPLIT = {"remove_from_start", "remove_from_end", "origin", "solution", "hints"}
ORIGIN_FIELDS = {"date", "originator", "method", "location", "remarks"}
SOURCE_FIELDS = {"type", "title", "author", "publisher", "date", "page", "url", "note"}
SOURCE_TYPES = {"book", "web", "letter", "periodical", "person", "competition", "other"}
SOLUTION_FIELDS = {"plaintext", "plaintext_charset", "key", "solvers"}
SOLVER_FIELDS = {"solved_by", "solved_date", "method", "notes"}
HINT_FIELDS = {"text", "position", "source", "confidence", "notes"}
REFERENCE_FIELDS = {"citation", "url"}
NOTE_FIELDS = {"title", "text"}
CHATTER_FIELDS = {"author", "date", "text"}

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

    def get(self, id_: str) -> CiphertextEntry:
        for ct in self.ciphertexts:
            if ct.id == id_:
                return ct
        raise KeyError(f"No ciphertext with id {id_!r}")


# ---------- validation ----------

def _is_valid_uuid(value) -> bool:
    return isinstance(value, str) and _UUID_RE.fullmatch(value) is not None


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


def _check_origin(origin, where: str, errors: list) -> None:
    if origin is None:
        return
    _check_fields(origin, ORIGIN_FIELDS, where, errors)


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

    _check_source_list(data.get('sources', []), "document.sources", errors)
    _check_note_list(data.get('notes', []), "document.notes", errors)
    _check_chatter_list(data.get('chatter', []), "document.chatter", errors)

    ciphertexts = data.get('ciphertexts')
    if not ciphertexts:
        errors.append("document.ciphertexts: required, must have at least one entry")
        return errors

    ids_seen = set()
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

        has_raw = 'raw' in ct
        has_parts = 'parts' in ct
        if has_raw and has_parts:
            errors.append(f"{where}: has both 'raw' and 'parts' -- exactly one is required")
        if not has_raw and not has_parts:
            errors.append(f"{where}: has neither 'raw' nor 'parts' -- exactly one is required")

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

        _check_source_list(ct.get('sources', []), f"{where}.sources", errors)
        _check_note_list(ct.get('notes', []), f"{where}.notes", errors)
        _check_chatter_list(ct.get('chatter', []), f"{where}.chatter", errors)

    return errors


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
        sources=ct.get('sources', []),
        references=ct.get('references', []),
        notes=ct.get('notes', []),
        chatter=ct.get('chatter', []),
    )

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


def _serialize_ciphertext(ct: CiphertextEntry, defaults: dict) -> dict:
    out = {'id': ct.id}
    for name in _INHERITED_FIELDS:
        value = getattr(ct, name)
        if value != defaults[name]:
            out[name] = value

    if ct.parts is not None:
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

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write('\n')
