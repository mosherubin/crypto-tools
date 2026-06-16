# Complete Reconstruction Matrix
Given a polyalphabetic reconstruction matrix, perform the maximal number of indirect symmetry of position operations to reconstruct the matrix.

# Quick start

When presented with a polyalphabet reconstruction matrix (e.g., the table derived from known plaintext letters in a polyalphabetic cipher) it is helpful to reconstruct the secondary alphabet(s), followed by reconstructing the primary alphabet(s).  Here is an example of a reconstruction marix:

```
# Source: The Cryptogram, MJ2026, E-23, Quagmire III.

0  ABCDEFGHIJKLMNOPQRSTUVWXYZ
1  .W..G.Z............K......
2  ....K..Z.....S......F.....
3  ....X..............U......
4  E......GO..........P......
5  ..R.D..C.....P............
6  ....J.NO......F...........
7  ....................O.....
8  ......C...................
9  .......JH..........S..A...
10 .......EV....Q............
```

Each line is a secondary alphabet (either complete or partial) with the format "<alphabet-name> <partial-alphabet>".  In our example:

- Alphabet '0' is the plaintext alphabet in A-Z order.  If we're dealing with a K3 or K4 cipher, then this plaintext alphabet is a secondary alphabet having an underlying mixed order.
- Alphabet '1' is a partial ciphertext alphabet.
. . .
- Alphabet '8' is a partial ciphertext alphabet.

The command to run this is, and its output:

```
D:\Private\Dev\MVS\Repositories\crypto\Crypt\Tools\CompleteReconstructionMatrix>python complete-table.py < input\initial-table.MCII-page148-figure-42.txt
Start time: 2026-05-28 17:19:19

=== Initial Matrix ===
0  ABCDEFGHIJKLMNOPQRSTUVWXYZ
1  ....B..Q...........E......
2  ....C..L...........X......
3  ....I..V...........C......
4  ....N..P...........B......
5  ....X..O...........P......
6  ....T..Z...........V......

=== Pass 1 ===
Complete rectangles: 504
Incomplete rectangles: 3312

B(1-5):E(1-20):N(4-5):B(4-20) -> B(0-2):E(0-5):?(1-2):B(1-5)
B(1-5):E(1-20):I(3-5):C(3-20) -> B(0-2):E(0-5):?(2-2):C(2-5)
B(1-5):E(1-20):C(2-5):X(2-20) -> B(0-2):E(0-5):?(5-2):X(5-5)
B(1-5):E(0-5):E(1-20):T(0-20) -> B(0-2):E(0-5):?(6-2):T(6-5)
C(3-20):E(1-20):I(3-5):B(1-5) -> C(0-3):E(0-5):?(1-3):B(1-5)
C(2-5):E(0-5):X(2-20):T(0-20) -> C(0-3):E(0-5):?(6-3):T(6-5)
E(0-5):I(3-5):T(0-20):C(3-20) -> E(0-5):I(0-9):T(6-5):?(6-9)
E(0-5):N(4-5):T(0-20):B(4-20) -> E(0-5):N(0-14):T(6-5):?(6-14)
E(1-20):P(5-20):B(1-5):X(5-5) -> E(0-5):P(0-16):B(1-5):?(1-16)
E(1-20):Q(1-8):B(4-20):P(4-8) -> E(0-5):Q(0-17):B(1-5):?(1-17)
E(1-20):Q(1-8):C(3-20):V(3-8) -> E(0-5):Q(0-17):C(2-5):?(2-17)
E(1-20):Q(1-8):X(2-20):L(2-8) -> E(0-5):Q(0-17):X(5-5):?(5-17)
E(1-20):Q(1-8):T(0-20):H(0-8) -> E(0-5):Q(0-17):T(6-5):?(6-17)
E(1-20):V(6-20):B(1-5):T(6-5) -> E(0-5):V(0-22):B(1-5):?(1-22)
E(1-20):X(2-20):B(1-5):C(2-5) -> E(0-5):X(0-24):B(1-5):?(1-24)
E(0-5):X(5-5):T(0-20):P(5-20) -> E(0-5):X(0-24):T(6-5):?(6-24)
T(6-5):V(6-20):X(5-5):P(5-20) -> T(0-20):V(0-22):X(2-20):?(2-22)
T(6-5):V(6-20):C(2-5):X(2-20) -> T(0-20):V(0-22):C(3-20):?(3-22)
T(6-5):V(6-20):B(1-5):E(1-20) -> T(0-20):V(0-22):B(4-20):?(4-22)
T(6-5):Z(6-8):E(0-5):H(0-8) -> T(0-20):Z(0-26):E(1-20):?(1-26)
T(6-5):Z(6-8):X(5-5):O(5-8) -> T(0-20):Z(0-26):X(2-20):?(2-26)
T(6-5):Z(6-8):C(2-5):L(2-8) -> T(0-20):Z(0-26):C(3-20):?(3-26)
T(6-5):Z(6-8):B(1-5):Q(1-8) -> T(0-20):Z(0-26):B(4-20):?(4-26)

New letters added this pass: 23

=== Interim Matrix ===
0  ABCDEFGHIJKLMNOPQRSTUVWXYZ
1  .NI.B..Q.......XP..E.T.C.H
2  .I..C..L........V..X.P...O
3  ....I..V...........C.X...L
4  ....N..P...........B.E...Q
5  .C..X..O........L..P......
6  .EX.T..ZC....B..H..V...P..

=== Pass 2 ===
Complete rectangles: 2208
Incomplete rectangles: 8352

B(0-2):N(1-2):C(0-3):I(1-3) -> B(0-2):N(0-14):C(5-2):?(5-14)
B(1-5):P(1-17):C(2-5):V(2-17) -> B(0-2):P(0-16):C(5-2):?(5-16)
B(1-5):P(1-17):E(0-5):Q(0-17) -> B(0-2):P(0-16):E(6-2):?(6-16)
C(5-2):L(5-17):I(2-2):V(2-17) -> C(0-3):L(0-12):I(1-3):?(1-12)
C(2-5):L(2-8):X(5-5):O(5-8) -> C(0-3):L(0-12):X(6-3):?(6-12)
C(5-2):O(5-8):I(2-2):L(2-8) -> C(0-3):O(0-15):I(1-3):?(1-15)
C(2-5):V(2-17):B(1-5):P(1-17) -> C(0-3):V(0-22):?(2-3):P(2-22)
C(2-5):V(2-17):X(5-5):L(5-17) -> C(0-3):V(0-22):X(6-3):?(6-22)
E(1-20):P(5-20):N(1-2):C(5-2) -> E(0-5):P(0-16):N(4-5):?(4-16)
E(6-2):X(6-3):N(1-2):I(1-3) -> E(0-5):X(0-24):N(4-5):?(4-24)
H(0-8):L(2-8):V(0-22):P(2-22) -> H(0-8):L(0-12):V(3-8):?(3-12)
H(1-26):O(2-26):P(1-17):V(2-17) -> H(0-8):O(0-15):P(4-8):?(4-15)
H(0-8):P(4-8):V(0-22):E(4-22) -> H(0-8):P(0-16):V(3-8):?(3-16)
H(0-8):Q(1-8):V(0-22):T(1-22) -> H(0-8):Q(0-17):V(3-8):?(3-17)
H(0-8):Q(1-8):P(0-16):X(1-16) -> H(0-8):Q(0-17):P(4-8):?(4-17)
I(2-2):V(2-17):N(1-2):P(1-17) -> I(0-9):V(0-22):?(2-9):P(2-22)
L(2-8):V(2-17):Q(1-8):P(1-17) -> L(0-12):V(0-22):?(2-12):P(2-22)
O(2-26):V(2-17):H(1-26):P(1-17) -> O(0-15):V(0-22):?(2-15):P(2-22)
P(1-17):Q(0-17):T(1-22):V(0-22) -> P(0-16):Q(0-17):?(2-16):V(2-17)
T(1-22):V(0-22):P(1-17):Q(0-17) -> T(0-20):V(0-22):P(5-20):?(5-22)
V(2-17):X(2-20):P(1-17):E(1-20) -> V(0-22):X(0-24):P(2-22):?(2-24)
V(6-20):B(4-20):Z(6-8):P(4-8) -> V(3-8):?(3-24):Z(6-8):P(6-24)
E(1-20):P(1-17):X(2-20):V(2-17) -> ?(5-3):P(5-20):X(6-3):V(6-20)
B(1-5):P(1-17):C(2-5):V(2-17) -> ?(5-9):P(5-20):C(6-9):V(6-20)
P(1-17):T(1-22):V(2-17):P(2-22) -> P(5-20):?(5-24):V(6-20):P(6-24)

New letters added this pass: 25

=== Interim Matrix ===
0  ABCDEFGHIJKLMNOPQRSTUVWXYZ
1  .NI.B..Q...V..LXP..E.T.C.H
2  .IB.C..LN..Q..HTV..X.P.E.O
3  ....I..V...P...ET..C.X.B.L
4  ....N..P......VCX..B.E.I.Q
5  .CE.X..OB....I.VL..P.Q.T..
6  .EX.T..ZC..O.B.QH..V.L.P..

=== Pass 3 ===
Complete rectangles: 7216
Incomplete rectangles: 11776

B(2-3):L(2-8):C(0-3):H(0-8) -> B(0-2):L(0-12):C(5-2):?(5-12)
B(2-3):O(2-26):C(0-3):Z(0-26) -> B(0-2):O(0-15):C(5-2):?(5-15)
C(0-3):E(5-3):N(0-14):I(5-14) -> C(0-3):E(0-5):?(3-3):I(3-5)
E(6-2):L(6-22):N(1-2):T(1-22) -> E(0-5):L(0-12):N(4-5):?(4-12)
E(5-3):O(5-8):I(1-3):Q(1-8) -> E(0-5):O(0-15):I(3-5):?(3-15)

New letters added this pass: 5

=== Interim Matrix ===
0  ABCDEFGHIJKLMNOPQRSTUVWXYZ
1  .NI.B..Q...V..LXP..E.T.C.H
2  .IB.C..LN..Q..HTV..X.P.E.O
3  ..N.I..V...P..QET..C.X.B.L
4  ....N..P...T..VCX..B.E.I.Q
5  .CE.X..OB..H.IZVL..P.Q.T..
6  .EX.T..ZC..O.B.QH..V.L.P..

=== Pass 4 ===
Complete rectangles: 9048
Incomplete rectangles: 11392


New letters added this pass: 0

No new letters found. Stopping.

=== Final Matrix ===
0  ABCDEFGHIJKLMNOPQRSTUVWXYZ
1  .NI.B..Q...V..LXP..E.T.C.H
2  .IB.C..LN..Q..HTV..X.P.E.O
3  ..N.I..V...P..QET..C.X.B.L
4  ....N..P...T..VCX..B.E.I.Q
5  .CE.X..OB..H.IZVL..P.Q.T..
6  .EX.T..ZC..O.B.QH..V.L.P..

End time:   2026-05-28 17:19:20
Elapsed:    0:00:00.508441
```

# References

* For the fundamental text used to create the script's algorithm, see [Military Cryptanalytics, Part II](https://www.nsa.gov/portals/75/documents/news-features/declassified-documents/friedman-documents/publications/FOLDER_257/41751819079101.pdf), Chapter VII.