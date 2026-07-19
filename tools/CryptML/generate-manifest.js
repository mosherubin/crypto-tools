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
const { validate } = require('../../docs/js/cryptml-editor.js');

const INPUT_DIR = path.join(__dirname, 'input');
const MANIFEST_PATH = path.join(INPUT_DIR, 'index.json');
const EXCLUDED = new Set(['template.cryptml']);

function main() {
  const files = fs.readdirSync(INPUT_DIR)
    .filter(f => f.endsWith('.cryptml') && !EXCLUDED.has(f))
    .sort();

  const entries = [];
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
    entries.push({
      filename,
      title: data.title || '',
      ciphertext_count: data.ciphertexts.length,
    });
  }

  if (errors.length) {
    console.error(`${errors.length} error(s) found -- manifest NOT written:`);
    for (const e of errors) console.error(' -', e);
    process.exit(1);
  }

  const manifest = { generated: new Date().toISOString(), files: entries };
  fs.writeFileSync(MANIFEST_PATH, JSON.stringify(manifest, null, 2) + '\n', 'utf-8');
  console.log(`Wrote ${MANIFEST_PATH} (${entries.length} file(s)).`);
}

main();
