# 076 confirmation (073 opened once; ea0.5w1 - 0.379 main)

- 073 fold 3: rows 429, molecules 366, views {'c2': 366, 'c1': 63}
- 073 fold 4: rows 455, molecules 381, views {'c2': 381, 'c1': 74}
- **073 NP C2 (H, N equal; blocks equal): +0.0246 [+0.0169, +0.0333]** | blocks f3 / f4 +0.0238 / +0.0254
    f3 NP_H c2: n 214 main 0.6253 -> 0.6342 (+0.0089; up 14 / down 0)
    f3 NP_H c1: n 36 main 0.9167 -> 0.8889 (-0.0278; up 0 / down 2)
    f3 NP_N c2: n 139 main 0.5505 -> 0.5891 (+0.0386; up 33 / down 0)
    f3 NP_N c1: n 27 main 0.8627 -> 0.8586 (-0.0040; up 1 / down 2)
    f3 NP_X c2: n 13 main 0.3821 -> 0.3883 (+0.0062; up 5 / down 0)
    f4 NP_H c2: n 268 main 0.5757 -> 0.5836 (+0.0079; up 15 / down 0)
    f4 NP_H c1: n 41 main 0.8844 -> 0.8823 (-0.0020; up 0 / down 1)
    f4 NP_N c2: n 110 main 0.5660 -> 0.6089 (+0.0429; up 22 / down 0)
    f4 NP_N c1: n 33 main 0.9038 -> 0.8712 (-0.0326; up 0 / down 4)
    f4 NP_X c2: n 3 main 0.6905 -> 0.6970 (+0.0065; up 1 / down 0)
- reach-conditional (truth in the view shortlist) NP C2: +0.0265 [+0.0183, +0.0354]
- **f3b/f4b G C1 (2 blocks equal): -0.0020 [-0.0069, +0.0028]** | blocks -0.0030 / -0.0011 | n [169, 167] | worsened [6, 2] improved [4, 1]
- f3b/f4b G C2 (C2 is non-worsening by construction): +0.0015
- stress: 073 NP_H C1 (non-timsTOF, new identities): -0.0149 [-0.0357, +0.0000]
- REGISTERED VERDICT: PASS (073 point >= +0.005: True; 073 lower > -0.01: True; G C1 lower > -0.01: True)
