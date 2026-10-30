# 149 v2 S2 (i) MIST (M) vs current E2 recipe (C): fixed-recipe development cross-fit comparison (2026-10-30 14:17)

- primary 1/2 A' + 1/2 B_D' (F_M - F_C, C2): **-0.0003 [-0.0043, +0.0036]** (A' -0.0009 [-0.0049, +0.0030], B_D' +0.0004 [-0.0068, +0.0071])
- direction point estimates: fold 3 eval (4->3 models) -0.0026, fold 4 eval (3->4 models) +0.0021
- protection old B' C2 (8 cells): +0.0045 [+0.0004, +0.0087]
- protection E-outside C2 (A' + old B', pooled): +0.0110 [+0.0050, +0.0176]
- protection G C1 (2 cells): -0.0001 [-0.0045, +0.0044]
- protection NP C1 (pooled identities): +0.0007 [-0.0031, +0.0045]
- **gate: no**

## Descriptive (not used for the decision)

- F_M - F_Ccov (same covered training groups): A' +0.0006 [-0.0032, +0.0044], B_D' +0.0021 [-0.0052, +0.0089]
- A' C2: n 1600, MIST-covered 0.725, P empty 10 | P 0.5988, E2C 0.5558, E2M 0.5512, E2Ccov 0.5506, FC 0.6306, FM 0.6293, FCcov 0.6284 | sum(+) 24.90, sum(-) -27.01 | oracle max(E2C, E2M) - E2C +0.0456 | P-wrong rows FM - FC +0.0004 | same-formula truth rank C -> M (both ok, n 1409): median 1.0 -> 1.0, M better 218 / worse 258
- B_D' C2: n 400, MIST-covered 0.975, P empty 1 | P 0.2962, E2C 0.1451, E2M 0.1438, E2Ccov 0.1485, FC 0.2485, FM 0.2488, FCcov 0.2467 | sum(+) 2.77, sum(-) -2.63 | oracle max(E2C, E2M) - E2C +0.0063 | P-wrong rows FM - FC +0.0020 | same-formula truth rank C -> M (both ok, n 71): median 1.0 -> 1.0, M better 8 / worse 8
- old B' C2: n 1273, MIST-covered 0.549, P empty 19 | P 0.4404, E2C 0.2569, E2M 0.2492, E2Ccov 0.2547, FC 0.3956, FM 0.4001, FCcov 0.3958 | sum(+) 13.50, sum(-) -7.73 | oracle max(E2C, E2M) - E2C +0.0068 | P-wrong rows FM - FC -0.0011 | same-formula truth rank C -> M (both ok, n 499): median 1.0 -> 1.0, M better 33 / worse 58
- G C1: n 336, MIST-covered 0.920, P empty 0 | P 0.8600, E2C 0.9129, E2M 0.8962, E2Ccov 0.9136, FC 0.9379, FM 0.9378, FCcov 0.9373 | sum(+) 0.55, sum(-) -0.57 | oracle max(E2C, E2M) - E2C +0.0102 | P-wrong rows FM - FC -0.0003 | same-formula truth rank C -> M (both ok, n 336): median 1.0 -> 1.0, M better 7 / worse 24
- NP C1: n 941, MIST-covered 0.559, P empty 0 | P 0.8948, E2C 0.8890, E2M 0.8926, E2Ccov 0.8861, FC 0.9040, FM 0.9047, FCcov 0.9036 | sum(+) 4.07, sum(-) -3.43 | oracle max(E2C, E2M) - E2C +0.0107 | P-wrong rows FM - FC +0.0077 | same-formula truth rank C -> M (both ok, n 939): median 1.0 -> 1.0, M better 29 / worse 32
- MIST candidate coverage (all frames): 1208548 / 1977014; MSG overlap of the rosters: 0 (preflight; sensitivity trivial)
