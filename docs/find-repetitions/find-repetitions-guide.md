---
title: "Find Repetitions — Guide"
author: "Moshe Rubin"
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

Here are the parts of the page, from top to bottom:

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

To add another box, press **+** under any box; to remove a box, press **−**
under it. The first box can't be removed. Empty boxes are skipped when the
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
  beside the box and in the report, for example `Ciphertext 2 (Intercept A50/18)`.
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
example in a garbled intercept. Enter the character that marks such
positions, such as `.` or `-`. It is empty, meaning no dits, by default.

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

Press **Run**. Every ciphertext is searched against itself, and every pair of
ciphertexts against each other.

**Print** opens the browser's print dialog with just the report, so you can
print it or save it as a PDF.

## Reading the report

The report has a header, giving the date and time of the run, the description,
the character set and the number of dits, if any. The ciphertexts follow, if
you asked for them, and then two tables.

### Repetitions found

Each line is one repetition, listed once for each pair of places it occurs:

| Column | Meaning |
|---|---|
| MSG A, MSG B | The two ciphertexts it occurs in, numbered as on the page. They are the same number for a repetition within one ciphertext. |
| POS A, POS B | Where it starts in each of them, counting the first letter as 1. |
| LEN | Its length. |
| TEXT | The repeated letters. |

The longest repetitions are listed first. Each one is as long as it can be: it
is reported in full, not as a set of shorter overlapping pieces.

For a repetition within one ciphertext, POS B is always after POS A, and the
**interval** is POS B − POS A. A sequence that occurs more than twice appears
on one line for every pair of its occurrences: three occurrences give three
lines, four give six.

The tool does not compare a ciphertext with itself shifted by a single
position: that comparison can only find runs of one repeated letter, such as
`EEEEEE`.

### Repetition counts

This table lists every sequence that appears on more than two lines of the
first table, with the number of lines. It picks out sequences that occur many
times, such as a common word or a stereotyped phrase. Because the count is of
pairs, a count of 3 usually means three occurrences, and a count of 6 four.

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
