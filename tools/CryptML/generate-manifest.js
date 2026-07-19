#!/usr/bin/env node
/*
 * Regenerates tools/CryptML/input/index.json from the .cryptml files in that
 * directory, so browser tools can discover what's there via
 * raw.githubusercontent.com without ever calling the rate-limited GitHub
 * Contents API. Validates every file first (reusing the same validate()
 * the browser editor and pre-commit hook use) and refuses to write a
 * manifest if any file is broken -- run by the local pre-commit hook and
 * by .github/workflows/cryptml-manifest.yml.
 *
 * Usage: node generate-manifest.js
 * Exit code: 0 on success, 1 if any .cryptml file fails validation.
 */
const fs = require('fs');
const path = require('path');
const { validate, isValidUuid } = require('../../docs/js/cryptml-editor.js');

const INPUT_DIR = path.join(__dirname, 'input');
const MANIFEST_PATH = path.join(INPUT_DIR, 'index.json');
const EXCLUDED = new Set(['template.cryptml']);

function main() {
  const files = fs.readdirSync(INPUT_DIR)
    .filter(f => f.endsWith('.cryptml') && !EXCLUDED.has(f))
    .sort();

  const fileEntries = [];
  const ciphertextEntries = [];
  const uuidOwner = new Map(); // uuid -> filename that first claimed it
  const errors = [];

  for (const filename of files) {
    const text = fs.readFileSync(path.join(INPUT_DIR, filename), 'utf-8');
    let data;
    try {
      data = JSON.parse(text);
    } catch (e) {
      errors.push(`${filename}: invalid JSON -- ${e.message}`);
      continue;
    }
    const fileErrors = validate(data);
    if (fileErrors.length) {
      for (const err of fileErrors) errors.push(`${filename}: ${err}`);
      continue;
    }

    // Schema validation treats cryptml_uuid as optional; membership in this
    // directory requires it -- see "Corpus identity" in docs/cryptml-spec.md.
    if (!isValidUuid(data.cryptml_uuid)) {
      errors.push(`${filename}: missing or invalid cryptml_uuid -- every file under tools/CryptML/input/ must have one (assign it via the Editor's "Prepare for the corpus" action)`);
      continue;
    }
    const uuid = data.cryptml_uuid;
    if (uuidOwner.has(uuid)) {
      errors.push(`${filename}: cryptml_uuid ${uuid} is already used by ${uuidOwner.get(uuid)}`);
      continue;
    }
    uuidOwner.set(uuid, filename);

    fileEntries.push({
      filename,
      uuid,
      title: data.title || '',
      ciphertext_count: data.ciphertexts.length,
    });
    // A lone ciphertext may omit 'id' and default to "1" -- resolve that
    // here too, so the catalog never has an entry with no id.
    for (const ct of data.ciphertexts) {
      const id = ct.id ?? '1';
      ciphertextEntries.push({ uuid, id, filename });
    }
  }

  if (errors.length) {
    console.error(`${errors.length} error(s) found -- manifest NOT written:`);
    for (const e of errors) console.error(' -', e);
    process.exit(1);
  }

  const manifest = { generated: new Date().toISOString(), files: fileEntries, ciphertexts: ciphertextEntries };
  fs.writeFileSync(MANIFEST_PATH, JSON.stringify(manifest, null, 2) + '\n', 'utf-8');
  console.log(`Wrote ${MANIFEST_PATH} (${fileEntries.length} file(s), ${ciphertextEntries.length} ciphertext(s)).`);
}

main();
