# Solve Polyalphabet Isolog Messages

Given two polyalphabetic periodic ciphers that are isologs, perform the grunge work needed to implement Abraham Sinkov's method.

# Usage

The command for running this script is:

```
usage: solve-polyalphabetic-isologs.py [-h] --message1 MESSAGE1 --period1 PERIOD1 --message2 MESSAGE2
                                       --period2 PERIOD2
```

The command line options are all mandatory.

# Examples

Suppose we have two K3 polyalphabetic periodic ciphers whose plaintexts are identical (i.e., isologs):

```
CRBVK DLEXY ZGXPP LVBDF DMRWK WLEUP MXIGK HYMIX UXQUU CEIGK HYMIX 
ULSYS KUTLK ZUTCQ WEFGL BSBNY DMFWA MTTDQ PVIGF MYBGL ALQTA XBODY 
SLJWL RABDF KAYZY BQEUX ULSCA CLSYP VVFCS KAFWA EVMTF DMRWK WLEUL 
MG

BQFJF EVVSO WVTZL FUCCP YNMSV GRAZS EPJZF DCBMZ XUWCT KDKEE BPDVE 
WRPRW IAHGF MLORS BGJOM ICCAZ YNXSW OAZBD KZJZT NCZHR PYWUY TIYCZ 
IITSJ PHOBU IOLHU YDVEZ XYCEY KFQLM NOXYK ZHRVE QZQQT EXSLI BYDCM 
ZX
```

The following command produces the following output:

```
python solve-polyalphabetic-isologs.py --message1 "CRBVK DLEXY ZGXPP LVBDF DMRWK WLEUP MXIGK HYMIX UXQUU CEIGK HYMIX ULSYS KUTLK ZUTCQ WEFGL BSBNY DMFWA MTTDQ PVIGF MYBGL ALQTA XBODY SLJWL RABDF KAYZY BQEUX ULSCA CLSYP VVFCS KAFWA EVMTF DMRWK WLEUL MG" --period1 5 --message2 "BQFJF EVVSO WVTZL FUCCP YNMSV GRAZS EPJZF DCBMZ XUWCT KDKEE BPDVE WRPRW IAHGF MLORS BGJOM ICCAZ YNXSW OAZBD KZJZT NCZHR PYWUY TIYCZ IITSJ PHOBU IOLHU YDVEZ XYCEY KFQLM NOXYK ZHRVE QZQQT EXSLI BYDCM ZX" --period2 6

Message 1 (period 5): CRBVKDLEXYZGXPPLVBDFDMRWKWLEUPMXIGKHYMIXUXQUUCEIGKHYMIXULSYSKUTLKZUTCQWEFGLBSBNYDMFWAMTTDQPVIGFMYBGLALQTAXBODYSLJWLRABDFKAYZYBQEUXULSCACLSYPVVFCSKAFWAEVMTFDMRWKWLEULMG
Message 2 (period 6): BQFJFEVVSOWVTZLFUCCPYNMSVGRAZSEPJZFDCBMZXUWCTKDKEEBPDVEWRPRWIAHGFMLORSBGJOMICCAZYNXSWOAZBDKZJZTNCZHRPYWUYTIYCZIITSJPHOBUIOLHUYDVEZXYCEYKFQLMNOXYKZHRVEQZQQTEXSLIBYDCMZX

Initial array: 11 rows x 167 columns (rows 0..4 = message1, rows 5..10 = message2)

              1111111111222222222233333333334444444444555555555566666666667777777777888888888899999999990000000000111111111122222222223333333333444444444455555555556666666
    01234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456
 0: C....D....Z....L....D....W....M....H....U....C....H....U....K....Z....W....B....D....M....P....M....A....X....S....R....K....B....U....C....V....K....E....D....W....M.
 1: .R....L....G....V....M....L....X....Y....X....E....Y....L....U....U....E....S....M....T....V....Y....L....B....L....A....A....Q....L....L....V....A....V....M....L....G
 2: ..B....E....X....B....R....E....I....M....Q....I....M....S....T....T....F....B....F....T....I....B....Q....O....J....B....Y....E....S....S....F....F....M....R....E....
 3: ...V....X....P....D....W....U....G....I....U....G....I....Y....L....C....G....N....W....D....G....G....T....D....W....D....Z....U....C....Y....C....W....T....W....U...
 4: ....K....Y....P....F....K....P....K....X....U....K....X....S....K....Q....L....Y....A....Q....F....L....A....Y....L....F....Y....X....A....P....S....A....F....K....L..
    -----------------------------------------------------------------------------------------------------------------------------------------------------------------------
 5: B.....V.....T.....C.....V.....E.....C.....W.....E.....E.....I.....L.....J.....A.....W.....K.....C.....W.....C.....J.....I.....D.....C.....L.....K.....Q.....X.....D....
 6: .Q.....V.....Z.....P.....G.....P.....B.....C.....E.....W.....A.....O.....O.....Z.....O.....Z.....Z.....U.....Z.....P.....O.....V.....E.....M.....Z.....Z.....S.....C...
 7: ..F.....S.....L.....Y.....R.....J.....M.....T.....B.....R.....H.....R.....M.....Y.....A.....J.....H.....Y.....I.....H.....L.....E.....Y.....N.....H.....Q.....L.....M..
 8: ...J.....O.....F.....N.....A.....Z.....Z.....K.....P.....P.....G.....S.....I.....N.....Z.....Z.....R.....T.....I.....O.....H.....Z.....K.....O.....R.....Q.....I.....Z.
 9: ....F.....W.....U.....M.....Z.....F.....X.....D.....D.....R.....F.....B.....C.....X.....B.....T.....P.....I.....T.....B.....U.....X.....F.....X.....V.....T.....B.....X
10: .....E.....V.....C.....S.....S.....D.....U.....K.....V.....W.....M.....G.....C.....S.....D.....N.....Y.....Y.....S.....U.....Y.....Y.....Q.....Y.....E.....E.....Y.....

Compressed array after 130 merge(s): 11 rows x 37 columns

              111111111122222222223333333
    0123456789012345678901234567890123456
 0: C.K.BD..ZU..LWR...M.H...P....A.X.S.VE
 1: .RV.L.Q..G...YXM..A..E.U..S.T...B....
 2: ..B.OQE..FXY.SJ.R.TI.M...............
 3: ..PVC..X.I.W.D...UG....Y.L.N..T...Z..
 4: ..Y.KA...L.P..F...X.Q.U.S............
    -------------------------------------
 5: B.I.VWD..JT..C.X..E....LK..A........Q
 6: .QZ.E.V..W.M.GP.SCO..B.A......U......
 7: ..F.RY.S.M.L.....EHJBQT.....A....I.N.
 8: K.OJI.A..R..FP.N..Z.S....G....QT..H..
 9: ..U.F...WX.V.BT.MZ...D.R..C..P..I....
10: ..C.YE..MV.S.QU...NKDG..W............
```

Running the compressed array though our tool complete-table.py:

```
D:\Private\Dev\MVS\Repositories\crypto\Crypt\Tools\CompleteReconstructionMatrix>python complete-table.py --allowdup < input\initial-table-my-AC-isolog-con.txt
Start time: 2026-06-02 14:34:18

=== Initial Matrix ===
0   C.K.BD..ZU..LWR...M.H...P....A.X.S.VE
1   .RV.L.Q..G...YXM..A..E.U..S.T...B....
2   ..B.OQE..FXY.SJ.R.TI.M...............
3   ..PVC..X.I.W.D...UG....Y.L.N..T...Z..
4   ..Y.KA...L.P..F...X.Q.U.S............
5   B.I.VWD..JT..C.X..E....LK..A........Q
6   .QZ.E.V..W.M.GP.SCO..B.A......U......
7   ..F.RY.S.M.L.....EHJBQT.....A....I.N.
8   K.OJI.A..R..FP.N..Z.S....G....QT..H..
9   ..U.F...WX.V.BT.MZ...D.R..C..P..I....
10  ..C.YE..MV.S.QU...NKDG..W............

=== Pass 1 ===
Complete rectangles: 10304
Incomplete rectangles: 40512

C(10-3):K(0-3):Y(10-5):B(0-5) -> C(0-1):K(0-3):?(2-1):B(2-3)
C(0-1):K(8-1):W(0-14):P(8-14) -> C(0-1):K(0-3):?(3-1):P(3-3)
C(3-5):K(4-5):P(3-3):Y(4-3) -> C(0-1):K(0-3):?(4-1):Y(4-3)
...
Q(1-7):E(2-7):G(1-10):F(2-10) -> Q(6-2):E(6-5):?(9-2):F(9-5)
W(6-10):J(5-10):V(6-7):D(5-7) -> W(6-10):?(6-21):V(10-10):D(10-21)
F(9-5):C(3-5):U(9-3):P(3-3) -> F(7-3):?(7-30):U(9-3):P(9-30)

New letters added this pass: 251
...
=== Final Matrix ===
0   CVKFBDZZZUNCLWRJFJMOHXFOPRDTGAAXPSDVE
1   ORVNLSQQQGZOJYXMNMAUCENUBXSDTWWEBKSRH
2   YLBROQEEEFXYUSJGRGTIWMRICJQZNDDMCPQLA
3   WBPVCZXXXIRWODLUVUGYAJVYHLZNFTTJHQZBM
4   PIYUKATTTLGPVHFRURXBQNUBSFAMJEENSWAIZ
5   BFIGVWDDDJTBRCNXGXELPZGLKNWAMHHZKYWFQ
6   MQZSEFVVVWKMHGPCSCOAJBSAXPFIYUUBXNFQL
7   LNFTRYSSSMDLXOZETEHJBQTJVZYWACCQVIYNP
8   KUOJIHAAARMKFPGNJNZVSTJVYGHEXQQTYCHUD
9   VGUMFCWWWXAVNBTZMZQRKDMRITCHEPPDIOCGS
10  SOCLYEMMMVJSIQUFLFNKDGLKWUEXRZZGWHEOT

End time:   2026-06-02 14:34:23
Elapsed:    0:00:04.922553
```

Using this completed reconstruction matrix enables us to reduce te polyalphabetic to a monoalphabetic.