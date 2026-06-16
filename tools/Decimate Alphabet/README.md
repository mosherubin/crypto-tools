# Decimate an Alphabet

Given an alphabet, this script will decimate the inputted alphabet.

# Usage

The command for running this script is:

```
usage: decimate-alphabet.py [-h] [--even] alphabet
```

# Examples

Here is an example of decimating the straight alphabet:

```
D:\Private\Dev\MVS\Repositories\crypto\Crypt\Tools\Decimate Alphabet>python decimate-alphabet.py abcdefghijklmnopqrstuvwxyz
  3: (adgjmpsvybehknqtwzcfilorux)
  5: (afkpuzejotydinsxchmrwbglqv)
  7: (ahovcjqxelszgnubipwdkryfmt)
  9: (ajsbktcludmvenwfoxgpyhqzir)
 11: (alwhsdozkvgrcnyjufqbmxitep)
 13: (an) (bo) (cp) (dq) (er) (fs) (gt) (hu) (iv) (jw) (kx) (ly) (mz)
 15: (apetixmbqfujyncrgvkzodshwl)
 17: (arizqhypgxofwnevmdulctkbsj)
 19: (atmfyrkdwpibungzslexqjcvoh)
 21: (avqlgbwrmhcxsnidytojezupkf)
 23: (axurolifczwtqnkhebyvspmjgd)
 25: (azyxwvutsrqponmlkjihgfedcb)
 ```

By default, the script skips all even decimation values.  If we add the "--even" flag, we get:

```
D:\Private\Dev\MVS\Repositories\crypto\Crypt\Tools\Decimate Alphabet>python decimate-alphabet.py --even abcdefghijklmnopqrstuvwxyz
  2: (acegikmoqsuwy) (bdfhjlnprtvxz)
  3: (adgjmpsvybehknqtwzcfilorux)
  4: (aeimquycgkosw) (bfjnrvzdhlptx)
  5: (afkpuzejotydinsxchmrwbglqv)
  6: (agmsyekqwciou) (bhntzflrxdjpv)
  7: (ahovcjqxelszgnubipwdkryfmt)
  8: (aiqygowemucks) (bjrzhpxfnvdlt)
  9: (ajsbktcludmvenwfoxgpyhqzir)
 10: (akueoyiscmwgq) (blvfpzjtdnxhr)
 11: (alwhsdozkvgrcnyjufqbmxitep)
 12: (amykwiugseqco) (bnzlxjvhtfrdp)
 13: (an) (bo) (cp) (dq) (er) (fs) (gt) (hu) (iv) (jw) (kx) (ly) (mz)
 14: (aocqesguiwkym) (bpdrfthvjxlzn)
 15: (apetixmbqfujyncrgvkzodshwl)
 16: (aqgwmcsiyoeuk) (brhxndtjzpfvl)
 17: (arizqhypgxofwnevmdulctkbsj)
 18: (askcumewogyqi) (btldvnfxphzrj)
 19: (atmfyrkdwpibungzslexqjcvoh)
 20: (auoicwqkeysmg) (bvpjdxrlfztnh)
 21: (avqlgbwrmhcxsnidytojezupkf)
 22: (awsokgcyuqmie) (bxtplhdzvrnjf)
 23: (axurolifczwtqnkhebyvspmjgd)
 24: (aywusqomkigec) (bzxvtrpnljhfd)
 25: (azyxwvutsrqponmlkjihgfedcb)
 ```
 
 Here's another example of doing this on a non-straight 20-character secondary alphabet:
 
 ```
D:\Private\Dev\MVS\Repositories\crypto\Crypt\Tools\Decimate Alphabet>python decimate-alphabet.py --even OWDPGJBCANRMULHKZIEQ
 2: (ODGBARUHZE) (WPJCNMLKIQ)
 3: (OPBNUKEWGCRLZQDJAMHI)
 4: (OGAUZ) (WJNLI) (DBRHE) (PCMKQ)
 5: (OJRK) (WBMZ) (DCUI) (PALE) (GNHQ)
 6: (OBUEGRZDAH) (WCLQJMIPNK)
 7: (OCHWAKDNZPRIGMEJUQBL)
 8: (OAZGU) (WNIJL) (DREBH) (PMQCK)
 9: (ONECZJHPUWRQAIBKGLDM)
10: (OR) (WM) (DU) (PL) (GH) (JK) (BZ) (CI) (AE) (NQ)
11: (OMDLGKBIAQRWUPHJZCEN)
12: (OUGZA) (WLJIN) (DHBER) (PKCQM)
13: (OLBQUJEMGIRPZNDKAWHC)
14: (OHADZRGEUB) (WKNPIMJQLC)
15: (OKRJ) (WZMB) (DIUC) (PELA) (GQHN)
16: (OZUAG) (WILNJ) (DEHRB) (PQKMC)
17: (OIHMAJDQZLRCGWEKUNBP)
18: (OEZHURABGD) (WQIKLMNCJP)
19: (OQEIZKHLUMRNACBJGPDW)
```
 
 The 20-character secondary alphabet comes from the Haganah worksheet in Danny Rosenne's paper titled "[British Intelligence Superiority in Palestine and Its Reliance on Breaking Haganah Ciphers, 1942-1948](https://www.amutakesher.org.il/_Uploads/dbsAttachedFiles/British_Intelligence_Superiority_in_Palestine_1.01.pdf)".

A decimation value of 18 shows:

```
18: (OEZHURABGD) (WQIKLMNCJP)
```

The first cycle shows the letters in Hebrew alphabetical order "ABGDOEZHUR" (where 'R' is an anomaly here), while the second cycle completes the alphabet with "IKLMNCJPWQ".  The tool was especially useful in this case for quickly recognizing an important decimation value.