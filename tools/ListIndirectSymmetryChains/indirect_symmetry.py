#!/usr/bin/env python3
"""
Indirect Symmetry of Position
Cryptanalytic chaining script.
"""

import sys
from itertools import combinations


def parse_input(lines):
    rows = []
    for lineno, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            continue
        if line.startswith('#'):
            continue
        parts = line.split(None, 1)
        if len(parts) != 2:
            print(f"Error on line {lineno}: expected 'name contents', got: {repr(line)}", file=sys.stderr)
            sys.exit(1)
        name, contents = parts
        contents = contents.upper()
        rows.append((name, contents, lineno))
    return rows


def validate_rows(rows):
    # Check all content strings are the same length
    lengths = [(name, len(contents)) for name, contents, _ in rows]
    expected_len = lengths[0][1]
    for name, length in lengths[1:]:
        if length != expected_len:
            print(
                f"Error: row '{name}' has length {length}, "
                f"but expected {expected_len} (same as first row).",
                file=sys.stderr
            )
            sys.exit(1)

    # Check no repeated characters within each row (ignoring periods)
    for name, contents, lineno in rows:
        seen = {}
        for pos, ch in enumerate(contents):
            if ch == '.':
                continue
            if ch in seen:
                print(
                    f"Error: row '{name}' (line {lineno}) has duplicate character "
                    f"'{ch}' at positions {seen[ch]} and {pos}.",
                    file=sys.stderr
                )
                sys.exit(1)
            seen[ch] = pos


def build_chains(top_name, top_contents, bot_name, bot_contents):
    n = len(top_contents)

    # Build lookup: character -> position, for each row
    top_pos = {}  # char -> index in top row
    bot_pos = {}  # char -> index in bottom row

    for i, ch in enumerate(top_contents):
        if ch != '.':
            top_pos[ch] = i

    for i, ch in enumerate(bot_contents):
        if ch != '.':
            bot_pos[ch] = i

    used_top = set()  # positions in top row already assigned to a chain
    used_bot = set()  # positions in bottom row already assigned to a chain

    chains = []  # list of (start_position, chain_string)

    for start_pos in range(n):
        top_ch = top_contents[start_pos]
        bot_ch = bot_contents[start_pos]

        # Skip if either is a period, or either position already used
        if top_ch == '.' or bot_ch == '.':
            continue
        if start_pos in used_top or start_pos in used_bot:
            continue

        # Start a chain from this vertical pair
        chain = [top_ch, bot_ch]
        used_top.add(start_pos)
        used_bot.add(start_pos)

        # Extend to the right:
        # Take last char of chain, find it in top row, read bottom row at that position
        while True:
            last_ch = chain[-1]
            if last_ch not in top_pos:
                break
            next_pos = top_pos[last_ch]
            if next_pos in used_top or next_pos in used_bot:
                break
            next_ch = bot_contents[next_pos]
            if next_ch == '.':
                break
            chain.append(next_ch)
            used_top.add(next_pos)
            used_bot.add(next_pos)

        # Extend to the left:
        # Take first char of chain, find it in bottom row, read top row at that position
        while True:
            first_ch = chain[0]
            if first_ch not in bot_pos:
                break
            prev_pos = bot_pos[first_ch]
            if prev_pos in used_top or prev_pos in used_bot:
                break
            prev_ch = top_contents[prev_pos]
            if prev_ch == '.':
                break
            chain.insert(0, prev_ch)
            used_top.add(prev_pos)
            used_bot.add(prev_pos)

        if len(chain) >= 2:
            chains.append((start_pos, ''.join(chain)))

    # Sort by the position of the first vertical pair that initiated the chain
    chains.sort(key=lambda x: x[0])

    return [chain_str for _, chain_str in chains]


def main():
    lines = sys.stdin.read().splitlines()
    rows = parse_input(lines)

    if len(rows) < 2:
        print("Error: at least two rows are required.", file=sys.stderr)
        sys.exit(1)

    validate_rows(rows)

    for (name_a, contents_a, _), (name_b, contents_b, _) in combinations(rows, 2):
        chains = build_chains(name_a, contents_a, name_b, contents_b)
        if chains:
            chain_str = ' / '.join(chains)
            print(f"{name_a}-{name_b} {chain_str}")
        else:
            print(f"{name_a}-{name_b} (no chains)")


if __name__ == '__main__':
    main()
