// Shared JS port of tools/Library/reconstruction_matrix.py.
// Only the functions actually used by the browser-based tool ports are
// included here; port additional functions from the Python library as
// needed by future tools.
//
// Loaded as a plain (non-module) script via <script src="js/reconstruction-matrix.js">
// so that tool pages work when opened directly from disk (file://), not just
// when served over HTTP. Everything shared is attached to the single global
// `ReconstructionMatrix` namespace at the bottom of this file.

(function (global) {

class MatrixContradiction extends Error {}

function parseAndValidate(lines) {
  const rows = [];
  const seenNames = new Set();
  let expectedLength = null;

  for (const raw of lines) {
    const stripped = raw.trim();
    if (!stripped) continue;
    if (stripped.startsWith('#')) continue;

    const parts = stripped.split(/\s+/);
    if (parts.length !== 2) {
      throw new Error(`Each non-blank line must have exactly two whitespace-delimited tokens (name + alphabet); got: '${stripped}'`);
    }

    const [name, alphabetRaw] = parts;
    const alphabet = alphabetRaw.toUpperCase();

    for (const ch of alphabet) {
      if (ch !== '.' && !(ch >= 'A' && ch <= 'Z')) {
        throw new Error(`Row '${name}': alphabet contains invalid character '${ch}'; only A-Z and '.' are allowed.`);
      }
    }

    const seenLetters = new Set();
    for (const ch of alphabet) {
      if (ch === '.') continue;
      if (seenLetters.has(ch)) {
        throw new Error(`Row '${name}': letter '${ch}' appears more than once.`);
      }
      seenLetters.add(ch);
    }

    if (expectedLength === null) {
      expectedLength = alphabet.length;
    } else if (alphabet.length !== expectedLength) {
      throw new Error(`Row '${name}': alphabet length ${alphabet.length} does not match the expected length ${expectedLength} (set by the first row).`);
    }

    if (seenNames.has(name)) {
      throw new Error(`Duplicate row name: '${name}'.`);
    }
    seenNames.add(name);

    rows.push([name, alphabet]);
  }

  if (rows.length === 0) {
    throw new Error('Input contains no valid data rows.');
  }
  return rows;
}

function validateMatrix(rows) {
  const nonZeroRows = rows.filter(([name]) => name !== '0');
  const n = nonZeroRows.length;
  for (let i = 0; i < n; i++) {
    const [nameA, alphaA] = nonZeroRows[i];
    for (let j = i + 1; j < n; j++) {
      const [nameB, alphaB] = nonZeroRows[j];
      let anyMatch = false, anyMismatch = false;
      for (let col = 0; col < alphaA.length; col++) {
        const la = alphaA[col], lb = alphaB[col];
        if (la === '.' || la === '*' || lb === '.' || lb === '*') continue;
        if (la === lb) anyMatch = true; else anyMismatch = true;
      }
      if (anyMatch && anyMismatch) {
        return { ok: false, reason: `The common letters between lines '${nameA}' and '${nameB}' must be identical, but they are not.` };
      }
    }
  }
  return { ok: true, reason: null };
}

function validateK3Matrix(rows, isK3) {
  if (!isK3) return { ok: true, reason: null };
  const nameToAlpha = new Map(rows);
  if (!nameToAlpha.has('0')) return { ok: true, reason: null };
  const row0 = nameToAlpha.get('0');
  for (const [name, alpha] of rows) {
    if (name === '0') continue;
    let anyMatch = false, anyMismatch = false;
    for (let col = 0; col < alpha.length; col++) {
      const letter = alpha[col];
      if (letter === '.' || letter === '*') continue;
      if (letter === row0[col]) anyMatch = true; else anyMismatch = true;
    }
    if (anyMatch && anyMismatch) {
      return { ok: false, reason: `All letters in line '${name}' that are known should be identical to line '0' but are not.` };
    }
  }
  return { ok: true, reason: null };
}

function printMatrix(rows) {
  const maxNameLen = Math.max(...rows.map(([name]) => name.length));
  return rows.map(([name, alpha]) => `${name.padEnd(maxNameLen)}  ${alpha}`).join('\n');
}

function cornerStr(corner) {
  const [letter, rowName, col1based] = corner;
  return `${letter}(${rowName}-${col1based})`;
}

function rectStr(rect) {
  return rect.map(cornerStr).join(':');
}

function addRectGeometry(topName, topAlpha, botName, botAlpha, col1, col2, rectangles, rectIndex, rectGeometries) {
  const geom = `${topName} ${botName} ${col1} ${col2}`;
  if (rectGeometries.has(geom)) return;
  rectGeometries.add(geom);

  const tlCh = topAlpha[col1], trCh = topAlpha[col2];
  const blCh = botAlpha[col1], brCh = botAlpha[col2];
  const pos1 = col1 + 1, pos2 = col2 + 1;

  const tl = [tlCh, topName, pos1];
  const tr = [trCh, topName, pos2];
  const bl = [blCh, botName, pos1];
  const br = [brCh, botName, pos2];

  const orderings = [
    [tl, tr, bl, br], [tl, bl, tr, br], [tr, tl, br, bl], [bl, tl, br, tr],
    [bl, br, tl, tr], [tr, br, tl, bl], [br, bl, tr, tl], [br, tr, bl, tl],
  ];

  for (const rect of orderings) {
    const offset = rectangles.length;
    rectangles.push(rect);
    const seq = rect.map(c => c[0]);
    for (let ki = 0; ki < 4; ki++) {
      const key = seq.map((ch, j) => (j === ki ? '.' : ch)).join('');
      if (!rectIndex.has(key)) rectIndex.set(key, []);
      rectIndex.get(key).push(offset);
    }
  }
}

function findRectangles(rows, isK3) {
  const activeRows = isK3 ? rows : rows.filter(([name]) => name !== '0');
  const rectangles = [];
  const rectIndex = new Map();
  const rectGeometries = new Set();
  const numRows = activeRows.length;

  for (let topIdx = 0; topIdx < numRows - 1; topIdx++) {
    const [topName, topAlpha] = activeRows[topIdx];
    const topPositions = [];
    for (let i = 0; i < topAlpha.length; i++) if (topAlpha[i] !== '.') topPositions.push(i);

    for (let a = 0; a < topPositions.length; a++) {
      const col1 = topPositions[a];
      for (let b = a + 1; b < topPositions.length; b++) {
        const col2 = topPositions[b];
        for (let botIdx = topIdx + 1; botIdx < numRows; botIdx++) {
          const [botName, botAlpha] = activeRows[botIdx];
          if (botAlpha[col1] === '.' || botAlpha[col2] === '.') continue;
          addRectGeometry(topName, topAlpha, botName, botAlpha, col1, col2, rectangles, rectIndex, rectGeometries);
        }
      }
    }
  }

  return { rectangles, rectIndex };
}

function findIncompleteRectangles(rows, isK3) {
  const activeRows = isK3 ? rows : rows.filter(([name]) => name !== '0');
  const incomplete = [];
  const numRows = activeRows.length;
  const n = activeRows.length > 0 ? activeRows[0][1].length : 0;

  for (let topIdx = 0; topIdx < numRows - 1; topIdx++) {
    const [topName, topAlpha] = activeRows[topIdx];
    for (let botIdx = topIdx + 1; botIdx < numRows; botIdx++) {
      const [botName, botAlpha] = activeRows[botIdx];

      for (let col1 = 0; col1 < n; col1++) {
        const tlCh = topAlpha[col1];
        const tlKnown = tlCh !== '.';

        for (let col2 = col1 + 1; col2 < n; col2++) {
          const trCh = topAlpha[col2];
          const trKnown = trCh !== '.';
          const blCh = botAlpha[col1];
          const blKnown = blCh !== '.';
          const brCh = botAlpha[col2];
          const brKnown = brCh !== '.';

          const knownCount = [tlKnown, trKnown, blKnown, brKnown].filter(Boolean).length;
          if (knownCount !== 3) continue;

          const pos1 = col1 + 1, pos2 = col2 + 1;
          const tl = [tlKnown ? tlCh : '?', topName, pos1];
          const tr = [trKnown ? trCh : '?', topName, pos2];
          const bl = [blKnown ? blCh : '?', botName, pos1];
          const br = [brKnown ? brCh : '?', botName, pos2];

          incomplete.push([tl, tr, bl, br]);
          incomplete.push([tl, bl, tr, br]);
          incomplete.push([tr, tl, br, bl]);
          incomplete.push([bl, tl, br, tr]);
          incomplete.push([bl, br, tl, tr]);
          incomplete.push([tr, br, tl, bl]);
          incomplete.push([br, bl, tr, tl]);
          incomplete.push([br, tr, bl, tl]);
        }
      }
    }
  }

  return incomplete;
}

function normalizeMatrix(rows, isK3) {
  if (!isK3) return { ok: true, rows };

  while (true) {
    const nameToAlpha = new Map(rows.map(([name, alpha]) => [name, alpha.split('')]));
    const nonZeroNames = rows.map(([name]) => name).filter(name => name !== '0');
    let changed = false;

    for (let i = 0; i < nonZeroNames.length; i++) {
      const nameA = nonZeroNames[i];
      for (let j = i + 1; j < nonZeroNames.length; j++) {
        const nameB = nonZeroNames[j];
        const alphaA = nameToAlpha.get(nameA);
        const alphaB = nameToAlpha.get(nameB);
        const nCols = alphaA.length;

        let anyMatch = false;
        for (let col = 0; col < nCols; col++) {
          if (alphaA[col] !== '.' && alphaA[col] !== '*' && alphaA[col] === alphaB[col]) {
            anyMatch = true;
            break;
          }
        }
        if (!anyMatch) continue;

        for (let col = 0; col < nCols; col++) {
          const la = alphaA[col], lb = alphaB[col];
          if (la !== '.' && la !== '*' && lb !== '.' && lb !== '*' && la !== lb) {
            return {
              ok: false,
              reason: `Contradiction in normalize_matrix: lines '${nameA}' and '${nameB}' are equivalent (share a common letter) but differ at position ${col + 1} (line '${nameA}' has '${la}', line '${nameB}' has '${lb}').`,
            };
          }
        }

        for (let col = 0; col < nCols; col++) {
          const la = alphaA[col], lb = alphaB[col];
          if (la !== '.' && la !== '*' && lb === '.') {
            nameToAlpha.get(nameB)[col] = la;
            changed = true;
          } else if (lb !== '.' && lb !== '*' && la === '.') {
            nameToAlpha.get(nameA)[col] = lb;
            changed = true;
          }
        }
      }
    }

    rows = rows.map(([name]) => [name, nameToAlpha.get(name).join('')]);
    if (!changed) break;
  }

  return { ok: true, rows };
}

function applyIndirectSymmetry(rows, rectangles, rectIndex, incomplete, allowRowDups, allowColDups, isK3) {
  const norm = normalizeMatrix(rows, isK3);
  if (!norm.ok) {
    throw new MatrixContradiction(`NORMALIZATION CONTRADICTION: ${norm.reason}`);
  }
  rows = norm.rows;

  const nameToIdx = new Map(rows.map(([name], i) => [name, i]));
  const alphabets = rows.map(([, alpha]) => alpha.split(''));

  const inferred = new Map(); // `${rowName} ${col}` -> letter
  let newLetters = 0;
  const outputLines = [];

  for (const incRect of incomplete) {
    const unknownIdx = incRect.findIndex(c => c[0] === '?');
    if (unknownIdx === -1) continue;

    const unknownRowName = incRect[unknownIdx][1];
    const unknownCol = incRect[unknownIdx][2] - 1;
    const unknownRef = `(${unknownRowName}-${unknownCol + 1})`;

    const cellKey = `${unknownRowName} ${unknownCol}`;
    if (inferred.has(cellKey)) continue;

    const lookupKey = incRect.map(c => (c[0] === '?' ? '.' : c[0])).join('');

    let matchedRect = null;
    let inferredLetter = null;
    const offsets = rectIndex.get(lookupKey);
    if (offsets && offsets.length) {
      matchedRect = rectangles[offsets[0]];
      inferredLetter = matchedRect[unknownIdx][0];
    }
    if (matchedRect === null) continue;

    const rowIdx = nameToIdx.get(unknownRowName);
    const current = alphabets[rowIdx][unknownCol];

    if (current !== '.' && current !== '*') {
      if (current !== inferredLetter) {
        outputLines.push(`CONFLICT at ${unknownRef}: existing='${current}' inferred='${inferredLetter}' from ${rectStr(matchedRect)} -> ${rectStr(incRect)}`);
        alphabets[rowIdx][unknownCol] = '*';
        inferred.set(cellKey, '*');
        newLetters++;
      }
      continue;
    }
    if (current === '*') continue;

    const rowLetters = alphabets[rowIdx];
    if (rowLetters.includes(inferredLetter)) {
      if (!allowRowDups) {
        const dupCol = rowLetters.indexOf(inferredLetter);
        throw new MatrixContradiction(
          `DUPLICATION ERROR (row): inserting '${inferredLetter}' at ${unknownRef} would duplicate the letter already at 1-based col ${dupCol + 1} in row '${unknownRowName}'.\n` +
          `  Complete:   ${rectStr(matchedRect)}\n  Incomplete: ${rectStr(incRect)}`);
      }
      continue; // skip: would create a row duplicate
    }

    let skipColDup = false;
    for (let chkRowIdx = 0; chkRowIdx < alphabets.length; chkRowIdx++) {
      const chkRowName = rows[chkRowIdx][0];
      if (alphabets[chkRowIdx][unknownCol] === inferredLetter && chkRowName !== '0') {
        if (!allowColDups) {
          throw new MatrixContradiction(
            `DUPLICATION ERROR (column): inserting '${inferredLetter}' at ${unknownRef} would duplicate the letter already at row '${chkRowName}', 1-based col ${unknownCol + 1}.\n` +
            `  Complete:   ${rectStr(matchedRect)}\n  Incomplete: ${rectStr(incRect)}`);
        }
        skipColDup = true;
        break;
      }
    }
    if (skipColDup) continue; // skip: would create a column duplicate

    if (isK3 && nameToIdx.has('0')) {
      const row0Alpha = alphabets[nameToIdx.get('0')];
      const line0LetterAtCol = row0Alpha[unknownCol];
      if (inferredLetter === line0LetterAtCol) {
        const targetAlpha = alphabets[rowIdx];
        let mismatchFound = false;
        for (let colI = 0; colI < targetAlpha.length; colI++) {
          const letter = targetAlpha[colI];
          if (letter === '.' || letter === '*') continue;
          if (colI === unknownCol) continue;
          if (letter !== row0Alpha[colI]) { mismatchFound = true; break; }
        }
        if (mismatchFound) {
          throw new MatrixContradiction(
            `K3 ERROR at ${unknownRef}: inferred '${inferredLetter}' matches line '0' at col ${unknownCol + 1} but other letters in row '${unknownRowName}' do not all match line '0'.\n` +
            `  Complete:   ${rectStr(matchedRect)}\n  Incomplete: ${rectStr(incRect)}`);
        }
      }
    }

    if (isK3 && nameToIdx.has('0')) {
      const row0Alpha = alphabets[nameToIdx.get('0')];
      const line0LetterAtCol = row0Alpha[unknownCol];
      if (inferredLetter !== line0LetterAtCol) {
        const targetAlpha = alphabets[rowIdx];
        let matchFound = false;
        for (let colI = 0; colI < targetAlpha.length; colI++) {
          const letter = targetAlpha[colI];
          if (letter === '.' || letter === '*') continue;
          if (colI === unknownCol) continue;
          if (letter === row0Alpha[colI]) { matchFound = true; break; }
        }
        if (matchFound) {
          throw new MatrixContradiction(
            `K3 ERROR at ${unknownRef}: inferred '${inferredLetter}' does not match line '0' letter '${line0LetterAtCol}' at col ${unknownCol + 1}, but other letters in row '${unknownRowName}' are identical to line '0' -- the inferred letter should be identical but is not.\n` +
            `  Complete:   ${rectStr(matchedRect)}\n  Incomplete: ${rectStr(incRect)}`);
        }
      }
    }

    outputLines.push(`${rectStr(matchedRect)} -> ${rectStr(incRect)} -> ${inferredLetter}(${unknownRowName}-${unknownCol + 1})`);
    alphabets[rowIdx][unknownCol] = inferredLetter;
    inferred.set(cellKey, inferredLetter);
    newLetters++;
  }

  const updatedRows = rows.map(([name], i) => [name, alphabets[i].join('')]);
  return { rows: updatedRows, newLetters, outputLines };
}

// ---------------------------------------------------------------------------
// Tetragram validity check
// ---------------------------------------------------------------------------

function tetragramIndex(chars) {
  return chars[0] * 17576 + chars[1] * 676 + chars[2] * 26 + chars[3];
}

// Mirrors is_tetragram_valid from the Python library. `cache` is a plain
// object owned by the caller; pass the same object on every call to reuse
// wildcard-expansion results. Requires global.TETRAGRAM_FREQUENCY_DATA
// (loaded via js/tetragram-data.js) to already be set.
function isTetragramValid(tetragram, cache, cutoff = 'A') {
  const data = global.TETRAGRAM_FREQUENCY_DATA;

  tetragram = tetragram.toUpperCase();
  cutoff = cutoff.toUpperCase();

  const dotCount = [...tetragram].filter(ch => ch === '.').length;
  if (dotCount >= 3) return true;

  if (dotCount === 0) {
    const chars = [...tetragram].map(ch => ch.charCodeAt(0) - 65);
    return data[tetragramIndex(chars)] > cutoff;
  }

  const cacheKey = `${tetragram}|${cutoff}`;
  if (cacheKey in cache) return cache[cacheKey];

  const wildcardPositions = [];
  for (let i = 0; i < tetragram.length; i++) if (tetragram[i] === '.') wildcardPositions.push(i);
  const chars = [...tetragram].map(ch => (ch === '.' ? null : ch.charCodeAt(0) - 65));

  const total = 26 ** wildcardPositions.length;
  for (let n = 0; n < total; n++) {
    let rem = n;
    for (const pos of wildcardPositions) {
      chars[pos] = rem % 26;
      rem = Math.floor(rem / 26);
    }
    if (data[tetragramIndex(chars)] > cutoff) {
      cache[cacheKey] = true;
      return true;
    }
  }

  cache[cacheKey] = false;
  return false;
}

function validateColumnConsistency(rows) {
  const nRows = rows.length;
  const nCols = rows[0][1].length;
  for (let i = 0; i < nCols; i++) {
    for (let j = i + 1; j < nCols; j++) {
      let shared = false;
      for (let r = 0; r < nRows; r++) {
        const a = rows[r][1][i], b = rows[r][1][j];
        if (a !== '.' && b !== '.' && a === b) { shared = true; break; }
      }
      if (!shared) continue;
      for (let r = 0; r < nRows; r++) {
        const a = rows[r][1][i], b = rows[r][1][j];
        if (a !== '.' && b !== '.' && a !== b) {
          return { ok: false, col1: i + 1, col2: j + 1, rowName: rows[r][0], letter1: a, letter2: b };
        }
      }
    }
  }
  return { ok: true };
}

function deduplicateColumns(rows) {
  const nRows = rows.length;
  const originalLen = rows[0][1].length;

  const grid = rows.map(([, alpha]) => alpha.split(''));
  // tracks which original 0-based column index each current column came from
  let origIdx = Array.from({ length: originalLen }, (_, i) => i);

  function colHasLetters(c) {
    return grid.some(row => row[c] !== '.');
  }

  function compatible(a, b) {
    for (let r = 0; r < nRows; r++) {
      const ca = grid[r][a], cb = grid[r][b];
      if (ca !== '.' && cb !== '.' && ca !== cb) return false;
    }
    return true;
  }

  function findSharedLetterPair() {
    const nCols = origIdx.length;
    for (let i = 0; i < nCols; i++) {
      for (let j = i + 1; j < nCols; j++) {
        let sharedLetter = false;
        let conflict = false;
        for (let r = 0; r < nRows; r++) {
          const a = grid[r][i], b = grid[r][j];
          if (a !== '.' && b !== '.') {
            if (a === b) sharedLetter = true;
            else { conflict = true; break; }
          }
        }
        if (sharedLetter && !conflict) return [i, j];
      }
    }
    return null;
  }

  function findUniqueCompatiblePair() {
    const nCols = origIdx.length;
    for (let b = 0; b < nCols; b++) {
      if (!colHasLetters(b)) continue;
      let partner = -1;
      let count = 0;
      for (let a = 0; a < nCols; a++) {
        if (a === b || !colHasLetters(a)) continue;
        if (compatible(a, b)) {
          partner = a;
          count++;
          if (count > 1) break;
        }
      }
      if (count === 1) return [partner, b];
    }
    return null;
  }

  function mergeCols(i, j) {
    for (let r = 0; r < nRows; r++) {
      const a = grid[r][i], b = grid[r][j];
      if (a !== '.' && b !== '.' && a !== b) {
        throw new Error(
          `Deduplication conflict: column ${origIdx[i] + 1} has '${a}' but column ${origIdx[j] + 1} has '${b}' in row '${rows[r][0]}'`
        );
      }
    }
    for (let r = 0; r < nRows; r++) {
      if (grid[r][j] !== '.' && grid[r][i] === '.') grid[r][i] = grid[r][j];
    }
    for (let r = 0; r < nRows; r++) grid[r].splice(j, 1);
    origIdx.splice(j, 1);
  }

  while (true) {
    const pair = findSharedLetterPair();
    if (pair) { mergeCols(pair[0], pair[1]); continue; }

    const uniquePair = findUniqueCompatiblePair();
    if (uniquePair) { mergeCols(uniquePair[0], uniquePair[1]); continue; }

    break;
  }

  const keptSet = new Set(origIdx);
  const dropped = originalLen - origIdx.length;
  const droppedPositions = [];
  for (let c = 0; c < originalLen; c++) if (!keptSet.has(c)) droppedPositions.push(c + 1);

  const dedupRows = rows.map(([name], r) => [name, grid[r].join('')]);
  return { rows: dedupRows, dropped, droppedPositions };
}

global.ReconstructionMatrix = {
  MatrixContradiction,
  isTetragramValid,
  parseAndValidate,
  validateMatrix,
  validateK3Matrix,
  printMatrix,
  rectStr,
  findRectangles,
  findIncompleteRectangles,
  normalizeMatrix,
  applyIndirectSymmetry,
  deduplicateColumns,
  validateColumnConsistency,
};

})(window);
