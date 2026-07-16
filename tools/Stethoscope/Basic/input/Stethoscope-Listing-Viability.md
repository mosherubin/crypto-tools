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
| <code>MC-I 2 7</code> | 1 | <span style="background-color:#FF7F7F; padding:2px 8px;">No</span> | Alph | 'm' and 'n' freq counts are +/- 1 |
| <code>MC-I 2 13</code> | 3 | <span style="background-color:#FF7F7F; padding:2px 8px;">No</span> | Alph | True length=225, listing says 208 with 18 dits |
| <code>MC-I 3 5</code> | 5 | <span style="background-color:#FF7F7F; padding:2px 8px;">No</span> | Numeric | True length 240, not 236, freq count is off |
| <code>MC-I 3 6</code> | 7 | <span style="background-color:#FF7F7F; padding:2px 8px;">No</span> | Numeric | Listing says has 1 dit |
| <code>MC-I 3 7</code> | 9 | <span style="background-color:#90EE90; padding:2px 8px;">Yes</span> | Numeric | |
| <code>MC-I 4 3</code> | 11 | <span style="background-color:#90EE90; padding:2px 8px;">Yes</span> | Numeric | |
| <code>MC-I 4 4</code> | 13 | <span style="background-color:#90EE90; padding:2px 8px;">Yes</span> | Numeric | |
| <code>MC-I 4 5</code> | 15 | <span style="background-color:#90EE90; padding:2px 8px;">Yes</span> | Numeric | |
| <code>MC-I 4 7</code> | 17 | <span style="background-color:#FF7F7F; padding:2px 8px;">No</span> | Numeric | Rob Roy listing says 329 characters, really has 330.  Mono count of '9' is 36 and not 35 as in listing|
| <code>MC-I 4 8A</code> | 19 | <span style="background-color:#FF7F7F; padding:2px 8px;">No</span> | Numeric | Has a non-zero number (1) of dits|
| <code>MC-I 4 8B</code> | 21 | <span style="background-color:#FF7F7F; padding:2px 8px;">No</span> | Numeric | Has a non-zero number (1) of dits|
| <code>MC-I 4 9A</code> | 23 | <span style="background-color:#90EE90; padding:2px 8px;">Yes</span> | Numeric | |
| <code>MC-I 4 9B</code> | 25 | <span style="background-color:#90EE90; padding:2px 8px;">Yes</span> | Numeric | |
| <code>MC-I 5 1</code> | 27 | <span style="background-color:#FF7F7F; padding:2px 8px;">No</span> | Alph | Frequencies (G,Q) in Rob Roy is (28,19), should be (27,20).|
| <code>MC-I 6 1</code> | 29 | <span style="background-color:#90EE90; padding:2px 8px;">Yes</span> | Alph | |
| <code>MC-I 6 4</code> | 31 | <span style="background-color:#90EE90; padding:2px 8px;">Yes</span> | Alph | |
| <code>MC-I 6 5</code> | 33 | | | |
| <code>MC-I 7 4</code> | 35 | <span style="background-color:#FF7F7F; padding:2px 8px;">No</span> | Numeric | Count of '5' is really 23 and not 22, count of '6' is really 25 and not 26. NOTE: Although CT is groups of 3, the cuts are NOT shifted |
| <code>MC-I 7 5</code> | 37 | <span style="background-color:#90EE90; padding:2px 8px;">Yes</span> | Alph | BUG: The Tri- CUT results are shifted around, checking if it's the groups of 3 |
| <code>MC-I 7 6</code> | 39 | <span style="background-color:#FF7F7F; padding:2px 8px;">No</span> | Numeric | Really has 320 digits, it says it has 319 |
| <code>MC-I 8 1</code> | 41 | | | |
| <code>MC-I 8 3</code> | 43 | | | |
| <code>MC-I 8 6</code> | 45 | | | |
| <code>MC-I 8 7</code> | 47 | | | |
| <code>MC-I 8 9</code> | 49 | | | |
| <code>MC-I 9 1</code> | 51 | | | |
| <code>MC-I 9 2</code> | 53 | | | |
| <code>MC-I 10 2</code> | 55 | <span style="background-color:#90EE90; padding:2px 8px;">Yes</span> | Alph | |
| <code>MC-I 10 3</code> | 57 | <span style="background-color:#FF7F7F; padding:2px 8px;">No</span> | Alph | True length is 300, not 299 |
| <code>MC-I 10 4</code> | 59 | <span style="background-color:#90EE90; padding:2px 8px;">Yes</span> | Alph | |
| <code>MC-II 1 1</code> | 61 | | | |
| <code>MC-II 1 1*</code> | 63 | | | |
| <code>MC-II 1 2</code> | 65 | | | |
| <code>MC-II 1 2*</code> | 67 | | | |
| <code>MC-II 1 7</code> | 69 | | | |
| <code>MC-II 2 3</code> | 71 | | | |
| <code>MC-II 2 6a</code> | 73 | | | |
| <code>MC-II 2 6b</code> | 75 | | | |
| <code>MC-II 4 4</code> | 77 | | | |
| <code>MC-II 4 6</code> | 79 | | | |
| <code>MC-II 4 7</code> | 81 | | | |
| <code>MC-II 5 1</code> | 83 | | | |
| <code>MC-II 5 7</code> | 85 | | | |
| <code>MC-II 5 8</code> | 87 | | | |
| <code>MC-II 6 3/3</code> | 89 | | | |
| <code>MC-II 6 4/2</code> | 91 | | | |
| <code>MC-II 7 1</code> | 93 | | | |
| <code>MC-II 7 2</code> | 95 | <span style="background-color:#90EE90; padding:2px 8px;">Yes</span> | Alph | Last three letters are padding Xs |
| <code>MC-II 7 9</code> | 97 | | | |
| <code>MC-II 8 1</code> | 99 | | | |
| <code>MC-II 8 2</code> | 101 | | | |
| <code>MC-II 8 4</code> | 103 | | | |
| <code>MC-II 8 5</code> | 105 | | | |
| <code>MC-II 8 6</code> | 107 | | | |
| <code>MC-II 8 7A</code> | 109 | | | |
| <code>MC-II 9 1A</code> | 111 | | | |
| <code>MC-II 9 2A</code> | 113 | | | |
| <code>MC-II 9 2B</code> | 115 | | | |
| <code>MC-II 10 1</code> | 117 | | | |
| <code>MC-II 10 3A</code> | 119 | | | |
| <code>MC-II 10 3B</code> | 121 | | | |
| <code>MC-II 10 9</code> | 123 | | | |
| <code>MC-III 1 8</code> | 125 | | | |
| <code>MC-III 1 9</code> | 127 | | | |
| <code>MC-III 1 10</code> | 129 | | | |
| <code>MC-III 1 11a</code> | 131 | | | |
| <code>MC-III 1 11b</code> | 133 | | | |
| <code>MC-III 1 12</code> | 135 | | | |
| <code>MC-III 3 2</code> | 137 | | | |
| <code>MC-III 3 3</code> | 139 | | | |
| <code>MC-III 3 4</code> | 141 | | | |
| <code>MC-III 3 5</code> | 143 | | | |
| <code>MC-III 3 6A</code> | 145 | | | |
| <code>MC-III 3 6B</code> | 147 | | | |
| <code>MC-III 3 7</code> | 149 | | | |
| <code>MC-III 2 8a</code> | 151 | <span style="background-color:#FF7F7F; padding:2px 8px;">No</span> | Alphanumeric | Incorrectly identified as "MC-III 3 8a" in the Rob Roy listing.  The mono count is radically different from the ciphertext; the count should be (1, 4, 8, 5, 3, 2, 2, 4, 1, 0, 4, 1, 6, 2, 4, 3, 5, 0, 1, 1, 5, 2, 3, 2, 1, 0, 0, 0, 1, 3, 9, 0, 3, 1, 3, 0) |
| <code>MC-III 2 8b</code> | 153 | <span style="background-color:#FF7F7F; padding:2px 8px;">No</span> | Alphanumeric | Incorrectly identified as "MC-III 3 8b" in the Rob Roy listing. Rob Roy total is 119 while there are 120 characters, H=6 but should be 7. |

> **Note:** 

| Source | Page | Viable? | Alph/Numeric? | Comment |
|--------|-----:|:-------:|:-------------:|---------|
| <code>Z 295 AEFEA</code> | 155 | | | |
| <code>Z 240 CCFII</code> | 157 | | | |
| <code>Z 306 CCFII</code> | 159 | | | |
| <code>Z 311 CFIFC</code> | 161 | | | |
| <code>Z 085 CJCCJ</code> | 163 | | | |
| <code>Z 343 DAEAD</code> | 165 | | | |
| <code>Z 103 DCGCD</code> | 167 | | | |
| <code>Z 312 DCGCD</code> | 169 | | | |
| <code>Z 077 DDHAA</code> | 171 | | | |
| <code>Z 369 DDHAA</code> | 173 | <span style="background-color:#FF7F7F; padding:2px 8px;">No</span> | Alph | Listing says 473 with 3 dits (?) |
| <code>Z 262 DJDJD</code> | 175 | | | |
| <code>Z 011 ECHCE</code> | 177 | | | |
| <code>Z 161 EGBGE</code> | 179 | | | |
| <code>Z 020 FEAFE</code> | 181 | | | |
| <code>Z 084 FFBGG</code> | 183 | | | |
| <code>Z 319 FFBGG</code> | 185 | | | |
| <code>Z 107 GIFIG</code> | 187 | | | |
| <code>Z 017 HAIHA</code> | 189 | | | |
| <code>Z 298 HBJBH</code> | 191 | | | |
| <code>Z 042 IIHFF</code> | 193 | | | |
| <code>Z 060 IIHFF</code> | 195 | | | |
| <code>Z 091 JAAAJ</code> | 197 | | | |
| <code>Z 001 JGGJG</code> | 199 | | | |
| <code>Z 105 28082</code> | 201 | | | |
| <code>Z 106 28082</code> | 203 | | | |
| <code>Z 243 50505</code> | 205 | | | |
| <code>Z 314 50505</code> | 207 | | | |
| <code>Z 133 68486</code> | 209 | | | |
| <code>Z 284 68486</code> | 211 | | | |
| <code>Z 069 80808</code> | 213 | | | |
| <code>Z 359 80808</code> | 215 | | | |
| <code>Z 180 95459</code> | 217 | | | |
| <code>Z 313 95459</code> | 219 | | | |
| <code>D 100</code> | 221 | | | |
| <code>D 110</code> | 223 | | | |
| <code>D 111</code> | 225 | | | |
| <code>D 113</code> | 227 | | | |
| <code>D 114</code> | 229 | | | |
| <code>D 128A</code> | 231 | | | |
| <code>D 128B</code> | 233 | | | |
| <code>D 131</code> | 235 | | | |
| <code>D 137</code> | 237 | | | |
| <code>D 139</code> | 239 | | | |
| <code>D 141</code> | 241 | | | |
| <code>D 142</code> | 243 | | | |
| <code>D 143</code> | 245 | | | |
| <code>D 146A</code> | 247 | | | |
| <code>D 146B</code> | 249 | | | |
| <code>D 150</code> | 251 | | | |
| <code>D 151A</code> | 253 | | | |
| <code>D 151B</code> | 255 | | | |
| <code>D 152</code> | 257 | | | |
| <code>D 152A</code> | 259 | | | |
| <code>D 158</code> | 261 | | | |
| <code>D 159</code> | 263 | | | |
| <code>D 161</code> | 265 | | | |
| <code>D 165</code> | 267 | | | |
| <code>D 190</code> | 269 | | | |
| <code>D 195</code> | 271 | | | |
| <code>D 196</code> | 273 | | | |
| <code>D 206</code> | 275 | | | |
| <code>D 208</code> | 277 | | | |
| <code>D 210</code> | 279 | | | |
| <code>D 211</code> | 281 | | | |
| <code>D 212</code> | 283 | | | |
| <code>D 214</code> | 285 | | | |
| <code>D 218B</code> | 287 | | | |
| <code>D 219</code> | 289 | | | |
| <code>D 220</code> | 291 | | | |
| <code>D 222</code> | 293 | | | |
