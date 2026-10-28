# evidence-family audit v2 (full denominators, neutral ties, increments on the main list's errors)

| layer | n (rows) | main MRR | fp MRR | gl MRR | pop MRR | lib MRR | S MRR | glfp MRR | GL coverage (mean) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| A 053 NP C2 (H/N) | 520 | 0.5808 | 0.1828 | 0.2602 | 0.3334 | 0.0211 | 0.5009 | 0.2554 | 0.768 |
| B_D f1/f2 D C2 | 200 | 0.2782 | 0.1211 | 0.1594 | 0.0693 | 0.0056 | 0.2241 | 0.1598 | 1.000 |
| old B f1/f2 NP C2 | 800 | 0.4217 | 0.1798 | 0.1416 | 0.1378 | 0.0165 | 0.2950 | 0.1301 | 0.496 |
| G C1 | 200 | 0.8830 | 0.5434 | 0.6235 | 0.0104 | 0.8727 | 0.6752 | 0.6235 | 0.935 |
| panel C1 clean | 202 | 0.9251 | 0.6179 | 0.3979 | 0.7799 | 0.8955 | 0.9066 | 0.3921 | 0.847 |

Rescue potential: rows with a wrong main rank-1 and the truth in the list; share in which the evidence scores the truth above the main rank-1 (all / same-formula decoy). Damage potential: rows with a correct main rank-1; share in which the evidence scores the main rank-2 above the truth.

| layer | n wrong@1 (same formula) | rescue fp | rescue gl | rescue pop | rescue lib | rescue S | n right@1 | damage fp | damage gl | damage pop | damage lib | damage S |
|---|---|---|---|---|---|---|---:|---|---|---|---|---|
| A 053 NP C2 (H/N) | 185 (168) | 0.34 / 0.32 | 0.25 / 0.27 | 0.32 / 0.29 | 0.00 / 0.00 | 0.18 / 0.15 | 247 | 0.42 | 0.29 | 0.17 | 0.21 | 0.13 |
| B_D f1/f2 D C2 | 36 (30) | 0.39 / 0.33 | 0.19 / 0.20 | 0.28 / 0.27 | 0.00 / 0.00 | 0.08 / 0.10 | 44 | 0.32 | 0.30 | 0.30 | 0.23 | 0.16 |
| old B f1/f2 NP C2 | 276 (252) | 0.36 / 0.33 | 0.31 / 0.32 | 0.26 / 0.23 | 0.00 / 0.00 | 0.24 / 0.21 | 266 | 0.36 | 0.38 | 0.35 | 0.18 | 0.26 |
| G C1 | 35 (34) | 0.29 / 0.26 | 0.28 / 0.28 | 0.17 / 0.18 | 0.66 / 0.65 | 0.23 / 0.21 | 162 | 0.27 | 0.20 | 0.54 | 0.05 | 0.23 |
| panel C1 clean | 24 (24) | 0.58 / 0.58 | 0.29 / 0.29 | 0.46 / 0.46 | 0.67 / 0.67 | 0.50 / 0.50 | 178 | 0.12 | 0.29 | 0.06 | 0.09 | 0.03 |
