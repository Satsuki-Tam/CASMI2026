# Continuous training-structure penalty S - gamma * seen on the frozen v8w7a top-25 lists (exploratory description; label-using)

Score scale: the stored main score (median within-list gap rank1 - rank2 shown below). g = mean C2 delta (NP strata, molecule-weighted over folds), c = -mean C1 delta (same), pi* = g / (g + c).

| gamma | NP C2 g | NP C1 c | NP pi* | other C2 g | other C1 c | other pi* | panel C2 g | panel C1 c | panel pi* |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.25 | +0.0112 | +0.0064 | 0.64 | +0.0087 | +0.0068 | 0.56 | +0.0047 | +0.0054 | 0.46 |
| 0.5 | +0.0184 | +0.0087 | 0.68 | +0.0152 | +0.0253 | 0.38 | +0.0118 | +0.0090 | 0.57 |
| 1.0 | +0.0330 | +0.0237 | 0.58 | +0.0270 | +0.0471 | 0.36 | +0.0139 | +0.0255 | 0.35 |
| 2.0 | +0.0476 | +0.0670 | 0.42 | +0.0386 | +0.1018 | 0.28 | +0.0208 | +0.0907 | 0.19 |
| 4.0 | +0.0629 | +0.2117 | 0.23 | +0.0510 | +0.2305 | 0.18 | +0.0223 | +0.3433 | 0.06 |
| 8.0 | +0.0672 | +0.5039 | 0.12 | +0.0617 | +0.4364 | 0.12 | +0.0247 | +0.6946 | 0.03 |

- median score gap rank 1 - rank 2 over all stored lists: 2.153 (q25 0.740, q75 4.902)
