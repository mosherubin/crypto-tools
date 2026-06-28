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
<h1>STETHOSCOPE PROGRAM</h1>

<div class="row">
  <span class="lbl">Ciphertext:</span>
  <div class="ctrl">
    <textarea id="ciphertext" placeholder="Paste ciphertext here…"></textarea>
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
  return `STETHOSCOPE PROGRAM (Moshe Rubin)  Timestamp  ${dd} ${mon} ${yyyy}  -  ${hh}:${mm}:${ss}`;
}

async function runTests() {
  const btn = document.getElementById('run-btn');
  btn.disabled = true;
  const out = document.getElementById('output');
  out.value = 'Running…';
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
    out.value = data.error
      ? ('ERROR: ' + data.error)
      : (runHeader() + '\n\n' + data.output);
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
        output = _run_suite(ct, display_ct)
    except Exception:
        return jsonify({'error': traceback.format_exc()})

    return jsonify({'output': output})


def _run_suite(ct, display_ct: bool) -> str:
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
    lor_result   = list_of_repeats.run(ct)
    dig_overall  = digraphic_ic.run_overall(ct)
    dig_cut_a    = digraphic_ic.run_cut_a(ct)
    dig_cut_b    = digraphic_ic.run_cut_b(ct)
    trig_overall = trigraphic_ic.run_overall(ct)
    trig_cut_a   = trigraphic_ic.run_cut_A(ct)
    trig_cut_b   = trigraphic_ic.run_cut_B(ct)
    trig_cut_c   = trigraphic_ic.run_cut_C(ct)

    parts.append(format_report.format_listing(
        ct, mc_result, ic_result,
        dig_overall, dig_cut_a, dig_cut_b,
        trig_overall, trig_cut_a, trig_cut_b, trig_cut_c,
        lr_result, wt_result, poly_result, lor_result,
    ))
    return '\n'.join(parts)


if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    print(f'STETHOSCOPE server → http://localhost:{port}/')
    app.run(host='0.0.0.0', port=port, debug=False)
