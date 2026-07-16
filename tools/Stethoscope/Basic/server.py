"""
STETHOSCOPE web server.
Serves an HTML frontend for running STETHOSCOPE cryptanalytic tests.

Usage:  python server.py [port]     (default port 5000)
        Then open http://localhost:5000/ in a browser.
"""

import sys
import os
import traceback

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'Library'))
from isomorph_search import locate_isomorphs as _locate_isomorphs
from isomorph_evaluation import evaluate_isomorph as _evaluate_isomorph

_ISO_MIN_LEN = 4
_ISO_MAX_EXPECTED = 0.5

def _find_significant_isomorphs(letters: str, alphabet_size: int) -> list:
    candidates = _locate_isomorphs([letters], _ISO_MIN_LEN)
    results = []
    for c in candidates:
        sig = _evaluate_isomorph(c.text_a, alphabet_size, len(letters), len(letters),
                                 True, _ISO_MAX_EXPECTED)
        if sig.significant:
            results.append((c, sig))
    return results

from flask import Flask, request, jsonify

import ciphertext as ct_module
import tests.mono_count as mono_count
import tests.compute_ic_mono as compute_ic_mono
import tests.digraphic_ic as digraphic_ic
import tests.trigraphic_ic as trigraphic_ic
import tests.local_roughness as local_roughness
import tests.width_tests as width_tests
import tests.polygraphic_ic as polygraphic_ic
import tests.list_of_repeats as list_of_repeats
import tests.delta_stream as delta_stream
import format_report

app = Flask(__name__)

CHARSET_MAP = {
    '[A-Za-z]':    ('[A-Z]',       False),
    '[0-9]':       ('[0-9]',       True),
    '[A-Za-z0-9]': ('[A-Za-z0-9]', False),
}

_HTML = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>STETHOSCOPE PROGRAM</title>
<style>
  * { box-sizing: border-box; }
  body {
    font-family: Arial, sans-serif;
    max-width: 1400px;
    margin: 0 auto;
    padding: 24px 20px;
    background: #fff;
  }
  h1 {
    text-align: center;
    letter-spacing: 6px;
    font-size: 1.4em;
    margin-bottom: 24px;
  }
  .row {
    display: flex;
    align-items: flex-start;
    margin: 8px 0;
    gap: 12px;
  }
  .lbl {
    min-width: 220px;
    padding-top: 5px;
    font-weight: bold;
    text-align: right;
  }
  .ctrl { flex: 1; }
  textarea#ciphertext {
    width: 100%;
    height: 110px;
    resize: both;
    font-family: monospace;
    font-size: 0.9em;
  }
  input#description { width: 100%; }
  #run-btn {
    margin: 14px 0 4px 232px;
    padding: 7px 30px;
    font-size: 1em;
    cursor: pointer;
  }
  #run-btn:disabled { cursor: wait; opacity: 0.6; }
  #output {
    display: block;
    width: 100%;
    height: 680px;
    font-family: monospace;
    font-size: 0.82em;
    line-height: 1.35;
    background: #f6f6f6;
    border: 1px solid #ccc;
    padding: 8px;
    resize: vertical;
    white-space: pre;
    overflow: auto;
    margin-top: 10px;
  }
</style>
</head>
<body>
<h1>STETHOSCOPE PROGRAM <span style="letter-spacing:normal; font-size:0.75em;">(version 0.13)</span></h1>

<div class="row">
  <span class="lbl">Ciphertext:</span>
  <div class="ctrl">
    <textarea id="ciphertext" placeholder="Paste ciphertext here..."></textarea>
  </div>
</div>

<div class="row">
  <span class="lbl">Description (optional):</span>
  <div class="ctrl">
    <input type="text" id="description" />
  </div>
</div>

<div class="row">
  <span class="lbl">Character set:</span>
  <div class="ctrl">
    <select id="charset">
      <option value="[A-Za-z]">[A-Za-z] — 26 characters (default)</option>
      <option value="[0-9]">[0-9] — 10 characters</option>
      <option value="[A-Za-z0-9]">[A-Za-z0-9] — 36 characters</option>
    </select>
  </div>
</div>

<div class="row">
  <span class="lbl"></span>
  <div class="ctrl">
    <label>
      <input type="checkbox" id="display_ct">
      Display ciphertext in output
    </label>
  </div>
</div>

<button id="run-btn" onclick="runTests()">Run</button>

<textarea id="output" readonly></textarea>

<script>
const _MONTHS = ['January','February','March','April','May','June',
                 'July','August','September','October','November','December'];

function runHeader() {
  const n = new Date();
  const dd   = String(n.getDate()).padStart(2, '0');
  const mon  = _MONTHS[n.getMonth()];
  const yyyy = n.getFullYear();
  const hh   = String(n.getHours()).padStart(2, '0');
  const mm   = String(n.getMinutes()).padStart(2, '0');
  const ss   = String(n.getSeconds()).padStart(2, '0');
  return `STETHOSCOPE PROGRAM (version 0.13)  (Moshe Rubin)  Timestamp  ${dd} ${mon} ${yyyy}  -  ${hh}:${mm}:${ss}`;
}

async function runTests() {
  const btn = document.getElementById('run-btn');
  btn.disabled = true;
  const out = document.getElementById('output');
  out.value = 'Running...';
  try {
    const resp = await fetch('/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ciphertext:        document.getElementById('ciphertext').value,
        description:       document.getElementById('description').value,
        charset:           document.getElementById('charset').value,
        display_ciphertext: document.getElementById('display_ct').checked,
      })
    });
    const data = await resp.json();
    if (data.error) {
      out.value = 'ERROR: ' + data.error;
    } else {
      const desc       = document.getElementById('description').value.trim();
      const displayCt  = document.getElementById('display_ct').checked;
      const descLine   = desc ? ('Description: ' + desc) : '';
      let text;
      if (displayCt && descLine) {
        const cut  = data.output.indexOf('\\n\\n');
        const ctBlock   = cut >= 0 ? data.output.slice(0, cut)       : data.output;
        const reportBlock = cut >= 0 ? data.output.slice(cut + 2)    : '';
        text = runHeader() + '\\n\\n' + ctBlock + '\\n\\n' + descLine + '\\n\\n' + reportBlock;
      } else {
        text = runHeader() + '\\n\\n';
        if (descLine) text += descLine + '\\n\\n';
        text += data.output;
      }
      out.value = text;
    }
  } catch (e) {
    out.value = 'Network error: ' + e.message;
  }
  btn.disabled = false;
}
</script>
</body>
</html>
"""


@app.route('/')
def index():
    return _HTML


@app.route('/run', methods=['POST'])
def run():
    payload     = request.get_json(force=True)
    raw         = payload.get('ciphertext', '')
    description = payload.get('description', '')
    charset_key = payload.get('charset', '[A-Za-z]')
    display_ct  = payload.get('display_ciphertext', False)
    max_repeats = int(payload.get('max_repeats', 50))
    delta_config = None
    if payload.get('delta_enabled'):
        delta_config = {
            'offset':   int(payload.get('delta_offset', 1)),
            'alphabet': payload.get('delta_alphabet', '').upper(),
        }

    charset_pattern, casesensitive = CHARSET_MAP.get(charset_key, ('[A-Z]', False))

    try:
        ct = ct_module.create_from_text(
            raw,
            charset_pattern=charset_pattern,
            casesensitive=casesensitive,
            description=description,
        )
    except Exception as e:
        return jsonify({'error': str(e)})

    if len(ct.letters) < 4:
        return jsonify({'error': f'Too few cipher characters ({len(ct.letters)}); need at least 4.'})

    try:
        output = _run_suite(ct, display_ct, max_repeats, delta_config,
                            charset_pattern=charset_pattern, casesensitive=casesensitive)
    except Exception:
        return jsonify({'error': traceback.format_exc()})

    return jsonify({'output': output})


def _run_suite(ct, display_ct: bool, max_repeats: int = 50,
               delta_config=None, charset_pattern='[A-Z]', casesensitive=False,
               include_isomorphs: bool = True) -> str:
    parts = []

    if display_ct:
        text = ct.letters
        groups = [text[i:i + 5] for i in range(0, len(text), 5)]
        rows   = [' '.join(groups[i:i + 10]) for i in range(0, len(groups), 10)]
        parts.append('CIPHERTEXT:')
        parts.extend(rows)
        parts.append('')

    mc_result    = mono_count.run(ct)
    ic_result    = compute_ic_mono.run(ct, mc_result.counts)
    lr_result    = local_roughness.run(ct, mc_result.counts)
    wt_result    = width_tests.run(ct, mc_result.counts)
    poly_result  = polygraphic_ic.run(ct)
    lor_result   = list_of_repeats.run(ct, max_repeats)
    dig_overall  = digraphic_ic.run_overall(ct)
    dig_cut_a    = digraphic_ic.run_cut_a(ct)
    dig_cut_b    = digraphic_ic.run_cut_b(ct)
    trig_overall = trigraphic_ic.run_overall(ct)
    trig_cut_a   = trigraphic_ic.run_cut_A(ct)
    trig_cut_b   = trigraphic_ic.run_cut_B(ct)
    trig_cut_c   = trigraphic_ic.run_cut_C(ct)

    iso_result = _find_significant_isomorphs(ct.letters, len(ct.alphabet)) if include_isomorphs else None

    ds_result = None
    if delta_config:
        offset   = delta_config['offset']
        alphabet = delta_config['alphabet']
        N = len(ct.letters)
        if 1 <= offset <= N - 1:
            from tests.delta_stream import DeltaEntry, DeltaResult, compute_stream
            stream = compute_stream(ct.letters, alphabet, offset)
            ds_result = DeltaResult(
                entries=[DeltaEntry(offset=offset, alphabet=alphabet, stream=stream)],
                passed=None,
            )
    else:
        ds_result = delta_stream.run(ct)

    parts.append(format_report.format_listing(
        ct, mc_result, ic_result,
        dig_overall, dig_cut_a, dig_cut_b,
        trig_overall, trig_cut_a, trig_cut_b, trig_cut_c,
        lr_result, wt_result, poly_result, lor_result, ds_result, iso_result,
    ))

    if ds_result and ds_result.entries:
        entry = ds_result.entries[0]
        sep = '=' * 80
        delta_ct = ct_module.create_from_text(
            entry.stream,
            charset_pattern=charset_pattern,
            casesensitive=casesensitive,
            description=f'Delta stream offset={entry.offset}',
        )
        parts.append('')
        parts.append(sep)
        parts.append(f'STETHOSCOPE ANALYSIS OF DELTA STREAM  OFFSET {entry.offset:>2}'
                     f'  ALPHABET  {entry.alphabet}')
        parts.append(sep)
        parts.append(_run_suite(delta_ct, False, max_repeats))

    return '\n'.join(parts)


if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    print(f'STETHOSCOPE server → http://localhost:{port}/')
    app.run(host='0.0.0.0', port=port, debug=False)
