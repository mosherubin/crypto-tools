"""
STETHOSCOPE test runner.
Usage: python run_tests.py <input.json> [<input.json> ...]
"""

import sys
import ciphertext
import tests.mono_count as mono_count
import tests.compute_ic_mono as compute_ic_mono
import tests.digraphic_ic as digraphic_ic
import tests.trigraphic_ic as trigraphic_ic
import tests.local_roughness as local_roughness
import tests.width_tests as width_tests
import tests.polygraphic_ic as polygraphic_ic
import tests.list_of_repeats as list_of_repeats


def run_file(path: str):
    print(f"=== {path} ===")
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

    # mono_count runs first; its output feeds compute_ic_mono and local_roughness
    mc_result = None
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
            _report('local_roughness', local_roughness.run(ct, mc_result.counts))
    except Exception as e:
        print(f"  [local_roughness] RUNTIME ERROR: {e}")

    try:
        if mc_result is not None:
            _report('width_tests', width_tests.run(ct, mc_result.counts))
    except Exception as e:
        print(f"  [width_tests] RUNTIME ERROR: {e}")

    try:
        _report('polygraphic_ic', polygraphic_ic.run(ct))
    except Exception as e:
        print(f"  [polygraphic_ic] RUNTIME ERROR: {e}")

    try:
        lor_result = list_of_repeats.run(ct)
        _report('list_of_repeats', lor_result)
        print(list_of_repeats.format_output(lor_result))
        print()
    except Exception as e:
        print(f"  [list_of_repeats] RUNTIME ERROR: {e}")

    for label, fn in [
        ('compute_digraphic_ic_overall',  digraphic_ic.run_overall),
        ('compute_digraphic_ic_cut_a',   digraphic_ic.run_cut_a),
        ('compute_digraphic_ic_cut_b',  digraphic_ic.run_cut_b),
        ('compute_trigraphic_ic_overall', trigraphic_ic.run_overall),
        ('compute_trigraphic_ic_cut_A',   trigraphic_ic.run_cut_A),
        ('compute_trigraphic_ic_cut_B',   trigraphic_ic.run_cut_B),
        ('compute_trigraphic_ic_cut_C',   trigraphic_ic.run_cut_C),
    ]:
        try:
            _report(label, fn(ct))
        except Exception as e:
            print(f"  [{label}] RUNTIME ERROR: {e}")

    print()


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
