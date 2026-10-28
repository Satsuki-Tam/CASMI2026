# transductive edge audit (label-free edges; truth Tanimoto only for the audit)

| batch | n | nn_sim >= 0.5 | >= 0.6 | >= 0.7 | nearest (sim >= 0.6): truth Tanimoto median | its share >= 0.7 | family density: any other truth Tanimoto >= 0.7 | families reached by an edge (sim >= 0.6) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| f1dev | 499 | 0.281 | 0.160 | 0.104 | 0.210 | 0.050 | 0.080 | 4/40 |
| f2dev | 498 | 0.299 | 0.157 | 0.086 | 0.192 | 0.167 | 0.106 | 13/53 |
| np053f1dev | 319 | 0.345 | 0.179 | 0.100 | 0.602 | 0.439 | 0.257 | 25/82 |
| np053f2dev | 319 | 0.276 | 0.150 | 0.088 | 0.385 | 0.333 | 0.204 | 16/65 |
| panel | 250 | 0.680 | 0.480 | 0.344 | 0.404 | 0.208 | 0.192 | 25/48 |
| union_dev | 1635 | 0.464 | 0.262 | 0.160 | 0.257 | 0.219 | 0.201 | 94/328 |
