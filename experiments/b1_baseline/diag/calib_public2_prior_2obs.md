# Two-stage Public-calibrated prediction: 500,000 draws, accepted 70

observed (stage 1, fold-0 configurations) {'main': 0.354, 'insurance': 0.336} | check {} | tol diff 0.015, level 0.03 | q_seen 0.8

| type | n local | fold-0 main | insurance | pool | pc | pcd0.5 | pcd1 | pcd2 | posterior weight mean [5%, 95%] |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| C1 panel | 250 | 0.882 | 0.865 | 0.898 | 0.000 | 0.888 | 0.890 | 0.891 | 0.103 [0.017, 0.205] |
| C1 hard NP dev2 | 290 | 0.697 | 0.651 | 0.817 | 0.000 | 0.715 | 0.739 | 0.775 | 0.080 [0.008, 0.215] |
| C1 W7 NP | 71 | 0.913 | 0.744 | 0.943 | 0.000 | 0.914 | 0.917 | 0.935 | 0.023 [0.002, 0.062] |
| C2 COCONUT panel | 249 | 0.904 | 0.858 | 0.917 | 0.000 | 0.906 | 0.907 | 0.911 | 0.069 [0.007, 0.165] |
| C2 COCONUT dev2 | 119 | 0.549 | 0.489 | 0.596 | 0.000 | 0.560 | 0.570 | 0.579 | 0.072 [0.008, 0.177] |
| C2 COCONUT W7 NP | 48 | 0.731 | 0.566 | 0.748 | 0.000 | 0.731 | 0.732 | 0.733 | 0.019 [0.002, 0.051] |
| C2 PubChem-only dev2 | 226 | 0.587 | 0.515 | 0.000 | 0.637 | 0.561 | 0.549 | 0.523 | 0.039 [0.004, 0.120] |
| C2 PubChem-only W7 timsTOF | 283 | 0.837 | 0.684 | 0.000 | 0.846 | 0.833 | 0.827 | 0.812 | 0.024 [0.001, 0.064] |
| C2 PubChem-only W7 NP | 122 | 0.801 | 0.694 | 0.000 | 0.829 | 0.786 | 0.772 | 0.727 | 0.035 [0.003, 0.092] |
| zero under every configuration | 0 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.535 [0.480, 0.586] |

| class share (proxy weights, not the hidden class composition) | mean [5%, 95%] |
|---|---|
| class-1 proxies | 0.206 [0.096, 0.331] |
| class-2 COCONUT-truth proxies | 0.161 [0.055, 0.272] |
| class-2 PubChem-only-truth proxies | 0.098 [0.033, 0.189] |
| zero under every configuration | 0.535 [0.480, 0.586] |

| configuration | predicted Public delta vs 0.354 mean [5%, 95%] | imputed cells -> 0 | check |
|---|---|---|---|
| pcd0.5 | +0.0014 [-0.0016, +0.0037] | +0.0014 |  |
| pcd1 | +0.0032 [-0.0021, +0.0082] | +0.0032 |  |
| pcd2 | +0.0047 [-0.0063, +0.0139] | +0.0047 |  |
| pcd4 | +0.0044 [-0.0116, +0.0183] | +0.0044 |  |
| pool | -0.0544 [-0.1277, -0.0089] | -0.0544 |  |
| pc | -0.2810 [-0.3373, -0.2110] | -0.2810 |  |
| insurance | -0.0302 [-0.0329, -0.0250] | -0.0302 |  |
| fe_main (full_eval + rank_v4b, submitted) | -0.0020 [-0.0047, +0.0005] | -0.0006 |  |
| fe_new (full_eval + rank_rk_fx) | -0.0044 [-0.0094, +0.0005] | -0.0013 |  |
| rk_old (full_rk + rank_v4b) | -0.0039 [-0.0066, -0.0014] | -0.0027 |  |
| rk_new (full_rk + rank_rk_fx) | -0.0056 [-0.0111, -0.0000] | -0.0027 |  |

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
- fe_main (full_eval + rank_v4b, submitted): C1 panel +0.006; C1 hard NP dev2 +0.001; C1 W7 NP +0.006 (imp); C2 COCONUT panel -0.020 (imp); C2 COCONUT dev2 -0.020; C2 COCONUT W7 NP -0.020 (imp); C2 PubChem-only dev2 +0.004; C2 PubChem-only W7 timsTOF +0.004 (imp); C2 PubChem-only W7 NP +0.004 (imp)
  - C1 panel: (1-q_seen) x measured (n 250), seen part 0 | C1 hard NP dev2: (1-q_seen) x measured (n 290), seen part 0 | C1 W7 NP: imputed from C1 panel | C2 COCONUT panel: imputed from C2 COCONUT dev2 | C2 COCONUT dev2: measured (n 119) | C2 COCONUT W7 NP: imputed from C2 COCONUT dev2 | C2 PubChem-only dev2: measured (n 226) | C2 PubChem-only W7 timsTOF: imputed from C2 PubChem-only dev2 | C2 PubChem-only W7 NP: imputed from C2 PubChem-only dev2
- fe_new (full_eval + rank_rk_fx): C1 panel +0.010; C1 hard NP dev2 +0.005; C1 W7 NP +0.010 (imp); C2 COCONUT panel -0.038 (imp); C2 COCONUT dev2 -0.038; C2 COCONUT W7 NP -0.038 (imp); C2 PubChem-only dev2 +0.002; C2 PubChem-only W7 timsTOF +0.002 (imp); C2 PubChem-only W7 NP +0.002 (imp)
  - C1 panel: (1-q_seen) x measured (n 250), seen part 0 | C1 hard NP dev2: (1-q_seen) x measured (n 290), seen part 0 | C1 W7 NP: imputed from C1 panel | C2 COCONUT panel: imputed from C2 COCONUT dev2 | C2 COCONUT dev2: measured (n 119) | C2 COCONUT W7 NP: imputed from C2 COCONUT dev2 | C2 PubChem-only dev2: measured (n 226) | C2 PubChem-only W7 timsTOF: imputed from C2 PubChem-only dev2 | C2 PubChem-only W7 NP: imputed from C2 PubChem-only dev2
- rk_old (full_rk + rank_v4b): C1 panel +0.006; C1 hard NP dev2 -0.002; C1 W7 NP +0.003; C2 COCONUT panel -0.018 (imp); C2 COCONUT dev2 -0.018; C2 COCONUT W7 NP -0.022; C2 PubChem-only dev2 +0.002; C2 PubChem-only W7 timsTOF -0.023; C2 PubChem-only W7 NP -0.031
  - C1 panel: (1-q_seen) x measured (n 250), seen part 0 | C1 hard NP dev2: (1-q_seen) x measured (n 290), seen part 0 | C1 W7 NP: (1-q_seen) x measured (n 71), seen part 0 | C2 COCONUT panel: imputed from C2 COCONUT dev2 | C2 COCONUT dev2: measured (n 119) | C2 COCONUT W7 NP: measured (n 27) | C2 PubChem-only dev2: measured (n 226) | C2 PubChem-only W7 timsTOF: measured (n 278) | C2 PubChem-only W7 NP: measured (n 80)
- rk_new (full_rk + rank_rk_fx): C1 panel +0.008; C1 hard NP dev2 +0.003; C1 W7 NP +0.007; C2 COCONUT panel -0.043 (imp); C2 COCONUT dev2 -0.043; C2 COCONUT W7 NP -0.021; C2 PubChem-only dev2 +0.008; C2 PubChem-only W7 timsTOF +0.008; C2 PubChem-only W7 NP -0.025
  - C1 panel: (1-q_seen) x measured (n 250), seen part 0 | C1 hard NP dev2: (1-q_seen) x measured (n 290), seen part 0 | C1 W7 NP: (1-q_seen) x measured (n 71), seen part 0 | C2 COCONUT panel: imputed from C2 COCONUT dev2 | C2 COCONUT dev2: measured (n 119) | C2 COCONUT W7 NP: measured (n 27) | C2 PubChem-only dev2: measured (n 226) | C2 PubChem-only W7 timsTOF: measured (n 278) | C2 PubChem-only W7 NP: measured (n 80)