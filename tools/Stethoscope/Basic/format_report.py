"""
STETHOSCOPE compact listing formatter.

Formats all test results into the STETHOSCOPE printed-listing style.
The 26-line body pairs alphabet character counts in the left margin with
IC tests, digraphic/trigraphic, local roughness, and width-test header.
Width tests, polygraphic IC, and list of repeats follow below.
"""

import sys, os; sys.path.insert(0, os.path.dirname(__file__))

_ISO_MIN_LEN = 4
_ISO_MAX_EXPECTED = 0.5


def format_listing(ct, mc_result, ic_result,
                   dig_overall, dig_cut_a, dig_cut_b,
                   trig_overall, trig_cut_a, trig_cut_b, trig_cut_c,
                   lr_result, wt_result, poly_result, repeats_result,
                   ds_result=None, iso_result=None):
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
    total_dits_line = f'TOTAL {N}  DITS {ct.ditscount}'
    body[0] = ' ' * 51 + 'HITS' + ' ' * 8 + 'HITS'
    body[1] = 'IC TESTS FOR SIGNIFICANCE' + ' ' * 15 + 'TOTAL    OBSERVED    EXPECTED'
    if ic_result:
        body[2] = _ic_row(' MONO',     f'{ic_result.ic:.4f}', ic_result.sigmage,
                          ic_result.total, ic_result.hits_observed,
                          f'{ic_result.hits_expected:>4}')
    if dig_overall:
        body[3] = ' DIGRAPHIC TESTS'
        body[4] = _ic_row('  DIGRAPH', f'{dig_overall.ic:.3f}', dig_overall.sigmage,
                          dig_overall.total, dig_overall.hits_observed,
                          f'{dig_overall.hits_expected:>4}')
    if dig_cut_a:
        body[5] = _ic_row('  CUT A',   f'{dig_cut_a.ic:.3f}', dig_cut_a.sigmage,
                          dig_cut_a.total, dig_cut_a.hits_observed,
                          f'{dig_cut_a.hits_expected:>4}')
    if dig_cut_b:
        body[6] = _ic_row('  CUT B',   f'{dig_cut_b.ic:.3f}', dig_cut_b.sigmage,
                          dig_cut_b.total, dig_cut_b.hits_observed,
                          f'{dig_cut_b.hits_expected:>4}')
    if trig_overall:
        body[7] = ' TRIGRAPHIC TESTS'
        body[8] = _ic_row('  TRIGRAPH', f'{trig_overall.ic:.2f}', trig_overall.sigmage,
                          trig_overall.total, trig_overall.hits_observed,
                          _fmt_exp_float(trig_overall.hits_expected))
    if trig_cut_a:
        body[9]  = _ic_row('  CUT A',  f'{trig_cut_a.ic:.2f}', trig_cut_a.sigmage,
                           trig_cut_a.total, trig_cut_a.hits_observed,
                           _fmt_exp_float(trig_cut_a.hits_expected))
    if trig_cut_b:
        body[10] = _ic_row('  CUT B',  f'{trig_cut_b.ic:.2f}', trig_cut_b.sigmage,
                           trig_cut_b.total, trig_cut_b.hits_observed,
                           _fmt_exp_float(trig_cut_b.hits_expected))
    if trig_cut_c:
        body[11] = _ic_row('  CUT C',  f'{trig_cut_c.ic:.2f}', trig_cut_c.sigmage,
                           trig_cut_c.total, trig_cut_c.hits_observed,
                           _fmt_exp_float(trig_cut_c.hits_expected))
    if lr_entries:
        body[12] = f'LOCAL ROUGHNESS  OFFSETS 1 TO {max_offset}'
        body[13] = ('OFF  OBS  EXP  SIGMAGE | '
                    'OFF  OBS  EXP  SIGMAGE | '
                    'OFF  OBS  EXP  SIGMAGE')
        for i in range(11):
            parts = []
            for col in range(3):
                off = i + 1 + col * 11
                e = entry_by_offset.get(off)
                if e:
                    parts.append(f'{off:>3}{e.observed:>5}{e.expected:>5}{e.sigmage:9.1f}')
                else:
                    parts.append(' ' * 22)
            body[14 + i] = ' | '.join(parts)
    body[25] = 'WIDTH TESTS  2 TO 51  INCLUDING NO. OF COMPARISONS FOR EACH W'

    # Left-margin table: "MONO COUNT" header, then 26 body lines
    out.append('MONO')
    out.append('COUNT')
    out.append(f'{"":24}{total_dits_line}')
    for i, content in enumerate(body):
        if i < len(alphabet):
            ch = alphabet[i]
            left = f'{ch} {counts.get(ch, 0):>5}'
        else:
            left = ' ' * 7
        out.append(f'{left}   {content}')

    # Width tests (2 columns: w=2-26 left, w=27-51 right)
    if wt_result and wt_result.entries:
        wt_hdr = f'{"W":>2}  {"HITS":>5}  {"COMPS":>6}  {"AVG IC":>6}  {"SIGMAGE":>7}'
        left_entries  = wt_result.entries[:25]
        right_entries = wt_result.entries[25:]
        has_right = len(right_entries) > 0
        out.append(f'{"":7}   {wt_hdr}' + (f' | {wt_hdr}' if has_right else ''))
        for idx, l_e in enumerate(left_entries):
            r_e = right_entries[idx] if idx < len(right_entries) else None
            row = f'{"":7}   {_wt_row(l_e)}'
            if r_e is not None:
                row += f' | {_wt_row(r_e)}'
            out.append(row)

    # Polygraphic IC
    if poly_result and poly_result.entries:
        out.append('')
        out.append('POLYGRAPHIC HITS AND IC')
        out.append(f'{"LENGTH":>6}  {"TOTAL":>5}  {"OBSERVED":>8}  '
                   f'{"EXPECTED":>8}  {"IC":>10}  {"SIGMAGE":>7}')
        for e in poly_result.entries:
            out.append(f'{e.length:>6}  {e.total:>5}  {e.observed:>8}  '
                       f'{e.expected:>8.2f}  {e.ic:>10}  {e.sigmage:>7}')

    # List of repeats
    if repeats_result:
        out.append('')
        out.append('LIST OF HITS OF LENGTH 4 OR LONGER')
        out.append(f'{"LENGTH":>6}  {"POSITION":>8}  {"OFFSET":>6}    REPEATED TEXT')
        for r in repeats_result.repeats:
            out.append(f'{r.length:>6}  {r.position:>8}  {r.offset:>6}    '
                       + '  '.join(r.text.lower()))
        remaining = repeats_result.total_found - len(repeats_result.repeats)
        if remaining > 0:
            out.append(f'MORE ({remaining} remaining)')

    # Significant isomorphs
    if iso_result is not None:
        out.append('')
        out.append(_format_iso_section(iso_result))

    # Delta stream
    if ds_result and ds_result.entries:
        out.append('')
        out.append('DELTA STREAM')
        for e in ds_result.entries:
            out.append(f'OFFSET {e.offset:>2}  ALPHABET  {e.alphabet}')
            groups = [e.stream[i:i + 5] for i in range(0, len(e.stream), 5)]
            rows = [' '.join(groups[i:i + 10]) for i in range(0, len(groups), 10)]
            for row in rows:
                out.append(row)

    return '\n'.join(out)


def _format_iso_section(iso_pairs):
    lines = [f'SIGNIFICANT ISOMORPHS  (minimum length {_ISO_MIN_LEN}, maximum expected {_ISO_MAX_EXPECTED})']
    lines.append(f'{"MSG A":>6} {"MSG B":>6} {"POS A":>6} {"POS B":>6} {"LEN":>4} {"EXPECTED":>12}   STRINGS')
    sorted_pairs = sorted(iso_pairs, key=lambda r: r[1].expected_occurrences)
    for i, (candidate, significance) in enumerate(sorted_pairs):
        prefix = (f'{candidate.message_a + 1:>6} {candidate.message_b + 1:>6} '
                  f'{candidate.position_a + 1:>6} {candidate.position_b + 1:>6} '
                  f'{candidate.length:>4} {significance.expected_occurrences:>12.4f}   ')
        lines.append(prefix + candidate.text_a)
        lines.append(' ' * len(prefix) + candidate.text_b)
        if i < len(sorted_pairs) - 1:
            lines.append('')
    if not sorted_pairs:
        lines.append('(none found)')
    else:
        lines.append('')
        lines.append(f'Total significant isomorphs found: {len(sorted_pairs)}')
    return '\n'.join(lines)


def _ic_row(label, ic_str, sigmage, N, obs, exp_str):
    pad = ' ' * max(0, 8 - len(ic_str))
    return f'{label:<13}IC  {ic_str}{pad}SIGMAGE {sigmage:7.1f} {N:4d}    {obs:8}    {exp_str}'


def _fmt_exp_float(val, dp=2):
    s = f'{val:.{dp}f}'
    dot = s.index('.')
    return f'{s[:dot]:>4}{s[dot:]}'


def _wt_row(e):
    return (f'{e.width:>2}  {e.hits:>5}  {e.comparisons:>6}  '
            f'{e.average_ic:6.3f}  {e.sigmage:7.2f}')
