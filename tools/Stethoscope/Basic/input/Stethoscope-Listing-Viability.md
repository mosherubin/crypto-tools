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
By "viable" we mean that the listing does not have obvious errors in it. Any
non-viable listing cannot be used for testing our STETHOSCOPE tool implementation.

| Source | Page | Viable? | Alph/Numeric? | Comment |
|--------|-----:|:-------:|:-------------:|---------|
| I 2 7 | 1 | No | Alph | 'm' and 'n' freq counts are +/- 1 |
| I 2 13 | 3 | No | Alph | True length=225, listing says 208 with 18 dits |
| I 3 5 | 5 | No | Numeric | True length 240, not 236, freq count is off |
| I 3 6 | 7 | No | Numeric | Listing says has 1 dit |
| I 3 7 | 9 | Yes | Numeric | |
| I 4 3 | 11 | Yes | Numeric | |
| I 4 4 | 13 | Yes | Numeric | |
| I 4 5 | 15 | Yes | Numeric | |
| I 4 7 | 17 | No | Numeric | Rob Roy listing says 329 characters, really has 330.  Mono count of '9' is 36 and not 35 as in listing|
| I 4 8A | 19 | No | Numeric | Has a non-zero number (1) of dits|
| I 4 8B | 21 | No | Numeric | Has a non-zero number (1) of dits|
| I 4 9A | 23 | Yes | Numeric | |
| I 4 9B | 25 | Yes | Numeric | |
| I 5 1 | 27 | | | |
| I 6 1 | 29 | | | |
| I 6 4 | 31 | | | |
| I 6 5 | 33 | | | |
| I 7 4 | 35 | No | Numeric | Count of '5' is really 23 and not 22, count of '6' is really 25 and not 26. NOTE: Although CT is groups of 3, the cuts are NOT shifted |
| I 7 5 | 37 | Yes | Alph | BUG: The Tri- CUT results are shifted around, checking if it's the groups of 3 |
| I 7 6 | 39 | No | Numeric | Really has 320 digits, it says it has 319 |
| I 8 1 | 41 | | | |
| I 8 3 | 43 | | | |
| I 8 6 | 45 | | | |
| I 8 7 | 47 | | | |
| I 8 9 | 49 | | | |
| I 9 1 | 51 | | | |
| I 9 2 | 53 | | | |
| I 10 2 | 55 | Yes | Alph | |
| I 10 3 | 57 | No | Alph | True length is 300, not 299 |
| I 10 4 | 59 | Yes | Alph | |
| II 1 1 | 61 | | | |
| II 1 1* | 63 | | | |
| II 1 2 | 65 | | | |
| II 1 2* | 67 | | | |
| II 1 7 | 69 | | | |
| II 2 3 | 71 | | | |
| II 2 6a | 73 | | | |
| II 2 6b | 75 | | | |
| II 4 4 | 77 | | | |
| II 4 6 | 79 | | | |
| II 4 7 | 81 | | | |
| II 5 1 | 83 | | | |
| II 5 7 | 85 | | | |
| II 5 8 | 87 | | | |
| II 6 3/3 | 89 | | | |
| II 6 4/2 | 91 | | | |
| II 7 1 | 93 | | | |
| II 7 2 | 95 | Yes | Alph | Last three letters are padding Xs |
| II 7 9 | 97 | | | |
| II 8 1 | 99 | | | |
| II 8 2 | 101 | | | |
| II 8 4 | 103 | | | |
| II 8 5 | 105 | | | |
| II 8 6 | 107 | | | |
| II 8 7A | 109 | | | |
| II 9 1A | 111 | | | |
| II 9 2A | 113 | | | |
| II 9 2B | 115 | | | |
| II 10 1 | 117 | | | |
| II 10 3A | 119 | | | |
| II 10 3B | 121 | | | |
| II 10 9 | 123 | | | |
| III 1 8 | 125 | | | |
| III 1 9 | 127 | | | |
| III 1 10 | 129 | | | |
| III 1 11a | 131 | | | |
| III 1 11b | 133 | | | |
| III 1 12 | 135 | | | |
| III 3 2 | 137 | | | |
| III 3 3 | 139 | | | |
| III 3 4 | 141 | | | |
| III 3 5 | 143 | | | |
| III 3 6A | 145 | | | |
| III 3 6B | 147 | | | |
| III 7 7 | 149 | | | |
| III 3 8A | 151 | | | |
| III 3 8B | 153 | | | |

> **Note:** Remove two groups from start and end = reduce by 20

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
