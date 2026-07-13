"""
Loader/saver for CryptML (Cryptographic Markup Language) documents.
Format defined in docs/cryptml-spec.md.
"""

import json
from dataclasses import dataclass, field

CRYPTML_VERSION = "1.0"

DEFAULT_SETTINGS = {
    "cipher_system": "unknown",
    "charset": "[A-Z]",
    "casesensitive": False,
    "ditschar": "-",
    "ignorechars": r"\s",
    "plaintext_charset": "[A-Z]",
}

_INHERITED_FIELDS = ("cipher_system", "charset", "casesensitive", "ditschar", "ignorechars")


@dataclass
class CiphertextEntry:
    id: str
    raw: str
    cipher_system: str
    charset: str
    casesensitive: bool
    ditschar: str
    ignorechars: str
    remove_from_start: int = 0
    remove_from_end: int = 0
    origin: dict = field(default_factory=dict)
    sources: list = field(default_factory=list)
    solution: dict | None = None
    hints: list = field(default_factory=list)
    tests: list = field(default_factory=list)
    references: list = field(default_factory=list)
    notes: list = field(default_factory=list)
    chitchat: list = field(default_factory=list)


@dataclass
class CryptMLDocument:
    cryptml_version: str = CRYPTML_VERSION
    title: str = ""
    defaults: dict = field(default_factory=lambda: dict(DEFAULT_SETTINGS))
    references: list = field(default_factory=list)
    notes: list = field(default_factory=list)
    chitchat: list = field(default_factory=list)
    ciphertexts: list = field(default_factory=list)  # list[CiphertextEntry]

    def get(self, id_: str) -> CiphertextEntry:
        for ct in self.ciphertexts:
            if ct.id == id_:
                return ct
        raise KeyError(f"No ciphertext with id {id_!r}")


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


def load(path: str) -> CryptMLDocument:
    """Load a CryptML file, resolving each ciphertext's inherited fields against `defaults`."""
    with open(path, encoding='utf-8') as f:
        data = json.load(f)

    raw_ciphertexts = data.get('ciphertexts')
    if not raw_ciphertexts:
        raise ValueError(f"'{path}' contains no ciphertexts")

    defaults = _resolve_settings(data.get('defaults', {}))

    ciphertexts = []
    for index, ct in enumerate(raw_ciphertexts):
        if 'id' in ct:
            id_ = ct['id']
        elif len(raw_ciphertexts) == 1:
            id_ = "1"
        else:
            raise ValueError(
                f"Ciphertext at index {index} has no 'id', and the file has more than one ciphertext"
            )

        if 'raw' not in ct:
            raise ValueError(f"Ciphertext {id_!r} is missing required field 'raw'")

        ciphertexts.append(CiphertextEntry(
            id=id_,
            raw=ct['raw'],
            cipher_system=ct.get('cipher_system', defaults['cipher_system']),
            charset=ct.get('charset', defaults['charset']),
            casesensitive=ct.get('casesensitive', defaults['casesensitive']),
            ditschar=ct.get('ditschar', defaults['ditschar']),
            ignorechars=ct.get('ignorechars', defaults['ignorechars']),
            remove_from_start=ct.get('remove_from_start', 0),
            remove_from_end=ct.get('remove_from_end', 0),
            origin=ct.get('origin', {}),
            sources=ct.get('sources', []),
            solution=_resolve_solution(ct.get('solution'), defaults),
            hints=ct.get('hints', []),
            tests=ct.get('tests', []),
            references=ct.get('references', []),
            notes=ct.get('notes', []),
            chitchat=ct.get('chitchat', []),
        ))

    return CryptMLDocument(
        cryptml_version=data.get('cryptml_version', CRYPTML_VERSION),
        title=data.get('title', ''),
        defaults=defaults,
        references=data.get('references', []),
        notes=data.get('notes', []),
        chitchat=data.get('chitchat', []),
        ciphertexts=ciphertexts,
    )


def _serialize_solution(solution: dict, defaults: dict) -> dict:
    out = dict(solution)
    if out.get('plaintext_charset') == defaults['plaintext_charset']:
        del out['plaintext_charset']
    return out


def _serialize_ciphertext(ct: CiphertextEntry, defaults: dict) -> dict:
    out = {'id': ct.id, 'raw': ct.raw}
    for name in _INHERITED_FIELDS:
        value = getattr(ct, name)
        if value != defaults[name]:
            out[name] = value
    if ct.remove_from_start:
        out['remove_from_start'] = ct.remove_from_start
    if ct.remove_from_end:
        out['remove_from_end'] = ct.remove_from_end
    if ct.origin:
        out['origin'] = ct.origin
    if ct.sources:
        out['sources'] = ct.sources
    if ct.solution:
        out['solution'] = _serialize_solution(ct.solution, defaults)
    if ct.hints:
        out['hints'] = ct.hints
    if ct.tests:
        out['tests'] = ct.tests
    if ct.references:
        out['references'] = ct.references
    if ct.notes:
        out['notes'] = ct.notes
    if ct.chitchat:
        out['chitchat'] = ct.chitchat
    return out


def save(document: CryptMLDocument, path: str) -> None:
    """Write a CryptML file, omitting per-ciphertext fields that equal the document defaults."""
    data = {
        'cryptml_version': document.cryptml_version,
        'ciphertexts': [_serialize_ciphertext(ct, document.defaults) for ct in document.ciphertexts],
    }
    if document.title:
        data['title'] = document.title
    if document.defaults != DEFAULT_SETTINGS:
        data['defaults'] = document.defaults
    if document.references:
        data['references'] = document.references
    if document.notes:
        data['notes'] = document.notes
    if document.chitchat:
        data['chitchat'] = document.chitchat

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write('\n')
