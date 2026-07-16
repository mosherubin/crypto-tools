---
title: "Stethoscope Listing Viability"
author: "Moshe Rubin"
date: "22 June 2026"
header-includes: |
  <style>
  table { border-collapse: collapse; width: 100%; }
  th, td { border: 1px solid #888; padding: 6px 10px; }
  th { background-color: #f0f0f0; }
  tr:nth-child(even) { background-color: #f9f9f9; }
  </style>
---

# Stethoscope Listing Viability

*22 June 2026*

This document records which of Callimahos's 147 STETHOSCOPE listings are viable.
By "viable" we mean that the listing does not have obvious errors in it (e.g., it
says it has "dits" or garbled characters, or the frequency count is incorrect). Any
non-viable listing cannot be used for testing our STETHOSCOPE tool implementation.

Source Legend:

- **MC-I [lesson] [problem]** = Problem Book Course, Military Cryptanalytics, Part I
- **MC-II [section] [problem]** = Military Cryptanalytics, Part II, Section 3, Appendix 9 (page 671)
- **MC-III [section] [problem]** = Military Cryptanalytics, Part III, Appendix 7 (page 611)
- **Z [num]** = Zendian problem, Military Cryptanalytics, Part II, Section 3, Appendix 8 (page 273)
- **D [num]** = D-series of diagnostic problems ("Problems in Cryptanalytic Diagnosis") [classified, not available]

| Source | Page | Viable? | Alph/Numeric? | Comment |
|--------|-----:|:-------:|:-------------:|---------|
| MC-I 2 7 | 1 | No | Alph | 'm' and 'n' freq counts are +/- 1 |
| MC-I 2 13 | 3 | No | Alph | True length=225, listing says 208 with 18 dits |
| MC-I 3 5 | 5 | No | Numeric | True length 240, not 236, freq count is off |
| MC-I 3 6 | 7 | No | Numeric | Listing says has 1 dit |
| MC-I 3 7 | 9 | Yes | Numeric | |
| MC-I 4 3 | 11 | Yes | Numeric | |
| MC-I 4 4 | 13 | Yes | Numeric | |
| MC-I 4 5 | 15 | Yes | Numeric | |
| MC-I 4 7 | 17 | No | Numeric | Rob Roy listing says 329 characters, really has 330.  Mono count of '9' is 36 and not 35 as in listing|
| MC-I 4 8A | 19 | No | Numeric | Has a non-zero number (1) of dits|
| MC-I 4 8B | 21 | No | Numeric | Has a non-zero number (1) of dits|
| MC-I 4 9A | 23 | Yes | Numeric | |
| MC-I 4 9B | 25 | Yes | Numeric | |
| MC-I 5 1 | 27 | No | Alph | Frequencies (G,Q) in Rob Roy is (28,19), should be (27,20).|
| MC-I 6 1 | 29 | Yes | Alph | |
| MC-I 6 4 | 31 | Yes | Alph | |
| MC-I 6 5 | 33 | | | |
| MC-I 7 4 | 35 | No | Numeric | Count of '5' is really 23 and not 22, count of '6' is really 25 and not 26. NOTE: Although CT is groups of 3, the cuts are NOT shifted |
| MC-I 7 5 | 37 | Yes | Alph | BUG: The Tri- CUT results are shifted around, checking if it's the groups of 3 |
| MC-I 7 6 | 39 | No | Numeric | Really has 320 digits, it says it has 319 |
| MC-I 8 1 | 41 | | | |
| MC-I 8 3 | 43 | | | |
| MC-I 8 6 | 45 | | | |
| MC-I 8 7 | 47 | | | |
| MC-I 8 9 | 49 | | | |
| MC-I 9 1 | 51 | | | |
| MC-I 9 2 | 53 | | | |
| MC-I 10 2 | 55 | Yes | Alph | |
| MC-I 10 3 | 57 | No | Alph | True length is 300, not 299 |
| MC-I 10 4 | 59 | Yes | Alph | |
| MC-II 1 1 | 61 | | | |
| MC-II 1 1* | 63 | | | |
| MC-II 1 2 | 65 | | | |
| MC-II 1 2* | 67 | | | |
| MC-II 1 7 | 69 | | | |
| MC-II 2 3 | 71 | | | |
| MC-II 2 6a | 73 | | | |
| MC-II 2 6b | 75 | | | |
| MC-II 4 4 | 77 | | | |
| MC-II 4 6 | 79 | | | |
| MC-II 4 7 | 81 | | | |
| MC-II 5 1 | 83 | | | |
| MC-II 5 7 | 85 | | | |
| MC-II 5 8 | 87 | | | |
| MC-II 6 3/3 | 89 | | | |
| MC-II 6 4/2 | 91 | | | |
| MC-II 7 1 | 93 | | | |
| MC-II 7 2 | 95 | Yes | Alph | Last three letters are padding Xs |
| MC-II 7 9 | 97 | | | |
| MC-II 8 1 | 99 | | | |
| MC-II 8 2 | 101 | | | |
| MC-II 8 4 | 103 | | | |
| MC-II 8 5 | 105 | | | |
| MC-II 8 6 | 107 | | | |
| MC-II 8 7A | 109 | | | |
| MC-II 9 1A | 111 | | | |
| MC-II 9 2A | 113 | | | |
| MC-II 9 2B | 115 | | | |
| MC-II 10 1 | 117 | | | |
| MC-II 10 3A | 119 | | | |
| MC-II 10 3B | 121 | | | |
| MC-II 10 9 | 123 | | | |
| MC-III 1 8 | 125 | | | |
| MC-III 1 9 | 127 | | | |
| MC-III 1 10 | 129 | | | |
| MC-III 1 11a | 131 | | | |
| MC-III 1 11b | 133 | | | |
| MC-III 1 12 | 135 | | | |
| MC-III 3 2 | 137 | | | |
| MC-III 3 3 | 139 | | | |
| MC-III 3 4 | 141 | | | |
| MC-III 3 5 | 143 | | | |
| MC-III 3 6A | 145 | | | |
| MC-III 3 6B | 147 | | | |
| MC-III 3 7 | 149 | | | |
| MC-III 2 8a | 151 | No | Alphanumeric | Incorrectly identified as "MC-III 3 8a" in the Rob Roy listing.  The mono count is radically different from the ciphertext; the count should be (1, 4, 8, 5, 3, 2, 2, 4, 1, 0, 4, 1, 6, 2, 4, 3, 5, 0, 1, 1, 5, 2, 3, 2, 1, 0, 0, 0, 1, 3, 9, 0, 3, 1, 3, 0) |
| MC-III 2 8b | 153 | No | Alphanumeric | Incorrectly identified as "MC-III 3 8b" in the Rob Roy listing. Rob Roy total is 119 while there are 120 characters, H=6 but should be 7. |

> **Note:** 

| Source | Page | Viable? | Alph/Numeric? | Comment |
|--------|-----:|:-------:|:-------------:|---------|
| Z 295 AEFEA | 155 | | | |
| Z 240 CCFII | 157 | | | |
| Z 306 CCFII | 159 | | | |
| Z 311 CFIFC | 161 | | | |
| Z 085 CJCCJ | 163 | | | |
| Z 343 DAEAD | 165 | | | |
| Z 103 DCGCD | 167 | | | |
| Z 312 DCGCD | 169 | | | |
| Z 077 DDHAA | 171 | | | |
| Z 369 DDHAA | 173 | No | Alph | Listing says 473 with 3 dits (?) |
| Z 262 DJDJD | 175 | | | |
| Z 011 ECHCE | 177 | | | |
| Z 161 EGBGE | 179 | | | |
| Z 020 FEAFE | 181 | | | |
| Z 084 FFBGG | 183 | | | |
| Z 319 FFBGG | 185 | | | |
| Z 107 GIFIG | 187 | | | |
| Z 017 HAIHA | 189 | | | |
| Z 298 HBJBH | 191 | | | |
| Z 042 IIHFF | 193 | | | |
| Z 060 IIHFF | 195 | | | |
| Z 091 JAAAJ | 197 | | | |
| Z 001 JGGJG | 199 | | | |
| Z 105 28082 | 201 | | | |
| Z 106 28082 | 203 | | | |
| Z 243 50505 | 205 | | | |
| Z 314 50505 | 207 | | | |
| Z 133 68486 | 209 | | | |
| Z 284 68486 | 211 | | | |
| Z 069 80808 | 213 | | | |
| Z 359 80808 | 215 | | | |
| Z 180 95459 | 217 | | | |
| Z 313 95459 | 219 | | | |
| D 100 | 221 | | | |
| D 110 | 223 | | | |
| D 111 | 225 | | | |
| D 113 | 227 | | | |
| D 114 | 229 | | | |
| D 128A | 231 | | | |
| D 128B | 233 | | | |
| D 131 | 235 | | | |
| D 137 | 237 | | | |
| D 139 | 239 | | | |
| D 141 | 241 | | | |
| D 142 | 243 | | | |
| D 143 | 245 | | | |
| D 146A | 247 | | | |
| D 146B | 249 | | | |
| D 150 | 251 | | | |
| D 151A | 253 | | | |
| D 151B | 255 | | | |
| D 152 | 257 | | | |
| D 152A | 259 | | | |
| D 158 | 261 | | | |
| D 159 | 263 | | | |
| D 161 | 265 | | | |
| D 165 | 267 | | | |
| D 190 | 269 | | | |
| D 195 | 271 | | | |
| D 196 | 273 | | | |
| D 206 | 275 | | | |
| D 208 | 277 | | | |
| D 210 | 279 | | | |
| D 211 | 281 | | | |
| D 212 | 283 | | | |
| D 214 | 285 | | | |
| D 218B | 287 | | | |
| D 219 | 289 | | | |
| D 220 | 291 | | | |
| D 222 | 293 | | | |
