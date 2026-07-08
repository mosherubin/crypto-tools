import argparse
import re
import sys


def parse_matrix(text):
    lines = {}
    for raw in text.splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith('#'):
            continue
        match = re.match(r'^(\d+)\s+([A-Za-z.]{26})\s*$', stripped)
        if not match:
            sys.exit(f"Error: invalid matrix line: {raw!r}")
        line_num = int(match.group(1))
        alphabet = match.group(2).upper()
        if line_num in lines:
            sys.exit(f"Error: duplicate matrix line {line_num}")
        lines[line_num] = alphabet
    return lines


DEFAULT_LINE0 = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'


def validate_matrix(lines):
    cipher_lines = {k: v for k, v in lines.items() if k > 0}
    if not cipher_lines:
        sys.exit("Error: matrix contains no cipher alphabet lines (1..N)")
    period = max(cipher_lines)
    for i in range(1, period + 1):
        if i not in cipher_lines:
            sys.exit(f"Error: matrix is missing line {i}")
    line0 = lines.get(0, DEFAULT_LINE0)
    return period, line0, cipher_lines


def convert(ciphertext, period, line0, cipher_lines):
    letters = [c.upper() for c in ciphertext if c.isalpha()]
    plaintext = []
    for i, c in enumerate(letters):
        m = (i % period) + 1
        p = cipher_lines[m].find(c)
        plaintext.append(line0[p] if p != -1 else '.')
    return ''.join(letters), ''.join(plaintext)


def grouped(text, group_size):
    return [text[i:i+group_size] for i in range(0, len(text), group_size)]


def print_aligned(ciphertext, plaintext, period):
    ct_groups = grouped(ciphertext, period)
    pt_groups = grouped(plaintext, period)
    groups_per_line = (50 + 1) // (period + 1)
    for i in range(0, len(pt_groups), groups_per_line):
        print(' '.join(pt_groups[i:i+groups_per_line]))
        print(' '.join(ct_groups[i:i+groups_per_line]))
        if i + groups_per_line < len(pt_groups):
            print()


def main():
    parser = argparse.ArgumentParser(
        description='Convert periodic polyalphabetic ciphertext to monoalphabetic '
                    'using a reconstruction matrix.'
    )
    parser.add_argument('ciphertext',
                        help='Ciphertext (A-Z letters; non-alpha characters are ignored)')
    parser.add_argument('matrix_file',
                        help='Path to the reconstruction matrix file')
    args = parser.parse_args()

    try:
        with open(args.matrix_file, encoding='utf-8') as f:
            matrix_text = f.read()
    except OSError as e:
        sys.exit(f"Error: cannot read matrix file: {e}")

    lines = parse_matrix(matrix_text)
    period, line0, cipher_lines = validate_matrix(lines)
    ciphertext, plaintext = convert(args.ciphertext, period, line0, cipher_lines)

    print()
    print_aligned(ciphertext, plaintext, period)


if __name__ == '__main__':
    main()
