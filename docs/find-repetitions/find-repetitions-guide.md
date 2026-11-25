---
title: "Find Repetitions — Guide"
author: "Moshe Rubin"
toc: true
---

[&larr; back to Find Repetitions](find-repetitions.html)

## What is this tool used for?

A **repetition** is a sequence of ciphertext letters that occurs more than once,
either within one ciphertext or in two different ciphertexts. Short repetitions
happen by chance in any text, but long ones rarely do: a long repetition almost
always means that the same plaintext was enciphered in the same way twice.

Repetitions are among the first things a cryptanalyst looks for:

* **Within one ciphertext.** In a periodic polyalphabetic cipher, such as the
  Vigenère, the same plaintext gives the same ciphertext only when both
  occurrences fall at the same point in the key. The distance between them, the
  **interval**, is then a multiple of the period. Factoring the intervals of
  several repetitions and looking for the factor they share points to the
  period. This is the method of Kasiski.
* **Between ciphertexts.** A repetition shared by two messages suggests that
  they were enciphered with the same key, or that they contain the same
  stereotyped wording, such as a common opening or signature. Messages like
  these can often be set in depth and solved together.

This tool finds every repetition at or above a length you choose, within each
ciphertext and between every pair of ciphertexts, and lists where each one
occurs.

## Parts of the page

From top to bottom, the page has:

* the ciphertext boxes and the **Import** button;
* the settings: **Description**, **Character set**, **Dits character**,
  **Display ciphertext(s) in output** and **Minimum Sequence Length**;
* the **Run** and **Print** buttons;
* the output report.

Hover over any part of the page for a second to see a short tip about it.

## Entering the ciphertexts

### Typing or pasting

Type or paste one ciphertext into each box. Spaces and line breaks are ignored,
so the ciphertext may be in five-letter groups or in one long line. Upper and
lower case are treated the same.

To add another box, click **+** under any box; to remove a box, click **−**
under it. The first box cannot be removed. Empty boxes are skipped when the
search runs.

A character that is neither in the character set nor the dits character (see
below) stops the search with an error naming the character and its position.

### Importing a file

**Import** reads one or more ciphertexts from a text file, such as one exported
from a CryptML file. The file is read like this:

* Ciphertexts are separated by blank lines or by comment lines, which start
  with `#`. One ciphertext may run over several lines, as long as no blank line
  comes between them.
* A comment line just before a ciphertext becomes its **label**, which is shown
  beside the box and in the report, for example
  `Ciphertext 2 (Intercept A50/18)`.
* A comment line of the form `# Date: "…" Time: "…" Ditschar: "."`, with any
  field left out, gives the ciphertext's date, time and dit character instead.

For example:

```
# Intercept A50/17
# Date: "12 March 1943" Time: "0815"
XKQBM TRWPA LMNVC
ZJQOE TRWPA

# Intercept A50/18
TRWPA HHJKL QWOEP
```

The first ciphertext in the file goes into the first empty box, and each of the
others gets a new box. If a ciphertext in the file is already in one of the
boxes, or appears twice in the file, the tool says so and offers to skip it.
Importing the same file twice by mistake would otherwise double every
repetition.

An imported ciphertext keeps its label, date, time and dit character only until
you edit it by hand. After that it is treated like a typed one.

## Settings

### Description (optional)

A label for this run. It is printed at the top of the report.

### Character set

The symbols the ciphertexts are written in:

* `[A-Za-z]`: the 26 letters (the default);
* `[0-9]`: the 10 digits;
* `[A-Za-z0-9]`: letters and digits;
* **Other…**: any set you type, written as in a regular expression. The
  brackets are optional: `ADFGVX`, `[ADFGVX]` and `A-IK-Z` (a 25-letter
  alphabet without J) are all accepted. Case is ignored.

### Dits character

A **dit** marks a position whose symbol exists but could not be read, for
example in a garbled intercept. Enter the character that marks such positions,
such as `.` or `-`. By default it is empty, meaning there are no dits.

A dit keeps its place, so the positions of the letters after it are unchanged,
but it never matches anything, not even another dit. A repetition therefore
stops at a dit and never contains one.

An imported ciphertext uses the dit character its file names, or none if the
file names none; this setting applies only to ciphertexts you type or paste.

### Display ciphertext(s) in output

When checked, the report starts by printing each ciphertext in groups of five,
ten groups to a line, with its letter count. Dits are printed as `.`. This
makes it easy to check positions by hand.

### Minimum Sequence Length

The shortest repetition to report; the default is 5. Every text repeats short
sequences by chance, so a floor is needed. Lower it to look for weaker
evidence, and raise it if the list is flooded with chance repetitions. For a
period search, repetitions of three or four letters are often worth seeing as
well.

## Running the search

Click **Run**. Every ciphertext is searched against itself, and every pair of
ciphertexts against each other.

**Print** opens the browser's print dialog with just the report, so you can
print it or save it as a PDF.

## Reading the report

The report has a header, giving the date and time of the run, the description,
the character set and the number of dits, if any. The ciphertexts follow, if
you asked for them, and then two tables.

### Repetitions found

Each line is one repetition, listed once for each pair of places where it
occurs:

| Column | Meaning |
|---|---|
| MSG A, MSG B | The two ciphertexts it occurs in, numbered as on the page. They are the same number for a repetition within one ciphertext. |
| POS A, POS B | Where it starts in each of them, counting the first letter as 1. |
| LEN | Its length. |
| DIST | For a repetition within one ciphertext, the distance between its two occurrences, POS B − POS A. Left blank for a repetition between two different ciphertexts. |
| TEXT | The repeated letters. |

The longest repetitions are listed first. Each one is as long as it can be: it
is reported in full, not as a set of shorter overlapping pieces.

For a repetition within one ciphertext, POS B is always after POS A, and DIST is
the **interval** between them. With a repeating key, the intervals of genuine
repetitions are multiples of the period, but those of chance repetitions need
not be.

A sequence that occurs more than twice appears on one line for every pair of its
occurrences: three occurrences give three lines, four give six.

The tool does not compare a ciphertext with itself shifted by a single
position: that comparison can only find runs of one repeated letter, such as
`EEEEEE`.

### Repetition counts

This table lists every sequence that appears on more than two lines of the
first table, with the number of lines. It picks out sequences that occur many
times, such as a common word or a stereotyped phrase. Because the count is of
pairs, a count of 3 usually means three occurrences, and a count of 6 four.

## Uses of repetitions between messages

Repetitions between messages have many uses, grouped below.

### Messages in the same monoalphabetic system

1. **Identifying messages that share an alphabet.** Repetitions at any position
   between two messages show they probably use the same cipher alphabet. If
   messages that repeat within themselves never repeat against each other, they
   probably use different alphabets.
2. **Finding stock phrases and probable words.** Greetings, addresses, headings,
   signatures, `SECRET` and standard formulas recur in many messages. A repeat
   found across several messages is a strong candidate for such a phrase, and it
   gives you a crib.
3. **Carrying solved text from one message to another.** Once a stretch of one
   message is solved, the same ciphertext in another message is solved too, and
   the letters around it become new cribs.
4. **Pooling for frequency counts.** Messages known to share an alphabet can be
   counted together. A bigger sample gives far more reliable frequencies.

### Polyalphabetic messages with the identical key

5. **Detecting identical keys.** In a periodic polyalphabetic cipher, a
   plaintext repeated at the same key phase gives the same ciphertext. Many long
   repetitions between messages mean they were probably enciphered with the same
   key.
6. **Putting messages in depth.** Each repetition gives an offset,
   `POS A − POS B`. If the offsets agree (taken mod the period), sliding one
   message by that amount lines up the key letters. Every column then holds
   letters from the same alphabet. Several repetitions with the same offset
   confirm the alignment.
7. **Measuring the period.** Within one message, the factors common to the
   `DIST` values point to the period. Between messages, the offsets give a
   second, independent check, because they must agree with the same period.
8. **Comparing key start points.** A repetition at the same position in two
   messages means the key started at the same point. A repetition at a constant
   non-zero offset means the key started at a different point. This tells you
   how the message indicators relate, and whether the key is being reused at a
   shifted setting.
9. **Telling mono- from polyalphabetic.** Between monoalphabetic messages,
   repetitions fall at any offset. Between polyalphabetic ones, they fall only
   at offsets that agree modulo the period.
10. **Spotting autokey.** In a plaintext autokey system, each letter is
    enciphered with the previous plaintext letters (after an introductory key),
    so a plaintext repeated in two messages gives a ciphertext repeat that
    starts late, by the length of the introductory key. A ciphertext repeat that
    begins a letter or two after the matching plaintext, with one isolated
    differing letter before it, points to an autokey with a short introductory
    key. In [Example 2](example-2-multiple-ciphertexts-manually-inserted.html#what-the-search-results-show),
    the first letters of messages 1 and 2 (`H` and `J`) differ before the shared
    `UFIIOCQJJIVZOZ`. *Military Cryptanalytics* reads that isolated first letter
    as the sign of a 1-letter introductory key.

### Message housekeeping

11. **Clustering a collection.** Messages that share many repetitions probably
    belong together, and a message with none belongs elsewhere. This is the
    "cryptographic homogeneity" that *Military Cryptanalytics* speaks of, and it
    tells you which messages to work on together.
12. **Finding retransmissions, corrections and garbles.** A long repeat covering
    nearly a whole message means a re-sent message. A long repeat interrupted by
    a few letters means the same plaintext with a transmission error or a
    changed word. Both are used for error correction and as cribs.
13. **Spotting fixed formats.** Repeats at the same position near the start or
    end of several messages reveal fixed openings and closings, and padding.

### Reading the results

14. **Weighing chance.** For random letters, the number of chance repeats of
    length *L* between messages of lengths *a* and *b* is about `a × b / 26^L`.
    For two 100-letter messages that is about 0.6 at length 3 and about 0.001 at
    length 5. Real text is less uniform, so expect more. Longer repeats are
    strong evidence, and short ones may be chance.

Repetitions between messages enciphered with different keys will not normally
appear as repeated sequences. Isomorphs, which share a pattern of repeated
letters rather than the letters themselves, are the tool for that case.

## Examples of finding repetitions

* [A single ciphertext manually inserted](example-1-single-ciphertext-manually-inserted.html)
* [Multiple ciphertexts manually inserted](example-2-multiple-ciphertexts-manually-inserted.html)
* [Multiple ciphertexts from an imported file](example-3-multiple-ciphertexts-from-imported-file.html)

## References

* Kasiski, Friedrich W. *Die Geheimschriften und die Dechiffrir-Kunst*. Berlin:
  E. S. Mittler und Sohn, 1863.
* Friedman, William F. *Military Cryptanalysis, Part II: Simpler Varieties of
  Polyalphabetic Substitution Systems*. Washington, DC: Government Printing
  Office, 1938.
* Gaines, Helen Fouché. *Elementary Cryptanalysis: A Study of Ciphers and Their
  Solution*. Boston: American Photographic Publishing, 1939. Reprinted as
  *Cryptanalysis: A Study of Ciphers and Their Solution*. New York: Dover, 1956.
* Callimahos, Lambros D. *Military Cryptanalytics, Part III*. Fort George G. 
  Meade, MD: National Security Agency, 1977.
