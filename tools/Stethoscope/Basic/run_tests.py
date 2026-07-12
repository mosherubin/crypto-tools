"""
STETHOSCOPE test runner.
Usage: python run_tests.py <input.json> [<input.json> ...]
"""

import sys
import os
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

import ciphertext
import format_report
import version as _version
import tests.mono_count as mono_count
import tests.compute_ic_mono as compute_ic_mono
import tests.digraphic_ic as digraphic_ic
import tests.trigraphic_ic as trigraphic_ic
import tests.local_roughness as local_roughness
import tests.width_tests as width_tests
import tests.polygraphic_ic as polygraphic_ic
import tests.list_of_repeats as list_of_repeats
import tests.delta_stream as delta_stream


def run_file(path: str):
    print(f"=== {path} ===")
    print(f"  STETHOSCOPE PROGRAM (version {_version.get()})")
    try:
        ct = ciphertext.load(path)
    except Exception as e:
        print(f"  LOAD ERROR: {e}")
        print()
        return

    print(f"  test_case_id  : {ct.test_case_id}")
    print(f"  total_letters : {len(ct.letters)}")
    print(f"  ditscount     : {ct.ditscount}")
    print()

    mc_result = ic_result = lr_result = wt_result = poly_result = lor_result = ds_result = iso_result = None
    dig_overall = dig_cut_a = dig_cut_b = None
    trig_overall = trig_cut_a = trig_cut_b = trig_cut_c = None

    try:
        mc_result = mono_count.run(ct)
        _report('mono_count', mc_result)
    except Exception as e:
        print(f"  [mono_count] RUNTIME ERROR: {e}")

    try:
        if mc_result is not None:
            ic_result = compute_ic_mono.run(ct, mc_result.counts)
            _report('compute_ic_mono', ic_result)
    except Exception as e:
        print(f"  [compute_ic_mono] RUNTIME ERROR: {e}")

    try:
        if mc_result is not None:
            lr_result = local_roughness.run(ct, mc_result.counts)
            _report('local_roughness', lr_result)
    except Exception as e:
        print(f"  [local_roughness] RUNTIME ERROR: {e}")

    try:
        if mc_result is not None:
            wt_result = width_tests.run(ct, mc_result.counts)
            _report('width_tests', wt_result)
    except Exception as e:
        print(f"  [width_tests] RUNTIME ERROR: {e}")

    try:
        poly_result = polygraphic_ic.run(ct)
        _report('polygraphic_ic', poly_result)
    except Exception as e:
        print(f"  [polygraphic_ic] RUNTIME ERROR: {e}")

    try:
        lor_result = list_of_repeats.run(ct)
        _report('list_of_repeats', lor_result)
    except Exception as e:
        print(f"  [list_of_repeats] RUNTIME ERROR: {e}")

    try:
        ds_result = delta_stream.run(ct)
        _report('delta_stream', ds_result)
    except Exception as e:
        print(f"  [delta_stream] RUNTIME ERROR: {e}")

    try:
        iso_result = _find_significant_isomorphs(ct.letters, len(ct.alphabet))
    except Exception as e:
        print(f"  [isomorphs] RUNTIME ERROR: {e}")

    try:
        dig_overall = digraphic_ic.run_overall(ct)
        _report('compute_digraphic_ic_overall', dig_overall)
    except Exception as e:
        print(f"  [compute_digraphic_ic_overall] RUNTIME ERROR: {e}")

    try:
        dig_cut_a = digraphic_ic.run_cut_a(ct)
        _report('compute_digraphic_ic_cut_a', dig_cut_a)
    except Exception as e:
        print(f"  [compute_digraphic_ic_cut_a] RUNTIME ERROR: {e}")

    try:
        dig_cut_b = digraphic_ic.run_cut_b(ct)
        _report('compute_digraphic_ic_cut_b', dig_cut_b)
    except Exception as e:
        print(f"  [compute_digraphic_ic_cut_b] RUNTIME ERROR: {e}")

    try:
        trig_overall = trigraphic_ic.run_overall(ct)
        _report('compute_trigraphic_ic_overall', trig_overall)
    except Exception as e:
        print(f"  [compute_trigraphic_ic_overall] RUNTIME ERROR: {e}")

    try:
        trig_cut_a = trigraphic_ic.run_cut_A(ct)
        _report('compute_trigraphic_ic_cut_A', trig_cut_a)
    except Exception as e:
        print(f"  [compute_trigraphic_ic_cut_A] RUNTIME ERROR: {e}")

    try:
        trig_cut_b = trigraphic_ic.run_cut_B(ct)
        _report('compute_trigraphic_ic_cut_B', trig_cut_b)
    except Exception as e:
        print(f"  [compute_trigraphic_ic_cut_B] RUNTIME ERROR: {e}")

    try:
        trig_cut_c = trigraphic_ic.run_cut_C(ct)
        _report('compute_trigraphic_ic_cut_C', trig_cut_c)
    except Exception as e:
        print(f"  [compute_trigraphic_ic_cut_C] RUNTIME ERROR: {e}")

    print()

    if mc_result is not None:
        try:
            listing = format_report.format_listing(
                ct, mc_result, ic_result,
                dig_overall, dig_cut_a, dig_cut_b,
                trig_overall, trig_cut_a, trig_cut_b, trig_cut_c,
                lr_result, wt_result, poly_result, lor_result, ds_result, iso_result,
            )
            print(listing)
        except Exception as e:
            print(f"  [format_report] RUNTIME ERROR: {e}")
            import traceback; traceback.print_exc()

    if ds_result and ds_result.entries:
        for entry in ds_result.entries:
            try:
                sep = '=' * 80
                delta_ct = ciphertext.create_from_text(
                    entry.stream,
                    charset_pattern=ct.charset,
                    casesensitive=ct.casesensitive,
                    description=f'Delta stream offset={entry.offset}',
                )
                print()
                print(sep)
                print(f'STETHOSCOPE ANALYSIS OF DELTA STREAM  OFFSET {entry.offset:>2}'
                      f'  ALPHABET  {entry.alphabet}')
                print(sep)
                _run_full_listing(delta_ct)
            except Exception as e:
                print(f"  [delta_stream second pass] RUNTIME ERROR: {e}")
                import traceback; traceback.print_exc()

    print()


def _run_full_listing(ct) -> None:
    """Run and print the full STETHOSCOPE suite on ct without fixture validation."""
    mc  = mono_count.run(ct)
    ic  = compute_ic_mono.run(ct, mc.counts)
    lr  = local_roughness.run(ct, mc.counts)
    wt  = width_tests.run(ct, mc.counts)
    poly = polygraphic_ic.run(ct)
    lor  = list_of_repeats.run(ct)
    dig_overall = digraphic_ic.run_overall(ct)
    dig_cut_a   = digraphic_ic.run_cut_a(ct)
    dig_cut_b   = digraphic_ic.run_cut_b(ct)
    trig_overall = trigraphic_ic.run_overall(ct)
    trig_cut_a   = trigraphic_ic.run_cut_A(ct)
    trig_cut_b   = trigraphic_ic.run_cut_B(ct)
    trig_cut_c   = trigraphic_ic.run_cut_C(ct)
    print(format_report.format_listing(
        ct, mc, ic,
        dig_overall, dig_cut_a, dig_cut_b,
        trig_overall, trig_cut_a, trig_cut_b, trig_cut_c,
        lr, wt, poly, lor,
    ))


def _report(name: str, result) -> None:
    if result.passed is None:
        print(f"  [{name}] (no expected results to verify)")
    elif result.passed:
        print(f"  [{name}] PASS")
    else:
        print(f"  [{name}] FAIL")
        for err in result.errors:
            print(f"    {err}")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python run_tests.py <input.json> [<input.json> ...]")
        sys.exit(1)
    for path in sys.argv[1:]:
        run_file(path)
