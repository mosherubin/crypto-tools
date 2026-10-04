/*
 * CryptML data model + form rendering helpers.
 * Format: docs/cryptml-spec.md
 */
const CryptMLEditor = (() => {

  const DEFAULT_SETTINGS = {
    cipher_system: 'unknown',
    charset: '[A-Z]',
    casesensitive: false,
    ditschar: '-',
    ignorechars: '[\\s]',
    plaintext_charset: '[A-Z]',
  };

  const INHERITED_FIELDS = ['cipher_system', 'charset', 'casesensitive', 'ditschar', 'ignorechars', 'unit_type', 'codebook_id', 'unit_length', 'channel'];

  // ---------- data model ----------

  function resolveSettings(documentDefaults) {
    return { ...DEFAULT_SETTINGS, ...(documentDefaults || {}) };
  }

  function blankOrigin() {
    return { date: '', time: '', originator: '', addressee: '', method: '', location: '', remarks: '' };
  }

  function blankSolver() {
    return { solved_by: '', solved_date: '', method: '', notes: '' };
  }

  function blankSolution(defaults) {
    return { plaintext: '', plaintext_charset: defaults.plaintext_charset, key: '', solvers: [] };
  }

  function blankPart(partId) {
    return {
      part_id: partId,
      raw: '',
      remove_from_start: 0,
      remove_from_end: 0,
      origin: blankOrigin(),
      solution: null,
      hints: [],
    };
  }

  function newCiphertext(id, defaults) {
    return {
      id,
      raw: '',
      parts: null, // array of parts when this ciphertext is split; null means single raw
      cipher_system: defaults.cipher_system,
      charset: defaults.charset,
      casesensitive: defaults.casesensitive,
      ditschar: defaults.ditschar,
      ignorechars: defaults.ignorechars,
      remove_from_start: 0,
      remove_from_end: 0,
      origin: blankOrigin(),
      sources: [],
      solution: null,
      hints: [],
      references: [],
      notes: [],
      chatter: [],
    };
  }

  function newDocument() {
    const defaults = resolveSettings({});
    return {
      cryptml_version: '1.2',
      cryptml_uuid: null, // never auto-assigned -- see "Prepare for the corpus" in the editor
      title: '',
      defaults,
      sources: [],
      references: [],
      notes: [],
      chatter: [],
      ciphertexts: [newCiphertext('1', defaults)],
      service_records: [],
      plaintext_records: [],
    };
  }

  // "A9" before "A10": digit runs compare as numbers, everything else as text.
  function naturalCompare(a, b) {
    const ax = String(a).match(/\d+|\D+/g) || [];
    const bx = String(b).match(/\d+|\D+/g) || [];
    for (let i = 0; i < Math.max(ax.length, bx.length); i++) {
      const ac = ax[i], bc = bx[i];
      if (ac === undefined) return -1;
      if (bc === undefined) return 1;
      if (/^\d+$/.test(ac) && /^\d+$/.test(bc)) {
        const diff = Number(ac) - Number(bc);
        if (diff !== 0) return diff;
      } else {
        const cmp = ac.localeCompare(bc);
        if (cmp !== 0) return cmp;
      }
    }
    return 0;
  }

  function sortCiphertextsById(doc) {
    doc.ciphertexts.sort((a, b) => naturalCompare(a.id, b.id));
  }

  function nextCiphertextId(doc) {
    const used = new Set(doc.ciphertexts.map(ct => ct.id));
    let n = 1;
    while (used.has(String(n))) n++;
    return String(n);
  }

  function nextPartId(parts) {
    const used = new Set(parts.map(p => p.part_id));
    for (let i = 0; i < 26; i++) {
      const letter = String.fromCharCode('a'.charCodeAt(0) + i);
      if (!used.has(letter)) return letter;
    }
    let n = 1;
    while (used.has(String(n))) n++;
    return String(n);
  }

  function parseOrigin(raw) {
    return { ...blankOrigin(), ...(raw || {}) };
  }

  function parseSolution(raw, defaults) {
    if (!raw) return null;
    return {
      ...blankSolution(defaults),
      ...raw,
      solvers: (raw.solvers || []).map(sv => ({ ...blankSolver(), ...sv })),
    };
  }

  function parsePart(raw, defaults) {
    return {
      part_id: raw.part_id,
      raw: raw.raw,
      remove_from_start: raw.remove_from_start ?? 0,
      remove_from_end: raw.remove_from_end ?? 0,
      origin: parseOrigin(raw.origin),
      solution: parseSolution(raw.solution, defaults),
      hints: raw.hints || [],
    };
  }

  // Archival message fields (CryptML 1.2) that the Editor doesn't yet have form controls for --
  // carried through verbatim on load/save so opening one of these files here can never silently
  // discard its metadata, even before there's dedicated UI for editing it.
  // 'channel' cascades the same way 'unit_type' does (see the "common" object in parseDocument)
  // and so is deliberately excluded here, same as 'unit_type'/'codebook_id'/'unit_length'.
  const ARCHIVAL_PASSTHROUGH_FIELDS = [
    'is_stub', 'source_id', 'archive_page', 'indicator_raw', 'serial', 'gr_stated',
    'pages', 'transcription_state', 'legibility', 'resend_of', 'related', 'anomaly_notes',
    'preamble_raw', 'service_line_raw',
    'unit_type_asserted', 'extensions',
  ];

  function copyArchivalFields(ct) {
    const out = {};
    for (const key of ARCHIVAL_PASSTHROUGH_FIELDS) {
      if (key in ct) out[key] = ct[key];
    }
    return out;
  }

  function parseDocument(data) {
    const defaults = resolveSettings(data.defaults);
    const rawCiphertexts = data.ciphertexts || [];
    if (!rawCiphertexts.length) throw new Error('File contains no ciphertexts');

    const ciphertexts = rawCiphertexts.map((ct, index) => {
      let id;
      if ('id' in ct) id = ct.id;
      else if (rawCiphertexts.length === 1) id = '1';
      else throw new Error(`Ciphertext at index ${index} has no 'id', and the file has more than one ciphertext`);

      const common = {
        id,
        cipher_system: ct.cipher_system ?? defaults.cipher_system,
        charset: ct.charset ?? defaults.charset,
        casesensitive: ct.casesensitive ?? defaults.casesensitive,
        ditschar: ct.ditschar ?? defaults.ditschar,
        ignorechars: ct.ignorechars ?? defaults.ignorechars,
        unit_type: ct.unit_type ?? defaults.unit_type,
        codebook_id: ct.codebook_id ?? defaults.codebook_id,
        unit_length: ct.unit_length ?? defaults.unit_length,
        channel: ct.channel ?? defaults.channel,
        sources: ct.sources || [],
        references: ct.references || [],
        notes: ct.notes || [],
        chatter: ct.chatter || [],
        ...copyArchivalFields(ct),
      };

      if (ct.parts) {
        return {
          ...common,
          raw: '',
          parts: ct.parts.map(p => parsePart(p, defaults)),
          remove_from_start: 0,
          remove_from_end: 0,
          origin: blankOrigin(),
          solution: null,
          hints: [],
        };
      }

      if (ct.is_stub === true) {
        return {
          ...common,
          raw: '',
          parts: null,
          remove_from_start: 0,
          remove_from_end: 0,
          origin: parseOrigin(ct.origin),
          solution: null,
          hints: [],
        };
      }

      if (!('raw' in ct)) throw new Error(`Ciphertext '${id}' has neither 'raw' nor 'parts' (and is_stub is not set)`);

      return {
        ...common,
        raw: ct.raw,
        parts: null,
        remove_from_start: ct.remove_from_start ?? 0,
        remove_from_end: ct.remove_from_end ?? 0,
        origin: parseOrigin(ct.origin),
        solution: parseSolution(ct.solution, defaults),
        hints: ct.hints || [],
      };
    });

    return {
      cryptml_version: data.cryptml_version || '1.1',
      cryptml_uuid: data.cryptml_uuid ?? null,
      title: data.title || '',
      defaults,
      sources: data.sources || [],
      references: data.references || [],
      notes: data.notes || [],
      chatter: data.chatter || [],
      ciphertexts,
      service_records: data.service_records || [],
      plaintext_records: data.plaintext_records || [],
    };
  }

  function trimObject(obj) {
    const entries = Object.entries(obj || {}).filter(([, v]) => v);
    return entries.length ? Object.fromEntries(entries) : null;
  }

  function serializeSolution(solution, defaults) {
    if (!solution) return null;
    const out = trimObject({ plaintext: solution.plaintext, key: solution.key }) || {};
    if (solution.plaintext_charset && solution.plaintext_charset !== defaults.plaintext_charset) {
      out.plaintext_charset = solution.plaintext_charset;
    }
    const solvers = (solution.solvers || []).map(sv => trimObject(sv)).filter(Boolean);
    if (solvers.length) out.solvers = solvers;
    return Object.keys(out).length ? out : null;
  }

  function serializePart(part, defaults) {
    const out = { part_id: part.part_id, raw: part.raw };
    if (part.remove_from_start) out.remove_from_start = part.remove_from_start;
    if (part.remove_from_end) out.remove_from_end = part.remove_from_end;
    const origin = trimObject(part.origin);
    if (origin) out.origin = origin;
    const solution = serializeSolution(part.solution, defaults);
    if (solution) out.solution = solution;
    const hints = (part.hints || []).map(h => trimObject(h)).filter(Boolean);
    if (hints.length) out.hints = hints;
    return out;
  }

  function serializeCiphertext(ct, defaults) {
    const out = { id: ct.id };
    for (const name of INHERITED_FIELDS) {
      if (ct[name] !== undefined && ct[name] !== defaults[name]) out[name] = ct[name];
    }

    if (ct.parts) {
      out.parts = ct.parts.map(p => serializePart(p, defaults));
    } else {
      if (!ct.is_stub) out.raw = ct.raw; // a stub has no raw to write -- that's the whole point of it
      if (ct.remove_from_start) out.remove_from_start = ct.remove_from_start;
      if (ct.remove_from_end) out.remove_from_end = ct.remove_from_end;
      const origin = trimObject(ct.origin);
      if (origin) out.origin = origin;
      const solution = serializeSolution(ct.solution, defaults);
      if (solution) out.solution = solution;
      const hints = ct.hints.map(h => trimObject(h)).filter(Boolean);
      if (hints.length) out.hints = hints;
    }

    for (const key of ARCHIVAL_PASSTHROUGH_FIELDS) {
      const val = ct[key];
      if (val === undefined) continue;
      if (key === 'related' && Array.isArray(val) && !val.length) continue;
      if (key === 'extensions' && isPlainObject(val) && !Object.keys(val).length) continue;
      out[key] = val;
    }

    const sources = ct.sources.map(s => trimObject(s)).filter(Boolean);
    if (sources.length) out.sources = sources;
    const references = ct.references.map(r => trimObject(r)).filter(Boolean);
    if (references.length) out.references = references;
    const notes = ct.notes.map(n => trimObject(n)).filter(Boolean);
    if (notes.length) out.notes = notes;
    const chatter = ct.chatter.map(c => trimObject(c)).filter(Boolean);
    if (chatter.length) out.chatter = chatter;
    return out;
  }

  function serializeDocument(doc) {
    const out = {
      cryptml_version: doc.cryptml_version,
      ciphertexts: doc.ciphertexts.map(ct => serializeCiphertext(ct, doc.defaults)),
    };
    if (doc.cryptml_uuid) out.cryptml_uuid = doc.cryptml_uuid;
    if (doc.title) out.title = doc.title;
    if (JSON.stringify(doc.defaults) !== JSON.stringify(DEFAULT_SETTINGS)) out.defaults = doc.defaults;
    const sources = doc.sources.map(s => trimObject(s)).filter(Boolean);
    if (sources.length) out.sources = sources;
    const references = doc.references.map(r => trimObject(r)).filter(Boolean);
    if (references.length) out.references = references;
    const notes = doc.notes.map(n => trimObject(n)).filter(Boolean);
    if (notes.length) out.notes = notes;
    const chatter = doc.chatter.map(c => trimObject(c)).filter(Boolean);
    if (chatter.length) out.chatter = chatter;
    if (doc.service_records && doc.service_records.length) out.service_records = doc.service_records.map(serializeRecord);
    if (doc.plaintext_records && doc.plaintext_records.length) out.plaintext_records = doc.plaintext_records.map(serializeRecord);
    return out;
  }

  // Service/plaintext records: drop fields left blank in the form (and an origin or extensions
  // object left with nothing in it), so the saved file only shows what was actually recorded.
  function serializeRecord(rec) {
    const out = {};
    for (const [key, value] of Object.entries(rec)) {
      if (key === 'origin') {
        const origin = trimObject(value);
        if (origin) out.origin = origin;
      } else if (key === 'extensions') {
        if (isPlainObject(value) && Object.keys(value).length) out.extensions = value;
      } else if (value !== undefined && value !== '') {
        out[key] = value;
      }
    }
    return out;
  }

  // ---------- validation ----------
  // Pure data/logic, no DOM dependency -- ported from tools/Library/cryptml.py's
  // validate(), field for field, so the two stay equivalent. Runs equally in the
  // browser and under Node (see the CommonJS export at the bottom of this file).

  const DOCUMENT_FIELDS = new Set([
    'cryptml_version', 'cryptml_uuid', 'title', 'defaults', 'sources', 'references', 'notes', 'chatter',
    'ciphertexts', 'service_records', 'plaintext_records',
  ]);
  const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
  const DEFAULTS_FIELDS = new Set([
    'cipher_system', 'charset', 'casesensitive', 'ditschar', 'ignorechars', 'plaintext_charset',
    'unit_type', 'codebook_id', 'unit_length', 'channel',
  ]);
  const CIPHERTEXT_FIELDS = new Set([
    'id', 'raw', 'parts', 'cipher_system', 'charset', 'casesensitive', 'ditschar', 'ignorechars',
    'remove_from_start', 'remove_from_end', 'origin', 'sources', 'references', 'notes', 'chatter',
    'solution', 'hints',
    // Archival message metadata (CryptML 1.2) -- see "Archival message metadata" in the spec.
    'is_stub', 'source_id', 'archive_page', 'indicator_raw', 'channel', 'serial', 'gr_stated',
    'pages', 'transcription_state', 'legibility', 'resend_of', 'related', 'anomaly_notes',
    'preamble_raw', 'service_line_raw',
    'unit_type', 'unit_type_asserted', 'codebook_id', 'unit_length', 'extensions',
  ]);
  const PART_FIELDS = new Set(['part_id', 'raw', 'remove_from_start', 'remove_from_end', 'origin', 'solution', 'hints']);
  const PART_ONLY_WHEN_SPLIT = ['remove_from_start', 'remove_from_end', 'origin', 'solution', 'hints'];
  const ORIGIN_FIELD_SET = new Set(['date', 'time', 'originator', 'addressee', 'method', 'location', 'remarks']);
  const SOURCE_FIELD_SET = new Set(['id', 'type', 'title', 'identifier', 'author', 'publisher', 'date', 'page', 'url', 'note']);
  const SOURCE_TYPES = new Set(['book', 'web', 'letter', 'periodical', 'person', 'competition', 'other']);
  const SOLUTION_FIELD_SET = new Set(['plaintext', 'plaintext_charset', 'key', 'solvers']);
  const SOLVER_FIELD_SET = new Set(['solved_by', 'solved_date', 'method', 'notes']);
  const HINT_FIELD_SET = new Set(['text', 'position', 'source', 'confidence', 'notes']);
  const NOTE_FIELD_SET = new Set(['title', 'text']);
  const CHATTER_FIELD_SET = new Set(['author', 'date', 'text']);
  const GAP_MARKER = '[...]';

  // ---------- archival message metadata (CryptML 1.2) ----------

  const UNIT_TYPE_VALUES = new Set(['codebook', 'cipher', 'unknown']);
  const TRANSCRIPTION_STATE_VALUES = new Set(['none', 'head_tail', 'full']);
  const LEGIBILITY_VALUES = new Set(['clean', 'partial', 'poor']);
  const SERVICE_TYPE_VALUES = new Set(['repeat_request', 'repeat', 'receipt', 'plain_message', 'chatter', 'other']);
  const SERVICE_RECORD_FIELDS = new Set([
    'id', 'source_id', 'archive_page', 'origin', 'service_type', 'refers_channel', 'refers_serial',
    'text_verbatim', 'extensions',
  ]);
  const PLAINTEXT_RECORD_FIELDS = new Set([
    'id', 'source_id', 'archive_page', 'origin', 'message_ref', 'plaintext_verbatim', 'extensions',
  ]);
  // Indicator shorthand, e.g. "A42/53" -> channel "A", serial 42, gr_stated 53; "NP33" -> channel
  // "NP", serial 33, no gr_stated. Best-effort only -- indicator_raw is free text by design, so a
  // channel whose indicators don't fit this shape just skips the cross-check rather than erroring.
  const INDICATOR_RE = /^([A-Za-z]+)(\d+)(?:\/(\d+))?$/;
  // A reference is a bare id (same document) or "<cryptml_uuid> :: <id>" (another document),
  // reusing the exact " :: " convention the Export feature already uses for file :: id comments.
  function parseReference(ref) {
    if (typeof ref !== 'string' || !ref) return null;
    const sep = ref.indexOf(' :: ');
    if (sep !== -1 && isValidUuid(ref.slice(0, sep))) {
      return { uuid: ref.slice(0, sep), id: ref.slice(sep + 4) };
    }
    return { uuid: null, id: ref };
  }

  function isPlainObject(v) {
    return typeof v === 'object' && v !== null && !Array.isArray(v);
  }

  function isValidUuid(v) {
    return typeof v === 'string' && UUID_RE.test(v);
  }

  function isSingleBracketedClass(pattern) {
    if (typeof pattern !== 'string' || !pattern.startsWith('[') || !pattern.endsWith(']')) return false;
    try { new RegExp(pattern); } catch { return false; }
    const inner = pattern.slice(1, -1);
    for (let i = 0; i < inner.length; i++) {
      if (inner[i] === '\\') { i++; continue; }
      if (inner[i] === ']') return false;
    }
    return true;
  }

  function checkFields(obj, allowed, where, errors) {
    if (!isPlainObject(obj)) { errors.push(`${where}: expected an object, got ${typeof obj}`); return; }
    for (const key of Object.keys(obj)) {
      if (!allowed.has(key)) errors.push(`${where}: unrecognized field '${key}'`);
    }
  }

  function checkOrigin(origin, where, errors, requiredFields = []) {
    if (origin == null) {
      if (requiredFields.length) errors.push(`${where}: required (missing ${requiredFields.join(', ')})`);
      return;
    }
    checkFields(origin, ORIGIN_FIELD_SET, where, errors);
    if (!isPlainObject(origin)) return;
    for (const key of requiredFields) {
      if (!origin[key]) errors.push(`${where}.${key}: required`);
    }
  }

  function checkSolution(solution, where, errors) {
    if (solution == null) return;
    checkFields(solution, SOLUTION_FIELD_SET, where, errors);
    if (!isPlainObject(solution)) return;
    const solvers = solution.solvers ?? [];
    if (!Array.isArray(solvers)) { errors.push(`${where}.solvers must be an array, got ${typeof solvers}`); return; }
    solvers.forEach((sv, i) => checkFields(sv, SOLVER_FIELD_SET, `${where}.solvers[${i}]`, errors));
  }

  function checkHints(hints, where, errors) {
    (hints || []).forEach((h, i) => checkFields(h, HINT_FIELD_SET, `${where}[${i}]`, errors));
  }

  // allowId: only document-level sources may carry an `id` -- a ciphertext's own source could
  // never be referenced by anything, so an id there is a mistake, not a feature.
  function checkSourceList(sources, where, errors, { allowId = false } = {}) {
    (sources || []).forEach((s, i) => {
      checkFields(s, SOURCE_FIELD_SET, `${where}[${i}]`, errors);
      if (isPlainObject(s) && 'type' in s && !SOURCE_TYPES.has(s.type)) {
        errors.push(`${where}[${i}].type = ${JSON.stringify(s.type)} not in [${[...SOURCE_TYPES].join(', ')}]`);
      }
      if (isPlainObject(s) && 'id' in s) {
        if (!allowId) {
          errors.push(`${where}[${i}]: 'id' is only meaningful on document-level sources -- nothing can reference a ciphertext's own source`);
        } else if (typeof s.id !== 'string' || !s.id) {
          errors.push(`${where}[${i}].id must be a non-empty string, got ${JSON.stringify(s.id)}`);
        }
      }
    });
  }

  function collectSourceIds(sources, where, errors) {
    const ids = new Set();
    (sources || []).forEach((s, i) => {
      if (!isPlainObject(s) || typeof s.id !== 'string' || !s.id) return;
      if (ids.has(s.id)) errors.push(`${where}[${i}]: duplicate source id '${s.id}'`);
      else ids.add(s.id);
    });
    return ids;
  }

  function checkSourceIdField(value, where, errors, sourceIds, required) {
    if (value === undefined) {
      if (required) errors.push(`${where}: missing required 'source_id'`);
      return;
    }
    if (typeof value !== 'string' || !value) {
      errors.push(`${where}.source_id must be a non-empty string, got ${JSON.stringify(value)}`);
    } else if (!sourceIds.has(value)) {
      errors.push(`${where}.source_id ${JSON.stringify(value)} does not match the id of any document-level source`);
    }
  }

  function checkNoteList(notes, where, errors) {
    (notes || []).forEach((n, i) => checkFields(n, NOTE_FIELD_SET, `${where}[${i}]`, errors));
  }

  function checkChatterList(chatter, where, errors) {
    (chatter || []).forEach((c, i) => checkFields(c, CHATTER_FIELD_SET, `${where}[${i}]`, errors));
  }

  function checkRawChars(raw, charsetRe, ignoreRe, ditschar, where, errors) {
    if (typeof raw !== 'string') { errors.push(`${where}: expected a string, got ${typeof raw}`); return; }
    const rawNoGaps = raw.split(GAP_MARKER).join('');
    const bad = new Set();
    for (const ch of rawNoGaps) {
      if (!charsetRe.test(ch) && ch !== ditschar && !ignoreRe.test(ch)) bad.add(ch);
    }
    if (bad.size) errors.push(`${where}: characters not matched by charset/ditschar/ignorechars: ${JSON.stringify([...bad].sort())}`);
  }

  function fullMatchRegex(pattern, caseInsensitive) {
    // charset/ignorechars are single character classes matched against one character
    // at a time -- anchor so e.g. "[A]" doesn't accidentally match via partial search.
    return new RegExp(`^(?:${pattern})$`, caseInsensitive ? 'iu' : 'u');
  }

  // Character count with the gap marker and ignorechars removed -- the count that
  // unit_length/codebook group-structure rules are checked against.
  function cleanLength(raw, ignoreRe) {
    const noGaps = raw.split(GAP_MARKER).join('');
    let count = 0;
    for (const ch of noGaps) if (!ignoreRe.test(ch)) count++;
    return count;
  }

  // Strips remove_from_start/remove_from_end non-ignored characters from raw's ends,
  // exactly like tools/Stethoscope/Basic/ciphertext.py's _strip_ignored_boundary. Group-structure
  // checks must count the message's own content, not an embedded indicator token or other
  // boundary material that remove_from_start/remove_from_end trims away (e.g. RCA-Outgoing.cryptml
  // embeds the indicator in raw itself and strips it with remove_from_start). Returns null if a
  // trim amount exceeds the available non-ignored characters, so the caller skips the check
  // rather than guess at a length that can't actually be computed.
  function trimBoundary(raw, removeFromStart, removeFromEnd, ignoreRe) {
    let start = 0;
    if (removeFromStart) {
      let seen = 0, found = false;
      for (let i = 0; i < raw.length; i++) {
        if (!ignoreRe.test(raw[i])) {
          seen++;
          if (seen === removeFromStart) { start = i + 1; found = true; break; }
        }
      }
      if (!found) return null;
    }
    let end = raw.length;
    if (removeFromEnd) {
      let seen = 0, found = false;
      for (let i = raw.length - 1; i >= 0; i--) {
        if (!ignoreRe.test(raw[i])) {
          seen++;
          if (seen === removeFromEnd) { end = i; found = true; break; }
        }
      }
      if (!found) return null;
    }
    return start <= end ? raw.slice(start, end) : null;
  }

  function checkReferenceField(ref, where, errors) {
    if (typeof ref !== 'string' || !ref.trim()) {
      errors.push(`${where}: expected a non-empty reference string, got ${JSON.stringify(ref)}`);
      return null;
    }
    const parsed = parseReference(ref);
    if (!parsed.id) {
      errors.push(`${where}: reference ${JSON.stringify(ref)} has no id after ' :: '`);
      return null;
    }
    return parsed;
  }

  // service_records[] and plaintext_records[] are dedicated, single-purpose arrays -- unlike the
  // archival fields on ciphertexts[] (which must stay optional, since that array also holds every
  // ordinary non-archival entry), everything in these two arrays only ever means one thing, so
  // their own declared-required fields are enforced directly.
  function checkServiceRecords(records, where, errors, idsSeen, pendingReferences, sourceIds) {
    if (records === undefined) return;
    if (!Array.isArray(records)) { errors.push(`${where}: expected an array, got ${typeof records}`); return; }
    records.forEach((rec, idx) => {
      const recWhere = `${where}[${idx}]`;
      checkFields(rec, SERVICE_RECORD_FIELDS, recWhere, errors);
      if (!isPlainObject(rec)) return;

      if (typeof rec.id !== 'string' || !rec.id) {
        errors.push(`${recWhere}: missing required 'id'`);
      } else if (idsSeen.has(rec.id)) {
        errors.push(`${recWhere}: duplicate id '${rec.id}'`);
      } else {
        idsSeen.add(rec.id);
      }

      checkSourceIdField(rec.source_id, recWhere, errors, sourceIds, true);
      if (typeof rec.archive_page !== 'string' || !rec.archive_page) errors.push(`${recWhere}: missing required 'archive_page'`);
      // 'addressee' is deliberately not required here: a margin annotation or file note
      // captured as a service record may have no addressee at all, and forcing one would
      // just invite a fabricated value.
      checkOrigin(rec.origin, `${recWhere}.origin`, errors, ['date', 'originator']);

      if (!SERVICE_TYPE_VALUES.has(rec.service_type)) {
        errors.push(`${recWhere}.service_type = ${JSON.stringify(rec.service_type)} not in [${[...SERVICE_TYPE_VALUES].join(', ')}]`);
      }
      if (rec.refers_channel !== undefined && typeof rec.refers_channel !== 'string') {
        errors.push(`${recWhere}.refers_channel must be a string, got ${typeof rec.refers_channel}`);
      }
      if (rec.refers_serial !== undefined && !Number.isInteger(rec.refers_serial)) {
        errors.push(`${recWhere}.refers_serial must be an integer, got ${JSON.stringify(rec.refers_serial)}`);
      }
      if (typeof rec.text_verbatim !== 'string' || !rec.text_verbatim) {
        errors.push(`${recWhere}: missing required 'text_verbatim'`);
      }
      if ('extensions' in rec && !isPlainObject(rec.extensions)) {
        errors.push(`${recWhere}.extensions must be an object, got ${typeof rec.extensions}`);
      }
      // refers_channel/refers_serial are deliberately NOT added to pendingReferences: they're
      // read off the plaintext of a message that may never itself be catalogued, so they must
      // not be required to resolve (confirmed with the MIL session -- an unresolved refers_* is
      // their missing-serial-gap finding, not a CryptML validation error).
    });
  }

  function checkPlaintextRecords(records, where, errors, idsSeen, pendingReferences, sourceIds) {
    if (records === undefined) return;
    if (!Array.isArray(records)) { errors.push(`${where}: expected an array, got ${typeof records}`); return; }
    records.forEach((rec, idx) => {
      const recWhere = `${where}[${idx}]`;
      checkFields(rec, PLAINTEXT_RECORD_FIELDS, recWhere, errors);
      if (!isPlainObject(rec)) return;

      if (typeof rec.id !== 'string' || !rec.id) {
        errors.push(`${recWhere}: missing required 'id'`);
      } else if (idsSeen.has(rec.id)) {
        errors.push(`${recWhere}: duplicate id '${rec.id}'`);
      } else {
        idsSeen.add(rec.id);
      }

      checkSourceIdField(rec.source_id, recWhere, errors, sourceIds, true);
      if (typeof rec.archive_page !== 'string' || !rec.archive_page) errors.push(`${recWhere}: missing required 'archive_page'`);
      checkOrigin(rec.origin, `${recWhere}.origin`, errors);

      if (typeof rec.plaintext_verbatim !== 'string' || !rec.plaintext_verbatim) {
        errors.push(`${recWhere}: missing required 'plaintext_verbatim'`);
      }
      if ('extensions' in rec && !isPlainObject(rec.extensions)) {
        errors.push(`${recWhere}.extensions must be an object, got ${typeof rec.extensions}`);
      }

      if (!('message_ref' in rec)) {
        errors.push(`${recWhere}: missing required 'message_ref'`);
      } else {
        const parsed = checkReferenceField(rec.message_ref, `${recWhere}.message_ref`, errors);
        if (parsed) pendingReferences.push({ parsed, where: `${recWhere}.message_ref`, raw: rec.message_ref });
      }
    });
  }

  function validate(data) {
    const errors = [];
    if (!isPlainObject(data)) return [`document: expected an object, got ${typeof data}`];

    checkFields(data, DOCUMENT_FIELDS, 'document', errors);

    if ('cryptml_uuid' in data && !isValidUuid(data.cryptml_uuid)) {
      errors.push(`document.cryptml_uuid = ${JSON.stringify(data.cryptml_uuid)} is not a valid UUID`);
    }

    const defaultsRaw = isPlainObject(data.defaults) ? data.defaults : {};
    checkFields(data.defaults ?? {}, DEFAULTS_FIELDS, 'defaults', errors);
    const defaults = { ...DEFAULT_SETTINGS, ...defaultsRaw };

    for (const key of ['charset', 'ignorechars']) {
      if (!isSingleBracketedClass(defaults[key])) errors.push(`defaults.${key} = ${JSON.stringify(defaults[key])} is not a single bracketed character class`);
    }
    if (typeof defaults.ditschar !== 'string' || defaults.ditschar.length !== 1) {
      errors.push(`defaults.ditschar must be exactly one character, got ${JSON.stringify(defaults.ditschar)}`);
    }
    if (defaults.unit_type !== undefined && !UNIT_TYPE_VALUES.has(defaults.unit_type)) {
      errors.push(`defaults.unit_type = ${JSON.stringify(defaults.unit_type)} not in [${[...UNIT_TYPE_VALUES].join(', ')}]`);
    }
    if (defaults.unit_length !== undefined && !(Number.isInteger(defaults.unit_length) && defaults.unit_length > 0)) {
      errors.push(`defaults.unit_length must be a positive integer, got ${JSON.stringify(defaults.unit_length)}`);
    }

    checkSourceList(data.sources, 'document.sources', errors, { allowId: true });
    const sourceIds = collectSourceIds(data.sources, 'document.sources', errors);
    checkNoteList(data.notes, 'document.notes', errors);
    checkChatterList(data.chatter, 'document.chatter', errors);

    const ciphertexts = data.ciphertexts;
    if (!Array.isArray(ciphertexts) || !ciphertexts.length) {
      errors.push('document.ciphertexts: required, must have at least one entry');
      return errors;
    }

    const idsSeen = new Set();
    const pendingReferences = []; // resolved once idsSeen covers ciphertexts + service/plaintext records
    ciphertexts.forEach((ct, idx) => {
      const where = `ciphertexts[${idx}] (id=${isPlainObject(ct) && 'id' in ct ? ct.id : '?'})`;
      checkFields(ct, CIPHERTEXT_FIELDS, where, errors);
      if (!isPlainObject(ct)) return;

      const cid = ct.id;
      if (cid === undefined) {
        if (ciphertexts.length > 1) errors.push(`${where}: missing 'id', required when there is more than one ciphertext`);
      } else {
        if (idsSeen.has(cid)) errors.push(`${where}: duplicate id '${cid}'`);
        idsSeen.add(cid);
      }

      const isStub = ct.is_stub === true;
      if ('is_stub' in ct && typeof ct.is_stub !== 'boolean') {
        errors.push(`${where}.is_stub must be a boolean, got ${JSON.stringify(ct.is_stub)}`);
      }

      const hasRaw = 'raw' in ct;
      const hasParts = 'parts' in ct;
      if (hasRaw && hasParts) errors.push(`${where}: has both 'raw' and 'parts' -- exactly one is required`);
      if (isStub && (hasRaw || hasParts)) {
        errors.push(`${where}: is_stub is true but 'raw'/'parts' is also present -- a stub must have neither`);
      } else if (!isStub && !hasRaw && !hasParts) {
        errors.push(`${where}: has neither 'raw' nor 'parts' -- exactly one is required (or set is_stub: true)`);
      }

      // Archival message metadata -- see "Archival message metadata" in the spec. All optional:
      // CryptML's own validator never requires these, since ciphertexts[] also holds every
      // ordinary, non-archival entry in the corpus. Enforcing "required for a message record" is
      // a project-specific policy left to that project's own semantic validator.
      for (const [key, val] of [['serial', ct.serial], ['gr_stated', ct.gr_stated], ['pages', ct.pages]]) {
        if (val !== undefined && !(Number.isInteger(val) && val >= 0)) {
          errors.push(`${where}.${key} must be a non-negative integer, got ${JSON.stringify(val)}`);
        }
      }
      if (ct.transcription_state !== undefined && !TRANSCRIPTION_STATE_VALUES.has(ct.transcription_state)) {
        errors.push(`${where}.transcription_state = ${JSON.stringify(ct.transcription_state)} not in [${[...TRANSCRIPTION_STATE_VALUES].join(', ')}]`);
      }
      if (ct.legibility !== undefined && !LEGIBILITY_VALUES.has(ct.legibility)) {
        errors.push(`${where}.legibility = ${JSON.stringify(ct.legibility)} not in [${[...LEGIBILITY_VALUES].join(', ')}]`);
      }
      for (const key of ['unit_type', 'unit_type_asserted']) {
        if (ct[key] !== undefined && !UNIT_TYPE_VALUES.has(ct[key])) {
          errors.push(`${where}.${key} = ${JSON.stringify(ct[key])} not in [${[...UNIT_TYPE_VALUES].join(', ')}]`);
        }
      }
      if (ct.unit_length !== undefined && !(Number.isInteger(ct.unit_length) && ct.unit_length > 0)) {
        errors.push(`${where}.unit_length must be a positive integer, got ${JSON.stringify(ct.unit_length)}`);
      }
      if ('extensions' in ct && !isPlainObject(ct.extensions)) {
        errors.push(`${where}.extensions must be an object, got ${typeof ct.extensions}`);
      }
      checkSourceIdField(ct.source_id, where, errors, sourceIds, false);

      // indicator_raw is free text by design; only cross-check channel/serial/gr_stated against
      // it when it actually fits the common "<channel><serial>[/<gr_stated>]" shape -- a channel
      // whose indicators don't fit this shape just skips the cross-check, not an error.
      if (typeof ct.indicator_raw === 'string') {
        const m = ct.indicator_raw.match(INDICATOR_RE);
        if (m) {
          const [, parsedChannel, parsedSerial, parsedGrStated] = m;
          const effectiveChannel = ct.channel ?? defaults.channel;
          if (effectiveChannel !== undefined && effectiveChannel !== parsedChannel) {
            errors.push(`${where}: channel ${JSON.stringify(effectiveChannel)} doesn't match indicator_raw ${JSON.stringify(ct.indicator_raw)} (expected ${JSON.stringify(parsedChannel)})`);
          }
          if (ct.serial !== undefined && String(ct.serial) !== parsedSerial) {
            errors.push(`${where}: serial ${JSON.stringify(ct.serial)} doesn't match indicator_raw ${JSON.stringify(ct.indicator_raw)} (expected ${parsedSerial})`);
          }
          if (parsedGrStated !== undefined && ct.gr_stated !== undefined && String(ct.gr_stated) !== parsedGrStated) {
            errors.push(`${where}: gr_stated ${JSON.stringify(ct.gr_stated)} doesn't match indicator_raw ${JSON.stringify(ct.indicator_raw)} (expected ${parsedGrStated})`);
          }
        }
      }

      if ('resend_of' in ct) {
        const parsed = checkReferenceField(ct.resend_of, `${where}.resend_of`, errors);
        if (parsed) pendingReferences.push({ parsed, where: `${where}.resend_of`, raw: ct.resend_of });
      }
      if ('related' in ct) {
        if (!Array.isArray(ct.related)) {
          errors.push(`${where}.related must be an array, got ${typeof ct.related}`);
        } else {
          ct.related.forEach((ref, i) => {
            const refWhere = `${where}.related[${i}]`;
            const parsed = checkReferenceField(ref, refWhere, errors);
            if (parsed) pendingReferences.push({ parsed, where: refWhere, raw: ref });
          });
        }
      }

      let ditschar = ct.ditschar ?? defaults.ditschar;
      if (typeof ditschar !== 'string' || ditschar.length !== 1) {
        errors.push(`${where}.ditschar must be exactly one character, got ${JSON.stringify(ditschar)}`);
        ditschar = defaults.ditschar;
      }

      const charset = ct.charset ?? defaults.charset;
      const ignorechars = ct.ignorechars ?? defaults.ignorechars;
      for (const [fname, fval] of [['charset', charset], ['ignorechars', ignorechars]]) {
        if (!isSingleBracketedClass(fval)) errors.push(`${where}.${fname} = ${JSON.stringify(fval)} is not a single bracketed character class`);
      }

      const casesensitive = ct.casesensitive ?? defaults.casesensitive;
      let charsetRe = null, ignoreRe = null;
      try {
        charsetRe = fullMatchRegex(charset, !casesensitive);
        ignoreRe = fullMatchRegex(ignorechars, !casesensitive);
      } catch (e) {
        errors.push(`${where}: invalid charset/ignorechars regex: ${e.message}`);
      }

      if (charsetRe && ignoreRe.test(ditschar)) {
        errors.push(`${where}: ditschar ${JSON.stringify(ditschar)} is also matched by ignorechars ${JSON.stringify(ignorechars)}`);
      }

      if (hasParts) {
        for (const f of PART_ONLY_WHEN_SPLIT) {
          if (f in ct) errors.push(`${where}: '${f}' is illegal on a ciphertext that uses 'parts' -- move it to each part`);
        }

        const parts = ct.parts;
        if (!Array.isArray(parts) || parts.length < 2) {
          errors.push(`${where}.parts: must be an array with at least 2 entries`);
        } else {
          const partIdsSeen = new Set();
          parts.forEach((part, pidx) => {
            const pwhere = `${where}.parts[${pidx}]`;
            checkFields(part, PART_FIELDS, pwhere, errors);
            if (!isPlainObject(part)) return;
            const pid = part.part_id;
            if (pid === undefined) errors.push(`${pwhere}: missing required 'part_id'`);
            else if (partIdsSeen.has(pid)) errors.push(`${pwhere}: duplicate part_id '${pid}'`);
            else partIdsSeen.add(pid);
            if (!('raw' in part)) errors.push(`${pwhere}: missing required 'raw'`);
            else if (charsetRe) checkRawChars(part.raw, charsetRe, ignoreRe, ditschar, `${pwhere}.raw (part_id=${pid})`, errors);
            checkOrigin(part.origin, `${pwhere}.origin`, errors);
            checkSolution(part.solution, `${pwhere}.solution`, errors);
            checkHints(part.hints, `${pwhere}.hints`, errors);
          });
        }
      } else if (hasRaw && charsetRe) {
        checkRawChars(ct.raw, charsetRe, ignoreRe, ditschar, `${where}.raw`, errors);
        checkOrigin(ct.origin, `${where}.origin`, errors);
        checkSolution(ct.solution, `${where}.solution`, errors);
        checkHints(ct.hints, `${where}.hints`, errors);

        // Group structure: codebook channels must divide evenly into unit_length (every code
        // word is exactly that wide); a short final group is only ever expected on a cipher
        // channel, where it's flagged, not an error -- see validateWarnings(). unit_type_asserted
        // outranks everything else here, since its purpose is overriding the channel's norm for
        // one message (or supplying it by hand on a stub, though a stub never reaches this branch).
        const effectiveUnitType = ct.unit_type_asserted ?? ct.unit_type ?? defaults.unit_type;
        const effectiveUnitLength = ct.unit_length ?? defaults.unit_length;
        const effectiveCodebookId = ct.codebook_id ?? defaults.codebook_id;
        if (effectiveUnitType === 'codebook') {
          if (!effectiveCodebookId) {
            errors.push(`${where}: codebook_id is required when unit_type is 'codebook'`);
          }
          if (Number.isInteger(effectiveUnitLength) && effectiveUnitLength > 0 && typeof ct.raw === 'string') {
            const trimmed = trimBoundary(ct.raw, ct.remove_from_start ?? 0, ct.remove_from_end ?? 0, ignoreRe);
            if (trimmed !== null) {
              const len = cleanLength(trimmed, ignoreRe);
              if (len % effectiveUnitLength !== 0) {
                errors.push(`${where}: character count (${len}) is not a multiple of unit_length (${effectiveUnitLength}) for a codebook channel`);
              }
            }
          }
        }
      } else if (isStub) {
        // No raw to check characters/group-structure against, but origin/solution/hints are
        // still ordinary ciphertext-level objects on a stub and must have their shape checked --
        // a typo'd key inside ct.origin shouldn't silently pass just because there's no raw.
        checkOrigin(ct.origin, `${where}.origin`, errors);
        checkSolution(ct.solution, `${where}.solution`, errors);
        checkHints(ct.hints, `${where}.hints`, errors);
      }

      checkSourceList(ct.sources, `${where}.sources`, errors);
      checkNoteList(ct.notes, `${where}.notes`, errors);
      checkChatterList(ct.chatter, `${where}.chatter`, errors);
    });

    checkServiceRecords(data.service_records, 'document.service_records', errors, idsSeen, pendingReferences, sourceIds);
    checkPlaintextRecords(data.plaintext_records, 'document.plaintext_records', errors, idsSeen, pendingReferences, sourceIds);

    // resend_of/related/message_ref resolve only within this same document -- a cross-document
    // reference (a different cryptml_uuid) can't be checked without the rest of the corpus, so
    // it's accepted on syntax alone. See "Archival message metadata" in the spec.
    for (const { parsed, where, raw } of pendingReferences) {
      if (parsed.uuid === null || parsed.uuid === data.cryptml_uuid) {
        if (!idsSeen.has(parsed.id)) {
          errors.push(`${where}: reference ${JSON.stringify(raw)} does not resolve to any id in this document`);
        }
      }
    }

    return errors;
  }

  // Advisory findings that are never blocking, kept entirely separate from validate() so every
  // existing caller's pass/fail contract (errors.length === 0 means valid) stays exactly as it
  // was -- callers that want these opt in by calling this too, nothing requires it.
  function validateWarnings(data) {
    const warnings = [];
    if (!isPlainObject(data) || !Array.isArray(data.ciphertexts)) return warnings;
    const defaultsRaw = isPlainObject(data.defaults) ? data.defaults : {};
    const defaults = { ...DEFAULT_SETTINGS, ...defaultsRaw };
    const hasIdentifiedSources = Array.isArray(data.sources)
      && data.sources.some(src => isPlainObject(src) && typeof src.id === 'string' && src.id);

    // A service record should be filed under the channel it names; a cable naming several
    // channels (or none) legitimately has to go somewhere, so this is only a warning.
    if (defaults.channel !== undefined && Array.isArray(data.service_records)) {
      data.service_records.forEach((rec, idx) => {
        if (isPlainObject(rec) && typeof rec.refers_channel === 'string' && rec.refers_channel !== defaults.channel) {
          warnings.push(`document.service_records[${idx}] (id=${'id' in rec ? rec.id : '?'}): refers to channel ${JSON.stringify(rec.refers_channel)} but this file's channel is ${JSON.stringify(defaults.channel)} -- filed under a different channel than the one it names`);
        }
      });
    }

    data.ciphertexts.forEach((ct, idx) => {
      if (!isPlainObject(ct)) return;
      const where = `ciphertexts[${idx}] (id=${'id' in ct ? ct.id : '?'})`;

      if (ct.legibility === 'poor' && ct.transcription_state === 'full') {
        warnings.push(`${where}: legibility is 'poor' but transcription_state is 'full' -- a statistic built on this transcription may be unreliable`);
      }

      if (hasIdentifiedSources && ct.source_id === undefined) {
        warnings.push(`${where}: no source_id, although this document defines identified sources -- was it filed under its source?`);
      }

      if (ct.is_stub === true || typeof ct.raw !== 'string') return; // nothing to count groups on

      const ignorechars = ct.ignorechars ?? defaults.ignorechars;
      const casesensitive = ct.casesensitive ?? defaults.casesensitive;
      let ignoreRe;
      try { ignoreRe = fullMatchRegex(ignorechars, !casesensitive); } catch { return; }

      const effectiveUnitType = ct.unit_type_asserted ?? ct.unit_type ?? defaults.unit_type;
      const effectiveUnitLength = ct.unit_length ?? defaults.unit_length;
      if (!Number.isInteger(effectiveUnitLength) || effectiveUnitLength <= 0) return;

      const trimmed = trimBoundary(ct.raw, ct.remove_from_start ?? 0, ct.remove_from_end ?? 0, ignoreRe);
      if (trimmed === null) return;
      const len = cleanLength(trimmed, ignoreRe);
      const remainder = len % effectiveUnitLength;
      if (effectiveUnitType === 'cipher' && remainder !== 0) {
        warnings.push(`${where}: short final group of ${remainder} character(s) (group width ${effectiveUnitLength}) -- preserved, not padded or trimmed`);
      }

      // Only meaningful on a full transcription: on "head_tail"/"none", the counted
      // total is legitimately partial and disagrees with gr_stated by design, not by error.
      if (ct.gr_stated !== undefined && ct.transcription_state === 'full') {
        const computedGroups = Math.ceil(len / effectiveUnitLength);
        if (computedGroups !== ct.gr_stated) {
          warnings.push(`${where}: gr_stated (${ct.gr_stated}) doesn't match the counted group total (${computedGroups})`);
        }
      }
    });

    return warnings;
  }

  // ---------- field specs for repeatable / single-object sections ----------

  // Fields the page used to define inline; shared here so the document Defaults and each
  // ciphertext show identical wording, and so a test can insist every field has a hint.
  const DOCUMENT_TITLE_FIELD = { key: 'title', label: 'Title', hint: 'A name for this document or collection.', type: 'text' };

  const CIPHERTEXT_ID_FIELD = { key: 'id', label: 'ID', hint: 'Unique name for this ciphertext, e.g. A42/53. Must be unique across all the records in this file (ciphertexts, service records and plaintext records together). Free text; shown on its tab and used by references from other records.', type: 'text' };

  const PART_ID_FIELD = { key: 'part_id', label: 'Part ID', hint: 'Label for this part, e.g. a or b. Must be unique within this ciphertext.', type: 'text' };

  const CIPHER_SETTING_FIELDS = [
    { key: 'cipher_system', label: 'Cipher system', hint: 'The kind of cipher, e.g. Vigenere, Hill, Playfair, or unknown. Free text.', type: 'text' },
    { key: 'charset', label: 'Charset (regex character class)', hint: 'Regex character class of the valid cipher symbols, e.g. [A-Z] or [A-Z0-9]. It must be a single bracketed class. Every character of the ciphertext must match this, the dits char, or the ignore chars.', type: 'text' },
    { key: 'casesensitive', label: 'Case sensitive', hint: 'Tick if upper and lower case letters are different symbols. Unticked, letters are treated as upper case.', type: 'checkbox' },
    { key: 'ditschar', label: 'Dits char', hint: 'One character standing for a missing or unrecoverable symbol, e.g. -.', type: 'text' },
    { key: 'ignorechars', label: 'Ignore chars (regex character class)', hint: 'Regex character class of characters that are silently dropped, such as the spaces between groups: [\s].', type: 'text' },
  ];

  const PLAINTEXT_CHARSET_FIELD = { key: 'plaintext_charset', label: 'Plaintext charset (descriptive only)', hint: 'Describes the alphabet the cipher units stand for, e.g. [A-Z]. Descriptive only: it is not checked against the plaintext.', type: 'text' };

  const TRIM_FIELDS = [
    { key: 'remove_from_start', label: 'Remove from start', hint: 'How many non-ignored characters to strip from the start of the ciphertext, e.g. 6 for an indicator such as A50/18 written into the text. Counts letters and digits, not spaces.', type: 'number', min: 0 },
    { key: 'remove_from_end', label: 'Remove from end', hint: 'How many non-ignored characters to strip from the end of the ciphertext, e.g. padding added to fill the last group.', type: 'number', min: 0 },
  ];

  const RAW_HINT = 'The ciphertext exactly as transcribed. Write [...] where an unknown amount of text was not transcribed.';

  const SOURCE_FIELDS = [
    { key: 'type', label: 'Type', hint: 'What kind of source this is: book, web, letter, periodical, person, competition or other.', type: 'select', options: ['book', 'web', 'letter', 'periodical', 'person', 'competition', 'other'] },
    { key: 'title', label: 'Title', hint: 'Title of the book, web page, archive file or other item.', type: 'text' },
    { key: 'identifier', label: 'Identifier', hint: 'Shelfmark, accession number, ISBN, DOI, physical ID -- whatever identifies the item in its own collection.', type: 'text' },
    { key: 'author', label: 'Author', hint: 'Author of the publication. Not who composed the cryptogram; that is Origin: Originator.', type: 'text' },
    { key: 'publisher', label: 'Publisher', hint: 'Publisher, if any.', type: 'text' },
    { key: 'date', label: 'Date', hint: 'Publication or acquisition date of this citation, not when the ciphertext was created. Free text.', type: 'text' },
    { key: 'page', label: 'Page', hint: 'Page or section of the whole publication that this source refers to. The page of an individual message goes in Archive page(s) on the ciphertext instead.', type: 'text' },
    { key: 'url', label: 'URL', hint: 'Web address, if the source is on the web.', type: 'text' },
    { key: 'note', label: 'Note', hint: 'Anything else about this source.', type: 'text' },
  ];

  // Only document-level sources can carry an id (so a ciphertext can name one via source_id).
  const DOCUMENT_SOURCE_FIELDS = [
    { key: 'id', label: 'ID', hint: 'Optional. A source with an ID applies only to ciphertexts that name it in their Source field; a source without one applies to every ciphertext.', type: 'text' },
    ...SOURCE_FIELDS,
  ];

  const HINT_FIELDS = [
    { key: 'text', label: 'Text', hint: 'The suspected plaintext fragment (a crib), e.g. THE.', type: 'text' },
    { key: 'position', label: 'Position', hint: 'Where in the ciphertext the fragment is believed to occur, e.g. start, or 120-123.', type: 'text' },
    { key: 'source', label: 'Source', hint: 'Where the hint came from, e.g. the puzzle statement.', type: 'text' },
    { key: 'confidence', label: 'Confidence', hint: 'How sure the hint is, e.g. certain, probable, guess.', type: 'text' },
    { key: 'notes', label: 'Notes', hint: 'Anything else about this hint.', type: 'text' },
  ];

  const REFERENCE_FIELDS = [
    { key: 'citation', label: 'Citation', hint: 'A bibliographic citation for related reading.', type: 'text' },
    { key: 'url', label: 'URL', hint: 'Web address for that reference.', type: 'text' },
  ];

  const NOTE_FIELDS = [
    { key: 'title', label: 'Title', hint: 'A short heading for the note.', type: 'text' },
    { key: 'text', label: 'Text', hint: 'The note itself. Free text.', type: 'textarea' },
  ];

  const CHATTER_FIELDS = [
    { key: 'author', label: 'Author', hint: 'Who wrote the remark.', type: 'text' },
    { key: 'date', label: 'Date', hint: 'When the remark was written. Free text.', type: 'text' },
    { key: 'text', label: 'Text', hint: 'The remark: a working comment or discussion about this item.', type: 'textarea' },
  ];

  const ORIGIN_FIELDS = [
    { key: 'date', label: 'Date', hint: 'When the message was created or sent, not when it was published. Free text, e.g. 1949-01-27.', type: 'text' },
    { key: 'time', label: 'Time', hint: 'Time of day it was sent, e.g. 1300 or 14:32. Free text.', type: 'text' },
    { key: 'originator', label: 'Originator', hint: 'Who composed or sent it, as written, e.g. ISR1 NEWYORK. Not the author of a book it later appeared in.', type: 'text' },
    { key: 'addressee', label: 'Addressee', hint: 'Who it was sent to, as written, e.g. MEMISRAEL GENEVA.', type: 'text' },
    { key: 'method', label: 'Method', hint: 'How this copy was produced or obtained, e.g. transcribed from a photo. Not the cipher system.', type: 'text' },
    { key: 'location', label: 'Location', hint: 'Where the message was found or created, in free text. Leave blank for archival material; use Source and Archive page(s) instead.', type: 'text' },
    { key: 'remarks', label: 'Remarks', hint: "Anything else about the message's origin.", type: 'textarea' },
  ];

  // ---------- archival message metadata (CryptML 1.2) form specs ----------
  // Every spec key here must also be in the matching validation field set above -- the Node tests
  // check that, so a form control can never write a field the validator then rejects as unknown.

  const INHERIT_HINT = 'Leave blank to inherit this from the document Defaults.';
  const ARCHIVE_PAGE_HINT = 'Page or range within the source. Free text; it is not checked. Convention: one page 45, a range 45-46, several separated by commas 45, 47-48.';

  const DEFAULTS_ARCHIVAL_FIELDS = [
    { key: 'channel', label: 'Channel', hint: 'Channel prefix, e.g. A or NP. Cascades to every ciphertext that does not override it.', type: 'text', optional: true },
    { key: 'unit_type', label: 'Unit type', hint: 'What the groups are: codebook, cipher or unknown. Selects the group-structure validation rule.', type: 'select', options: [...UNIT_TYPE_VALUES], optional: true },
    { key: 'codebook_id', label: 'Codebook ID', hint: 'Required whenever the unit type is codebook.', type: 'text', optional: true },
    { key: 'unit_length', label: 'Unit length', hint: 'Group / code-word width in characters.', type: 'number', min: 1, optional: true },
  ];

  // The whole document Defaults form.
  const DEFAULTS_FORM_FIELDS = [...CIPHER_SETTING_FIELDS, PLAINTEXT_CHARSET_FIELD, ...DEFAULTS_ARCHIVAL_FIELDS];

  const ARCHIVAL_FORM_GROUPS = [
    { title: 'Source and page', fields: [
      { key: 'source_id', label: 'Source', hint: 'Which document-level Source this comes from (a source that has an ID).', type: 'text', optional: true },
      { key: 'archive_page', label: 'Archive page(s)', hint: ARCHIVE_PAGE_HINT, type: 'text', optional: true },
    ] },
    { title: 'Indicator and preamble (verbatim)', fields: [
      { key: 'indicator_raw', label: 'Indicator (verbatim)', hint: 'The indicator exactly as written on the cable, e.g. A42/53 or NA9. Never normalise it.', type: 'text', monospace: true, optional: true },
      { key: 'channel', label: 'Channel (inherits)', hint: 'Channel prefix, e.g. A or NP. ' + INHERIT_HINT, type: 'text', optional: true },
      { key: 'serial', label: 'Serial', hint: 'The running number from the indicator (the 42 in A42/53).', type: 'number', min: 0, optional: true },
      { key: 'gr_stated', label: 'Groups stated', hint: 'Group count as written in the indicator itself. Leave blank if the indicator carries none -- that absence is meaningful.', type: 'number', min: 0, optional: true },
      { key: 'pages', label: 'Transmission pages', hint: 'Number of transmission pages the message occupied.', type: 'number', min: 0, optional: true },
      { key: 'preamble_raw', label: 'Preamble (verbatim)', hint: 'The whole header line(s) exactly as transcribed, e.g. ISR6 NEWYORK JAN 27 / CDE PALOFFICE GENEVA. The Origin fields hold your parsed reading of it.', type: 'textarea', rows: 3, monospace: true, optional: true },
      { key: 'service_line_raw', label: 'Service line (verbatim)', hint: 'Trailing service text exactly as transcribed, e.g. ACKPLS ISR / RECD ISR2 HE 1633 TU. A correction the sender transmitted (e.g. CORRN PLS INSERT AFTER ...) is service text and belongs here, verbatim. Corrections you make to your own reading go in Anomaly notes instead.', type: 'textarea', rows: 3, monospace: true, optional: true },
    ] },
    { title: 'Quality and state', fields: [
      { key: 'transcription_state', label: 'Transcription state', hint: 'How much of the message is transcribed: none, head_tail (start and end only) or full.', type: 'select', options: [...TRANSCRIPTION_STATE_VALUES], optional: true },
      { key: 'legibility', label: 'Legibility', hint: 'How readable the source is: clean, partial or poor.', type: 'select', options: [...LEGIBILITY_VALUES], optional: true },
      { key: 'anomaly_notes', label: 'Anomaly notes', hint: 'Anything odd about the source, exactly as seen: overstrikes, struck-through groups, garbles, corrections marked on the document, marginalia. A correction the sender transmitted belongs in Service line instead.', type: 'textarea', rows: 3, optional: true },
    ] },
    { title: 'Group structure', fields: [
      { key: 'unit_type', label: 'Unit type (inherits)', hint: 'What the groups are: codebook, cipher or unknown. ' + INHERIT_HINT, type: 'select', options: [...UNIT_TYPE_VALUES], optional: true },
      { key: 'unit_type_asserted', label: 'Unit type asserted', hint: 'Hand-asserted classification for this one message; outranks the inherited unit type.', type: 'select', options: [...UNIT_TYPE_VALUES], optional: true },
      { key: 'codebook_id', label: 'Codebook ID (inherits)', hint: 'Which codebook is in use. Required when the unit type is codebook. ' + INHERIT_HINT, type: 'text', optional: true },
      { key: 'unit_length', label: 'Unit length (inherits)', hint: 'Group / code-word width in characters. ' + INHERIT_HINT, type: 'number', min: 1, optional: true },
    ] },
    { title: 'Links to other records', fields: [
      { key: 'resend_of', label: 'Resend of', hint: 'The message this one retransmits: an id in this file, or "<cryptml_uuid> :: <id>" for another file.', type: 'text', optional: true },
      { key: 'related', label: 'Related (one per line)', hint: 'Other records bearing on this one, one reference per line (id, or "<cryptml_uuid> :: <id>").', type: 'lines', optional: true },
    ] },
    { title: 'Extensions', fields: [
      { key: 'extensions', label: 'Extensions (JSON)', hint: 'Free-form JSON object, never validated. Nothing may depend on what is in it.', type: 'json', rows: 4, optional: true },
    ] },
  ];

  const ARCHIVAL_FORM_KEYS = ARCHIVAL_FORM_GROUPS.flatMap(g => g.fields.map(f => f.key));

  const SERVICE_RECORD_FORM_FIELDS = [
    { key: 'id', label: 'ID', hint: 'Unique across all the records in this file: ciphertexts, service records and plaintext records together.', type: 'text' },
    { key: 'source_id', label: 'Source', hint: 'Which document-level Source this comes from (a source that has an ID).', type: 'text', optional: true },
    { key: 'archive_page', label: 'Archive page(s)', hint: ARCHIVE_PAGE_HINT, type: 'text' },
    { key: 'service_type', label: 'Service type', hint: 'Kind of service traffic: repeat_request (asks for a repeat), repeat (the sender re-sending part or all of an earlier message), receipt, plain_message, chatter or other.', type: 'select', options: [...SERVICE_TYPE_VALUES] },
    { key: 'refers_channel', label: 'Refers to channel', hint: 'Channel named in the text, if any, e.g. PN. Descriptive only; it need not match a message in this file.', type: 'text', optional: true },
    { key: 'refers_serial', label: 'Refers to serial', hint: 'Serial named in the text, if any, e.g. 41. Descriptive only.', type: 'number', min: 0, optional: true },
    { key: 'text_verbatim', label: 'Text (verbatim)', hint: 'The full text exactly as written.', type: 'textarea', rows: 4, monospace: true },
    { key: 'extensions', label: 'Extensions (JSON)', hint: 'Free-form JSON object, never validated. Nothing may depend on what is in it.', type: 'json', optional: true },
  ];

  const PLAINTEXT_RECORD_FORM_FIELDS = [
    { key: 'id', label: 'ID', hint: 'Unique across all the records in this file: ciphertexts, service records and plaintext records together.', type: 'text' },
    { key: 'source_id', label: 'Source', hint: 'Which document-level Source this comes from (a source that has an ID).', type: 'text', optional: true },
    { key: 'archive_page', label: 'Archive page(s)', hint: ARCHIVE_PAGE_HINT, type: 'text' },
    { key: 'message_ref', label: 'Message ref', hint: 'The message this plaintext corresponds to: an id in this file, or "<cryptml_uuid> :: <id>".', type: 'text' },
    { key: 'plaintext_verbatim', label: 'Plaintext (verbatim)', hint: 'The recovered plaintext exactly as recovered.', type: 'textarea', rows: 4, monospace: true },
    { key: 'extensions', label: 'Extensions (JSON)', hint: 'Free-form JSON object, never validated. Nothing may depend on what is in it.', type: 'json', optional: true },
  ];

  // Turns the plain-text `source_id` spec into a dropdown of the document's identified sources.
  // The option list is a function, re-read whenever the dropdown gets focus, so a source added
  // or renamed since the form was drawn still shows up.
  function withSourceChoices(specs, getDoc) {
    const identified = () => (getDoc().sources || []).filter(src => src && src.id);
    return specs.map(spec => spec.key !== 'source_id' ? spec : {
      ...spec,
      type: 'select',
      options: () => identified().map(src => src.id),
      optionLabel: id => {
        const src = identified().find(x => x.id === id);
        return src && src.title ? `${id} -- ${src.title}` : id;
      },
    });
  }

  function blankServiceRecord() {
    return { id: '', archive_page: '', origin: blankOrigin(), service_type: 'other', text_verbatim: '' };
  }

  function blankPlaintextRecord() {
    return { id: '', archive_page: '', origin: blankOrigin(), message_ref: '', plaintext_verbatim: '' };
  }

  const SOLUTION_FIELDS = [
    { key: 'plaintext', label: 'Plaintext', hint: 'The recovered plaintext, written naturally: mixed case and punctuation are fine. It is not checked against any alphabet.', type: 'textarea', monospace: true },
    PLAINTEXT_CHARSET_FIELD,
    { key: 'key', label: 'Key', hint: 'The key, if known, e.g. 3-1-2 or a keyword.', type: 'text' },
  ];

  const SOLVER_FIELDS = [
    { key: 'solved_by', label: 'Solved by', hint: 'Who solved it.', type: 'text' },
    { key: 'solved_date', label: 'Solved date', hint: 'When it was solved. Free text.', type: 'text' },
    { key: 'method', label: 'Method', hint: 'How it was solved.', type: 'textarea' },
    { key: 'notes', label: 'Notes', hint: 'Anything else about this attempt.', type: 'textarea' },
  ];

  // ---------- DOM helpers ----------

  function el(tag, props = {}, children = []) {
    const node = document.createElement(tag);
    for (const [k, v] of Object.entries(props)) {
      if (k === 'className') node.className = v;
      else if (k.startsWith('on') && typeof v === 'function') node.addEventListener(k.slice(2).toLowerCase(), v);
      else if (v !== undefined && v !== null) node.setAttribute(k, v);
    }
    for (const child of [].concat(children)) {
      if (child === null || child === undefined) continue;
      node.appendChild(typeof child === 'string' ? document.createTextNode(child) : child);
    }
    return node;
  }

  // spec.optional: an emptied field is deleted from obj rather than stored as ''/0, because for
  // archival metadata "absent" is meaningful (e.g. no gr_stated is itself a fact about a channel,
  // distinct from gr_stated: 0).
  function buildFieldRow(spec, obj, onChange) {
    const value = obj[spec.key];
    const changed = () => { if (onChange) onChange(); };
    const setOrClear = (isEmpty, newValue) => {
      if (spec.optional && isEmpty) delete obj[spec.key];
      else obj[spec.key] = newValue;
      changed();
    };
    let errorEl = null;
    let input;
    if (spec.type === 'textarea') {
      input = el('textarea', { rows: spec.rows || 2, onInput: e => setOrClear(e.target.value === '', e.target.value) });
      input.value = value ?? '';
    } else if (spec.type === 'select') {
      const optionLabel = opt => opt === '' ? '(not set)' : (spec.optionLabel ? spec.optionLabel(opt) : opt);
      input = el('select', { onChange: e => setOrClear(e.target.value === '', e.target.value) });
      const fillOptions = () => {
        const current = obj[spec.key];
        const base = typeof spec.options === 'function' ? spec.options() : spec.options;
        const options = [...(spec.optional ? [''] : []), ...base];
        // a stored value that is no longer a valid choice stays visible rather than silently vanishing
        if (current !== undefined && current !== '' && !options.includes(current)) options.push(current);
        input.innerHTML = '';
        options.forEach(opt => input.appendChild(
          el('option', { value: opt, selected: opt === (current ?? '') ? 'selected' : undefined }, optionLabel(opt))));
      };
      fillOptions();
      if (typeof spec.options === 'function') input.addEventListener('focus', fillOptions);
    } else if (spec.type === 'checkbox') {
      input = el('input', { type: 'checkbox', onChange: e => setOrClear(!e.target.checked, e.target.checked) });
      input.checked = !!value;
    } else if (spec.type === 'number') {
      input = el('input', {
        type: 'number', min: spec.min, step: 1,
        onInput: e => setOrClear(e.target.value === '', e.target.value === '' ? 0 : Number(e.target.value)),
      });
      input.value = value ?? (spec.optional ? '' : 0);
    } else if (spec.type === 'lines') {
      input = el('textarea', {
        rows: spec.rows || 3,
        onInput: e => {
          const lines = e.target.value.split('\n').map(s => s.trim()).filter(Boolean);
          if (lines.length) obj[spec.key] = lines; else delete obj[spec.key];
          changed();
        },
      });
      input.value = (value || []).join('\n');
    } else if (spec.type === 'json') {
      errorEl = el('div', { className: 'field-error' });
      input = el('textarea', {
        rows: spec.rows || 3,
        onInput: e => {
          const text = e.target.value.trim();
          if (!text) { delete obj[spec.key]; errorEl.textContent = ''; changed(); return; }
          let parsed;
          try { parsed = JSON.parse(text); } catch (err) { errorEl.textContent = `Not valid JSON: ${err.message}`; return; }
          if (!isPlainObject(parsed)) { errorEl.textContent = 'Must be a JSON object, e.g. {"key": "value"}'; return; }
          if (Object.keys(parsed).length) obj[spec.key] = parsed; else delete obj[spec.key];
          errorEl.textContent = '';
          changed();
        },
      });
      input.value = isPlainObject(value) && Object.keys(value).length ? JSON.stringify(value, null, 2) : '';
      input.classList.add('mono-field');
    } else {
      input = el('input', { type: 'text', onInput: e => setOrClear(e.target.value === '', e.target.value) });
      input.value = value ?? '';
    }
    if (spec.monospace) input.classList.add('mono-field');
    input.id = `f_${Math.random().toString(36).slice(2)}`;
    if (spec.hint) input.title = spec.hint;
    const label = el('label', { for: input.id, title: spec.hint }, spec.label);
    const control = errorEl ? el('div', { className: 'field-control' }, [input, errorEl]) : input;
    return el('div', { className: 'field-row' }, [label, control]);
  }

  function renderObjectSection(container, obj, fieldSpecs, onChange) {
    container.innerHTML = '';
    for (const spec of fieldSpecs) container.appendChild(buildFieldRow(spec, obj, onChange));
  }

  function renderRepeatable(container, items, fieldSpecs, opts) {
    container.innerHTML = '';
    items.forEach((item, index) => {
      const fieldset = el('fieldset', { className: 'repeat-item' }, [
        el('legend', {}, [
          `#${index + 1}`,
          el('button', {
            type: 'button', className: 'remove-btn',
            onClick: () => { items.splice(index, 1); renderRepeatable(container, items, fieldSpecs, opts); },
          }, 'Remove'),
        ]),
      ]);
      for (const spec of fieldSpecs) fieldset.appendChild(buildFieldRow(spec, item, opts && opts.onChange));
      // opts.nested: [{ key, label, fields }] -- an object-valued field (e.g. a record's `origin`)
      // edited as its own collapsible group inside the item.
      for (const nest of (opts && opts.nested) || []) {
        item[nest.key] = item[nest.key] || {};
        const body = el('div', {});
        renderObjectSection(body, item[nest.key], nest.fields, opts.onChange);
        fieldset.appendChild(el('details', { className: 'subsection', open: 'open' }, [el('summary', {}, nest.label), body]));
      }
      container.appendChild(fieldset);
    });
    container.appendChild(el('button', {
      type: 'button', className: 'add-btn',
      onClick: () => {
        items.push(opts.blank());
        renderRepeatable(container, items, fieldSpecs, opts);
      },
    }, `+ Add ${opts.itemLabel}`));
  }

  return {
    DEFAULT_SETTINGS,
    resolveSettings,
    newDocument,
    newCiphertext,
    nextCiphertextId,
    nextPartId,
    naturalCompare,
    sortCiphertextsById,
    parseDocument,
    serializeDocument,
    validate,
    validateWarnings,
    isValidUuid,
    parseReference,
    SOURCE_FIELDS, DOCUMENT_SOURCE_FIELDS, HINT_FIELDS, REFERENCE_FIELDS, NOTE_FIELDS, CHATTER_FIELDS,
    ORIGIN_FIELDS, SOLUTION_FIELDS, SOLVER_FIELDS,
    DEFAULTS_ARCHIVAL_FIELDS, DEFAULTS_FORM_FIELDS, ARCHIVAL_FORM_GROUPS, ARCHIVAL_FORM_KEYS,
    DOCUMENT_TITLE_FIELD, CIPHERTEXT_ID_FIELD, PART_ID_FIELD, CIPHER_SETTING_FIELDS, PLAINTEXT_CHARSET_FIELD,
    TRIM_FIELDS, RAW_HINT,
    SERVICE_RECORD_FORM_FIELDS, PLAINTEXT_RECORD_FORM_FIELDS,
    el, buildFieldRow, renderObjectSection, renderRepeatable, withSourceChoices,
    blankOrigin, blankSolution, blankSolver, blankPart, blankServiceRecord, blankPlaintextRecord,
    serializeSolution,
  };
})();

// Dual-environment export: a plain <script> tag in the browser just sees the
// `const CryptMLEditor` global above. Under Node (no `window`), also export it
// as a CommonJS module so tools/CryptML/generate-manifest.js and the GitHub
// Action can `require()` the same validation logic instead of reimplementing it.
if (typeof module !== 'undefined' && module.exports) {
  module.exports = CryptMLEditor;
}
