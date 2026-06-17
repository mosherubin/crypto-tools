"""
STETHOSCOPE test runner.
Usage: python run_tests.py <input.json> [<input.json> ...]
"""

import sys
import ciphertext
import tests.mono_count as mono_count


TESTS = [
    ('mono_count', mono_count.run),
]


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

    for name, fn in TESTS:
        try:
            result = fn(ct)
        except Exception as e:
            print(f"  [{name}] RUNTIME ERROR: {e}")
            continue

        if result.passed is None:
            print(f"  [{name}] (no expected results to verify)")
        elif result.passed:
            print(f"  [{name}] PASS")
        else:
            print(f"  [{name}] FAIL")
            for err in result.errors:
                print(f"    {err}")
    print()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python run_tests.py <input.json> [<input.json> ...]")
        sys.exit(1)
    for path in sys.argv[1:]:
        run_file(path)
