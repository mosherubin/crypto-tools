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

  const INHERITED_FIELDS = ['cipher_system', 'charset', 'casesensitive', 'ditschar', 'ignorechars'];

  // ---------- data model ----------

  function resolveSettings(documentDefaults) {
    return { ...DEFAULT_SETTINGS, ...(documentDefaults || {}) };
  }

  function blankOrigin() {
    return { date: '', originator: '', method: '', location: '', remarks: '' };
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
      cryptml_version: '1.0',
      title: '',
      defaults,
      sources: [],
      references: [],
      notes: [],
      chatter: [],
      ciphertexts: [newCiphertext('1', defaults)],
    };
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
        sources: ct.sources || [],
        references: ct.references || [],
        notes: ct.notes || [],
        chatter: ct.chatter || [],
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

      if (!('raw' in ct)) throw new Error(`Ciphertext '${id}' has neither 'raw' nor 'parts'`);

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
      cryptml_version: data.cryptml_version || '1.0',
      title: data.title || '',
      defaults,
      sources: data.sources || [],
      references: data.references || [],
      notes: data.notes || [],
      chatter: data.chatter || [],
      ciphertexts,
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
      if (ct[name] !== defaults[name]) out[name] = ct[name];
    }

    if (ct.parts) {
      out.parts = ct.parts.map(p => serializePart(p, defaults));
    } else {
      out.raw = ct.raw;
      if (ct.remove_from_start) out.remove_from_start = ct.remove_from_start;
      if (ct.remove_from_end) out.remove_from_end = ct.remove_from_end;
      const origin = trimObject(ct.origin);
      if (origin) out.origin = origin;
      const solution = serializeSolution(ct.solution, defaults);
      if (solution) out.solution = solution;
      const hints = ct.hints.map(h => trimObject(h)).filter(Boolean);
      if (hints.length) out.hints = hints;
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
    return out;
  }

  // ---------- field specs for repeatable / single-object sections ----------

  const SOURCE_FIELDS = [
    { key: 'type', label: 'Type', type: 'select', options: ['book', 'web', 'letter', 'periodical', 'person', 'competition', 'other'] },
    { key: 'title', label: 'Title', type: 'text' },
    { key: 'author', label: 'Author', type: 'text' },
    { key: 'publisher', label: 'Publisher', type: 'text' },
    { key: 'date', label: 'Date', type: 'text' },
    { key: 'page', label: 'Page', type: 'text' },
    { key: 'url', label: 'URL', type: 'text' },
    { key: 'note', label: 'Note', type: 'text' },
  ];

  const HINT_FIELDS = [
    { key: 'text', label: 'Text', type: 'text' },
    { key: 'position', label: 'Position', type: 'text' },
    { key: 'source', label: 'Source', type: 'text' },
    { key: 'confidence', label: 'Confidence', type: 'text' },
    { key: 'notes', label: 'Notes', type: 'text' },
  ];

  const REFERENCE_FIELDS = [
    { key: 'citation', label: 'Citation', type: 'text' },
    { key: 'url', label: 'URL', type: 'text' },
  ];

  const NOTE_FIELDS = [
    { key: 'title', label: 'Title', type: 'text' },
    { key: 'text', label: 'Text', type: 'textarea' },
  ];

  const CHATTER_FIELDS = [
    { key: 'author', label: 'Author', type: 'text' },
    { key: 'date', label: 'Date', type: 'text' },
    { key: 'text', label: 'Text', type: 'textarea' },
  ];

  const ORIGIN_FIELDS = [
    { key: 'date', label: 'Date', type: 'text' },
    { key: 'originator', label: 'Originator', type: 'text' },
    { key: 'method', label: 'Method', type: 'text' },
    { key: 'location', label: 'Location', type: 'text' },
    { key: 'remarks', label: 'Remarks', type: 'textarea' },
  ];

  const SOLUTION_FIELDS = [
    { key: 'plaintext', label: 'Plaintext', type: 'textarea' },
    { key: 'plaintext_charset', label: 'Plaintext charset (descriptive only)', type: 'text' },
    { key: 'key', label: 'Key', type: 'text' },
  ];

  const SOLVER_FIELDS = [
    { key: 'solved_by', label: 'Solved by', type: 'text' },
    { key: 'solved_date', label: 'Solved date', type: 'text' },
    { key: 'method', label: 'Method', type: 'textarea' },
    { key: 'notes', label: 'Notes', type: 'textarea' },
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

  function buildFieldRow(spec, obj, onChange) {
    const value = obj[spec.key];
    let input;
    if (spec.type === 'textarea') {
      input = el('textarea', { rows: 2, onInput: e => { obj[spec.key] = e.target.value; if (onChange) onChange(); } });
      input.value = value ?? '';
    } else if (spec.type === 'select') {
      input = el('select', { onChange: e => { obj[spec.key] = e.target.value; if (onChange) onChange(); } },
        spec.options.map(opt => el('option', { value: opt, selected: opt === value ? 'selected' : undefined }, opt)));
    } else if (spec.type === 'checkbox') {
      input = el('input', { type: 'checkbox', onChange: e => { obj[spec.key] = e.target.checked; if (onChange) onChange(); } });
      input.checked = !!value;
    } else if (spec.type === 'number') {
      input = el('input', { type: 'number', onInput: e => { obj[spec.key] = e.target.value === '' ? 0 : Number(e.target.value); if (onChange) onChange(); } });
      input.value = value ?? 0;
    } else {
      input = el('input', { type: 'text', onInput: e => { obj[spec.key] = e.target.value; if (onChange) onChange(); } });
      input.value = value ?? '';
    }
    input.id = `f_${Math.random().toString(36).slice(2)}`;
    const label = el('label', { for: input.id }, spec.label);
    return el('div', { className: 'field-row' }, [label, input]);
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
    parseDocument,
    serializeDocument,
    SOURCE_FIELDS, HINT_FIELDS, REFERENCE_FIELDS, NOTE_FIELDS, CHATTER_FIELDS,
    ORIGIN_FIELDS, SOLUTION_FIELDS, SOLVER_FIELDS,
    el, buildFieldRow, renderObjectSection, renderRepeatable,
    blankOrigin, blankSolution, blankSolver, blankPart, serializeSolution,
  };
})();
