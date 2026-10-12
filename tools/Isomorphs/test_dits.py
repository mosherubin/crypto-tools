"""
Tests for dit handling in the isomorph search and its evaluator.
Usage: python test_dits.py

A dit is a position whose symbol exists but is unknown. It keeps its position,
never equals anything, and so no window containing one is ever isomorphic.
"""

import os
import random
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'Library'))

from isomorph_evaluation import evaluate_isomorph
from isomorph_search import DIT, PRUNE_MODES, _build_delta, _find_isomorphs_between, locate_isomorphs, prune_candidates
from run_isomorph import read_ciphertext

ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
MESSAGE_B = "XYZXWV"


def located(messages, min_isolen):
    return {(c.message_a, c.message_b, c.position_a, c.position_b, c.length)
            for c in locate_isomorphs(messages, min_isolen)}


def with_dit_at(message, index):
    return message[:index] + DIT + message[index + 1:]


def canonical(window):
    first_seen = {}
    return tuple(first_seen.setdefault(symbol, len(first_seen)) for symbol in window)


class Delta(unittest.TestCase):
    def test_a_dit_is_never_a_repeat_of_a_letter_or_of_another_dit(self):
        self.assertEqual(_build_delta("A" + DIT + DIT + "A"), [3, None, None, None])


class WorkedCase(unittest.TestCase):
    def test_isomorphic_over_all_six_positions_without_a_dit(self):
        self.assertIn((0, 1, 0, 0, 6), located(["ABCADE", MESSAGE_B], 4))

    def test_dit_in_every_four_window_reports_nothing(self):
        self.assertEqual(located(["AB" + DIT + "ADE", MESSAGE_B], 4), set())


class DitPlacement(unittest.TestCase):
    def test_dit_inside_a_window_in_a_blocks_the_full_isomorph(self):
        for index in range(1, 5):
            self.assertNotIn((0, 1, 0, 0, 6), located([with_dit_at("ABCADE", index), MESSAGE_B], 4))
            self.assertEqual(located([with_dit_at("ABCADE", index), MESSAGE_B], 6), set())

    def test_dit_inside_a_window_in_b_blocks_the_full_isomorph(self):
        for index in range(1, 5):
            self.assertNotIn((0, 1, 0, 0, 6), located(["ABCADE", with_dit_at(MESSAGE_B, index)], 4))
            self.assertEqual(located(["ABCADE", with_dit_at(MESSAGE_B, index)], 6), set())

    def test_dit_at_the_start_of_a_window_is_skipped_and_the_rest_is_found(self):
        found = located([with_dit_at("ABCADE", 0), MESSAGE_B], 5)
        self.assertIn((0, 1, 1, 1, 5), found)
        self.assertFalse([c for c in found if c[2] == 0])

    def test_dit_at_the_end_of_a_window_is_skipped_and_the_rest_is_found(self):
        found = located([with_dit_at("ABCADE", 5), MESSAGE_B], 5)
        self.assertIn((0, 1, 0, 0, 5), found)
        self.assertFalse([c for c in found if c[2] + c[4] > 5])

    def test_isomorph_ending_before_a_dit_and_another_starting_after_it_are_both_found(self):
        message_a = "ABAC" + DIT + "DEDF"
        message_b = "XYXZ" + "Q" + "UVUW"
        same_alignment = {c for c in located([message_a, message_b], 4) if c[3] - c[2] == 0 and c[0] == 0 and c[1] == 1}
        self.assertEqual(same_alignment, {(0, 1, 0, 0, 4), (0, 1, 5, 5, 4)})

    def test_the_same_pair_without_a_dit_is_one_isomorph(self):
        found = located(["ABACGDEDF", "XYXZQUVUW"], 4)
        self.assertIn((0, 1, 0, 0, 9), found)

    def test_self_search_across_a_dit(self):
        message = "ABCADE" + DIT + "FGHFIJ"
        self.assertEqual(located([message], 6), {(0, 0, 0, 7, 6)})

    def test_self_search_with_a_dit_inside_a_window(self):
        message = "ABC" + DIT + "DE" + DIT + "FGHFIJ"
        self.assertEqual(located([message], 6), set())


class DitCharacters(unittest.TestCase):
    def test_different_dit_characters_read_to_the_same_text(self):
        self.assertEqual(read_ciphertext("ABC.DE", ALPHABET, ".", "a"), "ABC" + DIT + "DE")
        self.assertEqual(read_ciphertext("ABC-DE", ALPHABET, "-", "b"), "ABC" + DIT + "DE")

    def test_messages_written_with_different_dit_characters_give_identical_results(self):
        mixed = [read_ciphertext("ABCADE.FGHFIJ", ALPHABET, ".", "a"),
                 read_ciphertext("XYZXWV-QRSQTU", ALPHABET, "-", "b")]
        same = [read_ciphertext("ABCADE.FGHFIJ", ALPHABET, ".", "a"),
                read_ciphertext("XYZXWV.QRSQTU", ALPHABET, ".", "b")]
        self.assertEqual(mixed, same)
        self.assertEqual(located(mixed, 4), located(same, 4))

    def test_no_dit_unless_one_is_declared(self):
        with self.assertRaisesRegex(ValueError, "Invalid character '.'"):
            read_ciphertext("ABC.DE", ALPHABET, None, "a")

    def test_whitespace_is_dropped_and_takes_no_position(self):
        self.assertEqual(read_ciphertext("AB C\nD.E", ALPHABET, ".", "a"), "ABCD" + DIT + "E")

    def test_a_declared_dit_wins_over_the_alphabet(self):
        self.assertEqual(read_ciphertext("ABX", ALPHABET, "X", "a"), "AB" + DIT)


class Evaluator(unittest.TestCase):
    def comparisons(self, text, message_a, message_b, self_search):
        significance = evaluate_isomorph(text, 26, message_a, message_b, self_search, 1e9)
        return round(significance.expected_occurrences / significance.probability)

    def test_dit_free_counts_are_the_classic_formulas(self):
        for length_a, length_b, isolen in [(100, 100, 8), (565, 225, 12), (30, 50, 4), (20, 20, 10)]:
            message_a, message_b = "A" * length_a, "B" * length_b
            text = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"[:isolen]
            self.assertEqual(self.comparisons(text, message_a, message_b, False),
                             (length_a - isolen + 1) * (length_b - isolen + 1))
            k = length_a - 2 * isolen + 1
            self.assertEqual(self.comparisons(text, message_a, message_a, True), max(0, k * (k + 1) // 2))

    def test_cross_search_counts_only_windows_without_a_dit(self):
        message_a = "A" * 50 + DIT + "A" * 49
        self.assertEqual(self.comparisons("ABCDEFGH", message_a, "B" * 100, False), (43 + 42) * 93)

    def test_self_search_counts_match_brute_force(self):
        rng = random.Random(7)
        for _ in range(200):
            message = "".join(DIT if rng.random() < 0.2 else "A" for _ in range(rng.randint(1, 40)))
            isolen = rng.randint(1, 8)
            starts = [p for p in range(len(message) - isolen + 1) if DIT not in message[p:p + isolen]]
            expected = sum(1 for p in starts for q in starts if q >= p + isolen)
            self.assertEqual(self.comparisons("ABCDEFGH"[:isolen], message, message, True), expected)

    def test_cross_search_counts_match_brute_force(self):
        rng = random.Random(11)
        for _ in range(200):
            messages = ["".join(DIT if rng.random() < 0.2 else "A" for _ in range(rng.randint(1, 40))) for _ in range(2)]
            isolen = rng.randint(1, 8)
            windows = [sum(1 for p in range(len(m) - isolen + 1) if DIT not in m[p:p + isolen]) for m in messages]
            self.assertEqual(self.comparisons("ABCDEFGH"[:isolen], messages[0], messages[1], False), windows[0] * windows[1])


class RandomMessages(unittest.TestCase):
    @staticmethod
    def random_message(rng, length, alphabet, dit_rate):
        return "".join(DIT if rng.random() < dit_rate else rng.choice(alphabet) for _ in range(length))

    @staticmethod
    def brute_force(letters_a, letters_b, min_isolen, self_search):
        found = set()
        len_a, len_b = len(letters_a), len(letters_b)
        offsets = range(min_isolen, len_a) if self_search else range(-(len_a - 1), len_b)
        for offset in offsets:
            for pos_a in range(max(0, -offset), len_a):
                pos_b = pos_a + offset
                if pos_b >= len_b:
                    break
                room = min(len_a - pos_a, len_b - pos_b)
                if self_search:
                    room = min(room, offset)
                best = 0
                for length in range(1, room + 1):
                    window_a, window_b = letters_a[pos_a:pos_a + length], letters_b[pos_b:pos_b + length]
                    if DIT in window_a or DIT in window_b or canonical(window_a) != canonical(window_b):
                        break
                    best = length
                if best >= min_isolen:
                    found.add((pos_a, pos_b, best))
        return found

    def test_scan_matches_brute_force(self):
        rng = random.Random(20261012)
        for _ in range(200):
            alphabet = "ABCDEF"[:rng.randint(2, 6)]
            dit_rate = rng.choice([0.0, 0.05, 0.1, 0.2])
            letters_a = self.random_message(rng, rng.randint(8, 30), alphabet, dit_rate)
            self_search = rng.random() < 0.4
            letters_b = letters_a if self_search else self.random_message(rng, rng.randint(8, 30), alphabet, dit_rate)
            min_isolen = rng.randint(2, 5)

            scanned = {(c.position_a, c.position_b, c.length)
                       for c in _find_isomorphs_between(letters_a, _build_delta(letters_a), letters_b,
                                                         _build_delta(letters_b), min_isolen, self_search)}
            self.assertEqual(scanned, self.brute_force(letters_a, letters_b, min_isolen, self_search),
                             (letters_a, letters_b, min_isolen, self_search))

    def test_every_located_and_pruned_candidate_is_dit_free_at_its_true_position(self):
        rng = random.Random(99)
        for _ in range(60):
            messages = [self.random_message(rng, rng.randint(15, 45), "ABCDEF", 0.1) for _ in range(rng.randint(1, 3))]
            min_isolen = rng.randint(3, 5)
            candidates = locate_isomorphs(messages, min_isolen)
            for mode in PRUNE_MODES:
                for c in prune_candidates(candidates, mode, min_isolen):
                    self.assertEqual(messages[c.message_a][c.position_a:c.position_a + c.length], c.text_a)
                    self.assertEqual(messages[c.message_b][c.position_b:c.position_b + c.length], c.text_b)
                    self.assertNotIn(DIT, c.text_a)
                    self.assertNotIn(DIT, c.text_b)
                    self.assertEqual(canonical(c.text_a), canonical(c.text_b))


if __name__ == "__main__":
    unittest.main()
