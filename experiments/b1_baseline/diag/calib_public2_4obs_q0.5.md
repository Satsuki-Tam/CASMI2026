# Two-stage Public-calibrated prediction: 3,000,000 draws, accepted 40

observed (stage 1, fold-0 configurations) {'main': 0.354, 'insurance': 0.336, 'pc': 0.046, 'pool': 0.336} | check {'fe_main': 0.37} | tol diff 0.015, level 0.03 | q_seen 0.5

| type | n local | fold-0 main | insurance | pool | pc | pcd0.5 | pcd1 | pcd2 | posterior weight mean [5%, 95%] |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| C1 panel | 250 | 0.882 | 0.865 | 0.898 | 0.000 | 0.888 | 0.890 | 0.891 | 0.104 [0.019, 0.199] |
| C1 hard NP dev2 | 290 | 0.697 | 0.651 | 0.817 | 0.000 | 0.715 | 0.739 | 0.775 | 0.102 [0.017, 0.212] |
| C1 W7 NP | 71 | 0.913 | 0.744 | 0.943 | 0.000 | 0.914 | 0.917 | 0.935 | 0.027 [0.002, 0.067] |
| C2 COCONUT panel | 249 | 0.904 | 0.858 | 0.917 | 0.000 | 0.906 | 0.907 | 0.911 | 0.066 [0.005, 0.168] |
| C2 COCONUT dev2 | 119 | 0.549 | 0.489 | 0.596 | 0.000 | 0.560 | 0.570 | 0.579 | 0.068 [0.006, 0.183] |
| C2 COCONUT W7 NP | 48 | 0.731 | 0.566 | 0.748 | 0.000 | 0.731 | 0.732 | 0.733 | 0.032 [0.007, 0.070] |
| C2 PubChem-only dev2 | 226 | 0.587 | 0.515 | 0.000 | 0.637 | 0.561 | 0.549 | 0.523 | 0.019 [0.001, 0.047] |
| C2 PubChem-only W7 timsTOF | 283 | 0.837 | 0.684 | 0.000 | 0.846 | 0.833 | 0.827 | 0.812 | 0.017 [0.002, 0.038] |
| C2 PubChem-only W7 NP | 122 | 0.801 | 0.694 | 0.000 | 0.829 | 0.786 | 0.772 | 0.727 | 0.018 [0.004, 0.041] |
| zero under every configuration | 0 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.547 [0.510, 0.591] |

| class share (proxy weights, not the hidden class composition) | mean [5%, 95%] |
|---|---|
| class-1 proxies | 0.233 [0.099, 0.341] |
| class-2 COCONUT-truth proxies | 0.166 [0.056, 0.320] |
| class-2 PubChem-only-truth proxies | 0.054 [0.033, 0.070] |
| zero under every configuration | 0.547 [0.510, 0.591] |

| configuration | predicted Public delta vs 0.354 mean [5%, 95%] | imputed cells -> 0 | check |
|---|---|---|---|
| pcd0.5 | +0.0025 [+0.0011, +0.0046] | +0.0025 |  |
| pcd1 | +0.0054 [+0.0022, +0.0098] | +0.0054 |  |
| pcd2 | +0.0091 [+0.0037, +0.0168] | +0.0091 |  |
| pcd4 | +0.0115 [+0.0038, +0.0209] | +0.0115 |  |
| pool | -0.0206 [-0.0316, -0.0068] | -0.0206 |  |
| pc | -0.3061 [-0.3188, -0.2935] | -0.3061 |  |
| insurance | -0.0293 [-0.0327, -0.0244] | -0.0293 |  |
| fe_main (full_eval + rank_v4b, submitted) | -0.0009 [-0.0055, +0.0023] | +0.0005 | 0.37 |
| fe_new (full_eval + rank_rk_fx) | -0.0019 [-0.0107, +0.0044] | +0.0011 |  |
| rk_old (full_rk + rank_v4b) | -0.0027 [-0.0061, +0.0002] | -0.0016 |  |
| rk_new (full_rk + rank_rk_fx) | -0.0033 [-0.0118, +0.0030] | -0.0005 |  |

Per-type deltas used in stage 2:

- pcd0.5: C1 panel +0.006; C1 hard NP dev2 +0.019; C1 W7 NP +0.001; C2 COCONUT panel +0.002; C2 COCONUT dev2 +0.011; C2 COCONUT W7 NP +0.000; C2 PubChem-only dev2 -0.027; C2 PubChem-only W7 timsTOF -0.004; C2 PubChem-only W7 NP -0.015
  - C1 panel: measured (n 250) | C1 hard NP dev2: measured (n 290) | C1 W7 NP: measured (n 71) | C2 COCONUT panel: measured (n 249) | C2 COCONUT dev2: measured (n 119) | C2 COCONUT W7 NP: measured (n 48) | C2 PubChem-only dev2: measured (n 226) | C2 PubChem-only W7 timsTOF: measured (n 283) | C2 PubChem-only W7 NP: measured (n 122)
- pcd1: C1 panel +0.008; C1 hard NP dev2 +0.042; C1 W7 NP +0.003; C2 COCONUT panel +0.002; C2 COCONUT dev2 +0.021; C2 COCONUT W7 NP +0.001; C2 PubChem-only dev2 -0.038; C2 PubChem-only W7 timsTOF -0.010; C2 PubChem-only W7 NP -0.029
  - C1 panel: measured (n 250) | C1 hard NP dev2: measured (n 290) | C1 W7 NP: measured (n 71) | C2 COCONUT panel: measured (n 249) | C2 COCONUT dev2: measured (n 119) | C2 COCONUT W7 NP: measured (n 48) | C2 PubChem-only dev2: measured (n 226) | C2 PubChem-only W7 timsTOF: measured (n 283) | C2 PubChem-only W7 NP: measured (n 122)
- pcd2: C1 panel +0.009; C1 hard NP dev2 +0.078; C1 W7 NP +0.021; C2 COCONUT panel +0.006; C2 COCONUT dev2 +0.030; C2 COCONUT W7 NP +0.002; C2 PubChem-only dev2 -0.065; C2 PubChem-only W7 timsTOF -0.025; C2 PubChem-only W7 NP -0.074
  - C1 panel: measured (n 250) | C1 hard NP dev2: measured (n 290) | C1 W7 NP: measured (n 71) | C2 COCONUT panel: measured (n 249) | C2 COCONUT dev2: measured (n 119) | C2 COCONUT W7 NP: measured (n 48) | C2 PubChem-only dev2: measured (n 226) | C2 PubChem-only W7 timsTOF: measured (n 283) | C2 PubChem-only W7 NP: measured (n 122)
- pcd4: C1 panel +0.014; C1 hard NP dev2 +0.108; C1 W7 NP +0.029; C2 COCONUT panel +0.011; C2 COCONUT dev2 +0.039; C2 COCONUT W7 NP +0.016; C2 PubChem-only dev2 -0.117; C2 PubChem-only W7 timsTOF -0.096; C2 PubChem-only W7 NP -0.098
  - C1 panel: measured (n 250) | C1 hard NP dev2: measured (n 290) | C1 W7 NP: measured (n 71) | C2 COCONUT panel: measured (n 249) | C2 COCONUT dev2: measured (n 119) | C2 COCONUT W7 NP: measured (n 48) | C2 PubChem-only dev2: measured (n 226) | C2 PubChem-only W7 timsTOF: measured (n 283) | C2 PubChem-only W7 NP: measured (n 122)
- pool: C1 panel +0.016; C1 hard NP dev2 +0.120; C1 W7 NP +0.030; C2 COCONUT panel +0.013; C2 COCONUT dev2 +0.048; C2 COCONUT W7 NP +0.017; C2 PubChem-only dev2 -0.587; C2 PubChem-only W7 timsTOF -0.837; C2 PubChem-only W7 NP -0.801
  - C1 panel: measured (n 250) | C1 hard NP dev2: measured (n 290) | C1 W7 NP: measured (n 71) | C2 COCONUT panel: measured (n 249) | C2 COCONUT dev2: measured (n 119) | C2 COCONUT W7 NP: measured (n 48) | C2 PubChem-only dev2: measured (n 226) | C2 PubChem-only W7 timsTOF: measured (n 283) | C2 PubChem-only W7 NP: measured (n 122)
- pc: C1 panel -0.882; C1 hard NP dev2 -0.697; C1 W7 NP -0.913; C2 COCONUT panel -0.904; C2 COCONUT dev2 -0.549; C2 COCONUT W7 NP -0.731; C2 PubChem-only dev2 +0.050; C2 PubChem-only W7 timsTOF +0.009; C2 PubChem-only W7 NP +0.028
  - C1 panel: measured (n 250) | C1 hard NP dev2: measured (n 290) | C1 W7 NP: measured (n 71) | C2 COCONUT panel: measured (n 249) | C2 COCONUT dev2: measured (n 119) | C2 COCONUT W7 NP: measured (n 48) | C2 PubChem-only dev2: measured (n 226) | C2 PubChem-only W7 timsTOF: measured (n 283) | C2 PubChem-only W7 NP: measured (n 122)
- insurance: C1 panel -0.016; C1 hard NP dev2 -0.045; C1 W7 NP -0.169; C2 COCONUT panel -0.047; C2 COCONUT dev2 -0.059; C2 COCONUT W7 NP -0.164; C2 PubChem-only dev2 -0.073; C2 PubChem-only W7 timsTOF -0.153; C2 PubChem-only W7 NP -0.107
  - C1 panel: measured (n 250) | C1 hard NP dev2: measured (n 290) | C1 W7 NP: measured (n 71) | C2 COCONUT panel: measured (n 249) | C2 COCONUT dev2: measured (n 119) | C2 COCONUT W7 NP: measured (n 48) | C2 PubChem-only dev2: measured (n 226) | C2 PubChem-only W7 timsTOF: measured (n 283) | C2 PubChem-only W7 NP: measured (n 122)
- fe_main (full_eval + rank_v4b, submitted): C1 panel +0.015; C1 hard NP dev2 +0.002; C1 W7 NP +0.015 (imp); C2 COCONUT panel -0.020 (imp); C2 COCONUT dev2 -0.020; C2 COCONUT W7 NP -0.020 (imp); C2 PubChem-only dev2 +0.004; C2 PubChem-only W7 timsTOF +0.004 (imp); C2 PubChem-only W7 NP +0.004 (imp)
  - C1 panel: (1-q_seen) x measured (n 250), seen part 0 | C1 hard NP dev2: (1-q_seen) x measured (n 290), seen part 0 | C1 W7 NP: imputed from C1 panel | C2 COCONUT panel: imputed from C2 COCONUT dev2 | C2 COCONUT dev2: measured (n 119) | C2 COCONUT W7 NP: imputed from C2 COCONUT dev2 | C2 PubChem-only dev2: measured (n 226) | C2 PubChem-only W7 timsTOF: imputed from C2 PubChem-only dev2 | C2 PubChem-only W7 NP: imputed from C2 PubChem-only dev2
- fe_new (full_eval + rank_rk_fx): C1 panel +0.024; C1 hard NP dev2 +0.012; C1 W7 NP +0.024 (imp); C2 COCONUT panel -0.038 (imp); C2 COCONUT dev2 -0.038; C2 COCONUT W7 NP -0.038 (imp); C2 PubChem-only dev2 +0.002; C2 PubChem-only W7 timsTOF +0.002 (imp); C2 PubChem-only W7 NP +0.002 (imp)
  - C1 panel: (1-q_seen) x measured (n 250), seen part 0 | C1 hard NP dev2: (1-q_seen) x measured (n 290), seen part 0 | C1 W7 NP: imputed from C1 panel | C2 COCONUT panel: imputed from C2 COCONUT dev2 | C2 COCONUT dev2: measured (n 119) | C2 COCONUT W7 NP: imputed from C2 COCONUT dev2 | C2 PubChem-only dev2: measured (n 226) | C2 PubChem-only W7 timsTOF: imputed from C2 PubChem-only dev2 | C2 PubChem-only W7 NP: imputed from C2 PubChem-only dev2
- rk_old (full_rk + rank_v4b): C1 panel +0.015; C1 hard NP dev2 -0.006; C1 W7 NP +0.008; C2 COCONUT panel -0.018 (imp); C2 COCONUT dev2 -0.018; C2 COCONUT W7 NP -0.022; C2 PubChem-only dev2 +0.002; C2 PubChem-only W7 timsTOF -0.023; C2 PubChem-only W7 NP -0.031
  - C1 panel: (1-q_seen) x measured (n 250), seen part 0 | C1 hard NP dev2: (1-q_seen) x measured (n 290), seen part 0 | C1 W7 NP: (1-q_seen) x measured (n 71), seen part 0 | C2 COCONUT panel: imputed from C2 COCONUT dev2 | C2 COCONUT dev2: measured (n 119) | C2 COCONUT W7 NP: measured (n 27) | C2 PubChem-only dev2: measured (n 226) | C2 PubChem-only W7 timsTOF: measured (n 278) | C2 PubChem-only W7 NP: measured (n 80)
- rk_new (full_rk + rank_rk_fx): C1 panel +0.019; C1 hard NP dev2 +0.008; C1 W7 NP +0.017; C2 COCONUT panel -0.043 (imp); C2 COCONUT dev2 -0.043; C2 COCONUT W7 NP -0.021; C2 PubChem-only dev2 +0.008; C2 PubChem-only W7 timsTOF +0.008; C2 PubChem-only W7 NP -0.025
  - C1 panel: (1-q_seen) x measured (n 250), seen part 0 | C1 hard NP dev2: (1-q_seen) x measured (n 290), seen part 0 | C1 W7 NP: (1-q_seen) x measured (n 71), seen part 0 | C2 COCONUT panel: imputed from C2 COCONUT dev2 | C2 COCONUT dev2: measured (n 119) | C2 COCONUT W7 NP: measured (n 27) | C2 PubChem-only dev2: measured (n 226) | C2 PubChem-only W7 timsTOF: measured (n 278) | C2 PubChem-only W7 NP: measured (n 80)