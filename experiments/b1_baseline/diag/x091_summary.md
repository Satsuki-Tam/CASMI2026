# 091 development reading (per-spectrum FPNet logit mean vs PC-recomputed merged input)

tables missing (stress only): ['p2dev']

- **Primary (f1/f2 NP strict C2, fp_s - fp_m)**: +0.0016 [-0.0028, +0.0064] (fold 1 -0.0015, fold 2 +0.0046)
- G C1 (f1/f2): +0.0079 [-0.0096, +0.0264] (non-inferior); 053 NP C1: -0.0032 [-0.0109, +0.0012] (undetermined); panel C1 clean: +0.0051 [-0.0001, +0.0127] (non-inferior)
- **GATE to the pipeline implementation: FAIL**

- 053 dev C2 (NP_H/X/N, f1/f2 blocks): +0.0005 [-0.0049, +0.0059]
- reference fp_s main - table main (incl. platform noise), f1/f2 NP C2: +0.0012 [-0.0033, +0.0061]; fp_m main - table main: -0.0003 [-0.0010, +0.0003]
- f1/f2 NP C2 query spectra 1 (n 424): +0.0000 [+0.0000, +0.0000]
- f1/f2 NP C2 2-3 (n 235): +0.0087 [-0.0020, +0.0209]
- f1/f2 NP C2 4+ (n 134): -0.0061 [-0.0251, +0.0146]
- f1/f2 NP C2 truth COCONUT (n 275): +0.0009 [-0.0051, +0.0093]
- f1/f2 NP C2 truth not COCONUT (n 525): +0.0022 [-0.0036, +0.0084]
- f1/f2 NP C2 GL path (n 386): +0.0037 [-0.0055, +0.0137]
- f1/f2 NP C2 fallback (n 414): -0.0004 [-0.0018, +0.0007]
- 053 C2 query spectra 1 (n 233): +0.0000
- 053 C2 query spectra 2-3 (n 151): -0.0004
- 053 C2 query spectra 4+ (n 249): +0.0017
