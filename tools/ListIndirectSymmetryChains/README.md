# List Indirect Symmetry Chains
Given a polyalphabetic reconstruction matrix, list all derivable chains from the secondary alphabets

# Quick start

When presented with a polyalphabet reconstruction matrix (e.g., the table derived from known plaintext letters in a polyalphabetic cipher) it is helpful to reconstruct the secondary alphabet(s), followed by reconstructing the primary alphabet(s).  Here is an example of a reconstruction marix:

```
0 ABCDEFGHIJKLMNOPQRSTUVWXYZ
1 ..B....N.....T............
2 ....G.........T.....X.....
3 .............K...CZ.......
4 G...K............F........
5 ...K..O.Q........D........
6 ...U.............K.B......
7 ..............M...........
8 .................F.S..A...
```

Each line is a secondary alphabet (either complete or partial) with the format "<alphabet-name> <partial-alphabet>".  In our example:

- Alphabet '0' is the plaintext alphabet in A-Z order.  If we're dealing with a K3 or K4 cipher, then this plaintext alphabet is a secondary alphabet having an underlying mixed order.
- Alphabet '1' is a partial ciphertext alphabet.
. . .
- Alphabet '8' is a partial ciphertext alphabet.

The command to run this is, and its output:

```
D:\Private\Dev\MVS\Repositories\crypto\Crypt\Tools\ListIndirectSymmetryChains>python indirect_symmetry.py < secondary-table.input.txt
0-1 OAZ / MQCK / REB / HD / JL
0-2 AU / CMK / LIW / JN / OG / RH
0-3 AMH / BN / EW / IOP / RL
0-4 JBCANRM / IEQOW / HK / PG
0-5 BJ / EI / HLU / MRN / PD
0-6 AW / COLBQU / NDK / JEMG / IRPZ
0-7 AQ / BI / CEN / DL / PH / RW
1-2 ZU / QKM / LN / AG / EH
1-3 ZM / BW / QH / AP / EL
1-4 ZN / DKAW / LBQ / CO / EM
1-5 BI / DL / QR / EN
1-6 ZW / KO / BM / ALEP / QG / CU
1-7 ZQ / KEW / BN
2-3 UM / WO / KHL / GP
2-4 UNB / HMA / GWE
2-5 IU / KR / HN
2-6 UWR / MO / NE / IB / KGL / HP
2-7 UQ / ME / HW
3-4 LMNC / PWQ / OE
3-5 LNJ / WI / HR
3-6 MWM / NQ / OR / HG / PLP
3-7 MQ / LWNI
4-5 CJ / QI / KL / GD / MN
4-6 NWL / CQMP / AOU / BERD / GZ
4-7 NQN / CI / AE / GH / MW
5-6 JQ / IM / UB / RG / DZ / NP
5-7 JINW / DH
6-7 PWQI / OE / KL / MN / ZH
```

# Future addition

* Allow blank lines, and lines beginning with a '#' sign.