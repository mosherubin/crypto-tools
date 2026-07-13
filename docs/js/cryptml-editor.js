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
    ignorechars: '\\s',
    plaintext_charset: '[A-Z]',
  };

  const INHERITED_FIELDS = ['cipher_system', 'charset', 'casesensitive', 'ditschar', 'ignorechars'];

  // ---------- data model ----------

  function resolveSettings(documentDefaults) {
    return { ...DEFAULT_SETTINGS, ...(documentDefaults || {}) };
  }

  function blankOrigin() {
    return { date: '', collector: '', method: '', location: '', remarks: '' };
  }

  function blankSolution(defaults) {
    return { plaintext: '', plaintext_charset: defaults.plaintext_charset, key: '', solved_by: '', solved_date: '', method: '', notes: '' };
  }

  function newCiphertext(id, defaults) {
    return {
      id,
      raw: '',
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
      tests: [],
      references: [],
      notes: [],
      chitchat: [],
    };
  }

  function newDocument() {
    const defaults = resolveSettings({});
    return {
      cryptml_version: '1.0',
      title: '',
      defaults,
      references: [],
      notes: [],
      chitchat: [],
      ciphertexts: [newCiphertext('1', defaults)],
    };
  }

  function nextCiphertextId(doc) {
    const used = new Set(doc.ciphertexts.map(ct => ct.id));
    let n = 1;
    while (used.has(String(n))) n++;
    return String(n);
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

      if (!('raw' in ct)) throw new Error(`Ciphertext '${id}' is missing required field 'raw'`);

      let solution = null;
      if (ct.solution) {
        solution = { ...blankSolution(defaults), ...ct.solution };
      }

      return {
        id,
        raw: ct.raw,
        cipher_system: ct.cipher_system ?? defaults.cipher_system,
        charset: ct.charset ?? defaults.charset,
        casesensitive: ct.casesensitive ?? defaults.casesensitive,
        ditschar: ct.ditschar ?? defaults.ditschar,
        ignorechars: ct.ignorechars ?? defaults.ignorechars,
        remove_from_start: ct.remove_from_start ?? 0,
        remove_from_end: ct.remove_from_end ?? 0,
        origin: { ...blankOrigin(), ...(ct.origin || {}) },
        sources: ct.sources || [],
        solution,
        hints: ct.hints || [],
        tests: ct.tests || [],
        references: ct.references || [],
        notes: ct.notes || [],
        chitchat: ct.chitchat || [],
      };
    });

    return {
      cryptml_version: data.cryptml_version || '1.0',
      title: data.title || '',
      defaults,
      references: data.references || [],
      notes: data.notes || [],
      chitchat: data.chitchat || [],
      ciphertexts,
    };
  }

  function trimObject(obj) {
    const entries = Object.entries(obj || {}).filter(([, v]) => v);
    return entries.length ? Object.fromEntries(entries) : null;
  }

  function smartParse(text) {
    if (typeof text !== 'string' || text.trim() === '') return undefined;
    try {
      return JSON.parse(text);
    } catch {
      return text;
    }
  }

  function serializeCiphertext(ct, defaults) {
    const out = { id: ct.id, raw: ct.raw };
    for (const name of INHERITED_FIELDS) {
      if (ct[name] !== defaults[name]) out[name] = ct[name];
    }
    if (ct.remove_from_start) out.remove_from_start = ct.remove_from_start;
    if (ct.remove_from_end) out.remove_from_end = ct.remove_from_end;
    const origin = trimObject(ct.origin);
    if (origin) out.origin = origin;
    if (ct.sources.length) out.sources = ct.sources.map(s => trimObject(s) || {});
    if (ct.solution) {
      const solution = { ...ct.solution };
      if (solution.plaintext_charset === defaults.plaintext_charset) delete solution.plaintext_charset;
      out.solution = solution;
    }
    if (ct.hints.length) out.hints = ct.hints.map(h => trimObject(h) || {});
    if (ct.tests.length) {
      out.tests = ct.tests.map(t => {
        const test = trimObject(t) || {};
        if ('parameters' in test) test.parameters = smartParse(test.parameters);
        if ('result' in test) test.result = smartParse(test.result);
        return test;
      });
    }
    if (ct.references.length) out.references = ct.references.map(r => trimObject(r) || {});
    if (ct.notes.length) out.notes = ct.notes.map(n => trimObject(n) || {});
    if (ct.chitchat.length) out.chitchat = ct.chitchat.map(c => trimObject(c) || {});
    return out;
  }

  function serializeDocument(doc) {
    const out = {
      cryptml_version: doc.cryptml_version,
      ciphertexts: doc.ciphertexts.map(ct => serializeCiphertext(ct, doc.defaults)),
    };
    if (doc.title) out.title = doc.title;
    if (JSON.stringify(doc.defaults) !== JSON.stringify(DEFAULT_SETTINGS)) out.defaults = doc.defaults;
    if (doc.references.length) out.references = doc.references.map(r => trimObject(r) || {});
    if (doc.notes.length) out.notes = doc.notes.map(n => trimObject(n) || {});
    if (doc.chitchat.length) out.chitchat = doc.chitchat.map(c => trimObject(c) || {});
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

  const TEST_FIELDS = [
    { key: 'tool', label: 'Tool', type: 'text' },
    { key: 'test_name', label: 'Test name', type: 'text' },
    { key: 'date', label: 'Date', type: 'text' },
    { key: 'parameters', label: 'Parameters (JSON or text)', type: 'textarea' },
    { key: 'result', label: 'Result (JSON or text)', type: 'textarea' },
    { key: 'notes', label: 'Notes', type: 'textarea' },
  ];

  const REFERENCE_FIELDS = [
    { key: 'citation', label: 'Citation', type: 'text' },
    { key: 'url', label: 'URL', type: 'text' },
  ];

  const NOTE_FIELDS = [
    { key: 'title', label: 'Title', type: 'text' },
    { key: 'text', label: 'Text', type: 'textarea' },
  ];

  const CHITCHAT_FIELDS = [
    { key: 'author', label: 'Author', type: 'text' },
    { key: 'date', label: 'Date', type: 'text' },
    { key: 'text', label: 'Text', type: 'textarea' },
  ];

  const ORIGIN_FIELDS = [
    { key: 'date', label: 'Date', type: 'text' },
    { key: 'collector', label: 'Collector', type: 'text' },
    { key: 'method', label: 'Method', type: 'text' },
    { key: 'location', label: 'Location', type: 'text' },
    { key: 'remarks', label: 'Remarks', type: 'textarea' },
  ];

  const SOLUTION_FIELDS = [
    { key: 'plaintext', label: 'Plaintext', type: 'textarea' },
    { key: 'plaintext_charset', label: 'Plaintext charset', type: 'text' },
    { key: 'key', label: 'Key', type: 'text' },
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
    parseDocument,
    serializeDocument,
    SOURCE_FIELDS, HINT_FIELDS, TEST_FIELDS, REFERENCE_FIELDS, NOTE_FIELDS, CHITCHAT_FIELDS,
    ORIGIN_FIELDS, SOLUTION_FIELDS,
    el, buildFieldRow, renderObjectSection, renderRepeatable,
    blankOrigin, blankSolution,
  };
})();
