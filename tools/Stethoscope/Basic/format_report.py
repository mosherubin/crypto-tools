"""
STETHOSCOPE compact listing formatter.

Formats all test results into the STETHOSCOPE printed-listing style.
The 26-line body pairs alphabet character counts in the left margin with
IC tests, digraphic/trigraphic, local roughness, and width-test header.
Width tests, polygraphic IC, and list of repeats follow below.
"""

import sys, os; sys.path.insert(0, os.path.dirname(__file__))


def format_listing(ct, mc_result, ic_result,
                   dig_overall, dig_cut_a, dig_cut_b,
                   trig_overall, trig_cut_a, trig_cut_b, trig_cut_c,
                   lr_result, wt_result, poly_result, repeats_result):
    out = []
    alphabet = ct.alphabet
    counts = mc_result.counts
    N = len(ct.letters)

    lr_entries = lr_result.entries if lr_result else []
    max_offset = lr_entries[-1].offset if lr_entries else 0
    entry_by_offset = {e.offset: e for e in lr_entries}

    # 26 fixed-position test body lines (indices 0-25 = lines a-z)
    # Line 0 carries TOTAL/DITS; line 1 carries IC TESTS header.
    body = [''] * 26
    body[0]  = f'TOTAL {N}  DITS {ct.ditscount}'
    body[1]  = 'IC TESTS FOR SIGNIFICANCE    TOTAL  OBSERVED  EXPECTED'
    if ic_result:
        body[2]  = (f'MONO IC {ic_result.ic:.4f}  SIGMAGE  {ic_result.sigmage}  '
                    f'{ic_result.total}  {ic_result.hits_observed}  {ic_result.hits_expected}')
    if dig_overall:
        body[3]  = 'DIGRAPHIC TESTS'
        body[4]  = _dig_row('DIGRAPH', dig_overall)
    if dig_cut_a:
        body[5]  = _dig_row('CUT A', dig_cut_a)
    if dig_cut_b:
        body[6]  = _dig_row('CUT B', dig_cut_b)
    if trig_overall:
        body[7]  = 'TRIGRAPHIC TESTS'
        body[8]  = _trig_row('TRIGRAPH', trig_overall)
    if trig_cut_a:
        body[9]  = _trig_row('CUT A', trig_cut_a)
    if trig_cut_b:
        body[10] = _trig_row('CUT B', trig_cut_b)
    if trig_cut_c:
        body[11] = _trig_row('CUT C', trig_cut_c)
    if lr_entries:
        body[12] = f'LOCAL ROUGHNESS  OFFSETS 1 TO {max_offset}'
        body[13] = ('OFF  OBS  EXP  SIGMAGE    '
                    'OFF  OBS  EXP  SIGMAGE    '
                    'OFF  OBS  EXP  SIGMAGE')
        for i in range(11):
            parts = []
            for col in range(3):
                off = i + 1 + col * 11
                e = entry_by_offset.get(off)
                if e:
                    parts.append(f'{off:>2}  {e.observed:>3}  {e.expected:>3}  {e.sigmage:>4}')
                else:
                    parts.append(' ' * 17)
            body[14 + i] = '    '.join(parts)
    body[25] = 'WIDTH TESTS  2 TO 51  INCLUDING NO. OF COMPARISONS FOR EACH W'

    # Left-margin table: "MONO COUNT" header, then 26 body lines
    out.append('MONO COUNT')
    for i, content in enumerate(body):
        if i < len(alphabet):
            ch = alphabet[i]
            left = f'{ch}  {counts.get(ch, 0):>3}'
        else:
            left = ' ' * 6
        out.append(f'{left}    {content}')

    # Width tests (2 columns: w=2-26 left, w=27-51 right)
    if wt_result and wt_result.entries:
        wt_hdr = f'{"W":>2}  {"HITS":>5}  {"COMPS":>6}  {"AVG IC":>6}  {"SIGMAGE":>7}'
        out.append(f'{"":6}    {wt_hdr}    {wt_hdr}')
        for idx in range(25):
            l_e = wt_result.entries[idx]       # w = 2..26
            r_e = wt_result.entries[idx + 25]  # w = 27..51
            out.append(f'{"":6}    {_wt_row(l_e)}    {_wt_row(r_e)}')

    # Polygraphic IC
    if poly_result and poly_result.entries:
        out.append('')
        out.append('POLYGRAPHIC HITS AND IC')
        out.append(f'{"LENGTH":>6}  {"TOTAL":>5}  {"OBSERVED":>8}  '
                   f'{"EXPECTED":>8}  {"IC":>10}  {"SIGMAGE":>7}')
        for e in poly_result.entries:
            out.append(f'{e.length:>6}  {e.total:>5}  {e.observed:>8}  '
                       f'{e.expected:>8}  {e.ic:>10}  {e.sigmage:>7}')

    # List of repeats
    if repeats_result:
        out.append('')
        out.append('LIST OF HITS OF LENGTH 4 OR LONGER')
        out.append(f'{"LENGTH":>6}  {"POSITION":>8}  {"OFFSET":>6}  REPEATED TEXT')
        for r in repeats_result.repeats:
            out.append(f'{r.length:>6}  {r.position:>8}  {r.offset:>6}  '
                       + '  '.join(r.text.upper()))
        remaining = repeats_result.total_found - len(repeats_result.repeats)
        if remaining > 0:
            out.append(f'MORE ({remaining} remaining)')

    return '\n'.join(out)


def _dig_row(label, r):
    return (f'{label}  IC  {r.ic:.3f}  SIGMAGE  {r.sigmage}  '
            f'{r.total}  {r.hits_observed}  {r.hits_expected}')


def _trig_row(label, r):
    return (f'{label}  IC  {r.ic:.2f}  SIGMAGE  {r.sigmage}  '
            f'{r.total}  {r.hits_observed}  {r.hits_expected:.2f}')


def _wt_row(e):
    return (f'{e.width:>2}  {e.hits:>5}  {e.comparisons:>6}  '
            f'{e.average_ic:6.3f}  {e.sigmage:7.2f}')
