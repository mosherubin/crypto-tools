# CryptML — Cryptographic Markup Language

CryptML is a JSON format for exchanging ciphertexts together with the metadata
needed to work with them: origin, sources, character sets, known solutions,
hints, and free-form notes. A document is two-tier: document
level metadata, and a flat list of ciphertexts, each inheriting from the
document unless it overrides. It replaces ad-hoc text files with a single
self-describing container that Moshe's Python and browser tools can read
directly.

A CryptML ciphertext is also guaranteed *clean*, not just conveniently
structured. Every character of `raw` (once the [gap marker](#gap-marker) is
set aside) must classify as a `charset` symbol, the `ditschar`, or an
`ignorechars` character — anything else is a validation error, not a
silently-tolerated stray. That's a real, structural guarantee, not a
convention: a `raw` field can never carry the debris of a copy-paste from a
PDF — smart quotes, ligatures (`ﬁ`), non-breaking spaces, soft hyphens, OCR
noise, mixed line endings — the way a plain text file can. If it doesn't
parse cleanly against its own declared charset, it doesn't validate.
The same judgment applies when transcribing from a printed book: a
cryptogram's trailing sentence-punctuation (e.g. a period, if the book
typesets the cryptogram as the end of a sentence) is the book's, not the
cipher's — leave it out of `raw` rather than adding it to `ignorechars`.

Version described here: **1.0** (draft — schema under review, not yet implemented).

## Design principles

- **Defaults are robust.** A file containing nothing but a raw ciphertext
  string is valid. Every other field has a sensible default.
- **Common settings live once, and cascade — exactly one level.** Settings
  that apply to the whole file (a shared book source, a shared charset) are
  stated once at the document level and flow down to every ciphertext unless
  it overrides them. There is no deeper structure than document → ciphertext:
  an earlier draft of this spec introduced nested "groups" (chapters,
  lessons) with cascading metadata, but real examples showed that the
  metadata that would have cascaded (cipher system, in particular) actually
  varies ciphertext-to-ciphertext even within a chapter or lesson — so the
  extra structure bought nothing and was cut. If a real, demonstrated need
  for grouping resurfaces, it can be added later as a backward-compatible
  extension; nothing here is designed to anticipate it.
- **Strict, not permissive.** Every field is only legal at the level listed
  below. An unrecognized field, or a known field used at the wrong level, is
  a validation error — not a silently-ignored typo. No field anywhere in the
  schema is free-form; every one has a fixed, validated shape. (An earlier
  draft had a `tests` field with free-form `parameters`/`result` for
  recording analysis-tool output. It was cut: test results are a snapshot of
  what one particular tool computed on one particular date, not a durable
  fact about the cryptogram — mixing that into a file meant for global,
  tool-agnostic exchange risks a stranger trusting a stale or buggy number
  as if it carried the same authority as the ciphertext itself. That data
  belongs in a tool-specific fixture format —
  `tools/Stethoscope/Basic/`'s own JSON already serves that purpose — not in
  CryptML.)
- **`id` is free-form.** CryptML does not prescribe a naming convention —
  `"1"`, `"GRP42"`, `"L2-P16-a"` are all just opaque, unique strings. Choosing
  a good convention is the author's job, not the schema's.
- **Vocabulary matches existing tools.** `raw`, `charset`, `casesensitive`,
  `ditschar`, `ignorechars`, `remove_from_start`, `remove_from_end` mean
  exactly what they mean in `tools/Stethoscope/Basic/ciphertext.py`.
- **UTF-8, always.** A CryptML file is UTF-8-encoded JSON text (JSON's own
  interchange encoding, per RFC 8259). Every string field — `title`, `raw`,
  `notes`, `chatter`, `origin.remarks`, `source.author`, and so on — may
  contain any Unicode character; the format itself imposes no language
  restriction. This guarantees free-text metadata can be written in any
  language. It does **not** by itself guarantee that a non-Latin *ciphertext
  alphabet* (e.g. `charset: "[א-ת]"`) works end-to-end through every tool —
  that depends on each tool's own character-handling, not on this encoding
  statement.
- **Corpus membership is opt-in, not automatic.** A CryptML file is assumed
  to carry nothing but ciphertext data by default. `cryptml_uuid` marks a
  file as a member of the published corpus, and it's assigned deliberately —
  never generated automatically on file creation — because most files
  (working files, files produced by extract) are never meant to be part of
  it. See [Corpus identity](#corpus-identity-cryptml_uuid).

## Node types and their legal fields

Two node types exist: **document** (exactly one, the root) and
**ciphertext** (each entry in `ciphertexts`). A field listed for one node
type is a validation error if it appears on the other.

### Document node (root)

| Field | Required | Meaning |
|---|---|---|
| `cryptml_version` | no, default `"1.0"` | Format version. |
| `cryptml_uuid` | no | Marks this file as a corpus member — see [Corpus identity](#corpus-identity-cryptml_uuid). Required only for files under `tools/CryptML/input/`, not by the schema itself. |
| `title` | no | Name for this document/collection. |
| `defaults` | no | Cascading scalar settings — see [Cascade rules](#cascade-rules). |
| `sources` | no | Cascading list — see below. |
| `references` | no | Cascading list. |
| `notes` | no | Cascading list. |
| `chatter` | no | Cascading list. |
| `ciphertexts` | **yes**, ≥1 entry | Array of [ciphertext nodes](#ciphertext-node). |

### Ciphertext node

| Field | Required | Meaning |
|---|---|---|
| `id` | conditionally — see below | Reference name, e.g. `"1"`, `"GRP42"`, `"L2-P16-a"`. Unique across the whole document. |
| `raw` | conditionally — exactly one of `raw`/`parts` required | The ciphertext text, exactly as transcribed. |
| `parts` | conditionally — exactly one of `raw`/`parts` required | Array of ≥2 [part](#part) objects, for one exercise made of several inseparable raw blocks (e.g. messages "a" and "b" that must be solved jointly). See below. |
| `cipher_system` | no, cascades | e.g. `"Vigenère"`, `"Hill"`, `"Quagmire III"`, `"unknown"`. |
| `charset` | no, cascades | Regex character class (e.g. `[A-Z]`) matching valid cipher symbols. To match any character (e.g. a concealment/null cipher), use `[\s\S]` — see [Validation rules](#validation-rules) — not `[.]`, which matches only a literal period. |
| `casesensitive` | no, cascades | Whether `charset` matching is case-sensitive. |
| `ditschar` | no, cascades | Character standing in for a missing/unrecoverable symbol. |
| `ignorechars` | no, cascades | Regex character class (e.g. `[\s]`) of characters silently dropped (whitespace, group separators). |
| `remove_from_start` | no, default `0` | Number of non-ignored characters (i.e. not matched by `ignorechars`) to strip from the start of `raw` — typically a message preamble. Only legal alongside `raw`; with `parts`, each part has its own instead (see below). No cascade. |
| `remove_from_end` | no, default `0` | Number of non-ignored characters to strip from the end of `raw` — typically padding added to reach a group-length multiple. Only legal alongside `raw`; with `parts`, each part has its own instead. No cascade. |
| `origin` | no | No cascade. Only legal alongside `raw`; with `parts`, each part has its own instead. See [origin](#origin). |
| `sources` | no, cascades | This ciphertext's own sources, merged with the document's. |
| `references` | no, cascades | Merged with the document's. |
| `notes` | no, cascades | Merged with the document's. |
| `chatter` | no, cascades | Merged with the document's. |
| `solution` | no | No cascade (except `solution.plaintext_charset`, see below). Only legal alongside `raw`; with `parts`, each part has its own instead — independent messages sharing key material usually decrypt to different plaintexts. See [solution](#solution). |
| `hints` | no | No cascade. Only legal alongside `raw`; with `parts`, each part has its own instead — a crib usually applies to one message's content, not the exercise in the abstract. See [hint](#hint). |

`id` default rule: if `ciphertexts` has exactly one entry, `id` may be
omitted and defaults to `"1"`. Whenever there's more than one ciphertext in
the file, every one of them needs an explicit `id`, and all ids must be
unique across the document.

### `part` (item of a `parts` list)

The split follows one rule: fields describing **the system/exercise as a
whole** (`cipher_system`, `charset`/`casesensitive`/`ditschar`/
`ignorechars`, `sources`/`references`/`notes`/`chatter`) stay on the parent
ciphertext and apply to every part uniformly — that's exactly what makes
independent messages "in depth" in the first place, same system and key.
Fields describing **one specific message's own content and outcome**
(`raw`, `origin`, `solution`, `hints`) move onto each part instead, because
those genuinely differ between independent messages — different plaintexts,
possibly different cribs, possibly even different interception details,
despite sharing key material.

| Field | Required | Meaning |
|---|---|---|
| `part_id` | **yes** | Label for this part, e.g. `"a"`, `"b"`. Unique within the `parts` list. Free-form, like ciphertext `id` — no auto-default, since `parts` never has just one entry. |
| `raw` | **yes** | This part's ciphertext text. |
| `remove_from_start` | no, default `0` | Same meaning as the ciphertext-level field, scoped to this part's `raw`. |
| `remove_from_end` | no, default `0` | Same meaning as the ciphertext-level field, scoped to this part's `raw`. |
| `origin` | no | Same shape as ciphertext-level [origin](#origin), scoped to this part. |
| `solution` | no | Same shape as ciphertext-level [solution](#solution), scoped to this part. |
| `hints` | no | Same shape as ciphertext-level [hint](#hint) list, scoped to this part. |

Two inseparable messages that must be solved jointly (e.g. Military
Cryptanalytics, Part I, Lesson 4, Problem 9's messages 'a' and 'b') — one
`id` and one `cipher_system` shared by both, but each part carries its own
`solution` since the two messages decrypt to different plaintexts:

```json
{
  "id": "MC-I-4-9",
  "cipher_system": "Vigenère (two messages in depth)",
  "parts": [
    { "part_id": "a", "raw": "QLZOV EEXWO ...", "solution": { "plaintext": "ATTACK AT DAWN ..." } },
    { "part_id": "b", "raw": "TKHNS RIOAB ...", "solution": { "plaintext": "HOLD UNTIL REINFORCED ..." } }
  ]
}
```

## Cascade rules

Exactly two cascade behaviors, both document → ciphertext, one level:

1. **Scalar override** (`defaults`: `cipher_system`, `charset`,
   `casesensitive`, `ditschar`, `ignorechars`, `plaintext_charset`). A
   ciphertext's own field, if present, wins; otherwise the document's
   `defaults` value is used; otherwise the built-in default
   (`charset: "[A-Z]"`, `casesensitive: false`, `ditschar: "-"`,
   `ignorechars: "[\\s]"`, `cipher_system: "unknown"`,
   `plaintext_charset: "[A-Z]"`).
2. **List merge** (`sources`, `references`, `notes`, `chatter`). A
   ciphertext's effective list is `document.<field> + ciphertext.<field>`,
   document's entries first, then the ciphertext's own.

Everything else — `id`, `raw`, `parts`, `remove_from_start`,
`remove_from_end`, `origin`, `solution`, `hints` — is ciphertext-only and
never cascades; it's a validation error for any of these to appear on the
document. `solution.plaintext_charset` is the one exception inside a
non-cascading object: it still resolves via the scalar-override chain,
because a plaintext alphabet is conceptually the same kind of setting as
`charset`, just for the solution. Unlike `charset`, though, it's
**descriptive, not enforced** — see [solution](#solution) for why.

## Gap marker

`raw` (or a `part`'s own `raw`, if the ciphertext uses `parts`) may contain
the literal reserved string `"[...]"` to mark a point where an unspecified
number of groups/symbols from the original message were never transcribed —
e.g. an analyst excerpting only the first several and last several groups
of a long message log. This is different from
`ditschar`, which stands for exactly one unrecoverable symbol at a known
position: `[...]` makes no claim about how much is missing, only that
something is. It's also different from `remove_from_start`/
`remove_from_end`, which trim characters that are physically present in
`raw` but unwanted (e.g. page numbers) — `[...]` marks text that was never
transcribed at all.

`[...]` is fixed and universal — not configurable, no cascading override,
and not part of `charset`/`ditschar`/`ignorechars`. A CryptML-aware parser
recognizes it as an atomic token and strips it out *before* doing
per-character `charset`/`ditschar`/`ignorechars` classification on what
remains; it never appears in the cleaned letter stream and is never counted
as a `ditschar`. (`tools/Stethoscope/Basic/ciphertext.py` currently
classifies `raw` strictly character-by-character and will need a first pass
added to recognize and strip this token before its existing per-character
scan runs — a real, if small, change to that parser, not just documentation
here.)

```json
{ "id": "1", "raw": "AXBQP LKQRS DTMNC FVXWA QPLEZ TRSUV WNMKL [...] QRTSU VWXYZ ABCDE" }
```

Multiple occurrences in one `raw` are allowed; there's no cap.

## Corpus identity (`cryptml_uuid`)

`cryptml_uuid` is an optional document-level UUIDv4 string. Its presence
marks a file as a member of the published corpus — something meant to be
queried, searched, and merged into the CryptML database project
(`tools/CryptML/input/` in the GitHub repo) — and it's what makes a
ciphertext globally addressable from outside the file it lives in: an
external consumer refers to a specific ciphertext as the pair
`(cryptml_uuid, id)`.

Most CryptML files never need one. A file is assumed to carry nothing but
ciphertext data by default. Files produced by the extract tool never carry
a `cryptml_uuid`, even if their source file had one — an extracted file is
a working copy of ciphertext content, not a corpus member, and is never a
candidate for inclusion. No CryptML-aware tool auto-generates
`cryptml_uuid` on file creation; it's assigned only by an explicit action,
taken when an author decides a file is actually meant to be submitted as a
pull request into the corpus.

`cryptml_uuid` is generated once and never regenerated. That's what lets a
file be renamed or moved later without losing its identity: identity lives
inside the file's own content, not in its filename or location. The
published manifest (`tools/CryptML/input/index.json`) is a derived index
built by reading every corpus file's own `cryptml_uuid` — it is never the
source of truth, and it never assigns one itself.

When ciphertexts from one file are folded into another via the merge tool,
they adopt the target file's existing `cryptml_uuid`. A ciphertext's global
identity is scoped to whichever corpus file currently contains it, not to
the ciphertext itself — moving a ciphertext between files changes its
`(cryptml_uuid, id)` address.

Two validation tiers apply:

- **Format** — enforced everywhere, by the same `validate()` the Editor,
  Validator, List, and Search tools all share: if `cryptml_uuid` is
  present, it must be a syntactically valid UUID. Its absence is not an
  error; it just means the file isn't a corpus member.
- **Corpus membership** — enforced only by the tooling that manages
  `tools/CryptML/input/` (`generate-manifest.js`, the local pre-commit
  hook, the GitHub Action), not by the general schema validator: every file
  in that directory must have a `cryptml_uuid`, and no two corpus files may
  share one.

## Validation rules

- **`[...]` inside `raw`** is the reserved gap marker (see
  [Gap marker](#gap-marker) above), not cipher-alphabet content — it is
  never validated against `charset`.
- **Every remaining character of `raw` must classify.** Once gap markers are
  removed, each character must match `charset`, equal `ditschar`, or match
  `ignorechars` — there is no fourth bucket. A character that matches none
  of the three is a validation error. This is the mechanism behind the
  "guaranteed clean" claim above: a `raw` field can never quietly carry
  unaccounted-for characters. With `parts`, this rule applies independently
  to each part's own `raw`, against the same ciphertext-level `charset`/
  `ditschar`/`ignorechars`.
- **A ciphertext has exactly one of `raw` or `parts`.** Neither, or both,
  is a validation error.
- **`parts` must have at least 2 entries.** A single-entry `parts` array is
  rejected — use `raw` instead; there's exactly one way to say "one raw
  block."
- **`part_id` is required and unique within its `parts` list.** No
  auto-default, since `parts` never has just one entry to default from.
- **`remove_from_start`/`remove_from_end` are illegal on a ciphertext that
  uses `parts`.** Use each part's own instead — there's no single `raw` on
  that ciphertext for a ciphertext-level trim to unambiguously apply to.
- **`origin`, `solution`, and `hints` are likewise illegal on a ciphertext
  that uses `parts`.** Use each part's own instead — these describe one
  message's own content and outcome, which independent in-depth messages
  don't share even when their cipher system and key do.
- **Unknown fields are errors.** Every node type and every sub-object below
  has a fixed field set. A key not in that set is rejected.
- **Misplaced fields are errors**, symmetrically: a ciphertext-only field
  (`raw`, `parts`, `remove_from_start`, `remove_from_end`, `origin`,
  `solution`, `hints`) found on the document is an error; a document-only
  field (`cryptml_version`, `title`, `defaults`, `ciphertexts`) found on a
  ciphertext is an error.
- **Duplicate `id` anywhere in `ciphertexts` is an error.**
- **`cryptml_uuid`, if present, must be a syntactically valid UUID.**
  Requiring it (and rejecting duplicates across files) is a separate,
  stricter rule that applies only to corpus files — see
  [Corpus identity](#corpus-identity-cryptml_uuid).
- **`source.type`** must be one of the enumerated values (see below) — not
  an arbitrary string.
- **`ditschar`** must be exactly one character.
- **`charset` and `ignorechars`** must each be a single bracketed regex
  character class — `[...]` or `[^...]` — spanning the entire value, and
  must compile. Nothing is allowed outside the brackets: no quantifiers,
  groups, alternation, or anchors. `[A-Z]` is valid; `[A-Z]+`, `A-Z`, and
  `A|B|C` are not. Brackets are always required **on disk** — a CryptML
  file is never expected to contain a bare `A-Z`. (The browser editor may
  let you type `A-Z` and auto-wrap it to `[A-Z]` before saving, as a
  data-entry convenience, but that's an editor behavior, not a
  file-format allowance — every reader can assume brackets are always
  present and never needs its own normalization step.) `plaintext_charset`
  is exempt from this rule entirely — see [solution](#solution).
- **To match any character at all** (e.g. a concealment/null cipher, where
  `raw` is ordinary prose rather than a restricted cipher alphabet), use
  `charset: "[\s\S]"`, not `charset: "[.]"`. Inside a character class, `.`
  loses its special "any character" meaning and matches only a literal
  period — `[.]` rejects every letter, digit, and space. `[\s\S]`
  ("whitespace or non-whitespace") is the standard idiom for "match
  anything," including characters plain `.` doesn't match by default, like
  newlines. Pair it with `casesensitive: true` if the original casing of
  the text is meaningful, since the default (`false`) forces the derived
  letter stream to uppercase.

## Shared sub-object shapes

`origin` and `source` are easy to conflate but answer different questions.
`origin` is the one-of-a-kind story of how *this specific ciphertext* came
to exist and how you came to have it — one story per ciphertext, never
cascades. `source` is a bibliographic citation of where it's published or
documented, and a ciphertext can have more than one (a real intercept might
be in a book *and* discussed on a web forum) — hence `sources` is a list,
and it cascades (see [Cascade rules](#cascade-rules)).

### `origin`

| Field | Type | Meaning |
|---|---|---|
| `date` | string | When the message/cryptogram itself was created or transmitted — not when it was published. |
| `originator` | string | Who composed or sent it — the puzzle's setter, or a real message's sender. Not the author of a book it later appeared in; see `source.author` for that. |
| `method` | string | How this copy was produced or obtained, e.g. "transcribed from photo", "typed from book". |
| `location` | string | Free text, e.g. where it was found or created. |
| `remarks` | string | Anything else about the origin. |

### `source` (item of a `sources` list)

| Field | Type | Meaning |
|---|---|---|
| `type` | one of `book`, `web`, `letter`, `periodical`, `person`, `competition`, `other` | |
| `title` | string | Title of the book/page/periodical/etc. |
| `author` | string | Author of the publication — not who composed the cryptogram itself; see `origin.originator` for that. |
| `publisher` | string | Publisher, if applicable. |
| `date` | string | Publication or acquisition date of this citation — not when the ciphertext itself was created. |
| `page` | string | Page/section reference. |
| `url` | string | URL, if a web source. |
| `note` | string | Anything else about this source. |

### `solution`

| Field | Type | Cascades? |
|---|---|---|
| `plaintext` | free text | no |
| `plaintext_charset` | descriptive string, default inherited via scalar-override chain | **yes** (exception, see above) |
| `key` | string | no |
| `solvers` | array of [solver](#solver) objects | no |

`plaintext`, `plaintext_charset`, and `key` describe the solution itself and
occur once. Multiple people may have solved the same cipher independently,
by different methods, at different times — `solvers` records each of those
attempts separately rather than forcing one `solved_by`/`method` pair to
speak for all of them.

`plaintext` is free text, not validated character-by-character the way
`raw` is validated against `charset`. A recovered plaintext is usually
written the way a person would naturally write it — mixed case,
punctuation, even `...` for a partial or truncated answer — not forced into
an all-caps letter stream. `plaintext_charset` still cascades the same way
`charset` does, but it's **descriptive only**: it documents what alphabet
the cipher's underlying units correspond to (e.g. a Tridigital cipher's
digit-triples map to `[A-Z]`), not an enforced constraint on `plaintext`
itself.

### `solver` (item of a `solvers` list)

| Field | Type |
|---|---|
| `solved_by` | string |
| `solved_date` | string |
| `method` | string |
| `notes` | string |

### `hint` (item of a `hints` list)

| Field | Type |
|---|---|
| `text` | string |
| `position` | string |
| `source` | string |
| `confidence` | string |
| `notes` | string |

### `reference` (item of a `references` list)

| Field | Type |
|---|---|
| `citation` | string |
| `url` | string |

### `note` (item of a `notes` list)

| Field | Type |
|---|---|
| `title` | string |
| `text` | string |

### `chatter` (item of a `chatter` list)

| Field | Type |
|---|---|
| `author` | string |
| `date` | string |
| `text` | string |

## Minimal example

Relies entirely on defaults:

```json
{
  "cryptml_version": "1.0",
  "ciphertexts": [
    { "raw": "WKRUL BXHVI DQGWK HODZQ FRXOG..." }
  ]
}
```

## Illustrative example

A whole-file shared source (merges into every ciphertext), a document-wide
charset default (overridden by one ciphertext that needs a different
alphabet), free-form ids, and one solved entry.

```json
{
  "cryptml_version": "1.0",
  "title": "MC-I Problem Book, Lesson 2 (excerpt)",
  "defaults": { "charset": "[A-Z]", "casesensitive": false, "ditschar": "-", "ignorechars": "[\\s]" },
  "sources": [
    { "type": "book", "title": "Military Cryptanalytics, Part I, Problem Book", "author": "NSA", "page": "L2" }
  ],
  "ciphertexts": [
    {
      "id": "L2-P16-a",
      "raw": "...",
      "cipher_system": "Playfair"
    },
    {
      "id": "L2-P16-b",
      "raw": "...",
      "cipher_system": "Nihilist Substitution",
      "solution": {
        "plaintext": "ATTACKATDAWN",
        "key": "3-1-2",
        "solvers": [
          { "solved_by": "Moshe", "solved_date": "2026-06-20", "method": "frequency analysis of digit triples" },
          { "solved_by": "J. Doe", "solved_date": "2026-06-22", "notes": "Solved independently via crib-dragging, before seeing Moshe's writeup." }
        ]
      }
    },
    {
      "id": "L2-P17",
      "raw": "213 132 321",
      "cipher_system": "Tridigital",
      "charset": "[1-3]"
    }
  ]
}
```

Resolved view of `L2-P16-a`: `charset = "[A-Z]"` / `casesensitive = false` /
`ditschar = "-"` / `ignorechars = "[\\s]"` (all from the document, unchanged),
`cipher_system = "Playfair"` (its own), `sources = [ {"type": "book",
"title": "Military Cryptanalytics, Part I, Problem Book", ...} ]` (merged
down from the document — it has none of its own). `L2-P17` overrides
`charset` to `"[1-3]"` for its own use, everything else still cascades
normally.

## Example: single-`raw` and `parts` ciphertexts side by side

Two ciphertexts in one document — an ordinary single-message problem, and
an in-depth pair. `MC-I-4-7` looks exactly like every other ciphertext
you've already seen. `MC-I-4-9` has no `raw`, `origin`, `solution`, or
`hints` of its own at all — those all live on its two parts instead,
because `cipher_system` is the only thing 'a' and 'b' actually share.

```json
{
  "cryptml_version": "1.0",
  "title": "Military Cryptanalytics, Part I, Lesson 4 (excerpt)",
  "defaults": { "charset": "[A-Z]", "casesensitive": false, "ditschar": "-", "ignorechars": "[\\s]" },
  "sources": [
    { "type": "book", "title": "Military Cryptanalytics, Part I", "author": "Friedman and Callimahos" }
  ],
  "ciphertexts": [
    {
      "id": "MC-I-4-7",
      "raw": "WKRUL BXHVI DQGWK HODZQ FRXOG",
      "cipher_system": "Monoalphabetic substitution",
      "solution": { "plaintext": "THE QUICK BROWN FOX" }
    },
    {
      "id": "MC-I-4-9",
      "cipher_system": "Vigenère (two messages in depth)",
      "parts": [
        {
          "part_id": "a",
          "raw": "QLZOV EEXWO ...",
          "origin": { "date": "1943-06", "method": "intercepted teleprinter traffic" },
          "hints": [ { "text": "Believed to begin with a standard preamble." } ],
          "solution": { "plaintext": "ATTACK AT DAWN ..." }
        },
        {
          "part_id": "b",
          "raw": "TKHNS RIOAB ...",
          "solution": { "plaintext": "HOLD UNTIL REINFORCED ..." }
        }
      ]
    }
  ]
}
```

Note that `origin`/`hints` are entirely optional per part — part 'a' has
both, part 'b' has neither, and that's fine; nothing requires parts to be
symmetric with each other.

## Invalid examples

```json
// ERROR: "hints" is ciphertext-only, not legal on the document.
{ "cryptml_version": "1.0", "hints": [{"text": "THE"}], "ciphertexts": [...] }
```
```json
// ERROR: "defaults" is not legal on a ciphertext (its scalars are bare fields instead).
{ "id": "1", "raw": "...", "defaults": { "charset": "[A-Z]" } }
```
```json
// ERROR: "priority" is not a recognized field anywhere in the schema.
{ "cryptml_version": "1.0", "priority": "high", "ciphertexts": [...] }
```
```json
// ERROR: two ciphertexts share id "1".
{ "ciphertexts": [ { "id": "1", "raw": "..." }, { "id": "1", "raw": "..." } ] }
```
```json
// ERROR: "charset" has no enclosing brackets. On disk it must be "[1-3]",
// not "1-3" -- the editor may let you type it bare, but never saves it that way.
{ "id": "1", "raw": "213132", "charset": "1-3" }
```

## Future work

- An XML serialization of the same schema (not yet defined).
- A formal JSON Schema for automated validation.
- Reconsider a cascading grouping mechanism if a real corpus demonstrates
  clear, repeated duplication that document-level `defaults` can't address.
- Non-Latin ciphertext alphabets (`charset`/`raw` composed of e.g. Hebrew or
  Cyrillic symbols) are a known gap: `tools/Stethoscope/Basic/ciphertext.py`'s
  alphabet expansion only scans printable ASCII, so such a `charset` would
  pass CryptML's own validation but fail in that tool. Deliberately deferred
  — revisit only if a real ciphertext in another script actually shows up.
- A `tests` field for recording analysis-tool output was drafted and then
  cut (see "Strict, not permissive" above for why). Revisit only if a real,
  cross-tool need for shared test-result interchange emerges — and if so,
  it belongs in a separate, tool-scoped format, not folded back into
  CryptML itself.
