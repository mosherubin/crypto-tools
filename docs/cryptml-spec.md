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

Version described here: **1.2**.

**1.2** adds [archival message metadata](#archival-message-metadata): a `service_records`/
`plaintext_records` pair of document-level arrays for traffic with no ciphertext of its own, an `is_stub`
ciphertext flag licensing a message record with neither `raw` nor `parts`, a cascading `unit_type`/
`codebook_id`/`unit_length` classification for group-structure validation, `origin.addressee`, a reserved
free-form `extensions` object, optional `id` and `identifier` on a source with a `source_id` field that lets
a ciphertext or record name exactly one of them, and a set of optional archival provenance/indicator/quality
fields. A separate, non-blocking `validateWarnings()` channel is introduced alongside the existing pass/fail
`validate()`. All of this is purely additive and optional: files written under 1.0 or 1.1 remain valid
as-is, with no need to edit or re-version them. The archival field set was revised on 4 October 2026,
before any data used it: `isa_file` and `image_ref` were removed, `isa_page` became `archive_page`, and
`source_id` and source `id`/`identifier` were added. **1.1** added `origin.time` (see [origin](#origin))
alongside the existing `origin.date`. **1.0** was the initial release.

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
| `cryptml_version` | no, default `"1.2"` | Format version. |
| `cryptml_uuid` | no | Marks this file as a corpus member — see [Corpus identity](#corpus-identity-cryptml_uuid). Required only for files under `tools/CryptML/input/`, not by the schema itself. Also used to qualify a cross-document reference — see [Archival message metadata](#archival-message-metadata). |
| `title` | no | Name for this document/collection. |
| `defaults` | no | Cascading scalar settings — see [Cascade rules](#cascade-rules). |
| `sources` | no | Cascading list — see below. |
| `references` | no | Cascading list. |
| `notes` | no | Cascading list. |
| `chatter` | no | Cascading list. |
| `ciphertexts` | **yes**, ≥1 entry | Array of [ciphertext nodes](#ciphertext-node). |
| `service_records` | no | Array of [service records](#service-record) — plaintext traffic with no ciphertext of its own. See [Archival message metadata](#archival-message-metadata). |
| `plaintext_records` | no | Array of [plaintext records](#plaintext-record) — a recovered plaintext for a known message. See [Archival message metadata](#archival-message-metadata). |

### Ciphertext node

| Field | Required | Meaning |
|---|---|---|
| `id` | conditionally — see below | Reference name, e.g. `"1"`, `"GRP42"`, `"L2-P16-a"`. Unique across the whole document. |
| `raw` | conditionally — exactly one of `raw`/`parts` required, unless `is_stub` | The ciphertext text, exactly as transcribed. |
| `parts` | conditionally — exactly one of `raw`/`parts` required, unless `is_stub` | Array of ≥2 [part](#part) objects, for one exercise made of several inseparable raw blocks (e.g. messages "a" and "b" that must be solved jointly). See below. |
| `is_stub` | no, default `false` | When `true`, licenses omitting *both* `raw` and `parts` — a catalogued record with no transcribed ciphertext. Illegal alongside either. See [Archival message metadata](#archival-message-metadata). |
| `cipher_system` | no, cascades | e.g. `"Vigenère"`, `"Hill"`, `"Quagmire III"`, `"unknown"`. |
| `charset` | no, cascades | Regex character class (e.g. `[A-Z]`) matching valid cipher symbols. To match any character (e.g. a concealment/null cipher), use `[\s\S]` — see [Validation rules](#validation-rules) — not `[.]`, which matches only a literal period. |
| `casesensitive` | no, cascades | Whether `charset` matching is case-sensitive. |
| `ditschar` | no, cascades | Character standing in for a missing/unrecoverable symbol. |
| `ignorechars` | no, cascades | Regex character class (e.g. `[\s]`) of characters silently dropped (whitespace, group separators). |
| `remove_from_start` | no, default `0` | Number of non-ignored characters (i.e. not matched by `ignorechars`) to strip from the start of `raw` — typically a message preamble. Only legal alongside `raw`; with `parts`, each part has its own instead (see below). No cascade. |
| `remove_from_end` | no, default `0` | Number of non-ignored characters to strip from the end of `raw` — typically padding added to reach a group-length multiple. Only legal alongside `raw`; with `parts`, each part has its own instead. No cascade. |
| `origin` | no | No cascade. Illegal on a ciphertext that uses `parts` (each part has its own instead); legal on both an ordinary `raw` message and a stub — see [Stub entries](#stub-entries-is_stub). See [origin](#origin). |
| `sources` | no, cascades | This ciphertext's own sources, merged with the document's. |
| `references` | no, cascades | Merged with the document's. |
| `notes` | no, cascades | Merged with the document's. |
| `chatter` | no, cascades | Merged with the document's. |
| `solution` | no | No cascade (except `solution.plaintext_charset`, see below). Illegal on a ciphertext that uses `parts` (each part has its own instead — independent messages sharing key material usually decrypt to different plaintexts); legal on both an ordinary `raw` message and a stub. See [solution](#solution). |
| `hints` | no | No cascade. Illegal on a ciphertext that uses `parts` (each part has its own instead — a crib usually applies to one message's content, not the exercise in the abstract); legal on both an ordinary `raw` message and a stub. See [hint](#hint). |
| `unit_type` | no, cascades | `"codebook"` \| `"cipher"` \| `"unknown"` — what the group structure *is*, for arithmetic/validation purposes. See [Archival message metadata](#archival-message-metadata). |
| `unit_type_asserted` | no, no cascade | Overrides the cascaded `unit_type` for rule-selection on this one message — highest precedence. Legal on any message, not just a stub. See [Archival message metadata](#archival-message-metadata). |
| `codebook_id` | no, cascades | Free-string identifier of the codebook in use. Required whenever the effective `unit_type` is `"codebook"`. |
| `unit_length` | no, cascades | Positive integer group/code-word width, used by the group-structure check. |
| `channel` | no, cascades | Parsed channel prefix, e.g. `"A"`, `"NP"` — cascades because a survey typically holds one file per channel. Cross-checked against `indicator_raw` — see [Archival message metadata](#archival-message-metadata). |
| `source_id`, `archive_page`, `indicator_raw`, `serial`, `gr_stated`, `pages`, `transcription_state`, `legibility`, `resend_of`, `related`, `anomaly_notes`, `preamble_raw`, `service_line_raw` | no | Archival provenance/indicator/quality/cross-reference fields — see [Archival message metadata](#archival-message-metadata). `source_id` names one document-level [source](#source-item-of-a-sources-list) that has an `id`. |
| `extensions` | no | Reserved free-form object, entirely unvalidated — see [Archival message metadata](#archival-message-metadata). |

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
   `casesensitive`, `ditschar`, `ignorechars`, `plaintext_charset`,
   `unit_type`, `codebook_id`, `unit_length`, `channel`). A
   ciphertext's own field, if present, wins; otherwise the document's
   `defaults` value is used; otherwise the built-in default
   (`charset: "[A-Z]"`, `casesensitive: false`, `ditschar: "-"`,
   `ignorechars: "[\\s]"`, `cipher_system: "unknown"`,
   `plaintext_charset: "[A-Z]"`). `unit_type`/`codebook_id`/`unit_length`/
   `channel` have no built-in default — absent at every level simply means
   "not classified"/"not recorded." `unit_type_asserted` is a related but
   **non-cascading** field — see
   [Archival message metadata](#archival-message-metadata). `channel`
   cascades because a real survey typically holds one file per channel (see
   [Archival message metadata](#archival-message-metadata)), so repeating the
   same channel string on every one of several hundred messages would invite
   drift; the per-message override still exists for a document that mixes
   channels. The [indicator consistency check](#archival-message-metadata)
   cross-checks the *effective* (cascaded) `channel` against each message's
   own `indicator_raw`, not just a locally-set one.
2. **List merge** (`sources`, `references`, `notes`, `chatter`). A
   ciphertext's effective list is `document.<field> + ciphertext.<field>`,
   document's entries first, then the ciphertext's own. **One exception:**
   a document-level source that has an `id` is *not* merged into every
   ciphertext. It applies only to a ciphertext (or record) whose `source_id`
   names it. A ciphertext's effective sources are therefore, in this order,
   the document sources *without* an `id`, then the one source named by its
   `source_id` (if any), then its own `sources`.

Everything else — `id`, `raw`, `parts`, `is_stub`, `remove_from_start`,
`remove_from_end`, `origin`, `solution`, `hints`, `unit_type_asserted`,
`source_id`, `archive_page`, `indicator_raw`, `serial`,
`gr_stated`, `pages`, `transcription_state`, `legibility`, `resend_of`,
`related`, `anomaly_notes`, `preamble_raw`, `service_line_raw`, `extensions`
— is ciphertext-only and
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

## Archival message metadata

This extension lets CryptML serve as the single authoritative store for an
archival survey of real traffic — e.g. a diplomatic-cable catalogue — where
most records are catalogued but never transcribed, plaintext service traffic
(repeat requests, receipts, chatter) matters as much as ciphertext, and a
recovered plaintext needs to point back at the message it solves. It was
designed jointly with a downstream cataloguing project; CryptML validates
*structure*, and that project's own semantic validator (codebook membership,
cross-channel consistency) builds on top of it.

Three kinds of record are involved, but only the first needs a flag:

- **A message** — an ordinary [ciphertext node](#ciphertext-node), optionally
  a **stub** (`is_stub: true`, no `raw`/`parts` — see below).
- **A service record** — plaintext service traffic with no ciphertext and no
  required channel of its own (e.g. `"YOUR PN41 NEVER RECEIVED"`, sent in
  clear). Lives in the document-level `service_records` array, never inside
  `ciphertexts`. See [`service` record](#service-record).
- **A plaintext record** — a recovered plaintext corresponding to a known
  message, the single highest-value record in a codebook survey (it yields
  the key by subtraction). Lives in `plaintext_records`. See
  [`plaintext` record](#plaintext-record).

### Stub entries (`is_stub`)

A ciphertext entry with `is_stub: true` must have **neither** `raw` nor
`parts` — the reverse of the normal rule. It's a validation error for
`is_stub: true` to coexist with either. Every other ciphertext-level field
(archival, `origin`, `solution`, `hints`, `sources`, …) behaves exactly as on
a non-stub entry — including shape-checking: a stub's `origin` (or
`solution`/`hints`, however unusual those are on a stub) is validated field
by field exactly as it would be on a transcribed message, even though there's
no `raw` for the rest of that branch's checks to run against. Most of a
large survey will typically be stubs: cataloguing a message's indicator,
preamble, and provenance doesn't require transcribing it.

### Group-structure classification (`unit_type`, `codebook_id`, `unit_length`)

Different channels require different arithmetic — a codebook channel is
differenced on code *numbers*, a cipher channel on *letters* — so the
classification doubles as a safety interlock, not just a label.

- **`unit_type`** — `"codebook"` | `"cipher"` | `"unknown"`. Cascades exactly
  like `cipher_system`/`charset` (document `defaults` → ciphertext, one
  level).
- **`codebook_id`** — a free-string codebook identifier. **Required**
  whenever the effective `unit_type` is `"codebook"`.
- **`unit_length`** — positive integer group/code-word width.
- **`unit_type_asserted`** — a *separate*, **non-cascading**, ciphertext-only
  override. It exists for a stub (which has no groups to classify
  mechanically) or any message where a hand classification needs to win
  outright, and takes **highest precedence** over the cascaded `unit_type`
  for rule-selection purposes on that one message. Keeping it a distinct key
  from `unit_type` means a hand guess can never masquerade as a
  machine-computed classification downstream.

Resolution order for which structural rule applies to a given message:
`ciphertext.unit_type_asserted` → `ciphertext.unit_type` → `defaults.unit_type`
→ if none of those is set, the group-structure rules below are skipped
entirely (only the ordinary charset check still applies).

**Group-structure rules**, once an effective `unit_type` is known and the
message has a `raw` (a stub has no groups to check):

- **`"codebook"`**: the character count must be a multiple of `unit_length`
  — **a validation error** if not (a transcription error or garble). Skipped
  if `unit_length` is unknown or if `remove_from_start`/`remove_from_end`
  can't be applied (see below).
- **`"cipher"`**: a short final group is legitimate and is never padded,
  trimmed, or treated as an error — but it's flagged, with its length, as a
  **warning** (see [`validateWarnings()`](#validatewarnings-non-blocking-findings)
  below), since how a final group is handled is itself analytically
  significant.

**Order of operations for the character count**: `remove_from_start`/
`remove_from_end` are applied first, then the gap marker is stripped, then
`ignorechars` characters are excluded — the same order a tool would apply to
recover the message's actual content, and the only order that gives a
meaningful count. This matters immediately for real data:
`tools/CryptML/input/RCA-Outgoing.cryptml` embeds each message's indicator
inside `raw` itself (`"A50/18 GYHTE DISEU …"`) and strips it with
`remove_from_start: 6` — 96 non-ignored characters before the trim, 90 after.
Counting before the trim would make a `unit_length: 5` codebook check fail on
every message in that file; counting after it passes. If the trim amount
itself can't be applied (it exceeds the available non-ignored characters at
that end of `raw`), the codebook/cipher checks are silently skipped for that
message rather than counting against the wrong substring — the same
fail-safe-by-omission the rest of this extension uses when a cascaded field
is simply absent.

### Cross-references

A reference is one of:

- a bare `id` — resolved against the *same* document, or
- `"<cryptml_uuid> :: <id>"` — a qualified reference into *another*
  document, using the document's own `cryptml_uuid`. Resolution is
  syntax-only in that case: a single-document `validate()` call has no way
  to open the other file, so a qualified reference whose `uuid` isn't this
  document's own is accepted without resolving it.

This is used by `resend_of` and `related` (ciphertext-level) and
`message_ref` (plaintext record). A reference that fails to parse (empty, or
nothing after `" :: "`) is a syntax error; a bare/same-document reference
that doesn't match any `id` in the document is a resolution error.
`refers_channel`/`refers_serial` on a service record are the one exception:
they're **descriptive only, never required to resolve** — service traffic
routinely refers to a message that was never catalogued, and a downstream
extractor can report that as a "missing serial" statistic rather than a
CryptML validation error.

### Recording where a ciphertext came from

Three things look alike but answer different questions:

| Where | Question it answers |
|---|---|
| A document-level **source** (with an `id`) | Which published or archived item is this from? One entry per item — for example one per archive file — carrying its title, URL and `identifier`. |
| `source_id` and `archive_page` on the ciphertext | Which of those sources, and where in it? The per-message pointer. |
| **`origin`** | How did the message itself come to exist: when it was sent, by whom, to whom, and how this copy was made. |

Working rule: record each archive file once as a source with an `id`; give
every message a `source_id` and an `archive_page`; leave `origin.location`
blank for archival material (it suits puzzles, such as a magazine issue). A
document-level source *without* an `id` still applies to every ciphertext,
so it is the place for a citation that covers the whole file.

**Service records live in the channel file they name.** A service record is
filed under the channel in `refers_channel`, in that file's own
`service_records` array. There is no separate service file: a file with no
ciphertexts is not valid. A cable naming several channels, or none, goes in
whichever file the cataloguer chooses, and a tool that wants all service
traffic together reads the `service_records` of every channel file and keys
each record by file and `id`. `validateWarnings()` flags a service record
whose `refers_channel` differs from the file's `channel`.

### Provenance, indicator, and quality fields

All optional, all on the ciphertext node, never required by CryptML's
generic validator — a downstream project's own semantic validator is where
"required for a message record" policy belongs, since `ciphertexts[]` is
shared with the entire rest of the (non-archival) corpus.

| Field | Type | Meaning |
|---|---|---|
| `source_id` | string | The `id` of the one document-level [source](#source-item-of-a-sources-list) this message comes from, e.g. `"ISA-107"`. Must match a source in this document. Exactly one: a rare second copy goes in a note. |
| `archive_page` | string | Page or range within that source, e.g. `"107-112"`. |
| `indicator_raw` | string | The indicator **verbatim, unnormalised**, e.g. `"A42/53"`, `"NA9"`. Recorded as written — if a channel turns out to use its indicator differently than currently assumed, only the raw form reveals that. |
| `preamble_raw` | string | The whole header line(s), **verbatim**, exactly as transcribed — e.g. `"ISR6 NEWYORK JAN 27\nCDE PALOFFICE GENEVA"`. `origin.originator`/`origin.addressee`/`origin.date`/`origin.time` are the analyst's *parsed-out* reading of this same line; `preamble_raw` is what's actually on the page, so a parsing mistake or an unusual indicator convention stays recoverable from the raw text rather than silently lost. |
| `service_line_raw` | string | Trailing service text, **verbatim** — acknowledgements, routing, relay annotations appended after the message body (e.g. `"ACKPLS ISR\nRECD ISR2 HE 1633 TU"`). Distinct from `anomaly_notes` (which records something *wrong* with the transcription) and from a `service_records` entry (which is a separate, standalone plaintext message in its own right, not an annotation trailing this one). |
| `channel` | string, **cascades** | Parsed channel prefix, e.g. `"A"`, `"NP"` — the one archival field that cascades from `document.defaults`, since a survey typically holds one file per channel (see [Cascade rules](#cascade-rules)). Cross-checked against `indicator_raw` — see below. |
| `serial` | non-negative integer | Parsed running number. Cross-checked against `indicator_raw`. |
| `gr_stated` | non-negative integer | Group count as given *in the indicator itself*, if any. Its absence is a significant fact about the channel, distinct from "not yet recorded" — don't default it to anything. On a `transcription_state: "full"` message, a mismatch against the counted group total is a [warning](#validatewarnings-non-blocking-findings), not an error: it may be a garble, a miscount, or evidence the indicator's second number isn't a group count at all. The check is skipped on `"none"`/`"head_tail"`, where the counted total is legitimately partial and would mismatch by design, not by error. |
| `pages` | non-negative integer | Transmission page count. |
| `transcription_state` | `"none"` \| `"head_tail"` \| `"full"` | How much of the message has actually been transcribed into `raw`. |
| `legibility` | `"clean"` \| `"partial"` \| `"poor"` | Legibility of the source. `"poor"` combined with `transcription_state: "full"` is a [warning](#validatewarnings-non-blocking-findings) — a statistic built on an unreliable transcription is worse than no statistic. |
| `resend_of` | [reference](#cross-references) | The message this one retransmits. |
| `related` | array of [reference](#cross-references) | Other records bearing on this one. |
| `anomaly_notes` | string | Anything anomalous, verbatim — overstrikes, struck-through groups, garbles, corrections, marginalia. (Distinct from the existing, list-shaped `notes` field.) |

**Indicator consistency check**: a best-effort pattern,
`^([A-Za-z]+)(\d+)(?:/(\d+))?$`, parses `indicator_raw`'s common shorthand
(e.g. `"A42/53"` → channel `"A"`, serial `42`, `gr_stated` `53`). When
`indicator_raw` matches, the *effective* `channel` (the message's own if set,
otherwise the cascaded `defaults.channel`) is cross-checked against it, along
with `serial`/`gr_stated`. When it doesn't match — `indicator_raw` is free
text by design — the cross-check is silently skipped, not an error.

### `extensions`

A reserved, per-record free-form object (on a ciphertext, a service record,
or a plaintext record) whose contents are entirely unvalidated — the
escape hatch for anything project-specific that hasn't earned a place in the
fixed vocabulary yet. This is deliberately a dedicated key, not a prefix
convention on ordinary field names: that separation is what lets the
validator keep distinguishing a genuine *unrecognized field* (almost always
a typo, and still a hard error) from a deliberate *extension field*. An
extension key must never become load-bearing for any CryptML-aware tool; if
one proves generally useful, promote it into the fixed vocabulary instead of
leaning on it indefinitely.

### `service` record

Lives in the document-level `service_records` array. Unlike a ciphertext
entry, these required fields *are* strictly enforced by CryptML's generic
validator, since this is a dedicated, single-purpose array rather than one
shared with the rest of the corpus.

| Field | Required | Type | Meaning |
|---|---|---|---|
| `id` | **yes** | string | Stable key, referenceable from `related`/`resend_of`. Unique across `ciphertexts`, `service_records`, and `plaintext_records` together. |
| `source_id` | **yes** | string | As on a ciphertext: must match the `id` of a document-level source. |
| `archive_page` | **yes** | string | As on a ciphertext. |
| `origin` | **yes** | object | Same shape as ciphertext [`origin`](#origin). `date` and `originator` are required within it for a service record specifically; `addressee` is not — a margin annotation or file note captured this way may have none, and forcing one would just invite a fabricated value. |
| `service_type` | **yes** | `"repeat_request"` \| `"receipt"` \| `"plain_message"` \| `"chatter"` \| `"other"` | |
| `refers_channel` | no | string | Channel named in the text, if any. Descriptive only — see [Cross-references](#cross-references). |
| `refers_serial` | no | non-negative integer | Serial named in the text, if any. Descriptive only. |
| `text_verbatim` | **yes** | string | The full text, exactly as written. |
| `extensions` | no | object | See [`extensions`](#extensions) above. |

### `plaintext` record

Lives in the document-level `plaintext_records` array.

| Field | Required | Type | Meaning |
|---|---|---|---|
| `id` | **yes** | string | Stable key. Unique across `ciphertexts`, `service_records`, and `plaintext_records` together. |
| `source_id` | **yes** | string | As on a ciphertext: must match the `id` of a document-level source. |
| `archive_page` | **yes** | string | As on a ciphertext. |
| `origin` | no | object | Same shape as ciphertext [`origin`](#origin), no required sub-fields. |
| `message_ref` | **yes** | [reference](#cross-references) | The message this plaintext corresponds to. Must resolve. |
| `plaintext_verbatim` | **yes** | string | The recovered plaintext, exactly as recovered. |
| `extensions` | no | object | See [`extensions`](#extensions) above. |

### `validateWarnings()`: non-blocking findings

A second, separate function alongside `validate()`, returning advisory
findings that never affect pass/fail — deliberately kept apart so every
existing caller of `validate()` (Editor, Validator, List, Search,
`generate-manifest.js`, the pre-commit hook, the GitHub Action, the Python
`load()`) keeps its existing all-or-nothing contract unchanged. It currently
reports five things, each described where it's introduced above: a ciphertext
with no `source_id` although the document defines identified sources, a
service record whose `refers_channel` differs from the file's `channel`, a
`gr_stated` mismatch against the counted group total (only on a `"full"`
transcription — see above), `legibility: "poor"` combined with
`transcription_state: "full"`, and a short final group on a
`"cipher"`-classified message. A disagreement surfaced this way is treated
as a finding worth seeing, not a problem worth suppressing.

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
- **A ciphertext has exactly one of `raw` or `parts`, unless `is_stub: true`.**
  Neither, or both, is a validation error — except a stub, which requires
  *neither*. See [Archival message metadata](#archival-message-metadata).
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
- **`unit_type`/`unit_type_asserted`/`transcription_state`/`legibility`,
  and a `service` record's `service_type`,** must each be one of their
  enumerated values. **`codebook_id`** is required whenever the effective
  `unit_type` is `"codebook"`. **`unit_length`** must be a positive integer;
  `serial`/`gr_stated`/`pages`/`refers_serial` must each be a non-negative
  integer. See [Archival message metadata](#archival-message-metadata).
- **A codebook-classified message's character count must be a multiple of
  `unit_length`** — an error, not a warning (see
  [Archival message metadata](#archival-message-metadata)); a
  short final group on a cipher-classified message is a warning instead, via
  [`validateWarnings()`](#validatewarnings-non-blocking-findings).
- **`resend_of`, `related`, and a plaintext record's `message_ref` must
  resolve** (same-document references only) — see
  [Cross-references](#cross-references). A service record's
  `refers_channel`/`refers_serial` are the one exception: descriptive only,
  never required to resolve.
- **Source ids are unique, and `source_id` must resolve.** A `source_id` on a
  ciphertext, service record or plaintext record must be a non-empty string
  matching the `id` of a document-level source (service and plaintext records
  require one). An `id` on a ciphertext's own source is an error. See
  [Recording where a ciphertext came from](#recording-where-a-ciphertext-came-from).
- **`extensions`, wherever legal, must be an object** — its contents are
  otherwise entirely unvalidated. See [`extensions`](#extensions).
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
| `time` | string | Time of day the message/cryptogram was created or transmitted, alongside `date`. Free text, like `date` — no enforced format (e.g. "0800Z", "14:32" are both fine). |
| `originator` | string | Who composed or sent it — the puzzle's setter, or a real message's sender. Not the author of a book it later appeared in; see `source.author` for that. |
| `addressee` | string | Who it was sent to. Sibling of `originator` — together they're the correspondent pair, significant for traffic-analysis partitioning. |
| `method` | string | How this copy was produced or obtained, e.g. "transcribed from photo", "typed from book". This is transcription provenance, not the cryptosystem — see `cipher_system`, a separate field. |
| `location` | string | Free text, e.g. where it was found or created. |
| `remarks` | string | Anything else about the origin. |

### `source` (item of a `sources` list)

| Field | Type | Meaning |
|---|---|---|
| `id` | string | Optional, and only legal on a *document-level* source (an `id` on a ciphertext's own source is an error — nothing could reference it). Unique among the document's sources. A source with an `id` applies only to ciphertexts and records that name it in `source_id`; a source without one applies to every ciphertext, as always. |
| `type` | one of `book`, `web`, `letter`, `periodical`, `person`, `competition`, `other` | |
| `title` | string | Title of the book/page/periodical/etc. |
| `identifier` | string | Whatever identifies the item within its own collection: a shelfmark, accession number, physical ID, ISBN, DOI or call number. |
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

## Example: archival message metadata

A single-file illustration of every new 1.2 shape: a stub, a transcribed
codebook message with a short-final-group sibling (classified `"cipher"` on
purpose, to show the warning rather than the codebook error), an `extensions`
key, a service record, and a plaintext record linked back to the codebook
message. `channel` is declared once in `defaults`, since this file holds one
channel's traffic, rather than repeated on every message.

```json
{
  "cryptml_version": "1.2",
  "cryptml_uuid": "6f1b1a1a-6c2e-4a7a-9b1e-2f6b7c8d9e0a",
  "title": "Channel A, 1949",
  "defaults": {
    "unit_type": "codebook",
    "codebook_id": "bentley-second-phrase-1945",
    "unit_length": 5,
    "channel": "A"
  },
  "sources": [
    { "id": "ISA-123", "type": "web", "title": "RCA, Outgoing, January 1949", "identifier": "FILE-79/13",
      "url": "https://example.org/archive/123" },
    { "id": "ISA-200", "type": "web", "title": "RCA, Incoming, February 1949", "identifier": "FILE-79/14" }
  ],
  "ciphertexts": [
    {
      "id": "A42/53",
      "is_stub": true,
      "source_id": "ISA-123",
      "archive_page": "45-46",
      "indicator_raw": "A42/53",
      "serial": 42,
      "gr_stated": 53,
      "transcription_state": "none",
      "legibility": "clean",
      "origin": { "date": "1949-01-27", "originator": "ISR6 NEWYORK", "addressee": "CDE EYTAN" }
    },
    {
      "id": "A55",
      "source_id": "ISA-123",
      "archive_page": "47",
      "indicator_raw": "A55",
      "serial": 55,
      "transcription_state": "full",
      "legibility": "partial",
      "unit_type_asserted": "cipher",
      "anomaly_notes": "final group short by one letter -- not a transcription error, see raw",
      "preamble_raw": "ISR6 NEWYORK JAN 28\nCDE EYTAN MEMISRAEL LAUSANNE",
      "service_line_raw": "ACKPLS ISR\nRECD ISR6 HE 1420 TU",
      "raw": "VQFTX LMPRS DJKWN HBYO",
      "origin": { "date": "1949-01-28", "originator": "ISR6 NEWYORK", "addressee": "CDE EYTAN" },
      "extensions": { "confidence_score": 0.6, "surveyor": "mr" }
    }
  ],
  "service_records": [
    {
      "id": "SVC-1949-02-03-a",
      "source_id": "ISA-123",
      "archive_page": "48",
      "origin": { "date": "1949-02-03", "originator": "ISR6 NEWYORK", "addressee": "CDE EYTAN" },
      "service_type": "repeat_request",
      "refers_channel": "A",
      "refers_serial": 54,
      "text_verbatim": "YOUR A54 NEVER RECEIVED PLEASE REPEAT"
    }
  ],
  "plaintext_records": [
    {
      "id": "PT-A42-53",
      "source_id": "ISA-200",
      "archive_page": "12",
      "message_ref": "A42/53",
      "plaintext_verbatim": "Meeting confirmed for Tuesday at the usual place."
    }
  ]
}
```

`A42/53` is a stub inheriting `unit_type: "codebook"` and `channel: "A"` from
`defaults` — fine, since a stub has no `raw` for the group-structure check to
run against, and `channel` still cross-checks cleanly against its own
`indicator_raw`. `A55` inherits the same cascaded `channel: "A"`.
`A55` has a 19-character `raw` and asserts `"cipher"` to opt out of the
codebook channel's arithmetic for this one message (a codebook message with
19 characters would otherwise be a hard error); `validate()` passes it
cleanly, and `validateWarnings()` reports the short final group (remainder 4
against `unit_length: 5`) rather than erroring. `A55`'s `preamble_raw` and
`service_line_raw` carry the header and trailer lines exactly as transcribed;
`origin.originator`/`origin.addressee`/`origin.date` are the parsed-out
reading of that same `preamble_raw` line, kept alongside it rather than
replacing it. The service record refers to `A54`, a serial that was never
catalogued in this file — that's fine, since `refers_channel`/`refers_serial`
never need to resolve. The plaintext record resolves `message_ref` against
`A42/53` in the same document. Each message and record names its source with
`source_id` and gives its page in `archive_page`; the two sources carry the
file's title, URL and `identifier` once. The service record cites channel `A`
and sits in this channel-`A` file, so it raises no filing warning.

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
```json
// ERROR: source_id names no source in this document's sources list.
{ "sources": [ { "id": "ISA-123", "type": "web" } ], "ciphertexts": [ { "id": "A1", "raw": "...", "source_id": "ISA-999" } ] }
```
```json
// ERROR: is_stub: true requires neither "raw" nor "parts" -- a stub must have neither.
{ "id": "A1", "is_stub": true, "raw": "ABCDE" }
```
```json
// ERROR: unit_type is "codebook" but codebook_id is missing.
{ "id": "A1", "raw": "ABCDEFGHIJ", "unit_type": "codebook", "unit_length": 5 }
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
